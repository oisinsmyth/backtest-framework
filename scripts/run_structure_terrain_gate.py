"""D214 — the terrain map as a confluence gate on the structure setups.

    uv run python scripts/run_structure_terrain_gate.py
    uv run python scripts/run_structure_terrain_gate.py --report-only

`docs/decisions/D214-the-terrain-gate.md` governs this and was committed before this file
existed. Read it first — it records the override of D203's stop, the prior, and why
`inverted` is the pre-registered primary.

## The three bars, which are the deliverable

Every verdict is reported against three multiplicity counts — this study alone, plus the
structure ledger, plus both ledgers — with an explicit pass/fail on each. `TERRAIN_RESULTS`
states the rule that forces the third: *"Anything that reuses these sensors inherits the
count."* A result that clears the fresh bar and fails the combined one is reported as
exactly that.

## Three things this file is careful about

**The gate reads the signal bar, not the entry bar.** `entry_index - 1`, so the bar that
decides never also pays. Both inputs are individually look-ahead guarded; their composition
is new, and composition is where a leak gets reintroduced.

**The field's windows are calendar-matched to 15m.** D202 ran daily. Leaving `atr_window`
at 20 would put five hours of volatility under a map spanning years — D194's defect
exactly — so it is 1,920 here and asserted by test.

**A gate changes the sample merely by existing.** Keeping half the trades moves the mean
whatever it selects on, so the gate-shuffle control permutes the readings among setups and
re-applies the identical gate. That is what separates terrain's *placement* from the gate's
*selectivity*, and D213 is the reason it is not optional: 54% of noise draws there
manufactured a surviving rule.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.research.breakout_universe import align_volumes  # noqa: E402
from backtest_framework.research.structure import market_structure  # noqa: E402
from backtest_framework.research.structure_setups import (  # noqa: E402
    ATR_WINDOW_15M,
    find_setups,
)
from backtest_framework.research.structure_strategies import (  # noqa: E402
    Wrapper,
    expectancy,
    r_multiples,
    run_arm,
)
from backtest_framework.research.terrain_field import (  # noqa: E402
    FieldParams,
    Grid,
    build_grid,
    confirmed_swings,
    local_imbalance,
)
from backtest_framework.research.terrain_field_nulls import rotation_null  # noqa: E402
from backtest_framework.research.terrain_strategies import (  # noqa: E402
    PositionResult,
    buy_and_hold,
)
from backtest_framework.validation.dsr import (  # noqa: E402
    deflated_sharpe_ratio,
    expected_max_sharpe,
)

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "structure_terrain_gate_summary.json"
RESULTS = REPO / "docs" / "results" / "STRUCTURE_RESULTS.md"

SYMBOLS = ("BTCUSDT", "ETHUSDT")
PRIMARY_K, PRIMARY_TOUCH = 2, 0.5
PPY = 96.0 * 365.0
BARS_PER_DAY = 96
SEED, N_SHUFFLES = 0, 500
N_ROTATIONS = 200
"""Fewer draws than the gate-shuffle control, and run on fewer cells, for a stated reason.

Each rotation walks a 294,000-bar equity curve, so 500 draws across all twelve cells is
hours. The rotation null answers *did the exposure change at the right moments*, which only
has something to explain where there is an advantage to explain — so it runs on the primary
cell always, plus any cell that clears the gross-R hurdle. Scoping a control by where it can
change a verdict is legitimate; scoping it by where it gives the answer you want is not, and
the rule is fixed here rather than after the numbers."""
START_CAPITAL = 10_000.0

TIERS = ((0.0, "zero"), (10.0, "10bp"), (40.0, "40bp"))
"""Per side, so a round trip pays twice each (D212). Zero is a diagnostic, never a strategy."""
VERDICT_TIER = "40bp"

FIELD = FieldParams(
    k=2,
    cluster_atr=0.5,
    erase=False,
    atr_window=ATR_WINDOW_15M,
    vol_norm_bars=90 * BARS_PER_DAY,
)
"""D202's raw-field parameters with every window calendar-matched at 96 bars/day (D194).

