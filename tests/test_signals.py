from datetime import datetime, timezone

from trading_bot.analysis import assess, confidence_label
from trading_bot.signals import build_signal, format_signal, round_to_tick


def test_uptrend_yields_long_assessment(cfg, trending_up):
    asset = cfg.asset("nasdaq")
    a = assess(asset, trending_up, cfg)
    assert a.direction == "long"
    assert "trend_5m" in a.criteria and "trend_15m" in a.criteria
    assert a.hourly_range and a.hourly_range > 0


def test_downtrend_yields_short_assessment(cfg, trending_down):
    a = assess(cfg.asset("nasdaq"), trending_down, cfg)
    assert a.direction == "short"


def test_choppy_market_gives_no_or_weak_signal(cfg, choppy):
    a = assess(cfg.asset("nasdaq"), choppy, cfg)
    sig, _ = build_signal(cfg.asset("nasdaq"), a, cfg, "calme")
    # soit aucune direction, soit convergence insuffisante : jamais de signal fort
    assert sig is None or sig.confidence != "fort"


def test_insufficient_history_rejected(cfg, trending_up):
    a = assess(cfg.asset("nasdaq"), trending_up[:50], cfg)
    assert a.direction is None and a.reasons_rejected


def test_build_signal_levels_and_rr(cfg, trending_up):
    asset = cfg.asset("nasdaq")
    a = assess(asset, trending_up, cfg)
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    sig, why = build_signal(asset, a, cfg, "actualité calme", now)
    assert sig is not None, why
    assert sig.direction == "long"
    assert sig.stop_loss < sig.entry < sig.take_profit
    assert sig.risk_reward >= cfg.min_risk_reward
    # TP borné par le range horaire (réaliste sous 1h)
    assert abs(sig.take_profit - sig.entry) <= cfg.max_tp_range_fraction * sig.hourly_range + asset.tick_size
    assert abs(sig.take_profit - sig.entry) >= cfg.min_tp_range_fraction * sig.hourly_range - asset.tick_size
    assert sig.expires_at.endswith("Z") and "15:00" in sig.expires_at
    text = format_signal(sig)
    for needle in ("LONG", "Entrée", "Take Profit", "Stop Loss", "Risque / rendement", "Confiance", "Actualité"):
        assert needle in text


def test_low_volatility_refused(cfg, trending_up):
    asset = cfg.asset("nasdaq")
    a = assess(asset, trending_up, cfg)
    a.hourly_range = a.price * 0.0001  # 0.01 % : trop calme
    sig, why = build_signal(asset, a, cfg, "calme")
    assert sig is None and any("trop faible" in w for w in why)


def test_abnormal_volatility_refused(cfg, trending_up):
    asset = cfg.asset("nasdaq")
    a = assess(asset, trending_up, cfg)
    a.hourly_range = a.price * 0.10
    sig, why = build_signal(asset, a, cfg, "calme")
    assert sig is None and any("anormale" in w for w in why)


def test_strong_confidence_required(cfg, trending_up):
    cfg.min_confidence = "fort"
    asset = cfg.asset("nasdaq")
    a = assess(asset, trending_up, cfg)
    if confidence_label(a.score, a.n_criteria, cfg) != "fort":
        sig, why = build_signal(asset, a, cfg, "calme")
        assert sig is None


def test_round_to_tick():
    assert round_to_tick(20000.13, 0.25) == 20000.25
    assert round_to_tick(65432.4, 1.0) == 65432.0
    assert round_to_tick(1.2345, 0) == 1.2345


def test_entry_guidance_zone_and_price_age():
    from datetime import datetime, timedelta, timezone
    from trading_bot.models import Signal, iso
    from trading_bot.signals import entry_guidance, format_signal
    now = datetime(2026, 9, 22, 14, 37, tzinfo=timezone.utc)
    sig = Signal(id="x", asset="nasdaq", asset_label="Nasdaq", direction="long", entry=30000.0, take_profit=30060.0,
                 stop_loss=29960.0, risk_reward=1.5, confidence="fort", score=6, criteria=["rsi"], rationale="",
                 news_context="", created_at=iso(now), expires_at=iso(now + timedelta(hours=1)),
                 meta={"tick": 0.25, "price_time": iso(now - timedelta(minutes=12))})
    lines = entry_guidance(sig, now)
    assert "il y a 12 min" in lines[0]
    # au milieu du stop et de l'objectif, gain possible = risque ; à mi-chemin du stop, scénario affaibli
    assert "de 29980 à 30010" in lines[1]
    short = Signal(**{**sig.__dict__, "direction": "short", "take_profit": 29940.0, "stop_loss": 30040.0, "meta": {"tick": 0.25}})
    assert "de 29990 à 30020" in entry_guidance(short, now)[0]
    weak = Signal(**{**sig.__dict__, "risk_reward": 0.8, "meta": {}})
    assert "déjà plus petit que le risque" in entry_guidance(weak, now)[0]
    assert "Zone d'entrée" in format_signal(sig)
