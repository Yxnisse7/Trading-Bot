"""Setups pré-enregistrés : aucun biais de futur, déclenchement, backtest et verdict."""
from trading_bot import setups
from trading_bot.config import Config, default_assets
from trading_bot.models import Candle

from conftest import make_candles


def _uptrend_with_pullback(n=320, start=1_700_000_000):
    """Indicateurs posés à la main (tendance haussière forte), bougies : montée, repli sur l'EMA 20, reprise."""
    candles, price = [], 100.0
    for i in range(n):
        o = price
        price += -0.3 if n - 6 <= i < n - 1 else 0.2        # 5 bougies de repli puis la reprise
        if i == n - 1:
            price = o + 0.6
        candles.append(Candle(start + i * 300, o, max(o, price) + 0.05, min(o, price) - 0.05, price, 100.0))
    ema20 = [c.close - 1.0 for c in candles]                 # moyenne sous le prix pendant la montée
    for j in range(n - 3, n - 1):
        ema20[j] = candles[j].low + 0.01                     # le repli touche l'EMA 20
    ema20[-1] = candles[-1].close - 0.5
    return setups.Prepared(candles, ema20, [0.6] * n, [40.0] * n, [30.0] * n, [10.0] * n,
                           [50.0] * n, [100.0] * n)


def test_no_lookahead_detection_matches_truncated_series():
    candles = make_candles(n=700, drift=0.0004, noise=0.002, seed=3, start_ts=1_700_000_000)
    full = setups.prepare(candles)
    for setup in setups.SETUPS:
        for i in range(setups.WARMUP, len(candles), 7):
            cut = setups.prepare(candles[: i + 1])
            assert setups.detect(full, i, setup) == setups.detect(cut, i, setup)


def test_pullback_setup_fires_long_in_an_uptrend():
    p = _uptrend_with_pullback()
    h = setups.detect(p, len(p.candles) - 1, "setup_repli")
    assert h and h["direction"] == "long"
    assert h["stop"] < h["entry"] < h["target"]
    assert abs((h["target"] - h["entry"]) - 1.5 * (h["entry"] - h["stop"])) < 1e-9
    assert setups.detect(p, len(p.candles) - 1, "setup_vwap") is None        # ADX 40 : pas de VWAP
    p.adx15[-1] = 25.0
    assert setups.detect(p, len(p.candles) - 1, "setup_repli") is None       # tendance trop faible


def test_backtest_one_position_at_a_time_and_evaluation_verdict():
    cfg = Config(assets=default_assets())
    asset = cfg.assets["bitcoin"]
    candles = make_candles(n=1500, drift=0.0003, noise=0.002, seed=11, start_ts=1_700_000_000)
    sigs = setups.run_setup_backtest(asset, candles, "setup_repli")
    for a, b in zip(sigs, sigs[1:]):
        assert b.created_at >= a.closed_at                  # jamais deux positions en même temps
    assert all(s.status in ("tp", "sl", "expired") and s.source == "backtest" for s in sigs)
    out = setups.evaluate({"bitcoin": asset}, {"bitcoin": candles}, "test")
    v = out["setups"]["setup_repli"]
    assert set(v["checks"]) and v["passed"] == all(v["checks"].values())
    assert v["total"]["n"] == len(sigs)
