"""D232 — the scale-corrected Impulse MACD.

`md` is measured in DOLLARS, so it scales with the price level, and `hist` is a
slope estimator on it. A steady decline therefore reads as bullish: md is
negative but its magnitude SHRINKS as the price falls, and a shrinking negative
number is a rising one.

Two corrections, registered together because they are not equivalent:

    I1r   md_r = md / mid                     approximate scale invariance
    I1L   the whole indicator on LOG prices   exact

Stage 1 only. The holdout is not touched.
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


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


L = _load("d217_ladder", "run_macd_ladder.py")
J = _load("d229_jerk", "run_jerk_rung.py")

SUMMARY = REPO / "data" / "scale_corrected_summary.json"
RESULTS = REPO / "docs" / "results" / "SCALE_CORRECTED_RESULTS.md"

PPY = L.PPY
LAG = 1
DELTA_HURDLE = L.DELTA_HURDLE
GATE_WINDOW = L.GATE_WINDOW
RUNGS = ("I1_signal", "I1r_ratio", "I1L_log")
CORRECTED = ("I1r_ratio", "I1L_log")


def _band_md(hi, lo, mi):
    """The published dead-zone rule, shared by every construction here.

    `0.0` inside the channel is a STATED VALUE, not a missing one (D218), and that
    is preserved by both corrections -- a fix that quietly changed the dead zone
    would be testing two things at once."""
    out = []
    for m, h, l in zip(mi, hi, lo):
        if m != m or h != h or l != l:
            out.append(math.nan)
        elif m > h:
            out.append(m - h)
        elif m < l:
            out.append(m - l)
        else:
            out.append(0.0)
    return out


def _hist(md, signal):
    sig = M._sma(md, signal)
    return tuple(
        math.nan if (a != a or b != b) else a - b for a, b in zip(md, sig)
    )


def ratio_score(bars, length=M.IMPULSE_LENGTH, signal=M.IMPULSE_SIGNAL):
    """I1r — the published series with the displacement divided by `mid`.

    `mid = smma(close, length)` is already inside `ImpulseSeries`: contemporaneous,
    smooth and strictly positive. Dividing by the raw close instead would inject
    the close's own noise into the denominator for no benefit."""
    s = M.impulse_macd_series(bars, length, signal)
    md_r = [
        math.nan if (m != m or d != d or d == 0.0) else m / d
        for m, d in zip(s.md, s.mid)
    ]
    return _hist(md_r, signal)


def log_score(bars, length=M.IMPULSE_LENGTH, signal=M.IMPULSE_SIGNAL):
    """I1L — the ENTIRE indicator recomputed on log prices.

    `smma` and `zlema` are linear with unit DC gain, so on log(kP) = log k + log P
    every leg shifts by the same constant and `mi - hi` is EXACTLY unchanged. And a
    steady exponential trend is a STRAIGHT LINE in log space, so md_L becomes
    constant and hist_L goes to zero -- the rule stands aside, which is the correct
    answer for a path carrying no acceleration.

    Not a call to `impulse_macd_series`: that function reads price fields off the
    bars, and the whole point here is to smooth the logs rather than the prices."""
    h = [math.log(b.bar.high) for b in bars]
    lo = [math.log(b.bar.low) for b in bars]
    c = [math.log(b.bar.close) for b in bars]
    hlc3 = [(a + x + y) / 3.0 for a, x, y in zip(h, lo, c)]
    md_L = _band_md(M.smma(h, length), M.smma(lo, length), M.zlema(hlc3, length))
    return _hist(md_L, signal)


SCORES = {
    "I1_signal": lambda bars: M.impulse_signal_score(M.impulse_macd_series(bars)),
    "I1r_ratio": ratio_score,
    "I1L_log": log_score,
}


def arm_positions(panel, cleaned, rung, *, long_short, gated, start):
    rows = []
    for sym in panel.symbols:
        bars = cleaned[sym]
        score = SCORES[rung](bars)
        gate = M.trailing_ma(bars, GATE_WINDOW) if gated else None
        closes = [b.bar.close for b in bars] if gated else None
        decided = M.positions(
            score, start=start, long_short=long_short, gate=gate, closes=closes
        )
        rows.append((0.0,) * LAG + decided[:-LAG])
    return np.asarray(rows, dtype=float)


