from pydantic import BaseModel, Field, field_validator, model_validator


LIVE_TABLE_MAX_SYMBOLS = 10


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


def default_live_table_symbols() -> list[LiveMarketSymbol]:
    return [
        LiveMarketSymbol(symbol="BTCUSDT", label="Bitcoin", decimals=2),
        LiveMarketSymbol(symbol="ETHUSDT", label="Ethereum", decimals=2),
        LiveMarketSymbol(symbol="BNBUSDT", label="BNB", decimals=2),
        LiveMarketSymbol(symbol="SOLUSDT", label="Solana", decimals=2),
        LiveMarketSymbol(symbol="XRPUSDT", label="XRP", decimals=4),
        LiveMarketSymbol(symbol="ADAUSDT", label="Cardano", decimals=4),
        LiveMarketSymbol(symbol="DOGEUSDT", label="Dogecoin", decimals=5),
        LiveMarketSymbol(symbol="AVAXUSDT", label="Avalanche", decimals=2),
        LiveMarketSymbol(symbol="LINKUSDT", label="Chainlink", decimals=2),
        LiveMarketSymbol(symbol="TRXUSDT", label="TRON", decimals=4),
    ]


class LiveMarketsTable(BaseModel):
    enabled: bool = True
    title: str = "Live Crypto Markets"
    symbols: list[LiveMarketSymbol] = Field(default_factory=default_live_table_symbols)

    @field_validator("symbols")
    @classmethod
    def cap_symbol_count(cls, symbols: list[LiveMarketSymbol]) -> list[LiveMarketSymbol]:
        capped = symbols[:LIVE_TABLE_MAX_SYMBOLS]
        return capped if capped else default_live_table_symbols()


class MarketsContent(BaseModel):
    eyebrow: str
    title_before: str
    title_highlight: str
    intro: str
    widgets: dict[str, MarketWidget]
    data_providers: MarketDataProviders
    live_table: LiveMarketsTable = Field(default_factory=LiveMarketsTable)

    @model_validator(mode="after")
    def ensure_live_table_symbols(self) -> "MarketsContent":
        if self.live_table.enabled and not self.live_table.symbols:
            self.live_table.symbols = default_live_table_symbols()
        return self

    @classmethod
    def default_widgets(cls) -> dict[str, MarketWidget]:
        return {
            "chart": MarketWidget(title="Live Chart", provider="alpaca"),
            "overview": MarketWidget(title="Market Overview", provider="alpaca"),
            "screener": MarketWidget(title="Cross-Asset Screener", provider="alpaca"),
        }


WIDGET_KEYS = ("chart", "overview", "screener")
DATA_PROVIDER_OPTIONS = ("alpaca", "tradingview")
