from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import SessionLocal, get_db
from app.schemas.submissions import (
    ConsultationRequestCreate,
    ContactSubmissionCreate,
    MembershipRequestCreate,
    NotificationItem,
    NotificationSummary,
    SubmissionResponse,
)
from app.services import submission_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

api_router = APIRouter(prefix="/api/submissions", tags=["submissions"])
webhook_router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
admin_router = APIRouter(prefix="/admin/leads", tags=["leads"])


@api_router.post("/contact", response_model=SubmissionResponse)
async def submit_contact(payload: ContactSubmissionCreate, db: Session = Depends(get_db)):
    submission_service.create_contact_submission(db, payload)
    return SubmissionResponse(
        message="Thank you — your confidential request has been received. We will respond within one business day."
    )


@api_router.post("/membership", response_model=SubmissionResponse)
async def submit_membership(payload: MembershipRequestCreate, db: Session = Depends(get_db)):
    submission_service.create_membership_request(db, payload)
    return SubmissionResponse(
        message="Thank you — your membership request has been received. We will follow up with next steps shortly."
    )


@api_router.post("/consultation", response_model=SubmissionResponse)
async def submit_consultation(payload: ConsultationRequestCreate, db: Session = Depends(get_db)):
    submission_service.create_consultation_from_form(db, payload)
    return SubmissionResponse(
        message="Thank you — your consultation request has been received. We will confirm or follow up within one business day."
    )


