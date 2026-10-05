"""Suivi en ombre des stratégies du laboratoire : même règle que le test, une position à la fois, silencieux."""
from datetime import datetime, timezone

from trading_bot import strategies as sl
from trading_bot.config import Config, default_assets
from trading_bot.engine import Engine
from trading_bot.storage import Store

from conftest import make_candles


def _engine(tmp_path, monkeypatch, candles):
    eng = Engine(Config(assets=default_assets()))
    eng.store = Store(tmp_path / "data", tmp_path / "docs")
    monkeypatch.setattr("trading_bot.engine.market.fetch_candles_5m", lambda asset, days=5: candles)
    monkeypatch.setattr(sl, "SHADOW", {("donchian_1h", "bitcoin"): "2026-01-01T00:00:00Z"})
    return eng


def test_lab_shadow_records_the_same_trades_as_the_backtest_once_per_hour(tmp_path, monkeypatch):
    start = int(datetime(2026, 3, 2, tzinfo=timezone.utc).timestamp())
    candles = make_candles(n=288 * 8, start_price=60000, drift=0.0001, noise=0.002, seed=9, start_ts=start)
    now = datetime.fromtimestamp(candles[-1].ts + 300, tz=timezone.utc)
    eng = _engine(tmp_path, monkeypatch, candles)
    rec = eng.lab_shadow(now)["donchian_1h:bitcoin"]
    expected = sl.donchian_1h(candles, "bitcoin")
    assert [t["entry_ts"] for t in rec["trades"]] == [t.entry_ts for t in expected]
    closed = [t for t in rec["trades"] if t["status"] == "closed"]
    assert closed and all(t["r_topstep"] is not None for t in closed) and rec["n"] == len(closed)
    assert sum(t["status"] == "open" for t in rec["trades"]) <= 1
    # même heure : rien n'est recalculé ; aucune notification n'est jamais envoyée
    monkeypatch.setattr("trading_bot.engine.market.fetch_candles_5m", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    assert eng.lab_shadow(now)["donchian_1h:bitcoin"]["trades"] == rec["trades"]
    assert eng.store.lab_shadow()["donchian_1h:bitcoin"]["checked_hour"] == now.replace(minute=0).strftime("%Y-%m-%dT%H:00:00Z")


def test_lab_shadow_ignores_trades_before_its_start(tmp_path, monkeypatch):
    start = int(datetime(2026, 3, 2, tzinfo=timezone.utc).timestamp())
    candles = make_candles(n=288 * 8, start_price=60000, drift=0.0001, noise=0.002, seed=9, start_ts=start)
    now = datetime.fromtimestamp(candles[-1].ts + 300, tz=timezone.utc)
    eng = _engine(tmp_path, monkeypatch, candles)
    monkeypatch.setattr(sl, "SHADOW", {("donchian_1h", "bitcoin"): "2030-01-01T00:00:00Z"})
    assert eng.lab_shadow(now)["donchian_1h:bitcoin"]["trades"] == []
