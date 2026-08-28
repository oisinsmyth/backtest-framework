"""D239 — time-series momentum as arm two.

    position = 1  if  close[t] > close[t - 252]      (12-month price return > 0)
               0  otherwise

Three cells:

    T1  all 57                     58.31% exposure
    T2  the non-equity subset      49.81%, 11 instruments, partitioned by ASSET
                                   CLASS and fixed in D239 before the run
    T3  a declared 50/50 capital blend of S1 and T1

THE PRIMARY HURDLE IS THE ROTATION NULL. A 58%-exposed long-flat book, in a
market that rose 8.42%/yr, posts a positive Sharpe for entirely trivial reasons.
Only a matched-count rotation -- same exposure, same turnover, same holding
periods, wrong bars -- separates trend TIMING from BEING INVESTED A LOT.

D212: the scorer, the financing, the rotation null and its money/volatility legs
are all D238's `run_short_mirror`, unchanged. That module was written to be the
general signed-book scorer and this is its first reuse. Written fresh here: the
252-bar signal, the asset-class partition, and the blend.

STAGE 1 ONLY. The holdout 60 and the 2025-2026 forward window are not touched.

Offline, deterministic, seed 0. `--report-only` re-renders from the artifact.
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


X = _load("d238_mirror", "run_short_mirror.py")
L, S, J = X.L, X.S, X.J

SUMMARY = REPO / "data" / "tsmom_arm_summary.json"
RESULTS = REPO / "TSMOM_ARM_RESULTS.md"

PPY = X.PPY
SEED = X.SEED
LAG = X.LAG
RF_ANNUAL = X.RF_ANNUAL
RF_PER_BAR = X.RF_PER_BAR

# D239's one constant, and it is the canonical one -- 12 months, the value
# time-series momentum has been published at since Moskowitz-Ooi-Pedersen (2012).
LOOKBACK = 252

# Partitioned by ASSET CLASS, not by performance, and fixed in the record before
# the run. GDX and GDXJ are EQUITY securities and are classified as such despite
# being metals-driven -- the strict reading, chosen so the split cannot be tuned.
NON_EQUITY = frozenset(
    {"AGG", "GLD", "HYG", "IEF", "LQD", "SHY", "SLV", "TIP", "TLT", "UNG", "USO"}
)

BLEND_WEIGHT = 0.5  # declared, not optimised

CELL_ORDER = ("S1", "T1", "T2", "T3")


def subset_panel(panel, rows):
    """A panel restricted to `rows`, so an N-name book is equal-weighted over N.

    THIS EXISTS BECAUSE THE OBVIOUS SHORTCUT IS WRONG. Zeroing the unwanted rows of
    a 57-row position matrix leaves `portfolio_log_returns` dividing by 57, so an
    11-name book at 49.8% exposure scores as a 57-name book at 9.6%. The registered
    exposure caught it -- which is the argument for disclosing exposure before the
    run rather than reporting it after."""
    r = list(rows)
    return type(panel)(
        symbols=tuple(panel.symbols[i] for i in r),
        closes=panel.closes[r],
        log_returns=panel.log_returns[r],
        cost_fraction=panel.cost_fraction[r],
        dates=panel.dates,
        total_log_returns=panel.total_log_returns[r],
    )


def tsmom_positions(panel, start: int, rows=None) -> np.ndarray:
    """`close[t] > close[t-252]`, lag-shifted so bar t is decided at t-1.

    The signal is computed on PRICE and the scoring on TOTAL RETURN -- D217's
    standing convention, because rewriting the price to smuggle dividends into the
    signal would be a different rule wearing the same name."""
    c = panel.closes
    n, T = c.shape
    sig = np.zeros((n, T), dtype=bool)
    sig[:, LOOKBACK:] = c[:, LOOKBACK:] > c[:, :-LOOKBACK]
    pos = np.zeros((n, T))
    pos[:, LAG:] = sig[:, :-LAG]
    pos[:, :start] = 0.0
    if rows is not None:
        keep = np.zeros(n, dtype=bool)
        keep[list(rows)] = True
        pos[~keep] = 0.0
    return pos


def deployable(cell: dict) -> float:
    """CAGR with T-bills credited on the idle fraction.

    Every CAGR in this programme credits idle cash NOTHING -- the scorer earns
    `position * return`, so a flat bar earns zero. For a book that is flat most of
    the time that materially understates what it would actually pay, and it is the
    number D239 says the case will be made or lost on."""
    return float(np.expm1(np.log1p(cell["cagr"]) + math.log1p(RF_ANNUAL)
                          * (1.0 - cell["exposure_gross"])))


def build() -> dict:
    t0 = time.time()
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    assert LOOKBACK < start, "the signal must be defined from the shared start bar"

    md, hs, ok = S.base_masks(panel, cleaned, start)
    s1 = S.hold_book((hs > 0) & (md <= 0) & ok, start)

    non_eq = [i for i, sym in enumerate(panel.symbols) if sym in NON_EQUITY]
    assert len(non_eq) == len(NON_EQUITY), "a declared non-equity symbol is missing"

    t1 = tsmom_positions(panel, start)
    t3 = BLEND_WEIGHT * s1 + (1.0 - BLEND_WEIGHT) * t1

    # T2 lives on its OWN panel of 11 names, equal-weighted over 11 -- see
    # `subset_panel`. It therefore gets its own scorer and its own rotation null.
    panel2 = subset_panel(panel, non_eq)
    t2 = tsmom_positions(panel2, start)

    ones = np.ones_like(s1)
    ones[:, :start] = 0.0

    positions = {"S1": s1, "T1": t1, "T3": t3}
    cells = {k: X.score(panel, positions[k], start) for k in ("S1", "T1", "T3")}
    cells["T2"] = X.score(panel2, t2, start)
    bh = X.score(panel, ones, start)

    # S1 must not have moved. If the comparison arm shifts, the study is void.
    assert abs(cells["S1"]["excess_sharpe"] - 0.746) < 5e-4, "S1 moved"
    assert abs(cells["S1"]["exposure_gross"] - 0.1887) < 5e-4, "S1's exposure moved"

    def excess(pnl, pos):
        total = X.signed_log_returns(pnl, pos, total_return=True)[start:]
        return X.excess_of(total, pos, start)

    r_s1, r_t1, r_t3 = (excess(panel, p) for p in (s1, t1, t3))
    r_t2 = excess(panel2, t2)

    nl = X.rotation_nulls(panel, {"T1": t1, "T3": t3}, start)
    nl2 = X.rotation_nulls(panel2, {"T2": t2}, start)
    for key in ("draws", "money", "vol"):
        nl[key] = {**nl[key], **nl2[key]}
    nulls = {}
    for k, draws in nl["draws"].items():
        actual = cells[k]["excess_sharpe"]
        m_draws, v_draws = nl["money"][k], nl["vol"][k]
        nulls[k] = {
            "p50": float(np.percentile(draws, 50)),
            "p95": float(np.percentile(draws, 95)),
            "sd": float(np.std(draws, ddof=1)),
            "percentile_of_actual": float((draws < actual).mean() * 100.0),
            "clears_P3": bool(actual > float(np.percentile(draws, 95))),
            "money_p50": float(np.percentile(m_draws, 50)),
            "money_percentile_of_actual": float(
                (m_draws < cells[k]["total_return"]).mean() * 100.0
            ),
            "vol_p50": float(np.percentile(v_draws, 50)),
            "vol_ratio_actual_over_null": float(
                cells[k]["vol"] / np.percentile(v_draws, 50)
            ),
        }

    sr_s1 = cells["S1"]["excess_sharpe"]
    rho = {k: float(np.corrcoef(r_s1, r)[0, 1]) for k, r in (("T1", r_t1), ("T2", r_t2))}
    p1 = {
        k: {
            "rho": rho[k],
            "bar": rho[k] * sr_s1,
            "actual": cells[k]["excess_sharpe"],
            "clears_P1": bool(cells[k]["excess_sharpe"] > rho[k] * sr_s1),
        }
        for k in ("T1", "T2")
    }

    boot = J.paired_block_bootstrap(r_t3, r_s1)
    p2 = {
        "delta_t3_minus_s1": cells["T3"]["excess_sharpe"] - sr_s1,
        "bootstrap": boot,
        "clears_P2": bool(cells["T3"]["excess_sharpe"] > sr_s1 and boot["p05"] > 0.0),
    }

    # sqrt(f): what a SELECTION-FREE book at each cell's exposure would score, and
    # the selection quality implied by the gap. D231's decomposition.
    bh_sh = bh["excess_sharpe"]
    root_f = {}
    for k in ("T1", "T2", "T3"):
        f = cells[k]["exposure_gross"]
        pred = bh_sh * math.sqrt(f)
        root_f[k] = {
            "exposure": f,
            "sqrt_f_prediction": pred,
            "selection_quality": (cells[k]["excess_sharpe"] / pred - 1.0) if pred else None,
        }

    return {
        "produced": "D239",
        "stage": "screen (mined 57) -- the holdout and forward window are untouched",
        "seed": SEED,
        "n_sims": X.N_SIMS,
        "lookback": LOOKBACK,
        "blend_weight": BLEND_WEIGHT,
        "rf_annual": RF_ANNUAL,
        "non_equity": sorted(NON_EQUITY),
        "n_symbols": len(panel.symbols),
        "live_bars": len(panel.dates) - start,
        "first_live_date": panel.dates[start],
        "last_date": panel.dates[-1],
        "cells": cells,
        "buy_and_hold": bh,
        "deployable_return": {k: deployable(cells[k]) for k in CELL_ORDER}
        | {"buy_and_hold": deployable(bh)},
        "nulls": nulls,
        "p1": p1,
        "p2": p2,
        "sqrt_f": root_f,
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    c, n, s = p["cells"], p["nulls"], p["sqrt_f"]
    dep, b = p["deployable_return"], p["buy_and_hold"]
    o = ["# D239 — time-series momentum as arm two\n"]
    o.append(f"**STAGE 1 — A SCREEN, NOT A VERDICT.** {p['stage']}\n")
    o.append(
        f"*seed {p['seed']}, {p['n_sims']:,} rotations, {p['elapsed_seconds']}s. "
        f"{p['n_symbols']} ETFs x {p['live_bars']:,} live bars, "
        f"{p['first_live_date'][:10]} .. {p['last_date'][:10]}. "
        f"Lookback {p['lookback']} bars; blend {p['blend_weight']:.0%}/"
        f"{1 - p['blend_weight']:.0%}.*\n"
    )

    rules = {
        "S1": "the recovery rule (arm one)",
        "T1": "`close[t] > close[t−252]`, all 57",
        "T2": "the same rule, non-equity 11",
        "T3": "50/50 blend of S1 and T1",
    }
    o.append("## The four books\n")
    o.append(
        "| | rule | exposure | excess Sharpe | CAGR | **deployable** | vol | max DD | "
        "Calmar | E |"
    )
    o.append("|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|")
    for k in CELL_ORDER:
        x = c[k]
        cal = x["cagr"] / abs(x["max_drawdown"]) if x["max_drawdown"] else float("nan")
        o.append(
            f"| **{k}** | {rules[k]} | {x['exposure_gross']:.1%} | "
            f"**{x['excess_sharpe']:+.3f}** | {x['cagr'] * 100:.2f}% | "
            f"**{dep[k] * 100:.2f}%** | {x['vol'] * 100:.1f}% | "
            f"{x['max_drawdown'] * 100:+.2f}% | {cal:.3f} | "
            f"{'✓' if x['clears_E'] else '✗'} |"
        )
    cal_b = b["cagr"] / abs(b["max_drawdown"])
    o.append(
        f"| B&H | always long | 100.0% | {b['excess_sharpe']:+.3f} | "
        f"{b['cagr'] * 100:.2f}% | {dep['buy_and_hold'] * 100:.2f}% | "
        f"{b['vol'] * 100:.1f}% | {b['max_drawdown'] * 100:+.2f}% | {cal_b:.3f} | — |"
    )
    o.append("")
    o.append(
        "***deployable*** *credits T-bills at "
        f"{p['rf_annual']:.0%} on the idle fraction. Every CAGR in this programme earns "
        "nothing on cash, which materially understates a book that is flat most of the "
        "time.*\n"
    )

    o.append("## P3 — the rotation null, and why it is the primary\n")
    o.append(
        "*A 58%-exposed long-flat book, in a market that rose 8.42%/yr, posts a positive "
        "Sharpe for entirely trivial reasons. Same exposure, same turnover, same holding "
        "periods, wrong bars — this is what separates trend **timing** from **being "
        "invested a lot**.*\n"
    )
    o.append(
        "| | actual | null p50 | null p95 | **percentile** | money pct | vol ratio | P3 |"
    )
    o.append("|---|---:|---:|---:|---:|---:|---:|:--:|")
    for k in ("T1", "T2", "T3"):
        o.append(
            f"| **{k}** | **{c[k]['excess_sharpe']:+.3f}** | {n[k]['p50']:+.3f} | "
            f"{n[k]['p95']:+.3f} | **{n[k]['percentile_of_actual']:.1f}th** | "
            f"{n[k]['money_percentile_of_actual']:.1f}th | "
            f"{n[k]['vol_ratio_actual_over_null']:.3f}x | "
            f"{'✓' if n[k]['clears_P3'] else '✗'} |"
        )
    o.append("")

    o.append("## P4 — versus buy-and-hold, with the √f decomposition\n")
    o.append(
        "| | exposure | √f predicts | actual | **selection quality** | beats B&H |"
    )
    o.append("|---|---:|---:|---:|---:|:--:|")
    for k in ("T1", "T2", "T3"):
        q = s[k]
        o.append(
            f"| **{k}** | {q['exposure']:.1%} | {q['sqrt_f_prediction']:+.3f} | "
            f"{c[k]['excess_sharpe']:+.3f} | **{q['selection_quality'] * 100:+.1f}%** | "
            f"{'✓' if c[k]['excess_sharpe'] > b['excess_sharpe'] else '✗'} |"
        )
    o.append("")
    o.append(
        f"*√f predicts what a **selection-free** book at that exposure would score, from "
        f"buy-and-hold's {b['excess_sharpe']:+.3f}.*\n"
    )

    o.append("## P1 — the diversification condition, which needs no weighting choice\n")
    o.append("*Adding an arm raises the book's maximum attainable Sharpe iff "
             "`SR_B > ρ · SR_A`.*\n")
    o.append("| | ρ with S1 | bar `ρ × 0.746` | actual | P1 |")
    o.append("|---|---:|---:|---:|:--:|")
    for k in ("T1", "T2"):
        q = p["p1"][k]
        o.append(
            f"| **{k}** | {q['rho']:+.4f} | {q['bar']:+.3f} | **{q['actual']:+.3f}** | "
            f"{'✓' if q['clears_P1'] else '✗'} |"
        )
    o.append("")

    q = p["p2"]
    o.append("## P2 — does a declared 50/50 blend beat S1 alone?\n")
    o.append(
        f"| | excess Sharpe |\n|---|---:|\n"
        f"| S1 alone | {c['S1']['excess_sharpe']:+.3f} |\n"
        f"| **T3 blend** | **{c['T3']['excess_sharpe']:+.3f}** |\n"
        f"| **delta** | **{q['delta_t3_minus_s1']:+.3f}** |\n"
        f"| paired bootstrap p05 | {q['bootstrap']['p05']:+.3f} |\n"
        f"| paired bootstrap p95 | {q['bootstrap']['p95']:+.3f} |\n"
        f"| **P2** | **{'✓ CLEARS' if q['clears_P2'] else '✗ FAILS'}** |\n"
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

    c, n, dep = payload["cells"], payload["nulls"], payload["deployable_return"]
    print()
    print(f"{'cell':5s} {'expo':>7s} {'exSh':>8s} {'CAGR':>8s} {'deploy':>8s} "
          f"{'maxDD':>8s} {'nullp95':>8s} {'pctile':>8s}  P3")
    for k in CELL_ORDER:
        x, nn = c[k], n.get(k)
        print(
            f"{k:5s} {x['exposure_gross']:7.1%} {x['excess_sharpe']:+8.3f} "
            f"{x['cagr']:8.2%} {dep[k]:8.2%} {x['max_drawdown']:+8.2%} "
            + (f"{nn['p95']:+8.3f} {nn['percentile_of_actual']:7.1f}th  "
               f"{'Y' if nn['clears_P3'] else 'N'}" if nn else f"{'—':>8s} {'—':>8s}   -")
        )
    b = payload["buy_and_hold"]
    print(f"{'B&H':5s} {100.0:6.1f}% {b['excess_sharpe']:+8.3f} {b['cagr']:8.2%} "
          f"{dep['buy_and_hold']:8.2%} {b['max_drawdown']:+8.2%}")
    print()
    for k in ("T1", "T2"):
        q = payload["p1"][k]
        print(f"P1 {k}: rho {q['rho']:+.4f}  bar {q['bar']:+.3f}  actual {q['actual']:+.3f}"
              f"  -> {'CLEARS' if q['clears_P1'] else 'FAILS'}")
    q = payload["p2"]
    print(f"P2    : T3 - S1 = {q['delta_t3_minus_s1']:+.3f}  "
          f"[p05 {q['bootstrap']['p05']:+.3f}, p95 {q['bootstrap']['p95']:+.3f}]  "
          f"{'CLEARS' if q['clears_P2'] else 'FAILS'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
