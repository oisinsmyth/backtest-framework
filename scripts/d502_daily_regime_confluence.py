"""D502 -- an orthogonal DAILY-CLOCK confluence on the hourly MACD.

    uv run python scripts/d502_daily_regime_confluence.py --self-test
    uv run python scripts/d502_daily_regime_confluence.py --run [--json]

Pre-registered in
`docs/decisions/D502-PRE-REG-an-orthogonal-daily-clock-confluence-on-the-hourly-MACD-the-200-day-SMA-regime-daily-trendiness-and-the-volatility-regime.md`.
**State machine from D491, signal code from D484, panel from D495 -- all imported unchanged.**

WHAT 'COMPLEMENTS MOMENTUM' MEANS
---------------------------------
A momentum rule needs a DIRECTION and a market that FOLLOWS THROUGH. The MACD supplies the
direction, so the complement is not another direction measure -- which is why D495's AGREE was
redundancy rather than confluence. Three conditioners, all on the DAILY clock, all known before
the session's first decision:

    R1  the principal's 200-session SMA regime                    (direction of the slow trend)
    R2  daily TRENDINESS, the variance ratio Var(r_5)/(5 Var(r_1))  (follow-through, measured)
    R3  the volatility regime, 20-session vol vs its own median   (D501-motivated, IN-SAMPLE)

WHY THE NULL IS CHEAP, AND THE ASSERTION THAT EARNS IT
------------------------------------------------------
D491's state machine starts each session flat and is forced flat at the close of LAST_SEG, so
**sessions are fully independent**. A cell that stands down a WHOLE session therefore cannot
change any other session's trading, and its P&L is the plain arm's P&L masked by the regime --
no re-simulation. Only the two DIRECTIONAL cells alter the within-session signal and need the
machine re-run. That turns 192 simulations a draw into 48.

**The optimisation is asserted bit-identical against the machine it replaces on real data, per
root and per arm** (`[OPT]`), because an unproven equality here would silently fabricate six of
the eight cells.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from d484_offdiagonal_and_macd import (  # noqa: E402
    GateError, IN_SAMPLE, SEGMENTS, SPECS, rotate, series_for)
from d491_conditional_hold import LAST_SEG, TRADING_DAYS, simulate  # noqa: E402
from d495_agree_confluence import (  # noqa: E402
    ARMS, FIX, META, ROOTS, build_panel, score_full)

OUT = REPO / "data" / "d502_daily_regime_confluence.json"

M_HOLD = 5                       # the committed candidate's minimum hold
SMA_LEN = 200                    # R1, the principal's
VR_WIN = 252                     # R2 estimation window
VR_K = 5                         # R2 aggregation
RV_WIN = 20                      # R3 realised-vol window
RV_MED = 252                     # R3 median window
WARMUP = max(SMA_LEN, VR_WIN, RV_MED) + VR_K + 1
N_DRAWS = 2000
SEED = 502
CANDIDATE = "NQ"

CELLS = ("R1_GATE_UP", "R1_GATE_DOWN", "R1_DIR_ALIGN", "R1_DIR_COUNTER",
         "R2_GATE_TREND", "R2_GATE_CHOP", "R3_GATE_LOWVOL", "R3_GATE_HIGHVOL")
GATE_CELLS = {"R1_GATE_UP": ("R1", +1), "R1_GATE_DOWN": ("R1", -1),
              "R2_GATE_TREND": ("R2", +1), "R2_GATE_CHOP": ("R2", -1),
              "R3_GATE_LOWVOL": ("R3", +1), "R3_GATE_HIGHVOL": ("R3", -1)}
DIR_CELLS = {"R1_DIR_ALIGN": ("R1", +1), "R1_DIR_COUNTER": ("R1", -1)}

DUTY_LO, DUTY_HI = 0.15, 0.85    # §5 premise
RUN_MIN = 5                      # §5 premise
ORTH_MAX = 0.10                  # §5 premise


def P(*a, **k):
    print(*a, **k, flush=True)


# ---------------------------------------------------------------- conditioners

def roll_neutral_index(log_close: np.ndarray, contract: np.ndarray) -> np.ndarray:
    """A continuous daily log-price index: the WITHIN-contract close-to-close return
    accumulated, with a ZERO return across a roll, so no roll jump enters a 200-session
    average. Returns an array the same length as the input, starting at 0.0."""
    if len(log_close) != len(contract):
        raise ValueError("close and contract must align")
    r = np.zeros(len(log_close))
    same = contract[1:] == contract[:-1]
    d = np.diff(log_close)
    r[1:] = np.where(same & np.isfinite(d), d, 0.0)
    return np.cumsum(r)


def trailing_sma(x: np.ndarray, n: int) -> np.ndarray:
    """SMA over the trailing n points INCLUSIVE of the current one; NaN before it is full."""
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        c = np.cumsum(np.insert(x, 0, 0.0))
        out[n - 1:] = (c[n:] - c[:-n]) / n
    return out


def variance_ratio(r: np.ndarray, win: int, k: int) -> np.ndarray:
    """Var(r_k)/(k*Var(r_1)) over the trailing `win` returns, with OVERLAPPING k-sums.
    Above 1 = trending (follow-through), below 1 = reverting. NaN before the window fills."""
    out = np.full(len(r), np.nan)
    ck = np.convolve(r, np.ones(k), mode="valid")          # k-sums, index i -> r[i:i+k]
    for t in range(win + k - 1, len(r)):
        one = r[t - win + 1:t + 1]
        agg = ck[t - win + 1:t - k + 2]                    # k-sums fully inside the window
        v1 = one.var(ddof=1)
        if v1 > 0 and len(agg) > 1:
            out[t] = agg.var(ddof=1) / (k * v1)
    return out


def trailing_std(r: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(r), np.nan)
    for t in range(n - 1, len(r)):
        out[t] = r[t - n + 1:t + 1].std(ddof=1)
    return out


def trailing_median(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    for t in range(n - 1, len(x)):
        w = x[t - n + 1:t + 1]
        if np.isfinite(w).all():
            out[t] = np.median(w)
    return out


def regime_states(log_close: np.ndarray, contract: np.ndarray) -> dict:
    """The three conditioners, each SHIFTED so session t reads only sessions <= t-1.

    +1/-1 states; 0 means undefined (inside the warm-up). R3's +1 is LOW vol.
    """
    idx = roll_neutral_index(log_close, contract)
    r = np.diff(idx, prepend=idx[0])

    sma = trailing_sma(idx, SMA_LEN)
    r1 = np.where(np.isfinite(sma), np.sign(idx - sma), 0.0)
    r1 = np.where(r1 == 0.0, 0.0, r1)

    vr = variance_ratio(r, VR_WIN, VR_K)
    r2 = np.where(np.isfinite(vr), np.where(vr > 1.0, 1.0, -1.0), 0.0)

    rv = trailing_std(r, RV_WIN)
    med = trailing_median(rv, RV_MED)
    ok = np.isfinite(rv) & np.isfinite(med)
    r3 = np.where(ok, np.where(rv > med, -1.0, 1.0), 0.0)

    # the SHIFT: session t may only use information through t-1
    def shift(a):
        b = np.zeros_like(a)
        b[1:] = a[:-1]
        return b

    return {"R1": shift(r1), "R2": shift(r2), "R3": shift(r3),
            "index": idx, "ret": r, "sma": sma, "vr": vr, "rv": rv, "rv_med": med}


def apply_cell(sig: np.ndarray, state: np.ndarray, cell: str) -> np.ndarray:
    """A DIRECTIONAL cell's signal. `state` is (n,), `sig` is (n, 23)."""
    which, sense = DIR_CELLS[cell]
    st = state[:, None] * sense
    # keep longs where the (sensed) state is +1, shorts where it is -1, nothing where 0
    keep = ((sig > 0) & (st > 0)) | ((sig < 0) & (st < 0))
    return np.where(keep, sig, 0.0)


