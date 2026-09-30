"""Investissement halal à long terme : ETF islamiques, sukuk et or physique, suivis en euros.

Ce n'est pas du trading : on regarde des années, pas des heures. Une fois par jour, le module :
  - récupère l'historique mensuel de chaque produit (Yahoo, gratuit) et le convertit en euros ;
  - calcule rendements annualisés, volatilité, pire baisse, et surtout, pour chaque durée de
    détention (1 à 15 ans), la part des périodes gagnantes dans l'historique : la « durée conseillée »
    est la plus courte durée qui a été gagnante au moins 95 % du temps ;
  - simule des portefeuilles types (prudent, équilibré, dynamique) rééquilibrés chaque mois ;
  - applique quelques règles simples et transparentes (tendance longue, distance au plus haut,
    ce qui a suivi les baisses passées) pour un avis par produit ;
  - rassemble l'actualité récente (finance islamique, sukuk, or, marchés).
Données publiées dans docs/invest/data.json pour la page « Investir ». Aucun ordre n'est passé.
"""
from __future__ import annotations

import logging
import math
import re
import statistics as st
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from .config import ROOT_DIR
from .models import iso, utcnow
from .providers.http import ProviderError, get_json, get_text
from .providers.news import parse_rss
from .providers.yahoo import CHART_URL

log = logging.getLogger(__name__)

# ------------------------------------------------------------------ produits
# `yahoo` : cotation utilisée pour l'historique ; `proxy` : série plus longue qui décrit le même
# marché (affichée comme telle) quand le produit est trop récent pour juger sur plusieurs années.
UNIVERSE: list[dict[str, Any]] = [
    {"key": "monde", "name": "iShares MSCI World Islamic", "isin": "IE00B27YCN58", "yahoo": "ISDW.L", "ter": 0.30,
     "category": "Actions des pays développés", "kind": "actions", "income": "distribue (2 fois par an)",
     "role": "Cœur du portefeuille : environ 400 grandes entreprises mondiales filtrées charia (MSCI).",
     "since": 2007},
    {"key": "acwi", "name": "Invesco MSCI ACWI Islamic M-Series", "isin": "IE000LFC57H7", "yahoo": "MWIM.L",
     "ter": 0.35, "category": "Actions monde entier (développés + émergents)", "kind": "actions",
     "income": "capitalise", "role": "Alternative « tout en un » : pays développés et émergents dans un seul ETF.",
     "since": 2026, "proxy": "monde"},
    {"key": "usa", "name": "iShares MSCI USA Islamic", "isin": "IE00B296QM64", "yahoo": "ISDU.L", "ter": 0.30,
     "category": "Actions américaines", "kind": "actions", "income": "distribue",
     "role": "Pour renforcer les États-Unis ; très concentré sur quelques géants de la technologie.", "since": 2008},
    {"key": "emergents", "name": "iShares MSCI EM Islamic", "isin": "IE00B27YCP72", "yahoo": "ISDE.L", "ter": 0.35,
     "category": "Actions des pays émergents", "kind": "actions", "income": "distribue (2 fois par an)",
     "role": "Diversification (Asie, Moyen-Orient, Amérique latine) ; plus volatil.", "since": 2007},
    {"key": "dev_dj", "name": "Invesco Dow Jones Islamic Global Developed Markets", "isin": "IE000UOXRAM8",
     "yahoo": "IGDA.L", "ter": 0.40, "category": "Actions des pays développés", "kind": "actions",
     "income": "capitalise", "role": "Même marché que le MSCI World Islamic, autre filtre charia (Dow Jones).",
     "since": 2022, "proxy": "monde"},
    {"key": "sp500_wahed", "name": "Wahed S&P 500 Shariah", "isin": "IE000QF8TEK7", "yahoo": "SPWI.L", "ter": 0.49,
     "category": "Actions américaines", "kind": "actions", "income": "capitalise",
     "role": "Grandes entreprises américaines du S&P 500 conformes à la charia, filtre humanitaire en plus.",
     "since": 2026, "proxy": "usa"},
    {"key": "sukuk", "name": "HSBC Global Sukuk", "isin": "IE000E8WZD37", "yahoo": "HBKU.L", "ter": 0.37,
     "category": "Sukuk (obligations islamiques)", "kind": "sukuk", "income": "distribue",
     "role": "La partie stable : sukuk en dollars de bonne qualité (États, banques). Rendement régulier, faibles variations.",
     "since": 2025},
    {"key": "or", "name": "Royal Mint Physical Gold ETC", "isin": "XS2115336336", "yahoo": "RMAU.L", "ter": 0.25,
     "category": "Or physique", "kind": "or", "income": "aucun revenu",
     "role": "Protection en cas de crise et contre l'inflation ; or physique alloué, certifié charia (Amanie Advisors).",
     "since": 2020, "proxy": "or_long"},
]
# séries longues servant de référence (pas des produits à acheter)
PROXIES = {"or_long": {"name": "prix de l'or (contrat à terme, référence)", "yahoo": "GC=F"}}
FX = {"USD": "EURUSD=X", "GBP": "EURGBP=X"}

