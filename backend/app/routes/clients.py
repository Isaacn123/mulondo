from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.clients import ClientsContent
from app.services.clients_service import load_clients, save_clients

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["clients"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


def _parse_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


@admin_router.get("/clients")
async def clients_section_form(request: Request, saved: bool = Query(False)):
    clients = load_clients()
    return templates.TemplateResponse(
        request,
        "admin/clients/section.html",
        {
            "page_title": "Client Profile",
            "active_nav": "pages",
            "active_item": "clients-section",
            "clients": clients,
            "saved": saved,
        },
    )


@admin_router.post("/clients")
async def clients_section_save(
    request: Request,
    eyebrow: str = Form(...),
    title_before: str = Form(...),
    title_highlight: str = Form(...),
):
    clients = load_clients()
    updated = clients.model_copy(
        update={
            "eyebrow": eyebrow.strip(),
            "title_before": title_before.strip(),
            "title_highlight": title_highlight.strip(),
        }
    )
    save_clients(updated)
    return RedirectResponse(url="/admin/clients?saved=1", status_code=303)


@admin_router.get("/clients/profiles")
async def clients_profiles_form(request: Request, saved: bool = Query(False)):
    clients = load_clients()
    return templates.TemplateResponse(
        request,
        "admin/clients/profiles.html",
        {
            "page_title": "Client Profiles",
            "active_nav": "pages",
            "active_item": "client-profiles",
            "clients": clients,
            "saved": saved,
        },
    )


@admin_router.post("/clients/profiles")
async def clients_profiles_save(request: Request, profiles: str = Form(...)):
    clients = load_clients()
    updated = clients.model_copy(update={"profiles": _parse_lines(profiles)})
    save_clients(updated)
    return RedirectResponse(url="/admin/clients/profiles?saved=1", status_code=303)


@api_router.get("/clients")
async def clients_api() -> ClientsContent:
    return load_clients()
