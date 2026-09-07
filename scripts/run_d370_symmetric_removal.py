"""D370 -- the symmetric top-ten removal: every draw loses its OWN winners.

    uv run python scripts/run_d370_symmetric_removal.py --selftest
    uv run python scripts/run_d370_symmetric_removal.py --sym --draws 2000 --part i --nparts 8
    uv run python scripts/run_d370_symmetric_removal.py --report

D367 removed the ten names the OBSERVED book earned most from, then compared what remained against rotated gates
that never produced those names. D369 measured the resulting bias: the observed book drops 4.187 bp/bar, the
median rotation only 2.256. A set chosen from one book's outcome cannot test that book against books that did not
produce it.

Here every draw removes its OWN top ten -- the selection happens inside the draw, so nothing crosses from the
observed book to its null. The hedge is rebuilt on the reduced universe (a name you cannot trade is a name you
cannot short); the gate's INDEX is deliberately not reduced, because the market still contains those names and
reducing it per draw would make the gate a different object in every draw.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import d369_fast_kernel as FK                 # noqa: E402
import run_d369_null_precision as V69         # noqa: E402
import run_d367_gate_deconstruction as V67    # noqa: E402
import run_d366_gated_buffer as V66           # noqa: E402
import run_d365_momentum_buffer as V65        # noqa: E402

PREP, V58, V50 = FK.PREP, FK.V58, V66.V50
STUDY, SEED, TOPN = 370, V66.SEED, 10
OUT = REPO / "data"


def el(t0):
    return f"{time.time() - t0:.0f}s"


def name_pnl(K, hold, rows, e0):
    """Per-name hedged P&L in bp, from the kernel's own pre-zeroed grids -- the same values the book sums."""
    c = np.where(hold, K.ZCC, 0.0).sum(axis=0)
    np.add.at(c, rows, K.ZOC[e0, rows] - K.ZCC[e0, rows])      # entry bars fill open-to-close
    return c * 1e4


def reduced_pieces(P, cols, elig_full):
    """The universe with `cols` removed: re-ranked score, reduced eligibility, and a hedge rebuilt on it."""
    e2 = elig_full.copy()
    e2[:, cols] = False
    raw = np.asarray(V50.lagged(P, V65.SCORE), float).copy()
    raw[:, cols] = np.nan
    pct2 = V66.V47.percentile_grid(raw)
    cc2, oc2 = V66.dvw_market(dict(P, elig=e2))                # the hedge cannot short what it cannot trade
    return pct2, e2, cc2, oc2


def kernel(P, pct, elig, cc, oc):
    K = FK.Kernel(P, pct, elig, cc, oc)
    K.keep_open = K.keep_shut                                  # D369's single exit rank
    return K


def one_draw(P, K_full, gate, elig_full):
    """A book under `gate`, then the same book with ITS OWN top ten removed from the universe."""
    hold = K_full.hold(gate)
    rows, e0, ex = K_full.ledger(hold)
    per = name_pnl(K_full, hold, rows, e0)
    cols = np.argsort(per)[::-1][:TOPN]
    pct2, e2, cc2, oc2 = reduced_pieces(P, cols, elig_full)
    return kernel(P, pct2, e2, cc2, oc2).net(gate), [int(c) for c in cols]


# ================================================================== stages
def build(P):
    pct = V58.pct_of(P, V65.SCORE)
    elig = np.asarray(P["elig"], bool)
    cond, C, vq = V67.conditions(P)
    G = V67.gate_set(cond)
    cc, oc = V66.dvw_market(P)
    return pct, elig, G, cc, oc


