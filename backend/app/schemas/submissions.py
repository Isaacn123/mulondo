from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ContactSubmissionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    country: str = ""
    investor_type: str = ""
    capital_range: str = ""
    message: str = ""


class MembershipRequestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    phone: str = ""
    country: str = ""
    tier: str = ""
    message: str = ""


class SubmissionResponse(BaseModel):
    ok: bool = True
    message: str = "Thank you. We received your request and will respond shortly."


class ContactSubmissionOut(BaseModel):
    id: int
    name: str
    email: str
    country: str
    investor_type: str
    capital_range: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MembershipRequestOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    country: str
    tier: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationItem(BaseModel):
    id: int
    kind: str
    title: str
    subtitle: str
    created_at: datetime
    admin_url: str


class NotificationSummary(BaseModel):
    unread_total: int = 0
    unread_contact: int = 0
    unread_membership: int = 0
    recent: list[NotificationItem] = Field(default_factory=list)
