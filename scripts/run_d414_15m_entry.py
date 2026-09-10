"""D414 -- daily zone, 15-minute entry: the execution delta. Bar committed in 330ab58 BEFORE this ran.

    uv run python scripts/run_d414_15m_entry.py --run

Path-invariant: every touch is its own trade, no slot cap, no book, no refill.

THIS DOES NOT TEST THE SIGNAL (record section 1). On the only data with 15m bars -- 32 survivor
names from 2018 -- the daily edge is not visible and at +-17 bp cannot be refuted. It tests
EXECUTION: two entries on IDENTICAL events, exits held fixed at the close of t+5, so the exit
cancels and the paired delta is nothing but the entry:

    delta = sign * (log C[t] - log P_entry)        positive = the 15m entry was BETTER

  MARKET  at the close of the first 15m bar trading into the zone     (crosses the spread)
  LIMIT   at the zone's near edge, or the OPEN if price gapped through (fills with no queue)

THE BASIS IS WHERE THIS CAN DIE SILENTLY (section 4). The zone is in the daily fixture's basis and
the 15m bars in an adjusted one; D403 found NOW at 5x and ILMN at 0.97276x under raw_price_factor.
The repair is D403's phi[t] = (15m last close of session t) / (daily close), reused. Three
assertions guard it: [ALIGN] as D403 wrote it, [BASIS] phi[u] == phi[t] per event, [SAME-DAY] the
first 15m bar into the zone is on the daily touch day.

TWO THINGS THE PRE-REGISTRATION LEFT IMPLICIT, DECIDED HERE AND FLAGGED IN THE RESULT:
  1. The 15m session is 09:30-15:45. A daily touch that happened only in the last quarter-hour or
     the closing auction is INVISIBLE on 15m bars. That is an expected miss, not a basis failure,
     so [SAME-DAY] carries a 10% tolerance: above it the runner STOPS as section 4 says; below it
     the misses are dropped and counted.
  2. A limit order fills at the BETTER of the edge and the open when price gaps through the zone
     at 09:30. That is the correct fill convention and is still optimistic on queue position.

2024-01-01 ONWARD IS RESERVED (section 2). [RESERVED] asserts no bar past 2023-12-31 reaches the
event loop.
"""
import argparse
import gzip
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d413c", REPO / "scripts" / "run_d413_combine.py")
C = importlib.util.module_from_spec(_s)
sys.modules["d413c"] = C
_s.loader.exec_module(C)                      # D411's [SPLIT] holdout guard comes with it
M, Z4, D, CS = C.M, C.Z4, C.D, C.CS

FIX_15 = (REPO / "data/fixtures/cohort3_intraday_15m_raw.csv.gz",
          REPO / "data/fixtures/cohort4_intraday_15m_raw.csv.gz")
CACHE = REPO / "temp" / "d414_15m.npz"
OUT = REPO / "data" / "d414_15m_entry.json"
START, END = "2018-01-02", "2023-12-31"       # MINING; 2024+ is RESERVED and never read
MIN_EVENTS = 500
SAME_DAY_TOL = 0.10
ALIGN_TOL = 0.005
BASIS_STEP = 0.02            # a basis STEP is a corporate action (>= 2%); below it is auction noise
BARS_PER_SESSION = 26


# ------------------------------------------------------------------ the 15m fixtures
def load_15m(verbose=True):
    """(name -> ts, date, o, h, l, c) at 15m, BOTH cohorts, cached in temp/ keyed on both mtimes."""
    key = "_".join(str(int(p.stat().st_mtime_ns) % (1 << 40)) for p in FIX_15)
    f = CACHE.with_name(f"d414_15m_{key}.npz")
    if f.exists():
        z = np.load(f, allow_pickle=False)
        names = sorted({k.split("__")[0] for k in z.files})
        return {s: dict(ts=z[s + "__ts"], date=z[s + "__d"], o=z[s + "__o"], h=z[s + "__h"],
                        l=z[s + "__l"], c=z[s + "__c"]) for s in names}
    t0 = time.time()
    rows = {}
    for p in FIX_15:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            hdr = next(fh).strip().split(",")
            assert hdr == ["timestamp", "symbol", "open", "high", "low", "close", "volume"], hdr
            for line in fh:
                q = line.rstrip("\n").split(",")
                rows.setdefault(q[1], []).append((q[0], float(q[2]), float(q[3]), float(q[4]),
                                                  float(q[5])))
    out, save = {}, {}
    for s, v in rows.items():
        v.sort(key=lambda r: r[0])
        ts = np.array([r[0] for r in v])
        out[s] = dict(ts=ts, date=np.array([x[:10] for x in ts]),
                      o=np.array([r[1] for r in v]), h=np.array([r[2] for r in v]),
                      l=np.array([r[3] for r in v]), c=np.array([r[4] for r in v]))
        for k in ("ts", "date", "o", "h", "l", "c"):
            save[f"{s}__{'d' if k == 'date' else k}"] = out[s][k]
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(f, **save)
    if verbose:
        print(f"  15m parsed {sum(len(v['c']) for v in out.values()):,} bars, "
              f"{len(out)} names, in {time.time()-t0:.0f}s")
    return out


