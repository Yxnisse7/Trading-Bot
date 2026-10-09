"""Essai 16 (HYPOTHESES.md) : le swing, positions de 2 à 5 jours.

Tendance journalière et 1 h dans le même sens, repli du RSI 21 vers la zone neutre en 15 min, stop sous le
2e creux, trois façons de sortir (W1 objectif 3 R, W2 deux unités, W3 stop suiveur seul). Règles fixées avant
tout calcul ; décisions sur bougies clôturées seulement. Frais du bot (tout courtier), pas de Topstep (qui
interdit de garder une position la nuit). « Prouvé » avec la marge corrigée pour 266 essais.
"""
from __future__ import annotations

from bisect import bisect_left
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from . import essai14 as e14
from . import essai15 as e15
from . import strategies as sl

N_TRIALS = 266
ASSETS = e14.ASSETS
VARIANTS = {
    "W1": "une sortie : objectif 3 R, stop fixe",
    "W2": "deux unités : moitié à +1 R, stop à l'entrée puis sous les creux 1 h",
    "W3": "stop suiveur seul sous les creux 1 h, sans objectif",
}
PARIS = ZoneInfo("Europe/Paris")
MAX_HOLD = 5 * 86400
# Estimation IC Markets Raw (spread + commission + 1 tick, en points), pour information seulement
IC_COST_PTS = {"gold": 0.25, "nasdaq": 1.25, "sp500": 0.75}


class Ctx(e15.Ctx):
    def __init__(self, candles):
        super().__init__(candles)
        self.h1_piv_lo = e15._pivots(self.h1.c, True)
        self.h1_piv_hi = e15._pivots(self.h1.c, False)


def _daily_trend(ctx: Ctx, T: int) -> str | None:
    d = datetime.fromtimestamp(T, timezone.utc).date()
    k = bisect_left(ctx.d_keys, d) - 1
    if k < 5 or ctx.d_sma[k] is None or ctx.d_sma[k - 5] is None:
        return None
    c, m, m5 = ctx.d_close[k], ctx.d_sma[k], ctx.d_sma[k - 5]
    if c > m and m > m5:  # type: ignore[operator]
        return "long"
    if c < m and m < m5:  # type: ignore[operator]
        return "short"
    return None


def _entry_ok(asset: str, T: int) -> bool:
    p = datetime.fromtimestamp(T, PARIS)
    if not 8 <= p.hour < 22:
        return False
    if asset != "bitcoin":
        ny = datetime.fromtimestamp(T, sl.NY)
        if ny.weekday() >= 5 or (ny.weekday() == 4 and ny.hour >= 12):
            return False
    return True


def _friday_close(asset: str, end_ts: int) -> bool:
    if asset == "bitcoin":
        return False
    ny = datetime.fromtimestamp(end_ts, sl.NY)
    return ny.weekday() >= 5 or (ny.weekday() == 4 and ny.hour >= 16)


def signals(asset: str, ctx: Ctx):
    """Entrées candidates (k, direction, entrée, stop), dans l'ordre ; le suivi impose une position à la fois."""
    f, h = ctx.m15, ctx.h1
    c, r = f.c, f.rsi
    for k in range(45, len(c) - 1):
        T = c[k].ts + f.sec
        if r[k] is None or r[k - 1] is None or not f.atr[k] or not _entry_ok(asset, T):
            continue
        d = _daily_trend(ctx, T)
        if d is None or ctx.trend_1h(T) != d:
            continue
        hk = h.closed_at(T)
        if hk is None or h.sma[hk] is None or not h.atr[hk]:
            continue
        if abs(h.c[hk].close - h.sma[hk]) > 2 * h.atr[hk]:  # type: ignore[operator]
            continue
        long = d == "long"
        rs = [x if long else 100 - x for x in r[k - 12: k + 1] if x is not None]
        if len(rs) < 13 or not (40 <= rs[-2] <= 50 < rs[-1] and min(rs[-7:]) >= 40 and max(rs[:-1]) > 55):
            continue
        piv = ctx.piv_lo if long else ctx.piv_hi
        ps = [p for p in range(k - 40, k - 1) if piv[p]][-2:]
        if len(ps) == 2:
            ext = min(c[p].low for p in ps) if long else max(c[p].high for p in ps)
            stop = ext - 0.1 * f.atr[k] if long else ext + 0.1 * f.atr[k]  # type: ignore[operator]
        else:
            stop = min(x.low for x in c[k - 9: k + 1]) if long else max(x.high for x in c[k - 9: k + 1])
        risk = (c[k].close - stop) * (1 if long else -1)
        if not 0.3 * h.atr[hk] <= risk <= 3 * h.atr[hk]:  # type: ignore[operator]
            continue
        yield k, d, c[k].close, stop


