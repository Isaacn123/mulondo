import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content
from app.database import SessionLocal
from app.models.trust import TrustSection
from app.schemas.content_defaults import default_trust
from app.schemas.trust import TrustContent

BASE_DIR = Path(__file__).resolve().parent.parent
TRUST_FILE = BASE_DIR / "data" / "trust.json"
TRUST_SLUG = "homepage"


def _load_trust_from_db(db: Session) -> TrustContent | None:
    row = db.query(TrustSection).filter(TrustSection.slug == TRUST_SLUG).one_or_none()
    if row is None:
        return None
    return TrustContent.model_validate(row.content)


def _save_trust_to_json(trust: TrustContent) -> TrustContent:
    TRUST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with TRUST_FILE.open("w", encoding="utf-8") as f:
        json.dump(trust.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return trust


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
    return load_cms_content(
        model=TrustContent,
        json_path=TRUST_FILE,
        db_loader=_load_trust_from_db,
        default_factory=default_trust,
    )


def save_trust(trust: TrustContent) -> TrustContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_trust_to_db(db, trust)
        finally:
            db.close()
    return _save_trust_to_json(trust)
