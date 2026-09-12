"""D412 SCREEN -- departure zones. The bar was committed in f48e21b BEFORE this ran.

    uv run python scripts/run_d412_departure_zones.py --stage0
    uv run python scripts/run_d412_departure_zones.py --screen

A PRE-SCREEN, not a study. D263's inversion. Nothing is scored into a book.

THE CONSTRUCTION (record section 3):
  create   |C_u - O_u| / ATR_u >= theta           zone = [L_u, H_u]
  ARM      first bar within 20 whose CLOSE is fully outside the zone; the departure DIRECTION
           sets the type (up -> demand +1, down -> supply -1), not the bar's own colour
  live     at most L bars after arming
  die      at the FIRST bar trading back in: HI >= L_u and LO <= H_u   -- consumed on contact
  resp     sign * (log C[t'+h] - log C[t']), entered at the touch bar's close.  [T+1]

THE BAR (record section 5), DIRECTION DECLARED IN ADVANCE (resp expected POSITIVE):
  T1  mean resp at first touch > 0
  T2  beats LVL's p95      <- the control D403 declared and never built
  T3  beats ORD's p95
  T4  first touch exceeds the second by more than 2 SE of the difference

EVERY CONTROL NAMES WHAT IT DESTROYS AND WHAT IT KEEPS, because D411's VOL-SHUF preserved the very
sign it was meant to test and the inference stated for it was wrong:
  LVL  destroys the LEVEL, keeps name, calendar, arming bar, and the (width, distance) PAIR --
       permuted across zones, so the joint geometry distribution is preserved EXACTLY, not merely
       approximately. [MATCH] is then true by construction and is asserted anyway.
  ORD  destroys the DISPLACEMENT, keeps the machine.
  ABS  swaps departure for its opposite (D407's absorption bars). CONTRAST ARM, CANNOT CLEAR.
  REV2/3 destroys FRESHNESS, keeps the level.
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
_s.loader.exec_module(D)                   # installs the [SPLIT] holdout guard; D412 adds no unlock

OUT = REPO / "data" / "d412_departure_zones.json"

THETA, LIFE, H_PRIMARY = 1.0, 60, 5
THETAS, LIVES, HS = (1.0, 0.75, 1.5), (60, 20, 120), (5, 1, 21)
ARM_MAX = 20                 # a candidate that has not departed within 20 bars is discarded
ATR_W = 20
N_DRAW = 200
MIN_EVENTS = 2000


def atr_of(P, w=ATR_W):
    pc = D.shift(P["CL"], 1)
    tr = np.maximum(P["HI"], pc) - np.minimum(P["LO"], pc)
    return D.roll_mean(tr, w)


def gather(A, rows, cols, T):
    """A[rows, cols] with out-of-panel rows clipped and reported, so no wraparound is possible."""
    ok = (rows >= 0) & (rows < T)
    return np.where(ok, A[np.clip(rows, 0, T - 1), cols], np.nan), ok


def build_zones(P, cand, atr, life, verbose=False, delta=0.0):
    """Candidates -> ARMED zones. Returns a flat event table; every field is causal.

    `delta` is D413's distance gate (f48e21b is D412's record; 6374e5c is D413's): the close must
    clear the zone by delta * ATR, measured at the CREATION bar, not merely sit outside it.

    delta = 0.0 IS D412's RULE EXACTLY. The pad is then a scalar zero rather than `0 * atr`, so a
    bar whose ATR is still NaN behaves as it did before this parameter existed -- `C > H + NaN`
    would be False and would have silently changed D412's committed result."""
    T, n = P["CL"].shape
    u, i = np.where(cand)
    if verbose:
        print(f"      candidates {len(u):,}")
    lo_z, hi_z = P["LO"][u, i], P["HI"][u, i]
    # ---- arming: first bar within ARM_MAX whose CLOSE clears the zone by delta * ATR
    pad = 0.0 if delta == 0 else delta * atr[u, i]
    hi_a, lo_a = hi_z + pad, lo_z - pad
    off = np.arange(1, ARM_MAX + 1)
    rows = u[:, None] + off[None, :]
    cols = np.repeat(i[:, None], ARM_MAX, axis=1)
    Cw, okw = gather(P["CL"], rows, cols, T)
    out = ((Cw > hi_a[:, None]) | (Cw < lo_a[:, None])) & okw
    armed = out.any(axis=1)
    k = np.argmax(out, axis=1)
    a = u + 1 + k
    keep = armed & (a < T)
    u, i, lo_z, hi_z, a = u[keep], i[keep], lo_z[keep], hi_z[keep], a[keep]
    Ca = P["CL"][a, i]
    side = np.where(Ca > hi_z, 1, -1)              # departure UP -> demand; DOWN -> supply
    # distance from price at arming to the near edge of the zone, and the zone's width
    dist = np.where(side > 0, Ca - hi_z, lo_z - Ca)
    wid = hi_z - lo_z
    at = atr[a, i]
    ok = np.isfinite(at) & (at > 0) & (dist > 0) & (wid > 0) & P["elig"][a, i] & P["elig"][u, i]
    # atr_u is the ATR the ARMING RULE used (measured at the creation bar). [DIST] must read the
    # same quantity the gate read; dividing by atr[a] instead compares against a different number
    # and fires spuriously whenever volatility moved between creation and arming.
    return dict(u=u[ok], i=i[ok], lo=lo_z[ok], hi=hi_z[ok], a=a[ok], side=side[ok],
                dist=dist[ok], wid=wid[ok], Ca=Ca[ok], atr=at[ok], atr_u=atr[u, i][ok])


