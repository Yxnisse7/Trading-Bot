"""L'agent IA décide de chaque trade du démo avant l'ordre (demandé par Yanisse le 09/11/2026)."""
import json
from types import SimpleNamespace as NS

from trading_bot import decideur as dc
from trading_bot import mt5_check
from trading_bot import mt5_copy as mc
from test_mt5_copy import FakeMT5 as CopyMT5, sig, site
from test_mt5_tgcopy import BENA, T0, make, post


# ---------------------------------------------------------------- décision pure
def test_unreadable_answers_mean_no_trade():
    assert dc.normalize(None)["action"] == "aucune"
    assert dc.normalize({"action": "peut-être"})["action"] == "aucune"
    d = dc.normalize({"action": "prendre", "stop": "4190", "objectif": None, "confiance": 9, "raison": " ok "})
    assert d["stop"] == 4190.0 and d["confiance"] == 5 and d["raison"] == "ok"
    assert dc.last_json("Usage IA : {}\nbla\n" + json.dumps({"action": "refuser"})) == {"action": "refuser"}


def test_plan_keeps_rule_levels_when_the_agent_levels_are_absurd():
    take = dc.normalize({"action": "prendre", "stop": 4210.0, "objectif": 4180.0})
    p = dc.plan(take, False, 4200.0, 8.0, 8.0, 0.5)                 # vente : SL 10 au-dessus, TP 20 en dessous
    assert p["action"] == "prendre" and p["stop"] == 10.0 and p["target"] == 20.0 and not p["notes"]
    wrong = dc.normalize({"action": "prendre", "stop": 4190.0, "objectif": 4230.0})
    p = dc.plan(wrong, False, 4200.0, 8.0, None, 0.5)
    assert p["stop"] == 8.0 and p["target"] is None and len(p["notes"]) == 2
    far = dc.normalize({"action": "prendre", "stop": 4300.0})
    assert dc.plan(far, False, 4200.0, 8.0, None, 0.5)["stop"] == 8.0      # 100 $ au lieu de 8 : écarté


def test_plan_wait_needs_a_better_price_not_too_far():
    wait = dc.normalize({"action": "attendre", "entree": 4205.0, "stop": 4212.0, "objectif": 4190.0})
    p = dc.plan(wait, False, 4200.0, 8.0, 8.0, 0.5)                 # vendre 5 plus haut
    assert p["action"] == "attendre" and p["entry"] == 4205.0 and p["stop"] == 7.0 and p["target"] == 15.0
    worse = dc.normalize({"action": "attendre", "entree": 4195.0})
    assert dc.plan(worse, False, 4200.0, 8.0, 8.0, 0.5)["action"] == "refuser"
    too_far = dc.normalize({"action": "attendre", "entree": 4230.0})
    assert dc.plan(too_far, False, 4200.0, 8.0, 8.0, 0.5)["action"] == "refuser"


def agent_dir(tmp_path, decider=True):
    folder = tmp_path / "agent"
    (folder / "agent").mkdir(parents=True, exist_ok=True)
    script = folder / "agent" / "avis_direct.py"
    script.write_text("ap.add_argument('--decider')" if decider else "ap.add_argument('--signal')")
    return {"command": f"python {script}", "dir": str(folder), "decide": True}


def fake_spawn(answers, calls):
    def spawn(args, cwd, stdout, **k):
        calls.append(json.loads(open(args[-1], encoding="utf-8").read()))
        a = answers.pop(0)
        if a is not None:
            stdout.write("Usage IA : {}\n" + json.dumps(a) + "\n")
        stdout.close()
        return NS(poll=lambda: None if a is None else 0, kill=lambda: None)
    return spawn


def test_decideur_needs_an_agent_that_knows_the_new_option(tmp_path):
    assert not dc.Decideur(tmp_path, lambda: 0, agent_dir(tmp_path, decider=False)).available()
    assert dc.Decideur(tmp_path, lambda: 0, agent_dir(tmp_path)).available()
    assert not dc.Decideur(tmp_path, lambda: 0, dict(agent_dir(tmp_path), decide=False)).available()


def test_decideur_times_out_into_no_trade(tmp_path):
    now = [0.0]
    d = dc.Decideur(tmp_path, lambda: now[0], agent_dir(tmp_path), spawn=fake_spawn([None], []))
    assert d.ask("k", {"id": "k"})
    assert d.poll("k") is None
    now[0] = dc.TIMEOUT + 1
    assert d.poll("k")["action"] == "aucune"


