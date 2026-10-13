"""Essai 7 : alerte de décrochage des stratégies en ombre."""
from types import SimpleNamespace

from trading_bot import drift


REF = [1.5, -1.0, 2.0, -1.0, -1.0, 0.5, 3.0, -1.0, -1.0, 0.2] * 10


def test_max_drawdown_measures_worst_fall_from_peak():
    assert drift.max_drawdown([1, -2, 0.5, -1]) == 2.5
    assert drift.max_drawdown([1, 1]) == 0


def test_thresholds_need_enough_trades():
    assert drift.status_of(3, 0.001, 0.5) == "trop tôt"
    assert drift.status_of(6, 0.001, 0.5) == "à surveiller"
    assert drift.status_of(10, 0.005, 0.5) == "décroché"
    assert drift.status_of(10, 0.3, 0.995) == "décroché"
    assert drift.status_of(10, 0.3, 0.5) == "dans la norme"


def test_compare_flags_a_live_run_far_below_the_backtest():
    ok = drift.compare(REF, REF[:12], draws=500)
    assert ok["status"] == "dans la norme"
    bad = drift.compare(REF, [-1.0] * 12, draws=500)
    assert bad["status"] == "décroché" and bad["cum_pct"] < 0.01
    assert drift.compare(REF[:10], [-1.0] * 12)["status"] == "trop tôt"      # référence trop courte


def _sig(r_points, status, day):
    d = {"asset": "gold", "entry": 3000.0, "stop_loss": 2990.0, "pnl_gross_pct": r_points / 3000 * 100,
         "created_at": f"2026-10-{day:02d}T10:00:00Z"}
    return SimpleNamespace(source="shadow", meta={"variant": drift.VARIANT}, status=status,
                           created_at=d["created_at"], to_dict=lambda: d)


def test_run_alerts_only_when_status_worsens_and_blocks_promotion():
    lab = {"donchian_1h:gold": {"trades": [{"entry_ts": i, "status": "closed", "r_topstep": 1.0} for i in range(3)]
                                + [{"entry_ts": 9, "status": "open"}]}}
    sigs = [_sig(-10.0, "sl", d) for d in range(1, 13)] + [_sig(5.0, "open", 20)]
    ref = {"donchian_1h:gold": {"rSeries": REF}, drift.VARIANT: {"rSeries": REF}}
    sent = []
    state = drift.run(lab, sigs, ref, {}, send=sent.append)
    assert state["cells"]["donchian_1h:gold"]["n"] == 3 and state["cells"][drift.VARIANT]["n"] == 12
    assert state["cells"][drift.VARIANT]["status"] == "décroché" and len(sent) == 1
    assert "Horizon 3 h" in sent[0] and "promue" in sent[0]
    assert drift.blocked(state) == {drift.VARIANT}
    assert drift.run(lab, sigs, ref, state, send=sent.append) is None          # rien de neuf : pas de calcul
    more = sigs + [_sig(-10.0, "sl", 25)]
    again = drift.run(lab, more, ref, state, send=sent.append)
    assert again["cells"][drift.VARIANT]["status"] == "décroché" and len(sent) == 1   # pas de doublon
    assert again["cells"][drift.VARIANT]["since_status"] == state["cells"][drift.VARIANT]["since_status"]


def test_engine_skips_promotion_of_a_drifting_variant(tmp_path, monkeypatch):
    from trading_bot.storage import Store
    st = Store(tmp_path)
    st.save_drift({"cells": {drift.VARIANT: {"status": "décroché"}, "donchian_1h:gold": {"status": "décroché"}}})
    assert drift.blocked(st.drift()) == {drift.VARIANT}


