"""Calendrier économique gratuit (flux JSON hebdomadaire de ForexFactory, sans clé).

Une requête par heure au plus (cache), résultat mis en cache sur disque pour survivre aux pannes.
Chaque événement : titre, pays (devise), horodatage UTC, impact (High / Medium / Low / Holiday),
prévision et valeur précédente quand elles existent.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .http import ProviderError, get_json
from .news import MacroEvent

log = logging.getLogger(__name__)

FEEDS = [
    "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
    "https://nfs.faireconomy.media/ff_calendar_nextweek.json",
]
# Devises dont les annonces à fort impact bloquent les signaux
BLACKOUT_CURRENCIES = {"USD"}
CACHE_TTL_HOURS = 6


def parse_events(rows: list[dict]) -> list[MacroEvent]:
    out: list[MacroEvent] = []
    for r in rows:
        try:
            at = datetime.fromisoformat(str(r.get("date", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)
        impact = str(r.get("impact", "")).strip().lower()
        level = {"high": "high", "medium": "medium", "low": "low"}.get(impact, "low")
        country = str(r.get("country", "")).upper()
        title = str(r.get("title", "")).strip()
        if not title:
            continue
        name = f"{country} {title}".strip()
        extra = []
        if r.get("forecast"):
            extra.append(f"prévu {r['forecast']}")
        if r.get("previous"):
            extra.append(f"précédent {r['previous']}")
        if extra:
            name += " (" + ", ".join(extra) + ")"
        out.append(MacroEvent(name=name, at=at.astimezone(timezone.utc),
                              impact=level if country in BLACKOUT_CURRENCIES else ("medium" if level == "high" else "low")))
    return out


def fetch_events(cache_file: Path | None = None) -> list[MacroEvent]:
    """Événements de la semaine et de la suivante. En cas d'échec réseau, dernier cache disque."""
    rows: list[dict] = []
    errors = []
    for url in FEEDS:
        try:
            data = get_json(url, retries=1, cache_seconds=3600)
            if isinstance(data, list):
                rows.extend(data)
        except ProviderError as exc:
            errors.append(str(exc))
    if rows:
        events = parse_events(rows)
        if cache_file is not None:
            try:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(json.dumps({"fetched_at": datetime.now(timezone.utc).isoformat(),
                                                  "events": [{"name": e.name, "at": e.at.isoformat(), "impact": e.impact}
                                                             for e in events]}, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
            except OSError:
                pass
        return events
    log.warning("calendrier économique indisponible (%s) : utilisation du cache", " | ".join(errors))
    return load_cache(cache_file)


def load_cache(cache_file: Path | None) -> list[MacroEvent]:
    if cache_file is None or not cache_file.exists():
        return []
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        return [MacroEvent(e["name"], datetime.fromisoformat(e["at"]), e.get("impact", "high")) for e in data.get("events", [])]
    except (ValueError, KeyError, TypeError):
        return []


def upcoming(events: list[MacroEvent], now: datetime, hours: float = 24.0, min_impact: str = "high") -> list[MacroEvent]:
    order = {"low": 0, "medium": 1, "high": 2}
    floor = order.get(min_impact, 2)
    end = now + timedelta(hours=hours)
    return sorted((e for e in events if now <= e.at <= end and order.get(e.impact, 0) >= floor), key=lambda e: e.at)


def format_agenda(events: list[MacroEvent], tz_name: str = "Europe/Paris") -> str:
    from zoneinfo import ZoneInfo

    if not events:
        return "Aucune annonce à fort impact prévue."
    tz = ZoneInfo(tz_name)
    lines = []
    for e in events:
        icon = "🔴" if e.impact == "high" else "🟠"
        lines.append(f"  {icon} {e.at.astimezone(tz):%a %d/%m %H:%M} — {e.name}")
    return "\n".join(lines)
