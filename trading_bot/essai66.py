"""Essai 66 : poche d'actions halal logeable dans un PEA (sièges UE/EEE). Règles dans HYPOTHESES.md.

    python -m trading_bot.essai66
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import halal_stocks as hs
from . import invest
from . import invest_review as rv
from .invest import month_key
from .providers.http import ProviderError

ROOT = Path(__file__).resolve().parent.parent
PEA_COUNTRIES = {"Germany", "France", "Italy", "Spain", "Netherlands", "Belgium", "Austria", "Portugal",
                 "Finland", "Sweden", "Denmark", "Norway"}
START = "2010-01"


def load(universe):
    fx = {}
    for ccy, sym in hs.FX_PAIRS.items():
        try:
            rows, _ = invest.fetch_monthly(sym)
            fx[ccy] = {month_key(t): v for t, v in rows}
        except ProviderError:
            continue
    series, meta, missing = {}, {}, []
    for h in universe:
        try:
            rows, ccy = invest.fetch_monthly(h["yahoo"])
        except ProviderError:
            missing.append(h["yahoo"])
            continue
        s = [x for x in hs.to_eur_series(rows, ccy, fx) if x[0] >= START]
        if len(s) >= 14:
            series[h["yahoo"]], meta[h["yahoo"]] = s, h
        else:
            missing.append(h["yahoo"])
        time.sleep(0.15)
    return series, meta, missing


def summary(r):
    if not r:
        return None
    keep = ("cagr", "vol", "max_dd", "worst_12m")
    return {"rule": {k: r["rule"].get(k) for k in keep}, "halves": [{k: h.get(k) for k in keep} if h else None
                                                                       for h in r["rule"]["halves"]],
            "equal_weight": {k: r["equal_weight"].get(k) for k in keep} if r["equal_weight"] else None,
            "ew_halves": [{k: h.get(k) for k in keep} if h else None for h in r["equal_weight"]["halves"]],
            "random": r["random"], "edge_proven": r["edge_proven"], "halves_ok": r["halves_ok"], "period": r["period"]}


def main() -> None:
    holdings = json.loads((hs.data_dir() / "stocks_cache.json").read_text(encoding="utf-8"))["holdings"]
    universe = [h for h in holdings if h.get("country") in PEA_COUNTRIES and not hs.is_israeli(h)]
    series, meta, missing = load(universe)
    sectors = {k: meta[k].get("sector", "") for k in series}
    products, _fx, _err = invest.load_series(invest.fetch_monthly)
    bench = [x for x in products.get("monde") or [] if x[0] >= START]
    out = {"universe": len(universe), "priced": len(series), "missing": missing,
           "names": {k: [meta[k]["name"], meta[k]["country"], meta[k]["sector"]] for k in series}}
    out["A"] = summary(rv.review_pocket(series, bench, sectors, 10, 12, 20, 3))
    out["B"] = summary(rv.review_pocket(series, bench, sectors, 5, 12, 10, 2))
    bt = hs.backtest(series, bench, 10, sectors, every=3)
    if bt:
        out["bench"] = {"cagr": bt["bench_cagr"], "max_dd": bt["bench_max_dd"], "worst_12m": bt["bench_worst_12m"],
                        "period": [bt["start"], bt["end"]]}
        out["A_curve_end"] = bt["curve"][-1]
    month = hs.last_common_month(series)
    picks = hs.select(hs.momentum_table(series, month), [], 10, sectors=sectors)
    out["picks_now"] = [[k, meta[k]["name"], meta[k]["country"]] for k in picks]
    (ROOT / "data" / "essai66.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "names"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
