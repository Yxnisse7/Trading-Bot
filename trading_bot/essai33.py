"""Essais 33 à 37 (HYPOTHESES.md) : idées des vidéos @kara_tools.

    python -m trading_bot.essai33          → data/essai33.json

Données hors dépôt (data/history/long/) : gold_1m.npz (HistData XAUUSD 1 min, UTC) et btc_5m.npz (Binance BTCUSDT
5 min avec le volume). 35 structure de marché sur l'or, 34 stop selon l'heure, 33 annonces, 36 profil de volume du
Bitcoin, 37 anciens extrêmes sur l'or.
"""
from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable
from zoneinfo import ZoneInfo

import numpy as np

from .config import DATA_DIR

UTC = timezone.utc
NY = ZoneInfo("America/New_York")
HALF = int(datetime(2020, 1, 1, tzinfo=UTC).timestamp())
RECENT = int(datetime(2024, 10, 14, tzinfo=UTC).timestamp())
GOLD_FEE = 0.30            # $ l'once aller-retour
BTC_FEE = 0.06             # % aller-retour
N_MONKEYS = 1000
MIN_TRADES = 200
LONG = Path(DATA_DIR) / "history" / "long"


def z_threshold(n: int) -> float:
    return NormalDist().inv_cdf(1 - 0.05 / n)


# ---------------------------------------------------------------- bougies

class Bars:
    def __init__(self, ts, o, h, l, c, v=None):
        self.ts, self.o, self.h, self.l, self.c = ts, o, h, l, c
        self.v = v
        self.tod = ts % 86400

    @classmethod
    def load(cls, name: str) -> "Bars":
        d = np.load(LONG / name)
        return cls(d["ts"], d["o"], d["h"], d["l"], d["c"], d["v"] if "v" in d else None)

    def resample(self, step: int) -> "Bars":
        key = self.ts // step
        cut = np.flatnonzero(np.diff(key)) + 1
        start = np.r_[0, cut]
        return Bars(key[start] * step, self.o[start], np.maximum.reduceat(self.h, start),
                    np.minimum.reduceat(self.l, start), self.c[np.r_[cut - 1, len(key) - 1]],
                    None if self.v is None else np.add.reduceat(self.v, start))


# ---------------------------------------------------------------- simulation d'un trade

def bracket(b: Bars, i: int, entry: float, sign: int, stop: float, target: float | None, max_bars: int,
            first_bar_from_entry: bool = False, cut: int | None = None) -> tuple[int, float, str]:
    """Position ouverte au prix `entry` dans la bougie i (à l'ouverture, ou en cours de bougie si
    `first_bar_from_entry`). Stop prioritaire si stop et objectif tombent dans la même bougie.
    `cut` : indice de bougie où l'on sort à l'ouverture (filtre d'annonce)."""
    end = min(len(b.ts) - 1, i + max_bars)
    for k in range(i, end):
        if cut is not None and k >= cut:
            return k, float(b.o[k]), "annonce"
        hi, lo = b.h[k], b.l[k]
        if sign > 0:
            if lo <= stop:
                return k, float(min(stop, b.o[k]) if k > i else stop), "stop"
            if target is not None and hi >= target:
                return k, float(max(target, b.o[k]) if k > i else target), "objectif"
        else:
            if hi >= stop:
                return k, float(max(stop, b.o[k]) if k > i else stop), "stop"
            if target is not None and lo <= target:
                return k, float(min(target, b.o[k]) if k > i else target), "objectif"
    return end, float(b.o[end]), "temps"


