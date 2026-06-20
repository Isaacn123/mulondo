import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database import SessionLocal
from app.models.hero import HeroSection
from app.schemas.hero import HeroContent

BASE_DIR = Path(__file__).resolve().parent.parent
HERO_FILE = BASE_DIR / "data" / "hero.json"
HERO_SLUG = "homepage"


def _load_hero_from_json() -> HeroContent:
    with HERO_FILE.open(encoding="utf-8") as f:
        return HeroContent.model_validate_json(f.read())


def _save_hero_to_json(hero: HeroContent) -> HeroContent:
    HERO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HERO_FILE.open("w", encoding="utf-8") as f:
        json.dump(hero.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return hero


def _load_hero_from_db(db: Session) -> HeroContent:
    row = db.query(HeroSection).filter(HeroSection.slug == HERO_SLUG).one()
    return HeroContent.model_validate(row.content)


def _save_hero_to_db(db: Session, hero: HeroContent) -> HeroContent:
    row = db.query(HeroSection).filter(HeroSection.slug == HERO_SLUG).one_or_none()
    payload = hero.model_dump()
    if row is None:
        row = HeroSection(slug=HERO_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return HeroContent.model_validate(row.content)


def load_hero() -> HeroContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _load_hero_from_db(db)
        finally:
            db.close()
    return _load_hero_from_json()


def save_hero(hero: HeroContent) -> HeroContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_hero_to_db(db, hero)
        finally:
            db.close()
    return _save_hero_to_json(hero)
