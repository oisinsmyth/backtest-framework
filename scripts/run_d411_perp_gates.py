"""D411 -- the four gates for I_perp, which section 5 of f0a8a14 REQUIRED and the screen omitted.

    uv run python scripts/run_d411_perp_gates.py --run

NOT a new arm and NOT post-hoc. The record declared, before the run:

    "I_perp runs against the same four gates. It is the arm that actually answers PICKUP
     section 0d2's challenge -- whether a construction built on volume carries anything the
     price path does not."

`run_d411_signed_volume_at_price.py` computed I_perp's quintile table but nulled only the raw
arm, so T2, T3 and T4 were never evaluated for it. That is an incompleteness in the runner, of
exactly the kind D403 recorded when OCC and LVL were pre-registered and never built -- and the
fix is to run them, not to report around them.

T4 needs an unsigned counterpart on the same footing, so the unsigned field is residualised on
the same two regressors. Comparing a residualised signed field to a RAW unsigned one would
compare two different objects and T4 would be meaningless.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d411", REPO / "scripts" / "run_d411_signed_volume_at_price.py")
D = importlib.util.module_from_spec(_s)
sys.modules["d411"] = D
_s.loader.exec_module(D)                      # installs D411's [SPLIT] guard; this adds no unlock

OUT = REPO / "data" / "d411_perp_gates.json"
SEED = 23


def resid(I, TR, LP, elig):
    """Same object as D.residualise -- 3x3 normal equations instead of lstsq, guarded by
    equality against it on a slice below rather than assumed."""
    R = np.full_like(I, np.nan)
    for t in range(I.shape[0]):
        m = elig[t] & np.isfinite(I[t]) & np.isfinite(TR[t]) & np.isfinite(LP[t])
        c = int(m.sum())
        if c < D.MIN_NAMES:
            continue
        A = np.column_stack([np.ones(c), TR[t, m], LP[t, m]])
        y = I[t, m]
        G = A.T @ A
        try:
            coef = np.linalg.solve(G, A.T @ y)
        except np.linalg.LinAlgError:
            continue
        R[t, m] = y - A @ coef
    return R


def run():
    t0 = time.time()
    print("D411  the four gates for I_perp -- required by section 5 of f0a8a14\n")
    P = D.load_panel()
    elig = P["elig"]
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    tr20 = D.trailing_ret(lg, 20)
    LP = lg
    F = D.fwd_logret(P, D.H_PRIMARY)[0]

    I = D.imbalance(P, D.W_PRIMARY, D.K_PRIMARY, verbose=True)[0]
    U = D.imbalance(P, D.W_PRIMARY, D.K_PRIMARY, signed=False, verbose=True)[0]

    # the normal-equation residualiser must equal the lstsq one it replaces
    sl = slice(2000, 2200)
    A = D.residualise(I[sl], tr20[sl], LP[sl], elig[sl])
    B = resid(I[sl], tr20[sl], LP[sl], elig[sl])
    m = np.isfinite(A) & np.isfinite(B)
    worst = float(np.max(np.abs(A[m] - B[m])))
    assert worst < 1e-9, f"[X] residualiser rewrite disagrees by {worst:.3e}"
    print(f"  residualiser matches lstsq to {worst:.1e} on a 200-day slice\n")

    Ip = resid(I, tr20, LP, elig)
    Up = resid(U, tr20, LP, elig)
    prim = D.quintile_table(Ip, F, elig)
    unsg = D.quintile_table(Up, F, elig)
    print("  I_perp    " + "  ".join(f"{1e4*m:+7.1f}" for m in prim["means"])
          + f"  bp   spread {1e4*prim['spread']:+.1f}   inc {prim['monotone_inc']}")
    print("  U_perp    " + "  ".join(f"{1e4*m:+7.1f}" for m in unsg["means"])
          + f"  bp   spread {1e4*unsg['spread']:+.1f}   inc {unsg['monotone_inc']}")

    pn = D.perm_null(Ip, F, elig, D.N_PERM, seed=11)
    NP = D.null_stats(pn, prim["spread"])
    print(f"\n  PERM  {D.N_PERM} draws   observed {1e4*NP['observed']:+6.1f}   "
          f"p5 {1e4*NP['p5']:+5.1f}  p50 {1e4*NP['p50']:+5.1f}  p95 {1e4*NP['p95']:+5.1f} bp   "
          f"beats {NP['beats']}   margin {NP['margin_se']:+.1f} SE"
          + ("   UNRESOLVED" if NP["unresolved"] else ""))

    rng = np.random.default_rng(SEED)
    vs = []
    for d in range(D.N_VOLSHUF):
        Vs = P["VOL"].copy()
        for i in range(Vs.shape[1]):
            m = np.isfinite(Vs[:, i])
            if m.sum() > 2:
                Vs[m, i] = rng.permutation(Vs[m, i])
        J = D.imbalance(P, D.W_PRIMARY, D.K_PRIMARY, VOL=Vs)[0]
        c = D.quintile_table(resid(J, tr20, LP, elig), F, elig)
        vs.append(c["spread"] if c else np.nan)
        if d in (0, 9, 24):
            print(f"        VOL-SHUF draw {d+1} of {D.N_VOLSHUF} at {time.time()-t0:.0f}s",
                  flush=True)
    vs = np.array([x for x in vs if np.isfinite(x)])
    VS = D.null_stats(vs, prim["spread"])
    print(f"  VOL-SHUF {len(vs)} draws  observed {1e4*VS['observed']:+6.1f}   "
          f"p5 {1e4*VS['p5']:+5.1f}  p50 {1e4*VS['p50']:+5.1f}  p95 {1e4*VS['p95']:+5.1f} bp   "
          f"beats {VS['beats']}   margin {VS['margin_se']:+.1f} SE"
          + ("   UNRESOLVED" if VS["unresolved"] else ""))

    T1 = bool(prim["monotone_inc"] and prim["spread"] > 0)
    T2 = bool(NP["beats"] and not NP["unresolved"])
    T3 = bool(VS["beats"] and not VS["unresolved"])
    T4 = bool(abs(prim["spread"]) >= D.T4_FACTOR * abs(unsg["spread"]))
    print("\n  --- THE BAR, applied to I_perp (committed f0a8a14) ---")
    print(f"    T1 monotone INCREASING, spread > 0 : {T1}   "
          f"({1e4*prim['spread']:+.1f} bp, inc {prim['monotone_inc']})")
    print(f"    T2 outside the permutation p95     : {T2}")
    print(f"    T3 outside VOL-SHUF p95            : {T3}")
    print(f"    T4 signed >= 1.5x unsigned         : {T4}   "
          f"({1e4*prim['spread']:+.1f} vs {1e4*unsg['spread']:+.1f} bp, "
          f"ratio {abs(prim['spread'])/max(abs(unsg['spread']),1e-12):.2f}x)")
    clears = bool(T1 and T2 and T3 and T4)
    print(f"\n  VERDICT for I_perp: {'CLEARS' if clears else 'FAILS'}")
    OUT.write_text(json.dumps(dict(arm="I_perp", bar=dict(T1=T1, T2=T2, T3=T3, T4=T4,
                                                          clears=clears),
                                   perp=prim, unsigned_perp=unsg,
                                   nulls=dict(perm=NP, volshuf=VS)),
                              indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT}  in {time.time()-t0:.0f}s")
    return clears


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--draws", type=int, default=None,
                    help="Override N_VOLSHUF. Used ONLY to resolve a margin the 50 declared "
                         "draws left inside 2 SE -- D373's rule says record UNRESOLVED, and the "
                         "way out of UNRESOLVED is more draws, not a softer bar.")
    ap.add_argument("--seed", type=int, default=23)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    if a.draws:
        D.N_VOLSHUF = a.draws
    SEED = a.seed
    if a.out:
        OUT = pathlib.Path(a.out)
    run()
