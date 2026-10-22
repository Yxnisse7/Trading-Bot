"""L'agent IA cherche lui-même des trades sur l'or et le Nasdaq, aux heures où ils bougent (demandé par Yanisse le 20/10/2026).

Il prend la suite des passages horaires de l'assistant (13-20/10) sans tourner toute la journée : le pont le réveille
à l'ouverture de Londres (9h05 Paris), aux stats américaines (14h35), à l'ouverture de New York (15h35) et 20 min
après chaque annonce USD à fort impact, en semaine. À chaque réveil, il reçoit les graphiques de l'or (5 min, 15 min,
1 h, jour) et les annonces, et répond achat, vente ou rien, avec un stop et un objectif. Nasdaq (ajouté le même jour, à
la demande de Yanisse) : réveil à 15h50 (20 min après l'ouverture de Wall Street) et 20 min après les annonces USD fortes.

Le jugement est dans le dépôt privé de l'agent (agent/chasse.py, copié sur le PC) ; ici, seulement les horaires, les
garde-fous et les ordres. Garde-fous : compte démo uniquement, confiance ≥ 3/5, stop du bon côté et objectif ≥ 1 R,
1 % du solde risqué, une seule position de l'agent à la fois (numéro magique à part), sortie au SL/TP ou au bout de
4 h, règle d'arrêt dans demo_rules (une position par marché). Le trade est annoncé sur Telegram avec la raison de l'agent, la sortie en réponse.
"""
from __future__ import annotations

import json
import logging
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from . import claude_desk as desk
from . import demo_rules
from . import messages as msg
from .mt5_copy import SYMBOLS
from .mt5_local import server_offset

log = logging.getLogger("mt5_hunt")

PARIS = ZoneInfo("Europe/Paris")
MAGIC = 777002
# marché → (nom, heures fixes Paris, lot maximum)
ASSETS = {"gold": ("Or (XAU/USD)", (("09:05", "ouverture de Londres"), ("14:35", "stats américaines"),
                                    ("15:35", "ouverture de New York")), 0.10),
          "nasdaq": ("Nasdaq 100", (("15:50", "ouverture de Wall Street"),), 2.0)}
# veille régulière (demande de Yanisse le 22/10/2026 : 2 à 3 recherches par heure) : plages de Paris, réveil toutes
# les `every_minutes` (config du pont, 20 par défaut) en plus des heures fixes
WATCH = {"gold": (("09:00", "12:00"), ("14:30", "18:00")), "nasdaq": (("15:40", "21:00"),)}
EVERY = 20
AFTER_NEWS = 20 * 60                      # s après une annonce USD à fort impact
LATE = 10 * 60                            # un réveil manqué de plus de 10 min est sauté
MAX_HOLD = 4 * 3600
MIN_CONF = 3
TIMEOUT = 80
FRAMES = (("candles_5m", "TIMEFRAME_M5", 288), ("candles_15m", "TIMEFRAME_M15", 96),
          ("candles_1h", "TIMEFRAME_H1", 48), ("candles_1d", "TIMEFRAME_D1", 20))
DEFAULTS = {"command": r"E:\TradingBot\venv\Scripts\python.exe E:\TradingBot\agent\agent\chasse.py",
            "dir": r"E:\TradingBot\agent"}


