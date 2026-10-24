"""Essai 47 : « Session Momentum » (vidéo TikTok @thequantbuilder, 24/10/2026) sur le Nasdaq 5 min.

1re bougie 5 min de New York : clôture au-dessus de la moyenne exponentielle 12 → achat, en dessous → vente.
Stop initial à l'autre extrémité de la bougie. A : stop suiveur sur la moyenne 12 ; B : sans ; C : objectif 2 R.
Fermeture à 16:00 New York au plus. Frais 1,25 point. Comparé à 500 « singes » : mêmes jours, mêmes règles de
stop et de sortie, sens tiré au hasard. Voir HYPOTHESES.md.

    python -m trading_bot.essai47
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

NY = ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "data" / "history" / "long" / "nasdaq_5m.json"
COST = 1.25
MONKEYS = 500


def prepare(rows):
    a = np.array(rows, dtype=float)
    ts, o, h, lo, c = a[:, 0].astype(np.int64), a[:, 1], a[:, 2], a[:, 3], a[:, 4]
    ema = np.empty(len(c))
    k, e = 2 / 13, c[0]
    for i, x in enumerate(c):
        e += k * (x - e)
        ema[i] = e
    starts, seen = [], set()
    for i, t in enumerate(ts):
        d = datetime.fromtimestamp(int(t), NY)
        if d.hour == 9 and d.minute == 30 and d.date() not in seen:
            seen.add(d.date())
            end = i + 1
            limit = int(datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY).timestamp())
            while end < len(ts) and ts[end] < limit and end - i < 80:
                end += 1
            if end - i > 10:
                starts.append((i, end, d.year))
    return ts, h, lo, c, ema, starts


def trade(i, end, sg, h, lo, c, ema, variant):
    stop = lo[i] if sg > 0 else h[i]
    risk = abs(c[i] - stop)
    if risk < 2:                                   # 1re bougie de moins de 2 points (données creuses) : écarté
        return None
    target = c[i] + sg * 2 * risk
    exit_ = c[end - 1]
    for j in range(i + 1, end):
        if (lo[j] <= stop) if sg > 0 else (h[j] >= stop):
            exit_ = stop
            break
        if variant == "C" and ((h[j] >= target) if sg > 0 else (lo[j] <= target)):
            exit_ = target
            break
        if variant == "A" and (c[j] - ema[j]) * sg < 0:
            exit_ = c[j]
            break
    return (sg * (exit_ - c[i]) - COST) / risk


def main() -> None:
    ts, h, lo, c, ema, starts = prepare(json.loads(FILE.read_text(encoding="utf-8")))
    rng = np.random.default_rng(47)
    res = {"periode": [datetime.fromtimestamp(int(ts[starts[0][0]]), NY).date().isoformat(),
                       datetime.fromtimestamp(int(ts[starts[-1][0]]), NY).date().isoformat()]}
    for v in "ABC":
        rs, yrs, keep = [], [], []
        for n, (i, end, y) in enumerate(starts):
            if c[i] == ema[i]:
                continue
            r = trade(i, end, 1 if c[i] > ema[i] else -1, h, lo, c, ema, v)
            if r is not None:
                rs.append(r), yrs.append(y), keep.append(n)
        r, yrs = np.array(rs), np.array(yrs)
        monkeys = []
        for _ in range(MONKEYS):
            s = rng.choice([1, -1], len(keep))
            m = [trade(starts[n][0], starts[n][1], int(sg), h, lo, c, ema, v) for n, sg in zip(keep, s)]
            monkeys.append(np.mean([x for x in m if x is not None]))   # stop trop court de ce côté : écarté
        a, b = r[yrs <= 2019], r[yrs >= 2020]
        res[v] = {"trades": len(r), "R": round(float(r.mean()), 3), "R_median": round(float(np.median(r)), 3),
                  "2014-2019": round(float(a.mean()), 3), "2020+": round(float(b.mean()), 3),
                  "gagnants": round(float((r > 0).mean()), 3),
                  "sans_5pct_meilleurs": round(float(np.sort(r)[:int(len(r) * 0.95)].mean()), 3),
                  "singes_moyenne": round(float(np.mean(monkeys)), 3),
                  "bat_singes": round(float(np.mean(np.array(monkeys) < r.mean())), 3),
                  "par_an": {int(y): round(float(r[yrs == y].mean()), 3) for y in sorted(set(yrs))}}
        print(v, json.dumps(res[v], ensure_ascii=False), flush=True)
    (ROOT / "data" / "essai47.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(res["periode"])


if __name__ == "__main__":
    main()
