"""D700 STAGE 0 -- the premise check for the principal's channel trend detector: after D480's hand-cell channel spans
10 bars with a minimum slope, does ES continue or fade, and on which clock (1, 5 or 15 minutes)? (The principal,
2026-09-30: "If we have stable channels for 10 bars in the one minute time frame and they have a some minimum slope?
... reuse that machinary"; then "Ok lets go with your proposal".) Design:
docs/decisions/D700-STAGE-0-DESIGN-where-es-channels-stop-fading.md, committed before this runner.

    uv run python scripts/stage0_d700_channel_clock_profile.py --selftest
    uv run python scripts/stage0_d700_channel_clock_profile.py --run --data-root "<main checkout>/data"

In-sample on D688's panel, 2016-01-05 -> 2023-12-29; nothing on or after 2024-01-01 is read. Trades nothing.

THE CONSTRUCTION (the design's; nothing here is tuned)
  lines      D480's hand cell (CELL_HAND) unchanged: D399's tie-tolerant pivots at k = 1 and recalc_pair with every
             hand-cell setting; the margin (a drawn-level offset nothing here reads) is 0
  rescaling  each clock's bars are rescaled so the per-bar sigma is SIGMA_REF = 0.0205, the median per-bar sigma of
             the twelve hand-drawn windows (D478) on which the percent dials were set: within session d the bar log
             returns are multiplied by SIGMA_REF / s_hat(c, d), s_hat = the sd of the clock's within-session bar
             returns over the 20 sessions before d (prior-only); O/H/L/C are each rescaled against the previous
             bar's close, the first bar of a session against its own open (the overnight gap is dropped; the
             series and the channel state run on across sessions)
  clocks     1-, 5- and 15-minute bars aggregated within the session from D688's 1-minute bars (390, 78, 26 a day)
  channel    at bar close t in direction D: both lines drawn; D*g_support >= f*SIGMA_REF and D*g_resistance >=
             f*SIGMA_REF; each side's segment anchor at or before t - 9 (the lines span 10 bars); f = 0.1 declared
  event      the first bar close the channel holds after one it did not; deciding close up to 15:45; filled one
             minute after the deciding close
DECLARED OUTPUTS: the profile (clock x horizon {15, 30, 60 min, close} x gamma class) of the signed move in MES
dollars against the time-matched drift, with the excess's day-clustered t; the timing null per clock (short-gamma
days, +60 min, the event schedule rotated among short-gamma days, enumerated); the slope sweep f in {0.05, 0.1,
0.2, 0.4} and the strict "held at each of the last 10 closes" reading at +60; up vs down and events by hour on the
primary 5-minute clock; channel coverage.
DECLARED READING per clock (short-gamma days, +60 min, f = 0.1): CONTINUES if the excess has clustered t >= +2 and the
signed gross is above the timing null's p95; FADES if t <= -2 and below its p05; else NEITHER.

Output data/d700_channel_clock_profile.json: statistics only, no per-date GEX (SqueezeMetrics, under the permission
of 2026-09-28).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d688_gamma_close as S  # noqa: E402  (importing defines, never runs)

OUT = REPO / "data" / "d700_channel_clock_profile.json"
D688_JSON = REPO / "data" / "d688_gamma_close.json"
SIGMA_REF = 0.0205
CLOCKS = (1, 5, 15)
PRIMARY_CLOCK = 5
SPAN = 10
F_PRIMARY = 0.1
F_SWEEP = (0.05, 0.1, 0.2, 0.4)
HORIZONS = (15, 30, 60)
H_PRIMARY = 60
LAST_DECIDE_J = 375                               # 15:45
CLOSE_J = 390
TRAIL = 20
N_PROBES = 10                                     # per kind: event bars, bars just before an event, random bars
PROBE_LIMIT = {1: 60000, 5: 40000, 15: 60000}     # probes within the first bars, to bound the rebuild's cost


def P(*a, **k):
    print(*a, **k, flush=True)


def _load(name, filename):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ bars and rescaling
def clock_bars(O1, H1, L1, C1, c):
    """Aggregate the 1-minute day-session bars (n x 390) into c-minute bars (n x 390/c) within the session."""
    n, nb = O1.shape[0], 390 // c
    return (O1[:, ::c].copy(), H1.reshape(n, nb, c).max(2), L1.reshape(n, nb, c).min(2), C1[:, c - 1::c].copy())


def rescale(O, H, L, C, valid, gapped=False):
    """The rescaled, spliced series. Returns rows (the day indices in the series, in order), the per-day s_hat, and
    flattened rescaled O/H/L/C prices. Prior-only: s_hat(d) reads the 20 valid days before d; the cumulative sum is
    prefix-stable. `gapped` measures a session's first bar from the PRIOR session's close (the right-quantity
    contrast only)."""
    n, nb = O.shape
    prevP = np.concatenate([O[:, :1], C[:, :-1]], axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.log(C / prevP)
    vi = np.flatnonzero(valid)
    sig = np.full(n, np.nan)
    for q in range(TRAIL, len(vi)):
        sig[vi[q]] = np.std(r[vi[q - TRAIL:q]].ravel(), ddof=1)
    rows = vi[TRAIL:]
    s = (SIGMA_REF / sig[rows])[:, None]
    pp = prevP[rows].copy()
    if gapped and len(rows) > 1:
        pp[1:, 0] = C[rows[:-1], -1]
    with np.errstate(divide="ignore", invalid="ignore"):
        lo_, lh_, ll_, lc_ = (np.log(X[rows] / pp) for X in (O, H, L, C))
    if gapped:
        lc_[1:, 0] = np.log(C[rows[1:], 0] / pp[1:, 0])
    inc = (s * lc_).ravel()
    ycl = np.cumsum(inc)
    yref = np.concatenate([[0.0], ycl[:-1]])
    so = s.repeat(nb, axis=1).ravel()
    yo = yref + so * lo_.ravel()
    yh = yref + so * lh_.ravel()
    yl = yref + so * ll_.ravel()
    return {"rows": rows, "sig": sig, "nb": nb, "op": np.exp(yo), "hi": np.exp(yh), "lo": np.exp(yl), "cl": np.exp(ycl), "inc": inc}


def lines(op, hi, lo, cl):
    """D480's hand cell on the rescaled bars. Returns G, L, S per side (S = the live segment's anchor bar, -1 when not
    drawn), exactly `lines_from_arrays`'s call with the anchors kept and no margin."""
    H = _load("d480h", "d480_hand_cell.py")
    RC = _load("d399rc", "d399_recalc_segment.py")
    DR = _load("d399dr", "d399_draw_construction.py")
    from backtest_framework.data.bars import TimestampedBar
    from backtest_framework.research.structure import pivots_tie_tolerant as PVT
    from backtest_framework.simulator.fills import Bar
    cell = H.CELL_HAND
    t0 = datetime(2000, 1, 1)
    bars = [TimestampedBar(t0 + timedelta(minutes=i), Bar(float(op[i]), float(hi[i]), float(lo[i]), float(cl[i]))) for i in range(op.size)]
    piv = H.pivots_of(PVT, bars, cell["k"])
    with np.errstate(divide="ignore"):
        body = {"support": np.log(np.minimum(op, cl)), "resistance": np.log(np.maximum(op, cl))}
        ext = {"support": np.log(lo), "resistance": np.log(hi)}
    G, L, Sg, _ = RC.recalc_pair(
        piv, cell["k"], body, op.size, carry=cell["carry"], min_piv=cell["min_piv"],
        max_dg=RC.INF if cell["dg"] is None else DR.h_of_annual(cell["dg"]),
        max_dh=math.log1p(cell["dh"] / 100), use_body=cell["use_body"], min_width=math.log1p(cell["min_width"] / 100),
        delta=DR.DELTA, ext_log=ext, break_pivot=cell["break_pivot"], anchor_clear=cell["anchor_clear"],
        decay_end=cell["decay_end"], extend_back=cell["extend_back"], back_tol=None, fit_mode=cell["fit_mode"],
        touch_tol=cell["touch_tol"], min_touch=cell["min_touch"], height_mode=cell["height_mode"],
        walk_chain=cell["walk_chain"], max_reach=cell["max_reach"], syn_ttl=cell["syn_ttl"], stale_w=cell["stale_w"],
        stale_d=math.log1p(cell["stale_d"] / 100), stale_stat=cell["stale_stat"],
        fit_tol=None if cell["fit_tol"] is None else math.log1p(cell["fit_tol"] / 100),
        pair_break=cell["pair_break"], pair_draw=cell["pair_draw"], anchor_mode=cell["anchor_mode"],
        anchor_q=cell["anchor_q"], decay_mode=cell["decay_mode"], break_depth=math.log1p(cell["break_depth"] / 100),
        break_bars=cell["break_bars"], max_piv=cell["max_piv"], break_keep=cell.get("break_keep"))
    return G, L, Sg


