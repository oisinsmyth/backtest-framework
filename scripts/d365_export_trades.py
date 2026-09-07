"""D365 TRADE EXPORT and RISK REPORT -- every trade of the momentum buffer book, its per-bar path, the book's own
series, and the analysis the principal asked for: drawdown on era 1, era 2 and COMBINED, and exposure on both lenses.

    uv run python scripts/d365_export_trades.py --selftest
    uv run python scripts/d365_export_trades.py --export [--cell 95:80] [--out-dir DIR]
    uv run python scripts/d365_export_trades.py --risk   [--cell 95:80] [--out-dir DIR]

WHAT THIS IS. D365's RESULT (834cda1) established the book: enter above the 95th percentile of `mom_252_21`, hold
until the 80th, equal-weight, hedged, next-open fill. 1,709 trades, +2.59 bp/bar net PUB, Sharpe 0.417. This script
does not re-derive any of that -- it IMPORTS run_d365 and calls its functions (R9: an ad-hoc script gets none of the
look-ahead protection the runners have), and [ID] asserts every headline against the committed
`data/d365_momentum_buffer.json` before a row is written.

THE TWO LENSES ARE KEPT APART. CLAUDE.md: path-invariant (per TRADE) and path-variant (the book, in bp/bar) are
"never compared on the same statistic". `--risk` prints exposure under both and labels every line with the lens it
belongs to. A holding period is a per-trade statistic; a share of bars deployed is a book statistic; they do not go
in the same table and neither is the other's denominator.

THE DRAWDOWN QUESTION, AND WHY THE COMBINED NUMBER IS NOT THE MAX OF THE TWO. Splitting a series at the era
boundary and taking each half's worst drawdown HIDES any drawdown that spans the boundary: the peak is in era 1 and
the trough in era 2, so neither half sees the whole fall. The combined window is computed on the undivided series
and [DD] asserts it is >= both halves, reporting by how much and naming the dates when it spans.

Two conventions are reported for every window because they answer different questions and disagree by construction:
ADDITIVE (`cumsum` of bp -- the record's own, G22.costed's `maxdd`, a constant-notional book) and COMPOUNDED
(`cumprod(1 + net/1e4)` -- a book that reinvests). On a series with a large early drawdown the compounded number is
smaller in percentage terms; on one with a large late drawdown it is larger. Neither is "right".
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

# run_d365 FIRST: it installs the holdout audit hook before any other chain module opens a file.
import run_d365_momentum_buffer as V65            # noqa: E402

PREP, V58, V50, V47 = V65.PREP, V65.V58, V65.V50, V65.V47
STUDY = 365
EXTRA_SCORES = ("rsi", "rev_5", "rev_21", "dist_52w_high", "max_ret_21",
                "park_vol_21", "amihud_21", "cs_spread", "trailing_return")
RESULT_JSON = REPO / "data" / "d365_momentum_buffer.json"
CTRL_JSON = REPO / "data" / "d365_ctrl_95_80_p0.json"


def el(t0):
    return f"{time.time() - t0:.0f}s"


# ================================================================== the book, from the runner's own functions
def build(P, hi, lo, fill="open"):
    """Everything downstream reads this dict. Not one line of it is re-derived here."""
    pct = V58.pct_of(P, V65.SCORE)
    elig = np.asarray(P["elig"], bool)
    hold = V65.hold_grid(pct, elig, hi, lo, P["m_start"])
    ent = V65.entries_of(hold)
    X_cc, X_oc = V65.returns_grids(P)
    ret = V65.ret_of(X_cc, X_oc, ent, fill)
    book, mask, members, n_ret = V65.book_series(hold, ret, elig)
    trades, open_end, nan_bars = V65.trades_of(hold, ret)
    return dict(pct=pct, elig=elig, hold=hold, ent=ent, ret=ret, X_cc=X_cc, X_oc=X_oc,
                book=book, mask=mask, members=members, n_ret=n_ret,
                trades=trades, open_end=open_end, nan_bars=nan_bars, hi=hi, lo=lo, fill=fill)


def assert_ID(P, B, hi, lo):
    """Every headline this file rests on, against the committed result. Nothing is written before this passes."""
    if not RESULT_JSON.exists():
        raise SystemExit(f"[ID] {RESULT_JSON.name} is missing -- run run_d365_momentum_buffer.py --report first")
    R = json.loads(RESULT_JSON.read_text())
    key = V65.cell_name(hi, lo)
    if key not in R["results"]:
        raise SystemExit(f"[ID] {key} not in the committed result's cells {sorted(R['results'])}")
    st = R["results"][key][B["fill"]]
    blk = V65.cell_block(P, B["hold"], B["ret"], B["fill"])
    checks = []
    for name, got, want in (
        ("trades", len(B["trades"]), st["trades"]),
        ("gross_bp (pooled)", blk["gross_bp"], st["gross_bp"]),
        ("gross_bar_bp (series)", blk["gross_bar_bp"], st["gross_bar_bp"]),
        ("net_PUB_bp", blk["PUB"]["net_bp"], st["PUB"]["net_bp"]),
        ("sharpe_net", blk["PUB"]["sharpe_net"], st["PUB"]["sharpe_net"]),
        ("mean_members", blk["mean_members"], st["mean_members"]),
        ("turnover", blk["turnover"], st["turnover"]),
        ("maxdd_bp (gross series)", blk["maxdd_bp"], st["maxdd_bp"]),
    ):
        d = abs(float(got) - float(want))
        tol = 1e-9 if name == "trades" else 1e-6
        if d > tol:
            raise AssertionError(f"[ID] {key} {name}: {got!r} != committed {want!r}")
        checks.append(f"{name} {float(got):.6f}")
    print(f"    [ID] {key}/{B['fill']} reproduces the committed result to 1e-6: " + "; ".join(checks))
    return blk


# ================================================================== the trades
def exit_reason(P, B, row, e0, age):
    T = P["T"]
    t = e0 + age
    if t >= T:
        return "open_at_end"
    last_live = np.asarray(P["last_live"])[row] if "last_live" in P else T - 1
    if t > last_live:
        return "delist"
    if not B["elig"][t, row]:
        return "ineligible"
    p = B["pct"][t, row]
    if not np.isfinite(p):
        return "ineligible"
    return "rank" if p <= B["lo"] else "other"


def trade_rows(P, B):
    """One dict per trade. Every 'at entry' column is t-1 information by construction (the percentile grids are lagged)."""
    T, n = P["T"], P["n"]
    dates, symbols = P["dates"], P["symbols"]
    half = T // 2
    RAWC = np.asarray(P["RAW_CLOSE"], float)
    CLOSE = np.asarray(P["CLOSE"], float)
    RAW = np.asarray(P["RAW"], float)
    ocT = np.asarray(P["ocT"], float)
    DV = np.asarray(P["DV"], float)
    beta = np.asarray(P["beta"], float)
    HALF = {cv: np.asarray(P["HALF"][cv], float) for cv in V65.CONVS}
    mom_raw = V50.lagged(P, V65.SCORE)
    dvp = V65.dv_level_pct(P)
    extra = {s: V58.pct_of(P, s) for s in EXTRA_SCORES}
    meta = _meta_status(P)
    X_cc, X_oc, ret = B["X_cc"], B["X_oc"], B["ret"]
    r1T, ocT_r = np.asarray(P["r1T"], float), np.asarray(P["ocT"], float)
    m_f, m_oc = np.asarray(P["m_f"], float), np.asarray(P["m_f_oc"], float)
    two_c = {cv: V65.per_trade_two_c(P, B["trades"], cv)[0] for cv in V65.CONVS}
    yrs = np.asarray(P["years"])

    rows, paths = [], []
    for tid, (row, e0, age, pnl, _side) in enumerate(B["trades"]):
        b_ex = e0 + age - 1
        seg = ret[e0:e0 + age, row]
        fin = np.isfinite(seg)
        cum = np.cumsum(np.where(fin, seg, 0.0))
        mfe_i = int(np.argmax(cum)) if cum.size else 0
        mae_i = int(np.argmin(cum)) if cum.size else 0
        unh = np.where(np.arange(e0, e0 + age) == e0, ocT_r[e0:e0 + age, row], r1T[e0:e0 + age, row])
        mkt = np.where(np.arange(e0, e0 + age) == e0, m_oc[e0:e0 + age], m_f[e0:e0 + age])
        rows.append(dict(
            trade_id=tid, symbol=symbols[row], row=row,
            bar_entry=e0, date_entry=dates[e0], bar_exit=b_ex, date_exit=dates[b_ex],
            hold_bars=age, era=1 if e0 < half else 2, year_entry=int(yrs[e0]),
            exit_reason=exit_reason(P, B, row, e0, age),
            pct_mom=_f(B["pct"][e0, row]), mom_raw=_f(mom_raw[e0, row]),
            pct_mom_exit=_f(B["pct"][min(e0 + age, P["T"] - 1), row]),
            price_close=_f(RAWC[e0, row]), price_open_fill=_f(CLOSE[e0, row] / (1.0 + ocT_r[e0, row]) * RAW[e0, row])
            if np.isfinite(ocT_r[e0, row]) and ocT_r[e0, row] != -1 else "",
            price_close_exit=_f(RAWC[b_ex, row]),
            dv=_f(DV[e0, row]), dv_pct=_f(dvp[e0, row]), beta=_f(beta[e0, row]),
            half_spread_PUB_bp=_f(HALF["PUB"][e0, row]), half_spread_PB_bp=_f(HALF["PB"][e0, row]),
            members_at_entry=int(B["members"][e0]),
            **{f"pct_{s}": _f(extra[s][e0, row]) for s in EXTRA_SCORES},
            pnl_hedged_bp=_f(pnl * 1e4, 8), pnl_unhedged_bp=_f(np.nansum(unh) * 1e4, 8),
            pnl_market_bp=_f(np.nansum(np.where(fin, mkt, np.nan)) * 1e4, 8),
            mfe_bp=_f(cum[mfe_i] * 1e4 if cum.size else 0.0), mae_bp=_f(cum[mae_i] * 1e4 if cum.size else 0.0),
            bars_to_mfe=mfe_i + 1, bars_to_mae=mae_i + 1,
            two_c_PUB_bp=_f(two_c["PUB"][tid]), two_c_PB_bp=_f(two_c["PB"][tid]),
            pnl_net_PUB_bp=_f(pnl * 1e4 - two_c["PUB"][tid], 8), pnl_net_PB_bp=_f(pnl * 1e4 - two_c["PB"][tid], 8),
            status_meta=meta.get(symbols[row], ("", ""))[0], delist_date=meta.get(symbols[row], ("", ""))[1],
        ))
        for k in range(age):
            t = e0 + k
            paths.append((tid, symbols[row], t, dates[t], k + 1,
                          _f(seg[k] * 1e4, 8), _f(unh[k] * 1e4, 8), _f(mkt[k] * 1e4, 8), _f(cum[k] * 1e4, 8)))
    return rows, paths


def _f(x, nd=6):
    x = float(x)
    return "" if not np.isfinite(x) else repr(round(x, nd))


def _meta_status(P):
    p = REPO / "data" / "fixtures" / "us_shorts_daily_raw.meta.json"
    if not p.exists():
        return {}
    m = json.loads(p.read_text())
    out = {}
    for key in ("symbols", "per_symbol", "names"):
        blk = m.get(key)
        if isinstance(blk, dict):
            for s, v in blk.items():
                if isinstance(v, dict):
                    out[s] = (str(v.get("status", "")), str(v.get("delistingDate", v.get("delist_date", "")) or ""))
            if out:
                return out
    return out


def series_rows(P, B, blk):
    """One row per bar of the book. This is what the drawdown reads."""
    T = P["T"]
    dates, yrs = P["dates"], np.asarray(P["years"])
    half = T // 2
    ent = B["ent"].sum(axis=1)
    ex = np.zeros(T, np.int64)
    for row, e0, age, _p, _s in B["trades"]:
        if e0 + age < T:
            ex[e0 + age] += 1
    m_f = np.asarray(P["m_f"], float)
    # The cost is a per-bar constant by construction (round trip x turnover, both book-level), so the series' net is the
    # gross series less a constant. That is the record's own arithmetic; it is not a per-bar cost measurement.
    cost_bar = blk["PUB"]["cost_bp"]
    cost_pb = blk["PB"]["cost_bp"]
    g = B["book"] * 1e4
    rows, eq_g, eq_n = [], 0.0, 0.0
    for t in range(T):
        if not B["mask"][t]:
            continue
        gross = float(g[t])
        net = gross - cost_bar
        eq_g += gross
        eq_n += net
        rows.append(dict(bar=t, date=dates[t], year=int(yrs[t]), era=1 if t < half else 2,
                         members=int(B["members"][t]), entries=int(ent[t]), exits=int(ex[t]),
                         gross_bp=_f(gross, 8), cost_bp=_f(cost_bar, 8),
                         net_PUB_bp=_f(net, 8), net_PB_bp=_f(gross - cost_pb, 8),
                         equity_gross_bp=_f(eq_g, 6), equity_net_PUB_bp=_f(eq_n, 6),
                         market_bp=_f(m_f[t] * 1e4, 8)))
    return rows


# ================================================================== drawdown
def drawdowns(x, dates, top=5):
    """Every drawdown of an ADDITIVE equity curve built from the per-bar series x (bp).
    Returns (max block, list of the `top` deepest). A drawdown runs from a running-max peak to the next new high."""
    eq = np.cumsum(x)
    peak = np.maximum.accumulate(eq)
    under = eq < peak - 1e-12
    out, i, T = [], 0, len(x)
    while i < T:
        if not under[i]:
            i += 1
            continue
        j = i
        while j < T and under[j]:
            j += 1
        seg = eq[i:j]
        k = int(np.argmin(seg))
        pk = i - 1 if i > 0 else 0
        out.append(dict(peak_i=pk, trough_i=i + k, end_i=j - 1 if j < T else T - 1,
                        recovered=bool(j < T), depth_bp=float(peak[i] - seg[k]),
                        peak_date=dates[pk], trough_date=dates[i + k],
                        recovery_date=dates[j] if j < T else "NOT RECOVERED",
                        bars_to_trough=int(k + 1), bars_under=int(j - i)))
        i = j
    out.sort(key=lambda d: -d["depth_bp"])
    return (out[0] if out else None), out[:top]


def drawdowns_compound(x, dates, top=5):
    """The same, on a COMPOUNDED curve. Depth is a percentage of the running peak."""
    eq = np.cumprod(1.0 + np.asarray(x, float) / 1e4)
    peak = np.maximum.accumulate(eq)
    under = eq < peak * (1 - 1e-15)
    out, i, T = [], 0, len(x)
    while i < T:
        if not under[i]:
            i += 1
            continue
        j = i
        while j < T and under[j]:
            j += 1
        seg = eq[i:j]
        k = int(np.argmin(seg))
        pk = i - 1 if i > 0 else 0
        out.append(dict(peak_i=pk, trough_i=i + k, depth_pct=float(100.0 * (1.0 - seg[k] / peak[i])),
                        peak_date=dates[pk], trough_date=dates[i + k],
                        recovery_date=dates[j] if j < T else "NOT RECOVERED",
                        recovered=bool(j < T), bars_under=int(j - i)))
        i = j
    out.sort(key=lambda d: -d["depth_pct"])
    return (out[0] if out else None), out[:top]


def longest_underwater(x):
    eq = np.cumsum(x)
    peak = np.maximum.accumulate(eq)
    under = eq < peak - 1e-12
    best = run = 0
    for u in under:
        run = run + 1 if u else 0
        best = max(best, run)
    return best


def dd_loop_check(x):
    """[DD]: a plain scalar loop, no numpy accumulators, for the max additive drawdown."""
    eq = 0.0
    pk = -1e18
    worst = 0.0
    for v in x:
        eq += float(v)
        pk = max(pk, eq)
        worst = max(worst, pk - eq)
    return worst


# ================================================================== stages
def stage_export(P, hi, lo, out_dir, t0):
    B = build(P, hi, lo)
    blk = assert_ID(P, B, hi, lo)
    rows, paths = trade_rows(P, B)
    srows = series_rows(P, B, blk)

    # [PATH] on the RAW quantities, not the CSV's rounded text: the arithmetic is what is being checked. The rounding the
    # file introduces is measured separately below, because that is a statement about the file, not about the book.
    ret = B["ret"]
    worst = 0.0
    per_bar = np.zeros(P["T"])
    cnt = np.zeros(P["T"], np.int64)
    for row, e0, age, pnl, _s in B["trades"]:
        seg = ret[e0:e0 + age, row]
        fin = np.isfinite(seg)
        worst = max(worst, abs(float(seg[fin].sum()) - pnl))
        idx = np.arange(e0, e0 + age)[fin]
        per_bar[idx] += seg[fin]
        cnt[idx] += 1
    g = B["book"]
    wb = 0.0
    for t in range(P["T"]):
        if B["mask"][t] and cnt[t] > 0:
            wb = max(wb, abs(per_bar[t] / cnt[t] - g[t]))
    assert worst < 1e-12 and wb < 1e-15, f"[PATH] trade {worst:.2e}, bar {wb:.2e}"
    print(f"    [PATH] all {len(rows):,} trades' bar returns sum to their own P&L to {worst:.1e}; the open trades' mean "
          f"equals the book's gross on every one of {int(B['mask'].sum()):,} deployed bars to {wb:.1e}")

    # [CSV] what the file's own precision costs, so a reader knows what they are analysing.
    by_trade = {}
    for p in paths:
        by_trade[p[0]] = by_trade.get(p[0], 0.0) + (float(p[5]) if p[5] != "" else 0.0)
    csv_worst = max(abs(by_trade.get(r["trade_id"], 0.0) - float(r["pnl_hedged_bp"])) for r in rows)
    print(f"    [CSV] re-summing the WRITTEN path rows reproduces the written P&L to {csv_worst:.1e} bp -- the cost of "
          f"8 decimal places over holds up to {max(r['hold_bars'] for r in rows)} bars, and the file's true precision")

    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    tag = f"{hi}_{lo}"
    ft = d / f"d365_trades_{tag}.csv"
    with ft.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    fp = d / f"d365_trade_paths_{tag}.csv.gz"
    with gzip.open(fp, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["trade_id", "symbol", "bar", "date", "k", "r_hedged_bp", "r_unhedged_bp", "r_market_bp", "cum_hedged_bp"])
        w.writerows(paths)
    fs = d / f"d365_series_{tag}.csv"
    with fs.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(srows[0].keys()))
        w.writeheader()
        w.writerows(srows)
    for p in (ft, fp, fs):
        print(f"    wrote {p.name}  ({p.stat().st_size/1e6:.2f} MB)")
    print(f"    trades {len(rows):,}  path rows {len(paths):,}  book bars {len(srows):,}  ({el(t0)})")
    return B, blk, rows, srows


def stage_risk(P, hi, lo, out_dir, t0):
    B = build(P, hi, lo)
    blk = assert_ID(P, B, hi, lo)
    rows, _paths = trade_rows(P, B)
    srows = series_rows(P, B, blk)
    dates = [r["date"] for r in srows]
    net = np.array([float(r["net_PUB_bp"]) for r in srows])
    gross = np.array([float(r["gross_bp"]) for r in srows])
    era = np.array([r["era"] for r in srows])
    T = len(net)
    half_date = dates[int(np.argmax(era == 2))] if (era == 2).any() else "-"

    print(f"\n  DRAWDOWN -- net PUB, three windows. Era 1 is bars before the panel's midpoint ({dates[0]} .. "
          f"{dates[int(np.argmax(era == 2)) - 1]}), era 2 from {half_date}.")
    print("  A drawdown that SPANS the boundary is invisible to either half; the combined window is computed on the")
    print("  undivided series and is asserted >= both halves.\n")
    W = (("era 1", era == 1), ("era 2", era == 2), ("COMBINED", np.ones(T, bool)))
    dd = {}
    print(f"    {'window':>9} {'series':>6} | {'addDD bp':>9} {'peak':>11} {'trough':>11} {'recovery':>13} {'toTrough':>9} "
          f"{'under':>6} {'longUW':>7} | {'cmpDD %':>8} {'ann bp':>7} {'Calmar':>7}")
    for lbl, m in W:
        for nm, x in (("net", net[m]), ("gross", gross[m])):
            mx, top = drawdowns(x, [d for d, k in zip(dates, m) if k])
            mc, _ = drawdowns_compound(x, [d for d, k in zip(dates, m) if k])
            lo_ = dd_loop_check(x)
            assert abs(lo_ - (mx["depth_bp"] if mx else 0.0)) < 1e-6, f"[DD] loop {lo_} != {mx}"
            ann = float(np.mean(x)) * 252.0
            cal = ann / mx["depth_bp"] if mx and mx["depth_bp"] > 0 else float("nan")
            dd[(lbl, nm)] = dict(add=mx, top=top, comp=mc, ann_bp=ann, calmar=cal, longest_uw=longest_underwater(x), n=int(m.sum()))
            print(f"    {lbl:>9} {nm:>6} | {mx['depth_bp']:9.0f} {mx['peak_date']:>11} {mx['trough_date']:>11} "
                  f"{mx['recovery_date']:>13} {mx['bars_to_trough']:9d} {mx['bars_under']:6d} {longest_underwater(x):7d} | "
                  f"{mc['depth_pct']:8.2f} {ann:7.0f} {cal:7.3f}")

    a1, a2, ac = (dd[(k, "net")]["add"]["depth_bp"] for k in ("era 1", "era 2", "COMBINED"))
    assert ac >= max(a1, a2) - 1e-9, f"[DD] combined {ac} < max(era) {max(a1, a2)}"
    span = dd[("COMBINED", "net")]["add"]
    p_era = 1 if span["peak_i"] < int((era == 1).sum()) else 2
    t_era = 1 if span["trough_i"] < int((era == 1).sum()) else 2
    print(f"\n    [DD] combined {ac:.0f} bp >= max(era 1 {a1:.0f}, era 2 {a2:.0f}) by {ac - max(a1, a2):.0f} bp. "
          f"The combined worst runs {span['peak_date']} (era {p_era}) -> {span['trough_date']} (era {t_era}), "
          + ("SPANNING THE BOUNDARY -- neither half sees it whole." if p_era != t_era else "inside era %d." % p_era))
    for lbl in ("era 1", "era 2", "COMBINED"):
        print(f"\n    top 5 drawdowns, {lbl} (net PUB, additive)")
        for k, d_ in enumerate(dd[(lbl, "net")]["top"], 1):
            print(f"      {k}. {d_['depth_bp']:8.0f} bp   {d_['peak_date']} -> {d_['trough_date']} -> "
                  f"{d_['recovery_date']:>13}   {d_['bars_under']:4d} bars under")

    # ---------------- exposure, both lenses, never mixed
    members = np.array([r["members"] for r in srows], float)
    entries = np.array([r["entries"] for r in srows], float)
    exits = np.array([r["exits"] for r in srows], float)
    elig_n = np.asarray(B["elig"], bool).sum(axis=1)[[r["bar"] for r in srows]]
    yrs_book = len(srows) / 252.0
    print("\n  EXPOSURE -- PATH-VARIANT lens (the BOOK, scored in bp per BAR). These are book statistics.")
    print(f"    bars with at least one member          {(members > 0).mean():.4%} of {len(srows):,} defined bars")
    print(f"    members                                 mean {members.mean():.1f}  median {np.median(members):.0f}  "
          f"min {members.min():.0f}  max {members.max():.0f}")
    print(f"    members as a share of the eligible universe   mean {np.mean(members / np.maximum(elig_n, 1)):.2%} "
          f"(the universe averages {elig_n.mean():.0f} eligible names)")
    print(f"    entries / exits per year                {entries.sum()/yrs_book:.0f} / {exits.sum()/yrs_book:.0f}")
    print(f"    turnover                                {blk['turnover']:.4%} per bar = {blk['turnover']*252:.1%} a year")
    print(f"    time in market                          100% by construction -- the book is never flat; it holds "
          f"whatever qualifies, and something always does")

    holds = np.array([r["hold_bars"] for r in rows], float)
    names = Counter(r["symbol"] for r in rows)
    pos_bars = holds.sum()
    print("\n  EXPOSURE -- PATH-INVARIANT lens (per TRADE). These are trade statistics and are NOT comparable to the above.")
    print(f"    trades                                  {len(rows):,} over {len(names):,} distinct names")
    print(f"    holding period (bars)                   mean {holds.mean():.1f}  median {np.median(holds):.0f}  "
          f"p10 {np.percentile(holds,10):.0f}  p90 {np.percentile(holds,90):.0f}  max {holds.max():.0f}")
    print(f"    position-bars                           {pos_bars:,.0f} (== the book's summed members: "
          f"{members.sum():,.0f}; [EXP] {abs(pos_bars - members.sum()) < 1e-6})")
    print(f"    concurrency (open trades per bar)       mean {members.mean():.1f}  max {members.max():.0f}")
    re_entry = sum(c - 1 for c in names.values() if c > 1)
    print(f"    re-entry                                {re_entry:,} of {len(rows):,} trades are a name being bought "
          f"again ({re_entry/len(rows):.1%}); {sum(1 for c in names.values() if c > 1):,} names traded more than once")
    print(f"    share of an eligible name's life held   {pos_bars / max(elig_n.sum(), 1):.2%} of eligible name-bars")
    print(f"    exit reasons                            " + ", ".join(f"{k} {v:,}" for k, v in
          Counter(r["exit_reason"] for r in rows).most_common()))
    assert abs(pos_bars - members.sum()) < 1e-6, "[EXP] position-bars != summed members"
    print("\n    [EXP] the two lenses agree where they must (position-bars == summed members) and are reported apart "
          "everywhere else: a holding period is per TRADE, a share of bars deployed is per BOOK (CLAUDE.md).")

    out = dict(study=STUDY, cell=V65.cell_name(hi, lo), fill=B["fill"],
               note="D365's book, exported. Drawdown on era 1, era 2 and the undivided series, two conventions; "
                    "exposure on both lenses, never mixed. Nothing re-derived: run_d365's own functions build the book "
                    "and [ID] holds every headline to data/d365_momentum_buffer.json.",
               drawdown={f"{k[0]}|{k[1]}": v for k, v in dd.items()},
               exposure_book=dict(bars=len(srows), members_mean=float(members.mean()), members_max=float(members.max()),
                                  turnover=float(blk["turnover"]), entries_per_year=float(entries.sum()/yrs_book)),
               exposure_trade=dict(trades=len(rows), names=len(names), hold_mean=float(holds.mean()),
                                   hold_median=float(np.median(holds)), position_bars=float(pos_bars),
                                   re_entries=int(re_entry)))
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    p = d / "d365_risk_report.json"
    p.write_text(json.dumps(V65.clean(out), indent=1))
    print(f"\n  wrote {p.name}  ({el(t0)})  {PREP.rss_line()}")
    return dd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--risk", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--cell", default="95:80")
    ap.add_argument("--out-dir", default=str(REPO / "data"))
    a = ap.parse_args()
    t0 = time.time()
    hi, lo = (int(x) for x in a.cell.split(":"))
    print(f"D365 EXPORT  the momentum buffer book, cell {hi}/{lo} -- every trade, its path, the book's series, "
          f"the drawdowns and both exposure lenses")
    P = PREP.prep(need_grids=False)
    V65.assert_HOLDOUT_GUARD()
    if a.selftest:
        B = build(P, hi, lo)
        assert_ID(P, B, hi, lo)
        # bars      1     2     3     4     5        the peak is +1 at bar 1 and the trough -5 at bar 4,
        # x        +1    -3    +2    -5    +6        so the worst drawdown is 6, and it recovers at bar 5.
        # cumsum   +1    -2     0    -5    +1
        x = np.array([1.0, -3.0, 2.0, -5.0, 6.0])
        mx, _ = drawdowns(x, ["b1", "b2", "b3", "b4", "b5"])
        assert abs(mx["depth_bp"] - 6.0) < 1e-12 and abs(dd_loop_check(x) - 6.0) < 1e-12, \
            f"[DD] hand case: got {mx['depth_bp']} / {dd_loop_check(x)}, expected 6.0"
        assert mx["peak_date"] == "b1" and mx["trough_date"] == "b4" and mx["recovery_date"] == "b5", \
            f"[DD] hand case dates: {mx['peak_date']} -> {mx['trough_date']} -> {mx['recovery_date']}"
        mc, _ = drawdowns_compound(x, ["b1", "b2", "b3", "b4", "b5"])
        assert mc["trough_date"] == "b4", "[DD] the compounded convention must find the same trough here"
        print(f"    [DD] hand case: cumsum +1 -2 0 -5 +1 -> worst {mx['depth_bp']:.1f} bp, peak {mx['peak_date']} "
              f"trough {mx['trough_date']} recovery {mx['recovery_date']}; the scalar loop agrees; the compounded "
              f"convention finds the same trough at {mc['depth_pct']:.4f}%")
        broke = False
        try:
            assert abs(dd_loop_check(x) - 5.0) < 1e-12
        except AssertionError:
            broke = True
        assert broke, "[6] the [DD] check must fail when handed the wrong answer"
        print("    [6] [DD] raises when handed 5.0 instead of 6.0")
        stage_export(P, hi, lo, str(REPO / "temp" / "d365_selftest"), t0)
        print(f"\nOK  selftest passes  ({el(t0)})  {PREP.rss_line()}")
    elif a.export:
        stage_export(P, hi, lo, a.out_dir, t0)
    elif a.risk:
        stage_risk(P, hi, lo, a.out_dir, t0)
    else:
        ap.error("one of --export, --risk, --selftest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