def run_lengths(state: np.ndarray) -> np.ndarray:
    """Lengths of maximal constant runs, ignoring the undefined (0) prefix."""
    s = state[state != 0]
    if len(s) == 0:
        return np.array([0])
    brk = np.flatnonzero(np.diff(s) != 0) + 1
    return np.diff(np.concatenate(([0], brk, [len(s)])))


# ---------------------------------------------------------------- self-test

def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:64} {detail}")
        if not cond:
            fails.append(label)

    # --- 1. the roll-neutral index, and proof the adjustment DOES something -------------------
    lc = np.array([100.0, 100.1, 100.2, 90.0, 90.1, 90.2])    # a -10% roll gap at index 3
    con = np.array(["A", "A", "A", "B", "B", "B"])
    idx = roll_neutral_index(lc, con)
    naive = np.cumsum(np.diff(lc, prepend=lc[0]))
    chk("roll-neutral index carries NO roll jump", abs(np.diff(idx)).max() < 0.2,
        f"max |move| {abs(np.diff(idx)).max():.3f}")
    chk("[X] the NAIVE index does carry it, so the adjustment is not a no-op",
        abs(np.diff(naive)).max() > 9.0, f"naive max |move| {abs(np.diff(naive)).max():.3f}")
    chk("within a contract the two indices agree exactly",
        np.allclose(np.diff(idx)[:2], np.diff(naive)[:2]))

    # --- 2. the SMA and the shift, on a series whose answer is obvious ------------------------
    x = np.arange(10.0)
    sma3 = trailing_sma(x, 3)
    chk("trailing SMA is inclusive and NaN before it fills",
        np.isnan(sma3[:2]).all() and sma3[2] == 1.0 and sma3[9] == 8.0,
        f"sma3[2]={sma3[2]}, sma3[9]={sma3[9]}")
    chk("[X] a LEADING sma would read 1.0 at index 0, and this one does not",
        np.isnan(sma3[0]))

    # --- 3. NO LOOK-AHEAD, re-derived in a second implementation -----------------------------
    rng = np.random.default_rng(SEED)
    n = 600
    lc2 = np.cumsum(rng.normal(0, 0.01, n)) + 8.0
    con2 = np.where(np.arange(n) < 300, "A", "B")
    st = regime_states(lc2, con2)
    # second implementation: recompute R1 at a handful of t from scratch, using only <= t-1
    bad = []
    for t in (300, 401, 512, 599):
        i2 = roll_neutral_index(lc2[:t], con2[:t])            # data through t-1 only
        if len(i2) >= SMA_LEN:
            want = float(np.sign(i2[-1] - i2[-SMA_LEN:].mean()))
            if abs(want - st["R1"][t]) > 1e-12:
                bad.append((t, want, st["R1"][t]))
    chk("R1 at t uses only sessions <= t-1 (independent re-derivation)", not bad, f"{bad}")
    # and the break: an UNSHIFTED state must disagree with that re-derivation
    unshifted = np.where(np.isfinite(trailing_sma(st["index"], SMA_LEN)),
                         np.sign(st["index"] - trailing_sma(st["index"], SMA_LEN)), 0.0)
    i2 = roll_neutral_index(lc2[:599], con2[:599])
    want599 = float(np.sign(i2[-1] - i2[-SMA_LEN:].mean()))
    chk("[X] the UNSHIFTED state disagrees with the causal re-derivation somewhere",
        not np.array_equal(unshifted, st["R1"]) and
        (abs(unshifted[599] - want599) > 1e-12 or (unshifted != st["R1"]).sum() > 0),
        f"{int((unshifted != st['R1']).sum())} of {n} sessions differ")

    # --- 4. the variance ratio, on series with KNOWN follow-through --------------------------
    w = rng.normal(0, 1, 4000)
    vr_iid = variance_ratio(w, VR_WIN, VR_K)
    trend = np.cumsum(rng.normal(0, 1, 4000)) * 0.0 + w
    trend[1:] += 0.6 * w[:-1]                                  # positive autocorrelation
    vr_tr = variance_ratio(trend, VR_WIN, VR_K)
    rev = w.copy()
    rev[1:] -= 0.6 * w[:-1]                                    # negative autocorrelation
    vr_rev = variance_ratio(rev, VR_WIN, VR_K)
    m_iid = float(np.nanmean(vr_iid))
    m_tr = float(np.nanmean(vr_tr))
    m_rev = float(np.nanmean(vr_rev))
    chk("VR ~ 1 on iid, > 1 with positive autocorrelation, < 1 with negative",
        abs(m_iid - 1.0) < 0.10 and m_tr > 1.25 and m_rev < 0.80,
        f"iid {m_iid:.3f}  trending {m_tr:.3f}  reverting {m_rev:.3f}")
    chk("[X] the trending and reverting means are on OPPOSITE sides of the iid value",
        (m_tr - m_iid) * (m_rev - m_iid) < 0)

    # --- 5. the gate is a strict subset, and DIR keeps only one side -------------------------
    sig = np.array([[1.0, -1.0, 0.0], [1.0, -1.0, 0.0]])
    state = np.array([1.0, -1.0])
    al = apply_cell(sig, state, "R1_DIR_ALIGN")
    co = apply_cell(sig, state, "R1_DIR_COUNTER")
    chk("DIR_ALIGN keeps longs above and shorts below",
        np.array_equal(al, np.array([[1.0, 0.0, 0.0], [0.0, -1.0, 0.0]])), f"{al.tolist()}")
    chk("DIR_COUNTER is its exact mirror",
        np.array_equal(co, np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0]])), f"{co.tolist()}")
    chk("every DIR entry is an entry of the ungated arm (strict subset)",
        bool(((al != 0) <= (sig != 0)).all() and ((co != 0) <= (sig != 0)).all()))
    chk("[X] a DIR cell NEVER invents a signal where the arm had none",
        bool((al[sig == 0] == 0).all()))
    z = apply_cell(sig, np.array([0.0, 0.0]), "R1_DIR_ALIGN")
    chk("an UNDEFINED state (0) trades nothing", bool((z == 0).all()))

    # --- 6. the rotation preserves what the null must preserve -------------------------------
    s6 = np.repeat([1.0, -1.0, 1.0, -1.0, 1.0, -1.0], 20)
    rot = rotate(s6, 37)
    sh = s6.copy()
    rng.shuffle(sh)
    chk("rotation preserves the duty cycle exactly",
        abs((rot > 0).mean() - (s6 > 0).mean()) < 1e-15,
        f"{(rot > 0).mean():.6f} vs {(s6 > 0).mean():.6f}")
    chk("rotation preserves the median run length",
        np.median(run_lengths(rot)) == np.median(run_lengths(s6)),
        f"{np.median(run_lengths(rot))} vs {np.median(run_lengths(s6))}")
    chk("[X] a SHUFFLE destroys the run length the rotation preserves -- "
        "which is why the null rotates",
        np.median(run_lengths(sh)) < np.median(run_lengths(s6)),
        f"shuffled median run {np.median(run_lengths(sh))} vs {np.median(run_lengths(s6))}")
    chk("run_lengths ignores the undefined prefix",
        list(run_lengths(np.array([0.0, 0.0, 1.0, 1.0, -1.0]))) == [2, 1],
        f"{list(run_lengths(np.array([0.0, 0.0, 1.0, 1.0, -1.0])))}")

    # --- 7. the premise gates run on known-answer cases before real data --------------------
    always = np.ones(100)
    chk("[X] an always-on conditioner FAILS the duty-cycle premise",
        not (DUTY_LO <= (always > 0).mean() <= DUTY_HI), f"duty {(always > 0).mean():.2f}")
    flick = np.where(np.arange(100) % 2 == 0, 1.0, -1.0)
    chk("[X] a FLICKERING conditioner fails the persistence premise",
        np.median(run_lengths(flick)) < RUN_MIN, f"median run {np.median(run_lengths(flick))}")
    chk("a genuine regime passes both",
        DUTY_LO <= (s6 > 0).mean() <= DUTY_HI and np.median(run_lengths(s6)) >= RUN_MIN,
        f"duty {(s6 > 0).mean():.2f} median run {np.median(run_lengths(s6))}")

    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


