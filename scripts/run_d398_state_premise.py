"""D398 -- the structural state premise check: how often is a single name in a two-sided
structural trend on daily bars, and what do the path-efficiency and volatility overlays leave?

    uv run python scripts/run_d398_state_premise.py --selftest
    uv run python scripts/run_d398_state_premise.py --pin       [S2] bit-identity against S2's own runner
    uv run python scripts/run_d398_state_premise.py --run

Spec: docs/decisions/D398-the-structural-state-premise-check.md, committed BEFORE this file (R8).

WHAT IT IS. A MEASUREMENT (D280's class). It scores no strategy, computes no return, draws no null,
chooses no operating point and admits nothing (R15). It answers: how often is the state on, how
long does it last, and how much of it survives the overlays?

WHY. The principal's construction is a two-sided structural trend on DAILY bars, overlaid with path
efficiency and a volatility band, with entries/stops/targets set at 15 MINUTES. Three numbers the
design cannot be written without, and none can be guessed:
  * onset entry vs state entry -- a rough estimate off S2's ETF exposure gives ~115 long onsets on
    the 24-name cohort4 panel over 8.6 years, which would be too few to study
  * what each overlay costs in EVENTS -- filters multiply, and D366 found that out too late
  * how much SURVIVORSHIP would bias a short leg -- section 5's Q6 measures it directly

NOTHING IS REIMPLEMENTED. `pivots` comes from research.structure and `rolling_fit` from S2's own
runner, with S2's constants (K=3, WINDOW=252, MIN_PIVOTS=3) imported rather than restated.

THE RAGGED TRAP, AND IT IS THE ONE REAL DIFFERENCE FROM S2. `run_uptrend_onset.signals` calls
`rolling_fit(T, ...)` with the PANEL's T, because on the 57-ETF panel every symbol is full length
and aligned, so a pivot's local index equals its grid column. ON THE 1,573-NAME RAGGED PANEL THEY
ARE NOT EQUAL. `pivots(cleaned[s], k)` indexes into the symbol's OWN row list. So the fit runs on
`len(bars)` with local indices and is scattered back to `np.flatnonzero(live[i])` -- `er_grid`'s
rule. Done the other way every value after a symbol's start would be silently misplaced, and [S2]
below is what proves it was not: on the ETF panel this code must reduce to S2's exactly.

ASSERTIONS [S2][L][X][E][W][P] -- spec section 6. No cache: the whole pass profiled at 25 s
(load_ragged 19 s, every pivot 6 s), so a cache keyed on module mtimes would be staleness risk
bought with no time saved. The projection was measured before the decision, not guessed.
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


FIX = REPO / "data" / "fixtures"
OUT = REPO / "data" / "d398_state_premise.json"

MINING = (FIX / "us_shorts_daily_raw.csv.gz", FIX / "us_shorts_daily_raw_events.json")
ETF = (FIX / "universe_daily_2015_2024_raw.csv.gz", FIX / "universe_daily_2015_2024_raw_events.json")

# the overlay levels, declared in the pre-registration before any count was seen (section 3)
ER_WINDOWS = (10, 21, 63)
ER_LEVELS = (0.3, 0.5, 0.7)
BAND_X = (0.10, 0.25, 0.50)
VOL_WIN = 21                      # rvol21, the programme's standard measure
SMA_WIN = 300                     # the principal's specification

# the three 15m single-name sets, zero overlap; see spec section 1
INTRADAY_SETS = ("cohort4_intraday_15m_raw", "cohort3_intraday_15m_raw", "holdout_intraday_15m_raw")


# ------------------------------------------------------------------ the state
def state_grids(panel, cleaned, UO, PV):
    """`g_lo`, `g_hi` as (n, T) on the panel grid, each fitted on the name's OWN bars.

    S2's `rolling_fit` unmodified, so S2's WINDOW, MIN_PIVOTS and the D173 confirmation
    lag (the window usable at t is [t-WINDOW, t-k], NOT [t-WINDOW, t]) come with it."""
    n, T = panel.closes.shape
    g_lo = np.full((n, T), np.nan)
    g_hi = np.full((n, T), np.nan)
    for i, s in enumerate(panel.symbols):
        bars = cleaned[s]
        at = np.flatnonzero(panel.live[i])
        assert at.size == len(bars), \
            f"[E] {s}: live bars {at.size} != cleaned rows {len(bars)} -- the scatter would misalign"
        ps = PV(bars, UO.K)
        lo_i = np.array([p.index for p in ps if p.sign < 0], dtype=int)
        hi_i = np.array([p.index for p in ps if p.sign > 0], dtype=int)
        lo_p = np.log([p.price for p in ps if p.sign < 0]) if lo_i.size else np.array([])
        hi_p = np.log([p.price for p in ps if p.sign > 0]) if hi_i.size else np.array([])
        gl, _ = UO.rolling_fit(len(bars), lo_i, lo_p, UO.K)
        gh, _ = UO.rolling_fit(len(bars), hi_i, hi_p, UO.K)
        g_lo[i, at] = gl
        g_hi[i, at] = gh
    return g_lo, g_hi


def warm_mask(live, w):
    """True where a name has at least `w` of its OWN live bars behind it.

    WHY THIS IS NEEDED AND WHY [W] CAUGHT ITS ABSENCE. `rolling_fit` clips the window's lower
    edge to 0 (`lo = np.clip(t - WINDOW, 0, n_bars)`), so before a name's 252nd bar it fits an
    EXPANDING window and emits a slope as soon as MIN_PIVOTS=3 pivots exist -- possibly over
    thirty bars. That is not "a confirmed structural trend over the past year".

    S2 carries exactly this guard: `signals` zeroes `up[:, :start]` and `build` asserts
    `WINDOW < start`. Its `start` is a PANEL-WIDE bar index, shared with S1 so both books score
    identical bars; on a ragged panel where names begin at different times the faithful analogue
    is PER-NAME, which is also what this record's section 2 and [W] declared."""
    out = np.zeros_like(live)
    for i in range(live.shape[0]):
        at = np.flatnonzero(live[i])
        if at.size > w:
            out[i, at[w:]] = True
    return out