def monkeys_bracket(b: Bars, tr: list[dict], cost_fn: Callable, rng, n: int = N_MONKEYS) -> np.ndarray:
    """Singes : n'importe quel jour, même heure UTC, même sens, même stop et objectif en % du prix, même durée max.
    Renvoie le R net moyen de chaque série."""
    by_tod: dict[int, np.ndarray] = {}
    tods = b.tod
    out = np.zeros((len(tr), n))
    for j, t in enumerate(tr):
        tod = int(tods[t["i"]])
        if tod not in by_tod:
            idx = np.flatnonzero(tods == tod)
            by_tod[tod] = idx[idx < len(b.ts) - t["max"] - 1]
        pool = by_tod[tod]
        starts = pool[rng.integers(0, len(pool), n)]
        sp, tp, mb, sg = t["stop_pct"], t["target_pct"], t["max"], t["sign"]
        e = b.o[starts]
        win = starts[:, None] + np.arange(mb)[None, :]
        hi, lo = b.h[win], b.l[win]
        stop = e * (1 - sg * sp)
        if sg > 0:
            hs = lo <= stop[:, None]
            ht = hi >= (e * (1 + tp))[:, None] if tp else np.zeros_like(hs)
        else:
            hs = hi >= stop[:, None]
            ht = lo <= (e * (1 - tp))[:, None] if tp else np.zeros_like(hs)
        fs = np.where(hs.any(1), hs.argmax(1), mb)
        ft = np.where(ht.any(1), ht.argmax(1), mb)
        exit_px = b.o[starts + mb]
        exit_px = np.where(ft < fs, e * (1 + sg * tp) if tp else exit_px, exit_px)
        exit_px = np.where((fs <= ft) & (fs < mb), stop, exit_px)
        out[j] = cost_fn(sg * (exit_px - e), e, e * sp)
    return out.mean(0)


def gold_r(move, entry, risk, fee=GOLD_FEE):
    return (move - fee) / risk


def btc_r(move, entry, risk, fee=BTC_FEE):
    return (move / entry * 100 - fee) / (risk / entry * 100)


# ---------------------------------------------------------------- contrôles

def checks(b: Bars, tr: list[dict], cost_fn, rng, z_need: float, monkeys: bool = True) -> dict[str, Any]:
    if not tr:
        return {"trades": 0, "verdict": "aucun trade"}
    r = np.array([t["r"] for t in tr]); r2 = np.array([t["r2"] for t in tr])
    ts = np.array([b.ts[t["i"]] for t in tr])
    yrs = np.array([datetime.fromtimestamp(int(x), UTC).year for x in ts])
    last = datetime.fromtimestamp(int(b.ts[-1]), UTC).year
    years = {int(y): round(float(r[yrs == y].mean()), 3) for y in sorted(set(yrs)) if y < last}
    gains, losses = r[r > 0].sum(), -r[r < 0].sum()
    pf = float(gains / losses) if losses > 0 else float("inf")
    out: dict[str, Any] = {
        "trades": int(len(r)), "R": round(float(r.mean()), 3), "PF": round(pf, 2),
        "objectif": round(float(np.mean([t["why"] == "objectif" for t in tr])), 2),
        "stop": round(float(np.mean([t["why"] == "stop" for t in tr])), 2),
        "annees": years, "annees_pos": f"{sum(v > 0 for v in years.values())}/{len(years)}",
        "avant2020": round(float(r[ts < HALF].mean()), 3) if (ts < HALF).any() else None,
        "depuis2020": round(float(r[ts >= HALF].mean()), 3) if (ts >= HALF).any() else None,
        "recent": round(float(r[ts >= RECENT].mean()), 3) if (ts >= RECENT).any() else None,
        "frais_x2": round(float(r2.mean()), 3),
    }
    ok = (len(r) >= MIN_TRADES and out["R"] > 0 and pf >= 1.1
          and sum(v > 0 for v in years.values()) >= 0.6 * len(years)
          and (out["avant2020"] or 0) > 0 and (out["depuis2020"] or 0) > 0 and (out["recent"] or 0) > 0
          and out["frais_x2"] > 0)
    out["controles"] = bool(ok)
    if monkeys and ok:
        mk = monkeys_bracket(b, tr, cost_fn, rng)
        out["singes_moyen"] = round(float(mk.mean()), 3)
        out["singes_battus"] = int((mk < out["R"]).sum())
        out["z"] = round(float((out["R"] - mk.mean()) / mk.std()), 2) if mk.std() > 0 else None
        out["prouvee"] = bool(out["singes_battus"] >= 950 and (out["z"] or 0) > z_need)
    else:
        out["prouvee"] = False
    out["verdict"] = "PROUVÉE" if out["prouvee"] else ("contrôles OK, singes non" if ok else "écartée")
    return out


