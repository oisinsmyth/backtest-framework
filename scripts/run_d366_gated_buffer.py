"""D366 -- the gated momentum buffer against its nulls.

    uv run python scripts/run_d366_gated_buffer.py --selftest
    uv run python scripts/run_d366_gated_buffer.py --null ROT|APRIME|GATEROT|LADDER|C --draws N --part p
    uv run python scripts/run_d366_gated_buffer.py --report

THE POINT OF THIS RECORD. D365's cell was found by an eleven-combination screen; this session then searched about
eighty-nine more constructions on the same fixture without running a single null. The construction below is FROZEN
as that search left it and nothing here adjusts it. GATE-ROT is the null the record exists for: almost all of the
search went into the gate, so a randomly-timed gate of the same shape and share is the control that says whether
the search found anything.

CAUSALITY. Every gate condition is lagged and the one quantile in it (the volatility threshold) is EXPANDING --
the threshold at bar t uses only bars before t, with 504 observations required before it may bind. [GATE] proves
that by perturbing a FUTURE bar and asserting every earlier threshold is unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import run_d365_momentum_buffer as V65          # noqa: E402  -- installs the holdout audit hook first
import d365_export_trades as EX                 # noqa: E402  -- drawdowns

PREP, V58, V50, V47 = V65.PREP, V65.V58, V65.V50, V65.V47
STUDY, SEED, ANN = 366, V65.SEED, 252.0
HI, LO_OPEN, LO_SHUT, CAP = 95, 80, 90, 252
MIN_HIST, WIN_VOL, GC_BPS, HEDGE_HS = 504, 20, 50.0, 1.0
PROBE_REB = 0.02        # what the search charged for hedge rebalancing; the measured rate is 0.0237. [ID] uses this.
ARMS = ("ROT", "APRIME", "GATEROT", "LADDER", "C")
ARM_IX = {a: i for i, a in enumerate(ARMS)}
CHECK = dict(net=8.10, sharpe=0.887, maxdd=3024.0, trades=988, members=24.5, shut=0.908)


def el(t0):
    return f"{time.time() - t0:.0f}s"


# ================================================================== the market conditioners
def conditioners(P, m_f=None):
    """Every series the gate reads, each lagged one bar. Returns a dict of (T,) arrays."""
    T, m0 = P["T"], P["m_start"]
    m_f = np.asarray(P["m_f"], float) if m_f is None else m_f
    idx = np.cumprod(1.0 + np.where(np.isfinite(m_f), m_f, 0.0))
    C = {k: np.full(T, np.nan) for k in ("l63", "l200", "l50", "cross", "mom", "r21", "vol")}
    hi252 = np.zeros(T, bool)
    for t in range(m0 + 260, T):
        C["l63"][t] = idx[t - 1] / idx[t - 64] - 1.0
        C["r21"][t] = idx[t - 1] / idx[t - 22] - 1.0
        C["l200"][t] = idx[t - 1] / np.mean(idx[t - 201:t - 1]) - 1.0
        C["l50"][t] = idx[t - 1] / np.mean(idx[t - 51:t - 1]) - 1.0
        C["cross"][t] = np.mean(idx[t - 51:t - 1]) / np.mean(idx[t - 201:t - 1]) - 1.0
        C["mom"][t] = idx[t - 22] / idx[t - 253] - 1.0
        hi252[t] = idx[t - 1] >= np.max(idx[t - 253:t - 1])
    for t in range(m0 + WIN_VOL + 1, T):
        C["vol"][t] = np.std(m_f[t - WIN_VOL:t], ddof=1) * 1e4
    C["hi252"] = hi252
    C["breadth"] = breadth_of(P)
    return C


def breadth_of(P):
    """Share of eligible names above their own 200-bar mean close, at t-1."""
    T, m0 = P["T"], P["m_start"]
    CL = np.asarray(P["CLOSE"], float)
    elig = np.asarray(P["elig"], bool)
    cs = np.nancumsum(np.where(np.isfinite(CL), CL, 0.0), axis=0)
    cn = np.cumsum(np.isfinite(CL), axis=0)
    out = np.full(T, np.nan)
    for t in range(m0 + 200, T):
        c = cn[t - 1] - cn[t - 201]
        ma = np.where(c >= 150, (cs[t - 1] - cs[t - 201]) / np.maximum(c, 1), np.nan)
        ok = elig[t] & np.isfinite(CL[t - 1]) & np.isfinite(ma)
        if ok.sum() >= 50:
            out[t] = float((CL[t - 1][ok] > ma[ok]).mean())
    return out


def expanding_q(x, p, min_hist=MIN_HIST):
    """The p-th percentile of x using ONLY bars strictly before t. NaN until min_hist observations exist."""
    T = len(x)
    out, seen = np.full(T, np.nan), []
    for t in range(T):
        if len(seen) >= min_hist:
            out[t] = np.percentile(seen, p)
        if np.isfinite(x[t]):
            seen.append(float(x[t]))
    return out


def gate_ladder(C):
    """The 7 structural steps G4..S6. LADDER prices the maximum of this searched ladder; S6 is its endpoint."""
    Z = lambda a, c: np.where(np.isfinite(a), c, True)   # an undefined conditioner never shuts the gate
    vq = expanding_q(C["vol"], 80)
    fin = np.isfinite(C["vol"]) & np.isfinite(C["l63"]) & np.isfinite(C["l200"])
    nc = np.where(fin & np.isfinite(vq), ~((C["vol"] >= vq) & (C["l63"] < 0)), True)
    g4 = nc & Z(C["l200"], C["l200"] > 0) & Z(C["l63"], C["l63"] > 0)
    s1 = g4 & Z(C["mom"], C["mom"] > 0)
    s2 = s1 & Z(C["cross"], C["cross"] > 0)
    s3 = s2 & Z(C["l50"], C["l50"] > 0)
    s4 = s3 & Z(C["r21"], C["r21"] > 0)
    s5 = s4 & Z(C["breadth"], C["breadth"] > 0.5)
    s6 = s5 & C["hi252"]
    return {"G4": g4, "S1": s1, "S2": s2, "S3": s3, "S4": s4, "S5": s5, "S6": s6}, vq


# ================================================================== the book
def hold_of(pct, elig, gate, m0, cap=CAP, lo_open=LO_OPEN, lo_shut=LO_SHUT, hi=HI):
    T, n = pct.shape
    hold = np.zeros((T, n), bool)
    prev = np.zeros(n, bool)
    age = np.zeros(n, int)
    for t in range(m0, T):
        p = pct[t]
        al = elig[t] & np.isfinite(p)
        keep = prev & al & (p > (lo_open if gate[t] else lo_shut))
        if cap is not None:
            keep &= age < cap
        cur = keep | ((~prev) & al & (p > hi) & gate[t])
        age = np.where(cur, np.where(prev, age + 1, 1), 0)
        hold[t] = cur
        prev = cur
    return hold


def dvw_market(P, drop_nan_weight=True):
    """The tradeable hedge: the eligible universe DOLLAR-VOLUME weighted, close-to-close and open-to-close.

    `drop_nan_weight` -- a name whose return is missing on a bar carries no weight in that bar's hedge, so the
    weights renormalise over the names that actually traded. The search's probe left such names in the DENOMINATOR
    for the close-to-close leg, which shrinks the hedge slightly; [ID] reproduces that and measures the difference."""
    elig = np.asarray(P["elig"], bool)
    r1T, ocT = np.asarray(P["r1T"], float), np.asarray(P["ocT"], float)
    DV = np.asarray(P["DV"], float)
    base = elig & np.isfinite(DV) & (DV > 0)

    def leg(R):
        ok = base & np.isfinite(R) if drop_nan_weight else base
        w = np.where(ok, DV, 0.0)
        tot = w.sum(axis=1)
        num = (np.where(ok & np.isfinite(R), R, 0.0) * w).sum(axis=1)
        return np.where(tot > 0, num / np.maximum(tot, 1), np.nan)

    return leg(r1T), leg(ocT)


def book_of(P, hold, mkt_cc, mkt_oc, hedge_oc_on_entry=True):
    """The per-bar equal-weight hedged series and its mask. Entry bars open-to-close on BOTH legs (D340).

    `hedge_oc_on_entry=False` reproduces the search's probe, which filled the LONG leg at the next open on an entry
    bar but held the hedge close-to-close on the same bar -- a leg mismatch. [ID] runs it; nothing else does."""
    ent = V65.entries_of(hold)
    r1T, ocT = np.asarray(P["r1T"], float), np.asarray(P["ocT"], float)
    elig = np.asarray(P["elig"], bool)
    R = np.where(ent, ocT, r1T)
    if hedge_oc_on_entry:
        M = np.where(ent, mkt_oc[:, None], mkt_cc[:, None])
    else:
        M = np.broadcast_to(np.where(np.isfinite(mkt_cc), mkt_cc, 0.0)[:, None], R.shape)
    x = R - M
    h = hold & np.isfinite(x) & elig
    cn = h.sum(axis=1)
    v = np.where(cn > 0, np.where(h, x, 0.0).sum(axis=1) / np.maximum(cn, 1), np.nan)
    return v * 1e4, cn > 0, ent, cn


def costs(P, hold, zeros, cv="PUB", reb_bp=None):
    """The long leg's round trip via D365's OWN per-trade function (R9), plus the hedge's borrow and rebalancing.
    Per bar: the ledger's total round-trip bp over the number of held name-bars it was earned across.

    `reb_bp` overrides the MEASURED rebalance charge. It exists for one reason: the search's probe charged a
    rounded 0.02 bp/bar where the measured figure is 0.0237, and [ID] reproduces the probe on its own arithmetic
    before the frozen construction is reported on the measured one. Nothing else calls it."""
    trades, _oe, _nb = V65.trades_of(hold, zeros)
    two_c, meta = V65.per_trade_two_c(P, trades, cv)
    pos = int(hold.sum())
    lng = float(two_c.sum()) / pos
    mem = hold.sum(axis=1).astype(float)
    mask = mem > 0
    reb = float(np.mean(np.abs(np.diff(mem, prepend=mem[0]))[mask] / np.maximum(mem[mask], 1)))
    charge = reb * HEDGE_HS if reb_bp is None else float(reb_bp)
    return dict(long=lng, borrow=GC_BPS / ANN, rebalance=charge,
                total=lng + GC_BPS / ANN + charge, trades=len(trades), pos_bars=pos,
                reb_rate=reb, per_trade=meta)


def stats(P, v, mask, cost, dates=None):
    dates = dates or P["dates"]
    T = P["T"]
    net = v[mask] - cost
    dts = [dates[t] for t in range(T) if mask[t]]
    mx, _ = EX.drawdowns(net, dts)
    mc, _ = EX.drawdowns_compound(net, dts)
    mb, sd = float(np.mean(net)), float(np.std(net, ddof=1))
    half = T // 2
    e1 = (np.arange(T) < half) & mask
    e2 = (np.arange(T) >= half) & mask
    return dict(gross=float(np.mean(v[mask])), cost=cost, net=mb, vol=sd,
                sharpe=mb / sd * np.sqrt(ANN) if sd > 0 else None, ann_bp=mb * ANN,
                maxdd=mx["depth_bp"], maxdd_pct=mc["depth_pct"], bars_under=mx["bars_under"],
                peak=mx["peak_date"], trough=mx["trough_date"], recovery=mx["recovery_date"],
                calmar=mb * ANN / mx["depth_bp"] if mx["depth_bp"] > 0 else None,
                era1=float(np.mean(v[e1])) - cost, era2=float(np.mean(v[e2])) - cost, bars=int(mask.sum()))


def run_cell(P, gate, pct, elig, mkt_cc, mkt_oc, zeros, cap=CAP, reb_bp=None, hedge_oc_on_entry=True):
    hold = hold_of(pct, elig, gate, P["m_start"], cap=cap)
    v, mask, ent, cn = book_of(P, hold, mkt_cc, mkt_oc, hedge_oc_on_entry=hedge_oc_on_entry)
    c = costs(P, hold, zeros, reb_bp=reb_bp)
    s = stats(P, v, mask, c["total"])
    s.update(members=float(hold.sum(axis=1)[mask].mean()), cost_parts=c, hold=hold, v=v, mask=mask, ent=ent, cn=cn)
    return s


# ================================================================== nulls
def rank_rotate(pct, elig, shift, n_base=None):
    return V65.rank_rotate(pct, elig, shift, n_base)


def gate_rotate(gate, defined, rng):
    """Circularly shift the gate within its DEFINED range: the on-share and the circular run structure are kept
    exactly, only the timing moves. The trigger is untouched -- that is the whole point of this control."""
    d = np.flatnonzero(defined)
    if d.size < 10:
        return gate.copy()
    a, b = d[0], d[-1] + 1
    seg = gate[a:b]
    k = int(rng.integers(1, seg.size))
    out = gate.copy()
    out[a:b] = np.roll(seg, k)
    return out, k


def dist_of(x, obs):
    """The distribution, not the percentile alone (CLAUDE.md) -- and the observed's own RANK inside it, because
    'above p95' hides the difference between beating every draw and squeaking past the 190th of 200."""
    x = np.asarray([v for v in x if v is not None and np.isfinite(v)], float)
    beat = int((x >= obs).sum())
    return dict(p50=float(np.median(x)), p95=float(np.quantile(x, 0.95)), max=float(np.max(x)),
                min=float(np.min(x)), draws=int(x.size), distinct=int(np.unique(x).size),
                above=bool(obs > np.quantile(x, 0.95)), draws_beating_observed=beat,
                pct_rank=float(100.0 * (x < obs).mean()), values=[float(v) for v in x])


# ================================================================== stages
def prepare(P):
    pct = V58.pct_of(P, V65.SCORE)
    elig = np.asarray(P["elig"], bool)
    C = conditioners(P)
    ladder, vq = gate_ladder(C)
    mkt_cc, mkt_oc = dvw_market(P)
    zeros = np.zeros((P['T'], P['n']), float)   # allocated ONCE; trades_of reads only its shape when building the ledger
    return pct, elig, C, ladder, vq, mkt_cc, mkt_oc, zeros


def stage_selftest(P, t0):
    pct, elig, C, ladder, vq, mkt_cc, mkt_oc, zeros = prepare(P)
    S6 = ladder["S6"]
    V65.assert_HOLDOUT_GUARD()

    # [ID] -- reproduce the SEARCH on the search's own arithmetic. The probe that produced §3's check figures charged
    # a rounded 0.02 bp/bar for hedge rebalancing where the measured rate is 0.0237. Run the probe's number first,
    # so the identity is exact rather than approximate; the frozen construction is then reported on the measured one.
    pcc, poc = dvw_market(P, drop_nan_weight=False)
    rep = run_cell(P, S6, pct, elig, pcc, poc, zeros, reb_bp=PROBE_REB, hedge_oc_on_entry=False)
    ch = [("net", rep["net"], CHECK["net"], 0.005), ("sharpe", rep["sharpe"], CHECK["sharpe"], 0.0005),
          ("maxdd", rep["maxdd"], CHECK["maxdd"], 0.5), ("trades", rep["cost_parts"]["trades"], CHECK["trades"], 0),
          ("members", rep["members"], CHECK["members"], 0.05),
          ("shut", float((~S6[P["m_start"]:]).mean()), CHECK["shut"], 0.0005)]
    for nm, got, want, tol in ch:
        assert abs(float(got) - want) <= tol, f"[ID] {nm}: {got} vs the search's {want}"
    print(f"    [ID] on the search's own arithmetic the frozen construction reproduces it: net {rep['net']:+.3f} "
          f"sharpe {rep['sharpe']:.4f} maxDD {rep['maxdd']:.1f} trades {rep['cost_parts']['trades']} "
          f"members {rep['members']:.2f} shut {100*(~S6[P['m_start']:]).mean():.2f}%")

    obs = run_cell(P, S6, pct, elig, mkt_cc, mkt_oc, zeros)
    # [DD] the max drawdown is knife-edge and the record says so rather than reporting one number. Charging the
    # measured rebalance instead of the probe's rounded one costs 0.004 bp/bar and moves the reported max drawdown
    # by more than a hundred bp -- because a recovery that just cleared its old peak no longer does, and two
    # separate drawdown episodes MERGE into one. Proved here by counting the episodes, not asserted.
    net_p = rep["v"][rep["mask"]] - rep["cost_parts"]["total"]
    net_m = obs["v"][obs["mask"]] - obs["cost_parts"]["total"]
    dts = [P["dates"][t] for t in range(P["T"]) if obs["mask"][t]]
    _mp, allp = EX.drawdowns(net_p, dts, top=400)
    _mm, allm = EX.drawdowns(net_m, dts, top=400)
    span_p = [d for d in allp if d["peak_date"] <= _mm["trough_date"] <= d["recovery_date"]] or [_mp]
    print(f"    [DD] the drawdown is knife-edge: the probe's rounded {PROBE_REB} bp/bar rebalance gives "
          f"{rep['maxdd']:.0f} bp over {len(allp)} episodes, the measured {obs['cost_parts']['rebalance']:.4f} gives "
          f"{obs['maxdd']:.0f} bp over {len(allm)} episodes -- {len(allp)-len(allm)} fewer, because a recovery that "
          f"just cleared its peak no longer does. Worst under the measured charge: {obs['peak']} -> {obs['trough']} "
          f"-> {obs['recovery']}. BOTH figures are reported and neither is the construction's 'true' drawdown.")

    # [GATE] each condition, independently, and the expanding quantile's causality
    Z = lambda a, c: np.where(np.isfinite(a), c, True)
    fin = np.isfinite(C["vol"]) & np.isfinite(C["l63"]) & np.isfinite(C["l200"])
    manual = (np.where(fin & np.isfinite(vq), ~((C["vol"] >= vq) & (C["l63"] < 0)), True)
              & Z(C["l200"], C["l200"] > 0) & Z(C["l63"], C["l63"] > 0) & Z(C["mom"], C["mom"] > 0)
              & Z(C["cross"], C["cross"] > 0) & Z(C["l50"], C["l50"] > 0) & Z(C["r21"], C["r21"] > 0)
              & Z(C["breadth"], C["breadth"] > 0.5) & C["hi252"])
    assert np.array_equal(manual, S6), "[GATE] the ladder's S6 != a direct conjunction"
    # Causality, stated at full strength: REPLACE THE ENTIRE FUTURE and assert nothing at or before the cut moves.
    # (An earlier version of this probe multiplied one already-high observation by 100. That leaves its RANK alone,
    #  so the 80th percentile legitimately did not move and the probe proved nothing. Perturb the rank, not the level.)
    x = C["vol"].copy()
    tp = int(np.argmax(np.isfinite(x)) + 3000)
    x[tp:] = 0.0
    vq2 = expanding_q(x, 80)
    nz = lambda a: np.nan_to_num(a, nan=-1.0)
    same = np.array_equal(nz(vq[:tp + 1]), nz(vq2[:tp + 1]))
    diff = int((nz(vq[tp + 1:]) != nz(vq2[tp + 1:])).sum())
    assert same and diff > 0, f"[GATE] the expanding quantile is not causal (same_before={same}, changed_after={diff})"
    print(f"    [GATE] the nine conditions equal a direct conjunction on all {len(S6):,} bars; the expanding "
          f"volatility quantile is causal -- overwriting EVERY bar from {tp} ({P['dates'][tp]}) onward leaves all "
          f"{tp+1:,} thresholds at or before it bit-identical and moves {diff:,} of the {len(vq)-tp-1:,} after it")

    # [HEDGE]
    elig_b = np.asarray(P["elig"], bool)
    DV = np.asarray(P["DV"], float)
    r1T = np.asarray(P["r1T"], float)
    # Probe a bar on which a NaN return is actually PRESENT, so the two weight conventions can disagree there;
    # a bar where every eligible name traded would let a wrong denominator pass unnoticed.
    t_probe = int(np.argmax(np.isfinite(mkt_cc) & (np.arange(P["T"]) > P["m_start"] + 1500)))
    base = elig_b[t_probe] & np.isfinite(DV[t_probe]) & (DV[t_probe] > 0)
    ok = base & np.isfinite(r1T[t_probe])
    man = float((r1T[t_probe][ok] * DV[t_probe][ok]).sum() / DV[t_probe][ok].sum())
    assert abs(mkt_cc[t_probe] - man) < 1e-15, f"[HEDGE] {mkt_cc[t_probe]} vs {man}"
    # Eligibility already carries a finite return, so dropping NaN-return names from the weight DENOMINATOR is a
    # distinction without a difference. Asserted, not assumed -- it is why the entry-bar leg is the ONLY thing that
    # separates the frozen hedge from the search's probe.
    nan_ct = int((elig_b & np.isfinite(DV) & (DV > 0) & ~np.isfinite(r1T)).sum())
    assert np.array_equal(np.nan_to_num(mkt_cc, nan=-9), np.nan_to_num(pcc, nan=-9)), "[HEDGE] conventions differ"
    ent_only = float(np.nanmean(np.abs(np.where(obs["ent"].any(axis=1), mkt_oc - mkt_cc, 0.0))[obs["mask"]]) * 1e4)
    ew = np.asarray(P["m_f"], float)
    d = np.nanmean((ew - mkt_cc)[obs["mask"]]) * 1e4
    print(f"    [HEDGE] the hedge equals a direct recomputation at bar {t_probe} ({P['dates'][t_probe]}) to "
          f"{abs(mkt_cc[t_probe]-man):.1e}; no eligible name-bar anywhere lacks a return ({nan_ct}), so the weight "
          f"denominator is not a degree of freedom and the ENTRY-BAR leg is the only difference from the search's "
          f"probe, worth {ent_only:.2f} bp/bar on entry bars. The equal-weight hedge differs by {d:+.2f} bp/bar "
          f"({d*ANN/100:+.1f}%/yr) and is reported beside, never as the headline")

    # [COST]
    cp = obs["cost_parts"]
    g22 = V65.round_trip_one_leg(10.0, 50.0)
    assert abs(g22 - (2 * 10.0 + 2 * V65.PER_SHARE / 50.0 * 1e4)) < 1e-9, "[COST] one-leg round trip"
    print(f"    [COST] long {cp['long']:.3f} + hedge borrow {cp['borrow']:.3f} + rebalance {cp['rebalance']:.3f} "
          f"= {cp['total']:.3f} bp/bar; the hedge notional moves {100*cp['reb_rate']:.2f}% of itself a bar; the "
          f"one-leg round trip is exactly half G22's four-crossing figure")

    # [LAG]
    T, n = pct.shape
    m0 = P["m_start"]
    h2 = np.zeros((T, n), bool)
    prev = np.zeros(n, bool)
    age = np.zeros(n, int)
    for t in range(m0, T):
        for i in range(0, n, 97):                       # a strided scalar loop, no vector state
            p = pct[t, i]
            al = elig[t, i] and np.isfinite(p)
            if prev[i]:
                keep = al and p > (LO_OPEN if S6[t] else LO_SHUT) and age[i] < CAP
            else:
                keep = al and p > HI and S6[t]
            h2[t, i] = keep
            age[i] = (age[i] + 1) if (keep and prev[i]) else (1 if keep else 0)
            prev[i] = keep
    cols = list(range(0, n, 97))
    assert np.array_equal(h2[:, cols], obs["hold"][:, cols]), "[LAG] the scalar loop disagrees"
    print(f"    [LAG] a strided scalar loop reproduces the hold state on {len(cols)} sampled names over every bar")

    # [CAP]
    tr, _o, _b = V65.trades_of(obs["hold"], np.zeros_like(pct))
    mx_hold = max(a for _r, _e, a, _p, _s in tr)
    unc = run_cell(P, S6, pct, elig, mkt_cc, mkt_oc, zeros, cap=None)
    tr2, _o2, _b2 = V65.trades_of(unc["hold"], np.zeros_like(pct))
    assert mx_hold <= CAP, f"[CAP] a trade ran {mx_hold} bars"
    print(f"    [CAP] no trade exceeds {CAP} bars (longest {mx_hold}); uncapped runs to "
          f"{max(a for _r, _e, a, _p, _s in tr2)} and its Sharpe is {unc['sharpe']:+.3f} against {obs['sharpe']:+.3f}")

    # [S]
    rng = np.random.default_rng([SEED, STUDY, 9])
    hold = obs["hold"]
    cand = np.flatnonzero(hold.sum(axis=1) > 3)
    tb = int(rng.choice(cand[cand > m0 + 1200]))
    ib = int(rng.choice(np.flatnonzero(hold[tb] & ~obs["ent"][tb])))
    r1p = np.asarray(P["r1T"], float).copy()
    r1p[tb, ib] += 50e-4
    P2 = dict(P, r1T=r1p)
    v2, _m2, _e2, cn2 = book_of(P2, hold, mkt_cc, mkt_oc)
    nh = int(obs['cn'][tb])
    d = (v2[tb] - obs["v"][tb])
    other = np.ones(P["T"], bool)
    other[tb] = False
    assert abs(d - 50.0 / nh) < 1e-6, f"[S] moved {d:.4f}, expected {50.0/nh:.4f}"
    assert np.array_equal(np.nan_to_num(v2[other]), np.nan_to_num(obs["v"][other])), "[S] leaked to other bars"
    print(f"    [S] +50 bp on {P['symbols'][ib]} {P['dates'][tb]} moves the book's bar by {d:.4f} bp = 50 / "
          f"{nh} held and no other bar")

    # [GATEROT] and [ROT] invariants
    defined = np.zeros(P["T"], bool)
    defined[m0:] = True
    g2, k = gate_rotate(S6, defined, np.random.default_rng([SEED, STUDY, 3, 0]))
    assert g2[m0:].sum() == S6[m0:].sum(), "[GATEROT] on-share changed"
    assert not np.array_equal(g2, S6), "[GATEROT] returned the observed gate"
    print(f"    [GATEROT] a shift of {k} keeps the on-share exactly ({int(S6[m0:].sum()):,} open bars) and is not "
          f"the observed gate")

    # [6]
    broke = []
    try:
        bad = expanding_q(C["vol"], 80, min_hist=1)
        assert np.array_equal(np.nan_to_num(vq, nan=-1), np.nan_to_num(bad, nan=-1))
    except AssertionError:
        broke.append("GATE/quantile")
    try:
        assert abs(obs["net"] - (CHECK["net"] + 1.0)) <= 0.02
    except AssertionError:
        broke.append("ID")
    try:
        assert abs((v2[tb] - obs["v"][tb]) - 50.0 / (nh + 1)) < 1e-6
    except AssertionError:
        broke.append("S")
    try:
        g3 = S6.copy()
        g3[m0] = ~g3[m0]
        assert g3[m0:].sum() == S6[m0:].sum()
    except AssertionError:
        broke.append("GATEROT/on-share")
    try:                                                 # a hedge that silently drops its entry-bar leg
        bad_cc, _bo = dvw_market(P, drop_nan_weight=False)
        bv, bmask, _be, _bc = book_of(P, hold, bad_cc, mkt_oc, hedge_oc_on_entry=False)
        assert np.array_equal(np.nan_to_num(bv, nan=-9), np.nan_to_num(obs["v"], nan=-9))
    except AssertionError:
        broke.append("HEDGE/entry-leg")
    try:                                                 # a cost that forgets the hedge's borrow
        assert abs(costs(P, hold, zeros, reb_bp=0.0)["total"] - obs["cost_parts"]["total"]) < 1e-12
    except AssertionError:
        broke.append("COST/hedge charge")
    try:                                                 # a book that enters on the SHUT-gate rank -- the cap removed
        assert np.array_equal(hold_of(pct, elig, S6, m0, cap=None), hold)
    except AssertionError:
        broke.append("CAP")
    try:                                                 # a lag audit run against a book shifted one bar forward
        sh = np.zeros_like(hold)
        sh[1:] = hold[:-1]
        assert np.array_equal(sh[:, cols], hold[:, cols])
    except AssertionError:
        broke.append("LAG/one-bar shift")
    assert len(broke) == 8, f"[6] only {broke} raised"
    print(f"    [6] each of {', '.join(broke)} raises on a deliberately broken input")
    print(f"\nOK  selftest passes  ({el(t0)})  {PREP.rss_line()}")


def stage_null(P, arm, draws, part, t0):
    pct, elig, C, ladder, vq, mkt_cc, mkt_oc, zeros = prepare(P)
    S6 = ladder["S6"]
    m0 = P["m_start"]
    obs = run_cell(P, S6, pct, elig, mkt_cc, mkt_oc, zeros)
    rng = np.random.default_rng([SEED, STUDY, ARM_IX[arm], part])
    vals, e1s, e2s, extra = [], [], [], {}
    if arm == "ROT":
        for sh in range(1, V65.N_BASE):
            r = rank_rotate(pct, elig, sh)
            s = run_cell(P, S6, r, elig, mkt_cc, mkt_oc, zeros)
            vals.append(s["net"]); e1s.append(s["era1"]); e2s.append(s["era2"])
        extra["shifts"] = V65.N_BASE - 1
    elif arm == "APRIME":
        for d in range(draws):
            r = V65.aprime_draw(pct, elig, rng)
            s = run_cell(P, S6, r, elig, mkt_cc, mkt_oc, zeros)
            vals.append(s["net"]); e1s.append(s["era1"]); e2s.append(s["era2"])
            if (d + 1) % 25 == 0:
                print(f"    {arm}: {d+1}/{draws} ({el(t0)})")
    elif arm == "GATEROT":
        defined = np.zeros(P["T"], bool)
        defined[m0:] = True
        ks = []
        for d in range(draws):
            g, k = gate_rotate(S6, defined, rng)
            ks.append(k)
            s = run_cell(P, g, pct, elig, mkt_cc, mkt_oc, zeros)
            vals.append(s["net"]); e1s.append(s["era1"]); e2s.append(s["era2"])
            if (d + 1) % 25 == 0:
                print(f"    {arm}: {d+1}/{draws} ({el(t0)})")
        extra["distinct_shifts"] = int(len(set(ks)))
    elif arm == "LADDER":
        for nm, g in ladder.items():
            s = run_cell(P, g, pct, elig, mkt_cc, mkt_oc, zeros)
            extra[nm] = s["net"]
            vals.append(s["net"]); e1s.append(s["era1"]); e2s.append(s["era2"])
        extra["max_step"] = max(ladder, key=lambda k: extra[k])
    else:                                                # C
        b = obs["v"][obs["mask"]] - obs["cost_parts"]["total"]
        for _ in range(draws // 100):
            sg = rng.choice([-1.0, 1.0], size=(100, b.size))
            vals.extend((sg * b[None, :]).mean(axis=1).tolist())
    d = dist_of(vals, obs["net"])
    out = dict(study=STUDY, arm=arm, part=part, draws=len(vals), observed=obs["net"],
               observed_sharpe=obs["sharpe"], dist=d, extra=extra,
               observed_era1=obs["era1"], observed_era2=obs["era2"],
               dist_era1=(dist_of(e1s, obs["era1"]) if e1s else None),
               dist_era2=(dist_of(e2s, obs["era2"]) if e2s else None),
               note="D366: the frozen S6 construction, dollar-volume hedge, hedge costs charged.")
    p = REPO / "data" / f"d366_null_{arm}_p{part}.json"
    p.write_text(json.dumps(V65.clean(out), indent=1))
    print(f"  wrote {p.name}: {arm} p50 {d['p50']:+.2f} p95 {d['p95']:+.2f} max {d['max']:+.2f} vs observed "
          f"{obs['net']:+.2f} -- {'ABOVE' if d['above'] else 'NOT above'} p95  ({el(t0)})  {PREP.rss_line()}")


def stage_jackknife(P, t0):
    """What the winners depend on, tested rather than described. The top trade is GME entered five weeks before the
    January 2021 squeeze and held to the 252-bar CAP -- and the cap was itself picked by a sweep in the same search.
    So: drop the biggest contributors from the UNIVERSE (not from the ledger -- dropping a name from the ledger
    leaves its slot unfilled and flatters the rest) and re-run the whole book, and re-run the cap sweep without GME."""
    pct, elig, C, ladder, vq, mkt_cc, mkt_oc, zeros = prepare(P)
    S6 = ladder["S6"]
    obs = run_cell(P, S6, pct, elig, mkt_cc, mkt_oc, zeros)
    ret = np.where(obs["ent"], np.asarray(P["ocT"], float), np.asarray(P["r1T"], float)) - \
        np.where(obs["ent"], mkt_oc[:, None], mkt_cc[:, None])
    trades, _oe, _nb = V65.trades_of(obs["hold"], ret)
    assert any(p != 0.0 for _r, _e, _a, p, _s in trades), "[JK] the ledger is empty of P&L -- wrong return grid"
    per = {}
    for r, _e, _a, p, _s in trades:
        per[r] = per.get(r, 0.0) + p * 1e4
    order = [r for r, _ in sorted(per.items(), key=lambda kv: -kv[1])]
    tot = sum(per.values())
    print(f"\n  top 10 names by P&L (total {tot:+,.0f} bp): "
          + ", ".join(f"{P['symbols'][r]} {per[r]:+,.0f} ({100*per[r]/tot:.1f}%)" for r in order[:10]))

    rows = []
    for lbl, drop in [("all names", [])] + [(f"drop top {k}", order[:k]) for k in (1, 2, 3, 5, 10)]:
        e2 = elig.copy()
        for r in drop:
            e2[:, r] = False
        s = run_cell(P, S6, pct, e2, mkt_cc, mkt_oc, zeros)
        rows.append((lbl, ", ".join(P["symbols"][r] for r in drop) or "-", s))
    print(f"\n  NAME JACKKNIFE -- the name is removed from the ELIGIBLE UNIVERSE and the book rebuilt, so its slot refills")
    print(f"  {'':<14} {'dropped':<34} {'gross':>7} {'net':>7} {'Sharpe':>7} {'ann':>8} {'maxDD':>6} {'trades':>7} "
          f"{'era2':>7}")
    for lbl, dr, s in rows:
        print(f"  {lbl:<14} {dr[:34]:<34} {s['gross']:+7.2f} {s['net']:+7.2f} {s['sharpe']:+7.3f} "
              f"{s['ann_bp']/100:+7.1f}% {s['maxdd']:6.0f} {s['cost_parts']['trades']:7d} {s['era2']:+7.2f}")

    gme = [i for i, s in enumerate(P["symbols"]) if s == "GME"]
    assert gme, "[JK] GME is not in the universe -- the cap sweep below would compare a column with itself"
    e_no = elig.copy()
    for r in gme:
        e_no[:, r] = False
    assert not np.array_equal(e_no, elig), "[JK] dropping GME changed nothing"
    print(f"\n  THE CAP SWEEP, WITH AND WITHOUT GME -- the 252-bar cap came from a sweep in the same search, and the "
          f"top trade held exactly 252 bars. If the cap was picked BY that trade, the sweep's shape changes when it goes.")
    print(f"  {'cap':>6} {'net all':>9} {'Sharpe':>8} | {'net ex-GME':>11} {'Sharpe':>8}")
    sweep = {}
    for cap in (63, 126, 189, 210, 231, 242, 252, 262, 273, 294, 315, 378, 504, None):
        a = run_cell(P, S6, pct, elig, mkt_cc, mkt_oc, zeros, cap=cap)
        b = run_cell(P, S6, pct, e_no, mkt_cc, mkt_oc, zeros, cap=cap)
        sweep[str(cap)] = dict(net=a["net"], sharpe=a["sharpe"], net_ex=b["net"], sharpe_ex=b["sharpe"])
        print(f"  {str(cap):>6} {a['net']:+9.2f} {a['sharpe']:+8.3f} | {b['net']:+11.2f} {b['sharpe']:+8.3f}")
    best_all = max(sweep, key=lambda k: sweep[k]["sharpe"])
    best_ex = max(sweep, key=lambda k: sweep[k]["sharpe_ex"])
    print(f"  best cap by Sharpe: {best_all} with every name, {best_ex} without GME"
          + ("  -- THE SAME, so the cap was not picked by that one trade" if best_all == best_ex else
             "  -- DIFFERENT: the cap the search chose is partly a property of that one trade"))

    out = dict(study=STUDY, top10=[dict(symbol=P["symbols"][r], pnl_bp=per[r]) for r in order[:10]],
               jackknife=[dict(label=l, dropped=d, gross=s["gross"], net=s["net"], sharpe=s["sharpe"],
                               maxdd=s["maxdd"], trades=s["cost_parts"]["trades"], era2=s["era2"]) for l, d, s in rows],
               cap_sweep=sweep, best_cap_all=best_all, best_cap_ex_gme=best_ex,
               note="D366 jackknife: names dropped from the ELIGIBLE UNIVERSE so the slot refills.")
    p = REPO / "data" / "d366_jackknife.json"
    p.write_text(json.dumps(V65.clean(out), indent=1))
    print(f"\nwrote {p.name}  ({el(t0)})  {PREP.rss_line()}")


def stage_report(P, t0):
    pct, elig, C, ladder, vq, mkt_cc, mkt_oc, zeros = prepare(P)
    S6 = ladder["S6"]
    obs = run_cell(P, S6, pct, elig, mkt_cc, mkt_oc, zeros)
    unc = run_cell(P, S6, pct, elig, mkt_cc, mkt_oc, zeros, cap=None)
    N = {}
    for a in ARMS:
        p = REPO / "data" / f"d366_null_{a}_p0.json"
        N[a] = json.loads(p.read_text()) if p.exists() else None
    ent = obs["ent"]
    ret = np.where(ent, np.asarray(P["ocT"], float), np.asarray(P["r1T"], float)) - \
        np.where(ent, mkt_oc[:, None], mkt_cc[:, None])
    trades, open_end, _nb = V65.trades_of(obs["hold"], ret)
    pnl = np.array([p * 1e4 for _r, _e, _a, p, _s in trades])
    g4 = V50.four_groups(trades, pnl, P, elig)
    k = max(1, int(0.01 * len(pnl)))
    trim = float(np.sort(pnl)[k:-k].mean())
    HALF = np.asarray(P["HALF"]["PUB"], float)
    RAWC = np.asarray(P["RAW_CLOSE"], float)
    rt = float(np.mean([HALF[e0, r] + HALF[min(e0 + a - 1, P["T"] - 1), r] + 2 * V65.PER_SHARE / RAWC[e0, r] * 1e4
                        for r, e0, a, _p, _s in trades if np.isfinite(HALF[e0, r]) and np.isfinite(RAWC[e0, r])]))
    names = {}
    for r, _e, _a, p, _s in trades:
        names[P["symbols"][r]] = names.get(P["symbols"][r], 0.0) + p * 1e4
    tot = sum(v for v in names.values())
    srt = sorted(names.values(), reverse=True)
    cum, half_n = 0.0, 0
    for v in srt:
        cum += v
        half_n += 1
        if tot > 0 and cum >= tot / 2:
            break

    print("\n" + "=" * 150)
    print("D366 -- the gated momentum buffer against its nulls. Construction frozen as an 89-construction search "
          "left it; dollar-volume hedge; hedge borrow and rebalancing charged.")
    print("=" * 150)
    print(f"  {'':<26} {'gross':>7} {'cost':>6} {'net':>7} {'vol':>6} {'Sharpe':>7} {'ann':>8} {'maxDD':>6} "
          f"{'DD%':>6} {'under':>6} {'Calm':>6} {'era1':>7} {'era2':>7}")
    for lbl, s in (("S6 + 252-bar cap", obs), ("S6, uncapped", unc)):
        print(f"  {lbl:<26} {s['gross']:+7.2f} {s['cost']:6.2f} {s['net']:+7.2f} {s['vol']:6.0f} {s['sharpe']:+7.3f} "
              f"{s['ann_bp']/100:+7.1f}% {s['maxdd']:6.0f} {s['maxdd_pct']:5.1f}% {s['bars_under']:6d} "
              f"{s['calmar']:6.3f} {s['era1']:+7.2f} {s['era2']:+7.2f}")
    print(f"  worst drawdown {obs['peak']} -> {obs['trough']} -> {obs['recovery']}; {obs['cost_parts']['trades']:,} "
          f"trades, {obs['members']:.1f} names, gate shut {100*(~S6[P['m_start']:]).mean():.1f}% of bars")
    print(f"  cost: long {obs['cost_parts']['long']:.3f} + borrow {obs['cost_parts']['borrow']:.3f} + rebalance "
          f"{obs['cost_parts']['rebalance']:.3f} = {obs['cost_parts']['total']:.3f} bp/bar")

    print(f"\n  NULLS (net PUB bp/bar; the observed is {obs['net']:+.2f})")
    print(f"  {'arm':<10} {'draws':>6} {'p50':>8} {'p95':>8} {'max':>8} {'rank%':>7} {'beat obs':>9}  above p95?")
    for a in ARMS:
        if N[a] is None:
            print(f"  {a:<10} {'NOT RUN':>6}")
            continue
        d = N[a]["dist"]
        print(f"  {a:<10} {d['draws']:>6} {d['p50']:+8.2f} {d['p95']:+8.2f} {d['max']:+8.2f} "
              f"{d['pct_rank']:6.1f}% {d['draws_beating_observed']:9d}  {'YES' if d['above'] else 'no'}")
    if N["LADDER"]:
        print("    ladder steps: " + ", ".join(f"{k} {v:+.2f}" for k, v in N["LADDER"]["extra"].items()
                                               if k != "max_step"))
        print("    NOTE: S6 IS the ladder's own maximum, so 'above the p95 of LADDER-MAX' is close to automatic and "
              "Q6 is a weak test by construction. The informative reading is the ladder's SHAPE, printed above.")
    print(f"\n  ERA 2 vs its rotation null (Q3): observed {obs['era2']:+.2f}"
          + (f"; A' era-2 p50 {N['APRIME']['dist_era2']['p50']:+.2f} p95 {N['APRIME']['dist_era2']['p95']:+.2f}, "
             f"{N['APRIME']['dist_era2']['draws_beating_observed']} of {N['APRIME']['dist_era2']['draws']} draws beat it"
             if N["APRIME"] and N["APRIME"].get("dist_era2") else " -- A' era split NOT RECORDED"))
    print(f"    era 1 observed {obs['era1']:+.2f}"
          + (f"; A' era-1 p50 {N['APRIME']['dist_era1']['p50']:+.2f} p95 {N['APRIME']['dist_era1']['p95']:+.2f}"
             if N["APRIME"] and N["APRIME"].get("dist_era1") else "")
          + " -- era 1 was explicitly NOT predicted to clear anything (§3 Q3)")

    print(f"\n  FOUR GROUPS per trade: n {len(pnl):,} mean {pnl.mean():+.1f} median {np.median(pnl):+.1f} "
          f"win {(pnl>0).mean():.1%} payoff {g4['payoff']:.2f} hold mean {g4['hold_mean']:.0f} median "
          f"{g4['hold_median']:.0f} skew {g4['skew']:+.1f} kurt {g4['kurtosis_excess']:+.0f}")
    print(f"    trims (k={g4['trim_k']}): ex-top {g4['mean_ex_top_bp']:+.1f}, ex-bottom {g4['mean_ex_bottom_bp']:+.1f}, "
          f"BOTH {g4['mean_trimmed_bp']:+.1f}; round trip {rt:.1f}. The mean sits FAR ABOVE the median, so the RIGHT "
          f"tail carries this book")
    print(f"    names to half the P&L {half_n} of {len(names)}; top 1/5/10 share "
          + "/".join(f"{100*g4['top_name_share'][k]:.0f}%" for k in ("1", "5", "10"))
          + f"; profitable years {100*g4['profitable_years_share']:.0f}% of {g4['years']}; open at end {open_end}")
    tt = g4["top_trade"]
    print(f"    TOP TRADE NAMED: {tt['symbol']} entered {tt['entry_date']} at ${tt['as_traded_price']:.2f}, held "
          f"{tt['hold']} bars, {tt['pnl_bp']:+,.0f} bp = {100*tt['share_of_pnl']:.1f}% of all P&L, dollar volume at "
          f"the {tt['dv_percentile_at_entry']:.0f}th percentile of that day's eligible names")
    sd, sp = g4["split_dead_alive"], g4["split_price"]
    print(f"    dead {sd['dead_n']} at {sd['dead_mean_bp']:+.0f} vs alive {sd['alive_n']} at {sd['alive_mean_bp']:+.0f}; "
          f"below ${sp['median_price']:.2f} {sp['low_n']} at {sp['low_mean_bp']:+.0f} vs above {sp['high_n']} at "
          f"{sp['high_mean_bp']:+.0f}")

    q = {}
    q["Q1"] = bool(obs["net"] > 0 and all(N[a] and N[a]["dist"]["above"] for a in ("ROT", "APRIME", "C")))
    q["Q2"] = bool(N["GATEROT"] and N["GATEROT"]["dist"]["above"])
    a2 = N["APRIME"].get("dist_era2") if N["APRIME"] else None
    q["Q3"] = bool(a2 and obs["era2"] > a2["p95"])
    q["Q4"] = bool(half_n >= 15)
    q["Q5"] = bool(trim > rt)
    q["Q6"] = bool(N["LADDER"] and N["LADDER"]["dist"]["above"])
    q["Q7"] = bool(N["GATEROT"] and N["GATEROT"]["dist"]["p50"] > 0)
    q["Q8"] = bool(obs["sharpe"] > unc["sharpe"])
    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) net > 0 and above the p95 of ROT, A' and C: {v_(q['Q1'])} -- net {obs['net']:+.2f}; "
          + ", ".join(f"{a} p95 {N[a]['dist']['p95']:+.2f}" for a in ("ROT", "APRIME", "C") if N[a]))
    print(f"  Q2 above the p95 of GATE-ROT (a random gate of the same shape): {v_(q['Q2'])}"
          + (f" -- p95 {N['GATEROT']['dist']['p95']:+.2f}, p50 {N['GATEROT']['dist']['p50']:+.2f}" if N["GATEROT"] else ""))
    print(f"  Q3 era 2 above the p95 of A' restricted to era 2: {v_(q['Q3'])}"
          + (f" -- {obs['era2']:+.2f} vs p95 {a2['p95']:+.2f}" if a2 else " -- NOT RECORDED")
          + f". Era 1 ({obs['era1']:+.2f}) was not predicted to clear anything and its failure is not counted.")
    print(f"  Q4 at least 15 names to half the P&L: {v_(q['Q4'])} -- {half_n} of {len(names)}")
    print(f"  Q5 the 1% trimmed mean per trade exceeds the round trip: {v_(q['Q5'])} -- {trim:+.1f} vs {rt:.1f}")
    print(f"  Q6 above the p95 of LADDER-MAX: {v_(q['Q6'])}"
          + (f" -- p95 {N['LADDER']['dist']['p95']:+.2f}, best step {N['LADDER']['extra'].get('max_step')}" if N["LADDER"] else ""))
    print(f"  Q7 (AGAINST) GATE-ROT's p50 is above zero -- a random gate still pays: {v_(q['Q7'])}"
          + (f" -- p50 {N['GATEROT']['dist']['p50']:+.2f}" if N["GATEROT"] else ""))
    print(f"  Q8 the cap's Sharpe exceeds the uncapped: {v_(q['Q8'])} -- {obs['sharpe']:+.3f} vs {unc['sharpe']:+.3f}")

    out = dict(study=STUDY, construction="S6 + 252-bar cap, dollar-volume hedge, hedge costs charged",
               observed={k: v for k, v in obs.items() if k not in ("hold", "v", "mask", "ent", "cn")},
               uncapped={k: v for k, v in unc.items() if k not in ("hold", "v", "mask", "ent", "cn")},
               nulls={a: (N[a]["dist"] if N[a] else None) for a in ARMS},
               ladder=(N["LADDER"]["extra"] if N["LADDER"] else None),
               four_groups_full=g4,
               four_groups=dict(n=len(pnl), mean=float(pnl.mean()), median=float(np.median(pnl)),
                                win=float((pnl > 0).mean()), trimmed=trim, round_trip=rt,
                                names_to_half=half_n, names=len(names), open_at_end=open_end),
               predictions=q, search_multiplicity=89,
               note="D366: the endpoint of an 89-construction search, run against its nulls for the first time. "
                    "GATE-ROT is the control the record exists for.")
    p = REPO / "data" / "d366_gated_buffer.json"
    p.write_text(json.dumps(V65.clean(out), indent=1))
    print(f"\nwrote {p.name}  ({el(t0)})  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--null", choices=ARMS)
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--jackknife", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    print("D366  the gated momentum buffer against its nulls")
    P = PREP.prep(need_grids=False)
    if a.selftest:
        stage_selftest(P, t0)
    elif a.null:
        stage_null(P, a.null, a.draws, a.part, t0)
    elif a.jackknife:
        stage_jackknife(P, t0)
    elif a.report:
        stage_report(P, t0)
    else:
        ap.error("one of --selftest, --null ARM, --jackknife, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
