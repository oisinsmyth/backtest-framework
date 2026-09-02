"""D288 gates 0 and A -- independence, then the best-of-31 floor.

    uv run python scripts/d288_gates.py --gate0
    uv run python scripts/d288_gates.py --gateA [--sims 200]

SEPARATE FROM THE SCREEN ON PURPOSE. `run_mine_neutral.py` produces the numbers
and applies no gate; this file applies the gates and produces no number. Keeping
them apart is what stops a floor from being quietly recomputed once the observed
values are visible -- which is the single easiest way to turn a mine into a
result, and it never looks like cheating from the inside.

Both gates are pre-registered at `fa098a2`, which was committed before either
this file or the screen existed.

--------------------------------------------------------------------------
GATE 0 -- ARE THE 31 ACTUALLY 31?

D268 measured NINE PRICE SCORES COLLAPSING TO 2.87 EFFECTIVE INPUTS. If D288's
31 carry fewer than `MIN_EFFECTIVE_FAMILIES`, a best-of-31 floor is DISHONEST in
the direction that flatters the study -- it prices 31 independent looks that were
not taken, so it sets the bar too HIGH and a genuine effect could be buried by
its own multiplicity correction. Either way the count has to be restated before
gate A means anything.

RANKED WITHIN BAR, NOT WITHIN SYMBOL, AND THAT IS A DEPARTURE FROM D268.
`d268_score_independence` ranks each score within a SYMBOL and pools, which is
correct there because the consensus rule it gated ranks per name. D288's book is
purely CROSS-SECTIONAL: `legs` sorts the live names against each other inside one
bar and takes the extremes. Two scores can agree strongly along a symbol's own
history and disagree completely about who is extreme today. D280 part G2 already
made this mistake once -- it reported a POOLED correlation for a book that only
ever ranks cross-sectionally, and those numbers were withdrawn.

--------------------------------------------------------------------------
GATE A -- THE BEST-OF-31 FLOOR

D228's construction, adapted to this statistic. Per draw ONE SHARED OFFSET VECTOR
rotates every candidate, so the floor prices the fact that 31 CORRELATED looks
are fewer than 31 independent ones. Drawing a separate offset per candidate would
make them artificially independent and set the bar far too high.

ROTATION IS WITHIN EACH SYMBOL'S OWN LIVE BARS. Rolling the raw grid row would
move NaN regions around and change coverage, so the null would differ from the
observed run in sample as well as in alignment. Rotating the values AT the live
positions leaves every symbol's coverage, distribution and autocorrelation
exactly as they are, and destroys only the thing being tested: alignment with
what happened next.

THE FLOOR PRICES THE WHOLE SEARCH -- max over 31 candidates x 3 N x 12 horizons,
because that is the grid the headline is read off. D277's best cell was +0.392
against a best-of-300 floor of +0.605: it did not fail for want of ideas, it
failed because searching 300 things raises the bar you have to clear.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


M = _load("run_mine_neutral", "run_mine_neutral.py")
D268 = _load("d268", "d268_score_independence.py")
FN = M.FN

OUT0 = REPO / "data" / "d288_gate0_independence.json"
OUTA = REPO / "data" / "d288_gateA_floor.json"
MIN_EFFECTIVE_FAMILIES = 3.0        # D268's bar, unchanged
BETWEEN_AXIS_LIMIT = 0.70           # D268's limit, unchanged
SEED = 20260902
N_SIMS = 200


def _panel():
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    g = M.P1.build_grids(panel, cleaned)
    scores, warm, _ = M.build_scores(panel, cleaned, g, live)
    return panel, live, scores, warm & live


# --------------------------------------------------------------------------
def gate0(scores, base) -> int:
    names = list(M.CANDIDATES)
    n, T = base.shape

    # WITHIN EACH BAR, across the live names -- see the module docstring.
    cols = []
    for c in names:
        s = np.where(base, scores[c], np.nan)
        r = np.full((n, T), np.nan)
        for t in range(T):
            r[:, t] = D268.rankify(s[:, t])
        cols.append(r.reshape(-1))
    X = np.vstack(cols)
    ok = np.all(np.isfinite(X), axis=0)
    X = X[:, ok]
    print(f"\n  {X.shape[1]:,} name-bars with ALL {len(names)} candidates finite "
          f"(of {int(base.sum()):,} in the shared base)")
    print(f"  Ranking is within-bar, so this is the correlation the book's own "
          f"selection sees.")

    Rm = np.corrcoef(X)
    within, between = [], []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            same = M.AXIS_OF[names[i]] == M.AXIS_OF[names[j]]
            rec = {"a": names[i], "b": names[j], "rho": float(Rm[i, j]),
                   "axis_a": M.AXIS_OF[names[i]], "axis_b": M.AXIS_OF[names[j]]}
            (within if same else between).append(rec)

    print(f"\n  WITHIN-axis pairs:  n={len(within):3d}  mean |rho| "
          f"{np.mean([abs(p['rho']) for p in within]):.3f}")
    print(f"  BETWEEN-axis pairs: n={len(between):3d}  mean |rho| "
          f"{np.mean([abs(p['rho']) for p in between]):.3f}")

    viol = sorted([p for p in between if abs(p["rho"]) >= BETWEEN_AXIS_LIMIT],
                  key=lambda p: -abs(p["rho"]))
    print(f"\n  BETWEEN-AXIS pairs at |rho| >= {BETWEEN_AXIS_LIMIT} -- NOT distinct "
          f"inputs: {len(viol)}")
    for p in viol:
        print(f"    {p['a']:16s} ({p['axis_a']}) vs {p['b']:16s} ({p['axis_b']})"
              f"  rho {p['rho']:+.3f}")
    if not viol:
        print("    none")
    # DISCLOSED IN ADVANCE (D288 pre-registration): B6 `range_frac` and E5
    # `range_over_atr` share a numerator, and E1/E3 both measure volatility
    # level. If those show up above, the measurement is working, not surprising.

    lam = np.maximum(np.linalg.eigvalsh(Rm), 0.0)
    eff = float(lam.sum() ** 2 / (lam ** 2).sum())
    print(f"\n  EFFECTIVE INDEPENDENT CANDIDATES (participation ratio): "
          f"{eff:.2f} of {len(names)}")
    print(f"    first component holds {max(lam) / lam.sum():.1%} of the variance")
    print(f"    eigenvalues: " + " ".join(f"{v:.2f}" for v in sorted(lam)[::-1][:8])
          + " ...")

    per_axis = {}
    for ax in "ABCDEF":
        idx = [i for i, c in enumerate(names) if M.AXIS_OF[c] == ax]
        la = np.maximum(np.linalg.eigvalsh(Rm[np.ix_(idx, idx)]), 0.0)
        per_axis[ax] = float(la.sum() ** 2 / (la ** 2).sum())
        print(f"    axis {ax}: {per_axis[ax]:.2f} effective of {len(idx)}")

    ok_gate = eff >= MIN_EFFECTIVE_FAMILIES
    print(f"\n  bar: effective >= {MIN_EFFECTIVE_FAMILIES:.1f}")
    print(f"  VERDICT: {'PASS' if ok_gate else 'FAIL'} -- "
          + ("the best-of-31 floor prices looks that were genuinely taken"
             if ok_gate else
             "31 correlated looks are not 31 looks; the COUNT MUST BE RESTATED "
             "before gate A is read, because a floor over 31 nominal candidates "
             "sets the bar too high and could bury a real effect"))

    OUT0.write_text(json.dumps(
        {"purpose": "D288 gate 0: are the 31 candidates 31 distinct opinions?",
         "ranked": "within bar (cross-sectional), NOT within symbol -- the book "
                   "only ever ranks names against each other inside one bar",
         "names": names, "axis": M.AXIS_OF, "spearman": Rm.tolist(),
         "between_axis_violations": viol,
         "effective_independent": eff, "effective_per_axis": per_axis,
         "first_component_share": float(max(lam) / lam.sum()),
         "bar": MIN_EFFECTIVE_FAMILIES, "pass": bool(ok_gate),
         "cells": int(X.shape[1])}, indent=1))
    print(f"\n  wrote {OUT0.relative_to(REPO)}")
    return 0


# --------------------------------------------------------------------------
def rotate(score, ats, off):
    """Roll each symbol's values WITHIN its own live bars. Coverage unchanged."""
    out = np.full(score.shape, np.nan)
    for i, at in enumerate(ats):
        if at.size:
            out[i, at] = np.roll(score[i, at], int(off[i]))
    return out


