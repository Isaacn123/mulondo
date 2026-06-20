import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database import SessionLocal
from app.models.philosophy import PhilosophySection
from app.schemas.philosophy import PhilosophyContent

BASE_DIR = Path(__file__).resolve().parent.parent
PHILOSOPHY_FILE = BASE_DIR / "data" / "philosophy.json"
PHILOSOPHY_SLUG = "homepage"


def _load_philosophy_from_json() -> PhilosophyContent:
    with PHILOSOPHY_FILE.open(encoding="utf-8") as f:
        return PhilosophyContent.model_validate_json(f.read())


def _save_philosophy_to_json(philosophy: PhilosophyContent) -> PhilosophyContent:
    PHILOSOPHY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PHILOSOPHY_FILE.open("w", encoding="utf-8") as f:
        json.dump(philosophy.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return philosophy


def _load_philosophy_from_db(db: Session) -> PhilosophyContent:
    row = db.query(PhilosophySection).filter(PhilosophySection.slug == PHILOSOPHY_SLUG).one()
    return PhilosophyContent.model_validate(row.content)


def _save_philosophy_to_db(db: Session, philosophy: PhilosophyContent) -> PhilosophyContent:
    row = db.query(PhilosophySection).filter(PhilosophySection.slug == PHILOSOPHY_SLUG).one_or_none()
    payload = philosophy.model_dump()
    if row is None:
        row = PhilosophySection(slug=PHILOSOPHY_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return PhilosophyContent.model_validate(row.content)


def load_philosophy() -> PhilosophyContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _load_philosophy_from_db(db)
        finally:
            db.close()
    return _load_philosophy_from_json()


def save_philosophy(philosophy: PhilosophyContent) -> PhilosophyContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_philosophy_to_db(db, philosophy)
        finally:
            db.close()
    return _save_philosophy_to_json(philosophy)