def test_live_strategy_sends_entry_then_exit_and_journals_topstep(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from trading_bot import engine as engmod
    from trading_bot import strategies as sl
    from trading_bot.config import load_config
    sent = []
    monkeypatch.setattr(engmod, "notify", lambda text, **k: sent.append(text))
    cfg = load_config()
    eng = engmod.Engine(cfg)
    from trading_bot.storage import Store
    eng.store = Store(tmp_path)
    now = datetime(2026, 10, 8, 14, 20, tzinfo=timezone.utc)
    t0 = int(datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc).timestamp())
    trade = {"entry_ts": t0, "direction": "long", "entry": 4000.0, "risk": 10.0, "stop": 3990.0, "status": "open",
             "reason": None, "exit_ts": None, "exit": None, "r_topstep": None}
    since = datetime(2026, 10, 8, 7, 30, tzinfo=timezone.utc)
    asset = cfg.assets["gold"]
    eng._live_signals("donchian_day:gold", asset, [trade], since, now)
    assert len(sent) == 1 and "SIGNAL RÉEL" in sent[0] and "ACHAT" in sent[0] and "Stop : 3 990,00" in sent[0]
    assert trade["micros"] == 2 and trade["close_at"] == sl.session_close_ts(t0)       # 250 $ ÷ (10 pts × 10 $)
    eng._live_signals("donchian_day:gold", asset, [trade], since, now)
    assert len(sent) == 1                                                               # pas de doublon
    trade.update(status="closed", reason="heure", exit_ts=t0 + 3600 * 6, exit=4012.5, r_topstep=1.21)
    eng._live_signals("donchian_day:gold", asset, [trade], since, now + timedelta(hours=6))
    assert len(sent) == 2 and "SORTIE" in sent[1] and "+1,21 R" in sent[1] and "+250 $" in sent[1]
    journal = eng.topstep().state["journal"]
    assert len(journal) == 1 and journal[0]["contracts"] == 2 and journal[0]["exit"] == 4012.5
    old = dict(trade, entry_ts=t0 - 86_400 * 3, notified_entry=None, notified_exit=None)
    eng._live_signals("donchian_day:gold", asset, [old], since, now)
    assert len(sent) == 2                                                               # rien d'ancien


def test_live_donchian_day_does_not_exit_on_the_unfinished_last_hour():
    """En direct, la dernière bougie 1 h n'a qu'une bougie 5 min : ce n'est pas la fin de séance."""
    from datetime import datetime, timezone
    from trading_bot import strategies as sl
    from trading_bot.models import Candle
    t0 = int(datetime(2026, 10, 6, 13, 0, tzinfo=timezone.utc).timestamp())       # 8:00 à Chicago
    candles = [Candle(t0 + 300 * k, 100.0, 100.5, 99.5, 100.0, 1.0) for k in range(12 * 25)]
    end = candles[-1].ts + 300
    candles += [Candle(end + 300 * k, 100.0 + k / 2, 100.6 + k / 2, 99.9 + k / 2, 100.5 + k / 2, 1.0) for k in range(12)]
    candles.append(Candle(end + 3600, 106.0, 106.2, 105.8, 106.0, 1.0))           # heure suivante, en cours
    trades = sl.donchian_day(candles, "gold")
    assert len(trades) == 1 and trades[0].reason == "fin des données"

def test_live_signals_stop_new_entries_after_end_but_still_send_the_exit(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from trading_bot import engine as engmod
    from trading_bot.config import load_config
    from trading_bot.storage import Store
    sent = []
    monkeypatch.setattr(engmod, "notify", lambda text, **k: sent.append(text))
    cfg = load_config()
    eng = engmod.Engine(cfg)
    eng.store = Store(tmp_path)
    since, end = datetime(2026, 10, 8, 7, 30, tzinfo=timezone.utc), datetime(2026, 10, 13, 19, 30, tzinfo=timezone.utc)
    t0 = int(datetime(2026, 10, 13, 18, 0, tzinfo=timezone.utc).timestamp())
    known = {"entry_ts": t0, "direction": "short", "entry": 4000.0, "risk": 10.0, "stop": 4010.0, "status": "closed",
             "reason": "heure", "exit_ts": t0 + 7200, "exit": 3990.0, "r_topstep": 0.98,
             "notified_entry": "2026-10-13T18:10:00Z", "micros": 2, "close_at": t0 + 7200}
    new = {"entry_ts": t0 + 86_400, "direction": "long", "entry": 4000.0, "risk": 10.0, "stop": 3990.0, "status": "open",
           "reason": None, "exit_ts": None, "exit": None, "r_topstep": None}
    eng._live_signals("donchian_day:gold", cfg.assets["gold"], [known, new], since, end + timedelta(days=1), end)
    assert len(sent) == 1 and "SORTIE" in sent[0] and not new.get("notified_entry")