def peak(score, base, fwd, T):
    """Max SPREAD and max t over 3 N x 12 horizons -- the grid the headline is
    read off, so the grid the floor must price.

    BOTH STATISTICS, FROM ONE PASS, AND BOTH REPORTED. A floor prices whatever
    quantity you maximise, and maximising raw spread systematically selects the
    NOISIEST cell: `md` peaks at +163.1 bp carrying t +1.31 while
    `close_in_range` peaks at +90.6 bp carrying t +6.43. A spread floor answers
    "how big a number does chance produce"; a t floor answers "how much evidence
    does chance produce". They are different questions and the second is the one
    a book cares about.

    DISCLOSED DEPARTURE. D288 pre-registered gate A as "best-of-31, one shared
    offset vector, D277's construction" without naming the statistic. Running two
    RAISES the multiplicity rather than lowering it -- it is a harder test, not
    an easier one -- and both floors are reported whatever they say. The ledger
    counts both.
    """
    mx, mt = -9e9, -9e9
    order, cnt = M.rank_columns(score, base)        # once, not once per N
    for N in M.N_LEVELS:
        ev_lo, ev_hi, _ = M.legs_from_order(order, cnt, N, base.shape)
        lr, lc = np.nonzero(ev_lo)
        hr, hc = np.nonzero(ev_hi)
        for k in M.HORIZONS:
            f = fwd[k]
            slo, clo = M.bar_sums(f, lr, lc, T)
            shi, chi = M.bar_sums(f, hr, hc, T)
            m = (clo > 0) & (chi > 0)
            if int(m.sum()) < M.MIN_BARS:
                continue
            d = slo[m] / clo[m] - shi[m] / chi[m]
            mx = max(mx, float(d.mean() * 1e4))
            sd = d.std(ddof=1)
            if sd > 0:
                mt = max(mt, float(d.mean() / (sd / np.sqrt(d.size))))
    return mx, mt


