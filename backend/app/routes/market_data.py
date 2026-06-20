from fastapi import APIRouter, HTTPException, Query

from app.schemas.markets import MarketsContent
from app.services.market_data.alpaca import alpaca_client
from app.services.markets_service import load_markets

router = APIRouter(prefix="/api/market-data", tags=["market-data"])


@router.get("/config")
async def market_data_config() -> dict:
    markets = load_markets()
    return {
        "primary": markets.data_providers.primary,
        "widgets": markets.widgets,
        "providers": {
            "alpaca": {
                "enabled": markets.data_providers.alpaca.enabled,
                "chart_symbol": markets.data_providers.alpaca.chart_symbol,
                "chart_timeframe": markets.data_providers.alpaca.chart_timeframe,
                "overview_symbols": markets.data_providers.alpaca.overview_symbols,
                "screener_symbols": markets.data_providers.alpaca.screener_symbols,
                "feed": markets.data_providers.alpaca.feed,
                "configured": alpaca_client.is_configured,
            },
            "tradingview": {
                "enabled": markets.data_providers.tradingview.enabled,
                "chart_symbol": markets.data_providers.tradingview.chart_symbol,
                "chart_interval": markets.data_providers.tradingview.chart_interval,
                "chart_timezone": markets.data_providers.tradingview.chart_timezone,
                "screener_market": markets.data_providers.tradingview.screener_market,
                "screener_default_screen": markets.data_providers.tradingview.screener_default_screen,
                "theme": markets.data_providers.tradingview.theme,
                "locale": markets.data_providers.tradingview.locale,
            },
        },
    }


@router.get("/alpaca/bars")
async def alpaca_bars(
    symbol: str = Query(..., description="Stock symbol e.g. AAPL or crypto BTC/USD"),
    timeframe: str = Query("1Day"),
    limit: int = Query(100, ge=1, le=1000),
    feed: str = Query("iex"),
    asset_class: str = Query("stock", pattern="^(stock|crypto)$"),
):
    if asset_class == "crypto":
        return await alpaca_client.get_crypto_bars(symbol=symbol, timeframe=timeframe, limit=limit)
    return await alpaca_client.get_stock_bars(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        feed=feed,
    )


@router.get("/alpaca/snapshots")
async def alpaca_snapshots(symbols: str = Query(..., description="Comma-separated symbols")):
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="At least one symbol is required.")
    return await alpaca_client.get_stock_snapshots(symbol_list)


@router.get("/markets")
async def markets_content_with_providers() -> MarketsContent:
    return load_markets()
