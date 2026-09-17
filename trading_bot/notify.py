"""Notifications gratuites : Telegram (bot), Discord (webhook), console + journal local."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import requests

from .config import DATA_DIR

log = logging.getLogger(__name__)


def telegram_chat_ids() -> list[str]:
    """Identifiants de chat autorisés (TELEGRAM_CHAT_ID, plusieurs séparés par des virgules)."""
    raw = os.environ.get("TELEGRAM_CHAT_ID") or ""
    return [c.strip() for c in raw.replace(";", ",").split(",") if c.strip()]


def notify(text: str, *, title: str | None = None, chat_id: str | None = None) -> None:
    """Envoie un message. `chat_id` : cible un seul chat Telegram (réponse à une commande) ;
    sinon tous les chats configurés + Discord."""
    body = f"{title}\n{text}" if title else text
    print(body, flush=True)
    _append_log(body)
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        for cid in ([chat_id] if chat_id else telegram_chat_ids()):
            _telegram(token, cid, body)
    if chat_id is None:
        webhook = os.environ.get("DISCORD_WEBHOOK_URL")
        if webhook:
            _discord(webhook, body)


def _append_log(body: str) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_DIR / "notifications.log", "a", encoding="utf-8") as fh:
            fh.write(f"--- {datetime.now(timezone.utc).isoformat()} ---\n{body}\n\n")
    except OSError as exc:
        log.warning("journal de notifications indisponible: %s", exc)


def _telegram(token: str, chat_id: str, body: str) -> None:
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": body[:4000], "disable_web_page_preview": True},
                          timeout=10)
        r.raise_for_status()
    except requests.RequestException as exc:
        log.warning("Telegram : envoi impossible (%s)", exc)


def _discord(webhook: str, body: str) -> None:
    try:
        r = requests.post(webhook, json={"content": body[:1990]}, timeout=10)
        r.raise_for_status()
    except requests.RequestException as exc:
        log.warning("Discord : envoi impossible (%s)", exc)


def telegram_updates(offset: int | None = None) -> list[dict]:
    """Messages reçus par le bot Telegram (getUpdates). Vide si Telegram n'est pas configuré."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return []
    params: dict = {"timeout": 0, "allowed_updates": '["message"]'}
    if offset is not None:
        params["offset"] = offset
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as exc:
        log.warning("Telegram : lecture des messages impossible (%s)", exc)
        return []
    out = []
    for upd in data.get("result", []):
        msg = upd.get("message") or {}
        text = msg.get("text")
        chat = (msg.get("chat") or {}).get("id")
        if text and chat is not None:
            out.append({"update_id": upd.get("update_id"), "chat_id": str(chat), "text": text.strip(),
                        "date": msg.get("date")})
    return out


def telegram_chat_id() -> str | None:
    ids = telegram_chat_ids()
    return ids[0] if ids else None
