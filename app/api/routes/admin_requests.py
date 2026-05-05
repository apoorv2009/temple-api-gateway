import asyncio
import httpx
from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import get_settings
from app.schemas.admin_request import (
    ApprovalRequest,
    ApprovalResponse,
    RejectRequest,
    RejectResponse,
    TempleSubscriptionListResponse,
)

router = APIRouter()


async def _forward_request(
    *,
    method: str,
    url: str,
    body: dict[str, object] | None = None,
) -> dict[str, object]:
    settings = get_settings()
    attempts = max(1, settings.upstream_retry_attempts)
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(settings.upstream_timeout_seconds),
            ) as client:
                response = await client.request(method=method, url=url, json=body)
        except httpx.HTTPError as exc:
            last_error = exc
            if attempt < attempts - 1:
                await asyncio.sleep(1 + attempt)
                continue
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach admin service",
            ) from exc

        if response.status_code >= 500:
            if attempt < attempts - 1:
                await asyncio.sleep(1 + attempt)
                continue
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Admin service returned an unexpected error",
            )

        break
    else:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to reach admin service",
        ) from last_error

    if response.status_code >= 400:
        detail = "Unable to process temple subscription admin request"
        try:
            body_data = response.json()
            detail = body_data.get("detail", detail)
        except ValueError:
            pass
        raise HTTPException(status_code=response.status_code, detail=detail)

    return response.json()


@router.get("", response_model=TempleSubscriptionListResponse)
async def list_temple_subscriptions(
    temple_id: str = Query(..., min_length=3),
    status_filter: str = Query(default="pending"),
) -> TempleSubscriptionListResponse:
    settings = get_settings()
    body = await _forward_request(
        method="GET",
        url=(
            f"{settings.admin_service_url}/api/v1/admin/temple-subscriptions"
            f"?temple_id={temple_id}&status_filter={status_filter}"
        ),
    )
    return TempleSubscriptionListResponse.model_validate(body)


@router.post("/{subscription_id}/approve", response_model=ApprovalResponse)
async def approve_temple_subscription(
    subscription_id: str,
    payload: ApprovalRequest,
) -> ApprovalResponse:
    settings = get_settings()
    body = await _forward_request(
        method="POST",
        url=f"{settings.admin_service_url}/api/v1/admin/temple-subscriptions/{subscription_id}/approve",
        body=payload.model_dump(),
    )
    return ApprovalResponse.model_validate(body)


@router.post("/{subscription_id}/reject", response_model=RejectResponse)
async def reject_temple_subscription(
    subscription_id: str,
    payload: RejectRequest,
) -> RejectResponse:
    settings = get_settings()
    body = await _forward_request(
        method="POST",
        url=f"{settings.admin_service_url}/api/v1/admin/temple-subscriptions/{subscription_id}/reject",
        body=payload.model_dump(),
    )
    return RejectResponse.model_validate(body)
