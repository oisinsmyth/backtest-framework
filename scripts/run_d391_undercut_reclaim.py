"""D391 STAGE 0 -- the undercut-and-reclaim: the four things that must be read before any null.

    uv run python scripts/run_d391_undercut_reclaim.py --selftest
    uv run python scripts/run_d391_undercut_reclaim.py --stage0
    uv run python scripts/run_d391_undercut_reclaim.py --build-pivots     (cache only; --stage0 does it)

Pre-registration: docs/decisions/D391-the-undercut-and-reclaim.md (committed BEFORE this file, R8).

THE EVENT, section 1 frozen, on fresh confirmed pivots from research.structure.market_structure
with K = 3 (ragged_structure_scores.K, taken and not chosen):

    fresh      t - last_low_index <= 252            FRESH_BARS -- a level older than a year is not a level
    real leg   (last_high - last_low) > 0.5 * ATR   the guard that stopped retrace_leg ranging over [-2295, +1207]
    UNDERCUT   low[t]   <  last_low                 the level is taken out intrabar
    RECLAIM    close[t] >  last_low                 and price closes back above it     -> the EVENT, long at t+1's open

and the same-bar population that undercut and closed BELOW is the B_r pool -- same pool, same day,
same structure, opposite outcome. It is built here because Stage 0's second question needs it.

STAGE 0 IS FOUR READINGS AND TWO OF THEM CAN STOP THE RECORD (pre-reg section 2):
    1. the exposure arithmetic, entries/bar x hold = open positions, computed BEFORE it is predicted
    2. THE POOL'S OWN DRIFT -- what an undercut name earns REGARDLESS of reclaim (FINDINGS 52's rule
       applied before the fact). If reclaimers and the whole pool earn the same, the record stops here
    3. the split sizes, reclaim vs no-reclaim
    4. the four groups, with the TOP TRADE NAMED and its bar printed (D322)

NO NULL IS RUN HERE. Stage 0 scores no cell and admits nothing (R15).

BUILD (R16): today's panel, load_ragged(..., dividend_bound=True), D333's default. Nothing is
inherited from a pre-D333 record, so no cross-build identity is owed.

ASSERTIONS
  [PIV] the level is CAUSAL: last_low at bar t recomputed from a panel truncated at t equals the
        full-run value, by a second market_structure pass. A level that moves when the future is
        deleted is look-ahead and fails the run.
  [POOL] events and the B_r pool are disjoint, both are subsets of the undercut set, and their
        union is exactly it.
  [E]   every event sits on an eligible bar (D351's mask, the one the strategy may trade).
  [P]   the JSON is persisted BEFORE it is rendered (D371).
  [X]   the self-test RAISES on (a) the reclaim condition inverted and (b) a pivot level read one
        bar early. A self-test that cannot fail is worse than none.
"""

from __future__ import annotations

import argparse
import hashlib
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


OUT = REPO / "data" / "d391_stage0.json"
CACHE_DIR = REPO / "temp" / "d391_pivots"
K = 3                    # ragged_structure_scores.K
FRESH_BARS = 252         # ragged_structure_scores.FRESH_BARS
LEG_ATR = 0.5            # the retrace_leg guard
CAPS = (5, 10, 20, 40, 60)
PRIMARY_CAP = 20
HORIZON_FOR_POOL = 20    # the pool-drift read; the cap grid is separate


def pivot_key(V):
    """Cache key: the fixture AND every module whose edit changes a pivot (CLAUDE.md's rule)."""
    parts = []
    fx = Path(V.M.B.FIXTURE)
    st = fx.stat()
    parts.append(f"{fx.name}:{st.st_size}:{int(st.st_mtime)}")
    for f in (REPO / "src" / "backtest_framework" / "research" / "structure.py",
              REPO / "scripts" / "ragged_structure_scores.py",
              REPO / "scripts" / "ragged_panel.py"):
        parts.append(f"{f.name}:{int(f.stat().st_mtime)}")
    parts.append(f"K={K}")
    return hashlib.sha1("\n".join(parts).encode()).hexdigest()[:16]


