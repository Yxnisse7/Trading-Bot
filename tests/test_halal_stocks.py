"""Poche actions halal : univers iShares, tickers Yahoo, momentum 12-1, sélection avec marge, backtest."""
import math
from datetime import datetime, timezone

from trading_bot import halal_stocks as hs

from test_invest import NOW, _months

CSV = '''iShares MSCI World Islamic UCITS ETF
Fund Holdings as of,"Sep 29, 2026"

Ticker,Name,Sector,Asset Class,Market Value,Weight (%),Notional Value,Shares,Price,Location,Exchange,Market Currency,FX Rate
"AAA","ALPHA CORP","Information Technology","Equity","1,000","5.10","1,000","10","100","United States","NASDAQ","USD","1"
"7203","TOYOTA MOTOR CORP","Consumer Discretionary","Equity","900","2.00","900","10","90","Japan","Tokyo Stock Exchange","JPY","150"
"NOVO B","NOVO NORDISK CLASS B","Health Care","Equity","800","3.00","800","10","80","Denmark","Omx Nordic Exchange Copenhagen A/S","DKK","7"
"700","TENCENT","Communication","Equity","700","1.00","700","10","70","China","Hong Kong Exchanges And Clearing Ltd","HKD","8"
"USD","USD CASH","Cash","Cash","100","0.50","100","100","1","United States","-","USD","1"
'''


def test_holdings_parsing_and_yahoo_tickers():
    rows = hs.parse_holdings(CSV)
    assert [r["yahoo"] for r in rows] == ["AAA", "NOVO-B.CO", "7203.T", "0700.HK"]        # triés par poids, sans liquidités
    assert rows[0]["name"] == "Alpha Corp" and rows[0]["weight"] == 5.1
    assert hs.yahoo_ticker("AZN", "London Stock Exchange") == "AZN.L"
    assert hs.yahoo_ticker("XYZ", "Bourse inconnue") is None


def _stock(n, growth):
    ts = _months(n)
    return [(m, 100 * math.exp(growth * i) * (1 + 0.02 * math.sin(i))) for i, m in enumerate(ts)]


def test_momentum_selection_keeps_holdings_within_the_buffer():
    from trading_bot.invest import month_key
    series = {f"S{k}": [(month_key(t), v) for t, v in _stock(40, 0.002 * k - 0.02)] for k in range(30)}
    month = series["S0"][-1][0]
    table = hs.momentum_table(series, month)
    assert table[0]["key"] == "S29" and table[0]["rank"] == 1
    picks = hs.select(table, [], 10)
    assert picks[0] == "S29" and len(picks) == 10 and all(table[[r["key"] for r in table].index(p)]["trend"] for p in picks)
    # S15 est détenue, classée entre 11 et 20 : gardée ; une action en baisse est remplacée
    held = ["S15", "S0"]
    kept = hs.select(table, held, 10)
    assert "S15" in kept and "S0" not in kept


def test_backtest_and_weekly_cache(tmp_path):
    calls = {"n": 0}

    def fetch(sym):
        calls["n"] += 1
        if sym.startswith("EUR"):
            return [(t, 1.0) for t in _months(72)], "USD"
        k = int(sym[1:].split(".")[0])
        return _stock(72, 0.001 * k - 0.01), "USD"

    holdings = [{"ticker": f"S{k}", "yahoo": f"S{k}", "name": f"Société {k}", "sector": f"Secteur {k % 5}", "country": "US",
                 "currency": "USD", "weight": 1.0} for k in range(40)]
    bench = [(m, v) for m, v in hs.to_eur_series(_stock(72, 0.008), "EUR", {})]
    res = hs.build(bench, NOW, fetch_monthly=fetch, holdings_fn=lambda: holdings, cache_dir=tmp_path, pause=0)
    assert res["priced_n"] == 40 and len(res["picks"]) == 10 and res["picks"][0]["yahoo"] == "S39"
    bt = res["backtest"]
    assert bt and bt["months"] >= 24 and bt["bench_cagr"] is not None and 0 <= bt["beat_12m"] <= 1
    modes = res["modes"]["modes"]
    assert set(modes) == {"mensuelle", "trimestrielle", "sans_vente", "etf"}
    assert modes["sans_vente"]["sales"] == 0 and modes["sans_vente"]["taxes"] == 0
    assert modes["trimestrielle"]["sales"] <= modes["mensuelle"]["sales"]
    assert all(abs(m["invested"] - modes["etf"]["invested"]) < 1e-6 for m in modes.values())
    n = calls["n"]
    again = hs.build(bench, NOW, fetch_monthly=fetch, holdings_fn=lambda: holdings, cache_dir=tmp_path, pause=0)
    assert again == res and calls["n"] == n                      # moins d'une semaine : cache, aucun appel


