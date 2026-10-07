"""Revue de la stratégie d'investissement halal (essai 6 de HYPOTHESES.md, écrit avant tout calcul).

1. Témoins dans le même univers que la poche actions et les pépites : toutes les actions à poids égal et
   des tirages au hasard. Ils subissent le même biais du survivant (univers = composition actuelle de
   l'indice) : l'écart avec eux mesure l'apport réel du momentum.
2. Deux variantes de la règle : anti-krach (pas d'action ayant perdu 25 % ou plus le mois précédent) et
   corrélation (pas deux actions corrélées à plus de 0,75 sur 24 mois).
3. Risque du portefeuille complet « Dynamique » réglé comme sur le site (skill historical-risk).
4. Contrôle charia AAOIFI des actions sélectionnées (skill sharia-screening), avec taux de purification.

Lancé à la main sur GitHub Actions (`python run.py invest-review`) : Yahoo n'est pas joignable partout.
Résultat dans data/invest/review.json, copié pour la page Investir.
"""
from __future__ import annotations

import json
import logging
import math
import random
import statistics as st
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from . import halal_stocks as hs
from .config import ROOT_DIR
from .models import iso, utcnow
from .providers.http import ProviderError, get_json

log = logging.getLogger(__name__)

CRASH = -0.25            # anti-krach : baisse du mois précédent à partir de laquelle on n'achète ni ne garde
CORR_MAX, CORR_MONTHS = 0.75, 24
N_RANDOM = 500
EVERY = hs.REVISION_EVERY

# Portefeuille « Dynamique » tel que réglé sur le site par Yanisse (7 octobre 2026)
SITE_SETTINGS = {"pocket": 0.20, "pepites": 0.05, "bitcoin": 0.03}
SIM_START, SIM_MONTHLY = 1000.0, 200.0

# AAOIFI, norme 21 : rapports à la capitalisation boursière
AAOIFI_DEBT, AAOIFI_CASH, AAOIFI_IMPURE = 0.30, 0.30, 0.05
TIMESERIES_URL = "https://query2.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{sym}"
FUND_TYPES = ["annualTotalDebt", "annualCapitalLeaseObligations", "annualCashCashEquivalentsAndShortTermInvestments",
              "annualTotalRevenue", "annualInterestIncome", "annualInterestIncomeNonOperating", "trailingMarketCap"]


# ------------------------------------------------------------------ statistiques sur une suite de rendements
def stats_of(rets: list[float]) -> dict[str, Any] | None:
    if len(rets) < 12:
        return None
    value, peak, worst, curve = 1.0, 1.0, 0.0, [1.0]
    for r in rets:
        value *= 1 + r
        curve.append(value)
        peak = max(peak, value)
        worst = min(worst, value / peak - 1)
    years = len(rets) / 12
    roll = [curve[i + 12] / curve[i] - 1 for i in range(len(curve) - 12)]
    srt = sorted(rets)
    return {"months": len(rets), "cagr": value ** (1 / years) - 1, "vol": st.pstdev(rets) * math.sqrt(12),
            "max_dd": worst, "worst_12m": min(roll) if roll else None,
            "var95_month": -srt[max(0, int(0.05 * len(srt)) - 1)] if len(srt) >= 20 else None}


def halves(dated: list[tuple[str, float]]) -> list[dict[str, Any] | None]:
    """Statistiques de chaque moitié de la période (mêmes mois pour tous les portefeuilles comparés)."""
    mid = len(dated) // 2
    return [stats_of([r for _, r in dated[:mid]]), stats_of([r for _, r in dated[mid:]])]


# ------------------------------------------------------------------ témoins dans le même univers
def equal_weight(series: dict[str, list[tuple[str, float]]], months: list[str], every: int = EVERY,
                 cost: float = hs.COST_PER_TURNOVER) -> list[tuple[str, float]]:
    """Toutes les actions disponibles à poids égal, remis à égalité tous les `every` mois (frais compris),
    poids qui dérivent entre deux. Rendements datés sur les mêmes mois que la règle."""
    maps = {k: dict(s) for k, s in series.items()}
    out, weights = [], {}
    for i, b in enumerate(months):
        a = _prev_month(b)
        avail = [k for k, m in maps.items() if a in m and b in m]
        if not avail:
            continue
        r_cost = 0.0
        if i % every == 0 or not weights:
            new = {k: 1 / len(avail) for k in avail}
            r_cost = sum(abs(new.get(k, 0) - weights.get(k, 0)) for k in set(new) | set(weights)) * cost
            weights = new
        live = {k: w for k, w in weights.items() if k in avail}
        tot = sum(live.values()) or 1.0
        rets = {k: maps[k][b] / maps[k][a] - 1 for k in live}
        r = sum(w / tot * rets[k] for k, w in live.items()) - r_cost
        grown = {k: w / tot * (1 + rets[k]) for k, w in live.items()}
        g = sum(grown.values()) or 1.0
        weights = {k: v / g for k, v in grown.items()}
        out.append((b, r))
    return out


