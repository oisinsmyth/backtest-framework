"""D440 -- THE CAUSAL CONSTRUCTION REBUILT FROM THE ORACLE: grow right, one bar at a time.

    uv run python scripts/d440_causal_grow.py --proof        twelve live names, audits, timing

WHY. D439's oracle is greedy left-to-right growth: seed a minimum-length window, extend it while
it passes every filter, stop at the first bar that fails, restart past it. At every bar during
growth the decision "the window [a0, t] is valid" reads only bars <= t. Only two things in the
oracle see the future:

  1. the line drawn at an interior bar s is the fit on the WHOLE window, to its end;
  2. the first `minlen` - 1 bars are drawn retroactively -- a window that never reaches the
     minimum length is never drawn at all.

Remove both and the same algorithm is an online one. That is this file. The window grows one bar
at a time (the oracle's stride growth can step over an invalid interior length, so its channels
can be longer; the online walk cannot skip a bar); the line at bar t is the fit on [a0, t]; a bar
is drawn only once its window is `minlen` long. Everything else -- the envelope fit, the touch
count, the width, the parallelism, the offset and touch-density filters, the restart at the
break bar -- is the oracle's, parameter for parameter, so the settings line the principal chose
by eye on the oracle page means the same thing here.

TWO DIALS THE ORACLE DOES NOT HAVE, both about restarting:
  `back`   how many bars BEFORE the break bar the next window may begin. 0 is the oracle: the next
           window starts at the break bar, so `minlen` - 1 bars pass before anything is drawn
           again. `minlen` - 1 lets a fresh window be tried at the break bar itself.
  `atmax`  what happens when the window reaches `maxlen`: "end" is the oracle (the channel ends,
           the next starts after it); "slide" drops the oldest bar each bar instead.

AUDITS.
  [O]  with back = 0 and atmax = end, the WINDOWS this finds (start, end) are exactly the oracle's
       greedy channels when the oracle grows one bar at a time -- so the only differences between
       the two line sources are the two hindsight leaks above, and nothing else.
  [F]  truncating the series at any bar t and recomputing gives the same lines up to t -- the
       construction reads nothing after the bar. The trader-side [F] in D439 tested the RULE; this
       tests the LINES.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
LIVE = REPO / "temp" / "d399_live_bars.json"

# THE BASELINE, chosen by eye by the principal on the grow-right page (2026-09-11). Looser than
# the oracle line in the two places that bind (max gradient gap 0.4 -> 1.05, max width 24 -> 55%),
# the touch-density filter off, two touches a side, and a 30-bar seed.
DEFAULTS = dict(tol=math.log1p(0.02), mt=2, basis="wick", minlen=30, maxlen=1000,
                mw=0.0, maxw=math.log1p(0.55), maxoff=-1.0, mintd=-1.0, tau=1.05,
                grow="parallel", back=9, atmax="end",
                brk=-1.0, bbars=1, bon="close")
SETTINGS_LINE = ("split=causal grow=parallel back=9 atmax=end tol=2 mt=2 basis=wick minlen=30 "
                 "maxlen=1000 mw=0 maxw=55 maxoff=-1 mintd=-1 tau=1.05 brk=-1 bbars=1 bon=close")
# THE BREAK RULE (`brk`, `bbars`, `bon`). The envelope contains every wick by construction, so a
# bar through the line never fails the fit -- the hull simply re-tilts around it, and a window
# can live for hundreds of bars while the line it shows is redrawn under the trader's feet. The
# principal asked for a bar that breaks the line to invalidate it. So: at bar t, the line the
# trader HAD (the previous bar's fit, projected one bar) is compared with the bar's close (`bon`
# = close) or its wick (`bon` = wick); a price beyond it by more than `brk` per cent is a break;
# `bbars` consecutive breaks kill the window. -1 = off. Checked BEFORE the refit, so a broken
# window is never re-fitted into validity.
# the oracle line it replaced, kept so [O] and the D439 comparison can still be reproduced
ORACLE_LINE = ("split=causal grow=chain back=0 atmax=end tol=1.75 mt=3 basis=wick minlen=20 "
               "maxlen=1000 mw=0 maxw=24 maxoff=-1 mintd=35 tau=0.4")


def parse_line(line):
    """The page's settings line -> the parameter dict. Percentages become logs, as on the page."""
    P = dict(DEFAULTS)
    for tok in line.split():
        k, v = tok.split("=", 1)
        if k in ("tol", "mw"):
            P[k] = math.log1p(float(v) / 100)
        elif k in ("maxw", "maxoff", "brk"):
            P[k] = math.log1p(float(v) / 100) if float(v) >= 0 else -1.0
        elif k == "mintd":
            P[k] = float(v) / 100 if float(v) >= 0 else -1.0
        elif k in ("mt", "minlen", "maxlen", "back", "bbars"):
            P[k] = int(v)
        elif k == "tau":
            P[k] = float(v)
        elif k in ("basis", "atmax", "grow", "bon"):
            P[k] = v
    return P


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def fit_window(RC, lo, hi, a, b, P):
    """One window, fitted and filtered: D439's `fit_window` with the constants made parameters.
    Same tests in the same order, same clamp of a negative offset to zero, same touch count."""
    m = b - a + 1
    if m < 2:
        return None
    x = np.arange(a, b + 1, dtype=float)
    gs, cs, ts = RC.envelope_fit(x, lo[a:b + 1], "support", P["tol"])
    gr, cr, tr = RC.envelope_fit(x, hi[a:b + 1], "resistance", P["tol"])
    if not (np.isfinite(gs) and np.isfinite(gr)) or ts < P["mt"] or tr < P["mt"]:
        return None
    w0 = (gr * x[0] + cr) - (gs * x[0] + cs)
    w1 = (gr * x[-1] + cr) - (gs * x[-1] + cs)
    if min(w0, w1) < P["mw"]:
        return None
    if P["maxw"] >= 0 and max(w0, w1) > P["maxw"]:
        return None
    if P["tau"] >= 0 and abs(gs - gr) > P["tau"] * max(abs(gs), abs(gr)):
        return None
    d = np.minimum(lo[a:b + 1] - (gs * x + cs), (gr * x + cr) - hi[a:b + 1])
    off = float(np.maximum(d, 0.0).sum() / m)
    td = float((d <= P["tol"]).sum() / m)
    if P["maxoff"] >= 0 and off > P["maxoff"]:
        return None
    if P["mintd"] >= 0 and td < P["mintd"]:
        return None
    return dict(a=a, b=b, gs=float(gs), cs=float(cs), gr=float(gr), cr=float(cr),
                ts=int(ts), tr=int(tr), off=off, td=td, w=float((w0 + w1) / 2),
                score=int(ts) + int(tr))


