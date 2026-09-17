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
    assert score2 == 1  # macro critique non liée : 1 point ; piratage crypto non lié à l'or : 0
    # titres hors sujet (finances personnelles, action isolée) : aucun point
    noise = [news.NewsItem("I have $125,000 in credit-card debt. Will it affect my bankruptcy?", "", items[0].published, "x", "macro"),
             news.NewsItem("Generac's stock soars 30% after Amazon deal", "", items[0].published, "x", "macro"),
             news.NewsItem("Fed rate decision looms as Powell speaks", "", items[0].published, "y", "macro")]  # doublon
    score3, hits3 = news.risk_score(items + noise, ("nasdaq", "fed"))
    assert score3 == 2 and len(hits3) == 1


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
    cfg.assets["sp500"].session_utc = None
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
    candles = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7,
                           start_ts=int(now.timestamp()) - 500 * 300)
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    sigs = eng.scan(now)
    # même série pour les 5 actifs, mais plafond de 4 signaux ouverts simultanés
    assert len(sigs) == 4
    assert all(s.direction == "long" for s in sigs)
    assert len(eng.store.open_signals()) == 4
    assert eng.store.report_file.exists() and eng.store.dashboard_file.exists()

    # un second scan immédiat ne produit rien (signal ouvert + cooldown)
    assert eng.scan(now + timedelta(minutes=5)) == []

    # suivi : le prix atteint le TP de tous les signaux
    from trading_bot import engine as engmod
    monkeypatch.setattr(engmod.market, "fetch_price", lambda asset: 10 ** 9)
    closed = eng.track(now + timedelta(minutes=20))
    assert len(closed) == 4 and all(s.status == "tp" for s in closed)
    assert eng.store.open_signals() == [] and len(eng.store.history()) == 4
    assert eng.store.adjustments()["sample"] == 4

    text = eng.summary(now.date(), send=False)
    assert "Signaux proposés : 4" in text and "Gagnants (TP) : 4" in text
    report = eng.store.report_file.read_text(encoding="utf-8")
    assert "Trades clôturés : **4**" in report and "Par critère technique" in report


def test_daily_limit_and_cooldown(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7, start_ts=int(now.timestamp()) - 500 * 300)
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    eng.cfg.max_signals_per_asset_per_day = 1
    eng.cfg.max_open_signals = 5
    assert len(eng.scan(now)) == 5
    from trading_bot import engine as engmod
    monkeypatch.setattr(engmod.market, "fetch_price", lambda asset: 10 ** 9)
    eng.track(now + timedelta(minutes=10))
    # plus de signaux le même jour, même avec un setup parfait, même après le cooldown
    later = now + timedelta(hours=3)
    candles2 = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7, start_ts=int(later.timestamp()) - 500 * 300)
    monkeypatch.setattr(engmod.market, "fetch_candles_5m", lambda asset, days=5: candles2)
    assert eng.scan(later) == []


def test_news_risk_blocks_signal(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7, start_ts=int(now.timestamp()) - 500 * 300)
    items = [news.NewsItem("Fed rate decision shocks Wall Street, Nasdaq plunges", "", now, "x", "macro"),
             news.NewsItem("FOMC minutes: Powell warns on inflation data", "", now, "x", "macro"),
             news.NewsItem("Bitcoin ETF decision and exchange hack", "", now, "x", "crypto")]
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close, rss_items=items)
    sigs = eng.scan(now)
    assert all(s.asset == "gold" for s in sigs)  # nasdaq et bitcoin bloqués par l'actualité


def test_stale_candles_skipped(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7, start_ts=int(now.timestamp()) - 600 * 300)
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    assert eng.scan(now) == []


def test_tick_scans_only_on_interval(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7, start_ts=int(now.timestamp()) - 500 * 300)
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    r1 = eng.tick(now)
    assert len(r1["new"]) == 4
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