MODELS = {
    "prudent": {"label": "Prudent", "weights": {"sukuk": 0.50, "monde": 0.30, "or": 0.20},
                "for": "Objectif dans 3 à 5 ans, ou peu de tolérance aux baisses."},
    "equilibre": {"label": "Équilibré", "weights": {"monde": 0.55, "emergents": 0.10, "sukuk": 0.25, "or": 0.10},
                  "for": "Objectif dans 5 à 10 ans."},
    "dynamique": {"label": "Dynamique", "weights": {"monde": 0.70, "emergents": 0.15, "usa": 0.10, "or": 0.05},
                  "for": "Objectif à plus de 10 ans, en acceptant des baisses de 30 % ou plus en route."},
}
HORIZONS = [1, 2, 3, 5, 7, 10, 15]
# durée minimale de bon sens, quel que soit l'historique (l'or a stagné près de 20 ans, de 1980 à 2000)
FLOOR_YEARS = {"actions": 5, "or": 5, "sukuk": 2, "prudent": 3, "equilibre": 5, "dynamique": 8}


def advised(data_years: int | None, floor: int) -> dict[str, Any]:
    return {"years": max(floor, data_years or 0), "data_years": data_years, "floor": floor}

NEWS_QUERIES = [
    ('"finance islamique"', "finance islamique"),
    ('"ETF islamique" OR "ETF islamiques" OR "islamic ETF" OR "Shariah ETF"', "ETF islamiques"),
    ("sukuk", "sukuk"),
    ('"cours de l\'or" OR "prix de l\'or" once', "or"),
    ('"Bourse de Paris" OR "Wall Street" OR "marchés actions"', "marchés"),
]
NEWS_PER_TAG = 6
# sites qui inondent les résultats (prix de l'or en dongs traduits automatiquement, etc.)
NEWS_BLOCKED = re.compile(r"(\.vn\b|vietnam|laodong|\bVND\b|\bSJC\b|\btaels?\b)", re.I)


def invest_dir() -> Path:
    return ROOT_DIR / "data" / "invest"


# ------------------------------------------------------------------ données
def fetch_monthly(symbol: str) -> tuple[list[tuple[int, float]], str]:
    """(horodatage, clôture) mensuels sur tout l'historique, et devise de cotation Yahoo."""
    data = get_json(CHART_URL.format(symbol=symbol), params={"interval": "1mo", "range": "max"}, timeout=20)
    try:
        res = data["chart"]["result"][0]
        ts, closes = res["timestamp"], res["indicators"]["quote"][0]["close"]
        ccy = res["meta"].get("currency") or "USD"
        adj = (res["indicators"].get("adjclose") or [{}])[0].get("adjclose")
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError(f"réponse Yahoo inattendue pour {symbol}: {exc}") from exc
    vals = adj if adj and len(adj) == len(ts) else closes       # dividendes réinvestis si disponible
    rows = [(int(t), float(v)) for t, v in zip(ts, vals) if v is not None and v > 0]
    return rows, ccy


