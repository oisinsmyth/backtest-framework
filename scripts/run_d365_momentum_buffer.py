"""D365 -- the momentum buffer book: a broad, slow, hysteretic long, and whether its edge is momentum or size.

    uv run python scripts/run_d365_momentum_buffer.py --selftest
    uv run python scripts/run_d365_momentum_buffer.py --stage0
    uv run python scripts/run_d365_momentum_buffer.py --cell 95:80 --draws 200 --part 0
    uv run python scripts/run_d365_momentum_buffer.py --report
    --out-dir DIR    (every stage; default data/ -- the smoke runs pass temp/... so that nothing under data/ is touched)

Pre-registration: docs/decisions/D365-the-momentum-buffer-book.md (48410cb). Within-sample confirmation with nulls, not a
discovery: the primary cell was chosen by an eleven-combination screen run on this same fixture. Nothing is promoted (R15).

THE CONSTRUCTION (pre-reg section 1), verbatim:

    pct = pct_of(P, "mom_252_21")                     # run_d358_flat_sleeve's percentile grid: V50.lagged -> floor -> F0 ->
    prev = zeros(n, bool)                             # V47.percentile_grid.  pct[t] reads the score at t-1.
    for t in range(m_start, T):
        p = pct[t]; alive = elig[t] & isfinite(p)
        cur = where(prev, alive & (p > lo), alive & (p > hi))
        hold[t] = cur; prev = cur

Long, equal weight over whatever qualifies, hedged each bar by the floored universe's equal-weight return. No slot cap, no
stop, no target, no time limit.  FILL (D340): the entry bar earns `ocT - m_f_oc`, every later bar `r1T - m_f`.  The
close-to-close variant (`r1T - m_f` on every bar) is built beside it as the screen's own basis and is what [ID] holds.

THE GRID: hi in {90, 95} x lo in {60, 70, 80, 85}, lo < hi -- 8 cells.  PRIMARY 95/80.  The daily-refresh cell hi = lo = 90
is NOT one of the eight; it is reported beside for Q5.

TWO GROSS STATISTICS, both reported, never mixed:
    gross      the SCREEN's: the pooled mean over held name-bars of the hedged return (`nanmean(X[hold & ok])`).  Every
               pre-registered target number (+3.43, +2.65, +3.87, -0.56) is in this statistic, so it is the headline and it
               is what [ID] reproduces.
    gross_bar  the BOOK's: the mean over deployed bars of the per-bar equal-weight book return.  The per-bar series is what
               carries vol, Sharpe, maxDD, the splits and control C, so its own mean is reported beside the pooled one.
    They differ only in how bars are weighted (the pooled mean weights a bar by its membership).

COST.  `cost bp/bar = round trip x turnover`, turnover = entries / mean members / bars (G22.costed's own definition; [TURN]
asserts the identity and the equality with G22.costed key for key).  THIS BOOK HAS ONE LEG, so the round trip is
`2 x half-spread + 2 x $0.005 / price x 1e4` -- exactly V47.two_c, and exactly half of G22.costed's `4 x half + 4 x
commission`, which prices the two-legged spread book G22 was written for.  [TURN] asserts that factor of two explicitly
rather than quietly dividing.  BOTH D363 CONVENTIONS:
    held-median  the line the record has used since D285 and the line the screen used: the median half-spread and the median
                 as-traded price over the HELD NAME-BARS.  (G22.costed's own held median is over the ledger's ENTRY bars; it
                 is reported as a third line and asserted against.)
    per-trade    each trade charged its own name's half-spread at its own entry and exit bars plus 2 x $0.005 / its own
                 as-traded close at entry; cost bp/bar = sum over trades / total position-bars.
PUB primary, PB beside.

STAGE 0 (pre-reg section 2) -- the premise, and it is not the drift:
    1. the top decile's hedged next-bar drift against the equal-weight floored market AND against a DV-DECILE-MATCHED hedge
       (the equal-weight return of eligible names in the same dollar-volume decile that day, the name itself excluded);
    2. the rank-band profile of both across (0,10] (10,25] (25,50] (50,75] (75,90] (90,100], with median price, median PUB
       half-spread, median DV and mean beta per band;
    3. a two-factor decomposition: the top decile's equal-weight excess return regressed on the market (`m_f`) and on a size
       factor (top DV decile EW minus bottom DV decile EW, same eligible universe), intercept in bp/bar with a PLAIN OLS
       standard error (primary) and a Newey-West(5) one beside.
    DV deciles come from `P["DV"]`, which `roll_mean_T` already lags one bar, so R9 is satisfied without a further shift.

THE NULLS on the primary cell (seeds [SEED, 365, cell_index, arm, part]; arm ROT 0, A' 1, SIZE 2, C 3):
    ROT   24 deterministic shifts -- D348's rank rotation carried to a threshold book.  D348 shifts the rank ASSIGNMENT
          inside its 25-name gate (`eff = (rk + shift) % N_BASE`).  Here the gate is the whole day, so shift s reassigns each
          eligible name's score to the score of the name k = round(s * L / 25) places above it in that day's ranking: the
          day's multiset of percentiles is preserved exactly, the count above any threshold is preserved exactly, and the
          selected band walks down the ranking.  The book is rebuilt from the rotated score and re-run.
    A'    200 draws (--draws) -- D351's per-name circular rotation of the SCORE within that name's ELIGIBLE bars
          (EB.rotate_signals, the committed implementation), the book rebuilt from the rotated score.
    SIZE  1 deterministic run, NOT a draw: the identical buffer construction with `pct_of(P, "dollar_vol")` as the score.
          A RIVAL HYPOTHESIS, not a random control, and reported as such.
    C     1,000 draws -- random direction on the per-bar contribution ledger (V58.control_C on the book series in bp).
    Per draw: hedged net PUB bp/bar, gross bp/bar, net Sharpe, turnover, mean members.
    The GRID-MAX null uses ROT's 24 shifts as SHARED offsets: the max over the 8 cells is recomputed on each shift.

HOLDOUT GUARD: run_d362's audit hook pattern, installed on `open` before the first module of the chain executes -- a path
containing 'holdout' is REFUSED before the file is touched, and every open under data/fixtures is counted by basename.

ASSERTIONS [K][F0][R][HOLDOUT-GUARD][ID][BUF][LAG][FILL][TURN][SZ][S][ROT][A'][SIZE][C][6] -- pre-reg section 7.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

# ------------------------------------------------------------------ the holdout guard: before ANY module of the chain executes
_OPENED = dict(n=0, fixtures=Counter(), refused=0)


def _audit(event, args):
    if event != "open":
        return
    p = args[0]
    if isinstance(p, bytes):
        p = p.decode(errors="replace")
    elif not isinstance(p, (str, os.PathLike)):
        return
    s = os.fspath(p)
    low = s.replace("\\", "/").lower()
    _OPENED["n"] += 1
    if "holdout" in low:
        _OPENED["refused"] += 1
        raise RuntimeError(f"[HOLDOUT-GUARD] refused to open {s}")
    if "data/fixtures/" in low:
        _OPENED["fixtures"][low.rsplit("/", 1)[-1]] += 1


sys.addaudithook(_audit)

sys.path.insert(0, str(REPO / "scripts"))
import memo_load                                   # noqa: E402  -- each chain script executes ONCE per process
memo_load.install()                                # must precede the first _load()


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


PREP = _load("d348p", "d348_prep.py")                       # installs memo_load too; the alias chain executes once
V58 = _load("d358r", "run_d358_flat_sleeve.py")             # pct_of (THE percentile grid), control_C, clean
V50 = _load("d350r", "run_d350_long_timing_screen.py")      # four_groups, lagged, clean (memoised to V58's own _load)
V47 = PREP.V47
G22, EB, UF, X = PREP.G22, PREP.EB, PREP.UF, PREP.X

STUDY = 365
SEED = V47.SEED
ANN = 252.0
CONVS = V47.CONVS                                            # ("PB", "PUB")
PER_SHARE = X.PER_SHARE                                      # $0.005 a share
CROSSINGS_ONE_LEG = 2.0                                      # this book has ONE leg: in and out. G22 prices four crossings.
N_BASE = PREP.W.N_BASE                                       # 25 -- D348's gate width, and so ROT's 24 shifts
HIS, LOS = (90, 95), (60, 70, 80, 85)
GRID = [(hi, lo) for hi in HIS for lo in LOS if lo < hi]     # 8 cells
PRIMARY = (95, 80)
DAILY = (90, 90)                                             # the daily-refresh cell, reported beside; NOT one of the eight
SCORE, SIZE_SCORE = "mom_252_21", "dollar_vol"
FILLS = ("open", "cc")                                       # "open" is the declared convention (D340); "cc" is the screen's
ARM = dict(ROT=0, APRIME=1, SIZE=2, C=3)
ROT_SHIFTS = tuple(range(1, N_BASE))                         # 24
APRIME_DRAWS, C_DRAWS = 200, 1000
BANDS = ((0.0, 10.0), (10.0, 25.0), (25.0, 50.0), (50.0, 75.0), (75.0, 90.0), (90.0, 100.0))
YEAR_MIN_BARS = 500                                          # the screen's own definition of a "full year" (held name-bars)
DATA = REPO / "data"
SELFTEST_TMP = REPO / "temp" / "d365_selftest"
clean = V50.clean

# The screen's printed targets (pre-reg section 5, "check"). [ID] holds the close-to-close variant to these.
SCREEN_TARGETS = {(95, 80): dict(members=41.0, turnover=0.0101, gross=3.43, net_pub=2.65),
                  (90, 90): dict(members=46.0, turnover=0.0593, gross=3.87, net_pub=-0.56)}


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, stage0=d / "d365_stage0.json", ctrl=str(d / "d365_ctrl_{hi}_{lo}_p{part}.json"),
                report=d / "d365_momentum_buffer.json")


def cell_name(hi, lo):
    return f"{hi}:{lo}"


def cell_index(hi, lo):
    return GRID.index((hi, lo)) if (hi, lo) in GRID else len(GRID)      # the daily-refresh cell gets the slot after the grid


def fq(x, nd=2):
    return "-" if x is None or not np.isfinite(x) else f"{x:+.{nd}f}"


def guard_line():
    fx = _OPENED["fixtures"]
    return (f"{_OPENED['n']:,} file opens audited in this process, {sum(fx.values())} under data/fixtures "
            f"({', '.join(f'{k} x{v}' for k, v in sorted(fx.items())) or 'none'}); none containing 'holdout' opened "
            f"({_OPENED['refused']} refused: the probe)")


def assert_HOLDOUT_GUARD():
    probe = DATA / "fixtures" / "holdout_probe_that_does_not_exist.txt"
    assert not probe.exists()
    try:
        open(probe)
    except RuntimeError as e:
        assert "[HOLDOUT-GUARD]" in str(e), str(e)
    else:
        raise AssertionError("[HOLDOUT-GUARD] the audit hook did not fire")
    assert not any("holdout" in k for k in _OPENED["fixtures"]), "[HOLDOUT-GUARD] a holdout fixture was opened"
    print(f"    [HOLDOUT-GUARD] {guard_line()}")


# ================================================================== the construction
def hold_grid(pct, elig, hi, lo, m_start):
    """The pre-registration's loop, verbatim. hold[t, i]: name i is in the book on bar t."""
    T, n = pct.shape
    hold = np.zeros((T, n), bool)
    prev = np.zeros(n, bool)
    for t in range(m_start, T):
        p = pct[t]
        alive = elig[t] & np.isfinite(p)
        cur = np.where(prev, alive & (p > lo), alive & (p > hi))
        hold[t] = cur
        prev = cur
    return hold


def hold_loop(pct, elig, hi, lo, m_start, names=None):
    """[BUF]'s second implementation: a plain Python loop, one name at a time, scalars only."""
    T, n = pct.shape
    names = range(n) if names is None else names
    out = np.zeros((T, n), bool)
    for i in names:
        held = False
        for t in range(m_start, T):
            p = pct[t, i]
            alive = bool(elig[t, i]) and (p == p)                     # p == p: finite/NaN without numpy
            held = (alive and p > lo) if held else (alive and p > hi)
            out[t, i] = held
    return out


def hold_cummax(pct, elig, hi, lo, m_start):
    """[LAG]'s independent derivation. NO sequential state and it never calls hold_grid or hold_loop: a name is held at t iff
    `stay` holds at t and an `enter` bar occurred at or after the last bar where `stay` failed. Cumulative maxima give both."""
    T, n = pct.shape
    with np.errstate(invalid="ignore"):
        alive = np.asarray(elig, bool) & np.isfinite(pct)
        stay = alive & (pct > lo)
        enter = alive & (pct > hi)
    stay[:m_start] = False
    enter[:m_start] = False
    idx = np.arange(T, dtype=np.int64)[:, None]
    last_break = np.maximum.accumulate(np.where(stay, -1, idx), axis=0)
    last_enter = np.maximum.accumulate(np.where(enter, idx, -1), axis=0)
    return stay & (last_enter > last_break)


def entries_of(hold):
    """ent[t, i]: the bar name i is entered on."""
    ent = np.zeros_like(hold)
    ent[0] = hold[0]
    ent[1:] = hold[1:] & ~hold[:-1]
    return ent


