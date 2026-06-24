from datetime import datetime

from pydantic import BaseModel, Field


KYC_STATUSES = ("draft", "pending", "approved", "rejected")
KYC_PORTAL_ROLES = ("investor", "mentee")


class KycSubmissionUpdate(BaseModel):
    legal_full_name: str = ""
    country: str = ""
    id_number: str = ""
    member_notes: str = ""
    government_id_url: str = ""
    government_id_name: str = ""
    proof_of_address_url: str = ""
    proof_of_address_name: str = ""


class KycSubmissionRead(BaseModel):
    id: int
    user_id: int
    portal_role: str
    status: str
    legal_full_name: str
    country: str
    id_number: str
    government_id_url: str
    government_id_name: str
    proof_of_address_url: str
    proof_of_address_name: str
    member_notes: str
    rejection_reason: str
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None

    model_config = {"from_attributes": True}


class KycReviewRequest(BaseModel):
    rejection_reason: str = Field(default="", max_length=2000)
