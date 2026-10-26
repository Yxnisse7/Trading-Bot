"""Copie sur le démo des trades postés dans des canaux Telegram (demandé par Yanisse le 23/10/2026)."""
import json
from types import SimpleNamespace as NS

from trading_bot import mt5_tgcopy as tc
from trading_bot import tg_listen, tg_parse

T0 = 1792744800


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO, TRADE_ACTION_DEAL, ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1, 0, 1
    ORDER_TIME_GTC, TRADE_RETCODE_DONE, POSITION_TYPE_BUY = 0, 10009, 0
    ORDER_FILLING_FOK, ORDER_FILLING_IOC, ORDER_FILLING_RETURN = 0, 1, 2
    TRADE_ACTION_PENDING, TRADE_ACTION_REMOVE, TRADE_ACTION_SLTP, TRADE_ACTION_MODIFY = 5, 8, 6, 7
    ORDER_TYPE_BUY_LIMIT, ORDER_TYPE_SELL_LIMIT = 2, 3

    def __init__(self):
        self.sent, self.positions, self.pending, self.deals, self.n = [], [], [], {}, 100
        self.bid = 4110.0

    def account_info(self):
        return NS(trade_mode=0, balance=1000.0)

    def symbol_select(self, s, on):
        return True

    def symbol_info_tick(self, s):
        return NS(bid=self.bid, ask=self.bid + 0.1) if s == "XAUUSD+" else None

    def symbol_info(self, s):
        return NS(digits=2, trade_stops_level=20, point=0.01, trade_tick_size=0.01, trade_tick_value=1.0,
                  volume_step=0.01, volume_min=0.01, filling_mode=1)

    def history_deals_get(self, *a, position=None, **k):
        return self.deals.get(position, []) if position is not None else []

    def positions_get(self, symbol=None):
        return self.positions

    def orders_get(self, symbol=None):
        return self.pending

    def order_send(self, req):
        self.sent.append(req)
        self.n += 1
        if req["action"] == self.TRADE_ACTION_PENDING:
            self.pending.append(NS(ticket=self.n, price_open=req["price"], tp=req["tp"]))
        if req["action"] == self.TRADE_ACTION_REMOVE:
            self.pending = [o for o in self.pending if o.ticket != req["order"]]
        return NS(retcode=10009, price=req.get("price"), order=self.n)


def make(tmp_path, answers, now, claude=True):
    bot = tmp_path / "bot"
    (bot / "trading_bot").mkdir(parents=True)
    (bot / "trading_bot" / "tg_parse.py").write_text("")
    agent = tmp_path / "agent"
    agent.mkdir()
    (agent / "ia.py").write_text("")
    sess = tmp_path / "telegram"
    sess.mkdir()
    (sess / "yanisse.session").write_text("")
    sent, ids = [], iter(range(10, 99))
    reviews = []

    class Relay:
        def enabled(self):
            return True

        def _post(self, body, reply=None):
            sent.append((body, reply))
            return {"1": next(ids)}

        def _agent(self, key, s, sym, stop, target, ids, sortie=None, ticket=None):
            reviews.append((key, s, stop, target, ids, sortie))

    def spawn(args, cwd, stdout, **k):
        if "--message" in args:
            stdout.write(json.dumps(answers.pop(0)) + "\n")
        stdout.close()
        return NS(poll=lambda: 0 if "--message" in args else None, kill=lambda: None)

    mt5 = FakeMT5()
    c = tc.TgCopier(mt5, tmp_path, lambda: now[0], relay=Relay(), spawn=spawn,
                    cfg={"channels": ["Gold VIP"], "claude": claude, "dir": str(bot), "agent_dir": str(agent), "session_dir": str(sess)})
    c.reviews = reviews
    return c, mt5, sent


def post(tmp_path, msg_id, text, now, reply_to=None):
    tg_listen.record(tmp_path, -100123, "Gold VIP", msg_id, text, reply_to, now, False)


