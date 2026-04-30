from typing import Literal

from pydantic import BaseModel, Field


class TempleSubscriptionCreateRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=32)
    temple_id: str = Field(..., min_length=3, max_length=20)
    requester_name: str = Field(..., min_length=2, max_length=100)


class TempleSubscriptionResponse(BaseModel):
    subscription_id: str
    user_id: str
    temple_id: str
    temple_name: str
    requester_name: str
    status: Literal["pending"]
    phase: str = "temple_subscription"


class TempleSubscriptionItem(BaseModel):
    subscription_id: str
    user_id: str
    temple_id: str
    temple_name: str
    requester_name: str
    status: Literal["pending", "approved", "rejected"]
    rejection_reason: str | None = None
    requested_at: str
    reviewed_at: str | None = None
    phase: str = "temple_subscription"


class TempleSubscriptionListResponse(BaseModel):
    items: list[TempleSubscriptionItem]
    phase: str = "temple_subscription"
