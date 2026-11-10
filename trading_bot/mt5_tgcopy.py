"""Copie sur le démo MT5 des trades postés dans des canaux Telegram de signaleurs (demandé par Yanisse le 23/10/2026).

Chaîne : tg_listen.py (compte Telegram de Yanisse, lancé et relancé par le pont) écrit chaque message des canaux choisis
dans journal/tg_inbox/ ; ici, chaque message est lu et le pont l'applique sur le démo et l'annonce sur Telegram (sortie
en réponse). Premier canal : BENAGOLD, au format fixe (lu sans Claude, `parse`) :
    SELL GOLD / Prix d'entrée : 4028-4032 / Stop Loss : 4038 / Take Profit 1 : 4019 / 2 : 4007 / 3 : 3989
et « sécurisez » = stop au prix d'entrée (choix de Yanisse le 23/10/2026). Deuxième canal (28/10/2026) : RTZ ACADEMY,
    🚨SELL XAUUSD / ENTRY : 4139-4145 / SL : 4148 / TP1: 4132
(« BUY NOW XAUUSD » aussi ; les « TRADE MODIFIER » et un signal renvoyé à l'identique ne rouvrent rien).
Tout autre message est ignoré. Pour un canal
au format libre, "claude": true fait lire chaque message qui parle de trade par Claude (tg_parse.py).
Zone d'entrée : on prend le prix de la zone le plus proche du prix actuel.

Garde-fous : compte démo uniquement, jamais de trade sans stop, 1 % du solde risqué par signal (réparti sur un ordre
par objectif, 3 au plus), au plus 5 signaux ouverts, numéro magique à part (300001), règle d'arrêt de demo_rules.
Prix d'entrée donné et déjà dépassé de plus d'un quart du stop : ordre limite au prix du signaleur, annulé au bout de
2 h. Un trade est fermé au bout de 24 h. Un message vieux de plus de 10 min (PC éteint) n'est pas copié.

Réglages (config.json du PC) : "tg_copy": {"channels": ["nom ou numéro du canal", …], "risk_pct": 0.01, "lot": 0.02}.
"lot" : taille fixe de CHAQUE ordre (choix de Yanisse le 23/10/2026 : 3 trades de 0,02 lot quand il y a 3 TP), à la
place du calcul au risque. "tp_max": {"RTZ ACADEMY": 1} : au plus ce nombre d'objectifs pour ce canal (RTZ : TP1
seul, c'est ce qui a été rejoué le 28/10/2026 : +0,18 R par trade contre +0,05 R avec tous les TP). "opens_only":
["RTZ ACADEMY"] : on ne copie que les ouvertures de ce canal, sans « sécurisez / BE / clôturez » (RTZ en parle dans
presque chaque message, souvent avant d'avoir à le faire ; le rejeu est fait sans).
10/11/2026 (demande de Yanisse) : "no_agent": ["RTZ ACADEMY"] copie ce canal sans demander l'agent IA (ni décision, ni
avis), et "manage": ["RTZ ACADEMY"] suit ses consignes de gestion (lues sur 6 243 messages du canal, `gestion`) :
« MODIFIER TP1 A x » / « MODIFIER SL A x » / « DÉPLACEZ SL A x » changent l'objectif ou le stop, « METTEZ VOUS BE » /
« SÉCURISEZ » mettent le stop au prix d'entrée, « CLÔTUREZ 75 % » ferme 75 % du lot (tout, si le lot est trop petit
pour être coupé), « OUT » / « ON CLÔTURE » / « TRADE ANNULER » ferment tout ; quand RTZ corrige son message de signal
(« TRADE MODIFIER »), le nouveau stop, les nouveaux objectifs et, pour un ordre en attente, la nouvelle entrée sont
appliqués. Les conseils au choix (« vous pouvez », « n'hésitez pas ») ne déclenchent rien. Une consigne en réponse à
un signal qu'on n'a pas copié est ignorée ; sans réponse, elle vise le dernier signal copié du canal.
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

from . import decideur as dc
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
MARKET = re.compile(r"\b(BUY|SELL|ACHAT|VENTE)\s+(?:NOW\s+)?(GOLD|XAU\w*|OR)\b", re.I)
NUM = r"(\d{3,}(?:[.,]\d+)?)"
ENTRY = re.compile(r"(?:entr[ée]e|entry(?:\s*price)?)\s*:?\s*" + NUM + r"(?:\s*[-–/à]\s*" + NUM + ")?", re.I)
STOP = re.compile(r"(?:stop\s*loss|\bsl)\s*:?\s*" + NUM, re.I)
TARGET = re.compile(r"(?:take\s*profit|\btp)\s*\d?\s*:?\s*" + NUM, re.I)
SECURE = re.compile(r"s[ée]curis|break\s*even|\bBE\b", re.I)
# Fermetures (choix de Yanisse le 26/10/2026, après lecture de 48 messages du canal) : « Close now », « on clôture
# (toute) la position », « fermer la position » ou un message qui commence par « Clôture » ferment tout ;
# « Clôture partielle » ferme un seul ordre (celui du TP le plus proche) ; les témoignages (« belle clôture »,
# « j'ai clôturé mon … », « les clôtures ») ne déclenchent rien.
PARTIAL = re.compile(r"cl[oô]ture\s+partielle|cl[oô]tur\w*\s+(?:encore\s+)?une\s+partie", re.I)
CLOSE = re.compile(r"\bclose\s+now\b|cl[oô]tur\w*\s+(?:toute\s+)?(?:la|ma|les|vos|toute)\s+positions?|"
                   r"ferme[rz]?\s+(?:toute\s+)?(?:la|les|vos|ta|ma)\s+positions?|^\W*cl[oô]ture\b", re.I | re.M)
# Consignes de gestion d'un canal suivi ("manage"), d'après les messages de RTZ ACADEMY (10/11/2026)
G_OPTION = re.compile(r"pouvez|h[ée]sit|si\s+(?:les|vos)\s+profits|veut\s+dire|convien|quand\s+je\s+dis|tuto|"
                      r"comment\s+cl", re.I)
G_OUT = re.compile(r"\bout\b|\bon\s+cl[oô]ture\b|annul|cl[oô]tur\w*\s+(?:au\s+be\b|manuellement|le\s+tout|tout\b)|"
                   r"\bclose\s+now\b", re.I)
G_PART = re.compile(r"(?:cl[oô]tur|s[ée]curis)\w*\s+(\d{1,3})\s*%", re.I)
G_BE = re.compile(r"\bbe\b(?!\s*hit)|break\s*even|s[ée]curis|stop\s*loss\s+au\s+point\s+d.entr", re.I)
G_TP = re.compile(r"(?:modifi\w*|d[ée]place\w*)\s+(?:le\s+|votre\s+)?tp\s*(\d)?\s*(?:[aà]\s+)?:?\s*" + NUM +
                  r"|\btp\s*(\d)?\s+modifi\w*\s+(?:[aà]\s+)?" + NUM, re.I)
G_SL = re.compile(r"(?:modifi\w*|d[ée]place\w*)\s+(?:le\s+|votre\s+)?(?:sl|stop(?:\s*loss)?)\s*(?:[aà]\s+)?:?\s*" + NUM +
                  r"|\b(?:sl|stop)\s+modifi\w*\s+(?:[aà]\s+)?" + NUM, re.I)
DEFAULTS = {"command": r"E:\TradingBot\venv\Scripts\python.exe -m trading_bot.tg_parse",
            "listen": r"E:\TradingBot\venv\Scripts\python.exe -m trading_bot.tg_listen run",
            "dir": r"E:\TradingBot\bot", "agent_dir": r"E:\TradingBot\agent\agent", "session_dir": str(SESSION_DIR)}


def _num(x: str) -> float:
    return float(x.replace(",", "."))


def parse(text: str, reply_to: int | None, opened: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Message au format BENAGOLD → action (même forme que tg_parse), ou None si ce n'est pas un trade."""
    m, stop = MARKET.search(text), STOP.search(text)
    if m and stop:
        if re.search(r"modifi", text, re.I):
            return None                        # « TRADE MODIFIER » de RTZ : pas un nouveau trade
        e = ENTRY.search(text)
        zone = sorted(_num(x) for x in e.groups() if x) if e else []
        sens = "achat" if m.group(1).lower() in ("buy", "achat") else "vente"
        if any(o["sens"] == sens and abs(float(o["stop"]) - _num(stop.group(1))) < 0.01 for o in opened):
            return None                        # même signal renvoyé (RTZ le renvoie parfois 45 min après)
        return {"type": "ouverture", "marche": "gold", "sens": sens, "entree": zone[0] if len(zone) == 1 else None, "zone": zone if len(zone) == 2 else None,
                "stop": _num(stop.group(1)), "objectifs": [_num(x) for x in TARGET.findall(text)], "signal": None,
                "raison": "format BENAGOLD"}
    partial = bool(PARTIAL.search(text))
    kind = "stop" if SECURE.search(text) else "fermer" if partial or CLOSE.search(text) else None
    if kind is None or not opened:
        return None
    target = next((o for o in opened if o["msg_id"] == reply_to), None) or opened[-1]
    return {"type": kind, "marche": None, "sens": None, "entree": None,
            "stop": target["entree"] if kind == "stop" else None, "objectifs": [], "signal": target["id"],
            "partiel": partial and kind == "fermer",
            "raison": "sécurisez : stop au prix d'entrée" if kind == "stop" else
            "clôture partielle" if partial else "fermeture demandée"}


