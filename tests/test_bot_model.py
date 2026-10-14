"""Bot appris (essai 25) : le modèle écarte les signaux de l'or et du Nasdaq dont le R prévu n'est pas > 0."""
from types import SimpleNamespace

from trading_bot import bot_model


def _sig(asset="gold"):
    return SimpleNamespace(asset=asset, criteria=["trend_5m", "adx"], meta={"ctx": {"adx": 30, "cost_r": 0.2}},
                           created_at="2026-10-14T14:05:00Z", score=5.0, direction="long")


def test_features_shape_and_flags():
    x = bot_model.features(["trend_5m", "vwap"], {"ctx": {"adx": 25}}, "2026-10-14T06:00:00Z", 4.0, "short", "nasdaq")
    assert len(x) == len(bot_model.CRITERIA) + len(bot_model.CTX) + 1 + 4 + len(bot_model.ASSETS)
    assert x[0] == 1.0 and x[bot_model.CRITERIA.index("vwap")] == 1.0 and x[-3] == 1.0


def test_rejects_only_on_applied_assets(monkeypatch):
    monkeypatch.setattr(bot_model, "APPLIED", {"gold", "nasdaq"})
    monkeypatch.setattr(bot_model, "predicted_r", lambda s: -0.1 if s.asset == "gold" else 0.2)
    assert bot_model.rejects(_sig("gold")) and not bot_model.rejects(_sig("nasdaq"))
    assert not bot_model.rejects(_sig("sp500"))


def test_missing_model_rejects(monkeypatch):
    monkeypatch.setattr(bot_model, "APPLIED", {"gold"})
    monkeypatch.setattr(bot_model, "load", lambda path=None: None)
    s = _sig()
    assert bot_model.rejects(s) and s.meta["model_r"] is None


def test_saved_model_predicts():
    bot_model._cache.clear()
    m = bot_model.load()
    if m is None:                                    # bibliothèque absente : rien à vérifier ici
        return
    assert isinstance(bot_model.predicted_r(_sig()), float)
