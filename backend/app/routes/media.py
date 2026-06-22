from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.media import MediaContent, MediaPageHeader
from app.services import media_service, r2_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["media"])
api_router = APIRouter(prefix="/api/content", tags=["content"])

MEDIA_CATEGORIES = ("Speaking", "Conference", "Press", "Interview", "Workshop", "Other")


def _normalize_media(media_type: str, media_url: str) -> tuple[str, str]:
    media_type = (media_type or "").strip().lower()
    media_url = (media_url or "").strip()
    if media_type not in ("image", "video") or not media_url:
        return "", ""
    return media_type, media_url


@admin_router.get("/media/images")
@admin_router.get("/media/videos")
@admin_router.get("/media/documents")
async def media_legacy_redirect():
    return RedirectResponse(url="/admin/media/gallery", status_code=301)


@admin_router.get("/media")
async def media_section_form(request: Request, saved: bool = Query(False)):
    media = media_service.load_media()
    return templates.TemplateResponse(
        request,
        "admin/media/section.html",
        {
            "page_title": "Media Page",
            "active_nav": "media",
            "active_item": "media-section",
            "media": media,
            "saved": saved,
        },
    )


@admin_router.post("/media")
async def media_section_save(
    request: Request,
    eyebrow: str = Form(...),
    title_before: str = Form(...),
    title_highlight: str = Form(...),
    intro: str = Form(...),
    page_description: str = Form(""),
):
    header = MediaPageHeader(
        eyebrow=eyebrow.strip(),
        title_before=title_before.strip(),
        title_highlight=title_highlight.strip(),
        intro=intro.strip(),
        page_description=page_description.strip(),
    )
    media_service.save_media_header(header)
    return RedirectResponse(url="/admin/media?saved=1", status_code=303)


@admin_router.get("/media/gallery")
async def media_gallery_list(
    request: Request,
    saved: bool = Query(False),
    deleted: bool = Query(False),
    error: str | None = Query(None),
):
    items = media_service.list_items()
    published = [i for i in items if i.status == "published"]
    drafts = [i for i in items if i.status == "draft"]
    return templates.TemplateResponse(
        request,
        "admin/media/list.html",
        {
            "page_title": "Media Gallery",
            "active_nav": "media",
            "active_item": "media-gallery",
            "published_items": published,
            "draft_items": drafts,
            "saved": saved,
            "deleted": deleted,
            "error": error,
            "r2_configured": r2_service.r2_configured(),
        },
    )


@admin_router.get("/media/new")
async def media_new_form(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/media/item_form.html",
        {
            "page_title": "Add Media Item",
            "active_nav": "media",
            "active_item": "media-gallery",
            "item": None,
            "is_new": True,
            "categories": MEDIA_CATEGORIES,
            "r2_configured": r2_service.r2_configured(),
        },
    )


@admin_router.post("/media/new")
async def media_create(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    event_date: str = Form(""),
    category: str = Form(""),
    media_type: str = Form(""),
    media_url: str = Form(""),
    thumbnail_url: str = Form(""),
    status: str = Form("draft"),
    sort_order: int = Form(0),
):
    media_type, media_url = _normalize_media(media_type, media_url)
    if not media_type:
        return RedirectResponse(url="/admin/media/new?error=media_required", status_code=303)
    media_service.add_item(
        title=title,
        description=description,
        location=location,
        event_date=event_date,
        category=category,
        media_type=media_type,
        media_url=media_url,
        thumbnail_url=thumbnail_url,
        status=status,
        sort_order=sort_order,
    )
    return RedirectResponse(url="/admin/media/gallery?saved=1", status_code=303)


@admin_router.get("/media/{slug}")
async def media_edit_form(request: Request, slug: str):
    item = media_service.get_item(slug)
    if item is None:
        return RedirectResponse(url="/admin/media/gallery?error=not_found", status_code=303)
    return templates.TemplateResponse(
        request,
        "admin/media/item_form.html",
        {
            "page_title": "Edit Media Item",
            "active_nav": "media",
            "active_item": "media-gallery",
            "item": item,
            "is_new": False,
            "categories": MEDIA_CATEGORIES,
            "r2_configured": r2_service.r2_configured(),
        },
    )


@admin_router.post("/media/{slug}")
async def media_update(
    request: Request,
    slug: str,
    title: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    event_date: str = Form(""),
    category: str = Form(""),
    media_type: str = Form(""),
    media_url: str = Form(""),
    thumbnail_url: str = Form(""),
    status: str = Form("draft"),
    sort_order: int = Form(0),
):
    media_type, media_url = _normalize_media(media_type, media_url)
    if not media_type:
        return RedirectResponse(url=f"/admin/media/{slug}?error=media_required", status_code=303)
    item = media_service.update_item(
        slug,
        title=title.strip(),
        description=description.strip(),
        location=location.strip(),
        event_date=event_date.strip(),
        category=category.strip(),
        media_type=media_type,
        media_url=media_url,
        thumbnail_url=thumbnail_url.strip(),
        status=status if status in ("draft", "published") else "draft",
        sort_order=sort_order,
    )
    if item is None:
        return RedirectResponse(url="/admin/media/gallery?error=not_found", status_code=303)
    return RedirectResponse(url="/admin/media/gallery?saved=1", status_code=303)


@admin_router.post("/media/{slug}/delete")
async def media_delete(slug: str):
    media_service.delete_item(slug)
    return RedirectResponse(url="/admin/media/gallery?deleted=1", status_code=303)


@api_router.get("/media")
async def media_api() -> MediaContent:
    content = media_service.load_media()
    published = [item for item in content.items if item.status == "published"]
    return content.model_copy(update={"items": published})
