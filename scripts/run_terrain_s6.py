"""D197 — S6, the signed inventory field, against its control and its two nulls.

    uv run python scripts/run_terrain_s6.py --benchmark   # one cell, project the grid
    uv run python scripts/run_terrain_s6.py               # the full grid
    uv run python scripts/run_terrain_s6.py --report-only # re-render from the JSON

Three hurdles, all required on the primary configuration and on BOTH symbols (D197):
beat the erasure-only control by >= +0.10 Sharpe, beat the matched null by the same, and
beat buy-and-hold. The control is the primary comparison: the erasure is a deterministic
function of price and every null draw carries it identically, so no null can detect a
confound living in it.
"""

from __future__ import annotations

import argparse
import functools
import json
import statistics
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
    field_signals,
)
from backtest_framework.research.terrain_field_nulls import (  # noqa: E402
    ShuffleBand,
    compare_field_to_null,
)
from backtest_framework.research.terrain_strategies import (  # noqa: E402
    BENCHMARK_RF_ANNUAL as RF_ANNUAL,
    FIELD_TARGET_R,
    MAX_HOLD,
    STOP_ATR,
    StrategyResult,
    buy_and_hold,
    run_field_reversal,
)

FIXTURE = "data/fixtures/crypto_daily_2015_2025_raw.csv.gz"
OUT = Path("data/terrain_s6_summary.json")
SYMBOLS = ("BTC-USD", "ETH-USD")
N_SIMS, SEED, COST_BPS, PPY = 500, 0, 40.0, 365.0
THRESHOLDS = (0.0, 0.1)
K_SET = (2, 3)
CLUSTER_SET = (0.5, 0.25)
PRIMARY = {"k": 2, "cluster_atr": 0.5, "threshold": 0.0}
EFFECT_FLOOR = 0.10


def load():
    raw, rawv = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)
    vols = {s: bu.align_volumes(cleaned[s], raw[s], rawv[s]) for s in cleaned}
    return cleaned, vols


def leg(result: StrategyResult, direction: int, bars, cost_bps: float) -> dict:
    """One side of the book on its own. D197 requires the legs reported separately: the
    census measured a 321/171 short bias driven by where information exists, not by the
    market, and a pooled number would hide it."""
    only = StrategyResult(
        tuple(t for t in result.trades if t.direction == direction), cost_bps, PPY
    )
    return {
        "n_trades": only.n_trades,
        "sharpe": only.curve_sharpe_zero_rf(bars, PPY) if only.n_trades >= 3 else 0.0,
        "excess_sharpe": only.curve_excess_sharpe(bars, PPY, RF_ANNUAL) if only.n_trades >= 3 else 0.0,
        "rf_annual": RF_ANNUAL,
        "total_return": only.curve_total_return(bars) if only.n_trades else 0.0,
        "hit_rate": only.hit_rate,
    }


def four_cells(signals) -> dict:
    """Every fire by shape. Two of the four are continuation and are never traded."""
    out = {
        "up_into_supply_SHORT": 0, "down_into_demand_LONG": 0,
        "up_into_demand_untraded": 0, "down_into_supply_untraded": 0,
        "virgin": 0,
    }
    for s in signals:
        if s.virgin:
            out["virgin"] += 1
        elif s.direction > 0:
            out["up_into_supply_SHORT" if s.tilt < 0 else "up_into_demand_untraded"] += 1
        else:
            out["down_into_demand_LONG" if s.tilt > 0 else "down_into_supply_untraded"] += 1
    return out


