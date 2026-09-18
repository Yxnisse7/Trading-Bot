from datetime import datetime, timezone

from trading_bot.providers import calendar as cal


ROWS = [
    {"title": "CPI m/m", "country": "USD", "date": "2026-09-18T12:30:00-04:00", "impact": "High", "forecast": "0.3%", "previous": "0.2%"},
    {"title": "Retail Sales", "country": "USD", "date": "2026-09-18T12:30:00-04:00", "impact": "Medium"},
    {"title": "ECB Press Conference", "country": "EUR", "date": "2026-09-19T12:45:00-04:00", "impact": "High"},
    {"title": "Bank Holiday", "country": "JPY", "date": "2026-09-21T00:00:00-04:00", "impact": "Holiday"},
    {"title": "", "country": "USD", "date": "2026-09-18T10:00:00-04:00", "impact": "High"},
]


def test_parse_events_levels_and_utc():
    events = cal.parse_events(ROWS)
    assert len(events) == 4
    cpi = events[0]
    assert cpi.at == datetime(2026, 9, 18, 16, 30, tzinfo=timezone.utc)
    assert cpi.impact == "high" and "prévu 0.3%" in cpi.name and cpi.name.startswith("USD CPI")
    assert events[1].impact == "medium"          # USD Medium → medium (pas de blackout)
    assert events[2].impact == "medium"          # EUR High → medium (hors devise de blackout)
    assert events[3].impact == "low"


def test_upcoming_and_agenda_and_cache(tmp_path):
    events = cal.parse_events(ROWS)
    now = datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc)
    up = cal.upcoming(events, now, hours=24, min_impact="high")
    assert [e.name.split(" (")[0] for e in up] == ["USD CPI m/m"]
    text = cal.format_agenda(up)
    assert "18/09 18:30" in text and "CPI" in text
    assert cal.format_agenda([]) == "Aucune annonce à fort impact prévue."
    # cache disque : écriture puis relecture
    f = tmp_path / "cal.json"
    import json
    f.write_text(json.dumps({"events": [{"name": "x", "at": "2026-09-18T16:30:00+00:00", "impact": "high"}]}), encoding="utf-8")
    cached = cal.load_cache(f)
    assert len(cached) == 1 and cached[0].impact == "high"
    assert cal.load_cache(None) == [] and cal.load_cache(tmp_path / "absent.json") == []
