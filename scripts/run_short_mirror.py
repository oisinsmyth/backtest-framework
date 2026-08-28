"""D238 — the short-side mirror of the recovery rule.

    S1      position = +1  if  hist_L > 0  AND  md_L <= 0
    MIRROR  position = -1  if  hist_L < 0  AND  md_L >= 0

Three cells:

    M1  the literal mirror         hist_L < 0 AND md_L >= 0    29.5% exposure
    M2  strictly above the band    hist_L < 0 AND md_L >  0    25.0%
    M3  the combined book          S1 - M1, net in {-1, 0, +1}

THE PRIMARY HURDLE IS THE ROTATION NULL, NOT PROFITABILITY. A short book at
29.5% exposure carries roughly -14% of mechanical drift drag over this span, so
"does it lose money" is close to a foregone conclusion. "Does the timing carry
information once the drift is matched away" is not, and a matched-count rotation
null answers exactly that: a rotated short book has the same exposure and so the
same drag.

WHY THE SCORER IS WRITTEN FRESH RATHER THAN REUSED (D212 needs the reason named).
`run_macd_ladder.portfolio_log_returns` computes `position * log_return`. That is
EXACT at pos in {0, 1} and WRONG at pos = -1: a daily-rebalanced short earns
log(1 - r_simple) per bar, not -log(1 + r_simple). Measured on M1 the naive form
overstates the arm by +9.22 percentage points. `run_exposure_dial.score`,
`_excess_sharpe` and `rotation_nulls` all inherit the defect. The replacements
here are exactly backward-compatible on long-flat books, and that is pinned by
test rather than asserted.

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


L = _load("d217_ladder", "run_macd_ladder.py")
S = _load("d235_stops", "run_stops_targets.py")
J = _load("d229_jerk", "run_jerk_rung.py")

SUMMARY = REPO / "data" / "short_mirror_summary.json"
RESULTS = REPO / "SHORT_MIRROR_RESULTS.md"

PPY = L.PPY
SEED = 0
LAG = S.LAG
N_SIMS = 1000

RF_ANNUAL = J.RF_ANNUAL          # 0.04
RF_PER_BAR = J.RF_PER_BAR

# D238: a stated, deliberately conservative rate for a basket mixing liquid index
# ETFs with sector and commodity funds. NOT swept -- the breakeven rate is
# reported instead, so the sensitivity is visible without spending cells on it.
BORROW_ANNUAL = 0.010
BORROW_PER_BAR = math.log1p(BORROW_ANNUAL) / PPY

# Explicit page order. `json.dumps(sort_keys=True)` reorders a dict on the round
# trip, so a render that iterated it produced a DIFFERENT ROW ORDER under
# --report-only than on the live run. Same idempotency defect as D220, D222, D229.
CELL_ORDER = ("S1", "M1", "M2", "M3", "M4")

# M4 IS A DISCLOSED POST-HOC LOOK, NOT A REGISTERED CELL. D238 registered three.
# After M1 cleared W1, the reading turned on one question the registration did not
# ask: does `md_L >= 0` add anything the programme's known one-bit finding
# (`sign(hist)` alone) does not already supply? Computed on the analyst's
# initiative, following D234's precedent -- disclosed, and counted in the ledger.
POST_HOC = ("M4",)


# --------------------------------------------------------------------------
# The signed-book scorer -- the piece D238 asymmetry 3 is about
# --------------------------------------------------------------------------


def signed_log_returns(panel, position: np.ndarray, *, total_return: bool = False):
    """Equal-weighted portfolio log returns for a book that may be SHORT.

    The generalisation, and it is exactly backward-compatible:

        per_bar = log1p(pos * expm1(r))  +  log1p(-cost * |d pos|)

        pos = +1 -> log1p(expm1(r))       = r          the current code
        pos =  0 -> log1p(0)              = 0          the current code
        pos = -1 -> log1p(-expm1(r)) = log(2 - e^r)    the correct short

    Cost is charged on every unit of exposure CHANGED, so a flip from +1 to -1 is
    charged twice -- per side, D212, unchanged from the long-flat construction."""
    turnover = np.abs(np.diff(position, axis=1, prepend=0.0))
    charge = panel.cost_fraction[:, None] * turnover
    if np.any(charge >= 1.0):  # pragma: no cover - a cost of 100% is a config error
        raise ValueError("a per-bar charge reached 100% of notional")
    rets = panel.total_log_returns if total_return else panel.log_returns
    growth = 1.0 + position * np.expm1(rets)
    if np.any(growth <= 0.0):  # pragma: no cover - a short wiped out on one bar
        raise ValueError("a short position was wiped out on a single bar")
    return (np.log(growth) + np.log1p(-charge)).mean(axis=0)


def _legs(position: np.ndarray, start: int):
    """Long and short exposure fractions, which carry DIFFERENT financing."""
    live = position[:, start:]
    return float(np.maximum(live, 0.0).mean()), float(np.maximum(-live, 0.0).mean())


def excess_of(total: np.ndarray, position: np.ndarray, start: int) -> np.ndarray:
    """D238 asymmetry 4. rf is charged on the LONG fraction only -- a short book's
    collateral earns rf, which cancels against the benchmark -- and borrow is
    charged on the short fraction. Reduces exactly to `total - f*rf` when the book
    is long-flat, which is every book scored before this study."""
    live = position[:, start:]
    long_f = np.maximum(live, 0.0).mean(axis=0)
    short_f = np.maximum(-live, 0.0).mean(axis=0)
    return total - long_f * RF_PER_BAR - short_f * BORROW_PER_BAR


def score(panel, position: np.ndarray, start: int) -> dict:
    live = slice(start, None)
    total = signed_log_returns(panel, position, total_return=True)[live]
    price = signed_log_returns(panel, position)[live]
    ex = excess_of(total, position, start)
    sd = float(np.std(ex, ddof=1))
    long_f, short_f = _legs(position, start)

    active = (position != 0.0).astype(float)
    entries_per_sym = np.sum(np.diff(active, axis=1, prepend=0.0)[:, live] > 0.0, axis=1)

    # The borrow rate at which excess Sharpe crosses zero. Negative means the arm
    # loses even with FREE stock loan -- the charge is not what killed it.
    if short_f > 0.0:
        be = (float(np.mean(total)) - long_f * RF_PER_BAR) / short_f
        breakeven = float(np.expm1(be * PPY))
    else:
        breakeven = None

    return {
        "excess_sharpe": (float(np.mean(ex)) / sd * math.sqrt(PPY)) if sd > 0 else 0.0,
        "sharpe_rf0": L.sharpe_of(total),
        "total_return": L.total_return_of(total),
        "total_return_price": L.total_return_of(price),
        "max_drawdown": L.max_drawdown_of(total),
        "cagr": float(np.expm1(np.sum(total) / (len(total) / PPY))),
        "vol": float(np.std(total, ddof=1) * math.sqrt(PPY)),
        "exposure_long": long_f,
        "exposure_short": short_f,
        "exposure_gross": long_f + short_f,
        "entries": int(entries_per_sym.sum()),
        "min_entries_per_symbol": int(entries_per_sym.min()),
        "turnover_units": float(np.abs(np.diff(position, axis=1)).sum()),
        "breakeven_borrow_annual": breakeven,
        "clears_E": bool(entries_per_sym.sum() >= 100 and entries_per_sym.min() >= 30),
    }


def _excess_sharpe(panel, position: np.ndarray, start: int) -> float:
    """Lean scorer for the null's inner loop -- one portfolio pass, not the dict."""
    total = signed_log_returns(panel, position, total_return=True)[start:]
    ex = excess_of(total, position, start)
    sd = float(np.std(ex, ddof=1))
    return (float(np.mean(ex)) / sd * math.sqrt(PPY)) if sd > 0 else 0.0


