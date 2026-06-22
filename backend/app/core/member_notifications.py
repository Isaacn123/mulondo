from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import get_settings
from app.core.moodle_auth import requires_moodle_auth
from app.core.portal_auth import requires_portal_auth
from app.database import SessionLocal
from app.services import message_service, user_service

settings = get_settings()


def _load_member_notifications(request: Request) -> None:
    user_id = request.session.get("user_id")
    account_type = request.session.get("account_type")
    if not user_id or account_type not in ("investor", "mentee"):
        return

    db = SessionLocal()
    try:
        if account_type == "mentee":
            user = user_service.get_mentee(db, int(user_id))
        else:
            user = user_service.get_investor(db, int(user_id))
        if user is None:
            return

        request.state.member_unread = message_service.unread_count_for_investor(db, user.id)
        request.state.member_notifications = message_service.list_unread_from_admin(db, user.id, limit=8)
    finally:
        db.close()


class MemberNotificationsMiddleware(BaseHTTPMiddleware):
    """Attach unread admin message counts to investor and Moodle portal pages."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        request.state.member_unread = 0
        request.state.member_notifications = []
        if requires_portal_auth(path) or requires_moodle_auth(path):
            login_suffixes = ("/login", "/logout")
            if not any(path.rstrip("/").endswith(suffix) for suffix in login_suffixes):
                _load_member_notifications(request)
        return await call_next(request)
