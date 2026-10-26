"""Essai 53 : la stratégie de BENAGOLD reconstituée d'après ses signaux, rejouée sur l'or 5 min. Règles dans HYPOTHESES.md.

    python -m trading_bot.essai53
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

PA = ZoneInfo("Europe/Paris")
ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "data" / "history" / "long" / "gold_5m.json"
COST, MOVE, NEAR, STOP, TPS, HOLD, MONKEYS = 0.35, 0.0015, 0.0008, 0.0025, (1.0, 2.0, 3.5), 24 * 3600, 200
Z_MIN = 2.24          # 5 % unilatéral corrigé sur 4 cellules


def run(ts, h, lo, c, i, sg, e, risk, be, cost=COST):
    """R moyen des 3 parts (stop commun, objectifs 1 / 2 / 3,5 R), sortie au bout de 24 h ou avant un trou de données."""
    j1 = np.searchsorted(ts, ts[i] + HOLD, side="right")
    gap = np.nonzero(np.diff(ts[i:j1]) > 6 * 3600)[0]
    if len(gap):
        j1 = i + gap[0] + 1
    hh, ll = h[i + 1:j1], lo[i + 1:j1]
    if len(hh) == 0:
        return 0.0
    stop = e - sg * risk
    hit_stop = (ll <= stop) if sg > 0 else (hh >= stop)
    out = []
    first_tp = None
    for k in TPS:
        tgt = e + sg * k * risk
        hit = (hh >= tgt) if sg > 0 else (ll <= tgt)
        out.append((tgt, hit))
        if first_tp is None:
            first_tp = int(np.argmax(hit)) if hit.any() else None
    res = []
    for tgt, hit in out:
        st_hit = hit_stop.copy()
        if be and first_tp is not None:
            after = np.zeros(len(hh), bool)
            after[first_tp + 1:] = True
            be_hit = ((ll <= e) if sg > 0 else (hh >= e)) & after
        else:
            be_hit = np.zeros(len(hh), bool)
        ks = int(np.argmax(st_hit)) if st_hit.any() else 10 ** 9
        kb = int(np.argmax(be_hit)) if be_hit.any() else 10 ** 9
        kt = int(np.argmax(hit)) if hit.any() else 10 ** 9
        k = min(ks, kb, kt)
        if k == 10 ** 9:
            px = c[j1 - 1]
        elif k == ks:
            px = stop
        elif k == kt and kt < kb:
            px = tgt
        else:
            px = e
        res.append((sg * (px - e) - cost) / risk)
    return float(np.mean(res))


def main() -> None:
    a = np.array(json.loads(FILE.read_text(encoding="utf-8")), dtype=float)
    ts, o, h, lo, c = a[:, 0].astype(np.int64), a[:, 1], a[:, 2], a[:, 3], a[:, 4]
    loc = [datetime.fromtimestamp(int(t), PA) for t in ts]
    hour = np.array([d.hour + d.minute / 60 for d in loc])
    wd = np.array([d.weekday() for d in loc])
    day = np.array([d.toordinal() for d in loc])
    year = np.array([d.year for d in loc])
    # moyenne 20 bougies 4 h (finies) au moment de chaque clôture 5 min
    b4 = ts // (4 * 3600)
    starts = np.r_[0, np.nonzero(np.diff(b4))[0] + 1]
    c4 = c[np.r_[starts[1:] - 1, len(c) - 1]]
    m4 = np.convolve(c4, np.ones(20) / 20)[:len(c4)]
    m4[:19] = np.nan
    grp = np.searchsorted(starts, np.arange(len(c)), side="right") - 1
    mm4 = np.where(grp >= 1, m4[np.maximum(grp - 1, 0)], np.nan)
    # ouverture et plus haut / bas des 60 dernières minutes (12 bougies, la bougie qui clôture comprise)
    cells = {"F1": {}, "F2": {"be": True}, "F3": {"trend": True}, "F4": {"from": 14.0}}
    trades = {k: [] for k in cells}
    for name, cfg in cells.items():
        busy_until, count, cur_day = 0, 0, None
        for i in range(12, len(c)):
            if wd[i] >= 5:
                continue
            t_close = hour[i] + 5 / 60
            if not (cfg.get("from", 10.0) <= t_close <= 17.0):
                continue
            if ts[i] - ts[i - 11] > 3600:
                continue
            if day[i] != cur_day:
                cur_day, count = day[i], 0
            if count >= 2 or ts[i] < busy_until:
                continue
            o60, hi60, lo60 = o[i - 11], h[i - 11:i + 1].max(), lo[i - 11:i + 1].min()
            px = c[i]
            sg = 0
            if px - o60 >= MOVE * px and hi60 - px <= NEAR * px:
                sg = -1
            elif o60 - px >= MOVE * px and px - lo60 <= NEAR * px:
                sg = 1
            if sg == 0:
                continue
            if cfg.get("trend") and not (np.isfinite(mm4[i]) and sg * (px - mm4[i]) > 0):
                continue
            risk = STOP * px
            r = run(ts, h, lo, c, i, sg, px, risk, cfg.get("be", False))
            r2 = run(ts, h, lo, c, i, sg, px, risk, cfg.get("be", False), cost=2 * COST)
            trades[name].append((i, sg, r, r2, int(year[i])))
            count += 1
            busy_until = ts[i] + HOLD          # approximation prudente : un trade à la fois tant qu'il peut vivre
            j = np.searchsorted(ts, ts[i] + HOLD)
            # libère plus tôt si le trade est fini (stop ou dernier objectif) : on rejoue la sortie la plus lointaine
            hh, ll = h[i + 1:j], lo[i + 1:j]
            stop = px - sg * risk
            tgt = px + sg * TPS[-1] * risk
            done = ((ll <= stop) | (hh >= tgt)) if sg > 0 else ((hh >= stop) | (ll <= tgt))
            if done.any():
                busy_until = ts[i + 1 + int(np.argmax(done))] + 1

    rng = np.random.default_rng(53)
    slot = ts % 86400
    by_slot: dict[int, np.ndarray] = {}
    order = np.argsort(slot, kind="stable")
    ss = slot[order]
    cut = np.r_[0, np.nonzero(np.diff(ss))[0] + 1, len(ss)]
    for a0, b0 in zip(cut[:-1], cut[1:]):
        by_slot[int(ss[a0])] = order[a0:b0]
    res = {"donnees": f"{datetime.fromtimestamp(int(ts[0]), PA):%Y-%m-%d} → {datetime.fromtimestamp(int(ts[-1]), PA):%Y-%m-%d}"}
    for name, tl in trades.items():
        r = np.array([t[2] for t in tl])
        r2 = np.array([t[3] for t in tl])
        yrs = np.array([t[4] for t in tl])
        be = cells[name].get("be", False)
        monkeys = []
        for _ in range(MONKEYS):
            mr = []
            for i, sg, *_ in tl:
                cand = by_slot[int(slot[i])]
                k = int(cand[rng.integers(len(cand))])
                if k >= len(c) - 2:
                    k = len(c) - 3
                s2 = int(rng.choice([1, -1]))
                mr.append(run(ts, h, lo, c, k, s2, c[k], STOP * c[k], be))
            monkeys.append(np.mean(mr))
        monkeys = np.array(monkeys)
        per_year = {int(y): round(float(r[yrs == y].mean()), 3) for y in sorted(set(yrs))}
        z = float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if len(r) > 1 else 0.0
        a1, b1 = r[yrs <= 2019], r[yrs >= 2020]
        checks = {"200 trades": len(r) >= 200, "2014-2019 > 0": a1.mean() > 0, "2020+ > 0": b1.mean() > 0,
                  "60 % des années": np.mean([v > 0 for v in per_year.values()]) >= 0.6, "frais x2 > 0": r2.mean() > 0,
                  "singes 95 %": float(np.mean(monkeys < r.mean())) >= 0.95, f"z ≥ {Z_MIN}": z >= Z_MIN}
        res[name] = {"trades": len(r), "R": round(float(r.mean()), 3), "gagnants": round(float((r > 0).mean()), 3),
                     "2014-2019": round(float(a1.mean()), 3), "2020+": round(float(b1.mean()), 3),
                     "frais_x2": round(float(r2.mean()), 3), "ventes": int(sum(1 for t in tl if t[1] < 0)),
                     "singes": round(float(monkeys.mean()), 3), "bat_singes": round(float(np.mean(monkeys < r.mean())), 3),
                     "z": round(z, 2), "par_an": per_year, "controles": {k: bool(v) for k, v in checks.items()},
                     "passe": bool(all(checks.values()))}
        print(name, json.dumps(res[name], ensure_ascii=False), flush=True)
    (ROOT / "data" / "essai53.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
