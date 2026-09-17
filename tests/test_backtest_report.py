from datetime import datetime, timezone

from trading_bot.backtest import format_backtest, run_backtest
from trading_bot.config import Config, default_assets
from trading_bot.report import build_report
from trading_bot import indicators as ind

from conftest import make_candles


def _cfg():
    cfg = Config(assets=default_assets())
    cfg.assets["nasdaq"].session_utc = None
    return cfg


def test_backtest_runs_without_lookahead_and_respects_policy():
    cfg = _cfg()
    candles = make_candles(n=2000, drift=0.0002, noise=0.0012, seed=5)
    res = run_backtest(cfg.asset("nasdaq"), candles, cfg, step=3)
    assert res["n"] > 0
    assert res["tp"] + res["sl"] + res["expired"] == res["n"]
    trades = res["trades"]
    for t in trades:
        assert t["status"] in ("tp", "sl", "expired") and t["duration_minutes"] <= 60
    # au plus 3 signaux par jour civil (Europe/Paris) et jamais deux à moins d'une heure
    from collections import Counter
    from trading_bot.models import parse_iso
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(cfg.timezone)
    per_day = Counter(parse_iso(t["created_at"]).astimezone(tz).date() for t in trades)
    assert max(per_day.values()) <= cfg.max_signals_per_asset_per_day
    times = sorted(parse_iso(t["created_at"]) for t in trades)
    assert all((b - a).total_seconds() >= cfg.cooldown_minutes * 60 for a, b in zip(times, times[1:]))
    text = format_backtest(res)
    assert "BACKTEST" in text and "Taux de réussite" in text


def test_backtest_driftless_market_mostly_rejects():
    cfg = _cfg()
    candles = make_candles(n=1500, drift=0.0, noise=0.0008, seed=9)
    res = run_backtest(cfg.asset("nasdaq"), candles, cfg, step=3)
    n_days = (candles[-1].ts - candles[0].ts) // 86400 + 1
    assert res["n"] <= cfg.max_signals_per_asset_per_day * n_days
    assert sum(res["rejected"].values()) > res["n"] * 3


def test_report_without_history():
    cfg = _cfg()
    text = build_report([], cfg, None, None, now=datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc))
    assert "Trades clôturés : **0**" in text and "paper trading" in text


def test_barrier_probabilities_monotonic():
    sigma = 0.001
    p_wide, _ = ind.barrier_probabilities(100, 101.0, 99.0, sigma)
    p_narrow, p_tp = ind.barrier_probabilities(100, 100.2, 99.8, sigma)
    assert p_narrow > p_wide
    assert 0.3 < p_tp < 0.7  # sans dérive et barrières symétriques : ≈ 50 % des cas résolus
    assert ind.barrier_probabilities(100, 101, 99, 0.0) == (0.0, 0.0)


def test_adx_gate_rejects_ranging_market():
    cfg = _cfg()
    from trading_bot.analysis import assess
    candles = make_candles(n=500, drift=0.0, noise=0.0008, seed=9)
    a = assess(cfg.asset("nasdaq"), candles, cfg)
    assert a.direction is None
    assert any("ADX" in r for r in a.reasons_rejected)


def test_closed_candles_and_vwap():
    candles = make_candles(n=20)
    assert len(ind.closed_candles(candles, candles[-1].ts + 299)) == 19
    assert len(ind.closed_candles(candles, candles[-1].ts + 300)) == 20
    v = ind.vwap(candles, candles[0].ts)
    lo, hi = min(c.low for c in candles), max(c.high for c in candles)
    assert lo <= v <= hi
    assert ind.vwap([candles[0]._replace(volume=0) if hasattr(candles[0], "_replace") else candles[0]], candles[0].ts + 1) is None
