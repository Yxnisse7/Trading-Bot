"""Bot classique du Nasdaq calculé sur le PC avec les prix MT5 (demandé par Yanisse le 19/10/2026)."""
from datetime import datetime, timezone

from trading_bot import mt5_bot as mb
from trading_bot import mt5_copy as mc
from trading_bot import pc_link
from trading_bot.models import Signal, iso

from test_mt5_copy import LocalMT5

NOW = datetime(2026, 10, 14, 14, 6, tzinfo=timezone.utc).timestamp()


class NasMT5(LocalMT5):
    """CFD du Nasdaq à 21 000, serveur à UTC+3."""
    price = 21000.0

    def symbol_info_tick(self, sym):
        return __import__("types").SimpleNamespace(bid=self.price, ask=self.price + 1, time=int(self.now) + self.OFF)

    def copy_rates_from_pos(self, sym, tf, start, n):
        if sym != "NAS100":
            return None
        t0 = int(self.now) // 300 * 300 - 300 * 1000
        p = self.price
        return [{"time": t + self.OFF, "open": p, "high": p + 5, "low": p - 5, "close": p, "tick_volume": 10}
                for t in range(t0, int(self.now) // 300 * 300 + 300, 300)]


def _signal(created: float, direction="long") -> Signal:
    return Signal(id="x1", asset="nasdaq", asset_label="Nasdaq 100 (NQ)", direction=direction, entry=21000.0,
                  take_profit=21090.0, stop_loss=20970.0, risk_reward=3.0, confidence="fort", score=4.0,
                  criteria=[], rationale="", news_context="", created_at=iso(datetime.fromtimestamp(created, timezone.utc)),
                  expires_at=iso(datetime.fromtimestamp(created + 86400, timezone.utc)))


def _bot(tmp_path, mt5, now, scans):
    bot = mb.LocalBot(mt5, mc.SYMBOLS, lambda: now[0], tmp_path, download=lambda name: b"{}")
    bot._scan = lambda bars, t: scans.pop(0) if scans else []
    return bot


def test_pc_bot_signal_is_copied_with_its_target_then_closed_at_the_stop(tmp_path):
    now = [NOW]
    mt5 = NasMT5(now[0])
    bot = _bot(tmp_path, mt5, now, [[_signal(NOW - 60)]])
    found, ok = bot.signals()
    assert ok == {"local:bot"} and len(found) == 1
    s = found[0]
    assert s["key"].startswith("lab:bot:") and s["stop"] == 30.0 and s["target"] == 90.0 and s["source"] == "local"
    # GitHub publie le même signal du bot : la copie ne prend que celui du PC
    gh = {"open_signals": [{"id": "g1", "direction": "long", "entry": 21010.0, "stop_loss": 20980.0,
                            "take_profit": 21100.0, "created_at": "2026-10-14T14:10:00Z",
                            "expires_at": "2026-10-15T14:10:00Z"}]}
    get = lambda url: {} if "lab_shadow" in url else gh if "nasdaq" in url else {"open_signals": []}
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: now[0], get=get, local=True, bot=bot)
    c.step()
    assert len(mt5.sent) == 1 and mt5.sent[0]["tp"] > mt5.sent[0]["price"]          # objectif du bot gardé
    assert c.state["bot:g1"]["status"] == "pas de signal sur les prix MT5"
    # le prix tombe sous le SL : le signal du PC est clos sur les bougies du courtier
    now[0] += 600
    mt5.now, mt5.price = now[0], 20900.0
    found, ok = bot.signals()
    assert found == [] and bot.store.history()[-1].status == "sl"


def test_pc_bot_hands_over_to_github_without_mt5_bars(tmp_path):
    now = [NOW]
    mt5 = NasMT5(now[0])
    mt5.copy_rates_from_pos = lambda *a: None
    bot = _bot(tmp_path, mt5, now, [[_signal(NOW - 60)]])
    assert bot.signals() == ([], set())
    raw = pc_link.encode(NOW, [], ok=set())
    assert pc_link.entry_owner(raw, "bot", int(NOW), "long", NOW + 60, window=1800) == "wait"


def test_github_bot_stays_silent_when_the_pc_computes_it():
    raw = pc_link.encode(NOW, [{"k": f"lab:bot:{int(NOW) - 600}", "d": "long"}], ok={"bot"})
    assert pc_link.entry_owner(raw, "bot", int(NOW), "long", NOW + 60, window=1800) == "pc"
    assert pc_link.entry_owner(raw, "bot", int(NOW) + 3600, "long", NOW + 60, window=1800) == "absent"
    assert pc_link.entry_owner(raw, "bot", int(NOW), "short", NOW + 60, window=1800) == "absent"
