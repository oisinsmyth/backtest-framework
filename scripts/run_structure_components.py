"""WP3 — each component alone, against its own matched placebo. No costs (D204).

    uv run python scripts/run_structure_components.py
    uv run python scripts/run_structure_components.py --report-only

Five arms, five different questions, and only the C3 ladder needs no random draws at all.

- **C1** the change of character — the base book against `rotation_null`, which preserves
  exposure, autocorrelation and net tilt exactly and isolates *when* from *how much*.
- **C2** the flipped level — against levels drawn uniformly over the same impulse leg.
- **C3** the 61.8% retracement — against `structure.PLACEBO_RATIOS` on the same legs. **The
  cheapest decisive test in the programme:** any level partway into a retracement sits
  where price has recently been, so a reaction at 0.618 alone establishes nothing, and a
  reaction 0.447 does not share establishes something.
- **C4** the fair value gap — against a band of the same width displaced within the leg.
- **C5** RSI — against a random bar of the same window.

**No costs anywhere in this file.** WP3 asks whether the components carry information;
whether that information survives 40 bps is WP5's question, and WP2 already showed the toll
is 0.4-1.0R. Mixing the two would let a real signal be reported as absent because it is
expensive, which D202's zero-cost diagnostic exists to prevent.

A component failing here is **not dropped**. It can be individually null and still
marginally useful, which is WP4's question. What this pass does is put the failure on the
record before WP4 runs, so a later "it works in combination" has to survive having been
predicted against.
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
from backtest_framework.research.structure import (  # noqa: E402
    CANONICAL_RATIOS,
    PLACEBO_RATIOS,
    fair_value_gaps,
    market_structure,
)
from backtest_framework.research.structure_nulls import (  # noqa: E402
    CONTINUATION,
    DEFAULT_SIMS,
    DepthTable,
    Reaction,
    depth_of,
    displaced_gap_levels,
    first_gap_in_leg,
    leg_span_levels,
    paired_bootstrap,
    ratio_levels,
    reaction_at,
    touch_and_continue,
    continue_from,
)
from backtest_framework.research.structure_setups import (  # noqa: E402
    ATR_WINDOW_15M,
    GOLDEN_RATIO,
    find_setups,
)
from backtest_framework.research.breakout_nulls import summarise_null  # noqa: E402
from backtest_framework.research.terrain import rolling_mean_true_range  # noqa: E402
from backtest_framework.research.terrain_field_nulls import rotation_null  # noqa: E402
from backtest_framework.research.terrain_nulls import HORIZON  # noqa: E402
from backtest_framework.research.terrain_strategies import PositionResult  # noqa: E402

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "structure_components_summary.json"
RESULTS = REPO / "docs" / "results" / "STRUCTURE_RESULTS.md"

SYMBOLS = ("BTCUSDT", "ETHUSDT")
PRIMARY_K, PRIMARY_TOUCH = 2, 0.5
N_SIMS, SEED = DEFAULT_SIMS, 0
PPY = 96.0 * 365.0
"""15m bars: 96 a day, 365 days. Crypto does not close."""

EFFECT_FLOOR = 0.10
"""`STRUCTURE_MODEL.md`'s hurdle, in Sharpe for C1. For the touch statistics the delta is
a probability and the floor does not apply — the percentile carries the verdict there, and
is reported beside every delta either way (D202's lesson 5)."""


def bar_returns(bars: Sequence[Any]) -> tuple[float, ...]:
    closes = [b.bar.close for b in bars]
    return tuple(
        [0.0]
        + [
            math.log(b / a) if a > 0.0 and b > 0.0 else 0.0
            for a, b in zip(closes, closes[1:])
        ]
    )


def choch_position(bars: Sequence[Any], setups: Sequence[Any]) -> PositionResult:
    """C1's book: hold the change of character's direction for `HORIZON` bars.

    Entered at the bar the impulse leg confirms and held from the NEXT bar — D197-D201's
    convention, so the close that decides never also pays. Overlapping setups overwrite,
    which is what a trader following the newest structure would do.

    Zero cost. This is a question about information, not about whether it is affordable."""
    position = [0.0] * len(bars)
    for setup in setups:
        start = setup.ready_index + 1
        for t in range(start, min(start + HORIZON, len(bars))):
            position[t] = float(setup.direction)
    return PositionResult(tuple(position), bar_returns(bars), 0.0, PPY)


def run_c1(bars: Sequence[Any], setups: Sequence[Any]) -> dict[str, Any]:
    real = choch_position(bars, setups)
    rng = np.random.default_rng(SEED)
    nulls = rotation_null(real, N_SIMS, rng)
    real_sharpe = real.curve_sharpe(bars, PPY)
    values = [n.curve_sharpe(bars, PPY) for n in nulls]
    spec = CONTINUATION.__class__("sharpe", "high", "Sharpe (ann.)", "at least the real Sharpe")
    dist = summarise_null(values, real_sharpe, spec)
    return {
        "real_sharpe": real_sharpe,
        "net_exposure": real.net_exposure,
        "share_long": real.share_long,
        "bars_held": sum(1 for p in real.position if p != 0.0),
        "null": dist.to_dict(),
        "delta_vs_null_mean": real_sharpe - dist.null_mean,
        "clears_floor": (real_sharpe - dist.null_mean) >= EFFECT_FLOOR,
        "beats_p95": real_sharpe > dist.null_p95,
    }


def arm_outcomes(
    closes: Sequence[float],
    atr: Sequence[float],
    setups: Sequence[Any],
    levels: Sequence[float],
    touch: float,
) -> tuple[list[bool], list[bool]]:
    touched: list[bool] = []
    continued: list[bool] = []
    for setup, level in zip(setups, levels):
        hit, went_on = touch_and_continue(closes, atr, setup, level, touch)
        touched.append(hit)
        continued.append(went_on)
    return touched, continued


def run_touch_arm(
    closes: Sequence[float],
    atr: Sequence[float],
    setups: Sequence[Any],
    real_levels: Sequence[float],
    factory: Any,
    touch: float,
) -> dict[str, Any]:
    """One real arm against `N_SIMS` placebo arms, paired setup by setup — and then
    against a DEPTH-MATCHED placebo, which is the comparison that actually decides it.

    The C3 ladder came back a strictly monotone staircase in retracement depth. That makes
    depth a nuisance variable running through every other arm: a level sitting deep on the
    leg beats a uniformly-drawn placebo whether or not it means anything. So the unmatched
    percentile is reported and is NOT the verdict."""
    real_touched, real_continued = arm_outcomes(closes, atr, setups, real_levels, touch)
    real = Reaction(len(setups), sum(real_touched), sum(real_continued))
    real_depths = [
        depth_of(s, level)
        for s, level, hit in zip(setups, real_levels, real_touched)
        if hit
    ]

    rng = np.random.default_rng(SEED)
    values: list[float] = []
    table = DepthTable.empty()
    placebo_depths: list[float] = []
    for draw in range(N_SIMS):
        levels = factory(rng)
        touched, continued = arm_outcomes(closes, atr, setups, levels, touch)
        values.append(Reaction(len(setups), sum(touched), sum(continued)).p_continuation)
        for setup, level, hit, went_on in zip(setups, levels, touched, continued):
            if not hit:
                continue
            depth = depth_of(setup, level)
            table.add(depth, went_on)
            if draw == 0:
                placebo_depths.append(depth)

    dist = summarise_null(values, real.p_continuation, CONTINUATION)
    matched_rate, matched_n = table.expected_for(real_depths)
    return {
        "real": real.to_dict(),
        "null": dist.to_dict(),
        "delta_vs_null_mean": real.p_continuation - dist.null_mean,
        "beats_p95": real.p_continuation > dist.null_p95,
        "depth": {
            "real_median": _median_or_nan(real_depths),
            "placebo_median": _median_or_nan(placebo_depths),
            "matched_expected_rate": matched_rate,
            "matched_touches_covered": matched_n,
            "matched_touches_total": len(real_depths),
            "delta_vs_depth_matched": real.p_continuation - matched_rate,
        },
    }


def _median_or_nan(values: Sequence[float]) -> float:
    finite = [v for v in values if math.isfinite(v)]
    return statistics.median(finite) if finite else math.nan


def run_c3_ladder(
    closes: Sequence[float],
    atr: Sequence[float],
    setups: Sequence[Any],
    touch: float,
) -> dict[str, Any]:
    """Every ratio on the same legs — the paired placebo that needs no draws.

    The golden ratio is compared against each non-canonical ratio by a paired bootstrap
    over SETUPS: one index vector applied to both arms, because the arms share the setups
    and resampling them independently would manufacture a difference."""
    ladder: dict[str, Any] = {}
    outcomes: dict[float, tuple[list[bool], list[bool]]] = {}
    for ratio in sorted(set(CANONICAL_RATIOS) | set(PLACEBO_RATIOS)):
        levels = ratio_levels(setups, ratio)
        touched, continued = arm_outcomes(closes, atr, setups, levels, touch)
        outcomes[ratio] = (touched, continued)
        reaction = Reaction(len(setups), sum(touched), sum(continued))
        ladder[f"{ratio:.3f}"] = {
            "ratio": ratio,
            "canonical": ratio in CANONICAL_RATIOS,
            "golden": ratio == GOLDEN_RATIO,
            **reaction.to_dict(),
        }

    golden_touched, golden_continued = outcomes[GOLDEN_RATIO]
    comparisons: dict[str, Any] = {}
    for ratio in PLACEBO_RATIOS:
        touched, continued = outcomes[ratio]
        comparisons[f"{ratio:.3f}"] = paired_bootstrap(
            golden_continued, continued, golden_touched, touched, N_SIMS, SEED
        )

    rates = [(v["p_continuation"], v["ratio"]) for v in ladder.values()]
    rates.sort(reverse=True)
    rank = next(i for i, (_, r) in enumerate(rates, start=1) if r == GOLDEN_RATIO)
    placebo_rates = [ladder[f"{r:.3f}"]["p_continuation"] for r in PLACEBO_RATIOS]
    return {
        "ladder": ladder,
        "vs_placebo": comparisons,
        "golden_rank_of_8": rank,
        "golden_rate": ladder[f"{GOLDEN_RATIO:.3f}"]["p_continuation"],
        "placebo_mean_rate": statistics.fmean(placebo_rates),
        "spread_across_all_eight": max(v for v, _ in rates) - min(v for v, _ in rates),
    }


def run_symbol(symbol: str, bars: Sequence[Any]) -> dict[str, Any]:
    closes = [b.bar.close for b in bars]
    atr = rolling_mean_true_range(bars, ATR_WINDOW_15M)
    states = market_structure(bars, PRIMARY_K)
    population = find_setups(bars, PRIMARY_K, PRIMARY_TOUCH, states=states)
    setups = list(population.setups)
    gaps = fair_value_gaps(bars)

    print(f"  C1 rotation null over {len(setups):,} setups", flush=True)
    c1 = run_c1(bars, setups)

    print("  C2 flipped level vs levels drawn on the same leg", flush=True)
    c2 = run_touch_arm(
        closes, atr, setups, [_level_of(s, states) for s in setups],
        lambda rng: leg_span_levels(setups, rng), PRIMARY_TOUCH,
    )

    print("  C3 the ratio ladder — 8 ratios, no draws", flush=True)
    c3 = run_c3_ladder(closes, atr, setups, PRIMARY_TOUCH)

    print("  C4 gap midpoint vs a displaced band of the same width", flush=True)
    midpoints, widths = zip(*(first_gap_in_leg(s, gaps) for s in setups))
    real_gap_levels = [m if m is not None else math.nan for m in midpoints]
    c4 = run_touch_arm(
        closes, atr, setups, real_gap_levels,
        lambda rng: displaced_gap_levels(setups, midpoints, widths, rng),
        PRIMARY_TOUCH,
    )
    c4["n_setups_with_a_gap"] = sum(1 for m in midpoints if m is not None)

    print("  C5 RSI bar vs a random bar of the same window", flush=True)
    c5 = run_c5(closes, atr, setups, PRIMARY_TOUCH)

    return {
        "n_bars": len(bars),
        "n_setups": len(setups),
        "C1": c1,
        "C2": c2,
        "C3": c3,
        "C4": c4,
        "C5": c5,
    }


def _level_of(setup: Any, states: Sequence[Any]) -> float:
    level = states[setup.choch_index].choch_level
    return float(level) if level is not None else math.nan


def _rsi_trigger_bar(setup: Any) -> int | None:
    """The first bar in the window where the RSI condition held, or None."""
    for index, held in zip(setup.window, setup.holds):
        if "C5" in held:
            return index
    return None


def run_c5(
    closes: Sequence[float], atr: Sequence[float], setups: Sequence[Any], touch: float
) -> dict[str, Any]:
    """C5 fires at a BAR, not at a price, so it uses `continue_from` and its placebo is a
    random bar of the same window.

    Routing it through the level statistic would search each window for the first bar near
    the trigger's close, which can land on an earlier bar at a similar price and quietly
    measure a different moment. The resolution rule is identical either way, so the arms
    stay comparable with the rest of the table."""
    triggers = [_rsi_trigger_bar(s) for s in setups]
    live = [(s, t) for s, t in zip(setups, triggers) if t is not None]
    real_continued = sum(
        continue_from(closes, atr, t, s.direction, touch) for s, t in live
    )
    real = Reaction(len(setups), len(live), real_continued)

    real_depths = [depth_of(s, closes[t]) for s, t in live]

    rng = np.random.default_rng(SEED)
    values: list[float] = []
    table = DepthTable.empty()
    placebo_depths: list[float] = []
    for draw in range(N_SIMS):
        drawn = 0
        for setup, _trigger in live:
            index = setup.window[int(rng.integers(0, len(setup.window)))]
            went_on = continue_from(closes, atr, index, setup.direction, touch)
            drawn += went_on
            depth = depth_of(setup, closes[index])
            table.add(depth, went_on)
            if draw == 0:
                placebo_depths.append(depth)
        values.append(drawn / len(live) if live else 0.0)
    dist = summarise_null(values, real.p_continuation, CONTINUATION)
    matched_rate, matched_n = table.expected_for(real_depths)
    return {
        "real": real.to_dict(),
        "null": dist.to_dict(),
        "delta_vs_null_mean": real.p_continuation - dist.null_mean,
        "beats_p95": real.p_continuation > dist.null_p95,
        "n_setups_with_a_trigger": len(live),
        "depth": {
            "real_median": _median_or_nan(real_depths),
            "placebo_median": _median_or_nan(placebo_depths),
            "matched_expected_rate": matched_rate,
            "matched_touches_covered": matched_n,
            "matched_touches_total": len(real_depths),
            "delta_vs_depth_matched": real.p_continuation - matched_rate,
        },
    }


def _pct(value: float) -> str:
    return f"{value:.1%}"


def _reading(payload: dict[str, Any]) -> str:
    """Generated from the payload so the prose and the artifact cannot drift (D176/D183/D186)."""
    runs = payload["runs"]
    parts: list[str] = []

    c1 = {s: runs[s]["C1"] for s in runs}
    parts.append(
        "**C1 — the change of character.** "
        + " and ".join(
            f"`{s}` Sharpe {c1[s]['real_sharpe']:+.3f} against a rotation null mean of "
            f"{c1[s]['null']['null_mean']:+.3f}, at the {c1[s]['null']['percentile']:.1f}th "
            f"percentile (delta {c1[s]['delta_vs_null_mean']:+.3f})"
            for s in runs
        )
        + ". The book runs at "
        + " and ".join(f"{c1[s]['net_exposure']:+.4f}" for s in runs)
        + " net exposure, so this is a timing reading and not a disguised long — the "
        "confound that made D201's best cells one multi-year long is absent here by "
        "construction.\n"
    )

    for key, name, extra in (
        ("C2", "the flipped level", "levels drawn uniformly over the same impulse leg"),
        ("C4", "the fair value gap", "a band of the same width displaced within the leg"),
        ("C5", "RSI", "a random bar of the same window"),
    ):
        arm = {s: runs[s][key] for s in runs}
        parts.append(
            f"**{key} — {name}**, against {extra}. "
            + " and ".join(
                f"`{s}` {_pct(arm[s]['real']['p_continuation'])} on "
                f"{arm[s]['real']['n_touches']:,} touches against a null mean of "
                f"{_pct(arm[s]['null']['null_mean'])}, at the "
                f"{arm[s]['null']['percentile']:.1f}th percentile "
                f"(delta {arm[s]['delta_vs_null_mean']:+.4f})"
                for s in runs
            )
            + ".\n"
        )

    parts.append(
        "**And now the same three arms at matched depth, which is the verdict.** "
        + " and ".join(
            f"`{sym}` C4 falls from {runs[sym]['C4']['delta_vs_null_mean']:+.4f} against a "
            f"uniform placebo to {runs[sym]['C4']['depth']['delta_vs_depth_matched']:+.4f} "
            f"against one at the same depth"
            for sym in runs
        )
        + ". The real gaps sit at retracement "
        + " and ".join(f"{runs[sym]['C4']['depth']['real_median']:.3f}" for sym in runs)
        + " while the uniform placebo sits at "
        + " and ".join(f"{runs[sym]['C4']['depth']['placebo_median']:.3f}" for sym in runs)
        + " — so **the fair value gap's entire apparent edge was that it sits deeper on "
        "the leg.** C2 is negative either way. C5 is the only arm that survives matching, "
        "at "
        + " and ".join(
            f"{runs[sym]['C5']['depth']['delta_vs_depth_matched']:+.4f}" for sym in runs
        )
        + " on "
        + " and ".join(
            f"{runs[sym]['C5']['depth']['matched_touches_covered']:,}" for sym in runs
        )
        + " covered touches — a small sample, and the one component in the study that was "
        "put there as a control."
    )

    c3 = {s: runs[s]["C3"] for s in runs}
    parts.append(
        "**C3 — the golden ratio, against seven other numbers on the same legs.** "
        + " and ".join(
            f"0.618 ranks **{c3[s]['golden_rank_of_8']} of 8** on `{s}` "
            f"({_pct(c3[s]['golden_rate'])} against a placebo mean of "
            f"{_pct(c3[s]['placebo_mean_rate'])})"
            for s in runs
        )
        + ". The spread across all eight ratios is "
        + " and ".join(f"{c3[s]['spread_across_all_eight']:.4f}" for s in runs)
        + ", against a golden-minus-placebo gap of "
        + " and ".join(
            f"{c3[s]['golden_rate'] - c3[s]['placebo_mean_rate']:+.4f}" for s in runs
        )
        + " — so the variation *between arbitrary ratios* is larger than the advantage "
        "the golden one is supposed to have over them.\n"
    )
    return "\n".join(parts)


def render(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    runs = payload["runs"]

    add("## WP3 — each component alone, against its own matched placebo\n")
    add(f"**Produced:** {payload['produced']} · **Reproduce:** "
        "`uv run python scripts/run_structure_components.py` (offline, deterministic, "
        f"seed {payload['seed']})\n")
    add(f"Primary cell only: `k={payload['primary']['k']}`, touch band "
        f"{payload['primary']['touch_atr']} ATR, {payload['n_sims']} draws. "
        "**No costs anywhere in this section** — WP3 asks whether the components carry "
        "information, and WP2 already priced the toll at 0.4-1.0R. Mixing the two would let "
        "a real signal be reported as absent because it is expensive, which D202's "
        "zero-cost diagnostic exists to prevent.\n")

    add("### The statistic, restated\n")
    add("**Touch**: the first bar of a setup's pullback window inside `k x ATR` of the "
        "level whose predecessor was outside. **Band fixed at the touch** and not revisited. "
        "**Continuation**: within 5 bars the close moves a band beyond the level *in the "
        "change of character's direction* without first moving a band beyond it against. "
        "Unresolved counts as not continued, identically in both arms.\n")
    add("This is `terrain_nulls`' reversal definition with one change: the direction comes "
        "from the setup rather than from the approach side. That is not cosmetic — a "
        "reversal statistic is agnostic about which way price then goes, and this one is "
        "not, because the strategy is not.\n")

    add("### C1 — the change of character, against a rotation null\n")
    add("| symbol | real Sharpe | null mean | null p95 | percentile | delta | net exposure | clears +0.10 |")
    add("|---|---:|---:|---:|---:|---:|---:|:--:|")
    for s in runs:
        c = runs[s]["C1"]
        add(f"| `{s}` | {c['real_sharpe']:+.3f} | {c['null']['null_mean']:+.3f} | "
            f"{c['null']['null_p95']:+.3f} | {c['null']['percentile']:.1f}th | "
            f"{c['delta_vs_null_mean']:+.3f} | {c['net_exposure']:+.4f} | "
            f"{'yes' if c['clears_floor'] else 'no'} |")
    add("")
    add("Rotation preserves the exposure distribution, the autocorrelation, the turnover "
        "and the net tilt exactly, and destroys only the alignment with price. It asks "
        "*did the exposure change at the right moments* — the one question D201 could not "
        "answer about itself.\n")

    add("### C2, C4, C5 — touch statistics against matched placebos\n")
    add("| symbol | arm | placebo | touches | P(cont) real | null mean | null p95 | percentile | delta | beats p95 |")
    add("|---|---|---|---:|---:|---:|---:|---:|---:|:--:|")
    for s in runs:
        for key, placebo in (
            ("C2", "level drawn on the same leg"),
            ("C4", "same-width band, displaced"),
            ("C5", "random bar of the window"),
        ):
            a = runs[s][key]
            add(f"| `{s}` | {key} | {placebo} | {a['real']['n_touches']:,} | "
                f"{_pct(a['real']['p_continuation'])} | {_pct(a['null']['null_mean'])} | "
                f"{_pct(a['null']['null_p95'])} | {a['null']['percentile']:.1f}th | "
                f"{a['delta_vs_null_mean']:+.4f} | "
                f"{'yes' if a['beats_p95'] else 'no'} |")
    add("")
    add("Every delta is printed with its percentile beside it. D202's lesson 5 is the "
        "reason: a delta over a *wide* null's mean cleared that programme's +0.10 floor at "
        "the 67th percentile, and a floor without a percentile is not a hurdle.\n")

    add("#### The same three arms, depth-matched - and this is the verdict")
    add("")
    add("The C3 ladder below came back a **strictly monotone staircase in retracement "
        "depth**. That makes depth a nuisance variable running through every other arm: a "
        "level sitting deep on its leg beats a uniformly-drawn placebo whether or not it "
        "means anything, and a shallow one loses to it. So the table above is not the "
        "verdict. This one is - *does the real arm beat a placebo at the SAME depth?*")
    add("")
    add("| symbol | arm | real depth | placebo depth | P(cont) real | depth-matched expectation | delta | touches covered |")
    add("|---|---|---:|---:|---:|---:|---:|---:|")
    for sym in runs:
        for key in ("C2", "C4", "C5"):
            a = runs[sym][key]
            d = a["depth"]
            add(f"| `{sym}` | {key} | {d['real_median']:.3f} | {d['placebo_median']:.3f} | "
                f"{_pct(a['real']['p_continuation'])} | {_pct(d['matched_expected_rate'])} | "
                f"{d['delta_vs_depth_matched']:+.4f} | "
                f"{d['matched_touches_covered']:,}/{d['matched_touches_total']:,} |")
    add("")
    add("Real touches landing in a depth bin the placebo never reached are excluded and "
        "counted, never imputed from a neighbouring bin - an unpopulated bin means the "
        "comparison has nothing to say there, and filling it in would invent the answer at "
        "exactly the depths where the real arm is unusual.")
    add("")
    add("### C3 — the golden ratio against seven other numbers\n")
    add("The same setups, the same legs, a different number. No draws are needed because "
        "the placebo ratios ARE the null, and D189's H2 confound — levels sitting where "
        "price has recently been — cancels exactly, since every ratio is a point on the "
        "same leg.\n")
    for s in runs:
        add(f"**`{s}`**\n")
        add("| ratio | kind | touches | P(continuation) |")
        add("|---:|---|---:|---:|")
        for key in sorted(runs[s]["C3"]["ladder"], key=float):
            row = runs[s]["C3"]["ladder"][key]
            kind = "**golden**" if row["golden"] else ("canonical" if row["canonical"] else "placebo")
            add(f"| {row['ratio']:.3f} | {kind} | {row['n_touches']:,} | "
                f"{_pct(row['p_continuation'])} |")
        add("")
    add("Paired bootstrap of 0.618 minus each placebo ratio, one resampled index vector "
        "applied to both arms:\n")
    add("| symbol | vs ratio | mean difference | 5th-95th | share of draws NOT better |")
    add("|---|---:|---:|---|---:|")
    for s in runs:
        for key, b in runs[s]["C3"]["vs_placebo"].items():
            add(f"| `{s}` | {key} | {b['mean_difference']:+.4f} | "
                f"[{b['p05']:+.4f}, {b['p95']:+.4f}] | {b['share_not_better']:.1%} |")
    add("")

    add("### What the arms say\n")
    add(_reading(payload))

    add("\n### Multiplicity\n")
    add("| arm | cells | looks |")
    add("|---|---|---:|")
    add("| C1 rotation null | 2 symbols | 2 |")
    add("| C2 flipped level | 2 symbols | 2 |")
    add("| C3 ratio ladder | 8 ratios x 2 symbols | 16 |")
    add("| C4 fair value gap | 2 symbols | 2 |")
    add("| C5 RSI | 2 symbols | 2 |")
    add("| depth-matched re-reading (POST-HOC) | 3 arms x 2 symbols | 6 |")
    add("| **WP3 total** | | **30** |")
    add("")
    add("**The depth-matched comparison was NOT pre-registered.** It was designed after "
        "the C3 ladder came back a monotone staircase, which is post-hoc by any honest "
        "accounting, and it is counted as six further looks rather than folded into the "
        "arms it re-reads. Two things make it disclosable rather than disqualifying: it "
        "makes every verdict HARSHER, not kinder — C4 goes from a clean pass to nothing — "
        "and the confound it controls for was named in `structure_nulls.py`'s docstring "
        "before any run, as D189's H2. What was not anticipated is that the confound would "
        "turn out to explain the whole result.")
    add("")
    add("The `k` and touch-band grid is NOT run here. WP3 reports the pre-registered "
        "primary cell only; the grid belongs to WP6's discretion audit, where the spread "
        "across parameterisations is the question rather than a sensitivity footnote. "
        "Running it twice would double the count for one answer.\n")
    return "\n".join(lines)


def append_section(payload: dict[str, Any]) -> None:
    text = RESULTS.read_text(encoding="utf-8")
    marker = "## WP3 — each component alone, against its own matched placebo"
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


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
        append_section(payload)
        print(f"re-rendered the WP3 section of {RESULTS.name} from {SUMMARY.name}")
        return 0

    started = time.time()
    raw, _ = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)
    runs: dict[str, Any] = {}
    for symbol in SYMBOLS:
        print(f"{symbol}: {len(cleaned[symbol]):,} bars", flush=True)
        runs[symbol] = run_symbol(symbol, cleaned[symbol])

    payload = {
        "produced": time.strftime("%Y-%m-%d"),
        "fixture": FIXTURE.name,
        "symbols": list(SYMBOLS),
        "primary": {"k": PRIMARY_K, "touch_atr": PRIMARY_TOUCH},
        "n_sims": N_SIMS,
        "seed": SEED,
        "horizon": HORIZON,
        "periods_per_year": PPY,
        "effect_floor": EFFECT_FLOOR,
        "runs": runs,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    SUMMARY.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    append_section(payload)
    print(f"\nwrote {SUMMARY.name} and the WP3 section in {payload['elapsed_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
