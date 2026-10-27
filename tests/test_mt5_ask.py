"""Questions à l'agent IA depuis Telegram : /avis (27/10/2026)."""
import json
from datetime import datetime, timezone
from types import SimpleNamespace as NS

from trading_bot import ask
from trading_bot import mt5_ask as ma
from test_mt5_hunt import FakeMT5

MON16 = int(datetime(2026, 10, 26, 15, 0, 20, tzinfo=timezone.utc).timestamp())


def test_parse_and_asset():
    assert ma.parse("/avis ton avis sur le nasdaq ?") == "ton avis sur le nasdaq ?"
    assert ma.parse("/AVIS@MonBot  l'or monte, je garde ?") == "l'or monte, je garde ?"
    assert ma.parse("/avis") == "" and ma.parse("/hugo") is None and ma.parse("avis nasdaq") is None
    assert ma.asset_of("ton avis sur le Nasdaq", []) == "nasdaq" and ma.asset_of("le BTC rebondit ?", []) == "bitcoin"
    assert ma.asset_of("l'or va monter ?", []) == "gold"
    assert ma.asset_of("je garde ?", [{"asset": "gold"}]) == "gold"       # sans marché cité : celui de la position
    assert ma.asset_of("je garde ?", []) == "nasdaq"


def test_agent_message_and_decide():
    m = {"now": "2026-10-26T15:00:00Z", "ask": 29400.5, "bid": 29400.0, "asset_label": "Nasdaq 100",
         "question": "je garde ou je sécurise ?",
         "positions": [{"marche": "Nasdaq 100", "sens": "vente", "lot": 0.1, "entree": 29470.0, "stop": 29595.0,
                        "objectif": 29150.0, "profit": 7.5, "origine": "l'agent IA (chasse)"}]}
    seen = {}

    def call(message, consigne, schema, timeout):
        seen.update(message=message, consigne=consigne)
        return {"structured_output": {"conseil": "securiser", "reponse": "Remonte le stop à 29 470."}}
    r = ask.decide(m, call)
    assert r == {"conseil": "securiser", "reponse": "Remonte le stop à 29 470."}
    assert "je garde ou je sécurise ?" in seen["message"] and "vente 0.1 lot" in seen["message"]
    assert "aucun ordre" in seen["consigne"]
    assert ask.check({"conseil": "n'importe quoi", "reponse": "Ok."})["conseil"] == "autre"
    assert "Pas de réponse" in ask.check({"conseil": "garder", "reponse": " "})["reponse"]
    assert ask.decide(m, lambda *a: None)["conseil"] == "autre"


def _setup(tmp_path, monkeypatch, answers, updates):
    monkeypatch.setattr(ma, "telegram_chat_ids", lambda: ["42"])
    now = [MON16]
    mt5 = FakeMT5(now)
    mt5.positions = [NS(symbol="NAS100", type=1, volume=0.1, price_open=29470.0, sl=29595.0, tp=29150.0, profit=7.5,
                        swap=0.0, magic=777002)]
    bot, agent = tmp_path / "bot", tmp_path / "agent"
    (bot / "trading_bot").mkdir(parents=True)
    (bot / "trading_bot" / "ask.py").write_text("")
    agent.mkdir()
    (agent / "ia.py").write_text("")
    sent = []

    class Relay:
        token = "x"

        def enabled(self):
            return True

        def _post(self, body, reply=None):
            sent.append(body)
            return {"42": 1}

    class Proc:
        def poll(self):
            return 0

    data = []

    def spawn(args, cwd, stdout, **k):
        data.append(json.loads(open(args[-1]).read()))
        stdout.write(json.dumps(answers.pop(0)) + "\n")
        stdout.close()
        return Proc()

    a = ma.Asker(mt5, tmp_path, lambda: now[0], relay=Relay(), spawn=spawn, updates=lambda tok: list(updates),
                 cfg={"command": "python -m trading_bot.ask", "dir": str(bot), "agent_dir": str(agent)})
    return a, mt5, now, sent, data


def test_question_is_answered_with_positions_and_no_order(tmp_path, monkeypatch):
    rep = {"conseil": "securiser", "reponse": "Tendance haussière à court terme, remonte ton stop à 29 470."}
    upd = [{"update_id": 5, "message": {"text": "/avis ton avis sur le nasdaq, je garde ou je sécurise ?",
                                        "chat": {"id": 42}, "date": MON16 - 5}},
           {"update_id": 6, "message": {"text": "/avis ancien", "chat": {"id": 42}, "date": MON16 - 3600}},
           {"update_id": 7, "message": {"text": "/avis hacker", "chat": {"id": 99}, "date": MON16 - 5}},
           {"update_id": 8, "message": {"text": "/hugo", "chat": {"id": 42}, "date": MON16 - 5}}]
    a, mt5, now, sent, data = _setup(tmp_path, monkeypatch, [rep], upd)
    assert a.step() == "question : agent réveillé (nasdaq)"
    assert a.state["tg_seen"] == 8 and len(data) == 1
    assert data[0]["question"].startswith("ton avis sur le nasdaq") and data[0]["asset"] == "nasdaq"
    assert data[0]["positions"][0]["sens"] == "vente" and data[0]["positions"][0]["origine"] == "l'agent IA (chasse)"
    assert data[0]["candles_1h"] and "Je regarde" in sent[-1]
    a.step()
    assert "Sécuriser" in sent[-1] and "remonte ton stop à 29 470" in sent[-1] and "Un avis, pas un ordre" in sent[-1]
    assert mt5.orders == []                                                  # jamais d'ordre


def test_empty_question_and_queue_limit(tmp_path, monkeypatch):
    upd = [{"update_id": 1, "message": {"text": "/avis", "chat": {"id": 42}, "date": MON16 - 5}}]
    a, mt5, now, sent, data = _setup(tmp_path, monkeypatch, [], upd)
    a.step()
    assert "Écris ta question" in sent[-1] and not data
    upd.clear()
    upd += [{"update_id": 2 + i, "message": {"text": f"/avis question {i}", "chat": {"id": 42}, "date": MON16 - 1}}
            for i in range(5)]
    a.queue.clear()
    a.last_poll = 0
    a.proc = (NS(poll=lambda: None), MON16, "x", tmp_path / "x.log", {})                # une analyse déjà en cours
    a.step()
    assert len(a.queue) == 3 and "Trois questions attendent" in sent[-1]


def test_closed_market_uses_last_known_price_and_candles(tmp_path, monkeypatch):
    rep = {"conseil": "garder", "reponse": "Marché fermé, je garde."}
    upd = [{"update_id": 5, "message": {"text": "/avis nasdaq, je garde ?", "chat": {"id": 42}, "date": MON16 - 5}}]
    a, mt5, now, sent, data = _setup(tmp_path, monkeypatch, [rep, rep], upd)
    mt5.symbol_info_tick = lambda s: NS(time=now[0] + 10800 - 11000, bid=29400.0, ask=29400.5)   # cotation vieille de 3 h
    a.state["off"] = 10800
    assert a.step() == "question : agent réveillé (nasdaq)"
    assert data[0]["ferme"].startswith("marché fermé") and data[0]["bid"] == 29400.0 and data[0]["candles_5m"]
    assert "ATTENTION : marché fermé" in ask.message(data[0])
    assert "marché fermé" not in ask.message(dict(data[0], ferme=""))
    mt5.symbol_info_tick = lambda s: None                                  # aucune cotation : on prend la dernière bougie
    a.queue.append("nasdaq ?")
    a.proc = None
    a.step()
    assert data[-1]["bid"] == data[-1]["candles_5m"][-1][4]
