from datetime import datetime, timedelta, timezone

from trading_bot.models import Candle, Signal, iso
from trading_bot.tracker import format_outcome, update_signal

T0 = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)


def _sig(direction="long", entry=100.0, tp=101.0, sl=99.5):
    return Signal(id="abc", asset="nasdaq", asset_label="NQ", direction=direction, entry=entry,
                  take_profit=tp, stop_loss=sl, risk_reward=2.0, confidence="moyen", score=3.5,
                  criteria=["trend_5m"], rationale="", news_context="calme",
                  created_at=iso(T0), expires_at=iso(T0 + timedelta(minutes=60)))


def _candle(minute: int, low: float, high: float, close: float | None = None) -> Candle:
    ts = int((T0 + timedelta(minutes=minute)).timestamp())
    return Candle(ts, (low + high) / 2, high, low, close if close is not None else (low + high) / 2)


def test_tp_hit_with_candles():
    s = _sig()
    candles = [_candle(-5, 99.8, 100.2), _candle(5, 99.9, 100.4), _candle(10, 100.2, 101.2)]
    done = update_signal(s, candles, 100.9, T0 + timedelta(minutes=12))
    assert done is not None and done.status == "tp"
    assert done.close_price == 101.0 and done.duration_minutes == 10
    assert done.pnl_pct == 1.0
    assert "TP TOUCHÉ" in format_outcome(done)


def test_sl_wins_when_both_touched_same_candle():
    s = _sig()
    done = update_signal(s, [_candle(5, 99.0, 101.5)], None, T0 + timedelta(minutes=6))
    assert done.status == "sl" and done.pnl_pct == -0.5


def test_short_sl_with_price_only():
    s = _sig(direction="short", entry=100.0, tp=99.0, sl=100.5)
    assert update_signal(s, None, 100.2, T0 + timedelta(minutes=5)) is None
    done = update_signal(s, None, 100.6, T0 + timedelta(minutes=6))
    assert done.status == "sl"


def test_candles_before_signal_are_ignored():
    s = _sig()
    done = update_signal(s, [_candle(-10, 98.0, 102.0)], 100.1, T0 + timedelta(minutes=5))
    assert done is None


def test_expiry_closes_at_current_price():
    s = _sig()
    assert update_signal(s, None, 100.3, T0 + timedelta(minutes=59)) is None
    done = update_signal(s, None, 100.3, T0 + timedelta(minutes=60))
    assert done.status == "expired" and done.close_price == 100.3
    assert abs(done.pnl_pct - 0.3) < 1e-6 and done.duration_minutes == 60
    assert "EXPIRÉ" in format_outcome(done)


def test_candles_after_expiry_do_not_count():
    s = _sig()
    done = update_signal(s, [_candle(70, 100.5, 101.5)], 100.2, T0 + timedelta(minutes=75))
    assert done.status == "expired"


def test_costs_are_deducted_from_pnl():
    s = _sig()
    done = update_signal(s, None, 101.0, T0 + timedelta(minutes=5), cost_pct=0.06)
    assert done.status == "tp"
    assert done.pnl_gross_pct == 1.0 and done.pnl_pct == 0.94
    assert "net" in format_outcome(done) and "brut" in format_outcome(done)
