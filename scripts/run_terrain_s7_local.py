"""D202 — the local imbalance, sized on its magnitude, against a timing null.

    uv run python scripts/run_terrain_s7_local.py --benchmark
    uv run python scripts/run_terrain_s7_local.py
    uv run python scripts/run_terrain_s7_local.py --report-only

Primary is the local statistic, continuous sizing, 40 bps. Three hurdles, all required on
both symbols: beat the ROTATION null (timing) by >= +0.10 Sharpe, beat the MASS-SHUFFLE
null (placement) by the same, and beat buy-and-hold.

The zero-cost arm is a DIAGNOSTIC and never a strategy. It exists to separate "no
information" from "information this cost structure cannot support".
"""

from __future__ import annotations

import argparse
import functools
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

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
    local_imbalance,
)
from backtest_framework.research.terrain_field_nulls import (  # noqa: E402
    ShuffleBand,
    compare_field_to_null,
    rotation_null,
)
from backtest_framework.research.terrain_strategies import (  # noqa: E402
    buy_and_hold,
    run_field_position,
)

FIXTURE = "data/fixtures/crypto_daily_2015_2025_raw.csv.gz"
OUT = Path("data/terrain_s7_local_summary.json")
SYMBOLS = ("BTC-USD", "ETH-USD")
N_SIMS, SEED, COST_BPS, PPY = 500, 0, 40.0, 365.0
PARAMS = FieldParams(k=2, cluster_atr=0.5, erase=False)  # raw field, D202
SMOOTH = 5  # terrain_nulls.HORIZON, itself breakout_study.E2_N
EFFECT_FLOOR = 0.10
PRIMARY = "local|continuous|40bps"

CONFIGS = (
    ("local|continuous|40bps", "local", True, COST_BPS, 1),
    ("local|continuous|0bps_DIAGNOSTIC", "local", True, 0.0, 1),
    ("local|smoothed|40bps", "local", True, COST_BPS, SMOOTH),
    ("local|binary|40bps", "local", False, COST_BPS, 1),
    ("global|continuous|40bps", "global", True, COST_BPS, 1),
)


def smooth(series, window: int):
    if window <= 1:
        return list(series)
    out = []
    for i in range(len(series)):
        a = max(0, i - window + 1)
        out.append(statistics.fmean(series[a : i + 1]))
    return out


def book(result, bars) -> dict:
    n = len(result.position)
    years = n / PPY
    return {
        "sharpe": result.curve_sharpe(bars, PPY),
        "total_return": result.curve_total_return(),
        "max_drawdown": result.max_drawdown(),
        "hit_rate": result.hit_rate,
        "turnover": result.turnover,
        "turnover_per_year": result.turnover / years,
        "realised_cost_drag_per_year": result.turnover * (result.cost_bps / 1e4) / years,
        "sign_changes": result.sign_changes,
        "net_exposure": result.net_exposure,
        "share_long": sum(1 for p in result.position if p > 0) / n,
        "share_short": sum(1 for p in result.position if p < 0) / n,
        "share_flat": sum(1 for p in result.position if p == 0) / n,
        "long_leg_sharpe": result.leg(1).curve_sharpe(bars, PPY),
        "short_leg_sharpe": result.leg(-1).curve_sharpe(bars, PPY),
    }


def by_year(bars, result) -> dict:
    out: dict[str, float] = {}
    for i, p in enumerate(result.position):
        if p == 0.0:
            continue
        y = str(bars[i].timestamp.year)
        out[y] = out.get(y, 0.0) + p * result.returns[i]
    return dict(sorted(out.items()))


def _run(bars, grid, atr, stat, continuous, cost, window, swings):
    if stat == "local":
        sig = local_imbalance(bars, swings, PARAMS, grid)
    else:
        sig = [0.0 if x != x else x for x in field_imbalance(bars, swings, PARAMS, grid)]
    return run_field_position(
        bars, smooth(sig, window), atr, cost, PPY, continuous=continuous
    )


