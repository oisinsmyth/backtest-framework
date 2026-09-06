"""D354 -- the pair book: a trigger hedged with an equal-weight basket of the ranking's opposite extreme.

Pure numpy + a bar loop, deliberately shaped like scripts/d345_event_book.py::simulate_event so
that, with the basket ABSENT (zero_basket=True), its trigger ledger equals simulate_event's with
a zero market bit-identically at the same n_max (D354 section 5 [ID]). Reads nothing but the
arrays it is handed.

    res = simulate_pairs(A2, trig, score_T, gate, side=0, exit="cap", cap=40, n_max_pairs=2,
                         basket=3, partner="extreme")

Inputs are (T, n) and ALREADY LAGGED: trig[t] and score_T[t] are what is known at the close of
t-1; gate = gate_from(rankT, finT, keep=elig) is lagged by construction (rank_columns lags the
score). side 0 = a LONG trigger hedged with a SHORT basket drawn from gate side 1 (highest rsi);
side 1 = a SHORT trigger hedged with a LONG basket from gate side 0 (lowest rsi). The fill is
the next open (D340): every leg earns ocT on its entry bar and r1T after. Per bar: exits on
information through t-1 (age > 0), then entries most extreme first, then one mark per pair.

Pair return per bar: pr = sgn * (v_trigger - mean(v_basket over live basket legs)), sgn = +1
for side 0, -1 for side 1. NO market term: the pair is self-hedged.

Exits: the trigger's cap (age >= cap) or invalidation (score crosses 50 from the entry side);
the trigger delisting closes the pair; a basket name delisting is dropped from the basket at
its last mark (basket_delist) and the basket continues equal-weight on the rest; a basket that
empties closes the pair (basket_empty).

Entries: trigger events at t on names not held on ANY leg of an open pair, ordered as the event
kernel orders them (side 0: score ascending, ties by row ascending; side 1: score descending,
ties by row descending), up to n_max_pairs - open (overflow counted in `skipped`). The basket
for a pair opened at t is drawn from the same-day opposite-side gate slice
gateF[gateO[opp, t]:gateO[opp, t+1]] (already finT & elig at t, most extreme first), skipping
the trigger and any name held on any leg: partner="extreme" takes the first `basket` names in
gate order; partner="random" draws `basket` names without replacement from the whole slice
under the same exclusions (rng). Fewer than `basket` available -> the pair is not opened
(no_basket).

zero_basket=True: the basket is ABSENT -- no partners are drawn, no basket constraint binds an
entry, the basket return is 0.0. The pair is then the trigger leg alone, and the ledger must
equal simulate_event's with mkt = mkt_oc = 0 ([ID]).

Returned dict:
  pairs         [(row, e0, age, pnl, side, partners, partner_ages)]  closed pairs, summed pr
  pnl_trig      per closed pair, sum of sgn * v_trigger        (the trigger leg's own P&L)
  pnl_basket    per closed pair, sum of -sgn * mean(v_basket)  (the basket leg's own P&L)
  seq           per closed pair, the order in which pairs were OPENED (for the lag audit)
  open_pairs    pairs still open at the last bar, same tuple, age = bars marked so far
  legs          [(row, e0, age, side_of_leg, kind)] kind 0 = trigger, 1 = basket leg; leg_pair
                maps each leg to its index in `pairs`
  book_dep      sum(pr) / n_open, NaN when flat                  (DEPLOYED capital)
  book_tot      sum(pr) / U, NaN before first_bar                (TOTAL capital, U pairs)
  n_open, ent, skipped, no_basket, basket_delist, basket_empty   per bar
"""

from __future__ import annotations

import numpy as np

EXITS = ("cap", "invalidation")
PARTNERS = ("extreme", "random")
MID = 50.0


