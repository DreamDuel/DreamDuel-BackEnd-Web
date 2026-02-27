"""API router configuration"""

from fastapi import APIRouter
from app.api.v1.routes import (
    auth, users, payments, upload, generate, analytics, oauth
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(oauth.router, prefix="/oauth", tags=["OAuth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(generate.router, prefix="/generate", tags=["AI Image Generation"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
