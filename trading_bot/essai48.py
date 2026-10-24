"""Essai 48 : tasse avec anse (cup and handle), vidéo TikTok @_trading_elite_ (24/10/2026). Règles dans HYPOTHESES.md.

    python -m trading_bot.essai48
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
LONG = ROOT / "data" / "history" / "long"
COSTS = {"nasdaq": lambda p: 1.25, "gold": lambda p: 0.35, "bitcoin": lambda p: p * 0.001}
PIV, ATR_N = 5, 14
CUP_MIN, CUP_MAX, DEPTH_ATR = 20, 150, 4.0
RIM_TOL, H_MIN, H_MAX, H_RET_MIN, H_RET_MAX, BREAK_MAX = 0.15, 3, 30, 0.10, 0.50, 30
HOLD = 5 * 48
MONKEYS = 500


def bars30(path: Path):
    rows = np.array(json.loads(path.read_text(encoding="utf-8")), dtype=float)
    key = (rows[:, 0] // 1800).astype(np.int64)
    cut = np.flatnonzero(np.diff(key)) + 1
    idx = np.split(np.arange(len(rows)), cut)
    ts = np.array([key[g[0]] * 1800 for g in idx])
    o = np.array([rows[g[0], 1] for g in idx])
    h = np.array([rows[g, 2].max() for g in idx])
    lo = np.array([rows[g, 3].min() for g in idx])
    c = np.array([rows[g[-1], 4] for g in idx])
    return ts, o, h, lo, c


def atr(h, lo, c):
    tr = np.maximum(h - lo, np.maximum(abs(h - np.roll(c, 1)), abs(lo - np.roll(c, 1))))
    out = np.convolve(tr, np.ones(ATR_N) / ATR_N)[:len(tr)]
    out[:ATR_N] = np.nan
    return out


def setups(ts, h, lo, c, a):
    n = len(c)
    piv = [i for i in range(PIV, n - PIV) if h[i] == h[i - PIV:i + PIV + 1].max()]
    out, last_entry = [], -1
    for k, r in enumerate(piv):                       # r = bord droit (connu PIV bougies plus tard)
        for left in reversed(piv[:k]):
            span = r - left
            if span < CUP_MIN:
                continue
            if span > CUP_MAX:
                break
            res = max(h[left], h[r])
            bot = left + int(np.argmin(lo[left:r + 1]))
            depth = min(h[left], h[r]) - lo[bot]
            if np.isnan(a[r]) or depth < DEPTH_ATR * a[r] or abs(h[left] - h[r]) > RIM_TOL * depth:
                continue
            if not (left + span / 3 <= bot <= r - span / 3) or h[left + 1:r].max() > res:
                continue
            # anse puis cassure, à partir du moment où le bord droit est confirmé
            for j in range(r + PIV, min(r + BREAK_MAX, n - 1) + 1):
                hl = lo[r + 1:j].min() if j > r + 1 else lo[r]
                ret = (h[r] - hl) / depth
                if ret > H_RET_MAX or h[r + 1:j].max(initial=0) > res:
                    break
                if c[j] > res:
                    if j - r >= H_MIN and ret >= H_RET_MIN and j > last_entry and c[j] - hl > 0:
                        out.append((j, c[j], hl, c[j] + depth))
                        last_entry = j + HOLD
                    break
            break
    return out


def outcome(j, entry, stop, target, h, lo, c, ts, cost):
    risk = entry - stop
    end = min(j + HOLD, len(c) - 1)
    ex = c[end]
    for t in range(j + 1, end + 1):
        if ts[t] - ts[t - 1] > 4 * 86400:             # trou dans les données
            ex = c[t - 1]
            break
        if lo[t] <= stop:
            ex = stop
            break
        if h[t] >= target:
            ex = target
            break
    return (ex - entry - cost) / risk


def main() -> None:
    rng = np.random.default_rng(48)
    res = {}
    for m in ("gold", "nasdaq", "bitcoin"):
        ts, o, h, lo, c = bars30(LONG / f"{m}_5m.json")
        a = atr(h, lo, c)
        su = setups(ts, h, lo, c, a)
        cost = COSTS[m]
        rs = np.array([outcome(j, e, s, t, h, lo, c, ts, cost(e)) for j, e, s, t in su])
        yrs = np.array([datetime.fromtimestamp(int(ts[j]), timezone.utc).year for j, *_ in su])
        slot = ts % 86400
        by_slot = {}
        for i, s_ in enumerate(slot):
            by_slot.setdefault(int(s_), []).append(i)
        monkeys = []
        for _ in range(MONKEYS):
            mr = []
            for j, e, s, t in su:
                cand = by_slot[int(slot[j])]
                k = cand[rng.integers(len(cand))]
                if k + HOLD >= len(c):
                    continue
                d_s, d_t = (e - s) / e, (t - e) / e
                px = c[k]
                mr.append(outcome(k, px, px * (1 - d_s), px * (1 + d_t), h, lo, c, ts, cost(px)))
            monkeys.append(np.mean(mr))
        a1, b1 = rs[yrs <= 2019], rs[yrs >= 2020]
        res[m] = {"trades": len(rs), "R": round(float(rs.mean()), 3) if len(rs) else None,
                  "2014-2019": round(float(a1.mean()), 3) if len(a1) else None,
                  "2020+": round(float(b1.mean()), 3) if len(b1) else None,
                  "objectif_touche": round(float(np.mean(rs > 0.5)), 3) if len(rs) else None,
                  "singes": round(float(np.mean(monkeys)), 3),
                  "bat_singes": round(float(np.mean(np.array(monkeys) < rs.mean())), 3) if len(rs) else None,
                  "periode": [datetime.fromtimestamp(int(ts[0]), timezone.utc).date().isoformat(),
                              datetime.fromtimestamp(int(ts[-1]), timezone.utc).date().isoformat()]}
        print(m, json.dumps(res[m], ensure_ascii=False), flush=True)
    (ROOT / "data" / "essai48.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
