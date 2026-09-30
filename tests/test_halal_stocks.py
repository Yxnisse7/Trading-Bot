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

    holdings = [{"ticker": f"S{k}", "yahoo": f"S{k}", "name": f"Société {k}", "sector": "Tech", "country": "US",
                 "currency": "USD", "weight": 1.0} for k in range(40)]
    bench = [(m, v) for m, v in hs.to_eur_series(_stock(72, 0.008), "EUR", {})]
    res = hs.build(bench, NOW, fetch_monthly=fetch, holdings_fn=lambda: holdings, cache_dir=tmp_path, pause=0)
    assert res["priced_n"] == 40 and len(res["picks"]) == 10 and res["picks"][0]["yahoo"] == "S39"
    bt = res["backtest"]
    assert bt and bt["months"] >= 24 and bt["bench_cagr"] is not None and 0 <= bt["beat_12m"] <= 1
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
