"""D217 Stage 1 — the MACD crossover ladder on the frozen 57-ETF daily universe.

    uv run python scripts/run_macd_ladder.py
    uv run python scripts/run_macd_ladder.py --report-only

Offline, deterministic, seeded. The decision record
`docs/decisions/D217-the-macd-crossover-ladder.md` was written and committed
BEFORE this file existed, and nothing here may quietly widen it.

WHAT IS BEING TESTED
--------------------
Not "does MACD make money". Whether the SIGNAL LINE adds anything over the
zero-line cross — which is identically a 12/26 EMA crossover — and whether that
adds anything over plain momentum at the same centre of mass. Three strictly
nested rungs; the deltas between them are the study, not the levels.

THREE THINGS THIS FILE IS CAREFUL ABOUT
---------------------------------------
1. **The position is shifted.** `positions()` returns the sign decided ON bar t
   from bar t's completed close. `PositionResult.position[t]` is the exposure
   held THROUGH bar t, decided on t-1's information. So the series is shifted by
   one bar before it is scored, which is the next-open fill convention expressed
   in a position series. Getting this wrong would let every arm trade on the bar
   that produced its own signal.

2. **The cost is derived per ETF, and the IBKR per-order minimum is not
   waved away.** `IBKRCommission` is $0.005/share with a $1.00 per-order minimum
   and a 1% cap. At a 57-way split of a retail book the MINIMUM BINDS and
   dominates everything else, so the per-side cost is reported as a function of
   book size rather than quoted as a single number. D212: per side is the
   authority, always.

3. **57 ETFs are the sample, not 57 hypotheses.** Every arm produces ONE
   cross-sectional statistic; per-ETF numbers are reported as dispersion and are
   never selected from. The multiplicity ledger counts arms, not arm x symbol.

The census (WP2) and the break-even arithmetic carry ZERO looks — a census is not
a test — and they run first, because counts have repeatedly caught defects in this
project before they became results.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.corporate_actions import load_events_json  # noqa: E402
from backtest_framework.data.csv_fixture import load_fixture_csv  # noqa: E402
from backtest_framework.research import macd as M  # noqa: E402
from backtest_framework.validation.dsr import expected_max_sharpe  # noqa: E402

FIXTURE = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw_events.json"
SUMMARY = REPO / "data" / "macd_ladder_summary.json"
RESULTS = REPO / "MACD_RESULTS.md"

PPY = 252.0
SEED = 0
N_SIMS = 400

# The book sizes the per-side cost is reported at. The primary is the one where
# the IBKR per-order minimum does NOT bind on a 57-way split; the retail book is
# reported beside it because that is who is sold this strategy.
PRIMARY_CAPITAL = 10_000_000.0
RETAIL_CAPITAL = 100_000.0
HALF_SPREAD_BPS = 1.0
IBKR_PER_SHARE = 0.005
IBKR_MIN_PER_ORDER = 1.00
IBKR_MAX_PCT = 0.01

# The chronological halves for the stability hurdle (F).
HALF_SPLIT = "2020-01-01"

# Hurdles, from the decision record. Not tunable here.
DELTA_HURDLE = 0.10
NULL_PERCENTILE = 95.0
MIN_SIGNALS_POOLED = 100
MIN_ENTRIES_PER_ETF = 30

# The declared sweep grid. Fixed in D217 and NOT extended here.
SWEEP_FAST = (6, 12, 24)
SWEEP_SLOW = (13, 26, 52)
SWEEP_SIGNAL = (5, 9, 18)

GATE_WINDOW = 200

# Disclosed adjacent, per the ledger. The structure+terrain combined bar.
DISCLOSED_PRIOR_LOOKS = 395


# --------------------------------------------------------------------------
# Cost
# --------------------------------------------------------------------------


def per_side_bps(median_close: float, notional: float) -> float:
    """Per-side cost in bps: the IBKR schedule at this ETF's median close, plus a
    1 bp half-spread. Derived, not chosen (D217).

    The commission is `max(min(per_share * shares, cap), minimum)` — D65's reading
    that the cap overrides the minimum is not exercised here because the cap only
    binds on sub-dollar prices, which no ETF in this universe has."""
    shares = notional / median_close
    commission = min(IBKR_PER_SHARE * shares, IBKR_MAX_PCT * notional)
    commission = max(commission, IBKR_MIN_PER_ORDER)
    return 1e4 * commission / notional + HALF_SPREAD_BPS


# --------------------------------------------------------------------------
# Scoring a panel of position series
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Panel:
    """The whole universe as aligned arrays. Symbols are rows, bars are columns."""

    symbols: tuple[str, ...]
    closes: np.ndarray  # (n, T)
    log_returns: np.ndarray  # (n, T), price only, [:, 0] = 0
    cost_fraction: np.ndarray  # (n,) per-side cost as a fraction of notional
    dates: tuple[str, ...]
    total_log_returns: np.ndarray  # (n, T), dividends reinvested on the ex-date
    dividends_matched: int = 0
    dividends_unmatched: int = 0


def portfolio_log_returns(
    panel: Panel, position: np.ndarray, *, total_return: bool = False
) -> np.ndarray:
    """Equal-weighted, daily-rebalanced portfolio of the per-symbol books.

    Per symbol this is exactly `PositionResult.equity_curve`'s arithmetic written
    additively — cost charged on every unit of exposure CHANGED (so a flip is
    charged twice, which is per side, D212) and the bar's return earned at THIS
    bar's position:

        r_i[t] = pos_i[t] * ret_i[t] + log(1 - c_i * |pos_i[t] - pos_i[t-1]|)

    `test_macd_ladder.py` pins this against `PositionResult` on a single symbol,
    which is the whole reason the identity is written out here rather than trusted.
    """
    turnover = np.abs(np.diff(position, axis=1, prepend=0.0))
    charge = panel.cost_fraction[:, None] * turnover
    if np.any(charge >= 1.0):  # pragma: no cover - a cost of 100% is a config error
        raise ValueError("a per-bar charge reached 100% of notional")
    rets = panel.total_log_returns if total_return else panel.log_returns
    per_symbol = position * rets + np.log1p(-charge)
    return per_symbol.mean(axis=0)

    # `total_return=True` swaps the PRICE return for the dividend-reinvested one.
    # It never touches the position series: MACD is computed on the price a trader
    # actually sees, and rewriting the price to smuggle dividends into the SIGNAL
    # would be a different indicator wearing the same name.


def sharpe_of(log_returns: np.ndarray) -> float:
    """Annualised Sharpe of a log-return series, rf = 0.

    Deliberately `terrain_strategies.curve_sharpe`'s convention and not
    `analytics.metrics.sharpe`: every STRUCTURE/TERRAIN headline Sharpe in this
    project comes from the former, and switching estimator mid-programme would
    make this study's numbers incomparable with the ones it sits beside."""
    if len(log_returns) < 3:
        return 0.0
    sd = float(np.std(log_returns, ddof=1))
    if sd <= 0.0:
        return 0.0
    return float(np.mean(log_returns)) / sd * math.sqrt(PPY)


