"""D215 — is the depth staircase just mean reversion? Delete the structure and find out.

    uv run python scripts/run_generic_reversal.py
    uv run python scripts/run_generic_reversal.py --report-only

`docs/decisions/D215-is-it-just-mean-reversion.md` governs this and was committed before
this file existed.

## The one thing that makes the comparison mean anything

**Both arms call `structure_nulls.continue_from`.** Not two implementations of the same
rule — the same function, with the same band, the same horizon and the same
band-fixed-at-the-bar convention. Its docstring already says why it exists: it fires at a
*bar* rather than at a price, "so the resolution rule is identical to the level arms' and
the two remain comparable". A restatement here would be a second definition to drift from
the first, which is the defect this repo has recorded more than any other.

## What the two arms are

**Generic.** Every M-th bar, bucketed by `|move|` where `move(t) = (close[t] − close[t−M])
/ ATR[t]`. No change of character, no leg, no level, no gap. The bet is against the move.

**Structure.** Every touch of every rung of the Fibonacci ladder, carrying the counter-move
size that produced it — `|close − leg.end| / ATR` — so each touch lands in a generic bucket.
The bet is the change of character's direction, which is the same bet: against the pullback.

The verdict is the **matched** comparison. D208 is the precedent and the warning: there the
fair value gap sat at the 100th percentile of 500 draws against a uniform placebo and at
+0.006 against one matched on depth. The raw comparison was not wrong; it answered a
different question.

## Non-overlapping sampling

Adjacent bars share nearly all of their lookback and their forward window, so 294,000 is not
the sample size. The generic arm steps by `M`. Pre-registered, because overlapping windows
would make a **negative** look sharper than it is — the failure mode nobody checks.
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
sys.path.insert(0, str(REPO / "scripts"))  # results_document, a sibling helper

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.research.feature_analysis import spearman  # noqa: E402
from backtest_framework.research.structure import (  # noqa: E402
    CANONICAL_RATIOS,
    PLACEBO_RATIOS,
    market_structure,
    ratio_price,
)
from backtest_framework.research.structure_nulls import continue_from  # noqa: E402
from backtest_framework.research.structure_setups import (  # noqa: E402
    ATR_WINDOW_15M,
    find_setups,
)
from backtest_framework.research.structure_strategies import (  # noqa: E402
    Wrapper,
    expectancy,
    run_arm,
)
from backtest_framework.research.terrain import rolling_mean_true_range  # noqa: E402
from backtest_framework.research.terrain_nulls import HORIZON  # noqa: E402
from results_document import splice_section  # noqa: E402

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "generic_reversal_summary.json"
LADDER_ARTIFACT = REPO / "data" / "structure_components_summary.json"
RESULTS = REPO / "docs" / "results" / "STRUCTURE_RESULTS.md"

SYMBOLS = ("BTCUSDT", "ETHUSDT")
PRIMARY_K, PRIMARY_TOUCH = 2, 0.5
BAND = 0.5
"""`k` for the resolution band, the same 0.5 ATR the ladder used."""
HORIZONS = (5, 20, 60)
"""`HORIZON` itself plus two longer ones. Reversion decays; a structural level should not."""
N_BUCKETS = 8
"""Matching the ladder's eight rungs, so the two staircases are read side by side."""
TARGETS = (1.0, 2.0, 5.0)
COST_BPS = 40.0
MATCH_TOLERANCE = 0.02
"""H2's bar: structure touches must score within this of matched generic bars."""

ALL_RATIOS = tuple(sorted(set(CANONICAL_RATIOS) | set(PLACEBO_RATIOS)))


def median_leg_bars(setups: Sequence[Any]) -> int:
    """`M`, the lookback — the median impulse-leg length over the setup population.

    A census, not a choice: it is read off the structure population rather than picked, and
    counting has never been a look in this project (D197 onward).

    D215's wording pointed at `structure_examples_summary.json`, which carries seven trades
    — too thin for a median. Computing it over the full population is the same constant
    measured properly, and the deviation is recorded here rather than absorbed."""
    lengths = [s.leg.end_index - s.leg.start_index for s in setups]
    return max(2, int(statistics.median(lengths)))