def month_key(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m")


def to_eur(rows: list[tuple[int, float]], ccy: str, fx: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    """Série mensuelle en euros (« GBp » = pence : /100 puis livres)."""
    factor = 0.01 if ccy in ("GBp", "GBX") else 1.0
    base = "GBP" if ccy in ("GBp", "GBX") else ccy
    out: dict[str, float] = {}
    for t, v in rows:
        m = month_key(t)
        if base == "EUR":
            out[m] = v * factor
        else:
            rate = (fx.get(base) or {}).get(m)
            if rate:
                out[m] = v * factor / rate          # EURUSD = dollars pour 1 euro
    return sorted(out.items())


# ------------------------------------------------------------------ statistiques
def returns(series: list[tuple[str, float]]) -> list[float]:
    return [series[i][1] / series[i - 1][1] - 1 for i in range(1, len(series))]


def annualized(series: list[tuple[str, float]], months: int) -> float | None:
    if len(series) <= months:
        return None
    return (series[-1][1] / series[-1 - months][1]) ** (12 / months) - 1


def max_drawdown(series: list[tuple[str, float]]) -> tuple[float, float]:
    """(pire baisse depuis un plus haut, baisse actuelle depuis le plus haut)."""
    peak, worst = 0.0, 0.0
    for _, v in series:
        peak = max(peak, v)
        worst = min(worst, v / peak - 1)
    return worst, series[-1][1] / peak - 1 if series else 0.0


def holding_periods(series: list[tuple[str, float]]) -> dict[str, Any]:
    """Pour chaque durée : part des périodes gagnantes, rendement annualisé médian, pire et meilleur."""
    out = {}
    vals = [v for _, v in series]
    for h in HORIZONS:
        m = 12 * h
        if len(vals) <= m + 6:
            continue
        rs = [(vals[i + m] / vals[i]) ** (1 / h) - 1 for i in range(len(vals) - m)]
        srt = sorted(rs)
        out[str(h)] = {"n": len(rs), "positive": round(sum(1 for r in rs if r > 0) / len(rs), 3),
                       "median": round(st.median(rs), 4), "worst": round(srt[0], 4), "best": round(srt[-1], 4),
                       "p10": round(srt[len(srt) // 10], 4), "p90": round(srt[(9 * len(srt)) // 10], 4)}
    return out


def advised_horizon(periods: dict[str, Any], threshold: float = 1.0) -> int | None:
    for h in HORIZONS:
        p = periods.get(str(h))
        if p and p["n"] >= 12 and p["positive"] >= threshold:
            return h
    return None


def after_drawdowns(series: list[tuple[str, float]], depth: float = -0.10, years: int = 3) -> dict[str, Any] | None:
    """Rendement sur `years` ans après les mois où le prix était à `depth` ou plus sous son plus haut,
    comparé à tous les mois : ce qu'ont donné, dans le passé, les achats pendant une baisse."""
    m = 12 * years
    vals = [v for _, v in series]
    if len(vals) <= m + 24:
        return None
    peak, dd = 0.0, []
    for v in vals:
        peak = max(peak, v)
        dd.append(v / peak - 1)
    fwd = [(vals[i + m] / vals[i]) ** (1 / years) - 1 for i in range(len(vals) - m)]
    cond = [f for i, f in enumerate(fwd) if dd[i] <= depth]
    if len(cond) < 6:
        return None
    return {"n": len(cond), "median_after": round(st.median(cond), 4), "median_all": round(st.median(fwd), 4),
            "years": years, "depth": depth}


def stats(series: list[tuple[str, float]]) -> dict[str, Any]:
    rs = returns(series)
    worst, current_dd = max_drawdown(series)
    sma10 = sum(v for _, v in series[-10:]) / 10 if len(series) >= 10 else None
    periods = holding_periods(series)
    return {
        "start": series[0][0] if series else None, "months": len(series),
        "last": round(series[-1][1], 4) if series else None, "last_month": series[-1][0] if series else None,
        "r1": annualized(series, 12), "r3": annualized(series, 36), "r5": annualized(series, 60),
        "r10": annualized(series, 120),
        "r_all": (series[-1][1] / series[0][1]) ** (12 / (len(series) - 1)) - 1 if len(series) > 12 else None,
        "vol": st.pstdev(rs) * math.sqrt(12) if len(rs) >= 12 else None,
        "max_dd": worst, "dd_now": current_dd,
        "trend_ratio": series[-1][1] / sma10 if sma10 else None,
        "periods": periods, "advised_years": advised_horizon(periods),
        "after_dd": after_drawdowns(series),
    }


def advice(p: dict[str, Any], s: dict[str, Any] | None, long: bool) -> dict[str, str]:
    """Avis par règles simples et affichées (pas un conseil personnalisé)."""
    if not s or s["months"] < 12:
        return {"tag": "neu", "label": "Trop récent", "text": "Moins d'un an de cotation : fiez-vous à l'historique de référence."}
    notes = []
    tr, dd = s.get("trend_ratio"), s.get("dd_now") or 0.0
    trend_up = tr is not None and tr >= 1.0
    notes.append(f"tendance longue {'haussière' if trend_up else 'baissière'} (prix {'au-dessus' if trend_up else 'en dessous'} "
                 "de sa moyenne sur 10 mois)")
    if dd <= -0.02:
        notes.append(f"{abs(dd) * 100:.0f} % sous son plus haut")
    else:
        notes.append("proche de son plus haut")
    ad = s.get("after_dd")
    if dd <= -0.10 and long:
        extra = ""
        if ad:
            extra = (f" Dans le passé, acheter pendant une baisse de 10 % ou plus a donné en médiane "
                     f"{ad['median_after'] * 100:+.1f} % par an sur {ad['years']} ans (contre {ad['median_all'] * 100:+.1f} % en général).")
        return {"tag": "up", "label": "Renforcer progressivement",
                "text": "Baisse marquée : bon moment pour continuer, voire augmenter un peu, les versements mensuels. "
                        + "; ".join(notes).capitalize() + "." + extra}
    if tr is not None and tr >= 1.15:
        return {"tag": "brand", "label": "Ne pas surpondérer",
                "text": "Forte hausse récente : continuer les versements prévus, sans dépasser la part cible du portefeuille. "
                        + "; ".join(notes).capitalize() + "."}
    if not trend_up and p["kind"] == "actions":
        return {"tag": "neu", "label": "Versements réguliers, patience",
                "text": "Tendance baissière : ne pas tout investir d'un coup, étaler sur plusieurs mois. "
                        + "; ".join(notes).capitalize() + "."}
    return {"tag": "up" if trend_up else "neu", "label": "Versements réguliers",
            "text": "Rien d'anormal : investir chaque mois le même montant. " + "; ".join(notes).capitalize() + "."}


def simulate_model(weights: dict[str, float], series: dict[str, list[tuple[str, float]]]) -> dict[str, Any] | None:
    """Portefeuille rééquilibré chaque mois, sur la période commune des produits qui ont au moins 3 ans.
    Les produits trop récents sont retirés et les poids répartis sur les autres (signalé)."""
    usable = {k: w for k, w in weights.items() if len(series.get(k) or []) >= 37}
    dropped = [k for k in weights if k not in usable]
    if not usable:
        return None
    total = sum(usable.values())
    usable = {k: w / total for k, w in usable.items()}
    maps = {k: dict(series[k]) for k in usable}
    months = sorted(set.intersection(*(set(m) for m in maps.values())))
    if len(months) < 37:
        return None
    value, curve = 1.0, [(months[0], 1.0)]
    for a, b in zip(months, months[1:]):
        value *= 1 + sum(w * (maps[k][b] / maps[k][a] - 1) for k, w in usable.items())
        curve.append((b, value))
    s = stats(curve)
    s["dropped"] = dropped
    s["weights_used"] = {k: round(w, 3) for k, w in usable.items()}
    pts = curve[::3] if (len(curve) - 1) % 3 == 0 else curve[::3] + [curve[-1]]
    s["curve"] = [[m, round(v, 4)] for m, v in pts]
    return s


# ------------------------------------------------------------------ actualités
def fetch_invest_news(now: datetime | None = None, days: int = 10, limit: int = 24) -> list[dict[str, Any]]:
    now = now or utcnow()
    cutoff = now - timedelta(days=days)
    seen, out = set(), []
    for q, tag in NEWS_QUERIES:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=fr&gl=FR&ceid=FR:fr"
        try:
            items = parse_rss(get_text(url, timeout=12), "news.google.com", tag)
        except ProviderError as exc:
            log.warning("actualité « %s » indisponible : %s", q, exc)
            continue
        for it in items:
            title = it.title.strip()
            source = ""
            m = re.match(r"^(.*) - ([^-]{2,60})$", title)
            if m:
                title, source = m.group(1).strip(), m.group(2).strip()
            key = re.sub(r"\W+", " ", title.lower())[:80]
            if it.published < cutoff or key in seen or NEWS_BLOCKED.search(f"{title} {source}"):
                continue
            seen.add(key)
            out.append({"title": title, "source": source, "link": it.link, "published": iso(it.published), "tag": tag})
    # quelques articles par thème (le plus récent d'abord), pour qu'un seul sujet n'envahisse pas la liste
    out.sort(key=lambda x: x["published"], reverse=True)
    kept, per = [], {}
    for x in out:
        if per.get(x["tag"], 0) < NEWS_PER_TAG:
            per[x["tag"]] = per.get(x["tag"], 0) + 1
            kept.append(x)
    return kept[:limit]


# ------------------------------------------------------------------ assemblage
def _stocks(bench, now, fetch):
    from . import halal_stocks
    return halal_stocks.build(bench, now, fetch_monthly=fetch)


def build(now: datetime | None = None, fetch=fetch_monthly, news=fetch_invest_news, stocks=_stocks) -> dict[str, Any]:
    now = now or utcnow()
    fx: dict[str, dict[str, float]] = {}
    for ccy, sym in FX.items():
        try:
            rows, _ = fetch(sym)
            fx[ccy] = {month_key(t): v for t, v in rows}
        except ProviderError as exc:
            log.warning("taux %s indisponible : %s", sym, exc)
    series: dict[str, list[tuple[str, float]]] = {}
    errors: dict[str, str] = {}
    for key, sym in [(p["key"], p["yahoo"]) for p in UNIVERSE] + [(k, v["yahoo"]) for k, v in PROXIES.items()]:
        try:
            rows, ccy = fetch(sym)
            s = to_eur(rows, ccy, fx)
            if len(s) >= 2:
                series[key] = s
            else:
                errors[key] = "historique vide"
        except ProviderError as exc:
            errors[key] = str(exc)[:120]
            log.warning("%s : %s", sym, exc)

    products = []
    for p in UNIVERSE:
        s = stats(series[p["key"]]) if p["key"] in series else None
        ref_key = p.get("proxy")
        ref = None
        if ref_key and ref_key in series and (not s or s["months"] < 60):
            ref = stats(series[ref_key])
            ref["name"] = PROXIES.get(ref_key, {}).get("name") or next(x["name"] for x in UNIVERSE if x["key"] == ref_key)
        long = bool((s and s["months"] >= 60) or ref)
        base = ref or s
        products.append({**{k: v for k, v in p.items() if k != "proxy"}, "stats": s, "reference": ref,
                         "advised": advised(base["advised_years"] if base else None, FLOOR_YEARS[p["kind"]]),
                         "advice": advice(p, s, long), "error": errors.get(p["key"])})

    # portefeuilles : l'or s'appuie sur sa série longue de référence
    model_series = dict(series)
    if "or_long" in series:
        model_series["or"] = series["or_long"]
    models = {}
    for key, m in MODELS.items():
        sim = simulate_model(m["weights"], model_series)
        models[key] = {**m, "sim": sim, "advised": advised(sim["advised_years"] if sim else None, FLOOR_YEARS[key])}

    stock_part = None
    if stocks:
        try:
            stock_part = stocks(series.get("monde"), now, fetch)
        except Exception:  # noqa: BLE001 — la poche actions ne doit jamais bloquer le reste de la page
            log.exception("poche actions halal")
    prices = {p["key"]: round(series[p["key"]][-1][1], 4) for p in UNIVERSE if p["key"] in series}
    return {"updated_at": iso(now), "products": products, "models": models, "stocks": stock_part, "prices": prices,
            "news": news(now) if news else [], "errors": errors,
            "fx_last": {c: (sorted(v.items())[-1][1] if v else None) for c, v in fx.items()}}


def publish(data: dict[str, Any], data_dir: Path | None = None, docs_dir: Path | None = None) -> None:
    import json
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    for d in (data_dir or invest_dir(), docs_dir or ROOT_DIR / "docs" / "invest"):
        d.mkdir(parents=True, exist_ok=True)
        (d / "data.json").write_text(text, encoding="utf-8")
