"""D339 -- DIAGNOSTIC census: where does each F0 book's P&L sit against a price
floor and a dollar-volume floor? Stage-0 measurement. No predictions, no verdicts.

    uv run python scripts/d339_census.py --selftest
    uv run python scripts/d339_census.py

Every one of the 46 signals as a SYMMETRIC F0 book (depth 2, k=20, variant lens,
D303 target exit -- D335's cell), plus the incumbent C0 (k=5, unfiltered). For
each ledger, three cuts on the ENTRY bar:

    (a) the AS-TRADED price at the prior close is below $5   (RAW_CLOSE[e0-1] < 5)
    (b) the name fails the 28th-percentile dollar-volume cut  (~keep28[e0])
    (c) either

RAW_CLOSE undoes the fixture's split adjustment: CLOSE times the product of the
split ratios dated strictly AFTER the bar. D338's top trade (VSA, 2025-01-31)
was a $90.55 adjusted close that traded at $0.18 (two reverse splits later).

ASSERTIONS -- properties of code
  [K]  the score cache is the D334 rebuild (D338's check)
  [R]  RAW_FACTOR == 1 for a symbol with no splits on file; VSA at 2025-01-30 is
       ~0.1811 as traded (90.55 x 0.02 x 0.1)
  [1]  the unfloored retrace_leg book reproduces D338's group1.PUB net and gross
       bp/bar to 1e-9
  [6]  [1] raises on a book handed +5 bp on 200 masked bars
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


V35 = _load("d335", "run_d335_legs_under_filter.py")
V31, PA, V9 = V35.V31, V35.PA, V35.V9
V6, Y, W, D, M, SP, R, X = V35.V6, V35.Y, V35.W, V35.D, V35.M, V35.SP, V35.R, V35.X
G22, EXCLUDED = V35.G22, V35.EXCLUDED
EXPECT_APPLIED, EXPECT_PCT = V35.EXPECT_APPLIED, V35.EXPECT_PCT

K0, DEPTH = 20, 2
PRICE_FLOOR, DV_PCT = 5.0, 28.0
SIG_CHECK = "retrace_leg"
OUT_JSON = REPO / "data" / "d339_census.json"
OUT_TXT = REPO / "data" / "d339_census.txt"
D338_JSON = REPO / "data" / "d338_retrace_leg_candidate.json"


# ------------------------------------------------------------------ helpers
def raw_factor(events, symbols, dates):
    """(T, n): product of split ratios dated strictly AFTER dates[t]; 1 where none."""
    T, n = len(dates), len(symbols)
    F = np.ones((T, n))
    darr = np.array(dates)
    for i, s in enumerate(symbols):
        for d, ratio in events["splits"].get(s, []):
            k = int(np.searchsorted(darr, d[:10], side="left"))   # dates[t] < d for t < k
            F[:k, i] *= float(ratio)
    return F


def dv_percentile(DV, finT, t, row):
    m = finT[t] & np.isfinite(DV[t])
    if not m.any() or not np.isfinite(DV[t, row]):
        return np.nan
    return float((DV[t][m] < DV[t, row]).mean())


def book_stats(res, contrib, cost, RAW_CLOSE, keep28, DV, finT, panel):
    tr = res["trades"]
    rows = np.array([t[0] for t in tr]); e0 = np.array([t[1] for t in tr])
    pnl = np.array([t[3] for t in tr]); side = np.array([t[4] for t in tr])
    total = float(contrib.sum())
    by = {}
    for r, v in zip(rows, contrib):
        by[int(r)] = by.get(int(r), 0.0) + float(v)
    v = np.sort(np.array(list(by.values())))[::-1]
    half = int(np.searchsorted(np.cumsum(v), 0.5 * total) + 1) if total > 0 else None
    prev = np.maximum(e0 - 1, 0)
    rawpx = RAW_CLOSE[prev, rows]
    with np.errstate(invalid="ignore"):
        cut_a = rawpx < PRICE_FLOOR
    cut_b = ~keep28[e0, rows]
    cuts = {"a": cut_a, "b": cut_b, "c": cut_a | cut_b}

    def one(sel):
        return dict(trade_share=float(sel.mean()), n=int(sel.sum()),
                    pnl_share=float(contrib[sel].sum() / total) if total != 0 else None,
                    mean_bp_in=float(pnl[sel].mean()) * 1e4 if sel.any() else None,
                    mean_bp_out=float(pnl[~sel].mean()) * 1e4 if (~sel).any() else None)

    i = int(np.argmax(pnl))
    top = dict(symbol=panel.symbols[rows[i]], side="long" if side[i] == 0 else "short",
               entry=panel.dates[e0[i]], hold=int(tr[i][2]), pnl_bp=float(pnl[i]) * 1e4,
               share_raw_pnl=float(pnl[i] / pnl.sum()) if pnl.sum() != 0 else None,
               raw_px_prev=float(rawpx[i]) if np.isfinite(rawpx[i]) else None,
               dv_pct_at_entry=dv_percentile(DV, finT, int(e0[i]), int(rows[i])),
               fails_a=bool(cut_a[i]), fails_b=bool(cut_b[i]))
    return dict(gross_bp_bar=cost["gross_bp"], net_bp_bar=cost["net_bp"], trades=len(tr),
                total_contrib_bp=total * 1e4, total_raw_pnl_bp=float(pnl.sum()) * 1e4,
                names=len(by), names_to_half=half, n_rawpx_nan=int((~np.isfinite(rawpx)).sum()),
                cuts={k: one(s) for k, s in cuts.items()}, top_trade=top)


def fmt_row(name, b):
    if b is None:
        return "  %-22s %s" % (name, "degenerate")
    c, tp = b["cuts"], b["top_trade"]
    pc = lambda x: ("%6.1f%%" % (100 * x)) if x is not None else "     --"
    return ("  %-22s %8.2f %8.2f %6d %5d %5s %s %s %s %s   %-6s %-5s %s %3d %+9.0f %5.1f%% %9s %5s %s%s" % (
        name, b["net_bp_bar"], b["gross_bp_bar"], b["trades"], b["names"],
        str(b["names_to_half"]) if b["names_to_half"] is not None else "--",
        pc(c["a"]["pnl_share"]), pc(c["b"]["pnl_share"]), pc(c["c"]["pnl_share"]), pc(c["c"]["trade_share"]),
        tp["symbol"], tp["side"], tp["entry"], tp["hold"], tp["pnl_bp"],
        100 * (tp["share_raw_pnl"] or 0.0),
        ("$%.4f" % tp["raw_px_prev"]) if tp["raw_px_prev"] is not None else "nan",
        ("%.2f" % tp["dv_pct_at_entry"]) if np.isfinite(tp["dv_pct_at_entry"]) else "nan",
        "a" if tp["fails_a"] else "-", "b" if tp["fails_b"] else "-"))


HEADER = ("  %-22s %8s %8s %6s %5s %5s %7s %7s %7s %7s   %-6s %-5s %-10s %3s %9s %6s %9s %5s %s" % (
    "signal", "PUBnet", "gross", "trades", "names", "half", "P&L(a)", "P&L(b)", "P&L(c)", "trd(c)",
    "top", "side", "entry", "hld", "pnl_bp", "share", "raw_px", "dvpct", "ab"))


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    lines = []
    say = lambda s="": (print(s), lines.append(s))
    say("D339  DIAGNOSTIC CENSUS: P&L below a $5 as-traded floor and below the dv28 cut, every F0 book")

    # [K]
    cache = Path(R.BC.CACHE)
    rp = REPO / "scripts" / "ragged_panel.py"
    assert cache.exists(), "[K] no score cache"
    assert cache.stat().st_mtime > rp.stat().st_mtime, "[K] npz older than ragged_panel.py"
    z = np.load(cache, allow_pickle=False)
    assert str(z["key"]) == R.BC.cache_key(M.B.FIXTURE), "[K] npz key != cache_key()"
    say("    [K] SCORE CACHE: key matches cache_key() with ragged_panel.py in the tuple; npz newer than the builder")

    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
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
    DV = X.roll_mean_T(CLOSE * VOL)
    base = z["warm"] & panel.live
    n, T = panel.live.shape
    HALF_PUB = np.full((T, n), np.nan)
    HALF_PUB[1:] = (z["cs_spread"][:, :-1] / 2.0 * 1e4).T
    G4 = (HALF_PUB, CLOSE, DV, finT)
    last_live = PA.last_live_bar(finT)
    first_live = np.array([int(np.flatnonzero(finT[:, i])[0]) if finT[:, i].any() else T for i in range(n)])
    years = np.array([int(d[:4]) for d in panel.dates])
    events = json.loads(Path(M.B.EVENTS).read_text())
    pool = [s for s in z.files if s not in ("key", "warm") and s not in EXCLUDED]
    assert len(pool) == 46, f"pool is {len(pool)}, not 46"
    say(f"  panel {finT.shape}, {len(pool)} signals ({time.time() - t0:.0f}s)")

    # RAW_FACTOR / RAW_CLOSE and [R]
    RAW_FACTOR = raw_factor(events, panel.symbols, panel.dates)
    RAW_CLOSE = CLOSE * RAW_FACTOR
    nosplit = [s for s in panel.symbols if not events["splits"].get(s)]
    assert nosplit and (RAW_FACTOR[:, sym[nosplit[0]]] == 1.0).all(), "[R] factor != 1 without splits"
    tv, iv = pos["2025-01-30"], sym["VSA"]
    assert abs(RAW_CLOSE[tv, iv] - 90.55 * 0.002) < 1e-3, f"[R] VSA raw {RAW_CLOSE[tv, iv]}"
    say(f"    [R] RAW PRICE: factor == 1 on every bar for {nosplit[0]} (no splits on file; {len(nosplit)} such names); "
        f"VSA 2025-01-30 adjusted {CLOSE[tv, iv]:.2f} -> as traded ${RAW_CLOSE[tv, iv]:.4f}")

    # F0 mask
    dj = json.loads(V31.DEALS.read_text())
    fb, drops, n_ok = V31.filing_bars(dj["deals"], panel.symbols, panel.dates, first_live, last_live,
                                      lambda f: f["form"] in V31.F0_FORMS)
    excl = V31.exclusion_mask(fb, n, T, last_live)
    pct = 100.0 * (excl & finT.T).sum() / finT.sum()
    assert n_ok == EXPECT_APPLIED and abs(pct - EXPECT_PCT) < 0.02, f"[F] {n_ok} / {pct:.3f}%"
    say(f"    [F] F0 MASK: {n_ok:,} filings applied, {pct:.2f}% of live name-bars excluded")

    def rank_f0(sig):
        return Y.rank_single({sig: np.where(excl, np.nan, z[sig])}, base, sig, n, T)

    def sim(rankT, k):
        W.BASE_HOLD = k
        res = W.simulate(A, Y.gate_from(rankT, finT), DEPTH, True, slots=True)
        return res, G22.contributions(res, r1T)

    # [1] and [6] on retrace_leg
    d338 = json.loads(D338_JSON.read_text())["group1"]["PUB"]
    res_rl, contrib_rl = sim(rank_f0(SIG_CHECK), K0)
    c_rl = G22.costed(res_rl, G4)
    worst = max(abs(c_rl["net_bp"] - d338["net_bp_bar"]), abs(c_rl["gross_bp"] - d338["gross_bp_bar"]))
    assert worst < 1e-9, f"[1] {worst:.2e}"
    say(f"    [1] IDENTITY: retrace_leg F0 book reproduces D338's PUB net {c_rl['net_bp']:+.4f} and gross "
        f"{c_rl['gross_bp']:+.4f} bp/bar to {worst:.1e}")
    broke = False
    try:
        bk = res_rl["book"].copy()
        bk[np.flatnonzero(res_rl["mask"])[:200]] += 5e-4
        bad = G22.costed(dict(res_rl, book=bk), G4)
        assert abs(bad["net_bp"] - d338["net_bp_bar"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6] [1] passed a book handed free money"
    say("    [6] and [1] raises on a book handed +5 bp on 200 masked bars")
    if a.selftest:
        say(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # the dv28 keep mask (already lagged: DV is roll_mean_T's lagged mean)
    keep28 = X.keep_mask(DV, finT, DV_PCT, True)
    say(f"  keep28 built: {100 * (~keep28 & finT).sum() / finT.sum():.1f}% of live name-bars fail ({time.time() - t0:.0f}s)")

    # ---- every book --------------------------------------------------------------
    books = {}
    for sig in pool:
        res, contrib = (res_rl, contrib_rl) if sig == SIG_CHECK else sim(rank_f0(sig), K0)
        try:
            cost = G22.costed(res, G4)
            books[sig] = book_stats(res, contrib, cost, RAW_CLOSE, keep28, DV, finT, panel)
        except (ZeroDivisionError, ValueError):
            books[sig] = None
    Q = V6.Q
    prim, pair = Q.COMPOSITES["C0_incumbent"]
    rk = Q.rank_composite({k: z[k] for k in ("hist_L", "macd_hist", "rsi")}, base, prim, pair, n, T)
    res_c0, contrib_c0 = sim(rk, 5)
    books["C0_incumbent(k5,unfilt)"] = book_stats(res_c0, contrib_c0, G22.costed(res_c0, G4), RAW_CLOSE, keep28, DV, finT, panel)
    say(f"  {len(books)} books simulated ({time.time() - t0:.0f}s)")

    # ---- universe-level ----------------------------------------------------------
    UA = np.zeros((T, n), bool)
    with np.errstate(invalid="ignore"):
        UA[1:] = RAW_CLOSE[:-1] < PRICE_FLOOR
    UB = ~keep28
    live = finT

    def ushare(m, sel=None):
        s = live if sel is None else (live & sel[:, None])
        return float((m & s).sum() / s.sum())

    universe = dict(overall=dict(a=ushare(UA), b=ushare(UB), c=ushare(UA | UB)), by_year={})
    for y in np.unique(years):
        sel = years == y
        universe["by_year"][int(y)] = dict(a=ushare(UA, sel), b=ushare(UB, sel), c=ushare(UA | UB, sel),
                                           live_name_bars=int((live & sel[:, None]).sum()))

    # ---- report ------------------------------------------------------------------
    order = sorted(books, key=lambda s: -(books[s]["net_bp_bar"] if books[s] else -np.inf))
    say("\n" + "=" * 150)
    say("CENSUS -- symmetric F0 books, depth 2, k=20, variant lens, PUB; sorted by PUB net bp/bar")
    say("  P&L(x) = share of contribution-P&L from trades in cut x; trd(c) = share of trades in cut c;")
    say("  (a) as-traded prior close < $5, (b) fails dv28 at entry, (c) either; 'ab' flags the top trade")
    say("=" * 150)
    say(HEADER)
    for s in order:
        say(fmt_row(s, books[s]))
    say("\n  MEAN RAW TRADE P&L (bp) INSIDE / OUTSIDE EACH CUT")
    say("  %-22s %6s %9s %9s   %6s %9s %9s   %6s %9s %9s" % (
        "signal", "n(a)", "in(a)", "out(a)", "n(b)", "in(b)", "out(b)", "n(c)", "in(c)", "out(c)"))
    fb_ = lambda x: ("%+9.1f" % x) if x is not None else "       --"
    for s in order:
        b = books[s]
        if b is None:
            continue
        c = b["cuts"]
        say("  %-22s %6d %s %s   %6d %s %s   %6d %s %s" % (
            s, c["a"]["n"], fb_(c["a"]["mean_bp_in"]), fb_(c["a"]["mean_bp_out"]),
            c["b"]["n"], fb_(c["b"]["mean_bp_in"]), fb_(c["b"]["mean_bp_out"]),
            c["c"]["n"], fb_(c["c"]["mean_bp_in"]), fb_(c["c"]["mean_bp_out"])))
    ok_books = [b for b in books.values() if b is not None]
    n_maj = {k: sum(1 for b in ok_books if (b["cuts"][k]["pnl_share"] or 0) > 0.5) for k in "abc"}
    say(f"\n  books with MORE THAN HALF their P&L in the cut: (a) {n_maj['a']}, (b) {n_maj['b']}, (c) {n_maj['c']} of {len(ok_books)}")
    say(f"  top trade fails (a): {sum(1 for b in ok_books if b['top_trade']['fails_a'])}, fails (b): "
        f"{sum(1 for b in ok_books if b['top_trade']['fails_b'])}, either: "
        f"{sum(1 for b in ok_books if b['top_trade']['fails_a'] or b['top_trade']['fails_b'])} of {len(ok_books)}")

    say("\n  UNIVERSE: share of LIVE name-bars failing each cut")
    u = universe["overall"]
    say("  %-8s %8s %8s %8s %12s" % ("year", "(a)", "(b)", "(c)", "live bars"))
    say("  %-8s %7.1f%% %7.1f%% %7.1f%% %12d" % ("all", 100 * u["a"], 100 * u["b"], 100 * u["c"], int(live.sum())))
    for y, v in universe["by_year"].items():
        say("  %-8d %7.1f%% %7.1f%% %7.1f%% %12d" % (y, 100 * v["a"], 100 * v["b"], 100 * v["c"], v["live_name_bars"]))

    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.floating, float)):
            return None if not np.isfinite(o) else float(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        return o

    out = dict(
        note="D339 DIAGNOSTIC census. Stage-0 measurement only: no predictions, no verdicts, nothing promoted. "
             "Each of the 46 signals as a symmetric F0 book (depth 2, k=20, variant lens, PUB) plus the incumbent C0 "
             "(k=5, unfiltered); cuts on the entry bar: (a) as-traded prior close < $5 (CLOSE x product of later split "
             "ratios), (b) fails the dv28 keep mask at entry, (c) either. P&L shares are contribution-based; means are "
             "raw trade P&L. Universe shares are over live name-bars.",
        cell=dict(depth=DEPTH, k=K0, filter="F0", lens="variant", convention="PUB", price_floor=PRICE_FLOOR, dv_pct=DV_PCT),
        f0=dict(applied=int(n_ok), drops=drops, excluded_live_pct=float(pct)),
        identity_worst=worst, keep28_fail_share_live=float((~keep28 & finT).sum() / finT.sum()),
        books=books, order=order, universe=universe,
        summary=dict(books_majority_in_cut=n_maj, n_books=len(ok_books)))
    OUT_JSON.write_text(json.dumps(clean(out), indent=1))
    OUT_TXT.write_text("\n".join(lines) + "\n")
    print(f"\nwrote {OUT_JSON.relative_to(REPO)} and {OUT_TXT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
