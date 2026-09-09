"""D411 SCREEN -- signed volume at price. The bar was committed in f0a8a14 BEFORE this ran.

    uv run python scripts/run_d411_signed_volume_at_price.py --stage0
    uv run python scripts/run_d411_signed_volume_at_price.py --screen

A PRE-SCREEN, not a study. Nothing is scored into a book. D263's inversion.

THE CONSTRUCTION (record section 3), and it has NO GRID AND NO BANDWIDTH:
  sign_u = 2*(C-L)/(H-L) - 1                 close's position in its OWN range
  each bar spreads sign_u * v_u UNIFORMLY over [L_u, H_u], so the quantity resting in any
  interval is exact overlap arithmetic. D405's FP scalar turned out to be grid noise; a
  construction without a grid cannot fail that way.
  D_below = SUM max(sign,0) * v * overlap(u, [P-b, P))
  S_above = SUM max(-sign,0) * v * overlap(u, (P, P+b])
  I = (D_below - S_above) / (D_below + S_above)

THE BAR, from the record section 4, unchanged, WITH THE DIRECTION DECLARED IN ADVANCE
(high I predicts HIGHER forward return):
  T1  mean forward return monotone INCREASING across Q1->Q5, spread > 0
  T2  outside the p95 of the within-day permutation null
  T3  outside the p95 of VOL-SHUF
  T4  the signed spread is at least 1.5x the UNSIGNED spread   <- decides if this is a new object
  G4  corr(I, trailing 20d return); above 0.5 the raw arm is a momentum restatement whatever it
      scores, and I_perp (residualised on trailing return and log price) is the arm that can carry
      information. BOTH DECLARED IN ADVANCE.

DAILY ONLY. There is no 15m arm and there will not be one: D403's [ALIGN] put ServiceNow's map at
five times its own prices, and never crossing fixtures avoids the trap entirely.
"""
import argparse
import importlib.util
import json
import os
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]

_OPENED = dict(n=0, refused=0)


def _audit(event, args):
    if event != "open":
        return
    p = args[0]
    if isinstance(p, bytes):
        p = p.decode(errors="replace")
    elif not isinstance(p, (str, os.PathLike)):
        return
    low = os.fspath(p).replace("\\", "/").lower()
    _OPENED["n"] += 1
    if "holdout" in low:
        _OPENED["refused"] += 1
        raise RuntimeError(f"[SPLIT] refused to open {low}")


sys.addaudithook(_audit)


def _load(name, fname):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fname)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


sys.path.insert(0, str(REPO / "src"))
RP = _load("rp", "ragged_panel.py")
X = _load("d320", "run_d320_tilt_filters.py")
UF = _load("d339", "d339_universe_floor.py")
UF.bind(X, None)

FIX = REPO / "data/fixtures/us_shorts_daily_raw.csv.gz"
EVJ = REPO / "data/fixtures/us_shorts_daily_raw_events.json"
CACHE = REPO / "temp" / "d411_panel.npz"
OUT = REPO / "data" / "d411_signed_volume_at_price.json"

W_PRIMARY, K_PRIMARY, H_PRIMARY = 100, 2.0, 5
WS = (100, 60, 250)                  # window in daily bars; 100 primary
KS = (2.0, 1.0, 4.0)                 # band half-width in ATR; 2.0 primary
HS = (5, 1, 21)                      # forward horizon; 5 primary
NQ = 5
MIN_NAMES = 50                       # per day, for quintiles to mean anything
N_PERM = 200
N_VOLSHUF = 50
T4_FACTOR = 1.5
G4_BAR = 0.50
P1_BAR = 0.95


