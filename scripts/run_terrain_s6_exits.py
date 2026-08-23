"""D199 — the exit policy: a shorter clock, and a stop that follows the trade.

    uv run python scripts/run_terrain_s6_exits.py
    uv run python scripts/run_terrain_s6_exits.py --report-only

Two primaries, each isolating ONE change from D197's baseline (ALL / fixed / 60):
  A — the clock: ALL / fixed / MAX_HOLD 20
  B — the trail: ALL / chandelier / MAX_HOLD 60

Each must beat that baseline by >= +0.10 Sharpe, beat its matched local-band null by the
same, and beat buy-and-hold, on BOTH symbols.
"""

from __future__ import annotations

import argparse
import functools
import json
import statistics
import sys
import time
from collections import Counter
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
    split_by_confirmation,
)
from backtest_framework.research.terrain_field_nulls import (  # noqa: E402
    ShuffleBand,
    compare_field_to_null,
)
from backtest_framework.research.terrain_strategies import (  # noqa: E402
    StrategyResult,
    buy_and_hold,
    run_field_reversal,
    run_field_trailing,
)

FIXTURE = "data/fixtures/crypto_daily_2015_2025_raw.csv.gz"
OUT = Path("data/terrain_s6_exits_summary.json")
SYMBOLS = ("BTC-USD", "ETH-USD")
N_SIMS, SEED, COST_BPS, PPY = 500, 0, 40.0, 365.0
PARAMS = FieldParams(k=2, cluster_atr=0.5)
HOLDS = (5, 20, 60)          # HORIZON, CONFIRM_WINDOW, MAX_HOLD — all existing constants
EFFECT_FLOOR = 0.10
BASELINE = ("all", "fixed", 60)
PRIMARY_A = ("all", "fixed", 20)
PRIMARY_B = ("all", "trail", 60)


def leg(result: StrategyResult, direction: int, bars) -> dict:
    only = StrategyResult(
        tuple(t for t in result.trades if t.direction == direction), COST_BPS, PPY
    )
    return {
        "n_trades": only.n_trades,
        "sharpe": only.curve_sharpe(bars, PPY) if only.n_trades >= 3 else 0.0,
        "total_return": only.curve_total_return(bars) if only.n_trades else 0.0,
        "hit_rate": only.hit_rate,
    }


def book(result: StrategyResult, bars) -> dict:
    holds = [t.exit_index - t.entry_index for t in result.trades]
    reasons = Counter(t.reason for t in result.trades)
    assert sum(reasons.values()) == result.n_trades, "exit reasons lost a trade"
    return {
        "n_trades": result.n_trades,
        "sharpe": result.curve_sharpe(bars, PPY),
        "total_return": result.curve_total_return(bars),
        "max_drawdown": result.max_drawdown(bars),
        "hit_rate": result.hit_rate,
        "median_bars_held": statistics.median(holds) if holds else 0,
        "exit_reasons": dict(reasons),
        "long": leg(result, 1, bars),
        "short": leg(result, -1, bars),
    }


def by_year(bars, result: StrategyResult) -> dict:
    out: dict[str, dict] = {}
    for t in result.trades:
        y = str(bars[t.entry_index].timestamp.year)
        r = out.setdefault(y, {"n": 0, "sum_net": 0.0})
        r["n"] += 1
        r["sum_net"] += t.gross_return - 2.0 * COST_BPS / 1e4
    return dict(sorted(out.items()))


def _run(bars, grid, atr, entry, exit_policy, hold, swings):
    """The closure both arms go through. Only the swings differ between real and null."""
    sigs = field_signals(bars, swings, PARAMS, grid)
    if entry == "confirmed":
        sigs = list(split_by_confirmation(bars, sigs, PARAMS).confirmed)
        filtered = False  # qualification already happened inside the split
    else:
        filtered = True
    fn = run_field_reversal if exit_policy == "fixed" else run_field_trailing
    return fn(bars, sigs, atr, COST_BPS, PPY, filtered=filtered, max_hold=hold)


