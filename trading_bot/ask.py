"""Question posée à l'agent IA depuis Telegram (demandé par Yanisse le 27/10/2026) : « /avis ton avis sur le Nasdaq ? ».

Le pont MT5 du PC (mt5_ask.py) lance ce script avec le marché du moment, les positions ouvertes du démo et la question :

    python -m trading_bot.ask --marche chemin/marche.json

La DERNIÈRE ligne affichée est la réponse en JSON : {"conseil": "garder"|"securiser"|"fermer"|"aucune_position"|
"autre", "reponse": "..."}. Un avis seulement : aucun ordre, aucun stop déplacé. L'appel à Claude réutilise agent/ia.py
du dépôt privé de l'agent, copié sur le PC (dossier réglable par AGENT_DIR).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
AGENT_DIR = r"E:\TradingBot\agent\agent"
TIMEOUT = 70
CONSEILS = ("garder", "securiser", "fermer", "aucune_position", "autre")

SCHEMA = {
    "type": "object",
    "properties": {
        "conseil": {"type": "string", "enum": list(CONSEILS)},
        "reponse": {"type": "string"},
    },
    "required": ["conseil", "reponse"],
}

CONSIGNE = """Tu es le conseiller d'un trader débutant qui te pose une question depuis Telegram, sur son compte démo MT5.
Tu vois les bougies du marché concerné (jour, 1 h, 15 min, 5 min), le prix du moment, les annonces à venir et ses
positions ouvertes (sens, entrée, stop, objectif, gain ou perte du moment, qui l'a ouverte).

Réponds à sa question, en français simple, en 6 phrases au plus :
- Commence par ton avis net : la tendance du moment et ce qui peut arriver ensuite (plutôt hausse, plutôt baisse, ou pas
  clair), avec les niveaux de prix qui comptent (support, résistance, creux ou sommet récent).
- S'il a des positions et que sa question les concerne : pour chacune, dis s'il vaut mieux la garder, sécuriser
  (remonter le stop à l'entrée ou sous un creux récent, en donnant le niveau) ou la fermer, et pourquoi.
- Si le marché est fermé, dis-le en une phrase, et donne ton avis pour la réouverture (écart possible à l'ouverture).
- Dis ce qui changerait ton avis (un niveau cassé, une annonce).
- Pas de promesse, pas de certitude : le marché peut faire l'inverse. Tu ne passes aucun ordre et tu ne déplaces
  aucun stop : tu donnes un avis, c'est lui qui décide.
- Si la question n'a rien à voir avec les marchés, réponds brièvement et honnêtement, conseil « autre ».
- conseil : « garder », « securiser » ou « fermer » (pour l'ensemble de ses positions concernées, la plus importante
  si elles diffèrent), « aucune_position » s'il n'a rien d'ouvert sur ce marché, « autre » sinon.
Ne conseille jamais de trader un compte réel ni de grossir une position pour se refaire."""

FAIL = {"conseil": "autre"}


def fmt(bougies: list[list[float]], n: int) -> str:
    return "\n".join(
        f"{datetime.fromtimestamp(x[0], PARIS):%d/%m %H:%M} O {x[1]:g} H {x[2]:g} L {x[3]:g} C {x[4]:g}"
        for x in bougies[-n:]) or "indisponibles"


def message(m: dict[str, Any]) -> str:
    now = datetime.fromisoformat(m["now"].replace("Z", "+00:00")).astimezone(PARIS)
    annonces = "\n".join(f"- {a.get('heure')} : {a.get('titre')} (impact {a.get('impact')})"
                         for a in m.get("annonces") or []) or "- aucune"
    pos = "\n".join(
        f"- {p.get('marche')} {p.get('sens')} {p.get('lot')} lot, entrée {p.get('entree')}, stop {p.get('stop')}, "
        f"objectif {p.get('objectif')}, gain/perte du moment {p.get('profit')} $, ouverte par {p.get('origine')}"
        for p in m.get("positions") or []) or "- aucune position ouverte"
    return f"""Question du trader : {m.get('question', '')}

Marché concerné : {m.get('asset_label', m.get('asset', '?'))} · {now:%A %d/%m/%Y %H:%M} (heure de Paris)
Prix : achat (ask) {m['ask']:g} · vente (bid) {m['bid']:g}
{("ATTENTION : " + m["ferme"] + ". Le prix ci-dessus est le dernier connu, les bougies s'arrêtent à la clôture : donne ton avis pour la réouverture.") if m.get("ferme") else ""}

Positions ouvertes sur son démo (tous marchés) :
{pos}

Annonces (de −2 h à +6 h, heure de Paris) :
{annonces}

Bougies jour :
{fmt(m.get('candles_1d', []), 10)}

Bougies 1 h :
{fmt(m.get('candles_1h', []), 24)}

Bougies 15 min :
{fmt(m.get('candles_15m', []), 32)}

Bougies 5 min :
{fmt(m.get('candles_5m', []), 36)}

Ta réponse :"""


def check(rep: dict[str, Any]) -> dict[str, Any]:
    text = str(rep.get("reponse") or "").strip()
    if not text:
        return dict(FAIL, reponse="Pas de réponse lisible de Claude.")
    conseil = rep.get("conseil") if rep.get("conseil") in CONSEILS else "autre"
    return {"conseil": conseil, "reponse": text}


def decide(m: dict[str, Any], call: Callable[..., Any] | None = None) -> dict[str, Any]:
    if call is None:
        if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
            return dict(FAIL, reponse="Claude n'est pas connecté sur le PC.")
        sys.path.insert(0, os.environ.get("AGENT_DIR", AGENT_DIR))
        from ia import appeler_claude, installer_claude  # dépôt privé de l'agent, copié sur le PC
        if not installer_claude():
            return dict(FAIL, reponse="Claude n'est pas installé sur le PC.")
        call = appeler_claude
    out = call(message(m), CONSIGNE, SCHEMA, TIMEOUT)
    rep = (out or {}).get("structured_output")
    if not rep and out:
        text = out.get("result", "")
        try:
            rep = json.loads(text[text.index("{"):text.rindex("}") + 1])
        except ValueError:
            rep = None
    if not rep or (out or {}).get("is_error"):
        return dict(FAIL, reponse="Pas de réponse lisible de Claude.")
    return check(rep)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--marche", required=True, help="fichier JSON du marché (pont MT5)")
    m = json.loads(Path(ap.parse_args().marche).read_text(encoding="utf-8"))
    try:
        d = decide(m)
    except Exception as e:  # noqa: BLE001 — le pont attend toujours une réponse sur la dernière ligne
        d = dict(FAIL, reponse=f"Erreur de l'agent ({type(e).__name__}).")
    print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
