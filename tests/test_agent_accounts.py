"""29/10/2026 : les trades de l'agent IA (démo MT5 du PC) passent aussi dans la Simulation et le compte Topstep,
et Topstep ne prend aucune entrée de nuit (ni de l'agent, ni des stratégies, ni du bot)."""
from datetime import datetime, timezone

from trading_bot.config import Config, default_assets
from trading_bot.engine import Engine
from trading_bot.storage import Store
from trading_bot.topstep import in_session

COLS = ["closed", "opened", "symbol", "side", "volume", "open", "close", "pnl", "origin", "why", "sl", "tp"]
DAY = int(datetime(2026, 10, 30, 14, 0, tzinfo=timezone.utc).timestamp())     # 15 h Paris
NIGHT = int(datetime(2026, 10, 30, 23, 0, tzinfo=timezone.utc).timestamp())   # minuit Paris
LATER = datetime(2026, 11, 2, tzinfo=timezone.utc)


def _engine(tmp_path):
    eng = Engine(Config(assets=default_assets()))
    eng.store = Store(tmp_path / "data", tmp_path / "docs")
    eng.agent_accounts({})                                   # crée la Simulation sur le nouveau magasin
    eng.portfolio.data["started_at"] = "2026-10-01T00:00:00Z"
    return eng


def test_topstep_session_hours():
    at = lambda h, m=0: datetime(2026, 10, 30, h, m, tzinfo=timezone.utc)      # noqa: E731
    assert not in_session(at(6, 30)) and in_session(at(7, 30))                   # 7h30 / 8h30 Paris
    assert in_session(at(20, 0)) and not in_session(at(20, 15))                  # 15:10 à Chicago
    assert not in_session(datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc))   # samedi


def test_agent_trades_reach_simulation_and_topstep(tmp_path):
    eng = _engine(tmp_path)
    demo = {"cols": COLS, "off": 10800, "positions": [
        {"symbol": "NAS100", "side": "achat", "volume": 0.1, "open": 29400.0, "price": 29420.0, "sl": 29350.0,
         "tp": 29550.0, "profit": 2.0, "opened": DAY, "origin": "Agent IA"}],
        "closed": [[NIGHT + 3600, NIGHT, "XAUUSD+", "vente", 0.01, 4050.0, 4040.0, 9.5, "Méthode Hugo", "TP", 4060.0, 4040.0],
                   [DAY + 60, DAY - 3600, "NAS100", "achat", 0.1, 29000.0, 29100.0, 10.0, "Copie du bot", "TP", None, None],
                   [DAY, DAY - 7200, "NAS100", "achat", 0.1, 29000.0, 29100.0, 10.0, "Agent IA", "TP", None, None]]}
    assert {t["id"] for t in eng.agent_trades(demo)} == {f"agent-ag-{DAY}", f"agent-hu-{NIGHT}"}   # sans stop : ignoré
    assert eng.agent_accounts(demo, LATER) >= 3
    pf = eng.portfolio.data
    assert f"agent-ag-{DAY}" in pf["open"] and any(h["id"] == f"agent-hu-{NIGHT}" and h["source"] == "agent"
                                                    for h in pf["history"])
    acct = eng.topstep()
    assert [r["note"] for r in acct.state["open_lab"]] == ["trade de l'agent IA (chasse)"]
    assert not acct.state.get("journal")                                     # l'or de nuit : pas dans Topstep
    n = eng.agent_accounts(demo, LATER)
    assert n == 0                                                             # rien de neuf : rien ne bouge
    # la position se ferme : Simulation soldée, ligne du journal Topstep avec les mêmes micros
    micros = acct.state["open_lab"][0]["contracts"]
    demo["positions"] = []
    demo["closed"].insert(0, [DAY + 1800, DAY, "NAS100", "achat", 0.1, 29400.0, 29550.0, 15.0, "Agent IA", "TP",
                              29350.0, 29550.0])
    eng.agent_accounts(demo, LATER)
    acct = eng.topstep()
    assert not acct.state["open_lab"] and acct.state["journal"][0]["contracts"] == micros
    assert any(h["id"] == f"agent-ag-{DAY}" and h["exit"] == 29550.0 for h in eng.portfolio.data["history"])
    assert eng.agent_accounts(demo, LATER) == 0


def test_topstep_skips_bot_signals_opened_at_night(tmp_path):
    from trading_bot.models import Signal
    from trading_bot.topstep import TopstepAccount
    acct = TopstepAccount(tmp_path / "ts")
    mk = lambda sid, ts: Signal(id=sid, asset="nasdaq", asset_label="Nasdaq", direction="long", entry=1.0,  # noqa: E731
                                take_profit=2.0, stop_loss=0.5, risk_reward=2.0, confidence="moyen", score=0.0,
                                criteria=[], rationale="", news_context="",
                                created_at=datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                expires_at="2026-11-01T00:00:00Z", source="bot")
    got = acct.included([mk("jour", DAY), mk("nuit", NIGHT)], mirror_ids={"jour", "nuit"})
    assert [s.id for s, _, _ in got] == ["jour"]


def test_agent_trades_shifted_by_a_bad_server_clock_are_not_added_again(tmp_path):
    """30/10/2026 : marché fermé, le PC lit mal l'heure du serveur et renvoie le même trade décalé (30 min, 3 h)."""
    eng = _engine(tmp_path)
    row = lambda shift: [DAY + 2364 + shift, DAY + shift, "NAS100", "vente", 0.1, 28265.0, 28365.0, -10.0,  # noqa: E731
                         "Agent IA", "SL", 28365.0, 28100.0]
    demo = {"cols": COLS, "off": 10800, "positions": [], "closed": [row(0)]}
    assert eng.agent_accounts(demo, LATER) >= 2
    for shift in (1800, 10800, -1800):
        assert eng.agent_accounts({**demo, "closed": [row(shift)]}, LATER) == 0
    assert [h["id"] for h in eng.portfolio.data["history"]] == [f"agent-ag-{DAY}"]
    assert len(eng.topstep().state["journal"]) == 1
    # relevé d'un ancien pont (sans décalage connu) ou daté dans le futur : ignoré
    assert eng.agent_accounts({**demo, "off": None, "closed": [row(7200)]}, LATER) == 0
    fresh = {**demo, "closed": [[DAY + 9000, DAY + 8000, "NAS100", "vente", 0.1, 28000.0, 28100.0, -10.0, "Agent IA",
                                 "SL", 28100.0, 27900.0]]}
    assert eng.agent_accounts(fresh, datetime.fromtimestamp(DAY + 8500, timezone.utc)) == 0


def test_yahoo_bad_open_is_fixed():
    """Bougie Nasdaq du 30/10/2026 19:00 UTC : ouverture à 29 562 pour une clôture d'avant à 28 234."""
    from trading_bot.models import Candle
    from trading_bot.providers.yahoo import fix_bad_opens
    c = [Candle(1, 28271.0, 28272.5, 28232.75, 28234.5, 1.0), Candle(2, 29562.0, 29562.0, 28283.25, 28307.75, 1.0),
         Candle(3, 28307.75, 28376.0, 28304.75, 28374.25, 1.0)]
    out = fix_bad_opens(c)
    assert (out[1].open, out[1].high, out[1].low, out[1].close) == (28234.5, 28307.75, 28234.5, 28307.75)
    assert out[0] == c[0] and out[2] == c[2]
    gap = [Candle(1, 100.0, 100.0, 100.0, 100.0, 1.0), Candle(2, 103.0, 104.0, 102.5, 103.5, 1.0)]  # vrai trou
    assert fix_bad_opens(gap) == gap
