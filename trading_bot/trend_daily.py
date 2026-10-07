"""Essai 11 (HYPOTHESES.md) : suivi de tendance sur bougies journalières, 16 marchés, depuis 2007.

Données : cours journaliers ajustés de 16 ETF qui détiennent les contrats et les roulent eux-mêmes (le prix suit
ce que gagne celui qui garde le contrat, sans les sauts artificiels des séries « =F »), gardés hors du dépôt
(`data/history/etf_<symbole>_1d.json`). Deux règles publiées, aucun réglage ajusté :
  A. cassure de Donchian 55/20 (système 2 des « Turtles »), stop à 2 ATR(20), résultat en R ;
  B. momentum sur 12 mois (Moskowitz, Ooi & Pedersen, 2012), revu chaque fin de mois, taille inverse à la volatilité.
Verdict sur le portefeuille, chacune des deux moitiés (2007-2016, 2017-2026). Simulation d'un défi CFD 50 000 $
sur l'historique réel (départs successifs), pour information.
"""
from __future__ import annotations

import json
import math
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import indicators as ind
from .config import DATA_DIR
from .models import Candle, iso, utcnow

MARKETS = {  # symbole : nom
    "GLD": "Or", "SLV": "Argent", "USO": "Pétrole", "UNG": "Gaz naturel", "DBA": "Agriculture",
    "DBB": "Métaux industriels", "IEF": "Taux US 7-10 ans", "TLT": "Taux US 20 ans+", "FXE": "Euro", "FXY": "Yen",
    "FXB": "Livre sterling", "FXA": "Dollar australien", "FXC": "Dollar canadien", "SPY": "Actions US (S&P 500)",
    "QQQ": "Nasdaq 100", "EEM": "Actions émergentes",
}
START = datetime(2007, 3, 1, tzinfo=timezone.utc)
HALF = datetime(2017, 1, 1, tzinfo=timezone.utc)
COST = 0.0005                      # 0,05 % du prix par aller-retour
N_TRIALS = 96
ENTRY_N, EXIT_N, ATR_N, STOP_ATR = 55, 20, 20, 2.0


def history_file(sym: str) -> Path:
    return Path(DATA_DIR) / "history" / f"etf_{sym}_1d.json"


def fetch_daily(sym: str, get=None) -> list[Candle]:
    """Cours journaliers ajustés (ouverture, plus haut, plus bas ramenés au même facteur que la clôture ajustée)."""
    if get is None:
        from .providers.http import get_json as get
    data = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
               params={"interval": "1d", "period1": 1_104_537_600, "period2": int(time.time()) + 86_400,
                       "events": "div,split"}, timeout=60)
    r = data["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    adj = ((r["indicators"].get("adjclose") or [{}])[0].get("adjclose")) or q["close"]
    out = []
    for i, t in enumerate(r["timestamp"]):
        o, h, lo, c, a = q["open"][i], q["high"][i], q["low"][i], q["close"][i], adj[i]
        if None in (o, h, lo, c, a) or c <= 0:
            continue
        f = a / c
        out.append(Candle(int(t) - int(t) % 86_400, o * f, h * f, lo * f, a, float(q["volume"][i] or 0)))
    return out


def load(sym: str, refresh: bool = False, get=None) -> list[Candle]:
    f = history_file(sym)
    if f.exists() and not refresh:
        return [Candle(*x) for x in json.loads(f.read_text(encoding="utf-8"))]
    bars = fetch_daily(sym, get)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps([[b.ts, b.open, b.high, b.low, b.close, b.volume] for b in bars]), encoding="utf-8")
    return bars


