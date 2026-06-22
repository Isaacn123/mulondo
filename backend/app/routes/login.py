from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import admin_url
from app.database import get_db
from app.services.user_service import get_user_by_username
from app.util.users_utility import verify_password

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(prefix="/admin", tags=["auth"])


@router.get("/login")
async def login_form(request: Request, error: str | None = None):
    if request.session.get("user_id"):
        return RedirectResponse(url=admin_url("/"), status_code=302)
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {
            "error": error,
            "page_title": "Admin Login",
            "login_action": admin_url("/login"),
        },
    )


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_user_by_username(db, username.strip())

    if not user or not user.is_admin or not verify_password(password, user.password_hash):
        return RedirectResponse(
            url=f"{admin_url('/login')}?error=invalid",
            status_code=302,
        )

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["account_type"] = "admin"

    return RedirectResponse(url=admin_url("/"), status_code=302)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url=admin_url("/login"), status_code=302)
