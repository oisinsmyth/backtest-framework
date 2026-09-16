"""D248 — the strength-filtered intraday short.

    z      = |hist_L| / trailing_sd(hist_L, 1638)
    SHORT  when  hist_L < 0  AND  md_L >= 0  AND  z >= c[i,t]
    c[i,t] = the (1 - TARGET) quantile of that symbol's own z over the prior 1638 bars
    FLAT   at the first bar of every session, always

Three cells at exposure targets 5%, 10%, 15%. The threshold SELF-CALIBRATES
(D231) so exposure is a control rather than an outcome, which is what makes the
rule portable to a holdout without re-fitting.

THE THESIS: D247's intraday short failed on turnover (334 units/yr, breakeven
0.13bp against 1.6 charged) AND its edge concentrated monotonically in signal
strength (+413.69% at the weakest quintile through -71.07% at the strongest).
The weak bars ARE the churning bars -- hist_L near zero sits on its own boundary
and flips. One filter attacks both failures.

A TIME SPLIT carries the verdict: screen to 2022-06-30, validate after. D243
established time is the axis these rules actually fail on. The signal is computed
on the FULL series and the split is applied to SCORED RETURNS ONLY, so the
validation half carries the warm-up and quantile history it would have had.

A7 IS THE MOST INFORMATIVE HURDLE: the quintile monotonicity in z must survive on
the validation half. A real effect decays smoothly on data it was not found on; a
fitted one scrambles.

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


D = _load("d247_intraday", "run_intraday_shorts.py")
F = _load("d228_filter", "run_filter_search.py")
X, L, S, J = D.X, D.L, D.S, D.J

SUMMARY = REPO / "data" / "intraday_filtered_summary.json"
RESULTS = REPO / "docs" / "results" / "INTRADAY_FILTERED_RESULTS.md"

SEED, N_SIMS = X.SEED, X.N_SIMS
RF_ANNUAL = X.RF_ANNUAL
N_BOOT, BLOCK = J.N_BOOT, J.BLOCK

NORM_WINDOW = 1638            # 63 sessions ~ one quarter. Declared, not swept.
TARGETS = (0.05, 0.10, 0.15)
SPLIT = "2022-06-30"
EXPOSURE_TOL = 0.03           # D231's tolerance
CHARGED_BPS = 1.6
CELL_ORDER = tuple(f"T{int(t * 100):02d}" for t in TARGETS)


def z_scores(hs):
    """|hist_L| normalised by its own trailing dispersion, so `z = 1.5` means the
    same thing on AGG and GDXJ. D231's construction, `trailing_std` reused."""
    sd = F.trailing_std(np.nan_to_num(hs, nan=0.0), NORM_WINDOW)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(sd > 0.0, np.abs(hs) / sd, np.nan)


def session_thresholds(z, sig, first, target, start):
    """AMENDMENT 1, made at build time and declared. D248 specifies the quantile
    over the prior NORM_WINDOW bars but not how often it is recomputed. A per-bar
    recompute is 3.2M quantiles over 1,638 elements; this updates ONCE PER SESSION
    OPEN and holds the level through the session. Cheaper by 26x AND more realistic
    -- a trader sets the day's threshold at the open. STRICTLY TRAILING: the window
    ends at t-1, so bar t is never in its own threshold.

    AMENDMENT 2, forced by an assertion. The first version took the (1-target)
    quantile of z over ALL bars and then intersected with the direction condition,
    which is true on only ~27% of bars -- so the 5% cell landed at 0.9% EXPOSURE
    and D248's claim that "exposure lands near the target by construction" was
    simply false.

    The fix is to calibrate on the population the rule actually selects from:
    score bars that fail the direction condition at a SENTINEL below any real z,
    then take the (1-target) quantile over the whole window. The top target-share
    of that window is then exactly the signal-on bars with the highest z, so
    exposure lands on target by construction as claimed."""
    n, T = z.shape
    thr = np.full((n, T), np.nan)
    q = 100.0 * (1.0 - target)
    SENTINEL = -1.0                       # z is a ratio of magnitudes, so z >= 0
    w_all = np.where(sig & ~np.isnan(z), z, SENTINEL)
    # AMENDMENT 3. `z` itself needs NORM_WINDOW bars of trailing sd, so it is NaN
    # until bar NORM_WINDOW -- and the threshold at bar t reads z over
    # [t-NORM_WINDOW, t), which therefore needs t >= 2 * NORM_WINDOW. The first
    # attempt started one warm-up too early, every early window was all-sentinel,
    # and the guard below caught it as "target exceeds the signal-on rate".
    opens = np.where(first)[0]
    for t in opens:
        if t < start:
            continue
        w = w_all[:, t - NORM_WINDOW:t]
        thr[:, t] = np.percentile(w, q, axis=1)
    # AMENDMENT 4. In some symbol-quarters the direction condition fires on FEWER
    # bars than the target asks for, and the quantile lands on the sentinel. That is
    # a boundary condition, not an error: the honest behaviour is to take every
    # signal-on bar available. Clipping to 0 does exactly that, since z >= 0.
    #
    # It means a cell can come in UNDER its target, so the exposure assertion is
    # one-sided from here -- never above target, possibly below, and the achieved
    # figure is reported rather than assumed.
    capped = float((thr[:, start:] <= SENTINEL).mean())
    thr = np.maximum(thr, 0.0)
    # hold the level through the session
    idx = np.where(~np.isnan(thr[0]))[0]
    for a, b in zip(idx, list(idx[1:]) + [T]):
        thr[:, a:b] = thr[:, a][:, None]
    return thr, capped


