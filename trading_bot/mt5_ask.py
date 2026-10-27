"""Questions à l'agent IA depuis Telegram, quand le PC est allumé (demandé par Yanisse le 27/10/2026).

`/avis ton avis sur le Nasdaq, je garde mes trades ou je sécurise ?` : le pont lit le message, prépare le marché du moment,
les positions ouvertes du démo et la question, lance l'agent (trading_bot/ask.py) et poste sa réponse sur Telegram.
Un avis seulement : aucun ordre, aucun stop déplacé, aucun trade ouvert ici.

Comme /hugo, les messages sont lus sans être acquittés (getUpdates sans offset) : le bot de GitHub continue de recevoir
les autres commandes et ignore /avis.
"""
from __future__ import annotations

import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from . import messages as msg
from .mt5_copy import SYMBOLS
from .mt5_hugo import FRESH, POLL, _updates
from .mt5_hunt import Hunter
from .mt5_local import server_offset
from .notify import chat_key, telegram_chat_ids

log = logging.getLogger("mt5_ask")

COMMANDS = ("/avis", "/question", "/ask")
LABELS = {"gold": "Or (XAU/USD)", "nasdaq": "Nasdaq 100", "bitcoin": "Bitcoin", "sp500": "S&P 500",
          "ethereum": "Ethereum"}
WORDS = {"nasdaq": ("nasdaq", "nq", "nas100", "us100"), "gold": ("gold", "xau", "l'or", " or ", "l or"),
         "bitcoin": ("bitcoin", "btc"), "sp500": ("s&p", "sp500", "spx"), "ethereum": ("ethereum", "eth ")}
ORIGINS = {0: "lui (à la main)", 200001: "la copie des signaux", 300001: "la copie du canal Telegram",
           777001: "le poste de l'assistant", 777002: "l'agent IA (chasse)", 777003: "l'agent IA (méthode Hugo)"}
ICONS = {"garder": "✅ Garder", "securiser": "🛡 Sécuriser", "fermer": "🚪 Fermer", "aucune_position": "ℹ️ Rien d'ouvert",
         "autre": "💬"}


def parse(text: str) -> str | None:
    """Question après /avis (None : ce n'est pas la commande ; chaîne vide : commande sans question)."""
    parts = text.strip().split(None, 1)
    if not parts or parts[0].lower().split("@", 1)[0] not in COMMANDS:
        return None
    return parts[1].strip() if len(parts) > 1 else ""


def asset_of(question: str, positions: list[dict[str, Any]]) -> str:
    """Marché visé par la question ; sinon celui de la première position ouverte ; sinon le Nasdaq."""
    q = f" {question.lower()} "
    for asset, words in WORDS.items():
        if any(w in q for w in words):
            return asset
    return positions[0]["asset"] if positions else "nasdaq"


