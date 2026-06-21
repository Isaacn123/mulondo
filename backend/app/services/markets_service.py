import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content
from app.database import SessionLocal
from app.models.markets import MarketsSection
from app.schemas.content_defaults import default_markets
from app.schemas.markets import MarketsContent

BASE_DIR = Path(__file__).resolve().parent.parent
MARKETS_FILE = BASE_DIR / "data" / "markets.json"
MARKETS_SLUG = "homepage"


def _load_markets_from_db(db: Session) -> MarketsContent | None:
    row = db.query(MarketsSection).filter(MarketsSection.slug == MARKETS_SLUG).one_or_none()
    if row is None:
        return None
    return MarketsContent.model_validate(row.content)


def _save_markets_to_json(markets: MarketsContent) -> MarketsContent:
    MARKETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MARKETS_FILE.open("w", encoding="utf-8") as f:
        json.dump(markets.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return markets


def _save_markets_to_db(db: Session, markets: MarketsContent) -> MarketsContent:
    row = db.query(MarketsSection).filter(MarketsSection.slug == MARKETS_SLUG).one_or_none()
    payload = markets.model_dump()
    if row is None:
        row = MarketsSection(slug=MARKETS_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return MarketsContent.model_validate(row.content)


def load_markets() -> MarketsContent:
    return load_cms_content(
        model=MarketsContent,
        json_path=MARKETS_FILE,
        db_loader=_load_markets_from_db,
        default_factory=default_markets,
    )


def save_markets(markets: MarketsContent) -> MarketsContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_markets_to_db(db, markets)
        finally:
            db.close()
    return _save_markets_to_json(markets)
