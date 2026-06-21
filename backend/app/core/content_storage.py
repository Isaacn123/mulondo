import json
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database import SessionLocal

T = TypeVar("T", bound=BaseModel)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json_model(path: Path, model: type[T]) -> T | None:
    if not path.is_file():
        return None
    try:
        return model.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def load_raw_json(path: Path, default: dict | list | None = None) -> dict | list | None:
    if not path.is_file():
        return default
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError, TypeError):
        return default


def load_cms_content(
    *,
    model: type[T],
    json_path: Path,
    db_loader: Callable[[Session], T | None],
    default_factory: Callable[[], T],
) -> T:
    """Load CMS content from DB, JSON file, or defaults — never raises on missing data."""
    settings = get_settings()
    if settings.storage_backend == "database":
        db = SessionLocal()
        try:
            content = db_loader(db)
            if content is not None:
                return content
        except Exception:
            pass
        finally:
            db.close()

    from_json = load_json_model(json_path, model)
    if from_json is not None:
        return from_json

    return default_factory()


def using_fallback_source(json_path: Path, db_has_row: bool | None = None) -> bool:
    """True when admin is showing fallback content rather than saved DB data."""
    if get_settings().storage_backend != "database":
        return False
    if db_has_row is True:
        return False
    return json_path.is_file() or db_has_row is False
