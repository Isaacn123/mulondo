from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.kyc import KYC_STATUS_PENDING
from app.services import kyc_service, message_service, r2_service, user_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["kyc"])


@admin_router.get("/kyc")
async def kyc_list(
    request: Request,
    role: str | None = Query(None),
    status: str | None = Query(None),
    saved: bool = Query(False),
    db: Session = Depends(get_db),
):
    kyc_service.mark_all_pending_seen(db)
    submissions = kyc_service.list_submissions(db, portal_role=role or None, status=status or None)
    user_map = {u.id: u for u in user_service.list_users(db)}
    counts = kyc_service.count_by_status(db)
    return templates.TemplateResponse(
        request,
        "admin/kyc/list.html",
        {
            "page_title": "KYC Verification",
            "active_nav": "kyc",
            "active_item": "kyc",
            "submissions": submissions,
            "user_map": user_map,
            "counts": counts,
            "filter_role": role or "",
            "filter_status": status or "",
            "status_label": kyc_service.status_label,
            "role_label": kyc_service.role_label,
            "saved": saved,
        },
    )


@admin_router.get("/kyc/{submission_id}")
async def kyc_review(
    request: Request,
    submission_id: int,
    error: str | None = Query(None),
    saved: bool = Query(False),
    db: Session = Depends(get_db),
):
    submission = kyc_service.get_submission_by_id(db, submission_id)
    if not submission:
        return RedirectResponse(url="/admin/kyc?error=not_found", status_code=302)
    user = user_service.get_user(db, submission.user_id)
    if submission.status == KYC_STATUS_PENDING and not submission.admin_seen:
        submission.admin_seen = True
        db.commit()
    return templates.TemplateResponse(
        request,
        "admin/kyc/review.html",
        {
            "page_title": f"KYC — {user.full_name if user else submission.user_id}",
            "active_nav": "kyc",
            "active_item": "kyc",
            "submission": submission,
            "member": user,
            "status_label": kyc_service.status_label,
            "role_label": kyc_service.role_label,
            "error": error,
            "saved": saved,
        },
    )


@admin_router.post("/kyc/{submission_id}/approve")
async def kyc_approve(submission_id: int, db: Session = Depends(get_db)):
    submission = kyc_service.get_submission_by_id(db, submission_id)
    if not submission:
        return RedirectResponse(url="/admin/kyc?error=not_found", status_code=302)
    kyc_service.approve_submission(db, submission)
    user = user_service.get_user(db, submission.user_id)
    if user:
        message_service.send_from_admin(
            db,
            user,
            "Your identity verification (KYC) has been approved. You now have full access to member resources.",
        )
    return RedirectResponse(url=f"/admin/kyc/{submission_id}?saved=1", status_code=303)


@admin_router.post("/kyc/{submission_id}/reject")
async def kyc_reject(
    submission_id: int,
    rejection_reason: str = Form(...),
    db: Session = Depends(get_db),
):
    submission = kyc_service.get_submission_by_id(db, submission_id)
    if not submission:
        return RedirectResponse(url="/admin/kyc?error=not_found", status_code=302)
    reason = rejection_reason.strip()
    if not reason:
        return RedirectResponse(url=f"/admin/kyc/{submission_id}?error=reason_required", status_code=302)
    kyc_service.reject_submission(db, submission, reason)
    user = user_service.get_user(db, submission.user_id)
    if user:
        message_service.send_from_admin(
            db,
            user,
            "Your identity verification (KYC) needs updates.\n\nReason: " + reason + "\n\nPlease resubmit your documents from the KYC page.",
        )
    return RedirectResponse(url=f"/admin/kyc/{submission_id}?saved=1", status_code=303)
