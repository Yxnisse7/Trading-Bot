"""Essai 15 (HYPOTHESES.md) : les autres règles codables de notre liste, 25 idées.

Trois familles, règles fixées avant tout calcul, sur les mêmes données et le même découpage que l'essai 14 :
- F : filtres qui retirent des trades du bot actuel ;
- G : autre gestion des mêmes entrées (sortie, stop, taille, limites du jour) ;
- S : nouveaux setups en 15 min.

Sans biais de futur : chaque décision n'utilise que des bougies clôturées. « Prouvé » avec la marge corrigée pour
254 essais.
"""
from __future__ import annotations

from bisect import bisect_left
from datetime import date, datetime, time, timezone
from typing import Any

from . import essai14 as e14
from . import indicators as ind
from . import strategies as sl
from .models import Candle

N_TRIALS = 254
ASSETS = e14.ASSETS
FUTURES = e14.FUTURES
OPEN_NY = e14.OPEN_NY
FILTERS = {
    "F1": "biais 1 h : prix ou pente de la moyenne 20 (1 h) contre le trade",
    "F2": "biais oscillateur 1 h : RSI 21 et stochastique du mauvais côté de 50",
    "F3": "tendance journalière : veille du mauvais côté de la moyenne 20 des jours",
    "F4": "bougie de contrôle : prix encore dans une bougie 15 min d'au moins 2 ATR",
    "F5": "marché plat : moyenne 20 (15 min) plate et RSI 21 entre 45 et 55",
    "F6": "range trop étroit : range de la dernière heure < 2 × (stop + frais)",
    "F8": "heures actives seulement (8:00-12:00 sauf 9:30-9:45, 14:00-16:00 New York)",
}
GESTION = {
    "G30": "objectif 3 R, 3 h au plus",
    "G31": "stop sous les 2 dernières bougies, objectif 1,5 fois ce risque",
    "G34": "stop suiveur sur 3 bougies, sans objectif, 3 h au plus",
    "G35": "objectif posé 7 % avant",
    "G36": "sortie quand le RSI 21 (5 min) repasse 50",
    "G37": "sortie sur bougie exceptionnelle (≥ 2,5 ATR dans le sens du trade)",
    "G38": "renfort : moitié à l'entrée, moitié à +1 R, stop à l'entrée, objectif 3 R",
    "G39": "demi-taille en marché indécis (F5 ou A2)",
    "G40": "3 trades par jour au plus, arrêt après 2 pertes",
}
SETUPS = {
    "S15": "repli du RSI vers 40-50 puis retour au-dessus de 50, dans la tendance 1 h",
    "S16": "divergence validée : creux plus bas sans survente, puis RSI au-dessus de 50",
    "S17": "divergence avortée : nouveau plus haut après une divergence, dans la tendance 1 h",
    "S25": "creux cassé puis repris en 2 bougies, dans la tendance 1 h",
    "S26": "retournement en 4 temps",
    "S27": "double creux, objectif la hauteur de la figure",
    "S28": "rebond sur un VWAP qui monte",
    "S21": "position par rapport au milieu de la 1re bougie, à la fin de la 1re heure",
    "S22": "écart d'ouverture : suivi si gros volume, comblé sinon",
}
INDICES = ("nasdaq", "sp500")


# ---------------------------------------------------------------- séries
def stoch_k(candles: list[Candle], n: int = 21, s: int = 3) -> list[float | None]:
    """%K lent : %K brut sur n bougies, lissé sur s."""
    raw: list[float | None] = [None] * len(candles)
    for i in range(n - 1, len(candles)):
        w = candles[i - n + 1: i + 1]
        hh, ll = max(x.high for x in w), min(x.low for x in w)
        raw[i] = 100 * (candles[i].close - ll) / (hh - ll) if hh > ll else 50.0
    out: list[float | None] = [None] * len(candles)
    for i in range(len(candles)):
        w = raw[max(0, i - s + 1): i + 1]
        if len(w) == s and all(x is not None for x in w):
            out[i] = sum(w) / s  # type: ignore[arg-type]
    return out


