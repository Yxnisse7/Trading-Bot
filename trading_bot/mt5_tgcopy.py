"""Copie sur le démo MT5 des trades postés dans des canaux Telegram de signaleurs (demandé par Yanisse le 23/10/2026).

Chaîne : tg_listen.py (compte Telegram de Yanisse, lancé et relancé par le pont) écrit chaque message des canaux choisis
dans journal/tg_inbox/ ; ici, chaque message est lu et le pont l'applique sur le démo et l'annonce sur Telegram (sortie
en réponse). Premier canal : BENAGOLD, au format fixe (lu sans Claude, `parse`) :
    SELL GOLD / Prix d'entrée : 4028-4032 / Stop Loss : 4038 / Take Profit 1 : 4019 / 2 : 4007 / 3 : 3989
et « sécurisez » = stop au prix d'entrée (choix de Yanisse le 23/10/2026). Tout autre message est ignoré. Pour un canal
au format libre, "claude": true fait lire chaque message qui parle de trade par Claude (tg_parse.py).
Zone d'entrée : on prend le prix de la zone le plus proche du prix actuel.

Garde-fous : compte démo uniquement, jamais de trade sans stop, 1 % du solde risqué par signal (réparti sur un ordre
par objectif, 3 au plus), au plus 5 signaux ouverts, numéro magique à part (300001), règle d'arrêt de demo_rules.
Prix d'entrée donné et déjà dépassé de plus d'un quart du stop : ordre limite au prix du signaleur, annulé au bout de
2 h. Un trade est fermé au bout de 24 h. Un message vieux de plus de 10 min (PC éteint) n'est pas copié.

Réglages (config.json du PC) : "tg_copy": {"channels": ["nom ou numéro du canal", …], "risk_pct": 0.01, "lot": 0.02}.
"lot" : taille fixe de CHAQUE ordre (choix de Yanisse le 23/10/2026 : 3 trades de 0,02 lot quand il y a 3 TP), à la
place du calcul au risque.
"""
from __future__ import annotations

import csv
import json
import logging
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import demo_rules
from . import messages as msg
from .mt5_copy import COMMENT_MAX, SYMBOLS
from .mt5_hunt import PARIS
from .tg_listen import SESSION_DIR, inbox

log = logging.getLogger("mt5_tgcopy")

MAGIC = 300001
RISK_PCT = 0.01
MIN_LOT_MAX_RISK = 0.03            # au lot minimum du courtier, pas plus de 3 % du solde au stop
MAX_SPLIT = 3
MAX_OPEN = 5
CHASE = 0.25                       # prix parti de plus d'un quart du stop au-delà de l'entrée : ordre limite
PENDING_MAX = 2 * 3600
MAX_HOLD = 24 * 3600
MAX_AGE = 10 * 60
TIMEOUT = 70
RELAUNCH = 60
TAG = "Copie Telegram"
LABELS = {"gold": "Or (XAU/USD)", "nasdaq": "Nasdaq 100", "sp500": "S&P 500", "bitcoin": "Bitcoin",
          "ethereum": "Ethereum", "oil": "Pétrole", "euro": "EUR/USD"}
# un message sans aucun de ces mots ne part pas chez Claude (économie de l'abonnement)
WORDS = re.compile(r"buy|sell|achat|achète|vente|vend|long|short|\bsl\b|\btp\d?\b|stop|\bbe\b|break|clos|clôt|ferm|"
                   r"sort|coupe|sécur|secur|entr|exit|cancel|annul", re.I)
MARKET = re.compile(r"\b(BUY|SELL|ACHAT|VENTE)\s+(GOLD|XAU\w*|OR)\b", re.I)
NUM = r"(\d{3,}(?:[.,]\d+)?)"
ENTRY = re.compile(r"entr[ée]e\s*:?\s*" + NUM + r"(?:\s*[-–/à]\s*" + NUM + ")?", re.I)
STOP = re.compile(r"(?:stop\s*loss|\bsl)\s*:?\s*" + NUM, re.I)
TARGET = re.compile(r"(?:take\s*profit|\btp)\s*\d?\s*:?\s*" + NUM, re.I)
SECURE = re.compile(r"s[ée]curis|break\s*even|\bBE\b", re.I)
CLOSE = re.compile(r"cl[oô]tur|fermez|\bclose\b", re.I)
DEFAULTS = {"command": r"E:\TradingBot\venv\Scripts\python.exe -m trading_bot.tg_parse",
            "listen": r"E:\TradingBot\venv\Scripts\python.exe -m trading_bot.tg_listen run",
            "dir": r"E:\TradingBot\bot", "agent_dir": r"E:\TradingBot\agent\agent", "session_dir": str(SESSION_DIR)}


