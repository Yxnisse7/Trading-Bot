"""Binance API publique (sans clé) : hôte principal puis miroirs.

- api.binance.com : refuse les adresses américaines (HTTP 451), dont GitHub Actions
- data-api.binance.vision : miroir « données de marché » de Binance
- api.binance.us : Binance US (même format, volumes plus faibles mais réels)
"""
from __future__ import annotations

import logging

from ..models import Candle
from .http import ProviderError, get_json

HOSTS = [
    "https://api.binance.com",
    "https://data-api.binance.vision",
    "https://api.binance.us",
]

log = logging.getLogger(__name__)


def parse_klines(rows: list[list]) -> list[Candle]:
    out = []
    for r in rows:
        out.append(Candle(ts=int(r[0]) // 1000, open=float(r[1]), high=float(r[2]),
                          low=float(r[3]), close=float(r[4]), volume=float(r[5])))
    return out


def _first_host(path: str, params: dict, *, cache_seconds: int = 0):
    errors = []
    for host in HOSTS:
        try:
            return get_json(f"{host}{path}", params=params, retries=1, cache_seconds=cache_seconds)
        except ProviderError as exc:
            errors.append(f"{host.split('//')[1]}: {exc}")
            continue
    raise ProviderError("binance indisponible (" + " | ".join(errors) + ")")


def fetch_candles(symbol: str = "BTCUSDT", interval: str = "5m", limit: int = 500) -> list[Candle]:
    rows = _first_host("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": min(limit, 1000)},
                       cache_seconds=30)
    if not isinstance(rows, list) or not rows:
        raise ProviderError("réponse Binance vide")
    return parse_klines(rows)


def fetch_price(symbol: str = "BTCUSDT") -> float:
    data = _first_host("/api/v3/ticker/price", {"symbol": symbol})
    return float(data["price"])
