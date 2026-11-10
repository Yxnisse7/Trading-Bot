"""Essai 75 (HYPOTHESES.md) : les objections habituelles de l'agent IA font-elles vraiment perdre ? (10/11/2026)

Pour chaque trade de nos stratégies en réel (2014 → 10/2026) et du bot classique Nasdaq (essai 74, 2014-2024), on
regarde la dernière bougie 5 min clôturée avant l'entrée et on note les 6 objections de l'agent :
  O1 RSI 14 étiré (≥ 70 achat, ≤ 30 vente)        O4 sommet/creux des 24 h devant, à moins de 1 R
  O2 > 2 ATR de la moyenne 20, dans le sens       O5 chiffre rond devant, à moins de 0,5 R
  O3 > 3 ATR parcourus en 30 min, dans le sens    O6 contre la tendance 15 min (moyenne 20)
Puis on compare les trades signalés aux autres (critères pré-enregistrés).

    python -m trading_bot.essai75          → data/essai75.json
"""
from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np

from . import strategies as sl
from .config import DATA_DIR, load_config
from .essai21 import bot_cost
from .essai33 import LONG, Bars
from .models import Candle

HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
OBJ = {"O1": "RSI étiré", "O2": "loin de la moyenne 20", "O3": "accélération en 30 min",
       "O4": "sommet/creux 24 h devant (< 1 R)", "O5": "chiffre rond devant (< 0,5 R)", "O6": "contre la tendance 15 min"}
ROUND = {"nasdaq": 100.0, "gold": 10.0, "bitcoin": 1000.0}
STRATS = {"nasdaq": ("noise_area_v2", "double7"), "gold": ("nuit_asie", "crabel_nr4"),
          "bitcoin": ("donchian_1h", "swing_w3", "cassure_williams")}
N_PERM = 1000


def bars(asset: str) -> Bars:
    if asset == "bitcoin":
        return Bars.load("btc_5m.npz")
    from .essai72 import load_gold
    b = load_gold() if asset == "gold" else Bars.load("nasdaq_1m.npz")
    return b.resample(300)


def candles(b: Bars) -> list[Candle]:
    return [Candle(int(t), float(o), float(h), float(lo), float(c), 0.0)
            for t, o, h, lo, c in zip(b.ts, b.o, b.h, b.l, b.c)]