def touch_windows(P, Z, life):
    """Gather the HI/LO windows ONCE. They depend only on (name, arming bar), which no control
    changes -- so all 200 LVL draws reuse them and only the band moves."""
    T = P["CL"].shape[0]
    off = np.arange(1, life + 1)
    rows = Z["a"][:, None] + off[None, :]
    cols = np.repeat(Z["i"][:, None], life, axis=1)
    HIw, ok = gather(P["HI"], rows, cols, T)
    LOw, _ = gather(P["LO"], rows, cols, T)
    return HIw, LOw, ok, rows, cols


def touches(HIw, LOw, ok, lo_b, hi_b, which=0):
    """Index (into the window) of the (which+1)-th bar trading into [lo_b, hi_b]; -1 if none."""
    hit = (HIw >= lo_b[:, None]) & (LOw <= hi_b[:, None]) & ok
    if which == 0:
        # The first touch needs no cumsum -- argmax IS the first True. The LVL null calls this
        # 200 times on a 15.7M-cell window, so the cumsum it does not do is the run's largest
        # single cost.
        has = hit.any(axis=1)
        return np.where(has, np.argmax(hit, axis=1), -1), has
    cs = np.cumsum(hit, axis=1)
    want = (cs == which + 1) & hit
    has = want.any(axis=1)
    idx = np.where(has, np.argmax(want, axis=1), -1)
    return idx, has


def response(P, Z, rows, idx, has, side, h):
    """resp = side * (log C[t'+h] - log C[t']), entered at the TOUCH BAR'S CLOSE."""
    T = P["CL"].shape[0]
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    n = len(side)
    tt = np.where(has, rows[np.arange(n), np.clip(idx, 0, rows.shape[1] - 1)], -1)
    okt = has & (tt >= 0) & (tt + h < T)
    ii = Z["i"]
    a0 = np.where(okt, lg[np.clip(tt, 0, T - 1), ii], np.nan)
    a1 = np.where(okt, lg[np.clip(tt + h, 0, T - 1), ii], np.nan)
    liv = np.zeros(n, bool)
    liv[okt] = P["live"][np.clip(tt + h, 0, T - 1)[okt], ii[okt]] & P["elig"][tt[okt], ii[okt]]
    r = side * (a1 - a0)
    good = okt & liv & np.isfinite(r)
    return r, good, tt


def arm_stats(r, good):
    x = r[good]
    if x.size < MIN_EVENTS:
        return None
    return dict(n=int(x.size), mean=float(x.mean()), median=float(np.median(x)),
                se=float(x.std(ddof=1) / np.sqrt(x.size)),
                win=float((x > 0).mean()))


