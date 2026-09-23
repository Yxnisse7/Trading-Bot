"""Mode halal : second bot séparé (achat seulement, au comptant, sans levier, données à part)."""
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from trading_bot import engine as engmod
from trading_bot.analysis import Assessment
from trading_bot.config import ROOT_DIR, Config, default_assets
from trading_bot.halal import HalalEngine, halal_assets, halal_config, halal_data_dir, halal_store, page_buttons
from trading_bot.models import Signal
from trading_bot.portfolio import Portfolio, size_position
from trading_bot.storage import Store

from conftest import make_candles

NOW = datetime(2026, 9, 17, 10, 0, tzinfo=timezone.utc)


def _assessment(asset_key: str, direction: str | None, price: float = 100.0) -> Assessment:
    return Assessment(asset_key, price, direction, 6.0 if direction else 0.0,
                      ["adx", "macd", "rsi", "trend_15m", "trend_5m"] if direction else [],
                      hourly_range=2.0, atr=0.5, sigma_5m=0.01, horizon_minutes=720, base_minutes=60)


@pytest.fixture
def halal(tmp_path, monkeypatch):
    """Moteur halal sur un dossier temporaire ; le marché, l'actualité et Telegram sont simulés."""
    sent = []
    candles = make_candles(n=400, start_price=100.0, start_ts=int(NOW.timestamp()) - 400 * 300 - 300)
    monkeypatch.setattr(engmod.market, "fetch_candles_5m", lambda asset, days=5: candles)
    monkeypatch.setattr(engmod.market, "fetch_candles_1m", lambda asset: [])
    monkeypatch.setattr(engmod.market, "fetch_price", lambda asset: 100.0)
    monkeypatch.setattr(engmod.newsmod, "fetch_news", lambda cats, lb, now: [])
    monkeypatch.setattr(engmod.calmod, "fetch_events", lambda f: [])
    import trading_bot.halal as halmod
    monkeypatch.setattr(engmod, "notify", lambda text, **kw: sent.append((text, kw)))
    monkeypatch.setattr(halmod, "notify", lambda text, **kw: sent.append((text, kw)))
    cfg = halal_config()
    for a in cfg.assets.values():
        a.session_utc = None
    eng = HalalEngine(cfg, Store(tmp_path / "halal"))
    eng.portfolio.data["started_at"] = "2020-01-01T00:00:00Z"   # la simulation compte les trades du test
    return eng, sent, monkeypatch


def test_defaults_leave_the_main_bot_unchanged():
    cfg = Config(assets=default_assets())
    assert not cfg.long_only and not cfg.cash_only and cfg.scan_bases is None and cfg.scan_days == 5
    assert all(a.fee_per_order == 0 for a in cfg.assets.values())


def test_halal_assets_are_spot_without_leverage():
    assets = halal_assets()
    assert {"bitcoin", "ethereum", "usa_islamique", "monde_islamique", "or_physique"} == set(assets)
    assert all(a.max_leverage == 1.0 for a in assets.values())
    assert not any(a.yahoo_symbol.endswith("=F") for a in assets.values())   # aucun contrat à terme
    cfg = halal_config()
    assert cfg.long_only and cfg.cash_only and cfg.scan_bases == [60]
    assert not cfg.shadow_enabled and not cfg.variants_enabled


def test_halal_never_uses_the_main_data_folder(tmp_path):
    with pytest.raises(RuntimeError):
        HalalEngine(halal_config(), Store(ROOT_DIR / "data"))
    assert halal_data_dir() == ROOT_DIR / "data" / "halal"
    assert halal_store(tmp_path / "halal").docs is None     # seul data/halal est publié (dans docs/halal)


def test_long_only_signal_with_cash_sizing_and_isolated_files(halal, tmp_path):
    eng, sent, mp = halal
    mp.setattr(engmod, "assess", lambda asset, candles, cfg, weights=None, **kw: _assessment(asset.key, "long"))
    sigs = eng.scan(NOW)
    assert sigs and all(s.direction == "long" and s.horizon == "12h" for s in sigs)
    first = sigs[0].meta["sim"]
    assert first["lots"] > 0 and first["leverage"] <= 1.0        # jamais plus que les liquidités
    later = [s.meta["sim"] for s in sigs[1:]]
    assert later and all(x["lots"] == 0 and "liquidités" in x["reason"] for x in later)
    texts = [t for t, _ in sent]
    assert all(t.startswith("🌙 <b>HALAL</b>") for t in texts)
    assert all("halal.html" in kw["buttons"][0][0][1] for _, kw in sent)
    assert "swing ~12 h" in texts[0] and "expire le" in texts[0]
    # rien en dehors du dossier du mode halal
    assert {p.name for p in tmp_path.iterdir()} == {"halal"}


