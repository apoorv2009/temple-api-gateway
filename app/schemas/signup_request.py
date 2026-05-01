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


class ShantidharaBookingCreateRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=32)
    temple_id: str = Field(..., min_length=3, max_length=20)
    slot_id: str = Field(..., min_length=3, max_length=32)


class ShantidharaBookingResponse(BaseModel):
    booking_id: str
    user_id: str
    temple_id: str
    temple_name: str
    slot_id: str
    slot_label: str
    slot_date: str
    amount_label: str
    status: Literal["payment_pending"]
    payment_id: str
    phase: str = "temple_booking"


class ShantidharaBookingItem(BaseModel):
    booking_id: str
    user_id: str
    temple_id: str
    temple_name: str
    slot_id: str
    slot_label: str
    slot_date: str
    amount_label: str
    status: Literal["payment_pending", "confirmed", "cancelled"]
    created_at: str
    phase: str = "temple_booking"


class ShantidharaBookingListResponse(BaseModel):
    items: list[ShantidharaBookingItem]
    phase: str = "temple_booking"


class DonationCreateRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=32)
    temple_id: str = Field(..., min_length=3, max_length=20)
    donation_type: Literal["monthly", "one_time"]
    amount_label: str = Field(..., min_length=2, max_length=40)


class DonationResponse(BaseModel):
    donation_id: str
    user_id: str
    temple_id: str
    temple_name: str
    donation_type: Literal["monthly", "one_time"]
    amount_label: str
    status: Literal["payment_pending"]
    payment_id: str
    phase: str = "temple_donation"


class DonationItem(BaseModel):
    donation_id: str
    user_id: str
    temple_id: str
    temple_name: str
    donation_type: Literal["monthly", "one_time"]
    amount_label: str
    status: Literal["payment_pending", "paid", "cancelled"]
    created_at: str
    phase: str = "temple_donation"


class DonationListResponse(BaseModel):
    items: list[DonationItem]
    phase: str = "temple_donation"