def build_book(hs, md, ok, z, thr, first, start):
    sig = (hs < 0) & (md >= 0) & ok & ~np.isnan(z) & ~np.isnan(thr) & (z >= thr)
    book = -D.flatten_overnight(S.hold_book(sig, start), first)
    return book


def _sharpe(ex, ppy):
    sd = float(np.std(ex, ddof=1))
    return (float(np.mean(ex)) / sd * math.sqrt(ppy)) if sd > 0 else 0.0


def score_half(panel, pos, start, first, gap, ppy, mask):
    """Score one half. The MASK selects scored bars; the position matrix is the
    full-span one, so the half carries the warm-up it would have had."""
    total = X.signed_log_returns(panel, pos, total_return=True)[start:]
    ex, borrow = D.excess_intraday(total, pos, start, first, gap, ppy)
    live = pos[:, start:][:, mask]
    turn = float(np.abs(np.diff(pos, axis=1, prepend=0.0))[:, start:][:, mask].sum())
    yrs = mask.sum() / ppy
    paid = float((panel.cost_fraction[:, None]
                  * np.abs(np.diff(pos, axis=1, prepend=0.0)))[:, start:][:, mask].sum()
                 / len(panel.symbols))
    per_unit = turn / len(panel.symbols)
    gross = float(np.sum(ex[mask])) + paid
    return {
        "excess_sharpe": _sharpe(ex[mask], ppy),
        "cagr": float(np.expm1(np.sum(total[mask]) / yrs)),
        "exposure_short": float(np.maximum(-live, 0.0).mean()),
        "max_drawdown": L.max_drawdown_of(total[mask]),
        "turnover_per_year": per_unit / yrs,
        "borrow_paid_annualised": float(np.expm1(borrow / yrs)) if borrow else 0.0,
        "breakeven_bps": (1e4 * (1.0 - math.exp(-gross / per_unit))) if per_unit > 0 else None,
        "bars": int(mask.sum()), "years": yrs,
    }


def rotation_nulls(panel, books, start, first, gap, ppy, mask):
    """Matched-count rotation, ONE SHARED OFFSET VECTOR across cells (D228), scored
    on the same half as the cell. Uses D247's hoisted scorer."""
    rng = np.random.default_rng(SEED)
    n, T = panel.closes.shape
    span = T - start
    names = list(books)
    exp_rets = np.expm1(panel.total_log_returns)
    cost = panel.cost_fraction[:, None]

    def fast_total(pos):
        charge = cost * np.abs(np.diff(pos, axis=1, prepend=0.0))
        return (np.log1p(pos * exp_rets) + np.log1p(-charge)).mean(axis=0)[start:]

    probe = next(iter(books.values()))
    assert np.allclose(fast_total(probe),
                       X.signed_log_returns(panel, probe, total_return=True)[start:],
                       rtol=0, atol=1e-12), "the fast scorer diverged"

    per = {k: np.empty(N_SIMS) for k in names}
    best = np.empty(N_SIMS)
    rot = np.zeros((n, T))
    for s in range(N_SIMS):
        off = rng.integers(1, span, size=n)
        vals = []
        for k in names:
            src = books[k][:, start:]
            for i in range(n):
                rot[i, start:] = np.roll(src[i], int(off[i]))
            ex, _ = D.excess_intraday(fast_total(rot), rot, start, first, gap, ppy)
            v = _sharpe(ex[mask], ppy)
            per[k][s] = v
            vals.append(v)
        best[s] = max(vals)
    return per, float(np.percentile(best, 95))


