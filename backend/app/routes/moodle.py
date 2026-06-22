from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.moodle_auth import moodle_url
from app.database import get_db
from app.services import message_service, mentorship_resource_service, mentorship_service, user_service
from app.util.users_utility import verify_password

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["moodle_url"] = moodle_url

_moodle_prefix = get_settings().moodle_path_prefix.rstrip("/") or "/moodle"
router = APIRouter(prefix=_moodle_prefix, tags=["moodle-portal"])


def _current_mentee(db: Session, request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return user_service.get_mentee(db, int(user_id))


@router.get("/login")
async def moodle_login_form(request: Request, error: str | None = None):
    if request.session.get("account_type") == "mentee" and request.session.get("user_id"):
        return RedirectResponse(url=moodle_url("/"), status_code=302)
    return templates.TemplateResponse(
        request,
        "moodle/login.html",
        {"error": error, "page_title": "Moodle Sign In", "login_action": moodle_url("/login")},
    )


@router.post("/login")
async def moodle_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = user_service.get_user_by_email(db, email.strip().lower())
    if not user or user.is_admin or user.portal_role != "mentee":
        return RedirectResponse(url=f"{moodle_url('/login')}?error=invalid", status_code=302)
    if not verify_password(password, user.password_hash):
        return RedirectResponse(url=f"{moodle_url('/login')}?error=invalid", status_code=302)

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.full_name
    request.session["account_type"] = "mentee"
    return RedirectResponse(url=moodle_url("/"), status_code=302)


@router.get("/logout")
async def moodle_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url=moodle_url("/login"), status_code=302)


@router.get("/")
@router.get("")
async def moodle_dashboard(request: Request, db: Session = Depends(get_db)):
    mentee = _current_mentee(db, request)
    if not mentee:
        return RedirectResponse(url=moodle_url("/login"), status_code=302)
    unread = message_service.unread_count_for_investor(db, mentee.id)
    mentorship = mentorship_service.load_mentorship()
    resources = mentorship_resource_service.list_resources(published_only=True)
    messages = message_service.list_thread(db, mentee.id)[-5:]
    return templates.TemplateResponse(
        request,
        "moodle/dashboard.html",
        {
            "page_title": "Moodle Dashboard",
            "active_nav": "dashboard",
            "mentee": mentee,
            "unread_messages": unread,
            "mentorship": mentorship,
            "resource_count": len(resources),
            "recent_messages": messages,
        },
    )


@router.get("/curriculum")
async def moodle_curriculum(request: Request, db: Session = Depends(get_db)):
    mentee = _current_mentee(db, request)
    if not mentee:
        return RedirectResponse(url=moodle_url("/login"), status_code=302)
    mentorship = mentorship_service.load_mentorship()
    if not mentorship.published:
        return RedirectResponse(url=moodle_url("/"), status_code=302)
    unread = message_service.unread_count_for_investor(db, mentee.id)
    return templates.TemplateResponse(
        request,
        "moodle/curriculum.html",
        {
            "page_title": mentorship.title,
            "active_nav": "curriculum",
            "mentee": mentee,
            "unread_messages": unread,
            "mentorship": mentorship,
        },
    )


@router.get("/messages")
async def moodle_messages(request: Request, db: Session = Depends(get_db)):
    mentee = _current_mentee(db, request)
    if not mentee:
        return RedirectResponse(url=moodle_url("/login"), status_code=302)
    message_service.mark_read_for_investor(db, mentee.id)
    messages = message_service.list_thread(db, mentee.id)
    return templates.TemplateResponse(
        request,
        "moodle/messages.html",
        {
            "page_title": "Messages",
            "active_nav": "messages",
            "mentee": mentee,
            "messages": messages,
            "unread_messages": 0,
        },
    )


@router.post("/messages")
async def moodle_send_message(
    request: Request,
    body: str = Form(...),
    db: Session = Depends(get_db),
):
    mentee = _current_mentee(db, request)
    if not mentee:
        return RedirectResponse(url=moodle_url("/login"), status_code=302)
    if body.strip():
        message_service.send_from_investor(db, mentee, body)
    return RedirectResponse(url=moodle_url("/messages"), status_code=303)


@router.get("/resources")
async def moodle_resources(request: Request, db: Session = Depends(get_db)):
    mentee = _current_mentee(db, request)
    if not mentee:
        return RedirectResponse(url=moodle_url("/login"), status_code=302)
    unread = message_service.unread_count_for_investor(db, mentee.id)
    resources = mentorship_resource_service.list_resources(published_only=True)
    return templates.TemplateResponse(
        request,
        "moodle/resources.html",
        {
            "page_title": "Resources",
            "active_nav": "resources",
            "mentee": mentee,
            "unread_messages": unread,
            "resources": resources,
            "format_file_size": mentorship_resource_service.format_file_size,
        },
    )


@router.get("/profile")
async def moodle_profile(request: Request, db: Session = Depends(get_db)):
    mentee = _current_mentee(db, request)
    if not mentee:
        return RedirectResponse(url=moodle_url("/login"), status_code=302)
    unread = message_service.unread_count_for_investor(db, mentee.id)
    return templates.TemplateResponse(
        request,
        "moodle/profile.html",
        {
            "page_title": "My Profile",
            "active_nav": "profile",
            "mentee": mentee,
            "unread_messages": unread,
        },
    )
