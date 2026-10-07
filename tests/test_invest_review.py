"""Revue de la stratégie halal (essai 6) : témoins, variantes, risque du portefeuille, contrôle AAOIFI."""
import math

from trading_bot import halal_stocks as hs
from trading_bot import invest_review as ir
from trading_bot.invest import month_key

from test_halal_stocks import _stock
from test_invest import NOW, _months


def _series(n_stocks=40, n_months=72):
    return {f"S{k}": [(month_key(t), v) for t, v in _stock(n_months, 0.0008 * k - 0.01)] for k in range(n_stocks)}


def test_stats_measure_drawdown_and_halves_split_the_period():
    s = ir.stats_of([0.1] * 6 + [-0.5] + [0.0] * 5)
    assert round(s["max_dd"], 4) == -0.5 and s["months"] == 12
    dated = [(f"2020-{m:02d}", 0.01) for m in range(1, 13)] + [(f"2021-{m:02d}", -0.01) for m in range(1, 13)]
    first, second = ir.halves(dated)
    assert first["cagr"] > 0 > second["cagr"]


def test_selection_variants_skip_crashed_and_correlated_stocks():
    table = [{"key": k, "rank": i + 1, "trend": True, "r1m": -0.30 if k == "A" else 0.01, "mom": 1 - i / 10}
             for i, k in enumerate("ABCDE")]
    assert hs.select(table, [], 3) == ["A", "B", "C"]
    assert hs.select(table, [], 3, exclude=lambda r: r["r1m"] <= ir.CRASH) == ["B", "C", "D"]
    twins = {"B": "C"}
    assert hs.select(table, [], 3, too_close=lambda k, kept: any(twins.get(j) == k for j in kept)) == ["A", "B", "D"]


def test_correlation_test_only_uses_known_months():
    months = [month_key(t) for t in _months(40)]
    a = [(m, 100 * (1 + 0.05 * math.sin(i))) for i, m in enumerate(months)]
    b = [(m, 50 * (1 + 0.05 * math.sin(i))) for i, m in enumerate(months)]           # même mouvement
    c = [(m, 100 * (1 + 0.05 * math.cos(i * 2.3))) for i, m in enumerate(months)]
    close = ir.correlation_test({"A": a, "B": b, "C": c})(months[30])
    assert close("B", ["A"]) and not close("C", ["A"])


def test_witnesses_use_the_same_months_and_costs_as_the_rule():
    series = _series()
    sectors = {k: f"Secteur {int(k[1:]) % 5}" for k in series}
    base = hs.backtest(series, None, sectors=sectors, every=3)
    months = [m for m, _, _ in base["returns"]]
    ew = ir.equal_weight(series, months)
    assert [m for m, _ in ew] == months
    runs = ir.random_runs(series, base["returns"], 10, draws=5)
    assert len(runs) == 5 and all([m for m, _ in run] == months for run in runs)


def test_review_pocket_reports_edge_against_witnesses_and_judges_variants():
    series = _series()
    sectors = {k: f"Secteur {int(k[1:]) % 5}" for k in series}
    r = ir.review_pocket(series, None, sectors, 10, 12, 20, 3, draws=30)
    assert r["rule"]["cagr"] > r["equal_weight"]["cagr"]           # les meilleures tendances gagnent ici
    assert r["random"]["rule_beats_share"] >= 0.9 and r["edge_proven"]
    assert set(r["variants"]) == {"anti_krach", "correlation"}
    assert all(isinstance(v["adopt"], bool) for v in r["variants"].values())


def test_portfolio_risk_mixes_etf_pocket_and_bitcoin_in_euros():
    months = [month_key(t) for t in _months(48)]
    prod = {k: [(m, 100 * (1.01 + 0.002 * j) ** i) for i, m in enumerate(months)]
            for j, k in enumerate(["monde", "emergents", "usa", "or", "bitcoin"])}
    rets = [(m, 0.02) for m in months[1:]]
    model = {"monde": 0.7, "emergents": 0.15, "usa": 0.1, "or": 0.05}
    risk = ir.portfolio_risk(prod, rets, rets, model)
    assert abs(sum(risk["weights"].values()) - 1) < 1e-9 and risk["weights"]["pocket"] == 0.2
    assert risk["sim"]["paid"] == 1000 + 200 * (len(months) - 2)
    assert risk["portfolio"]["cagr"] > 0
    assert ir.portfolio_risk(prod, None, None, model, {"pocket": 0, "pepites": 0, "bitcoin": 0})["weights"]["bitcoin"] == 0


