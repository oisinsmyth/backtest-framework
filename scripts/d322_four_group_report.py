"""D322 -- the four-group report on the current best book. A REPORT, not a study.

    uv run python scripts/d322_four_group_report.py --selftest
    uv run python scripts/d322_four_group_report.py [--draws 200]

WHAT THIS IS. CLAUDE.md's "Reporting a result" demands four groups and says a
number without them is not a result. The programme's current best book -- D306's
construction at N_eff = 2 with D303's market-referenced target -- has never had
them. Groups 2 and 3 have carried the note "inherited from D310" since D313, and
D310 is a DIFFERENT AND WORSE CONSTRUCTION (STACK.md section 1, axis C): 1.73x the
turnover and a net that flips sign under D317's re-costing. So the inheritance was
never valid, and nobody has computed groups 2 and 3 for the book that actually
runs.

WHAT THIS IS NOT. It scores no new rule, sweeps no parameter, and closes nothing.
Both cells were fixed before this file existed -- BASE is D306's published
`N=2/target` and dv28 is D321's published `dv28`, at a threshold D321 fixed in
advance. **R8 does not apply: there is no hypothesis here to pre-register.** If
this runner ever grows a grid, a threshold search or a promotion rule, it stops
being a report and needs a pre-registration of its own.

THE TWO CELLS, side by side, because STACK.md's dv28 guard is not optional:
dv28 is CARRIED, NOT PROMOTED at p = 0.0100 unconfirmed, and any study using it
must report the cell with AND without it.

THE COST BASIS IS D318's AND IS NOT REINVENTED HERE
===================================================
  spread      per-cell round trip = 4 x median(half-spread at entry over the
              trades this cell actually took). Corwin-Schultz off the OHLC, never
              a fee assumption (D285 missed a guessed bar by 0.65).
  commission  IBKR per-share, 4 x (0.005 / held median price) x 1e4.
  turnover    entries / names HELD / bars -- NOT the nominal slot count. D306's
              simulator weights 1/n_t, so a starved gate is a NARROWER BOOK AT
              FULL NOTIONAL, not a book partly in cash. D321's [F], and D320
              section 2 is where both BH survivors died of the nominal form.

THE UNIT ARITHMETIC, stated once because two groups depend on it
================================================================
`rt = 4 x half` is cost per unit of turnover where turnover divides by the names
HELD (both legs). A position's weight in the book is `1 / (held/2)`, so its cost
expressed in ITS OWN notional is `(rt / held) x (held / 2) = rt / 2`. **The
round-trip cost bar `2c` against which a trade's mean move is judged is therefore
`rt_total / 2`, not `rt_total`.** The same factor two is why the mean TRADE P&L
(+68 bp) is about twice the mean trade CONTRIBUTION to the book (+34 bp): group 2
reports the position-level quantity and group 1's reconciliation the book-level
one. Assertion [2] holds them together rather than assuming it.

ASSERTIONS
==========
  [1]  BASE reproduces d306_width_exits.json's `N=2/target` gross AND net, and
       dv28 reproduces d321_dv_sweep.json's `dv28` net AND net Sharpe, to 1e-9.
  [2]  the trade ledger reconciles to the book: sum of per-trade contributions
       over bars equals gross bp/bar, up to the positions still OPEN at the end
       of the run. D307c chased a 0.1530 bp residual that was exactly that.
  [3]  the both-tail trim is SYMMETRIC -- n dropped from the top equals n dropped
       from the bottom. D307's withdrawn "lottery book" verdict came from a
       one-sided trim, and the correction record is why this assertion exists.
  [4]  a book handed free money on 200 bars inside the mask makes [1] RAISE.
       A self-test that cannot fail is worse than none.

Group 4 re-runs D306's own rank-rotation null (seeded identically, so assertion
[N] holds it to D306's published p95 bit-for-bit) to obtain the p50 D306 never
published, and QUOTES D321's exclusion-rotation null for dv28 rather than
re-running it.
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


S = _load("d321", "run_d321_dv_sweep.py")       # the dv sweep: keep masks, PCTS
X = S.X                                          # d320: keep_mask, gate_with
W, D, M, SP = X.W, X.D, X.M, X.SP                # d306 simulator and loaders

DEPTH = 2
DV_PCT = 28.0
ANN = 252.0
PER_SHARE, CROSSINGS = X.PER_SHARE, X.CROSSINGS
META = REPO / "data" / "fixtures" / "us_shorts_daily_raw.meta.json"
OUT = REPO / "data" / "d322_four_group_report.json"


# ------------------------------------------------------------------ costing
def costed(res, G4):
    """D318's basis, per cell. Mirrors d321's `score` -- assertion [1] is what
    holds it there rather than a shared import, because a report that silently
    inherited the sweep's costing could not detect the sweep being wrong."""
    HALF, CLOSE, DV, _ = G4
    ok = res["mask"]
    b = res["book"][ok]
    bars = b.size
    e = int(res["ent"][ok].sum())
    held = float(res["held"][ok].mean())
    hs = X.held_median(res, HALF)
    px = X.held_median(res, CLOSE)
    rt = 4.0 * hs
    rtc = CROSSINGS * PER_SHARE / px * 1e4 if px > 0 else np.nan
    turn = e / held / bars                       # [F]: names HELD, not slots
    g = float(b.mean()) * 1e4
    v = float(b.std(ddof=1)) * 1e4
    net = g - (rt + rtc) * turn
    eq = np.cumsum(b)
    return dict(
        gross_bp=g, vol_bp=v, net_bp=net,
        sharpe_gross=g / v * np.sqrt(ANN) if v > 0 else 0.0,
        sharpe_net=net / v * np.sqrt(ANN) if v > 0 else 0.0,
        round_trip=rt, commission_rt=rtc, cost_bp=(rt + rtc) * turn,
        turnover=turn, held_per_bar=held, fill=held / (2.0 * DEPTH),
        held_half_spread=hs, held_price=px, held_dv=X.held_median(res, DV),
        maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4,
        entries=e, bars=bars, trades=len(res["trades"]))


