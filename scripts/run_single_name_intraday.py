"""D264 -- the intraday short on single names, stratified by volatility.

    uv run python scripts/run_single_name_intraday.py
    uv run python scripts/run_single_name_intraday.py --report-only

A CROSS-SCREEN UNDER R12 of D247's construction onto a different universe.
Every constant is frozen at the value D247 and D256 already ran. Nothing here
is fitted, swept or re-cut. The pre-registration is
`docs/decisions/D264-the-intraday-short-on-single-names.md`, committed BEFORE
this ran.

WHY IT IS WORTH RUNNING, and the number is D247's
--------------------------------------------------
D247 measured the only encouraging thing the short side of this programme has
produced: the intraday-only S1 short holds bars returning -4.27%/yr against the
continuous version's +4.72% -- an 8.99-point swing, and "the first construction
in this programme to isolate bars that actually fall." It lost anyway, on
ARITHMETIC: turnover 334/yr, breakeven 0.13 bp/side, charged ~1.6 bp/side. The
cost was TWELVE TIMES the gross edge.

A single name has more idiosyncratic variance (FINDINGS 2), which should raise
the edge, and a wider spread, which raises the cost. THE QUESTION IS WHICH RISES
FASTER. The eight names span a 5.5x volatility range precisely so the screen can
say which end binds.

WHAT IS REUSED AND WHAT IS WRITTEN FRESH -- D212 is binding
------------------------------------------------------------
REUSED, unchanged: `macd`, `pivots`, `signals`/`walk` (S2), `base_masks`/
`hold_book` (S1), `load_panel`, `per_side_bps`'s IBKR schedule,
`effective_instruments`, D247's `session_structure`, `flatten_overnight` and
`breakeven_bps`.

WRITTEN FRESH, and only these three:
  * `cost_vector`   -- per-SYMBOL cost. The commission stays derived from the
                       IBKR schedule; only the HALF-SPREAD is per-stratum. Pinned
                       against `L.per_side_bps` for exact equality at the ETF
                       spread, so the reuse is proved rather than asserted.
  * `excess_vec`    -- D247's financing with a per-SYMBOL borrow rate. Pinned
                       against `D.excess_intraday` for exact equality when the
                       borrow vector is constant.
  * `rotation_all`  -- one SHARED offset draw across ALL 16 cells in ALL THREE
                       strata (D228). Sharing across strata is the point: the
                       strata are subsets of the same eight symbols, so drawing
                       independently per stratum would make the cells
                       artificially independent and inflate the best-of floor.

Offline, deterministic, seed 0.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


D = _load("d247_intraday_shorts", "run_intraday_shorts.py")
BW = _load("d245_book_wide", "run_book_wide.py")
U, X, L, S, J, M = D.U, D.X, D.L, D.S, D.J, D.M
pivots = D.pivots

SUMMARY = REPO / "data" / "single_name_intraday_summary.json"
RESULTS = REPO / "SINGLE_NAME_INTRADAY_RESULTS.md"
FIX = REPO / "data" / "fixtures"
FIXTURE = FIX / "single_name_intraday_15m_panel.csv.gz"
EVENTS = FIX / "single_name_intraday_15m_panel_events.json"

SEED, N_SIMS = X.SEED, X.N_SIMS
RF_ANNUAL = X.RF_ANNUAL
N_BOOT, BLOCK = J.N_BOOT, J.BLOCK

# --------------------------------------------------------------------------
# THE SAMPLE AND THE COST SCHEDULE -- fixed in D264, before this ran
# --------------------------------------------------------------------------
LOW_VOL = ("PG", "LMT", "PM", "MO")
HIGH_VOL = ("CLF", "SM", "YELP", "RH")
STRATUM = {**{s: "low" for s in LOW_VOL}, **{s: "high" for s in HIGH_VOL}}

HALF_SPREAD_BPS = {"low": 1.5, "high": 4.5}     # ETF reference: 1.0
BORROW_ANNUAL = {"low": 0.0030, "high": 0.0300}  # ETF reference: 0.010

# D247's OWN per-position notional, not a total-capital figure. Commission in bps
# depends on notional PER POSITION, so holding that constant is what makes this
# study's cost comparable to D247's rather than merely similar.
NOTIONAL_PER_SYMBOL = L.PRIMARY_CAPITAL / 57.0

STRATA = {"ALL": LOW_VOL + HIGH_VOL, "LOW": LOW_VOL, "HIGH": HIGH_VOL}
SHORT_CELLS = ("S1_short_cont", "S1_short_intra", "S2_short_cont", "S2_short_intra")
LONG_CELLS = ("S1_long_cont", "S1_long_intra", "S2_long_cont", "S2_long_intra")
# 12 short cells (4 x 3 strata) + 4 long controls (ALL only) = 16. D264's count.
SCORED = [("ALL", c) for c in SHORT_CELLS + LONG_CELLS] + \
         [(st, c) for st in ("LOW", "HIGH") for c in SHORT_CELLS]


# --------------------------------------------------------------------------
# WRITTEN FRESH 1 -- per-symbol cost, commission still derived
# --------------------------------------------------------------------------


def cost_vector(symbols, closes) -> np.ndarray:
    """Per-side cost as a fraction of notional, ONE PER SYMBOL.

    The IBKR schedule is reused exactly as `L.per_side_bps` applies it; the only
    per-stratum quantity is the half-spread. The assert below is the proof of
    reuse: at the ETF half-spread this function IS `L.per_side_bps`."""
    out = np.empty(len(symbols))
    for i, sym in enumerate(symbols):
        med = float(np.median(closes[i]))
        shares = NOTIONAL_PER_SYMBOL / med
        comm = min(L.IBKR_PER_SHARE * shares, L.IBKR_MAX_PCT * NOTIONAL_PER_SYMBOL)
        comm = max(comm, L.IBKR_MIN_PER_ORDER)
        bps = 1e4 * comm / NOTIONAL_PER_SYMBOL + HALF_SPREAD_BPS[STRATUM[sym]]
        ref = L.per_side_bps(med, NOTIONAL_PER_SYMBOL)
        assert abs((bps - HALF_SPREAD_BPS[STRATUM[sym]]) - (ref - L.HALF_SPREAD_BPS)) < 1e-9, \
            f"{sym}: the commission leg diverged from the committed per_side_bps"
        out[i] = bps / 1e4
    return out


def borrow_vector(symbols) -> np.ndarray:
    return np.array([BORROW_ANNUAL[STRATUM[s]] for s in symbols])


# --------------------------------------------------------------------------
# WRITTEN FRESH 2 -- D247's financing with a per-symbol borrow rate
# --------------------------------------------------------------------------


def excess_vec(total, pos, start, first, gap, ppy, borrow_v):
    """rf on the LONG fraction per bar; borrow ONLY where a short is carried
    across a session boundary, prorated by the real calendar gap -- D247's model,
    with the single scalar borrow rate replaced by a per-symbol vector."""
    live = pos[:, start:]
    long_f = np.maximum(live, 0.0).mean(axis=0)
    ex = total - long_f * (math.log1p(RF_ANNUAL) / ppy)
    fb, gd = first[start:], gap[start:]
    short_i = np.maximum(-live, 0.0)
    borrow = (short_i * np.log1p(borrow_v)[:, None]).mean(axis=0) * gd / 365.0
    borrow[~fb] = 0.0
    return ex - borrow, float(borrow.sum())


def _sharpe(ex, ppy):
    sd = float(np.std(ex, ddof=1))
    return (float(np.mean(ex)) / sd * math.sqrt(ppy)) if sd > 0 else 0.0


def score(panel, pos, start, first, gap, ppy, borrow_v):
    total = X.signed_log_returns(panel, pos, total_return=True)[start:]
    ex, borrow = excess_vec(total, pos, start, first, gap, ppy, borrow_v)
    live = pos[:, start:]
    turn = float(np.abs(np.diff(pos, axis=1, prepend=0.0))[:, start:].sum())
    active = (pos != 0.0).astype(float)
    ents = np.sum(np.diff(active, axis=1, prepend=0.0)[:, start:] > 0.0, axis=1)
    yrs = len(total) / ppy
    exposure = float(np.maximum(-live, 0.0).mean() + np.maximum(live, 0.0).mean())
    cagr = float(np.expm1(np.sum(total) / yrs))
    return {
        "excess_sharpe": _sharpe(ex, ppy),
        "cagr": cagr,
        "exposure": exposure,
        # FINDINGS 1a: never the edge alone.
        "exposure_x_edge": exposure * (cagr / exposure) if exposure > 0 else 0.0,
        "total_return": L.total_return_of(total),
        "vol": float(np.std(total, ddof=1) * math.sqrt(ppy)),
        "max_drawdown": L.max_drawdown_of(total),
        "exposure_long": float(np.maximum(live, 0.0).mean()),
        "exposure_short": float(np.maximum(-live, 0.0).mean()),
        "turnover_per_year": turn / len(panel.symbols) / yrs,
        "borrow_paid_annualised": float(np.expm1(borrow / yrs)),
        "entries": int(ents.sum()),
        "min_entries_per_symbol": int(ents.min()),
        "clears_E": bool(ents.sum() >= 100 and ents.min() >= 30),
        "clears_V": bool(cagr > 0.0),
    }


def breakeven_bps(panel, pos, start, first, gap, ppy, borrow_v):
    """The per-side cost at which the arm's excess return reaches zero.

    THE PRIMARY COST STATISTIC, because it is a property of the strategy and not
    of the half-spread I assumed. A reader who disagrees with 1.5 and 4.5 bp can
    substitute their own and re-read the verdict without re-running anything."""
    turn = float(np.abs(np.diff(pos, axis=1, prepend=0.0))[:, start:].sum()) / len(panel.symbols)
    if turn <= 0:
        return None
    total = X.signed_log_returns(panel, pos, total_return=True)[start:]
    ex, _ = excess_vec(total, pos, start, first, gap, ppy, borrow_v)
    paid = float((panel.cost_fraction[:, None]
                  * np.abs(np.diff(pos, axis=1, prepend=0.0)))[:, start:].sum()
                 / len(panel.symbols))
    gross = float(np.sum(ex)) + paid
    return 1e4 * (1.0 - math.exp(-gross / turn))


# --------------------------------------------------------------------------
# Books
# --------------------------------------------------------------------------


def build_books(panel, cleaned, start, first):
    """S1 and S2, short and long, continuous and intraday-only. Exactly D247."""
    md, hs, ok = S.base_masks(panel, cleaned, start)

    n, T = panel.closes.shape
    g_lo = np.full((n, T), np.nan)
    g_hi = np.full((n, T), np.nan)
    i_lo = np.full((n, T), np.nan)
    atr = np.full((n, T), np.nan)
    for i, sym in enumerate(panel.symbols):
        ps = pivots(cleaned[sym], U.K)
        li = np.array([p.index for p in ps if p.sign < 0], dtype=int)
        hj = np.array([p.index for p in ps if p.sign > 0], dtype=int)
        g_lo[i], i_lo[i] = U.rolling_fit(
            T, li, np.log([p.price for p in ps if p.sign < 0]) if len(li) else np.array([]), U.K)
        g_hi[i], _ = U.rolling_fit(
            T, hj, np.log([p.price for p in ps if p.sign > 0]) if len(hj) else np.array([]), U.K)
        atr[i] = U.atr_log(cleaned[sym], U.ATR_WINDOW)
    sok = ~(np.isnan(g_lo) | np.isnan(g_hi) | np.isnan(atr))
    up = (g_lo > 0) & (g_hi > 0) & sok
    down = (g_lo < 0) & (g_hi < 0) & sok
    up[:, :start] = False
    down[:, :start] = False
    up_ref, _, _, _ = U.signals(panel, cleaned, start)
    assert np.array_equal(up, up_ref), "reconstructed UPTREND differs from U.signals"

    s1_long = S.hold_book((hs > 0) & (md <= 0) & ok, start)
    s1_short = -S.hold_book((hs < 0) & (md >= 0) & ok, start)
    s2_long, _, _ = U.walk(panel, up, g_lo, i_lo, atr, start)
    s2_short = -U.walk(panel, down, g_lo, i_lo, atr, start)[0]

    books = {
        "S1_short_cont": s1_short, "S1_short_intra": D.flatten_overnight(s1_short, first),
        "S2_short_cont": s2_short, "S2_short_intra": D.flatten_overnight(s2_short, first),
        "S1_long_cont": s1_long, "S1_long_intra": D.flatten_overnight(s1_long, first),
        "S2_long_cont": s2_long, "S2_long_intra": D.flatten_overnight(s2_long, first),
    }
    for k in books:
        if k.endswith("_intra"):
            assert not books[k][:, first].any(), f"{k} is not flat at every session open"
    return books


def load_full():
    """The eight-name panel, loaded ONCE.

    `load_panel` refuses a panel whose symbols have different bar counts, so this
    reads the PANEL fixture (`build_intraday_panel.py --single-names`), not the
    raw one -- the same thing D247 did, for the same reason."""
    saved = (L.FIXTURE, L.EVENTS)
    try:
        L.FIXTURE, L.EVENTS = FIXTURE, EVENTS
        return L.load_panel()
    finally:
        L.FIXTURE, L.EVENTS = saved


def subset(panel, cleaned, symbols):
    """A stratum panel, carved from the eight-name one.

    THE TIME GRID IS THE EIGHT-SYMBOL INTERSECTION FOR EVERY STRATUM, deliberately.
    A LOW-only panel built from scratch would keep a few bars the eight-name
    intersection drops, and the two strata would then be scored on different grids
    -- which is exactly the comparison this study is built to make. A handful of
    bars is the right price for LOW and HIGH being measured on the same clock."""
    keep = [i for i, s in enumerate(panel.symbols) if s in symbols]
    syms = tuple(panel.symbols[i] for i in keep)
    assert set(syms) == set(symbols), f"missing symbols: {set(symbols) - set(syms)}"
    sub = type(panel)(
        symbols=syms, closes=panel.closes[keep], log_returns=panel.log_returns[keep],
        cost_fraction=cost_vector(syms, panel.closes[keep]), dates=panel.dates,
        total_log_returns=panel.total_log_returns[keep],
    )
    return sub, {s: cleaned[s] for s in syms}


# --------------------------------------------------------------------------
# WRITTEN FRESH 3 -- one shared offset draw across all 16 cells, all 3 strata
# --------------------------------------------------------------------------


def rotation_all(ctx, ppy, start, first, gap):
    """Matched-count rotation. ONE offset per (sim, symbol), shared by every cell
    in every stratum (D228).

    The strata are SUBSETS OF THE SAME EIGHT SYMBOLS. Drawing independently per
    stratum would make the cells artificially independent and inflate the
    best-of-16 floor -- exactly the failure D228 exists to prevent. So the draw
    is over all eight, and each stratum indexes into it."""
    rng = np.random.default_rng(SEED)
    all_syms = list(STRATA["ALL"])
    span = ctx["ALL"]["panel"].closes.shape[1] - start
    per = {key: np.empty(N_SIMS) for key in SCORED}
    best = np.empty(N_SIMS)

    fast = {}
    for st, c in ctx.items():
        p = c["panel"]
        exp_rets = np.expm1(p.total_log_returns)
        cost = p.cost_fraction[:, None]

        def _mk(exp_rets=exp_rets, cost=cost):
            def _f(pos):
                charge = cost * np.abs(np.diff(pos, axis=1, prepend=0.0))
                return (np.log1p(pos * exp_rets) + np.log1p(-charge)).mean(axis=0)[start:]
            return _f
        fast[st] = _mk()
        probe = c["books"]["S1_short_cont"]
        assert np.allclose(fast[st](probe),
                           X.signed_log_returns(p, probe, total_return=True)[start:],
                           rtol=0, atol=1e-12), f"{st}: fast scorer diverged from the committed one"

    scratch = {st: np.zeros_like(c["panel"].closes) for st, c in ctx.items()}
    idx_of = {st: [all_syms.index(s) for s in ctx[st]["panel"].symbols] for st in ctx}

    for s in range(N_SIMS):
        off8 = rng.integers(1, span, size=len(all_syms))
        vals = []
        for st, c in ctx.items():
            rot = scratch[st]
            off = off8[idx_of[st]]
            for k in [cc for (sst, cc) in SCORED if sst == st]:
                src = c["books"][k][:, start:]
                for i in range(len(off)):
                    rot[i, start:] = np.roll(src[i], int(off[i]))
                ex, _ = excess_vec(fast[st](rot), rot, start, first, gap, ppy, c["borrow"])
                v = _sharpe(ex, ppy)
                per[(st, k)][s] = v
                vals.append(v)
        best[s] = max(vals)
    return per, best


# --------------------------------------------------------------------------


def build() -> dict:
    t0 = time.time()
    raw_panel, raw_cleaned = load_full()
    panel_all, cleaned_all = subset(raw_panel, raw_cleaned, STRATA["ALL"])
    first, gap = D.session_structure(panel_all.dates)
    n_sessions = int(first.sum())
    T = panel_all.closes.shape[1]
    ppy = (T / n_sessions) * 252.0
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

    # PIN: the fresh financing must equal D247's when borrow is constant.
    probe_pos = np.zeros_like(panel_all.closes)
    probe_pos[:, start:] = -1.0
    probe_tot = X.signed_log_returns(panel_all, probe_pos, total_return=True)[start:]
    a, _ = excess_vec(probe_tot, probe_pos, start, first, gap, ppy,
                      np.full(len(panel_all.symbols), D.BORROW_ANNUAL))
    b, _ = D.excess_intraday(probe_tot, probe_pos, start, first, gap, ppy)
    assert np.allclose(a, b, rtol=0, atol=1e-15), "excess_vec diverged from D247's excess_intraday"

    ctx = {}
    for st, syms in STRATA.items():
        p, cl = ((panel_all, cleaned_all) if st == "ALL"
                 else subset(raw_panel, raw_cleaned, syms))
        ctx[st] = {"panel": p, "cleaned": cl, "borrow": borrow_vector(p.symbols),
                   "books": build_books(p, cl, start, first)}

    # ---------------- Part A: the anatomy, BEFORE any cell is read ----------
    anatomy = {}
    for st, c in ctx.items():
        p = c["panel"]
        rets = p.total_log_returns[:, start:]
        overnight = rets[:, first[start:]]
        intraday = rets[:, ~first[start:]]
        n_sess_live = int(first[start:].sum())
        ones = np.ones_like(p.closes)
        ones[:, :start] = 0.0
        short_all = -ones
        sa = score(p, short_all, start, first, gap, ppy, c["borrow"])
        sig2 = float(np.var(rets.mean(axis=0), ddof=1)) * ppy
        mu = float(rets.mean(axis=0).sum() / (rets.shape[1] / ppy))
        anatomy[st] = {
            "symbols": list(p.symbols),
            "n_symbols": len(p.symbols),
            # D247 measured +8.59% overnight vs -0.36% intraday on the 57 ETFs.
            # The whole case for a flat-at-close short rests on that split.
            "overnight_drift_annualised": float(np.expm1(overnight.mean(axis=0).sum()
                                                         / (rets.shape[1] / ppy))),
            "intraday_drift_annualised": float(np.expm1(intraday.mean(axis=0).sum()
                                                        / (rets.shape[1] / ppy))),
            "buy_and_hold": score(p, ones, start, first, gap, ppy, c["borrow"]),
            "SHORT_ALL": sa,
            "sigma_squared": sig2,
            "mu_geometric": mu,
            # FINDINGS 1b: a short pays -mu - sigma^2. D253 landed within 2.85 pts.
            "predicted_short_all_cagr": float(np.expm1(-math.log1p(mu) - sig2)),
            "effective_instruments": BW.effective_instruments(rets),
            "mean_pairwise_rho": float(np.nan_to_num(np.corrcoef(rets), nan=0.0)[
                np.triu_indices(len(p.symbols), 1)].mean()) if len(p.symbols) > 1 else 1.0,
            "live_sessions": n_sess_live,
            "cost_bps_per_side": {s: float(p.cost_fraction[i] * 1e4)
                                  for i, s in enumerate(p.symbols)},
        }

    # what the held bars actually return -- D244's lesson, per cell
    conditional = {}
    for st, c in ctx.items():
        rets = c["panel"].total_log_returns[:, start:]
        for k in c["books"]:
            held = c["books"][k][:, start:] != 0.0
            v = rets[held]
            conditional[f"{st}:{k}"] = {
                "bars": int(v.size),
                "annualised": float(np.expm1(v.mean() * ppy)) if v.size else None}
        conditional[f"{st}:ALL BARS"] = {"bars": int(rets.size),
                                         "annualised": float(np.expm1(rets.mean() * ppy))}

    # R10 concurrency, actual against a per-symbol-rotated book
    rng_c = np.random.default_rng(SEED)
    concurrency = {}
    for st, k in SCORED:
        pos = ctx[st]["books"][k][:, start:]
        n = pos.shape[0]
        held = (pos != 0.0)
        rot = np.zeros_like(held)
        for i in range(n):
            rot[i] = np.roll(held[i], int(rng_c.integers(1, pos.shape[1])))
        concurrency[f"{st}:{k}"] = {
            "mean_held": float(held.sum(axis=0).mean()),
            "max_held": int(held.sum(axis=0).max()),
            "share_of_universe_mean": float(held.sum(axis=0).mean() / n),
            "rotated_max_held": int(rot.sum(axis=0).max()),
            "sd_ratio": (float(held.sum(axis=0).std() / rot.sum(axis=0).std())
                         if rot.sum(axis=0).std() > 0 else None)}

    # ---------------- Part B: the 16 cells ---------------------------------
    cells, be = {}, {}
    for st, k in SCORED:
        c = ctx[st]
        cells[f"{st}:{k}"] = score(c["panel"], c["books"][k], start, first, gap, ppy, c["borrow"])
        be[f"{st}:{k}"] = breakeven_bps(c["panel"], c["books"][k], start, first, gap, ppy, c["borrow"])
    for st, k in SCORED:
        if k.endswith("_intra"):
            assert cells[f"{st}:{k}"]["borrow_paid_annualised"] == 0.0, \
                f"{st}:{k} paid overnight borrow"

    per, best = rotation_all(ctx, ppy, start, first, gap)
    best_p95 = float(np.percentile(best, 95))
    nulls = {}
    for key in SCORED:
        st, k = key
        a = cells[f"{st}:{k}"]["excess_sharpe"]
        nulls[f"{st}:{k}"] = {
            "p50": float(np.percentile(per[key], 50)),
            "p95": float(np.percentile(per[key], 95)),
            "percentile_of_actual": float((per[key] < a).mean() * 100.0),
            "clears_H_sharpe": bool(a > float(np.percentile(per[key], 95)))}

    # hurdle H's money leg -- R10's second corollary requires BOTH
    rngm = np.random.default_rng(SEED + 1)
    for st, k in SCORED:
        c = ctx[st]
        p, pos = c["panel"], c["books"][k]
        n, TT = p.closes.shape
        span = TT - start
        money = np.empty(N_SIMS)
        rot = np.zeros_like(p.closes)
        src = pos[:, start:]
        for s in range(N_SIMS):
            off = rngm.integers(1, span, size=n)
            for i in range(n):
                rot[i, start:] = np.roll(src[i], int(off[i]))
            tot = X.signed_log_returns(p, rot, total_return=True)[start:]
            money[s] = float(np.sum(tot))
        actual = float(np.sum(X.signed_log_returns(p, pos, total_return=True)[start:]))
        nulls[f"{st}:{k}"]["money_percentile"] = float((money < actual).mean() * 100.0)
        nulls[f"{st}:{k}"]["clears_H_money"] = bool(actual > float(np.percentile(money, 95)))
        nulls[f"{st}:{k}"]["clears_H"] = bool(nulls[f"{st}:{k}"]["clears_H_sharpe"]
                                              and nulls[f"{st}:{k}"]["clears_H_money"])

    # hurdle B -- the bootstrap. R6/D230: never optional.
    rb = np.random.default_rng(SEED)
    nlen = T - start
    nblk = math.ceil(nlen / BLOCK)
    idxs = [(rb.integers(0, nlen - BLOCK + 1, size=nblk)[:, None]
             + np.arange(BLOCK)[None, :]).ravel()[:nlen] for _ in range(N_BOOT)]
    boot = {}
    for st, k in SCORED:
        c = ctx[st]
        tot = X.signed_log_returns(c["panel"], c["books"][k], total_return=True)[start:]
        ex, _ = excess_vec(tot, c["books"][k], start, first, gap, ppy, c["borrow"])
        d = np.array([_sharpe(ex[i], ppy) for i in idxs])
        boot[f"{st}:{k}"] = {"p05": float(np.percentile(d, 5)),
                             "p95": float(np.percentile(d, 95)),
                             "clears_B": bool(np.percentile(d, 5) > 0.0)}

    verdict = {}
    for st, k in SCORED:
        key = f"{st}:{k}"
        charged = float(np.mean(ctx[st]["panel"].cost_fraction) * 1e4)
        v = {
            "clears_H": nulls[key]["clears_H"],
            "clears_V": cells[key]["clears_V"],
            "clears_E": cells[key]["clears_E"],
            "clears_K": bool(be[key] is not None and be[key] >= charged),
            "clears_B": boot[key]["clears_B"],
            "clears_F": bool(cells[key]["excess_sharpe"] > best_p95),
            "charged_bps": charged,
            "headroom_x": (be[key] / charged) if (be[key] is not None and charged > 0) else None,
        }
        v["clears_all"] = all(v[x] for x in ("clears_H", "clears_V", "clears_E",
                                             "clears_K", "clears_B", "clears_F"))
        verdict[key] = v

    shorts = [f"{st}:{k}" for st, k in SCORED if "_short_" in k]
    survivors = [k for k in shorts if verdict[k]["clears_all"]]
    return {
        "produced": "D264",
        "stage": "SCREEN -- a cross-screen under R12, not a verdict",
        "preregistration": "docs/decisions/D264-the-intraday-short-on-single-names.md",
        "seed": SEED, "n_sims": N_SIMS, "n_boot": N_BOOT, "ppy": ppy,
        "half_spread_bps": HALF_SPREAD_BPS, "borrow_annual": BORROW_ANNUAL,
        "notional_per_symbol": NOTIONAL_PER_SYMBOL,
        "strata": {k: list(v) for k, v in STRATA.items()},
        "bars": T, "sessions": n_sessions, "bars_per_session": T / n_sessions,
        "warmup_bars": start, "live_bars": T - start, "live_years": (T - start) / ppy,
        "first_bar": panel_all.dates[0], "last_bar": panel_all.dates[-1],
        "anatomy": anatomy, "conditional_returns": conditional, "concurrency": concurrency,
        "cells": cells, "breakeven_bps": be, "nulls": nulls, "bootstrap": boot,
        "best_of_p95": best_p95, "verdict": verdict, "survivors": survivors,
        "n_cells_scored": len(SCORED),
        "SURVIVORSHIP": ("SURVIVOR-ONLY. TIME_SERIES_INTRADAY serves no delisted "
                         "ticker; 41.6% of the 2013-2017 cohort is unreachable. "
                         "D264 declares the direction IN ADVANCE: the bias is "
                         "CONSERVATIVE for a short, so a PASS is informative and a "
                         "FAIL IS AMBIGUOUS and does not close the question."),
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    o = []
    A = o.append
    A("# D264 — the intraday short on single names\n")
    A(f"**A SCREEN, NOT A VERDICT.** Cross-screen under R12 of "
      f"[D247](docs/decisions/D247-the-short-side-at-fifteen-minutes.md)'s construction "
      f"onto eight single names. Pre-registered in "
      f"[`{p['preregistration']}`]({p['preregistration']}) **before this ran**.\n")
    A(f"*seed {p['seed']}, {p['n_sims']:,} rotations, {p['elapsed_seconds']}s. "
      f"{len(p['strata']['ALL'])} names x {p['bars']:,} bars over {p['sessions']:,} sessions "
      f"({p['bars_per_session']:.2f}/session, PPY {p['ppy']:.0f}); warm-up {p['warmup_bars']:,} "
      f"bars, live {p['live_years']:.2f} years. {p['first_bar']} .. {p['last_bar']}.*\n")
    A(f"> **{p['SURVIVORSHIP']}**\n")
    A(f"**Strata.** LOW `{' '.join(p['strata']['LOW'])}` · "
      f"HIGH `{' '.join(p['strata']['HIGH'])}`. Half-spread "
      f"{p['half_spread_bps']['low']}/{p['half_spread_bps']['high']} bp, borrow "
      f"{p['borrow_annual']['low']:.2%}/{p['borrow_annual']['high']:.2%}, "
      f"notional ${p['notional_per_symbol']:,.0f}/position (D247's own figure).\n")

    A("\n## Part A — the anatomy, reported before any cell was scored\n")
    A("### The drift decomposition — the measurement the whole construction rests on\n")
    A("*On the 57 ETFs D247 measured **+8.59%/yr overnight against −0.36% intraday**. "
      "A book flat at every close faces the second number instead of the first.*\n")
    A("| stratum | overnight/yr | intraday/yr | swing | B&H CAGR | vol |")
    A("|---|---:|---:|---:|---:|---:|")
    for st in ("ALL", "LOW", "HIGH"):
        a = p["anatomy"][st]
        A(f"| **{st}** | {a['overnight_drift_annualised']:+.2%} | "
          f"{a['intraday_drift_annualised']:+.2%} | "
          f"{(a['overnight_drift_annualised'] - a['intraday_drift_annualised']) * 100:+.2f} pts | "
          f"{a['buy_and_hold']['cagr']:+.2%} | {a['buy_and_hold']['vol']:.1%} |")

    A("\n### The variance tax, against its formula\n")
    A("*FINDINGS §1b: a daily-rebalanced short earns approximately `−mu − sigma^2`. "
      "D253 landed within 2.85 points on crypto. **A short book that does not clearly "
      "beat `SHORT_ALL` has found nothing.***\n")
    A("| stratum | sigma^2 | mu | predicted SHORT_ALL | **measured** | error |")
    A("|---|---:|---:|---:|---:|---:|")
    for st in ("ALL", "LOW", "HIGH"):
        a = p["anatomy"][st]
        m = a["SHORT_ALL"]["cagr"]
        A(f"| **{st}** | {a['sigma_squared']:.4f} | {a['mu_geometric']:+.2%} | "
          f"{a['predicted_short_all_cagr']:+.2%} | **{m:+.2%}** | "
          f"{(m - a['predicted_short_all_cagr']) * 100:+.2f} pts |")

    A("\n### Breadth — R10, and pooled counts are not sample sizes\n")
    A("| stratum | names | effective instruments | mean pairwise rho |")
    A("|---|---:|---:|---:|")
    for st in ("ALL", "LOW", "HIGH"):
        a = p["anatomy"][st]
        A(f"| **{st}** | {a['n_symbols']} | **{a['effective_instruments']:.2f}** | "
          f"{a['mean_pairwise_rho']:.3f} |")

    A("\n### What the held bars actually return\n")
    A("*D244's lesson: a null can be beaten or lost by drift structure alone, so this "
      "is measured before any null result is interpreted. D247's swing on ETFs was "
      "**8.99 points** between `cont` and `intra`.*\n")
    A("| stratum | cell | bars held | annualised return of those bars |")
    A("|---|---|---:|---:|")
    for st in ("ALL", "LOW", "HIGH"):
        A(f"| **{st}** | *all bars* | {p['conditional_returns'][f'{st}:ALL BARS']['bars']:,} | "
          f"*{p['conditional_returns'][f'{st}:ALL BARS']['annualised']:+.2%}* |")
        for k in SHORT_CELLS:
            c = p["conditional_returns"][f"{st}:{k}"]
            A(f"| | {k} | {c['bars']:,} | "
              + (f"**{c['annualised']:+.2%}** |" if c["annualised"] is not None else "— |"))

    A("\n## Part B — the 16 cells\n")
    A("| stratum | cell | exposure | CAGR | exp x edge | excess Sharpe | max DD | "
      "turnover/yr | borrow/yr | entries (min/sym) |")
    A("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for st, k in SCORED:
        c = p["cells"][f"{st}:{k}"]
        A(f"| {st} | **{k}** | {c['exposure']:.1%} | {c['cagr']:+.2%} | "
          f"{c['exposure_x_edge']:+.2%} | **{c['excess_sharpe']:+.3f}** | "
          f"{c['max_drawdown']:.2%} | {c['turnover_per_year']:.0f} | "
          f"{c['borrow_paid_annualised']:.2%} | {c['entries']:,} ({c['min_entries_per_symbol']}) |")

    A("\n### The cost wall — the breakeven is the result, the charged figure is my assumption\n")
    A("*D247's S1_short_intra: breakeven **0.13 bp/side** against ~1.6 charged — "
      "a **12x** shortfall. That is the number this study exists to move.*\n")
    A("| stratum | cell | turnover/yr | **breakeven bp/side** | charged | headroom | K |")
    A("|---|---|---:|---:|---:|---:|:--:|")
    for st, k in SCORED:
        key = f"{st}:{k}"
        v, b = p["verdict"][key], p["breakeven_bps"][key]
        A(f"| {st} | **{k}** | {p['cells'][key]['turnover_per_year']:.0f} | "
          + (f"**{b:.2f}**" if b is not None else "—")
          + f" | {v['charged_bps']:.2f} | "
          + (f"{v['headroom_x']:.2f}x" if v["headroom_x"] is not None else "—")
          + f" | {'YES' if v['clears_K'] else 'no'} |")

    A("\n### Hurdles — all six, every leg computed (R6)\n")
    A(f"*Best-of-{p['n_cells_scored']} floor (D228, one shared offset vector across "
      f"all strata): **{p['best_of_p95']:+.3f}**.*\n")
    A("| stratum | cell | H sharpe | H money | **H** | V | E | K | B | F | **ALL** |")
    A("|---|---|---:|---:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|")
    for st, k in SCORED:
        key = f"{st}:{k}"
        v, n = p["verdict"][key], p["nulls"][key]
        y = lambda x: "PASS" if x else "fail"  # noqa: E731
        A(f"| {st} | **{k}** | {n['percentile_of_actual']:.1f}th | "
          f"{n['money_percentile']:.1f}th | {y(v['clears_H'])} | {y(v['clears_V'])} | "
          f"{y(v['clears_E'])} | {y(v['clears_K'])} | {y(v['clears_B'])} | "
          f"{y(v['clears_F'])} | **{y(v['clears_all'])}** |")

    A("\n### R10 — concurrency, actual against a per-symbol-rotated book\n")
    A("| stratum | cell | mean held | max | share of universe | *rotated max* | sd ratio |")
    A("|---|---|---:|---:|---:|---:|---:|")
    for st, k in SCORED:
        c = p["concurrency"][f"{st}:{k}"]
        A(f"| {st} | {k} | {c['mean_held']:.2f} | {c['max_held']} | "
          f"{c['share_of_universe_mean']:.1%} | *{c['rotated_max_held']}* | "
          + (f"{c['sd_ratio']:.2f}x |" if c["sd_ratio"] is not None else "— |"))

    A("\n## Limitations carried into the reading, none of them discovered afterwards\n")
    A(f"1. **Survivorship.** {p['SURVIVORSHIP']}")
    A(f"2. **Breadth.** Effective independent instruments "
      f"**{p['anatomy']['ALL']['effective_instruments']:.2f}** of "
      f"{p['anatomy']['ALL']['n_symbols']}. R10's corollary is binding: the pooled entry "
      f"counts in Part B are **not** sample sizes, and are never quoted alone.")
    A(f"3. **The bootstrap block is {BLOCK} bars**, inherited from D247 unchanged so the two "
      f"studies stay comparable. At fifteen minutes that is **under one session**, so hurdle B "
      f"under-weights any autocorrelation living at the daily scale and is the weakest of the "
      f"six. Kept rather than re-chosen: picking a block length after seeing the data is the "
      f"defect R9's corollary warns about.")
    A("4. **The half-spread and borrow are assumptions** (1.5/4.5 bp, 0.30/3.00%). The "
      "commission is derived from the committed IBKR schedule. **Read hurdle K off the "
      "breakeven column, which is a property of the strategy**, not off my spread guess.")
    A("5. **Locate fees and SEC Rule 201 are not modelled**, and both run *against* the short "
      "— hardest on the HIGH stratum, where a falling small-cap is exactly what becomes "
      "expensive to borrow.")
    A("6. **The volatility axis is confounded with sector** — sorting a liquid pool on "
      "volatility produced defensive mega-caps at one end and cyclicals at the other. "
      "Unavoidable, and any stratum-level reading carries it.")
    A("7. **The calendar mismatch is D247's and is severe.** S1's 34-bar Impulse is ~1.3 "
      "sessions here against seven weeks daily; S2's 252-bar regression is ~9.8 sessions "
      "against a year.")

    A("\n## Verdict\n")
    if p["survivors"]:
        A(f"**{len(p['survivors'])} short cell(s) cleared all six hurdles: "
          f"`{'`, `'.join(p['survivors'])}`.**\n")
        A("Under R8 nothing is promoted. A clearing cell becomes a candidate needing its "
          "own pre-registered out-of-sample test on names this study never touched.\n")
    else:
        A("**ZERO of the 12 short cells clear all six hurdles.**\n")
        A("Per D264's stop, the construction is closed **on this sample** — no parameter "
          "sweep, no additional stratum, no third arm, no re-cut window, no 5-minute bars.\n")
        A("**And the closure is bounded, in the words fixed before the run:** it closes this "
          "construction on these eight survivor names. It does **not** close the intraday "
          "short as a question, because the sample is survivor-only, the bias runs *against* "
          "the short, and eight names is thin.\n")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args()
    if a.report_only:
        payload = json.loads(SUMMARY.read_text())
    else:
        payload = build()
        SUMMARY.write_text(json.dumps(payload, indent=1) + "\n")
    RESULTS.write_text(render(payload), encoding="utf-8")
    print(f"wrote {SUMMARY.name} and {RESULTS.name}")
    print(f"\nsurvivors: {payload['survivors'] or 'NONE'}")
    for st, k in SCORED:
        key = f"{st}:{k}"
        c, v, b = payload["cells"][key], payload["verdict"][key], payload["breakeven_bps"][key]
        print(f"  {st:4s} {k:16s} SR {c['excess_sharpe']:+7.3f}  CAGR {c['cagr']:+7.2%}  "
              f"be {b if b is None else round(b, 2)!s:>7s} vs {v['charged_bps']:.2f} bp  "
              f"{'ALL SIX' if v['clears_all'] else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