def states(g_lo, g_hi, warm=None, delta=0.0):
    """`delta` is the LEVEL dead band of amendment 9 -- both slopes must clear it in the state's
    own direction. delta=0.0 is the section 1 definition exactly and is the sweep's control.

    NOT to be confused with a dead band on the gradient's CHANGE (hysteresis), which stabilises
    the line and leaves the frequency alone. Amendment 9a is the distinction."""
    ok = np.isfinite(g_lo) & np.isfinite(g_hi)
    if warm is not None:
        ok = ok & warm
    return {"UP": (g_lo > delta) & (g_hi > delta) & ok,
            "DOWN": (g_lo < -delta) & (g_hi < -delta) & ok}


# the level dead band, in log-return per bar, frozen in amendment 9b before any cell was computed
DELTAS = (0.0, 1e-4, 2e-4, 5e-4, 1e-3, 2e-3)
BARS_PER_YEAR = 252


def delta_sweep(g_lo, g_hi, warm, elig, live, rows_by_universe):
    """Amendment 9: frequency, episodes and durations at each level dead band."""
    out = {}
    for uni, rows in rows_by_universe.items():
        addr = int((elig & live & warm)[rows].sum())
        for d in DELTAS:
            S = states(g_lo, g_hi, warm, d)
            for nm, msk in S.items():
                m = (msk & elig)[rows]
                lens = []
                eps = 0
                for i in range(m.shape[0]):
                    st, ln = episodes_of(m[i])
                    eps += st.size
                    lens.append(ln)
                L = np.concatenate(lens) if lens else np.empty(0, int)
                bars = int(m.sum())
                out[f"{uni}|{nm}|{d:g}"] = dict(
                    universe=uni, direction=nm, delta=d,
                    annualised=round(float(np.expm1(BARS_PER_YEAR * d)), 4),
                    bars_in_state=bars,
                    share_of_addressable=round(bars / addr, 5) if addr else None,
                    episodes=int(eps),
                    median_len=float(np.median(L)) if L.size else None,
                    p90_len=float(np.quantile(L, .90)) if L.size else None,
                    names_hit=int((m.sum(axis=1) > 0).sum()))
    return out


def sma_own(v_nT, live_nT, w):
    """SMA over each name's OWN live bars, scattered back. Each window is summed DIRECTLY --
    not as a difference of cumulative sums, which is the reordering that broke `er_grid`."""
    n, T = v_nT.shape
    out = np.full((n, T), np.nan)
    for i in range(n):
        at = np.flatnonzero(live_nT[i])
        if at.size < w:
            continue
        x = v_nT[i, at]
        win = np.lib.stride_tricks.sliding_window_view(x, w)
        out[i, at[w - 1:]] = win.mean(axis=-1)
    return out


def episodes_of(mask_row):
    """(start, length) for every run of True. One pass, no allocation per run."""
    idx = np.flatnonzero(mask_row)
    if idx.size == 0:
        return np.empty(0, int), np.empty(0, int)
    brk = np.flatnonzero(np.diff(idx) != 1)
    starts = np.concatenate(([idx[0]], idx[brk + 1]))
    ends = np.concatenate((idx[brk], [idx[-1]]))
    return starts, ends - starts + 1


