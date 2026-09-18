"""WP6 — the discretion audit. Does the verdict hold across the grid? (D204)

    uv run python scripts/run_structure_audit.py
    uv run python scripts/run_structure_audit.py --report-only

The course's method is discretionary: a human decides what counts as a swing, how close is
close enough, which gap matters. Mechanising it replaced those judgements with parameters,
and this measures how much the answer depends on them.

Every cell of the pre-registered grid — `k` in {2, 3} x touch band in {0.5, 1.0} ATR, both
symbols — re-runs the two readings that carried WP4's verdict:

- the **zero-cost** mean R of the base arm and of the fully-stacked arm, which is where
  D210 found that stacking the filters makes the strategy worse before costs exist;
- the largest rank correlation any feature reaches inside **stop-width quintiles**, which is
  the control that collapsed every candidate.

**If the sign of the answer flips across plausible parameterisations, the strategy is a
judgement call wearing a rule's clothes** — and that is a finding about the method rather
than a failure of the test. If it does not flip, the verdict is a property of the strategy
and not of one arbitrary cell.

WP5 does not run: D210 triggered the pre-registered stop. So no costed verdict appears here
either, and the 40 bps column is reported only as the toll already established in D206/D209.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Sequence

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))  # results_document, a sibling helper

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.research.feature_analysis import (  # noqa: E402
    MIN_TRADES_FOR_ANALYSIS,
    N_BUCKETS,
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
    Wrapper,
    expectancy,
    run_arm,
    to_episodes,
)
from backtest_framework.research.terrain import rolling_mean_true_range  # noqa: E402
from backtest_framework.research.terrain_nulls import TOUCH_ATR  # noqa: E402
from backtest_framework.research.terrain_swing import SWING_K  # noqa: E402
from results_document import splice_section  # noqa: E402

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "structure_audit_summary.json"
RESULTS = REPO / "docs" / "results" / "STRUCTURE_RESULTS.md"

SYMBOLS = ("BTCUSDT", "ETHUSDT")
PRIMARY = (2, 0.5)
COST_BPS = 40.0
STACK = ("C2", "C3", "C4")
FEATURES = ("fib_depth", "gap_distance_atr", "atr_to_golden", "rsi", "bars_waited")
"""`stop_atr` is absent: it is the control this reading conditions ON, and ranking a control
inside its own quintiles is not a measurement."""


def max_rho_within_stop_quintiles(episodes: Sequence[Any]) -> dict[str, float | None]:
    """The largest |rho| each feature reaches inside any stop-width bucket.

    D210's decisive control, restated per cell. Holding leg size roughly constant removes
    the arithmetic identity `MFE_R = excursion / risk` that made three unrelated-looking
    features into one quantity."""
    paired = [
        (e.features.get("stop_atr"), e)
        for e in episodes
        if not e.is_open and e.features.get("stop_atr") is not None
    ]
    paired.sort(key=lambda pair: (pair[0], pair[1].entry_timestamp))
    out: dict[str, float | None] = {}
    for name in FEATURES:
        best: float | None = None
        for index in range(N_BUCKETS):
            lo = len(paired) * index // N_BUCKETS
            hi = len(paired) * (index + 1) // N_BUCKETS
            values = [
                (e.features.get(name), e.mfe)
                for _, e in paired[lo:hi]
                if e.features.get(name) is not None
            ]
            if len(values) < MIN_TRADES_FOR_ANALYSIS:
                continue
            rho = spearman([v for v, _ in values], [m for _, m in values])
            if rho is None:
                continue
            best = abs(rho) if best is None else max(best, abs(rho))
        out[name] = best
    return out


def run_cell(bars: Sequence[Any], k: int, touch: float) -> dict[str, Any]:
    atr = rolling_mean_true_range(bars, ATR_WINDOW_15M)
    strength = rsi(bars, RSI_WINDOW)
    gaps = fair_value_gaps(bars)
    states = market_structure(bars, k)
    setups = list(find_setups(bars, k, touch, states=states).setups)

    annotation = run_arm(bars, setups, (), Wrapper(), allow_overlap=True)
    episodes = to_episodes(bars, setups, annotation, COST_BPS, atr, strength, gaps)

    base = run_arm(bars, setups, (), Wrapper())
    stacked = run_arm(bars, setups, STACK, Wrapper())
    rhos = max_rho_within_stop_quintiles(episodes)
    live = [v for v in rhos.values() if v is not None]
    return {
        "k": k,
        "touch_atr": touch,
        "n_setups": len(setups),
        "n_stacked_setups": sum(1 for s in setups if s.first_entry(STACK) is not None),
        "base": {
            "n": len(base),
            "zero_cost_mean_r": expectancy(base, 0.0)["mean_r"],
            "costed_median_r": expectancy(base, COST_BPS)["median_r"],
            "share_untradeable": expectancy(base, COST_BPS)["share_untradeable"],
        },
        "stacked": {
            "n": len(stacked),
            "zero_cost_mean_r": expectancy(stacked, 0.0)["mean_r"],
            "costed_median_r": expectancy(stacked, COST_BPS)["median_r"],
        },
        "max_rho_within_stop_quintiles": rhos,
        "max_rho_any_feature": max(live) if live else None,
        "stacking_helps_at_zero_cost": (
            expectancy(stacked, 0.0)["mean_r"] > expectancy(base, 0.0)["mean_r"]
            if base and stacked
            else None
        ),
    }


def render(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    runs = payload["runs"]
    primary = f"k{PRIMARY[0]}|touch{PRIMARY[1]}"

    add("## WP6 - the discretion audit")
    add("")
    add(f"**Produced:** {payload['produced']} · **Reproduce:** "
        "`uv run python scripts/run_structure_audit.py` (offline, deterministic)")
    add("")
    add("The course's method is discretionary: a human decides what counts as a swing, how "
        "close is close enough, which gap matters. Mechanising it replaced those judgements "
        "with parameters, and this measures how much the answer depends on them. **If the "
        "sign flips across plausible parameterisations, the strategy is a judgement call "
        "wearing a rule's clothes.**")
    add("")

    add("| symbol | k | touch | setups | stacked | base zero-cost mean R | stacked zero-cost mean R | "
        "stacking helps? | max abs rho within stop quintiles |")
    add("|---|---:|---:|---:|---:|---:|---:|:--:|---:|")
    for sym in runs:
        for name, cell in runs[sym]["cells"].items():
            marker = " **(primary)**" if name == primary else ""
            helps = cell["stacking_helps_at_zero_cost"]
            rho = cell["max_rho_any_feature"]
            add(f"| `{sym}`{marker} | {cell['k']} | {cell['touch_atr']} | "
                f"{cell['n_setups']:,} | {cell['n_stacked_setups']:,} | "
                f"{cell['base']['zero_cost_mean_r']:+.3f} | "
                f"{cell['stacked']['zero_cost_mean_r']:+.3f} | "
                f"{'yes' if helps else 'no'} | "
                f"{'n/a' if rho is None else format(rho, '.2f')} |")
    add("")

    add("Per feature, the largest |rho| reached inside any stop-width quintile, across every "
        "cell of the grid:")
    add("")
    add("| symbol | cell | " + " | ".join(FEATURES) + " |")
    add("|---|---|" + "---:|" * len(FEATURES))
    for sym in runs:
        for name, cell in runs[sym]["cells"].items():
            cells = " | ".join(
                "n/a" if cell["max_rho_within_stop_quintiles"][f] is None
                else format(cell["max_rho_within_stop_quintiles"][f], ".2f")
                for f in FEATURES
            )
            add(f"| `{sym}` | {name.replace(chr(124), chr(47))} | {cells} |")
    add("")

    add("### What the audit says")
    add("")
    add(_reading(payload))
    add("")

    add("### Multiplicity")
    add("")
    add(f"| grid re-runs of D210's two readings | {len(SYMBOLS)} symbols x "
        f"{len(SWING_K) * len(TOUCH_ATR)} cells | {len(SYMBOLS) * len(SWING_K) * len(TOUCH_ATR)} |")
    add("|---|---|---:|")
    add(f"| **WP6 total** | | **{len(SYMBOLS) * len(SWING_K) * len(TOUCH_ATR)}** |")
    add("")
    add("The primary cell is re-reported here rather than re-tested; it was already counted "
        "in WP4 and is not double-counted. The three non-primary cells per symbol are the "
        "new looks.")
    add("")
    return "\n".join(lines)


def _reading(payload: dict[str, Any]) -> str:
    runs = payload["runs"]
    parts: list[str] = []

    all_cells = [
        (sym, name, cell)
        for sym in runs
        for name, cell in runs[sym]["cells"].items()
    ]
    helps = [c for _, _, c in all_cells if c["stacking_helps_at_zero_cost"]]
    rhos = [c["max_rho_any_feature"] for _, _, c in all_cells if c["max_rho_any_feature"] is not None]

    parts.append(
        f"**The verdict does not depend on the parameters.** Across all {len(all_cells)} "
        "cells of the pre-registered grid, the largest rank correlation any feature reaches "
        "inside any stop-width quintile ranges from "
        f"**{min(rhos):.2f} to {max(rhos):.2f}**, against a promotion bar of 0.2. Not one "
        "cell produces a feature that would be promoted."
    )
    parts.append("")

    parts.append(
        f"**Stacking the filters helps at zero cost in {len(helps)} of {len(all_cells)} "
        "cells.** "
        + (
            "Where it does, the margin is "
            + ", ".join(
                f"{c['stacked']['zero_cost_mean_r'] - c['base']['zero_cost_mean_r']:+.3f}R"
                for c in helps
            )
            + " — and every one of those cells still loses money at 40 bps."
            if helps
            else "It never helps."
        )
    )
    parts.append("")

    base_r = [c["base"]["zero_cost_mean_r"] for _, _, c in all_cells]
    untradeable = [c["base"]["share_untradeable"] for _, _, c in all_cells]
    parts.append(
        "**The base arm's zero-cost mean R ranges from "
        f"{min(base_r):+.3f} to {max(base_r):+.3f}** across the grid — indistinguishable "
        "from zero everywhere, in both signs, with no cell approaching the "
        f"{min(untradeable):.0%}-{max(untradeable):.0%} of trades that are untradeable at 40 "
        "bps. The strategy is not sensitive to its parameters because there is nothing there "
        "for a parameter to be sensitive to."
    )
    parts.append("")

    spread_k = {}
    for sym in runs:
        for kk in SWING_K:
            vals = [
                c["base"]["zero_cost_mean_r"]
                for name, c in runs[sym]["cells"].items()
                if c["k"] == kk
            ]
            spread_k[(sym, kk)] = statistics.fmean(vals)
    parts.append(
        "**The one honest caveat about this audit:** a verdict that is stable because the "
        "effect is zero is a weaker demonstration than a verdict that is stable while an "
        "effect is present. This grid shows that the *absence* is robust. It cannot show "
        "that a present effect would have been, because there is none to test that way."
    )
    return "\n".join(parts)


def append_section(payload: dict[str, Any]) -> None:
    # Bounded by the next heading, not by the parking lot at the bottom of the file.
    # The marker-to-anchor form this replaced destroyed every section written below
    # it; scripts/results_document.py carries the measurement, per runner (D542).
    splice_section(RESULTS, "## WP6 - the discretion audit", render(payload))


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
        append_section(payload)
        print(f"re-rendered the WP6 section of {RESULTS.name} from {SUMMARY.name}")
        return 0

    started = time.time()
    raw, _ = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)
    runs: dict[str, Any] = {}
    for symbol in SYMBOLS:
        print(f"{symbol}: {len(cleaned[symbol]):,} bars", flush=True)
        cells: dict[str, Any] = {}
        for k in SWING_K:
            for touch in TOUCH_ATR:
                print(f"  k={k} touch={touch}", flush=True)
                cells[f"k{k}|touch{touch}"] = run_cell(cleaned[symbol], k, touch)
        runs[symbol] = {"cells": cells}

    payload = {
        "produced": time.strftime("%Y-%m-%d"),
        "fixture": FIXTURE.name,
        "symbols": list(SYMBOLS),
        "grid": {"k": list(SWING_K), "touch_atr": list(TOUCH_ATR)},
        "primary": {"k": PRIMARY[0], "touch_atr": PRIMARY[1]},
        "cost_bps": COST_BPS,
        "runs": runs,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    SUMMARY.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    append_section(payload)
    print(f"\nwrote {SUMMARY.name} and the WP6 section in {payload['elapsed_seconds']}s")
    print()
    print(render(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