def causal_channels(RC, lo, hi, P, a0=0, a1=None, cl=None):
    """THE ONLINE WALK. One pass, left to right; at bar t everything read is <= t.

    Returns runs of DRAWN bars. A run is {a, b, A, As[], gs[], cs[], gr[], cr[], ...}: `a` the
    first drawn bar, `b` the last, `As` the start of the window shown at each bar (`A` is the
    last of them), and per-bar arrays of the fit on [As[j], t]. Nothing is drawn while a window
    is shorter than `minlen`, and nothing between windows.

    TWO GROWTH RULES (`grow`):
      "chain"     the oracle's greedy walk made online: one window at a time, the next search
                  begins where the last window broke. Path-dependent by construction -- every
                  boundary is an artifact of the previous one, so a change in `minlen` re-times
                  the whole chain. Kept because [O] proves it IS the oracle minus hindsight.
      "parallel"  every candidate grows at once: each bar spawns a seed from the last `minlen`
                  bars if they pass, every live window is extended by one bar and dropped when
                  it fails, and the LONGEST survivor is shown. The line at t depends only on the
                  bars inside its own window, never on where an earlier window ended ([I])."""
    if P.get("brk", -1.0) >= 0 and P.get("bon", "close") == "close" and cl is None:
        raise ValueError("the break rule on closes needs `cl` (log closes)")
    if P.get("grow", "parallel") == "parallel":
        return _grow_parallel(RC, lo, hi, P, a0, a1, cl)
    return _grow_chain(RC, lo, hi, P, a0, a1, cl)


