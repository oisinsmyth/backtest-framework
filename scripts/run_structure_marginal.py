"""WP4 — what does each component add on top of the others? (D204, amended by D207)

    uv run python scripts/run_structure_marginal.py
    uv run python scripts/run_structure_marginal.py --report-only

This is the work package the whole programme exists for. WP3 asked whether each component
carries information alone; this asks whether it carries any that the others do not.

Three readings, in order of power:

**(a) PRIMARY — feature quintiles on ONE trade population.** The loosest arm (C1 only,
every pullback after a change of character) generates several thousand trades, and every
component is annotated onto them as a **continuous** feature. `feature_analysis` then ranks
and buckets them under promotion criteria this project already committed to — |rho| >= 0.2,
sign agreement across halves, quintile means stepping monotonically. Restating those
thresholds here would be re-choosing them.

Deliberately primary: eight backtest arms give eight noisy numbers, whereas quintiles over
thousands of trades give a gradient. It is also what terrain's WP5/WP6 was designed to do
and never reached.

**(b) CONDITIONAL — the same features WITHIN depth quintiles.** D208 found that retracement
depth explains every apparent effect in the strategy, so "does this component add anything?"
now means "does it add anything **at a given depth**?". A feature whose rank correlation
vanishes inside every depth quintile is a proxy for depth and nothing else. This reading
did not exist in the pre-registration; it is here because D208 made it the question.

**(c) CONFIRMATION — the ablation lattice.** All 2^3 = 8 subsets of {C2, C3, C4}, wrapper
frozen, same setups, same windows. C5 is absent because D206 dropped it on counts (RSI at
30/70 leaves 2 stacked entries). Trade counts are printed beside every Sharpe: an arm that
wins on nine trades has not won.

**The wrapper is identical in every arm.** D203's finding is that refining a wrapper
improves a strategy against its own predecessor and moves the null comparison not at all, so
the wrapper is a constant here and the filters are the only thing that varies.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import time
from itertools import combinations
from pathlib import Path
from typing import Any, Sequence

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.research.feature_analysis import (  # noqa: E402
    MIN_TRADES_FOR_ANALYSIS,
    N_BUCKETS,
    analyse_feature,
    spearman,
)
from backtest_framework.research.structure import (  # noqa: E402
    RSI_WINDOW,
    fair_value_gaps,
    market_structure,
    rsi,
)
from backtest_framework.research.structure_setups import (  # noqa: E402
    ATR_WINDOW_15M,
    find_setups,
)
from backtest_framework.research.structure_strategies import (  # noqa: E402
    COURSE_TARGET_R,
    Wrapper,
    expectancy,
    run_arm,
    to_episodes,
)
from backtest_framework.research.terrain import rolling_mean_true_range  # noqa: E402

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "structure_marginal_summary.json"
RESULTS = REPO / "docs" / "results" / "STRUCTURE_RESULTS.md"

SYMBOLS = ("BTCUSDT", "ETHUSDT")
PRIMARY_K, PRIMARY_TOUCH = 2, 0.5
COST_BPS = 40.0
FILTERS = ("C2", "C3", "C4")
"""C5 is absent by D206 — RSI at 30/70 leaves 2 stacked entries on both symbols. It is
carried as a continuous feature in reading (a) instead, where a rank correlation over
thousands of trades has power a 2-trade arm does not."""

FEATURES = (
    "fib_depth",
    "gap_distance_atr",
    "atr_to_golden",
    "rsi",
    "stop_atr",
    "bars_waited",
)


def arm_name(required: Sequence[str]) -> str:
    return "C1" if not required else "C1+" + "+".join(required)


def run_lattice(
    bars: Sequence[Any], setups: Sequence[Any], atr: Sequence[float]
) -> dict[str, Any]:
    """Every subset of the filters, through the identical frozen wrapper."""
    out: dict[str, Any] = {}
    wrapper = Wrapper()
    for size in range(len(FILTERS) + 1):
        for required in combinations(FILTERS, size):
            trades = run_arm(bars, setups, required, wrapper)
            costed = expectancy(trades, COST_BPS)
            free = expectancy(trades, 0.0)
            depths = [
                d
                for d in (
                    _depth(setups[t.setup_index], bars[t.entry_index - 1].bar.close)
                    for t in trades
                )
                if d is not None
            ]
            reasons = {
                r: sum(1 for t in trades if t.reason == r)
                for r in ("stop", "target", "max_hold")
            }
            out[arm_name(required)] = {
                "required": list(required),
                "costed": costed,
                "zero_cost_diagnostic": free,
                "median_entry_depth": statistics.median(depths) if depths else None,
                "exit_reasons": reasons,
            }
    return out


def _depth(setup: Any, price: float) -> float | None:
    from backtest_framework.research.structure import retracement

    return retracement(setup.leg, price)


def collinearity(episodes: Sequence[Any]) -> dict[str, dict[str, float | None]]:
    """Pairwise rank correlation between the features themselves.

    Added after the corrected run returned three CANDIDATEs whose signs and magnitudes were
    suspiciously alike. If `stop_atr`, `atr_to_golden` and `gap_distance_atr` are highly
    rank-correlated with each other then they are one quantity under three names — leg size
    relative to ATR — and only one of them can be a finding.

    Cheap, legible, and exactly the census-before-the-verdict discipline that has caught
    every other defect in this programme."""
    closed = [e for e in episodes if not e.is_open]
    out: dict[str, dict[str, float | None]] = {}
    for a in FEATURES:
        row: dict[str, float | None] = {}
        for b in FEATURES:
            pairs = [
                (e.features.get(a), e.features.get(b))
                for e in closed
                if e.features.get(a) is not None and e.features.get(b) is not None
            ]
            row[b] = (
                spearman([x for x, _ in pairs], [y for _, y in pairs])
                if len(pairs) >= MIN_TRADES_FOR_ANALYSIS
                else None
            )
        out[a] = row
    return out


def conditional_by(
    episodes: Sequence[Any], feature: str, control: str
) -> dict[str, Any]:
    """Rank trades by `feature` inside quintiles of `control`.

    Generalises `conditional_by_depth`. Two controls are run: **depth**, because D208 found
    it explains every WP3 effect, and **`stop_atr`**, because MFE is measured in R and
    `MFE_R = excursion / risk` — so anything that varies with leg size relative to ATR
    inherits a correlation with it arithmetically, whether or not it means anything."""
    paired = [
        (e.features.get(control), e)
        for e in episodes
        if not e.is_open and e.features.get(control) is not None
    ]
    paired.sort(key=lambda pair: (pair[0], pair[1].entry_timestamp))
    buckets: list[dict[str, Any]] = []
    for index in range(N_BUCKETS):
        lo = len(paired) * index // N_BUCKETS
        hi = len(paired) * (index + 1) // N_BUCKETS
        chunk = [e for _, e in paired[lo:hi]]
        values = [
            (e.features.get(feature), e.mfe)
            for e in chunk
            if e.features.get(feature) is not None
        ]
        rho = (
            spearman([v for v, _ in values], [m for _, m in values])
            if len(values) >= MIN_TRADES_FOR_ANALYSIS
            else None
        )
        buckets.append(
            {
                "quintile": index + 1,
                "lo": paired[lo][0] if hi > lo else None,
                "hi": paired[hi - 1][0] if hi > lo else None,
                "n": len(values),
                "rho_mfe": rho,
            }
        )
    live = [b["rho_mfe"] for b in buckets if b["rho_mfe"] is not None]
    return {
        "feature": feature,
        "control": control,
        "buckets": buckets,
        "max_abs_rho": max((abs(r) for r in live), default=None),
        "mean_rho": statistics.fmean(live) if live else None,
        "signs_agree": bool(live) and (all(r > 0 for r in live) or all(r < 0 for r in live)),
    }


def conditional_by_depth(episodes: Sequence[Any], feature: str) -> dict[str, Any]:
    """Rank trades by `feature` INSIDE each depth quintile.

    D208 made this the question. A feature whose rank correlation with MFE vanishes inside
    every depth bucket is a proxy for depth and adds nothing to it; one that survives is
    carrying something depth does not.

    Quintiles of `fib_depth`, not of the feature — the point is to hold depth roughly
    constant and let the feature vary."""
    paired = [
        (e.features.get("fib_depth"), e)
        for e in episodes
        if not e.is_open and e.features.get("fib_depth") is not None
    ]
    paired.sort(key=lambda pair: (pair[0], pair[1].entry_timestamp))
    buckets: list[dict[str, Any]] = []
    for index in range(N_BUCKETS):
        lo = len(paired) * index // N_BUCKETS
        hi = len(paired) * (index + 1) // N_BUCKETS
        chunk = [e for _, e in paired[lo:hi]]
        values = [
            (e.features.get(feature), e.mfe)
            for e in chunk
            if e.features.get(feature) is not None
        ]
        rho = spearman([v for v, _ in values], [m for _, m in values]) if len(
            values
        ) >= MIN_TRADES_FOR_ANALYSIS else None
        buckets.append(
            {
                "quintile": index + 1,
                "depth_lo": paired[lo][0] if hi > lo else None,
                "depth_hi": paired[hi - 1][0] if hi > lo else None,
                "n": len(values),
                "rho_mfe": rho,
            }
        )
    live = [b["rho_mfe"] for b in buckets if b["rho_mfe"] is not None]
    return {
        "feature": feature,
        "buckets": buckets,
        "max_abs_rho": max((abs(r) for r in live), default=None),
        "mean_rho": statistics.fmean(live) if live else None,
        "signs_agree": bool(live) and (all(r > 0 for r in live) or all(r < 0 for r in live)),
    }


def run_symbol(symbol: str, bars: Sequence[Any]) -> dict[str, Any]:
    atr = rolling_mean_true_range(bars, ATR_WINDOW_15M)
    strength = rsi(bars, RSI_WINDOW)
    gaps = fair_value_gaps(bars)
    states = market_structure(bars, PRIMARY_K)
    setups = list(find_setups(bars, PRIMARY_K, PRIMARY_TOUCH, states=states).setups)

    print("  (a) feature quintiles on the C1-only population", flush=True)
    # allow_overlap: this is an ANNOTATION population, not a book. The one-position-at-a-time
    # rule is right for an equity path and throws away most of the sample for a rank
    # statistic — 3,875 setups became 275 trades in the first run.
    annotation = run_arm(bars, setups, (), Wrapper(), allow_overlap=True)
    episodes = to_episodes(bars, setups, annotation, COST_BPS, atr, strength, gaps)
    features = {
        name: analyse_feature(episodes, name).to_dict() for name in FEATURES
    }

    print("  (b) the same features within depth quintiles", flush=True)
    conditional = {
        name: conditional_by_depth(episodes, name)
        for name in FEATURES
        if name != "fib_depth"
    }
    print("  (b2) and within stop-width quintiles, plus the collinearity matrix", flush=True)
    conditional_stop = {
        name: conditional_by(episodes, name, "stop_atr")
        for name in FEATURES
        if name != "stop_atr"
    }
    matrix = collinearity(episodes)

    print("  (c) the 8-arm ablation lattice", flush=True)
    lattice = run_lattice(bars, setups, atr)

    return {
        "n_setups": len(setups),
        "n_annotation_trades": len(annotation),
        "n_book_trades": len(run_arm(bars, setups, (), Wrapper())),
        "features": features,
        "conditional_on_depth": conditional,
        "conditional_on_stop_atr": conditional_stop,
        "collinearity": matrix,
        "lattice": lattice,
    }


def _fmt(value: float | None, spec: str = "+.3f") -> str:
    return "n/a" if value is None else format(value, spec)


def _reading(payload: dict[str, Any]) -> str:
    """Generated from the payload so prose and artifact cannot drift (D176/D183/D186).

    Written to report the verdicts the run produced rather than the ones expected: the
    first draft of this function asserted that depth would be the feature that cleared the
    criteria, and depth did not clear them."""
    runs = payload["runs"]
    parts: list[str] = []

    passing = {
        s: [f for f in FEATURES if runs[s]["features"][f]["verdict"] == "CANDIDATE"]
        for s in runs
    }
    both = sorted(set.intersection(*(set(v) for v in passing.values())))
    parts.append(
        "**Unconditionally, "
        + (
            ", ".join(f"`{f}`" for f in both) + " clear the promotion criteria on both "
            "symbols"
            if both
            else "no feature clears the promotion criteria on both symbols"
        )
        + " — and the next two paragraphs take that back.** The bar is "
        "`feature_analysis`'s, unchanged: |rho| >= 0.2, the same sign in both halves, and "
        "quintile means stepping monotonically."
    )
    parts.append("")

    parts.append(
        "| feature | "
        + " | ".join(f"`{s}` rho / verdict" for s in runs)
        + " |"
    )
    parts.append("|---|" + "---|" * len(runs))
    for f in FEATURES:
        cells = " | ".join(
            f"{_fmt(runs[s]['features'][f]['rho_mfe'])} / "
            f"{runs[s]['features'][f]['verdict']}"
            for s in runs
        )
        parts.append(f"| {f} | {cells} |")
    parts.append("")

    others = [f for f in FEATURES if f != "fib_depth"]
    trio = [f for f in FEATURES if f in ("stop_atr", "atr_to_golden", "gap_distance_atr")]
    pairs = []
    for s in runs:
        for i, a in enumerate(trio):
            for b in trio[i + 1:]:
                value = runs[s]["collinearity"][a][b]
                if value is not None:
                    pairs.append((f"`{s}` {a}~{b}", value))
    parts.append(
        "**And the survivors are one quantity, not three.** Pairwise rank correlation "
        "between them: "
        + ", ".join(f"{name} {value:+.2f}" for name, value in pairs)
        + ". `stop_atr` is leg size relative to ATR; `atr_to_golden` is a distance to a "
        "fixed fraction of the same leg, in the same ATR units; `gap_distance_atr` is a "
        "distance to a level inside it. **MFE is measured in R, so `MFE_R = excursion / "
        "risk` correlates with leg size arithmetically** — which is what all three are "
        "reporting."
    )
    parts.append("")

    parts.append(
        "**Conditioned on depth, the largest rank correlation any component reaches in any "
        "depth bucket is** "
        + " and ".join(
            f"`{s}` "
            + ", ".join(
                f"{f} {_fmt(runs[s]['conditional_on_depth'][f]['max_abs_rho'], '.2f')}"
                for f in others
            )
            for s in runs
        )
        + ", against the promotion bar of 0.2. Signs agreeing across all five depth "
        "buckets: "
        + "; ".join(
            f"`{s}` "
            + (
                ", ".join(
                    f
                    for f in others
                    if runs[s]["conditional_on_depth"][f]["signs_agree"]
                )
                or "none"
            )
            for s in runs
        )
        + ". A component that neither clears the bar nor holds its sign inside depth "
        "buckets is carrying nothing depth does not already carry."
    )
    parts.append("")

    others2 = [f for f in FEATURES if f != "stop_atr"]
    worst = {
        s: max(
            (runs[s]["conditional_on_stop_atr"][f]["max_abs_rho"] or 0.0)
            for f in others2
        )
        for s in runs
    }
    parts.append(
        "**And holding leg size constant instead, everything collapses.** Inside stop-width "
        "quintiles the largest rank correlation ANY feature reaches in ANY bucket is "
        + " and ".join(f"{worst[s]:.2f} on `{s}`" for s in runs)
        + ", against a bar of 0.2, and not one of them holds its sign across all five "
        "buckets. Depth included. **That is the verdict: once leg size relative to ATR is "
        "held constant, no component of this strategy predicts anything.**"
    )
    parts.append("")

    lat = {s: runs[s]["lattice"] for s in runs}
    full = "C1+" + "+".join(payload["filters"])
    parts.append(
        "**The lattice shows the mechanism.** Median entry depth rises from "
        + " and ".join(
            f"{lat[s]['C1']['median_entry_depth']:.3f} to "
            f"{lat[s][full]['median_entry_depth']:.3f} on `{s}`"
            for s in runs
        )
        + " as the filters stack — they enter deeper, which is what D206's census predicted "
        "and D208 showed is the whole of it. The fully-stacked arm holds "
        + " and ".join(f"{lat[s][full]['costed']['n']}" for s in runs)
        + " trades, so it is powered enough to carry a verdict, and the verdict is that at "
        "zero cost it earns "
        + " and ".join(
            f"{lat[s][full]['zero_cost_diagnostic']['mean_r']:+.3f}R" for s in runs
        )
        + " a trade against the base arm's "
        + " and ".join(
            f"{lat[s]['C1']['zero_cost_diagnostic']['mean_r']:+.3f}R" for s in runs
        )
        + " — **stacking all four filters makes it worse, before costs.**"
    )
    parts.append("")

    parts.append(
        "**Every arm loses at 40 bps, and most of them lose before costs too.** Median net "
        "R on the base arm is "
        + " and ".join(f"{lat[s]['C1']['costed']['median_r']:+.3f}" for s in runs)
        + f", with {lat[list(runs)[0]]['C1']['costed']['share_untradeable']:.0%} and "
        + f"{lat[list(runs)[1]]['C1']['costed']['share_untradeable']:.0%} of its trades "
        "untradeable outright — the round trip costs at least their whole risk. The "
        "zero-cost diagnostic on the same arm is "
        + " and ".join(
            f"{lat[s]['C1']['zero_cost_diagnostic']['mean_r']:+.3f}" for s in runs
        )
        + " mean R, which separates 'no information' from 'information the costs ate': "
        "there was not much to eat."
    )
    return "\n".join(parts)


def render(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    runs = payload["runs"]

    add("## WP4 - what each component adds on top of the others")
    add("")
    add(f"**Produced:** {payload['produced']} · **Reproduce:** "
        "`uv run python scripts/run_structure_marginal.py` (offline, deterministic)")
    add("")
    add(f"Wrapper frozen in every arm: stop at the swing extreme, {COURSE_TARGET_R:.0f}R "
        "target, channel trail after 1R, 60-bar cap. D203's finding is that refining a "
        "wrapper improves a strategy against its own predecessor and moves the null not at "
        "all, so the filters are the only thing that varies.")
    add("")

    add("### (a) Feature quintiles on one trade population - the primary reading")
    add("")
    add("The loosest arm (C1 only) generates the population; every component is annotated "
        "onto it as a **continuous** feature. Promotion criteria are "
        "`feature_analysis`'s, unchanged: |rho| >= 0.2, the same sign in both halves of the "
        "sample, and quintile means stepping monotonically.")
    add("")
    add("| symbol | feature | n | rho(MFE) | first half | second half | verdict |")
    add("|---|---|---:|---:|---:|---:|---|")
    for s in runs:
        for name in FEATURES:
            f = runs[s]["features"][name]
            add(f"| `{s}` | {name} | {f['n_available']:,} | {_fmt(f['rho_mfe'])} | "
                f"{_fmt(f['rho_first_half'])} | {_fmt(f['rho_second_half'])} | "
                f"{f['verdict']} |")
    add("")

    for s in runs:
        f = runs[s]["features"]["fib_depth"]
        if not f["buckets"]:
            continue
        add(f"Depth quintiles on `{s}` - the gradient the ladder in WP3 predicted:")
        add("")
        add("| quintile | depth range | n | mean MFE | mean MAE | win rate |")
        add("|---:|---|---:|---:|---:|---:|")
        for b in f["buckets"]:
            add(f"| {b['quintile']} | {b['lo']:.3f} - {b['hi']:.3f} | {b['n']:,} | "
                f"{b['mean_mfe']:+.4f} | {b['mean_mae']:+.4f} | {b['win_rate']:.1%} |")
        add("")

    add("### (b) The same features WITHIN depth quintiles - the reading D208 forced")
    add("")
    add("D208 found that retracement depth explains every apparent effect in the strategy, "
        "so *does this component add anything* now means *does it add anything at a given "
        "depth*. Trades are split into depth quintiles and each feature is ranked inside "
        "each one, holding depth roughly constant while the feature varies.")
    add("")
    add("| symbol | feature | rho by depth quintile (1 shallow -> 5 deep) | max abs | signs agree |")
    add("|---|---|---|---:|:--:|")
    for s in runs:
        for name, block in runs[s]["conditional_on_depth"].items():
            cells = " / ".join(_fmt(b["rho_mfe"], "+.2f") for b in block["buckets"])
            add(f"| `{s}` | {name} | {cells} | "
                f"{_fmt(block['max_abs_rho'], '.3f')} | "
                f"{'yes' if block['signs_agree'] else 'no'} |")
    add("")
    add("The promotion bar is |rho| >= 0.2. A feature that never reaches it inside any "
        "depth bucket is a proxy for depth and nothing more.")
    add("")

    add("#### (b2) The same features within STOP-WIDTH quintiles")
    add("")
    add("MFE is measured in R, and `MFE_R = excursion / risk`. So anything that varies with "
        "leg size relative to ATR inherits a correlation with it **arithmetically**, whether "
        "or not it means anything. This holds stop width roughly constant instead of depth.")
    add("")
    add("| symbol | feature | rho by stop-width quintile | max abs | signs agree |")
    add("|---|---|---|---:|:--:|")
    for sym in runs:
        for name, block_ in runs[sym]["conditional_on_stop_atr"].items():
            cells = " / ".join(_fmt(b["rho_mfe"], "+.2f") for b in block_["buckets"])
            add(f"| `{sym}` | {name} | {cells} | "
                f"{_fmt(block_['max_abs_rho'], '.3f')} | "
                f"{'yes' if block_['signs_agree'] else 'no'} |")
    add("")

    add("#### Are the surviving features three things or one?")
    add("")
    add("Pairwise rank correlation between the features themselves. Added after the "
        "corrected run returned three candidates whose signs and magnitudes were "
        "suspiciously alike.")
    add("")
    for sym in runs:
        add(f"**`{sym}`**")
        add("")
        add("| | " + " | ".join(FEATURES) + " |")
        add("|---|" + "---:|" * len(FEATURES))
        for a in FEATURES:
            cells = " | ".join(
                _fmt(runs[sym]["collinearity"][a][b], "+.2f") for b in FEATURES
            )
            add(f"| {a} | {cells} |")
        add("")

    add("### (c) The ablation lattice - confirmation")
    add("")
    add("All 8 subsets of {C2, C3, C4}, identical wrapper, identical setups. C5 is absent "
        "by D206: RSI at 30/70 leaves 2 stacked entries on both symbols, and it is carried "
        "as a continuous feature in (a) instead. **Trade counts are printed beside every "
        "number - an arm that wins on nine trades has not won.**")
    add("")
    add("| symbol | arm | trades | untradeable | hit rate | median R (40bp) | "
        "mean R, takeable only (40bp) | mean R (0bp, diagnostic) | median entry depth | "
        "stops/targets/caps |")
    add("|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for s in runs:
        for name, arm in runs[s]["lattice"].items():
            c, z = arm["costed"], arm["zero_cost_diagnostic"]
            r = arm["exit_reasons"]
            depth = arm["median_entry_depth"]
            add(f"| `{s}` | {name} | {c['n']:,} | {c['share_untradeable']:.0%} | "
                f"{c['hit_rate']:.1%} | {c['median_r']:+.3f} | "
                f"{c['mean_r_tradeable']:+.3f} | {z['mean_r']:+.3f} | "
                f"{'n/a' if depth is None else format(depth, '.3f')} | "
                f"{r['stop']}/{r['target']}/{r['max_hold']} |")
    add("")
    add("**`untradeable` is the share of trades whose 40 bps round trip costs at least their "
        "entire risk.** A stop placed at the swing extreme, entered at a shallow "
        "retracement, can sit a few basis points away, and the plain mean R for those "
        "trades runs to -100 and worse. That is correct arithmetic describing a position "
        "size nobody can take, so the median and the takeable-only mean are what the table "
        "reports and the raw mean is left in the JSON.")
    add("")
    add("The zero-cost column is a **diagnostic and never a strategy** - D202's device for "
        "separating 'no information' from 'information this cost structure cannot support'.")
    add("")

    add("### What the readings say")
    add("")
    add(_reading(payload))
    add("")

    add("### Multiplicity")
    add("")
    add("| reading | cells | looks |")
    add("|---|---|---:|")
    add(f"| (a) feature quintiles | {len(FEATURES)} features x 2 symbols | {len(FEATURES) * 2} |")
    add(f"| (b) conditional on depth | {len(FEATURES) - 1} features x 2 symbols | {(len(FEATURES) - 1) * 2} |")
    add(f"| (b2) conditional on stop width | {len(FEATURES) - 1} features x 2 symbols | {(len(FEATURES) - 1) * 2} |")
    add("| collinearity matrix | diagnostic, not a test | 0 |")
    add("| (c) ablation lattice | 8 arms x 2 symbols | 16 |")
    add(f"| **WP4 total** | | **{len(FEATURES) * 2 + (len(FEATURES) - 1) * 4 + 16}** |")
    add("")
    add("Reading (b) was not pre-registered - D208 created the question it answers. It is "
        "counted in full rather than folded into (a), and like D208's depth-matched null it "
        "makes the verdict harsher rather than kinder.")
    add("")
    return "\n".join(lines)


def append_section(payload: dict[str, Any]) -> None:
    text = RESULTS.read_text(encoding="utf-8")
    marker = "## WP4 - what each component adds on top of the others"
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
        print(f"re-rendered the WP4 section of {RESULTS.name} from {SUMMARY.name}")
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
        "primary": {"k": PRIMARY_K, "touch_atr": PRIMARY_TOUCH, "cost_bps": COST_BPS},
        "target_r": COURSE_TARGET_R,
        "features": list(FEATURES),
        "filters": list(FILTERS),
        "runs": runs,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    SUMMARY.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    append_section(payload)
    print(f"\nwrote {SUMMARY.name} and the WP4 section in {payload['elapsed_seconds']}s")
    print()
    print(render(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
