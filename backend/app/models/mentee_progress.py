from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MenteeModuleProgress(Base):
    __tablename__ = "mentee_module_progress"
    __table_args__ = (UniqueConstraint("user_id", "module_key", name="uq_mentee_module"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    module_key: Mapped[str] = mapped_column(String(32), nullable=False)
    reading_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quiz_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quiz_score_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_awarded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
