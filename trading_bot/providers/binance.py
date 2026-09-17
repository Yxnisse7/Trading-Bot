"""Binance API publique (sans clé) pour BTC/USDT."""
from __future__ import annotations

from ..models import Candle
from .http import ProviderError, get_json

BASE = "https://api.binance.com/api/v3"


def parse_klines(rows: list[list]) -> list[Candle]:
    out = []
    for r in rows:
        out.append(Candle(ts=int(r[0]) // 1000, open=float(r[1]), high=float(r[2]),
                          low=float(r[3]), close=float(r[4]), volume=float(r[5])))
    return out


def fetch_candles(symbol: str = "BTCUSDT", interval: str = "5m", limit: int = 500) -> list[Candle]:
    rows = get_json(f"{BASE}/klines", params={"symbol": symbol, "interval": interval, "limit": limit},
                    cache_seconds=30)
    if not isinstance(rows, list) or not rows:
        raise ProviderError("réponse Binance vide")
    return parse_klines(rows)


def fetch_price(symbol: str = "BTCUSDT") -> float:
    data = get_json(f"{BASE}/ticker/price", params={"symbol": symbol})
    return float(data["price"])
