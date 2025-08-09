# 7-Day E2E Thin Slice Roadmap

Objective
- Deliver a minimal, reliable E2E flow: fetch market data (yfinance), compute basic analytics, and produce a simple report without external paid APIs.

KPIs
- >95% green test run rate on default branch.
- CI wall time under 6 minutes for unit + thin E2E tests.
- Zero import-time network side-effects across top-level packages.
- Reproducible installs on Python 3.9–3.12.

Plan (D1–D7)
- D1: Stabilize tests in CI, confirm env bootstrapping via `.env.test`, capture baseline timings.
- D2: Harden market data adapters for offline mode (cached sample fixtures), add 2 happy-path tests.
- D3: Add a small healthcheck CLI (`python -m investment_system.healthcheck`) exercising core wiring.
- D4: Introduce simple report generation with deterministic sample data; add snapshot test.
- D5: Add ruff/mypy fast lanes to CI, fix high-signal warnings only.
- D6: Document troubleshooting and local dev quickstart; improve error messages for missing keys.
- D7: Review shim usage and deprecation notice; draft removal PR.

Risks & Mitigations
- External API rate limits: prefer cached sample data in tests.
- Dependency drift: keep optional extras for heavy providers (e.g., Alpaca).
- Import side-effects: keep __init__.py lightweight; enforce via lint rule later.
