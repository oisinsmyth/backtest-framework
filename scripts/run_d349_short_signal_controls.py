"""D349 -- is the short signal real? D347's three drift-matched controls on the SHORT side, with the borrow.

    uv run python scripts/run_d349_short_signal_controls.py --selftest
    uv run python scripts/run_d349_short_signal_controls.py --controls on_share --draws 100 --part 0   (one per signal, in parallel)
    uv run python scripts/run_d349_short_signal_controls.py --report

Five short signals as events on the floored, deal-filtered, lagged scores: on_share,
skew_63, close_in_range and the rsi decile entering their TOP decile (the leg the slot
book shorts); the rsi turn (cross back down through 70) as the second reference. Next-
open fill; every event taken (D345's kernel, n_max=None, fed (zeros, hi)); two exits --
a 40-bar cap (the statistic every control uses) and invalidation (pct or rsi crossing
50). The mirror is the LONG of the same event.

Hedge: the floored universe's own equal-weight return, beta-adjusted beside it. Cost:
the PUB / PB round trip, commission, AND the borrow at D337's rates (GC 50 bp/yr, HTB
500 when the name is in an F0 window at e0-1 or its as-traded close is below $5),
charged per bar held by d337_borrow.borrow_per_trade_bp. Net with and without borrow.

Controls: A per-name time rotation of the event series; B same-date same-rsi-bucket
random name -- D347's helper, but its pool (and the bucket base rates) confined to
name-bars WITH a defined rsi percentile, because bucket_of(NaN) digitizes to the top
bucket and the short events live there; C tail-randomised direction. Timing value =
observed - A's p50. Splits:
down-years, era halves, the mirror. Interaction: rsi-percentile buckets with each
bucket's SHORT forward-40 base rate (-F) removed; Q5 reads the top bucket (98, 100].

Everything shared with D347 is imported from run_d347_long_signal_controls.py, not
copied; the prep is the cached one in d348_prep.py (D347's prep() dict, same keys).

ASSERTIONS [K][F0][R][ID][E][H][S][SB][A][B][C][F][X][6] -- pre-reg section 7.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_PREP_FILE = REPO / "scripts" / "d348_prep.py"
if not _PREP_FILE.exists():
    raise SystemExit("scripts/d348_prep.py is not present -- the shared cached prep is written by D348")
PREP = _load("d348p", "d348_prep.py")     # executes D347's alias chain ONCE; D347 and every alias are taken from here
V47 = PREP.V47                            # run_d347_long_signal_controls: main guarded; every alias and helper
V45 = V47.V45
W, D, Y, R, M, X, PA = V47.W, V47.D, V47.Y, V47.R, V47.M, V47.X, V47.PA
G22, UF, FL, BR, V9, V38, V31, CEN, SP, EB = (V47.G22, V47.UF, V47.FL, V47.BR, V47.V9, V47.V38, V47.V31,
                                               V47.CEN, V47.SP, V47.EB)
# D347's helpers, reused not copied
percentile_grid, floored_market, roll_beta = V47.percentile_grid, V47.floored_market, V47.roll_beta
forward_excess_grid, bucket_of, pnl_beta_adjusted, two_c = (V47.forward_excess_grid, V47.bucket_of,
                                                            V47.pnl_beta_adjusted, V47.two_c)
rotate_confined, run_events, pnl_bp, control_b_signal = (V47.rotate_confined, V47.run_events, V47.pnl_bp,
                                                         V47.control_b_signal)
BUCKET_EDGES, CAP, X_TARGET, ANN = V47.BUCKET_EDGES, V47.CAP, V47.X_TARGET, V47.ANN
ledger_set = V45.ledger_set

SIGNALS = ("on_share", "skew_63", "close_in_range", "rsi_decile", "rsi_turn")     # order fixes the RNG keys
CANDIDATES = ("on_share", "skew_63", "close_in_range")                              # Q1's three
SCORE_OF = {"on_share": "on_share", "skew_63": "skew_63", "close_in_range": "close_in_range",
            "rsi_decile": "rsi", "rsi_turn": "rsi"}
SCORES = ("on_share", "skew_63", "close_in_range", "rsi")
TOP = 100.0 - V47.DECILE            # 90: the top decile the slot book shorts
MID = V47.MID                       # 50: invalidation
RSI_HI = V47.RSI_HI                 # 70: the turn
TOP_BUCKET = 9                      # (98, 100] of the rsi percentile at t-1
SEED = W.SEED
STUDY = 349
OUT = REPO / "data" / "d349_short_signal_controls.json"
CTRL = REPO / "data" / "d349_ctrl_{sig}.json"
CONVS = ("PB", "PUB")
BORROW_SCHEME = "gc_htb"
PER_SHARE = 0.005                   # commission per share, as V47.two_c
PREP_KEYS = ("A", "A3", "r1T", "finT", "ocT", "m_f", "m_f_oc", "keep", "elig", "base", "z", "n", "T", "HALF",
             "CLOSE", "RAW_CLOSE", "years", "down_years", "yr_ret", "beta", "bucket_rsi", "excl", "t0", "m_start",
             "mkt", "mkt_oc")                     # mkt / mkt_oc: the panel-wide market, D345's kernel input, for [ID]


# ------------------------------------------------------------------ preparation
def prep(need_grids=True):
    kw = {"need_grids": need_grids} if "need_grids" in inspect.signature(PREP.prep).parameters else {}
    P = PREP.prep(**kw)
    missing = [k for k in PREP_KEYS if k not in P]
    assert not missing, f"d348_prep.prep() is missing keys {missing}"
    if need_grids and P.get("F") is None:
        P["F"] = forward_excess_grid(P["r1T"], P["ocT"], P["m_f"], P["m_f_oc"], P["finT"])
    add_short_events(P)
    return P


def add_short_events(P):
    """The four lagged floored scores, their percentiles, and the five short-event grids."""
    t0 = time.time()
    z, excl, keep, base, T, n, elig = P["z"], P["excl"], P["keep"], P["base"], P["T"], P["n"], P["elig"]

    def lagged(sig):                                                # D347's closure, verbatim
        sc = UF.apply_floor_replace(np.where(excl, np.nan, np.asarray(z[sig])), keep)
        sc = np.where(base, sc, np.nan)
        out = np.full((T, n), np.nan)
        out[1:] = sc[:, :-1].T
        return out

    LAG = {s: lagged(s) for s in SCORES}
    if isinstance(P.get("LAG"), dict) and "rsi" in P["LAG"]:
        assert np.array_equal(LAG["rsi"], np.asarray(P["LAG"]["rsi"]), equal_nan=True), "lagged rsi differs from the shared prep"
    PCT = {}
    for s in SCORES:
        if s == "rsi" and isinstance(P.get("PCT"), dict) and "rsi" in P["PCT"]:
            PCT[s] = np.asarray(P["PCT"]["rsi"])                     # the shared prep's, built by the same function
        else:
            PCT[s] = percentile_grid(LAG[s])
    assert np.array_equal(bucket_of(PCT["rsi"]), np.asarray(P["bucket_rsi"])), "bucket_rsi differs from bucket_of(PCT[rsi])"
    assert not elig[:P["m_start"]].any(), "elig not confined to the hedge-defined bars"

    def events_for(sig):
        """(sig_short, score_for_exit): a fresh entry into the top decile, or the rsi cross back down through 70."""
        if sig == "rsi_turn":
            r = LAG["rsi"]
            prev = np.full_like(r, np.nan)
            prev[1:] = r[:-1]
            with np.errstate(invalid="ignore"):
                hi = (r < RSI_HI) & (prev >= RSI_HI) & elig
            return hi, r
        p = PCT[SCORE_OF[sig]]
        prev = np.full_like(p, np.nan)
        prev[1:] = p[:-1]
        with np.errstate(invalid="ignore"):
            hi = (p >= TOP) & (prev < TOP) & elig
        return hi, p

    P["LAG49"], P["PCT49"] = LAG, PCT
    P["EVENTS49"] = {s: events_for(s) for s in SIGNALS}
    P["rsi_pct_ok"] = np.isfinite(PCT["rsi"])
    # bucket_of(NaN) digitizes to bucket 9: an eligible name-bar with NO rsi percentile (off the warm base) would otherwise sit
    # in the top bucket -- in control B's replacement pool and in E_b[9]. Both are confined to name-bars with a defined percentile.
    P["elig_b"] = elig & P["rsi_pct_ok"]
    n_nan = int((elig & ~P["rsi_pct_ok"]).sum())
    n_nan_base = int((elig & base.T & ~P["rsi_pct_ok"]).sum())
    for s in SIGNALS:
        print(f"  short events {s:14s}: {int(P['EVENTS49'][s][0].sum()):,}")
    print(f"  lagged scores, percentiles and short events built ({time.time() - t0:.0f}s); eligible name-bars with an undefined "
          f"rsi percentile: {n_nan:,} of {int(elig.sum()):,} ({n_nan_base:,} of them on the warm base) -- excluded from control B's "
          f"pool and from the bucket base rates")


def control_b_defined(P, hi, rng):
    """D347's control B (same date, same rsi bucket, a random other eligible name) drawn from names WITH a defined rsi percentile."""
    return control_b_signal(dict(P, elig=P["elig_b"]), hi, rng)


