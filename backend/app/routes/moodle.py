from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.moodle_auth import moodle_url
from app.database import get_db
from app.services import message_service, mentorship_progress_service, mentorship_resource_service, mentorship_service, user_service
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
    completed_count = mentorship_progress_service.completed_module_count(db, mentee.id)
    total_points = mentorship_progress_service.total_points(db, mentee.id)
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
            "completed_count": completed_count,
            "total_points": total_points,
        },
    )


def _get_module(mentorship, stage_idx: int, module_idx: int):
    if stage_idx < 0 or stage_idx >= len(mentorship.stages):
        return None, None
    stage = mentorship.stages[stage_idx]
    if module_idx < 0 or module_idx >= len(stage.modules):
        return None, None
    return stage, stage.modules[module_idx]


@router.get("/module/{stage_idx}/{module_idx}")
async def moodle_module_reading(
    request: Request,
    stage_idx: int,
    module_idx: int,
    db: Session = Depends(get_db),
):
    mentee = _current_mentee(db, request)
    if not mentee:
        return RedirectResponse(url=moodle_url("/login"), status_code=302)
    mentorship = mentorship_service.load_mentorship()
    if not mentorship.published:
        return RedirectResponse(url=moodle_url("/"), status_code=302)
    stage, module = _get_module(mentorship, stage_idx, module_idx)
    if module is None:
        return RedirectResponse(url=moodle_url("/curriculum"), status_code=302)
    key = mentorship_progress_service.module_key(stage_idx, module_idx)
    progress_map = mentorship_progress_service.list_progress_for_user(db, mentee.id)
    progress = progress_map.get(key)
    unread = message_service.unread_count_for_investor(db, mentee.id)
    return templates.TemplateResponse(
        request,
        "moodle/module.html",
        {
            "page_title": module.title,
            "active_nav": "curriculum",
            "mentee": mentee,
            "unread_messages": unread,
            "mentorship": mentorship,
            "stage": stage,
            "module": module,
            "stage_idx": stage_idx,
            "module_idx": module_idx,
            "progress": progress,
        },
    )


@router.post("/module/{stage_idx}/{module_idx}/finish-reading")
async def moodle_module_finish_reading(
    request: Request,
    stage_idx: int,
    module_idx: int,
    db: Session = Depends(get_db),
):
    mentee = _current_mentee(db, request)
    if not mentee:
        return RedirectResponse(url=moodle_url("/login"), status_code=302)
    mentorship = mentorship_service.load_mentorship()
    _, module = _get_module(mentorship, stage_idx, module_idx)
    if module is None:
        return RedirectResponse(url=moodle_url("/curriculum"), status_code=302)
    key = mentorship_progress_service.module_key(stage_idx, module_idx)
    mentorship_progress_service.mark_reading_complete(db, mentee.id, key)
    if module.quiz.enabled and module.quiz.questions:
        return RedirectResponse(url=moodle_url(f"/module/{stage_idx}/{module_idx}/quiz"), status_code=303)
    mentorship_progress_service.record_quiz_attempt(
        db,
        mentee.id,
        key,
        score_percent=100,
        passed=True,
        award_points=0,
    )
    return RedirectResponse(url=moodle_url(f"/module/{stage_idx}/{module_idx}/complete"), status_code=303)


@router.get("/module/{stage_idx}/{module_idx}/quiz")
async def moodle_module_quiz(
    request: Request,
    stage_idx: int,
    module_idx: int,
    db: Session = Depends(get_db),
):
    mentee = _current_mentee(db, request)
    if not mentee:
        return RedirectResponse(url=moodle_url("/login"), status_code=302)
    mentorship = mentorship_service.load_mentorship()
    _, module = _get_module(mentorship, stage_idx, module_idx)
    if module is None or not module.quiz.enabled or not module.quiz.questions:
        return RedirectResponse(url=moodle_url(f"/module/{stage_idx}/{module_idx}"), status_code=302)
    key = mentorship_progress_service.module_key(stage_idx, module_idx)
    progress = mentorship_progress_service.get_progress(db, mentee.id, key)
    if not progress or not progress.reading_completed:
        return RedirectResponse(url=moodle_url(f"/module/{stage_idx}/{module_idx}"), status_code=302)
    if progress.quiz_passed:
        return RedirectResponse(url=moodle_url(f"/module/{stage_idx}/{module_idx}/complete"), status_code=302)
    unread = message_service.unread_count_for_investor(db, mentee.id)
    return templates.TemplateResponse(
        request,
        "moodle/module_quiz.html",
        {
            "page_title": f"Quiz — {module.title}",
            "active_nav": "curriculum",
            "mentee": mentee,
            "unread_messages": unread,
            "module": module,
            "stage_idx": stage_idx,
            "module_idx": module_idx,
            "progress": progress,
        },
    )


