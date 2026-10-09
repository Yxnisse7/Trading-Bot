"""Laboratoire de stratégies : des méthodes publiées, testées une par une sur chaque actif.

Le bot actuel additionne des critères qui disent presque tous « la tendance est là » (présents sur
quasiment chaque trade) : les repondérer ne crée pas d'avantage. Ici, chaque stratégie porte une idée
différente, tirée d'une étude ou d'une méthode connue, avec des réglages fixés d'avance (voir
HYPOTHESES.md, essai 3). On mesure stratégie × actif, avec deux jeux de frais :

- frais du bot (`cost_pct`, estimation prudente valable pour n'importe quel courtier) ;
- frais réels Topstep (commission par micro-contrat + un tick de glissement, `topstep.FEES`).

Sans biais de futur : chaque décision n'utilise que des bougies déjà closes ; l'entrée se fait à la
clôture de la bougie de décision, la sortie au stop (au prix d'ouverture si la bougie s'ouvre au-delà),
à l'objectif, ou à l'heure prévue. Heures de séance américaine en heure de New York (été/hiver gérés).
"""
from __future__ import annotations

import math
from bisect import bisect_left
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from statistics import NormalDist
from typing import Any, Callable
from zoneinfo import ZoneInfo

from . import indicators as ind
from .models import Candle

NY = ZoneInfo("America/New_York")
CT = ZoneInfo("America/Chicago")

STRATEGIES = {
    "orb5": "Cassure de la 1re bougie de 5 min de New York (Zarattini & Aziz, 2023)",
    "orb30": "Cassure du range des 30 premières minutes de New York",
    "intraday_mom": "Momentum intraday : la 1re demi-heure prédit la dernière (Gao, Han, Li & Zhou, 2018)",
    "noise_area": "Sortie de la « zone de bruit » du jour (Zarattini, Aziz & Barbon, 2024)",
    "gap_fade": "Comblement de l'écart d'ouverture de New York",
    "london_breakout": "Cassure du range asiatique à l'ouverture de Londres",
    "donchian_1h": "Cassure de canal de Donchian 20 heures, sortie sur 10 heures (méthode Turtle)",
    "rsi2_1h": "Retour à la moyenne RSI(2) dans le sens de la MM200, en bougies 1 h (Connors)",
    "news_breakout": "Cassure du range des 15 min qui suivent une annonce (emploi, inflation, Fed)",
    "pre_fomc": "Achat des indices la veille d'une décision de la Fed (Lucca & Moench, 2015)",
    "noise_area_v2": "Zone de bruit avec un stop réaliste, au moins 1 ATR 15 min (essai 5)",
}
INFO_ONLY = {"pre_fomc"}
ROBUST_ONLY = {"noise_area_v2"}   # plus de données vierges : critères de l'essai 5 sur les 24 mois
# Suivis en ombre sur le marché réel (aucune notification) : (stratégie, actif) → date de début
SHADOW = {("donchian_1h", "bitcoin"): "2026-10-05T19:00:00Z",
          ("donchian_1h", "gold"): "2026-10-05T20:00:00Z",      # validé à l'essai 3 (confirmation 2024-25)
          ("donchian_day", "gold"): "2026-10-07T21:00:00Z",     # validé à l'essai 8 (fermé chaque soir)
          ("creux_repris_15m", "nasdaq"): "2026-10-09T22:00:00Z"}  # validé à l'essai 15 (S25)
# Envoyées en signaux réels sur Telegram (entrée, stop, sortie), en plus du suivi : (stratégie, actif) → date de début.
# Choix de Yanisse le 08/10/2026 : validée en backtest (essai 8), pas encore prouvée sur le marché réel.
LIVE = {("donchian_day", "gold"): "2026-10-08T07:30:00Z"}
MIN_TRADES = {"news_breakout": 20}


@dataclass
class Trade:
    strategy: str
    asset: str
    direction: str
    entry_ts: int
    exit_ts: int
    entry: float
    exit: float
    risk: float          # distance d'entrée au stop initial, en points (dénominateur du R)
    reason: str

    def gross_points(self) -> float:
        return (self.exit - self.entry) * (1 if self.direction == "long" else -1)


