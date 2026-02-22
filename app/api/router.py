"""API router configuration"""

from fastapi import APIRouter
from app.api.v1.routes import (
    auth, users, stories, comments, 
    payments, upload, generate, analytics
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(stories.router, prefix="/stories", tags=["Stories"])
api_router.include_router(comments.router, prefix="/comments", tags=["Comments"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(generate.router, prefix="/generate", tags=["AI Generation (Placeholder)"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
