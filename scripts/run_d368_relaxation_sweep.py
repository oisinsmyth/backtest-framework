"""D368 -- the relaxation sweep: is the gate a knife-edge at the high, or the end of a smooth curve?

    uv run python scripts/run_d368_relaxation_sweep.py --selftest
    uv run python scripts/run_d368_relaxation_sweep.py --sweep --draws 200
    uv run python scripts/run_d368_relaxation_sweep.py --report

ONE PARAMETER, SWEPT, NOTHING TUNED. C9 becomes "the index closes within d% of its trailing 252-bar high" for
d = 0, 0.5, 1, 2, 5, 10. d = 0 recovers D367's C9 exactly and is the IDENTITY CHECK, not a data point earned.

THE EXIT RANK IS COLLAPSED TO ONE VALUE, AND THAT REMOVES A CONFOUND RATHER THAN ADDING A PARAMETER. D366's exit
depends on gate state (80 open, 90 shut), so raising d would loosen the exit on more bars at the same time as it
opened the gate on more. D367 measured that split to be dead. The primary here is a single exit rank of 90; the
frozen 80/90 is reported beside at every d, with the count of bars on which the open-state rank actually BINDS.

THREE FAMILIES, BECAUSE THE REDUNDANCY BREAKS AS d GROWS. At d = 0 an index at its high necessarily sits above its
moving averages, is positive over 63 and 21 bars, is not in a crash and is broad -- which is why six of D366's
nine conditions cost nothing. At d = 5 none of that is entailed. [IMPLY] measures where each stops being implied.
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

import run_d367_gate_deconstruction as V67    # noqa: E402  -- conditions, circ_runs, rotate, summarise
import run_d366_gated_buffer as V66           # noqa: E402  -- the frozen construction
import run_d365_momentum_buffer as V65        # noqa: E402

PREP, V58, V50 = V66.PREP, V66.V58, V66.V50
STUDY, SEED, ANN = 368, V66.SEED, 252.0
DS = (0.0, 0.5, 1.0, 2.0, 5.0, 10.0)
FAMILIES = ("A", "B", "C")
FAM_TEXT = {"A": "C9(d) alone", "B": "C9(d) + C4", "C": "C9(d) + all eight others"}
EXIT_ONE = 90                                  # the primary: one exit rank, gate is purely an entry condition
D367_GATES = REPO / "data" / "d367_gates.json"


def el(t0):
    return f"{time.time() - t0:.0f}s"


def key(fam, d):
    return f"{fam}@{d:g}"


# ================================================================== the relaxed condition
def c9_of(P, d):
    """C9(d): idx[t-1] >= (1 - d/100) * max(idx[t-253:t-1]). d=0 is D367's C9 exactly."""
    T, m0 = P["T"], P["m_start"]
    m_f = np.asarray(P["m_f"], float)
    idx = np.cumprod(1.0 + np.where(np.isfinite(m_f), m_f, 0.0))
    out = np.zeros(T, bool)
    thr = 1.0 - d / 100.0
    for t in range(m0 + 260, T):
        out[t] = idx[t - 1] >= thr * np.max(idx[t - 253:t - 1])
    return out


def gates_of(P, cond):
    """The 18 gates: three families across six d."""
    G, c9 = {}, {}
    others = [c for c in V67.COND if c not in ("C9", "C4")]
    for d in DS:
        g9 = c9_of(P, d)
        c9[d] = g9
        G[key("A", d)] = g9.copy()
        G[key("B", d)] = g9 & cond["C4"]
        gc = g9 & cond["C4"]
        for c in others:
            gc = gc & cond[c]
        G[key("C", d)] = gc
    return G, c9


# ================================================================== the book, with a single exit rank
def run_at(P, gate, pct, elig, cc, oc, zeros, exit_one=True):
    lo_open = EXIT_ONE if exit_one else V66.LO_OPEN
    hold = V66.hold_of(pct, elig, gate, P["m_start"], cap=V66.CAP, lo_open=lo_open, lo_shut=V66.LO_SHUT)
    v, mask, ent, cn = V66.book_of(P, hold, cc, oc)
    c = V66.costs(P, hold, zeros)
    s = V66.stats(P, v, mask, c["total"])
    s.update(members=float(hold.sum(axis=1)[mask].mean()), cost_parts=c, hold=hold, v=v, mask=mask, ent=ent, cn=cn)
    return s