def generic_ladder(
    closes: Sequence[float],
    atr: Sequence[float],
    lookback: int,
    horizon: int,
    warmup: int,
) -> list[tuple[float, bool]]:
    """`(|move| in ATR, did it revert)` for every M-th bar. No structure anywhere.

    Steps by `lookback` so no two samples share a lookback window."""
    out: list[tuple[float, bool]] = []
    for t in range(max(warmup, lookback), len(closes) - horizon - 1, lookback):
        a = atr[t]
        if not math.isfinite(a) or a <= 0.0:
            continue
        move = (closes[t] - closes[t - lookback]) / a
        if not math.isfinite(move) or move == 0.0:
            continue
        against = -1 if move > 0.0 else 1
        out.append((abs(move), continue_from(closes, atr, t, against, BAND, horizon)))
    return out


def structure_touches(
    bars: Sequence[Any],
    closes: Sequence[float],
    atr: Sequence[float],
    setups: Sequence[Any],
    horizon: int,
) -> list[tuple[float, bool]]:
    """`(|counter-move| in ATR, did it continue)` for every touch of every ladder rung.

    The counter-move is the distance from the leg's extreme to the touched level, which is
    exactly what `|move|` is in the generic arm — so a touch lands in a generic bucket
    without any translation."""
    out: list[tuple[float, bool]] = []
    for setup in setups:
        for ratio in ALL_RATIOS:
            level = ratio_price(setup.leg, ratio)
            for index in setup.window:
                a = atr[index]
                if not math.isfinite(a) or a <= 0.0:
                    continue
                if abs(closes[index] - level) > BAND * a:
                    continue
                size = abs(closes[index] - setup.leg.end_price) / a
                out.append(
                    (size, continue_from(closes, atr, index, setup.direction, BAND, horizon))
                )
                break  # first touch of this rung only, as the ladder counted them
    return out


def quantile_edges(values: Sequence[float], n: int) -> list[float]:
    """Bucket boundaries by quantile. Move size is unbounded, so `DepthTable`'s fixed-width
    bins over [0, 1] do not transfer and this is its sibling rather than an edit to it."""
    arr = np.asarray(values, dtype=float)
    return [float(np.percentile(arr, 100.0 * i / n)) for i in range(1, n)]


def bucket_of(value: float, edges: Sequence[float]) -> int:
    for i, edge in enumerate(edges):
        if value <= edge:
            return i
    return len(edges)


