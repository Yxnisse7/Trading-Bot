"""Poche offensive : actions halal choisies par une règle testée (momentum), pas par intuition.

Univers : les entreprises de l'ETF iShares MSCI World Islamic (déjà filtrées charia par MSCI),
les 150 plus grosses. Chaque semaine :
  - composition de l'ETF (fichier public d'iShares ; la dernière composition connue est gardée) ;
  - historique mensuel de chaque action (Yahoo), converti en euros ;
  - règle « momentum 12-1 » : hausse sur 12 mois sans le dernier mois (effet documenté depuis les
    années 1990), avec un filtre de tendance (prix au-dessus de sa moyenne sur 10 mois).
    Les 10 meilleures forment la poche, 3 au plus par secteur ; une action détenue n'est remplacée
    que si elle sort du top 20 ou perd sa tendance (moins d'allers-retours, moins de frais) ;
  - backtest de la règle, mois par mois, contre l'ETF Monde islamique, frais de rotation compris.
    Biais connu : l'univers est la composition d'aujourd'hui (les entreprises sorties de l'indice
    ne sont pas rejouées), ce qui flatte un peu le résultat : c'est affiché.
"""
from __future__ import annotations

import csv
import io
import json
import logging
import math
import re
import statistics as st
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from .config import ROOT_DIR
from .models import iso, parse_iso, utcnow
from .providers.http import ProviderError, get_text

log = logging.getLogger(__name__)

UNIVERSE_SIZE = 150
# Poche « pépites » : entreprises plus petites de l'indice (rangs 151 à 400), momentum récent (6 mois),
# 5 actions, 2 au plus par secteur, révision tous les 3 mois
PEPITES_FROM, PEPITES_TO, PEPITES_N, PEPITES_KEEP, PEPITES_CAP, PEPITES_LOOKBACK = 150, 400, 5, 10, 2, 6
REVISION_EVERY = 3
# Entreprises israéliennes exclues de la poche et des pépites (choix éthique de l'utilisateur) : pays du siège
# indiqué par iShares, plus les sociétés israéliennes connues cotées ou domiciliées ailleurs.
ISRAEL_NAMES = re.compile(r"\b(mobileye|check ?point|teva|nice ltd|wix|monday\.?com|elbit|amdocs|global-e|zim integrated|"
                          r"tower semiconductor|camtek|nova ltd|inmode|oddity|cyberark|solaredge|ormat|playtika|"
                          r"taboola|fiverr|lemonade|sapiens|radware|cellebrite|jfrog|riskified|similarweb)\b", re.I)


def is_israeli(h: dict[str, Any]) -> bool:
    return "israel" in (h.get("country") or "").lower() or bool(ISRAEL_NAMES.search(h.get("name") or ""))
TOP_N = 10
KEEP_RANK = 20
SECTOR_CAP = 3                  # au plus 3 actions d'un même secteur : la poche ne doit pas être un pari sur un seul thème
COST_PER_TURNOVER = 0.003       # 0,3 % par euro échangé (courtage, écart, change)
REFRESH_DAYS = 7

# Bourse (colonne « Exchange » d'iShares) → suffixe Yahoo, devise attendue
EXCHANGES = [
    (r"nasdaq(?!.*(nordic|omx|helsinki|stockholm|copenhagen))|new york|nyse(?! euronext)|cboe|bats|nyse arca", ""),
    (r"tokyo", ".T"), (r"london", ".L"), (r"xetra|deutsche b|frankfurt", ".DE"), (r"paris", ".PA"),
    (r"amsterdam", ".AS"), (r"brussels", ".BR"), (r"lisbon", ".LS"), (r"madrid|bolsa", ".MC"), (r"italiana|milan", ".MI"),
    (r"six swiss|swiss", ".SW"), (r"toronto", ".TO"), (r"asx|australian", ".AX"), (r"hong kong", ".HK"),
    (r"copenhagen", ".CO"), (r"stockholm|nasdaq omx nordic", ".ST"), (r"helsinki", ".HE"), (r"oslo", ".OL"),
    (r"singapore", ".SI"), (r"tel aviv", ".TA"), (r"new zealand", ".NZ"), (r"wiener|vienna", ".VI"), (r"irish|dublin", ".IR"),
]
RULES = {"top_n": TOP_N, "keep_rank": KEEP_RANK, "cost": COST_PER_TURNOVER, "sector_cap": SECTOR_CAP, "modes": 1,
         "revision_every": REVISION_EVERY, "exclude_israel": True, "month_rule": 2, "pepites": [PEPITES_FROM, PEPITES_TO, PEPITES_N, PEPITES_KEEP, PEPITES_CAP, PEPITES_LOOKBACK]}
