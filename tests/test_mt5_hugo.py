"""Méthode Hugo de l'agent IA sur le Nasdaq démo : heures fixes, /hugo sur Telegram, règles de journée (20/10/2026)."""
import json
from datetime import datetime, timezone
from types import SimpleNamespace as NS

from trading_bot import hugo
from trading_bot import mt5_hugo as mg
from test_mt5_hunt import FakeMT5

MON9 = int(datetime(2026, 10, 19, 7, 0, 20, tzinfo=timezone.utc).timestamp())     # lundi 9h00 Paris


def test_agent_check_and_decide():
    m = {"ask": 25000.5, "bid": 25000.0, "now": "2026-10-19T07:00:00Z"}
    ok = {"action": "achat", "stop": 24980.0, "objectif": 25041.0, "confiance": 4, "raison": "BPR 5 min.", "a_surveiller": ""}
    assert hugo.check(m, ok)["action"] == "achat"
    assert hugo.check(m, {**ok, "objectif": 25020.0})["action"] == "rien"          # moins de 1,5 R
    assert hugo.check(m, {**ok, "confiance": 2})["action"] == "rien"
    w = hugo.check(m, {"action": "rien", "stop": None, "objectif": None, "confiance": 2, "raison": "Rien de net.",
                       "a_surveiller": "FVG H1 vers 24 950 avant 11h."})
    assert w["a_surveiller"].startswith("FVG H1")
    seen = {}

    def call(message, consigne, schema, timeout):
        seen.update(message=message, consigne=consigne)
        return {"structured_output": ok}
    assert hugo.decide({**m, "candles_4h": [[1760853600, 1, 2, 0.5, 1.5]]}, call)["stop"] == 24980.0
    assert "Bougies 4 h" in seen["message"] and "BPR" in seen["consigne"]


class MT5(FakeMT5):
    TIMEFRAME_H4 = 16388

    def account_info(self):
        return NS(trade_mode=0, balance=1000.0)

    def symbol_info(self, s):
        return NS(digits=2, trade_stops_level=0, point=0.01, trade_tick_size=0.01, trade_tick_value=0.01,
                  volume_step=0.01, volume_min=0.01, filling_mode=1)


def _setup(tmp_path, monkeypatch, answers, updates=()):
    monkeypatch.setattr(mg, "telegram_chat_ids", lambda: ["42"])
    now = [MON9]
    mt5 = MT5(now)
    bot, agent = tmp_path / "bot", tmp_path / "agent"
    (bot / "trading_bot").mkdir(parents=True)
    (bot / "trading_bot" / "hugo.py").write_text("")
    agent.mkdir()
    (agent / "ia.py").write_text("")
    sent, ids = [], iter(range(10, 99))

    class Relay:
        token = "x"

        def enabled(self):
            return True

        def _post(self, body, reply=None):
            sent.append((body, reply))
            return {"42": next(ids)}

    class Proc:
        def poll(self):
            return 0

    data = []

    def spawn(args, cwd, stdout, **k):
        data.append(json.loads(open(args[-1]).read()))
        stdout.write(json.dumps(answers.pop(0)) + "\n")
        stdout.close()
        return Proc()

    h = mg.HugoHunter(mt5, tmp_path, lambda: now[0], relay=Relay(), spawn=spawn, updates=lambda tok: list(updates),
                      cfg={"command": "python -m trading_bot.hugo", "dir": str(bot), "agent_dir": str(agent)})
    return h, mt5, now, sent, data


def test_hugo_command_answers_even_without_trade(tmp_path, monkeypatch):
    rien = {"action": "rien", "stop": None, "objectif": None, "confiance": 2, "raison": "Pas de réaction sur la zone.",
            "a_surveiller": "FVG H1 vers 24 950, attendre un BPR 5 min avant 11h."}
    upd = [{"update_id": 7, "message": {"text": "/hugo", "chat": {"id": 42}, "date": MON9 - 3600 * 2}},   # 9h passé : 7h Paris
           {"update_id": 8, "message": {"text": "/help", "chat": {"id": 42}, "date": MON9}}]
    h, mt5, now, sent, data = _setup(tmp_path, monkeypatch, [rien], upd)
    now[0] = MON9 + 3600 * 9                     # 18h : pas de réveil prévu ; /hugo trop ancien → ignoré
    assert h.step() == "" and h.state["tg_seen"] == 8
    upd.append({"update_id": 9, "message": {"text": "/hugo@MonBot", "chat": {"id": 42}, "date": now[0] - 5}})
    h.last_poll = 0
    assert "agent réveillé" in h.step()
    assert data[0]["methode"] == "hugo" and data[0]["candles_4h"] and data[0]["moment"] == "demande /hugo"
    h.step()
    assert "À surveiller : FVG H1" in sent[-1][0] and not mt5.orders


def test_schedule_order_day_rule_and_virtual_topstep(tmp_path, monkeypatch):
    buy = {"action": "achat", "stop": 25000.0, "objectif": 25040.0, "confiance": 4, "raison": "BPR 5 min.", "a_surveiller": ""}
    h, mt5, now, sent, data = _setup(tmp_path, monkeypatch, [buy])
    mt5.symbol_info_tick = lambda s: NS(time=now[0], bid=25010.0, ask=25010.0)
    assert h.step() == "chasse : agent réveillé (nasdaq, matin)"
    h.step()
    o = mt5.orders[-1]
    assert o["magic"] == 777003 and o["comment"] == "hugo IA" and o["volume"] == 1.0          # 10 $ / 10 pts
    assert "Méthode Hugo (agent IA)" in sent[-1][0]
    mt5.deals = [NS(profit=0.0, commission=0.0, swap=0.0, price=25010.0), NS(profit=30.0, commission=0.0, swap=0.0, price=25040.0)]
    h.step()
    out = sent[-1][0]
    assert "1 gain(s), 0 perte(s) aujourd'hui : journée terminée" in out and "Topstep 50K virtuel n°1 : 50\xa0900 $" in out
    assert not h.may_trade("nasdaq", now[0])
    now[0] = MON9 + 3600                         # 10h : réveil sauté, la journée est finie
    assert h.step() == ""
