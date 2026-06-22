from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.core.config import get_settings
from app.core.auth import get_session_user_id
from app.database import SessionLocal
from app.services import user_service

settings = get_settings()


def moodle_url(path: str) -> str:
    prefix = settings.moodle_path_prefix.rstrip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    if not prefix:
        return path
    if path == "/":
        return f"{prefix}/"
    return f"{prefix}{path}"


def moodle_public_paths() -> frozenset[str]:
    prefix = settings.moodle_path_prefix.rstrip("/")
    if not prefix:
        return frozenset()
    return frozenset(
        {
            moodle_url("/login"),
            moodle_url("/logout"),
            f"{prefix}/login/",
            f"{prefix}/logout/",
        }
    )


def requires_moodle_auth(path: str) -> bool:
    prefix = settings.moodle_path_prefix.rstrip("/")
    if not prefix:
        return False
    normalized = path.rstrip("/") or "/"
    public = {p.rstrip("/") or "/" for p in moodle_public_paths()}
    if normalized in public:
        return False
    if path.startswith(f"{prefix}/static"):
        return False
    return path == prefix or path.startswith(f"{prefix}/")


def is_mentee_session(request: Request) -> bool:
    if request.session.get("account_type") != "mentee":
        return False
    user_id = get_session_user_id(request)
    if not user_id:
        return False
    db = SessionLocal()
    try:
        user = user_service.get_mentee(db, user_id)
        return user is not None
    finally:
        db.close()


class MoodleAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not requires_moodle_auth(path):
            return await call_next(request)
        login_path = moodle_url("/login")
        if request.method == "POST" and path.rstrip("/") == login_path.rstrip("/"):
            return await call_next(request)
        if not is_mentee_session(request):
            return RedirectResponse(url=login_path, status_code=302)
        return await call_next(request)
