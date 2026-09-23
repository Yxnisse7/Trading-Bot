"""Arrêt manuel d'un trade : sortie encaissée par la simulation, suivi silencieux, règle d'apprentissage."""
from datetime import datetime, timedelta, timezone

import pytest

from trading_bot import engine as engmod
from trading_bot.config import Config, default_assets
from trading_bot.engine import Engine
from trading_bot.learning import trade_r
from trading_bot.models import Signal, iso
from trading_bot.storage import Store

NOW = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)


def _sig(**kw) -> Signal:
    base = dict(id="abc123def0", asset="gold", asset_label="Or (XAU/USD)", direction="long", entry=100.0,
                take_profit=102.0, stop_loss=99.0, risk_reward=2.0, confidence="fort", score=6.0,
                criteria=["macd"], rationale="", news_context="", created_at=iso(NOW), expires_at=iso(NOW + timedelta(hours=1)))
    base.update(kw)
    return Signal(**base)


@pytest.fixture
def eng(tmp_path, monkeypatch):
    sent = []
    e = Engine(Config(assets=default_assets()), Store(tmp_path))
    e.set_balance(1000, 1.0, NOW - timedelta(minutes=5))
    sig = _sig()
    sig.meta["sim"] = e.portfolio.on_open(sig, e.cfg.assets["gold"])
    e.store.add_signal(sig)
    monkeypatch.setattr(engmod, "notify", lambda text, **kw: sent.append((text, kw)))
    monkeypatch.setattr(engmod.market, "fetch_candles_1m", lambda asset: [])
    monkeypatch.setattr(Engine, "eur_rate", lambda self: 1.17)
    return e, sent, monkeypatch


def test_stop_closes_the_simulated_position_and_keeps_tracking(eng):
    e, sent, mp = eng
    res = e.stop_trade("or", NOW + timedelta(minutes=10), price=101.0)
    row = res["row"]
    assert row["status"] == "manual" and row["exit"] == 101.0 and row["pnl"] > 0
    assert e.portfolio.data["open"] == {} and e.portfolio.data["balance"] > 1000
    text, kw = sent[-1]
    assert "ARRÊTÉ À LA MAIN" in text and "€" in text and kw["reply_to"] == "abc123def0"
    # le signal reste suivi, mais ne bloque plus un nouveau signal sur l'actif
    open_sigs = e.store.open_signals()
    assert len(open_sigs) == 1 and open_sigs[0].meta["manual_exit"]["price"] == 101.0
    assert not any("déjà ouvert" in r for r in e._policy_block("gold", open_sigs, NOW + timedelta(hours=2)))
    # plus rien à arrêter
    with pytest.raises(ValueError):
        e.stop_trade(None, NOW, price=101.0)


def test_real_outcome_after_manual_stop_is_silent_and_does_not_touch_the_balance(eng):
    e, sent, mp = eng
    e.stop_trade(None, NOW + timedelta(minutes=10), price=101.0)
    balance = e.portfolio.data["balance"]
    mp.setattr(engmod.market, "fetch_price", lambda asset: 98.0)          # le prix finit au SL
    closed = e.track(NOW + timedelta(minutes=30))
    assert closed and closed[0].status == "sl"
    assert e.portfolio.data["balance"] == balance
    text, kw = sent[-1]
    assert "Suite du trade arrêté" in text and kw.get("silent") and "Bonne sortie" in text


def test_learning_rule_for_manual_stops():
    risk = 1.0  # entrée 100, SL 99 → 1 % de risque
    # arrêté en gain (+1 %), puis SL : le petit gain est appris
    s = _sig(status="sl", pnl_pct=-1.0, pnl_gross_pct=-1.0, meta={"manual_exit": {"pnl_pct": 0.95, "pnl_gross_pct": 1.0}})
    assert trade_r(s) == pytest.approx(1.0 / risk)
    # arrêté en gain, puis TP : le TP reste un TP
    s = _sig(status="tp", pnl_pct=2.0, pnl_gross_pct=2.0, meta={"manual_exit": {"pnl_pct": 0.5, "pnl_gross_pct": 0.5}})
    assert trade_r(s) == pytest.approx(2.0)
    # arrêté en perte, puis TP : c'est un gain pour le bot
    s = _sig(status="tp", pnl_pct=2.0, pnl_gross_pct=2.0, meta={"manual_exit": {"pnl_pct": -0.5, "pnl_gross_pct": -0.5}})
    assert trade_r(s) == pytest.approx(2.0)
    # arrêté en perte, puis SL : la vraie perte compte (pas celle, plus petite, de la sortie)
    s = _sig(status="sl", pnl_pct=-1.0, pnl_gross_pct=-1.0, meta={"manual_exit": {"pnl_pct": -0.4, "pnl_gross_pct": -0.4}})
    assert trade_r(s) == pytest.approx(-1.0)


def test_telegram_stop_command(eng):
    e, sent, mp = eng
    mp.setattr(engmod.market, "fetch_price", lambda asset: 100.5)
    assert e.handle_command("/stop", NOW) is None
    assert "ARRÊTÉ À LA MAIN" in sent[-1][0]
    assert "Arrêt impossible" in e.handle_command("/stop", NOW)
    assert "/stop" in e.help_text()
