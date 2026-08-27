"""D231 — the exposure dial.

Two families that raise the bar the signal must clear, rather than adding an
unrelated AND condition:

    T  hold when z > c[i,t], c a rolling per-symbol quantile   (time-series bar)
    N  hold the strongest fraction of the universe among positives (cross-sectional)

    z = hist / trailing_sd(hist, 252)

Both SELF-CALIBRATE to a declared exposure target, so exposure is a control
rather than an outcome and the two families are comparable (amendment 1).

TWO STAGES (amendment 2):
    --stage screen   the mined 57. Proves the machinery, kills catastrophic
                     cells. NOT A TEST -- no verdict is drawn here.
    --stage test     the holdout 60. The verdict, survivors only.

Offline, deterministic, seed 0. `--report-only` re-renders from the artifact.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
import warnings
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research import macd as M  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


L = _load("d217_ladder", "run_macd_ladder.py")
J = _load("d229_jerk", "run_jerk_rung.py")
F = _load("d228_filter", "run_filter_search.py")

SUMMARY = REPO / "data" / "exposure_dial_{stage}.json"
RESULTS = REPO / "EXPOSURE_DIAL_RESULTS.md"

PPY = L.PPY
SEED = 0
LAG = 1
N_SIMS = 1000
RF_PER_BAR = J.RF_PER_BAR
RF_ANNUAL = J.RF_ANNUAL

# Declared in D231.
NORM_WINDOW = 252
TARGETS = (0.40, 0.30, 0.20, 0.10)
UNIVERSE_FRACTIONS = {0.40: 0.544, 0.30: 0.351, 0.20: 0.228, 0.10: 0.105}

# Amendment 2: the screen's two declared gates.
EXPOSURE_TOLERANCE_PP = 3.0
SELECTION_FLOOR = -0.25

FIXTURES = {
    "screen": (
        REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw.csv.gz",
        REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw_events.json",
    ),
    "test": (
        REPO / "data" / "fixtures" / "universe_holdout_daily_raw.csv.gz",
        REPO / "data" / "fixtures" / "universe_holdout_daily_raw_events.json",
    ),
}


def load(stage: str):
    """Reuse `run_macd_ladder.load_panel` by repointing its module constants.

    Cleaning, per-symbol costs, the dividend sidecar and the total-return frame
    are all D217's, unchanged. Writing a second loader would be restating the
    thing D212 says to reuse -- and would be the place a divergence between the
    two fixtures could hide."""
    L.FIXTURE, L.EVENTS = FIXTURES[stage]
    return L.load_panel()


def z_scores(panel, cleaned) -> np.ndarray:
    """Signal strength, comparable across instruments.

    `hist` scales with price level and volatility, so a raw bar would hold energy
    funds constantly and bond funds never. Dividing by each symbol's own trailing
    dispersion makes `z = 1.5` mean the same thing everywhere."""
    hist = np.asarray(
        [M.impulse_macd_series(cleaned[s]).histogram for s in panel.symbols], dtype=float
    )
    sd = F.trailing_std(np.nan_to_num(hist, nan=0.0), NORM_WINDOW)
    with np.errstate(invalid="ignore", divide="ignore"):
        z = np.where(sd > 0.0, hist / sd, np.nan)
    return z


def dial_threshold(z: np.ndarray, target: float) -> np.ndarray:
    """Family T. `c[i,t]` is the (1-target) quantile of that symbol's own z over
    the prior NORM_WINDOW bars -- STRICTLY trailing, so bar t is not in its own
    threshold. Exposure lands near `target` by construction, on any fixture, with
    nothing inherited from any other one."""
    n, T = z.shape
    hold = np.zeros((n, T))
    q = 1.0 - target
    for t in range(NORM_WINDOW, T):
        window = z[:, t - NORM_WINDOW : t]
        with np.errstate(invalid="ignore"), warnings.catch_warnings():
            # Rows are all-NaN until the z-normaliser itself has warmed up. That is
            # by construction, and those bars are inside the arm's 1,000-bar warm-up
            # anyway -- the warning is noise, not news.
            warnings.simplefilter("ignore", RuntimeWarning)
            c = np.nanquantile(window, q, axis=1)
        cur = z[:, t]
        hold[:, t] = np.where(np.isnan(cur) | np.isnan(c), 0.0, (cur > c) * 1.0)
    return hold


def dial_top_n(z: np.ndarray, target: float) -> np.ndarray:
    """Family N. Among symbols with z > 0, hold the strongest `frac * n`.

    Declared as a FRACTION of the universe rather than a count, so the rule moves
    from 57 symbols to 60 without a second calibration."""
    n, T = z.shape
    k = max(1, int(round(UNIVERSE_FRACTIONS[target] * n)))
    filled = np.nan_to_num(z, nan=-np.inf)
    order = np.argsort(-filled, axis=0)
    rank = np.empty_like(order)
    np.put_along_axis(rank, order, np.arange(n)[:, None].repeat(T, 1), axis=0)
    return ((rank < k) & (filled > 0.0)) * 1.0


def score(panel, position: np.ndarray, start: int) -> dict:
    live = slice(start, None)
    total = L.portfolio_log_returns(panel, position, total_return=True)[live]
    price = L.portfolio_log_returns(panel, position)[live]
    exposure = position[:, live].mean(axis=0)
    changes = np.diff(position, axis=1, prepend=0.0)[:, live]
    ex = total - exposure * RF_PER_BAR
    sd = float(np.std(ex, ddof=1))
    return {
        "excess_sharpe": (float(np.mean(ex)) / sd * math.sqrt(PPY)) if sd > 0 else 0.0,
        "sharpe_rf0": L.sharpe_of(total),
        "total_return": L.total_return_of(total),
        "total_return_price": L.total_return_of(price),
        "max_drawdown": L.max_drawdown_of(total),
        "cagr": float(np.expm1(np.sum(total) / (len(total) / PPY))),
        "vol": float(np.std(total, ddof=1) * math.sqrt(PPY)),
        "exposure": float(exposure.mean()),
        "entries": int(np.sum(changes > 0.0)),
        "min_entries_per_symbol": int(np.sum(changes > 0.0, axis=1).min()),
        "turnover_units": int(np.sum(np.diff(position, axis=1) != 0.0)),
    }


def _excess_sharpe(panel, position: np.ndarray, start: int) -> float:
    """Lean scorer for the null's inner loop — one portfolio pass, not the full dict."""
    total = L.portfolio_log_returns(panel, position, total_return=True)[start:]
    ex = total - position[:, start:].mean(axis=0) * RF_PER_BAR
    sd = float(np.std(ex, ddof=1))
    return (float(np.mean(ex)) / sd * math.sqrt(PPY)) if sd > 0 else 0.0


