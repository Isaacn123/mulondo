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


def _portal_label(user: User) -> str:
    return "AISkills" if user.portal_role == "mentee" else "investor dashboard"


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
    brevo_service.notify_investor_new_message(
        investor.full_name,
        investor.email,
        body,
        portal_label=_portal_label(investor),
    )
    return message


def post_investor_welcome_message(db: Session, investor: User) -> InvestorMessage:
    """Dashboard welcome note for new investors."""
    message = InvestorMessage(
        investor_id=investor.id,
        from_admin=True,
        body=(
            "Welcome to your investor dashboard. Your account is active — browse member materials, "
            "check updates here, and message our team anytime you have questions."
        ),
        is_read=False,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def post_moodle_welcome_message(db: Session, mentee: User) -> InvestorMessage:
    """Dashboard welcome note for new Moodle mentees."""
    message = InvestorMessage(
        investor_id=mentee.id,
        from_admin=True,
        body=(
            "Welcome to AISkills — Build AI-Powered Trading Skills Mentorship. Open the training curriculum, "
            "follow the structured floor plan, and message your mentor anytime."
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
    brevo_service.notify_admin_investor_message(
        investor.full_name,
        investor.email,
        body,
        portal_label=_portal_label(investor),
    )
    return message


SUPPORT_CATEGORY_LABELS: dict[str, str] = {
    "kyc": "KYC / Identity verification",
    "account": "Account access",
    "resources": "Resources & materials",
    "membership": "Membership & billing",
    "mentorship": "Training & curriculum",
    "technical": "Technical issue",
    "other": "Other",
}

INVESTOR_SUPPORT_CATEGORIES = (
    ("kyc", SUPPORT_CATEGORY_LABELS["kyc"]),
    ("account", SUPPORT_CATEGORY_LABELS["account"]),
    ("resources", SUPPORT_CATEGORY_LABELS["resources"]),
    ("membership", SUPPORT_CATEGORY_LABELS["membership"]),
    ("technical", SUPPORT_CATEGORY_LABELS["technical"]),
    ("other", SUPPORT_CATEGORY_LABELS["other"]),
)

MOODLE_SUPPORT_CATEGORIES = (
    ("kyc", SUPPORT_CATEGORY_LABELS["kyc"]),
    ("mentorship", SUPPORT_CATEGORY_LABELS["mentorship"]),
    ("account", SUPPORT_CATEGORY_LABELS["account"]),
    ("resources", SUPPORT_CATEGORY_LABELS["resources"]),
    ("technical", SUPPORT_CATEGORY_LABELS["technical"]),
    ("other", SUPPORT_CATEGORY_LABELS["other"]),
)


def format_support_message(*, category: str, subject: str, body: str) -> str:
    label = SUPPORT_CATEGORY_LABELS.get(category, category.replace("_", " ").title())
    lines = [f"[Support — {label}]"]
    if subject.strip():
        lines.append(f"Subject: {subject.strip()}")
    lines.append("")
    lines.append(body.strip())
    return "\n".join(lines)


def send_support_request(
    db: Session,
    user: User,
    *,
    category: str,
    subject: str,
    body: str,
) -> InvestorMessage:
    if not body.strip():
        raise ValueError("Message is required.")
    if category not in SUPPORT_CATEGORY_LABELS:
        category = "other"
    formatted = format_support_message(category=category, subject=subject, body=body)
    return send_from_investor(db, user, formatted)


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


def list_unread_from_admin(db: Session, investor_id: int, limit: int = 10) -> list[InvestorMessage]:
    return (
        db.query(InvestorMessage)
        .filter(
            InvestorMessage.investor_id == investor_id,
            InvestorMessage.from_admin.is_(True),
            InvestorMessage.is_read.is_(False),
        )
        .order_by(InvestorMessage.created_at.desc())
        .limit(limit)
        .all()
    )


def recent_admin_messages(db: Session, investor_id: int, limit: int = 5) -> list[InvestorMessage]:
    return (
        db.query(InvestorMessage)
        .filter(
            InvestorMessage.investor_id == investor_id,
            InvestorMessage.from_admin.is_(True),
        )
        .order_by(InvestorMessage.created_at.desc())
        .limit(limit)
        .all()
    )


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
