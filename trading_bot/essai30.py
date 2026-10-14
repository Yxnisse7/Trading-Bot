"""Essai 30 (HYPOTHESES.md) : stratégies Bitcoin courtes trouvées par une recherche large.

    python -m trading_bot.essai30          → data/essai30.json
"""
from __future__ import annotations

import zlib
from datetime import date, datetime, time, timedelta, timezone
from statistics import NormalDist
from typing import Any, Callable

import numpy as np

from . import strategies as sl

COST = 0.06                       # % aller-retour (config du bot)
HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
RECENT = int(datetime(2024, 10, 14, tzinfo=timezone.utc).timestamp())
N_MONKEYS = 1000
MIN_TRADES = 200
UTC = timezone.utc
H = 3600

Trade = tuple[int, int, float, float, int]      # indice d'entrée, indice de sortie, prix d'entrée, prix de sortie, sens


class Bars:
    def __init__(self, candles):
        self.ts = np.array([c.ts for c in candles], dtype=np.int64)
        self.op = np.array([c.open for c in candles])
        self.hi = np.array([c.high for c in candles])
        self.lo = np.array([c.low for c in candles])
        self.cl = np.array([c.close for c in candles])
        d0 = datetime.fromtimestamp(int(self.ts[0]), UTC).date()
        d1 = datetime.fromtimestamp(int(self.ts[-1]), UTC).date()
        self.days = [d0 + timedelta(days=i) for i in range((d1 - d0).days + 1)]

    def at(self, t: int, tol: int = 600) -> int | None:
        i = int(np.searchsorted(self.ts, t))
        return i if i < len(self.ts) and self.ts[i] - t <= tol else None


def _ts(d: date, hh: int, mm: int = 0, tz=UTC) -> int:
    return int(datetime.combine(d, time(hh, mm), tz).timestamp())


def _op(b: Bars, i: int | None) -> float | None:
    return None if i is None else float(b.op[i])


def timed(b: Bars, hin, hout, sign_fn: Callable[[date], int | None], tz=UTC, next_day=False) -> list[Trade]:
    out = []
    for d in b.days:
        s = sign_fn(d)
        if not s:
            continue
        a = b.at(_ts(d, *hin, tz))
        z = b.at(_ts(d + timedelta(days=1) if next_day else d, *hout, tz))
        if a is not None and z is not None and z > a:
            out.append((a, z, float(b.op[a]), float(b.op[z]), s))
    return out