def test_loss_protection_and_cooldown_after_loss(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7, start_ts=int(now.timestamp()) - 500 * 300)
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    eng.cfg.max_open_signals = 1
    eng.cfg.max_losses_per_asset_per_day = 1
    from trading_bot import engine as engmod
    first = eng.scan(now)
    assert len(first) == 1 and first[0].asset == "nasdaq"
    # stop touché
    monkeypatch.setattr(engmod.market, "fetch_price", lambda asset: 1.0)
    assert eng.track(now + timedelta(minutes=5))[0].status == "sl"
    # cooldown après perte (60 min) : rien à +40 min même sur un autre passage
    later = now + timedelta(minutes=40)
    candles2 = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7, start_ts=int(later.timestamp()) - 500 * 300)
    monkeypatch.setattr(engmod.market, "fetch_candles_5m", lambda asset, days=5: candles2)
    sigs = eng.scan(later)
    assert all(s.asset != "nasdaq" for s in sigs)
    # après le cooldown, la protection quotidienne (1 stop) bloque toujours le Nasdaq
    much_later = now + timedelta(minutes=200)
    candles3 = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7, start_ts=int(much_later.timestamp()) - 500 * 300)
    monkeypatch.setattr(engmod.market, "fetch_candles_5m", lambda asset, days=5: candles3)
    monkeypatch.setattr(engmod.market, "fetch_price", lambda asset: 10 ** 9)
    eng.track(much_later)  # clôture d'éventuels signaux ouverts sur les autres actifs
    reasons = eng._policy_block("nasdaq", eng.store.all_signals(), much_later)
    assert any("protection quotidienne" in r for r in reasons)


def test_forming_candle_is_dropped_before_analysis(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 2, tzinfo=timezone.utc)
    # dernière bougie ouverte à 14:00 : en cours de formation à 14:02 → ignorée
    candles = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7, start_ts=int(now.timestamp()) - 120 - 499 * 300)
    seen = {}
    from trading_bot import engine as engmod
    real_assess = engmod.assess

    def spy(asset, cs, cfg, weights=None):
        seen["last_ts"] = cs[-1].ts
        return real_assess(asset, cs, cfg, weights)

    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    monkeypatch.setattr(engmod, "assess", spy)
    eng.scan(now)
    assert seen["last_ts"] == candles[-2].ts


def test_shadow_signals_are_tracked_silently(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7, start_ts=int(now.timestamp()) - 500 * 300)
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    notified = []
    from trading_bot import engine as engmod
    monkeypatch.setattr(engmod, "notify", lambda text, title=None: notified.append(text))
    # seuil de confiance inatteignable → aucun signal notifié, mais des fantômes (≥ 2 critères)
    eng.cfg.min_criteria = 20
    assert eng.scan(now) == []
    shadow = eng.store.open_shadow()
    assert len(shadow) == 5 and all(s.source == "shadow" for s in shadow)
    assert notified == []
    # suivi : les fantômes se clôturent sans notification et alimentent l'historique
    monkeypatch.setattr(engmod.market, "fetch_price", lambda asset: 10 ** 9)
    assert eng.track(now + timedelta(minutes=10)) == []
    assert eng.store.open_shadow() == [] and len(eng.store.history()) == 5
    assert notified == []
    # les fantômes n'apparaissent pas dans les compteurs du résumé, mais sont mentionnés à part
    text = eng.summary(now.date(), send=False)
    assert "Signaux proposés : 0" in text and "Signaux fantômes du jour" in text and ": 5" in text
    dash = __import__("json").loads(eng.store.dashboard_file.read_text(encoding="utf-8"))
    assert dash["overview"]["shadow"]["n"] == 5 and dash["overview"]["visible"]["n"] == 0
    assert any(c["by_source"]["shadow"]["n"] > 0 for c in dash["criteria"])