def run_symbol(symbol, bars, vols, n_sims, only_primary=False):
    atr = rolling_mean_true_range(bars, ATR_WINDOW)
    grid = build_grid(bars)
    swings = confirmed_swings(bars, vols, PARAMS)
    bh = buy_and_hold(bars, 0, PPY)
    cells = {}

    for (name, stat, continuous, cost, window) in CONFIGS:
        if only_primary and name != PRIMARY:
            continue
        run = functools.partial(_run, bars, grid, atr, stat, continuous, cost, window)
        real = run(swings)

        mass = compare_field_to_null(
            bars, swings, PARAMS, run, ShuffleBand.LOCAL, n_sims, SEED, PPY
        )
        rot = rotation_null(real, n_sims, np.random.default_rng(SEED))
        rot_sharpes = [r.curve_sharpe(bars, PPY) for r in rot]
        rot_mean = statistics.fmean(rot_sharpes)
        real_sharpe = real.curve_sharpe(bars, PPY)

        key = f"{symbol}|{name}"
        cells[key] = {
            "symbol": symbol, "config": name,
            **book(real, bars),
            "by_year": by_year(bars, real),
            "bh_sharpe": bh["sharpe"],
            "mass_null": mass.to_dict(bars, PPY),
            "rotation_null": {
                "mean": rot_mean,
                "p05": float(np.percentile(rot_sharpes, 5)),
                "p95": float(np.percentile(rot_sharpes, 95)),
                "sharpe_delta": real_sharpe - rot_mean,
                "percentile": 100.0
                * sum(1 for x in rot_sharpes if x < real_sharpe)
                / len(rot_sharpes),
                "n_sims": len(rot_sharpes),
            },
        }
        c = cells[key]
        c["beats_rotation"] = c["rotation_null"]["sharpe_delta"] >= EFFECT_FLOOR
        c["beats_mass"] = c["mass_null"]["sharpe_delta"] >= EFFECT_FLOOR
        c["beats_bh"] = c["sharpe"] > c["bh_sharpe"]
        c["clears_all"] = c["beats_rotation"] and c["beats_mass"] and c["beats_bh"]
        print(f"  {name:<34} S {c['sharpe']:+.3f}  BH {c['bh_sharpe']:+.3f}  "
              f"rotD {c['rotation_null']['sharpe_delta']:+.3f} "
              f"({c['rotation_null']['percentile']:>5.1f})  "
              f"massD {c['mass_null']['sharpe_delta']:+.3f}  "
              f"net {c['net_exposure']:+.2f}  drag "
              f"{100*c['realised_cost_drag_per_year']:.1f}%/yr", flush=True)
    return cells


def render(payload) -> None:
    cells = payload["cells"]
    print(f"\n{'cell':<46} {'Sharpe':>8} {'BH':>8} {'rotD':>8} {'massD':>8} "
          f"{'net':>6} {'drag':>7}  verdict")
    for key, c in cells.items():
        v = []
        if c["beats_rotation"]: v.append("ROT")
        if c["beats_mass"]: v.append("MASS")
        if c["beats_bh"]: v.append("BH")
        print(f"{key:<46} {c['sharpe']:>+8.3f} {c['bh_sharpe']:>+8.3f} "
              f"{c['rotation_null']['sharpe_delta']:>+8.3f} "
              f"{c['mass_null']['sharpe_delta']:>+8.3f} {c['net_exposure']:>+6.2f} "
              f"{100*c['realised_cost_drag_per_year']:>6.1f}%"
              f"  {'+'.join(v) if v else 'fail'}")
    n = sum(1 for k, c in cells.items()
            if c["clears_all"] and "DIAGNOSTIC" not in k)
    print(f"\n{len(cells)} cells; {n} tradeable cells clear all three hurdles")
    print("The 0bps arm is a DIAGNOSTIC and is never a strategy.")


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
        print(f"\nbenchmark: {el:.1f}s for 1 cell x 20 sims -> {el/20*1000:.0f} ms a draw")
        print(f"  projected grid (10 cells x {N_SIMS}): {el/20*N_SIMS*10/60:.1f} min")
        return

    started = time.time()
    cells = {}
    for symbol in SYMBOLS:
        print(f"\n=== {symbol} ===", flush=True)
        cells.update(run_symbol(symbol, cleaned[symbol], vols[symbol], args.sims))

    payload = {
        "n_sims": args.sims, "seed": SEED, "cost_bps": COST_BPS,
        "smooth_window": SMOOTH, "effect_floor": EFFECT_FLOOR, "primary": PRIMARY,
        "cells": cells, "elapsed_seconds": time.time() - started,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    render(payload)
    print(f"\nwrote {OUT} in {payload['elapsed_seconds']:.0f}s")


if __name__ == "__main__":
    main()
