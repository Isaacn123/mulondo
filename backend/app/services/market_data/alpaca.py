from fastapi import HTTPException
import httpx

from app.core.config import get_settings


class AlpacaClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.alpaca_data_base_url.rstrip("/")
        self.api_key = settings.alpaca_api_key
        self.api_secret = settings.alpaca_api_secret

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def _headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
        }

    def _require_configured(self) -> None:
        if not self.is_configured:
            raise HTTPException(
                status_code=503,
                detail="Alpaca API keys are not configured. Add ALPACA_API_KEY and ALPACA_API_SECRET to .env",
            )

    async def get_stock_bars(
        self,
        symbol: str,
        timeframe: str = "1Day",
        limit: int = 100,
        feed: str = "iex",
    ) -> dict:
        self._require_configured()
        params = {
            "symbols": symbol,
            "timeframe": timeframe,
            "limit": limit,
            "feed": feed,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{self.base_url}/v2/stocks/bars",
                headers=self._headers(),
                params=params,
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

    async def get_stock_snapshots(self, symbols: list[str]) -> dict:
        self._require_configured()
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{self.base_url}/v2/stocks/snapshots",
                headers=self._headers(),
                params={"symbols": ",".join(symbols)},
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

    async def get_crypto_bars(
        self,
        symbol: str,
        timeframe: str = "1Day",
        limit: int = 100,
    ) -> dict:
        self._require_configured()
        params = {
            "symbols": symbol,
            "timeframe": timeframe,
            "limit": limit,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{self.base_url}/v1beta3/crypto/us/bars",
                headers=self._headers(),
                params=params,
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


alpaca_client = AlpacaClient()
