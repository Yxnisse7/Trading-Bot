"""Chances de réussir le Combine Topstep : séries de R, profils, témoin sans avantage, publication."""
import json
import shutil

import pytest

from trading_bot import topstep_odds as to
from trading_bot.models import Candle


def _sig(asset, entry, stop, gross_pct, day):
    return {"asset": asset, "entry": entry, "stop_loss": stop, "pnl_gross_pct": gross_pct,
            "created_at": f"2026-09-{day:02d}T14:00:00Z"}


def test_r_from_signal_removes_topstep_fees_in_points():
    s = _sig("nasdaq", 20000.0, 19990.0, 0.1, 1)              # +20 points pour 10 de risque
    fee, tick = to.FEES["nasdaq"]
    assert to.r_from_signal(s) == round((20 - (fee + tick) / 2.0) / 10, 4)
    assert to.r_from_signal({**s, "asset": "inconnu"}) is None
    assert to.r_from_signal({**s, "stop_loss": 20000.0}) is None


def test_r_from_account_uses_risk_of_balance_before_trade():
    rows = [{"closed_at": "2026-09-25T10:00:00Z", "pnl": 250.0, "balance_after": 50250.0},
            {"closed_at": "2026-09-24T10:00:00Z", "pnl": -250.0, "balance_after": 50000.0},
            {"closed_at": "2026-09-26T10:00:00Z", "pnl": None, "balance_after": None}]
    assert to.r_from_account(rows, 0.5) == [round(-250 / 251.25, 4), 1.0]


def test_witness_keeps_the_trades_but_removes_the_edge():
    sigs = [_sig("gold", 3000.0, 2990.0, 0.5 if k % 2 else -0.3, 1 + k % 20) for k in range(30)]
    base = to.backtest_profile({"gold": sigs})
    w = to.witness_profile(base)
    assert base["rSeries"] and abs(sum(w["rSeries"])) < 1e-6 * len(w["rSeries"]) + 1e-3
    assert w["tradesPerDay"] == base["tradesPerDay"] and to.backtest_profile({"gold": sigs[:5]}) is None


def test_build_donchian_keeps_closed_trades_in_r(monkeypatch):
    from trading_bot import strategies as sl
    candles = [Candle(1_700_000_000 + 300 * i, 1, 1, 1, 1) for i in range(5000)]
    fake = [sl.Trade("donchian_1h", "gold", "long", candles[10].ts, candles[20].ts, 100.0, 104.0, 2.0, "sortie"),
            sl.Trade("donchian_1h", "gold", "long", candles[30].ts, candles[-1].ts, 100.0, 101.0, 2.0, "fin des données")]
    monkeypatch.setitem(sl.RUNNERS_1H, "donchian_1h", lambda c, a: fake)
    d = to.build_donchian(candles)
    assert len(d["rSeries"]) == 1 and d["rSeries"][0] < 2.0 and d["tradesPerDay"] > 0


def test_build_and_publish_with_fake_engine(tmp_path):
    ddir = tmp_path / "data" / "topstep"
    ddir.mkdir(parents=True)
    sigs = {"nasdaq": [_sig("nasdaq", 20000.0, 19990.0, 0.1 if k % 3 else -0.06, 1 + k % 25) for k in range(40)]}
    (tmp_path / "data" / "backtest_trades.json").write_text(json.dumps(sigs))
    (ddir / "dashboard.json").write_text(json.dumps({"risk_pct": 0.5, "started_at": "2026-09-24T00:00:00Z", "trades": [
        {"closed_at": "2026-09-25T10:00:00Z", "pnl": 250.0, "balance_after": 50250.0}]}))
    seen = []

    def engine(profiles):
        seen.extend(p["key"] for p in profiles)
        return {"paths": 10, "seed": 42, "spec": {"fees": {"price": 49}}, "flags": ["bootstrap-resampling"],
                "profiles": [{"key": p["key"], "label": p["label"], "risks": [
                    {"risk": 250, "pass": 0.3, "fail": {"max-loss": 30, "abandoned": 10}}]} for p in profiles]}

    res = to.build(data_dir=ddir, engine=engine)
    assert seen == ["account", "backtest", "witness"]        # donchian absent, compte trop court mais gardé
    row = res["profiles"][1]
    assert row["stats"]["n"] == 40 and row["risks"][0]["fail"] == {"max-loss": 0.75, "abandoned": 0.25}
    to.publish(res, ddir, tmp_path / "docs")
    assert json.loads((tmp_path / "docs" / "odds.json").read_text())["fees"] == {"price": 49}


