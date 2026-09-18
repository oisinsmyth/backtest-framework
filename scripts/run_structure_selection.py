"""D213 — mine a selection rule on one year, then carry it to the seven it never saw.

    uv run python scripts/run_structure_selection.py
    uv run python scripts/run_structure_selection.py --report-only

The pre-registration is `docs/decisions/D213-conditional-selection-on-a-held-out-year.md`
and it governs everything here. Read it first: the design's primary output is not a filter,
it is a measurement of how much in-sample selection flatters, and the shuffled-outcome
control is what makes the other two numbers mean anything.

## Three things this file is careful about

**The development year is chosen by count, not by outcome.** The earliest full calendar
year in which both symbols carry at least 200 base-arm trades. Counting is a census; this
project has drawn that line since D197.

**Thresholds are frozen at the dev year's medians.** Re-taking the median inside each
holdout year would let the rule adapt to data it is supposed to be tested on — the
quietest form of leakage available here, because the result still looks like a holdout.

**Mining runs on gross R, never net.** Cost divided by a four-basis-point stop runs past
20R, so mining on net R would be a search for wide stops wearing a search for signal. Costs
are applied to the verdict afterwards and never to the search.
"""

from __future__ import annotations

import json
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
from backtest_framework.research.structure import (  # noqa: E402
    RSI_WINDOW,
    market_structure,
    retracement,
    rsi,
)
from backtest_framework.research.structure_setups import (  # noqa: E402
    ATR_WINDOW_15M,
    find_setups,
)
from backtest_framework.research.structure_strategies import (  # noqa: E402
    Wrapper,
    r_multiples,
    run_arm,
)
from backtest_framework.research.terrain import rolling_mean_true_range  # noqa: E402
from results_document import splice_section  # noqa: E402

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "structure_selection_summary.json"
RESULTS = REPO / "docs" / "results" / "STRUCTURE_RESULTS.md"

SYMBOLS = ("BTCUSDT", "ETHUSDT")
PRIMARY_K, PRIMARY_TOUCH = 2, 0.5
COST_BPS = 40.0
MIN_DEV_TRADES = 200
"""Trades a year must carry, on BOTH symbols, to be eligible as the development year."""

FEATURES = (
    "fib_depth",
    "stop_atr",
    "rsi",
    "bars_waited",
    "hour_utc",
    "trend_align",
    "leg_bars",
    "vol_regime",
)
"""The eight named in D213. A ninth thought of after the run would be a ninth look."""

EDGE = 0.10
"""Mean gross R a median split must gain to keep its feature. Pre-registered."""
N_SHUFFLES, SEED = 200, 0
TREND_WINDOW = 200
"""Bars of close average defining "the trend" for `trend_align`."""


def rolling_mean(values: Sequence[float], window: int) -> list[float]:
    """Causal simple mean; NaN until the window is full."""
    out = [float("nan")] * len(values)
    total = 0.0
    for i, v in enumerate(values):
        total += v
        if i >= window:
            total -= values[i - window]
        if i >= window - 1:
            out[i] = total / window
    return out


