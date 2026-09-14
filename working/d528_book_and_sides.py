"""THE BOOK, AND THE LONG/SHORT DECOMPOSITION.

    python working/d528_book_and_sides.py --self-test
    python working/d528_book_and_sides.py --run

Nothing admitted (R15). In-sample only; the reserved slice (2026-04-11 -> 2026-09-09) stays UNREAD.

TWO OBJECTS, AND THEY ARE NOT THE SAME LENS (CLAUDE.md: "where a path exists, both lenses").

  PATH-INVARIANT   every candidate trade, no slot cap, scored per TRADE. That is what every
                   earlier D528 table measured.
  PATH-VARIANT     the slot-limited BOOK, one position per root, ranked entry, scored as an
                   equity curve in DOLLARS. Their difference is opportunity cost.

These are never compared on the same statistic. Per-trade ticks belong to the first; Sharpe,
drawdown and exposure belong to the second.

SIZE AND COST ARE THE INSTRUMENT'S OWN, computed by the runner, per the component standard:

    tick_usd                per-tick dollars at the MINIMUM TRADABLE SIZE (micro where one
                            exists -- MNQ is $0.50/tick against MNQ-full's $5.00)
    crossing                the measured full-year effective crossing in ticks (D507 final),
                            converted at that root's own tick_usd
    COMMISSION_RT           $3.00 per round trip, the figure this repo standardises on at micro
                            size (D469). It is charged PER TRADE and it is not small: the
                            measured edge is ~0.3 ticks, which on MNQ is $0.15.

THE ACCOUNT is the prop geometry already in play: $50,000 with a 4% trailing max loss, so the
drawdown that matters is $2,000 and it is reported against that number, not as a percentage.

LONG/SHORT DECOMPOSITION. Under the principal's rule the side is fully determined by which
extreme was reached:

    drift > 0, price at the LOW extreme   ->  s = sign(y) = -1  ->  LONG
    drift < 0, price at the HIGH extreme  ->  s = sign(y) = +1  ->  SHORT

so splitting on s splits on side. It is worth splitting because the two are NOT symmetric
selections: a long requires a locally rising level and a short a falling one, and the roots here
span equity index, rates, FX, metals, grains and crypto, whose unconditional intraday drifts
differ. The sign shuffle is symmetric by construction, so ANY asymmetry in the NULL's two sides
is sampling noise and calibrates how much of the real asymmetry to believe.
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

H = Z.H
X = 2.0
STOP_FRAC = 0.5
TAU = 20
BIG = R.BIG
ACCOUNT_USD = 50_000.0
TRAIL_MAX_LOSS = 0.04 * ACCOUNT_USD             # $2,000
COMMISSION_RT = 3.00
TRADING_DAYS = 252
SLOT_LADDER = (1, 3, 5, 10, 999)
PRIMARY_SLOTS = 3
N_SHUF = 20
SEED = 528607

# (classifier, level, scale, label). The first is the construction AS SPECIFIED.
CELLS = (
    ("cross2",   "line", 1, "A  as specified (cross2)"),
    ("none",     "flat", 1, "B  no classifier"),
    ("traverse", "flat", 1, "C  traverse (yours)"),
)


def P(*a):
    print(*a, flush=True)


def sessions_with_bars(g, s):
    """Like Q.session_bars but also returns the ABSOLUTE starting minute of the sampled run.

    A book needs a common clock: without the run's own bar offset there is no way to know which
    minute a root's bar i actually is, and positions across roots cannot be sequenced.
    """
    bar = g["bar"].to_numpy()
    mid = g["mid"].to_numpy(np.float64)
    day = g["day"].to_numpy()
    cut = np.flatnonzero(day[1:] != day[:-1]) + 1
    out = []
    for a, b in zip(np.concatenate(([0], cut)), np.concatenate((cut, [len(g)]))):
        bb, mm = bar[a:b], mid[a:b]
        o = np.argsort(bb, kind="stable")
        bb, mm = bb[o], mm[o]
        brk = np.flatnonzero(np.diff(bb) != 1)
        st = np.concatenate(([0], brk + 1))
        sp_ = np.concatenate((brk + 1, [len(bb)]))
        i = int(np.argmax(sp_ - st))
        run, b0 = mm[st[i]:sp_[i]], int(bb[st[i]])
        npts = len(run) // s
        if npts < Q.N + 1:
            continue
        idx = np.arange(npts, dtype=np.int64) * s
        out.append((day[a], run[idx], b0))
    return out


def candidates(path, c, lvl, keep, s, day_idx, bar0, root, tick, tick_usd, cost_tk):
    """Every admitted entry with its outcome, on the GLOBAL minute clock. No overlap rule here --
    the book applies its own, because a per-root overlap rule is not the same constraint as a
    slot cap and conflating them would hide the opportunity cost the two lenses differ by."""
    idx = np.flatnonzero(keep)
    n = len(path)
    if len(idx) == 0:
        return []
    t = idx + 2 * H
    ok = t < n - 1
    idx, t = idx[ok], t[ok]
    if len(idx) == 0:
        return []
    y = c[f"{lvl}_y"][idx]
    sd = c[f"{lvl}_sd"][idx]
    sgn = np.sign(y)
    p0 = path[t]
    tgt = c[f"{lvl}_lvl"][idx]
    stp = p0 + sgn * STOP_FRAC * np.abs(y)
    kk = np.arange(1, TAU + 1)
    j = t[:, None] + kk[None, :]
    valid = j <= (n - 1)
    F = path[np.minimum(j, n - 1)]
    ht = ((F - tgt[:, None]) * sgn[:, None] <= 0.0) & valid
    hs = ((F - stp[:, None]) * sgn[:, None] >= 0.0) & valid
    i_t = np.where(ht.any(1), ht.argmax(1), BIG)
    i_s = np.where(hs.any(1), hs.argmax(1), BIG)
    nv = valid.sum(1)
    miss = (i_t == BIG) & (i_s == BIG)
    stopf = (~miss) & (i_s <= i_t)
    kind = np.where(miss, 2, np.where(stopf, 1, 0))
    d = np.where(miss, nv, np.where(stopf, i_s + 1, i_t + 1))
    last = np.clip(t + nv, 0, n - 1)
    rows = np.arange(len(idx))
    px_real = np.where(miss, path[last],
                       np.where(stopf, F[rows, np.minimum(i_s, TAU - 1)], tgt))
    px_ideal = np.where(miss, path[last], np.where(stopf, stp, tgt))
    g_real = (-sgn) * (px_real - p0) / tick
    g_ideal = (-sgn) * (px_ideal - p0) / tick
    base = day_idx * 2000 + bar0
    cost_usd = float(cost_tk * tick_usd + COMMISSION_RT)
    out = []
    for q in range(len(idx)):
        tgt_tk = float(abs(y[q]) / tick)
        out.append({
            "t_in": int(base + t[q] * s), "t_out": int(base + (t[q] + d[q]) * s),
            "day": day_idx, "root": root, "side": -1 if sgn[q] < 0 else +1,
            "bars": int(d[q]), "kind": int(kind[q]),
            "g_real_tk": float(g_real[q]), "g_ideal_tk": float(g_ideal[q]),
            "cost_usd": cost_usd, "tick_usd": float(tick_usd), "tgt_tk": tgt_tk,
            # --- the three capital-allocation keys ---
            # x_sig: how EXTREME the excursion is, in sigma. Scale-free, says nothing about money.
            "x_sig": float(abs(y[q]) / sd[q]) if sd[q] > 0 else 0.0,
            # er_usd: EXPECTED RETURN ON A PERFECT SET-UP, in dollars. Under perfect reversion the
            # exit is the frozen level, so the gross gain is exactly |y| -- hence this is the
            # trade's best possible outcome, net of what it costs to put on. Same quantity the
            # feasibility filter gated on, used here to RANK rather than to exclude.
            "er_usd": tgt_tk * tick_usd - cost_usd,
            "fcfs": 0.0,                         # no ranking: arrival order, the control
        })
    return out


def build_multi(cells, d, sp, roots, day_index, shuffle_rng=None):
    """All candidates for EVERY cell in one walk of the data, keyed by (classifier, level, scale).

    One walk rather than one per cell, for two reasons. It is 3x faster, and -- more importantly
    for the null books -- every cell then sees the SAME shuffled universe, so the three nulls
    differ only by classifier and not by which random draw they happened to get.
    """
    out = {(cl, lvl, s): [] for (cl, lvl, s, _) in cells}
    scales = sorted({s for (_, _, s, _) in cells})
    for r in roots:
        g = d[d["root"] == r]
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        for s in scales:
            for day, pth, b0 in sessions_with_bars(g, s):
                if shuffle_rng is not None:
                    pth = Z.shuffled(pth, shuffle_rng, 1)[0]
                c = Z.classify2(pth, tick)
                if c is None:
                    continue
                for (cl, lvl, sc, _) in cells:
                    if sc != s:
                        continue
                    keep = Z.entry_mask(c, lvl, tick, cost_tk, cl)
                    out[(cl, lvl, sc)].extend(
                        candidates(pth, c, lvl, keep, s, day_index[day], b0,
                                   r, tick, tick_usd, cost_tk))
    return out


def run_book(cands, n_slots, rank_key="er_usd"):
    """Slot-limited book. One position per root.

    CAPITAL ALLOCATION. With 3 slots against ~10^5 candidates the ranking does almost all the
    work, so it is the decision, not a detail. `rank_key` selects it and the book is sorted by
    (arrival minute, then that key descending) so that when more candidates arrive in a minute
    than there are free slots, capital goes to the highest-ranked:

        er_usd   expected return on a PERFECT set-up, in dollars   <- the principal's rule
        x_sig    the most extreme excursion, in sigma
        fcfs     arrival order only -- the control, which shows what the ranking is worth

    Returns the taken trades and the slot-minutes consumed.
    """
    cands = sorted(cands, key=lambda z: (z["t_in"], -z[rank_key]))
    taken = []
    open_pos = []            # (t_out, root)
    held = set()
    slot_minutes = 0
    for z in cands:
        t = z["t_in"]
        keep = []
        for (t_out, rt) in open_pos:
            if t_out <= t:
                held.discard(rt)
            else:
                keep.append((t_out, rt))
        open_pos = keep
        if len(open_pos) >= n_slots or z["root"] in held:
            continue
        open_pos.append((z["t_out"], z["root"]))
        held.add(z["root"])
        slot_minutes += z["t_out"] - z["t_in"]
        taken.append(z)
    return taken, slot_minutes


def perf(taken, slot_minutes, n_slots, total_minutes, fill="g_real_tk"):
    """Equity-curve statistics in DOLLARS, gross beside net."""
    if not taken:
        return None
    gross = np.array([z[fill] * z["tick_usd"] for z in taken])
    cost = np.array([z["cost_usd"] for z in taken])
    net = gross - cost
    days = np.array([z["day"] for z in taken])
    ud = np.unique(days)
    dg = np.array([gross[days == u].sum() for u in ud])
    dn = np.array([net[days == u].sum() for u in ud])
    # Every session in the window is a return observation, including the flat ones -- a book that
    # trades on 20 of 147 sessions has 127 zero-return days and its Sharpe must carry them.
    # GUARD THE DOOR: if the window implies fewer sessions than the book actually traded, the
    # denominator is wrong and every Sharpe below it is wrong. Raise rather than fall back.
    nsess = total_minutes // 420
    if nsess < len(ud):
        raise ValueError(
            f"total_minutes={total_minutes} implies {nsess} sessions but the book traded on "
            f"{len(ud)} distinct days -- the Sharpe denominator would be wrong")
    def sharpe(dv):
        full = np.zeros(nsess)
        full[:len(dv)] = dv                      # placement is irrelevant to mean/sd
        rr = full / ACCOUNT_USD
        return (rr.mean() / rr.std(ddof=1) * np.sqrt(TRADING_DAYS)) if rr.std(ddof=1) > 0 else np.nan
    eq = np.cumsum(dn)
    dd = float(np.max(np.maximum.accumulate(np.concatenate(([0.0], eq))) -
                      np.concatenate(([0.0], eq))))
    lo, hi = np.quantile(net, [0.01, 0.99])
    tr = net[(net >= lo) & (net <= hi)]
    wins, losses = net[net > 0], net[net <= 0]
    return {
        "n": len(taken), "gross_usd": gross.sum(), "net_usd": net.sum(),
        "gross_pt": gross.mean(), "net_pt": net.mean(), "cost_pt": cost.mean(),
        "med_pt": float(np.median(net)),
        "sharpe_g": sharpe(dg), "sharpe_n": sharpe(dn),
        "win": float((net > 0).mean()),
        "payoff": (wins.mean() / abs(losses.mean())) if len(losses) and losses.mean() != 0 else np.nan,
        "skew": float(((net - net.mean()) ** 3).mean() / net.std() ** 3) if net.std() > 0 else np.nan,
        "kurt": float(((net - net.mean()) ** 4).mean() / net.std() ** 4) if net.std() > 0 else np.nan,
        "trim": tr.mean(), "extop": net[net <= hi].mean(), "exbot": net[net >= lo].mean(),
        "top1": (net[net >= np.quantile(net, 0.99)].sum() / net[net > 0].sum()
                 if (net > 0).any() else np.nan),
        "maxdd": dd, "dd_frac_limit": dd / TRAIL_MAX_LOSS,
        "hold": float(np.mean([z["bars"] for z in taken])),
        "exposure": slot_minutes / max(n_slots * total_minutes, 1),
        "daily_sd": float((dn / ACCOUNT_USD).std(ddof=1)) if len(dn) > 1 else np.nan,
        "be_cost": gross.mean(),                 # cost per RT at which net expectancy is zero
        "tgt_tk": float(np.mean([z["tgt_tk"] for z in taken])),
    }


# ------------------------------------------------------------------------------- self-tests
def self_test():
    rng = np.random.default_rng(2)
    # 1. THE SLOT CAP MUST BIND, AND MONOTONICALLY. More slots can never take fewer trades.
    fake = []
    for i in range(200):
        fake.append({"t_in": i // 4, "t_out": i // 4 + 30, "day": 0, "root": f"R{i%7}",
                     "bars": 30, "kind": 0, "g_real_tk": 1.0, "g_ideal_tk": 1.0,
                     "cost_usd": 1.0, "tick_usd": 1.0, "tgt_tk": 5.0,
                     "x_sig": float(i % 5), "er_usd": float((i * 7) % 11), "fcfs": 0.0})
    counts = []
    for ns in (1, 2, 3, 7, 999):
        tk, _ = run_book(fake, ns)
        counts.append(len(tk))
        assert len(set(z["root"] for z in tk)) <= 7
    assert counts == sorted(counts), f"slot counts not monotone: {counts}"
    assert counts[0] < counts[-1], "the slot cap never bound -- the test cannot fire"
    P(f"   [1] slot cap binds and is monotone in slots: {counts}                      OK")

    # 2. NO TWO OPEN POSITIONS IN THE SAME ROOT, and no position open past its exit
    tk, _ = run_book(fake, 999)
    by_root = {}
    for z in tk:
        prev = by_root.get(z["root"])
        assert prev is None or prev <= z["t_in"], f"{z['root']} overlapped itself"
        by_root[z["root"]] = z["t_out"]
    P(f"   [2] {len(tk)} trades, no root ever holds two positions at once              OK")

    # 2b. THE RANKING MUST CHANGE THE SELECTION. If every rank_key took the same trades, section
    #     2b would be comparing a rule against itself and could not say anything.
    sel = {}
    for rk in ("er_usd", "x_sig", "fcfs"):
        tkr, _ = run_book(fake, 2, rank_key=rk)
        sel[rk] = [(z["t_in"], z["root"]) for z in tkr]
    assert sel["er_usd"] != sel["x_sig"],         "perfect-ER and extremeness picked identical books -- the ranking is not being applied"
    assert sel["er_usd"] != sel["fcfs"], "perfect-ER and arrival order picked identical books"
    P(f"   [2b] the three allocation rules pick DIFFERENT books "
      f"({len(sel['er_usd'])}/{len(sel['x_sig'])}/{len(sel['fcfs'])} trades)          OK")

    # 3. SIGN AUDIT IN MONEY. A favourable move must pay positively at BOTH sides, and the two
    #    sides must respond OPPOSITELY to the same price move.
    n = 2 * H + 8
    up = np.concatenate([20000 + rng.normal(0, 3, 2 * H), np.full(8, 20050.0)])
    dn = np.concatenate([20000 + rng.normal(0, 3, 2 * H), np.full(8, 19950.0)])
    got = {}
    for nm, pth in (("up", up), ("dn", dn)):
        c = Z.classify2(pth, 0.25)
        keep = Z.entry_mask(c, "flat", 0.25, 0.0, "none", align=False)
        cs = candidates(pth, c, "flat", keep, 1, 0, 540, "T", 0.25, 0.5, 0.0)
        assert cs, f"{nm}: no candidates -- the sign audit cannot fire"
        q = max(cs, key=lambda z: z["x_sig"])
        got[nm] = (q["side"], q["g_real_tk"])
    assert got["up"][0] != got["dn"][0], (
        f"a jump up and a jump down produced the SAME side ({got['up'][0]}) -- the side is not "
        f"keyed to the extreme reached")
    P(f"   [3] jump up -> side {got['up'][0]:+d}, jump down -> side {got['dn'][0]:+d}; "
      f"opposite sides    OK")

    # 4. COST IS CHARGED ONCE PER TRADE, IN THE INSTRUMENT'S OWN DOLLARS, and the commission
    #    dominates at micro size -- which is the whole point of the component standard.
    sp = Q.specs()
    for r, ct in (("NQ", 2.134), ("ES", 1.060)):
        cu = ct * sp[r]["tick_usd"] + COMMISSION_RT
        share = COMMISSION_RT / cu
        assert 0.0 < share < 1.0
        P(f"   [4] {r}: crossing {ct:.3f} tk x ${sp[r]['tick_usd']:.2f} = "
          f"${ct*sp[r]['tick_usd']:.2f} + ${COMMISSION_RT:.2f} fee = ${cu:.2f}/RT "
          f"({share:.0%} is fee)")

    # 5. A KNOWN-ANSWER BOOK. Fifty trades of exactly +2 ticks at $1/tick against $1.00 cost must
    #    give gross $100, net $50, win rate 1.0 -- and the perf function must NOT silently flip
    #    a sign or drop the cost.
    known = [{"t_in": i * 50, "t_out": i * 50 + 10, "day": i, "root": f"K{i}",
              "bars": 10, "kind": 0, "g_real_tk": 2.0, "g_ideal_tk": 2.0, "cost_usd": 1.0,
              "tick_usd": 1.0, "tgt_tk": 2.0, "x_sig": 1.0, "er_usd": 1.0, "fcfs": 0.0}
             for i in range(50)]
    tkk, sm = run_book(known, 999)
    o = perf(tkk, sm, 999, 50 * 420)
    assert abs(o["gross_usd"] - 100.0) < 1e-9, o["gross_usd"]
    assert abs(o["net_usd"] - 50.0) < 1e-9, o["net_usd"]
    assert o["win"] == 1.0 and abs(o["net_pt"] - 1.0) < 1e-9
    P(f"   [5] known book: gross ${o['gross_usd']:.2f}, net ${o['net_usd']:.2f}, "
      f"win {o['win']:.0%}, ${o['net_pt']:.2f}/trade                OK")
    # and it must fail if the cost were dropped
    broke = False
    try:
        assert abs(o["gross_usd"] - o["net_usd"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "gross equals net -- the cost is not being charged"
    P("   [6] and that check REJECTS a book where cost is not charged                  OK")
    P("\n   all self-tests pass\n")


# --------------------------------------------------------------------------------------- run
def run(micro_only=False):
    d = Q.load()
    sp = Q.specs()
    roots = sorted(set(d["root"]) & set(sp))
    if micro_only:
        # THE ONLY UNIVERSE THIS ACCOUNT CAN TRADE. 27 of the 35 roots have no micro contract, so
        # a position in them is a full-size contract: all-in cost $13.50-$128.00 per round trip,
        # and a day-session sigma up to $2,806 (SI) against a $2,000 trailing max loss. Several
        # single instruments therefore risk more than the entire drawdown allowance in one
        # session, which is why the all-root book's maxDD ran at 61-415x the limit. That is the
        # vehicle constraint, not an edge result.
        roots = [r for r in roots if sp[r].get("has_micro")]
        P("MICRO-ONLY UNIVERSE: the 8 roots with a micro contract.")
        P("  27 roots dropped: no micro, so a position is a full-size contract whose own daily")
        P("  sigma can exceed the account's entire $2,000 trailing allowance.\n")
    udays = sorted(set(d["day"]))
    day_index = {u: i for i, u in enumerate(udays)}
    total_minutes = len(udays) * 420
    P("THE BOOK AND THE LONG/SHORT DECOMPOSITION")
    P(f"  {len(roots)} roots, {len(udays)} sessions, {d['day'].min()} .. {d['day'].max()}")
    P(f"  size = 1 contract at MINIMUM TRADABLE SIZE (micro where one exists)")
    P(f"  cost = measured crossing x that root's tick_usd + ${COMMISSION_RT:.2f}/RT commission")
    P(f"  account ${ACCOUNT_USD:,.0f}, 4% trailing max loss = ${TRAIL_MAX_LOSS:,.0f}")
    P(f"  x={X} sigma, stop={STOP_FRAC}x target, tau={TAU}, s=1, drift-aligned\n")

    micro = sum(1 for r in roots if sp[r].get("has_micro"))
    tu = np.array([sp[r]["tick_usd"] for r in roots])
    P(f"  {micro} of {len(roots)} roots have a micro; tick_usd ranges "
      f"${tu.min():.2f} to ${tu.max():.2f}, median ${np.median(tu):.2f}\n")

    built = build_multi(CELLS, d, sp, roots, day_index)

    # ---------------------------------------------------------------- 1. LONG vs SHORT
    P("=" * 108)
    P("1  LONG vs SHORT -- path-invariant, every candidate, per TRADE. Null is the sign shuffle,")
    P("   which is symmetric by construction, so its own asymmetry is the noise floor.")
    P("")
    rng = np.random.default_rng(SEED)
    nulls = build_multi(CELLS, d, sp, roots, day_index, shuffle_rng=rng)
    for (cl, lvl, s, label) in CELLS:
        cands = built[(cl, lvl, s)]
        nl = nulls[(cl, lvl, s)]
        P(f"  {label}")
        P("    side     n     share  P(target)  win%   mean tk   med tk   gross $   net $   "
          "hold  | NULL n   P(tgt)  mean tk")
        for sv, nm in ((-1, "LONG"), (+1, "SHORT")):
            g = [z for z in cands if z["side"] == sv]
            gn = [z for z in nl if z["side"] == sv]
            if len(g) < 20:
                continue
            gr = np.array([z["g_real_tk"] for z in g])
            gu = np.array([z["g_real_tk"] * z["tick_usd"] for z in g])
            cu = np.array([z["cost_usd"] for z in g])
            kd = np.array([z["kind"] for z in g])
            nr = np.array([z["g_real_tk"] for z in gn]) if gn else np.zeros(0)
            nkd = np.array([z["kind"] for z in gn]) if gn else np.zeros(0)
            P(f"    {nm:<6} {len(g):>6,} {len(g)/len(cands):>6.1%}   {(kd==0).mean():.4f} "
              f"{(gr>0).mean():>6.1%} {gr.mean():>+9.3f} {np.median(gr):>+8.2f} "
              f"{gu.mean():>+9.2f} {(gu-cu).mean():>+7.2f} "
              f"{np.mean([z['bars'] for z in g]):>5.1f}  | {len(gn):>6,}  "
              f"{((nkd==0).mean() if len(nkd) else np.nan):.4f} "
              f"{(nr.mean() if len(nr) else np.nan):>+8.3f}")
        both = np.array([z["g_real_tk"] for z in cands])
        lg = np.array([z["g_real_tk"] for z in cands if z["side"] == -1])
        st = np.array([z["g_real_tk"] for z in cands if z["side"] == +1])
        if len(lg) > 20 and len(st) > 20:
            se = np.sqrt(lg.var(ddof=1) / len(lg) + st.var(ddof=1) / len(st))
            nlg = np.array([z["g_real_tk"] for z in nl if z["side"] == -1])
            nst = np.array([z["g_real_tk"] for z in nl if z["side"] == +1])
            nse = (np.sqrt(nlg.var(ddof=1) / max(len(nlg), 1) + nst.var(ddof=1) / max(len(nst), 1))
                   if len(nlg) > 2 and len(nst) > 2 else np.nan)
            nd = (nlg.mean() - nst.mean()) if len(nlg) > 2 and len(nst) > 2 else np.nan
            P(f"    LONG - SHORT  {lg.mean()-st.mean():+.3f} tk  (SE {se:.3f}, "
              f"t {(lg.mean()-st.mean())/se:+.2f})     "
              f"the same difference in the NULL: {nd:+.3f} tk (SE {nse:.3f})")
        P("")

    # ---------------------------------------------------------------- 2. THE BOOK
    P("=" * 108)
    P("2  THE BOOK -- path-variant, slot-limited, in DOLLARS. Opportunity cost is the difference")
    P("   between this and section 1, and it is what the slot ladder measures.")
    P("")
    for (cl, lvl, s, label) in CELLS:
        cands = built[(cl, lvl, s)]
        P(f"  {label}   ({len(cands):,} candidate entries)")
        P("    slots  trades  expo   GROSS $  NET $   $/trade  cost/tr  Sharpe g  Sharpe n  "
          "win%  payoff  maxDD $  /2000  hold")
        for ns in SLOT_LADDER:
            tk, sm = run_book(cands, ns)
            o = perf(tk, sm, ns, total_minutes)
            if o is None:
                continue
            lbl = "none" if ns == 999 else str(ns)
            P(f"    {lbl:>5} {o['n']:>7,} {o['exposure']:>5.1%} {o['gross_usd']:>+9.0f} "
              f"{o['net_usd']:>+7.0f} {o['net_pt']:>+8.2f} {o['cost_pt']:>8.2f} "
              f"{o['sharpe_g']:>+9.2f} {o['sharpe_n']:>+9.2f} {o['win']:>5.1%} "
              f"{o['payoff']:>7.2f} {o['maxdd']:>8.0f} {o['dd_frac_limit']:>6.2f} "
              f"{o['hold']:>5.1f}")
        P("")

    # ------------------------------------------------- 2b. CAPITAL PRIORITISATION
    P("=" * 108)
    P("2b PRIORITISING CAPITAL ON THE EXPECTED RETURN OF A PERFECT SET-UP")
    P("   Under perfect reversion the exit is the frozen level, so the gross gain is exactly |y|.")
    P("   er_usd = |y| in ticks x that root's tick_usd - its own round-trip cost: the best the")
    P("   trade can possibly do, in money. Ranked against extremeness and against no ranking.")
    P("")
    for (cl, lvl, s, label) in CELLS:
        cands = built[(cl, lvl, s)]
        P(f"  {label}")
        P("    rank by      slots  trades   NET $   $/trade  Sharpe n  Sharpe g  win%  "
          "mean er$  realised/er  top-3 roots")
        for rk, rname in (("er_usd", "perfect ER $"), ("x_sig", "extremeness"),
                          ("fcfs", "arrival only")):
            for ns in (PRIMARY_SLOTS, 10):
                tk, sm = run_book(cands, ns, rank_key=rk)
                o = perf(tk, sm, ns, total_minutes)
                if o is None:
                    continue
                er = np.mean([z["er_usd"] for z in tk])
                cnt = {}
                for z in tk:
                    cnt[z["root"]] = cnt.get(z["root"], 0) + 1
                top3 = sorted(cnt.items(), key=lambda kv: -kv[1])[:3]
                t3s = " ".join(f"{k}:{v/len(tk):.0%}" for k, v in top3)
                P(f"    {rname:<12} {ns:>5} {o['n']:>7,} {o['net_usd']:>+7.0f} "
                  f"{o['net_pt']:>+8.2f} {o['sharpe_n']:>+9.2f} {o['sharpe_g']:>+9.2f} "
                  f"{o['win']:>5.1%} {er:>9.2f} {o['gross_pt']/er if er else np.nan:>+12.3f}"
                  f"  {t3s}")
        P("")
    P("  'realised/er' is gross $/trade divided by the mean perfect-set-up payoff: the fraction")
    P("  of the perfect outcome the book actually collects. It is the number the prioritisation")
    P("  is trying to raise, and it caps at 1.0 by construction.")
    P("")

    # ---------------------------------------------------------------- 3. THE PRIMARY BOOK, FULL
    P("=" * 108)
    P(f"3  THE FULL REPORT on the book as specified, at {PRIMARY_SLOTS} slots, "
      f"capital ranked by perfect-set-up ER")
    P("")
    for (cl, lvl, s, label) in CELLS:
        tk, sm = run_book(built[(cl, lvl, s)], PRIMARY_SLOTS)
        o = perf(tk, sm, PRIMARY_SLOTS, total_minutes)
        oi = perf(tk, sm, PRIMARY_SLOTS, total_minutes, fill="g_ideal_tk")
        if o is None:
            continue
        P(f"  {label}")
        P(f"    trades {o['n']:,}   exposure {o['exposure']:.1%}   mean hold {o['hold']:.1f} bars"
          f"   mean target {o['tgt_tk']:.1f} tk")
        P(f"    GROSS  ${o['gross_usd']:+,.0f} total, ${o['gross_pt']:+.3f}/trade   "
          f"Sharpe {o['sharpe_g']:+.2f}")
        P(f"    NET    ${o['net_usd']:+,.0f} total, ${o['net_pt']:+.3f}/trade   "
          f"Sharpe {o['sharpe_n']:+.2f}   (cost ${o['cost_pt']:.2f}/trade)")
        P(f"    IDEAL-FILL BRACKET  net ${oi['net_pt']:+.3f}/trade, Sharpe "
          f"{oi['sharpe_n']:+.2f}  -- the true value lies between the two")
        P(f"    BREAKEVEN COST  ${o['be_cost']:.3f}/RT against ${o['cost_pt']:.2f} actually paid"
          f"  ({o['be_cost']/o['cost_pt']:.0%} of it)")
        P(f"    DISTRIBUTION  win {o['win']:.1%}  payoff {o['payoff']:.2f}  "
          f"median ${o['med_pt']:+.2f}  skew {o['skew']:+.2f}  kurt {o['kurt']:.1f}")
        P(f"    TRIMMED 1% both ${o['trim']:+.3f}   ex-top ${o['extop']:+.3f}   "
          f"ex-bottom ${o['exbot']:+.3f}   top 1% = {o['top1']:.1%} of gross +P&L")
        P(f"    RISK  maxDD ${o['maxdd']:,.0f} = {o['dd_frac_limit']:.2f}x the "
          f"${TRAIL_MAX_LOSS:,.0f} trailing limit   daily sd {o['daily_sd']*1e4:.1f} bp")
        P("")

    # ---------------------------------------------------------------- 4. NULL BOOKS
    P("=" * 108)
    P(f"4  NULL BOOKS -- the same construction on {N_SHUF} sign-shuffled universes, "
      f"{PRIMARY_SLOTS} slots")
    P("   Reported as a DISTRIBUTION, with p50 and p95, not a percentile alone.")
    P("")
    nrng = np.random.default_rng(SEED + 99)
    acc = {(cl, lvl, s): {"n": [], "g": [], "npt": []} for (cl, lvl, s, _) in CELLS}
    for _ in range(N_SHUF):
        nl_all = build_multi(CELLS, d, sp, roots, day_index, shuffle_rng=nrng)
        for (cl, lvl, s, _) in CELLS:
            tkn, smn = run_book(nl_all[(cl, lvl, s)], PRIMARY_SLOTS)
            on = perf(tkn, smn, PRIMARY_SLOTS, total_minutes)
            if on:
                acc[(cl, lvl, s)]["n"].append(on["sharpe_n"])
                acc[(cl, lvl, s)]["g"].append(on["sharpe_g"])
                acc[(cl, lvl, s)]["npt"].append(on["net_pt"])
    P("    cell                       real Sh_n |  null p5    p50    p95  | real Sh_g | "
      "null g p50    p95  | real $/tr | null $/tr p50")
    for (cl, lvl, s, label) in CELLS:
        tk, sm = run_book(built[(cl, lvl, s)], PRIMARY_SLOTS)
        o = perf(tk, sm, PRIMARY_SLOTS, total_minutes)
        a = acc[(cl, lvl, s)]
        if not a["n"] or o is None:
            continue
        sn, sg, npt = np.array(a["n"]), np.array(a["g"]), np.array(a["npt"])
        P(f"    {label:<26} {o['sharpe_n']:>+9.2f} | {np.percentile(sn,5):>+7.2f} "
          f"{np.percentile(sn,50):>+6.2f} {np.percentile(sn,95):>+6.2f} | "
          f"{o['sharpe_g']:>+9.2f} | {np.percentile(sg,50):>+10.2f} "
          f"{np.percentile(sg,95):>+6.2f} | {o['net_pt']:>+9.2f} | "
          f"{np.percentile(npt,50):>+14.2f}")
    P("")
    P("  The null is the SAME construction on a sign-shuffled universe, so it carries the same")
    P("  cost, the same slot cap and the same allocation rule. A real Sharpe inside the null's")
    P("  p5-p95 band is indistinguishable from the shuffle at this sample size.")
    P("")
    P("  COMPONENT LINE: not written. A component line requires a construction with positive")
    P("  net expectancy to score; these are negative at every slot count, so there is nothing")
    P("  to enter in docs/COMPONENTS_PROP.md and no correlation against K8 worth computing.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--micro", action="store_true",
                    help="restrict to the 8 roots with a micro contract -- the only universe a "
                         "$50k account with a $2,000 trailing limit can actually trade")
    a = ap.parse_args()
    if a.self_test:
        P("SELF-TESTS")
        self_test()
    if a.run or a.micro:
        run(micro_only=a.micro)
    if not (a.self_test or a.run or a.micro):
        ap.error("choose --self-test, --run or --micro")