def _broken(lo, hi, cl, t, f, P):
    """Does bar t break the line the trader had (fit `f` from the previous bar, projected to t)?"""
    d = P["brk"]
    if d < 0 or f is None:
        return False
    s_line, r_line = f["gs"] * t + f["cs"], f["gr"] * t + f["cr"]
    if P["bon"] == "close":
        return cl[t] < s_line - d or cl[t] > r_line + d
    return lo[t] < s_line - d or hi[t] > r_line + d


def _grow_parallel(RC, lo, hi, P, a0=0, a1=None, cl=None):
    n = lo.size if a1 is None else a1
    minlen, maxlen, slide, bbars = P["minlen"], P["maxlen"], P["atmax"] == "slide", P["bbars"]
    back = P["back"]
    runs, run, live = [], None, []          # live: [A, last fit, break count], oldest first
    shown, shown_nb = None, 0               # the line the trader SAW at the previous bar
    bound = a0                              # no window may start before this bar (set by a break)
    for t in range(a0, n):
        # A BREAK OF THE SHOWN LINE KILLS EVERY WINDOW OLDER THAN `back`. Testing each window
        # against its own line was not enough: when the longest died, the next survivor -- a
        # sibling seeded a few bars later, sharing most of its bars -- was drawn in its place,
        # and the trader saw the line jump rather than disappear (627 sibling switches against
        # 408 gaps on the twelve names). The line the trader had is the one that breaks; when it
        # does, the structure it stood on is gone, so only windows younger than `back` bars
        # before the break survive. `back` then means the same thing under both growth rules.
        shown_nb = shown_nb + 1 if _broken(lo, hi, cl, t, shown, P) else 0
        if P["brk"] >= 0 and shown_nb >= bbars:
            bound = t - back                # ... and the same floor binds the seeds that follow:
            live = [w for w in live if w[0] >= bound]   # the [B] audit caught a seed at t -
            shown_nb = 0                    # minlen + 1 reaching back across the break
        keep, best = [], None
        for A, fprev, nb in live:
            nb = nb + 1 if _broken(lo, hi, cl, t, fprev, P) else 0
            if nb >= bbars and P["brk"] >= 0:
                continue                    # the bar broke the line the trader had: dead
            if t - A + 1 > maxlen:
                if not slide:
                    continue
                A = t - maxlen + 1
            if keep and keep[-1][0] == A:   # two windows slid onto the same start: one fit
                continue
            f = fit_window(RC, lo, hi, A, t, P)
            if f is None:
                continue
            keep.append([A, f, nb])
            if best is None:                # oldest first, so the first survivor is the longest
                best = (A, f)
        s = t - minlen + 1
        if s >= bound and (not keep or keep[-1][0] != s):
            f = fit_window(RC, lo, hi, s, t, P)
            if f is not None:
                keep.append([s, f, 0])
                if best is None:
                    best = (s, f)
        live = keep
        if best is None:
            shown = None
            if run is not None:
                runs.append(run)
                run = None
            continue
        A, f = best
        shown = f
        if run is None:
            run = dict(a=t, b=t, A=A, As=[], gs=[], cs=[], gr=[], cr=[], ts=[], tr=[],
                       off=[], td=[], w=[])
        run["A"] = A
        run["As"].append(A)
        _push(run, f)
    if run is not None:
        runs.append(run)
    return runs