# ------------------------------------------------------------------ self-test
def selftest() -> int:
    print("D398 SELF-TEST -- episodes, the direct-sum SMA, and two breaks that must be caught\n")

    m = np.array([0, 1, 1, 1, 0, 0, 1, 0, 1, 1], bool)
    st, ln = episodes_of(m)
    assert list(st) == [1, 6, 8] and list(ln) == [3, 1, 2], f"episodes wrong: {st} {ln}"
    assert ln.sum() == m.sum(), "[H] episode lengths do not sum to bars-in-state"
    print(f"    [H] episodes on a hand mask: starts {list(st)} lengths {list(ln)}, "
          f"sum {ln.sum()} == {m.sum()} bars in state")

    v = np.arange(1, 11, dtype=float)[None, :]
    lv = np.ones((1, 10), bool)
    s3 = sma_own(v, lv, 3)
    assert np.isnan(s3[0, :2]).all(), "[W] SMA leaked before its own warm-up"
    assert np.allclose(s3[0, 2:], [2, 3, 4, 5, 6, 7, 8, 9]), f"[H] SMA wrong: {s3}"
    print(f"    [H] SMA(3) on 1..10 = {list(s3[0, 2:].astype(int))}, first two NaN "
          f"([W] no value before the window exists)")

    # a hole must not shift the scatter: bar 5 missing, SMA lands on OWN bars
    lv2 = np.ones((1, 10), bool)
    lv2[0, 5] = False
    v2 = np.full((1, 10), np.nan)
    v2[0, lv2[0]] = np.arange(1, 10, dtype=float)
    s2 = sma_own(v2, lv2, 3)
    assert np.isnan(s2[0, 5]), "[E] the SMA wrote a value on a bar the name was not live"
    print("    [E] with an internal hole the SMA writes only on the name's OWN live bars")

    lv3 = np.ones((1, 8), bool)
    lv3[0, 2] = False                                   # a hole: own bars are 0,1,3,4,5,6,7
    wm = warm_mask(lv3, 3)
    assert list(wm[0]) == [False, False, False, False, True, True, True, True], wm
    print(f"    [W] warm_mask(w=3) with a hole at bar 2 opens at grid bar 4, "
          f"i.e. after THREE of the name's OWN bars, not three grid bars")

    g_lo = np.array([[0.1, -0.1, 0.1, np.nan]])
    g_hi = np.array([[0.2, -0.2, -0.2, 0.1]])
    S = states(g_lo, g_hi)
    Sw = states(g_lo, g_hi, np.array([[False, True, True, True]]))
    assert not Sw["UP"][0, 0] and S["UP"][0, 0], "[W] the warm-up mask does not gate the state"
    print("    [W] a warm-up mask removes a state bar that the unmasked call keeps")
    assert list(S["UP"][0]) == [True, False, False, False], S["UP"]
    assert list(S["DOWN"][0]) == [False, True, False, False], S["DOWN"]
    print("    [H] UP and DOWN are exclusive, and a NaN slope is in neither")

    raised = False
    try:
        bad = np.array([0, 1, 1, 0], bool)
        st2, ln2 = episodes_of(bad)
        assert ln2.sum() == bad.sum() + 1, "planted"
    except AssertionError:
        raised = True
    assert raised, "[X] THE EPISODE CHECK CANNOT FAIL -- a wrong total passed"
    print("    [X] a wrong bars-in-state total IS CAUGHT")

    raised = False
    try:
        assert np.isnan(sma_own(v, lv, 3)[0, 1]), "ok"
        assert not np.isnan(sma_own(v, lv, 3)[0, 1]), "[W] planted: a leaked warm-up value"
    except AssertionError:
        raised = True
    assert raised, "[X] THE WARM-UP CHECK CANNOT FAIL"
    print("    [X] a leaked SMA warm-up value IS CAUGHT")
    print("\nSELF-TEST PASSED\n")
    return 0


