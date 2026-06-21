from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import user_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["users"])


def _current_user_id(request: Request) -> int | None:
    raw = request.session.get("user_id")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


@admin_router.get("/users")
async def users_list(
    request: Request,
    saved: bool = Query(False),
    error: str | None = Query(None),
    db: Session = Depends(get_db),
):
    users = user_service.list_users(db)
    return templates.TemplateResponse(
        request,
        "admin/users/list.html",
        {
            "page_title": "Users",
            "active_nav": "users",
            "active_item": "users",
            "users": users,
            "saved": saved,
            "error": error,
            "current_user_id": _current_user_id(request),
        },
    )


@admin_router.get("/users/new")
async def users_new_form(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/users/user_form.html",
        {
            "page_title": "Add User",
            "active_nav": "users",
            "active_item": "users-new",
            "user": None,
            "is_new": True,
            "error": None,
        },
    )


@admin_router.post("/users/new")
async def users_create(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    is_admin: str | None = Form(None),
    is_active: str | None = Form(None),
    db: Session = Depends(get_db),
):
    username = username.strip()
    email = email.strip().lower()
    password = password.strip()

    if len(username) < 3:
        return _form_error(request, None, True, "Username must be at least 3 characters.")
    if len(password) < 8:
        return _form_error(request, None, True, "Password must be at least 8 characters.")
    if user_service.get_user_by_username_any(db, username):
        return _form_error(request, None, True, "That username is already taken.")
    if user_service.get_user_by_email(db, email):
        return _form_error(request, None, True, "That email is already in use.")

    user_service.create_user(
        db,
        username=username,
        email=email,
        password=password,
        is_admin=is_admin == "on",
        is_active=is_active != "off",
    )
    return RedirectResponse(url="/admin/users?saved=1", status_code=303)


@admin_router.get("/users/{user_id}")
async def users_edit_form(
    request: Request,
    user_id: int,
    saved: bool = Query(False),
    db: Session = Depends(get_db),
):
    user = user_service.get_user(db, user_id)
    if user is None:
        return RedirectResponse(url="/admin/users?error=not_found", status_code=303)
    return templates.TemplateResponse(
        request,
        "admin/users/user_form.html",
        {
            "page_title": "Edit User",
            "active_nav": "users",
            "active_item": "users-edit",
            "user": user,
            "is_new": False,
            "saved": saved,
            "error": None,
            "current_user_id": _current_user_id(request),
        },
    )


@admin_router.post("/users/{user_id}")
async def users_update(
    request: Request,
    user_id: int,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(""),
    is_admin: str | None = Form(None),
    is_active: str | None = Form(None),
    db: Session = Depends(get_db),
):
    user = user_service.get_user(db, user_id)
    if user is None:
        return RedirectResponse(url="/admin/users?error=not_found", status_code=303)

    username = username.strip()
    email = email.strip().lower()
    password = password.strip()
    make_admin = is_admin == "on"
    make_active = is_active != "off"
    current_id = _current_user_id(request)

    if len(username) < 3:
        return _form_error(request, user, False, "Username must be at least 3 characters.")

    existing_username = user_service.get_user_by_username_any(db, username)
    if existing_username and existing_username.id != user.id:
        return _form_error(request, user, False, "That username is already taken.")
    if user_service.get_user_by_email(db, email, exclude_id=user.id):
        return _form_error(request, user, False, "That email is already in use.")

    if user.id == current_id and not make_active:
        return _form_error(request, user, False, "You cannot deactivate your own account.")
    if user.id == current_id and not make_admin:
        return _form_error(request, user, False, "You cannot remove admin access from your own account.")

    if user.is_admin and user.is_active and (not make_admin or not make_active):
        if user_service.count_active_admins(db, exclude_id=user.id) == 0:
            return _form_error(request, user, False, "At least one active admin is required.")

    user_service.update_user(
        db,
        user,
        username=username,
        email=email,
        password=password or None,
        is_admin=make_admin,
        is_active=make_active,
    )
    return RedirectResponse(url=f"/admin/users/{user_id}?saved=1", status_code=303)


def _form_error(request: Request, user, is_new: bool, message: str):
    return templates.TemplateResponse(
        request,
        "admin/users/user_form.html",
        {
            "page_title": "Add User" if is_new else "Edit User",
            "active_nav": "users",
            "active_item": "users-new" if is_new else "users-edit",
            "user": user,
            "is_new": is_new,
            "error": message,
            "current_user_id": _current_user_id(request),
        },
        status_code=400,
    )