def sma(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    cs = np.cumsum(np.insert(x, 0, 0.0))
    out[n - 1:] = (cs[n:] - cs[:-n]) / n
    return out


def wilder(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) <= n:
        return out
    out[n] = x[1:n + 1].mean()
    a = 1.0 / n
    for i in range(n + 1, len(x)):
        out[i] = out[i - 1] + a * (x[i] - out[i - 1])
    return out


class Ind:
    """Indicateurs 5 min et 15 min, calculés une fois par marché."""

    def __init__(self, b: Bars):
        self.ts, self.h, self.l, self.c = b.ts, b.h, b.l, b.c
        d = np.diff(b.c, prepend=b.c[0])
        ag, al = wilder(np.maximum(d, 0), 14), wilder(np.maximum(-d, 0), 14)
        with np.errstate(divide="ignore", invalid="ignore"):
            self.rsi = np.where(al == 0, 100.0, 100 - 100 / (1 + ag / al))
        pc = np.roll(b.c, 1)
        pc[0] = b.c[0]
        tr = np.maximum(b.h - b.l, np.maximum(abs(b.h - pc), abs(b.l - pc)))
        self.atr = wilder(tr, 14)
        self.ma20 = sma(b.c, 20)
        # 15 min : bougie = ts // 900 ; clôture = dernière bougie 5 min du quart d'heure
        q = b.ts // 900
        last = np.flatnonzero(np.diff(q, append=q[-1] + 1) != 0)
        self.q_end = (q[last] + 1) * 900                      # heure de fin de chaque bougie 15 min
        self.q_c = b.c[last]
        self.q_ma = sma(self.q_c, 20)

    def at(self, entry_ts: int) -> int:
        """Dernière bougie 5 min clôturée au moment de l'entrée."""
        return int(np.searchsorted(self.ts, entry_ts - 300, side="right")) - 1

    def flags(self, asset: str, entry_ts: int, long: bool, entry: float, risk: float) -> dict[str, bool] | None:
        i = self.at(entry_ts)
        if i < 300 or np.isnan(self.atr[i]) or np.isnan(self.ma20[i]) or risk <= 0:
            return None
        sg = 1 if long else -1
        a = self.atr[i]
        o1 = self.rsi[i] >= 70 if long else self.rsi[i] <= 30
        o2 = sg * (self.c[i] - self.ma20[i]) > 2 * a
        o3 = sg * (self.c[i] - self.c[i - 6]) > 3 * a
        lo = int(np.searchsorted(self.ts, self.ts[i] - 86400, side="left"))
        ext = self.h[lo:i + 1].max() if long else self.l[lo:i + 1].min()
        o4 = 0 < sg * (ext - entry) <= risk
        step = ROUND[asset]
        nxt = (np.floor(entry / step) + 1) * step if long else (np.ceil(entry / step) - 1) * step
        o5 = abs(nxt - entry) <= 0.5 * risk
        k = int(np.searchsorted(self.q_end, entry_ts, side="right")) - 1
        if k < 20 or np.isnan(self.q_ma[k]):
            return None
        o6 = (self.q_c[k] < self.q_ma[k]) if long else (self.q_c[k] > self.q_ma[k])
        return {"O1": bool(o1), "O2": bool(o2), "O3": bool(o3), "O4": bool(o4), "O5": bool(o5), "O6": bool(o6)}


def collect() -> list[dict]:
    cfg = load_config()
    rows: list[dict] = []
    for asset, names in STRATS.items():
        b = bars(asset)
        ind = Ind(b)
        cost = bot_cost(asset, cfg)[0]
        trades = sl.run_all(asset, candles(b), only=list(names))
        for t in trades:
            if t.reason == "fin des données" or t.risk <= 0:
                continue
            f = ind.flags(asset, t.entry_ts, t.direction == "long", t.entry, t.risk)
            if f is None:
                continue
            g, c = t.gross_points(), cost(t.entry)
            rows.append({"strat": t.strategy, "asset": asset, "ts": t.entry_ts, "r": (g - c) / t.risk,
                         "r2": (g - 2 * c) / t.risk, **f})
        if asset == "nasdaq":
            ref = pickle.load((LONG / "essai74_res_nasdaq.pkl").open("rb"))["REF"]
            for x in ref:
                row = x["row"]
                risk = abs(row["entry"] - row["stop_loss"])
                f = ind.flags(asset, int(x["ts"]), row["direction"] == "long", row["entry"], risk)
                if f is None:
                    continue
                rows.append({"strat": "bot", "asset": asset, "ts": int(x["ts"]), "r": x["r"], "r2": x["r2"], **f})
        print(asset, "ok", len(rows), flush=True)
    return rows


def _m(x: np.ndarray) -> float | None:
    return float(x.mean()) if len(x) else None


def judge(rows: list[dict], z_need: float) -> dict:
    r = np.array([x["r"] for x in rows])
    r2 = np.array([x["r2"] for x in rows])
    ts = np.array([x["ts"] for x in rows])
    st = np.array([x["strat"] for x in rows])
    groups = {s: np.flatnonzero(st == s) for s in sorted(set(st))}
    rng = np.random.default_rng(75)
    out = {}
    for o, label in OBJ.items():
        f = np.array([x[o] for x in rows])
        nf, nu = int(f.sum()), int((~f).sum())
        mf, mu = _m(r[f]), _m(r[~f])
        h1, h2 = ts < HALF, ts >= HALF
        halves = [(_m(r[f & h]), _m(r[~f & h])) for h in (h1, h2)]
        z = None
        if nf > 1 and nu > 1:
            z = (mu - mf) / np.sqrt(r[f].var(ddof=1) / nf + r[~f].var(ddof=1) / nu)
        lower = 0
        for _ in range(N_PERM):
            sf = np.zeros(len(r), bool)
            for idx in groups.values():
                k = int(f[idx].sum())
                if k:
                    sf[rng.choice(idx, k, replace=False)] = True
            lower += int(r[sf].mean() > mf) if nf else 0
        checks = {"≥ 200 signalés": nf >= 200,
                  "signalés < 0 et < autres": mf is not None and mf < 0 and mf < (mu or 0),
                  "deux moitiés": all(a is not None and b is not None and a < b for a, b in halves),
                  "frais × 2 < 0": nf > 0 and float(r2[f].mean()) < 0,
                  "hasard (950/1000)": lower >= 950,
                  "z corrigé": z is not None and z >= z_need}
        checks = {k: bool(v) for k, v in checks.items()}
        status = ("validée" if all(checks.values())
                  else "à oublier" if mf is not None and mu is not None and mf >= mu else "pas prouvée")
        per = {}
        for s, idx in groups.items():
            fs = f[idx]
            per[s] = {"n": len(idx), "signalés": int(fs.sum()), "R signalés": _rd(_m(r[idx][fs])),
                      "R autres": _rd(_m(r[idx][~fs])), "total sans eux": round(float(r[idx][~fs].sum()), 1),
                      "total": round(float(r[idx].sum()), 1)}
        out[o] = {"objection": label, "n_signalés": nf, "n_autres": nu, "R_signalés": _rd(mf), "R_autres": _rd(mu),
                  "moitiés": [[_rd(a), _rd(b)] for a, b in halves], "R_signalés_frais_x2": _rd(_m(r2[f])),
                  "hasard_battu": lower, "z": _rd(z), "checks": checks, "statut": status, "par_stratégie": per}
    return out


def _rd(x):
    return None if x is None else round(float(x), 3)


def main() -> None:
    cache = LONG / "essai75_rows.pkl"
    if cache.exists():
        rows = pickle.load(cache.open("rb"))
    else:
        rows = collect()
        pickle.dump(rows, cache.open("wb"))
    z_need = NormalDist().inv_cdf(1 - 0.05 / len(OBJ))
    res = judge(rows, z_need)
    st = {s: sum(1 for x in rows if x["strat"] == s) for s in sorted({x["strat"] for x in rows})}
    out = {"essai": 75, "n_trades": len(rows), "par_stratégie": st, "z_seuil": round(z_need, 2),
           "R_moyen_global": round(float(np.mean([x["r"] for x in rows])), 3), "objections": res}
    (Path(DATA_DIR) / "essai75.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "objections"}, ensure_ascii=False))
    for o, v in res.items():
        print(o, v["objection"], v["statut"], "n", v["n_signalés"], "R sig", v["R_signalés"], "R autres", v["R_autres"],
              "moitiés", v["moitiés"], "hasard", v["hasard_battu"], "z", v["z"])


if __name__ == "__main__":
    main()
