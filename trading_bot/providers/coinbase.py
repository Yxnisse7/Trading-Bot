"""Coinbase Exchange (API publique, sans clé, accessible depuis les États-Unis) : bougies avec vrais volumes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..models import Candle
from .http import ProviderError, get_json

BASE = "https://api.exchange.coinbase.com"
MAX_PER_REQUEST = 300


def parse_candles(rows: list[list]) -> list[Candle]:
    # format : [time, low, high, open, close, volume], du plus récent au plus ancien
    out = []
    for r in rows:
        out.append(Candle(ts=int(r[0]), open=float(r[3]), high=float(r[2]), low=float(r[1]),
                          close=float(r[4]), volume=float(r[5])))
    out.sort(key=lambda c: c.ts)
    return out


def fetch_candles(product: str = "BTC-USD", granularity: int = 300, limit: int = 1440) -> list[Candle]:
    """Jusqu'à `limit` bougies de `granularity` secondes, par tranches de 300 (limite de l'API)."""
    end = datetime.now(timezone.utc).replace(microsecond=0)
    out: dict[int, Candle] = {}
    remaining = limit
    while remaining > 0:
        n = min(MAX_PER_REQUEST, remaining)
        start = end - timedelta(seconds=granularity * n)
        rows = get_json(f"{BASE}/products/{product}/candles",
                        params={"granularity": granularity, "start": start.isoformat(), "end": end.isoformat()},
                        retries=2, cache_seconds=30)
        if not isinstance(rows, list) or not rows:
            break
        for c in parse_candles(rows):
            out[c.ts] = c
        remaining -= n
        end = start
    if not out:
        raise ProviderError(f"aucune bougie Coinbase pour {product}")
    return [out[k] for k in sorted(out)]


def fetch_price(product: str = "BTC-USD") -> float:
    data = get_json(f"{BASE}/products/{product}/ticker", retries=2)
    return float(data["price"])
