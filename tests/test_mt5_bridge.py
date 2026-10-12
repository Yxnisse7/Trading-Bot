from datetime import datetime, timezone
from types import SimpleNamespace as NS

import pytest

from trading_bot import essai18 as e18
from trading_bot import mt5_bridge as mb
from trading_bot.agent_hook import Agent

NOW = int(datetime(2026, 10, 13, 13, 0, 5, tzinfo=timezone.utc).timestamp())   # mardi 9:00 à New York
OFFSET = 3 * 3600                                                                # serveur en UTC+3


class FakeMT5:
    TIMEFRAME_M1 = 1
    ACCOUNT_TRADE_MODE_DEMO, ACCOUNT_TRADE_MODE_REAL = 0, 2
    POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1
    ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1
    TRADE_ACTION_DEAL, ORDER_TIME_GTC = 1, 0
    ORDER_FILLING_FOK, ORDER_FILLING_IOC, ORDER_FILLING_RETURN = 0, 1, 2
    TRADE_RETCODE_DONE = 10009

    def __init__(self, demo=True):
        self.mode = 0 if demo else 2
        self.sent, self.positions, self.deals = [], [], []

    def symbol_info_tick(self, sym):
        return NS(time=NOW + OFFSET, bid=4100.0, ask=4100.2)

    def copy_rates_from_pos(self, sym, tf, start, n):
        t0 = NOW - NOW % 60 - 60 * (n - 1)
        return [{"time": t0 + 60 * k + OFFSET, "open": 4100, "high": 4101, "low": 4099, "close": 4100,
                 "tick_volume": 10} for k in range(n)]

    def account_info(self):
        return NS(trade_mode=self.mode)

    def positions_get(self, symbol):
        return self.positions

    def history_deals_get(self, lo, hi):
        return self.deals

    def symbol_info(self, sym):
        return NS(filling_mode=1, digits=2, trade_stops_level=0, point=0.01)

    def order_send(self, req):
        self.sent.append(req)
        return NS(retcode=self.TRADE_RETCODE_DONE, price=req["price"])


@pytest.fixture
def forced_buy(monkeypatch):
    monkeypatch.setattr(e18, "signal", lambda entry, x, i: 1)
    monkeypatch.setattr(e18, "plan", lambda x, i, d, px: (px - 3.0, 3.0))


def bridge(tmp_path, mt5, mode):
    cfg = mb.load_config(tmp_path)
    cfg.update(mode=mode, bars=200)
    return mb.Bridge(mt5, cfg, tmp_path, clock=lambda: NOW)


def test_observe_mode_never_sends_orders(tmp_path, forced_buy):
    mt5 = FakeMT5()
    assert bridge(tmp_path, mt5, "observe").step() == "observé"
    assert mt5.sent == []
    assert "observé" in next((tmp_path / "journal").glob("*.csv")).read_text(encoding="utf-8")


def test_demo_mode_refuses_a_real_account(tmp_path, forced_buy):
    mt5 = FakeMT5(demo=False)
    assert bridge(tmp_path, mt5, "demo").step() == "compte réel refusé"
    assert mt5.sent == []


def test_demo_order_has_stop_and_one_r_target(tmp_path, forced_buy):
    mt5 = FakeMT5()
    assert bridge(tmp_path, mt5, "demo").step() == "entrée"
    req = mt5.sent[0]
    assert req["volume"] == 0.01 and req["sl"] == 4097.2 and req["tp"] == 4103.2


def test_daily_loss_limit_stops_trading(tmp_path, forced_buy):
    mt5 = FakeMT5()
    mt5.deals = [NS(magic=180018, time=NOW + OFFSET - 600, profit=-11.0, commission=0.0, swap=0.0)]
    assert bridge(tmp_path, mt5, "demo").step() == "limite du jour"
    assert mt5.sent == []


def test_position_closed_after_one_hour(tmp_path):
    mt5 = FakeMT5()
    mt5.positions = [NS(magic=180018, time=NOW + OFFSET - 3700, type=0, volume=0.01, ticket=7)]
    assert bridge(tmp_path, mt5, "demo").step() == "position ouverte"
    assert mt5.sent[0]["position"] == 7 and mt5.sent[0]["type"] == FakeMT5.ORDER_TYPE_SELL


def test_stale_feed_does_nothing(tmp_path, forced_buy):
    mt5 = FakeMT5()
    b = bridge(tmp_path, mt5, "demo")
    b.clock = lambda: NOW + 600
    assert b.step() == "flux arrêté" and mt5.sent == []


def test_agent_is_off_without_key(tmp_path):
    a = Agent({"enabled": True, "model": "x", "library": ""}, tmp_path, env={})
    assert not a.enabled and a.ask({}) == (True, "agent inactif")


def test_no_quote_means_no_trading(tmp_path, forced_buy):
    mt5 = FakeMT5()
    mt5.symbol_info_tick = lambda sym: NS(time=0, bid=0.0, ask=0.0)
    assert bridge(tmp_path, mt5, "demo").step() == "flux arrêté" and mt5.sent == []
