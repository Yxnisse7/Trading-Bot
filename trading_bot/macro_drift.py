"""Essai 12 (HYPOTHESES.md) : la réaction du marché à une annonce macro continue-t-elle pendant des heures ?

Faute d'historique gratuit des prévisions (consensus), la surprise est lue dans la réaction du marché : sens du
mouvement entre la clôture de la bougie 5 min juste avant l'annonce et 30 min après. Entrée à ce moment dans le
sens de la réaction, sortie à 15:00 heure de Chicago (même jour) ; pour information, sortie le lendemain à 15:00.
Résultat en unités d'ATR 1 h (14) à l'entrée, frais Topstep compris. H2 : filtre pour `donchian_day` sur l'or.
"""
from __future__ import annotations

import math
import statistics
from datetime import datetime, timezone
from typing import Any

from . import indicators as ind
from . import macro_history as mh
from .models import Candle, iso, utcnow

ASSETS = ("gold", "nasdaq", "sp500", "euro")
SPLIT = int(datetime(2025, 10, 1, tzinfo=timezone.utc).timestamp())
N_TRIALS = 100


def _close_at_or_before(index: dict[int, int], candles: list[Candle], ts_end: int) -> tuple[float, int] | None:
    """Clôture de la dernière bougie 5 min finie au plus tard à `ts_end` (cherche jusqu'à 2 h avant)."""
    for back in range(0, 25):
        k = index.get(ts_end - 300 * (back + 1))
        if k is not None:
            return candles[k].close, candles[k].ts + 300
    return None


def reactions(candles: list[Candle], asset: str, events: list[tuple[int, str]] | None = None) -> list[dict[str, Any]]:
    from . import strategies as sl
    from .topstep import FEES, PRODUCTS
    index = {c.ts: i for i, c in enumerate(candles)}
    hours = ind.resample(candles, 60)
    atr_h = ind.atr(hours, 14)
    hour_ts = [h.ts for h in hours]
    fee = FEES.get(asset)
    cost_pts = (sum(fee) / PRODUCTS[asset][1]) if fee and asset in PRODUCTS else 0.0
    out = []
    for t_ev, kind in events or mh.events():
        pre = index.get(t_ev - 300)
        post = index.get(t_ev + 1500)                 # bougie 5 min qui finit 30 min après l'annonce
        if pre is None or post is None:
            continue
        p0, entry = candles[pre].close, candles[post].close
        if entry == p0:
            continue
        d = 1 if entry > p0 else -1
        entry_ts = t_ev + 1800
        from bisect import bisect_left
        k = bisect_left(hour_ts, entry_ts - 3600) - 1    # dernière bougie 1 h finie avant l'entrée
        atr = atr_h[k] if 0 <= k < len(atr_h) else None
        if not atr:
            continue
        close_a = sl.session_close_ts(entry_ts)
        if close_a is None:
            continue
        close_b = sl.session_close_ts(close_a + 3 * 3600)
        ex_a = _close_at_or_before(index, candles, close_a)
        ex_b = _close_at_or_before(index, candles, close_b) if close_b else None
        if ex_a is None or ex_a[1] <= entry_ts:
            continue
        row = {"ts": t_ev, "at": iso(datetime.fromtimestamp(t_ev, timezone.utc)), "kind": kind, "dir": d,
               "reaction_atr": round(abs(entry - p0) / atr, 3), "entry": entry, "atr": atr, "close_a_ts": close_a,
               "r_day": round((d * (ex_a[0] - entry) - cost_pts) / atr, 4)}
        if ex_b and ex_b[1] > ex_a[1]:
            row["r_next"] = round((d * (ex_b[0] - entry) - cost_pts) / atr, 4)
        out.append(row)
    return out


def summary(rs: list[float]) -> dict[str, Any]:
    n = len(rs)
    if n < 2:
        return {"n": n, "mean": rs[0] if rs else None, "t": None}
    m, sd = statistics.mean(rs), statistics.stdev(rs)
    return {"n": n, "mean": round(m, 4), "t": round(m / (sd / math.sqrt(n)), 2) if sd else None,
            "win_rate": round(sum(r > 0 for r in rs) / n, 3)}


def judge(rows: list[dict[str, Any]]) -> dict[str, Any]:
    day = [r["r_day"] for r in rows]
    y1 = [r["r_day"] for r in rows if r["ts"] < SPLIT]
    y2 = [r["r_day"] for r in rows if r["ts"] >= SPLIT]
    s_all, s1, s2 = summary(day), summary(y1), summary(y2)
    kept = bool(s_all["n"] >= 20 and (s_all["mean"] or 0) > 0 and (s_all["t"] or 0) >= 2
                and (s1["mean"] or 0) > 0 and (s2["mean"] or 0) > 0)
    med = statistics.median([r["reaction_atr"] for r in rows]) if rows else 0
    strong = [r["r_day"] for r in rows if r["reaction_atr"] >= med]
    by_kind = {k: summary([r["r_day"] for r in rows if r["kind"] == k]) for k in ("nfp", "cpi", "fomc")}
    return {"kept": kept, "all": s_all, "year1": s1, "year2": s2, "strong": summary(strong),
            "next_day": summary([r["r_next"] for r in rows if "r_next" in r]), "by_kind": by_kind}


def donchian_filter(candles: list[Candle], rows: list[dict[str, Any]]) -> dict[str, Any]:
    """H2 : trades `donchian_day` sur l'or ouverts entre la réaction (annonce + 30 min) et la fin de séance."""
    from . import strategies as sl
    from .topstep import FEES, PRODUCTS
    tcost = (sum(FEES["gold"]), PRODUCTS["gold"][1])
    trades = [t for t in sl.donchian_day(candles, "gold") if t.reason != "fin des données"]
    aligned, opposed, other = [], [], []
    for t in trades:
        r = sl.trade_rs(t, 0.0, tcost)["net_topstep"]
        ev = next((e for e in rows if e["ts"] + 1800 <= t.entry_ts <= e["close_a_ts"]), None)
        if ev is None:
            other.append(r)
        elif (t.direction == "long") == (ev["dir"] > 0):
            aligned.append(r)
        else:
            opposed.append(r)
    a, o = summary(aligned), summary(opposed)
    propose = bool(a["n"] >= 15 and o["n"] >= 15 and (a["mean"] or 0) - (o["mean"] or 0) >= 0.3)
    return {"aligned": a, "opposed": o, "other_days": summary(other), "propose_filter": propose}


def run(store) -> dict[str, Any]:
    out: dict[str, Any] = {"essai": 12, "updated_at": iso(utcnow()), "n_trials": N_TRIALS, "assets": {}}
    gold_rows = None
    for key in ASSETS:
        candles = store.load_history(key)
        if not candles:
            out["assets"][key] = {"error": "pas d'historique"}
            continue
        rows = reactions(candles, key)
        out["assets"][key] = {**judge(rows), "events": rows}
        if key == "gold":
            gold_rows = rows
            out["donchian_filter"] = donchian_filter(candles, rows)
    return out
