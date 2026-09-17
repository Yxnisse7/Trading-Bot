"""Yahoo Finance (API chart publique, sans clé) : NQ=F, GC=F, BTC-USD…"""
from __future__ import annotations

from typing import Any

from ..models import Candle
from .http import ProviderError, get_json

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


INTERVAL_SECONDS = {"1m": 60, "2m": 120, "5m": 300, "15m": 900, "30m": 1800, "60m": 3600, "1h": 3600, "1d": 86400}


def parse_chart(payload: dict[str, Any], interval: str | None = None) -> list[Candle]:
    """Convertit la réponse « chart » en bougies.

    Yahoo ajoute en fin de série un point correspondant à la dernière cotation (horodatage
    non aligné sur l'intervalle, ex. 10:16:45 pour la période 10:15) : il est écarté pour ne
    pas dupliquer la bougie en cours.
    """
    step = INTERVAL_SECONDS.get(interval or "", 0)
    try:
        result = payload["chart"]["result"][0]
        ts = result["timestamp"]
        q = result["indicators"]["quote"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError(f"réponse Yahoo inattendue: {exc}") from exc
    candles: list[Candle] = []
    for i, t in enumerate(ts):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        if step and int(t) % step != 0:
            continue
        v = q.get("volume", [None] * len(ts))[i] or 0.0
        candles.append(Candle(ts=int(t), open=float(o), high=float(h), low=float(l),
                              close=float(c), volume=float(v)))
    return candles


def fetch_candles(symbol: str, interval: str = "5m", range_: str = "5d") -> list[Candle]:
    data = get_json(CHART_URL.format(symbol=symbol),
                    params={"interval": interval, "range": range_, "includePrePost": "false"},
                    cache_seconds=60)
    candles = parse_chart(data, interval)
    if not candles:
        raise ProviderError(f"aucune bougie Yahoo pour {symbol}")
    return candles


def fetch_price(symbol: str) -> float:
    data = get_json(CHART_URL.format(symbol=symbol), params={"interval": "1m", "range": "1d"})
    try:
        meta = data["chart"]["result"][0]["meta"]
        return float(meta["regularMarketPrice"])
    except (KeyError, IndexError, TypeError):
        candles = parse_chart(data)
        if not candles:
            raise ProviderError(f"prix Yahoo indisponible pour {symbol}")
        return candles[-1].close
