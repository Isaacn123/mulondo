from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.submission import ConsultationRequest, ContactSubmission, MembershipRequest
from app.schemas.submissions import (
    ConsultationRequestCreate,
    ContactSubmissionCreate,
    MembershipRequestCreate,
    NotificationItem,
    NotificationSummary,
)
from app.services import brevo_service


@dataclass
class CreatedSubmission:
    kind: str
    id: int
    name: str
    email: str


def create_contact_submission(db: Session, payload: ContactSubmissionCreate) -> CreatedSubmission:
    row = ContactSubmission(
        name=payload.name.strip(),
        email=str(payload.email).strip().lower(),
        country=payload.country.strip(),
        investor_type=payload.investor_type.strip(),
        capital_range=payload.capital_range.strip(),
        message=payload.message.strip(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    data = payload.model_dump()
    brevo_service.notify_admin_contact_submission(data)
    brevo_service.notify_visitor_contact_received(row.name, row.email)

    return CreatedSubmission(kind="contact", id=row.id, name=row.name, email=row.email)


def create_membership_request(db: Session, payload: MembershipRequestCreate) -> CreatedSubmission:
    row = MembershipRequest(
        name=payload.name.strip(),
        email=str(payload.email).strip().lower(),
        phone=payload.phone.strip(),
        country=payload.country.strip(),
        tier=payload.tier.strip(),
        message=payload.message.strip(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    data = payload.model_dump()
    brevo_service.notify_admin_membership_request(data)
    brevo_service.notify_visitor_membership_received(row.name, row.email, row.tier)

    return CreatedSubmission(kind="membership", id=row.id, name=row.name, email=row.email)


def create_consultation_request(
    db: Session,
    *,
    name: str,
    email: str,
    phone: str = "",
    message: str = "",
    event_name: str = "Consultation request",
    scheduled_at=None,
    source: str = "form",
) -> CreatedSubmission:
    row = ConsultationRequest(
        name=name.strip(),
        email=email.strip().lower(),
        phone=phone.strip(),
        message=message.strip(),
        event_name=event_name.strip() or "Consultation request",
        scheduled_at=scheduled_at,
        source=source,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    data = {
        "name": row.name,
        "email": row.email,
        "phone": row.phone,
        "message": row.message,
        "event_name": row.event_name,
        "scheduled_at": row.scheduled_at.isoformat() if row.scheduled_at else "",
        "source": row.source,
    }
    brevo_service.notify_admin_consultation_request(data)
    brevo_service.notify_visitor_consultation_received(row.name, row.email, row.event_name, row.scheduled_at)

    return CreatedSubmission(kind="consultation", id=row.id, name=row.name, email=row.email)


def create_consultation_from_form(db: Session, payload: ConsultationRequestCreate) -> CreatedSubmission:
    return create_consultation_request(
        db,
        name=payload.name,
        email=str(payload.email),
        phone=payload.phone,
        message=payload.message,
        source="form",
    )


def list_contact_submissions(db: Session) -> list[ContactSubmission]:
    return db.query(ContactSubmission).order_by(ContactSubmission.created_at.desc()).all()


def list_membership_requests(db: Session) -> list[MembershipRequest]:
    return db.query(MembershipRequest).order_by(MembershipRequest.created_at.desc()).all()


def list_consultation_requests(db: Session) -> list[ConsultationRequest]:
    return db.query(ConsultationRequest).order_by(ConsultationRequest.created_at.desc()).all()


def get_contact_submission(db: Session, submission_id: int) -> ContactSubmission | None:
    return db.query(ContactSubmission).filter(ContactSubmission.id == submission_id).first()


def get_membership_request(db: Session, request_id: int) -> MembershipRequest | None:
    return db.query(MembershipRequest).filter(MembershipRequest.id == request_id).first()


def get_consultation_request(db: Session, request_id: int) -> ConsultationRequest | None:
    return db.query(ConsultationRequest).filter(ConsultationRequest.id == request_id).first()


def mark_contact_read(db: Session, submission_id: int) -> bool:
    row = get_contact_submission(db, submission_id)
    if row is None:
        return False
    row.is_read = True
    db.commit()
    return True


def mark_membership_read(db: Session, request_id: int) -> bool:
    row = get_membership_request(db, request_id)
    if row is None:
        return False
    row.is_read = True
    db.commit()
    return True


def mark_consultation_read(db: Session, request_id: int) -> bool:
    row = get_consultation_request(db, request_id)
    if row is None:
        return False
    row.is_read = True
    db.commit()
    return True


def mark_all_read(db: Session) -> None:
    db.query(ContactSubmission).filter(ContactSubmission.is_read.is_(False)).update({"is_read": True})
    db.query(MembershipRequest).filter(MembershipRequest.is_read.is_(False)).update({"is_read": True})
    db.query(ConsultationRequest).filter(ConsultationRequest.is_read.is_(False)).update({"is_read": True})
    db.commit()


def get_notification_summary(db: Session, limit: int = 8) -> NotificationSummary:
    unread_contact = db.query(ContactSubmission).filter(ContactSubmission.is_read.is_(False)).count()
    unread_membership = db.query(MembershipRequest).filter(MembershipRequest.is_read.is_(False)).count()
    unread_consultation = db.query(ConsultationRequest).filter(ConsultationRequest.is_read.is_(False)).count()

    contacts = (
        db.query(ContactSubmission)
        .filter(ContactSubmission.is_read.is_(False))
        .order_by(ContactSubmission.created_at.desc())
        .limit(limit)
        .all()
    )
    memberships = (
        db.query(MembershipRequest)
        .filter(MembershipRequest.is_read.is_(False))
        .order_by(MembershipRequest.created_at.desc())
        .limit(limit)
        .all()
    )
    consultations = (
        db.query(ConsultationRequest)
        .filter(ConsultationRequest.is_read.is_(False))
        .order_by(ConsultationRequest.created_at.desc())
        .limit(limit)
        .all()
    )

    items: list[NotificationItem] = []
    for row in contacts:
        items.append(
            NotificationItem(
                id=row.id,
                kind="contact",
                title=f"Contact: {row.name}",
                subtitle=row.investor_type or row.email,
                created_at=row.created_at,
                admin_url=f"/admin/leads/contact-submissions/{row.id}",
            )
        )
    for row in memberships:
        items.append(
            NotificationItem(
                id=row.id,
                kind="membership",
                title=f"Membership: {row.name}",
                subtitle=row.tier or row.email,
                created_at=row.created_at,
                admin_url=f"/admin/leads/membership-requests/{row.id}",
            )
        )
    for row in consultations:
        subtitle = row.event_name
        if row.scheduled_at:
            subtitle = f"{row.event_name} · {row.scheduled_at.strftime('%d %b %Y, %H:%M')}"
        items.append(
            NotificationItem(
                id=row.id,
                kind="consultation",
                title=f"Consultation: {row.name}",
                subtitle=subtitle or row.email,
                created_at=row.created_at,
                admin_url=f"/admin/leads/consultation-requests/{row.id}",
            )
        )

    items.sort(key=lambda item: item.created_at, reverse=True)
    return NotificationSummary(
        unread_total=unread_contact + unread_membership + unread_consultation,
        unread_contact=unread_contact,
        unread_membership=unread_membership,
        unread_consultation=unread_consultation,
        recent=items[:limit],
    )