# ------------------------------------------------------------------ the panel
def load_panel(verbose=True):
    """O/H/L/C/V on the union date grid, plus D406's eligibility mask, unchanged."""
    if CACHE.exists():
        z = np.load(CACHE, allow_pickle=True)
        if verbose:
            print(f"  panel from cache {CACHE.name}")
        return {k: z[k] for k in ("OP", "HI", "LO", "CL", "VOL", "live", "elig")} | dict(
            dates=list(z["dates"]), symbols=list(z["symbols"]))
    t0 = time.time()
    panel, cleaned = RP.load_ragged(FIX, EVJ, fee_bps=0.0)
    CL = np.ascontiguousarray(panel.closes.T)
    live = np.ascontiguousarray(panel.live.T)
    T, n = CL.shape
    OP, HI, LO, VOL = (np.full((T, n), np.nan) for _ in range(4))
    pos = {d: i for i, d in enumerate(panel.dates)}
    sym = {s: i for i, s in enumerate(panel.symbols)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                b = st.bar
                OP[t, i], HI[t, i], LO[t, i], VOL[t, i] = b.open, b.high, b.low, b.volume
    ev = json.loads(EVJ.read_text(encoding="utf-8"))
    RAWF = UF.raw_price_factor(panel, ev)
    DV = X.roll_mean_T(CL * VOL)
    elig = live & UF.floor_mask_v2(CL * RAWF, DV, live)
    if verbose:
        print(f"  panel {T} dates x {n} names in {time.time()-t0:.0f}s   "
              f"elig {100*elig.mean():.1f}% of cells")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, OP=OP, HI=HI, LO=LO, CL=CL, VOL=VOL, live=live, elig=elig,
                        dates=np.array(panel.dates), symbols=np.array(panel.symbols))
    return dict(OP=OP, HI=HI, LO=LO, CL=CL, VOL=VOL, live=live, elig=elig,
                dates=list(panel.dates), symbols=list(panel.symbols))


def shift(A, j, fill=np.nan):
    """A[t-j], so row t holds bar t-j. Rows < j are `fill`. This is the [LAG] guarantee."""
    out = np.full_like(A, fill)
    if j < A.shape[0]:
        out[j:] = A[:-j]
    return out


def roll_mean(A, W):
    """CAUSAL trailing mean over W bars ENDING AT t-1 -- the current bar never enters."""
    fin = np.isfinite(A)
    Z = np.where(fin, A, 0.0)
    cs = np.cumsum(Z, axis=0)
    cn = np.cumsum(fin, axis=0)
    out = np.full_like(A, np.nan)
    num = cs[W:] - cs[:-W]
    den = (cn[W:] - cn[:-W]).astype(float)
    out[W + 1:] = np.where(den[:-1] > 0, num[:-1] / np.maximum(den[:-1], 1), np.nan)
    return out


# ------------------------------------------------------------------ the field
def bar_sign(P):
    """2*(C-L)/(H-L) - 1. Zero-range bars contribute NOTHING -- they are halts and stub prints."""
    rng = P["HI"] - P["LO"]
    ok = np.isfinite(rng) & (rng > 0) & np.isfinite(P["VOL"]) & (P["VOL"] > 0)
    s = np.zeros_like(rng)
    np.divide(2.0 * (P["CL"] - P["LO"]), rng, out=s, where=ok)
    return np.where(ok, s - 1.0, 0.0), ok


def _field_inputs(P, W, signed, VOL):
    V = P["VOL"] if VOL is None else VOL
    sgn, ok = bar_sign(P)
    ok = ok & np.isfinite(V) & (V > 0)
    vbar = roll_mean(np.where(ok, V, np.nan), W)
    v = np.where(ok & np.isfinite(vbar) & (vbar > 0), V / np.maximum(vbar, 1e-12), 0.0)
    tr = np.maximum(P["HI"], shift(P["CL"], 1)) - np.minimum(P["LO"], shift(P["CL"], 1))
    atr = roll_mean(tr, W)
    wb = v if not signed else np.maximum(sgn, 0.0) * v
    wa = v if not signed else np.maximum(-sgn, 0.0) * v
    return v, atr, wb, wa


def _imbalance_ref(P, W, k, signed=True, VOL=None):
    """THE LOOP THE FAST PATH REPLACED. Kept so the rewrite is guarded by equality, not by
    inspection -- CLAUDE.md. Materialises a shifted copy of four (T,n) arrays per lag."""
    v, atr, wb_all, wa_all = _field_inputs(P, W, signed, VOL)
    Pc = P["CL"]
    b = k * atr
    a, c = Pc - b, Pc + b
    Db = np.zeros_like(Pc)
    Sa = np.zeros_like(Pc)
    for j in range(1, W + 1):
        Lj, Hj = shift(P["LO"], j), shift(P["HI"], j)
        w = Hj - Lj
        inv = np.where(np.isfinite(w) & (w > 0), 1.0 / np.where(w > 0, w, 1.0), 0.0)
        ovb = np.clip(np.minimum(Hj, Pc) - np.maximum(Lj, a), 0.0, None) * inv
        ova = np.clip(np.minimum(Hj, c) - np.maximum(Lj, Pc), 0.0, None) * inv
        Db += np.nan_to_num(shift(wb_all, j, 0.0) * ovb)
        Sa += np.nan_to_num(shift(wa_all, j, 0.0) * ova)
    tot = Db + Sa
    I = np.where(tot > 0, (Db - Sa) / np.maximum(tot, 1e-12), np.nan)
    I[~np.isfinite(atr)] = np.nan
    return I, Db, Sa


