from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.homepage_layout import HomepageLayout, HomepageSection
from app.schemas.navigation import NavLink, NavigationContent
from app.services import homepage_layout_service, navigation_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["site-layout"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


@admin_router.get("/site/navigation")
async def navigation_edit_form(request: Request, saved: bool = Query(False)):
    navigation = navigation_service.load_navigation()
    all_links = sorted(navigation.links, key=lambda link: (-link.sort_order, link.label.lower()))
    return templates.TemplateResponse(
        request,
        "admin/site/navigation.html",
        {
            "page_title": "Site Navigation",
            "page_description": "Manage header and footer links on the public site.",
            "active_nav": "pages",
            "active_item": "site-navigation",
            "links": all_links,
            "saved": saved,
        },
    )


@admin_router.post("/site/navigation")
async def navigation_save(request: Request):
    form = await request.form()
    keys = [key for key in form.getlist("link_key")]
    links: list[NavLink] = []
    for key in keys:
        links.append(
            NavLink(
                key=key,
                label=(form.get(f"{key}_label") or "").strip(),
                href=(form.get(f"{key}_href") or "").strip(),
                enabled=f"{key}_enabled" in form,
                show_in_header=f"{key}_header" in form,
                show_in_footer=f"{key}_footer" in form,
                sort_order=int(form.get(f"{key}_sort_order") or 0),
                style="cta" if form.get(f"{key}_style") == "cta" else "link",
            )
        )
    navigation_service.save_navigation(NavigationContent(links=links))
    return RedirectResponse(url="/admin/site/navigation?saved=1", status_code=303)


@admin_router.get("/site/homepage-layout")
async def homepage_layout_edit_form(request: Request, saved: bool = Query(False)):
    layout = homepage_layout_service.load_homepage_layout()
    sections = homepage_layout_service.sorted_sections(layout)
    return templates.TemplateResponse(
        request,
        "admin/site/homepage_layout.html",
        {
            "page_title": "Homepage Layout",
            "page_description": "Show, hide, and reorder homepage sections on the public site.",
            "active_nav": "pages",
            "active_item": "homepage-layout",
            "sections": sections,
            "saved": saved,
        },
    )


@admin_router.post("/site/homepage-layout")
async def homepage_layout_save(request: Request):
    form = await request.form()
    keys = [key for key in form.getlist("section_key")]
    sections: list[HomepageSection] = []
    for key in keys:
        sections.append(
            HomepageSection(
                key=key,
                label=(form.get(f"{key}_label") or key).strip(),
                element_id=(form.get(f"{key}_element_id") or key).strip(),
                enabled=f"{key}_enabled" in form,
                sort_order=int(form.get(f"{key}_sort_order") or 0),
            )
        )
    homepage_layout_service.save_homepage_layout(HomepageLayout(sections=sections))
    return RedirectResponse(url="/admin/site/homepage-layout?saved=1", status_code=303)


@api_router.get("/navigation")
async def navigation_api():
    return navigation_service.load_navigation()


@api_router.get("/homepage-layout")
async def homepage_layout_api():
    return homepage_layout_service.load_homepage_layout()
