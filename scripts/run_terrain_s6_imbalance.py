"""D201 — the imbalance formulation, with and without stops, erased and raw fields.

    uv run python scripts/run_terrain_s6_imbalance.py --benchmark
    uv run python scripts/run_terrain_s6_imbalance.py
    uv run python scripts/run_terrain_s6_imbalance.py --report-only

Primary is the ERASED field with NO stop. Both hurdles required on both symbols: beat
buy-and-hold, and beat the matched local-band null by >= +0.10 Sharpe. The raw field is a
pre-registered variant, NOT a second attempt at the bar.
"""

from __future__ import annotations

import argparse
import functools
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.research import breakout_universe as bu  # noqa: E402
from backtest_framework.research.terrain import (  # noqa: E402
    ATR_WINDOW,
    rolling_mean_true_range,
)
from backtest_framework.research.terrain_field import (  # noqa: E402
    FieldParams,
    build_grid,
    confirmed_swings,
    field_imbalance,
)
from backtest_framework.research.terrain_field_nulls import (  # noqa: E402
    ShuffleBand,
    compare_field_to_null,
)
from backtest_framework.research.terrain_strategies import (  # noqa: E402
    BENCHMARK_RF_ANNUAL as RF_ANNUAL,
    STOP_ATR,
    buy_and_hold,
    run_field_imbalance,
)

FIXTURE = "data/fixtures/crypto_daily_2015_2025_raw.csv.gz"
OUT = Path("data/terrain_s6_imbalance_summary.json")
SYMBOLS = ("BTC-USD", "ETH-USD")
N_SIMS, SEED, COST_BPS, PPY = 500, 0, 40.0, 365.0
FIELDS = (("erased", True), ("raw", False))
STOPS = (("nostop", False), ("stop", True))
EFFECT_FLOOR = 0.10
PRIMARY = ("erased", "nostop")


def flips(result) -> list[dict]:
    """Every sign change and what it earned. With nine of them on BTC the per-decision
    detail IS the result, so it is reported rather than summarised away (D201)."""
    out, pos = [], result.position
    start, cur = 0, pos[0]
    for i in range(1, len(pos)):
        if pos[i] != cur:
            if cur != 0:
                out.append({
                    "from": start, "to": i, "direction": cur, "bars": i - start,
                    "sum_log_return": sum(cur * result.returns[j] for j in range(start, i)),
                })
            start, cur = i, pos[i]
    if cur != 0:
        out.append({
            "from": start, "to": len(pos), "direction": cur, "bars": len(pos) - start,
            "sum_log_return": sum(cur * result.returns[j] for j in range(start, len(pos))),
        })
    return out


def book(result, bars) -> dict:
    n = len(result.position)
    return {
        "n_position_changes": result.n_trades,
        "turnover": result.turnover,
        "sharpe": result.curve_sharpe_zero_rf(bars, PPY),
        "excess_sharpe": result.curve_excess_sharpe(bars, PPY, RF_ANNUAL),
        "rf_annual": RF_ANNUAL,
        "total_return": result.curve_total_return(),
        "max_drawdown": result.max_drawdown(),
        "hit_rate": result.hit_rate,
        "share_long": sum(1 for p in result.position if p > 0) / n,
        "share_short": sum(1 for p in result.position if p < 0) / n,
        "share_flat": sum(1 for p in result.position if p == 0) / n,
        "long_leg_sharpe": result.leg(1).curve_sharpe_zero_rf(bars, PPY),
        "short_leg_sharpe": result.leg(-1).curve_sharpe_zero_rf(bars, PPY),
        "long_leg_return": result.leg(1).curve_total_return(),
        "short_leg_return": result.leg(-1).curve_total_return(),
    }


def by_year(bars, result) -> dict:
    out: dict[str, float] = {}
    for i, p in enumerate(result.position):
        if p == 0:
            continue
        y = str(bars[i].timestamp.year)
        out[y] = out.get(y, 0.0) + p * result.returns[i]
    return dict(sorted(out.items()))


def _run(bars, grid, atr, params, use_stop, swings):
    imb = field_imbalance(bars, swings, params, grid)
    return run_field_imbalance(
        bars, imb, atr, COST_BPS, PPY, threshold=0.0, use_stop=use_stop
    )