# ------------------------------------------------------------------ the controls
def lvl_null(P, Z, HIw, LOw, ok, rows, h, n_draw, seed=5):
    """LVL -- the control D403 declared and never built.

    Destroys the LEVEL. Keeps the name, the calendar, the arming bar, and the (width, distance)
    pair, which is PERMUTED ACROSS ZONES WITHIN DIRECTION -- so the joint geometry distribution is
    preserved exactly rather than approximately, and [MATCH] holds by construction.

    D273: reachability is arithmetic and any random line reproduces a monotone distance ordering.
    A departure zone that cannot beat its own geometry, relabelled onto another zone's, is that."""
    rng = np.random.default_rng(seed)
    side = Z["side"]
    out = []
    grp = {s: np.where(side == s)[0] for s in (1, -1)}
    for _ in range(n_draw):
        w2 = np.empty_like(Z["wid"])
        d2 = np.empty_like(Z["dist"])
        for s, g in grp.items():
            p = rng.permutation(g)
            w2[g], d2[g] = Z["wid"][p], Z["dist"][p]
        hi_b = np.where(side > 0, Z["Ca"] - d2, Z["Ca"] + d2 + w2)
        lo_b = np.where(side > 0, Z["Ca"] - d2 - w2, Z["Ca"] + d2)
        idx, has = touches(HIw, LOw, ok, lo_b, hi_b)
        r, good, _ = response(P, Z, rows, idx, has, side, h)
        out.append(float(r[good].mean()) if good.sum() >= MIN_EVENTS else np.nan)
    return np.array([x for x in out if np.isfinite(x)])


def subsample_null(r, good, n_target, n_draw, seed=6):
    """ORD/ABS -- the machine ran ONCE on the whole candidate pool; a draw is a subsample to the
    real zone count, so the null's sampling variance matches the estimate it is judged against."""
    rng = np.random.default_rng(seed)
    x = r[good]
    if x.size < n_target:
        return np.array([]), x.size
    return np.array([float(rng.choice(x, n_target, replace=False).mean())
                     for _ in range(n_draw)]), x.size


def null_stats(draws, obs):
    if draws.size == 0:
        return None
    p5, p50, p95 = (float(np.quantile(draws, q)) for q in (.05, .5, .95))
    se = float(np.std(draws, ddof=1) / np.sqrt(draws.size))
    edge = obs - p95
    return dict(n=int(draws.size), p5=p5, p50=p50, p95=p95, se=se, observed=float(obs),
                beats=bool(edge > 0), margin_se=float(edge / se) if se > 0 else float("inf"),
                unresolved=bool(abs(edge) < 2 * se))


# ------------------------------------------------------------------ assertions
def assert_STATE(Z, rows, idx, has):
    """[STATE] a zone cannot be touched before it is armed, nor armed before it is created, nor
    counted twice as a FIRST touch. Asserted on the event table, not in prose."""
    assert np.all(Z["a"] > Z["u"]), "[STATE] a zone armed at or before its creation bar"
    tt = rows[np.arange(len(has)), np.clip(idx, 0, rows.shape[1] - 1)]
    assert np.all(tt[has] > Z["a"][has]), "[STATE] a touch at or before the arming bar"
    assert np.all(Z["dist"] > 0), "[STATE] a zone armed with price inside it"
    return dict(zones=int(len(Z["u"])), touched=int(has.sum()))


