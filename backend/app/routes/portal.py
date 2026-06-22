from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.portal_auth import portal_url
from app.database import get_db
from app.services import message_service, mentorship_service, user_service
from app.util.users_utility import verify_password

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["portal_url"] = portal_url

_investor_prefix = get_settings().investor_path_prefix.rstrip("/") or "/investors"
router = APIRouter(prefix=_investor_prefix, tags=["investors-portal"])


def _current_investor(db: Session, request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return user_service.get_investor(db, int(user_id))


@router.get("/login")
async def portal_login_form(request: Request, error: str | None = None):
    if request.session.get("account_type") == "investor" and request.session.get("user_id"):
        return RedirectResponse(url=portal_url("/"), status_code=302)
    return templates.TemplateResponse(
        request,
        "portal/login.html",
        {"error": error, "page_title": "Investor Sign In", "login_action": portal_url("/login")},
    )


@router.post("/login")
async def portal_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = user_service.get_user_by_email(db, email.strip().lower())
    if not user or user.is_admin or not verify_password(password, user.password_hash):
        return RedirectResponse(url=f"{portal_url('/login')}?error=invalid", status_code=302)

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.full_name
    request.session["account_type"] = "investor"
    return RedirectResponse(url=portal_url("/"), status_code=302)


@router.get("/logout")
async def portal_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url=portal_url("/login"), status_code=302)


@router.get("/")
@router.get("")
async def portal_dashboard(request: Request, db: Session = Depends(get_db)):
    investor = _current_investor(db, request)
    if not investor:
        return RedirectResponse(url=portal_url("/login"), status_code=302)
    unread = message_service.unread_count_for_investor(db, investor.id)
    messages = message_service.list_thread(db, investor.id)[-5:]
    return templates.TemplateResponse(
        request,
        "portal/dashboard.html",
        {
            "page_title": "Dashboard",
            "active_nav": "dashboard",
            "investor": investor,
            "unread_messages": unread,
            "recent_messages": messages,
        },
    )


@router.get("/messages")
async def portal_messages(request: Request, db: Session = Depends(get_db)):
    investor = _current_investor(db, request)
    if not investor:
        return RedirectResponse(url=portal_url("/login"), status_code=302)
    message_service.mark_read_for_investor(db, investor.id)
    messages = message_service.list_thread(db, investor.id)
    return templates.TemplateResponse(
        request,
        "portal/messages.html",
        {
            "page_title": "Messages",
            "active_nav": "messages",
            "investor": investor,
            "messages": messages,
            "unread_messages": 0,
        },
    )


@router.post("/messages")
async def portal_send_message(
    request: Request,
    body: str = Form(...),
    db: Session = Depends(get_db),
):
    investor = _current_investor(db, request)
    if not investor:
        return RedirectResponse(url=portal_url("/login"), status_code=302)
    if body.strip():
        message_service.send_from_investor(db, investor, body)
    return RedirectResponse(url=portal_url("/messages"), status_code=303)


@router.get("/materials")
async def portal_materials(request: Request, db: Session = Depends(get_db)):
    investor = _current_investor(db, request)
    if not investor:
        return RedirectResponse(url=portal_url("/login"), status_code=302)
    unread = message_service.unread_count_for_investor(db, investor.id)
    mentorship = mentorship_service.load_mentorship()
    return templates.TemplateResponse(
        request,
        "portal/materials.html",
        {
            "page_title": "Member Materials",
            "active_nav": "materials",
            "investor": investor,
            "unread_messages": unread,
            "mentorship": mentorship,
        },
    )


@router.get("/mentorship")
async def portal_mentorship(request: Request, db: Session = Depends(get_db)):
    investor = _current_investor(db, request)
    if not investor:
        return RedirectResponse(url=portal_url("/login"), status_code=302)
    mentorship = mentorship_service.load_mentorship()
    if not mentorship.published:
        return RedirectResponse(url=portal_url("/materials"), status_code=302)
    unread = message_service.unread_count_for_investor(db, investor.id)
    return templates.TemplateResponse(
        request,
        "portal/mentorship.html",
        {
            "page_title": mentorship.title,
            "active_nav": "materials",
            "investor": investor,
            "unread_messages": unread,
            "mentorship": mentorship,
        },
    )


@router.get("/profile")
async def portal_profile(request: Request, db: Session = Depends(get_db)):
    investor = _current_investor(db, request)
    if not investor:
        return RedirectResponse(url=portal_url("/login"), status_code=302)
    unread = message_service.unread_count_for_investor(db, investor.id)
    return templates.TemplateResponse(
        request,
        "portal/profile.html",
        {
            "page_title": "My Profile",
            "active_nav": "profile",
            "investor": investor,
            "unread_messages": unread,
        },
    )