def unattributed(res, trades=None):
    """Position-bars held by the book that NO closed trade covers.

    The exact half of assertion [2]. `cnt0`/`cnt1` count positions held per bar
    per leg; a ledger entry `(row, e0, age, pnl, side)` covers bars
    `[e0, e0 + age)`. Rebuilding the counts from the ledger and differencing
    says precisely which held bars the ledger misses -- and the answer must be
    "only the tail of the positions still open at the last bar", never a hole
    in the middle. Returns (gap position-bars, earliest gap bar, T).
    """
    T = res["mask"].size
    trades = res["trades"] if trades is None else trades
    gap_bars, first = 0.0, T
    for side in (0, 1):
        d = np.zeros(T + 2)
        for row, e0, age, _p, s in trades:
            if s == side:
                d[e0] += 1
                d[min(e0 + age, T + 1)] -= 1
        rebuilt = np.cumsum(d)[:T]
        gap = np.asarray(res[f"cnt{side}"], float) - rebuilt
        assert (gap >= -1e-9).all(), \
            "[2] the ledger claims a position the book never held"
        nz = np.flatnonzero(gap > 0)
        if nz.size:
            first = min(first, int(nz.min()))
            gap_bars += float(gap.sum())
    return gap_bars, first, T


def contributions(res, r1T):
    """Each closed trade's contribution to the BOOK, in return units.

    Second implementation of D307c's decomposition, kept here so assertion [2]
    is a check and not an import. Two subtleties, both of which cost D307c a
    debugging pass: the weight is 1/n_t for the trade's OWN LEG and never
    1/depth, because a delisting can leave a leg short of its slots; and the
    weight is ZERO off the book's mask, because a bar where the other leg is
    empty contributes to no book return and must contribute to no trade.
    """
    n = {0: np.asarray(res["cnt0"], float), 1: np.asarray(res["cnt1"], float)}
    m = res["mask"].astype(float)
    w = {s: np.where(n[s] > 0, 1.0 / np.maximum(n[s], 1), 0.0) * m for s in (0, 1)}
    out = np.empty(len(res["trades"]))
    for i, (row, e0, age, _pnl, side) in enumerate(res["trades"]):
        sgn = 1.0 if side == 0 else -1.0
        sl = slice(e0, e0 + age)
        v = np.nan_to_num(r1T[sl, row], nan=0.0)
        out[i] = sgn * float(np.dot(v, w[side][sl]))
    return out


# ------------------------------------------------------------------ group 1
def group1(res, c, contrib, r1T):
    """Performance, NET AND GROSS side by side. Gross separates cost failure
    from signal failure -- they take opposite fixes."""
    pnl = np.array([t[3] for t in res["trades"]])
    rt_total = c["round_trip"] + c["commission_rt"]
    two_c = rt_total / 2.0                       # see the module docstring
    # Breakeven: the half-spread per side at which net = 0, commission held at
    # its measured value. Reported against what the HELD names actually measure.
    be_half = (c["gross_bp"] / c["turnover"] - c["commission_rt"]) / 4.0
    return dict(
        gross_bp_bar=c["gross_bp"], net_bp_bar=c["net_bp"],
        vol_bp_bar=c["vol_bp"],
        sharpe_gross=c["sharpe_gross"], sharpe_net=c["sharpe_net"],
        t_gross=c["gross_bp"] / (c["vol_bp"] / np.sqrt(c["bars"])),
        maxdd_bp=c["maxdd_bp"],
        ann_gross_pct=c["gross_bp"] * ANN / 100.0,
        ann_net_pct=c["net_bp"] * ANN / 100.0,
        bars=c["bars"], bars_in_panel=int(r1T.shape[0]),
        exposure_bars=c["bars"] / float(r1T.shape[0]),
        held_per_bar=c["held_per_bar"], fill=c["fill"],
        turnover_held=c["turnover"],
        cost_bp_bar=c["cost_bp"], round_trip_spread=c["round_trip"],
        round_trip_commission=c["commission_rt"], round_trip_total=rt_total,
        two_c_bp=two_c,
        trade_mean_bp=float(pnl.mean()) * 1e4,
        trade_mean_over_2c=float(pnl.mean()) * 1e4 / two_c,
        trade_net_mean_bp=float(pnl.mean()) * 1e4 - two_c,
        contribution_mean_bp=float(contrib.mean()) * 1e4,
        held_half_spread=c["held_half_spread"],
        breakeven_half_spread_bp_side=be_half,
        breakeven_multiple=be_half / c["held_half_spread"],
        held_price=c["held_price"], held_dollar_volume=c["held_dv"])


# ------------------------------------------------------------------ group 2
def trim_sym(p, k_top, k_bot):
    """Drop the k_bot smallest and k_top largest. Kept general ON PURPOSE so
    assertion [3] has something to reject: a symmetric trim asserted in prose
    is exactly what produced D307's withdrawn verdict."""
    s = np.sort(p)
    n = s.size
    assert k_top + k_bot < n, "the trim would remove the whole sample"
    return s[k_bot:n - k_top], int(k_top), int(k_bot)