def assert_SIGN(h=5):
    """[SIGN] in money and in the DECLARED direction, on the scalar the gate reads.

    A demand zone touched and then followed by a RISE must pay positively; a supply zone touched
    and followed by a FALL must ALSO pay positively, because the response is sign-adjusted."""
    T, n = 200, 2
    CL = np.zeros((T, n))
    CL[:, 0] = 100.0
    CL[:, 1] = 100.0
    # name 0: up-departure (demand), price returns, then RISES  -> must pay +
    CL[:60, 0] = 100.0
    CL[60, 0] = 108.0                      # the displacing bar
    CL[61:70, 0] = 115.0                   # departs upward -> armed, demand
    CL[70:75, 0] = 106.0                   # returns into [100, 108] -> first touch
    CL[75:, 0] = 118.0                     # then rises
    # name 1: down-departure (supply), price returns, then FALLS -> must ALSO pay +
    CL[:60, 1] = 100.0
    CL[60, 1] = 92.0
    CL[61:70, 1] = 85.0
    CL[70:75, 1] = 94.0
    CL[75:, 1] = 82.0
    OP = np.roll(CL, 1, axis=0)
    OP[0] = CL[0]
    HI = np.maximum(OP, CL) * 1.001
    LO = np.minimum(OP, CL) * 0.999
    Q = dict(OP=OP, HI=HI, LO=LO, CL=CL, VOL=np.full((T, n), 1e6),
             live=np.ones((T, n), bool))
    Q["elig"] = Q["live"]
    at = atr_of(Q)
    d = np.abs(CL - OP) / np.where(at > 0, at, np.nan)
    cand = np.isfinite(d) & (d >= 1.0) & Q["elig"]
    Z = build_zones(Q, cand, at, LIFE)
    assert len(Z["u"]) >= 2, f"[SIGN] the synthetic produced {len(Z['u'])} zones, needs both"
    HIw, LOw, ok, rows, cols = touch_windows(Q, Z, LIFE)
    idx, has = touches(HIw, LOw, ok, Z["lo"], Z["hi"])
    r, good, tt = response(Q, Z, rows, idx, has, Z["side"], h)
    for s, tag in ((1, "demand"), (-1, "supply")):
        m = good & (Z["side"] == s)
        assert m.any(), f"[SIGN] no {tag} zone resolved"
        assert r[m].mean() > 0, f"[SIGN] {tag} zone paid {r[m].mean():+.4f}, must be positive"
    return dict(demand=float(r[good & (Z["side"] == 1)].mean()),
                supply=float(r[good & (Z["side"] == -1)].mean()))


def assert_MATCH(Z, seed=5):
    """[MATCH] a control that is not matched is not a control -- the assertion D403's missing LVL
    never had. The permutation preserves the (width, distance) joint distribution EXACTLY."""
    rng = np.random.default_rng(seed)
    worst = 0.0
    for s in (1, -1):
        g = np.where(Z["side"] == s)[0]
        if g.size < 10:
            continue
        p = rng.permutation(g)
        for real, ctrl in ((Z["wid"][g], Z["wid"][p]), (Z["dist"][g], Z["dist"][p])):
            qa = np.quantile(real, [.1, .25, .5, .75, .9])
            qb = np.quantile(ctrl, [.1, .25, .5, .75, .9])
            worst = max(worst, float(np.max(np.abs(qa - qb))))
    assert worst < 1e-9, f"[MATCH] LVL geometry does not match the real zones: {worst:.3e}"
    return worst


# ------------------------------------------------------------------ candidates
def candidates(P, atr, kind, theta=THETA):
    d = np.abs(P["CL"] - P["OP"]) / np.where(atr > 0, atr, np.nan)
    base = np.isfinite(d) & P["elig"]
    if kind == "dep":
        return base & (d >= theta), d
    if kind == "ord":
        # ORD destroys the DISPLACEMENT and keeps everything else: the bottom tercile of the
        # same statistic, on the same mask.
        cut = float(np.nanquantile(d[base], 1 / 3))
        return base & (d <= cut), d
    if kind == "abs":
        # D407's absorption statistic: heavy volume in a small range.
        vbar = D.roll_mean(np.where(np.isfinite(P["VOL"]), P["VOL"], np.nan), ATR_W)
        rng_ = (P["HI"] - P["LO"]) / np.where(atr > 0, atr, np.nan)
        ab = (P["VOL"] / np.where(vbar > 0, vbar, np.nan)) / np.where(rng_ > 0, rng_, np.nan)
        m = base & np.isfinite(ab)
        cut = float(np.nanquantile(ab[m], 0.9))
        return m & (ab >= cut), d
    raise ValueError(kind)


