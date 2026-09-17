from datetime import datetime, timedelta, timezone

from trading_bot.config import Config, default_assets
from trading_bot.engine import Engine
from trading_bot.providers import news
from trading_bot.storage import Store

from conftest import make_candles

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Fed rate decision looms as Powell speaks</title><link>http://x/1</link>
<pubDate>Thu, 17 Sep 2026 13:30:00 GMT</pubDate></item>
<item><title>Bitcoin exchange hacked, $200M drained</title><link>http://x/2</link>
<pubDate>Thu, 17 Sep 2026 13:00:00 GMT</pubDate></item>
<item><title>Quiet session ahead of earnings</title><link>http://x/3</link>
<pubDate>Thu, 17 Sep 2026 12:00:00 GMT</pubDate></item>
</channel></rss>"""


def test_parse_rss_and_risk_score():
    items = news.parse_rss(RSS, "x", "macro")
    assert len(items) == 3
    score, hits = news.risk_score(items, ("fed", "bitcoin"))
    assert score == 4 and len(hits) == 2
    score2, _ = news.risk_score(items, ("gold",))
    assert score2 == 2  # deux titres à risque, non liés à l'actif → 1 point chacun


def test_blackout_windows():
    now = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)  # 1er vendredi d'octobre → NFP 12h30
    evs = news.recurring_macro_events(now)
    assert evs and "NFP" in evs[0].name
    assert news.in_blackout(now, evs, 45, 30) is not None
    assert news.in_blackout(now - timedelta(hours=2), evs, 45, 30) is None
    custom = news.load_calendar([{"name": "FOMC", "at": "2026-09-16T18:00:00Z", "impact": "high"},
                                 {"name": "x", "at": "bad"}])
    assert len(custom) == 1
    assert news.in_blackout(datetime(2026, 9, 16, 18, 20, tzinfo=timezone.utc), custom, 45, 30).name == "FOMC"


def _engine(tmp_path, monkeypatch, candles, price, rss_items=None):
    cfg = Config(assets=default_assets())
    cfg.assets["nasdaq"].session_utc = None
    cfg.assets["gold"].session_utc = None
    store = Store(tmp_path)
    eng = Engine(cfg, store)
    from trading_bot import engine as engmod
    monkeypatch.setattr(engmod.market, "fetch_candles_5m", lambda asset, days=5: candles)
    monkeypatch.setattr(engmod.market, "fetch_candles_1m", lambda asset: [])
    monkeypatch.setattr(engmod.market, "fetch_price", lambda asset: price)
    monkeypatch.setattr(engmod.newsmod, "fetch_news", lambda cats, lb, now: rss_items or [])
    monkeypatch.setattr(engmod, "notify", lambda text, title=None: None)
    return eng


def test_full_cycle_scan_track_summary(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0006, noise=0.0004, seed=7,
                           start_ts=int(now.timestamp()) - 500 * 300)
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    sigs = eng.scan(now)
    assert len(sigs) == 3  # même série pour les 3 actifs → 3 signaux long
    assert all(s.direction == "long" for s in sigs)
    assert len(eng.store.open_signals()) == 3

    # un second scan immédiat ne produit rien (signal ouvert + cooldown)
    assert eng.scan(now + timedelta(minutes=5)) == []

    # suivi : le prix atteint le TP de tous les signaux
    from trading_bot import engine as engmod
    monkeypatch.setattr(engmod.market, "fetch_price", lambda asset: 10 ** 9)
    closed = eng.track(now + timedelta(minutes=20))
    assert len(closed) == 3 and all(s.status == "tp" for s in closed)
    assert eng.store.open_signals() == [] and len(eng.store.history()) == 3
    assert eng.store.adjustments()["sample"] == 3

    text = eng.summary(now.date(), send=False)
    assert "Signaux proposés : 3" in text and "Gagnants (TP) : 3" in text


def test_daily_limit_and_cooldown(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0006, noise=0.0004, seed=7, start_ts=int(now.timestamp()) - 500 * 300)
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    eng.cfg.max_signals_per_asset_per_day = 1
    assert len(eng.scan(now)) == 3
    from trading_bot import engine as engmod
    monkeypatch.setattr(engmod.market, "fetch_price", lambda asset: 10 ** 9)
    eng.track(now + timedelta(minutes=10))
    # plus de signaux le même jour, même avec un setup parfait, même après le cooldown
    later = now + timedelta(hours=3)
    candles2 = make_candles(n=500, drift=0.0006, noise=0.0004, seed=7, start_ts=int(later.timestamp()) - 500 * 300)
    monkeypatch.setattr(engmod.market, "fetch_candles_5m", lambda asset, days=5: candles2)
    assert eng.scan(later) == []


def test_news_risk_blocks_signal(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0006, noise=0.0004, seed=7, start_ts=int(now.timestamp()) - 500 * 300)
    items = [news.NewsItem("Fed rate decision shocks Wall Street, Nasdaq plunges", "", now, "x", "macro"),
             news.NewsItem("Bitcoin ETF decision and exchange hack", "", now, "x", "crypto")]
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close, rss_items=items)
    sigs = eng.scan(now)
    assert all(s.asset == "gold" for s in sigs)  # nasdaq et bitcoin bloqués par l'actualité


def test_stale_candles_skipped(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0006, noise=0.0004, seed=7, start_ts=int(now.timestamp()) - 600 * 300)
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    assert eng.scan(now) == []


def test_tick_scans_only_on_interval(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0006, noise=0.0004, seed=7, start_ts=int(now.timestamp()) - 500 * 300)
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    r1 = eng.tick(now)
    assert len(r1["new"]) == 3
    r2 = eng.tick(now + timedelta(minutes=5))
    assert r2["new"] == [] and r2["closed"] == []


def test_4xx_is_not_retried(monkeypatch):
    import requests

    from trading_bot.providers import http as h

    calls = []

    class R:
        status_code = 451
        def json(self): return {}
        def raise_for_status(self): raise requests.HTTPError("451")

    monkeypatch.setattr(h.requests, "get", lambda *a, **k: (calls.append(1), R())[1])
    monkeypatch.setattr(h.time, "sleep", lambda s: None)
    import pytest
    with pytest.raises(h.ProviderError):
        h.get_json("https://example.invalid/x", retries=3)
    assert len(calls) == 1