@pytest.mark.skipif(not shutil.which("node") or not (to.TOOL.parent / "node_modules").exists(),
                    reason="moteur node non installé")
def test_real_engine_separates_an_edge_from_chance():
    good = [1.5, -1.0, 1.5, -1.0, 1.5] * 30
    zero = [r - sum(good) / len(good) for r in good]
    out = to.run_engine([{"key": "g", "label": "g", "rSeries": good, "tradesPerDay": 3},
                         {"key": "z", "label": "z", "rSeries": zero, "tradesPerDay": 3}], risks=(250.0,), paths=2000)
    g, z = (p["risks"][0]["pass"] for p in out["profiles"])
    assert g > z + 0.3


def test_directory_keeps_only_rules_and_drops_excluded_countries():
    payload = {"data": {"propfirms": [
        {"propfirmId": "a", "name": "A", "countryIso2": "US", "productTypes": ["Futures"], "offers": [{"affiliateLink": "x"}],
         "challenges": [{"challengeId": "a-50k", "accountSize": 50000, "price": 99, "promo": "y"}]},
        {"propfirmId": "b", "name": "B", "countryIso2": "IL", "challenges": []}]}}
    firms, excluded = to.fetch_directory(lambda: payload)
    assert excluded == ["B"] and len(firms) == 1
    assert "offers" not in firms[0] and firms[0]["challenges"] == [{**{k: None for k in to.RULE_FIELDS},
                                                                   "challengeId": "a-50k", "accountSize": 50000, "price": 99}]


def test_build_firms_with_fake_engine(tmp_path):
    ddir = tmp_path / "data" / "topstep"
    ddir.mkdir(parents=True)
    sigs = {"gold": [_sig("gold", 3000.0, 2990.0, 0.5 if k % 2 else -0.3, 1 + k % 20) for k in range(30)]}
    (tmp_path / "data" / "backtest_trades.json").write_text(json.dumps(sigs))
    (ddir / to.DONCHIAN_FILE).write_text(json.dumps({"rSeries": [1.0, -1.0] * 10, "tradesPerDay": 0.5,
                                                     "period": ["2024-01-01", "2026-01-01"],
                                                     "holding": {"n": 20, "overnight": 12, "weekend": 3}}))
    seen = {}

    def engine(profiles, firms):
        seen["profiles"] = [p["key"] for p in profiles]
        seen["firms"] = [f["name"] for f in firms]
        return {"paths": 10, "challenges": [{"firm": "A"}], "errors": []}

    payload = {"data": {"propfirms": [{"name": "A", "countryIso2": "FR", "challenges": []},
                                      {"name": "B", "countryIso2": "il", "challenges": []}]}}
    res = to.build_firms(data_dir=ddir, fetch=lambda: payload, engine=engine)
    assert seen == {"profiles": ["donchian_gold", "backtest", "witness"], "firms": ["A"]}
    assert res["excluded"] == ["B"] and res["profiles"][0]["holding"]["overnight"] == 12
    assert [p["holds_overnight"] for p in res["profiles"]] == [True, False, False]


def test_holding_stats_counts_positions_kept_after_the_close():
    from datetime import datetime, timezone
    from trading_bot import strategies as sl
    ts = lambda s: int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())  # noqa: E731
    same_day = sl.Trade("donchian_1h", "gold", "long", ts("2026-10-06T14:00:00"), ts("2026-10-06T18:00:00"), 1, 1, 1, "x")
    overnight = sl.Trade("donchian_1h", "gold", "long", ts("2026-10-06T14:00:00"), ts("2026-10-07T15:00:00"), 1, 1, 1, "x")
    weekend = sl.Trade("donchian_1h", "gold", "long", ts("2026-10-09T14:00:00"), ts("2026-10-12T15:00:00"), 1, 1, 1, "x")
    assert to.holding_stats([same_day, overnight, weekend]) == {"n": 3, "overnight": 2, "weekend": 1}


@pytest.mark.skipif(not shutil.which("node") or not (to.TOOL.parent / "node_modules").exists(),
                    reason="moteur node non installé")