def run_arm(P, atr, kind, theta, life, h, verbose=False, cap=None, seed=9, delta=0.0):
    cand, _ = candidates(P, atr, kind, theta)
    if cap is not None and cand.sum() > cap:
        # ORD's pool is ~3.5x the departure pool and its windows would allocate ~1 GB. A uniform
        # random subsample bounds that without biasing the pool it draws from; the null still
        # draws the SAME event count as the estimate it judges, which is what makes the
        # sampling variance comparable.
        w = np.where(cand.ravel())[0]
        drop = np.random.default_rng(seed).choice(w, w.size - cap, replace=False)
        cand = cand.copy()
        cand.ravel()[drop] = False
    Z = build_zones(P, cand, atr, life, verbose=verbose, delta=delta)
    if len(Z["u"]) < MIN_EVENTS:
        return None
    HIw, LOw, ok, rows, cols = touch_windows(P, Z, life)
    idx, has = touches(HIw, LOw, ok, Z["lo"], Z["hi"])
    r, good, tt = response(P, Z, rows, idx, has, Z["side"], h)
    return dict(Z=Z, HIw=HIw, LOw=LOw, ok=ok, rows=rows, idx=idx, has=has,
                r=r, good=good, tt=tt, cand=int(cand.sum()))


# ------------------------------------------------------------------ stage 0
def stage0(P, atr, verbose=True):
    A = run_arm(P, atr, "dep", THETA, LIFE, H_PRIMARY, verbose=verbose)
    assert A is not None, "no departure zones built"
    Z, has = A["Z"], A["has"]
    life_used = LIFE
    age = np.full(len(has), -1)
    age[has] = A["idx"][has] + 1
    out = dict()
    out["P1"] = dict(candidates=A["cand"], armed=int(len(Z["u"])), touched=int(has.sum()),
                     expired_unrevisited=int((~has).sum()),
                     touched_within_5=float(np.mean(age[has] <= 5)),
                     age_p10=float(np.quantile(age[has], .1)),
                     age_p50=float(np.quantile(age[has], .5)),
                     age_p90=float(np.quantile(age[has], .9)),
                     resolved=int(A["good"].sum()))
    if verbose:
        p = out["P1"]
        print(f"  P1  candidates {p['candidates']:,}  armed {p['armed']:,}  "
              f"touched {p['touched']:,}  expired unrevisited {p['expired_unrevisited']:,} "
              f"({100*p['expired_unrevisited']/max(p['armed'],1):.1f}%)")
        print(f"      age at first touch  p10 {p['age_p10']:.0f}  p50 {p['age_p50']:.0f}  "
              f"p90 {p['age_p90']:.0f} bars   within 5 bars {100*p['touched_within_5']:.1f}%")
        print(f"      resolved to a response: {p['resolved']:,}")
    out["P2"] = dict(wid_atr=[float(np.quantile(Z["wid"] / Z["atr"], q)) for q in (.1, .5, .9)],
                     dist_atr=[float(np.quantile(Z["dist"] / Z["atr"], q)) for q in (.1, .5, .9)],
                     demand=int((Z["side"] == 1).sum()), supply=int((Z["side"] == -1).sum()))
    if verbose:
        print(f"  P2  width/ATR  p10/50/90 " + " ".join(f"{x:.2f}" for x in out["P2"]["wid_atr"])
              + f"   distance/ATR " + " ".join(f"{x:.2f}" for x in out["P2"]["dist_atr"]))
        print(f"      demand {out['P2']['demand']:,}   supply {out['P2']['supply']:,}")
    # P3 -- D411's G4, carried forward as standing equipment
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    tr20 = D.trailing_ret(lg, 20)
    g = A["good"]
    tv = np.full(len(g), np.nan)
    tv[g] = tr20[A["tt"][g], Z["i"][g]] * Z["side"][g]
    m = g & np.isfinite(tv)
    c = float(np.corrcoef(A["r"][m], tv[m])[0, 1])
    out["P3"] = dict(corr_resp_trailing20=c, n=int(m.sum()), fires=bool(abs(c) > 0.5))
    if verbose:
        print(f"  P3  corr(resp, signed trailing 20d at touch)  {c:+.4f}   n {out['P3']['n']:,}"
              + ("   FIRES" if out["P3"]["fires"] else ""))
    # P4 -- LOOK AT THE OBJECT
    j = int(np.where(g)[0][np.argmax(age[np.where(g)[0]])])
    out["P4"] = dict(symbol=P["symbols"][Z["i"][j]], created=P["dates"][Z["u"][j]],
                     armed=P["dates"][Z["a"][j]], touched=P["dates"][A["tt"][j]],
                     lo=float(Z["lo"][j]), hi=float(Z["hi"][j]),
                     side=int(Z["side"][j]), age=int(age[j]), resp=float(A["r"][j]))
    if verbose:
        e = out["P4"]
        print(f"  P4  oldest resolved zone: {e['symbol']}  created {e['created']}  "
              f"armed {e['armed']}  touched {e['touched']} after {e['age']} bars")
        print(f"      zone [{e['lo']:.2f}, {e['hi']:.2f}]  side {e['side']:+d}  "
              f"resp {1e4*e['resp']:+.1f} bp")
    return out, A


