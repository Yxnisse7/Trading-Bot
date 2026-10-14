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
    return make_candles(n=500, drift=0.0003, noise=0.0012, seed=7)


@pytest.fixture
def trending_down():
    return make_candles(n=500, drift=-0.0003, noise=0.0012, seed=11)


@pytest.fixture
def choppy():
    # oscillation sinusoïdale : indécis
    base = make_candles(n=500, drift=0.0, noise=0.0002, seed=3)
    out = []
    for i, c in enumerate(base):
        f = 1 + 0.002 * math.sin(i / 6)
        out.append(Candle(c.ts, c.open * f, c.high * f, c.low * f, c.close * f, c.volume))
    return out


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Aucun test ne doit toucher au réseau : toute requête HTTP échoue immédiatement."""
    import requests

    def _blocked(*args, **kwargs):
        raise requests.ConnectionError("réseau désactivé dans les tests")

    monkeypatch.setattr(requests, "get", _blocked)
    monkeypatch.setattr(requests, "post", _blocked)
    monkeypatch.setattr("trading_bot.providers.http.time.sleep", lambda s: None)


@pytest.fixture(autouse=True)
def _no_bot_model(monkeypatch):
    """Le bot appris (essai 25) ne filtre rien dans les tests, sauf ceux qui le testent exprès."""
    from trading_bot import bot_model
    monkeypatch.setattr(bot_model, "APPLIED", set())


@pytest.fixture(autouse=True)
def _no_exit_override(monkeypatch):
    """Les tests des signaux gardent les sorties d'origine ; l'élargissement de l'essai 29 a son propre test."""
    from trading_bot import signals
    monkeypatch.setattr(signals, "EXIT_OVERRIDE", {})


@pytest.fixture(autouse=True)
def _no_shadow_assets(monkeypatch):
    """Les tests du moteur annoncent les signaux de tous les actifs ; la mise en ombre du 14/10 a son propre test."""
    from trading_bot import engine
    monkeypatch.setattr(engine, "SHADOW_ASSETS", set())