def _pivots(c: list[Candle], low: bool) -> list[bool]:
    out = [False] * len(c)
    for p in range(2, len(c) - 2):
        v = c[p].low if low else c[p].high
        side = [c[p + d].low if low else c[p + d].high for d in (-2, -1, 1, 2)]
        out[p] = all(v < x for x in side) if low else all(v > x for x in side)
    return out


class Ctx(e14.Ctx):
    def __init__(self, candles: list[Candle]):
        super().__init__(candles)
        self.h1_k = stoch_k(self.h1.c)
        closes: dict[date, float] = {}
        for x in candles:
            closes[datetime.fromtimestamp(x.ts, timezone.utc).date()] = x.close
        self.d_keys = sorted(closes)
        self.d_close = [closes[d] for d in self.d_keys]
        self.d_sma = ind.sma(self.d_close, 20)
        self.piv_lo = _pivots(self.m15.c, True)
        self.piv_hi = _pivots(self.m15.c, False)


def _ny(ts: int) -> tuple[int, int]:
    d = datetime.fromtimestamp(ts, sl.NY)
    return d.hour, d.minute


# ---------------------------------------------------------------- famille F
def removed_by(f: str, t: sl.Trade, ctx: Ctx, cost_pts: float) -> bool:
    sign = 1 if t.direction == "long" else -1
    T = t.entry_ts
    if f == "F1":
        h = ctx.h1.closed_at(T)
        if h is None or h < 3 or ctx.h1.sma[h] is None or ctx.h1.sma[h - 3] is None:
            return False
        return (ctx.h1.c[h].close - ctx.h1.sma[h]) * sign < 0 or (ctx.h1.sma[h] - ctx.h1.sma[h - 3]) * sign < 0
    if f == "F2":
        h = ctx.h1.closed_at(T)
        if h is None or ctx.h1.rsi[h] is None or ctx.h1_k[h] is None:
            return False
        return (ctx.h1.rsi[h] - 50) * sign < 0 and (ctx.h1_k[h] - 50) * sign < 0  # type: ignore[operator]
    if f == "F3":
        d = datetime.fromtimestamp(T, timezone.utc).date()
        k = bisect_left(ctx.d_keys, d) - 1
        if k < 0 or ctx.d_sma[k] is None:
            return False
        return (ctx.d_close[k] - ctx.d_sma[k]) * sign < 0  # type: ignore[operator]
    if f == "F4":
        k = ctx.m15.closed_at(T)
        if k is None or k < 8 or not ctx.m15.atr[k]:
            return False
        return any(b.high - b.low >= 2 * ctx.m15.atr[k] and b.low <= t.entry <= b.high  # type: ignore[operator]
                   for b in ctx.m15.c[k - 7: k + 1])
    if f == "F5":
        k = ctx.m15.closed_at(T)
        if k is None or k < 4 or ctx.m15.sma[k] is None or ctx.m15.sma[k - 4] is None or not ctx.m15.atr[k]:
            return False
        r = ctx.m15.rsi[k]
        flat = abs(ctx.m15.sma[k] - ctx.m15.sma[k - 4]) < 0.25 * ctx.m15.atr[k]  # type: ignore[operator]
        return flat and r is not None and 45 <= r <= 55
    if f == "F6":
        i = ctx.m5.closed_at(T)
        if i is None or i < 12:
            return False
        w = ctx.m5.c[i - 11: i + 1]
        return max(x.high for x in w) - min(x.low for x in w) < 2 * (t.risk + cost_pts)
    if f == "F8":
        hh, mm = _ny(T)
        m = hh * 60 + mm
        return not ((480 <= m < 720 and not 570 <= m < 585) or 840 <= m < 960)
    raise ValueError(f)