FX_PAIRS = {c: f"EUR{c}=X" for c in ("USD", "GBP", "JPY", "CHF", "CAD", "AUD", "DKK", "SEK", "NOK", "HKD", "SGD", "ILS", "NZD")}


def data_dir() -> Path:
    return ROOT_DIR / "data" / "invest"


# ------------------------------------------------------------------ univers
def yahoo_ticker(ticker: str, exchange: str) -> str | None:
    t = (ticker or "").strip().upper()
    if not t or t in ("-", "CASH"):
        return None
    suffix = None
    for pattern, suf in EXCHANGES:
        if re.search(pattern, exchange or "", re.I):
            suffix = suf
            break
    if suffix is None:
        return None
    t = re.sub(r"[ .]+", "-", t)
    if suffix == ".HK" and t.isdigit():
        t = t.zfill(4)
    if suffix == ".L" and t.endswith("-"):
        t = t[:-1]
    return t + suffix


def parse_holdings(text: str) -> list[dict[str, Any]]:
    """Fichier CSV d'iShares : quelques lignes d'en-tête, puis le tableau des positions."""
    lines = text.lstrip("\ufeff").replace("\xa0", " ").splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith("Ticker") or ln.startswith('"Ticker"')), None)
    if start is None:
        raise ProviderError("composition iShares : tableau introuvable")
    rows = []
    for r in csv.DictReader(io.StringIO("\n".join(lines[start:]))):
        if (r.get("Asset Class") or "").strip().lower() != "equity":
            continue
        try:
            weight = float((r.get("Weight (%)") or "0").replace(",", ""))
        except ValueError:
            continue
        y = yahoo_ticker(r.get("Ticker", ""), r.get("Exchange", ""))
        if not y:
            continue
        rows.append({"ticker": r.get("Ticker", "").strip(), "yahoo": y, "name": (r.get("Name") or "").strip().title(),
                     "sector": (r.get("Sector") or "").strip(), "country": (r.get("Location") or "").strip(),
                     "currency": (r.get("Market Currency") or "").strip(), "weight": weight})
    rows.sort(key=lambda x: -x["weight"])
    return rows


ISHARES_CSV = [
    "https://www.ishares.com/uk/individual/en/products/251394/fund/1506575576011.ajax?fileType=csv&fileName=ISWD_holdings&dataType=fund",
    "https://www.ishares.com/uk/professional/en/products/251394/fund/1506575576011.ajax?fileType=csv&fileName=ISWD_holdings&dataType=fund",
    "https://www.ishares.com/ch/individual/en/products/251394/fund/1495092304805.ajax?fileType=csv&fileName=ISWD_holdings&dataType=fund",
]
# secours : composition de l'ETF Invesco MSCI ACWI Islamic (même famille d'indices), en JSON
INVESCO_JSON = "https://dng-api.invesco.com/cache/v1/accounts/en_GB/shareclasses/IE000LFC57H7/holdings/fund?idType=isin"
YAHOO_SEARCH = "https://query2.finance.yahoo.com/v1/finance/search"
SECONDARY = {"FRA", "BER", "MUN", "STU", "DUS", "HAM", "GER", "EBS", "VIE", "IOB", "MEX", "BUE", "SAO", "PNK"}


def fetch_holdings() -> list[dict[str, Any]]:
    """Composition de l'ETF iShares MSCI World Islamic (CSV), sinon celle de l'Invesco MSCI ACWI Islamic."""
    last: Exception | None = None
    for url in ISHARES_CSV:
        text = ""
        try:
            text = get_text(url, timeout=30)
            rows = parse_holdings(text)
            if rows:
                return rows
        except ProviderError as exc:
            last = exc
            log.warning("composition iShares illisible (%s) : %s [%s]", url[:70], exc, re.sub(r"\s+", " ", text[:120]))
    try:
        rows = invesco_holdings()
        if rows:
            return rows
    except ProviderError as exc:
        last = exc
        log.warning("composition Invesco indisponible : %s", exc)
    raise ProviderError(f"composition de l'ETF indisponible : {last}")


