"""Notifications gratuites : Telegram (bot), Discord (webhook), console + journal local.

Options d'un message (toutes facultatives) :
  - html : le texte est en HTML Telegram (gras, italique, prix en « code » copiables d'un appui) ;
    en cas de refus de Telegram, le message repart aussitôt en texte brut ;
  - buttons : boutons-liens sous le message, en lignes de (libellé, adresse) ;
  - silent : message sans son (résumé quotidien de minuit) ;
  - key : identifiant retenu pour y répondre plus tard (l'id du signal) ;
  - reply_to : le message répond à celui enregistré sous cette clé (l'issue répond à son signal).
Les numéros des messages envoyés sont gardés dans data/telegram_messages.json, indexés par une
empreinte du chat : le numéro de chat lui-même n'est jamais écrit (dépôt public).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import requests

from .config import DATA_DIR

log = logging.getLogger(__name__)
MESSAGES_FILE = "telegram_messages.json"
MAX_KEYS = 300


@dataclass
class Message:
    """Réponse riche à une commande (sinon une simple chaîne suffit)."""
    text: str
    html: bool = False
    buttons: list = field(default_factory=list)


def chat_key(chat_id: str) -> str:
    """Empreinte courte d'un identifiant de chat (jamais le numéro lui-même dans l'état public)."""
    return hashlib.sha256(str(chat_id).encode("utf-8")).hexdigest()[:12]


def telegram_chat_ids() -> list[str]:
    """Identifiants de chat autorisés (TELEGRAM_CHAT_ID, plusieurs séparés par des virgules)."""
    raw = os.environ.get("TELEGRAM_CHAT_ID") or ""
    return [c.strip() for c in raw.replace(";", ",").split(",") if c.strip()]


def plain(text: str) -> str:
    from .messages import strip_html
    return strip_html(text)


def notify(text: str, *, title: str | None = None, chat_id: str | None = None, html: bool = False,
           buttons: list | None = None, silent: bool = False, key: str | None = None,
           reply_to: str | None = None) -> None:
    """Envoie un message. `chat_id` : cible un seul chat Telegram (réponse à une commande) ;
    sinon tous les chats configurés + Discord.

    Si TRADING_BOT_OUTBOX désigne un fichier, le message y est mis en attente au lieu d'être
    envoyé : `flush_outbox()` l'enverra une fois l'état du bot enregistré (exactement une fois,
    même si le passage doit être rejoué après une collision d'écriture).
    """
    body = f"{title}\n{text}" if title else text
    readable = plain(body) if html else body
    print(readable, flush=True)
    _append_log(readable)
    item = {"text": body, "chat_id": chat_id, "html": html, "buttons": buttons or [], "silent": silent,
            "key": key, "reply_to": reply_to}
    outbox = os.environ.get("TRADING_BOT_OUTBOX")
    if outbox:
        try:
            with open(outbox, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
            return
        except OSError as exc:
            log.warning("boîte d'envoi indisponible (%s) : envoi direct", exc)
    _send(item)


def _send(item: dict) -> None:
    body, chat_id, html = item.get("text", ""), item.get("chat_id"), bool(item.get("html"))
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        ids = _load_ids()
        reply_map = ids.get(item["reply_to"], {}) if item.get("reply_to") else {}
        sent_ids = {}
        for cid in ([chat_id] if chat_id else telegram_chat_ids()):
            mid = _telegram(token, cid, body, html=html, buttons=item.get("buttons") or [],
                            silent=bool(item.get("silent")), reply_to=reply_map.get(chat_key(cid)))
            if mid:
                sent_ids[chat_key(cid)] = mid
        if item.get("key") and sent_ids:
            ids.setdefault(item["key"], {}).update(sent_ids)
            _save_ids(ids)
    if chat_id is None:
        webhook = os.environ.get("DISCORD_WEBHOOK_URL")
        if webhook:
            _discord(webhook, plain(body) if html else body)


def flush_outbox(path: str | None = None) -> int:
    """Envoie les messages en attente puis vide la boîte. Renvoie le nombre envoyé."""
    path = path or os.environ.get("TRADING_BOT_OUTBOX")
    if not path or not os.path.exists(path):
        return 0
    sent = 0
    with open(path, encoding="utf-8") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    for ln in lines:
        try:
            item = json.loads(ln)
        except ValueError:
            continue
        _send(item)
        sent += 1
    try:
        os.remove(path)
    except OSError:
        pass
    return sent


# ----------------------------------------------------------------- numéros des messages envoyés
def _dir():
    """Dossier du journal et des numéros de messages (celui du mode halal pour ses propres messages)."""
    return Path(os.environ.get("TRADING_BOT_NOTIFY_DIR") or DATA_DIR)


def _ids_path():
    return _dir() / MESSAGES_FILE


def _load_ids() -> dict:
    try:
        return json.loads(_ids_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_ids(ids: dict) -> None:
    keys = list(ids)[-MAX_KEYS:]
    try:
        _dir().mkdir(parents=True, exist_ok=True)
        _ids_path().write_text(json.dumps({k: ids[k] for k in keys}, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError as exc:
        log.warning("numéros des messages non enregistrés : %s", exc)


def _redact(body: str) -> str:
    """Le journal est versionné dans un dépôt public : on masque les identifiants de chat."""
    return re.sub(r"(identifiant de chat est )\d+", r"\1(masqué)", body)


def _append_log(body: str) -> None:
    body = _redact(body)
    try:
        _dir().mkdir(parents=True, exist_ok=True)
        with open(_dir() / "notifications.log", "a", encoding="utf-8") as fh:
            fh.write(f"--- {datetime.now(timezone.utc).isoformat()} ---\n{body}\n\n")
    except OSError as exc:
        log.warning("journal de notifications indisponible: %s", exc)


def _telegram(token: str, chat_id: str, body: str, *, html: bool = False, buttons: list | None = None,
              silent: bool = False, reply_to: int | None = None) -> int | None:
    """Envoie un message ; renvoie son numéro, ou None en cas d'échec."""
    payload: dict = {"chat_id": chat_id, "text": body[:4000], "disable_web_page_preview": True}
    if html:
        payload["parse_mode"] = "HTML"
    if silent:
        payload["disable_notification"] = True
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": [[{"text": t, "url": u} for t, u in row] for row in buttons]}
    if reply_to:
        payload["reply_parameters"] = {"message_id": int(reply_to), "allow_sending_without_reply": True}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 400 and html:
            # HTML refusé (balise inattendue) : on renvoie le même message en texte brut
            log.warning("Telegram : HTML refusé (%s), envoi en texte brut", r.text[:200])
            payload.pop("parse_mode", None)
            payload["text"] = plain(body)[:4000]
            r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return (r.json().get("result") or {}).get("message_id")
    except (requests.RequestException, ValueError) as exc:
        log.warning("Telegram : envoi impossible (%s)", exc)
        return None


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
