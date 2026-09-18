"""Kraken (API publique, sans clé) : bougies OHLC avec volumes (720 dernières bougies au maximum)."""
from __future__ import annotations

from ..models import Candle
from .http import ProviderError, get_json

BASE = "https://api.kraken.com/0/public"


def fetch_candles(pair: str = "XBTUSD", interval: int = 5) -> list[Candle]:
    data = get_json(f"{BASE}/OHLC", params={"pair": pair, "interval": interval}, retries=2, cache_seconds=30)
    if data.get("error"):
        raise ProviderError(f"kraken: {data['error']}")
    result = data.get("result") or {}
    rows = next((v for k, v in result.items() if k != "last"), None)
    if not rows:
        raise ProviderError(f"aucune bougie Kraken pour {pair}")
    out = []
    for r in rows:
        # [time, open, high, low, close, vwap, volume, count]
        out.append(Candle(ts=int(r[0]), open=float(r[1]), high=float(r[2]), low=float(r[3]),
                          close=float(r[4]), volume=float(r[6])))
    return out


def fetch_price(pair: str = "XBTUSD") -> float:
    data = get_json(f"{BASE}/Ticker", params={"pair": pair}, retries=2)
    if data.get("error"):
        raise ProviderError(f"kraken: {data['error']}")
    result = data.get("result") or {}
    first = next(iter(result.values()), None)
    if not first:
        raise ProviderError("réponse Kraken vide")
    return float(first["c"][0])
