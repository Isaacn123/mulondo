import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content
from app.database import SessionLocal
from app.models.coverage import CoverageSection
from app.schemas.content_defaults import default_coverage
from app.schemas.coverage import CoverageContent

BASE_DIR = Path(__file__).resolve().parent.parent
COVERAGE_FILE = BASE_DIR / "data" / "coverage.json"
COVERAGE_SLUG = "homepage"


def _load_coverage_from_db(db: Session) -> CoverageContent | None:
    row = db.query(CoverageSection).filter(CoverageSection.slug == COVERAGE_SLUG).one_or_none()
    if row is None:
        return None
    return CoverageContent.model_validate(row.content)


def _save_coverage_to_json(coverage: CoverageContent) -> CoverageContent:
    COVERAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with COVERAGE_FILE.open("w", encoding="utf-8") as f:
        json.dump(coverage.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return coverage


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
    return load_cms_content(
        model=CoverageContent,
        json_path=COVERAGE_FILE,
        db_loader=_load_coverage_from_db,
        default_factory=default_coverage,
    )


def save_coverage(coverage: CoverageContent) -> CoverageContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_coverage_to_db(db, coverage)
        finally:
            db.close()
    return _save_coverage_to_json(coverage)
