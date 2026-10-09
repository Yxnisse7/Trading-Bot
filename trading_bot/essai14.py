"""Essai 14 (HYPOTHESES.md) : entrer sur repli plutôt qu'après l'accélération.

Trois familles, règles fixées avant tout calcul :
- A : filtres qui retirent des trades du bot actuel (rejoué sur l'historique long) ;
- C : autres sorties sur les mêmes entrées du bot ;
- B : nouveaux setups sur bougies de 15 min.

Sans biais de futur : chaque décision n'utilise que des bougies clôturées. Verdict par cellule (idée × actif)
avec les critères de l'essai 3 (découverte puis confirmation), « prouvé » avec la marge corrigée pour 157 essais.
"""
from __future__ import annotations

from bisect import bisect_right
from datetime import date, datetime, time, timezone
from typing import Any

from . import indicators as ind
from . import strategies as sl
from .models import Candle, parse_iso

N_TRIALS = 157
SPLIT = int(datetime(2025, 9, 28, tzinfo=timezone.utc).timestamp())
ASSETS = ("gold", "nasdaq", "sp500", "bitcoin")
FUTURES = {"gold", "nasdaq", "sp500"}
FILTERS = {
    "A1": "étirement : clôture à plus de 1,5 ATR de la moyenne 20 (5 min)",
    "A2": "journée sans direction : dans le range de la veille et moyenne 20 (15 min) plate",
    "A3": "obstacle : plus haut / plus bas de la veille entre l'entrée et l'objectif",
    "A4": "marge : RSI 21 en 1 h au-delà de 65 (achat) ou 35 (vente)",
    "A5": "indices : l'autre indice du mauvais côté de sa moyenne 20 (15 min)",
}
EXITS = {
    "C11": "deux moitiés : moitié à +1 R, stop à l'entrée puis suiveur sur 3 bougies, 3 h au plus",
    "C12": "stop temps : sortie après 30 min si +0,5 R jamais atteint",
    "C13": "sortie à la clôture d'une bougie 5 min du mauvais côté de la moyenne 20",
}
SETUPS = {
    "B6": "repli de 3 à 6 bougies 15 min près de la moyenne 20, dans la tendance 1 h",
    "B7": "cassure du canal 20 bougies 15 min avec un volume au moins double",
    "B8": "bougie la plus étroite des 7, près de la moyenne 20, dans la tendance 1 h",
    "B9": "cassure ratée sans volume, retour vers l'autre borne",
    "B10": "cassure du range des 15 premières minutes, prix déjà hors du range de la veille",
}
OPEN_NY = {"nasdaq": (9, 30), "sp500": (9, 30), "gold": (8, 20)}


# ---------------------------------------------------------------- séries
class Frame:
    """Bougies d'une unité de temps avec moyenne 20, ATR 14 et RSI 21, indexées par début de bougie."""

    def __init__(self, candles: list[Candle], seconds: int):
        self.c, self.sec = candles, seconds
        self.ts = [x.ts for x in candles]
        closes = [x.close for x in candles]
        self.sma = ind.sma(closes, 20)
        self.atr = ind.atr(candles, 14)
        self.rsi = ind.rsi(closes, 21)

    def closed_at(self, t: int) -> int | None:
        """Dernière bougie clôturée à l'instant t (fin ≤ t)."""
        k = bisect_right(self.ts, t - self.sec) - 1
        return k if k >= 0 else None


class Ctx:
    def __init__(self, candles: list[Candle]):
        self.m5 = Frame(candles, 300)
        self.m15 = Frame(ind.resample(candles, 15), 900)
        self.h1 = Frame(ind.resample(candles, 60), 3600)
        days: dict[date, list[float]] = {}
        for c in candles:
            d = datetime.fromtimestamp(c.ts, timezone.utc).date()
            r = days.setdefault(d, [c.high, c.low])
            r[0], r[1] = max(r[0], c.high), min(r[1], c.low)
        self.day_keys = sorted(days)
        self.days = days

    def prev_day(self, t: int) -> tuple[float, float] | None:
        """Plus haut / plus bas de la journée UTC de cotation précédente."""
        d = datetime.fromtimestamp(t, timezone.utc).date()
        k = bisect_right(self.day_keys, d) - 1
        while k >= 0 and self.day_keys[k] >= d:
            k -= 1
        if k < 0:
            return None
        hi, lo = self.days[self.day_keys[k]]
        return hi, lo

    def trend_1h(self, t: int) -> str | None:
        h = self.h1.closed_at(t)
        if h is None or h < 3 or self.h1.sma[h] is None or self.h1.sma[h - 3] is None:
            return None
        c, m, m3 = self.h1.c[h].close, self.h1.sma[h], self.h1.sma[h - 3]
        if c > m and m > m3:
            return "long"
        if c < m and m < m3:
            return "short"
        return None