class Asker(Hunter):
    """Réutilise la lecture des bougies et le lancement de l'agent du pont ; ne chasse aucun trade."""
    MAGIC = 777004
    NAME = "question"
    ASSETS = {a: (LABELS[a], (), 1.0) for a in SYMBOLS if a in LABELS}
    NEWS = False
    TAG = "Question à l'agent IA"
    COMMENT = "question IA"
    FRAMES = (("candles_5m", "TIMEFRAME_M5", 288), ("candles_15m", "TIMEFRAME_M15", 96),
              ("candles_1h", "TIMEFRAME_H1", 72), ("candles_1d", "TIMEFRAME_D1", 30))
    DEFAULTS = {"command": r"E:\TradingBot\venv\Scripts\python.exe -m trading_bot.ask", "dir": r"E:\TradingBot\bot",
                "agent_dir": r"E:\TradingBot\agent\agent"}

    def __init__(self, mt5, root: Path, clock: Callable[[], float], relay=None, cfg: dict[str, Any] | None = None,
                 spawn=None, updates: Callable[[str], list[dict[str, Any]]] = _updates):
        kw = {"spawn": spawn} if spawn is not None else {}
        super().__init__(mt5, root, clock, relay=relay, cfg=cfg, **kw)
        self.updates = updates
        self.last_poll = 0.0
        self.queue: list[str] = []

    def ready(self) -> bool:
        return (Path(self.cfg["dir"]) / "trading_bot" / "ask.py").exists() and \
            (Path(self.cfg["agent_dir"]) / "ia.py").exists()

    # ------------------------------------------------------------------ passage
    def step(self) -> str:
        self._reap()
        said = self.poll()
        if self.proc is None and self.queue:
            return self._ask(self.clock(), self.queue.pop(0)) or said
        return said

    def poll(self) -> str:
        now = self.clock()
        if self.relay is None or not self.relay.enabled() or now - self.last_poll < POLL:
            return ""
        self.last_poll = now
        allowed = {chat_key(c) for c in telegram_chat_ids()}
        seen = int(self.state.get("tg_seen") or 0)
        got = ""
        for u in self.updates(self.relay.token):
            uid = int(u.get("update_id") or 0)
            m = u.get("message") or {}
            if uid <= seen:
                continue
            seen = max(seen, uid)
            question = parse(str(m.get("text") or ""))
            if question is None:
                continue
            if chat_key(str((m.get("chat") or {}).get("id"))) not in allowed or now - float(m.get("date") or 0) > FRESH:
                continue
            if not question:
                self.relay._post("🔎 Écris ta question après la commande, par exemple : "
                                 "<code>/avis ton avis sur le Nasdaq, je garde mes trades ou je sécurise ?</code>")
                continue
            if len(self.queue) >= 3:
                self.relay._post("🔎 Trois questions attendent déjà : je réponds d'abord à celles-là.")
                continue
            self.queue.append(question[:500])
            got = "question reçue"
        self.state["tg_seen"] = seen
        self._save()
        return got

    def positions(self, off: int) -> list[dict[str, Any]]:
        back = {v: k for k, v in SYMBOLS.items()}
        out = []
        for p in self.mt5.positions_get() or []:
            asset = back.get(p.symbol)
            out.append({"asset": asset or p.symbol, "marche": LABELS.get(asset, p.symbol),
                        "sens": "achat" if p.type == 0 else "vente", "lot": p.volume, "entree": p.price_open,
                        "stop": p.sl or None, "objectif": p.tp or None, "profit": round(p.profit + p.swap, 2),
                        "origine": ORIGINS.get(p.magic, f"magic {p.magic}")})
        return out

    def _ask(self, now: float, question: str) -> str:
        if not self.ready():
            self.relay._post("🔎 L'agent n'est pas installé sur le PC, je ne peux pas répondre.")
            return "question : agent absent"
        acc = self.mt5.account_info()
        if acc is None or acc.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
            self.relay._post("🔎 MT5 n'est pas sur le compte démo, je ne réponds pas.")
            return "question : pas de démo"
        pos = self.positions(0)
        asset = asset_of(question, pos)
        sym = SYMBOLS[asset]
        self.mt5.symbol_select(sym, True)
        off = server_offset(self.mt5, sym, now)
        tick = self.mt5.symbol_info_tick(sym)
        if off is None or tick is None:
            self.relay._post(f"🔎 Le marché {LABELS.get(asset, asset)} est fermé : je n'ai pas de prix pour répondre.")
            return f"question : marché fermé ({asset})"
        evs = self.events()
        data = {"id": f"question-{asset}-{int(now)}", "asset": asset, "asset_label": LABELS.get(asset, asset),
                "now": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)), "question": question,
                "bid": tick.bid, "ask": tick.ask, "positions": pos,
                "annonces": [{"heure": e["at"], "titre": e["name"], "impact": e.get("impact")} for e in evs
                             if str(e.get("name", "")).startswith("USD")
                             and -7200 <= datetime.fromisoformat(e["at"]).timestamp() - now <= 6 * 3600]}
        for k, tf, n in self.FRAMES:
            data[k] = self._candles(sym, tf, n, off)
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / f"{data['id']}.json"
        path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        out = open(self.folder / f"{data['id']}.log", "w", encoding="utf-8")
        proc = self.spawn(self.cfg["command"].split() + ["--marche", str(path)], cwd=self.cfg["dir"], stdout=out,
                          stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.proc = (proc, now, data["id"], self.folder / f"{data['id']}.log", data)
        self.relay._post(f"🔎 Je regarde {msg.esc(LABELS.get(asset, asset))} et tes positions, réponse dans une minute.")
        log.info("question : agent réveillé (%s)", asset)
        return f"question : agent réveillé ({asset})"

    def _decide(self, a: dict[str, Any], data: dict[str, Any]) -> None:
        if self.relay is None or not self.relay.enabled():
            return
        lines = [f"<b>{ICONS.get(a.get('conseil'), '💬')} · {msg.esc(data['asset_label'])}</b> · avis de l'agent IA",
                 "", msg.esc(str(a.get("reponse", ""))), "",
                 "<i>Un avis, pas un ordre : rien n'a été déplacé ni fermé. Démo seulement.</i>"]
        self.relay._post("\n".join(lines))
        log.info("question : réponse envoyée (%s)", a.get("conseil"))