def stage_selftest(P, t0):
    pct, elig, G, cc, oc = build(P)
    m0 = P["m_start"]
    V65.assert_HOLDOUT_GUARD()
    K = kernel(P, pct, elig, cc, oc)
    S6 = G["S6"]

    # [FAST]
    zeros = np.zeros((P["T"], P["n"]), float)
    s = V66.run_cell(P, S6, pct, elig, cc, oc, zeros)
    assert FK.Kernel(P, pct, elig, cc, oc).net(S6) == s["net"], "[FAST] not bit-identical"
    print(f"    [FAST] the kernel is bit-identical to D366's functions ({s['net']:+.6f})")

    # [OWN] -- the observed book's own ten, and the check against D369's stored set
    obs_net, obs_cols = one_draw(P, K, S6, elig)
    syms = sorted(P["symbols"][c] for c in obs_cols)
    d367 = sorted(V67.removed_names(P)[0])
    assert len(obs_cols) == TOPN and len(set(obs_cols)) == TOPN, "[OWN] not ten distinct names"
    print(f"    [OWN] the observed book's own top ten: {', '.join(syms)}")
    print(f"          D367's stored ten:               {', '.join(d367)}   -- overlap "
          f"{len(set(syms) & set(d367))}/10")

    # [HEDGE] -- rebuilt on the reduced universe, and the size of that change
    pct2, e2, cc2, oc2 = reduced_pieces(P, obs_cols, elig)
    man = V66.dvw_market(dict(P, elig=e2))[0]
    assert np.array_equal(np.nan_to_num(cc2, nan=-9), np.nan_to_num(man, nan=-9)), "[HEDGE] recomputation"
    full_hedge_net = kernel(P, pct2, e2, cc, oc).net(S6)       # D367/D369's convention: full-universe hedge
    print(f"    [HEDGE] rebuilt on the reduced universe it equals an independent recomputation; the book is "
          f"{obs_net:+.4f} against {full_hedge_net:+.4f} under D367/D369's full-universe hedge -- the "
          f"inconsistency was worth {obs_net-full_hedge_net:+.4f} bp/bar")
    d69 = json.loads((OUT / "d369_report.json").read_text())
    print(f"          D369's stored reduced observed (its ten, full-universe hedge): "
          f"{d69['observed']['REDUCED']:+.4f}")

    # [RANK]
    assert np.all(np.isnan(pct2[:, obs_cols])), "[RANK] a removed name kept a percentile"
    moved = int((np.nan_to_num(pct2, nan=-1) != np.nan_to_num(pct, nan=-1)).any(axis=0).sum())
    assert moved > TOPN, f"[RANK] only {moved} names moved"
    print(f"    [RANK] removal re-ranks: the ten carry no percentile and {moved} names' ranks move")

    # [SHARE] and that draws differ from one another
    rng = np.random.default_rng([SEED, STUDY, 1])
    seen = []
    for i in range(4):
        k = int(rng.integers(1, P["T"] - m0))
        g = V67.rotate(S6, m0, k)
        assert g[m0:].sum() == S6[m0:].sum(), "[SHARE] on-share"
        assert V67.circ_runs(g[m0:]) == V67.circ_runs(S6[m0:]), "[SHARE] circular runs"
        n, cols = one_draw(P, K, g, elig)
        ov = len(set(cols) & set(obs_cols))
        seen.append((k, n, ov, [P["symbols"][c] for c in cols[:4]]))
        print(f"    draw shift {k:>5}: net {n:+7.3f}, its own ten overlap the observed's on {ov}/10 "
              f"({', '.join(seen[-1][3])}, ...)")
    assert len({tuple(sorted(s[3])) for s in seen}) > 1, "[OWN] every draw picked the same names"
    print(f"    [SHARE] rotations preserve on-share and the circular run-length multiset; the removed sets "
          f"genuinely differ across draws")

    # timing
    t = time.time()
    for _ in range(3):
        one_draw(P, K, V67.rotate(S6, m0, 1234), elig)
    per_draw = (time.time() - t) / 3
    print(f"    [COST] {per_draw*1000:.0f} ms per draw -> 2,000 draws is {per_draw*2000/60:.1f} min serial, "
          f"{per_draw*2000/60/8:.1f} min on 8 processes")

    # [6]
    broke = []
    try:
        assert len(set(obs_cols) & set(V67.removed_names(P)[1])) == 0
    except AssertionError:
        broke.append("OWN/overlap")
    try:
        assert np.array_equal(np.nan_to_num(cc2, nan=-9), np.nan_to_num(cc, nan=-9))
    except AssertionError:
        broke.append("HEDGE/reduced differs from full")
    try:
        assert np.all(np.isnan(pct[:, obs_cols]))
    except AssertionError:
        broke.append("RANK/full grid still ranks them")
    try:
        g = V67.rotate(S6, m0, 7).copy()
        g[m0] = ~g[m0]
        assert g[m0:].sum() == S6[m0:].sum()
    except AssertionError:
        broke.append("SHARE/on-share")
    assert len(broke) == 4, f"[6] only {broke} raised"
    print(f"    [6] each of {', '.join(broke)} raises on a deliberately broken input")
    print(f"\nOK  selftest passes  ({el(t0)})  {PREP.rss_line()}")


def stage_sym(P, draws, part, nparts, t0):
    pct, elig, G, cc, oc = build(P)
    m0 = P["m_start"]
    K = kernel(P, pct, elig, cc, oc)
    S6 = G["S6"]
    mine = [i for i in range(draws) if i % nparts == part]
    idx, vals, ovs = [], [], []
    for j, i in enumerate(mine):
        rng = np.random.default_rng([SEED, STUDY, 2, i])
        k = int(rng.integers(1, P["T"] - m0))
        n, cols = one_draw(P, K, V67.rotate(S6, m0, k), elig)
        idx.append(i)
        vals.append(float(n))
        ovs.append(int(len(set(cols) & set(V67.removed_names(P)[1]))))
        if (j + 1) % 25 == 0:
            print(f"    SYM p{part}: {j+1}/{len(mine)} ({el(t0)})", flush=True)
    p = OUT / f"d370_SYM_p{part}of{nparts}.json"
    p.write_text(json.dumps(dict(study=STUDY, part=part, nparts=nparts, draws=draws,
                                 idx=idx, vals=vals, overlap=ovs), indent=1))
    print(f"  wrote {p.name}: {len(vals)} draws  ({el(t0)})  {PREP.rss_line()}", flush=True)


