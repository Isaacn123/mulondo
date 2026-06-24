from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.calculator import CalculatorContent
from app.services.calculator_service import load_calculator, save_calculator

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["calculator"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


def _parse_scale_labels(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _optional_float(value: str) -> float | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    return float(cleaned)


@admin_router.get("/calculator")
async def calculator_section_form(request: Request, saved: bool = Query(False)):
    calculator = load_calculator()
    return templates.TemplateResponse(
        request,
        "admin/calculator/section.html",
        {
            "page_title": "Investment Calculator",
            "active_nav": "pages",
            "active_item": "calculator-section",
            "calculator": calculator,
            "saved": saved,
        },
    )


@admin_router.post("/calculator")
async def calculator_section_save(
    request: Request,
    eyebrow: str = Form(...),
    title_before: str = Form(...),
    title_highlight: str = Form(...),
    intro: str = Form(...),
):
    calculator = load_calculator()
    updated = calculator.model_copy(
        update={
            "eyebrow": eyebrow.strip(),
            "title_before": title_before.strip(),
            "title_highlight": title_highlight.strip(),
            "intro": intro.strip(),
        }
    )
    save_calculator(updated)
    return RedirectResponse(url="/admin/calculator?saved=1", status_code=303)


@admin_router.get("/calculator/assumptions")
async def calculator_assumptions_form(request: Request, saved: bool = Query(False)):
    calculator = load_calculator()
    return templates.TemplateResponse(
        request,
        "admin/calculator/assumptions.html",
        {
            "page_title": "Calculator Assumptions",
            "active_nav": "pages",
            "active_item": "assumptions",
            "calculator": calculator,
            "saved": saved,
        },
    )


@admin_router.post("/calculator/assumptions")
async def calculator_assumptions_save(
    request: Request,
    initial_label: str = Form(...),
    initial_input_min: str = Form(""),
    initial_input_step: str = Form(""),
    initial_range_min: float = Form(...),
    initial_range_max: float = Form(...),
    initial_range_step: float = Form(...),
    initial_enabled: str | None = Form(None),
    contrib_label: str = Form(...),
    contrib_range_min: float = Form(...),
    contrib_range_max: float = Form(...),
    contrib_range_step: float = Form(...),
    contrib_enabled: str | None = Form(None),
    horizon_label: str = Form(...),
    horizon_range_min: float = Form(...),
    horizon_range_max: float = Form(...),
    horizon_range_step: float = Form(...),
    horizon_scale: str = Form(""),
    horizon_enabled: str | None = Form(None),
    rate_label: str = Form(...),
    rate_range_min: float = Form(...),
    rate_range_max: float = Form(...),
    rate_range_step: float = Form(...),
    rate_scale: str = Form(""),
    rate_enabled: str | None = Form(None),
):
    calculator = load_calculator()
    updated = calculator.model_copy(
        update={
            "initial_capital": calculator.initial_capital.model_copy(
                update={
                    "label": initial_label.strip(),
                    "enabled": initial_enabled == "1",
                    "input_min": _optional_float(initial_input_min),
                    "input_step": _optional_float(initial_input_step),
                    "range_min": initial_range_min,
                    "range_max": initial_range_max,
                    "range_step": initial_range_step,
                }
            ),
            "monthly_contribution": calculator.monthly_contribution.model_copy(
                update={
                    "label": contrib_label.strip(),
                    "enabled": contrib_enabled == "1",
                    "range_min": contrib_range_min,
                    "range_max": contrib_range_max,
                    "range_step": contrib_range_step,
                }
            ),
            "investment_horizon": calculator.investment_horizon.model_copy(
                update={
                    "label": horizon_label.strip(),
                    "enabled": horizon_enabled == "1",
                    "range_min": horizon_range_min,
                    "range_max": horizon_range_max,
                    "range_step": horizon_range_step,
                    "scale_labels": _parse_scale_labels(horizon_scale),
                }
            ),
            "annual_rate": calculator.annual_rate.model_copy(
                update={
                    "label": rate_label.strip(),
                    "enabled": rate_enabled == "1",
                    "range_min": rate_range_min,
                    "range_max": rate_range_max,
                    "range_step": rate_range_step,
                    "scale_labels": _parse_scale_labels(rate_scale),
                }
            ),
        }
    )
    save_calculator(updated)
    return RedirectResponse(url="/admin/calculator/assumptions?saved=1", status_code=303)


@admin_router.get("/calculator/default-rates")
async def calculator_default_rates_form(request: Request, saved: bool = Query(False)):
    calculator = load_calculator()
    return templates.TemplateResponse(
        request,
        "admin/calculator/default_rates.html",
        {
            "page_title": "Default Rates",
            "active_nav": "pages",
            "active_item": "default-rates",
            "calculator": calculator,
            "saved": saved,
        },
    )


@admin_router.post("/calculator/default-rates")
async def calculator_default_rates_save(
    request: Request,
    initial_default: float = Form(...),
    contrib_default: float = Form(...),
    horizon_default: float = Form(...),
    rate_default: float = Form(...),
):
    calculator = load_calculator()
    updated = calculator.model_copy(
        update={
            "initial_capital": calculator.initial_capital.model_copy(update={"default": initial_default}),
            "monthly_contribution": calculator.monthly_contribution.model_copy(update={"default": contrib_default}),
            "investment_horizon": calculator.investment_horizon.model_copy(update={"default": horizon_default}),
            "annual_rate": calculator.annual_rate.model_copy(update={"default": rate_default}),
        }
    )
    save_calculator(updated)
    return RedirectResponse(url="/admin/calculator/default-rates?saved=1", status_code=303)


@admin_router.get("/calculator/disclaimers")
async def calculator_disclaimers_form(request: Request, saved: bool = Query(False)):
    calculator = load_calculator()
    return templates.TemplateResponse(
        request,
        "admin/calculator/disclaimers.html",
        {
            "page_title": "Calculator Disclaimers",
            "active_nav": "pages",
            "active_item": "disclaimers",
            "calculator": calculator,
            "saved": saved,
        },
    )


@admin_router.post("/calculator/disclaimers")
async def calculator_disclaimers_save(
    request: Request,
    disclaimer: str = Form(...),
    cta_text: str = Form(...),
    cta_link: str = Form(...),
    show_disclaimer: str | None = Form(None),
    show_summary: str | None = Form(None),
    show_chart: str | None = Form(None),
    show_table: str | None = Form(None),
    show_cta: str | None = Form(None),
):
    calculator = load_calculator()
    updated = calculator.model_copy(
        update={
            "disclaimer": disclaimer.strip(),
            "cta_text": cta_text.strip(),
            "cta_link": cta_link.strip(),
            "show_disclaimer": show_disclaimer == "1",
            "show_summary": show_summary == "1",
            "show_chart": show_chart == "1",
            "show_table": show_table == "1",
            "show_cta": show_cta == "1",
        }
    )
    save_calculator(updated)
    return RedirectResponse(url="/admin/calculator/disclaimers?saved=1", status_code=303)


@api_router.get("/calculator")
async def calculator_api() -> CalculatorContent:
    return load_calculator()
