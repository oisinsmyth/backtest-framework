"""D399 Stage 0 -- the ratcheted structural line, on DAILY bars only.

    uv run python scripts/run_d399_ratcheted_line.py --selftest
    uv run python scripts/run_d399_ratcheted_line.py --stage0

Spec: docs/decisions/D399-the-ratcheted-structural-line.md, committed BEFORE this file (R8).

STAGE 0 ONLY. No 15-minute bar is read. Stage 1 is NOT authorised by that record and is not here.

THE CONSTRUCTION, three objects (spec section 0):
  1. delta = 1e-3, the LEVEL dead band, FIXED by the principal on D398's measurement. NOT swept.
  2. h = delta, the gradient HYSTERESIS: the held gradient G does not update until a refit moves
     it by more than h. The state reads the HELD gradients, so hysteresis also suppresses flicker.
  3. the WIDENING RATCHET: between re-anchors the line's offset moves only AWAY from price. It is
     NOT a stop -- it defines a level price can RETURN to, and the return is the event.

TWO LINES, NOT ONE, AND THE DIRECTION IS A PROPERTY OF THE LINE NOT OF THE STATE. The low line
(fitted through swing lows) sits under price and widens DOWNWARD; the high line sits over price and
widens UPWARD. The state merely selects which one is read -- UP reads the low line, DOWN the high.
That is why the ratchet needs no knowledge of the state.

NOTHING IS REIMPLEMENTED. `pivots` from research.structure; `rolling_fit`, K, WINDOW, MIN_PIVOTS
from S2's own runner; `state_grids`, `warm_mask`, `episodes_of`, `sma_own` from D399's own premise
check (D398); `er_grid` from a1_er_stage0; the kernel and `two_c`/`pnl_bp` through run_d359.

ASSERTIONS [S2][D0][R][L][X][W][E][P] -- spec section 8, including its two written corrections.
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
OUT = REPO / "data" / "d399_stage0.json"
MINING = (FIX / "us_shorts_daily_raw.csv.gz", FIX / "us_shorts_daily_raw_events.json")

# ---- frozen in the pre-registration, before any number was seen -------------
DELTA = 1e-3                      # section 3a, fixed by the principal on D398 amendment 9
H = DELTA                         # section 3b: h := delta, not a second free parameter
ER_CELLS = ((10, 0.3), (10, 0.5), (21, 0.3), (21, 0.5))     # er63 dropped (D398 section 1a)
BANDS = (0.25, 0.50)
PRIMARY = ((10, 0.3), 0.25)       # section 3e
CAPS = (5, 10, 20)
PRIMARY_CAP = 10
K0_MIN_EVENTS = 400               # section 4's kill condition
INTRADAY_SETS = ("cohort4_intraday_15m_raw", "cohort3_intraday_15m_raw", "holdout_intraday_15m_raw")


# ------------------------------------------------------- the hysteresis + ratchet
def ratchet(g, c, live, h, widen):
    """One causal forward pass per name. Returns (G, L, anchored).

    `widen` is -1 for the LOW line (its offset may only fall) and +1 for the HIGH line (may only
    rise). No knowledge of the state is used or needed.

    A pure Python loop because it is genuinely sequential -- bar t's held gradient depends on
    bar t-1's. Vectorising a recurrence is not one of the three rewrites CLAUDE.md allows."""
    n, T = g.shape
    G = np.full((n, T), np.nan)
    L = np.full((n, T), np.nan)
    anc = np.zeros((n, T), bool)
    for i in range(n):
        at = np.flatnonzero(live[i])
        gi, ci = g[i, at], c[i, at]
        Gh = np.nan
        Lh = np.nan
        for j in range(at.size):
            gj, cj = gi[j], ci[j]
            if not (np.isfinite(gj) and np.isfinite(cj)):
                continue                      # G, L stay NaN here; the state cannot be on
            fresh = gj * j + cj               # the fresh fit's LEVEL at this local bar
            if not np.isfinite(Gh) or abs(gj - Gh) > h:
                Gh, Lh, a = gj, fresh, True   # RE-ANCHOR
            else:
                adv = Lh + Gh                 # the held line advances at its own gradient
                Lh = min(adv, fresh) if widen < 0 else max(adv, fresh)
                a = False
            G[i, at[j]] = Gh
            L[i, at[j]] = Lh
            anc[i, at[j]] = a
    return G, L, anc


