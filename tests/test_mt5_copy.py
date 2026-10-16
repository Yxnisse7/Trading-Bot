from types import SimpleNamespace as NS

from trading_bot import mt5_copy as mc

NOW = 1_791_950_000


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1
    ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1
    TRADE_ACTION_DEAL, ORDER_TIME_GTC = 1, 0
    ORDER_FILLING_FOK, ORDER_FILLING_IOC, ORDER_FILLING_RETURN = 0, 1, 2
    TRADE_RETCODE_DONE = 10009

    def __init__(self):
        self.sent, self.pos = [], []

    def account_info(self):
        return NS(trade_mode=0, balance=1000.0)

    def history_deals_get(self, lo, hi):
        return []

    def symbol_select(self, sym, on):
        return True

    def symbol_info(self, sym):
        return NS(trade_contract_size=100.0, volume_step=0.01, volume_min=0.01, volume_max=100.0, digits=2,
                  trade_stops_level=20, point=0.01, filling_mode=1)

    def symbol_info_tick(self, sym):
        return NS(bid=4200.0, ask=4200.2)

    def positions_get(self):
        return self.pos

    def order_send(self, req):
        self.sent.append(req)
        if "position" not in req:
            self.pos.append(NS(ticket=555, magic=mc.MAGIC, symbol=req["symbol"], type=req["type"], volume=req["volume"]))
        return NS(retcode=self.TRADE_RETCODE_DONE, price=req["price"], order=555)


def site(signals):
    def get(url):
        if "lab_shadow" in url:
            return {}
        return {"open_signals": signals if "gold" in url else []}
    return get


def sig(**kw):
    s = {"id": "abc", "direction": "short", "entry": 4210.0, "stop_loss": 4218.0, "take_profit": 4202.0,
         "source": "bot", "created_at": "2026-10-14T13:50:00Z", "expires_at": "2026-10-14T15:00:00Z"}
    s.update(kw)
    return s


def test_copies_a_fresh_bot_signal_with_its_distances_and_five_percent_risk(tmp_path):
    mt5 = FakeMT5()
    created = mc._ts("2026-10-14T13:50:00Z")
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: created + 60, get=site([sig()]))
    c.step()
    req = mt5.sent[0]
    assert req["symbol"] == "XAUUSD+" and req["type"] == mt5.ORDER_TYPE_SELL
    assert req["sl"] == 4208.0 and req["tp"] == 4192.0              # 8 $ de stop, 8 $ d'objectif autour de 4 200
    assert req["volume"] == 0.06                                    # 5 % de 1 000 $ / (8 $ × 100) = 0,0625 → 0,06
    c.last = 0
    c.step()
    assert len(mt5.sent) == 1                                       # pas de doublon


def test_old_signals_are_not_copied_and_closed_signals_are_closed(tmp_path):
    mt5 = FakeMT5()
    created = mc._ts("2026-10-14T13:50:00Z")
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: created + 3600, get=site([sig()]))
    c.step()
    assert mt5.sent == []
    c2 = mc.Copier(FakeMT5(), tmp_path / "b", lambda *a, **k: None, lambda: created + 60, get=site([sig()]))
    c2.step()
    c2.get, c2.last = site([]), 0
    c2.step()
    assert "position" in c2.mt5.sent[-1]                            # le bot a fermé le signal : on ferme


def test_shadow_signals_and_real_accounts_are_ignored(tmp_path):
    mt5 = FakeMT5()
    created = mc._ts("2026-10-14T13:50:00Z")
    mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: created + 60, get=site([sig(source="shadow")])).step()
    assert mt5.sent == []
    mt5.account_info = lambda: NS(trade_mode=2, balance=1000.0)
    c = mc.Copier(mt5, tmp_path / "r", lambda *a, **k: None, lambda: created + 60, get=site([sig()]))
    assert "réel" in c.step() and mt5.sent == []


def test_min_lot_exception_for_asian_night():
    from types import SimpleNamespace
    info = SimpleNamespace(trade_contract_size=100.0, volume_step=0.01, volume_min=0.01, volume_max=1.0)
    assert mc.lot_for(1000, 41.0, info, mc.MIN_LOT_MAX_RISK["nuit_asie"]) == 0.01   # 41 $ : 4,1 %, sous 5 %
    assert mc.lot_for(1000, 90.0, info) == 0.01                    # lot minimum toléré jusqu'à 2 × 5 % = 10 %
    assert mc.lot_for(1000, 120.0, info) == 0.0                    # 12 % : pas copié


def test_zero_quote_is_retried_not_sent(tmp_path, monkeypatch):
    """Le 14/10, NAS100 : premier prix à 0 juste après symbol_select → ordre envoyé avec un stop à 64 et rejeté."""
    monkeypatch.setattr(mc.time, "sleep", lambda s: None)
    mt5 = FakeMT5()
    mt5.symbol_info_tick = lambda sym: NS(bid=0.0, ask=0.0)
    created = mc._ts("2026-10-14T13:50:00Z")
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: created + 60, get=site([sig()]))
    c.step()
    assert mt5.sent == []
    mt5.symbol_info_tick = lambda sym: NS(bid=4200.0, ask=4200.2)       # la cotation arrive : copie au passage suivant
    c.last = 0
    c.step()
    assert len(mt5.sent) == 1 and mt5.sent[0]["sl"] == 4208.0


def test_floor_of_dollars_per_point():
    """Choix de Yanisse le 14/10 : au moins 0,50 $ par point sur le NAS100, si le risque reste sous 10 %."""
    nas = NS(trade_contract_size=1.0, volume_step=0.01, volume_min=0.01, volume_max=100.0)
    assert mc.floor_lot(0.15, 1000, 64.0, nas, 0.5) == 0.5          # 32 $ au stop, 3,2 %
    assert mc.floor_lot(0.15, 1000, 250.0, nas, 0.5) == 0.0         # 125 $ au stop : trop risqué, pas copié
    assert mc.floor_lot(0.8, 1000, 10.0, nas, 0.5) == 0.8           # déjà au-dessus
    assert mc.floor_lot(0.02, 1000, 500.0, nas, None) == 0.02       # pas de plancher (cryptos)


def test_asian_night_is_copied_at_least_at_005_lot(tmp_path):
    """Choix de Yanisse le 16/10 : nuit asiatique au moins 0,05 lot, même si le stop de sécurité (1 %) dépasse 5 %."""
    mt5 = FakeMT5()
    created = mc._ts("2026-10-14T22:00:00Z")
    lab = {"nuit_asie|gold": {"strategy": "nuit_asie", "asset": "gold", "trades": [
        {"status": "open", "notified_entry": True, "direction": "long", "entry": 4200.0, "risk": 42.0,
         "entry_ts": created, "close_at": created + 9 * 3600}]}}
    get = lambda url: lab if "lab_shadow" in url else {"open_signals": []}
    mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: created + 60, get=get).step()
    assert mt5.sent[0]["volume"] == 0.05
