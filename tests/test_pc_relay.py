"""PC allumé : le pont annonce lui-même les signaux réels et GitHub se tait (demandé par Yanisse le 19/10/2026)."""
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

from trading_bot import mt5_copy as mc
from trading_bot import pc_link
from trading_bot.pc_relay import Relay

from test_mt5_copy import LocalMT5

T22 = int(datetime(2026, 10, 14, 22, 0, tzinfo=timezone.utc).timestamp())


def test_entry_owner_pc_wait_or_github():
    raw = pc_link.encode(T22 + 60, [{"k": f"lab:nuit_asie:{T22}", "d": "long"}])
    # même signal à une bougie près (prix CFD contre contrats à terme) : déjà annoncé par le PC
    assert pc_link.entry_owner(raw, "nuit_asie", T22 + 300, "long", T22 + 400) == "pc"
    assert pc_link.entry_owner(raw, "nuit_asie", T22, "short", T22 + 400) == "wait"     # pas le même sens
    assert pc_link.entry_owner(raw, "donchian_1h", T22, "long", T22 + 400) == "wait"    # PC vivant : on attend
    assert pc_link.entry_owner(raw, "donchian_1h", T22, "long", T22 + pc_link.WAIT + 1) == "github"
    assert pc_link.entry_owner(raw, "donchian_1h", T22, "long", T22 + 60 + pc_link.FRESH + 1) == "github"
    assert pc_link.entry_owner(None, "nuit_asie", T22, "long", T22 + 60) == "github"     # PC éteint
    assert pc_link.alive(raw, T22 + 120) and not pc_link.alive("pas du json", T22)


class DealsMT5(LocalMT5):
    TIMEFRAME_H1, TIMEFRAME_D1 = 16385, 16408
    DEAL_REASON_SL, DEAL_REASON_TP = 4, 5

    def history_deals_get(self, *a, position=None, **k):
        if position is None:
            return []
        return [NS(profit=0.0, commission=-1.0, swap=0.0, price=4200.2, reason=0, comment=""),
                NS(profit=-48.0, commission=-1.0, swap=0.0, price=4158.0, reason=4, comment="")]


def _relay(tmp_path, mt5, now, agent_dir=None):
    sent, beats, spawned = [], [], []
    ids = iter(range(100, 200))

    def send(token, cid, body, **k):
        sent.append((cid, body, k.get("reply_to")))
        return next(ids)

    class Proc:
        def poll(self):
            return None

        def kill(self):
            spawned.append("tué")

    def spawn(args, **k):
        spawned.append((args, k["cwd"]))
        return Proc()

    env = {"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_CHAT_ID": "1,2", "PONT_GITHUB_TOKEN": "g"}
    agent = {"command": "python avis_direct.py", "dir": str(agent_dir)} if agent_dir else {}
    relay = Relay(mt5, tmp_path, lambda: now[0], agent=agent, env=env, send=send,
                  github=lambda m, url, tok, body: beats.append((m, body)) or 204, spawn=spawn)
    return relay, sent, beats, spawned


def test_pc_announces_entry_then_exit_in_reply_and_launches_the_agent(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1,2")
    now = [datetime(2026, 10, 14, 22, 6, tzinfo=timezone.utc).timestamp()]
    mt5 = DealsMT5(now[0])
    (tmp_path / "agent").mkdir()
    relay, sent, beats, spawned = _relay(tmp_path, mt5, now, agent_dir=tmp_path / "agent")
    get = lambda url: {} if "lab_shadow" in url else {"open_signals": []}
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: now[0], get=get, local=True, relay=relay)
    c.step()
    key = f"lab:nuit_asie:{T22}"
    assert len(mt5.sent) == 1 and c.state[key]["status"] == "ouvert"
    assert len(sent) == 2 and "↗️ ACHAT" in sent[0][1] and "Nuit asiatique" in sent[0][1] and "copié" in sent[0][1]
    # GitHub apprend tout de suite que le PC l'a annoncé
    raw = beats[-1][1]["value"]
    assert pc_link.entry_owner(raw, "nuit_asie", T22, "long", now[0]) == "pc"
    # l'agent part en arrière-plan avec le signal et 24 h de bougies 5 min arrêtées à l'entrée
    args, cwd = spawned[0]
    assert cwd == str(tmp_path / "agent") and args[-2] == "--signal"
    data = json.loads(open(args[-1], encoding="utf-8").read())
    assert data["strategie"] == "nuit_asie" and data["take_profit"] is None and data["telegram_message_ids"] == {"1": 100, "2": 101}
    assert len(data["candles_5m"]) == 288 and data["candles_5m"][-1][0] < T22
    # rien n'est annoncé deux fois
    c.last = 0
    c.step()
    assert len(sent) == 2
    # la position touche son SL chez le courtier : sortie en réponse à l'entrée, avec le résultat MT5
    mt5.pos.clear()
    now[0] += 3600
    mt5.now = now[0]
    c.last = 0
    c.step()
    assert len(sent) == 4 and "❌ PERTE" in sent[2][1] and "SL touché" in sent[2][1] and "−50,00\xa0$" in sent[2][1]
    assert sent[2][2] == 100 and sent[3][2] == 101
    now[0] += 200
    relay.step({}, set(), set())
    assert spawned[-1] == "tué"                                   # l'agent est arrêté après 90 s