def test_manual_signal_is_notified_and_tracked(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0, noise=0.0008, seed=9, start_ts=int(now.timestamp()) - 500 * 300)
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    notified = []
    from trading_bot import engine as engmod
    monkeypatch.setattr(engmod, "notify", lambda text, title=None: notified.append(text))
    sig = eng.manual("bitcoin", "short", now, note="test")
    assert sig.source == "manual" and sig.direction == "short" and sig.stop_loss > sig.entry > sig.take_profit
    assert len(notified) == 1 and "SIGNAL MANUEL" in notified[0] and "test" in notified[0]
    assert eng.store.open_signals()[0].id == sig.id
    import pytest
    with pytest.raises(ValueError):
        eng.manual("inconnu", "long", now)
    with pytest.raises(ValueError):
        eng.manual("bitcoin", "haut", now)


def test_propose_with_and_without_direction(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    trending = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7, start_ts=int(now.timestamp()) - 500 * 300)
    eng = _engine(tmp_path, monkeypatch, trending, trending[-1].close)
    notified = []
    from trading_bot import engine as engmod
    monkeypatch.setattr(engmod, "notify", lambda text, title=None: notified.append(text))
    res = eng.propose("bitcoin", now)
    assert res["proposed"] and res["signal"]["source"] == "request"
    assert "ANALYSE À LA DEMANDE" in notified[-1] and "Lecture des indicateurs" in notified[-1]
    assert eng.store.open_signals()[0].source == "request"
    # second appel : signal déjà ouvert → pas de doublon
    res2 = eng.propose("bitcoin", now + timedelta(minutes=5))
    assert not res2["proposed"] and res2["reason"] == "signal déjà ouvert"
    # marché sans direction → abstention expliquée, rien d'ouvert
    flat = make_candles(n=500, drift=0.0, noise=0.0008, seed=9, start_ts=int(now.timestamp()) - 500 * 300)
    monkeypatch.setattr(engmod.market, "fetch_candles_5m", lambda asset, days=5: flat)
    res3 = eng.propose("gold", now)
    assert not res3["proposed"] and "abstiens" in notified[-1]
    assert all(s.asset != "gold" for s in eng.store.open_signals())


def test_telegram_commands(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0003, noise=0.0012, seed=7, start_ts=int(now.timestamp()) - 500 * 300)
    eng = _engine(tmp_path, monkeypatch, candles, candles[-1].close)
    sent = []
    from trading_bot import engine as engmod
    monkeypatch.setattr(engmod, "notify", lambda text, title=None: sent.append(text))
    monkeypatch.setattr(engmod, "telegram_chat_id", lambda: "42")
    ts = int(now.timestamp())
    updates = [
        {"update_id": 1, "chat_id": "42", "text": "/help", "date": ts},
        {"update_id": 2, "chat_id": "99", "text": "/long btc", "date": ts},          # chat non autorisé
        {"update_id": 3, "chat_id": "42", "text": "/short xyz", "date": ts},         # actif inconnu
        {"update_id": 4, "chat_id": "42", "text": "/long eth cassure", "date": ts},  # manuel
        {"update_id": 5, "chat_id": "42", "text": "/status", "date": ts},
        {"update_id": 6, "chat_id": "42", "text": "/propose nq", "date": ts - 7 * 3600},  # trop ancien
        {"update_id": 7, "chat_id": "42", "text": "bonjour", "date": ts},            # pas une commande
    ]
    seen_offsets = []
    monkeypatch.setattr(engmod, "telegram_updates", lambda offset=None: (seen_offsets.append(offset), updates)[1])
    n = eng.process_commands(now)
    assert n == 5
    assert seen_offsets == [None]
    assert eng.store.state()["telegram_offset"] == 8
    assert any("Commandes disponibles" in s for s in sent)
    assert any("Actif inconnu" in s for s in sent)
    assert any("SIGNAL MANUEL" in s and "Ethereum" in s for s in sent)
    assert sent[-1].startswith("📡 SIGNAL") and "Entrée visée" in sent[-1]   # /status
    assert not any("Nasdaq" in s for s in sent)
    open_sigs = eng.store.open_signals()
    assert len(open_sigs) == 1 and open_sigs[0].asset == "ethereum" and open_sigs[0].source == "manual"
    # sans chat configuré : rien n'est lu
    monkeypatch.setattr(engmod, "telegram_chat_id", lambda: None)
    assert eng.process_commands(now) == 0
