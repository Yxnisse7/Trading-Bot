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
