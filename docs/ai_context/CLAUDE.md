# CLAUDE.md

This file guides Claude Code when working in this repository. **Follow these rules exactly.**

## 🚨 Critical Organization Rules

**Mandatory placement**
- **All Python code →** `src/investment_system/` (top-level import is **`investment_system`**, *never* `src.investment_system`).
- **Config code →** `src/config/` (e.g., `settings.py`). Non-code config files (e.g., json) may live in `config/`.
- **Tests →** `tests/` (mirror `src/` hierarchy).
- **Runtime artifacts →** `runtime/` (gitignored).
- **Docs →** `docs/` (exceptions allowed at root: `README.md`, `CHANGELOG.md`, `LICENSE`, and **`CLAUDE.md`**).

**Absolutely avoid**
- Creating `.py` files at repo root.
- Importing with the `src.` prefix (wrong for src-layout).
- Adding `os.getenv` outside `src/config/**` (use `config.settings.get_settings()`).

## Current Project State (source of truth)

- Src-layout with editable install.
- Pre-commit blocks `os.getenv` outside `src/config/**`.
- Tests pass locally (offline-friendly scaffolding via `.env.test` + `pytest.ini`).
- Compatibility shim for legacy imports: `core.investment_system` re-exports `investment_system`.
- `STATUS.md` and `ROADMAP.md` describe capabilities and near-term KPIs.

## Imports (correct patterns)

```python
# ✅ Correct (src-layout creates top-level package `investment_system`)
from investment_system.analysis.quick_analysis import run
from investment_system.data.market_data_collector import MarketDataCollector

# ❌ Incorrect (do not prefix with src.)
# from src.investment_system.analysis.quick_analysis import run
```

## Configuration (do this)

- Load settings via `src/config/settings.py`:
  ```python
  from config.settings import get_settings
  settings = get_settings()
  ```
- `.env` (local), `.env.test` (tests/CI). **Never** hardcode secrets.
- Loader tolerates `config/` and `src/config/` paths.

## Allowed Edit Scope for Claude

When implementing features or fixes, restrict changes to:
- `src/investment_system/**`, `src/config/**`
- `tests/**`
- `.github/workflows/**`
- `docs/**`, `README.md`, `STATUS.md`, `ROADMAP.md`
- `Makefile`, `pyproject.toml`, `pytest.ini`

**Do not** touch unrelated modules, delete public APIs, or refactor widely without an explicit instruction.

## Common Commands

```bash
# Dev setup
pip install -e .[dev]

# Run API (healthcheck at /healthz)
uvicorn investment_system.api:app --reload

# Tests (offline-friendly)
pytest -q

# Make targets (if present)
make setup | make lint | make test | make cov | make run
```

## Next Milestone (E2E Thin Slice)

Implement minimal E2E without breaking existing logic:

**A) Ingest — `src/investment_system/pipeline/ingest.py`**
- `fetch_prices(symbols: list[str], lookback_days: int=120) -> pd.DataFrame`
- yfinance + tenacity retry/backoff + simple rate-limit.
- TTL cache 10m under `runtime/cache/{symbol}.parquet`.
- Fallback: cached (stale-but-usable) or tiny baked sample for tests.
- Columns: `date, open, high, low, close, volume, symbol` (lowercase).

**B) Analyze — `src/investment_system/pipeline/analyze.py`**
- `add_indicators(df)` → SMA_20, SMA_50, RSI_14.
- `generate_signals(df)` → `{symbol, ts, signal, rsi, sma20, sma50}`.
- Rule: SMA20 cross over/under SMA50; RSI guards (<30 buy bias, >70 sell bias).

**C) Persist — `src/investment_system/db/store.py`**
- SQLAlchemy (SQLite `runtime/app.db`), create-if-not-exists.
- Tables: `prices`, `signals`; upsert latest signals.
- Pragmas: `journal_mode=WAL`, `synchronous=NORMAL`. Short-lived sessions, retry on lock.

**D) API & Dashboard — `src/investment_system/api.py` + `src/investment_system/web/templates/index.html`**
- `POST /run` `{symbols[]}` → run pipeline; attach `correlation_id` (log it).
- `GET /signals` → latest N signals (JSON).
- `GET /export.csv` → CSV (filename `signals_YYYYMMDD_HHMM.csv`).
- `GET /export.pdf` → 501 JSON if PDF lib not installed.
- Dashboard lists (symbol, ts, signal, rsi, sma20, sma50); badge “stale” if from cache.

**E) Resilience & Logs**
- Retries with jitter and per-request timeouts.
- Structured JSON logs (`ts, level, msg, module, correlation_id`), secrets redacted.

**F) Tests — `tests/investment_system/test_pipeline_smoke.py`**
- `/run` with `["AAPL","MSFT"]` → 200.
- `/signals` returns ≥1 item.
- `/export.csv` → 200 and non-empty.
- Idempotent: second `/run` doesn’t duplicate latest ts.
- Must pass **offline** (cache/sample fallback).

**G) CI — `.github/workflows/ci.yml`**
- Python 3.11, `pip install -e .[dev]`, `ruff check`, `pytest -q --cov=src --cov-report=term-missing`.
- Keep workflow short; optional pip cache.

## Guardrails (Do / Don’t)

**Do**
- Small PRs, narrow diffs, file allowlist above.
- Prefer injection/time-of-use for `get_settings()` (avoid import-time side-effects).
- Log structured JSON with `correlation_id`.

**Don’t**
- Introduce new `os.getenv` outside `src/config/**`.
- Add heavy imports in any `__init__.py`.
- Break existing endpoints or tests.
- Depend on live network in tests.

## Verification Script (run before PR)

```bash
pip install -e .[dev]
uvicorn investment_system.api:app --reload & sleep 2 && curl -sSf http://127.0.0.1:8000/healthz && pkill -f uvicorn
curl -s -X POST localhost:8000/run -H "content-type: application/json" -d '{"symbols":["AAPL","MSFT"]}'
curl -s localhost:8000/signals | head
curl -s -D- localhost:8000/export.csv | head
pytest -q tests/investment_system/test_pipeline_smoke.py
```

## PR Template (copy into PR body)

**Title:** `feat(e2e): thin slice ingest→analyze→persist→api/export with resilience`

**Summary**
- Add ingest/analyze/store modules with caching, retries, and SQLite upserts.
- Extend API with /run, /signals, /export.csv (/export.pdf 501 if unavailable).
- JSON logging + correlation_id; offline-friendly smoke test.
- CI workflow (ruff + pytest coverage). Docs updated.

**Verification**
- Healthz 200 ✅
- /run 200 with symbols ✅
- /signals returns data ✅
- /export.csv non-empty ✅
- Tests pass; CI green ✅

**Notes**
- PDF export optional; returns 501 without weasyprint/reportlab.
- Cache TTL 10m; stale badge on dashboard.