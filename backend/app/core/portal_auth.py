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


def portal_public_paths() -> frozenset[str]:
    """Paths that must stay accessible without an investor session."""
    prefix = settings.investor_path_prefix.rstrip("/")
    if not prefix:
        return frozenset()
    return frozenset(
        {
            portal_url("/login"),
            portal_url("/logout"),
            f"{prefix}/login/",
            f"{prefix}/logout/",
        }
    )


def requires_portal_auth(path: str) -> bool:
    prefix = settings.investor_path_prefix.rstrip("/")
    if not prefix:
        return False
    normalized = path.rstrip("/") or "/"
    public = {p.rstrip("/") or "/" for p in portal_public_paths()}
    if normalized in public:
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
        user = user_service.get_investor(db, user_id)
        return user is not None
    finally:
        db.close()


class PortalAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not requires_portal_auth(path):
            return await call_next(request)
        login_path = portal_url("/login")
        if request.method == "POST" and path.rstrip("/") == login_path.rstrip("/"):
            return await call_next(request)
        if not is_investor_session(request):
            return RedirectResponse(url=login_path, status_code=302)
        return await call_next(request)