def zeros_like(hi):
    return np.zeros_like(hi)


def run_short(P, hi, sc, exit_):
    """The kernel fed (zeros, hi): every short event taken."""
    return run_events(P, zeros_like(hi), hi, sc, exit_)


def run_mirror(P, hi, sc, exit_):
    """The LONG of the same event."""
    return run_events(P, hi, zeros_like(hi), sc, exit_)


# ------------------------------------------------------------------ borrow
def borrow_of(P, trades):
    """(per-trade borrow bp, htb flags, annual rate bp) at D337's gc_htb scheme on the as-traded close."""
    htb = BR.htb_flags(trades, P["excl"], P["RAW_CLOSE"])
    rate = BR.rate_bps(trades, htb, BORROW_SCHEME)
    return BR.borrow_per_trade_bp(trades, rate), htb, rate


def check_borrow(P, trades, per_trade, htb, rng, k=200):
    """[SB]: an independent recomputation -- the rule (F0 window at e0-1, or as-traded close < $5) x bars held / 252."""
    excl, RAW_CLOSE = P["excl"], P["RAW_CLOSE"]
    idx = rng.choice(len(trades), size=min(k, len(trades)), replace=False)
    worst = 0.0
    for i in idx:
        row, e0, age, _p, side = trades[i]
        assert side == 1, "[SB] a long in the short ledger"
        px = float(RAW_CLOSE[e0, row])
        is_htb = bool(excl[row, max(e0 - 1, 0)]) or bool(px < BR.PX_HTB)
        assert is_htb == bool(htb[i]), f"[SB] htb flag disagrees with the rule on trade {i}"
        direct = (BR.HTB_BPS if is_htb else BR.GC_BPS) * float(age) / BR.ANN
        worst = max(worst, abs(direct - float(per_trade[i])))
        assert worst < 1e-9, f"[SB] borrow {per_trade[i]} != direct {direct} on trade {i}"
    return idx, worst


