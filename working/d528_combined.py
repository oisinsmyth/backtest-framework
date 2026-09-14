"""THE COMBINED TEST: opposite-extreme target x drift-following exits x stop width, with nulls.

    python working/d528_combined.py --self-test
    python working/d528_combined.py --run

Nothing admitted (R15). Micro universe (8 roots), in sample only; the reserved slice
(2026-04-11 -> 2026-09-09) remains UNREAD.

WHY THIS FILE EXISTS. ADDENDUM 5 crossed target x frame, so `opposite`+drift and `reflect`+drift
were measured -- but its G and tau ladders, AND its nulls, were run only in the FROZEN frame. Two
consequences the principal caught:

  * the best cell in that file (`reflect` + drift, net -$1.66/trade) has NO null, and
  * the one rung that turned positive net (G=4.0, frozen) was never tried in the drift frame,

so "all the improvements at once" was never actually tested. It is tested here, with a null on
every rung of the live grid and on both lenses.

DECLARED PRIMARY, before running: target = `reflect`, frame = `drift`, G = 3.0 (the principal's own
1.5*X proposal, NOT the ladder-best), tau = 40, `traverse`, micro, 3 slots. The two structural
choices are the ones the principal asked for; no parameter in the declared cell was picked by
looking at a table. G = 4.0 is deliberately NOT the declared stop, because it was chosen by
reading ADDENDUM 5's ladder and that is selection.

AND THE HONEST FRAME FOR ALL OF IT: the settings being combined were identified by inspecting
earlier in-sample tables. That is selection, so the sign-shuffle null is the only statistic here
that can speak, and even a clean null leaves the construction needing the reserved slice. Nothing
in this file can promote anything.

ONE OPTIMISATION, STATED. `classify2` is the expensive call and it does not depend on the target,
frame, stop or tau -- so it is called ONCE per session and every variant is resolved off it. That
turns 30 passes over the data into 1, which is what makes a null on the whole grid affordable
(60 shuffled passes rather than 1,800).
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_book_and_sides as B                 # noqa: E402
import d528_opposite_extreme_and_drift_stops as O   # noqa: E402

X = O.X
TAU = 40
G_LADDER = (2.5, 3.0, 3.5, 4.0, 5.0)
TARGETS = ("level", "opposite", "reflect")
FRAMES = ("frozen", "drift")
SLOTS = 3
N_SHUF = 20
SEED = 528881
CELLS = (("traverse", "flat", "C traverse"),
         ("none", "flat", "B no-classifier"),
         ("cross2", "line", "A as-specified"))
PRIMARY = ("reflect", "drift", 3.0)
# the grid that carries nulls: the drift frame, which ADDENDUM 5 never nulled
LIVE = [(t, "drift", g) for t in ("opposite", "reflect") for g in G_LADDER]


def P(*a):
    print(*a, flush=True)


def variants_for_session(pth, tick, tick_usd, cost_tk, cl, lvl, day_idx, b0, root, grid):
    """Resolve EVERY variant in `grid` off ONE classify2 call. Returns {variant: [trades]}."""
    c = Z.classify2(pth, tick)
    if c is None:
        return {}
    keep = Z.entry_mask(c, lvl, tick, cost_tk, cl)
    out = {}
    for (target, frame, g) in grid:
        out[(target, frame, g)] = O.resolve(
            pth, c, lvl, keep, tick, tick_usd, cost_tk, target, frame, g, TAU,
            day_idx, b0, root)
    return out


def gather_grid(cl, lvl, grid, d, sp, roots, day_index, shuffle_rng=None):
    acc = {v: [] for v in grid}
    for r in roots:
        gg = d[d["root"] == r]
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        for day, pth, b0 in B.sessions_with_bars(gg, 1):
            if shuffle_rng is not None:
                pth = Z.shuffled(pth, shuffle_rng, 1)[0]
            got = variants_for_session(pth, tick, tick_usd, cost_tk, cl, lvl,
                                       day_index[day], b0, r, grid)
            for v, tr in got.items():
                if tr:
                    acc[v].extend(tr)
    return acc


def self_test():
    rng = np.random.default_rng(21)
    d = None
    # 1. THE ONE-CLASSIFY OPTIMISATION MUST BE EXACT. Resolving every variant off a single
    #    classify2 call must give bit-identical trades to calling classify2 per variant, or the
    #    speedup changed a number. Probed on a tie-heavy path, where rewrites disagree.
    for label, pth in (("gaussian", 20000 + np.cumsum(rng.normal(0, 3.0, 260))),
                       ("tie-heavy", 20000 + np.cumsum(
                           np.round(rng.normal(0, 1.0, 260) * 4) / 4))):
        grid = [(t, f, g) for t in TARGETS for f in FRAMES for g in (2.5, 3.0)]
        fast = variants_for_session(pth, 0.25, 1.0, 1.0, "none", "flat", 0, 540, "T", grid)
        for v in grid:
            c = Z.classify2(pth, 0.25)
            keep = Z.entry_mask(c, "flat", 0.25, 1.0, "none")
            slow = O.resolve(pth, c, "flat", keep, 0.25, 1.0, 1.0, v[0], v[1], v[2], TAU,
                             0, 540, "T")
            assert len(fast[v]) == len(slow), f"{label} {v}: {len(fast[v])} vs {len(slow)}"
            for a, b in zip(fast[v], slow):
                assert a == b, f"{label} {v}: trade mismatch\n{a}\n{b}"
        P(f"   [1] {label:<10} one-classify grid == per-variant, bit-identical "
          f"({len(grid)} variants)  OK")

    # 2. THE GRID MUST ACTUALLY VARY. If different variants produced identical trade lists the
    #    whole file would be comparing a setting against itself.
    # Accumulated over many sessions and with the alignment filter off, so there are enough
    # trades for the grid to be able to differ. A 400-bar aligned path gives ~3 entries, where
    # 30 variants collapse to 2 signatures and the check cannot catch a collapsed grid.
    grid = [(t, f, g) for t in TARGETS for f in FRAMES for g in G_LADDER]
    got = {v: [] for v in grid}
    for i in range(40):
        pp = 20000 + np.cumsum(rng.normal(0, 3.0, 300))
        cc = Z.classify2(pp, 0.25)
        kk = Z.entry_mask(cc, "flat", 0.25, 0.0, "none", align=False)
        for v in grid:
            got[v].extend(O.resolve(pp, cc, "flat", kk, 0.25, 1.0, 0.0, v[0], v[1], v[2],
                                    TAU, i, 540, "T"))
    n_tr = len(got[grid[0]])
    assert n_tr >= 300, f"only {n_tr} trades -- the grid-variation check cannot fire"
    sigs = {v: tuple(z["kind"] for z in tr) for v, tr in got.items() if tr}
    ndist = len(set(sigs.values()))
    assert ndist >= 20, (f"only {ndist} distinct outcome signatures across {len(grid)} variants "
                         f"on {n_tr} trades -- the grid is collapsing")
    P(f"   [2] {len(sigs)} variants on {n_tr:,} trades, {ndist} distinct outcome signatures"
      f"      OK")

    # 3. STRUCTURAL MONOTONICITY, within each (target, frame): a WIDER stop can only make the
    #    target more likely to be reached first.
    for t in TARGETS:
        for f in FRAMES:
            pt = []
            for g in G_LADDER:
                tr = got.get((t, f, g)) or []
                if len(tr) < 5:
                    pt = []
                    break
                pt.append(float(np.mean([z["kind"] == 0 for z in tr])))
            if pt:
                assert pt == sorted(pt), f"{t}/{f}: P(target) not monotone in G: {pt}"
    P("   [3] P(target) monotone in the stop width within every (target, frame)          OK")

    # 4. AND THE DECLARED PRIMARY MUST BE IN THE LIVE GRID, or its null is never computed --
    #    which is exactly the omission this file exists to fix.
    assert PRIMARY in LIVE, f"the declared primary {PRIMARY} is not in the nulled grid"
    P(f"   [4] declared primary {PRIMARY} IS in the nulled grid ({len(LIVE)} rungs)      OK")
    P("\n   all self-tests pass\n")


def run():
    d = Q.load()
    sp = Q.specs()
    roots = [r for r in sorted(set(d["root"]) & set(sp)) if sp[r].get("has_micro")]
    udays = sorted(set(d["day"]))
    day_index = {u: i for i, u in enumerate(udays)}
    total_minutes = len(udays) * 420
    full = [(t, f, g) for t in TARGETS for f in FRAMES for g in G_LADDER]
    P("THE COMBINED TEST -- target x frame x stop width, with nulls on the drift frame")
    P(f"  micro universe, {len(roots)} roots, {len(udays)} sessions, s=1, x={X} sigma, tau={TAU}")
    P(f"  DECLARED PRIMARY: target={PRIMARY[0]}, frame={PRIMARY[1]}, G={PRIMARY[2]}, "
      f"traverse, {SLOTS} slots")
    P(f"  G=4.0 is deliberately NOT declared: it was chosen by reading ADDENDUM 5's ladder.\n")

    real = {}
    for (cl, lvl, label) in CELLS:
        real[cl] = gather_grid(cl, lvl, full, d, sp, roots, day_index)

    P("=" * 116)
    P("1  THE FULL COMBINED GRID, real data. Both lenses side by side.")
    P("   PATH-INVARIANT per trade | PATH-VARIANT book at 3 slots")
    P("")
    for (cl, lvl, label) in CELLS:
        P(f"  {label}")
        P("    target    frame   G     n      TGT%  win%  payoff | GROSS $   NET $ | "
          "bk trades  Sh_g   Sh_n   NET$tot  maxDD/2k")
        for v in full:
            tr = real[cl].get(v) or []
            iv = O.invariant(tr)
            if iv is None or iv["n"] < 20:
                continue
            vv = O.variant(tr, SLOTS, total_minutes)
            star = "  <-- PRIMARY" if (cl == "traverse" and v == PRIMARY) else ""
            P(f"    {v[0]:<9} {v[1]:<7} {v[2]:.1f} {iv['n']:>6,} {iv['p_tgt']:>6.1%} "
              f"{iv['win']:>5.1%} {iv['payoff']:>7.2f} | {iv['gross_pt']:>+8.2f} "
              f"{iv['net_pt']:>+7.2f} | {vv['n']:>9,} {vv['sharpe_g']:>+6.2f} "
              f"{vv['sharpe_n']:>+6.2f} {vv['net_usd']:>+9.0f} {vv['dd_frac_limit']:>9.2f}"
              f"{star}")
        P("")

    P("=" * 116)
    P(f"2  NULLS on the drift-frame grid -- {N_SHUF} sign-shuffled universes, both lenses.")
    P("   This is the grid ADDENDUM 5 left un-nulled. 'above' means the real value exceeds p95.")
    P("")
    rng = np.random.default_rng(SEED)
    for (cl, lvl, label) in CELLS:
        nulls = {v: {"gi": [], "sg": [], "sn": []} for v in LIVE}
        for _ in range(N_SHUF):
            acc = gather_grid(cl, lvl, LIVE, d, sp, roots, day_index, shuffle_rng=rng)
            for v in LIVE:
                tr = acc.get(v) or []
                iv = O.invariant(tr)
                vv = O.variant(tr, SLOTS, total_minutes)
                if iv:
                    nulls[v]["gi"].append(iv["gross_pt"])
                if vv:
                    nulls[v]["sg"].append(vv["sharpe_g"])
                    nulls[v]["sn"].append(vv["sharpe_n"])
        P(f"  {label}")
        P("    target    G    real gross | null p50    p95   | real Sh_g | null p50   p95   |"
          " real Sh_n | null p50   p95   | verdict")
        for v in LIVE:
            tr = real[cl].get(v) or []
            iv = O.invariant(tr)
            vv = O.variant(tr, SLOTS, total_minutes)
            if iv is None or iv["n"] < 20 or not nulls[v]["gi"]:
                continue
            gi = np.array(nulls[v]["gi"]); sg = np.array(nulls[v]["sg"])
            sn = np.array(nulls[v]["sn"])
            above = []
            if iv["gross_pt"] > np.percentile(gi, 95):
                above.append("gross")
            if vv and vv["sharpe_g"] > np.percentile(sg, 95):
                above.append("Sh_g")
            if vv and vv["sharpe_n"] > np.percentile(sn, 95):
                above.append("Sh_n")
            verdict = ("ABOVE p95: " + "+".join(above)) if above else "inside"
            if above and vv and vv["net_pt"] <= 0:
                verdict += " (but net<0)"
            star = " <-- PRIMARY" if (cl == "traverse" and v == PRIMARY) else ""
            P(f"    {v[0]:<9} {v[2]:.1f} {iv['gross_pt']:>+10.2f} | "
              f"{np.percentile(gi,50):>+8.2f} {np.percentile(gi,95):>+6.2f} | "
              f"{vv['sharpe_g']:>+9.2f} | {np.percentile(sg,50):>+8.2f} "
              f"{np.percentile(sg,95):>+6.2f} | {vv['sharpe_n']:>+9.2f} | "
              f"{np.percentile(sn,50):>+8.2f} {np.percentile(sn,95):>+6.2f} | "
              f"{verdict}{star}")
        P("")

    P("=" * 116)
    P("3  THE INCREMENT: what each change was worth, cell C, at the principal's own G=3.0")
    P("")
    base = real["traverse"].get(("level", "frozen", 3.0)) or []
    P("    step                                        NET $/trade   book Sh_n   delta")
    prev = None
    for v, name in ((("level", "frozen", 3.0), "start: level target, frozen exits"),
                    (("opposite", "frozen", 3.0), "+ target at the band edge"),
                    (("reflect", "frozen", 3.0), "+ target at the mirror instead"),
                    (("reflect", "drift", 3.0), "+ drift-following exits  = PRIMARY")):
        tr = real["traverse"].get(v) or []
        iv = O.invariant(tr)
        vv = O.variant(tr, SLOTS, total_minutes)
        if iv is None:
            continue
        dl = "" if prev is None else f"{iv['net_pt'] - prev:+.2f}"
        P(f"    {name:<44} {iv['net_pt']:>+10.2f} {vv['sharpe_n']:>+11.2f}   {dl}")
        prev = iv["net_pt"]
    P("")
    P("  Multiplicity: the settings combined here were identified by inspecting earlier")
    P("  in-sample tables, which is selection. Only the null columns can speak, and a clean")
    P("  null would still leave the construction needing the reserved slice.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        P("SELF-TESTS")
        self_test()
    if a.run:
        run()
    if not (a.self_test or a.run):
        ap.error("choose --self-test or --run")
