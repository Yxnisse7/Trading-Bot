"""Sauvegarde hebdomadaire envoyée sur Telegram : de quoi tout reconstruire si GitHub bloquait le dépôt.

L'archive (zip) contient tous les fichiers suivis du dépôt (code, données, site), plus l'historique
des bougies gardé dans la release « candles » quand il est fourni. Elle part uniquement vers le
premier chat de TELEGRAM_CHAT_ID (le propriétaire), jamais vers les autres chats autorisés.
Les secrets (jeton Telegram…) ne sont pas dans le dépôt, donc pas dans l'archive.
"""
from __future__ import annotations

import logging
import os
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

import requests

from .notify import telegram_chat_id

log = logging.getLogger(__name__)
TELEGRAM_LIMIT = 49 * 1024 * 1024        # les bots Telegram envoient jusqu'à 50 Mo
PREFIX = "Trading-Bot"


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True).stdout
    return [f for f in out.decode("utf-8").split("\0") if f]


def build_archive(root: Path, out_dir: Path, day: datetime, candles: Path | None = None) -> tuple[Path, dict]:
    """Construit l'archive ; renvoie son chemin et un petit résumé (fichiers, bougies incluses)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"yasuke-sauvegarde-{day:%Y-%m-%d}.zip"
    files = tracked_files(root)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in files:
            src = root / rel
            if src.is_file():
                zf.write(src, f"{PREFIX}/{rel}")
        with_candles = candles is not None and candles.is_file()
        if with_candles:
            zf.write(candles, f"{PREFIX}/sauvegarde/candles.tar.gz")
        zf.writestr(f"{PREFIX}/sauvegarde/LISEZMOI.txt", restore_notes(day, with_candles))
    if with_candles and path.stat().st_size > TELEGRAM_LIMIT:
        # trop gros pour Telegram : on retire les bougies (le reste est l'essentiel)
        log.warning("archive trop lourde avec les bougies (%d o) : envoyée sans", path.stat().st_size)
        return build_archive(root, out_dir, day, None)
    return path, {"files": len(files), "candles": with_candles, "size": path.stat().st_size}


def restore_notes(day: datetime, with_candles: bool) -> str:
    return (
        f"Sauvegarde du Yasuke Trading-Bot du {day:%d/%m/%Y}.\n\n"
        "Pour repartir si le dépôt GitHub n'est plus accessible :\n"
        "1. Créer un nouveau dépôt GitHub public et y envoyer le contenu du dossier Trading-Bot\n"
        "   (sans le dossier « sauvegarde »).\n"
        "2. Dans Settings > Secrets and variables > Actions, remettre les secrets TELEGRAM_BOT_TOKEN\n"
        "   et TELEGRAM_CHAT_ID (ils ne sont jamais dans l'archive).\n"
        "3. Activer GitHub Pages sur le dossier /docs de la branche main, puis les workflows (onglet Actions).\n"
        "4. Remettre l'adresse du nouveau dépôt dans cron-job.org (déclenchement toutes les 5 minutes).\n"
        + ("5. Historique des bougies : créer une release « candles » et y joindre sauvegarde/candles.tar.gz.\n"
           if with_candles else "")
        + "\nToutes les données (trades, apprentissage, simulation, Topstep, investissement) sont dans data/.\n"
    )


def send_document(path: Path, caption: str, chat_id: str | None = None) -> bool:
    """Envoie le fichier au propriétaire sur Telegram. False si Telegram n'est pas configuré ou refuse."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or telegram_chat_id()
    if not token or not chat_id:
        log.warning("Telegram non configuré : sauvegarde non envoyée")
        return False
    try:
        with open(path, "rb") as fh:
            r = requests.post(f"https://api.telegram.org/bot{token}/sendDocument",
                              data={"chat_id": chat_id, "caption": caption[:1000], "disable_notification": True},
                              files={"document": (path.name, fh, "application/zip")}, timeout=120)
        r.raise_for_status()
        return True
    except requests.RequestException as exc:
        log.warning("Telegram : envoi de la sauvegarde impossible (%s)", exc)
        return False


def caption(summary: dict, day: datetime) -> str:
    size = summary["size"] / (1024 * 1024)
    return (f"💾 Sauvegarde hebdomadaire du {day:%d/%m/%Y} ({size:.1f} Mo)\n"
            f"Code, données et site ({summary['files']} fichiers)"
            + (", plus l'historique des bougies" if summary["candles"] else "") + ".\n"
            "À garder : de quoi tout reconstruire si GitHub bloquait le dépôt (mode d'emploi dans sauvegarde/LISEZMOI.txt).")
