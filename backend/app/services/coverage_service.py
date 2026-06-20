import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database import SessionLocal
from app.models.coverage import CoverageSection
from app.schemas.coverage import CoverageContent

BASE_DIR = Path(__file__).resolve().parent.parent
COVERAGE_FILE = BASE_DIR / "data" / "coverage.json"
COVERAGE_SLUG = "homepage"


def _load_coverage_from_json() -> CoverageContent:
    with COVERAGE_FILE.open(encoding="utf-8") as f:
        return CoverageContent.model_validate_json(f.read())


def _save_coverage_to_json(coverage: CoverageContent) -> CoverageContent:
    COVERAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with COVERAGE_FILE.open("w", encoding="utf-8") as f:
        json.dump(coverage.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return coverage


def _load_coverage_from_db(db: Session) -> CoverageContent:
    row = db.query(CoverageSection).filter(CoverageSection.slug == COVERAGE_SLUG).one()
    return CoverageContent.model_validate(row.content)


def _save_coverage_to_db(db: Session, coverage: CoverageContent) -> CoverageContent:
    row = db.query(CoverageSection).filter(CoverageSection.slug == COVERAGE_SLUG).one_or_none()
    payload = coverage.model_dump()
    if row is None:
        row = CoverageSection(slug=COVERAGE_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return CoverageContent.model_validate(row.content)


def load_coverage() -> CoverageContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _load_coverage_from_db(db)
        finally:
            db.close()
    return _load_coverage_from_json()


def save_coverage(coverage: CoverageContent) -> CoverageContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_coverage_to_db(db, coverage)
        finally:
            db.close()
    return _save_coverage_to_json(coverage)