def test_open_split_be_and_exit(tmp_path):
    now = [T0]
    ans = [{"type": "ouverture", "marche": "gold", "sens": "achat", "entree": 4110.5, "stop": 4101.0,
            "objectifs": [4115.0, 4120.0, 4130.0], "signal": None, "raison": "achat or"},
           {"type": "stop", "marche": None, "sens": None, "entree": None, "stop": 4110.1, "objectifs": [],
            "signal": "100123-7", "raison": "BE"}]
    c, mt5, sent = make(tmp_path, ans, now)
    post(tmp_path, 7, "GOLD BUY NOW 4110 SL 4101 TP1 4115 TP2 4120 TP3 4130", now[0])
    post(tmp_path, 8, "Bonne journée à tous", now[0])
    assert "message lu" in c.step() and c.listener is not None      # écoute lancée, message envoyé à Claude
    c.step()                                                          # réponse lue : 3 ordres au marché
    deals = [r for r in mt5.sent if r["action"] == mt5.TRADE_ACTION_DEAL]
    assert [r["tp"] for r in deals] == [4115.0, 4120.0, 4130.0] and all(r["sl"] == 4101.0 for r in deals)
    assert sum(r["volume"] for r in deals) == 0.03 and all(r["magic"] == tc.MAGIC for r in deals)
    assert "ACHAT" in sent[0][0] and "Gold VIP" in sent[0][0] and "TP3" in sent[0][0]
    key, s0, stop, target, ids_, sortie = c.reviews[0]                # avis de l'agent IA sous l'annonce
    assert key == "tg:copie_telegram:100123-7" and s0["direction"] == "long" and stop == 4101.0 and target == 4115.0
    assert ids_ == {"1": 10} and "Gold VIP" in sortie
    tickets = c.state["signals"]["100123-7"]["tickets"]
    mt5.positions = [NS(magic=tc.MAGIC, ticket=t, type=0, volume=0.01, tp=0.0) for t in tickets]
    c.step()                                                          # « bonne journée » : pas envoyé à Claude
    mt5.bid = 4114.0
    post(tmp_path, 9, "SL au BE !", now[0], reply_to=7)
    c.step()
    c.step()
    sl = [r for r in mt5.sent if r["action"] == mt5.TRADE_ACTION_SLTP]
    assert len(sl) == 3 and sl[0]["sl"] == 4110.1 and "(BE)" in sent[-1][0] and sent[-1][1] == {"1": 10}
    mt5.positions = []
    mt5.deals = {t: [NS(profit=0.0, commission=-0.1, swap=0.0), NS(profit=5.0, commission=-0.1, swap=0.0)]
                 for t in tickets}
    c.step()
    assert "Sortie" in sent[-1][0] and "+14,40 $" in sent[-1][0] and c.state["signals"] == {}


def test_limit_when_price_ran_and_refusals(tmp_path):
    now = [T0]
    ans = [{"type": "ouverture", "marche": "gold", "sens": "achat", "entree": 4100.0, "stop": 4092.0,
            "objectifs": [4120.0], "signal": None, "raison": ""},
           {"type": "ouverture", "marche": "gold", "sens": "vente", "entree": None, "stop": 4100.0,
            "objectifs": [], "signal": None, "raison": ""}]
    c, mt5, sent = make(tmp_path, ans, now)
    post(tmp_path, 20, "buy gold 4100 sl 4092 tp 4120", now[0])
    c.step()
    c.step()
    o = mt5.sent[-1]
    assert o["action"] == mt5.TRADE_ACTION_PENDING and o["type"] == mt5.ORDER_TYPE_BUY_LIMIT and o["price"] == 4100.0
    assert "LIMITE" in sent[-1][0]
    post(tmp_path, 21, "sell gold now sl 4100", now[0])
    c.step()
    c.step()
    assert "pas copié" in sent[-1][0] and "stop" in sent[-1][0]                 # stop sous le prix pour une vente
    now[0] += tc.PENDING_MAX + 1
    c.step()
    assert mt5.sent[-1]["action"] == mt5.TRADE_ACTION_REMOVE
    c.step()
    assert "Annulé" in sent[-1][0] and c.state["signals"] == {}


def test_old_messages_and_no_session(tmp_path):
    now = [T0]
    c, mt5, sent = make(tmp_path, [], now)
    post(tmp_path, 30, "BUY GOLD 4110 SL 4100", now[0] - tc.MAX_AGE - 5)
    c.step()
    assert c.proc is None and not list((tmp_path / "journal" / "tg_inbox").glob("*.json"))
    (tmp_path / "telegram" / "yanisse.session").unlink()
    c.listener = None
    assert "pas encore connecté" in c.step()


def test_lots_split_and_floor():
    info = NS(trade_tick_size=0.01, trade_tick_value=1.0, volume_step=0.01, volume_min=0.01)
    assert tc.TgCopier.lots(1000.0, 3.0, info, 3, 0.01) == [0.01, 0.01, 0.01]   # 10 $ / 300 $ par lot → 0,033
    assert tc.TgCopier.lots(1000.0, 8.0, info, 3, 0.01) == [0.01] * 3            # 3 × 0,01 lot = 24 $ ≤ 3 %
    assert tc.TgCopier.lots(1000.0, 12.0, info, 3, 0.01) == [0.01] * 2           # 3 × 12 $ > 30 $ : deux objectifs
    assert tc.TgCopier.lots(1000.0, 40.0, info, 1, 0.01) == []                  # 0,01 lot = 40 $ > 3 %