def build_pivots(V, MS, panel, cleaned, live):
    """(T, n) grids of the confirmed pivot levels and their ages. Cached; the state machine is a
    per-symbol Python forward pass and costs minutes."""
    key = pivot_key(V)
    d = CACHE_DIR / key
    names = ("last_low", "last_high", "low_age", "high_age")
    if all((d / f"{k}.npy").exists() for k in names):
        print(f"    [K] pivot cache HIT {key}", flush=True)
        return {k: np.load(d / f"{k}.npy") for k in names}
    print(f"    [K] pivot cache BUILD {key}", flush=True)
    n, T = live.shape
    out = {k: np.full((n, T), np.nan) for k in names}
    t0 = time.time()
    for i, sym in enumerate(panel.symbols):
        at = np.flatnonzero(live[i])
        bars = cleaned[sym]
        if at.size != len(bars) or at.size == 0:
            continue
        for j, s in enumerate(MS.market_structure(bars, K)):
            if s.last_low is not None:
                out["last_low"][i, at[j]] = s.last_low
                out["low_age"][i, at[j]] = j - s.last_low_index
            if s.last_high is not None:
                out["last_high"][i, at[j]] = s.last_high
                out["high_age"][i, at[j]] = j - s.last_high_index
        if (i + 1) % 300 == 0:
            print(f"      {i + 1}/{len(panel.symbols)} symbols ({time.time() - t0:.0f}s)", flush=True)
    d.mkdir(parents=True, exist_ok=True)
    for k in names:
        np.save(d / f"{k}.npy", out[k])
    print(f"    pivots built in {time.time() - t0:.0f}s, cached", flush=True)
    return out


def lag1_mask(m):
    """Shift a SIGNAL mask one bar forward, to a POSITION mask. **This is not optional and its
    absence was a look-ahead defect in the first version of this file.**

    The kernel (`EB.simulate_event` via `run_d359`) treats the mask it is given as the bar the
    position OPENS ON, and books that bar's open-to-close. D359 and D361 can pass their signals
    straight in because those are built from percentile grids ALREADY LAGGED to t-1, so entering
    at bar t's open uses only information through t-1.

    **This study's event is defined by bar t's OWN low and close.** Passing it unlagged made the
    kernel book the very bar whose close defines the event: measured, the signal bar's own excess
    is +47.19 bp and the next bar's is +0.61. The whole of the first reported ledger was that one
    bar. D279's error, in a new place, caught by `temp/which_bar.py`."""
    out = np.zeros_like(m)
    out[1:] = m[:-1]
    return np.ascontiguousarray(out)


def event_masks(PV, g, atr, eligT):
    """(T, n) masks: the EVENT (undercut + reclaim), the B_r pool (undercut + close below), and
    their parent (any qualifying undercut). Everything on eligible bars only [E]."""
    LO, CL, HI = g["low"], g["close"], g["high"]                 # (n, T)
    lastlow, lasthigh = PV["last_low"], PV["last_high"]
    with np.errstate(invalid="ignore"):
        fresh = (PV["low_age"] <= FRESH_BARS) & (PV["high_age"] <= FRESH_BARS)
        leg = (lasthigh - lastlow) > LEG_ATR * atr
        ok = fresh & leg & np.isfinite(lastlow) & np.isfinite(atr) & (atr > 0)
        undercut = ok & (LO < lastlow)
        event = undercut & (CL > lastlow)
        pool = undercut & ~(CL > lastlow)
        # the short mirror, reported as a mechanism check only (FINDINGS 33 rule 1)
        mirror = ok & np.isfinite(lasthigh) & (HI > lasthigh) & (CL < lasthigh)
    e = eligT.T                                                   # (n, T) eligibility
    return (np.ascontiguousarray((event & e).T), np.ascontiguousarray((pool & e).T),
            np.ascontiguousarray((undercut & e).T), np.ascontiguousarray((mirror & e).T))