def channel(G, L, Sg, f, sign):
    """The channel condition at every bar close, direction `sign`."""
    t = np.arange(G["support"].size)
    thr = f * SIGMA_REF
    ok = np.isfinite(L["support"]) & np.isfinite(L["resistance"])
    with np.errstate(invalid="ignore"):
        ok &= (sign * G["support"] >= thr) & (sign * G["resistance"] >= thr)
    ok &= (Sg["support"] >= 0) & (Sg["resistance"] >= 0)
    ok &= (t - Sg["support"] >= SPAN - 1) & (t - Sg["resistance"] >= SPAN - 1)
    return ok


def onsets(cond):
    prev = np.concatenate([[False], cond[:-1]])
    return cond & ~prev


def strict(cond):
    """Held at each of the last SPAN bar closes."""
    cs = np.concatenate([[0], np.cumsum(cond.astype(np.int64))])
    t = np.arange(cond.size)
    lo_ = np.maximum(t + 1 - SPAN, 0)
    return (cs[t + 1] - cs[lo_] == SPAN)


# ------------------------------------------------------------------ the worker (one clock) with its lag audit
def clock_job(args):
    c, O1, H1, L1, C1, valid, seed = args
    t0 = time.time()
    O, H, L, C = clock_bars(O1, H1, L1, C1, c)
    R = rescale(O, H, L, C, valid)
    G, Lx, Sg = lines(R["op"], R["hi"], R["lo"], R["cl"])
    cu = channel(G, Lx, Sg, F_PRIMARY, +1)
    cd = channel(G, Lx, Sg, F_PRIMARY, -1)
    build_s = time.time() - t0
    # the truncation rebuild: cut the RAW bars at t (later days dropped, later bars of t's day blanked), rebuild the
    # rescaling, the pivots and the lines on the cut, and compare the channel state at t
    nb = R["nb"]
    rng = np.random.default_rng([seed, c])
    lim = min(PROBE_LIMIT[c], cu.size)
    ev = np.flatnonzero(onsets(cu | cd)[:lim])
    ev = ev[ev > 3 * nb]
    pick = lambda a: a[rng.choice(a.size, min(N_PROBES, a.size), replace=False)] if a.size else a
    probes = np.unique(np.concatenate([pick(ev), pick(ev - 1), pick(np.arange(3 * nb, lim))]))

    def rebuild_state(tp):
        q, b = divmod(int(tp), nb)
        day = int(R["rows"][q])
        keep = np.zeros_like(valid); keep[:day + 1] = valid[:day + 1]
        O2, H2, L2, C2 = O.copy(), H.copy(), L.copy(), C.copy()
        for X in (O2, H2, L2, C2):
            X[day, b + 1:] = np.nan
            X[day + 1:] = np.nan
        R2 = rescale(O2, H2, L2, C2, keep)
        sl = slice(0, int(tp) + 1)
        if not (R2["rows"].size and R2["rows"][q] == day):
            raise AssertionError(f"[LAG] clock {c}: the cut series lost day {day}")
        G2, L2x, S2 = lines(R2["op"][sl], R2["hi"][sl], R2["lo"][sl], R2["cl"][sl])
        return bool(channel(G2, L2x, S2, F_PRIMARY, +1)[-1]), bool(channel(G2, L2x, S2, F_PRIMARY, -1)[-1])

    states = {int(tp): rebuild_state(tp) for tp in probes}

    def audit(u, d):
        for tp, (a, b_) in states.items():
            assert (a, b_) == (bool(u[tp]), bool(d[tp])), f"[LAG] clock {c}, bar {tp}: full {bool(u[tp]), bool(d[tp])} vs the truncated rebuild {a, b_}"

    audit(cu, cd)
    peek = lambda x: np.concatenate([x[1:], x[-1:]])
    fired = True
    try:
        audit(peek(cu), peek(cd))
        fired = False
    except AssertionError:
        pass
    return {"c": c, "rows": R["rows"], "sig": R["sig"], "nb": nb, "inc": R["inc"], "G": G, "L": Lx, "S": Sg,
            "n_probes": int(len(probes)), "n_probe_events": int(sum(1 for tp in probes if cu[tp] or cd[tp])), "peek_fired": fired,
            "build_s": build_s, "audit_s": time.time() - t0 - build_s}


