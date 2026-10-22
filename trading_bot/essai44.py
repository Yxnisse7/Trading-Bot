"""Essai 44 (HYPOTHESES.md) : le bot Nasdaq sur les prix MT5 (CFD Vantage) contre les prix futures qu'il a appris.

Point 3 de la relecture Perplexity : le modèle de l'essai 26 a appris sur les futures, le PC trade le CFD NAS100.
Sur la période commune, on rejoue le bot (backtest corrigé de l'essai 42) sur les deux séries de bougies et on compare :
mêmes signaux ? même avis du filtre ? même résultat ? À lancer sur le PC (MT5 ouvert sur le démo) :

    python -m trading_bot.essai44          → data/essai44.json
"""
from __future__ import annotations

import gzip
import json
import urllib.request
from datetime import datetime, timezone
from typing import Any

HISTORY = "https://github.com/Yxnisse7/Trading-Bot/releases/download/history/nasdaq_5m.json.gz"
MATCH = 900                  # même signal : même sens, émis à moins de 15 min d'écart
N_BARS = 99000


def mt5_candles(symbol: str = "NAS100") -> list:
    import MetaTrader5 as mt5

    from .models import Candle
    from .mt5_local import server_offset
    if not mt5.initialize():
        raise SystemExit("MT5 ne s'ouvre pas")
    acc = mt5.account_info()
    if acc is None or acc.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
        raise SystemExit("MT5 n'est pas sur le compte démo")
    mt5.symbol_select(symbol, True)
    now = datetime.now(timezone.utc).timestamp()
    off = server_offset(mt5, symbol, now)
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, N_BARS)
    if rates is None or off is None:
        raise SystemExit(f"pas de bougies {symbol} : {mt5.last_error()}")
    bars = [Candle(int(r["time"]) - off, float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]),
                   float(r["tick_volume"])) for r in rates]
    return [b for b in bars if b.ts + 300 <= now]


def futures_candles(store) -> list:
    from .models import Candle
    old = store.load_history("nasdaq")
    try:
        with urllib.request.urlopen(HISTORY, timeout=60) as r:
            rows = json.loads(gzip.decompress(r.read()))
        new = [Candle(int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])) for x in rows]
    except OSError:
        new = []
    return sorted({c.ts: c for c in old + new}.values(), key=lambda c: c.ts)


def replay(cfg, candles) -> list:
    from .backtest import run_backtest
    from .models import Signal
    return [Signal.from_dict(t) for t in run_backtest(cfg.assets["nasdaq"], candles, cfg)["trades"]]


def r_of(s) -> float:
    risk = abs(s.entry - s.stop_loss)
    return (s.close_price - s.entry) * (1 if s.direction == "long" else -1) / risk if risk else 0.0


def compare(cfg, fut: list, cfd: list) -> dict[str, Any]:
    from . import bot_model
    from .models import parse_iso
    start = max(fut[0].ts, cfd[0].ts)
    end = min(fut[-1].ts, cfd[-1].ts)
    fut = [c for c in fut if start <= c.ts <= end]
    cfd = [c for c in cfd if start <= c.ts <= end]
    sf, sc = replay(cfg, fut), replay(cfg, cfd)

    def ts(s) -> int:
        return int(parse_iso(s.created_at).timestamp())

    pairs, used = [], set()
    for a in sf:
        best = None
        for j, b in enumerate(sc):
            if j not in used and b.direction == a.direction and abs(ts(b) - ts(a)) <= MATCH:
                best = j
                break
        if best is not None:
            used.add(best)
            pairs.append((a, sc[best]))
    keep_f = [not bot_model.rejects(s) for s in sf]
    keep_c = [not bot_model.rejects(s) for s in sc]
    same_filter = sum(1 for a, b in pairs if bot_model.rejects(a) == bot_model.rejects(b))
    same_result = sum(1 for a, b in pairs if (r_of(a) > 0) == (r_of(b) > 0))
    basis = [b.entry - a.entry for a, b in pairs]

    def block(sigs, keep) -> dict[str, Any]:
        rs = [r_of(s) for s in sigs]
        kept = [r for r, k in zip(rs, keep) if k]
        return {"n": len(rs), "mean_r": round(sum(rs) / len(rs), 4) if rs else None,
                "kept": len(kept), "kept_mean_r": round(sum(kept) / len(kept), 4) if kept else None}

    return {
        "period": f"{datetime.fromtimestamp(start, timezone.utc):%d/%m/%Y} → {datetime.fromtimestamp(end, timezone.utc):%d/%m/%Y}",
        "futures": block(sf, keep_f), "mt5": block(sc, keep_c),
        "matched": len(pairs), "matched_share_of_futures": round(len(pairs) / max(1, len(sf)), 3),
        "same_filter_verdict": round(same_filter / max(1, len(pairs)), 3),
        "same_win_or_loss": round(same_result / max(1, len(pairs)), 3),
        "basis_points_median": round(sorted(basis)[len(basis) // 2], 2) if basis else None,
    }


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    fut = futures_candles(eng.store)
    cfd = mt5_candles()
    print(f"futures : {len(fut)} bougies, MT5 : {len(cfd)} bougies", flush=True)
    out = {"essai": 44, **compare(eng.cfg, fut, cfd), "updated_at": iso(utcnow())}
    print(json.dumps(out, ensure_ascii=False, indent=1), flush=True)
    eng.store._write(eng.store.dir / "essai44.json", out)


if __name__ == "__main__":
    main()
