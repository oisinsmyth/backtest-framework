"""D404 §12a -- measure the three construction defects, before the runner exists.

    uv run python scripts/probe_d404_construction.py

NOTHING HERE SCORES A CELL. No forward return is read, no book is built, no null is drawn.
It measures properties of D404's three DECLARED STATE CONSTRUCTIONS and nothing else.

WHY IT EXISTS. An external-evidence brief (working/leads/R1-cross-asset-regime.md) alleged two
mechanical defects in D404 §4. Those are claims about OUR construction rather than about the
literature, so they are checkable here, and the standing rule for that directory is that an
agent's summary is not a reading. This file checks them.

WHAT IT FOUND, and the third one is the reason the file is worth keeping:

  (i)  THE DISTRIBUTION-DRIFT CLAIM IS FALSE AS STATED. Alleged 2-5%/yr downward drift in
       log(HYG/IEF); measured -0.92%/yr, with the resulting median-rule imbalance running the
       OPPOSITE way (56.8% risk-ON). CURVE drifts -0.00%/yr at 49.8%. The brief's figures came
       from present-day yield aggregators and do not describe the realised 2010-2026 path.

  (ii) THE PRICE-SUM DEFECT IS REAL AND SEVERE. (XLU+XLP)/(XLY+XLK) sums SHARE PRICES, so XLP
       carries 66.5% of its own leg and XLK 60.9% of the other, purely on price level. A
       synthetic 2-for-1 split of one leg moves the level by 0.338 log units.

  (iii) AND THE ONE NOBODY HAD: EQUAL-WEIGHTING DOES NOT FIX THE IMBALANCE. The price-sum
       version sits above its trailing median on 28.5% of bars and the corrected equal-weighted
       version on 28.7%, because the imbalance is a REAL 16-YEAR TREND, not an artefact. A
       trailing-median rule on a trending series is a TREND RULE, not a state classifier. That
       is FINDINGS section 14's problem in the time domain, and it is why D404 now carries a
       [BAL] assertion requiring 40-60%.

THE HONEST LIMIT OF THIS PROBE, stated because the first version of it got this wrong. It
CANNOT settle the distribution question. A "cumulated log-return difference" of two PRICE series
is algebraically identical to their log price ratio -- the same object, so comparing them
isolates nothing and any agreement between them is a tautology, not a check. The real test
rebuilds the states on TOTAL RETURN using the fixture's events file, and is left to the runner.
`assert_tautology` below proves the identity holds to floating point so the limitation is
demonstrated rather than merely asserted.
"""

from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "data" / "fixtures"
ETF = FIX / "etf_wide_daily_raw.csv.gz"
OUT = ROOT / "data" / "d404_construction_probe.json"

LEGS = ["HYG", "IEF", "SHY", "XLU", "XLP", "XLY", "XLK"]
MED_BARS = 252
BAL_LO, BAL_HI = 0.40, 0.60          # the [BAL] band D404 section 12a(iii) now requires


def load() -> tuple[list[str], dict[str, np.ndarray]]:
    px: dict[str, dict[str, float]] = {s: {} for s in LEGS}
    dates: set[str] = set()
    with gzip.open(ETF, "rt") as fh:
        for r in csv.DictReader(fh):
            s = r["symbol"]
            if s in px:
                px[s][r["timestamp"][:10]] = float(r["close"])
                dates.add(r["timestamp"][:10])
    grid = sorted(dates)
    for s in LEGS:
        assert len(px[s]) == len(grid), f"{s}: {len(px[s])} bars against a {len(grid)}-bar grid"
    return grid, {s: np.array([px[s][d] for d in grid]) for s in grid and LEGS}


def drift_pa(level: np.ndarray) -> float:
    """Annualised linear drift of a log-level series, per 252 bars."""
    return float(np.polyfit(np.arange(level.size), level, 1)[0] * 252.0)


def above_median_share(level: np.ndarray, w: int = MED_BARS) -> tuple[float, int]:
    """Share of DEFINED bars on which level exceeds its own trailing w-bar median.

    Causal, and identical to c1_gate_stage0.trailing_median_rule's comparison: the window
    ends at t-1, so the value at t is never inside its own median."""
    m = np.full(level.size, np.nan)
    W = np.lib.stride_tricks.sliding_window_view(level[:-1], w)
    m[w:] = np.median(W, axis=-1)
    ok = np.isfinite(m)
    return float((level[ok] > m[ok]).mean()), int(ok.sum())


def cum_ret_diff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.concatenate([[0.0], np.cumsum(np.diff(np.log(a)) - np.diff(np.log(b)))])