# ---------------------------------------------------------------- copie des signaux du bot
class MT5(CopyMT5):
    TRADE_ACTION_PENDING, TRADE_ACTION_REMOVE = 5, 8
    ORDER_TYPE_BUY_LIMIT, ORDER_TYPE_SELL_LIMIT = 2, 3

    def __init__(self):
        super().__init__()
        self.orders = []

    def orders_get(self):
        return self.orders

    def history_deals_get(self, *a, position=None, **k):
        return []

    def order_send(self, req):
        if req["action"] == self.TRADE_ACTION_PENDING:
            self.sent.append(req)
            self.orders.append(NS(ticket=777, magic=mc.MAGIC))
            return NS(retcode=self.TRADE_RETCODE_DONE, price=req["price"], order=777)
        if req["action"] == self.TRADE_ACTION_REMOVE:
            self.sent.append(req)
            self.orders = [o for o in self.orders if o.ticket != req["order"]]
            return NS(retcode=self.TRADE_RETCODE_DONE)
        return super().order_send(req)


class Relay:
    def __init__(self):
        self.notes, self.replies = [], []

    def beat(self):
        pass

    def _candles(self, sym, tf, n, until):
        return [[1, 2, 3, 1, 2]]

    def note(self, key, s, rec):
        self.notes.append((key, dict(s), dict(rec)))

    def entry(self, key, s, rec):
        self.notes.append((key, dict(s), dict(rec)))

    def reply_to(self, key, text):
        self.replies.append(text)

    def cancelled(self, key, text):
        self.replies.append(text)

    def step(self, *a):
        pass


def copier(tmp_path, answers, now, calls):
    mt5, relay = MT5(), Relay()
    dec = dc.Decideur(tmp_path, lambda: now[0], agent_dir(tmp_path), spawn=fake_spawn(answers, calls))
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: now[0], get=site([sig()]), relay=relay, decider=dec)
    return c, mt5, relay


def test_copy_waits_for_the_agent_and_uses_its_levels(tmp_path):
    now, calls = [mc._ts("2026-10-14T13:50:00Z") + 60], []
    c, mt5, relay = copier(tmp_path, [{"action": "prendre", "stop": 4210.0, "objectif": 4180.0, "confiance": 4,
                                       "raison": "Vente dans le sens de la journée."}], now, calls)
    c.step()
    assert calls[0]["entry"] == 4200.0 and calls[0]["stop_loss"] == 4208.0 and calls[0]["bid"] == 4200.0
    assert calls[0]["candles_5m"] and mt5.sent == []                # rien avant la réponse
    assert c.state["bot:abc"]["status"] == "agent : en réflexion"
    c.step()                                                         # tour suivant du pont (moins de 30 s après)
    req = mt5.sent[0]
    assert req["sl"] == 4210.0 and req["tp"] == 4180.0 and req["volume"] == 0.02    # 2 % de 1 000 $ / (10 $ × 100)
    rec = c.state["bot:abc"]
    assert rec["status"] == "ouvert" and rec["agent"]["action"] == "prendre"
    assert "pris" in dc.line(rec["agent"]) and relay.notes[0][0] == "bot:abc"


def test_copy_refused_or_unanswered_means_no_trade(tmp_path):
    now, calls = [mc._ts("2026-10-14T13:50:00Z") + 60], []
    c, mt5, relay = copier(tmp_path, [{"action": "refuser", "confiance": 2, "raison": "Annonce dans 10 min."}], now, calls)
    c.step()
    c.step()
    assert mt5.sent == [] and c.state["bot:abc"]["status"] == "agent : refusé"
    assert "agent" in mt5_check.reason(c.state["bot:abc"]["status"])
    report = mt5_check.report(c.state, now[0])
    assert "0 raté" in report and "laissé(s) de côté par l'agent" in report
    c2, mt52, _ = copier(tmp_path / "b", [None], now, [])
    c2.step()
    now[0] += dc.TIMEOUT + 1
    c2.step()
    assert mt52.sent == [] and c2.state["bot:abc"]["status"] == "agent : pas de réponse"


