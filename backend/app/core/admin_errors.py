from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _wants_admin_html(request: Request) -> bool:
    path = request.url.path
    if not path.startswith("/admin"):
        return False
    accept = request.headers.get("accept", "")
    return "text/html" in accept or "*/*" in accept or not accept


def _admin_back_link(path: str) -> tuple[str, str]:
    if path.startswith("/admin/blog"):
        return "/admin/blog", "Back to Blog"
    if path.startswith("/admin/users"):
        return "/admin/users", "Back to Users"
    if path.startswith("/admin/insights/research"):
        return "/admin/insights/research", "Back to Research"
    if path.startswith("/admin/services"):
        return "/admin/services", "Back to Services"
    return "/admin/", "Back to Dashboard"


def _friendly_title(status_code: int) -> str:
    if status_code == 404:
        return "This content is not available yet"
    if status_code == 400:
        return "Something was wrong with the request"
    if status_code == 403:
        return "You do not have access to this page"
    return "Something went wrong"


async def admin_http_exception_handler(request: Request, exc: HTTPException):
    if not _wants_admin_html(request):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    detail = exc.detail if isinstance(exc.detail, str) else "An unexpected error occurred."
    back_url, back_label = _admin_back_link(request.url.path)
    return templates.TemplateResponse(
        request,
        "admin/error.html",
        {
            "page_title": _friendly_title(exc.status_code),
            "status_code": exc.status_code,
            "title": _friendly_title(exc.status_code),
            "detail": detail,
            "back_url": back_url,
            "back_label": back_label,
            "active_nav": "",
            "active_item": "",
        },
        status_code=exc.status_code,
    )


async def admin_starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return await admin_http_exception_handler(
        request,
        HTTPException(status_code=exc.status_code, detail=exc.detail),
    )


async def admin_unhandled_exception_handler(request: Request, exc: Exception):
    if not _wants_admin_html(request):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    back_url, back_label = _admin_back_link(request.url.path)
    return templates.TemplateResponse(
        request,
        "admin/error.html",
        {
            "page_title": "Something went wrong",
            "status_code": 500,
            "title": "We could not load this page",
            "detail": "An unexpected error occurred. Try again, or return to the dashboard.",
            "back_url": back_url,
            "back_label": back_label,
            "active_nav": "",
            "active_item": "",
        },
        status_code=500,
    )