def paired(b: Bars, base: list[dict], var: list[dict], z_need: float) -> dict[str, Any]:
    """Contrôle apparié (essai 32) : écart trade par trade, variante − témoin."""
    d = np.array([v["r"] - t["r"] for t, v in zip(base, var)])
    vr = np.array([v["r"] for v in var])
    ts = np.array([b.ts[t["i"]] for t in base])
    yrs = np.array([datetime.fromtimestamp(int(x), UTC).year for x in ts])
    last = datetime.fromtimestamp(int(b.ts[-1]), UTC).year
    years = {int(y): round(float(d[yrs == y].mean()), 3) for y in sorted(set(yrs)) if y < last}
    z = float(d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))) if len(d) > 2 and d.std() > 0 else 0.0
    out = {"trades": int(len(d)), "temoin_R": round(float(np.mean([t["r"] for t in base])), 3),
           "variante_R": round(float(vr.mean()), 3), "ecart": round(float(d.mean()), 3),
           "avant2020": round(float(d[ts < HALF].mean()), 3), "depuis2020": round(float(d[ts >= HALF].mean()), 3),
           "recent": round(float(d[ts >= RECENT].mean()), 3) if (ts >= RECENT).any() else None,
           "annees_pos": f"{sum(v > 0 for v in years.values())}/{len(years)}", "z": round(z, 2)}
    ok = (out["ecart"] > 0 and out["avant2020"] > 0 and out["depuis2020"] > 0 and (out["recent"] or 0) > 0
          and sum(v > 0 for v in years.values()) >= 0.6 * len(years) and out["variante_R"] > 0)
    out["prouvee"] = bool(ok and z > z_need)
    out["verdict"] = "PROUVÉE" if out["prouvee"] else ("mieux mais pas prouvée" if ok else "pas mieux")
    return out


# ---------------------------------------------------------------- essai 35 : structure

def structure_signals(b: Bars, wick: bool) -> list[dict]:
    """Cassures de structure (vidéo « lire le prix »). Un creux n'est confirmé qu'à la cassure du sommet ; il vaut le
    plus bas entre le sommet et la cassure. `wick` : la cassure se fait par une mèche (sinon par une clôture)."""
    h, l, c = b.h, b.l, b.c
    trend, top, top_i, bot, bot_i = 1, h[0], 0, l[0], 0
    sig = []
    for i in range(1, len(c)):
        if trend > 0:
            if c[i] < bot:                     # creux confirmé cassé en clôture : la tendance change
                trend = -1
                lo_i = top_i + int(np.argmin(l[top_i:i + 1]))
                bot, bot_i = l[lo_i], lo_i     # creux de structure (la jambe baissière en cours)
                continue
            broke = (h[i] > top) if wick else (c[i] > top)
            if broke and i > top_i + 1:
                seg = l[top_i + 1:i]
                m_i = top_i + 1 + int(np.argmin(seg))
                m = l[m_i]
                leg = top - bot
                if leg > 0 and m < top:
                    sig.append({"i": i, "sign": 1, "level": float(top), "ext": float(m), "leg": float(leg),
                                "depth": float((top - m) / leg), "fast": bool(i - m_i < m_i - top_i)})
                    bot, bot_i = m, m_i
            if h[i] > top and (wick or c[i] > top):
                top, top_i = h[i], i
        else:
            if c[i] > top:
                trend = 1
                hi_i = bot_i + int(np.argmax(h[bot_i:i + 1]))
                top, top_i = h[hi_i], hi_i
                continue
            broke = (l[i] < bot) if wick else (c[i] < bot)
            if broke and i > bot_i + 1:
                seg = h[bot_i + 1:i]
                m_i = bot_i + 1 + int(np.argmax(seg))
                m = h[m_i]
                leg = top - bot
                if leg > 0 and m > bot:
                    sig.append({"i": i, "sign": -1, "level": float(bot), "ext": float(m), "leg": float(leg),
                                "depth": float((m - bot) / leg), "fast": bool(i - m_i < m_i - bot_i)})
                    top, top_i = m, m_i
            if l[i] < bot and (wick or c[i] < bot):
                bot, bot_i = l[i], i
    return sig


