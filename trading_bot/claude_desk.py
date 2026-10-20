"""Poste de lecture et d'ordres pour les passages manuels de l'assistant sur le compte démo MetaTrader 5.

    python -m trading_bot.claude_desk look                 # résumé compact du marché de l'or et du compte
    python -m trading_bot.claude_desk order buy|sell SL TP "raison"   # ordre risquant 1 % du solde, stop obligatoire
    python -m trading_bot.claude_desk close "raison"       # ferme les positions de l'assistant

Garde-fous : compte démo uniquement, taille calculée pour perdre 1 % du solde au stop (0,01 à 0,10 lot), un stop sur chaque ordre, une seule position à la fois, numéro
magique distinct du pont (ses trades sont comptés à part), journal dans journal/assistant.csv.
"""
from __future__ import annotations

import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import demo_rules
from . import indicators as ind
from .models import Candle

ROOT = Path(__file__).resolve().parents[2]          # E:\TradingBot (le code est dans E:\TradingBot\bot)
SYMBOL = "XAUUSD+"
MAGIC = 777001
RISK_PCT = 0.01                                     # perte au stop = 1 % du solde
MIN_LOT, MAX_LOT = 0.01, 0.10
CALENDAR = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"


def _offset(mt5) -> int:
    tick = mt5.symbol_info_tick(SYMBOL)
    return round((tick.time - time.time()) / 1800) * 1800


def _bars(mt5, tf, n: int, off: int) -> list[Candle]:
    r = mt5.copy_rates_from_pos(SYMBOL, tf, 0, n + 1)
    return [Candle(int(x["time"]) - off, float(x["open"]), float(x["high"]), float(x["low"]), float(x["close"]),
                   float(x["tick_volume"])) for x in (r if r is not None else [])]


def _frame(name: str, c: list[Candle], show: int) -> str:
    closes = [x.close for x in c]
    ma20, ma50, rsi, atr = ind.sma(closes, 20), ind.sma(closes, 50), ind.rsi(closes, 21), ind.atr(c, 14)
    head = (f"{name}: MM20 {ma20[-2]:.2f} (il y a 3 : {ma20[-5]:.2f}) MM50 {ma50[-2]:.2f} RSI21 {rsi[-2]:.1f} "
            f"ATR14 {atr[-2]:.2f}" if ma50[-2] and rsi[-2] and atr[-2] else f"{name}: pas assez de bougies")
    rows = [f"  {datetime.fromtimestamp(x.ts, timezone.utc):%H:%M} o{x.open:.2f} h{x.high:.2f} l{x.low:.2f} "
            f"c{x.close:.2f} v{x.volume:.0f}" for x in c[-show:]]
    return "\n".join([head, *rows])


def look(mt5) -> str:
    off = _offset(mt5)
    tick = mt5.symbol_info_tick(SYMBOL)
    acc = mt5.account_info()
    now = datetime.now(timezone.utc)
    pos = [p for p in (mt5.positions_get(symbol=SYMBOL) or [])]
    lines = [f"{now:%Y-%m-%d %H:%M} UTC  {SYMBOL} bid {tick.bid:.2f} ask {tick.ask:.2f} écart {tick.ask - tick.bid:.2f}",
             f"compte {'DÉMO' if acc.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO else 'RÉEL'} solde {acc.balance:.2f} "
             f"capitaux {acc.equity:.2f}",
             "positions : " + ("; ".join(f"{'achat' if p.type == 0 else 'vente'} {p.volume} @ {p.price_open:.2f} "
                                         f"SL {p.sl:.2f} TP {p.tp:.2f} P&L {p.profit:.2f} magic {p.magic}" for p in pos)
                               or "aucune")]
    day = _bars(mt5, mt5.TIMEFRAME_D1, 5, off)
    if len(day) > 1:
        lines.append(f"veille : h{day[-2].high:.2f} l{day[-2].low:.2f} c{day[-2].close:.2f} ; jour : o{day[-1].open:.2f} "
                     f"h{day[-1].high:.2f} l{day[-1].low:.2f}")
    lines.append(_frame("H1", _bars(mt5, mt5.TIMEFRAME_H1, 80, off)[:-1], 12))
    lines.append(_frame("M15", _bars(mt5, mt5.TIMEFRAME_M15, 80, off)[:-1], 12))
    lines.append(_frame("M5", _bars(mt5, mt5.TIMEFRAME_M5, 80, off)[:-1], 18))
    return "\n".join(lines)


def news(hours: float = 36.0) -> str:
    """Annonces USD fortes et moyennes à venir (calendrier gratuit de la semaine, sans clé)."""
    import requests
    from zoneinfo import ZoneInfo
    try:
        rows = requests.get(CALENDAR, timeout=15, headers={"User-Agent": "Mozilla/5.0"}).json()
    except (requests.RequestException, ValueError) as exc:
        return f"annonces : calendrier injoignable ({exc.__class__.__name__})"
    now = datetime.now(timezone.utc)
    out = []
    for e in rows:
        if e.get("country") != "USD" or e.get("impact") not in ("High", "Medium"):
            continue
        at = datetime.fromisoformat(e["date"]).astimezone(timezone.utc)
        if -3600 <= (at - now).total_seconds() <= hours * 3600:
            out.append(f"  {at.astimezone(ZoneInfo('Europe/Paris')):%a %H:%M} Paris  {e['impact']:6s} {e['title']}")
    return "annonces USD (-1 h a +36 h) :\n" + ("\n".join(out) or "  aucune")