def random_runs(series: dict[str, list[tuple[str, float]]], rule_returns: list[list], n: int,
                draws: int = N_RANDOM, seed: int = 6, every: int = EVERY,
                cost: float = hs.COST_PER_TURNOVER) -> list[list[tuple[str, float]]]:
    """Tirages au hasard avec la même rotation que la règle : à chaque révision, autant d'actions remplacées
    que la règle en a remplacé ce mois-là (mêmes frais), les autres gardées."""
    maps = {k: dict(s) for k, s in series.items()}
    rng = random.Random(seed)
    runs = []
    for _ in range(draws):
        held: list[str] = []
        out = []
        for i, (b, _r, turnover) in enumerate(rule_returns):
            a = _prev_month(b)
            avail = [k for k, m in maps.items() if a in m and b in m]
            if len(avail) < n:
                continue
            held = [k for k in held if k in avail]
            if not held:
                held, t = rng.sample(avail, n), 1.0
            else:
                t = 0.0
                if i % every == 0:
                    k_out = min(len(held), round(turnover * n))
                    for k in rng.sample(held, k_out):
                        held.remove(k)
                    t = k_out / n
                pool = [k for k in avail if k not in held]
                missing = n - len(held)
                if missing > 0:
                    held += rng.sample(pool, missing)
                    t = max(t, missing / n)
            r = sum(maps[k][b] / maps[k][a] - 1 for k in held) / len(held) - t * 2 * cost
            out.append((b, r))
        runs.append(out)
    return runs


def _prev_month(m: str) -> str:
    y, mo = int(m[:4]), int(m[5:7])
    y, mo = (y, mo - 1) if mo > 1 else (y - 1, 12)
    return f"{y:04d}-{mo:02d}"


# ------------------------------------------------------------------ variante corrélation
def correlation_test(series: dict[str, list[tuple[str, float]]], limit: float = CORR_MAX,
                     window: int = CORR_MONTHS) -> Callable[[str], Callable[[str, list[str]], bool]]:
    """`close_at(mois)` → test « trop corrélée à une action déjà retenue », avec les seuls mois connus."""
    maps = {k: dict(s) for k, s in series.items()}

    def rets_until(k: str, month: str) -> dict[str, float]:
        m, out = month, {}
        for _ in range(window):
            p = _prev_month(m)
            if m in maps[k] and p in maps[k]:
                out[m] = maps[k][m] / maps[k][p] - 1
            m = p
        return out

    def close_at(month: str) -> Callable[[str, list[str]], bool]:
        cache: dict[str, dict[str, float]] = {}

        def get(k):
            if k not in cache:
                cache[k] = rets_until(k, month)
            return cache[k]

        def too_close(k: str, kept: list[str]) -> bool:
            return any((c := corr(get(k), get(j))) is not None and c > limit for j in kept)
        return too_close
    return close_at


def corr(x: dict[str, float], y: dict[str, float]) -> float | None:
    common = sorted(set(x) & set(y))
    if len(common) < 12:
        return None
    a, b = [x[m] for m in common], [y[m] for m in common]
    sa, sb = st.pstdev(a), st.pstdev(b)
    if not sa or not sb:
        return None
    ma, mb = st.fmean(a), st.fmean(b)
    return sum((u - ma) * (v - mb) for u, v in zip(a, b)) / (len(a) * sa * sb)


def pairwise(series: dict[str, list[tuple[str, float]]], keys: list[str], month: str) -> dict[str, Any]:
    """Corrélations entre les actions retenues (24 derniers mois) : moyenne et paires au-dessus de 0,75."""
    maps = {k: dict(series[k]) for k in keys if k in series}
    rets = {}
    for k, m in maps.items():
        ms = sorted(m)[-(CORR_MONTHS + 1):]
        rets[k] = {b: m[b] / m[a] - 1 for a, b in zip(ms, ms[1:])}
    pairs = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if a in rets and b in rets and (c := corr(rets[a], rets[b])) is not None:
                pairs.append((a, b, c))
    return {"mean": st.fmean(c for *_, c in pairs) if pairs else None,
            "high": [[a, b, round(c, 2)] for a, b, c in sorted(pairs, key=lambda p: -p[2]) if c > CORR_MAX]}


