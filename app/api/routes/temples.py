import httpx
from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import get_settings
from app.schemas.temple import (
    ActiveTempleListResponse,
    BulkTempleAdminCreateRequest,
    BulkTempleAdminCreateResponse,
    ShantidharaSlotListResponse,
    LeadershipMemberCreateRequest,
    LeadershipMemberResponse,
    TempleNewsFeedListResponse,
    TempleCreateRequest,
    TempleDetailResponse,
    TempleResponse,
    TempleWallOfFameListResponse,
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
            detail="Unable to reach admin service",
        ) from exc

    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Admin service returned an unexpected error",
        )

    if response.status_code >= 400:
        detail = "Admin service request failed"
        try:
            detail = response.json().get("detail", detail)
        except ValueError:
            pass
        raise HTTPException(status_code=response.status_code, detail=detail)

    return response.json()


@router.post("", response_model=TempleResponse)
async def create_temple(payload: TempleCreateRequest) -> TempleResponse:
    settings = get_settings()
    body = await _forward_request(
        method="POST",
        url=f"{settings.admin_service_url}/api/v1/temples",
        body=payload.model_dump(),
    )
    return TempleResponse.model_validate(body)


@router.get("/active", response_model=ActiveTempleListResponse)
async def list_active_temples() -> ActiveTempleListResponse:
    settings = get_settings()
    body = await _forward_request(
        method="GET",
        url=f"{settings.admin_service_url}/api/v1/temples/active",
    )
    return ActiveTempleListResponse.model_validate(body)


@router.get("/{temple_id}", response_model=TempleDetailResponse)
async def get_temple(temple_id: str) -> TempleDetailResponse:
    settings = get_settings()
    body = await _forward_request(
        method="GET",
        url=f"{settings.admin_service_url}/api/v1/temples/{temple_id}",
    )
    return TempleDetailResponse.model_validate(body)


@router.post(
    "/{temple_id}/leadership-members",
    response_model=LeadershipMemberResponse,
)
async def add_leadership_member(
    temple_id: str,
    payload: LeadershipMemberCreateRequest,
) -> LeadershipMemberResponse:
    settings = get_settings()
    body = await _forward_request(
        method="POST",
        url=f"{settings.admin_service_url}/api/v1/temples/{temple_id}/leadership-members",
        body=payload.model_dump(),
    )
    return LeadershipMemberResponse.model_validate(body)


@router.post(
    "/{temple_id}/admins/bulk",
    response_model=BulkTempleAdminCreateResponse,
)
async def bulk_add_temple_admins(
    temple_id: str,
    payload: BulkTempleAdminCreateRequest,
) -> BulkTempleAdminCreateResponse:
    settings = get_settings()
    body = await _forward_request(
        method="POST",
        url=f"{settings.admin_service_url}/api/v1/temples/{temple_id}/admins/bulk",
        body=payload.model_dump(),
    )
    return BulkTempleAdminCreateResponse.model_validate(body)


@router.post("/{temple_id}/activate", response_model=TempleResponse)
async def activate_temple(temple_id: str) -> TempleResponse:
    settings = get_settings()
    body = await _forward_request(
        method="POST",
        url=f"{settings.admin_service_url}/api/v1/temples/{temple_id}/activate",
    )
    return TempleResponse.model_validate(body)


@router.get("/{temple_id}/news-feed", response_model=TempleNewsFeedListResponse)
async def list_temple_news_feed(temple_id: str) -> TempleNewsFeedListResponse:
    settings = get_settings()
    body = await _forward_request(
        method="GET",
        url=f"{settings.admin_service_url}/api/v1/temples/{temple_id}/news-feed",
    )
    return TempleNewsFeedListResponse.model_validate(body)


@router.get("/{temple_id}/wall-of-fame", response_model=TempleWallOfFameListResponse)
async def list_temple_wall_of_fame(temple_id: str) -> TempleWallOfFameListResponse:
    settings = get_settings()
    body = await _forward_request(
        method="GET",
        url=f"{settings.admin_service_url}/api/v1/temples/{temple_id}/wall-of-fame",
    )
    return TempleWallOfFameListResponse.model_validate(body)


@router.get("/{temple_id}/shantidhara/slots", response_model=ShantidharaSlotListResponse)
async def list_shantidhara_slots(
    temple_id: str,
    slot_date: str | None = Query(default=None),
) -> ShantidharaSlotListResponse:
    settings = get_settings()
    suffix = f"?slot_date={slot_date}" if slot_date else ""
    body = await _forward_request(
        method="GET",
        url=f"{settings.admin_service_url}/api/v1/temples/{temple_id}/shantidhara/slots{suffix}",
    )
    return ShantidharaSlotListResponse.model_validate(body)