def quintiles(rets, sig_intraday, z, start, mask, ppy):
    """A7. Bucket ALL signal-on intraday bars by z and report the held-bar return.
    Unfiltered by any cell -- this tests the RELATIONSHIP, not a book.

    CORRECTION. The first version passed z UNLAGGED while the signal was lagged,
    and reported a monotone +465-point spread. That was LOOK-AHEAD: z[t] is
    |hist_L[t]| / sd, and hist_L[t] is computed from bar t's CLOSE, so a large
    |hist_L| with hist_L < 0 means the bar ALREADY FELL. Selecting bar t on z[t]
    and then measuring bar t's return measures the fall that was conditioned on.

    The RULE never had this problem -- `hold_book` shifts by lag = 1, so it uses
    z[t-1]. Passing the lagged z here is what makes A7 test the same relationship
    the rule can actually trade. Both are computed so the artifact records the size
    of the artifact."""
    m = sig_intraday[:, start:][:, mask]
    zz = z[:, start:][:, mask]
    rr = rets[:, start:][:, mask]
    sel = m & ~np.isnan(zz)
    if sel.sum() < 1000:
        return None
    qs = np.nanpercentile(zz[sel], [20, 40, 60, 80])
    out = []
    lo = [-np.inf] + list(qs)
    hi = list(qs) + [np.inf]
    for a, b in zip(lo, hi):
        s2 = sel & (zz > a) & (zz <= b)
        v = rr[s2]
        out.append({"bars": int(v.size),
                    "annualised": float(np.expm1(v.mean() * ppy)) if v.size else None})
    return out


def monotone(q):
    """Strictly decreasing across the five buckets?"""
    a = [x["annualised"] for x in q]
    return all(a[i] > a[i + 1] for i in range(4))


