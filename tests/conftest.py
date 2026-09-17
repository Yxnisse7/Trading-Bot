import math
import random
from datetime import datetime, timezone

import pytest

from trading_bot.config import Config, default_assets
from trading_bot.models import Candle


def make_candles(n: int = 400, start_price: float = 20000.0, drift: float = 0.0,
                 noise: float = 0.0008, seed: int = 42, step: int = 300,
                 start_ts: int | None = None) -> list[Candle]:
    """Série 5m synthétique : marche aléatoire avec dérive optionnelle (fraction par bougie)."""
    rnd = random.Random(seed)
    ts = start_ts if start_ts is not None else int(datetime(2026, 9, 17, 8, 0, tzinfo=timezone.utc).timestamp()) - n * step
    price = start_price
    out = []
    for i in range(n):
        o = price
        change = drift + rnd.gauss(0, noise)
        c = o * (1 + change)
        wiggle = abs(rnd.gauss(0, noise)) * o
        h = max(o, c) + wiggle
        l = min(o, c) - wiggle
        v = 1000 + rnd.random() * 200
        out.append(Candle(ts=ts + i * step, open=o, high=h, low=l, close=c, volume=v))
        price = c
    return out


@pytest.fixture
def cfg() -> Config:
    return Config(assets=default_assets())


@pytest.fixture
def trending_up():
    return make_candles(n=500, drift=0.0006, noise=0.0004, seed=7)


@pytest.fixture
def trending_down():
    return make_candles(n=500, drift=-0.0006, noise=0.0004, seed=11)


@pytest.fixture
def choppy():
    # oscillation sinusoïdale : indécis
    base = make_candles(n=500, drift=0.0, noise=0.0002, seed=3)
    out = []
    for i, c in enumerate(base):
        f = 1 + 0.002 * math.sin(i / 6)
        out.append(Candle(c.ts, c.open * f, c.high * f, c.low * f, c.close * f, c.volume))
    return out