# ---------------------------------------------------------------- trades du bot
def bot_trades(rows: list[dict[str, Any]], asset: str) -> list[sl.Trade]:
    out = []
    for s in rows:
        if s.get("status") not in ("tp", "sl", "expired") or s.get("close_price") is None:
            continue
        risk = abs(s["entry"] - s["stop_loss"])
        if risk <= 0:
            continue
        t = sl.Trade("bot", asset, s["direction"], int(parse_iso(s["created_at"]).timestamp()),
                     int(parse_iso(s["closed_at"]).timestamp()), s["entry"], s["close_price"], risk, s["status"])
        t.tp = s["take_profit"]            # type: ignore[attr-defined]
        t.stop = s["stop_loss"]            # type: ignore[attr-defined]
        out.append(t)
    return out


def removed_by(f: str, t: sl.Trade, ctx: Ctx, other: Ctx | None) -> bool:
    long = t.direction == "long"
    sign = 1 if long else -1
    T = t.entry_ts
    if f == "A1":
        i = ctx.m5.closed_at(T)
        if i is None or ctx.m5.sma[i] is None or not ctx.m5.atr[i]:
            return False
        return (ctx.m5.c[i].close - ctx.m5.sma[i]) * sign > 1.5 * ctx.m5.atr[i]
    if f == "A2":
        pd, k = ctx.prev_day(T), ctx.m15.closed_at(T)
        if pd is None or k is None or k < 4 or ctx.m15.sma[k] is None or ctx.m15.sma[k - 4] is None or not ctx.m15.atr[k]:
            return False
        inside = pd[1] <= t.entry <= pd[0]
        flat = abs(ctx.m15.sma[k] - ctx.m15.sma[k - 4]) < 0.25 * ctx.m15.atr[k]
        return inside and flat
    if f == "A3":
        pd = ctx.prev_day(T)
        if pd is None:
            return False
        tp = t.tp  # type: ignore[attr-defined]
        return (t.entry < pd[0] <= tp) if long else (tp <= pd[1] < t.entry)
    if f == "A4":
        h = ctx.h1.closed_at(T)
        r = ctx.h1.rsi[h] if h is not None else None
        if r is None:
            return False
        return r > 65 if long else r < 35
    if f == "A5":
        if other is None:
            return False
        k = other.m15.closed_at(T)
        if k is None or other.m15.sma[k] is None or T - (other.m15.c[k].ts + 900) > 3600:
            return False
        c, m = other.m15.c[k].close, other.m15.sma[k]
        return c < m if long else c > m
    raise ValueError(f)


def _loop(ctx: Ctx, t: sl.Trade, max_bars: int, on_bar) -> sl.Trade | None:
    """Rejoue un trade du bot bougie par bougie (5 min) depuis la clôture de la bougie d'entrée."""
    i = ctx.m5.closed_at(t.entry_ts)
    if i is None or ctx.m5.c[i].ts + 300 != t.entry_ts:
        return None
    long = t.direction == "long"
    st = {"stop": t.stop, "mfe": 0.0, "half": None}  # type: ignore[attr-defined]
    bars = ctx.m5.c
    for j in range(i + 1, min(len(bars), i + 1 + max_bars)):
        b = bars[j]
        if b.ts - bars[j - 1].ts > 4 * 86400:
            return _close(t, bars[j - 1].close, bars[j - 1].ts + 300, st)
        stop = st["stop"]
        if (b.low <= stop) if long else (b.high >= stop):
            px = min(stop, b.open) if long else max(stop, b.open)
            return _close(t, px, b.ts + 300, st)
        res = on_bar(j, b, st, long)
        if res is not None:
            return _close(t, res, b.ts + 300, st)
        fav = ((b.high - t.entry) if long else (t.entry - b.low)) / t.risk
        st["mfe"] = max(st["mfe"], fav)
    j = min(len(bars), i + 1 + max_bars) - 1
    return _close(t, bars[j].close, bars[j].ts + 300, st)


def _close(t: sl.Trade, px: float, ts: int, st: dict) -> sl.Trade:
    if st.get("half") is not None:        # moyenne des deux moitiés
        px = (st["half"] + px) / 2
    return sl.Trade(t.strategy, t.asset, t.direction, t.entry_ts, ts, t.entry, px, t.risk, "")


