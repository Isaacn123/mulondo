from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.auth import get_session_user_id, requires_admin_auth
from app.database import SessionLocal
from app.services import user_service


class AdminContextMiddleware(BaseHTTPMiddleware):
    """Attach the signed-in admin user to request.state for templates."""

    async def dispatch(self, request: Request, call_next):
        if (
            requires_admin_auth(request.url.path)
            and request.session.get("account_type") == "admin"
        ):
            user_id = get_session_user_id(request)
            if user_id:
                db = SessionLocal()
                try:
                    user = user_service.get_user(db, user_id)
                    if user and user.is_admin and user.is_active:
                        request.state.admin_user = user
                finally:
                    db.close()
        return await call_next(request)
