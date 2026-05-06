import asyncio
import httpx
from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import get_settings
from app.schemas.signup_request import (
    DonationCreateRequest,
    DonationListResponse,
    DonationResponse,
    MemberActivityListResponse,
    PaymentSubmissionCreateRequest,
    PaymentSubmissionResponse,
    ShantidharaBookingCreateRequest,
    ShantidharaBookingListResponse,
    ShantidharaBookingResponse,
    TempleSubscriptionCreateRequest,
    TempleSubscriptionListResponse,
    TempleSubscriptionResponse,
)

router = APIRouter()


def _retry_delay_seconds(attempt: int) -> float:
    return min(12.0, float(2 ** attempt))


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
                await asyncio.sleep(_retry_delay_seconds(attempt + 1))
                continue
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach registration service",
            ) from exc

        if response.status_code >= 500:
            if attempt < attempts - 1:
                await asyncio.sleep(_retry_delay_seconds(attempt + 1))
                continue
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Registration service returned an unexpected error",
            )

        break
    else:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to reach registration service",
        ) from last_error

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


@router.post("/shantidhara-bookings", response_model=ShantidharaBookingResponse)
async def create_shantidhara_booking(
    payload: ShantidharaBookingCreateRequest,
) -> ShantidharaBookingResponse:
    settings = get_settings()
    body = await _forward_request(
        method="POST",
        url=f"{settings.registration_service_url}/api/v1/temple-subscriptions/shantidhara-bookings",
        body=payload.model_dump(),
    )
    return ShantidharaBookingResponse.model_validate(body)


@router.get("/shantidhara-bookings/me", response_model=ShantidharaBookingListResponse)
async def list_my_shantidhara_bookings(
    user_id: str = Query(..., min_length=3),
    temple_id: str | None = Query(default=None),
) -> ShantidharaBookingListResponse:
    settings = get_settings()
    suffix = f"&temple_id={temple_id}" if temple_id else ""
    body = await _forward_request(
        method="GET",
        url=(
            f"{settings.registration_service_url}/api/v1/temple-subscriptions/shantidhara-bookings/me"
            f"?user_id={user_id}{suffix}"
        ),
    )
    return ShantidharaBookingListResponse.model_validate(body)


@router.post(
    "/shantidhara-bookings/{booking_id}/payment-submission",
    response_model=PaymentSubmissionResponse,
)
async def submit_shantidhara_payment(
    booking_id: str,
    payload: PaymentSubmissionCreateRequest,
) -> PaymentSubmissionResponse:
    settings = get_settings()
    body = await _forward_request(
        method="POST",
        url=(
            f"{settings.registration_service_url}/api/v1/temple-subscriptions/"
            f"shantidhara-bookings/{booking_id}/payment-submission"
        ),
        body=payload.model_dump(),
    )
    return PaymentSubmissionResponse.model_validate(body)


@router.post("/donations", response_model=DonationResponse)
async def create_donation(payload: DonationCreateRequest) -> DonationResponse:
    settings = get_settings()
    body = await _forward_request(
        method="POST",
        url=f"{settings.registration_service_url}/api/v1/temple-subscriptions/donations",
        body=payload.model_dump(),
    )
    return DonationResponse.model_validate(body)


@router.get("/donations/me", response_model=DonationListResponse)
async def list_my_donations(
    user_id: str = Query(..., min_length=3),
    temple_id: str | None = Query(default=None),
) -> DonationListResponse:
    settings = get_settings()
    suffix = f"&temple_id={temple_id}" if temple_id else ""
    body = await _forward_request(
        method="GET",
        url=(
            f"{settings.registration_service_url}/api/v1/temple-subscriptions/donations/me"
            f"?user_id={user_id}{suffix}"
        ),
    )
    return DonationListResponse.model_validate(body)


@router.post(
    "/donations/{donation_id}/payment-submission",
    response_model=PaymentSubmissionResponse,
)
async def submit_donation_payment(
    donation_id: str,
    payload: PaymentSubmissionCreateRequest,
) -> PaymentSubmissionResponse:
    settings = get_settings()
    body = await _forward_request(
        method="POST",
        url=(
            f"{settings.registration_service_url}/api/v1/temple-subscriptions/"
            f"donations/{donation_id}/payment-submission"
        ),
        body=payload.model_dump(),
    )
    return PaymentSubmissionResponse.model_validate(body)


@router.get("/member-activity/me", response_model=MemberActivityListResponse)
async def list_my_member_activity(
    user_id: str = Query(..., min_length=3),
    limit: int = Query(default=20, ge=1, le=50),
) -> MemberActivityListResponse:
    settings = get_settings()
    body = await _forward_request(
        method="GET",
        url=(
            f"{settings.registration_service_url}/api/v1/temple-subscriptions/member-activity/me"
            f"?user_id={user_id}&limit={limit}"
        ),
    )
    return MemberActivityListResponse.model_validate(body)
