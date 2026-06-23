from pathlib import Path

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import investor_resource_service, message_service, r2_service, user_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["investors"])


def _form_error(request: Request, error: str):
    return templates.TemplateResponse(
        request,
        "admin/investors/investor_form.html",
        {
            "page_title": "Add Investor",
            "active_nav": "investors",
            "active_item": "investors-new",
            "error": error,
        },
        status_code=400,
    )


@admin_router.get("/investors")
async def investors_list(
    request: Request,
    saved: bool = Query(False),
    error: str | None = Query(None),
    db: Session = Depends(get_db),
):
    investors = user_service.list_investors(db)
    unread_map = message_service.unread_by_investor(db)
    from app.services import registration_service

    registration_service.mark_all_registrations_seen(db)
    return templates.TemplateResponse(
        request,
        "admin/investors/list.html",
        {
            "page_title": "Investors",
            "active_nav": "investors",
            "active_item": "investors",
            "investors": investors,
            "unread_map": unread_map,
            "saved": saved,
            "error": error,
        },
    )


@admin_router.get("/investors/new")
async def investors_new_form(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/investors/investor_form.html",
        {
            "page_title": "Add Investor",
            "active_nav": "investors",
            "active_item": "investors-new",
            "error": None,
        },
    )


@admin_router.post("/investors/new")
async def investors_create(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    is_active: str | None = Form(None),
    db: Session = Depends(get_db),
):
    first_name = first_name.strip()
    last_name = last_name.strip()
    email = email.strip().lower()
    password = password.strip()

    if not first_name or not last_name:
        return _form_error(request, "First name and last name are required.")
    if len(password) < 8:
        return _form_error(request, "Password must be at least 8 characters.")
    if user_service.get_user_by_email(db, email):
        return _form_error(request, "That email is already registered.")

    investor = user_service.create_investor(
        db,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        mark_seen_by_admin=True,
    )
    if is_active == "off":
        investor.is_active = False
        db.commit()

    return RedirectResponse(url="/admin/investors?saved=1", status_code=303)


@admin_router.get("/investors/resources")
async def investor_resources_list(
    request: Request,
    saved: bool = Query(False),
    deleted: bool = Query(False),
    error: str | None = Query(None),
):
    items = investor_resource_service.list_resources()
    published = [r for r in items if r.status == "published"]
    drafts = [r for r in items if r.status == "draft"]
    return templates.TemplateResponse(
        request,
        "admin/investors/resources/list.html",
        {
            "page_title": "Investor Resources",
            "active_nav": "investors",
            "active_item": "investor-resources",
            "published_items": published,
            "draft_items": drafts,
            "saved": saved,
            "deleted": deleted,
            "error": error,
            "format_file_size": investor_resource_service.format_file_size,
            "r2_configured": r2_service.r2_configured(),
        },
    )


@admin_router.get("/investors/resources/new")
async def investor_resource_new_form(request: Request, error: str | None = Query(None)):
    return templates.TemplateResponse(
        request,
        "admin/investors/resources/item_form.html",
        {
            "page_title": "Add Investor Resource",
            "active_nav": "investors",
            "active_item": "investor-resources",
            "item": None,
            "is_new": True,
            "error": error,
            "r2_configured": r2_service.r2_configured(),
            "format_file_size": investor_resource_service.format_file_size,
        },
    )


@admin_router.post("/investors/resources/new")
async def investor_resource_create(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    file_url: str = Form(""),
    file_name: str = Form(""),
    file_size_bytes: int = Form(0),
    status: str = Form("draft"),
    sort_order: int = Form(0),
):
    if not file_url.strip():
        return RedirectResponse(url="/admin/investors/resources/new?error=file_required", status_code=303)
    investor_resource_service.add_resource(
        title=title,
        description=description,
        file_url=file_url,
        file_name=file_name,
        file_size_bytes=file_size_bytes,
        status=status,
        sort_order=sort_order,
    )
    return RedirectResponse(url="/admin/investors/resources?saved=1", status_code=303)


@admin_router.get("/investors/resources/{slug}")
async def investor_resource_edit_form(request: Request, slug: str):
    item = investor_resource_service.get_resource(slug)
    if item is None:
        return RedirectResponse(url="/admin/investors/resources?error=not_found", status_code=303)
    return templates.TemplateResponse(
        request,
        "admin/investors/resources/item_form.html",
        {
            "page_title": "Edit Investor Resource",
            "active_nav": "investors",
            "active_item": "investor-resources",
            "item": item,
            "is_new": False,
            "error": None,
            "r2_configured": r2_service.r2_configured(),
            "format_file_size": investor_resource_service.format_file_size,
        },
    )


@admin_router.post("/investors/resources/{slug}")
async def investor_resource_update(
    request: Request,
    slug: str,
    title: str = Form(...),
    description: str = Form(""),
    file_url: str = Form(""),
    file_name: str = Form(""),
    file_size_bytes: int = Form(0),
    status: str = Form("draft"),
    sort_order: int = Form(0),
):
    if not file_url.strip():
        return RedirectResponse(url=f"/admin/investors/resources/{slug}?error=file_required", status_code=303)
    item = investor_resource_service.update_resource(
        slug,
        title=title.strip(),
        description=description.strip(),
        file_url=file_url.strip(),
        file_name=file_name.strip(),
        file_size_bytes=max(0, file_size_bytes),
        status=status if status in ("draft", "published") else "draft",
        sort_order=sort_order,
    )
    if item is None:
        return RedirectResponse(url="/admin/investors/resources?error=not_found", status_code=303)
    return RedirectResponse(url="/admin/investors/resources?saved=1", status_code=303)


@admin_router.post("/investors/resources/{slug}/delete")
async def investor_resource_delete(slug: str):
    investor_resource_service.delete_resource(slug)
    return RedirectResponse(url="/admin/investors/resources?deleted=1", status_code=303)


@admin_router.get("/investors/{investor_id}")
async def investor_thread(request: Request, investor_id: int, db: Session = Depends(get_db)):
    investor = user_service.get_user(db, investor_id)
    if not investor or investor.is_admin:
        return RedirectResponse(url="/admin/investors?error=not_found", status_code=303)
    from app.services import registration_service

    registration_service.mark_registration_seen(db, investor_id)
    message_service.mark_read_for_admin(db, investor_id)
    messages = message_service.list_thread(db, investor_id)
    return templates.TemplateResponse(
        request,
        "admin/investors/thread.html",
        {
            "page_title": investor.full_name,
            "active_nav": "investors",
            "active_item": "investors",
            "investor": investor,
            "messages": messages,
        },
    )


@admin_router.post("/investors/{investor_id}/messages")
async def investor_send_message(
    request: Request,
    investor_id: int,
    body: str = Form(...),
    db: Session = Depends(get_db),
):
    investor = user_service.get_user(db, investor_id)
    if not investor or investor.is_admin:
        return RedirectResponse(url="/admin/investors?error=not_found", status_code=303)
    if body.strip():
        message_service.send_from_admin(db, investor, body)
    return RedirectResponse(url=f"/admin/investors/{investor_id}", status_code=303)