# ------------------------------------------------------------------ [S2] the pin
def pin(UO, PV, RP) -> int:
    """[S2] On the 57-ETF panel this file's ragged path must reduce to S2's own, bit-identically.

    LOADED THROUGH S2'S OWN LOADER (`UO.L.load_panel`, i.e. run_macd_ladder), not through
    `load_ragged` -- the ETF fixture predates the gates block and `assert_gates_passed` refuses it,
    which is the gate discipline working and is not something to weaken for a pin. Using S2's own
    loader also makes this a stronger comparison: S2's bars, S2's fit, against this file's ragged
    scatter."""
    print("D398 [S2] PIN -- the ragged path against S2's own runner on the 57 ETFs\n")
    p57, cleaned = UO.L.load_panel()
    n, T = p57.closes.shape

    class _Shim:
        """`state_grids` needs only these three, and `live` is all-True here by construction:
        `load_panel` refuses a universe whose symbols have different bar counts."""
        symbols = p57.symbols
        closes = p57.closes
        live = np.ones((n, T), bool)

    panel = _Shim()
    assert all(len(cleaned[s]) == T for s in panel.symbols), \
        "[S2] a symbol is not full length; the pin's local==global premise fails"
    print(f"    ETF panel {n} x {T}, every symbol full length "
          f"(so local index == grid column, which is why S2 could pass the panel T)")

    g_lo, g_hi = state_grids(panel, cleaned, UO, PV)

    # S2's own path, on the same bars
    s_lo = np.full((n, T), np.nan)
    s_hi = np.full((n, T), np.nan)
    for i, s in enumerate(panel.symbols):
        ps = PV(cleaned[s], UO.K)
        li = np.array([p.index for p in ps if p.sign < 0], dtype=int)
        hj = np.array([p.index for p in ps if p.sign > 0], dtype=int)
        s_lo[i], _ = UO.rolling_fit(T, li,
                                    np.log([p.price for p in ps if p.sign < 0]) if li.size else np.array([]), UO.K)
        s_hi[i], _ = UO.rolling_fit(T, hj,
                                    np.log([p.price for p in ps if p.sign > 0]) if hj.size else np.array([]), UO.K)

    assert np.array_equal(g_lo, s_lo, equal_nan=True), "[S2] g_lo differs from S2's own"
    assert np.array_equal(g_hi, s_hi, equal_nan=True), "[S2] g_hi differs from S2's own"
    up_mine = states(g_lo, g_hi)["UP"]
    ok = ~(np.isnan(s_lo) | np.isnan(s_hi))
    up_s2 = (s_lo > 0) & (s_hi > 0) & ok
    assert np.array_equal(up_mine, up_s2), "[S2] the UP mask differs from S2's own"
    print(f"    [S2] g_lo, g_hi and the UP mask are BIT-IDENTICAL to S2's path "
          f"over {n * T:,} cells ({int(up_mine.sum()):,} UP bars)")

    # [X] the pin must be able to fail
    raised = False
    try:
        broken = s_lo.copy()
        broken[0, 500] = (0.0 if not np.isfinite(broken[0, 500]) else broken[0, 500]) + 1e-12
        assert np.array_equal(g_lo, broken, equal_nan=True), "[S2] planted mismatch"
    except AssertionError:
        raised = True
    assert raised, "[X] THE PIN CANNOT FAIL -- a perturbed slope passed"
    print("    [X] a slope perturbed by 1e-12 IS CAUGHT by the pin\n")
    print("[S2] PIN PASSED\n")
    return 0


# ------------------------------------------------------------------ [L] causality
def causality(panel, cleaned, UO, PV, LA, rng, k_probe=250) -> dict:
    """[L] `g_lo`/`g_hi` at bar t, recomputed from a panel TRUNCATED at t, must equal the
    full-panel value. A pivot needs k bars after it, and the fit window ends at t-k, so
    truncation at t+1 removes nothing the value at t was entitled to read."""
    n, T = panel.closes.shape
    live = panel.live
    cand = [(i, t) for i in rng.choice(n, size=min(60, n), replace=False)
            for t in rng.choice(np.flatnonzero(live[i]), size=5, replace=False)
            if t >= UO.WINDOW]
    rng.shuffle(cand)
    cand = cand[:k_probe]
    checked = 0
    for i, t in cand:
        s = panel.symbols[i]
        at = np.flatnonzero(live[i])
        j = int(np.searchsorted(at, t))
        bars = cleaned[s][:j + 1]                      # every bar up to and including t
        if len(bars) <= UO.WINDOW:
            continue
        ps = PV(bars, UO.K)
        li = np.array([p.index for p in ps if p.sign < 0], dtype=int)
        gl, _ = UO.rolling_fit(len(bars), li,
                               np.log([p.price for p in ps if p.sign < 0]) if li.size else np.array([]), UO.K)
        full = G_LO_CACHE[i, t]
        a, b = gl[j], full
        assert (np.isnan(a) and np.isnan(b)) or a == b, \
            f"[L] {s} bar {t}: truncated {a!r} != full {b!r} -- the slope reads its own future"
        checked += 1
    assert checked >= 50, f"[L] only {checked} probes ran; the audit is not exercised"

    def _broken(gl_row, full_row):
        assert np.array_equal(gl_row, full_row, equal_nan=True), "[L] shifted grid"

    row = G_LO_CACHE[0]
    LA.raises_on_broken(_broken, np.roll(row, 1), row)
    return dict(probes=checked, note="truncated-panel recompute equals the full-panel value")