def returns_grids(P):
    """(X_cc, X_oc): the hedged close-to-close and open-to-close returns, (T, n)."""
    r1T, ocT = np.asarray(P["r1T"], float), np.asarray(P["ocT"], float)
    m_f, m_oc = np.asarray(P["m_f"], float), np.asarray(P["m_f_oc"], float)
    return r1T - m_f[:, None], ocT - m_oc[:, None]


def ret_of(X_cc, X_oc, ent, fill):
    """The bar return under a fill convention. 'open': the entry bar earns ocT - m_f_oc, later bars r1T - m_f (D340)."""
    if fill == "cc":
        return X_cc
    return np.where(ent, X_oc, X_cc)


def book_series(hold, ret, elig):
    """(book, mask, members, n_ret): the per-bar equal-weight mean of the hedged return over the held names."""
    with np.errstate(invalid="ignore"):
        h = hold & np.isfinite(ret) & elig
    n_ret = h.sum(axis=1)
    s = np.where(h, ret, 0.0).sum(axis=1)
    with np.errstate(invalid="ignore"):
        book = np.where(n_ret > 0, s / np.maximum(n_ret, 1), np.nan)
    return book, n_ret > 0, hold.sum(axis=1), n_ret


def trades_of(hold, ret):
    """The ledger (row, e0, age, pnl, side=0), one entry per contiguous run of hold. A run reaching the last bar is still in
    the ledger and is counted as open_at_end. pnl is the sum of the run's FINITE bar returns (the bars the book averaged)."""
    T, n = hold.shape
    trades, open_end, nan_bars = [], 0, 0
    for i in range(n):
        col = hold[:, i]
        if not col.any():
            continue
        d = np.diff(col.astype(np.int8), prepend=np.int8(0), append=np.int8(0))
        st = np.flatnonzero(d == 1)
        en = np.flatnonzero(d == -1)                                  # exclusive
        v = ret[:, i]
        for a, b in zip(st, en):
            seg = v[a:b]
            fin = np.isfinite(seg)
            nan_bars += int((~fin).sum())
            trades.append((int(i), int(a), int(b - a), float(seg[fin].sum()), 0))
            open_end += int(b == T)
    trades.sort(key=lambda t: (t[1], t[0]))
    return trades, open_end, nan_bars


# ================================================================== costing
def round_trip_one_leg(hs, px):
    """ONE leg: buy and sell. 2 half-spreads + 2 commissions. == V47.two_c's per-name figure; == G22.costed's / 2."""
    return 2.0 * hs + CROSSINGS_ONE_LEG * PER_SHARE / px * 1e4


def held_name_bar_median(h, A):
    """The screen's / D285's held median: over the HELD NAME-BARS, not over the ledger's entry bars.
    `A[h]` rather than `nanmedian(where(h, A, nan))` -- the same finite multiset, so the same median, without allocating a
    (T, n) copy per call. [ID] holds this against `screen_stats`, which keeps the screen's expression verbatim."""
    v = np.asarray(A, float)[h]
    return float(np.nanmedian(v)) if v.size else np.nan


def per_trade_two_c(P, trades, cv):
    """D363's per-trade line: own half-spread at own entry AND exit bar + 2 x $0.005 / own as-traded close at entry.
    A NaN exit half falls back to the entry half (counted); a NaN entry half falls back to the ledger median (counted)."""
    HALF = np.asarray(P["HALF"][cv], float)
    RAWC = np.asarray(P["RAW_CLOSE"], float)
    ent_h = np.array([HALF[e0, row] for row, e0, _a, _p, _s in trades])
    ex_h = np.array([HALF[min(e0 + a - 1, HALF.shape[0] - 1), row] for row, e0, a, _p, _s in trades])
    px = np.array([RAWC[e0, row] for row, e0, _a, _p, _s in trades])
    med = float(np.nanmedian(ent_h))
    n_ent_nan = int((~np.isfinite(ent_h)).sum())
    ent_h = np.where(np.isfinite(ent_h), ent_h, med)
    n_ex_nan = int((~np.isfinite(ex_h)).sum())
    ex_h = np.where(np.isfinite(ex_h), ex_h, ent_h)
    two_c = ent_h + ex_h + CROSSINGS_ONE_LEG * PER_SHARE / px * 1e4
    return two_c, dict(entry_half_nan=n_ent_nan, exit_half_nan=n_ex_nan, mean_two_c=float(two_c.mean()),
                       median_two_c=float(np.median(two_c)), median_entry_half=float(np.median(ent_h)),
                       median_exit_half=float(np.median(ex_h)), median_price=float(np.nanmedian(px)))


def screen_stats(hold, X, ok, HALF, RAWC, m_start):
    """The screen's arithmetic, transcribed from the reference implementation and NOT re-derived: the pooled name-bar gross,
    entries per member-bar, the name-bar median half-spread and price, cost = round trip x turnover. [ID] holds this."""
    h = hold & ok
    nm = hold.sum(axis=1)[m_start:]
    ent = (hold[1:] & ~hold[:-1]).sum(axis=1)
    turn = ent.sum() / max(nm[nm > 0].sum(), 1)
    gross = float(np.nanmean(np.where(h, X, np.nan))) * 1e4
    hs = float(np.nanmedian(np.where(h, HALF, np.nan)))
    px = float(np.nanmedian(np.where(h, RAWC, np.nan)))
    rt = round_trip_one_leg(hs, px)
    return dict(members=float(nm.mean()), turnover=float(turn), hold_bars=1.0 / turn if turn > 0 else np.nan,
                gross_bp=gross, half_spread=hs, price=px, round_trip=rt, cost_bp=rt * turn, net_bp=gross - rt * turn,
                entries=int(ent.sum()), position_bars=int(nm.sum()))


def cell_block(P, hold, ret, fill, want_trades=True):
    """Every statistic of one (cell, fill): the screen's pooled line, the book's per-bar line, both cost conventions, both
    spread conventions, the ledger and its splits."""
    elig = np.asarray(P["elig"], bool)
    HALF, RAWC = P["HALF"], np.asarray(P["RAW_CLOSE"], float)
    book, mask, members, n_ret = book_series(hold, ret, elig)
    with np.errstate(invalid="ignore"):
        h = hold & np.isfinite(ret) & elig
    ent = entries_of(hold)
    bars = int(mask.sum())
    pos_bars = int(hold.sum())
    entries = int(ent.sum())
    ent_in_mask = int(ent[mask].sum())
    held_in_mask = float(members[mask].mean()) if bars else np.nan
    turnover = ent_in_mask / held_in_mask / bars if bars and held_in_mask > 0 else np.nan
    turnover_all = entries / pos_bars if pos_bars else np.nan
    b = book[mask]
    g_bar = float(b.mean()) * 1e4 if bars else np.nan
    vol = float(b.std(ddof=1)) * 1e4 if bars > 1 else np.nan
    eq = np.cumsum(b)
    maxdd = float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4 if bars else np.nan
    g_pool = float(np.nanmean(np.where(h, ret, np.nan))) * 1e4
    trades, open_end, nan_bars = trades_of(hold, ret) if want_trades else ([], 0, 0)
    out = dict(fill=fill, bars=bars, position_bars=pos_bars, entries=entries, entries_in_mask=ent_in_mask,
               mean_members=held_in_mask, max_members=int(members.max()),
               # the SCREEN's membership: position-bars over EVERY bar from m_start, including the ~900 before the momentum
               # warm-up lets the book hold anything. That is the statistic the pre-registered "41 members" is in.
               mean_members_all_bars=pos_bars / max(P["T"] - P["m_start"], 1),
               turnover=float(turnover), turnover_all_bars=float(turnover_all),
               hold_bars=float(1.0 / turnover) if turnover and turnover > 0 else None,
               gross_bp=g_pool, gross_bar_bp=g_bar, vol_bp=vol, maxdd_bp=maxdd,
               trades=len(trades), open_at_end=open_end, nan_return_bars_in_runs=nan_bars,
               entries_per_year=entries / (bars / ANN) if bars else None,
               bars_held_no_return=int(((members > 0) & ~mask).sum()))
    for cv in CONVS:
        hs = held_name_bar_median(h, HALF[cv])
        px = held_name_bar_median(h, RAWC)
        rt = round_trip_one_leg(hs, px)
        cost = rt * turnover
        d = dict(half_spread=hs, price=px, round_trip=rt, cost_bp=cost,
                 net_bp=g_pool - cost, net_bar_bp=g_bar - cost,
                 sharpe_gross=g_bar / vol * np.sqrt(ANN) if vol and vol > 0 else None,
                 sharpe_net=(g_bar - cost) / vol * np.sqrt(ANN) if vol and vol > 0 else None,
                 pct_per_year=(g_pool - cost) * ANN / 100.0,
                 breakeven_half_spread_bp_side=((g_pool / turnover) - CROSSINGS_ONE_LEG * PER_SHARE / px * 1e4) / 2.0
                 if turnover and turnover > 0 else None)
        if trades:
            tc, tinfo = per_trade_two_c(P, trades, cv)
            cost_pt = float(tc.sum()) / pos_bars
            d["per_trade"] = dict(tinfo, cost_bp=cost_pt, net_bp=g_pool - cost_pt, net_bar_bp=g_bar - cost_pt,
                                  sharpe_net=(g_bar - cost_pt) / vol * np.sqrt(ANN) if vol and vol > 0 else None,
                                  pct_per_year=(g_pool - cost_pt) * ANN / 100.0)
            # G22's own held median is over the ledger's ENTRY bars; carried as a third line, never as the headline
            hs_e = float(np.nanmedian([HALF[cv][e0, row] for row, e0, _a, _p, _s in trades]))
            px_e = float(np.nanmedian([np.asarray(P["CLOSE"], float)[e0, row] for row, e0, _a, _p, _s in trades]))
            rt_e = round_trip_one_leg(hs_e, px_e)
            d["entry_median"] = dict(half_spread=hs_e, price=px_e, round_trip=rt_e, cost_bp=rt_e * turnover,
                                     net_bp=g_pool - rt_e * turnover)
        out[cv] = d
    out["_book"] = book
    out["_mask"] = mask
    out["_members"] = members
    out["_trades"] = trades
    return out


