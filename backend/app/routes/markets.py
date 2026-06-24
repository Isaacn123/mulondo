from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas.markets import (
    AlpacaProviderSettings,
    DATA_PROVIDER_OPTIONS,
    LiveMarketSymbol,
    LiveMarketsTable,
    MarketDataProviders,
    MarketWidget,
    MarketsContent,
    TradingViewProviderSettings,
    WIDGET_KEYS,
)
from app.services.markets_service import load_markets, save_markets

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

admin_router = APIRouter(prefix="/admin", tags=["markets"])
api_router = APIRouter(prefix="/api/content", tags=["content"])


def _parse_csv_symbols(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _live_table_symbols_from_text(raw: str) -> list[LiveMarketSymbol]:
    symbols: list[LiveMarketSymbol] = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        symbol = parts[0].upper()
        if not symbol:
            continue
        label = parts[1] if len(parts) > 1 and parts[1] else symbol
        decimals = 2
        if len(parts) > 2 and parts[2].isdigit():
            decimals = int(parts[2])
        link = parts[3] if len(parts) > 3 else ""
        symbols.append(LiveMarketSymbol(symbol=symbol, label=label, decimals=decimals, link=link))
    return symbols


def _live_table_symbols_to_text(symbols: list[LiveMarketSymbol]) -> str:
    return "\n".join(
        f"{s.symbol}|{s.label}|{s.decimals}|{s.link}" if s.link else f"{s.symbol}|{s.label}|{s.decimals}"
        for s in symbols
    )


@admin_router.get("/markets")
async def markets_section_form(request: Request, saved: bool = Query(False)):
    markets = load_markets()
    return templates.TemplateResponse(
        request,
        "admin/markets/section.html",
        {
            "page_title": "Markets Section",
            "active_nav": "pages",
            "active_item": "markets-section",
            "markets": markets,
            "saved": saved,
        },
    )


@admin_router.post("/markets")
async def markets_section_save(
    request: Request,
    eyebrow: str = Form(...),
    title_before: str = Form(...),
    title_highlight: str = Form(...),
):
    markets = load_markets()
    updated = markets.model_copy(
        update={
            "eyebrow": eyebrow.strip(),
            "title_before": title_before.strip(),
            "title_highlight": title_highlight.strip(),
        }
    )
    save_markets(updated)
    return RedirectResponse(url="/admin/markets?saved=1", status_code=303)


@admin_router.get("/markets/widgets")
async def markets_widgets_form(request: Request, saved: bool = Query(False)):
    markets = load_markets()
    return templates.TemplateResponse(
        request,
        "admin/markets/widgets.html",
        {
            "page_title": "Market Widgets",
            "active_nav": "pages",
            "active_item": "market-widgets",
            "markets": markets,
            "widget_keys": WIDGET_KEYS,
            "provider_options": DATA_PROVIDER_OPTIONS,
            "saved": saved,
        },
    )


@admin_router.post("/markets/widgets")
async def markets_widgets_save(
    request: Request,
    chart_title: str = Form(...),
    overview_title: str = Form(...),
    screener_title: str = Form(...),
    chart_enabled: str | None = Form(None),
    overview_enabled: str | None = Form(None),
    screener_enabled: str | None = Form(None),
    chart_provider: str = Form(...),
    overview_provider: str = Form(...),
    screener_provider: str = Form(...),
):
    markets = load_markets()
    widgets = {
        "chart": MarketWidget(
            title=chart_title.strip(),
            enabled=chart_enabled == "1",
            provider=chart_provider.strip(),
        ),
        "overview": MarketWidget(
            title=overview_title.strip(),
            enabled=overview_enabled == "1",
            provider=overview_provider.strip(),
        ),
        "screener": MarketWidget(
            title=screener_title.strip(),
            enabled=screener_enabled == "1",
            provider=screener_provider.strip(),
        ),
    }
    save_markets(markets.model_copy(update={"widgets": widgets}))
    return RedirectResponse(url="/admin/markets/widgets?saved=1", status_code=303)


@admin_router.get("/markets/data-providers")
async def markets_data_providers_form(request: Request, saved: bool = Query(False)):
    markets = load_markets()
    return templates.TemplateResponse(
        request,
        "admin/markets/data_providers.html",
        {
            "page_title": "Data Providers",
            "active_nav": "pages",
            "active_item": "data-providers",
            "providers": markets.data_providers,
            "provider_options": DATA_PROVIDER_OPTIONS,
            "saved": saved,
        },
    )


@admin_router.post("/markets/data-providers")
async def markets_data_providers_save(
    request: Request,
    primary: str = Form(...),
    alpaca_enabled: str | None = Form(None),
    alpaca_chart_symbol: str = Form(...),
    alpaca_chart_timeframe: str = Form(...),
    alpaca_feed: str = Form(...),
    alpaca_overview_symbols: str = Form(...),
    alpaca_screener_symbols: str = Form(...),
    tv_enabled: str | None = Form(None),
    tv_chart_symbol: str = Form(...),
    tv_chart_interval: str = Form(...),
    tv_chart_timezone: str = Form(...),
    tv_screener_market: str = Form(...),
    tv_screener_default_screen: str = Form(...),
):
    markets = load_markets()
    data_providers = MarketDataProviders(
        primary=primary.strip(),
        alpaca=AlpacaProviderSettings(
            enabled=alpaca_enabled == "1",
            chart_symbol=alpaca_chart_symbol.strip(),
            chart_timeframe=alpaca_chart_timeframe.strip(),
            overview_symbols=_parse_csv_symbols(alpaca_overview_symbols),
            screener_symbols=_parse_csv_symbols(alpaca_screener_symbols),
            feed=alpaca_feed.strip(),
        ),
        tradingview=TradingViewProviderSettings(
            enabled=tv_enabled == "1",
            chart_symbol=tv_chart_symbol.strip(),
            chart_interval=tv_chart_interval.strip(),
            chart_timezone=tv_chart_timezone.strip(),
            screener_market=tv_screener_market.strip(),
            screener_default_screen=tv_screener_default_screen.strip(),
        ),
    )
    save_markets(markets.model_copy(update={"data_providers": data_providers}))
    return RedirectResponse(url="/admin/markets/data-providers?saved=1", status_code=303)


@admin_router.get("/markets/tradingview")
async def markets_tradingview_redirect():
    return RedirectResponse(url="/admin/markets/data-providers", status_code=307)


@admin_router.get("/markets/asset-coverage")
async def markets_asset_coverage_form(request: Request, saved: bool = Query(False)):
    markets = load_markets()
    return templates.TemplateResponse(
        request,
        "admin/markets/asset_coverage.html",
        {
            "page_title": "Asset Coverage",
            "active_nav": "pages",
            "active_item": "asset-coverage",
            "intro": markets.intro,
            "saved": saved,
        },
    )


@admin_router.post("/markets/asset-coverage")
async def markets_asset_coverage_save(
    request: Request,
    intro: str = Form(...),
):
    markets = load_markets()
    save_markets(markets.model_copy(update={"intro": intro.strip()}))
    return RedirectResponse(url="/admin/markets/asset-coverage?saved=1", status_code=303)


@admin_router.get("/markets/live-table")
async def markets_live_table_form(request: Request, saved: bool = Query(False)):
    markets = load_markets()
    return templates.TemplateResponse(
        request,
        "admin/markets/live_table.html",
        {
            "page_title": "Live Markets Table",
            "active_nav": "pages",
            "active_item": "live-markets-table",
            "live_table": markets.live_table,
            "symbols_to_text": _live_table_symbols_to_text,
            "saved": saved,
        },
    )


@admin_router.post("/markets/live-table")
async def markets_live_table_save(
    request: Request,
    enabled: str | None = Form(None),
    title: str = Form(...),
    symbols: str = Form(""),
):
    markets = load_markets()
    live_table = LiveMarketsTable(
        enabled=enabled == "1",
        title=title.strip() or "Live Crypto Markets",
        symbols=_live_table_symbols_from_text(symbols),
    )
    save_markets(markets.model_copy(update={"live_table": live_table}))
    return RedirectResponse(url="/admin/markets/live-table?saved=1", status_code=303)


@api_router.get("/markets")
async def markets_api() -> MarketsContent:
    return load_markets()
