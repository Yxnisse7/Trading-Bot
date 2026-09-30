"""Apprentissage par contexte, excursions (règles de sortie) et filtres testés hors échantillon."""
import random
from datetime import datetime, timedelta, timezone

from trading_bot import context as ctxmod
from trading_bot import engine as engmod
from trading_bot.config import Config, default_assets
from trading_bot.learning import learn
from trading_bot.models import Candle, Signal, iso
from trading_bot.storage import Store

from test_open_and_restart import THU, _engine

T0 = datetime(2026, 9, 29, 13, 45, tzinfo=timezone.utc)      # 15:45 à Paris, 15 min après l'ouverture US


def _sig(i=0, status="sl", r=-1.0, source="bot", asset="nasdaq", when=T0, **meta):
    """Long à 100, stop à 99 (risque 1 point = 1 % : R = résultat en %)."""
    return Signal(id=f"s{i}", asset=asset, asset_label=asset, direction="long", entry=100.0, take_profit=101.5,
                  stop_loss=99.0, risk_reward=1.5, confidence="fort", score=6.0, criteria=["adx"], rationale="",
                  news_context="", created_at=iso(when), expires_at=iso(when + timedelta(hours=1)), status=status,
                  closed_at=iso(when + timedelta(minutes=20)), close_price=100.0 + r, pnl_gross_pct=r,
                  pnl_pct=r - 0.05, source=source, meta=dict(meta))


def test_excursions_and_stop_at_entry_rule():
    s = _sig(status="open")
    s.meta = {}
    t = int(T0.timestamp())
    candles = [Candle(t, 100, 100.6, 99.8, 100.5, 1), Candle(t + 300, 100.5, 100.55, 99.95, 100.0, 1),
               Candle(t + 600, 100, 100.1, 99.0, 99.0, 1)]
    ctxmod.walk_excursion(s, candles[:2], None)
    ctxmod.walk_excursion(s, candles, None)              # bougies déjà vues ignorées
    exc = s.meta["exc"]
    assert exc["mfe"] == 0.6 and exc["mae"] == 1.0
    assert exc["be"]["0.5"] and not exc["be"]["0.8"]     # +0,6 R atteint, puis retour à l'entrée
    assert ctxmod.rule_r(s, -1.0, 0.5) == 0.0 and ctxmod.rule_r(s, -1.0, 1.0) == -1.0


def test_exit_report_flags_a_better_rule_only_with_enough_trades():
    cfg = Config(assets=default_assets())
    trades = []
    for i in range(120):
        be = i % 2 == 0                                   # la moitié des stops était passée par +0,8 R
        trades.append(_sig(i, "sl", -1.0, exc={"mfe": 0.9 if be else 0.2, "mae": 1.0,
                                               "be": {"0.5": be, "0.8": be, "1.0": False}, "armed": {}}))
    rep = ctxmod.exit_report(trades, cfg)["réels et en ombre"]
    assert rep["n"] == 120 and rep["sl_reached"]["0.8"] == 60
    assert rep["rules"]["0.8"]["better"] and not rep["rules"]["1.0"]["better"]
    assert not ctxmod.exit_report(trades[:50], cfg)["réels et en ombre"]["rules"]["0.8"]["better"]


def test_context_learning_finds_a_losing_bucket_and_matches_new_signals():
    cfg = Config(assets=default_assets())
    rng = random.Random(3)
    trades = []
    for i in range(240):
        adx = rng.uniform(15, 45)
        r = -1.0 if adx < 25 else rng.choice([1.5, -1.0, 1.5])
        trades.append(_sig(i, "tp" if r > 0 else "sl", r, ctx={"adx": adx, "weekday": 1}))
    adj = learn(trades, cfg)
    feats = adj["context"]["features"]
    assert "adx" in feats and any(a["feature"] == "adx" for a in adj["context"]["avoid"])
    assert ctxmod.context_hits({"adx": 16.0}, adj["context"]) and not ctxmod.context_hits({"adx": 40.0}, adj["context"])
    assert any("contexte perdant" in n for n in adj["notes"])


def test_filters_are_judged_only_on_trades_marked_after_the_test_started():
    cfg = Config(assets=default_assets())
    kept = [_sig(i, "tp" if i % 2 else "sl", 1.5 if i % 2 else -1.0, filters=[], filters_checked=True) for i in range(110)]
    out = [_sig(200 + i, "sl", -1.0, filters=["sans_ouverture_us"], filters_checked=True) for i in range(25)]
    rep = ctxmod.filter_report(kept + out, cfg)["sans_ouverture_us"]
    assert rep["n_out"] == 25 and rep["n_kept"] == 110 and rep["promoted"]
    unmarked = [_sig(i, "sl", -1.0) for i in range(200)]             # trades d'avant le test : ignorés
    assert ctxmod.filter_report(unmarked, cfg)["sans_ouverture_us"]["n"] == 0
    assert not ctxmod.filter_report(kept[:60] + out, cfg)["sans_ouverture_us"]["promoted"]


def test_us_open_window():
    assert ctxmod.in_us_open_window("nasdaq", T0) and ctxmod.in_us_open_window("gold", T0)
    assert not ctxmod.in_us_open_window("bitcoin", T0)
    assert not ctxmod.in_us_open_window("nasdaq", T0.replace(hour=16))       # 2 h 30 après l'ouverture
    assert ctxmod.in_us_open_window("sp500", T0.replace(hour=13, minute=0))  # 30 min avant


def test_scan_marks_signals_and_applies_a_proven_filter(tmp_path, monkeypatch):
    now = THU.replace(hour=14, minute=15)                  # 16:15 à Paris : dans la fenêtre de l'ouverture
    eng = _engine(tmp_path, monkeypatch, now)
    real = eng.scan(now)
    nq = next(s for s in real if s.asset == "nasdaq")
    assert nq.meta["filters"] == ["sans_ouverture_us"] and nq.meta["filters_checked"]
    assert {"adx", "rsi_dir", "cost_r", "us_open_min", "weekday"} & set(nq.meta["ctx"])
    btc = next(s for s in real if s.asset == "bitcoin")
    assert btc.meta["filters"] == []

    # filtre promu : les signaux des indices dans la fenêtre sont suivis en silence, pas envoyés
    eng2 = _engine(tmp_path / "b", monkeypatch, now)
    eng2.store.save_adjustments({"promoted_variants": ["sans_ouverture_us"]})
    real2 = eng2.scan(now)
    assert all(s.asset not in ("nasdaq", "sp500", "gold") for s in real2)
    assert ("nasdaq", "sans_ouverture_us") in {(s.asset, (s.meta or {}).get("variant")) for s in eng2.store.open_shadow()}


def test_backtest_trades_keep_context_and_excursions(tmp_path):
    st = Store(tmp_path)
    s = _sig(ctx={"adx": 30.0}, exc={"mfe": 0.4, "mae": 1.0, "be": {}, "armed": {}})
    s.meta["details"] = {"trop": "gros"}
    st.save_backtests({"nasdaq": {"asset_label": "NQ", "trades": [s.to_dict()]}}, replace=True)
    back = st.backtest_trades()[0]
    assert back.meta == {"ctx": {"adx": 30.0}, "exc": {"mfe": 0.4, "mae": 1.0, "be": {}, "armed": {}}}