def gestion(text: str) -> dict[str, Any] | None:
    """Consigne de gestion d'un canal suivi → {"close": part à fermer (1 = tout) ou None, "be": bool, "stop": prix ou
    None, "tp": {numéro de l'objectif (0 = tous): prix}} ; None si le message ne demande rien."""
    if G_OPTION.search(text):
        return None
    if G_OUT.search(text):
        return {"close": 1.0, "be": False, "stop": None, "tp": {}}
    part = G_PART.search(text)
    close = min(1.0, int(part.group(1)) / 100) if part else None
    sl = G_SL.search(text)
    stop = _num(sl.group(1) or sl.group(2)) if sl else None
    tp = {}
    for a, b, c, d in G_TP.findall(text):
        tp[int(a or c or 0)] = _num(b or d)
    be = bool(G_BE.search(text)) and stop is None
    if close is None and not be and stop is None and not tp:
        return None
    return {"close": close, "be": be, "stop": stop, "tp": tp}


def levels(text: str) -> dict[str, Any] | None:
    """Niveaux d'un message de signal (pour un signal corrigé par le canal) : sens, zone, stop, objectifs."""
    m, stop = MARKET.search(text), STOP.search(text)
    if not (m and stop):
        return None
    e = ENTRY.search(text)
    return {"buy": m.group(1).lower() in ("buy", "achat"), "zone": sorted(_num(x) for x in e.groups() if x) if e else [],
            "stop": _num(stop.group(1)), "targets": [_num(x) for x in TARGET.findall(text)]}


