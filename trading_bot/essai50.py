"""Essai 50 (HYPOTHESES.md) : zone de bruit Nasdaq, demande de Yanisse (26/10/2026).

Référence B = `noise_area_v2` (en réel). E1 : entrée dès qu'une bougie 5 min clôture hors zone (10:00-15:30), sortie
comme B. E2 : entrée et sortie (sous max(borne, VWAP)) vérifiées à chaque bougie 5 min, stop dur gardé. S1 : entrée
aux demi-heures, stop = bord de la zone qui se déplace à chaque bougie (touché en cours de bougie), plus de VWAP ni
de stop dur. S2 : entrée dès la sortie + stop sur le bord. R = risque de B (écart à max(borne, VWAP), au moins
1 ATR 15 min) pour toutes, pour comparer. Bougies 2014-2026 comme l'essai 24, frais et singes de l'essai 21.

    python -m trading_bot.essai50          → data/essai50.json
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

from . import strategies as sl
from .essai21 import Bars, bot_cost, judge, real_rs
from .essai23 import load

HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
CELLS = {"B": ("30", "30", "v2"), "E1": ("5", "30", "v2"), "E2": ("5", "5", "v2"),
         "S1": ("30", "30", "bord"), "S2": ("5", "30", "bord")}


def noise(s: sl._Series, name: str, entry_every: str, exit_every: str, stop_mode: str, lookback: int = 14,
          trigger: float | None = None, margin: float = 0.0):
    """trigger/margin (essai 51) : stop fixe de B, puis dès +trigger R atteint, stop au bord de la zone − margin
    ATR 15 min (jamais plus bas que le stop fixe), déplacé à chaque bougie."""
    atr15 = sl._atr15(s)
    out = []
    days = sl._days(s.c)
    moves: dict[date, dict[int, float]] = {}
    for d in days:
        i0 = s.at(sl._ny_ts(d, 9, 30))
        if i0 is None:
            continue
        o, m, k, end = s.c[i0].open, {}, i0, sl._ny_ts(d, 16, 0)
        while k < len(s.c) and s.c[k].ts < end:
            m[(s.c[k].ts + 300 - s.c[i0].ts) // 60] = abs(s.c[k].close / o - 1)
            k += 1
        moves[d] = m
    hist: list[date] = []
    for d in days:
        i0 = s.at(sl._ny_ts(d, 9, 30))
        pci = sl._prev_close(s, d)
        if i0 is None or pci is None or len(hist) < lookback:
            if d in moves:
                hist.append(d)
            continue
        past = hist[-lookback:]
        o, pc = s.c[i0].open, s.c[pci].close
        hb, lb_ = max(o, pc), min(o, pc)

        def bounds(minute):
            vals = [moves[p][minute] for p in past if minute in moves[p]]
            if len(vals) < lookback // 2:
                return None
            sig = sum(vals) / len(vals)
            return hb * (1 + sig), lb_ * (1 - sig)

        t10, t1530, end = sl._ny_ts(d, 10, 0), sl._ny_ts(d, 15, 30), sl._ny_ts(d, 16, 0)
        pv = vv = 0.0
        k, pos, prev_bd = i0, None, None          # pos = (sens, entrée, risque, i_entrée)
        while k < len(s.c) and s.c[k].ts < end:
            b = s.c[k]
            if pos is not None and k > pos[3]:
                long = pos[0] == "long"
                if stop_mode == "v2":
                    lvl = pos[1] - pos[2] if long else pos[1] + pos[2]
                    if trigger is not None and pos[4] and prev_bd and atr15[k - 1]:
                        e = (prev_bd[0] - margin * atr15[k - 1]) if long else (prev_bd[1] + margin * atr15[k - 1])
                        lvl = max(lvl, e) if long else min(lvl, e)
                else:
                    lvl = (prev_bd[0] if long else prev_bd[1]) if prev_bd else None
                if lvl is not None and ((b.low <= lvl) if long else (b.high >= lvl)):
                    px = min(lvl, b.open) if long else max(lvl, b.open)
                    out.append(sl.Trade(name, "nasdaq", pos[0], s.c[pos[3]].ts + 300, b.ts + 300, pos[1], px, pos[2], "stop"))
                    pos = None
            if pos is not None and trigger is not None and not pos[4]:
                fav = (b.high - pos[1]) if pos[0] == "long" else (pos[1] - b.low)
                if fav >= trigger * pos[2]:
                    pos = (*pos[:4], True)
            tp = (b.high + b.low + b.close) / 3
            pv += tp * max(b.volume, 1.0)
            vv += max(b.volume, 1.0)
            ct = b.ts + 300
            bd = bounds((ct - s.c[i0].ts) // 60)
            vw = pv / vv
            half = (ct - t10) % 1800 == 0
            if bd and t10 <= ct:
                ub, lb = bd
                if pos is None and ct <= t1530 and (entry_every == "5" or half):
                    if (b.close > ub or b.close < lb) and atr15[k]:
                        long = b.close > ub
                        st = max(ub, vw) if long else min(lb, vw)
                        pos = ("long" if long else "short", b.close, max(abs(b.close - st), atr15[k]), k, False)
                elif pos is not None and stop_mode == "v2" and (exit_every == "5" or half) and k > pos[3]:
                    long = pos[0] == "long"
                    st = max(ub, vw) if long else min(lb, vw)
                    if (b.close < st) if long else (b.close > st):
                        out.append(sl.Trade(name, "nasdaq", pos[0], s.c[pos[3]].ts + 300, ct, pos[1], b.close, pos[2], "bornes"))
                        pos = None
            prev_bd = bd
            k += 1
        if pos is not None:
            last = s.c[k - 1]
            out.append(sl.Trade(name, "nasdaq", pos[0], s.c[pos[3]].ts + 300, last.ts + 300, pos[1], last.close,
                                pos[2], "fin des données" if k >= len(s.c) else "heure"))
        hist.append(d)
    return out


def main(cells=None, essai: int = 50) -> None:
    cells = cells or {k: (*v, None, 0.0) for k, v in CELLS.items()}
    from .config import load_config
    from .engine import Engine
    eng = Engine(load_config())
    cfg, store = eng.cfg, eng.store
    root = Path(__file__).resolve().parent.parent / "data"
    old = load(root / "history" / "long" / "nasdaq_5m.json")
    new = store.load_history("nasdaq")
    real = [c for c in old if c.ts < new[0].ts] + new
    s, bars = sl._Series(real), Bars(real)
    cost, label = bot_cost("nasdaq", cfg)
    out = {"essai": essai, "frais": label, "periode": [datetime.fromtimestamp(real[0].ts, timezone.utc).date().isoformat(),
                                                   datetime.fromtimestamp(real[-1].ts, timezone.utc).date().isoformat()]}
    for name, (ee, xe, sm, trig, marg) in cells.items():
        tr = sorted((t for t in noise(s, name, ee, xe, sm, trigger=trig, margin=marg) if t.reason != "fin des données" and t.risk > 0),
                    key=lambda t: t.entry_ts)
        rs = real_rs(tr, cost)
        early = np.array([t.entry_ts < HALF for t in tr])
        years: dict[int, list[float]] = {}
        for t, r in zip(tr, rs):
            years.setdefault(datetime.fromtimestamp(t.entry_ts, timezone.utc).year, []).append(float(r))
        srt = np.sort(rs)
        m = judge(f"essai{essai}:{name}", "nasdaq", tr, bars, cost)
        out[name] = {"trades": len(tr), "R": round(float(rs.mean()), 3),
                     "2014-2019": round(float(rs[early].mean()), 3), "2020+": round(float(rs[~early].mean()), 3),
                     "gagnants": round(float((rs > 0).mean()), 3),
                     "sans_5pc_meilleurs": round(float(srt[: int(len(srt) * 0.95)].mean()), 3),
                     "pire_trade": round(float(srt[0]), 2),
                     "pct_par_trade": round(float(np.mean([(t.gross_points() - cost(t.entry)) / t.entry * 100 for t in tr])), 4),
                     "annees_positives": f"{sum(1 for v in years.values() if np.mean(v) > 0)}/{len(years)}",
                     "singes": m.get("all", {})}
        print(name, json.dumps(out[name], ensure_ascii=False), flush=True)
    (root / f"essai{essai}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
