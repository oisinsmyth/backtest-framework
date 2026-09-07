"""D369 -- the null precision rerun: 10,000 draws on the settings we would actually trade.

    uv run python scripts/run_d369_null_precision.py --selftest
    uv run python scripts/run_d369_null_precision.py --arm GATEROT_S6 --draws 10000 --part 0 --nparts 8
    uv run python scripts/run_d369_null_precision.py --report

THE COMMITMENT (pre-registered, 8479558). The verdicts here SUPERSEDE the 200-draw ones in D366/D367/D368
whichever way they fall. The draw count was fixed before running and is not revisited.

AND THE CATEGORY THAT EXISTS SO A NARROW RESULT CANNOT BE WRITTEN UP AS A CLEAN ONE. Every p95 carries a
bootstrap standard error, and a margin under TWO of those SEs is reported UNRESOLVED -- not a pass, not a fail.

Draws are STRIDED across worker processes (draw i goes to part i % nparts), never sliced, so every part sees the
same mix of shifts and the union is exactly the draw set. [PART] asserts that.
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
import run_d367_gate_deconstruction as V67    # noqa: E402
import run_d366_gated_buffer as V66           # noqa: E402
import run_d365_momentum_buffer as V65        # noqa: E402

PREP, V58 = FK.PREP, FK.V58
STUDY, SEED = 369, V66.SEED
EXIT_ONE = 90
ARMS = ("GATEROT_S6", "GATEROT_C9", "APRIME_S6", "APRIME_C9", "GATEROT_REDUCED", "MULTI", "C")
MULTI_GATES = list(V67.COND) + ["S6"]
OUT = REPO / "data"


def el(t0):
    return f"{time.time() - t0:.0f}s"


def build(P):
    pct = V58.pct_of(P, V65.SCORE)
    elig = np.asarray(P["elig"], bool)
    cond, C, vq = V67.conditions(P)
    G = V67.gate_set(cond)
    cc, oc = V66.dvw_market(P)
    return pct, elig, cond, G, cc, oc


def kernel_for(P, pct, elig, cc, oc):
    """The primary construction: a SINGLE exit rank of 90, so the gate is purely an entry condition."""
    K = FK.Kernel(P, pct, elig, cc, oc)
    K.keep_open = K.keep_shut                  # one exit rank; D367 measured the 80/90 split at 0.02 bp/bar
    return K


def boot_se(x, q=0.95, n_boot=1000, seed=0):
    """The p95's OWN standard error, by resampling the draw set. Reported beside every p95, because a margin
    smaller than this is not a verdict."""
    x = np.asarray(x, float)
    rng = np.random.default_rng([SEED, STUDY, 77, seed])
    idx = rng.integers(0, x.size, size=(n_boot, x.size))
    return float(np.std(np.quantile(x[idx], q, axis=1), ddof=1))


def summarise(vals, obs, seed=0):
    x = np.asarray([v for v in vals if np.isfinite(v)], float)
    p95 = float(np.quantile(x, 0.95))
    se = boot_se(x, seed=seed)
    margin = float(obs - p95)
    return dict(draws=int(x.size), p50=float(np.median(x)), p95=p95, p95_se=se,
                max=float(np.max(x)), min=float(np.min(x)), observed=float(obs), margin=margin,
                margin_in_se=(margin / se if se > 0 else None),
                verdict=("UNRESOLVED" if abs(margin) < 2 * se else ("CLEARS" if margin > 0 else "FAILS")),
                draws_beating_observed=int((x >= obs).sum()), pct_rank=float(100.0 * (x < obs).mean()))


# ================================================================== arms
def arm_draws(P, K, G, arm, pct, elig, cc, oc, draws, part, nparts, t0):
    """Returns (list of (draw_index, value)) for this part's strided share of the draw set."""
    m0 = P["m_start"]
    mine = [i for i in range(draws) if i % nparts == part]
    out = []
    if arm in ("GATEROT_S6", "GATEROT_C9", "GATEROT_REDUCED"):
        gate = G["S6"] if arm != "GATEROT_C9" else G["C9"]
        for j, i in enumerate(mine):
            rng = np.random.default_rng([SEED, STUDY, 1, i])          # per-draw seed: order-independent
            k = int(rng.integers(1, P["T"] - m0))
            out.append((i, K.net(V67.rotate(gate, m0, k))))
            if (j + 1) % 200 == 0:
                print(f"    {arm} p{part}: {j+1}/{len(mine)} ({el(t0)})", flush=True)
    elif arm in ("APRIME_S6", "APRIME_C9"):
        gate = G["S6"] if arm == "APRIME_S6" else G["C9"]
        for j, i in enumerate(mine):
            rng = np.random.default_rng([SEED, STUDY, 2, i])
            r = V65.aprime_draw(pct, elig, rng)
            K2 = kernel_for(P, r, elig, cc, oc)
            out.append((i, K2.net(gate)))
            if (j + 1) % 100 == 0:
                print(f"    {arm} p{part}: {j+1}/{len(mine)} ({el(t0)})", flush=True)
    elif arm == "MULTI":
        p50 = json.loads((OUT / "d369_multi_p50.json").read_text())["p50"]
        for j, i in enumerate(mine):
            rng = np.random.default_rng([SEED, STUDY, 3, i])
            k = int(rng.integers(1, P["T"] - m0))
            best = max(K.net(V67.rotate(G[nm], m0, k)) - p50[nm] for nm in MULTI_GATES)
            out.append((i, best))
            if (j + 1) % 20 == 0:
                print(f"    {arm} p{part}: {j+1}/{len(mine)} ({el(t0)})", flush=True)
    else:                                                              # C -- random direction on the ledger
        f = K.net(G["S6"], want=("v",))
        b = f["v"][f["mask"]] - f["cost"]
        rng = np.random.default_rng([SEED, STUDY, 4, part])
        blk = max(1, len(mine) // 100)
        for c in range(blk):
            sg = rng.choice([-1.0, 1.0], size=(100, b.size))
            out.extend((-1, x) for x in (sg * b[None, :]).mean(axis=1).tolist())
    return out


def stage_arm(P, arm, draws, part, nparts, t0):
    pct, elig, cond, G, cc, oc = build(P)
    if arm == "GATEROT_REDUCED":
        syms, cols = V67.removed_names(P)
        elig = V67.reduced_elig(P, elig, cols)
        pct = V67.reduced_pct(P, cols)
    K = kernel_for(P, pct, elig, cc, oc)
    vals = arm_draws(P, K, G, arm, pct, elig, cc, oc, draws, part, nparts, t0)
    p = OUT / f"d369_{arm}_p{part}of{nparts}.json"
    p.write_text(json.dumps(dict(study=STUDY, arm=arm, part=part, nparts=nparts, draws=draws,
                                 idx=[i for i, _ in vals], vals=[float(v) for _, v in vals]), indent=1))
    print(f"  wrote {p.name}: {len(vals)} draws  ({el(t0)})  {PREP.rss_line()}", flush=True)


def stage_multi_p50(P, draws, t0):
    """MULTI needs each gate's own rotation median as its centre. Computed once, from a fixed 400-draw
    pre-pass with its own seed, and STORED -- so every worker centres on the same numbers."""
    pct, elig, cond, G, cc, oc = build(P)
    K = kernel_for(P, pct, elig, cc, oc)
    m0 = P["m_start"]
    p50 = {}
    for nm in MULTI_GATES:
        v = []
        for i in range(400):
            rng = np.random.default_rng([SEED, STUDY, 5, i])
            v.append(K.net(V67.rotate(G[nm], m0, int(rng.integers(1, P["T"] - m0)))))
        p50[nm] = float(np.median(v))
        print(f"    {nm}: rotation p50 {p50[nm]:+.3f} ({el(t0)})", flush=True)
    (OUT / "d369_multi_p50.json").write_text(json.dumps(dict(study=STUDY, draws=400, p50=p50), indent=1))
    print(f"  wrote d369_multi_p50.json  ({el(t0)})")


def stage_selftest(P, t0):
    pct, elig, cond, G, cc, oc = build(P)
    m0 = P["m_start"]
    V65.assert_HOLDOUT_GUARD()
    K = kernel_for(P, pct, elig, cc, oc)

    # [FAST] / [ID] -- bit-identity against D366's own functions, and against the STORED figures
    zeros = np.zeros((P["T"], P["n"]), float)
    for nm in ("S6", "C9"):
        s = V66.run_cell(P, G[nm], pct, elig, cc, oc, zeros)          # frozen 80/90 exit
        f = FK.Kernel(P, pct, elig, cc, oc).net(G[nm], want=("v",))
        assert f["net"] == s["net"], f"[FAST] {nm}: {f['net']} vs {s['net']}"
    d66 = json.loads((OUT / "d366_gated_buffer.json").read_text())["observed"]
    s6f = FK.Kernel(P, pct, elig, cc, oc).net(G["S6"], want=("v",))
    assert s6f["net"] == d66["net"], f"[ID] {s6f['net']} vs stored {d66['net']}"
    one = K.net(G["S6"], want=("v",))
    print(f"    [FAST] the kernel is bit-identical to D366's functions on S6 and C9 (zero delta), and S6 equals "
          f"the STORED d366_gated_buffer.json exactly: {s6f['net']:+.6f}")
    print(f"    [ID] under the single exit rank of {EXIT_ONE} the primary is {one['net']:+.4f} against the frozen "
          f"80/90's {s6f['net']:+.4f} -- a difference of {one['net']-s6f['net']:+.4f} bp/bar")

    # [SHARE]
    rng = np.random.default_rng([SEED, STUDY, 1, 0])
    k = int(rng.integers(1, P["T"] - m0))
    for nm in ("S6", "C9"):
        r = V67.rotate(G[nm], m0, k)
        assert r[m0:].sum() == G[nm][m0:].sum(), f"[SHARE] {nm}"
        assert V67.circ_runs(G[nm][m0:]) == V67.circ_runs(r[m0:]), f"[SHARE] {nm} runs"
    print(f"    [SHARE] shift {k} preserves on-share and the circular run-length multiset on both candidates")

    # [SHARED]
    rot = {nm: V67.rotate(G[nm], m0, k) for nm in MULTI_GATES}
    for nm in MULTI_GATES:
        assert np.array_equal(rot[nm], V67.rotate(G[nm], m0, k)), f"[SHARED] {nm}"
    print(f"    [SHARED] all {len(MULTI_GATES)} MULTI gates recompute from the single shift {k}")

    # [PART] -- the strided split is a partition, and a strided run equals a serial one EXACTLY
    nparts = 8
    union = sorted(i for p in range(nparts) for i in range(200) if i % nparts == p)
    assert union == list(range(200)), "[PART] the strided split is not a partition"
    serial = [K.net(V67.rotate(G["S6"], m0,
                               int(np.random.default_rng([SEED, STUDY, 1, i]).integers(1, P["T"] - m0))))
              for i in range(24)]
    strided = {}
    for p in range(4):
        for i in range(24):
            if i % 4 == p:
                strided[i] = K.net(V67.rotate(G["S6"], m0,
                                              int(np.random.default_rng([SEED, STUDY, 1, i])
                                                  .integers(1, P["T"] - m0))))
    assert [strided[i] for i in range(24)] == serial, "[PART] strided != serial"
    print(f"    [PART] draws stride across workers (i % nparts), the union is exactly the draw set, and a "
          f"4-way strided run reproduces the 24-draw serial run BIT-IDENTICALLY -- the per-draw seed is "
          f"[{SEED}, {STUDY}, arm, i], so a draw's value does not depend on which worker ran it")

    # [SE]
    v = [K.net(V67.rotate(G["S6"], m0, int(np.random.default_rng([SEED, STUDY, 1, i])
                                           .integers(1, P["T"] - m0)))) for i in range(200)]
    s200 = summarise(v, one["net"])
    print(f"    [SE] at 200 draws the p95 is {s200['p95']:+.3f} with a bootstrap SE of {s200['p95_se']:.3f}; "
          f"the observed margin is {s200['margin']:+.3f} = {s200['margin_in_se']:.1f} SE -> {s200['verdict']}. "
          f"THIS IS THE PROBLEM D368 FOUND, quantified.")

    # [MEM]
    print(f"    [MEM] one worker holds {PREP.rss_line()}; 8 workers is sized to leave at least 6 GB free")

    # [6]
    broke = []
    try:
        assert FK.Kernel(P, pct, elig, cc, oc).net(G["S6"]) == FK.Kernel(P, pct, elig, cc, oc).net(G["C9"])
    except AssertionError:
        broke.append("FAST/two gates differ")
    try:
        r = V67.rotate(G["S6"], m0, k).copy()
        r[m0] = ~r[m0]
        assert r[m0:].sum() == G["S6"][m0:].sum()
    except AssertionError:
        broke.append("SHARE/on-share")
    try:
        assert np.array_equal(V67.rotate(G["S6"], m0, k), V67.rotate(G["S6"], m0, k + 1))
    except AssertionError:
        broke.append("SHARED/one shift")
    try:
        bad = sorted(i for p in range(3) for i in range(200) if i % 4 == p)
        assert bad == list(range(200))
    except AssertionError:
        broke.append("PART/partition")
    assert len(broke) == 4, f"[6] only {broke} raised"
    print(f"    [6] each of {', '.join(broke)} raises on a deliberately broken input")
    print(f"\nOK  selftest passes  ({el(t0)})  {PREP.rss_line()}")


def stage_report(P, t0):
    pct, elig, cond, G, cc, oc = build(P)
    K = kernel_for(P, pct, elig, cc, oc)
    m0 = P["m_start"]
    obs = {"S6": K.net(G["S6"]), "C9": K.net(G["C9"])}
    syms, cols = V67.removed_names(P)
    Kr = kernel_for(P, V67.reduced_pct(P, cols), V67.reduced_elig(P, elig, cols), cc, oc)
    obs["REDUCED"] = Kr.net(G["S6"])
    obs_for = {"GATEROT_S6": obs["S6"], "GATEROT_C9": obs["C9"], "APRIME_S6": obs["S6"],
               "APRIME_C9": obs["C9"], "GATEROT_REDUCED": obs["REDUCED"], "C": obs["S6"]}

    R = {}
    for a in ARMS:
        parts = sorted(OUT.glob(f"d369_{a}_p*of*.json"))
        if not parts:
            continue
        idx, vals = [], []
        for p in parts:
            j = json.loads(p.read_text())
            idx += j["idx"]
            vals += j["vals"]
        if a == "MULTI":
            p50 = json.loads((OUT / "d369_multi_p50.json").read_text())["p50"]
            for cand in ("S6", "C9"):
                R[f"MULTI_{cand}"] = summarise(vals, obs[cand] - p50[cand], seed=hash(cand) % 97)
            R["MULTI"] = dict(draws=len(vals), parts=len(parts))
            continue
        if a != "C":
            assert sorted(idx) == list(range(len(idx))), f"[PART] {a}: draw indices are not a partition"
        R[a] = summarise(vals, obs_for[a], seed=ARMS.index(a))
        R[a]["parts"] = len(parts)

    print("\n" + "=" * 150)
    print("D369 -- the null precision rerun. Verdicts here SUPERSEDE the 200-draw ones in D366/D367/D368.")
    print("=" * 150)
    print(f"  observed (single exit rank {EXIT_ONE}): S6 {obs['S6']:+.4f}   C9 {obs['C9']:+.4f}   "
          f"reduced universe {obs['REDUCED']:+.4f}  bp/bar net PUB")
    print(f"\n  {'arm':<18}{'draws':>8}{'p50':>9}{'p95':>9}{'p95 SE':>9}{'observed':>10}{'margin':>9}"
          f"{'in SE':>7}{'rank%':>7}{'beat':>7}   verdict")
    for a in ("GATEROT_S6", "GATEROT_C9", "APRIME_S6", "APRIME_C9", "GATEROT_REDUCED", "C",
              "MULTI_S6", "MULTI_C9"):
        if a not in R:
            print(f"  {a:<18}{'NOT RUN':>8}")
            continue
        d = R[a]
        print(f"  {a:<18}{d['draws']:8,}{d['p50']:+9.3f}{d['p95']:+9.3f}{d['p95_se']:9.3f}{d['observed']:+10.3f}"
              f"{d['margin']:+9.3f}{d['margin_in_se']:7.1f}{d['pct_rank']:6.1f}%{d['draws_beating_observed']:7,}"
              f"   {d['verdict']}")
    print(f"\n  ROT (rank rotation) is EXACT, not sampled: 24 shifts is the whole population at D348's gate "
          f"width, so it carries no sampling error. D366 measured its p95 at -3.48 against an observed +8.09.")

    ses = [R[a]["p95_se"] for a in R if "p95_se" in R[a]]
    q = {}
    q["Q1"] = R.get("GATEROT_S6", {}).get("verdict") == "CLEARS"
    q["Q2"] = R.get("GATEROT_C9", {}).get("verdict") == "CLEARS"
    q["Q3"] = all(R.get(a, {}).get("verdict") == "CLEARS" for a in ("APRIME_S6", "APRIME_C9"))
    q["Q4"] = R.get("MULTI_S6", {}).get("verdict") == "CLEARS"
    q["Q5"] = R.get("MULTI_C9", {}).get("verdict") == "FAILS"
    q["Q6"] = R.get("GATEROT_REDUCED", {}).get("verdict") == "FAILS"
    q["Q7"] = any(R.get(a, {}).get("verdict") == "UNRESOLVED"
                  for a in ("GATEROT_C9", "MULTI_C9", "GATEROT_REDUCED"))
    q["Q8"] = bool(ses and max(ses) < 0.10)
    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    print("\nPREDICTIONS")
    for lbl, k2 in (("Q1 (LOAD-BEARING) S6 clears its own GATE-ROT p95 by >2 SE", "Q1"),
                    ("Q2 (LOAD-BEARING) C9 alone clears its own GATE-ROT p95 by >2 SE", "Q2"),
                    ("Q3 both candidates clear their A' p95 by >2 SE", "Q3"),
                    ("Q4 S6 clears the MULTI p95", "Q4"),
                    ("Q5 (AGAINST) C9 alone FAILS the MULTI p95", "Q5"),
                    ("Q6 the reduced universe FAILS its GATE-ROT p95", "Q6"),
                    ("Q7 at least one flagged verdict is UNRESOLVED or reversed", "Q7"),
                    ("Q8 the p95 bootstrap SE is below 0.10 bp/bar", "Q8")):
        print(f"  {lbl}: {v_(q[k2])}")
    if ses:
        print(f"     largest p95 SE {max(ses):.4f}; D368's two 200-draw runs differed by 0.40 on the same gate")

    out = dict(study=STUDY, observed=obs, arms=R, predictions=q, exit_rank=EXIT_ONE,
               supersedes="the 200-draw verdicts in D366, D367 and D368",
               note="D369: 10,000 draws per rotation arm. A margin under 2 bootstrap SEs is UNRESOLVED.")
    (OUT / "d369_report.json").write_text(json.dumps(V65.clean(out), indent=1))
    print(f"\nwrote d369_report.json  ({el(t0)})  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--arm", choices=ARMS)
    ap.add_argument("--multi-p50", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--draws", type=int, default=10000)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--nparts", type=int, default=1)
    a = ap.parse_args()
    t0 = time.time()
    print(f"D369  null precision  {a.arm or ('selftest' if a.selftest else 'report')}", flush=True)
    P = PREP.prep(need_grids=False, verbose=False)
    if a.selftest:
        stage_selftest(P, t0)
    elif a.multi_p50:
        stage_multi_p50(P, a.draws, t0)
    elif a.arm:
        stage_arm(P, a.arm, a.draws, a.part, a.nparts, t0)
    elif a.report:
        stage_report(P, t0)
    else:
        ap.error("one of --selftest, --arm, --multi-p50, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
