import json
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content, load_json_model, load_raw_json
from app.database import SessionLocal
from app.models.cms_document import CmsDocument

T = TypeVar("T", bound=BaseModel)


def _load_row(db: Session, slug: str) -> CmsDocument | None:
    return db.query(CmsDocument).filter(CmsDocument.slug == slug).one_or_none()


def _save_row(db: Session, slug: str, payload: dict) -> dict:
    row = _load_row(db, slug)
    if row is None:
        row = CmsDocument(slug=slug, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return row.content


def _delete_row(db: Session, slug: str) -> bool:
    row = _load_row(db, slug)
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _db_loader_for_model(slug: str, model: type[T]) -> Callable[[Session], T | None]:
    def loader(db: Session) -> T | None:
        row = _load_row(db, slug)
        if row is None:
            return None
        return model.model_validate(row.content)

    return loader


def _db_loader_for_dict(slug: str) -> Callable[[Session], dict | None]:
    def loader(db: Session) -> dict | None:
        row = _load_row(db, slug)
        if row is None:
            return None
        return dict(row.content)

    return loader


def load_model(
    *,
    slug: str,
    model: type[T],
    json_path: Path,
    default_factory: Callable[[], T],
) -> T:
    return load_cms_content(
        model=model,
        json_path=json_path,
        db_loader=_db_loader_for_model(slug, model),
        default_factory=default_factory,
    )


def save_model(*, slug: str, content: T, json_path: Path) -> T:
    payload = content.model_dump()
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            _save_row(db, slug, payload)
            return content
        finally:
            db.close()
    _write_json(json_path, payload)
    return content


def load_dict(
    *,
    slug: str,
    json_path: Path,
    default_factory: Callable[[], dict],
) -> dict:
    settings = get_settings()
    if settings.storage_backend == "database":
        db = SessionLocal()
        try:
            row = _load_row(db, slug)
            if row is not None:
                return dict(row.content)
        except Exception:
            pass
        finally:
            db.close()

    loaded = load_raw_json(json_path, default=None)
    if loaded is not None:
        return loaded
    return default_factory()


def save_dict(*, slug: str, data: dict, json_path: Path) -> dict:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_row(db, slug, data)
        finally:
            db.close()
    _write_json(json_path, data)
    return data


def delete_document(*, slug: str, json_path: Path | None = None) -> bool:
    """Remove a CMS document from the database (and optional JSON file)."""
    deleted = False
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            deleted = _delete_row(db, slug)
        finally:
            db.close()
    if json_path and json_path.is_file():
        json_path.unlink()
        deleted = True
    return deleted


def seed_model_from_json(
    db: Session,
    *,
    slug: str,
    model: type[T],
    json_path: Path,
    overwrite: bool = False,
) -> bool:
    if not json_path.is_file():
        return False
    if _load_row(db, slug) is not None and not overwrite:
        return False
    content = load_json_model(json_path, model)
    if content is None:
        return False
    _save_row(db, slug, content.model_dump())
    return True


def seed_dict_from_json(
    db: Session,
    *,
    slug: str,
    json_path: Path,
    overwrite: bool = False,
) -> bool:
    if not json_path.is_file():
        return False
    if _load_row(db, slug) is not None and not overwrite:
        return False
    loaded = load_raw_json(json_path, default=None)
    if loaded is None:
        return False
    _save_row(db, slug, loaded)
    return True
