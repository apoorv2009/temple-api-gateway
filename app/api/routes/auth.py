import httpx
from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.schemas.auth import SignInRequest, SignInResponse, SignUpRequest, SignUpResponse

router = APIRouter()


async def _forward_auth_request(
    *,
    path: str,
    body: dict[str, object],
    default_error: str,
) -> dict[str, object]:
    settings = get_settings()
    url = f"{settings.identity_service_url}{path}"

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.upstream_timeout_seconds),
        ) as client:
            response = await client.post(url, json=body)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to reach identity service",
        ) from exc

    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Identity service returned an unexpected error",
        )

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
