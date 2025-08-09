# Project Status

Last updated: 2025-08-09

What currently works
- Local health checks and basic data utilities run without network side-effects at import time.
- Tests auto-load environment from `.env.test` via pytest configuration (no manual exports).
- PyPI dev install `pip install -e .[dev]` resolves without alpaca/urllib3 conflicts by default.
- No top-level imports trigger external network calls; heavy modules are deferred.

Quality gates
- Lint/type: configured in `pyproject.toml` (ruff/flake8/mypy) — run as needed.
- Tests: `pytest -q` expected to pass with defaults.
- Packaging: editable install supported.

Environment
- Uses `.env.test` for CI and local test runs.
- Runtime artifacts written under `runtime/` and `cache/` as needed by tests.

Notes
- Alpaca client is optional; install with `pip install -e .[alpaca]` when needed.
- The `core/investment_system` path remains as a temporary shim for compatibility.

## E2E Pipeline Capabilities

**Implemented Features** (as of 2025-08-09)
- **Data Ingestion**: Fetch price data via yfinance with retry/backoff logic, TTL caching (10min), and offline fallback
- **Technical Analysis**: Calculate SMA20, SMA50, RSI14 indicators; generate buy/sell/hold signals based on crossovers
- **Persistence**: SQLAlchemy with SQLite, optimized pragmas (WAL mode), upsert operations for idempotency
- **API Endpoints**:
  - `POST /run`: Execute pipeline for symbols with correlation tracking
  - `GET /signals`: Retrieve latest signals (JSON)
  - `GET /export.csv`: Export signals as CSV with timestamped filename
  - `GET /export.pdf`: Returns 501 (not implemented) with helpful message
  - `GET /`: Interactive dashboard with real-time signal display
- **Dashboard**: HTML/JS interface showing signals table with stale data badges
- **Resilience**: Cached data fallback, stale marking, structured JSON logging, correlation IDs

**Performance Targets**
- Cold cache: < 60s for 2-3 symbols
- Warm cache: < 10s response time
- Rate limiting: ~5 requests/second to avoid API throttling

**Limitations**
- PDF export requires additional libraries (reportlab/weasyprint)
- Dashboard uses polling for updates (not WebSocket)
- Single-threaded processing (async I/O planned)
