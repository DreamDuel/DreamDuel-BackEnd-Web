"""Main FastAPI application — Guest checkout only"""

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
from app.infrastructure.database.session import init_db, get_db
from app.infrastructure.cache.redis_client import redis_client
from app.api.router import api_router
from app.api.v1.routes import generate as generate_router
from app.api.v1.routes import payments as payments_router
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import Depends


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    print("🚀 Starting DreamDuel API...")

    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            integrations=[FastApiIntegration()],
            traces_sample_rate=1.0 if settings.DEBUG else 0.1,
        )

    redis_client.connect()
    print("✅ Redis connected")

    if settings.DEBUG:
        init_db()
        print("✅ Database initialized")

    yield

    print("👋 Shutting down DreamDuel API...")
    redis_client.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for DreamDuel — AI-powered image generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)


# Exception handlers
@app.exception_handler(DreamDuelException)
async def dreamduel_exception_handler(request: Request, exc: DreamDuelException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error": exc.__class__.__name__}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        import traceback
        print(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc) if settings.DEBUG else "An unexpected error occurred"}
    )


# Health check
@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    db_status = "ok"
    redis_status = "ok"

    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "error"
        print(f"Database health check failed: {e}")

    try:
        if not redis_client.client or not redis_client.client.ping():
            redis_status = "error"
    except Exception as e:
        redis_status = "error"
        print(f"Redis health check failed: {e}")

    overall_status = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"

    return {
        "status": overall_status,
        "db": db_status,
        "redis": redis_status,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }


# Routers — with /api prefix
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Routers — without prefix (frontend compatibility)
app.include_router(generate_router.router, prefix="/generate", tags=["AI Image Generation"])
app.include_router(payments_router.router, prefix="/payments", tags=["Payments"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to DreamDuel API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
