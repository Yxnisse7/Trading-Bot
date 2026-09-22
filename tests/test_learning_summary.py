from datetime import datetime, timedelta, timezone

from trading_bot.analysis import DEFAULT_WEIGHTS
from trading_bot.learning import analyze, learn, win_rate
from trading_bot.models import Signal, iso
from trading_bot.summary import daily_summary

T0 = datetime(2026, 9, 17, 13, 0, tzinfo=timezone.utc)


def _closed(i: int, status: str, criteria: list[str], asset="nasdaq", conf="moyen") -> Signal:
    created = T0 + timedelta(minutes=10 * i)
    pnl = {"tp": 0.5, "sl": -0.3, "expired": 0.05}[status]
    return Signal(id=f"s{i}", asset=asset, asset_label=asset, direction="long", entry=100.0,
                  take_profit=100.5, stop_loss=99.7, risk_reward=1.67, confidence=conf, score=3.5,
                  criteria=criteria, rationale="", news_context="actualité calme",
                  created_at=iso(created), expires_at=iso(created + timedelta(hours=1)), status=status,
                  closed_at=iso(created + timedelta(minutes=30)), close_price=100.0 + pnl, pnl_pct=pnl,
                  duration_minutes=30)


def test_win_rate_ignores_expired():
    sigs = [_closed(0, "tp", []), _closed(1, "sl", []), _closed(2, "expired", []), _closed(3, "tp", [])]
    assert win_rate(sigs) == 2 / 3
    assert win_rate([]) is None


def _trade(i, status, criteria, source="bot", asset="nasdaq", hour=None, variant=None):
    s = _closed(i, status, criteria, asset=asset)
    s.source = source
    if hour is not None:
        created = datetime(2026, 9, 17, hour, 0, tzinfo=timezone.utc) + timedelta(days=i)
        s.created_at = iso(created)
    if variant:
        s.meta["variant"] = variant
    return s


def test_learn_is_stateless_and_deterministic(cfg):
    """Même données → mêmes poids, quel que soit l'état précédent : aucun trade compté deux fois."""
    hist = [_trade(i, "sl", ["volume"]) for i in range(60)] + [_trade(100 + i, "tp", ["macd"]) for i in range(60)]
    a = learn(hist, cfg)
    b = learn(hist, cfg, {"weights": {"volume": 0.01, "macd": 9.0}})   # ancien état ignoré
    c = learn(hist, cfg)
    assert a["weights"] == b["weights"] == c["weights"]


def test_learn_ignores_small_samples_and_noise(cfg):
    # 10 stops : trop peu de trades pour conclure → poids par défaut
    few = learn([_trade(i, "sl", ["volume"]) for i in range(10)], cfg)
    assert few["weights"]["volume"] == DEFAULT_WEIGHTS["volume"]
    # 60 trades autour du hasard (≈ 0 R) → aucun écart prouvé → poids par défaut
    mixed = [_trade(i, "tp" if i % 8 < 3 else "sl", ["rsi"]) for i in range(64)]   # 3 TP pour 5 SL ≈ 0 R
    adj = learn(mixed, cfg)
    assert adj["weights"]["rsi"] == DEFAULT_WEIGHTS["rsi"]
    assert any("aucun critère ne s'écarte" in n for n in adj["notes"])


def test_learn_moves_weights_only_beyond_margin(cfg):
    bad = [_trade(i, "sl", ["volume"]) for i in range(60)]
    good = [_trade(100 + i, "tp" if i % 5 else "sl", ["macd"]) for i in range(60)]
    adj = learn(bad + good, cfg)
    assert adj["weights"]["volume"] < DEFAULT_WEIGHTS["volume"]
    assert adj["weights"]["macd"] > DEFAULT_WEIGHTS["macd"]
    assert adj["weights"]["rsi"] == DEFAULT_WEIGHTS["rsi"]
    assert 0.25 <= min(adj["weights"].values()) and max(adj["weights"].values()) <= 1.5
    st = adj["stats"]["macd"]
    assert st["mean_r"] > st["margin_r"] > 0            # écart prouvé : au-delà de la marge


def test_learn_weights_real_trades_more_than_backtest(cfg):
    """40 vrais TP contre 120 stops de backtest : le réel l'emporte grâce à la pondération des sources."""
    hist = [_trade(i, "tp", ["macd"]) for i in range(40)] + [_trade(100 + i, "sl", ["macd"], source="backtest") for i in range(120)]
    adj = learn(hist, cfg)
    assert adj["stats"]["macd"]["mean_r"] > 0
    unweighted = sum((1.667 if s.status == "tp" else -1.0) for s in hist) / len(hist)
    assert unweighted < 0                                 # sans pondération, la conclusion serait inverse


