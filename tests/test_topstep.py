"""Compte Topstep 50K simulé : vos seuls trades, règles Topstep, séparé du reste."""
from datetime import datetime, timedelta, timezone

import pytest

from trading_bot import engine as engmod
from trading_bot import topstep as ts
from trading_bot.config import Config, default_assets
from trading_bot.engine import Engine
from trading_bot.models import Signal, iso
from trading_bot.storage import Store

T0 = datetime(2026, 9, 22, 14, 0, tzinfo=timezone.utc)   # mardi 09:00 à Chicago


def _sig(id_, source="bot", status="tp", entry=20000.0, close=20020.0, when=T0, asset="nasdaq", direction="long",
         sl=19990.0, duration=20, **kw):
    return Signal(id=id_, asset=asset, asset_label="Nasdaq 100 (NQ)", direction=direction, entry=entry,
                  take_profit=entry + 20, stop_loss=sl, risk_reward=2.0, confidence="fort", score=6.0, criteria=[],
                  rationale="", news_context="", created_at=iso(when), expires_at=iso(when + timedelta(hours=1)),
                  status=status, closed_at=iso(when + timedelta(minutes=duration)) if status != "open" else None,
                  close_price=close if status != "open" else None, source=source, **kw)


def _acct(tmp_path):
    return ts.TopstepAccount(tmp_path / "topstep", docs_dir=tmp_path / "docs")


def test_only_your_trades_are_in_the_account(tmp_path):
    cfg = Config(assets=default_assets())
    acct = _acct(tmp_path)
    sigs = [_sig("bot1"), _sig("man1", source="manual"), _sig("sh1", source="shadow")]
    d = acct.compute(sigs, cfg)
    assert [t["id"] for t in d["trades"]] == ["man1"]              # le bot n'ajoute rien de lui-même
    acct.take(sigs[0], 3)
    d = acct.compute(sigs, cfg)
    row = next(t for t in d["trades"] if t["id"] == "bot1")
    # 3 MNQ × 20 points × 2 $ = 120 $ brut, moins l'écart acheteur-vendeur estimé
    assert row["symbol"] == "MNQ" and row["contracts"] == 3 and row["pnl_gross"] == 120.0 and row["pnl"] < 120.0
    with pytest.raises(ValueError):
        acct.take(sigs[2])                                          # un fantôme n'a jamais été envoyé
    acct.remove("man1")
    assert {t["id"] for t in acct.compute(sigs, cfg)["trades"]} == {"bot1"}


def test_manual_stop_price_is_used(tmp_path):
    cfg = Config(assets=default_assets())
    acct = _acct(tmp_path)
    s = _sig("m1", source="manual", status="sl", close=19990.0,
             meta={"manual_exit": {"price": 20010.0, "at": iso(T0 + timedelta(minutes=5)), "pnl_pct": 0.05}})
    r = acct.compute([s], cfg)["trades"][0]
    assert r["exit"] == 20010.0 and r["status"] == "manual" and r["pnl_gross"] > 0


def test_max_loss_trails_end_of_day_and_fails_the_account(tmp_path):
    cfg = Config(assets=default_assets())
    cfg.assets["nasdaq"].cost_pct = 0.0
    acct = _acct(tmp_path)
    day1 = _sig("a", source="manual", entry=20000, close=20100, sl=19900)             # +100 pts
    day2 = _sig("b", source="manual", entry=20000, close=19700, sl=19600, when=T0 + timedelta(days=1))
    acct.state["taken"] = {}
    # 10 micros par trade : +2 000 $ le premier jour, puis −6 000 $
    acct.take(day1, 10)
    acct.take(day2, 10)
    d = acct.compute([day1, day2], cfg, now=T0 + timedelta(days=1, hours=2))
    assert d["trades"][0]["balance_after"] == 52_000.0
    assert d["mll"] == 50_000.0                                      # remontée à 52 000 − 2 000, plafonnée au départ
    assert d["status"] == "échoué" and d["failed"]["mll"] == 50_000.0


