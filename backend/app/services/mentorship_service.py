import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content
from app.database import SessionLocal
from app.models.mentorship import MentorshipSection
from app.schemas.content_defaults import default_mentorship
from app.schemas.mentorship import MentorshipContent

BASE_DIR = Path(__file__).resolve().parent.parent
MENTORSHIP_FILE = BASE_DIR / "data" / "mentorship.json"
MENTORSHIP_SLUG = "homepage"


def _load_mentorship_from_db(db: Session) -> MentorshipContent | None:
    row = db.query(MentorshipSection).filter(MentorshipSection.slug == MENTORSHIP_SLUG).one_or_none()
    if row is None:
        return None
    return MentorshipContent.model_validate(row.content)


def _save_mentorship_to_json(mentorship: MentorshipContent) -> MentorshipContent:
    MENTORSHIP_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MENTORSHIP_FILE.open("w", encoding="utf-8") as f:
        json.dump(mentorship.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return mentorship


def _save_mentorship_to_db(db: Session, mentorship: MentorshipContent) -> MentorshipContent:
    row = db.query(MentorshipSection).filter(MentorshipSection.slug == MENTORSHIP_SLUG).one_or_none()
    payload = mentorship.model_dump()
    if row is None:
        row = MentorshipSection(slug=MENTORSHIP_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return MentorshipContent.model_validate(row.content)


def load_mentorship() -> MentorshipContent:
    return load_cms_content(
        model=MentorshipContent,
        json_path=MENTORSHIP_FILE,
        db_loader=_load_mentorship_from_db,
        default_factory=default_mentorship,
    )


def save_mentorship(mentorship: MentorshipContent) -> MentorshipContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_mentorship_to_db(db, mentorship)
        finally:
            db.close()
    return _save_mentorship_to_json(mentorship)
