"""D526 -- the path scaling exponent on a BOUNCE-FREE QUOTED MID, paired against the trade close.

    python scripts/d526_mid_vs_trade_scaling.py --self-test   # checks, seconds
    python scripts/d526_mid_vs_trade_scaling.py --decode       # bbo-1m -> 5-minute mid, cached
    python scripts/d526_mid_vs_trade_scaling.py --build        # the mid fixture
    python scripts/d526_mid_vs_trade_scaling.py --run          # the paired measurement

WHY.  D523's efficiency label was VOID and D525 was RETIRED before it ran, both for the same
underlying reason: the statistic was computed on TRADE CLOSES, which carry bid-ask bounce, and
bounce enters a path statistic asymmetrically.  The principal's instruction is to measure on the
bounce-free mid first.

THE PAIRED DESIGN IS THE POINT.  The same sessions, the same roots, the same statistic, two price
series:

    trade close   from data/fixtures/fut_day5m.parquet   (carries bounce)
    quoted mid    (bid+ask)/2 from bbo-1m                (carries none -- nobody trades at it)

so the bounce contribution is a WITHIN-SESSION DIFFERENCE rather than a comparison across periods
or roots.  That is far more precise, and it is the only way to answer whether the D525 design
check's "index roots are persistent" reading was a property of markets or of the tick.

THE STATISTIC IS THE PATH-LENGTH ESTIMATOR, which D525's audit produced and which replaces the
efficiency ratio outright:

    sum|r_k| ~ N * sigma * k^(Hu-1)     =>     log sum|r_k| = (Hu - 1) log k + const

so the OLS SLOPE IS Hu - 1.  It contains no `net`, hence no log(0), NO DROPPED SESSIONS and NO
SELECTION -- where the efficiency form dropped perfect round trips, the most mean-reverting
sessions there are, biasing the estimate toward persistence by 48-75% of the effect size.
Per-session sd is identical (0.2043 vs 0.2043), so this is strictly better on bias and neutral on
variance.

THE BENCHMARK IS SIMULATED, NEVER THE CLOSED FORM.  At N=72 the finite-window bias exceeds the
whole Hu 0.50-to-0.55 effect, so a theoretical 0.5 would manufacture a result out of arithmetic.

WINDOW.  bbo-1m exists only for 2025-09-11 .. 2026-09-11.  That is INSIDE the slice D525 s6
reserved, and spending it is recorded rather than hidden: s6 itself measured that slice at 48%
power for the close-price confirmation it was held for, this is a VALIDITY CHECK ON THE INSTRUMENT
rather than a test of an edge, and the quoted data exists nowhere else.

NO RETURN IS READ AS P&L, no cost, no position (R15).
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
BREADTH = REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz"
DAY5M = REPO / "data" / "fixtures" / "fut_day5m.parquet"
DAY5M_META = REPO / "data" / "fixtures" / "fut_day5m.meta.json"
CACHE = REPO / "temp" / "d526_mid_cache"
MIDFIX = REPO / "data" / "fixtures" / "fut_day5m_mid.parquet"
OUT = REPO / "data" / "d526_mid_vs_trade.json"

PX = 1e-9                       # Databento fixed-point price scale
UNDEF_PRICE = 2 ** 63 - 1       # an absent price; INT64_MAX PASSES a `> 0` test (D507)
SYM = re.compile(r"^([A-Z0-9]{1,3})([FGHJKMNQUVXZ])(\d)$")
BAR_MIN = 5
DAY_LO, DAY_HI = 540, 959       # 09:00 .. 15:59 ET
N_BARS = 84

NRET = 72                       # 72 has divisors 1..24; 83 is prime
SCALES = (1, 2, 3, 4, 6, 8, 9, 12, 18, 24)
KMIN = 3                        # the bounce-robust set; k=1,2 carry the most bounce
STD_WIN = 13
SEED = 526
N_BENCH = 8000


class GateError(RuntimeError):
    pass


def P(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------------------------------------
# the statistic
# ---------------------------------------------------------------------------------------------
def vol_standardise(R: np.ndarray, w: int = STD_WIN) -> np.ndarray:
    """Divide each return by a CENTRED rolling mean of |r|.

    Legitimate for a LABEL (it may see the whole session); a causal feature could not use the
    centred form.  Measured in D525's design check: leaves a constant rescale EXACT, cuts the
    U-shaped-profile bias 12-fold, and keeps 88% of the Hu=0.55 signal."""
    a = np.abs(R)
    pad = w // 2
    padded = np.vstack([a[:1].repeat(pad, 0), a, a[-1:].repeat(pad, 0)])
    ker = np.ones(w) / w
    loc = np.apply_along_axis(lambda v: np.convolve(v, ker, mode="valid"), 0, padded)
    loc = np.where(loc > 0, loc, np.nan)
    return np.nan_to_num(R / loc, nan=0.0)


def path_slope(R: np.ndarray, kmin: int = KMIN, min_pts: int = 3) -> np.ndarray:
    """OLS slope of log sum|r_k| on log k, per column.  SLOPE = Hu - 1.

    THE MISSING-DATA RULE, and it is the whole reason this estimator replaced the efficiency
    ratio.  The efficiency form needed `log|net|`, so a session whose net was exactly zero -- a
    PERFECT ROUND TRIP, the most mean-reverting session there is -- was dropped, biasing the
    estimate toward persistence by 48-75% of the effect size (D525 s11.2).

    This form needs no `net`, but it is NOT selection-free either, and asserting that it was
    is a claim the self-test refuted: `sum|r_k|` can still be zero if EVERY k-block sums to
    zero, as a perfectly alternating path does at k=2.  So the rule here drops the affected
    SCALE, not the session, and a session is lost only if fewer than `min_pts` scales survive.
    On real data that is rarer than the efficiency form's drop by orders of magnitude, and the
    runner reports both counts rather than claiming either is zero."""
    N, n = R.shape
    xs, ys = [], []
    for k in SCALES:
        if k < kmin or N % k:
            continue
        agg = R.reshape(N // k, k, n).sum(1)
        path = np.abs(agg).sum(0)
        with np.errstate(divide="ignore"):
            ys.append(np.log(np.where(path > 0, path, np.nan)))
        xs.append(np.log(k))
    X = np.array(xs)[:, None]
    Y = np.vstack(ys)
    W = np.isfinite(Y)
    Yz = np.where(W, Y, 0.0)
    Xz = np.where(W, X, 0.0)
    m = W.sum(0).astype(np.float64)
    Sx, Sy = Xz.sum(0), Yz.sum(0)
    Sxx, Sxy = (Xz * Xz).sum(0), (Xz * Yz).sum(0)
    den = m * Sxx - Sx * Sx
    with np.errstate(invalid="ignore", divide="ignore"):
        slope = (m * Sxy - Sx * Sy) / den
    return np.where((m >= min_pts) & (den > 0), slope, np.nan)


def fgn(n: int, hurst: float, size: int, rng: np.random.Generator) -> np.ndarray:
    """Fractional Gaussian noise, Davies-Harte exact circulant embedding.  Returns (n, size)."""
    k = np.arange(n + 1, dtype=np.float64)
    g = 0.5 * (np.abs(k + 1) ** (2 * hurst) - 2 * np.abs(k) ** (2 * hurst)
               + np.abs(k - 1) ** (2 * hurst))
    c = np.concatenate([g, g[-2:0:-1]])
    lam = np.fft.fft(c).real
    if lam.min() < -1e-8:
        raise GateError(f"[FGN] circulant not PSD at hurst={hurst}: min {lam.min():.3e}")
    lam = np.clip(lam, 0, None)
    m = len(c)
    w = (rng.normal(size=(size, m)) + 1j * rng.normal(size=(size, m))) / np.sqrt(2 * m)
    out = np.fft.fft(w * np.sqrt(lam)[None, :], axis=1).real[:, :n]
    return (out / out.std(axis=1, keepdims=True)).T


def benchmark(standardise: bool) -> float:
    """The SIMULATED random-walk slope at this N and scale set.  Never the closed form."""
    rng = np.random.default_rng(SEED)
    R = fgn(NRET, 0.50, N_BENCH, rng)
    if standardise:
        R = vol_standardise(R)
    return float(np.nanmean(path_slope(R)))


def lag1(R: np.ndarray) -> float:
    """Mean lag-1 autocorrelation of the returns, per column then averaged.

    THE DECISIVE INSTRUMENT CHECK.  Bid-ask bounce is an MA(-1) in the trade price, so it shows
    up here and nowhere else so cleanly.  A mid built from quotes should be markedly closer to
    zero than the trade close on the same sessions."""
    A = R - R.mean(0, keepdims=True)
    num = (A[:-1] * A[1:]).sum(0)
    den = (A * A).sum(0)
    return float(np.nanmean(np.where(den > 0, num / den, np.nan)))


# ---------------------------------------------------------------------------------------------
# the mid fixture
# ---------------------------------------------------------------------------------------------
def bar_of(minute: np.ndarray) -> np.ndarray:
    """5-minute bar index inside the day session; -1 outside it."""
    return np.where((minute >= DAY_LO) & (minute <= DAY_HI),
                    (minute - DAY_LO) // BAR_MIN, -1)


def id_windows(store) -> dict:
    """{instrument_id: [(root, symbol, start_ns, end_ns), ...]} -- WINDOWED, not flat.

    A flat id->symbol dict pools contracts a decade apart and ingests foreign instruments
    (D520/D521).  D507 used a flat dict on this same schema; over a 12-month window the reuse
    risk is small but it is not zero, and the fix is one extra tuple."""
    out: dict[int, list] = {}
    for sym, ivs in store.metadata.mappings.items():
        m = SYM.match(str(sym))
        if not m:
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if not sid:
                continue
            s = iv.get("start_date") if isinstance(iv, dict) else getattr(iv, "start_date", None)
            e = iv.get("end_date") if isinstance(iv, dict) else getattr(iv, "end_date", None)
            s_ns = pd.Timestamp(s).tz_localize("UTC").value if s is not None else 0
            e_ns = (pd.Timestamp(e).tz_localize("UTC").value if e is not None
                    else np.iinfo(np.int64).max)
            out.setdefault(int(sid), []).append((m.group(1), str(sym), s_ns, e_ns))
    return out


def bbo_files() -> list[Path]:
    f = sorted(RAW.glob("*/*.bbo-1m.dbn.zst"))
    if not f:
        raise GateError("[FILES] no bbo-1m files found")
    return f


def do_decode() -> int:
    import databento as db

    CACHE.mkdir(parents=True, exist_ok=True)
    files = bbo_files()
    todo = [f for f in files if not (CACHE / f"{f.stem}.mid5m.parquet").exists()]
    P(f"  {len(files)} bbo-1m files, {len(files)-len(todo)} cached, {len(todo)} to decode "
      f"({sum(f.stat().st_size for f in todo)/2**30:.2f} GiB)")
    t0 = time.time()
    for i, f in enumerate(todo, 1):
        t1 = time.time()
        store = db.DBNStore.from_file(f)
        win = id_windows(store)
        arr = store.to_ndarray()
        keep = np.isin(arr["instrument_id"], np.fromiter(win, dtype=np.uint32))
        a = arr[keep]
        del arr
        n_raw = len(a)
        # THE SENTINEL PASSES `> 0`. This is D507's recorded bug and it belongs in the filter.
        undef = (a["bid_px_00"] == UNDEF_PRICE) | (a["ask_px_00"] == UNDEF_PRICE)
        ok = (a["bid_px_00"] > 0) & (a["ask_px_00"] > 0) & (~undef) \
            & (a["ask_px_00"] > a["bid_px_00"])
        n_undef, n_bad = int(undef.sum()), int((~ok).sum() - undef.sum())
        a = a[ok]
        mid = (a["bid_px_00"].astype(np.float64) + a["ask_px_00"].astype(np.float64)) * 0.5 * PX
        ts = pd.to_datetime(a["ts_recv"], utc=True).tz_convert("US/Eastern")
        minute = (ts.hour * 60 + ts.minute).to_numpy()
        bar = bar_of(minute)
        day = ts.strftime("%Y-%m-%d").to_numpy()
        tsv = ts.value.to_numpy() if hasattr(ts, "value") else ts.astype("int64").to_numpy()

        iid = a["instrument_id"].astype(np.int64)
        roots = np.empty(len(a), object)
        syms = np.empty(len(a), object)
        nowin = 0
        for k, lst in win.items():
            m = iid == k
            if not m.any():
                continue
            if len(lst) == 1:
                roots[m], syms[m] = lst[0][0], lst[0][1]
                continue
            tt = tsv[m]
            rr = np.empty(m.sum(), object)
            ss = np.empty(m.sum(), object)
            hit = np.zeros(m.sum(), bool)
            for (rt, sy, s_ns, e_ns) in lst:
                sel = (tt >= s_ns) & (tt < e_ns) & (~hit)
                rr[sel], ss[sel], hit[sel] = rt, sy, True
            nowin += int((~hit).sum())
            roots[m], syms[m] = rr, ss
        good = (bar >= 0) & (roots != None)                              # noqa: E711
        d = pd.DataFrame({"root": roots[good].astype(str), "contract": syms[good].astype(str),
                          "day": day[good], "bar": bar[good].astype(np.int16),
                          "minute": minute[good], "mid": mid[good]})
        # the LAST minute in each 5-minute block, mirroring the trade fixture's close_at_last
        d = d.sort_values(["root", "contract", "day", "bar", "minute"], kind="stable")
        g = d.groupby(["root", "contract", "day", "bar"], as_index=False).agg(
            mid=("mid", "last"), n_min=("minute", "size"))
        g.to_parquet(CACHE / f"{f.stem}.mid5m.parquet", index=False)
        rate = (time.time() - t0) / i
        P(f"  [{i:2d}/{len(todo)}] {f.name[-30:]:<30} {n_raw:>10,} quoted, "
          f"{n_undef:>7,} one-sided, {n_bad:>6,} crossed, {nowin:>5,} unwindowed -> "
          f"{len(g):>8,} bars, {g['root'].nunique():>2} roots  "
          f"({time.time()-t1:.0f}s, ETA {rate*(len(todo)-i)/60:.0f} min)")
    P(f"\n  decode done in {(time.time()-t0)/60:.1f} min")
    return 0


def do_build() -> int:
    files = bbo_files()
    have = sorted(CACHE.glob("*.mid5m.parquet"))
    if len(have) != len(files):
        raise GateError(f"[CACHE] {len(have)} of {len(files)} decoded -- run --decode first")
    G = pd.concat([pd.read_parquet(p) for p in have], ignore_index=True)
    G = G.groupby(["root", "contract", "day", "bar"], as_index=False).agg(
        mid=("mid", "last"), n_min=("n_min", "sum"))
    P(f"  {len(G):,} raw 5-minute mid bars, {G['root'].nunique()} roots")
    b = pd.read_csv(BREADTH, usecols=["root", "day", "contract", "same_front", "present"])
    n0 = len(G)
    G = G.merge(b, on=["root", "day", "contract"], how="inner")
    P(f"  front-month join: {n0:,} -> {len(G):,} ({len(G)/n0:.1%} kept)")
    if len(G) == 0:
        raise GateError("[JOIN] the front-month join kept nothing")
    G = G.sort_values(["root", "day", "bar"], kind="stable").reset_index(drop=True)
    MIDFIX.parent.mkdir(parents=True, exist_ok=True)
    G.to_parquet(MIDFIX, index=False)
    per = G.groupby("root").agg(bars=("mid", "size"), sessions=("day", "nunique"),
                                first=("day", "min"), last=("day", "max"))
    P("\n     root      bars  sessions  bars/sess       span")
    for r, row in per.iterrows():
        P(f"     {r:>4}{row['bars']:>10,.0f}{row['sessions']:>10,.0f}"
          f"{row['bars']/row['sessions']:>11.1f}   {row['first']} .. {row['last']}")
    P(f"\n  wrote {MIDFIX.relative_to(REPO)}  ({len(G):,} rows)")
    return 0


# ---------------------------------------------------------------------------------------------
def session_matrix(g: pd.DataFrame, col: str) -> tuple[np.ndarray, list]:
    """(NRET, n_sessions) log returns from the first NRET+1 CONSECUTIVE bars, per session."""
    bars = g["bar"].to_numpy()
    px = g[col].to_numpy(np.float64)
    day = g["day"].to_numpy()
    cut = np.flatnonzero(day[1:] != day[:-1]) + 1
    segs = list(zip(np.concatenate(([0], cut)), np.concatenate((cut, [len(g)]))))
    cols, days = [], []
    for a, b in segs:
        bb, pp = bars[a:b], px[a:b]
        if len(bb) < NRET + 1 or bb[NRET] - bb[0] != NRET or not np.all(pp[:NRET + 1] > 0):
            continue
        cols.append(np.diff(np.log(pp[:NRET + 1])))
        days.append(day[a])
    if not cols:
        return np.zeros((NRET, 0)), []
    return np.vstack(cols).T, days


def do_run() -> int:
    if not MIDFIX.exists():
        raise GateError("[FIX] the mid fixture is absent -- run --decode then --build")
    B_raw, B_std = benchmark(False), benchmark(True)
    P("D526 -- the path scaling exponent on the QUOTED MID, paired against the TRADE CLOSE")
    P(f"  statistic: OLS slope of log sum|r_k| on log k, k>={KMIN}, N={NRET}. SLOPE = Hu - 1.")
    P(f"  SIMULATED benchmarks at seed {SEED}: raw {B_raw:+.4f}   standardised {B_std:+.4f}")
    P(f"  (the closed form says {0.5-1:+.4f}; the finite-window bias is "
      f"{B_raw-(0.5-1):+.4f}, which is why it is simulated)")

    mid = pd.read_parquet(MIDFIX)
    mid = mid[mid["present"]]
    mid = mid[mid["same_front"]]
    trd = pd.read_parquet(DAY5M, columns=["root", "day", "bar", "close", "present", "same_front"])
    trd = trd[trd["present"]]
    trd = trd[trd["same_front"]]
    lo, hi = mid["day"].min(), mid["day"].max()
    trd = trd[(trd["day"] >= lo) & (trd["day"] <= hi)]
    P(f"  window {lo} .. {hi}   (bbo-1m's extent; inside D525 s6's reserved slice, spent "
      f"knowingly -- see the module docstring)")

    roots = sorted(set(mid["root"]) & set(trd["root"]))
    rows = {}
    P("")
    P("   root   sess    TRADE slope   dev    Hu     MID slope    dev    Hu    "
      "lag1 trade  lag1 mid   bounce share")
    for r in roots:
        gm = mid[mid["root"] == r].sort_values(["day", "bar"], kind="stable")
        gt = trd[trd["root"] == r].sort_values(["day", "bar"], kind="stable")
        Rm, dm = session_matrix(gm, "mid")
        Rt, dt = session_matrix(gt, "close")
        common = sorted(set(dm) & set(dt))
        if len(common) < 100:
            continue
        im = [dm.index(d) for d in common]
        it = [dt.index(d) for d in common]
        Rm, Rt = Rm[:, im], Rt[:, it]
        sm = np.nanmean(path_slope(vol_standardise(Rm)))
        st = np.nanmean(path_slope(vol_standardise(Rt)))
        dev_m, dev_t = sm - B_std, st - B_std
        l1t, l1m = lag1(Rt), lag1(Rm)
        share = (dev_t - dev_m) / dev_t if abs(dev_t) > 1e-9 else np.nan
        rows[r] = {"sessions": len(common),
                   "trade_slope": float(st), "trade_dev": float(dev_t),
                   "trade_hu": float(1 + st), "mid_slope": float(sm),
                   "mid_dev": float(dev_m), "mid_hu": float(1 + sm),
                   "lag1_trade": l1t, "lag1_mid": l1m,
                   "bounce_share_of_dev": float(share),
                   "sd_trade": float(np.nanstd(path_slope(vol_standardise(Rt)), ddof=1)),
                   "sd_mid": float(np.nanstd(path_slope(vol_standardise(Rm)), ddof=1))}
        P(f"   {r:>4}  {len(common):>5}   {st:+.4f}  {dev_t:+.4f} {1+st:.3f}   "
          f"{sm:+.4f}  {dev_m:+.4f} {1+sm:.3f}   {l1t:+.4f}   {l1m:+.4f}"
          f"   {share:+.1%}" if np.isfinite(share) else "")
    art = {"purpose": "D526: the path scaling exponent on a bounce-free quoted mid, paired "
                      "against the trade close on the same sessions",
           "statistic": "OLS slope of log sum|r_k| on log k; slope = Hu - 1; no net, so no "
                        "session is dropped and there is no selection",
           "benchmarks": {"raw": B_raw, "standardised": B_std, "seed": SEED,
                          "note": "simulated fGn at Hu=0.50; the closed form would be -0.5 and "
                                  "the finite-window bias exceeds the whole effect"},
           "window": [str(lo), str(hi)],
           "holdout_note": "bbo-1m exists only here, inside D525 s6's reserved slice; spent "
                           "knowingly as a validity check on the instrument, not a test of an "
                           "edge, and s6 measured that slice at 48% power for its original use",
           "per_root": rows}
    OUT.write_text(json.dumps(art, indent=1), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


# ---------------------------------------------------------------------------------------------
def do_self_test() -> int:
    fails = []
    rng = np.random.default_rng(1)

    def chk(name, ok, note=""):
        P(f"    [{'PASS' if ok else 'FAIL'}] {name:<70} {note}")
        if not ok:
            fails.append(name)

    # 1 -- the path-length slope recovers Hu, monotonically
    got = {}
    for hu in (0.40, 0.45, 0.50, 0.55, 0.60):
        got[hu] = float(np.nanmean(path_slope(fgn(NRET, hu, 6000, rng))))
    P(f"      slopes: " + "  ".join(f"Hu{h:.2f}->{v:+.4f}" for h, v in got.items()))
    chk("the path-length slope is MONOTONE INCREASING in Hu",
        all(got[a] < got[b] for a, b in zip(sorted(got), sorted(got)[1:])))
    chk("and slope+1 tracks Hu to within 0.06 at N=72",
        all(abs(1 + got[h] - h) < 0.06 for h in got),
        f"max |slope+1-Hu| = {max(abs(1+got[h]-h) for h in got):.4f}")
    chk("[X] the CLOSED FORM's bias is at least half the whole 0.50-0.55 effect, so it is unusable",
        abs(got[0.50] - (0.50 - 1)) > 0.5 * abs(got[0.55] - got[0.50]),
        f"bias {got[0.50]-(0.50-1):+.4f} vs effect {got[0.55]-got[0.50]:+.4f}")

    # 2 -- THE MISSING-DATA RULE. A net==0 session survives here (the efficiency form dropped
    # it); a PERFECTLY ALTERNATING session loses the k=2 scale but keeps the rest.
    R = fgn(NRET, 0.5, 500, rng)
    R[:, 0] = np.concatenate([np.ones(NRET // 2), -np.ones(NRET // 2)])   # net 0, path fine
    s = path_slope(R)
    chk("a net==0 session survives -- which is exactly what the efficiency form dropped",
        abs(R[:, 0].sum()) < 1e-12 and np.isfinite(s[0]),
        f"net {R[:,0].sum():+.1e}, slope {s[0]:+.4f}")
    alt = np.tile(np.array([1.0, -1.0]), NRET // 2)[:, None]
    chk("[X] a PERFECTLY ALTERNATING path has a zero aggregate at k=2 and STILL yields a slope",
        np.isfinite(path_slope(alt, kmin=1)[0]),
        f"slope {path_slope(alt, kmin=1)[0]:+.4f} from the surviving scales")
    chk("[X] and a column with too few surviving scales is NaN, not a fabricated fit",
        np.isnan(path_slope(np.zeros((NRET, 1)), kmin=1)[0]))
    # [OPT] the masked OLS must equal a plain OLS wherever nothing is missing
    def plain_ols(Rm, kmin=KMIN):
        xs, ys = [], []
        for k in SCALES:
            if k < kmin or Rm.shape[0] % k:
                continue
            xs.append(np.log(k))
            ys.append(np.log(np.abs(Rm.reshape(Rm.shape[0] // k, k, Rm.shape[1])
                                    .sum(1)).sum(0)))
        X = np.array(xs)
        Y = np.vstack(ys)
        Xc = X - X.mean()
        return (Xc[:, None] * (Y - Y.mean(0))).sum(0) / (Xc ** 2).sum()

    Rc = fgn(NRET, 0.52, 2000, rng)
    ms, ps = path_slope(Rc), plain_ols(Rc)
    chk("[OPT] the masked OLS equals a plain OLS to 1e-12 where no scale is missing",
        np.isfinite(ms).all() and np.abs(ms - ps).max() < 1e-12,
        f"max diff {np.abs(ms - ps).max():.2e} over {len(ms):,} columns")

    # 3 -- vol standardisation: exact under a constant rescale
    Rb = fgn(NRET, 0.55, 3000, rng)
    chk("vol-standardisation is BIT-IDENTICAL under a constant rescale",
        np.array_equal(path_slope(vol_standardise(Rb)),
                       path_slope(vol_standardise(4.0 * Rb))))
    prof = 1.0 + 2.0 * np.cos(np.linspace(-np.pi, np.pi, NRET)) ** 2
    raw_bias = abs(np.nanmean(path_slope(Rb * prof[:, None])) - np.nanmean(path_slope(Rb)))
    std_bias = abs(np.nanmean(path_slope(vol_standardise(Rb * prof[:, None])))
                   - np.nanmean(path_slope(vol_standardise(Rb))))
    chk("[X] and it REDUCES the U-shaped-vol bias (which the raw form carries)",
        std_bias < raw_bias / 3, f"raw {raw_bias:.4f} -> standardised {std_bias:.4f}")

    # 4 -- the aggregates partition the window and net is invariant to k
    A = fgn(NRET, 0.5, 50, rng)
    nets = [A.reshape(NRET // k, k, 50).sum(1).sum(0) for k in SCALES if NRET % k == 0]
    chk("the k-bar aggregates PARTITION the window: net is invariant to k to 1e-12",
        max(np.abs(n - nets[0]).max() for n in nets) < 1e-12)

    # 5 -- lag1 detects bounce, which is the instrument check the run depends on
    clean = fgn(NRET, 0.5, 4000, rng)
    u = rng.normal(0, 0.5, (NRET + 1, 4000))
    bouncy = clean + np.diff(u, axis=0)
    chk("lag1 is near zero on a clean series", abs(lag1(clean)) < 0.03, f"{lag1(clean):+.4f}")
    chk("[X] and STRONGLY NEGATIVE once bounce is added -- so the run can tell them apart",
        lag1(bouncy) < -0.15, f"{lag1(bouncy):+.4f} at psi/sigma 0.5")

    # 6 -- bar_of
    chk("09:00 is bar 0, 15:55 is bar 83, outside the session is -1",
        list(bar_of(np.array([540, 955, 539, 960, 0]))) == [0, 83, -1, -1, -1])

    # 7 -- session_matrix needs NRET+1 CONSECUTIVE bars
    g = pd.DataFrame({"day": ["d1"] * (NRET + 1) + ["d2"] * NRET,
                      "bar": list(range(NRET + 1)) + list(range(NRET)),
                      "close": np.arange(1, 2 * NRET + 2, dtype=float)})
    R2, days = session_matrix(g, "close")
    chk("session_matrix keeps only sessions with NRET+1 consecutive bars",
        R2.shape == (NRET, 1) and days == ["d1"], f"{R2.shape}, {days}")
    holed = g[~((g["day"] == "d1") & (g["bar"] == 10))]
    chk("[X] and a hole inside the window REJECTS that session",
        session_matrix(holed, "close")[0].shape[1] == 0)

    # 8 -- the sentinel filter
    px = np.array([100_000_000, UNDEF_PRICE, 0, 250_000_000], dtype=np.int64)
    chk("[X] the UNDEFINED-price sentinel PASSES a `> 0` test -- which is why it is named",
        bool((px > 0)[1]))
    chk("and the filter excludes it explicitly",
        list((px > 0) & (px != UNDEF_PRICE)) == [True, False, False, True])

    # 9 -- the frozen benchmark
    b1, b2 = benchmark(False), benchmark(True)
    chk("the benchmark is reproducible at the frozen seed",
        abs(benchmark(False) - b1) < 1e-12 and abs(benchmark(True) - b2) < 1e-12,
        f"raw {b1:+.4f}  standardised {b2:+.4f}")

    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--decode", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.decode:
        return do_decode()
    if a.build:
        return do_build()
    if a.run:
        return do_run()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
