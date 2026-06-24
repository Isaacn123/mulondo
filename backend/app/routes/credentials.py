from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.credentials import CredentialsContent
from app.services import r2_service
from app.services.credentials_service import credentials_from_form, load_credentials, public_credentials, save_credentials

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["credentials"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


def credentials_form_context(content: CredentialsContent, *, saved: bool = False):
    return {
        "page_title": "Professional Credentials",
        "page_description": "Manage accreditation cards on the homepage.",
        "active_nav": "pages",
        "active_item": "credentials",
        "credentials_content": content,
        "saved": saved,
        "r2_configured": r2_service.r2_configured(),
    }


@admin_router.get("/homepage/credentials")
async def credentials_edit_form(request: Request, saved: bool = Query(False)):
    content = load_credentials()
    return templates.TemplateResponse(
        request,
        "admin/homepage/credentials.html",
        credentials_form_context(content, saved=saved),
    )


@admin_router.post("/homepage/credentials")
async def credentials_save(request: Request):
    form = await request.form()
    content = CredentialsContent(
        eyebrow=(form.get("eyebrow") or "").strip(),
        title_before=(form.get("title_before") or "").strip(),
        title_highlight=(form.get("title_highlight") or "").strip(),
        intro=(form.get("intro") or "").strip(),
        footnote=(form.get("footnote") or "").strip(),
        credentials=credentials_from_form(form),
    )
    save_credentials(content)
    return RedirectResponse(url="/admin/homepage/credentials?saved=1", status_code=303)


@api_router.get("/credentials")
async def credentials_api() -> CredentialsContent:
    return public_credentials()