def assert_ratchet(G, L, live, anc, widen, label):
    """[R] between re-anchors the OFFSET moves only in the widening direction.

    The offset is L[t] - G*t in the name's OWN bar coordinates. Section 8's first draft asserted
    `L[t] - L[t-1] == G` exactly; that is FALSE whenever the ratchet binds, and the correction is
    recorded in the spec. The offset monotonicity is the invariant that actually holds."""
    n = G.shape[0]
    checked = 0
    for i in range(n):
        at = np.flatnonzero(live[i])
        Li, Gi, Ai = L[i, at], G[i, at], anc[i, at]
        ok = np.isfinite(Li) & np.isfinite(Gi)
        j = np.arange(at.size)
        off = np.where(ok, Li - Gi * j, np.nan)
        for t in range(1, at.size):
            if Ai[t] or not (ok[t] and ok[t - 1]):
                continue
            d = off[t] - off[t - 1]
            assert (d <= 1e-12) if widen < 0 else (d >= -1e-12), \
                f"[R] {label} offset moved TOWARD price at own-bar {t}: {d:+.3e}"
            checked += 1
    assert checked > 1000, f"[R] only {checked} non-anchor bars checked; the audit is not exercised"
    return checked


# ------------------------------------------------------------------ self-test
def selftest(UO=None) -> int:
    print("D399 SELF-TEST -- the ratchet, the hysteresis, and three breaks that must be caught\n")

    # a hand line: g constant at 0.01, fresh level wanders. widen=-1 (low line).
    live = np.ones((1, 6), bool)
    g = np.full((1, 6), 0.01)
    # c chosen so fresh = g*j + c takes the values below
    fresh = np.array([0.0, 0.05, 0.02, 0.30, 0.01, 0.40])
    c = fresh - 0.01 * np.arange(6)
    G, L, anc = ratchet(g, c[None, :], live, h=1.0, widen=-1)
    # h=1.0 >> any |g-G|=0, so ONE anchor at bar 0 and the ratchet runs thereafter
    assert list(anc[0]) == [True, False, False, False, False, False], anc
    exp = [0.0]
    for j in range(1, 6):
        exp.append(min(exp[-1] + 0.01, fresh[j]))
    assert np.allclose(L[0], exp), f"[H] ratchet {L[0]} != {exp}"
    print(f"    [H] low line, h=1.0: one anchor then min(advance, fresh) -> "
          f"{[round(float(x), 3) for x in L[0]]}")
    off = L[0] - G[0] * np.arange(6)
    assert np.all(np.diff(off) <= 1e-12), f"[R] offset rose: {off}"
    print(f"    [R] its offset is non-increasing: {[round(float(x), 3) for x in off]}")

    # widen=+1 mirrors exactly
    G2, L2, _ = ratchet(g, c[None, :], live, h=1.0, widen=+1)
    exp2 = [0.0]
    for j in range(1, 6):
        exp2.append(max(exp2[-1] + 0.01, fresh[j]))
    assert np.allclose(L2[0], exp2), f"[H] high line {L2[0]} != {exp2}"
    print(f"    [H] high line is the mirror: {[round(float(x), 3) for x in L2[0]]}")

    # hysteresis: h=0 re-anchors every bar, so G == g exactly ([D0]'s premise)
    gv = np.array([[0.01, 0.011, 0.03, 0.03, -0.02]])
    cv = np.zeros((1, 5))
    G0, _, anc0 = ratchet(gv, cv, np.ones((1, 5), bool), h=0.0, widen=-1)
    assert np.array_equal(G0[0], gv[0]), f"[D0] h=0 did not track the raw fit: {G0[0]}"
    print(f"    [D0] h=0 gives G == g exactly ({list(G0[0])}) -- the control the spec corrected")

    Gh, _, anch = ratchet(gv, cv, np.ones((1, 5), bool), h=0.005, widen=-1)
    assert list(anch[0]) == [True, False, True, False, True], anch
    assert np.allclose(Gh[0], [0.01, 0.01, 0.03, 0.03, -0.02]), Gh
    print(f"    [H] h=0.005: 0.011 is inside the band and held at 0.010; 0.03 and -0.02 re-anchor")

    # [X] three planted breaks
    for name, fn in (
        ("a ratchet moving TOWARD price",
         lambda: assert_ratchet(np.zeros((1, 4)), np.array([[0.0, 1.0, 2.0, 3.0]]),
                                np.ones((1, 4), bool), np.zeros((1, 4), bool), -1, "planted")),
        ("an under-exercised audit",
         lambda: assert_ratchet(G, L, live, anc, -1, "tiny")),
    ):
        raised = False
        try:
            fn()
        except AssertionError:
            raised = True
        assert raised, f"[X] THE AUDIT CANNOT FAIL -- {name} passed"
        print(f"    [X] {name} IS CAUGHT")

    raised = False
    try:
        assert np.array_equal(ratchet(gv, cv, np.ones((1, 5), bool), h=1e9, widen=-1)[0][0], gv[0]), \
            "[D0] planted: h=inf is NOT the control"
    except AssertionError:
        raised = True
    assert raised, "[X] h=inf passed as the control -- section 8's first draft said exactly this"
    print("    [X] h=inf FAILS as the control (it freezes G at the first value) -- "
          "the spec's own corrected error")
    print("\nSELF-TEST PASSED\n")
    return 0


