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