def _grow_chain(RC, lo, hi, P, a0=0, a1=None, cl=None):
    n = lo.size if a1 is None else a1
    minlen, maxlen, back, bbars = P["minlen"], P["maxlen"], P["back"], P["bbars"]
    runs, run, A, bound, t, fprev, nb = [], None, -1, a0, a0, None, 0
    while t < n:
        f = None
        if A >= 0:
            nb = nb + 1 if _broken(lo, hi, cl, t, fprev, P) else 0
            dead = nb >= bbars and P["brk"] >= 0
            L = t - A + 1
            if dead:
                pass
            elif L <= maxlen:
                f = fit_window(RC, lo, hi, A, t, P)
            elif P["atmax"] == "slide":
                A = t - maxlen + 1
                f = fit_window(RC, lo, hi, A, t, P)
            if f is not None:
                run["As"].append(A)
                _push(run, f)
                fprev = f
                t += 1
                continue
            # the window ends at t - 1; t is the break bar (or the bar past maxlen). The oracle
            # restarts its search at exactly this bar; `back` lets it start earlier.
            runs.append(run)
            run, A, bound, fprev, nb = None, -1, t - back, None, 0
        s = t - minlen + 1
        if s >= bound and s >= a0:
            f = fit_window(RC, lo, hi, s, t, P)
            if f is not None:
                A = s
                run = dict(a=t, b=t, A=A, As=[A], gs=[], cs=[], gr=[], cr=[], ts=[], tr=[],
                           off=[], td=[], w=[])
                _push(run, f)
                fprev, nb = f, 0
        t += 1
    if run is not None:
        runs.append(run)
    return runs


def _push(run, f):
    run["b"] = f["b"]
    for k in ("gs", "cs", "gr", "cr", "ts", "tr", "off", "td", "w"):
        run[k].append(f[k])


def oracle_onebar(RC, lo, hi, P, a0=0, a1=None):
    """D439's greedy oracle (slack 0) with the stride growth replaced by one bar at a time. The
    reference for [O]: its channels' (start, end) must equal the online walk's windows."""
    n = lo.size if a1 is None else a1
    segs, a = [], a0
    minlen, maxlen = P["minlen"], P["maxlen"]
    while a + minlen <= n:
        cur = fit_window(RC, lo, hi, a, a + minlen - 1, P)
        if cur is None:
            a += 1
            continue
        b = a + minlen - 1
        while b + 1 < n and b + 1 - a + 1 <= maxlen:
            f = fit_window(RC, lo, hi, a, b + 1, P)
            if f is None:
                break
            cur, b = f, b + 1
        segs.append(cur)
        a = b + 1
    return segs


def causal_lines(RC, bars, P, runs=None):
    """The per-bar view the trader is given, shaped exactly like D434's `build_lines` and D439's
    `oracle_lines` so the same rule and walk read it: a level and a gradient per side on drawn
    bars, nan elsewhere, plus `proj`/`gproj`/`seen`/`drawn`."""
    m = len(bars)
    op = np.array([b.bar.open for b in bars], float)
    cl = np.array([b.bar.close for b in bars], float)
    hi = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    with np.errstate(divide="ignore"):
        if P["basis"] == "body":
            llo, lhi = np.log(np.minimum(op, cl)), np.log(np.maximum(op, cl))
        else:
            llo, lhi = np.log(lo), np.log(hi)
        lcl = np.log(cl)
    if runs is None:
        runs = causal_channels(RC, llo, lhi, P, cl=lcl)
    G = {kd: np.full(m, np.nan) for kd in ("support", "resistance")}
    L = {kd: np.full(m, np.nan) for kd in ("support", "resistance")}
    q = np.arange(m, dtype=float)
    for r in runs:
        i = np.arange(r["a"], r["b"] + 1)
        gs, cs, gr, cr = (np.array(r[k]) for k in ("gs", "cs", "gr", "cr"))
        G["support"][i], L["support"][i] = gs, gs * i + cs
        G["resistance"][i], L["resistance"][i] = gr, gr * i + cr
    proj, gproj, seen, drawn = {}, {}, {}, {}
    for kd in ("support", "resistance"):
        on = np.isfinite(L[kd])
        c_at = np.where(on, L[kd] - G[kd] * q, np.nan)
        idx = np.where(on, np.arange(m), -1)
        last = np.maximum.accumulate(idx)
        ok = last >= 0
        g_last = np.where(ok, G[kd][np.maximum(last, 0)], np.nan)
        c_last = np.where(ok, c_at[np.maximum(last, 0)], np.nan)
        proj[kd] = g_last * q + c_last
        gproj[kd] = g_last
        seen[kd] = last
        drawn[kd] = on
    return dict(m=m, op=op, cl=cl, hi=hi, lo=lo, G=G, L=L, proj=proj, gproj=gproj, seen=seen,
                drawn=drawn), runs


