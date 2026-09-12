"""D413 -- departure zones armed on DISTANCE. The bar was committed in 6374e5c BEFORE this ran.

    uv run python scripts/run_d413_distance_armed_zones.py --run

D412's construction with exactly ONE rule changed, imported rather than restated so the two are
provably the same object:

    D412  ARM when C[t] > H_u             or C[t] < L_u
    D413  ARM when C[t] > H_u + delta*ATR or C[t] < L_u - delta*ATR      delta = 1.0

"Left and never came back" is a claim about distance and time. D412 encoded neither, and its median
zone armed 0.38 ATR out and was touched ONE BAR later. delta = 0.0 reproduces D412's committed
artifact byte-for-byte, which was verified before this file was written.

THE BAR (record section 4) -- D412's, with ONE ORDERING DEFECT FIXED and no threshold moved:
  T1  first-touch mean > 0, direction declared in advance
  T2  beats LVL's p95         NOT EVALUATED unless T1 holds. In D411 and again in D412 a control
  T3  beats ORD's p95         gate read True while estimate and control were BOTH NEGATIVE.
  T4  first touch exceeds the second by more than 2 SE
  R1  SEPARATE, and a REPLICATION not a discovery: age terciles monotone increasing, oldest
      positive. D412's -3.06/+5.47/+10.40 is why this study exists, so R1 clears nothing.

[DIST] guards the only thing that changed, and it must FAIL against D412's rule.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d412", REPO / "scripts" / "run_d412_departure_zones.py")
Z4 = importlib.util.module_from_spec(_s)
sys.modules["d412"] = Z4
_s.loader.exec_module(Z4)                  # installs the [SPLIT] holdout guard; D413 adds no unlock
D = Z4.D

OUT = REPO / "data" / "d413_distance_armed_zones.json"
DELTA, THETA, LIFE, H = 1.0, 1.0, 60, 5
SWEEP = [("delta", d) for d in (0.5, 2.0)] + [("life", L) for L in (120, 250)] + \
        [("h", x) for x in (1, 21)]
N_DRAW = 200


def assert_DIST(P, atr, delta):
    """[DIST] every armed zone clears the zone by >= delta*ATR -- AND the same assertion must FAIL
    on D412's rule. A gate that cannot be shown to bind on the old behaviour is not a gate."""
    cand, _ = Z4.candidates(P, atr, "dep", THETA)

    def worst(dl):
        Z = Z4.build_zones(P, cand, atr, LIFE, delta=dl)
        # atr_u, NOT atr: the gate padded by the ATR at the CREATION bar, so the check must
        # divide by that same quantity. Dividing by the arming-bar ATR fires whenever volatility
        # moved in between -- which is what it did, at 0.358, on the first run of this assertion.
        return float(np.min(Z["dist"] / (delta * Z["atr_u"]))), len(Z["u"])

    w_new, n_new = worst(delta)
    w_old, n_old = worst(0.0)
    assert w_new >= 1.0 - 1e-9, f"[DIST] a D413 zone armed at {w_new:.3f} of the required distance"
    assert w_old < 1.0, f"[DIST] cannot fail on D412's rule -- it is not a gate ({w_old:.3f})"
    return dict(ratio_new=w_new, ratio_old=w_old, n_new=n_new, n_old=n_old)


def age_table(A, nq=3):
    """First-touch response stratified by AGE (bars from arming to touch). R1's object."""
    g = A["good"]
    age = (A["idx"] + 1)[g].astype(float)
    r = A["r"][g]
    q = np.quantile(age, np.linspace(0, 1, nq + 1))
    q[-1] += 1e-9
    b = np.clip(np.searchsorted(q, age, side="right") - 1, 0, nq - 1)
    rows = []
    for j in range(nq):
        m = b == j
        rows.append(dict(n=int(m.sum()), age_lo=float(age[m].min()), age_hi=float(age[m].max()),
                         mean=float(r[m].mean()),
                         se=float(r[m].std(ddof=1) / np.sqrt(max(m.sum(), 2)))))
    return rows, q


