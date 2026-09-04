"""D323b -- the multiplicity, the ranking shift and the null quality D323 owes.

    uv run python scripts/d323b_shortlist_analysis.py

`run_d323_shortlist_at_operating_point.py` defined `m_eff` and `bh` and NEVER
CALLED THEM -- the cell loop wrote the JSON and stopped. That is my omission, not
a design choice, and this script supplies what the pre-registration promised:

  * BH-FDR at the NOMINAL and the EFFECTIVE test count (D321's amendment). The
    104 cells are built from 13 correlated scores over 4 nested holding periods,
    so a nominal correction would price tests that do not exist.
  * Q3, the study's PREMISE: does the candidate ranking move between D290's own
    best cells and N_eff = 2? Spearman against D290's published tier-1 order.
  * R7 per candidate: a null centred negative makes its p meaningless, which is
    `price_log`'s recorded defect and must not pass unremarked twice.
  * The incumbent at every k, which is the comparison Q2 turns on.

Cells with fill below 85% are FLAGGED and excluded from the headline, per D320:
a filter that starves the gate makes a narrower book, not a better one.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "d323b_analysis.json"
FILL_FLOOR = 0.85

# D290's published tier-1 spread order, by `open t` -- the ranking this study
# asks whether concentration reorders.
D290_ORDER = ("price_log", "macd_hist", "rsi", "dist_52w_high", "on_persist",
              "rev_5", "choch_dist", "retrace_leg", "skew_63", "macd_line",
              "hist_L", "rev_21", "dist_lvn")


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


Y = _load("d323", "run_d323_shortlist_at_operating_point.py")
W, F, D, M, SP, R = Y.W, Y.F, Y.D, Y.M, Y.SP, Y.R


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def main() -> int:
    d = json.loads((REPO / "data" / "d323_shortlist.json").read_text())
    C, INC = d["cells"], d["incumbent"]

    # ---- rebuild each cell's per-bar series, for the correlation -----------
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel.closes.T)
    VOL = np.full(CLOSE.shape, np.nan)
    sym = {s: i for i, s in enumerate(panel.symbols)}
    pos = {dt: i for i, dt in enumerate(panel.dates)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                VOL[t, i] = st.bar.volume
    finT = np.asarray(A["finT"])
    n, T = panel.live.shape
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    keep28 = F.keep_mask(F.roll_mean_T(CLOSE * VOL), finT, Y.DV_PCT, True)

    names = list(C)
    books, masks = [], []
    for nm in names:
        c = C[nm]
        rk = Y.rank_single(z, base, c["candidate"], n, T)
        G = Y.gate_from(rk, finT, keep28 if c["dv"] else None)
        W.BASE_HOLD = c["k"]
        r = W.simulate(A, G, Y.DEPTH, True)
        books.append(np.nan_to_num(r["book"], nan=0.0))
        masks.append(r["mask"])
    # PAIRWISE-COMPLETE CORRELATION, and the first version of this was WRONG.
    # It intersected all 104 masks and got 73 common bars, so a 104x104 matrix
    # was estimated on 73 observations -- rank-deficient, eigenvalues garbage,
    # and the effective count computed from it meaningless. Different candidates
    # activate on different bars, so the intersection collapses. Each pair is
    # correlated over the bars where BOTH are active instead.
    Mk = np.array(masks)
    B = np.array(books)
    q = len(names)
    Cm = np.eye(q)
    pair_n = []
    for i in range(q):
        for j in range(i + 1, q):
            both = Mk[i] & Mk[j]
            k = int(both.sum())
            pair_n.append(k)
            if k > 200:
                Cm[i, j] = Cm[j, i] = np.corrcoef(B[i][both], B[j][both])[0, 1]
    Cm = np.nan_to_num(Cm, nan=0.0)
    ev = np.linalg.eigvalsh(Cm)[::-1]
    liji = float(sum((1.0 if e >= 1 else 0.0) + min(1.0, max(0.0, e - np.floor(e)))
                     for e in ev))
    nyh = float(1 + (q - 1) * (1 - np.var(ev, ddof=1) / q))
    medc = float(np.median(Cm[np.triu_indices(q, 1)]))
    print("D323b  the multiplicity, the ranking shift and the null quality\n")
    print(f"  {q} cells; PAIRWISE-complete correlation, median pair overlap "
          f"{int(np.median(pair_n)):,} bars (the 104-way intersection is only "
          f"{int(np.logical_and.reduce(masks).sum())})")
    print(f"  median pairwise correlation {medc:.3f}")
    print(f"  EFFECTIVE TESTS   Li-Ji {liji:.1f}   Cheverud-Nyholt {nyh:.1f}   "
          f"(nominal {len(names)})")

    ps = np.array([C[nm]["p"] for nm in names])
    rej_nom = Y.bh(ps, len(names))
    rej_eff = Y.bh(ps, max(1, int(round(liji))))
    print(f"\n  BH q=0.10 at the NOMINAL {len(names)}: "
          f"{', '.join(nm for nm, r in zip(names, rej_nom) if r) or 'NONE'}")
    print(f"  BH q=0.10 at the EFFECTIVE {int(round(liji))}: "
          f"{', '.join(nm for nm, r in zip(names, rej_eff) if r) or 'NONE'}")

    # ---- R7: null quality per candidate ------------------------------------
    #
    # THE THRESHOLD HERE WAS WRONG IN THE FIRST VERSION AND IS CORRECTED. It
    # flagged any null with a NEGATIVE MEDIAN, which flagged 13 of 13 and so
    # told you nothing. R7's actual pathology, from D295, is a null whose **p95**
    # is negative -- "a null that the worst book in the grid tops is broken, not
    # passed". A costed two-name book built from a scrambled ranking SHOULD lose,
    # so a negative median is the null working, not failing. What must not happen
    # is the null's UPPER TAIL failing to reach positive territory.
    print("\nR7 -- the pathology is a null whose p95 is NEGATIVE (D295), not one")
    print("      whose median is. A scrambled 2-name book SHOULD lose money.")
    bad = []
    for cand in D290_ORDER:
        cs = [C[nm] for nm in names if C[nm]["candidate"] == cand]
        if not cs:
            continue
        p50 = float(np.median([c["null_p50"] for c in cs]))
        p95 = float(np.max([c["null_p95"] for c in cs]))
        if p95 < 0.0:
            bad.append(cand)
        print("    %-15s median null p50 %+7.3f   max null p95 %+7.3f   %s"
              % (cand, p50, p95, "FLAGGED -- TOOTHLESS" if p95 < 0 else "ok"))
    print("    %d of %d flagged" % (len(bad), len(D290_ORDER)))

    # ---- the headline table, fill-filtered ---------------------------------
    print("\nBEST CELL PER CANDIDATE (fill >= %.0f%%), against the incumbent"
          % (100 * FILL_FLOOR))
    inc = {k: INC[f"k{k}/dv0"]["sharpe_net"] for k in Y.KS}
    inc_dv = {k: INC[f"k{k}/dv1"]["sharpe_net"] for k in Y.KS}
    print("  incumbent net Sharpe by k, dv off: " +
          "  ".join("k%d %+.3f" % (k, v) for k, v in inc.items()))
    print("  incumbent net Sharpe by k, dv ON : " +
          "  ".join("k%d %+.3f" % (k, v) for k, v in inc_dv.items()))
    best_inc = max(list(inc.values()) + list(inc_dv.values()))
    print("  BEST INCUMBENT CELL: %+.3f\n" % best_inc)
    h = "  %-15s %4s %3s %9s %9s %8s %7s %8s %8s"
    print(h % ("candidate", "k", "dv", "netSHRP", "net bp", "half", "fill",
               "p", "vs inc"))
    print("  " + "-" * 80)
    rows, newrank = [], {}
    for cand in D290_ORDER:
        cs = [C[nm] for nm in names
              if C[nm]["candidate"] == cand and C[nm]["fill"] >= FILL_FLOOR]
        if not cs:
            newrank[cand] = -9.0
            continue
        b = max(cs, key=lambda c: c["sharpe_net"])
        newrank[cand] = b["sharpe_net"]
        rows.append(b)
        print(h % (cand, b["k"], "Y" if b["dv"] else "n",
                   "%+.3f" % b["sharpe_net"], "%+.2f" % b["net_bp"],
                   "%.2f" % b["held_half_spread"], "%.0f%%" % (100 * b["fill"]),
                   "%.4f" % b["p"], "%+.3f" % (b["sharpe_net"] - best_inc)))

    # ---- Q3: does the ranking move? ----------------------------------------
    old = np.arange(len(D290_ORDER), 0, -1, dtype=float)   # D290's order, best first
    new = np.array([newrank[c] for c in D290_ORDER])
    rho = spearman(old, new)
    print(f"\nQ3 -- the ranking shift: Spearman rho = {rho:+.3f} against D290's "
          f"published tier-1 order")
    print("     (Q3 predicted BELOW 0.7 -- that the ranking DOES move with width)")

    winners = [r for r in rows if r["sharpe_net"] > best_inc]
    print(f"\nQ2 -- {len(winners)} candidate(s) beat the best incumbent cell "
          f"({best_inc:+.3f}) on net Sharpe at fill >= {100*FILL_FLOOR:.0f}%:")
    for r in sorted(winners, key=lambda x: -x["sharpe_net"]):
        surv = rej_eff[names.index(
            f"{r['candidate']}/k{r['k']}/dv{int(r['dv'])}")]
        print("     %-15s k=%-3d dv=%s  %+.3f  p=%.4f  BH(eff) %s"
              % (r["candidate"], r["k"], "Y" if r["dv"] else "n",
                 r["sharpe_net"], r["p"], "SURVIVES" if surv else "rejected"))

    OUT.write_text(json.dumps(dict(
        note="D323b: the multiplicity, ranking shift and null quality the runner "
             "omitted. Cells below 85% fill excluded from the headline.",
        n_cells=q, median_pair_overlap=int(np.median(pair_n)), median_corr=medc,
        m_eff_li_ji=liji, m_eff_cheverud_nyholt=nyh,
        bh_nominal=[nm for nm, r in zip(names, rej_nom) if r],
        bh_effective=[nm for nm, r in zip(names, rej_eff) if r],
        toothless_nulls=bad, incumbent_by_k=inc, incumbent_by_k_dv=inc_dv,
        best_incumbent=best_inc, spearman_vs_d290=rho,
        best_per_candidate={r["candidate"]: r for r in rows}), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
