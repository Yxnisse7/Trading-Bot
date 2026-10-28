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


def test_copies_a_fresh_bot_signal_with_its_distances_and_two_percent_risk(tmp_path):
    mt5 = FakeMT5()
    created = mc._ts("2026-10-14T13:50:00Z")
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: created + 60, get=site([sig()]))
    c.step()
    req = mt5.sent[0]
    assert req["symbol"] == "XAUUSD+" and req["type"] == mt5.ORDER_TYPE_SELL
    assert req["sl"] == 4208.0 and req["tp"] == 4192.0              # 8 $ de stop, 8 $ d'objectif autour de 4 200
    assert req["volume"] == 0.02                                    # 2 % de 1 000 $ / (8 $ × 100) = 0,025 → 0,02
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


def test_min_lot_is_taken_up_to_the_cap():
    from types import SimpleNamespace
    info = SimpleNamespace(trade_contract_size=100.0, volume_step=0.01, volume_min=0.01, volume_max=1.0)
    assert mc.lot_for(1000, 90.0, info) == 0.01                    # 9 % du solde : lot minimum toléré (plafond 15 %)
    assert mc.lot_for(1000, 150.0, info) == 0.01                   # 15 % pile
    assert mc.lot_for(1000, 200.0, info) == 0.0                    # 20 % : pas copié


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


def test_asian_night_follows_the_same_cap_as_the_others(tmp_path):
    """26/10 : plus de lot minimum imposé par stratégie ; stop de sécurité 42 $ = 4,2 % de 1 000 $ → 0,01 lot."""
    mt5 = FakeMT5()
    created = mc._ts("2026-10-14T22:00:00Z")
    lab = {"nuit_asie|gold": {"strategy": "nuit_asie", "asset": "gold", "trades": [
        {"status": "open", "notified_entry": True, "direction": "long", "entry": 4200.0, "risk": 42.0,
         "entry_ts": created, "close_at": created + 9 * 3600}]}}
    get = lambda url: lab if "lab_shadow" in url else {"open_signals": []}
    mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: created + 60, get=get).step()
    assert mt5.sent[0]["volume"] == 0.02          # 28/10 : trade du bot pris seul = 0,02 lot au moins


def test_lab_signal_age_counts_from_the_telegram_announcement(tmp_path):
    """16/10 : annoncé 10 min après la bougie, puis lu sur GitHub quelques minutes plus tard, le signal était
    déjà « trop ancien » si l'âge partait de la bougie d'entrée."""
    mt5 = FakeMT5()
    bar = mc._ts("2026-10-16T14:00:00Z")
    lab = {"noise_area:nasdaq": {"strategy": "noise_area", "asset": "gold", "trades": [
        {"status": "open", "notified_entry": "2026-10-16T14:10:47Z", "direction": "short", "entry": 4200.0,
         "risk": 8.0, "entry_ts": bar, "close_at": bar + 8 * 3600}]}}
    get = lambda url: lab if "lab_shadow" in url else {"open_signals": []}
    mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: bar + 17 * 60, get=get).step()
    assert len(mt5.sent) == 1


def test_too_short_stop_is_widened_to_the_broker_minimum(tmp_path):
    """Un SL plus court que le minimum du courtier (écart compris) est élargi au lieu d'être rejeté (code 10016)."""
    mt5 = FakeMT5()
    created = mc._ts("2026-10-14T13:50:00Z")
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: created + 60,
                  get=site([sig(stop_loss=4210.1, take_profit=4202.0)]))
    c.step()
    req = mt5.sent[0]
    assert req["sl"] - 4200.0 >= 0.2 + 0.20 - 1e-9                  # écart 0,20 + 20 points de 0,01