def build(symbol: str, bars: Sequence[Any]) -> list[dict[str, Any]]:
    """Every base-arm trade with its eight features and its year."""
    atr = rolling_mean_true_range(bars, ATR_WINDOW_15M)
    strength = rsi(bars, RSI_WINDOW)
    closes = [b.bar.close for b in bars]
    sma = rolling_mean(closes, TREND_WINDOW)
    atr_np = np.asarray(atr, dtype=float)

    states = market_structure(bars, PRIMARY_K)
    setups = list(find_setups(bars, PRIMARY_K, PRIMARY_TOUCH, states=states).setups)
    trades = run_arm(bars, setups, (), Wrapper(), allow_overlap=True)
    nets = r_multiples(trades, COST_BPS)

    rows: list[dict[str, Any]] = []
    for trade, net in zip(trades, nets):
        setup = setups[trade.setup_index]
        s = trade.entry_index - 1
        a = atr[s]
        if not (a == a) or a <= 0.0:
            continue
        depth = retracement(setup.leg, closes[s])
        if depth is None or not (sma[s] == sma[s]):
            continue
        lo = max(0, s - ATR_WINDOW_15M + 1)
        window = atr_np[lo : s + 1]
        window = window[np.isfinite(window)]
        if window.size == 0:
            continue
        median_atr = float(np.median(window))
        if median_atr <= 0.0:
            continue
        trend = 1.0 if closes[s] > sma[s] else -1.0
        rows.append(
            {
                "symbol": symbol,
                "year": bars[trade.entry_index].timestamp.year,
                "gross_r": trade.r_multiple,
                "net_r": net,
                "fib_depth": depth,
                "stop_atr": trade.risk / a,
                "rsi": strength[s] if strength[s] == strength[s] else 50.0,
                "bars_waited": float(s - setup.choch_index),
                "hour_utc": float(bars[s].timestamp.hour),
                "trend_align": float(trade.direction) * trend,
                "leg_bars": float(setup.leg.end_index - setup.leg.start_index),
                "vol_regime": a / median_atr,
            }
        )
    return rows


def median_split(rows: Sequence[dict[str, Any]], feature: str, target: str = "gross_r"):
    """`(threshold, above_mean, below_mean, better_side, edge)` for one feature."""
    values = [r[feature] for r in rows]
    threshold = statistics.median(values)
    above = [r[target] for r in rows if r[feature] > threshold]
    below = [r[target] for r in rows if r[feature] <= threshold]
    if len(above) < 20 or len(below) < 20:
        return None
    ma, mb = statistics.fmean(above), statistics.fmean(below)
    side = "above" if ma > mb else "below"
    return {
        "feature": feature,
        "threshold": threshold,
        "mean_above": ma,
        "mean_below": mb,
        "n_above": len(above),
        "n_below": len(below),
        "better_side": side,
        "edge": abs(ma - mb),
    }


def passes(row: dict[str, Any], rule: Sequence[dict[str, Any]]) -> bool:
    for clause in rule:
        value = row[clause["feature"]]
        ok = value > clause["threshold"] if clause["better_side"] == "above" else value <= clause["threshold"]
        if not ok:
            return False
    return True


def mine(dev_by_symbol: dict[str, list[dict[str, Any]]], target: str = "gross_r"):
    """The whole procedure, so the shuffled control can run it identically."""
    splits: dict[str, dict[str, Any]] = {}
    for symbol, rows in dev_by_symbol.items():
        for feature in FEATURES:
            got = median_split(rows, feature, target)
            if got is not None:
                splits[f"{symbol}|{feature}"] = got

    survivors: list[dict[str, Any]] = []
    per_feature: dict[str, Any] = {}
    for feature in FEATURES:
        cells = [splits.get(f"{s}|{feature}") for s in SYMBOLS]
        if any(c is None for c in cells):
            continue
        sides = {c["better_side"] for c in cells}
        edges = [c["edge"] for c in cells]
        agreed = len(sides) == 1
        kept = agreed and all(e >= EDGE for e in edges)
        per_feature[feature] = {
            "cells": {s: splits[f"{s}|{feature}"] for s in SYMBOLS},
            "sides_agree": agreed,
            "min_edge": min(edges),
            "kept": kept,
        }
        if kept:
            # One clause per symbol: the threshold is that symbol's own dev-year median,
            # frozen here and never recomputed on a holdout year.
            for s in SYMBOLS:
                survivors.append({**splits[f"{s}|{feature}"], "symbol": s})
    return per_feature, survivors


def rule_for(survivors: Sequence[dict[str, Any]], symbol: str) -> list[dict[str, Any]]:
    return [c for c in survivors if c["symbol"] == symbol]