def test_short_setups_are_never_signalled(halal):
    eng, sent, mp = halal
    mp.setattr(engmod, "assess", lambda asset, candles, cfg, weights=None, **kw: _assessment(asset.key, "short"))
    assert eng.scan(NOW) == []
    assert sent == [] and eng.store.open_signals() == []


def test_cash_only_sizing_and_fixed_fees(tmp_path):
    asset = halal_assets()["usa_islamique"]
    # 1 % de 1 000 = 10 de risque, stop à 0,80 → 12 parts voulues, mais 1 000 de liquidités → 10 parts
    s = size_position(1000.0, 1.0, asset, 100.0, 99.2, cash=1000.0)
    assert s["lots"] == 10 and s["notional"] == 1000.0 and not s["risky"]
    assert size_position(1000.0, 1.0, asset, 100.0, 99.2, cash=50.0)["lots"] == 0
    # sans mode comptant (bot principal), le calcul reste celui d'avant
    assert size_position(1000.0, 1.0, replace(asset, max_leverage=20), 100.0, 99.2)["lots"] == 12

    cfg = halal_config()
    port = Portfolio(Store(tmp_path), cfg)
    sig = Signal(id="h1", asset="usa_islamique", asset_label=asset.label, direction="long", entry=100.0,
                 take_profit=101.2, stop_loss=99.2, risk_reward=1.5, confidence="moyen", score=4.0, criteria=[],
                 rationale="", news_context="", created_at="2099-01-01T10:00:00Z", expires_at="2099-01-01T22:00:00Z")
    port.on_open(sig, asset)
    sig.status, sig.close_price, sig.closed_at = "tp", 101.2, "2099-01-01T12:00:00Z"
    row = port.on_close(sig, asset)
    # 10 parts × 1,20 = 12 brut ; coûts = 0,10 % × 1 000 + 2 ordres à 1 = 3
    assert row["pnl_gross"] == 12.0 and row["cost"] == 3.0 and row["pnl"] == 9.0


def test_tick_never_reads_telegram_commands(halal):
    eng, sent, mp = halal

    def boom(*a, **k):
        raise AssertionError("le mode halal ne doit pas lire les messages Telegram")
    mp.setattr(engmod, "telegram_updates", boom)
    mp.setattr(engmod, "assess", lambda asset, candles, cfg, weights=None, **kw: _assessment(asset.key, None))
    out = eng.tick(NOW)
    assert out == {"closed": [], "new": []}
    with pytest.raises(RuntimeError):
        eng.manual("bitcoin", "long")


def test_halal_summary_is_separate_and_sent_once(halal):
    eng, sent, mp = halal
    text = eng.summary(NOW.date())
    assert text.startswith("<b>🌙 RÉSUMÉ HALAL")
    assert "SIMULATION HALAL" in text and "en ombre" not in text
    assert len(sent) == 1 and sent[0][1].get("silent")
    assert eng.summary(NOW.date()) == "" and len(sent) == 1


def test_page_buttons_point_to_the_halal_page():
    rows = page_buttons("https://x.github.io/Trading-Bot/", "bitcoin")
    assert rows[0][0][1] == "https://x.github.io/Trading-Bot/halal.html?actif=bitcoin#live"
    assert page_buttons("") == []


def test_sparse_session_data_still_gives_a_range():
    """ETF de Londres : bougies 5 min clairsemées, séance de 8 h 30 → le range sur 12 h doit rester mesurable."""
    from trading_bot import indicators as ind
    base = make_candles(n=4000, start_price=100.0, seed=5)
    sparse = [c for i, c in enumerate(base) if 7 <= (c.ts // 3600) % 24 < 15 and i % 2 == 0]
    assert ind.average_range(sparse, 12 * 3600, buckets=16) is None           # réglage du bot principal
    assert ind.average_range(sparse, 12 * 3600, buckets=16, min_fill=halal_config().range_min_fill) > 0


def test_scan_survives_an_asset_fully_blocked_by_the_policy(halal):
    """Après un stop, l'actif est bloqué par le refroidissement : le passage halal ne doit pas planter
    (il cherchait les motifs de l'horizon « 1h », absent en mode halal)."""
    from datetime import timedelta
    from trading_bot.models import iso
    eng, sent, mp = halal
    mp.setattr(engmod, "assess", lambda asset, candles, cfg, weights=None, **kw: _assessment(asset.key, None))
    stopped = Signal(id="x1", asset="bitcoin", asset_label="Bitcoin (BTC)", direction="long", entry=100.0,
                     take_profit=102.0, stop_loss=99.0, risk_reward=2.0, confidence="moyen", score=4.0, criteria=[],
                     rationale="", news_context="", created_at=iso(NOW - timedelta(minutes=40)),
                     expires_at=iso(NOW + timedelta(hours=11)), status="sl", closed_at=iso(NOW - timedelta(minutes=5)),
                     close_price=99.0, pnl_pct=-1.0, horizon="12h", horizon_minutes=720)
    eng.store.append_history(stopped)
    assert eng.scan(NOW) == []