# ---------------------------------------------------------------- outils
def _ny_ts(day: date, hh: int, mm: int) -> int:
    return int(datetime.combine(day, time(hh, mm), NY).timestamp())


def _utc_ts(day: date, hh: int, mm: int = 0) -> int:
    return int(datetime.combine(day, time(hh, mm), timezone.utc).timestamp())


def _prev_session(d: date) -> date:
    return d - timedelta(days=3 if d.weekday() == 0 else 1)


def _prev_close(s: "_Series", d: date) -> int | None:
    """Indice de la clôture de 16:00 (New York) de la séance précédente ; None si absente."""
    prev = _prev_session(d)
    i = s.last_before(_ny_ts(prev, 16, 0))
    return i if i is not None and s.c[i].ts >= _ny_ts(prev, 15, 30) else None


def _days(candles: list[Candle], tz=NY) -> list[date]:
    seen, out = set(), []
    for c in candles:
        d = datetime.fromtimestamp(c.ts, tz).date()
        if d not in seen and d.weekday() < 5:
            seen.add(d)
            out.append(d)
    return out


def simulate(bars: list[Candle], i: int, direction: str, entry: float, stop: float, *,
             target: float | None = None, exit_ts: int | None = None, max_bars: int | None = None,
             on_close: Callable[[int, Candle, float], tuple[str, float] | float | None] | None = None,
             bar_seconds: int = 300) -> tuple[float, int, str]:
    """Suit la position depuis la bougie i+1. Stop prioritaire sur l'objectif dans la même bougie.
    `on_close(j, bar, stop)` peut renvoyer un nouveau stop (resserré seulement) ou ("exit", prix)."""
    long = direction == "long"
    j, n = i + 1, len(bars)
    while j < n:
        b = bars[j]
        if b.ts - bars[j - 1].ts > 4 * 86400:            # trou dans les données : on sort avant
            return bars[j - 1].close, j - 1, "trou"
        if (b.low <= stop) if long else (b.high >= stop):
            return (min(stop, b.open) if long else max(stop, b.open)), j, "stop"
        if target is not None and ((b.high >= target) if long else (b.low <= target)):
            return (max(target, b.open) if long else min(target, b.open)), j, "objectif"
        if on_close is not None:
            r = on_close(j, b, stop)
            if isinstance(r, tuple):
                return r[1], j, r[0]
            if r is not None:
                stop = max(stop, r) if long else min(stop, r)
        if exit_ts is not None and b.ts + bar_seconds >= exit_ts:
            return b.close, j, "heure"
        if max_bars is not None and j - i >= max_bars:
            return b.close, j, "durée"
        j += 1
    return bars[-1].close, n - 1, "fin des données"


class _Series:
    """Index des bougies 5 min par horodatage de début."""

    def __init__(self, candles: list[Candle]):
        self.c = candles
        self.ts = [x.ts for x in candles]
        self.pos = {t: k for k, t in enumerate(self.ts)}
        self.atr = ind.atr(candles, 14)

    def at(self, ts: int) -> int | None:
        return self.pos.get(ts)

    def last_before(self, ts: int) -> int | None:
        """Dernière bougie qui commence avant `ts` (donc close au plus tard à ts)."""
        k = bisect_left(self.ts, ts) - 1
        return k if k >= 0 else None


# ---------------------------------------------------------------- stratégies (bougies 5 min)
def orb5(s: _Series, asset: str) -> list[Trade]:
    out = []
    for d in _days(s.c):
        i = s.at(_ny_ts(d, 9, 30))
        if i is None:
            continue
        b = s.c[i]
        if b.close == b.open or b.high == b.low:
            continue
        long = b.close > b.open
        stop = b.low if long else b.high
        entry = b.close
        risk = abs(entry - stop)
        if risk <= 0:
            continue
        target = entry + 10 * risk if long else entry - 10 * risk
        px, j, why = simulate(s.c, i, "long" if long else "short", entry, stop, target=target,
                              exit_ts=_ny_ts(d, 16, 0))
        out.append(Trade("orb5", asset, "long" if long else "short", b.ts + 300, s.c[j].ts + 300, entry, px, risk, why))
    return out


