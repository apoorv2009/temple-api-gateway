from fastapi import APIRouter

from app.api.routes import admin_requests, auth, health, status, temples
from app.api.routes import signup_requests as temple_subscriptions

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(status.router, prefix="/api/v1", tags=["status"])
api_router.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
api_router.include_router(temples.router, prefix="/api/v1/temples", tags=["temples"])
api_router.include_router(
    temple_subscriptions.router,
    prefix="/api/v1/temple-subscriptions",
    tags=["temple-subscriptions"],
)
api_router.include_router(
    admin_requests.router,
    prefix="/api/v1/admin/temple-subscriptions",
    tags=["admin-temple-subscriptions"],
)