def binds_count(P, gate, pct, elig):
    """Bars on which the OPEN-state exit rank actually binds: gate open, name held, rank in (80, 90].
    ~0 at d=0 and not at d=10; this is why the two exit conventions can diverge as d grows."""
    hold = V66.hold_of(pct, elig, gate, P["m_start"], cap=V66.CAP, lo_open=V66.LO_OPEN, lo_shut=V66.LO_SHUT)
    band = (pct > V66.LO_OPEN) & (pct <= V66.LO_SHUT)
    return int((hold & band & gate[:, None]).sum())


# ================================================================== stages
def prepare(P):
    pct = V58.pct_of(P, V65.SCORE)
    elig = np.asarray(P["elig"], bool)
    cond, C, vq = V67.conditions(P)
    G, c9 = gates_of(P, cond)
    cc, oc = V66.dvw_market(P)
    zeros = np.zeros((P["T"], P["n"]), float)
    return pct, elig, cond, G, c9, cc, oc, zeros


def stage_selftest(P, t0):
    pct, elig, cond, G, c9, cc, oc, zeros = prepare(P)
    m0 = P["m_start"]
    V65.assert_HOLDOUT_GUARD()

    # [ID] -- d=0 under the FROZEN exit must be D367's stored C9
    assert D367_GATES.exists(), "run D367 --gates first"
    d67 = json.loads(D367_GATES.read_text())["gates"]["C9"]
    assert np.array_equal(c9[0.0], cond["C9"]), "[ID] C9(0) is not D367's C9"
    s0 = run_at(P, G[key("A", 0.0)], pct, elig, cc, oc, zeros, exit_one=False)
    for k, got, want in (("net", s0["net"], d67["observed"]["net"]),
                         ("gross", s0["gross"], d67["observed"]["gross"]),
                         ("sharpe", s0["sharpe"], d67["observed"]["sharpe"])):
        assert abs(float(got) - float(want)) < 1e-9, f"[ID] {k}: {got} vs D367's stored {want}"
    assert s0["cost_parts"]["trades"] == d67["observed"]["trades"], "[ID] trades"
    print(f"    [ID] C9(0) under the frozen 80/90 exit reproduces D367's STORED C9 to <1e-9: net {s0['net']:+.4f} "
          f"gross {s0['gross']:+.4f} sharpe {s0['sharpe']:.4f} trades {s0['cost_parts']['trades']}")

    # [MONO]
    shares = {}
    for i, d in enumerate(DS):
        shares[d] = float(c9[d][m0:].mean())
        if i:
            prev = DS[i - 1]
            assert np.all(c9[prev][m0:] <= c9[d][m0:]), f"[MONO] C9({d}) is not a superset of C9({prev})"
            assert shares[d] > shares[prev], f"[MONO] on-share not increasing at d={d}"
    print(f"    [MONO] C9(d) is a strict superset of C9(d') for every d>d'; on-share rises "
          + " -> ".join(f"{100*shares[d]:.1f}%" for d in DS))

    # [IMPLY] -- where each 'redundant' condition stops being implied
    others = [c for c in V67.COND if c not in ("C9", "C4")]
    first_bites = {}
    for c in others:
        first_bites[c] = None
        for d in DS:
            extra = int((c9[d][m0:] & ~cond[c][m0:]).sum())
            if extra > 0:
                first_bites[c] = (d, extra)
                break
    at0 = [c for c in others if int((c9[0.0][m0:] & ~cond[c][m0:]).sum()) == 0]
    for c in at0:                                     # byte-identical books at d=0
        a = run_at(P, G[key("A", 0.0)], pct, elig, cc, oc, zeros)
        b = run_at(P, c9[0.0] & cond[c], pct, elig, cc, oc, zeros)
        assert np.array_equal(a["hold"], b["hold"]), f"[IMPLY] {c} claimed implied but changes the book"
    print(f"    [IMPLY] at d=0, {len(at0)} of {len(others)} conditions are entailed by the high and give a "
          f"BYTE-IDENTICAL book ({', '.join(at0)}); each first bites at: "
          + ", ".join(f"{c} d={first_bites[c][0]:g} ({first_bites[c][1]} bars)" if first_bites[c] else f"{c} never"
                      for c in others))

    # [EXIT]
    print(f"    [EXIT] {'d':>5} {'open%':>7} {'binds':>7} {'net(one)':>9} {'net(80/90)':>11} {'diff':>7}")
    for d in DS:
        g = G[key("A", d)]
        a = run_at(P, g, pct, elig, cc, oc, zeros, exit_one=True)
        b = run_at(P, g, pct, elig, cc, oc, zeros, exit_one=False)
        print(f"           {d:5g} {100*shares[d]:6.1f}% {binds_count(P, g, pct, elig):7,} {a['net']:+9.2f} "
              f"{b['net']:+11.2f} {a['net']-b['net']:+7.2f}")

    # [SHARE] / [SHARED]
    rng = np.random.default_rng([SEED, STUDY, 1])
    k = int(rng.integers(1, P["T"] - m0))
    for nm in (key("A", 0.0), key("A", 5.0), key("C", 10.0)):
        r = V67.rotate(G[nm], m0, k)
        assert r[m0:].sum() == G[nm][m0:].sum(), f"[SHARE] {nm} on-share"
        assert V67.circ_runs(G[nm][m0:]) == V67.circ_runs(r[m0:]), f"[SHARE] {nm} circular runs"
        assert not np.array_equal(r, G[nm]), f"[SHARE] {nm} returned the observed gate"
    rot = {nm: V67.rotate(g, m0, k) for nm, g in G.items()}
    for nm in list(G)[:4]:
        assert np.array_equal(rot[nm], V67.rotate(G[nm], m0, k)), f"[SHARED] {nm}"
    print(f"    [SHARE] a shift of {k} preserves on-share and the circular run-length multiset on the extremes of "
          f"the sweep; [SHARED] all {len(G)} gates recompute from that one shift")

    # [S]
    rng2 = np.random.default_rng([SEED, STUDY, 9])
    s = run_at(P, G[key("A", 2.0)], pct, elig, cc, oc, zeros)
    hold = s["hold"]
    cand = np.flatnonzero(hold.sum(axis=1) > 3)
    tb = int(rng2.choice(cand[cand > m0 + 1200]))
    ib = int(rng2.choice(np.flatnonzero(hold[tb] & ~s["ent"][tb])))
    r1p = np.asarray(P["r1T"], float).copy()
    r1p[tb, ib] += 50e-4
    v2, _m, _e, _c = V66.book_of(dict(P, r1T=r1p), hold, cc, oc)
    nh = int(s["cn"][tb])
    dmv = v2[tb] - s["v"][tb]
    other = np.ones(P["T"], bool)
    other[tb] = False
    assert abs(dmv - 50.0 / nh) < 1e-6, f"[S] moved {dmv:.4f}, expected {50.0/nh:.4f}"
    assert np.array_equal(np.nan_to_num(v2[other]), np.nan_to_num(s["v"][other])), "[S] leaked"
    print(f"    [S] +50 bp on {P['symbols'][ib]} {P['dates'][tb]} moves the bar by {dmv:.4f} = 50 / {nh} held, "
          f"and no other bar")

    # [6]
    broke = []
    try:
        assert np.all(c9[5.0][m0:] <= c9[1.0][m0:])
    except AssertionError:
        broke.append("MONO/superset")
    try:
        a = run_at(P, G[key("A", 0.0)], pct, elig, cc, oc, zeros)
        b = run_at(P, c9[0.0] & cond["C4"], pct, elig, cc, oc, zeros)
        assert np.array_equal(a["hold"], b["hold"])
    except AssertionError:
        broke.append("IMPLY/C4 is not entailed")
    try:
        r = V67.rotate(G[key("A", 0.0)], m0, k)
        r[m0] = ~r[m0]
        assert r[m0:].sum() == G[key("A", 0.0)][m0:].sum()
    except AssertionError:
        broke.append("SHARE/on-share")
    try:
        assert np.array_equal(V67.rotate(G[key("A", 0.0)], m0, k), V67.rotate(G[key("A", 0.0)], m0, k + 1))
    except AssertionError:
        broke.append("SHARED/one shift")
    try:
        assert abs(dmv - 50.0 / (nh + 1)) < 1e-6
    except AssertionError:
        broke.append("S")
    assert len(broke) == 5, f"[6] only {broke} raised"
    print(f"    [6] each of {', '.join(broke)} raises on a deliberately broken input")
    print(f"\nOK  selftest passes  ({el(t0)})  {PREP.rss_line()}")


