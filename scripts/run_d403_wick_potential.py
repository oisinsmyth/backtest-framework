"""D403 -- the wick-stack potential map, built on daily bars and read at 15 minutes.

    uv run python scripts/run_d403_wick_potential.py --audit
    uv run python scripts/run_d403_wick_potential.py --run --groups g1
    uv run python scripts/run_d403_wick_potential.py --run --groups g1,g2
    uv run python scripts/run_d403_wick_potential.py --run --groups g3        (confirmation)

DESCRIPTIVE MEASUREMENT. No position is taken, nothing is scored, nothing is admitted.
Pre-registration 7860c21, amended 95dad11, both predate the runs they govern (R8).

Each daily candle contributes a supply zone [max(O,C), H] and a demand zone [L, min(O,C)].
AMENDMENT 95dad11 -- the principal's ruling after section 5.1 showed the bare stack is a
comb of ~96 teeth, not a potential: each zone is CLAMPED AT HEIGHT ONE across its own span
and a DISTRIBUTION TAKES OVER FROM THE EDGE, so overlapping wicks pool. Equivalently

    K_i(p) = g(dist(p, [a_i, b_i])),   g(0) = 1

since the distance to an interval is zero inside it. Stack additively over W trailing daily
bars, subtract the valley floor between the two peaks, clamp at zero, read at 15 minutes.

THE SIXTH LOOK AT A PRICE-LEVEL MAP. TERRAIN (259 looks) closed terminal, STRUCTURE (86)
closed, D272/D273 closed, the density line retired. The R13 ledger transfers, and TERRAIN's
mechanism -- the map is not uninformative, it is RELIABLY WRONG -- is carried as a
pre-registered prediction in section 5.6, measured here as `terrain_prediction`.
"""
import argparse
import importlib.util
import json
import os
import pathlib
import random
import sys
import time
from collections import Counter

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]

# ------------------------------------------------- [SPLIT] default-deny holdout guard
# Registered BEFORE any import so this hook fires first and its counter is the one that
# moves; D387's identical hook is installed underneath it when d388 loads, and two
# refusing hooks are strictly safer than one.
_OPENED = dict(n=0, refused=0, holdout=Counter())


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
        _OPENED["holdout"][low] += 1
        raise RuntimeError(f"[SPLIT] refused to open {low}")


sys.addaudithook(_audit)                     # D403 NEVER calls allow_holdout. There is no unlock.


def _load(name, fname):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fname)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


sys.path.insert(0, str(REPO / "src"))
D388 = _load("d388", "run_d388_rare_event_levels.py")   # pulls d387, which installs its own guard
D387 = D388.D
RP, FN = D387.RP, D387.FN
X = _load("d320", "run_d320_tilt_filters.py")           # keep_mask, roll_mean_T
UF = _load("d339", "d339_universe_floor.py")            # the universe floor
UF.bind(X, None)                                        # only floor_mask needs _X; gate_starved is never called

from backtest_framework.research.terrain_swing import _is_swing_bars   # noqa: E402  the pinned pivot definition

FIX_D = REPO / "data/fixtures/us_shorts_daily_raw.csv.gz"
EVJ_D = REPO / "data/fixtures/us_shorts_daily_raw_events.json"
FIX_I = REPO / "data/fixtures/cohort4_intraday_15m_raw.csv.gz"
OUT = REPO / "data" / "d403_wick_potential.json"
CACHE = REPO / "temp" / "d403_cache"

POOL_SEED = 20260828          # the programme's pinned seed; never a new shuffle
END_DATE = "2023-12-31"       # D383 reserves 2024+
WINDOWS = (100, 50, 200)      # W=100 is the principal's; 50 and 200 are shape (R14)
KERNELS = ("gauss", "exp", "tri")
CS = (0.25, 0.5, 1.0, 2.0)    # h = c * ATR over the map's own window
PRIMARY = dict(W=100, kind="gauss", c=0.5)
GRID_N = 601                  # [GRID] re-runs the object at 2x this and requires agreement
PAD = 8.0                     # grid half-span beyond the zones, in h; exp(-8) = 3.4e-4 of mass
QS = (0.5, 0.7, 0.9)          # barrier quantiles
HOLDS = (4, 8, 26)            # forward horizons in 15m bars; 26 = one session
SWING_KS = (2, 3)             # terrain_swing.SWING_K, reused not re-chosen
KS = D388.KS                  # {"move": (2.0, 2.5), "reversal": (1.0, 1.5)}
HL_VOL_I = 60                 # EW sigma half-life on the 15m clock
MIN_SESSIONS = 400
BASE_RATE_FLAG = 0.20         # [BASE] shouts above this
OCC_BINS = 10


# =====================================================================  the object
def zones_of(o, h, l, c):
    """The two wick spans per bar. Zero-width zones (no upper wick) contribute NOTHING
    rather than being widened to a minimum -- section 3.3."""
    bt, bb = np.maximum(o, c), np.minimum(o, c)
    lo = np.concatenate([bt, l])
    hi = np.concatenate([h, bb])
    ok = np.isfinite(lo) & np.isfinite(hi) & (hi > lo)
    return lo[ok], hi[ok]


def atr_of(h, l, c):
    """Average true range over the map's own window. CAUSAL by construction -- the window
    is D-W..D-1 -- and the unit h is expressed in. Never a fixed percentage, which is
    D387's error, and never estimated from the whole sample, which is D384's."""
    tr = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    tr = tr[np.isfinite(tr)]
    return float(tr.mean()) if tr.size else np.nan


def tail(d, hbw, kind):
    """g(0) = 1, decaying in the distance from the zone edge."""
    if kind == "gauss":
        return np.exp(-0.5 * (d / hbw) ** 2)
    if kind == "exp":
        return np.exp(-d / hbw)
    if kind == "tri":
        return np.maximum(1.0 - d / hbw, 0.0)
    raise ValueError(kind)


def tail_mass(hbw, kind):
    """Analytic mass of the two tails of ONE zone, beyond its plateau. [QTY] compares the
    grid integral to (summed zone width) + n_zones * this, so the check is against a closed
    form rather than against the same code that produced the field."""
    if kind == "gauss":
        return hbw * np.sqrt(2.0 * np.pi)          # 2 * integral_0^inf exp(-d^2/2h^2)
    if kind == "exp":
        return 2.0 * hbw                            # 2 * integral_0^inf exp(-d/h)
    return hbw                                      # 2 * integral_0^h (1 - d/h)


def field(lo, hi, hbw, kind, x):
    """M_raw on the grid `x`: sum over zones of g(distance to the zone).

    dist(p, [a,b]) = max(a-p, 0, p-b), which is 0 inside, so the clamped plateau of height
    one and the tail beyond the edge are the SAME expression."""
    d = np.maximum(np.maximum(lo[:, None] - x[None, :], x[None, :] - hi[:, None]), 0.0)
    return tail(d, hbw, kind).sum(axis=0)