def exit_variant(e: str, t: sl.Trade, ctx: Ctx) -> sl.Trade | None:
    tp = t.tp  # type: ignore[attr-defined]
    m5 = ctx.m5

    def hit_tp(b, long):
        if (b.high >= tp) if long else (b.low <= tp):
            return max(tp, b.open) if long else min(tp, b.open)
        return None

    if e == "C11":
        def on_bar(j, b, st, long):
            one = t.entry + (t.risk if long else -t.risk)
            if st["half"] is None and ((b.high >= one) if long else (b.low <= one)):
                st["half"] = max(one, b.open) if long else min(one, b.open)
                st["stop"] = t.entry
            if st["half"] is not None:
                w = m5.c[j - 2: j + 1]
                trail = min(x.low for x in w) if long else max(x.high for x in w)
                st["stop"] = max(st["stop"], trail) if long else min(st["stop"], trail)
            return None
        return _loop(ctx, t, 36, on_bar)
    if e == "C12":
        i0 = m5.closed_at(t.entry_ts)

        def on_bar(j, b, st, long):
            px = hit_tp(b, long)
            if px is not None:
                return px
            fav = ((b.high - t.entry) if long else (t.entry - b.low)) / t.risk
            if j - i0 == 6 and max(st["mfe"], fav) < 0.5:
                return b.close
            return None
        return _loop(ctx, t, 12, on_bar)
    if e == "C13":
        def on_bar(j, b, st, long):
            px = hit_tp(b, long)
            if px is not None:
                return px
            m = m5.sma[j]
            if m is not None and ((b.close < m) if long else (b.close > m)):
                return b.close
            return None
        return _loop(ctx, t, 12, on_bar)
    raise ValueError(e)


# ---------------------------------------------------------------- setups (15 min)
def _limits(asset: str, ts: int) -> tuple[bool, int | None]:
    """(entrée permise, heure de sortie forcée)."""
    if asset not in FUTURES:
        return True, None
    close = sl.session_close_ts(ts)
    return close is not None, close


def _risk_ok(risk: float, atr: float | None) -> bool:
    return bool(atr) and 0.3 * atr <= risk <= 3 * atr


def _run(asset: str, name: str, f: Frame, k: int, direction: str, entry: float, stop: float,
         entry_bar: int, target: float | None, intrabar: bool) -> tuple[sl.Trade | None, int]:
    """Entrée pendant (intrabar) ou à la clôture de la bougie `entry_bar` ; suivi par sl.simulate."""
    long = direction == "long"
    risk = abs(entry - stop)
    ok, close_ts = _limits(asset, f.c[entry_bar].ts)
    if not ok or risk <= 0 or not _risk_ok(risk, f.atr[k]):
        return None, entry_bar
    tgt = target if target is not None else entry + (3 * risk if long else -3 * risk)
    b = f.c[entry_bar]
    ets = b.ts if intrabar else b.ts + f.sec
    if intrabar and ((b.low <= stop) if long else (b.high >= stop)):
        return sl.Trade(name, asset, direction, ets, b.ts + f.sec, entry, stop, risk, "stop"), entry_bar
    px, j, why = sl.simulate(f.c, entry_bar, direction, entry, stop, target=tgt, exit_ts=close_ts,
                             max_bars=16, bar_seconds=f.sec)
    if why == "fin des données":
        return None, len(f.c)
    return sl.Trade(name, asset, direction, ets, f.c[j].ts + f.sec, entry, px, risk, why), j


