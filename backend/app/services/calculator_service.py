import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content
from app.database import SessionLocal
from app.models.calculator import CalculatorSection
from app.schemas.calculator import CalculatorContent
from app.schemas.content_defaults import default_calculator

BASE_DIR = Path(__file__).resolve().parent.parent
CALCULATOR_FILE = BASE_DIR / "data" / "calculator.json"
CALCULATOR_SLUG = "homepage"


def _load_calculator_from_db(db: Session) -> CalculatorContent | None:
    row = db.query(CalculatorSection).filter(CalculatorSection.slug == CALCULATOR_SLUG).one_or_none()
    if row is None:
        return None
    return CalculatorContent.model_validate(row.content)


def _save_calculator_to_json(calculator: CalculatorContent) -> CalculatorContent:
    CALCULATOR_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CALCULATOR_FILE.open("w", encoding="utf-8") as f:
        json.dump(calculator.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return calculator


def _save_calculator_to_db(db: Session, calculator: CalculatorContent) -> CalculatorContent:
    row = db.query(CalculatorSection).filter(CalculatorSection.slug == CALCULATOR_SLUG).one_or_none()
    payload = calculator.model_dump()
    if row is None:
        row = CalculatorSection(slug=CALCULATOR_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return CalculatorContent.model_validate(row.content)


def load_calculator() -> CalculatorContent:
    return load_cms_content(
        model=CalculatorContent,
        json_path=CALCULATOR_FILE,
        db_loader=_load_calculator_from_db,
        default_factory=default_calculator,
    )


def save_calculator(calculator: CalculatorContent) -> CalculatorContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_calculator_to_db(db, calculator)
        finally:
            db.close()
    return _save_calculator_to_json(calculator)