def structure_trades(b: Bars, sig: list[dict], keep: Callable[[dict], bool], wick: bool, max_bars: int = 48,
                     fee_fn=gold_r, fee: float = GOLD_FEE, block: Callable[[int], bool] | None = None,
                     cut_fn: Callable[[int, int], int | None] | None = None) -> list[dict]:
    out, busy_until = [], -1
    for s in sig:
        if not keep(s):
            continue
        i = s["i"]
        if wick:
            k = i
            entry = float(max(s["level"], b.o[i])) if s["sign"] > 0 else float(min(s["level"], b.o[i]))
        else:
            k = i + 1
            if k >= len(b.ts):
                break
            entry = float(b.o[k])
        if k <= busy_until or (block and block(int(b.ts[k]))):
            continue
        sg, stop = s["sign"], s["ext"]
        target = stop + sg * s["leg"]
        risk = sg * (entry - stop)
        if risk <= 0.0005 * entry or sg * (target - entry) <= 0:
            continue
        cut = cut_fn(k, max_bars) if cut_fn else None
        j, px, why = bracket(b, k, entry, sg, stop, target, max_bars, first_bar_from_entry=wick, cut=cut)
        out.append({"i": k, "sign": sg, "entry": entry, "stop": stop, "exit_i": j, "exit": px, "why": why,
                    "stop_pct": risk / entry, "target_pct": abs(target - entry) / entry, "max": max_bars,
                    "r": fee_fn(sg * (px - entry), entry, risk), "r2": fee_fn(sg * (px - entry), entry, risk, fee * 2)})
        busy_until = j
    return out


S_CELLS = {
    "S1 creux fort, clôture, rapide": (False, lambda s: s["depth"] >= 0.5 and s["fast"]),
    "S2 creux fort, clôture": (False, lambda s: s["depth"] >= 0.5),
    "S3 creux faible, clôture": (False, lambda s: s["depth"] < 0.25),
    "S4 creux fort, mèche, rapide": (True, lambda s: s["depth"] >= 0.5 and s["fast"]),
}


# ---------------------------------------------------------------- essai 34 : stop selon l'heure