def simulate_pairs(A2, trig, score_T, gate, *, side, exit, cap, n_max_pairs, basket=3, partner="extreme", rng=None,
                   zero_basket=False, U=4, first_bar=1):
    if exit not in EXITS:
        raise ValueError(f"exit must be one of {EXITS}, got {exit!r}")
    if partner not in PARTNERS:
        raise ValueError(f"partner must be one of {PARTNERS}, got {partner!r}")
    if partner == "random" and rng is None and not zero_basket:
        raise ValueError("partner='random' needs an rng")
    if side not in (0, 1):
        raise ValueError("side must be 0 (long trigger) or 1 (short trigger)")
    r1T, finT, ocT = A2["r1T"], A2["finT"], A2["ocT"]
    T, n = r1T.shape
    sgn = 1.0 if side == 0 else -1.0
    opp = 1 - side
    gateF, gateO = gate["gateF"], gate["gateO"]
    n_open = np.zeros(T, np.int32)
    ent = np.zeros(T, np.int32)
    skipped = np.zeros(T, np.int32)
    no_basket = np.zeros(T, np.int32)
    basket_delist = np.zeros(T, np.int32)
    basket_empty = np.zeros(T, np.int32)
    sum_pr = np.zeros(T)
    pairs, pnl_trig, pnl_basket, seq_out, legs, leg_pair = [], [], [], [], [], []
    open_ = {}                                   # trigger row -> [age, pnl, e0, partners, page, plive, pnl_t, pnl_b, seq]
    held = np.zeros(n, bool)                     # every name on any leg of an open pair
    buf = np.empty(max(basket, 1))
    seq = 0
    # the trigger's events, sparse: rows ascending per bar, exactly np.flatnonzero(trig[t])'s order
    ev_t, ev_i = np.nonzero(trig)
    ev_start = np.searchsorted(ev_t, np.arange(T + 1))

    def close(row, st):
        held[row] = False
        for p in st[3]:
            held[p] = False
        if st[0] > 0:
            k = len(pairs)
            pairs.append((row, st[2], st[0], st[1], side, tuple(st[3]), tuple(st[4])))
            pnl_trig.append(st[6])
            pnl_basket.append(st[7])
            seq_out.append(st[8])
            legs.append((row, st[2], st[0], side, 0))
            leg_pair.append(k)
            for p, a in zip(st[3], st[4]):
                legs.append((p, st[2], a, opp, 1))
                leg_pair.append(k)

    for t in range(first_bar, T):
        r1t, fint, oct_, sct = r1T[t], finT[t], ocT[t], score_T[t]
        # 1. EXIT on information through t-1 (age > 0); the trigger delisting closes the pair at once
        for row in list(open_):
            st = open_[row]
            age = st[0]
            trig_exit = False
            if exit == "invalidation":
                s = sct[row]
                if s == s:
                    trig_exit = (s >= MID) if side == 0 else (s <= MID)
            cap_hit = age >= cap
            if ((trig_exit or cap_hit) and age > 0) or not fint[row]:
                close(row, open_.pop(row))
                continue
            if not zero_basket:
                # a basket name that delists is dropped at its last mark; an empty basket closes the pair
                plive = st[5]
                for j, p in enumerate(st[3]):
                    if plive[j] and not fint[p]:
                        plive[j] = False
                        held[p] = False
                        basket_delist[t] += 1
                if not any(plive):
                    basket_empty[t] += 1
                    close(row, open_.pop(row))
        # 2. ENTER on the trigger known at the close of t-1, most extreme first (the event kernel's order)
        rows = ev_i[ev_start[t]:ev_start[t + 1]]
        cand = rows[fint[rows] & ~held[rows]] if rows.size else rows
        if cand.size:
            key = np.where(np.isfinite(sct[cand]), sct[cand], np.inf if side == 0 else -np.inf)
            order = np.argsort(key, kind="stable")
            cand = cand[order] if side == 0 else cand[order[::-1]]
            free = n_max_pairs - len(open_)
            if free < cand.size:
                skipped[t] += cand.size - max(free, 0)
                cand = cand[:max(free, 0)]
            for r in cand:
                r = int(r)
                if zero_basket:
                    partners = []
                else:
                    pool = gateF[gateO[opp, t]:gateO[opp, t + 1]]
                    if partner == "extreme":
                        partners = []
                        for p in pool:
                            p = int(p)
                            if p != r and not held[p] and fint[p]:
                                partners.append(p)
                                if len(partners) == basket:
                                    break
                    else:
                        avail = pool[(pool != r) & ~held[pool] & fint[pool]]
                        partners = [int(p) for p in rng.choice(avail, size=basket, replace=False)] if avail.size >= basket else []
                    if len(partners) < basket:
                        no_basket[t] += 1
                        continue
                open_[r] = [0, 0.0, t, partners, [0] * len(partners), [True] * len(partners), 0.0, 0.0, seq]
                seq += 1
                held[r] = True
                for p in partners:
                    held[p] = True
                ent[t] += 1
        # 3. MARK every open pair once
        if open_:
            k = 0
            tot = 0.0
            for row, st in open_.items():
                entry = st[2] == t
                v = oct_[row] if entry else r1t[row]
                if zero_basket:
                    vb = 0.0
                else:
                    j = 0
                    page, plive = st[4], st[5]
                    for q, p in enumerate(st[3]):
                        if plive[q]:
                            buf[j] = oct_[p] if entry else r1t[p]
                            j += 1
                            page[q] += 1
                    vb = float(np.mean(buf[:j]))
                pr = sgn * (v - vb)
                st[0] += 1
                st[1] += pr
                st[6] += sgn * v
                st[7] += -sgn * vb
                tot += pr
                k += 1
            n_open[t] = k
            sum_pr[t] = tot
    open_pairs = [(row, st[2], st[0], st[1], side, tuple(st[3]), tuple(st[4])) for row, st in open_.items()]
    open_seq = np.array([st[8] for st in open_.values()], np.int64)
    mask_dep = n_open > 0
    mask_tot = np.zeros(T, bool)
    mask_tot[first_bar:] = True
    book_dep = np.where(mask_dep, sum_pr / np.maximum(n_open, 1), np.nan)
    book_tot = np.where(mask_tot, sum_pr / float(U), np.nan)
    return dict(pairs=pairs, pnl_trig=np.array(pnl_trig), pnl_basket=np.array(pnl_basket), seq=np.array(seq_out, np.int64),
                open_pairs=open_pairs, open_seq=open_seq, legs=legs, leg_pair=np.array(leg_pair, np.int64),
                book_dep=book_dep, mask_dep=mask_dep, book_tot=book_tot, mask_tot=mask_tot, n_open=n_open, ent=ent,
                skipped=skipped, no_basket=no_basket, basket_delist=basket_delist, basket_empty=basket_empty, U=U,
                side=side, exit=exit, cap=cap, n_max_pairs=n_max_pairs, basket=basket, partner=partner, zero_basket=zero_basket,
                first_bar=first_bar)


