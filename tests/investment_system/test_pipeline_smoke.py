"""Smoke tests for the E2E pipeline - offline-friendly."""

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from investment_system.api import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    """Setup test environment with temporary directories."""
    # Use temporary runtime directory for tests
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(exist_ok=True)
    cache_dir = runtime_dir / "cache"
    cache_dir.mkdir(exist_ok=True)
    
    # Patch runtime paths
    monkeypatch.setattr("investment_system.pipeline.ingest.CACHE_DIR", cache_dir)
    monkeypatch.setattr("investment_system.db.store.RUNTIME_DIR", runtime_dir)
    monkeypatch.setattr("investment_system.db.store.DATABASE_URL", f"sqlite:///{runtime_dir}/test.db")


def test_healthz(client):
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_run_pipeline(client):
    """Test pipeline execution with symbols."""
    # Run pipeline with test symbols
    response = client.post(
        "/run",
        json={"symbols": ["AAPL", "MSFT"]}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "correlation_id" in data
    assert data["symbols_processed"] == 2
    assert "signals_generated" in data
    assert "timestamp" in data


def test_get_signals(client):
    """Test retrieving signals."""
    # First run the pipeline to generate signals
    run_response = client.post(
        "/run",
        json={"symbols": ["AAPL", "MSFT"]}
    )
    assert run_response.status_code == 200
    
    # Get signals
    response = client.get("/signals")
    assert response.status_code == 200
    data = response.json()
    assert "signals" in data
    assert "count" in data
    assert "timestamp" in data
    
    # Should have at least one signal
    assert len(data["signals"]) >= 1
    
    # Validate signal structure
    if data["signals"]:
        signal = data["signals"][0]
        assert "symbol" in signal
        assert "ts" in signal
        assert "signal" in signal
        assert signal["signal"] in ["buy", "sell", "hold"]


def test_export_csv(client):
    """Test CSV export."""
    # First run the pipeline to generate signals
    run_response = client.post(
        "/run",
        json={"symbols": ["AAPL", "MSFT"]}
    )
    assert run_response.status_code == 200
    
    # Export CSV
    response = client.get("/export.csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers.get("content-disposition", "")
    
    # Check CSV content is non-empty
    content = response.text
    assert len(content) > 0
    assert "symbol,ts,signal" in content.lower()


def test_export_pdf_not_implemented(client):
    """Test PDF export returns 501 when library not available."""
    response = client.get("/export.pdf")
    assert response.status_code == 501
    data = response.json()
    assert "error" in data
    assert "PDF" in data["error"] or "PDF" in data.get("message", "")


def test_dashboard(client):
    """Test dashboard endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Investment System Dashboard" in response.text


def test_pipeline_idempotency(client):
    """Test that running pipeline twice doesn't duplicate signals for same timestamp."""
    # Run pipeline first time
    response1 = client.post(
        "/run",
        json={"symbols": ["AAPL"]}
    )
    assert response1.status_code == 200
    signals_count1 = response1.json()["signals_generated"]
    
    # Small delay to ensure different correlation_id
    time.sleep(0.1)
    
    # Run pipeline second time with same symbol
    response2 = client.post(
        "/run",
        json={"symbols": ["AAPL"]}
    )
    assert response2.status_code == 200
    signals_count2 = response2.json()["signals_generated"]
    
    # Get all signals
    signals_response = client.get("/signals?limit=100")
    assert signals_response.status_code == 200
    all_signals = signals_response.json()["signals"]
    
    # Check for no duplicate timestamps for same symbol
    apple_signals = [s for s in all_signals if s["symbol"] == "AAPL"]
    timestamps = [s["ts"] for s in apple_signals]
    
    # Should have unique timestamps (no duplicates due to upsert)
    assert len(timestamps) == len(set(timestamps)), "Found duplicate timestamps for same symbol"


def test_offline_fallback(client, monkeypatch):
    """Test that pipeline works offline with fallback data."""
    # Mock yfinance to simulate network failure
    def mock_history(*args, **kwargs):
        raise ConnectionError("Network unavailable")
    
    # Patch yfinance Ticker.history to fail
    import yfinance
    monkeypatch.setattr(yfinance.Ticker, "history", mock_history)
    
    # Should still work with fallback data
    response = client.post(
        "/run",
        json={"symbols": ["TEST"]}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # Should generate signals from fallback data
    assert data["signals_generated"] > 0


def test_signals_with_limit(client):
    """Test signals endpoint with limit parameter."""
    # Run pipeline first
    client.post("/run", json={"symbols": ["AAPL", "MSFT"]})
    
    # Get limited signals
    response = client.get("/signals?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["signals"]) <= 5


def test_empty_symbols(client):
    """Test pipeline with empty symbols list."""
    response = client.post(
        "/run",
        json={"symbols": []}
    )
    
    # Should handle gracefully
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["symbols_processed"] == 0