def test_pc_stays_silent_without_telegram_token(tmp_path):
    now = [datetime(2026, 10, 14, 22, 6, tzinfo=timezone.utc).timestamp()]
    relay, sent, beats, _ = _relay(tmp_path, DealsMT5(now[0]), now)
    relay.env = {}
    relay.beat()
    relay.entry("lab:nuit_asie:1", {"direction": "long", "entry": 1.0, "stop": 0.1, "asset": "gold"}, {})
    assert sent == [] and beats == []                            # GitHub garde la main


def test_github_is_silent_on_signals_the_pc_announced(tmp_path, monkeypatch):
    from trading_bot import engine as engmod
    from trading_bot.config import load_config
    from trading_bot.portfolio import Portfolio
    from trading_bot.storage import Store
    sent = []
    monkeypatch.setattr(engmod, "notify", lambda text, **k: sent.append(text))
    cfg = load_config()
    eng = engmod.Engine(cfg)
    eng.store = Store(tmp_path)
    eng.portfolio = Portfolio(eng.store, cfg)
    eng.portfolio.data["started_at"] = "2026-10-01T00:00:00Z"
    now = datetime(2026, 10, 8, 14, 10, tzinfo=timezone.utc)
    t0 = int(datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc).timestamp())
    since = datetime(2026, 10, 8, 7, 30, tzinfo=timezone.utc)
    asset = cfg.assets["gold"]

    def trade():
        return {"entry_ts": t0, "direction": "long", "entry": 4000.0, "risk": 10.0, "stop": 3990.0,
                "status": "open", "reason": None, "exit_ts": None, "exit": None, "r_topstep": None}

    # PC vivant, signal pas encore annoncé : GitHub attend
    monkeypatch.setenv("PC_ALIVE", pc_link.encode(now.timestamp() - 30, []))
    t = trade()
    eng._live_signals("donchian_day:gold", asset, [t], since, now)
    assert sent == [] and not t.get("notified_entry")
    # le PC l'a annoncé : GitHub se tait mais tient Topstep, puis se tait aussi à la sortie
    monkeypatch.setenv("PC_ALIVE", pc_link.encode(now.timestamp() - 30, [{"k": f"lab:donchian_day:{t0}", "d": "long"}]))
    eng._live_signals("donchian_day:gold", asset, [t], since, now)
    assert sent == [] and t["notified_entry"] and t["pc"] and t["micros"] == 2
    t.update(status="closed", reason="heure", exit_ts=t0 + 3600, exit=4012.5, r_topstep=1.21)
    later = now + timedelta(hours=1)
    monkeypatch.setenv("PC_ALIVE", pc_link.encode(later.timestamp() - 30, []))
    eng._live_signals("donchian_day:gold", asset, [t], since, later)
    assert sent == [] and t["notified_exit"] and len(eng.topstep().state["journal"]) == 1
    # le PC calcule la stratégie et ne voit pas ce signal sur les prix MT5 : rien, ni à l'entrée ni à la sortie
    monkeypatch.setenv("PC_ALIVE", pc_link.encode(now.timestamp() - 30, [], ok={"donchian_day"}))
    t3 = trade()
    eng._live_signals("donchian_day:gold", asset, [t3], since, now)
    assert sent == [] and t3["pc_absent"]
    monkeypatch.delenv("PC_ALIVE")
    t3.update(status="closed", reason="heure", exit_ts=t0 + 3600, exit=4012.5, r_topstep=1.21)
    n = len(eng.topstep().state["journal"])
    eng._live_signals("donchian_day:gold", asset, [t3], since, later)
    assert sent == [] and t3["notified_exit"] and len(eng.topstep().state["journal"]) == n
    # PC éteint : GitHub annonce tout, comme avant
    t2 = trade()
    eng._live_signals("donchian_day:gold", asset, [t2], since, now)
    assert len(sent) == 1 and "↗️ ACHAT" in sent[0]