@router.post("/module/{stage_idx}/{module_idx}/quiz")
async def moodle_module_quiz_submit(
    request: Request,
    stage_idx: int,
    module_idx: int,
    db: Session = Depends(get_db),
):
    mentee = _current_mentee(db, request)
    if not mentee:
        return RedirectResponse(url=moodle_url("/login"), status_code=302)
    form = await request.form()
    mentorship = mentorship_service.load_mentorship()
    _, module = _get_module(mentorship, stage_idx, module_idx)
    if module is None or not module.quiz.questions:
        return RedirectResponse(url=moodle_url("/curriculum"), status_code=302)
    key = mentorship_progress_service.module_key(stage_idx, module_idx)
    correct = 0
    for i, question in enumerate(module.quiz.questions):
        try:
            selected = int(form.get(f"q_{i}", -1))
        except (TypeError, ValueError):
            selected = -1
        if selected == question.correct_index:
            correct += 1
    total = len(module.quiz.questions)
    score_percent = round((correct / total) * 100) if total else 0
    passed = score_percent >= module.quiz.pass_percent
    existing = mentorship_progress_service.get_progress(db, mentee.id, key)
    award = module.quiz.award_points if passed and not (existing and existing.quiz_passed) else 0
    mentorship_progress_service.record_quiz_attempt(
        db,
        mentee.id,
        key,
        score_percent=score_percent,
        passed=passed,
        award_points=award,
    )
    return RedirectResponse(
        url=moodle_url(f"/module/{stage_idx}/{module_idx}/complete?score={score_percent}&passed={'1' if passed else '0'}"),
        status_code=303,
    )


@router.get("/module/{stage_idx}/{module_idx}/complete")
async def moodle_module_complete(
    request: Request,
    stage_idx: int,
    module_idx: int,
    score: int | None = None,
    passed: str | None = None,
    db: Session = Depends(get_db),
):
    mentee = _current_mentee(db, request)
    if not mentee:
        return RedirectResponse(url=moodle_url("/login"), status_code=302)
    mentorship = mentorship_service.load_mentorship()
    _, module = _get_module(mentorship, stage_idx, module_idx)
    if module is None:
        return RedirectResponse(url=moodle_url("/curriculum"), status_code=302)
    key = mentorship_progress_service.module_key(stage_idx, module_idx)
    progress = mentorship_progress_service.get_progress(db, mentee.id, key)
    unread = message_service.unread_count_for_investor(db, mentee.id)
    total_points = mentorship_progress_service.total_points(db, mentee.id)
    return templates.TemplateResponse(
        request,
        "moodle/module_complete.html",
        {
            "page_title": "Module complete",
            "active_nav": "curriculum",
            "mentee": mentee,
            "unread_messages": unread,
            "module": module,
            "stage_idx": stage_idx,
            "module_idx": module_idx,
            "progress": progress,
            "score": score if score is not None else (progress.quiz_score_percent if progress else 0),
            "passed": passed == "1" or (progress.quiz_passed if progress else False),
            "total_points": total_points,
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
    progress_map = mentorship_progress_service.list_progress_for_user(db, mentee.id)
    completed_count = mentorship_progress_service.completed_module_count(db, mentee.id)
    total_points = mentorship_progress_service.total_points(db, mentee.id)
    return templates.TemplateResponse(
        request,
        "moodle/curriculum.html",
        {
            "page_title": mentorship.title,
            "active_nav": "curriculum",
            "mentee": mentee,
            "unread_messages": unread,
            "mentorship": mentorship,
            "progress_map": progress_map,
            "completed_count": completed_count,
            "total_points": total_points,
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
