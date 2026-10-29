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
    demo = {"cols": COLS, "positions": [
        {"symbol": "NAS100", "side": "achat", "volume": 0.1, "open": 29400.0, "price": 29420.0, "sl": 29350.0,
         "tp": 29550.0, "profit": 2.0, "opened": DAY, "origin": "Agent IA"}],
        "closed": [[NIGHT + 3600, NIGHT, "XAUUSD+", "vente", 0.01, 4050.0, 4040.0, 9.5, "Méthode Hugo", "TP", 4060.0, 4040.0],
                   [DAY + 60, DAY - 3600, "NAS100", "achat", 0.1, 29000.0, 29100.0, 10.0, "Copie du bot", "TP", None, None],
                   [DAY, DAY - 7200, "NAS100", "achat", 0.1, 29000.0, 29100.0, 10.0, "Agent IA", "TP", None, None]]}
    assert {t["id"] for t in eng.agent_trades(demo)} == {f"agent-ag-{DAY}", f"agent-hu-{NIGHT}"}   # sans stop : ignoré
    assert eng.agent_accounts(demo) >= 3
    pf = eng.portfolio.data
    assert f"agent-ag-{DAY}" in pf["open"] and any(h["id"] == f"agent-hu-{NIGHT}" and h["source"] == "agent"
                                                    for h in pf["history"])
    acct = eng.topstep()
    assert [r["note"] for r in acct.state["open_lab"]] == ["trade de l'agent IA (chasse)"]
    assert not acct.state.get("journal")                                     # l'or de nuit : pas dans Topstep
    n = eng.agent_accounts(demo)
    assert n == 0                                                             # rien de neuf : rien ne bouge
    # la position se ferme : Simulation soldée, ligne du journal Topstep avec les mêmes micros
    micros = acct.state["open_lab"][0]["contracts"]
    demo["positions"] = []
    demo["closed"].insert(0, [DAY + 1800, DAY, "NAS100", "achat", 0.1, 29400.0, 29550.0, 15.0, "Agent IA", "TP",
                              29350.0, 29550.0])
    eng.agent_accounts(demo)
    acct = eng.topstep()
    assert not acct.state["open_lab"] and acct.state["journal"][0]["contracts"] == micros
    assert any(h["id"] == f"agent-ag-{DAY}" and h["exit"] == 29550.0 for h in eng.portfolio.data["history"])
    assert eng.agent_accounts(demo) == 0


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