def slots(day: datetime, events: list[dict[str, Any]], asset: str = "gold", table: dict | None = None,
          news: bool = True, watch: tuple = (), every: int = EVERY) -> list[tuple[int, str]]:
    """Réveils du jour (heure UTC en s, moment) : heures fixes en semaine, veille toutes les `every` min dans les
    plages `watch`, + 20 min après les annonces USD fortes."""
    d = day.astimezone(PARIS).date()
    if d.weekday() >= 5:
        return []

    def at(hm: str) -> int:
        return int(datetime.combine(d, datetime.strptime(hm, "%H:%M").time(), PARIS).timestamp())

    out = [(at(hm), name) for hm, name in (table or ASSETS)[asset][1]]
    for a, b in watch if every > 0 else ():
        out += [(t, "veille") for t in range(at(a), at(b) + 1, every * 60)]
    for e in events if news else ():
        if e.get("impact") != "high" or not str(e.get("name", "")).startswith("USD"):
            continue
        at = datetime.fromisoformat(e["at"])
        if at.astimezone(PARIS).date() == d:
            out.append((int(at.timestamp()) + AFTER_NEWS, f"après annonce : {e['name'][4:]}"))
    out.sort()
    keep: list[tuple[int, str]] = []
    for ts, name in out:                  # deux réveils trop proches : un seul (une heure fixe passe avant la veille)
        if keep and ts - keep[-1][0] < min(900, every * 60 - 60 if every > 0 else 900):
            if name != "veille" and keep[-1][1] == "veille":
                keep[-1] = (ts, name)
            continue
        keep.append((ts, name))
    return keep


