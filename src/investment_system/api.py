"""API module with endpoints for pipeline execution and data export."""

import csv
import io
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel
from pathlib import Path

from investment_system.pipeline.ingest import fetch_prices
from investment_system.pipeline.analyze import generate_signals
from investment_system.db.store import get_store

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s","module":"%(name)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Investment System API", version="1.0.0")

# Setup Jinja2 templates
templates_dir = Path(__file__).parent / "web" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


class RunRequest(BaseModel):
    """Request model for /run endpoint."""
    symbols: List[str]


class SignalResponse(BaseModel):
    """Response model for signals."""
    symbol: str
    ts: str
    signal: str
    rsi: Optional[float]
    sma20: Optional[float]
    sma50: Optional[float]
    close: Optional[float]
    is_stale: bool = False


@app.get("/healthz")
def healthz():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/run")
async def run_pipeline(request: RunRequest):
    """
    Run the investment pipeline for specified symbols.
    
    Args:
        request: RunRequest with list of symbols
    
    Returns:
        Status and correlation ID
    """
    correlation_id = str(uuid.uuid4())
    
    # Log with correlation ID
    logger.info(f"Starting pipeline run", extra={"correlation_id": correlation_id, "symbols": request.symbols})
    
    try:
        # Fetch prices with caching
        prices_df = fetch_prices(request.symbols, lookback_days=120)
        logger.info(f"Fetched {len(prices_df)} price records", extra={"correlation_id": correlation_id})
        
        # Generate signals
        signals = generate_signals(prices_df)
        logger.info(f"Generated {len(signals)} signals", extra={"correlation_id": correlation_id})
        
        # Store in database
        store = get_store()
        
        # Store prices
        if not prices_df.empty:
            store.upsert_prices(prices_df)
        
        # Store signals
        if signals:
            store.upsert_signals(signals)
        
        return {
            "status": "success",
            "correlation_id": correlation_id,
            "symbols_processed": len(request.symbols),
            "signals_generated": len(signals),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")


@app.get("/signals")
async def get_signals(limit: int = 50):
    """
    Get latest trading signals.
    
    Args:
        limit: Maximum number of signals to return (default 50)
    
    Returns:
        List of latest signals
    """
    try:
        store = get_store()
        signals = store.get_latest_signals(limit=limit)
        
        return {
            "signals": signals,
            "count": len(signals),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get signals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve signals: {str(e)}")


@app.get("/export.csv")
async def export_csv():
    """
    Export latest signals as CSV.
    
    Returns:
        CSV file with signals
    """
    try:
        store = get_store()
        signals = store.get_latest_signals(limit=100)
        
        if not signals:
            raise HTTPException(status_code=404, detail="No signals available")
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=['symbol', 'ts', 'signal', 'rsi', 'sma20', 'sma50', 'close', 'is_stale'],
            extrasaction='ignore'
        )
        
        writer.writeheader()
        writer.writerows(signals)
        
        # Prepare response
        output.seek(0)
        filename = f"signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")


@app.get("/export.pdf")
async def export_pdf():
    """
    Export signals as PDF (placeholder - returns 501 if PDF library not available).
    
    Returns:
        PDF file or 501 status if not implemented
    """
    # Check if PDF library is available
    try:
        import reportlab
        # If we get here, reportlab is installed - would implement PDF generation
        # For now, still return 501 as implementation is not complete
        return JSONResponse(
            status_code=501,
            content={"error": "PDF export not yet implemented", "message": "Install reportlab or weasyprint for PDF support"}
        )
    except ImportError:
        return JSONResponse(
            status_code=501,
            content={"error": "PDF library not installed", "message": "Install reportlab or weasyprint for PDF support"}
        )


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the dashboard with Jinja2 template."""
    return templates.TemplateResponse("index.html", {"request": request})


# For running with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)