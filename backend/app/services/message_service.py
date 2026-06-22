from sqlalchemy.orm import Session

from app.models.user import InvestorMessage, User
from app.services import brevo_service


def list_thread(db: Session, investor_id: int) -> list[InvestorMessage]:
    return (
        db.query(InvestorMessage)
        .filter(InvestorMessage.investor_id == investor_id)
        .order_by(InvestorMessage.created_at.asc())
        .all()
    )


def send_from_admin(db: Session, investor: User, body: str) -> InvestorMessage:
    message = InvestorMessage(
        investor_id=investor.id,
        from_admin=True,
        body=body.strip(),
        is_read=False,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    brevo_service.notify_investor_new_message(investor.full_name, investor.email, body)
    return message


def post_welcome_message(db: Session, investor: User) -> InvestorMessage:
    """Dashboard welcome note for new investors (no separate email — welcome email is sent separately)."""
    message = InvestorMessage(
        investor_id=investor.id,
        from_admin=True,
        body=(
            "Welcome to your investor portal. Your account is active — browse member materials, "
            "check updates here, and message our team anytime you have questions."
        ),
        is_read=False,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def send_from_investor(db: Session, investor: User, body: str) -> InvestorMessage:
    message = InvestorMessage(
        investor_id=investor.id,
        from_admin=False,
        body=body.strip(),
        is_read=False,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    brevo_service.notify_admin_investor_message(investor.full_name, investor.email, body)
    return message


def mark_read_for_investor(db: Session, investor_id: int) -> None:
    (
        db.query(InvestorMessage)
        .filter(
            InvestorMessage.investor_id == investor_id,
            InvestorMessage.from_admin.is_(True),
            InvestorMessage.is_read.is_(False),
        )
        .update({"is_read": True})
    )
    db.commit()


def mark_read_for_admin(db: Session, investor_id: int) -> None:
    (
        db.query(InvestorMessage)
        .filter(
            InvestorMessage.investor_id == investor_id,
            InvestorMessage.from_admin.is_(False),
            InvestorMessage.is_read.is_(False),
        )
        .update({"is_read": True})
    )
    db.commit()


def unread_count_for_investor(db: Session, investor_id: int) -> int:
    return (
        db.query(InvestorMessage)
        .filter(
            InvestorMessage.investor_id == investor_id,
            InvestorMessage.from_admin.is_(True),
            InvestorMessage.is_read.is_(False),
        )
        .count()
    )


def unread_count_for_admin(db: Session) -> int:
    return (
        db.query(InvestorMessage)
        .filter(InvestorMessage.from_admin.is_(False), InvestorMessage.is_read.is_(False))
        .count()
    )


def unread_by_investor(db: Session) -> dict[int, int]:
    rows = (
        db.query(InvestorMessage.investor_id)
        .filter(InvestorMessage.from_admin.is_(False), InvestorMessage.is_read.is_(False))
        .all()
    )
    counts: dict[int, int] = {}
    for (investor_id,) in rows:
        counts[investor_id] = counts.get(investor_id, 0) + 1
    return counts


def recent_unread_for_admin(db: Session, limit: int = 8) -> list[InvestorMessage]:
    return (
        db.query(InvestorMessage)
        .filter(InvestorMessage.from_admin.is_(False), InvestorMessage.is_read.is_(False))
        .order_by(InvestorMessage.created_at.desc())
        .limit(limit)
        .all()
    )
