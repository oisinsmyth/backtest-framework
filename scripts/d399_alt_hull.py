"""D399 ALT -- THE CONVEX HULL ENVELOPE, scored against the principal's hand-drawn lines.

    uv run python scripts/d399_alt_hull.py                 the whole grid
    uv run python scripts/d399_alt_hull.py --selftest      causality + hull invariants
    uv run python scripts/d399_alt_hull.py --null RULE:W   enumerated time-rotation floor

THE IDEA, and it is nearly parameter-free. A support line that is NEVER VIOLATED by the wicks is
exactly an edge of the LOWER CONVEX HULL of the points (i, log low[i]); a resistance line that is
never violated is an edge of the UPPER hull of (i, log high[i]). No `h`, no gradient dead band, no
pivot detector, no regression: the hull IS the set of admissible trendlines and the only question
left is WHICH EDGE of it is "the current line".

CAUSALITY. At bar t the hull is built over a trailing window of bars [max(0, t-W+1), t] and over
nothing else. `--selftest` proves it by scrambling every bar after T0 and asserting the gradient
series at t <= T0 is bit-identical.

WHICH EDGE. The brief's literal reading is "the edge touching the most recent hull vertex". Bar t
is ALWAYS a vertex of its own window's hull, so that reading is the LAST edge -- and the last edge
of a lower hull is the STEEPEST line back from t (its slope is max over i<t of (y_t-y_i)/(t-i)),
which is pinned to the current wick and moves every bar. That is one rule among several and it is
reported, not privileged. The others are the same hull read differently:

    last    (v_{k-1}, t)      the literal reading -- steepest line back from the current bar
    prev    (v_{k-2}, v_{k-1}) the last edge that does NOT touch the current bar
    first   (v_0, v_1)        the TIGHTEST line anchored at the window start: for support,
                              slope = min over i in (a,t] of (y_i - y_a)/(i - a). This is what a
                              human does -- pick a low, rotate the line up until it just touches
                              the next low that keeps every bar above it.
    long    the widest-spanning edge of the hull
    mature  the last edge whose RIGHT endpoint is already >= MIN_RUN bars old
    span    the last edge spanning >= MIN_RUN bars

    break   'first', but the anchor RESETS to bar t whenever the previous bar's line is violated
            by the new wick -- the window is "since the last hull break" rather than fixed W.
            A line is drawn only once the anchor is MIN_RUN bars old ("in those spaces we just
            don't trend"), so the reset is silent, not noisy.

MIN_RUN = 5 and DELTA = 1e-3 are taken from `d399_draw_construction`, not chosen here.

Scored by importing `d399_score_against_drawn.score_side` and `.human_mask` verbatim, so the number
is the same number, not a re-implementation of it.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
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


GT = REPO / "data" / "d399_drawn_ground_truth.json"
RULES = ("last", "prev", "first", "long", "mature", "span")
WGRID = (63, 126, 252)


# ---------------------------------------------------------------- the hull

def hull(y, a, t, side):
    """Monotone chain over the points (i, y[i]) for i in [a, t]. `side` -1 = LOWER hull (support),
    +1 = UPPER hull (resistance). Returns the vertex indices, ascending; H[-1] == t always.

    x is the bar index, so the abscissae are consecutive integers and strictly increasing; the turn
    test is therefore a cross-multiplied slope comparison with both denominators positive. Collinear
    points are POPPED (>=, <=), so a straight run of touches becomes one long edge rather than many
    short ones -- which is what makes 'span' and 'long' mean anything.

    O(t-a) with one list used as the chain stack. No scipy."""
    H = []
    for i in range(a, t + 1):
        yi = y[i]
        if not np.isfinite(yi):
            continue
        while len(H) >= 2:
            i1, i2 = H[-2], H[-1]
            lhs = (y[i2] - y[i1]) * (i - i2)
            rhs = (yi - y[i2]) * (i2 - i1)
            if (lhs >= rhs) if side < 0 else (lhs <= rhs):
                H.pop()
            else:
                break
        H.append(i)
    return H


def edge_slope(y, u, v):
    return (y[v] - y[u]) / (v - u)


def pick_edge(H, y, t, rule, min_run):
    """(u, v) of the chosen hull edge, or None. Every rule reads the SAME hull."""
    k = len(H)
    if k < 2:
        return None
    if rule == "last":
        return H[-2], H[-1]
    if rule == "prev":
        return (H[-3], H[-2]) if k >= 3 else None
    if rule == "first":
        return H[0], H[1]
    if rule == "long":
        j = int(np.argmax(np.diff(H)))
        return H[j], H[j + 1]
    if rule == "mature":
        for j in range(k - 2, -1, -1):
            if H[j + 1] <= t - min_run:
                return H[j], H[j + 1]
        return None
    if rule == "span":
        for j in range(k - 2, -1, -1):
            if H[j + 1] - H[j] >= min_run:
                return H[j], H[j + 1]
        return None
    raise ValueError(rule)


def run_fixed(y, lo_t, hi_t, W, side, rule, min_run):
    """Gradient at every bar in [lo_t, hi_t], from the hull of the trailing W bars. Bar t sees
    y[max(0, t-W+1) .. t] and nothing else."""
    g = np.full(hi_t + 1, np.nan)
    anch = np.full(hi_t + 1, -1, int)
    for t in range(lo_t, hi_t + 1):
        a = max(0, t - W + 1)
        H = hull(y, a, t, side)
        e = pick_edge(H, y, t, rule, min_run)
        if e is None:
            continue
        u, v = e
        g[t] = edge_slope(y, u, v)
        anch[t] = u
    return g, anch


def run_break(y, lo_t, hi_t, W, side, min_run, warm=252):
    """'first', with the anchor RESET at every violation of the previous bar's line.

    The line held at bar t-1 is  y[s] + g*(i - s)  with g the tightest slope from the anchor s over
    [s, t-1]. If the new wick violates it -- low below a support line, high above a resistance line
    -- the anchor is stale and the window restarts AT BAR t. Until the anchor is min_run bars old
    there is no line at all. W caps how long one anchor may live.

    The loop must be warmed from before lo_t or the state at lo_t would depend on where the report
    window happens to start; `warm` bars of burn-in do that, and they are all <= t."""
    n = hi_t + 1
    g = np.full(n, np.nan)
    anch = np.full(n, -1, int)
    s = max(0, lo_t - warm)
    for t in range(s, hi_t + 1):
        if t > s and np.isfinite(g[t - 1]):
            line = y[anch[t - 1]] + g[t - 1] * (t - anch[t - 1])
            hit = (y[t] < line) if side < 0 else (y[t] > line)
            if hit:
                s = t                                  # THE BREAK: history before t stops counting
        if t - s + 1 > W:
            s = t
        if t - s < min_run:                            # anchor too young -> no trend here
            continue
        H = hull(y, s, t, side)
        if len(H) < 2:
            continue
        g[t] = edge_slope(y, H[0], H[1])
        anch[t] = H[0]
    return g, anch


# ---------------------------------------------------------------- gates

def gate(g, mode, delta, min_run, DR):
    if mode == "none":
        return g
    out = g.copy()
    if mode in ("delta", "delta+run"):
        out[~(np.abs(out) > delta)] = np.nan
    if mode == "delta+run":
        st = np.where(np.isfinite(out), np.sign(out), 0).astype(int)
        st = DR.enforce_min_run(st, min_run)
        out[st == 0] = np.nan
    return out


# ---------------------------------------------------------------- driver

def build(y_lo, y_hi, kind, W, rule, start, n, min_run, warm=252):
    side = -1 if kind == "support" else +1
    y = y_lo if kind == "support" else y_hi
    hi_t = start + n - 1
    if rule == "break":
        g, _a = run_break(y, start, hi_t, W, side, min_run, warm=warm)
    else:
        g, _a = run_fixed(y, start, hi_t, W, side, rule, min_run)
    return g[start:start + n]


def score_config(SC, gt, y_lo, y_hi, start, n, W, rule, gmode, delta, min_run, DR):
    cells = {}
    for kind in ("support", "resistance"):
        gw = build(y_lo, y_hi, kind, W, rule, start, n, min_run)
        gw = gate(gw, gmode, delta, min_run, DR)
        hon, hg, _lvl = SC.human_mask(gt["lines"], n, kind)
        both = hon & np.isfinite(gw)
        cells[kind] = SC.score_side(gw, hg, both, int(hon.sum()), delta)
        cells[kind]["g"] = gw
    total = float(np.mean([cells[k]["score"] for k in cells]))
    return total, cells


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--null", metavar="RULE:W:GATE", default=None,
                    help="enumerate the time-rotation null for one configuration")
    ap.add_argument("--out", default=None, help="write the grid to this temp/ json")
    ap.add_argument("--inspect", metavar="RULE:W:GATE", default=None,
                    help="print the fitted line against EACH drawn line, and its anchors")
    a = ap.parse_args()

    DR = _load("d399draw", "d399_draw_construction.py")
    SC = _load("d399score", "d399_score_against_drawn.py")
    UO = _load("d240_uptrend", "run_uptrend_onset.py")
    RP = _load("ragged_panel", "ragged_panel.py")

    DELTA, MIN_RUN = DR.DELTA, DR.MIN_RUN
    gt = json.loads(GT.read_text())
    sym, start, n = gt["symbol"], int(gt["start_bar"]), int(gt["n"])

    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    bars = cleaned[sym]
    lo = np.array([b.bar.low for b in bars], float)
    hi = np.array([b.bar.high for b in bars], float)
    y_lo, y_hi = np.log(lo), np.log(hi)
    assert start + n <= lo.size, "the drawn window runs past the fixture"

    if a.selftest:
        return selftest(y_lo, y_hi, start, n, MIN_RUN)

    if a.inspect:
        rule, W, gmode = a.inspect.split(":")
        W = 10 ** 9 if W == "inf" else int(W)
        return inspect(gt, y_lo, y_hi, start, n, W, rule, gmode, DELTA, MIN_RUN, DR)

    if a.null:
        rule, W, gmode = a.null.split(":")
        W = 10 ** 9 if W == "inf" else int(W)
        return null_floor(SC, gt, y_lo, y_hi, start, n, W, rule, gmode, DELTA, MIN_RUN, DR)

    print(f"\n  {sym} bars {start}-{start+n}  {gt['first_date']} -> {gt['last_date']}")
    print(f"  THE CONVEX HULL ENVELOPE. delta {DELTA:g}, min_run {MIN_RUN}, "
          f"scored by d399_score_against_drawn.score_side\n")
    print(f"  {'rule':>7s} {'W':>5s} {'gate':>9s} | "
          f"{'sup A':>6s} {'sup R':>6s} {'sup S':>6s} | "
          f"{'res A':>6s} {'res R':>6s} {'res S':>6s} | {'SCORE':>6s}")
    print("  " + "-" * 88)

    rows = []
    combos = [(r, W) for r in RULES for W in WGRID]
    combos += [("break", W) for W in (63, 126, 252, 10 ** 9)]
    for rule, W in combos:
        for gmode in ("none", "delta", "delta+run"):
            total, cells = score_config(SC, gt, y_lo, y_hi, start, n, W, rule, gmode,
                                        DELTA, MIN_RUN, DR)
            s, r = cells["support"], cells["resistance"]
            rows.append(dict(rule=rule, W=("inf" if W > 10 ** 8 else W), gate=gmode,
                             sup_agreement=s["agreement"], sup_recall=s["recall"],
                             sup_score=s["score"], sup_overlap=s["overlap_bars"],
                             res_agreement=r["agreement"], res_recall=r["recall"],
                             res_score=r["score"], res_overlap=r["overlap_bars"],
                             SCORE=round(total, 4)))
            wlab = "inf" if W > 10 ** 8 else str(W)
            print(f"  {rule:>7s} {wlab:>5s} {gmode:>9s} | "
                  f"{(s['agreement'] or 0):>6.3f} {s['recall']:>6.3f} {s['score']:>6.3f} | "
                  f"{(r['agreement'] or 0):>6.3f} {r['recall']:>6.3f} {r['score']:>6.3f} | "
                  f"{total:>6.3f}")

    best = max(rows, key=lambda d: d["SCORE"])
    print(f"\n  BEST OF {len(rows)}: {best['rule']} W={best['W']} gate={best['gate']}  "
          f"SCORE {best['SCORE']:.4f}")
    print(f"    support     agreement {best['sup_agreement']} recall {best['sup_recall']} "
          f"({best['sup_overlap']} bars)")
    print(f"    resistance  agreement {best['res_agreement']} recall {best['res_recall']} "
          f"({best['res_overlap']} bars)")
    print(f"\n  A BEST-OF-{len(rows)} IS NOT A RESULT until it clears a floor: "
          f"--null {best['rule']}:{best['W']}:{best['gate']}")

    if a.out:
        p = Path(a.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(dict(symbol=sym, start=start, n=n, delta=DELTA,
                                     min_run=MIN_RUN, rows=rows, best=best), indent=1))
        print(f"  wrote {p}")
    return 0


def inspect(gt, y_lo, y_hi, start, n, W, rule, gmode, delta, min_run, DR):
    """LOOK AT THE OBJECT. Per DRAWN line: what slope the hull actually reports over its bars, how
    many bars it speaks on, what the per-bar agreement is, and which hull edge is doing the work."""
    print(f"\n  {rule} W={W} gate={gmode} -- the fitted gradient against each drawn line\n")
    print(f"  {'kind':>10s} {'bars':>9s} {'g drawn':>10s} {'g fit med':>10s} {'ann fit':>8s} "
          f"{'ann drawn':>9s} {'on':>4s} {'agree':>6s}  anchors")
    for kind, side in (("support", -1), ("resistance", +1)):
        y = y_lo if kind == "support" else y_hi
        hi_t = start + n - 1
        if rule == "break":
            g, anch = run_break(y, start, hi_t, W, side, min_run)
        else:
            g, anch = run_fixed(y, start, hi_t, W, side, rule, min_run)
        gw = gate(g[start:start + n], gmode, delta, min_run, DR)
        aw = anch[start:start + n]
        for L in gt["lines"]:
            if L["kind"] != kind:
                continue
            i0, i1, gd = int(L["i0"]), int(L["i1"]), float(L["g_per_bar"])
            seg = gw[i0:i1 + 1]
            fin = np.isfinite(seg)
            if not fin.any():
                print(f"  {kind:>10s} {i0:>4d}-{i1:<4d}  {gd:>+10.5f}  (silent everywhere)")
                continue
            med = float(np.median(seg[fin]))
            rel = np.abs(seg[fin] - gd) / max(abs(gd), delta)
            ag = float(np.clip(1 - rel, 0, None).mean())
            anc = sorted(set(int(v) for v in aw[i0:i1 + 1] if v >= 0))
            atxt = ",".join(str(v - start) for v in anc[:6]) + ("..." if len(anc) > 6 else "")
            print(f"  {kind:>10s} {i0:>4d}-{i1:<4d} {gd:>+10.5f} {med:>+10.5f} "
                  f"{np.expm1(252*med):>+8.2f} {np.expm1(252*gd):>+9.2f} {int(fin.sum()):>4d} "
                  f"{ag:>6.3f}  [{atxt}]")
    return 0


def null_floor(SC, gt, y_lo, y_hi, start, n, W, rule, gmode, delta, min_run, DR):
    """THE ENUMERATED TIME ROTATION. The construction's own gradient series is a single market-level
    series over n bars, so its rotation group is finite and small (n-1 offsets): enumerate it and
    the p95 has a bootstrap SE of exactly zero (D373's rule, CLAUDE.md). What is randomised is WHEN
    the construction speaks relative to the drawn lines, not what it says -- so the null holds the
    slope distribution, the silence pattern and the segment structure fixed."""
    total, cells = score_config(SC, gt, y_lo, y_hi, start, n, W, rule, gmode, delta, min_run, DR)
    scores = []
    for off in range(1, n):
        parts = []
        for kind in ("support", "resistance"):
            gw = np.roll(cells[kind]["g"], off)
            hon, hg, _l = SC.human_mask(gt["lines"], n, kind)
            both = hon & np.isfinite(gw)
            parts.append(SC.score_side(gw, hg, both, int(hon.sum()), delta)["score"])
        scores.append(float(np.mean(parts)))
    s = np.array(scores)
    off = np.arange(1, n)
    far = np.minimum(off, n - off) >= 21        # a rotation of a few bars is nearly the treatment
    print(f"\n  {rule} W={W} gate={gmode}: SCORE {total:.4f}")
    print(f"  ENUMERATED time rotation, all {s.size} offsets (SE of the p95 is exactly 0):")
    for lab, sel in (("all offsets", np.ones(s.size, bool)), ("|offset| >= 21 bars", far)):
        z = s[sel]
        print(f"    {lab:>20s}  n {z.size:>3d}  p50 {np.percentile(z, 50):.4f}  "
              f"p95 {np.percentile(z, 95):.4f}  max {z.max():.4f}  "
              f"share >= observed {float((z >= total).mean()):.4f}  "
              f"margin {total - float(np.percentile(z, 95)):+.4f}")
    return 0


def selftest(y_lo, y_hi, start, n, min_run) -> int:
    """Three checks, and each is made to FAIL first so it is not a self-test that cannot fail."""
    rng = np.random.default_rng(0)
    ok = True

    # 1. HULL INVARIANT: lower-hull slopes strictly increase, upper-hull slopes strictly decrease,
    #    and every point in the window is on the correct side of every edge.
    for side, y in ((-1, y_lo), (+1, y_hi)):
        t = start + 137
        H = hull(y, t - 251, t, side)
        sl = np.array([edge_slope(y, H[j], H[j + 1]) for j in range(len(H) - 1)])
        assert H[-1] == t, "the current bar must be a vertex of its own window's hull"
        assert (np.diff(sl) > 0).all() if side < 0 else (np.diff(sl) < 0).all(), "hull not convex"
        for j in range(len(H) - 1):
            u, v = H[j], H[j + 1]
            g0 = edge_slope(y, u, v)
            line = y[u] + g0 * (np.arange(t - 251, t + 1) - u)
            viol = (y[t - 251:t + 1] < line - 1e-12) if side < 0 else (y[t - 251:t + 1] > line + 1e-12)
            assert not viol.any(), "a hull edge is violated by a bar in its own window"
    print("  [1] hull invariants hold (convex chain; no edge violated inside its window)")
    yb = y_lo.copy(); yb[start + 100] -= 5.0                 # a deliberate break
    try:
        H = hull(yb, start + 50, start + 137, -1)
        sl = np.array([edge_slope(yb, H[j], H[j + 1]) for j in range(len(H) - 1)])
        # the broken point MUST have become a vertex; if it has not, the hull is not a hull
        assert (start + 100) in H
        print("      [X] the assertion reads the vertex set: a bar driven 5 log-units below the "
              "chain becomes a hull vertex, as it must")
    except AssertionError:
        ok = False
        print("      [X] FAILED: the hull missed a point far below its own chain")

    # 2. CAUSALITY. Scramble every bar after T0 and demand the gradients at t <= T0 be IDENTICAL.
    n_case = 0
    for T0 in (start + 20, start + 150, start + n - 30):
        for kind, side, y in (("support", -1, y_lo), ("resistance", +1, y_hi)):
            yb = y.copy()
            yb[T0 + 1:] = yb[T0 + 1:] + rng.normal(0, 2.0, yb.size - T0 - 1)
            for W in (63, 126, 252):
                for rule in RULES + ("break",):
                    def f(yy, rule=rule, side=side, W=W):
                        if rule == "break":
                            return run_break(yy, start, start + n - 1, W, side, min_run)[0]
                        return run_fixed(yy, start, start + n - 1, W, side, rule, min_run)[0]
                    a0 = f(y)[start:T0 + 1]
                    a1 = f(yb)[start:T0 + 1]
                    n_case += 1
                    if not np.array_equal(np.nan_to_num(a0, nan=-999.0),
                                          np.nan_to_num(a1, nan=-999.0)):
                        ok = False
                        print(f"      LEAK: {kind}/{rule}/W={W}/T0={T0-start} changed at t <= T0 "
                              f"when the FUTURE was scrambled")
    print(f"  [2] causal: scrambling every bar after T0 leaves g[t<=T0] bit-identical -- "
          f"{n_case} cases (3 T0 x 2 sides x 3 W x 7 rules)")
    yleak = y_lo.copy()
    g_leak = np.full(start + n, np.nan)
    for t in range(start, start + n):                        # a deliberately LEAKY construction
        g_leak[t] = edge_slope(yleak, t, min(t + 5, yleak.size - 1))
    yb = yleak.copy(); yb[T0 + 1:] += 2.0
    g_leak2 = np.full(start + n, np.nan)
    for t in range(start, start + n):
        g_leak2[t] = edge_slope(yb, t, min(t + 5, yb.size - 1))
    if np.array_equal(g_leak[start:T0 + 1], g_leak2[start:T0 + 1]):
        ok = False
        print("      [X] FAILED: the leak probe did not detect a construction that reads t+5")
    else:
        print("      [X] the probe reads the gradient itself: a construction that peeks at t+5 IS "
              "caught by the same test")

    # 3. THE RULES ARE DIFFERENT OBJECTS -- a grid of aliases would be a fake sweep.
    gs = {r: run_fixed(y_lo, start, start + n - 1, 126, -1, r, min_run)[0][start:] for r in RULES}
    dup = [(p, q) for i, p in enumerate(RULES) for q in RULES[i + 1:]
           if np.array_equal(np.nan_to_num(gs[p], nan=-9.0), np.nan_to_num(gs[q], nan=-9.0))]
    assert not dup, f"these rules are the same series: {dup}"
    print(f"  [3] the {len(RULES)} fixed-window rules are {len(RULES)} distinct series")
    print("\n  SELFTEST " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
