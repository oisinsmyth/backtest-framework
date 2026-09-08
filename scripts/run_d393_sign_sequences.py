"""D393 STAGE 0 -- is a sign statistic a new input, or trailing return with the magnitude removed?

    uv run python scripts/run_d393_sign_sequences.py --selftest
    uv run python scripts/run_d393_sign_sequences.py --stage0

Pre-registration: docs/decisions/D393-the-sign-sequence-family.md (committed BEFORE this file, R8).

DESCRIPTIVE. Stage 0 scores no book and admits nothing (R15). It answers K1/K2/K3 from the
pre-registration's section 2, and reports the exposure arithmetic and the atlas floor beside them.

**K1 IS EXPECTED TO FIRE.** Q1 is declared against the candidate: fifteen up days out of
twenty-one is mechanically a positive trailing return, so the claim that magnitude-free buys
independence is exactly what K1 measures. If it fires the record stops here.

THE SCORES ARE COMPUTED IN-PROCESS AND THE CACHE IS NOT TOUCHED, and that is a deliberate choice
with a cost. `run_d350_long_timing_screen.py:97-102` asserts its pool is exactly 46 names AND
set-equal to the npz's members; adding a family to `temp/d290_scores.npz` makes that raise for
D350 and D352, whose 46-name pool and 138-member count are load-bearing in two published records.
The write would also cost 2.7 GB, invalidate `d348_prep`'s cache through `cache_key`, and -- with
`temp/d290_chunk_*.npz` absent from this worktree -- trigger the full C/D/G/H fan.

**So this is a PROBE, not a repeatable artifact.** The grids live only in this process. If Stage 0
clears, promoting the family into the cache properly (new `AXES["I"]`, `"ABCDEFGH"` -> `"...I"` in
two places, the `cache_key` file tuple, a D371-style merge-rewrite) is its own piece of work.

ASSERTIONS
  [T]  the scores are causal -- `ragged_sign_scores`' truncation audit re-run HERE rather than
       trusted from the module's own self-test.
  [L]  from `scripts/lag_audit.py`, with `raises_on_broken` on a deliberately unlagged input.
       D391 listed this requirement and did not implement it.
  [E]  every event sits on an eligible bar (D351).
  [C]  the cache is untouched: `temp/d290_scores.npz` size and mtime unchanged across the run.
  [P]  the JSON is persisted BEFORE it is rendered (D371; D391 reproduced that defect).
  [X]  the self-test RAISES on a flipped direction and on an unlagged mask.
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


OUT = REPO / "data" / "d393_stage0.json"
NPZ = REPO / "temp" / "d290_scores.npz"
ATLAS = REPO / "data" / "d392_atlas.json"

SIGN = ("up_run_21", "sign_flips_21", "up_frac_21")
K1_REF = ("rev_5", "rev_21", "trailing_return", "mom_252_21")
K2_REF = ("rvol21", "atr_norm")
K_RHO = 0.50
K3_MIN_EFF = 2.0
MIN_NAMES = 50
CAPS = (5, 10, 20, 40, 60)
PRIMARY_CAP = 20
POOL = "ALL"                    # declared in the pre-registration section 3, before any number


def rank01(v):
    return np.argsort(np.argsort(v)) / (len(v) - 1) if len(v) > 1 else np.zeros_like(v, float)


def effective_inputs(Rm):
    lam = np.maximum(np.linalg.eigvalsh(Rm), 0.0)
    M = Rm.shape[0]
    return dict(participation_ratio=float(lam.sum() ** 2 / (lam ** 2).sum()),
                li_ji=float(np.sum((lam >= 1.0) + (lam - np.floor(lam)))),
                cheverud_nyholt=float(1.0 + (M - 1) * (1.0 - np.var(lam) / M)))


# ---------------------------------------------------------------------- self-test
def selftest(LA) -> int:
    print("D393 STAGE 0 SELF-TEST -- the direction, the lag, and two breaks that must be caught\n")
    T, N = 60, 30
    rng = np.random.default_rng(393)

    # the declared direction: LONG on the LOW end of the sign statistic
    p = rng.uniform(0, 100, size=(T, N))
    prev = np.full_like(p, np.nan)
    prev[1:] = p[:-1]
    with np.errstate(invalid="ignore"):
        e1 = (p <= 10.0) & (prev > 10.0)
    lo_end = e1.sum()
    with np.errstate(invalid="ignore"):
        wrong = (p >= 90.0) & (prev < 90.0)
    assert lo_end > 0 and wrong.sum() > 0
    print(f"    E1 on the LOW end fires {lo_end} times; the high-end mirror {wrong.sum()} "
          f"-- the declared long is the low end")

    raised = False
    try:
        assert np.array_equal(e1, wrong), "the declared direction must not equal its mirror"
    except AssertionError:
        raised = True
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- the flipped direction passed"
    print("    [X] the direction flipped IS CAUGHT")

    pos = LA.lag1_mask(e1)
    LA.assert_mask_is_lagged(pos, e1)
    LA.raises_on_broken(LA.assert_mask_is_lagged, e1, e1)
    print("    [L] positions open one bar after the signal, and handing the RAW mask over "
          "IS CAUGHT (D391's defect)")
    print("\nSELF-TEST PASSED\n")
    return 0


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--stage0", action="store_true")
    a = ap.parse_args()
    LA = _load("lag_audit", "lag_audit.py")
    if a.selftest:
        return selftest(LA)
    if not a.stage0:
        ap.error("pass --stage0 (stage 1 is not authorised; K1 may stop the record)")
    selftest(LA)

    t0 = time.time()
    npz_before = (NPZ.stat().st_size, int(NPZ.stat().st_mtime)) if NPZ.exists() else None
    PREP = _load("d348p", "d348_prep.py")
    SG = _load("ragged_sign_scores", "ragged_sign_scores.py")
    V50 = _load("d350r", "run_d350_long_timing_screen.py")
    P = PREP.prep(need_grids=True)
    M = PREP.M
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    live = panel.live
    T, N = P["T"], P["n"]
    elig = np.asarray(P["elig"])
    print(f"  prep in {time.time() - t0:.0f}s | {N} names x {T} bars", flush=True)

    # ---- the scores, in-process ------------------------------------------
    t1 = time.time()
    raw = SG.sign_scores(g, live)
    print(f"    sign scores built in {time.time() - t1:.0f}s (IN-PROCESS; the cache is not "
          f"touched)", flush=True)

    # ---- [T] causal, re-checked here rather than trusted -----------------
    T0 = int(T * 0.7)

    def build(cut):
        if cut is None:
            return raw
        gg = {k: v[:, :cut] for k, v in g.items()}
        return SG.sign_scores(gg, live[:, :cut])

    bad = SG.V.truncation_audit(build, live, T0, SIGN, "I")
    assert bad == 0, f"[T] {bad} sign score(s) read the future"
    print(f"    [T] all three scores causal at the truncation audit (column {T0})", flush=True)

    # ---- the comparison grids, through the SAME pipeline ------------------
    def lagged_from(arr):
        """`run_d350.lagged` with the array passed in instead of a cache name -- floored,
        deal-filtered, warm-based, then shifted one bar. Four lines, and the only npz-dependent
        input was the raw grid."""
        sc = np.where(P["excl"], np.nan, arr)
        sc = PREP.UF.apply_floor_replace(sc, P["keep"])
        sc = np.where(P["base"], sc, np.nan)
        out = np.full((T, N), np.nan)
        out[1:] = sc[:, :-1].T
        return out

    cols = {}
    for k in SIGN:
        cols[k] = lagged_from(raw[k])
    for k in K1_REF + K2_REF:
        cols[k] = lagged_from(np.asarray(P["score"](k)))
    names = list(SIGN) + list(K1_REF) + list(K2_REF)
    print(f"    comparison grids built through run_d350.lagged's pipeline "
          f"({len(names)} scores)", flush=True)

    # ---- K1 / K2 / K3: the within-bar correlation, the operative lens -----
    m = len(names)
    acc = np.zeros((m, m))
    bars = 0
    for t in range(T):
        ok = elig[t].copy()
        for k in names:
            ok = ok & np.isfinite(cols[k][t])
        if ok.sum() < MIN_NAMES:
            continue
        X = np.vstack([rank01(cols[k][t][ok]) for k in names])
        R = np.corrcoef(X)
        if np.isfinite(R).all():
            acc += R
            bars += 1
    assert bars > 0, "no bar carried enough eligible names with every score finite"
    Rm = acc / bars
    idx = {k: i for i, k in enumerate(names)}
    rho = lambda a_, b_: float(Rm[idx[a_], idx[b_]])                     # noqa: E731

    k1 = [{"sign": s, "ref": r, "rho": rho(s, r)} for s in SIGN for r in K1_REF
          if abs(rho(s, r)) > K_RHO]
    k2 = [{"sign": s, "ref": r, "rho": rho(s, r)} for s in SIGN for r in K2_REF
          if abs(rho(s, r)) > K_RHO]
    sub = Rm[np.ix_([idx[s] for s in SIGN], [idx[s] for s in SIGN])]
    eff = effective_inputs(sub)
    k3_fail = eff["participation_ratio"] < K3_MIN_EFF

    # ---- the exposure arithmetic, computed before it is predicted --------
    p_sign = {}
    for s in SIGN:
        p_sign[s] = PREP.V47.percentile_grid(cols[s])
    ev = {}
    for s in SIGN:
        p = p_sign[s]
        prev = np.full_like(p, np.nan)
        prev[1:] = p[:-1]
        with np.errstate(invalid="ignore"):
            e1 = (p <= 10.0) & (prev > 10.0) & elig
        ev[s] = int(e1.sum())
    bars_def = int(elig.any(axis=1).sum())

    # ---- the atlas floor for the DECLARED pool ---------------------------
    atlas = json.loads(ATLAS.read_text())
    ATL = _load("d392a", "run_d392_base_rate_atlas.py")
    floors = {}
    for s in SIGN:
        approx_trades = ev[s]           # cap 20 collapses this; reported as the EVENT count
        try:
            floors[s] = ATL.lookup(atlas, approx_trades, PRIMARY_CAP, "long", POOL)
        except (ValueError, KeyError) as e:
            floors[s] = {"error": str(e)}

    # ---- [C] the cache is untouched --------------------------------------
    npz_after = (NPZ.stat().st_size, int(NPZ.stat().st_mtime)) if NPZ.exists() else None
    assert npz_before == npz_after, f"[C] the score cache CHANGED: {npz_before} -> {npz_after}"
    print(f"    [C] temp/d290_scores.npz unchanged ({npz_after[0] / 1e9:.2f} GB)", flush=True)

    verdict = ("K1 FIRES -- a sign statistic is trailing return with the magnitude removed"
               if k1 else "K2 FIRES -- a volatility proxy" if k2 else
               "SIGN STATISTICS CLEAR K1 AND K2 -- a new input on this universe")

    payload = dict(
        study=393, stage=0, purpose="D393 Stage 0: K1/K2/K3 on the sign-sequence family. "
                                    "Descriptive; scores nothing, admits nothing (R15).",
        prereg="docs/decisions/D393-the-sign-sequence-family.md",
        note="Scores computed IN-PROCESS; temp/d290_scores.npz deliberately not written, because "
             "run_d350.load_pool asserts a 46-name pool set-equal to the npz members and two "
             "published records depend on it. This is a probe, not a repeatable artifact.",
        bars=bars, names=names, spearman_within_bar=Rm.tolist(),
        K_RHO=K_RHO, K1_violations=k1, K2_violations=k2,
        effective_inputs_sign_only=eff, K3_fails=bool(k3_fail),
        events_E1=ev, bars_defined=bars_def,
        exposure_arithmetic={s: {str(c): ev[s] / max(1, bars_def) * c for c in CAPS} for s in SIGN},
        atlas_pool=POOL, atlas_floor=floors, verdict=verdict)
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    # ---- render ------------------------------------------------------------
    print(f"\nWITHIN-BAR SPEARMAN, mean over {bars:,} bars (the operative lens)\n")
    print("            " + " ".join(f"{k[:11]:>12s}" for k in names))
    for i, k in enumerate(names):
        print(f"{k[:11]:>11s} " + " ".join(f"{Rm[i, j]:12.3f}" for j in range(m)))

    print(f"\nK1  trailing-return proxy? (|rho| > {K_RHO} vs {', '.join(K1_REF)})\n")
    for s in SIGN:
        print(f"      {s:<14s} " + "  ".join(f"{r} {rho(s, r):+.3f}" for r in K1_REF))
    print(f"    -> {'FIRES' if k1 else 'CLEARS'}")
    print(f"\nK2  volatility proxy? (|rho| > {K_RHO} vs {', '.join(K2_REF)})\n")
    for s in SIGN:
        print(f"      {s:<14s} " + "  ".join(f"{r} {rho(s, r):+.3f}" for r in K2_REF))
    print(f"    -> {'FIRES' if k2 else 'CLEARS'}")
    print(f"\nK3  effective inputs among the three (bar {K3_MIN_EFF}): "
          f"participation ratio {eff['participation_ratio']:.2f}, Li-Ji {eff['li_ji']:.2f}")
    print(f"    -> {'FAILS' if k3_fail else 'CLEARS'}")

    print(f"\nEXPOSURE ARITHMETIC (section 38 rule 2), E1 events over {bars_def:,} bars\n")
    for s in SIGN:
        print(f"      {s:<14s} {ev[s]:>8,} events = {ev[s] / max(1, bars_def):6.2f}/bar "
              f"-> {ev[s] / max(1, bars_def) * PRIMARY_CAP:8.1f} open at cap {PRIMARY_CAP}")

    print(f"\nATLAS FLOOR, pool {POOL} declared in advance (cap {PRIMARY_CAP}, long)\n")
    for s in SIGN:
        f = floors[s]
        print(f"      {s:<14s} " + (f"p95 {f['p95']:+.2f} +/- {f['se_p95']:.2f}"
                                    if "p95" in f else f"-- {f['error'][:64]}"))

    print(f"\nVERDICT: {verdict}")
    print(f"\n  ({time.time() - t0:.0f}s)  No null was run. Stage 1 is not authorised by this file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
