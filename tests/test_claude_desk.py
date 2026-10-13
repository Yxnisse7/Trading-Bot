from trading_bot.claude_desk import lot_for


def test_lot_risks_one_percent_and_stays_in_bounds():
    assert lot_for(1000, 3.0) == 0.03          # 3 $ de stop × 0,03 lot × 100 onces = 9 $ ≤ 10 $
    assert lot_for(1000, 8.0) == 0.01
    assert lot_for(1000, 0.5) == 0.10          # plafond
    assert lot_for(100, 8.0) == 0.01           # plancher