class LocalMT5(FakeMT5):
    """Terminal avec des bougies 5 min d'or, serveur à UTC+3."""
    TIMEFRAME_M5 = 5
    OFF = 3 * 3600

    def __init__(self, now):
        super().__init__()
        self.now = now

    def symbol_info_tick(self, sym):
        return NS(bid=4200.0, ask=4200.2, time=int(self.now) + self.OFF)

    def copy_rates_from_pos(self, sym, tf, start, n):
        if sym != "XAUUSD+":
            return None
        t0 = int(self.now) // 300 * 300 - 300 * 1000
        return [{"time": t + self.OFF, "open": 4200.0, "high": 4201.0, "low": 4199.0, "close": 4200.0,
                 "tick_volume": 10} for t in range(t0, int(self.now) // 300 * 300 + 300, 300)]


def test_local_engine_opens_the_asian_night_at_once_and_skips_the_github_twin(tmp_path):
    """16/10 : le PC calcule la nuit asiatique sur les prix MT5 et copie dès 22:05 ; le signal de GitHub qui
    arrive ensuite pour la même nuit n'ouvre pas une 2e position."""
    from datetime import datetime, timezone
    now = datetime(2026, 10, 14, 22, 6, tzinfo=timezone.utc).timestamp()     # 18:06 à New York
    mt5 = LocalMT5(now)
    lab = {}
    get = lambda url: lab if "lab_shadow" in url else {"open_signals": []}
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: now, get=get, local=True)
    c.step()
    t22 = int(datetime(2026, 10, 14, 22, 0, tzinfo=timezone.utc).timestamp())
    assert len(mt5.sent) == 1 and mt5.sent[0]["type"] == mt5.ORDER_TYPE_BUY
    assert c.state[f"lab:nuit_asie:{t22}"]["source"] == "local"
    lab["nuit_asie:gold"] = {"strategy": "nuit_asie", "asset": "gold", "trades": [
        {"status": "open", "notified_entry": "2026-10-14T22:10:00Z", "direction": "long", "entry": 4200.0,
         "risk": 42.0, "entry_ts": t22 + 300, "close_at": t22 + 9 * 3600}]}
    c.last = 0
    c.step()
    assert len(mt5.sent) == 1 and c.state[f"lab:nuit_asie:{t22 + 300}"]["status"].startswith("même signal")


def test_local_engine_falls_back_to_github_when_mt5_has_no_bars(tmp_path):
    from datetime import datetime, timezone
    now = datetime(2026, 10, 14, 22, 6, tzinfo=timezone.utc).timestamp()
    mt5 = LocalMT5(now)
    mt5.copy_rates_from_pos = lambda *a: None
    t22 = int(datetime(2026, 10, 14, 22, 0, tzinfo=timezone.utc).timestamp())
    lab = {"nuit_asie:gold": {"strategy": "nuit_asie", "asset": "gold", "trades": [
        {"status": "open", "notified_entry": "2026-10-14T22:05:00Z", "direction": "long", "entry": 4200.0,
         "risk": 42.0, "entry_ts": t22, "close_at": t22 + 9 * 3600}]}}
    get = lambda url: lab if "lab_shadow" in url else {"open_signals": []}
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: now, get=get, local=True)
    c.step()
    assert len(mt5.sent) == 1 and c.state[f"lab:nuit_asie:{t22}"]["source"] == "github"


def test_restart_does_not_close_a_github_copy_that_the_pc_also_sees(tmp_path):
    """16/10 : au redémarrage du pont, la copie de la zone de bruit v2 (vue par GitHub et par le PC) a été fermée."""
    from datetime import datetime, timezone
    now = datetime(2026, 10, 14, 22, 6, tzinfo=timezone.utc).timestamp()
    t22 = int(datetime(2026, 10, 14, 22, 0, tzinfo=timezone.utc).timestamp())
    mt5 = LocalMT5(now)
    mt5.pos.append(NS(ticket=777, magic=mc.MAGIC, symbol="XAUUSD+", type=0, volume=0.05))
    (tmp_path / "journal").mkdir()
    (tmp_path / "journal" / "copies.json").write_text(
        '{"lab:nuit_asie:%d": {"asset": "gold", "status": "ouvert", "ticket": 777, "expires": %d}}' % (t22, t22 + 9 * 3600))
    lab = {"nuit_asie:gold": {"strategy": "nuit_asie", "asset": "gold", "trades": [
        {"status": "open", "notified_entry": "2026-10-14T22:05:00Z", "direction": "long", "entry": 4200.0,
         "risk": 42.0, "entry_ts": t22, "close_at": t22 + 9 * 3600}]}}
    get = lambda url: lab if "lab_shadow" in url else {"open_signals": []}
    mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: now, get=get, local=True).step()
    assert mt5.sent == []                                            # ni fermée, ni rouverte


def test_late_github_copy_is_skipped_when_the_price_already_ran(tmp_path):
    created = mc._ts("2026-10-14T13:50:00Z")
    mt5 = FakeMT5()
    mt5.TIMEFRAME_M1 = 1
    mt5.copy_rates_from = lambda sym, tf, t, n: [{"close": 4215.0}]   # 15 $ plus haut à l'annonce (vente)
    c = mc.Copier(mt5, tmp_path, lambda *a, **k: None, lambda: created + 300, get=site([sig()]))
    c.step()
    assert mt5.sent == [] and c.state["bot:abc"]["status"].startswith("prix déjà parti")


def test_solo_trade_is_taken_at_two_hundredths_when_the_cap_allows_it():
    info = NS(trade_contract_size=1.0, volume_step=0.01, volume_min=0.01, volume_max=100.0)
    assert mc.solo_floor(0.01, 1000, 100.0, info) == 0.02          # 0,02 lot risque 2 % : ok
    assert mc.solo_floor(0.01, 100, 800.0, info) == 0.01           # 0,02 lot risquerait plus de 15 % du solde : on garde 0,01
    assert mc.solo_floor(0.05, 1000, 100.0, info) == 0.05 and mc.solo_floor(0.0, 1000, 100.0, info) == 0.0
    gold = NS(trade_contract_size=100.0, volume_step=0.01, volume_min=0.01, volume_max=100.0)
    assert mc.solo_floor(0.01, 190, 40.0, gold) == 0.01            # or à 190 $ : 0,02 lot = 80 $ (42 %) > 15 %