# ------------------------------------------------------------------ second implementations
def per_bar_from_ledger(pairs, r1T, ocT, side, T, mkt=None, mkt_oc=None):
    """Every pair's per-bar pr rebuilt from (row, e0, age, partners, partner_ages) alone -- the entry bar on ocT,
    later bars on r1T, a basket leg live for its own partner_age bars, the basket the np.mean over the live legs.
    Returns (sum of pr per bar, count per bar, per-pair pnl). With mkt/mkt_oc given, ALSO the trigger leg's
    market-hedged sum sgn * (v_trig - m) per bar (the pair's own trades, hedged as D353 hedges them)."""
    sgn = 1.0 if side == 0 else -1.0
    acc = np.zeros(T)
    cnt = np.zeros(T, np.int32)
    acc_x = np.zeros(T) if mkt is not None else None
    pnl = np.empty(len(pairs))
    for j, (row, e0, age, _p, _s, partners, pages) in enumerate(pairs):
        tot = 0.0
        for a in range(age):
            t = e0 + a
            v = ocT[t, row] if a == 0 else r1T[t, row]
            live = [p for p, pa in zip(partners, pages) if a < pa]
            if live:
                vb = float(np.mean(np.array([ocT[t, p] if a == 0 else r1T[t, p] for p in live])))
            else:
                vb = 0.0
            pr = sgn * (v - vb)
            acc[t] += pr
            cnt[t] += 1
            tot += pr
            if acc_x is not None:
                acc_x[t] += sgn * (v - (mkt_oc[t] if a == 0 else mkt[t]))
        pnl[j] = tot
    return acc, cnt, pnl, acc_x


def rotate_trigger_elig(trig, score_T, elig, rng):
    """N1: per-name circular rotation in time of the trigger (and the score it reads) within the name's
    ELIGIBLE bars (D351's domain). Same count per name, different dates; every rotated event eligible."""
    T, n = elig.shape
    tr, sc = trig.copy(), score_T.copy()
    for i in range(n):
        idx = np.flatnonzero(elig[:, i])
        if idx.size < 2:
            continue
        k = int(rng.integers(0, idx.size))
        if k == 0:
            continue
        tr[idx, i] = np.roll(trig[idx, i], k)
        sc[idx, i] = np.roll(score_T[idx, i], k)
    assert not (tr & ~elig).any(), "[N1] a rotated trigger landed off the floor"
    assert np.array_equal(tr.sum(axis=0), trig.sum(axis=0)), "[N1] per-name trigger count changed"
    return tr, sc


