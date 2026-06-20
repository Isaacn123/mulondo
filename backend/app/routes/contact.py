from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.contact import CalendlyConfig, ContactContent, ContactFormConfig
from app.services.contact_service import load_contact, save_contact

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["contact"])
bookings_router = APIRouter(prefix="/admin/bookings", tags=["bookings"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


def _parse_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


@admin_router.get("/contact")
async def contact_section_form(request: Request, saved: bool = Query(False)):
    contact = load_contact()
    return templates.TemplateResponse(
        request,
        "admin/contact/section.html",
        {
            "page_title": "Contact Section",
            "active_nav": "pages",
            "active_item": "contact-section",
            "contact": contact,
            "saved": saved,
        },
    )


@admin_router.post("/contact")
async def contact_section_save(
    request: Request,
    eyebrow: str = Form(...),
    title_before: str = Form(...),
    title_highlight: str = Form(...),
    intro: str = Form(...),
):
    contact = load_contact()
    updated = contact.model_copy(
        update={
            "eyebrow": eyebrow.strip(),
            "title_before": title_before.strip(),
            "title_highlight": title_highlight.strip(),
            "intro": intro.strip(),
        }
    )
    save_contact(updated)
    return RedirectResponse(url="/admin/contact?saved=1", status_code=303)


@admin_router.get("/contact/form")
async def contact_form_settings(request: Request, saved: bool = Query(False)):
    contact = load_contact()
    return templates.TemplateResponse(
        request,
        "admin/contact/form.html",
        {
            "page_title": "Contact Form",
            "active_nav": "pages",
            "active_item": "contact-form",
            "contact": contact,
            "saved": saved,
        },
    )


@admin_router.post("/contact/form")
async def contact_form_save(
    request: Request,
    form_title: str = Form(...),
    form_subtitle: str = Form(...),
    action_url: str = Form(...),
    submit_text: str = Form(...),
    consent_text: str = Form(...),
    country_placeholder: str = Form(...),
    message_placeholder: str = Form(""),
    investor_types: str = Form(...),
    capital_ranges: str = Form(...),
):
    contact = load_contact()
    updated = contact.model_copy(
        update={
            "form": ContactFormConfig(
                title=form_title.strip(),
                subtitle=form_subtitle.strip(),
                action_url=action_url.strip(),
                submit_text=submit_text.strip(),
                consent_text=consent_text.strip(),
                country_placeholder=country_placeholder.strip(),
                message_placeholder=message_placeholder.strip(),
                investor_types=_parse_lines(investor_types),
                capital_ranges=_parse_lines(capital_ranges),
            )
        }
    )
    save_contact(updated)
    return RedirectResponse(url="/admin/contact/form?saved=1", status_code=303)


@bookings_router.get("/calendly")
async def calendly_settings_form(request: Request, saved: bool = Query(False)):
    contact = load_contact()
    return templates.TemplateResponse(
        request,
        "admin/contact/calendly.html",
        {
            "page_title": "Calendly",
            "active_nav": "pages",
            "active_item": "calendly",
            "contact": contact,
            "saved": saved,
        },
    )


@bookings_router.post("/calendly")
async def calendly_settings_save(
    request: Request,
    calendly_title: str = Form(...),
    calendly_subtitle: str = Form(...),
    widget_url: str = Form(...),
    fallback_url: str = Form(...),
    widget_height: int = Form(...),
):
    contact = load_contact()
    updated = contact.model_copy(
        update={
            "calendly": CalendlyConfig(
                title=calendly_title.strip(),
                subtitle=calendly_subtitle.strip(),
                widget_url=widget_url.strip(),
                fallback_url=fallback_url.strip(),
                widget_height=widget_height,
            )
        }
    )
    save_contact(updated)
    return RedirectResponse(url="/admin/bookings/calendly?saved=1", status_code=303)


@api_router.get("/contact")
async def contact_api() -> ContactContent:
    return load_contact()
