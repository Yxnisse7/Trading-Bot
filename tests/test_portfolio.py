from datetime import datetime, timedelta, timezone

import pytest

from trading_bot.config import Config, default_assets
from trading_bot.models import Signal, iso
from trading_bot.portfolio import Portfolio, size_position
from trading_bot.storage import Store
from trading_bot.tracker import close_signal

T0 = datetime(2026, 9, 18, 14, 0, tzinfo=timezone.utc)


def _sig(asset="nasdaq", direction="long", entry=20000.0, tp=20060.0, sl=19960.0, created=T0, source="bot"):
    return Signal(id=f"s{int(created.timestamp())}{asset}", asset=asset, asset_label=asset, direction=direction, entry=entry,
                  take_profit=tp, stop_loss=sl, risk_reward=1.5, confidence="moyen", score=3.5, criteria=["rsi"],
                  rationale="", news_context="", created_at=iso(created), expires_at=iso(created + timedelta(hours=1)), source=source)


def test_size_position_risk_and_leverage():
    cfg = Config(assets=default_assets())
    nq = cfg.asset("nasdaq")
    # risque 1 % de 10 000 = 100 ; perte par lot au stop = 40 pts × 2 $ = 80 $ → 1 lot (arrondi au pas)
    s = size_position(10000, 1.0, nq, 20000, 19960)
    assert s["lots"] == 1 and s["risk_amount"] == 80.0 and s["notional"] == 40000.0
    # balance trop petite : 1 000 → risque 10 < 80 par lot → non pris
    s2 = size_position(1000, 1.0, nq, 20000, 19960)
    assert s2["lots"] == 0 and "insuffisante" in s2["reason"]
    # crypto : pas fin, plafond de levier ×3
    btc = cfg.asset("bitcoin")
    s3 = size_position(1000, 1.0, btc, 60000, 59700)   # risque 10 $, 300 $ par BTC → 0,033 BTC
    assert s3["lots"] == 0.033 and s3["leverage"] < 3
    s4 = size_position(1000, 10.0, btc, 60000, 59970)  # risque 100 $, 30 $/BTC → 3,33 BTC = 200 k$ → plafonné à 3 000 $
    assert s4["capped_by_leverage"] and s4["notional"] <= 3000.0 + 60


def test_portfolio_lifecycle_and_no_retroactivity(tmp_path):
    cfg = Config(assets=default_assets())
    store = Store(tmp_path)
    pf = Portfolio(store, cfg)
    assert pf.data["is_default"] and pf.data["balance"] == cfg.portfolio_default_balance
    # nouvelle balance définie à T0 : un signal ouvert avant n'est pas pris
    pf.set_balance(10000, 1.0, T0)
    old = _sig(created=T0 - timedelta(minutes=10))
    assert pf.on_open(old, cfg.asset("nasdaq")) is None
    # signal après : dimensionné
    sig = _sig(created=T0 + timedelta(minutes=5))
    sizing = pf.on_open(sig, cfg.asset("nasdaq"))
    assert sizing["lots"] == 1 and sig.id in pf.data["open"]
    # TP touché : +60 pts × 2 $ = 120 $ brut, coûts 0,01 % × 40 000 = 4 $
    close_signal(sig, "tp", 20060.0, T0 + timedelta(minutes=30), cfg.asset("nasdaq").cost_pct)
    row = pf.on_close(sig, cfg.asset("nasdaq"))
    assert row["pnl_gross"] == 120.0 and row["cost"] == 4.0 and row["pnl"] == 116.0
    assert pf.data["balance"] == 10116.0 and pf.data["peak"] == 10116.0
    # SL sur un short crypto
    s2 = _sig(asset="bitcoin", direction="short", entry=60000.0, tp=59700.0, sl=60300.0, created=T0 + timedelta(hours=1))
    sz = pf.on_open(s2, cfg.asset("bitcoin"))
    assert sz["lots"] > 0
    close_signal(s2, "sl", 60300.0, T0 + timedelta(hours=1, minutes=20), cfg.asset("bitcoin").cost_pct)
    row2 = pf.on_close(s2, cfg.asset("bitcoin"))
    assert row2["pnl"] < 0 and abs(row2["pnl_gross"] + 300 * sz["lots"]) < 1e-6
    assert pf.data["balance"] == round(10116.0 + row2["pnl"], 2)
    summ = pf.summary()
    assert summ["trades"] == 2 and summ["wins"] == 1 and summ["losses"] == 1 and summ["drawdown_pct"] > 0
    text = pf.format_summary()
    assert "Balance" in text and "Trades : 2" in text
    # fantômes ignorés ; balance insuffisante → « non pris »
    assert pf.on_open(_sig(created=T0 + timedelta(hours=2), source="shadow"), cfg.asset("nasdaq")) is None
    pf.set_balance(100, 1.0, T0 + timedelta(hours=3))
    assert len(pf.data["archives"]) == 1 and pf.data["history"] == []
    small = _sig(created=T0 + timedelta(hours=4))
    assert pf.on_open(small, cfg.asset("nasdaq"))["lots"] == 0 and len(pf.data["skipped"]) == 1
    # persistance
    again = Portfolio(Store(tmp_path), cfg)
    assert again.data["balance"] == 100 and not again.data["is_default"]
    with pytest.raises(ValueError):
        pf.set_balance(-5)
