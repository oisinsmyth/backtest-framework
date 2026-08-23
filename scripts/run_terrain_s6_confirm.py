"""D198 — does waiting for a second distinct approach help, or discard the winners?

    uv run python scripts/run_terrain_s6_confirm.py
    uv run python scripts/run_terrain_s6_confirm.py --report-only

Three hurdles, all required on both symbols: CONFIRMED beats ALL SIGNALS by >= +0.10
Sharpe, beats its matched local-band null by the same, and beats buy-and-hold.

The UNCONFIRMED book is hindsight-classified — a signal is only known to be unconfirmed
once the window has expired — so it is a DIAGNOSTIC and is labelled as one everywhere it
is printed. It is not a strategy and no hurdle is applied to it.
"""

from __future__ import annotations

import argparse
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
    CONFIRM_WINDOW,
    FieldParams,
    build_grid,
    confirmed_swings,
    field_signals,
    qualifying,
    split_by_confirmation,
)
from backtest_framework.research.terrain_field_nulls import (  # noqa: E402
    ShuffleBand,
    compare_field_to_null,
)
from backtest_framework.research.terrain_strategies import (  # noqa: E402
    FIELD_TARGET_R,
    MAX_HOLD,
    STOP_ATR,
    StrategyResult,
    buy_and_hold,
    run_field_reversal,
)

FIXTURE = "data/fixtures/crypto_daily_2015_2025_raw.csv.gz"
OUT = Path("data/terrain_s6_confirm_summary.json")
SYMBOLS = ("BTC-USD", "ETH-USD")
N_SIMS, SEED, COST_BPS, PPY = 500, 0, 40.0, 365.0
PARAMS = FieldParams(k=2, cluster_atr=0.5)  # D197's primary; NOT re-swept
EFFECT_FLOOR = 0.10


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
    return {
        "n_trades": result.n_trades,
        "sharpe": result.curve_sharpe(bars, PPY),
        "total_return": result.curve_total_return(bars),
        "max_drawdown": result.max_drawdown(bars),
        "hit_rate": result.hit_rate,
        "long": leg(result, 1, bars),
        "short": leg(result, -1, bars),
    }


def by_year(bars, result: StrategyResult) -> dict:
    """Mandatory reporting: a rule that waits for price to come home fires more in
    ranging markets, and this fixture contains one long bear market where fading works
    for reasons that have nothing to do with supply and demand."""
    out: dict[str, dict] = {}
    for t in result.trades:
        y = str(bars[t.entry_index].timestamp.year)
        r = out.setdefault(y, {"n": 0, "sum_net": 0.0})
        r["n"] += 1
        r["sum_net"] += t.gross_return - 2.0 * COST_BPS / 1e4
    return dict(sorted(out.items()))


def run_symbol(symbol, bars, vols, n_sims):
    atr = rolling_mean_true_range(bars, ATR_WINDOW)
    grid = build_grid(bars)
    swings = confirmed_swings(bars, vols, PARAMS)
    sigs = field_signals(bars, swings, PARAMS, grid)
    split = split_by_confirmation(bars, sigs, PARAMS)
    assert split.accounts(), "confirmation bookkeeping lost a signal"

    start = sigs[0].index if sigs else 0
    bh = buy_and_hold(bars, start, PPY)

    all_signals = run_field_reversal(bars, sigs, atr, COST_BPS, PPY)
    conf = run_field_reversal(bars, split.confirmed, atr, COST_BPS, PPY, filtered=False)
    unconf = run_field_reversal(
        bars, split.unconfirmed, atr, COST_BPS, PPY, filtered=False
    )
    # filtered=False on already-selected signals: the qualification test ran inside
    # split_by_confirmation, so re-applying it here would be a no-op that hides which
    # stage did the selecting.

    def run_conf(shuffled_swings_list):
        s = field_signals(bars, shuffled_swings_list, PARAMS, grid)
        sp = split_by_confirmation(bars, s, PARAMS)
        return run_field_reversal(bars, sp.confirmed, atr, COST_BPS, PPY, filtered=False)

    cmp = compare_field_to_null(
        bars, swings, PARAMS, run_conf, ShuffleBand.LOCAL, n_sims, SEED, PPY
    )

    row = {
        "symbol": symbol,
        "n_qualifying": split.n_qualifying,
        "n_triggers": split.n_triggers,
        "n_absorbed": split.n_absorbed,
        "confirmed": book(conf, bars),
        "all_signals": book(all_signals, bars),
        "unconfirmed_DIAGNOSTIC_hindsight": book(unconf, bars),
        "confirmed_by_year": by_year(bars, conf),
        "bh_sharpe": bh["sharpe"],
        "bh_total_return": bh["total_return"],
        "null": cmp.to_dict(bars, PPY),
    }
    row["vs_all_delta"] = row["confirmed"]["sharpe"] - row["all_signals"]["sharpe"]
    row["vs_unconf_delta"] = (
        row["confirmed"]["sharpe"] - row["unconfirmed_DIAGNOSTIC_hindsight"]["sharpe"]
    )
    row["beats_all"] = row["vs_all_delta"] >= EFFECT_FLOOR
    row["beats_null"] = row["null"]["sharpe_delta"] >= EFFECT_FLOOR
    row["beats_bh"] = row["confirmed"]["sharpe"] > bh["sharpe"]
    row["clears_all_three"] = row["beats_all"] and row["beats_null"] and row["beats_bh"]
    return row


