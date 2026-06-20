from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.coverage import CoverageContent
from app.services.coverage_service import load_coverage, save_coverage

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["coverage"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


def _parse_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


@admin_router.get("/coverage")
async def coverage_section_form(request: Request, saved: bool = Query(False)):
    coverage = load_coverage()
    return templates.TemplateResponse(
        request,
        "admin/coverage/section.html",
        {
            "page_title": "Geographic Coverage",
            "active_nav": "pages",
            "active_item": "coverage-section",
            "coverage": coverage,
            "saved": saved,
        },
    )


@admin_router.post("/coverage")
async def coverage_section_save(
    request: Request,
    eyebrow: str = Form(...),
    title_before: str = Form(...),
    title_highlight: str = Form(...),
    title_after: str = Form(""),
):
    coverage = load_coverage()
    updated = coverage.model_copy(
        update={
            "eyebrow": eyebrow.strip(),
            "title_before": title_before.strip(),
            "title_highlight": title_highlight.strip(),
            "title_after": title_after.strip(),
        }
    )
    save_coverage(updated)
    return RedirectResponse(url="/admin/coverage?saved=1", status_code=303)


@admin_router.get("/coverage/countries")
async def coverage_countries_form(request: Request, saved: bool = Query(False)):
    coverage = load_coverage()
    return templates.TemplateResponse(
        request,
        "admin/coverage/countries.html",
        {
            "page_title": "Countries",
            "active_nav": "pages",
            "active_item": "countries",
            "coverage": coverage,
            "saved": saved,
        },
    )


@admin_router.post("/coverage/countries")
async def coverage_countries_save(request: Request, countries: str = Form(...)):
    coverage = load_coverage()
    updated = coverage.model_copy(update={"countries": _parse_lines(countries)})
    save_coverage(updated)
    return RedirectResponse(url="/admin/coverage/countries?saved=1", status_code=303)


@admin_router.get("/coverage/regions")
async def coverage_regions_form(request: Request, saved: bool = Query(False)):
    coverage = load_coverage()
    return templates.TemplateResponse(
        request,
        "admin/coverage/regions.html",
        {
            "page_title": "Regions",
            "active_nav": "pages",
            "active_item": "regions",
            "coverage": coverage,
            "saved": saved,
        },
    )


@admin_router.post("/coverage/regions")
async def coverage_regions_save(request: Request, regions: str = Form(...)):
    coverage = load_coverage()
    updated = coverage.model_copy(update={"regions": _parse_lines(regions)})
    save_coverage(updated)
    return RedirectResponse(url="/admin/coverage/regions?saved=1", status_code=303)


@api_router.get("/coverage")
async def coverage_api() -> CoverageContent:
    return load_coverage()