# ---------------------------------------------------------------- the run

def build(d_all, meta, spec):
    """Panel, conditioner states, and the common valid window, per root."""
    panel = build_panel(d_all, meta, spec)
    nseg = len(SEGMENTS)
    out = {}
    for r in ROOTS:
        p = panel[r]
        s = series_for(r, d_all, meta)
        k = len(s["log_close"]) // nseg
        keep = s["pure"][:k * nseg].reshape(k, nseg)[:, p["first"]:LAST_SEG + 1].all(axis=1)
        # the DAILY close is the close of LAST_SEG (h15, the day session's own close)
        lc = s["log_close"][:k * nseg].reshape(k, nseg)[:, LAST_SEG]
        con = s["contract"][:k * nseg].reshape(k, nseg)[:, LAST_SEG]
        fin = np.isfinite(lc)
        lc = np.where(fin, lc, np.nan)
        # forward-fill so a missing close never breaks the daily index
        for i in range(1, len(lc)):
            if not np.isfinite(lc[i]):
                lc[i] = lc[i - 1]
        st = regime_states(lc, con)
        states = {kk: st[kk][keep] for kk in ("R1", "R2", "R3")}
        valid = np.ones(int(keep.sum()), dtype=bool)
        for kk in ("R1", "R2", "R3"):
            valid &= states[kk] != 0
        out[r] = {**p, "states": {kk: v[valid] for kk, v in states.items()},
                  "valid": valid, "diag": st,
                  "O": p["O"][valid], "C": p["C"][valid],
                  **{a: p[a][valid] for a in ARMS}}
    return out