# ------------------------------------------------------------------ revue d'une poche
def review_pocket(series: dict[str, list[tuple[str, float]]], bench: list[tuple[str, float]] | None,
                  sectors: dict[str, str], n: int, lookback: int, keep_rank: int, cap: int,
                  draws: int = N_RANDOM) -> dict[str, Any] | None:
    kw = dict(n=n, sectors=sectors, every=EVERY, lookback=lookback, keep_rank=keep_rank, cap=cap)
    base = hs.backtest(series, bench, **kw)
    if not base:
        return None
    rule = [(m, r) for m, r, _ in base["returns"]]
    months = [m for m, _ in rule]
    ew = [x for x in equal_weight(series, months) if x[0] in set(months)]
    runs = random_runs(series, base["returns"], n, draws)
    rnd_cagr = sorted(s["cagr"] for s in (stats_of([r for _, r in run]) for run in runs) if s)
    rnd_half = [sorted(h["cagr"] for h in (halves(run)[i] for run in runs) if h) for i in (0, 1)]

    def pct_beaten(value, dist):
        return sum(1 for x in dist if value > x) / len(dist) if dist else None

    rule_s, ew_s = stats_of([r for _, r in rule]), stats_of([r for _, r in ew])
    rule_h, ew_h = halves(rule), halves(ew)
    halves_ok = []
    for i in (0, 1):
        ok = (rule_h[i] and ew_h[i] and rule_h[i]["cagr"] > ew_h[i]["cagr"]
              and (pct_beaten(rule_h[i]["cagr"], rnd_half[i]) or 0) >= 0.9)
        halves_ok.append(bool(ok))
    out = {
        "rule": {**rule_s, "halves": rule_h},
        "equal_weight": {**ew_s, "halves": ew_h} if ew_s else None,
        "random": {"draws": len(rnd_cagr), "median_cagr": st.median(rnd_cagr) if rnd_cagr else None,
                   "p90_cagr": rnd_cagr[int(0.9 * len(rnd_cagr)) - 1] if rnd_cagr else None,
                   "rule_beats_share": pct_beaten(rule_s["cagr"], rnd_cagr),
                   "halves_rule_beats_share": [pct_beaten(rule_h[i]["cagr"], rnd_half[i]) if rule_h[i] else None
                                               for i in (0, 1)]},
        "momentum_edge": rule_s["cagr"] - ew_s["cagr"] if ew_s else None,
        "edge_proven": all(halves_ok),
        "halves_ok": halves_ok,
        "period": [months[0], months[-1]],
        "variants": {},
    }
    variants = {"anti_krach": dict(exclude=lambda row: row["r1m"] <= CRASH),
                "correlation": dict(close_at=correlation_test(series))}
    for name, extra in variants.items():
        v = hs.backtest(series, bench, **kw, **extra)
        if not v:
            continue
        vr = [(m, r) for m, r, _ in v["returns"]]
        vs, vh = stats_of([r for _, r in vr]), halves(vr)
        adopt = (vs["max_dd"] - rule_s["max_dd"] >= 0.03 and vs["cagr"] >= rule_s["cagr"] - 0.01
                 and all(vh[i] and rule_h[i] and vh[i]["max_dd"] >= rule_h[i]["max_dd"] for i in (0, 1)))
        out["variants"][name] = {**vs, "halves": vh, "adopt": bool(adopt)}
    return out


