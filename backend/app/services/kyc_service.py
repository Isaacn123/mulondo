from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.kyc import KYC_STATUS_APPROVED, KYC_STATUS_DRAFT, KYC_STATUS_PENDING, KYC_STATUS_REJECTED, KycSubmission
from app.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_submission(db: Session, user_id: int) -> KycSubmission | None:
    return db.query(KycSubmission).filter(KycSubmission.user_id == user_id).one_or_none()


def get_or_create_submission(db: Session, user: User) -> KycSubmission:
    row = get_submission(db, user.id)
    if row:
        if row.portal_role != user.portal_role:
            row.portal_role = user.portal_role
            db.commit()
            db.refresh(row)
        return row
    row = KycSubmission(
        user_id=user.id,
        portal_role=user.portal_role,
        status=KYC_STATUS_DRAFT,
        legal_full_name=user.full_name,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_submission(
    db: Session,
    user: User,
    *,
    legal_full_name: str = "",
    country: str = "",
    id_number: str = "",
    member_notes: str = "",
    government_id_url: str | None = None,
    government_id_name: str | None = None,
    proof_of_address_url: str | None = None,
    proof_of_address_name: str | None = None,
) -> KycSubmission:
    row = get_or_create_submission(db, user)
    if row.status == KYC_STATUS_PENDING:
        return row
    if row.status == KYC_STATUS_APPROVED:
        return row

    row.legal_full_name = legal_full_name.strip() or user.full_name
    row.country = country.strip()
    row.id_number = id_number.strip()
    row.member_notes = member_notes.strip()
    if government_id_url is not None:
        row.government_id_url = government_id_url.strip()
    if government_id_name is not None:
        row.government_id_name = government_id_name.strip()
    if proof_of_address_url is not None:
        row.proof_of_address_url = proof_of_address_url.strip()
    if proof_of_address_name is not None:
        row.proof_of_address_name = proof_of_address_name.strip()
    if row.status == KYC_STATUS_REJECTED:
        row.status = KYC_STATUS_DRAFT
        row.rejection_reason = ""
        row.reviewed_at = None
    db.commit()
    db.refresh(row)
    return row


def submit_for_review(db: Session, user: User) -> tuple[KycSubmission | None, str | None]:
    row = get_or_create_submission(db, user)
    if row.status == KYC_STATUS_PENDING:
        return row, None
    if row.status == KYC_STATUS_APPROVED:
        return row, "Your identity verification is already approved."

    if not row.legal_full_name.strip():
        return None, "Enter your full legal name."
    if not row.country.strip():
        return None, "Enter your country of residence."
    if not row.government_id_url.strip():
        return None, "Upload a government-issued ID document."
    if not row.proof_of_address_url.strip():
        return None, "Upload proof of address."

    row.status = KYC_STATUS_PENDING
    row.submitted_at = _utcnow()
    row.admin_seen = False
    row.rejection_reason = ""
    db.commit()
    db.refresh(row)
    return row, None


def list_submissions(
    db: Session,
    *,
    portal_role: str | None = None,
    status: str | None = None,
    limit: int | None = None,
) -> list[KycSubmission]:
    q = db.query(KycSubmission).join(User).order_by(KycSubmission.updated_at.desc())
    if portal_role:
        q = q.filter(KycSubmission.portal_role == portal_role)
    if status:
        q = q.filter(KycSubmission.status == status)
    if limit:
        q = q.limit(limit)
    return q.all()


def count_by_status(db: Session) -> dict[str, int]:
    from sqlalchemy import func

    counts = {KYC_STATUS_DRAFT: 0, KYC_STATUS_PENDING: 0, KYC_STATUS_APPROVED: 0, KYC_STATUS_REJECTED: 0}
    for status, total in db.query(KycSubmission.status, func.count(KycSubmission.id)).group_by(KycSubmission.status):
        counts[status] = int(total)
    return counts


def count_pending(db: Session) -> int:
    return db.query(KycSubmission).filter(KycSubmission.status == KYC_STATUS_PENDING).count()


def count_unseen_pending(db: Session) -> int:
    return (
        db.query(KycSubmission)
        .filter(KycSubmission.status == KYC_STATUS_PENDING, KycSubmission.admin_seen.is_(False))
        .count()
    )


def list_unseen_pending(db: Session, limit: int = 8) -> list[KycSubmission]:
    return (
        db.query(KycSubmission)
        .filter(KycSubmission.status == KYC_STATUS_PENDING, KycSubmission.admin_seen.is_(False))
        .order_by(KycSubmission.submitted_at.desc())
        .limit(limit)
        .all()
    )


def mark_all_pending_seen(db: Session) -> None:
    db.query(KycSubmission).filter(
        KycSubmission.status == KYC_STATUS_PENDING,
        KycSubmission.admin_seen.is_(False),
    ).update({KycSubmission.admin_seen: True}, synchronize_session=False)
    db.commit()


def get_submission_by_id(db: Session, submission_id: int) -> KycSubmission | None:
    return db.query(KycSubmission).filter(KycSubmission.id == submission_id).one_or_none()


def approve_submission(db: Session, submission: KycSubmission) -> KycSubmission:
    submission.status = KYC_STATUS_APPROVED
    submission.reviewed_at = _utcnow()
    submission.rejection_reason = ""
    submission.admin_seen = True
    db.commit()
    db.refresh(submission)
    return submission


def reject_submission(db: Session, submission: KycSubmission, reason: str) -> KycSubmission:
    submission.status = KYC_STATUS_REJECTED
    submission.reviewed_at = _utcnow()
    submission.rejection_reason = reason.strip()
    submission.admin_seen = True
    db.commit()
    db.refresh(submission)
    return submission


def status_label(status: str) -> str:
    return {
        KYC_STATUS_DRAFT: "Not submitted",
        KYC_STATUS_PENDING: "Pending review",
        KYC_STATUS_APPROVED: "Approved",
        KYC_STATUS_REJECTED: "Rejected",
    }.get(status, status.title())


def role_label(portal_role: str) -> str:
    return {"investor": "Investor / Membership", "mentee": "Mentorship"}.get(portal_role, portal_role.title())