def assert_tautology(P: dict[str, np.ndarray]) -> None:
    """[X] THE LIMITATION, DEMONSTRATED. A cumulated log-return difference of two PRICE series
    IS their log price ratio, up to the starting constant. If this assertion ever fails, the
    two are different objects and the comparison would mean something; while it passes, any
    agreement between them is arithmetic and settles nothing about distributions."""
    lhs = cum_ret_diff(P["HYG"], P["IEF"])
    rhs = np.log(P["HYG"]) - np.log(P["IEF"])
    rhs = rhs - rhs[0]
    worst = float(np.max(np.abs(lhs - rhs)))
    assert worst < 1e-10, f"[X] the identity does not hold ({worst:.2e}) -- re-read the probe"
    print(f"  [X] cumulated log-return difference == log price ratio to {worst:.2e} "
          f"-- so that comparison CANNOT test the distribution claim")


def main() -> None:
    grid, P = load()
    T = len(grid)
    print(f"{T} bars, {grid[0]} -> {grid[-1]} ({T / 252:.1f} years)\n")
    assert_tautology(P)

    meta = json.loads((FIX / "etf_wide_daily_raw.meta.json").read_text())
    evj = json.loads((FIX / "etf_wide_daily_raw_events.json").read_text())
    payload = evj.get("dividends", evj) if isinstance(evj, dict) else {}
    divs = {s: len(payload.get(s, [])) for s in LEGS} if isinstance(payload, dict) else {}
    print(f"  fixture split_adjusted={meta.get('split_adjusted')}; dividend records {divs}")
    print("  -> distributions ARE available; rebuilding the states on total return is the "
          "runner's job, not this probe's\n")

    states = {
        "CREDIT": np.log(P["HYG"]) - np.log(P["IEF"]),
        "CURVE": np.log(P["IEF"]) - np.log(P["SHY"]),
        "DEFENSIVE_price_sum": np.log(P["XLU"] + P["XLP"]) - np.log(P["XLY"] + P["XLK"]),
        "DEFENSIVE_equal_weight": np.concatenate([[0.0], np.cumsum(
            0.5 * (np.diff(np.log(P["XLU"])) + np.diff(np.log(P["XLP"])))
            - 0.5 * (np.diff(np.log(P["XLY"])) + np.diff(np.log(P["XLK"]))))]),
    }

    res = {}
    print(f"{'state':<24}{'drift %/yr':>12}{'above median':>14}{'bars':>7}  [BAL] 40-60%")
    for name, lv in states.items():
        d, (sh, nb) = drift_pa(lv), above_median_share(lv)
        ok = BAL_LO <= sh <= BAL_HI
        res[name] = {"drift_pa": d, "above_median_share": sh, "defined_bars": nb, "bal_pass": ok}
        print(f"{name:<24}{d * 100:>+11.2f}%{sh:>13.1%}{nb:>7}  {'PASS' if ok else 'FAIL'}")

    # the price-sum defect, in the two forms that make it concrete
    su, sy = P["XLU"][-1] + P["XLP"][-1], P["XLY"][-1] + P["XLK"][-1]
    weights = {"XLU": P["XLU"][-1] / su, "XLP": P["XLP"][-1] / su,
               "XLY": P["XLY"][-1] / sy, "XLK": P["XLK"][-1] / sy}
    split = np.log(P["XLU"] + P["XLP"]) - np.log(P["XLY"] / 2.0 + P["XLK"])
    shift = float(np.abs(split - states["DEFENSIVE_price_sum"]).mean())
    print(f"\n  price-sum leg weights, last bar: "
          + ", ".join(f"{k} {v:.1%}" for k, v in weights.items()))
    print(f"  a synthetic 2-for-1 split of XLY alone moves the price-sum level by "
          f"{shift:+.4f} log units on average")
    print(f"  the equal-weighted return version is split-invariant by construction")

    print(f"\n  (iii) equal-weighting moves the imbalance from "
          f"{res['DEFENSIVE_price_sum']['above_median_share']:.1%} to "
          f"{res['DEFENSIVE_equal_weight']['above_median_share']:.1%} -- i.e. NOT AT ALL. "
          f"The imbalance is a real trend, not an artefact.")

    OUT.write_text(json.dumps({
        "record": "docs/decisions/D404-the-cross-asset-state.md section 12a",
        "bars": T, "span": [grid[0], grid[-1]],
        "split_adjusted": meta.get("split_adjusted"), "dividend_records": divs,
        "states": res, "price_sum_leg_weights_last_bar": weights,
        "synthetic_split_shift_log_units": shift,
        "bal_band": [BAL_LO, BAL_HI],
        "limitation": "cumulated log-return difference of PRICE series == log price ratio; "
                      "the distribution question needs total-return series and is left open",
    }, indent=2))
    print(f"\nwritten {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