G_LO_CACHE = None


# ------------------------------------------------------------------ the measurement
def summarise(mask, elig, live, warm, cohort_dead, er, band):
    """Every quantity section 4 asks for, for one direction on one universe.

    EVERY GRID IS ALREADY ROW-SLICED TO THIS UNIVERSE. The first version re-indexed the full
    (n, T) grids inside the 39-key retention loop, which copies 6.6M cells per key; slicing once
    per universe instead is the same arithmetic on the same cells."""
    m = mask & elig
    n_rows = m.shape[0]
    lens_all, per_name = [], []
    onsets = 0
    for i in range(n_rows):
        st, ln = episodes_of(m[i])
        onsets += st.size
        lens_all.append(ln)
        per_name.append(int(m[i].sum()))
    lens = np.concatenate(lens_all) if lens_all else np.empty(0, int)
    bars = int(m.sum())
    denom = int((elig & live).sum())
    addr = int((elig & live & warm).sum())
    out = dict(
        names=n_rows,
        bars_in_state=bars,
        eligible_live_bars=denom,
        addressable_bars=addr,
        share_of_eligible=round(bars / denom, 5) if denom else None,
        share_of_addressable=round(bars / addr, 5) if addr else None,
        episodes=int(onsets),
        names_with_an_episode=int(sum(1 for x in per_name if x > 0)),
        episode_len=dict(
            median=float(np.median(lens)) if lens.size else None,
            p25=float(np.quantile(lens, .25)) if lens.size else None,
            p75=float(np.quantile(lens, .75)) if lens.size else None,
            p90=float(np.quantile(lens, .90)) if lens.size else None,
            max=int(lens.max()) if lens.size else None,
            mean=float(lens.mean()) if lens.size else None),
        bars_per_name=dict(
            median=float(np.median(per_name)) if per_name else None,
            max=int(max(per_name)) if per_name else None),
    )
    # Q6: how much of the state do DEAD names carry?
    #
    # THE HEADCOUNT SHARE IS THE WRONG DENOMINATOR AND Q6 USED IT. A dead name is short-lived,
    # and the state costs 252 of its OWN bars in warm-up before it can be in any state at all, so
    # the dead cohort contributes far fewer ADDRESSABLE bars than names. Comparing a share of
    # state bars against a share of NAMES therefore measures lifespan, not downtrend. The
    # denominator that answers the design question is the dead cohort's share of eligible
    # post-warm-up bars -- what a book could have traded -- and both are reported.
    nd = int(cohort_dead.sum())
    addressable = elig & live & warm            # what a book could have traded at all
    out["dead_share_of_names"] = round(nd / n_rows, 4) if n_rows else None
    out["dead_share_of_state_bars"] = round(int(m[cohort_dead].sum()) / bars, 4) if bars and nd else None
    dn = int(addressable.sum())
    out["dead_share_of_addressable_bars"] = \
        round(int(addressable[cohort_dead].sum()) / dn, 4) if dn and nd else None
    if out["dead_share_of_state_bars"] is not None and out["dead_share_of_addressable_bars"]:
        out["dead_tilt"] = round(out["dead_share_of_state_bars"] /
                                 out["dead_share_of_addressable_bars"], 4)

    # retention under each overlay, and the intersection (section 3c: counts, never P&L)
    ret = {}
    erk = {(w, lv): (m & (g >= lv)) for w, g in er.items() for lv in ER_LEVELS}
    for (w, lv), keep in erk.items():
        ret[f"er{w}>={lv}"] = round(int(keep.sum()) / bars, 4) if bars else None
    for x, b in band.items():
        ret[f"band<={x}"] = round(int((m & b).sum()) / bars, 4) if bars else None
    for (w, lv), keep in erk.items():
        for x, b in band.items():
            ret[f"er{w}>={lv} AND band<={x}"] = round(int((keep & b).sum()) / bars, 4) if bars else None
    out["retention"] = ret
    return out


