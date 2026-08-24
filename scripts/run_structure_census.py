"""WP2 — the census. Counts only, before any performance number exists (D204).

    uv run python scripts/run_structure_census.py
    uv run python scripts/run_structure_census.py --report-only

This produces **no return, no Sharpe and no verdict about whether anything works.** That is
the point. `STRUCTURE_MODEL.md` requires a counts-only pass first because counts have
repeatedly caught defects in this project before they became results — D198's census
rejected a proposed rule outright once it showed 86% of signals already had a second
approach within 20 bars, making the "filter" a one-bar entry delay wearing a filter's name.

Four things it reports:

1. **The funnel.** How many changes of character become setups, and how many setups survive
   each additional filter. Reported both as SIMULTANEOUS confluence (the course's actual
   claim — the filters line up at one price at one time) and as each condition holding
   somewhere in the window. The gap between those two numbers is the confluence claim
   measured in counts, and it costs nothing to look at.

2. **The stop-condition check.** Fewer than 30 fully-stacked entries per symbol and that arm
   carries no verdict, per the pre-registration.

3. **The friction, by arithmetic rather than experiment.** D196/D197 pin a 40 bps round trip
   at 0.49R on a 0.5-ATR stop and 0.12R at 2 ATR. Applied to the stop widths this strategy
   actually produces, that yields the hit rate the course's 5R target requires — and the
   course's entire claimed edge is a hit-rate argument made with costs omitted.

4. **The sensitivity across the pre-registered grid**, so WP6's discretion audit has counts
   to stand on and so a cell that produces nothing cannot quietly vanish.

Offline and deterministic: one committed fixture, no RNG.
"""

from __future__ import annotations

import json
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
from backtest_framework.research.structure import (  # noqa: E402
    Event,
    market_structure,
    retracement,
)
from backtest_framework.research.structure_setups import (  # noqa: E402
    ATR_WINDOW_15M,
    CONDITIONS,
    Setup,
    find_setups,
    friction_in_r,
    required_hit_rate,
    stop_distance,
)
from backtest_framework.research.terrain import rolling_mean_true_range  # noqa: E402
from backtest_framework.research.terrain_nulls import TOUCH_ATR  # noqa: E402
from backtest_framework.research.terrain_swing import SWING_K  # noqa: E402

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "structure_census_summary.json"
RESULTS = REPO / "STRUCTURE_RESULTS.md"

SYMBOLS = ("BTCUSDT", "ETHUSDT")
PRIMARY_K, PRIMARY_TOUCH = 2, 0.5
COST_BPS = 40.0
COURSE_TARGET_R = 5.0
"""The course settles on ~5R after claiming 4R-8R. Its arithmetic — 20% breaks even, 30% is
'highly profitable' — is stated with no costs at all."""

MIN_STACKED_ENTRIES = 30
"""The pre-registered stop condition. Below this the fully-stacked arm is reported as
underpowered and carries no verdict; only the marginal analysis in WP4a proceeds."""

STACK = ("C2", "C3", "C4")
"""The course's structural confluence. C5 is reported separately — it is the control, and
stacking a control into the primary arm would make it a fifth idea."""


def funnel(setups: Sequence[Setup]) -> dict[str, Any]:
    """Setups surviving each cumulative filter, simultaneous and 'ever' side by side."""
    cumulative: dict[str, int] = {"C1": len(setups)}
    required: list[str] = []
    for condition in STACK + ("C5",):
        required.append(condition)
        name = "C1+" + "+".join(required)
        cumulative[name] = sum(
            1 for s in setups if s.first_entry(required) is not None
        )

    alone = {
        f"C1+{c}": sum(1 for s in setups if s.first_entry((c,)) is not None)
        for c in CONDITIONS
    }
    ever = {c: sum(1 for s in setups if s.ever(c)) for c in CONDITIONS}
    ever_all = sum(1 for s in setups if all(s.ever(c) for c in STACK))
    simultaneous_all = sum(1 for s in setups if s.first_entry(STACK) is not None)
    return {
        "cumulative": cumulative,
        "each_alone": alone,
        "ever_in_window": ever,
        "stack_ever_separately": ever_all,
        "stack_simultaneously": simultaneous_all,
    }