class TgCopier:
    def __init__(self, mt5, root: Path, clock: Callable[[], float], relay=None, cfg: dict[str, Any] | None = None,
                 spawn: Callable[..., Any] = subprocess.Popen, decider=None):
        self.mt5, self.root, self.clock, self.relay, self.spawn = mt5, Path(root), clock, relay, spawn
        # 09/11/2026 : l'agent IA décide de chaque signal du canal avant l'ordre (decideur.py)
        self.decider = decider
        self.waiting: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
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
        if self.waiting:
            said = self._decisions() or said
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
            before = self.state["texts"].get(key)
            reply = self.state["texts"].get(f"{m['chat_id']}:{m.get('reply_to')}") if m.get("reply_to") else None
            self.state["texts"][key] = m["text"][:1500]
            self._save()
            try:                               # message modifié : son âge compte depuis la modification
                got = int(f.name.split("_")[0]) / 1000 if m.get("edited") else float(m.get("date") or 0)
            except ValueError:
                got = float(m.get("date") or 0)
            if self.clock() - got > MAX_AGE:
                continue
            if not self.cfg.get("claude"):
                manage = self._in(m, "manage")
                if m.get("edited"):
                    if manage:                 # signal corrigé par le canal (« TRADE MODIFIER »)
                        said = self._edited(m, before)
                        if said:
                            return said
                    continue                   # un message modifié (« TP1 ✅ » ajouté…) ne rouvre rien
                opened = self._opened(m["chat_id"])
                d = parse(m["text"], m.get("reply_to"), opened)
                if manage and (d is None or d["type"] != "ouverture"):
                    g = gestion(m["text"])
                    sid = self._target(m, opened) if g else None
                    if sid is None:
                        continue
                    self._journal({"canal": m.get("chat"), "action": "gestion",
                                   "detail": json.dumps({"signal": sid, **g}, ensure_ascii=False)})
                    self._manage(sid, g)
                    return f"copie Telegram : gestion ({m.get('chat')} n°{m['msg_id']})"
                if d is None or (d["type"] != "ouverture" and self._in(m, "opens_only")):
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
                if self.decider is not None and self.decider.available() and not self._in(data, "no_agent"):
                    self._consult(d, data)
                else:
                    self._open(d, data)
            elif d.get("type") == "stop":
                self._move(d, data)
            elif d.get("type") == "fermer":
                self._close_signal(d["signal"], "demandé par le canal", partial=bool(d.get("partiel")))
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

    @staticmethod
    def _norm(x: Any) -> str:
        return "".join(ch for ch in str(x).lower() if ch.isalnum())

    def _in(self, data: dict[str, Any], key: str) -> bool:
        return self._norm(data.get("chat", "")) in {self._norm(c) for c in self.cfg.get(key) or []}

    def _tp_max(self, data: dict[str, Any]) -> int:
        per = {self._norm(k): int(v) for k, v in (self.cfg.get("tp_max") or {}).items()}
        return min(MAX_SPLIT, per.get(self._norm(data.get("chat", "")), MAX_SPLIT))

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
        limit = (now_px - entry) * s > CHASE * dist or bool(d.get("force_limit"))
        px = entry if limit else now_px
        targets = [float(x) for x in d.get("objectifs") or [] if (float(x) - px) * s > lvl][:self._tp_max(data)]
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
        if not d.get("agent") and not self._in(data, "no_agent"):   # l'agent a déjà décidé avant l'ordre
            self._review(sid, sig)

    # ------------------------------------------------------------------ décision de l'agent IA (09/11/2026)
    def _consult(self, d: dict[str, Any], data: dict[str, Any]) -> None:
        key = f"{data['chat_id']}:{data['msg_id']}"
        if key in self.waiting or any(s["key"] == key for s in self.state["signals"].values()):
            return
        if len(self.state["signals"]) >= MAX_OPEN:
            return self._refuse(data, d, f"déjà {MAX_OPEN} signaux ouverts")
        why = demo_rules.check(self.mt5, MAGIC)
        if why:
            return self._refuse(data, d, f"règle d'arrêt ({why})")
        buy = d["sens"] == "achat"
        sym = SYMBOLS[d["marche"]]
        self.mt5.symbol_select(sym, True)
        tick = self.mt5.symbol_info_tick(sym)
        if tick is None or not tick.bid:
            return self._refuse(data, d, "marché fermé")
        now_px = tick.ask if buy else tick.bid
        zone = d.get("zone")
        entry = min(max(now_px, zone[0]), zone[1]) if zone else float(d["entree"]) if d.get("entree") is not None \
            else now_px
        targets = [float(x) for x in d.get("objectifs") or []]
        get = getattr(self.relay, "_candles", None)
        candles = (lambda tf, n: get(sym, tf, n, None) or []) if get else (lambda tf, n: [])  # noqa: E731
        now = self.clock()
        iso = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
        tps = " / ".join(f"{x:g}" for x in targets)
        info = {"id": f"tg-{abs(data['chat_id'])}-{data['msg_id']}", "strategie": "copie_telegram",
                "asset": d["marche"], "asset_label": LABELS.get(d["marche"], d["marche"]),
                "direction": "long" if buy else "short", "entry": entry, "stop_loss": float(d["stop"]),
                "take_profit": targets[0] if targets else None, "objectifs": targets,
                "sortie": f"signal du canal {data.get('chat')} : un ordre par objectif ({tps or 'aucun'}), "
                          f"fermé au bout de {MAX_HOLD // 3600} h au plus",
                "message_du_canal": str(data.get("text", ""))[:1500],
                "created_at": iso(float(data.get("date") or now)), "maintenant": iso(now),
                "bid": tick.bid, "ask": tick.ask, "attente_max_min": dc.WAIT_MAX // 60,
                "telegram_message_ids": {}, "ticket_mt5": None,
                "candles_5m": candles("TIMEFRAME_M5", 288), "candles_1h": candles("TIMEFRAME_H1", 48),
                "candles_1d": candles("TIMEFRAME_D1", 20)}
        if not self.decider.ask(f"tg:{key}", info):
            return self._refuse(data, d, "agent IA : il n'a pas pu être lancé")
        self.waiting[key] = (d, data)

    def _decisions(self) -> str:
        said = ""
        for key in list(self.waiting):
            dec = self.decider.poll(f"tg:{key}")
            if dec is None:
                continue
            d, data = self.waiting.pop(key)
            self._journal({"canal": data.get("chat"), "action": f"agent : {dec['action']}",
                           "detail": json.dumps(dec, ensure_ascii=False)})
            said = f"copie Telegram : agent {dec['action']} ({data.get('chat')} n°{data['msg_id']})"
            if dec["action"] not in ("prendre", "attendre"):
                self._refuse(data, d, f"agent IA {dc.line(dec)[len('Agent IA : '):]}")
                continue
            buy = d["sens"] == "achat"
            sg = 1 if buy else -1
            sym = SYMBOLS[d["marche"]]
            tick, info = self.mt5.symbol_info_tick(sym), self.mt5.symbol_info(sym)
            if tick is None or info is None or not tick.bid:
                self._refuse(data, d, "marché fermé après la décision de l'agent")
                continue
            now_px = tick.ask if buy else tick.bid
            gap = getattr(info, "trade_stops_level", 0) * getattr(info, "point", 0.01) + abs(tick.ask - tick.bid)
            stop = float(d["stop"])
            p = dc.plan(dec, buy, now_px, abs(now_px - stop) or gap, None, gap)
            if p["action"] == "refuser":
                self._refuse(data, d, f"agent IA : {'; '.join(p['notes'])}")
                continue
            ref = p["entry"] or now_px
            d2 = dict(d, agent=dict(dec, notes=p["notes"]))
            if p["entry"]:
                d2.update(zone=None, entree=p["entry"], force_limit=True)
            if dec.get("stop") is not None and not any(n.startswith("SL") for n in p["notes"]):
                d2["stop"] = ref - sg * p["stop"]
            if p["target"]:
                obj = ref + sg * p["target"]
                d2["objectifs"] = [x for x in d.get("objectifs") or [] if (obj - float(x)) * sg > 0] + [obj]
            self._open(d2, data)
        return said

    def _review(self, sid: str, s: dict[str, Any]) -> None:
        """Avis de l'agent IA sous l'annonce, comme pour les signaux du bot (demandé par Yanisse le 23/10/2026)."""
        if self.relay is None or not s["msg"]:
            return
        tps = " / ".join(f"{t:g}" for t in s["targets"])
        self.relay._agent(f"tg:copie_telegram:{sid}",
                          {"asset": s["market"], "direction": "long" if s["buy"] else "short", "entry": s["entry"],
                           "created": int(s["placed"])},
                          s["sym"], s["stop"], s["targets"][0] if s["targets"] else None, s["msg"],
                          sortie=f"signal du canal {s['chat']} : un ordre par objectif ({tps or 'aucun'}), "
                                 f"« sécurisez » = stop au prix d'entrée, fermé au bout de {MAX_HOLD // 3600} h au plus",
                          ticket=s["tickets"][0] if s["tickets"] else None)

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
        if d.get("agent"):
            lines.append(msg.esc(dc.line(d["agent"], d["agent"].get("notes"))))
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

    def _move(self, d: dict[str, Any], data: dict[str, Any], why: str = "demandé par le canal") -> None:
        s = self.state["signals"].get(d["signal"])
        if not s:
            return
        new = round(float(d["stop"]), s["digits"])
        tick = self.mt5.symbol_info_tick(s["sym"])
        sgn = 1 if s["buy"] else -1
        if tick is None or ((tick.bid if s["buy"] else tick.ask) - new) * sgn <= 0:
            self._post(f"📡 Stop à {msg.num(new, s['digits'])} ({why}) <b>pas appliqué</b> : le prix "
                       f"est déjà de l'autre côté.", reply=s["msg"])
            return
        pos, orders = self._live(s)
        m = self.mt5
        ok = (getattr(m, "TRADE_RETCODE_DONE", 10009), getattr(m, "TRADE_RETCODE_PLACED", 10008),
              getattr(m, "TRADE_RETCODE_NO_CHANGES", 10025))
        refused = []
        for p in pos:
            res = m.order_send({"action": m.TRADE_ACTION_SLTP, "symbol": s["sym"], "position": p.ticket, "sl": new,
                                "tp": getattr(p, "tp", 0.0)})
            if getattr(res, "retcode", None) not in ok:
                refused.append(getattr(res, "retcode", None))
        for o in orders:
            res = m.order_send({"action": m.TRADE_ACTION_MODIFY, "order": o.ticket, "price": o.price_open, "sl": new,
                                "tp": getattr(o, "tp", 0.0)})
            if getattr(res, "retcode", None) not in ok:
                refused.append(getattr(res, "retcode", None))
        total = len(pos) + len(orders)
        codes = ", ".join(str(c) for c in sorted(set(refused), key=str))
        if total and len(refused) == total:   # rien n'a été accepté par MT5 : on ne l'annonce pas comme fait
            log.warning("copie Telegram : stop %s refusé par MT5 (code %s)", new, codes)
            self._post(f"📡 Stop à {msg.num(new, s['digits'])} ({why}) <b>refusé par MT5</b> "
                       f"(code {codes}) : l'ancien stop reste en place.", reply=s["msg"])
            return
        be = abs(new - s["entry"]) < 10 ** -s["digits"] * 5
        s["stop"] = new
        self._save()
        part = f" ({total - len(refused)}/{total} ordres, refus MT5 code {codes})" if refused else ""
        self._post(f"📡 Stop déplacé à {msg.code_price(new, s['digits'])}{' (BE)' if be else ''}, {why}{part}.",
                   reply=s["msg"])

    # ------------------------------------------------------------------ consignes d'un canal suivi (10/11/2026)
    def _target(self, m: dict[str, Any], opened: list[dict[str, Any]]) -> str | None:
        """Signal visé : celui auquel le message répond (rien s'il n'a pas été copié), sinon le dernier copié."""
        if m.get("reply_to"):
            return next((o["id"] for o in opened if o["msg_id"] == m["reply_to"]), None)
        text = str(m.get("text", "")).strip()          # sans réponse : seulement une consigne courte, sur un signal
        if not opened or len(text) > 80 or "\n" in text:   # récent (les bilans et tutos du canal en parlent aussi)
            return None
        s = self.state["signals"].get(opened[-1]["id"]) or {}
        return opened[-1]["id"] if self.clock() - float(s.get("placed") or 0) <= 3 * 3600 else None

    def _manage(self, sid: str, g: dict[str, Any], why: str = "demandé par le canal") -> None:
        s = self.state["signals"].get(sid)
        if not s:
            return
        if g.get("close") is not None and g["close"] >= 1:
            return self._close_signal(sid, why)
        if g.get("close") and not s["pending"]:
            self._close_part(s, g["close"], why)
        if g.get("stop") is not None:
            self._move({"signal": sid, "stop": g["stop"]}, {}, why)
        elif g.get("be") and not s["pending"]:
            self._move({"signal": sid, "stop": s["entry"]}, {}, why)
        for n, px in (g.get("tp") or {}).items():
            self._set_tp(s, int(n), float(px), why)

    def _close_part(self, s: dict[str, Any], frac: float, why: str) -> None:
        """Ferme `frac` du lot de chaque position (arrondi au pas du courtier ; tout si le reste serait trop petit)."""
        pos, _ = self._live(s)
        m = self.mt5
        info = m.symbol_info(s["sym"])
        step = getattr(info, "volume_step", 0.01) or 0.01
        vmin = getattr(info, "volume_min", 0.01) or 0.01
        tick = m.symbol_info_tick(s["sym"])
        done = 0.0
        for p in pos:
            vol = round(int(p.volume * frac / step + 0.5 + 1e-9) * step, 2)     # au plus proche, moitié vers le haut
            if vol <= 0:
                continue
            if p.volume - vol < vmin - 1e-9:
                vol = p.volume
            long = p.type == m.POSITION_TYPE_BUY
            res = m.order_send({"action": m.TRADE_ACTION_DEAL, "symbol": s["sym"], "volume": vol, "position": p.ticket,
                                "type": m.ORDER_TYPE_SELL if long else m.ORDER_TYPE_BUY,
                                "price": tick.bid if long else tick.ask, "deviation": 30, "magic": MAGIC,
                                "comment": "tg part", "type_time": m.ORDER_TIME_GTC, "type_filling": self._filling(info)})
            if getattr(res, "retcode", None) == m.TRADE_RETCODE_DONE:
                done += vol
        if done:
            total = sum(p.volume for p in pos)
            self._post(f"📡 Clôture de {frac:.0%} ({why}) : {msg.num(done, 2)} lot sur {msg.num(total, 2)} fermé"
                       f"{' (le lot ne se coupe pas plus finement)' if done >= total - 1e-9 else ''}.", reply=s["msg"])

    def _set_tp(self, s: dict[str, Any], n: int, px: float, why: str) -> None:
        """Nouvel objectif pour l'ordre n° n (1 = TP1 ; 0 = tous les ordres)."""
        m = self.mt5
        pos, orders = self._live(s)
        idx = {t: i for i, t in enumerate(s["tickets"])}
        mine = [x for x in pos + orders if n == 0 or idx.get(x.ticket) == n - 1]
        if not mine:
            return
        info, tick = m.symbol_info(s["sym"]), m.symbol_info_tick(s["sym"])
        sg = 1 if s["buy"] else -1
        lvl = getattr(info, "trade_stops_level", 0) * getattr(info, "point", 0.01)
        new = round(px, s["digits"])
        ok = (getattr(m, "TRADE_RETCODE_DONE", 10009), getattr(m, "TRADE_RETCODE_PLACED", 10008),
              getattr(m, "TRADE_RETCODE_NO_CHANGES", 10025))
        done = 0
        for x in mine:
            ref = (tick.bid if s["buy"] else tick.ask) if x in pos else x.price_open
            if tick is None or (new - ref) * sg <= lvl:
                continue
            if x in pos:
                req = {"action": m.TRADE_ACTION_SLTP, "symbol": s["sym"], "position": x.ticket,
                       "sl": getattr(x, "sl", s["stop"]) or s["stop"], "tp": new}
            else:
                req = {"action": m.TRADE_ACTION_MODIFY, "order": x.ticket, "price": x.price_open,
                       "sl": getattr(x, "sl", s["stop"]) or s["stop"], "tp": new}
            if getattr(m.order_send(req), "retcode", None) in ok:
                done += 1
                i = idx.get(x.ticket)
                if i is not None and i < len(s["targets"]):
                    s["targets"][i] = new
        self._save()
        name = "TP" if n == 0 else f"TP{n}"
        if done:
            self._post(f"🎯 {name} déplacé à {msg.code_price(new, s['digits'])}, {why}.", reply=s["msg"])
        else:
            self._post(f"🎯 {name} à {msg.num(new, s['digits'])} ({why}) <b>pas appliqué</b> : le prix est déjà "
                       f"au-delà ou MT5 l'a refusé.", reply=s["msg"])

    def _edited(self, m: dict[str, Any], before: str | None) -> str:
        """Le canal a corrigé le message d'un signal copié : nouveau stop, nouveaux objectifs, nouvelle entrée. Seuls
        les niveaux qui ont changé depuis la version précédente du message comptent (un « ✅ » ajouté après une
        consigne « MODIFIER TP1 » ne doit pas remettre l'ancien objectif)."""
        sid = f"{abs(m['chat_id'])}-{m['msg_id']}"
        s = self.state["signals"].get(sid)
        lv = levels(m["text"]) if s else None
        if not s or not lv or lv["buy"] != s["buy"]:
            return ""
        old = levels(before or "")
        if old and old["buy"] == lv["buy"]:
            same = lambda a, b: abs(a - b) < 10 ** -s["digits"]  # noqa: E731
            if same(old["stop"], lv["stop"]):
                lv["stop"] = s["stop"]
            lv["targets"] = [s["targets"][i] if i < len(old["targets"]) and i < len(s["targets"])
                             and same(old["targets"][i], t) else t for i, t in enumerate(lv["targets"])]
            if old["zone"] == lv["zone"]:
                lv["zone"] = []
        why, dg, did = "message du signal corrigé par le canal", s["digits"], False
        if s["pending"] and lv["zone"] and not lv["zone"][0] - 1e-9 <= s["entry"] <= lv["zone"][-1] + 1e-9:
            new = round(lv["zone"][-1] if s["buy"] else lv["zone"][0], dg)   # bord de zone le plus proche du prix
            _, orders = self._live(s)
            for o in orders:
                self.mt5.order_send({"action": self.mt5.TRADE_ACTION_MODIFY, "order": o.ticket, "price": new,
                                     "sl": round(lv["stop"], dg), "tp": getattr(o, "tp", 0.0)})
            if orders:
                s["entry"], did = new, True
                self._post(f"📡 Entrée de l'ordre en attente déplacée à {msg.code_price(new, dg)}, {why}.",
                           reply=s["msg"])
        if abs(lv["stop"] - s["stop"]) >= 10 ** -dg:
            self._move({"signal": sid, "stop": lv["stop"]}, {}, why)
            did = True
        for i, t in enumerate(lv["targets"][:len(s["targets"])]):
            if abs(t - s["targets"][i]) >= 10 ** -dg:
                self._set_tp(s, i + 1, t, why)
                did = True
        self._save()
        return f"copie Telegram : signal corrigé ({m.get('chat')} n°{m['msg_id']})" if did else ""

    def _close_signal(self, sid: str, why: str, partial: bool = False) -> None:
        s = self.state["signals"].get(sid)
        if not s:
            return
        pos, orders = self._live(s)
        m = self.mt5
        if partial:                       # un seul ordre : celui dont le TP est le plus proche de l'entrée
            near = lambda x: abs((getattr(x, "tp", 0.0) or 1e12) - s["entry"])  # noqa: E731
            first = min(pos + orders, key=near, default=None)
            pos, orders = ([first], []) if first in pos else ([], [first] if first is not None else [])
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
        if not partial:
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
