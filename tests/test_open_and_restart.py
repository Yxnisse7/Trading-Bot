"""SL adaptés à l'heure, entrées avant l'ouverture américaine et reprise après un stop (variantes silencieuses)."""
from datetime import datetime, timedelta, timezone

from trading_bot import engine as engmod
from trading_bot import indicators as ind
from trading_bot.analysis import Assessment
from trading_bot.config import Config, default_assets
from trading_bot.engine import Engine
from trading_bot.halal import halal_config
from trading_bot.models import Candle, Signal, iso
from trading_bot.storage import Store

from conftest import make_candles

THU = datetime(2026, 9, 17, 0, 0, tzinfo=timezone.utc)   # jeudi, heure d'été à New York


def _strong(asset, candles, cfg, weights=None, **kw):
    price = candles[-1].close
    return Assessment(asset.key, price, "short", 6.0, ["adx", "macd", "rsi", "trend_15m", "trend_1h", "trend_5m"],
                      hourly_range=price * 0.01, atr=price * 0.002, sigma_5m=0.004, horizon_minutes=60, base_minutes=5)


def _engine(tmp_path, monkeypatch, now):
    cfg = Config(assets=default_assets())
    cfg.long_horizon_enabled = False
    eng = Engine(cfg, Store(tmp_path))
    candles = make_candles(n=400, start_ts=int(now.timestamp()) - 400 * 300)
    monkeypatch.setattr(engmod.market, "fetch_candles_5m", lambda asset, days=5: candles)
    monkeypatch.setattr(engmod.market, "fetch_price", lambda asset: candles[-1].close)
    monkeypatch.setattr(engmod.newsmod, "fetch_news", lambda cats, lb, now: [])
    monkeypatch.setattr(engmod.calmod, "fetch_events", lambda f: [])
    monkeypatch.setattr(engmod, "notify", lambda text, **kw: None)
    monkeypatch.setattr(engmod, "assess", _strong)
    monkeypatch.setattr(Engine, "correlation_context", lambda self, now: {})
    return eng


def test_us_open_follows_new_york_time():
    assert ind.us_open_ts(int(THU.timestamp())) == int(THU.replace(hour=13, minute=30).timestamp())
    winter = datetime(2026, 12, 3, tzinfo=timezone.utc)
    assert ind.us_open_ts(int(winter.timestamp())) == int(winter.replace(hour=14, minute=30).timestamp())


def test_same_hour_range_sees_the_busy_open():
    """Nuit calme, ouverture agitée : la même heure les jours précédents donne un range bien plus grand."""
    candles = []
    start = int(THU.timestamp()) - 5 * 86400
    price = 100.0
    for i in range(5 * 288):
        ts = start + i * 300
        busy = 13 * 3600 + 1800 <= ts % 86400 < 14 * 3600 + 1800
        amp = 0.004 if busy else 0.0004
        candles.append(Candle(ts, price, price * (1 + amp), price * (1 - amp), price, 1000.0))
    now_idx = next(i for i, c in enumerate(candles) if c.ts % 86400 == 13 * 3600 + 1500 and c.ts > start + 4 * 86400)
    window = candles[:now_idx + 1]
    avg24 = ind.average_range(window, 3600, buckets=24)
    same = ind.same_hour_range(window, 3600)
    assert same > 3 * avg24


def test_entries_before_the_us_open_are_silent(tmp_path, monkeypatch):
    now = THU.replace(hour=13, minute=10)                  # 15:10 à Paris, 20 min avant l'ouverture
    eng = _engine(tmp_path, monkeypatch, now)
    real = eng.scan(now)
    assert real and all(eng.cfg.assets[s.asset].session_utc is None for s in real)       # cryptos seulement
    variants = {(s.asset, (s.meta or {}).get("variant")) for s in eng.store.open_shadow()}
    assert ("nasdaq", "avant_ouverture") in variants and ("sp500", "avant_ouverture") in variants


def test_restart_after_a_stop_is_tested_in_silence(tmp_path, monkeypatch):
    now = THU.replace(hour=14, minute=30)
    eng = _engine(tmp_path, monkeypatch, now)
    stop = Signal(id="s1", asset="nasdaq", asset_label="Nasdaq 100 (NQ)", direction="short", entry=100.0,
                  take_profit=99.0, stop_loss=101.0, risk_reward=1.0, confidence="fort", score=6.0, criteria=[],
                  rationale="", news_context="", created_at=iso(now - timedelta(minutes=40)),
                  expires_at=iso(now + timedelta(minutes=20)), status="sl", closed_at=iso(now - timedelta(minutes=20)),
                  close_price=101.0, pnl_pct=-1.0)
    eng.store.append_history(stop)
    real = eng.scan(now)
    assert "nasdaq" not in {s.asset for s in real}
    assert ("nasdaq", "reprise_apres_stop") in {(s.asset, (s.meta or {}).get("variant")) for s in eng.store.open_shadow()}


def test_halal_ignores_the_pre_open_window():
    cfg = halal_config()
    eng = Engine.__new__(Engine)
    eng.cfg = cfg
    assert not eng._before_us_open(THU.replace(hour=13, minute=10))
    assert default_assets()["nasdaq"].session_range and not default_assets()["bitcoin"].session_range
