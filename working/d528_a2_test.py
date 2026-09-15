"""THE a2 TEST: does the 4-tick lattice filter cost candidates without buying signal?

    python working/d528_a2_test.py --run

Nothing admitted (R15). Wide 5-minute fixture through 2026-04-10; reserved slice NOT read.

=================================================================================================
EVERY DESIGN CHOICE, ENUMERATED. The principal asked for these explicitly and they are printed
in the output as well as recorded here.
=================================================================================================

WHAT a2 IS. `a2ok` = median |bar return| over the trailing window >= MIN_TICKS (4 ticks). It
rejects windows where price barely moves in TICK terms, to avoid discretisation artefacts. It was
calibrated for 1-MINUTE data, where a 4-tick floor was meaningful. On 5-minute bars typical moves
are far larger, so it may now be near-redundant.

THE PRECEDENT. `slope_ok` was tested exactly this way and failed: it removed 93.1% of bars and
moved P(traverse) by -0.0027. This test follows the same shape so the two are comparable.

D1  THE TARGET is P(traverse, PRICE-referenced): does price reach both -1.5 and +1.5 sigma of the
    price at t, over [t, t+H). Price-referenced because ADDENDUM 12 established that a
    line-referenced target partly measures its own reference level and reversed a key asymmetry.
D2  THE COMPARISON is a2 ON versus a2 OFF, with every other filter identical: sd > 0, |y| >= X
    sigma, drift alignment, feasibility, no-truncation room. slope_ok stays DROPPED.
D3  DEPTH: X = 2.0 (maximum power) and X = 3.5 (the optimum found by the depth sweep). Both,
    because a2 interacts with excursion size and a single depth could mislead.
D4  UNIVERSES: all roots (for power) and micro-8 (for tradeability), reported separately.
D5  SPLIT: out of time. Cuts and forecast z-scores from 2010-2019, evaluated on 2020-2026.
D6  TRADE for the P&L leg: market entry, mirror target, drift-carried exits, stop at X + 1 sigma,
    tau = 20 -- the best known configuration (ADDENDUM 13).
D7  DECISION RULE, declared before running: drop a2 if P(traverse) changes by less than 0.005
    AND net $/trade does not worsen by more than $0.25. That is the same tolerance slope_ok was
    judged on. Anything larger means a2 is buying something and stays.

=================================================================================================
THE CONFOUNDS, NAMED. a2 is not a random sample of bars, so dropping it does not simply give
"more of the same trades". Three things move with it and all three are reported:
=================================================================================================

C1  ROOT MIX. Coarse-tick roots (ZN, ZB, UB have large tick sizes relative to their moves) fail
    a2 more often, so dropping it shifts WHICH INSTRUMENTS trade. The root composition of each
    arm is printed. A P&L difference could be entirely a change of instrument.
C2  SIGMA MIX. a2 is a floor on movement, so it correlates with sigma. Dropping it admits
    quieter windows, which have SMALLER targets while cost is fixed -- so cost/payoff should
    RISE. That is a mechanical effect, not a signal effect, and it is printed.
C3  COST MIX. Because a2 shifts the root mix (C1), it shifts the mean cost per trade too. Mean
    cost is printed per arm so a net difference can be decomposed into gross versus cost.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_wide as W                           # noqa: E402
import d528_forecast_reversion as FR            # noqa: E402
import d528_target_and_stability as TS          # noqa: E402
import d528_confirmation_entry as CE            # noqa: E402

H = Z.H
XS = (2.0, 3.5)
TAU, STOP_BEYOND = 20, 1.0
SPLIT = FR.SPLIT
MICRO = W.MICRO
FEATS4 = TS.FEATS4
TOL_TRAV, TOL_NET = 0.005, 0.25


def P(*a):
    print(*a, flush=True)


def design():
    P("DESIGN CHOICES (printed so they travel with the result)")
    P("  D1 target      P(traverse, PRICE-referenced) over [t, t+H), +/-1.5 sigma")
    P("  D2 comparison  a2 ON vs OFF; all other filters identical; slope_ok stays DROPPED")
    P(f"  D3 depth       X = {XS} -- both, because a2 interacts with excursion size")
    P("  D4 universes   all roots (power) and micro-8 (tradeability), separately")
    P(f"  D5 split       out of time, cuts from <{SPLIT}, evaluated on >={SPLIT}")
    P(f"  D6 trade       market entry, mirror target, drift exits, stop X+{STOP_BEYOND}, tau {TAU}")
    P(f"  D7 rule        DROP a2 if |dP(traverse)| < {TOL_TRAV} AND net worsens by < ${TOL_NET}")
    P("  D8 forecast    each arm gets its OWN forecast, fitted and cut on its OWN early half;")
    P("                 the Q1 lift on P(traverse) is reported per arm, because a2 could be")
    P("                 buying something the forecast already captures")
    P("")
    P("CONFOUNDS REPORTED ALONGSIDE (a2 is not a random sample of bars)")
    P("  C1 root mix    coarse-tick roots fail a2 more; dropping it changes WHICH roots trade")
    P("  C2 sigma mix   a2 is a movement floor, so dropping it admits quieter windows with")
    P("                 smaller targets against a fixed cost -- cost/payoff should RISE")
    P("  C3 cost mix    a changed root mix changes mean cost, so net is decomposed vs gross")
    P("")


def forecast_lift(tr, te):
    """The forecast's Q1 lift on P(traverse), computed INSIDE one subpopulation.

    D8  The composite is the mean of the four causal features' z-scores, standardised on that
        subpopulation's OWN early half and cut at that half's own median -- so the a2-ON and
        a2-OFF arms are each given their own fitted forecast rather than a shared one. If a2
        were buying signal the forecast has already captured, dropping a2 would SHRINK this
        lift; if a2 is dead weight, the lift survives on the larger sample.
        Sign convention follows the rest of D528: LOWER composite z = more forecastable.
    """
    if len(tr) < 200 or len(te) < 200:
        return None
    zt, ze = [], []
    for k in FEATS4:
        mu, sd = np.nanmean(tr[k]), np.nanstd(tr[k])
        if not np.isfinite(sd) or sd == 0:
            return None
        zt.append(((tr[k] - mu) / sd).to_numpy(float))
        ze.append(((te[k] - mu) / sd).to_numpy(float))
    cut = float(np.nanpercentile(np.nanmean(np.vstack(zt), axis=0), 50))
    hi = np.nanmean(np.vstack(ze), axis=0) <= cut
    a, b = te["trav"].to_numpy(float)[hi], te["trav"].to_numpy(float)[~hi]
    if len(a) < 100 or len(b) < 100:
        return None
    return {"n_hi": len(a), "p_hi": a.mean(), "p_lo": b.mean(), "lift": a.mean() - b.mean()}


def collect(roots, src, sp):
    rows = []
    for r in roots:
        if r not in sp:
            continue
        g = src[src["root"] == r]
        if r in W.GATE_2016:
            g = g[g["day"] >= "2016-01-04"]
        if len(g) == 0:
            continue
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        sess = W.sessions_of(g, "close")
        vols = W.tod_and_vol(sess)
        for (day, px, vol, b0), vm in zip(sess, vols):
            c = Z.classify2(px, tick)
            if c is None:
                continue
            tg, ok = TS.three_targets(px, c)
            ft = FR.causal_features(px, c, vm, b0)
            n_t = len(ok)
            room = np.zeros(n_t, bool)
            room[:max(0, len(px) - 2 * H - TAU)] = True
            for xv in XS:
                with np.errstate(invalid="ignore"):
                    common = (c["flat_sd"] > 0) & room & ok
                    common = common & (np.abs(c["flat_y"]) >= xv * c["flat_sd"])
                    common = common & (np.sign(c["flat_y"]) * c["slope"] < 0)
                    common = common & (np.abs(c["flat_y"]) / tick > cost_tk)
                common = np.nan_to_num(common, nan=False).astype(bool)
                if not common.any():
                    continue
                for arm, mask in (("a2_on", common & np.asarray(c["a2ok"])),
                                  ("a2_off", common)):
                    if not mask.any():
                        continue
                    tr = CE.resolve_entry(px, c, mask, tick, tick_usd, cost_tk,
                                          "market", 0.0, 0, 0, b0, r, g=xv + STOP_BEYOND)
                    # ALIGNMENT. resolve_entry SKIPS (emits no row at all for) signal bars with
                    # no room for an exit, so position in `tr` is NOT position in
                    # flatnonzero(mask). It now records its own source index, so the join is
                    # exact rather than positional -- this is the class of silent off-by-one
                    # that has already cost this study twice.
                    tr = [z for z in tr if z["filled"] > 0.5]
                    if not tr:
                        continue
                    sel = np.array([int(z["i"]) for z in tr])
                    assert mask[sel].all(), "resolve_entry returned an unmasked index"
                    k = len(sel)
                    rows.append({
                        "x": np.full(k, xv), "arm": np.full(k, arm, dtype=object),
                        "root": np.full(k, r, dtype=object),
                        "day": np.full(k, day, dtype=object),
                        "trav": tg["price"][sel].astype(float),
                        "sigma_usd": c["flat_sd"][sel] / tick * tick_usd,
                        "gross": np.array([z["gross"] for z in tr], float),
                        "cost": np.array([z["cost"] for z in tr], float),
                        "tgt_usd": np.array([z["tgt_usd"] for z in tr], float),
                        "kind": np.array([z["kind"] for z in tr], float),
                        **{kk: ft[kk][sel].astype(float) for kk in FEATS4}})
    cols = rows[0].keys()
    return pd.DataFrame({cc: np.concatenate([b[cc] for b in rows]) for cc in cols})


def run():
    sp = Q.specs()
    f = W.load("close")
    roots = sorted(set(f["root"]) & set(sp))
    P("THE a2 TEST -- does the 4-tick lattice filter buy anything?")
    P(f"  wide 5-minute fixture, {len(roots)} roots, through {W.IS_END}\n")
    design()
    d = collect(roots, f, sp)
    early = d[d["day"] < SPLIT]
    te = d[d["day"] >= SPLIT]
    P(f"  {len(d):,} rows collected, {len(te):,} in the out-of-time half\n")
    for uni, label in ((None, "ALL ROOTS"), (list(MICRO), "MICRO (tradeable)")):
        sub = te if uni is None else te[te["root"].isin(uni)]
        sub_e = early if uni is None else early[early["root"].isin(uni)]
        P("=" * 116)
        P(f"{label}")
        P("")
        P("      X   arm       n       P(trav)   P(tgt)  gross$    net$   cost$  median sigma$"
          "  cost/pay  top-3 roots")
        for xv in XS:
            res = {}
            for arm in ("a2_on", "a2_off"):
                g = sub[(np.isclose(sub["x"], xv)) & (sub["arm"] == arm)]
                if len(g) < 100:
                    continue
                net = (g["gross"] - g["cost"]).to_numpy(float)
                cnt = g["root"].value_counts()
                top3 = " ".join(f"{k}:{v/len(g):.0%}" for k, v in cnt.head(3).items())
                res[arm] = {"n": len(g), "trav": g["trav"].mean(),
                            "tgt": (g["kind"] == 0).mean(), "gross": g["gross"].mean(),
                            "net": net.mean(), "cost": g["cost"].mean(),
                            "sig": g["sigma_usd"].median(),
                            "cp": g["cost"].mean() / g["tgt_usd"].mean()}
                P(f"    {xv:>3.1f}   {arm:<7} {len(g):>7,} {res[arm]['trav']:>9.4f} "
                  f"{res[arm]['tgt']:>8.1%} {res[arm]['gross']:>+7.2f} {res[arm]['net']:>+7.2f} "
                  f"{res[arm]['cost']:>7.2f} {res[arm]['sig']:>14.1f} {res[arm]['cp']:>9.1%}"
                  f"  {top3}")
            if len(res) == 2:
                on, off = res["a2_on"], res["a2_off"]
                dt = off["trav"] - on["trav"]
                dn = off["net"] - on["net"]
                gain = off["n"] / max(on["n"], 1)
                verdict = ("DROP a2" if abs(dt) < TOL_TRAV and dn > -TOL_NET else "KEEP a2")
                P(f"    {xv:>3.1f}   DELTA   {gain:>6.2f}x  {dt:>+9.4f} "
                  f"{'':>8} {off['gross']-on['gross']:>+7.2f} {dn:>+7.2f} "
                  f"{off['cost']-on['cost']:>+7.2f}  -> {verdict}")
            P("")
        P("    D8 -- the forecast fitted INSIDE each arm (own early half, own median cut)")
        for xv in XS:
            for arm in ("a2_on", "a2_off"):
                mt = (np.isclose(sub_e["x"], xv)) & (sub_e["arm"] == arm)
                me = (np.isclose(sub["x"], xv)) & (sub["arm"] == arm)
                fl = forecast_lift(sub_e[mt], sub[me])
                if fl is None:
                    P(f"      X={xv:.1f} {arm:<7}  too few rows for a fitted forecast")
                    continue
                P(f"      X={xv:.1f} {arm:<7}  n(fav) {fl['n_hi']:>6,}   "
                  f"P(trav) favourable {fl['p_hi']:.4f}  rest {fl['p_lo']:.4f}  "
                  f"lift {fl['lift']:>+.4f}")
        P("")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.run:
        run()
    else:
        ap.error("choose --run")
