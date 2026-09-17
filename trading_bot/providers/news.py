"""Flux RSS financiers gratuits + calendrier macro pour filtrer les périodes risquées."""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from .http import ProviderError, get_text

log = logging.getLogger(__name__)

# Flux RSS publics et gratuits (aucune clé requise)
FEEDS: dict[str, list[str]] = {
    "macro": [
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",     # MarketWatch
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",            # CNBC Top News
        "https://www.cnbc.com/id/20910258/device/rss/rss.html",             # CNBC Economy
        "https://finance.yahoo.com/news/rssindex",                          # Yahoo Finance
    ],
    "crypto": [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",                  # CoinDesk
        "https://cointelegraph.com/rss",                                    # Cointelegraph
    ],
    "gold": [
        "https://www.fxstreet.com/rss/news",                                # FXStreet (forex / or / dollar)
    ],
}

# Actualité macro critique : compte pour tous les actifs (1 point, 2 si le titre cite l'actif)
MACRO_CRITICAL_PATTERNS = [
    r"\bfomc\b", r"\bfed (decision|meeting|rate)", r"\brate (hike|cut|decision)s?\b",
    r"\bcpi\b", r"\binflation (data|report|print)", r"\bnon-?farm\b", r"\bpayrolls\b",
    r"\bjobs report\b", r"\bpowell\b", r"\becb (decision|meeting)", r"\bflash crash\b",
    r"\bcircuit breaker\b", r"\btrading halt", r"\bmarket crash", r"\bstocks? (plunge|crash|tumble)",
    r"\btariffs?\b", r"\bmissile", r"\bstrikes? on\b", r"\bstate of emergency\b",
]
# Actualité spécifique : ne compte (2 points) que si le titre cite l'actif concerné
ASSET_SPECIFIC_PATTERNS = [
    r"\bhack(ed|ers)?\b", r"\bexploit", r"\bbankrupt", r"\bdefaults?\b", r"\bliquidations?\b",
    r"\bplunge", r"\bcrash", r"\bsoar", r"\bsurge", r"\btumble", r"\bhalt",
    r"\bsec (lawsuit|charges|sues)", r"\betf (approval|rejected|decision)", r"\bwar\b",
]
HIGH_RISK_PATTERNS = MACRO_CRITICAL_PATTERNS + ASSET_SPECIFIC_PATTERNS  # compatibilité


@dataclass
class NewsItem:
    title: str
    link: str
    published: datetime
    source: str
    category: str


@dataclass
class MacroEvent:
    name: str
    at: datetime          # UTC
    impact: str = "high"  # high | medium


def parse_rss(xml_text: str, source: str, category: str) -> list[NewsItem]:
    items: list[NewsItem] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for node in root.iter("item"):
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        date_raw = node.findtext("pubDate") or node.findtext("{http://purl.org/dc/elements/1.1/}date") or ""
        published = _parse_date(date_raw)
        if title and published:
            items.append(NewsItem(title, link, published, source, category))
    for node in root.findall(".//atom:entry", ns):
        title = (node.findtext("atom:title", default="", namespaces=ns) or "").strip()
        link_el = node.find("atom:link", ns)
        link = link_el.get("href", "") if link_el is not None else ""
        date_raw = node.findtext("atom:updated", default="", namespaces=ns) or node.findtext("atom:published", default="", namespaces=ns)
        published = _parse_date(date_raw or "")
        if title and published:
            items.append(NewsItem(title, link, published, source, category))
    return items


def _parse_date(raw: str) -> datetime | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def fetch_news(categories: list[str], lookback_minutes: int = 120, now: datetime | None = None) -> list[NewsItem]:
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=lookback_minutes)
    out: list[NewsItem] = []
    for cat in categories:
        for url in FEEDS.get(cat, []):
            try:
                text = get_text(url, timeout=10)
            except ProviderError as exc:
                log.warning("flux RSS indisponible %s: %s", url, exc)
                continue
            for item in parse_rss(text, url.split("/")[2], cat):
                if item.published >= cutoff:
                    out.append(item)
    out.sort(key=lambda i: i.published, reverse=True)
    return out


def risk_score(items: list[NewsItem], asset_keywords: tuple[str, ...]) -> tuple[int, list[str]]:
    """Score de risque : titres récents à fort impact.

    - macro critique (FOMC, CPI, emploi, krach, tarifs, frappes…) : 1 point, 2 si l'actif est cité
    - spécifique (piratage, faillite, envolée, effondrement…) : 2 points seulement si l'actif est cité
    Les titres identiques repris par plusieurs flux ne comptent qu'une fois.
    """
    score = 0
    hits: list[str] = []
    seen: set[str] = set()
    for item in items:
        t = item.title.lower().strip()
        key = re.sub(r"\W+", " ", t)
        if key in seen:
            continue
        seen.add(key)
        related = any(k in t for k in asset_keywords)
        macro = any(re.search(p, t) for p in MACRO_CRITICAL_PATTERNS)
        specific = any(re.search(p, t) for p in ASSET_SPECIFIC_PATTERNS)
        if macro:
            score += 2 if related else 1
            hits.append(item.title)
        elif specific and related:
            score += 2
            hits.append(item.title)
    return score, hits[:5]


# ---- Calendrier macro (blackout) -------------------------------------------------

def recurring_macro_events(day: datetime) -> list[MacroEvent]:
    """Événements récurrents déductibles sans API : NFP (1er vendredi, 12h30 UTC)."""
    events: list[MacroEvent] = []
    d = day.astimezone(timezone.utc)
    if d.weekday() == 4 and d.day <= 7:
        events.append(MacroEvent("Rapport emploi US (NFP)", d.replace(hour=12, minute=30, second=0, microsecond=0)))
    return events


def load_calendar(events_raw: list[dict]) -> list[MacroEvent]:
    out = []
    for e in events_raw:
        try:
            at = datetime.fromisoformat(e["at"].replace("Z", "+00:00")).astimezone(timezone.utc)
            out.append(MacroEvent(e["name"], at, e.get("impact", "high")))
        except (KeyError, ValueError):
            continue
    return out


def in_blackout(now: datetime, events: list[MacroEvent], before_min: int, after_min: int) -> MacroEvent | None:
    for ev in events:
        if ev.impact != "high":
            continue
        if ev.at - timedelta(minutes=before_min) <= now <= ev.at + timedelta(minutes=after_min):
            return ev
    return None
