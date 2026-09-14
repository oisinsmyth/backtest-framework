"""THE ORACLE DETECTOR vs THE CAUSAL ONE -- where does the edge live?

    python working/d528_oracle_vs_causal.py --self-test
    python working/d528_oracle_vs_causal.py --run

Nothing admitted (R15). Micro universe, in sample only; reserved slice UNREAD. The oracle arms
here READ THE FUTURE by construction and can never be traded -- they exist to bound what any
causal detector could achieve, per D528's own definition of an oracle: a label computed with
foresight whose only purpose is to define the target a causal statistic is asked to hit.

THE QUESTION. Every result so far says the construction is close to fair. That is consistent with
two very different stories, and they have opposite implications:

    A  THE TRADE IS FAIR.        Being at the extreme of a range carries no edge, because the
                                 market has already priced the chance of return. Then NO detector
                                 helps and the line is finished.
    B  THE DETECTOR IS BLIND.    Ranging regimes genuinely are tradeable, and our causal
                                 classifier simply cannot identify them ahead of time. Then the
                                 edge is real and the work is in detection.

ONE EXPERIMENT SEPARATES THEM: run the identical strategy with the identical entry, alignment,
feasibility, target, frame, stop and tau -- changing ONLY whether the traverse test is computed on
the PAST window or the FUTURE one.

    causal      traverse of +/-1.5 sigma measured on [t-H, t),  level fitted on [t-2H, t-H)
    oracle_h    traverse measured on [t, t+H),                  level fitted on [t-H, t)
    oracle_tau  traverse measured on [t, t+tau),                level fitted on [t-H, t)

Only the traverse test moves. The level's provenance relative to the window it scores is identical
in every arm, so the saturation problem is not reintroduced, and the ONLY difference is foresight.

    oracle profitable, causal not  ->  story B: the regime is tradeable, our detector is blind,
                                       and the gap is the value of perfect detection
    neither profitable             ->  story A: no detector can help, because the trade at an
                                       extreme is fair whatever the regime

AND THE PREMISE CHECK THAT SHOULD HAVE COME FIRST. This programme's own rule is to measure a
conditioner's persistence BEFORE designing a study that conditions on it. It was never done for
`traverse`. Section 1 does it now:

    P(traverse ahead)  vs  P(traverse ahead | traverse behind)

If those are equal, a past traversal carries no information about a future one, and the entire
classifier was built on an unchecked premise. That single number is the most likely place the
reasoning went wrong.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as swv

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_book_and_sides as B                 # noqa: E402
import d528_opposite_extreme_and_drift_stops as O   # noqa: E402

H = Z.H
X = 2.0
G = 3.0
TAU = 40
TRAV_K = 1.5                 # the band half-width the traverse test uses, in sigma
TARGET, FRAME = "reflect", "drift"
ARMS = ("none", "causal", "oracle_h", "oracle_tau")
SLOTS = 3
N_SHUF = 20
SEED = 528451


def P(*a):
    print(*a, flush=True)


def traverse_flags(path, tick):
    """Per bar t in [2H, n): the traverse test computed BACKWARD and FORWARD, plus what a trade
    needs. Returns arrays indexed by t-2H, with `ok_*` validity masks.

    The backward arm reproduces `classify2`'s `trav`. The forward arms score the SAME test on
    bars at or after t, against a level fitted on [t-H, t) -- so each arm's level sits exactly one
    window before the bars it scores, and no arm is saturated.
    """
    c = Z.classify2(path, tick)
    if c is None:
        return None
    n = path.shape[-1]
    n_t = n - 2 * H
    a2, b2, s2 = c["a2"], c["slope"], c["flat_sd"]
    # the LINE fit on [t-H, t) -- classify2 exposes its intercept as a2 for the line level
    lin_a, lin_b = c["a2"], c["slope"]

    def fwd_traverse(width):
        """Traverse of +/-TRAV_K*sigma over [t, t+width), against the [t-H,t) line."""
        out = np.zeros(n_t, dtype=bool)
        ok = np.zeros(n_t, dtype=bool)
        m = np.arange(width, dtype=np.float64)
        for i in range(n_t):
            t = i + 2 * H
            if t + width > n:
                continue
            seg = path[t:t + width]
            lvl = lin_a[i] + lin_b[i] * (H + m)
            y = seg - lvl
            sd = c["line_sd"][i]
            if not np.isfinite(sd) or sd <= 0:
                continue
            ok[i] = True
            out[i] = (y.min() <= -TRAV_K * sd) and (y.max() >= TRAV_K * sd)
        return out, ok

    fh, ok_h = fwd_traverse(H)
    ft, ok_t = fwd_traverse(TAU)
    return {"c": c, "back": c["trav"], "fwd_h": fh, "ok_h": ok_h,
            "fwd_tau": ft, "ok_tau": ok_t}


def arm_mask(tf, tick, cost, arm):
    """The entry mask for one arm. Everything except the traverse test is identical."""
    c = tf["c"]
    keep = (c["flat_sd"] > 0) & c["slope_ok"] & c["a2ok"]
    if arm == "none":
        pass
    elif arm == "causal":
        keep = keep & tf["back"]
    elif arm == "oracle_h":
        keep = keep & tf["fwd_h"] & tf["ok_h"]
    elif arm == "oracle_tau":
        keep = keep & tf["fwd_tau"] & tf["ok_tau"]
    else:
        raise ValueError(arm)
    y, sd = c["flat_y"], c["flat_sd"]
    with np.errstate(invalid="ignore"):
        keep = keep & (np.abs(y) >= X * sd)
    s = np.sign(y)
    keep = keep & (s * c["slope"] < 0)
    keep = keep & (np.abs(y) / tick > cost)
    return np.nan_to_num(keep, nan=False).astype(bool)


def gather(arm, d, sp, roots, day_index, shuffle_rng=None, want_persist=False):
    trades, pers = [], []
    for r in roots:
        gg = d[d["root"] == r]
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        for day, pth, b0 in B.sessions_with_bars(gg, 1):
            if shuffle_rng is not None:
                pth = Z.shuffled(pth, shuffle_rng, 1)[0]
            tf = traverse_flags(pth, tick)
            if tf is None:
                continue
            if want_persist:
                ok = tf["ok_h"]
                if ok.any():
                    pers.append((tf["back"][ok], tf["fwd_h"][ok]))
            keep = arm_mask(tf, tick, cost_tk, arm)
            trades.extend(O.resolve(pth, tf["c"], "flat", keep, tick, tick_usd, cost_tk,
                                    TARGET, FRAME, G, TAU, day_index[day], b0, r))
    return (trades, pers) if want_persist else trades


def self_test():
    rng = np.random.default_rng(41)
    # 1. THE ORACLE MUST ACTUALLY SEE THE FUTURE. On a path engineered to traverse AFTER bar t
    #    and not before, the forward arm must fire where the backward arm does not.
    n = 200
    pth = np.full(n, 20000.0)
    pth[:120] += rng.normal(0, 0.05, 120)                    # quiet: no traversal behind
    pth[120:] = 20000 + 12 * np.sin(np.arange(n - 120) / 2.2)  # loud: traversal ahead
    tf = traverse_flags(pth, 0.25)
    assert tf is not None
    i = 120 - 2 * H
    win_b = tf["back"][max(i - 3, 0):i + 3]
    win_f = tf["fwd_h"][max(i - 3, 0):i + 3]
    assert win_f.any(), "the forward arm never fired on a path that traverses ahead"
    assert win_f.sum() > win_b.sum(), (
        f"forward fired {win_f.sum()} times vs backward {win_b.sum()} at the regime change -- "
        f"the oracle is not seeing the future")
    P(f"   [1] at the regime change the forward arm fires {int(win_f.sum())}x vs backward "
      f"{int(win_b.sum())}x   OK")

    # 2. AND IT MUST BE THE SAME TEST, just shifted. On a stationary oscillation both arms should
    #    fire at a similar rate -- if the forward arm fired far more on a homogeneous path, the
    #    two tests would not be comparable and the contrast would measure the test, not foresight.
    osc = 20000 + 12 * np.sin(np.arange(400) / 2.2) + rng.normal(0, 0.4, 400)
    tf2 = traverse_flags(osc, 0.25)
    rb = tf2["back"].mean()
    rf = tf2["fwd_h"][tf2["ok_h"]].mean()
    assert abs(rb - rf) < 0.25, (
        f"on a stationary path backward fires {rb:.3f} and forward {rf:.3f} -- not the same test")
    P(f"   [2] on a stationary oscillation both arms fire alike: back {rb:.3f}, "
      f"forward {rf:.3f}    OK")

    # 3. THE ARMS MUST DIFFER IN ADMISSION, or the comparison is empty.
    # Accumulated over several paths: one 400-bar walk admits so few bars that both arms can be
    # all-False, and two empty masks compare EQUAL -- the check would pass on a broken contrast
    # and fail on a working one purely by sample size.
    # ON REAL SESSIONS, because synthetic fixtures cannot exercise this path. A random walk fires
    # the traverse test about once in 10,000 bars (25 paths of 400 gave ONE admission, which
    # mirrors the real data: cell C admits 109 of 12,865 candidates), and a smooth oscillation
    # fails the `slope_ok` stability filter instead, because a sine's slope turns over inside the
    # window. The real fixture is the actual input domain, so the check runs there.
    dd = Q.load()
    spx = Q.specs()
    cnt = {a: 0 for a in ARMS}
    diff = 0
    paths = []
    gnq = dd[dd["root"] == "NQ"]
    tick_nq = spx["NQ"]["tick_price_units"]
    for day, p3, b0 in B.sessions_with_bars(gnq, 1)[:40]:
        tf3 = traverse_flags(p3, tick_nq)
        if tf3 is None:
            continue
        ms = {a: arm_mask(tf3, tick_nq, 0.0, a) for a in ARMS}
        for a in ARMS:
            cnt[a] += int(ms[a].sum())
        diff += int((ms["causal"] != ms["oracle_h"]).sum())
        paths.append((p3, tf3, ms))
    # The bar is deliberately low: `traverse` admits about 0.09 trades per root-session in the
    # real data (109 over 8 roots x 147 sessions), so 40 NQ sessions yields a handful. What must
    # be shown is that the contrast is NON-EMPTY, not that it is large.
    assert cnt["causal"] >= 3 and cnt["oracle_h"] >= 3, \
        f"too few admissions to compare: {cnt} -- the check cannot fire"
    assert cnt["none"] >= max(cnt["causal"], cnt["oracle_h"]), "a filter admitted MORE than none"
    assert diff > 0, "causal and oracle_h admitted identical bars -- the contrast is empty"
    P(f"   [3] on 40 real NQ sessions: admissions {cnt}, differing on {diff} bars  OK")
    p3, tf3, ms = paths[0]

    # 4. AND THE ORACLE MUST NOT LEAK INTO THE TRADE ITSELF. The entry price, level, sigma and
    #    slope must be byte-identical across arms -- only WHICH bars are admitted may differ.
    c = tf3["c"]
    for a in ARMS:
        idx = np.flatnonzero(ms[a])
        if len(idx) == 0:
            continue
        tr = O.resolve(p3, c, "flat", ms[a], tick_nq, 1.0, 0.0, TARGET, FRAME, G, TAU, 0, 540, "T")
        base = O.resolve(p3, c, "flat", ms["none"], tick_nq, 1.0, 0.0, TARGET, FRAME, G, TAU,
                         0, 540, "T")
        bykey = {z["t_in"]: z for z in base}
        for z in tr:
            b0 = bykey.get(z["t_in"])
            assert b0 is not None and b0 == z, (
                f"arm {a} changed the TRADE at t_in={z['t_in']}, not just its admission")
    P("   [4] every arm's trades are identical to the unfiltered ones at the same bars      OK")
    P("\n   all self-tests pass\n")


def run():
    d = Q.load()
    sp = Q.specs()
    roots = [r for r in sorted(set(d["root"]) & set(sp)) if sp[r].get("has_micro")]
    udays = sorted(set(d["day"]))
    day_index = {u: i for i, u in enumerate(udays)}
    total_minutes = len(udays) * 420
    P("THE ORACLE DETECTOR vs THE CAUSAL ONE")
    P(f"  micro universe, {len(roots)} roots, {len(udays)} sessions, s=1")
    P(f"  identical in every arm: entry {X} sigma, alignment, feasibility, target={TARGET}, "
      f"frame={FRAME}, G={G}, tau={TAU}")
    P(f"  ONLY the traverse test moves: past window vs future window\n")

    # ---------------------------------------------------------------- 1 the premise check
    P("=" * 108)
    P("1  THE PREMISE CHECK THAT SHOULD HAVE COME FIRST")
    P("   Does a traversal BEHIND predict a traversal AHEAD? If not, the classifier was built")
    P("   on an unchecked premise and that is where the reasoning went wrong.")
    P("")
    _, pers = gather("none", d, sp, roots, day_index, want_persist=True)
    bk = np.concatenate([p[0] for p in pers])
    fw = np.concatenate([p[1] for p in pers])
    p_ahead = fw.mean()
    p_cond = fw[bk].mean() if bk.any() else np.nan
    p_cond_not = fw[~bk].mean() if (~bk).any() else np.nan
    se = np.sqrt(p_cond * (1 - p_cond) / max(bk.sum(), 1)
                 + p_ahead * (1 - p_ahead) / max(len(fw), 1))
    P(f"    bars scored                              {len(fw):,}")
    P(f"    P(traverse ahead)                        {p_ahead:.4f}")
    P(f"    P(traverse ahead | traverse behind)      {p_cond:.4f}   on {int(bk.sum()):,} bars")
    P(f"    P(traverse ahead | NO traverse behind)   {p_cond_not:.4f}")
    P(f"    LIFT                                     {p_cond - p_ahead:+.4f}  "
      f"(SE {se:.4f}, t {(p_cond - p_ahead)/se:+.2f})")
    P("")

    # ---------------------------------------------------------------- 2 the arms
    P("=" * 108)
    P("2  THE ARMS -- both lenses. oracle_* READ THE FUTURE and cannot be traded.")
    P("")
    rng = np.random.default_rng(SEED)
    P("    arm          n      TGT%  win%  payoff | GROSS $   NET $ | bk trades  Sh_g   Sh_n "
      "  NET$tot  maxDD/2k")
    real = {}
    for arm in ARMS:
        tr = gather(arm, d, sp, roots, day_index)
        real[arm] = tr
        iv = O.invariant(tr)
        if iv is None or iv["n"] < 20:
            P(f"    {arm:<12} too few")
            continue
        vv = O.variant(tr, SLOTS, total_minutes)
        P(f"    {arm:<12} {iv['n']:>6,} {iv['p_tgt']:>6.1%} {iv['win']:>5.1%} "
          f"{iv['payoff']:>7.2f} | {iv['gross_pt']:>+8.2f} {iv['net_pt']:>+7.2f} | "
          f"{vv['n']:>9,} {vv['sharpe_g']:>+6.2f} {vv['sharpe_n']:>+6.2f} "
          f"{vv['net_usd']:>+9.0f} {vv['dd_frac_limit']:>9.2f}")
    P("")

    # ---------------------------------------------------------------- 3 nulls
    P("=" * 108)
    P(f"3  AGAINST THE SIGN-SHUFFLE NULL, {N_SHUF} shuffles, both lenses")
    P("")
    P("    arm          real gross | null p50    p95  | real Sh_n | null p50   p95  | verdict")
    for arm in ARMS:
        tr = real.get(arm) or []
        iv, vv = O.invariant(tr), O.variant(tr, SLOTS, total_minutes)
        if iv is None or iv["n"] < 20:
            continue
        gi, sn = [], []
        for _ in range(N_SHUF):
            trn = gather(arm, d, sp, roots, day_index, shuffle_rng=rng)
            a = O.invariant(trn)
            bb = O.variant(trn, SLOTS, total_minutes)
            if a:
                gi.append(a["gross_pt"])
            if bb:
                sn.append(bb["sharpe_n"])
        if not gi:
            continue
        gi, sn = np.array(gi), np.array(sn)
        ab = []
        if iv["gross_pt"] > np.percentile(gi, 95):
            ab.append("gross")
        if vv and sn.size and vv["sharpe_n"] > np.percentile(sn, 95):
            ab.append("Sh_n")
        v = ("ABOVE p95: " + "+".join(ab)) if ab else "inside"
        if ab and iv["net_pt"] <= 0:
            v += " (net<0)"
        P(f"    {arm:<12} {iv['gross_pt']:>+10.2f} | {np.percentile(gi,50):>+8.2f} "
          f"{np.percentile(gi,95):>+6.2f} | {vv['sharpe_n']:>+9.2f} | "
          f"{np.percentile(sn,50):>+8.2f} {np.percentile(sn,95):>+6.2f} | {v}")
    P("")
    P("  READING IT. If oracle_* pays and causal does not, the regime IS tradeable and the")
    P("  detector is blind -- the gap is the value of perfect detection, and an upper bound on")
    P("  what any causal classifier could ever be worth. If NO arm pays, the trade at an extreme")
    P("  is fair whatever the regime, and no detector can help.")


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
