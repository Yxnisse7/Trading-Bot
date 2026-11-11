from types import SimpleNamespace as NS

from trading_bot import gardien

NOW = 1_794_400_000          # novembre 2026 : serveur à UTC+2
INFO = NS(trade_contract_size=100.0)


class MT5:
    def __init__(self, pos=(), connected=True):
        self.pos, self.connected = list(pos), connected

    def terminal_info(self):
        return NS(connected=self.connected)

    def positions_get(self):
        return self.pos

    def symbol_info(self, sym):
        return INFO


def tick(spread=0.2, age=1):
    return NS(bid=4000.0, ask=4000.0 + spread, time=NOW + 7200 - age)


def test_ordre_normal_passe():
    assert gardien.check(MT5(), "XAUUSD+", tick(), INFO, 8.0, 0.01, 1000.0, NOW) == ""


def test_terminal_deconnecte_et_prix_fige():
    assert "déconnecté" in gardien.check(MT5(connected=False), "X", tick(), INFO, 8.0, 0.01, 1000.0, NOW)
    assert "prix figé" in gardien.check(MT5(), "X", tick(age=600), INFO, 8.0, 0.01, 1000.0, NOW)


def test_ecart_anormal():
    assert "écart" in gardien.check(MT5(), "X", tick(spread=3.0), INFO, 8.0, 0.01, 1000.0, NOW)
    assert gardien.check(MT5(), "X", tick(spread=1.9), INFO, 8.0, 0.01, 1000.0, NOW) == ""


def test_risque_total():
    # déjà 2 positions qui risquent 45 $ chacune sur 1000 $, le trade en ajoute 20 : 11 % > 10 %
    pos = [NS(symbol="X", type=0, volume=0.05, price_open=4000.0, sl=3991.0),
           NS(symbol="X", type=1, volume=0.05, price_open=4000.0, sl=4009.0)]
    assert "risque total" in gardien.check(MT5(pos), "X", tick(), INFO, 20.0, 0.01, 1000.0, NOW)
    assert gardien.check(MT5(pos[:1]), "X", tick(), INFO, 20.0, 0.01, 1000.0, NOW) == ""
    # un SL déjà passé au-dessus de l'entrée (gain protégé) ne compte pas
    safe = NS(symbol="X", type=0, volume=1.0, price_open=4000.0, sl=4005.0)
    assert gardien.position_risk(safe, INFO) == 0.0


def test_annonce_proche_previent_sans_bloquer():
    ev = [{"name": "USD CPI", "impact": "high", "assets": ["gold"], "at": "2026-11-11T13:30:00+00:00"}]
    at = 1794403800
    from datetime import datetime
    at = datetime.fromisoformat(ev[0]["at"]).timestamp()
    assert "dans 3 min" in gardien.news(ev, "gold", at - 180)
    assert "il y a 1 min" in gardien.news(ev, "gold", at + 60)
    assert gardien.news(ev, "gold", at - 3600) == ""
    assert gardien.news(ev, "bitcoin", at - 60) == ""