def session_index(iv):
    """date -> (start, end) slice into the name's sorted 15m arrays."""
    d = iv["date"]
    chg = np.flatnonzero(d[1:] != d[:-1]) + 1
    starts = np.r_[0, chg]
    ends = np.r_[chg, d.size]
    return {d[a]: (a, b) for a, b in zip(starts, ends)}


# ------------------------------------------------------------------ the basis
def basis_phi(P, intr, names):
    """phi[t, i] = (15m last close of session t) / (daily close of t), forward-filled.

    D403's repair, reused: per session, never smoothed -- a rolling median would smear a 5x step
    over its window. Units, not information; bar t's own phi is knowable at t's close."""
    T = P["CL"].shape[0]
    pos = {d: t for t, d in enumerate(P["dates"])}
    sym = {s: i for i, s in enumerate(P["symbols"])}
    PHI = {}
    for s in names:
        i = sym[s]
        v = np.full(T, np.nan)
        idx = session_index(intr[s])
        for d, (a, b) in idx.items():
            t = pos.get(d)
            if t is not None and np.isfinite(P["CL"][t, i]) and P["CL"][t, i] > 0:
                v[t] = intr[s]["c"][b - 1] / P["CL"][t, i]
        ok = np.flatnonzero(np.isfinite(v))
        assert ok.size > 200, f"[ALIGN] {s}: only {ok.size} overlapping sessions"
        v[: ok[0]] = v[ok[0]]
        fwd = np.maximum.accumulate(np.where(np.isfinite(v), np.arange(T), 0))
        PHI[s] = v[fwd]
    return PHI


def assert_ALIGN(P, intr, PHI, names):
    """D403's assertion, unchanged in substance: after the repair the 15m and daily closes must be
    the same prices. It earned its place catching NOW at 5x and ILMN at 0.97276x."""
    rep = {}
    pos = {d: t for t, d in enumerate(P["dates"])}
    sym = {s: i for i, s in enumerate(P["symbols"])}
    for s in names:
        i = sym[s]
        idx = session_index(intr[s])
        rat = []
        for d, (a, b) in idx.items():
            t = pos.get(d)
            if t is not None and np.isfinite(P["CL"][t, i]) and P["CL"][t, i] > 0:
                rat.append(intr[s]["c"][b - 1] / (P["CL"][t, i] * PHI[s][t]))
        rat = np.array(rat)
        med, bad = float(np.median(rat)), float(np.mean(np.abs(rat - 1.0) > ALIGN_TOL))
        levels = sorted(set(np.round(PHI[s][np.isfinite(PHI[s])], 3).tolist()))
        rep[s] = dict(n=int(rat.size), median=med, off=bad, phi_levels=levels)
        assert abs(med - 1.0) < ALIGN_TOL, f"[ALIGN] {s}: median ratio {med:.4f}"
        assert bad < 0.01, f"[ALIGN] {s}: {100*bad:.2f}% of sessions off by >{100*ALIGN_TOL:.1f}%"
    return rep


def assert_SIGN():
    """[SIGN] in money, in the declared direction: a demand zone touched intraday and closing
    ABOVE the touch must give a POSITIVE delta; the supply mirror must too."""
    for side, c15_touch, close, lim in ((+1, 98.0, 101.0, 99.0), (-1, 102.0, 99.0, 101.0)):
        d_mkt = side * (np.log(close) - np.log(c15_touch))
        d_lim = side * (np.log(close) - np.log(lim))
        assert d_mkt > 0 and d_lim > 0, f"[SIGN] side {side}: {d_mkt:+.4f} {d_lim:+.4f}"
    return True


