from datetime import datetime, timezone

from trading_bot import humeur as h

NOW = datetime(2026, 10, 27, 15, 0, tzinfo=timezone.utc).timestamp()
H = 3600


def trades(pnls, end=NOW - H):
    return [{"closed": end - (len(pnls) - k) * 6 * H, "pnl": p} for k, p in enumerate(pnls)]


def mood(pnls, **kw):
    base = dict(now=NOW, balance=1000, peak=1000, start=1000, unit=20)
    base.update(kw)
    return h.humeur(trades(pnls), **base)["humeur"]


def test_moods_in_priority_order():
    assert mood([10, -5, 10, -5]) == "serein"
    assert mood([-5, 10, 10, 10]) == "confiant"
    assert mood([10] * 6) == "euphorique"
    assert mood([10, -5, -5, -5, -5]) == "frustre"
    assert mood([10, 10, 10], balance=600) == "frustre"                     # 40 % sous le plus haut
    assert mood([10, 10, 10], scared=True) == "peur"
    assert mood([10], stopped="limite du jour") == "pause"
    assert mood([10, 10], **{"now": NOW + 10 * 86400}) == "pause"            # plus rien depuis 4 jours
    today = [{"closed": NOW - k * 600, "pnl": -20} for k in (3, 2, 1)]
    assert h.humeur(today, now=NOW, balance=940, peak=1000, start=1000, unit=20)["humeur"] == "tilt"


def test_shadow_scares_only_when_clearly_better():
    t = lambda r, live=True: {"r_bot": r, "exit_ts": NOW - H, "notified_entry": "x" if live else None}  # noqa: E731
    lab = {"a": {"live": True, "trades": [t(-0.5)] * 6}, "b": {"live": False, "trades": [t(0.4, False)] * 9}}
    assert h.ombre(lab, NOW)["peur"]
    lab["b"]["trades"] = [t(0.4, False)] * 5
    assert not h.ombre(lab, NOW)["peur"]                                     # trop peu de trades en ombre
    lab["b"]["trades"] = [t(-0.1, False)] * 9
    assert not h.ombre(lab, NOW)["peur"]                                     # l'ombre perd aussi : pas de peur


def test_mt5_curve_rebuilt_from_balance_and_previous_kept():
    raw = '{"ts": %d, "bal": 900, "eq": 905, "open": 1, "stop": null, "d": [[%d, -50, 200001, "NAS100"], [%d, -50, 777002, "XAUUSD+"]]}' % (
        NOW, NOW - 5 * H, NOW - 2 * H)
    out = h.build(portfolio={}, topstep_acct={}, lab_shadow={}, pc_raw=raw, previous=None, now=NOW)
    m = out["comptes"]["mt5"]
    assert [p[1] for p in m["courbe"]] == [1000, 950, 900] and m["derniers"][0]["source"] == "Agent IA"
    again = h.build(portfolio={}, topstep_acct={}, lab_shadow={}, pc_raw=None, previous=out, now=NOW)
    assert again["comptes"]["mt5"] == m                                       # PC éteint : dernier résumé gardé
