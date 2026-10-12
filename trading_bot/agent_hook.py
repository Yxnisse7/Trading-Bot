"""Second avis d'un agent IA avant chaque ordre du pont MetaTrader 5 (désactivé tant qu'il n'y a pas de clé).

Il s'active seulement si config.json contient "agent": {"enabled": true, "model": "<modèle>", "library": "<dossier>"}
et si la clé est dans la variable d'environnement ANTHROPIC_API_KEY (jamais dans un fichier du bot). La
bibliothèque est un dossier local de textes (.md) lus par l'agent à chaque avis ; elle reste sur le PC.
Sans réponse claire de l'agent, le trade n'est pas pris (prudence).
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import requests

log = logging.getLogger("agent_hook")
API = "https://api.anthropic.com/v1/messages"
MAX_CHARS = 600_000

INSTRUCTIONS = (
    "Tu es le second avis d'un robot de scalping sur l'or (trades de quelques minutes, un seul à la fois). "
    "Le robot a trouvé une entrée avec ses règles. Juge-la uniquement avec la méthode décrite dans la "
    "bibliothèque ci-dessus (contexte des unités de temps, niveaux, chiffres ronds, étirement, annonces, "
    "qualité du stop). Réponds sur la première ligne par OUI ou NON, puis une phrase qui explique pourquoi."
)


class Agent:
    def __init__(self, cfg: dict[str, Any], root: Path, env: dict[str, str] | None = None):
        env = os.environ if env is None else env
        self.key = env.get("ANTHROPIC_API_KEY", "")
        self.model = cfg.get("model", "")
        lib = cfg.get("library") or ""
        self.library = Path(lib) if lib and Path(lib).is_absolute() else root / lib if lib else None
        self.enabled = bool(cfg.get("enabled") and self.key and self.model)
        self._text: str | None = None

    def library_text(self) -> str:
        if self._text is None:
            parts: list[str] = []
            if self.library and self.library.exists():
                files = sorted(self.library.rglob("*.md"), key=lambda p: (p.name != "MEMO-METHODE.md", str(p)))
                for f in files:
                    parts.append(f"### {f.relative_to(self.library)}\n{f.read_text(encoding='utf-8', errors='ignore')}")
            self._text = "\n\n".join(parts)[:MAX_CHARS]
        return self._text

    def ask(self, info: dict[str, Any]) -> tuple[bool, str]:
        if not self.enabled:
            return True, "agent inactif"
        body = {
            "model": self.model, "max_tokens": 200,
            "system": [{"type": "text", "text": self.library_text() or "(bibliothèque vide)",
                        "cache_control": {"type": "ephemeral"}},
                       {"type": "text", "text": INSTRUCTIONS}],
            "messages": [{"role": "user", "content": json.dumps(info, ensure_ascii=False)}],
        }
        try:
            r = requests.post(API, json=body, timeout=30, headers={
                "x-api-key": self.key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
            r.raise_for_status()
            text = "".join(b.get("text", "") for b in r.json().get("content", [])).strip()
        except (requests.RequestException, ValueError) as exc:
            log.warning("agent injoignable : %s", exc)
            return False, "agent injoignable"
        first = text.splitlines()[0].strip().upper() if text else ""
        return first.startswith("OUI"), text[:500]
