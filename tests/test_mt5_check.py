"""Contrôle du soir : signaux annoncés contre trades pris (28/10/2026)."""
from datetime import datetime, timezone
from types import SimpleNamespace as NS

from trading_bot import mt5_check as ck

NOW = datetime(2026, 10, 27, 22, 40, tzinfo=timezone.utc).timestamp()          # 23 h 40 à Paris
SEEN = datetime(2026, 10, 27, 13, 5, tzinfo=timezone.utc).timestamp()


def _state():
    return {
        "lab:bot:1": {"asset": "nasdaq", "direction": "long", "status": "ouvert", "seen": SEEN},
        "lab:bot:2": {"asset": "nasdaq", "direction": "long", "status": "fermé", "seen": SEEN + 60},
        "lab:cassure_williams:3": {"asset": "bitcoin", "direction": "long", "seen": SEEN + 120,
                                   "status": "rejeté (code 10018)"},
        "lab:nuit_asie:4": {"asset": "gold", "direction": "long", "seen": SEEN + 180,
                            "status": "taille minimale trop risquée"},
        "lab:bot:5": {"asset": "nasdaq", "direction": "long", "seen": SEEN + 240, "status": "même signal que lab:bot:1"},
        "lab:bot:6": {"asset": "nasdaq", "direction": "long", "status": "ouvert", "seen": SEEN - 3 * 86400},
    }


def test_report_counts_taken_missed_and_explains():
    text = ck.report(_state(), NOW)
    assert "4 signal(aux) annoncé(s) · <b>2 pris sur MT5</b> · 2 raté(s)" in text
    assert "1 doublon" in text
    assert "cassure Williams · Bitcoin · achat : MT5 a refusé l'ordre (code 10018)" in text
    assert "nuit asiatique · Or · achat : le lot minimum risquait trop pour ton solde" in text
    assert "bot classique · Nasdaq" not in text.split("\n", 3)[-1]               # les trades pris ne sont pas listés
    assert "Aucun signal" in ck.report({}, NOW)
    assert "Tout ce qui a été annoncé" in ck.report({"lab:bot:1": _state()["lab:bot:1"]}, NOW)


def test_daily_check_is_sent_once_after_23h30_on_weekdays(tmp_path):
    sent, now = [], [NOW - 3600]
    relay = NS(enabled=lambda: True, _post=lambda body, reply=None: sent.append(body))
    d = ck.DailyCheck(NS(state=_state()), relay, tmp_path, lambda: now[0])
    assert d.step() == "" and not sent                                              # 22 h 40 à Paris : trop tôt
    now[0] = NOW
    assert d.step() == "contrôle du soir envoyé" and "Contrôle du soir" in sent[0]
    now[0] += 60
    assert d.step() == "" and len(sent) == 1                                        # une seule fois par jour
    d2 = ck.DailyCheck(NS(state=_state()), relay, tmp_path, lambda: now[0])
    assert d2.step() == "" and len(sent) == 1                                       # même après un redémarrage
    now[0] = datetime(2026, 10, 31, 22, 40, tzinfo=timezone.utc).timestamp()        # samedi
    assert d2.step() == ""
