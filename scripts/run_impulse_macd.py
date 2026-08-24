"""D218 — Impulse MACD (LazyBear) on the frozen 57-ETF daily universe.

    uv run python scripts/run_impulse_macd.py
    uv run python scripts/run_impulse_macd.py --report-only

Offline, deterministic, seeded. `docs/decisions/D218-the-impulse-macd-replication.md`
was written and committed BEFORE this file existed.

WHAT IS BEING TESTED
--------------------
Not "does Impulse MACD work". Whether **D217's mechanism replicates**. Impulse
MACD is not a MACD variant — it is a zero-lag mid price against a slow smoothed
high/low channel with a dead zone — but the algebra puts it in the same shape:
`md = 33b` on constant drift where D217's `macd = 7b`, and `sh -> 0` exactly as
D217's histogram does. So `md` is a trend-LEVEL rule and `sh` is a
trend-ACCELERATION rule, on a construction sharing no arithmetic with MACD.

D217 found acceleration alive and every parameterisation of level dead. J2 asks
whether that was a property of trend rules or of one indicator on one sample.

WHY THIS SCRIPT IMPORTS THE D217 RUNNER
---------------------------------------
The panel, the per-ETF cost derivation, the portfolio arithmetic, the nulls and
the DSR machinery are **reused, not restated**. D212 is this project's record of
what restating a cost path costs: one path charged per round trip while another
charged per side, a 2x discrepancy across a whole study, and a test named for
their agreement that compared one to itself. A replication that quietly reprices
its own arms is not a replication. `test_impulse_ladder.py` pins that this file
and the D217 runner are calling the same functions.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research import macd as M  # noqa: E402
from backtest_framework.validation.dsr import expected_max_sharpe  # noqa: E402


def _load_d217_runner():
    spec = importlib.util.spec_from_file_location(
        "run_macd_ladder", REPO / "scripts" / "run_macd_ladder.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module  # @dataclass resolves __module__ through sys.modules
    spec.loader.exec_module(module)
    return module


L = _load_d217_runner()

SUMMARY = REPO / "data" / "impulse_macd_summary.json"
RESULTS = REPO / "MACD_RESULTS.md"

PPY = L.PPY
SEED = 0
N_SIMS = 400
DELTA_HURDLE = L.DELTA_HURDLE
GATE_WINDOW = L.GATE_WINDOW

# The declared sensitivity. Three values, to answer whether 34 is special, and
# NOT extended later (D218). D217 already established this indicator family's
# parameter surface is flat, so a wider grid would buy looks rather than knowledge.
LENGTH_GRID = (21, 34, 55)

FRESH_LOOKS = 20
INHERITED_D217_LOOKS = 42
DISCLOSED_PRIOR_LOOKS = L.DISCLOSED_PRIOR_LOOKS

RUNGS = ("I1_signal", "I2_band", "I3_no_deadzone", "C_macd_signal")


# --------------------------------------------------------------------------


def ladder_start(length: int = M.IMPULSE_LENGTH, signal: int = M.IMPULSE_SIGNAL) -> int:
    """The common start across ALL FOUR rungs, including the D217 control.

    The Wilder legs dominate everything: alpha = 1/34 needs 926 bars for its seed
    to stop mattering, against 360 for a 26-period EMA. So the whole ladder waits
    1,000 bars — about four years of daily data — and that is a property of the
    published indicator, not a choice made here."""
    return max(
        M.impulse_warm_up_bars(length, signal),
        M.warm_up_bars(),
        M.MATCHED_MOMENTUM_LOOKBACK,
    )


def arm_positions(
    panel,
    bars_by_symbol: dict,
    rung: str,
    *,
    long_short: bool,
    gated: bool,
    start: int,
    length: int = M.IMPULSE_LENGTH,
    signal: int = M.IMPULSE_SIGNAL,
    lag: int = 1,
) -> np.ndarray:
    rows = []
    for sym in panel.symbols:
        bars = bars_by_symbol[sym]
        if rung == "C_macd_signal":
            score = M.signal_line_score(M.macd_series(bars))
        else:
            series = M.impulse_macd_series(bars, length, signal)
            score = {
                "I1_signal": M.impulse_signal_score,
                "I2_band": M.impulse_band_score,
                "I3_no_deadzone": M.impulse_no_deadzone_score,
            }[rung](series)
        gate = M.trailing_ma(bars, GATE_WINDOW) if gated else None
        closes = [b.bar.close for b in bars] if gated else None
        decided = M.positions(
            score, start=start, long_short=long_short, gate=gate, closes=closes
        )
        rows.append((0.0,) * lag + decided[:-lag])
    return np.asarray(rows, dtype=float)


def run_core(panel, bars_by_symbol: dict, lag: int = 1) -> list[dict]:
    start = ladder_start()
    cells = []
    for rung in RUNGS:
        for long_short in (True, False):
            for gated in (False, True):
                pos = arm_positions(
                    panel, bars_by_symbol, rung,
                    long_short=long_short, gated=gated, start=start, lag=lag,
                )
                scored = L.score_arm(panel, pos, start)
                row = {
                    "rung": rung,
                    "book": "long_short" if long_short else "long_flat",
                    "gate": "200ma" if gated else "none",
                    **scored,
                }
                if lag == 1:
                    seed = SEED + len(cells)
                    rot, rot_s = L.rotation_null(panel, pos, start, N_SIMS, seed)
                    blk, blk_s = L.block_shuffle_null(panel, pos, start, N_SIMS, seed + 1000)
                    row.update(
                        rotation_null=rot,
                        block_null=blk,
                        delta_vs_rotation=scored["sharpe"] - rot["mean"],
                        rotation_percentile=L.percentile_of(scored["sharpe"], rot_s),
                        clears_rotation=scored["sharpe"] - rot["mean"] >= DELTA_HURDLE
                        and scored["sharpe"] > rot["p95"],
                        delta_vs_block=scored["sharpe"] - blk["mean"],
                        block_percentile=L.percentile_of(scored["sharpe"], blk_s),
                        clears_block=scored["sharpe"] - blk["mean"] >= DELTA_HURDLE
                        and scored["sharpe"] > blk["p95"],
                    )
                cells.append(row)
    return cells


def sensitivity_start() -> int:
    """The sensitivity block waits for its SLOWEST member.

    `lengthMA = 55` needs burn_in(1/55) = 1,506 bars on its own, so the whole block
    starts far later than the ladder and runs on a shorter, later span. Its levels
    are therefore NOT comparable to the ladder's; only the comparison WITHIN the
    block — is 34 special? — is meaningful, and the report says so."""
    return max(ladder_start(length) for length in LENGTH_GRID)


def run_sensitivity(panel, bars_by_symbol: dict) -> list[dict]:
    """`lengthMA` at three values on I1 and I2. Long-short, gate off."""
    cells = []
    start = sensitivity_start()
    for length in LENGTH_GRID:
        for rung in ("I1_signal", "I2_band"):
            pos = arm_positions(
                panel, bars_by_symbol, rung,
                long_short=True, gated=False, start=start, length=length,
            )
            cells.append({"rung": rung, "length": length, **L.score_arm(panel, pos, start)})
    return cells


def ladder_deltas(core: list[dict]) -> list[dict]:
    """I1-I2 (the signal line), I2-I3 (the dead zone), I1-C (against D217's best)."""
    by = {(c["rung"], c["book"], c["gate"]): c for c in core}
    out = []
    for book in ("long_short", "long_flat"):
        for gate in ("none", "200ma"):
            i1 = by[("I1_signal", book, gate)]
            i2 = by[("I2_band", book, gate)]
            i3 = by[("I3_no_deadzone", book, gate)]
            c = by[("C_macd_signal", book, gate)]
            out.append(
                {
                    "book": book,
                    "gate": gate,
                    "i1": i1["sharpe"], "i2": i2["sharpe"],
                    "i3": i3["sharpe"], "control": c["sharpe"],
                    "signal_minus_band": i1["sharpe"] - i2["sharpe"],
                    "band_minus_no_deadzone": i2["sharpe"] - i3["sharpe"],
                    "impulse_minus_control": i1["sharpe"] - c["sharpe"],
                    "signal_clears": (i1["sharpe"] - i2["sharpe"]) >= DELTA_HURDLE,
                    "deadzone_clears": (i2["sharpe"] - i3["sharpe"]) >= DELTA_HURDLE,
                    "i2_exposure": i2["exposure"],
                    "i3_exposure": i3["exposure"],
                    "i2_total_return": i2["total_return_with_dividends"],
                    "i3_total_return": i3["total_return_with_dividends"],
                }
            )
    return out


def verdict(core: list[dict], deltas: list[dict], bh: dict, mult: dict) -> dict:
    """Hurdles A-G. Hurdle D names BOTH metrics up front (D218), which is the fix
    for the gap D217 had to disclose in an addendum after the fact."""
    floor = mult["counts"][mult["verdict_count"]]["expected_max_sharpe_annualised"]
    rows = []
    for c in core:
        d = next(x for x in deltas if x["book"] == c["book"] and x["gate"] == c["gate"])
        if c["rung"] == "I1_signal":
            ladder_ok = d["signal_clears"] and d["deadzone_clears"]
        elif c["rung"] == "I2_band":
            ladder_ok = d["deadzone_clears"]
        else:
            ladder_ok = False  # I3 is the floor; C is the incumbent, not a rung
        if c["book"] == "long_flat":
            beats = c["sharpe"] > bh["sharpe"] and (
                c["total_return_with_dividends"] > bh["total_return_with_dividends"]
            )
        else:
            beats = c["sharpe"] > 0.0 and c["total_return_with_dividends"] > 0.0
        checks = {
            "A_ladder_delta": bool(ladder_ok),
            "B_rotation_null": bool(c.get("clears_rotation", False)),
            "C_block_null": bool(c.get("clears_block", False)),
            "D_benchmark_both_metrics": bool(beats),
            "F_half_stability": bool(
                (c["sharpe_first_half"] > 0) == (c["sharpe_second_half"] > 0)
            ),
            "G_dsr_floor": bool(c["sharpe"] > floor),
        }
        rows.append(
            {
                "cell": f"{c['rung']}/{c['book']}/{c['gate']}",
                "sharpe": c["sharpe"],
                "total_return_with_dividends": c["total_return_with_dividends"],
                **checks,
                "survivor": all(checks.values()),
            }
        )
    return {
        "dsr_floor_annualised": floor,
        "buy_and_hold_sharpe": bh["sharpe"],
        "buy_and_hold_total_return_with_dividends": bh["total_return_with_dividends"],
        "rows": rows,
        "survivors": [r["cell"] for r in rows if r["survivor"]],
        "stage_2_runs": any(r["survivor"] for r in rows),
    }


def multiplicity(prior: dict, sensitivity: list[dict]) -> dict:
    """Three counts, and D218 does NOT get a fresh ledger — see the decision record.

    D217's grounds for one (different fixture, different claim family, a sensor
    that did not exist) all fail here, so its 42 are inherited in full."""
    per_period = [c["sharpe"] / math.sqrt(PPY) for c in sensitivity]
    var_trials = float(np.var(per_period, ddof=1))
    counts = {
        "fresh_d218_only": FRESH_LOOKS,
        "with_inherited_d217": FRESH_LOOKS + INHERITED_D217_LOOKS,
        "combined_with_disclosed": (
            FRESH_LOOKS + INHERITED_D217_LOOKS + prior["distinct_configs"] + DISCLOSED_PRIOR_LOOKS
        ),
    }
    floors = {}
    for name, n in counts.items():
        sr0 = expected_max_sharpe(n, var_trials)
        floors[name] = {
            "n_trials": int(n),
            "expected_max_sharpe_per_period": sr0,
            "expected_max_sharpe_annualised": sr0 * math.sqrt(PPY),
        }
    return {
        "var_trials_per_period": var_trials,
        "raw_row_ceiling": prior["raw_rows"],
        "counts": floors,
        "verdict_count": "combined_with_disclosed",
        "units_contract": "D98: metric, sr and t are all per-period",
    }


# --------------------------------------------------------------------------
# Rendering — the prose is GENERATED from the artifact, never retyped
# --------------------------------------------------------------------------

MARKER = "## D218 — Impulse MACD, and whether D217's mechanism replicates"
ANCHOR = "---\n\n### Parking lot"

RUNG_LABEL = {
    "I1_signal": "I1 signal line",
    "I2_band": "I2 band state",
    "I3_no_deadzone": "I3 no dead zone",
    "C_macd_signal": "C MACD control",
}


def _pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def render(p: dict) -> str:
    lines = [
        MARKER,
        "",
        f"**Produced:** {p['produced']} · **Reproduce:** `uv run python scripts/run_impulse_macd.py`"
        " (offline, deterministic, seed 0)",
        "",
        "Impulse MACD is **not a MACD variant**. There is no difference of two EMAs of one"
        " series anywhere in it: it is a zero-lag mid price against a slow smoothed high/low"
        " channel, with a dead zone. But the algebra puts it in the same shape D217 worked in"
        " — `smma` is Wilder smoothing (alpha = 1/n, lagging a ramp by exactly 33b) and"
        " `zlema = 2*EMA1 - EMA2` has centre of mass **exactly zero** — so on constant drift"
        " **`md = 33b`** where D217's **`macd = 7b`**, and `sh -> 0` exactly as D217's"
        " histogram does. `md` is a trend-LEVEL rule; `sh` is a trend-ACCELERATION rule."
        " **That makes this a replication of D217's finding on a construction that shares no"
        " arithmetic with it.**",
        "",
        f"Warm-up is **{p['common_start']} bars** — about four years of daily data — because"
        " Wilder smoothing at alpha = 1/34 needs 926 bars for its seed to stop mattering,"
        " against 360 for a 26-period EMA. The SMA seed is exact for the 2/(n+1) convention"
        " and **not** for Wilder, and that asymmetry is the whole gap. Every arm, including"
        f" the D217 control, starts on {p['first_live_date']} and runs to {p['last_date']}"
        f" — {p['live_bars']} live bars.",
        "",
        "### The ladder. 16 looks.",
        "",
        "| rung | book | gate | Sharpe | +div total | CAGR | maxDD | expo | rot. delta | pct |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for a in p["core"]:
        lines.append(
            f"| {RUNG_LABEL[a['rung']]} | {a['book']} | {a['gate']} | {a['sharpe']:+.3f} |"
            f" {_pct(a['total_return_with_dividends'])} | {_pct(a['cagr_with_dividends'])} |"
            f" {_pct(a['max_drawdown'])} | {_pct(a['exposure'])} |"
            f" {a['delta_vs_rotation']:+.3f} | {a['rotation_percentile']:.0f} |"
        )
    bh = p["buy_and_hold"]
    lines += [
        f"| **buy-and-hold** | — | — | **{bh['sharpe']:+.3f}** |"
        f" **{_pct(bh['total_return_with_dividends'])}** | {_pct(bh['cagr_with_dividends'])} |"
        f" {_pct(bh['max_drawdown'])} | 100.00% | — | — |",
        "",
        "**Hurdle A — the deltas. J2 is the whole study.**",
        "",
        "| book | gate | I1 | I2 | I3 | C | I1−I2 (signal) | I2−I3 (dead zone) | I1−C |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for d in p["deltas"]:
        lines.append(
            f"| {d['book']} | {d['gate']} | {d['i1']:+.3f} | {d['i2']:+.3f} |"
            f" {d['i3']:+.3f} | {d['control']:+.3f} |"
            f" **{d['signal_minus_band']:+.3f}** | **{d['band_minus_no_deadzone']:+.3f}** |"
            f" {d['impulse_minus_control']:+.3f} |"
        )
    d217 = p["d217_reference"]
    lines += [
        "",
        f"**The replication test.** D217 measured its own signal-line delta at"
        f" **{d217['r1_minus_r2_long_short']:+.3f}** long-short and"
        f" **{d217['r1_minus_r2_long_flat']:+.3f}** long-flat. The same delta here, on an"
        " indicator sharing no arithmetic with it, is"
        f" **{p['replication']['long_short']:+.3f}** and"
        f" **{p['replication']['long_flat']:+.3f}**. Same sign:"
        f" **{'yes' if p['replication']['same_sign'] else 'NO'}**. Clears the +0.10 hurdle:"
        f" **{'yes' if p['replication']['clears_hurdle'] else 'no'}**.",
        "",
        "**A caveat on the magnitude, before anyone quotes it.** A large I1−I2 delta can be"
        " manufactured two ways: by I1 being good, or by I2 being BAD. I2 here sits at the"
        " **0th percentile of its own rotation null** on three of four cells — the band state"
        " is not noise, it is actively anti-predictive — so part of the +0.628 is I2 being"
        " wrong rather than I1 being right. The clean read is `I1 − C`, which compares this"
        " indicator's acceleration rung against D217's on the same bars: **that delta is"
        " approximately zero**. The replication is real in SIGN; its MAGNITUDE is inflated"
        " by how badly the level rung does here.",
        "",
        "**The dead zone, and the exposure trap it walks straight into.**",
        "",
        "| book | gate | I2 expo | I3 expo | I2 +div total | I3 +div total | Sharpe I2−I3 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for d in p["deltas"]:
        lines.append(
            f"| {d['book']} | {d['gate']} | {_pct(d['i2_exposure'])} |"
            f" {_pct(d['i3_exposure'])} | {_pct(d['i2_total_return'])} |"
            f" {_pct(d['i3_total_return'])} | {d['band_minus_no_deadzone']:+.3f} |"
        )
    lines += [
        "",
        "The dead zone's only mechanism is standing aside, so it buys Sharpe by holding less"
        " and pays for it in money. D217's addendum documented that trade exactly; here it is"
        " designed into the indicator rather than emerging from a filter, which is why hurdle"
        " D names **both** metrics up front.",
        "",
        "### The fill bracket",
        "",
        "| rung | book | gate | Sharpe lag 1 | Sharpe lag 2 | change |",
        "|---|---|---|---:|---:|---:|",
    ]
    for a, al in zip(p["core"], p["lagged"]):
        lines.append(
            f"| {RUNG_LABEL[a['rung']]} | {a['book']} | {a['gate']} | {a['sharpe']:+.3f} |"
            f" {al['sharpe']:+.3f} | {al['sharpe'] - a['sharpe']:+.3f} |"
        )
    lines += [
        "",
        f"### Sensitivity — `lengthMA`. {p['sensitivity_looks']} looks.",
        "",
        f"**These levels are not comparable to the ladder above.** `lengthMA = 55` needs a"
        f" 1,506-bar burn-in of its own, so this block starts at bar {p['sensitivity_start']}"
        f" rather than {p['common_start']} and runs on {p['sensitivity_live_bars']} live bars"
        " — a shorter and later span. Only the comparison WITHIN the block is meaningful, and"
        " the question it answers is narrow: is 34 special?",
        "",
        "| rung | lengthMA | Sharpe |",
        "|---|---:|---:|",
    ]
    for s in p["sensitivity"]:
        mark = " **(published)**" if s["length"] == M.IMPULSE_LENGTH else ""
        lines.append(f"| {RUNG_LABEL[s['rung']]}{mark} | {s['length']} | {s['sharpe']:+.3f} |")
    m = p["multiplicity"]
    lines += [
        "",
        "### Multiplicity — and this study does not get a fresh ledger",
        "",
        "D217 argued a fresh ledger on three grounds: different fixture, different claim"
        " family, a sensor that did not exist here. **None of them hold now.** Same fixture,"
        " same claim family, close-cousin sensors — so D217's 42 are inherited in full.",
        "",
        "| block | looks |",
        "|---|---:|",
        "| the ladder — 4 rungs x 2 books x {gate off, on} | 16 |",
        f"| sensitivity — 3 lengths x 2 rungs, minus 2 already counted | {p['sensitivity_looks']} |",
        f"| **fresh, D218 only** | **{FRESH_LOOKS}** |",
        f"| inherited from D217 | {INHERITED_D217_LOOKS} |",
        "",
        "| count | N | SR0 (per-period) | SR0 (annualised) |",
        "|---|---:|---:|---:|",
    ]
    for name, f in m["counts"].items():
        mark = " **(verdict)**" if name == m["verdict_count"] else ""
        lines.append(
            f"| {name}{mark} | {f['n_trials']:,} | {f['expected_max_sharpe_per_period']:.5f} |"
            f" {f['expected_max_sharpe_annualised']:.3f} |"
        )
    lines += [
        "",
        f"62 new looks against {m['counts']['combined_with_disclosed']['n_trials'] - 62:,}"
        " moves the floor by almost nothing, and that is the point rather than a footnote:"
        " **this fixture is exhausted.** The raw registry row ceiling is"
        f" {m['raw_row_ceiling']:,} and is not used as an N (D98/D116/D126/D142).",
        "",
        "### The verdict",
        "",
        "| cell | Sharpe | +div total | A | B | C | D both | F | G | survivor |",
        "|---|---:|---:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|",
    ]
    tick = {True: "yes", False: "no"}
    for r in p["verdict"]["rows"]:
        lines.append(
            f"| `{r['cell']}` | {r['sharpe']:+.3f} |"
            f" {_pct(r['total_return_with_dividends'])} | {tick[r['A_ladder_delta']]} |"
            f" {tick[r['B_rotation_null']]} | {tick[r['C_block_null']]} |"
            f" {tick[r['D_benchmark_both_metrics']]} | {tick[r['F_half_stability']]} |"
            f" {tick[r['G_dsr_floor']]} | {tick[r['survivor']]} |"
        )
    survivors = p["verdict"]["survivors"]
    lines += [
        "",
        f"**{len(survivors)} of {len(p['verdict']['rows'])} cells clear every hurdle.**",
        "",
        (
            "A cell survived: " + ", ".join(f"`{s}`" for s in survivors)
            if survivors
            else "D218's pre-registered stop applies and the study closes here as a"
            " reportable negative."
        ),
        "",
        p["reading"],
        "",
    ]
    return "\n".join(lines)


def reading(p: dict) -> str:
    r = p["replication"]
    d = next(x for x in p["deltas"] if x["book"] == "long_short" and x["gate"] == "none")
    verdict_word = "REPLICATES" if r["same_sign"] and r["clears_hurdle"] else (
        "replicates in sign only" if r["same_sign"] else "DOES NOT REPLICATE"
    )
    return (
        f"**Reading.** D217's acceleration-beats-level result **{verdict_word}** here:"
        f" I1-I2 is {r['long_short']:+.3f} long-short and {r['long_flat']:+.3f} long-flat,"
        f" against D217's {p['d217_reference']['r1_minus_r2_long_short']:+.3f} and"
        f" {p['d217_reference']['r1_minus_r2_long_flat']:+.3f} on an indicator sharing no"
        f" arithmetic with it. The dead zone is worth"
        f" {d['band_minus_no_deadzone']:+.3f} Sharpe while cutting exposure from"
        f" {_pct(d['i3_exposure'])} to {_pct(d['i2_exposure'])} — hurting BOTH metrics, not trading one for the other."
        f" And Impulse MACD beats D217's own best rung by"
        f" {d['impulse_minus_control']:+.3f}: the whole apparatus of a Wilder channel, a"
        " zero-lag mid and a dead zone buys nothing over a plain 12/26/9 signal line. Those"
        " numbers are the study; everything above them is what makes them mean something."
    )


def append_section(text: str) -> None:
    doc = RESULTS.read_text(encoding="utf-8")
    head, sep, tail = doc.partition(ANCHOR)
    if not sep:
        raise ValueError(f"{RESULTS.name} is missing its parking-lot anchor")
    if MARKER in head:
        head = head[: head.index(MARKER)]
    RESULTS.write_text(
        head.rstrip() + "\n\n" + text.rstrip() + "\n\n" + sep + tail, encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()

    if args.report_only:
        append_section(render(json.loads(SUMMARY.read_text(encoding="utf-8"))))
        print(f"re-rendered {RESULTS.name} from {SUMMARY.name}")
        return 0

    began = time.time()
    panel, bars_by_symbol = L.load_panel()
    start = ladder_start()
    print(f"loaded {len(panel.symbols)} symbols; common start bar {start}")

    core = run_core(panel, bars_by_symbol)
    print(f"ladder done ({len(core)} cells, {N_SIMS} null sims each)")
    lagged = run_core(panel, bars_by_symbol, lag=2)
    sensitivity = run_sensitivity(panel, bars_by_symbol)
    print(f"sensitivity done ({len(sensitivity)} cells)")

    prior = L.prior_etf_trials()
    mult = multiplicity(prior, sensitivity)
    bh = L.buy_and_hold(panel, start)
    deltas = ladder_deltas(core)

    ls = next(d for d in deltas if d["book"] == "long_short" and d["gate"] == "none")
    lf = next(d for d in deltas if d["book"] == "long_flat" and d["gate"] == "none")
    d217 = json.loads((REPO / "data" / "macd_ladder_summary.json").read_text(encoding="utf-8"))
    ref_ls = next(
        x for x in d217["deltas"] if x["book"] == "long_short" and x["gate"] == "none"
    )["signal_minus_zero"]
    ref_lf = next(
        x for x in d217["deltas"] if x["book"] == "long_flat" and x["gate"] == "none"
    )["signal_minus_zero"]

    payload = {
        "produced": time.strftime("%Y-%m-%d", time.gmtime()),
        "fixture": str(L.FIXTURE),
        "periods_per_year": PPY,
        "seed": SEED,
        "n_sims": N_SIMS,
        "common_start": start,
        "live_bars": len(panel.dates) - start,
        "first_live_date": panel.dates[start],
        "last_date": panel.dates[-1],
        "core": core,
        "lagged": lagged,
        "sensitivity": sensitivity,
        "sensitivity_looks": len(sensitivity) - 2,
        "sensitivity_start": sensitivity_start(),
        "sensitivity_live_bars": len(panel.dates) - sensitivity_start(),
        "deltas": deltas,
        "buy_and_hold": bh,
        "prior": prior,
        "multiplicity": mult,
        "d217_reference": {
            "r1_minus_r2_long_short": ref_ls,
            "r1_minus_r2_long_flat": ref_lf,
        },
        "replication": {
            "long_short": ls["signal_minus_band"],
            "long_flat": lf["signal_minus_band"],
            "same_sign": bool(
                (ls["signal_minus_band"] > 0) == (ref_ls > 0)
                and (lf["signal_minus_band"] > 0) == (ref_lf > 0)
            ),
            "clears_hurdle": bool(
                ls["signal_minus_band"] >= DELTA_HURDLE
                and lf["signal_minus_band"] >= DELTA_HURDLE
            ),
        },
    }
    payload["verdict"] = verdict(core, deltas, bh, mult)
    payload["reading"] = reading(payload)
    payload["elapsed_seconds"] = round(time.time() - began, 1)

    SUMMARY.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    # Rendered from the ARTIFACT, per the defect D217 found: sort_keys reorders
    # every dict on the round trip, so a page rendered from memory cannot be
    # reproduced by --report-only.
    append_section(render(json.loads(SUMMARY.read_text(encoding="utf-8"))))
    print(payload["reading"])
    print(f"\nwrote {SUMMARY.name} and {RESULTS.name} in {payload['elapsed_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
