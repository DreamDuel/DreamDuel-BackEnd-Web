"""API router — Guest checkout only"""

from fastapi import APIRouter
from app.api.v1.routes import payments, generate

api_router = APIRouter()

api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(generate.router, prefix="/generate", tags=["AI Image Generation"])
