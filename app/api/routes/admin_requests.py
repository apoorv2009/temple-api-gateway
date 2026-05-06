import asyncio

import httpx
from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import get_settings
from app.schemas.admin_request import (
    ApprovalRequest,
    ApprovalResponse,
    RejectRequest,
    RejectResponse,
    TempleSubscriptionItem,
    TempleSubscriptionListResponse,
)

router = APIRouter()


def _retry_delay_seconds(attempt: int) -> float:
    return min(12.0, float(2 ** attempt))


async def _forward_request(
    *,
    method: str,
    url: str,
    downstream_name: str,
    default_error: str,
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
                await asyncio.sleep(_retry_delay_seconds(attempt + 1))
                continue
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to reach {downstream_name}",
            ) from exc

        if response.status_code >= 500:
            if attempt < attempts - 1:
                await asyncio.sleep(_retry_delay_seconds(attempt + 1))
                continue
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{downstream_name.capitalize()} returned an unexpected error",
            )

        if response.status_code >= 400:
            detail = default_error
            try:
                detail = response.json().get("detail", detail)
            except ValueError:
                pass
            raise HTTPException(status_code=response.status_code, detail=detail)

        return response.json()

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Unable to reach {downstream_name}",
    ) from last_error


@router.get("", response_model=TempleSubscriptionListResponse)
async def list_temple_subscriptions(
    temple_id: str = Query(..., min_length=3),
    status_filter: str = Query(default="pending"),
) -> TempleSubscriptionListResponse:
    settings = get_settings()
    body = await _forward_request(
        method="GET",
        url=(
            f"{settings.registration_service_url}/api/v1/temple-subscriptions/admin/list"
            f"?temple_id={temple_id}&status_filter={status_filter}"
        ),
        downstream_name="registration service",
        default_error="Unable to load temple subscription requests",
    )
    return TempleSubscriptionListResponse.model_validate(body)


@router.post("/{subscription_id}/approve", response_model=ApprovalResponse)
async def approve_temple_subscription(
    subscription_id: str,
    payload: ApprovalRequest,
) -> ApprovalResponse:
    settings = get_settings()

    current = await _forward_request(
        method="GET",
        url=(
            f"{settings.registration_service_url}/api/v1/temple-subscriptions/admin/list"
            f"?temple_id={payload.temple_id}&status_filter=pending"
        ),
        downstream_name="registration service",
        default_error="Unable to load temple subscription requests",
    )
    matching = [
        item for item in current.get("items", []) if item.get("subscription_id") == subscription_id
    ]
    if not matching:
        raise HTTPException(status_code=403, detail="Temple admin cannot approve another temple's request")

    approved_body = await _forward_request(
        method="POST",
        url=f"{settings.registration_service_url}/api/v1/temple-subscriptions/admin/{subscription_id}/approve",
        body={},
        downstream_name="registration service",
        default_error="Unable to approve temple subscription request",
    )
    item = TempleSubscriptionItem.model_validate(approved_body)

    await _forward_request(
        method="POST",
        url=f"{settings.identity_service_url}/api/v1/auth/internal/devotees/assign-temple",
        body={
            "user_id": item.user_id,
            "temple_id": item.temple_id,
            "temple_name": item.temple_name,
        },
        downstream_name="identity service",
        default_error="Temple request was approved, but the devotee profile could not be updated",
    )

    return ApprovalResponse(
        subscription_id=item.subscription_id,
        status="approved",
        temple_id=item.temple_id,
    )


@router.post("/{subscription_id}/reject", response_model=RejectResponse)
async def reject_temple_subscription(
    subscription_id: str,
    payload: RejectRequest,
) -> RejectResponse:
    settings = get_settings()
    current = await _forward_request(
        method="GET",
        url=(
            f"{settings.registration_service_url}/api/v1/temple-subscriptions/admin/list"
            f"?temple_id={payload.temple_id}&status_filter=pending"
        ),
        downstream_name="registration service",
        default_error="Unable to load temple subscription requests",
    )
    matching = [
        item for item in current.get("items", []) if item.get("subscription_id") == subscription_id
    ]
    if not matching:
        raise HTTPException(status_code=403, detail="Temple admin cannot reject another temple's request")

    await _forward_request(
        method="POST",
        url=f"{settings.registration_service_url}/api/v1/temple-subscriptions/admin/{subscription_id}/reject",
        body={"reason": payload.reason},
        downstream_name="registration service",
        default_error="Unable to reject temple subscription request",
    )
    return RejectResponse(
        subscription_id=subscription_id,
        status="rejected",
        reason=payload.reason,
        temple_id=payload.temple_id,
    )
