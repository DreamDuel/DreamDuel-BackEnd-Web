"""Main FastAPI application"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.core.config import settings
from app.core.exceptions import DreamDuelException
from app.core.middleware import RateLimitMiddleware
from app.infrastructure.database.session import init_db
from app.infrastructure.cache.redis_client import redis_client
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting DreamDuel API...")
    
    # Initialize Sentry if configured
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            integrations=[FastApiIntegration()],
            traces_sample_rate=1.0 if settings.DEBUG else 0.1,
        )
    
    # Initialize Redis
    redis_client.connect()
    print("✅ Redis connected")
    
    # Initialize database (only in development)
    if settings.DEBUG:
        init_db()
        print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down DreamDuel API...")
    redis_client.disconnect()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for DreamDuel - AI-powered image generation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    debug=settings.DEBUG
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (temporarily disabled for development)
# TODO: Fix async issues and re-enable in production
# app.add_middleware(RateLimitMiddleware, requests_per_minute=60)


# Custom exception handlers
@app.exception_handler(DreamDuelException)
async def dreamduel_exception_handler(request: Request, exc: DreamDuelException):
    """Handle custom DreamDuel exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error": exc.__class__.__name__
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    if settings.DEBUG:
        import traceback
        print(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    db_status = "ok"
    redis_status = "ok"
    
    try:
        # Check Redis
        if not redis_client.client or not redis_client.client.ping():
            redis_status = "error"
    except Exception:
        redis_status = "error"
    
    # TODO: Add database health check
    
    overall_status = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    
    return {
        "status": overall_status,
        "db": db_status,
        "redis": redis_status,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }


@app.get("/metrics", tags=["Health"])
async def metrics():
    """Prometheus metrics endpoint (placeholder)"""
    # TODO: Implement Prometheus metrics
    return {"message": "Metrics endpoint - to be implemented"}


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to DreamDuel API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