# ------------------------------------------------------------------ the screen
def screen(quick=False):
    t0 = time.time()
    print("D412 SCREEN  departure zones")
    print("      the bar was committed in f48e21b BEFORE this ran\n")
    P = D.load_panel()
    atr = atr_of(P)

    print("\n  --- assertions ---")
    s = assert_SIGN()
    print(f"  [SIGN] demand {1e4*s['demand']:+.1f} bp   supply {1e4*s['supply']:+.1f} bp   "
          f"both positive, in the declared direction")

    print("\n  --- STAGE 0 (record section 6) ---")
    s0, A = stage0(P, atr)
    Z = A["Z"]
    print(f"  [STATE] {assert_STATE(Z, A['rows'], A['idx'], A['has'])}")
    print(f"  [MATCH] LVL geometry quantile gap {assert_MATCH(Z):.1e}")

    prim = arm_stats(A["r"], A["good"])
    assert prim is not None, "the primary arm did not populate"
    print(f"\n  --- THE PRIMARY (theta={THETA}, life={LIFE}, h={H_PRIMARY}) ---")
    print(f"  first touch   n {prim['n']:,}   mean {1e4*prim['mean']:+7.2f} bp  "
          f"+-{1e4*prim['se']:.2f}   median {1e4*prim['median']:+.2f}   "
          f"win {100*prim['win']:.1f}%")

    # ---- T4: later revisits. Destroys FRESHNESS, keeps the level.
    rev = {}
    for w in (1, 2):
        idx2, has2 = touches(A["HIw"], A["LOw"], A["ok"], Z["lo"], Z["hi"], which=w)
        r2, g2, _ = response(P, Z, A["rows"], idx2, has2, Z["side"], H_PRIMARY)
        rev[w + 1] = arm_stats(r2, g2)
        if rev[w + 1]:
            print(f"  touch #{w+1}      n {rev[w+1]['n']:,}   mean {1e4*rev[w+1]['mean']:+7.2f} bp  "
                  f"+-{1e4*rev[w+1]['se']:.2f}")

    # ---- the controls
    print(f"\n  --- the controls ---")
    lv = lvl_null(P, Z, A["HIw"], A["LOw"], A["ok"], A["rows"], H_PRIMARY, N_DRAW)
    LV = null_stats(lv, prim["mean"])
    print(f"  LVL  {LV['n']} draws   observed {1e4*LV['observed']:+7.2f}   "
          f"p5 {1e4*LV['p5']:+6.2f}  p50 {1e4*LV['p50']:+6.2f}  p95 {1e4*LV['p95']:+6.2f} bp   "
          f"beats {LV['beats']}   margin {LV['margin_se']:+.1f} SE"
          + ("   UNRESOLVED" if LV["unresolved"] else ""))

    Ao = run_arm(P, atr, "ord", THETA, LIFE, H_PRIMARY, cap=3 * len(Z["u"]))
    od, n_ord = subsample_null(Ao["r"], Ao["good"], prim["n"], N_DRAW)
    OD = null_stats(od, prim["mean"])
    if OD:
        print(f"  ORD  {OD['n']} draws   observed {1e4*OD['observed']:+7.2f}   "
              f"p5 {1e4*OD['p5']:+6.2f}  p50 {1e4*OD['p50']:+6.2f}  p95 {1e4*OD['p95']:+6.2f} bp   "
              f"beats {OD['beats']}   margin {OD['margin_se']:+.1f} SE"
              + ("   UNRESOLVED" if OD["unresolved"] else ""))
    else:
        print(f"  ORD  pool {n_ord:,} < the {prim['n']:,} needed for a matched draw")

    Aa = run_arm(P, atr, "abs", THETA, LIFE, H_PRIMARY)
    ab = arm_stats(Aa["r"], Aa["good"]) if Aa else None
    if ab:
        print(f"  ABS  (contrast, CANNOT CLEAR)  n {ab['n']:,}  "
              f"mean {1e4*ab['mean']:+7.2f} bp +-{1e4*ab['se']:.2f}")

    # ---- the bar
    T1 = bool(prim["mean"] > 0)
    T2 = bool(LV["beats"] and not LV["unresolved"])
    T3 = bool(OD and OD["beats"] and not OD["unresolved"])
    d2 = rev.get(2)
    if d2:
        diff = prim["mean"] - d2["mean"]
        sed = float(np.hypot(prim["se"], d2["se"]))
        T4 = bool(diff > 2 * sed)
    else:
        diff = sed = float("nan")
        T4 = False
    print("\n  --- THE BAR (committed f48e21b) ---")
    print(f"    T1 first-touch mean > 0        : {T1}   ({1e4*prim['mean']:+.2f} bp, "
          f"{prim['mean']/prim['se']:+.1f} SE)")
    print(f"    T2 beats LVL p95               : {T2}")
    print(f"    T3 beats ORD p95               : {T3}")
    print(f"    T4 first touch > second by 2SE : {T4}   "
          f"({1e4*diff:+.2f} bp vs 2SE {2e4*sed:.2f})")
    if s0["P3"]["fires"]:
        print(f"    P3 FIRED at {s0['P3']['corr_resp_trailing20']:+.4f} -- reported as momentum "
              f"whatever it scores.")

    cells = dict(primary=prim, revisit=rev, abs_contrast=ab)
    if not quick:
        print("\n  --- the sweep, SHAPE only, cannot clear (R14) ---")
        for th in THETAS:
            for lf in LIVES:
                for h in HS:
                    if (th, lf, h) == (THETA, LIFE, H_PRIMARY):
                        continue
                    if sum(x != y for x, y in ((th, THETA), (lf, LIFE), (h, H_PRIMARY))) > 1:
                        continue
                    B = run_arm(P, atr, "dep", th, lf, h)
                    st = arm_stats(B["r"], B["good"]) if B else None
                    cells[f"dep_th{th}_L{lf}_h{h}"] = st
                    if st:
                        print(f"  theta={th}  life={lf:3d}  h={h:2d}   n {st['n']:7,}   "
                              f"mean {1e4*st['mean']:+7.2f} bp  +-{1e4*st['se']:.2f}")

    clears = bool(T1 and T2 and T3 and T4)
    print(f"\n  VERDICT: {'CLEARS' if clears else 'FAILS'}")
    OUT.write_text(json.dumps(dict(
        primary=dict(theta=THETA, life=LIFE, h=H_PRIMARY),
        bar=dict(T1=T1, T2=T2, T3=T3, T4=T4, clears=clears),
        nulls=dict(lvl=LV, ord=OD), stage0=s0, cells=cells,
        t4=dict(diff=diff, se=sed)), indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")
    return clears


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage0", action="store_true")
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    P = D.load_panel()
    atr = atr_of(P)
    if a.stage0:
        print(f"  [SIGN] {assert_SIGN()}")
        s0, A = stage0(P, atr)
        print(f"  [STATE] {assert_STATE(A['Z'], A['rows'], A['idx'], A['has'])}")
        print(f"  [MATCH] {assert_MATCH(A['Z']):.1e}")
    elif a.screen:
        screen(quick=a.quick)
    else:
        ap.error("pass --stage0 or --screen")
