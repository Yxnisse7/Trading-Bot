from datetime import datetime, timezone

from trading_bot import essai17 as e17
from trading_bot import strategies as sl
from trading_bot.config import load_config

from conftest import make_candles


def test_remap_reads_paris_minus_30_min_as_new_york_time():
    # 9:00 à Paris (7:00 UTC en été) devient 9:30 heure de New York
    ts = int(datetime(2026, 7, 1, 7, 0, tzinfo=timezone.utc).timestamp())
    c = make_candles(n=3, start_ts=ts)
    out = e17.remap(c)
    ny = datetime.fromtimestamp(out[0].ts, sl.NY)
    assert (ny.hour, ny.minute) == (9, 30) and len(out) == 3
    assert [x.close for x in out] == [x.close for x in c]


def test_cells_run_on_synthetic_data():
    e17.enable_european_sessions()
    cfg = load_config()
    a = e17.asset_config(cfg, "dax")
    assert a.key == "dax" and a.cost_pct == 0.01
    real = make_candles(n=6000, drift=0.0001, noise=0.0015, seed=4)
    rem = e17.remap(real)
    ctx = e17.e15.Ctx(rem)
    names = [n for n, _ in e17.cells("dax", real, rem, ctx, ctx, [], a.cost_pct)]
    assert len(names) == 54 and len(set(names)) == 54
