from trading_bot import pc_link


def raw(ts):
    return pc_link.encode(ts, [], [])


def test_alerte_une_seule_fois_puis_retour():
    t0 = 1_800_000_000
    assert pc_link.watch(raw(t0), t0 + 60, None) == (None, None)            # PC vivant
    assert pc_link.watch(raw(t0), t0 + 11 * 60, None) == (None, None)       # pas encore 15 min
    assert pc_link.watch(raw(t0), t0 + 16 * 60, None) == ("down", t0)       # alerte
    assert pc_link.watch(raw(t0), t0 + 3 * 3600, t0) == (None, t0)          # pas de répétition
    assert pc_link.watch(raw(t0 + 4 * 3600), t0 + 4 * 3600 + 30, t0) == ("up", None)


def test_variable_absente_ou_tres_vieille():
    assert pc_link.watch(None, 1_800_000_000, None) == (None, None)
    assert pc_link.watch(raw(1_800_000_000), 1_800_000_000 + 5 * 86400, None) == (None, None)