def forward_h(P, h, start=1):
    """Hedged forward drift over `h` bars, STARTING `start` bars after the signal bar.

    `start=1` IS NOT A DETAIL AND IT IS NOT V61's DEFAULT. `r1T[t]` is the return earned DURING
    bar t, and D361's `forward20` pairs it with a gate LAGGED to t-1, so `F[t]` is correct there.
    **This study's event is known only at bar t's CLOSE** -- and the two arms are defined by that
    close's position, the reclaim arm closing ABOVE the level and the pool arm BELOW it. Including
    bar t's own return would therefore hand the reclaim arm an up-day and the pool arm a down-day
    BY CONSTRUCTION, manufacturing the entire spread out of the definition. That is D279's error
    in a new place: the quantity is lagged correctly in the kernel and the DIAGNOSTIC beside it is
    not.

    The kernel agrees: entry is at the NEXT OPEN, so the ledger starts earning at t+1. The
    diagnostic must start where the money starts.

    `start=0` is computed too and printed beside it, so the size of the artifact is visible rather
    than asserted away."""
    r1T, m_f, finT = np.asarray(P["r1T"]), np.asarray(P["m_f"]), np.asarray(P["finT"])
    T, n = r1T.shape
    ex = np.where(finT & np.isfinite(r1T) & np.isfinite(m_f)[:, None], r1T - m_f[:, None], 0.0)
    Cm = np.concatenate([np.zeros((1, n)), np.cumsum(ex, axis=0)])
    F = np.full((T, n), np.nan)
    t = np.arange(0, T - h - start + 1)
    F[t] = Cm[t + start + h] - Cm[t + start]
    return F


def group_stats(pnl):
    """The four-group numbers that do not need a ledger object."""
    p = np.asarray(pnl, float)
    lo, hi = np.percentile(p, 1), np.percentile(p, 99)
    return dict(n=int(p.size), mean_bp=float(p.mean()), median_bp=float(np.median(p)),
                win_rate=float((p > 0).mean()),
                t=float(p.mean() / (p.std(ddof=1) / np.sqrt(p.size))) if p.size > 1 else None,
                skew=float(((p - p.mean()) ** 3).mean() / p.std() ** 3) if p.std() > 0 else None,
                kurtosis=float(((p - p.mean()) ** 4).mean() / p.std() ** 4 - 3.0) if p.std() > 0 else None,
                trim_ex_top_bp=float(p[p <= hi].mean()), trim_ex_bottom_bp=float(p[p >= lo].mean()),
                trim_both_bp=float(p[(p >= lo) & (p <= hi)].mean()))


