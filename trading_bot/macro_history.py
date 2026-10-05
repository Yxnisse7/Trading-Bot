"""Annonces macro américaines passées (octobre 2024 → décembre 2026), pour les tests sur l'historique.

Heures officielles en heure de New York : emploi (NFP) et inflation (CPI) à 8:30, décision de la Fed
(FOMC) à 14:00. Sources : federalreserve.gov (calendrier FOMC 2024-2026), bls.gov (calendriers CPI et
Employment Situation), dont les reports dus à la fermeture de l'État fédéral du 1er octobre au
12 novembre 2025 : CPI de septembre publié le 24/10/2025, pas de CPI d'octobre 2025, emploi de
septembre publié le 20/11/2025, emploi d'octobre et novembre publié ensemble le 16/12/2025.
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")

NFP = ["2024-10-04", "2024-11-01", "2024-12-06",
       "2025-01-10", "2025-02-07", "2025-03-07", "2025-04-04", "2025-05-02", "2025-06-06", "2025-07-03",
       "2025-08-01", "2025-09-05", "2025-11-20", "2025-12-16",
       "2026-01-09", "2026-02-11", "2026-03-06", "2026-04-03", "2026-05-08", "2026-06-05", "2026-07-02",
       "2026-08-07", "2026-09-04", "2026-10-02", "2026-11-06", "2026-12-04"]
CPI = ["2024-10-10", "2024-11-13", "2024-12-11",
       "2025-01-15", "2025-02-12", "2025-03-12", "2025-04-10", "2025-05-13", "2025-06-11", "2025-07-15",
       "2025-08-12", "2025-09-11", "2025-10-24", "2025-12-18",
       "2026-01-13", "2026-02-13", "2026-03-11", "2026-04-10", "2026-05-12", "2026-06-10", "2026-07-14",
       "2026-08-12", "2026-09-11", "2026-10-14", "2026-11-10", "2026-12-10"]
FOMC = ["2024-11-07", "2024-12-18",
        "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29",
        "2025-12-10",
        "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28",
        "2026-12-09"]

LABELS = {"nfp": "Emploi US (NFP)", "cpi": "Inflation US (CPI)", "fomc": "Décision de la Fed (FOMC)"}


def _at(day: str, hh: int, mm: int) -> int:
    return int(datetime.combine(date.fromisoformat(day), time(hh, mm), NY).timestamp())


def events() -> list[tuple[int, str]]:
    """(horodatage UTC de l'annonce, type) triés dans le temps."""
    out = [(_at(d, 8, 30), "nfp") for d in NFP] + [(_at(d, 8, 30), "cpi") for d in CPI] \
        + [(_at(d, 14, 0), "fomc") for d in FOMC]
    return sorted(out)


def as_utc(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)
