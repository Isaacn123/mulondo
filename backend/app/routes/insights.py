from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.insights import (
    InsightsContent,
    InsightsWidget,
    ResearchArticle,
    TradingViewEventsSettings,
    TradingViewNewsSettings,
    slugify,
)
from app.services.insights_service import (
    add_research_article,
    delete_research_article,
    get_research_article,
    load_insights,
    save_insights,
    update_research_article,
)

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["insights"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


@admin_router.get("/insights")
async def insights_section_form(request: Request, saved: bool = Query(False)):
    insights = load_insights()
    return templates.TemplateResponse(
        request,
        "admin/insights/section.html",
        {
            "page_title": "Insights Section",
            "active_nav": "pages",
            "active_item": "insights-section",
            "insights": insights,
            "saved": saved,
        },
    )


@admin_router.post("/insights")
async def insights_section_save(
    request: Request,
    eyebrow: str = Form(...),
    title_before: str = Form(...),
    title_highlight: str = Form(...),
):
    insights = load_insights()
    updated = insights.model_copy(
        update={
            "eyebrow": eyebrow.strip(),
            "title_before": title_before.strip(),
            "title_highlight": title_highlight.strip(),
        }
    )
    save_insights(updated)
    return RedirectResponse(url="/admin/insights?saved=1", status_code=303)


@admin_router.get("/insights/news")
async def insights_news_form(request: Request, saved: bool = Query(False)):
    insights = load_insights()
    return templates.TemplateResponse(
        request,
        "admin/insights/news.html",
        {
            "page_title": "Market News Widget",
            "active_nav": "pages",
            "active_item": "news",
            "insights": insights,
            "saved": saved,
        },
    )


@admin_router.post("/insights/news")
async def insights_news_save(
    request: Request,
    news_title: str = Form(...),
    news_enabled: str | None = Form(None),
    feed_mode: str = Form(...),
    display_mode: str = Form(...),
    color_theme: str = Form(...),
    locale: str = Form(...),
    is_transparent: str | None = Form(None),
):
    insights = load_insights()
    updated = insights.model_copy(
        update={
            "news": InsightsWidget(title=news_title.strip(), enabled=news_enabled == "1"),
            "news_settings": TradingViewNewsSettings(
                feed_mode=feed_mode.strip(),
                display_mode=display_mode.strip(),
                color_theme=color_theme.strip(),
                locale=locale.strip(),
                is_transparent=is_transparent == "1",
            ),
        }
    )
    save_insights(updated)
    return RedirectResponse(url="/admin/insights/news?saved=1", status_code=303)


@admin_router.get("/insights/economic-calendar")
async def insights_calendar_form(request: Request, saved: bool = Query(False)):
    insights = load_insights()
    return templates.TemplateResponse(
        request,
        "admin/insights/economic_calendar.html",
        {
            "page_title": "Economic Calendar Widget",
            "active_nav": "pages",
            "active_item": "economic-calendar",
            "insights": insights,
            "saved": saved,
        },
    )


@admin_router.post("/insights/economic-calendar")
async def insights_calendar_save(
    request: Request,
    calendar_title: str = Form(...),
    calendar_enabled: str | None = Form(None),
    color_theme: str = Form(...),
    locale: str = Form(...),
    is_transparent: str | None = Form(None),
    importance_filter: str = Form(...),
    country_filter: str = Form(...),
):
    insights = load_insights()
    updated = insights.model_copy(
        update={
            "economic_calendar": InsightsWidget(
                title=calendar_title.strip(),
                enabled=calendar_enabled == "1",
            ),
            "events_settings": TradingViewEventsSettings(
                color_theme=color_theme.strip(),
                locale=locale.strip(),
                is_transparent=is_transparent == "1",
                importance_filter=importance_filter.strip(),
                country_filter=country_filter.strip(),
            ),
        }
    )
    save_insights(updated)
    return RedirectResponse(url="/admin/insights/economic-calendar?saved=1", status_code=303)


@admin_router.get("/insights/research")
async def insights_research_list(request: Request, saved: bool = Query(False), deleted: bool = Query(False)):
    insights = load_insights()
    return templates.TemplateResponse(
        request,
        "admin/insights/research.html",
        {
            "page_title": "Research Articles",
            "active_nav": "pages",
            "active_item": "research",
            "insights": insights,
            "saved": saved,
            "deleted": deleted,
        },
    )


@admin_router.get("/insights/research/new")
async def insights_research_new_form(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/insights/research_form.html",
        {
            "page_title": "Add Research Article",
            "active_nav": "pages",
            "active_item": "research",
            "article": None,
            "is_new": True,
        },
    )


@admin_router.post("/insights/research/new")
async def insights_research_create(
    request: Request,
    title: str = Form(...),
    excerpt: str = Form(""),
    url: str = Form(""),
    published_at: str = Form(""),
    enabled: str | None = Form(None),
):
    article = ResearchArticle(
        slug=slugify(title),
        title=title.strip(),
        excerpt=excerpt.strip(),
        url=url.strip(),
        published_at=published_at.strip(),
        enabled=enabled == "1",
    )
    add_research_article(article)
    return RedirectResponse(url="/admin/insights/research?saved=1", status_code=303)


@admin_router.get("/insights/research/{slug}")
async def insights_research_edit_form(request: Request, slug: str, saved: bool = Query(False)):
    article = get_research_article(slug)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return templates.TemplateResponse(
        request,
        "admin/insights/research_form.html",
        {
            "page_title": "Edit Research Article",
            "active_nav": "pages",
            "active_item": "research",
            "article": article,
            "is_new": False,
            "saved": saved,
        },
    )


@admin_router.post("/insights/research/{slug}")
async def insights_research_update(
    request: Request,
    slug: str,
    title: str = Form(...),
    excerpt: str = Form(""),
    url: str = Form(""),
    published_at: str = Form(""),
    enabled: str | None = Form(None),
):
    existing = get_research_article(slug)
    if existing is None:
        raise HTTPException(status_code=404, detail="Article not found")
    article = ResearchArticle(
        slug=slug,
        title=title.strip(),
        excerpt=excerpt.strip(),
        url=url.strip(),
        published_at=published_at.strip(),
        enabled=enabled == "1",
    )
    update_research_article(slug, article)
    return RedirectResponse(url=f"/admin/insights/research/{slug}?saved=1", status_code=303)


@admin_router.post("/insights/research/{slug}/delete")
async def insights_research_delete(request: Request, slug: str):
    try:
        delete_research_article(slug)
    except KeyError:
        raise HTTPException(status_code=404, detail="Article not found")
    return RedirectResponse(url="/admin/insights/research?deleted=1", status_code=303)


@api_router.get("/insights")
async def insights_api() -> InsightsContent:
    return load_insights()
