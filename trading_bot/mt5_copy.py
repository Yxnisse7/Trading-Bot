"""Copie sur le démo MetaTrader 5 des signaux envoyés sur Telegram (demandé par Yanisse le 13/10/2026).

Le pont lit, toutes les 30 s, les signaux ouverts publiés par le bot sur le site (docs/live/<actif>.json) et les
signaux réels du laboratoire (data/lab_shadow.json : creux repris sur le Nasdaq). Les prix du bot sont ceux des
contrats à terme (Yahoo), un peu différents de ceux du CFD : on garde donc les **distances** du stop et de l'objectif,
appliquées au prix du CFD au moment de la copie. Taille : 1 % du solde démo au stop. Un signal publié il y a plus de
15 min n'est plus copié. Sortie : stop et objectif chez le courtier, ou fermeture à l'expiration du signal, ou quand
le bot le ferme. Compte démo seulement, magic 200001, règles d'arrêt de demo_rules.
"""
from __future__ import annotations

import json
import logging
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import demo_rules

log = logging.getLogger("mt5_copy")

MAGIC = 200001
RISK_PCT = 0.01
MAX_AGE = 15 * 60
EVERY = 30
SYMBOLS = {"gold": "XAUUSD+", "nasdaq": "NAS100", "sp500": "SP500", "bitcoin": "BTCUSD", "ethereum": "ETHUSD",
           "oil": "CL-OIL", "euro": "EURUSD"}
SITE = "https://yxnisse7.github.io/Trading-Bot/live/{asset}.json"
LAB = "https://raw.githubusercontent.com/Yxnisse7/Trading-Bot/main/data/lab_shadow.json"
LAB_TARGET_R = {"creux_repris_15m": 3.0}