def setup_trades(name: str, asset: str, ctx: Ctx) -> list[sl.Trade]:
    f = ctx.m15
    c = f.c
    out: list[sl.Trade] = []
    if name == "B10":
        return _b10(asset, ctx)
    k, n = 21, len(c)
    while k < n - 2:
        T = c[k].ts + f.sec
        sma, atr = f.sma[k], f.atr[k]
        trade, nxt = None, k
        if name in ("B6", "B8") and sma is not None and atr:
            tr = ctx.trend_1h(T)
            if tr:
                long = tr == "long"
                go = False
                if name == "B6":
                    m, streak = k, 0
                    while m > 0 and ((c[m].low < c[m - 1].low) if long else (c[m].high > c[m - 1].high)):
                        streak += 1
                        m -= 1
                    near = (abs(c[k].low - sma) if long else abs(c[k].high - sma)) <= 0.5 * atr
                    go = 3 <= streak <= 6 and near
                    stop = min(c[k].low, c[k - 1].low) if long else max(c[k].high, c[k - 1].high)
                else:
                    rng = [x.high - x.low for x in c[k - 6: k + 1]]
                    go = rng[-1] == min(rng) and abs(c[k].close - sma) <= 0.5 * atr
                    stop = c[k].low if long else c[k].high
                nb = c[k + 1]
                lvl = c[k].high if long else c[k].low
                if go and ((nb.high > lvl) if long else (nb.low < lvl)):
                    entry = max(lvl, nb.open) if long else min(lvl, nb.open)
                    trade, nxt = _run(asset, name, f, k, tr, entry, stop, k + 1, None, True)
        elif name in ("B7", "B9") and atr:
            win = c[k - 20: k]
            hh, ll = max(x.high for x in win), min(x.low for x in win)
            vm = sum(x.volume for x in win) / 20
            b = c[k]
            if name == "B7" and vm > 0 and b.volume >= 2 * vm:
                if b.close > hh:
                    trade, nxt = _run(asset, name, f, k, "long", b.close, ll, k, None, False)
                elif b.close < ll:
                    trade, nxt = _run(asset, name, f, k, "short", b.close, hh, k, None, False)
            elif name == "B9" and vm > 0 and b.volume < vm:
                if b.high > hh and b.close < hh:
                    stop = b.high + 0.1 * atr
                    if b.close - ll >= stop - b.close:
                        trade, nxt = _run(asset, name, f, k, "short", b.close, stop, k, ll, False)
                elif b.low < ll and b.close > ll:
                    stop = b.low - 0.1 * atr
                    if hh - b.close >= b.close - stop:
                        trade, nxt = _run(asset, name, f, k, "long", b.close, stop, k, hh, False)
        if trade is not None:
            out.append(trade)
        k = max(k, nxt) + 1
    return out


def _b10(asset: str, ctx: Ctx) -> list[sl.Trade]:
    if asset not in OPEN_NY:
        return []
    m5 = ctx.m5
    bars = m5.c
    hh_, mm_ = OPEN_NY[asset]
    out = []
    for d in sl._days(bars):
        start = int(datetime.combine(d, time(hh_, mm_), sl.NY).timestamp())
        noon = int(datetime.combine(d, time(12, 0), sl.NY).timestamp())
        i0 = m5.closed_at(start + 300)
        if i0 is None or bars[i0].ts != start or i0 + 3 >= len(bars) or bars[i0 + 2].ts != start + 600:
            continue
        orb = bars[i0: i0 + 3]
        hi, lo = max(x.high for x in orb), min(x.low for x in orb)
        pd = ctx.prev_day(start)
        if pd is None:
            continue
        last = orb[-1].close
        side = "long" if last > pd[0] else "short" if last < pd[1] else None
        if side is None:
            continue
        j = i0 + 3
        while j < len(bars) and bars[j].ts + 300 <= noon:
            b = bars[j]
            if (b.close > hi) if side == "long" else (b.close < lo):
                entry, stop = b.close, (lo if side == "long" else hi)
                risk = abs(entry - stop)
                k15 = ctx.m15.closed_at(b.ts + 300)
                ok, close_ts = _limits(asset, b.ts)
                if ok and k15 is not None and _risk_ok(risk, ctx.m15.atr[k15]):
                    tgt = entry + (3 * risk if side == "long" else -3 * risk)
                    px, jj, why = sl.simulate(bars, j, side, entry, stop, target=tgt, exit_ts=close_ts)
                    if why != "fin des données":
                        out.append(sl.Trade("B10", asset, side, b.ts + 300, bars[jj].ts + 300, entry, px, risk, why))
                break
            j += 1
    return out


# ---------------------------------------------------------------- verdict
def verdict(trades: list[sl.Trade], cost_pct: float, tcost: tuple[float, float] | None) -> dict[str, Any]:
    disc = sl.evaluate(trades, cost_pct, tcost, start_ts=SPLIT)
    conf = sl.evaluate(trades, cost_pct, tcost, end_ts=SPLIT)
    both = sl.evaluate(trades, cost_pct, tcost)
    ok_d, ok_c = sl.discovery_pass(disc), sl.confirmation_pass(conf)
    status = ("prouvé" if sl.proven(both, N_TRIALS) else "validé") if ok_d and ok_c else (
        "écarté (découverte)" if not ok_d else "écarté (confirmation)")
    return {"discovery": disc, "confirmation": conf, "all": both, "status": status}