def build_map(lo, hi, hbw, kind, c_ref, n=GRID_N):
    """The field, its grid, the two peaks, the pedestal and M. None if a peak is undefined."""
    x = np.linspace(lo.min() - PAD * hbw, hi.max() + PAD * hbw, n)
    Mr = field(lo, hi, hbw, kind, x)
    up, dn = x > c_ref, x < c_ref
    if not up.any() or not dn.any() or Mr.max() <= 0:
        return None
    iu = np.flatnonzero(up)[np.argmax(Mr[up])]
    il = np.flatnonzero(dn)[np.argmax(Mr[dn])]
    p_u, p_l = float(x[iu]), float(x[il])
    tau = float(Mr[min(il, iu): max(il, iu) + 1].min())
    return dict(x=x, Mr=Mr, M=np.maximum(Mr - tau, 0.0), p_l=p_l, p_u=p_u, tau=tau,
                c_ref=float(c_ref), n_zones=int(lo.size), width=float((hi - lo).sum()))


def read_M(m, p):
    """M at prices `p`. Linear interpolation on the field's own grid; zero outside it."""
    return np.interp(p, m["x"], m["M"], left=0.0, right=0.0)


def modes_of(v):
    """Strict local maxima of a sampled field, plateaus counted once."""
    w = v[np.concatenate([[True], np.diff(v) != 0])]
    if w.size < 3:
        return int(w.size > 0)
    return int(((w[1:-1] > w[:-2]) & (w[1:-1] > w[2:])).sum()) + int(w[0] > w[1]) + int(w[-1] > w[-2])


# =====================================================================  15m events
def swings_vec(h, l, k, sign):
    """Vectorised strict-and-unique k-bar fractal. Asserted bit-identical to
    terrain_swing._is_swing_bars by assert_PIVOT on a TIE-HEAVY input, which is where a
    rewrite disagrees."""
    x = h if sign > 0 else l
    n = x.size
    out = np.zeros(n, bool)
    if n < 2 * k + 1:
        return out
    W = np.lib.stride_tricks.sliding_window_view(x, 2 * k + 1)
    ext = W.max(axis=1) if sign > 0 else W.min(axis=1)
    uniq = (W == ext[:, None]).sum(axis=1) == 1
    out[k: n - k] = (x[k: n - k] == ext) & uniq
    return out


def regions(x, M, q):
    """Maximal price bands with M >= q * max(M). Returns (lo_price, hi_price) pairs."""
    if M.size == 0 or M.max() <= 0:
        return []
    hot = M >= q * M.max()
    d = np.diff(hot.astype(np.int8))
    st = list(np.flatnonzero(d == 1) + 1) + ([0] if hot[0] else [])
    en = list(np.flatnonzero(d == -1) + 1) + ([hot.size - 1] if hot[-1] else [])
    return [(float(x[a]), float(x[min(b, x.size - 1)])) for a, b in zip(sorted(st), sorted(en))]


# =====================================================================  loading
def _key(*paths):
    return "%016x" % (abs(hash(tuple(int(pathlib.Path(p).stat().st_mtime_ns) for p in paths))) % (1 << 63))


def load_intraday(verbose=True):
    """(name -> session date, o, h, l, c) at 15m. Cached in temp/ keyed on the fixture's
    mtime -- CLAUDE.md's rule, so a refetched fixture invalidates it."""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"intraday_{_key(FIX_I)}.npz"
    if f.exists():
        z = np.load(f, allow_pickle=False)
        names = sorted({s.split("__")[0] for s in z.files})
        return {s: dict(date=z[s + "__d"], o=z[s + "__o"], h=z[s + "__h"],
                        l=z[s + "__l"], c=z[s + "__c"]) for s in names}
    import gzip
    t0 = time.time()
    rows = {}
    with gzip.open(FIX_I, "rt") as fh:
        hdr = next(fh).strip().split(",")
        assert hdr == ["timestamp", "symbol", "open", "high", "low", "close", "volume"], hdr
        for line in fh:
            p = line.rstrip("\n").split(",")
            rows.setdefault(p[1], []).append((p[0], float(p[2]), float(p[3]), float(p[4]), float(p[5])))
    out, save = {}, {}
    for s, v in rows.items():
        v.sort(key=lambda r: r[0])
        d = np.array([r[0][:10] for r in v])
        o = np.array([r[1] for r in v]); h = np.array([r[2] for r in v])
        l = np.array([r[3] for r in v]); c = np.array([r[4] for r in v])
        out[s] = dict(date=d, o=o, h=h, l=l, c=c)
        save[s + "__d"], save[s + "__o"], save[s + "__h"] = d, o, h
        save[s + "__l"], save[s + "__c"] = l, c
    np.savez_compressed(f, **save)
    if verbose:
        print(f"  15m parsed {sum(len(v['c']) for v in out.values()):,} bars in {time.time()-t0:.0f}s")
    return out


def build_grids(panel, cleaned, syms):
    """(n_sub, T) OHLC grids for `syms` only.

    Deliberately duplicated from d280_forecast_precheck.build_grids rather than imported,
    for the reason run_descending_ranking.py:117 gives -- the D280 files are under
    concurrent use on another branch and this study must not depend on their state --
    and restricted to the study names, which is the whole cost of the loop."""
    pos = {d: i for i, d in enumerate(panel.dates)}
    T = len(panel.dates)
    g = {c: np.full((len(syms), T), np.nan) for c in ("open", "high", "low", "close")}
    for i, s in enumerate(syms):
        for st in cleaned[s]:
            t = pos[st.timestamp[:10]]
            b = st.bar
            g["open"][i, t], g["high"][i, t] = b.open, b.high
            g["low"][i, t], g["close"][i, t] = b.low, b.close
    return g