# ------------------------------------------------------------------ portefeuille complet
def portfolio_risk(products: dict[str, list[tuple[str, float]]], pocket_rets: list[tuple[str, float]] | None,
                   pepite_rets: list[tuple[str, float]] | None, model_weights: dict[str, float],
                   settings: dict[str, float] = SITE_SETTINGS) -> dict[str, Any] | None:
    """Portefeuille du site rééquilibré chaque mois, sur la période commune : ETF + or (reste), poche,
    pépites et Bitcoin aux parts choisies. Ce que donnent 1 000 € puis 200 €/mois au pire moment."""
    core = 1 - settings["pocket"] - settings["pepites"] - settings["bitcoin"]
    weights = {k: w * core for k, w in model_weights.items()}
    weights["bitcoin"] = settings["bitcoin"]
    rets: dict[str, dict[str, float]] = {}
    for k in list(weights):
        s = products.get(k)
        if not s:
            return None
        rets[k] = {b: vb / va - 1 for (a, va), (b, vb) in zip(s, s[1:])}
    if settings["pocket"]:
        if not pocket_rets:
            return None
        rets["pocket"], weights["pocket"] = dict(pocket_rets), settings["pocket"]
    if settings["pepites"]:
        if not pepite_rets:
            return None
        rets["pepites"], weights["pepites"] = dict(pepite_rets), settings["pepites"]
    months = sorted(set.intersection(*(set(r) for r in rets.values())))
    if len(months) < 24:
        return None
    port = [(m, sum(w * rets[k][m] for k, w in weights.items())) for m in months]
    core_only = [(m, sum(model_weights[k] * rets[k][m] for k in model_weights)) for m in months]
    s, c = stats_of([r for _, r in port]), stats_of([r for _, r in core_only])
    # versements : 1 000 € au départ puis 200 €/mois ; plus forte perte en euros par rapport au plus haut
    value, paid, peak, worst_eur, worst_at = SIM_START, SIM_START, SIM_START, 0.0, None
    for i, (m, r) in enumerate(port):
        value *= 1 + r
        if i:
            value += SIM_MONTHLY
            paid += SIM_MONTHLY
        if value > peak:
            peak = value
        if value - peak < worst_eur:
            worst_eur, worst_at = value - peak, m
    return {"weights": {k: round(w, 4) for k, w in weights.items()}, "period": [months[0], months[-1]],
            "portfolio": s, "etf_only": c, "sim": {"paid": round(paid, 2), "value": round(value, 2),
                                                   "worst_drop_eur": round(worst_eur, 2), "worst_at": worst_at}}


# ------------------------------------------------------------------ contrôle charia AAOIFI
def fetch_fundamentals(sym: str, now: datetime | None = None) -> dict[str, Any]:
    now = now or utcnow()
    p2 = int(now.timestamp())
    p1 = int((now - timedelta(days=5 * 366)).timestamp())
    data = get_json(TIMESERIES_URL.format(sym=sym), params={"symbol": sym, "type": ",".join(FUND_TYPES),
                                                            "period1": p1, "period2": p2}, timeout=20)
    out: dict[str, Any] = {}
    for res in (data.get("timeseries") or {}).get("result") or []:
        typ = ((res.get("meta") or {}).get("type") or [None])[0]
        vals = [v for v in (res.get(typ) or []) if v and (v.get("reportedValue") or {}).get("raw") is not None]
        if typ and vals:
            last = max(vals, key=lambda v: v.get("asOfDate") or "")
            out[typ] = {"value": float(last["reportedValue"]["raw"]), "date": last.get("asOfDate"),
                        "ccy": last.get("currencyCode")}
    return out


def aaoifi(f: dict[str, Any]) -> dict[str, Any]:
    """Ratios AAOIFI sur les derniers comptes annuels (corrigés des défauts du script d'origine : loyers retirés
    de la dette, intérêts annuels rapportés au chiffre d'affaires annuel)."""
    def v(k):
        return (f.get(k) or {}).get("value")
    cap, rev = v("trailingMarketCap"), v("annualTotalRevenue")
    debt = v("annualTotalDebt")
    if debt is not None and v("annualCapitalLeaseObligations"):
        debt -= v("annualCapitalLeaseObligations")
    cash = v("annualCashCashEquivalentsAndShortTermInvestments")
    interest = v("annualInterestIncome") if v("annualInterestIncome") is not None else v("annualInterestIncomeNonOperating")
    ccys = {(f.get(k) or {}).get("ccy") for k in ("annualTotalDebt", "annualTotalRevenue", "trailingMarketCap")} - {None}
    res: dict[str, Any] = {"debt": None, "cash": None, "impure": None, "verdict": "données manquantes",
                           "as_of": (f.get("annualTotalRevenue") or {}).get("date")}
    if not cap or cap <= 0 or debt is None or cash is None or not rev:
        return res
    res["debt"], res["cash"] = debt / cap, cash / cap
    res["impure"] = (interest or 0.0) / rev
    if len(ccys) > 1:
        res["verdict"] = "à vérifier (devises différentes)"
        return res
    ok = res["debt"] < AAOIFI_DEBT and res["cash"] < AAOIFI_CASH and res["impure"] < AAOIFI_IMPURE
    res["verdict"] = "conforme" if ok else "non conforme AAOIFI"
    res["purification"] = res["impure"] if ok else None
    return res


def screen(symbols: list[str], fetch: Callable[[str], dict[str, Any]] = fetch_fundamentals) -> dict[str, Any]:
    out = {}
    for sym in symbols:
        try:
            out[sym] = aaoifi(fetch(sym))
        except (ProviderError, ValueError, TypeError) as exc:
            log.warning("comptes de %s indisponibles : %s", sym, exc)
            out[sym] = {"verdict": "données manquantes"}
    return out