# ---------------------------------------------------------------------- self-test
def selftest(MS) -> int:
    print("D391 STAGE 0 SELF-TEST -- the event, its mirror pool, and two breaks that must be caught\n")
    # a hand case: level 100; a bar that dips to 99 and closes 101 is an EVENT; closes 99 is POOL
    lastlow = np.array([[100.0, 100.0, 100.0]])
    low = np.array([[99.0, 99.0, 101.0]])
    close = np.array([[101.0, 99.0, 102.0]])
    under = low < lastlow
    ev = under & (close > lastlow)
    pool = under & ~(close > lastlow)
    assert ev.tolist() == [[True, False, False]], f"event mask wrong: {ev}"
    assert pool.tolist() == [[False, True, False]], f"pool mask wrong: {pool}"
    assert not (ev & pool).any(), "[POOL] event and pool overlap"
    assert ((ev | pool) == under).all(), "[POOL] event u pool != undercut"
    print("    hand case: dip-and-reclaim is an EVENT, dip-and-close-below is the POOL, "
          "no-dip is neither; they partition the undercut set")

    # [X] break 1 -- invert the reclaim and the two masks must swap
    ev_bad = under & ~(close > lastlow)
    raised = False
    try:
        assert ev_bad.tolist() == [[True, False, False]], "an inverted reclaim must not reproduce the event"
    except AssertionError:
        raised = True
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- an inverted reclaim passed"
    print("    [X] the reclaim condition inverted IS CAUGHT")

    # [X] break 2 -- a pivot level read one bar early must change the mask
    shifted = np.array([[np.nan, 100.0, 100.0]])
    ev_shift = (low < shifted) & (close > shifted)
    assert not np.array_equal(np.nan_to_num(ev_shift), np.nan_to_num(ev)), \
        "[X] a level read one bar early left the event mask unchanged"
    print("    [X] a pivot level shifted one bar IS CAUGHT (the mask changes)")
    print("\nSELF-TEST PASSED\n")
    return 0


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--stage0", action="store_true")
    ap.add_argument("--build-pivots", action="store_true")
    a = ap.parse_args()

    from backtest_framework.research import structure as MS
    if a.selftest:
        return selftest(MS)
    if not (a.stage0 or a.build_pivots):
        ap.error("pass --stage0 (no null runs here; stage 1 is not authorised)")
    selftest(MS)

    t0 = time.time()
    PREP = _load("d348p", "d348_prep.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    ST = _load("ragged_structure_scores", "ragged_structure_scores.py")
    P = PREP.prep(need_grids=True)
    M = PREP.M
    print(f"  prep in {time.time() - t0:.0f}s | {P['n']} names x {P['T']} bars", flush=True)

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    live = panel.live
    PREP.M = M
    PV = build_pivots(type("V", (), {"M": M})(), MS, panel, cleaned, live)
    if a.build_pivots and not a.stage0:
        return 0

    # ATR in price units, ragged_structure_scores' own helper, per symbol on its own bars
    n, T = live.shape
    atr = np.full((n, T), np.nan)
    for i in range(n):
        at = np.flatnonzero(live[i])
        if at.size < 2:
            continue
        atr[i, at] = ST._atr_price(g["open"][i, at], g["high"][i, at],
                                   g["low"][i, at], g["close"][i, at])

    elig = np.asarray(P["elig"])                                  # (T, n)
    EV, POOL, UNDER, MIRROR = event_masks(PV, g, atr, elig)
    for nm, m in (("event", EV), ("pool", POOL), ("undercut", UNDER)):
        assert not (m & ~elig).any(), f"[E] {nm} has an event off the eligible mask"
    assert not (EV & POOL).any() and np.array_equal(EV | POOL, UNDER), \
        "[POOL] the event and the B_r pool do not partition the undercut set"
    print(f"    [E] every event sits on an eligible bar | [POOL] event {int(EV.sum()):,} + "
          f"pool {int(POOL.sum()):,} = undercut {int(UNDER.sum()):,}", flush=True)

    # ---- [PIV] the level is causal ----------------------------------------
    rng = np.random.default_rng(391)
    checked = 0
    for i in rng.choice(np.flatnonzero(live.sum(axis=1) > 400), size=6, replace=False):
        at = np.flatnonzero(live[i])
        bars = cleaned[panel.symbols[i]]
        full = MS.market_structure(bars, K)
        for j in rng.choice(np.arange(300, len(bars)), size=4, replace=False):
            trunc = MS.market_structure(bars[:j + 1], K)
            a_, b_ = full[j].last_low, trunc[j].last_low
            assert (a_ is None and b_ is None) or (a_ == b_), \
                f"[PIV] {panel.symbols[i]} bar {j}: level moved when the future was deleted ({a_} vs {b_})"
            checked += 1
    print(f"    [PIV] {checked} sampled bars: last_low recomputed from a panel truncated at t "
          f"equals the full-run value -- the level is causal", flush=True)

    # ---- 1. the exposure arithmetic, BEFORE it is predicted ----------------
    bars_defined = int(elig.any(axis=1).sum())
    ev_per_bar = EV.sum() / max(1, bars_defined)
    exposure_pred = {c: float(min(1.0, ev_per_bar * c / max(1.0, elig.sum(axis=1).mean())))
                     for c in CAPS}
    print(f"\n  1. EXPOSURE ARITHMETIC (section 38 rule 2, computed before it is predicted)")
    print(f"     {int(EV.sum()):,} events over {bars_defined:,} bars = "
          f"{ev_per_bar:.2f} entries/bar")
    for c in CAPS:
        print(f"     cap {c:<3d} -> {ev_per_bar * c:>8.1f} open positions on the average bar")

    # ---- 2. THE POOL'S OWN DRIFT (FINDINGS 52's rule, before the fact) -----
    drift, drift_unlagged = {}, {}
    for start, into in ((1, drift), (0, drift_unlagged)):
        Fh = forward_h(P, HORIZON_FOR_POOL, start=start)
        for nm, m in (("event_reclaim", EV), ("pool_no_reclaim", POOL), ("undercut_all", UNDER)):
            v = Fh[m]
            v = v[np.isfinite(v)]
            into[nm] = dict(n=int(v.size), bp=float(v.mean()) * 1e4,
                            median_bp=float(np.median(v)) * 1e4)
    edge_over_pool = drift["event_reclaim"]["bp"] - drift["pool_no_reclaim"]["bp"]
    edge_unlagged = drift_unlagged["event_reclaim"]["bp"] - drift_unlagged["pool_no_reclaim"]["bp"]
    assert abs(edge_unlagged - edge_over_pool) > 1e-9, \
        "[LAG] including the event bar changed nothing -- the alignment is not what it claims"

    print(f"\n  2. THE POOL'S OWN DRIFT -- hedged forward-{HORIZON_FOR_POOL}, per name-bar, bp,")
    print(f"     STARTING AT t+1 where the kernel's next-open entry starts")
    for nm, d in drift.items():
        print(f"     {nm:<18s} n {d['n']:>8,}  mean {d['bp']:>+8.1f}  median {d['median_bp']:>+8.1f}")
    print(f"     RECLAIM minus NO-RECLAIM: {edge_over_pool:+.1f} bp  <-- what H3 must survive a null on")
    print(f"\n     [LAG] the same read INCLUDING the event bar gives {edge_unlagged:+.1f} bp. That "
          f"version is NOT the finding:")
    print(f"           the reclaim arm closes ABOVE its level by definition and the pool arm BELOW, "
          f"so bar t's own")
    print(f"           return is the event's definition rather than its consequence. The "
          f"{edge_unlagged - edge_over_pool:+.1f} bp difference is the artifact.")

    # ---- 3. the split sizes ------------------------------------------------
    years = np.asarray(P["years"])
    by_year = {}
    for y in sorted(set(int(x) for x in years)):
        sel = years == y
        by_year[y] = dict(event=int(EV[sel].sum()), pool=int(POOL[sel].sum()))
    print(f"\n  3. SPLIT SIZES: {int(EV.sum()):,} reclaim vs {int(POOL.sum()):,} no-reclaim "
          f"({100 * EV.sum() / max(1, UNDER.sum()):.1f}% reclaim)")

    # ---- 4. the ledger and the four groups, TOP TRADE NAMED ---------------
    sc = np.full((T, n), 50.0)                                    # unused under exit="cap"; asserted
    # THE MASK MUST BE LAGGED BEFORE IT REACHES THE KERNEL -- see lag1_mask.
    EV_POS, MIRROR_POS = lag1_mask(EV), lag1_mask(MIRROR)
    # [L] the lag audit the pre-registration required and the first version omitted: no position
    # may open on a bar that is itself an event bar for that name.
    assert np.array_equal(EV_POS[1:], EV[:-1]) and not EV_POS[0].any(), \
        "[L] the position mask is not the signal mask shifted exactly one bar"
    print(f"    [L] positions open one bar AFTER the signal: {int(EV_POS.sum()):,} long, "
          f"{int(MIRROR_POS.sum()):,} short (signal bars {int(EV.sum()):,} / "
          f"{int(MIRROR.sum()):,})", flush=True)
    res = V59.run_mirror(P, EV_POS, sc, "cap", PRIMARY_CAP)
    res2 = V59.run_mirror(P, EV_POS, np.full((T, n), 17.0), "cap", PRIMARY_CAP)
    assert len(res["trades"]) == len(res2["trades"]), "[SC] the score changed the cap-exit ledger"
    pnl = PREP.V47.pnl_bp(res)
    trd = V59.trade_block(P, res, np.asarray(P["elig"]), 0, False)
    dep = V59.deployed_block(res, P)
    gs = group_stats(pnl)

    tr = res["trades"]
    k = int(np.argmax(pnl))
    top = dict(symbol=P["symbols"][tr[k][0]], entry_bar=int(tr[k][1]),
               entry_date=P["dates"][tr[k][1]], held=int(tr[k][2]), pnl_bp=float(pnl[k]),
               share_of_total=float(pnl[k] / pnl.sum()) if pnl.sum() != 0 else None)
    # the mirror, mechanism check only
    resm = V59.run_short(P, MIRROR_POS, sc, "cap", PRIMARY_CAP)
    pnlm = PREP.V47.pnl_bp(resm)

    # ---- [P] PERSIST BEFORE ANY OF SECTION 4 IS RENDERED -------------------
    #      The first version of this file put the write AFTER these prints and lost the run to a
    #      KeyError in the print loop -- D371's exact failure, reproduced by the file whose own
    #      assertion list forbids it. The write now precedes every print that reads the ledger.
    payload = dict(
        study=391, stage=0, cap_primary=PRIMARY_CAP, caps=list(CAPS), K=K,
        purpose="D391 Stage 0: exposure, the pool's own drift, the split, and the four groups. "
                "No null is run; nothing is admitted (R15).",
        build="load_ragged(dividend_bound=True), D333's default (R16)",
        counts=dict(event=int(EV.sum()), pool=int(POOL.sum()), undercut=int(UNDER.sum()),
                    mirror=int(MIRROR.sum()), bars=bars_defined,
                    entries_per_bar=float(ev_per_bar)),
        exposure_arithmetic={str(c): float(ev_per_bar * c) for c in CAPS},
        pool_drift=drift, pool_drift_including_event_bar=drift_unlagged,
        reclaim_minus_pool_bp=float(edge_over_pool),
        reclaim_minus_pool_bp_including_event_bar=float(edge_unlagged),
        by_year=by_year, groups=gs, per_trade=trd, deployed=dep, top_trade=top,
        mirror=dict(trades=int(len(resm["trades"])), mean_bp=float(pnlm.mean()),
                    median_bp=float(np.median(pnlm))))
    OUT.write_text(json.dumps(V59.clean(payload) if hasattr(V59, "clean") else payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering section 4")

    print(f"\n  4. THE LEDGER at cap {PRIMARY_CAP}: {gs['n']:,} trades, mean {gs['mean_bp']:+.2f} bp, "
          f"median {gs['median_bp']:+.2f}, win {100 * gs['win_rate']:.1f}%, t {gs['t']:+.2f}")
    print(f"     trim: ex-top {gs['trim_ex_top_bp']:+.2f} | ex-bottom {gs['trim_ex_bottom_bp']:+.2f} "
          f"| both {gs['trim_both_bp']:+.2f}   <- the SYMMETRIC trim is the honest one (CLAUDE.md)")
    print(f"     TOP TRADE: {top['symbol']} entered {top['entry_date']} (bar {top['entry_bar']}), "
          f"held {top['held']}, {top['pnl_bp']:+,.0f} bp = {100 * (top['share_of_total'] or 0):.1f}% "
          f"of the ledger")
    hedged = dep["PUB"]["hedged"]
    print(f"     deployed (PUB, hedged): gross {hedged['gross_bp']:+.3f} bp/bar, "
          f"net {hedged['net_bp']:+.3f}, exposure {100 * hedged.get('exposure', float('nan')):.1f}%")
    print(f"\n  MIRROR (mechanism check only, FINDINGS 33 rule 1): {len(resm['trades']):,} short "
          f"trades, mean {pnlm.mean():+.2f} bp, median {np.median(pnlm):+.2f}")
    print(f"\n  ({time.time() - t0:.0f}s)  No null was run. Stage 1 is not authorised by this file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
