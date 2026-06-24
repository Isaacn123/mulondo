from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

KYC_STATUS_DRAFT = "draft"
KYC_STATUS_PENDING = "pending"
KYC_STATUS_APPROVED = "approved"
KYC_STATUS_REJECTED = "rejected"


class KycSubmission(Base):
    __tablename__ = "kyc_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    portal_role: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=KYC_STATUS_DRAFT, index=True)
    legal_full_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    id_number: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    government_id_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    government_id_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    proof_of_address_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    proof_of_address_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    member_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    admin_seen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="kyc_submission")