def grid_returns(b: Bars, step: int) -> tuple[np.ndarray, np.ndarray]:
    """Bougies de `step` secondes alignées sur UTC : (indices des ouvertures, rendements), NaN si une borne manque."""
    t = np.arange((int(b.ts[0]) // step + 1) * step, int(b.ts[-1]), step)
    i = np.searchsorted(b.ts, t)
    i = np.clip(i, 0, len(b.ts) - 1)
    ok = b.ts[i] == t
    px = np.where(ok, b.op[i], np.nan)
    r = px[1:] / px[:-1] - 1
    return np.where(ok, i, -1), r


def shock_fade(b: Bars, step: int, k: float, window: int) -> list[Trade]:
    idx, r = grid_returns(b, step)
    out = []
    for j in range(window, len(r) - 1):
        x = r[j]
        if np.isnan(x):
            continue
        past = r[j - window:j]
        past = past[~np.isnan(past)]
        if len(past) < window // 2:
            continue
        sd = past.std()
        if sd <= 0 or abs(x) <= k * sd:
            continue
        a, z = idx[j + 1], idx[j + 2]
        if a < 0 or z < 0:
            continue
        out.append((int(a), int(z), float(b.op[a]), float(b.op[z]), -1 if x > 0 else 1))
    return out


def agitated_days(b: Bars) -> set[date]:
    idx, r = grid_returns(b, H)
    t0 = (int(b.ts[0]) // H + 1) * H
    vols: list[tuple[date, float]] = []
    for d in b.days:
        j = (_ts(d, 0) - t0) // H
        if j < 720:
            continue
        past = r[j - 720:j]
        past = past[~np.isnan(past)]
        if len(past) >= 360:
            vols.append((d, float(past.std())))
    out = set()
    for n, (d, v) in enumerate(vols):
        if n >= 365 and v > np.median([x for _, x in vols[n - 365:n]]):
            out.add(d)
    return out


def last_half_hour(b: Bars, contrarian: bool) -> list[Trade]:
    def sign(d: date) -> int | None:
        if contrarian:
            p0, p1 = _op(b, b.at(_ts(d, 16, 0, sl.NY))), _op(b, b.at(_ts(d, 16, 30, sl.NY)))
        else:
            p0, p1 = _op(b, b.at(_ts(d - timedelta(days=1), 17, 0, sl.NY))), _op(b, b.at(_ts(d, 10, 0, sl.NY)))
        if p0 is None or p1 is None or p1 == p0:
            return None
        s = 1 if p1 > p0 else -1
        return -s if contrarian else s
    return timed(b, (16, 30), (17, 0), sign, sl.NY)


def max10(b: Bars) -> list[Trade]:
    px = {d: _op(b, b.at(_ts(d, 16, 0, sl.NY))) for d in b.days}

    def sign(d: date) -> int | None:
        if d.weekday() not in (0, 1, 4) or px[d] is None:
            return None
        past = [px.get(d - timedelta(days=i)) for i in range(1, 11)]
        past = [p for p in past if p is not None]
        return 1 if len(past) >= 8 and px[d] > max(past) else None
    return timed(b, (16, 0), (10, 0), sign, sl.NY, next_day=True)


def williams(b: Bars, ma5: bool) -> list[Trade]:
    out = []
    closes: list[float] = []
    prev = None
    for d in b.days:
        a, z = b.at(_ts(d, 0)), b.at(_ts(d + timedelta(days=1), 0))
        if a is None or z is None or z <= a:
            prev = None
            continue
        if prev is not None and (not ma5 or (len(closes) >= 5 and b.op[a] > np.mean(closes[-5:]))):
            level = b.op[a] + 0.5 * prev
            hit = np.flatnonzero(b.hi[a:z] >= level)
            if len(hit):
                k = a + int(hit[0])
                if k + 1 < z:
                    out.append((k, z, float(max(level, b.op[k])), float(b.op[z]), 1))
        prev = float(b.hi[a:z].max() - b.lo[a:z].min())
        closes.append(float(b.op[z]))
    return out


def cells(b: Bars) -> dict[str, tuple[Callable[[], list[Trade]], str]]:
    every = lambda d: 1  # noqa: E731
    return {
        "B1 heure du soir": (lambda: timed(b, (21, 0), (23, 0), every), "jour"),
        "B2 heure du soir, vendredi": (lambda: timed(b, (21, 0), (23, 0), lambda d: 1 if d.weekday() == 4 else None), "jour"),
        "B3 heure du soir, jours agités": (lambda: (lambda s: timed(b, (21, 0), (23, 0), lambda d: 1 if d in s else None))(
            agitated_days(b)), "jour"),
        "B4 contre une bougie 1 h de 3 σ": (lambda: shock_fade(b, H, 3, 720), "heure"),
        "B5 contre une bougie 1 h de 2 σ": (lambda: shock_fade(b, H, 2, 720), "heure"),
        "B6 contre une bougie 2 h de 3 σ": (lambda: shock_fade(b, 2 * H, 3, 360), "heure"),
        "B7 dernière demi-heure, contre-sens": (lambda: last_half_hour(b, True), "jour"),
        "B8 dernière demi-heure, sens du jour": (lambda: last_half_hour(b, False), "jour"),
        "B9 plus haut de 10 jours le soir": (lambda: max10(b), "heure"),
        "B10 cassure Larry Williams": (lambda: williams(b, False), "heure"),
        "B11 cassure Larry Williams + moyenne 5 j": (lambda: williams(b, True), "heure"),
        "B12 ouverture de Tokyo le lundi": (lambda: timed(b, (19, 0), (19, 0), lambda d: 1 if d.weekday() == 6 else None,
                                                          sl.NY, next_day=True), "jour"),
    }


def monkeys(b: Bars, tr: list[Trade], mode: str, rng) -> np.ndarray:
    a = np.array([x[0] for x in tr]); z = np.array([x[1] for x in tr]); sg = np.array([x[4] for x in tr])
    dur = b.ts[z] - b.ts[a]
    if mode == "jour":        # même jour UTC, heure au hasard
        d0 = (b.ts[a] // 86400) * 86400
        starts = d0[:, None] + rng.integers(0, 288, (len(tr), N_MONKEYS)) * 300
    else:                     # n'importe quel jour, même heure
        tod = b.ts[a] % 86400
        first, last = int(b.ts[0]) // 86400 + 1, int(b.ts[-1]) // 86400 - 4
        starts = rng.integers(first, last, (len(tr), N_MONKEYS)) * 86400 + tod[:, None]
    ia = np.clip(np.searchsorted(b.ts, starts), 0, len(b.ts) - 1)
    ib = np.clip(np.searchsorted(b.ts, starts + dur[:, None]), 0, len(b.ts) - 1)
    mk = sg[:, None] * (b.op[ib] - b.op[ia]) / b.op[ia] * 100 - COST
    return mk.mean(0)


def judge(b: Bars, tr: list[Trade], name: str, mode: str) -> dict[str, Any]:
    last_year = datetime.fromtimestamp(int(b.ts[-1]), UTC).year
    a = np.array([x[0] for x in tr])
    e = np.array([x[2] for x in tr]); px = np.array([x[3] for x in tr]); sg = np.array([x[4] for x in tr])
    gross = sg * (px - e) / e * 100
    net = gross - COST
    t_in = b.ts[a]
    yrs: dict[int, list[float]] = {}
    for t, r in zip(t_in, net):
        yrs.setdefault(datetime.fromtimestamp(int(t), UTC).year, []).append(float(r))
    full = {y: v for y, v in yrs.items() if y < last_year and y > 2017}
    pos = sum(1 for v in full.values() if sum(v) > 0)
    means = monkeys(b, tr, mode, np.random.default_rng(zlib.crc32(f"essai30:{name}".encode())))
    sd = float(means.std(ddof=1))
    real = float(net.mean())
    mean = lambda m: round(float(net[m].mean()), 4) if m.any() else None  # noqa: E731
    hold = float(np.median(b.ts[np.array([x[1] for x in tr])] - t_in)) / 3600
    v = {"n": len(tr), "hold_hours": round(hold, 1), "gross_pct": round(float(gross.mean()), 4), "net_pct": round(real, 4),
         "win_rate": round(float((net > 0).mean()), 3), "positive_years": f"{pos}/{len(full)}",
         "years": {str(y): round(sum(x) / len(x), 4) for y, x in sorted(yrs.items())},
         "before_2020": mean(t_in < HALF), "since_2020": mean(t_in >= HALF), "last_2_years": mean(t_in >= RECENT),
         "fees_x2": round(float((gross - 2 * COST).mean()), 4), "monkey_mode": mode,
         "monkeys": {"mean_pct": round(float(means.mean()), 4), "beaten": int((means < real).sum()),
                     "z": round((real - float(means.mean())) / sd, 2) if sd > 0 else None}}
    v["checks"] = {"200 trades": len(tr) >= MIN_TRADES, "> 0": real > 0, "60 % des années": pos >= 0.6 * len(full),
                   "deux moitiés": (v["before_2020"] or 0) > 0 and (v["since_2020"] or 0) > 0,
                   "2 dernières années": (v["last_2_years"] or 0) > 0, "frais doublés": v["fees_x2"] > 0,
                   "singes": v["monkeys"]["beaten"] >= 950}
    v["robust"] = all(v["checks"].values())
    return v


def run(candles, log=print) -> dict[str, Any]:
    b = Bars(candles)
    out: dict[str, Any] = {"essai": 30, "cost_pct": COST, "cells": {}}
    for name, (fn, mode) in cells(b).items():
        v = judge(b, fn(), name, mode)
        out["cells"][name] = v
        failed = [k for k, ok in v["checks"].items() if not ok]
        log(f"{name:40s} n={v['n']:5d} {v['hold_hours']} h net {v['net_pct']:+.4f} % brut {v['gross_pct']:+.4f} "
            f"années {v['positive_years']} av.2020 {v['before_2020']} depuis {v['since_2020']} récent {v['last_2_years']} "
            f"frais×2 {v['fees_x2']} singes {v['monkeys']['beaten']} z {v['monkeys']['z']} → "
            f"{'ROBUSTE' if not failed else 'échoue : ' + ', '.join(failed)}")
    z_thr = NormalDist().inv_cdf(1 - 0.05 / len(out["cells"]))
    out["z_threshold"] = round(z_thr, 2)
    for v in out["cells"].values():
        v["status"] = ("prouvé" if v["robust"] and (v["monkeys"]["z"] or 0) > z_thr
                       else "robuste" if v["robust"] else "pas robuste")
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .essai23 import load
    from .models import iso, utcnow
    eng = Engine(load_config())
    new = eng.store.load_history("bitcoin")
    candles = [c for c in load(eng.store.dir / "history" / "long" / "bitcoin_5m.json") if c.ts < new[0].ts] + new
    out = run(candles, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    for k, v in out["cells"].items():
        print(f"{k:40s} {v['status']}", flush=True)
    eng.store._write(eng.store.dir / "essai30.json", out)


if __name__ == "__main__":
    main()