def test_aaoifi_ratios_remove_leases_and_flag_missing_or_mixed_data():
    def f(**kw):
        return {k: {"value": v, "date": "2025-12-31", "ccy": "USD"} for k, v in kw.items()}
    ok = ir.aaoifi(f(trailingMarketCap=1000, annualTotalDebt=350, annualCapitalLeaseObligations=100,
                     annualCashCashEquivalentsAndShortTermInvestments=200, annualTotalRevenue=500, annualInterestIncome=10))
    assert ok["verdict"] == "conforme" and round(ok["debt"], 2) == 0.25 and round(ok["purification"], 3) == 0.02
    bad = ir.aaoifi(f(trailingMarketCap=1000, annualTotalDebt=400, annualCashCashEquivalentsAndShortTermInvestments=50,
                      annualTotalRevenue=500, annualInterestIncome=1))
    assert bad["verdict"] == "non conforme AAOIFI" and bad["purification"] is None
    assert ir.aaoifi(f(trailingMarketCap=1000))["verdict"] == "données manquantes"
    mixed = f(trailingMarketCap=1000, annualTotalDebt=10, annualCashCashEquivalentsAndShortTermInvestments=10,
              annualTotalRevenue=500)
    mixed["annualTotalRevenue"]["ccy"] = "JPY"
    assert ir.aaoifi(mixed)["verdict"].startswith("à vérifier")


def test_fundamentals_parse_yahoo_timeseries(monkeypatch):
    payload = {"timeseries": {"result": [
        {"meta": {"type": ["annualTotalDebt"]}, "annualTotalDebt": [
            {"asOfDate": "2024-12-31", "currencyCode": "USD", "reportedValue": {"raw": 5}},
            {"asOfDate": "2025-12-31", "currencyCode": "USD", "reportedValue": {"raw": 7}}]},
        {"meta": {"type": ["trailingMarketCap"]}, "trailingMarketCap": [None]}]}}
    monkeypatch.setattr(ir, "get_json", lambda *a, **k: payload)
    out = ir.fetch_fundamentals("AAA", NOW)
    assert out == {"annualTotalDebt": {"value": 7.0, "date": "2025-12-31", "ccy": "USD"}}


def test_full_run_with_fake_data(tmp_path, monkeypatch):
    monkeypatch.setattr(hs, "UNIVERSE_SIZE", 40)
    monkeypatch.setattr(hs, "PEPITES_FROM", 40)
    monkeypatch.setattr(hs, "PEPITES_TO", 70)

    def fetch(sym):
        if sym.startswith("EUR"):
            return [(t, 1.0) for t in _months(72)], "USD"
        if sym.startswith("S") and sym[1:].isdigit():
            k = int(sym[1:])
            return _stock(72, 0.0008 * (k % 40) - 0.01), "USD"
        return _stock(150, 0.006), "EUR"

    holdings = [{"ticker": f"S{k}", "yahoo": f"S{k}", "name": f"Société {k}", "sector": f"Secteur {k % 6}",
                 "country": "US", "currency": "USD", "weight": 100 - k} for k in range(70)]
    fund = {"trailingMarketCap": {"value": 1000, "ccy": "USD"}, "annualTotalDebt": {"value": 10, "ccy": "USD"},
            "annualCashCashEquivalentsAndShortTermInvestments": {"value": 10, "ccy": "USD"},
            "annualTotalRevenue": {"value": 100, "ccy": "USD"}, "annualInterestIncome": {"value": 1, "ccy": "USD"}}
    res = ir.run(NOW, fetch_monthly=fetch, holdings_fn=lambda: holdings, fundamentals=lambda s: fund, draws=10, pause=0)
    assert res["pocket"] and res["pepites"] and res["risk"]["site"] and res["risk"]["etf_only"]
    assert len(res["current"]["picks"]) == 10 and len(res["current"]["pepites"]) == 5
    assert all(v["verdict"] == "conforme" for v in res["current"]["aaoifi"].values())
    ir.publish(res, tmp_path / "d", tmp_path / "docs")
    assert (tmp_path / "docs" / "review.json").exists()
