"""Essai 52 (HYPOTHESES.md) : stratégies de retour à la moyenne, qui visent un fort taux de réussite (demande de
Yanisse, 26/10/2026). Nasdaq, S&P 500, or, Bitcoin, 2014-2026 (bougies de l'essai 24), frais et singes de l'essai 21.

Jours : séance 9:30-16:00 New York pour les indices, jour New York 18:00 → 17:00 pour l'or, jour UTC pour Bitcoin.
Achats seulement, au-dessus de la moyenne 200 jours, entrée à la clôture du jour, stop 2 ATR 14 jours (touché sur les
bougies 5 min, nuit comprise), 10 jours au plus.
  R1 RSI(2) < 10 → sortie à la 1re clôture au-dessus de la moyenne 5 jours (Connors)
  R2 IBS < 0,2 (clôture dans les 20 % bas de la bougie du jour) → sortie à la clôture suivante
  R3 « Double 7 » : plus basse clôture de 7 jours → sortie à la plus haute clôture de 7 jours
  R4 3 jours de baisse d'affilée → sortie à la 1re clôture en hausse
  R5 (Nasdaq, S&P, 5 min) : clôture à plus de 2 écarts-types du VWAP du jour (10:00-15:00) → trade inverse,
     objectif le VWAP, stop 1 ATR 15 min, fermeture 15:55 ; les deux sens.

    python -m trading_bot.essai52          → data/essai52.json
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from . import strategies as sl
from .essai21 import Bars, bot_cost, judge, real_rs
from .essai23 import load

HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
ASSETS = ("nasdaq", "sp500", "gold", "bitcoin")


def day_key(ts: int, asset: str):
    if asset == "bitcoin":
        return datetime.fromtimestamp(ts, timezone.utc).date()
    d = datetime.fromtimestamp(ts, sl.NY)
    if asset == "gold":
        return (d + timedelta(hours=6)).date()
    m = d.hour * 60 + d.minute
    return d.date() if 570 <= m < 960 else None


def daily(c, asset):
    out = []
    for k, x in enumerate(c):
        key = day_key(x.ts, asset)
        if key is None:
            continue
        if out and out[-1][0] == key:
            r = out[-1]
            r[2], r[3], r[4], r[6] = max(r[2], x.high), min(r[3], x.low), x.close, k
        else:
            out.append([key, x.open, x.high, x.low, x.close, k, k])
    return [r for r in out if r[6] - r[5] >= 30]


def rsi2(cl):
    out = np.full(len(cl), np.nan)
    ag = al = None
    for i in range(1, len(cl)):
        ch = cl[i] - cl[i - 1]
        g, lo = max(ch, 0), max(-ch, 0)
        if i < 3:
            ag = (ag or 0) + g / 2
            al = (al or 0) + lo / 2
            continue
        ag, al = (ag + g) / 2, (al + lo) / 2
        out[i] = 100 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def daily_trades(c, asset, rule):
    D = daily(c, asset)
    cl = np.array([r[4] for r in D])
    hi, lo = np.array([r[2] for r in D]), np.array([r[3] for r in D])
    n = len(D)
    sma = lambda w: np.array([cl[max(0, i - w + 1): i + 1].mean() if i >= w - 1 else np.nan for i in range(n)])
    s200, s5 = sma(200), sma(5)
    tr = np.maximum(hi[1:] - lo[1:], np.maximum(abs(hi[1:] - cl[:-1]), abs(lo[1:] - cl[:-1])))
    atr = np.full(n, np.nan)
    for i in range(14, n):
        atr[i] = tr[i - 14:i].mean()
    r2 = rsi2(cl)
    out, i = [], 200
    while i < n - 1:
        rng_ = hi[i] - lo[i]
        sig = cl[i] > s200[i] and not np.isnan(atr[i]) and (
            rule == "R1" and r2[i] < 10 or
            rule == "R2" and rng_ > 0 and (cl[i] - lo[i]) / rng_ < 0.2 or
            rule == "R3" and cl[i] <= cl[i - 6: i + 1].min() or
            rule == "R4" and cl[i] < cl[i - 1] < cl[i - 2] < cl[i - 3])
        if not sig:
            i += 1
            continue
        entry, risk = cl[i], 2 * atr[i]
        stop = entry - risk
        k0 = D[i][6]
        px, why, j_end = None, None, None
        for j in range(i + 1, min(n, i + 11)):
            seg = range(D[j - 1][6] + 1, D[j][6] + 1)
            hit = next((k for k in seg if c[k].low <= stop), None)
            if hit is not None:
                px, why, j_end, kx = min(stop, c[hit].open), "stop", j, hit
                break
            done = (rule == "R1" and cl[j] > s5[j] or rule == "R2" or
                    rule == "R3" and cl[j] >= cl[j - 6: j + 1].max() or rule == "R4" and cl[j] > cl[j - 1])
            if done or j == i + 10:
                px, why, j_end, kx = cl[j], "règle" if done else "durée", j, D[j][6]
                break
        if px is None:
            break
        out.append(sl.Trade(rule, asset, "long", c[k0].ts + 300, c[kx].ts + 300, entry, px, risk, why))
        i = j_end + 1
    return out


def vwap_fade(c, asset):
    s = sl._Series(c)
    a15 = sl._atr15(s)
    out = []
    for d in sl._days(c):
        i0 = s.at(sl._ny_ts(d, 9, 30))
        if i0 is None:
            continue
        t10, t15, end = sl._ny_ts(d, 10, 0), sl._ny_ts(d, 15, 0), sl._ny_ts(d, 15, 55)
        sw = swp = swp2 = 0.0
        k, pos = i0, None
        while k < len(c) and c[k].ts < end:
            b = c[k]
            tp, w = (b.high + b.low + b.close) / 3, max(b.volume, 1.0)
            if pos is not None and k > pos[3]:
                long = pos[0] == "long"
                st, tg = pos[1] - pos[2] if long else pos[1] + pos[2], pos[4]
                if (b.low <= st) if long else (b.high >= st):
                    out.append(sl.Trade("R5", asset, pos[0], c[pos[3]].ts + 300, b.ts + 300, pos[1],
                                        min(st, b.open) if long else max(st, b.open), pos[2], "stop"))
                    pos = None
                elif (b.high >= tg) if long else (b.low <= tg):
                    out.append(sl.Trade("R5", asset, pos[0], c[pos[3]].ts + 300, b.ts + 300, pos[1],
                                        max(tg, b.open) if long else min(tg, b.open), pos[2], "objectif"))
                    pos = None
            sw, swp, swp2 = sw + w, swp + w * tp, swp2 + w * tp * tp
            vw = swp / sw
            sd = max(swp2 / sw - vw * vw, 0) ** 0.5
            ct = b.ts + 300
            if pos is None and t10 <= ct <= t15 and sd > 0 and a15[k]:
                if b.close > vw + 2 * sd:
                    pos = ("short", b.close, a15[k], k, vw)
                elif b.close < vw - 2 * sd:
                    pos = ("long", b.close, a15[k], k, vw)
            k += 1
        if pos is not None:
            last = c[k - 1]
            out.append(sl.Trade("R5", asset, pos[0], c[pos[3]].ts + 300, last.ts + 300, pos[1], last.close,
                                pos[2], "fin des données" if k >= len(c) else "heure"))
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    eng = Engine(load_config())
    root = Path(__file__).resolve().parent.parent / "data"
    out = {"essai": 52}
    for asset in ASSETS:
        old = load(root / "history" / "long" / f"{asset}_5m.json")
        new = eng.store.load_history(asset)
        c = [x for x in old if x.ts < new[0].ts] + new
        bars = Bars(c)
        cost, label = bot_cost(asset, eng.cfg)
        rules = ["R1", "R2", "R3", "R4"] + (["R5"] if asset in ("nasdaq", "sp500") else [])
        for rule in rules:
            tr = vwap_fade(c, asset) if rule == "R5" else daily_trades(c, asset, rule)
            tr = sorted((t for t in tr if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
            if not tr:
                continue
            rs = real_rs(tr, cost)
            early = np.array([t.entry_ts < HALF for t in tr])
            m = judge(f"essai52:{rule}", asset, tr, bars, cost)
            v = {"trades": len(tr), "R": round(float(rs.mean()), 3), "gagnants": round(float((rs > 0).mean()), 3),
                 "2014-2019": round(float(rs[early].mean()), 3) if early.any() else None,
                 "2020+": round(float(rs[~early].mean()), 3) if (~early).any() else None,
                 "gain_moyen": round(float(rs[rs > 0].mean()), 3) if (rs > 0).any() else None,
                 "perte_moyenne": round(float(rs[rs <= 0].mean()), 3) if (rs <= 0).any() else None,
                 "pct_par_trade": round(float(np.mean([(t.gross_points() - cost(t.entry)) / t.entry * 100 for t in tr])), 4),
                 "frais": label, "singes": {k: m.get("all", {}).get(k) for k in ("monkeys_r", "beaten", "z")}}
            out[f"{rule} {asset}"] = v
            print(rule, asset, json.dumps(v, ensure_ascii=False), flush=True)
    (root / "essai52.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
