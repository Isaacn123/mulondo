import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database import SessionLocal
from app.models.about import AboutSection
from app.schemas.about import AboutContent

BASE_DIR = Path(__file__).resolve().parent.parent
ABOUT_FILE = BASE_DIR / "data" / "about.json"
ABOUT_SLUG = "homepage"


def _load_about_from_json() -> AboutContent:
    with ABOUT_FILE.open(encoding="utf-8") as f:
        return AboutContent.model_validate_json(f.read())


def _save_about_to_json(about: AboutContent) -> AboutContent:
    ABOUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with ABOUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(about.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return about


def _load_about_from_db(db: Session) -> AboutContent:
    row = db.query(AboutSection).filter(AboutSection.slug == ABOUT_SLUG).one()
    return AboutContent.model_validate(row.content)


def _save_about_to_db(db: Session, about: AboutContent) -> AboutContent:
    row = db.query(AboutSection).filter(AboutSection.slug == ABOUT_SLUG).one_or_none()
    payload = about.model_dump()
    if row is None:
        row = AboutSection(slug=ABOUT_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return AboutContent.model_validate(row.content)


def load_about() -> AboutContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _load_about_from_db(db)
        finally:
            db.close()
    return _load_about_from_json()


def save_about(about: AboutContent) -> AboutContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_about_to_db(db, about)
        finally:
            db.close()
    return _save_about_to_json(about)
