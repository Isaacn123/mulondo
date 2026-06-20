import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database import SessionLocal
from app.models.blog import BlogPostRow
from app.schemas.blog import BlogPost, BlogStore
from app.schemas.insights import slugify

BASE_DIR = Path(__file__).resolve().parent.parent
BLOG_FILE = BASE_DIR / "data" / "blog.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row_to_post(row: BlogPostRow) -> BlogPost:
    return BlogPost(
        slug=row.slug,
        title=row.title,
        excerpt=row.excerpt,
        body=row.body,
        author=row.author,
        published_at=row.published_at,
        status=row.status,  # type: ignore[arg-type]
        created_at=row.created_at.replace(tzinfo=timezone.utc).isoformat() if row.created_at else "",
        updated_at=row.updated_at.replace(tzinfo=timezone.utc).isoformat() if row.updated_at else "",
    )


def _load_store_from_json() -> BlogStore:
    with BLOG_FILE.open(encoding="utf-8") as f:
        return BlogStore.model_validate_json(f.read())


def _save_store_to_json(store: BlogStore) -> BlogStore:
    BLOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with BLOG_FILE.open("w", encoding="utf-8") as f:
        json.dump(store.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return store


def _load_posts_from_db(db: Session) -> list[BlogPost]:
    rows = db.query(BlogPostRow).order_by(BlogPostRow.published_at.desc(), BlogPostRow.updated_at.desc()).all()
    return [_row_to_post(row) for row in rows]


def _load_store() -> BlogStore:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return BlogStore(posts=_load_posts_from_db(db))
        finally:
            db.close()
    return _load_store_from_json()


def _save_post_to_db(db: Session, post: BlogPost) -> BlogPost:
    row = db.query(BlogPostRow).filter(BlogPostRow.slug == post.slug).one_or_none()
    if row is None:
        row = BlogPostRow(
            slug=post.slug,
            title=post.title,
            excerpt=post.excerpt,
            body=post.body,
            author=post.author,
            published_at=post.published_at,
            status=post.status,
        )
        db.add(row)
    else:
        row.title = post.title
        row.excerpt = post.excerpt
        row.body = post.body
        row.author = post.author
        row.published_at = post.published_at
        row.status = post.status
    db.commit()
    db.refresh(row)
    return _row_to_post(row)


def _delete_post_from_db(db: Session, slug: str) -> None:
    row = db.query(BlogPostRow).filter(BlogPostRow.slug == slug).one_or_none()
    if row is None:
        raise KeyError(slug)
    db.delete(row)
    db.commit()


def list_posts(*, published_only: bool = False) -> list[BlogPost]:
    posts = _load_store().posts
    if published_only:
        posts = [post for post in posts if post.status == "published"]
    return sorted(
        posts,
        key=lambda post: post.published_at or post.updated_at or post.created_at,
        reverse=True,
    )


def get_post(slug: str) -> BlogPost | None:
    for post in _load_store().posts:
        if post.slug == slug:
            return post
    return None


def _unique_slug(base: str, existing: set[str]) -> str:
    slug = slugify(base)
    if slug not in existing:
        return slug
    index = 2
    while f"{slug}-{index}" in existing:
        index += 1
    return f"{slug}-{index}"


def add_post(post: BlogPost) -> BlogPost:
    store = _load_store()
    existing = {item.slug for item in store.posts}
    if post.slug in existing:
        post = post.model_copy(update={"slug": _unique_slug(post.title, existing)})
    now = _now_iso()
    post = post.model_copy(
        update={
            "created_at": now,
            "updated_at": now,
            "published_at": post.published_at or (now[:10] if post.status == "published" else ""),
        }
    )
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_post_to_db(db, post)
        finally:
            db.close()
    store.posts.append(post)
    _save_store_to_json(store)
    return post


def update_post(slug: str, post: BlogPost) -> BlogPost:
    store = _load_store()
    now = _now_iso()
    updated_post: BlogPost | None = None
    updated_posts: list[BlogPost] = []

    for item in store.posts:
        if item.slug == slug:
            updated_post = post.model_copy(
                update={
                    "slug": slug,
                    "created_at": item.created_at or now,
                    "updated_at": now,
                    "published_at": post.published_at or (now[:10] if post.status == "published" else item.published_at),
                }
            )
            updated_posts.append(updated_post)
        else:
            updated_posts.append(item)

    if updated_post is None:
        raise KeyError(slug)

    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_post_to_db(db, updated_post)
        finally:
            db.close()

    _save_store_to_json(BlogStore(posts=updated_posts))
    return updated_post


def delete_post(slug: str) -> None:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            _delete_post_from_db(db, slug)
            return
        finally:
            db.close()
    store = _load_store()
    filtered = [item for item in store.posts if item.slug != slug]
    if len(filtered) == len(store.posts):
        raise KeyError(slug)
    _save_store_to_json(BlogStore(posts=filtered))
