"""D283 -- the descending ranking.
Pre-registered in `docs/decisions/D283-the-descending-ranking.md`, commit
05722a0, BEFORE this file was written.

    uv run python scripts/run_descending_ranking.py

ONE CHANGE FROM D281: rank DESCENDING. Short the N HIGHEST lagged `hist_L`
instead of the N lowest.

THIS HYPOTHESIS IS POST-HOC AND THE RECORD SAYS SO FIRST. The direction was
chosen after seeing results -- D280's sign audit and D281's scored run, both of
which found the ASCENDING short loses. D280 reports 165 statistics (161
distinct) and the median largest |t| under a 161-test null is 2.86. The
principal asked for this test directly and that is the REASON it is run, not an
independent motivation. Read the pre-registration's opening section first.

THE CENTRAL RISK: SYMMETRY IS ASSUMED, NOT MEASURED
---------------------------------------------------
`data/d280_sign_audit.json` scored ONLY the ascending book: shorting the 25
LOWEST lagged `hist_L` loses 14.64 bp per night. THAT DOES NOT IMPLY THE
HIGHEST TAIL GAINS 14.64 BP. The two tails are DIFFERENT NAMES -- different
volatility, price, liquidity and borrow -- cross-sectional returns are skewed,
and FINDINGS 1b's variance tax is direction-blind and falls on whichever tail
is more volatile.

So this runner measures the DESCENDING book directly AND reports the ASCENDING
book beside it at matched N, in the sign audit's own basis-point units as well
as in scored Sharpe. `short_bp_table` is that deliverable and it is the finding
either way.

TWO POPULATIONS, because D280 measured OPPOSITE IC SIGNS in them
---------------------------------------------------------------
  ALL   every live, warm name with a finite (md_L, hist_L) pair. D281's
        population. Lagged `hist_L` IC over it: -0.00524, t -1.79.
  QUAL  `hist_L < 0 & md_L >= 0`. D279's and D256's qualifying set. IC inside
        it: +0.00462, t +1.43 -- the OTHER SIGN.
A sign-flipped arm therefore has an opposite prior in each, and carrying only
one would leave the study unable to say whether a result is a property of the
DIRECTION or of the POPULATION.

BOTH KNOWN CONTROL DEFECTS ARE DESIGNED AGAINST
-----------------------------------------------
  rnd-N  D279 scored the same nominal cell -1.528 and -1.633 on two different
         RNG sequences: ONE DRAW IS NOT A DISTRIBUTION. Drawn FIVE times here,
         reported as min/median/max, and hurdle C is scored against the MEDIAN
         with C-star (beats the MAX) reported beside it.
  per-N  NOT turnover-matched on an unfiltered universe -- no qualifying
         condition means no vacancies, and D281 measured a 0.002x ratio. The
         ratio is computed per cell and anything under 0.10x is FLAGGED and its
         comparison demoted to a holding-period comparison in the record.

THE LAG, AND WHY THIS FILE ASSERTS RATHER THAN TRUSTS. D279's first result did
not exist: `top_n` ranked with `score[:, t]` and `top25` scored +2.250 Sharpe
unlagged against -0.638 lagged. The fix lives inside `top_n`, which calls `lag1`
unconditionally. A FIX IN A DEPENDENCY IS NOT A GUARANTEE IN A CALLER, so
`audit_lag` below re-derives the held set from `score[:, t-1]` in a second
implementation that does NOT call `top_n`, in BOTH directions, and raises on the
first disagreement.

Every cell is NET and GROSS (zero fees, zero borrow, zero rf). D279 established
the book loses GROSS on this fixture, so THE GROSS NUMBER IS THE INFORMATIVE ONE.
Hurdle H is computed, printed, and EXCLUDED from every verdict under R7's
corollary -- D281 watched a RANDOM control clear it at the 100th percentile on
both legs while losing money.

Constants frozen from D279/D281: 5 bp/side, borrow 3%/yr, rf 4%, PPY 252,
seed 0, 300 null draws. No fourth N. Nothing is varied.
"""

from __future__ import annotations

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


B = _load("d256", "run_book_single_names.py")
C = _load("d279", "run_concentrated_short.py")
TD = _load("d279_turnover", "d279_turnover_decomposition.py")
EP = _load("d279_eprime", "d279_fix_eprime.py")
RP, U = B.RP, B.U

OUT = REPO / "data" / "d283_descending_summary.json"
D281_JSON = REPO / "data" / "d281_unfiltered_summary.json"
D279_JSON = REPO / "data" / "d279_concentrated_summary.json"