# ------------------------------------------------------------------ statistics
def cl_t(x, day):
    """Mean and its day-clustered t."""
    x = np.asarray(x, float)
    n = x.size
    if n < 3:
        return float(x.mean()) if n else float("nan"), float("nan")
    _, g = np.unique(day, return_inverse=True)
    u = np.bincount(g, weights=x - x.mean())
    G_ = u.size
    var = (u ** 2).sum() / n ** 2 * G_ / max(G_ - 1, 1)
    return float(x.mean()), float(x.mean() / math.sqrt(var)) if var > 0 else float("nan")


def move(PM, row, jf, d, h, usd):
    """The signed move in dollars from the fill minute jf to jf + h (h = None: to 16:00)."""
    j2 = np.full_like(jf, CLOSE_J) if h is None else jf + h
    return d * (PM[row, j2] - PM[row, jf]) * usd


def profile(PM, ev, mbar, usd, n_days):
    """Per horizon: count, events a day, mean and median signed gross, hit, drift control, excess and clustered t."""
    out = {}
    for h in HORIZONS + (None,):
        m = np.ones(ev["jf"].size, bool) if h is None else (ev["jf"] + h <= CLOSE_J)
        row, jf, d = ev["row"][m], ev["jf"][m], ev["d"][m]
        key = "close" if h is None else f"+{h}m"
        if not m.any():
            out[key] = {"n": 0}
            continue
        g = move(PM, row, jf, d, h, usd)
        j2 = np.full_like(jf, CLOSE_J) if h is None else jf + h
        ctrl = d * (mbar[j2] - mbar[jf]) * usd
        mx, tx = cl_t(g - ctrl, row)
        mg, tg = cl_t(g, row)
        out[key] = {"n": int(m.sum()), "per_day": float(m.sum() / n_days), "mean_gross": mg, "t_gross": tg, "median_gross": float(np.median(g)),
                    "hit": float((g > 0).mean()), "mean_drift_control": float(ctrl.mean()), "mean_excess": mx, "t_excess": tx}
    return out