# ------------------------------------------------------------------ A. Donchian 55/20
def donchian(bars: list[Candle], market: str) -> tuple[list[dict[str, Any]], dict[int, float]]:
    """Trades (en R, frais compris) et gain journalier latent en R, jour par jour (clôture à clôture)."""
    atr = ind.atr(bars, ATR_N)
    trades: list[dict[str, Any]] = []
    daily: dict[int, float] = {}
    i = ENTRY_N
    n = len(bars)
    while i < n - 1:
        b = bars[i]
        hi = max(x.high for x in bars[i - ENTRY_N:i])
        lo = min(x.low for x in bars[i - ENTRY_N:i])
        if not atr[i] or not (b.close > hi or b.close < lo):
            i += 1
            continue
        d = 1 if b.close > hi else -1
        j = i + 1
        entry = bars[j].open
        risk = STOP_ATR * atr[i]
        stop = entry - d * risk
        prev = entry
        marks: dict[int, float] = {}               # gain latent jour par jour, gardé seulement si le trade se clôt
        exit_px, why = None, "fin des données"
        while j < n:
            x = bars[j]
            if (x.low <= stop) if d > 0 else (x.high >= stop):          # stop (à l'ouverture si elle est au-delà)
                exit_px = min(stop, x.open) if d > 0 else max(stop, x.open)
                why = "stop"
                break
            marks[x.ts] = marks.get(x.ts, 0.0) + d * (x.close - prev) / risk
            prev = x.close
            chan = bars[max(0, j - EXIT_N):j]
            if (x.close < min(c.low for c in chan)) if d > 0 else (x.close > max(c.high for c in chan)):
                if j + 1 < n:
                    j += 1
                    exit_px, why = bars[j].open, "canal"
                break
            j += 1
        if exit_px is None:                                            # encore ouvert à la fin des données
            break
        x = bars[min(j, n - 1)]
        cost = COST * entry / risk
        marks[x.ts] = marks.get(x.ts, 0.0) + d * (exit_px - prev) / risk - cost
        for k, v in marks.items():
            daily[k] = daily.get(k, 0.0) + v
        trades.append({"market": market, "dir": d, "entry_ts": bars[i + 1].ts, "exit_ts": x.ts, "entry": entry,
                       "exit": exit_px, "risk": risk, "risk_pct": risk / entry,
                       "r": d * (exit_px - entry) / risk - cost, "why": why})
        i = j if why == "stop" else j          # nouvelle cassure possible dès la clôture du jour de sortie
    return trades, daily


def _stats(rs: list[float]) -> dict[str, Any]:
    n = len(rs)
    if not n:
        return {"n": 0, "mean_r": None, "pf": None, "win_rate": None}
    gains, losses = sum(r for r in rs if r > 0), -sum(r for r in rs if r < 0)
    sd = statistics.pstdev(rs) if n > 1 else 0.0
    return {"n": n, "mean_r": round(sum(rs) / n, 4), "se": round(sd / math.sqrt(n), 4),
            "pf": round(gains / losses, 3) if losses else None, "win_rate": round(sum(r > 0 for r in rs) / n, 4)}


def max_drawdown(values: list[float]) -> float:
    peak = cum = worst = 0.0
    for v in values:
        cum += v
        peak = max(peak, cum)
        worst = max(worst, peak - cum)
    return worst


def year_of(ts: int) -> int:
    return datetime.fromtimestamp(ts, timezone.utc).year