# ---------------------------------------------------------------- famille G
def _copy(t: sl.Trade, stop: float, tp: float | None, risk: float) -> sl.Trade:
    n = sl.Trade(t.strategy, t.asset, t.direction, t.entry_ts, t.exit_ts, t.entry, t.exit, risk, t.reason)
    n.stop, n.tp = stop, tp  # type: ignore[attr-defined]
    return n


def _hit(tp: float | None, b: Candle, long: bool) -> float | None:
    if tp is not None and ((b.high >= tp) if long else (b.low <= tp)):
        return max(tp, b.open) if long else min(tp, b.open)
    return None


def manage(g: str, t: sl.Trade, ctx: Ctx) -> sl.Trade | None:
    m5 = ctx.m5
    long = t.direction == "long"
    sign = 1 if long else -1
    tp0 = t.tp  # type: ignore[attr-defined]

    def with_tp(tp):
        return lambda j, b, st, lg: _hit(tp, b, lg)

    if g == "G30":
        n = _copy(t, t.stop, t.entry + sign * 3 * t.risk, t.risk)  # type: ignore[attr-defined]
        return e14._loop(ctx, n, 36, with_tp(n.tp))  # type: ignore[attr-defined]
    if g == "G31":
        i = m5.closed_at(t.entry_ts)
        if i is None or i < 1 or not m5.atr[i]:
            return None
        w = m5.c[i - 1: i + 1]
        stop = min(x.low for x in w) - 0.1 * m5.atr[i] if long else max(x.high for x in w) + 0.1 * m5.atr[i]  # type: ignore[operator]
        risk = (t.entry - stop) * sign
        if risk <= 0:
            return None
        n = _copy(t, stop, t.entry + sign * 1.5 * risk, risk)
        return e14._loop(ctx, n, 12, with_tp(n.tp))  # type: ignore[attr-defined]
    if g == "G34":
        def trail(j, b, st, lg):
            w = m5.c[j - 2: j + 1]
            v = min(x.low for x in w) if lg else max(x.high for x in w)
            st["stop"] = max(st["stop"], v) if lg else min(st["stop"], v)
            return None
        return e14._loop(ctx, t, 36, trail)
    if g == "G35":
        return e14._loop(ctx, t, 12, with_tp(t.entry + 0.93 * (tp0 - t.entry)))
    if g == "G36":
        def rsi_exit(j, b, st, lg):
            px = _hit(tp0, b, lg)
            if px is not None:
                return px
            r = m5.rsi[j]
            return b.close if r is not None and (r - 50) * (1 if lg else -1) < 0 else None
        return e14._loop(ctx, t, 12, rsi_exit)
    if g == "G37":
        def big(j, b, st, lg):
            px = _hit(tp0, b, lg)
            if px is not None:
                return px
            a = m5.atr[j]
            if a and (b.close - b.open) * (1 if lg else -1) > 0 and b.high - b.low >= 2.5 * a:
                return b.close
            return None
        return e14._loop(ctx, t, 12, big)
    if g == "G38":
        tp = t.entry + sign * 3 * t.risk
        one = t.entry + sign * t.risk
        extra: dict[str, float | None] = {"add": None}

        def pyramid(j, b, st, lg):
            if extra["add"] is None and ((b.high >= one) if lg else (b.low <= one)):
                extra["add"] = max(one, b.open) if lg else min(one, b.open)
                st["stop"] = t.entry
            return _hit(tp, b, lg)
        out = e14._loop(ctx, t, 36, pyramid)
        if out is None:
            return None
        a = extra["add"]
        # moitié entrée à `entry`, moitié à `a` : sortie équivalente pour une taille complète entrée à `entry`
        px = (out.exit + t.entry) / 2 if a is None else out.exit - (a - t.entry) / 2
        return sl.Trade(t.strategy, t.asset, t.direction, t.entry_ts, out.exit_ts, t.entry, px, t.risk, "")
    raise ValueError(g)


