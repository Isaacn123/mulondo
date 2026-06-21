"""Create the initial admin user if none exists.

    python -m app.scripts.seed_admin_user

Requires ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL in .env (see .env.example).
"""
from app.core.config import get_settings
from app.database import SessionLocal
from app.models.user import User
from app.util.users_utility import hash_password

settings = get_settings()


def main() -> None:
    if not settings.admin_username or not settings.admin_password:
        print("Set ADMIN_USERNAME and ADMIN_PASSWORD in .env before seeding.")
        return

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == settings.admin_username).first()
        if existing:
            print(f"Admin user '{settings.admin_username}' already exists (id={existing.id}).")
            return

        user = User(
            username=settings.admin_username,
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            is_active=True,
            is_admin=True,
        )
        db.add(user)
        db.commit()
        print(f"Created admin user '{settings.admin_username}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
