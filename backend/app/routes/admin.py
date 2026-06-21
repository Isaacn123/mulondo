from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_PAGES = [
  # Overview
  ("overview/site-statistics", "Site Statistics", "View site traffic and engagement metrics.", "overview", "site-statistics"),
  ("overview/visitors", "Visitors", "Track visitor sessions and geographic distribution.", "overview", "visitors"),
  ("overview/leads", "Leads", "Review inbound lead activity and conversion trends.", "overview", "leads"),
  ("overview/consultation-requests", "Consultation Requests", "Manage consultation requests from the public site.", "overview", "consultation-requests"),
  # Homepage (hero, trust, about, philosophy have dedicated forms in routes/homepage.py)
  # Services (dedicated forms in routes/services.py)
  # Markets (dedicated forms in routes/markets.py)
  ("homepage/ai-banner", "AI Banner", "Configure the AI banner section on the homepage.", "pages", "ai-banner"),
  # Calculator (dedicated forms in routes/calculator.py)
  # Insights (dedicated forms in routes/insights.py)
  # Coverage (dedicated forms in routes/coverage.py)
  # Clients (dedicated forms in routes/clients.py)
  # Contact form & Calendly (dedicated forms in routes/contact.py)
  # Leads & contacts (contact-submissions handled in routes/submissions.py)
  ("leads/consultation-requests", "Consultation Requests", "Review consultation booking requests.", "pages", "leads-consultation-requests"),
  ("leads/newsletter", "Newsletter Subscribers", "Manage newsletter subscriber list.", "pages", "newsletter"),
  # Bookings (Calendly settings in routes/contact.py)
  ("bookings/meetings", "Meetings", "View scheduled meetings and appointments.", "pages", "meetings"),
  # Partners
  ("partners/xa-markets", "XA Markets", "Manage XA Markets partner information.", "pages", "xa-markets"),
  ("partners/affiliates", "Affiliates", "Manage affiliate partners and referral links.", "pages", "affiliates"),
  # Media
  ("media/images", "Images", "Upload and manage site images.", "pages", "images"),
  ("media/videos", "Videos", "Upload and manage site videos.", "pages", "videos"),
  ("media/documents", "Documents", "Upload and manage downloadable documents.", "pages", "documents"),
  # SEO
  ("seo/meta-tags", "Meta Tags", "Manage page titles, descriptions and meta keywords.", "seo", "meta-tags"),
  ("seo/open-graph", "Open Graph", "Configure social sharing previews and Open Graph tags.", "seo", "open-graph"),
  ("seo/sitemap", "Sitemap", "Manage sitemap entries and crawl settings.", "seo", "sitemap"),
  # System
  ("settings", "Settings", "Configure global site and admin settings.", "settings", "settings"),
  ("forgot-password", "Forgot Password", "Password recovery page configuration.", "pages", "forgot-password"),
  ("404", "404 Page", "Customize the not-found page content.", "pages", "404"),
  ("blank", "Blank Page", "Starter page template for new admin sections.", "pages", "blank"),
]


def render_admin_page(
    request: Request,
    title: str,
    description: str,
    active_nav: str,
    active_item: str,
):
    return templates.TemplateResponse(
        request,
        "admin/page.html",
        {
            "page_title": title,
            "page_description": description,
            "active_nav": active_nav,
            "active_item": active_item,
        },
    )


def make_page_handler(title: str, description: str, active_nav: str, active_item: str):
    async def handler(request: Request):
        return render_admin_page(request, title, description, active_nav, active_item)

    handler.__name__ = f"admin_{active_item.replace('-', '_')}"
    return handler


for route_path, title, description, active_nav, active_item in ADMIN_PAGES:
    router.add_api_route(
        f"/{route_path}",
        make_page_handler(title, description, active_nav, active_item),
        methods=["GET"],
        name=f"admin-{route_path.replace('/', '-')}",
    )