def half_size(trades: list[sl.Trade], ctx: Ctx) -> list[sl.Trade]:
    """G39 : taille divisée par deux (R et frais en R divisés par deux) quand F5 ou A2 aurait retiré le trade."""
    out = []
    for t in trades:
        weak = removed_by("F5", t, ctx, 0.0) or e14.removed_by("A2", t, ctx, None)
        out.append(_copy(t, t.stop, t.tp, 2 * t.risk) if weak else t)  # type: ignore[attr-defined]
    return out


def day_limits(trades: list[sl.Trade]) -> list[sl.Trade]:
    """G40 : 3 trades par jour de New York au plus, plus aucun après 2 pertes dans la journée."""
    out, count, losses = [], {}, {}
    for t in sorted(trades, key=lambda x: x.entry_ts):
        d = datetime.fromtimestamp(t.entry_ts, sl.NY).date()
        lost = sum(1 for x in out if datetime.fromtimestamp(x.entry_ts, sl.NY).date() == d
                   and x.exit_ts <= t.entry_ts and x.gross_points() < 0)
        if count.get(d, 0) >= 3 or lost >= 2:
            continue
        count[d] = count.get(d, 0) + 1
        out.append(t)
    return out


# ---------------------------------------------------------------- famille S (15 min)
def _run(asset: str, name: str, f: e14.Frame, k: int, direction: str, entry: float, stop: float,
         target: float | None, exit_ts: int | None = None) -> tuple[sl.Trade | None, int]:
    """Entrée à la clôture de la bougie k, règles communes de la famille B de l'essai 14."""
    long = direction == "long"
    risk = (entry - stop) * (1 if long else -1)
    ok, close_ts = e14._limits(asset, f.c[k].ts)
    if exit_ts is not None:
        close_ts = exit_ts if close_ts is None else min(close_ts, exit_ts)
    if not ok or risk <= 0 or not e14._risk_ok(risk, f.atr[k]):
        return None, k
    if close_ts is not None and f.c[k].ts + f.sec >= close_ts:
        return None, k
    tgt = target if target is not None else entry + (3 * risk if long else -3 * risk)
    px, j, why = sl.simulate(f.c, k, direction, entry, stop, target=tgt, exit_ts=close_ts,
                             max_bars=16, bar_seconds=f.sec)
    if why == "fin des données":
        return None, len(f.c)
    return sl.Trade(name, asset, direction, f.c[k].ts + f.sec, f.c[j].ts + f.sec, entry, px, risk, why), j


def _vwap15(asset: str, ctx: Ctx) -> tuple[list[float | None], list[int | None]]:
    """VWAP de séance à la clôture de chaque bougie 15 min (calculé sur le 5 min) et début de séance."""
    m5, m15 = ctx.m5.c, ctx.m15
    vw5: list[float | None] = [None] * len(m5)
    st5: list[int | None] = [None] * len(m5)
    start, pv, vol = None, 0.0, 0.0
    for i, b in enumerate(m5):
        d = datetime.fromtimestamp(b.ts, sl.NY if asset != "bitcoin" else timezone.utc).date()
        if asset == "bitcoin":
            s0, s1 = int(datetime.combine(d, time(0, 0), timezone.utc).timestamp()), None
        else:
            hh, mm = OPEN_NY[asset]
            s0 = int(datetime.combine(d, time(hh, mm), sl.NY).timestamp())
            s1 = int(datetime.combine(d, time(16, 0), sl.NY).timestamp())
        if b.ts < s0 or (s1 is not None and b.ts >= s1):
            start = None
            continue
        if start != s0:
            start, pv, vol = s0, 0.0, 0.0
        pv += (b.high + b.low + b.close) / 3 * b.volume
        vol += b.volume
        vw5[i], st5[i] = (pv / vol if vol > 0 else None), s0
    vw: list[float | None] = [None] * len(m15.c)
    st: list[int | None] = [None] * len(m15.c)
    for k, b in enumerate(m15.c):
        i = ctx.m5.closed_at(b.ts + 900)
        if i is not None and m5[i].ts + 300 == b.ts + 900:
            vw[k], st[k] = vw5[i], st5[i]
    return vw, st