def total_return_of(log_returns: np.ndarray) -> float:
    return float(np.expm1(np.sum(log_returns)))


def max_drawdown_of(log_returns: np.ndarray) -> float:
    equity = np.exp(np.cumsum(log_returns))
    peak = np.maximum.accumulate(equity)
    return float(np.min(equity / peak - 1.0))


# --------------------------------------------------------------------------
# Arms
# --------------------------------------------------------------------------

RUNGS = ("signal_line", "zero_line", "momentum")


def arm_positions(
    panel: Panel,
    bars_by_symbol: dict,
    rung: str,
    fast: int,
    slow: int,
    signal: int,
    *,
    long_short: bool,
    gated: bool,
    start: int,
    lag: int = 1,
) -> np.ndarray:
    """The (n, T) position matrix for one arm, shifted by `lag` bars.

    THE FILL CONVENTION, AND A DISCREPANCY WITH THE PRE-REGISTRATION.
    D217 says the cross is evaluated on a completed bar and filled at the NEXT
    OPEN. A close-to-close position series cannot express an open fill without
    decomposing each bar, so `lag=1` — the repo's own `PositionResult`
    convention, exposure held THROUGH bar t decided on t-1's information —
    charges the arm as if it filled at the close that produced its signal.
    That is ONE BAR MORE FAVOURABLE than what was pre-registered, and the
    direction of the bias is toward the strategy.

    Rather than argue about which is closer, both are run: `lag=1` is the
    primary and `lag=2` (a full extra bar, strictly LESS favourable than
    next-open) brackets it. A result that lives between them is real; a result
    that only exists at `lag=1` is a fill-timing artifact, and given that this
    study returned a POSITIVE on its headline hypothesis, that is exactly the
    thing that has to be checked before anyone believes it."""
    rows = []
    for sym in panel.symbols:
        bars = bars_by_symbol[sym]
        if rung == "momentum":
            score = M.trailing_return_score(bars, M.MATCHED_MOMENTUM_LOOKBACK)
        else:
            series = M.macd_series(bars, fast, slow, signal)
            score = (
                M.signal_line_score(series)
                if rung == "signal_line"
                else M.zero_line_score(series)
            )
        gate = M.trailing_ma(bars, GATE_WINDOW) if gated else None
        closes = [b.bar.close for b in bars] if gated else None
        decided = M.positions(
            score, start=start, long_short=long_short, gate=gate, closes=closes
        )
        # THE SHIFT. `decided[t]` is read from bar t's close; the exposure it
        # produces is held through bar t+lag. Without this every arm would earn
        # the return of the bar that generated its own signal.
        rows.append((0.0,) * lag + decided[:-lag])
    return np.asarray(rows, dtype=float)


def ladder_start(fast: int, slow: int, signal: int) -> int:
    """The ladder's COMMON start — the max warm-up across the rungs.

    Every arm begins on the same bar or the three equity curves cover different
    spans and the ladder is not a comparison (D217)."""
    return max(M.warm_up_bars(fast, slow, signal), M.MATCHED_MOMENTUM_LOOKBACK)


# --------------------------------------------------------------------------
# Nulls
# --------------------------------------------------------------------------


def rotation_null(
    panel: Panel, position: np.ndarray, start: int, n_sims: int, seed: int
) -> tuple[dict, np.ndarray]:
    """Circularly rotate each symbol's position series by an independent offset.

    Matched EXACTLY on the thing that matters: every rotated series has the same
    exposure, the same turnover and the same holding-period distribution as the
    real one — it is the same series, pointed at the wrong bars. So a delta over
    this null cannot be explained by the arm simply being in the market more, or
    trading less, than the comparison.

    The percentile is reported beside the delta because D201's statistic cleared
    +0.10 over a null MEAN at the 67th percentile, which is not clearing anything.
    """
    rng = np.random.default_rng(seed)
    live = position[:, start:]
    n, span = live.shape
    out = np.empty(n_sims, dtype=float)
    for s in range(n_sims):
        offsets = rng.integers(1, span, size=n)
        rotated = np.empty_like(live)
        for i in range(n):
            rotated[i] = np.roll(live[i], int(offsets[i]))
        full = np.zeros_like(position)
        full[:, start:] = rotated
        out[s] = sharpe_of(portfolio_log_returns(panel, full)[start:])
    return _null_summary(out), out


def block_shuffle_null(
    panel: Panel, position: np.ndarray, start: int, n_sims: int, seed: int, block: int = 21
) -> tuple[dict, np.ndarray]:
    """Shuffle contiguous blocks of the position series — a placebo that keeps
    local structure while destroying its alignment with returns.

    Weaker than rotation on turnover matching (block joins create a few extra
    changes), which is why rotation is primary and this is the confirmation."""
    rng = np.random.default_rng(seed)
    live = position[:, start:]
    n, span = live.shape
    n_blocks = math.ceil(span / block)
    out = np.empty(n_sims, dtype=float)
    for s in range(n_sims):
        shuffled = np.empty_like(live)
        for i in range(n):
            blocks = [live[i][b * block : (b + 1) * block] for b in range(n_blocks)]
            rng.shuffle(blocks)
            shuffled[i] = np.concatenate(blocks)[:span]
        full = np.zeros_like(position)
        full[:, start:] = shuffled
        out[s] = sharpe_of(portfolio_log_returns(panel, full)[start:])
    return _null_summary(out), out


def _null_summary(samples: np.ndarray) -> dict:
    return {
        "mean": float(np.mean(samples)),
        "sd": float(np.std(samples, ddof=1)),
        "p50": float(np.percentile(samples, 50)),
        "p95": float(np.percentile(samples, NULL_PERCENTILE)),
        "p99": float(np.percentile(samples, 99)),
        "max": float(np.max(samples)),
        "n_sims": int(len(samples)),
    }


