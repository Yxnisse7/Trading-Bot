"""Essai 12 : réaction du marché à une annonce, gardée jusqu'à la fin de séance."""
from datetime import datetime, timezone

from trading_bot import macro_drift as md
from trading_bot.models import Candle


def test_reaction_direction_and_session_exit_in_atr_units():
    t_ev = int(datetime(2026, 3, 6, 13, 30, tzinfo=timezone.utc).timestamp())      # NFP, 8:30 à New York
    start = t_ev - 3 * 86_400
    candles, px = [], 100.0
    for k in range(0, 5 * 288):
        ts = start + 300 * k
        if ts == t_ev:
            px += 2.0                                                               # réaction haussière
        elif ts > t_ev:
            px += 0.01                                                              # puis la hausse continue
        candles.append(Candle(ts, px, px + 0.2, px - 0.2, px))
    rows = md.reactions(candles, "gold", [(t_ev, "nfp")])
    assert len(rows) == 1 and rows[0]["dir"] == 1 and rows[0]["r_day"] > 0 and "r_next" in rows[0]
    j = md.judge(rows * 25)
    assert j["all"]["n"] == 25 and set(j["by_kind"]) == {"nfp", "cpi", "fomc"}


def test_long_events_file_and_needed_days():
    from datetime import date
    from trading_bot import macro_long as ml
    ev = ml.events()
    kinds = {k for _, k in ev}
    assert kinds == {"nfp", "cpi", "fomc"} and len(ev) > 400
    t0 = datetime.fromtimestamp(ev[0][0], timezone.utc)
    assert t0.year == 2010 and t0.hour in (13, 14)                     # 8:30 à New York = 13:30 ou 12:30 UTC
    fomc = [ts for ts, k in ev if k == "fomc"]
    assert all(datetime.fromtimestamp(ts, timezone.utc).year >= 2013 for ts in fomc)
    days = ml.needed_days([(int(datetime(2015, 1, 9, 13, 30, tzinfo=timezone.utc).timestamp()), "nfp")])
    assert days == [date(2015, 1, 8), date(2015, 1, 9), date(2015, 1, 12)]   # veille, jour, lundi suivant