def test_copy_wait_places_a_limit_then_cancels_it(tmp_path):
    now, calls = [mc._ts("2026-10-14T13:50:00Z") + 60], []
    c, mt5, relay = copier(tmp_path, [{"action": "attendre", "entree": 4204.0, "stop": 4211.0, "objectif": 4190.0,
                                       "confiance": 3, "raison": "Mieux vendre sur le retour à 4204."}], now, calls)
    c.step()
    c.step()
    req = mt5.sent[0]
    assert req["action"] == mt5.TRADE_ACTION_PENDING and req["type"] == mt5.ORDER_TYPE_SELL_LIMIT
    assert req["price"] == 4204.0 and req["sl"] == 4211.0 and req["tp"] == 4190.0
    assert c.state["bot:abc"]["status"] == "limite"
    now[0] += dc.WAIT_MAX + 1                                        # jamais touché (et signal expiré entre-temps)
    c.last = 0
    c.step()
    assert mt5.sent[-1]["action"] == mt5.TRADE_ACTION_REMOVE
    assert c.state["bot:abc"]["status"].startswith("limite annulée") and relay.replies


def test_copy_stays_automatic_when_the_agent_is_too_old(tmp_path):
    now = [mc._ts("2026-10-14T13:50:00Z") + 60]
    mt5 = MT5()
    dec = dc.Decideur(tmp_path, lambda: now[0], agent_dir(tmp_path, decider=False))
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: now[0], get=site([sig()]), decider=dec)
    c.step()
    assert mt5.sent[0]["sl"] == 4208.0 and c.state["bot:abc"]["status"] == "ouvert"


# ---------------------------------------------------------------- copie des canaux Telegram
def tg(tmp_path, answers):
    now = [T0]
    c, mt5, sent = make(tmp_path, [], now, claude=False)
    calls = []
    c.decider = dc.Decideur(tmp_path, lambda: now[0], agent_dir(tmp_path), spawn=fake_spawn(answers, calls))
    mt5.bid = 4030.0
    post(tmp_path, 40, BENA, now[0])
    return c, mt5, sent, calls


def test_channel_signal_refused_by_the_agent(tmp_path):
    c, mt5, sent, calls = tg(tmp_path, [{"action": "refuser", "confiance": 2, "raison": "Contre la tendance."}])
    c.step()
    assert calls[0]["strategie"] == "copie_telegram" and calls[0]["objectifs"] == [4019.0, 4007.0, 3989.0]
    assert mt5.sent == []
    c.step()
    assert mt5.sent == [] and "pas copié" in sent[-1][0] and "Contre la tendance" in sent[-1][0]


def test_channel_signal_taken_with_the_agent_stop(tmp_path):
    c, mt5, sent, calls = tg(tmp_path, [{"action": "prendre", "stop": 4036.0, "objectif": None, "confiance": 4,
                                         "raison": "Rejet propre du haut."}])
    c.step()
    c.step()
    deals = [r for r in mt5.sent if r["action"] == mt5.TRADE_ACTION_DEAL]
    assert len(deals) == 3 and all(r["sl"] == 4036.0 for r in deals)
    assert "Agent IA" in sent[-1][0] and not c.reviews                # plus d'avis après coup


def test_relay_shows_the_decision_and_skips_the_late_review(tmp_path, monkeypatch):
    from test_pc_relay import DealsMT5, _relay
    from datetime import datetime, timezone
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    now = [datetime(2026, 10, 14, 22, 6, tzinfo=timezone.utc).timestamp()]
    (tmp_path / "agent").mkdir()
    relay, sent, beats, spawned = _relay(tmp_path, DealsMT5(now[0]), now, agent_dir=tmp_path / "agent")
    dec = dict(dc.normalize({"action": "attendre", "entree": 4190.0, "confiance": 3, "raison": "Retour attendu."}),
               notes=[])
    rec = {"status": "limite", "ticket": 9, "symbol": "XAUUSD+", "lot": 0.02, "price": 4190.0,
           "limit_until": now[0] + 7200, "agent": dec}
    relay.entry("lab:nuit_asie:1", {"direction": "long", "entry": 4190.0, "stop": 10.0, "asset": "gold",
                                    "created": now[0]}, rec)
    body = sent[-1][1]
    assert "ordre limite à 4" in body and "Agent IA : ⏳" in body and "Retour attendu." in body
    assert not [s for s in spawned if isinstance(s, tuple)]          # pas d'avis lancé après coup
    relay.cancelled("lab:nuit_asie:1", "Ordre limite de l'agent annulé : pas touché à temps. Pas de trade.")
    assert sent[-1][2] is not None and relay.state["lab:nuit_asie:1"]["exit_sent"]