# ------------------------------------------------------------------ costing
def costed_pairs(res, HALF, CLOSE, DV, excl, RAW_CLOSE, per_share=0.005, ann=252.0, tot_mask=None, scheme="gc_htb", BR=None):
    """D318's basis on the pair book, two capital bases, every leg paying its own way.

    Round trip per pair = the trigger leg's 2c (2 x its held median half-spread) + the basket legs' 2c at 1/basket
    each (2 x the held median half-spread over basket legs) + commission per crossing (2 per leg) at each leg's held
    median price, weighted the same way. Borrow (D337's GC/HTB) on every SHORT leg, as a per-bar charge: each short
    leg's rate x its weight (1 for the trigger, 1/basket for a basket leg) / 252 / n_open on the DEPLOYED base and
    / U on the TOTAL base. turnover = pair entries / mean open pairs / bars (deployed), entries / U / bars (total).
    """
    if BR is None:
        raise ValueError("pass the d337_borrow module as BR")
    pairs, legs, leg_pair, basket = res["pairs"], res["legs"], res["leg_pair"], res["basket"]
    T = res["n_open"].size
    kind = np.array([l[4] for l in legs], np.int64)
    side_leg = np.array([l[3] for l in legs], np.int64)
    e0s = np.array([l[1] for l in legs], np.int64)
    rows = np.array([l[0] for l in legs], np.int64)
    ages = np.array([l[2] for l in legs], np.int64)
    trig_m, bask_m = kind == 0, kind == 1

    def med(X, m):
        v = X[e0s[m], rows[m]] if m.any() else np.array([np.nan])
        return float(np.nanmedian(v)) if np.isfinite(v).any() else np.nan

    hs_t, px_t, dv_t = med(HALF, trig_m), med(CLOSE, trig_m), med(DV, trig_m)
    hs_b, px_b, dv_b = med(HALF, bask_m), med(CLOSE, bask_m), med(DV, bask_m)
    raw_t = float(np.nanmedian(RAW_CLOSE[np.maximum(e0s[trig_m] - 1, 0), rows[trig_m]])) if trig_m.any() else np.nan
    raw_b = float(np.nanmedian(RAW_CLOSE[np.maximum(e0s[bask_m] - 1, 0), rows[bask_m]])) if bask_m.any() else np.nan
    has_b = bool(bask_m.any())
    trig_2c = 2.0 * hs_t
    basket_2c = 2.0 * hs_b if has_b else 0.0
    comm_t = 2.0 * per_share / px_t * 1e4
    comm_b = (2.0 * per_share / px_b * 1e4) if has_b else 0.0
    comm = comm_t + comm_b
    rt = trig_2c + basket_2c + comm
    # borrow on every short leg
    trades5 = [(int(r), int(e), int(a), 0.0, int(s)) for r, e, a, s in zip(rows, e0s, ages, side_leg)]
    htb = BR.htb_flags(trades5, excl, CLOSE) if trades5 else np.zeros(0, bool)
    rate = BR.rate_bps(trades5, htb, scheme) if trades5 else np.zeros(0)
    per_leg = BR.borrow_per_trade_bp(trades5, rate) if trades5 else np.zeros(0)
    w = np.where(kind == 0, 1.0, 1.0 / basket)
    acc = np.zeros(T)
    for (r, e, a, s), rr, ww in zip(zip(rows, e0s, ages, side_leg), rate, w):
        if s == 1 and rr > 0.0:
            acc[e:e + a] += rr * ww / ann
    n_open = res["n_open"].astype(float)
    borrow_dep_bar = np.where(n_open > 0, acc / np.maximum(n_open, 1.0), 0.0)
    borrow_tot_bar = acc / float(res["U"])
    per_pair_borrow = np.bincount(leg_pair, weights=per_leg * w, minlength=len(pairs)) if len(pairs) else np.zeros(0)
    short_m = side_leg == 1
    e = float(res["ent"].sum())

    def stats(b, cost_bp, bars):
        g = float(b.mean()) * 1e4
        v = float(b.std(ddof=1)) * 1e4 if b.size > 1 else 0.0
        eq = np.cumsum(b)
        return dict(gross_bp=g, vol_bp=v, net_bp=g - cost_bp, cost_bp=cost_bp,
                    sharpe_gross=g / v * np.sqrt(ann) if v > 0 else 0.0, sharpe_net=(g - cost_bp) / v * np.sqrt(ann) if v > 0 else 0.0,
                    maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4 if b.size else 0.0, bars=int(bars))

    dep_mask = res["mask_dep"]
    bd = res["book_dep"][dep_mask]
    mean_open = float(n_open[dep_mask].mean()) if bd.size else 0.0
    turn_dep = e / mean_open / bd.size if (bd.size and mean_open > 0) else 0.0
    borrow_dep = float(borrow_dep_bar[dep_mask].mean()) if bd.size else 0.0
    dep = stats(bd, rt * turn_dep + borrow_dep, bd.size)
    dep.update(turnover=turn_dep, mean_pairs=mean_open, borrow_bp=borrow_dep, spread_bp=(trig_2c + basket_2c) * turn_dep,
               commission_bp=comm * turn_dep,
               breakeven_half_spread_bp_side=((dep["gross_bp"] - borrow_dep) / turn_dep - comm) / 4.0 if turn_dep > 0 else np.nan)
    tm = res["mask_tot"] if tot_mask is None else (res["mask_tot"] & np.asarray(tot_mask, bool))
    bt = res["book_tot"][tm]
    turn_tot = e / bt.size / float(res["U"]) if bt.size else 0.0
    borrow_tot = float(borrow_tot_bar[tm].mean()) if bt.size else 0.0
    tot = stats(bt, rt * turn_tot + borrow_tot, bt.size)
    tot.update(turnover=turn_tot, exposure=float((n_open[tm] > 0).mean()) if bt.size else 0.0,
               mean_pairs=float(n_open[tm].mean()) if bt.size else 0.0, max_pairs=int(res["n_open"][tm].max()) if bt.size else 0,
               borrow_bp=borrow_tot, spread_bp=(trig_2c + basket_2c) * turn_tot, commission_bp=comm * turn_tot,
               breakeven_half_spread_bp_side=((tot["gross_bp"] - borrow_tot) / turn_tot - comm) / 4.0 if turn_tot > 0 else np.nan)
    pnl = np.array([p[3] for p in pairs]) * 1e4
    pb = per_pair_borrow
    out = dict(trigger_2c=trig_2c, basket_2c=basket_2c, commission_rt=comm, commission_trigger=comm_t, commission_basket=comm_b,
               round_trip=rt, held_half_spread_trigger=hs_t, held_half_spread_basket=hs_b, held_price_trigger=px_t, held_price_basket=px_b,
               held_raw_price_trigger=raw_t, held_raw_price_basket=raw_b, held_dv_trigger=dv_t, held_dv_basket=dv_b,
               borrow_scheme=scheme, borrow_per_pair_bp=float(pb.mean()) if pb.size else 0.0,
               htb_share_short_legs=float(htb[short_m].mean()) if short_m.any() else 0.0, short_legs=int(short_m.sum()),
               entries=int(e), pairs=len(pairs), open_at_end=len(res["open_pairs"]), skipped=int(res["skipped"].sum()),
               no_basket=int(res["no_basket"].sum()), basket_delist=int(res["basket_delist"].sum()), basket_empty=int(res["basket_empty"].sum()),
               deployed=dep, total=tot,
               pair_mean_bp=float(pnl.mean()) if pnl.size else np.nan, pair_median_bp=float(np.median(pnl)) if pnl.size else np.nan,
               pair_net_mean_bp=(float(pnl.mean()) - rt - float(pb.mean())) if pnl.size else np.nan,
               pair_breakeven_half_spread_bp_side=((float(pnl.mean()) - comm - float(pb.mean())) / 4.0) if pnl.size else np.nan,
               trigger_leg_mean_bp=float(res["pnl_trig"].mean()) * 1e4 if pnl.size else np.nan,
               basket_leg_mean_bp=float(res["pnl_basket"].mean()) * 1e4 if pnl.size else np.nan,
               hold_mean=float(np.mean([p[2] for p in pairs])) if pairs else np.nan)
    return out