def stage_report(P, t0):
    pct, elig, G, cc, oc = build(P)
    K = kernel(P, pct, elig, cc, oc)
    S6 = G["S6"]
    obs_net, obs_cols = one_draw(P, K, S6, elig)
    full = K.net(S6)

    parts = sorted(OUT.glob("d370_SYM_p*of*.json"))
    assert parts, "run --sym first"
    idx, vals, ovs = [], [], []
    for p in parts:
        j = json.loads(p.read_text())
        idx += j["idx"]
        vals += j["vals"]
        ovs += j["overlap"]
    assert sorted(idx) == list(range(len(idx))), "[PART] draw indices are not a partition"
    S = V69.summarise(vals, obs_net, seed=1)

    d69 = json.loads((OUT / "d369_report.json").read_text())
    A = d69["arms"]["GATEROT_REDUCED"]
    drops = [full - v for v in vals]                      # each draw's own drop is not available; see note

    print("\n" + "=" * 150)
    print("D370 -- the symmetric top-ten removal: every draw loses its OWN winners")
    print("=" * 150)
    print(f"  observed, full universe                 {full:+8.4f}")
    print(f"  observed, minus ITS OWN ten             {obs_net:+8.4f}   (drop {full-obs_net:+.4f})")
    print(f"  the ten: {', '.join(sorted(P['symbols'][c] for c in obs_cols))}")
    print(f"\n  {'test':<34}{'draws':>7}{'p50':>9}{'p95':>9}{'p95 SE':>9}{'observed':>10}{'margin':>9}"
          f"{'in SE':>7}{'beat':>7}   verdict")
    print(f"  {'SYMMETRIC (own ten per draw)':<34}{S['draws']:7,}{S['p50']:+9.3f}{S['p95']:+9.3f}"
          f"{S['p95_se']:9.3f}{S['observed']:+10.3f}{S['margin']:+9.3f}{S['margin_in_se']:7.1f}"
          f"{S['draws_beating_observed']:7,}   {S['verdict']}")
    print(f"  {'ASYMMETRIC (D369, the SAME ten)':<34}{A['draws']:7,}{A['p50']:+9.3f}{A['p95']:+9.3f}"
          f"{A['p95_se']:9.3f}{A['observed']:+10.3f}{A['margin']:+9.3f}{A['margin_in_se']:7.1f}"
          f"{A['draws_beating_observed']:7,}   {A['verdict']}")
    print(f"\n  overlap between a draw's own ten and the observed book's ten: median {np.median(ovs):.0f}/10, "
          f"mean {np.mean(ovs):.1f}, range {min(ovs)}-{max(ovs)}")

    q = {}
    q["Q1"] = S["verdict"] == "CLEARS"
    q["Q2"] = bool(S["p50"] < A["p50"])
    q["Q3"] = bool(S["verdict"] == "CLEARS" and A["verdict"] == "FAILS")
    q["Q5"] = bool(np.median(ovs) < 6)
    q["Q6"] = bool(S["p95_se"] < 0.10)
    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) the observed minus its own ten clears the SYM p95 by >2 SE: {v_(q['Q1'])} -- "
          f"{S['margin']:+.3f} = {S['margin_in_se']:.1f} SE -> {S['verdict']}")
    print(f"  Q2 the SYM p50 is below the ASYM p50: {v_(q['Q2'])} -- {S['p50']:+.3f} vs {A['p50']:+.3f}")
    print(f"  Q3 (AGAINST) the symmetric test REVERSES D369's verdict: {v_(q['Q3'])} -- SYM {S['verdict']}, "
          f"ASYM {A['verdict']}")
    print(f"  Q4 reported as the drop comparison above (each draw's own full-universe net is not stored; the "
          f"median SYM level is the comparable quantity)")
    print(f"  Q5 the median overlap is fewer than 6 names: {v_(q['Q5'])} -- median {np.median(ovs):.0f}/10")
    print(f"  Q6 the SYM p95 SE is below 0.10: {v_(q['Q6'])} -- {S['p95_se']:.4f}")

    out = dict(study=STUDY, observed_full=full, observed_reduced=obs_net,
               own_ten=[P["symbols"][c] for c in obs_cols], symmetric=S, asymmetric=A,
               overlap=dict(median=float(np.median(ovs)), mean=float(np.mean(ovs)),
                            min=int(min(ovs)), max=int(max(ovs))),
               predictions=q,
               note="D370: every draw removes its OWN top ten; hedge rebuilt on the reduced universe; the "
                    "gate's index is NOT reduced.")
    (OUT / "d370_report.json").write_text(json.dumps(V65.clean(out), indent=1))
    print(f"\nwrote d370_report.json  ({el(t0)})  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sym", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--nparts", type=int, default=1)
    a = ap.parse_args()
    t0 = time.time()
    print(f"D370  symmetric top-ten removal", flush=True)
    P = PREP.prep(need_grids=False, verbose=False)
    if a.selftest:
        stage_selftest(P, t0)
    elif a.sym:
        stage_sym(P, a.draws, a.part, a.nparts, t0)
    elif a.report:
        stage_report(P, t0)
    else:
        ap.error("one of --selftest, --sym, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