def _find_rows(obj: Any) -> list[dict[str, Any]]:
    """Première liste de positions (dictionnaires avec un ISIN) dans une réponse JSON de forme inconnue."""
    if isinstance(obj, list):
        if obj and isinstance(obj[0], dict) and any(k.lower() == "isin" for k in obj[0]):
            return obj
        for x in obj:
            found = _find_rows(x)
            if found:
                return found
    elif isinstance(obj, dict):
        for v in obj.values():
            found = _find_rows(v)
            if found:
                return found
    return []


def isin_to_yahoo(isin: str) -> str | None:
    from .providers.http import get_json
    try:
        data = get_json(YAHOO_SEARCH, params={"q": isin, "quotesCount": 6, "newsCount": 0}, timeout=10, retries=2)
    except ProviderError:
        return None
    quotes = [q for q in data.get("quotes", []) if q.get("quoteType") == "EQUITY" and q.get("symbol")]
    main = [q for q in quotes if (q.get("exchange") or "").upper() not in SECONDARY]
    return (main or quotes or [{}])[0].get("symbol")


def invesco_holdings(pause: float = 0.1) -> list[dict[str, Any]]:
    from .providers.http import get_json
    data = get_json(INVESCO_JSON, timeout=30)
    rows = _find_rows(data)
    if not rows:
        raise ProviderError("réponse Invesco sans positions")
    out = []
    for r in rows:
        low = {k.lower(): v for k, v in r.items()}
        isin = str(low.get("isin") or "").strip()
        weight = low.get("weight") or low.get("percentageofnetassets") or low.get("percentage") or 0
        try:
            weight = float(str(weight).replace("%", "").replace(",", "."))
        except ValueError:
            weight = 0.0
        if len(isin) != 12:
            continue
        out.append({"ticker": isin, "isin": isin, "name": str(low.get("name") or low.get("issuername") or isin).title(),
                    "sector": str(low.get("sector") or low.get("gicssector") or ""), "country": str(low.get("country") or ""),
                    "currency": str(low.get("currency") or ""), "weight": weight})
    out.sort(key=lambda x: -x["weight"])
    mapped = []
    for h in out[:UNIVERSE_SIZE + 30]:
        y = isin_to_yahoo(h["isin"])
        if y:
            mapped.append({**h, "yahoo": y})
        if pause:
            time.sleep(pause)
    return mapped


