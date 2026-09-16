"""D235 — stops and targets on the recovery rule.

Baseline:  position = 1 if hist_L > 0 AND md_L <= 0

    BE  breakeven stop, ARMS ONLY after +X%, then exits at entry.
        Never touches the entry dip -- the thing fixed stops destroy.
    PT  bank half at +X%, let the remainder run to the natural exit.
    DT  hysteresis: enter below the channel, hold until md_L > c.

EVERY EXIT IS CLOSE-TO-CLOSE. D224 produced a gross Sharpe of +4.197 from a stop
that escaped an adverse move it could not have escaped. On daily OHLC there is no
way to know whether an intrabar touch filled at the level or gapped through it,
so no intrabar fill is assumed anywhere. A level is breached only if the CLOSE
breaches it, and the exit takes effect on the FOLLOWING bar.

Stage 1 only. The holdout and the 2025-2026 forward window are not touched.
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
A = _load("d234_activation", "run_activation_threshold.py")
E = _load("d231_dial", "run_exposure_dial.py")
F = _load("d228_filter", "run_filter_search.py")

SUMMARY = REPO / "data" / "stops_targets_summary.json"
RESULTS = REPO / "docs" / "results" / "STOPS_TARGETS_RESULTS.md"

PPY = L.PPY
SEED = 0
LAG = 1
N_SIMS = 1000

# Declared in D235.
BE_ARMS = (0.03, 0.06)          # 3% is the measured median best-gain-from-entry
PT_LEVELS = (0.03, 0.06)
DT_BANDS = (0.005, 0.010, 0.020)
FRESH_LOOKS = 7


def base_masks(panel, cleaned, start):
    n, T = panel.closes.shape
    md = np.full((n, T), np.nan)
    hs = np.full((n, T), np.nan)
    for i, sym in enumerate(panel.symbols):
        md[i], hs[i] = A.log_parts(cleaned[sym])
    ok = ~(np.isnan(md) | np.isnan(hs))
    return md, hs, ok


def hold_book(mask, start):
    """A memoryless level rule, lag-shifted. `position[t]` is decided on `t-1`."""
    p = np.zeros_like(mask, dtype=float)
    p[:, LAG:] = mask[:, :-LAG]
    p[:, :start] = 0.0
    return p


def overlay(base_pos, closes, start, *, mode, level):
    """Apply a stateful exit overlay to an existing position matrix.

    THE CONVENTION, stated because it decides the result: `position[t]` earns
    `log(C[t]/C[t-1])`, so a position held at bar `a` was bought at `C[a-1]`.
    Entry price is therefore the close BEFORE exposure begins, which is also what
    the trade-anatomy measurement used.

    At the close of bar `t` the trade's gain is known, so an exit decided there
    takes effect from `t+1`. Nothing reads a price it could not have seen.

    ONCE STOPPED, STAY FLAT UNTIL THE BASE SIGNAL CYCLES. Re-entering while the
    level rule is still true would defeat the stop entirely -- you would be
    stopped out and immediately back in at the same price."""
    out = base_pos.copy()
    sym, s0, e0 = F.trade_spans(base_pos)
    for i, a, b in zip(sym, s0, e0):
        if a < start or a == 0:
            continue
        entry = closes[i, a - 1]
        armed = False
        for t in range(a, b):
            g = closes[i, t] / entry - 1.0
            if mode == "BE":
                if not armed and g >= level:
                    armed = True
                elif armed and g <= 0.0:
                    out[i, t + 1 : b] = 0.0        # decided at close t, effective t+1
                    break
            elif mode == "PT":
                if g >= level:
                    out[i, t + 1 : b] = 0.5
                    break
    return out


def delayed_target(md, hs, ok, closes, start, band):
    """DT — a HYSTERESIS rule: the entry band and the exit band differ.

    Enter when `hist_L > 0 AND md_L <= 0` (below the channel and climbing); hold
    while `hist_L > 0 AND md_L <= band`. Stateful by construction, so it is walked
    rather than masked."""
    n, T = md.shape
    enter = (hs > 0) & (md <= 0.0) & ok
    hold = (hs > 0) & (md <= band) & ok
    sig = np.zeros((n, T), dtype=float)
    for i in range(n):
        on = False
        for t in range(start - 1, T):
            on = (on and hold[i, t]) or enter[i, t]
            sig[i, t] = 1.0 if on else 0.0
    return hold_book(sig.astype(bool), start)


def build() -> dict:
    t0 = time.time()
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    md, hs, ok = base_masks(panel, cleaned, start)
    C = panel.closes

    base = hold_book((hs > 0) & (md <= 0) & ok, start)
    par = E.score(panel, base, start)

    ones = np.ones_like(base)
    ones[:, :start] = 0.0
    bh = E.score(panel, ones, start)

    cells, pos = [], {}
    for x in BE_ARMS:
        pos[f"BE@{x * 100:.0f}%"] = overlay(base, C, start, mode="BE", level=x)
    for x in PT_LEVELS:
        pos[f"PT@{x * 100:.0f}%"] = overlay(base, C, start, mode="PT", level=x)
    for c in DT_BANDS:
        pos[f"DT@{c * 100:.1f}%"] = delayed_target(md, hs, ok, C, start, c)

    for name, p in pos.items():
        s = E.score(panel, p, start)
        pred = par["excess_sharpe"] * math.sqrt(s["exposure"] / par["exposure"])
        cells.append({
            "cell": name,
            "family": name.split("@")[0],
            **s,
            "sqrt_f_predicted": pred,
            "selection_quality": (s["excess_sharpe"] / pred - 1.0) if pred else 0.0,
            "delta_vs_baseline": s["excess_sharpe"] - par["excess_sharpe"],
            "delta_money": s["total_return"] - par["total_return"],
            "clears_P": s["excess_sharpe"] > par["excess_sharpe"],
        })

    nulls = E.rotation_nulls(panel, pos, start, par["excess_sharpe"])
    for c in cells:
        c["beats_own_rotation_p95"] = bool(
            c["delta_vs_baseline"] > nulls["per_cell_p95"][c["cell"]]
        )
    best = max(cells, key=lambda c: c["delta_vs_baseline"])

    fam = {}
    for f in ("BE", "PT", "DT"):
        d = [c["delta_vs_baseline"] for c in cells if c["family"] == f]
        fam[f] = {"mean_delta": float(np.mean(d)), "best_delta": float(max(d))}

    return {
        "produced": "D235",
        "stage": "screen",
        "is_verdict": False,
        "seed": SEED,
        "n_sims": N_SIMS,
        "first_live_date": panel.dates[start],
        "last_date": panel.dates[-1],
        "live_bars": C.shape[1] - start,
        "n_symbols": len(panel.symbols),
        "baseline_recovery": par,
        "buy_and_hold": bh,
        "cells": cells,
        "family_summary": fam,
        "nulls": nulls,
        "best_cell": best["cell"],
        "clears_B": bool(best["delta_vs_baseline"] > nulls["best_p95"]),
        "ledger": {"fresh": FRESH_LOOKS, "with_d234": FRESH_LOOKS + 6,
                   "verdict_count": FRESH_LOOKS + 6 + 45_803},
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    o = ["# D235 — stops and targets on the recovery rule\n"]
    o.append(
        "**STAGE 1 — SCREEN. Not a verdict.** The holdout and the 2025–2026 forward window "
        "are untouched.\n"
    )
    o.append(
        f"*seed {p['seed']}, {p['n_sims']:,} rotations, {p['elapsed_seconds']}s. "
        f"{p['n_symbols']} symbols, {p['first_live_date']} to {p['last_date']}, "
        f"{p['live_bars']:,} live bars. All exits close-to-close, effective the following bar.*\n"
    )
    par, bh = p["baseline_recovery"], p["buy_and_hold"]
    o.append("## Baseline\n")
    o.append("| book | excess Sharpe | CAGR | vol | money | max DD | exposure |")
    o.append("|---|---:|---:|---:|---:|---:|---:|")
    for lab, s in (("**recovery — the baseline**", par), ("buy and hold", bh)):
        o.append(
            f"| {lab} | {s['excess_sharpe']:+.3f} | {s['cagr'] * 100:.2f}% | "
            f"{s['vol'] * 100:.1f}% | {s['total_return'] * 100:+.2f}% | "
            f"{s['max_drawdown'] * 100:+.2f}% | {s['exposure'] * 100:.1f}% |"
        )
    o.append("")
    o.append("## The seven cells\n")
    o.append("| cell | exposure | excess Sharpe | √f predicts | selection | Δ baseline | money | rotation |")
    o.append("|---|---:|---:|---:|---:|---:|---:|:--:|")
    for c in p["cells"]:
        o.append(
            f"| **{c['cell']}** | {c['exposure'] * 100:.1f}% | {c['excess_sharpe']:+.3f} | "
            f"{c['sqrt_f_predicted']:+.3f} | {c['selection_quality'] * 100:+.0f}% | "
            f"{c['delta_vs_baseline']:+.3f} | {c['total_return'] * 100:+.2f}% | "
            f"{'**PASS**' if c['beats_own_rotation_p95'] else '—'} |"
        )
    o.append("")
    o.append("## V2 — the mechanism test\n")
    o.append(
        "`BE` is the only variant that neither cuts the entry dip nor caps the tail. If it does "
        "*not* do least harm, then \"stops fail because they cut the entry dip\" is the wrong "
        "explanation.\n"
    )
    o.append("| family | mean Δ | best Δ |")
    o.append("|---|---:|---:|")
    for f, v in p["family_summary"].items():
        o.append(f"| **{f}** | {v['mean_delta']:+.3f} | {v['best_delta']:+.3f} |")
    o.append("")
    nl = p["nulls"]
    o.append("## Hurdle B\n")
    o.append(
        f"Best real **{max(c['delta_vs_baseline'] for c in p['cells']):+.3f}** against a "
        f"null p95 of **{nl['best_p95']:+.3f}**. "
        f"**{'CLEARS' if p['clears_B'] else 'FAILS'}.**\n"
    )
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

    par = payload["baseline_recovery"]
    print(f"recovery baseline   {par['excess_sharpe']:+.3f}  exposure {par['exposure']:.1%}  "
          f"money {par['total_return']:+.2%}")
    print(f"buy and hold        {payload['buy_and_hold']['excess_sharpe']:+.3f}")
    print()
    print(f"{'cell':10s} {'expo':>7s} {'exSh':>8s} {'sqrt-f':>8s} {'select':>8s} "
          f"{'d(base)':>8s} {'money':>9s}  rot")
    for c in payload["cells"]:
        print(f"{c['cell']:10s} {c['exposure']:6.1%} {c['excess_sharpe']:+8.3f} "
              f"{c['sqrt_f_predicted']:+8.3f} {c['selection_quality']:+7.0%} "
              f"{c['delta_vs_baseline']:+8.3f} {c['total_return']:+8.2%}  "
              f"{'PASS' if c['beats_own_rotation_p95'] else ' .  '}")
    print()
    for f, v in payload["family_summary"].items():
        print(f"V2  {f}  mean delta {v['mean_delta']:+.3f}   best {v['best_delta']:+.3f}")
    print(f"hurdle B: best {max(c['delta_vs_baseline'] for c in payload['cells']):+.3f}  "
          f"null p95 {payload['nulls']['best_p95']:+.3f}  "
          f"{'CLEARS' if payload['clears_B'] else 'FAILS'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
