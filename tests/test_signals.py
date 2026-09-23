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
    for needle in ("ACHAT", "Entrée", "TP ", "SL ", "Gain/risque", "Pourquoi", "Actualité", "Zone d'entrée"):
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


def test_telegram_message_formats():
    from datetime import datetime, timedelta, timezone
    from trading_bot import messages as m
    from trading_bot.models import Signal, iso
    now = datetime(2026, 9, 22, 19, 30, tzinfo=timezone.utc)
    sig = Signal(id="x", asset="sp500", asset_label="S&P 500 (ES)", direction="short", entry=7832.5, take_profit=7822.5,
                 stop_loss=7839.25, risk_reward=1.48, confidence="fort", score=6, criteria=["trend_5m", "trend_1h", "adx", "pdhl"],
                 rationale="… probabilité de résolution sous 1 h ≈ 95%.", news_context="actualité à surveiller (score 3) : Fed's Barkin | autre",
                 created_at=iso(now), expires_at=iso(now + timedelta(hours=1)), meta={"tick": 0.25, "price_time": iso(now - timedelta(minutes=6))})
    text = m.signal_text(sig, now=now, history=m.history_line(sig.asset_label, {"n": 12, "tp": 7, "sl": 4, "win_rate": 7 / 11, "neutral_win_rate": 0.41}))
    assert "S&amp;P 500" in text and "<code>7832,50</code>" in text          # HTML échappé, prix copiables
    assert "↘️ VENTE" in text and "−0,13 %" in text and "+0,09 %" in text
    assert "il y a 6 min" in text and "expire à 22:30" in text
    assert "tendance 5 min · 1 h, tendance forte, niveaux de la veille" in text
    assert "probabilité" not in text and "Fed's Barkin" in text and "autre" not in text
    assert "64 % gagnants sur 11, hasard 41 %" in text
    assert "sous 7831,00" in text and "Actualité : ⚠️ à surveiller : Fed's Barkin" in text                                             # zone d'entrée d'une vente
    assert m.history_line("Or (XAU/USD)", {"n": 2, "tp": 1, "sl": 1}).endswith("pas encore de recul")
    line = m.sizing_line({"lots": 1, "lot_label": "MNQ", "risk_amount": 53.5, "risk_pct_effective": 8.76, "risky": True,
                          "leverage": 101.52, "warnings": ["lot minimal 1 MNQ imposé : risque au stop 53.50 au lieu de 61.09 visé",
                                                           "levier ×101.5 au-delà du plafond ×20"]})
    assert line == "Simulation : 1 MNQ · risque 53,50 $ (8,8 %) · ⚠️ levier ×102"
    assert m.streak_text([sig.__class__(**{**sig.__dict__, "status": st}) for st in ("sl", "tp", "tp", "tp")]) == "3e gain d'affilée"
    assert m.strip_html("<b>A</b> &amp; <code>1</code>") == "A & 1"
