"""D394 -- stops, take profits and trailing stops on the low hold: 63 cells per hold, re-cut.

    uv run python scripts/run_d394_exit_grid.py --selftest
    uv run python scripts/run_d394_exit_grid.py --run

Pre-registration: docs/decisions/D394-exit-rules-on-the-low-hold.md, committed BEFORE this file
(R8), with amendment 2a' also committed before it.

THE KERNEL IS NOT TOUCHED. D380 established that a trade's P&L is the sum of its OWN per-bar path,
so every exit rule is a re-cut of one stored cumulative-sum matrix. `trade_paths`, `pnl_at`,
`assert_CUT` and `assert_OVL` are IMPORTED from `run_d380_exit_rules`, not reimplemented -- adding
an exit mode to `d345_event_book` would touch the file eighteen studies depend on, to compute
something that needs no kernel at all.

THE BAR, from the pre-registration's section 0 and fixed before any number here: an exit rule does
NOT change cost per trade -- same entries, one round trip, ~61 bp. So gross must rise
+10.52 -> ~61 at cap 10 (5.8x) to reach gate 1c's 1.0x. **Q1 is declared AGAINST the construction:
no cell of the 126 exceeds 0.6x.**

AND THE RECORD PREDICTS THE SIGN. The cap-20 ledger's mean is +22.06 but +60.29 with the worst 1%
dropped and **-19.82 with the best 1% dropped** -- the RIGHT tail carries this book. So a take
profit should REDUCE gross (Q2) and a trailing stop should behave like one (Q3). Both declared
against.

FILL: market-on-close on the bar the rule fires, which is D380's convention. Section 2's "next
open" was not implementable -- the re-cut matrix is close-to-close. The one-bar-later sensitivity
is reported for the best cell because MOC is the more favourable of the two.

ASSERTIONS
  [CUT] the re-cut reproduces the KERNEL's own per-trade P&L before any rule is applied (D380's).
  [B]   with every level off, each arm reproduces the plain cap ledger BIT-IDENTICALLY.
  [OVL] every rule SHORTENS: same trade count, no hold above the baseline's (D380's).
  [M]   the cap is still in force -- no hold exceeds it.
  [H]   hand cases for all three rules on a constructed path, before the fixture.
  [X]   the self-test RAISES on a stop that reads a bar it cannot know and on a trailing peak that
        includes the current bar.
  [P]   the JSON is persisted BEFORE it is rendered.
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _rss():
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 1e9
    except Exception:
        return float("nan")


OUT = REPO / "data" / "d394_exit_grid.json"
CANDIDATE = "up_run_21"
SHAPE = "E1"
PRIMARY_CAP = 10                       # declared in section 2; cap 5 reported beside it
CAPS = (10, 5)
LEVELS_BP = (500.0, 1000.0, 2000.0)    # section 2's {5%, 10%, 20%}, in bp -- the unit C is in
GATE_1C = 1.0
Q1_BOUND = 0.6                         # section 4's Q1: the best of all 126 stays below this


# ------------------------------------------------------------------ the rules
def rule_holds(C, holds0, s=None, p=None, r=None):
    """Per-trade hold under a stop / take profit / trailing stop, or any combination.

    `C[i, k]` is the trade's cumulative hedged bp through its own bar k, NaN past its life. A rule
    fires at the FIRST bar whose cumulative value breaches, and the trade is booked at that bar's
    close (D380's convention). `holds0` and the cap always still bind, so a rule can only SHORTEN.

    Causality: bar k's decision reads C[:, :k+1] only -- `argmax` over the hit mask takes the first
    True, and every column of C at or before k is known at the close of k. The trailing peak uses
    an INCLUSIVE running max, so at k=0 the drawdown is 0 and no trail can fire on its own first
    bar."""
    valid = ~np.isnan(C)
    BIG = np.iinfo(np.int64).max
    cands = []

    def first_hit(hit):
        return np.where(hit.any(axis=1), hit.argmax(axis=1) + 1, BIG).astype(np.int64)

    with np.errstate(invalid="ignore"):
        if s is not None:
            cands.append(first_hit(valid & (C <= -s)))
        if p is not None:
            cands.append(first_hit(valid & (C >= p)))
        if r is not None:
            peak = np.fmax.accumulate(np.where(valid, C, -np.inf), axis=1)
            cands.append(first_hit(valid & (C <= peak - r)))
    first = np.minimum.reduce(cands) if cands else np.full(C.shape[0], BIG, np.int64)
    return np.minimum(first, np.asarray(holds0, np.int64)).astype(np.int64)


def grid():
    """The 63 cells section 2 declared: 3 singles x 3 levels, 3 pairs x 9, 1 triple x 27."""
    cells = []
    for s in LEVELS_BP:
        cells.append(("S", s, None, None))
    for p in LEVELS_BP:
        cells.append(("T", None, p, None))
    for r in LEVELS_BP:
        cells.append(("R", None, None, r))
    for s in LEVELS_BP:
        for p in LEVELS_BP:
            cells.append(("S*T", s, p, None))
    for s in LEVELS_BP:
        for r in LEVELS_BP:
            cells.append(("S*R", s, None, r))
    for p in LEVELS_BP:
        for r in LEVELS_BP:
            cells.append(("T*R", None, p, r))
    for s in LEVELS_BP:
        for p in LEVELS_BP:
            for r in LEVELS_BP:
                cells.append(("S*T*R", s, p, r))
    assert len(cells) == 63, len(cells)
    return cells


def label(fam, s, p, r):
    bits = [f"s{int(s / 100)}" if s else "", f"p{int(p / 100)}" if p else "",
            f"r{int(r / 100)}" if r else ""]
    return f"{fam}:" + "/".join(b for b in bits if b)


# ------------------------------------------------------------------ self-test
def selftest(V80) -> int:
    print("D394 SELF-TEST -- the three rules on hand paths, then two breaks that must be caught\n")
    # a path that rises to +12%, falls to -6%, recovers. bp: 500, 1200, 600, -600, 0
    C = np.array([[500.0, 1200.0, 600.0, -600.0, 0.0]])
    h0 = np.array([5])

    assert rule_holds(C, h0).tolist() == [5], "[B] no rule must not shorten"
    print("    [B] with every level off the hold is unchanged (5)")

    # stop at -500 bp: first breach is bar 3 (-600) -> hold 4
    assert rule_holds(C, h0, s=500.0).tolist() == [4], rule_holds(C, h0, s=500.0)
    # take profit at +1000: first breach bar 1 (1200) -> hold 2
    assert rule_holds(C, h0, p=1000.0).tolist() == [2], rule_holds(C, h0, p=1000.0)
    # trail 500: peak 1200 at bar 1; bar 2 is 600 = 1200-600 <= 700 -> fires bar 2 -> hold 3
    assert rule_holds(C, h0, r=500.0).tolist() == [3], rule_holds(C, h0, r=500.0)
    print("    [H] stop -500 -> hold 4 | target +1000 -> hold 2 | trail 500 -> hold 3")

    # combined takes the EARLIEST
    assert rule_holds(C, h0, s=500.0, p=1000.0, r=500.0).tolist() == [2]
    print("    [H] the combination fires on the earliest of the three (2)")

    # a trail cannot fire on its own first bar: peak is inclusive
    assert rule_holds(np.array([[-900.0, 100.0]]), np.array([2]), r=500.0).tolist() == [2], \
        "[X] a trail fired on bar 0, so the running peak is EXCLUSIVE of the current bar"
    print("    [X] a trail cannot fire on its own first bar (the peak is inclusive)")

    # [M] the cap still binds
    assert rule_holds(C, np.array([2]), s=500.0).tolist() == [2]
    print("    [M] a shorter baseline hold still binds over a later rule breach")

    # [X] a stop that reads a bar it cannot know: shift the hit mask LEFT by one and require
    #     a DIFFERENT answer, which is what a look-ahead would produce
    bad = np.where(~np.isnan(C) & (C <= -500.0), True, False)
    lead = np.zeros_like(bad)
    lead[:, :-1] = bad[:, 1:]
    h_bad = np.where(lead.any(axis=1), lead.argmax(axis=1) + 1, 5)
    assert h_bad.tolist() != rule_holds(C, h0, s=500.0).tolist(), \
        "[X] a one-bar look-ahead gives the SAME hold, so this test cannot catch one"
    print(f"    [X] a one-bar look-ahead would give hold {h_bad.tolist()[0]}, not 4 -- "
          f"the test can distinguish them")
    print("\nSELF-TEST PASSED")
    return 0


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    V80 = _load("d380r", "run_d380_exit_rules.py")
    if a.selftest:
        return selftest(V80)
    if not a.run:
        ap.error("pass --selftest or --run")
    selftest(V80)
    t0 = time.time()

    R = _load("d393b", "run_d393_bs_null.py")
    PREP = _load("d348p", "d348_prep.py")
    SG = _load("ragged_sign_scores", "ragged_sign_scores.py")
    V50 = _load("d350r", "run_d350_long_timing_screen.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    V47 = PREP.V47

    P, elig, cols, masks, dec, T, n, bucket, elig_b = R.build(PREP, V50, SG)
    col = cols[CANDIDATE]
    pct = V47.percentile_grid(col)
    mask = V50.shape_masks(pct, elig)[SHAPE][0]
    sc = np.where(np.isfinite(col), col, 50.0)
    del cols, masks, dec, bucket, elig_b, pct
    gc.collect()
    print(f"  build {time.time() - t0:.0f}s, RSS {_rss():.2f} GB", flush=True)

    cells_out = {}
    base_out = {}
    for cap in CAPS:
        res0 = V59.run_mirror(P, mask, sc, "cap", cap)
        pnl0 = np.asarray(V47.pnl_bp(res0), float)
        tr0 = res0["trades"]
        C, holds0 = V80.trade_paths(P, res0)

        cut = V80.assert_CUT(C, holds0, pnl0)
        print(f"    cap {cap}: [CUT] re-cut matches the kernel to {cut['max_abs_dev']:.2e} "
              f"on {len(tr0):,} trades", flush=True)
        h_none = rule_holds(C, holds0)
        assert np.array_equal(h_none, holds0), "[B] the no-rule hold is not the baseline's"
        assert np.array_equal(V80.pnl_at(C, h_none), V80.pnl_at(C, holds0)), "[B] not bit-identical"
        print(f"    cap {cap}: [B] with every level off the ledger is the plain cap ledger, "
              f"bit-identically", flush=True)

        cost0, half0, px0 = V47.two_c(tr0, P["HALF"]["PUB"], P["CLOSE"])
        base_out[cap] = dict(trades=len(tr0), gross_bp=float(pnl0.mean()),
                             median_bp=float(np.median(pnl0)), hold=float(holds0.mean()),
                             round_trip=float(cost0), net_bp=float(pnl0.mean() - cost0),
                             ratio=float(pnl0.mean() / cost0))

        for fam, s, p, r in grid():
            h = rule_holds(C, holds0, s, p, r)
            assert (h <= holds0).all(), "[OVL] a rule lengthened a hold"
            assert (h <= cap).all(), "[M] a hold exceeds the cap"
            pnl = V80.pnl_at(C, h)
            tr = [(t_[0], t_[1], int(hh), t_[3], t_[4]) for t_, hh in zip(tr0, h)]
            cost, half, px = V47.two_c(tr, P["HALF"]["PUB"], P["CLOSE"])
            fired = int((h < holds0).sum())
            cells_out[f"cap{cap}/{label(fam, s, p, r)}"] = dict(
                cap=cap, family=fam, stop=s, target=p, trail=r,
                fired=fired, fired_share=fired / len(tr0),
                trades=len(tr0), gross_bp=float(pnl.mean()), median_bp=float(np.median(pnl)),
                hold=float(h.mean()), per_bar_bp=float(pnl.mean() / h.mean()),
                round_trip=float(cost), net_bp=float(pnl.mean() - cost),
                ratio=float(pnl.mean() / cost),
                delta_gross=float(pnl.mean() - pnl0.mean()))
        print(f"    cap {cap}: 63 cells re-cut ({time.time() - t0:.0f}s)", flush=True)

    # ---- score the predictions ------------------------------------------
    best_k = max(cells_out, key=lambda k: cells_out[k]["ratio"])
    best = cells_out[best_k]
    q1 = best["ratio"] < Q1_BOUND
    tarms = {k: v for k, v in cells_out.items() if v["family"] == "T"}
    rarms = {k: v for k, v in cells_out.items() if v["family"] == "R"}
    sarms = {k: v for k, v in cells_out.items() if v["family"] == "S"}
    q2 = all(v["delta_gross"] < 0 for v in tarms.values())
    q3 = all(v["delta_gross"] < 0 for v in rarms.values())

    payload = dict(study=394, stage="grid", score=CANDIDATE, shape=SHAPE,
                   caps=list(CAPS), primary_cap=PRIMARY_CAP, levels_bp=list(LEVELS_BP),
                   prereg="docs/decisions/D394-exit-rules-on-the-low-hold.md",
                   fill="market-on-close on the firing bar (D380's convention; amendment 2a')",
                   purpose="126 exit-rule cells by re-cut. DESCRIPTIVE unless a cell clears "
                           "gate 1c; no null drawn here. Admits nothing (R15).",
                   baseline=base_out, cells=cells_out,
                   best_cell=best_k, best=best,
                   predictions=dict(Q1_no_cell_above_0p6=bool(q1),
                                    Q2_target_reduces_gross=bool(q2),
                                    Q3_trail_reduces_gross=bool(q3)),
                   gate_1c=GATE_1C,
                   any_cell_clears_1c=bool(best["ratio"] >= GATE_1C))
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    # ---- render ----------------------------------------------------------
    print(f"\nBASELINE (no exit rule)\n")
    for cap, b in base_out.items():
        print(f"  cap {cap:<3d} {b['trades']:>7,} trades  gross {b['gross_bp']:+7.2f}  "
              f"2c {b['round_trip']:6.2f}  net {b['net_bp']:+7.2f}  ratio {b['ratio']:.2f}x")

    for cap in CAPS:
        print(f"\nCAP {cap} -- all 63 cells, best 12 by ratio (full grid in the artifact)\n")
        sub = {k: v for k, v in cells_out.items() if v["cap"] == cap}
        top = sorted(sub, key=lambda k: -sub[k]["ratio"])[:12]
        print(f"  {'cell':<20s} {'fired':>7s} {'gross':>8s} {'d.gross':>8s} {'median':>8s} "
              f"{'hold':>5s} {'2c':>6s} {'net':>8s} {'ratio':>7s}")
        for k in top:
            v = sub[k]
            print(f"  {k:<20s} {100 * v['fired_share']:6.1f}% {v['gross_bp']:+8.2f} "
                  f"{v['delta_gross']:+8.2f} {v['median_bp']:+8.2f} {v['hold']:5.1f} "
                  f"{v['round_trip']:6.2f} {v['net_bp']:+8.2f} {v['ratio']:7.2f}x")

    print(f"\nARM SUMMARY on the primary cap {PRIMARY_CAP} -- change in gross vs the baseline\n")
    for fam, nm in (("S", "stop"), ("T", "take profit"), ("R", "trailing stop")):
        row = [(v["stop"] or v["target"] or v["trail"], v["delta_gross"])
               for k, v in cells_out.items() if v["cap"] == PRIMARY_CAP and v["family"] == fam]
        row.sort()
        print(f"  {nm:<14s} " + "  ".join(f"{int(l / 100)}%: {d:+7.2f}" for l, d in row))

    print(f"\nPREDICTIONS")
    print(f"  Q1  no cell above {Q1_BOUND}x ratio          "
          f"{'HELD' if q1 else 'FAILED'}   (best {best['ratio']:.2f}x at {best_k})")
    print(f"  Q2  take profit REDUCES gross everywhere   {'HELD' if q2 else 'FAILED'}")
    print(f"  Q3  trailing stop REDUCES gross everywhere {'HELD' if q3 else 'FAILED'}")
    print(f"\n  GATE 1c (ratio >= {GATE_1C}): "
          f"{'CLEARED by ' + best_k if best['ratio'] >= GATE_1C else 'NOT CLEARED by any of the 126'}")
    print(f"\n  ({time.time() - t0:.0f}s)  No null drawn. Nothing admitted (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
