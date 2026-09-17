from datetime import datetime, timedelta, timezone

from trading_bot.analysis import DEFAULT_WEIGHTS
from trading_bot.learning import analyze, learn, win_rate
from trading_bot.models import Signal, iso
from trading_bot.summary import daily_summary

T0 = datetime(2026, 9, 17, 13, 0, tzinfo=timezone.utc)


def _closed(i: int, status: str, criteria: list[str], asset="nasdaq", conf="moyen") -> Signal:
    created = T0 + timedelta(minutes=10 * i)
    pnl = {"tp": 0.5, "sl": -0.3, "expired": 0.05}[status]
    return Signal(id=f"s{i}", asset=asset, asset_label=asset, direction="long", entry=100.0,
                  take_profit=100.5, stop_loss=99.7, risk_reward=1.67, confidence=conf, score=3.5,
                  criteria=criteria, rationale="", news_context="actualité calme",
                  created_at=iso(created), expires_at=iso(created + timedelta(hours=1)), status=status,
                  closed_at=iso(created + timedelta(minutes=30)), close_price=100.0 + pnl, pnl_pct=pnl,
                  duration_minutes=30)


def test_win_rate_ignores_expired():
    sigs = [_closed(0, "tp", []), _closed(1, "sl", []), _closed(2, "expired", []), _closed(3, "tp", [])]
    assert win_rate(sigs) == 2 / 3
    assert win_rate([]) is None


def test_learn_lowers_weak_and_raises_strong(cfg):
    hist = [_closed(i, "sl", ["volume"]) for i in range(10)] + [_closed(20 + i, "tp", ["macd"]) for i in range(10)]
    adj = learn(hist, cfg)
    assert adj["weights"]["volume"] < DEFAULT_WEIGHTS["volume"]
    assert adj["weights"]["macd"] > DEFAULT_WEIGHTS["macd"]
    assert adj["weights"]["rsi"] == DEFAULT_WEIGHTS["rsi"]
    assert any("volume" in n for n in adj["notes"])
    # la tranche 13h UTC a 50 % : pas évitée
    assert adj["avoid_hours_utc"] == []


def test_learn_needs_enough_samples(cfg):
    hist = [_closed(i, "sl", ["volume"]) for i in range(5)]
    adj = learn(hist, cfg)
    assert adj["weights"]["volume"] == DEFAULT_WEIGHTS["volume"]


def test_analyze_groups(cfg):
    hist = [_closed(0, "tp", ["rsi"], asset="gold"), _closed(1, "sl", ["rsi", "macd"], asset="bitcoin")]
    rep = analyze(hist)
    assert rep["total"] == 2
    assert rep["by_asset"]["gold"]["tp"] == 1
    assert rep["by_criterion"]["rsi"]["n"] == 2 and rep["by_criterion"]["macd"]["sl"] == 1


def test_daily_summary_content(cfg):
    hist = [_closed(0, "tp", ["rsi"]), _closed(1, "sl", ["rsi"]), _closed(2, "expired", ["rsi"])]
    text = daily_summary(hist, cfg, T0.date(), {"notes": ["rsi: test"], "avoid_hours_utc": []})
    assert "Signaux proposés : 3" in text
    assert "Gagnants (TP) : 1 | Perdants (SL) : 1 | Expirés sans issue : 1" in text
    assert "Taux de réussite du jour : 50%" in text
    assert "paper trading" in text
    assert "rsi: test" in text
