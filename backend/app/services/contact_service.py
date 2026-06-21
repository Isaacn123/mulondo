import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content
from app.database import SessionLocal
from app.models.contact import ContactSection
from app.schemas.contact import ContactContent
from app.schemas.content_defaults import default_contact

BASE_DIR = Path(__file__).resolve().parent.parent
CONTACT_FILE = BASE_DIR / "data" / "contact.json"
CONTACT_SLUG = "homepage"


def _load_contact_from_db(db: Session) -> ContactContent | None:
    row = db.query(ContactSection).filter(ContactSection.slug == CONTACT_SLUG).one_or_none()
    if row is None:
        return None
    return ContactContent.model_validate(row.content)


def _save_contact_to_json(contact: ContactContent) -> ContactContent:
    CONTACT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONTACT_FILE.open("w", encoding="utf-8") as f:
        json.dump(contact.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return contact


def _save_contact_to_db(db: Session, contact: ContactContent) -> ContactContent:
    row = db.query(ContactSection).filter(ContactSection.slug == CONTACT_SLUG).one_or_none()
    payload = contact.model_dump()
    if row is None:
        row = ContactSection(slug=CONTACT_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return ContactContent.model_validate(row.content)


def load_contact() -> ContactContent:
    return load_cms_content(
        model=ContactContent,
        json_path=CONTACT_FILE,
        db_loader=_load_contact_from_db,
        default_factory=default_contact,
    )


def save_contact(contact: ContactContent) -> ContactContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_contact_to_db(db, contact)
        finally:
            db.close()
    return _save_contact_to_json(contact)
