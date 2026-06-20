import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database import SessionLocal
from app.models.trust import TrustSection
from app.schemas.trust import TrustContent

BASE_DIR = Path(__file__).resolve().parent.parent
TRUST_FILE = BASE_DIR / "data" / "trust.json"
TRUST_SLUG = "homepage"


def _load_trust_from_json() -> TrustContent:
    with TRUST_FILE.open(encoding="utf-8") as f:
        return TrustContent.model_validate_json(f.read())


def _save_trust_to_json(trust: TrustContent) -> TrustContent:
    TRUST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with TRUST_FILE.open("w", encoding="utf-8") as f:
        json.dump(trust.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return trust


def _load_trust_from_db(db: Session) -> TrustContent:
    row = db.query(TrustSection).filter(TrustSection.slug == TRUST_SLUG).one()
    return TrustContent.model_validate(row.content)


def _save_trust_to_db(db: Session, trust: TrustContent) -> TrustContent:
    row = db.query(TrustSection).filter(TrustSection.slug == TRUST_SLUG).one_or_none()
    payload = trust.model_dump()
    if row is None:
        row = TrustSection(slug=TRUST_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return TrustContent.model_validate(row.content)


def load_trust() -> TrustContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _load_trust_from_db(db)
        finally:
            db.close()
    return _load_trust_from_json()


def save_trust(trust: TrustContent) -> TrustContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_trust_to_db(db, trust)
        finally:
            db.close()
    return _save_trust_to_json(trust)