def setup_trades(name: str, asset: str, ctx: Ctx) -> list[sl.Trade]:
    if name == "S21":
        return _s21(asset, ctx)
    if name == "S22":
        return _s22(asset, ctx)
    f = ctx.m15
    c, r = f.c, f.rsi
    vw, vst = _vwap15(asset, ctx) if name == "S28" else ([], [])
    out: list[sl.Trade] = []
    k, n = 45, len(c)
    while k < n - 2:
        T = c[k].ts + f.sec
        atr, sma = f.atr[k], f.sma[k]
        trade, nxt = None, k
        if not atr or r[k] is None or r[k - 1] is None:
            k += 1
            continue
        for long in (True, False):
            if trade is not None:
                break
            sg = 1 if long else -1
            d = "long" if long else "short"
            lo = (lambda x: x.low) if long else (lambda x: x.high)      # côté du stop
            hi = (lambda x: x.high) if long else (lambda x: x.low)      # côté de l'objectif
            better = (lambda a, b: a > b) if long else (lambda a, b: a < b)
            ext_lo = min if long else max
            ext_hi = max if long else min
            rs = [x if long else (None if x is None else 100 - x) for x in r[k - 30: k + 1]]  # RSI vu « à l'achat »
            if any(x is None for x in rs):
                continue
            if name == "S15":
                if ctx.trend_1h(T) != d:
                    continue
                if 40 <= rs[-2] <= 50 < rs[-1] and min(rs[-7:]) >= 40 and max(rs[-13:-1]) > 55:
                    stop = ext_lo(lo(x) for x in c[k - 4: k + 1])
                    trade, nxt = _run(asset, name, f, k, d, c[k].close, stop, None)
            elif name == "S16":
                if not (rs[-2] <= 50 < rs[-1]):
                    continue
                p2 = min(range(k - 30, k), key=lambda p: lo(c[p]) * sg)
                if rs[p2 - (k - 30)] <= 30 or max(rs[p2 - (k - 30): -1]) > 50 or p2 - 33 < 0:
                    continue
                p1s = [p for p in range(p2 - 30, p2 - 2) if r[p] is not None
                       and (r[p] if long else 100 - r[p]) < 30  # type: ignore[operator]
                       and ext_lo(lo(x) for x in c[p - 19: p + 1]) == lo(c[p])]
                if not p1s:
                    continue
                p1 = min(p1s, key=lambda p: lo(c[p]) * sg)
                if better(lo(c[p1]), lo(c[p2])):
                    trade, nxt = _run(asset, name, f, k, d, c[k].close, lo(c[p2]), None)
            elif name == "S17":
                if ctx.trend_1h(T) != d:
                    continue
                p2 = max(range(k - 10, k), key=lambda p: hi(c[p]) * sg)
                if p2 < 52 or ext_hi(hi(x) for x in c[p2 - 19: p2 + 1]) != hi(c[p2]):
                    continue
                if not better(c[k].close, hi(c[p2])) or any(better(x.close, hi(c[p2])) for x in c[p2 + 1: k]):
                    continue
                rv = (lambda p: r[p] if long else 100 - r[p])  # type: ignore[operator]
                p1s = [p for p in range(p2 - 30, p2 - 2) if r[p] is not None
                       and ext_hi(hi(x) for x in c[p - 19: p + 1]) == hi(c[p]) and better(hi(c[p2]), hi(c[p]))]
                if p1s and any(rv(p) > rv(p2) for p in p1s):
                    stop = ext_lo(lo(x) for x in c[k - 4: k + 1])
                    trade, nxt = _run(asset, name, f, k, d, c[k].close, stop, None)
            elif name == "S25":
                if ctx.trend_1h(T) != d:
                    continue
                for m in (k - 1, k - 2):
                    L = ext_lo(lo(x) for x in c[m - 10: m])
                    broke = better(L, lo(c[m])) and not better(c[m].close, L)
                    first = not any(better(x.close, L) for x in c[m + 1: k])
                    if broke and first and better(c[k].close, L):
                        stop = ext_lo(lo(x) for x in c[m: k + 1]) - sg * 0.1 * atr
                        trade, nxt = _run(asset, name, f, k, d, c[k].close, stop, None)
                        break
            elif name == "S26":
                piv = ctx.piv_lo if long else ctx.piv_hi
                for x in range(k - 1, k - 31, -1):
                    if f.sma[x] is None or f.sma[x - 1] is None or f.sma[x - 11] is None:
                        break
                    crossed = better(c[x].close, f.sma[x]) and not better(c[x - 1].close, f.sma[x - 1])
                    if not crossed:
                        continue
                    falling = better(f.sma[x - 11], f.sma[x - 1])
                    if not falling:
                        break
                    tl = min(range(x - 20, x + 1), key=lambda p: lo(c[p]) * sg)
                    ps = [p for p in range(x + 1, k - 1) if piv[p] and better(lo(c[p]), lo(c[tl]))]
                    if ps:
                        p = ps[-1]
                        H = ext_hi(hi(y) for y in c[tl: p + 1])
                        if better(c[k].close, H) and not any(better(y.close, H) for y in c[p + 1: k]):
                            trade, nxt = _run(asset, name, f, k, d, c[k].close, lo(c[p]), None)
                    break
            elif name == "S27":
                piv = ctx.piv_lo if long else ctx.piv_hi
                p2s = [p for p in range(k - 10, k - 1) if piv[p]]
                for p2 in reversed(p2s):
                    p1s = [p for p in range(p2 - 30, p2 - 4) if p >= 0 and piv[p] and abs(lo(c[p]) - lo(c[p2])) <= 0.3 * atr]
                    if not p1s:
                        continue
                    p1 = p1s[-1]
                    neck = ext_hi(hi(y) for y in c[p1 + 1: p2])
                    if better(c[k].close, neck) and not any(better(y.close, neck) for y in c[p2 + 1: k]):
                        stop = ext_lo(lo(c[p1]), lo(c[p2]))
                        # objectif = ligne de cou + hauteur ; toujours < 1 R avec ce stop (voir le journal)
                        trade, nxt = _run(asset, name, f, k, d, c[k].close, stop, neck + (neck - stop))
                    break
            elif name == "S28":
                v, s0 = vw[k], vst[k]
                if v is None or s0 is None or T - s0 < 1800:
                    continue
                kb = k - 4
                if kb < 0 or vst[kb] != s0 or vw[kb] is None or not better(v, vw[kb]):
                    continue
                touched = (c[k].low <= v) if long else (c[k].high >= v)
                if touched and better(c[k].close, v):
                    stop = lo(c[k]) - sg * 0.1 * atr
                    risk = (c[k].close - stop) * sg
                    end = (s0 + 86400) if asset == "bitcoin" else None
                    trade, nxt = _run(asset, name, f, k, d, c[k].close, stop, c[k].close + sg * 2 * risk, end)
        if trade is not None:
            out.append(trade)
        k = max(k, nxt) + 1
    return out


