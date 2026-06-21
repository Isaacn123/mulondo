import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database import SessionLocal
from app.models.membership import MembershipSection
from app.schemas.membership import MembershipContent

BASE_DIR = Path(__file__).resolve().parent.parent
MEMBERSHIP_FILE = BASE_DIR / "data" / "membership.json"
MEMBERSHIP_SLUG = "homepage"


def _load_membership_from_json() -> MembershipContent:
    with MEMBERSHIP_FILE.open(encoding="utf-8") as f:
        return MembershipContent.model_validate_json(f.read())


def _save_membership_to_json(membership: MembershipContent) -> MembershipContent:
    MEMBERSHIP_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MEMBERSHIP_FILE.open("w", encoding="utf-8") as f:
        json.dump(membership.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return membership


def _load_membership_from_db(db: Session) -> MembershipContent:
    row = db.query(MembershipSection).filter(MembershipSection.slug == MEMBERSHIP_SLUG).one()
    return MembershipContent.model_validate(row.content)


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
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _load_membership_from_db(db)
        finally:
            db.close()
    return _load_membership_from_json()


def save_membership(membership: MembershipContent) -> MembershipContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_membership_to_db(db, membership)
        finally:
            db.close()
    return _save_membership_to_json(membership)