def rotation_nulls(panel, positions: dict, start: int) -> dict:
    """Matched-count rotation null on ABSOLUTE excess Sharpe.

    Rotation is matched exactly on the things that would otherwise explain a short
    book's result -- every rotated book has the SAME exposure, the SAME turnover,
    the SAME holding-period distribution AND THEREFORE THE SAME DRIFT DRAG. It is
    the same book pointed at the wrong bars.

    That last property is why this hurdle carries D238's verdict rather than
    profitability: a short book loses to drift whether or not its timing is any
    good, and the rotated book loses exactly as much.

    ONE OFFSET VECTOR SHARED ACROSS CELLS, following D228. No parent is subtracted
    -- `run_exposure_dial.rotation_nulls` scores a delta against a long parent, and
    there is no such parent for a standalone short arm.

    THREE LEGS, NOT ONE, AND THE EXTRA TWO ARE A DIAGNOSTIC ON THE HURDLE ITSELF.
    Sharpe is `mean / sd`. A real short book concentrates its exposure after
    declines, when volatility is high; a rotated one spreads the same exposure
    across calm bars too. For a book whose mean is NEGATIVE, a larger sd makes the
    Sharpe LESS negative -- so an arm could beat this null on Sharpe purely by
    being exposed in noisy weather, with no skill at all.

    Money cannot be inflated that way. Recording the null distribution of TOTAL
    RETURN and of VOLATILITY beside it is what separates the two readings, and
    R7's corollary -- a hurdle everything clears is a broken hurdle, and all three
    cells cleared this one -- is why it is worth the second pass."""
    rng = np.random.default_rng(SEED)
    n, T = next(iter(positions.values())).shape
    span = T - start
    # Dict insertion order, NOT this module's CELL_ORDER. Filtering against
    # CELL_ORDER made the function silently return nothing for any caller whose
    # cells are named differently -- which D239 is. Callers pass an ordered dict,
    # and for D238's own call the two orders coincide exactly, so the artifact and
    # the page are unchanged (pinned by `test_the_page_round_trips_byte_for_byte`).
    names = list(positions)
    per = {k: np.empty(N_SIMS) for k in names}
    money = {k: np.empty(N_SIMS) for k in names}
    vol = {k: np.empty(N_SIMS) for k in names}
    for s in range(N_SIMS):
        offsets = rng.integers(1, span, size=n)
        for k in names:
            src = positions[k][:, start:]
            rot = np.zeros_like(positions[k])
            for i in range(n):
                rot[i, start:] = np.roll(src[i], int(offsets[i]))
            total = signed_log_returns(panel, rot, total_return=True)[start:]
            ex = excess_of(total, rot, start)
            sd = float(np.std(ex, ddof=1))
            per[k][s] = (float(np.mean(ex)) / sd * math.sqrt(PPY)) if sd > 0 else 0.0
            money[k][s] = L.total_return_of(total)
            vol[k][s] = float(np.std(total, ddof=1) * math.sqrt(PPY))
    return {"n_sims": N_SIMS, "draws": per, "money": money, "vol": vol}


