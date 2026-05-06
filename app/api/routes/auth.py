import asyncio
import httpx
from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.schemas.auth import (
    PushTokenRegisterRequest,
    PushTokenRegisterResponse,
    SignInRequest,
    SignInResponse,
    SignUpRequest,
    SignUpResponse,
)

router = APIRouter()


def _retry_delay_seconds(attempt: int) -> float:
    return min(12.0, float(2 ** attempt))


async def _forward_auth_request(
    *,
    path: str,
    body: dict[str, object],
    default_error: str,
) -> dict[str, object]:
    settings = get_settings()
    url = f"{settings.identity_service_url}{path}"
    attempts = max(1, settings.upstream_retry_attempts)
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(settings.upstream_timeout_seconds),
            ) as client:
                response = await client.post(url, json=body)
        except httpx.HTTPError as exc:
            last_error = exc
            if attempt < attempts - 1:
                await asyncio.sleep(_retry_delay_seconds(attempt + 1))
                continue
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach identity service",
            ) from exc

        if response.status_code >= 500:
            if attempt < attempts - 1:
                await asyncio.sleep(_retry_delay_seconds(attempt + 1))
                continue
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Identity service returned an unexpected error",
            )

        break
    else:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to reach identity service",
        ) from last_error

    if response.status_code >= 400:
        detail = default_error
        try:
            detail = response.json().get("detail", detail)
        except ValueError:
            pass
        raise HTTPException(status_code=response.status_code, detail=detail)

    return response.json()


@router.post("/signup", response_model=SignUpResponse)
async def signup(payload: SignUpRequest) -> SignUpResponse:
    body = await _forward_auth_request(
        path="/api/v1/auth/signup",
        body=payload.model_dump(),
        default_error="Unable to sign up",
    )
    return SignUpResponse.model_validate(body)


@router.post("/signin", response_model=SignInResponse)
async def signin(payload: SignInRequest) -> SignInResponse:
    body = await _forward_auth_request(
        path="/api/v1/auth/signin",
        body=payload.model_dump(),
        default_error="Unable to sign in",
    )
    return SignInResponse.model_validate(body)


@router.post("/push-tokens/register", response_model=PushTokenRegisterResponse)
async def register_push_token(
    payload: PushTokenRegisterRequest,
) -> PushTokenRegisterResponse:
    body = await _forward_auth_request(
        path="/api/v1/auth/push-tokens/register",
        body=payload.model_dump(),
        default_error="Unable to register push notifications",
    )
    return PushTokenRegisterResponse.model_validate(body)


@router.get("/prewarm")
async def prewarm() -> dict[str, str]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.upstream_timeout_seconds),
        ) as client:
            await client.get(f"{settings.identity_service_url}/health")
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to prewarm identity service",
        ) from exc

    return {"status": "warm"}