def follow(variant: str, asset: str, ctx: Ctx, k: int, direction: str, entry: float, stop: float
           ) -> tuple[sl.Trade | None, int]:
    f, h = ctx.m15, ctx.h1
    c = f.c
    long = direction == "long"
    sg = 1 if long else -1
    risk = (entry - stop) * sg
    ets = c[k].ts + f.sec
    target = entry + sg * 3 * risk if variant == "W1" else None
    one = entry + sg * risk
    half = None
    trail = variant == "W3"
    piv = ctx.h1_piv_lo if long else ctx.h1_piv_hi

    def done(px: float, j: int, why: str):
        if half is not None:
            px = (half + px) / 2
        return sl.Trade(variant, asset, direction, ets, c[j].ts + f.sec, entry, px, risk, why), j

    for j in range(k + 1, len(c)):
        b = c[j]
        if b.ts - c[j - 1].ts > 4 * 86400:
            return done(c[j - 1].close, j - 1, "trou")
        if (b.low <= stop) if long else (b.high >= stop):
            return done(min(stop, b.open) if long else max(stop, b.open), j, "stop")
        if target is not None and ((b.high >= target) if long else (b.low <= target)):
            return done(max(target, b.open) if long else min(target, b.open), j, "objectif")
        if variant == "W2" and half is None and ((b.high >= one) if long else (b.low <= one)):
            half = max(one, b.open) if long else min(one, b.open)
            stop = max(stop, entry) if long else min(stop, entry)
            trail = True
        end = b.ts + f.sec
        if trail:
            hk = h.closed_at(end)
            if hk is not None:
                ps = [p for p in range(max(0, hk - 120), hk - 1) if piv[p] and h.c[p].ts >= ets and h.atr[p + 2]]
                if ps:
                    p = ps[-1]
                    a = h.atr[p + 2]
                    lvl = h.c[p].low - 0.1 * a if long else h.c[p].high + 0.1 * a  # type: ignore[operator]
                    stop = max(stop, lvl) if long else min(stop, lvl)
        if end - ets >= MAX_HOLD:
            return done(b.close, j, "durée")
        if _friday_close(asset, end):
            return done(b.close, j, "vendredi")
    return None, len(c)


def trades(variant: str, asset: str, ctx: Ctx) -> list[sl.Trade]:
    out: list[sl.Trade] = []
    busy = -1
    for k, d, entry, stop in signals(asset, ctx):
        if k <= busy:
            continue
        t, j = follow(variant, asset, ctx, k, d, entry, stop)
        if t is None:
            break
        out.append(t)
        busy = j
    return out


def verdict(tr: list[sl.Trade], cost_pct: float, asset: str) -> dict[str, Any]:
    disc = sl.evaluate(tr, cost_pct, None, start_ts=e14.SPLIT)
    conf = sl.evaluate(tr, cost_pct, None, end_ts=e14.SPLIT)
    both = sl.evaluate(tr, cost_pct, None)
    ok_d, ok_c = sl.discovery_pass(disc), sl.confirmation_pass(conf)
    status = ("prouvé" if sl.proven(both, N_TRIALS) else "validé") if ok_d and ok_c else (
        "écarté (découverte)" if not ok_d else "écarté (confirmation)")
    out = {"discovery": disc, "confirmation": conf, "all": both, "status": status}
    if asset in IC_COST_PTS and tr:
        rs = [(t.gross_points() - IC_COST_PTS[asset]) / t.risk for t in tr]
        out["info_ic_markets_mean_r"] = round(sum(rs) / len(rs), 4)
    if tr:
        out["mean_hold_hours"] = round(sum(t.exit_ts - t.entry_ts for t in tr) / len(tr) / 3600, 1)
        out["exits"] = {w: sum(1 for t in tr if t.reason == w) for w in sorted({t.reason for t in tr})}
    return out