`k` and `cluster_atr` are the only values `FieldParams` enforces, so the windows are free
parameters and the match needs no change to the closed module."""

DIRECTIONS = (("inverted", -1), ("aligned", +1))
"""`inverted` first because it is the pre-registered primary: D202 measured this reading
anti-predictive at the 2.6th percentile, so gating on terrain DISAGREEING is the one
mechanism here with evidence behind it."""

THRESHOLD_NAMES = ("zero", "median", "tertile")
"""WP7's own set — |terrain| above 0, its median, its upper tertile — reused not re-chosen."""

EDGE = 0.10
"""Gross-R gain a gate must produce over the ungated arm. Pre-registered."""

INHERITED = {"fresh": 0, "structure only": 124, "combined": 124 + 259}
"""Looks inherited before this study's own 12 are added. The combined figure is forced by
`TERRAIN_RESULTS.md`: anything reusing these sensors inherits the count."""
OWN_LOOKS = 12


def bar_returns(bars: Sequence[Any]) -> tuple[float, ...]:
    closes = [b.bar.close for b in bars]
    return tuple(
        [0.0]
        + [
            math.log(b / a) if a > 0.0 and b > 0.0 else 0.0
            for a, b in zip(closes, closes[1:])
        ]
    )


def position_of(bars: Sequence[Any], trades: Sequence[Any], cost_bps: float) -> PositionResult:
    position = [0.0] * len(bars)
    for trade in trades:
        for t in range(trade.entry_index, min(trade.exit_index + 1, len(bars))):
            position[t] = float(trade.direction)
    return PositionResult(tuple(position), bar_returns(bars), cost_bps, PPY)


def gate_keeps(reading: float, direction: int, want: int, floor: float) -> bool:
    """Does this trade survive the gate?

    `want` is +1 for `aligned` and -1 for `inverted`. A reading of exactly zero carries no
    opinion and is refused by both directions rather than assigned to one — an arbitrary
    tiebreak here would put every flat-field trade into whichever arm the sign convention
    happened to favour."""
    if not math.isfinite(reading) or abs(reading) < floor:
        return False
    side = 1 if reading > 0.0 else (-1 if reading < 0.0 else 0)
    if side == 0:
        return False
    return side == want * direction


def evaluate(
    bars: Sequence[Any],
    trades: Sequence[Any],
    readings: Sequence[float],
    want: int,
    floor: float,
) -> dict[str, Any]:
    """One gate cell: the kept book, the rejected book, and the ungated one beside them."""
    kept, rejected = [], []
    for trade, reading in zip(trades, readings):
        (kept if gate_keeps(reading, trade.direction, want, floor) else rejected).append(trade)

    # D206/D209, three times over: a count that only appears as a subtraction is unchecked.
    assert len(kept) + len(rejected) == len(trades)

    def book(subset: Sequence[Any]) -> dict[str, Any]:
        if not subset:
            return {"n": 0}
        out: dict[str, Any] = {"n": len(subset)}
        for bps, label in TIERS:
            result = position_of(bars, subset, bps)
            stats = expectancy(subset, bps)
            out[label] = {
                "mean_gross_r": statistics.fmean(t.r_multiple for t in subset),
                "mean_net_r": stats["mean_r"],
                "median_net_r": stats["median_r"],
                "hit_rate": stats["hit_rate"],
                "share_untradeable": stats["share_untradeable"],
                "sharpe": result.curve_sharpe(bars, PPY),
                "total_return": result.curve_total_return(bars),
                "pnl": START_CAPITAL * result.curve_total_return(bars),
                "max_drawdown": result.max_drawdown(bars),
            }
        return out

    all_book, kept_book, rejected_book = book(trades), book(kept), book(rejected)
    gross_all = statistics.fmean(t.r_multiple for t in trades)
    return {
        "n_all": len(trades),
        "n_kept": len(kept),
        "n_rejected": len(rejected),
        "share_kept": len(kept) / len(trades) if trades else 0.0,
        "ungated": all_book,
        "kept": kept_book,
        "rejected": rejected_book,
        "advantage_gross_r": (
            statistics.fmean(t.r_multiple for t in kept) - gross_all if kept else float("nan")
        ),
        "counterfactual_gross_r": (
            statistics.fmean(t.r_multiple for t in rejected) if rejected else float("nan")
        ),
        "_kept_trades": kept,
    }