def main() -> int:
    global G_LO_CACHE
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--pin", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    from backtest_framework.research.structure import pivots as PV
    UO = _load("d240_uptrend", "run_uptrend_onset.py")
    RP = _load("ragged_panel", "ragged_panel.py")
    LA = _load("lag_audit", "lag_audit.py")

    if a.pin:
        return pin(UO, PV, RP)
    if not a.run:
        ap.error("pass --selftest, --pin or --run")

    selftest()
    pin(UO, PV, RP)

    t0 = time.time()
    PREP = _load("d348p", "d348_prep.py")
    P = PREP.prep(need_grids=False, verbose=False)
    panel, cleaned = RP.load_ragged(*MINING, fee_bps=0.0, dividend_bound=True)
    n, T = panel.closes.shape
    assert list(P["symbols"]) == list(panel.symbols), "[E] prep and panel disagree on symbols"
    assert list(P["dates"]) == list(panel.dates), "[E] prep and panel disagree on the date grid"
    elig = np.asarray(P["elig"]).T                                  # prep is (T, n); panel is (n, T)
    live = np.asarray(panel.live)
    assert elig.shape == (n, T), f"[E] eligibility is {elig.shape}, expected {(n, T)}"
    assert not (elig & ~live).any(), "[E] an eligible bar sits outside the name's live window"
    print(f"  loaded in {time.time() - t0:.0f}s | {n} names x {T} bars | "
          f"{int(live.sum()):,} live, {int(elig.sum()):,} eligible", flush=True)

    t1 = time.time()
    g_lo, g_hi = state_grids(panel, cleaned, UO, PV)
    G_LO_CACHE = g_lo
    warm = warm_mask(live, UO.WINDOW)
    raw = states(g_lo, g_hi)
    S = states(g_lo, g_hi, warm)
    cut = {k: int(raw[k].sum()) - int(S[k].sum()) for k in S}
    print(f"  state grids in {time.time() - t1:.0f}s "
          f"(k={UO.K}, window={UO.WINDOW}, min_pivots={UO.MIN_PIVOTS}, all imported from S2)",
          flush=True)
    print(f"    warm-up: rolling_fit's window EXPANDS below {UO.WINDOW} bars, so it emits a slope "
          f"on as few as {UO.MIN_PIVOTS} pivots. Masking each name's first {UO.WINDOW} own bars "
          f"removes UP {cut['UP']:,} and DOWN {cut['DOWN']:,} state bars "
          f"({100 * cut['UP'] / max(int(raw['UP'].sum()), 1):.1f}% / "
          f"{100 * cut['DOWN'] / max(int(raw['DOWN'].sum()), 1):.1f}%)", flush=True)

    caus = causality(panel, cleaned, UO, PV, LA, np.random.default_rng(398))
    print(f"    [L] {caus['probes']} truncated-panel recomputes equal the full-panel slope; "
          f"[X] a shifted grid IS CAUGHT", flush=True)

    # [W] no state bar before the name's own WINDOW-th bar. This FIRED on the first run
    # (AA in UP before its own 252nd bar) and the fix was to implement the guard the
    # pre-registration declared, not to relax the assertion. S2's own `build` carries the
    # same invariant as `assert WINDOW < start`.
    for nm, msk in S.items():
        for i in range(n):
            at = np.flatnonzero(live[i])
            early = msk[i, at[:UO.WINDOW]] if at.size else np.empty(0, bool)
            assert not early.any(), f"[W] {panel.symbols[i]} is in {nm} before its own {UO.WINDOW}th bar"
    assert raw["UP"].sum() > S["UP"].sum(), "[X] the warm-up removed NOTHING -- the guard is vacuous"
    print(f"    [W] no state bar precedes a name's own {UO.WINDOW}th bar, on either side "
          f"(and the guard is not vacuous: it removes {cut['UP']:,} UP bars)", flush=True)

    # the overlays
    t2 = time.time()
    A1 = _load("a1_er", "a1_er_stage0.py")
    er = {w: A1.er_grid(panel.closes, live, w) for w in ER_WINDOWS}
    v = np.asarray(P["score"]("rvol21"))
    assert v.shape == (n, T), f"[E] rvol21 is {v.shape}, expected {(n, T)}"
    s300 = sma_own(v, live, SMA_WIN)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = v / s300
    band = {x: np.isfinite(r) & (np.abs(r - 1.0) <= x) for x in BAND_X}
    print(f"  overlays in {time.time() - t2:.0f}s | ER windows {ER_WINDOWS} | "
          f"band on rvol{VOL_WIN}/SMA{SMA_WIN}, X {BAND_X}", flush=True)

    # cohorts and the 15m-reachable slice
    meta = json.loads((FIX / "us_shorts_daily_raw.meta.json").read_text())
    dead = np.array([meta["symbols"][s]["cohort"] == "dead" for s in panel.symbols])
    reach = set()
    for f in INTRADAY_SETS:
        d = json.loads((FIX / f"{f}.meta.json").read_text())
        reach.update(d["symbols_included"])
    pos = {s: i for i, s in enumerate(panel.symbols)}
    missing = sorted(x for x in reach if x not in pos)
    slice15 = np.array(sorted(pos[s] for s in reach if s in pos))
    all_rows = np.arange(n)
    print(f"  15m-reachable single names: {len(reach)} declared, {slice15.size} present in the "
          f"daily fixture" + (f"; MISSING {missing}" if missing else ""), flush=True)

    res = dict(
        study=398, spec="docs/decisions/D398-the-structural-state-premise-check.md",
        build="us_shorts_daily_raw via load_ragged(dividend_bound=True); keep_v2 + F0 eligibility; "
              "S2's k=3/WINDOW=252/MIN_PIVOTS=3 imported from run_uptrend_onset",
        statistic="counts and durations only. NO return, NO cost, NO null. Admits nothing (R15).",
        universe=dict(names=n, bars=T, live=int(live.sum()), eligible=int(elig.sum()),
                      dead_names=int(dead.sum()), dead_share=round(float(dead.mean()), 4),
                      span=[panel.dates[0], panel.dates[-1]]),
        intraday_reachable=dict(declared=len(reach), present=int(slice15.size), missing=missing,
                                names=[panel.symbols[i] for i in slice15]),
        warmup=dict(bars=UO.WINDOW, per="each name's own live bars",
                    removed_UP=cut["UP"], removed_DOWN=cut["DOWN"],
                    note="rolling_fit's window expands below WINDOW and emits a slope on as few "
                         "as MIN_PIVOTS pivots; [W] caught the guard's absence on the first run "
                         "(AA in UP before its own 252nd bar) and it was implemented, not relaxed"),
        causality=caus, cells={})
    for universe, rows in (("all_1573", all_rows), ("reachable_15m", slice15)):
        el_u, lv_u, wm_u, dd_u = elig[rows], live[rows], warm[rows], dead[rows]
        er_u = {w: g[rows] for w, g in er.items()}
        bd_u = {x: b[rows] for x, b in band.items()}
        for nm, msk in S.items():
            res["cells"][f"{universe}|{nm}"] = summarise(msk[rows], el_u, lv_u, wm_u, dd_u,
                                                         er_u, bd_u)

    # amendment 9 -- the LEVEL dead band sweep
    t3 = time.time()
    res["delta_sweep"] = delta_sweep(g_lo, g_hi, warm, elig, live,
                                     {"all_1573": all_rows, "reachable_15m": slice15})
    # the control MUST reproduce section 1 exactly, or the sweep is measuring a different object
    for uni in ("all_1573", "reachable_15m"):
        for nm in ("UP", "DOWN"):
            a = res["delta_sweep"][f"{uni}|{nm}|0"]["bars_in_state"]
            b = res["cells"][f"{uni}|{nm}"]["bars_in_state"]
            assert a == b, f"[D0] delta=0 gives {a:,} bars for {uni}|{nm}, section 1 gives {b:,}"
    print(f"  delta sweep in {time.time() - t3:.0f}s | [D0] delta=0 reproduces section 1 "
          f"bar-for-bar on all four cells", flush=True)

    # [P] persist BEFORE rendering
    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  [P] {OUT.relative_to(REPO)} written before anything is rendered "
          f"({(time.time() - t0) / 60:.1f} min total)\n")

    render(res)
    return 0