def test_consistency_raises_the_needed_profit(tmp_path):
    cfg = Config(assets=default_assets())
    cfg.assets["nasdaq"].cost_pct = 0.0
    acct = _acct(tmp_path)
    big = _sig("a", source="manual", entry=20000, close=20100, sl=19900)
    acct.take(big, 10)                                               # +2 000 $ en une journée
    d = acct.compute([big], cfg)
    assert d["best_day"] == 2000.0 and d["needed_profit"] == 4000.0 and not d["consistency_ok"]
    assert d["status"] == "en cours"


def test_rule_violations_are_reported(tmp_path):
    cfg = Config(assets=default_assets())
    acct = _acct(tmp_path)
    late = _sig("late", source="manual", when=datetime(2026, 9, 22, 20, 5, tzinfo=timezone.utc), duration=15)
    d = acct.compute([late], cfg)
    assert any("15:10" in v for v in d["violations"])                # 15:05 → 15:20 à Chicago
    loss = _sig("loss", source="manual", entry=20000, close=19400, sl=19300)
    acct.take(loss, 10)
    d = acct.compute([loss], cfg)
    assert any("limite journalière" in v for v in d["violations"])


def test_trading_day_starts_at_5pm_chicago():
    evening = datetime(2026, 9, 22, 23, 0, tzinfo=timezone.utc)      # 18:00 à Chicago
    assert ts.trading_day(evening).isoformat() == "2026-09-23"
    assert ts.trading_day(T0).isoformat() == "2026-09-22"


def test_journal_parsing():
    j = ts.parse_journal("nasdaq short 30950 30910 3 2026-09-23T15:01".split())
    assert j["direction"] == "short" and j["contracts"] == 3 and j["opened_at"].hour == 13
    with pytest.raises(ValueError):
        ts.parse_journal(["nasdaq"])


def test_telegram_commands_and_isolation(tmp_path, monkeypatch):
    eng = Engine(Config(assets=default_assets()), Store(tmp_path))
    monkeypatch.setattr(engmod, "notify", lambda text, **kw: None)
    eng.store.append_history(_sig("bot1"))
    before = dict(eng.portfolio.data)
    reply = eng.handle_command("/pris nasdaq 4", T0)
    assert "Ajouté au compte Topstep" in reply.text and "4 micros MNQ" in reply.text
    assert "TOPSTEP 50K" in eng.handle_command("/topstep", T0).text
    assert "journal" in eng.handle_command("/journal nasdaq long 20000 20010 2", T0).text.lower()
    assert eng.portfolio.data == before                              # la simulation du bot n'est pas touchée
    assert (tmp_path / "topstep" / "dashboard.json").exists()


def test_topstep_exit_leaves_the_bot_signal_untouched(tmp_path, monkeypatch):
    eng = Engine(Config(assets=default_assets()), Store(tmp_path))
    monkeypatch.setattr(engmod, "notify", lambda text, **kw: None)
    monkeypatch.setattr(engmod.market, "fetch_price", lambda asset: 20030.0)
    sig = _sig("open1", status="open")
    eng.store.save_open([sig])
    eng.handle_command("/pris nasdaq 2", T0)
    assert eng.topstep_update()["open"][0]["id"] == "open1"
    reply = eng.handle_command("/sortie nasdaq", T0)
    assert "Sortie Topstep enregistrée à 20030" in reply.text
    d = eng.topstep_update()
    assert not d["open"] and d["trades"][0]["pnl_gross"] == 120.0      # 30 points × 2 $ × 2 micros
    still = eng.store.open_signals()[0]
    assert still.status == "open" and "manual_exit" not in (still.meta or {})   # le bot continue normalement


def test_candidates_list_recent_bot_signals_not_yet_taken(tmp_path):
    acct = _acct(tmp_path)
    sigs = [_sig("a1", when=T0), _sig("s1", source="shadow", when=T0), _sig("m1", source="manual", when=T0),
            _sig("old", when=T0 - timedelta(days=5))]
    d = acct.compute(sigs, Config(assets=default_assets()), T0 + timedelta(hours=1))
    assert [c["id"] for c in d["candidates"]] == ["a1"]
    acct.take(sigs[0], 3)
    assert acct.compute(sigs, Config(assets=default_assets()), T0 + timedelta(hours=1))["candidates"] == []
