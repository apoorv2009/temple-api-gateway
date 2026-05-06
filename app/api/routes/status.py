import asyncio

import httpx
from fastapi import APIRouter, HTTPException, status

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


@router.get("/status/prewarm-temple-access")
async def prewarm_temple_access() -> dict[str, str]:
    settings = get_settings()

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.upstream_timeout_seconds),
        ) as client:
            await asyncio.gather(
                client.get(f"{settings.registration_service_url}/health"),
                client.get(f"{settings.admin_service_url}/health"),
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to prewarm temple access services",
        ) from exc

    return {"status": "warm"}