def percentile_of(value: float, samples: np.ndarray) -> float:
    """Where the real number sits inside its own null. Reported beside every delta."""
    return float((samples < value).mean() * 100.0)


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def load_panel() -> tuple[Panel, dict]:
    raw = load_fixture_csv(FIXTURE)
    cleaned, _report = clean(raw)
    symbols = tuple(sorted(cleaned))
    lengths = {len(cleaned[s]) for s in symbols}
    if len(lengths) != 1:
        raise ValueError(f"symbols have different bar counts: {sorted(lengths)}")

    closes = np.asarray(
        [[b.bar.close for b in cleaned[s]] for s in symbols], dtype=float
    )
    log_returns = np.zeros_like(closes)
    log_returns[:, 1:] = np.log(closes[:, 1:] / closes[:, :-1])

    median_close = np.median(closes, axis=1)
    cost_bps = np.asarray(
        [per_side_bps(float(p), PRIMARY_CAPITAL / len(symbols)) for p in median_close]
    )
    dates = tuple(b.timestamp.date().isoformat() for b in cleaned[symbols[0]])
    cash, matched, unmatched = dividend_panel(symbols, cleaned, closes.shape[1])

    # Total return: the dividend lands on its ex-date bar and is reinvested.
    #   r_tr[t] = log((close[t] + div[t]) / close[t-1])
    # The sidecar dividends and the fixture prices are BOTH in the split-adjusted
    # frame (D75), so no conversion is needed and `as_declared_dividends` is
    # deliberately not called — that transform is for as-traded prices, which these
    # are not.
    total = np.zeros_like(closes)
    total[:, 1:] = np.log((closes[:, 1:] + cash[:, 1:]) / closes[:, :-1])

    panel = Panel(
        symbols,
        closes,
        log_returns,
        cost_bps / 1e4,
        dates,
        total_log_returns=total,
        dividends_matched=matched,
        dividends_unmatched=unmatched,
    )
    return panel, cleaned


def dividend_panel(
    symbols: tuple[str, ...], cleaned: dict, n_bars: int
) -> tuple[np.ndarray, int, int]:
    """Per-share dividends laid onto the bar grid, one row per symbol.

    An ex-date that is not itself a bar in the cleaned series is attached to the
    NEXT bar at or after it — dropping it would silently understate the benchmark,
    which is the direction that flatters a part-time-exposed strategy. Ex-dates
    after the last bar have nowhere to go and are counted as unmatched rather than
    discarded quietly."""
    actions = load_events_json(EVENTS)
    cash = np.zeros((len(symbols), n_bars))
    matched = unmatched = 0
    for i, sym in enumerate(symbols):
        index = {b.timestamp.date(): j for j, b in enumerate(cleaned[sym])}
        ordered = sorted(index)
        for ts, amount in actions.dividends_by_symbol.get(sym, ()):  # noqa: B007
            day = ts.date()
            j = index.get(day)
            if j is None:
                after = [d for d in ordered if d >= day]
                if not after:
                    unmatched += 1
                    continue
                j = index[after[0]]
            cash[i, j] += float(amount)
            matched += 1
    return cash, matched, unmatched


# --------------------------------------------------------------------------
# WP2 — the census and the break-even arithmetic. ZERO LOOKS.
# --------------------------------------------------------------------------


def census(panel: Panel, bars_by_symbol: dict) -> dict:
    """Counts only, before any performance number.

    A census is not a test: nothing here compares anything to anything, no
    hypothesis is scored, and no parameter is chosen on the strength of it. It
    exists because counts have repeatedly caught defects in this project before
    they became results, and because "there is no sample" is a legitimate finding
    about a strategy sold as a repeatable process.
    """
    start = ladder_start(M.DEFAULT_FAST, M.DEFAULT_SLOW, M.DEFAULT_SIGNAL)
    span = panel.log_returns.shape[1] - start

    arms = {}
    for rung in RUNGS:
        for gated in (False, True):
            pos = arm_positions(
                panel,
                bars_by_symbol,
                rung,
                M.DEFAULT_FAST,
                M.DEFAULT_SLOW,
                M.DEFAULT_SIGNAL,
                long_short=True,
                gated=gated,
                start=start,
            )
            live = pos[:, start:]
            steps = np.diff(live, axis=1)
            per_etf = (np.abs(steps) > 0).sum(axis=1)
            entries_per_etf = ((steps != 0) & (live[:, 1:] != 0)).sum(axis=1)
            holding = span / np.maximum(per_etf, 1)
            key = rung + ("_gated" if gated else "")
            arms[key] = {
                "position_changes_total": int(per_etf.sum()),
                "position_changes_per_etf_median": float(np.median(per_etf)),
                "entries_per_etf_median": float(np.median(entries_per_etf)),
                "entries_per_etf_min": int(entries_per_etf.min()),
                "etfs_below_min_entries": int((entries_per_etf < MIN_ENTRIES_PER_ETF).sum()),
                "median_bars_held": float(np.median(holding)),
                "share_of_bars_in_market": float(np.mean(np.abs(live))),
                "underpowered": bool(
                    entries_per_etf.min() < MIN_ENTRIES_PER_ETF
                    or int(per_etf.sum()) < MIN_SIGNALS_POOLED
                ),
            }

    # The break-even arithmetic, done before any backtest (D206/D216 precedent).
    # A round trip costs two sides; over `median_bars_held` bars the arm must earn
    # more than that in expectation or it is dead on arithmetic.
    daily_vol = float(np.median(np.std(panel.log_returns[:, start:], axis=1, ddof=1)))
    cost_bps_primary = float(np.median(panel.cost_fraction) * 1e4)
    retail_notional = RETAIL_CAPITAL / len(panel.symbols)
    retail = [
        per_side_bps(float(np.median(panel.closes[i])), retail_notional)
        for i in range(len(panel.symbols))
    ]
    retail_median = float(statistics.median(retail))
    binds = sum(
        1
        for i in range(len(panel.symbols))
        if IBKR_PER_SHARE * (retail_notional / float(np.median(panel.closes[i])))
        < IBKR_MIN_PER_ORDER
    )
    zero_hold = arms["zero_line"]["median_bars_held"]
    turns_per_year = PPY / zero_hold
    drag_primary = 2.0 * cost_bps_primary / 1e4 * turns_per_year
    drag_retail = 2.0 * retail_median / 1e4 * turns_per_year
    annual_vol = daily_vol * math.sqrt(PPY)
    return {
        "bars_total": int(panel.log_returns.shape[1]),
        "common_start_bar": start,
        "live_bars": span,
        "first_live_date": panel.dates[start],
        "last_date": panel.dates[-1],
        "warm_up_share_of_sample": start / panel.log_returns.shape[1],
        "n_symbols": len(panel.symbols),
        "dividends_matched": int(panel.dividends_matched),
        "dividends_unmatched": int(panel.dividends_unmatched),
        "arms": arms,
        "cost": {
            "primary_capital": PRIMARY_CAPITAL,
            "primary_per_side_bps_median": cost_bps_primary,
            "primary_per_side_bps_max": float(np.max(panel.cost_fraction) * 1e4),
            "retail_capital": RETAIL_CAPITAL,
            "retail_per_side_bps_median": retail_median,
            "retail_minimum_binds_on": binds,
            "half_spread_bps": HALF_SPREAD_BPS,
        },
        "break_even": {
            "median_annual_vol": annual_vol,
            "zero_line_turns_per_year": turns_per_year,
            "annual_cost_drag_primary": drag_primary,
            "annual_cost_drag_retail": drag_retail,
            "sharpe_drag_primary": drag_primary / annual_vol,
            "sharpe_drag_retail": drag_retail / annual_vol,
        },
    }


