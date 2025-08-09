You are my senior engineer. Branch: `integration-claude-review`. Working tree clean, synced with origin.

Current state
- pytest.ini autoloads .env.test; tests pass (2 passed, 1 skipped).
- Alpaca moved to optional extra; urllib3 pinned; default dev env conflict-free.
- Side-effect imports removed from __init__.py.
- Compatibility shim: `core.investment_system` → `investment_system`.
- STATUS.md & ROADMAP.md linked in README.
- Config loader falls back to `config/` or `src/config/`.
- /healthz OK; pre-commit blocks `os.getenv` outside `src/config/**`.

Constraints
- Do NOT change business logic outside the new thin-slice modules/endpoints.
- Small commits; surgical diffs; no mass refactors.
- Keep runtime artifacts under `runtime/` (gitignored).
- Tests must NOT rely on live network (use caching/fallbacks/mocks).

Goals (next phase)
1) Prove E2E flow: ingest → analyze → persist → API/dashboard → export.
2) Add resilience: retry/backoff, TTL cache, stale-but-usable fallback, timeouts.
3) CI: lint + tests + coverage (Python 3.11).
4) Ship concise docs + a ready-to-paste PR body.

Performance/UX targets
- Quick run (2–3 symbols): < 60s end-to-end on a cold cache.
- Warm cache path: < 10s.
- API endpoints idempotent; return JSON errors with helpful messages.

Tasks (strict allowlist edits)
A) E2E Thin Slice (new modules only)
- `src/investment_system/pipeline/ingest.py`
  - `fetch_prices(symbols: list[str], lookback_days: int=120) -> pd.DataFrame`
  - Use yfinance with:
    - Tenacity retry/backoff (max ~5 attempts, jitter), per-request timeout (~25s/symbol).
    - Simple rate-limit (e.g., sleep if >5 req/min).
  - Cache raw frames per symbol under `runtime/cache/{symbol}.parquet` with TTL=10m.
  - Validate schema: date, open, high, low, close, volume, symbol (lowercase col names).
  - If live fetch fails, return cached data if within TTL; else return a tiny baked-in sample for tests.

- `src/investment_system/pipeline/analyze.py`
  - `add_indicators(df) -> df` (SMA_20, SMA_50, RSI_14).
  - `generate_signals(df) -> list[dict]` → {symbol, ts, signal: buy|sell|hold, rsi, sma20, sma50}.
  - Rule: SMA20 cross over/under SMA50; RSI guards (<30 buy bias, >70 sell bias).
  - Ensure NaN-safe calculations; drop warmup rows.

- `src/investment_system/db/store.py`
  - SQLAlchemy (SQLite `runtime/app.db`).
  - Tables: `prices` (symbol, ts, ohlcv), `signals` (symbol, ts, signal, rsi, sma20, sma50).
  - Create-if-not-exists; upsert latest signals.
  - Use short-lived sessions, pragmas:
    - `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`
  - Wrap writes in transactions; small retry if DB is locked.

B) API + Dashboard (extend safely)
- `src/investment_system/api.py`
  - `POST /run` {symbols[]} → run pipeline & persist. Generate `correlation_id` and log it.
  - `GET /signals` → latest N signals (JSON, N param with sane default).
  - `GET /export.csv` → CSV of latest signals (filename `signals_YYYYMMDD_HHMM.csv`).
  - `GET /export.pdf` → if PDF lib unavailable, return 501 + JSON message.
- `src/investment_system/web/templates/index.html` (Jinja)
  - Minimal table: symbol, ts, signal, rsi, sma20, sma50.
  - Show “stale” badge if data is from cache fallback.

C) Resilience & Logging
- Tenacity retry/backoff + per-request timeouts on external calls.
- Serve cached data if live fetch fails (mark `stale:true`).
- Structured JSON logs with keys: `ts, level, msg, module, correlation_id`.
- Redact secrets; propagate `correlation_id` across the `/run` execution.

D) Tests (smoke; offline-friendly)
- `tests/investment_system/test_pipeline_smoke.py`
  - `/run` with ["AAPL","MSFT"] → 200.
  - `/signals` returns ≥1 item.
  - `/export.csv` → 200 and non-empty body.
  - Must pass **offline** (cache/sample fallback).
  - Idempotency: calling `/run` twice does not duplicate latest signals for same ts.

E) CI (minimal)
- `.github/workflows/ci.yml`:
  - checkout; setup-python 3.11;
  - `pip install -e .[dev]`;
  - `ruff check`;
  - `pytest -q --cov=src --cov-report=term-missing`.
- Optional: pip cache; upload CSV as artifact if generated.

F) Docs & PR
- Append to STATUS.md: E2E capabilities, limits (stale cache, PDF optional), perf notes.
- Append to ROADMAP.md: next 7-day KPIs (async I/O, news sentiment basics, monitoring/alerts, coverage ≥85%).
- Prepare a PR body with:
  - Title: `feat(e2e): thin slice ingest→analyze→persist→api/export with resilience`
  - Summary bullets of changes.
  - Verification commands (below).
  - Checklist: healthz 200, /run 200, /signals data, CSV exported, tests passing, CI green.

Verification commands (run; report PASS/FAIL; do not edit logic if they fail—propose smallest fix)
- `pip install -e .[dev]`
- `uvicorn investment_system.api:app --reload & sleep 2 && curl -sSf http://127.0.0.1:8000/healthz && pkill -f uvicorn`
- `curl -s -X POST localhost:8000/run -H "content-type: application/json" -d '{"symbols":["AAPL","MSFT"]}'`
- `curl -s localhost:8000/signals | head`
- `curl -s -D- localhost:8000/export.csv | head`
- `pytest -q tests/investment_system/test_pipeline_smoke.py`

File allowlist (edit/create only these unless a truly minimal fix is unavoidable)
- `src/investment_system/pipeline/ingest.py`
- `src/investment_system/pipeline/analyze.py`
- `src/investment_system/db/store.py`
- `src/investment_system/web/templates/index.html`
- `src/investment_system/api.py`
- `tests/investment_system/test_pipeline_smoke.py`
- `.github/workflows/ci.yml`
- `STATUS.md`, `ROADMAP.md` (append), `README.md` (links only)

Deliverables
- Small commits per section A–F with descriptive messages.
- Final report:
  - ✅/❌ for each verification step (healthz, run, signals, CSV, tests, CI).
  - If any ❌: exact file:line, cause, smallest fix.
  - “What changed” list (file → one-line rationale).
  - PR title + description (ready to paste).

Stop criteria
- All verification steps ✅; CI green; STATUS/ROADMAP updated.
- Reply exactly: “E2E thin slice complete — ready for demo.”
