"""Main FastAPI application"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.core.config import settings
from app.core.exceptions import DreamDuelException
from app.api.router import api_router
from app.api.v1.routes import generate as generate_router
from app.api.v1.routes import upload as upload_router


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
    
    # Database initialized conditionally - bypassed for stateless setup
    
    yield
    
    # Shutdown
    print("👋 Shutting down DreamDuel API...")


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
cors_origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
# Always allow localhost for local development
localhost_origins = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]
all_origins = list(set(cors_origins + localhost_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Health check endpoint - verifies stateles app connections"""
    redis_status = "skipped"
    db_status = "skipped"
    
    overall_status = "ok"
    
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


# Include API router (with /api prefix)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Also include routes WITHOUT prefix for frontend compatibility
# Frontend calls /generate directly
app.include_router(generate_router.router, prefix="/generate", tags=["AI Image Generation (root)"])
app.include_router(upload_router.router, prefix="/api/upload/image", tags=["Upload (Stateless)"])
app.include_router(upload_router.router, prefix="/upload/image", tags=["Upload (Stateless Direct)"])


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
