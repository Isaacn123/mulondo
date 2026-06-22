from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.core.admin_errors import (
    admin_http_exception_handler,
    admin_starlette_http_exception_handler,
    admin_unhandled_exception_handler,
)
from app.core.auth import AdminAuthMiddleware
from app.core.config import get_settings
from app.core.portal_auth import PortalAuthMiddleware, portal_url
from app.routes import (
    admin,
    blog,
    calculator,
    clients,
    contact,
    coverage,
    dashboard,
    homepage,
    insights,
    investor_auth,
    investors,
    login,
    market_data,
    markets,
    membership,
    mentorship,
    portal,
    services,
    submissions,
    upload,
    users,
)
from app.routes.submissions import AdminNotificationsMiddleware

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
settings = get_settings()


app = FastAPI()

app.add_exception_handler(HTTPException, admin_http_exception_handler)
app.add_exception_handler(StarletteHTTPException, admin_starlette_http_exception_handler)
app.add_exception_handler(Exception, admin_unhandled_exception_handler)

app.add_middleware(AdminNotificationsMiddleware)
app.add_middleware(AdminAuthMiddleware)
app.add_middleware(PortalAuthMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    max_age=settings.session_max_age,
    same_site="lax",
    https_only=False,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.get("/")
# async def root():
#     return {
#         "users": 1250,
#         "sales": 5200,
#         "orders": 184
#     }

app.include_router(investor_auth.router)
app.include_router(portal.router)
app.include_router(investors.admin_router)
app.include_router(upload.admin_router)
app.include_router(login.router)
app.include_router(dashboard.router)
app.include_router(blog.admin_router)
app.include_router(blog.api_router)
app.include_router(homepage.admin_router)
app.include_router(homepage.api_router)
app.include_router(services.admin_router)
app.include_router(services.api_router)
app.include_router(markets.admin_router)
app.include_router(markets.api_router)
app.include_router(calculator.admin_router)
app.include_router(calculator.api_router)
app.include_router(insights.admin_router)
app.include_router(insights.api_router)
app.include_router(coverage.admin_router)
app.include_router(coverage.api_router)
app.include_router(clients.admin_router)
app.include_router(clients.api_router)
app.include_router(membership.admin_router)
app.include_router(membership.api_router)
app.include_router(mentorship.admin_router)
app.include_router(mentorship.api_router)
app.include_router(contact.admin_router)
app.include_router(contact.bookings_router)
app.include_router(contact.api_router)
app.include_router(users.admin_router)
app.include_router(submissions.api_router)
app.include_router(submissions.webhook_router)
app.include_router(submissions.admin_router)
app.include_router(market_data.router)
app.include_router(admin.router)

static_files = StaticFiles(directory=str(STATIC_DIR))
_investor_static = settings.investor_path_prefix.rstrip("/") or "/investors"
app.mount("/admin/static", static_files, name="admin-static")
app.mount(f"{_investor_static}/static", static_files, name="investor-static")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)))


@app.get("/portal")
@app.get("/portal/{path:path}")
async def legacy_portal_redirect(path: str = ""):
    """Redirect old /portal URLs to /investors (avoids broken bookmarks)."""
    target = portal_url(f"/{path}") if path else portal_url("/")
    return RedirectResponse(url=target, status_code=301)
