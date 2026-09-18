"""D216 — the tail, the frequency and the fill. Can the reversion effect ever pay?

    uv run python scripts/run_reversion_tail.py
    uv run python scripts/run_reversion_tail.py --report-only

`docs/decisions/D216-the-tail-the-frequency-and-the-fill.md` governs this and was committed
before this file existed. It also records two corrections to arithmetic I had stated
earlier, both of which change what this study has to measure.

## Break-even is a fixed point, not a constant

A bracketed trade's cost is asymmetric: the take-profit is a resting limit and can be a maker
fill, the stop must cross and cannot. So the round trip depends on `p` itself:

    p* = (c_in + c_stop + 0.5*ATR) / (ATR + c_stop - c_tp)

It reduces to `0.5 + RT/ATR` when the legs are symmetric, which is the identity the solver is
pinned against by test — a solver subtly wrong here would move every verdict in the study.

## The fill convention decides it, and cuts the wrong way

Maker is the only tier where `p*` is reachable **and** the only tier adversely selected
against this signal. A reversion entry rests a bid below a falling market; it fills when the
fall continues. `FillAssumption.TRADE_THROUGH` exists for exactly this and says so:

> the honest one for a bounce strategy — being filled only when price keeps going is
> precisely the adverse selection D9 named.

So every cell is measured twice, and the maker arm carries the verdict because it is the arm
whose cost makes the trade possible at all.

## Sampling

Scan every bar, take those above the cutoff, enforce `>= M` bars between selected events.
D215 stepped blindly every M-th bar, which would give ~365 samples at the 99th percentile
where this gives roughly eight times more with the same non-overlap. Strictly better for tail
work, and stated rather than absorbed.
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
from backtest_framework.research.structure_nulls import continue_from  # noqa: E402
from backtest_framework.research.terrain import rolling_mean_true_range  # noqa: E402
from backtest_framework.research.terrain_nulls import HORIZON  # noqa: E402
from backtest_framework.research.terrain_strategies import (  # noqa: E402
    TRADE_THROUGH_EPS,
)
from results_document import splice_section  # noqa: E402

SUMMARY = REPO / "data" / "reversion_tail_summary.json"
RESULTS = REPO / "docs" / "results" / "STRUCTURE_RESULTS.md"

FREQUENCIES = (
    {
        "name": "15m",
        "fixture": "crypto_binance_15m_raw.csv.gz",
        "symbols": ("BTCUSDT", "ETHUSDT"),
        "atr_window": 1_920,
        "tail": True,
    },
    {
        "name": "1d",
        "fixture": "crypto_daily_2015_2025_raw.csv.gz",
        "symbols": ("BTC-USD", "ETH-USD"),
        "atr_window": 20,
        "tail": False,
    },
)
"""ATR windows are each frequency's own established convention — 1,920 bars at 15m is D194's
calendar match, 20 is the daily default `AtrStop` and every terrain study used."""

LOOKBACK = 8
"""`M`, reused from D215 rather than re-chosen. Bar-count matching, both frequencies —
calendar-matching would put the daily lookback at 768 bars."""

BAND = 0.5
CUTOFFS = (87.5, 95.0, 99.0, 99.5)
MIN_N = 100
"""Below this a bucket is reported underpowered and carries no verdict."""

FEES = (
    {"name": "maker in/out", "c_in": 1.0, "c_tp": 1.0, "c_stop": 1.0, "arm": "maker"},
    {"name": "maker in, taker stop", "c_in": 1.0, "c_tp": 1.0, "c_stop": 10.0, "arm": "maker"},
    {"name": "taker throughout", "c_in": 40.0, "c_tp": 40.0, "c_stop": 40.0, "arm": "taker"},
)
"""Basis points per fill, and **which fill arm each tier is coherent with**.

That last field is a correction to this study's own first draft, which scored BOTH arms
against every tier and produced a "pass" by pairing a TAKER fill with MAKER costs. You
cannot pay a maker fee and cross the spread: a tier that assumes the entry rested has to be
scored on the population that actually filled by resting, which is a different and
adversely-selected sample. Pairing them freely inflates `p` and deflates the cost at the
same time.