def test_invesco_fallback_maps_isin_to_yahoo(monkeypatch):
    from trading_bot.providers import http
    payload = {"effectiveDate": "2026-09-29", "holdings": [
        {"name": "ALPHA CORP", "isin": "US0000000001", "weight": 4.2, "currency": "USD"},
        {"name": "BETA AG", "isin": "DE0000000002", "weight": "1,5", "currency": "EUR"}]}
    search = {"US0000000001": {"quotes": [{"symbol": "ALP.F", "exchange": "FRA", "quoteType": "EQUITY"},
                                          {"symbol": "ALP", "exchange": "NMS", "quoteType": "EQUITY"}]},
              "DE0000000002": {"quotes": [{"symbol": "BET.DE", "exchange": "GER", "quoteType": "EQUITY"}]}}
    monkeypatch.setattr(http, "get_json", lambda url, params=None, **kw: payload if "invesco" in url else search[params["q"]])
    rows = hs.invesco_holdings(pause=0)
    assert [(r["yahoo"], r["weight"]) for r in rows] == [("ALP", 4.2), ("BET.DE", 1.5)]      # cotation principale d'abord


def test_sector_cap_limits_the_pocket_to_three_per_sector():
    table = [{"key": f"T{i}", "rank": i + 1, "trend": True, "mom": 1 - i / 100} for i in range(20)]
    sectors = {f"T{i}": ("Tech" if i < 8 else f"Autre{i}") for i in range(20)}
    picks = hs.select(table, [], 10, sectors=sectors)
    assert sum(1 for p in picks if sectors[p] == "Tech") == 3 and len(picks) == 10


def test_pepites_pocket_and_quarterly_reminder(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from trading_bot import invest
    monkeypatch.setattr(hs, "UNIVERSE_SIZE", 40)
    monkeypatch.setattr(hs, "PEPITES_FROM", 40)
    monkeypatch.setattr(hs, "PEPITES_TO", 70)

    def fetch(sym):
        if sym.startswith("EUR"):
            return [(t, 1.0) for t in _months(72)], "USD"
        k = int(sym[1:])
        return _stock(72, 0.0008 * (k % 40) - 0.01), "USD"

    holdings = [{"ticker": f"S{k}", "yahoo": f"S{k}", "name": f"Société {k}", "sector": f"Secteur {k % 6}",
                 "country": "US", "currency": "USD", "weight": 100 - k} for k in range(70)]
    bench = hs.to_eur_series(_stock(72, 0.008), "EUR", {})
    res = hs.build(bench, NOW, fetch_monthly=fetch, holdings_fn=lambda: holdings, cache_dir=tmp_path, pause=0)
    pep = res["pepites"]
    assert pep and len(pep["picks"]) == 5 and all(int(p["yahoo"][1:]) >= 40 for p in pep["picks"])
    assert res["backtest"] and res["backtest_monthly"]
    sectors = [p["sector"] for p in pep["picks"]]
    assert max(sectors.count(x) for x in sectors) <= 2
    # rappel : seulement en janvier, avril, juillet, octobre, une fois par trimestre
    data = {"stocks": res}
    sf = tmp_path / "state.json"
    assert invest.revision_reminder(data, datetime(2026, 9, 30, tzinfo=timezone.utc), sf) is None
    text = invest.revision_reminder(data, datetime(2026, 10, 1, tzinfo=timezone.utc), sf)
    assert text and "Révision trimestrielle" in text and "Pépites" in text
    assert invest.revision_reminder(data, datetime(2026, 10, 2, tzinfo=timezone.utc), sf) is None
    assert invest.next_revision(datetime(2026, 11, 5, tzinfo=timezone.utc)) == "2027-01"


def test_israeli_companies_are_excluded(tmp_path):
    assert hs.is_israeli({"name": "Check Point Software Technologies", "country": "United States"})
    assert hs.is_israeli({"name": "Bank Leumi", "country": "Israel"})
    assert not hs.is_israeli({"name": "Toyota Motor", "country": "Japan"})

    def fetch(sym):
        if sym.startswith("EUR"):
            return [(t, 1.0) for t in _months(72)], "USD"
        k = int(sym[1:])
        return _stock(72, 0.001 * k - 0.01), "USD"

    holdings = [{"ticker": f"S{k}", "yahoo": f"S{k}", "name": f"Société {k}", "sector": f"Secteur {k % 5}",
                 "country": "Israel" if k == 39 else "US", "currency": "USD", "weight": 1.0} for k in range(40)]
    res = hs.build([], NOW, fetch_monthly=fetch, holdings_fn=lambda: holdings, cache_dir=tmp_path, pause=0)
    assert "S39" not in res["prices"] and all(p["yahoo"] != "S39" for p in res["picks"])
    assert res["excluded"][0]["name"] == "Société 39" and res["israel_weight"] == 1.0


def test_ranking_month_follows_the_majority_not_stale_histories():
    series = {f"S{k}": [("2026-08", 1.0), ("2026-09", 1.0), ("2026-10", 1.0)] for k in range(10)}
    series.update({"OLD1": [("2026-06", 1.0)], "OLD2": [("2026-07", 1.0)], "OLD3": [("2026-05", 1.0)]})
    assert hs.last_common_month(series) == "2026-10"