def render(res):
    C = res["cells"]
    print("  THE STATE -- counts and durations, both directions, both universes\n")
    print(f"  {'universe':>14s} {'dir':>5s} {'names':>6s} {'episodes':>9s} {'bars in state':>14s} "
          f"{'% of addr':>10s} {'med len':>8s} {'p90':>6s} {'max':>6s} {'names hit':>10s}")
    for k, c in C.items():
        u, d = k.split("|")
        el = c["episode_len"]
        print(f"  {u:>14s} {d:>5s} {c['names']:>6,} {c['episodes']:>9,} {c['bars_in_state']:>14,} "
              f"{100 * (c['share_of_addressable'] or 0):>9.2f}% {el['median'] or 0:>8.0f} "
              f"{el['p90'] or 0:>6.0f} {el['max'] or 0:>6,} {c['names_with_an_episode']:>10,}")

    print("\n  SURVIVORSHIP (Q6) -- and the headcount denominator Q6 used is the WRONG one:\n"
          "  a dead name is short-lived and spends 252 of its own bars in warm-up, so its share\n"
          "  of NAMES overstates the bars it could ever contribute. Both are shown; the tilt\n"
          "  column is state share / addressable share, and 1.00 means no tilt at all.\n")
    print(f"  {'universe':>14s} {'dir':>5s} {'dead % names':>13s} {'dead % addressable':>19s} "
          f"{'dead % of state':>16s} {'TILT':>6s}")
    for k, c in C.items():
        u, d = k.split("|")
        dn, da, db = (c["dead_share_of_names"], c.get("dead_share_of_addressable_bars"),
                      c["dead_share_of_state_bars"])
        tl = c.get("dead_tilt")
        print(f"  {u:>14s} {d:>5s} {100 * (dn or 0):>12.1f}% {100 * (da or 0):>18.1f}% "
              f"{100 * (db or 0):>15.1f}% {tl if tl is not None else float('nan'):>6.2f}")

    print("\n  RETENTION -- what each overlay leaves of the state (counts, never P&L)\n")
    keys = [f"er{w}>={lv}" for w in ER_WINDOWS for lv in ER_LEVELS] + [f"band<={x}" for x in BAND_X]
    print(f"  {'universe':>14s} {'dir':>5s} " + " ".join(f"{k:>13s}" for k in keys))
    for k, c in C.items():
        u, d = k.split("|")
        print(f"  {u:>14s} {d:>5s} " +
              " ".join(f"{100 * (c['retention'].get(x) or 0):>12.1f}%" for x in keys))

    print("\n  INDEPENDENCE (Q5) -- intersection against the product of the marginals.\n"
          "  ONLY cells breaching 5 pp are listed; an empty table means Q5 HELD everywhere.\n")
    print(f"  {'universe':>14s} {'dir':>5s} {'cell':>26s} {'inter':>8s} {'product':>9s} {'gap pp':>8s}")
    breaches = 0
    for k, c in C.items():
        u, d = k.split("|")
        R = c["retention"]
        for w in ER_WINDOWS:
            for lv in ER_LEVELS:
                for x in BAND_X:
                    a, b = R.get(f"er{w}>={lv}"), R.get(f"band<={x}")
                    i = R.get(f"er{w}>={lv} AND band<={x}")
                    if a is None or b is None or i is None:
                        continue
                    gap = 100 * (i - a * b)
                    if abs(gap) >= 5.0:
                        breaches += 1
                        print(f"  {u:>14s} {d:>5s} {f'er{w}>={lv} x band<={x}':>26s} "
                              f"{100 * i:>7.1f}% {100 * a * b:>8.1f}% {gap:>+7.1f}")
    n_pairs = len(C) * len(ER_WINDOWS) * len(ER_LEVELS) * len(BAND_X)
    print(f"    {breaches} of {n_pairs} intersections breach 5 pp -- "
          f"Q5 {'FAILS' if breaches else 'HOLDS'} on all of them")

    print("\n  ONSET vs STATE -- the fork the design turns on\n")
    for k, c in C.items():
        u, d = k.split("|")
        print(f"    {u:>14s} {d:>5s}: {c['episodes']:>8,} onsets  vs  "
              f"{c['bars_in_state']:>10,} bars in state  "
              f"({c['bars_in_state'] / max(c['episodes'], 1):.0f} bars per episode)")

    D = res.get("delta_sweep")
    if D:
        print("\n  THE LEVEL DEAD BAND (amendment 9) -- does a steeper bar cut the 95%?\n")
        for uni in ("all_1573", "reachable_15m"):
            print(f"    {uni}")
            print(f"      {'delta':>8s} {'ann %/yr':>9s} {'dir':>5s} {'bars':>11s} {'% addr':>8s} "
                  f"{'episodes':>9s} {'med len':>8s} {'p90':>6s} {'names':>6s}")
            for d in DELTAS:
                for nm in ("UP", "DOWN"):
                    c = D[f"{uni}|{nm}|{d:g}"]
                    print(f"      {d:>8.4g} {100 * c['annualised']:>8.1f}% {nm:>5s} "
                          f"{c['bars_in_state']:>11,} "
                          f"{100 * (c['share_of_addressable'] or 0):>7.2f}% {c['episodes']:>9,} "
                          f"{c['median_len'] or 0:>8.0f} {c['p90_len'] or 0:>6.0f} "
                          f"{c['names_hit']:>6,}")
            print()
        print("    Q9 -- does the EPISODE COUNT peak in the interior?")
        for uni in ("all_1573", "reachable_15m"):
            for nm in ("UP", "DOWN"):
                seq = [D[f"{uni}|{nm}|{d:g}"]["episodes"] for d in DELTAS]
                top = int(np.argmax(seq))
                interior = 0 < top < len(DELTAS) - 1
                print(f"      {uni:>14s} {nm:>5s}: {seq}  peak at delta="
                      f"{DELTAS[top]:g} -> {'INTERIOR, Q9 holds' if interior else 'at an END, Q9 fails'}")

    print("\nThis is a MEASUREMENT. No return was computed, no operating point was chosen,")
    print("no 15-minute bar was read, and it admits nothing (R15).")


if __name__ == "__main__":
    raise SystemExit(main())
