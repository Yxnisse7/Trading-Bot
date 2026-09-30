"""Poche offensive : actions halal choisies par une règle testée (momentum), pas par intuition.

Univers : les entreprises de l'ETF iShares MSCI World Islamic (déjà filtrées charia par MSCI),
les 150 plus grosses. Chaque semaine :
  - composition de l'ETF (fichier public d'iShares ; la dernière composition connue est gardée) ;
  - historique mensuel de chaque action (Yahoo), converti en euros ;
  - règle « momentum 12-1 » : hausse sur 12 mois sans le dernier mois (effet documenté depuis les
    années 1990), avec un filtre de tendance (prix au-dessus de sa moyenne sur 10 mois).
    Les 10 meilleures forment la poche ; une action détenue n'est remplacée que si elle sort du
    top 20 ou perd sa tendance (moins d'allers-retours, moins de frais) ;
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

PRODUCT_URL = "https://www.ishares.com/uk/individual/en/products/251394/ishares-msci-world-islamic-ucits-etf"
FALLBACK_CSV = PRODUCT_URL + "/1506575576011.ajax?fileType=csv&fileName=ISWD_holdings&dataType=fund"
UNIVERSE_SIZE = 150
TOP_N = 10
KEEP_RANK = 20
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


def fetch_holdings() -> list[dict[str, Any]]:
    """Composition de l'ETF : lien trouvé sur la page du fonds, sinon liens connus (site particulier et
    professionnel, avec passage direct de la page d'avertissement d'iShares)."""
    pass_ = "siteEntryPassthrough=true"
    candidates = []
    for base in (PRODUCT_URL, PRODUCT_URL.replace("/individual/", "/professional/")):
        try:
            page = get_text(f"{base}?{pass_}", timeout=20)
            m = re.search(r'href="([^"]+\.ajax\?fileType=csv&(?:amp;)?fileName=[^"]*_holdings&(?:amp;)?dataType=fund)"', page)
            if m:
                candidates.append("https://www.ishares.com" + m.group(1).replace("&amp;", "&") + "&" + pass_)
        except ProviderError as exc:
            log.warning("page iShares indisponible (%s)", exc)
        candidates.append(base + "/1506575576011.ajax?fileType=csv&fileName=ISWD_holdings&dataType=fund&" + pass_)
    last: Exception | None = None
    for url in dict.fromkeys(candidates):
        try:
            text = get_text(url, timeout=30)
            rows = parse_holdings(text)
            if rows:
                return rows
        except ProviderError as exc:
            last = exc
            snippet = re.sub(r"\s+", " ", locals().get("text", "")[:200])
            log.warning("composition iShares illisible (%s) : %s… [%s]", url.split("?")[0][-60:], exc, snippet)
    raise ProviderError(f"composition iShares indisponible : {last}")


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


def momentum_table(series: dict[str, list[tuple[str, float]]], month: str) -> list[dict[str, Any]]:
    """Classement au mois `month` (fin de mois) : momentum 12-1 et filtre de tendance 10 mois."""
    out = []
    for key, s in series.items():
        idx = {m: i for i, (m, _) in enumerate(s)}
        i = idx.get(month)
        if i is None or i < 12:
            continue
        vals = [v for _, v in s]
        mom = vals[i - 1] / vals[i - 12] - 1
        sma = sum(vals[i - 9: i + 1]) / 10
        out.append({"key": key, "mom": mom, "trend": vals[i] > sma, "r1m": vals[i] / vals[i - 1] - 1})
    out.sort(key=lambda x: -x["mom"])
    for rank, row in enumerate(out, 1):
        row["rank"] = rank
    return out


def select(table: list[dict[str, Any]], held: list[str], n: int = TOP_N, keep_rank: int = KEEP_RANK) -> list[str]:
    """Garde les actions détenues encore dans le top `keep_rank` avec leur tendance, complète par les meilleures."""
    by = {r["key"]: r for r in table}
    kept = [k for k in held if k in by and by[k]["rank"] <= keep_rank and by[k]["trend"]]
    for r in table:
        if len(kept) >= n:
            break
        if r["trend"] and r["key"] not in kept:
            kept.append(r["key"])
    return kept[:n]


def backtest(series: dict[str, list[tuple[str, float]]], bench: list[tuple[str, float]] | None,
             n: int = TOP_N) -> dict[str, Any] | None:
    """Rejoue la règle chaque mois : poche équipondérée, rendement du mois suivant, frais de rotation."""
    months = sorted({m for s in series.values() for m, _ in s})
    maps = {k: dict(s) for k, s in series.items()}
    bmap = dict(bench or [])
    held: list[str] = []
    value, bvalue, curve, rows = 1.0, 1.0, [], []
    for a, b in zip(months, months[1:]):
        table = momentum_table(series, a)
        if len(table) < 3 * n:
            continue
        new = select(table, held, n)
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
    }


# ------------------------------------------------------------------ assemblage
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
    if fresh and not force and cache.get("result"):
        return cache["result"]

    holdings, source = None, "iShares"
    try:
        holdings = holdings_fn()
    except ProviderError as exc:
        log.warning("composition de l'ETF indisponible : %s", exc)
    if not holdings:
        holdings, source = cache.get("holdings"), "dernière composition connue"
    if not holdings:
        return cache.get("result")
    universe = holdings[:UNIVERSE_SIZE]

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
        s = to_eur_series(rows, ccy, fx)
        # 6 ans au plus, et au moins 14 mois pour pouvoir classer
        s = s[-73:]
        if len(s) >= 14:
            series[h["yahoo"]] = s
            meta[h["yahoo"]] = h
        else:
            missing.append(h["yahoo"])
        if pause:
            time.sleep(pause)
    if len(series) < 3 * TOP_N:
        log.warning("poche actions : trop peu d'historiques (%d)", len(series))
        return cache.get("result")

    # dernier mois complet commun (le mois en cours est partiel)
    last = sorted({s[-1][0] for s in series.values()})
    month = st.median_low(last)
    table = momentum_table(series, month)
    picks = select(table, [], TOP_N)
    by = {r["key"]: r for r in table}

    def row(k):
        h, r = meta[k], by.get(k, {})
        return {"yahoo": k, "name": h["name"], "sector": h["sector"], "country": h["country"], "index_weight": h["weight"],
                "price_eur": round(series[k][-1][1], 4), "mom": round(r.get("mom", 0), 4), "r1m": round(r.get("r1m", 0), 4),
                "trend": bool(r.get("trend")), "rank": r.get("rank")}

    result = {
        "updated_at": iso(now), "source": source, "universe_n": len(universe), "priced_n": len(series),
        "missing": missing[:40], "month": month,
        "rules": {"top_n": TOP_N, "keep_rank": KEEP_RANK, "cost": COST_PER_TURNOVER},
        "picks": [row(k) for k in picks],
        "ranked": [row(r["key"]) for r in table[:40]],
        "keep": [r["key"] for r in table if r["rank"] <= KEEP_RANK and r["trend"]],
        "prices": {k: {"name": meta[k]["name"], "price_eur": round(s[-1][1], 4)} for k, s in series.items()},
        "backtest": backtest(series, bench),
    }
    cdir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps({"updated_at": iso(now), "holdings": holdings, "result": result},
                                     ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return result