def _ts(s: str | None) -> int | None:
    if not s:
        return None
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def _get(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def read_signals(get: Callable[[str], Any] = _get) -> tuple[list[dict[str, Any]], set[str]]:
    """Signaux ouverts à copier, et les actifs (ou « lab ») lus sans erreur."""
    out, ok = [], set()
    for asset in SYMBOLS:
        try:
            d = get(SITE.format(asset=asset))
        except Exception as exc:                     # site injoignable : on ne ferme rien sur cet actif
            log.info("signaux %s illisibles (%s)", asset, exc)
            continue
        ok.add(asset)
        for s in d.get("open_signals") or []:
            if s.get("source") == "shadow" or s.get("stop_loss") is None:
                continue
            out.append({"key": f"bot:{s['id']}", "asset": asset, "direction": s["direction"], "entry": s["entry"],
                        "stop": abs(s["entry"] - s["stop_loss"]),
                        "target": abs(s["take_profit"] - s["entry"]) if s.get("take_profit") else None,
                        "created": _ts(s.get("created_at")), "expires": _ts(s.get("expires_at"))})
    try:
        lab = get(LAB)
        ok.add("lab")
        for name, rec in lab.items():
            if not rec.get("live") or rec.get("asset") not in SYMBOLS:
                continue
            for t in rec.get("trades") or []:
                if t.get("status") != "open" or not t.get("notified_entry"):
                    continue
                k = LAB_TARGET_R.get(rec.get("strategy"))
                out.append({"key": f"lab:{rec['strategy'][:8]}:{t['entry_ts']}", "asset": rec["asset"],
                            "direction": t["direction"], "entry": t["entry"], "stop": t["risk"],
                            "target": k * t["risk"] if k else None, "created": t["entry_ts"],
                            "expires": t.get("close_at")})
    except Exception as exc:
        log.info("laboratoire illisible (%s)", exc)
    return out, ok


def lot_for(balance: float, dist: float, info) -> float:
    """Lot qui risque RISK_PCT du solde au stop, arrondi au pas du courtier ; 0 si même le minimum risque trop."""
    contract, step = float(info.trade_contract_size), float(info.volume_step)
    if dist <= 0 or contract <= 0 or step <= 0:
        return 0.0
    raw = balance * RISK_PCT / (dist * contract)
    lot = int(raw / step + 1e-9) * step
    if lot < info.volume_min:
        # le minimum du courtier risque plus que prévu : toléré jusqu'à 2 fois le risque voulu
        return float(info.volume_min) if info.volume_min * dist * contract <= 2 * balance * RISK_PCT else 0.0
    return round(min(lot, float(info.volume_max)), 2)


class Copier:
    def __init__(self, mt5, root: Path, journal: Callable[..., None], clock: Callable[[], float],
                 get: Callable[[str], Any] = _get):
        self.mt5, self.root, self.journal, self.clock, self.get = mt5, root, journal, clock, get
        self.state_file = root / "journal" / "copies.json"
        self.last = 0.0
        try:
            self.state: dict[str, Any] = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.state = {}

    def _save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=1), encoding="utf-8")

    def _filling(self, sym: str) -> int:
        mode = getattr(self.mt5.symbol_info(sym), "filling_mode", 0)
        return self.mt5.ORDER_FILLING_FOK if mode & 1 else self.mt5.ORDER_FILLING_IOC if mode & 2 else self.mt5.ORDER_FILLING_RETURN

    def _positions(self) -> dict[int, Any]:
        return {p.ticket: p for p in (self.mt5.positions_get() or []) if p.magic == MAGIC}

    def _close(self, p, why: str) -> None:
        tick = self.mt5.symbol_info_tick(p.symbol)
        long = p.type == self.mt5.POSITION_TYPE_BUY
        res = self.mt5.order_send({
            "action": self.mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": p.volume, "position": p.ticket,
            "type": self.mt5.ORDER_TYPE_SELL if long else self.mt5.ORDER_TYPE_BUY,
            "price": tick.bid if long else tick.ask, "deviation": 50, "magic": MAGIC, "comment": f"copie {why}"[:31],
            "type_time": self.mt5.ORDER_TIME_GTC, "type_filling": self._filling(p.symbol)})
        self.journal("copie sortie", sens="achat" if long else "vente", prix=tick.bid if long else tick.ask,
                     lot=p.volume, note=f"{p.symbol} {why} (code {getattr(res, 'retcode', None)})")

    def step(self) -> str:
        now = self.clock()
        if now - self.last < EVERY:
            return ""
        self.last = now
        acc = self.mt5.account_info()
        if acc is None or acc.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
            return "copie : compte réel refusé"
        signals, ok = read_signals(self.get)
        live = {s["key"]: s for s in signals}
        pos = self._positions()
        # sorties : signal expiré, ou fermé par le bot (seulement si sa source a bien été lue)
        for key, rec in list(self.state.items()):
            p = pos.get(rec.get("ticket"))
            if p is None:
                if rec.get("ticket") and rec.get("status") == "ouvert":
                    rec["status"] = "fermé"
                continue
            source = "lab" if key.startswith("lab:") else rec["asset"]
            if rec.get("expires") and now >= rec["expires"]:
                self._close(p, "expiration")
            elif source in ok and key not in live:
                self._close(p, "fermé par le bot")
        # entrées
        why = demo_rules.check(self.mt5, MAGIC)
        for key, s in live.items():
            if key in self.state:
                continue
            self.state[key] = {"asset": s["asset"], "status": "vu", "expires": s["expires"]}
            if why:
                self.state[key]["status"] = f"refusé : {why}"
                self.journal("copie refusée", note=f"{key} règle d'arrêt : {why}")
                continue
            if not s["created"] or now - s["created"] > MAX_AGE:
                self.state[key]["status"] = "trop ancien"
                continue
            self.state[key].update(self._open(s, acc.balance))
        self._save()
        return f"copie : {sum(1 for r in self.state.values() if r.get('status') == 'ouvert')} position(s)"

    def _open(self, s: dict[str, Any], balance: float) -> dict[str, Any]:
        sym = SYMBOLS[s["asset"]]
        if not self.mt5.symbol_select(sym, True):
            return {"status": f"symbole {sym} indisponible"}
        info, tick = self.mt5.symbol_info(sym), self.mt5.symbol_info_tick(sym)
        if info is None or tick is None:
            return {"status": "pas de prix"}
        long = s["direction"] == "long"
        px = tick.ask if long else tick.bid
        sg = 1 if long else -1
        sl = round(px - sg * s["stop"], info.digits)
        tp = round(px + sg * s["target"], info.digits) if s["target"] else 0.0
        if s["stop"] < info.trade_stops_level * info.point:
            return {"status": "stop plus court que le minimum du courtier"}
        lot = lot_for(balance, s["stop"], info)
        if lot <= 0:
            return {"status": "taille minimale trop risquée"}
        res = self.mt5.order_send({
            "action": self.mt5.TRADE_ACTION_DEAL, "symbol": sym, "volume": lot,
            "type": self.mt5.ORDER_TYPE_BUY if long else self.mt5.ORDER_TYPE_SELL, "price": px, "sl": sl, "tp": tp,
            "deviation": 50, "magic": MAGIC, "comment": s["key"][:31], "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self._filling(sym)})
        code = getattr(res, "retcode", None)
        ok = code == self.mt5.TRADE_RETCODE_DONE
        self.journal("copie entrée" if ok else "copie rejetée", sens="achat" if long else "vente",
                     prix=getattr(res, "price", px) or px, stop=sl, objectif=tp or "", lot=lot,
                     note=f"{sym} {s['key']} (code {code})")
        if not ok:
            return {"status": f"rejeté (code {code})"}
        return {"status": "ouvert", "ticket": getattr(res, "order", None) or getattr(res, "deal", None), "symbol": sym,
                "lot": lot}