def stage_sweep(P, draws, t0):
    pct, elig, cond, G, c9, cc, oc, zeros = prepare(P)
    m0 = P["m_start"]
    names = list(G)
    obs = {}
    for nm in names:
        a = run_at(P, G[nm], pct, elig, cc, oc, zeros, exit_one=True)
        b = run_at(P, G[nm], pct, elig, cc, oc, zeros, exit_one=False)
        obs[nm] = dict(net=a["net"], gross=a["gross"], sharpe=a["sharpe"], maxdd=a["maxdd"],
                       trades=a["cost_parts"]["trades"], members=a["members"], era1=a["era1"], era2=a["era2"],
                       open_share=float(G[nm][m0:].mean()), open_bars=int(G[nm][m0:].sum()),
                       net_frozen_exit=b["net"], sharpe_frozen_exit=b["sharpe"],
                       binds=binds_count(P, G[nm], pct, elig))
    print(f"    observed {len(names)} gates ({el(t0)})")

    per = {nm: [] for nm in names}
    rows = []
    rng = np.random.default_rng([SEED, STUDY, 3])
    for d_ in range(draws):
        k = int(rng.integers(1, P["T"] - m0))
        row = {}
        for nm in names:
            row[nm] = run_at(P, V67.rotate(G[nm], m0, k), pct, elig, cc, oc, zeros, exit_one=True)["net"]
            per[nm].append(row[nm])
        rows.append(row)
        if (d_ + 1) % 10 == 0:
            print(f"    draws {d_+1}/{draws} ({el(t0)})  {PREP.rss_line()}")

    p50 = {nm: float(np.median(per[nm])) for nm in names}
    out_g = {}
    for nm in names:
        out_g[nm] = dict(observed=obs[nm], rotation=V67.summarise(per[nm], obs[nm]["net"]),
                         rot_p50=p50[nm], timing_premium=obs[nm]["net"] - p50[nm])
    smax = [max(r[nm] - p50[nm] for nm in names) for r in rows]
    best = max(names, key=lambda k2: out_g[k2]["timing_premium"])

    out = dict(study=STUDY, ds=list(DS), families=FAM_TEXT, draws=draws, gates=out_g,
               shared_offset_max=V67.summarise(smax, out_g[best]["timing_premium"]), best_gate=best,
               exit_primary=EXIT_ONE,
               note="D368: one parameter swept. d=0 recovers D367's C9 and is the identity check. Primary uses a "
                    "SINGLE exit rank so the gate is purely an entry condition; the frozen 80/90 is beside.")
    p = REPO / "data" / "d368_sweep.json"
    p.write_text(json.dumps(V65.clean(out), indent=1))
    print(f"\n  wrote {p.name}: best {best} premium {out_g[best]['timing_premium']:+.2f}, shared-offset max p95 "
          f"{out['shared_offset_max']['p95']:+.2f}  ({el(t0)})  {PREP.rss_line()}")