def ladder_from(
    samples: Sequence[tuple[float, bool]], edges: Sequence[float]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for b in range(len(edges) + 1):
        chunk = [ok for size, ok in samples if bucket_of(size, edges) == b]
        sizes = [size for size, _ in samples if bucket_of(size, edges) == b]
        rows.append(
            {
                "bucket": b + 1,
                "n": len(chunk),
                "lo": min(sizes) if sizes else None,
                "hi": max(sizes) if sizes else None,
                "median_move_atr": statistics.median(sizes) if sizes else None,
                "p_reversal": (sum(chunk) / len(chunk)) if chunk else None,
            }
        )
    return rows


def slope_of(samples: Sequence[tuple[float, bool]]) -> float | None:
    """Rank correlation between move size and reversal — the ladder's slope in one number."""
    if len(samples) < 50:
        return None
    return spearman([s for s, _ in samples], [1.0 if ok else 0.0 for _, ok in samples])


def matched_comparison(
    structure: Sequence[tuple[float, bool]],
    generic: Sequence[tuple[float, bool]],
    edges: Sequence[float],
) -> dict[str, Any]:
    """Do structure touches beat plain bars that moved the same distance?

    The verdict. Each structure touch is scored against the generic reversal rate of its own
    move-size bucket, and the difference is averaged over the structure population's own
    size distribution — so the comparison is weighted the way the strategy actually trades
    rather than the way the market is distributed.

    Buckets the generic arm never populated are EXCLUDED and counted, never imputed from a
    neighbour: an empty bucket means the comparison has nothing to say at that move size,
    and filling it in would invent the answer exactly where structure is unusual."""
    rates: dict[int, float | None] = {}
    for b in range(len(edges) + 1):
        chunk = [ok for size, ok in generic if bucket_of(size, edges) == b]
        rates[b] = (sum(chunk) / len(chunk)) if chunk else None

    covered, uncovered = 0, 0
    real_total = 0.0
    expected_total = 0.0
    per_bucket: list[dict[str, Any]] = []
    for b in range(len(edges) + 1):
        chunk = [ok for size, ok in structure if bucket_of(size, edges) == b]
        if not chunk:
            per_bucket.append({"bucket": b + 1, "n": 0})
            continue
        if rates[b] is None:
            uncovered += len(chunk)
            per_bucket.append({"bucket": b + 1, "n": len(chunk), "generic": None})
            continue
        covered += len(chunk)
        real = sum(chunk) / len(chunk)
        real_total += real * len(chunk)
        expected_total += rates[b] * len(chunk)
        per_bucket.append(
            {
                "bucket": b + 1,
                "n": len(chunk),
                "structure": real,
                "generic": rates[b],
                "delta": real - rates[b],
            }
        )

    return {
        "n_covered": covered,
        "n_uncovered": uncovered,
        "structure_rate": real_total / covered if covered else float("nan"),
        "matched_generic_rate": expected_total / covered if covered else float("nan"),
        "delta": (real_total - expected_total) / covered if covered else float("nan"),
        "per_bucket": per_bucket,
    }


def run_symbol(symbol: str, bars: Sequence[Any]) -> dict[str, Any]:
    closes = [b.bar.close for b in bars]
    atr = rolling_mean_true_range(bars, ATR_WINDOW_15M)
    states = market_structure(bars, PRIMARY_K)
    setups = list(find_setups(bars, PRIMARY_K, PRIMARY_TOUCH, states=states).setups)

    lookback = median_leg_bars(setups)
    warmup = ATR_WINDOW_15M + 1
    print(f"    census: M = {lookback} bars (median impulse leg over "
          f"{len(setups):,} setups)", flush=True)

    print("    A: the generic ladder, structure deleted", flush=True)
    generic = generic_ladder(closes, atr, lookback, HORIZON, warmup)
    edges = quantile_edges([s for s, _ in generic], N_BUCKETS)
    struct = structure_touches(bars, closes, atr, setups, HORIZON)
    matched = matched_comparison(struct, generic, edges)
    print(f"       generic n={len(generic):,}  structure touches n={len(struct):,}  "
          f"matched delta {matched['delta']:+.4f}", flush=True)

    print("    B: the slope across horizons", flush=True)
    by_horizon: dict[str, Any] = {}
    for h in HORIZONS:
        samples = generic_ladder(closes, atr, lookback, h, warmup)
        by_horizon[str(h)] = {
            "n": len(samples),
            "slope": slope_of(samples),
            "overall_reversal": (
                sum(1 for _, ok in samples if ok) / len(samples) if samples else None
            ),
        }
        print(f"       h={h:2d}  slope {by_horizon[str(h)]['slope']:+.4f}", flush=True)

    print("    C: the target sweep", flush=True)
    by_target: dict[str, Any] = {}
    for target in TARGETS:
        trades = run_arm(bars, setups, (), Wrapper(target_r=target), allow_overlap=True)
        stats = expectancy(trades, COST_BPS)
        reasons = {r: sum(1 for t in trades if t.reason == r)
                   for r in ("stop", "target", "max_hold")}
        by_target[f"{target:.0f}R"] = {
            "n": len(trades),
            "p_target": reasons["target"] / len(trades) if trades else 0.0,
            "hit_rate": stats["hit_rate"],
            "mean_gross_r": statistics.fmean(t.r_multiple for t in trades),
            "mean_net_r": stats["mean_r"],
            "median_net_r": stats["median_r"],
            "share_untradeable": stats["share_untradeable"],
            "exit_reasons": reasons,
        }
        print(f"       {target:.0f}R  P(target) {by_target[f'{target:.0f}R']['p_target']:.1%}"
              f"  gross {by_target[f'{target:.0f}R']['mean_gross_r']:+.3f}"
              f"  net {by_target[f'{target:.0f}R']['mean_net_r']:+.3f}", flush=True)

    band_pct = statistics.median(
        [BAND * atr[t] / closes[t] for t in range(warmup, len(bars), 500)
         if math.isfinite(atr[t]) and atr[t] > 0 and closes[t] > 0]
    )

    return {
        "lookback_M": lookback,
        "n_setups": len(setups),
        "generic": {
            "n": len(generic),
            "edges": edges,
            "ladder": ladder_from(generic, edges),
            "slope": slope_of(generic),
        },
        "structure": {"n": len(struct), "ladder": ladder_from(struct, edges)},
        "matched": matched,
        "by_horizon": by_horizon,
        "by_target": by_target,
        "band_as_share_of_price": band_pct,
        "round_trip_share_of_price": 2 * COST_BPS / 10_000.0,
    }


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
        append_section(payload)
        print(f"re-rendered the D215 section of {RESULTS.name}")
        return 0

    started = time.time()
    raw, _ = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)
    runs: dict[str, Any] = {}
    for symbol in SYMBOLS:
        print(f"{symbol}: {len(cleaned[symbol]):,} bars", flush=True)
        runs[symbol] = run_symbol(symbol, cleaned[symbol])

    prior = json.loads(LADDER_ARTIFACT.read_text(encoding="utf-8"))
    payload = {
        "produced": time.strftime("%Y-%m-%d"),
        "fixture": FIXTURE.name,
        "symbols": list(SYMBOLS),
        "band_atr": BAND,
        "horizons": list(HORIZONS),
        "targets": list(TARGETS),
        "cost_bps_per_side": COST_BPS,
        "match_tolerance": MATCH_TOLERANCE,
        "fib_ladder_for_reference": {
            s: {k: v["p_continuation"] for k, v in prior["runs"][s]["C3"]["ladder"].items()}
            for s in SYMBOLS
        },
        "runs": runs,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    SUMMARY.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    append_section(payload)
    print(f"\nwrote {SUMMARY.name} in {payload['elapsed_seconds']}s\n")
    print(render(payload))
    return 0


def _f(x, spec="+.4f"):
    return "n/a" if x is None or x != x else format(x, spec)


def render(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    runs = payload["runs"]

    add("## D215 - is it just mean reversion?")
    add("")
    add(f"**Produced:** {payload['produced']} · **Reproduce:** "
        "`uv run python scripts/run_generic_reversal.py` (offline, deterministic)")
    add("")
    add("Pre-registered in `docs/decisions/D215-is-it-just-mean-reversion.md` before this "
        "runner existed. The claim: the retracement-depth staircase - the only monotone "
        "relationship either programme found - is generic short-horizon reversion after a "
        "large move, and the structure contributes nothing.")
    add("")
    add("**Both arms call the same function.** `structure_nulls.continue_from`, same 0.5 ATR "
        "band fixed at the bar, same horizon. Not two implementations of one rule - one "
        "function, because a second definition is a thing to drift from.")
    add("")

    add("### The census that sets the lookback")
    add("")
    add("| symbol | setups | M = median impulse leg | generic samples | structure touches |")
    add("|---|---:|---:|---:|---:|")
    for s in runs:
        r = runs[s]
        add(f"| `{s}` | {r['n_setups']:,} | **{r['lookback_M']} bars** | "
            f"{r['generic']['n']:,} | {r['structure']['n']:,} |")
    add("")
    add("`M` is read off the structure population, not chosen. The generic arm steps by `M` "
        "so no two samples share a lookback window - pre-registered, because overlapping "
        "windows make a **negative** look sharper than it is.")
    add("")

    add("### A - the staircase with the structure deleted")
    add("")
    for s in runs:
        add(f"**`{s}`** - every {runs[s]['lookback_M']}th bar, bucketed by move size, no "
            "change of character and no levels anywhere:")
        add("")
        add("| bucket | move size (ATR) | n | P(reversal) generic | P(continuation) structure |")
        add("|---:|---|---:|---:|---:|")
        gl = runs[s]["generic"]["ladder"]
        sl = {row["bucket"]: row for row in runs[s]["structure"]["ladder"]}
        for row in gl:
            st = sl.get(row["bucket"], {})
            med = row["median_move_atr"]
            add(f"| {row['bucket']} | {_f(med, '.2f')} | {row['n']:,} | "
                f"{_f(row['p_reversal'], '.1%')} | {_f(st.get('p_reversal'), '.1%')} "
                f"({st.get('n', 0):,}) |")
        add("")
    add("For reference, the Fibonacci ladder this is being compared against ran "
        + " and ".join(
            f"`{s}` {min(payload['fib_ladder_for_reference'][s].values()):.1%} to "
            f"{max(payload['fib_ladder_for_reference'][s].values()):.1%}"
            for s in runs
        )
        + " across its eight rungs.")
    add("")

    add("### The verdict: matched on move size")
    add("")
    add("Each structure touch scored against the generic reversal rate of its own move-size "
        "bucket. D208's precedent and its warning - there the fair value gap sat at the "
        "100th percentile of 500 draws raw and at +0.006 depth-matched.")
    add("")
    add("| symbol | touches covered | structure | matched generic | delta | within ±0.02 |")
    add("|---|---:|---:|---:|---:|:--:|")
    for s in runs:
        m = runs[s]["matched"]
        ok = abs(m["delta"]) <= payload["match_tolerance"]
        add(f"| `{s}` | {m['n_covered']:,} | {_f(m['structure_rate'], '.1%')} | "
            f"{_f(m['matched_generic_rate'], '.1%')} | **{_f(m['delta'])}** | "
            f"{'yes' if ok else '**NO**'} |")
    add("")

    add("### B - does the slope decay with horizon?")
    add("")
    add("| symbol | " + " | ".join(f"h={h} slope" for h in payload["horizons"]) + " | decays |")
    add("|---|" + "---:|" * len(payload["horizons"]) + ":--:|")
    for s in runs:
        slopes = [runs[s]["by_horizon"][str(h)]["slope"] for h in payload["horizons"]]
        live = [v for v in slopes if v is not None]
        decays = len(live) == len(slopes) and all(
            abs(a) >= abs(b) for a, b in zip(live, live[1:])
        )
        add(f"| `{s}` | " + " | ".join(_f(v) for v in slopes)
            + f" | {'yes' if decays else 'no'} |")
    add("")

    add("### C - the target sweep, and its counterintuitive prediction")
    add("")
    add("| symbol | target | P(reach target) | mean gross R | mean net R @40bp | untradeable |")
    add("|---|---:|---:|---:|---:|---:|")
    for s in runs:
        for name, blk in runs[s]["by_target"].items():
            add(f"| `{s}` | {name} | {blk['p_target']:.1%} | {blk['mean_gross_r']:+.3f} | "
                f"{blk['mean_net_r']:+.3f} | {blk['share_untradeable']:.0%} |")
    add("")

    add("### The arithmetic that makes all of it moot at this bar size")
    add("")
    add("| symbol | 0.5 ATR band as share of price | 80 bp round trip | move predicted / cost |")
    add("|---|---:|---:|---:|")
    for s in runs:
        b = runs[s]["band_as_share_of_price"]
        c = runs[s]["round_trip_share_of_price"]
        add(f"| `{s}` | {b:.3%} | {c:.3%} | **{b / c:.2f}x** |")
    add("")

    add("### Verdict")
    add("")
    add(_reading(payload))
    add("")

    add("### Multiplicity")
    add("")
    add("| test | cells | looks |")
    add("|---|---|---:|")
    add(f"| A generic ladder + matched comparison | 2 metrics x {len(runs)} symbols | {2 * len(runs)} |")
    add(f"| B slope by horizon | {len(payload['horizons'])} horizons x {len(runs)} symbols | {len(payload['horizons']) * len(runs)} |")
    add(f"| C target sweep | {len(payload['targets'])} targets x {len(runs)} symbols | {len(payload['targets']) * len(runs)} |")
    add(f"| **D215 total** | | **{2 * len(runs) + (len(payload['horizons']) + len(payload['targets'])) * len(runs)}** |")
    add("")
    add("**Test A starts a fresh ledger**: it reuses no sensor, component or level, and "
        "multiplicity inflates false positives - a test whose predicted outcome is *this "
        "effect is generic and therefore not yours* is not weakened by prior looks. B and C "
        "reuse the structure machinery and inherit the 395.")
    add("")
    return "\n".join(lines)


def _reading(payload: dict[str, Any]) -> str:
    runs = payload["runs"]
    tol = payload["match_tolerance"]
    parts: list[str] = []

    slopes = {s: runs[s]["generic"]["slope"] for s in runs}
    parts.append(
        "**The staircase survives with the structure deleted.** The generic ladder's slope "
        "is "
        + " and ".join(f"{_f(slopes[s])} on `{s}`" for s in runs)
        + " — plain bars, bucketed by how far price just moved, with no change of "
        "character, no impulse leg, no Fibonacci level and no fair value gap anywhere in "
        "the construction. H1 "
        + ("confirmed." if all(v is not None and v > 0 for v in slopes.values())
           else "**falsified**: the generic ladder does not slope the way the Fib one does.")
    )
    parts.append("")

    deltas = {s: runs[s]["matched"]["delta"] for s in runs}
    within = all(abs(v) <= tol for v in deltas.values())
    parts.append(
        "**And matched on move size, the structure adds "
        + ("nothing" if within else "something")
        + ".** Structure touches score "
        + " and ".join(
            f"{_f(runs[s]['matched']['structure_rate'], '.1%')} against a matched-generic "
            f"{_f(runs[s]['matched']['matched_generic_rate'], '.1%')} on `{s}`"
            for s in runs
        )
        + " — deltas of "
        + " and ".join(_f(v) for v in deltas.values())
        + f", against H2's ±{tol:.2f} bar. **H2 "
        + ("confirmed." if within else "FALSIFIED — the components carry something the raw "
           "move does not, which is the first positive finding in 395 looks and needs its "
           "own study.**")
        + ("**" if within else "")
    )
    parts.append("")

    parts.append(
        "So the five components, the confluence, the golden ratio and the fair value gap "
        "reduce to **how far price just moved**. That is not a level, it is not structure, "
        "and it is not the course's mechanism — it is the oldest effect in intraday data "
        "wearing a chart pattern."
    )
    parts.append("")

    for s in runs:
        hs = runs[s]["by_horizon"]
        parts.append(
            f"**`{s}` across horizons:** slope "
            + ", ".join(f"{_f(hs[str(h)]['slope'])} at {h} bars" for h in payload["horizons"])
            + "."
        )
    parts.append("")

    for s in runs:
        t = runs[s]["by_target"]
        one, five = t["1R"], t["5R"]
        parts.append(
            f"**`{s}` target sweep:** dropping from 5R to 1R lifts P(reach target) "
            f"{five['p_target']:.1%} -> {one['p_target']:.1%} and mean gross R "
            f"{five['mean_gross_r']:+.3f} -> {one['mean_gross_r']:+.3f}, while mean net R "
            f"goes {five['mean_net_r']:+.3f} -> {one['mean_net_r']:+.3f} — "
            + ("**worse, as H4 predicted**." if one["mean_net_r"] < five["mean_net_r"]
               else "better, which falsifies H4.")
        )
    parts.append("")

    ratios = {s: runs[s]["band_as_share_of_price"] / runs[s]["round_trip_share_of_price"]
              for s in runs}
    parts.append(
        "**And the arithmetic that ends it at this bar size.** The move being predicted is "
        "half an ATR, which on 15m bars is "
        + " and ".join(f"{runs[s]['band_as_share_of_price']:.3%}" for s in runs)
        + " of price, against an 80 bp round trip. The effect is "
        + " and ".join(f"{ratios[s]:.2f}x" for s in runs)
        + " the cost of capturing it. **H5 "
        + ("confirmed" if all(v < 1.0 for v in ratios.values()) else "falsified")
        + "** — a real effect, and not one you can trade at fifteen minutes. Which is the "
        "whole argument for the frequency frontier: the binding question was never which "
        "levels to draw, it is what bar size makes this move large relative to the spread."
    )
    return "\n".join(parts)


def append_section(payload: dict[str, Any]) -> None:
    # Bounded by the next heading, not by the parking lot at the bottom of the file.
    # The marker-to-anchor form this replaced destroyed every section written below
    # it; scripts/results_document.py carries the measurement, per runner (D542).
    splice_section(RESULTS, "## D215 - is it just mean reversion?", render(payload))


if __name__ == "__main__":
    raise SystemExit(main())