def lvl_oldest(P, Z, A, HIw, LOw, ok, rows_w, h, age_lo, n_draw, seed=5):
    """NOT DECLARED in 6374e5c. An extra control on R1's oldest tercile, run because it can only
    WEAKEN R1 -- the direction of a post-hoc test is what makes it a rescue, and this runs the
    other way. Control events are restricted to the SAME age band as the real oldest tercile."""
    rng = np.random.default_rng(seed)
    side = Z["side"]
    grp = {s: np.where(side == s)[0] for s in (1, -1)}
    out = []
    for _ in range(n_draw):
        w2, d2 = np.empty_like(Z["wid"]), np.empty_like(Z["dist"])
        for s, g in grp.items():
            p = rng.permutation(g)
            w2[g], d2[g] = Z["wid"][p], Z["dist"][p]
        hi_b = np.where(side > 0, Z["Ca"] - d2, Z["Ca"] + d2 + w2)
        lo_b = np.where(side > 0, Z["Ca"] - d2 - w2, Z["Ca"] + d2)
        idx, has = Z4.touches(HIw, LOw, ok, lo_b, hi_b)
        r, good, _ = Z4.response(P, Z, rows_w, idx, has, side, h)
        m = good & ((idx + 1) >= age_lo)
        out.append(float(r[m].mean()) if m.sum() >= Z4.MIN_EVENTS else np.nan)
    return np.array([x for x in out if np.isfinite(x)])


