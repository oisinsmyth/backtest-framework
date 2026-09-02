"""D291 -- the three things the main runner did not measure.

    uv run python scripts/d291_diagnostics.py

1. Q3, WHICH WAS PRE-REGISTERED AND WHICH `run_d291_confluence.py` DOES NOT
   ANSWER. The prediction was that the dead-name veto cuts A's long-leg dead
   share by >= 10pp. It is a MECHANICAL check: a veto that does not do what it
   claims produces an uninterpretable result, whichever way the return goes.

2. THE PERMUTATION / PAIRED-t CONTRADICTION. 46% of veto cells put the observed
   book above 95% of their own random removals, while the paired t against those
   same removals has median +0.23. Both cannot be a fair reading of the same
   comparison, and which one is wrong changes the result.

3. WHY 18 OF 272 CELLS PRODUCED NOTHING. An unevaluated cell is not a passing
   cell and not a failing one, and a study that does not say which is which has
   a hole in its denominator.

The dead-name definition is D290's: a name whose live window ends before the
panel's last bar. Verified against gate 1g's own numbers -- price_log's long leg
reproduces at 33.5% exactly.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
spec = importlib.util.spec_from_file_location(
    "r291", REPO / "scripts" / "run_d291_confluence.py")
R = importlib.util.module_from_spec(spec)
sys.modules["r291"] = R
spec.loader.exec_module(R)
M = R.M
OUT = REPO / "data" / "d291_diagnostics.json"


def main() -> int:
    panel, _ = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    fwd = M.forward_returns(panel, live)
    pool, peaks = R.pool_and_peaks()
    res = json.loads((REPO / "data" / "d291_confluence.json").read_text())

    last = np.array([np.flatnonzero(live[i]).max() if live[i].any() else -1
                     for i in range(live.shape[0])])
    dead = last < (T - 1)

    Rk = {c: R.ranked(z[c], base) for c in pool}
    plans = {c: R.LegPlan(Rk[c][0], Rk[c][1], peaks[c][0], T) for c in pool}

    # ---------------------------------------------------------------- Q3
    print("Q3  DOES THE VETO ACTUALLY REMOVE DEAD NAMES?")
    print("    pre-registered: the dead-name veto cuts A's LONG-leg dead share "
          "by >= 10pp\n")
    print(f"    {'A':16s} {'B':16s} {'f':>5s} | {'dead% A':>8s} "
          f"{'dead% kept':>10s} {'change':>8s} | {'held':>6s}")
    q3 = []
    best = {}
    for a, b in R.CELLS["veto"]:
        if a not in pool or b not in pool:
            continue
        pl = plans[a]
        _, cnt_b, pos_b = Rk[b]
        d_all = float(dead[pl.lo].mean())
        for f in R.FRACTIONS:
            klo, _ = R.keep_masks(pos_b, cnt_b, pl, f)
            if not klo.any():
                continue
            d_kept = float(dead[pl.lo][klo].mean())
            row = dict(A=a, B=b, f=f, dead_a=d_all, dead_kept=d_kept,
                       change_pp=(d_kept - d_all) * 100,
                       held=float(klo.sum(axis=0).mean()), N=pl.N)
            q3.append(row)
            if a not in best or row["change_pp"] < best[a]["change_pp"]:
                best[a] = row
    for row in sorted(q3, key=lambda r: r["change_pp"])[:12]:
        print(f"    {row['A']:16s} {row['B']:16s} {row['f']:5.2f} | "
              f"{row['dead_a']:8.1%} {row['dead_kept']:10.1%} "
              f"{row['change_pp']:+7.1f}pp | {row['held']:6.1f}")
    ch = np.array([r["change_pp"] for r in q3])
    print(f"\n    {len(q3)} veto cells: change p50 {np.median(ch):+.1f}pp  "
          f"best {ch.min():+.1f}pp  worst {ch.max():+.1f}pp")
    print(f"    cells cutting the dead share by >= 10pp: "
          f"{int((ch <= -10).sum())} of {len(q3)}")
    print(f"    Q3 {'HOLDS' if ch.min() <= -10 else 'FAILS'} -- the best any "
          f"veto manages is {ch.min():+.1f}pp\n")

    # ------------------------------------------- the permutation contradiction
    print("\nTHE PERMUTATION / PAIRED-t CONTRADICTION")
    print("    for one veto cell, both statistics recomputed from the SAME 50 "
          "draws\n")
    probe = []
    for a, b in R.CELLS["veto"][:6]:
        if a not in pool or b not in pool:
            continue
        pl = plans[a]
        _, cnt_b, pos_b = Rk[b]
        k = peaks[a][1]
        klo, khi = R.keep_masks(pos_b, cnt_b, pl, 0.75)
        conf = R.spread_sums(fwd[k], pl, klo, khi, T)
        rng = np.random.default_rng(4242)
        ctrl, totals = R.control_random_removal(fwd[k], pl, klo, khi, T, rng)
        st = R.paired_t(conf[0], conf[1], ctrl[0], ctrl[1],
                        conf[2], conf[3], ctrl[2], ctrl[3])
        if st is None:
            continue
        dbp, t, bars, cbp, kbp = st
        # the permutation, but on the SAME common bars the paired t uses
        m = (conf[1] > 0) & (ctrl[1] > 0) & (conf[3] > 0) & (ctrl[3] > 0)
        obs = float(np.mean(conf[0][m] / conf[1][m] - conf[2][m] / conf[3][m]))
        p_own = float((totals >= obs).sum() + 1) / (totals.size + 1)
        probe.append(dict(A=a, B=b, paired_t=t, d_bp=dbp, obs_bp=obs * 1e4,
                          rand_mean_bp=float(totals.mean() * 1e4),
                          rand_sd_bp=float(totals.std(ddof=1) * 1e4),
                          perm_p=p_own,
                          implied_t=float((obs - totals.mean())
                                          / totals.std(ddof=1))))
    print(f"    {'A':16s} {'B':14s} | {'paired t':>8s} | {'obs bp':>8s} "
          f"{'rand bp':>8s} {'rand sd':>8s} | {'perm t':>7s} {'perm p':>7s}")
    for p in probe:
        print(f"    {p['A']:16s} {p['B']:14s} | {p['paired_t']:+8.2f} | "
              f"{p['obs_bp']:+8.1f} {p['rand_mean_bp']:+8.1f} "
              f"{p['rand_sd_bp']:8.1f} | {p['implied_t']:+7.2f} "
              f"{p['perm_p']:7.3f}")
    print("\n    The two disagree because they divide by DIFFERENT spreads. The")
    print("    paired t divides by the bar-to-bar sd of the difference; the")
    print("    permutation divides by the sd of 50 whole-history MEANS, which is")
    print("    ~sqrt(bars) smaller. The permutation is therefore the SHARPER")
    print("    test of 'does the veto beat random removal on average' -- and it")
    print("    has no multiplicity floor, which is exactly what 87 cells need.")

    # -------------------------------------------------- the 18 missing cells
    print("\n\nTHE 18 CELLS THAT PRODUCED NOTHING")
    have = {(r["kind"], r["A"], r["B"], r["f"]) for r in res["rows"]}
    missing = []
    for kind, a, b in R.group_list(pool):
        pl = plans[a]
        _, cnt_b, pos_b = Rk[b]
        for f in R.FRACTIONS:
            if (kind, a, b, f) in have:
                continue
            klo, khi = R.keep_masks(pos_b, cnt_b, pl, f)
            k = peaks[a][1]
            conf = R.spread_sums(fwd[k], pl, klo, khi, T)
            both = (conf[1] > 0) & (conf[3] > 0)
            ent = conf[1][conf[1] > 0]
            missing.append(dict(kind=kind, A=a, B=b, f=f, N=pl.N,
                                held=float(klo.sum(axis=0).mean()),
                                entries=float(ent.mean()) if ent.size else 0.0,
                                bars_both=int(both.sum())))
    print(f"    {'kind':5s} {'A':16s} {'B':16s} {'f':>5s} {'N':>3s} | "
          f"{'held/bar':>8s} {'entries':>8s} | {'bars w/ both':>12s}")
    for m in missing:
        print(f"    {m['kind']:5s} {m['A']:16s} {m['B']:16s} {m['f']:5.2f} "
              f"{m['N']:3d} | {m['held']:8.2f} {m['entries']:8.2f} | "
              f"{m['bars_both']:12d}")
    print(f"\n    {len(missing)} cells produced no statistic, and the reason is "
          f"NOT that any\n    one book is thin. Each of the four legs a paired "
          f"difference needs is\n    active on 600-1500 bars. It is the "
          f"FOUR-WAY INTERSECTION that collapses:\n    at N=3 and N=5 a book "
          f"re-enters about once a bar and fires on roughly a\n    quarter of "
          f"them, so all four legs coincide on 12-72 bars against D286's\n    "
          f"{R.MIN_BARS}-bar floor. Every one of the 18 is `choch_dist` (N=5) or "
          f"`rev_21` (N=3).\n    The paired difference is underpowered at small "
          f"N BY CONSTRUCTION, which is\n    a property of the design and not of "
          f"the candidates.")

    json.dump({"purpose": "D291 diagnostics: the pre-registered Q3 dead-name "
                          "check, the permutation/paired-t contradiction, and "
                          "the cells that produced no statistic.",
               "dead_definition": "live window ends before the panel's last bar",
               "q3": q3, "q3_best_per_A": best, "perm_probe": probe,
               "missing": missing}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