def _journal(row: dict) -> None:
    f = ROOT / "journal" / "assistant.csv"
    f.parent.mkdir(parents=True, exist_ok=True)
    new = not f.exists()
    with f.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["heure_utc", "action", "prix", "stop", "objectif", "resultat", "raison"])
        if new:
            w.writeheader()
        w.writerow({"heure_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), **row})


def _filling(mt5) -> int:
    mode = mt5.symbol_info(SYMBOL).filling_mode
    return mt5.ORDER_FILLING_FOK if mode & 1 else mt5.ORDER_FILLING_IOC if mode & 2 else mt5.ORDER_FILLING_RETURN


def lot_for(balance: float, dist: float, contract: float = 100.0) -> float:
    """Lot qui perd RISK_PCT du solde si le stop (à dist $ du prix) est touché, arrondi vers le bas à 0,01."""
    if dist <= 0:
        return MIN_LOT
    lot = int(balance * RISK_PCT / (dist * contract) * 100) / 100
    return max(MIN_LOT, min(MAX_LOT, lot))


def order(mt5, side: str, sl: float, tp: float, why: str) -> str:
    acc = mt5.account_info()
    if acc is None or acc.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
        return "REFUSÉ : ce n'est pas un compte démo"
    if [p for p in (mt5.positions_get(symbol=SYMBOL) or []) if p.magic == MAGIC]:
        return "REFUSÉ : l'assistant a déjà une position ouverte"
    stop_rule = demo_rules.check(mt5, MAGIC)
    if stop_rule:
        return f"REFUSÉ : règle d'arrêt du démo franchie ({stop_rule}), voir HYPOTHESES.md"
    tick = mt5.symbol_info_tick(SYMBOL)
    buy = side == "buy"
    px = tick.ask if buy else tick.bid
    if (buy and not sl < px < tp) or (not buy and not tp < px < sl):
        return f"REFUSÉ : stop {sl} et objectif {tp} incohérents avec le prix {px}"
    lot = lot_for(acc.balance, abs(px - sl), mt5.symbol_info(SYMBOL).trade_contract_size)
    res = mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": lot,
                          "type": mt5.ORDER_TYPE_BUY if buy else mt5.ORDER_TYPE_SELL, "price": px, "sl": sl, "tp": tp,
                          "deviation": 30, "magic": MAGIC, "comment": "assistant", "type_time": mt5.ORDER_TIME_GTC,
                          "type_filling": _filling(mt5)})
    ok = getattr(res, "retcode", None) == mt5.TRADE_RETCODE_DONE
    _journal({"action": ("achat" if buy else "vente") if ok else "rejeté", "prix": getattr(res, "price", px),
              "stop": sl, "objectif": tp, "resultat": "", "raison": why})
    return f"{'OK' if ok else 'REJETÉ'} code {getattr(res, 'retcode', None)} prix {getattr(res, 'price', px)} lot {lot}"


def close(mt5, why: str) -> str:
    out = []
    for p in [p for p in (mt5.positions_get(symbol=SYMBOL) or []) if p.magic == MAGIC]:
        tick = mt5.symbol_info_tick(SYMBOL)
        long = p.type == mt5.POSITION_TYPE_BUY
        res = mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": p.volume,
                              "position": p.ticket, "type": mt5.ORDER_TYPE_SELL if long else mt5.ORDER_TYPE_BUY,
                              "price": tick.bid if long else tick.ask, "deviation": 30, "magic": MAGIC,
                              "comment": "assistant", "type_time": mt5.ORDER_TIME_GTC, "type_filling": _filling(mt5)})
        _journal({"action": "sortie", "prix": tick.bid if long else tick.ask, "stop": "", "objectif": "",
                  "resultat": round(p.profit, 2), "raison": why})
        out.append(f"fermé {p.ticket} code {getattr(res, 'retcode', None)} P&L {p.profit:.2f}")
    return "; ".join(out) or "aucune position de l'assistant"


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import MetaTrader5 as mt5
    if not mt5.initialize():
        print("MetaTrader 5 injoignable", mt5.last_error())
        return 1
    mt5.symbol_select(SYMBOL, True)
    cmd = argv[1] if len(argv) > 1 else "look"
    if cmd == "look":
        print(look(mt5))
        print(news())
    elif cmd == "order":
        print(order(mt5, argv[2], float(argv[3]), float(argv[4]), argv[5] if len(argv) > 5 else ""))
    elif cmd == "close":
        print(close(mt5, argv[2] if len(argv) > 2 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
