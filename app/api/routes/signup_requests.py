import httpx
from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import get_settings
from app.schemas.signup_request import (
    TempleSubscriptionCreateRequest,
    TempleSubscriptionListResponse,
    TempleSubscriptionResponse,
)

router = APIRouter()


async def _forward_request(
    *,
    method: str,
    url: str,
    body: dict[str, object] | None = None,
) -> dict[str, object]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(method=method, url=url, json=body)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to reach registration service",
        ) from exc

    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Registration service returned an unexpected error",
        )

    if response.status_code >= 400:
        detail = "Unable to process temple subscription"
        try:
            detail = response.json().get("detail", detail)
        except ValueError:
            pass
        raise HTTPException(status_code=response.status_code, detail=detail)

    return response.json()


@router.post("", response_model=TempleSubscriptionResponse)
async def create_temple_subscription(
    payload: TempleSubscriptionCreateRequest,
) -> TempleSubscriptionResponse:
    settings = get_settings()
    body = await _forward_request(
        method="POST",
        url=f"{settings.registration_service_url}/api/v1/temple-subscriptions",
        body=payload.model_dump(),
    )
    return TempleSubscriptionResponse.model_validate(body)


@router.get("/me", response_model=TempleSubscriptionListResponse)
async def list_my_temple_subscriptions(
    user_id: str = Query(..., min_length=3),
) -> TempleSubscriptionListResponse:
    settings = get_settings()
    body = await _forward_request(
        method="GET",
        url=f"{settings.registration_service_url}/api/v1/temple-subscriptions/me?user_id={user_id}",
    )
    return TempleSubscriptionListResponse.model_validate(body)