def hour_ranges(h1: Bars) -> tuple[dict[tuple[date, int], float], dict[date, float]]:
    """Amplitude médiane de la bougie 1 h de chaque heure UTC, et toutes heures, sur les 250 jours d'avant."""
    rng = h1.h - h1.l
    days = (h1.ts // 86400).astype(np.int64)
    hours = (h1.tod // 3600).astype(np.int64)
    by_hour: dict[int, list[tuple[int, float]]] = {}
    for d, hh, x in zip(days, hours, rng):
        by_hour.setdefault(int(hh), []).append((int(d), float(x)))
    per: dict[tuple[int, int], float] = {}
    for hh, lst in by_hour.items():
        ds = np.array([d for d, _ in lst]); xs = np.array([x for _, x in lst])
        for n in range(len(ds)):
            lo = np.searchsorted(ds, ds[n] - 250)
            if n - lo >= 100:
                per[(int(ds[n]), hh)] = float(np.median(xs[lo:n]))
    glob: dict[int, float] = {}
    ud = np.unique(days)
    for d in ud:
        a, z = np.searchsorted(days, d - 250), np.searchsorted(days, d)
        if z - a >= 2000:
            glob[int(d)] = float(np.median(rng[a:z]))
    return per, glob


def hour_stop_trades(b: Bars, base: list[dict], per, glob, k: float, by_hour: bool) -> list[dict | None]:
    out: list[dict | None] = []
    for t in base:
        i, sg, e = t["i"], t["sign"], t["entry"]
        d, hh = int(b.ts[i] // 86400), int(b.tod[i] // 3600)
        ref = per.get((d, hh)) if by_hour else glob.get(d)
        if ref is None or per.get((d, hh)) is None or glob.get(d) is None:
            out.append(None)
            continue
        dist = k * ref
        stop, target = e - sg * dist, e + sg * 2 * dist
        j, px, why = bracket(b, i, e, sg, stop, target, t["max"])
        out.append({"i": i, "r": gold_r(sg * (px - e), e, dist), "r2": gold_r(sg * (px - e), e, dist, 2 * GOLD_FEE),
                    "why": why})
    return out


# ---------------------------------------------------------------- essai 33 : annonces

def event_times() -> list[int]:
    data = json.loads((Path(DATA_DIR) / "macro_events_2010_2024.json").read_text(encoding="utf-8"))
    out = []
    for kind in ("nfp", "cpi", "fomc"):
        hh, mm = (int(x) for x in data["times_ny"][kind].split(":"))
        for d in data[kind]:
            if d >= "2014-01-01":
                out.append(int(datetime.combine(date.fromisoformat(d), time(hh, mm), NY).timestamp()))
    return sorted(set(out))


def news_amplitude(m1: Bars, evs: list[int]) -> dict[str, Any]:
    pos = {int(t): n for n, t in enumerate(m1.ts)}
    rng = m1.h - m1.l
    ev_set = set(evs)
    res = []
    for e in evs:
        n = pos.get(e)
        if n is None:
            continue
        tod = e % 86400
        # même minute UTC, jours ouvrés sans annonce, 60 jours autour
        others = [rng[p] for dd in range(-30, 31) if dd
                  and (p := pos.get(e + dd * 86400)) is not None and (e + dd * 86400) not in ev_set
                  and datetime.fromtimestamp(e + dd * 86400, UTC).weekday() < 5 and (e + dd * 86400) % 86400 == tod]
        if len(others) >= 10:
            res.append((float(rng[n]), float(np.mean(others))))
    a = np.array(res)
    return {"annonces": len(a), "amplitude_annonce": round(float(a[:, 0].mean()), 2),
            "amplitude_normale": round(float(a[:, 1].mean()), 2), "rapport": round(float(a[:, 0].mean() / a[:, 1].mean()), 1)}


def worst_fill(m1: Bars, bars: Bars, step: int, evs: np.ndarray, tr: list[dict]) -> tuple[list[dict], list[float]]:
    """Stops touchés dans une bougie qui contient une minute d'annonce : remplis au pire prix de cette minute."""
    pos = {int(t): n for n, t in enumerate(m1.ts)}
    slips, out = [], []
    for t in tr:
        t = dict(t)
        if t["why"] == "stop":
            t0 = int(bars.ts[t["exit_i"]])
            k = np.searchsorted(evs, t0)
            if k < len(evs) and evs[k] < t0 + step and (n := pos.get(int(evs[k]))) is not None:
                worst = float(m1.l[n]) if t["sign"] > 0 else float(m1.h[n])
                if t["sign"] * (worst - t["stop"]) < 0:
                    slips.append(abs(worst - t["stop"]))
                    risk = t["stop_pct"] * t["entry"]
                    t["exit"] = worst
                    t["r"] = gold_r(t["sign"] * (worst - t["entry"]), t["entry"], risk)
                    t["r2"] = gold_r(t["sign"] * (worst - t["entry"]), t["entry"], risk, 2 * GOLD_FEE)
        out.append(t)
    return out, slips


# ---------------------------------------------------------------- essai 36 : profil de volume

NBINS = 40


def profiles(b: Bars) -> dict[int, dict]:
    days = b.ts // 86400
    out = {}
    for d in np.unique(days):
        a, z = np.searchsorted(days, d), np.searchsorted(days, d + 1)
        if z - a < 250:
            continue
        lo, hi = float(b.l[a:z].min()), float(b.h[a:z].max())
        if hi <= lo:
            continue
        w = (hi - lo) / NBINS
        idx = np.clip(((b.c[a:z] - lo) / w).astype(int), 0, NBINS - 1)
        vol = np.bincount(idx, weights=b.v[a:z], minlength=NBINS)
        mean = vol.mean()
        lab = np.where(vol >= 1.5 * mean, 1, np.where(vol <= 0.5 * mean, -1, 0))
        poc = int(vol.argmax())
        lo_b, hi_b, tot = poc, poc, vol[poc]
        while tot < 0.7 * vol.sum():
            up = vol[hi_b + 1] if hi_b + 1 < NBINS else -1
            dn = vol[lo_b - 1] if lo_b > 0 else -1
            if up >= dn:
                hi_b += 1; tot += up
            else:
                lo_b -= 1; tot += dn
        out[int(d)] = {"lo": lo, "w": w, "lab": lab, "va": (lo_b, hi_b)}
    return out


def traversal(b: Bars, prof: dict[int, dict], lab_of: Callable[[int], np.ndarray]) -> float:
    """Temps moyen (bougies) passé par tranche traversée, zones creuses ÷ zones pleines, tous jours réunis."""
    days = b.ts // 86400
    th = nh = tf = nf = 0
    for d in prof:
        if d + 1 not in prof:
            continue
        a, z = np.searchsorted(days, d + 1), np.searchsorted(days, d + 2)
        p = prof[d]
        j = ((b.c[a:z] - p["lo"]) / p["w"]).astype(int)
        j = j[(j >= 0) & (j < NBINS)]
        if not len(j):
            continue
        lab = lab_of(d)
        lj = lab[j]
        th += (lj == -1).sum(); nh += len(np.unique(j[lj == -1]))
        tf += (lj == 1).sum(); nf += len(np.unique(j[lj == 1]))
    return (th / nh) / (tf / nf)


def lvn_trades(b: Bars, prof: dict[int, dict], value_only: bool, max_bars: int = 48) -> list[dict]:
    days = b.ts // 86400
    out, busy = [], -1
    for n in range(1, len(b.ts) - 1):
        if n <= busy:
            continue
        p = prof.get(int(days[n]) - 1)
        if p is None or days[n - 1] != days[n]:
            continue
        j = int((b.c[n] - p["lo"]) // p["w"]); j0 = int((b.c[n - 1] - p["lo"]) // p["w"])
        if not (0 <= j < NBINS and 0 <= j0 < NBINS) or abs(j - j0) != 1:
            continue
        lab = p["lab"]
        if lab[j] != -1 or lab[j0] == -1:
            continue
        if value_only and not (p["va"][0] <= j <= p["va"][1]):
            continue
        sg = 1 if j > j0 else -1
        k = j
        while 0 <= k + sg < NBINS and lab[k + sg] == -1:
            k += sg
        edge_in = p["lo"] + p["w"] * (j if sg > 0 else j + 1)
        target = p["lo"] + p["w"] * (k + 1 if sg > 0 else k)
        dist = abs(target - edge_in)
        stop = edge_in - sg * dist
        e = float(b.o[n + 1])
        risk = sg * (e - stop)
        if risk <= 0 or sg * (target - e) <= 0:
            continue
        i, px, why = bracket(b, n + 1, e, sg, stop, target, max_bars)
        out.append({"i": n + 1, "sign": sg, "entry": e, "stop": stop, "exit_i": i, "exit": px, "why": why,
                    "stop_pct": risk / e, "target_pct": abs(target - e) / e, "max": max_bars,
                    "r": btc_r(sg * (px - e), e, risk), "r2": btc_r(sg * (px - e), e, risk, 2 * BTC_FEE)})
        busy = i
    return out


# ---------------------------------------------------------------- essai 37 : anciens extrêmes

def sessions(b: Bars) -> np.ndarray:
    """Numéro de séance (18:00 → 17:00 New York) de chaque bougie."""
    loc = np.array([datetime.fromtimestamp(int(t), NY) for t in b.ts])
    return np.array([(x + timedelta(hours=6)).date().toordinal() for x in loc])


def extremes(b: Bars, sess: np.ndarray) -> dict[str, Any]:
    starts = np.r_[0, np.flatnonzero(np.diff(sess)) + 1]
    ends = np.r_[starts[1:], len(sess)]
    res = {"vrai": {"15": [], "60": []}, "temoin": {"15": [], "60": []}}
    for s in range(1, len(starts)):
        a0, z0, a, z = starts[s - 1], ends[s - 1], starts[s], ends[s]
        if z0 - a0 < 150 or z - a < 150:
            continue
        ph, pl = b.h[a0:z0].max(), b.l[a0:z0].min()
        for kind, up, dn in (("vrai", ph, pl), ("temoin", ph * 0.9975, pl * 1.0025)):
            for sg, lvl in ((1, up), (-1, dn)):
                hit = np.flatnonzero(b.h[a:z] > lvl) if sg > 0 else np.flatnonzero(b.l[a:z] < lvl)
                if not len(hit):
                    continue
                i = a + int(hit[0])
                for key, n in (("15", 3), ("60", 12)):
                    if i + n < z:
                        res[kind][key].append(sg * (b.c[i + n] - lvl) > 0)
    return {k: {kk: {"cas": len(v), "au_dela": round(float(np.mean(v)) * 100, 1)} for kk, v in d.items()}
            for k, d in res.items()}


def extreme_trades(b: Bars, sess: np.ndarray, hold: int) -> list[dict]:
    starts = np.r_[0, np.flatnonzero(np.diff(sess)) + 1]
    ends = np.r_[starts[1:], len(sess)]
    out, busy = [], -1
    for s in range(1, len(starts)):
        a0, z0, a, z = starts[s - 1], ends[s - 1], starts[s], ends[s]
        if z0 - a0 < 150 or z - a < 150:
            continue
        ph, pl = b.h[a0:z0].max(), b.l[a0:z0].min()
        cand = []
        for sg, lvl in ((1, ph), (-1, pl)):
            hit = np.flatnonzero(b.c[a:z] > lvl) if sg > 0 else np.flatnonzero(b.c[a:z] < lvl)
            if len(hit):
                cand.append((a + int(hit[0]), sg))
        for i, sg in sorted(cand):
            k = i + 1
            if k <= busy or k + hold >= z:
                continue
            e = float(b.o[k]); stop = e * (1 - sg * 0.005)
            j, px, why = bracket(b, k, e, sg, stop, None, hold)
            risk = e * 0.005
            out.append({"i": k, "sign": sg, "entry": e, "stop": stop, "exit_i": j, "exit": px, "why": why,
                        "stop_pct": 0.005, "target_pct": 0.0, "max": hold,
                        "r": gold_r(sg * (px - e), e, risk), "r2": gold_r(sg * (px - e), e, risk, 2 * GOLD_FEE)})
            busy = j
    return out


# ---------------------------------------------------------------- main

def run(log: Callable[[str], None] = print) -> dict[str, Any]:
    rng = np.random.default_rng(33)
    m1 = Bars.load("gold_1m.npz")
    tf = {"1 h": (m1.resample(3600), 3600), "5 min": (m1.resample(300), 300)}
    res: dict[str, Any] = {"donnees": {
        "or": f"{datetime.fromtimestamp(int(m1.ts[0]), UTC):%Y-%m-%d} → {datetime.fromtimestamp(int(m1.ts[-1]), UTC):%Y-%m-%d}"}}
    evs = np.array(event_times())

    # Essai 35
    z35 = z_threshold(8)
    res["essai35"] = {}
    base_tr: dict[str, dict[str, list[dict]]] = {}
    for tn, (b, step) in tf.items():
        sig = {w: structure_signals(b, w) for w in (False, True)}
        base_tr[tn] = {}
        for name, (wick, keep) in S_CELLS.items():
            tr = structure_trades(b, sig[wick], keep, wick)
            tr, _ = worst_fill(m1, b, step, evs, tr)
            base_tr[tn][name] = tr
            v = checks(b, tr, gold_r, rng, z35)
            res["essai35"][f"{name} ({tn})"] = v
            log(f"35 {name} ({tn}) : {v['trades']} trades, R {v.get('R')}, PF {v.get('PF')}, {v.get('annees_pos')} → {v['verdict']}")

    # Essai 34
    z34 = z_threshold(6)
    per, glob = hour_ranges(tf["1 h"][0])
    res["essai34"] = {}
    for tn, (b, _) in tf.items():
        base = base_tr[tn]["S2 creux fort, clôture"]
        for k in (1, 2, 3):
            var = hour_stop_trades(b, base, per, glob, k, True)
            wit = hour_stop_trades(b, base, per, glob, k, False)
            pairs = [(w, v) for w, v in zip(wit, var) if w is not None and v is not None]
            p = paired(b, [w for w, _ in pairs], [v for _, v in pairs], z34)
            res["essai34"][f"stop {k} × heure ({tn})"] = p
            log(f"34 k={k} ({tn}) : témoin {p['temoin_R']} → variante {p['variante_R']}, écart {p['ecart']}, z {p['z']} → {p['verdict']}")

    # Essai 33
    res["essai33"] = {"33a": news_amplitude(m1, list(evs))}
    slips = []
    for tn, (b, step) in tf.items():
        for name in S_CELLS:
            _, s = worst_fill(m1, b, step, evs, [t for t in base_tr[tn][name]])
            slips += s
    res["essai33"]["33a"]["stops_dans_minute_annonce"] = len(slips)
    res["essai33"]["33a"]["glissement_moyen_$"] = round(float(np.mean(slips)), 2) if slips else None
    res["essai33"]["33a"]["glissement_max_$"] = round(float(np.max(slips)), 2) if slips else None
    log(f"33a : {res['essai33']['33a']}")
    z33 = z_threshold(8)
    res["essai33"]["33b"] = {}
    for tn, (b, step) in tf.items():
        def block(t: int) -> bool:
            k = np.searchsorted(evs, t - 15 * 60)
            return bool(k < len(evs) and evs[k] - 30 * 60 <= t)

        def cut_fn(k: int, mb: int) -> int | None:
            t0, t1 = int(b.ts[k]), int(b.ts[min(len(b.ts) - 1, k + mb)])
            e = np.searchsorted(evs, t0 + 30 * 60)
            if e < len(evs) and evs[e] - 30 * 60 <= t1:
                c = int(np.searchsorted(b.ts, evs[e] - 30 * 60))
                return c if c > k else None
            return None
        sig = {w: structure_signals(b, w) for w in (False, True)}
        for name, (wick, keep) in S_CELLS.items():
            orig = base_tr[tn][name]
            var, _ = worst_fill(m1, b, step, evs, structure_trades(b, sig[wick], keep, wick, block=block, cut_fn=cut_fn))
            # appariement par bougie d'entrée ; une entrée bloquée compte 0 R dans la variante
            vmap = {t["i"]: t for t in var}
            pv = [vmap.get(t["i"], {"r": 0.0}) for t in orig]
            p = paired(b, orig, pv, z33)
            p["entrees_sautees"] = sum(t["i"] not in vmap for t in orig)
            res["essai33"]["33b"][f"{name} ({tn})"] = p
            log(f"33b {name} ({tn}) : {p['temoin_R']} → {p['variante_R']}, écart {p['ecart']}, z {p['z']} → {p['verdict']}")

    # Essai 37
    b5 = tf["5 min"][0]
    sess = sessions(b5)
    res["essai37"] = {"37a": extremes(b5, sess)}
    log(f"37a : {res['essai37']['37a']}")
    z37 = z_threshold(2)
    for name, hold in (("37b sortie 15 min", 3), ("37c sortie 1 h", 12)):
        v = checks(b5, extreme_trades(b5, sess, hold), gold_r, rng, z37)
        res["essai37"][name] = v
        log(f"{name} : {v['trades']} trades, R {v.get('R')}, PF {v.get('PF')} → {v['verdict']}")

    # Essai 36
    bt = Bars.load("btc_5m.npz")
    prof = profiles(bt)
    keys = sorted(prof)
    real = traversal(bt, prof, lambda d: prof[d]["lab"])
    draws = [traversal(bt, prof, lambda d, r=np.random.default_rng(s): prof[keys[r.integers(len(keys))]]["lab"])
             for s in range(200)]
    beat = int(sum(real < x for x in draws))
    res["essai36"] = {"36a": {"rapport_reel": round(float(real), 2), "rapport_hasard_moyen": round(float(np.mean(draws)), 2),
                              "tirages_battus": beat, "confirme": beat >= 190}}
    log(f"36a : {res['essai36']['36a']}")
    z36 = z_threshold(2)
    for name, vo in (("36b zone creuse", False), ("36c zone creuse dans la zone de valeur", True)):
        v = checks(bt, lvn_trades(bt, prof, vo), btc_r, rng, z36)
        res["essai36"][name] = v
        log(f"{name} : {v['trades']} trades, R {v.get('R')}, PF {v.get('PF')} → {v['verdict']}")
    return res


def main() -> None:
    res = run()
    (Path(DATA_DIR) / "essai33.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