def event_accounting(P, hi, res, cap=CAP):
    """The pre-reg's check: cap-exit trades == events - events on names already held - events on unpriced bars - open at end.
    A counting replay that reads no returns (EB.concurrency_fixed_hold's logic) supplies the skips independently."""
    finT = P["finT"]
    T, n = finT.shape
    held_until = np.full(n, -1)
    n_skip = n_ent = 0
    alive_now = np.zeros(n, bool)
    for t in range(1, T):
        alive = (held_until >= t) & finT[t]
        held_until[~finT[t]] = -1
        ev = hi[t] & finT[t]
        n_skip += int((ev & alive).sum())
        new = ev & ~alive
        held_until[new] = t + cap - 1
        n_ent += int(new.sum())
        alive_now = alive | new
    n_unpriced = int((hi[1:] & ~finT[1:]).sum()) + int(hi[0].sum())     # bar 0 is never visited by the kernel
    n_open_end = int(alive_now.sum())
    out = dict(events=int(hi.sum()), already_held=n_skip, unpriced=n_unpriced, open_at_end=n_open_end, trades=len(res["trades"]),
               entries=n_ent)
    assert n_ent == int(res["ent"].sum()), f"check: replay entries {n_ent} != kernel {int(res['ent'].sum())}"
    assert out["events"] == n_ent + n_skip + n_unpriced, "check: events != entries + already held + unpriced"
    assert out["trades"] == n_ent - n_open_end, f"check: trades {out['trades']} != entries {n_ent} - open at end {n_open_end}"
    return out


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    print("\nASSERTIONS")
    A3, r1T, finT, ocT, n, T = P["A3"], P["r1T"], P["finT"], P["ocT"], P["n"], P["T"]
    LAG, PCT, EVENTS = P["LAG49"], P["PCT49"], P["EVENTS49"]
    # [ID] D345's kernel identity, on the SHORT side: fed rank < 2 on the short leg with the slot exit, the kernel reproduces
    # the slot book's invariant SHORT ledger; the reference is W.simulate(slots=False) on the PANEL-WIDE market (D345's
    # kernel input: A["mkt"] and FL.with_open_fill's mkt_oc, both from the shared prep), not the floored hedge
    sc_nT = UF.apply_floor_replace(np.where(P["excl"], np.nan, P["z"]["rsi"]), P["keep"])
    rankT = Y.rank_single({"rsi": sc_nT}, P["base"], "rsi", n, T)
    W.BASE_HOLD = 20
    A2 = dict(A3, mkt=np.asarray(P["mkt"]), mkt_oc=np.asarray(P["mkt_oc"]))
    res_ref = W.simulate(A2, Y.gate_from(rankT, finT), 2, True, slots=False, fill="open")
    sig_gs = np.ascontiguousarray(rankT[1] < 2)
    res_id = EB.simulate_event(A2, np.zeros_like(sig_gs), sig_gs, LAG["rsi"], exit="target", cap=20, n_max=None,
                               x_target=X_TARGET, U=4)
    ref_short = [t for t in res_ref["trades"] if t[4] == 1]
    assert all(t[4] == 1 for t in res_id["trades"]), "[ID] a long in the short-only run"
    assert ledger_set(res_id["trades"]) == ledger_set(ref_short), "[ID] short ledgers differ"
    assert np.array_equal(res_id["cnt1"], res_ref["cnt1"]) and not res_id["cnt0"].any(), "[ID] cnt1"
    assert len(ref_short) < len(res_ref["trades"]), "[ID] the reference has no long leg to leave out"
    print(f"    [ID] KERNEL: fed rank < 2 on the SHORT leg with the slot exit, the event kernel reproduces the slot book's invariant "
          f"short ledger bit-identically ({len(res_id['trades']):,} short trades of the reference's {len(res_ref['trades']):,}; cnt1 equal)")
    # [E] events on the raw lagged percentile (or rsi) at t-1, fresh, and different unlagged; second implementation by direct count
    rng = np.random.default_rng(STUDY)
    for s in SIGNALS:
        hi, sc = EVENTS[s]
        ev_idx = np.argwhere(hi)
        sample = ev_idx[rng.choice(len(ev_idx), size=min(300, len(ev_idx)), replace=False)]
        n_unl = 0
        for t, i in sample:
            assert P["elig"][t, i], f"[E] {s} ({t},{i}) not eligible"
            if s == "rsi_turn":
                r = LAG["rsi"]
                assert r[t, i] < RSI_HI and r[t - 1, i] >= RSI_HI, f"[E] {s} ({t},{i})"
                sc_t = r[t + 1, i] if t + 1 < T else np.nan          # the score AT t, known only at the close of t
                n_unl += not (sc_t == sc_t and sc_t < RSI_HI and r[t, i] >= RSI_HI)
            else:
                v = LAG[SCORE_OF[s]][t]
                fin = np.isfinite(v)
                pct_direct = (float((v[fin] < v[i]).sum()) + 0.5 * float((v[fin] == v[i]).sum())) / fin.sum() * 100.0
                assert pct_direct >= TOP - 1e-9, f"[E] {s} ({t},{i}) pct {pct_direct}"
                v2 = LAG[SCORE_OF[s]][t - 1]
                fin2 = np.isfinite(v2)
                pct_prev = ((float((v2[fin2] < v2[i]).sum()) + 0.5 * float((v2[fin2] == v2[i]).sum())) / fin2.sum() * 100.0
                            if fin2[i] else np.nan)
                assert not (pct_prev == pct_prev and pct_prev >= TOP), f"[E] {s} ({t},{i}) not fresh"
                p_t = PCT[SCORE_OF[s]][t + 1, i] if t + 1 < T else np.nan
                n_unl += not (p_t == p_t and p_t >= TOP and PCT[SCORE_OF[s]][t, i] < TOP)
        print(f"    [E] {s:14s}: {len(ev_idx):,} short events; {len(sample)} sampled all satisfy the entry condition on the raw lagged "
              f"score at t-1 (direct count), are fresh and eligible; the unlagged condition differs on {n_unl} of {len(sample)}")
    # [H] floored market and beta (D347's construction, re-checked here)
    m_f, m_f_oc = P["m_f"], P["m_f_oc"]
    for t in rng.choice(np.flatnonzero(np.isfinite(m_f)), size=200, replace=False):
        idx = np.flatnonzero(P["keep"][t] & finT[t] & np.isfinite(r1T[t]))
        assert abs(float(np.mean([r1T[t, i] for i in idx])) - m_f[t]) < 1e-12, f"[H] bar {t}"
    syn = 2.0 * np.nan_to_num(m_f, nan=0.0) + rng.normal(0, 0.002, size=T)
    b_syn = roll_beta(syn[:, None], m_f)[:, 0]
    fin_b = np.isfinite(b_syn)
    assert abs(float(np.nanmedian(b_syn[fin_b])) - 2.0) < 0.05, f"[H] synthetic beta {np.nanmedian(b_syn[fin_b])}"
    print(f"    [H] the floored market equals a direct mean over keep & priced names on 200 sampled bars to 1e-12; a synthetic name with "
          f"returns 2m + noise recovers beta {np.nanmedian(b_syn[fin_b]):.3f}")
    # [S] sign in money on on_share SHORT events, cap exit: pnl == -(long excess); a name that rises against the market pays negatively
    hi, sc = EVENTS["on_share"]
    res = run_short(P, hi, sc, "cap")
    tr = res["trades"]
    assert all(t[4] == 1 for t in tr), "[S] a long in the short ledger"
    pnl = np.array([t[3] for t in tr])
    rec = FL.pnl_recomputed_fill(tr, r1T, m_f, ocT, m_f_oc)
    worst = float(np.abs(rec - pnl).max())
    assert worst < 1e-12, f"[S] {worst:.2e}"
    ex = np.array([float((ocT[e0, row] - m_f_oc[e0]) + np.nansum(r1T[e0 + 1:e0 + age, row] - m_f[e0 + 1:e0 + age]))
                   for row, e0, age, _p, _s in tr])
    assert (pnl[ex > 0] < 0).all() and (pnl[ex < 0] > 0).all(), "[S] short sign"
    assert float(np.abs(pnl + ex).max()) < 1e-9, "[S] pnl != -(excess)"
    acc = event_accounting(P, hi, res)
    print(f"    [S] SIGN IN MONEY: every on_share cap-exit SHORT trade equals the open-fill recomputation against the floored market "
          f"with the short sign to {worst:.1e}; a name that rises against the market pays negatively, one that falls pays positively "
          f"({len(tr):,} trades; {int((ex > 0).sum()):,} rose, {int((ex < 0).sum()):,} fell)")
    print(f"    check: {acc['events']:,} events = {acc['entries']:,} entries + {acc['already_held']:,} on names already held + "
          f"{acc['unpriced']:,} unpriced; trades {acc['trades']:,} = entries - {acc['open_at_end']} open at the end")
    # [SB] the borrow
    pt, htb, rate = borrow_of(P, tr)
    idx_sb, worst_b = check_borrow(P, tr, pt, htb, rng)
    assert (rate[htb] == BR.HTB_BPS).all() and (rate[~htb] == BR.GC_BPS).all(), "[SB] rates"
    print(f"    [SB] BORROW: on {len(idx_sb)} sampled short trades the per-trade borrow equals the rule x bars held / 252 to {worst_b:.1e}, "
          f"and every HTB flag agrees with the F0-window / ${BR.PX_HTB:.0f} rule; HTB on {int(htb.sum())} of {len(tr):,} trades "
          f"(F0 windows are NaN'd out of the lagged score and the floor removes sub-$5 names, so HTB is structurally rare here); "
          f"mean borrow {pt.mean():.2f} bp per trade")
    # [A] control A keeps every name's event count up to the hedge-defined confinement, and produces no NaN P&L
    sl_, ss_, sc_ = rotate_confined(P, zeros_like(hi), hi, sc, rng)
    assert not sl_.any(), "[A] a long appeared in the rotation"
    lost = int(hi.sum() - ss_.sum())
    assert (ss_.sum(axis=0) <= hi.sum(axis=0)).all() and lost < 0.02 * hi.sum(), f"[A] lost {lost}"
    rA = run_short(P, ss_, sc_, "cap")
    assert np.isfinite(pnl_bp(rA)).all() and all(t[4] == 1 for t in rA["trades"]), "[A] a rotated trade carries NaN"
    print(f"    [A] control A keeps every name's event count except {lost} of {int(hi.sum()):,} rotated onto bars before the hedge is "
          f"defined ({100 * lost / hi.sum():.2f}%); no rotated trade carries a NaN")
    # [B] control B keeps every event's date and rsi bucket and changes its name
    sigB = control_b_defined(P, hi, rng)
    assert np.array_equal(sigB.sum(axis=1), hi.sum(axis=1)), "[B] dates changed"
    bo, bn = P["bucket_rsi"][hi], P["bucket_rsi"][sigB]
    assert sorted(bo.tolist()) == sorted(bn.tolist()), "[B] bucket multiset changed"
    assert not (sigB & hi).sum() > 0.05 * hi.sum(), "[B] too many names unchanged"
    assert P["rsi_pct_ok"][sigB].all() and P["rsi_pct_ok"][hi].all(), "[B] a replacement (or an event) has no rsi percentile"
    assert P["elig"][sigB].all(), "[B] a replacement is not eligible"
    print(f"    [B] control B keeps every event's date and rsi bucket; every replacement is eligible with a defined rsi percentile; "
          f"{int((sigB & hi).sum())} of {int(hi.sum()):,} events kept their name by chance")
    # [C] control C is centred at zero
    signs = rng.choice([-1.0, 1.0], size=(1000, pnl.size))
    cm = (signs * pnl[None, :] * 1e4).mean(axis=1)
    se = cm.std(ddof=1) / np.sqrt(cm.size)
    assert abs(cm.mean()) < 2 * se + 1e-9, "[C]"
    print(f"    [C] control C: mean {cm.mean():+.3f} bp, within 2 standard errors ({se:.3f}) of zero")
    # [F] the SHORT base-rate grid -F on sampled cells
    Fs = -P["F"]
    cells = np.argwhere(np.isfinite(Fs) & P["elig"])
    sample = cells[rng.choice(len(cells), size=3000, replace=False)]
    worst_f = 0.0
    for t, i in sample:
        v = r1T[t:t + CAP, i].copy()
        mm = m_f[t:t + CAP].copy()
        v[0], mm[0] = ocT[t, i], m_f_oc[t]
        okk = finT[t:t + CAP, i] & np.isfinite(v) & np.isfinite(mm)
        okk[0] = True
        direct = -float(np.sum(np.where(okk, v - mm, 0.0)))
        worst_f = max(worst_f, abs(direct - Fs[t, i]))
    assert worst_f < 1e-9, f"[F] {worst_f:.2e}"
    print(f"    [F] the short forward-40 base-rate grid -F equals a direct per-cell recomputation on 3,000 sampled cells to {worst_f:.1e}")
    # [X] the interaction identity on the short ledger: sum over buckets of n_b (E_sb - E_s) == 0; the buckets partition the events
    b_ev = event_buckets(P, tr)
    Es = pnl.mean()
    groups = [b for b in range(-1, 10) if (b_ev == b).any()]
    assert sum(int((b_ev == b).sum()) for b in groups) == pnl.size, "[X] partition"
    tot = sum((b_ev == b).sum() * (pnl[b_ev == b].mean() - Es) for b in groups)
    assert abs(tot) < 1e-9 * max(1.0, abs(pnl).sum()), f"[X] {tot}"
    print(f"    [X] the bucket decomposition sums to the event count and sum_b n_b (E_sb - E_s) == 0 "
          f"({int((b_ev < 0).sum())} events with an undefined rsi percentile)")
    # [6] the audits raise on deliberately broken ledgers
    broke = False
    try:
        rec2 = FL.pnl_recomputed_fill(tr, r1T, m_f, ocT, m_f_oc)
        assert np.abs(rec2 - (pnl + 50e-4)).max() < 1e-12
    except AssertionError:
        broke = True
    assert broke, "[6] [S] did not raise"
    # [SB] must raise on a borrow charged at GC where the rule says HTB: take a GC trade, put its name in an F0 window at e0-1
    # (so the rule says HTB) and hand the audit the GC borrow with an HTB flag (and again with the stale GC flag)
    j = int(np.flatnonzero(~htb)[0])
    row, e0 = tr[j][0], tr[j][1]
    excl6 = np.array(P["excl"], bool, copy=True)
    excl6[row, max(e0 - 1, 0)] = True
    P6 = dict(P, excl=excl6)
    pt_gc = BR.borrow_per_trade_bp([tr[j]], np.array([BR.GC_BPS]))
    n_raised = 0
    for flag in (True, False):
        try:
            check_borrow(P6, [tr[j]], pt_gc, np.array([flag]), np.random.default_rng(0), k=1)
        except AssertionError:
            n_raised += 1
    assert n_raised == 2, "[6] [SB] did not raise"
    check_borrow(P6, [tr[j]], BR.borrow_per_trade_bp([tr[j]], np.array([BR.HTB_BPS])), np.array([True]), np.random.default_rng(0), k=1)
    print("    [6] [S] raises on a short ledger handed +50 bp; [SB] raises on a borrow charged at GC for a trade the rule says is HTB")
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)")


