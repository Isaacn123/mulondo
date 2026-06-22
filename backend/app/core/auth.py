from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi import HTTPException

from app.core.config import get_settings

settings = get_settings()

PUBLIC_PATHS = frozenset(
    {
        "/admin/login",
        "/admin/logout",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
)
PUBLIC_PREFIXES = (
    "/static",
    "/admin/static",
    "/api/",
)


def admin_url(path: str) -> str:
    """Build admin URL (nginx passes full /admin/* paths to the backend)."""
    prefix = settings.admin_path_prefix.rstrip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    if not prefix:
        return path
    if path == "/":
        return f"{prefix}/"
    return f"{prefix}{path}"


def is_public_path(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def requires_admin_auth(path: str) -> bool:
    if is_public_path(path):
        return False
    prefix = settings.admin_path_prefix.rstrip("/")
    if not prefix:
        return False
    return path == prefix or path.startswith(f"{prefix}/")


def get_session_user_id(request: Request) -> int | None:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def require_login(request: Request) -> int:
    """Dependency: raise 401 if not authenticated (for JSON/API use)."""
    user_id = get_session_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


def require_login_redirect(request: Request) -> int | RedirectResponse:
    """Dependency: redirect to login for HTML admin routes."""
    user_id = get_session_user_id(request)
    if not user_id:
        return RedirectResponse(url=admin_url("/login"), status_code=302)
    return user_id


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """Redirect unauthenticated or non-admin users away from admin HTML routes."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not requires_admin_auth(path):
            return await call_next(request)
        if request.method == "POST" and path == admin_url("/login"):
            return await call_next(request)
        user_id = get_session_user_id(request)
        if not user_id or request.session.get("account_type") != "admin":
            return RedirectResponse(url=admin_url("/login"), status_code=302)
        return await call_next(request)