def per_symbol_sharpe(panel, position, start):
    """One Sharpe per symbol, for Z5's mechanism test."""
    out = []
    for i in range(len(panel.symbols)):
        r = position[i, start:] * panel.total_log_returns[i, start:]
        sd = float(np.std(r, ddof=1))
        out.append((float(np.mean(r)) / sd * math.sqrt(PPY)) if sd > 0 else 0.0)
    return np.asarray(out)


def build() -> dict:
    t0 = time.time()
    panel, cleaned = L.load_panel()
    gross = None
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

    cells, series, psym = {}, {}, {}
    for rung in RUNGS:
        for book, ls in (("long_flat", False), ("long_short", True)):
            for gate, g in (("none", False), ("200ma", True)):
                pos = arm_positions(panel, cleaned, rung, long_short=ls, gated=g, start=start)
                key = f"{rung}|{book}|{gate}"
                cells[key] = J.score_cell(panel, panel, pos, start)
                series[key] = L.portfolio_log_returns(panel, pos)[start:]
                if book == "long_flat" and gate == "none":
                    psym[rung] = per_symbol_sharpe(panel, pos, start)

    bh = L.buy_and_hold(panel, start)
    ones = np.ones((len(panel.symbols), panel.closes.shape[1]))
    ones[:, :start] = 0.0
    bh["excess_sharpe"] = J.excess_sharpe(
        L.portfolio_log_returns(panel, ones, total_return=True)[start:],
        np.ones(panel.closes.shape[1] - start),
    )

    deltas = {}
    for book in ("long_flat", "long_short"):
        for gate in ("none", "200ma"):
            base = series[f"I1_signal|{book}|{gate}"]
            for rung in CORRECTED:
                k = f"{rung}|{book}|{gate}"
                d = L.sharpe_of(series[k]) - L.sharpe_of(base)
                boot = J.paired_block_bootstrap(series[k], base)
                deltas[f"{rung}|{book}|{gate}"] = {
                    "rung": rung, "book": book, "gate": gate,
                    "delta": d,
                    "delta_excess": cells[k]["excess_sharpe"]
                    - cells[f"I1_signal|{book}|{gate}"]["excess_sharpe"],
                    "boot": boot,
                    "clears_A": bool(d >= DELTA_HURDLE and boot["p05"] > DELTA_HURDLE),
                }
            # the two corrections against each other (Z6)
            deltas[f"I1L_minus_I1r|{book}|{gate}"] = {
                "rung": "I1L_minus_I1r", "book": book, "gate": gate,
                "delta": L.sharpe_of(series[f"I1L_log|{book}|{gate}"])
                - L.sharpe_of(series[f"I1r_ratio|{book}|{gate}"]),
                "delta_excess": cells[f"I1L_log|{book}|{gate}"]["excess_sharpe"]
                - cells[f"I1r_ratio|{book}|{gate}"]["excess_sharpe"],
                "boot": J.paired_block_bootstrap(
                    series[f"I1L_log|{book}|{gate}"], series[f"I1r_ratio|{book}|{gate}"]
                ),
                "clears_A": False,
            }

    # Z5 -- the mechanism test. The defect scales with LEVEL DRIFT, so the fix
    # should help most where the level moved most. A positive Z1 with a null Z5
    # would mean the fix helped by accident.
    drift = np.abs(np.log(panel.closes[:, -1] / panel.closes[:, start]))
    mech = {}
    for rung in CORRECTED:
        imp = psym[rung] - psym["I1_signal"]
        mech[rung] = {
            "corr_improvement_vs_log_drift": float(np.corrcoef(drift, imp)[0, 1]),
            "mean_improvement": float(imp.mean()),
            "symbols_improved": int((imp > 0).sum()),
        }

    return {
        "produced": "D232",
        "stage": "screen",
        "is_verdict": False,
        "seed": J.SEED,
        "n_boot": J.N_BOOT,
        "delta_hurdle": DELTA_HURDLE,
        "first_live_date": panel.dates[start],
        "last_date": panel.dates[-1],
        "live_bars": len(panel.dates) - start,
        "n_symbols": len(panel.symbols),
        "cells": cells,
        "deltas": deltas,
        "buy_and_hold": bh,
        "mechanism": mech,
        "elapsed_seconds": round(time.time() - t0, 1),
    }


ORDER = ("long_flat|none", "long_flat|200ma", "long_short|none", "long_short|200ma")