# ------------------------------------------------------------------ séries
def to_eur_series(rows: list[tuple[int, float]], ccy: str, fx: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    from .invest import month_key
    factor, base = 1.0, ccy
    if ccy in ("GBp", "GBX"):
        factor, base = 0.01, "GBP"
    if ccy == "ILA":                       # agorot israéliens
        factor, base = 0.01, "ILS"
    out: dict[str, float] = {}
    for t, v in rows:
        m = month_key(t)
        if base == "EUR":
            out[m] = v * factor
        elif (fx.get(base) or {}).get(m):
            out[m] = v * factor / fx[base][m]
    return sorted(out.items())


def momentum_table(series: dict[str, list[tuple[str, float]]], month: str, lookback: int = 12) -> list[dict[str, Any]]:
    """Classement au mois `month` (fin de mois) : momentum `lookback`-1 (hausse sur `lookback` mois sans
    le dernier) et filtre de tendance 10 mois."""
    out = []
    for key, s in series.items():
        idx = {m: i for i, (m, _) in enumerate(s)}
        i = idx.get(month)
        if i is None or i < max(12, lookback):
            continue
        vals = [v for _, v in s]
        mom = vals[i - 1] / vals[i - lookback] - 1
        sma = sum(vals[i - 9: i + 1]) / 10
        out.append({"key": key, "mom": mom, "trend": vals[i] > sma, "r1m": vals[i] / vals[i - 1] - 1})
    out.sort(key=lambda x: -x["mom"])
    for rank, row in enumerate(out, 1):
        row["rank"] = rank
    return out


def select(table: list[dict[str, Any]], held: list[str], n: int = TOP_N, keep_rank: int = KEEP_RANK,
           sectors: dict[str, str] | None = None, cap: int = SECTOR_CAP,
           exclude: Callable[[dict[str, Any]], bool] | None = None,
           too_close: Callable[[str, list[str]], bool] | None = None) -> list[str]:
    """Garde les actions détenues encore dans le top `keep_rank` avec leur tendance, complète par les meilleures,
    sans dépasser `cap` actions d'un même secteur. Variantes testées (essai 6) : `exclude(ligne)` écarte une
    action (anti-krach), `too_close(clé, retenues)` saute une action trop corrélée à celles déjà retenues."""
    sectors = sectors or {}
    by = {r["key"]: r for r in table}
    kept: list[str] = []
    count: dict[str, int] = {}

    def add(k: str) -> None:
        sec = sectors.get(k, "")
        if sec and count.get(sec, 0) >= cap:
            return
        if exclude and exclude(by[k]):
            return
        if too_close and kept and too_close(k, kept):
            return
        kept.append(k)
        if sec:
            count[sec] = count.get(sec, 0) + 1

    for k in sorted((k for k in held if k in by and by[k]["rank"] <= keep_rank and by[k]["trend"]), key=lambda k: by[k]["rank"]):
        add(k)
    for r in table:
        if len(kept) >= n:
            break
        if r["trend"] and r["key"] not in kept:
            add(r["key"])
    return kept[:n]


def backtest(series: dict[str, list[tuple[str, float]]], bench: list[tuple[str, float]] | None,
             n: int = TOP_N, sectors: dict[str, str] | None = None, every: int = 1, lookback: int = 12,
             keep_rank: int = KEEP_RANK, cap: int = SECTOR_CAP,
             exclude: Callable[[dict[str, Any]], bool] | None = None,
             close_at: Callable[[str], Callable[[str, list[str]], bool]] | None = None) -> dict[str, Any] | None:
    """Rejoue la règle : révision tous les `every` mois (entre deux, on garde les mêmes), poche
    équipondérée à chaque révision, rendement du mois suivant, frais de rotation.
    `close_at(mois)` fournit le test de corrélation connu à ce mois (variante de l'essai 6)."""
    months = sorted({m for s in series.values() for m, _ in s})
    maps = {k: dict(s) for k, s in series.items()}
    bmap = dict(bench or [])
    held: list[str] = []
    value, bvalue, curve, rows = 1.0, 1.0, [], []
    months_done: list[str] = []
    for a, b in zip(months, months[1:]):
        table = momentum_table(series, a, lookback)
        if len(table) < 3 * n:
            continue
        step = len(rows)
        new = (select(table, held, n, keep_rank, sectors=sectors, cap=cap, exclude=exclude,
                      too_close=close_at(a) if close_at else None)
               if (not held or step % every == 0) else held)
        if not new:
            continue
        turnover = len(set(new) - set(held)) / n if held else 1.0
        rets = [maps[k][b] / maps[k][a] - 1 for k in new if b in maps[k] and a in maps[k]]
        if not rets:
            continue
        r = sum(rets) / len(rets) - turnover * 2 * COST_PER_TURNOVER
        br = bmap[b] / bmap[a] - 1 if a in bmap and b in bmap else None
        value *= 1 + r
        if br is not None:
            bvalue *= 1 + br
        held = new
        if not curve:
            curve.append((a, 1.0, 1.0))
        curve.append((b, value, bvalue))
        rows.append((r, br, turnover))
        months_done.append(b)
    if len(rows) < 24:
        return None
    rs = [r for r, _, _ in rows]
    brs = [br for _, br, _ in rows if br is not None]
    years = len(rows) / 12

    def dd(vals):
        peak, worst = 0.0, 0.0
        for v in vals:
            peak = max(peak, v)
            worst = min(worst, v / peak - 1)
        return worst

    def roll12(vals):
        return [vals[i + 12] / vals[i] - 1 for i in range(len(vals) - 12)]

    pv, bv = [c[1] for c in curve], [c[2] for c in curve]
    p12, b12 = roll12(pv), roll12(bv)
    return {
        "start": curve[0][0], "end": curve[-1][0], "months": len(rows),
        "cagr": value ** (1 / years) - 1, "bench_cagr": bvalue ** (1 / years) - 1 if brs else None,
        "vol": st.pstdev(rs) * math.sqrt(12), "bench_vol": st.pstdev(brs) * math.sqrt(12) if len(brs) > 2 else None,
        "max_dd": dd(pv), "bench_max_dd": dd(bv) if brs else None,
        "beat_months": sum(1 for r, br, _ in rows if br is not None and r > br) / max(1, len(brs)),
        "beat_12m": sum(1 for x, y in zip(p12, b12) if x > y) / max(1, len(p12)),
        "worst_12m": min(p12) if p12 else None, "best_12m": max(p12) if p12 else None,
        "bench_worst_12m": min(b12) if b12 else None,
        "turnover": sum(t for _, _, t in rows) / len(rows),
        "curve": [[m, round(v, 4), round(b, 4)] for m, v, b in curve],
        "returns": [[m, round(r, 6), round(t, 4)] for m, (r, _, t) in zip(months_done, rows)],
    }



# ------------------------------------------------------------------ modes de révision (avec vos montants)
MODES = {
    "mensuelle": "Révision chaque mois : une action sortie du top 20 (ou sans tendance) est vendue et remplacée",
    "trimestrielle": "Révision tous les 3 mois (janvier, avril, juillet, octobre) ; entre deux, on garde les mêmes",
    "sans_vente": "Jamais de vente : chaque versement va aux meilleures actions du moment, les anciennes restent",
}
SIM_INIT, SIM_MONTHLY, SIM_FEE, SIM_TAX = 200.0, 20.0, 1.0, 0.314


def simulate_modes(series: dict[str, list[tuple[str, float]]], bench: list[tuple[str, float]] | None,
                   sectors: dict[str, str] | None = None, init: float = SIM_INIT, monthly: float = SIM_MONTHLY,
                   fee: float = SIM_FEE, tax: float = SIM_TAX, n: int = TOP_N) -> dict[str, Any] | None:
    """Rejoue les trois modes avec de vrais montants : versement initial puis mensuel, achats en plan
    d'investissement (gratuits), 1 € par vente, impôt sur chaque vente en gain (sans compensation des
    pertes : prudent). L'ETF Monde islamique reçoit les mêmes versements, pour comparer."""
    months = sorted({m for s in series.values() for m, _ in s})
    maps = {k: dict(s) for k, s in series.items()}
    bmap = dict(bench or [])
    steps = [(a, b) for a, b in zip(months, months[1:]) if len(momentum_table(series, a)) >= 3 * n]
    if len(steps) < 24:
        return None

    def run(mode: str) -> dict[str, Any]:
        pos: dict[str, dict[str, float]] = {}          # action -> {"value", "cost"}
        invested = sales = fees = taxes = 0.0
        idx, peak, worst, prev_unit = 1.0, 1.0, 0.0, None
        for i, (a, b) in enumerate(steps):
            table = momentum_table(series, a)
            held = [k for k in pos if pos[k]["value"] > 0]
            if mode == "sans_vente":
                picks = select(table, [], n, sectors=sectors)
            elif mode == "trimestrielle" and i % 3 and held:
                picks = held
            else:
                picks = select(table, held, n, sectors=sectors)
            cash = init if i == 0 else monthly
            invested += cash
            if mode != "sans_vente":
                for k in [k for k in held if k not in picks]:
                    p = pos.pop(k)
                    gain = p["value"] - p["cost"]
                    t = max(0.0, gain) * tax
                    cash += p["value"] - fee - t
                    sales += 1
                    fees += fee
                    taxes += t
            # versement : d'abord aux actions retenues les plus en retard (parts égales visées)
            if picks:
                target = (sum(pos[k]["value"] for k in pos if k in picks) + cash) / len(picks)
                need = {k: max(0.0, target - pos.get(k, {"value": 0.0})["value"]) for k in picks}
                tot = sum(need.values())
                for k in picks:
                    add = cash * (need[k] / tot if tot else 1 / len(picks))
                    if add > 0:
                        q = pos.setdefault(k, {"value": 0.0, "cost": 0.0})
                        q["value"] += add
                        q["cost"] += add
            before = sum(p["value"] for p in pos.values())
            for k, p in pos.items():
                if a in maps[k] and b in maps[k]:
                    p["value"] *= maps[k][b] / maps[k][a]
            after = sum(p["value"] for p in pos.values())
            if before > 0:
                idx *= after / before
                peak = max(peak, idx)
                worst = min(worst, idx / peak - 1)
        value = sum(p["value"] for p in pos.values())
        latent = sum(max(0.0, p["value"] - p["cost"]) for p in pos.values())
        years = len(steps) / 12
        return {"label": MODES[mode], "value": round(value, 2), "invested": round(invested, 2),
                "net_if_sold": round(value - latent * tax - fee * len(pos), 2), "sales": int(sales),
                "fees": round(fees, 2), "taxes": round(taxes, 2), "lines": len(pos),
                "twr": idx ** (1 / years) - 1, "max_dd": worst}

    out = {m: run(m) for m in MODES}
    # l'ETF avec les mêmes versements, jamais vendu
    v = cost = 0.0
    idx, peak, worst = 1.0, 1.0, 0.0
    for i, (a, b) in enumerate(steps):
        c = init if i == 0 else monthly
        v += c
        cost += c
        if a in bmap and b in bmap:
            r = bmap[b] / bmap[a]
            v *= r
            idx *= r
            peak = max(peak, idx)
            worst = min(worst, idx / peak - 1)
    years = len(steps) / 12
    out["etf"] = {"label": "ETF Monde islamique, mêmes versements, jamais vendu", "value": round(v, 2),
                  "invested": round(cost, 2), "net_if_sold": round(v - max(0.0, v - cost) * tax - fee, 2),
                  "sales": 0, "fees": 0.0, "taxes": 0.0, "lines": 1, "twr": idx ** (1 / years) - 1, "max_dd": worst}
    return {"start": steps[0][0], "end": steps[-1][1], "months": len(steps), "init": init, "monthly": monthly,
            "fee": fee, "tax": tax, "modes": out}


# ------------------------------------------------------------------ assemblage
def last_common_month(series: dict[str, list[tuple[str, float]]]) -> str:
    """Mois de classement : le dernier mois de la majorité des actions (médiane sur toutes les séries, pas
    sur les mois distincts : quelques historiques arrêtés plus tôt ne doivent pas faire reculer le classement)."""
    return st.median_low(sorted(s[-1][0] for s in series.values()))


def load_universe(universe: list[dict[str, Any]], fetch_monthly: Callable, pause: float = 0.15
                  ) -> tuple[dict[str, list[tuple[str, float]]], dict[str, dict[str, Any]], list[str]]:
    """Historique mensuel en euros de chaque action (6 ans au plus, 14 mois au moins pour pouvoir classer)."""
    from .invest import month_key
    fx: dict[str, dict[str, float]] = {}
    for ccy, sym in FX_PAIRS.items():
        try:
            rows, _ = fetch_monthly(sym)
            fx[ccy] = {month_key(t): v for t, v in rows}
        except ProviderError:
            continue
    series, meta, missing = {}, {}, []
    for h in universe:
        try:
            rows, ccy = fetch_monthly(h["yahoo"])
        except ProviderError:
            missing.append(h["yahoo"])
            continue
        s = to_eur_series(rows, ccy, fx)[-73:]
        if len(s) >= 14:
            series[h["yahoo"]] = s
            meta[h["yahoo"]] = h
        else:
            missing.append(h["yahoo"])
        if pause:
            time.sleep(pause)
    return series, meta, missing


def build(bench: list[tuple[str, float]] | None, now: datetime | None = None,
          fetch_monthly: Callable | None = None, holdings_fn: Callable = fetch_holdings,
          cache_dir: Path | None = None, force: bool = False, pause: float = 0.15) -> dict[str, Any] | None:
    """Section « actions » des données d'investissement ; recalculée au plus une fois par semaine."""
    from .invest import fetch_monthly as default_fetch, month_key
    fetch_monthly = fetch_monthly or default_fetch
    now = now or utcnow()
    cdir = cache_dir or data_dir()
    cache_file = cdir / "stocks_cache.json"
    cache: dict[str, Any] = {}
    try:
        cache = json.loads(cache_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    fresh = cache.get("updated_at") and now - parse_iso(cache["updated_at"]) < timedelta(days=REFRESH_DAYS)
    same_rules = (cache.get("result") or {}).get("rules") == RULES
    if fresh and same_rules and not force and cache.get("result"):
        return cache["result"]

    holdings, source = None, "composition de l'ETF"
    try:
        holdings = holdings_fn()
        source = "iShares MSCI World Islamic" if holdings and holdings[0].get("isin") is None else "Invesco MSCI ACWI Islamic"
    except ProviderError as exc:
        log.warning("composition de l'ETF indisponible : %s", exc)
    if not holdings:
        holdings, source = cache.get("holdings"), "dernière composition connue"
    if not holdings:
        return cache.get("result")
    excluded = [h for h in holdings if is_israeli(h)]
    israel_weight = round(sum(h.get("weight") or 0 for h in excluded), 2)
    universe = [h for h in holdings if not is_israeli(h)][:PEPITES_TO]

    series, meta, missing = load_universe(universe, fetch_monthly, pause)
    big_keys = [h["yahoo"] for h in universe[:UNIVERSE_SIZE]]
    small_keys = [h["yahoo"] for h in universe[PEPITES_FROM:PEPITES_TO]]
    all_series = series
    series = {k: all_series[k] for k in big_keys if k in all_series}
    small = {k: all_series[k] for k in small_keys if k in all_series}
    if len(series) < 3 * TOP_N:
        log.warning("poche actions : trop peu d'historiques (%d)", len(series))
        return cache.get("result")

    # mois de classement : celui de la majorité des actions (le momentum saute de toute façon le dernier mois)
    month = last_common_month(series)
    table = momentum_table(series, month)
    sectors = {k: meta[k].get("sector", "") for k in series}
    picks = select(table, [], TOP_N, sectors=sectors)
    by = {r["key"]: r for r in table}

    def row(k):
        h, r = meta[k], by.get(k, {})
        return {"yahoo": k, "name": h["name"], "sector": h["sector"], "country": h["country"], "index_weight": h["weight"],
                "price_eur": round(series[k][-1][1], 4), "mom": round(r.get("mom", 0), 4), "r1m": round(r.get("r1m", 0), 4),
                "trend": bool(r.get("trend")), "rank": r.get("rank")}

    pepites = None
    if len(small) >= 3 * PEPITES_N:
        ptable = momentum_table(small, month, PEPITES_LOOKBACK)
        psec = {k: meta[k].get("sector", "") for k in small}
        ppicks = select(ptable, [], PEPITES_N, PEPITES_KEEP, sectors=psec, cap=PEPITES_CAP)
        pby = {r["key"]: r for r in ptable}

        def prow(k):
            h, r = meta[k], pby.get(k, {})
            return {"yahoo": k, "name": h["name"], "sector": h["sector"], "country": h["country"],
                    "price_eur": round(small[k][-1][1], 4), "mom": round(r.get("mom", 0), 4),
                    "r1m": round(r.get("r1m", 0), 4), "trend": bool(r.get("trend")), "rank": r.get("rank")}
        pepites = {"universe_n": len(small_keys), "priced_n": len(small), "picks": [prow(k) for k in ppicks],
                   "keep": [r["key"] for r in ptable if r["rank"] <= PEPITES_KEEP and r["trend"]],
                   "rules": {"top_n": PEPITES_N, "keep_rank": PEPITES_KEEP, "sector_cap": PEPITES_CAP,
                             "lookback": PEPITES_LOOKBACK, "from": PEPITES_FROM + 1, "to": PEPITES_TO},
                   "backtest": backtest(small, bench, PEPITES_N, psec, every=REVISION_EVERY, lookback=PEPITES_LOOKBACK,
                                        keep_rank=PEPITES_KEEP, cap=PEPITES_CAP)}

    result = {
        "updated_at": iso(now), "source": source, "universe_n": min(len(universe), UNIVERSE_SIZE), "priced_n": len(series),
        "missing": missing[:40], "month": month,
        "excluded": [{"name": h["name"], "country": h.get("country"), "weight": h.get("weight")} for h in excluded],
        "israel_weight": israel_weight,
        "rules": RULES,
        "picks": [row(k) for k in picks],
        "ranked": [row(r["key"]) for r in table[:40]],
        "keep": [r["key"] for r in table if r["rank"] <= KEEP_RANK and r["trend"]],
        "prices": {k: {"name": meta[k]["name"], "price_eur": round(s[-1][1], 4), "pocket": "pepites" if k in small else "main"}
                   for k, s in all_series.items()},
        "backtest": backtest(series, bench, sectors=sectors, every=REVISION_EVERY),
        "backtest_monthly": backtest(series, bench, sectors=sectors),
        "pepites": pepites,
        "modes": simulate_modes(series, bench, sectors=sectors),
    }
    cdir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps({"updated_at": iso(now), "holdings": holdings, "result": result},
                                     ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return result