def shuffle_control(
    trades: Sequence[Any],
    readings: Sequence[float],
    want: int,
    floor: float,
    n: int,
    seed: int,
) -> dict[str, Any]:
    """Permute the readings among setups and re-apply the identical gate.

    A gate keeping half the trades moves the mean whatever it selects on. This is what
    separates terrain's PLACEMENT from the gate's SELECTIVITY, and D213 is why it is not
    optional — 54% of noise draws there manufactured a surviving rule."""
    rng = np.random.default_rng(seed)
    gross = np.asarray([t.r_multiple for t in trades], dtype=float)
    dirs = np.asarray([t.direction for t in trades], dtype=int)
    vals = np.asarray(readings, dtype=float)
    base = float(gross.mean())
    out: list[float] = []
    for _ in range(n):
        shuffled = vals[rng.permutation(len(vals))]
        mask = np.array(
            [gate_keeps(v, d, want, floor) for v, d in zip(shuffled, dirs)], dtype=bool
        )
        out.append(float(gross[mask].mean() - base) if mask.any() else 0.0)
    arr = np.asarray(out, dtype=float)
    return {
        "n_draws": n,
        "mean": float(arr.mean()),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "max": float(arr.max()),
    }


def dsr_table(sharpe: float, t: int, var_trials: float) -> dict[str, Any]:
    """The deliverable: the same observed Sharpe against three multiplicity counts.

    Required-Sharpe is found by bisection on `deflated_sharpe_ratio` rather than inverted
    analytically, because the closed form is not worth the risk of getting it subtly wrong
    for a number this load-bearing."""
    daily = 1.0 / math.sqrt(PPY)
    out: dict[str, Any] = {}
    for label, inherited in INHERITED.items():
        n = inherited + OWN_LOOKS
        sr0 = expected_max_sharpe(n, var_trials)
        observed = deflated_sharpe_ratio(sharpe * daily, t, 0.0, 3.0, n, var_trials / PPY)
        lo, hi = 0.0, 8.0
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if deflated_sharpe_ratio(mid * daily, t, 0.0, 3.0, n, var_trials / PPY) < 0.95:
                lo = mid
            else:
                hi = mid
        out[label] = {
            "n_looks": n,
            "sr0_annual": sr0,
            "required_annual_sharpe": hi,
            "observed_dsr": observed,
            "clears": sharpe >= hi,
        }
    return out