# ------------------------------------------------------------------ stage 0
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--stage0", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not a.stage0:
        ap.error("pass --selftest or --stage0")
    selftest()

    from backtest_framework.research.structure import pivots as PV
    UO = _load("d240_uptrend", "run_uptrend_onset.py")
    RP = _load("ragged_panel", "ragged_panel.py")
    D398 = _load("d398", "run_d398_state_premise.py")
    A1 = _load("a1_er", "a1_er_stage0.py")
    LA = _load("lag_audit", "lag_audit.py")
    PREP = _load("d348p", "d348_prep.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    AT = _load("d392a", "run_d392_base_rate_atlas.py")
    V47 = V59.V47

    t0 = time.time()
    P = PREP.prep(need_grids=False, verbose=False)
    panel, cleaned = RP.load_ragged(*MINING, fee_bps=0.0, dividend_bound=True)
    n, T = panel.closes.shape
    assert list(P["symbols"]) == list(panel.symbols), "[E] prep and panel disagree on symbols"
    elig_nT = np.asarray(P["elig"]).T
    live = np.asarray(panel.live)
    print(f"  loaded in {time.time() - t0:.0f}s | {n} x {T} | {int(elig_nT.sum()):,} eligible",
          flush=True)

    # ---- the fits, with INTERCEPTS this time -------------------------------
    t1 = time.time()
    g_lo = np.full((n, T), np.nan); c_lo = np.full((n, T), np.nan)
    g_hi = np.full((n, T), np.nan); c_hi = np.full((n, T), np.nan)
    for i, s in enumerate(panel.symbols):
        bars = cleaned[s]
        at = np.flatnonzero(live[i])
        assert at.size == len(bars), f"[E] {s}: live {at.size} != rows {len(bars)}"
        ps = PV(bars, UO.K)
        for sign, gg, cc in ((-1, g_lo, c_lo), (+1, g_hi, c_hi)):
            idx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
            px = np.log([p.price for p in ps if p.sign == sign]) if idx.size else np.array([])
            sl, it = UO.rolling_fit(len(bars), idx, px, UO.K)
            gg[i, at] = sl
            cc[i, at] = it
    warm = D398.warm_mask(live, UO.WINDOW)
    print(f"  fits in {time.time() - t1:.0f}s (k={UO.K}, window={UO.WINDOW}, "
          f"min_pivots={UO.MIN_PIVOTS}, imported from S2)", flush=True)

    # ---- [S2] and [D0]: h = 0, delta = 0 must reproduce D398 ----------------
    G0lo, _, _ = ratchet(g_lo, c_lo, live, h=0.0, widen=-1)
    G0hi, _, _ = ratchet(g_hi, c_hi, live, h=0.0, widen=+1)
    assert np.array_equal(G0lo, g_lo, equal_nan=True), "[D0] h=0 low line != the raw fit"
    assert np.array_equal(G0hi, g_hi, equal_nan=True), "[D0] h=0 high line != the raw fit"
    S_raw = D398.states(g_lo, g_hi, warm, 0.0)
    d398 = json.loads((REPO / "data" / "d398_state_premise.json").read_text())
    for nm in ("UP", "DOWN"):
        got = int((S_raw[nm] & elig_nT).sum())
        want = d398["cells"][f"all_1573|{nm}"]["bars_in_state"]
        assert got == want, f"[D0] {nm}: {got:,} != D398's {want:,}"
    print(f"    [D0] at delta=0, h=0 the state reproduces D398 section 1 bar-for-bar "
          f"(UP {int((S_raw['UP'] & elig_nT).sum()):,}, "
          f"DOWN {int((S_raw['DOWN'] & elig_nT).sum()):,})", flush=True)

    # ---- the construction ---------------------------------------------------
    t2 = time.time()
    G_lo, L_lo, anc_lo = ratchet(g_lo, c_lo, live, h=H, widen=-1)
    G_hi, L_hi, anc_hi = ratchet(g_hi, c_hi, live, h=H, widen=+1)
    print(f"  ratchet in {time.time() - t2:.0f}s (h={H:g})", flush=True)
    n_lo = assert_ratchet(G_lo, L_lo, live, anc_lo, -1, "low")
    n_hi = assert_ratchet(G_hi, L_hi, live, anc_hi, +1, "high")
    print(f"    [R] the offset never moves toward price: {n_lo:,} low and {n_hi:,} high "
          f"non-anchor bars checked", flush=True)

    ok = np.isfinite(G_lo) & np.isfinite(G_hi) & warm
    UP = (G_lo > DELTA) & (G_hi > DELTA) & ok
    DOWN = (G_lo < -DELTA) & (G_hi < -DELTA) & ok
    logC = np.log(panel.closes, where=np.isfinite(panel.closes) & (panel.closes > 0),
                  out=np.full((n, T), np.nan))
    EV = {"UP": UP & (logC <= L_lo) & elig_nT, "DOWN": DOWN & (logC >= L_hi) & elig_nT}

    # [W] and [E]
    for nm, m in EV.items():
        assert not (m & ~warm).any(), f"[W] {nm} event before a name's own {UO.WINDOW}th bar"
        assert not (m & ~elig_nT).any(), f"[E] {nm} event on an ineligible bar"
    print(f"    [W][E] every event is past its name's own {UO.WINDOW}th bar and eligible",
          flush=True)

    # ---- [L] THE LAG AUDIT, and it is the one this file got wrong first time --
    # The event condition reads bar t's own close, so the mask handed to the kernel must be
    # bar t-1's events. Proved here on the real grids, in a second implementation that never
    # calls lag1_mask, and proved to RAISE on the unlagged mask the first run actually used.
    for nm in ("UP", "DOWN"):
        raw_T = np.ascontiguousarray(EV[nm].T)
        pos_T = LA.lag1_mask(raw_T)
        assert np.array_equal(pos_T[1:], raw_T[:-1]), f"[L] {nm} mask is not shifted one bar"
        assert not pos_T[0].any(), f"[L] {nm} opens a position on bar 0"
        LA.raises_on_broken(LA.assert_mask_is_lagged, raw_T, raw_T)
    print(f"    [L] the event reads bar t's OWN close, so every mask is shifted before the "
          f"kernel sees it; [X] the UNLAGGED mask RAISES", flush=True)

    # Q2: hysteresis against D398's raw-gradient state
    S_h = {"UP": UP, "DOWN": DOWN}
    q2 = {}
    for nm in ("UP", "DOWN"):
        raw = D398.states(g_lo, g_hi, warm, DELTA)[nm] & elig_nT
        het = S_h[nm] & elig_nT
        re_, he = [], []
        for i in range(n):
            re_.append(D398.episodes_of(raw[i])[1])
            he.append(D398.episodes_of(het[i])[1])
        R_ = np.concatenate(re_) if re_ else np.empty(0)
        H_ = np.concatenate(he) if he else np.empty(0)
        q2[nm] = dict(raw_bars=int(raw.sum()), held_bars=int(het.sum()),
                      raw_eps=int(R_.size), held_eps=int(H_.size),
                      raw_med=float(np.median(R_)) if R_.size else None,
                      held_med=float(np.median(H_)) if H_.size else None)

    # ---- overlays -----------------------------------------------------------
    er = {w: A1.er_grid(panel.closes, live, w) for w in (10, 21)}
    v = np.asarray(P["score"]("rvol21"))
    s300 = D398.sma_own(v, live, 300)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = v / s300
    band = {x: np.isfinite(r) & (np.abs(r - 1.0) <= x) for x in BANDS}

    meta = json.loads((FIX / "us_shorts_daily_raw.meta.json").read_text())
    dead = np.array([meta["symbols"][s]["cohort"] == "dead" for s in panel.symbols])
    reach = set()
    for f in INTRADAY_SETS:
        reach.update(json.loads((FIX / f"{f}.meta.json").read_text())["symbols_included"])
    pos = {s: i for i, s in enumerate(panel.symbols)}
    is15 = np.zeros(n, bool)
    for s in reach:
        if s in pos:
            is15[pos[s]] = True

    # ---- K0, on the primary --------------------------------------------------
    (pw, pl), pb_ = PRIMARY
    prim = {nm: EV[nm] & (er[pw] >= pl) & band[pb_] for nm in EV}
    k0 = {nm: int(prim[nm].sum()) for nm in prim}
    print(f"\n  EVENTS -- raw touch, then the PRIMARY cell (er{pw}>={pl} AND band<={pb_})\n")
    for nm in ("UP", "DOWN"):
        print(f"    {nm:>5s}: {int(EV[nm].sum()):>8,} touches -> {k0[nm]:>8,} primary events "
              f"({int(prim[nm][is15].sum()):>6,} on the 48 with 15m bars)")

    res = dict(study=399, stage=0, spec="docs/decisions/D399-the-ratcheted-structural-line.md",
               build="us_shorts_daily_raw via load_ragged(dividend_bound=True); keep_v2 + F0; F0; "
                     "next-open fill (D340); EB.simulate_event via run_d359 (R16)",
               delta=DELTA, h=H, primary=dict(er_window=pw, er_level=pl, band=pb_, cap=PRIMARY_CAP),
               hysteresis_vs_raw=q2,
               touches={k: int(m.sum()) for k, m in EV.items()},
               primary_events=k0,
               primary_events_on_15m_names={nm: int(prim[nm][is15].sum()) for nm in prim},
               k0_min=K0_MIN_EVENTS, cells={})

    if min(k0.values()) < K0_MIN_EVENTS:
        res["verdict"] = "K0 FIRED"
        OUT.write_text(json.dumps(res, indent=1))
        print(f"\n  *** K0 FIRES: the primary yields {min(k0.values()):,} events on the thinner "
              f"side, below the pre-registered {K0_MIN_EVENTS}. ***")
        print("  Section 4: the construction is not measurable as specified. THE RECORD STOPS.")
        print("  Widening the grid to rescue it is forbidden (D366's search; D393 section 9).")
        print(f"\n  [P] {OUT.relative_to(REPO)} written.")
        return 0

    # ---- the cells -----------------------------------------------------------
    sc = np.full((T, n), 50.0)
    print(f"\n  {'dir':>5s} {'cell':>22s} {'cap':>4s} {'trades':>8s} {'gross':>8s} {'2c':>7s} "
          f"{'net':>8s} {'ratio':>6s} {'atlas p95':>10s} {'+/-':>5s} {'vs floor':>9s}")
    for nm in ("UP", "DOWN"):
        side = "long" if nm == "UP" else "short"
        for (w, lv) in ER_CELLS:
            for x in BANDS:
                m_nT = EV[nm] & (er[w] >= lv) & band[x]
                raw = np.ascontiguousarray(m_nT.T)           # kernel masks are (T, n)
                # [L] THE EVENT READS BAR t'S OWN CLOSE, so it MUST be shifted before the
                # kernel sees it. `simulate_event` treats its mask as the bar the position
                # OPENS ON. Handing it the raw mask books the very down-move that created the
                # event -- which is D391's look-ahead, and the first run of this file had it.
                mask = LA.lag1_mask(raw)
                LA.assert_mask_is_lagged(mask, raw)
                for cap in CAPS:
                    run = V59.run_mirror if side == "long" else V59.run_short
                    r_ = run(P, mask, sc, "cap", cap)
                    tr = r_["trades"]
                    if not tr:
                        continue
                    p_ = V59.V47.pnl_bp(r_)
                    cost, half, px = V47.two_c(tr, P["HALF"]["PUB"], P["CLOSE"])
                    gross = float(p_.mean())
                    # HOLD-DRIVEN or not (D289 seventh amendment): cost is ONE round trip
                    # regardless of cap, so a longer hold raises gross per TRADE while per-BAR
                    # edge may fall. Reporting only the trade figure hides which one moved.
                    age = np.array([t_[2] for t_ in tr], float)
                    rows = np.array([t_[0] for t_ in tr], int)
                    d_ = dead[rows]
                    tot = float(p_.sum())
                    try:
                        fl = AT.lookup(json.loads((REPO / "data" / "d392_atlas.json").read_text()),
                                       len(tr), cap, side)
                        fp, fse = fl["p95"], fl["se_p95"]
                    except (ValueError, KeyError):
                        fp, fse = None, None
                    key = f"{nm}|er{w}>={lv}|band<={x}|cap{cap}"
                    res["cells"][key] = dict(
                        direction=nm, side=side, er_window=w, er_level=lv, band=x, cap=cap,
                        trades=len(tr), gross_bp=gross, two_c=float(cost),
                        held_half_spread=float(half), held_price=float(px),
                        net_bp=gross - float(cost),
                        ratio=gross / float(cost) if cost else None,
                        median_bp=float(np.median(p_)), win_rate=float((p_ > 0).mean()),
                        mean_age=float(age.mean()),
                        bp_per_bar=float(gross / age.mean()) if age.mean() else None,
                        # Q6: the return-side survivorship question D398 could not answer
                        dead_share_of_trades=float(d_.mean()),
                        dead_share_of_gross=(float(p_[d_].sum() / tot) if tot else None),
                        atlas_p95=fp, atlas_se=fse,
                        clears_atlas=(None if fp is None else bool(gross > fp)),
                        margin_in_se=(None if not fse else float((gross - fp) / fse)))
                    c_ = res["cells"][key]
                    print(f"  {nm:>5s} {f'er{w}>={lv} band<={x}':>22s} {cap:>4d} {len(tr):>8,} "
                          f"{gross:>+8.2f} {cost:>7.2f} {c_['net_bp']:>+8.2f} "
                          f"{(c_['ratio'] or 0):>6.2f} "
                          f"{(fp if fp is not None else float('nan')):>+10.2f} "
                          f"{(fse if fse is not None else float('nan')):>5.2f} "
                          f"{'ABOVE' if c_['clears_atlas'] else 'inside':>9s}", flush=True)

    # [P] persist before rendering the verdict
    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  [P] {OUT.relative_to(REPO)} written before the verdict is rendered")
    render(res, dead, prim, is15, EV, er, band)
    return 0


def render(res, dead, prim, is15, EV, er, band):
    C = res["cells"]
    (pw, pl), pb_ = PRIMARY
    print("\n  THE PRIMARY CELL, both sides\n")
    for nm in ("UP", "DOWN"):
        k = f"{nm}|er{pw}>={pl}|band<={pb_}|cap{PRIMARY_CAP}"
        c = C.get(k)
        if not c:
            print(f"    {nm}: no trades")
            continue
        print(f"    {nm:>5s}  {c['trades']:,} trades  gross {c['gross_bp']:+.2f}  "
              f"2c {c['two_c']:.2f}  net {c['net_bp']:+.2f}  ratio {c['ratio']:.2f}x  "
              f"atlas {c['atlas_p95']:+.2f} +/- {c['atlas_se']:.2f}  "
              f"margin {c['margin_in_se']:+.1f} SE")

    print("\n  Q3/Q4 -- does either side clear its atlas floor at the primary cap?")
    for nm in ("UP", "DOWN"):
        k = f"{nm}|er{pw}>={pl}|band<={pb_}|cap{PRIMARY_CAP}"
        c = C.get(k)
        if c and c["atlas_p95"] is not None:
            v = "CLEARS" if c["clears_atlas"] else "does NOT clear"
            unres = abs(c["margin_in_se"] or 0) < 2.0
            print(f"    {nm:>5s}: gross {c['gross_bp']:+.2f} vs floor {c['atlas_p95']:+.2f} "
                  f"-> {v}" + ("  [UNRESOLVED: inside 2 SE, D369/D373]" if unres else ""))

    print("\n  IS THE CAP GAIN HOLD-DRIVEN? (D289 seventh amendment)\n")
    print(f"  {'dir':>5s} {'cell':>22s} " + " ".join(f"{'cap' + str(c):>18s}" for c in CAPS))
    for nm in ("UP", "DOWN"):
        for (w, lv) in ER_CELLS:
            for x in BANDS:
                row = []
                for c in CAPS:
                    k = f"{nm}|er{w}>={lv}|band<={x}|cap{c}"
                    cc = C.get(k)
                    row.append(f"{cc['gross_bp']:+7.2f} /{cc['bp_per_bar']:5.2f}bpb"
                               if cc else f"{'-':>18s}")
                pb = [C[f"{nm}|er{w}>={lv}|band<={x}|cap{c}"]["bp_per_bar"] for c in CAPS
                      if f"{nm}|er{w}>={lv}|band<={x}|cap{c}" in C]
                tag = "  HOLD-DRIVEN" if len(pb) == len(CAPS) and pb[-1] < pb[0] else ""
                print(f"  {nm:>5s} {f'er{w}>={lv} band<={x}':>22s} " + " ".join(row) + tag)

    print("\n  Q6 -- does the SHORT side's P&L live in the names that delist?\n")
    print(f"  {'dir':>5s} {'cell':>22s} {'cap':>4s} {'dead % trades':>14s} {'dead % of gross':>16s}")
    for nm in ("UP", "DOWN"):
        for c in CAPS:
            k = f"{nm}|er{pw}>={pl}|band<={pb_}|cap{c}"
            cc = C.get(k)
            if cc and cc["dead_share_of_gross"] is not None:
                print(f"  {nm:>5s} {f'PRIMARY':>22s} {c:>4d} "
                      f"{100 * cc['dead_share_of_trades']:>13.1f}% "
                      f"{100 * cc['dead_share_of_gross']:>15.1f}%")

    print("\n  Q5 -- the best of the 8 cells at the primary cap, per side")
    for nm in ("UP", "DOWN"):
        cs = [c for c in C.values() if c["direction"] == nm and c["cap"] == PRIMARY_CAP]
        if not cs:
            continue
        b = max(cs, key=lambda c: c["gross_bp"])
        print(f"    {nm:>5s}: best is er{b['er_window']}>={b['er_level']} band<={b['band']} "
              f"at {b['gross_bp']:+.2f} on {b['trades']:,} trades "
              f"(primary was {C[f'{nm}|er{pw}>={pl}|band<={pb_}|cap{PRIMARY_CAP}']['gross_bp']:+.2f})")
    print("      A best-of-8 FLOOR is NOT computed here: H1 is only spent if H2 and H3 clear,")
    print("      and section 6 orders the hurdles so nulls are never drawn on a failing cell.")

    print("\nThis is STAGE 0. No 15-minute bar was read, no null was drawn, nothing is admitted (R15).")


if __name__ == "__main__":
    raise SystemExit(main())
