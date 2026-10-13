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
