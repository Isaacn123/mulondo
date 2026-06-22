from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.core.config import get_settings
from app.core.auth import get_session_user_id
from app.database import SessionLocal
from app.services import user_service

settings = get_settings()


def portal_url(path: str) -> str:
    prefix = settings.investor_path_prefix.rstrip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    if not prefix:
        return path
    if path == "/":
        return f"{prefix}/"
    return f"{prefix}{path}"


PORTAL_PUBLIC_PATHS = frozenset({"/portal/login", "/portal/logout"})


def requires_portal_auth(path: str) -> bool:
    prefix = settings.investor_path_prefix.rstrip("/")
    if not prefix:
        return False
    if path in PORTAL_PUBLIC_PATHS:
        return False
    if path.startswith(f"{prefix}/static"):
        return False
    return path == prefix or path.startswith(f"{prefix}/")


def is_investor_session(request: Request) -> bool:
    if request.session.get("account_type") != "investor":
        return False
    user_id = get_session_user_id(request)
    if not user_id:
        return False
    db = SessionLocal()
    try:
        user = user_service.get_user(db, user_id)
        return user is not None and not user.is_admin and user.is_active
    finally:
        db.close()


class PortalAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not requires_portal_auth(path):
            return await call_next(request)
        if request.method == "POST" and path == portal_url("/login"):
            return await call_next(request)
        if not is_investor_session(request):
            return RedirectResponse(url=portal_url("/login"), status_code=302)
        return await call_next(request)