def _parse_calendly_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@webhook_router.post("/calendly")
async def calendly_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive Calendly invitee.created events when someone books a consultation."""
    try:
        body = await request.json()
    except Exception:
        return {"ok": False}

    if body.get("event") != "invitee.created":
        return {"ok": True, "ignored": True}

    payload = body.get("payload") or {}
    scheduled = payload.get("scheduled_event") or {}
    notes = ""
    for qa in payload.get("questions_and_answers") or []:
        if isinstance(qa, dict) and qa.get("answer"):
            notes = str(qa["answer"]).strip()
            break
    email = (payload.get("email") or "").strip()
    if not email:
        return {"ok": True, "ignored": True}
    submission_service.create_consultation_request(
        db,
        name=(payload.get("name") or "Calendly guest").strip(),
        email=email,
        phone="",
        message=notes,
        event_name=(scheduled.get("name") or "Calendly consultation").strip(),
        scheduled_at=_parse_calendly_datetime(scheduled.get("start_time")),
        source="calendly",
    )
    return {"ok": True}


@admin_router.get("/contact-submissions")
async def contact_submissions_list(request: Request, db: Session = Depends(get_db)):
    submissions = submission_service.list_contact_submissions(db)
    unread = sum(1 for item in submissions if not item.is_read)
    return templates.TemplateResponse(
        request,
        "admin/leads/contact_list.html",
        {
            "page_title": "Contact Submissions",
            "active_nav": "leads",
            "active_item": "contact-submissions",
            "submissions": submissions,
            "unread_count": unread,
        },
    )


@admin_router.get("/contact-submissions/{submission_id}")
async def contact_submission_detail(
    request: Request,
    submission_id: int,
    db: Session = Depends(get_db),
):
    submission = submission_service.get_contact_submission(db, submission_id)
    if submission is None:
        return RedirectResponse(url="/admin/leads/contact-submissions?error=not_found", status_code=303)
    submission_service.mark_contact_read(db, submission_id)
    return templates.TemplateResponse(
        request,
        "admin/leads/contact_detail.html",
        {
            "page_title": "Contact Submission",
            "active_nav": "leads",
            "active_item": "contact-submissions",
            "submission": submission,
        },
    )


@admin_router.post("/contact-submissions/mark-all-read")
async def contact_mark_all_read(db: Session = Depends(get_db)):
    submission_service.mark_all_read(db)
    return RedirectResponse(url="/admin/leads/contact-submissions", status_code=303)


@admin_router.get("/membership-requests")
async def membership_requests_list(request: Request, db: Session = Depends(get_db)):
    requests_list = submission_service.list_membership_requests(db)
    unread = sum(1 for item in requests_list if not item.is_read)
    return templates.TemplateResponse(
        request,
        "admin/leads/membership_list.html",
        {
            "page_title": "Membership Requests",
            "active_nav": "leads",
            "active_item": "membership-requests",
            "requests": requests_list,
            "unread_count": unread,
        },
    )


@admin_router.get("/membership-requests/{request_id}")
async def membership_request_detail(
    request: Request,
    request_id: int,
    db: Session = Depends(get_db),
):
    membership_request = submission_service.get_membership_request(db, request_id)
    if membership_request is None:
        return RedirectResponse(url="/admin/leads/membership-requests?error=not_found", status_code=303)
    submission_service.mark_membership_read(db, request_id)
    return templates.TemplateResponse(
        request,
        "admin/leads/membership_detail.html",
        {
            "page_title": "Membership Request",
            "active_nav": "leads",
            "active_item": "membership-requests",
            "membership_request": membership_request,
        },
    )


@admin_router.get("/consultation-requests")
async def consultation_requests_list(request: Request, db: Session = Depends(get_db)):
    requests_list = submission_service.list_consultation_requests(db)
    unread = sum(1 for item in requests_list if not item.is_read)
    return templates.TemplateResponse(
        request,
        "admin/leads/consultation_list.html",
        {
            "page_title": "Consultation Requests",
            "active_nav": "leads",
            "active_item": "leads-consultation-requests",
            "requests": requests_list,
            "unread_count": unread,
        },
    )


@admin_router.get("/consultation-requests/{request_id}")
async def consultation_request_detail(
    request: Request,
    request_id: int,
    db: Session = Depends(get_db),
):
    consultation = submission_service.get_consultation_request(db, request_id)
    if consultation is None:
        return RedirectResponse(url="/admin/leads/consultation-requests?error=not_found", status_code=303)
    submission_service.mark_consultation_read(db, request_id)
    return templates.TemplateResponse(
        request,
        "admin/leads/consultation_detail.html",
        {
            "page_title": "Consultation Request",
            "active_nav": "leads",
            "active_item": "leads-consultation-requests",
            "consultation": consultation,
        },
    )


class AdminNotificationsMiddleware(BaseHTTPMiddleware):
    """Attach unread visitor submission and investor message counts to admin HTML requests."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/admin") and not path.startswith("/admin/static"):
            db = SessionLocal()
            try:
                from app.services import kyc_service, message_service, registration_service, user_service

                summary = submission_service.get_notification_summary(db)
                try:
                    inv_unread = message_service.unread_count_for_admin(db)
                    new_investors = registration_service.count_unseen_registrations(db)
                    kyc_unseen = kyc_service.count_unseen_pending(db)
                    summary.unread_investor = inv_unread
                    summary.unread_new_investors = new_investors
                    summary.unread_kyc = kyc_unseen
                    summary.unread_total += inv_unread + new_investors + kyc_unseen
                    for investor in registration_service.list_unseen_registrations(db, limit=5):
                        summary.recent.append(
                            NotificationItem(
                                id=investor.id,
                                kind="investor-registration",
                                title=f"New investor: {investor.full_name}",
                                subtitle=investor.email,
                                created_at=investor.created_at,
                                admin_url=f"/admin/investors/{investor.id}",
                            )
                        )
                    for msg in message_service.recent_unread_for_admin(db, limit=5):
                        investor = user_service.get_user(db, msg.investor_id)
                        if not investor:
                            continue
                        summary.recent.append(
                            NotificationItem(
                                id=msg.id,
                                kind="investor-message",
                                title=f"Investor: {investor.full_name}",
                                subtitle=(msg.body[:80] + "…") if len(msg.body) > 80 else msg.body,
                                created_at=msg.created_at,
                                admin_url=f"/admin/investors/{investor.id}",
                            )
                        )
                    for kyc_row in kyc_service.list_unseen_pending(db, limit=5):
                        member = user_service.get_user(db, kyc_row.user_id)
                        if not member:
                            continue
                        summary.recent.append(
                            NotificationItem(
                                id=kyc_row.id,
                                kind="kyc-pending",
                                title=f"KYC review: {member.full_name}",
                                subtitle=kyc_service.role_label(kyc_row.portal_role),
                                created_at=kyc_row.submitted_at or kyc_row.updated_at,
                                admin_url=f"/admin/kyc/{kyc_row.id}",
                            )
                        )
                    summary.recent.sort(key=lambda item: item.created_at, reverse=True)
                    summary.recent = summary.recent[:8]
                except Exception:
                    pass
                request.state.notifications = summary
            except Exception:
                request.state.notifications = NotificationSummary()
            finally:
                db.close()
        return await call_next(request)