def timing_null(PM, ev, rows_s, usd, h=H_PRIMARY):
    """The event schedule (fill minute, direction) of day i + k applied to day i's prices, k = 10 .. n-10."""
    m = ev["jf"] + h <= CLOSE_J
    pos = {int(r): q for q, r in enumerate(rows_s)}
    A = np.zeros((rows_s.size, CLOSE_J + 1))
    for r, jf, d in zip(ev["row"][m], ev["jf"][m], ev["d"][m]):
        A[pos[int(r)], jf + h] += d
        A[pos[int(r)], jf] -= d
    Gm = A @ PM[rows_s].T * usd
    ntr = int(m.sum())
    direct = float(move(PM, ev["row"][m], ev["jf"][m], ev["d"][m], h, usd).sum())
    if abs(np.trace(Gm) - direct) > 1e-6 * max(1.0, abs(direct)):
        raise S.GateError(f"[NULL] the schedule matrix's diagonal {np.trace(Gm)} != the events' sum {direct}")
    n = rows_s.size
    ar = np.arange(n)
    ks = S.rot_ks(n)
    stat = np.array([Gm[(ar + k) % n, ar].sum() / ntr for k in ks])
    b = S.blk(float(stat[0]), stat[1:])
    b["below_p05"] = bool(stat[0] < b["p05"])
    return b