def orb30(s: _Series, asset: str) -> list[Trade]:
    out = []
    for d in _days(s.c):
        i0 = s.at(_ny_ts(d, 9, 30))
        i1 = s.at(_ny_ts(d, 9, 55))
        if i0 is None or i1 is None or i1 - i0 != 5:
            continue
        hi = max(x.high for x in s.c[i0:i1 + 1])
        lo = min(x.low for x in s.c[i0:i1 + 1])
        stop_at = _ny_ts(d, 12, 0)
        k = i1 + 1
        while k < len(s.c) and s.c[k].ts < stop_at:
            b = s.c[k]
            if b.close > hi or b.close < lo:
                long = b.close > hi
                stop = lo if long else hi
                risk = abs(b.close - stop)
                px, j, why = simulate(s.c, k, "long" if long else "short", b.close, stop, exit_ts=_ny_ts(d, 16, 0))
                out.append(Trade("orb30", asset, "long" if long else "short", b.ts + 300, s.c[j].ts + 300,
                                 b.close, px, risk, why))
                break
            k += 1
    return out


def intraday_mom(s: _Series, asset: str) -> list[Trade]:
    out = []
    for d in _days(s.c):
        ip = _prev_close(s, d)
        i10 = s.last_before(_ny_ts(d, 10, 0))
        ie = s.last_before(_ny_ts(d, 15, 30))
        if None in (ip, i10, ie) or s.c[i10].ts < _ny_ts(d, 9, 30) \
                or s.c[ie].ts < _ny_ts(d, 15, 0) or not s.atr[ie]:
            continue
        r1 = s.c[i10].close / s.c[ip].close - 1
        if r1 == 0:
            continue
        long = r1 > 0
        entry = s.c[ie].close
        risk = 2 * s.atr[ie]
        stop = entry - risk if long else entry + risk
        px, j, why = simulate(s.c, ie, "long" if long else "short", entry, stop, exit_ts=_ny_ts(d, 16, 0))
        out.append(Trade("intraday_mom", asset, "long" if long else "short", s.c[ie].ts + 300, s.c[j].ts + 300,
                         entry, px, risk, why))
    return out


def _atr15(s: _Series) -> list[float | None]:
    """ATR(14) de la dernière bougie de 15 min close, aligné sur chaque bougie de 5 min (sans biais de futur)."""
    c15 = ind.resample(s.c, 15)
    a15 = ind.atr(c15, 14)
    out, k = [], -1
    for c in s.c:
        while k + 1 < len(c15) and c15[k + 1].ts + 900 <= c.ts + 300:
            k += 1
        out.append(a15[k] if k >= 0 else None)
    return out


def noise_area_v2(s: _Series, asset: str) -> list[Trade]:
    """Essai 5 : `noise_area` avec un stop dur réaliste (au moins 1 ATR 15 min), qui sert aussi de R."""
    return noise_area(s, asset, realistic_stop=True)