class Hunter:
    MAGIC, ASSETS, NAME, MAX_HOLD, FRAMES, DEFAULTS = MAGIC, ASSETS, "chasse", MAX_HOLD, FRAMES, DEFAULTS
    TAG, COMMENT, NEWS, WATCH = "Trade de l'agent IA", "agent IA", True, WATCH

    def __init__(self, mt5, root: Path, clock: Callable[[], float], relay=None, cfg: dict[str, Any] | None = None,
                 spawn: Callable[..., Any] = subprocess.Popen):
        self.mt5, self.root, self.clock, self.relay, self.spawn = mt5, Path(root), clock, relay, spawn
        self.cfg = {**self.DEFAULTS, **(cfg or {})}
        self.file = self.root / "journal" / f"{self.NAME}.json"
        self.folder = self.root / "journal" / self.NAME
        self.state: dict[str, Any] = {"done": [], "trades": {}}
        if self.file.exists():
            try:
                self.state.update(json.loads(self.file.read_text(encoding="utf-8")))
            except ValueError:
                pass
        if self.state.get("trade"):             # ancien format (or seul)
            self.state["trades"]["gold"] = self.state.pop("trade")
        self.state.pop("trade", None)
        self.proc: tuple[Any, float, str, Path, dict[str, Any]] | None = None

    def _save(self) -> None:
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.state["done"] = self.state["done"][-200:]
        self.file.write_text(json.dumps(self.state, indent=1, ensure_ascii=False), encoding="utf-8")

    def extra(self, asset: str, now: float) -> dict[str, Any]:
        """Champs en plus pour l'agent (aucun ici)."""
        return {}

    def may_trade(self, asset: str, now: float) -> bool:
        """Règle de journée propre à une méthode (aucune ici)."""
        return True

    def closed(self, asset: str, t: dict[str, Any], profit: float, r: float) -> list[str]:
        """Appelé à la sortie d'un trade : lignes en plus pour le message de sortie (aucune ici)."""
        return []

    def ready(self) -> bool:
        """Le fichier de l'agent est sur le PC (sinon le pont ne fait rien)."""
        cmd = self.cfg["command"].split()
        return Path(self.cfg["dir"]).exists() and Path(cmd[-1]).exists()

    def events(self) -> list[dict[str, Any]]:
        for f in (self.root / "journal" / "bot_pc" / "calendar_cache.json", self.root / "bot" / "data" / "calendar_cache.json"):
            try:
                return json.loads(f.read_text(encoding="utf-8")).get("events", [])
            except (OSError, ValueError):
                continue
        return []

    # ------------------------------------------------------------------ passage
    def step(self) -> str:
        self._reap()
        for asset in list(self.state["trades"]):
            self._follow(asset)
        now = self.clock()
        if self.proc is not None or not self.ready():
            return ""
        acc = self.mt5.account_info()
        if acc is None or acc.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
            return ""
        evs = self.events()
        for asset in self.ASSETS:
            if self.state["trades"].get(asset) or not self.may_trade(asset, now):
                continue
            for ts, name in slots(datetime.fromtimestamp(now, timezone.utc), evs, asset, self.ASSETS, self.NEWS,
                                  self.WATCH.get(asset, ()), int(self.cfg.get("every_minutes", EVERY))):
                key = f"{asset}:{ts}"
                if key in self.state["done"] or not ts <= now <= ts + LATE:
                    continue
                self.state["done"].append(key)
                self._save()
                return self._wake(asset, now, name, evs, acc)
        return ""

    def _candles(self, sym: str, tf: str, n: int, off: int) -> list[list[float]]:
        rates = self.mt5.copy_rates_from_pos(sym, getattr(self.mt5, tf), 0, n + 1)
        rows = [[int(x["time"]) - off, float(x["open"]), float(x["high"]), float(x["low"]), float(x["close"])]
                for x in (rates if rates is not None else [])]
        return rows[:-1][-n:]                 # la dernière bougie est en cours

    def _wake(self, asset: str, now: float, moment: str, evs: list[dict[str, Any]], acc) -> str:
        sym = SYMBOLS[asset]
        self.mt5.symbol_select(sym, True)
        off = server_offset(self.mt5, sym, now)
        tick = self.mt5.symbol_info_tick(sym)
        if off is None or tick is None:
            return f"chasse : marché fermé ({asset})"
        why = demo_rules.check(self.mt5, self.MAGIC)
        if why:
            return f"chasse : règle d'arrêt ({why})"
        data = {"id": f"{self.NAME}-{asset}-{int(now)}", "asset": asset, "asset_label": self.ASSETS[asset][0],
                "now": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)), "moment": moment,
                "bid": tick.bid, "ask": tick.ask, "spread": round(tick.ask - tick.bid, 2), "solde": acc.balance,
                "annonces": [{"heure": e["at"], "titre": e["name"], "impact": e.get("impact")} for e in evs
                             if str(e.get("name", "")).startswith("USD")
                             and -7200 <= datetime.fromisoformat(e["at"]).timestamp() - now <= 6 * 3600],
                "position_agent": None}
        for k, tf, n in self.FRAMES:
            data[k] = self._candles(sym, tf, n, off)
        data.update(self.extra(asset, now))
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / f"{data['id']}.json"
        path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        out = open(self.folder / f"{data['id']}.log", "w", encoding="utf-8")
        proc = self.spawn(self.cfg["command"].split() + ["--marche", str(path)], cwd=self.cfg["dir"], stdout=out,
                          stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.proc = (proc, now, data["id"], self.folder / f"{data['id']}.log", data)
        log.info("chasse : agent réveillé (%s, %s)", asset, moment)
        return f"chasse : agent réveillé ({asset}, {moment})"

    def _reap(self) -> None:
        if self.proc is None:
            return
        proc, start, sid, logf, data = self.proc
        if proc.poll() is None:
            if self.clock() - start > TIMEOUT + 10:
                proc.kill()
                self.proc = None
                log.warning("chasse : agent arrêté après %s s", TIMEOUT + 10)
            return
        self.proc = None
        try:
            lines = [x for x in logf.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
            answer = json.loads(lines[-1])
        except (OSError, ValueError, IndexError):
            log.warning("chasse : réponse de l'agent illisible (%s)", logf.name)
            return
        self._decide(answer, data)

    # ------------------------------------------------------------------ décision
    def check(self, a: dict[str, Any], px_buy: float, px_sell: float, stops_level: float) -> str | None:
        """Raison de refuser la réponse de l'agent, ou None si l'ordre peut partir."""
        if a.get("action") not in ("achat", "vente"):
            return "rien à faire"
        if int(a.get("confiance") or 0) < MIN_CONF:
            return f"confiance {a.get('confiance')}/5 < {MIN_CONF}"
        try:
            stop, target = float(a["stop"]), float(a["objectif"])
        except (KeyError, TypeError, ValueError):
            return "stop ou objectif manquant"
        buy = a["action"] == "achat"
        px = px_buy if buy else px_sell
        risk, gain = (px - stop, target - px) if buy else (stop - px, px - target)
        if risk <= max(stops_level, 0.0) or gain <= 0:
            return f"stop {stop} ou objectif {target} du mauvais côté du prix {px}"
        if gain < risk:
            return f"objectif {gain:.2f} < risque {risk:.2f}"
        return None

    @staticmethod
    def lot(balance: float, dist: float, info, max_lot: float) -> float:
        """Lot qui perd 1 % du solde au stop (valeur du point lue chez le courtier), arrondi vers le bas."""
        size, value = getattr(info, "trade_tick_size", 0) or 0, getattr(info, "trade_tick_value", 0) or 0
        per_lot = dist / size * value if size and value else dist * (getattr(info, "trade_contract_size", 100.0) or 100.0)
        step = getattr(info, "volume_step", 0.01) or 0.01
        vmin = getattr(info, "volume_min", 0.01) or 0.01
        lot = int(balance * desk.RISK_PCT / per_lot / step) * step if per_lot > 0 else vmin
        return round(max(vmin, min(max_lot, lot)), 2)

    def _decide(self, a: dict[str, Any], data: dict[str, Any]) -> None:
        asset = data["asset"]
        sym = SYMBOLS[asset]
        tick = self.mt5.symbol_info_tick(sym)
        info = self.mt5.symbol_info(sym)
        lvl = getattr(info, "trade_stops_level", 0) * getattr(info, "point", 0.01)
        why = self.check(a, tick.ask, tick.bid, lvl)
        desk._journal({"action": f"agent {asset} : {a.get('action')}", "prix": tick.bid, "stop": a.get("stop"),
                       "objectif": a.get("objectif"), "resultat": why or "",
                       "raison": f"[{data['moment']}] {a.get('raison', '')}"})
        if why:
            log.info("chasse : pas d'ordre (%s)", why)
            return
        acc = self.mt5.account_info()
        if acc is None or acc.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
            return
        buy = a["action"] == "achat"
        px = tick.ask if buy else tick.bid
        digits = int(getattr(info, "digits", 2) or 2)
        stop, target = round(float(a["stop"]), digits), round(float(a["objectif"]), digits)
        lot = self.lot(acc.balance, abs(px - stop), info, self.ASSETS[asset][2])
        res = self.mt5.order_send({"action": self.mt5.TRADE_ACTION_DEAL, "symbol": sym, "volume": lot,
                                   "type": self.mt5.ORDER_TYPE_BUY if buy else self.mt5.ORDER_TYPE_SELL, "price": px,
                                   "sl": stop, "tp": target, "deviation": 30, "magic": self.MAGIC, "comment": self.COMMENT,
                                   "type_time": self.mt5.ORDER_TIME_GTC, "type_filling": self._filling(info)})
        if getattr(res, "retcode", None) != self.mt5.TRADE_RETCODE_DONE:
            log.warning("chasse : ordre rejeté (code %s)", getattr(res, "retcode", None))
            return
        entry = float(getattr(res, "price", px) or px)
        ticket = int(getattr(res, "order", 0) or 0)
        size, value = getattr(info, "trade_tick_size", 0) or 0, getattr(info, "trade_tick_value", 0) or 0
        risk_usd = (abs(entry - stop) / size * value if size and value else abs(entry - stop) * 100.0) * lot
        trade = {"ticket": ticket, "buy": buy, "entry": entry, "stop": stop, "target": target, "lot": lot,
                 "risk_usd": round(risk_usd, 2), "digits": digits, "opened": self.clock(), "moment": data["moment"],
                 "label": data["asset_label"], "msg": {}}
        trade["msg"] = self._announce(trade, a, digits)
        self.state["trades"][asset] = trade
        self._save()

    def _filling(self, info) -> int:
        mode = getattr(info, "filling_mode", 1)
        m = self.mt5
        return m.ORDER_FILLING_FOK if mode & 1 else m.ORDER_FILLING_IOC if mode & 2 else m.ORDER_FILLING_RETURN

    def _announce(self, t: dict[str, Any], a: dict[str, Any], digits: int) -> dict[str, int]:
        if self.relay is None or not self.relay.enabled():
            return {}
        chg = lambda v: msg.pct((v / t["entry"] - 1) * 100.0)  # noqa: E731
        conf = int(a.get("confiance") or 0)
        lines = [f"<b>🤖 {'↗️ ACHAT' if t['buy'] else '↘️ VENTE'} · {msg.esc(t['label'])}</b> · {self.TAG}",
                 f"Entrée {msg.code_price(t['entry'], digits)}",
                 f"SL     {msg.code_price(t['stop'], digits)}  {chg(t['stop'])}",
                 f"TP     {msg.code_price(t['target'], digits)}  {chg(t['target'])}",
                 f"Moment : {msg.esc(t['moment'])} · confiance {conf}/5",
                 "",
                 msg.esc(str(a.get("raison", ""))),
                 "",
                 f"MT5 démo : {msg.num(t['lot'], 2)} lot (1 % du solde au SL), sortie au SL, au TP ou au bout de {self.MAX_HOLD // 3600} h.",
                 "<i>Décidé par l'agent IA sur ton PC. Démo seulement, aucun ordre réel.</i>"]
        return self.relay._post("\n".join(lines))

    # ------------------------------------------------------------------ suivi
    def _close(self, sym: str, p) -> None:
        tick = self.mt5.symbol_info_tick(sym)
        long = p.type == self.mt5.POSITION_TYPE_BUY
        self.mt5.order_send({"action": self.mt5.TRADE_ACTION_DEAL, "symbol": sym, "volume": p.volume,
                             "position": p.ticket, "type": self.mt5.ORDER_TYPE_SELL if long else self.mt5.ORDER_TYPE_BUY,
                             "price": tick.bid if long else tick.ask, "deviation": 30, "magic": self.MAGIC,
                             "comment": f"{self.COMMENT} fin", "type_time": self.mt5.ORDER_TIME_GTC,
                             "type_filling": self._filling(self.mt5.symbol_info(sym))})

    def _follow(self, asset: str) -> None:
        t = self.state["trades"].get(asset)
        if not t:
            return
        sym = SYMBOLS[asset]
        open_ = [p for p in (self.mt5.positions_get(symbol=sym) or []) if p.magic == self.MAGIC]
        if open_:
            if self.clock() - t["opened"] >= self.MAX_HOLD:
                for p in open_:
                    self._close(sym, p)
            return
        deals = self.mt5.history_deals_get(position=t["ticket"]) or [] if t.get("ticket") else []
        if t.get("ticket") and len(deals) < 2:
            return                             # l'historique du courtier n'a pas encore la sortie
        profit = sum(float(d.profit) + float(getattr(d, "commission", 0) or 0) + float(getattr(d, "swap", 0) or 0)
                     for d in deals)
        exit_px = float(deals[-1].price) if deals else None
        risk = t.get("risk_usd") or abs(t["entry"] - t["stop"]) * t["lot"] * 100.0
        r = profit / risk if risk else 0.0
        extra = self.closed(asset, t, profit, r)
        if self.relay is not None and self.relay.enabled() and t.get("msg"):
            lines = [f"<b>{'✅' if profit >= 0 else '❌'} Sortie · {msg.esc(t.get('label', asset))} · {self.TAG}</b>",
                     f"Sortie {msg.code_price(exit_px, t.get('digits', 2))}" if exit_px else "Sortie",
                     f"Résultat MT5 démo : {profit:+.2f} $ ({r:+.2f} R)".replace(".", ","), *extra]
            self.relay._post("\n".join(lines), reply=t["msg"])
        desk._journal({"action": f"{self.COMMENT} {asset} : sortie", "prix": exit_px or "", "stop": "", "objectif": "",
                       "resultat": round(profit, 2), "raison": t["moment"]})
        self.state["trades"].pop(asset, None)
        self._save()
