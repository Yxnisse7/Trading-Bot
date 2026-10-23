"""Écoute de canaux Telegram avec le compte de Yanisse, sur son PC (demandé par Yanisse le 23/10/2026).

Le bot Telegram du projet ne peut pas lire les canaux d'un autre signaleur : il faut le compte de Yanisse lui-même
(bibliothèque Telethon). Ce programme ne fait qu'écouter : chaque nouveau message (ou message modifié) des canaux
choisis est écrit dans journal/tg_inbox/ ; le pont MT5 (mt5_tgcopy.py) le lit, le fait comprendre par Claude et le
copie sur le démo.

Clés : api_id et api_hash de https://my.telegram.org, tapés par Yanisse sur son PC dans les variables Windows
TG_API_ID et TG_API_HASH (jamais dans un fichier du dépôt ni dans un message). La session Telegram (preuve de
connexion) est gardée dans E:\\TradingBot\\telegram\\, hors du dépôt.

    python -m trading_bot.tg_listen login     → première connexion (numéro + code reçu sur Telegram)
    python -m trading_bot.tg_listen canaux    → liste des canaux et groupes du compte (nom et numéro)
    python -m trading_bot.tg_listen run       → écoute (lancé par le pont)
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

SESSION_DIR = Path(r"E:\TradingBot\telegram")
ROOT = Path(r"E:\TradingBot")


def inbox(root: Path) -> Path:
    return root / "journal" / "tg_inbox"


def config(root: Path) -> dict[str, Any]:
    try:
        return json.loads((root / "config.json").read_text(encoding="utf-8")).get("tg_copy") or {}
    except (OSError, ValueError):
        return {}


def wanted(chat_id: int, title: str, channels: list[Any]) -> bool:
    """Le canal fait partie de la liste : numéro exact, ou nom égal au titre sans tenir compte des majuscules, des
    espaces ni des émojis (« BENAGOLD » ↔ « BENAGOLD 🫀 »)."""
    def norm(x: Any) -> str:
        return "".join(ch for ch in str(x).lower() if ch.isalnum())
    ids = {str(c).strip() for c in channels}
    return str(chat_id) in ids or str(abs(chat_id)) in ids or norm(title) in {norm(c) for c in channels}


def record(root: Path, chat_id: int, title: str, msg_id: int, text: str, reply_to: int | None, date: float,
           edited: bool) -> Path:
    folder = inbox(root)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{int(time.time() * 1000)}_{abs(chat_id)}_{msg_id}{'_e' if edited else ''}.json"
    tmp = folder / (name + ".tmp")
    tmp.write_text(json.dumps({"chat_id": chat_id, "chat": title, "msg_id": msg_id, "reply_to": reply_to,
                               "date": date, "text": text, "edited": edited}, ensure_ascii=False), encoding="utf-8")
    tmp.replace(folder / name)
    return folder / name


def client():
    from telethon import TelegramClient
    api_id, api_hash = os.environ.get("TG_API_ID"), os.environ.get("TG_API_HASH")
    if not api_id or not api_hash:
        raise SystemExit("TG_API_ID et TG_API_HASH manquent (variables Windows, voir l'explication de Claude).")
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return TelegramClient(str(SESSION_DIR / "yanisse"), int(api_id), api_hash)


def login() -> None:
    c = client()
    c.start()                                   # demande le numéro, puis le code reçu sur Telegram (et le mot de passe)
    me = c.loop.run_until_complete(c.get_me())
    print(f"Connecté : {me.first_name}. Tu peux fermer cette fenêtre.")
    c.disconnect()


def canaux() -> None:
    c = client()
    c.start()

    async def go():
        async for d in c.iter_dialogs():
            if d.is_channel or d.is_group:
                print(f"{d.id:>16}  {d.name}")
    c.loop.run_until_complete(go())
    c.disconnect()


def run(root: Path = ROOT) -> None:
    from telethon import events
    channels = config(root).get("channels") or []
    if not channels:
        raise SystemExit("aucun canal dans config.json (tg_copy.channels)")
    c = client()
    c.start()

    async def on(event, edited: bool = False):
        chat = await event.get_chat()
        title = getattr(chat, "title", None) or getattr(chat, "first_name", "") or ""
        if not wanted(event.chat_id, title, channels):
            return
        m = event.message
        if not (m.message or "").strip():
            return
        reply = m.reply_to.reply_to_msg_id if m.reply_to else None
        record(root, event.chat_id, title, m.id, m.message, reply, m.date.timestamp(), edited)
        print(f"{title} #{m.id}{' (modifié)' if edited else ''}", flush=True)

    c.add_event_handler(on, events.NewMessage())
    c.add_event_handler(lambda e: on(e, True), events.MessageEdited())
    print(f"écoute de {len(channels)} canal(aux)", flush=True)
    c.run_until_disconnected()


if __name__ == "__main__":
    cmd = (sys.argv[1:2] or ["run"])[0]
    {"login": login, "canaux": canaux, "run": run}[cmd]()