def gateA(panel, live, scores, base, sims, workers) -> int:
    T = live.shape[1]
    ats = [np.flatnonzero(live[i]) for i in range(live.shape[0])]
    fwd = M.forward_returns(panel, live)

    obs = {c: peak(scores[c], base, fwd, T) for c in M.CANDIDATES}
    observed = {c: v[0] for c, v in obs.items()}
    observed_t = {c: v[1] for c, v in obs.items()}
    bs = max(observed, key=observed.get)
    bt = max(observed_t, key=observed_t.get)
    print(f"\n  OBSERVED best of {len(M.CANDIDATES)}:")
    print(f"    by SPREAD  {observed[bs]:+8.1f} bp   {bs} (axis {M.AXIS_OF[bs]})")
    print(f"    by t       {observed_t[bt]:+8.2f}      {bt} (axis {M.AXIS_OF[bt]})",
          flush=True)

    rng = np.random.default_rng(SEED)
    # ONE SHARED OFFSET VECTOR PER DRAW, drawn up front so the parallel map is
    # reproducible regardless of the order threads finish in.
    offs = [rng.integers(1, T, size=live.shape[0]) for _ in range(sims)]

    def one(s, off):
        r = [peak(rotate(scores[c], ats, off), base, fwd, T) for c in M.CANDIDATES]
        return (max(x[0] for x in r), max(x[1] for x in r))

    print(f"\n  best-of-{len(M.CANDIDATES)} floor: {sims} shared-offset draws",
          flush=True)
    t0 = time.time()
    res = FN.parallel_map(one, list(enumerate(offs)), workers=workers)
    best = np.array([res[s][0] for s in range(sims)])
    best_t = np.array([res[s][1] for s in range(sims)])
    floor = float(np.percentile(best, 95))
    floor_t = float(np.percentile(best_t, 95))
    print(f"  {sims} draws in {time.time() - t0:.0f}s")

    print(f"\n{'=' * 78}")
    print(f"  BEST-OF-{len(M.CANDIDATES)} FLOOR (p95)")
    print(f"    by SPREAD  {floor:+8.1f} bp   null max: mean {best.mean():+.1f} "
          f"p50 {np.percentile(best, 50):+.1f} max {best.max():+.1f}")
    print(f"    by t       {floor_t:+8.2f}      null max: mean {best_t.mean():+.2f} "
          f"p50 {np.percentile(best_t, 50):+.2f} max {best_t.max():+.2f}")
    print(f"  observed best: {observed[bs]:+.1f} bp ({bs}), "
          f"t {observed_t[bt]:+.2f} ({bt})")

    sur_s = sorted([c for c in M.CANDIDATES if observed[c] > floor],
                   key=lambda c: -observed[c])
    sur_t = sorted([c for c in M.CANDIDATES if observed_t[c] > floor_t],
                   key=lambda c: -observed_t[c])
    print(f"\n  CLEARS THE SPREAD FLOOR: {len(sur_s)}")
    for c in sur_s:
        print(f"    {M.AXIS_OF[c]}  {c:16s} {observed[c]:+8.1f} bp")
    print(f"  CLEARS THE t FLOOR: {len(sur_t)}")
    for c in sur_t:
        print(f"    {M.AXIS_OF[c]}  {c:16s} t {observed_t[c]:+7.2f}  "
              f"({observed[c]:+.1f} bp)")
    # A SURVIVOR MUST CLEAR BOTH. Clearing only one is reported because a number
    # that is big but unevidenced, or evidenced but tiny, is exactly what the
    # reader needs to see rather than a single word.
    survivors = [c for c in sur_s if c in set(sur_t)]
    print(f"\n  GATE A SURVIVORS (clear BOTH): {len(survivors)}")
    for c in survivors:
        print(f"    {M.AXIS_OF[c]}  {c:16s} {observed[c]:+8.1f} bp  "
              f"t {observed_t[c]:+.2f}")
    if not survivors:
        print(f"    none -- and D288's stop condition applies: the mine is closed, "
              f"with no\n    thirty-second candidate and no re-cut of the axes.")
    print(f"{'=' * 78}")

    OUTA.write_text(json.dumps(
        {"purpose": "D288 gate A: the best-of-31 floor, D228's construction",
         "statistic": "max spread in bp over 3 N x 12 horizons",
         "rotation": "within each symbol's own live bars; one shared offset "
                     "vector per draw so the floor prices correlated looks",
         "seed": SEED, "sims": sims,
         "floor_p95": floor, "floor_p95_t": floor_t,
         "null_max": {"mean": float(best.mean()),
                      "p50": float(np.percentile(best, 50)),
                      "max": float(best.max())},
         "null_max_t": {"mean": float(best_t.mean()),
                        "p50": float(np.percentile(best_t, 50)),
                        "max": float(best_t.max())},
         "observed": observed, "observed_t": observed_t,
         "clears_spread_floor": sur_s, "clears_t_floor": sur_t,
         "survivors": survivors}, indent=1))
    print(f"\n  wrote {OUTA.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate0", action="store_true")
    ap.add_argument("--gateA", action="store_true")
    ap.add_argument("--sims", type=int, default=N_SIMS)
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()
    if not (a.gate0 or a.gateA):
        print(__doc__)
        return 0

    t0 = time.time()
    panel, live, scores, base = _panel()
    print(f"loaded and built in {time.time() - t0:.0f}s", flush=True)
    rc = 0
    if a.gate0:
        rc |= gate0(scores, base)
    if a.gateA:
        rc |= gateA(panel, live, scores, base, a.sims, a.workers)
    print(f"\n  {time.time() - t0:.0f}s total")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