def _num(x: str) -> float:
    return float(x.replace(",", "."))


def parse(text: str, reply_to: int | None, opened: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Message au format BENAGOLD → action (même forme que tg_parse), ou None si ce n'est pas un trade."""
    m, stop = MARKET.search(text), STOP.search(text)
    if m and stop:
        e = ENTRY.search(text)
        zone = sorted(_num(x) for x in e.groups() if x) if e else []
        return {"type": "ouverture", "marche": "gold", "sens": "achat" if m.group(1).lower() in ("buy", "achat") else
                "vente", "entree": zone[0] if len(zone) == 1 else None, "zone": zone if len(zone) == 2 else None,
                "stop": _num(stop.group(1)), "objectifs": [_num(x) for x in TARGET.findall(text)], "signal": None,
                "raison": "format BENAGOLD"}
    kind = "stop" if SECURE.search(text) else "fermer" if CLOSE.search(text) else None
    if kind is None or not opened:
        return None
    target = next((o for o in opened if o["msg_id"] == reply_to), None) or opened[-1]
    return {"type": kind, "marche": None, "sens": None, "entree": None,
            "stop": target["entree"] if kind == "stop" else None, "objectifs": [], "signal": target["id"],
            "raison": "sécurisez : stop au prix d'entrée" if kind == "stop" else "fermeture demandée"}


class TgCopier:
    def __init__(self, mt5, root: Path, clock: Callable[[], float], relay=None, cfg: dict[str, Any] | None = None,
                 spawn: Callable[..., Any] = subprocess.Popen):
        self.mt5, self.root, self.clock, self.relay, self.spawn = mt5, Path(root), clock, relay, spawn
        self.cfg = {**DEFAULTS, **(cfg or {})}
        self.file = self.root / "journal" / "tg_copy.json"
        self.folder = self.root / "journal" / "tg_copy"
        self.state: dict[str, Any] = {"signals": {}, "texts": {}}
        if self.file.exists():
            try:
                self.state.update(json.loads(self.file.read_text(encoding="utf-8")))
            except ValueError:
                pass
        self.proc: tuple[Any, float, Path, dict[str, Any]] | None = None
        self.listener = None
        self.listen_at = 0.0
        self.warned = False

    def _save(self) -> None:
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.state["texts"] = dict(list(self.state["texts"].items())[-300:])
        self.file.write_text(json.dumps(self.state, indent=1, ensure_ascii=False), encoding="utf-8")

    def _journal(self, row: dict[str, Any]) -> None:
        f = self.root / "journal" / "tg_copy.csv"
        new = not f.exists()
        with f.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["heure_utc", "canal", "action", "detail"])
            if new:
                w.writeheader()
            w.writerow({"heure_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), **row})

    def _post(self, text: str, reply: dict[str, int] | None = None) -> dict[str, int]:
        if self.relay is None or not self.relay.enabled():
            return {}
        return self.relay._post(text, reply=reply) or {}

    # ------------------------------------------------------------------ passage
    def ready(self) -> bool:
        if not self.cfg.get("channels"):
            return False
        return not self.cfg.get("claude") or ((Path(self.cfg["dir"]) / "trading_bot" / "tg_parse.py").exists()
                                              and (Path(self.cfg["agent_dir"]) / "ia.py").exists())

    def step(self) -> str:
        if not self.ready():
            return ""
        acc = self.mt5.account_info()
        if acc is None or acc.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
            return ""
        said = self._listen()
        self._reap()
        for sid in list(self.state["signals"]):
            self._follow(sid)
        if self.proc is None:
            said = self._next() or said
        return said

    def _listen(self) -> str:
        """Garde l'écoute Telegram lancée (relancée au plus une fois par minute si elle s'arrête)."""
        if not any(Path(self.cfg["session_dir"]).glob("*.session")):
            if not self.warned:
                self.warned = True
                return "copie Telegram : compte pas encore connecté (python -m trading_bot.tg_listen login)"
            return ""
        if self.listener is not None and self.listener.poll() is None:
            return ""
        now = self.clock()
        if now - self.listen_at < RELAUNCH:
            return ""
        self.listen_at = now
        out = open(self.root / "journal" / "tg_listen.log", "a", encoding="utf-8")  # noqa: SIM115 — gardé par le processus
        self.listener = self.spawn(self.cfg["listen"].split(), cwd=self.cfg["dir"], stdout=out,
                                   stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return "copie Telegram : écoute des canaux lancée"

    def _next(self) -> str:
        box = inbox(self.root)
        for f in sorted(box.glob("*.json")) if box.exists() else []:
            try:
                m = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            f.unlink(missing_ok=True)
            key = f"{m['chat_id']}:{m['msg_id']}"
            reply = self.state["texts"].get(f"{m['chat_id']}:{m.get('reply_to')}") if m.get("reply_to") else None
            self.state["texts"][key] = m["text"][:1500]
            self._save()
            if self.clock() - float(m.get("date") or 0) > MAX_AGE:
                continue
            if not self.cfg.get("claude"):
                if m.get("edited"):
                    continue                   # un message modifié (« TP1 ✅ » ajouté…) ne rouvre rien
                d = parse(m["text"], m.get("reply_to"), self._opened(m["chat_id"]))
                if d is None:
                    continue
                self._act(d, m)
                return f"copie Telegram : {d['type']} ({m.get('chat')} n°{m['msg_id']})"
            if not WORDS.search(m["text"]) and not (reply and re.search(r"\d", m["text"])):
                continue
            if not m.get("edited") and any(s["key"] == key for s in self.state["signals"].values()):
                continue
            return self._ask(m, reply)
        return ""

    def _ask(self, m: dict[str, Any], reply: str | None) -> str:
        prices = {}
        for k, sym in SYMBOLS.items():
            self.mt5.symbol_select(sym, True)
            t = self.mt5.symbol_info_tick(sym)
            if t is not None and t.bid:
                prices[k] = {"bid": t.bid, "ask": t.ask}
        data = {"id": f"tg-{abs(m['chat_id'])}-{m['msg_id']}-{int(self.clock())}", **m, "reponse_a": reply,
                "ouverts": self._opened(m["chat_id"]), "prix": prices}
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / f"{data['id']}.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        logf = self.folder / f"{data['id']}.log"
        out = open(logf, "w", encoding="utf-8")  # noqa: SIM115 — fermé par le processus
        proc = self.spawn(self.cfg["command"].split() + ["--message", str(path)], cwd=self.cfg["dir"], stdout=out,
                          stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.proc = (proc, self.clock(), logf, data)
        return f"copie Telegram : message lu ({m.get('chat')} n°{m['msg_id']})"

    def _opened(self, chat_id: int) -> list[dict[str, Any]]:
        return [{"id": sid, "marche": s["market"], "sens": "achat" if s["buy"] else "vente", "entree": s["entry"],
                 "stop": s["stop"], "objectifs": s["targets"], "msg_id": s["msg_id"]}
                for sid, s in self.state["signals"].items() if s["chat_id"] == chat_id]

    def _reap(self) -> None:
        if self.proc is None:
            return
        proc, start, logf, data = self.proc
        if proc.poll() is None:
            if self.clock() - start > TIMEOUT + 10:
                proc.kill()
                self.proc = None
                log.warning("copie Telegram : lecture arrêtée après %s s", TIMEOUT + 10)
            return
        self.proc = None
        try:
            lines = [x for x in logf.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
            d = json.loads(lines[-1])
        except (OSError, ValueError, IndexError):
            log.warning("copie Telegram : réponse illisible (%s)", logf.name)
            return
        self._act(d, data)

    def _act(self, d: dict[str, Any], data: dict[str, Any]) -> None:
        self._journal({"canal": data.get("chat"), "action": d.get("type"), "detail": json.dumps(d, ensure_ascii=False)})
        try:
            if d.get("type") == "ouverture":
                self._open(d, data)
            elif d.get("type") == "stop":
                self._move(d, data)
            elif d.get("type") == "fermer":
                self._close_signal(d["signal"], "demandé par le canal")
        except (KeyError, TypeError, ValueError) as exc:
            log.warning("copie Telegram : action impossible (%s)", exc)

    # ------------------------------------------------------------------ ouverture
    def _filling(self, info) -> int:
        mode, m = getattr(info, "filling_mode", 1), self.mt5
        return m.ORDER_FILLING_FOK if mode & 1 else m.ORDER_FILLING_IOC if mode & 2 else m.ORDER_FILLING_RETURN

    @staticmethod
    def per_lot(dist: float, info) -> float:
        """Perte en $ au stop pour 1 lot (valeur du point lue chez le courtier)."""
        size, value = getattr(info, "trade_tick_size", 0) or 0, getattr(info, "trade_tick_value", 0) or 0
        return dist / size * value if size and value else dist * (getattr(info, "trade_contract_size", 100.0) or 100.0)

    @classmethod
    def lots(cls, balance: float, dist: float, info, n: int, risk_pct: float) -> list[float]:
        """Lots, un par objectif : ensemble `risk_pct` du solde au stop ; au lot minimum du courtier, on garde le plus
        d'objectifs possible tant que le tout risque au plus MIN_LOT_MAX_RISK du solde ; [] si même un seul lot
        minimum risque plus que ça."""
        per_lot = cls.per_lot(dist, info)
        step = getattr(info, "volume_step", 0.01) or 0.01
        vmin = getattr(info, "volume_min", 0.01) or 0.01
        if per_lot <= 0:
            return []
        total = balance * risk_pct / per_lot
        cap = balance * max(risk_pct, MIN_LOT_MAX_RISK)
        while n >= 1:
            each = max(vmin, int(total / n / step + 1e-9) * step)
            if each * n * per_lot <= cap + 1e-9:
                return [round(each, 2)] * n
            n -= 1
        return []

    def _open(self, d: dict[str, Any], data: dict[str, Any]) -> None:
        key = f"{data['chat_id']}:{data['msg_id']}"
        if any(s["key"] == key for s in self.state["signals"].values()):
            return
        if len(self.state["signals"]) >= MAX_OPEN:
            return self._refuse(data, d, f"déjà {MAX_OPEN} signaux ouverts")
        why = demo_rules.check(self.mt5, MAGIC)
        if why:
            return self._refuse(data, d, f"règle d'arrêt ({why})")
        market, buy = d["marche"], d["sens"] == "achat"
        sym = SYMBOLS[market]
        self.mt5.symbol_select(sym, True)
        tick, info, acc = self.mt5.symbol_info_tick(sym), self.mt5.symbol_info(sym), self.mt5.account_info()
        if tick is None or info is None or not tick.bid:
            return self._refuse(data, d, "marché fermé")
        s = 1 if buy else -1
        now_px = tick.ask if buy else tick.bid
        zone = d.get("zone")
        entry = min(max(now_px, zone[0]), zone[1]) if zone else float(d["entree"]) if d.get("entree") is not None \
            else now_px
        stop = float(d["stop"])
        dist = (entry - stop) * s
        lvl = getattr(info, "trade_stops_level", 0) * getattr(info, "point", 0.01)
        if dist <= 0:
            return self._refuse(data, d, "stop du mauvais côté de l'entrée")
        if (now_px - stop) * s <= lvl:
            return self._refuse(data, d, "le prix a déjà atteint le stop")
        limit = (now_px - entry) * s > CHASE * dist
        px = entry if limit else now_px
        targets = [float(x) for x in d.get("objectifs") or [] if (float(x) - px) * s > lvl][:MAX_SPLIT]
        if d.get("objectifs") and not targets:
            return self._refuse(data, d, "le prix a déjà dépassé les objectifs")
        digits = int(getattr(info, "digits", 2) or 2)
        n = max(1, len(targets))
        lots = [round(float(self.cfg["lot"]), 2)] * n if self.cfg.get("lot") else \
            self.lots(acc.balance, abs(px - stop), info, n, float(self.cfg.get("risk_pct", RISK_PCT)))
        if not lots:
            return self._refuse(data, d, "même le plus petit lot risque trop")
        m = self.mt5
        comment = f"tg {data.get('chat', '')}"[:COMMENT_MAX]
        tickets = []
        for i, lot in enumerate(lots):
            tp = round(targets[i], digits) if i < len(targets) else 0.0
            req = {"action": m.TRADE_ACTION_DEAL, "symbol": sym, "volume": lot,
                   "type": m.ORDER_TYPE_BUY if buy else m.ORDER_TYPE_SELL, "price": round(px, digits),
                   "sl": round(stop, digits), "tp": tp, "deviation": 30, "magic": MAGIC, "comment": comment,
                   "type_time": m.ORDER_TIME_GTC, "type_filling": self._filling(info)}
            if limit:
                req.update(action=m.TRADE_ACTION_PENDING, type=m.ORDER_TYPE_BUY_LIMIT if buy else m.ORDER_TYPE_SELL_LIMIT,
                           type_filling=m.ORDER_FILLING_RETURN)
                req.pop("deviation")
            res = m.order_send(req)
            if getattr(res, "retcode", None) == m.TRADE_RETCODE_DONE:
                tickets.append(int(getattr(res, "order", 0) or 0))
                if not limit:
                    px = float(getattr(res, "price", px) or px)
            else:
                log.warning("copie Telegram : ordre rejeté (code %s)", getattr(res, "retcode", None))
        if not tickets:
            return self._refuse(data, d, "ordre refusé par le courtier")
        sid = f"{abs(data['chat_id'])}-{data['msg_id']}"
        sig = {"key": key, "chat": data.get("chat"), "chat_id": data["chat_id"], "msg_id": data["msg_id"],
               "market": market, "sym": sym, "buy": buy, "entry": round(px, digits), "stop": round(stop, digits),
               "targets": [round(x, digits) for x in targets], "tickets": tickets, "lots": lots[:len(tickets)],
               "risk_usd": round(self.per_lot(abs(px - stop), info) * sum(lots[:len(tickets)]), 2),
               "digits": digits, "pending": limit, "placed": self.clock(), "opened": None if limit else self.clock(),
               "msg": {}}
        sig["msg"] = self._announce(sig, d)
        self.state["signals"][sid] = sig
        self._save()

    def _refuse(self, data: dict[str, Any], d: dict[str, Any], why: str) -> None:
        log.info("copie Telegram : pas copié (%s)", why)
        self._journal({"canal": data.get("chat"), "action": "pas copié", "detail": why})
        self._post(f"📡 {TAG} · {msg.esc(data.get('chat', ''))} : {'achat' if d.get('sens') == 'achat' else 'vente'} "
                   f"{msg.esc(LABELS.get(d.get('marche'), d.get('marche')))} <b>pas copié</b> ({msg.esc(why)}).")

    def _announce(self, s: dict[str, Any], d: dict[str, Any]) -> dict[str, int]:
        dg = s["digits"]
        kind = ("↗️ ACHAT" if s["buy"] else "↘️ VENTE") + (" LIMITE" if s["pending"] else "")
        wait = datetime.fromtimestamp(s["placed"] + PENDING_MAX, PARIS).strftime("%H:%M") if s["pending"] else ""
        lines = [f"<b>📡 {kind} · {msg.esc(LABELS[s['market']])}</b> · {TAG}",
                 f"Canal : {msg.esc(s['chat'])}",
                 f"Entrée {msg.code_price(s['entry'], dg)}" + (f"  (en attente jusqu'à {wait})" if wait else ""),
                 f"SL     {msg.code_price(s['stop'], dg)}"]
        lines += [f"TP{i + 1}    {msg.code_price(t, dg)}" for i, t in enumerate(s["targets"])] or ["TP     aucun"]
        lines += ["", f"MT5 démo : {len(s['lots'])} × {msg.num(s['lots'][0], 2)} lot "
                      f"(risque {msg.num(s['risk_usd'], 2)} $ si tout touche le SL), "
                      f"fermé au bout de {MAX_HOLD // 3600} h au plus.",
                  "<i>Copié depuis le canal par le pont du PC. Démo seulement, aucun ordre réel.</i>"]
        return self._post("\n".join(lines))

    # ------------------------------------------------------------------ stop déplacé, fermeture
    def _live(self, s: dict[str, Any]) -> tuple[list, list]:
        pos = [p for p in (self.mt5.positions_get(symbol=s["sym"]) or []) if p.magic == MAGIC and p.ticket in s["tickets"]]
        orders = [o for o in (self.mt5.orders_get(symbol=s["sym"]) or []) if o.ticket in s["tickets"]]
        return pos, orders

    def _move(self, d: dict[str, Any], data: dict[str, Any]) -> None:
        s = self.state["signals"].get(d["signal"])
        if not s:
            return
        new = round(float(d["stop"]), s["digits"])
        tick = self.mt5.symbol_info_tick(s["sym"])
        sgn = 1 if s["buy"] else -1
        if tick is None or ((tick.bid if s["buy"] else tick.ask) - new) * sgn <= 0:
            self._post(f"📡 Stop à {msg.num(new, s['digits'])} demandé par le canal, <b>pas appliqué</b> : le prix "
                       f"est déjà de l'autre côté.", reply=s["msg"])
            return
        pos, orders = self._live(s)
        m = self.mt5
        for p in pos:
            m.order_send({"action": m.TRADE_ACTION_SLTP, "symbol": s["sym"], "position": p.ticket, "sl": new,
                          "tp": getattr(p, "tp", 0.0)})
        for o in orders:
            m.order_send({"action": m.TRADE_ACTION_MODIFY, "order": o.ticket, "price": o.price_open, "sl": new,
                          "tp": getattr(o, "tp", 0.0)})
        be = abs(new - s["entry"]) < 10 ** -s["digits"] * 5
        s["stop"] = new
        self._save()
        self._post(f"📡 Stop déplacé à {msg.code_price(new, s['digits'])}{' (BE)' if be else ''}, demandé par le canal.",
                   reply=s["msg"])

    def _close_signal(self, sid: str, why: str) -> None:
        s = self.state["signals"].get(sid)
        if not s:
            return
        pos, orders = self._live(s)
        m = self.mt5
        for o in orders:
            m.order_send({"action": m.TRADE_ACTION_REMOVE, "order": o.ticket})
        tick = m.symbol_info_tick(s["sym"])
        for p in pos:
            long = p.type == m.POSITION_TYPE_BUY
            m.order_send({"action": m.TRADE_ACTION_DEAL, "symbol": s["sym"], "volume": p.volume, "position": p.ticket,
                          "type": m.ORDER_TYPE_SELL if long else m.ORDER_TYPE_BUY,
                          "price": tick.bid if long else tick.ask, "deviation": 30, "magic": MAGIC,
                          "comment": "tg fin", "type_time": m.ORDER_TIME_GTC,
                          "type_filling": self._filling(m.symbol_info(s["sym"]))})
        s["why"] = why

    # ------------------------------------------------------------------ suivi
    def _follow(self, sid: str) -> None:
        s = self.state["signals"][sid]
        pos, orders = self._live(s)
        now = self.clock()
        if s["pending"]:
            if pos:
                s["pending"], s["opened"] = False, now
                s["entry"] = float(getattr(pos[0], "price_open", s["entry"]) or s["entry"])
                self._save()
                self._post(f"▶️ Ordre exécuté à {msg.code_price(s['entry'], s['digits'])}", reply=s["msg"])
            elif orders:
                if now - s["placed"] >= PENDING_MAX:
                    for o in orders:
                        self.mt5.order_send({"action": self.mt5.TRADE_ACTION_REMOVE, "order": o.ticket})
                return
            elif not any(len(self.mt5.history_deals_get(position=t) or []) for t in s["tickets"]):
                why = s.get("why") or f"prix d'entrée pas touché en {PENDING_MAX // 3600} h"
                self._post(f"⌛ Annulé : {msg.esc(why)}.", reply=s["msg"])
                self._journal({"canal": s["chat"], "action": "annulé", "detail": sid})
                self.state["signals"].pop(sid)
                self._save()
                return
        if pos or orders:
            if s.get("opened") and now - s["opened"] >= MAX_HOLD and not s.get("why"):
                self._close_signal(sid, f"{MAX_HOLD // 3600} h atteintes")
            return
        deals = [self.mt5.history_deals_get(position=t) or [] for t in s["tickets"]]
        if not any(deals):                     # rien dans l'historique : pas encore à jour, ou ordre jamais exécuté
            if now - (s.get("opened") or s["placed"]) > 600:
                self._journal({"canal": s["chat"], "action": "disparu", "detail": sid})
                self.state["signals"].pop(sid)
                self._save()
            return
        if any(len(x) == 1 for x in deals):
            return                             # l'historique du courtier n'a pas encore la sortie
        profit = sum(float(x.profit) + float(getattr(x, "commission", 0) or 0) + float(getattr(x, "swap", 0) or 0)
                     for ds in deals for x in ds)
        risk = s.get("risk_usd")
        r = f" ({profit / risk:+.2f} R)".replace(".", ",") if risk else ""
        why = f" · {s['why']}" if s.get("why") else ""
        self._post(f"<b>{'✅' if profit >= 0 else '❌'} Sortie · {msg.esc(LABELS[s['market']])} · {TAG}</b>\n"
                   f"Résultat MT5 démo : {profit:+.2f} $".replace(".", ",") + f"{r}{why}", reply=s["msg"])
        self._journal({"canal": s["chat"], "action": "sortie", "detail": f"{sid} {profit:+.2f} $"})
        self.state["signals"].pop(sid)
        self._save()