def run():
    t0 = time.time()
    print("D413  departure zones armed on DISTANCE")
    print("      the bar was committed in 6374e5c BEFORE this ran\n")
    P = D.load_panel()
    atr = Z4.atr_of(P)

    dd = assert_DIST(P, atr, DELTA)
    print(f"  [DIST] D413 min separation {dd['ratio_new']:.3f} of the required {DELTA} ATR "
          f"(>=1 required)")
    print(f"         D412's rule gives {dd['ratio_old']:.3f} -- the gate BINDS, it is not "
          f"decorative")
    print(f"         zones: {dd['n_new']:,} armed at delta={DELTA} vs {dd['n_old']:,} at delta=0 "
          f"({100*dd['n_new']/dd['n_old']:.1f}%)")

    A = Z4.run_arm(P, atr, "dep", THETA, LIFE, H, delta=DELTA, verbose=True)
    assert A is not None, "no zones survived the distance gate"
    Z = A["Z"]
    has = A["has"]
    age = np.where(has, A["idx"] + 1, -1)

    # ---------------- stage 0
    p1 = dict(armed=int(len(Z["u"])), touched=int(has.sum()),
              expired=int((~has).sum()), resolved=int(A["good"].sum()),
              age_p50=float(np.median(age[has])), within2=float(np.mean(age[has] <= 2)),
              within5=float(np.mean(age[has] <= 5)))
    print(f"\n  P1  armed {p1['armed']:,}  touched {p1['touched']:,}  "
          f"expired unrevisited {p1['expired']:,} "
          f"({100*p1['expired']/max(p1['armed'],1):.1f}%)  resolved {p1['resolved']:,}")
    print(f"      median age at first touch {p1['age_p50']:.0f} bars   "
          f"within 2 {100*p1['within2']:.1f}%   within 5 {100*p1['within5']:.1f}%   "
          f"(D412: 1 bar, 81.1% within 5)")
    gate_worked = p1["age_p50"] > 2
    print(f"      the distance gate {'MOVED' if gate_worked else 'DID NOT MOVE'} the number it "
          f"exists to move")
    dist_atr = Z["dist"] / Z["atr"]
    p2 = [float(np.quantile(dist_atr, q)) for q in (.1, .5, .9)]
    print(f"  P2  distance/ATR at arming  p10/50/90 " + " ".join(f"{x:.2f}" for x in p2)
          + "   (D412: 0.06 0.38 1.18)")
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    tr20 = D.trailing_ret(lg, 20)
    g = A["good"]
    tv = np.full(len(g), np.nan)
    tv[g] = tr20[A["tt"][g], Z["i"][g]] * Z["side"][g]
    m = g & np.isfinite(tv)
    p3 = float(np.corrcoef(A["r"][m], tv[m])[0, 1])
    print(f"  P3  corr(resp, signed trailing 20d)  {p3:+.4f}" + ("   FIRES" if abs(p3) > .5 else ""))
    j = int(np.where(g)[0][np.argmax(age[np.where(g)[0]])])
    p4 = dict(symbol=P["symbols"][Z["i"][j]], created=P["dates"][Z["u"][j]],
              armed=P["dates"][Z["a"][j]], touched=P["dates"][A["tt"][j]], age=int(age[j]),
              lo=float(Z["lo"][j]), hi=float(Z["hi"][j]), side=int(Z["side"][j]),
              dist_atr=float(dist_atr[j]), resp=float(A["r"][j]))
    print(f"  P4  oldest resolved: {p4['symbol']} created {p4['created']} armed {p4['armed']} "
          f"touched {p4['touched']} after {p4['age']} bars")
    print(f"      zone [{p4['lo']:.2f},{p4['hi']:.2f}] side {p4['side']:+d} "
          f"armed {p4['dist_atr']:.2f} ATR out  resp {1e4*p4['resp']:+.1f} bp")

    # ---------------- the primary
    prim = Z4.arm_stats(A["r"], A["good"])
    assert prim is not None, "the primary arm did not populate"
    print(f"\n  --- THE PRIMARY (delta={DELTA}, theta={THETA}, life={LIFE}, h={H}) ---")
    print(f"  first touch   n {prim['n']:,}   mean {1e4*prim['mean']:+7.2f} bp "
          f"+-{1e4*prim['se']:.2f}   {prim['mean']/prim['se']:+.1f} SE   "
          f"win {100*prim['win']:.1f}%")

    rev = {}
    for w in (1, 2):
        i2, h2 = Z4.touches(A["HIw"], A["LOw"], A["ok"], Z["lo"], Z["hi"], which=w)
        r2, g2, _ = Z4.response(P, Z, A["rows"], i2, h2, Z["side"], H)
        rev[w + 1] = Z4.arm_stats(r2, g2)
        if rev[w + 1]:
            print(f"  touch #{w+1}      n {rev[w+1]['n']:,}   mean {1e4*rev[w+1]['mean']:+7.2f} bp "
                  f"+-{1e4*rev[w+1]['se']:.2f}")

    # ---------------- R1, declared as a replication
    ages, qcut = age_table(A)
    print(f"\n  --- R1, a REPLICATION and not a discovery (record section 3) ---")
    for k, row in enumerate(ages):
        print(f"  age tercile {k+1}  [{row['age_lo']:.0f},{row['age_hi']:.0f}] bars   "
              f"n {row['n']:7,}   mean {1e4*row['mean']:+7.2f} bp +-{1e4*row['se']:.2f}")
    R1 = bool(all(ages[k]["mean"] <= ages[k + 1]["mean"] for k in range(len(ages) - 1))
              and ages[-1]["mean"] > 0)
    print(f"  R1 monotone increasing AND oldest positive : {R1}")

    # ---------------- controls
    print(f"\n  --- the controls (median printed beside the observed, per record section 4) ---")
    lv = Z4.lvl_null(P, Z, A["HIw"], A["LOw"], A["ok"], A["rows"], H, N_DRAW)
    LV = Z4.null_stats(lv, prim["mean"])
    print(f"  LVL  {LV['n']} draws  observed {1e4*LV['observed']:+7.2f}   "
          f"p50 {1e4*LV['p50']:+6.2f}   p95 {1e4*LV['p95']:+6.2f} bp   "
          f"beats {LV['beats']}  margin {LV['margin_se']:+.1f} SE"
          + ("  UNRESOLVED" if LV["unresolved"] else ""))
    Ao = Z4.run_arm(P, atr, "ord", THETA, LIFE, H, cap=3 * len(Z["u"]), delta=DELTA)
    od, n_ord = Z4.subsample_null(Ao["r"], Ao["good"], prim["n"], N_DRAW) if Ao else (np.array([]), 0)
    OD = Z4.null_stats(od, prim["mean"])
    if OD:
        print(f"  ORD  {OD['n']} draws  observed {1e4*OD['observed']:+7.2f}   "
              f"p50 {1e4*OD['p50']:+6.2f}   p95 {1e4*OD['p95']:+6.2f} bp   "
              f"beats {OD['beats']}  margin {OD['margin_se']:+.1f} SE"
              + ("  UNRESOLVED" if OD["unresolved"] else ""))
    Aa = Z4.run_arm(P, atr, "abs", THETA, LIFE, H, delta=DELTA)
    ab = Z4.arm_stats(Aa["r"], Aa["good"]) if Aa else None
    if ab:
        d = prim["mean"] - ab["mean"]
        sd = float(np.hypot(prim["se"], ab["se"]))
        print(f"  ABS  (contrast, CANNOT CLEAR)  n {ab['n']:,}  mean {1e4*ab['mean']:+7.2f} bp "
              f"+-{1e4*ab['se']:.2f}   departure - absorption {1e4*d:+.2f} vs SE {1e4*sd:.2f}")

    # ---------------- the extra control on R1's oldest tercile
    LVo = None
    if R1:
        lvo = lvl_oldest(P, Z, A, A["HIw"], A["LOw"], A["ok"], A["rows"], H,
                         ages[-1]["age_lo"], N_DRAW)
        LVo = Z4.null_stats(lvo, ages[-1]["mean"])
        if LVo:
            print(f"\n  LVL on R1's oldest tercile (NOT DECLARED; can only weaken R1)")
            print(f"       observed {1e4*LVo['observed']:+7.2f}   p50 {1e4*LVo['p50']:+6.2f}   "
                  f"p95 {1e4*LVo['p95']:+6.2f} bp   beats {LVo['beats']}  "
                  f"margin {LVo['margin_se']:+.1f} SE"
                  + ("  UNRESOLVED" if LVo["unresolved"] else ""))

    # ---------------- the bar, with T2/T3 GATED ON T1
    T1 = bool(prim["mean"] > 0)
    T2 = (bool(LV["beats"] and not LV["unresolved"]) if T1 else "not_applicable")
    T3 = ((bool(OD["beats"] and not OD["unresolved"]) if OD else False) if T1 else "not_applicable")
    d2 = rev.get(2)
    diff = prim["mean"] - d2["mean"] if d2 else float("nan")
    sed = float(np.hypot(prim["se"], d2["se"])) if d2 else float("nan")
    T4 = bool(d2 and diff > 2 * sed)
    print("\n  --- THE BAR (committed 6374e5c) ---")
    print(f"    T1 first-touch mean > 0        : {T1}   ({1e4*prim['mean']:+.2f} bp, "
          f"{prim['mean']/prim['se']:+.1f} SE)")
    print(f"    T2 beats LVL p95               : {T2}"
          + ("   <- T1 failed, so the control gates are NOT EVALUATED" if T2 == "not_applicable"
             else ""))
    print(f"    T3 beats ORD p95               : {T3}")
    print(f"    T4 first touch > second by 2SE : {T4}   ({1e4*diff:+.2f} bp vs 2SE {2e4*sed:.2f})")
    print(f"    R1 (separate, clears nothing)  : {R1}")

    cells = dict(primary=prim, revisit=rev, ages=ages, abs_contrast=ab)
    print("\n  --- the sweep, SHAPE only, cannot clear (R14) ---")
    for what, val in SWEEP:
        dl, lf, hh = DELTA, LIFE, H
        if what == "delta":
            dl = val
        elif what == "life":
            lf = val
        else:
            hh = val
        B = Z4.run_arm(P, atr, "dep", THETA, lf, hh, delta=dl)
        st = Z4.arm_stats(B["r"], B["good"]) if B else None
        cells[f"dep_d{dl}_L{lf}_h{hh}"] = st
        if st:
            print(f"  delta={dl}  life={lf:3d}  h={hh:2d}   n {st['n']:7,}   "
                  f"mean {1e4*st['mean']:+7.2f} bp +-{1e4*st['se']:.2f}   "
                  f"{st['mean']/st['se']:+.1f} SE")

    clears = bool(T1 and T2 is True and T3 is True and T4)
    print(f"\n  VERDICT: {'CLEARS' if clears else 'FAILS'}   R1 {R1}")
    OUT.write_text(json.dumps(dict(
        primary=dict(delta=DELTA, theta=THETA, life=LIFE, h=H),
        bar=dict(T1=T1, T2=T2, T3=T3, T4=T4, clears=clears), R1=R1,
        dist=dd, stage0=dict(P1=p1, P2=p2, P3=p3, P4=p4, gate_worked=gate_worked),
        nulls=dict(lvl=LV, ord=OD, lvl_oldest=LVo), cells=cells,
        t4=dict(diff=diff, se=sed)), indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")
    return clears


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()
