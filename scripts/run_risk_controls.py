"""D236 — portfolio-level risk controls on the recovery rule.

    C  cap total exposure at X by PROPORTIONAL SCALING
    R  hold only when SMA(50) > SMA(200) on the equal-weighted basket
    D  flat for 21 bars after the book's drawdown exceeds X

None of these touches WHICH trades are taken -- only how much of the book is
held. That is why D235's finding against trade-level stops does not carry over.

The primary hurdle is NOT Sharpe. Every control cuts exposure, so excess Sharpe
falls roughly as sqrt(f) whether or not the control is any good. The verdict is
CAGR / |max drawdown|.

R7's overlay null is applied: each control is compared against binding at RANDOM
bars, MATCHED on how often it really binds.

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
E = _load("d231_dial", "run_exposure_dial.py")
S = _load("d235_stops", "run_stops_targets.py")

SUMMARY = REPO / "data" / "risk_controls_summary.json"
RESULTS = REPO / "RISK_CONTROLS_RESULTS.md"

PPY = L.PPY
SEED = 0
N_NULL = 400

CAPS = (0.30, 0.40, 0.50)
DD_TRIGGERS = (0.05, 0.08)
DD_PAUSE = 21
REGIME_FAST, REGIME_SLOW = 50, 200
FRESH_LOOKS = 6


def sma1d(x: np.ndarray, w: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    c = np.cumsum(x)
    for i in range(w, len(x)):
        out[i] = (c[i] - c[i - w]) / w
    return out


def apply_cap(base: np.ndarray, cap: float) -> tuple[np.ndarray, np.ndarray]:
    """Scale every position proportionally when total exposure exceeds `cap`.

    PROPORTIONAL, not "keep the strongest N": ranking would introduce a selection
    decision, which is a different hypothesis. This uses no information the base
    rule did not already use."""
    tot = base.mean(axis=0)
    scale = np.where(tot > cap, cap / np.maximum(tot, 1e-12), 1.0)
    return base * scale[None, :], tot > cap


def regime_mask(panel, start: int) -> np.ndarray:
    """SMA(50) > SMA(200) on the equal-weighted basket, lag-shifted by one bar.

    The basket rather than a single index, so no instrument choice is smuggled in."""
    lr = np.diff(np.log(panel.closes), axis=1).mean(axis=0)
    idx = np.exp(np.cumsum(np.r_[0.0, lr]))
    f, s = sma1d(idx, REGIME_FAST), sma1d(idx, REGIME_SLOW)
    on = np.zeros(len(idx), dtype=bool)
    m = ~(np.isnan(f) | np.isnan(s))
    on[m] = f[m] > s[m]
    return np.r_[False, on[:-1]]          # decided at t-1, acted on at t


def apply_breaker(panel, base: np.ndarray, start: int, trigger: float, pause: int):
    """Flat for `pause` bars once the book's drawdown from peak exceeds `trigger`.

    The drawdown at close t is known at close t, so the pause takes effect from
    t+1. Walked bar by bar because the book's own path feeds back into its
    positions -- the equity curve must be rebuilt as the control acts, or the
    drawdown being reacted to is not the one the book actually experienced."""
    n, T = base.shape
    out = base.copy()
    eq, peak, until = 1.0, 1.0, -1
    bound = np.zeros(T, dtype=bool)
    for t in range(start, T):
        if t <= until:
            out[:, t] = 0.0
            bound[t] = True
        r = float(np.sum(out[:, t] * panel.total_log_returns[:, t]) / n)
        eq *= math.exp(r)
        peak = max(peak, eq)
        if eq / peak - 1.0 <= -trigger and t > until:
            until = t + pause                      # decided at close t, acts from t+1
    return out, bound


def overlay_null(panel, base: np.ndarray, controlled: np.ndarray, start: int,
                 bound: np.ndarray, seed: int = SEED) -> dict:
    """R7. Keep the base book; apply the SAME AMOUNT of holding-back at RANDOM bars.

    A rotation null would randomise the whole book's timing, which is the right
    question for an entry rule and the wrong one for a control that modifies an
    existing book (D235). What varies here is only WHEN the control binds."""
    rng = np.random.default_rng(seed)
    live = slice(start, None)
    # per-bar fraction of the book the real control held back
    held_back = base[:, live].mean(axis=0) - controlled[:, live].mean(axis=0)
    n_bind = int(bound[start:].sum())
    span = base.shape[1] - start
    out = np.empty(N_NULL)
    pool = held_back[held_back > 1e-12]
    for k in range(N_NULL):
        p = base.copy()
        if n_bind and len(pool):
            where = rng.choice(span, size=n_bind, replace=False)
            amounts = rng.choice(pool, size=n_bind, replace=True)
            tot = p[:, live].mean(axis=0)
            sc = np.ones(span)
            keep = tot[where] > 1e-12
            sc[where[keep]] = np.maximum(
                0.0, 1.0 - amounts[keep] / tot[where[keep]]
            )
            p[:, live] = p[:, live] * sc[None, :]
        out[k] = E._excess_sharpe(panel, p, start)
    return {"n_sims": N_NULL, "p05": float(np.percentile(out, 5)),
            "p50": float(np.percentile(out, 50)),
            "p95": float(np.percentile(out, 95)), "max": float(out.max())}


def build() -> dict:
    t0 = time.time()
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    md, hs, ok = S.base_masks(panel, cleaned, start)
    base = S.hold_book((hs > 0) & (md <= 0) & ok, start)
    par = E.score(panel, base, start)
    par["calmar"] = par["cagr"] / abs(par["max_drawdown"])

    ones = np.ones_like(base)
    ones[:, :start] = 0.0
    bh = E.score(panel, ones, start)
    bh["calmar"] = bh["cagr"] / abs(bh["max_drawdown"])

    reg = regime_mask(panel, start)
    cells = []
    for cap in CAPS:
        p, b = apply_cap(base, cap)
        cells.append((f"C@{cap * 100:.0f}%", "C", p, b))
    rp = base * reg[None, :]
    cells.append((f"R SMA{REGIME_FAST}>{REGIME_SLOW}", "R", rp, ~reg))
    for tr in DD_TRIGGERS:
        p, b = apply_breaker(panel, base, start, tr, DD_PAUSE)
        cells.append((f"D@{tr * 100:.0f}%", "D", p, b))

    out = []
    for name, fam, pos, bound in cells:
        s = E.score(panel, pos, start)
        s["calmar"] = s["cagr"] / abs(s["max_drawdown"]) if s["max_drawdown"] else 0.0
        pred = par["excess_sharpe"] * math.sqrt(s["exposure"] / par["exposure"])
        nl = overlay_null(panel, base, pos, start, bound)
        out.append({
            "cell": name, "family": fam, **s,
            "sqrt_f_predicted": pred,
            "selection_quality": (s["excess_sharpe"] / pred - 1.0) if pred else 0.0,
            "delta_sharpe": s["excess_sharpe"] - par["excess_sharpe"],
            "delta_calmar": s["calmar"] - par["calmar"],
            "binds_pct": float(bound[start:].mean()),
            "clears_K1": s["max_drawdown"] > par["max_drawdown"],
            "clears_K2": s["calmar"] > par["calmar"],
            "overlay_null": nl,
            "clears_N": bool(s["excess_sharpe"] > nl["p95"]),
        })

    return {
        "produced": "D236", "stage": "screen", "is_verdict": False,
        "seed": SEED, "n_null": N_NULL,
        "first_live_date": panel.dates[start], "last_date": panel.dates[-1],
        "live_bars": panel.closes.shape[1] - start, "n_symbols": len(panel.symbols),
        "baseline_recovery": par, "buy_and_hold": bh, "cells": out,
        "regime_on_share": float(reg[start:].mean()),
        "ledger": {"fresh": FRESH_LOOKS, "with_d234_d235": FRESH_LOOKS + 13,
                   "verdict_count": FRESH_LOOKS + 13 + 45_803},
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    o = ["# D236 — portfolio-level risk controls\n"]
    o.append("**STAGE 1 — SCREEN. Not a verdict.** Holdout and forward window untouched.\n")
    o.append(
        f"*seed {p['seed']}, {p['n_null']} overlay-null replications per cell, "
        f"{p['elapsed_seconds']}s. {p['n_symbols']} symbols, {p['first_live_date']} to "
        f"{p['last_date']}, {p['live_bars']:,} live bars.*\n"
    )
    par, bh = p["baseline_recovery"], p["buy_and_hold"]
    o.append("## Baseline\n")
    o.append("| book | excess Sharpe | CAGR | max DD | **CAGR/\\|DD\\|** | vol | exposure |")
    o.append("|---|---:|---:|---:|---:|---:|---:|")
    for lab, s in (("**recovery — baseline**", par), ("buy and hold", bh)):
        o.append(
            f"| {lab} | {s['excess_sharpe']:+.3f} | {s['cagr'] * 100:.2f}% | "
            f"{s['max_drawdown'] * 100:+.2f}% | **{s['calmar']:.3f}** | "
            f"{s['vol'] * 100:.1f}% | {s['exposure'] * 100:.1f}% |"
        )
    o.append("")
    o.append("## The six controls\n")
    o.append("| cell | binds | exposure | max DD | CAGR/\\|DD\\| | Δ | excess Sharpe | √f | K1 | K2 | N |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|")
    for c in p["cells"]:
        o.append(
            f"| **{c['cell']}** | {c['binds_pct'] * 100:.1f}% | {c['exposure'] * 100:.1f}% | "
            f"{c['max_drawdown'] * 100:+.2f}% | {c['calmar']:.3f} | "
            f"{c['delta_calmar']:+.3f} | {c['excess_sharpe']:+.3f} | "
            f"{c['sqrt_f_predicted']:+.3f} | {'✓' if c['clears_K1'] else '—'} | "
            f"{'**✓**' if c['clears_K2'] else '—'} | {'**✓**' if c['clears_N'] else '—'} |"
        )
    o.append("")
    o.append("## N — the overlay null (R7)\n")
    o.append(
        "Keep the base book; hold back the **same amount at random bars**, matched on how "
        "often the control really binds. If a control does no better than that, its *timing* "
        "carries nothing.\n"
    )
    o.append("| cell | real excess Sharpe | null p50 | null p95 | clears |")
    o.append("|---|---:|---:|---:|:--:|")
    for c in p["cells"]:
        nl = c["overlay_null"]
        o.append(
            f"| {c['cell']} | **{c['excess_sharpe']:+.3f}** | {nl['p50']:+.3f} | "
            f"{nl['p95']:+.3f} | {'**PASS**' if c['clears_N'] else '—'} |"
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

    par = payload["baseline_recovery"]
    print(f"baseline   exSh {par['excess_sharpe']:+.3f}  CAGR {par['cagr']:.2%}  "
          f"maxDD {par['max_drawdown']:+.2%}  CAGR/DD {par['calmar']:.3f}  "
          f"expo {par['exposure']:.1%}")
    bh = payload["buy_and_hold"]
    print(f"buy&hold   exSh {bh['excess_sharpe']:+.3f}  CAGR {bh['cagr']:.2%}  "
          f"maxDD {bh['max_drawdown']:+.2%}  CAGR/DD {bh['calmar']:.3f}")
    print()
    print(f"{'cell':16s} {'binds':>6s} {'expo':>7s} {'maxDD':>8s} {'CAGR/DD':>8s} {'dCalmar':>8s} "
          f"{'exSh':>8s} {'sqrt-f':>8s} {'nullp95':>8s}  K1 K2  N")
    for c in payload["cells"]:
        nl = c["overlay_null"]
        print(f"{c['cell']:16s} {c['binds_pct']:5.1%} {c['exposure']:6.1%} "
              f"{c['max_drawdown']:+7.2%} {c['calmar']:8.3f} {c['delta_calmar']:+8.3f} "
              f"{c['excess_sharpe']:+8.3f} {c['sqrt_f_predicted']:+8.3f} {nl['p95']:+8.3f}  "
              f"{'Y' if c['clears_K1'] else '.'}  {'Y' if c['clears_K2'] else '.'}  "
              f"{'Y' if c['clears_N'] else '.'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