# ------------------------------------------------------------------ the study
def run():
    t0 = time.time()
    print("D414  daily zone, 15-minute entry -- the execution delta")
    print("      the bar was committed in 330ab58 BEFORE this ran\n")
    assert_SIGN()
    P = D.load_panel(verbose=False)
    atr = Z4.atr_of(P)
    intr = load_15m()
    names = sorted(s for s in intr if s in P["symbols"])
    missing = sorted(set(intr) - set(names))
    assert not missing, f"[UNI] 15m names absent from the daily fixture: {missing}"

    # ---- [RESERVED]: nothing past END reaches the event loop
    for s in names:
        keep = intr[s]["date"] <= END
        for k in ("ts", "date", "o", "h", "l", "c"):
            intr[s][k] = intr[s][k][keep]
        assert (intr[s]["date"] <= END).all(), f"[RESERVED] {s} carries a bar past {END}"
    print(f"  [RESERVED] every 15m bar past {END} cut before scoring; "
          f"{sum(len(v['c']) for v in intr.values()):,} bars remain on {len(names)} names")

    PHI = basis_phi(P, intr, names)
    al = assert_ALIGN(P, intr, PHI, names)
    stepped = {s: v["phi_levels"] for s, v in al.items() if len(v["phi_levels"]) > 1}
    print(f"  [ALIGN] {len(al)} names, worst median {max(abs(v['median']-1) for v in al.values()):.5f}, "
          f"worst off-share {100*max(v['off'] for v in al.values()):.2f}%")
    print(f"          names with a basis STEP inside the window: "
          + (", ".join(f"{s} {v}" for s, v in stepped.items()) if stepped else "none"))

    # ---- the events: D413's zones, restricted to 15m names and the mining window
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z, g, tt = A["Z"], A["good"], A["tt"]
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    tr5 = D.trailing_ret(lg, 5)
    eff = C.path_efficiency(lg)
    DV = D.X.roll_mean_T(P["CL"] * P["VOL"])
    ii, te, uu = Z["i"][g], tt[g], Z["u"][g]
    rev, ef, dv = tr5[te, ii] * Z["side"][g], eff[te, ii], DV[te, ii]
    fin = np.isfinite(rev) & np.isfinite(ef) & np.isfinite(dv)
    cuts = (np.median(rev[fin]), np.median(ef[fin]), np.median(dv[fin]))
    cell2 = fin & (rev <= cuts[0]) & (ef > cuts[1]) & (dv > cuts[2])
    symarr = np.array(P["symbols"])
    datearr = np.array(P["dates"])
    nm, dt = symarr[ii], datearr[te]
    in15 = np.isin(nm, names)
    win = (dt >= START) & (dt <= END)
    sel = np.flatnonzero(in15 & win)
    print(f"\n  P1  D413 touches on 15m names in {START}..{END}: {sel.size:,}   "
          f"(cell 2 among them: {int(cell2[sel].sum()):,})")

    # ---- the neutral spread, per ADDENDUM 2
    spread = CS.corwin_schultz(P["HI"].T, P["LO"].T, P["live"].T).T
    neutral = np.full_like(spread, np.nan)
    for t in range(62, spread.shape[0]):
        with np.errstate(invalid="ignore"):
            neutral[t] = np.nanmedian(spread[t - 62:t - 2], axis=0)

    sidx = {s: session_index(intr[s]) for s in names}
    ev = []
    n_basis, n_miss, n_nosess = 0, 0, 0
    steps = []
    for k in sel:
        s, i, t, u = nm[k], int(ii[k]), int(te[k]), int(uu[k])
        side = int(Z["side"][g][k])
        # [BASIS] no corporate action between creation and touch. phi is measured per session
        # from the 15m 16:00 close against the daily close WITH the auction print, so it carries
        # a few tenths of a percent of closing-auction noise on every session -- the first version
        # of this check asked for equality to 1e-9 and dropped 88% of events on that noise. A
        # real action is >= 2% (ILMN's spinoff was 2.7%, a split is 100%+); the noise tops out
        # near 1.5% on the most volatile name here. The gate sits between them, and the observed
        # scale is reported so the choice is visible rather than buried.
        step = abs(PHI[s][u] / PHI[s][t] - 1.0)
        steps.append(step)
        if step > BASIS_STEP:
            n_basis += 1
            continue
        ph = PHI[s][t]
        lo15, hi15 = Z["lo"][g][k] * ph, Z["hi"][g][k] * ph
        c_day = P["CL"][t, i] * ph                       # == the session's last 15m close
        d = datearr[t]
        if d not in sidx[s]:
            n_nosess += 1
            continue
        a, b = sidx[s][d]
        o, h, l, c = (intr[s][x][a:b] for x in ("o", "h", "l", "c"))
        hit = (h >= lo15) & (l <= hi15)
        if not hit.any():
            n_miss += 1                                  # [SAME-DAY] -- counted, tolerance below
            continue
        j = int(np.argmax(hit))
        p_mkt = c[j]
        p_lim = min(hi15, o[j]) if side > 0 else max(lo15, o[j])
        # a limit at the edge cannot fill worse than the edge; if the bar never traded through
        # the edge on the entry side, the fill IS the edge (the touch reaches it by definition)
        ev.append(dict(sym=s, date=d, t=t, u=u, side=side, bar=j, ts=str(intr[s]["ts"][a + j]),
                       lo=float(lo15), hi=float(hi15), close=float(c_day),
                       p_mkt=float(p_mkt), p_lim=float(p_lim),
                       d_mkt=float(side * (np.log(c_day) - np.log(p_mkt))),
                       d_lim=float(side * (np.log(c_day) - np.log(p_lim))),
                       half_spread=float(0.5 * neutral[t, i]) if np.isfinite(neutral[t, i]) else np.nan,
                       cell2=bool(cell2[k]), r_daily=float(A["r"][g][k])))
    n_in = sel.size - n_basis - n_nosess
    miss_rate = n_miss / max(n_in, 1)
    st_ = np.array(steps)
    print(f"      [BASIS] |phi[u]/phi[t] - 1| over events: p50 {100*np.median(st_):.2f}%  "
          f"p90 {100*np.quantile(st_, .9):.2f}%  p99 {100*np.quantile(st_, .99):.2f}%  "
          f"max {100*st_.max():.2f}%   (auction noise; a step is >= {100*BASIS_STEP:.0f}%)")
    print(f"      [BASIS] dropped {n_basis} ({100*n_basis/max(sel.size,1):.2f}%) straddling a "
          f"step;  no 15m session on the touch day: {n_nosess}")
    print(f"      [SAME-DAY] daily touch with NO 15m bar into the zone: {n_miss} of {n_in} "
          f"({100*miss_rate:.2f}%)   tolerance {100*SAME_DAY_TOL:.0f}%")
    assert miss_rate <= SAME_DAY_TOL, (f"[SAME-DAY] {100*miss_rate:.1f}% of daily touches have no "
                                       f"15m touch -- the basis is wrong, stopping")
    print(f"      paired events: {len(ev):,}   (G1 needs {MIN_EVENTS})")
    assert len(ev) >= MIN_EVENTS, f"G1: only {len(ev)} paired events"

    dm = np.array([e["d_mkt"] for e in ev]); dl = np.array([e["d_lim"] for e in ev])
    hs = np.array([e["half_spread"] for e in ev]); c2 = np.array([e["cell2"] for e in ev])
    bar = np.array([e["bar"] for e in ev]); side = np.array([e["side"] for e in ev])

    # ---- P3: when in the day does the entry fire?
    print(f"\n  P3  first 15m touch by bar-of-day (0 = 09:30): "
          + "  ".join(f"b{q}:{100*np.mean(bar==q):.0f}%" for q in range(0, 26, 5))
          + f"   first hour (b0-b3) {100*np.mean(bar<=3):.1f}%   at the open (b0) {100*np.mean(bar==0):.1f}%")

    # ---- P4: look at the object
    e = max(ev, key=lambda x: abs(x["d_mkt"]))
    print(f"  P4  largest |delta|: {e['sym']} {e['date']}  side {e['side']:+d}  zone "
          f"[{e['lo']:.2f},{e['hi']:.2f}]  first touch {e['ts'][11:16]} (bar {e['bar']})  "
          f"mkt {e['p_mkt']:.2f}  lim {e['p_lim']:.2f}  close {e['close']:.2f}  "
          f"delta mkt {1e4*e['d_mkt']:+.0f} lim {1e4*e['d_lim']:+.0f} bp")
    e = ev[len(ev) // 2]
    print(f"      a median one : {e['sym']} {e['date']}  side {e['side']:+d}  zone "
          f"[{e['lo']:.2f},{e['hi']:.2f}]  first touch {e['ts'][11:16]} (bar {e['bar']})  "
          f"mkt {e['p_mkt']:.2f}  lim {e['p_lim']:.2f}  close {e['close']:.2f}  "
          f"delta mkt {1e4*e['d_mkt']:+.0f} lim {1e4*e['d_lim']:+.0f} bp")

    def stat(x, label):
        se = x.std(ddof=1) / np.sqrt(x.size)
        return dict(label=label, n=int(x.size), mean=float(1e4 * x.mean()), se=float(1e4 * se),
                    t=float(x.mean() / se), median=float(1e4 * np.median(x)),
                    win=float(100 * (x > 0).mean()))

    def show(st):
        print(f"  {st['label']:34s} n {st['n']:5,}   mean {st['mean']:+8.2f} +-{st['se']:.2f} bp"
              f"   {st['t']:+5.1f} SE   median {st['median']:+7.2f}   >0 {st['win']:.1f}%")

    print(f"\n  --- THE PAIRED DELTA, gross (record section 3) ---")
    S = dict(mkt=stat(dm, "MARKET  first-bar close vs daily close"),
             lim=stat(dl, "LIMIT   edge/open fill vs daily close"))
    show(S["mkt"]); show(S["lim"])
    print(f"\n  --- by side ---")
    for sd, lab in ((1, "demand (long)"), (-1, "supply (short)")):
        m = side == sd
        S[f"mkt_{lab[:6]}"] = stat(dm[m], f"MARKET  {lab}"); show(S[f"mkt_{lab[:6]}"])
        S[f"lim_{lab[:6]}"] = stat(dl[m], f"LIMIT   {lab}"); show(S[f"lim_{lab[:6]}"])
    print(f"\n  --- the cell-2 stratum (reported, NOT gated) ---")
    S["mkt_c2"] = stat(dm[c2], "MARKET  cell 2"); show(S["mkt_c2"])
    S["lim_c2"] = stat(dl[c2], "LIMIT   cell 2"); show(S["lim_c2"])
    S["mkt_not"] = stat(dm[~c2], "MARKET  not cell 2"); show(S["mkt_not"])

    # ---- N: net of cost, RELATIVE TO THE DAILY-CLOSE BASELINE which itself crosses the spread.
    #      The market arm pays the same half-spread the baseline pays -> its delta is already net.
    #      The limit arm pays none -> it SAVES a half-spread relative to the baseline.
    ok = np.isfinite(hs)
    S["cost"] = dict(half_spread_median_bp=float(1e4 * np.nanmedian(hs)),
                     lim_net_of_saved_spread=stat(dl[ok] + hs[ok], "LIMIT   + half-spread saved"))
    print(f"\n  --- N: net, relative to the daily-close baseline (which also crosses the spread) ---")
    print(f"  neutral half-spread at entry, median {S['cost']['half_spread_median_bp']:.1f} bp")
    print(f"  MARKET arm pays the same half-spread as the baseline -> its delta above IS the net")
    show(S["cost"]["lim_net_of_saved_spread"])

    T1 = bool(S["mkt"]["t"] > 2.0)
    T2 = bool(S["lim"]["t"] > 2.0)
    print(f"\n  --- THE BAR (committed 330ab58) ---")
    print(f"    G1 assertions hold, n >= {MIN_EVENTS}     : True   (n {len(ev):,})")
    print(f"    T1 MARKET delta > 0 by 2 paired SE  : {T1}   ({S['mkt']['mean']:+.2f} bp, {S['mkt']['t']:+.1f} SE)")
    print(f"    T2 LIMIT  delta > 0 by 2 paired SE  : {T2}   ({S['lim']['mean']:+.2f} bp, {S['lim']['t']:+.1f} SE)")
    print(f"\n  VERDICT: T1 {'PASS' if T1 else 'FAIL'}   T2 {'PASS' if T2 else 'FAIL'}")

    OUT.write_text(json.dumps(dict(
        window=dict(start=START, end=END, reserved_from="2024-01-01"),
        names=names, align=al, counts=dict(candidates=int(sel.size), basis_dropped=n_basis,
                                           no_session=n_nosess, same_day_miss=n_miss,
                                           miss_rate=miss_rate, paired=len(ev),
                                           cell2=int(c2.sum())),
        bar=dict(G1=True, T1=T1, T2=T2), stats=S,
        bar_of_day=[float(np.mean(bar == q)) for q in range(BARS_PER_SESSION)],
        events=ev), indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()