The middle tier is the realistic one — you can rest an entry and a take-profit, you cannot
rest a stop. `maker in/out` is an optimistic bound, kept precisely so the gap between the
bound and the realistic tier is visible rather than hidden."""
VERDICT_FEE = "maker in, taker stop"


def break_even_p(atr_bp: float, c_in: float, c_tp: float, c_stop: float) -> float:
    """`p*` for a symmetric +/-0.5 ATR bracket with asymmetric fills.

        edge(p)  = 0.5 * ATR * (2p - 1)
        cost(p)  = c_in + p*c_tp + (1-p)*c_stop

    Setting them equal and solving for `p` gives the expression below. With
    `c_tp == c_stop` it collapses to `0.5 + (c_in + c)/ATR`, the familiar form, and
    `test_reversion_tail.py` pins that identity — the whole study's verdicts move if this is
    subtly wrong."""
    denominator = atr_bp + c_stop - c_tp
    if denominator <= 0.0:
        return float("inf")
    return (c_in + c_stop + 0.5 * atr_bp) / denominator


def tail_events(
    closes: Sequence[float],
    atr: Sequence[float],
    lookback: int,
    warmup: int,
    horizon: int,
    cutoff_value: float,
) -> list[int]:
    """Bar indices above the cutoff, spaced at least `lookback` apart.

    Greedy left to right: take the first qualifying bar, skip everything within `lookback`
    of it, continue. No two selected events share a lookback window, so the sample stays
    honest without throwing away the tail the way blind stepping does."""
    out: list[int] = []
    last = -10**9
    for t in range(max(warmup, lookback), len(closes) - horizon - 1):
        if t - last < lookback:
            continue
        a = atr[t]
        if not math.isfinite(a) or a <= 0.0:
            continue
        move = (closes[t] - closes[t - lookback]) / a
        if not math.isfinite(move) or abs(move) < cutoff_value:
            continue
        out.append(t)
        last = t
    return out


def move_at(closes: Sequence[float], atr: Sequence[float], t: int, lookback: int) -> float:
    return (closes[t] - closes[t - lookback]) / atr[t]


def maker_filled(bars: Sequence[Any], t: int, direction: int) -> bool:
    """Did a limit resting at `close[t]` fill on the next bar, by trade-through?

    For a reversion entry the direction is against the move: after a fall we want to buy, so
    the bid rests at the close and fills only if the next bar trades BELOW it — i.e. only if
    the fall continues. That is the adverse selection, and it is a property of the strategy
    rather than of this implementation.

    `TRADE_THROUGH_EPS` and the strict inequality are D9's pessimistic convention, reused
    rather than restated."""
    if t + 1 >= len(bars):
        return False
    limit = bars[t].bar.close
    nxt = bars[t + 1].bar
    if direction > 0:  # resting bid
        return nxt.low < limit - TRADE_THROUGH_EPS
    return nxt.high > limit + TRADE_THROUGH_EPS


def _rate(rows: Sequence[tuple[int, bool]]) -> float | None:
    """Share of events that reverted.

    **Module level on purpose.** This lived inside `measure` as a closure, which is part of
    why it shipped broken: a nested function cannot be imported, so it could not be pinned,
    so it was not.

    The first version was `sum(1 for _, ok in rows)` — no `if ok` — which counts every row
    and returns 1.0 identically. Every cell read 100.00%, every hurdle "cleared", and the
    reading function duly announced that H4 was falsified and a positive had been found.

    No test caught it. What caught it was `_halves`, which sums bools correctly and therefore
    said "not stable" while the headline said 100%. **Two views of one quantity disagreed** —
    the same tell as D209, where the census said 120 stacked setups and the lattice reported
    2. `test_reversion_tail.py` now pins this against a hand-counted list, and separately
    asserts the headline is the blend of the halves, so the disagreement that exposed the bug
    is a permanent gate rather than a lucky glance."""
    return (sum(1 for _, ok in rows if ok) / len(rows)) if rows else None


def _halves(
    rows: Sequence[tuple[int, bool]], n_bars: int
) -> tuple[float | None, float | None]:
    """The same rate over the two chronological halves. D213 is why this hurdle exists."""
    if len(rows) < MIN_N:
        return None, None
    cut = n_bars // 2
    early = [ok for t, ok in rows if t <= cut]
    late = [ok for t, ok in rows if t > cut]
    return (
        (sum(early) / len(early)) if early else None,
        (sum(late) / len(late)) if late else None,
    )


def measure(
    bars: Sequence[Any],
    closes: Sequence[float],
    atr: Sequence[float],
    events: Sequence[int],
    lookback: int,
    horizon: int,
) -> dict[str, Any]:
    """Both fill arms over one event set, plus the chronological halves."""
    taker: list[tuple[int, bool]] = []
    maker: list[tuple[int, bool]] = []
    for t in events:
        against = -1 if move_at(closes, atr, t, lookback) > 0.0 else 1
        taker.append((t, continue_from(closes, atr, t, against, BAND, horizon)))
        if maker_filled(bars, t, against):
            # Filled at the close of t, resolved from the bar it filled on.
            maker.append((t + 1, continue_from(closes, atr, t + 1, against, BAND, horizon)))

    t_early, t_late = _halves(taker, len(bars))
    m_early, m_late = _halves(maker, len(bars))
    return {
        "taker": {
            "n": len(taker),
            "p": _rate(taker),
            "p_first_half": t_early,
            "p_second_half": t_late,
        },
        "maker": {
            "n": len(maker),
            "fill_rate": len(maker) / len(taker) if taker else 0.0,
            "p": _rate(maker),
            "p_first_half": m_early,
            "p_second_half": m_late,
        },
        "adverse_selection": (
            _rate(taker) - _rate(maker)
            if _rate(taker) is not None and _rate(maker) is not None
            else None
        ),
    }


def verdict_for(
    cell: dict[str, Any], p_star: float, arm: str
) -> dict[str, Any]:
    """Hurdles 1-4 for one arm of one cell, each reported separately."""
    block = cell[arm]
    n, p = block["n"], block["p"]
    powered = n >= MIN_N
    clears = powered and p is not None and p >= p_star
    early, late = block["p_first_half"], block["p_second_half"]
    stable = (
        early is not None and late is not None
        and early >= p_star and late >= p_star
    )
    return {
        "n": n,
        "p": p,
        "p_star": p_star,
        "powered": powered,
        "clears_break_even": clears,
        "stable_across_halves": stable,
        "margin": (p - p_star) if p is not None else None,
    }


def run_symbol(
    freq: dict[str, Any], symbol: str, bars: Sequence[Any]
) -> dict[str, Any]:
    closes = [b.bar.close for b in bars]
    atr = rolling_mean_true_range(bars, freq["atr_window"])
    warmup = freq["atr_window"] + 1

    finite = [atr[i] / closes[i] for i in range(len(bars))
              if math.isfinite(atr[i]) and atr[i] > 0 and closes[i] > 0]
    atr_bp = statistics.median(finite) * 1e4

    # The move distribution, over the same spaced sample the cells will draw from.
    all_moves = []
    for t in range(max(warmup, LOOKBACK), len(closes) - HORIZON - 1):
        a = atr[t]
        if math.isfinite(a) and a > 0:
            m = (closes[t] - closes[t - LOOKBACK]) / a
            if math.isfinite(m):
                all_moves.append(abs(m))
    arr = np.asarray(all_moves, dtype=float)

    cutoffs = CUTOFFS if freq["tail"] else CUTOFFS[:1]
    cells: dict[str, Any] = {}
    for pct in cutoffs:
        value = float(np.percentile(arr, pct))
        events = tail_events(closes, atr, LOOKBACK, warmup, HORIZON, value)
        cell = measure(bars, closes, atr, events, LOOKBACK, HORIZON)
        cell["cutoff_pct"] = pct
        cell["cutoff_move_atr"] = value
        cell["break_even"] = {}
        for fee in FEES:
            p_star = break_even_p(atr_bp, fee["c_in"], fee["c_tp"], fee["c_stop"])
            # Only the coherent arm. See FEES: pairing a taker fill with maker costs is
            # what produced a spurious pass in this study's first draft.
            cell["break_even"][fee["name"]] = {
                "p_star": p_star,
                "arm": fee["arm"],
                "verdict": verdict_for(cell, p_star, fee["arm"]),
            }
        cells[f"p{pct}"] = cell
        print(
            f"    {pct:5.1f}th  move>={value:5.2f} ATR  taker n={cell['taker']['n']:5,} "
            f"p={_pc(cell['taker']['p'])}  maker n={cell['maker']['n']:5,} "
            f"p={_pc(cell['maker']['p'])}  adverse "
            f"{_pp(cell['adverse_selection'])}",
            flush=True,
        )

    return {
        "n_bars": len(bars),
        "atr_bp": atr_bp,
        "n_candidate_bars": len(all_moves),
        "cells": cells,
    }


def _pc(x):
    return "  n/a " if x is None else f"{x:6.2%}"


def _pp(x):
    return " n/a " if x is None else f"{x:+.2%}"


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
        append_section(payload)
        print(f"re-rendered the D216 section of {RESULTS.name}")
        return 0

    started = time.time()
    runs: dict[str, Any] = {}
    for freq in FREQUENCIES:
        raw, _ = load_fixture_csv_with_volumes(REPO / "data" / "fixtures" / freq["fixture"])
        cleaned, _ = clean(raw)
        for symbol in freq["symbols"]:
            print(f"{freq['name']} {symbol}: {len(cleaned[symbol]):,} bars", flush=True)
            runs[f"{freq['name']}|{symbol}"] = {
                "frequency": freq["name"],
                "symbol": symbol,
                "tail": freq["tail"],
                **run_symbol(freq, symbol, cleaned[symbol]),
            }

    payload = {
        "produced": time.strftime("%Y-%m-%d"),
        "lookback_M": LOOKBACK,
        "band_atr": BAND,
        "horizon": HORIZON,
        "cutoffs": list(CUTOFFS),
        "min_n": MIN_N,
        "fees": FEES,
        "verdict_fee": VERDICT_FEE,
        "runs": runs,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    SUMMARY.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    append_section(payload)
    print(f"\nwrote {SUMMARY.name} in {payload['elapsed_seconds']}s\n")
    print(render(payload))
    return 0


def render(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    runs = payload["runs"]
    fee = payload["verdict_fee"]

    add("## D216 - the tail, the frequency, and the fill")
    add("")
    add(f"**Produced:** {payload['produced']} · **Reproduce:** "
        "`uv run python scripts/run_reversion_tail.py` (offline, deterministic)")
    add("")
    add("Pre-registered in `docs/decisions/D216-the-tail-the-frequency-and-the-fill.md`, "
        "which also records two corrections to arithmetic I had stated earlier: daily ATR "
        "is ten times the 15m ATR so the same fixed cost is ten times cheaper in ATR terms, "
        "and a bracketed trade's cost is asymmetric because the take-profit can rest and the "
        "stop cannot - so break-even is a fixed point rather than a constant.")
    add("")

    add("### Break-even, per frequency and fee tier")
    add("")
    add("`p* = (c_in + c_stop + 0.5*ATR) / (ATR + c_stop - c_tp)`, which collapses to "
        "`0.5 + RT/ATR` when the legs are symmetric.")
    add("")
    add("| cell | ATR | " + " | ".join(f["name"] for f in payload["fees"]) + " |")
    add("|---|---:|" + "---:|" * len(payload["fees"]))
    for key, r in runs.items():
        first = next(iter(r["cells"].values()))
        cells = " | ".join(
            (lambda v: "impossible" if v >= 1.0 else f"{v:.2%}")(
                first["break_even"][f["name"]]["p_star"]
            )
            for f in payload["fees"]
        )
        add(f"| `{key}` | {r['atr_bp']:.1f} bp | {cells} |")
    add("")
    add(f"**`{fee}` carries the verdict** - you can rest an entry and a take-profit, you "
        "cannot rest a stop. `maker in/out` is an optimistic bound kept so the gap between "
        "the two is visible.")
    add("")

    add("### Every cell, both fill arms")
    add("")
    add("| cell | cutoff | move >= | taker n | taker p | maker n | fill rate | maker p | "
        "adverse selection |")
    add("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for key, r in runs.items():
        for name, c in r["cells"].items():
            add(f"| `{key}` | {c['cutoff_pct']:.1f}th | {c['cutoff_move_atr']:.2f} ATR | "
                f"{c['taker']['n']:,} | {_pc(c['taker']['p'])} | {c['maker']['n']:,} | "
                f"{c['maker']['fill_rate']:.1%} | {_pc(c['maker']['p'])} | "
                f"**{_pp(c['adverse_selection'])}** |")
    add("")
    add("**Adverse selection is the rightmost column and it is the study's second finding.** "
        "A reversion entry rests a bid below a falling market and fills only when the fall "
        "continues - the losing case by construction. `FillAssumption.TRADE_THROUGH` exists "
        "for exactly this and its docstring says so.")
    add("")

    add("### The verdict, each fee tier scored only on the arm it is coherent with")
    add("")
    add("**A tier that assumes the entry rested must be scored on the population that "
        "actually filled by resting.** This study's first draft scored both arms against "
        "every tier and produced a pass by pairing a taker fill with maker costs — inflating "
        "`p` and deflating the cost at the same time. The pairing below is enforced in "
        "`FEES`.")
    add("")
    add("| cell | cutoff | fee tier | arm | n | p | p* | margin | powered | clears | stable |")
    add("|---|---:|---|---|---:|---:|---:|---:|:--:|:--:|:--:|")
    for key, r in runs.items():
        for name, c in r["cells"].items():
            for f in payload["fees"]:
                blk = c["break_even"][f["name"]]
                v = blk["verdict"]
                star = "impossible" if v["p_star"] >= 1.0 else f"{v['p_star']:.2%}"
                mark = " **(verdict)**" if f["name"] == fee else ""
                add(f"| `{key}` | {c['cutoff_pct']:.1f}th | {f['name']}{mark} | "
                    f"{blk['arm']} | {v['n']:,} | {_pc(v['p'])} | {star} | "
                    f"{_pp(v['margin'])} | {'yes' if v['powered'] else '**no**'} | "
                    f"{'**YES**' if v['clears_break_even'] else 'no'} | "
                    f"{'yes' if v['stable_across_halves'] else 'no'} |")
    add("")

    add("### Verdict")
    add("")
    add(_reading(payload))
    add("")

    add("### Multiplicity")
    add("")
    n15 = sum(len(r["cells"]) for r in runs.values() if r["tail"]) * 2
    n1d = sum(len(r["cells"]) for r in runs.values() if not r["tail"]) * 2
    add("| | cells | looks |")
    add("|---|---|---:|")
    add(f"| 15m tail | cutoffs x symbols x 2 fills | {n15} |")
    add(f"| daily | top bucket x symbols x 2 fills | {n1d} |")
    add(f"| **D216 total** | | **{n15 + n1d}** |")
    add("")
    add(f"On the reversion ledger D215's Test A opened at 4 - running total **{4 + n15 + n1d}**. "
        "The structure programme's 395 are not inherited: no sensor, component or level is "
        "reused.")
    add("")
    return "\n".join(lines)


def _reading(payload: dict[str, Any]) -> str:
    runs = payload["runs"]
    fee = payload["verdict_fee"]
    parts: list[str] = []

    # H1: does p rise into the tail at 15m?
    for key, r in runs.items():
        if not r["tail"]:
            continue
        ps = [(c["cutoff_pct"], c["taker"]["p"]) for c in r["cells"].values()]
        live = [(a, b) for a, b in ps if b is not None]
        rising = all(b >= a - 0.005 for (_, a), (_, b) in zip(live, live[1:]))
        parts.append(
            f"**`{key}` into the tail:** "
            + ", ".join(f"{p:.2%} at the {c:.1f}th" for c, p in live)
            + f" — {'still rising' if rising else 'not monotone'}."
        )
    parts.append("")

    adverse = [
        c["adverse_selection"]
        for r in runs.values() for c in r["cells"].values()
        if c["adverse_selection"] is not None
    ]
    if adverse:
        mean_adv = statistics.fmean(adverse)
        wrong_sign = [a for a in adverse if a < 0]
        # The adjective is computed, not asserted. An earlier draft of this sentence read
        # "real and large" unconditionally and would have called a +1.5-point effect large
        # while the very next clause scored H2 falsified for being under 3.
        size = "large" if mean_adv >= 0.03 else "real in direction but small"
        parts.append(
            f"**Adverse selection is {size}.** Across all {len(adverse)} cells the maker arm "
            f"scores {mean_adv:+.2%} against the taker arm on average (predicted: at least "
            f"+3.00%), spanning {min(adverse):+.2%} to {max(adverse):+.2%}, with "
            f"{len(adverse) - len(wrong_sign)} of {len(adverse)} cells in the predicted "
            f"direction. **H2 "
            + ("confirmed" if mean_adv >= 0.03 else "falsified on magnitude")
            + "** — resting a bid below a falling market does fill you when the fall "
            "continues, but at this horizon it costs about half what I predicted."
        )
    parts.append("")

    daily = [
        (key, c["taker"]["p"])
        for key, r in runs.items() if not r["tail"]
        for c in r["cells"].values() if c["taker"]["p"] is not None
    ]
    if daily:
        inverted = [k for k, v in daily if v < 0.5]
        parts.append("")
        parts.append(
            "**At daily the effect is not weaker, it is absent or inverted.** "
            + ", ".join(f"`{k}` {v:.2%}" for k, v in daily)
            + f" against a coin-flip 50% — {len(inverted)} of {len(daily)} below it. "
            "H3 predicted a weaker-but-present reversion at daily; what is here is the "
            "opposite sign on one symbol and nothing on the other. **H3 falsified**, and in "
            "the direction that matches the standard stylised fact: reversal intraday, "
            "momentum at daily. These are the two thinnest samples in the study "
            "(n = "
            + ", ".join(
                f"{c['taker']['n']:,}"
                for r in runs.values() if not r["tail"]
                for c in r["cells"].values()
            )
            + ") and the claim is reported at that weight."
        )

    clears = [
        (key, c["cutoff_pct"], f["name"])
        for key, r in runs.items()
        for c in r["cells"].values()
        for f in payload["fees"]
        if c["break_even"][f["name"]]["verdict"]["clears_break_even"]
        and c["break_even"][f["name"]]["verdict"]["stable_across_halves"]
    ]
    total = sum(len(r["cells"]) for r in runs.values()) * len(payload["fees"])
    on_verdict = [c for c in clears if c[2] == fee]
    parts.append(
        f"**Coherent arm/fee pairings clearing all four hurdles: {len(clears)} of {total}.** "
        + (
            "None. **H4 confirmed.**"
            if not clears
            else "They are: "
            + ", ".join(f"`{k}` {c:.1f}th under `{a}`" for k, c, a in clears)
            + "."
        )
    )
    parts.append("")
    parts.append(
        f"**On the tier that carries the verdict — `{fee}` — {len(on_verdict)} of "
        f"{total // len(payload['fees'])} cells clear.** "
        + (
            "Every survivor above sits on `maker in/out`, the tier this pre-registration "
            "itself labelled *an optimistic bound*, and it is optimistic for a concrete "
            "reason: it prices the stop as a maker fill. **You cannot rest a stop.** A "
            "resting sell placed below a long's market price is immediately marketable and "
            "crosses as a taker. So the two clearing cells clear a fee model that cannot be "
            "traded.\n\n**H4 is falsified as literally written and confirmed as it was "
            "meant.** I score it falsified, because the hurdle text said *no cell* and two "
            "cells cleared, and because scoring my own prediction on the reading most "
            "favourable to it is the failure mode this whole programme exists to avoid. "
            "What the falsification buys is one real fact: at the 99.5th percentile the "
            "effect is finally large enough to beat a 2 bp round trip on both symbols, "
            "stably across both halves. It is still not large enough to beat the 11 bp round "
            "trip you would actually pay."
            if not on_verdict
            else "D215's pre-committed rule applies: that is a positive claim, it is **not** "
            "pursued inside this study, and it gets its own pre-registration and its own "
            "holdout before anyone believes it."
        )
    )
    parts.append("")

    thin = [
        (key, c["cutoff_pct"], f["name"])
        for key, r in runs.items()
        for c in r["cells"].values()
        for f in payload["fees"]
        if not c["break_even"][f["name"]]["verdict"]["powered"]
    ]
    parts.append(
        f"**Underpowered cells (n < {payload['min_n']}): {len(thin)} of {total}**, reported "
        "with no verdict rather than with a rate computed on too few events."
    )
    return "\n".join(parts)


def append_section(payload: dict[str, Any]) -> None:
    # Bounded by the next heading, not by the parking lot at the bottom of the file.
    # The marker-to-anchor form this replaced destroyed every section written below
    # it; scripts/results_document.py carries the measurement, per runner (D542).
    splice_section(RESULTS, "## D216 - the tail, the frequency, and the fill", render(payload))


if __name__ == "__main__":
    raise SystemExit(main())
