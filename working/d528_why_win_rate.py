"""WHY IS THE WIN RATE SO LOW, AND IS IT THE STOP?

    python working/d528_why_win_rate.py --self-test
    python working/d528_why_win_rate.py --run

Nothing admitted (R15). Micro universe (the 8 roots the account can trade), in sample only.

THE SHORT ANSWER IS THAT THE WIN RATE IS CHOSEN, NOT OBSERVED. The stop sits at f = 0.5 of the
target distance, and for a driftless walk

    P(reach target before stop) = stop / (target + stop) = f / (1 + f) = 1/3

so a ~33% win rate is what a 2:1 reward-to-risk geometry pays on a fair market. Observed 36-42% is
slightly BETTER than that. A 33% win rate is not a problem in itself: at 2:1 it breaks even.

SO THE QUESTION IS WHY THE PAYOFF IS 0.83-1.15 RATHER THAN 2.0, and this file decomposes it. Three
candidates, all measurable:

  1  OVERSHOOT. A stop is not a limit. Price gaps through it, so the realised loss exceeds the
     designed f*|y|. Measured as  realised loss / (f * |y|)  -- call it the overshoot ratio. If it
     is ~1.6 then a stop placed at 0.5 of the target actually risks 0.8 of it, and the designed 2:1
     is really 1.25:1 before cost.
  2  TIMEOUTS. An exit at market after tau bars is neither a win at the target nor a loss at the
     stop. It lands in between and dilutes both sides.
  3  COST. It is subtracted from the winner and ADDED to the loser, so it hits the payoff ratio
     twice: (W - c) / (L + c).

Each is reported in ticks and in dollars, per outcome, so the three shares add up rather than
being asserted.

AND THEN THE STOP LADDER, which is the actual answer to "is it the stop": win rate, payoff and
expectancy at six stop widths, each against BOTH benchmarks --

    f/(1+f)     the driftless-walk value: what the geometry alone buys
    sign shuffle the same construction on shuffled signs: what this market's fat tails and
                volatility clustering buy on top of the geometry

-- because the first is what makes 33% unsurprising and the second is the only one that can say
whether the construction beats its own noise.
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

TAU = 20
X = 2.0
F_LADDER = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
N_SHUF = 20
SEED = 528991
CELLS = (("cross2", "line", 1, "A  as specified (cross2)"),
         ("none", "flat", 1, "B  no classifier"),
         ("traverse", "flat", 1, "C  traverse (yours)"))
KIND = {0: "TARGET", 1: "STOP", 2: "TIMEOUT"}


def P(*a):
    print(*a, flush=True)


def outcomes(path, c, lvl, keep, tick, tick_usd, cost_tk, f):
    """Per admitted excursion: outcome, realised gross in ticks, and the pieces the payoff needs.

    Returns a dict of arrays. `loss_over_stop` is the realised adverse move divided by the
    DESIGNED stop distance -- the overshoot ratio, defined only for stop-outs.
    """
    idx = np.flatnonzero(keep)
    n = len(path)
    if len(idx) == 0:
        return None
    t = idx + 2 * Z.H
    ok = t < n - 1
    idx, t = idx[ok], t[ok]
    if len(idx) == 0:
        return None
    y = c[f"{lvl}_y"][idx]
    s = np.sign(y)
    p0 = path[t]
    tgt = c[f"{lvl}_lvl"][idx]
    stop_dist = f * np.abs(y)
    stp = p0 + s * stop_dist
    kk = np.arange(1, TAU + 1)
    j = t[:, None] + kk[None, :]
    valid = j <= (n - 1)
    F = path[np.minimum(j, n - 1)]
    ht = ((F - tgt[:, None]) * s[:, None] <= 0.0) & valid
    hs = ((F - stp[:, None]) * s[:, None] >= 0.0) & valid
    i_t = np.where(ht.any(1), ht.argmax(1), R.BIG)
    i_s = np.where(hs.any(1), hs.argmax(1), R.BIG)
    nv = valid.sum(1)
    miss = (i_t == R.BIG) & (i_s == R.BIG)
    stopf = (~miss) & (i_s <= i_t)
    kind = np.where(miss, 2, np.where(stopf, 1, 0))
    rows = np.arange(len(idx))
    last = np.clip(t + nv, 0, n - 1)
    px = np.where(miss, path[last], np.where(stopf, F[rows, np.minimum(i_s, TAU - 1)], tgt))
    gross_tk = (-s) * (px - p0) / tick
    # the overshoot: how far past the stop price the fill actually landed, over the stop distance
    adverse = s * (px - p0)                      # positive = moved against us, in price units
    with np.errstate(invalid="ignore", divide="ignore"):
        loss_over_stop = np.where(stopf & (stop_dist > 0), adverse / stop_dist, np.nan)
    return {"kind": kind, "gross_tk": gross_tk, "tgt_tk": np.abs(y) / tick,
            "stop_tk": stop_dist / tick, "loss_over_stop": loss_over_stop,
            "tick_usd": np.full(len(idx), tick_usd), "cost_tk": np.full(len(idx), cost_tk),
            "bars": np.where(miss, nv, np.where(stopf, i_s + 1, i_t + 1))}


def gather(cl, lvl, s, f, d, sp, roots, shuffle_rng=None):
    acc = None
    for r in roots:
        g = d[d["root"] == r]
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        for day, pth, b0 in B.sessions_with_bars(g, s):
            if shuffle_rng is not None:
                pth = Z.shuffled(pth, shuffle_rng, 1)[0]
            c = Z.classify2(pth, tick)
            if c is None:
                continue
            keep = Z.entry_mask(c, lvl, tick, cost_tk, cl)
            o = outcomes(pth, c, lvl, keep, tick, tick_usd, cost_tk, f)
            if o is None:
                continue
            if acc is None:
                acc = {k: [v] for k, v in o.items()}
            else:
                for k, v in o.items():
                    acc[k].append(v)
    if acc is None:
        return None
    return {k: np.concatenate(v) for k, v in acc.items()}


def stats(o):
    """Win rate, payoff and expectancy in DOLLARS, plus the designed versions for comparison."""
    cu = o["cost_tk"] * o["tick_usd"] + B.COMMISSION_RT
    g = o["gross_tk"] * o["tick_usd"]
    net = g - cu
    w, l = net[net > 0], net[net <= 0]
    tgt_usd = o["tgt_tk"] * o["tick_usd"]
    stp_usd = o["stop_tk"] * o["tick_usd"]
    return {
        "n": len(net),
        "p_target": float((o["kind"] == 0).mean()),
        "p_stop": float((o["kind"] == 1).mean()),
        "p_timeout": float((o["kind"] == 2).mean()),
        "win": float((net > 0).mean()),
        "mean_win": float(w.mean()) if len(w) else np.nan,
        "mean_loss": float(l.mean()) if len(l) else np.nan,
        "payoff": float(w.mean() / abs(l.mean())) if len(l) and l.mean() != 0 else np.nan,
        # the geometry as DESIGNED, before overshoot/timeout/cost degrade it
        "des_win": float(np.mean(tgt_usd - cu)),
        "des_loss": float(np.mean(stp_usd + cu)),
        "des_payoff": float(np.mean(tgt_usd - cu) / np.mean(stp_usd + cu)),
        "overshoot": float(np.nanmean(o["loss_over_stop"])),
        "net_pt": float(net.mean()), "gross_pt": float(g.mean()), "cost_pt": float(cu.mean()),
        "bars": float(o["bars"].mean()),
        # mean gross, in dollars, split by which exit fired
        "g_target": float(g[o["kind"] == 0].mean()) if (o["kind"] == 0).any() else np.nan,
        "g_stop": float(g[o["kind"] == 1].mean()) if (o["kind"] == 1).any() else np.nan,
        "g_timeout": float(g[o["kind"] == 2].mean()) if (o["kind"] == 2).any() else np.nan,
        "tgt_usd": float(tgt_usd.mean()), "stp_usd": float(stp_usd.mean()),
    }


def self_test():
    # 1. THE GEOMETRY IDENTITY. On a synthetic driftless Gaussian walk with no admission filter,
    #    P(target) must land near f/(1+f). This is the claim the whole answer rests on, so it is
    #    measured rather than asserted -- and it must hold at more than one f or it says nothing.
    rng = np.random.default_rng(4)
    P("   [1] P(target) vs the driftless-walk value f/(1+f), synthetic Gaussian walk.")
    P("       The closed form is a GUIDE, not a law here, and the deviations have two causes")
    P("       that pull opposite ways -- so the asserted invariant is MONOTONICITY in f, which")
    P("       is structural (a wider stop can only make the target more likely to come first).")
    obs_l, to_l, ov_l = [], [], []
    for f in (0.25, 0.5, 1.0, 2.0):
        hits = tot = touts = 0
        ovs = []
        for _ in range(140):
            pth = 20000 + np.cumsum(rng.normal(0, 2.0, 200))
            c = Z.classify2(pth, 0.25)
            keep = Z.entry_mask(c, "flat", 0.25, 0.0, "none", align=False)
            o = outcomes(pth, c, "flat", keep, 0.25, 1.0, 0.0, f)
            if o is None:
                continue
            hits += int((o["kind"] == 0).sum()); tot += len(o["kind"])
            touts += int((o["kind"] == 2).sum())
            ovs.append(o["loss_over_stop"][np.isfinite(o["loss_over_stop"])])
        obs = hits / max(tot, 1)
        ovm = float(np.mean(np.concatenate(ovs))) if ovs and len(np.concatenate(ovs)) else np.nan
        obs_l.append(obs); to_l.append(touts / max(tot, 1)); ov_l.append(ovm)
        P(f"       f={f:<5} P(tgt) {obs:.4f}   f/(1+f) {f/(1+f):.4f}   diff "
          f"{obs-f/(1+f):+.4f}   timeouts {touts/max(tot,1):.1%}   overshoot {ovm:.3f}")
    assert obs_l == sorted(obs_l), f"P(target) not monotone in f: {obs_l}"
    assert to_l == sorted(to_l), f"timeout share not monotone in f: {to_l}"
    assert ov_l == sorted(ov_l, reverse=True), f"overshoot not falling in f: {ov_l}"
    assert abs(obs_l[1] - 1 / 3) < 0.02, (
        f"at the SPECIFIED stop f=0.5 the observed {obs_l[1]:.4f} should sit near 1/3")
    P("       P(target) rises with f, timeouts rise with f, overshoot FALLS with f -- and at")
    P(f"       the specified f=0.5 the observed {obs_l[1]:.4f} sits on 1/3. So the low win rate")
    P("       at f=0.5 is the geometry; the deviations at the ends are timeout and overshoot.  OK")

    # 2. THE OVERSHOOT RATIO MUST BE >= 1 BY DEFINITION, and it must exceed 1 on real steps.
    #    A stop can only fill at or beyond its price, never better.
    rng2 = np.random.default_rng(6)
    pth = 20000 + np.cumsum(rng2.normal(0, 2.0, 400))
    c = Z.classify2(pth, 0.25)
    keep = Z.entry_mask(c, "flat", 0.25, 0.0, "none", align=False)
    o = outcomes(pth, c, "flat", keep, 0.25, 1.0, 0.0, 0.5)
    ls = o["loss_over_stop"][np.isfinite(o["loss_over_stop"])]
    assert len(ls) > 0, "no stop-outs -- the overshoot check cannot fire"
    assert ls.min() >= 1.0 - 1e-9, f"overshoot ratio below 1: {ls.min():.4f} -- a stop filled BETTER than its price"
    P(f"   [2] overshoot ratio on {len(ls)} stop-outs: min {ls.min():.3f}, mean {ls.mean():.3f} "
      f"(must be >= 1)   OK")

    # 3. A KNOWN-ANSWER PAYOFF. Designed payoff must equal (target-c)/(f*target+c) exactly.
    fake = {"kind": np.array([0, 1]), "gross_tk": np.array([20.0, -10.0]),
            "tgt_tk": np.array([20.0, 20.0]), "stop_tk": np.array([10.0, 10.0]),
            "loss_over_stop": np.array([np.nan, 1.0]),
            "tick_usd": np.array([1.0, 1.0]), "cost_tk": np.array([2.0, 2.0]),
            "bars": np.array([3, 3])}
    st = stats(fake)
    want = (20.0 - 5.0) / (10.0 + 5.0)           # cost = 2*1 + 3 = $5
    assert abs(st["des_payoff"] - want) < 1e-12, f"{st['des_payoff']} vs {want}"
    P(f"   [3] designed payoff {st['des_payoff']:.4f} == (20-5)/(10+5) = {want:.4f}          OK")
    # and the cost must hit the ratio TWICE -- removing it must RAISE the payoff
    fake0 = dict(fake); fake0["cost_tk"] = np.array([0.0, 0.0])
    st0 = stats(fake0)
    assert st0["des_payoff"] > st["des_payoff"], "cost is not degrading the payoff ratio"
    P(f"   [4] with zero cost the designed payoff rises to {st0['des_payoff']:.4f} "
      f"-- cost hits both sides   OK")
    P("\n   all self-tests pass\n")


def run():
    d = Q.load()
    sp = Q.specs()
    roots = [r for r in sorted(set(d["root"]) & set(sp)) if sp[r].get("has_micro")]
    P("WHY IS THE WIN RATE SO LOW, AND IS IT THE STOP?")
    P(f"  micro universe, {len(roots)} roots: {', '.join(roots)}")
    P(f"  {d['day'].nunique()} sessions, x={X} sigma, tau={TAU}, s=1, drift-aligned, "
      f"realised stop fill\n")

    P("=" * 104)
    P("1  WHERE THE PAYOFF GOES. Designed geometry vs realised, at the specified stop f=0.5")
    P("")
    for (cl, lvl, s, label) in CELLS:
        o = gather(cl, lvl, s, 0.5, d, sp, roots)
        if o is None:
            continue
        st = stats(o)
        P(f"  {label}   n {st['n']:,}")
        P(f"    outcome mix     TARGET {st['p_target']:.1%}   STOP {st['p_stop']:.1%}   "
          f"TIMEOUT {st['p_timeout']:.1%}      mean hold {st['bars']:.1f} bars")
        P(f"    win rate        {st['win']:.1%}   vs P(target) {st['p_target']:.1%}   "
          f"vs f/(1+f) = 33.3%   <- the geometry, not the market")
        P(f"    DESIGNED        win +${st['des_win']:.2f}  loss -${st['des_loss']:.2f}  "
          f"payoff {st['des_payoff']:.2f}   (target ${st['tgt_usd']:.2f}, stop "
          f"${st['stp_usd']:.2f}, cost ${st['cost_pt']:.2f})")
        P(f"    REALISED        win +${st['mean_win']:.2f}  loss ${st['mean_loss']:.2f}  "
          f"payoff {st['payoff']:.2f}")
        P(f"    THE OVERSHOOT   realised adverse move = {st['overshoot']:.3f} x the designed "
          f"stop distance")
        P(f"                    so a stop at {0.5:.2f} of the target actually risks "
          f"{0.5*st['overshoot']:.2f} of it")
        P(f"    gross by exit   TARGET +${st['g_target']:.2f}   STOP ${st['g_stop']:.2f}   "
          f"TIMEOUT ${st['g_timeout']:.2f}")
        P(f"    net/trade       ${st['net_pt']:+.2f}   (gross ${st['gross_pt']:+.2f} "
          f"- cost ${st['cost_pt']:.2f})")
        P("")

    P("=" * 104)
    P("2  THE STOP LADDER -- is it the stop? Win rate and payoff move in opposite directions by")
    P("   construction, so only the PRODUCT (expectancy) can answer.")
    P("")
    rng = np.random.default_rng(SEED)
    for (cl, lvl, s, label) in CELLS:
        P(f"  {label}")
        P("     f    n      f/(1+f)  P(tgt)  null   win%   payoff  des.payoff  overshoot  "
          "GROSS $  NET $")
        for f in F_LADDER:
            o = gather(cl, lvl, s, f, d, sp, roots)
            if o is None or len(o["kind"]) < 30:
                continue
            st = stats(o)
            hits = tot = 0
            for _ in range(N_SHUF):
                on = gather(cl, lvl, s, f, d, sp, roots, shuffle_rng=rng)
                if on is not None:
                    hits += int((on["kind"] == 0).sum()); tot += len(on["kind"])
            pn = hits / max(tot, 1)
            P(f"    {f:.2f} {st['n']:>6,}  {f/(1+f):>7.4f} {st['p_target']:>7.4f} {pn:>6.4f} "
              f"{st['win']:>6.1%} {st['payoff']:>8.2f} {st['des_payoff']:>11.2f} "
              f"{st['overshoot']:>10.3f} {st['gross_pt']:>+8.2f} {st['net_pt']:>+7.2f}")
        P("")
    P("  READING IT: P(tgt) tracks f/(1+f) closely -- the win rate is bought by the stop width,")
    P("  not earned. 'null' is the same construction on shuffled signs, and it is the only column")
    P("  that can show the market adding anything on top of the geometry. des.payoff is what the")
    P("  target and stop promise; payoff is what arrives after overshoot, timeouts and cost.")


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