def test_github_wakes_the_agent_after_sending_a_real_signal(tmp_path, monkeypatch):
    from trading_bot import notify as nt
    calls = []
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "7")
    monkeypatch.setenv("TRADING_BOT_NOTIFY_DIR", str(tmp_path))
    monkeypatch.setattr(nt, "_telegram", lambda *a, **k: 42)
    monkeypatch.setattr(nt.requests, "post", lambda url, **k: calls.append((url, k["json"])) or NS(status_code=204))
    nt.notify("x", key="lab-nuit_asie-1", avis={"id": "lab-nuit_asie-1", "candles_5m": []})
    assert calls == []                                            # pas de jeton : rien
    monkeypatch.setenv("AGENT_DISPATCH_TOKEN", "d")
    nt.notify("x", key="lab-nuit_asie-1", avis={"id": "lab-nuit_asie-1", "candles_5m": []})
    url, body = calls[0]
    assert url.endswith("/trading-agent/dispatches") and body["event_type"] == "avis"
    assert json.loads(body["client_payload"]["data"])["telegram_message_ids"] == {"7": 42}


def test_pc_prices_decide_for_strategies_the_pc_computes():
    # 20/10 : Donchian 1 h Bitcoin vu par GitHub mais pas sur les prix MT5 : GitHub se tait
    raw = pc_link.encode(T22 + 2 * 3600 - 30, [], ok={"donchian_1h"})
    assert pc_link.entry_owner(raw, "donchian_1h", T22, "short", T22 + 2 * 3600) == "absent"
    assert pc_link.entry_owner(raw, "swing_w3", T22 + 7000, "long", T22 + 7200) == "wait"  # pas calculée sur le PC
    assert pc_link.entry_owner(raw, "donchian_1h", T22, "short", T22 + 2 * 3600 + pc_link.FRESH) == "github"
    assert pc_link.local_strats(pc_link.encode(T22, [])) == set() and pc_link.local_strats(None) == set()


def test_copier_skips_github_signals_the_pc_does_not_see(tmp_path):
    now = [datetime(2026, 10, 14, 22, 6, tzinfo=timezone.utc).timestamp()]
    mt5 = DealsMT5(now[0])
    relay, sent, beats, _ = _relay(tmp_path, mt5, now)
    old = T22 - 5 * 3600                                          # signal GitHub que les prix MT5 ne donnent pas
    trade = {"status": "open", "notified_entry": "2026-10-14T22:04:00Z", "entry_ts": old, "direction": "short",
             "entry": 4200.0, "risk": 10.0}
    lab = {"nuit_asie:gold": {"strategy": "nuit_asie", "asset": "gold", "trades": [trade]}}
    get = lambda url: lab if "lab_shadow" in url else {"open_signals": []}
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: now[0], get=get, local=True, relay=relay)
    c.step()
    assert c.state[f"lab:nuit_asie:{old}"]["status"] == "pas de signal sur les prix MT5"
    assert len(mt5.sent) == 1                                     # seule la copie du signal calculé sur le PC
    assert relay.local_ok == {"nuit_asie"}
    now[0] += 61                                                  # battement suivant : GitHub apprend la liste
    mt5.now = now[0]
    c.last = 0
    c.step()
    assert pc_link.local_strats(beats[-1][1]["value"]) == {"nuit_asie"}
    # GitHub l'a marqué « absent » : il n'est même plus lu
    trade["pc_absent"] = True
    assert all(s["key"] != f"lab:nuit_asie:{old}" for s in mc.read_signals(get)[0])


def test_demo_snapshot_is_published_without_tickets_once_a_minute_when_it_changes():
    import json as _json
    from types import SimpleNamespace as _NS
    from trading_bot import pc_relay as pr
    puts, now = [], [1000.0]
    r = pr.Relay.__new__(pr.Relay)
    r.clock, r.env, r.last_demo, r.sent_demo = lambda: now[0], {"PONT_GITHUB_TOKEN": "t"}, 0.0, ""
    r.github = lambda method, url, tok, body=None: (puts.append((method, url, body)), 204)[1]
    snap = {"updated_at": "2026-10-28T10:00:00Z", "demo": True, "balance": 100.0, "equity": 101.0, "profit": 1.0,
            "positions": [{"ticket": 7, "symbol": "NAS100", "side": "achat", "comment": "lab:bot:1", "profit": 1.0}],
            "deals": [{"ticket": 8, "symbol": "XAUUSD+", "comment": "x", "profit": 2.0, "closed": 5}]}
    r.demo(snap)
    sent = _json.loads(puts[0][2]["value"])
    assert puts[0][1].endswith("/variables/PC_DEMO") and sent["balance"] == 100.0 and sent["updated_at"]
    assert "ticket" not in sent["positions"][0] and "comment" not in sent["deals"][0]
    now[0] += 30
    r.demo(snap)
    assert len(puts) == 1                                           # moins d'une minute
    now[0] += 61
    r.demo(dict(snap, updated_at="2026-10-28T10:02:00Z"))
    assert len(puts) == 1                                           # rien n'a changé (l'heure seule ne compte pas)
    now[0] += 61
    r.demo(dict(snap, equity=105.0))
    assert len(puts) == 2
    r.demo(dict(snap, demo=False, equity=1.0))
    now[0] += 61
    r.demo(dict(snap, demo=False, equity=2.0))
    assert len(puts) == 2                                           # jamais un compte réel