def test_parse_check_and_wanted():
    m = {"ouverts": [{"id": "1-7"}]}
    assert tg_parse.check(m, {"type": "ouverture", "marche": "gold", "sens": "achat", "stop": None})["type"] == "rien"
    assert tg_parse.check(m, {"type": "fermer", "signal": "9-9"})["type"] == "rien"
    assert tg_parse.check(m, {"type": "fermer", "signal": "1-7", "raison": "close"})["signal"] == "1-7"
    out = tg_parse.decide({"text": "x"}, call=lambda *a: {"structured_output": {
        "type": "ouverture", "marche": "nasdaq", "sens": "vente", "entree": None, "stop": 20100, "objectifs": [20000],
        "signal": None, "raison": "vente"}})
    assert out["marche"] == "nasdaq" and out["objectifs"] == [20000.0]
    assert tg_listen.wanted(-100123, "Gold VIP", ["gold vip"]) and tg_listen.wanted(-100123, "x", ["-100123"])
    assert not tg_listen.wanted(-100123, "Autre", ["gold vip"])
    assert tg_listen.wanted(-1, "BENAGOLD 🫀", ["BENAGOLD"]) and not tg_listen.wanted(-1, "BENA GOLD - Private", ["BENAGOLD"])


BENA = """BENAGOLD
Transféré de BENA GOLD - Private
📉 SELL GOLD

Prix d’entrée : 4028-4032

❌Stop Loss :4038

✅ Take Profit 1:4019

✅ Take Profit 2:4007

✅ Take Profit 3:3989"""


def test_benagold_format_without_claude(tmp_path):
    now = [T0]
    c, mt5, sent = make(tmp_path, [], now, claude=False)
    mt5.bid = 4030.0
    post(tmp_path, 40, BENA, now[0])
    post(tmp_path, 41, "Belle journée la team, on reste concentrés", now[0])
    assert "ouverture" in c.step()
    deals = [r for r in mt5.sent if r["action"] == mt5.TRADE_ACTION_DEAL]
    assert [r["type"] for r in deals] == [mt5.ORDER_TYPE_SELL] * 3 and [r["tp"] for r in deals] == [4019.0, 4007.0, 3989.0]
    assert all(r["sl"] == 4038.0 and r["price"] == 4030.0 for r in deals) and "VENTE" in sent[-1][0]
    tickets = c.state["signals"]["100123-40"]["tickets"]
    mt5.positions = [NS(magic=tc.MAGIC, ticket=t, type=1, volume=0.01, tp=0.0) for t in tickets[1:]]
    mt5.bid = 4018.0
    c.step()                                                          # message sans trade : ignoré
    assert len(mt5.sent) == 3
    post(tmp_path, 42, "TP1 touché ✅ Sécurisez vos trades 🔒", now[0])
    c.step()
    sl = [r for r in mt5.sent if r["action"] == mt5.TRADE_ACTION_SLTP]
    assert len(sl) == 2 and all(r["sl"] == 4030.0 for r in sl) and "(BE)" in sent[-1][0]


def test_benagold_zone_already_left_gives_limit(tmp_path):
    now = [T0]
    c, mt5, sent = make(tmp_path, [], now, claude=False)
    mt5.bid = 4024.0                                                  # le prix est déjà descendu sous la zone
    post(tmp_path, 50, BENA, now[0])
    c.step()
    o = mt5.sent[-1]
    assert o["action"] == mt5.TRADE_ACTION_PENDING and o["type"] == mt5.ORDER_TYPE_SELL_LIMIT and o["price"] == 4028.0


def test_fixed_lot_per_target(tmp_path):
    now = [T0]
    c, mt5, sent = make(tmp_path, [], now, claude=False)
    c.cfg["lot"] = 0.2
    mt5.bid = 4030.0
    post(tmp_path, 60, BENA, now[0])
    c.step()
    assert [r["volume"] for r in mt5.sent] == [0.2, 0.2, 0.2] and "3 × 0,20 lot" in sent[-1][0]


def test_benagold_close_messages(tmp_path):
    """26/10 : « Clôture partielle » ferme un seul ordre, « Close now » le reste, les témoignages rien."""
    now = [T0]
    c, mt5, sent = make(tmp_path, [], now, claude=False)
    mt5.bid = 4030.0
    post(tmp_path, 40, BENA, now[0])
    c.step()
    tickets = c.state["signals"]["100123-40"]["tickets"]
    mt5.positions = [NS(magic=tc.MAGIC, ticket=t, type=1, volume=0.02, tp=tp)
                     for t, tp in zip(tickets, (4019.0, 4007.0, 3989.0))]
    n = len(mt5.sent)
    post(tmp_path, 41, "Belle cloture 🙂 je te suis", now[0])
    c.step()
    assert len(mt5.sent) == n
    post(tmp_path, 42, "Clôture partielle !", now[0])
    c.step()
    closes = [r for r in mt5.sent[n:] if r["action"] == mt5.TRADE_ACTION_DEAL]
    assert [r["position"] for r in closes] == [tickets[0]]
    mt5.positions = mt5.positions[1:]
    post(tmp_path, 43, "Close now", now[0])
    c.step()
    closes = [r for r in mt5.sent[n:] if r["action"] == mt5.TRADE_ACTION_DEAL]
    assert [r["position"] for r in closes] == [tickets[0], tickets[1], tickets[2]]
