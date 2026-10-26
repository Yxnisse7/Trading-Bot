from trading_bot import taille


def test_factor_bounds_and_direction():
    calm = [(101.0, 99.0, 100.0)] * 250            # 2 % d'amplitude
    wild = [(103.0, 97.0, 100.0)] * 14             # 6 % : trois fois plus agité
    assert taille.factor(calm[:100]) is None
    assert taille.factor(calm + wild) == 2.0        # borné à 2
    assert abs(taille.factor(calm + [(101.0, 99.0, 100.0)] * 14) - 1.0) < 1e-9
    k = taille.factor(calm + [(100.5, 99.5, 100.0)] * 14)
    assert k == 0.5
    assert "agité" in taille.line(2.0) and "10 %" in taille.line(2.0)
    assert taille.line(None) is None
