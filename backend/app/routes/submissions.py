from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import SessionLocal, get_db
from app.schemas.submissions import (
    ContactSubmissionCreate,
    MembershipRequestCreate,
    NotificationSummary,
    SubmissionResponse,
)
from app.services import submission_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

api_router = APIRouter(prefix="/api/submissions", tags=["submissions"])
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


@admin_router.get("/contact-submissions")
async def contact_submissions_list(request: Request, db: Session = Depends(get_db)):
    submissions = submission_service.list_contact_submissions(db)
    unread = sum(1 for item in submissions if not item.is_read)
    return templates.TemplateResponse(
        request,
        "admin/leads/contact_list.html",
        {
            "page_title": "Contact Submissions",
            "active_nav": "pages",
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
            "active_nav": "pages",
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
            "active_nav": "pages",
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
            "active_nav": "pages",
            "active_item": "membership-requests",
            "membership_request": membership_request,
        },
    )


class AdminNotificationsMiddleware(BaseHTTPMiddleware):
    """Attach unread visitor submission counts to admin HTML requests."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/admin") and not path.startswith("/admin/static"):
            db = SessionLocal()
            try:
                request.state.notifications = submission_service.get_notification_summary(db)
            except Exception:
                request.state.notifications = NotificationSummary()
            finally:
                db.close()
        return await call_next(request)