N_LEVELS = C.N_LEVELS                      # (10, 25, 50), frozen from D279
N_SIMS, SEED = C.N_SIMS, C.SEED            # 300 draws, seed 0
PPY, RF, BORROW, FEE = C.PPY, C.RF, C.BORROW, C.FEE
RND_DRAWS = 5                              # defect 1: a control needs a spread
SPLIT_DATE = "2018-01-01"                  # the sign audit's window, for comparability
MIN_NAMES = 20                             # d280_score_extrapolation.MIN_NAMES
PER_TURNOVER_FLOOR = 0.10                  # defect 2: below this, per-N is not matched
UNIVERSES = ("ALL", "QUAL")
DIRECTIONS = ("dsc", "asc")


# ---------------------------------------------------------------- OHLC grids
def build_grids(panel, cleaned):
    """(n, T) open/high/low/close grids on the panel's date grid.

    Deliberately duplicated from `d280_forecast_precheck.build_grids` rather
    than imported: the D280 files are under concurrent use in another session
    and this study must not depend on their state. Twelve lines is cheaper than
    a coupling."""
    pos = {d: i for i, d in enumerate(panel.dates)}
    n, T = panel.closes.shape
    g = {c: np.full((n, T), np.nan) for c in ("open", "high", "low", "close")}
    for i, s in enumerate(panel.symbols):
        for st in cleaned[s]:
            t = pos[st.timestamp[:10]]
            b = st.bar
            g["open"][i, t], g["high"][i, t] = b.open, b.high
            g["low"][i, t], g["close"][i, t] = b.low, b.close
    return g


# ------------------------------------------------------------- the R9 gate
def audit_lag(base, score, n, pos, descending):
    """Re-derive the held set from `score[:, t-1]`, in BOTH directions.

    A SECOND IMPLEMENTATION, deliberately not a call into `top_n`: the point is
    to disagree with it if it is wrong, and a check that shares the code it
    checks cannot. It partitions the eligible indices into finite and non-finite
    scores, sorts the finite block by the RAW score in the stated direction, and
    appends the non-finite block in panel order -- which is what `top_n`'s
    `where(isfinite, s, inf)` plus stable ascending argsort amounts to, arrived
    at from the other end.

    Returns bars verified; raises on the first mismatch."""
    if np.any(base[:, 0] != 0.0):
        raise AssertionError("base column 0 is non-zero; hold_book did not lag")
    T = base.shape[1]
    checked = 0
    for t in range(1, T):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size == 0:
            continue
        if q.size <= n:
            want = q
        else:
            s = score[q, t - 1]                       # EXPLICITLY the prior bar
            fin = np.isfinite(s)
            key = -s[fin] if descending else s[fin]
            order = np.concatenate([q[fin][np.argsort(key, kind="stable")], q[~fin]])
            want = order[:n]
        got = np.flatnonzero(pos[:, t] != 0.0)
        if got.size != want.size or not np.array_equal(np.sort(got), np.sort(want)):
            raise AssertionError(
                f"{'desc' if descending else 'asc'} top{n} bar {t}: held set does "
                f"not match the rank of score[:, t-1]")
        checked += 1
    return checked


def held_rank_pctile(base, score, pos, shift):
    """Mean cross-sectional percentile of the HELD names in the bar's score.

    `shift=1` scores them on `score[:, t-1]` (what the book may see), `shift=0`
    on `score[:, t]` (the bar it earns). Percentile 0 is the LOWEST score. An
    ascending book sits near 0; a DESCENDING book must sit near 1, and if it
    does not the direction did not take."""
    acc = []
    for t in range(1, base.shape[1]):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size < 2:
            continue
        h = np.flatnonzero(pos[:, t] != 0.0)
        if h.size == 0:
            continue
        s = score[q, t - shift]
        s = np.where(np.isfinite(s), s, np.inf)
        rank = np.empty(q.size, dtype=float)
        rank[np.argsort(s, kind="stable")] = np.arange(q.size)
        acc.append(rank[np.searchsorted(q, h)] / max(q.size - 1, 1))
    return float(np.concatenate(acc).mean()) if acc else float("nan")