def events_of(cond_u, cond_d, nb, c, rows, dayok, row_of_day):
    """Onsets on the flattened series -> (PM row, fill minute, direction), deciding close <= 15:45, tradable days."""
    out = {"row": [], "jf": [], "d": []}
    for cond, sgn in ((cond_u, +1), (cond_d, -1)):
        t = np.flatnonzero(onsets(cond))
        q, b = np.divmod(t, nb)
        day = rows[q]
        j = c * (b + 1)
        k = dayok[day] & (j <= LAST_DECIDE_J)
        out["row"].append(row_of_day[day[k]]); out["jf"].append(j[k] + 1); out["d"].append(np.full(k.sum(), sgn))
    return {kk: np.concatenate(v).astype(int) for kk, v in out.items()}


# ------------------------------------------------------------------ the study
def core(O1, H1, L1, C1, valid, PM, pidx, short, days, usd, log=P, parallel=True, seed=700):
    """O1..C1: every loaded session x 390 one-minute bars; valid: sessions usable in the series; PM: the same sessions
    x 391 prices (09:30 open, then 09:31 .. 16:00); pidx: the panel's rows; short: the panel's G_SUM < 0."""
    nall = O1.shape[0]
    jobs = [(c, O1, H1, L1, C1, valid, seed) for c in CLOCKS]
    t0 = time.time()
    if parallel:
        with ProcessPoolExecutor(max_workers=len(CLOCKS)) as ex:
            outs = list(ex.map(clock_job, jobs))
    else:
        outs = [clock_job(j) for j in jobs]
    W = {o["c"]: o for o in outs}
    for c in CLOCKS:
        o = W[c]
        if not o["peek_fired"]:
            raise S.GateError(f"[LAG] clock {c}: the audit did not fire on a detection read one bar ahead")
        if o["n_probe_events"] == 0:
            raise S.GateError(f"[LAG] clock {c}: no probe landed on a channel bar; the audit is vacuous")
        log(f"  clock {c}m: lines built in {o['build_s']:.0f} s; lag audit {o['n_probes']} truncated rebuilds ({o['n_probe_events']} on channel bars) "
            f"agree, and it RAISES on a detection read one bar ahead ({o['audit_s']:.0f} s)")
    log(f"  lines and audits in {time.time() - t0:.0f} s")
    # the prior-only rescaling, re-derived for sampled days in plain Python from the raw minutes
    rng = np.random.default_rng(seed)
    for c in CLOCKS:
        rows, sig = W[c]["rows"], W[c]["sig"]
        vi = list(np.flatnonzero(valid))
        for d in rng.choice(rows, 3, replace=False):
            q = vi.index(int(d))
            rr = []
            for e in vi[q - TRAIL:q]:
                prev = float(O1[e, 0])
                for b in range(390 // c):
                    cl = float(C1[e, c * (b + 1) - 1])
                    rr.append(math.log(cl / prev)); prev = cl
            ref = statistics.stdev(rr)
            if abs(ref - sig[d]) > 1e-9 * ref:
                raise S.GateError(f"[RESCALE] clock {c}, day {d}: s_hat {sig[d]!r} vs the loop's {ref!r}")
    # tradable days: in the panel, in every clock's series, finite prices
    inser = np.ones(nall, bool)
    for c in CLOCKS:
        m = np.zeros(nall, bool); m[W[c]["rows"]] = True
        inser &= m
    prow = np.full(nall, -1); prow[pidx] = np.arange(pidx.size)
    dayok = np.zeros(nall, bool)
    dayok[pidx] = inser[pidx] & np.isfinite(PM[pidx]).all(1)
    row_of_day = np.arange(nall)                                   # PM rows are the loaded sessions
    sh_all = np.zeros(nall, bool); sh_all[pidx] = short
    cls = {"short_gamma": dayok & sh_all, "long_gamma": dayok & ~sh_all}
    mbar = {k: PM[v].mean(0) for k, v in cls.items()}
    ndays = {k: int(v.sum()) for k, v in cls.items()}
    log(f"  tradable days: {ndays}")
    # the sign audit, in money
    up = np.linspace(100.0, 110.0, CLOSE_J + 1)[None, :]
    if not (move(up, np.array([0]), np.array([16]), np.array([+1]), 60, usd)[0] > 0 > move(up, np.array([0]), np.array([16]), np.array([-1]), 60, usd)[0]):
        raise S.GateError("[SIGN] an up event on a rising path does not pay, or a down event does not pay the opposite")
    # the right quantity
    res = {"sigma_ref": SIGMA_REF, "span": SPAN, "f_primary": F_PRIMARY, "tradable_days": ndays, "clocks": {}}
    for c in CLOCKS:
        o = W[c]
        nb = o["nb"]
        q_in = np.flatnonzero(dayok[o["rows"]])
        sd = float(np.std(o["inc"].reshape(-1, nb)[q_in].ravel(), ddof=1))
        if abs(sd / SIGMA_REF - 1) > 0.15:
            raise S.GateError(f"[QUANTITY] clock {c}: the rescaled returns' sd {sd:.5f} is not within 15% of {SIGMA_REF}")
        Oc, Hc, Lc, Cc = clock_bars(O1, H1, L1, C1, c)
        gap = rescale(Oc, Hc, Lc, Cc, valid, gapped=True)
        if np.allclose(gap["cl"], np.exp(np.cumsum(o["inc"]))):
            raise S.GateError(f"[QUANTITY] clock {c}: the spliced series equals the gapped one")
        res["clocks"][c] = {"rescaled_sd_over_ref": sd / SIGMA_REF}
    # the profile, the null and the reading
    for c in CLOCKS:
        o = W[c]
        nb, rows = o["nb"], o["rows"]
        G, Lx, Sg = o["G"], o["L"], o["S"]
        cu, cd = channel(G, Lx, Sg, F_PRIMARY, +1), channel(G, Lx, Sg, F_PRIMARY, -1)
        inb = np.repeat(dayok[rows], nb)
        r = res["clocks"][c]
        r["coverage"] = {"both_lines_drawn": float((np.isfinite(Lx["support"]) & np.isfinite(Lx["resistance"]))[inb].mean()),
                         "channel_up": float(cu[inb].mean()), "channel_down": float(cd[inb].mean())}
        r["profile"] = {}
        EV = {}
        for k, dm in cls.items():
            ev = events_of(cu, cd, nb, c, rows, dm, row_of_day)
            EV[k] = ev
            r["profile"][k] = profile(PM, ev, mbar[k], usd, ndays[k])
        rows_s = np.flatnonzero(cls["short_gamma"])
        r["timing_null_short_60m"] = timing_null(PM, EV["short_gamma"], rows_s, usd)
        p = r["profile"]["short_gamma"][f"+{H_PRIMARY}m"]
        tn = r["timing_null_short_60m"]
        r["reading"] = ("CONTINUES" if p["t_excess"] >= 2 and tn["above_p95"] else "FADES" if p["t_excess"] <= -2 and tn["below_p05"] else "NEITHER")
        for k in cls:
            q = r["profile"][k]
            log(f"  {c:>2}m {k:11s}: " + " | ".join(
                f"{h} n{v['n']} ({v.get('per_day', 0):.2f}/d) gross ${v.get('mean_gross', float('nan')):+.2f} med ${v.get('median_gross', float('nan')):+.2f} "
                f"drift ${v.get('mean_drift_control', float('nan')):+.2f} excess ${v.get('mean_excess', float('nan')):+.2f} (t {v.get('t_excess', float('nan')):+.2f})"
                for h, v in q.items()))
        log(f"  {c:>2}m TIMING NULL (short, +60m): ${tn['observed']:+.2f} p05 ${tn['p05']:+.2f} p50 ${tn['p50']:+.2f} p95 ${tn['p95']:+.2f} (pct {tn['pct_rank']:.3f}); "
            f"coverage both-drawn {r['coverage']['both_lines_drawn']:.2f}, channel up {r['coverage']['channel_up']:.3f} down {r['coverage']['channel_down']:.3f}; READING {r['reading']}")
        # the slope sweep and the strict reading, at +60 on both classes
        r["slope_sweep_60m"] = {}
        for f in F_SWEEP:
            u_, d_ = channel(G, Lx, Sg, f, +1), channel(G, Lx, Sg, f, -1)
            r["slope_sweep_60m"][str(f)] = {k: profile(PM, events_of(u_, d_, nb, c, rows, dm, row_of_day), mbar[k], usd, ndays[k])[f"+{H_PRIMARY}m"] for k, dm in cls.items()}
        r["strict_60m"] = {k: profile(PM, events_of(strict(cu), strict(cd), nb, c, rows, dm, row_of_day), mbar[k], usd, ndays[k])[f"+{H_PRIMARY}m"] for k, dm in cls.items()}
        log(f"  {c:>2}m slope sweep +60m excess (short | long): " + " ".join(
            f"f{f}: ${v['short_gamma'].get('mean_excess', float('nan')):+.2f}(t{v['short_gamma'].get('t_excess', float('nan')):+.1f}) | ${v['long_gamma'].get('mean_excess', float('nan')):+.2f}(t{v['long_gamma'].get('t_excess', float('nan')):+.1f})"
            for f, v in r["slope_sweep_60m"].items()))
        s_ = r["strict_60m"]
        log(f"  {c:>2}m strict (held 10 closes) +60m: short n{s_['short_gamma']['n']} excess ${s_['short_gamma'].get('mean_excess', float('nan')):+.2f} (t {s_['short_gamma'].get('t_excess', float('nan')):+.2f}); "
            f"long n{s_['long_gamma']['n']} excess ${s_['long_gamma'].get('mean_excess', float('nan')):+.2f} (t {s_['long_gamma'].get('t_excess', float('nan')):+.2f})")
        if c == PRIMARY_CLOCK:
            ev = EV["short_gamma"]
            ud = {}
            for sgn, nm in ((+1, "up"), (-1, "down")):
                m = ev["d"] == sgn
                ud[nm] = profile(PM, {kk: v[m] for kk, v in ev.items()}, mbar["short_gamma"], usd, ndays["short_gamma"])[f"+{H_PRIMARY}m"]
            hr = (ev["jf"] - 1 + 30) // 60 + 9                                  # the deciding close's hour
            byh = {}
            for h_ in sorted(set(hr.tolist())):
                m = hr == h_
                byh[int(h_)] = profile(PM, {kk: v[m] for kk, v in ev.items()}, mbar["short_gamma"], usd, ndays["short_gamma"])[f"+{H_PRIMARY}m"]
            r["primary_short_up_down_60m"] = ud
            r["primary_short_by_hour_60m"] = byh
            log(f"  {c:>2}m short up/down +60m: " + " ".join(f"{k} n{v['n']} excess ${v.get('mean_excess', float('nan')):+.2f} (t {v.get('t_excess', float('nan')):+.2f})" for k, v in ud.items()))
            log(f"  {c:>2}m short by hour +60m: " + " ".join(f"{k}: n{v['n']} ${v.get('mean_excess', float('nan')):+.1f}" for k, v in byh.items()))
    res["reading"] = {c: res["clocks"][c]["reading"] for c in CLOCKS}
    log(f"  READING: {res['reading']}")
    return res


# ------------------------------------------------------------------ the data
def load(data_root: Path, log=P):
    D699 = _load("d699", "stage0_d699_gamma_macd_long.py")
    D, PM, pidx = D699.panel(data_root, log)
    b = pd.read_csv(data_root / "fixtures" / "fut_ES_rth_1m.csv.gz", usecols=["day", "hhmm", "open", "high", "low", "close"],
                    dtype={"day": str, "hhmm": str}, encoding="utf-8")
    b = b[(b["day"] >= S.WARM_FROM) & (b["day"] < S.CUTOFF)]
    S.guard_window(b["day"], "D700 minute OHLC")
    sess = pd.read_csv(data_root / "fixtures" / "fut_index_sessions.csv.gz", usecols=["root", "day", "bars"], dtype={"root": str, "day": str}, encoding="utf-8")
    cal = np.array(sorted(sess[(sess["root"] == "ES") & (sess["bars"] >= 380)]["day"].unique()))
    nb_ = b.groupby("day").size()
    alld = np.array([d for d in cal if S.WARM_FROM <= d < S.CUTOFF and nb_.get(d, 0) >= 380])     # load_inputs's rule
    if alld.size != PM.shape[0]:
        raise S.GateError(f"[DAYS] {alld.size} sessions against the panel grid's {PM.shape[0]}")
    mins = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=k)).strftime("%H:%M") for k in range(390)]
    piv = {x: b.pivot(index="day", columns="hhmm", values=x).reindex(index=alld, columns=mins).to_numpy(float) for x in ("open", "high", "low", "close")}
    C1 = pd.DataFrame(piv["close"]).ffill(axis=1).to_numpy(float)
    miss = ~np.isfinite(piv["close"])
    O1, H1, L1 = (np.where(miss, C1, piv[x]) for x in ("open", "high", "low"))
    if not np.array_equal(np.nan_to_num(C1, nan=-1.0), np.nan_to_num(PM[:, 1:], nan=-1.0)):
        raise S.GateError("[GRID] the OHLC close grid differs from D699's price grid")
    valid = np.isfinite(O1).all(1) & np.isfinite(H1).all(1) & np.isfinite(L1).all(1) & np.isfinite(C1).all(1)
    log(f"  minute OHLC: {alld.size} sessions, {int(valid.sum())} complete; panel {len(D)} sessions")
    return D, PM, pidx, O1, H1, L1, C1, valid


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    D, PM, pidx, O1, H1, L1, C1, valid = load(data_root, log)
    days = D.index.to_numpy().astype(str)
    E = S.d685()
    mes = E.cost_spec("ES", "micro")
    usd = mes["usd_per_point"]
    short = D["G_SUM"].to_numpy(float) < 0
    res = core(O1, H1, L1, C1, valid, PM, pidx, short, days, usd, log)
    res = {"spec": "D700 STAGE 0 (in-sample premise check; D480's hand-cell channel on rescaled ES bars, 1/5/15-minute clocks)",
           "cost_rt_usd_for_reference": mes["cost_rt_usd"], **res, "timing_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(res, indent=1, default=lambda o_: o_.item() if hasattr(o_, "item") else str(o_)), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


def selftest(log=P) -> int:
    """A synthetic random walk through every path of core(): the audits must pass and fire, and no clock's +60-minute
    excess on short-gamma days may sit outside +-2 clustered SE (the design's check)."""
    rng = np.random.default_rng(7)
    n = 160
    lr = 0.0004 * rng.standard_normal((n, 390, 4)) / 2
    base = 4000.0 * np.exp(np.cumsum(lr.reshape(n, -1), axis=1)).reshape(n, 390, 4)
    O1 = base[:, :, 0]; C1 = base[:, :, 3]
    H1 = base.max(2); L1 = base.min(2)
    PM = np.column_stack([O1[:, 0], C1])
    valid = np.ones(n, bool)
    pidx = np.arange(40, n)
    short = rng.random(pidx.size) < 0.5
    days = np.array([str((pd.Timestamp("2016-01-04") + pd.Timedelta(days=int(i))).date()) for i in pidx])
    global PROBE_LIMIT
    PROBE_LIMIT = {1: 25000, 5: 8000, 15: 4000}
    res = core(O1, H1, L1, C1, valid, PM, pidx, short, days, 5.0, log, parallel=False)
    for c in CLOCKS:
        t = res["clocks"][c]["profile"]["short_gamma"][f"+{H_PRIMARY}m"]["t_excess"]
        if not abs(t) < 2:
            raise S.GateError(f"[SELFTEST] clock {c}: t {t:+.2f} on a random walk")
    log("  SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.exit(run(a.data_root) if a.run else selftest() if a.selftest else 1)