# ----------------------------------------------------------------------------- audits
def audit_windows_match_oracle(RC, lo, hi, P, a0=0, a1=None):
    """[O] online windows == one-bar greedy oracle channels, as (start, end) pairs. The oracle
    has no break rule, so it is switched off here."""
    Q = dict(P, grow="chain", back=0, atmax="end", brk=-1.0)
    runs = causal_channels(RC, lo, hi, Q, a0, a1)
    segs = oracle_onebar(RC, lo, hi, Q, a0, a1)
    got = [(r["A"], r["b"]) for r in runs]
    want = [(s["a"], s["b"]) for s in segs]
    if got != want:
        raise AssertionError(f"[O] online windows {got[:6]}... != oracle one-bar {want[:6]}...")
    # and the LAST line of each run is the oracle's line for that channel, bit for bit
    for r, s in zip(runs, segs):
        if not (r["gs"][-1] == s["gs"] and r["cs"][-1] == s["cs"]
                and r["gr"][-1] == s["gr"] and r["cr"][-1] == s["cr"]):
            raise AssertionError("[O] the final fit of a window differs from the oracle's")
    return len(runs)


def _levels(runs, upto):
    """bar -> (gs, cs, gr, cr) for every drawn bar <= upto. What [F] compares."""
    out = {}
    for r in runs:
        for j, t in enumerate(range(r["a"], r["b"] + 1)):
            if t <= upto:
                out[t] = (r["gs"][j], r["cs"][j], r["gr"][j], r["cr"][j])
    return out


def audit_prefix(RC, lo, hi, P, probes, full=None, cl=None):
    """[F] the lines up to bar t are unchanged when the series is cut at t."""
    if full is None:
        full = causal_channels(RC, lo, hi, P, cl=cl)
    for t in probes:
        cut = causal_channels(RC, lo[:t + 1], hi[:t + 1], P,
                              cl=None if cl is None else cl[:t + 1])
        if _levels(full, t) != _levels(cut, t):
            raise AssertionError(f"[F] lines up to bar {t} changed when the series was cut there")
    return len(probes)


def audit_break(lo, hi, cl, runs, P):
    """[B] NO SHOWN LINE SURVIVES ITS OWN BREAK. Along every run of drawn bars, count consecutive
    bars that break the line SHOWN at the previous bar, whichever window it came from. When the
    count reaches `bbars` at bar t, the bar may still be drawn -- but only by a window that
    started within `back` bars before t (everything older was killed), and no later bar of the
    run may show a window older than that either."""
    if P["brk"] < 0:
        return 0
    checked = 0
    for r in runs:
        nb, floor = 0, -1
        for j in range(1, len(r["gs"])):
            t = r["a"] + j
            fprev = dict(gs=r["gs"][j - 1], cs=r["cs"][j - 1], gr=r["gr"][j - 1], cr=r["cr"][j - 1])
            nb = nb + 1 if _broken(lo, hi, cl, t, fprev, P) else 0
            checked += 1
            if nb >= P["bbars"]:
                floor, nb = t - P["back"], 0
            if r["As"][j] < floor:
                raise AssertionError(f"[B] bar {t} shows a window from {r['As'][j]}, older than "
                                     f"the break at {floor + P['back']} allows")
    return checked


def audit_phase_free(RC, lo, hi, P, t0, cl=None):
    """[I] PATH INDEPENDENCE. Start the walk at bar t0 instead of bar 0. No window is longer than
    `maxlen`, so from bar t0 + maxlen - 1 on, every window the late start can show is one the
    early start also had -- the lines must be identical there. The chain rule fails this (its
    phase is inherited from windows before t0); the parallel rule must pass it."""
    full = causal_channels(RC, lo, hi, P, cl=cl)
    late = causal_channels(RC, lo, hi, P, a0=t0, cl=cl)
    # with the break rule on, a break before t0 also floors the seeds by `back` bars, so the
    # horizon is maxlen + back; with it off, maxlen - 1
    t1 = t0 + P["maxlen"] + (P["back"] if P["brk"] >= 0 else -1)
    lf = {t: v for t, v in _levels(full, lo.size).items() if t >= t1}
    ll = {t: v for t, v in _levels(late, lo.size).items() if t >= t1}
    return lf == ll, len(lf)