def rotation_nulls(panel, positions: dict, start: int, parent_sh: float) -> dict:
    """Matched-count rotation null, per cell AND best-of-search across cells.

    Each replication circularly rotates every cell's position series by ONE shared
    offset vector. Rotation is matched exactly on the things that would otherwise
    explain a result -- every rotated book has the SAME exposure, the SAME turnover
    and the SAME holding-period distribution as the real one. It is the same book
    pointed at the wrong bars, so a delta over it cannot be "you just traded less".
    That is precisely the confound the sqrt(f) law describes analytically, measured
    here instead of assumed.

    ONE OFFSET VECTOR SHARED ACROSS CELLS, following D228: rotating each cell
    independently would make the eight artificially independent, inflating the max
    and producing a floor wrong in the conservative direction.

    `run_macd_ladder.rotation_null` is the precedent but scores at rf=0 and takes a
    single book; this needs excess Sharpe and the cross-cell maximum."""
    rng = np.random.default_rng(SEED)
    n, T = next(iter(positions.values())).shape
    span = T - start
    names = list(positions)
    per = {k: np.empty(N_SIMS) for k in names}
    best = np.empty(N_SIMS)
    for s in range(N_SIMS):
        offsets = rng.integers(1, span, size=n)
        deltas = []
        for k in names:
            live = positions[k][:, start:]
            rot = np.empty_like(positions[k])
            for i in range(n):
                rot[i, start:] = np.roll(live[i], int(offsets[i]))
            d = _excess_sharpe(panel, rot, start) - parent_sh
            per[k][s] = d
            deltas.append(d)
        best[s] = max(deltas)
    return {
        "n_sims": N_SIMS,
        "best_p50": float(np.percentile(best, 50)),
        "best_p95": float(np.percentile(best, 95)),
        "per_cell_p95": {k: float(np.percentile(per[k], 95)) for k in names},
        "per_cell_percentile_of_actual": {},  # filled by the caller
    }