def imbalance(P, W, k, signed=True, VOL=None, verbose=False):
    """I = (D_below - S_above)/(D_below + S_above), read from bars u <= t-1 only.

    `signed=False` is TERRAIN's volume node rebuilt in this runner: the SAME geometry with the
    sign dropped, so T4 compares like with like.

    THE ONLY OPTIMISATION IS HOISTING AND NOT MATERIALISING. Row t reads lag j at row t-j, which
    is the SLICE A[:-j] against Pc[j:] -- so the four shifted copies per lag become views and the
    NaN fill disappears. `inv` is hoisted out of the lag loop; it never depended on j. The
    multiplication ORDER is untouched (`w * (raw * inv)`), so `--verify` holds bit-identity
    against `_imbalance_ref` rather than to a tolerance."""
    t0 = time.time()
    v, atr, wb_all, wa_all = _field_inputs(P, W, signed, VOL)
    Pc = P["CL"]
    b = k * atr
    a, c = Pc - b, Pc + b
    wid = P["HI"] - P["LO"]
    good = np.isfinite(wid) & (wid > 0)
    inv = np.where(good, 1.0 / np.where(good, wid, 1.0), 0.0)
    # Dead cells carry NaN in LO/HI. Their weight is already exactly 0, but NaN * 0 is NaN, and
    # `_imbalance_ref` scrubbed that with nan_to_num. Filling the geometry instead keeps every
    # lag row finite, so no scrub is needed and none is done.
    LOf = np.where(good, P["LO"], 0.0)
    HIf = np.where(good, P["HI"], 0.0)
    Db = np.zeros_like(Pc)
    Sa = np.zeros_like(Pc)
    for j in range(1, W + 1):
        Lj, Hj, ij = LOf[:-j], HIf[:-j], inv[:-j]
        P_, a_, c_ = Pc[j:], a[j:], c[j:]
        ovb = np.clip(np.minimum(Hj, P_) - np.maximum(Lj, a_), 0.0, None) * ij
        ova = np.clip(np.minimum(Hj, c_) - np.maximum(Lj, P_), 0.0, None) * ij
        Db[j:] += wb_all[:-j] * ovb
        Sa[j:] += wa_all[:-j] * ova
    tot = Db + Sa
    I = np.where(tot > 0, (Db - Sa) / np.maximum(tot, 1e-12), np.nan)
    I[~np.isfinite(atr)] = np.nan
    if verbose:
        print(f"      field W={W} k={k} signed={signed} in {time.time()-t0:.0f}s", flush=True)
    return I, Db, Sa


def fwd_logret(P, h):
    """out[t] = log C[t+h] - log C[t], GROSS, and NaN unless the name is live at t+h."""
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    T = lg.shape[0]
    out = np.full_like(lg, np.nan)
    out[:T - h] = lg[h:] - lg[:T - h]
    okf = np.zeros_like(P["live"])
    okf[:T - h] = P["live"][h:]
    out[~okf] = np.nan
    return out, lg


def trailing_ret(lg, k=20):
    out = np.full_like(lg, np.nan)
    out[k:] = lg[k:] - lg[:-k]
    return out


# ------------------------------------------------------------------ the conditional
def quintile_table(I, F, elig, perm=None, rng=None):
    """Cross-sectional quintiles of I WITHIN each day, pooled. Q1 = lowest I.

    `perm` shuffles I across names INSIDE each day -- the matched null: it holds the
    cross-section, the calendar and every forward return fixed and destroys only the ordering."""
    T = I.shape[0]
    acc = [[] for _ in range(NQ)]
    used = 0
    for t in range(T):
        m = elig[t] & np.isfinite(I[t]) & np.isfinite(F[t])
        c = int(m.sum())
        if c < MIN_NAMES:
            continue
        used += 1
        v = I[t, m]
        f = F[t, m]
        if perm:
            v = rng.permutation(v)
        q = np.quantile(v, np.linspace(0, 1, NQ + 1))
        q[-1] += 1e-12
        b = np.clip(np.searchsorted(q, v, side="right") - 1, 0, NQ - 1)
        for j in range(NQ):
            s = b == j
            if s.any():
                acc[j].append(f[s])
    if used < 100 or any(not a for a in acc):
        return None
    means = [float(np.concatenate(a).mean()) for a in acc]
    ns = [int(sum(len(x) for x in a)) for a in acc]
    pooled = float(np.concatenate([x for a in acc for x in a]).mean())
    return dict(days=used, n=ns, means=means, pooled=pooled,
                spread=means[-1] - means[0],
                monotone_inc=bool(all(means[j] <= means[j + 1] for j in range(NQ - 1))),
                monotone_dec=bool(all(means[j] >= means[j + 1] for j in range(NQ - 1))))


