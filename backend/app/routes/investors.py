from pathlib import Path

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import message_service, user_service

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
    )
    if is_active == "off":
        investor.is_active = False
        db.commit()

    return RedirectResponse(url="/admin/investors?saved=1", status_code=303)


@admin_router.get("/investors/{investor_id}")
async def investor_thread(request: Request, investor_id: int, db: Session = Depends(get_db)):
    investor = user_service.get_user(db, investor_id)
    if not investor or investor.is_admin:
        return RedirectResponse(url="/admin/investors?error=not_found", status_code=303)
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
