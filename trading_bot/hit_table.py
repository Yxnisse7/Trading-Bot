"""Le passé d'un trade de l'agent IA : objectif ou stop touché d'abord ? (demandé par Yanisse le 23/10/2026).

Idée vue dans le « Time Machine » d'un skill Claude de day trading (vidéo TikTok @dan.ai.lab), refaite sur nos 12 ans de
bougies 5 min plutôt que sur 60 jours. Pour l'or et le Nasdaq, on prend chaque demi-heure de 2014 à 2026, on entre au
prix de clôture, à l'achat et à la vente, avec un stop de 0,5 à 6 fois l'amplitude moyenne des 14 dernières bougies
(« ATR ») et un objectif de 1 à 3 fois le stop, et on regarde sur 4 h (durée max d'un trade de l'agent) ce qui est
touché d'abord. Stop et objectif dans la même bougie : compté comme stop (prudent). Fenêtre coupée par un trou
(week-end, panne) : écartée.

Le tableau est calculé une fois (data/hit_table.json, versionné) ; le pont n'a qu'à le lire : aucun retard sur l'ordre,
aucun appel Claude. C'est une information (message Telegram, journal), pas un filtre.

    python -m trading_bot.hit_table          → data/hit_table.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
MARKETS = ("gold", "nasdaq")
STOPS = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0)        # stop en ATR
RRS = (1.0, 1.5, 2.0, 2.5, 3.0)                   # objectif en multiples du stop
HORIZON = 48                                       # bougies 5 min = 4 h
ATR_N = 14
FILE = Path(__file__).resolve().parent.parent / "data" / "hit_table.json"


def atr(highs, lows, n: int = ATR_N) -> float:
    """Amplitude moyenne (haut − bas) des n dernières bougies."""
    h, lo = list(highs)[-n:], list(lows)[-n:]
    return sum(a - b for a, b in zip(h, lo)) / len(h) if h else 0.0


def slot(ts: float) -> str:
    """Demi-heure de Paris : « 15:30 »."""
    d = datetime.fromtimestamp(ts, PARIS)
    return f"{d.hour:02d}:{30 if d.minute >= 30 else 0:02d}"


def build(candles, log=print) -> dict[str, Any]:
    import numpy as np
    ts = np.array([c.ts for c in candles], dtype=np.int64)
    hi = np.array([c.high for c in candles])
    lo = np.array([c.low for c in candles])
    cl = np.array([c.close for c in candles])
    rng = hi - lo
    csum = np.concatenate([[0.0], np.cumsum(rng)])
    starts = np.array([i for i in range(ATR_N, len(ts) - HORIZON - 1)
                       if (ts[i] + 300) % 1800 == 0], dtype=np.int64)      # bougie qui finit sur une demi-heure
    win = starts[:, None] + 1 + np.arange(HORIZON)[None, :]
    ok = (ts[win[:, -1]] - ts[starts]) <= (HORIZON + 12) * 300            # pas de trou de plus d'une heure
    starts, win = starts[ok], win[ok]
    a = (csum[starts + 1] - csum[starts + 1 - ATR_N]) / ATR_N
    good = a > 0
    starts, win, a = starts[good], win[good], a[good]
    entry = cl[starts]
    run_hi = np.maximum.accumulate(hi[win], axis=1)
    run_lo = np.minimum.accumulate(lo[win], axis=1)
    slots = np.array([slot(t + 300) for t in ts[starts]])
    log(f"{len(starts)} départs")

    def first(mask):
        hit = mask.any(axis=1)
        return np.where(hit, mask.argmax(axis=1), HORIZON)

    out: dict[str, Any] = {}
    for k in STOPS:
        d = a * k
        for side, s in (("achat", 1), ("vente", -1)):
            stop_t = first(run_lo <= (entry - d)[:, None]) if s > 0 else first(run_hi >= (entry + d)[:, None])
            for r in RRS:
                tgt = entry + s * d * r
                tgt_t = first(run_hi >= tgt[:, None]) if s > 0 else first(run_lo <= tgt[:, None])
                win_tp = tgt_t < stop_t
                win_sl = (stop_t <= tgt_t) & (stop_t < HORIZON)
                for sl_name in np.unique(slots):
                    m = slots == sl_name
                    n = int(m.sum())
                    cell = out.setdefault(sl_name, {}).setdefault(side, {}).setdefault(str(k), {})
                    cell[str(r)] = [round(float(win_tp[m].mean()), 3), round(float(win_sl[m].mean()), 3), n]
    return out


def nearest(values, x: float) -> float:
    return min(values, key=lambda v: abs(v - x))


def lookup(table: dict[str, Any], market: str, ts: float, buy: bool, entry: float, stop: float, target: float,
           atr_now: float) -> dict[str, Any] | None:
    """Ligne du tableau la plus proche du trade : {"tp": 0.31, "sl": 0.62, "n": 2950, "seuil": 0.33, ...} ou None."""
    risk = abs(entry - stop)
    if atr_now <= 0 or risk <= 0:
        return None
    k, r = nearest(STOPS, risk / atr_now), nearest(RRS, abs(target - entry) / risk)
    try:
        tp, sl, n = table[market][slot(ts)]["achat" if buy else "vente"][str(k)][str(r)]
    except KeyError:
        return None
    return {"tp": tp, "sl": sl, "n": n, "seuil": round(1 / (1 + r), 3), "stop_atr": k, "rr": r}


def text(h: dict[str, Any] | None) -> str:
    """Ligne pour Telegram."""
    if not h:
        return ""
    pct = lambda v: f"{v * 100:.0f} %"  # noqa: E731
    verdict = "au-dessus" if h["tp"] / max(h["tp"] + h["sl"], 1e-9) > h["seuil"] + 0.02 else \
        "en dessous" if h["tp"] / max(h["tp"] + h["sl"], 1e-9) < h["seuil"] - 0.02 else "au niveau"
    return (f"Passé 2014-2026 (même heure, stop et objectif de même taille) : TP d'abord {pct(h['tp'])}, "
            f"SL d'abord {pct(h['sl'])}, rien en 4 h {pct(max(0.0, 1 - h['tp'] - h['sl']))}. "
            f"Il faut {pct(h['seuil'])} de TP parmi les trades finis : {verdict} du seuil.")


def load_table(path: Path = FILE) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .essai23 import load
    eng = Engine(load_config())
    root = eng.store.dir
    out: dict[str, Any] = {"updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                           "horizon_h": HORIZON * 5 / 60, "atr_bars": ATR_N}
    for key in MARKETS:
        old = load(root / "history" / "long" / f"{key}_5m.json")
        new = eng.store.load_history(key) or []
        candles = [c for c in old if not new or c.ts < new[0].ts] + new
        print(f"{key} : {len(candles)} bougies", flush=True)
        out[key] = build(candles, log=lambda s: print(s, flush=True))
    FILE.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"écrit {FILE} ({FILE.stat().st_size // 1024} ko)")


if __name__ == "__main__":
    main()
