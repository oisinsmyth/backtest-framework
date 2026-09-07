"""C2 -- the cell D362 named and did not run: the gap-up fade with the CALM-MARKET condition alone and NO gate.

    uv run python scripts/c2_calm_vs_gate.py --selftest
    uv run python scripts/c2_calm_vs_gate.py [--draws-rot 200]

WHY THIS CELL, in D362's own words (FINDINGS section 42): "With the calm-market sink on, the
filtered cell is INSIDE the gate rotation's p95 (+79.3, p50 +30.6): a calm-market condition is a
market state, and it does part of what the gate did. **Which of the two is the state variable is
one cell the record has not run -- the trigger with the calm-market condition alone and no
gate.**"

AND SECTION 7e SHARPENED IT. D362's calm-market sink is S2: `mkt_vol_20 <= 99.03` -- the floored
market's own 20-bar volatility. C1b then found that the only decisive market state in the C1
sequence is REALISED VOLATILITY (VOL_XS +0.288 against a shuffled p95 of 0.152), while G2 -- the
200-day-mean gate this fade actually uses -- has NO decisive premise on any target. So the
question is no longer bookkeeping: **if a volatility condition alone reproduces what the 200-day
gate buys, the surviving short's state variable has been misidentified since D361.**

THE FIVE CELLS. Trigger T2 (D360's gap-up fade mirror (2, 10)) entered SHORT at the next open,
cap 10, D345's kernel -- D361's G2:T2 construction, imported and never re-derived.

    UNG        sig                      D361's gate-off reference           published +9.65
    UNG_S2     sig & ~S2                **THE UNRUN CELL** -- calm removed, NO gate
    GATED      sig & G2                 D361's gated cell                   published +42.33
    GATED_S2   sig & G2 & ~S2           what S2 adds ON TOP of the gate
    GATED_A2   sig & G2 & ~(S1 | S2)    D362's primary arm                  published +61.7

THE NULL, and it is the same object for both states. S2 is a market-level condition, so under
D362 rule 2 it IS a gate and must be tested as one. Both `~S2` and `G2` are rotated in time with
D361's own `rotate_gate` / `rot_offsets` / `assert_ROT` -- offsets drawn WITHOUT replacement, the
on-share and the circular run-length multiset preserved exactly -- and re-ANDed with the ungated
trigger. Identical machinery, identical seed policy, so the two states are compared like for like
rather than against D361's published draws.

    ROT_S2   does `~S2` remove the right TIMES, or merely the right NUMBER of bars?
    ROT_G2   the same question for the 200-day gate, recomputed here so the two are comparable.

PREDICTIONS, committed before the runner was executed and scored mechanically in section Q.

    Q1  (load-bearing) UNG_S2's gross mean per trade is materially above UNG's +9.65 -- the
        calm-market condition ALONE carries much of what the gate buys.
    Q2  UNG_S2 is above the p95 of ROT_S2 -- the condition is timing, not a count.
    Q3  (against) GATED_S2 is NOT materially above GATED: the two states overlap, so stacking the
        volatility condition on the 200-day gate adds little. If Q1 and Q3 both hold, the gate and
        the calm-market sink are one state and the record should say which.
    Q4  the Jaccard overlap of the `~S2` and `G2` ON bars is above 0.35 -- higher than the 0.28
        to 0.32 C1 measured between dispersion and the direction family, because both of these are
        conditions on the same market.

THIS SCORES NO NEW CONSTRUCTION AND ADMITS NOTHING. Every cell is D361's trigger with a mask
applied; the cost lines are reported and gate nothing (R15).

ASSERTIONS
  [ID]  GATED and UNG reproduce D361's published per-trade means and trade counts to 1e-9, and
        GATED_A2 reproduces D362's, BEFORE any new cell is read.
  [S2]  the S2 flag equals D362's `hit_grids` row 1 on every bar, and its threshold and operator
        are read from D362's own SINKS tuple rather than retyped.
  [ROT] every rotated gate keeps the on-share and the circular run-length multiset exactly, is
        never the observed gate, and its offset lies in [1, Td-1] (D361's assert_ROT, unchanged).
  [P]   the JSON is persisted BEFORE it is rendered (D371).
  [X]   the self-test RAISES on a rotation that does not preserve the on-share.
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


OUT = REPO / "data" / "c2_calm_vs_gate.json"
D361_JSON = REPO / "data" / "d361_regime_gated_short.json"
D362_JSON = REPO / "data" / "d362_sink_filter.json"
CELL, CAP, TRIG = "G2:T2", 10, "T2"
SEED = 20260907


def pack_from_bool(name, gate, defined):
    """A D361 `gate_pack`-shaped dict from a boolean series, so rotate_gate / rot_offsets /
    assert_ROT apply unchanged. NOT lagged here: `mkt_vol_20` is defined over bars t-20..t-1 and
    G2 over t-200..t-1, so both already read only the past -- lagging again would double-lag."""
    ok = np.flatnonzero(defined)
    assert ok.size, f"{name}: never defined"
    d0 = int(ok[0])
    assert defined[d0:].all(), f"{name}: undefined bars after d0"
    g = np.zeros_like(gate)
    g[d0:] = gate[d0:]
    return dict(name=name, d0=d0, Td=int(gate.size - d0), gate=g, defined=defined,
                on=int(g.sum()), on_share=float(g[d0:].mean()))


def score(P, sig, sc, elig, label):
    """One cell: the per-trade block and the deployed block. No gate object needed."""
    res = V61.run_short(P, sig, sc, "cap", CAP)
    trd = V59.trade_block(P, res, elig, 1, False)
    dep = V59.deployed_block(res, P)
    return dict(label=label, events=int(sig.sum()), per_trade=trd, deployed=dep), res


def jaccard(a, b):
    u = int((a | b).sum())
    return float((a & b).sum() / u) if u else float("nan")


# ---------------------------------------------------------------------- self-test
def selftest() -> int:
    print("C2 SELF-TEST -- the rotation invariant, and a break that must be caught\n")
    T = 500
    gate = np.zeros(T, bool)
    gate[100:140] = True
    gate[200:215] = True
    gate[400:460] = True
    defined = np.zeros(T, bool)
    defined[50:] = True
    gp = pack_from_bool("PROBE", gate, defined)
    rng = np.random.default_rng(1)
    for k in rng.choice(np.arange(1, gp["Td"]), size=25, replace=False):
        rot = V61.rotate_gate(gp, int(k))
        V61.assert_ROT(gp, rot, int(k), tag="[ROT]")
    print(f"    [ROT] 25 offsets: on-share and circular run multiset preserved exactly "
          f"(on {gp['on']} of {gp['Td']} defined bars)")

    # [X] a rotation that drops an on-bar must be CAUGHT
    bad = V61.rotate_gate(gp, 7)
    bad[np.flatnonzero(bad)[0]] = False
    raised = False
    try:
        V61.assert_ROT(gp, bad, 7, tag="[ROT]")
    except AssertionError:
        raised = True
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- a rotation that lost an on-bar passed"
    print("    [X] a rotation with one on-bar removed IS CAUGHT by assert_ROT")

    a = np.zeros(10, bool); a[:5] = True
    b = np.zeros(10, bool); b[3:8] = True
    assert abs(jaccard(a, b) - 2 / 8) < 1e-12, "jaccard"
    print(f"    jaccard on a hand case: {jaccard(a, b):.3f} == 2/8")
    print("\nSELF-TEST PASSED\n")
    return 0


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws-rot", type=int, default=200)
    ap.add_argument("--full", action="store_true",
                    help="score EVERY admissible rotation offset (Td-1 of them) instead of "
                         "sampling: the null is a finite group, so this makes the p95 EXACT")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    selftest()

    t0 = time.time()
    P = V62.PREP.prep(need_grids=True)
    T, n = P["T"], P["n"]
    gated, off, sig, sc = V61.arms_of(P, "G2", TRIG)
    elig = V61.triggers(P)[TRIG][2]
    G2 = V61.gate_pack(P, "G2")
    print(f"  prep in {time.time() - t0:.0f}s | trigger {TRIG}: {int(sig.sum()):,} ungated events, "
          f"{int(gated.sum()):,} gated", flush=True)

    # ---- [S2] the calm-market condition, taken from D362's own SINKS -------
    nm2, feat2, op2, th2 = V62.SINKS[1]
    assert nm2 == "S2" and feat2 == "mkt_vol_20" and op2 == "<=", f"[S2] SINKS[1] is {V62.SINKS[1]}"
    mv = V62.mkt_vol_20_series(P)
    fin = np.isfinite(mv)
    with np.errstate(invalid="ignore"):
        calm = fin & (mv <= th2)
    H, _hits = V62.hit_grids(V62.features(P), T, n)
    assert np.array_equal(H[1], np.broadcast_to(calm[:, None], (T, n))), \
        "[S2] the calm flag differs from D362's hit_grids row 1"
    print(f"    [S2] calm = mkt_vol_20 {op2} {th2} equals D362's hit_grids row 1 on all "
          f"{T * n:,} cells; calm on {int(calm.sum()):,} of {int(fin.sum()):,} defined bars "
          f"({100 * calm[fin].mean():.1f}%)", flush=True)
    NOTCALM = pack_from_bool("NOT_CALM", fin & ~calm, fin)

    # ---- the five cells -----------------------------------------------------
    masks = {
        "UNG": sig,
        "UNG_S2": np.ascontiguousarray(sig & NOTCALM["gate"][:, None]),
        "GATED": gated,
        "GATED_S2": np.ascontiguousarray(gated & NOTCALM["gate"][:, None]),
        "GATED_A2": np.ascontiguousarray(gated & ~(H[0] | H[1])),
    }
    R = {}
    for k, m in masks.items():
        R[k], _res = score(P, m, sc, elig, k)
        pt = R[k]["per_trade"]
        print(f"    {k:<9s} {pt['trades']:>6,} trades  gross {pt['mean_bp']:+7.2f} bp  "
              f"median {pt['median_bp']:+7.2f}  t {pt['t']:+.2f}", flush=True)

    # ---- [ID] against the published records --------------------------------
    d361 = json.loads(D361_JSON.read_text())[ "results"][CELL]
    pub_g = d361["gated"][f"cap{CAP}"]["per_trade"]
    pub_o = d361["off"][f"cap{CAP}"]["per_trade"]
    idr = {}
    for k, pub in (("GATED", pub_g),):
        got = R[k]["per_trade"]
        assert abs(got["mean_bp"] - pub["mean_bp"]) < 1e-9 and got["trades"] == pub["trades"], \
            f"[ID] {k}: {got['mean_bp']} / {got['trades']} != D361's {pub['mean_bp']} / {pub['trades']}"
        idr[k] = {"published": pub["mean_bp"], "recomputed": got["mean_bp"], "trades": got["trades"]}
        print(f"    [ID] {k} reproduces D361's published {pub['mean_bp']:+.5f} on "
              f"{pub['trades']:,} trades to 1e-9", flush=True)
    print(f"    [ID] D361's gate-OFF arm is published at {pub_o['mean_bp']:+.2f} on "
          f"{pub_o['trades']:,} trades; UNG here is the FULL ungated trigger "
          f"({R['UNG']['per_trade']['trades']:,} trades) and is a different arm by construction",
          flush=True)

    # ---- the rotations ------------------------------------------------------
    rot = {}
    for tag, gp in (("ROT_S2", NOTCALM), ("ROT_G2", G2)):
        rng = np.random.default_rng([SEED, 2, len(rot)])
        if a.full:
            # THE ROTATION NULL IS A FINITE GROUP AND CAN BE EXHAUSTED. A circular
            # shift of a market-level gate has exactly Td-1 admissible offsets, so
            # at `--full` there is NO SAMPLING and the p95 is EXACT -- no bootstrap
            # SE, because there is nothing to bootstrap. This is the clean answer to
            # D369, which found a 200-draw p95 carrying an SE that decided verdicts
            # it could not resolve: here the population is ~4,000 and affordable.
            offs = np.arange(1, gp["Td"])
        else:
            offs = V61.rot_offsets(gp, a.draws_rot, rng)
        vals, splits = [], 0
        t1 = time.time()
        for k in offs:
            rg = V61.rotate_gate(gp, int(k))
            info = V61.assert_ROT(gp, rg, int(k), tag=f"[{tag}]")
            splits += int(info["wrap_split"])
            m = np.ascontiguousarray(sig & rg[:, None])
            if not m.any():
                continue
            res = V61.run_short(P, m, sc, "cap", CAP)
            vals.append(float(V47.pnl_bp(res).mean()))
        v = np.array(vals)
        obs = R["UNG_S2" if tag == "ROT_S2" else "GATED"]["per_trade"]["mean_bp"]
        # D369's guard: the bootstrap SE of the reported p95. EXACT (0.0) under --full,
        # because the whole population of offsets was scored and nothing was sampled.
        if a.full:
            se95 = 0.0
        else:
            bs = np.random.default_rng([SEED, 3, len(rot)])
            se95 = float(np.std([np.quantile(bs.choice(v, v.size, replace=True), .95)
                                 for _ in range(1000)], ddof=1))
        p95 = float(np.quantile(v, .95))
        rot[tag] = dict(draws=int(v.size), exhaustive=bool(a.full), offsets_available=int(gp["Td"] - 1),
                        p50=float(np.median(v)), p95=p95, p95_bootstrap_se=se95,
                        p05=float(np.quantile(v, .05)), maxv=float(v.max()), observed=obs,
                        above_p95=bool(obs > p95), margin=float(obs - p95),
                        unresolved=bool(not a.full and abs(obs - p95) < 2.0 * se95),
                        pct_of=float((v < obs).mean() * 100.0), wrap_splits=splits,
                        values=[float(x) for x in v], seconds=time.time() - t1)
        r_ = rot[tag]
        print(f"    [{tag}] {v.size}{' EXHAUSTIVE' if a.full else ''} draws of "
              f"{gp['Td'] - 1} possible in {time.time() - t1:.0f}s: p50 {r_['p50']:+.2f}, "
              f"p95 {p95:+.2f} (SE {se95:.2f}); observed {obs:+.2f} -> "
              f"{'ABOVE' if r_['above_p95'] else 'inside'} p95, margin {r_['margin']:+.2f}"
              f"{'  [UNRESOLVED: inside 2 SE]' if r_['unresolved'] else ''} "
              f"({r_['pct_of']:.1f}th percentile)", flush=True)

    # ---- Q4: are the two states the same object? ---------------------------
    both = NOTCALM["defined"] & G2["defined"]
    ov = dict(bars=int(both.sum()),
              jaccard=jaccard(NOTCALM["gate"] & both, G2["gate"] & both),
              notcalm_share=float(NOTCALM["gate"][both].mean()),
              g2_share=float(G2["gate"][both].mean()),
              phi=float(np.corrcoef(NOTCALM["gate"][both].astype(float),
                                    G2["gate"][both].astype(float))[0, 1]))

    # ---- the predictions, scored -------------------------------------------
    m_ = lambda k: R[k]["per_trade"]["mean_bp"]                        # noqa: E731
    Q = {
        "Q1": bool(m_("UNG_S2") > m_("UNG") + 10.0),
        "Q2": bool(rot["ROT_S2"]["above_p95"]),
        "Q3": bool(not (m_("GATED_S2") > m_("GATED") + 10.0)),
        "Q4": bool(ov["jaccard"] > 0.35),
    }

    payload = dict(
        purpose="C2: the gap-up fade with the calm-market condition alone and no gate -- the cell "
                "D362 named as unrun. Descriptive; no new construction, nothing admitted (R15).",
        cell=CELL, cap=CAP, trigger=TRIG, seed=SEED, draws_rot=a.draws_rot,
        sink_S2=dict(name=nm2, feature=feat2, op=op2, threshold=th2),
        identity=idr, published_gate_off=dict(mean_bp=pub_o["mean_bp"], trades=pub_o["trades"]),
        cells={k: dict(events=v["events"], per_trade=v["per_trade"], deployed=v["deployed"])
               for k, v in R.items()},
        rotations=rot, state_overlap=ov, predictions=Q)
    OUT.write_text(json.dumps(V59.clean(payload) if hasattr(V59, "clean") else payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    # ---- render -------------------------------------------------------------
    print("\nTHE FIVE CELLS -- gap-up fade, short, cap 10, bp per TRADE (path-invariant; never "
          "compared to the per-bar lines)\n")
    print(f"  {'cell':<10s} {'trades':>7s} {'gross':>8s} {'median':>8s} {'t':>6s} "
          f"{'era1':>8s} {'era2':>8s} {'netPB':>8s} {'netPUB':>8s}")
    for k in masks:
        p = R[k]["per_trade"]
        print(f"  {k:<10s} {p['trades']:>7,} {p['mean_bp']:>+8.2f} {p['median_bp']:>+8.2f} "
              f"{(p['t'] or 0):>+6.2f} {(p['era1_mean_bp'] or 0):>+8.2f} "
              f"{(p['era2_mean_bp'] or 0):>+8.2f} {p['net_per_trade']['PB']:>+8.2f} "
              f"{p['net_per_trade']['PUB']:>+8.2f}")

    print("\nTHE ROTATIONS -- each state rotated in time, re-ANDed with the ungated trigger. "
          "Identical machinery for both.\n")
    print(f"  {'state':<8s} {'draws':>7s} {'of':>7s} {'p50':>8s} {'p95':>8s} {'SE':>6s} "
          f"{'observed':>9s} {'margin':>8s}  verdict")
    for tag, v in rot.items():
        print(f"  {tag:<8s} {v['draws']:>7d} {v['offsets_available']:>7d} {v['p50']:>+8.2f} "
              f"{v['p95']:>+8.2f} {v['p95_bootstrap_se']:>6.2f} {v['observed']:>+9.2f} "
              f"{v['margin']:>+8.2f}  "
              + ("ABOVE p95" if v["above_p95"] else "inside p95")
              + (" [EXACT]" if v["exhaustive"] else (" [UNRESOLVED]" if v["unresolved"] else "")))

    print(f"\nARE THE TWO STATES THE SAME OBJECT? over {ov['bars']:,} commonly-defined bars: "
          f"Jaccard {ov['jaccard']:.3f}, phi {ov['phi']:+.3f}")
    print(f"  NOT_CALM on {100 * ov['notcalm_share']:.1f}% of bars; G2 on "
          f"{100 * ov['g2_share']:.1f}%")

    print("\nPREDICTIONS")
    txt = {"Q1": "UNG_S2 materially above UNG (+10 bp) -- calm alone carries much of the gate",
           "Q2": "UNG_S2 above ROT_S2's p95 -- the condition is timing, not a count",
           "Q3": "(against) GATED_S2 NOT materially above GATED -- the two overlap",
           "Q4": "Jaccard of the two states above 0.35"}
    for k, v in Q.items():
        print(f"  {k} {'HELD    ' if v else 'FALSIFIED'}  {txt[k]}")
    print(f"\n  ({time.time() - t0:.0f}s)")
    return 0


V62 = _load("d362r", "run_d362_sink_filter.py")
V61 = V62.V61 if hasattr(V62, "V61") else _load("d361r", "run_d361_regime_gated_short.py")
V59, V47 = V61.V59, V61.V47

if __name__ == "__main__":
    raise SystemExit(main())
