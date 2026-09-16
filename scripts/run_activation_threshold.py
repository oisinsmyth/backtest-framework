"""D234 — the percentage activation threshold on the log construction.

    position = 1  if  hist_L > 0  AND  md_L > c

`md_L` is a dimensionless LOG-GAP: 0.01 means "the midline sits 1% outside the
channel", identically on every instrument. That is what makes a percentage
threshold expressible at all -- the published `md` is in dollars and has no
cross-instrument meaning.

Not a tenth filter on `hist`. It gates on the LEVEL rung, which carries its own
weak information (D218 measured I2 standalone at +0.129). D228's stop is
overridden in writing for this record only.

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
S = _load("d232_scale", "run_scale_corrected.py")
E = _load("d231_dial", "run_exposure_dial.py")

SUMMARY = REPO / "data" / "activation_threshold_summary.json"
RESULTS = REPO / "docs" / "results" / "ACTIVATION_THRESHOLD_RESULTS.md"

PPY = L.PPY
SEED = 0
LAG = 1
N_SIMS = 1000
RF_PER_BAR = E.RF_PER_BAR
RF_ANNUAL = E.RF_ANNUAL

# Declared in D234. Round numbers with physical meaning, chosen for
# interpretability rather than fitted.
THRESHOLDS = (0.0000, 0.0025, 0.0050, 0.0075, 0.0100)
FRESH_LOOKS = 5


def log_parts(bars):
    """`md_L` and `hist_L` together -- the level and its slope.

    Reuses D232's `_band_md` and `_hist` rather than restating the dead-zone rule,
    which is the piece most likely to drift between constructions."""
    h = [math.log(b.bar.high) for b in bars]
    lo = [math.log(b.bar.low) for b in bars]
    c = [math.log(b.bar.close) for b in bars]
    hlc3 = [(a + p + q) / 3.0 for a, p, q in zip(h, lo, c)]
    md = S._band_md(
        M.smma(h, M.IMPULSE_LENGTH), M.smma(lo, M.IMPULSE_LENGTH),
        M.zlema(hlc3, M.IMPULSE_LENGTH),
    )
    return np.asarray(md, dtype=float), np.asarray(S._hist(md, M.IMPULSE_SIGNAL), dtype=float)


def build() -> dict:
    t0 = time.time()
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    n, T = panel.closes.shape

    md = np.full((n, T), np.nan)
    hs = np.full((n, T), np.nan)
    for i, sym in enumerate(panel.symbols):
        md[i], hs[i] = log_parts(cleaned[sym])

    def book(mask):
        p = np.zeros((n, T))
        p[:, LAG:] = mask[:, :-LAG]
        p[:, :start] = 0.0
        return p

    ok = ~(np.isnan(md) | np.isnan(hs))
    baseline = book((hs > 0) & ok)
    par = E.score(panel, baseline, start)

    ones = np.ones((n, T))
    ones[:, :start] = 0.0
    bh = E.score(panel, ones, start)

    # the published rung, for continuity only -- not a candidate
    pub = S.arm_positions(panel, cleaned, "I1_signal", long_short=False, gated=False, start=start)
    published = E.score(panel, pub, start)

    cells, pos = [], {}
    for c in THRESHOLDS:
        name = f"md_L>{c * 100:.2f}%"
        p = book((hs > 0) & (md > c) & ok)
        pos[name] = p
        s = E.score(panel, p, start)
        pred = par["excess_sharpe"] * math.sqrt(s["exposure"] / par["exposure"])
        cells.append({
            "cell": name,
            "threshold": c,
            **s,
            "sqrt_f_predicted": pred,
            "selection_quality": (s["excess_sharpe"] / pred - 1.0) if pred else 0.0,
            "delta_vs_baseline": s["excess_sharpe"] - par["excess_sharpe"],
            "delta_money": s["total_return"] - par["total_return"],
            # D234 records that E fails on its per-symbol leg across the ladder.
            # Reported per cell rather than silently omitted.
            "clears_E_pooled": s["entries"] >= 100,
            "clears_E_per_symbol": s["min_entries_per_symbol"] >= 30,
            "levered_return_at_bh_vol": RF_ANNUAL + s["excess_sharpe"] * bh["vol"],
        })

    nulls = E.rotation_nulls(panel, pos, start, par["excess_sharpe"])
    for c in cells:
        c["beats_own_rotation_p95"] = bool(
            c["delta_vs_baseline"] > nulls["per_cell_p95"][c["cell"]]
        )
    best = max(cells, key=lambda c: c["delta_vs_baseline"])

    # W3 -- the sharp test. Does selection quality RISE with the threshold?
    xs = np.array([c["threshold"] for c in cells])
    ys = np.array([c["selection_quality"] for c in cells])
    w3 = {
        "slope_per_pct": float(np.polyfit(xs * 100, ys, 1)[0]),
        "corr": float(np.corrcoef(xs, ys)[0, 1]),
        "monotone_increasing": bool(np.all(np.diff(ys) > 0)),
    }

    return {
        "produced": "D234",
        "stage": "screen",
        "is_verdict": False,
        "seed": SEED,
        "n_sims": N_SIMS,
        "rf_annual": RF_ANNUAL,
        "first_live_date": panel.dates[start],
        "last_date": panel.dates[-1],
        "live_bars": T - start,
        "n_symbols": n,
        "baseline_I1L": par,
        "published_I1": published,
        "buy_and_hold": bh,
        "cells": cells,
        "nulls": nulls,
        "best_cell": best["cell"],
        "clears_B": bool(best["delta_vs_baseline"] > nulls["best_p95"]),
        "w3_selection_vs_threshold": w3,
        "ledger": {"fresh": FRESH_LOOKS, "with_inherited": FRESH_LOOKS + 62,
                   "verdict_count": FRESH_LOOKS + 45_803},
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    o = ["# D234 — the percentage activation threshold\n"]
    o.append(
        "**STAGE 1 — SCREEN. Not a verdict.** The mined fixture cannot detect a subtle "
        "success. The holdout is untouched.\n"
    )
    o.append(
        f"*seed {p['seed']}, {p['n_sims']:,} rotations, {p['elapsed_seconds']}s. "
        f"{p['n_symbols']} symbols, {p['first_live_date']} to {p['last_date']}, "
        f"{p['live_bars']:,} live bars. rf = {p['rf_annual']:.0%} on the exposed fraction.*\n"
    )
    o.append("## Baseline\n")
    o.append("| book | excess Sharpe | CAGR | vol | money | max DD | exposure |")
    o.append("|---|---:|---:|---:|---:|---:|---:|")
    for lab, s in (("**I1L — the baseline**", p["baseline_I1L"]),
                   ("I1 published (continuity)", p["published_I1"]),
                   ("buy and hold", p["buy_and_hold"])):
        o.append(
            f"| {lab} | {s['excess_sharpe']:+.3f} | {s['cagr'] * 100:.2f}% | "
            f"{s['vol'] * 100:.1f}% | {s['total_return'] * 100:+.2f}% | "
            f"{s['max_drawdown'] * 100:+.2f}% | {s['exposure'] * 100:.1f}% |"
        )
    o.append("")
    o.append("## The ladder\n")
    o.append(
        "`√f predicts` is what the cell scores from trading less **alone**. `selection` is what "
        "it earned above that.\n"
    )
    o.append("| c | exposure | excess Sharpe | √f predicts | **selection** | Δ baseline | money | min ent/sym | rotation |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|:--:|")
    for c in p["cells"]:
        o.append(
            f"| **{c['cell']}** | {c['exposure'] * 100:.1f}% | {c['excess_sharpe']:+.3f} | "
            f"{c['sqrt_f_predicted']:+.3f} | **{c['selection_quality'] * 100:+.0f}%** | "
            f"{c['delta_vs_baseline']:+.3f} | {c['total_return'] * 100:+.2f}% | "
            f"{c['min_entries_per_symbol']}{'' if c['clears_E_per_symbol'] else ' ✗'} | "
            f"{'**PASS**' if c['beats_own_rotation_p95'] else '—'} |"
        )
    o.append("")
    o.append(
        "*`✗` marks hurdle E failing on its per-symbol leg — known and stated before the run. "
        "Every cell is underpowered per symbol by construction.*\n"
    )
    w = p["w3_selection_vs_threshold"]
    o.append("## W3 — does the level rung carry information?\n")
    o.append(
        "The sharp test. If `md_L`'s level carries information, a higher bar should mean better "
        "trades and selection quality should **rise** with `c`. If it is noise, flat or falling.\n"
    )
    o.append(
        f"- slope: **{w['slope_per_pct'] * 100:+.1f}% of selection quality per 1% of threshold**\n"
        f"- correlation across the ladder: **{w['corr']:+.3f}**\n"
        f"- monotone increasing: **{'yes' if w['monotone_increasing'] else 'no'}**\n"
    )
    nl = p["nulls"]
    o.append("## Hurdle B — best-of-search rotation null\n")
    o.append(
        f"Best real **{max(c['delta_vs_baseline'] for c in p['cells']):+.3f}** against a null p95 "
        f"of **{nl['best_p95']:+.3f}** (p50 {nl['best_p50']:+.3f}). "
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

    par = payload["baseline_I1L"]
    print(f"I1L baseline    {par['excess_sharpe']:+.3f}  exposure {par['exposure']:.1%}")
    print(f"I1 published    {payload['published_I1']['excess_sharpe']:+.3f}")
    print(f"buy and hold    {payload['buy_and_hold']['excess_sharpe']:+.3f}")
    print()
    print(f"{'cell':14s} {'expo':>7s} {'exSh':>8s} {'sqrt-f':>8s} {'select':>8s} "
          f"{'d(base)':>8s} {'ent/sym':>8s}  rot")
    for c in payload["cells"]:
        print(f"{c['cell']:14s} {c['exposure']:6.1%} {c['excess_sharpe']:+8.3f} "
              f"{c['sqrt_f_predicted']:+8.3f} {c['selection_quality']:+7.0%} "
              f"{c['delta_vs_baseline']:+8.3f} {c['min_entries_per_symbol']:8d}  "
              f"{'PASS' if c['beats_own_rotation_p95'] else ' .  '}")
    w = payload["w3_selection_vs_threshold"]
    print()
    print(f"W3  selection vs threshold: slope {w['slope_per_pct'] * 100:+.1f}%/1%  "
          f"corr {w['corr']:+.3f}  monotone {w['monotone_increasing']}")
    print(f"hurdle B: best {max(c['delta_vs_baseline'] for c in payload['cells']):+.3f}  "
          f"null p95 {payload['nulls']['best_p95']:+.3f}  "
          f"{'CLEARS' if payload['clears_B'] else 'FAILS'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
