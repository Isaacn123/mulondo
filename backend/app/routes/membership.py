from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.membership import MembershipContent, MembershipModule, MembershipTier
from app.services.membership_service import load_membership, save_membership

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["membership"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


def _parse_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _parse_modules(value: str) -> list[MembershipModule]:
    modules: list[MembershipModule] = []
    for line in _parse_lines(value):
        if "|" in line:
            title, description = line.split("|", 1)
        else:
            title, description = line, ""
        modules.append(MembershipModule(title=title.strip(), description=description.strip()))
    return modules


def _modules_to_text(modules: list[MembershipModule]) -> str:
    return "\n".join(f"{m.title}|{m.description}" for m in modules)


@admin_router.get("/membership")
async def membership_section_form(request: Request, saved: bool = Query(False)):
    membership = load_membership()
    return templates.TemplateResponse(
        request,
        "admin/membership/section.html",
        {
            "page_title": "AI Membership Program",
            "active_nav": "pages",
            "active_item": "membership-section",
            "membership": membership,
            "saved": saved,
        },
    )


@admin_router.post("/membership")
async def membership_section_save(
    request: Request,
    eyebrow: str = Form(...),
    title_before: str = Form(...),
    title_highlight: str = Form(...),
    intro: str = Form(...),
    page_description: str = Form(""),
    overview_title: str = Form(...),
    overview_text: str = Form(...),
    certification_title: str = Form(...),
    certification_text: str = Form(...),
    enroll_title: str = Form(...),
    enroll_subtitle: str = Form(...),
    enroll_button_text: str = Form(...),
    enroll_link: str = Form(...),
):
    membership = load_membership()
    updated = membership.model_copy(
        update={
            "eyebrow": eyebrow.strip(),
            "title_before": title_before.strip(),
            "title_highlight": title_highlight.strip(),
            "intro": intro.strip(),
            "page_description": page_description.strip(),
            "overview_title": overview_title.strip(),
            "overview_text": overview_text.strip(),
            "certification_title": certification_title.strip(),
            "certification_text": certification_text.strip(),
            "enroll_title": enroll_title.strip(),
            "enroll_subtitle": enroll_subtitle.strip(),
            "enroll_button_text": enroll_button_text.strip(),
            "enroll_link": enroll_link.strip(),
        }
    )
    save_membership(updated)
    return RedirectResponse(url="/admin/membership?saved=1", status_code=303)


@admin_router.get("/membership/modules")
async def membership_modules_form(request: Request, saved: bool = Query(False)):
    membership = load_membership()
    return templates.TemplateResponse(
        request,
        "admin/membership/modules.html",
        {
            "page_title": "Curriculum Modules",
            "active_nav": "pages",
            "active_item": "membership-modules",
            "membership": membership,
            "modules_text": _modules_to_text(membership.modules),
            "saved": saved,
        },
    )


@admin_router.post("/membership/modules")
async def membership_modules_save(request: Request, modules: str = Form(...)):
    membership = load_membership()
    updated = membership.model_copy(update={"modules": _parse_modules(modules)})
    save_membership(updated)
    return RedirectResponse(url="/admin/membership/modules?saved=1", status_code=303)


@admin_router.get("/membership/tiers")
async def membership_tiers_form(request: Request, saved: bool = Query(False)):
    membership = load_membership()
    tiers = list(membership.tiers)
    while len(tiers) < 3:
        tiers.append(
            MembershipTier(name="", price="", features=[], cta_text="Enroll Now", cta_link="#enroll")
        )
    return templates.TemplateResponse(
        request,
        "admin/membership/tiers.html",
        {
            "page_title": "Membership Tiers",
            "active_nav": "pages",
            "active_item": "membership-tiers",
            "membership": membership,
            "tiers": tiers[:3],
            "saved": saved,
        },
    )


@admin_router.post("/membership/tiers")
async def membership_tiers_save(
    request: Request,
    tier_0_name: str = Form(""),
    tier_0_price: str = Form(""),
    tier_0_period: str = Form("/ year"),
    tier_0_features: str = Form(""),
    tier_0_highlighted: str = Form(""),
    tier_0_cta_text: str = Form("Enroll Now"),
    tier_0_cta_link: str = Form("#enroll"),
    tier_1_name: str = Form(""),
    tier_1_price: str = Form(""),
    tier_1_period: str = Form("/ year"),
    tier_1_features: str = Form(""),
    tier_1_highlighted: str = Form(""),
    tier_1_cta_text: str = Form("Enroll Now"),
    tier_1_cta_link: str = Form("#enroll"),
    tier_2_name: str = Form(""),
    tier_2_price: str = Form(""),
    tier_2_period: str = Form("/ year"),
    tier_2_features: str = Form(""),
    tier_2_highlighted: str = Form(""),
    tier_2_cta_text: str = Form("Enroll Now"),
    tier_2_cta_link: str = Form("#enroll"),
):
    tiers = []
    for i, highlighted in enumerate(
        [tier_0_highlighted, tier_1_highlighted, tier_2_highlighted]
    ):
        data = [
            (tier_0_name, tier_0_price, tier_0_period, tier_0_features, tier_0_cta_text, tier_0_cta_link),
            (tier_1_name, tier_1_price, tier_1_period, tier_1_features, tier_1_cta_text, tier_1_cta_link),
            (tier_2_name, tier_2_price, tier_2_period, tier_2_features, tier_2_cta_text, tier_2_cta_link),
        ][i]
        name, price, period, features, cta_text, cta_link = data
        if not name.strip():
            continue
        tiers.append(
            MembershipTier(
                name=name.strip(),
                price=price.strip(),
                period=period.strip() or "/ year",
                features=_parse_lines(features),
                highlighted=highlighted == "on",
                cta_text=cta_text.strip() or "Enroll Now",
                cta_link=cta_link.strip() or "#enroll",
            )
        )
    membership = load_membership()
    updated = membership.model_copy(update={"tiers": tiers or membership.tiers})
    save_membership(updated)
    return RedirectResponse(url="/admin/membership/tiers?saved=1", status_code=303)


@admin_router.get("/membership/benefits")
async def membership_benefits_form(request: Request, saved: bool = Query(False)):
    membership = load_membership()
    return templates.TemplateResponse(
        request,
        "admin/membership/benefits.html",
        {
            "page_title": "Benefits & Outcomes",
            "active_nav": "pages",
            "active_item": "membership-benefits",
            "membership": membership,
            "saved": saved,
        },
    )


@admin_router.post("/membership/benefits")
async def membership_benefits_save(
    request: Request,
    benefits: str = Form(""),
    certification_outcomes: str = Form(""),
):
    membership = load_membership()
    updated = membership.model_copy(
        update={
            "benefits": _parse_lines(benefits),
            "certification_outcomes": _parse_lines(certification_outcomes),
        }
    )
    save_membership(updated)
    return RedirectResponse(url="/admin/membership/benefits?saved=1", status_code=303)


@api_router.get("/membership")
async def membership_api() -> MembershipContent:
    return load_membership()
