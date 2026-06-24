from urllib.parse import quote

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.portal_auth import portal_url
from app.database import get_db
from app.services import investor_resource_service, kyc_service, message_service, r2_service, user_service
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
    if not user or user.is_admin or user.portal_role != "investor":
        return RedirectResponse(url=f"{portal_url('/login')}?error=invalid", status_code=302)
    if not verify_password(password, user.password_hash):
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
    resources = investor_resource_service.list_resources(published_only=True)
    messages = message_service.list_thread(db, investor.id)[-5:]
    return templates.TemplateResponse(
        request,
        "portal/dashboard.html",
        {
            "page_title": "Dashboard",
            "active_nav": "dashboard",
            "investor": investor,
            "unread_messages": unread,
            "resource_count": len(resources),
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


def _portal_support_context(
    *,
    saved: bool = False,
    error: str | None = None,
    default_category: str = "",
    default_subject: str = "",
    default_body: str = "",
):
    return {
        "support_action": portal_url("/support"),
        "support_categories": message_service.INVESTOR_SUPPORT_CATEGORIES,
        "messages_url": portal_url("/messages"),
        "support_heading": "Write to support",
        "support_intro": "Ask about KYC, your account, member resources, or billing. Our team replies in Messages.",
        "support_help_text": (
            "<strong>Typical response time:</strong> 1–2 business days.<br>"
            "For urgent KYC issues, choose <em>KYC / Identity verification</em> as the topic."
        ),
        "saved": saved,
        "error": error,
        "default_category": default_category,
        "default_subject": default_subject,
        "default_body": default_body,
    }


@router.get("/support")
async def portal_support(
    request: Request,
    category: str | None = Query(None),
    saved: bool = Query(False),
    error: str | None = Query(None),
    db: Session = Depends(get_db),
):
    investor = _current_investor(db, request)
    if not investor:
        return RedirectResponse(url=portal_url("/login"), status_code=302)
    ctx = _portal_support_context(
        saved=saved,
        error=error,
        default_category=category or "",
    )
    ctx.update(
        {
            "page_title": "Support",
            "active_nav": "support",
            "investor": investor,
            "unread_messages": message_service.unread_count_for_investor(db, investor.id),
        }
    )
    return templates.TemplateResponse(request, "portal/support.html", ctx)


@router.post("/support")
async def portal_support_send(
    request: Request,
    category: str = Form("other"),
    subject: str = Form(""),
    body: str = Form(""),
    db: Session = Depends(get_db),
):
    investor = _current_investor(db, request)
    if not investor:
        return RedirectResponse(url=portal_url("/login"), status_code=302)
    try:
        message_service.send_support_request(
            db, investor, category=category, subject=subject, body=body
        )
    except ValueError as exc:
        return RedirectResponse(
            url=f"{portal_url('/support')}?error={quote(str(exc))}&category={category}",
            status_code=303,
        )
    return RedirectResponse(url=f"{portal_url('/support')}?saved=1", status_code=303)


@router.get("/fund")
async def portal_fund(request: Request, db: Session = Depends(get_db)):
    investor = _current_investor(db, request)
    if not investor:
        return RedirectResponse(url=portal_url("/login"), status_code=302)
    return templates.TemplateResponse(
        request,
        "portal/fund.html",
        {
            "page_title": "My Fund",
            "active_nav": "fund",
            "investor": investor,
            "unread_messages": message_service.unread_count_for_investor(db, investor.id),
        },
    )


@router.get("/materials")
async def portal_materials(request: Request, db: Session = Depends(get_db)):
    return RedirectResponse(url=portal_url("/resources"), status_code=302)


@router.get("/resources")
async def portal_resources(request: Request, db: Session = Depends(get_db)):
    investor = _current_investor(db, request)
    if not investor:
        return RedirectResponse(url=portal_url("/login"), status_code=302)
    unread = message_service.unread_count_for_investor(db, investor.id)
    resources = investor_resource_service.list_resources(published_only=True)
    return templates.TemplateResponse(
        request,
        "portal/resources.html",
        {
            "page_title": "Resources",
            "active_nav": "resources",
            "investor": investor,
            "unread_messages": unread,
            "resources": resources,
            "format_file_size": investor_resource_service.format_file_size,
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


def _portal_kyc_context(request: Request, investor, kyc, *, saved: bool = False, error: str | None = None):
    return {
        "page_title": "KYC Verification",
        "active_nav": "kyc",
        "investor": investor,
        "member": investor,
        "kyc": kyc,
        "kyc_action": portal_url("/kyc"),
        "kyc_upload_url": portal_url("/kyc/upload"),
        "support_url": portal_url("/support"),
        "r2_configured": r2_service.r2_configured(),
        "unread_messages": 0,
        "saved": saved,
        "error": error,
    }


@router.get("/kyc")
async def portal_kyc(request: Request, saved: bool = Query(False), error: str | None = Query(None), db: Session = Depends(get_db)):
    investor = _current_investor(db, request)
    if not investor:
        return RedirectResponse(url=portal_url("/login"), status_code=302)
    kyc = kyc_service.get_or_create_submission(db, investor)
    ctx = _portal_kyc_context(request, investor, kyc, saved=saved, error=error)
    ctx["unread_messages"] = message_service.unread_count_for_investor(db, investor.id)
    return templates.TemplateResponse(request, "portal/kyc.html", ctx)


@router.post("/kyc/upload")
async def portal_kyc_upload(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
):
    from fastapi.responses import JSONResponse

    investor = _current_investor(db, request)
    if not investor:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    if document_type not in ("government_id", "proof_of_address"):
        return JSONResponse({"detail": "Invalid document type."}, status_code=400)
    url, file_name, size_bytes = await r2_service.upload_kyc_document(file, user_id=investor.id)
    kyc = kyc_service.get_or_create_submission(db, investor)
    if kyc.status not in ("pending", "approved"):
        if document_type == "government_id":
            kyc_service.update_submission(db, investor, government_id_url=url, government_id_name=file_name)
        else:
            kyc_service.update_submission(db, investor, proof_of_address_url=url, proof_of_address_name=file_name)
    return {"ok": True, "url": url, "file_name": file_name, "file_size_bytes": size_bytes}


@router.post("/kyc")
async def portal_kyc_save(
    request: Request,
    action: str = Form("save"),
    legal_full_name: str = Form(""),
    country: str = Form(""),
    id_number: str = Form(""),
    member_notes: str = Form(""),
    government_id_url: str = Form(""),
    government_id_name: str = Form(""),
    proof_of_address_url: str = Form(""),
    proof_of_address_name: str = Form(""),
    db: Session = Depends(get_db),
):
    investor = _current_investor(db, request)
    if not investor:
        return RedirectResponse(url=portal_url("/login"), status_code=302)
    kyc_service.update_submission(
        db,
        investor,
        legal_full_name=legal_full_name,
        country=country,
        id_number=id_number,
        member_notes=member_notes,
        government_id_url=government_id_url,
        government_id_name=government_id_name,
        proof_of_address_url=proof_of_address_url,
        proof_of_address_name=proof_of_address_name,
    )
    if action == "submit":
        _, err = kyc_service.submit_for_review(db, investor)
        if err:
            return RedirectResponse(url=f"{portal_url('/kyc')}?error={quote(err)}", status_code=303)
    return RedirectResponse(url=f"{portal_url('/kyc')}?saved=1", status_code=303)