def run_symbol(symbol, bars, vols, n_sims):
    atr = rolling_mean_true_range(bars, ATR_WINDOW)
    grid = build_grid(bars)
    swings = confirmed_swings(bars, vols, PARAMS)
    sigs = field_signals(bars, swings, PARAMS, grid)
    bh = buy_and_hold(bars, sigs[0].index if sigs else 0, PPY)

    # ALL over the full exit x hold grid; CONFIRMED only at the two primaries, which is
    # what keeps this at 8 cells a symbol rather than 12.
    combos = [("all", e, h) for e in ("fixed", "trail") for h in HOLDS]
    combos += [("confirmed", PRIMARY_A[1], PRIMARY_A[2]),
               ("confirmed", PRIMARY_B[1], PRIMARY_B[2])]
    assert BASELINE in combos and PRIMARY_A in combos and PRIMARY_B in combos

    cells = {}
    for (entry, exit_policy, hold) in combos:
        run = functools.partial(_run, bars, grid, atr, entry, exit_policy, hold)
        real = run(swings)
        cmp = compare_field_to_null(
            bars, swings, PARAMS, run, ShuffleBand.LOCAL, n_sims, SEED, PPY
        )
        key = f"{symbol}|{entry}|{exit_policy}|h{hold}"
        cells[key] = {
            "symbol": symbol, "entry": entry, "exit": exit_policy, "max_hold": hold,
            **book(real, bars),
            "by_year": by_year(bars, real),
            "bh_sharpe": bh["sharpe"],
            "null": cmp.to_dict(bars, PPY),
        }
        print(f"  {entry:<9} {exit_policy:<5} h={hold:<2} n={cells[key]['n_trades']:>4} "
              f"S {cells[key]['sharpe']:+.3f}  med_hold "
              f"{cells[key]['median_bars_held']:>2}  "
              f"nullD {cells[key]['null']['sharpe_delta']:+.3f} "
              f"pct {cells[key]['null']['sharpe_percentile']:>5.1f}  "
              f"exits {cells[key]['exit_reasons']}", flush=True)
    return cells, bh


def render(payload) -> None:
    cells = payload["cells"]
    base = {s: cells[f"{s}|all|fixed|h60"]["sharpe"] for s in SYMBOLS}
    print(f"\n{'cell':<30} {'n':>5} {'Sharpe':>8} {'vsBase':>8} {'nullD':>8} "
          f"{'pct':>6} {'held':>5} {'BH':>8}  verdict")
    for key, c in cells.items():
        vb = c["sharpe"] - base[c["symbol"]]
        v = []
        if vb >= payload["effect_floor"]: v.append("BASE")
        if c["null"]["sharpe_delta"] >= payload["effect_floor"]: v.append("NULL")
        if c["sharpe"] > c["bh_sharpe"]: v.append("BH")
        print(f"{key:<30} {c['n_trades']:>5} {c['sharpe']:>+8.3f} {vb:>+8.3f} "
              f"{c['null']['sharpe_delta']:>+8.3f} "
              f"{c['null']['sharpe_percentile']:>6.1f} {c['median_bars_held']:>5} "
              f"{c['bh_sharpe']:>+8.3f}  {'+'.join(v) if v else 'fail'}")
    print("\nPrimary A (clock) and B (trail) each need BASE + NULL + BH on both symbols.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--sims", type=int, default=N_SIMS)
    args = ap.parse_args()

    if args.report_only:
        render(json.loads(OUT.read_text()))
        return

    raw, rawv = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)
    vols = {s: bu.align_volumes(cleaned[s], raw[s], rawv[s]) for s in cleaned}

    started = time.time()
    cells, bhs = {}, {}
    for symbol in SYMBOLS:
        print(f"\n=== {symbol} ===", flush=True)
        c, bh = run_symbol(symbol, cleaned[symbol], vols[symbol], args.sims)
        cells.update(c)
        bhs[symbol] = bh

    payload = {
        "n_sims": args.sims, "seed": SEED, "cost_bps": COST_BPS,
        "holds": list(HOLDS), "effect_floor": EFFECT_FLOOR,
        "params": {"k": PARAMS.k, "cluster_atr": PARAMS.cluster_atr},
        "baseline": list(BASELINE), "primary_a": list(PRIMARY_A),
        "primary_b": list(PRIMARY_B),
        "buy_and_hold": bhs, "cells": cells,
        "elapsed_seconds": time.time() - started,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    render(payload)
    print(f"\nwrote {OUT} in {payload['elapsed_seconds']:.0f}s")


if __name__ == "__main__":
    main()