def evaluate(rows: Sequence[dict[str, Any]], rule: Sequence[dict[str, Any]]) -> dict[str, Any]:
    kept = [r for r in rows if passes(r, rule)] if rule else list(rows)
    if not rows:
        return {"n": 0}
    return {
        "n_all": len(rows),
        "n_kept": len(kept),
        "share_kept": len(kept) / len(rows),
        "mean_gross_r_all": statistics.fmean(r["gross_r"] for r in rows),
        "mean_gross_r_kept": statistics.fmean(r["gross_r"] for r in kept) if kept else float("nan"),
        "mean_net_r_all": statistics.fmean(r["net_r"] for r in rows),
        "mean_net_r_kept": statistics.fmean(r["net_r"] for r in kept) if kept else float("nan"),
        "advantage": (
            statistics.fmean(r["gross_r"] for r in kept)
            - statistics.fmean(r["gross_r"] for r in rows)
            if kept
            else float("nan")
        ),
    }


def shuffled_control(
    dev_by_symbol: dict[str, list[dict[str, Any]]], n: int, seed: int
) -> dict[str, Any]:
    """Run the identical mining procedure on outcomes shuffled within the dev year.

    This is the number that makes the other two interpretable. If the real in-sample
    advantage sits inside this distribution, the mining found a selection effect and not a
    signal — and the design says so directly rather than by argument.

    Shuffled WITHIN symbol and within the dev year, so every marginal distribution the
    procedure could exploit is preserved and only the pairing between features and outcome
    is destroyed."""
    rng = np.random.default_rng(seed)
    advantages: list[float] = []
    survivor_counts: list[int] = []
    for _ in range(n):
        fake: dict[str, list[dict[str, Any]]] = {}
        for symbol, rows in dev_by_symbol.items():
            values = [r["gross_r"] for r in rows]
            order = rng.permutation(len(values))
            fake[symbol] = [
                {**row, "gross_r": values[order[i]]} for i, row in enumerate(rows)
            ]
        _, survivors = mine(fake)
        survivor_counts.append(len({c["feature"] for c in survivors}))
        if not survivors:
            advantages.append(0.0)
            continue
        gains = []
        for symbol, rows in fake.items():
            got = evaluate(rows, rule_for(survivors, symbol))
            if got.get("n_kept"):
                gains.append(got["advantage"])
        advantages.append(statistics.fmean(gains) if gains else 0.0)
    arr = np.asarray(advantages, dtype=float)
    return {
        "n_draws": n,
        "mean": float(arr.mean()),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "max": float(arr.max()),
        "mean_survivors": float(statistics.fmean(survivor_counts)),
        "share_with_a_survivor": float(sum(1 for c in survivor_counts if c) / len(survivor_counts)),
    }


def binary_split(rows: Sequence[dict[str, Any]], feature: str) -> dict[str, Any] | None:
    """Split a +/-1 feature at zero rather than at its median.

    `trend_align` was pre-registered and then never tested: a median split on a binary
    puts the median AT one of the two values, so one side comes back empty and
    `median_split` returns None on its own thinness guard. It vanished from the results
    table without appearing as a failure.

    That is D196's H4 exactly — every S5b strategy read level prices and never the score,
    so ten cells came back bit-identical and the sensor was never tested at all. Caught
    here the same way, by checking which keys the output actually contains rather than
    trusting that eight features in means eight features out.

    Run as a STANDALONE test and deliberately not folded back into the mined rule: the rule
    was frozen before this ran, and re-mining it now — after seeing which way the holdout
    went — is precisely the move the whole design exists to prevent."""
    on = [r["gross_r"] for r in rows if r[feature] > 0]
    off = [r["gross_r"] for r in rows if r[feature] <= 0]
    if len(on) < 20 or len(off) < 20:
        return None
    return {
        "n_aligned": len(on),
        "n_against": len(off),
        "mean_aligned": statistics.fmean(on),
        "mean_against": statistics.fmean(off),
        "edge": statistics.fmean(on) - statistics.fmean(off),
    }


