"""D345 -- the event-driven book: flat by default, enter on a signal, exit on a condition.

Pure numpy + a bar loop, deliberately shaped like run_d306_width_exits.simulate so
that, fed the slot book's "rank < depth at t" as its signal with no holding cap, it
reproduces the slot book's invariant ledger bit-identically (D345 section 2). Reads
nothing but the arrays it is handed.

    res = simulate_event(A2, sig_long, sig_short, score_T, exit="target", cap=40,
                         n_max=2, x_target=0.9627, U=4)

Inputs are (T, n) and ALREADY LAGGED: sig_*[t] and score_T[t] are what is known at
the close of t-1. The fill is the next open (D340): the entry bar earns ocT against
mkt_oc, later bars r1T against mkt. Exits are decided on information through t-1
(age > 0), then entries, then every held position is marked once.

Returned dict:
  trades      [(row, e0, age, pnl, side)]  summed excess, as every ledger here
  cnt0, cnt1  positions held per bar per side
  ent         entries per bar; skipped  signals not taken (variant only)
  book_slot   mean(long v) - mean(short v), NaN unless both sides held  (slot-book def.)
  book_dep    sum(signed v) / n_held, NaN when flat                    (DEPLOYED capital)
  book_tot    sum(signed v) / U, 0.0 when flat                          (TOTAL capital)
  defined     bars where the signal is defined (>= MIN_DEFINED finite scores)

With hedged_series=True (D353; default False leaves the returned dict EXACTLY as above)
the mark loop also accumulates the HEDGED signed sum sgn * (v - m) per bar -- the same
term the ledger's per-trade pnl sums -- and three keys are ADDED:
  signed_x    sum over held positions of sgn * (v - m) per bar (0.0 when flat)
  book_dep_x  signed_x / n_held, NaN when flat                          (DEPLOYED, hedged)
  book_tot_x  signed_x / U over defined bars, NaN elsewhere              (TOTAL, hedged)
"""

from __future__ import annotations

import numpy as np

MIN_DEFINED = 50
EXITS = ("target", "invalidation", "cap")


def defined_bars(score_T, min_defined=MIN_DEFINED):
    return np.isfinite(score_T).sum(axis=1) >= min_defined