# ------------------------------------------------------------------ assemblage
def run(now: datetime | None = None, fetch_monthly: Callable | None = None, holdings_fn: Callable | None = None,
        fundamentals: Callable[[str], dict[str, Any]] = fetch_fundamentals, draws: int = N_RANDOM,
        pause: float = 0.15) -> dict[str, Any]:
    from . import invest
    now = now or utcnow()
    fetch_monthly = fetch_monthly or invest.fetch_monthly
    products, _fx, _err = invest.load_series(fetch_monthly)
    bench = products.get("monde")

    holdings = None
    try:
        holdings = (holdings_fn or hs.fetch_holdings)()
    except ProviderError as exc:
        log.warning("composition de l'ETF indisponible : %s", exc)
    if not holdings:
        try:
            cache = json.loads((hs.data_dir() / "stocks_cache.json").read_text(encoding="utf-8"))
            holdings = cache.get("holdings")
        except (OSError, ValueError):
            holdings = None
    if not holdings:
        raise ProviderError("aucune composition de l'indice disponible")
    universe = [h for h in holdings if not hs.is_israeli(h)][:hs.PEPITES_TO]
    series, meta, missing = hs.load_universe(universe, fetch_monthly, pause)
    big = {h["yahoo"]: series[h["yahoo"]] for h in universe[:hs.UNIVERSE_SIZE] if h["yahoo"] in series}
    small = {h["yahoo"]: series[h["yahoo"]] for h in universe[hs.PEPITES_FROM:hs.PEPITES_TO] if h["yahoo"] in series}
    sectors = {k: meta[k].get("sector", "") for k in series}

    pocket = review_pocket(big, bench, sectors, hs.TOP_N, 12, hs.KEEP_RANK, hs.SECTOR_CAP, draws)
    pep = review_pocket(small, bench, sectors, hs.PEPITES_N, hs.PEPITES_LOOKBACK, hs.PEPITES_KEEP, hs.PEPITES_CAP, draws)

    model = invest.MODELS["dynamique"]["weights"]
    model_series = dict(products)
    if "or_long" in products:
        model_series["or"] = products["or_long"]
    pocket_rets = [(m, r) for m, r, _ in (hs.backtest(big, bench, sectors=sectors, every=EVERY) or {}).get("returns", [])]
    pep_bt = hs.backtest(small, bench, hs.PEPITES_N, sectors, every=EVERY, lookback=hs.PEPITES_LOOKBACK,
                         keep_rank=hs.PEPITES_KEEP, cap=hs.PEPITES_CAP) or {}
    pep_rets = [(m, r) for m, r, _ in pep_bt.get("returns", [])]
    risk = {"site": portfolio_risk(model_series, pocket_rets, pep_rets, model),
            "etf_only": portfolio_risk(model_series, None, None, model, {"pocket": 0, "pepites": 0, "bitcoin": 0})}

    # sélection actuelle : corrélations et contrôle AAOIFI
    month = hs.last_common_month(big)
    picks = hs.select(hs.momentum_table(big, month), [], hs.TOP_N, sectors=sectors)
    ptable = hs.momentum_table(small, month, hs.PEPITES_LOOKBACK)
    ppicks = hs.select(ptable, [], hs.PEPITES_N, hs.PEPITES_KEEP, sectors=sectors, cap=hs.PEPITES_CAP)
    current = {"month": month, "picks": picks, "pepites": ppicks,
               "names": {k: meta[k]["name"] for k in picks + ppicks},
               "correlation": pairwise({**big, **small}, picks + ppicks, month),
               "aaoifi": screen(picks + ppicks, fundamentals)}
    return {"updated_at": iso(now), "universe": {"pocket": len(big), "pepites": len(small), "missing": len(missing)},
            "settings": SITE_SETTINGS, "pocket": pocket, "pepites": pep, "risk": risk, "current": current,
            "rules": {"crash": CRASH, "corr_max": CORR_MAX, "corr_months": CORR_MONTHS, "draws": draws,
                      "aaoifi": [AAOIFI_DEBT, AAOIFI_CASH, AAOIFI_IMPURE]}}


def publish(result: dict[str, Any], data_dir: Path | None = None, docs_dir: Path | None = None) -> None:
    text = json.dumps(result, ensure_ascii=False, separators=(",", ":"), default=float)
    for d in (data_dir or ROOT_DIR / "data" / "invest", docs_dir or ROOT_DIR / "docs" / "invest"):
        d.mkdir(parents=True, exist_ok=True)
        (d / "review.json").write_text(text, encoding="utf-8")