def render(payload) -> None:
    print(f"\n{'symbol':<10} {'book':<34} {'n':>5} {'Sharpe':>9} {'ret':>9} {'hit':>7}")
    for sym, r in payload["cells"].items():
        for name in ("confirmed", "all_signals", "unconfirmed_DIAGNOSTIC_hindsight"):
            b = r[name]
            print(f"{sym:<10} {name:<34} {b['n_trades']:>5} {b['sharpe']:>+9.3f} "
                  f"{b['total_return']:>+9.1%} {b['hit_rate']:>7.1%}")
        print(f"{sym:<10} {'buy_and_hold':<34} {'':>5} {r['bh_sharpe']:>+9.3f} "
              f"{r['bh_total_return']:>+9.1%}")
    print(f"\n{'symbol':<10} {'vs ALL':>9} {'vs null':>9} {'pct':>7} {'vs B&H':>9}  verdict")
    for sym, r in payload["cells"].items():
        v = []
        if r["beats_all"]: v.append("ALL")
        if r["beats_null"]: v.append("NULL")
        if r["beats_bh"]: v.append("BH")
        print(f"{sym:<10} {r['vs_all_delta']:>+9.3f} {r['null']['sharpe_delta']:>+9.3f} "
              f"{r['null']['sharpe_percentile']:>7.1f} "
              f"{r['confirmed']['sharpe'] - r['bh_sharpe']:>+9.3f}"
              f"  {'+'.join(v) if v else 'fail'}")
    n = sum(1 for r in payload["cells"].values() if r["clears_all_three"])
    print(f"\n{len(payload['cells'])} symbols; {n} clear all three hurdles")
    print("\nUNCONFIRMED is hindsight-classified: a DIAGNOSTIC, never a strategy.")


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
    cells = {}
    for symbol in SYMBOLS:
        print(f"=== {symbol} ===", flush=True)
        cells[symbol] = run_symbol(symbol, cleaned[symbol], vols[symbol], args.sims)
        r = cells[symbol]
        print(f"  confirmed {r['confirmed']['n_trades']:>4} S "
              f"{r['confirmed']['sharpe']:+.3f}   all {r['all_signals']['n_trades']:>4} S "
              f"{r['all_signals']['sharpe']:+.3f}   unconf(diag) "
              f"{r['unconfirmed_DIAGNOSTIC_hindsight']['n_trades']:>4} S "
              f"{r['unconfirmed_DIAGNOSTIC_hindsight']['sharpe']:+.3f}", flush=True)

    payload = {
        "n_sims": args.sims, "seed": SEED, "cost_bps": COST_BPS,
        "confirm_window": CONFIRM_WINDOW, "stop_atr": STOP_ATR,
        "target_r": FIELD_TARGET_R, "max_hold": MAX_HOLD,
        "params": {"k": PARAMS.k, "cluster_atr": PARAMS.cluster_atr},
        "effect_floor": EFFECT_FLOOR, "cells": cells,
        "elapsed_seconds": time.time() - started,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    render(payload)
    print(f"\nwrote {OUT} in {payload['elapsed_seconds']:.0f}s")


if __name__ == "__main__":
    main()
