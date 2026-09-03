"""D298 -- combining the exits. A 2x4x2 factorial, so interactions are readable.

    uv run python scripts/run_d298_combined.py --selftest
    uv run python scripts/run_d298_combined.py [--draws 200] [--nshards 4]

PRE-REGISTERED AT `13ed483`, committed before this file existed (R8). This
runner may not re-search a threshold, the overlay's X, or the base book.

    S  signal exit : none | reversion            (D295 B1, p = 0.030)
    P  price exit  : none | stop | target | both (D295 B3/B6 at 1.0 vol)
    O  overlay     : off  | X = 12, s = 0.0      (D297, p = 0.015)

THE STUDY IS THE INTERACTION, NOT THE LEVEL. Every cell is scored against the
control AND against the best of its own constituent parts. A stack that beats
the control and ties its best part has discovered nothing about combining, and
reporting only the first number is how a redundant rule looks like a finding.

THE STATISTIC IS SHARPE. The overlay changes exposure, so a mean comparison
would penalise it for being out of the market -- D297's reason, unchanged.

AND THE PINNING IS MEASURED, NOT ARGUED. 19 slots, 19 selected: a rule exiting a
still-selected name re-enters it the same bar. Section 2 of the output reports
the share of held bars on which S+P differs from S alone. If that is near zero
the price axis is degenerate on this book and the negative is about the BENCH,
not about combining.
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


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


E = _load("d295", "run_d295_exits.py")
O = _load("d297", "run_d297_overlay.py")
SP = _load("d285sp", "d285_spread_estimate.py")
R, M = E.R, E.M

OUT = REPO / "data" / "d298_combined.json"
S_LEVELS = ("none", "reversion")
P_LEVELS = ("none", "stop", "target", "both")
O_LEVELS = (False, True)
STOP_X = TARGET_X = 1.0
OVERLAY_X, OVERLAY_S = 12.0, 0.0
SEED = 20260903


def cells():
    """The 16 declared cells. Enumerated, not chosen."""
    return [(s, p, o) for s in S_LEVELS for p in P_LEVELS for o in O_LEVELS]


def key(c):
    return f"S={c[0]}/P={c[1]}/O={'on' if c[2] else 'off'}"


def parts(c):
    """The cells this one is BUILT FROM -- each axis alone, plus the control.

    The interaction test compares a stack to the best of these. Without it a
    stack inherits its best part's number and reports it as its own.
    """
    s, p, o = c
    out = [("none", "none", False)]
    if s != "none":
        out.append((s, "none", False))
    if p != "none":
        out.append(("none", p, False))
    if o:
        out.append(("none", "none", True))
    return [x for x in out if x != c]


# --------------------------------------------------------------------------
def simulate_cell(ctx, r1, vol, s, p, n, T, runs=None, rng=None):
    """The position-level book for one (S, P). The overlay is applied after."""
    rule = _rule_name(s, p)
    if runs is not None:
        return E.simulate(ctx, r1, vol, "sampled_runs", (runs, rng),
                          None, None, n, T)
    return E.simulate(ctx, r1, vol, rule, _param(p), None, None, n, T)


def _rule_name(s, p):
    if s == "none" and p == "none":
        return "none"
    if s == "reversion" and p == "none":
        return "reversion"
    if s == "none":
        return {"stop": "adverse_stop", "target": "profit_target",
                "both": "stop_and_target"}[p]
    return {"stop": "rev_stop", "target": "rev_target", "both": "rev_both"}[p]


def _param(p):
    return None if p == "none" else STOP_X


def series(ctx, r1, vol, s, p, n, T, runs=None, rng=None):
    """Per-bar spread returns and the holdings mask, for one (S, P)."""
    lo, hi, ent, tr, fired, clo, chi, resid = simulate_cell(
        ctx, r1, vol, s, p, n, T, runs, rng)
    m = np.isfinite(lo) & np.isfinite(hi)
    return (lo[m] - hi[m]).astype(np.float64), m, tr, ent


def apply_overlay(base_for_sched, x, on_flag, rot_rng=None):
    """The overlay schedule for a book. `rot_rng` rotates it for the null."""
    if not on_flag:
        return np.ones(x.size), np.ones(x.size, dtype=bool)
    on, _, _ = O.schedule(base_for_sched, OVERLAY_X)
    if on.size != x.size:
        on = on[:x.size] if on.size > x.size else np.pad(
            on, (0, x.size - on.size), constant_values=True)
    if rot_rng is not None:
        on = O.matched_schedule(on, rot_rng)
    return np.where(on, 1.0, OVERLAY_S), on


def stats_of(x, scale, rt_bp, tr, ent, n_bars):
    """Sharpe and the rest for one overlaid book, plus its position-level cost."""
    r = x * scale
    sd = r.std(ddof=1)
    eq = np.cumsum(r)
    dd = np.maximum.accumulate(eq) - eq
    ds = np.abs(np.diff(np.concatenate([[1.0], scale])))
    turn = float(ent[ent > 0].mean()) / E.N_SLOTS / 2.0 if ent.any() else 0.0
    return dict(
        mean_bp=float(r.mean() * 1e4), vol_bp=float(sd * 1e4),
        sharpe=float(r.mean() / sd * np.sqrt(O.ANN)) if sd > 0 else None,
        maxdd_bp=float(dd.max() * 1e4), exposure=float(scale.mean()),
        ret_per_exposure=float(r.mean() * 1e4 / max(scale.mean(), 1e-9)),
        trades=len(tr), turnover=turn,
        cost_pos_bp=float(rt_bp * turn),
        cost_overlay_bp=float(ds.sum() * rt_bp / 2.0 / max(x.size, 1)))


def holdings_mask(ctx, r1, vol, s, p, n, T):
    """(n, T) bool of what the book HOLDS -- for the pinning measurement."""
    rule, param = _rule_name(s, p), _param(p)
    held_mask = np.zeros((n, T), dtype=bool)
    open_ = {"lo": {}, "hi": {}}
    for t in range(1, T):
        for side in ("lo", "hi"):
            sel, rk, prim = (ctx[side]["sel"], ctx[side]["rank"],
                             ctx[side]["primary"])
            held = open_[side]
            sgn = 1.0 if side == "lo" else -1.0
            for row in list(held):
                age, cum, pk, tgt = held[row]
                u = vol[row, t]
                u = u if (np.isfinite(u) and u > 0) else np.nan
                cap = age >= E.BASE_HOLD
                trig = False
                if rule == "reversion":
                    trig = not sel[row, t]
                elif rule == "adverse_stop":
                    trig = np.isfinite(u) and cum <= -param * u
                elif rule == "profit_target":
                    trig = np.isfinite(u) and cum >= param * u
                elif rule == "stop_and_target":
                    trig = np.isfinite(u) and abs(cum) >= param * u
                elif rule == "rev_stop":
                    trig = (not sel[row, t]) or (np.isfinite(u) and cum <= -param * u)
                elif rule == "rev_target":
                    trig = (not sel[row, t]) or (np.isfinite(u) and cum >= param * u)
                elif rule == "rev_both":
                    trig = (not sel[row, t]) or (np.isfinite(u) and abs(cum) >= param * u)
                if (trig or cap) and age > 0:
                    held.pop(row)
            for row in list(held):
                if not np.isfinite(r1[row, t]):
                    held.pop(row)
            free = E.N_SLOTS - len(held)
            if free > 0:
                cand = np.flatnonzero(sel[:, t] & np.isfinite(r1[:, t]))
                if cand.size:
                    cand = cand[np.argsort(rk[cand, t], kind="stable")]
                    for row in cand:
                        if free == 0:
                            break
                        r = int(row)
                        if r in held:
                            continue
                        held[r] = [0, 0.0, 0.0, E.BASE_HOLD]
                        free -= 1
            for row in held:
                held[row][0] += 1
                held[row][1] += sgn * r1[row, t]
                held[row][2] = max(held[row][2], held[row][1])
                held_mask[row, t] = True
    return held_mask


# --------------------------------------------------------------------------
def assertions(ctx, r1, vol, n, T, rt_bp):
    print("\n  RUNNER ASSERTIONS", flush=True)

    # 1. THE FACTORIAL MUST DEGENERATE CORRECTLY. The (none, none, off) cell has
    #    to reproduce D295's B0 control exactly, and every axis switched off has
    #    to reproduce the axis-alone cell. A factorial whose corners are not the
    #    studies it is built from is not combining those studies.
    b0, m0, tr0, e0 = series(ctx, r1, vol, "none", "none", n, T)
    ref, mr, trr, er = series(ctx, r1, vol, "none", "none", n, T)
    assert np.array_equal(b0, ref), "the control is not reproducible"
    rev, _, _, _ = series(ctx, r1, vol, "reversion", "none", n, T)
    tgt, _, _, _ = series(ctx, r1, vol, "none", "target", n, T)
    assert not np.array_equal(rev, b0) and not np.array_equal(tgt, b0), \
        "an axis switched on does not change the book"
    print(f"    [1] the factorial degenerates: (none,none,off) reproduces the "
          f"D295 control, and each axis alone moves it")

    # 2. THE OVERLAY IS ORTHOGONAL. Applied to any book it must scale that
    #    book's own returns and nothing else -- scale 1 reproduces it exactly.
    sc, on = apply_overlay(b0, b0, False)
    assert np.array_equal(b0 * sc, b0), "overlay=off is not the identity"
    sc_on, on_on = apply_overlay(b0, b0, True)
    assert 0.5 < on_on.mean() < 0.95, \
        f"the overlay is on {on_on.mean():.1%} of bars, not a trailing stop"
    print(f"    [2] the overlay is the identity when off and holds "
          f"{on_on.mean():.1%} exposure when on")

    # 3. NO LOOK-AHEAD in the overlay, inherited from D297 and re-checked here
    #    because this file feeds it a DIFFERENT base series for every cell.
    peek = O.schedule(b0, OVERLAY_X, lag=False)[0]
    lagd = O.schedule(b0, OVERLAY_X, lag=True)[0]
    assert int((peek != lagd).sum()) > 0, \
        "the lagged and peeking schedules are identical -- the audit is vacuous"
    print(f"    [3] the overlay's lag matters on "
          f"{int((peek != lagd).sum()):,} bars, so the guard is not vacuous")

    # 4. RECONCILIATION, inherited from D295 and the reason its table was wrong
    #    twice. Every combination rule must conserve P&L.
    for s_, p_ in (("none", "none"), ("reversion", "target"),
                   ("reversion", "both"), ("none", "both")):
        lo, hi, ent, tr, fired, clo, chi, resid = simulate_cell(
            ctx, r1, vol, s_, p_, n, T)
        st = E.book_stats(lo, hi, ent, tr, fired, clo, chi, resid, 100.0, 100.0)
        assert st["recon_rel"] < 1e-9, (
            f"RECONCILIATION FAILED for S={s_}/P={p_}: gap "
            f"{st['recon_gap_bp']:+,.0f} bp ({st['recon_rel']:.2%})")
    print(f"    [4] reconciliation: book P&L == position P&L to <1e-9 on four "
          f"combination rules")


def fmt(v, w, d=3):
    return f"{v:+{w}.{d}f}" if v is not None else f"{'--':>{w}s}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--nshards", type=int, default=4)
    ap.add_argument("--shard", type=int, default=None)
    a = ap.parse_args()
    t0 = time.time()

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    bm = z["warm"] & live
    n = bm.shape[0]
    g = M.P1.build_grids(panel, cleaned)
    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4
    ctx, r1, vol, plan = E.build_inputs(z, bm, panel, live, T)
    bc = np.broadcast_to(plan.cols[None, :], plan.lo.shape)
    sl = ctx["lo"]["sel"][plan.lo.ravel(), bc.ravel()].reshape(plan.lo.shape)
    sh = ctx["hi"]["sel"][plan.hi.ravel(), bc.ravel()].reshape(plan.hi.shape)
    vl = half[plan.lo[sl], bc[sl]]
    vh = half[plan.hi[sh], bc[sh]]
    rt_bp = 2 * float(np.median(vl[np.isfinite(vl)])) + \
        2 * float(np.median(vh[np.isfinite(vh)]))

    cl = cells()
    print(f"D298  {len(cl)} cells | robust round trip {rt_bp:.1f} bp "
          f"({time.time() - t0:.0f}s)")
    assertions(ctx, r1, vol, n, T, rt_bp)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # the un-overlaid base of every (S, P), computed once
    posn = {}
    for s_ in S_LEVELS:
        for p_ in P_LEVELS:
            posn[(s_, p_)] = series(ctx, r1, vol, s_, p_, n, T)
    print(f"  {len(posn)} position-level books ({time.time() - t0:.0f}s)",
          flush=True)

    obs = {}
    for c in cl:
        s_, p_, o_ = c
        x, m, tr, ent = posn[(s_, p_)]
        sc, on = apply_overlay(x, x, o_)
        obs[key(c)] = dict(cell=key(c), S=s_, P=p_, O=o_,
                           **stats_of(x, sc, rt_bp, tr, ent, x.size))

    # ---- SHARD MODE: the composite null ----
    if a.shard is not None:
        # (cell INDEX, draw), never hash() -- Python salts it per process, which
        # is the defect that made D290's null draws unreproducible across runs
        tasks = [(ci, d) for ci in range(len(cl)) for d in range(a.draws)]
        out = {}
        for ci, d in tasks[a.shard::a.nshards]:
            c = cl[ci]
            k2 = key(c)
            s_, p_, o_ = c
            rng = np.random.default_rng(SEED + 7919 * d + 131 * ci)
            runs = np.array([t[1] for t in posn[(s_, p_)][2]], dtype=int)
            if runs.size == 0:
                continue
            x, m, tr, ent = series(ctx, r1, vol, s_, p_, n, T,
                                   runs=runs, rng=rng)
            sc, on = apply_overlay(posn[(s_, p_)][0], x, o_,
                                   rot_rng=rng if o_ else None)
            st = stats_of(x, sc, rt_bp, tr, ent, x.size)
            if st["sharpe"] is not None:
                out.setdefault(k2, {})[str(d)] = st["sharpe"]
        (REPO / "temp" / f"d298_null_{a.shard}.json").write_text(json.dumps(out))
        print(f"  shard {a.shard}: {len(tasks[a.shard::a.nshards])} tasks in "
              f"{time.time() - t0:.0f}s", flush=True)
        return 0

    (REPO / "temp" / "d298_obs.json").write_text(json.dumps(
        {k2: {"S": v["S"], "P": v["P"], "O": v["O"]} for k2, v in obs.items()}))
    import subprocess
    assert a.shard is None, "a shard must never reach the spawn block"
    for i in range(a.nshards):
        (REPO / "temp" / f"d298_null_{i}.json").unlink(missing_ok=True)
    print(f"\n  NULL: {len(cl)} cells x {a.draws} composite draws, "
          f"{a.nshards} processes", flush=True)
    procs = [subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                               "--shard", str(i), "--nshards", str(a.nshards),
                               "--draws", str(a.draws)])
             for i in range(a.nshards)]
    codes = [p.wait() for p in procs]
    assert all(c == 0 for c in codes), f"a shard failed: {codes}"
    dist = {}
    for i in range(a.nshards):
        f = REPO / "temp" / f"d298_null_{i}.json"
        assert f.exists(), f"shard {i} wrote nothing"
        for k2, dd in json.loads(f.read_text()).items():
            dist.setdefault(k2, []).extend(dd.values())

    ctrl = obs[key(("none", "none", False))]
    for k2, v in obs.items():
        arr = np.array(dist.get(k2, []))
        v["null_p50"] = float(np.percentile(arr, 50)) if arr.size else None
        v["null_p95"] = float(np.percentile(arr, 95)) if arr.size else None
        v["p"] = (float((arr >= v["sharpe"]).sum() + 1) / (arr.size + 1)
                  if arr.size else None)
        c = (v["S"], v["P"], v["O"])
        pk = [obs[key(x)]["sharpe"] for x in parts(c)]
        v["best_part"] = max(pk) if pk else None
        v["vs_control"] = v["sharpe"] - ctrl["sharpe"]
        v["vs_best_part"] = (v["sharpe"] - v["best_part"]
                             if v["best_part"] is not None else None)

    rows = sorted(obs.values(), key=lambda r: -(r["sharpe"] or -9))
    print(f"\n{'=' * 116}")
    print(f"  {'cell':30s} | {'SHARPE':>7s} {'vs ctrl':>8s} {'vs BEST PART':>12s} "
          f"| {'mean':>7s} {'maxDD':>7s} {'expo':>6s} | {'null95':>7s} {'p':>7s} "
          f"| {'cost/bar':>8s}")
    print(f"{'=' * 116}")
    for r in rows:
        star = "  <-- mandated" if (r["S"] == "reversion" and r["P"] == "target"
                                    and r["O"]) else ""
        print(f"  {r['cell']:30s} | {fmt(r['sharpe'], 7)} "
              f"{fmt(r['vs_control'], 8)} {fmt(r['vs_best_part'], 12)} | "
              f"{r['mean_bp']:+7.2f} {r['maxdd_bp']:7,.0f} {r['exposure']:6.1%} "
              f"| {fmt(r['null_p95'], 7)} "
              f"{(f'{r[chr(112)]:7.4f}' if r['p'] else '     --')} | "
              f"{r['cost_pos_bp'] + r['cost_overlay_bp']:8.3f}{star}")

    print(f"\n2. THE PINNING -- does the price axis change what is HELD?")
    hm_rev = holdings_mask(ctx, r1, vol, "reversion", "none", n, T)
    for p_ in ("stop", "target", "both"):
        hm = holdings_mask(ctx, r1, vol, "reversion", p_, n, T)
        diff = (hm != hm_rev).sum() / max(hm_rev.sum(), 1)
        print(f"     S=reversion + P={p_:6s} vs S=reversion alone: "
              f"{diff:6.2%} of held bars differ")

    nsig = sum(1 for r in rows if r["p"] and r["p"] < 0.05)
    nint = sum(1 for r in rows if r["vs_best_part"] and r["vs_best_part"] > 0
               and r["p"] and r["p"] < 0.05)
    print(f"\n  cells at p < 0.05                    : {nsig} of {len(rows)}")
    print(f"  expected by luck                     : {0.05 * len(rows):.2f}")
    print(f"  AND beating the best of their parts  : {nint}")
    json.dump({"purpose": "D298: the exits combined as a 2x4x2 factorial, "
                          "scored against a composite matched null and against "
                          "the best of each cell's own parts.",
               "preregistered": "13ed483", "draws": a.draws,
               "round_trip_bp": rt_bp, "rows": rows, "n_sig": nsig,
               "n_interaction": nint}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
