import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content, load_json_model
from app.database import SessionLocal
from app.models.about import AboutSection
from app.schemas.about import AboutContent
from app.schemas.content_defaults import default_about

BASE_DIR = Path(__file__).resolve().parent.parent
ABOUT_FILE = BASE_DIR / "data" / "about.json"
ABOUT_SLUG = "homepage"


def _load_about_from_db(db: Session) -> AboutContent | None:
    row = db.query(AboutSection).filter(AboutSection.slug == ABOUT_SLUG).one_or_none()
    if row is None:
        return None
    return AboutContent.model_validate(row.content)


def _save_about_to_json(about: AboutContent) -> AboutContent:
    ABOUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with ABOUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(about.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return about


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
    return load_cms_content(
        model=AboutContent,
        json_path=ABOUT_FILE,
        db_loader=_load_about_from_db,
        default_factory=default_about,
    )


def save_about(about: AboutContent) -> AboutContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_about_to_db(db, about)
        finally:
            db.close()
    return _save_about_to_json(about)