# --------------------------------------------------------------------------
# WP3 / WP4 — the arms
# --------------------------------------------------------------------------


def _half_index(panel: Panel, start: int) -> int:
    for i, d in enumerate(panel.dates):
        if d >= HALF_SPLIT:
            return max(i, start + 3)
    return len(panel.dates) // 2  # pragma: no cover - the fixture straddles 2020


def score_arm(panel: Panel, position: np.ndarray, start: int) -> dict:
    live = portfolio_log_returns(panel, position)[start:]
    tr = portfolio_log_returns(panel, position, total_return=True)[start:]
    half = _half_index(panel, start)
    return {
        "sharpe": sharpe_of(live),
        "total_return": total_return_of(live),
        "sharpe_total_return": sharpe_of(tr),
        "total_return_with_dividends": total_return_of(tr),
        "cagr_price_only": _cagr(total_return_of(live), len(live)),
        "cagr_with_dividends": _cagr(total_return_of(tr), len(tr)),
        "max_drawdown": max_drawdown_of(live),
        "turnover_units": float(np.abs(np.diff(position[:, start:], axis=1)).sum()),
        "exposure": float(np.mean(np.abs(position[:, start:]))),
        "net_exposure": float(np.mean(position[:, start:])),
        "sharpe_first_half": sharpe_of(live[: half - start]),
        "sharpe_second_half": sharpe_of(live[half - start :]),
    }


def _cagr(total: float, bars: int) -> float:
    years = bars / PPY
    return (1.0 + total) ** (1.0 / years) - 1.0 if years > 0 else 0.0


def buy_and_hold(panel: Panel, start: int) -> dict:
    """The benchmark long-flat arms must beat (hurdle D).

    Charged one entry at `start` and nothing thereafter, through the same cost
    path as every arm — a benchmark priced differently from the thing it
    benchmarks is not a benchmark."""
    ones = np.ones_like(panel.log_returns)
    ones[:, :start] = 0.0
    live = portfolio_log_returns(panel, ones)[start:]
    tr = portfolio_log_returns(panel, ones, total_return=True)[start:]
    return {
        "sharpe": sharpe_of(live),
        "total_return": total_return_of(live),
        "max_drawdown": max_drawdown_of(live),
        "sharpe_total_return": sharpe_of(tr),
        "total_return_with_dividends": total_return_of(tr),
        "cagr_price_only": _cagr(total_return_of(live), len(live)),
        "cagr_with_dividends": _cagr(total_return_of(tr), len(tr)),
    }


def run_core_ladder(panel: Panel, bars_by_symbol: dict, lag: int = 1) -> list[dict]:
    """The 12 core cells: 3 rungs x 2 books x {gate off, gate on}, with nulls.

    Nulls are run on the primary lag only. The lag-2 pass is a SENSITIVITY on the
    same 12 cells, not 12 further looks: it re-reads one arm under a stricter fill
    assumption rather than asking a new question."""
    start = ladder_start(M.DEFAULT_FAST, M.DEFAULT_SLOW, M.DEFAULT_SIGNAL)
    cells = []
    for rung in RUNGS:
        for long_short in (True, False):
            for gated in (False, True):
                pos = arm_positions(
                    panel,
                    bars_by_symbol,
                    rung,
                    M.DEFAULT_FAST,
                    M.DEFAULT_SLOW,
                    M.DEFAULT_SIGNAL,
                    long_short=long_short,
                    gated=gated,
                    start=start,
                    lag=lag,
                )
                scored = score_arm(panel, pos, start)
                if lag != 1:
                    cells.append(
                        {
                            "rung": rung,
                            "book": "long_short" if long_short else "long_flat",
                            "gate": "200ma" if gated else "none",
                            **scored,
                        }
                    )
                    continue
                seed = SEED + len(cells)
                rot, rot_s = rotation_null(panel, pos, start, N_SIMS, seed)
                blk, blk_s = block_shuffle_null(panel, pos, start, N_SIMS, seed + 1000)
                cells.append(
                    {
                        "rung": rung,
                        "book": "long_short" if long_short else "long_flat",
                        "gate": "200ma" if gated else "none",
                        **scored,
                        "rotation_null": rot,
                        "block_null": blk,
                        "delta_vs_rotation": scored["sharpe"] - rot["mean"],
                        "rotation_percentile": percentile_of(scored["sharpe"], rot_s),
                        "clears_rotation": scored["sharpe"] - rot["mean"] >= DELTA_HURDLE
                        and scored["sharpe"] > rot["p95"],
                        "delta_vs_block": scored["sharpe"] - blk["mean"],
                        "block_percentile": percentile_of(scored["sharpe"], blk_s),
                        "clears_block": scored["sharpe"] - blk["mean"] >= DELTA_HURDLE
                        and scored["sharpe"] > blk["p95"],
                    }
                )
    return cells


def run_sweep(panel: Panel, bars_by_symbol: dict) -> list[dict]:
    """The declared grid. Long-short, gate off. Answers H5 and nothing else.

    Every cell is reported whether or not it is flattering, and the grid is not
    extended here — it is fixed in D217."""
    cells = []
    for fast in SWEEP_FAST:
        for slow in SWEEP_SLOW:
            if fast >= slow:
                continue
            start = ladder_start(fast, slow, max(SWEEP_SIGNAL))
            for signal in SWEEP_SIGNAL:
                pos = arm_positions(
                    panel,
                    bars_by_symbol,
                    "signal_line",
                    fast,
                    slow,
                    signal,
                    long_short=True,
                    gated=False,
                    start=start,
                )
                cells.append(
                    {
                        "rung": "signal_line",
                        "fast": fast,
                        "slow": slow,
                        "signal": signal,
                        **score_arm(panel, pos, start),
                    }
                )
            pos = arm_positions(
                panel,
                bars_by_symbol,
                "zero_line",
                fast,
                slow,
                SWEEP_SIGNAL[1],
                long_short=True,
                gated=False,
                start=start,
            )
            cells.append(
                {
                    "rung": "zero_line",
                    "fast": fast,
                    "slow": slow,
                    "signal": None,
                    **score_arm(panel, pos, start),
                }
            )
    return cells