# ------------------------------------------ the asymmetry deliverable, in bp
def short_bp(base, pos, tgt, oos, n_min):
    """What a SHORT of the HELD names earns against the same bar's cross-section.

    `short P&L = -(mean(held) - mean(eligible))`, in basis points, no costs.
    POSITIVE = the short makes money. This is `d280_sign_audit`'s statistic with
    one change: the held set comes from THE BOOK ACTUALLY SCORED rather than
    being re-selected, so the number describes the cells in the grid above it.

    The eligible population is the book's own base, which additionally requires
    warm-up and a finite `md_L` where the audit required only a finite score --
    so these values are comparable to the audit's in units and construction but
    not identical in universe. Reported over the audit's OOS window."""
    per_bar = []
    for t in range(base.shape[1]):
        if not oos[t]:
            continue
        u = (base[:, t] != 0.0) & np.isfinite(tgt[:, t])
        if int(u.sum()) < max(MIN_NAMES, n_min + 5):
            continue
        h = (pos[:, t] != 0.0) & np.isfinite(tgt[:, t])
        if not h.any():
            continue
        per_bar.append(-(tgt[h, t].mean() - tgt[u, t].mean()))
    if len(per_bar) < 30:
        return None
    v = np.array(per_bar)
    return {"short_bp": float(v.mean() * 1e4),
            "t": float(v.mean() / (v.std(ddof=1) / np.sqrt(v.size))),
            "bars": int(v.size), "pct_positive": float((v > 0).mean())}


def shift_left(x):
    """`out[:, t] = x[:, t+1]`. `d280_sign_audit`'s `nxt`, restated.

    NOT COSMETIC, and it is why the bp table below is reported at TWO
    alignments. The audit scores its selection with `C.lag1(hs)` -- so column
    `t` carries `hs[t-1]` -- AND takes its targets through `nxt`, so column `t`
    carries bar `t+1`'s return. The pair is therefore `hs[t-1]` against
    `return[t+1]`. **The book D279, D281 and this study actually trade pairs
    `hs[t-1]` against `return[t]`**: `hold_book` lags the mask one bar, `top_n`
    lags the score one bar, and `pooled_returns` earns bar `t` on the position
    held at bar `t`. Either lag alone is correct; both together is ONE BAR TOO
    MANY, and the motivating -14.64 bp therefore describes a book one session
    staler than the one being scored here.

    Both alignments are computed rather than asserted: `book` is the one the
    grid trades, `audit` is the one the motivating number was measured at, and
    printing them side by side is what turns the claim into a measurement."""
    out = np.full_like(x, np.nan)
    out[:, :-1] = x[:, 1:]
    return out


def pnl_components(panel, pos, comps):
    """Pooled per-bar GROSS P&L of a book, split by window.

    Same pooling as `RP.pooled_returns` -- position times return, summed over
    names, divided by the LIVE count -- with zero cost, so these are gross. A
    non-finite component on a held name-bar contributes zero and is counted."""
    lv = panel.live
    denom = np.maximum(panel.n_live(), 1)
    p = pos * lv
    out = {}
    for name, g in comps.items():
        ok = np.isfinite(g)
        out[name] = {"series": (p * np.where(ok, g, 0.0)).sum(axis=0) / denom,
                     "missing_held": int(((p != 0.0) & ~ok).sum())}
    return out


