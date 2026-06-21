from sqlalchemy.orm import Session

from app.models.user import User
from app.util.users_utility import hash_password


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.username).all()


def get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


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


def create_user(
    db: Session,
    *,
    username: str,
    email: str,
    password: str,
    is_admin: bool = False,
    is_active: bool = True,
) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        is_admin=is_admin,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user: User,
    *,
    username: str,
    email: str,
    password: str | None,
    is_admin: bool,
    is_active: bool,
) -> User:
    user.username = username
    user.email = email
    user.is_admin = is_admin
    user.is_active = is_active
    if password:
        user.password_hash = hash_password(password)
    db.commit()
    db.refresh(user)
    return user