def load_daily(syms, intraday, verbose=True):
    """Daily OHLC for `syms` IN THE 15m FIXTURE'S OWN PRICE BASIS, plus the eligibility mask.

    THE FLOOR IS COMPUTED ON THE FULL 1,573-NAME PANEL AND THEN SUBSET. keep_mask cuts the
    worst 28% of the LIVE CROSS-SECTION bar by bar; evaluated on 24 large caps it would
    drop the bottom 28% OF THOSE, which is not the universe floor at all.

    TWO BASES, DELIBERATELY. The $5 floor is defined on AS-TRADED prices, so it reads
    RAW_CLOSE = CLOSE * raw_price_factor, unchanged. The MAP must instead live in whatever
    basis the 15m prices are quoted in, and measurement showed the two fixtures do not
    share one:

        NOW    15m/daily = 0.20000 flat 2018-2025, 1.0 in 2026   (5:1 split)
        ILMN   15m/daily = 0.97276 to 2024-06,     1.0 after     (the GRAIL spinoff)
        BMY, BMRN                  = 1.00000 throughout

    So the 15m series is fully corporate-action adjusted and the daily fixture is not.
    raw_price_factor CANNOT repair this -- it knows splits only, and a spinoff is not a
    split. Using it left ServiceNow's map at five times its own prices for the whole scored
    window, which would have made every level unreachable and reported it as a fact about
    supply and demand.

    The repair is a per-session basis factor phi[u] = (15m last close) / (daily close),
    applied to bar u's own OHLC, which carries every historical bar into the 15m series'
    basis exactly. It is causal -- bar u is never later than D-1 -- and it is units, not
    information. It is measured per bar rather than smoothed: a rolling median would smear
    a 5x step over its window, and 5 bp of closing-auction noise is harmless where 10 days
    of a 5x error is not. [ALIGN] proves the residual is 1.0."""
    t0 = time.time()
    panel, cleaned = RP.load_ragged(FIX_D, EVJ_D, fee_bps=0.0)     # assert_gates_passed lives in here
    missing = [s for s in syms if s not in panel.symbols]
    assert not missing, f"[UNI] study names absent from the daily fixture: {missing}"
    CLOSE = np.ascontiguousarray(panel.closes.T)
    finT = np.ascontiguousarray(panel.live.T)
    VOL = np.full(CLOSE.shape, np.nan)
    sym = {s: i for i, s in enumerate(panel.symbols)}
    pos = {d: i for i, d in enumerate(panel.dates)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                VOL[t, i] = st.bar.volume
    ev = json.loads(EVJ_D.read_text(encoding="utf-8"))
    RAWF = UF.raw_price_factor(panel, ev)
    DV = X.roll_mean_T(CLOSE * VOL)
    keep1 = UF.floor_mask(CLOSE * RAWF, DV, finT)
    keep = UF.floor_mask_v2(CLOSE * RAWF, DV, finT)
    elig = finT & keep
    share = UF.floor_share(keep, finT)
    idx = [sym[s] for s in syms]
    g = build_grids(panel, cleaned, syms)
    T = len(panel.dates)
    PHI = np.full((len(syms), T), np.nan)
    steps = {}
    for a, s in enumerate(syms):
        last = {}
        for d, c in zip(intraday[s]["date"], intraday[s]["c"]):
            last[d] = c                                   # the session's final bar wins
        for d, c in last.items():
            t = pos.get(d)
            if t is not None and np.isfinite(g["close"][a, t]) and g["close"][a, t] > 0:
                PHI[a, t] = c / g["close"][a, t]
        v = PHI[a]
        ok = np.flatnonzero(np.isfinite(v))
        if ok.size:
            v[: ok[0]] = v[ok[0]]
            f = np.maximum.accumulate(np.where(np.isfinite(v), np.arange(T), 0))
            PHI[a] = v[f]
            steps[s] = sorted(set(np.round(v[ok], 3).tolist()))
    out = dict(dates=np.array(panel.dates), symbols=list(syms),
               open=g["open"] * PHI, high=g["high"] * PHI, low=g["low"] * PHI,
               close=g["close"] * PHI, phi=PHI, phi_levels=steps,
               elig=elig[:, idx].T, live=finT[:, idx].T, floor_share=share,
               CLOSE=CLOSE, VOL=VOL, RAWF=RAWF, finT=finT, DV=DV, keep=keep, keep1=keep1)
    if verbose:
        print(f"  daily loaded {time.time()-t0:.0f}s   floor rejects {100*share:.2f}% of live name-bars")
    return out


def partition():
    """Three groups, small first, by ONE shuffle of the programme's pinned seed and
    contiguous prefixes -- fetch_short_universe.py:223's idiom. random.Random, never
    hash(), which d290_direction_nulls.py:40 records as non-reproducible across
    processes."""
    import gzip
    seen = set()
    with gzip.open(FIX_I, "rt") as fh:
        next(fh)
        for line in fh:
            seen.add(line.split(",", 2)[1])
    t = sorted(seen)
    random.Random(POOL_SEED).shuffle(t)
    return {"g1": t[:4], "g2": t[4:12], "g3": t[12:]}


# =====================================================================  per-name assembly
def name_frame(daily, intraday, s):
    """Everything about one name that does not depend on (W, kernel, h)."""
    i = daily["symbols"].index(s)
    iv = intraday[s]
    sel = iv["date"] <= END_DATE
    d15, o15, h15, l15, c15 = iv["date"][sel], iv["o"][sel], iv["h"][sel], iv["l"][sel], iv["c"][sel]
    order = np.argsort(d15, kind="stable")
    d15, o15, h15, l15, c15 = d15[order], o15[order], h15[order], l15[order], c15[order]
    logp = np.log(c15)
    r = np.zeros(logp.size); r[1:] = np.diff(logp)
    sg = D388.ew_sigma(r, HL_VOL_I)               # D388's causal warm-started EW sd, unmodified
    ev = {}
    for k in SWING_KS:
        ev[f"swing_high_k{k}"] = swings_vec(h15, l15, k, +1)
        ev[f"swing_low_k{k}"] = swings_vec(h15, l15, k, -1)
    for et, ks in KS.items():
        for k in ks:
            m = np.zeros(logp.size, bool)
            m[D388.events_sigma(logp, et, k)] = True
            ev[f"{et}_{k}sig"] = m
    return dict(i=i, date=d15, o=o15, h=h15, l=l15, c=c15, sigma=sg, events=ev)


def maps_for(daily, fr, W, kind, cmul):
    """Map per session for one name. Day D uses daily bars D-W .. D-1 ONLY."""
    i = fr["i"]
    dates = daily["dates"]
    O, H, L, C = (daily[k][i] for k in ("open", "high", "low", "close"))
    live = daily["live"][i]
    ok = np.isfinite(O) & np.isfinite(H) & np.isfinite(L) & np.isfinite(C) & live
    ok &= (H > L) & (C >= L) & (C <= H)        # malformed bars MASKED, not clamped (3.3)
    dpos = {d: t for t, d in enumerate(dates)}
    out, undef = {}, 0
    for d in sorted(set(fr["date"])):
        t = dpos.get(d)
        if t is None or t < W:
            continue
        sl = slice(t - W, t)
        m = ok[sl]
        if m.sum() < W // 2 or not np.isfinite(C[t - 1]):
            continue
        o_, h_, l_, c_ = O[sl][m], H[sl][m], L[sl][m], C[sl][m]
        a = atr_of(h_, l_, c_)
        if not np.isfinite(a) or a <= 0:
            continue
        lo, hi = zones_of(o_, h_, l_, c_)
        if lo.size == 0:
            continue
        mp = build_map(lo, hi, cmul * a, kind, C[t - 1])
        if mp is None:
            undef += 1
            continue
        mp["atr"] = a
        out[d] = mp
    return out, undef


# =====================================================================  measurement
def object_dump(daily, intraday, names, W, kind, cmul, stride=5, n=GRID_N):
    """SECTION 5.1 -- the object, before any statistic. Twice in one session a test
    statistic was reported without inspecting the construction, and both times the object
    was flat. Strided over sessions: this is a shape read, not an estimate."""
    modes, peaks, pedshare, clamped, wellw, cpos, hfrac = [], [], [], [], [], [], []
    samples, undef_tot, nd = [], 0, 0
    for s in names:
        fr = name_frame(daily, intraday, s)
        mp, undef = maps_for(daily, fr, W, kind, cmul)
        undef_tot += undef
        days = sorted(mp)[::stride]
        for d in days:
            m = mp[d]
            nd += 1
            modes.append(modes_of(m["Mr"])); peaks.append(modes_of(m["M"]))
            mx = m["Mr"].max()
            pedshare.append(m["tau"] / mx if mx > 0 else 0.0)
            dx = np.diff(m["x"])
            clamped.append(float(dx[m["M"][:-1] <= 0].sum() / dx.sum()))
            wellw.append((m["p_u"] - m["p_l"]) / m["c_ref"])
            rng = m["p_u"] - m["p_l"]
            cpos.append((m["c_ref"] - m["p_l"]) / rng if rng > 0 else np.nan)
            hfrac.append(cmul * m["atr"] / m["c_ref"])
        if len(samples) < 8 and mp:
            d = sorted(mp)[len(mp) // 2]
            m = mp[d]
            samples.append(dict(symbol=s, date=d, c_ref=m["c_ref"], tau=round(m["tau"], 2),
                                max_raw=round(float(m["Mr"].max()), 2), modes=modes_of(m["Mr"]),
                                peaks=modes_of(m["M"]), p_l=round(m["p_l"], 2), p_u=round(m["p_u"], 2),
                                h_pct=round(100 * cmul * m["atr"] / m["c_ref"], 3)))
    q = lambda a: [round(float(np.nanpercentile(a, p)), 4) for p in (10, 50, 90)] if len(a) else None
    return dict(name_days=nd, grid_n=n, modes_raw=q(modes), peaks_after_pedestal=q(peaks),
                unimodal_share=float(np.mean(np.array(modes) == 1)) if modes else None,
                bimodal_or_less_share=float(np.mean(np.array(modes) <= 2)) if modes else None,
                pedestal_share_of_max=q(pedshare), axis_clamped_share=q(clamped),
                well_width_frac=q(wellw), c_ref_position_in_well=q(cpos),
                h_pct_of_price=q(hfrac), peaks_undefined=undef_tot, samples=samples)


def measure_name(daily, fr, W, kind, cmul):
    """Sections 5.2-5.6 for one name at one cell."""
    mp, undef = maps_for(daily, fr, W, kind, cmul)
    if len(mp) < MIN_SESSIONS:
        return None
    days = sorted(mp)
    dayix = {d: k for k, d in enumerate(days)}
    keep = np.array([d in dayix for d in fr["date"]])
    dd = fr["date"][keep]
    cc, hh, ll = fr["c"][keep], fr["h"][keep], fr["l"][keep]
    sg = fr["sigma"][keep]
    ev = {k: v[keep] for k, v in fr["events"].items()}
    ev["ALL_BARS"] = np.ones(cc.size, bool)
    which = np.array([dayix[d] for d in dd])
    assert np.all(np.diff(which) >= 0), "[ORD] bars are not grouped by ascending session"
    K = len(days)
    starts = np.searchsorted(which, np.arange(K))

    # ---- true alignment
    Mv = np.zeros(cc.size)
    occ_w = np.zeros(OCC_BINS)                 # axis width, in price-sigma units
    occ_v = np.zeros(OCC_BINS)                 # visits
    for k, d in enumerate(days):
        m = mp[d]
        sl = which == k
        Mv[sl] = read_M(m, cc[sl])
        mx = m["M"].max()
        if mx <= 0 or not sl.any():
            continue
        sig_px = float(np.nanmedian(sg[sl])) * m["c_ref"]
        if not np.isfinite(sig_px) or sig_px <= 0:
            continue
        dx = np.diff(m["x"])
        b = np.clip((m["M"][:-1] / mx * OCC_BINS).astype(int), 0, OCC_BINS - 1)
        occ_w += np.bincount(b, weights=dx / sig_px, minlength=OCC_BINS)
        bv = np.clip((Mv[sl] / mx * OCC_BINS).astype(int), 0, OCC_BINS - 1)
        occ_v += np.bincount(bv, minlength=OCC_BINS)

    maxM = np.array([mp[d]["M"].max() for d in days])
    den = maxM[which]
    Mfrac = np.where(den > 0, Mv / np.where(den > 0, den, 1.0), np.nan)
    obs = {k: dict(n=int(v.sum()), base_rate=float(v.mean()),
                   mean_M=float(Mv[v].mean()) if v.any() else None,
                   mean_Mfrac=float(np.nanmean(Mfrac[v])) if v.any() else None)
           for k, v in ev.items()}

    # ---- A' ENUMERATED over all K-1 offsets.
    # Flipped inside out: read map j ONCE at every bar (one interp of 39k points), then
    # scatter its per-session sums to the offset each session-map pair belongs to. The
    # naive nesting is K^2 interp CALLS; this is K, and it is the difference between 34 s
    # and 2 s per name-cell.
    keys = list(ev)
    E = np.stack([ev[k].astype(float) for k in keys])          # (n_ev, n_bars)
    acc = np.zeros((len(keys), K))
    for j, d in enumerate(days):
        v = read_M(mp[d], cc)
        seg = np.add.reduceat(E * v, starts, axis=1)           # (n_ev, K)
        for e in range(len(keys)):
            acc[e] += np.roll(seg[e][::-1], j - K + 1)         # acc[o] += seg[(j-o) % K]
    ntot = E.sum(axis=1)
    aprime = {}
    for e, k in enumerate(keys):
        a = acc[e][1:] / max(ntot[e], 1.0)                     # drop offset 0 = true alignment
        p95 = float(np.nanpercentile(a, 95))
        aprime[k] = dict(p50=float(np.nanpercentile(a, 50)), p95=p95, mean=float(np.nanmean(a)),
                         n_offsets=int(a.size),
                         obs_above_p95=bool(obs[k]["mean_M"] is not None and obs[k]["mean_M"] > p95))

    return dict(n_bars=int(cc.size), n_sessions=K, peaks_undefined=undef,
                occupancy=occupancy(occ_v, occ_w), events=obs, aprime=aprime,
                breakout=breakouts(mp, days, hh, ll, cc, which, sg),
                reject_traverse=reject_traverse(mp, days, cc, which),
                terrain_prediction=terrain_prediction(daily, fr["i"], days, mp))


def occupancy(vis, wid):
    """log occupancy PER UNIT PRICE WIDTH against M/max(M). The normalisation is the whole
    point: raw visit counts against M recover only that price visits mid-range, which is
    also where the stack is thickest."""
    ok = wid > 0
    if ok.sum() < 3:
        return None
    y = vis[ok] / wid[ok]
    x = (np.arange(OCC_BINS)[ok] + 0.5) / OCC_BINS
    good = y > 0
    if good.sum() < 3:
        return None
    b, a = np.polyfit(x[good], np.log(y[good]), 1)
    return dict(bin_centre=[round(float(v), 3) for v in x],
                visits_per_sigma=[round(float(v), 4) for v in y],
                share_of_visits=[round(float(v), 5) for v in vis[ok] / max(vis.sum(), 1)],
                slope_beta=float(b), intercept=float(a),
                monotone_decreasing=bool(np.all(np.diff(y) <= 0)),
                ratio_top_to_bottom=float(y[-1] / y[0]) if y[0] > 0 else None)


def breakouts(mp, days, hh, ll, cc, which, sg):
    """Frequency and excursion beyond each peak, CONDITIONED ON DISTANCE in daily-sigma
    units and on barrier height. D273's monotone 62.6% -> 1.3% ordering is reproduced by
    any random line, so an unconditioned frequency says nothing."""
    rows = {"up": [], "down": []}
    for k, d in enumerate(days):
        m = mp[d]
        sl = np.flatnonzero(which == k)
        if sl.size < 4:
            continue
        c_, h_, l_ = cc[sl], hh[sl], ll[sl]
        sig = float(np.nanmedian(sg[sl])) * m["c_ref"]
        if not np.isfinite(sig) or sig <= 0:
            continue
        for side, peak, hit in (("up", m["p_u"], c_ > m["p_u"]), ("down", m["p_l"], c_ < m["p_l"])):
            dist = abs(peak - m["c_ref"]) / sig
            height = float(read_M(m, np.array([peak]))[0])
            j = int(np.flatnonzero(hit)[0]) if hit.any() else -1
            exc = {}
            if j >= 0:
                for H in HOLDS:
                    w = slice(j + 1, j + 1 + H)         # [T+1] the window starts AFTER the break bar
                    seg = h_[w] if side == "up" else l_[w]
                    if seg.size:
                        exc[H] = float((seg.max() - peak) / sig) if side == "up" else float((peak - seg.min()) / sig)
            rows[side].append((dist, height, j >= 0, exc))
    out = {}
    for side, rr in rows.items():
        if not rr:
            out[side] = None
            continue
        dist = np.array([r[0] for r in rr]); hgt = np.array([r[1] for r in rr])
        hit = np.array([r[2] for r in rr])
        out[side] = dict(n_sessions=len(rr), freq=float(hit.mean()),
                         dist_sigma_p50=float(np.nanmedian(dist)),
                         by_distance=_bucket(dist, hit, "dist_sigma"),
                         by_barrier_height=_bucket(hgt, hit, "height"),
                         excursion={str(H): _exc([r[3].get(H) for r in rr if r[2]]) for H in HOLDS})
    return out


def _bucket(x, hit, label, nb=5):
    ok = np.isfinite(x)
    if ok.sum() < 50:
        return None
    qs = np.nanquantile(x[ok], np.linspace(0, 1, nb + 1))
    qs[-1] += 1e-9
    b = np.clip(np.searchsorted(qs, x, side="right") - 1, 0, nb - 1)
    return [dict(**{label: round(float(np.nanmedian(x[(b == j) & ok])), 4)},
                 n=int(((b == j) & ok).sum()), freq=float(hit[(b == j) & ok].mean()))
            for j in range(nb) if ((b == j) & ok).sum() > 0]


def _exc(v):
    a = np.array([x for x in v if x is not None and np.isfinite(x)])
    if a.size < 20:
        return None
    lo, hi = np.percentile(a, [1, 99])
    tr = a[(a >= lo) & (a <= hi)]
    return dict(n=int(a.size), mean=float(a.mean()), median=float(np.median(a)),
                trimmed_mean=float(tr.mean()), ex_top=float(a[a <= hi].mean()),
                ex_bottom=float(a[a >= lo].mean()), p90=float(np.percentile(a, 90)))


def reject_traverse(mp, days, cc, which):
    """On entering a high-M band from outside, does price leave the side it came from
    (reject) or the far side (traverse)? No definitional freedom, unlike a swing point."""
    out = {}
    for q in QS:
        for H in HOLDS:
            rej = trav = unres = 0
            for k, d in enumerate(days):
                m = mp[d]
                sl = np.flatnonzero(which == k)
                if sl.size < 3:
                    continue
                c_ = cc[sl]
                for lo_, hi_ in regions(m["x"], m["M"], q):
                    inside = (c_ >= lo_) & (c_ < hi_)
                    if not inside.any():
                        continue
                    for e in np.flatnonzero(inside[1:] & ~inside[:-1]) + 1:
                        below = c_[e - 1] < lo_
                        w = c_[e + 1: e + 1 + H]              # [T+1]
                        ol, oh = w < lo_, w >= hi_
                        jl = int(np.flatnonzero(ol)[0]) if ol.any() else 10**9
                        jh = int(np.flatnonzero(oh)[0]) if oh.any() else 10**9
                        if jl == jh == 10**9:
                            unres += 1
                        elif (jl < jh) == below:
                            rej += 1
                        else:
                            trav += 1
            tot = rej + trav
            out[f"q{q}_H{H}"] = dict(reject=rej, traverse=trav, unresolved=unres,
                                     reject_share=float(rej / tot) if tot else None)
    return out


def terrain_prediction(daily, i, days, mp):
    """SECTION 5.6. TERRAIN closed on a mechanism: inventory accumulates below price exactly
    when price has been falling into it. If M at C_ref is largely a restatement of where
    price recently was, that is the same finding on a new object."""
    dpos = {d: t for t, d in enumerate(daily["dates"])}
    C = daily["close"][i]
    mc, tr = [], []
    for d in days:
        t = dpos[d]
        if t < 21 or not np.isfinite(C[t - 21]) or not np.isfinite(C[t - 1]):
            continue
        mc.append(float(read_M(mp[d], np.array([mp[d]["c_ref"]]))[0]))
        tr.append(float(np.log(C[t - 1] / C[t - 21])))
    if len(mc) < 100:
        return None
    mc, tr = np.array(mc), np.array(tr)
    if mc.std() == 0:
        return None
    return dict(n=len(mc), corr_M_at_price_vs_trailing20=float(np.corrcoef(mc, tr)[0, 1]),
                mean_M_after_up=float(mc[tr > 0].mean()), mean_M_after_down=float(mc[tr <= 0].mean()))


# =====================================================================  assertions
def assert_SPLIT():
    assert _OPENED["n"] > 0, "[SPLIT] the audit hook never saw an open -- it is not installed"
    mod = sys.modules[__name__]
    assert not hasattr(mod, "allow_holdout"), "[SPLIT] this module defines an unlock"
    assert not hasattr(mod, "_ALLOW"), "[SPLIT] this module defines an unlock flag"
    before = _OPENED["refused"]
    try:
        open(REPO / "data/fixtures/us_shorts_daily_holdout.csv.gz", "rb").close()
        raise AssertionError("[SPLIT] the guard did NOT refuse a holdout path")
    except RuntimeError as e:
        assert "refused" in str(e), f"[SPLIT] wrong refusal: {e}"
    assert _OPENED["refused"] == before + 1, "[SPLIT] the refusal was not counted"
    assert _OPENED["refused"] == 1, "[SPLIT] a holdout path was attempted outside this probe"
    return _OPENED["n"]


def assert_QTY(rng):
    """The field integrates to (summed zone width) + n_zones * (analytic tail mass) -- a
    CLOSED FORM, not the same code that built the field. Breaking it must move that
    scalar."""
    o = rng.normal(100, 3, 60); c = o + rng.normal(0, 1, 60)
    h = np.maximum(o, c) + np.abs(rng.normal(0, 1, 60))
    l = np.minimum(o, c) - np.abs(rng.normal(0, 1, 60))
    lo, hi = zones_of(o, h, l, c)
    rep = {}
    for kind in KERNELS:
        hbw = 0.5
        x = np.linspace(lo.min() - PAD * hbw, hi.max() + PAD * hbw, 40001)
        integ = float(np.trapezoid(field(lo, hi, hbw, kind, x), x))
        want = float((hi - lo).sum() + lo.size * tail_mass(hbw, kind))
        rel = abs(integ - want) / want
        assert rel < 2e-3, f"[QTY] {kind}: grid integral {integ:.4f} vs closed form {want:.4f} ({rel:.1e})"
        rep[kind] = round(rel, 8)
    m = build_map(lo, hi, 0.5, "gauss", float(np.median(c)))
    assert m is not None and m["tau"] > 0, "[QTY] the pedestal is a no-op on this sample"
    assert not np.array_equal(m["M"], m["Mr"]), "[QTY] pedestal-subtracted map == un-subtracted map"
    # [X] break the SCALAR: one zone fewer must move the closed form AND the integral
    lo2, hi2 = lo[:-1], hi[:-1]
    x = np.linspace(lo2.min() - 4.0, hi2.max() + 4.0, 40001)
    i2 = float(np.trapezoid(field(lo2, hi2, 0.5, "gauss", x), x))
    w2 = float((hi2 - lo2).sum() + lo2.size * tail_mass(0.5, "gauss"))
    assert abs(i2 - w2) / w2 < 2e-3 and abs(w2 - float((hi - lo).sum() + lo.size * tail_mass(0.5, "gauss"))) > 1e-9, \
        "[X] dropping a zone did not move the mass -- the check is inert"
    return rep


def assert_SIGN():
    """A big upper wick puts mass ABOVE the body and (almost) none below it; a close above
    p_u is a RISE. A sign asserted in prose inverted D280."""
    o, c = np.array([100.0]), np.array([101.0])
    h, l = np.array([110.0]), np.array([100.0])
    lo, hi = zones_of(o, h, l, c)
    hbw = 0.01                                   # tails must not be what carries the answer
    a = field(lo, hi, hbw, "gauss", np.array([105.0]))[0]
    b = field(lo, hi, hbw, "gauss", np.array([95.0]))[0]
    assert a > 0.99, f"[SIGN] upper wick put {a:.4f} above the body, expected 1"
    assert b < 1e-6, f"[SIGN] mass {b:.3e} below a candle with no lower wick"
    o2, c2 = np.array([101.0]), np.array([100.0])
    h2, l2 = np.array([101.0]), np.array([90.0])
    lo2, hi2 = zones_of(o2, h2, l2, c2)
    assert field(lo2, hi2, hbw, "gauss", np.array([95.0]))[0] > 0.99, "[SIGN] lower wick put no mass below"
    assert field(lo2, hi2, hbw, "gauss", np.array([105.0]))[0] < 1e-6, "[SIGN] mass above a candle with no upper wick"
    return True


def assert_GRID(daily, intraday, names, W, kind, cmul):
    """The grid returned with the amendment, so resolution is DEMONSTRATED not to carry the
    result rather than assumed. Every object statistic is recomputed at 2x."""
    a = object_dump(daily, intraday, names[:1], W, kind, cmul, stride=37, n=GRID_N)
    global GRID_N_ACTIVE
    b = _dump_at(daily, intraday, names[:1], W, kind, cmul, 2 * GRID_N - 1)
    worst, where = 0.0, None
    for k in ("modes_raw", "peaks_after_pedestal", "pedestal_share_of_max", "well_width_frac"):
        for u, v in zip(a[k], b[k]):
            d = abs(u - v) / max(abs(u), abs(v), 1e-9)
            if d > worst:
                worst, where = d, k
    assert worst < 0.15, f"[GRID] {where} moved {100*worst:.1f}% between {GRID_N} and {2*GRID_N-1} points"
    return dict(worst_rel_move=round(worst, 4), at=where, n_lo=GRID_N, n_hi=2 * GRID_N - 1)


def _dump_at(daily, intraday, names, W, kind, cmul, n):
    g = globals()
    old = g["GRID_N"]
    g["GRID_N"] = n
    try:
        return object_dump(daily, intraday, names, W, kind, cmul, stride=37, n=n)
    finally:
        g["GRID_N"] = old


def assert_LAG(daily, intraday, s, W=100):
    """The map for day D uses only D-W..D-1, re-derived by a SECOND IMPLEMENTATION that
    never calls maps_for or zones_of. Killed D279's first result -- 93% of its edge."""
    fr = name_frame(daily, intraday, s)
    i = fr["i"]
    dates = daily["dates"]
    O, H, L, C = (daily[k][i] for k in ("open", "high", "low", "close"))
    mp, _ = maps_for(daily, fr, W, "gauss", 0.5)
    d = sorted(mp)[len(mp) // 2]
    t = int(np.flatnonzero(dates == d)[0])
    got = mp[d]
    tot = 0.0
    nz = 0
    for u in range(t - W, t):
        if not (np.isfinite(O[u]) and np.isfinite(H[u]) and np.isfinite(L[u]) and np.isfinite(C[u])):
            continue
        if not (daily["live"][i][u] and H[u] > L[u] and L[u] <= C[u] <= H[u]):
            continue
        bt, bb = max(O[u], C[u]), min(O[u], C[u])
        if H[u] > bt:
            tot += H[u] - bt; nz += 1
        if bb > L[u]:
            tot += bb - L[u]; nz += 1
    assert abs(tot - got["width"]) < 1e-9, f"[LAG] second implementation {tot} != {got['width']}"
    assert nz == got["n_zones"], f"[LAG] zone count {nz} != {got['n_zones']}"
    assert got["c_ref"] == C[t - 1], "[LAG] C_ref is not the close of D-1"
    bt, bb = max(O[t], C[t]), min(O[t], C[t])
    extra = max(H[t] - bt, 0.0) + max(bb - L[t], 0.0)
    assert extra > 0, "[LAG] probe day has no wick -- pick another"
    assert abs(tot + extra - got["width"]) > 1e-9, "[X] including day D did not move the total -- inert"
    return dict(date=d, width=round(got["width"], 4), n_zones=nz)


def assert_PIVOT(rng):
    """The vectorised fractal is BIT-IDENTICAL to terrain_swing._is_swing_bars, probed on a
    TIE-HEAVY input -- ties are where a rewrite disagrees, and the definition is strict and
    unique so equal extremes must produce NO pivot."""
    class _B:
        def __init__(self, h, l):
            self.bar = type("b", (), {"high": h, "low": l})()

    n = 400
    h = np.round(rng.normal(100, 1.0, n), 1)
    l = h - np.round(np.abs(rng.normal(0, 0.4, n)) + 0.1, 1)
    bars = [_B(h[j], l[j]) for j in range(n)]
    for k in SWING_KS:
        for sign in (+1, -1):
            ref = np.array([_is_swing_bars(bars, j, k, sign) for j in range(n)])
            assert np.array_equal(ref, swings_vec(h, l, k, sign)), f"[PIVOT] mismatch k={k} sign={sign}"
    ties = int((h[:, None] == h[None, :]).sum() - n)
    assert ties > 0, "[PIVOT] the probe had no ties -- it cannot have tested the tie convention"
    k = 2
    full, trunc = swings_vec(h, l, k, +1), swings_vec(h[: n - k], l[: n - k], k, +1)
    assert np.array_equal(full[: n - 2 * k], trunc[: n - 2 * k]), "[PIVOT] truncation moved a confirmed pivot"
    return dict(ties=ties, n=n)


def assert_ALIGN(daily, intraday, names, tol=0.005):
    """After the per-session basis factor of load_daily, the daily bars and the 15m bars
    must be the same prices. THIS ASSERTION EARNED ITS PLACE: under raw_price_factor alone
    it caught NOW sitting at 5x its own prices for the entire scored window and ILMN at
    0.97276x, neither of which any other check would have seen."""
    rep = {}
    dpos = {d: t for t, d in enumerate(daily["dates"])}
    for s in names:
        i = daily["symbols"].index(s)
        last = {}
        for d, c in zip(intraday[s]["date"], intraday[s]["c"]):
            last[d] = c
        rat = np.array([c / daily["close"][i][dpos[d]] for d, c in last.items()
                        if d in dpos and np.isfinite(daily["close"][i][dpos[d]])])
        assert rat.size > 200, f"[ALIGN] {s}: only {rat.size} overlapping sessions"
        med, bad = float(np.median(rat)), float(np.mean(np.abs(rat - 1.0) > tol))
        rep[s] = dict(n=int(rat.size), median_ratio=med, share_off_by_gt_tol=bad,
                      basis_levels=daily["phi_levels"].get(s))
        assert abs(med - 1.0) < tol, f"[ALIGN] {s}: median 15m/daily ratio {med:.4f} -- bases disagree"
        assert bad < 0.01, f"[ALIGN] {s}: {100*bad:.2f}% of sessions differ by >{100*tol:.1f}%"
    return rep


def assert_BASE(res):
    """Every event's base rate is reported, and an event firing on more than 20% of bars is
    NOT an event. D385: swing lows at k=2 fire on 24% of ETF bars, which made f == g."""
    flagged = {}
    for s, r in res.items():
        if r is None:
            continue
        for k, v in r["events"].items():
            if k == "ALL_BARS":
                continue
            assert v["base_rate"] is not None, f"[BASE] {s}/{k} has no base rate"
            if v["base_rate"] > BASE_RATE_FLAG:
                flagged.setdefault(k, []).append(round(v["base_rate"], 4))
    return flagged


def assert_ELIG(daily, intraday, names):
    """A' rotates only among days already in the sample, and every sampled day is ELIGIBLE
    -- finT & keep_v2, not finT. D351: 8-13% of rotated events landed off the floor, earned
    +226 to +318 bp against +1.7, and inverted the headline."""
    rep = {}
    dpos = {d: t for t, d in enumerate(daily["dates"])}
    for s in names:
        i = daily["symbols"].index(s)
        sess = [d for d in sorted(set(intraday[s]["date"])) if d <= END_DATE and d in dpos]
        el = np.array([bool(daily["elig"][i][dpos[d]]) for d in sess])
        rep[s] = dict(sessions=len(sess), eligible_share=float(el.mean()))
        assert el.mean() > 0.90, f"[ELIG] {s}: only {100*el.mean():.1f}% of sessions are eligible"
    return rep


def assert_FLOOR(daily):
    """The floor agrees with keep_independent, which never calls roll_mean_T or keep_mask.

    keep_independent is the second implementation of floor_mask **v1** -- it carries no
    isfinite(DV) clause -- so it is compared against v1, the identity
    run_d339_universe_floor.py:291 asserts, and v2 is then checked to be exactly
    v1 & isfinite(DV). Comparing it straight to v2 fails at 62% on this panel."""
    ki = UF.keep_independent(daily["CLOSE"], daily["VOL"], daily["RAWF"], daily["finT"], X.WIN)
    assert np.array_equal(ki, daily["keep1"]), "[FLOOR] the independent floor differs from floor_mask v1"
    assert np.array_equal(daily["keep"], daily["keep1"] & np.isfinite(daily["DV"])), \
        "[FLOOR] keep_v2 != keep_v1 & isfinite(DV)"
    C2 = daily["CLOSE"].copy()
    j = int(np.argmax(daily["finT"].sum(axis=0)))
    C2[:, j] *= 1e-3
    k2 = UF.floor_mask_v2(C2 * daily["RAWF"], daily["DV"], daily["finT"])
    assert k2[:, j].sum() < daily["keep"][:, j].sum(), "[X] a sub-cent price kept eligibility -- the floor is inert"
    return dict(v1_agreement=1.0, floor_share=daily["floor_share"],
                v2_share_of_v1=float(daily["keep"].sum() / max(daily["keep1"].sum(), 1)))


# =====================================================================  drivers
def _preflight():
    rng = np.random.default_rng(20260909)
    r = dict(split_opens=assert_SPLIT(), qty=assert_QTY(rng), sign=assert_SIGN(), pivot=assert_PIVOT(rng))
    return r


def run_audit():
    t0 = time.time()
    print("D403  the wick-stack potential map, built daily and read at 15 minutes")
    print("      AUDIT -- assertions and the object across the kernel/bandwidth sweep\n")
    pf = _preflight()
    print(f"  [SPLIT] guard saw {pf['split_opens']:,} opens, refused {_OPENED['refused']}")
    print(f"  [QTY]   grid integral vs closed form, rel err: {pf['qty']}")
    print(f"  [SIGN]  upper wick above the body, lower wick below: {pf['sign']}")
    print(f"  [PIVOT] {pf['pivot']}")
    P = partition()
    print(f"\n  partition (POOL_SEED {POOL_SEED}, contiguous prefixes):")
    for g in ("g1", "g2", "g3"):
        print(f"    {g.upper()} n={len(P[g]):2d}  {' '.join(P[g])}")
    intraday = load_intraday()
    daily = load_daily(P["g1"] + P["g2"] + P["g3"], intraday)
    print(f"  [FLOOR] {assert_FLOOR(daily)}")
    for s, v in assert_ALIGN(daily, intraday, P["g1"]).items():
        print(f"  [ALIGN] {s:5s} n={v['n']:5d}  median {v['median_ratio']:.6f}  "
              f"off>0.5% {100*v['share_off_by_gt_tol']:.3f}%")
    print(f"  [LAG]   {assert_LAG(daily, intraday, P['g1'][0])}")
    print(f"  [ELIG]  {assert_ELIG(daily, intraday, P['g1'])}")
    print(f"  [GRID]  {assert_GRID(daily, intraday, P['g1'], 100, 'gauss', 0.5)}")

    print("\n  [OBJ] SECTION 5.1 -- THE OBJECT ACROSS THE SWEEP, G1, W=100, every 5th session")
    print(f"    {'kernel':7s} {'c':>5s} {'h %px':>7s} {'modes p10/50/90':>18s} {'<=2 modes':>10s} "
          f"{'peaks p50':>10s} {'tau/max p50':>12s} {'well % p50':>11s}")
    for kind in KERNELS:
        for cm in CS:
            d = object_dump(daily, intraday, P["g1"], 100, kind, cm)
            print(f"    {kind:7s} {cm:5.2f} {d['h_pct_of_price'][1]*100:6.2f}% "
                  f"{str(d['modes_raw']):>18s} {d['bimodal_or_less_share']:9.3f} "
                  f"{d['peaks_after_pedestal'][1]:10.1f} {d['pedestal_share_of_max'][1]:12.3f} "
                  f"{100*d['well_width_frac'][1]:10.2f}%")
    print(f"\n  audit clean in {time.time()-t0:.0f}s")


def run(groups):
    t0 = time.time()
    print("D403  the wick-stack potential map, built daily and read at 15 minutes")
    print(f"      RUN -- groups {','.join(groups)}   scored to {END_DATE} (D383 reserves 2024+)\n")
    _preflight()
    P = partition()
    names = [s for g in groups for s in P[g]]
    intraday = load_intraday()
    daily = load_daily(sorted(set(P["g1"] + P["g2"] + P["g3"])), intraday)
    assert_FLOOR(daily); assert_ALIGN(daily, intraday, names); assert_ELIG(daily, intraday, names)
    assert_LAG(daily, intraday, names[0])
    grid_rep = assert_GRID(daily, intraday, names, PRIMARY["W"], PRIMARY["kind"], PRIMARY["c"])

    cells = [dict(W=PRIMARY["W"], kind=PRIMARY["kind"], c=cm) for cm in CS]
    cells += [dict(W=PRIMARY["W"], kind=k, c=PRIMARY["c"]) for k in KERNELS if k != PRIMARY["kind"]]
    cells += [dict(W=w, kind=PRIMARY["kind"], c=PRIMARY["c"]) for w in WINDOWS if w != PRIMARY["W"]]

    frames = {s: name_frame(daily, intraday, s) for s in names}
    out = dict(groups={g: P[g] for g in groups}, end_date=END_DATE, primary=PRIMARY,
               grid=grid_rep, object={}, cells={})
    for cell in cells:
        tag = f"W{cell['W']}_{cell['kind']}_c{cell['c']}"
        ts = time.time()
        out["object"][tag] = object_dump(daily, intraday, names, cell["W"], cell["kind"], cell["c"])
        res = dict(FN.parallel_map(lambda s, _f: measure_name(daily, _f, cell["W"], cell["kind"], cell["c"]),
                                   list(frames.items())))
        out["cells"][tag] = res
        ok = {s: r for s, r in res.items() if r}
        above = sum(1 for r in ok.values() for k, v in r["aprime"].items()
                    if k != "ALL_BARS" and v["obs_above_p95"])
        tot = sum(1 for r in ok.values() for k in r["aprime"] if k != "ALL_BARS")
        occ = [r["occupancy"]["slope_beta"] for r in ok.values() if r["occupancy"]]
        print(f"  {tag:22s} names {len(ok):2d}  A' beaten {above:3d}/{tot:3d}  "
              f"occupancy beta p50 {np.median(occ):+7.3f}  {time.time()-ts:.0f}s")
    out["base_rate_flagged"] = assert_BASE(out["cells"][f"W{PRIMARY['W']}_{PRIMARY['kind']}_c{PRIMARY['c']}"])
    out["floor"] = assert_FLOOR(daily)
    out["split_guard"] = dict(opens=_OPENED["n"], refused=_OPENED["refused"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    print(f"\n  [BASE] events above {BASE_RATE_FLAG:.0%} of bars: "
          f"{ {k: (min(v), max(v)) for k, v in out['base_rate_flagged'].items()} or 'none'}")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--groups", default="g1")
    a = ap.parse_args()
    if a.audit:
        run_audit()
    elif a.run:
        run([g.strip() for g in a.groups.split(",")])
    else:
        ap.error("pass --audit or --run")