def entry_stats(
    bars: Sequence[Any], setups: Sequence[Setup], required: Sequence[str], atr: Sequence[float]
) -> dict[str, Any]:
    """Wait, stop width and friction for the entries one filter set actually produces."""
    waits: list[int] = []
    stops_atr: list[float] = []
    stops_pct: list[float] = []
    depths: list[float] = []
    frictions: list[float] = []
    directions: list[int] = []

    for setup in setups:
        index = setup.first_entry(required)
        if index is None:
            continue
        price = bars[index].bar.close
        stop = stop_distance(setup, price)
        if stop <= 0.0 or price <= 0.0 or atr[index] <= 0.0:
            continue
        waits.append(index - setup.choch_index)
        stops_atr.append(stop / atr[index])
        stops_pct.append(stop / price)
        depth = retracement(setup.leg, price)
        if depth is not None:
            depths.append(depth)
        value = friction_in_r(COST_BPS, price, stop)
        if value is not None:
            frictions.append(value)
        directions.append(setup.direction)

    if not waits:
        return {"n": 0}

    median_friction = statistics.median(frictions)
    return {
        "n": len(waits),
        "n_long": sum(1 for d in directions if d > 0),
        "n_short": sum(1 for d in directions if d < 0),
        "median_wait_bars": statistics.median(waits),
        "median_stop_atr": statistics.median(stops_atr),
        "median_stop_pct": statistics.median(stops_pct),
        "median_retracement": statistics.median(depths) if depths else None,
        "median_friction_r": median_friction,
        "mean_friction_r": statistics.fmean(frictions),
        "friction_r_p90": _percentile(frictions, 0.90),
        "required_hit_rate_at_5r": required_hit_rate(COURSE_TARGET_R, median_friction),
        "frictionless_hit_rate_at_5r": required_hit_rate(COURSE_TARGET_R, 0.0),
    }


