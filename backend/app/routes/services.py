from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.services import SERVICE_LABELS, SERVICE_SLUGS, ServiceCard, ServicesContent
from app.services.services_service import get_service_card, load_services, save_services, update_service_card

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["services"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


@admin_router.get("/services")
async def services_section_form(request: Request, saved: bool = Query(False)):
    services = load_services()
    return templates.TemplateResponse(
        request,
        "admin/services/section.html",
        {
            "page_title": "Services Section",
            "active_nav": "pages",
            "active_item": "services-section",
            "services": services,
            "saved": saved,
        },
    )


@admin_router.post("/services")
async def services_section_save(
    request: Request,
    eyebrow: str = Form(...),
    title_before: str = Form(...),
    title_highlight: str = Form(...),
):
    services = load_services()
    updated = services.model_copy(
        update={
            "eyebrow": eyebrow.strip(),
            "title_before": title_before.strip(),
            "title_highlight": title_highlight.strip(),
        }
    )
    save_services(updated)
    return RedirectResponse(url="/admin/services?saved=1", status_code=303)


@admin_router.get("/services/{slug}")
async def service_card_form(request: Request, slug: str, saved: bool = Query(False)):
    if slug not in SERVICE_SLUGS:
        raise HTTPException(status_code=404, detail="Service not found")
    card = get_service_card(slug)
    return templates.TemplateResponse(
        request,
        "admin/services/card.html",
        {
            "page_title": SERVICE_LABELS[slug],
            "active_nav": "pages",
            "active_item": slug,
            "card": card,
            "slug": slug,
            "saved": saved,
        },
    )


@admin_router.post("/services/{slug}")
async def service_card_save(
    request: Request,
    slug: str,
    icon: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
):
    if slug not in SERVICE_SLUGS:
        raise HTTPException(status_code=404, detail="Service not found")
    card = ServiceCard(
        slug=slug,
        icon=icon.strip(),
        title=title.strip(),
        description=description.strip(),
    )
    update_service_card(slug, card)
    return RedirectResponse(url=f"/admin/services/{slug}?saved=1", status_code=303)


@api_router.get("/services")
async def services_api() -> ServicesContent:
    return load_services()