def render(p: dict) -> str:
    o = ["# D232 — the scale-corrected Impulse MACD\n"]
    o.append(
        "**STAGE 1 — SCREEN. Not a verdict.** The mined fixture cannot detect a subtle "
        "success; this establishes whether the corrected signal is a better baseline.\n"
    )
    o.append(
        f"*seed {p['seed']}, {p['n_boot']:,} bootstrap replications, {p['elapsed_seconds']}s. "
        f"{p['n_symbols']} symbols, {p['first_live_date']} to {p['last_date']}, "
        f"{p['live_bars']:,} live bars.*\n"
    )
    o.append("## The three rungs, long-flat, no gate\n")
    o.append("| rung | Sharpe | excess @rf=4% | CAGR | money | max DD | exposure | turnover |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    names = {"I1_signal": "I1 published", "I1r_ratio": "**I1r ratio**", "I1L_log": "**I1L log**"}
    for r in RUNGS:
        c = p["cells"][f"{r}|long_flat|none"]
        o.append(
            f"| {names[r]} | {c['sharpe']:+.3f} | {c['excess_sharpe']:+.3f} | "
            f"{c['cagr_with_dividends'] * 100:.2f}% | "
            f"{c['total_return_with_dividends'] * 100:+.2f}% | "
            f"{c['max_drawdown'] * 100:+.2f}% | {c['exposure'] * 100:.1f}% | "
            f"{c['turnover_units']:,} |"
        )
    bh = p["buy_and_hold"]
    o.append(
        f"| buy and hold | {bh['sharpe']:+.3f} | {bh['excess_sharpe']:+.3f} | "
        f"{bh['cagr_with_dividends'] * 100:.2f}% | "
        f"{bh['total_return_with_dividends'] * 100:+.2f}% | "
        f"{bh['max_drawdown'] * 100:+.2f}% | 100.0% | — |"
    )
    o.append("")
    o.append("## Hurdle A — the paired deltas\n")
    o.append("| comparison | book | gate | Δ Sharpe | Δ excess | boot p05 | boot p95 | A |")
    o.append("|---|---|---|---:|---:|---:|---:|:--:|")
    for rung in (*CORRECTED, "I1L_minus_I1r"):
        for cell in ORDER:
            d = p["deltas"][f"{rung}|{cell}"]
            b = d["boot"]
            o.append(
                f"| `{rung}` | {d['book']} | {d['gate']} | **{d['delta']:+.3f}** | "
                f"{d['delta_excess']:+.3f} | {b['p05']:+.3f} | {b['p95']:+.3f} | "
                f"{'PASS' if d['clears_A'] else '—'} |"
            )
    o.append("")
    o.append("## Z5 — the mechanism test\n")
    o.append(
        "The defect scales with **level drift**, so the fix should help most where the price "
        "level moved most. A positive result with a null correlation here would mean the fix "
        "helped by accident.\n"
    )
    o.append("| rung | corr(improvement, abs log drift) | mean per-symbol Δ | symbols improved |")
    o.append("|---|---:|---:|---:|")
    for r, m in p["mechanism"].items():
        o.append(
            f"| `{r}` | **{m['corr_improvement_vs_log_drift']:+.3f}** | "
            f"{m['mean_improvement']:+.4f} | {m['symbols_improved']} / {p['n_symbols']} |"
        )
    o.append("")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    if args.report_only:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    else:
        payload = build()
        SUMMARY.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    RESULTS.write_text(render(payload), encoding="utf-8")

    for r in RUNGS:
        c = payload["cells"][f"{r}|long_flat|none"]
        print(f"{r:12s} Sharpe {c['sharpe']:+.3f}  excess {c['excess_sharpe']:+.3f}  "
              f"expo {c['exposure']:.1%}  turn {c['turnover_units']:,}")
    print(f"{'BUY&HOLD':12s} Sharpe {payload['buy_and_hold']['sharpe']:+.3f}  "
          f"excess {payload['buy_and_hold']['excess_sharpe']:+.3f}")
    print()
    for rung in (*CORRECTED, "I1L_minus_I1r"):
        d = payload["deltas"][f"{rung}|long_flat|none"]
        print(f"{rung:16s} delta {d['delta']:+.3f}  excess {d['delta_excess']:+.3f}  "
              f"p05 {d['boot']['p05']:+.3f}  A={'PASS' if d['clears_A'] else 'fail'}")
    print()
    for r, m in payload["mechanism"].items():
        print(f"Z5 {r:12s} corr(improvement, |log drift|) = "
              f"{m['corr_improvement_vs_log_drift']:+.3f}   "
              f"{m['symbols_improved']}/{payload['n_symbols']} improved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
