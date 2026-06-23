import json
from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.content_storage import load_raw_json
from app.schemas.hero import (
    Allocation,
    ButtonLink,
    FloatCard,
    HeroContent,
    HeroImage,
    HeroPanel,
    MetaStat,
)
from app.schemas.trust import CounterTrustStat, TextTrustStat, TrustContent
from app.schemas.about import AboutContent, AboutImage
from app.schemas.philosophy import PhilosophyContent, PhilosophyPillar
from app.schemas.content_defaults import default_ai_banner, default_partner
from app.services.about_service import load_about, save_about
from app.services.hero_service import load_hero, save_hero
from app.services.philosophy_service import load_philosophy, save_philosophy
from app.services.trust_service import load_trust, save_trust
from app.services import r2_service

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

AI_BANNER_FILE = DATA_DIR / "ai_banner.json"
PARTNER_FILE = DATA_DIR / "partner.json"


def _save_raw_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _load_ai_banner() -> dict:
    return load_raw_json(AI_BANNER_FILE, default=default_ai_banner()) or {}


def _load_partner() -> dict:
    return load_raw_json(PARTNER_FILE, default=default_partner()) or {}


admin_router = APIRouter(prefix="/admin", tags=["homepage"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


def hero_form_context(hero: HeroContent, saved: bool = False):
    return {
        "page_title": "Hero Section",
        "page_description": "Edit the homepage hero headline, copy, stats and panel.",
        "active_nav": "pages",
        "active_item": "hero",
        "hero": hero,
        "saved": saved,
        "r2_configured": r2_service.r2_configured(),
    }


@admin_router.get("/homepage/hero")
async def hero_edit_form(request: Request, saved: bool = Query(False)):
    hero = load_hero()
    return templates.TemplateResponse(
        request,
        "admin/homepage/hero.html",
        hero_form_context(hero, saved=saved),
    )


@admin_router.post("/homepage/hero")
async def hero_save(
    request: Request,
    eyebrow_text: str = Form(...),
    title_before: str = Form(...),
    title_highlight: str = Form(...),
    subtitle: str = Form(...),
    primary_btn_text: str = Form(...),
    primary_btn_link: str = Form(...),
    secondary_btn_text: str = Form(...),
    secondary_btn_link: str = Form(...),
    show_meta_stats: str | None = Form(None),
    meta_0_value: int = Form(...),
    meta_0_suffix: str = Form(""),
    meta_0_label: str = Form(...),
    meta_1_value: int = Form(...),
    meta_1_suffix: str = Form(""),
    meta_1_label: str = Form(...),
    meta_2_value: int = Form(...),
    meta_2_suffix: str = Form(""),
    meta_2_label: str = Form(...),
    show_globe: str | None = Form(None),
    globe_caption: str = Form("Global markets & Africa-native perspective"),
    panel_tag: str = Form(...),
    panel_live: str = Form(...),
    panel_label: str = Form(...),
    panel_value: str = Form(...),
    alloc_0_name: str = Form(...),
    alloc_0_percent: int = Form(...),
    alloc_1_name: str = Form(...),
    alloc_1_percent: int = Form(...),
    alloc_2_name: str = Form(...),
    alloc_2_percent: int = Form(...),
    alloc_3_name: str = Form(...),
    alloc_3_percent: int = Form(...),
    panel_foot_left: str = Form(...),
    panel_foot_right: str = Form(...),
    float_0_key: str = Form(...),
    float_0_value: str = Form(...),
    float_1_key: str = Form(...),
    float_1_value: str = Form(...),
    image_src: str = Form(""),
    image_alt: str = Form(""),
    image_object_position: str = Form("center top"),
):
    hero = HeroContent(
        eyebrow_text=eyebrow_text.strip(),
        title_before=title_before.strip(),
        title_highlight=title_highlight.strip(),
        subtitle=subtitle.strip(),
        primary_btn=ButtonLink(text=primary_btn_text.strip(), link=primary_btn_link.strip()),
        secondary_btn=ButtonLink(text=secondary_btn_text.strip(), link=secondary_btn_link.strip()),
        show_meta_stats=show_meta_stats == "1",
        meta_stats=[
            MetaStat(value=meta_0_value, suffix=meta_0_suffix.strip(), label=meta_0_label.strip()),
            MetaStat(value=meta_1_value, suffix=meta_1_suffix.strip(), label=meta_1_label.strip()),
            MetaStat(value=meta_2_value, suffix=meta_2_suffix.strip(), label=meta_2_label.strip()),
        ],
        show_globe=show_globe == "1",
        globe_caption=globe_caption.strip() or "Global markets & Africa-native perspective",
        panel=HeroPanel(
            tag=panel_tag.strip(),
            live=panel_live.strip(),
            label=panel_label.strip(),
            value=panel_value.strip(),
            allocations=[
                Allocation(name=alloc_0_name.strip(), percent=alloc_0_percent),
                Allocation(name=alloc_1_name.strip(), percent=alloc_1_percent),
                Allocation(name=alloc_2_name.strip(), percent=alloc_2_percent),
                Allocation(name=alloc_3_name.strip(), percent=alloc_3_percent),
            ],
            foot_left=panel_foot_left.strip(),
            foot_right=panel_foot_right.strip(),
        ),
        float_cards=[
            FloatCard(key=float_0_key.strip(), value=float_0_value.strip()),
            FloatCard(key=float_1_key.strip(), value=float_1_value.strip()),
        ],
        image=HeroImage(
            src=image_src.strip(),
            alt=image_alt.strip(),
            object_position=image_object_position.strip() or "center top",
        ),
    )
    save_hero(hero)
    return RedirectResponse(url="/admin/homepage/hero?saved=1", status_code=303)


@api_router.get("/hero")
async def hero_api():
    return load_hero()


def trust_form_context(trust: TrustContent, saved: bool = False):
    return {
        "page_title": "Trust Stats",
        "page_description": "Manage trust strip statistics shown below the hero.",
        "active_nav": "pages",
        "active_item": "trust",
        "trust": trust,
        "saved": saved,
    }


@admin_router.get("/homepage/trust")
async def trust_edit_form(request: Request, saved: bool = Query(False)):
    trust = load_trust()
    return templates.TemplateResponse(
        request,
        "admin/homepage/trust.html",
        trust_form_context(trust, saved=saved),
    )


@admin_router.post("/homepage/trust")
async def trust_save(
    request: Request,
    stat_0_type: str = Form(...),
    stat_0_value: int | None = Form(None),
    stat_0_suffix: str = Form(""),
    stat_0_label: str = Form(...),
    stat_0_title: str = Form(""),
    stat_1_type: str = Form(...),
    stat_1_value: int | None = Form(None),
    stat_1_suffix: str = Form(""),
    stat_1_label: str = Form(...),
    stat_1_title: str = Form(""),
    stat_2_type: str = Form(...),
    stat_2_value: int | None = Form(None),
    stat_2_suffix: str = Form(""),
    stat_2_label: str = Form(...),
    stat_2_title: str = Form(...),
    stat_3_type: str = Form(...),
    stat_3_value: int | None = Form(None),
    stat_3_suffix: str = Form(""),
    stat_3_label: str = Form(...),
    stat_3_title: str = Form(...),
    note_before: str = Form(...),
    countries: str = Form(...),
    note_after: str = Form(...),
):
    def build_stat(index: int) -> CounterTrustStat | TextTrustStat:
        types = [stat_0_type, stat_1_type, stat_2_type, stat_3_type]
        values = [stat_0_value, stat_1_value, stat_2_value, stat_3_value]
        suffixes = [stat_0_suffix, stat_1_suffix, stat_2_suffix, stat_3_suffix]
        labels = [stat_0_label, stat_1_label, stat_2_label, stat_3_label]
        titles = [stat_0_title, stat_1_title, stat_2_title, stat_3_title]

        stat_type = types[index].strip()
        if stat_type == "counter":
            if values[index] is None:
                raise ValueError(f"Stat {index + 1} requires a numeric value.")
            return CounterTrustStat(
                value=values[index],
                suffix=suffixes[index].strip(),
                label=labels[index].strip(),
            )
        return TextTrustStat(
            title=titles[index].strip(),
            label=labels[index].strip(),
        )

    trust = TrustContent(
        stats=[build_stat(i) for i in range(4)],
        note_before=note_before.strip(),
        countries=countries.strip(),
        note_after=note_after.strip(),
    )
    save_trust(trust)
    return RedirectResponse(url="/admin/homepage/trust?saved=1", status_code=303)


@api_router.get("/trust")
async def trust_api():
    return load_trust()


def about_form_context(about: AboutContent, saved: bool = False):
    return {
        "page_title": "About Daniel",
        "page_description": "Update the about section biography and highlights.",
        "active_nav": "pages",
        "active_item": "about",
        "about": about,
        "saved": saved,
        "r2_configured": r2_service.r2_configured(),
    }


@admin_router.get("/homepage/about")
async def about_edit_form(request: Request, saved: bool = Query(False)):
    about = load_about()
    return templates.TemplateResponse(
        request,
        "admin/homepage/about.html",
        about_form_context(about, saved=saved),
    )


@admin_router.post("/homepage/about")
async def about_save(
    request: Request,
    image_src: str = Form(...),
    image_alt: str = Form(...),
    image_width: int = Form(...),
    image_height: int = Form(...),
    badge_0: str = Form(...),
    badge_1: str = Form(...),
    eyebrow: str = Form(...),
    title_before: str = Form(...),
    title_highlight: str = Form(...),
    lead: str = Form(...),
    role_prefix: str = Form(...),
    role_title: str = Form(...),
    company_name: str = Form(...),
    company_url: str = Form(...),
    body_after: str = Form(...),
    highlights: str = Form(...),
    cta_text: str = Form(...),
    cta_link: str = Form(...),
):
    highlight_items = [line.strip() for line in highlights.splitlines() if line.strip()]
    about = AboutContent(
        image=AboutImage(
            src=image_src.strip(),
            alt=image_alt.strip(),
            width=image_width,
            height=image_height,
        ),
        badges=[badge_0.strip(), badge_1.strip()],
        eyebrow=eyebrow.strip(),
        title_before=title_before.strip(),
        title_highlight=title_highlight.strip(),
        lead=lead.strip(),
        role_prefix=role_prefix.strip(),
        role_title=role_title.strip(),
        company_name=company_name.strip(),
        company_url=company_url.strip(),
        body_after=body_after.strip(),
        highlights=highlight_items,
        cta_text=cta_text.strip(),
        cta_link=cta_link.strip(),
    )
    save_about(about)
    return RedirectResponse(url="/admin/homepage/about?saved=1", status_code=303)


@api_router.get("/about")
async def about_api():
    return load_about()


def philosophy_form_context(philosophy: PhilosophyContent, saved: bool = False):
    return {
        "page_title": "Investment Philosophy",
        "page_description": "Manage the investment philosophy section content.",
        "active_nav": "pages",
        "active_item": "philosophy",
        "philosophy": philosophy,
        "saved": saved,
    }


@admin_router.get("/homepage/philosophy")
async def philosophy_edit_form(request: Request, saved: bool = Query(False)):
    philosophy = load_philosophy()
    return templates.TemplateResponse(
        request,
        "admin/homepage/philosophy.html",
        philosophy_form_context(philosophy, saved=saved),
    )


@admin_router.post("/homepage/philosophy")
async def philosophy_save(
    request: Request,
    eyebrow: str = Form(...),
    title_before: str = Form(...),
    title_highlight: str = Form(...),
    intro: str = Form(...),
    pullquote: str = Form(...),
    pillar_0_number: str = Form(...),
    pillar_0_title: str = Form(...),
    pillar_0_description: str = Form(...),
    pillar_1_number: str = Form(...),
    pillar_1_title: str = Form(...),
    pillar_1_description: str = Form(...),
    pillar_2_number: str = Form(...),
    pillar_2_title: str = Form(...),
    pillar_2_description: str = Form(...),
    pillar_0_highlighted: str | None = Form(None),
    pillar_1_highlighted: str | None = Form(None),
    pillar_2_highlighted: str | None = Form(None),
):
    philosophy = PhilosophyContent(
        eyebrow=eyebrow.strip(),
        title_before=title_before.strip(),
        title_highlight=title_highlight.strip(),
        intro=intro.strip(),
        pullquote=pullquote.strip(),
        pillars=[
            PhilosophyPillar(
                number=pillar_0_number.strip(),
                title=pillar_0_title.strip(),
                description=pillar_0_description.strip(),
                highlighted=pillar_0_highlighted == "1",
            ),
            PhilosophyPillar(
                number=pillar_1_number.strip(),
                title=pillar_1_title.strip(),
                description=pillar_1_description.strip(),
                highlighted=pillar_1_highlighted == "1",
            ),
            PhilosophyPillar(
                number=pillar_2_number.strip(),
                title=pillar_2_title.strip(),
                description=pillar_2_description.strip(),
                highlighted=pillar_2_highlighted == "1",
            ),
        ],
    )
    save_philosophy(philosophy)
    return RedirectResponse(url="/admin/homepage/philosophy?saved=1", status_code=303)


@api_router.get("/philosophy")
async def philosophy_api():
    return load_philosophy()


@admin_router.get("/homepage/ai-banner")
async def ai_banner_edit_form(request: Request, saved: bool = Query(False)):
    banner = _load_ai_banner()
    return templates.TemplateResponse(
        request,
        "admin/homepage/ai_banner.html",
        {
            "page_title": "AI Banner",
            "active_nav": "pages",
            "active_item": "ai-banner",
            "banner": banner,
            "saved": saved,
            "r2_configured": r2_service.r2_configured(),
        },
    )


@admin_router.post("/homepage/ai-banner")
async def ai_banner_save(
    request: Request,
    eyebrow: str = Form(...),
    link: str = Form(...),
    link_label: str = Form(...),
    image_src: str = Form(...),
    image_alt: str = Form(...),
    image_width: int = Form(...),
    image_height: int = Form(...),
):
    data = {
        "eyebrow": eyebrow.strip(),
        "link": link.strip(),
        "link_label": link_label.strip(),
        "image": {
            "src": image_src.strip(),
            "alt": image_alt.strip(),
            "width": image_width,
            "height": image_height,
        },
    }
    _save_raw_json(AI_BANNER_FILE, data)
    return RedirectResponse(url="/admin/homepage/ai-banner?saved=1", status_code=303)


@admin_router.get("/partners/xa-markets")
async def partner_edit_form(request: Request, saved: bool = Query(False)):
    partner = _load_partner()
    return templates.TemplateResponse(
        request,
        "admin/partners/xa_markets.html",
        {
            "page_title": "XA Markets Partner",
            "active_nav": "pages",
            "active_item": "xa-markets",
            "partner": partner,
            "saved": saved,
            "r2_configured": r2_service.r2_configured(),
        },
    )


@admin_router.post("/partners/xa-markets")
async def partner_save(
    request: Request,
    eyebrow: str = Form(...),
    name: str = Form(...),
    url: str = Form(...),
    logo_src: str = Form(...),
    logo_alt: str = Form(...),
    text: str = Form(...),
    button_text: str = Form(...),
):
    data = {
        "eyebrow": eyebrow.strip(),
        "name": name.strip(),
        "url": url.strip(),
        "logo": {
            "src": logo_src.strip(),
            "alt": logo_alt.strip(),
        },
        "text": text.strip(),
        "button_text": button_text.strip(),
    }
    _save_raw_json(PARTNER_FILE, data)
    return RedirectResponse(url="/admin/partners/xa-markets?saved=1", status_code=303)


@api_router.get("/ai-banner")
async def ai_banner_api():
    return _load_ai_banner()


@api_router.get("/partner")
async def partner_api():
    return _load_partner()