def audit_audits_fire(RC, lo, hi, P):
    """A self-test that cannot fail is worse than none. Break what each assertion READS:
    [O] compares (start, end) lists -- feed it windows one bar longer; [F] compares per-bar
    levels -- feed it a construction whose level at t is the level at t + 1 (a peek)."""
    Q = dict(P, grow="chain", back=0, atmax="end", brk=-1.0)
    runs = causal_channels(RC, lo, hi, Q)
    if not runs or max(r["b"] - r["a"] for r in runs) < 2:
        raise AssertionError("self-test needs a run at least three bars long")
    segs = oracle_onebar(RC, lo, hi, Q)
    if [(r["A"], r["b"]) for r in runs] == [(s["a"], s["b"] + 1) for s in segs]:
        raise AssertionError("[O] self-test: windows one bar longer were not distinguishable")
    r = max(runs, key=lambda z: z["b"] - z["a"])
    peek = [dict(z) for z in runs]
    i = runs.index(r)
    peek[i] = dict(r, gs=r["gs"][1:] + r["gs"][-1:], cs=r["cs"][1:] + r["cs"][-1:],
                   gr=r["gr"][1:] + r["gr"][-1:], cr=r["cr"][1:] + r["cr"][-1:])
    key = [(r["gs"][j], r["cs"][j], r["gr"][j], r["cr"][j]) for j in range(len(r["gs"]))]
    moves = [j for j in range(len(key) - 1) if key[j] != key[j + 1]]
    if not moves:
        raise AssertionError("self-test needs a run whose line moves between two bars")
    t = r["a"] + moves[0]                 # the peeking level differs from the true one here
    try:
        audit_prefix(RC, lo, hi, Q, [t], full=peek)
    except AssertionError:
        return True
    raise AssertionError("[F] self-test: a construction that peeks one bar ahead passed")


