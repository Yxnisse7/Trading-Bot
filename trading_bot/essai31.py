"""Essai 31 (HYPOTHESES.md) : pétrole et euro sur 2014-2026.

Partie A : les 54 stratégies de l'essai 24 (bot compris) avec les contrôles de l'essai 24.
Partie B : 11 idées trouvées par une recherche large, contrôles de l'essai 30.

    python -m trading_bot.essai31 --bot     → rejoue le bot (cache data/history/long/essai31_bot_<actif>.json)
    python -m trading_bot.essai31           → data/essai31.json
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable
from zoneinfo import ZoneInfo

import numpy as np

from . import essai14 as e14
from . import essai15 as e15
from . import essai17 as e17
from . import essai22 as e22
from . import essai24 as e24
from . import essai30 as e30
from . import strategies as sl
from .essai21 import FILTER_CELLS, Bars as Bars21, bot_cost, judge as judge21
from .essai23 import load

ASSETS = ("oil", "euro")
OPEN = {"oil": (9, 0), "euro": (8, 20)}          # ouverture de la séance de jour (New York)
LONDON, FRANKFURT = ZoneInfo("Europe/London"), ZoneInfo("Europe/Berlin")
NY = sl.NY
Trade = e30.Trade


def candles(root: Path, key: str):
    return load(root / "history" / "long" / f"{key}_5m.json")


def bot_rows(cfg, root: Path, key: str, real) -> list[dict]:
    cache = root / "history" / "long" / f"essai31_bot_{key}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    from .backtest import run_backtest
    rows = run_backtest(cfg.assets[key], real, cfg)["trades"]
    cache.write_text(json.dumps(rows), encoding="utf-8")
    return rows


# ------------------------------------------------------------------ partie A
def part_a(cfg, root: Path, log) -> dict[str, Any]:
    e14.OPEN_NY.update(OPEN)
    out: dict[str, Any] = {}
    for key in ASSETS:
        real = candles(root, key)
        ctx = e15.Ctx(real)
        base = sorted(e14.bot_trades(bot_rows(cfg, root, key, real), key), key=lambda t: t.entry_ts)
        cost, label = bot_cost(key, cfg)
        bars = Bars21(real)
        keys, closes = e22.daily_closes(ctx)
        last_year = datetime.fromtimestamp(real[-1].ts, timezone.utc).year
        for name, trades in e17.cells(key, real, real, ctx, None, base, cfg.assets[key].cost_pct):
            trades = sorted((t for t in trades if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
            v = e24.checks(trades, cost, keys, closes, last_year)
            m = judge21(name, key, trades, bars, cost, base) if trades else {}
            a, f = m.get("all") or {}, m.get("filter_monkeys")
            v["monkeys"] = {"beaten": a.get("beaten"), "z": a.get("z"),
                            "filter_beaten": None if f is None else f.get("beaten")}
            v["checks"]["singes"] = (a.get("beaten") or 0) >= 950 and (
                name not in FILTER_CELLS or f is None or f.get("beaten", 0) >= 950)
            v.update({"idea": name, "asset": key, "fees": label, "robust": all(v["checks"].values())})
            out[f"{name}:{key}"] = v
            log(e24.line(v))
    judged = [v for v in out.values() if v["monkeys"]["z"] is not None]
    z_thr = NormalDist().inv_cdf(1 - 0.05 / max(1, len(judged)))
    for v in out.values():
        v["status"] = ("prouvée" if v["robust"] and (v["monkeys"]["z"] or 0) > z_thr
                       else "robuste" if v["robust"] else "pas robuste")
    return {"z_threshold": round(z_thr, 2), "cells": out}


# ------------------------------------------------------------------ partie B
def _px(b: e30.Bars, d: date, hh: int, mm: int, tz) -> float | None:
    return e30._op(b, b.at(e30._ts(d, hh, mm, tz)))


def signed(b: e30.Bars, sig: Callable[[date], tuple | None], hin, hout, tz=NY, weekdays=range(5)) -> list[Trade]:
    """sig(d) → (prix de départ, prix d'arrivée, suivre=+1/contre=−1) ; trade entre hin et hout dans ce sens."""
    def sign(d: date) -> int | None:
        if d.weekday() not in weekdays:
            return None
        s = sig(d)
        if s is None or s[0] is None or s[1] is None or s[0] == s[1]:
            return None
        return (1 if s[1] > s[0] else -1) * s[2]
    return e30.timed(b, hin, hout, sign, tz)


def prev_wd(d: date) -> date:
    d -= timedelta(days=1)
    while d.weekday() > 4:
        d -= timedelta(days=1)
    return d


def orb_band(b: e30.Bars, q: float = 1.28) -> list[Trade]:
    """P4 : bande autour de l'ouverture 09:00 = moyenne + q × écart-type des 60 rendements 09:00 → 14:30 d'avant."""
    out, hist = [], []
    for d in b.days:
        if d.weekday() > 4:
            continue
        a, z = b.at(e30._ts(d, 9, 0, NY)), b.at(e30._ts(d, 14, 30, NY))
        if a is None or z is None or z <= a:
            continue
        o = float(b.op[a])
        if len(hist) >= 60:
            mu, sd = float(np.mean(hist[-60:])), float(np.std(hist[-60:]))
            up, dn = o * (1 + abs(mu) + q * sd), o * (1 - abs(mu) - q * sd)
            for k in range(a, z):
                if b.hi[k] >= up or b.lo[k] <= dn:
                    if b.hi[k] >= up and b.lo[k] <= dn:
                        break                              # les deux dans la même bougie : on s'abstient
                    side = 1 if b.hi[k] >= up else -1
                    lvl = up if side == 1 else dn
                    e = max(lvl, b.op[k]) if side == 1 else min(lvl, b.op[k])
                    if k + 1 < z:
                        out.append((k, z, float(e), float(b.op[z]), side))
                    break
        hist.append(float(b.op[z]) / o - 1)
    return out


def eia_fade(b: e30.Bars) -> list[Trade]:
    """P5 : mercredi, bougie 10:30-10:35 au-delà de 2 σ (σ des 52 mercredis d'avant) → contre, sortie 11:00."""
    out, hist = [], []
    for d in b.days:
        if d.weekday() != 2:
            continue
        a0, a, z = b.at(e30._ts(d, 10, 30, NY)), b.at(e30._ts(d, 10, 35, NY)), b.at(e30._ts(d, 11, 0, NY))
        if a0 is None or a is None or z is None or not a0 < a < z:
            continue
        r = float(b.op[a]) / float(b.op[a0]) - 1
        if len(hist) >= 26 and abs(r) > 2 * float(np.std(hist[-52:])):
            out.append((a, z, float(b.op[a]), float(b.op[z]), -1 if r > 0 else 1))
        hist.append(r)
    return out


def api(b: e30.Bars) -> list[Trade]:
    """P6 : mardi, sens de 16:30 → 17:00 (rapport API) ; position de 18:00 à 10:25 le lendemain (avant l'EIA)."""
    def sign(d: date) -> int | None:
        if d.weekday() != 1:
            return None
        p0, p1 = _px(b, d, 16, 30, NY), _px(b, d, 17, 0, NY)
        return None if p0 is None or p1 is None or p0 == p1 else (1 if p1 > p0 else -1)
    return e30.timed(b, (18, 0), (10, 25), sign, NY, next_day=True)


def cells_b(b: e30.Bars, key: str) -> dict[str, tuple[Callable[[], list[Trade]], str]]:
    if key == "oil":
        return {
            "P1 suite du rapport EIA": (lambda: signed(b, lambda d: (_px(b, d, 10, 30, NY), _px(b, d, 11, 0, NY), 1),
                                                       (14, 0), (14, 30), weekdays=(2,)), "jour"),
            "P2 la matinée prédit la clôture": (lambda: signed(b, lambda d: (_px(b, prev_wd(d), 14, 30, NY),
                                                                             _px(b, d, 10, 0, NY), 1), (14, 0), (14, 30),
                                                               weekdays=(0, 1, 3, 4)), "jour"),
            "P3 la journée prédit la clôture": (lambda: signed(b, lambda d: (_px(b, prev_wd(d), 14, 30, NY),
                                                                             _px(b, d, 14, 0, NY), 1), (14, 0), (14, 30)),
                                                "jour"),
            "P4 cassure de bande à l'ouverture": (lambda: orb_band(b), "heure"),
            "P5 contre le rapport EIA": (lambda: eia_fade(b), "heure"),
            "P6 rapport API la veille": (lambda: api(b), "jour"),
        }
    return {
        "E1a vente avant le fixing BCE": (lambda: _cross_tz(b, (2, 0, NY), (14, 15, FRANKFURT), -1), "jour"),
        "E1b achat après le fixing de Londres": (lambda: _cross_tz(b, (16, 0, LONDON), (17, 0, NY), 1), "jour"),
        "E2a vente pendant Londres": (lambda: e30.timed(b, (3, 0), (11, 0), lambda d: -1 if d.weekday() < 5 else None, NY),
                                      "jour"),
        "E2b achat l'après-midi new-yorkais": (lambda: e30.timed(b, (11, 0), (16, 0), lambda d: 1 if d.weekday() < 5 else None,
                                                                 NY), "jour"),
        "E6 la journée prédit la clôture": (lambda: signed(b, lambda d: (_px(b, prev_wd(d), 15, 0, NY),
                                                                         _px(b, d, 14, 30, NY), 1), (14, 30), (15, 0)),
                                            "jour"),
    }


def _cross_tz(b: e30.Bars, t_in, t_out, sign: int) -> list[Trade]:
    out = []
    for d in b.days:
        if d.weekday() > 4:
            continue
        a, z = b.at(e30._ts(d, t_in[0], t_in[1], t_in[2])), b.at(e30._ts(d, t_out[0], t_out[1], t_out[2]))
        if a is not None and z is not None and z > a:
            out.append((a, z, float(b.op[a]), float(b.op[z]), sign))
    return out


def part_b(cfg, root: Path, log) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in ASSETS:
        b = e30.Bars(candles(root, key))
        e30.COST = cfg.assets[key].cost_pct
        for name, (fn, mode) in cells_b(b, key).items():
            tr = fn()
            if len(tr) < 30:
                v = {"n": len(tr), "robust": False, "checks": {"200 trades": False}, "monkeys": {"z": None}}
            else:
                v = e30.judge(b, tr, f"essai31:{name}", mode)
            v["cost_pct"] = e30.COST
            out[name] = v
            failed = [k for k, ok in v["checks"].items() if not ok]
            log(f"{name:40s} n={v['n']:5d} net {v.get('net_pct')} brut {v.get('gross_pct')} années {v.get('positive_years')} "
                f"av.2020 {v.get('before_2020')} depuis {v.get('since_2020')} récent {v.get('last_2_years')} "
                f"frais×2 {v.get('fees_x2')} singes {v['monkeys'].get('beaten')} z {v['monkeys'].get('z')} → "
                f"{'ROBUSTE' if not failed else 'échoue : ' + ', '.join(failed)}")
    z_thr = NormalDist().inv_cdf(1 - 0.05 / len(out))
    for v in out.values():
        v["status"] = ("prouvé" if v["robust"] and (v["monkeys"]["z"] or 0) > z_thr
                       else "robuste" if v["robust"] else "pas robuste")
    return {"z_threshold": round(z_thr, 2), "cells": out}


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    log = lambda s: print(s, flush=True)  # noqa: E731
    if "--bot" in sys.argv:
        for key in ASSETS:
            rows = bot_rows(eng.cfg, eng.store.dir, key, candles(eng.store.dir, key))
            print(key, len(rows), "trades rejoués", flush=True)
        return
    out = {"essai": 31, "B": part_b(eng.cfg, eng.store.dir, log), "A": part_a(eng.cfg, eng.store.dir, log)}
    out["updated_at"] = iso(utcnow())
    for part in ("A", "B"):
        for k, v in out[part]["cells"].items():
            if v["status"] != "pas robuste":
                print(part, k, v["status"], flush=True)
    eng.store._write(eng.store.dir / "essai31.json", out)


if __name__ == "__main__":
    main()