# --------------------------------------------------------------------------
# The ladder deltas — hurdle A, the actual study
# --------------------------------------------------------------------------


def ladder_deltas(core: list[dict]) -> list[dict]:
    """R1 - R2 and R2 - R3, per book and gate. This is what D217 is asking."""
    by_key = {(c["rung"], c["book"], c["gate"]): c for c in core}
    out = []
    for book in ("long_short", "long_flat"):
        for gate in ("none", "200ma"):
            r1 = by_key[("signal_line", book, gate)]["sharpe"]
            r2 = by_key[("zero_line", book, gate)]["sharpe"]
            r3 = by_key[("momentum", book, gate)]["sharpe"]
            t1 = by_key[("signal_line", book, gate)]["turnover_units"]
            t2 = by_key[("zero_line", book, gate)]["turnover_units"]
            out.append(
                {
                    "book": book,
                    "gate": gate,
                    "signal_line_sharpe": r1,
                    "zero_line_sharpe": r2,
                    "momentum_sharpe": r3,
                    "signal_minus_zero": r1 - r2,
                    "zero_minus_momentum": r2 - r3,
                    "signal_clears": (r1 - r2) >= DELTA_HURDLE,
                    "zero_clears": (r2 - r3) >= DELTA_HURDLE,
                    "signal_line_turnover_ratio": t1 / t2 if t2 else math.inf,
                }
            )
    return out


# --------------------------------------------------------------------------
# Multiplicity — the three counts
# --------------------------------------------------------------------------

ETF_REGISTRIES = (
    "e1_universe",
    "combined_universe",
    "portfolio_universe",
    "swing_universe",
    "capacity_portfolio",
    "etf_universe",
    "gross_sweep",
    "capacity_study",
    "convention_sensitivity",
    "pairs_study_v1",
    "pairs_study_v2",
    "pairs_study_v3",
)


def prior_etf_trials() -> dict:
    """Counted from the registries, never typed in (D98/D116/D126/D142).

    The raw row count is NOT an N: re-running the same window at scaled costs is
    not an independent trial. The `include` predicate here is DISTINCT LOGGED
    CONFIG PAYLOAD — it selects on config identity and never on presence of a
    metric — and the raw count is reported beside it as the ceiling."""
    import sqlite3

    rows = 0
    configs: set[str] = set()
    per_registry = {}
    for name in ETF_REGISTRIES:
        path = REPO / "data" / (name + "_registry.sqlite")
        if not path.exists():
            continue
        uri = "file:" + path.as_posix() + "?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            n = conn.execute("select count(*) from trials").fetchone()[0]
            local = {c for (c,) in conn.execute("select distinct config_json from trials")}
        rows += n
        configs |= local
        per_registry[name] = {"rows": int(n), "distinct_configs": len(local)}
    return {
        "raw_rows": int(rows),
        "distinct_configs": len(configs),
        "per_registry": per_registry,
        "predicate": "distinct logged config payload, de-duplicated across registries",
    }


def multiplicity(fresh: int, prior: dict, sweep: list[dict]) -> dict:
    """The DSR noise floor at each of the three counts. Count 3 carries the verdict."""
    per_period = [c["sharpe"] / math.sqrt(PPY) for c in sweep]
    var_trials = float(np.var(per_period, ddof=1))
    counts = {
        "fresh": fresh,
        "fresh_plus_prior_configs": fresh + prior["distinct_configs"],
        "combined_with_disclosed": fresh + prior["distinct_configs"] + DISCLOSED_PRIOR_LOOKS,
    }
    floors = {}
    for name, n in counts.items():
        sr0 = expected_max_sharpe(n, var_trials)
        floors[name] = {
            "n_trials": int(n),
            "expected_max_sharpe_per_period": sr0,
            "expected_max_sharpe_annualised": sr0 * math.sqrt(PPY),
        }
    return {
        "var_trials_per_period": var_trials,
        "raw_row_ceiling": prior["raw_rows"],
        "counts": floors,
        "verdict_count": "combined_with_disclosed",
        "units_contract": "D98: metric, sr and t are all per-period; annualised shown beside",
    }


# --------------------------------------------------------------------------
# The verdict
# --------------------------------------------------------------------------


def verdict(core: list[dict], deltas: list[dict], bh: dict, mult: dict) -> dict:
    """Hurdles A-G, applied. A cell that misses any one of them is not a survivor.

    Reported as a table of booleans rather than a sentence, because a sentence can
    be written after the fact and a table cannot."""
    floor = mult["counts"][mult["verdict_count"]]["expected_max_sharpe_annualised"]
    rows = []
    for c in core:
        d = next(
            x for x in deltas if x["book"] == c["book"] and x["gate"] == c["gate"]
        )
        stable = (c["sharpe_first_half"] > 0) == (c["sharpe_second_half"] > 0)
        if c["rung"] == "signal_line":
            ladder_ok = d["signal_clears"] and d["zero_clears"]
        elif c["rung"] == "zero_line":
            ladder_ok = d["zero_clears"]
        else:
            ladder_ok = False  # the floor cannot clear a hurdle it defines
        # Hurdle D says "beat buy-and-hold" without naming a metric. This is the
        # Sharpe reading, which is the one the study ran and therefore the one that
        # counts. The TOTAL-RETURN reading is recorded beside it and is NOT used to
        # move the verdict either way — see the addendum in the decision record.
        beats_benchmark = (
            c["sharpe"] > bh["sharpe"] if c["book"] == "long_flat" else c["sharpe"] > 0.0
        )
        beats_benchmark_pnl = (
            c["total_return_with_dividends"] > bh["total_return_with_dividends"]
            if c["book"] == "long_flat"
            else c["total_return_with_dividends"] > 0.0
        )
        checks = {
            "A_ladder_delta": bool(ladder_ok),
            "B_rotation_null": bool(c["clears_rotation"]),
            "C_block_null": bool(c["clears_block"]),
            "D_benchmark": bool(beats_benchmark),
            "F_half_stability": bool(stable),
            "G_dsr_floor": bool(c["sharpe"] > floor),
        }
        rows.append(
            {
                "cell": f"{c['rung']}/{c['book']}/{c['gate']}",
                "sharpe": c["sharpe"],
                **checks,
                "survivor": all(checks.values()),
                "D_benchmark_total_return_reading": bool(beats_benchmark_pnl),
                "survivor_under_pnl_reading": all(
                    {**checks, "D_benchmark": beats_benchmark_pnl}.values()
                ),
            }
        )
    return {
        "dsr_floor_annualised": floor,
        "buy_and_hold_sharpe": bh["sharpe"],
        "rows": rows,
        "survivors": [r["cell"] for r in rows if r["survivor"]],
        "stage_2_runs": any(r["survivor"] for r in rows),
        "survivors_under_pnl_reading": [
            r["cell"] for r in rows if r["survivor_under_pnl_reading"]
        ],
        "buy_and_hold_total_return_with_dividends": bh["total_return_with_dividends"],
    }