def simulate_event(A2, sig_long, sig_short, score_T, *, exit, cap, n_max=None, x_target=0.9627, U=4,
                   first_bar=1, hedged_series=False):
    if exit not in EXITS:
        raise ValueError(f"exit must be one of {EXITS}, got {exit!r}")
    r1T, mkt, vxT, finT = A2["r1T"], A2["mkt"], A2["vxT"], A2["finT"]
    ocT, mkt_oc = A2["ocT"], A2["mkt_oc"]
    T, n = r1T.shape
    sig = {0: sig_long, 1: sig_short}
    cnt = {0: np.zeros(T, np.int32), 1: np.zeros(T, np.int32)}
    ret = {0: np.full(T, np.nan), 1: np.full(T, np.nan)}
    signed_sum = np.zeros(T)
    signed_x = np.zeros(T) if hedged_series else None      # D353: the hedged signed sum, additive option
    ent = np.zeros(T, np.int32)
    skipped = np.zeros(T, np.int32)
    trades = []
    open_ = {0: {}, 1: {}}
    held_mask = {0: np.zeros(n, bool), 1: np.zeros(n, bool)}
    buf = np.empty(n)

    for t in range(first_bar, T):
        r1t, fint, mt, vxt, oct_, mot, sct = r1T[t], finT[t], mkt[t], vxT[t], ocT[t], mkt_oc[t], score_T[t]
        for side in (0, 1):
            held = open_[side]
            hm = held_mask[side]
            sgn = 1.0 if side == 0 else -1.0
            # 1. EXIT on information through t-1
            for row in list(held):
                age, cx, e0 = held[row]
                trig = False
                if exit == "target":
                    u = vxt[row]
                    if u == u and u > 0.0:
                        trig = cx >= x_target * u
                elif exit == "invalidation":
                    s = sct[row]
                    if s == s:
                        trig = (s >= 50.0) if side == 0 else (s <= 50.0)
                cap_hit = age >= cap
                if ((trig or cap_hit) and age > 0) or not fint[row]:
                    st = held.pop(row)
                    hm[row] = False
                    if st[0] > 0:
                        trades.append((row, st[2], st[0], st[1], side))
            # 2. ENTER on the signal known at the close of t-1, most extreme first.
            #    The order is the slot book's gate order exactly (rank_single's
            #    convention): longs by score ascending, ties by row ascending;
            #    shorts by score descending, ties by row DESCENDING (the ranker
            #    reverses an ascending stable sort). Insertion order is the mark
            #    order, and the mark is a np.mean over that order -- so the order
            #    must match for the per-side series to be bit-identical ([ID]).
            cand = np.flatnonzero(sig[side][t] & fint & ~hm)
            if cand.size:
                key = np.where(np.isfinite(sct[cand]), sct[cand], np.inf if side == 0 else -np.inf)
                order = np.argsort(key, kind="stable")
                cand = cand[order] if side == 0 else cand[order[::-1]]
                if n_max is not None:
                    free = n_max - len(held)
                    if free < cand.size:
                        skipped[t] += cand.size - max(free, 0)
                        cand = cand[:max(free, 0)]
                for r in cand:
                    r = int(r)
                    held[r] = [0, 0.0, t]
                    hm[r] = True
                    ent[t] += 1
            # 3. MARK every held position once (np.mean over the buffer, as the slot book)
            if held:
                k = 0
                for row, st in held.items():
                    if st[2] == t:
                        v, m_ = oct_[row], mot
                    else:
                        v, m_ = r1t[row], mt
                    st[0] += 1
                    st[1] += sgn * (v - m_)
                    if hedged_series:
                        signed_x[t] += sgn * (v - m_)
                    buf[k] = v
                    k += 1
                ret[side][t] = float(np.mean(buf[:k]))
                cnt[side][t] = k
                signed_sum[t] += sgn * float(buf[:k].sum())
    n_held = cnt[0] + cnt[1]
    ok_slot = np.isfinite(ret[0]) & np.isfinite(ret[1])
    book_slot = np.where(ok_slot, ret[0] - ret[1], np.nan)
    book_dep = np.where(n_held > 0, signed_sum / np.maximum(n_held, 1), np.nan)
    defined = defined_bars(score_T)
    book_tot = np.where(defined, signed_sum / float(U), np.nan)
    out = dict(trades=trades, cnt0=cnt[0], cnt1=cnt[1], ent=ent, skipped=skipped, held=n_held,
               book_slot=book_slot, mask_slot=ok_slot, book_dep=book_dep, mask_dep=n_held > 0,
               book_tot=book_tot, defined=defined, U=U, exit=exit, cap=cap, n_max=n_max)
    if hedged_series:
        out.update(signed_x=signed_x, book_dep_x=np.where(n_held > 0, signed_x / np.maximum(n_held, 1), np.nan),
                   book_tot_x=np.where(defined, signed_x / float(U), np.nan))
    return out


# ------------------------------------------------------------------ calibration
def concurrency_fixed_hold(sig_long, sig_short, finT, cap, defined):
    """Mean concurrent positions per side under a FIXED hold of `cap` bars, no
    returns read: a signal opens a position that lives `cap` bars or to the
    delisting. Pure counting -- this is what theta is calibrated on."""
    T, n = finT.shape
    out = []
    for sig in (sig_long, sig_short):
        held_until = np.full(n, -1)          # last bar (inclusive) each open position is held
        cnt = np.zeros(T, np.int32)
        for t in range(1, T):
            alive = (held_until >= t) & finT[t]
            held_until[~finT[t]] = -1
            new = sig[t] & finT[t] & ~alive
            held_until[new] = t + cap - 1
            alive = alive | new
            cnt[t] = int(alive.sum())
        out.append(float(cnt[defined].mean()))
    return out


def calibrate_theta(score_T, finT, cap, target=2.0, grid=range(5, 46)):
    """theta such that the fixed-hold event book averages `target` concurrent
    positions per side over the defined bars. Reads NO returns: the signature
    has no place for them. Returns (theta, table)."""
    defined = defined_bars(score_T)
    table = []
    for th in grid:
        with np.errstate(invalid="ignore"):
            sl = score_T <= th
            ss = score_T >= 100.0 - th
        cl, cs = concurrency_fixed_hold(sl, ss, finT, cap, defined)
        table.append((int(th), cl, cs, 0.5 * (cl + cs)))
    best = min(table, key=lambda r: abs(r[3] - target))
    return best[0], table