def pick_dev_year(by_symbol: dict[str, list[dict[str, Any]]]) -> tuple[int, dict[str, Any]]:
    """Earliest full calendar year with >= MIN_DEV_TRADES on BOTH symbols.

    A census, not a look: no outcome is consulted, only counts."""
    counts: dict[int, dict[str, int]] = {}
    for symbol, rows in by_symbol.items():
        for r in rows:
            counts.setdefault(r["year"], {}).setdefault(symbol, 0)
            counts[r["year"]][symbol] += 1
    eligible = sorted(
        y
        for y, per in counts.items()
        if all(per.get(s, 0) >= MIN_DEV_TRADES for s in SYMBOLS)
    )
    if not eligible:
        raise SystemExit("no year carries enough trades on both symbols")
    return eligible[0], {str(y): counts[y] for y in sorted(counts)}


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
        append_section(payload)
        print(f"re-rendered the D213 section of {RESULTS.name}")
        return 0

    started = time.time()
    raw, _ = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)

    by_symbol: dict[str, list[dict[str, Any]]] = {}
    for symbol in SYMBOLS:
        print(f"{symbol}: building base-arm trades", flush=True)
        by_symbol[symbol] = build(symbol, cleaned[symbol])
        print(f"  {len(by_symbol[symbol]):,} trades with full features", flush=True)

    dev_year, census = pick_dev_year(by_symbol)
    print(f"\ndevelopment year (by count, outcome-blind): {dev_year}", flush=True)

    dev = {s: [r for r in rows if r["year"] == dev_year] for s, rows in by_symbol.items()}
    hold = {s: [r for r in rows if r["year"] != dev_year] for s, rows in by_symbol.items()}

    print("mining the dev year", flush=True)
    per_feature, survivors = mine(dev)
    kept = sorted({c["feature"] for c in survivors})
    print(f"  survivors: {kept or 'none'}", flush=True)

    in_sample = {s: evaluate(dev[s], rule_for(survivors, s)) for s in SYMBOLS}
    out_sample = {s: evaluate(hold[s], rule_for(survivors, s)) for s in SYMBOLS}
    by_year = {
        s: {
            str(y): evaluate(
                [r for r in hold[s] if r["year"] == y], rule_for(survivors, s)
            )
            for y in sorted({r["year"] for r in hold[s]})
        }
        for s in SYMBOLS
    }

    print("testing trend_align on its own (binary split, D213 amendment)", flush=True)
    trend = {
        s_: {
            "dev": binary_split(dev[s_], "trend_align"),
            "holdout": binary_split(hold[s_], "trend_align"),
        }
        for s_ in SYMBOLS
    }

    print(f"running {N_SHUFFLES} shuffled-outcome controls", flush=True)
    control = shuffled_control(dev, N_SHUFFLES, SEED)

    real_in = statistics.fmean(
        in_sample[s]["advantage"] for s in SYMBOLS if in_sample[s].get("n_kept")
    ) if any(in_sample[s].get("n_kept") for s in SYMBOLS) else float("nan")

    payload = {
        "produced": time.strftime("%Y-%m-%d"),
        "fixture": FIXTURE.name,
        "symbols": list(SYMBOLS),
        "dev_year": dev_year,
        "trades_by_year": census,
        "features": list(FEATURES),
        "edge_bar": EDGE,
        "cost_bps_per_side": COST_BPS,
        "per_feature": per_feature,
        "survivors": kept,
        "rule": {s: rule_for(survivors, s) for s in SYMBOLS},
        "in_sample": in_sample,
        "out_of_sample": out_sample,
        "out_of_sample_by_year": by_year,
        "trend_align_standalone": trend,
        "shuffled_control": control,
        "real_in_sample_advantage": real_in,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    SUMMARY.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    append_section(payload)
    print(f"\nwrote {SUMMARY.name} in {payload['elapsed_seconds']}s\n")
    print(render(payload))
    return 0


def _pct(x: float) -> str:
    return "n/a" if x != x else f"{x:+.3f}"


def render(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    dev = payload["dev_year"]

    add("## D213 - can selection rescue it? A mined rule on a held-out seven years")
    add("")
    add(f"**Produced:** {payload['produced']} · **Reproduce:** "
        "`uv run python scripts/run_structure_selection.py` (offline, deterministic)")
    add("")
    add(f"Pre-registered in `docs/decisions/D213-conditional-selection-on-a-held-out-year.md` "
        f"before the mining ran. Development year **{dev}**, chosen by trade count on both "
        "symbols before any outcome was read; every later number excludes it entirely. "
        "Mining runs on **gross** R - cost divided by a four-basis-point stop runs past 20R, "
        "so mining on net R would be a search for wide stops wearing a search for signal.")
    add("")

    add("### Trades by year, and the year the rule was mined from")
    add("")
    add("| year | " + " | ".join(f"`{s}`" for s in payload["symbols"]) + " | role |")
    add("|---|---:|---:|---|")
    for year, per in payload["trades_by_year"].items():
        role = "**development**" if int(year) == dev else "held out"
        cells = " | ".join(str(per.get(s, 0)) for s in payload["symbols"])
        add(f"| {year} | {cells} | {role} |")
    add("")

    add(f"### What the {dev} data said about each feature")
    add("")
    add("Median split, no threshold search. A feature is kept only if the same side wins on "
        f"**both** symbols and gains at least **{payload['edge_bar']:.2f}R** on each.")
    add("")
    add("| feature | better side | " + " | ".join(f"`{s}` edge (R)" for s in payload["symbols"]) + " | sides agree | kept |")
    add("|---|---|---:|---:|:--:|:--:|")
    for feature in payload["features"]:
        block = payload["per_feature"].get(feature)
        if block is None:
            add(f"| {feature} | — | — | — | — | too thin |")
            continue
        sides = {payload["per_feature"][feature]["cells"][s]["better_side"] for s in payload["symbols"]}
        side = list(sides)[0] if len(sides) == 1 else "split"
        edges = " | ".join(
            f"{block['cells'][s]['edge']:.3f}" for s in payload["symbols"]
        )
        add(f"| {feature} | {side} | {edges} | "
            f"{'yes' if block['sides_agree'] else 'no'} | "
            f"{'**KEPT**' if block['kept'] else 'no'} |")
    add("")
    add(f"Survivors: **{', '.join(payload['survivors']) if payload['survivors'] else 'none'}**.")
    add("")

    if payload["survivors"]:
        add("### The frozen rule, in sample and out")
        add("")
        add("Thresholds are the development year's medians and are **not** recomputed on any "
            "holdout year - re-taking the median inside the test data is the quietest form "
            "of leakage available, because the result still looks like a holdout.")
        add("")
        add("| symbol | sample | trades | kept | mean gross R (all) | mean gross R (kept) | advantage | mean net R (kept) |")
        add("|---|---|---:|---:|---:|---:|---:|---:|")
        for s in payload["symbols"]:
            for label, key in ((f"{dev} (in sample)", "in_sample"),
                               ("all other years (held out)", "out_of_sample")):
                b = payload[key][s]
                add(f"| `{s}` | {label} | {b['n_all']:,} | {b['share_kept']:.0%} | "
                    f"{b['mean_gross_r_all']:+.3f} | {_pct(b['mean_gross_r_kept'])} | "
                    f"{_pct(b['advantage'])} | {_pct(b['mean_net_r_kept'])} |")
        add("")

        add("### The same rule, year by year on the holdout")
        add("")
        add("| symbol | " + " | ".join(sorted(payload["out_of_sample_by_year"][payload["symbols"][0]])) + " |")
        add("|---|" + "---:|" * len(payload["out_of_sample_by_year"][payload["symbols"][0]]))
        for s in payload["symbols"]:
            cells = " | ".join(
                _pct(payload["out_of_sample_by_year"][s][y]["advantage"])
                for y in sorted(payload["out_of_sample_by_year"][s])
            )
            add(f"| `{s}` | {cells} |")
        add("")
        add("Advantage in mean gross R of the filtered trades over all trades, that year.")
        add("")

    add("### The feature that was never tested, tested")
    add("")
    add("`trend_align` was pre-registered and then silently dropped: a median split on a "
        "+/-1 variable puts the median at one of the two values, so one side comes back "
        "empty and the thinness guard removes the feature. It disappeared from the table "
        "above without appearing as a failure - D196's H4 in a new costume, caught by "
        "checking which keys the output contains rather than trusting that eight features "
        "in means eight features out.")
    add("")
    add("Split at zero instead, and run **standalone**: the mined rule was frozen before "
        "this ran and is deliberately not re-mined to include it, because re-mining after "
        "seeing the holdout is the move the whole design exists to prevent.")
    add("")
    add("| symbol | sample | with the trend | against it | edge (R) |")
    add("|---|---|---:|---:|---:|")
    for sym in payload["symbols"]:
        for label, key in ((f"{dev} (dev)", "dev"), ("held out", "holdout")):
            blk = payload["trend_align_standalone"][sym][key]
            if blk is None:
                add(f"| `{sym}` | {label} | — | — | too thin |")
                continue
            add(f"| `{sym}` | {label} | {blk['mean_aligned']:+.3f} "
                f"({blk['n_aligned']:,}) | {blk['mean_against']:+.3f} "
                f"({blk['n_against']:,}) | {blk['edge']:+.3f} |")
    add("")

    add("### The control that makes those numbers readable")
    add("")
    c = payload["shuffled_control"]
    add(f"The identical mining procedure, run {c['n_draws']} times on the same {dev} trades "
        "with the outcomes **shuffled within symbol** - every marginal distribution "
        "preserved, only the pairing between feature and outcome destroyed.")
    add("")
    add("| | value |")
    add("|---|---:|")
    add(f"| draws that produced at least one survivor | {c['share_with_a_survivor']:.0%} |")
    add(f"| mean survivors per draw | {c['mean_survivors']:.2f} |")
    add(f"| median in-sample advantage from pure noise | {c['p50']:+.3f}R |")
    add(f"| 95th percentile | {c['p95']:+.3f}R |")
    add(f"| largest in {c['n_draws']} draws | {c['max']:+.3f}R |")
    add(f"| **the real rule's in-sample advantage** | **{_pct(payload['real_in_sample_advantage'])}R** |")
    add("")
    add("**A weakness of this control, stated rather than left for a reader to find.** The "
        "shuffle is independent per symbol, so it destroys the cross-symbol correlation "
        "real outcomes have - BTC and ETH move together. The survivor test requires both "
        "symbols to agree on which side wins, and real data gets that agreement more "
        "easily than independently-shuffled data does. So this distribution is **narrower "
        "than the true selection distribution**, and clearing its 95th percentile is an "
        "easier bar than it looks. A block shuffle preserving the cross-symbol pairing "
        "would be the right fix and is a different study.")
    add("")

    add("### Verdict")
    add("")
    add(_reading(payload))
    add("")

    add("### Multiplicity")
    add("")
    add("| | cells | looks |")
    add("|---|---|---:|")
    add(f"| dev-year feature splits | {len(payload['features'])} features x "
        f"{len(payload['symbols'])} symbols | {len(payload['features']) * len(payload['symbols'])} |")
    add(f"| frozen rule on the holdout | {len(payload['symbols'])} symbols | {len(payload['symbols'])} |")
    add(f"| trend_align standalone (amendment) | dev + holdout x {len(payload['symbols'])} symbols | {2 * len(payload['symbols'])} |")
    add("| shuffled control | a control, not a test | 0 |")
    add(f"| **D213 total** | | **{len(payload['features']) * len(payload['symbols']) + len(payload['symbols']) + 2 * len(payload['symbols'])}** |")
    add("")
    add("The structure programme's 102 looks are disclosed adjacent and separately counted.")
    add("")
    return "\n".join(lines)


def _reading(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    dev = payload["dev_year"]
    c = payload["shuffled_control"]
    survivors = payload["survivors"]

    if not survivors:
        parts.append(
            f"**No feature survived the {dev} split**, so there is no rule to carry "
            "forward and H1 is falsified. That is a cleaner outcome than it looks: with "
            f"eight features and a {payload['edge_bar']:.2f}R bar, the shuffled control "
            f"produced at least one survivor in {c['share_with_a_survivor']:.0%} of draws "
            "from pure noise. Finding nothing on real data where noise finds something "
            f"{c['share_with_a_survivor']:.0%} of the time is the strongest form of the "
            "negative available here."
        )
        return "\n\n".join(parts)

    real = payload["real_in_sample_advantage"]
    out = [payload["out_of_sample"][s]["advantage"] for s in payload["symbols"]]
    inn = [payload["in_sample"][s]["advantage"] for s in payload["symbols"]]
    beats_control = real > c["p95"]

    parts.append(
        f"**{len(survivors)} feature{'s' if len(survivors) != 1 else ''} survived the "
        f"{dev} split: {', '.join(survivors)}.** In sample the rule gains "
        + " and ".join(f"{v:+.3f}R" for v in inn)
        + " on the two symbols. H1 confirmed, as predicted at high confidence — with eight "
        "features and a low bar, something always survives."
    )
    parts.append(
        "**Out of sample it gains "
        + " and ".join(f"{v:+.3f}R" for v in out)
        + f"**, against the pre-registered hurdle of +{payload['edge_bar']:.2f}R on both "
        "symbols. "
        + (
            "It clears it."
            if all(v >= payload["edge_bar"] for v in out)
            else "**It does not clear it.**"
        )
    )
    ratio = [
        (o / i if i not in (0.0,) and i == i and o == o else float("nan"))
        for o, i in zip(out, inn)
    ]
    parts.append(
        "The out-of-sample advantage is "
        + " and ".join("n/a" if r != r else f"{r:.0%}" for r in ratio)
        + " of the in-sample one — H2 predicted under half."
    )
    parts.append(
        f"**Against the shuffled control the real in-sample advantage of {real:+.3f}R sits "
        + ("above" if beats_control else "**inside**")
        + f" the noise distribution** (95th percentile {c['p95']:+.3f}R, largest of "
        f"{c['n_draws']} draws {c['max']:+.3f}R). "
        + (
            "So the mining found more than a selection effect would have produced."
            if beats_control
            else "So the mining found what selecting on noise produces, and hurdle 3 fails."
        )
    )
    tr = payload["trend_align_standalone"]
    dev_edges = [tr[s]["dev"]["edge"] for s in payload["symbols"] if tr[s]["dev"]]
    hold_edges = [tr[s]["holdout"]["edge"] for s in payload["symbols"] if tr[s]["holdout"]]
    if dev_edges and hold_edges:
        parts.append(
            "**H5 was void, not falsified, until the amendment.** `trend_align` never "
            "reached the table because a median split cannot divide a binary. Tested "
            "properly it gains "
            + " and ".join(f"{v:+.3f}R" for v in dev_edges)
            + f" in {dev} and "
            + " and ".join(f"{v:+.3f}R" for v in hold_edges)
            + " on the held-out years — "
            + (
                "so trading with the 200-bar trend does carry information here."
                if all(v >= payload["edge_bar"] for v in hold_edges)
                else "below the +0.10R bar out of sample, so the most-cited missing filter "
                "in this style is not the missing piece either."
            )
        )

    net = [payload["out_of_sample"][s]["mean_net_r_kept"] for s in payload["symbols"]]
    parts.append(
        "**After costs the filtered arm returns "
        + " and ".join("n/a" if v != v else f"{v:+.3f}R" for v in net)
        + " a trade out of sample.** Hurdle 4 "
        + ("holds." if all(v == v and v > 0 for v in net) else "fails, as H4 predicted at "
           "high confidence: no entry filter changes what the wrapper risks, and the toll "
           "is 0.96R on the median base-arm trade.")
    )
    return "\n\n".join(parts)


def append_section(payload: dict[str, Any]) -> None:
    # Bounded by the next heading, not by the parking lot at the bottom of the file.
    # The marker-to-anchor form this replaced destroyed every section written below
    # it; scripts/results_document.py carries the measurement, per runner (D542).
    splice_section(RESULTS, "## D213 - can selection rescue it?", render(payload))


if __name__ == "__main__":
    raise SystemExit(main())