def test_learn_judges_trend_family_as_one(cfg):
    hist = [_trade(i, "sl", ["trend_5m", "adx"]) for i in range(60)]
    adj = learn(hist, cfg)
    w = adj["weights"]
    assert w["trend_5m"] == w["trend_15m"] == w["trend_1h"] == w["adx"] < 1.0
    assert "tendance" in adj["stats"] and "trend_5m" not in adj["stats"]


def test_learn_per_asset_correction_over_global_base(cfg):
    """Socle global + correction par actif, seulement si l'écart de l'actif est prouvé."""
    neutral = [_trade(i, "tp" if i % 8 < 3 else "sl", ["rsi"], asset="nasdaq") for i in range(160)]
    bad_eth = [_trade(500 + i, "sl", ["rsi"], asset="ethereum") for i in range(40)]
    few_gold = [_trade(900 + i, "sl", ["rsi"], asset="gold") for i in range(5)]
    adj = learn(neutral + bad_eth + few_gold, cfg)
    g = adj["weights"]["rsi"]
    assert adj["weights_by_asset"]["ethereum"]["rsi"] < g                       # écart prouvé → corrigé
    assert adj["weights_by_asset"]["gold"]["rsi"] == g                           # 5 trades → suit le global
    assert any(n.startswith("ethereum") for n in adj["notes"])


def test_learn_avoids_hours_only_when_clearly_losing(cfg):
    hist = [_trade(i, "sl", ["rsi"], hour=3) for i in range(40)] + [_trade(100 + i, "tp" if i % 8 < 3 else "sl", ["rsi"], hour=15) for i in range(40)]
    adj = learn(hist, cfg)
    assert adj["avoid_hours_utc"] == [3]


def test_variant_promotion_rule(cfg):
    bot = [_trade(i, "tp" if i % 8 < 3 else "sl", ["rsi"]) for i in range(40)]             # ≈ 0 R brut, négatif net
    good = [_trade(100 + i, "tp" if i % 2 else "sl", ["rsi"], source="shadow", variant="horizon_3h") for i in range(100)]
    short = [_trade(300 + i, "tp", ["rsi"], source="shadow", variant="hors_session") for i in range(99)]
    worse = [_trade(500 + i, "sl", ["rsi"], source="shadow", variant="confiance_moyenne") for i in range(120)]
    adj = learn(bot + good + short + worse, cfg)
    assert adj["promoted_variants"] == ["horizon_3h"]
    assert adj["variants"]["hors_session"]["missing"] == 1 and not adj["variants"]["hors_session"]["promoted"]
    assert not adj["variants"]["confiance_moyenne"]["promoted"]
    assert any("promue" in n for n in adj["notes"])


def test_analyze_groups(cfg):
    hist = [_closed(0, "tp", ["rsi"], asset="gold"), _closed(1, "sl", ["rsi", "macd"], asset="bitcoin")]
    rep = analyze(hist)
    assert rep["total"] == 2
    assert rep["by_asset"]["gold"]["tp"] == 1
    assert rep["by_criterion"]["rsi"]["n"] == 2 and rep["by_criterion"]["macd"]["sl"] == 1


def test_daily_summary_content(cfg):
    hist = [_closed(0, "tp", ["rsi"]), _closed(1, "sl", ["rsi"]), _closed(2, "expired", ["rsi"])]
    text = daily_summary(hist, cfg, T0.date(), {"notes": ["rsi: test"], "avoid_hours_utc": []})
    assert "Signaux proposés : 3" in text
    assert "Gagnants (TP) : 1 | Perdants (SL) : 1 | Expirés sans issue : 1" in text
    assert "Taux de réussite du jour : 50%" in text
    assert "paper trading" not in text   # l'avertissement complet n'est plus répété à chaque message, il est dans le guide
    assert "rsi: test" in text


def test_neutral_win_rate_and_edge(cfg):
    # TP à +0.5, SL à -0.3 → hasard attendu = 0.3 / 0.8 = 37.5 %
    hist = [_closed(i, "tp", ["rsi"]) for i in range(6)] + [_closed(10 + i, "sl", ["rsi"]) for i in range(4)]
    rep = analyze(hist)
    assert rep["neutral_win_rate"] == 0.375
    assert rep["overall"]["win_rate"] == 0.6
    assert abs(rep["edge"] - 0.225) < 1e-9
    text = daily_summary(hist, cfg, T0.date())
    assert "hasard attendu 38%" in text
