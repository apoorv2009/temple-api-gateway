from typing import Literal

from pydantic import BaseModel, Field


class SignUpRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    contact_number: str = Field(..., min_length=10, max_length=20)
    native_city: str = Field(..., min_length=2, max_length=100)
    local_area: str = Field(..., min_length=2, max_length=100)
    occupation: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class SignUpResponse(BaseModel):
    user_id: str
    role: Literal["devotee"] = "devotee"
    status: Literal["active"] = "active"
    phase: str = "app_access"


class SignInRequest(BaseModel):
    contact_number: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)


class SignInResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: Literal["devotee", "admin"]
    user_id: str
    display_name: str
    temple_id: str | None = None
    temple_name: str | None = None
    phase: str = "app_access"