# ------------------------------------------------------------------ costing
def costed_event(res, HALF, CLOSE, DV, per_share=0.005, crossings=4.0, ann=252.0):
    """D318's basis on the event book, two capital bases.

    rt is the paired round trip on the names HELD (4 x median half-spread at entry
    + 4 x commission); a single position's own round trip is rt / 2 = 2c.
    DEPLOYED: book_dep over bars with a position, cost = rt x entries / (mean held x bars)
              -- G22.costed's arithmetic on the deployed series.
    TOTAL:    book_tot over defined bars (zero when flat), cost = rt x entries / (U x bars).
    """
    tr = res["trades"]
    hs = float(np.nanmedian([HALF[e0, row] for row, e0, _a, _p, _s in tr]))
    px = float(np.nanmedian([CLOSE[e0, row] for row, e0, _a, _p, _s in tr]))
    dv = float(np.nanmedian([DV[e0, row] for row, e0, _a, _p, _s in tr]))
    rt = 4.0 * hs
    rtc = crossings * per_share / px * 1e4
    e = float(res["ent"].sum())
    out = dict(round_trip=rt, commission_rt=rtc, two_c_bp=(rt + rtc) / 2.0, held_half_spread=hs, held_price=px, held_dv=dv,
               entries=int(e), trades=len(tr))

    def stats(b, cost_bp, bars):
        g = float(b.mean()) * 1e4
        v = float(b.std(ddof=1)) * 1e4
        eq = np.cumsum(b)
        return dict(gross_bp=g, vol_bp=v, net_bp=g - cost_bp, cost_bp=cost_bp,
                    sharpe_gross=g / v * np.sqrt(ann) if v > 0 else 0.0, sharpe_net=(g - cost_bp) / v * np.sqrt(ann) if v > 0 else 0.0,
                    maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4, bars=int(bars),
                    breakeven_half_spread_bp_side=None)

    dep_mask = res["mask_dep"]
    bd = res["book_dep"][dep_mask]
    held_mean = float(res["held"][dep_mask].mean())
    turn_dep = e / held_mean / bd.size
    dep = stats(bd, (rt + rtc) * turn_dep, bd.size)
    dep.update(turnover=turn_dep, held_per_bar=held_mean)
    dep["breakeven_half_spread_bp_side"] = (dep["gross_bp"] / turn_dep - rtc) / 4.0
    tot_mask = res["defined"]
    bt = res["book_tot"][tot_mask]
    turn_tot = e / bt.size / float(res["U"])
    tot = stats(bt, (rt + rtc) * turn_tot, bt.size)
    tot.update(turnover=turn_tot, exposure=float((res["held"][tot_mask] > 0).mean()),
               flat_share=float((res["held"][tot_mask] == 0).mean()),
               mean_positions=float(res["held"][tot_mask].mean()),
               mean_positions_long=float(res["cnt0"][tot_mask].mean()), mean_positions_short=float(res["cnt1"][tot_mask].mean()),
               max_positions=int(res["held"][tot_mask].max()))
    tot["breakeven_half_spread_bp_side"] = (tot["gross_bp"] / turn_tot - rtc) / 4.0
    pnl = np.array([t[3] for t in tr])
    out.update(deployed=dep, total=tot, trade_mean_bp=float(pnl.mean()) * 1e4, trade_median_bp=float(np.median(pnl)) * 1e4,
               trade_net_mean_bp=float(pnl.mean()) * 1e4 - out["two_c_bp"], trade_mean_over_2c=float(pnl.mean()) * 1e4 / out["two_c_bp"])
    return out


def contributions_total(res, r1T, ocT):
    """Each closed trade's contribution to book_tot (1/U per position, open fill on the entry bar)."""
    U = float(res["U"])
    out = np.empty(len(res["trades"]))
    for i, (row, e0, age, _p, side) in enumerate(res["trades"]):
        sgn = 1.0 if side == 0 else -1.0
        v = r1T[e0:e0 + age, row].copy()
        v[0] = ocT[e0, row]
        out[i] = sgn * float(np.nan_to_num(v, nan=0.0).sum()) / U
    return out


def rotate_signals(sig_long, sig_short, score_T, finT, rng):
    """Per-name circular rotation in time of the signal (and the score it reads),
    within the name's priced bars. Same count per name, different dates."""
    T, n = finT.shape
    sl, ss, sc = sig_long.copy(), sig_short.copy(), score_T.copy()
    for i in range(n):
        idx = np.flatnonzero(finT[:, i])
        if idx.size < 2:
            continue
        k = int(rng.integers(0, idx.size))
        if k == 0:
            continue
        sl[idx, i] = np.roll(sig_long[idx, i], k)
        ss[idx, i] = np.roll(sig_short[idx, i], k)
        sc[idx, i] = np.roll(score_T[idx, i], k)
    return sl, ss, sc