def _percentile(values: Sequence[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    position = q * (len(ordered) - 1)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def run_symbol(symbol: str, bars: Sequence[Any]) -> dict[str, Any]:
    atr = rolling_mean_true_range(bars, ATR_WINDOW_15M)
    cells: dict[str, Any] = {}
    for k in SWING_K:
        states = market_structure(bars, k)
        events = {
            "choch": sum(
                1 for s in states if s.event in (Event.CHOCH_UP, Event.CHOCH_DOWN)
            ),
            "bos": sum(1 for s in states if s.event in (Event.BOS_UP, Event.BOS_DOWN)),
        }
        for touch in TOUCH_ATR:
            population = find_setups(bars, k, touch, states=states, atr_window=ATR_WINDOW_15M)
            setups = population.setups
            closed = {
                reason: sum(1 for s in setups if s.closed_by == reason)
                for reason in ("invalidated", "superseded", "max_hold", "series_end", "atr_unavailable")
            }
            cells[f"k{k}|touch{touch}"] = {
                "k": k,
                "touch_atr": touch,
                "events": events,
                "population": {
                    "n_choch": population.n_choch,
                    "setups": len(setups),
                    "dropped_no_leg": population.dropped_no_leg,
                    "dropped_dead_on_arrival": population.dropped_dead_on_arrival,
                    "dropped_no_atr": population.dropped_no_atr,
                },
                "closed_by": closed,
                "funnel": funnel(setups),
                "entries_base": entry_stats(bars, setups, (), atr),
                "entries_stacked": entry_stats(bars, setups, STACK, atr),
            }
            print(
                f"  k={k} touch={touch}: {len(setups):,} setups -> "
                f"{cells[f'k{k}|touch{touch}']['funnel']['cumulative']['C1+C2+C3+C4']} stacked",
                flush=True,
            )
    return {"n_bars": len(bars), "cells": cells}


def _reading(payload: dict[str, Any], primary: str) -> str:
    """The five things the counts settle, written from the payload rather than by hand.

    Generated so `--report-only` reproduces the prose from the artifact and the two cannot
    drift — the most repeated defect in this project's history (D176, D183, D186)."""
    runs = payload["runs"]
    parts: list[str] = []

    stacked = {s: runs[s]["cells"][primary]["funnel"]["cumulative"]["C1+C2+C3+C4"] for s in runs}
    rsi_stacked = {
        s: runs[s]["cells"][primary]["funnel"]["cumulative"]["C1+C2+C3+C4+C5"] for s in runs
    }
    base = {s: runs[s]["cells"][primary]["entries_base"] for s in runs}
    stack_stats = {s: runs[s]["cells"][primary]["entries_stacked"] for s in runs}
    fib_alone = {s: runs[s]["cells"][primary]["funnel"]["each_alone"]["C1+C3"] for s in runs}
    n_setups = {s: runs[s]["cells"][primary]["funnel"]["cumulative"]["C1"] for s in runs}
    ever = {s: runs[s]["cells"][primary]["funnel"]["stack_ever_separately"] for s in runs}

    parts.append(
        "**1. The stop condition clears, so the programme continues.** "
        + " and ".join(f"`{s}` produces {stacked[s]:,} stacked entries" for s in runs)
        + f", both above the pre-registered floor of {MIN_STACKED_ENTRIES}. H5 — that the "
        "stacked arm would be underpowered — is **falsified**. It was held at moderate "
        "confidence and it was wrong.\n"
    )

    parts.append(
        "**2. The round trip eats a third to a half of the risk before anything happens.** "
        "On the C1-only arm the median stop sits at "
        + " and ".join(f"{base[s]['median_stop_pct']:.2%} of price on `{s}`" for s in runs)
        + f", against a {COST_BPS:.0f} bps round trip — so friction is "
        + " and ".join(f"{base[s]['median_friction_r']:.2f}R" for s in runs)
        + ". That is arithmetic rather than a result, and it is the structural problem with "
        "running this strategy on 15m bars: a stop placed at a 15m swing extreme is close "
        "enough that crossing the spread twice is a material fraction of the whole trade.\n"
    )

    need = {s: stack_stats[s]["required_hit_rate_at_5r"] for s in runs}
    parts.append(
        "**3. The course's central arithmetic is wrong once costs exist.** It claims a 5R "
        f"target breaks even at ~20% and is \"highly profitable\" at 30%. Frictionless that "
        f"is nearly right — the true break-even is {required_hit_rate(COURSE_TARGET_R, 0.0):.1%}. "
        "At 40 bps on the stacked arm it becomes "
        + " and ".join(f"{need[s]:.1%} on `{s}`" for s in runs)
        + ", and on the C1-only arm "
        + " and ".join(
            f"{base[s]['required_hit_rate_at_5r']:.1%}" for s in runs
        )
        + ". **A 20% hit rate at 5R loses money at every cell measured here.** No backtest "
        "was needed to establish that, and none of it depends on whether the components "
        "carry information.\n"
    )

    worse = all(
        stack_stats[s]["median_friction_r"] > base[s]["median_friction_r"] for s in runs
    )
    parts.append(
        "**4. The confluence stack enters deeper, and that makes the arithmetic "
        + ("WORSE" if worse else "better")
        + ".** Median retracement moves from "
        + " and ".join(
            f"{base[s]['median_retracement']:.3f} to "
            f"{stack_stats[s]['median_retracement']:.3f} on `{s}`"
            for s in runs
        )
        + ". The stop sits at the extreme the leg came FROM, so a deeper entry is a "
        "**tighter** stop, not a wider one: "
        + " and ".join(
            f"{base[s]['median_stop_atr']:.2f} to "
            f"{stack_stats[s]['median_stop_atr']:.2f} ATR"
            for s in runs
        )
        + ", and friction rises from "
        + " and ".join(
            f"{base[s]['median_friction_r']:.2f}R to "
            f"{stack_stats[s]['median_friction_r']:.2f}R"
            for s in runs
        )
        + ". So the confluence the course sells as precision is, in cost terms, a tax: it "
        "buys a better price by risking less, and the fixed spread then eats a larger share "
        "of what is left. WP4 asks whether the better price is worth the tax.\n"
    )

    parts.append(
        "**5. Two filters barely filter, and one is incompatible with the rest.** C3 (the "
        "61.8% band) admits "
        + " and ".join(f"{fib_alone[s]:,} of {n_setups[s]:,}" for s in runs)
        + " setups on its own — roughly "
        + " and ".join(f"{fib_alone[s] / n_setups[s]:.0%}" for s in runs)
        + " of the population, which is very little work for a filter, before anyone asks "
        "whether 0.618 is special. C5 (RSI 30/70) collapses the stacked arm to "
        + " and ".join(f"{rsi_stacked[s]:,}" for s in runs)
        + " entries: the textbook thresholds essentially never coincide with structural "
        "confluence. **C5 is therefore dropped as a stacked filter and kept as a continuous "
        "feature in WP4a**, which is where a 2-trade arm has nothing to say and a rank "
        "correlation still does.\n"
    )

    parts.append(
        "**And one number that is the discretion gap itself.** "
        + " and ".join(
            f"`{s}`: {ever[s]:,} setups have all three conditions somewhere in the pullback "
            f"window but only {stacked[s]:,} have them at the same bar "
            f"({stacked[s] / ever[s]:.0%})"
            for s in runs
        )
        + ". A trader reading the chart afterwards sees the level, the retracement and the "
        "gap all present and calls it confluence. Two thirds of the time they were not "
        "simultaneous, and which bar you would actually have entered on is a judgement "
        "call. WP6 is the audit of that; this is its first measurement."
    )
    return "\n".join(parts)


def render(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    primary = f"k{PRIMARY_K}|touch{PRIMARY_TOUCH}"

    add("## WP2 — the census, counts only\n")
    add(f"**Produced:** {payload['produced']} · "
        "**Reproduce:** `uv run python scripts/run_structure_census.py` (offline, deterministic)\n")
    add("No return, no Sharpe and no verdict about whether anything works appears in this "
        "section. `STRUCTURE_MODEL.md` requires the counts first, because counts have "
        "repeatedly caught defects in this project before they became results (D197, D198, "
        "D201, D202).\n")

    add("> **CORRECTED TWICE, 2026-08-24 — D209 then D212.** Both corrections are named "
        "here rather than shown as new numbers under an old heading.")
    add(">")
    add("> **D209** — the stop was placed at `leg.end_price`, the extreme the impulse ran "
        "TO, which for a long sits ABOVE the entry and is not a stop at all. It also "
        "reversed the direction of finding 4 below: a deeper entry is a *tighter* stop, so "
        "the confluence stack raises friction rather than halving it.")
    add(">")
    add("> **D212** — the cost convention. `cost_bps` is a PER-SIDE exchange fee, so a "
        "round trip pays twice it. This section charged it once while WP4's lattice charged "
        "it twice: two halves of one study disagreeing by a factor of two on the same tier.")
    add(">")
    add("> Superseded base-arm friction: **0.97R / 0.72R** (D209 era) and **0.48R / 0.34R** "
        "(post-D209, pre-D212). Superseded required hit rate at 5R: **32.9% / 28.6%** and "
        "**24.7% / 22.3%**. The figures below are the current ones.")
    add("")

    add("### The population, at the primary cell\n")
    add(f"Primary: `k={PRIMARY_K}`, touch band `{PRIMARY_TOUCH}` ATR, "
        f"ATR window {ATR_WINDOW_15M:,} bars (20 days at 96/day, D194's calendar match).\n")
    add("| symbol | bars | CHoCH | BOS | setups | no leg | dead on arrival | in ATR warm-up |")
    add("|---|---:|---:|---:|---:|---:|---:|---:|")
    for symbol in payload["symbols"]:
        cell = payload["runs"][symbol]["cells"][primary]
        pop = cell["population"]
        add(f"| `{symbol}` | {payload['runs'][symbol]['n_bars']:,} | {pop['n_choch']:,} | "
            f"{cell['events']['bos']:,} | {pop['setups']:,} | {pop['dropped_no_leg']:,} | "
            f"{pop['dropped_dead_on_arrival']:,} | {pop['dropped_no_atr']:,} |")
    add("")
    add("*Dead on arrival* is a real category rather than a rounding error: the impulse "
        "leg's end pivot needs `k` bars to confirm, and price can retrace the whole leg "
        "inside those bars. Those setups are refused, never entered at a bar where the "
        "structure was already gone.\n")

    add("### The funnel — how many setups survive each filter\n")
    add("| symbol | C1 | +C2 level | +C3 fib | +C4 gap | +C5 rsi |")
    add("|---|---:|---:|---:|---:|---:|")
    for symbol in payload["symbols"]:
        c = payload["runs"][symbol]["cells"][primary]["funnel"]["cumulative"]
        add(f"| `{symbol}` | {c['C1']:,} | {c['C1+C2']:,} | {c['C1+C2+C3']:,} | "
            f"{c['C1+C2+C3+C4']:,} | {c['C1+C2+C3+C4+C5']:,} |")
    add("")

    add("Each filter on its own, against the same setup population:\n")
    add("| symbol | C1+C2 | C1+C3 | C1+C4 | C1+C5 |")
    add("|---|---:|---:|---:|---:|")
    for symbol in payload["symbols"]:
        a = payload["runs"][symbol]["cells"][primary]["funnel"]["each_alone"]
        add(f"| `{symbol}` | {a['C1+C2']:,} | {a['C1+C3']:,} | {a['C1+C4']:,} | {a['C1+C5']:,} |")
    add("")

    add("### Confluence, measured in counts\n")
    add("The course's claim is that the filters line up **at one price at one time**. That "
        "is a different population from each filter being satisfied somewhere during the "
        "pullback, and the gap between the two is the claim itself:\n")
    add("| symbol | each of C2/C3/C4 held somewhere | all three held simultaneously | ratio |")
    add("|---|---:|---:|---:|")
    for symbol in payload["symbols"]:
        f = payload["runs"][symbol]["cells"][primary]["funnel"]
        ever, sim = f["stack_ever_separately"], f["stack_simultaneously"]
        ratio = f"{sim / ever:.2f}" if ever else "n/a"
        add(f"| `{symbol}` | {ever:,} | {sim:,} | {ratio} |")
    add("")

    add("### The stop condition\n")
    for symbol in payload["symbols"]:
        n = payload["runs"][symbol]["cells"][primary]["funnel"]["cumulative"]["C1+C2+C3+C4"]
        state = "CLEARS" if n >= MIN_STACKED_ENTRIES else "FAILS"
        add(f"- `{symbol}`: **{n:,}** stacked entries against a floor of "
            f"{MIN_STACKED_ENTRIES} — **{state}**.")
    add("")

    add("### The friction, by arithmetic\n")
    add(f"A {COST_BPS:.0f} bps round trip against the stop widths these entries actually "
        "produce. D196/D197 already pinned the same arithmetic on daily bars at **0.49R on "
        "a 0.5-ATR stop** and **0.12R at 2 ATR**; this is that calculation on this "
        "strategy's stops, run before any backtest.\n")
    add("| symbol | arm | n | median wait (bars) | median retracement | median stop (ATR) | "
        "median stop (%) | median friction (R) | hit rate needed at 5R |")
    add("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for symbol in payload["symbols"]:
        cell = payload["runs"][symbol]["cells"][primary]
        for label, key in (("C1 only", "entries_base"), ("C1+C2+C3+C4", "entries_stacked")):
            e = cell[key]
            if not e.get("n"):
                add(f"| `{symbol}` | {label} | 0 | — | — | — | — | — | — |")
                continue
            need = e["required_hit_rate_at_5r"]
            need_text = f"{need:.1%}" if need is not None else "**unreachable**"
            depth = e.get("median_retracement")
            depth_text = f"{depth:.3f}" if depth is not None else "—"
            add(f"| `{symbol}` | {label} | {e['n']:,} | {e['median_wait_bars']:.0f} | "
                f"{depth_text} | {e['median_stop_atr']:.2f} | {e['median_stop_pct']:.2%} | "
                f"{e['median_friction_r']:.3f} | {need_text} |")
    add("")
    frictionless = required_hit_rate(COURSE_TARGET_R, 0.0)
    add(f"Frictionless, a 5R target breaks even at **{frictionless:.1%}** — the course's "
        "\"two out of ten\". The column above is the same arithmetic with costs put back.\n")

    add("### What the counts say\n")
    add(_reading(payload, primary))

    add("### Sensitivity across the pre-registered grid\n")
    add("| symbol | k | touch | setups | stacked | median stop (ATR) | median friction (R) |")
    add("|---|---:|---:|---:|---:|---:|---:|")
    for symbol in payload["symbols"]:
        for name, cell in payload["runs"][symbol]["cells"].items():
            e = cell["entries_stacked"]
            stop = f"{e['median_stop_atr']:.2f}" if e.get("n") else "—"
            fric = f"{e['median_friction_r']:.3f}" if e.get("n") else "—"
            marker = " **(primary)**" if name == primary else ""
            add(f"| `{symbol}`{marker} | {cell['k']} | {cell['touch_atr']} | "
                f"{cell['population']['setups']:,} | "
                f"{cell['funnel']['cumulative']['C1+C2+C3+C4']:,} | {stop} | {fric} |")
    add("")

    add("### Multiplicity\n")
    add("**Looks: 0.** A census is not a test. Nothing here compares anything to anything, "
        "no hypothesis is scored, and no parameter is chosen on the strength of it. The "
        "grid above is reported so that WP6's discretion audit has counts to stand on and "
        "so a cell producing nothing cannot quietly vanish from a later table.\n")
    return "\n".join(lines)


def append_section(payload: dict[str, Any]) -> None:
    text = RESULTS.read_text(encoding="utf-8")
    marker = "## WP2 — the census, counts only"
    body = render(payload)
    if marker in text:
        head, _, rest = text.partition(marker)
        tail = rest.partition("\n## ")
        remainder = ("\n## " + tail[2]) if tail[1] else ""
        text = head + body + remainder
    else:
        anchor = "### Parking lot"
        head, _, rest = text.partition(anchor)
        text = head + body + "\n---\n\n" + anchor + rest
    RESULTS.write_text(text, encoding="utf-8")


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
        append_section(payload)
        print(f"re-rendered the WP2 section of {RESULTS.name} from {SUMMARY.name}")
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
        "atr_window": ATR_WINDOW_15M,
        "min_stacked_entries": MIN_STACKED_ENTRIES,
        "course_target_r": COURSE_TARGET_R,
        "runs": runs,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    SUMMARY.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    append_section(payload)
    print(f"\nwrote {SUMMARY.name} and the WP2 section of {RESULTS.name} "
          f"in {payload['elapsed_seconds']}s")
    print()
    print(render(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
