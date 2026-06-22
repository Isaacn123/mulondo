from sqlalchemy import JSON, Column, DateTime, Integer, String, func

from app.database import Base


class MentorshipSection(Base):
    __tablename__ = "mentorship_sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(64), unique=True, nullable=False)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
