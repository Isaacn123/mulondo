import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database import SessionLocal
from app.models.contact import ContactSection
from app.schemas.contact import ContactContent

BASE_DIR = Path(__file__).resolve().parent.parent
CONTACT_FILE = BASE_DIR / "data" / "contact.json"
CONTACT_SLUG = "homepage"


def _load_contact_from_json() -> ContactContent:
    with CONTACT_FILE.open(encoding="utf-8") as f:
        return ContactContent.model_validate_json(f.read())


def _save_contact_to_json(contact: ContactContent) -> ContactContent:
    CONTACT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONTACT_FILE.open("w", encoding="utf-8") as f:
        json.dump(contact.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return contact


def _load_contact_from_db(db: Session) -> ContactContent:
    row = db.query(ContactSection).filter(ContactSection.slug == CONTACT_SLUG).one()
    return ContactContent.model_validate(row.content)


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
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _load_contact_from_db(db)
        finally:
            db.close()
    return _load_contact_from_json()


def save_contact(contact: ContactContent) -> ContactContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_contact_to_db(db, contact)
        finally:
            db.close()
    return _save_contact_to_json(contact)