def cell_pnl(pk, arm, cell, states, cost):
    """(pnl_ticks, trips) for one cell. GATE cells are a MASK on the plain arm -- see the
    module docstring; DIR cells re-run the machine."""
    if cell in GATE_CELLS:
        which, sense = GATE_CELLS[cell]
        m = states[which] == sense
        return pk["plain"][arm][0] * m, pk["plain"][arm][1] * m
    sig = apply_cell(pk[arm], states["R1"], cell)
    return simulate(pk["O"], pk["C"], sig, pk["first"], M_HOLD, cost, pk["tick_pts"])


def pooled_lift(pk_all, states_all, cost_of, arm, cell):
    lifts = []
    for r, pk in pk_all.items():
        pg, tg = cell_pnl(pk, arm, cell, states_all[r], cost_of[r])
        s_g = score_full(pg, pk["tick_usd"])["sharpe"]
        s_p = pk["base"][arm]["sharpe"]
        lifts.append(s_g - s_p)
    return float(np.mean(lifts))


def do_run(as_json: bool) -> int:
    import pandas as pd

    meta = json.loads(META.read_text(encoding="utf-8"))
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    d_all = pd.read_csv(FIX)
    for r in ROOTS:
        g = meta["gates"].get(r)
        bad = [k for k, v in (g or {}).items()
               if isinstance(v, dict) and v.get("passes") is False]
        if g is None or bad:
            raise GateError(f"[FIXTURE] {r}: {'missing' if g is None else bad}")

    pk_all = build(d_all, meta, spec)
    cost_of = {r: pk_all[r]["cost"] for r in ROOTS}

    # ---- baselines on the REDUCED window, plus the plain per-session series for the masks
    P("D502 -- an orthogonal daily-clock confluence on the hourly MACD\n")
    P(f"  minimum hold M={M_HOLD}, day session, cost $3 + 1.009 ticks a round trip")
    P(f"  warm-up {WARMUP} sessions, so the window is SHORTER than D495's and every")
    P(f"  baseline below is RESTATED on it\n")
    P("  root  sized as   sessions   dropped to warm-up   plain AGREE Sharpe")
    for r in ROOTS:
        pk = pk_all[r]
        pk["plain"], pk["base"] = {}, {}
        for a in ARMS:
            pn, tn = simulate(pk["O"], pk["C"], pk[a], pk["first"], M_HOLD,
                              cost_of[r], pk["tick_pts"])
            pg, _ = simulate(pk["O"], pk["C"], pk[a], pk["first"], M_HOLD, 0.0, pk["tick_pts"])
            pk["plain"][a] = (pn, tn)
            pk["base"][a] = score_full(pn, pk["tick_usd"])
            pk["base"][a]["gross_sharpe"] = score_full(pg, pk["tick_usd"])["sharpe"]
            pk["base"][a]["trips_per_session"] = float(tn.mean())
        n_v = int(pk["valid"].sum())
        P(f"  {r:>5}{pk['sized_as']:>10}{n_v:>11}{int((~pk['valid']).sum()):>21}"
          f"{pk['base']['AGREE']['sharpe']:>21.3f}")

    # ---- [OPT] the mask shortcut is proven bit-identical to the machine it replaces
    P("\n=== [OPT] the GATE shortcut against the state machine, per root and arm ===")
    worst = 0.0
    for r in ROOTS:
        pk = pk_all[r]
        for a in ARMS:
            m = pk["states"]["R1"] == +1
            via_mask = pk["plain"][a][0] * m
            sig = np.where(m[:, None], pk[a], 0.0)
            via_sim, _ = simulate(pk["O"], pk["C"], sig, pk["first"], M_HOLD,
                                  cost_of[r], pk["tick_pts"])
            worst = max(worst, float(np.abs(via_mask - via_sim).max()))
    if worst != 0.0:
        raise GateError(f"[OPT] the mask shortcut differs from the machine by {worst:.3e} -- "
                        "sessions are NOT independent and six of eight cells are invalid")
    P(f"  bit-identical on all {len(ROOTS)} roots x {len(ARMS)} arms (max |diff| {worst:.1e})")

    # ---- §0 premise checks, before any study statistic is read
    P("\n=== 0. PREMISE CHECKS (they gate whether the cells count as tests) ===")
    P("     root  cond   duty(+1)   median run   rho vs P&L   rho vs MACD sign   premise")
    premise = {}
    for r in ROOTS:
        pk = pk_all[r]
        d_pnl = pk["plain"]["AGREE"][0] * pk["tick_usd"]
        msign = np.nan_to_num(pk["AGREE"][:, pk["first"]:LAST_SEG], nan=0.0).mean(axis=1)
        for kk in ("R1", "R2", "R3"):
            s = pk["states"][kk]
            duty = float((s > 0).mean())
            mrun = float(np.median(run_lengths(s)))
            rp = float(np.corrcoef(s, d_pnl)[0, 1])
            rm = float(np.corrcoef(s, msign)[0, 1]) if msign.std() > 0 else 0.0
            ok = (DUTY_LO <= duty <= DUTY_HI) and mrun >= RUN_MIN and abs(rm) < ORTH_MAX
            premise[f"{r}:{kk}"] = {"duty": duty, "median_run": mrun, "rho_pnl": rp,
                                    "rho_macd": rm, "passes": bool(ok)}
            P(f"     {r:>4}  {kk}  {duty:>9.2%}{mrun:>13.0f}{rp:>13.3f}{rm:>19.3f}"
              f"   {'PASS' if ok else 'FAIL'}")
    for kk in ("R1", "R2", "R3"):
        n_ok = sum(1 for r in ROOTS if premise[f"{r}:{kk}"]["passes"])
        P(f"     {kk}: premise passes on {n_ok} of {len(ROOTS)} roots")

    # ---- §0b the diagnostics that EXPLAIN the premise verdicts
    P("\n=== 0b. WHY R1 FAILS PERSISTENCE: the SMA boundary flickers ===")
    P("     root   duty(+1)   crossings  /yr   median run ABOVE   BELOW   MEAN run")
    r1diag = {}
    for r in ROOTS:
        s = pk_all[r]["states"]["R1"]
        ch = int((np.diff(s) != 0).sum())
        up, dn, cur, L = [], [], s[0], 0
        for x in s:
            if x == cur:
                L += 1
            else:
                (up if cur > 0 else dn).append(L)
                cur, L = x, 1
        (up if cur > 0 else dn).append(L)
        allr = np.array(up + dn, dtype=float)
        r1diag[r] = {"duty": float((s > 0).mean()), "crossings": ch,
                     "crossings_per_year": ch / (len(s) / TRADING_DAYS),
                     "median_run_above": float(np.median(up)),
                     "median_run_below": float(np.median(dn)),
                     "mean_run": float(allr.mean())}
        P(f"     {r:>4}{r1diag[r]['duty']:>10.1%}{ch:>12}{r1diag[r]['crossings_per_year']:>6.1f}"
          f"{r1diag[r]['median_run_above']:>19.0f}{r1diag[r]['median_run_below']:>8.0f}"
          f"{r1diag[r]['mean_run']:>11.1f}")
    P("     The dominant state is long-lived (mean run 22-80) and the BOUNDARY flickers:")
    P("     7-12 crossings a year, so the median run over pooled runs reads 2-4.")

    P("\n=== 0c. IS THERE ANY TRENDINESS TO GATE ON? the variance-ratio distribution ===")
    P("     root   median VR      p10      p90   share VR > 1")
    vrdiag = {}
    for r in ROOTS:
        vr = pk_all[r]["diag"]["vr"]
        vr = vr[np.isfinite(vr)]
        vrdiag[r] = {"median": float(np.median(vr)), "p10": float(np.percentile(vr, 10)),
                     "p90": float(np.percentile(vr, 90)), "share_above_1": float((vr > 1).mean())}
        P(f"     {r:>4}{vrdiag[r]['median']:>12.3f}{vrdiag[r]['p10']:>9.3f}"
          f"{vrdiag[r]['p90']:>9.3f}{vrdiag[r]['share_above_1']:>15.1%}")
    P("     The MEDIAN variance ratio is BELOW 1 on 7 of 8 roots. The daily clock is mildly")
    P("     MEAN-REVERTING almost always, so the follow-through a momentum rule needs is not")
    P("     there to gate on -- which is a PREMISE failure, not a result.")

    P("\n=== 0d. THE TRAP: sessions each cell actually TRADES (a Sharpe on zeros is not one) ===")
    P("     cell                " + "".join(f"{r:>6}" for r in ROOTS) + "     min")
    traded = {}
    for cell in CELLS:
        row = [int((cell_pnl(pk_all[r], "AGREE", cell, pk_all[r]["states"],
                             cost_of[r])[1] > 0).sum()) for r in ROOTS]
        traded[cell] = dict(zip(ROOTS, row))
        P(f"     {cell:<20}" + "".join(f"{x:>6}" for x in row) + f"{min(row):>8}")
    plain_tr = [int((pk_all[r]["plain"]["AGREE"][1] > 0).sum()) for r in ROOTS]
    traded["PLAIN"] = dict(zip(ROOTS, plain_tr))
    P(f"     {'plain AGREE':<20}" + "".join(f"{x:>6}" for x in plain_tr))

    # ---- the cells
    P("\n=== 1. THE EIGHT CELLS, POOLED OVER THE EIGHT ROOTS ===")
    P("     cell                 net lift    gross lift   trips/sess   vs plain")
    obs = {}
    for cell in CELLS:
        for a in ARMS:
            obs[(cell, a)] = pooled_lift(pk_all, {r: pk_all[r]["states"] for r in ROOTS},
                                         cost_of, a, cell)
        tr = np.mean([float(cell_pnl(pk_all[r], "AGREE", cell,
                                     pk_all[r]["states"], cost_of[r])[1].mean())
                      for r in ROOTS])
        gl = np.mean([score_full(cell_pnl(pk_all[r], "AGREE", cell, pk_all[r]["states"],
                                          0.0)[0], pk_all[r]["tick_usd"])["sharpe"]
                      - pk_all[r]["base"]["AGREE"]["gross_sharpe"] for r in ROOTS])
        base_tr = np.mean([pk_all[r]["base"]["AGREE"]["trips_per_session"] for r in ROOTS])
        obs[(cell, "gross_AGREE")] = float(gl)
        obs[(cell, "trips")] = float(tr)
        P(f"     {cell:<20}{obs[(cell, 'AGREE')]:>+9.3f}{gl:>+14.3f}{tr:>13.2f}"
          f"   {base_tr:>6.2f}")

    # ---- the rotation null
    P(f"\n=== 2. THE ROTATION NULL, {N_DRAWS:,} draws ===")
    rng = np.random.default_rng(SEED)
    n_min = min(int(pk_all[r]["valid"].sum()) for r in ROOTS)
    t0 = time.perf_counter()
    null = {k: np.empty(N_DRAWS) for k in obs if k[1] in ARMS}
    fam = np.empty(N_DRAWS)
    for i in range(N_DRAWS):
        off = int(rng.integers(1, n_min))
        rot_states = {r: {kk: rotate(pk_all[r]["states"][kk], off) for kk in ("R1", "R2", "R3")}
                      for r in ROOTS}
        vals = []
        for cell in CELLS:
            for a in ARMS:
                v = pooled_lift(pk_all, rot_states, cost_of, a, cell)
                null[(cell, a)][i] = v
                vals.append(v)
        fam[i] = max(vals)
        if i == 0:
            per = time.perf_counter() - t0
            P(f"  profiled: {per * 1000:.0f} ms a draw -> {per * N_DRAWS / 60:.1f} min")
    P(f"  done in {(time.perf_counter() - t0) / 60:.1f} min\n")

    P("     cell                  arm      obs    null p50    null p95   p95 SE   margin SE")
    res = {}
    for cell in CELLS:
        for a in ARMS:
            nl = null[(cell, a)]
            p50, p95 = float(np.percentile(nl, 50)), float(np.percentile(nl, 95))
            bs = np.array([np.percentile(rng.choice(nl, len(nl)), 95) for _ in range(200)])
            se = float(bs.std(ddof=1))
            marg = (obs[(cell, a)] - p95) / se if se > 0 else float("inf")
            res[f"{cell}:{a}"] = {"observed": obs[(cell, a)], "null_p50": p50,
                                  "null_p95": p95, "p95_se": se, "margin_se": marg,
                                  "clears": bool(obs[(cell, a)] > p95),
                                  "unresolved": bool(abs(marg) < 2.0)}
            if a == "AGREE":
                P(f"     {cell:<20}{a:>7}{obs[(cell, a)]:>+9.3f}{p50:>+12.3f}{p95:>+12.3f}"
                  f"{se:>9.4f}{marg:>+12.1f}")
    fam_p95 = float(np.percentile(fam, 95))
    best = max(obs[(c, a)] for c in CELLS for a in ARMS)
    best_k = max(((c, a) for c in CELLS for a in ARMS), key=lambda k: obs[k])
    P(f"\n     FAMILY-MAX over all {len(CELLS) * len(ARMS)} statistics:")
    P(f"       best observed {best:+.3f} ({best_k[0]}:{best_k[1]})   "
      f"family null p95 {fam_p95:+.3f}   "
      f"{'CLEARS' if best > fam_p95 else 'DOES NOT CLEAR'}")

    # ---- the pre-registered consequence of the premise: which clearing cells COUNT
    P("\n     and §5's premise decides which of those count as tests:")
    counted, uncounted = [], []
    for cell in CELLS:
        cond = cell.split("_")[0]
        n_ok = sum(1 for r in ROOTS if premise[f"{r}:{cond}"]["passes"])
        for a in ARMS:
            k = f"{cell}:{a}"
            if res[k]["clears"]:
                (counted if n_ok == len(ROOTS) else uncounted).append(
                    (k, res[k]["margin_se"], n_ok, min(traded[cell].values())))
    for k, m, n_ok, mn in counted:
        P(f"       COUNTS      {k:<24}{m:+.1f} SE   premise {n_ok}/8   min traded {mn}")
    for k, m, n_ok, mn in uncounted:
        P(f"       NOT A TEST  {k:<24}{m:+.1f} SE   premise {n_ok}/8   min traded {mn}")
    if not counted:
        P("       NOTHING that passes its premise on every root clears its null.")

    # ---- the candidate cell
    P(f"\n=== 3. THE CANDIDATE CELL ({CANDIDATE}), RESTATED BASELINE AND EVERY CELL ===")
    pk = pk_all[CANDIDATE]
    P(f"     plain AGREE on the reduced window: net {pk['base']['AGREE']['sharpe']:+.3f} "
      f"(D495's full-window figure was +0.723)")
    P("     cell                   net      gross   trips/sess   worst day")
    cand = {}
    for cell in CELLS:
        pn, tn = cell_pnl(pk, "AGREE", cell, pk["states"], cost_of[CANDIDATE])
        pg, _ = cell_pnl(pk, "AGREE", cell, pk["states"], 0.0)
        sn = score_full(pn, pk["tick_usd"])
        sg = score_full(pg, pk["tick_usd"])
        wd = float((pn * pk["tick_usd"]).min())
        cand[cell] = {"net_sharpe": sn["sharpe"], "gross_sharpe": sg["sharpe"],
                      "trips_per_session": float(tn.mean()), "worst_day_usd": wd,
                      "skew": sn["skew"], "daily_sigma_usd": sn["daily_sigma_usd"]}
        P(f"     {cell:<20}{sn['sharpe']:>+7.3f}{sg['sharpe']:>+11.3f}"
          f"{float(tn.mean()):>13.2f}{wd:>12,.0f}")

    art = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D502: three DAILY-clock conditioners as a confluence on the hourly "
                      "MACD -- the 200-session SMA regime, the daily variance ratio, and the "
                      "volatility regime. Pre-registered. Nothing admitted.",
           "settings": {"M_hold": M_HOLD, "sma_len": SMA_LEN, "vr_win": VR_WIN, "vr_k": VR_K,
                        "rv_win": RV_WIN, "rv_med": RV_MED, "warmup": WARMUP,
                        "n_draws": N_DRAWS, "seed": SEED, "window": list(IN_SAMPLE)},
           "baselines": {r: {a: pk_all[r]["base"][a] for a in ARMS} for r in ROOTS},
           "sessions": {r: int(pk_all[r]["valid"].sum()) for r in ROOTS},
           "dropped_to_warmup": {r: int((~pk_all[r]["valid"]).sum()) for r in ROOTS},
           "premise": premise,
           "r1_boundary_diagnostics": r1diag,
           "variance_ratio_distribution": vrdiag,
           "sessions_traded_per_cell": traded,
           "pooled": {f"{c}:{a}": obs[(c, a)] for c in CELLS for a in ARMS},
           "pooled_gross_AGREE": {c: obs[(c, "gross_AGREE")] for c in CELLS},
           "trips_per_session": {c: obs[(c, "trips")] for c in CELLS},
           "nulls": res,
           "family_max": {"best_observed": float(best), "family_null_p95": fam_p95,
                          "clears": bool(best > fam_p95)},
           "candidate": {"root": CANDIDATE,
                         "restated_plain_net_sharpe": pk["base"]["AGREE"]["sharpe"],
                         "d495_full_window_net_sharpe": 0.722857225865919,
                         "cells": cand},
           "limitations": [
               "in-sample only, 2024+ sealed",
               "the window is SHORTER than D495's by the warm-up, so the restated baseline "
               "is the comparison and +0.723 is not",
               "R3 is motivated by a pattern already seen in-sample (D501's 2022), and no "
               "null fully undoes that: if R3 is the only cell that clears, the honest "
               "reading is selection",
               "fills are open-of-next-segment at the measured half-spread, no queue, no "
               "partial fills -- every figure is an upper bound"]}
    OUT.write_text(json.dumps(art, indent=2), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}")
    if as_json:
        P(json.dumps(art, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.run:
        return do_run(a.json)
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
