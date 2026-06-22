import re

from sqlalchemy.orm import Session

from app.models.user import InvestorMessage, User
from app.util.users_utility import hash_password


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.username).all()


def list_investors(db: Session) -> list[User]:
    return (
        db.query(User)
        .filter(User.is_admin.is_(False))
        .order_by(User.id.desc())
        .all()
    )


def count_investors(db: Session) -> tuple[int, int]:
    base = db.query(User).filter(User.is_admin.is_(False))
    total = base.count()
    active = base.filter(User.is_active.is_(True)).count()
    return total, active

def get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_investor(db: Session, user_id: int) -> User | None:
    return (
        db.query(User)
        .filter(
            User.id == user_id,
            User.is_admin.is_(False),
            User.is_active.is_(True),
            User.portal_role == "investor",
        )
        .first()
    )


def get_mentee(db: Session, user_id: int) -> User | None:
    return (
        db.query(User)
        .filter(
            User.id == user_id,
            User.is_admin.is_(False),
            User.is_active.is_(True),
            User.portal_role == "mentee",
        )
        .first()
    )


def get_user_by_username(db: Session, username: str) -> User | None:
    return (
        db.query(User)
        .filter(User.username == username, User.is_active.is_(True))
        .first()
    )


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return (
        db.query(User)
        .filter(User.id == user_id, User.is_active.is_(True))
        .first()
    )


def get_user_by_username_any(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str, exclude_id: int | None = None) -> User | None:
    query = db.query(User).filter(User.email == email)
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)
    return query.first()


def count_active_admins(db: Session, exclude_id: int | None = None) -> int:
    query = db.query(User).filter(User.is_admin.is_(True), User.is_active.is_(True))
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)
    return query.count()


def _slug_username(base: str, db: Session) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "investor"
    candidate = slug
    index = 2
    while get_user_by_username_any(db, candidate):
        candidate = f"{slug}-{index}"
        index += 1
    return candidate


def create_user(
    db: Session,
    *,
    username: str,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    is_admin: bool = False,
    is_active: bool = True,
) -> User:
    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        password_hash=hash_password(password),
        is_admin=is_admin,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_investor(
    db: Session,
    *,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    notify_registration: bool = True,
    mark_seen_by_admin: bool = False,
) -> User:
    local = email.split("@")[0]
    username = _slug_username(local or f"{first_name}-{last_name}", db)
    user = User(
        username=username,
        email=email.strip().lower(),
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        password_hash=hash_password(password),
        is_admin=False,
        is_active=True,
        portal_role="investor",
        admin_registration_seen=mark_seen_by_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    if notify_registration:
        from app.services.registration_service import notify_investor_registered

        notify_investor_registered(db, user, notify_admin=not mark_seen_by_admin)
    return user


def create_mentee(
    db: Session,
    *,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    notify_registration: bool = True,
    mark_seen_by_admin: bool = False,
) -> User:
    local = email.split("@")[0]
    username = _slug_username(local or f"{first_name}-{last_name}", db)
    user = User(
        username=username,
        email=email.strip().lower(),
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        password_hash=hash_password(password),
        is_admin=False,
        is_active=True,
        portal_role="mentee",
        admin_registration_seen=mark_seen_by_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    if notify_registration:
        from app.services.registration_service import notify_mentee_registered

        notify_mentee_registered(db, user, notify_admin=not mark_seen_by_admin)
    return user


def update_user(
    db: Session,
    user: User,
    *,
    username: str,
    email: str,
    password: str | None,
    first_name: str = "",
    last_name: str = "",
    is_admin: bool,
    is_active: bool,
) -> User:
    user.username = username
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    user.is_admin = is_admin
    user.is_active = is_active
    if password:
        user.password_hash = hash_password(password)
    db.commit()
    db.refresh(user)
    return user