# ----------------------------------------------------------------------------- proof on the live names
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--proof", action="store_true")
    ap.add_argument("--line", default=SETTINGS_LINE)
    ap.add_argument("--dump", default="", help="write per-name runs (page-window bounds) as JSON")
    a = ap.parse_args()
    RC = _load("d399rc", "d399_recalc_segment.py")
    P = parse_line(a.line)
    d = json.loads(LIVE.read_text())
    print(f"  {a.line}")
    print(f"  {'name':6} {'runs':>4} {'cover':>6} {'drawn med':>9} {'win med':>7} "
          f"{'width':>6} {'off':>5} {'touch':>5} {'ms':>6}")
    tot_runs, tot_cov, tot_bars, dump, nchk = 0, 0, 0, {}, 0
    for nm in d["names"]:
        o, h, l, c = (np.array(nm[k], float) for k in ("o", "h", "l", "c"))
        if P["basis"] == "body":
            lo, hi = np.log(np.minimum(o, c)), np.log(np.maximum(o, c))
        else:
            lo, hi = np.log(l), np.log(h)
        cl = np.log(c)
        st0, n = nm["start"], nm["n"]
        marg = min(P["maxlen"], 500)                      # the page's search bounds, exactly
        lo0, hi1 = max(0, st0 - marg), min(nm["m"], st0 + n + marg)
        t0 = time.time()
        runs = causal_channels(RC, lo, hi, P, lo0, hi1, cl=cl)
        nchk += audit_break(lo, hi, cl, runs, P)
        ms = 1000 * (time.time() - t0)
        shown = [r for r in runs if r["b"] >= st0 and r["a"] <= st0 + n - 1]
        cov = sum(min(r["b"], st0 + n - 1) - max(r["a"], st0) + 1 for r in shown)
        dl = [r["b"] - r["a"] + 1 for r in shown]
        wl = [r["b"] - r["A"] + 1 for r in shown]
        wid = [100 * math.expm1(r["w"][-1]) for r in shown]
        off = [100 * math.expm1(float(np.mean(r["off"]))) for r in shown]
        td = [100 * float(np.mean(r["td"])) for r in shown]
        print(f"  {nm['symbol']:6} {len(shown):4d} {100 * cov / n:5.0f}% "
              f"{np.median(dl) if dl else 0:9.0f} {np.median(wl) if wl else 0:7.0f} "
              f"{np.mean(wid) if wid else 0:6.1f} {np.mean(off) if off else 0:5.1f} "
              f"{np.mean(td) if td else 0:5.0f} {ms:6.0f}")
        tot_runs += len(shown)
        tot_cov += cov
        tot_bars += n
        dump.setdefault(nm["symbol"], []).append(
            [dict(a=r["a"], b=r["b"], A=r["A"], As=r["As"], gs=r["gs"], cs=r["cs"],
                  gr=r["gr"], cr=r["cr"]) for r in runs])
    print(f"  total {tot_runs} runs, {100 * tot_cov / tot_bars:.0f}% of bars covered"
          + (f"; [B] {nchk} drawn bars checked, none survived its own break  OK"
             if P["brk"] >= 0 else "; break rule off"))
    if a.dump:
        Path(a.dump).write_text(json.dumps(dump))
        print(f"  dumped runs to {a.dump}")
    if a.proof:
        nm = d["names"][0]
        lo, hi = np.log(np.array(nm["l"], float)), np.log(np.array(nm["h"], float))
        cl = np.log(np.array(nm["c"], float))
        k = audit_windows_match_oracle(RC, lo, hi, P)
        print(f"  [O] chain: {k} windows on {nm['symbol']} equal the one-bar greedy oracle's "
              f"channels, final fits bit-identical  OK")
        pr = [int(v) for v in np.linspace(60, lo.size - 2, 7)]
        for g in ("parallel", "chain"):
            audit_prefix(RC, lo, hi, dict(P, grow=g), pr, cl=cl)
        print(f"  [F] both rules: lines unchanged up to each of {len(pr)} cut points -- the "
              f"construction reads nothing after the bar  OK")
        audit_audits_fire(RC, lo, hi, P)
        print(f"  [X] both audits distinguish a shifted window list  OK")
        # [XB] the break audit must reject a walk that ignores breaks
        QB = dict(P, brk=math.log1p(0.01), bbars=1, bon="close")
        loose = causal_channels(RC, lo, hi, dict(QB, brk=-1.0), cl=cl)
        try:
            audit_break(lo, hi, cl, loose, QB)
            raise SystemExit("[XB] the break audit accepted a walk with the break rule off")
        except AssertionError:
            strict = causal_channels(RC, lo, hi, QB, cl=cl)
            nb = audit_break(lo, hi, cl, strict, QB)
            print(f"  [XB] break audit rejects the no-break walk and passes the 1%/1-bar walk "
                  f"({nb} bars checked, {len(loose)} -> {len(strict)} runs)  OK")
        t0 = lo.size // 3
        okp, np_ = audit_phase_free(RC, lo, hi, dict(P, grow="parallel"), t0, cl=cl)
        okc, nc_ = audit_phase_free(RC, lo, hi, dict(P, grow="chain"), t0, cl=cl)
        if not okp:
            raise AssertionError("[I] the parallel rule is path-dependent")
        okb, nb_ = audit_phase_free(RC, lo, hi, dict(QB, grow="parallel"), t0, cl=cl)
        if not okb:
            raise AssertionError("[I] the parallel rule with the break rule on is path-dependent")
        print(f"  [I] parallel + 1% break: identical lines on all {nb_} drawn bars after max "
              f"length + back  OK")
        print(f"  [I] parallel: starting the walk at bar {t0} instead of 0 gives identical lines "
              f"on all {np_} drawn bars after max length  OK; chain: "
              f"{'identical' if okc else 'DIFFERENT'} -- the chain "
              f"{'happens to agree here' if okc else 'inherits its phase, as the principal saw'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
