"""Notifications gratuites : Telegram (bot), Discord (webhook), console + journal local."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import requests

from .config import DATA_DIR

log = logging.getLogger(__name__)


def notify(text: str, *, title: str | None = None) -> None:
    body = f"{title}\n{text}" if title else text
    print(body, flush=True)
    _append_log(body)
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        _telegram(token, chat_id, body)
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