def build() -> dict:
    t0 = time.time()
    L.FIXTURE, L.EVENTS = D.FIXTURE, D.EVENTS
    panel, cleaned = L.load_panel()
    first, gap = D.session_structure(panel.dates)
    ppy = (panel.closes.shape[1] / int(first.sum())) * 252.0
    base = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    start = max(base, 2 * NORM_WINDOW)   # see AMENDMENT 3 in session_thresholds
    md, hs, ok = S.base_masks(panel, cleaned, base)
    rets = panel.total_log_returns

    # D247's unfiltered reference must reproduce, or the pipeline moved underneath us
    ref_book = -D.flatten_overnight(S.hold_book((hs < 0) & (md >= 0) & ok, base), first)
    ref = D.score(panel, ref_book, base, first, gap, ppy)
    assert abs(ref["excess_sharpe"] + 1.550) < 5e-3, f"D247 reference moved: {ref}"

    z = z_scores(hs)
    dates = np.array(panel.dates[start:])
    halves = {"SCREEN": dates <= SPLIT, "VALIDATE": dates > SPLIT, "FULL": np.ones(len(dates), bool)}
    assert halves["SCREEN"].sum() > 5000 and halves["VALIDATE"].sum() > 5000, "a half is too short"

    direction = (hs < 0) & (md >= 0) & ok
    books, cells, thr_used = {}, {}, {}
    for tgt, name in zip(TARGETS, CELL_ORDER):
        thr, capped = session_thresholds(z, direction, first, tgt, start)
        b = build_book(hs, md, ok, z, thr, first, start)
        books[name] = b
        thr_used[name] = {"target": tgt, "share_capped": capped}
        assert not b[:, first].any(), f"{name} is not flat at every session open"
        cells[name] = {h: score_half(panel, b, start, first, gap, ppy, m)
                       for h, m in halves.items()}
        for h in ("SCREEN", "VALIDATE"):
            assert cells[name][h]["borrow_paid_annualised"] == 0.0, f"{name}/{h} paid borrow"
            got = cells[name][h]["exposure_short"]
            assert abs(got - tgt) <= EXPOSURE_TOL, \
                f"{name}/{h}: exposure {got:.1%} misses target {tgt:.0%} by more than {EXPOSURE_TOL:.0%}"
        print(f"{name}: exposure {cells[name]['FULL']['exposure_short']:.1%}, "
              f"turnover {cells[name]['FULL']['turnover_per_year']:.0f}, "
              f"SCREEN {cells[name]['SCREEN']['excess_sharpe']:+.3f}, "
              f"VALIDATE {cells[name]['VALIDATE']['excess_sharpe']:+.3f}", flush=True)

    nulls, bestof = {}, {}
    for h in ("SCREEN", "VALIDATE"):
        per, bp95 = rotation_nulls(panel, books, start, first, gap, ppy, halves[h])
        bestof[h] = bp95
        nulls[h] = {}
        for k in CELL_ORDER:
            a = cells[k][h]["excess_sharpe"]
            nulls[h][k] = {"p95": float(np.percentile(per[k], 95)),
                           "percentile_of_actual": float((per[k] < a).mean() * 100.0),
                           "clears": bool(a > float(np.percentile(per[k], 95)))}
        print(f"nulls {h}: best-of-3 p95 {bp95:+.3f}", flush=True)

    sig_intra = ((hs < 0) & (md >= 0) & ok)
    sig_intra = np.roll(sig_intra, 1, axis=1)
    sig_intra[:, first] = False
    z_lag = np.full_like(z, np.nan)
    z_lag[:, 1:] = z[:, :-1]          # what the rule can actually see
    quint = {h: quintiles(rets, sig_intra, z_lag, start, halves[h], ppy)
             for h in ("SCREEN", "VALIDATE")}
    quint_lookahead = {h: quintiles(rets, sig_intra, z, start, halves[h], ppy)
                       for h in ("SCREEN", "VALIDATE")}

    verdict = {}
    for k in CELL_ORDER:
        sc, va = cells[k]["SCREEN"], cells[k]["VALIDATE"]
        verdict[k] = {
            "clears_A1": bool(sc["excess_sharpe"] > 0),
            "clears_A2": nulls["SCREEN"][k]["clears"],
            "clears_A3": bool(sc["excess_sharpe"] > bestof["SCREEN"]),
            "clears_A4": bool((sc["breakeven_bps"] or -9e9) > CHARGED_BPS),
            "clears_A5": bool(va["excess_sharpe"] > 0 and nulls["VALIDATE"][k]["clears"]),
            "clears_A6": bool((va["breakeven_bps"] or -9e9) > CHARGED_BPS),
        }
        verdict[k]["screen_ok"] = all(verdict[k][x] for x in
                                      ("clears_A1", "clears_A2", "clears_A3", "clears_A4"))
        verdict[k]["validate_ok"] = verdict[k]["clears_A5"] and verdict[k]["clears_A6"]

    a7 = {h: (monotone(quint[h]) if quint[h] else None) for h in quint}
    a7_lookahead = {h: (monotone(quint_lookahead[h]) if quint_lookahead[h] else None)
                    for h in quint_lookahead}
    any_pass = any(v["validate_ok"] for v in verdict.values())
    reading = (
        "A CELL SURVIVED THE TIME SPLIT. Not promoted -- it needs an instrument holdout at 15 "
        "minutes, which requires a fetch that has not been made."
        if any_pass else
        "NO CELL SURVIVES. The strength-filtered intraday short is CLOSED per D248's stop: no "
        "fourth target, no md_L variant, no re-cut window, no 30-minute bars.")

    return {
        "produced": "D248", "stage": "screen + time-split validation",
        "seed": SEED, "n_sims": N_SIMS, "ppy": ppy, "norm_window": NORM_WINDOW,
        "split": SPLIT, "charged_bps": CHARGED_BPS, "targets": list(TARGETS),
        "warmup_bars": start, "d247_reference": ref,
        "half_bars": {h: int(m.sum()) for h, m in halves.items()},
        "cells": cells, "nulls": nulls, "best_of_p95": bestof, "calibration": thr_used,
        "verdict": verdict, "quintiles": quint, "a7_monotone": a7,
        "quintiles_lookahead": quint_lookahead, "a7_monotone_lookahead": a7_lookahead,
        "reading": reading, "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    c, n, v, q = p["cells"], p["nulls"], p["verdict"], p["quintiles"]
    o = ["# D248 — the strength-filtered intraday short\n"]
    o.append(f"*seed {p['seed']}, {p['n_sims']:,} rotations, {p['elapsed_seconds']}s. "
             f"PPY {p['ppy']:.0f}, normalisation window {p['norm_window']:,} bars "
             f"(63 sessions). Split at **{p['split']}** — "
             f"SCREEN {p['half_bars']['SCREEN']:,} bars, "
             f"VALIDATE {p['half_bars']['VALIDATE']:,}.*\n")
    o.append(f"*D247's unfiltered reference reproduced at "
             f"**{p['d247_reference']['excess_sharpe']:+.3f}**.*\n")
    o.append("## The three cells\n")
    o.append("| | exposure | turnover/yr | SCREEN Sharpe | null pctile | breakeven | "
             "VALIDATE Sharpe | null pctile | breakeven |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k in CELL_ORDER:
        s, va = c[k]["SCREEN"], c[k]["VALIDATE"]
        o.append(
            f"| **{k}** | {c[k]['FULL']['exposure_short']:.1%} | "
            f"{c[k]['FULL']['turnover_per_year']:.0f} | "
            f"**{s['excess_sharpe']:+.3f}** | {n['SCREEN'][k]['percentile_of_actual']:.1f}th | "
            f"{s['breakeven_bps']:.2f} bp | "
            f"**{va['excess_sharpe']:+.3f}** | {n['VALIDATE'][k]['percentile_of_actual']:.1f}th | "
            f"{va['breakeven_bps']:.2f} bp |")
    o.append(f"\n*D247 unfiltered, for reference: 25.9% exposure, 334 turnover, "
             f"−1.550 Sharpe, 0.13 bp breakeven. Charged cost ~{p['charged_bps']} bp/side.*\n")
    o.append("## Hurdles\n")
    o.append("| | A1 >0 | A2 null | A3 best-of-3 | A4 cost | **SCREEN** | A5 | A6 | "
             "**VALIDATE** |")
    o.append("|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|")
    for k in CELL_ORDER:
        d = v[k]
        o.append("| **" + k + "** | " + " | ".join(
            "✓" if d[x] else "✗" for x in ("clears_A1", "clears_A2", "clears_A3", "clears_A4"))
            + f" | **{'✓' if d['screen_ok'] else '✗'}** | "
            + " | ".join("✓" if d[x] else "✗" for x in ("clears_A5", "clears_A6"))
            + f" | **{'✓' if d['validate_ok'] else '✗'}** |")
    o.append(f"\n*Best-of-three floor: SCREEN {p['best_of_p95']['SCREEN']:+.3f}, "
             f"VALIDATE {p['best_of_p95']['VALIDATE']:+.3f}.*\n")
    o.append("## A7 — does the strength ordering survive out of sample?\n")
    o.append("*The most informative hurdle. All signal-on intraday bars, bucketed by `z`, "
             "unfiltered by any cell — this tests the RELATIONSHIP, not a book.*\n")
    o.append("| quintile | SCREEN | VALIDATE |")
    o.append("|---|---:|---:|")
    for i in range(5):
        a = q["SCREEN"][i]["annualised"] if q["SCREEN"] else None
        b = q["VALIDATE"][i]["annualised"] if q["VALIDATE"] else None
        o.append(f"| Q{i + 1}{' — weakest' if i == 0 else ' — strongest' if i == 4 else ''} | "
                 f"{a * 100:+.2f}% | {b * 100:+.2f}% |")
    o.append(f"\n**Strictly monotone: SCREEN {'✓' if p['a7_monotone']['SCREEN'] else '✗'}, "
             f"VALIDATE {'✓' if p['a7_monotone']['VALIDATE'] else '✗'}.**\n")
    o.append("## The reading\n")
    o.append(f"> **{p['reading']}**\n")
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
    c, n, v = payload["cells"], payload["nulls"], payload["verdict"]
    print()
    print(f"{'cell':6s} {'expo':>7s} {'turn':>6s} | {'SCREEN':>8s} {'pct':>7s} {'be':>7s} "
          f"{'ok':>3s} | {'VALID':>8s} {'pct':>7s} {'be':>7s} {'ok':>3s}")
    for k in CELL_ORDER:
        s, va, d = c[k]["SCREEN"], c[k]["VALIDATE"], v[k]
        print(f"{k:6s} {c[k]['FULL']['exposure_short']:7.1%} "
              f"{c[k]['FULL']['turnover_per_year']:6.0f} | "
              f"{s['excess_sharpe']:+8.3f} {n['SCREEN'][k]['percentile_of_actual']:6.1f}th "
              f"{s['breakeven_bps']:7.2f} {'Y' if d['screen_ok'] else 'N':>3s} | "
              f"{va['excess_sharpe']:+8.3f} {n['VALIDATE'][k]['percentile_of_actual']:6.1f}th "
              f"{va['breakeven_bps']:7.2f} {'Y' if d['validate_ok'] else 'N':>3s}")
    print(f"\nA7 monotone: SCREEN {payload['a7_monotone']['SCREEN']}, "
          f"VALIDATE {payload['a7_monotone']['VALIDATE']}")
    for h in ("SCREEN", "VALIDATE"):
        qs = payload["quintiles"][h]
        print(f"  {h:9s} " + "  ".join(f"{x['annualised']:+8.2%}" for x in qs))
    print()
    print(payload["reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
