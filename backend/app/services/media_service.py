import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_json_model
from app.database import SessionLocal
from app.models.media import MediaItemRow, MediaSection
from app.schemas.content_defaults import default_media_content
from app.schemas.insights import slugify
from app.schemas.media import MediaContent, MediaItem, MediaPageHeader

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_FILE = BASE_DIR / "data" / "media.json"
SECTION_SLUG = "homepage"


def _row_to_item(row: MediaItemRow) -> MediaItem:
    return MediaItem(
        slug=row.slug,
        title=row.title,
        description=row.description,
        location=row.location,
        event_date=row.event_date,
        category=row.category,
        media_type=row.media_type or "image",  # type: ignore[arg-type]
        media_url=row.media_url,
        thumbnail_url=row.thumbnail_url or "",
        status=row.status,  # type: ignore[arg-type]
        sort_order=row.sort_order,
    )


def _load_header_from_db(db: Session) -> MediaPageHeader | None:
    row = db.query(MediaSection).filter(MediaSection.slug == SECTION_SLUG).one_or_none()
    if row is None:
        return None
    return MediaPageHeader.model_validate(row.content)


def _load_items_from_db(db: Session) -> list[MediaItem]:
    rows = (
        db.query(MediaItemRow)
        .order_by(MediaItemRow.sort_order.desc(), MediaItemRow.event_date.desc(), MediaItemRow.updated_at.desc())
        .all()
    )
    return [_row_to_item(row) for row in rows]


def _load_from_json() -> MediaContent:
    loaded = load_json_model(MEDIA_FILE, MediaContent)
    return loaded if loaded is not None else default_media_content()


def _save_to_json(content: MediaContent) -> MediaContent:
    MEDIA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MEDIA_FILE.open("w", encoding="utf-8") as f:
        json.dump(content.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return content


def load_media() -> MediaContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            header = _load_header_from_db(db)
            items = _load_items_from_db(db)
            if header is None:
                fallback = _load_from_json()
                return fallback.model_copy(update={"items": items})
            return MediaContent(**header.model_dump(), items=items)
        finally:
            db.close()
    return _load_from_json()


def save_media_header(header: MediaPageHeader) -> MediaPageHeader:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            row = db.query(MediaSection).filter(MediaSection.slug == SECTION_SLUG).one_or_none()
            payload = header.model_dump()
            if row is None:
                row = MediaSection(slug=SECTION_SLUG, content=payload)
                db.add(row)
            else:
                row.content = payload
            db.commit()
            return header
        finally:
            db.close()
    content = load_media()
    updated = content.model_copy(update=header.model_dump())
    _save_to_json(updated)
    return header


def list_items(published_only: bool = False) -> list[MediaItem]:
    items = load_media().items
    if published_only:
        items = [item for item in items if item.status == "published"]
    return items


def get_item(slug: str) -> MediaItem | None:
    for item in load_media().items:
        if item.slug == slug:
            return item
    return None


def _save_item_to_db(db: Session, item: MediaItem) -> MediaItem:
    row = db.query(MediaItemRow).filter(MediaItemRow.slug == item.slug).one_or_none()
    if row is None:
        row = MediaItemRow(
            slug=item.slug,
            title=item.title,
            description=item.description,
            location=item.location,
            event_date=item.event_date,
            category=item.category,
            media_type=item.media_type,
            media_url=item.media_url,
            thumbnail_url=item.thumbnail_url,
            status=item.status,
            sort_order=item.sort_order,
        )
        db.add(row)
    else:
        row.title = item.title
        row.description = item.description
        row.location = item.location
        row.event_date = item.event_date
        row.category = item.category
        row.media_type = item.media_type
        row.media_url = item.media_url
        row.thumbnail_url = item.thumbnail_url
        row.status = item.status
        row.sort_order = item.sort_order
    db.commit()
    db.refresh(row)
    return _row_to_item(row)


def _save_item_to_json(item: MediaItem) -> MediaItem:
    content = load_media()
    items = [i for i in content.items if i.slug != item.slug]
    items.append(item)
    items.sort(key=lambda i: (-i.sort_order, i.event_date), reverse=False)
    _save_to_json(content.model_copy(update={"items": items}))
    return item


def save_item(item: MediaItem) -> MediaItem:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_item_to_db(db, item)
        finally:
            db.close()
    return _save_item_to_json(item)


def add_item(
    *,
    title: str,
    description: str = "",
    location: str = "",
    event_date: str = "",
    category: str = "",
    media_type: str,
    media_url: str,
    thumbnail_url: str = "",
    status: str = "draft",
    sort_order: int = 0,
    slug: str | None = None,
) -> MediaItem:
    base_slug = slug or slugify(title)
    candidate = base_slug
    index = 2
    while get_item(candidate):
        candidate = f"{base_slug}-{index}"
        index += 1
    item = MediaItem(
        slug=candidate,
        title=title.strip(),
        description=description.strip(),
        location=location.strip(),
        event_date=event_date.strip(),
        category=category.strip(),
        media_type=media_type if media_type in ("image", "video") else "image",  # type: ignore[arg-type]
        media_url=media_url.strip(),
        thumbnail_url=thumbnail_url.strip(),
        status=status if status in ("draft", "published") else "draft",  # type: ignore[arg-type]
        sort_order=sort_order,
    )
    return save_item(item)


def update_item(slug: str, **fields) -> MediaItem | None:
    item = get_item(slug)
    if item is None:
        return None
    return save_item(item.model_copy(update=fields))


def delete_item(slug: str) -> bool:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            row = db.query(MediaItemRow).filter(MediaItemRow.slug == slug).one_or_none()
            if row is None:
                return False
            db.delete(row)
            db.commit()
            return True
        finally:
            db.close()
    content = load_media()
    new_items = [i for i in content.items if i.slug != slug]
    if len(new_items) == len(content.items):
        return False
    _save_to_json(content.model_copy(update={"items": new_items}))
    return True