def perm_null(I, F, elig, n_draw, seed=0):
    """Within-day permutation of I. Returns the spread distribution."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_draw):
        t = quintile_table(I, F, elig, perm=True, rng=rng)
        out.append(t["spread"])
    return np.array(out)


def null_stats(draws, obs, higher_is_better=True):
    p5, p50, p95 = (float(np.quantile(draws, q)) for q in (.05, .5, .95))
    se = float(np.std(draws, ddof=1) / np.sqrt(len(draws)))
    edge = (obs - p95) if higher_is_better else (p5 - obs)
    return dict(n=len(draws), p5=p5, p50=p50, p95=p95, se=se, observed=obs,
                beats=bool(edge > 0), margin_se=float(edge / se) if se > 0 else float("inf"),
                unresolved=bool(abs(edge) < 2 * se))


def residualise(I, TR, LP, elig):
    """I_perp -- I cross-sectionally residualised each day on trailing return and log price.

    Causal, same-day, NO fitted parameter carried across days. Declared in section 5 of the
    record BEFORE the run, so it is not an arm invented after seeing G4."""
    R = np.full_like(I, np.nan)
    for t in range(I.shape[0]):
        m = elig[t] & np.isfinite(I[t]) & np.isfinite(TR[t]) & np.isfinite(LP[t])
        if m.sum() < MIN_NAMES:
            continue
        A = np.column_stack([np.ones(m.sum()), TR[t, m], LP[t, m]])
        y = I[t, m]
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        R[t, m] = y - A @ coef
    return R


# ------------------------------------------------------------------ assertions
def assert_QTY(P):
    """[QTY] a bar's TOTAL contribution over the whole line is exactly sign_u * v_u.

    The overlap arithmetic has no grid, so this is checkable to float error rather than to a
    tolerance chosen to make it pass."""
    rng = np.random.default_rng(1)
    lo, hi = 10.0, 12.0
    edges = np.sort(rng.uniform(5.0, 20.0, 40))
    edges = np.r_[-1e9, edges, 1e9]
    tot = 0.0
    for a, b in zip(edges[:-1], edges[1:]):
        tot += max(0.0, min(hi, b) - max(lo, a)) / (hi - lo)
    assert abs(tot - 1.0) < 1e-12, f"[QTY] partition of unity failed: {tot!r}"
    return float(abs(tot - 1.0))


def assert_SIGN(P, W=20, k=2.0):
    """[SIGN] in the direction section 4 DECLARED, and on the scalar the verdict reads.

    A bar closing on its HIGH is demand; placed BELOW the read price it must push I UP. The
    mirror in the DECLARED geometry is a bar closing on its LOW placed ABOVE, which must push
    I DOWN.

    AND IT RECORDS A PROPERTY OF THE PRE-REGISTERED CONSTRUCTION: section 3 reads only
    max(sign,0) below and max(-sign,0) above, so SUPPLY BELOW AND DEMAND ABOVE ARE INVISIBLE --
    the trapped-short and trapped-long halves of the field are discarded by design. This is
    measured here rather than asserted in prose, because the construction is committed and the
    honest thing is to report what it ignores."""
    T, n = 60, 4
    base = np.full((T, n), 100.0)
    Q = dict(OP=base.copy(), HI=base + 1.0, LO=base - 1.0, CL=base.copy(),
             VOL=np.full((T, n), 1e6), live=np.ones((T, n), bool))
    Q["elig"] = Q["live"]
    # A PERFECTLY NEUTRAL NAME HAS AN EMPTY FIELD -- every bar signs to exactly 0, so
    # D_below = S_above = 0 and I is undefined. That is a real property of the construction and
    # it is why the baseline alternates +-0.2 rather than sitting at the midpoint.
    Q["CL"][0::2] = 100.2
    Q["CL"][1::2] = 99.8
    # 0: baseline. 1: demand BELOW. 2: supply ABOVE. 3: supply BELOW -- the discarded half.
    u = T - 5
    Q["LO"][u, 1], Q["HI"][u, 1], Q["CL"][u, 1] = 97.0, 99.0, 99.0     # on its HIGH, below
    Q["LO"][u, 2], Q["HI"][u, 2], Q["CL"][u, 2] = 101.0, 103.0, 101.0  # on its LOW, above
    Q["LO"][u, 3], Q["HI"][u, 3], Q["CL"][u, 3] = 97.0, 99.0, 97.0     # on its LOW, below
    Q["VOL"][u, 1:] = 5e7
    I, Db, Sa = imbalance(Q, W, k)
    t = T - 1
    assert I[t, 1] > I[t, 0] + 1e-9, f"[SIGN] demand below did not raise I: {I[t,1]} vs {I[t,0]}"
    assert I[t, 2] < I[t, 0] - 1e-9, f"[SIGN] supply above did not lower I: {I[t,2]} vs {I[t,0]}"
    return dict(baseline=float(I[t, 0]), demand_below=float(I[t, 1]),
                supply_above=float(I[t, 2]), supply_below=float(I[t, 3]),
                supply_below_is_invisible=bool(abs(I[t, 3] - I[t, 0]) < 0.1 * abs(
                    I[t, 1] - I[t, 0])))


def assert_LAG(P, W, k, n_probe=40, seed=7):
    """[LAG] re-derive I in a SECOND implementation that never calls `imbalance`, with an
    explicit loop over u in [t-W, t-1] -- and prove the current bar is absent from its own field."""
    I, _, _ = imbalance(P, W, k)
    rng = np.random.default_rng(seed)
    ts, iss = np.where(np.isfinite(I) & P["elig"])
    pick = rng.choice(len(ts), size=min(n_probe, len(ts)), replace=False)
    worst = 0.0
    sgn, ok = bar_sign(P)
    vbar = roll_mean(np.where(ok, P["VOL"], np.nan), W)
    tr = np.maximum(P["HI"], shift(P["CL"], 1)) - np.minimum(P["LO"], shift(P["CL"], 1))
    atr = roll_mean(tr, W)
    for p in pick:
        t, i = int(ts[p]), int(iss[p])
        Pc = P["CL"][t, i]
        b = k * atr[t, i]
        db = sa = 0.0
        for u in range(t - W, t):                      # u <= t-1, STRICTLY
            H, L = P["HI"][u, i], P["LO"][u, i]
            if not (np.isfinite(H) and np.isfinite(L) and H > L):
                continue
            if not (np.isfinite(vbar[u, i]) and vbar[u, i] > 0):
                continue
            v = P["VOL"][u, i] / vbar[u, i]
            s = 2.0 * (P["CL"][u, i] - L) / (H - L) - 1.0
            db += max(s, 0.0) * v * max(0.0, min(H, Pc) - max(L, Pc - b)) / (H - L)
            sa += max(-s, 0.0) * v * max(0.0, min(H, Pc + b) - max(L, Pc)) / (H - L)
        ref = (db - sa) / max(db + sa, 1e-12) if db + sa > 0 else np.nan
        if np.isfinite(ref):
            worst = max(worst, abs(ref - I[t, i]))
    assert worst < 1e-9, f"[LAG] second implementation disagrees by {worst:.3e}"
    return float(worst)


# ------------------------------------------------------------------ stage 0
def stage0(P, verbose=True):
    """The premise checks. P1 and P2 can end the screen on their own."""
    out = {}
    sgn, ok = bar_sign(P)
    m = ok & P["elig"]
    co = (P["CL"] - P["OP"]) / np.where(P["OP"] > 0, P["OP"], np.nan)
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    r = np.full_like(lg, np.nan)
    r[1:] = lg[1:] - lg[:-1]

    # ---- P1: is close-in-range signing just the day's own return?
    def cc(a, b, mask):
        k = mask & np.isfinite(a) & np.isfinite(b)
        return float(np.corrcoef(a[k], b[k])[0, 1]), int(k.sum())

    c_co, n1 = cc(sgn, co, m)
    c_r, _ = cc(sgn, r, m)
    c_sgn_co, _ = cc(np.sign(sgn), np.sign(co), m)
    out["P1"] = dict(corr_sign_vs_close_open=c_co, corr_sign_vs_logret=c_r,
                     corr_of_signs=c_sgn_co, n=n1, bar=P1_BAR,
                     is_d269_control=bool(max(abs(c_co), abs(c_r)) > P1_BAR))
    if verbose:
        print(f"  P1  corr(sign, (C-O)/O)      {c_co:+.4f}      n {n1:,}")
        print(f"      corr(sign, log return)   {c_r:+.4f}")
        print(f"      corr of the SIGNS only   {c_sgn_co:+.4f}")
        print(f"      bar {P1_BAR}  ->  " + ("IS D269's contaminated control -- the screen stops"
                                             if out["P1"]["is_d269_control"] else
                                             "not the same object as the day's own return"))
    if out["P1"]["is_d269_control"]:
        return out

    # ---- the field, primary cell
    I, Db, Sa = imbalance(P, W_PRIMARY, K_PRIMARY, verbose=verbose)
    U, _, _ = imbalance(P, W_PRIMARY, K_PRIMARY, signed=False, verbose=verbose)

    # ---- P2: is it a new object at all?
    c_iu, n2 = cc(I, U, P["elig"])
    out["P2"] = dict(corr_signed_vs_unsigned=c_iu, n=n2)
    if verbose:
        print(f"\n  P2  corr(I, unsigned)        {c_iu:+.4f}      n {n2:,}")

    # ---- P3: persistence of the conditioner itself
    ac = []
    for k in (1, 5, 21):
        a = I[:-k][P["elig"][:-k] & P["elig"][k:]]
        b = I[k:][P["elig"][:-k] & P["elig"][k:]]
        f = np.isfinite(a) & np.isfinite(b)
        ac.append(float(np.corrcoef(a[f], b[f])[0, 1]))
    hl = float(np.log(0.5) / np.log(ac[0])) if 0 < ac[0] < 1 else float("inf")
    out["P3"] = dict(ac1=ac[0], ac5=ac[1], ac21=ac[2], half_life_bars=hl)
    if verbose:
        print(f"  P3  autocorr of I  1/5/21    {ac[0]:+.4f} {ac[1]:+.4f} {ac[2]:+.4f}   "
              f"half-life {hl:.1f} bars")

    # ---- G4: the TERRAIN gate
    tr20 = trailing_ret(lg, 20)
    c_g4, n4 = cc(I, tr20, P["elig"])
    out["G4"] = dict(corr_I_trailing20=c_g4, n=n4, bar=G4_BAR,
                     fires=bool(abs(c_g4) > G4_BAR))
    if verbose:
        print(f"  G4  corr(I, trailing 20d)    {c_g4:+.4f}      n {n4:,}")
        print(f"      bar {G4_BAR}  ->  " + ("FIRES -- the raw arm is a momentum restatement "
                                             "whatever it scores" if out["G4"]["fires"] else
                                             "does NOT fire -- I is not a restatement of "
                                             "recent price"))

    # ---- P4: LOOK AT THE OBJECT. Reporting a statistic without inspecting the
    #      construction has been my failure twice.
    fin = I[P["elig"]]
    fin = fin[np.isfinite(fin)]
    qs = [float(np.quantile(fin, q)) for q in (0.01, .1, .25, .5, .75, .9, 0.99)]
    frac_extreme = float(np.mean(np.abs(fin) > 0.99))
    t_ex, i_ex = np.where(P["elig"] & np.isfinite(I))
    j = int(np.argmax(np.abs(I[t_ex, i_ex])))
    te, ie = int(t_ex[j]), int(i_ex[j])
    out["P4"] = dict(quantiles=qs, frac_abs_gt_099=frac_extreme,
                     example=dict(symbol=P["symbols"][ie], date=P["dates"][te],
                                  I=float(I[te, ie]), D_below=float(Db[te, ie]),
                                  S_above=float(Sa[te, ie]), close=float(P["CL"][te, ie])))
    if verbose:
        print(f"\n  P4  I quantiles 1/10/25/50/75/90/99: "
              + " ".join(f"{q:+.3f}" for q in qs))
        print(f"      |I| > 0.99 on {100*frac_extreme:.1f}% of eligible bars   "
              f"(a saturated field is a one-sided field)")
        e = out["P4"]["example"]
        print(f"      most extreme: {e['symbol']} {e['date']}  I {e['I']:+.4f}  "
              f"D_below {e['D_below']:.3f}  S_above {e['S_above']:.3f}  close {e['close']:.2f}")
    return out | dict(_I=I, _U=U, _lg=lg, _tr20=tr20)


# ------------------------------------------------------------------ the screen
def screen(quick=False):
    t0 = time.time()
    print("D411 SCREEN  signed volume at price")
    print("      the bar was committed in f0a8a14 BEFORE this ran\n")
    P = load_panel()

    print("\n  --- assertions ---")
    print(f"  [QTY]  partition of unity, error {assert_QTY(P):.1e}")
    s = assert_SIGN(P)
    print(f"  [SIGN] baseline {s['baseline']:+.4f}   demand below {s['demand_below']:+.4f}   "
          f"supply above {s['supply_above']:+.4f}")
    print(f"         supply BELOW {s['supply_below']:+.4f} -- invisible to the construction "
          f"by design: {s['supply_below_is_invisible']}")
    print(f"  [LAG]  second implementation agrees to {assert_LAG(P, 30, 2.0):.1e}")

    print("\n  --- STAGE 0 (record section 6) ---")
    s0 = stage0(P)
    if s0["P1"]["is_d269_control"]:
        OUT.write_text(json.dumps(dict(stopped_at="P1", stage0=s0), indent=1, default=float),
                       encoding="utf-8")
        print("\n  SCREEN STOPS AT P1.")
        return False
    I, U, lg, tr20 = s0.pop("_I"), s0.pop("_U"), s0.pop("_lg"), s0.pop("_tr20")
    LP = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    elig = P["elig"]

    print("\n  --- THE CONDITIONAL ---")
    Iperp = residualise(I, tr20, LP, elig)
    F = {h: fwd_logret(P, h)[0] for h in HS}
    cells = {}
    for tag, field in (("signed", I), ("unsigned", U), ("perp", Iperp)):
        for h in HS:
            c = quintile_table(field, F[h], elig)
            cells[f"{tag}_h{h}"] = c
            if c and (h == H_PRIMARY or not quick):
                print(f"  {tag:8s} h={h:2d}  " + "  ".join(f"{1e4*m:+7.1f}" for m in c["means"])
                      + f"  bp   spread {1e4*c['spread']:+7.1f} bp   inc {c['monotone_inc']}"
                      + ("   <- PRIMARY" if (tag == "signed" and h == H_PRIMARY) else ""))
    if not quick:
        print("\n  --- the sweep, SHAPE only, cannot clear (R14) ---")
        for w in WS:
            for k in KS:
                if (w, k) == (W_PRIMARY, K_PRIMARY):
                    continue
                J, _, _ = imbalance(P, w, k)
                c = quintile_table(J, F[H_PRIMARY], elig)
                cells[f"signed_W{w}_k{k}"] = c
                if c:
                    print(f"  W={w:3d} k={k:.1f}  spread {1e4*c['spread']:+7.1f} bp   "
                          f"inc {c['monotone_inc']}")

    prim = cells[f"signed_h{H_PRIMARY}"]
    assert prim is not None, "the primary cell did not populate"
    unsg = cells[f"unsigned_h{H_PRIMARY}"]

    print(f"\n  --- the nulls ---")
    pn = perm_null(I, F[H_PRIMARY], elig, N_PERM, seed=11)
    NP = null_stats(pn, prim["spread"])
    print(f"  PERM  {N_PERM} draws   observed {1e4*NP['observed']:+7.1f}   "
          f"p5 {1e4*NP['p5']:+6.1f}  p50 {1e4*NP['p50']:+6.1f}  p95 {1e4*NP['p95']:+6.1f} bp   "
          f"beats {NP['beats']}  margin {NP['margin_se']:+.1f} SE")
    rng = np.random.default_rng(23)
    vs = []
    for d in range(N_VOLSHUF):
        Vs = P["VOL"].copy()
        for i in range(Vs.shape[1]):
            m = np.isfinite(Vs[:, i])
            if m.sum() > 2:
                Vs[m, i] = rng.permutation(Vs[m, i])
        J, _, _ = imbalance(P, W_PRIMARY, K_PRIMARY, VOL=Vs)
        c = quintile_table(J, F[H_PRIMARY], elig)
        vs.append(c["spread"] if c else np.nan)
        if d == 0:
            print(f"        (VOL-SHUF draw 1 of {N_VOLSHUF} at {time.time()-t0:.0f}s)", flush=True)
    vs = np.array([x for x in vs if np.isfinite(x)])
    VS = null_stats(vs, prim["spread"])
    print(f"  VOL-SHUF {len(vs)} draws  observed {1e4*VS['observed']:+7.1f}   "
          f"p5 {1e4*VS['p5']:+6.1f}  p50 {1e4*VS['p50']:+6.1f}  p95 {1e4*VS['p95']:+6.1f} bp   "
          f"beats {VS['beats']}  margin {VS['margin_se']:+.1f} SE")

    T1 = bool(prim["monotone_inc"] and prim["spread"] > 0)
    T2 = bool(NP["beats"] and not NP["unresolved"])
    T3 = bool(VS["beats"] and not VS["unresolved"])
    T4 = bool(unsg and abs(prim["spread"]) >= T4_FACTOR * abs(unsg["spread"]))
    print("\n  --- THE BAR (committed f0a8a14) ---")
    print(f"    T1 monotone INCREASING, spread > 0 : {T1}   "
          f"({1e4*prim['spread']:+.1f} bp, inc {prim['monotone_inc']})")
    print(f"    T2 outside the permutation p95     : {T2}"
          + ("   UNRESOLVED (within 2 SE)" if NP["unresolved"] else ""))
    print(f"    T3 outside VOL-SHUF p95            : {T3}"
          + ("   UNRESOLVED (within 2 SE)" if VS["unresolved"] else ""))
    print(f"    T4 signed >= 1.5x unsigned         : {T4}   "
          f"({1e4*prim['spread']:+.1f} vs {1e4*unsg['spread']:+.1f} bp, "
          f"ratio {abs(prim['spread'])/max(abs(unsg['spread']),1e-12):.2f}x)")
    pp = cells[f"perp_h{H_PRIMARY}"]
    if pp:
        print(f"\n    I_perp (declared in advance, section 5): "
              + "  ".join(f"{1e4*m:+7.1f}" for m in pp["means"])
              + f"  bp   spread {1e4*pp['spread']:+.1f}   inc {pp['monotone_inc']}")
    if s0["G4"]["fires"]:
        print(f"    G4 FIRED at {s0['G4']['corr_I_trailing20']:+.4f} -- the raw arm above is "
              f"reported as a momentum restatement whatever it scores.")

    clears = bool(T1 and T2 and T3 and T4)
    print(f"\n  VERDICT: {'CLEARS' if clears else 'FAILS'}")
    OUT.write_text(json.dumps(dict(
        primary=dict(W=W_PRIMARY, k=K_PRIMARY, h=H_PRIMARY),
        bar=dict(T1=T1, T2=T2, T3=T3, T4=T4, clears=clears),
        nulls=dict(perm=NP, volshuf=VS), stage0=s0, cells=cells),
        indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")
    return clears


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage0", action="store_true")
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        Q = load_panel()
        for W, k, sg in ((30, 2.0, True), (60, 1.0, False), (100, 4.0, True)):
            t0 = time.time()
            A = _imbalance_ref(Q, W, k, signed=sg)[0]
            t1 = time.time()
            B = imbalance(Q, W, k, signed=sg)[0]
            t2 = time.time()
            same = np.array_equal(A, B, equal_nan=True)
            print(f"  W={W:3d} k={k} signed={sg}   ref {t1-t0:5.1f}s   fast {t2-t1:5.1f}s   "
                  f"{(t1-t0)/(t2-t1):.2f}x   BIT-IDENTICAL {same}")
            assert same, "the rewrite changed the field -- it is not an optimisation"
        F = fwd_logret(Q, H_PRIMARY)[0]
        I = imbalance(Q, W_PRIMARY, K_PRIMARY)[0]
        t0 = time.time()
        quintile_table(I, F, Q["elig"])
        print(f"  quintile_table {time.time()-t0:.2f}s  -> perm null of {N_PERM} "
              f"projects to {N_PERM*(time.time()-t0)/60:.1f} min")
    elif a.stage0:
        Q = load_panel()
        print(f"  [QTY] {assert_QTY(Q):.1e}   [SIGN] {assert_SIGN(Q)}   "
              f"[LAG] {assert_LAG(Q, 30, 2.0):.1e}")
        stage0(Q)
    elif a.screen:
        screen(quick=a.quick)
    else:
        ap.error("pass --stage0 or --screen")