def group2(res):
    """Trade distribution, with BOTH tails trimmed and all three means.

    Read D307-CORRECTION before touching this. The one-sided ex-top-1% mean is a
    FLAG, not a verdict: on a two-sided fat-tailed book it always frightens, and
    at N=19 the LOSING tail was the larger one (-181% against +161%).
    """
    p = np.array([t[3] for t in res["trades"]])
    age = np.array([t[2] for t in res["trades"]], float)
    n = p.size
    k = max(1, n // 100)
    s = np.sort(p)
    mid, kt, kb = trim_sym(p, k, k)
    assert kt == kb, f"[3] the trim is one-sided: {kt} top against {kb} bottom"
    win, loss = p[p > 0], p[p <= 0]
    tot = float(p.sum())
    m, med = float(p.mean()) * 1e4, float(np.median(p)) * 1e4
    return dict(
        n=int(n), k_trim=int(k),
        n_dropped_top=kt, n_dropped_bottom=kb,
        mean_bp=m, median_bp=med,
        mean_below_median=bool(m < med),
        mean_ex_top_bp=float(s[:n - k].mean()) * 1e4,
        mean_ex_bottom_bp=float(s[k:].mean()) * 1e4,
        mean_trimmed_bp=float(mid.mean()) * 1e4,
        win_rate=float((p > 0).mean()),
        payoff=float(win.mean() / abs(loss.mean())) if loss.size else None,
        mean_win_bp=float(win.mean()) * 1e4,
        mean_loss_bp=float(loss.mean()) * 1e4,
        holding_run_mean=float(age.mean()), holding_run_median=float(np.median(age)),
        holding_run_max=float(age.max()),
        skew=float(((p - p.mean()) ** 3).mean() / p.std() ** 3),
        kurtosis_raw=float(((p - p.mean()) ** 4).mean() / p.std() ** 4),
        top1_share=float(s[-k:].sum() / tot) if tot else None,
        bottom1_share=float(s[:k].sum() / tot) if tot else None,
        top1_mean_bp=float(s[-k:].mean()) * 1e4,
        bottom1_mean_bp=float(s[:k].mean()) * 1e4,
        drop_winners_moves=float(s[:n - k].mean() - p.mean()) * 1e4,
        drop_losers_moves=float(s[k:].mean() - p.mean()) * 1e4)


# ------------------------------------------------------------------ group 3
def split(contrib, pnl, sel, total, half, price):
    """One cut of the trade ledger, charged ITS OWN cost.

    Share of P&L is on CONTRIBUTIONS, because that is what reconciles to the
    book; the mean per trade is on the raw position P&L, because that is what
    group 2 and the `2c` bar speak. **Each cut carries its own `2c`**, built
    from the half-spread and price of the names IN THAT CUT -- charging the
    book's average would hide exactly the effect the price cut exists to find,
    since cost in bp scales inversely with price and that is what killed D284.
    """
    if not sel.any():
        return dict(n=0, share_pnl=0.0, mean_bp=None, contrib_bp=0.0)
    h = half[sel]
    p = price[sel]
    hm = float(np.nanmedian(h[np.isfinite(h)])) if np.isfinite(h).any() else np.nan
    pm = float(np.nanmedian(p[np.isfinite(p)])) if np.isfinite(p).any() else np.nan
    two_c = (4.0 * hm + CROSSINGS * PER_SHARE / pm * 1e4) / 2.0
    m = float(pnl[sel].mean()) * 1e4
    return dict(n=int(sel.sum()), share_pnl=float(contrib[sel].sum() / total),
                mean_bp=m, contrib_bp=float(contrib[sel].sum()) * 1e4,
                half_spread=hm, price=pm, two_c_bp=two_c,
                mean_over_2c=m / two_c if two_c > 0 else None,
                net_per_trade_bp=m - two_c)


def group3(res, contrib, c, years, dead, CLOSE, HALF):
    """What the winners depend on: names, years, dead-vs-alive, era, PRICE.

    Price is here because cost in bp scales inversely with it -- that cut killed
    D284 -- and this book's whole dv28 variant is a cost story.
    """
    pnl = np.array([t[3] for t in res["trades"]])
    rows = np.array([t[0] for t in res["trades"]])
    ent = np.array([t[1] for t in res["trades"]])
    total = float(contrib.sum())

    by = {}
    for r, v in zip(rows, contrib):
        by[int(r)] = by.get(int(r), 0.0) + float(v)
    v = np.sort(np.array(list(by.values())))[::-1]
    cum = np.cumsum(v)

    # the same cut on RAW trade P&L, so the number is comparable with D307's
    byr = {}
    for r, x in zip(rows, pnl):
        byr[int(r)] = byr.get(int(r), 0.0) + float(x)
    vr = np.sort(np.array(list(byr.values())))[::-1]

    ok = res["mask"]
    b = res["book"][ok]
    yb = years[ok]
    gross_yr, net_yr = {}, {}
    for u in np.unique(yb):
        g = float(b[yb == u].mean()) * 1e4
        gross_yr[int(u)] = g
        net_yr[int(u)] = g - c["cost_bp"]         # cost is flat per bar by design

    # Price and half-spread AT ENTRY -- the only values the rule could have seen
    # (R9: a conditioning variable is lagged exactly as the rule would lag it,
    # and the entry bar is where the cost is actually paid).
    price = np.array([CLOSE[e, r] for r, e in zip(rows, ent)], float)
    hsp = np.array([HALF[e, r] for r, e in zip(rows, ent)], float)
    fin = np.isfinite(price)
    q1, q2 = np.percentile(price[fin], [33.3333, 66.6667])
    order = np.flatnonzero(res["mask"])
    mid_bar = int(order[res["mask"].sum() // 2])

    def cut(sel):
        return split(contrib, pnl, sel, total, hsp, price)

    return dict(
        names=len(by),
        names_to_half_pnl=int(np.searchsorted(cum, 0.5 * total) + 1),
        top1_name_share=float(v[0] / total),
        top5_name_share=float(v[:5].sum() / total),
        top10_name_share=float(v[:10].sum() / total),
        names_to_half_pnl_rawpnl=int(
            np.searchsorted(np.cumsum(vr), 0.5 * vr.sum()) + 1),
        top1_name_share_rawpnl=float(vr[0] / vr.sum()),
        years=len(gross_yr),
        years_profitable_gross=sum(1 for x in gross_yr.values() if x > 0),
        years_profitable_net=sum(1 for x in net_yr.values() if x > 0),
        gross_by_year=gross_yr, net_by_year=net_yr,
        dead_names_in_panel=int(dead.sum()),
        dead=cut(dead[rows]), alive=cut(~dead[rows]),
        dead_trade_share=float(dead[rows].mean()),
        era_first_half=cut(ent < mid_bar), era_second_half=cut(ent >= mid_bar),
        era_split_bar=mid_bar,
        price_cuts=[float(q1), float(q2)],
        price_low=cut(fin & (price <= q1)),
        price_mid=cut(fin & (price > q1) & (price <= q2)),
        price_high=cut(fin & (price > q2)))


# ------------------------------------------------------------------ group 4
def rank_rotation_null(A, gate, G4, draws, seed_key):
    """D300/D306's null: circularly shift the rank assignment inside the 25-name
    gate. Seeded exactly as D306 seeded it, so assertion [N] can hold the result
    to D306's published p95 rather than to a re-derived one."""
    rng = np.random.default_rng(seed_key)
    offs = rng.choice(np.arange(1, W.N_BASE), size=draws, replace=True)
    g, sg, sn = [], [], []
    for s in offs:
        r = W.simulate(A, gate, DEPTH, True, shift=int(s))
        ok = r["mask"]
        if int(ok.sum()) < 200:
            continue
        b = r["book"][ok]
        g.append(float(b.mean()) * 1e4)
        sg.append(float(b.mean() / b.std(ddof=1) * np.sqrt(ANN)))
        sn.append(costed(r, G4)["sharpe_net"])
    return np.array(g), np.array(sg), np.array(sn)


def dist(nl, score):
    return dict(p50=float(np.median(nl)), p95=float(np.quantile(nl, .95)),
                p05=float(np.quantile(nl, .05)), max=float(nl.max()),
                score=float(score), draws=int(nl.size),
                p=float((nl >= score).sum() + 1) / (nl.size + 1))


# --------------------------------------------------------------- assertions
def assertions(cells, d306, d321, A, G4):
    print("\nASSERTIONS")

    # [1] REPRODUCTION. BASE against D306's own basis (spread only, nominal
    #     turnover); dv28 against D321's (spread + commission, held turnover).
    ref306 = d306["N=2/target"]
    b306 = cells["BASE"]["d306_basis"]
    e_g = abs(b306["gross_bp"] - ref306["gross_bp"])
    e_n = abs(b306["net_bp"] - ref306["net_bp"])
    ref321 = d321["cells"]["dv28"]
    c28 = cells["BASE+dv28"]["cost"]
    e_dn = abs(c28["net_bp"] - ref321["net_bp"])
    e_ds = abs(c28["sharpe_net"] - ref321["sharpe_net"])
    ctl = d321["control"]
    e_cn = abs(cells["BASE"]["cost"]["net_bp"] - ctl["net_bp"])
    worst = max(e_g, e_n, e_dn, e_ds, e_cn)
    assert worst < 1e-9, (
        f"[1] reproduction fails by {worst:.2e}: D306 gross {e_g:.2e} net "
        f"{e_n:.2e}; D321 control net {e_cn:.2e}, dv28 net {e_dn:.2e} "
        f"netSHRP {e_ds:.2e}")
    print(f"    [1] BASE reproduces D306's N=2/target gross {ref306['gross_bp']:+.4f} "
          f"and net {ref306['net_bp']:+.4f} ({max(e_g, e_n):.1e}); dv28 reproduces "
          f"D321's\n        net {ref321['net_bp']:+.4f} and netSHRP "
          f"{ref321['sharpe_net']:+.4f} ({max(e_dn, e_ds):.1e}), and BASE "
          f"reproduces D321's control net ({e_cn:.1e})")

    # [2] LEDGER RECONCILIATION. Stated relation, then checked:
    #     sum(contributions) / bars * 1e4  ==  gross bp/bar,  up to the
    #     positions still OPEN at the last bar, which are in the book and in no
    #     closed trade. D307c's 0.1530 bp residual was exactly that.
    for nm, cc in cells.items():
        res = cc["res"]
        attributed = float(cc["contrib"].sum()) / cc["cost"]["bars"] * 1e4
        resid = cc["cost"]["gross_bp"] - attributed
        n_open = int(res["ent"].sum()) - len(res["trades"])
        gap_bars, first, T = unattributed(res)
        cc.update(residual_bp=resid, open_positions=n_open,
                  unattributed_position_bars=gap_bars,
                  first_unattributed_bar=first)
        # The book holds at most 2 x DEPTH names, so at most that many can be
        # open when the run ends -- and every unattributed held bar must lie in
        # the last BASE_HOLD bars, because a position is capped at that age.
        assert 0 <= n_open <= 2 * DEPTH, \
            f"[2] {nm}: {n_open} positions unaccounted, more than the {2 * DEPTH} slots"
        assert first >= T - W.BASE_HOLD, (
            f"[2] {nm}: the ledger misses held bars from bar {first} of {T} -- "
            f"that is a HOLE, not the open tail")
        assert abs(resid) < 1.0, \
            f"[2] {nm}: {resid:.4f} bp unattributed is too large for {gap_bars:.0f} bars"
        # and the position/book factor of two must hold, or the `2c` bar is wrong
        ratio = float(np.mean([t[3] for t in res["trades"]])) / \
            float(cc["contrib"].mean())
        cc["pnl_over_contribution"] = ratio
        assert 1.5 < ratio < 2.5, \
            f"[2] {nm}: trade P&L is {ratio:.2f}x its contribution, not ~1/weight"
        print(f"    [2] {nm}: {len(res['trades']):,} closed trades reconstruct "
              f"gross to {resid:+.4f} bp. The gap is {n_open} positions still OPEN "
              f"at the end\n        ({gap_bars:.0f} held position-bars, none before "
              f"bar {first} of {T}, i.e. inside the last {T - first} bars). Trade "
              f"P&L is {ratio:.2f}x its\n        book contribution -- the 1/weight "
              f"factor the 2c bar uses.")
    # and the accounting must REJECT a ledger with a trade removed from the middle
    broke = False
    try:
        res = cells["BASE"]["res"]
        short = [t for i, t in enumerate(res["trades"]) if i != len(res["trades"]) // 2]
        _, first, T = unattributed(res, short)
        assert first >= T - W.BASE_HOLD
    except AssertionError:
        broke = True
    assert broke, "[2] the position-bar accounting accepted a ledger missing a trade"
    print("    [2] and the accounting REJECTS a ledger with one mid-run trade "
          "removed")

    # [3] THE TRIM IS SYMMETRIC, and the check must be able to reject.
    p = np.array([t[3] for t in cells["BASE"]["res"]["trades"]])
    k = max(1, p.size // 100)
    broke = False
    try:
        _, kt, kb = trim_sym(p, k, k + 1)
        assert kt == kb
    except AssertionError:
        broke = True
    assert broke, "[3] a 1-off asymmetric trim passed the symmetry check"
    for nm, cc in cells.items():
        assert cc["g2"]["n_dropped_top"] == cc["g2"]["n_dropped_bottom"]
    print(f"    [3] both-tail trim is symmetric at k={k} in every cell, and the "
          f"check REJECTS a trim one deeper on the bottom")

    # [4] THE SELF-TEST MUST RAISE. Free money on 200 bars inside the mask.
    broke = False
    try:
        r = cells["BASE"]["res"]
        bk = r["book"].copy()
        bk[np.flatnonzero(r["mask"])[:200]] += 5e-4
        bad = costed(dict(r, book=bk), G4)
        assert abs(bad["gross_bp"] - ref306["gross_bp"]) < 1e-9
        assert abs(bad["net_bp"] - d321["control"]["net_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[4] [1] passed a book handed free money inside the mask"
    print("    [4] and [1] RAISES on a book handed free money on 200 bars inside "
          "the mask")

    # [S] SPREAD BASIS -- the round trip comes from the names HELD, and using the
    #     universe median instead must be REJECTED. A flat 1.10x bar would be the
    #     wrong test for dv28, whose whole mechanism is to hold cheaper names;
    #     what must hold is that the held names are still wider than the universe
    #     and that the basis choice is worth more than a bp.
    uni = 4.0 * float(np.nanmedian(G4[0][np.isfinite(G4[0])]))
    for nm, cc in cells.items():
        c = cc["cost"]
        assert c["round_trip"] > uni, \
            f"[S] {nm}'s held rt {c['round_trip']:.1f} is below the universe " \
            f"median {uni:.1f} -- the held-name basis is not conservative"
        cc["net_on_universe_basis_bp"] = \
            c["gross_bp"] - (uni + c["commission_rt"]) * c["turnover"]
    b, v = cells["BASE"], cells["BASE+dv28"]
    assert b["net_on_universe_basis_bp"] - b["cost"]["net_bp"] > 1.0, \
        "[S] the universe basis does not flatter BASE -- the check cannot fail"
    # And the basis must be PER CELL: a common round trip would define dv28's
    # whole mechanism away (D320 section 5, which inverts D307 on purpose).
    assert b["cost"]["round_trip"] - v["cost"]["round_trip"] > 5.0, \
        "[S] the two cells' held round trips are too close to need separate bases"
    print(f"    [S] SPREAD BASIS: held rt {b['cost']['round_trip']:.2f} (BASE) vs "
          f"{v['cost']['round_trip']:.2f} (dv28), both above the universe median "
          f"{uni:.2f}.\n        Charging the universe median instead would flatter "
          f"net by "
          f"{b['net_on_universe_basis_bp'] - b['cost']['net_bp']:+.2f} (BASE) and "
          f"{v['net_on_universe_basis_bp'] - v['cost']['net_bp']:+.2f} (dv28) bp/bar"
          f"\n        -- and note dv28 pulls the held names to within "
          f"{v['cost']['round_trip'] - uni:.2f} bp of the universe's own spread")

    # [F] TURNOVER divides by the names HELD. It must matter for dv28 and it
    #     must be inert for BASE, which fills every slot.
    c28 = cells["BASE+dv28"]["cost"]
    nom = c28["entries"] / float(DEPTH) / 2.0 / c28["bars"]
    assert abs(c28["turnover"] / nom - 1.0 / c28["fill"]) < 1e-9
    assert c28["turnover"] > nom * 1.05, "[F] the fill correction is inert on dv28"
    assert abs(cells["BASE"]["cost"]["fill"] - 1.0) < 1e-12, "[F] BASE is starved"
    print(f"    [F] dv28 fills {c28['fill']:.0%}, so turnover on names HELD is "
          f"{c28['turnover'] / nom:.3f}x the nominal form; BASE fills 100% and the "
          f"correction is inert there")


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()

    print("D322  the four-group report -- REPORT, not a study; nothing "
          "pre-registered, nothing closed")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    r1T = np.asarray(A["r1T"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel.closes.T)
    VOL = np.full(CLOSE.shape, np.nan)
    sym = {s: i for i, s in enumerate(panel.symbols)}
    pos = {d: i for i, d in enumerate(panel.dates)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                VOL[t, i] = st.bar.volume
    finT = np.asarray(A["finT"])
    DV = X.roll_mean_T(CLOSE * VOL)
    G4 = (HALF, CLOSE, DV, finT)

    years = np.array([int(d[:4]) for d in panel.dates])
    meta = json.loads(META.read_text())["symbols"]
    # D279's definition: a name carrying a delistingDate in the fixture's own
    # metadata. Not D291's "live window ends early", which also catches names
    # that merely stopped trading.
    dead = np.array([bool(meta.get(s, {}).get("delistingDate"))
                     for s in panel.symbols])
    d306 = json.loads((REPO / "data" / "d306_width_exits.json").read_text())["cells"]
    d321 = json.loads((REPO / "data" / "d321_dv_sweep.json").read_text())
    print(f"  panel {finT.shape}, {int(dead.sum())} delisted names "
          f"({time.time() - t0:.0f}s)")

    # ---- the two cells, fixed in advance ----------------------------------
    ones = np.ones(finT.shape, bool)
    keep28 = X.keep_mask(DV, finT, DV_PCT, True)
    cells = {}
    for nm, keep in (("BASE", ones), ("BASE+dv28", keep28)):
        gate = G if nm == "BASE" else X.gate_with(A, keep)
        res = W.simulate(A, gate, DEPTH, True)
        c = costed(res, G4)
        cells[nm] = dict(res=res, gate=gate, cost=c,
                         contrib=contributions(res, r1T),
                         # D306's own basis, for assertion [1] only
                         d306_basis=W.stats(res, DEPTH, np.ones(r1T.shape[0]),
                                            W.held_rt(res, HALF), HALF))
        cells[nm]["g2"] = group2(res)
    print(f"  both cells simulated ({time.time() - t0:.0f}s)")

    assertions(cells, d306, d321, A, G4)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    for nm, cc in cells.items():
        cc["g1"] = group1(cc["res"], cc["cost"], cc["contrib"], r1T)
        cc["g3"] = group3(cc["res"], cc["contrib"], cc["cost"], years, dead,
                          CLOSE, HALF)

    ROW = "  %-33s %15s %15s"

    def table(d1, d2, spec):
        """spec = (label, key, formatter). One formatter, applied to both cells,
        so a unit can never differ between the two columns by accident."""
        print(ROW % ("", "BASE", "BASE + dv28"))
        print("  " + "-" * 65)
        for label, key, fn in spec:
            print(ROW % (label, fn(d1[key]), fn(d2[key])))

    def f2(v):
        return "%+.2f" % v

    def f1(v):
        return "%+.1f" % v

    def f3(v):
        return "%+.3f" % v

    def pc(v):
        return "%.1f%%" % (100 * v)

    # ---- GROUP 1 ----------------------------------------------------------
    B, V = cells["BASE"]["g1"], cells["BASE+dv28"]["g1"]
    print("\n" + "=" * 78)
    print("GROUP 1 -- PERFORMANCE, NET AND GROSS SIDE BY SIDE")
    print("=" * 78)
    table(B, V, (
        ("gross bp/bar", "gross_bp_bar", f2),
        ("cost bp/bar", "cost_bp_bar", lambda v: "%.2f" % v),
        ("NET bp/bar", "net_bp_bar", f2),
        ("vol bp/bar", "vol_bp_bar", lambda v: "%.1f" % v),
        ("gross Sharpe (ann)", "sharpe_gross", f3),
        ("NET Sharpe (ann)", "sharpe_net", f3),
        ("gross t", "t_gross", f2),
        ("annualised gross %", "ann_gross_pct", f2),
        ("annualised NET %", "ann_net_pct", f2),
        ("maxDD bp", "maxdd_bp", lambda v: "%.0f" % v),
        ("bars with a live book", "bars", lambda v: "%d" % v),
        ("exposure (bars / panel)", "exposure_bars", pc),
        ("names held per bar", "held_per_bar", lambda v: "%.2f" % v),
        ("fill of %d slots" % (2 * DEPTH), "fill", pc),
        ("turnover/bar (names HELD)", "turnover_held", lambda v: "%.4f" % v),
        ("held half-spread bp/side", "held_half_spread", lambda v: "%.2f" % v),
        ("held median price", "held_price", lambda v: "$%.2f" % v),
        ("spread round trip", "round_trip_spread", lambda v: "%.2f" % v),
        ("commission round trip", "round_trip_commission", lambda v: "%.2f" % v),
        ("2c = rt_total / 2", "two_c_bp", lambda v: "%.2f" % v),
        ("mean move per TRADE bp", "trade_mean_bp", f2),
        ("mean move / 2c", "trade_mean_over_2c", lambda v: "%.2fx" % v),
        ("net per trade bp", "trade_net_mean_bp", f2),
        ("BREAKEVEN half-spread /side", "breakeven_half_spread_bp_side",
         lambda v: "%.2f" % v),
        ("breakeven / measured", "breakeven_multiple", lambda v: "%.2fx" % v)))

    print("\n  Gross is all but identical (%+.2f vs %+.2f) and held price barely "
          "moves\n  ($%.0f vs $%.0f): the entire dv28 difference is COST."
          % (B["gross_bp_bar"], V["gross_bp_bar"], B["held_price"], V["held_price"]))

    # ---- GROUP 2 ----------------------------------------------------------
    print("\n" + "=" * 78)
    print("GROUP 2 -- TRADE DISTRIBUTION, BOTH TAILS TRIMMED")
    print("=" * 78)
    print("  the ex-top-1% mean alone is a FLAG, not a verdict (D307-CORRECTION)")
    B2, V2 = cells["BASE"]["g2"], cells["BASE+dv28"]["g2"]
    table(B2, V2, (
        ("trades", "n", lambda v: "%d" % v),
        ("mean bp", "mean_bp", f1),
        ("MEDIAN bp", "median_bp", f1),
        ("mean BELOW median?", "mean_below_median", lambda v: "YES" if v else "no"),
        ("win rate", "win_rate", pc),
        ("payoff (mean win / mean loss)", "payoff", lambda v: "%.2f" % v),
        ("mean win bp", "mean_win_bp", f1),
        ("mean loss bp", "mean_loss_bp", f1),
        ("holding run, mean bars", "holding_run_mean", lambda v: "%.2f" % v),
        ("holding run, median bars", "holding_run_median", lambda v: "%.1f" % v),
        ("skew", "skew", f2),
        ("kurtosis (raw)", "kurtosis_raw", lambda v: "%.1f" % v),
        ("trades trimmed each side", "k_trim", lambda v: "%d" % v),
        ("mean EX-TOP 1%", "mean_ex_top_bp", f1),
        ("mean EX-BOTTOM 1%", "mean_ex_bottom_bp", f1),
        ("mean TRIMMED 1% BOTH SIDES", "mean_trimmed_bp", f1),
        ("top 1% share of P&L", "top1_share", lambda v: "%+.0f%%" % (100 * v)),
        ("bottom 1% share of P&L", "bottom1_share", lambda v: "%+.0f%%" % (100 * v)),
        ("top 1% mean bp", "top1_mean_bp", lambda v: "%+.0f" % v),
        ("bottom 1% mean bp", "bottom1_mean_bp", lambda v: "%+.0f" % v)))
    for nm, d in (("BASE", B2), ("BASE+dv28", V2)):
        net = d["drop_winners_moves"] + d["drop_losers_moves"]
        print("\n  %-10s net effect of the two tails on the mean: %+.1f bp "
              "(winners %+.1f, losers %+.1f)" % (
                  nm, net, d["drop_winners_moves"], d["drop_losers_moves"]))
        print("             the SYMMETRIC trim is %+.1f bp against a raw mean of "
              "%+.1f and a median of %+.1f" % (
                  d["mean_trimmed_bp"], d["mean_bp"], d["median_bp"]))

    # ---- GROUP 3 ----------------------------------------------------------
    print("\n" + "=" * 78)
    print("GROUP 3 -- WHAT THE WINNERS DEPEND ON")
    print("=" * 78)
    B3, V3 = cells["BASE"]["g3"], cells["BASE+dv28"]["g3"]
    table(B3, V3, (
        ("distinct names traded", "names", lambda v: "%d" % v),
        ("NAMES TO HALF THE P&L", "names_to_half_pnl", lambda v: "%d" % v),
        ("top 1 name share", "top1_name_share", pc),
        ("top 5 name share", "top5_name_share", pc),
        ("top 10 name share", "top10_name_share", pc),
        ("names to half (raw trade P&L)", "names_to_half_pnl_rawpnl",
         lambda v: "%d" % v),
        ("calendar years", "years", lambda v: "%d" % v),
        ("years profitable GROSS", "years_profitable_gross", lambda v: "%d" % v),
        ("years profitable NET", "years_profitable_net", lambda v: "%d" % v)))

    print("\n  THE SPLITS -- each charged ITS OWN 2c, not the book's average")
    sh = "  %-13s %-13s %7s %8s %8s %8s %7s"
    print(sh % ("cell", "cut", "P&L%", "trades", "mean bp", "own 2c", "x2c"))
    print("  " + "-" * 72)
    for nm, d in (("BASE", B3), ("dv28", V3)):
        for label, key in (("dead", "dead"), ("alive", "alive"),
                           ("era 1st half", "era_first_half"),
                           ("era 2nd half", "era_second_half"),
                           ("price LOW", "price_low"),
                           ("price MID", "price_mid"),
                           ("price HIGH", "price_high")):
            x = d[key]
            print(sh % (nm if key == "dead" else "", label,
                        "%+.1f%%" % (100 * x["share_pnl"]), "%d" % x["n"],
                        "%+.1f" % x["mean_bp"], "%.1f" % x["two_c_bp"],
                        "%.2fx" % x["mean_over_2c"]))
        print("  " + "-" * 72)
    print("  price terciles cut at $%.2f / $%.2f (BASE). The LOW tercile trades at "
          "a median\n  $%.2f against $%.2f in the HIGH tercile, and its own round "
          "trip is %.1f bp\n  against %.1f -- cost in bp scales as 1/price, which "
          "is the cut that killed D284."
          % (B3["price_cuts"][0], B3["price_cuts"][1], B3["price_low"]["price"],
             B3["price_high"]["price"], 2 * B3["price_low"]["two_c_bp"],
             2 * B3["price_high"]["two_c_bp"]))
    print(f"\n  dead names are {B3['dead_names_in_panel']} of {len(panel.symbols)} "
          f"in the panel ({B3['dead_names_in_panel'] / len(panel.symbols):.1%}); "
          f"they are\n  {B3['dead_trade_share']:.1%} of BASE's trades and "
          f"{V3['dead_trade_share']:.1%} of dv28's")

    print("\n  BY CALENDAR YEAR -- gross bp/bar (net = gross minus the cell's "
          "flat cost)")
    yrs = sorted(set(B3["gross_by_year"]) | set(V3["gross_by_year"]))
    print("  %-12s %s" % ("cell", " ".join("%7d" % y for y in yrs)))
    for nm, d in (("BASE", B3), ("dv28", V3)):
        print("  %-12s %s" % (nm, " ".join(
            "%+7.1f" % d["gross_by_year"][y] if y in d["gross_by_year"] else "      -"
            for y in yrs)))
    for nm, d in (("BASE", B3), ("dv28", V3)):
        print("  %-12s NET-positive in %d of %d calendar years" % (
            nm, d["years_profitable_net"], d["years"]))

    # ---- GROUP 4 ----------------------------------------------------------
    print("\n" + "=" * 78)
    print("GROUP 4 -- NULLS: THE DISTRIBUTION, NOT THE PERCENTILE ALONE")
    print("=" * 78)
    nulls = {}
    for nm, key in (("BASE", [W.SEED, DEPTH, 1]),
                    ("BASE+dv28", [W.SEED, DEPTH, 1])):
        ng, nsg, nsn = rank_rotation_null(A, cells[nm]["gate"], G4, a.draws, key)
        c = cells[nm]["cost"]
        nulls[nm] = dict(
            construction="rank rotation inside the 25-name gate (D300/D306)",
            source="RE-RUN here, seeded as D306 seeded it",
            gross_bp=dist(ng, c["gross_bp"]),
            sharpe_gross=dist(nsg, c["sharpe_gross"]),
            sharpe_net=dist(nsn, c["sharpe_net"]))
        print(f"\n  {nm}  --  {nulls[nm]['construction']}")
        print("    %-16s %10s %10s %10s %10s" % ("statistic", "score", "null p50",
                                                 "null p95", "p"))
        for st in ("gross_bp", "sharpe_gross", "sharpe_net"):
            d = nulls[nm][st]
            print("    %-16s %10.3f %10.3f %10.3f %10.4f" % (
                st, d["score"], d["p50"], d["p95"], d["p"]))

    # [N] the re-run must reproduce D306's published p95 bit-for-bit.
    ref = d306["N=2/target"]
    e1 = abs(nulls["BASE"]["gross_bp"]["p95"] - ref["null_gross_p95"])
    e2 = abs(nulls["BASE"]["sharpe_gross"]["p95"] - ref["null_sharpe_p95"])
    e3 = abs(nulls["BASE"]["gross_bp"]["p"] - ref["p_gross"])
    assert max(e1, e2, e3) < 1e-9, (
        f"[N] the re-run null differs from D306's published one: gross p95 "
        f"{e1:.2e}, sharpe p95 {e2:.2e}, p {e3:.2e}")
    print(f"\n    [N] the BASE null reproduces D306's PUBLISHED p95 "
          f"({ref['null_gross_p95']:.4f} gross, {ref['null_sharpe_p95']:.4f} "
          f"Sharpe) and p ({ref['p_gross']:.4f}) to {max(e1, e2, e3):.1e}\n"
          f"        -- the p50 below is the number D306 never published")

    # dv28's own null is D321's EXCLUSION rotation, and it is QUOTED not re-run.
    r28 = d321["cells"]["dv28"]
    nulls["BASE+dv28"]["exclusion_rotation_QUOTED_from_D321"] = dict(
        construction="circular time rotation of the dv28 exclusion mask (D321)",
        source="QUOTED from data/d321_dv_sweep.json -- not re-run here",
        statistic="net Sharpe", score=r28["sharpe_net"],
        p50=r28["null_p50"], p95=r28["null_p95"], p=r28["p"],
        vs_control=r28["vs_control"], needed=r28["needed"])
    print("\n  BASE+dv28  --  D321's EXCLUSION rotation, QUOTED, not re-run")
    print("    %-16s %10.3f %10.3f %10.3f %10.4f" % (
        "sharpe_net", r28["sharpe_net"], r28["null_p50"], r28["null_p95"],
        r28["p"]))
    print("    the dv28 filter is what that null randomises; the rank rotation "
          "above randomises\n    the SIGNAL, so the two answer different "
          "questions and neither replaces the other.")

    # ---- write -------------------------------------------------------------
    out = dict(
        purpose="D322: the four-group report on the programme's current best "
                "book. A REPORT -- it scores no new rule, closes nothing, and "
                "needs no pre-registration (R8 does not apply).",
        status="REPORT. Scores no new rule, closes nothing, needs no "
               "pre-registration.",
        holdout_reads=0, programme_total_holdout_reads=0,
        cells_fixed_in_advance={
            "BASE": "D306 N=2/target: top-2 per leg, k=5 hold, D303's "
                    "market-referenced excess target X_TARGET=0.9627, no overlay",
            "BASE+dv28": "the same, excluding the bottom 28% of the live "
                         "cross-section by a lagged trailing-63-bar mean of "
                         "close x volume, applied per bar inside the gate cut "
                         "(D321)"},
        cost_basis="D318: per-cell held-name round trip 4 x median(half-spread "
                   "at entry over the trades taken); IBKR per-share commission "
                   "4 x (0.005 / held median price) x 1e4; turnover = entries / "
                   "names HELD / bars.",
        two_c_note="2c = rt_total / 2, because a position's weight in the book "
                   "is 1/(held/2) and rt is charged per unit of held-name "
                   "turnover.",
        dv28_guard="CARRIED, NOT PROMOTED. p = 0.0100 against D321's exclusion "
                   "rotation, unconfirmed on a separate construction. Does not "
                   "enter BOOK.md.",
        draws=a.draws,
        cells={nm: dict(cost={k: v for k, v in cc["cost"].items()},
                        group1=cc["g1"], group2=cc["g2"], group3=cc["g3"],
                        group4=nulls[nm],
                        ledger_residual_bp=cc["residual_bp"],
                        pnl_over_contribution=cc["pnl_over_contribution"],
                        d306_basis=cc["d306_basis"])
               for nm, cc in cells.items()})
    OUT.write_text(json.dumps(out, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