def _session_bars(ctx: Ctx, asset: str, d: date, count: int) -> int | None:
    hh, mm = OPEN_NY[asset]
    start = int(datetime.combine(d, time(hh, mm), sl.NY).timestamp())
    m5 = ctx.m5
    i0 = m5.closed_at(start + 300)
    if i0 is None or m5.c[i0].ts != start or i0 + count > len(m5.c):
        return None
    if m5.c[i0 + count - 1].ts != start + 300 * (count - 1):
        return None
    return i0


def _s21(asset: str, ctx: Ctx) -> list[sl.Trade]:
    if asset not in OPEN_NY:
        return []
    bars, out = ctx.m5.c, []
    for d in sl._days(bars):
        i0 = _session_bars(ctx, asset, d, 13)
        if i0 is None:
            continue
        hour = bars[i0: i0 + 12]
        mid = (bars[i0].high + bars[i0].low) / 2
        j = i0 + 11
        long = bars[j].close > mid
        entry = bars[j].close
        stop = min(x.low for x in hour) if long else max(x.high for x in hour)
        risk = abs(entry - stop)
        k15 = ctx.m15.closed_at(bars[j].ts + 300)
        ok, close_ts = e14._limits(asset, bars[j].ts)
        if not ok or k15 is None or not e14._risk_ok(risk, ctx.m15.atr[k15]):
            continue
        side = "long" if long else "short"
        px, jj, why = sl.simulate(bars, j, side, entry, stop, exit_ts=close_ts)
        if why != "fin des données":
            out.append(sl.Trade("S21", asset, side, bars[j].ts + 300, bars[jj].ts + 300, entry, px, risk, why))
    return out


