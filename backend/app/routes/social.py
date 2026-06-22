from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.social import SocialContent, SocialLink
from app.services.social_service import load_social, save_social

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

PLATFORMS = ("x", "facebook", "linkedin", "instagram", "github", "youtube")

admin_router = APIRouter(prefix="/admin", tags=["social"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


@admin_router.get("/social")
async def social_edit_form(request: Request, saved: bool = Query(False)):
    social = load_social()
    by_platform = {link.platform: link for link in social.links}
    links = [
        by_platform.get(
            platform,
            SocialLink(platform=platform, label=platform.title(), url="", enabled=False),
        )
        for platform in PLATFORMS
    ]
    return templates.TemplateResponse(
        request,
        "admin/social/links.html",
        {
            "page_title": "Social Links",
            "page_description": "Manage social profile links shown in the site footer.",
            "active_nav": "pages",
            "active_item": "social-links",
            "links": links,
            "saved": saved,
        },
    )


@admin_router.post("/social")
async def social_save(request: Request):
    links: list[SocialLink] = []
    form = await request.form()
    for platform in PLATFORMS:
        label_key = f"{platform}_label"
        url_key = f"{platform}_url"
        enabled_key = f"{platform}_enabled"
        links.append(
            SocialLink(
                platform=platform,
                label=(form.get(label_key) or platform.title()).strip(),
                url=(form.get(url_key) or "").strip(),
                enabled=enabled_key in form,
            )
        )
    save_social(SocialContent(links=links))
    return RedirectResponse(url="/admin/social?saved=1", status_code=303)


@api_router.get("/social")
async def social_api():
    return load_social()
