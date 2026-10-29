from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

from trading_bot import demo_rules as dr


def deal(pos, t, pnl, entry=1, magic=180018):
    return NS(position_id=pos, time=t, profit=pnl, commission=-0.06, swap=0.0, entry=entry, magic=magic)


def test_positions_are_grouped_with_fees_and_other_magics_ignored():
    deals = [deal(1, 10, 0.0, entry=0), deal(1, 20, 3.0), deal(2, 30, -2.0), deal(3, 40, 5.0, magic=777001)]
    assert dr.closed_trades(deals, 180018, 1) == [(20, 3.0 - 0.12), (30, -2.06)]


def test_rules_cumulative_loss_streak_and_gap_with_backtest():
    assert dr.breach([(i, -1.0) for i in range(7)], 180018) is None
    assert "pertes d'affilée" in dr.breach([(i, -1.0) for i in range(8)], 180018)
    assert "perte cumulée" in dr.breach([(0, -26.0)], 180018)
    mixed = [(i, 2.0 if i % 2 else -3.0) for i in range(40)]          # −0,5 $ par trade ≈ −0,13 R : toléré
    assert dr.breach(mixed, 180018) is None
    worse = [(i, 1.0 if i % 2 else -4.0) for i in range(40)]          # −1,5 $ par trade ≈ −0,40 R
    assert dr.breach(worse, 180018)                                    # la perte cumulée arrive avant l'écart
    assert "pertes d'affilée" in dr.breach([(i, -5.0) for i in range(6)], 777001)


def test_balance_rules_for_the_demo_copy():
    """26/10 : arrêt du jour à −6 % du solde du matin et arrêt total sous 90 $ (copie démo 200001)."""
    from types import SimpleNamespace as NS
    now = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc) + timedelta(days=1)
    today = int(datetime(2026, 10, 26, 10, 0, tzinfo=timezone.utc).timestamp())
    mt5 = NS(account_info=lambda: NS(balance=190.0))
    assert dr.balance_breach(mt5, 200001, [(today, -5.0)], now) is None             # −2,6 % : continue
    assert "perte du jour" in dr.balance_breach(mt5, 200001, [(today, -13.0)], now)   # −6,4 % du solde du matin (203 $)
    old = int(datetime(2026, 10, 24, 10, 0, tzinfo=timezone.utc).timestamp())
    assert dr.balance_breach(mt5, 200001, [(old, -50.0)], now) is None              # une perte d'un autre jour ne compte pas
    assert "solde" in dr.balance_breach(NS(account_info=lambda: NS(balance=85.0)), 200001, [], now)
    assert dr.balance_breach(mt5, 777002, [(today, -90.0)], now) is None            # règle propre à la copie


def test_night_trades_do_not_count_in_the_day_loss():
    """29/10 : le stop de la nuit asiatique (or) bloquait la copie de W3 Bitcoin à 12h20 (−40,77 $, 13,4 %)."""
    from types import SimpleNamespace as NS
    now = datetime(2026, 10, 29, 10, 0, tzinfo=timezone.utc) + timedelta(days=1)
    srv = lambda *a: int(datetime(*a, tzinfo=timezone.utc).timestamp()) + 3 * 3600   # heure du serveur (UTC+3)
    night_open = srv(2026, 10, 28, 23, 0)                                 # minuit Paris
    day_open = srv(2026, 10, 29, 9, 0)                                    # 10 h Paris
    assert dr.is_night(night_open) and not dr.is_night(day_open)
    assert dr.is_night(srv(2026, 10, 29, 6, 30)) and not dr.is_night(srv(2026, 10, 29, 7, 30))   # 7h30 / 8h30 Paris
    mt5 = NS(account_info=lambda: NS(balance=262.0))
    closed = srv(2026, 10, 29, 8, 0)
    assert dr.balance_breach(mt5, 200001, [(closed, -40.77, night_open)], now) is None
    assert "perte du jour" in dr.balance_breach(mt5, 200001, [(closed, -40.77, day_open)], now)
    assert "perte du jour" in dr.balance_breach(mt5, 200001, [(closed, -40.77, night_open), (closed, -20.0, day_open)],
                                                now)                      # −20 $ de jour sur 322 $ le matin : 6,2 %
    deals = [NS(magic=200001, position_id=1, profit=0.0, commission=-0.1, swap=0.0, time=night_open, entry=0),
             NS(magic=200001, position_id=1, profit=-40.0, commission=-0.1, swap=0.0, time=closed, entry=1)]
    assert dr.closed_trades(deals, 200001, 1, opened=True) == [(closed, -40.2, night_open)]
