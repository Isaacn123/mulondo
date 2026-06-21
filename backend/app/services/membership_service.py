import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content
from app.database import SessionLocal
from app.models.membership import MembershipSection
from app.schemas.content_defaults import default_membership
from app.schemas.membership import MembershipContent

BASE_DIR = Path(__file__).resolve().parent.parent
MEMBERSHIP_FILE = BASE_DIR / "data" / "membership.json"
MEMBERSHIP_SLUG = "homepage"


def _load_membership_from_db(db: Session) -> MembershipContent | None:
    row = db.query(MembershipSection).filter(MembershipSection.slug == MEMBERSHIP_SLUG).one_or_none()
    if row is None:
        return None
    return MembershipContent.model_validate(row.content)


def _save_membership_to_json(membership: MembershipContent) -> MembershipContent:
    MEMBERSHIP_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MEMBERSHIP_FILE.open("w", encoding="utf-8") as f:
        json.dump(membership.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return membership


def _save_membership_to_db(db: Session, membership: MembershipContent) -> MembershipContent:
    row = db.query(MembershipSection).filter(MembershipSection.slug == MEMBERSHIP_SLUG).one_or_none()
    payload = membership.model_dump()
    if row is None:
        row = MembershipSection(slug=MEMBERSHIP_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return MembershipContent.model_validate(row.content)


def load_membership() -> MembershipContent:
    return load_cms_content(
        model=MembershipContent,
        json_path=MEMBERSHIP_FILE,
        db_loader=_load_membership_from_db,
        default_factory=default_membership,
    )


def save_membership(membership: MembershipContent) -> MembershipContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_membership_to_db(db, membership)
        finally:
            db.close()
    return _save_membership_to_json(membership)
