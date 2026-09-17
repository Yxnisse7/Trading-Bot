"""CoinGecko (API publique gratuite) : prix spot de secours pour BTC."""
from __future__ import annotations

from .http import get_json

URL = "https://api.coingecko.com/api/v3/simple/price"


def fetch_price(coin: str = "bitcoin", vs: str = "usd") -> float:
    data = get_json(URL, params={"ids": coin, "vs_currencies": vs})
    return float(data[coin][vs])
