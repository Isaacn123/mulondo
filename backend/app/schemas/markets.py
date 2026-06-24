from pydantic import BaseModel, Field


class MarketWidget(BaseModel):
    title: str
    enabled: bool = True
    provider: str = "alpaca"


class AlpacaProviderSettings(BaseModel):
    enabled: bool = True
    chart_symbol: str = "AAPL"
    chart_timeframe: str = "1Day"
    chart_limit: int = Field(default=100, ge=1, le=1000)
    overview_symbols: list[str] = Field(default_factory=lambda: ["AAPL", "MSFT", "GOOGL", "AMZN"])
    screener_symbols: list[str] = Field(default_factory=lambda: ["AAPL", "TSLA", "NVDA", "META"])
    feed: str = "iex"


class TradingViewProviderSettings(BaseModel):
    enabled: bool = False
    chart_symbol: str = "BINANCE:BTCUSDT"
    chart_interval: str = "D"
    chart_timezone: str = "Africa/Nairobi"
    screener_market: str = "crypto"
    screener_default_screen: str = "general"
    theme: str = "dark"
    locale: str = "en"


class MarketDataProviders(BaseModel):
    primary: str = "alpaca"
    alpaca: AlpacaProviderSettings = Field(default_factory=AlpacaProviderSettings)
    tradingview: TradingViewProviderSettings = Field(default_factory=TradingViewProviderSettings)


class LiveMarketSymbol(BaseModel):
    symbol: str
    label: str
    decimals: int = Field(default=2, ge=0, le=8)
    link: str = ""


class LiveMarketsTable(BaseModel):
    enabled: bool = True
    title: str = "Live Crypto Markets"
    symbols: list[LiveMarketSymbol] = Field(default_factory=list)


class MarketsContent(BaseModel):
    eyebrow: str
    title_before: str
    title_highlight: str
    intro: str
    widgets: dict[str, MarketWidget]
    data_providers: MarketDataProviders
    live_table: LiveMarketsTable = Field(default_factory=LiveMarketsTable)

    @classmethod
    def default_widgets(cls) -> dict[str, MarketWidget]:
        return {
            "chart": MarketWidget(title="Live Chart", provider="alpaca"),
            "overview": MarketWidget(title="Market Overview", provider="alpaca"),
            "screener": MarketWidget(title="Cross-Asset Screener", provider="alpaca"),
        }


WIDGET_KEYS = ("chart", "overview", "screener")
DATA_PROVIDER_OPTIONS = ("alpaca", "tradingview")