# --------------------------------------------------------------------------


def build() -> dict:
    t0 = time.time()
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    md, hs, ok = S.base_masks(panel, cleaned, start)

    s1 = S.hold_book((hs > 0) & (md <= 0) & ok, start)
    m1 = -S.hold_book((hs < 0) & (md >= 0) & ok, start)
    m2 = -S.hold_book((hs < 0) & (md > 0) & ok, start)
    m3 = s1 + m1
    m4 = -S.hold_book((hs < 0) & ok, start)
    assert np.all(np.abs(m3) <= 1.0), "S1 and M1 fired together -- they must be disjoint"

    ones = np.ones_like(s1)
    ones[:, :start] = 0.0

    positions = {"S1": s1, "M1": m1, "M2": m2, "M3": m3, "M4": m4}
    cells = {k: score(panel, positions[k], start) for k in CELL_ORDER}
    bh = score(panel, ones, start)

    # Where md_L sits, and how much of each arm lives in the dead zone. Disclosed
    # in the pre-registration; recomputed here so the record and the artifact
    # cannot drift apart.
    live = np.zeros_like(ok)
    live[:, start:] = True
    live &= ok
    nlive = int(live.sum())
    held = {k: (positions[k][:, start:] != 0.0) for k in CELL_ORDER}
    dead = (md == 0)[:, start:]
    anatomy = {
        "live_cells": nlive,
        "share_above": float(((md > 0) & live).sum() / nlive),
        "share_inside": float(((md == 0) & live).sum() / nlive),
        "share_below": float(((md < 0) & live).sum() / nlive),
        "dead_zone_share_of_held": {
            k: float((held[k] & dead).sum() / max(held[k].sum(), 1)) for k in CELL_ORDER
        },
        "simultaneous_s1_m1": int(((s1 != 0) & (m1 != 0)).sum()),
    }

    # What the indicator's conditions are actually worth, per bar held, annualised.
    # THIS IS THE MEASUREMENT THAT DECIDES THE READING: a short needs bars that
    # FALL, and beating a rotation null only establishes bars that UNDERPERFORM.
    conditional = {}
    for label, mask in (
        ("hist>0 & md<=0  (S1)", (hs > 0) & (md <= 0) & ok),
        ("hist<0 & md>=0  (M1)", (hs < 0) & (md >= 0) & ok),
        ("hist<0 & md<0", (hs < 0) & (md < 0) & ok),
        ("hist<0 alone    (M4)", (hs < 0) & ok),
        ("all live bars", ok),
    ):
        sh = np.zeros_like(mask)
        sh[:, 1:] = mask[:, :-1]
        sh[:, :start] = False
        v = panel.total_log_returns[:, start:][sh[:, start:]]
        conditional[label] = {
            "bars": int(v.size),
            "annualised": float(np.expm1(float(v.mean()) * PPY)),
        }
    CONDITIONAL_ORDER = tuple(conditional)

    nl = rotation_nulls(panel, {k: positions[k] for k in ("M1", "M2", "M3", "M4")}, start)
    nulls = {}
    for k, draws in nl["draws"].items():
        actual = cells[k]["excess_sharpe"]
        m_draws, v_draws = nl["money"][k], nl["vol"][k]
        nulls[k] = {
            "p50": float(np.percentile(draws, 50)),
            "p95": float(np.percentile(draws, 95)),
            "sd": float(np.std(draws, ddof=1)),
            "percentile_of_actual": float((draws < actual).mean() * 100.0),
            "clears_W1": bool(actual > float(np.percentile(draws, 95))),
            "below_median": bool(actual < float(np.percentile(draws, 50))),
            # The diagnostic that separates skill from volatility timing.
            "money_p50": float(np.percentile(m_draws, 50)),
            "money_p95": float(np.percentile(m_draws, 95)),
            "money_percentile_of_actual": float(
                (m_draws < cells[k]["total_return"]).mean() * 100.0
            ),
            "vol_p50": float(np.percentile(v_draws, 50)),
            "vol_ratio_actual_over_null": float(cells[k]["vol"] / np.percentile(v_draws, 50)),
        }

    # W3 -- the paired bootstrap on M3 minus S1, both arms on identical dates.
    r_s1 = excess_of(signed_log_returns(panel, s1, total_return=True)[start:], s1, start)
    r_m1 = excess_of(signed_log_returns(panel, m1, total_return=True)[start:], m1, start)
    r_m3 = excess_of(signed_log_returns(panel, m3, total_return=True)[start:], m3, start)
    boot = J.paired_block_bootstrap(r_m3, r_s1)

    # sqrt(f) -- the exposure the mirror gets for free, and what it did with it.
    f_s1 = cells["S1"]["exposure_gross"]
    root_f = {
        k: math.sqrt(cells[k]["exposure_gross"] / f_s1) for k in ("M1", "M2", "M3", "M4")
    }

    return {
        "produced": "D238",
        "conditional_returns": conditional,
        "conditional_order": list(CONDITIONAL_ORDER),
        "post_hoc_cells": list(POST_HOC),
        "stage": "screen (mined 57) -- the holdout and forward window are untouched",
        "seed": SEED,
        "n_sims": N_SIMS,
        "rf_annual": RF_ANNUAL,
        "borrow_annual": BORROW_ANNUAL,
        "n_symbols": len(panel.symbols),
        "live_bars": len(panel.dates) - start,
        "first_live_date": panel.dates[start],
        "last_date": panel.dates[-1],
        "anatomy": anatomy,
        "cells": cells,
        "buy_and_hold": bh,
        "nulls": nulls,
        "sqrt_f_vs_s1": root_f,
        "correlation_s1_m1": float(np.corrcoef(r_s1, r_m1)[0, 1]),
        "w3": {
            "delta_m3_minus_s1": cells["M3"]["excess_sharpe"] - cells["S1"]["excess_sharpe"],
            "bootstrap": boot,
            "clears_W3": bool(
                cells["M3"]["excess_sharpe"] > cells["S1"]["excess_sharpe"]
                and boot["p05"] > 0.0
            ),
        },
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    a, c, n = p["anatomy"], p["cells"], p["nulls"]
    o = ["# D238 — the short-side mirror of the recovery rule\n"]
    o.append(f"**STAGE 1 — A SCREEN, NOT A VERDICT.** {p['stage']}\n")
    o.append(
        f"*seed {p['seed']}, {p['n_sims']:,} rotations, {p['elapsed_seconds']}s. "
        f"{p['n_symbols']} ETFs x {p['live_bars']:,} live bars, "
        f"{p['first_live_date'][:10]} .. {p['last_date'][:10]}. "
        f"rf {p['rf_annual']:.1%}/yr on long notional, borrow "
        f"{p['borrow_annual']:.1%}/yr on short.*\n"
    )

    o.append("## The channel is not symmetric\n")
    o.append("| where `md_L` sits | share of live bars |")
    o.append("|---|---:|")
    o.append(f"| **above** the channel — `md_L > 0` | **{a['share_above']:.2%}** |")
    o.append(f"| **inside** — `md_L = 0`, the dead zone | {a['share_inside']:.2%} |")
    o.append(f"| **below** the channel — `md_L < 0` | {a['share_below']:.2%} |")
    o.append("")
    o.append(
        f"S1 and M1 fire simultaneously on **{a['simultaneous_s1_m1']}** cells — they are "
        "disjoint, so M3 needs no weighting choice.\n"
    )

    o.append("## The four books\n")
    o.append(
        "| | rule | long | short | excess Sharpe | CAGR | vol | max DD | total return | E |"
    )
    o.append("|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|")
    rules = {
        "S1": "`hist>0 & md<=0` (+1)",
        "M1": "`hist<0 & md>=0` (−1)",
        "M2": "`hist<0 & md>0` (−1)",
        "M3": "S1 − M1",
        "M4": "`hist<0` alone (−1) *post-hoc*",
    }
    for k in CELL_ORDER:
        s = c[k]
        o.append(
            f"| **{k}** | {rules[k]} | {s['exposure_long']:.1%} | {s['exposure_short']:.1%} | "
            f"**{s['excess_sharpe']:+.3f}** | {s['cagr'] * 100:.2f}% | {s['vol'] * 100:.1f}% | "
            f"{s['max_drawdown'] * 100:+.2f}% | {s['total_return'] * 100:+.2f}% | "
            f"{'✓' if s['clears_E'] else '✗'} |"
        )
    b = p["buy_and_hold"]
    o.append(
        f"| B&H | always long | 100.0% | 0.0% | {b['excess_sharpe']:+.3f} | "
        f"{b['cagr'] * 100:.2f}% | {b['vol'] * 100:.1f}% | {b['max_drawdown'] * 100:+.2f}% | "
        f"{b['total_return'] * 100:+.2f}% | — |"
    )
    o.append("")

    o.append("## W1 — the rotation null, which carries the verdict\n")
    o.append(
        "*Same exposure, same turnover, same holding periods, wrong bars — **and therefore "
        "the same drift drag.** That is why this and not profitability is the primary.*\n"
    )
    o.append("| | actual | null p50 | null p95 | null sd | **percentile** | W1 |")
    o.append("|---|---:|---:|---:|---:|---:|:--:|")
    for k in ("M1", "M2", "M3", "M4"):
        o.append(
            f"| **{k}** | **{c[k]['excess_sharpe']:+.3f}** | {n[k]['p50']:+.3f} | "
            f"{n[k]['p95']:+.3f} | {n[k]['sd']:.3f} | **{n[k]['percentile_of_actual']:.1f}th** | "
            f"{'✓' if n[k]['clears_W1'] else '✗'} |"
        )
    o.append("")
    o.append(
        "**Every cell clears, which under R7's corollary is a tell rather than a triumph** — "
        "so the same null was re-run on money and on volatility, because Sharpe is `mean/sd` "
        "and a *negative*-mean book can beat this hurdle purely by being exposed in noisy "
        "weather. Money cannot be inflated that way.\n"
    )
    o.append("| | money | null p50 | **percentile** | vol | null vol p50 | **ratio** |")
    o.append("|---|---:|---:|---:|---:|---:|---:|")
    for k in ("M1", "M2", "M3", "M4"):
        o.append(
            f"| **{k}** | **{c[k]['total_return'] * 100:+.2f}%** | "
            f"{n[k]['money_p50'] * 100:+.2f}% | "
            f"**{n[k]['money_percentile_of_actual']:.1f}th** | {c[k]['vol'] * 100:.2f}% | "
            f"{n[k]['vol_p50'] * 100:.2f}% | {n[k]['vol_ratio_actual_over_null']:.3f}x |"
        )
    o.append("")

    o.append("## What a held bar is actually worth\n")
    o.append(
        "*Mean total return of the bars each condition selects, annualised. **This is the "
        "measurement that decides the reading**, because a short needs bars that FALL and a "
        "rotation null can only establish bars that UNDERPERFORM.*\n"
    )
    o.append("| condition | bars held | annualised return of those bars |")
    o.append("|---|---:|---:|")
    for label in p["conditional_order"]:
        d = p["conditional_returns"][label]
        o.append(f"| `{label}` | {d['bars']:,} | **{d['annualised'] * 100:+.2f}%** |")
    o.append("")

    o.append("## W2 — standalone viability, and the breakeven borrow rate\n")
    o.append("| | excess Sharpe | W2 | √f vs S1 | breakeven borrow |")
    o.append("|---|---:|:--:|---:|---:|")
    for k in ("M1", "M2", "M3", "M4"):
        be = c[k]["breakeven_borrow_annual"]
        o.append(
            f"| **{k}** | {c[k]['excess_sharpe']:+.3f} | "
            f"{'✓' if c[k]['excess_sharpe'] > 0 else '✗'} | "
            f"{p['sqrt_f_vs_s1'][k]:.3f}x | "
            f"{('%+.2f%%' % (be * 100)) if be is not None else '—'} |"
        )
    o.append("")
    o.append(
        "*A **negative** breakeven means the arm loses with free stock loan — the borrow "
        "charge is not what killed it.*\n"
    )

    w3 = p["w3"]
    o.append("## W3 — does the combined book beat S1 alone?\n")
    o.append(
        f"| | excess Sharpe |\n|---|---:|\n"
        f"| S1 alone | {c['S1']['excess_sharpe']:+.3f} |\n"
        f"| **M3 combined** | **{c['M3']['excess_sharpe']:+.3f}** |\n"
        f"| **delta** | **{w3['delta_m3_minus_s1']:+.3f}** |\n"
        f"| paired bootstrap p05 | {w3['bootstrap']['p05']:+.3f} |\n"
        f"| paired bootstrap p95 | {w3['bootstrap']['p95']:+.3f} |\n"
        f"| **W3** | **{'✓ CLEARS' if w3['clears_W3'] else '✗ FAILS'}** |\n"
    )
    o.append(
        f"**Correlation of the S1 and M1 daily excess returns: "
        f"`{p['correlation_s1_m1']:+.4f}`.**\n"
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

    c, n = payload["cells"], payload["nulls"]
    print()
    print(f"{'cell':5s} {'long':>7s} {'short':>7s} {'exSh':>8s} {'CAGR':>8s} "
          f"{'maxDD':>8s} {'nullp50':>8s} {'nullp95':>8s} {'pctile':>8s}  W1")
    for k in CELL_ORDER:
        s = c[k]
        nn = n.get(k)
        print(
            f"{k:5s} {s['exposure_long']:7.1%} {s['exposure_short']:7.1%} "
            f"{s['excess_sharpe']:+8.3f} {s['cagr']:8.2%} {s['max_drawdown']:+8.2%} "
            + (f"{nn['p50']:+8.3f} {nn['p95']:+8.3f} {nn['percentile_of_actual']:7.1f}th  "
               f"{'Y' if nn['clears_W1'] else 'N'}" if nn else f"{'—':>8s} {'—':>8s} {'—':>8s}   -")
        )
    print()
    print(f"corr(S1, M1) = {payload['correlation_s1_m1']:+.4f}")
    w3 = payload["w3"]
    print(f"W3  M3 - S1 = {w3['delta_m3_minus_s1']:+.3f}  "
          f"[p05 {w3['bootstrap']['p05']:+.3f}, p95 {w3['bootstrap']['p95']:+.3f}]  "
          f"{'CLEARS' if w3['clears_W3'] else 'FAILS'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
