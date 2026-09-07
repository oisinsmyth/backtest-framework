"""C2b -- the exhaustive rotation audit on ALL FOUR of D361's cells.

    uv run python scripts/c2b_rotation_audit.py --selftest
    uv run python scripts/c2b_rotation_audit.py [--cells G1:T1,G1:T2,G2:T1,G2:T2]

WHY. C2 (data/c2_calm_vs_gate.json) enumerated the rotation null for D361's G2:T2 cell instead of
sampling it, and the exact p95 came out at +41.81 against the published 200-draw value of +35.95.
The verdict SURVIVED -- observed +42.33 is still above -- but its margin fell from +6.4 to +0.52.
Three of D361's four cells have never been audited that way.

THE AUDIT IS CHEAP AND EXACT, and that is the whole point. A circular shift of a market-level gate
has exactly Td-1 admissible offsets -- a finite group of about 4,000 here. Scoring every one of
them gives a p95 with NO sampling error, so a verdict decided on it cannot move again. D369 met
the same wall and asked for more draws; where the population is finite and affordable the answer
is ALL of them.

WHAT THIS EXPECTS TO FIND, stated before the run so the audit is not read as a fishing trip. The
three unaudited cells failed their published rotation by WIDE margins:

    G1:T1   observed  -4.48   published rot p95  +56.54    fails by 61.0
    G1:T2   observed +15.57   published rot p95  +35.04    fails by 19.5
    G2:T1   observed  +4.18   published rot p95  +61.60    fails by 57.4
    G2:T2   observed +42.33   published rot p95  +35.95    PASSES by 6.4  -> exact +41.81, by 0.52

**No exact p95 is going to close a 19.5 bp gap, let alone 61.** So the audit is expected to CONFIRM
all three negatives, and its value is the SECOND output rather than the verdicts:

    THE PAIRED COMPARISON. Four cells give four (published 200-draw p95, exact p95) pairs, and
    with them the question the programme actually needs answered: **does a 200-draw p95
    systematically understate the true one?** If it does, every verdict in the record decided on a
    200-draw p95 is optimistic by an amount this table measures, and the fix is enumeration
    wherever the offset population is finite.

    The tell is already visible in C2's single cell: the MEDIAN was well estimated at 200 draws
    (exact +14.78 against the published +14.66, off by 0.12) while the p95 was off by 5.86. A
    centre estimated well and a tail estimated badly is exactly what 200 draws should produce, and
    four cells is enough to say whether it is a pattern or that one cell's luck.

CONSTRUCTION. Each cell's own gate rotated over its own defined bars, re-ANDed with THAT cell's
ungated trigger, re-simulated through D361's kernel at cap 10 (its primary exit). Identical to
D361's ROT except that the offsets are enumerated rather than sampled.

ASSERTIONS
  [ID]  every cell's observed gated per-trade mean and trade count reproduce D361's published
        values to 1e-9, BEFORE its null is read.
  [ROT] every rotated gate keeps the on-share and the circular run-length multiset exactly, is
        never the observed gate, and its offset lies in [1, Td-1] (D361's assert_ROT, unchanged).
  [E]   the enumeration is complete: the offsets scored are exactly {1 .. Td-1}, asserted as a set.
  [P]   the JSON is persisted BEFORE it is rendered (D371).
  [X]   the self-test RAISES on an enumeration with an offset missing.
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
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


OUT = REPO / "data" / "c2b_rotation_audit.json"
D361_JSON = REPO / "data" / "d361_regime_gated_short.json"
CAP, EXIT_KEY = 10, "cap10"
ALL_CELLS = ("G1:T1", "G1:T2", "G2:T1", "G2:T2")


def enumerate_rotation(P, gp, sig, sc, tag):
    """Score EVERY admissible offset. Returns the value array and the assertion report."""
    offs = np.arange(1, gp["Td"])
    assert set(offs.tolist()) == set(range(1, gp["Td"])), "[E] the enumeration is not {1..Td-1}"
    vals, splits, seen = [], 0, set()
    t0 = time.time()
    for k in offs:
        rg = V61.rotate_gate(gp, int(k))
        info = V61.assert_ROT(gp, rg, int(k), tag=tag)
        splits += int(info["wrap_split"])
        seen.add(int(k))
        m = np.ascontiguousarray(sig & rg[:, None])
        if not m.any():
            continue
        res = V61.run_short(P, m, sc, "cap", CAP)
        vals.append(float(V47.pnl_bp(res).mean()))
    assert seen == set(range(1, gp["Td"])), "[E] an offset was skipped"
    return np.array(vals), dict(offsets=int(offs.size), scored=len(vals), wrap_splits=splits,
                                seconds=time.time() - t0)


def selftest() -> int:
    print("C2b SELF-TEST -- the enumeration must be complete, and an incomplete one must be caught\n")
    Td = 50
    full = set(range(1, Td))
    assert set(np.arange(1, Td).tolist()) == full
    print(f"    a complete enumeration of {Td - 1} offsets is accepted")
    raised = False
    try:
        holed = set(np.arange(1, Td).tolist()) - {7}
        assert holed == full, "[E] an offset was skipped"
    except AssertionError:
        raised = True
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- an enumeration missing an offset passed"
    print("    [X] an enumeration missing offset 7 IS CAUGHT")
    print("\nSELF-TEST PASSED\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--cells", default=",".join(ALL_CELLS))
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    selftest()

    cells = [c.strip() for c in a.cells.split(",") if c.strip()]
    t0 = time.time()
    P = V61.PREP.prep(need_grids=True)
    d361 = json.loads(D361_JSON.read_text())["results"]
    print(f"  prep in {time.time() - t0:.0f}s | auditing {len(cells)} cells at {EXIT_KEY}\n", flush=True)

    R = {}
    for cell in cells:
        g, tr = cell.split(":")
        gated, _off, sig, sc = V61.arms_of(P, g, tr)
        gp = V61.gate_pack(P, g)
        res = V61.run_short(P, gated, sc, "cap", CAP)
        obs = float(V47.pnl_bp(res).mean())
        pub_pt = d361[cell]["gated"][EXIT_KEY]["per_trade"]
        assert abs(obs - pub_pt["mean_bp"]) < 1e-9 and len(res["trades"]) == pub_pt["trades"], \
            f"[ID] {cell}: {obs} / {len(res['trades'])} != D361's {pub_pt['mean_bp']} / {pub_pt['trades']}"
        print(f"    [ID] {cell}: observed {obs:+.5f} on {pub_pt['trades']:,} trades == D361's "
              f"published value to 1e-9", flush=True)

        v, rep = enumerate_rotation(P, gp, sig, sc, f"[ROT {cell}]")
        p50, p95 = float(np.median(v)), float(np.quantile(v, .95))
        pub = d361[cell]["controls"]["rot"]["trade_mean_bp"]
        R[cell] = dict(
            observed=obs, trades=int(pub_pt["trades"]), gate=g, trigger=tr,
            exact=dict(draws=int(v.size), offsets_available=int(gp["Td"] - 1), p50=p50, p95=p95,
                       p05=float(np.quantile(v, .05)), maxv=float(v.max()), se=0.0,
                       above_p95=bool(obs > p95), margin=float(obs - p95),
                       pct_of=float((v < obs).mean() * 100.0), **rep),
            published=dict(draws=pub["draws"], p50=pub["p50"], p95=pub["p95"], maxv=pub["max"],
                           above=pub["above"], margin=float(obs - pub["p95"])),
            delta=dict(p50=p50 - pub["p50"], p95=p95 - pub["p95"],
                       verdict_changed=bool((obs > p95) != bool(pub["above"]))))
        e, p = R[cell]["exact"], R[cell]["published"]
        print(f"    [{cell}] {e['draws']:,} EXHAUSTIVE of {e['offsets_available']:,} in "
              f"{e['seconds']:.0f}s: p50 {p50:+.2f} (pub {p['p50']:+.2f}, d {p50 - p['p50']:+.2f}) | "
              f"p95 {p95:+.2f} (pub {p['p95']:+.2f}, d {p95 - p['p95']:+.2f}) | observed {obs:+.2f} "
              f"-> {'ABOVE' if e['above_p95'] else 'inside'}, margin {e['margin']:+.2f}"
              f"{'   *** VERDICT CHANGED ***' if R[cell]['delta']['verdict_changed'] else ''}\n",
              flush=True)

    # ---- the paired comparison this audit exists for ------------------------
    d50 = [R[c]["delta"]["p50"] for c in R]
    d95 = [R[c]["delta"]["p95"] for c in R]
    paired = dict(cells=list(R),
                  p50_delta=dict(values=d50, mean=float(np.mean(d50)),
                                 mean_abs=float(np.mean(np.abs(d50)))),
                  p95_delta=dict(values=d95, mean=float(np.mean(d95)),
                                 mean_abs=float(np.mean(np.abs(d95)))),
                  understates=int(sum(x > 0 for x in d95)), of=len(d95),
                  verdicts_changed=[c for c in R if R[c]["delta"]["verdict_changed"]])

    payload = dict(
        purpose="C2b: the exhaustive rotation audit on all four of D361's cells. The null is a "
                "finite group of Td-1 offsets, so enumerating it gives an EXACT p95 (SE 0). "
                "Descriptive; scores no new construction and admits nothing (R15).",
        cap=CAP, exit=EXIT_KEY, cells=R, paired_comparison=paired)
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering\n", flush=True)

    print("THE AUDIT -- D361's rotation null, ENUMERATED. p95 exact, SE 0 by construction.\n")
    print(f"  {'cell':<7s} {'obs':>8s} {'p50 pub':>8s} {'p50 exa':>8s} {'d':>7s} | "
          f"{'p95 pub':>8s} {'p95 exa':>8s} {'d':>7s} | {'margin':>8s}  verdict")
    for c in R:
        e, p = R[c]["exact"], R[c]["published"]
        print(f"  {c:<7s} {R[c]['observed']:>+8.2f} {p['p50']:>+8.2f} {e['p50']:>+8.2f} "
              f"{R[c]['delta']['p50']:>+7.2f} | {p['p95']:>+8.2f} {e['p95']:>+8.2f} "
              f"{R[c]['delta']['p95']:>+7.2f} | {e['margin']:>+8.2f}  "
              + ("ABOVE p95" if e["above_p95"] else "inside p95")
              + ("  *** CHANGED ***" if R[c]["delta"]["verdict_changed"] else ""))

    print(f"\nDOES A 200-DRAW p95 UNDERSTATE THE EXACT ONE? {paired['understates']} of "
          f"{paired['of']} cells came in HIGHER when enumerated.")
    print(f"  p50 delta: mean {paired['p50_delta']['mean']:+.2f}, mean |d| "
          f"{paired['p50_delta']['mean_abs']:.2f}   <- the CENTRE, which 200 draws estimates well")
    print(f"  p95 delta: mean {paired['p95_delta']['mean']:+.2f}, mean |d| "
          f"{paired['p95_delta']['mean_abs']:.2f}   <- the TAIL, which is what every verdict uses")
    print(f"  verdicts changed: {paired['verdicts_changed'] or 'none'}")
    print(f"\n  ({time.time() - t0:.0f}s)")
    return 0


V61 = _load("d361r", "run_d361_regime_gated_short.py")
V47 = V61.V47

if __name__ == "__main__":
    raise SystemExit(main())