def stage_report(P, t0):
    p = REPO / "data" / "d368_sweep.json"
    assert p.exists(), "run --sweep first"
    J = json.loads(p.read_text())
    gs = J["gates"]
    print("\n" + "=" * 150)
    print("D368 -- the relaxation sweep: is the gate a knife-edge at the high, or the end of a smooth curve?")
    print("=" * 150)
    for fam in FAMILIES:
        print(f"\n  FAMILY {fam} -- {FAM_TEXT[fam]}")
        print(f"  {'d%':>6} {'open%':>7} {'gross':>7} {'net':>7} {'rot p50':>8} {'PREMIUM':>8} {'rot p95':>8} "
              f"{'rank%':>6} {'beat':>5} {'clears':>7} {'trades':>7} {'Sharpe':>7} {'net 80/90':>10} {'binds':>7}")
        for d in DS:
            g = gs[key(fam, d)]
            o, r = g["observed"], g["rotation"]
            print(f"  {d:6g} {100*o['open_share']:6.1f}% {o['gross']:+7.2f} {o['net']:+7.2f} {g['rot_p50']:+8.2f} "
                  f"{g['timing_premium']:+8.2f} {r['p95']:+8.2f} {r['pct_rank']:5.1f}% {r['draws_beating_observed']:5d} "
                  f"{'YES' if r['above_p95'] else 'no':>7} {o['trades']:7d} {o['sharpe']:+7.3f} "
                  f"{o['net_frozen_exit']:+10.2f} {o['binds']:7,}")

    A = [gs[key("A", d)] for d in DS]
    prem = [g["timing_premium"] for g in A]
    clears = [g["rotation"]["above_p95"] for g in A]
    inv = sum(1 for i in range(1, len(prem)) if prem[i] > prem[i - 1])
    sm = J["shared_offset_max"]
    print(f"\n  family A premium curve: " + " -> ".join(f"{x:+.2f}" for x in prem)
          + f"   ({sum(clears)} of 6 clear their own p95, {inv} inversion(s))")
    print(f"  MULTIPLICITY -- shared-offset max over all {len(gs)} gates: p50 {sm['p50']:+.2f} p95 {sm['p95']:+.2f} "
          f"max {sm['max']:+.2f}; best gate {J['best_gate']} premium "
          f"{gs[J['best_gate']]['timing_premium']:+.2f}, {sm['draws_beating_observed']} draws beat it")

    q = {}
    q["Q1"] = bool(sum(clears) >= 4)
    q["Q2"] = bool(inv <= 1)
    q["Q3"] = bool(prem[1] < 0.5 * prem[0])
    d0 = gs[key("C", 0.0)]["timing_premium"] - gs[key("A", 0.0)]["timing_premium"]
    d5 = gs[key("C", 5.0)]["timing_premium"] - gs[key("A", 5.0)]["timing_premium"]
    q["Q4"] = bool(d5 > 1.23)
    q["Q5"] = bool(gs[J["best_gate"]]["timing_premium"] > sm["p95"])
    cap = [(d, gs[key("A", d)]) for d in DS if gs[key("A", d)]["observed"]["open_share"] >= 0.20]
    q["Q6"] = bool(any(g["rotation"]["above_p95"] for _d, g in cap))
    q["Q7"] = all(gs[key("A", d)]["timing_premium"] > gs[key("B", d)]["timing_premium"] - 1.23 for d in DS)
    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) at least 4 of 6 d clear their own GATE-ROT p95: {v_(q['Q1'])} -- {sum(clears)} of 6 "
          f"(" + ", ".join(f"d={d:g}:{'Y' if c else 'n'}" for d, c in zip(DS, clears)) + ")")
    print(f"  Q2 the premium is non-increasing in d, at most one inversion: {v_(q['Q2'])} -- {inv} inversion(s)")
    print(f"  Q3 (AGAINST) premium(d=0.5) < half of premium(d=0): {v_(q['Q3'])} -- {prem[1]:+.2f} vs half of "
          f"{prem[0]:+.2f} = {0.5*prem[0]:+.2f}")
    print(f"  Q4 the redundancy breaks -- family C beats A by more than 1.23 at d=5: {v_(q['Q4'])} -- "
          f"{d5:+.2f} at d=5 against {d0:+.2f} at d=0")
    print(f"  Q5 the best of 18 is above the shared-offset p95: {v_(q['Q5'])} -- "
          f"{gs[J['best_gate']]['timing_premium']:+.2f} vs {sm['p95']:+.2f}")
    print(f"  Q6 (CAPACITY) some d with on-share >= 20% clears its own p95: {v_(q['Q6'])} -- "
          + (", ".join(f"d={d:g} open {100*g['observed']['open_share']:.0f}% "
                       f"{'clears' if g['rotation']['above_p95'] else 'does not'}" for d, g in cap)
             if cap else "no d reaches 20% on-share"))
    print(f"  Q7 C4's contribution does not grow with d: {v_(q['Q7'])} -- B-A by d: "
          + ", ".join(f"{gs[key('B',d)]['timing_premium']-gs[key('A',d)]['timing_premium']:+.2f}" for d in DS))

    out = dict(study=STUDY, predictions=q, premium_curve=prem, clears=clears, sweep=J)
    o = REPO / "data" / "d368_report.json"
    o.write_text(json.dumps(V65.clean(out), indent=1))
    print(f"\nwrote {o.name}  ({el(t0)})  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    print("D368  the relaxation sweep")
    P = PREP.prep(need_grids=False)
    if a.selftest:
        stage_selftest(P, t0)
    elif a.sweep:
        stage_sweep(P, a.draws, t0)
    elif a.report:
        stage_report(P, t0)
    else:
        ap.error("one of --selftest, --sweep, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