def summarise_component(series):
    m = float(series.mean())
    sd = float(series.std(ddof=1))
    return {"annualised": m * PPY, "bp_per_bar": m * 1e4,
            "t": (m / (sd / np.sqrt(series.size))) if sd > 0 else float("nan")}


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=FEE)
    n, T = panel.closes.shape
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    print(f"loaded + signals {time.time() - t0:.0f}s   {n} names x {T:,} bars", flush=True)

    ok = ~(np.isnan(md) | np.isnan(hs)) & warm
    bases = {"ALL": -B.hold_book(ok, warm),                          # D281's population
             "QUAL": -B.hold_book((hs < 0) & (md >= 0) & ok, warm)}  # D279's / D256's
    for u, b in bases.items():
        print(f"  {u:5s} universe: {int((b != 0).sum()):,} name-bars", flush=True)

    # ---- the books. RNG order is fixed and documented: universe, then N, then
    # the five rnd draws, then per. Changing the order changes every control. ----
    # A zero-cost panel for every GROSS number: same positions, no fees, no
    # borrow, no rf. D279 established the book loses gross on this fixture.
    free = type(panel)(**{**vars(panel),
                          "cost_fraction": np.zeros_like(panel.cost_fraction)})
    sc_net = lambda p: RP.score(panel, p, 0, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)
    sc_gro = lambda p: RP.score(free, p, 0, ppy=PPY, rf_annual=0.0, borrow_annual=0.0)

    # ---- the books. RNG order is fixed and documented: universe, then N, then
    # the five rnd draws, then per. Changing the order changes every control.
    # Draws 1..4 of rnd-N are SCORED AND DISCARDED -- 30 extra position grids is
    # 1.5 GB on this panel and only their statistics are needed. ----
    rng = np.random.default_rng(SEED)
    books, rnd_net, rnd_gro = {}, {}, {}
    for u, base in bases.items():
        books[f"{u}|all"] = base
        for N in N_LEVELS:
            books[f"{u}|dsc{N}"] = C.top_n(base, -hs, N)     # THE TREATMENT: N HIGHEST
            books[f"{u}|asc{N}"] = C.top_n(base, hs, N)      # D281 / D279 reproduced
            key = f"{u}|rnd{N}"
            rnd_net[key], rnd_gro[key] = [], []
            for d in range(RND_DRAWS):
                p = C.top_n(base, hs, N, rng=rng)
                rnd_net[key].append(sc_net(p))
                rnd_gro[key].append(sc_gro(p))
                if d == 0:
                    books[key] = p                           # draw 0 carries the nulls
            books[f"{u}|per{N}"] = TD.persistent_rnd(base, N, rng)
    print(f"built {len(books)} scored books, {RND_DRAWS} rnd draws each "
          f"{time.time() - t0:.0f}s", flush=True)

    # ---- R9 GATE. Nothing downstream runs until the lag is verified. ----
    print("\n  LAG AUDIT -- the check D279 failed:", flush=True)
    r = np.expm1(panel.total_log_returns)
    live = panel.live & np.isfinite(hs) & np.isfinite(C.lag1(hs)) & np.isfinite(r)
    audit = {"corr_score_t_return_t": float(np.corrcoef(hs[live], r[live])[0, 1]),
             "corr_score_lag1_return_t":
                 float(np.corrcoef(C.lag1(hs)[live], r[live])[0, 1])}
    print(f"    corr(hist_L at t,   return at t) : {audit['corr_score_t_return_t']:+.4f}"
          f"   ranking on this is peeking")
    print(f"    corr(hist_L at t-1, return at t) : "
          f"{audit['corr_score_lag1_return_t']:+.4f}   the tradeable version", flush=True)
    for u, base in bases.items():
        for d in DIRECTIONS:
            for N in N_LEVELS:
                p = books[f"{u}|{d}{N}"]
                # THE RAW SCORE AND A DIRECTION FLAG, never the negation `top_n`
                # was handed. If `-hs` were mis-ordering the book, this would say so.
                bars = audit_lag(base, hs, N, p, descending=(d == "dsc"))
                pl = held_rank_pctile(base, hs, p, 1)
                pn = held_rank_pctile(base, hs, p, 0)
                audit[f"{u}|{d}{N}"] = {"bars_verified": bars,
                                        "mean_pctile_lagged": pl,
                                        "mean_pctile_contemporaneous": pn}
                print(f"    {u:4s} {d}{N:<3d} {bars:,} bars re-derived from "
                      f"score[:, t-1] and MATCHED; held names at pctile "
                      f"{pl:.4f} LAGGED / {pn:.4f} contemporaneous", flush=True)
    print(f"  LAG AUDIT PASSED {time.time() - t0:.0f}s\n", flush=True)

    # ---- NET and GROSS for every retained book. ----
    net = {k: sc_net(p) for k, p in books.items()}
    gro = {k: sc_gro(p) for k, p in books.items()}
    print(f"scored {len(books)} books {time.time() - t0:.0f}s\n", flush=True)

    # ---- REPRODUCTION CHECK. The ascending cells and the bases are already-counted
    # D281 / D279 cells; re-measuring one is not a new look, but failing to check
    # that it reproduces would be a new defect. ----
    print("  REPRODUCTION of already-counted cells (asc == D281 / D279, to 1e-6):")
    repro = {}
    for path, uni, pref, keymap in (
            (D281_JSON, "ALL", "hist_L", {"all": "all", **{f"asc{N}": f"top{N}" for N in N_LEVELS}}),
            (D279_JSON, "QUAL", "S1_short", {"all": "all", **{f"asc{N}": f"top{N}" for N in N_LEVELS}})):
        if not path.exists():
            print(f"    {path.name} MISSING -- check skipped, and that is a gap")
            repro[uni] = "artifact missing"
            continue
        pub = json.loads(path.read_text())["cells"]
        for mine, theirs in keymap.items():
            k, pk = f"{uni}|{mine}", f"{pref}|{theirs}"
            if pk not in pub:
                continue
            d = abs(net[k]["excess_sharpe"] - pub[pk]["excess_sharpe"])
            repro[k] = {"published": pub[pk]["excess_sharpe"],
                        "here": net[k]["excess_sharpe"], "abs_diff": d}
            flag = "OK" if d < 1e-6 else "**MISMATCH**"
            print(f"    {k:12s} vs {pk:16s} {pub[pk]['excess_sharpe']:+.6f} -> "
                  f"{net[k]['excess_sharpe']:+.6f}   diff {d:.2e}  {flag}")
    print(flush=True)

    # ---- THE GRID ----
    print(f"  {'cell':14s} {'expo':>7s} {'turnover':>10s} {'net CAGR':>9s} {'net SR':>8s} "
          f"{'GROSS CAGR':>11s} {'GROSS SR':>9s} {'maxDD':>8s} {'trades':>8s}")
    for k in books:
        a, g = net[k], gro[k]
        print(f"  {k:14s} {a['exposure_gross']:6.2%} {a['turnover_units']:10,.0f} "
              f"{a['cagr']:+8.2%} {a['excess_sharpe']:+8.3f} {g['cagr']:+10.2%} "
              f"{g['excess_sharpe']:+9.3f} {a['max_drawdown']:7.2%} {a['entries']:8,d}",
              flush=True)

    # ---- CONTROL DEFECT 1: the rnd-N spread, which D279 could not report ----
    print("\n  rnd-N AS A DISTRIBUTION, not a draw -- 5 seeds, GROSS Sharpe:")
    rnd_stats = {}
    for k, v in rnd_gro.items():
        s = np.array([x["excess_sharpe"] for x in v])
        sn = np.array([x["excess_sharpe"] for x in rnd_net[k]])
        rnd_stats[k] = {
            "gross_sharpe": {"min": float(s.min()), "median": float(np.median(s)),
                             "max": float(s.max()), "spread": float(s.max() - s.min())},
            "net_sharpe": {"min": float(sn.min()), "median": float(np.median(sn)),
                           "max": float(sn.max()), "spread": float(sn.max() - sn.min())},
            "gross_money_median": float(np.median([x["total_return"] for x in v])),
            "gross_money_max": float(np.max([x["total_return"] for x in v])),
            "net_money_median": float(np.median([x["total_return"] for x in rnd_net[k]])),
            "net_money_max": float(np.max([x["total_return"] for x in rnd_net[k]])),
            "draws": RND_DRAWS}
        print(f"    {k:14s} min {s.min():+.3f}  median {np.median(s):+.3f}  "
              f"max {s.max():+.3f}   SPREAD {s.max() - s.min():.3f}", flush=True)

    # ---- CONTROL DEFECT 2: is per-N actually turnover-matched here? ----
    print("\n  per-N TURNOVER MATCH -- D281 measured 0.002x on an unfiltered universe:")
    turn_flags = {}
    for u in UNIVERSES:
        for N in N_LEVELS:
            t_ = net[f"{u}|dsc{N}"]["turnover_units"]
            ratio_p = net[f"{u}|per{N}"]["turnover_units"] / max(t_, 1e-9)
            ratio_r = net[f"{u}|rnd{N}"]["turnover_units"] / max(t_, 1e-9)
            bad = ratio_p < PER_TURNOVER_FLOOR
            turn_flags[f"{u}|{N}"] = {"per_over_dsc": ratio_p, "rnd_over_dsc": ratio_r,
                                      "per_not_turnover_matched": bool(bad)}
            print(f"    {u:4s} N={N:<3d} per {ratio_p:8.4f}x   rnd {ratio_r:6.2f}x   "
                  f"{'** per-N IS NOT TURNOVER-MATCHED **' if bad else 'per-N matched'}")

    # ---- THE ASYMMETRY DELIVERABLE, in the sign audit's own units ----
    print(f"\n  ASYMMETRY -- descending vs ascending at matched N, in SHORT bp against")
    print(f"  the same bar's cross-section. POSITIVE = the short makes money. OOS from")
    print(f"  {SPLIT_DATE}, no costs. Symmetry would make dsc the mirror of asc.")
    print(f"  D280's audit, ascending, ALL, overnight: -17.60 / -14.64 / -10.97 bp.\n")
    g = build_grids(panel, cleaned)
    O, Cl = g["open"], g["close"]
    lv2 = panel.live[:, 1:] & panel.live[:, :-1]

    def prev_pair(num, den):
        out = np.full_like(num, np.nan)
        out[:, 1:] = np.where(lv2, num[:, 1:] / den[:, :-1] - 1.0, np.nan)
        return out

    windows = {"overnight gap": prev_pair(O, Cl),
               "intraday": np.where(panel.live, Cl / O - 1.0, np.nan),
               "close-to-close": prev_pair(Cl, Cl),
               "total (scored)": np.where(panel.live, np.expm1(panel.total_log_returns),
                                          np.nan)}
    del g, O, Cl                       # 26 books already cost ~1.4 GB on this panel
    dates = np.array(panel.dates)
    oos = dates >= SPLIT_DATE
    # TWO ALIGNMENTS. `book` is what the scored grid trades (hs[t-1] -> return[t]);
    # `audit` is what d280_sign_audit measured (hs[t-1] -> return[t+1]). Added to
    # this runner AFTER the pre-registration was committed and BEFORE the run, as
    # a correctness check on the motivating number. IT SCORES NO CELL.
    aligned = {"book": windows,
               "audit": {w: shift_left(t) for w, t in windows.items()}}
    print(f"  {'universe':>8s} {'dir':>4s} {'N':>4s} {'window':>16s} {'align':>6s} "
          f"{'short bp':>10s} {'t':>7s} {'bars':>7s}")
    bp = {}
    for u in UNIVERSES:
        for N in N_LEVELS:
            for d in DIRECTIONS:
                for wname in windows:
                    for al, grids in aligned.items():
                        v = short_bp(bases[u], books[f"{u}|{d}{N}"], grids[wname],
                                     oos, N)
                        if v is None:
                            continue
                        bp[f"{u}|{d}{N}|{wname}|{al}"] = v
                        print(f"  {u:>8s} {d:>4s} {N:4d} {wname:>16s} {al:>6s} "
                              f"{v['short_bp']:+10.2f} {v['t']:+7.2f} {v['bars']:7,d}",
                              flush=True)
            print()

    print("  THE ASYMMETRY ITSELF -- dsc bp + asc bp. Perfect antisymmetry gives 0;")
    print("  a positive sum means the DESCENDING tail is the better short by that much,")
    print("  a negative sum means the ascending loss OVERSTATES the descending gain.\n")
    asym = {}
    for al in aligned:
        for u in UNIVERSES:
            for N in N_LEVELS:
                for wname in windows:
                    a = bp.get(f"{u}|asc{N}|{wname}|{al}")
                    dd = bp.get(f"{u}|dsc{N}|{wname}|{al}")
                    if a is None or dd is None:
                        continue
                    z = {"asc_bp": a["short_bp"], "dsc_bp": dd["short_bp"],
                         "sum": a["short_bp"] + dd["short_bp"],
                         "dsc_over_mirror": dd["short_bp"] / -a["short_bp"]
                         if a["short_bp"] != 0 else float("nan")}
                    asym[f"{al}|{u}|{N}|{wname}"] = z
                    print(f"  {al:>6s} {u:>5s} N={N:<3d} {wname:>16s}  "
                          f"asc {a['short_bp']:+8.2f}  dsc {dd['short_bp']:+8.2f}  "
                          f"sum {z['sum']:+8.2f}  dsc / mirror "
                          f"{z['dsc_over_mirror']:+7.2f}x")
            print()

    # ---- OVERNIGHT / INTRADAY DECOMPOSITION OF THE BOOK'S GROSS P&L ----
    print("  GROSS P&L DECOMPOSITION of the DESCENDING books -- annualised, over the")
    print("  FULL scored span, pooled exactly as `pooled_returns` does, zero cost.")
    print("  gap + intraday will NOT sum to the scored total: the components are RAW")
    print("  OHLC and the total carries dividends. The residual is printed.\n")
    print(f"  {'cell':14s} {'overnight':>11s} {'t':>7s} {'intraday':>11s} {'t':>7s} "
          f"{'close-close':>12s} {'total':>11s} {'div resid':>11s} {'missing':>9s}")
    decomp = {}
    for u in UNIVERSES:
        for d in DIRECTIONS:
            for N in N_LEVELS:
                k = f"{u}|{d}{N}"
                comp = pnl_components(panel, books[k], windows)
                row = {w: summarise_component(comp[w]["series"]) for w in windows}
                row["missing_held_gap"] = comp["overnight gap"]["missing_held"]
                row["dividend_residual_annual"] = (row["total (scored)"]["annualised"]
                                                   - row["close-to-close"]["annualised"])
                decomp[k] = row
                print(f"  {k:14s} {row['overnight gap']['annualised']:+10.2%} "
                      f"{row['overnight gap']['t']:+7.2f} "
                      f"{row['intraday']['annualised']:+10.2%} "
                      f"{row['intraday']['t']:+7.2f} "
                      f"{row['close-to-close']['annualised']:+11.2%} "
                      f"{row['total (scored)']['annualised']:+10.2%} "
                      f"{row['dividend_residual_annual']:+10.2%} "
                      f"{row['missing_held_gap']:9,d}", flush=True)
        print()

    # ---- E-prime OVER THE HELD BOOK. Expected to degenerate; says so if it does. ----
    print(f"  E-prime over the HELD BOOK (never the panel) {time.time() - t0:.0f}s ...",
          flush=True)
    eff = {}
    for k, p in books.items():
        e, kept = EP.eff_over_book(panel, p)
        # E-prime >= 0.9 x headcount means the correlation matrix is effectively
        # the identity: D279 scored 28.00 on 28 names, D281 63.00 on 63.
        degen = bool(kept > 0 and e >= 0.9 * kept)
        eff[k] = {"eff_book": e, "names_over_min_overlap": kept, "degenerate": degen}
        print(f"    {k:14s} names>=250 held {kept:5d}   E-prime {e:8.2f}"
              + ("   <-- ~= N: the correlation matrix is the IDENTITY and E-prime "
                 "has stopped measuring anything" if degen else "")
              + f"   {time.time() - t0:.0f}s", flush=True)

    # ---- Rotation nulls. ONE SHARED OFFSET VECTOR: rotation_null reseeds from SEED
    # and walks every symbol in panel order, so draw k uses identical offsets in
    # every book and the per-draw max across books is a valid best-of-K. ----
    print(f"\n  rotation nulls, {N_SIMS} draws each, K={len(books)} -- REPORTED, NOT "
          f"DECISIVE (R7 corollary) ...", flush=True)
    cells, draws = {}, []
    for k, p in books.items():
        sh, mn = RP.rotation_null(panel, p, 0, n_sims=N_SIMS, seed=SEED, ppy=PPY,
                                  rf_annual=RF, borrow_annual=BORROW)
        c = dict(net[k])
        c["gross"] = gro[k]
        c["sharpe_pct"] = float((sh < net[k]["excess_sharpe"]).mean() * 100)
        c["money_pct"] = float((mn < net[k]["total_return"]).mean() * 100)
        c["null_sharpe_p50"] = float(np.percentile(sh, 50))
        c["null_sharpe_p95"] = float(np.percentile(sh, 95))
        c["H"] = bool(c["sharpe_pct"] >= 95 and c["money_pct"] >= 95)
        c["V"] = bool(c["cagr"] > 0)
        c.update(eff[k])
        c["top_name_share"] = C.per_symbol_concentration(panel, p, 0)
        c["breakeven_borrow"] = C.breakeven_borrow(panel, p, 0, net[k])
        cells[k] = c
        draws.append(sh)
        print(f"    {k:14s} {c['sharpe_pct']:5.1f}th / {c['money_pct']:5.1f}th   "
              f"null p50 {c['null_sharpe_p50']:+.3f} p95 {c['null_sharpe_p95']:+.3f}   "
              f"{time.time() - t0:.0f}s", flush=True)
    floor = float(np.percentile(np.max(np.vstack(draws), axis=0), 95))
    print(f"\n  best-of-{len(books)} floor: {floor:+.3f}", flush=True)
    print("  AND IT UNDERSTATES THE CORRECTION: the DIRECTION tested here was chosen")
    print("  after D280's 165 statistics, which no floor computed inside this study")
    print("  can see. Read any t or percentile against 161 + 69, not against 69.\n")

    # ---- THE DECOMPOSITION: descending minus each control, and minus ascending ----
    print("  RANKING CONTRIBUTION -- descending minus each control, gross and net,")
    print("  and DESCENDING MINUS ASCENDING, which is the asymmetry in scored units.")
    print("  D281 measured the ASCENDING contribution over per-N at "
          "-0.167 / -0.116 / -0.113 GROSS.\n")
    print(f"  {'univ':>5s} {'N':>4s} {'vs rndMED net':>14s} {'vs rndMED GROSS':>16s} "
          f"{'vs per net':>11s} {'vs per GROSS':>13s} {'dsc-asc GROSS':>14s}")
    contrib = {}
    for u in UNIVERSES:
        for N in N_LEVELS:
            d_, a_ = net[f"{u}|dsc{N}"], net[f"{u}|asc{N}"]
            dg, ag = gro[f"{u}|dsc{N}"], gro[f"{u}|asc{N}"]
            pe, pg = net[f"{u}|per{N}"], gro[f"{u}|per{N}"]
            rs = rnd_stats[f"{u}|rnd{N}"]
            v = {"vs_rnd_median_net": d_["excess_sharpe"] - rs["net_sharpe"]["median"],
                 "vs_rnd_median_gross": dg["excess_sharpe"] - rs["gross_sharpe"]["median"],
                 "vs_rnd_max_gross": dg["excess_sharpe"] - rs["gross_sharpe"]["max"],
                 "vs_per_net": d_["excess_sharpe"] - pe["excess_sharpe"],
                 "vs_per_gross": dg["excess_sharpe"] - pg["excess_sharpe"],
                 "dsc_minus_asc_gross": dg["excess_sharpe"] - ag["excess_sharpe"],
                 "dsc_minus_asc_net": d_["excess_sharpe"] - a_["excess_sharpe"],
                 "asc_vs_per_gross": ag["excess_sharpe"] - pg["excess_sharpe"]}
            contrib[f"{u}|{N}"] = v
            print(f"  {u:>5s} {N:4d} {v['vs_rnd_median_net']:+14.3f} "
                  f"{v['vs_rnd_median_gross']:+16.3f} {v['vs_per_net']:+11.3f} "
                  f"{v['vs_per_gross']:+13.3f} {v['dsc_minus_asc_gross']:+14.3f}")

    # ---- HURDLES. C requires BOTH controls, Sharpe AND money, GROSS AND NET. ----
    print(f"\n  {'cell':14s} {'net CAGR':>9s} {'net SR':>8s} {'GROSS SR':>9s} "
          f"{'V':>3s} {'C':>3s} {'C*':>3s} {'F':>3s} {'E-prime':>8s} {'(H)':>5s}  ALL")
    surv = []
    for k in books:
        u, mode = k.split("|")
        c = cells[k]
        if mode.startswith("dsc"):
            N = mode[3:]
            rs = rnd_stats[f"{u}|rnd{N}"]
            pe, pg = net[f"{u}|per{N}"], gro[f"{u}|per{N}"]
            legs = [c["excess_sharpe"] > rs["net_sharpe"]["median"],
                    c["total_return"] > rs["net_money_median"],
                    gro[k]["excess_sharpe"] > rs["gross_sharpe"]["median"],
                    gro[k]["total_return"] > rs["gross_money_median"],
                    c["excess_sharpe"] > pe["excess_sharpe"],
                    c["total_return"] > pe["total_return"],
                    gro[k]["excess_sharpe"] > pg["excess_sharpe"],
                    gro[k]["total_return"] > pg["total_return"]]
            strict = [c["excess_sharpe"] > rs["net_sharpe"]["max"],
                      c["total_return"] > rs["net_money_max"],
                      gro[k]["excess_sharpe"] > rs["gross_sharpe"]["max"],
                      gro[k]["total_return"] > rs["gross_money_max"]]
            c["C"] = bool(all(legs))
            c["C_star"] = bool(all(legs) and all(strict))
            c["C_legs"] = [bool(x) for x in legs]
            c["per_not_turnover_matched"] = turn_flags[f"{u}|{N}"][
                "per_not_turnover_matched"]
        else:
            c["C"] = c["C_star"] = False
            c["C_legs"] = []
        c["F"] = bool(c["excess_sharpe"] > floor)
        c["Eprime"] = bool(c["eff_book"] >= 3.0 and c["entries"] >= 500)
        # H IS EXCLUDED FROM `clears_all` BY PRE-REGISTRATION -- R7's corollary.
        c["clears_all"] = bool(c["V"] and c["C"] and c["F"] and c["Eprime"])
        if c["clears_all"]:
            surv.append(k)
        y = lambda b: "YES" if b else "no"  # noqa: E731
        print(f"  {k:14s} {c['cagr']:+8.2%} {c['excess_sharpe']:+8.3f} "
              f"{gro[k]['excess_sharpe']:+9.3f} {y(c['V']):>3s} {y(c['C']):>3s} "
              f"{y(c['C_star']):>3s} {y(c['F']):>3s} {y(c['Eprime']):>8s} "
              f"{y(c['H']):>5s}  {'** YES **' if c['clears_all'] else 'no'}")

    print(f"\n  SURVIVORS: {surv or 'NONE'}")
    json.dump({"study": "D283", "hypothesis": "post-hoc; direction chosen after "
               "D280's 165 statistics and D281's result; see the record's opening "
               "section", "seed": SEED, "n_sims": N_SIMS, "fee_bps": FEE,
               "borrow_charged": BORROW, "rf": RF, "ppy": PPY,
               "n_levels": list(N_LEVELS), "rnd_draws": RND_DRAWS,
               "split_date_for_bp_table": SPLIT_DATE,
               "floor": floor, "K": len(books),
               "true_multiplicity_note": "the D228 floor is over K books in this study "
               "only; the direction was chosen after D280's 161 distinct statistics, so "
               "read any t or percentile against 161 + 69",
               "hurdle_H": "computed, reported, EXCLUDED from every verdict (R7 corollary)",
               "reproduction_check": repro, "lag_audit": audit,
               "rnd_distribution": rnd_stats, "turnover_match": turn_flags,
               "short_bp": bp, "asymmetry": asym, "pnl_decomposition": decomp,
               "contribution": contrib, "cells": cells, "survivors": surv,
               "elapsed_s": round(time.time() - t0, 1)},
              open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
