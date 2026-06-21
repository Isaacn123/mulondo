import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content
from app.database import SessionLocal
from app.models.philosophy import PhilosophySection
from app.schemas.content_defaults import default_philosophy
from app.schemas.philosophy import PhilosophyContent

BASE_DIR = Path(__file__).resolve().parent.parent
PHILOSOPHY_FILE = BASE_DIR / "data" / "philosophy.json"
PHILOSOPHY_SLUG = "homepage"


def _load_philosophy_from_db(db: Session) -> PhilosophyContent | None:
    row = db.query(PhilosophySection).filter(PhilosophySection.slug == PHILOSOPHY_SLUG).one_or_none()
    if row is None:
        return None
    return PhilosophyContent.model_validate(row.content)


def _save_philosophy_to_json(philosophy: PhilosophyContent) -> PhilosophyContent:
    PHILOSOPHY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PHILOSOPHY_FILE.open("w", encoding="utf-8") as f:
        json.dump(philosophy.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return philosophy


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
    return load_cms_content(
        model=PhilosophyContent,
        json_path=PHILOSOPHY_FILE,
        db_loader=_load_philosophy_from_db,
        default_factory=default_philosophy,
    )


def save_philosophy(philosophy: PhilosophyContent) -> PhilosophyContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_philosophy_to_db(db, philosophy)
        finally:
            db.close()
    return _save_philosophy_to_json(philosophy)