def build(stage: str) -> dict:
    t0 = time.time()
    panel, cleaned = load(stage)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

    parent_pos = J.arm_positions(
        panel, cleaned, "I1_signal", long_short=False, gated=False, start=start
    )
    parent = score(panel, parent_pos, start)

    ones = np.ones_like(parent_pos)
    ones[:, :start] = 0.0
    bh = score(panel, ones, start)

    z = z_scores(panel, cleaned)
    cells, failures, cell_pos = [], [], {}
    for family, fn in (("T", dial_threshold), ("N", dial_top_n)):
        for target in TARGETS:
            pos = F.shift(fn(z, target), LAG)
            pos[:, :start] = 0.0
            c = score(panel, pos, start)
            cell_pos[f"{family}@{target:.0%}"] = pos

            # The sqrt(f) law: Sharpe ~ sqrt(exposure) x (per-bet quality). What a
            # cell scores ABOVE that is the only part attributable to selection.
            predicted = parent["excess_sharpe"] * math.sqrt(
                c["exposure"] / parent["exposure"]
            )
            selection = (c["excess_sharpe"] / predicted - 1.0) if predicted else 0.0

            drift_pp = abs(c["exposure"] - target) * 100.0
            if drift_pp > EXPOSURE_TOLERANCE_PP:
                failures.append(
                    f"{family}@{target:.0%} landed at {c['exposure']:.1%} "
                    f"({drift_pp:.1f}pp off, tolerance {EXPOSURE_TOLERANCE_PP}pp)"
                )

            cells.append({
                "cell": f"{family}@{target:.0%}",
                "family": family,
                "target": target,
                **c,
                "exposure_drift_pp": drift_pp,
                "sqrt_f_predicted": predicted,
                "selection_quality": selection,
                "survives_screen": selection >= SELECTION_FLOOR,
                # Levered to B&H vol with financing at rf. DISCLOSED as a monotone
                # transform of excess Sharpe, not independent evidence -- it ranks
                # cells identically. Reported because it puts the answer in the
                # units the question was asked in.
                "levered_return_at_bh_vol": RF_ANNUAL
                + c["excess_sharpe"] * bh["vol"],
            })

    nulls = rotation_nulls(panel, cell_pos, start, parent["excess_sharpe"])
    for c in cells:
        d = c["excess_sharpe"] - parent["excess_sharpe"]
        c["delta_vs_parent"] = d
        c["beats_own_rotation_p95"] = bool(d > nulls["per_cell_p95"][c["cell"]])
    best_cell = max(cells, key=lambda c: c["delta_vs_parent"])
    clears_B = bool(best_cell["delta_vs_parent"] > nulls["best_p95"])

    if failures and stage == "screen":
        raise SystemExit(
            "EXPOSURE CALIBRATION FAILED -- the dials do not land where declared:\n  "
            + "\n  ".join(failures)
            + "\nD231 amendment 2 stops here rather than spending the holdout on a "
              "mechanism that does not do what the record says it does."
        )

    return {
        "produced": "D231",
        "stage": stage,
        "is_verdict": stage == "test",
        "seed": SEED,
        "rf_annual": RF_ANNUAL,
        "fixture": str(FIXTURES[stage][0].name),
        "first_live_date": panel.dates[start],
        "last_date": panel.dates[-1],
        "live_bars": len(panel.dates) - start,
        "n_symbols": len(panel.symbols),
        "parent": parent,
        "buy_and_hold": bh,
        "cells": cells,
        "nulls": nulls,
        "best_cell": best_cell["cell"],
        "clears_B": clears_B,
        "exposure_failures": failures,
        "screen": {
            "floor": SELECTION_FLOOR,
            "survivors": [c["cell"] for c in cells if c["survives_screen"]],
            "dropped": [c["cell"] for c in cells if not c["survives_screen"]],
        },
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def _pct(x: float) -> str:
    return f"{x * 100:+.2f}%"


def render(p: dict) -> str:
    o = []
    o.append("# D231 — the exposure dial\n")
    banner = (
        "**STAGE 1 — SCREEN. This is not a test and carries no verdict.** Its job is to prove "
        "the dials land where declared and to drop catastrophic cells before the holdout is "
        "spent. Sharpes below are reported for completeness only."
        if p["stage"] == "screen"
        else "**STAGE 2 — TEST. This is the verdict.**"
    )
    o.append(banner + "\n")
    o.append(
        f"*`scripts/run_exposure_dial.py --stage {p['stage']}`, seed {p['seed']}, "
        f"{p['elapsed_seconds']}s. `{p['fixture']}` — {p['n_symbols']} symbols, "
        f"{p['first_live_date']} to {p['last_date']}, {p['live_bars']:,} live bars. "
        f"rf = {p['rf_annual']:.0%} on the exposed fraction.*\n"
    )
    par, bh = p["parent"], p["buy_and_hold"]
    o.append("## Baseline\n")
    o.append("| book | excess Sharpe | CAGR | vol | money | max DD | exposure |")
    o.append("|---|---:|---:|---:|---:|---:|---:|")
    for label, s in (("**parent (50%)**", par), ("buy and hold", bh)):
        o.append(
            f"| {label} | {s['excess_sharpe']:+.3f} | {s['cagr'] * 100:.2f}% | "
            f"{s['vol'] * 100:.1f}% | {_pct(s['total_return'])} | "
            f"{_pct(s['max_drawdown'])} | {s['exposure'] * 100:.1f}% |"
        )
    o.append("")
    o.append("## The dial\n")
    o.append(
        "`√f predicts` is what the cell scores from trading less **alone**. `selection` is "
        "what it earned above that — the only part attributable to picking better trades.\n"
    )
    o.append("| cell | exposure | excess Sharpe | √f predicts | **selection** | money | entries/sym | levered @ B&H vol |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for c in p["cells"]:
        o.append(
            f"| **{c['cell']}** | {c['exposure'] * 100:.1f}% | {c['excess_sharpe']:+.3f} | "
            f"{c['sqrt_f_predicted']:+.3f} | **{c['selection_quality'] * 100:+.0f}%** | "
            f"{_pct(c['total_return'])} | {c['min_entries_per_symbol']} | "
            f"{c['levered_return_at_bh_vol'] * 100:.2f}% |"
        )
    o.append("")
    o.append(
        f"*Levered column is a monotone transform of excess Sharpe — it ranks cells "
        f"identically and is not independent evidence. Buy-and-hold makes "
        f"{bh['cagr'] * 100:.2f}% at {bh['vol'] * 100:.1f}% vol for comparison.*\n"
    )
    nl = p["nulls"]
    o.append("## Nulls — matched-count rotation\n")
    o.append(
        f"Each cell rotated against itself {nl['n_sims']:,} times: same exposure, same "
        f"turnover, same holding-period distribution, pointed at the wrong bars. A delta "
        f"over this cannot be \"you just traded less\" — it is the √f confound measured "
        f"rather than assumed. One offset vector shared across cells, so cross-cell "
        f"correlation survives.\n"
    )
    o.append("| cell | Δ vs parent | own-rotation p95 | beats own rotation |")
    o.append("|---|---:|---:|:--:|")
    for c in p["cells"]:
        o.append(
            f"| **{c['cell']}** | {c['delta_vs_parent']:+.3f} | "
            f"{nl['per_cell_p95'][c['cell']]:+.3f} | "
            f"{'**PASS**' if c['beats_own_rotation_p95'] else '—'} |"
        )
    o.append("")
    o.append(
        f"**Best-of-search across all {len(p['cells'])} cells: best real "
        f"{max(c['delta_vs_parent'] for c in p['cells']):+.3f} against a null p95 of "
        f"**{nl['best_p95']:+.3f}** (p50 {nl['best_p50']:+.3f}). "
        f"Hurdle B: {'CLEARS' if p['clears_B'] else 'FAILS'}.**\n"
    )
    if p["stage"] == "screen":
        o.append(
            "*Hurdle B is reported here for information. **Stage 1 carries no verdict** — "
            "the mined fixture's detection floor makes a pass here uninformative, and only "
            "stage 2 decides.*\n"
        )
    s = p["screen"]
    o.append("## Screen\n")
    o.append(
        f"Floor: selection quality ≥ {s['floor'] * 100:.0f}%. "
        f"**{len(s['survivors'])} of {len(p['cells'])} survive.**\n"
    )
    o.append(f"- **survivors:** {', '.join(s['survivors']) or 'none'}")
    o.append(f"- **dropped:** {', '.join(s['dropped']) or 'none'}")
    o.append("")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("screen", "test"), default="screen")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    path = Path(str(SUMMARY).format(stage=args.stage))
    if args.report_only:
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = build(args.stage)
        path.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")

    RESULTS.write_text(render(payload), encoding="utf-8")
    par = payload["parent"]
    print(f"stage               {payload['stage']}  ({payload['n_symbols']} symbols)")
    print(f"parent              {par['excess_sharpe']:+.3f}  exposure {par['exposure']:.1%}")
    print(f"buy and hold        {payload['buy_and_hold']['excess_sharpe']:+.3f}")
    print()
    nl = payload["nulls"]
    print(f"{'cell':10s} {'expo':>7s} {'exSh':>8s} {'sqrt-f':>8s} {'select':>8s} "
          f"{'d(par)':>8s} {'rot p95':>8s}  rot  screen")
    for c in payload["cells"]:
        print(f"{c['cell']:10s} {c['exposure']:6.1%} {c['excess_sharpe']:+8.3f} "
              f"{c['sqrt_f_predicted']:+8.3f} {c['selection_quality']:+7.0%} "
              f"{c['delta_vs_parent']:+8.3f} {nl['per_cell_p95'][c['cell']]:+8.3f}  "
              f"{'PASS' if c['beats_own_rotation_p95'] else '  . '}  "
              f"{'keep' if c['survives_screen'] else 'DROP'}")
    print()
    print(f"best-of-search      best {max(c['delta_vs_parent'] for c in payload['cells']):+.3f}"
          f"  null p95 {nl['best_p95']:+.3f}   hurdle B "
          f"{'CLEARS' if payload['clears_B'] else 'FAILS'}")
    print(f"survivors: {', '.join(payload['screen']['survivors']) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