def event_buckets(P, trades):
    """The rsi-percentile bucket at (e0, row); -1 where the rsi percentile is undefined."""
    b = np.array([P["bucket_rsi"][e0, row] for row, e0, _a, _p, _s in trades], int)
    ok = np.array([P["rsi_pct_ok"][e0, row] for row, e0, _a, _p, _s in trades], bool)
    return np.where(ok, b, -1)


def stage_controls(P, sig, draws, part=0):
    hi, sc = P["EVENTS49"][sig]
    res = run_short(P, hi, sc, "cap")
    obs = float(pnl_bp(res).mean())
    print(f"\n  {sig} part {part}: observed mean hedged excess, SHORT, cap exit {obs:+.2f} bp on {len(res['trades']):,} trades")
    rngA = np.random.default_rng([SEED, STUDY, 1, SIGNALS.index(sig), part])
    rngB = np.random.default_rng([SEED, STUDY, 2, SIGNALS.index(sig), part])
    A_, B_ = [], []
    ts = time.time()
    for d in range(draws):
        sl_, ss_, sc_ = rotate_confined(P, zeros_like(hi), hi, sc, rngA)
        rA = run_short(P, ss_, sc_, "cap")
        pa = pnl_bp(rA)
        assert np.isfinite(pa).all(), "[A] NaN in a rotated draw"
        A_.append(float(pa.mean()))
        sB = control_b_defined(P, hi, rngB)
        rB = run_short(P, sB, sc, "cap")
        B_.append(float(pnl_bp(rB).mean()))
        if (d + 1) % 25 == 0 or d + 1 == draws:
            print(f"    {sig}: {d + 1}/{draws} ({time.time() - ts:.0f}s, {(time.time() - ts) / (d + 1):.1f}s per draw)", flush=True)
    out = dict(signal=sig, draws=draws, part=part, observed=obs, trades=len(res["trades"]), control_A=A_, control_B=B_)
    f = Path(str(CTRL).format(sig=f"{sig}_p{part}"))
    f.write_text(json.dumps(out))
    print(f"  wrote {f.name}: A p50 {np.median(A_):+.2f} p95 {np.quantile(A_, .95):+.2f}; "
          f"B p50 {np.median(B_):+.2f} p95 {np.quantile(B_, .95):+.2f} ({time.time() - P['t0']:.0f}s)")