def judge_a(trades: list[dict[str, Any]], daily: dict[int, float]) -> dict[str, Any]:
    half = int(HALF.timestamp())
    h1 = [t["r"] for t in trades if t["entry_ts"] < half]
    h2 = [t["r"] for t in trades if t["entry_ts"] >= half]
    years: dict[int, float] = {}
    for ts, v in daily.items():
        years[year_of(ts)] = years.get(year_of(ts), 0.0) + v
    full_years = {y: v for y, v in years.items() if 2007 < y < datetime.now(timezone.utc).year}
    pos_share = sum(v > 0 for v in full_years.values()) / len(full_years) if full_years else 0.0
    s1, s2 = _stats(h1), _stats(h2)
    ok = all(s["n"] >= 30 and (s["mean_r"] or 0) > 0 and (s["pf"] or 0) >= 1.1 for s in (s1, s2)) and pos_share >= 0.6
    rs = sorted(t["r"] for t in trades)
    cut = max(1, len(rs) // 20)
    days = [daily[k] for k in sorted(daily)]
    return {"kept": ok, "first_half": s1, "second_half": s2, "all": _stats([t["r"] for t in trades]),
            "years": {str(y): round(v, 2) for y, v in sorted(years.items())}, "positive_years_share": round(pos_share, 3),
            "without_top5": round(sum(rs[:-cut]) / len(rs[:-cut]), 4) if len(rs) > cut else None,
            "max_drawdown_r": round(max_drawdown(days), 1), "total_r": round(sum(days), 1)}


# ------------------------------------------------------------------ B. momentum 12 mois
def tsmom(series: dict[str, list[Candle]]) -> dict[str, Any]:
    """Rendements journaliers du portefeuille momentum (poids égal, taille inverse à la volatilité, revu chaque
    fin de mois), frais compris. Renvoie aussi le Sharpe et le rendement de chaque moitié, ramenés à 10 % de
    volatilité annuelle sur toute la période (le Sharpe n'en dépend pas)."""
    dates = sorted({b.ts for bars in series.values() for b in bars if b.ts >= int(START.timestamp())})
    close = {m: {b.ts: b.close for b in bars} for m, bars in series.items()}
    rets: dict[str, dict[int, float]] = {}
    for m, bars in series.items():
        rets[m] = {bars[k].ts: bars[k].close / bars[k - 1].close - 1 for k in range(1, len(bars))}
    weights: dict[str, float] = {}
    port: list[tuple[int, float]] = []
    month = None
    for t in dates:
        r = sum(w * rets[m].get(t, 0.0) for m, w in weights.items())
        cur = datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m")
        port.append((t, r))
        if month is None:
            month = cur
        if cur != month:                     # premier jour d'un nouveau mois : on revoit les poids
            month = cur
            new = month_weights(series, t)
            turnover = sum(abs(new.get(m, 0.0) - weights.get(m, 0.0)) for m in set(new) | set(weights))
            port[-1] = (t, port[-1][1] - turnover * COST / 2)
            weights = new
    vals = [r for _, r in port]
    scale = 0.10 / (statistics.pstdev(vals) * math.sqrt(252)) if len(vals) > 1 and statistics.pstdev(vals) > 0 else 1.0
    half = int(HALF.timestamp())

    def summary(rows: list[float]) -> dict[str, Any]:
        if len(rows) < 2:
            return {"n_days": len(rows)}
        mu, sd = statistics.mean(rows), statistics.pstdev(rows)
        eq, peak, dd = 1.0, 1.0, 0.0
        for r in rows:
            eq *= 1 + r * scale
            peak = max(peak, eq)
            dd = max(dd, 1 - eq / peak)
        years = len(rows) / 252
        return {"n_days": len(rows), "sharpe": round(mu / sd * math.sqrt(252), 3) if sd else None,
                "annual_return_at_10pct_vol": round(eq ** (1 / years) - 1, 4) if years > 0 else None,
                "max_drawdown_at_10pct_vol": round(dd, 4)}
    s1 = summary([r for t, r in port if t < half])
    s2 = summary([r for t, r in port if t >= half])
    ok = all((s.get("sharpe") or 0) >= 0.3 and (s.get("annual_return_at_10pct_vol") or 0) > 0 for s in (s1, s2))
    return {"kept": ok, "first_half": s1, "second_half": s2, "all": summary(vals), "scale_10": round(scale, 4)}


def month_weights(series: dict[str, list[Candle]], t: int) -> dict[str, float]:
    """Poids du momentum 12 mois avec les clôtures d'avant `t` : sens du rendement sur 252 séances, taille
    40 % ÷ volatilité annuelle (60 séances), poids égal entre marchés."""
    live = []
    for m, bars in series.items():
        k = _index_before([b.ts for b in bars], t)
        if k is None or k < 252:
            continue
        r12 = bars[k].close / bars[k - 252].close - 1
        daily_r = [bars[q].close / bars[q - 1].close - 1 for q in range(k - 59, k + 1)]
        vol = statistics.pstdev(daily_r) * math.sqrt(252)
        if vol > 0:
            live.append((m, (1 if r12 > 0 else -1) * 0.40 / vol))
    return {m: w / len(live) for m, w in live} if live else {}


def _index_before(idx: list[int], ts: int) -> int | None:
    from bisect import bisect_left
    k = bisect_left(idx, ts) - 1
    return k if k >= 0 else None


# ------------------------------------------------------------------ défi CFD sur l'historique réel
def challenge(daily_r: list[tuple[int, float]], risk_usd: float, account: float = 50_000.0,
              steps=(0.10, 0.05), max_loss=0.10, daily_loss=0.05, step_days: int = 5) -> dict[str, Any]:
    """Départs successifs (tous les `step_days` jours) sur la vraie courbe journalière : part des départs qui
    atteignent chaque objectif sans toucher la perte maximale fixe ni la perte journalière (clôtures seulement),
    et délai en jours de bourse. Pas de limite de temps."""
    pnl = [v * risk_usd for _, v in daily_r]
    passed, days, fails = 0, [], {"perte maximale": 0, "perte journalière": 0, "pas fini": 0}
    starts = range(0, len(pnl), step_days)
    for s in starts:
        k, total, ok = s, 0, True
        for target in steps:
            eq = 0.0
            while k < len(pnl):
                eq += pnl[k]
                total += 1
                k += 1
                if pnl[k - 1] <= -daily_loss * account:
                    fails["perte journalière"] += 1
                    ok = False
                    break
                if eq <= -max_loss * account:
                    fails["perte maximale"] += 1
                    ok = False
                    break
                if eq >= target * account:
                    break
            else:
                fails["pas fini"] += 1
                ok = False
            if not ok:
                break
        if ok:
            passed += 1
            days.append(total)
    n = len(starts)
    days.sort()
    q = lambda p: days[min(len(days) - 1, int(p * len(days)))] if days else None  # noqa: E731
    return {"risk_usd": risk_usd, "starts": n, "pass": round(passed / n, 4) if n else None,
            "days_p50": q(0.5), "days_p90": q(0.9), "fails": fails}


def run(refresh: bool = False, get=None, pause: float = 0.4, shadow: dict[str, Any] | None = None,
        now: datetime | None = None) -> dict[str, Any]:
    series: dict[str, list[Candle]] = {}
    errors = {}
    for sym in MARKETS:
        try:
            bars = load(sym, refresh, get)
            series[sym] = [b for b in bars if b.ts >= int(START.timestamp()) - 400 * 86_400]
        except Exception as exc:  # noqa: BLE001
            errors[sym] = str(exc)[:100]
        if pause and refresh:
            time.sleep(pause)
    start = int(START.timestamp())
    all_trades, daily = [], {}
    per_market = {}
    for sym, bars in series.items():
        tr, d = donchian(bars, sym)
        tr = [t for t in tr if t["entry_ts"] >= start]
        d = {k: v for k, v in d.items() if k >= start}
        all_trades += tr
        for k, v in d.items():
            daily[k] = daily.get(k, 0.0) + v
        st = _stats([t["r"] for t in tr])
        per_market[sym] = {"label": MARKETS[sym], **st, "total_r": round(sum(t["r"] for t in tr), 1),
                           "median_risk_pct": round(statistics.median([t["risk_pct"] for t in tr]) * 100, 2) if tr else None}
    a = judge_a(all_trades, daily)
    a["per_market"] = per_market
    a["trades_per_week"] = round(len(all_trades) / ((max(daily) - min(daily)) / 86_400 / 7), 2) if daily else None
    holds = sorted((t["exit_ts"] - t["entry_ts"]) / 86_400 for t in all_trades)
    a["holding_days_median"] = holds[len(holds) // 2] if holds else None
    curve = sorted(daily.items())
    a["challenge"] = [challenge(curve, 250.0), challenge(curve, 500.0)]
    b = tsmom({s: bars for s, bars in series.items()})
    if shadow is not None and b.get("kept"):
        shadow_update(shadow, series, b["scale_10"], now or utcnow())
    return {"essai": 11, "updated_at": iso(utcnow()), "n_trials": N_TRIALS, "errors": errors,
            "period": [iso(datetime.fromtimestamp(min(daily), timezone.utc))[:10],
                       iso(datetime.fromtimestamp(max(daily), timezone.utc))[:10]] if daily else None,
            "donchian_55_20": a, "momentum_12m": b}


# ------------------------------------------------------------------ suivi en ombre du momentum (essai 11, B)
def shadow_update(state: dict[str, Any], series: dict[str, list[Candle]], scale: float, now: datetime) -> dict[str, Any]:
    """Une fois par mois : clôt le mois écoulé (rendement réel des poids annoncés, frais compris) et annonce les
    poids du nouveau mois (en % du capital, réglés pour 10 % de volatilité annuelle). Rien n'est rejoué après coup."""
    last_ts = max(b.ts for bars in series.values() for b in bars)
    month = datetime.fromtimestamp(last_ts, timezone.utc).strftime("%Y-%m")
    months = state.setdefault("months", [])
    if months and months[-1]["month"] == month:
        return state
    if months and months[-1].get("result") is None:
        prev = months[-1]
        r = 0.0
        for m, w in prev["weights"].items():
            bars = series.get(m) or []
            k = _index_before([b.ts for b in bars], last_ts + 1)
            if k is not None and prev["prices"].get(m):
                r += w * (bars[k].close / prev["prices"][m] - 1)
        prev["result"] = round(r, 5)
    weights = month_weights(series, last_ts + 1)
    if months:
        old = months[-1]["weights"]
        turnover = sum(abs(weights.get(m, 0.0) * scale - old.get(m, 0.0)) for m in set(weights) | set(old))
        months[-1]["result"] = round((months[-1].get("result") or 0.0) - turnover * COST / 2, 5)
    prices = {m: bars[-1].close for m, bars in series.items() if bars}
    months.append({"month": month, "decided_at": iso(now), "weights": {m: round(w * scale, 4) for m, w in weights.items()},
                   "prices": prices, "result": None})
    state.setdefault("since", month)
    done = [x["result"] for x in months if x.get("result") is not None]
    nav = 1.0
    for r in done:
        nav *= 1 + r
    state["nav"] = round(nav, 5)
    state["labels"] = MARKETS
    state["updated_at"] = iso(now)
    return state
