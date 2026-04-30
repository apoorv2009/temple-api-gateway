import httpx
from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.schemas.temple import (
    ActiveTempleListResponse,
    BulkTempleAdminCreateRequest,
    BulkTempleAdminCreateResponse,
    LeadershipMemberCreateRequest,
    LeadershipMemberResponse,
    TempleCreateRequest,
    TempleDetailResponse,
    TempleResponse,
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