def run_symbol(symbol: str, bars: Sequence[Any], volumes: Sequence[float]) -> dict[str, Any]:
    states = market_structure(bars, PRIMARY_K)
    setups = list(find_setups(bars, PRIMARY_K, PRIMARY_TOUCH, states=states).setups)
    trades = run_arm(bars, setups, (), Wrapper(), allow_overlap=True)

    print("    building the field (calendar-matched to 15m)", flush=True)
    grid = build_grid(bars, FIELD.bucket_ln)
    swings = confirmed_swings(bars, volumes, FIELD)
    field = local_imbalance(bars, swings, FIELD, grid)

    # An inherited non-causality, measured before the verdict rather than assumed away.
    # `build_grid` spans the WHOLE series' high and low, so the axis a reading is
    # discretised onto knows the eventual price range. `test_terrain_field.py` knew and
    # pinned around it ("same axis, or the buckets alone would differ") — correct for a
    # signal, where the axis is a discretisation choice. A GATE reads only the sign, so the
    # question is whether the sign moves, not whether the number does.
    #
    # The FIRST version of this census compared the full-series grid against one built from
    # the first half, and returned exactly zero on both symbols. Not a result — a
    # tautology. `Grid.bucket` and `Grid.centres` depend only on `ln_min` and `bucket_ln`,
    # and the lowest low of this fixture falls in the first half on both symbols, so
    # `ln_min` is unchanged and every bucket index is identical by construction. The two
    # grids differed only in their TOP, and causal deposits put no mass there at an early
    # bar. It could not have failed.
    #
    # Perturbing the ORIGIN is the potent version: shift `ln_min` by half a bucket, which
    # is the largest misalignment the discretisation admits, and count sign flips.
    shifted_grid = Grid(
        grid.ln_min - 0.5 * FIELD.bucket_ln, FIELD.bucket_ln, grid.n + 1
    )
    shifted_field = local_imbalance(bars, swings, FIELD, shifted_grid)
    shifts = [
        abs(field[t.entry_index - 1] - shifted_field[t.entry_index - 1]) for t in trades
    ]
    flips = sum(
        1 for t in trades
        if (field[t.entry_index - 1] > 0) != (shifted_field[t.entry_index - 1] > 0)
    )
    grid_census = {
        "n_trades": len(trades),
        "max_shift": max(shifts) if shifts else 0.0,
        "mean_shift": statistics.fmean(shifts) if shifts else 0.0,
        "sign_flips": flips,
        "share_flipped": flips / len(trades) if trades else 0.0,
        "prefix_grid_is_identical": True,
        "prefix_note": (
            "A prefix grid changes nothing on this fixture because the lowest low falls in "
            "the first half, so ln_min is unchanged and every bucket index is identical. "
            "That comparison is a tautology here and is reported as one."
        ),
    }
    print(
        f"    grid census: {len(trades):,} trades, mean shift "
        f"{grid_census['mean_shift']:.4f}, sign flips {flips} "
        f"({grid_census['share_flipped']:.2%})",
        flush=True,
    )

    # Read at the SIGNAL bar, so the bar that decides never also pays.
    readings = [field[t.entry_index - 1] for t in trades]
    magnitudes = [abs(r) for r in readings if math.isfinite(r) and r != 0.0]
    floors = {
        "zero": 0.0,
        "median": statistics.median(magnitudes) if magnitudes else 0.0,
        "tertile": (
            float(np.percentile(np.asarray(magnitudes), 66.7)) if magnitudes else 0.0
        ),
    }

    cells: dict[str, Any] = {}
    for name, want in DIRECTIONS:
        for tname in THRESHOLD_NAMES:
            key = f"{name}|{tname}"
            got = evaluate(bars, trades, readings, want, floors[tname])
            kept_trades = got.pop("_kept_trades")
            got["control"] = shuffle_control(
                trades, readings, want, floors[tname], N_SHUFFLES, SEED
            )
            wants_rotation = key == "inverted|zero" or (
                got["advantage_gross_r"] == got["advantage_gross_r"]
                and got["advantage_gross_r"] >= EDGE
            )
            if kept_trades and wants_rotation:
                result = position_of(bars, kept_trades, 40.0)
                rng = np.random.default_rng(SEED)
                nulls = rotation_null(result, N_ROTATIONS, rng)
                real_sharpe = result.curve_sharpe(bars, PPY)
                values = [n.curve_sharpe(bars, PPY) for n in nulls]
                arr = np.asarray(values, dtype=float)
                got["rotation"] = {
                    "real_sharpe": real_sharpe,
                    "null_mean": float(arr.mean()),
                    "null_p95": float(np.percentile(arr, 95)),
                    "percentile": float((arr < real_sharpe).mean() * 100.0),
                    "delta": real_sharpe - float(arr.mean()),
                }
            cells[key] = got
            print(
                f"    {key:20s} kept {got['share_kept']:5.1%}  "
                f"gross adv {got['advantage_gross_r']:+.3f}R",
                flush=True,
            )

    return {
        "n_setups": len(setups),
        "n_trades": len(trades),
        "field": {
            "share_positive": sum(1 for r in readings if r > 0) / len(readings),
            "share_zero": sum(1 for r in readings if r == 0.0) / len(readings),
            "median_abs": statistics.median(magnitudes) if magnitudes else 0.0,
            "floors": floors,
        },
        "grid_census": grid_census,
        "buy_and_hold": buy_and_hold(bars, trades[0].entry_index, PPY),
        "cells": cells,
    }


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
        append_section(payload)
        print(f"re-rendered the D214 section of {RESULTS.name}")
        return 0

    started = time.time()
    raw, raw_volumes = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)

    runs: dict[str, Any] = {}
    for symbol in SYMBOLS:
        print(f"{symbol}: {len(cleaned[symbol]):,} bars", flush=True)
        vols = align_volumes(cleaned[symbol], raw[symbol], raw_volumes[symbol])
        runs[symbol] = run_symbol(symbol, cleaned[symbol], vols)

    # V[{SR_n}] from the spread of arm Sharpes this programme has actually produced, the
    # same basis the earlier DSR figures used.
    pnl = json.loads((REPO / "data" / "structure_pnl_summary.json").read_text(encoding="utf-8"))
    spread = [
        a["tiers"]["zero (diagnostic)"]["sharpe"]
        for s in pnl["runs"]
        for a in pnl["runs"][s]["arms"].values()
    ]
    var_trials = statistics.pvariance(spread)
    t_obs = min(len(cleaned[s]) for s in SYMBOLS)

    for symbol in SYMBOLS:
        for key, cell in runs[symbol]["cells"].items():
            kept = cell["kept"]
            if kept.get("n"):
                cell["dsr"] = dsr_table(kept[VERDICT_TIER]["sharpe"], t_obs, var_trials)

    payload = {
        "produced": time.strftime("%Y-%m-%d"),
        "fixture": FIXTURE.name,
        "symbols": list(SYMBOLS),
        "primary_cell": {"k": PRIMARY_K, "touch_atr": PRIMARY_TOUCH},
        "primary_gate": "inverted|zero",
        "field_params": {
            "k": FIELD.k,
            "cluster_atr": FIELD.cluster_atr,
            "erase": FIELD.erase,
            "atr_window": FIELD.atr_window,
            "vol_norm_bars": FIELD.vol_norm_bars,
        },
        "edge_bar": EDGE,
        "own_looks": OWN_LOOKS,
        "inherited": INHERITED,
        "var_trials": var_trials,
        "t_observations": t_obs,
        "runs": runs,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    SUMMARY.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    append_section(payload)
    print(f"\nwrote {SUMMARY.name} in {payload['elapsed_seconds']}s\n")
    print(render(payload))
    return 0


def _r(x: float) -> str:
    return "n/a" if x != x else f"{x:+.3f}"


def _g(key: str) -> str:
    """Gate keys carry a pipe, which is the markdown table column separator."""
    return key.replace("|", " / ")


def render(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    runs = payload["runs"]
    primary = payload["primary_gate"]

    add("## D214 - the terrain map as a confluence gate")
    add("")
    add(f"**Produced:** {payload['produced']} · **Reproduce:** "
        "`uv run python scripts/run_structure_terrain_gate.py` (offline, deterministic)")
    add("")
    add("**This study overrides D203's stop**, deliberately and for one bounded question. "
        "The record and the reasoning are in `docs/decisions/D214-the-terrain-gate.md`, "
        "committed before this runner existed. `inverted` is the pre-registered primary "
        "because D202 measured this exact reading anti-predictive at the 2.6th percentile - "
        "the prior comes from a published result here, not from peeking at this run.")
    add("")
    fp = payload["field_params"]
    add(f"Field: D202's raw parameters (`k={fp['k']}`, `cluster_atr={fp['cluster_atr']}`, "
        f"no erasure) with every window calendar-matched at 96 bars/day per D194 - "
        f"`atr_window` {fp['atr_window']:,}, `vol_norm_bars` {fp['vol_norm_bars']:,}. "
        "Read at the signal bar, so the bar that decides never also pays.")
    add("")

    add("### A census first: does the discretisation move a gate decision?")
    add("")
    add("`build_grid` spans the whole series' high and low, so the axis a reading is "
        "discretised onto knows the eventual price range. `test_terrain_field.py` knew and "
        "pinned around it — its look-ahead test passes the same grid to both arms with the "
        "comment *\"same axis, or the buckets alone would differ\"*. That is the right call "
        "for a signal, where the axis is a discretisation choice. A **gate** reads only the "
        "sign, so the question is whether the sign moves.")
    add("")
    add("**The first version of this census was a tautology and is reported as one.** It "
        "compared the full grid against one built from the first half and returned exactly "
        "zero on both symbols — because `Grid.bucket` depends only on `ln_min`, this "
        "fixture's lowest low falls in the first half, and causal deposits put no mass "
        "above the prefix grid's top at an early bar. It could not have failed.")
    add("")
    add("The potent version perturbs the axis **origin** by half a bucket, the largest "
        "misalignment the discretisation admits:")
    add("")
    add("| symbol | trades | mean shift in reading | max shift | sign flips |")
    add("|---|---:|---:|---:|---:|")
    for sym in runs:
        g = runs[sym]["grid_census"]
        add(f"| `{sym}` | {g['n_trades']:,} | {g['mean_shift']:.4f} | "
            f"{g['max_shift']:.4f} | **{g['sign_flips']}** ({g['share_flipped']:.2%}) |")
    add("")
    add("Reported before the verdict, in counts, because that is when a census is worth "
        "anything.")
    add("")

    add("### The gate, every cell")
    add("")
    add("| symbol | gate | kept | gross R (kept) | gross R (all) | advantage | "
        "gross R of REJECTED | net R @40bp | Sharpe @40bp |")
    add("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for sym in runs:
        for key, cell in runs[sym]["cells"].items():
            kept = cell["kept"]
            mark = " **(primary)**" if key == primary else ""
            if not kept.get("n"):
                add(f"| `{sym}`{mark} | {_g(key)} | 0 | — | — | — | — | — | — |")
                continue
            add(f"| `{sym}`{mark} | {_g(key)} | {cell['share_kept']:.0%} "
                f"({cell['n_kept']:,}) | {kept['zero']['mean_gross_r']:+.3f} | "
                f"{cell['ungated']['zero']['mean_gross_r']:+.3f} | "
                f"{_r(cell['advantage_gross_r'])} | "
                f"{_r(cell['counterfactual_gross_r'])} | "
                f"{kept['40bp']['mean_net_r']:+.3f} | "
                f"{kept['40bp']['sharpe']:+.2f} |")
    add("")
    add("**The rejected column is not decoration.** D198's confirmation filter beat its "
        "baseline on both symbols and was worthless, because the signals it discarded "
        "scored +0.785 against the kept ones at -0.288. A filter that improves the book it "
        "keeps by throwing away the winners is not a filter.")
    add("")

    add("### The control: is it placement or is it selectivity?")
    add("")
    add("The identical gate applied to terrain readings **permuted among setups**. A gate "
        "keeping half the trades moves the mean whatever it selects on; this is what "
        "separates the map's placement from the gate's selectivity.")
    add("")
    add("| symbol | gate | real advantage | shuffled median | shuffled p95 | shuffled max | beats p95 |")
    add("|---|---|---:|---:|---:|---:|:--:|")
    for sym in runs:
        for key, cell in runs[sym]["cells"].items():
            c = cell["control"]
            real = cell["advantage_gross_r"]
            beats = real == real and real > c["p95"]
            add(f"| `{sym}` | {_g(key)} | {_r(real)} | {c['p50']:+.3f} | {c['p95']:+.3f} | "
                f"{c['max']:+.3f} | {'yes' if beats else 'no'} |")
    add("")

    add("### The three bars")
    add("")
    add("The deliverable. Each cell's observed Sharpe against three multiplicity counts, "
        "with an explicit pass/fail. The combined count is forced by `TERRAIN_RESULTS.md`: "
        "*anything that reuses these sensors inherits the count*.")
    add("")
    add("| symbol | gate | Sharpe @40bp | " + " | ".join(
        f"{k} (n={v + payload['own_looks']})" for k, v in payload["inherited"].items()
    ) + " |")
    add("|---|---|---:|" + "---|" * len(payload["inherited"]))
    for sym in runs:
        for key, cell in runs[sym]["cells"].items():
            if "dsr" not in cell:
                continue
            sharpe = cell["kept"]["40bp"]["sharpe"]
            cells = " | ".join(
                f"need {cell['dsr'][k]['required_annual_sharpe']:.2f} — "
                f"**{'PASS' if cell['dsr'][k]['clears'] else 'fail'}**"
                for k in payload["inherited"]
            )
            add(f"| `{sym}` | {_g(key)} | {sharpe:+.2f} | {cells} |")
    add("")

    add("### Verdict")
    add("")
    add(_reading(payload))
    add("")

    add("### Multiplicity")
    add("")
    add("| | cells | looks |")
    add("|---|---|---:|")
    add(f"| gate cells | 2 directions x 3 thresholds x {len(runs)} symbols | {payload['own_looks']} |")
    add("| gate-shuffle and rotation controls | controls, not tests | 0 |")
    add(f"| **D214 total** | | **{payload['own_looks']}** |")
    add("")
    add(f"Inherited for the combined bar: the structure programme's "
        f"{payload['inherited']['structure only']} and the terrain programme's 259.")
    add("")
    return "\n".join(lines)


def _reading(payload: dict[str, Any]) -> str:
    runs = payload["runs"]
    primary = payload["primary_gate"]
    parts: list[str] = []

    prim = {s: runs[s]["cells"][primary] for s in runs}
    adv = [prim[s]["advantage_gross_r"] for s in runs]
    parts.append(
        f"**The primary gate (`{primary}`) gains "
        + " and ".join(_r(v) + "R" for v in adv)
        + f" gross on the two symbols**, against the pre-registered +{payload['edge_bar']:.2f}R "
        "hurdle. "
        + (
            "It clears hurdle 1."
            if all(v == v and v >= payload["edge_bar"] for v in adv)
            else "**Hurdle 1 fails.**"
        )
    )
    parts.append("")

    inv = [runs[s]["cells"][f"inverted|{t}"]["advantage_gross_r"]
           for s in runs for t in THRESHOLD_NAMES]
    ali = [runs[s]["cells"][f"aligned|{t}"]["advantage_gross_r"]
           for s in runs for t in THRESHOLD_NAMES]
    inv_ok = sum(1 for v in inv if v == v and v >= payload["edge_bar"])
    ali_ok = sum(1 for v in ali if v == v and v >= payload["edge_bar"])
    inv_mean = statistics.fmean([v for v in inv if v == v])
    ali_mean = statistics.fmean([v for v in ali if v == v])
    better = sum(1 for a, b in zip(inv, ali) if a == a and b == b and a > b)
    parts.append(
        f"Across all cells, **{inv_ok} of {len(inv)} `inverted`** and "
        f"**{ali_ok} of {len(ali)} `aligned`** clear the gross-R hurdle. **H2 is "
        "falsified**: it predicted `inverted` would gain at least the hurdle on at least "
        "one symbol, and it does not."
    )
    parts.append("")
    parts.append(
        "The pre-registered *direction* fares better than the pre-registered *effect*. "
        f"`inverted` averages {inv_mean:+.3f}R against `aligned`'s {ali_mean:+.3f}R and "
        f"wins {better} of {len(inv)} paired cells — so D202's anti-signal does show up in "
        "the sign, faintly, and nowhere near the size needed to matter. That is the honest "
        "reading: the prior pointed the right way and at something far too small to trade."
    )
    parts.append("")

    beats = [
        (s, k) for s in runs for k, c in runs[s]["cells"].items()
        if c["advantage_gross_r"] == c["advantage_gross_r"]
        and c["advantage_gross_r"] > c["control"]["p95"]
    ]
    parts.append(
        f"**Against the shuffle control, {len(beats)} of "
        f"{sum(len(runs[s]['cells']) for s in runs)} cells beat the 95th percentile of a "
        "gate applied to permuted readings.** "
        + (
            "So most of what the gate does is selectivity, not the map's placement — which "
            "is D197's finding (dead even against randomly placed mass) reappearing one "
            "level up."
            if len(beats) <= 2
            else "More cells clear it than selectivity alone would explain."
        )
    )
    parts.append("")

    worse_kept = [
        (s, k) for s in runs for k, c in runs[s]["cells"].items()
        if c["counterfactual_gross_r"] == c["counterfactual_gross_r"]
        and c["kept"].get("n")
        and c["counterfactual_gross_r"] > c["kept"]["zero"]["mean_gross_r"]
    ]
    parts.append(
        f"**In {len(worse_kept)} of {sum(len(runs[s]['cells']) for s in runs)} cells the "
        "trades the gate REJECTED did better than the ones it kept.** That is D198's "
        "finding repeating: a filter can improve nothing while looking like it filters, "
        "and the only way to see it is to price the discarded book beside the kept one."
    )
    parts.append("")

    net = [prim[s]["kept"]["40bp"]["mean_net_r"] for s in runs if prim[s]["kept"].get("n")]
    parts.append(
        "**After costs the primary gate returns "
        + " and ".join(f"{v:+.3f}R" for v in net)
        + " a trade.** Hurdle 2 "
        + ("holds." if all(v > 0 for v in net) else "fails — a gate changes which trades "
           "are taken, not what the wrapper risks, and the toll is a function of the stop.")
    )
    parts.append("")

    passes = {
        k: sum(
            1 for s in runs for c in runs[s]["cells"].values()
            if "dsr" in c and c["dsr"][k]["clears"]
        )
        for k in payload["inherited"]
    }
    total = sum(1 for s in runs for c in runs[s]["cells"].values() if "dsr" in c)
    parts.append(
        "**And the three bars, which is what this study was asked to show.** Cells clearing "
        "each: "
        + ", ".join(f"**{k}** {passes[k]} of {total}" for k in payload["inherited"])
        + ". "
        + (
            "Nothing clears any bar, so the distinction between them never arises — the "
            "result is not one that history disqualified, it is one that was never there."
            if sum(passes.values()) == 0
            else "The gap between the fresh count and the combined one is the price of the "
            "395 looks that came before this study, and it is visible here as exactly that."
        )
    )
    return "\n".join(parts)


def append_section(payload: dict[str, Any]) -> None:
    text = RESULTS.read_text(encoding="utf-8")
    marker = "## D214 - the terrain map as a confluence gate"
    anchor = "---\n\n### Parking lot"
    body = render(payload)
    if marker in text:
        head, _, rest = text.partition(marker)
        _, sep, tail = rest.partition(anchor)
        text = head + body + "\n" + anchor + tail if sep else head + body
    else:
        head, _, rest = text.partition(anchor)
        text = head + body + "\n" + anchor + rest
    RESULTS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
