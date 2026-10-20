"""L'agent IA cherche des trades sur l'or à heures fixes et le pont les passe sur le démo (demandé par Yanisse le 20/10)."""
import json
from datetime import datetime, timezone
from types import SimpleNamespace as NS

import numpy as np

from trading_bot import mt5_hunt as mh

MON = datetime(2026, 10, 19, 7, 5, tzinfo=timezone.utc)          # lundi 9h05 Paris
T0 = int(MON.timestamp())


def test_slots_weekdays_news_and_dedupe():
    news = [{"name": "USD CPI m/m", "at": "2026-10-19T12:30:00+00:00", "impact": "high"},
            {"name": "USD Retail Sales", "at": "2026-10-19T09:00:00+00:00", "impact": "medium"},
            {"name": "EUR CPI", "at": "2026-10-19T09:00:00+00:00", "impact": "high"}]
    s = mh.slots(MON, news)
    paris = [datetime.fromtimestamp(t, mh.PARIS).strftime("%H:%M") for t, _ in s]
    assert paris == ["09:05", "14:35", "14:50", "15:35"]           # annonce forte de 14h30 + 20 min
    news[0]["at"] = "2026-10-19T13:20:00+00:00"                     # 15h40 : à moins de 15 min de 15h35, un seul
    assert len(mh.slots(MON, news)) == 3
    news[0]["at"] = "2026-10-19T16:00:00+00:00"
    assert [n for _, n in mh.slots(MON, news)][-1] == "après annonce : CPI m/m"
    assert mh.slots(datetime(2026, 10, 18, 9, tzinfo=timezone.utc), news) == []   # dimanche
    nq = [datetime.fromtimestamp(t, mh.PARIS).strftime("%H:%M") for t, _ in mh.slots(MON, news[:1], "nasdaq")]
    assert nq == ["15:50", "18:20"]


def test_lot_uses_broker_point_value():
    nas = NS(trade_tick_size=0.01, trade_tick_value=0.01, volume_step=0.01, volume_min=0.01)   # 1 $ par point et par lot
    assert mh.Hunter.lot(1000.0, 25.0, nas, 2.0) == 0.4                                         # 10 $ / 25 pts
    gold = NS(trade_tick_size=0.01, trade_tick_value=1.0, volume_step=0.01, volume_min=0.01)   # 100 $ par $ et par lot
    assert mh.Hunter.lot(1000.0, 5.0, gold, 0.10) == 0.02


def test_check_refuses_bad_answers():
    h = mh.Hunter.__new__(mh.Hunter)
    ok = {"action": "achat", "stop": 4100, "objectif": 4130, "confiance": 4}
    assert h.check(ok, 4110, 4109.9, 2.0) is None
    assert h.check({**ok, "action": "rien"}, 4110, 4109.9, 2.0) == "rien à faire"
    assert "confiance" in h.check({**ok, "confiance": 2}, 4110, 4109.9, 2.0)
    assert "mauvais côté" in h.check({**ok, "stop": 4120}, 4110, 4109.9, 2.0)
    assert "< risque" in h.check({**ok, "objectif": 4115}, 4110, 4109.9, 2.0)
    assert h.check({"action": "vente", "stop": 4120, "objectif": 4095, "confiance": 3}, 4110.1, 4110, 2.0) is None


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO, TRADE_ACTION_DEAL, ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1, 0, 1
    ORDER_TIME_GTC, TRADE_RETCODE_DONE, POSITION_TYPE_BUY = 0, 10009, 0
    ORDER_FILLING_FOK, ORDER_FILLING_IOC, ORDER_FILLING_RETURN = 0, 1, 2
    TIMEFRAME_M5, TIMEFRAME_M15, TIMEFRAME_H1, TIMEFRAME_D1 = 5, 15, 16385, 16408

    def __init__(self, now):
        self.now, self.orders, self.positions, self.deals = now, [], [], []

    def account_info(self):
        return NS(trade_mode=0, balance=1000.0)

    def symbol_info_tick(self, s):
        return NS(time=self.now[0], bid=4110.0, ask=4110.1)

    def symbol_info(self, s):
        return NS(digits=2, trade_stops_level=20, point=0.01, trade_contract_size=100.0, filling_mode=1)

    def copy_rates_from_pos(self, s, tf, start, n):
        a = np.zeros(n, dtype=[("time", "i8"), ("open", "f8"), ("high", "f8"), ("low", "f8"), ("close", "f8")])
        a["time"] = self.now[0] - np.arange(n)[::-1] * 300
        a["open"] = a["high"] = a["low"] = a["close"] = 4110.0
        return a

    def history_deals_get(self, *a, position=None, **k):
        return self.deals if position is not None else []

    def symbol_select(self, s, on):
        return True

    def positions_get(self, symbol=None):
        return self.positions

    def order_send(self, req):
        self.orders.append(req)
        return NS(retcode=10009, price=req["price"], order=555)


def test_wake_order_and_exit(tmp_path):
    now = [T0 + 30]
    mt5 = FakeMT5(now)
    agent = tmp_path / "agent"
    (agent / "agent").mkdir(parents=True)
    (agent / "agent" / "chasse.py").write_text("")
    sent, ids = [], iter(range(10, 99))

    class Relay:
        def enabled(self):
            return True

        def _post(self, body, reply=None):
            sent.append((body, reply))
            return {"1": next(ids)}

    answer = {"action": "achat", "stop": 4100.0, "objectif": 4130.0, "confiance": 4, "raison": "Repli sur la MM20 en tendance."}

    class Proc:
        def poll(self):
            return 0

    def spawn(args, cwd, stdout, **k):
        assert args[-2] == "--marche" and json.loads(open(args[-1]).read())["moment"] == "ouverture de Londres"
        stdout.write("préparation...\n" + json.dumps(answer) + "\n")
        stdout.close()
        return Proc()

    h = mh.Hunter(mt5, tmp_path, lambda: now[0], relay=Relay(),
                  cfg={"command": f"python {agent / 'agent' / 'chasse.py'}", "dir": str(agent)}, spawn=spawn)
    assert h.step() == "chasse : agent réveillé (gold, ouverture de Londres)"
    h.step()                                                       # réponse lue, ordre passé
    o = mt5.orders[-1]
    assert o["magic"] == mh.MAGIC and o["sl"] == 4100.0 and o["tp"] == 4130.0 and o["volume"] == 0.01
    assert "Trade de l'agent IA" in sent[0][0] and "Repli sur la MM20" in sent[0][0]
    assert h.step() == ""                                          # même réveil : pas deux fois
    mt5.positions = [NS(magic=mh.MAGIC, ticket=555, type=0, volume=0.01)]
    h.step()
    mt5.positions = []
    mt5.deals = [NS(profit=0.0, commission=-0.3, swap=0.0, price=4110.1), NS(profit=19.9, commission=-0.3, swap=0.0, price=4130.0)]
    h.step()
    assert "Sortie" in sent[-1][0] and sent[-1][1] == {"1": 10} and h.state["trades"] == {}


def test_nothing_without_agent_file(tmp_path):
    now = [T0 + 30]
    h = mh.Hunter(FakeMT5(now), tmp_path, lambda: now[0], cfg={"command": "python absent.py", "dir": str(tmp_path)},
                  spawn=lambda *a, **k: 1 / 0)
    assert h.step() == ""
