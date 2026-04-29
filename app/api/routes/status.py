from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/status")
async def gateway_status() -> dict[str, object]:
    settings = get_settings()
    return {
        "service": "temple-api-gateway",
        "environment": settings.environment,
        "downstream_services": {
            "identity": settings.identity_service_url,
            "registration": settings.registration_service_url,
            "admin": settings.admin_service_url,
        },
        "phase": "scaffold",
    }