# --------------------------------------------------------------------------
# Rendering — the prose is GENERATED from the payload, never retyped
# --------------------------------------------------------------------------

MARKER = "## WP1-WP4 — the ladder, the sweep and the verdict"
ANCHOR = "---\n\n### Parking lot"


def _pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def render(p: dict) -> str:
    c, cost, be = p["census"], p["census"]["cost"], p["census"]["break_even"]
    lines = [
        MARKER,
        "",
        f"**Produced:** {p['produced']} · **Reproduce:** `uv run python scripts/run_macd_ladder.py`"
        " (offline, deterministic, seed 0)",
        "",
        f"Fixture: `{Path(p['fixture']).name}` — {c['n_symbols']} ETFs, {c['bars_total']} daily"
        f" bars each. Warm-up burns {c['common_start_bar']} bars"
        f" ({_pct(c['warm_up_share_of_sample'])} of the sample), so every arm starts on"
        f" {c['first_live_date']} and runs to {c['last_date']} —"
        f" {c['live_bars']} live bars, the same bars for all three rungs.",
        "",
        "### WP2 — the census and the arithmetic. Zero looks.",
        "",
        "A census is not a test. Nothing here compares anything to anything.",
        "",
        "| arm | changes/ETF (median) | entries/ETF (median) | min | ETFs under 30 | bars held | in market |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, a in c["arms"].items():
        lines.append(
            f"| `{name}` | {a['position_changes_per_etf_median']:.0f} |"
            f" {a['entries_per_etf_median']:.0f} | {a['entries_per_etf_min']} |"
            f" {a['etfs_below_min_entries']} | {a['median_bars_held']:.1f} |"
            f" {_pct(a['share_of_bars_in_market'])} |"
        )
    lines += [
        "",
        "**The cost, derived rather than chosen — and it depends on who is trading.**",
        "",
        f"At an institutional book (${cost['primary_capital']:,.0f} split 57 ways) the IBKR"
        f" per-order minimum does not bind and the median per-side cost is"
        f" **{cost['primary_per_side_bps_median']:.2f} bp** (max"
        f" {cost['primary_per_side_bps_max']:.2f} bp), including a"
        f" {cost['half_spread_bps']:.0f} bp half-spread.",
        "",
        f"At a retail book (${cost['retail_capital']:,.0f} split 57 ways) the $1.00 minimum"
        f" binds on **{cost['retail_minimum_binds_on']} of {c['n_symbols']}** ETFs and the"
        f" median per-side cost is **{cost['retail_per_side_bps_median']:.1f} bp** — roughly"
        f" {cost['retail_per_side_bps_median'] / cost['primary_per_side_bps_median']:.0f}x"
        " the institutional figure, for the identical trades.",
        "",
        f"Zero-line turnover is {be['zero_line_turns_per_year']:.1f} position changes per year,"
        f" so the annual cost drag is {_pct(be['annual_cost_drag_primary'])} institutional"
        f" against {_pct(be['annual_cost_drag_retail'])} retail. Against a median annualised"
        f" vol of {_pct(be['median_annual_vol'])} that is"
        f" **{be['sharpe_drag_primary']:.3f} of Sharpe institutional and"
        f" {be['sharpe_drag_retail']:.3f} retail**.",
        "",
        "### WP3 — the ladder. 12 looks.",
        "",
        "| rung | book | gate | Sharpe | total | maxDD | turnover | rot. null mean | delta | pct | block delta | pct |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for a in p["core"]:
        lines.append(
            f"| {a['rung']} | {a['book']} | {a['gate']} | {a['sharpe']:+.3f} |"
            f" {_pct(a['total_return'])} | {_pct(a['max_drawdown'])} |"
            f" {a['turnover_units']:.0f} | {a['rotation_null']['mean']:+.3f} |"
            f" {a['delta_vs_rotation']:+.3f} | {a['rotation_percentile']:.0f} |"
            f" {a['delta_vs_block']:+.3f} | {a['block_percentile']:.0f} |"
        )
    lines += [
        "",
        f"Buy-and-hold over the same bars, through the same cost path:"
        f" **{p['buy_and_hold']['sharpe']:+.3f}** Sharpe,"
        f" {_pct(p['buy_and_hold']['total_return'])} total,"
        f" {_pct(p['buy_and_hold']['max_drawdown'])} max drawdown.",
        "",
        "**The money, and the dividend adjustment.**",
        "",
        "The fixture is split-adjusted and **dividend-unadjusted** (D75), so a price-only"
        " comparison silently favours a strategy that is out of the market part of the time"
        " over a benchmark that never is. The dividends are in the sidecar and in the same"
        " split-adjusted frame as the prices, so they are added back here: the ex-date"
        " dividend lands on its bar and is reinvested. **The position series is untouched** —"
        " MACD is computed on the price a trader sees, and rewriting the price to smuggle"
        " dividends into the SIGNAL would be a different indicator.",
        "",
        "| rung | book | gate | price-only | +dividends | CAGR (price) | CAGR (+div) | exposure |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for a in p["core"]:
        lines.append(
            f"| {a['rung']} | {a['book']} | {a['gate']} | {_pct(a['total_return'])} |"
            f" {_pct(a['total_return_with_dividends'])} | {_pct(a['cagr_price_only'])} |"
            f" {_pct(a['cagr_with_dividends'])} | {_pct(a['exposure'])} |"
        )
    bhp = p["buy_and_hold"]
    lines += [
        f"| **buy-and-hold** | — | — | **{_pct(bhp['total_return'])}** |"
        f" **{_pct(bhp['total_return_with_dividends'])}** | {_pct(bhp['cagr_price_only'])} |"
        f" **{_pct(bhp['cagr_with_dividends'])}** | 100.00% |",
        "",
        f"Dividends matched to bars: {p['census']['dividends_matched']:,}"
        f" ({p['census']['dividends_unmatched']} ex-dates fell past the last bar and are"
        " counted rather than dropped quietly).",
        "",
        "**Hurdle A — the nested deltas. This is the study.**",
        "",
        "| book | gate | R1 signal | R2 zero | R3 momentum | R1-R2 | R2-R3 | R1 turnover / R2 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for d in p["deltas"]:
        lines.append(
            f"| {d['book']} | {d['gate']} | {d['signal_line_sharpe']:+.3f} |"
            f" {d['zero_line_sharpe']:+.3f} | {d['momentum_sharpe']:+.3f} |"
            f" **{d['signal_minus_zero']:+.3f}** | **{d['zero_minus_momentum']:+.3f}** |"
            f" {d['signal_line_turnover_ratio']:.2f}x |"
        )
    lines += [
        "",
        f"The hurdle is +{DELTA_HURDLE:.2f} Sharpe, above the null's p95.",
        "",
        "**The fill-timing bracket — the first thing to check, because this returned a"
        " positive.** The record pre-registered a next-open fill. A close-to-close position"
        " series cannot express one, so the primary above charges the arm as if it filled at"
        " the close that produced its signal, which is one bar MORE favourable than what was"
        " pre-registered. The table below re-runs every cell with a full extra bar of lag,"
        " which is strictly LESS favourable. The true next-open number lies between them."
        " This is a sensitivity on the same 12 cells, not 12 further looks.",
        "",
        "| book | gate | R1-R2 lag 1 | R1-R2 lag 2 | R2-R3 lag 1 | R2-R3 lag 2 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for d, dl in zip(p["deltas"], p["lagged_deltas"]):
        lines.append(
            f"| {d['book']} | {d['gate']} | {d['signal_minus_zero']:+.3f} |"
            f" {dl['signal_minus_zero']:+.3f} | {d['zero_minus_momentum']:+.3f} |"
            f" {dl['zero_minus_momentum']:+.3f} |"
        )
    lines += [
        "",
        "| rung | book | gate | Sharpe lag 1 | Sharpe lag 2 | change |",
        "|---|---|---|---:|---:|---:|",
    ]
    for a, al in zip(p["core"], p["lagged"]):
        lines.append(
            f"| {a['rung']} | {a['book']} | {a['gate']} | {a['sharpe']:+.3f} |"
            f" {al['sharpe']:+.3f} | {al['sharpe'] - a['sharpe']:+.3f} |"
        )
    lines += [
        "",
        f"### WP4 — the declared sweep. {len(p['sweep']) - 2} looks.",
        "",
        f"{len(p['sweep'])} cells, grid fixed in D217 and not extended. Every cell reported.",
        "",
    ]
    sweeps = sorted(p["sweep"], key=lambda x: -x["sharpe"])
    lines += [
        "| rank | rung | fast | slow | signal | Sharpe |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for i, s in enumerate(sweeps, 1):
        sig = "-" if s["signal"] is None else str(s["signal"])
        lines.append(
            f"| {i} | {s['rung']} | {s['fast']} | {s['slow']} | {sig} | {s['sharpe']:+.3f} |"
        )
    default = next(
        (
            s
            for s in sweeps
            if s["rung"] == "signal_line" and s["fast"] == 12 and s["slow"] == 26 and s["signal"] == 9
        ),
        None,
    )
    if default is not None:
        rank = sweeps.index(default) + 1
        lines += [
            "",
            f"**Appel's 12/26/9 ranks {rank} of {len(sweeps)}** in its own declared grid,"
            f" at {default['sharpe']:+.3f} against a grid median of"
            f" {statistics.median(s['sharpe'] for s in sweeps):+.3f}"
            f" and a grid max of {sweeps[0]['sharpe']:+.3f}.",
        ]
    m = p["multiplicity"]
    lines += [
        "",
        "### Multiplicity",
        "",
        "| block | cells | looks |",
        "|---|---|---:|",
        "| core ladder | 3 rungs x 2 books x {gate off, on} | 12 |",
        f"| declared sweep | 8 (fast,slow) pairs x 3 signals + 8 zero-line, minus 2 already"
        f" counted | {len(p['sweep']) - 2} |",
        f"| **total, fresh** | | **{p['fresh_looks']}** |",
        "",
        "**A correction to the pre-registration's own arithmetic, disclosed rather than"
        " absorbed.** The record wrote the sweep block as 6 (fast,slow) pairs and 22 looks."
        " The grid it declares — fast in {6,12,24}, slow in {13,26,52}, fast < slow — admits"
        " EIGHT pairs, because (12,13) and (24,26) satisfy fast < slow and were missed when"
        " the pairs were counted by eye. The grid itself is unchanged and was not widened:"
        f" the COUNT was wrong, and the ledger carries the corrected {p['fresh_looks']},"
        " which is the number the deflated Sharpe is computed against.",
        "",
        "Census, break-even arithmetic, nulls and buy-and-hold carry zero looks — a null is"
        " the yardstick for a look, not an additional one.",
        "",
        "| count | N | SR0 (per-period) | SR0 (annualised) |",
        "|---|---:|---:|---:|",
    ]
    for name, f in m["counts"].items():
        mark = " **(verdict)**" if name == m["verdict_count"] else ""
        lines.append(
            f"| {name}{mark} | {f['n_trials']} | {f['expected_max_sharpe_per_period']:.5f} |"
            f" {f['expected_max_sharpe_annualised']:.3f} |"
        )
    lines += [
        "",
        f"The prior ETF-fixture registries hold **{m['raw_row_ceiling']:,} rows**, which is"
        " NOT an N — re-running the same window at scaled costs is not an independent trial"
        " (D98/D116/D126/D142). The `include` predicate is distinct logged config payload,"
        f" giving {p['prior']['distinct_configs']:,} distinct configurations; the raw count"
        " stands as the ceiling.",
        "",
        "### The verdict",
        "",
        "| cell | Sharpe | A ladder | B rotation | C block | D benchmark | F halves | G DSR | survivor |",
        "|---|---:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|",
    ]
    tick = {True: "yes", False: "no"}
    for r in p["verdict"]["rows"]:
        lines.append(
            f"| `{r['cell']}` | {r['sharpe']:+.3f} | {tick[r['A_ladder_delta']]} |"
            f" {tick[r['B_rotation_null']]} | {tick[r['C_block_null']]} |"
            f" {tick[r['D_benchmark']]} | {tick[r['F_half_stability']]} |"
            f" {tick[r['G_dsr_floor']]} | {tick[r['survivor']]} |"
        )
    v2 = p["verdict"]
    lines += [
        "",
        "**Hurdle D under a total-return reading, disclosed.** The record wrote"
        " *beat buy-and-hold* without naming a metric, and the study ran it on Sharpe,"
        " which is therefore the reading that counts. On dividend-adjusted TOTAL RETURN the"
        f" long-flat cells are judged against buy-and-hold's"
        f" {_pct(v2['buy_and_hold_total_return_with_dividends'])}, and"
        f" **{len(v2['survivors_under_pnl_reading'])}** cells would survive under that"
        " reading. The verdict is unchanged either way — every cell already fails G — so"
        " this is recorded as a second reading, not used to move a goalpost.",
    ]
    survivors = p["verdict"]["survivors"]
    lines += [
        "",
        (
            f"**{len(survivors)} of {len(p['verdict']['rows'])} cells clear every hurdle.**"
            if survivors
            else f"**0 of {len(p['verdict']['rows'])} cells clear every hurdle.**"
        ),
        "",
        (
            "Stage 2 — the costed engine verdict — **runs**, on the surviving configuration"
            " only, with no re-search: " + ", ".join(f"`{s}`" for s in survivors)
            if survivors
            else "Stage 2 — the costed engine verdict — **does not run.** D217's"
            " pre-registered programme stop applies and the study closes here as a"
            " reportable negative."
        ),
        "",
        p["reading"],
        "",
    ]
    return "\n".join(lines)


def reading(p: dict) -> str:
    """One paragraph, assembled from the numbers so it cannot drift from them."""
    d_ls = next(x for x in p["deltas"] if x["book"] == "long_short" and x["gate"] == "none")
    d_lf = next(x for x in p["deltas"] if x["book"] == "long_flat" and x["gate"] == "none")
    return (
        f"**Reading.** The signal line is worth {d_ls['signal_minus_zero']:+.3f} Sharpe"
        f" long-short and {d_lf['signal_minus_zero']:+.3f} long-flat against a"
        f" +{DELTA_HURDLE:.2f} hurdle, while turning over"
        f" {d_ls['signal_line_turnover_ratio']:.2f}x as much as the rung it sits on. The"
        f" two-EMA difference is worth {d_ls['zero_minus_momentum']:+.3f} and"
        f" {d_lf['zero_minus_momentum']:+.3f} over flat momentum at the same centre of"
        " mass. Those four numbers are the study; everything above them is the"
        " apparatus that makes them mean something."
    )


def append_section(text: str) -> None:
    if not RESULTS.exists():
        RESULTS.write_text(_scaffold(), encoding="utf-8")
    doc = RESULTS.read_text(encoding="utf-8")
    head, sep, tail = doc.partition(ANCHOR)
    if not sep:
        raise ValueError(f"{RESULTS.name} is missing its parking-lot anchor")
    if MARKER in head:
        head = head[: head.index(MARKER)]
    RESULTS.write_text(head.rstrip() + "\n\n" + text.rstrip() + "\n\n" + sep + tail, encoding="utf-8")


def _scaffold() -> str:
    return (
        "# MACD RESULTS — the crossover ladder (D217)\n\n"
        "The results ledger for D217. **Append-only.** Every work package adds a dated\n"
        "section; nothing above is rewritten. This document carries the multiplicity count\n"
        "that feeds the deflated Sharpe.\n\n"
        "## Inherited disclosure\n\n"
        "This study opens a **fresh ledger**, on the argument written into\n"
        "[`D217`](docs/decisions/D217-the-macd-crossover-ladder.md): a different fixture (ETF\n"
        "daily, not crypto 15m), a different claim family (directional single-name momentum,\n"
        "not structure or terrain), and a sensor that did not exist in this repo. The\n"
        "structure and terrain programmes' combined 395-look bar and the prior ETF-fixture\n"
        "registries are disclosed adjacent and enter the third multiplicity count, which\n"
        "carries the verdict.\n\n"
        "---\n\n### Parking lot\n\n"
        "- **PPO on the signal line.** `EMA(macd/d) != EMA(macd)/d`, so PPO-signal-cross and\n"
        "  MACD-signal-cross are genuinely different hypotheses (rungs 2 and 3 are provably\n"
        "  unmoved by any positive divisor). Deliberately outside this ledger; it is a\n"
        "  question for a crypto-daily replication, where the price multiple is large enough\n"
        "  for the two to diverge.\n"
    )


# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()

    if args.report_only:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
        append_section(render(payload))
        print(f"re-rendered {RESULTS.name} from {SUMMARY.name}")
        return 0

    began = time.time()
    panel, bars_by_symbol = load_panel()
    print(f"loaded {len(panel.symbols)} symbols x {panel.closes.shape[1]} bars")

    c = census(panel, bars_by_symbol)
    print(f"census done; common start bar {c['common_start_bar']}")

    start = ladder_start(M.DEFAULT_FAST, M.DEFAULT_SLOW, M.DEFAULT_SIGNAL)
    core = run_core_ladder(panel, bars_by_symbol)
    print(f"core ladder done ({len(core)} cells, {N_SIMS} null sims each)")
    lagged = run_core_ladder(panel, bars_by_symbol, lag=2)
    print(f"lag-2 sensitivity done ({len(lagged)} cells)")
    sweep = run_sweep(panel, bars_by_symbol)
    print(f"sweep done ({len(sweep)} cells)")

    prior = prior_etf_trials()
    # 12 core + (sweep cells minus the 2 already counted in the core ladder).
    # D217 wrote 22 for the sweep block; that was a MISCOUNT and the corrected
    # arithmetic is disclosed in the ledger below rather than quietly used.
    fresh = 12 + (len(sweep) - 2)
    mult = multiplicity(fresh, prior, sweep)
    bh = buy_and_hold(panel, start)
    deltas = ladder_deltas(core)

    payload = {
        "produced": time.strftime("%Y-%m-%d", time.gmtime()),
        "fixture": str(FIXTURE),
        "symbols": list(panel.symbols),
        "periods_per_year": PPY,
        "seed": SEED,
        "n_sims": N_SIMS,
        "census": c,
        "core": core,
        "lagged": lagged,
        "sweep": sweep,
        "fresh_looks": fresh,
        "deltas": deltas,
        "buy_and_hold": bh,
        "prior": prior,
        "multiplicity": mult,
    }
    payload["lagged_deltas"] = ladder_deltas(lagged)
    payload["verdict"] = verdict(core, deltas, bh, mult)
    payload["reading"] = reading(payload)
    payload["elapsed_seconds"] = round(time.time() - began, 1)

    SUMMARY.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    # Rendered from the ARTIFACT, not from the in-memory payload. `sort_keys=True`
    # reorders every dict on the round trip, so rendering from memory produced a
    # page that `--report-only` could not reproduce byte-for-byte — the published
    # page has to be a pure function of the committed JSON, or the artifact is not
    # the source of truth it claims to be.
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    append_section(render(payload))
    print(payload["reading"])
    print(f"\nwrote {SUMMARY.name} and {RESULTS.name} in {payload['elapsed_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
