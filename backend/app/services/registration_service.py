from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.portal_auth import portal_url
from app.models.user import User
from app.services import brevo_service, message_service


def _login_url() -> str:
    settings = get_settings()
    return f"{settings.public_site_url.rstrip('/')}{portal_url('/login')}"


def notify_investor_registered(db: Session, investor: User, *, notify_admin: bool = True) -> None:
    """Email admin + investor and add a welcome note on the investor dashboard."""
    if notify_admin:
        brevo_service.notify_admin_new_investor_registration(investor.full_name, investor.email)
    brevo_service.notify_investor_registration_welcome(
        investor.full_name,
        investor.email,
        _login_url(),
    )
    message_service.post_welcome_message(db, investor)


def count_unseen_registrations(db: Session) -> int:
    return (
        db.query(User)
        .filter(
            User.is_admin.is_(False),
            User.is_active.is_(True),
            User.admin_registration_seen.is_(False),
        )
        .count()
    )


def list_unseen_registrations(db: Session, limit: int = 8) -> list[User]:
    return (
        db.query(User)
        .filter(
            User.is_admin.is_(False),
            User.is_active.is_(True),
            User.admin_registration_seen.is_(False),
        )
        .order_by(User.created_at.desc())
        .limit(limit)
        .all()
    )


def mark_registration_seen(db: Session, investor_id: int) -> None:
    investor = db.query(User).filter(User.id == investor_id, User.is_admin.is_(False)).first()
    if investor and not investor.admin_registration_seen:
        investor.admin_registration_seen = True
        db.commit()


def mark_all_registrations_seen(db: Session) -> None:
    (
        db.query(User)
        .filter(User.is_admin.is_(False), User.admin_registration_seen.is_(False))
        .update({"admin_registration_seen": True})
    )
    db.commit()
