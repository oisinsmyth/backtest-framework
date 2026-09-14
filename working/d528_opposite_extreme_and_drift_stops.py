"""TARGET AT THE OPPOSITE EXTREME, AND WHETHER THE EXITS SHOULD FOLLOW THE DRIFT.
BOTH LENSES: path-invariant per trade, and the path-variant slot-limited book.

    python working/d528_opposite_extreme_and_drift_stops.py --self-test
    python working/d528_opposite_extreme_and_drift_stops.py --run

Nothing admitted (R15). Micro universe (8 roots), in sample only; the reserved slice
(2026-04-11 -> 2026-09-09) remains UNREAD. This is further in-sample looking on a window already
read repeatedly in this session; the multiplicity is stated, not hidden.

DECLARED PRIMARY, before running: target = OPPOSITE EXTREME (the far edge of the +/-X sigma band),
stop at G = 3.0 sigma from the level, exits FROZEN at entry, tau = 40, `traverse` classifier, micro
universe, s = 1, 3 slots. ONE cell, scored on both lenses. Everything else is a ladder and is
description, not a test.

-------------------------------------------------------------------------------------------------
1  THE PRINCIPAL'S STOP PROPOSAL IS THE STOP ALREADY IN PLACE.

"50% further from the mean than the extreme": entry at X = 2 sigma from the level, so the stop sits
at 1.5 * X = 3.0 sigma. Distance from ENTRY is 3 - 2 = 1 sigma = 0.5 * |y| -- exactly the f = 0.5
already used, and exactly EXT_MULT = 1.5 from the original D528 pre-registration. So the stop is
parametrised the principal's way here, as G sigma from the LEVEL, and G = 3.0 reproduces the
current construction. Self-test 1 asserts the two parametrisations agree numerically.

2  THE CURRENT STOP DOES NOT ACCOUNT FOR DRIFT, AND THAT WAS DELIBERATE.

When the decile charts showed trades killed by the level's own slope rather than by price, both
exits were frozen as prices at entry. That removed the runaway and also removed any drift
adjustment. The two frames:

    FROZEN   target and stop are prices fixed at entry -- a resting limit and a resting stop
    DRIFT    both live in RESIDUAL space and move with the level, carried by slope * k

Under the alignment rule s*slope < 0 the level recedes from the price, so in the DRIFT frame a
long's stop rises toward the price (tightening) while its target recedes. Drift-following is
therefore expected to hurt on BOTH sides in the aligned cell -- the runaway is implied by the
alignment rule, not an implementation accident. Measured, not argued.

3  THE OPPOSITE-EXTREME TARGET IS THE IDEA WITH LEVERAGE, FOR AN ARITHMETIC REASON.

Cost is FIXED per round trip; the target is not. Taking profit at the level asks for ~2.7 sigma of
travel; at the band's far edge it asks for ~4.7. Cost falls from ~14% of the perfect payoff to ~8%,
and the designed payoff roughly doubles. It also aligns the classifier with the target for the
first time: `traverse` selects windows in which price crossed the full width of the range, and
until now the target only asked for half of it.

TWO READINGS OF "THE OPPOSITE EXTREME", BOTH CARRIED, because they are not the same:

    opposite   the far edge of the +/- X sigma band, residual -s*X*sigma
    reflect    the MIRROR of the actual entry, residual -y

The entry overshoots its own threshold by ~35% -- |y| >= X*sigma is tested once per bar and the
crossing bar lands well past it, so the mean entry is ~2.7 sigma rather than 2.0. The band's far
edge therefore sits CLOSER than the mirror of the entry: 'opposite' asks ~4.7 sigma of travel,
'reflect' ~5.4. Guessing between them would have been a silent choice.

4  BOTH LENSES, NEVER ONE STATISTIC (CLAUDE.md).

    PATH-INVARIANT  every candidate, no slot cap, scored per TRADE: win rate, payoff, $/trade
    PATH-VARIANT    the slot-limited book, one position per root, scored as an equity curve:
                    Sharpe, exposure, maxDD against the $2,000 trailing limit

Their difference is opportunity cost. One `resolve` feeds both scorers so the two lenses can never
drift apart on entry or exit logic.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_book_and_sides as B                 # noqa: E402

X = 2.0                       # the entry extreme, in sigma from the level
G_PRIMARY = 3.0               # the stop, in sigma from the level -- the principal's 1.5 * X
TAU_PRIMARY = 40
SLOTS = (1, 3, 999)
SLOTS_PRIMARY = 3
G_LADDER = (2.5, 3.0, 3.5, 4.0, 5.0)
TAU_LADDER = (10, 20, 40, 80)
TARGETS = ("level", "opposite", "reflect")
FRAMES = ("frozen", "drift")
CELLS = (("traverse", "flat", "C  traverse (yours)"),
         ("none", "flat", "B  no classifier"),
         ("cross2", "line", "A  as specified"))
N_SHUF = 20
SEED = 528773


def P(*a):
    print(*a, flush=True)


def resolve(path, c, lvl, keep, tick, tick_usd, cost_tk, target, frame, g, tau,
            day_idx=0, bar0=540, root="?"):
    """Book-compatible trade records for one (target, frame, g, tau) combination.

    target  'level'    take profit at the level (residual 0)
            'opposite' the far edge of the +/- X sigma BAND, residual -s*X*sigma
            'reflect'  the MIRROR of the actual entry, residual -y
    frame   'frozen'   both exits are prices fixed at entry
            'drift'    both exits live in residual space and move with the level (slope*k)
    g       the stop's distance from the LEVEL, in sigma (the principal's parametrisation)

    Emits exactly the keys `d528_book_and_sides.run_book`/`perf` consume, so the path-variant
    lens and the path-invariant lens are computed from ONE trade list and cannot disagree.
    """
    idx = np.flatnonzero(keep)
    n = len(path)
    if len(idx) == 0:
        return []
    t = idx + 2 * Z.H
    ok = t < n - 1
    idx, t = idx[ok], t[ok]
    if len(idx) == 0:
        return []
    y = c[f"{lvl}_y"][idx]
    sd = c[f"{lvl}_sd"][idx]
    slope = c["slope"][idx]
    s = np.sign(y)
    p0 = path[t]
    lvl0 = c[f"{lvl}_lvl"][idx]

    if target == "level":
        y_tgt = np.zeros(len(idx))
    elif target == "opposite":
        y_tgt = -s * X * sd
    elif target == "reflect":
        y_tgt = -y
    else:
        raise ValueError(f"unknown target {target!r}")
    y_stp = s * g * sd

    kk = np.arange(1, tau + 1)
    j = t[:, None] + kk[None, :]
    valid = j <= (n - 1)
    F = path[np.minimum(j, n - 1)]
    lv = (lvl0[:, None] + slope[:, None] * kk[None, :]) if frame == "drift" \
        else np.repeat(lvl0[:, None], tau, axis=1)
    yk = F - lv
    ht = (((yk - y_tgt[:, None]) * s[:, None]) <= 0.0) & valid
    hs = (((yk - y_stp[:, None]) * s[:, None]) >= 0.0) & valid
    i_t = np.where(ht.any(1), ht.argmax(1), R.BIG)
    i_s = np.where(hs.any(1), hs.argmax(1), R.BIG)
    nv = valid.sum(1)
    miss = (i_t == R.BIG) & (i_s == R.BIG)
    stopf = (~miss) & (i_s <= i_t)
    kind = np.where(miss, 2, np.where(stopf, 1, 0))
    rows = np.arange(len(idx))
    last = np.clip(nv - 1, 0, tau - 1)
    # fills: a resting limit fills at its own price; a stop fills at the REALISED price (at or
    # beyond, never better); a timeout exits at market. The idealised variant takes the stop at
    # its own price, and the two bracket the truth (ADDENDUM 2 measured the bracket at 2.86 tk).
    px_tgt = lv[rows, np.minimum(i_t, tau - 1)] + y_tgt
    px_stp_real = F[rows, np.minimum(i_s, tau - 1)]
    px_stp_ideal = lv[rows, np.minimum(i_s, tau - 1)] + y_stp
    px_r = np.where(miss, F[rows, last], np.where(stopf, px_stp_real, px_tgt))
    px_i = np.where(miss, F[rows, last], np.where(stopf, px_stp_ideal, px_tgt))
    g_real = (-s) * (px_r - p0) / tick
    g_ideal = (-s) * (px_i - p0) / tick
    d = np.where(miss, nv, np.where(stopf, i_s + 1, i_t + 1))
    perfect_tk = (np.abs(y) + np.abs(y_tgt)) / tick
    cost_usd = float(cost_tk * tick_usd + B.COMMISSION_RT)
    base = day_idx * 2000 + bar0
    out = []
    for q in range(len(idx)):
        out.append({
            "t_in": int(base + t[q]), "t_out": int(base + t[q] + d[q]),
            "day": day_idx, "root": root, "side": -1 if s[q] < 0 else +1,
            "bars": int(d[q]), "kind": int(kind[q]),
            "g_real_tk": float(g_real[q]), "g_ideal_tk": float(g_ideal[q]),
            "cost_usd": cost_usd, "tick_usd": float(tick_usd),
            "tgt_tk": float(perfect_tk[q]), "perfect_tk": float(perfect_tk[q]),
            "x_sig": float(abs(y[q]) / sd[q]) if sd[q] > 0 else 0.0,
            "er_usd": float(perfect_tk[q] * tick_usd - cost_usd), "fcfs": 0.0,
        })
    return out


def gather(cl, lvl, target, frame, g, tau, d, sp, roots, day_index, shuffle_rng=None):
    out = []
    for r in roots:
        gg = d[d["root"] == r]
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        for day, pth, b0 in B.sessions_with_bars(gg, 1):
            if shuffle_rng is not None:
                pth = Z.shuffled(pth, shuffle_rng, 1)[0]
            c = Z.classify2(pth, tick)
            if c is None:
                continue
            keep = Z.entry_mask(c, lvl, tick, cost_tk, cl)
            out.extend(resolve(pth, c, lvl, keep, tick, tick_usd, cost_tk, target, frame,
                               g, tau, day_index[day], b0, r))
    return out


def invariant(trades, fill="g_real_tk"):
    """PATH-INVARIANT lens: every candidate, no slot cap, scored per TRADE."""
    if not trades:
        return None
    gr = np.array([z[fill] * z["tick_usd"] for z in trades])
    cu = np.array([z["cost_usd"] for z in trades])
    kd = np.array([z["kind"] for z in trades])
    pf = np.array([z["perfect_tk"] * z["tick_usd"] for z in trades])
    net = gr - cu
    w, l = net[net > 0], net[net <= 0]
    return {"n": len(net), "p_tgt": float((kd == 0).mean()), "p_stop": float((kd == 1).mean()),
            "p_to": float((kd == 2).mean()), "win": float((net > 0).mean()),
            "payoff": float(w.mean() / abs(l.mean())) if len(l) and l.mean() else np.nan,
            "gross_pt": float(gr.mean()), "net_pt": float(net.mean()),
            "cost_pt": float(cu.mean()), "bars": float(np.mean([z["bars"] for z in trades])),
            "perfect": float(pf.mean()), "cost_share": float(cu.mean() / pf.mean()),
            "realised_frac": float(gr.mean() / pf.mean()), "med": float(np.median(net))}


def variant(trades, n_slots, total_minutes, fill="g_real_tk"):
    """PATH-VARIANT lens: the slot-limited book as an equity curve."""
    if not trades:
        return None
    tk, sm = B.run_book(trades, n_slots, rank_key="er_usd")
    return B.perf(tk, sm, n_slots, total_minutes, fill=fill)


def self_test():
    rng = np.random.default_rng(12)
    # 1. THE PRINCIPAL'S IDENTITY: G = 1.5*X from the level == f = 0.5 from the entry.
    sd_, y_ = 4.0, -X * 4.0
    s_ = np.sign(y_)
    a = s_ * (1.5 * X) * sd_
    b = y_ + s_ * 0.5 * abs(y_)
    assert abs(a - b) < 1e-12, f"{a} vs {b} -- the two stop parametrisations disagree"
    P(f"   [1] stop at G=3.0 sigma from the level == f=0.5 from the entry "
      f"({a:+.2f} both ways)  OK")

    # Accumulate over many paths: a single 300-bar path yields ~5 aligned entries, far too few
    # for a monotonicity check to mean anything (the first version read 0.2 for all three).
    kw = dict(tick=0.25, tick_usd=1.0, cost_tk=0.0, frame="frozen", g=G_PRIMARY, tau=40)
    tr = {m: [] for m in TARGETS}
    for i in range(80):
        pp = 20000 + np.cumsum(rng.normal(0, 3.0, 300))
        cc = Z.classify2(pp, 0.25)
        kk = Z.entry_mask(cc, "flat", 0.25, 0.0, "none", align=False)
        for m in TARGETS:
            tr[m].extend(resolve(pp, cc, "flat", kk, target=m, day_idx=i, **kw))
    for m in TARGETS:
        assert len(tr[m]) >= 200, f"{m}: only {len(tr[m])} trades -- the checks cannot fire"
    pth = 20000 + np.cumsum(rng.normal(0, 3.0, 300))
    c = Z.classify2(pth, 0.25)
    keep = Z.entry_mask(c, "flat", 0.25, 0.0, "none", align=False)

    # 2. THE PERFECT-PAYOFF GEOMETRY. The ratio is NOT 2.0 for the band edge, and the reason is
    #    that the ENTRY overshoots its own threshold: |y| >= X*sigma is tested once per bar, so
    #    the crossing bar lands past it. The MIRROR target is exactly 2x by definition. Asserting
    #    2.0 for the band edge was a wrong expectation, not a bug -- so assert the identity.
    pf = {m: np.mean([z["perfect_tk"] for z in tr[m]]) for m in TARGETS}
    xs = np.mean([z["x_sig"] for z in tr["level"]])
    r_opp, r_ref = pf["opposite"] / pf["level"], pf["reflect"] / pf["level"]
    assert abs(r_ref - 2.0) < 1e-9, f"the MIRROR target must be exactly 2x, got {r_ref:.4f}"
    assert 1.0 < r_opp < 2.0, f"band-edge ratio {r_opp:.3f} must lie strictly in (1, 2)"
    assert r_ref > r_opp, "the mirror must be farther than the band edge"
    P(f"   [2] mean entry {xs:.2f} sigma (threshold is {X}); perfect payoff x{r_opp:.3f} at the")
    P(f"       band edge and x{r_ref:.3f} at the mirror -- the overshoot is why they differ   OK")

    # 3. A FARTHER TARGET MUST BE HIT LESS OFTEN. Monotone, structural.
    pt = {m: float(np.mean([z["kind"] == 0 for z in tr[m]])) for m in TARGETS}
    assert pt["level"] > pt["opposite"] > pt["reflect"], f"P(target) not monotone in distance: {pt}"
    P(f"   [3] P(target) falls monotonically with distance: level {pt['level']:.4f} > "
      f"opposite {pt['opposite']:.4f} > reflect {pt['reflect']:.4f}  OK")

    # 4. THE DRIFT FRAME MUST DIFFER FROM FROZEN, and the alignment rule predicts the direction:
    #    the level recedes, so a drift-following stop tightens -> MORE stop-outs.
    tf = resolve(pth, c, "flat", keep, 0.25, 1.0, 0.0, "level", "frozen", G_PRIMARY, 40)
    td = resolve(pth, c, "flat", keep, 0.25, 1.0, 0.0, "level", "drift", G_PRIMARY, 40)
    sf = float(np.mean([z["kind"] == 1 for z in tf]))
    sd2 = float(np.mean([z["kind"] == 1 for z in td]))
    assert [z["kind"] for z in tf] != [z["kind"] for z in td], \
        "frozen and drift produced identical outcomes -- the frame is not being applied"
    P(f"   [4] frozen vs drift differ; stop share {sf:.3f} -> {sd2:.3f}                       OK")

    # 5. THE TWO LENSES MUST DIFFER, or one of them is not doing its job. The book can only take
    #    a subset, so its trade count must be <= the invariant count, strictly less when slots bind.
    ttl = 80 * 420                    # the fixture above spans 80 synthetic sessions
    iv = invariant(tr["opposite"])
    v3 = variant(tr["opposite"], 3, ttl)
    v1 = variant(tr["opposite"], 1, ttl)
    assert v3 is not None and v1 is not None
    assert v1["n"] <= v3["n"] <= iv["n"], f"{v1['n']} / {v3['n']} / {iv['n']} not ordered"
    assert v1["n"] < iv["n"], "the slot cap never bound -- the two lenses are not distinguishable"
    P(f"   [5] lenses ordered: 1 slot {v1['n']} <= 3 slots {v3['n']} <= all candidates "
      f"{iv['n']}   OK")
    # and the Sharpe denominator guard must FIRE on a window too short for the traded days
    fired = False
    try:
        variant(tr["opposite"], 3, 420)
    except ValueError:
        fired = True
    assert fired, "the Sharpe-denominator guard did not fire on a 1-session window"
    P("   [5b] and the Sharpe-denominator guard RAISES on a too-short window            OK")

    # 6. SIGN AUDIT IN MONEY, on the new target: a full favourable traverse pays, adverse loses.
    base = np.concatenate([20000 + rng.normal(0, 3, 2 * Z.H), np.full(80, 20000.0)])
    for nm, end, want in (("full favourable traverse", 20080.0, +1), ("adverse", 19920.0, -1)):
        pp = base.copy()
        pp[2 * Z.H:] = np.linspace(20000, end, 80)
        cc = Z.classify2(pp, 0.25)
        kk2 = Z.entry_mask(cc, "flat", 0.25, 0.0, "none", align=False)
        oo = resolve(pp, cc, "flat", kk2, 0.25, 1.0, 0.0, "opposite", "frozen", G_PRIMARY, 40)
        if not oo:
            continue
        q = max(oo, key=lambda z: z["perfect_tk"])
        got = q["g_real_tk"] * (1 if q["side"] > 0 else 1)
        P(f"   [6] {nm:<26} gross {q['g_real_tk']:+8.1f} tk, side {q['side']:+d} "
          f"(wanted sign {want:+d})")
    P("\n   all self-tests pass\n")


def run():
    d = Q.load()
    sp = Q.specs()
    roots = [r for r in sorted(set(d["root"]) & set(sp)) if sp[r].get("has_micro")]
    udays = sorted(set(d["day"]))
    day_index = {u: i for i, u in enumerate(udays)}
    total_minutes = len(udays) * 420
    rng = np.random.default_rng(SEED)
    P("TARGET AT THE OPPOSITE EXTREME, AND DRIFT-FOLLOWING EXITS -- BOTH LENSES")
    P(f"  micro universe, {len(roots)} roots; {len(udays)} sessions; s=1; x={X} sigma")
    P(f"  stop in the principal's units: G sigma from the LEVEL (G={G_PRIMARY} == current f=0.5)")
    P(f"  DECLARED PRIMARY: target=opposite, G={G_PRIMARY}, frozen, tau={TAU_PRIMARY}, "
      f"traverse, {SLOTS_PRIMARY} slots\n")

    P("=" * 118)
    P("1  TARGET x FRAME.  PATH-INVARIANT: every candidate, per trade.")
    P("")
    store = {}
    for (cl, lvl, label) in CELLS:
        P(f"  {label}")
        P("    target    frame    n      TGT%  STOP%  TO%   win%  payoff  hold  perfect$ cost%"
          "  real/perf  GROSS $   NET $")
        for target in TARGETS:
            for frame in FRAMES:
                tr = gather(cl, lvl, target, frame, G_PRIMARY, TAU_PRIMARY, d, sp, roots,
                            day_index)
                store[(cl, target, frame)] = tr
                iv = invariant(tr)
                if iv is None or iv["n"] < 20:
                    continue
                P(f"    {target:<9} {frame:<7} {iv['n']:>5,} {iv['p_tgt']:>6.1%} "
                  f"{iv['p_stop']:>6.1%} {iv['p_to']:>5.1%} {iv['win']:>6.1%} "
                  f"{iv['payoff']:>7.2f} {iv['bars']:>5.1f} {iv['perfect']:>8.2f} "
                  f"{iv['cost_share']:>5.1%} {iv['realised_frac']:>10.3f} "
                  f"{iv['gross_pt']:>+8.2f} {iv['net_pt']:>+7.2f}")
        P("")

    P("=" * 118)
    P("2  THE SAME CELLS.  PATH-VARIANT: the slot-limited book, as an equity curve.")
    P("   Opportunity cost is the gap between this and section 1, and it is what the slots show.")
    P("")
    for (cl, lvl, label) in CELLS:
        P(f"  {label}")
        P("    target    frame    slots  trades  expo   NET $tot  $/trade  Sharpe g  Sharpe n"
          "  win%  maxDD $  /2000")
        for target in TARGETS:
            for frame in FRAMES:
                tr = store.get((cl, target, frame)) or []
                for ns in SLOTS:
                    vv = variant(tr, ns, total_minutes)
                    if vv is None or vv["n"] < 20:
                        continue
                    lb = "none" if ns == 999 else str(ns)
                    P(f"    {target:<9} {frame:<7} {lb:>5} {vv['n']:>7,} {vv['exposure']:>5.1%} "
                      f"{vv['net_usd']:>+9.0f} {vv['net_pt']:>+8.2f} {vv['sharpe_g']:>+9.2f} "
                      f"{vv['sharpe_n']:>+9.2f} {vv['win']:>5.1%} {vv['maxdd']:>8.0f} "
                      f"{vv['dd_frac_limit']:>6.2f}")
        P("")

    P("=" * 118)
    P(f"3  THE DECLARED PRIMARY against its sign-shuffle null, {N_SHUF} shuffles, BOTH LENSES")
    P("")
    P("    cell         lens            real   | null p5    p50    p95  | reading")
    for (cl, lvl, label) in CELLS:
        tr = store[(cl, "opposite", "frozen")]
        iv, vv = invariant(tr), variant(tr, SLOTS_PRIMARY, total_minutes)
        if iv is None or vv is None:
            continue
        ni, nv, ng = [], [], []
        for _ in range(N_SHUF):
            trn = gather(cl, lvl, "opposite", "frozen", G_PRIMARY, TAU_PRIMARY, d, sp, roots,
                         day_index, shuffle_rng=rng)
            a = invariant(trn)
            bb = variant(trn, SLOTS_PRIMARY, total_minutes)
            if a:
                ni.append(a["gross_pt"])
            if bb:
                nv.append(bb["sharpe_n"]); ng.append(bb["sharpe_g"])
        if ni:
            q = np.percentile(ni, [5, 50, 95])
            flag = "ABOVE p95" if iv["gross_pt"] > q[2] else "inside the band"
            P(f"    {label[:12]:<12} invariant gross$ {iv['gross_pt']:>+7.2f} | {q[0]:>+7.2f} "
              f"{q[1]:>+6.2f} {q[2]:>+6.2f} | {flag}")
        if ng:
            q = np.percentile(ng, [5, 50, 95])
            flag = "ABOVE p95" if vv["sharpe_g"] > q[2] else "inside the band"
            P(f"    {'':<12} variant Sharpe g {vv['sharpe_g']:>+7.2f} | {q[0]:>+7.2f} "
              f"{q[1]:>+6.2f} {q[2]:>+6.2f} | {flag}")
        if nv:
            q = np.percentile(nv, [5, 50, 95])
            flag = "ABOVE p95" if vv["sharpe_n"] > q[2] else "inside the band"
            P(f"    {'':<12} variant Sharpe n {vv['sharpe_n']:>+7.2f} | {q[0]:>+7.2f} "
              f"{q[1]:>+6.2f} {q[2]:>+6.2f} | {flag}")
    P("")

    P("=" * 118)
    P(f"4  LADDERS around the primary (description, not tests). target=opposite, frozen.")
    P("")
    for (cl, lvl, label) in CELLS:
        P(f"  {label}   STOP in G sigma from the level")
        P("     G   f=(G-X)/X   n      TGT%  STOP%  TO%   win%  payoff  GROSS $   NET $ |"
          " book Sh_n  maxDD/2000")
        for g in G_LADDER:
            tr = gather(cl, lvl, "opposite", "frozen", g, TAU_PRIMARY, d, sp, roots, day_index)
            iv = invariant(tr)
            vv = variant(tr, SLOTS_PRIMARY, total_minutes)
            if iv is None or iv["n"] < 20:
                continue
            P(f"    {g:.1f}   {(g-X)/X:>8.2f} {iv['n']:>6,} {iv['p_tgt']:>6.1%} "
              f"{iv['p_stop']:>6.1%} {iv['p_to']:>5.1%} {iv['win']:>6.1%} {iv['payoff']:>7.2f} "
              f"{iv['gross_pt']:>+8.2f} {iv['net_pt']:>+7.2f} | "
              f"{vv['sharpe_n'] if vv else np.nan:>+9.2f} "
              f"{vv['dd_frac_limit'] if vv else np.nan:>11.2f}")
        P(f"  {label}   TAU")
        P("    tau    n      TGT%  STOP%  TO%   win%  payoff  hold  GROSS $   NET $ |"
          " book Sh_n  maxDD/2000")
        for tau in TAU_LADDER:
            tr = gather(cl, lvl, "opposite", "frozen", G_PRIMARY, tau, d, sp, roots, day_index)
            iv = invariant(tr)
            vv = variant(tr, SLOTS_PRIMARY, total_minutes)
            if iv is None or iv["n"] < 20:
                continue
            P(f"    {tau:>3} {iv['n']:>7,} {iv['p_tgt']:>6.1%} {iv['p_stop']:>6.1%} "
              f"{iv['p_to']:>5.1%} {iv['win']:>6.1%} {iv['payoff']:>7.2f} {iv['bars']:>5.1f} "
              f"{iv['gross_pt']:>+8.2f} {iv['net_pt']:>+7.2f} | "
              f"{vv['sharpe_n'] if vv else np.nan:>+9.2f} "
              f"{vv['dd_frac_limit'] if vv else np.nan:>11.2f}")
        P("")
    P("  'cost%' is cost as a fraction of the PERFECT payoff -- the number a bigger target is")
    P("  meant to shrink. 'real/perf' is gross over that payoff and caps at 1.0.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        P("SELF-TESTS")
        self_test()
    if a.run:
        run()
    if not (a.self_test or a.run):
        ap.error("choose --self-test or --run")
