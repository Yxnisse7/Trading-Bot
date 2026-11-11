"""Filtre « bond du VIX » du bot classique Nasdaq (essai 81, choix de Yanisse le 11/11/2026).

Règle : pas de trade du bot classique Nasdaq le jour qui suit un bond du VIX d'au moins 10 % (clôture de la veille
contre clôture de l'avant-veille, séances de New York). Sur 2014-2026 : 328 trades dans ce cas, −0,18 R en moyenne
contre +0,13 R pour les autres, négatif avant et après 2020. Les trades écartés restent suivis en ombre.

Les clôtures viennent de Yahoo (^VIX, bougies jour) et sont gardées dans vix.json à côté des données du bot.
Sans donnée fraîche (panne, jour manquant), le filtre ne s'applique pas : on préfère un trade de plus à un blocage
sur une vieille valeur.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .providers.http import get_json
from .providers.yahoo import CHART_URL

log = logging.getLogger("vix")
NY = ZoneInfo("America/New_York")
FLAG = "vix_bond"
JUMP = 0.10
MAX_AGE = 6 * 3600        # s : au-delà, les clôtures sont relues
MAX_GAP = 4               # jours : la dernière séance connue ne doit pas être plus vieille (week-end + férié)
FILE = "vix.json"


def fetch() -> list[list]:
    """[[jour, clôture], …] des dernières séances (jour de New York), la séance en cours comprise."""
    data = get_json(CHART_URL.format(symbol="%5EVIX"), params={"interval": "1d", "range": "1mo"})
    res = data["chart"]["result"][0]
    out = {}
    for ts, c in zip(res.get("timestamp") or [], res["indicators"]["quote"][0].get("close") or []):
        if c and c > 0:
            out[datetime.fromtimestamp(int(ts), NY).date().isoformat()] = round(float(c), 2)
    return [[d, v] for d, v in sorted(out.items())]


def closes(folder: Path, now: datetime) -> list[list]:
    """Clôtures en cache, relues sur Yahoo si le cache est vieux. Jamais d'erreur : liste vide au pire."""
    f = Path(folder) / FILE
    try:
        cached = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cached = {}
    age = now.timestamp() - float(cached.get("ts") or 0)
    if 0 <= age < MAX_AGE and cached.get("closes"):
        return cached["closes"]
    try:
        rows = fetch()
        if rows:
            f.write_text(json.dumps({"ts": int(now.timestamp()), "closes": rows}), encoding="utf-8")
            return rows
    except Exception as exc:                                  # noqa: BLE001 — Yahoo en panne : pas de filtre
        log.info("VIX non relu (%s)", exc)
    return cached.get("closes") or [] if 0 <= age < 86400 else []


def jump(rows: list[list], day: date) -> float | None:
    """Variation du VIX à la dernière séance terminée AVANT `day` (jour de New York) ; None si pas de donnée sûre."""
    past = [(date.fromisoformat(d), float(v)) for d, v in rows if date.fromisoformat(d) < day]
    if len(past) < 2 or (day - past[-1][0]).days > MAX_GAP or past[-2][1] <= 0:
        return None
    return past[-1][1] / past[-2][1] - 1


def blocked(folder: Path, now: datetime) -> bool:
    day = now.astimezone(NY).date()
    j = jump(closes(folder, now), day)
    return j is not None and j >= JUMP

