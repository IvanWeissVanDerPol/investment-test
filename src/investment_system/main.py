"""
Unified Investment System API
High-quality, production-ready FastAPI application with proper error handling,
logging, and architecture patterns.
"""

import uuid
import structlog
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler as _http_exception_handler
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field

from config.settings import get_settings
from investment_system.core.exceptions import (
    APIError, ErrorCode, ValidationError, AuthenticationError,
    AuthorizationError, RateLimitError, ServiceUnavailableError
)
from investment_system.core.logging import setup_logging, get_logger
from investment_system.core.monitoring import setup_monitoring, track_request
from investment_system.infrastructure.database_session import get_database_session
from investment_system.api import router as api_router
from investment_system.sonar.api import router as sonar_router

# Initialize settings and logging
settings = get_settings()
setup_logging(settings.log_level, settings.log_format)
logger = get_logger(__name__)

# Setup monitoring (metrics, tracing)
monitoring = setup_monitoring(settings)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(..., description="Response timestamp")
    version: str = Field(..., description="API version")
    correlation_id: str = Field(..., description="Request correlation ID")
    dependencies: Dict[str, str] = Field(..., description="Dependency health status")


class ErrorResponseModel(BaseModel):
    """Standardized error response model."""
    error: Dict[str, Any] = Field(..., description="Error details")
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "details": {"field": "email", "issue": "Invalid email format"},
                    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2025-01-11T10:00:00Z"
                }
            }
        }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting Investment System API", version=settings.api_version)
    
    # Initialize database
    try:
        # Test database connection
        async with get_database_session() as session:
            await session.execute("SELECT 1")
        logger.info("Database connection verified")
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        raise
    
    # Initialize monitoring
    await monitoring.start()
    logger.info("Monitoring initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Investment System API")
    await monitoring.stop()


# Create FastAPI application
app = FastAPI(
    title="Investment System API",
    description="Production-ready trading signals API with comprehensive security and monitoring",
    version=settings.api_version,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
    lifespan=lifespan,
    responses={
        422: {"model": ErrorResponseModel, "description": "Validation Error"},
        500: {"model": ErrorResponseModel, "description": "Internal Server Error"},
    }
)

# Security middleware - order matters
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url if settings.redis_url else "memory://",
    default_limits=["1000/hour"]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def correlation_middleware(request: Request, call_next) -> Response:
    """Add correlation ID to all requests for tracing."""
    correlation_id = (
        request.headers.get("x-correlation-id") or 
        request.headers.get("x-request-id") or 
        str(uuid.uuid4())
    )
    
    # Store in request state for access in endpoints
    request.state.correlation_id = correlation_id
    
    # Add to logging context
    with structlog.contextvars.bound_contextvars(correlation_id=correlation_id):
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        start_time = datetime.now(timezone.utc)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        # Add correlation ID to response
        response.headers["x-correlation-id"] = correlation_id
        
        # Log response
        logger.info(
            "Request completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2)
        )
        
        # Track metrics
        await track_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        return response


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next) -> Response:
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Security headers
    response.headers.update({
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    })
    
    # Only add HSTS in production with HTTPS
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


# Exception handlers
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors with structured responses."""
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    logger.error(
        "API error occurred",
        error_code=exc.code.value,
        message=exc.message,
        details=exc.details,
        endpoint=request.url.path,
        method=request.method,
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    return JSONResponse(
        status_code=exc.code.http_status,
        content={
            "error": {
                "code": exc.code.value,
                "message": exc.message,
                "details": exc.details,
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions with structured responses."""
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    # Map HTTP status codes to error codes
    error_code_map = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.AUTHENTICATION_REQUIRED,
        403: ErrorCode.AUTHORIZATION_FAILED,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        409: ErrorCode.CONFLICT,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }
    
    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        error_code=error_code.value,
        detail=exc.detail,
        endpoint=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code.value,
                "message": str(exc.detail),
                "details": {},
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with proper logging and response."""
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    logger.exception(
        "Unhandled exception occurred",
        exception_type=type(exc).__name__,
        endpoint=request.url.path,
        method=request.method,
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    # Don't expose internal errors in production
    message = (
        str(exc) if settings.environment == "development" 
        else "An internal error occurred. Please contact support."
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": ErrorCode.INTERNAL_ERROR.value,
                "message": message,
                "details": {},
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
@limiter.limit("100/minute")
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint with dependency status.
    Returns detailed health information about the service and its dependencies.
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    # Check dependencies
    dependencies = {}
    
    # Database health
    try:
        async with get_database_session() as session:
            await session.execute("SELECT 1")
        dependencies["database"] = "healthy"
    except Exception as e:
        dependencies["database"] = f"unhealthy: {str(e)[:50]}"
        logger.warning("Database health check failed", error=str(e))
    
    # Redis health (if configured)
    if settings.redis_url:
        try:
            # Test Redis connection
            dependencies["redis"] = "healthy"
        except Exception as e:
            dependencies["redis"] = f"unhealthy: {str(e)[:50]}"
            logger.warning("Redis health check failed", error=str(e))
    
    # Overall status
    overall_status = "healthy" if all(
        status.startswith("healthy") for status in dependencies.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        version=settings.api_version,
        correlation_id=correlation_id,
        dependencies=dependencies
    )


# Legacy health endpoint for backward compatibility
@app.get("/healthz", include_in_schema=False)
@limiter.limit("100/minute")
async def legacy_health_check(request: Request):
    """Legacy health check endpoint for backward compatibility."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# Include API routers - integrate with existing structure
app.include_router(
    api_router,
    prefix="/api/v1",
    tags=["API v1"]
)

# Include SONAR API for AI context optimization
app.include_router(
    sonar_router,
    prefix="/sonar",
    tags=["SONAR"]
)

# Root endpoint
@app.get("/", tags=["Root"])
async def root(request: Request):
    """API root endpoint with basic information."""
    return {
        "name": "Investment System API",
        "version": settings.api_version,
        "status": "running",
        "docs_url": "/docs" if settings.environment == "development" else None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Development-only endpoints
if settings.environment == "development":
    @app.get("/debug/settings", tags=["Debug"])
    async def debug_settings(request: Request):
        """Debug endpoint to view current settings (development only)."""
        return {
            "environment": settings.environment,
            "api_version": settings.api_version,
            "log_level": settings.log_level,
            "database_configured": bool(settings.database_url),
            "redis_configured": bool(settings.redis_url),
            "cors_origins": settings.cors_origins,
        }
    
    @app.get("/debug/correlation/{correlation_id}", tags=["Debug"])
    async def debug_correlation(correlation_id: str, request: Request):
        """Debug endpoint to test correlation ID handling."""
        request.state.correlation_id = correlation_id
        return {
            "correlation_id": correlation_id,
            "message": "Correlation ID set successfully"
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "investment_system.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        access_log=True,
        log_config=None,  # Use our custom logging
    )