def run_symbol(symbol, bars, vols, n_sims, only_primary=False):
    atr = rolling_mean_true_range(bars, ATR_WINDOW)
    grid = build_grid(bars)
    bh = buy_and_hold(bars, 0, PPY)
    cells = {}

    combos = [PRIMARY] if only_primary else [
        (f, s) for (f, _) in FIELDS for (s, _) in STOPS
    ]
    for (fname, sname) in combos:
        erase = dict(FIELDS)[fname]
        use_stop = dict(STOPS)[sname]
        params = FieldParams(k=2, cluster_atr=0.5, erase=erase)
        swings = confirmed_swings(bars, vols, params)
        run = functools.partial(_run, bars, grid, atr, params, use_stop)
        real = run(swings)
        cmp = compare_field_to_null(
            bars, swings, params, run, ShuffleBand.LOCAL, n_sims, SEED, PPY
        )
        key = f"{symbol}|{fname}|{sname}"
        cells[key] = {
            "symbol": symbol, "field": fname, "stop": sname,
            **book(real, bars),
            "by_year": by_year(bars, real),
            "flips": flips(real),
            "bh_sharpe": bh["sharpe"], "bh_total_return": bh["total_return"],
            "null": cmp.to_dict(bars, PPY),
        }
        c = cells[key]
        c["beats_bh"] = c["sharpe"] > c["bh_sharpe"]
        c["beats_null"] = c["null"]["sharpe_delta"] >= EFFECT_FLOOR
        c["clears_both"] = c["beats_bh"] and c["beats_null"]
        print(f"  {fname:<6} {sname:<6} S {c['sharpe']:+.3f}  BH {c['bh_sharpe']:+.3f}  "
              f"nullD {c['null']['sharpe_delta']:+.3f} pct "
              f"{c['null']['sharpe_percentile']:>5.1f}  "
              f"long {100*c['share_long']:.0f}% flat {100*c['share_flat']:.0f}%  "
              f"changes {c['n_position_changes']}  flips {len(c['flips'])}", flush=True)
    return cells


def render(payload) -> None:
    cells = payload["cells"]
    print(f"\n{'cell':<26} {'Sharpe':>8} {'BH':>8} {'nullD':>8} {'pct':>6} "
          f"{'long%':>6} {'flat%':>6} {'chg':>4}  verdict")
    for key, c in cells.items():
        v = []
        if c["beats_bh"]: v.append("BH")
        if c["beats_null"]: v.append("NULL")
        print(f"{key:<26} {c['sharpe']:>+8.3f} {c['bh_sharpe']:>+8.3f} "
              f"{c['null']['sharpe_delta']:>+8.3f} "
              f"{c['null']['sharpe_percentile']:>6.1f} {100*c['share_long']:>6.1f} "
              f"{100*c['share_flat']:>6.1f} {c['n_position_changes']:>4}"
              f"  {'+'.join(v) if v else 'fail'}")
    n = sum(1 for c in cells.values() if c["clears_both"])
    print(f"\n{len(cells)} cells; {n} clear both hurdles")
    print("Primary is erased|nostop on BOTH symbols. Raw is a variant, not a second shot.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--sims", type=int, default=N_SIMS)
    args = ap.parse_args()

    if args.report_only:
        render(json.loads(OUT.read_text()))
        return

    raw, rawv = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)
    vols = {s: bu.align_volumes(cleaned[s], raw[s], rawv[s]) for s in cleaned}

    if args.benchmark:
        t0 = time.time()
        run_symbol("BTC-USD", cleaned["BTC-USD"], vols["BTC-USD"], 20, only_primary=True)
        el = time.time() - t0
        per = el / 20
        print(f"\nbenchmark: {el:.1f}s for 1 cell x 20 sims -> {per*1000:.0f} ms a draw")
        print(f"  projected grid (8 cells x {N_SIMS}): {per*N_SIMS*8/60:.1f} min")
        return

    started = time.time()
    cells = {}
    for symbol in SYMBOLS:
        print(f"\n=== {symbol} ===", flush=True)
        cells.update(run_symbol(symbol, cleaned[symbol], vols[symbol], args.sims))

    payload = {
        "n_sims": args.sims, "seed": SEED, "cost_bps": COST_BPS,
        "stop_atr": STOP_ATR, "effect_floor": EFFECT_FLOOR,
        "primary": list(PRIMARY), "cells": cells,
        "elapsed_seconds": time.time() - started,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    render(payload)
    print(f"\nwrote {OUT} in {payload['elapsed_seconds']:.0f}s")


if __name__ == "__main__":
    main()
