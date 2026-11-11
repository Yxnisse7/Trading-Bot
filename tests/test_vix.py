import json
from datetime import date, datetime, timezone

from trading_bot import vix

ROWS = [["2026-11-05", 20.0], ["2026-11-06", 20.4], ["2026-11-09", 23.0], ["2026-11-10", 23.1]]


def test_jump_uses_the_last_finished_session_before_the_day():
    assert round(vix.jump(ROWS, date(2026, 11, 10)), 3) == 0.127        # lundi 9 contre vendredi 6
    assert round(vix.jump(ROWS, date(2026, 11, 11)), 3) == 0.004
    assert vix.jump(ROWS, date(2026, 11, 9)) < 0.10                     # le lundi : vendredi contre jeudi
    assert vix.jump(ROWS, date(2026, 11, 20)) is None                   # donnée trop vieille : pas de filtre
    assert vix.jump(ROWS[:1], date(2026, 11, 6)) is None


def test_blocked_reads_the_cache_and_never_fails(tmp_path, monkeypatch):
    now = datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc)
    (tmp_path / vix.FILE).write_text(json.dumps({"ts": int(now.timestamp()) - 60, "closes": ROWS}))
    monkeypatch.setattr(vix, "fetch", lambda: (_ for _ in ()).throw(RuntimeError("pas de réseau")))
    assert vix.blocked(tmp_path, now) is True
    assert vix.blocked(tmp_path, datetime(2026, 11, 11, 15, 0, tzinfo=timezone.utc)) is False
    assert vix.blocked(tmp_path / "vide", now) is False                 # ni cache ni réseau : pas de filtre