def _s22(asset: str, ctx: Ctx) -> list[sl.Trade]:
    if asset not in INDICES:
        return []
    bars, out, vols = ctx.m5.c, [], []
    for d in sl._days(bars):
        i0 = _session_bars(ctx, asset, d, 2)
        if i0 is None:
            continue
        prev = sl._prev_session(d)
        pc_ts = int(datetime.combine(prev, time(15, 55), sl.NY).timestamp())
        ip = ctx.m5.closed_at(pc_ts + 300)
        b = bars[i0]
        avg = sum(vols[-20:]) / 20 if len(vols) >= 20 else None
        vols.append(b.volume)
        if ip is None or bars[ip].ts != pc_ts or avg is None or avg <= 0:
            continue
        pc = bars[ip].close
        gap = (b.open - pc) / pc
        if abs(gap) < 0.003:
            continue
        up = gap > 0
        long = up if b.volume >= 1.5 * avg else not up
        entry = b.close
        stop = b.low if long else b.high
        risk = abs(entry - stop)
        k15 = ctx.m15.closed_at(b.ts + 300)
        ok, close_ts = e14._limits(asset, b.ts)
        if not ok or risk <= 0 or k15 is None or not e14._risk_ok(risk, ctx.m15.atr[k15]):
            continue
        side = "long" if long else "short"
        tgt = entry + (2 * risk if long else -2 * risk)
        px, jj, why = sl.simulate(bars, i0, side, entry, stop, target=tgt, exit_ts=close_ts)
        if why != "fin des données":
            out.append(sl.Trade("S22", asset, side, b.ts + 300, bars[jj].ts + 300, entry, px, risk, why))
    return out


# ---------------------------------------------------------------- verdict et information
def verdict(trades: list[sl.Trade], cost_pct: float, tcost: tuple[float, float] | None) -> dict[str, Any]:
    disc = sl.evaluate(trades, cost_pct, tcost, start_ts=e14.SPLIT)
    conf = sl.evaluate(trades, cost_pct, tcost, end_ts=e14.SPLIT)
    both = sl.evaluate(trades, cost_pct, tcost)
    ok_d, ok_c = sl.discovery_pass(disc), sl.confirmation_pass(conf)
    status = ("prouvé" if sl.proven(both, N_TRIALS) else "validé") if ok_d and ok_c else (
        "écarté (découverte)" if not ok_d else "écarté (confirmation)")
    return {"discovery": disc, "confirmation": conf, "all": both, "status": status}


def risk_curve(rows: list[tuple[int, float]], risk_pct: float) -> dict[str, float]:
    """Capital composé (départ 1) et pire baisse en %, trades (heure de sortie, R net) dans l'ordre."""
    eq, peak, worst = 1.0, 1.0, 0.0
    for _, rr in sorted(rows):
        eq *= max(0.0, 1 + risk_pct / 100 * rr)
        peak = max(peak, eq)
        worst = max(worst, 1 - eq / peak)
    return {"final": round(eq, 4), "max_drawdown_pct": round(100 * worst, 1)}
