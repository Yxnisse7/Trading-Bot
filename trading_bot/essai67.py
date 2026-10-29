"""Essai 67 : poche PEA halal élargie (toutes les actions européennes, filtre AAOIFI). Règles dans HYPOTHESES.md.

    python -m trading_bot.essai67 /chemin/vers/europe_imi.csv
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from . import halal_stocks as hs
from . import invest
from . import invest_review as rv
from .essai66 import PEA_COUNTRIES, load, summary
from .providers.http import ProviderError

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_SECTORS = {"Financials", "Other"}
# alcool, tabac, jeux d'argent, armement, divertissement
EXCLUDED_NAMES = re.compile(
    r"heineken|carlsberg|pernod|remy cointreau|r[eé]my|campari|anheuser|ab inbev|royal unibrew|laurent[- ]perrier|"
    r"vranken|davide campari|tobacco|swedish match|scandinavian tobacco|imperial brands|evolution|flutter|lottomatica|"
    r"francaise des jeux|fdj|betsson|kindred|betsson|bet-at-home|kambi|ses\b|novomatic|rheinmetall|saab|leonardo|"
    r"thales|dassault aviation|hensoldt|kongsberg|renk|indra|fincantieri|kitron|nammo|cts eventim|universal music|"
    r"vivendi|banijay|prosiebensat|tf1|m6|mediaset|mfe|rtl group|embracer|ubisoft|cd projekt|paradox|stillfront|"
    r"modern times|mtg|nordic entertainment", re.I)


def dedup(rows):
    seen, out = set(), []
    for h in rows:
        root = re.sub(r"\b(class|cl|ser|series)?\s*[ab]\b|\b(pref|vz|ord|reg|non.?voting)\b", "", h["name"].lower())
        root = re.sub(r"[^a-z0-9]+", " ", root).strip()
        if root not in seen:
            seen.add(root)
            out.append(h)
    return out


def main(path: str) -> None:
    rows = hs.parse_holdings(Path(path).read_text(encoding="utf-8"))
    base = [h for h in rows if h["country"] in PEA_COUNTRIES and not hs.is_israeli(h)]
    activity = dedup([h for h in base if h["sector"] not in EXCLUDED_SECTORS and not EXCLUDED_NAMES.search(h["name"])])
    verdicts = {}
    for h in activity:
        try:
            verdicts[h["yahoo"]] = rv.aaoifi(rv.fetch_fundamentals(h["yahoo"]))
        except (ProviderError, ValueError, TypeError):
            verdicts[h["yahoo"]] = {"verdict": "données manquantes"}
        time.sleep(0.2)
    universe = [h for h in activity if verdicts[h["yahoo"]].get("verdict") == "conforme"]
    series, meta, missing = load(universe)
    sectors = {k: meta[k].get("sector", "") for k in series}
    products, _fx, _err = invest.load_series(invest.fetch_monthly)
    bench = [x for x in products.get("monde") or [] if x[0] >= "2010-01"]
    islamic = {h["name"].lower() for h in json.loads((hs.data_dir() / "stocks_cache.json").read_text(encoding="utf-8"))["holdings"]}
    out = {"pea_country": len(base), "after_activity": len(activity),
           "verdicts": {v: sum(1 for x in verdicts.values() if x.get("verdict") == v)
                        for v in {x.get("verdict") for x in verdicts.values()}},
           "universe": len(universe), "priced": len(series), "missing": missing,
           "names": {k: [meta[k]["name"], meta[k]["country"], meta[k]["sector"]] for k in series}}
    out["D"] = summary(rv.review_pocket(series, bench, sectors, 10, 12, 20, 3))
    month = hs.last_common_month(series)
    picks = hs.select(hs.momentum_table(series, month), [], 10, sectors=sectors)
    out["picks_now"] = [[k, meta[k]["name"], meta[k]["country"], meta[k]["name"].lower() in islamic] for k in picks]
    (ROOT / "data" / "essai67.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "names"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
