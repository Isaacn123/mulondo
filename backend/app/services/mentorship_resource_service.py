import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database import SessionLocal
from app.models.mentorship_resource import MentorshipResourceRow
from app.schemas.insights import slugify
from app.schemas.mentorship_resource import MentorshipResource, MentorshipResourceList

BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCES_FILE = BASE_DIR / "data" / "mentorship_resources.json"


def _row_to_resource(row: MentorshipResourceRow) -> MentorshipResource:
    return MentorshipResource(
        slug=row.slug,
        title=row.title,
        description=row.description,
        file_url=row.file_url,
        file_name=row.file_name or "",
        file_size_bytes=row.file_size_bytes or 0,
        status=row.status,  # type: ignore[arg-type]
        sort_order=row.sort_order,
    )


def _load_from_json() -> MentorshipResourceList:
    if not RESOURCES_FILE.exists():
        return MentorshipResourceList()
    data = json.loads(RESOURCES_FILE.read_text(encoding="utf-8"))
    return MentorshipResourceList.model_validate(data)


def _save_to_json(content: MentorshipResourceList) -> None:
    RESOURCES_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESOURCES_FILE.write_text(
        json.dumps(content.model_dump(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _load_from_db(db: Session) -> MentorshipResourceList:
    rows = db.query(MentorshipResourceRow).order_by(
        MentorshipResourceRow.sort_order.desc(),
        MentorshipResourceRow.title,
    )
    return MentorshipResourceList(items=[_row_to_resource(row) for row in rows])


def list_resources(*, published_only: bool = False) -> list[MentorshipResource]:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            items = _load_from_db(db).items
        finally:
            db.close()
    else:
        items = _load_from_json().items
    items.sort(key=lambda r: (-r.sort_order, r.title.lower()))
    if published_only:
        return [r for r in items if r.status == "published"]
    return items


def get_resource(slug: str) -> MentorshipResource | None:
    for item in list_resources():
        if item.slug == slug:
            return item
    return None


def _save_resource_to_db(db: Session, resource: MentorshipResource) -> MentorshipResource:
    row = db.query(MentorshipResourceRow).filter(MentorshipResourceRow.slug == resource.slug).one_or_none()
    if row is None:
        row = MentorshipResourceRow(
            slug=resource.slug,
            title=resource.title,
            description=resource.description,
            file_url=resource.file_url,
            file_name=resource.file_name,
            file_size_bytes=resource.file_size_bytes,
            status=resource.status,
            sort_order=resource.sort_order,
        )
        db.add(row)
    else:
        row.title = resource.title
        row.description = resource.description
        row.file_url = resource.file_url
        row.file_name = resource.file_name
        row.file_size_bytes = resource.file_size_bytes
        row.status = resource.status
        row.sort_order = resource.sort_order
    db.commit()
    db.refresh(row)
    return _row_to_resource(row)


def _save_resource_to_json(resource: MentorshipResource) -> MentorshipResource:
    content = _load_from_json()
    items = [i for i in content.items if i.slug != resource.slug]
    items.append(resource)
    items.sort(key=lambda r: (-r.sort_order, r.title.lower()))
    _save_to_json(content.model_copy(update={"items": items}))
    return resource


def save_resource(resource: MentorshipResource) -> MentorshipResource:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_resource_to_db(db, resource)
        finally:
            db.close()
    return _save_resource_to_json(resource)


def add_resource(
    *,
    title: str,
    description: str = "",
    file_url: str,
    file_name: str = "",
    file_size_bytes: int = 0,
    status: str = "draft",
    sort_order: int = 0,
    slug: str | None = None,
) -> MentorshipResource:
    base_slug = slug or slugify(title)
    candidate = base_slug
    index = 2
    while get_resource(candidate):
        candidate = f"{base_slug}-{index}"
        index += 1
    resource = MentorshipResource(
        slug=candidate,
        title=title.strip(),
        description=description.strip(),
        file_url=file_url.strip(),
        file_name=file_name.strip(),
        file_size_bytes=max(0, file_size_bytes),
        status=status if status in ("draft", "published") else "draft",  # type: ignore[arg-type]
        sort_order=sort_order,
    )
    return save_resource(resource)


def update_resource(slug: str, **fields) -> MentorshipResource | None:
    resource = get_resource(slug)
    if resource is None:
        return None
    return save_resource(resource.model_copy(update=fields))


def delete_resource(slug: str) -> bool:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            row = db.query(MentorshipResourceRow).filter(MentorshipResourceRow.slug == slug).one_or_none()
            if row is None:
                return False
            db.delete(row)
            db.commit()
            return True
        finally:
            db.close()
    content = _load_from_json()
    new_items = [i for i in content.items if i.slug != slug]
    if len(new_items) == len(content.items):
        return False
    _save_to_json(content.model_copy(update={"items": new_items}))
    return True


def format_file_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return ""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"
