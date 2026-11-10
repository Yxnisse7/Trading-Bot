from trading_bot import arret


def test_levels_follow_the_written_limits():
    assert arret.level("donchian_1h", [-1.0] * 8)["state"] == "ok"
    assert arret.level("donchian_1h", [-1.0] * 10)["state"] == "surveiller"
    assert arret.level("donchian_1h", [3.0] + [-1.0] * 20)["state"] == "ombre"       # seuls les 20 derniers comptent
    assert arret.level("inconnue", [-9.0]) is None


def test_only_announced_closed_trades_count_and_quiet_when_ok():
    lab = {"nuit_asie:gold": {"strategy": "nuit_asie", "trades": [
        {"status": "closed", "notified_entry": "x", "r_bot": -1.1, "entry_ts": 1},
        {"status": "closed", "notified_entry": "x", "r_bot": -1.2, "entry_ts": 2},
        {"status": "closed", "r_bot": -5.0, "entry_ts": 3},                           # en ombre : pas compté
        {"status": "open", "notified_entry": "x", "entry_ts": 4}]}}
    rows = arret.from_lab(lab)
    assert rows[0]["total_r"] == -2.3 and rows[0]["state"] == "surveiller"
    assert "surveiller" in arret.lines(rows)[0]
    assert arret.lines([arret.level("swing_w3", [-1.0] * 9)]) == []