def clean(o):
    """D347's NaN -> null cleaner (a closure there; replicated)."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def stage_report(P):
    r1T, finT, ocT, m_f, m_f_oc, beta, F = P["r1T"], P["finT"], P["ocT"], P["m_f"], P["m_f_oc"], P["beta"], P["F"]
    HALF, CLOSE, years, T = P["HALF"], P["CLOSE"], P["years"], P["T"]
    bucket_rsi, elig, ok_b = P["bucket_rsi"], P["elig"], P["rsi_pct_ok"]
    down = set(P["down_years"])
    half = T // 2
    Fs = -F                                                          # the SHORT base rate
    E_all = float(np.nanmean(Fs[elig & np.isfinite(Fs)])) * 1e4
    E_b = {}
    for b in range(10):
        m = elig & np.isfinite(Fs) & ok_b & (bucket_rsi == b)
        E_b[b] = float(np.nanmean(Fs[m])) * 1e4 if m.any() else np.nan
    print(f"\n  SHORT BASE RATES: -(forward-40 hedged excess), all floored name-bars {E_all:+.1f} bp; by rsi bucket: " +
          " ".join(f"b{b}:{E_b[b]:+.0f}" for b in range(10)))
    REPORT, CHECK = {}, {}
    rngC = np.random.default_rng([SEED, STUDY, 3])
    for sig in SIGNALS:
        hi, sc = P["EVENTS49"][sig]
        R_ = {}
        for lens in ("short", "mirror"):
            for exit_ in ("cap", "invalidation"):
                res = run_short(P, hi, sc, exit_) if lens == "short" else run_mirror(P, hi, sc, exit_)
                tr = res["trades"]
                assert all(t[4] == (1 if lens == "short" else 0) for t in tr), f"{sig} {lens}: wrong side in the ledger"
                pnl = pnl_bp(res)
                pb = pnl_beta_adjusted(tr, r1T, m_f, ocT, m_f_oc, beta) * 1e4
                yrs = np.array([years[t[1]] for t in tr])
                eras = np.array([t[1] < half for t in tr])
                c2 = {cv: two_c(tr, HALF[cv], CLOSE) for cv in CONVS}
                in_down = np.isin(yrs, list(down))
                d_ = dict(trades=len(tr), mean_bp=float(pnl.mean()), median_bp=float(np.median(pnl)),
                          t=float(pnl.mean() / (pnl.std(ddof=1) / np.sqrt(pnl.size))), share_pos=float((pnl > 0).mean()),
                          hold_mean=float(np.mean([t[2] for t in tr])),
                          beta_adj_mean_bp=float(np.nanmean(pb)), beta_median=float(np.nanmedian([beta[t[1], t[0]] for t in tr])),
                          two_c={cv: c2[cv][0] for cv in CONVS}, net_per_trade={cv: float(pnl.mean()) - c2[cv][0] for cv in CONVS},
                          held_half={cv: c2[cv][1] for cv in CONVS}, held_price=c2["PUB"][2],
                          down_years_mean_bp=(float(pnl[in_down].mean()) if in_down.any() else None), down_years_n=int(in_down.sum()),
                          era1_mean_bp=float(pnl[eras].mean()) if eras.any() else None, era2_mean_bp=float(pnl[~eras].mean()) if (~eras).any() else None,
                          by_year={int(y): float(pnl[yrs == y].mean()) for y in np.unique(yrs)})
                if lens == "short":
                    pt, htb, _rate = borrow_of(P, tr)
                    bm = float(pt.mean())
                    comm = 2.0 * PER_SHARE / c2["PUB"][2] * 1e4          # the commission half of 2c, bp per trade
                    d_["borrow"] = dict(scheme=BORROW_SCHEME, mean_bp=bm, median_bp=float(np.median(pt)), htb_share=float(htb.mean()),
                                        gc_bps=BR.GC_BPS, htb_bps=BR.HTB_BPS)
                    d_["net_per_trade_borrow"] = {cv: float(pnl.mean()) - c2[cv][0] - bm for cv in CONVS}
                    d_["breakeven_half_spread_bp_side"] = (float(pnl.mean()) - bm - comm) / 2.0
                if lens == "short" and exit_ == "cap":
                    CHECK[sig] = event_accounting(P, hi, res)
                    b_ev = event_buckets(P, tr)
                    Es = float(pnl.mean())
                    inter = {}
                    for b in range(10):
                        mb = b_ev == b
                        if mb.any():
                            Esb = float(pnl[mb].mean())
                            inter[b] = dict(n=int(mb.sum()), E_sb=Esb, E_b=E_b[b], interaction=Esb - E_b[b] - Es + E_all)
                    d_["interaction"] = inter
                    d_["events_undefined_rsi_bucket"] = int((b_ev < 0).sum())
                    signs = rngC.choice([-1.0, 1.0], size=(1000, pnl.size))
                    cC = (signs * pnl[None, :]).mean(axis=1)
                    d_["control_C"] = dict(p50=float(np.median(cC)), p95=float(np.quantile(cC, .95)), max=float(cC.max()), draws=1000,
                                           above=bool(Es > np.quantile(cC, .95)))
                R_[f"{lens}/{exit_}"] = d_
        parts = sorted(REPO.glob(f"data/d349_ctrl_{sig}_p*.json"))
        if parts:
            cs_ = [json.loads(p.read_text()) for p in parts]
            A_ = np.concatenate([np.array(c["control_A"]) for c in cs_])
            B_ = np.concatenate([np.array(c["control_B"]) for c in cs_])
            obs = R_["short/cap"]["mean_bp"]
            for c in cs_:
                assert abs(c["observed"] - obs) < 1e-9, f"observed differs between stages for {sig}"
                assert c["trades"] == R_["short/cap"]["trades"], f"trade count differs between stages for {sig}"
            R_["controls"] = dict(draws=int(sum(c["draws"] for c in cs_)), parts=[c["part"] for c in cs_],
                                  A=dict(p50=float(np.median(A_)), p95=float(np.quantile(A_, .95)), max=float(A_.max()),
                                         distinct=int(len(set(A_.tolist()))), above=bool(obs > np.quantile(A_, .95))),
                                  B=dict(p50=float(np.median(B_)), p95=float(np.quantile(B_, .95)), max=float(B_.max()),
                                         distinct=int(len(set(B_.tolist()))), above=bool(obs > np.quantile(B_, .95))),
                                  timing_value=float(obs - np.median(A_)))
        REPORT[sig] = R_

    # ---- print ----------------------------------------------------------------------------------------------------
    print("\n" + "=" * 128)
    print("THE SHORT SIGNALS -- every event taken, next-open fill, hedged against the floored market; bp per trade (mirror = the LONG of the same event)")
    print("=" * 128)
    print("  %-14s %-6s %-12s %6s %8s %8s %6s %7s %8s %9s %9s %9s %8s %8s" % ("signal", "side", "exit", "n", "mean", "median", "t", "hold", "beta-adj",
                                                                            "net PUB", "net PB", "PUB+brw", "down-yr", "eras"))
    for sig in SIGNALS:
        for key, d_ in REPORT[sig].items():
            if key == "controls":
                continue
            lens, exit_ = key.split("/")
            print("  %-14s %-6s %-12s %6d %+8.1f %+8.1f %+6.2f %7.1f %+8.1f %+9.1f %+9.1f %9s %8s %8s" % (
                sig, lens, exit_, d_["trades"], d_["mean_bp"], d_["median_bp"], d_["t"], d_["hold_mean"], d_["beta_adj_mean_bp"],
                d_["net_per_trade"]["PUB"], d_["net_per_trade"]["PB"],
                ("%+.1f" % d_["net_per_trade_borrow"]["PUB"]) if "net_per_trade_borrow" in d_ else "-",
                ("%+.0f" % d_["down_years_mean_bp"]) if d_["down_years_mean_bp"] is not None else "-",
                "%+.0f/%+.0f" % (d_["era1_mean_bp"] or 0, d_["era2_mean_bp"] or 0)))
    print(f"\n  down-years (floored market negative): {P['down_years']}")
    print("\n  CHECK (cap exit): events = entries + on names already held + unpriced; trades = entries - open at the end")
    for sig in SIGNALS:
        c = CHECK[sig]
        print(f"  {sig:14s} events {c['events']:6,} = {c['entries']:6,} + {c['already_held']:5,} + {c['unpriced']:3,}; "
              f"trades {c['trades']:6,} = {c['entries']:6,} - {c['open_at_end']}")
    print("\n  CONTROLS on the short cap-exit statistic (mean hedged excess, bp); timing = observed - A p50:")
    print("  %-14s %8s | %8s %8s %8s %4s %6s | %8s %8s %8s %4s %6s | %8s %8s %6s | %8s" % (
        "signal", "observed", "A p50", "A p95", "A max", "dist", "above", "B p50", "B p95", "B max", "dist", "above", "C p95", "C max", "above", "timing"))
    for sig in SIGNALS:
        R_ = REPORT[sig]
        c = R_.get("controls")
        cc = R_["short/cap"]["control_C"]
        if c:
            print("  %-14s %+8.2f | %+8.2f %+8.2f %+8.2f %4d %6s | %+8.2f %+8.2f %+8.2f %4d %6s | %+8.2f %+8.2f %6s | %+8.2f" % (
                sig, R_["short/cap"]["mean_bp"], c["A"]["p50"], c["A"]["p95"], c["A"]["max"], c["A"]["distinct"], "yes" if c["A"]["above"] else "NO",
                c["B"]["p50"], c["B"]["p95"], c["B"]["max"], c["B"]["distinct"], "yes" if c["B"]["above"] else "NO",
                cc["p95"], cc["max"], "yes" if cc["above"] else "NO", c["timing_value"]))
        else:
            print(f"  {sig:14s} {R_['short/cap']['mean_bp']:+8.2f} | controls not run" + " " * 62 +
                  f"| {cc['p95']:+8.2f} {cc['max']:+8.2f} {'yes' if cc['above'] else 'NO':>6s} |")
    print("\n  INTERACTION with the rsi ranking (short, cap exit, short base rate): bucket | n | E[signal,bucket] | E[bucket] | interaction")
    for sig in SIGNALS:
        inter = REPORT[sig]["short/cap"]["interaction"]
        print(f"  {sig}: " + " ".join(f"b{b}[{v['n']}] {v['E_sb']:+.0f}/{v['E_b']:+.0f}/{v['interaction']:+.0f}" for b, v in sorted(inter.items())))
    print("  buckets: 0=[0,2] 1=(2,5] 2=(5,10] 3=(10,25] 4=(25,50] 5=(50,75] 6=(75,90] 7=(90,95] 8=(95,98] 9=(98,100] of the rsi percentile at t-1")
    print("  top buckets: " + "; ".join(
        f"{sig} " + " ".join(f"b{b}:{REPORT[sig]['short/cap']['interaction'][b]['interaction']:+.0f}" if b in REPORT[sig]["short/cap"]["interaction"]
                             else f"b{b}:-" for b in (6, 7, 8, 9)) + f" | argmax b{top_bucket_of(REPORT[sig])}" for sig in SIGNALS))
    print("\n  NET per trade, SHORT: mean - 2c (PB / PUB) - borrow (gc_htb: GC %.0f, HTB %.0f bp/yr)" % (BR.GC_BPS, BR.HTB_BPS))
    print("  %-14s %-12s %8s %7s %7s %7s %6s | %8s %8s | %8s %8s | %8s" % ("signal", "exit", "mean", "2c PB", "2c PUB", "borrow", "HTB%",
                                                                         "net PB", "net PUB", "PB+brw", "PUB+brw", "be hs/s"))
    for sig in SIGNALS:
        for exit_ in ("cap", "invalidation"):
            d_ = REPORT[sig][f"short/{exit_}"]
            print("  %-14s %-12s %+8.1f %7.1f %7.1f %7.1f %6.1f | %+8.1f %+8.1f | %+8.1f %+8.1f | %8.1f" % (
                sig, exit_, d_["mean_bp"], d_["two_c"]["PB"], d_["two_c"]["PUB"], d_["borrow"]["mean_bp"], 100 * d_["borrow"]["htb_share"],
                d_["net_per_trade"]["PB"], d_["net_per_trade"]["PUB"], d_["net_per_trade_borrow"]["PB"], d_["net_per_trade_borrow"]["PUB"],
                d_["breakeven_half_spread_bp_side"]))
    print("  be hs/s: the held median half-spread (bp per side) at which net after commission and borrow is zero")

    # ---- predictions --------------------------------------------------------------------------------------------------
    def survives(sig):
        R_ = REPORT[sig]
        c = R_.get("controls")
        return bool(c and c["A"]["above"] and c["B"]["above"] and R_["short/cap"]["control_C"]["above"])
    with_ctrl = [s for s in SIGNALS if "controls" in REPORT[s]]
    surv = [s for s in CANDIDATES if survives(s)]
    all_surv = [s for s in SIGNALS if survives(s)]
    q = {}
    q["Q1"] = bool(len(surv) > 0)
    q["Q2"] = bool(len(with_ctrl) == len(SIGNALS) and all(REPORT[s]["controls"]["A"]["p50"] < 0 for s in SIGNALS))
    n_timing = sum(1 for s in with_ctrl if REPORT[s]["controls"]["timing_value"] > 0)
    q["Q3"] = bool(n_timing >= 2)
    q["Q4"] = bool(any(REPORT[s][f"short/{e}"]["net_per_trade_borrow"]["PUB"] > 0 for s in SIGNALS for e in ("cap", "invalidation")))

    def top_vs_rest(sig):
        inter = REPORT[sig]["short/cap"]["interaction"]
        if TOP_BUCKET not in inter:
            return None
        rest = [v["interaction"] for b, v in inter.items() if b != TOP_BUCKET]
        return inter[TOP_BUCKET]["interaction"] - max(rest) if rest else None
    q["Q5"] = bool(all((top_vs_rest(s) if top_vs_rest(s) is not None else -1e9) > 0 for s in ("on_share", "skew_63")))
    q["Q6"] = bool(all(REPORT[s]["mirror/cap"]["mean_bp"] < 0 for s in SIGNALS))
    q["Q7"] = bool(all(REPORT[s]["short/cap"]["down_years_mean_bp"] is not None
                       and REPORT[s]["short/cap"]["down_years_mean_bp"] > REPORT[s]["short/cap"]["mean_bp"] for s in SIGNALS))
    q["Q8"] = bool(all(REPORT[s]["short/cap"]["beta_adj_mean_bp"] > REPORT[s]["short/cap"]["mean_bp"] for s in SIGNALS))
    cf = lambda k: "CONFIRMED" if q[k] else "FALSIFIED"
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) on_share, skew_63 or close_in_range above all three controls: {cf('Q1')} -- survivors {surv}; "
          f"all survivors {all_surv}; controls run for {with_ctrl}")
    print(f"  Q2 control A centred below zero for every one of the five: {cf('Q2')} -- " +
          ", ".join(f"{s} {REPORT[s]['controls']['A']['p50']:+.1f}" for s in with_ctrl) +
          ("" if len(with_ctrl) == len(SIGNALS) else f" (missing {[s for s in SIGNALS if s not in with_ctrl]})"))
    print(f"  Q3 timing value observed - A p50 positive for at least two of the five: {cf('Q3')} -- {n_timing} positive: " +
          ", ".join(f"{s} {REPORT[s]['controls']['timing_value']:+.1f}" for s in with_ctrl))
    print(f"  Q4 (against) some short nets > 0 after the PUB round trip and the borrow, either exit: {cf('Q4')} -- " +
          ", ".join(f"{s} {REPORT[s]['short/cap']['net_per_trade_borrow']['PUB']:+.1f}/{REPORT[s]['short/invalidation']['net_per_trade_borrow']['PUB']:+.1f}"
                    for s in SIGNALS))
    print(f"  Q5 on_share and skew_63 interaction most positive in the top rsi bucket (98,100]: {cf('Q5')} -- " +
          ", ".join(f"{s} top-rest {top_vs_rest(s):+.1f} (argmax b{top_bucket_of(REPORT[s])})" if top_vs_rest(s) is not None else f"{s} no top-bucket events"
                    for s in ("on_share", "skew_63")))
    print(f"  Q6 every mirror (the long of the same event) < 0: {cf('Q6')} -- " +
          ", ".join(f"{s} {REPORT[s]['mirror/cap']['mean_bp']:+.1f}" for s in SIGNALS))
    print(f"  Q7 short excess in down-years exceeds the overall excess for every signal: {cf('Q7')} -- " +
          ", ".join(f"{s} {REPORT[s]['short/cap']['down_years_mean_bp']:+.1f} vs {REPORT[s]['short/cap']['mean_bp']:+.1f} (n {REPORT[s]['short/cap']['down_years_n']})"
                    for s in SIGNALS if REPORT[s]["short/cap"]["down_years_mean_bp"] is not None))
    print(f"  Q8 beta-adjusted above equal-weight for every short: {cf('Q8')} -- " +
          ", ".join(f"{s} {REPORT[s]['short/cap']['mean_bp']:+.1f}->{REPORT[s]['short/cap']['beta_adj_mean_bp']:+.1f} (beta {REPORT[s]['short/cap']['beta_median']:.2f})"
                    for s in SIGNALS))

    out = dict(note="D349: five short signals as events against three drift-matched controls, two hedges, the borrow, the splits, the "
                    "rsi-rank interaction on the short base rate. Every event taken (invariant lens); nothing is a book; nothing promoted.",
               signals=SIGNALS, candidates=CANDIDATES, cap=CAP, top_pct=TOP, rsi_turn_level=RSI_HI, bucket_edges=BUCKET_EDGES,
               short_base_rate_all_bp=E_all, short_base_rate_by_bucket_bp=E_b, down_years=P["down_years"], floored_market_by_year=P["yr_ret"],
               borrow=dict(scheme=BORROW_SCHEME, gc_bps=BR.GC_BPS, htb_bps=BR.HTB_BPS, px_htb=BR.PX_HTB),
               check=CHECK, report=REPORT, survivors=all_surv, candidate_survivors=surv, predictions=q)
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - P['t0']:.0f}s)")


def top_bucket_of(R_):
    inter = R_["short/cap"]["interaction"]
    return max(inter, key=lambda b: inter[b]["interaction"]) if inter else -1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--controls", choices=SIGNALS)
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    print("D349  is the short signal real? -- three drift-matched controls on the short side, with the borrow")
    P = prep(need_grids=a.selftest or a.report)
    if a.selftest:
        stage_selftest(P)
    elif a.controls:
        stage_controls(P, a.controls, a.draws, a.part)
    elif a.report:
        stage_report(P)
    else:
        ap.error("one of --selftest, --controls SIG, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