def splits_block(P, block, hold, ret):
    """By year, era halves and down-years, on BOTH the pooled name-bar gross (the screen's own split) and the book series."""
    elig = np.asarray(P["elig"], bool)
    years = np.asarray(P["years"])
    T = hold.shape[0]
    t = np.arange(T)
    book, mask = block["_book"], block["_mask"]
    with np.errstate(invalid="ignore"):
        h = hold & np.isfinite(ret) & elig
    cost = {cv: block[cv]["cost_bp"] for cv in CONVS}

    def sub(sel):
        hh = h & sel[:, None]
        n = int(hh.sum())
        mm = mask & sel
        d = dict(name_bars=n, bars=int(mm.sum()))
        if n:
            gp = float(np.nanmean(np.where(hh, ret, np.nan))) * 1e4
            d["gross_bp"] = gp
            d["gross_bar_bp"] = float(book[mm].mean()) * 1e4 if mm.any() else None
            for cv in CONVS:
                d[f"net_bp_{cv}"] = gp - cost[cv]
        return d
    by_year = {int(y): sub(years == y) for y in np.unique(years[mask])}
    full = {y: v for y, v in by_year.items() if v["name_bars"] >= YEAR_MIN_BARS}
    return dict(by_year=by_year, full_years=sorted(full), n_full_years=len(full),
                full_years_positive_gross=int(sum(1 for v in full.values() if v["gross_bp"] > 0)),
                full_years_positive_net_PUB=int(sum(1 for v in full.values() if v["net_bp_PUB"] > 0)),
                era1=sub(t < T // 2), era2=sub(t >= T // 2), era_split_bar=T // 2,
                down_years=sub(np.isin(years, list(P["down_years"]))))


# ================================================================== assertions
def assert_ID(P, pct, elig, X_cc, ok_cc):
    """[ID] the close-to-close variant reproduces the screen. The screen's own arithmetic is transcribed in screen_stats and
    checked against the record's PRINTED targets (41 members, 1.01%, +3.43, +2.65; 5.93%, +3.87, -0.56); the runner's own
    close-to-close cell_block must then equal it to 1e-9 on gross, turnover, cost, net and members."""
    HALF, RAWC, m_start = P["HALF"]["PUB"], np.asarray(P["RAW_CLOSE"], float), P["m_start"]
    lines, worst = [], 0.0
    for (hi, lo), tgt in SCREEN_TARGETS.items():
        hold = hold_grid(pct, elig, hi, lo, m_start)
        s = screen_stats(hold, X_cc, ok_cc, HALF, RAWC, m_start)
        assert abs(round(s["members"]) - tgt["members"]) < 1e-9, f"[ID] {hi}/{lo} members {s['members']:.2f} vs {tgt['members']}"
        assert abs(round(100 * s["turnover"], 2) - round(100 * tgt["turnover"], 2)) < 1e-9, \
            f"[ID] {hi}/{lo} turnover {100 * s['turnover']:.4f}% vs {100 * tgt['turnover']:.2f}%"
        assert abs(round(s["gross_bp"], 2) - tgt["gross"]) < 1e-9, f"[ID] {hi}/{lo} gross {s['gross_bp']:.4f} vs {tgt['gross']}"
        assert abs(round(s["net_bp"], 2) - tgt["net_pub"]) < 1e-9, f"[ID] {hi}/{lo} net PUB {s['net_bp']:.4f} vs {tgt['net_pub']}"
        blk = cell_block(P, hold, X_cc, "cc")
        for k_s, k_b in (("gross_bp", "gross_bp"), ("turnover", "turnover")):
            worst = max(worst, abs(s[k_s] - blk[k_b]))
        for k in ("half_spread", "price", "round_trip", "cost_bp", "net_bp"):
            worst = max(worst, abs(s[k] - blk["PUB"][k]))
        worst = max(worst, abs(s["members"] - blk["position_bars"] / (P["T"] - P["m_start"])))
        worst = max(worst, abs(s["entries"] - blk["entries"]), abs(s["position_bars"] - blk["position_bars"]))
        lines.append(f"{hi}/{lo} members {s['members']:.0f} turn {100 * s['turnover']:.2f}% gross {s['gross_bp']:+.2f} "
                     f"net PUB {s['net_bp']:+.2f}")
    assert worst < 1e-9, f"[ID] the runner's close-to-close cell_block differs from the screen's arithmetic by {worst:.2e}"
    return lines, worst


def assert_BUF(pct, elig, m_start, rng, n_names=60):
    """[BUF] the plain Python loop equals the vectorised construction on every bar and name (a sample of names for the loop's
    sake, the whole grid for the cummax implementation which is checked under [LAG])."""
    n = pct.shape[1]
    names = np.sort(rng.choice(n, size=min(n_names, n), replace=False))
    worst = []
    for hi, lo in ((95, 80), (90, 90), (90, 60)):
        A = hold_grid(pct, elig, hi, lo, m_start)
        B = hold_loop(pct, elig, hi, lo, m_start, names=names)
        bad = int((A[:, names] != B[:, names]).sum())
        assert bad == 0, f"[BUF] {hi}/{lo}: {bad} (bar, name) disagreements between the loop and the vectorised state"
        worst.append(f"{hi}/{lo} {A[:, names].sum():,} held name-bars over {len(names)} names")
    return worst, names


def sc_of(P, raw):
    """V50.lagged's closure BEFORE the one-bar shift: the (n, T) floored, deal-filtered, warm-based score. Every step is
    elementwise, which is what lets [LAG] perturb one cell and recompute one percentile row."""
    sc = UF.apply_floor_replace(np.where(np.asarray(P["excl"]), np.nan, raw), np.asarray(P["keep"]))
    return np.where(np.asarray(P["base"]), sc, np.nan)


def pct_from_raw(P, raw):
    """The whole grid from a supplied raw (n, T) score; asserted bit-identical to the study's own grid before any
    perturbation is made."""
    out = np.full((P["T"], P["n"]), np.nan)
    out[1:] = sc_of(P, raw)[:, :-1].T
    return V47.percentile_grid(out)


def pct_row_from_sc(sc, r, n):
    """Row r of the LAGGED percentile grid: V47.percentile_grid on the single column sc[:, r - 1]. The record's own
    implementation, called on one bar."""
    if r == 0:
        return np.full(n, np.nan)
    return V47.percentile_grid(np.ascontiguousarray(sc[:, r - 1])[None, :])[0]


def assert_LAG(P, pct, elig, m_start, rng, n_probe=25):
    """[LAG] three legs.
    (a) an INDEPENDENT derivation of the held set -- cumulative maxima over `stay`/`enter`, no sequential state, never calls
        hold_grid or hold_loop -- equals the book's hold grid on every bar and name, on every cell of the grid;
    (b) the lag itself, per row: perturbing the RAW score at own-bar t leaves percentile rows t - 2 .. t untouched and moves
        row t + 1 -- pct[t] reads the score at t - 1. Rows are recomputed one at a time so that the probe is cheap;
    (c) once, on the WHOLE grid: the same perturbation leaves the HELD SET unchanged at every bar <= t and changes it at
        t + 1."""
    for hi, lo in GRID + [DAILY]:
        A = hold_grid(pct, elig, hi, lo, m_start)
        B = hold_cummax(pct, elig, hi, lo, m_start)
        bad = int((A != B).sum())
        assert bad == 0, f"[LAG] {hi}/{lo}: the independent derivation differs on {bad} (bar, name) cells"
    hi, lo = PRIMARY
    hold = hold_grid(pct, elig, hi, lo, m_start)
    raw = np.array(P["score"](SCORE), dtype=float)                       # (n, T)
    sc = sc_of(P, raw)
    n, T = P["n"], P["T"]
    cand = np.argwhere(np.asarray(elig)[:-2] & np.isfinite(pct[:-2]))
    cand = cand[cand[:, 0] > m_start + 5]
    picks = rng.choice(len(cand), size=min(n_probe, len(cand)), replace=False)
    n_moved, n_same, n_full = 0, 0, 0
    for j, k in enumerate(picks):
        t, i = int(cand[k, 0]), int(cand[k, 1])
        if not np.isfinite(sc[i, t]):
            continue
        rows = [r for r in (t - 2, t - 1, t, t + 1) if 0 <= r < T]
        before = {r: pct_row_from_sc(sc, r, n) for r in rows}
        for r in rows:                                                    # the closure reproduces the study's own grid
            assert np.array_equal(before[r], pct[r], equal_nan=True), f"[LAG] the row closure differs from the study's grid at {r}"
        old = sc[i, t]
        sc[i, t] = np.nanmax(sc[:, t]) + 1e6
        after = {r: pct_row_from_sc(sc, r, n) for r in rows}
        sc[i, t] = old
        for r in rows:
            if r <= t:
                assert np.array_equal(after[r], before[r], equal_nan=True), \
                    f"[LAG] the raw score at own-bar {t} moved percentile row {r} (<= t)"
        n_same += 1
        if t + 1 < T and not np.array_equal(after[t + 1], before[t + 1], equal_nan=True):
            n_moved += 1
        # (c) once, on the WHOLE grid, on a name that is NOT held at t + 1: making it the day's top score must enter it
        if n_full == 0 and t + 1 < T and elig[t + 1, i] and not hold[t + 1, i]:
            r2 = raw.copy()
            r2[i, t] = np.nanmax(raw[:, t]) + 1e6
            p2 = pct_from_raw(P, r2)
            assert np.array_equal(p2[:t + 1], pct[:t + 1], equal_nan=True), f"[LAG] pct moved at or before {t}"
            h2 = hold_grid(p2, elig, hi, lo, m_start)
            assert np.array_equal(h2[:t + 1], hold[:t + 1]), f"[LAG] the held set moved at or before {t}"
            assert h2[t + 1, i] and not hold[t + 1, i], f"[LAG] the held set did NOT move at {t + 1}"
            n_full = 1
            del r2, p2, h2
    assert n_same > 0, "[LAG] no probe ran"
    assert n_full == 1, "[LAG] the whole-grid probe never ran"
    assert n_moved > 0, "[LAG] moving the raw score at t never moved the percentile at t + 1"
    return n_same, n_moved, n_full


def assert_FILL(P, hold, X_cc, X_oc):
    """[FILL] the entry bar earns ocT - m_f_oc and later bars r1T - m_f; the two books differ on EXACTLY the entry bars."""
    elig = np.asarray(P["elig"], bool)
    ent = entries_of(hold)
    r_open = ret_of(X_cc, X_oc, ent, "open")
    r_cc = ret_of(X_cc, X_oc, ent, "cc")
    assert np.array_equal(r_cc, X_cc, equal_nan=True), "[FILL] the close-to-close variant is not r1T - m_f everywhere"
    both = np.isfinite(r_open) & np.isfinite(r_cc)
    diff = both & (r_open != r_cc)
    assert not (diff & ~ent).any(), "[FILL] the two books differ off an entry bar"
    ent_defined = both & ent
    n_ent, n_diff = int(ent_defined.sum()), int(diff.sum())
    assert n_diff > 0.9 * n_ent, f"[FILL] only {n_diff} of {n_ent} defined entry bars differ"
    on = ent & elig & np.isfinite(X_oc)
    assert np.array_equal(np.where(on, r_open, 0.0), np.where(on, X_oc, 0.0)), "[FILL] an entry bar does not earn ocT - m_f_oc"
    later = hold & ~ent & elig & np.isfinite(X_cc)
    assert np.array_equal(np.where(later, r_open, 0.0), np.where(later, X_cc, 0.0)), "[FILL] a later bar does not earn r1T - m_f"
    return n_ent, n_diff


def assert_TURN(P, hold, ret, block):
    """[TURN] turnover == entries / member-bars from an INDEPENDENT count (the trade ledger), membership counts match the hold
    grid, and the arithmetic equals G22.costed's key for key -- with the ONE explicit exception that G22 prices four crossings
    (a two-legged spread book) where this book has two, so its cost is exactly twice this runner's."""
    trades = block["_trades"]
    assert trades, "[TURN] no trades"
    led_entries = len(trades)
    led_bars = int(sum(t[2] for t in trades))
    assert led_entries == block["entries"], f"[TURN] ledger {led_entries} entries vs grid {block['entries']}"
    assert led_bars == block["position_bars"], f"[TURN] ledger {led_bars} position-bars vs grid {block['position_bars']}"
    mask, members = block["_mask"], block["_members"]
    cnt = np.zeros(hold.shape[0], np.int64)
    for row, e0, age, _p, _s in trades:
        cnt[e0:e0 + age] += 1
    assert np.array_equal(cnt, members), "[TURN] the ledger's per-bar membership does not match the hold grid"
    lhs = block["turnover"]
    rhs = block["entries_in_mask"] / block["mean_members"] / block["bars"]
    assert abs(lhs - rhs) < 1e-15, f"[TURN] turnover identity {lhs} vs {rhs}"
    assert abs(block["turnover"] - block["turnover_all_bars"]) < 1e-12, \
        f"[TURN] the mask drops held bars: {block['turnover']} vs {block['turnover_all_bars']}"
    res = dict(book=block["_book"], mask=mask, ent=entries_of(hold).sum(axis=1).astype(np.int32),
               held=members.astype(np.int64), trades=trades)
    worst, n_keys = 0.0, 0
    g = G22.costed(res, P["G4"]["PUB"])
    for k, mine in (("gross_bp", block["gross_bar_bp"]), ("vol_bp", block["vol_bp"]), ("maxdd_bp", block["maxdd_bp"]),
                    ("turnover", block["turnover"]), ("held_per_bar", block["mean_members"]),
                    ("entries", block["entries_in_mask"]), ("bars", block["bars"]), ("trades", len(trades)),
                    ("sharpe_gross", block["PUB"]["sharpe_gross"])):
        worst = max(worst, abs(float(g[k]) - float(mine)))
        n_keys += 1
    # the factor of two, asserted rather than assumed
    rt_g22 = 4.0 * block["PUB"]["entry_median"]["half_spread"] + 4.0 * PER_SHARE / block["PUB"]["entry_median"]["price"] * 1e4
    assert abs(g["round_trip"] + g["commission_rt"] - rt_g22) < 1e-9, "[TURN] G22's round trip is not 4 half-spreads + 4 commissions"
    assert abs(rt_g22 - 2.0 * block["PUB"]["entry_median"]["round_trip"]) < 1e-9, \
        "[TURN] G22's four-crossing round trip is not exactly twice this book's two-crossing one"
    assert abs(g["cost_bp"] - 2.0 * block["PUB"]["entry_median"]["cost_bp"]) < 1e-9, "[TURN] G22's cost is not twice this book's"
    assert worst < 1e-9, f"[TURN] G22.costed disagrees by {worst:.2e}"
    return n_keys, worst, g


def assert_S(P, pct, elig, m_start, hi, lo, rng, book_fn=None):
    """[S] sign in money: +50 bp on ONE held name on ONE non-entry bar moves the book's bar by exactly 50 / n_held and moves
    no other bar; a favourable move pays positively. `book_fn` exists ONLY so that [6] can hand this a deliberately broken
    aggregator (an equal-weight SUM instead of the mean) and see the assertion raise."""
    book_fn = book_series if book_fn is None else book_fn
    hold = hold_grid(pct, elig, hi, lo, m_start)
    ent = entries_of(hold)
    X_cc, X_oc = returns_grids(P)
    ret = ret_of(X_cc, X_oc, ent, "open")
    book, mask, members, _ = book_fn(hold, ret, elig)
    cand = np.argwhere(hold & ~ent & np.isfinite(ret) & elig)
    cand = cand[cand[:, 0] > m_start + 10]
    t_, i_ = (int(v) for v in cand[rng.choice(len(cand))])
    r1p = np.array(P["r1T"], dtype=float)
    r1p[t_, i_] += 50e-4
    X2 = r1p - np.asarray(P["m_f"], float)[:, None]
    ret2 = ret_of(X2, X_oc, ent, "open")
    book2, mask2, _, _ = book_fn(hold, ret2, elig)
    n_held = int(members[t_])
    delta = (book2[t_] - book[t_]) * 1e4
    assert delta > 0, "[S] a favourable move did not pay positively"
    assert abs(delta - 50.0 / n_held) < 1e-9, f"[S] the book moved {delta:.6f} bp, expected {50.0 / n_held:.6f}"
    other = np.ones(book.size, bool)
    other[t_] = False
    assert np.array_equal(book[other], book2[other], equal_nan=True), "[S] the perturbation leaked to another bar"
    assert np.array_equal(mask, mask2), "[S] the perturbation changed the deployed mask"
    return t_, i_, n_held, delta


# ================================================================== Stage 0
def dv_level_pct(P):
    """The percentile grid of the dollar-volume LEVEL among eligible names -- the second size control, and the reason it
    exists is stated in the report: the pre-registration names `dollar_vol` as SIZE's score, and in this record's score cache
    `dollar_vol` is `log(dollar volume today) - median(log dollar volume over the trailing window)` (ragged_features
    .volume_scores) -- a relative-volume SURPRISE, not a size LEVEL. The pre-registered control is run exactly as written and
    this one is run beside it, because "is the book a size book" is a question about the level.
    `P["DV"]` is roll_mean_T's trailing 21-bar mean, already lagged one bar, so this conditions on nothing unseeable (R9)."""
    elig = np.asarray(P["elig"], bool)
    DV = np.asarray(P["DV"], float)
    return V47.percentile_grid(np.where(elig & np.isfinite(DV), DV, np.nan))


def dv_decile_grid(P):
    """The day's dollar-volume decile among ELIGIBLE names with a finite DV. P['DV'] is roll_mean_T's TRAILING mean, already
    lagged one bar, so this conditions on nothing the rule could not have seen (R9)."""
    elig = np.asarray(P["elig"], bool)
    DV = np.asarray(P["DV"], float)
    g = np.where(elig & np.isfinite(DV), DV, np.nan)
    dvpct = V47.percentile_grid(g)
    dec = np.where(np.isfinite(dvpct), np.clip(np.floor(dvpct / 10.0), 0, 9), -1).astype(np.int8)
    return dvpct, dec


def dv_matched_hedge(P, dec, V):
    """[SZ]'s object: for every eligible name-bar, the equal-weight return of the eligible names in the SAME dollar-volume
    decile that day, THE NAME ITSELF EXCLUDED. NaN where the pool would be empty (fewer than two names in the decile)."""
    elig = np.asarray(P["elig"], bool)
    V = np.asarray(V, float)
    T, n = V.shape
    out = np.full((T, n), np.nan)
    pool_n = np.zeros((T, n), np.int32)
    for t in range(T):
        d = dec[t]
        m = elig[t] & (d >= 0) & np.isfinite(V[t])
        if not m.any():
            continue
        dd = d[m]
        vv = V[t, m]
        s = np.bincount(dd, weights=vv, minlength=10)
        c = np.bincount(dd, minlength=10)
        idx = np.flatnonzero(m)
        cs, cc = s[dd], c[dd]
        with np.errstate(invalid="ignore", divide="ignore"):
            loo = np.where(cc >= 2, (cs - vv) / np.maximum(cc - 1, 1), np.nan)
        out[t, idx] = loo
        pool_n[t, idx] = cc - 1
    return out, pool_n


def assert_SZ(P, dec, dvm, pool_n, V, rng, n_probe=300):
    """[SZ] the matched pool is same-day, same-decile, eligible, and NEVER contains the name itself; every eligible name-bar
    either has a non-empty pool or is counted."""
    elig = np.asarray(P["elig"], bool)
    V = np.asarray(V, float)
    cand = np.argwhere(elig & np.isfinite(dvm))
    worst = 0.0
    for k in rng.choice(len(cand), size=min(n_probe, len(cand)), replace=False):
        t, i = int(cand[k, 0]), int(cand[k, 1])
        d = dec[t, i]
        peers = np.flatnonzero(elig[t] & (dec[t] == d) & np.isfinite(V[t]))
        peers = peers[peers != i]                                       # the name itself, removed by hand
        assert peers.size == pool_n[t, i], f"[SZ] pool size {peers.size} vs {pool_n[t, i]}"
        assert i not in set(peers.tolist()), "[SZ] the matched pool contains the name itself"
        worst = max(worst, abs(float(V[t, peers].mean()) - dvm[t, i]))
    assert worst < 1e-9, f"[SZ] the direct pool mean differs by {worst:.2e}"
    defined = elig & np.isfinite(V)
    empty = int((defined & ~np.isfinite(dvm)).sum())
    return worst, empty, int(defined.sum())


def ols(y, Xr, nw_lag=5):
    """Plain OLS with the classical standard error (PRIMARY, and this is what the report quotes) and a Newey-West(5) one
    beside it. Returns (coef, se_ols, se_nw)."""
    n, k = Xr.shape
    XtX_inv = np.linalg.inv(Xr.T @ Xr)
    b = XtX_inv @ (Xr.T @ y)
    e = y - Xr @ b
    s2 = float(e @ e) / (n - k)
    se = np.sqrt(np.diag(s2 * XtX_inv))
    S = (Xr * e[:, None]).T @ (Xr * e[:, None])
    for L in range(1, nw_lag + 1):
        w = 1.0 - L / (nw_lag + 1.0)
        G = (Xr[L:] * e[L:, None]).T @ (Xr[:-L] * e[:-L, None])
        S = S + w * (G + G.T)
    se_nw = np.sqrt(np.diag(XtX_inv @ S @ XtX_inv))
    return b, se, se_nw


def stage0(P, paths):
    t0 = time.time()
    print("\nSTAGE 0 -- the premise: is the top decile's drift momentum or size?")
    elig = np.asarray(P["elig"], bool)
    pct = V58.pct_of(P, SCORE)
    X_cc, _ = returns_grids(P)
    r1T = np.asarray(P["r1T"], float)
    m_f = np.asarray(P["m_f"], float)
    DV, beta, RAWC = np.asarray(P["DV"], float), np.asarray(P["beta"], float), np.asarray(P["RAW_CLOSE"], float)
    HALF = np.asarray(P["HALF"]["PUB"], float)
    dvpct, dec = dv_decile_grid(P)
    dvm, pool_n = dv_matched_hedge(P, dec, r1T)
    rng = np.random.default_rng([SEED, STUDY, 90])
    sz_worst, sz_empty, sz_defined = assert_SZ(P, dec, dvm, pool_n, r1T, rng)
    print(f"    [SZ] the DV-matched hedge is same-day, same-decile, eligible and excludes the name itself: 300 sampled pools "
          f"rebuilt by direct selection to {sz_worst:.1e}; {sz_empty:,} of {sz_defined:,} eligible name-bars ({100 * sz_empty / sz_defined:.3f}%) "
          f"have no pool (fewer than two names in their decile that day) and are counted, not silently dropped")
    X_dv = r1T - dvm

    def drift(m, A):
        v = np.where(m, A, np.nan)
        return float(np.nanmean(v)) * 1e4, int((m & np.isfinite(A)).sum())
    with np.errstate(invalid="ignore"):
        top = elig & (pct > 90.0)
    g_ew, n_ew = drift(top, X_cc)
    g_dv, n_dv = drift(top, X_dv)
    print(f"\n  1. TOP-DECILE DRIFT (pct > 90, hedged next-bar return, bp per NAME-BAR)")
    print(f"     vs the floored universe's equal-weight return : {g_ew:+.2f} bp on {n_ew:,} name-bars")
    print(f"     vs the DV-DECILE-MATCHED equal-weight return  : {g_dv:+.2f} bp on {n_dv:,} name-bars  "
          f"({100 * g_dv / g_ew:.0f}% of the equal-weight figure)")
    if abs(g_dv) < 0.5:
        print("     *** THE DV-MATCHED DRIFT IS NEAR ZERO. On this diagnostic the top decile does not out-drift names of its "
              "own size, and the equal-weight figure is a size tilt. ***")

    print(f"\n  2. RANK-BAND PROFILE (bp per name-bar; price, half-spread, DV and beta are medians/means over the band)")
    print("     %-12s %10s %9s %9s %8s %9s %10s %7s" % ("band", "name-bars", "EW hedge", "DV hedge", "px", "PUB hs", "DV $m", "beta"))
    bands = {}
    for a, b in BANDS:
        with np.errstate(invalid="ignore"):
            m = elig & (pct > a) & (pct <= b)
        ge, ne = drift(m, X_cc)
        gd, nd = drift(m, X_dv)
        row = dict(lo=a, hi=b, name_bars=ne, ew_bp=ge, dv_bp=gd, dv_name_bars=nd,
                   median_price=float(np.nanmedian(np.where(m, RAWC, np.nan))),
                   median_half_spread_PUB=float(np.nanmedian(np.where(m, HALF, np.nan))),
                   median_dv=float(np.nanmedian(np.where(m, DV, np.nan))),
                   mean_beta=float(np.nanmean(np.where(m, beta, np.nan))))
        bands[f"({a:.0f},{b:.0f}]"] = row
        print("     %-12s %10s %+9.2f %+9.2f %8.2f %9.1f %10.1f %7.2f" % (
            f"({a:.0f},{b:.0f}]", f"{ne:,}", ge, gd, row["median_price"], row["median_half_spread_PUB"],
            row["median_dv"] / 1e6, row["mean_beta"]))

    # 3. two-factor decomposition
    with np.errstate(invalid="ignore"):
        okr = elig & np.isfinite(r1T)
        mtop = top & np.isfinite(r1T)
    cnt_top = mtop.sum(axis=1)
    ew_top = np.where(cnt_top > 0, np.where(mtop, r1T, 0.0).sum(axis=1) / np.maximum(cnt_top, 1), np.nan)
    leg = {}
    for lbl, d in (("hi", 9), ("lo", 0)):
        m = okr & (dec == d)
        c = m.sum(axis=1)
        leg[lbl] = np.where(c > 0, np.where(m, r1T, 0.0).sum(axis=1) / np.maximum(c, 1), np.nan)
    smb = leg["hi"] - leg["lo"]
    good = np.isfinite(ew_top) & np.isfinite(m_f) & np.isfinite(smb) & (cnt_top >= 5)
    y = (ew_top - m_f)[good]
    Xr = np.column_stack([np.ones(good.sum()), m_f[good], smb[good]])
    b, se, se_nw = ols(y, Xr)
    a_bp, a_se, a_se_nw = b[0] * 1e4, se[0] * 1e4, se_nw[0] * 1e4
    print(f"\n  3. TWO-FACTOR DECOMPOSITION of the top decile's equal-weight EXCESS return (y = EW(pct > 90) - m_f), "
          f"{int(good.sum()):,} bars")
    print(f"     intercept {a_bp:+.3f} bp/bar   PLAIN OLS se {a_se:.3f} (t {a_bp / a_se:+.2f})   Newey-West(5) se {a_se_nw:.3f} "
          f"(t {a_bp / a_se_nw:+.2f})   -- the PLAIN OLS t is the one the predictions read")
    print(f"     market  loading {b[1]:+.4f} (se {se[1]:.4f}); size (top DV decile EW - bottom DV decile EW) loading "
          f"{b[2]:+.4f} (se {se[2]:.4f})")
    out = dict(study=STUDY, stage="stage0", note="D365 Stage 0 -- the top decile's drift against the equal-weight floored "
               "market and against a DV-decile-matched hedge, the rank-band profile of both, and a two-factor decomposition. "
               "OHLCV only; the holdout fixture is not read.",
               score=SCORE, top_decile=dict(ew_hedge_bp=g_ew, ew_name_bars=n_ew, dv_matched_bp=g_dv, dv_name_bars=n_dv,
                                            dv_share_of_ew=g_dv / g_ew if g_ew else None),
               bands=bands,
               two_factor=dict(bars=int(good.sum()), intercept_bp=a_bp, se_ols_bp=a_se, t_ols=a_bp / a_se,
                               se_nw5_bp=a_se_nw, t_nw5=a_bp / a_se_nw, beta_market=float(b[1]), se_market=float(se[1]),
                               beta_size=float(b[2]), se_size=float(se[2]),
                               definition="y = EW return of eligible pct>90 names minus m_f; regressors m_f and "
                                          "EW(top DV decile) - EW(bottom DV decile) over the same eligible universe"),
               sz=dict(sampled=300, worst=sz_worst, empty_pool_name_bars=sz_empty, defined_name_bars=sz_defined),
               holdout_guard=guard_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["stage0"].write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {paths['stage0']}  ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return out


# ================================================================== the nulls
def rank_rotate(pct, elig, shift, n_base=None):
    """ROT. D348 shifts the rank ASSIGNMENT inside its 25-name gate (`eff = (rk + shift) % N_BASE`). The gate here is the whole
    eligible day, so shift s moves each name k = round(s * L / 25) places up that day's ranking and hands it the score it finds
    there. The day's multiset of percentiles is preserved EXACTLY, so the number of names above any threshold is preserved."""
    n_base = N_BASE if n_base is None else n_base
    out = np.array(pct, dtype=float)
    T = pct.shape[0]
    for t in range(T):
        with np.errstate(invalid="ignore"):
            m = np.flatnonzero(np.asarray(elig[t], bool) & np.isfinite(pct[t]))
        L = m.size
        if L < 2:
            continue
        order = m[np.argsort(pct[t, m], kind="stable")]
        k = int(round(shift * L / n_base)) % L
        if k == 0:
            continue
        out[t, order] = np.roll(pct[t, order], -k)
    return out


def assert_ROT(pct, rot, elig, hi):
    """[ROT] the rotation keeps the per-bar multiset of scores exactly, keeps the count above the entry threshold exactly, and
    is not the identity."""
    T = pct.shape[0]
    n_diff = 0
    for t in range(0, T, 7):
        with np.errstate(invalid="ignore"):
            m = np.asarray(elig[t], bool) & np.isfinite(pct[t])
        if m.sum() < 2:
            continue
        a, b = np.sort(pct[t, m]), np.sort(rot[t, m])
        assert np.array_equal(a, b), f"[ROT] bar {t}: the multiset of scores changed"
        assert int((pct[t, m] > hi).sum()) == int((rot[t, m] > hi).sum()), f"[ROT] bar {t}: the count above {hi} changed"
        n_diff += int((pct[t, m] != rot[t, m]).any())
    assert n_diff > 0, "[ROT] the rotation is the identity on every sampled bar"
    return n_diff


def aprime_draw(pct, elig, rng):
    """A' (D351): the per-name circular rotation of the SCORE within that name's ELIGIBLE bars -- EB.rotate_signals, the
    committed implementation, with a zero signal so that only the score rotates."""
    z = np.zeros(pct.shape, bool)
    _sl, _ss, sc = EB.rotate_signals(z, z, pct, np.asarray(elig, bool), rng)
    return sc


def assert_APRIME(pct, sc, elig):
    """[A'] every rotated value stays inside the name's eligible bars (nothing outside elig moves) and each name's count of
    defined scores on eligible bars is kept."""
    e = np.asarray(elig, bool)
    assert np.array_equal(np.where(e, 0.0, np.nan_to_num(sc, nan=-1e18)),
                          np.where(e, 0.0, np.nan_to_num(pct, nan=-1e18))), "[A'] a value outside the eligible bars moved"
    a = (np.isfinite(pct) & e).sum(axis=0)
    b = (np.isfinite(sc) & e).sum(axis=0)
    assert np.array_equal(a, b), "[A'] a name's count of defined scores on eligible bars changed"
    return int(a.sum())


def null_stats(P, pct_used, elig, hi, lo, X_cc, X_oc):
    """Per draw: hedged net PUB bp/bar, gross bp/bar, net Sharpe, turnover, mean members (pre-reg section 3)."""
    hold = hold_grid(pct_used, elig, hi, lo, P["m_start"])
    if not hold.any():
        return dict(gross_bp=np.nan, gross_bar_bp=np.nan, net_bp_PUB=np.nan, net_bp_PB=np.nan, sharpe_net_PUB=np.nan,
                    turnover=np.nan, mean_members=0.0, entries=0, bars=0)
    ent = entries_of(hold)
    ret = ret_of(X_cc, X_oc, ent, "open")
    b = cell_block(P, hold, ret, "open", want_trades=False)
    return dict(gross_bp=b["gross_bp"], gross_bar_bp=b["gross_bar_bp"], net_bp_PUB=b["PUB"]["net_bp"],
                net_bp_PB=b["PB"]["net_bp"], sharpe_net_PUB=b["PUB"]["sharpe_net"], turnover=b["turnover"],
                mean_members=b["mean_members"], entries=b["entries"], bars=b["bars"])


NULL_KEYS = ("gross_bp", "gross_bar_bp", "net_bp_PUB", "net_bp_PB", "sharpe_net_PUB", "turnover", "mean_members")


def dist_of(x, obs):
    x = np.asarray([v for v in x if v is not None and np.isfinite(v)], float)
    if not x.size:
        return dict(p50=None, p95=None, max=None, min=None, draws=0, above=None, p=None)
    return dict(p50=float(np.median(x)), p95=float(np.quantile(x, .95)), max=float(x.max()), min=float(x.min()),
                draws=int(x.size), above=bool(obs > np.quantile(x, .95)) if obs is not None and np.isfinite(obs) else None,
                p=float(((x >= obs).sum() + 1) / (x.size + 1)) if obs is not None and np.isfinite(obs) else None)


def stage_cell(P, hi, lo, draws, part, paths):
    """The four nulls on one cell: ROT (24 deterministic shifts), A' (--draws), SIZE (1 deterministic run), C (1,000)."""
    t0 = time.time()
    ci = cell_index(hi, lo)
    elig = np.asarray(P["elig"], bool)
    pct = V58.pct_of(P, SCORE)
    X_cc, X_oc = returns_grids(P)
    hold = hold_grid(pct, elig, hi, lo, P["m_start"])
    ent = entries_of(hold)
    ret = ret_of(X_cc, X_oc, ent, "open")
    blk = cell_block(P, hold, ret, "open")
    obs = dict(gross_bp=blk["gross_bp"], gross_bar_bp=blk["gross_bar_bp"], net_bp_PUB=blk["PUB"]["net_bp"],
               net_bp_PB=blk["PB"]["net_bp"], sharpe_net_PUB=blk["PUB"]["sharpe_net"], turnover=blk["turnover"],
               mean_members=blk["mean_members"], entries=blk["entries"], bars=blk["bars"], trades=blk["trades"])
    print(f"\n  {cell_name(hi, lo)} part {part}: {obs['trades']:,} trades, {obs['entries']:,} entries, members "
          f"{obs['mean_members']:.1f}, turnover {100 * obs['turnover']:.2f}%; open fill gross {obs['gross_bp']:+.2f} "
          f"net PUB {obs['net_bp_PUB']:+.2f} bp/bar (Sharpe {obs['sharpe_net_PUB']:+.3f})")

    # ---- ROT: 24 deterministic shifts (no seed: the offsets are the shifts themselves)
    ts = time.time()
    ROT = []
    for s in ROT_SHIFTS:
        rot = rank_rotate(pct, elig, s)
        if s == ROT_SHIFTS[0]:
            assert_ROT(pct, rot, elig, hi)
        ROT.append(dict(shift=s, **null_stats(P, rot, elig, hi, lo, X_cc, X_oc)))
        del rot
    t_rot = time.time() - ts
    print(f"    ROT: {len(ROT)} shifts ({t_rot:.0f}s, {t_rot / len(ROT):.1f} s/shift) net PUB p50 "
          f"{np.median([r['net_bp_PUB'] for r in ROT]):+.2f} p95 {np.quantile([r['net_bp_PUB'] for r in ROT], .95):+.2f}", flush=True)

    # ---- SIZE: one deterministic run of the identical construction on dollar_vol. A RIVAL HYPOTHESIS, not a random control.
    ts = time.time()
    pct_sz = V58.pct_of(P, SIZE_SCORE)
    hold_sz = hold_grid(pct_sz, elig, hi, lo, P["m_start"])
    assert not np.array_equal(hold_sz, hold), "[SIZE] the size book is the same book as the momentum book"
    frac = float((hold_sz & hold).sum()) / max(float(hold.sum()), 1.0)
    SIZE = dict(**null_stats(P, pct_sz, elig, hi, lo, X_cc, X_oc), overlap_share_of_momentum_bars=frac,
                note="a rival hypothesis, not a random control")
    print(f"    SIZE ({SIZE_SCORE}, as pre-registered, {time.time() - ts:.0f}s): members {SIZE['mean_members']:.1f}, turnover "
          f"{100 * SIZE['turnover']:.2f}%, gross {SIZE['gross_bp']:+.2f}, net PUB {SIZE['net_bp_PUB']:+.2f}; "
          f"{100 * frac:.1f}% of the momentum book's position-bars are also held by the size book")
    del pct_sz, hold_sz
    # the size LEVEL control beside it -- see dv_level_pct's docstring for why the pre-registered score is not a size level
    ts = time.time()
    pct_dvl = dv_level_pct(P)
    hold_dvl = hold_grid(pct_dvl, elig, hi, lo, P["m_start"])
    frac_l = float((hold_dvl & hold).sum()) / max(float(hold.sum()), 1.0)
    SIZE_LEVEL = dict(**null_stats(P, pct_dvl, elig, hi, lo, X_cc, X_oc), overlap_share_of_momentum_bars=frac_l,
                      note="NOT pre-registered: the dollar-volume LEVEL (P['DV']) ranked by the identical construction, "
                           "because the pre-registered `dollar_vol` score is a relative-volume surprise, not a size level")
    print(f"    SIZE-LEVEL (P['DV'], NOT pre-registered, {time.time() - ts:.0f}s): members {SIZE_LEVEL['mean_members']:.1f}, "
          f"turnover {100 * SIZE_LEVEL['turnover']:.2f}%, gross {SIZE_LEVEL['gross_bp']:+.2f}, net PUB "
          f"{SIZE_LEVEL['net_bp_PUB']:+.2f}; {100 * frac_l:.1f}% overlap with the momentum book's position-bars")
    del pct_dvl, hold_dvl

    # ---- A': --draws per-name time rotations within elig
    ts = time.time()
    rngA = np.random.default_rng([SEED, STUDY, ci, ARM["APRIME"], part])
    A = []
    kept = None
    for d in range(draws):
        sc = aprime_draw(pct, elig, rngA)
        if d == 0:
            kept = assert_APRIME(pct, sc, elig)
        A.append(null_stats(P, sc, elig, hi, lo, X_cc, X_oc))
        del sc
        if (d + 1) % 10 == 0 or d + 1 == draws:
            print(f"    A': {d + 1}/{draws} ({time.time() - ts:.0f}s, {(time.time() - ts) / (d + 1):.1f} s/draw)", flush=True)
    t_ap = (time.time() - ts) / max(draws, 1)

    # ---- C: 1,000 random directions on the per-bar contribution ledger
    ts = time.time()
    series_bp = blk["_book"][blk["_mask"]] * 1e4
    C = V58.control_C(series_bp, np.random.default_rng([SEED, STUDY, ci, ARM["C"], part]), draws=C_DRAWS)
    z = C["mean"] / C["se"]
    # Section 7 asks [C] to assert BOTH that the null's mean is within 3 SE of zero AND that the observed lies outside it.
    # The first is a property of the CODE (a symmetric direction null must be centred) and is asserted. The SECOND is a
    # property of the DATA -- it is exactly Q1's evidence -- so it is RECORDED and printed loudly rather than raised: an
    # assert there would make a negative result unobtainable instead of reportable. A STATED WEAKENING of section 7.
    assert abs(z) < 3.0, f"[C] the direction null's mean is {z:+.2f} SE from zero"
    print(f"    C: {C_DRAWS} directions on {series_bp.size:,} bars ({time.time() - ts:.0f}s): mean {C['mean']:+.4f} bp "
          f"(se {C['se']:.4f}, z {z:+.2f}), p95 {C['p95']:+.2f} vs observed {float(series_bp.mean()):+.2f} -- observed "
          f"{'ABOVE' if C['above'] else '*** NOT ABOVE ***'} p95")

    out = dict(study=STUDY, cell=cell_name(hi, lo), hi=hi, lo=lo, cell_index=ci, part=part, draws=draws,
               seeds=dict(APRIME=[SEED, STUDY, ci, ARM["APRIME"], part], C=[SEED, STUDY, ci, ARM["C"], part],
                          ROT="deterministic: the 24 shifts themselves", SIZE="deterministic: one run"),
               observed=obs, ROT=ROT, SIZE=SIZE, SIZE_LEVEL=SIZE_LEVEL, control_A_prime={k: [x[k] for x in A] for k in NULL_KEYS},
               control_C=C, aprime_eligible_defined_scores=kept,
               seconds=dict(rot_per_shift=t_rot / len(ROT), aprime_per_draw=t_ap),
               holdout_guard=guard_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    f = Path(str(paths["ctrl"]).format(hi=hi, lo=lo, part=part))
    f.write_text(json.dumps(clean(out), indent=1))
    a = np.array([x["net_bp_PUB"] for x in A], float) if A else np.array([np.nan])
    print(f"  wrote {f.name}: net PUB observed {obs['net_bp_PUB']:+.2f}; ROT p95 "
          f"{np.quantile([r['net_bp_PUB'] for r in ROT], .95):+.2f}; A' p50 {np.nanmedian(a):+.2f} p95 "
          f"{np.nanquantile(a, .95):+.2f} ({draws} draws); SIZE {SIZE['net_bp_PUB']:+.2f}; C p95 {C['p95']:+.2f} "
          f"({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return out


# ================================================================== self-test
def stage_selftest(P):
    print("\nASSERTIONS")
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    SELFTEST_TMP.mkdir(parents=True, exist_ok=True)
    assert_HOLDOUT_GUARD()
    elig = np.asarray(P["elig"], bool)
    m_start = P["m_start"]
    pct = V58.pct_of(P, SCORE)
    X_cc, X_oc = returns_grids(P)
    with np.errstate(invalid="ignore"):
        ok_cc = np.isfinite(X_cc) & elig

    # [ID]
    lines, worst_id = assert_ID(P, pct, elig, X_cc, ok_cc)
    print(f"    [ID] the close-to-close variant reproduces the screen: " + "; ".join(lines)
          + f" -- every printed target matched exactly, and the runner's own cell_block equals the screen's arithmetic to "
            f"{worst_id:.1e} ({el()})")

    # [BUF]
    rng = np.random.default_rng([SEED, STUDY, 1])
    buf_lines, names = assert_BUF(pct, elig, m_start, rng)
    print(f"    [BUF] the hold state from a plain Python loop (scalars, one name at a time) equals the vectorised "
          f"construction on every bar and name: " + "; ".join(buf_lines) + f" ({el()})")

    # [LAG]
    n_same, n_moved, n_full = assert_LAG(P, pct, elig, m_start, np.random.default_rng([SEED, STUDY, 2]))
    print(f"    [LAG] a SECOND derivation of the held set -- cumulative maxima over stay/enter, no sequential state, never "
          f"calls the selection loop -- agrees on every bar and name of all {len(GRID) + 1} cells; on {n_same} sampled "
          f"(bar, name) probes, moving the RAW score at own-bar t left percentile rows t-2..t untouched and moved row t+1 on "
          f"{n_moved} of them; and on {n_full} whole-grid probe the held set was unchanged at every bar <= t and the "
          f"perturbed name entered the book at t+1 ({el()})")

    # [FILL]
    hi, lo = PRIMARY
    hold = hold_grid(pct, elig, hi, lo, m_start)
    n_ent, n_diff = assert_FILL(P, hold, X_cc, X_oc)
    ent = entries_of(hold)
    ret = ret_of(X_cc, X_oc, ent, "open")
    print(f"    [FILL] the entry bar earns ocT - m_f_oc and every later bar r1T - m_f; the open-fill and close-to-close books "
          f"differ on {n_diff:,} of {n_ent:,} defined entry bars and on NO other name-bar ({el()})")

    # [TURN]
    blk = cell_block(P, hold, ret, "open")
    n_keys, worst_t, g = assert_TURN(P, hold, ret, blk)
    print(f"    [TURN] turnover {100 * blk['turnover']:.3f}% == entries / mean members / bars ({blk['entries_in_mask']:,} / "
          f"{blk['mean_members']:.3f} / {blk['bars']:,}) and the trade ledger independently counts {blk['trades']:,} entries "
          f"and {blk['position_bars']:,} position-bars, membership matching the hold grid on every bar; {n_keys} statistics "
          f"equal G22.costed's to {worst_t:.1e}, and G22's four-crossing cost ({g['cost_bp']:.3f} bp/bar) is exactly twice "
          f"this ONE-LEG book's ({blk['PUB']['entry_median']['cost_bp']:.3f}) ({el()})")

    # [SZ]
    dvpct, dec = dv_decile_grid(P)
    dvm, pool_n = dv_matched_hedge(P, dec, np.asarray(P["r1T"], float))
    sz_worst, sz_empty, sz_defined = assert_SZ(P, dec, dvm, pool_n, np.asarray(P["r1T"], float),
                                               np.random.default_rng([SEED, STUDY, 3]))
    print(f"    [SZ] the DV-decile-matched pool is same-day, same-decile, eligible and never contains the name itself (300 "
          f"pools rebuilt by direct selection to {sz_worst:.1e}); {sz_empty:,} of {sz_defined:,} eligible name-bars have no "
          f"pool and are counted ({el()})")

    # [S]
    t_, i_, n_held, delta = assert_S(P, pct, elig, m_start, hi, lo, np.random.default_rng([SEED, STUDY, 4]))
    print(f"    [S] SIGN IN MONEY: +50 bp on r1T[{t_}, {i_}] ({P['symbols'][i_]} {P['dates'][t_]}, a non-entry bar of a held "
          f"name) pays POSITIVELY and moves the book's bar by {delta:.6f} bp = 50 / {n_held} held names, and no other bar "
          f"({el()})")

    # [ROT]
    rot = rank_rotate(pct, elig, 1)
    n_diff_rot = assert_ROT(pct, rot, elig, hi)
    rs = null_stats(P, rot, elig, hi, lo, X_cc, X_oc)
    print(f"    [ROT] shift 1 of {len(ROT_SHIFTS)}: every sampled bar keeps its multiset of scores and its count above "
          f"{hi} exactly, and the assignment changed on {n_diff_rot} of the sampled bars; the rebuilt book has "
          f"{rs['mean_members']:.1f} members, turnover {100 * rs['turnover']:.2f}%, net PUB {rs['net_bp_PUB']:+.2f} ({el()})")
    del rot

    # [A']
    sc = aprime_draw(pct, elig, np.random.default_rng([SEED, STUDY, cell_index(hi, lo), ARM["APRIME"], 0]))
    kept = assert_APRIME(pct, sc, elig)
    as_ = null_stats(P, sc, elig, hi, lo, X_cc, X_oc)
    print(f"    [A'] one draw: {kept:,} defined scores on eligible bars, every name's count kept, nothing outside the "
          f"eligible bars moved; the rebuilt book has {as_['mean_members']:.1f} members, net PUB {as_['net_bp_PUB']:+.2f} ({el()})")

    # [SIZE]
    pct_sz = V58.pct_of(P, SIZE_SCORE)
    hold_sz = hold_grid(pct_sz, elig, hi, lo, m_start)
    assert not np.array_equal(hold_sz, hold), "[SIZE] the size book is the momentum book"
    szs = null_stats(P, pct_sz, elig, hi, lo, X_cc, X_oc)
    pct_dvl = dv_level_pct(P)
    assert not np.array_equal(hold_grid(pct_dvl, elig, hi, lo, m_start), hold), "[SIZE] the size-level book is the momentum book"
    szl = null_stats(P, pct_dvl, elig, hi, lo, X_cc, X_oc)
    print(f"    [SIZE] the identical construction on {SIZE_SCORE} (a RIVAL HYPOTHESIS, not a random control): "
          f"{szs['mean_members']:.1f} members, turnover {100 * szs['turnover']:.2f}%, gross {szs['gross_bp']:+.2f}, net PUB "
          f"{szs['net_bp_PUB']:+.2f} vs the momentum book's gross {blk['gross_bp']:+.2f}; and on the dollar-volume LEVEL "
          f"(NOT pre-registered, but `dollar_vol` is a relative-volume surprise rather than a size level): "
          f"{szl['mean_members']:.1f} members, turnover {100 * szl['turnover']:.2f}%, gross {szl['gross_bp']:+.2f}, net PUB "
          f"{szl['net_bp_PUB']:+.2f} ({el()})")
    del pct_dvl

    # [C]
    C = V58.control_C(blk["_book"][blk["_mask"]] * 1e4, np.random.default_rng([SEED, STUDY, cell_index(hi, lo), ARM["C"], 0]),
                      draws=C_DRAWS)
    z = C["mean"] / C["se"]
    assert abs(z) < 3.0, f"[C] mean {C['mean']:+.4f} is {z:+.2f} SE from zero"
    print(f"    [C] {C_DRAWS} random directions on the per-bar contribution ledger: mean {C['mean']:+.4f} bp is {z:+.2f} SE "
          f"from zero (pre-registered bound 3 SE, ASSERTED) and the observed "
          f"{float(blk['_book'][blk['_mask']].mean()) * 1e4:+.2f} is "
          f"{'above' if C['above'] else '*** NOT above ***'} p95 {C['p95']:+.2f} (RECORDED, not asserted -- that half is a "
          f"fact about the data, i.e. Q1's own evidence; stated weakening of section 7) ({el()})")

    # [6] every one of [BUF] [LAG] [FILL] [SZ] [S] raises on a deliberately broken input
    broke = []
    try:                                                    # [BUF]: hysteresis removed (lo := hi) must NOT match the buffer
        A = hold_grid(pct, elig, hi, lo, m_start)
        B = hold_loop(pct, elig, hi, hi, m_start, names=names)
        assert int((A[:, names] != B[:, names]).sum()) == 0, "[BUF] broken"
    except AssertionError as e:
        assert "[BUF]" in str(e)
        broke.append("BUF")
    try:                                                    # [LAG]: the UNLAGGED percentile grid must not reproduce the book
        raw = np.array(P["score"](SCORE), dtype=float)
        sc0 = UF.apply_floor_replace(np.where(np.asarray(P["excl"]), np.nan, raw), np.asarray(P["keep"]))
        sc0 = np.where(np.asarray(P["base"]), sc0, np.nan)
        pct_unlagged = V47.percentile_grid(np.ascontiguousarray(sc0.T))
        assert np.array_equal(hold_cummax(pct_unlagged, elig, hi, lo, m_start), hold), "[LAG] broken"
        del raw, sc0, pct_unlagged
    except AssertionError as e:
        assert "[LAG]" in str(e)
        broke.append("LAG")
    try:                                                    # [FILL]: the open return applied on EVERY bar, not just entries
        bad_cc = np.where(hold, X_oc, X_cc)
        assert_FILL(P, hold, bad_cc, X_oc)
    except AssertionError as e:
        assert "[FILL]" in str(e)
        broke.append("FILL")
    try:                                                    # [SZ]: a matched hedge that FAILS to exclude the name itself
        bad = np.full(dvm.shape, np.nan)
        r1 = np.asarray(P["r1T"], float)
        for t in range(0, dvm.shape[0], 1):
            d = dec[t]
            m = elig[t] & (d >= 0) & np.isfinite(r1[t])
            if not m.any():
                continue
            dd, vv = d[m], r1[t, m]
            s = np.bincount(dd, weights=vv, minlength=10)
            c = np.bincount(dd, minlength=10)
            bad[t, np.flatnonzero(m)] = s[dd] / np.maximum(c[dd], 1)      # the name ITSELF left in
        assert_SZ(P, dec, bad, pool_n, r1, np.random.default_rng([SEED, STUDY, 5]))
        del bad
    except AssertionError as e:
        assert "[SZ]" in str(e)
        broke.append("SZ")
    try:                                                    # [S]: an equal-weight SUM instead of the mean -- 50 bp no longer
        def _sum_book(hold_, ret_, elig_):                  #      lands as 50 / n_held
            with np.errstate(invalid="ignore"):
                hh = hold_ & np.isfinite(ret_) & np.asarray(elig_, bool)
            c = hh.sum(axis=1)
            s = np.where(hh, ret_, 0.0).sum(axis=1)
            return np.where(c > 0, s, np.nan), c > 0, hold_.sum(axis=1), c
        assert_S(P, pct, elig, m_start, hi, lo, np.random.default_rng([SEED, STUDY, 4]), book_fn=_sum_book)
    except AssertionError as e:
        assert "[S]" in str(e)
        broke.append("S")
    assert broke == ["BUF", "LAG", "FILL", "SZ", "S"], f"[6] raised on: {broke}"
    print("    [6] each of [BUF] (hysteresis removed: lo := hi), [LAG] (the UNLAGGED percentile grid), [FILL] (the open "
          "return applied on every held bar, not only entries), [SZ] (a matched hedge that leaves the name itself in its own "
          "pool) and [S] (an equal-weight SUM in place of the mean) RAISES on the deliberately broken input")

    (SELFTEST_TMP / "selftest_ok.json").write_text(json.dumps(clean(dict(
        study=STUDY, cell=cell_name(hi, lo), id_lines=lines, turnover=blk["turnover"], members=blk["mean_members"],
        gross_bp=blk["gross_bp"], net_bp_PUB=blk["PUB"]["net_bp"], guard=guard_line()))))
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


# ================================================================== report
def load_controls(paths, hi, lo, obs):
    fs = sorted(Path(paths["dir"]).glob(f"d365_ctrl_{hi}_{lo}_p*.json"))
    if not fs:
        return None
    A, ROT, SIZE, SIZE_LEVEL, C, parts = {k: [] for k in NULL_KEYS}, None, None, None, None, []
    for f in fs:
        c = json.loads(f.read_text())
        assert c["hi"] == hi and c["lo"] == lo, f"[P] {f.name}"
        for k in ("gross_bp", "net_bp_PUB", "turnover", "mean_members"):
            assert abs(c["observed"][k] - obs[k]) < 1e-9, \
                f"[P] {f.name}: stored observed {k} {c['observed'][k]} differs from the re-simulated {obs[k]}"
        for k in NULL_KEYS:
            A[k].extend(c["control_A_prime"][k])
        ROT, SIZE, SIZE_LEVEL, C = c["ROT"], c["SIZE"], c.get("SIZE_LEVEL"), c["control_C"]
        parts.append(dict(file=f.name, part=c["part"], draws=c["draws"], seconds=c.get("seconds")))
    return dict(parts=parts, draws=len(A["net_bp_PUB"]), A_prime={k: dist_of(A[k], obs[k]) for k in NULL_KEYS},
                A_prime_raw=A, ROT={k: dist_of([r[k] for r in ROT], obs[k]) for k in NULL_KEYS}, ROT_raw=ROT,
                SIZE=SIZE, SIZE_LEVEL=SIZE_LEVEL, C=C)


def stage_report(P, paths):
    t0 = time.time()
    elig = np.asarray(P["elig"], bool)
    m_start = P["m_start"]
    pct = V58.pct_of(P, SCORE)
    X_cc, X_oc = returns_grids(P)
    with np.errstate(invalid="ignore"):
        ok_cc = np.isfinite(X_cc) & elig
    print("\nASSERTIONS")
    assert_HOLDOUT_GUARD()
    lines, worst_id = assert_ID(P, pct, elig, X_cc, ok_cc)
    print(f"    [ID] " + "; ".join(lines) + f" -- matched the screen's printed targets exactly; cell_block == the screen's "
          f"arithmetic to {worst_id:.1e}")

    CELLS = GRID + [DAILY]
    R, HOLDS = {}, {}
    for hi, lo in CELLS:
        hold = hold_grid(pct, elig, hi, lo, m_start)
        HOLDS[(hi, lo)] = hold
        ent = entries_of(hold)
        cell = dict(hi=hi, lo=lo, cell=cell_name(hi, lo), in_grid=(hi, lo) in GRID)
        for fill in FILLS:
            ret = ret_of(X_cc, X_oc, ent, fill)
            blk = cell_block(P, hold, ret, fill)
            blk["splits"] = splits_block(P, blk, hold, ret)
            if fill == "open":
                pnl = np.array([t[3] for t in blk["_trades"]], float) * 1e4
                blk["four_groups"] = V50.four_groups(blk["_trades"], pnl, P, elig)
                blk["per_trade_stats"] = dict(
                    n=len(pnl), mean_bp=float(pnl.mean()), median_bp=float(np.median(pnl)),
                    win_rate=float((pnl > 0).mean()), hold_mean=float(np.mean([t[2] for t in blk["_trades"]])),
                    hold_median=float(np.median([t[2] for t in blk["_trades"]])),
                    t=float(pnl.mean() / (pnl.std(ddof=1) / np.sqrt(pnl.size))) if pnl.size > 1 else None,
                    mean_over_2c={cv: float(pnl.mean() / blk[cv]["per_trade"]["mean_two_c"]) for cv in CONVS})
                if (hi, lo) == PRIMARY:
                    n_keys, worst_t, _g = assert_TURN(P, hold, ret, blk)
                    print(f"    [TURN] {cell_name(hi, lo)}: {n_keys} statistics equal G22.costed's to {worst_t:.1e}; "
                          f"the ledger independently counts {blk['trades']:,} entries and {blk['position_bars']:,} position-bars")
                    n_ent, n_diff = assert_FILL(P, hold, X_cc, X_oc)
                    print(f"    [FILL] {n_diff:,} of {n_ent:,} defined entry bars differ between the fills and no other name-bar")
            cell[fill] = blk
        R[cell_name(hi, lo)] = cell

    # ---- the grid tables
    for fill in FILLS:
        lbl = "OPEN FILL (D340, the declared convention)" if fill == "open" else "CLOSE-TO-CLOSE (the screen's own basis)"
        print("\n" + "=" * 152)
        print(f"THE BUFFER GRID -- {lbl}.  gross = pooled mean over held NAME-BARS (the screen's statistic and the headline); "
              f"gross_bar = the per-bar book mean")
        print("=" * 152)
        print("  %-9s %7s %7s %8s %7s | %7s %8s %6s %8s %8s %7s %8s %7s %8s | %6s %7s" % (
            "cell", "mem/dep", "mem/all", "turn/bar", "hold", "gross", "gross_bar", "cost", "netPUB", "netPB", "vol",
            "Sh net", "%/yr", "maxdd", "trades", "netPUB/t"))
        for hi, lo in CELLS:
            c = R[cell_name(hi, lo)][fill]
            tag = cell_name(hi, lo) + ("*" if (hi, lo) == PRIMARY else ("d" if (hi, lo) == DAILY else " "))
            print("  %-9s %7.1f %7.1f %7.2f%% %7.1f | %+7.2f %+8.2f %6.2f %+8.2f %+8.2f %7.1f %+8.3f %+7.1f %8.0f | %6d %+7.2f" % (
                tag, c["mean_members"], c["mean_members_all_bars"], 100 * c["turnover"], c["hold_bars"] or 0,
                c["gross_bp"], c["gross_bar_bp"], c["PUB"]["cost_bp"], c["PUB"]["net_bp"], c["PB"]["net_bp"], c["vol_bp"],
                c["PUB"]["sharpe_net"] or 0, c["PUB"]["pct_per_year"], c["maxdd_bp"], c["trades"],
                c["PUB"]["per_trade"]["net_bp"]))
        print("  * = the primary cell (95/80); d = the daily-refresh cell (hi = lo = 90), NOT one of the eight. "
              "hold = 1 / turnover. cost and netPUB use the HELD-MEDIAN convention; netPUB/t the PER-TRADE one.")
        print("  mem/dep = mean members over DEPLOYED bars; mem/all = over every bar from m_start (the SCREEN's statistic, "
              "and the one the pre-registered '41 members' is in -- the momentum warm-up leaves the book empty for the first "
              "~900 bars).")

    print("\n  BOTH COST CONVENTIONS on every cell, OPEN FILL, PUB (held-median = the median half-spread and price over the "
          "held NAME-BARS; per-trade = each trade's own halves at its own entry and exit bars; entry-median = G22's, over the "
          "ledger's entry bars, halved to one leg)")
    print("  %-9s | %8s %7s %8s | %8s %8s %8s | %8s %8s" % ("cell", "held hs", "px", "cost", "pt hs(e/x)", "pt 2c", "cost",
                                                            "em hs", "cost"))
    for hi, lo in CELLS:
        c = R[cell_name(hi, lo)]["open"]["PUB"]
        pt, em = c["per_trade"], c["entry_median"]
        print("  %-9s | %8.1f %7.2f %8.3f | %8s %8.1f %8.3f | %8.1f %8.3f" % (
            cell_name(hi, lo), c["half_spread"], c["price"], c["cost_bp"],
            f"{pt['median_entry_half']:.0f}/{pt['median_exit_half']:.0f}", pt["mean_two_c"], pt["cost_bp"],
            em["half_spread"], em["cost_bp"]))

    # ---- the grid max and its null under shared offsets
    print("\n  THE GRID MAX and a GRID-MAX NULL under SHARED offsets (each ROT shift is applied to all 8 cells and the max "
          "over the grid recomputed on that shift; 24 shifts)")
    best = max(GRID, key=lambda c: R[cell_name(*c)]["open"]["PUB"]["net_bp"])
    obs_max = R[cell_name(*best)]["open"]["PUB"]["net_bp"]
    gm, ts = [], time.time()
    for s in ROT_SHIFTS:
        rot = rank_rotate(pct, elig, s)
        vals = [null_stats(P, rot, elig, hi, lo, X_cc, X_oc)["net_bp_PUB"] for hi, lo in GRID]
        gm.append(float(np.nanmax(vals)))
        del rot
    d_gm = dist_of(gm, obs_max)
    print(f"    observed grid max {cell_name(*best)} net PUB {obs_max:+.2f} bp/bar; the grid-max null over {len(gm)} shared "
          f"shifts: p50 {d_gm['p50']:+.2f} p95 {d_gm['p95']:+.2f} max {d_gm['max']:+.2f} -- observed "
          f"{'ABOVE' if d_gm['above'] else 'NOT above'} p95, p = {d_gm['p']:.3f}  ({time.time() - ts:.0f}s)")

    # ---- controls on the primary
    prim = R[cell_name(*PRIMARY)]["open"]
    obs = dict(gross_bp=prim["gross_bp"], gross_bar_bp=prim["gross_bar_bp"], net_bp_PUB=prim["PUB"]["net_bp"],
               net_bp_PB=prim["PB"]["net_bp"], sharpe_net_PUB=prim["PUB"]["sharpe_net"], turnover=prim["turnover"],
               mean_members=prim["mean_members"])
    K = load_controls(paths, *PRIMARY, obs)
    print(f"\n  CONTROLS on the primary cell {cell_name(*PRIMARY)} (open fill)")
    if K is None:
        print("    no control files on disk -- run --cell 95:80 first. Q1 and Q2 are FALSIFIED BY ABSENCE.")
    else:
        print("    %-26s %10s | %9s %9s %9s | %9s" % ("statistic", "observed", "ROT p50", "ROT p95", "A' p50", "A' p95"))
        for k in ("gross_bp", "net_bp_PUB", "sharpe_net_PUB", "turnover", "mean_members"):
            r, a = K["ROT"][k], K["A_prime"][k]
            print("    %-26s %10.4f | %9.4f %9.4f %9.4f | %9.4f" % (k, obs[k], r["p50"], r["p95"], a["p50"], a["p95"]))
        rt_turn, rt_mem = K["ROT"]["turnover"], K["ROT"]["mean_members"]
        print(f"    CAUTION on ROT: the rank rotation WRAPS (D348's `eff = (rk + shift) % N_BASE` does too), so a name that "
              f"climbs past the wrap point is EXITED. The rotated books therefore run {rt_turn['p50'] / obs['turnover']:.1f}x "
              f"the observed turnover at the median ({100 * rt_turn['p50']:.2f}% vs {100 * obs['turnover']:.2f}%) and "
              f"{rt_mem['p50'] / obs['mean_members']:.1f}x the members. Cost scales with turnover, so ROT's NET is penalised "
              f"by construction -- read its GROSS row first (CLAUDE.md: a control must share the treatment's nuisance; D291).")
        for lbl, key in (("SIZE (pre-registered: the `dollar_vol` score)", "SIZE"),
                         ("SIZE-LEVEL (NOT pre-registered: the dollar-volume LEVEL)", "SIZE_LEVEL")):
            sz = K.get(key)
            if sz is None:
                print(f"    {lbl}: not in the control file")
                continue
            print(f"    {lbl}, 1 deterministic run: members {sz['mean_members']:.1f}, turnover "
                  f"{100 * sz['turnover']:.2f}%, gross {sz['gross_bp']:+.2f}, net PUB {sz['net_bp_PUB']:+.2f}, Sharpe "
                  f"{fq(sz['sharpe_net_PUB'], 3)}; {100 * sz['overlap_share_of_momentum_bars']:.1f}% of the momentum book's "
                  f"position-bars are also held by it")
        print(f"    NOTE on SIZE's score: `dollar_vol` in this record's score cache is log(dollar volume today) minus the "
              f"median of log dollar volume over the trailing window (ragged_features.volume_scores) -- a relative-volume "
              f"SURPRISE, not a size LEVEL. Q2 is scored on the pre-registered control; SIZE-LEVEL is the one that answers "
              f"'is this a size book', and both are reported.")
        print(f"    C (1,000 random directions on the per-bar contribution ledger): mean {K['C']['mean']:+.4f} bp "
              f"(se {K['C']['se']:.4f}), p95 {K['C']['p95']:+.2f}, observed above p95: {K['C']['above']}")
        print(f"    draws: ROT {len(K['ROT_raw'])} shifts, A' {K['draws']}, C 1,000; parts "
              + ", ".join(p["file"] for p in K["parts"]))

    # ---- four groups, splits
    g4 = prim["four_groups"]
    tt = g4["top_trade"]
    ps = prim["per_trade_stats"]
    print(f"\n  FOUR GROUPS on the primary cell ({cell_name(*PRIMARY)}, open fill), per TRADE in bp per trade (never compared "
          f"to the per-bar numbers)")
    print(f"    n {g4['count']:,} mean {g4['mean_bp']:+.1f} median {g4['median_bp']:+.1f} win {100 * g4['win_rate']:.1f}% "
          f"payoff {round(g4['payoff'], 2) if g4['payoff'] else '-'} hold {g4['hold_mean']:.1f} bars skew {g4['skew']:+.2f} "
          f"kurt {g4['kurtosis_excess']:+.1f}; t {ps['t']:+.2f}; mean / 2c PUB {ps['mean_over_2c']['PUB']:.2f}x")
    print(f"    trims (k={g4['trim_k']}): ex-top {g4['mean_ex_top_bp']:+.1f} ex-bottom {g4['mean_ex_bottom_bp']:+.1f} "
          f"trimmed {g4['mean_trimmed_bp']:+.1f}")
    print(f"    names to half the P&L {g4['names_to_half_pnl']} of {g4['n_names']}; top-1/5/10 name share "
          + "/".join(("%.0f%%" % (100 * v)) if v is not None else "-" for v in g4["top_name_share"].values())
          + f"; profitable years {100 * g4['profitable_years_share']:.0f}% of {g4['years']}")
    print(f"    TOP TRADE {tt['symbol']} entered {tt['entry_date']} at ${tt['as_traded_price']:.2f} (DV pct "
          f"{round(tt['dv_percentile_at_entry'], 1) if tt['dv_percentile_at_entry'] is not None else '-'}), held "
          f"{tt['hold']} bars, {tt['pnl_bp']:+.0f} bp = "
          f"{('%.1f%%' % (100 * tt['share_of_pnl'])) if tt['share_of_pnl'] is not None else '-'} of P&L")
    sd_, sp_ = g4["split_dead_alive"], g4["split_price"]
    print(f"    splits: dead {sd_['dead_n']} {fq(sd_['dead_mean_bp'], 1)} / alive {sd_['alive_n']} {fq(sd_['alive_mean_bp'], 1)}; "
          f"price <= ${sp_['median_price']:.2f} {sp_['low_n']} {fq(sp_['low_mean_bp'], 1)} / above {sp_['high_n']} "
          f"{fq(sp_['high_mean_bp'], 1)}; open at end {prim['open_at_end']}")

    print(f"\n  SPLITS of the primary cell (open fill): net PUB bp/bar [held name-bars]; down-years {P['down_years']}")
    for fill in FILLS:
        s = R[cell_name(*PRIMARY)][fill]["splits"]
        f_ = lambda d: f"{fq(d.get('net_bp_PUB'))}[{d['name_bars']:,}]"
        print(f"    {fill:5s} era1 {f_(s['era1'])} era2 {f_(s['era2'])} down {f_(s['down_years'])}; "
              f"full years {s['n_full_years']}, positive on gross {s['full_years_positive_gross']}, on net PUB "
              f"{s['full_years_positive_net_PUB']}")
        print("          by year: " + " ".join(f"{y}:{fq(v.get('gross_bp'))}/{fq(v.get('net_bp_PUB'))}"
                                               for y, v in sorted(s["by_year"].items())))

    # ---- Stage 0
    S0 = None
    if paths["stage0"].exists():
        S0 = json.loads(paths["stage0"].read_text())
        td = S0["top_decile"]
        print(f"\n  STAGE 0 (from {paths['stage0'].name})")
        print(f"    top-decile drift: EW hedge {td['ew_hedge_bp']:+.2f} bp/name-bar ({td['ew_name_bars']:,}); DV-matched "
              f"{td['dv_matched_bp']:+.2f} ({100 * td['dv_share_of_ew']:.0f}% of it)")
        print("    %-12s %10s %9s %9s %8s %9s %10s %7s" % ("band", "name-bars", "EW hedge", "DV hedge", "px", "PUB hs", "DV $m", "beta"))
        for k, v in S0["bands"].items():
            print("    %-12s %10s %+9.2f %+9.2f %8.2f %9.1f %10.1f %7.2f" % (
                k, f"{v['name_bars']:,}", v["ew_bp"], v["dv_bp"], v["median_price"], v["median_half_spread_PUB"],
                v["median_dv"] / 1e6, v["mean_beta"]))
        tf = S0["two_factor"]
        print(f"    two-factor intercept {tf['intercept_bp']:+.3f} bp/bar, OLS se {tf['se_ols_bp']:.3f} (t {tf['t_ols']:+.2f}), "
              f"NW(5) t {tf['t_nw5']:+.2f}; market {tf['beta_market']:+.3f}, size {tf['beta_size']:+.3f}")
    else:
        print(f"\n  STAGE 0 not on disk ({paths['stage0'].name}) -- Q3 is FALSIFIED BY ABSENCE. Run --stage0 first.")

    # ---- the DV-matched book on the primary cell (Q3's book reading)
    dvpct, dec = dv_decile_grid(P)
    dvm, _pn = dv_matched_hedge(P, dec, np.asarray(P["r1T"], float))
    dvm_oc, _pn2 = dv_matched_hedge(P, dec, np.asarray(P["ocT"], float))
    holdP = HOLDS[PRIMARY]
    entP = entries_of(holdP)
    ret_dv = np.where(entP, np.asarray(P["ocT"], float) - dvm_oc, np.asarray(P["r1T"], float) - dvm)
    blk_dv = cell_block(P, holdP, ret_dv, "open")
    blk_dv["splits"] = splits_block(P, blk_dv, holdP, ret_dv)
    print(f"\n  THE PRIMARY CELL UNDER THE DV-DECILE-MATCHED HEDGE (open fill; the same hold grid, a different benchmark)")
    print(f"    EW hedge : gross {prim['gross_bp']:+.2f} cost {prim['PUB']['cost_bp']:.2f} net PUB {prim['PUB']['net_bp']:+.2f} "
          f"Sharpe {prim['PUB']['sharpe_net']:+.3f} vol {prim['vol_bp']:.1f}")
    print(f"    DV-matched: gross {blk_dv['gross_bp']:+.2f} cost {blk_dv['PUB']['cost_bp']:.2f} net PUB "
          f"{blk_dv['PUB']['net_bp']:+.2f} Sharpe {blk_dv['PUB']['sharpe_net']:+.3f} vol {blk_dv['vol_bp']:.1f} "
          f"({100 * blk_dv['PUB']['net_bp'] / prim['PUB']['net_bp']:.0f}% of the EW-hedged net)")

    # ================= predictions =================
    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    q, qn = {}, {}
    daily = R[cell_name(*DAILY)]["open"]
    prim_cc = R[cell_name(*PRIMARY)]["cc"]

    # Q1
    if K is None:
        q["Q1"] = False
        qn["Q1"] = "the control files are not on disk; falsified by absence"
    else:
        above = all(K[n]["net_bp_PUB"]["above"] for n in ("ROT", "A_prime")) and bool(K["C"]["above"])
        q["Q1"] = bool(prim["PUB"]["net_bp"] > 0 and above)
        qn["Q1"] = (f"net PUB {prim['PUB']['net_bp']:+.2f} bp/bar (gross {prim['gross_bp']:+.2f}, cost "
                    f"{prim['PUB']['cost_bp']:.2f}); ROT p95 {K['ROT']['net_bp_PUB']['p95']:+.2f} (p50 "
                    f"{K['ROT']['net_bp_PUB']['p50']:+.2f}), A' p95 {K['A_prime']['net_bp_PUB']['p95']:+.2f} (p50 "
                    f"{K['A_prime']['net_bp_PUB']['p50']:+.2f}, {K['draws']} draws), C p95 {K['C']['p95']:+.2f} on the "
                    f"per-bar ledger")
    # Q2
    if K is None:
        q["Q2"] = False
        qn["Q2"] = "the SIZE control is in the control file, which is not on disk; falsified by absence"
    else:
        szg = K["SIZE"]["gross_bp"]
        q["Q2"] = bool(szg < 0.5 * prim["gross_bp"])
        szl = K.get("SIZE_LEVEL")
        qn["Q2"] = (f"SIZE gross {szg:+.2f} vs half the primary's gross {0.5 * prim['gross_bp']:+.2f} "
                    f"({100 * szg / prim['gross_bp']:.0f}% of {prim['gross_bp']:+.2f}); the pre-registered `dollar_vol` "
                    f"score is a relative-volume surprise, not a size level, so the SIZE-LEVEL control (the dollar-volume "
                    f"LEVEL) is reported beside it at gross "
                    + (f"{szl['gross_bp']:+.2f} ({100 * szl['gross_bp'] / prim['gross_bp']:.0f}%)" if szl else "-- not run"))
    # Q3
    if S0 is None:
        q["Q3"] = False
        qn["Q3"] = "Stage 0 is not on disk; falsified by absence"
    else:
        tf = S0["two_factor"]
        keep_net = blk_dv["PUB"]["net_bp"] >= 0.5 * prim["PUB"]["net_bp"]
        keep_drift = S0["top_decile"]["dv_matched_bp"] >= 0.5 * S0["top_decile"]["ew_hedge_bp"]
        q["Q3"] = bool(keep_net and tf["intercept_bp"] > 0 and tf["t_ols"] > 2.0)
        qn["Q3"] = (f"the primary cell's net PUB under the DV-matched hedge {blk_dv['PUB']['net_bp']:+.2f} vs half the "
                    f"EW-hedged net {0.5 * prim['PUB']['net_bp']:+.2f} ({'kept' if keep_net else 'NOT kept'}); Stage 0's "
                    f"top-decile drift {S0['top_decile']['dv_matched_bp']:+.2f} vs half of {S0['top_decile']['ew_hedge_bp']:+.2f} "
                    f"({'kept' if keep_drift else 'NOT kept'}); intercept {tf['intercept_bp']:+.3f} bp/bar, OLS t {tf['t_ols']:+.2f} "
                    f"(NW(5) t {tf['t_nw5']:+.2f})")
    # Q4
    e1 = R[cell_name(*PRIMARY)]["open"]["splits"]["era1"]
    q["Q4"] = bool(e1.get("net_bp_PUB", -np.inf) > 0)
    qn["Q4"] = (f"era 1 net PUB {fq(e1.get('net_bp_PUB'))} bp/bar on {e1['name_bars']:,} held name-bars "
                f"(era 2 {fq(R[cell_name(*PRIMARY)]['open']['splits']['era2'].get('net_bp_PUB'))})")
    # Q5 (against)
    gap = prim["PUB"]["net_bp"] - daily["PUB"]["net_bp"]
    q["Q5"] = bool(gap > 2.0)
    qn["Q5"] = (f"primary net PUB {prim['PUB']['net_bp']:+.2f} vs the daily-refresh cell's {daily['PUB']['net_bp']:+.2f} "
                f"-- a gap of {gap:+.2f} bp/bar against the 2.00 bar (open fill)")
    # Q6
    share = (prim_cc["gross_bp"] - prim["gross_bp"]) / prim_cc["gross_bp"] if prim_cc["gross_bp"] else np.nan
    q["Q6"] = bool(share < 0.20)
    qn["Q6"] = (f"close-to-close gross {prim_cc['gross_bp']:+.2f} -> open-fill gross {prim['gross_bp']:+.2f}: the fill costs "
                f"{prim_cc['gross_bp'] - prim['gross_bp']:+.2f} bp/bar = {100 * share:.1f}% of the close-to-close gross")
    # Q7
    sp = R[cell_name(*PRIMARY)]["open"]["splits"]
    q["Q7"] = bool(sp["full_years_positive_gross"] >= 10 and sp["n_full_years"] >= 13)
    qn["Q7"] = (f"{sp['full_years_positive_gross']} of {sp['n_full_years']} full years positive on gross "
                f"(a full year = >= {YEAR_MIN_BARS} held name-bars, the screen's own rule): {sp['full_years']}")
    # Q8
    q["Q8"] = bool(g4["names_to_half_pnl"] is not None and g4["names_to_half_pnl"] >= 20)
    qn["Q8"] = f"{g4['names_to_half_pnl']} names to half the P&L of {g4['n_names']} that traded"

    print("\nPREDICTIONS (primary cell 95/80, OPEN FILL, hedged net PUB bp/bar unless stated)")
    print(f"  Q1 (LOAD-BEARING) net PUB > 0 and above the p95 of ROT, A' and C: {v_(q['Q1'])} -- {qn['Q1']}")
    print(f"  Q2 the SIZE control earns less than half the primary's gross: {v_(q['Q2'])} -- {qn['Q2']}")
    print(f"  Q3 the DV-matched hedge keeps at least half the net, and the two-factor intercept is positive with t > 2: "
          f"{v_(q['Q3'])} -- {qn['Q3']}")
    print(f"  Q4 era 1's net PUB > 0: {v_(q['Q4'])} -- {qn['Q4']}")
    print(f"  Q5 (AGAINST) the primary beats the daily-refresh cell by more than 2 bp/bar net: {v_(q['Q5'])} -- {qn['Q5']}")
    print(f"  Q6 the open fill costs less than 20% of the close-to-close gross: {v_(q['Q6'])} -- {qn['Q6']}")
    print(f"  Q7 at least 10 of 13 full years positive on gross: {v_(q['Q7'])} -- {qn['Q7']}")
    print(f"  Q8 at least 20 names to half the P&L: {v_(q['Q8'])} -- {qn['Q8']}")
    print(f"  check: the close-to-close variant reproduces the screen ([ID], to {worst_id:.1e} against the screen's own "
          f"arithmetic and exactly against every printed target): " + "; ".join(lines))

    for c in R.values():
        for fill in FILLS:
            for k in ("_book", "_mask", "_members", "_trades"):
                c[fill].pop(k, None)
    for k in ("_book", "_mask", "_members", "_trades"):
        blk_dv.pop(k, None)
    out = dict(note="D365: the momentum buffer book -- a broad, slow, hysteretic long on mom_252_21, hedged by the floored "
                    "universe's equal-weight return, no slot cap. Eight declared cells plus the daily-refresh cell, both "
                    "fills, both cost conventions, four nulls on the primary cell. WITHIN-SAMPLE confirmation: the primary "
                    "cell came from an eleven-combination screen on this same fixture. Nothing is a book; nothing promoted.",
               study=STUDY, score=SCORE, size_score=SIZE_SCORE, grid=[cell_name(*c) for c in GRID],
               primary=cell_name(*PRIMARY), daily_refresh=cell_name(*DAILY), fills=list(FILLS),
               m_start=P["m_start"], down_years=P["down_years"], floored_market_by_year=P["yr_ret"],
               cost=dict(round_trip="one leg: 2 x half-spread + 2 x $0.005 / price x 1e4 (== V47.two_c; == G22.costed / 2, "
                                    "which prices the two-legged spread book)",
                         turnover="entries / mean members / bars (G22.costed's definition)",
                         conventions=["held-median (over held NAME-BARS, the screen's and D285's)",
                                      "per-trade (D363's: own halves at own entry and exit bars)",
                                      "entry-median (G22's own held median, over the ledger's entry bars)"]),
               seeds=dict(APRIME=[SEED, STUDY, "cell_index", ARM["APRIME"], "part"],
                          C=[SEED, STUDY, "cell_index", ARM["C"], "part"], ROT="deterministic", SIZE="deterministic"),
               results=R, primary_dv_matched_hedge=blk_dv, grid_max=dict(cell=cell_name(*best), observed=obs_max, null=d_gm,
                                                                         per_shift=gm),
               controls=K, stage0=S0, predictions=q, prediction_notes=qn, id_worst=worst_id, id_lines=lines,
               holdout_guard=guard_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {paths['report']}  ({time.time() - t0:.0f}s)  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--stage0", action="store_true")
    ap.add_argument("--cell", metavar="HI:LO", help="e.g. 95:80 -- the four nulls on one cell")
    ap.add_argument("--draws", type=int, default=APRIME_DRAWS, help="A' draws (pre-reg 200)")
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--out-dir", default=str(DATA), help="where the stage files go (default data/; smoke runs pass temp/...)")
    a = ap.parse_args()
    paths = out_paths(a.out_dir)
    print("D365  the momentum buffer book -- a broad, slow, hysteretic long, and whether its edge is momentum or size")
    P = PREP.prep(need_grids=False)
    if a.selftest:
        stage_selftest(P)
    elif a.stage0:
        stage0(P, paths)
    elif a.cell:
        hi, lo = (int(v) for v in a.cell.split(":"))
        assert (hi, lo) in GRID or (hi, lo) == DAILY, f"cell must be one of {[cell_name(*c) for c in GRID + [DAILY]]}"
        stage_cell(P, hi, lo, a.draws, a.part, paths)
    elif a.report:
        stage_report(P, paths)
    else:
        ap.error("one of --selftest, --stage0, --cell HI:LO, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
