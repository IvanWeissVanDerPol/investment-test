"""
Dev-only telemetry dashboard for internal monitoring.
NEVER exposed in production. Requires FEATURE_DEV_TELEMETRY=true.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import Response, HTMLResponse
from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    CONTENT_TYPE_LATEST, generate_latest, REGISTRY
)
import json


# Check if telemetry is enabled
def require_dev_telemetry():
    """Ensure telemetry is only available in dev mode."""
    if os.getenv("FEATURE_DEV_TELEMETRY") != "true":
        raise HTTPException(status_code=404, detail="Not found")
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=404, detail="Not found")


# Metrics (no PII, aggregated only)
ai_prompt_injection_blocked = Counter(
    "ai_prompt_injection_blocked_total",
    "Total prompt injection attempts blocked"
)

ai_context_token_spend = Summary(
    "ai_context_token_spend_sum",
    "Tokens spent on AI context"
)

ai_context_hit_rate = Gauge(
    "ai_context_hit_rate",
    "Cache hit rate for AI context"
)

sonar_core_nodes = Gauge(
    "sonar_core_nodes_count",
    "Number of core nodes in Sonar graph"
)

sonar_core_delta = Gauge(
    "sonar_core_delta",
    "Delta in core node importance"
)

api_requests = Counter(
    "api_requests_total",
    "Total API requests",
    ["tier", "endpoint", "method", "status"]
)

ai_output_repair = Counter(
    "ai_output_repair_count",
    "Number of AI outputs that needed repair"
)

latency_histogram = Histogram(
    "latency_ms_bucket",
    "Request latency in milliseconds",
    ["endpoint"],
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000)
)

# Create telemetry app
telemetry_app = FastAPI(
    title="Dev Telemetry Dashboard",
    description="Internal monitoring metrics (dev/staging only)",
    version="1.0.0"
)


@telemetry_app.get("/dev/telemetry/metrics")
def get_metrics(_: None = Depends(require_dev_telemetry)):
    """Prometheus-compatible metrics endpoint."""
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@telemetry_app.get("/dev/telemetry/health")
def health_check(_: None = Depends(require_dev_telemetry)):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "telemetry": "enabled",
        "timestamp": datetime.utcnow().isoformat()
    }


@telemetry_app.get("/dev/telemetry/dashboard", response_class=HTMLResponse)
def dashboard(_: None = Depends(require_dev_telemetry)):
    """Simple HTML dashboard for metrics visualization."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dev Telemetry Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
            .warning { background: #fff3cd; padding: 10px; border: 1px solid #ffc107; margin: 20px 0; }
            .metric-card { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric-title { font-weight: bold; color: #007bff; }
            .metric-value { font-size: 24px; color: #28a745; margin: 10px 0; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            button { background: #007bff; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 5px; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h1>🔍 Dev Telemetry Dashboard</h1>
        <div class="warning">
            ⚠️ <strong>Development Only</strong> - This dashboard is not available in production.
            No PII is collected. All metrics are aggregated and sampled.
        </div>
        
        <div class="grid">
            <div class="metric-card">
                <div class="metric-title">🛡️ Security</div>
                <div id="security-metrics">Loading...</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">🤖 AI Performance</div>
                <div id="ai-metrics">Loading...</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">📊 API Usage</div>
                <div id="api-metrics">Loading...</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">🔗 Code Graph</div>
                <div id="sonar-metrics">Loading...</div>
            </div>
        </div>
        
        <div style="margin-top: 30px;">
            <button onclick="refreshMetrics()">Refresh Metrics</button>
            <button onclick="downloadMetrics()">Download Raw Metrics</button>
        </div>
        
        <script>
            async function refreshMetrics() {
                try {
                    const response = await fetch('/dev/telemetry/stats');
                    const data = await response.json();
                    
                    document.getElementById('security-metrics').innerHTML = `
                        <div class="metric-value">${data.security.blocked_injections || 0}</div>
                        <div>Blocked prompt injections</div>
                    `;
                    
                    document.getElementById('ai-metrics').innerHTML = `
                        <div class="metric-value">${data.ai.avg_tokens || 0}</div>
                        <div>Avg tokens per request</div>
                        <div>Cache hit rate: ${(data.ai.cache_hit_rate * 100).toFixed(1)}%</div>
                    `;
                    
                    document.getElementById('api-metrics').innerHTML = `
                        <div class="metric-value">${data.api.total_requests || 0}</div>
                        <div>Total requests today</div>
                        <div>Avg latency: ${data.api.avg_latency || 0}ms</div>
                    `;
                    
                    document.getElementById('sonar-metrics').innerHTML = `
                        <div class="metric-value">${data.sonar.core_nodes || 0}</div>
                        <div>Core nodes tracked</div>
                        <div>Delta: ${(data.sonar.core_delta || 0).toFixed(3)}</div>
                    `;
                } catch (error) {
                    console.error('Failed to fetch metrics:', error);
                }
            }
            
            async function downloadMetrics() {
                window.open('/dev/telemetry/metrics', '_blank');
            }
            
            // Auto-refresh every 30 seconds
            setInterval(refreshMetrics, 30000);
            refreshMetrics();
        </script>
    </body>
    </html>
    """
    return html_content


@telemetry_app.get("/dev/telemetry/stats")
def get_stats(_: None = Depends(require_dev_telemetry)) -> Dict[str, Any]:
    """Get aggregated statistics for dashboard."""
    # This would normally query from a metrics store
    # For now, return mock aggregated data
    return {
        "security": {
            "blocked_injections": 0,
            "secrets_detected": 0
        },
        "ai": {
            "avg_tokens": 2500,
            "cache_hit_rate": 0.75,
            "output_repairs": 0
        },
        "api": {
            "total_requests": 1247,
            "avg_latency": 45,
            "error_rate": 0.002
        },
        "sonar": {
            "core_nodes": 42,
            "core_delta": 0.015,
            "total_edges": 187
        }
    }


class TelemetryMiddleware:
    """Middleware to collect telemetry metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Only collect if telemetry is enabled
        if os.getenv("FEATURE_DEV_TELEMETRY") != "true":
            await self.app(scope, receive, send)
            return
        
        # Start timer
        start_time = datetime.now()
        
        # Process request
        await self.app(scope, receive, send)
        
        # Record metrics (no PII)
        latency = (datetime.now() - start_time).total_seconds() * 1000
        endpoint = scope.get("path", "unknown")
        method = scope.get("method", "unknown")
        
        # Update metrics
        latency_histogram.labels(endpoint=endpoint).observe(latency)
        
        # Note: In real implementation, we'd extract tier and status from response
        api_requests.labels(
            tier="unknown",
            endpoint=endpoint,
            method=method,
            status="200"
        ).inc()


def update_telemetry(metric_name: str, value: float, labels: Optional[Dict] = None):
    """
    Update telemetry metric (dev only).
    
    Args:
        metric_name: Name of metric to update
        value: Metric value
        labels: Optional labels
    """
    if os.getenv("FEATURE_DEV_TELEMETRY") != "true":
        return
    
    # Update appropriate metric
    if metric_name == "prompt_injection_blocked":
        ai_prompt_injection_blocked.inc()
    elif metric_name == "context_tokens":
        ai_context_token_spend.observe(value)
    elif metric_name == "context_hit_rate":
        ai_context_hit_rate.set(value)
    elif metric_name == "sonar_nodes":
        sonar_core_nodes.set(value)
    elif metric_name == "sonar_delta":
        sonar_core_delta.set(value)
    elif metric_name == "output_repair":
        ai_output_repair.inc()


# Export for use in main app
__all__ = ["telemetry_app", "TelemetryMiddleware", "update_telemetry"]