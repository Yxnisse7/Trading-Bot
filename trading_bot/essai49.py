"""Essai 49 : « liquidity sweep » sur l'or (vidéo TikTok @arlo.fx, 24/10/2026). Règles dans HYPOTHESES.md.

    python -m trading_bot.essai49
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

NY, LDN = ZoneInfo("America/New_York"), ZoneInfo("Europe/London")
ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "data" / "history" / "long" / "gold_5m.json"
COST, ATR_N, LOOK, CONFIRM, ROOM, MONKEYS = 0.35, 14, 6, 12, 0.25, 500


def session(ts: int):
    """Jour de séance (18:00 → 17:00 New York)."""
    d = datetime.fromtimestamp(ts, NY)
    return (d + timedelta(hours=6)).date()


def main() -> None:
    a = np.array(json.loads(FILE.read_text(encoding="utf-8")), dtype=float)
    ts, h, lo, c = a[:, 0].astype(np.int64), a[:, 2], a[:, 3], a[:, 4]
    tr = h - lo
    atr = np.convolve(tr, np.ones(ATR_N) / ATR_N)[:len(tr)]
    sess = np.array([session(int(t)) for t in ts])
    days = {}
    for i, s in enumerate(sess):
        days.setdefault(s, [i, i])[1] = i
    keys = sorted(days)
    trades = {"A": [], "B": []}
    for k in range(1, len(keys)):
        prev, cur = days[keys[k - 1]], days[keys[k]]
        pdh, pdl = h[prev[0]:prev[1] + 1].max(), lo[prev[0]:prev[1] + 1].min()
        d0 = keys[k]
        start = int(datetime(d0.year, d0.month, d0.day, 8, 0, tzinfo=LDN).timestamp())
        stop_t = int(datetime(d0.year, d0.month, d0.day, 12, 0, tzinfo=NY).timestamp())
        close_t = int(datetime(d0.year, d0.month, d0.day, 17, 0, tzinfo=NY).timestamp())
        live = {"high": True, "low": True}
        setup = None
        for i in range(cur[0], cur[1] + 1):
            if ts[i] < start:
                if c[i] > pdh: live["high"] = False
                if c[i] < pdl: live["low"] = False
                continue
            if ts[i] >= stop_t:
                break
            if i < LOOK:
                continue
            if live["high"] and h[i] > pdh and c[i] < pdh:
                setup = (i, -1, h[i], lo[i - LOOK:i].min())
            elif live["low"] and lo[i] < pdl and c[i] > pdl:
                setup = (i, 1, lo[i], h[i - LOOK:i].max())
            else:
                if c[i] > pdh: live["high"] = False
                if c[i] < pdl: live["low"] = False
                continue
            break
        if setup is None:
            continue
        i0, sg, wick, level = setup
        entry_i = None
        for j in range(i0 + 1, min(i0 + 1 + CONFIRM, cur[1] + 1)):
            if (h[j] > wick) if sg < 0 else (lo[j] < wick):
                break
            if (c[j] < level) if sg < 0 else (c[j] > level):
                entry_i = j
                break
        if entry_i is None:
            continue
        e = c[entry_i]
        stop = wick - sg * ROOM * atr[i0]
        risk = abs(e - stop)
        if risk <= 0:
            continue
        for v, tgt in (("A", e + sg * 2 * risk), ("B", pdl if sg < 0 else pdh)):
            if (tgt - e) * sg < risk:
                tgt = e + sg * risk
            trades[v].append((entry_i, sg, e, stop, tgt, close_t, d0.year))

    def run(i, sg, e, stop, tgt, close_t):
        ex = None
        for j in range(i + 1, len(ts)):
            if ts[j] >= close_t or ts[j] - ts[j - 1] > 3600 * 6:
                ex = c[j - 1]
                break
            if (lo[j] <= stop) if sg > 0 else (h[j] >= stop):
                ex = stop
                break
            if (h[j] >= tgt) if sg > 0 else (lo[j] <= tgt):
                ex = tgt
                break
        if ex is None:
            ex = c[-1]
        return (sg * (ex - e) - COST) / abs(e - stop)

    rng = np.random.default_rng(49)
    slot = ts % 86400
    by_slot = {}
    for i, s in enumerate(slot):
        by_slot.setdefault(int(s), []).append(i)
    res = {}
    for v, tl in trades.items():
        r = np.array([run(*t[:6]) for t in tl])
        yrs = np.array([t[6] for t in tl])
        monkeys = []
        for _ in range(MONKEYS):
            mr = []
            for i, sg, e, stop, tgt, close_t, _y in tl:
                cand = by_slot[int(slot[i])]
                k = cand[rng.integers(len(cand))]
                s2 = int(rng.choice([1, -1]))
                px = c[k]
                mr.append(run(k, s2, px, px - s2 * abs(e - stop), px + s2 * abs(tgt - e), ts[k] + (close_t - ts[i])))
            monkeys.append(np.mean(mr))
        a1, b1 = r[yrs <= 2019], r[yrs >= 2020]
        res[v] = {"trades": len(r), "R": round(float(r.mean()), 3), "2014-2019": round(float(a1.mean()), 3),
                  "2020+": round(float(b1.mean()), 3), "gagnants": round(float((r > 0).mean()), 3),
                  "ventes": int(sum(1 for t in tl if t[1] < 0)), "singes": round(float(np.mean(monkeys)), 3),
                  "bat_singes": round(float(np.mean(np.array(monkeys) < r.mean())), 3),
                  "par_an": {int(y): round(float(r[yrs == y].mean()), 3) for y in sorted(set(yrs))}}
        print(v, json.dumps(res[v], ensure_ascii=False), flush=True)
    (ROOT / "data" / "essai49.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