def noise_area(s: _Series, asset: str, lookback: int = 14, realistic_stop: bool = False) -> list[Trade]:
    """Bornes = ouverture (corrigée de l'écart avec la clôture de la veille) ± moyenne sur 14 jours du
    mouvement absolu depuis l'ouverture à la même heure. Décisions aux demi-heures de 10:00 à 15:30."""
    name = "noise_area_v2" if realistic_stop else "noise_area"
    atr15 = _atr15(s) if realistic_stop else None
    out = []
    days = _days(s.c)
    moves: dict[date, dict[int, float]] = {}       # jour → {minutes depuis 9:30 → |clôture/ouverture − 1|}
    for d in days:
        i0 = s.at(_ny_ts(d, 9, 30))
        if i0 is None:
            continue
        o = s.c[i0].open
        m = {}
        k = i0
        end = _ny_ts(d, 16, 0)
        while k < len(s.c) and s.c[k].ts < end:
            m[(s.c[k].ts + 300 - s.c[i0].ts) // 60] = abs(s.c[k].close / o - 1)
            k += 1
        moves[d] = m
    hist: list[date] = []
    for d in days:
        i0 = s.at(_ny_ts(d, 9, 30))
        prev_close_i = _prev_close(s, d)
        if i0 is None or prev_close_i is None or len(hist) < lookback:
            if d in moves:
                hist.append(d)
            continue
        past = hist[-lookback:]
        o, pc = s.c[i0].open, s.c[prev_close_i].close
        hi_base, lo_base = max(o, pc), min(o, pc)

        def bounds(minute: int) -> tuple[float, float] | None:
            vals = [moves[p][minute] for p in past if minute in moves[p]]
            if len(vals) < lookback // 2:
                return None
            sig = sum(vals) / len(vals)
            return hi_base * (1 + sig), lo_base * (1 - sig)

        marks = [_ny_ts(d, 10, 0) + 1800 * k for k in range(12)]      # 10:00 … 15:30
        vwap_pv = vwap_v = 0.0
        k = i0
        pos = None                                                      # (direction, entry, stop, risk, i_entry)
        end = _ny_ts(d, 16, 0)
        while k < len(s.c) and s.c[k].ts < end:
            b = s.c[k]
            if realistic_stop and pos is not None and k > pos[4]:
                hard = pos[1] - pos[3] if pos[0] == "long" else pos[1] + pos[3]
                if (b.low <= hard) if pos[0] == "long" else (b.high >= hard):
                    px = min(hard, b.open) if pos[0] == "long" else max(hard, b.open)
                    out.append(Trade(name, asset, pos[0], s.c[pos[4]].ts + 300, b.ts + 300, pos[1], px, pos[3], "stop"))
                    pos = None
            tp = (b.high + b.low + b.close) / 3
            vwap_pv += tp * max(b.volume, 1.0)
            vwap_v += max(b.volume, 1.0)
            close_t = b.ts + 300
            if close_t in marks:
                bd = bounds((close_t - s.c[i0].ts) // 60)
                vw = vwap_pv / vwap_v
                if bd:
                    ub, lb = bd
                    if pos is None and close_t < marks[-1] + 1:
                        if b.close > ub or b.close < lb:
                            long = b.close > ub
                            stop = max(ub, vw) if long else min(lb, vw)
                            if realistic_stop:
                                if not atr15[k]:
                                    k += 1
                                    continue
                                risk = max(abs(b.close - stop), atr15[k])
                            else:
                                risk = max(abs(b.close - stop), 0.5 * (s.atr[k] or 0))
                            pos = ("long" if long else "short", b.close, stop, risk, k)
                    elif pos is not None:
                        long = pos[0] == "long"
                        stop = max(ub, vw) if long else min(lb, vw)
                        if (b.close < stop) if long else (b.close > stop):
                            out.append(Trade(name, asset, pos[0], s.c[pos[4]].ts + 300, close_t,
                                             pos[1], b.close, pos[3], "bornes"))
                            pos = None
            k += 1
        if pos is not None:
            last = s.c[k - 1]
            out.append(Trade(name, asset, pos[0], s.c[pos[4]].ts + 300, last.ts + 300,
                             pos[1], last.close, pos[3], "heure"))
        hist.append(d)
    return out


def gap_fade(s: _Series, asset: str) -> list[Trade]:
    out = []
    for d in _days(s.c):
        i0 = s.at(_ny_ts(d, 9, 30))
        ip = _prev_close(s, d)
        if i0 is None or ip is None:
            continue
        pc, o = s.c[ip].close, s.c[i0].open
        gap = o / pc - 1
        if not (0.0025 <= abs(gap) <= 0.01):
            continue
        b = s.c[i0]
        long = gap < 0                                     # écart baissier → on joue la remontée
        entry = b.close
        if (long and entry >= pc) or (not long and entry <= pc):
            continue                                       # déjà comblé pendant la 1re bougie
        dist = abs(pc - entry)
        stop = entry - dist if long else entry + dist
        px, j, why = simulate(s.c, i0, "long" if long else "short", entry, stop, target=pc,
                              exit_ts=_ny_ts(d, 12, 0))
        out.append(Trade("gap_fade", asset, "long" if long else "short", b.ts + 300, s.c[j].ts + 300,
                         entry, px, dist, why))
    return out


def london_breakout(s: _Series, asset: str) -> list[Trade]:
    out = []
    for d in _days(s.c, timezone.utc):
        a0, a1 = s.at(_utc_ts(d, 0)), s.last_before(_utc_ts(d, 7))
        if a0 is None or a1 is None or a1 - a0 < 60:       # au moins 5 h de range asiatique
            continue
        hi = max(x.high for x in s.c[a0:a1 + 1])
        lo = min(x.low for x in s.c[a0:a1 + 1])
        if hi <= lo:
            continue
        k, end_entry = a1 + 1, _utc_ts(d, 11)
        while k < len(s.c) and s.c[k].ts < end_entry:
            b = s.c[k]
            if b.close > hi or b.close < lo:
                long = b.close > hi
                stop = lo if long else hi
                risk = abs(b.close - stop)
                target = b.close + risk if long else b.close - risk
                px, j, why = simulate(s.c, k, "long" if long else "short", b.close, stop, target=target,
                                      exit_ts=_utc_ts(d, 16))
                out.append(Trade("london_breakout", asset, "long" if long else "short", b.ts + 300,
                                 s.c[j].ts + 300, b.close, px, risk, why))
                break
            k += 1
    return out


# ---------------------------------------------------------------- stratégies (bougies 1 h)
def session_close_ts(ts: int) -> int | None:
    """Essai 8 : heure de sortie forcée (15:00 heure de Chicago) de la séance Topstep qui contient l'instant
    `ts` ; None entre 15:00 et 17:00 (fin de séance et pause du marché : pas d'entrée)."""
    d = datetime.fromtimestamp(ts, timezone.utc).astimezone(CT)
    if 15 <= d.hour < 17:
        return None
    day = d.date() + timedelta(days=1) if d.hour >= 17 else d.date()
    return int(datetime.combine(day, time(15, 0), CT).timestamp())


def donchian_day(candles: list[Candle], asset: str) -> list[Trade]:
    """Essai 8 : `donchian_1h` fermé chaque jour à 15:00 heure de Chicago, sans entrée de 15:00 à 17:00."""
    return donchian_1h(candles, asset, day_close=True)


def donchian_15m_day(candles: list[Candle], asset: str) -> list[Trade]:
    """Essai 9 A : `donchian_day` sur des bougies de 15 min."""
    return donchian_1h(candles, asset, day_close=True, minutes=15)


def donchian_30m_day(candles: list[Candle], asset: str) -> list[Trade]:
    """Essai 9 B : `donchian_day` sur des bougies de 30 min."""
    return donchian_1h(candles, asset, day_close=True, minutes=30)


def comex_orb(s: _Series, asset: str) -> list[Trade]:
    """Essai 9 C : cassure des 30 premières minutes du COMEX (8:20 heure de New York), stop de l'autre côté du
    range, sortie au stop ou à 15:00 heure de Chicago (16:00 à New York). Un trade par jour au plus."""
    out = []
    for d in _days(s.c):
        i0, i1 = s.at(_ny_ts(d, 8, 20)), s.at(_ny_ts(d, 8, 45))
        if i0 is None or i1 is None or i1 - i0 != 5:
            continue
        hi = max(x.high for x in s.c[i0:i1 + 1])
        lo = min(x.low for x in s.c[i0:i1 + 1])
        stop_at = _ny_ts(d, 12, 0)
        k = i1 + 1
        while k < len(s.c) and s.c[k].ts < stop_at:
            b = s.c[k]
            if b.close > hi or b.close < lo:
                long = b.close > hi
                stop = lo if long else hi
                risk = abs(b.close - stop)
                if risk > 0:
                    px, j, why = simulate(s.c, k, "long" if long else "short", b.close, stop, exit_ts=_ny_ts(d, 16, 0))
                    out.append(Trade("comex_orb", asset, "long" if long else "short", b.ts + 300, s.c[j].ts + 300,
                                     b.close, px, risk, why))
                break
            k += 1
    return out


def donchian_1h(candles: list[Candle], asset: str, entry_n: int = 20, exit_n: int = 10,
                day_close: bool = False, minutes: int = 60) -> list[Trade]:
    sec = minutes * 60
    h = ind.resample(candles, minutes)
    atr = ind.atr(h, 14)
    out, i = [], max(entry_n, 15)
    while i < len(h) - 1:
        b = h[i]
        prev = h[i - entry_n:i]
        if not atr[i] or b.ts - h[i - 1].ts > 4 * 86400:
            i += 1
            continue
        hi, lo = max(x.high for x in prev), min(x.low for x in prev)
        close_at = session_close_ts(b.ts + sec) if day_close else None
        # séance plus courte (jour férié) : la dernière bougie de la séance ne permet pas d'entrer
        last_of_session = close_at is not None and h[i + 1].ts >= close_at
        if (b.close > hi or b.close < lo) and (not day_close or (close_at is not None and not last_of_session)):
            long = b.close > hi
            risk = 2 * atr[i]
            stop = b.close - risk if long else b.close + risk

            def trail(j, bar, st, long=long, close_at=close_at):
                if close_at is not None and (j + 1 >= len(h) or h[j + 1].ts >= close_at):
                    return ("heure", bar.close)            # dernière clôture de la séance (15:00, ou plus tôt)
                w = h[max(0, j - exit_n):j]
                if long and bar.close < min(x.low for x in w):
                    return ("canal", bar.close)
                if not long and bar.close > max(x.high for x in w):
                    return ("canal", bar.close)
                return None

            px, j, why = simulate(h, i, "long" if long else "short", b.close, stop, max_bars=120,
                                  on_close=trail, bar_seconds=sec, exit_ts=close_at)
            name = ("donchian_day" if minutes == 60 else f"donchian_{minutes}m_day") if day_close else "donchian_1h"
            out.append(Trade(name, asset, "long" if long else "short", b.ts + sec, h[j].ts + sec,
                             b.close, px, risk, why))
            i = j + 1
            continue
        i += 1
    return out


def rsi2_1h(candles: list[Candle], asset: str) -> list[Trade]:
    h = ind.resample(candles, 60)
    closes = [x.close for x in h]
    r2, ma, atr = ind.rsi(closes, 2), ind.sma(closes, 200), ind.atr(h, 14)
    out, i = [], 201
    while i < len(h) - 1:
        b = h[i]
        if r2[i] is None or ma[i] is None or not atr[i]:
            i += 1
            continue
        long = r2[i] < 10 and b.close > ma[i]
        short = r2[i] > 90 and b.close < ma[i]
        if long or short:
            risk = 2.5 * atr[i]
            stop = b.close - risk if long else b.close + risk

            def ex(j, bar, st, long=long):
                if r2[j] is not None and ((long and r2[j] > 70) or (not long and r2[j] < 30)):
                    return ("rsi", bar.close)
                return None

            px, j, why = simulate(h, i, "long" if long else "short", b.close, stop, max_bars=10,
                                  on_close=ex, bar_seconds=3600)
            out.append(Trade("rsi2_1h", asset, "long" if long else "short", b.ts + 3600, h[j].ts + 3600,
                             b.close, px, risk, why))
            i = j + 1
            continue
        i += 1
    return out


# ---------------------------------------------------------------- annonces macro (essai 4)
def news_breakout(s: _Series, asset: str, events: list[tuple[int, str]] | None = None) -> list[Trade]:
    from .macro_history import events as macro_events

    out = []
    for at, kind in (events if events is not None else macro_events()):
        day = datetime.fromtimestamp(at, NY).date()
        fed = kind == "fomc"
        i0 = s.at(at)
        i1 = s.at(at + 600)
        if i0 is None or i1 is None or i1 - i0 != 2:
            continue
        hi = max(x.high for x in s.c[i0:i1 + 1])
        lo = min(x.low for x in s.c[i0:i1 + 1])
        last_entry = _ny_ts(day, 15, 0) if fed else _ny_ts(day, 10, 0)
        exit_ts = _ny_ts(day, 16, 0) if fed else _ny_ts(day, 12, 0)
        k = i1 + 1
        while k < len(s.c) and s.c[k].ts + 300 <= last_entry:
            b = s.c[k]
            if b.close > hi or b.close < lo:
                long = b.close > hi
                stop = lo if long else hi
                px, j, why = simulate(s.c, k, "long" if long else "short", b.close, stop, exit_ts=exit_ts)
                out.append(Trade("news_breakout", asset, "long" if long else "short", b.ts + 300, s.c[j].ts + 300,
                                 b.close, px, abs(b.close - stop), why))
                break
            k += 1
    return out


def pre_fomc(candles: list[Candle], asset: str) -> list[Trade]:
    if asset not in ("nasdaq", "sp500"):
        return []
    from .macro_history import FOMC

    h = ind.resample(candles, 60)
    atr = ind.atr(h, 14)
    hts = [x.ts for x in h]
    out = []
    for d in FOMC:
        day = date.fromisoformat(d)
        start, end = _ny_ts(_prev_session(day), 14, 0), _ny_ts(day, 14, 0)
        i = bisect_left(hts, start) - 1                  # bougie horaire close juste avant 14:00 la veille
        if i < 15 or not atr[i] or hts[i] + 3600 > start or start - hts[i] > 7200:
            continue
        entry = h[i].close
        risk = 2 * atr[i]
        px, j, why = simulate(h, i, "long", entry, entry - risk, exit_ts=end - 300, bar_seconds=3600)
        out.append(Trade("pre_fomc", asset, "long", h[i].ts + 3600, h[j].ts + 3600, entry, px, risk, why))
    return out


RUNNERS_5M = {"orb5": orb5, "orb30": orb30, "intraday_mom": intraday_mom, "noise_area": noise_area,
              "gap_fade": gap_fade, "london_breakout": london_breakout, "news_breakout": news_breakout,
              "noise_area_v2": noise_area_v2, "comex_orb": comex_orb}
def creux_repris_15m(candles: list[Candle], asset: str) -> list[Trade]:
    """Essai 15, S25 : creux cassé puis repris en 2 bougies 15 min, dans la tendance 1 h (règle de essai15.py)."""
    from . import essai15
    return essai15.setup_trades("S25", asset, essai15.Ctx(candles))


RUNNERS_1H = {"donchian_1h": donchian_1h, "rsi2_1h": rsi2_1h, "pre_fomc": pre_fomc, "donchian_day": donchian_day,
              "donchian_15m_day": donchian_15m_day, "donchian_30m_day": donchian_30m_day, "creux_repris_15m": creux_repris_15m}


def run_all(asset: str, candles: list[Candle], only: list[str] | None = None) -> list[Trade]:
    s = _Series(candles)
    out: list[Trade] = []
    for name, fn in RUNNERS_5M.items():
        if not only or name in only:
            out += fn(s, asset)
    for name, fn in RUNNERS_1H.items():
        if not only or name in only:
            out += fn(candles, asset)
    return out


# ---------------------------------------------------------------- évaluation
def trade_rs(t: Trade, cost_bot_pct: float, topstep_cost: tuple[float, float] | None) -> dict[str, float]:
    """R brut, R net avec les frais du bot (% du prix), R net avec les frais Topstep ($ par micro)."""
    g = t.gross_points()
    bot = cost_bot_pct / 100 * t.entry
    out = {"gross": g / t.risk, "net_bot": (g - bot) / t.risk}
    if topstep_cost:
        fee_usd, mult = topstep_cost
        out["net_topstep"] = (g - fee_usd / mult) / t.risk
    return out


def _stats(rs: list[float]) -> dict[str, Any]:
    n = len(rs)
    if n == 0:
        return {"n": 0, "mean_r": None, "se": None, "profit_factor": None, "win_rate": None}
    m = sum(rs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in rs) / (n - 1)) if n > 1 else 0.0
    gains, losses = sum(x for x in rs if x > 0), -sum(x for x in rs if x < 0)
    return {"n": n, "mean_r": round(m, 4), "se": round(sd / math.sqrt(n), 4) if n > 1 else None,
            "profit_factor": round(gains / losses, 2) if losses > 0 else None,
            "win_rate": round(sum(1 for x in rs if x > 0) / n, 4)}


def evaluate(trades: list[Trade], cost_bot_pct: float, topstep_cost: tuple[float, float] | None,
             start_ts: int | None = None, end_ts: int | None = None) -> dict[str, Any]:
    sel = sorted((t for t in trades if (start_ts is None or t.entry_ts >= start_ts)
                  and (end_ts is None or t.entry_ts < end_ts)), key=lambda t: t.entry_ts)
    rows = [trade_rs(t, cost_bot_pct, topstep_cost) for t in sel]
    key = "net_topstep" if topstep_cost else "net_bot"
    main = [r[key] for r in rows]
    half = len(main) // 2
    return {"n": len(sel), "gross": _stats([r["gross"] for r in rows]), "net_bot": _stats([r["net_bot"] for r in rows]),
            "net": _stats(main), "net_key": key, "first_half": _stats(main[:half]), "second_half": _stats(main[half:]),
            "first": datetime.fromtimestamp(sel[0].entry_ts, tz=timezone.utc).date().isoformat() if sel else None,
            "last": datetime.fromtimestamp(sel[-1].entry_ts, tz=timezone.utc).date().isoformat() if sel else None}


def discovery_pass(ev: dict[str, Any], min_trades: int = 30) -> bool:
    """Critères de l'essai 3 sur la période de découverte (HYPOTHESES.md)."""
    net, h1, h2 = ev["net"], ev["first_half"], ev["second_half"]
    return (ev["n"] >= min_trades and (net["mean_r"] or 0) > 0 and (net["profit_factor"] or 0) >= 1.1
            and (h1["mean_r"] or 0) > 0 and (h2["mean_r"] or 0) > 0)


def confirmation_pass(ev: dict[str, Any], min_trades: int = 30) -> bool:
    net = ev["net"]
    return ev["n"] >= min_trades and (net["mean_r"] or 0) > 0 and (net["profit_factor"] or 0) >= 1.1


def robust_check(trades: list[Trade], cost_bot_pct: float, topstep_cost: tuple[float, float] | None,
                 split_ts: int) -> dict[str, Any]:
    """Critères de l'essai 5 sur toute la période : deux années positives, facteur de profit, résultat
    sans les 5 % meilleurs trades, et gain en % du prix (insensible à la taille du stop)."""
    key = "net_topstep" if topstep_cost else "net_bot"
    rows = [(t.entry_ts, trade_rs(t, cost_bot_pct, topstep_cost)[key],
             (t.gross_points() - ((topstep_cost[0] / topstep_cost[1]) if topstep_cost else cost_bot_pct / 100 * t.entry))
             / t.entry * 100) for t in trades]
    rs = sorted(r for _, r, _ in rows)
    y1 = [r for ts, r, _ in rows if ts < split_ts]
    y2 = [r for ts, r, _ in rows if ts >= split_ts]
    cut = max(1, len(rs) // 20)
    trimmed = rs[:-cut] if len(rs) > cut else []
    st_all = _stats(rs)
    checks = {
        "au moins 100 trades": len(rs) >= 100,
        "gain > 0 en 2024-25": bool(y1) and sum(y1) / len(y1) > 0,
        "gain > 0 en 2025-26": bool(y2) and sum(y2) / len(y2) > 0,
        "facteur de profit ≥ 1,1": (st_all["profit_factor"] or 0) >= 1.1,
        "≥ 0 sans les 5 % meilleurs trades": bool(trimmed) and sum(trimmed) / len(trimmed) >= 0,
        "gain en % du prix > 0": bool(rows) and sum(p for *_, p in rows) / len(rows) > 0,
    }
    return {"checks": checks, "passed": all(checks.values()),
            "mean_y1": round(sum(y1) / len(y1), 4) if y1 else None, "mean_y2": round(sum(y2) / len(y2), 4) if y2 else None,
            "trimmed_mean": round(sum(trimmed) / len(trimmed), 4) if trimmed else None,
            "mean_pct": round(sum(p for *_, p in rows) / len(rows), 4) if rows else None}


def proven(ev_all: dict[str, Any], n_trials: int, alpha: float = 0.05) -> bool:
    """Avantage prouvé sur toute la période : borne basse > 0 avec la marge corrigée du nombre d'essais."""
    net = ev_all["net"]
    if not net["n"] or net["se"] is None:
        return False
    z = NormalDist().inv_cdf(1 - alpha / max(1, n_trials))
    return net["mean_r"] - z * net["se"] > 0