def test_real_firms_engine_adapts_directory_rows_and_overrides():
    firm = {"propfirmId": "ftmo", "name": "FTMO", "productTypes": ["CFD"], "currency": "eur", "challenges": [
        {"challengeId": "ftmo-normal-challenge-1-step-50k", "challengeName": "FTMO - Normal Challenge - 1-Step 50k",
         "accountSize": 50000, "steps": 1, "profitTarget": [10], "profitTargetIsPercent": True, "minTradingDays": 2,
         "dailyLoss": 3, "maxLoss": 10, "maxLossType": "Static", "lossIsPercent": True, "price": 90,
         "interval": "one time", "profitSplitPercent": 90, "payoutFrequency": "14 days", "overnightHolding": True,
         "weekendHolding": True}]}
    good = [1.5, -1.0, 1.5, -1.0, 1.5] * 30
    out = to.run_firms([{"key": "g", "label": "g", "rSeries": good, "tradesPerDay": 3}], [firm], risks=(250.0,), paths=500)
    names = {c["firm"]: c for c in out["challenges"]}
    assert set(names) == {"Topstep", "FTMO"} and not out["errors"]
    ftmo = names["FTMO"]
    assert ftmo["fees"]["price"] == 319 and ftmo["completed"] and ftmo["maxLoss"]["mode"] == "trailing-realized-eod"
    assert names["Topstep"]["overnight"] is False and 0 < ftmo["results"]["g"][0]["pass"] <= 1


def test_session_close_is_15h_chicago_and_blocks_entries_until_17h():
    from datetime import datetime, timezone
    from trading_bot import strategies as sl
    ts = lambda s: int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())  # noqa: E731
    # 7 octobre 2026 : Chicago en heure d'été (UTC−5) → 15:00 CT = 20:00 UTC
    assert sl.session_close_ts(ts("2026-10-07T14:00:00")) == ts("2026-10-07T20:00:00")
    assert sl.session_close_ts(ts("2026-10-07T20:00:00")) is None            # 15:00 CT : plus d'entrée
    assert sl.session_close_ts(ts("2026-10-07T23:00:00")) == ts("2026-10-08T20:00:00")   # 18:00 CT : séance suivante


def test_donchian_day_never_keeps_a_position_after_the_session():
    from trading_bot import strategies as sl
    from trading_bot.models import Candle
    t0 = 1_780_000_000 - 1_780_000_000 % 3600
    candles, px = [], 100.0
    for k in range(24 * 30 * 12):                       # 30 jours de bougies 5 min avec de longues tendances
        px += 0.05 if (k // 600) % 2 == 0 else -0.05
        candles.append(Candle(t0 + 300 * k, px, px + 0.1, px - 0.1, px))
    day = sl.donchian_day(candles, "gold")
    assert day
    closed = [t for t in day if t.reason != "fin des données"]
    assert to.holding_stats(closed)["overnight"] == 0
    assert any(t.reason == "heure" for t in closed)
    assert len(sl.donchian_1h(candles, "gold")) <= len(day) + 50       # même règle d'entrée


def test_intraday_gold_strategies_close_each_session():
    from trading_bot import strategies as sl
    from trading_bot.models import Candle
    t0 = 1_780_000_000 - 1_780_000_000 % 3600
    candles, px = [], 100.0
    for k in range(24 * 12 * 30):
        px += 0.05 if (k // 300) % 2 == 0 else -0.05
        candles.append(Candle(t0 + 300 * k, px, px + 0.1, px - 0.1, px))
    for fn, name in ((sl.donchian_15m_day, "donchian_15m_day"), (sl.donchian_30m_day, "donchian_30m_day")):
        tr = [t for t in fn(candles, "gold") if t.reason != "fin des données"]
        assert tr and {t.strategy for t in tr} == {name}
        assert to.holding_stats(tr)["overnight"] == 0


def test_comex_orb_trades_the_first_close_outside_the_8h20_range():
    from datetime import datetime, time
    from trading_bot import strategies as sl
    from trading_bot.models import Candle
    day = datetime(2026, 10, 6).date()
    t820 = int(datetime.combine(day, time(8, 20), sl.NY).timestamp())
    candles = []
    for k in range(-12, 120):
        ts = t820 + 300 * k
        if 0 <= k <= 5:
            o = c = 100.0
            hi, lo = 101.0, 99.0                      # range 99 → 101
        elif k == 8:
            o, c, hi, lo = 100.5, 101.5, 101.6, 100.4   # première clôture au-dessus : achat à 101,5
        else:
            o = c = 101.5 if k > 8 else 100.0
            hi, lo = c + 0.2, c - 0.2
        candles.append(Candle(ts, o, hi, lo, c))
    tr = sl.comex_orb(sl._Series(candles), "gold")
    assert len(tr) == 1 and tr[0].direction == "long" and tr[0].entry == 101.5 and tr[0].risk == 2.5