def decile_response(bars, signals, horizon: int = MAX_HOLD) -> list[dict]:
    """Fade-direction return over `horizon` bars, by tilt decile. A DIAGNOSTIC, not a
    verdict: a monotone response is evidence the magnitude carries information, a single
    hot bucket is not. D196's post-hoc rank slice was non-monotone and that is exactly
    what stopped it being called a finding."""
    rows = []
    for s in signals:
        if s.virgin:
            continue
        j = min(s.index + horizon, len(bars) - 1)
        if j <= s.index:
            continue
        fwd = bars[j].bar.close / bars[s.index].bar.close - 1.0
        rows.append((s.tilt, -s.direction * fwd))  # signed the way the fade would trade
    if len(rows) < 20:
        return []
    rows.sort(key=lambda r: r[0])
    n = len(rows)
    out = []
    for d in range(10):
        chunk = rows[d * n // 10 : (d + 1) * n // 10]
        if not chunk:
            continue
        out.append({
            "decile": d + 1,
            "n": len(chunk),
            "tilt_lo": chunk[0][0],
            "tilt_hi": chunk[-1][0],
            "mean_fade_return": statistics.fmean(r[1] for r in chunk),
        })
    return out


def run_symbol(symbol, bars, vols, n_sims, only_primary=False):
    atr = rolling_mean_true_range(bars, ATR_WINDOW)
    grid = build_grid(bars)
    cells = {}

    # The fire set depends on the ERASURE only, which is a function of the bars, so it is
    # identical across every sensor configuration. The control is therefore one run per
    # symbol, not one per cell.
    base = field_signals(bars, confirmed_swings(bars, vols, FieldParams(2, 0.5)),
                         FieldParams(2, 0.5), grid)
    start = base[0].index if base else 0
    bh = buy_and_hold(bars, start, PPY)
    control = run_field_reversal(bars, base, atr, COST_BPS, PPY, filtered=False)
    control_sharpe = control.curve_sharpe_zero_rf(bars, PPY)
    control_row = {
        "n_trades": control.n_trades,
        "sharpe": control_sharpe,
        "total_return": control.curve_total_return(bars),
        "max_drawdown": control.max_drawdown(bars),
        "hit_rate": control.hit_rate,
        "long": leg(control, 1, bars, COST_BPS),
        "short": leg(control, -1, bars, COST_BPS),
    }

    combos = [(PRIMARY["k"], PRIMARY["cluster_atr"], PRIMARY["threshold"])] if only_primary \
        else [(k, ca, x) for k in K_SET for ca in CLUSTER_SET for x in THRESHOLDS]

    for (k, ca, x) in combos:
        params = FieldParams(k=k, cluster_atr=ca)
        swings = confirmed_swings(bars, vols, params)
        run = functools.partial(_run_one, bars, params, grid, atr, x)
        real = run(swings)
        sigs = field_signals(bars, swings, params, grid)

        row = {
            "symbol": symbol, "k": k, "cluster_atr": ca, "threshold": x,
            "n_trades": real.n_trades,
            "sharpe": real.curve_sharpe_zero_rf(bars, PPY),
            "excess_sharpe": real.curve_excess_sharpe(bars, PPY, RF_ANNUAL),
            "rf_annual": RF_ANNUAL,
            "total_return": real.curve_total_return(bars),
            "max_drawdown": real.max_drawdown(bars),
            "hit_rate": real.hit_rate,
            "long": leg(real, 1, bars, COST_BPS),
            "short": leg(real, -1, bars, COST_BPS),
            "four_cells": four_cells(sigs),
            "n_fires": len(sigs),
            "control_sharpe": control_sharpe,
            "control_delta": real.curve_sharpe_zero_rf(bars, PPY) - control_sharpe,
            "bh_sharpe": bh["sharpe"],
            "bh_total_return": bh["total_return"],
            "decile_response": decile_response(bars, sigs),
            "nulls": {},
        }
        for band in (ShuffleBand.LOCAL, ShuffleBand.SPAN):
            cmp = compare_field_to_null(
                bars, swings, params, run, band, n_sims, SEED, PPY
            )
            row["nulls"][band.value] = cmp.to_dict(bars, PPY)

        verdict_null = row["nulls"][ShuffleBand.LOCAL.value]
        row["beats_control"] = row["control_delta"] >= EFFECT_FLOOR
        row["beats_null"] = verdict_null["sharpe_delta"] >= EFFECT_FLOOR
        row["beats_bh"] = row["sharpe"] > bh["sharpe"]
        row["clears_all_three"] = (
            row["beats_control"] and row["beats_null"] and row["beats_bh"]
        )
        cells[f"{symbol}|k{k}|ca{ca:g}|x{x:g}"] = row
        print(
            f"  k={k} ca={ca:g} x={x:g}  n={row['n_trades']:>4} "
            f"S {row['sharpe']:+.3f}  ctrl {control_sharpe:+.3f} (d {row['control_delta']:+.3f})  "
            f"null {verdict_null['null_sharpe_mean']:+.3f} (d {verdict_null['sharpe_delta']:+.3f}, "
            f"pct {verdict_null['sharpe_percentile']:>5.1f})  BH {bh['sharpe']:+.3f}  "
            f"{'CTRL' if row['beats_control'] else '.'} "
            f"{'NULL' if row['beats_null'] else '.'} "
            f"{'BH' if row['beats_bh'] else '.'}",
            flush=True,
        )
    return cells, control_row, bh


def _run_one(bars, params, grid, atr, threshold, swings):
    """The closure both arms go through — bars, params, costs and geometry all fixed, only
    the swings differ. The pairing is enforced by the signature."""
    sigs = field_signals(bars, swings, params, grid)
    return run_field_reversal(bars, sigs, atr, COST_BPS, PPY, threshold=threshold)


def render(payload) -> None:
    cells = payload["cells"]
    print(f"\n{'cell':<26} {'n':>5} {'Sharpe':>8} {'ctrlD':>8} {'nullD':>8} "
          f"{'pct':>6} {'BH':>8}  verdict")
    for key, c in cells.items():
        v = []
        if c["beats_control"]: v.append("CTRL")
        if c["beats_null"]: v.append("NULL")
        if c["beats_bh"]: v.append("BH")
        print(f"{key:<26} {c['n_trades']:>5} {c['sharpe']:>+8.3f} "
              f"{c['control_delta']:>+8.3f} {c['nulls']['local']['sharpe_delta']:>+8.3f} "
              f"{c['nulls']['local']['sharpe_percentile']:>6.1f} {c['bh_sharpe']:>+8.3f}"
              f"  {'+'.join(v) if v else 'fail'}")
    n_all = sum(1 for c in cells.values() if c["clears_all_three"])
    print(f"\n{len(cells)} cells; {n_all} clear all three hurdles")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", action="store_true",
                    help="one cell on BTC, then project the grid")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--sims", type=int, default=N_SIMS)
    args = ap.parse_args()

    if args.report_only:
        render(json.loads(OUT.read_text()))
        return

    cleaned, vols = load()

    if args.benchmark:
        sims = 25
        t0 = time.time()
        run_symbol("BTC-USD", cleaned["BTC-USD"], vols["BTC-USD"], sims,
                   only_primary=True)
        el = time.time() - t0
        per_null = el / (sims * 2)
        full = per_null * N_SIMS * 2 * 16 * 1.0
        print(f"\nbenchmark: {el:.1f}s for 1 cell x {sims} sims x 2 bands")
        print(f"  per null draw: {per_null*1000:.0f} ms")
        print(f"  projected grid (16 cells x 2 bands x {N_SIMS}): "
              f"{full/60:.1f} min ({full/3600:.2f} h)")
        return

    started = time.time()
    cells, controls, bhs = {}, {}, {}
    for symbol in SYMBOLS:
        print(f"\n=== {symbol} ===", flush=True)
        c, ctrl, bh = run_symbol(symbol, cleaned[symbol], vols[symbol], args.sims)
        cells.update(c)
        controls[symbol] = ctrl
        bhs[symbol] = bh

    payload = {
        "n_sims": args.sims, "seed": SEED, "cost_bps": COST_BPS,
        "stop_atr": STOP_ATR, "target_r": FIELD_TARGET_R, "max_hold": MAX_HOLD,
        "primary": PRIMARY, "effect_floor": EFFECT_FLOOR,
        "controls": controls, "buy_and_hold": bhs, "cells": cells,
        "elapsed_seconds": time.time() - started,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    render(payload)
    print(f"\nwrote {OUT} in {payload['elapsed_seconds']:.0f}s")


if __name__ == "__main__":
    main()
