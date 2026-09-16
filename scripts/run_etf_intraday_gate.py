"""D226 — is the volume regime gate's fragility a property of the method, or of two coins?

    uv run python scripts/run_etf_intraday_gate.py
    uv run python scripts/run_etf_intraday_gate.py --smoke
    uv run python scripts/run_etf_intraday_gate.py --report-only

Offline, deterministic, seeded. The D226 pre-registration was written and committed
BEFORE this file existed; what follows restates it, and nothing here may quietly
widen it.

WHAT IS BEING TESTED
--------------------
D224/D225 found a **volume regime gate** — `EMA(n) > SMA(n)` on VOLUME, gating trade
ENTRIES only and never exiting — that beats its matched-count random null on BTC and
ETH. D225 then found that its working window is **one point wide** and INVERTS at
200h. Two readings survive that:

    (i)  the gate is real and the window is a genuinely narrow physical scale, or
    (ii) the gate is a two-asset accident and the "window" is the shape of noise.

Those are not distinguishable on two coins. This study puts the SAME mechanism, at
the SAME bar size, on **57 ETFs** — 57 draws from a different asset class with a
different microstructure — and sweeps the window across a grid that brackets D224's
committed 200 by a factor of four in each direction. Reading:

    a gate that works at one window on 57 ETFs and dies either side of it is (i);
    a gate whose 57-ETF sweep is a random walk around its null is (ii).

THE NULL CARRIES THE VERDICT, NOT THE PnL
-----------------------------------------
The gate can only REMOVE trades. On a book whose marginal trade does not cover its
costs, removing trades at random GAINS MONEY, so an improvement in net PnL is not
evidence of anything. The control is the **matched-count random null**: remove the
same COUNT of the parent's trades at random, 400 times, and ask where the gated book
sits in that distribution. It is recomputed per cell, because each window removes a
different number of trades and a null matched to the wrong count is not a null.

The ORACLE — remove the worst k trades by realised PnL — is the other bound. It is
look-ahead by construction, it is NEVER a strategy (D181: the look-ahead guard binds
strategies, not analytics), and it carries the word ORACLE everywhere it appears.

    capture = (gate - random_median) / (ORACLE - random_median)

THE HURDLES, FIXED IN ADVANCE
-----------------------------
    H_selectivity  net-Sharpe percentile >= 95 AND net-total-return percentile >= 95
                   in the matched-count null. BOTH legs, on the same cell.
    E_powered      >= 100 pooled trades AND >= 30 entries per ETF. The ORIGINAL
                   conjunction from D216 WP2 / D217, with both legs reported so a
                   failure can be attributed to the leg that caused it.
    P_beats_parent beats the ungated parent on Sharpe AND on total return.
    G              clears `expected_max_sharpe(N, var_trials)`, where `var_trials`
                   comes from the SIMULATED NULL and never from this study's own
                   cells (D219's amendment, and D224's demonstration that a sweep
                   containing real effects inflates the floor past usefulness).
                   Reported at N=10 (fresh), N=78 (+ hypothesis lineage) and N=45,819 (the
                   declared ledger, which carries the verdict).

FIVE THINGS THIS FILE IS CAREFUL ABOUT
--------------------------------------
1. **PPY = 26 * 252 = 6,552.** Twenty-six 15-minute bars in a US equity session,
   252 sessions in a year. NOT 252 (that is the daily fixture's calendar) and NOT
   35,040 (that is `run_sampling_invariance.ppy`'s 24/7 calendar, which overstates
   Sharpe here by sqrt(35040/6552) = 2.31x). Both wrong answers are asserted against
   below rather than left to a comment.

2. **The Sharpe estimator is parameterised, not patched.** `run_macd_ladder.sharpe_of`
   reads `PPY` as a MODULE GLOBAL, so it cannot be pointed at a different calendar by
   argument — and `L.PPY` must NOT be mutated, because `tests/unit/test_volume_filter.py`
   asserts `V.PPY is V.L.PPY` and a mutation breaks that identity for every other
   study in the process. `analytics.metrics.sharpe` takes `periods_per_year` as an
   argument; `_verify_sharpe_estimator` pins it EXACTLY equal to `L.sharpe_of` at
   `rf=0` when the two calendars agree, and it is then used at 6,552.

3. **The panel is inner-joined, not asserted equal.** `run_macd_ladder.load_panel`
   requires identical bar counts across symbols and RAISES on this fixture: short
   sessions differ per symbol, so the 57 ETFs carry seven distinct bar counts (IYT
   is 55,778 against the modal 56,056). The join here is on TIMESTAMP, and a bar
   missing on one ETF means no bar for any ETF at that instant — D45's rule, which
   is the only alignment under which one cross-sectional statistic means anything.

4. **The EMA is panel-shaped and its seeding is stated.** The repo's only EMA
   (`run_assembled_strategy.ema`) is 1-D. `panel_ema` is its recurrence written over
   rows, and `_verify_sensors` asserts the two agree bit-for-bit on a single row, so
   the gate computed here is the gate D224 committed and not a lookalike.

5. **The results page is its own file.** `MACD_RESULTS.md`'s appenders are
   destructive and would wipe the D218/D220 sections, so D226 writes
   `ETF_INTRADAY_RESULTS.md`. The page is always rendered from the RE-READ artifact,
   never from the in-memory payload — `sort_keys=True` reorders dicts on round-trip
   and D217 published a page that `--report-only` could not reproduce because of
   exactly that.

WHAT IS REUSED, AND WHY IT IS REUSED AND NOT RESTATED (D212)
------------------------------------------------------------
The panel container, the portfolio arithmetic, the cost derivation, trade extraction,
the census, the ORACLE ranking, the label permutation and the capture ratio all come
from `run_macd_ladder` and `run_volume_filter` unmodified. What is written locally is
exactly the set of things that are wrong at 15 minutes on a US equity calendar: the
panel loader (bar counts differ), the Sharpe annualisation (PPY differs), and the
functions that only annualise (`score`, `oracle_at`, `random_matched`). Those three
local functions still call the REUSED `book_from_trades` and `portfolio_log_returns`,
so the money arithmetic has exactly one implementation in this repo.

DISCLOSURE THAT BELONGS BESIDE THE VERDICT
------------------------------------------
**ETF volume is a weak instrument.** ETF liquidity comes from the creation/redemption
mechanism and the underlying basket, so on-exchange volume is a poor proxy for
interest — a quiet tape can mean the authorised participants simply did not need to
trade. This is the same caveat D220 published, and it cuts one way: a NEGATIVE here
is weaker evidence against the gate as a concept than the same result on single names
or crypto would be. A POSITIVE is not weakened by it at all.
"""

from __future__ import annotations

import argparse
import bisect
import gc
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.analytics import metrics  # noqa: E402
from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.corporate_actions import load_events_json  # noqa: E402
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.research import macd as M  # noqa: E402
from backtest_framework.validation.dsr import expected_max_sharpe  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module  # dataclasses resolve __module__ through sys.modules
    spec.loader.exec_module(module)
    return module


L = _load("run_macd_ladder", "run_macd_ladder.py")  # Panel, portfolio arithmetic, cost
V = _load("run_volume_filter", "run_volume_filter.py")  # trades, census, bounds, capture
A = _load("run_assembled_strategy", "run_assembled_strategy.py")  # ema/sma, 1-D

# `run_assembled_strategy` imports `run_sampling_invariance` for its 24/7 `ppy`.
# NOTHING in this file may reach through it: `S.ppy(15)` is 35,040 — a 365-day
# calendar — and using it here would overstate every Sharpe by 2.31x. Only `A.ema`
# and `A.sma` are touched, and only as the reference the local sensors are pinned to.
assert "run_sampling_invariance" in sys.modules

FIXTURE = REPO / "data" / "fixtures" / "etf_intraday_15m_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "etf_intraday_15m_raw_events.json"
SUMMARY = REPO / "data" / "etf_intraday_gate_summary.json"
RESULTS = REPO / "docs" / "results" / "ETF_INTRADAY_RESULTS.md"

# A smoke run must be incapable of being mistaken for the study, so it writes to its
# own artifact and its own page. Same code path, different filenames — a `--smoke`
# result that silently overwrote the real one would be the worst possible bug here.
SMOKE_SUMMARY = REPO / "data" / "etf_intraday_gate_summary.smoke.json"
SMOKE_RESULTS = REPO / "ETF_INTRADAY_RESULTS.smoke.md"

# ---- The calendar. Established by prior investigation; violating it is silent. ----
BAR_MINUTES = 15
BARS_PER_SESSION = 26  # 09:30 .. 15:45 inclusive, the fixture's own session
SESSIONS_PER_YEAR = 252
PPY = float(BARS_PER_SESSION * SESSIONS_PER_YEAR)
assert PPY == 6552.0
assert PPY != 252.0, "252 is the DAILY fixture's calendar, not this one"
assert PPY != 35040.0, "35,040 is a 24/7 calendar; US equities are not 24/7"

# ---- The parent arm. D224's committed configuration, unchanged. ----
K = 4
LENGTH, SIGNAL = 34 * K, 9 * K  # (136, 36) — the 33-hour channel selected in D224
LAG = 1  # exposure held THROUGH bar t is decided from bar t-1's close (repo convention)
WARM_UP = M.impulse_warm_up_bars(LENGTH, SIGNAL)
assert WARM_UP == 4049, f"the Impulse warm-up moved: {WARM_UP}"

# ---- The sweep. Windows in BARS, not hours: at 15m, 200 bars is 50 hours. ----
WINDOWS = (48, 96, 144, 200, 288, 400, 560, 800, 1200, 1920)
COMMITTED_VOL_WINDOW = 200  # D224's committed VOL_WINDOW, the point D225 found inverts
assert COMMITTED_VOL_WINDOW in WINDOWS, "the committed window is not in its own grid"
# Every window is defined everywhere the arm trades — the longest (1,920) is well
# inside the warm-up (4,049) — so there is NO per-window start and the ten cells cover
# an identical span. A per-window start would make the sweep a comparison of spans.
assert max(WINDOWS) < WARM_UP

SMOKE_WINDOWS = (200, 400)
SMOKE_SYMBOLS = 3

SEED = 0
N_SIMS = 400
N_PERMUTATIONS = 2000  # V.label_permutation_p's own count, restated for the artifact
NULL_PERCENTILE = 95.0

# ---- The hurdles. From the pre-registration. Not tunable here. ----
MIN_POOLED_TRADES = 100
MIN_ENTRIES_PER_ETF = 30
FRESH_LOOKS = len(WINDOWS)  # 10

# THE LEDGER, and the judgement in it stated rather than buried.
#
# D226 runs on the ETF INTRADAY fixture, which has never been used. So the three
# counts this project reports are:
#
#   1. fresh                     10   the declared window sweep
#   2. + hypothesis lineage      78   D220's 12 (ETF daily, entry filter) + D224's
#                                     10 + D225's 46. The CLAIM has been looked at
#                                     even though this fixture has not, and D225's
#                                     40-cell sweep attaches specifically because
#                                     the 200-bar gate is used BECAUSE it pointed
#                                     there.
#   3. + disclosed ETF prior 45,819   plus 45,741 (45,346 distinct registry configs
#                                     + the 395 structure/terrain bar).
#
# Count 3 carries the verdict, as in every study in this line. Note what does NOT
# transfer: D225's crypto-fixture prior of 3,739. That was logged on Binance data
# and has no bearing on an ETF study - carrying it here would be arithmetic
# theatre. An earlier draft of this file declared 3,879, which was exactly that
# mistake.
INHERITED_LINEAGE = 12 + 10 + 46  # D220 + D224 + D225
DISCLOSED_ETF_PRIOR = 45_741  # 45,346 distinct configs + 395 structure/terrain
VERDICT_COUNT = FRESH_LOOKS + INHERITED_LINEAGE + DISCLOSED_ETF_PRIOR  # 45,819
LINEAGE_COUNT = FRESH_LOOKS + INHERITED_LINEAGE  # 78
ORACLE_GRID = (0.10, 0.20, 0.30, 0.50)

# Both return bases are reported. The dividend-adjusted one is PRIMARY and carries the
# verdict: D217's addendum turned a tie into a 17-point loss the moment dividends were
# put back, and on a 57-ETF long-flat book that is out of the market roughly half the
# time the omission is not a rounding difference — the smoke run alone moves the parent
# from -0.146 to +0.004 Sharpe. Price-only is reported beside it, never instead of it.
PRIMARY_BASE = "dividend_adjusted"
BASES = ("dividend_adjusted", "price_only")
_TOTAL_RETURN_FLAG = {"dividend_adjusted": True, "price_only": False}


# --------------------------------------------------------------------------
# Sensors — the one thing the repo does not already have panel-shaped
# --------------------------------------------------------------------------


def panel_ema(values: np.ndarray, window: int) -> np.ndarray:
    """(n, T) exponential moving average, `alpha = 2 / (window + 1)`.

    THE SEEDING CONVENTION, stated because it is load-bearing:

        out[:, 0] = values[:, 0]

    the series is seeded at its OWN FIRST OBSERVATION and is therefore defined from
    bar 0 onward with no NaN prefix. That is `run_assembled_strategy.ema`'s
    convention exactly — the one that produced D224's committed `VOL_WINDOW = 200`
    result — and `_verify_sensors` asserts the two agree bit-for-bit on a single row
    rather than trusting this paragraph.

    A first-observation seed is biased toward the seed for roughly the first
    `burn_in` bars, which is why the gate is never read before the arm's 4,049-bar
    warm-up: at the shortest window here (48) the seed is 1e-12 of its weight after
    ~700 bars, and at the longest (1,920) after ~27,000 — but the SMA leg is NaN
    until `window - 1` in any case, and a NaN SMA closes the gate, so no comparison
    is made against a half-warmed EMA that the SMA has not also seen.

    Written panel-shaped rather than looped per symbol because the gate is a
    (57, T) object that is indexed at (row, entry) thousands of times per cell; a
    per-symbol list of arrays would be the same numbers in a shape that invites a
    row/column transposition, and that class of bug is silent."""
    alpha = 2.0 / (window + 1.0)
    out = np.empty_like(values, dtype=float)
    out[:, 0] = values[:, 0]
    for t in range(1, values.shape[1]):
        out[:, t] = alpha * values[:, t] + (1.0 - alpha) * out[:, t - 1]
    return out


def panel_sma(values: np.ndarray, window: int) -> np.ndarray:
    """(n, T) simple moving average — `run_volume_filter.trailing_mean`, reused.

    Not restated: it is already exactly the mean of the `window` bars ENDING AT t
    inclusive, NaN before it exists, panel-shaped, and free of any calendar. D212."""
    return V.trailing_mean(values, window)


def _verify_sensors() -> None:
    """The local panel sensors ARE the 1-D ones the committed result was built with.

    Bit-for-bit, not approximately: an EMA seeded one bar differently, or an SMA
    labelled one bar differently, produces a gate that is right almost everywhere and
    wrong at exactly the entries that matter."""
    rng = np.random.default_rng(20260826)
    row = rng.lognormal(12.0, 1.0, 4000)
    for window in (48, 200, 1920):
        assert np.array_equal(
            panel_ema(row[None, :], window)[0], A.ema(row, window), equal_nan=True
        ), f"panel_ema disagrees with run_assembled_strategy.ema at {window}"
        assert np.array_equal(
            panel_sma(row[None, :], window)[0], A.sma(row, window), equal_nan=True
        ), f"panel_sma disagrees with run_assembled_strategy.sma at {window}"


def _verify_sharpe_estimator() -> None:
    """`analytics.metrics.sharpe(x, 0.0, ppy)` IS `run_macd_ladder.sharpe_of(x)` when
    the two calendars agree — so swapping to the parameterised one changes the
    CALENDAR and nothing else.

    This is the whole justification for not mutating `L.PPY`. Exact equality is
    asserted, not `isclose`: `_rf_period(0.0, ppy)` is exactly 0.0, so the two
    expressions reduce to the same floating-point operations in the same order, and
    anything less than exact would mean one of them had quietly changed."""
    rng = np.random.default_rng(4049)
    for _ in range(8):
        x = rng.normal(0.0, 0.01, 500)
        assert sharpe_at(x, L.PPY) == L.sharpe_of(x)
    flat = np.zeros(500)
    assert sharpe_at(flat, L.PPY) == L.sharpe_of(flat) == 0.0
    # The degenerate guards below are L.sharpe_of's, kept so the two agree EVERYWHERE
    # and not merely on well-behaved input. `metrics.sharpe` raises under 2 points and
    # returns +/-inf at zero variance; neither is a number this study can publish.
    assert sharpe_at(np.ones(2)) == 0.0


# --------------------------------------------------------------------------
# The panel — inner-joined, because load_panel() raises on this fixture
# --------------------------------------------------------------------------


def load_panel(n_symbols: int | None = None) -> tuple[object, dict, np.ndarray, dict]:
    """(Panel, aligned bars by symbol, (n, T) volumes, a load report).

    WHY THIS IS LOCAL. `run_macd_ladder.load_panel` refuses a universe whose symbols
    have different bar counts, and this fixture has seven distinct counts because
    half-sessions differ per ETF. The refusal is right for a daily universe and wrong
    here, so the join is written rather than the guard weakened — no published daily
    number can move as a result, because that function is untouched.

    WHY NOT `alignment.align_bars`. It implements the same inner join, but it returns
    `AlignedBar` rows carrying `Bar` objects and NO VOLUME — and volume is the entire
    sensor in this study. Rebuilding column arrays out of 55,778 row dicts, and
    re-joining the volumes alongside them by timestamp anyway, is more moving parts
    than the join itself. Its duplicate-timestamp guard (D99) IS carried over below,
    because a duplicate would silently drop a bar last-wins.

    THE PRICES AND VOLUMES ARE ASSUMED SPLIT-ADJUSTED, and that assumption is
    VERIFIED rather than trusted — see `_assert_split_adjusted`."""
    raw, volumes = load_fixture_csv_with_volumes(FIXTURE)
    if n_symbols is not None:  # --smoke
        # A smoke run has to EXERCISE the join, not skip it. Forty-one of the 57 ETFs
        # share the modal bar count, so the first three alphabetically would all be
        # the same length and the inner join — the reason this loader exists at all —
        # would be a no-op that proved nothing. The SHORTEST symbol is forced into the
        # subset instead, which both makes the join drop bars and (on this fixture)
        # happens to pull in the one ETF carrying a 4-for-1 split, so the split guard
        # is exercised too.
        shortest = min(raw, key=lambda s: (len(raw[s]), s))
        others = [s for s in sorted(raw) if s != shortest][: n_symbols - 1]
        keep = sorted([shortest, *others])
        raw = {s: raw[s] for s in keep}
        volumes = {s: volumes[s] for s in keep}

    cleaned, report = clean(raw, volumes)
    symbols = tuple(sorted(cleaned))
    raw_counts = {s: len(raw[s]) for s in symbols}

    # Volume follows the RAW series, so it is re-joined by timestamp: `clean()` drops
    # bars and returns no volume series of its own, and a positional zip against the
    # cleaned bars would silently shift every volume after the first dropped bar.
    volume_by_ts = {
        s: {tb.timestamp: v for tb, v in zip(raw[s], volumes[s], strict=True)}
        for s in symbols
    }

    index_by_symbol = {}
    for s in symbols:
        index = {tb.timestamp: j for j, tb in enumerate(cleaned[s])}
        if len(index) != len(cleaned[s]):  # D99: refuse loudly, never last-wins
            raise ValueError(f"{s}: duplicate bar timestamps — refusing to align")
        index_by_symbol[s] = index

    grid = sorted(set.intersection(*(set(i) for i in index_by_symbol.values())))
    if not grid:
        raise ValueError("the inner join is empty — the symbols share no timestamps")

    bars = {s: [cleaned[s][index_by_symbol[s][ts]] for ts in grid] for s in symbols}
    vol = np.asarray(
        [[volume_by_ts[s][ts] for ts in grid] for s in symbols], dtype=float
    )
    if not np.isfinite(vol).all():
        raise ValueError("a joined bar has no finite volume")
    if (vol <= 0.0).any():
        raise ValueError("a joined bar has non-positive volume; the cleaner missed it")

    closes = np.asarray([[b.bar.close for b in bars[s]] for s in symbols], dtype=float)
    log_returns = np.zeros_like(closes)
    log_returns[:, 1:] = np.log(closes[:, 1:] / closes[:, :-1])

    actions = load_events_json(EVENTS)
    splits_checked = _assert_split_adjusted(symbols, grid, closes, actions)
    cash, matched, unmatched = dividend_panel(symbols, grid, actions)

    # Total return: the dividend lands on its ex-date bar and is reinvested.
    #   r_tr[t] = log((close[t] + div[t]) / close[t-1])
    # Identical to `load_panel`'s arithmetic. Both the sidecar dividends and the
    # fixture prices are in the split-adjusted frame, so `as_declared_dividends` is
    # deliberately not called — that transform is for as-traded prices (D75).
    total = np.zeros_like(closes)
    total[:, 1:] = np.log((closes[:, 1:] + cash[:, 1:]) / closes[:, :-1])

    median_close = np.median(closes, axis=1)
    cost_bps = np.asarray(
        [
            L.per_side_bps(float(p), L.PRIMARY_CAPITAL / len(symbols))
            for p in median_close
        ]
    )

    panel = L.Panel(
        symbols,
        closes,
        log_returns,
        cost_bps / 1e4,
        tuple(ts.isoformat(sep=" ") for ts in grid),
        total_log_returns=total,
        dividends_matched=matched,
        dividends_unmatched=unmatched,
    )

    load_report = {
        "n_symbols": len(symbols),
        "n_bars_joined": len(grid),
        "raw_bar_counts": sorted({int(c) for c in raw_counts.values()}),
        "bars_dropped_by_cleaner": len(report.changes),
        "bars_dropped_by_join": {
            s: int(len(cleaned[s]) - len(grid)) for s in symbols
        },
        "span": [grid[0].isoformat(sep=" "), grid[-1].isoformat(sep=" ")],
        "dividends_matched": matched,
        "dividends_unmatched": unmatched,
        # Recorded for the LOADED symbols and checked for them — reporting the whole
        # universe's split count beside a three-symbol smoke run would claim a
        # verification that never happened.
        "splits_recorded": sum(
            len(actions.splits_by_symbol.get(s, ())) for s in symbols
        ),
        "splits_checked": splits_checked,
        "median_cost_bps_per_side": float(np.median(cost_bps)),
        "half_spread_bps": L.HALF_SPREAD_BPS,
        "notional_per_symbol": L.PRIMARY_CAPITAL / len(symbols),
    }

    # A 3.19M-row fixture is ~1.3 GB of `TimestampedBar`/`Bar` objects before the
    # join. The arrays above are the only thing needed from the pre-join universe
    # (and `bars` holds references to the surviving objects), so the rest is dropped
    # here rather than carried through eleven minutes of nulls.
    del raw, volumes, cleaned, volume_by_ts, index_by_symbol
    gc.collect()
    return panel, bars, vol, load_report


def _assert_split_adjusted(symbols, grid, closes: np.ndarray, actions) -> int:
    """The study is run on the assumption that the fixture is SPLIT-ADJUSTED. Check it.

    Returns the number of splits actually checked, so the artifact can distinguish
    "verified" from "there were none in this subset".

    An unadjusted series shows a bare `log(1/ratio)` jump at the ex-date — IYT's
    4-for-1 is a -139% log return — and it would sit inside the price series as an
    enormous fake trend that the Impulse channel would happily trade, and inside the
    VOLUME series as an equally fake regime change that the gate would happily read.
    The threshold is half the split's own log magnitude: no US equity ETF moves 35%
    overnight, so a bound that loose cannot false-positive, and a surviving split
    (the smallest here is 2-for-1, a 69% jump) cannot sneak under it."""
    checked = 0
    for i, sym in enumerate(symbols):
        for ex_date, ratio in actions.splits_by_symbol.get(sym, ()):
            if ratio <= 0.0 or ratio == 1.0:
                continue
            j = bisect.bisect_left(grid, ex_date)
            if j <= 0 or j >= len(grid):
                continue  # the split is outside the joined span; nothing to check
            checked += 1
            jump = abs(float(np.log(closes[i, j] / closes[i, j - 1])))
            if jump > 0.5 * abs(math.log(ratio)):
                raise ValueError(
                    f"{sym}: a {ratio}-for-1 split at {ex_date.date()} is still in the "
                    f"prices (log return {jump:+.3f} at the ex-date bar) — this fixture "
                    "is NOT split-adjusted and the study must not run on it"
                )
    return checked


def _verify_split_guard() -> None:
    """The split guard must actually FIRE. A guard that has never been seen to raise
    is a comment with a function signature.

    Two synthetic ETFs, identical except that the second still carries a raw 4-for-1
    price drop at its recorded ex-date: the adjusted one must pass and the unadjusted
    one must raise."""
    from datetime import datetime, timedelta

    from backtest_framework.data.corporate_actions import CorporateActions

    ex = datetime(2020, 6, 15, 9, 30)
    grid = [ex - timedelta(minutes=15 * (10 - k)) for k in range(10)] + [
        ex + timedelta(minutes=15 * k) for k in range(10)
    ]
    actions = CorporateActions(splits_by_symbol={"OK": [(ex, 4.0)], "BAD": [(ex, 4.0)]})
    adjusted = np.full((1, len(grid)), 100.0)
    _assert_split_adjusted(("OK",), grid, adjusted, actions)  # must not raise
    unadjusted = adjusted.copy()
    unadjusted[0, 10:] = 25.0  # the raw 4-for-1 drop, never removed
    try:
        _assert_split_adjusted(("BAD",), grid, unadjusted, actions)
    except ValueError:
        return
    raise AssertionError("the split guard did not fire on an unadjusted series")


def dividend_panel(symbols, grid, actions) -> tuple[np.ndarray, int, int]:
    """Per-share dividends laid onto the INTRADAY bar grid, one row per symbol.

    The ex-dates in the sidecar are dates (midnight), and the bars are 09:30..15:45.
    An ex-date is attached to the FIRST BAR AT OR AFTER it, which for a normal ex-date
    is that session's 09:30 bar — and the return of that bar is the overnight one,
    which is precisely the bar across which the price drops by the dividend. Attaching
    it anywhere later would credit the cash after the drop had already been charged.

    Ex-dates after the last bar have nowhere to go and are COUNTED as unmatched rather
    than discarded quietly: dropping them would understate the benchmark, which is the
    direction that flatters a part-time-exposed strategy."""
    cash = np.zeros((len(symbols), len(grid)))
    matched = unmatched = 0
    for i, sym in enumerate(symbols):
        for ex_date, amount in actions.dividends_by_symbol.get(sym, ()):
            j = bisect.bisect_left(grid, ex_date)
            if j >= len(grid):
                unmatched += 1
                continue
            cash[i, j] += float(amount)
            matched += 1
    return cash, matched, unmatched


# --------------------------------------------------------------------------
# Scoring — the ONLY thing local here is the calendar
# --------------------------------------------------------------------------


def sharpe_at(log_returns: np.ndarray, periods_per_year: float = PPY) -> float:
    """Annualised Sharpe at a STATED calendar, rf = 0.

    `analytics.metrics.sharpe` because it takes `periods_per_year` as an argument.
    `run_macd_ladder.sharpe_of` reads its `PPY` from the module namespace and cannot
    be pointed anywhere else without mutating a global that another study's test
    asserts the identity of. The degenerate guards are `sharpe_of`'s, so the two are
    the same function everywhere and not merely on well-behaved input."""
    r = np.asarray(log_returns, dtype=float)
    if r.size < 3:
        return 0.0
    if float(np.std(r, ddof=1)) <= 0.0:
        return 0.0
    return metrics.sharpe(r, 0.0, periods_per_year)


def score_both(panel, position: np.ndarray, start: int) -> dict:
    """Net Sharpe and net total return on BOTH return bases, from ONE position matrix.

    `portfolio_log_returns` is the reused arithmetic — cost charged per side on every
    unit of exposure changed (D212) — called twice with the flag flipped. `total_return`
    swaps the PRICE return for the dividend-reinvested one and never touches the
    position series, so the two bases score the identical book."""
    out = {}
    for base in BASES:
        stream = L.portfolio_log_returns(
            panel, position, total_return=_TOTAL_RETURN_FLAG[base]
        )[start:]
        out[base] = {
            "sharpe": sharpe_at(stream),
            "total_return": L.total_return_of(stream),
        }
    return out


def drawdowns(panel, position: np.ndarray, start: int) -> dict:
    """Max drawdown per base. Computed for OBSERVED books only, never inside the null —
    400 sims x 2 bases of an extra cumsum buys nothing the percentile does not say."""
    return {
        base: L.max_drawdown_of(
            L.portfolio_log_returns(
                panel, position, total_return=_TOTAL_RETURN_FLAG[base]
            )[start:]
        )
        for base in BASES
    }


# --------------------------------------------------------------------------
# The two bounds — local ONLY because V's versions annualise at 252
# --------------------------------------------------------------------------


def oracle_at(panel, trades, shape, start: int, n_remove: int) -> dict:
    """ORACLE — remove the `n_remove` worst trades by REALISED PnL.

    Look-ahead by construction. A BOUND, NEVER A STRATEGY (D181: the look-ahead guard
    binds strategies, not analytics). `V.oracle_at` is this function annualised at 252;
    the ranking, the book construction and the money are identical.

    The ranking uses `V.extract_trades`' PnL, which is the DIVIDEND-ADJUSTED log return
    over the run less two sides of cost. So the ORACLE is defined once, on the primary
    base, and the price-only column reports what that same removal was worth — rather
    than two different ORACLEs removing two different sets of trades and being compared
    to each other."""
    keep = np.ones(len(trades), dtype=bool)
    if n_remove > 0:
        worst = np.argsort([t["pnl"] for t in trades])[:n_remove]
        keep[worst] = False
    return score_both(panel, V.book_from_trades(shape, trades, keep), start)


def random_matched(
    panel, trades, shape, start: int, n_remove: int, n_sims: int, seed: int
) -> dict:
    """The null for a selectivity claim: remove the same COUNT at random.

    Recomputed PER CELL, because each window blocks a different number of entries and
    a null matched to the wrong count is not a null. A delta over this cannot be
    explained by the gate simply having traded less, which is the only thing a
    removal-only filter can mechanically do."""
    rng = np.random.default_rng(seed)
    out = {
        base: {"sharpe": np.empty(n_sims), "total_return": np.empty(n_sims)}
        for base in BASES
    }
    for s in range(n_sims):
        keep = np.ones(len(trades), dtype=bool)
        if n_remove > 0:
            keep[rng.choice(len(trades), n_remove, replace=False)] = False
        scored = score_both(panel, V.book_from_trades(shape, trades, keep), start)
        for base in BASES:
            out[base]["sharpe"][s] = scored[base]["sharpe"]
            out[base]["total_return"][s] = scored[base]["total_return"]
    return out


# --------------------------------------------------------------------------
# The arm and the gate
# --------------------------------------------------------------------------


def parent_positions(panel, bars: dict) -> np.ndarray:
    """(n, T) long-flat Impulse MACD (136, 36) exposure, shifted by `LAG`.

    THE INFORMATION BOUNDARY. `M.positions` returns the sign decided ON bar t from
    bar t's completed close; the exposure it produces is held THROUGH bar t+1. Without
    the shift every symbol would earn the return of the bar that generated its own
    signal. `start=WARM_UP` is passed so every ETF begins on the same bar — 57 symbols
    are the SAMPLE, not 57 hypotheses, and a cross-sectional statistic over rows with
    different start dates is not one statistic."""
    rows = []
    for sym in panel.symbols:
        series = M.impulse_macd_series(bars[sym], LENGTH, SIGNAL)
        score = M.impulse_signal_score(series)
        decided = M.positions(score, start=WARM_UP, long_short=False)
        rows.append((0.0,) * LAG + decided[:-LAG])
    return np.asarray(rows, dtype=float)


def entry_allowed(volumes: np.ndarray, window: int) -> np.ndarray:
    """(n, T) boolean: may a trade whose exposure FIRST EXISTS at t be opened?

    THE GATE, and THE INFORMATION BOUNDARY for it. `live_gate = EMA(w) > SMA(w)` on
    volume is a statement about bar t's completed volume. With `LAG = 1` the exposure
    held through bar t was decided from bar t-1's close, so the newest volume
    legitimately available to that decision is bar t-1's:

        ok[:, 1:] = live_gate[:, :-1]

    which is D224's `ratio_ok[1:] = live_gate[:-1]` written panel-shaped. A gate that
    peeks one bar is the easiest way in the world to manufacture selectivity.

    A NaN SMA — the first `window - 1` bars — closes the gate rather than opening it.
    That side of the choice can only ever remove trades, never invent them, and no
    trade exists there in any case because the arm is flat until bar 4,049."""
    ema = panel_ema(volumes, window)
    sma = panel_sma(volumes, window)
    live_gate = np.where(np.isnan(sma), False, ema > sma)
    ok = np.zeros(volumes.shape, dtype=bool)
    ok[:, 1:] = live_gate[:, :-1]
    return ok


# --------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------


def run_cells(panel, bars: dict, volumes: np.ndarray, windows) -> tuple[list, dict]:
    shape = panel.log_returns.shape
    start = WARM_UP

    parent = parent_positions(panel, bars)
    trades = V.extract_trades(panel, parent, start)
    if not trades:
        raise ValueError("the parent arm took no trades — nothing to gate")
    pnl = np.array([t["pnl"] for t in trades], dtype=float)
    rows = np.array([t["row"] for t in trades])
    entries = np.array([t["entry"] for t in trades])

    parent_scores = score_both(panel, parent, start)
    parent_block = {
        "rung": "impulse_signal",
        "length": LENGTH,
        "signal": SIGNAL,
        "lag": LAG,
        "warm_up_bars": WARM_UP,
        "census": V.census(trades, shape[0]),
        "exposure": float(np.mean(np.abs(parent[:, start:]))),
        "max_drawdown": drawdowns(panel, parent, start),
        "scores": parent_scores,
        # The space any filter has to work in, at its own removal count. ORACLE.
        "oracle_grid": [
            {
                "remove_fraction": f,
                "n_removed": int(round(f * len(trades))),
                "scores": oracle_at(
                    panel, trades, shape, start, int(round(f * len(trades)))
                ),
            }
            for f in ORACLE_GRID
        ],
    }

    cells = []
    for window in windows:
        ok = entry_allowed(volumes, window)
        keep = ok[rows, entries]  # the gate is read AT THE ENTRY BAR and nowhere else
        n_remove = int((~keep).sum())
        book = V.book_from_trades(shape, trades, keep)
        observed = score_both(panel, book, start)
        kept_trades = [t for t, k in zip(trades, keep) if k]

        degenerate = n_remove == 0 or n_remove == len(trades)
        oracle = None if degenerate else oracle_at(panel, trades, shape, start, n_remove)
        null = (
            None
            if degenerate
            else random_matched(panel, trades, shape, start, n_remove, N_SIMS, SEED)
        )

        per_base = {}
        for base in BASES:
            value = observed[base]
            if degenerate:
                # A window that blocks nothing (or everything) has no matched-count
                # null to sit in: every draw would be the parent itself. Reported as
                # a non-result rather than as a percentile of a point mass.
                per_base[base] = _degenerate_base(value, parent_scores[base])
                continue
            n_sh, n_tot = null[base]["sharpe"], null[base]["total_return"]
            p_sh = L.percentile_of(value["sharpe"], n_sh)
            p_tot = L.percentile_of(value["total_return"], n_tot)
            # HURDLE G. `var_trials` comes from the SIMULATED NULL and never from this
            # study's own cells: D219's amendment recorded that a sweep containing real
            # effects inflates it, and D224 showed the inflation is not marginal. The
            # matched-count null IS the null distribution, so its variance is the right
            # estimate. Per-period, per D98's units contract.
            var_pp = float(np.var(n_sh / math.sqrt(PPY), ddof=1))
            floor_fresh = expected_max_sharpe(FRESH_LOOKS, var_pp) * math.sqrt(PPY)
            floor_verdict = expected_max_sharpe(VERDICT_COUNT, var_pp) * math.sqrt(PPY)
            per_base[base] = {
                "sharpe": value["sharpe"],
                "total_return": value["total_return"],
                "parent_sharpe": parent_scores[base]["sharpe"],
                "parent_total_return": parent_scores[base]["total_return"],
                "oracle_sharpe": oracle[base]["sharpe"],
                "oracle_total_return": oracle[base]["total_return"],
                "null_sharpe_p50": float(np.percentile(n_sh, 50)),
                "null_sharpe_p95": float(np.percentile(n_sh, NULL_PERCENTILE)),
                "null_sharpe_sd": float(np.std(n_sh, ddof=1)),
                "null_total_p50": float(np.percentile(n_tot, 50)),
                "null_total_p95": float(np.percentile(n_tot, NULL_PERCENTILE)),
                "sharpe_pct_in_null": p_sh,
                "total_pct_in_null": p_tot,
                "capture_sharpe": V.capture(
                    value["sharpe"],
                    float(np.percentile(n_sh, 50)),
                    oracle[base]["sharpe"],
                ),
                "capture_total": V.capture(
                    value["total_return"],
                    float(np.percentile(n_tot, 50)),
                    oracle[base]["total_return"],
                ),
                "var_trials_per_period": var_pp,
                "floor_fresh": floor_fresh,
                "floor_verdict": floor_verdict,
                "H_selectivity": bool(
                    p_sh >= NULL_PERCENTILE and p_tot >= NULL_PERCENTILE
                ),
                "P_beats_parent": bool(
                    value["sharpe"] > parent_scores[base]["sharpe"]
                    and value["total_return"] > parent_scores[base]["total_return"]
                ),
                "G_clears_fresh_floor": bool(value["sharpe"] > floor_fresh),
                "G_clears_verdict_floor": bool(value["sharpe"] > floor_verdict),
            }

        cen = V.census(kept_trades, shape[0])
        cells.append(
            {
                "window_bars": window,
                "window_hours": window * BAR_MINUTES / 60.0,
                "is_committed_window": window == COMMITTED_VOL_WINDOW,
                "degenerate_null": degenerate,
                "trades_kept": int(keep.sum()),
                "trades_removed": n_remove,
                "removal_fraction": float(n_remove / len(trades)),
                "exposure": float(np.mean(np.abs(book[:, start:]))),
                "max_drawdown": drawdowns(panel, book, start),
                "gate_open_fraction": float(ok[:, start:].mean()),
                "census": cen,
                "permutation": V.label_permutation_p(pnl, ~keep, SEED),
                # HURDLE E, the ORIGINAL conjunction, with BOTH legs reported so a
                # failure can be attributed to the leg that caused it.
                "E_pooled_trades": int(cen["n_trades"]),
                "E_pooled_ok": bool(cen["n_trades"] >= MIN_POOLED_TRADES),
                "E_min_entries_per_etf": cen["min_entries_per_etf"],
                "E_min_entries_ok": bool(
                    cen["min_entries_per_etf"] >= MIN_ENTRIES_PER_ETF
                ),
                "E_powered": bool(
                    cen["n_trades"] >= MIN_POOLED_TRADES
                    and cen["min_entries_per_etf"] >= MIN_ENTRIES_PER_ETF
                ),
                "bases": per_base,
            }
        )
    return cells, parent_block


def _degenerate_base(value: dict, parent: dict) -> dict:
    nan = float("nan")
    return {
        "sharpe": value["sharpe"],
        "total_return": value["total_return"],
        "parent_sharpe": parent["sharpe"],
        "parent_total_return": parent["total_return"],
        "oracle_sharpe": nan,
        "oracle_total_return": nan,
        "null_sharpe_p50": nan,
        "null_sharpe_p95": nan,
        "null_sharpe_sd": nan,
        "null_total_p50": nan,
        "null_total_p95": nan,
        "sharpe_pct_in_null": nan,
        "total_pct_in_null": nan,
        "capture_sharpe": nan,
        "capture_total": nan,
        "var_trials_per_period": nan,
        "floor_fresh": nan,
        "floor_verdict": nan,
        "H_selectivity": False,
        "P_beats_parent": False,
        "G_clears_fresh_floor": False,
        "G_clears_verdict_floor": False,
    }


def verdict(cells: list) -> dict:
    """Every hurdle, read on the PRIMARY (dividend-adjusted) base.

    Price-only is reported in full beside it and its own hurdle marks are in the
    artifact, but one base has to carry the verdict or the study has two answers."""
    rows = []
    for c in cells:
        b = c["bases"][PRIMARY_BASE]
        rows.append(
            {
                "window_bars": c["window_bars"],
                "H_selectivity": b["H_selectivity"],
                "E_powered": c["E_powered"],
                "P_beats_parent": b["P_beats_parent"],
                "G_clears_verdict_floor": b["G_clears_verdict_floor"],
                "G_clears_fresh_floor": b["G_clears_fresh_floor"],
                "survives": bool(
                    b["H_selectivity"]
                    and c["E_powered"]
                    and b["P_beats_parent"]
                    and b["G_clears_verdict_floor"]
                ),
                "H_on_price_only": c["bases"]["price_only"]["H_selectivity"],
            }
        )
    survivors = [r["window_bars"] for r in rows if r["survives"]]
    clearing_h = [r["window_bars"] for r in rows if r["H_selectivity"]]
    committed = next(
        (r for r in rows if r["window_bars"] == COMMITTED_VOL_WINDOW), None
    )
    return {
        "primary_base": PRIMARY_BASE,
        "rows": rows,
        "survivors": survivors,
        "windows_clearing_H": clearing_h,
        "n_clearing_H": len(clearing_h),
        "committed_window_clears_H": bool(committed and committed["H_selectivity"]),
        "committed_window_survives": bool(committed and committed["survives"]),
        # The D225 question, asked of 57 ETFs instead of two coins: is the working
        # region ONE POINT, a contiguous band, or scattered?
        "h_region_is_contiguous": _is_contiguous(clearing_h, [
            c["window_bars"] for c in cells
        ]),
        "h_region_width": len(clearing_h),
        "agrees_across_return_bases": all(
            r["H_selectivity"] == r["H_on_price_only"] for r in rows
        ),
        "fresh_looks": FRESH_LOOKS,
        "verdict_count": VERDICT_COUNT,
    }


def _is_contiguous(hits: list, grid: list) -> bool:
    """Do the windows that clear H form one unbroken run of the grid?

    Fewer than two hits is not a region and is reported as False, not as trivially
    contiguous — 'one point wide' is the D225 finding this study exists to test, and
    labelling it 'contiguous' would answer the question by definition."""
    if len(hits) < 2:
        return False
    positions = sorted(grid.index(h) for h in hits)
    return positions == list(range(positions[0], positions[0] + len(positions)))


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

MARKER = "## D226 — the volume regime gate on 57 ETFs at 15 minutes"


def _pct(x: float) -> str:
    return "n/a" if x != x else f"{x * 100:.2f}%"


def _num(x: float, spec: str = "+.3f") -> str:
    return "n/a" if x != x else format(x, spec)


def _mark(x: bool) -> str:
    return "PASS" if x else "FAIL"


def render(p: dict) -> str:
    """A pure function of the artifact.

    No clock, and no THRESHOLD read from module state: every hurdle constant printed
    below comes out of `p["config"]`, which is the config the numbers were actually
    computed under. That is D217's lesson generalised — `--report-only` on last
    month's artifact must reproduce last month's page, and it cannot do that if the
    page quotes today's constants against yesterday's numbers. Only `BASES` and
    `MARKER` are read from the module, and both are structural (a key order and a
    section heading), not a threshold."""
    out: list[str] = []
    w = out.append
    cfg, panel, par, v = p["config"], p["panel"], p["parent"], p["verdict"]
    smoke = p["smoke"]
    committed = cfg["committed_window"]

    w(MARKER)
    w("")
    if smoke:
        w("> **SMOKE RUN — NOT THE STUDY.** A reduced universe and a reduced grid, run")
        w("> only to prove the code path executes. No number below is a result.")
        w("")
    w(f"**Produced:** {p['produced']} · **Reproduce:** "
      "`uv run python scripts/run_etf_intraday_gate.py`")
    w("(offline, deterministic, seed 0) · Record: **D226**, pre-registered; the")
    w("pre-registration is restated in the runner's module docstring · Artifact:")
    w(f"`{p['artifact']}`")
    w("")
    w(f"{cfg['n_symbols']} ETFs · {cfg['bar_minutes']}m bars · "
      f"Impulse acceleration `({cfg['length']}, {cfg['signal']})` long-flat, lag "
      f"{cfg['lag']} · gate `EMA(w) > SMA(w)` on VOLUME at the ENTRY bar only · "
      f"**PPY = {cfg['ppy']:,.0f}** ({cfg['bars_per_session']} bars x "
      f"{cfg['sessions_per_year']} sessions).")
    w("")
    w(f"Panel: **{panel['n_bars_joined']:,} bars** inner-joined on timestamp from raw "
      f"counts {panel['raw_bar_counts']} · {panel['span'][0]} .. {panel['span'][1]} · "
      f"warm-up {cfg['warm_up_bars']:,} bars, leaving {p['n_bars_live']:,} live · "
      f"{panel['dividends_matched']:,} dividends matched "
      f"({panel['dividends_unmatched']:,} unmatched), "
      f"{panel['splits_checked']:,} of {panel['splits_recorded']:,} recorded splits "
      f"verified absent from the prices · median cost "
      f"{panel['median_cost_bps_per_side']:.2f} bp per side at "
      f"${panel['notional_per_symbol']:,.0f} a name.")
    w("")

    w("### The parent, and the space a gate has to work in")
    w("")
    c = par["census"]
    w(f"`Impulse({cfg['length']}, {cfg['signal']})` long-flat: **{c['n_trades']:,} "
      f"trades**, win rate **{_pct(c['win_rate'])}**, mean win {_pct(c['mean_win'])} "
      f"against mean loss {_pct(c['mean_loss'])}, median hold "
      f"{c['median_hold_bars']:,.0f} bars, exposure {_pct(par['exposure'])}. "
      f"Minimum {c['min_entries_per_etf']:,.0f} entries on the thinnest ETF, median "
      f"{c['median_entries_per_etf']:,.0f}.")
    w("")
    w("| base | Sharpe | total return | max drawdown |")
    w("|---|---:|---:|---:|")
    for base in BASES:
        w(f"| {base.replace('_', ' ')} | {_num(par['scores'][base]['sharpe'])} | "
          f"{_pct(par['scores'][base]['total_return'])} | "
          f"{_pct(par['max_drawdown'][base])} |")
    w("")
    w("**ORACLE** — remove the worst k% of trades by realised PnL. Look-ahead by")
    w("construction, never a strategy (D181), and the ceiling for ANY gate at that")
    w("removal count.")
    w("")
    w("| remove | n | ORACLE Sharpe | ORACLE total | (price-only Sharpe) |")
    w("|---:|---:|---:|---:|---:|")
    for g in par["oracle_grid"]:
        w(f"| {g['remove_fraction'] * 100:.0f}% | {g['n_removed']:,} | "
          f"{_num(g['scores'][PRIMARY_BASE]['sharpe'])} | "
          f"{_pct(g['scores'][PRIMARY_BASE]['total_return'])} | "
          f"{_num(g['scores']['price_only']['sharpe'])} |")
    w("")

    w("### The sweep — dividend-adjusted (primary)")
    w("")
    w("| window | hours | removed | Sharpe | total | ORACLE Sh | null p50 / p95 | "
      "pct in null (Sh / $) | capture Sh | perm |")
    w("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for cell in p["cells"]:
        b = cell["bases"][PRIMARY_BASE]
        star = " *" if cell["is_committed_window"] else ""
        w(f"| {cell['window_bars']:,}{star} | {cell['window_hours']:,.0f} | "
          f"{cell['trades_removed']:,} ({cell['removal_fraction'] * 100:.0f}%) | "
          f"{_num(b['sharpe'])} | {_pct(b['total_return'])} | "
          f"{_num(b['oracle_sharpe'])} | "
          f"{_num(b['null_sharpe_p50'])} / {_num(b['null_sharpe_p95'])} | "
          f"{_num(b['sharpe_pct_in_null'], '.0f')} / "
          f"{_num(b['total_pct_in_null'], '.0f')} | "
          f"{_num(b['capture_sharpe'] * 100, '+.0f')}% | "
          f"{_num(cell['permutation']['percentile'], '.0f')} |")
    w("")
    w(f"`*` = **{committed}**, D224's committed `VOL_WINDOW` and the point "
      "D225 found the effect inverts at.")
    w("`capture` is the fraction of the ORACLE-minus-random-median space the gate took,")
    w("at its own removal count. `perm` is the label-permutation percentile: the removed")
    w("set's mean PnL against the kept set's, holding the trade population and the")
    w("removal count fixed.")
    w("")

    w("### The sweep — price-only (the same books, dividends withheld)")
    w("")
    w("| window | Sharpe | total | pct in null (Sh / $) | H |")
    w("|---:|---:|---:|---:|:--:|")
    for cell in p["cells"]:
        b = cell["bases"]["price_only"]
        w(f"| {cell['window_bars']:,} | {_num(b['sharpe'])} | "
          f"{_pct(b['total_return'])} | "
          f"{_num(b['sharpe_pct_in_null'], '.0f')} / "
          f"{_num(b['total_pct_in_null'], '.0f')} | {_mark(b['H_selectivity'])} |")
    w("")
    w("Reported because D217's addendum turned a tie into a 17-point loss the moment")
    w("dividends were put back, and a gate whose verdict depends on which base it is")
    w("read at has not shown anything. Bases agree on hurdle H at every window: "
      f"**{'yes' if v['agrees_across_return_bases'] else 'NO'}**.")
    w("")

    w("### Hurdle E — powered, both legs")
    w("")
    w(f"The ORIGINAL conjunction: **>= {cfg['min_pooled_trades']} pooled trades AND >= "
      f"{cfg['min_entries_per_etf']} entries per ETF**. Both legs shown so a failure can")
    w("be attributed to the leg that caused it — a gate can keep thousands of pooled")
    w("trades while starving the thinnest ETF below the point where its column means")
    w("anything.")
    w("")
    w(f"| window | pooled trades | >= {cfg['min_pooled_trades']} | min entries / ETF | "
      f">= {cfg['min_entries_per_etf']} | **E** |")
    w("|---:|---:|:--:|---:|:--:|:--:|")
    for cell in p["cells"]:
        w(f"| {cell['window_bars']:,} | {cell['E_pooled_trades']:,} | "
          f"{_mark(cell['E_pooled_ok'])} | {cell['E_min_entries_per_etf']:,.0f} | "
          f"{_mark(cell['E_min_entries_ok'])} | {_mark(cell['E_powered'])} |")
    w("")

    w("### Hurdle G — the multiplicity floor")
    w("")
    w("**`var_trials` is taken from the simulated null, not from this study's own")
    w("cells.** D219's amendment recorded that a sweep containing real effects inflates")
    w("it; D224 showed the inflation is not marginal. The matched-count null IS the null")
    w("distribution, so its variance is the right estimate, and it is a DIFFERENT")
    w("estimate at every window because every window removes a different count.")
    w("")
    w(f"| window | Sharpe | null sd | floor @ {cfg['fresh_looks']} (fresh) | "
      f"floor @ {cfg['verdict_count']:,} (verdict) | G |")
    w("|---:|---:|---:|---:|---:|:--:|")
    for cell in p["cells"]:
        b = cell["bases"][PRIMARY_BASE]
        w(f"| {cell['window_bars']:,} | {_num(b['sharpe'])} | "
          f"{_num(b['null_sharpe_sd'], '.3f')} | {_num(b['floor_fresh'])} | "
          f"{_num(b['floor_verdict'])} | {_mark(b['G_clears_verdict_floor'])} |")
    w("")

    w("### Verdict")
    w("")
    w("| window | H | E | P (> parent) | G | **survives** |")
    w("|---:|:--:|:--:|:--:|:--:|:--:|")
    for r in v["rows"]:
        w(f"| {r['window_bars']:,} | {_mark(r['H_selectivity'])} | "
          f"{_mark(r['E_powered'])} | {_mark(r['P_beats_parent'])} | "
          f"{_mark(r['G_clears_verdict_floor'])} | {_mark(r['survives'])} |")
    w("")
    w(f"**{v['n_clearing_H']} of {len(v['rows'])} windows clear hurdle H. "
      f"{len(v['survivors'])} clear every hurdle.**")
    w("")
    w(f"- Windows clearing H: {v['windows_clearing_H'] or 'none'}.")
    w(f"- D224's committed {committed}: H "
      f"{'PASS' if v['committed_window_clears_H'] else 'FAIL'}, survives "
      f"{'yes' if v['committed_window_survives'] else 'no'}.")
    w(f"- The clearing region is contiguous: "
      f"**{'yes' if v['h_region_is_contiguous'] else 'no'}**, width "
      f"{v['h_region_width']} of {len(v['rows'])} grid points.")
    w("")
    w("**The D225 reading.** A gate that clears H in a contiguous band across a grid")
    w("spanning a factor of forty is a real scale. A gate that clears H at one isolated")
    w("point, or at scattered points, on 57 instruments from a different asset class is")
    w("the shape of noise, and D224/D225's two-coin result should be read as such.")
    w("")

    w("### The disclosure that belongs beside the verdict, not in a footnote")
    w("")
    w("**ETF volume is a weak instrument.** ETF liquidity comes from the")
    w("creation/redemption mechanism and the underlying basket, so on-exchange volume is")
    w("a poor proxy for interest — a quiet tape can simply mean the authorised")
    w("participants did not need to trade. A NEGATIVE result here is therefore **weaker")
    w("evidence against the gate as a concept** than the same result on single names or")
    w("crypto would be. A positive is not weakened by it at all.")
    w("")
    w("**The costs are the daily study's costs.** `per_side_bps` is the IBKR schedule at")
    w(f"each ETF's median close plus a {panel['half_spread_bps']:.0f} bp half-spread,")
    w(f"derived at ${panel['notional_per_symbol']:,.0f} a name — and it was derived for")
    w("DAILY rebalancing. At 15 minutes the half-spread is the optimistic part of that")
    w("estimate; it is charged per side on every unit of exposure changed either way.")
    w("")
    return "\n".join(out) + "\n"


def _scaffold() -> str:
    return (
        "# ETF INTRADAY RESULTS — the volume regime gate off its home fixture (D226)\n"
        "\n"
        "The results ledger for D226. **Its own file, deliberately.** `MACD_RESULTS.md`'s\n"
        "appenders splice around a parking-lot anchor and would have to rewrite that\n"
        "document to take this section; the D218 and D220 sections live there and are not\n"
        "worth the risk. This study also does not share a fixture, a bar size or a\n"
        "calendar with anything in that ledger.\n"
        "\n"
        "**Inherited disclosure.** D226 does not open a fresh ledger. It is the third look\n"
        "at one mechanism — D224 proposed the gate, D225 found its window one point wide\n"
        "and inverting — so the verdict count carries D224's declared 3,833 plus D225's 36\n"
        "plus this study's 10 windows.\n"
    )


def append_section(text: str) -> None:
    """Splice the D226 section in, IDEMPOTENTLY.

    D217 published a page `--report-only` could not reproduce, and D220's first
    `append_section` reintroduced the defect in a different place: its insert path and
    its replace path emitted a different number of blank lines. Here BOTH paths run
    the same single insertion — any existing section is truncated at the marker first,
    the head is `rstrip`ped, and exactly one blank line separates it from the section.
    Rendering the same artifact twice is therefore byte-identical."""
    page = RESULTS.read_text(encoding="utf-8") if RESULTS.exists() else _scaffold()
    head = page[: page.index(MARKER)] if MARKER in page else page
    RESULTS.write_text(
        head.rstrip("\n") + "\n\n" + text.rstrip("\n") + "\n", encoding="utf-8"
    )


# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="D226 — the volume gate on 57 ETFs at 15m")
    ap.add_argument("--report-only", action="store_true",
                    help="re-render the page from the committed artifact")
    ap.add_argument("--smoke", action="store_true",
                    help=f"{SMOKE_SYMBOLS} symbols, {len(SMOKE_WINDOWS)} windows, "
                         "written to a separate artifact and page")
    args = ap.parse_args()

    global RESULTS, SUMMARY
    if args.smoke:
        RESULTS, SUMMARY = SMOKE_RESULTS, SMOKE_SUMMARY

    if not args.report_only:
        _verify_sensors()
        _verify_sharpe_estimator()
        _verify_split_guard()
        t0 = time.time()
        panel, bars, volumes, load_report = load_panel(
            SMOKE_SYMBOLS if args.smoke else None
        )
        windows = SMOKE_WINDOWS if args.smoke else WINDOWS
        print(
            f"panel {volumes.shape} joined in {time.time() - t0:.1f}s; "
            f"{len(windows)} windows"
        )
        cells, parent = run_cells(panel, bars, volumes, windows)
        payload = {
            "produced": time.strftime("%Y-%m-%d"),
            "smoke": bool(args.smoke),
            "artifact": SUMMARY.relative_to(REPO).as_posix(),
            "config": {
                "n_symbols": len(panel.symbols),
                "symbols": list(panel.symbols),
                "bar_minutes": BAR_MINUTES,
                "bars_per_session": BARS_PER_SESSION,
                "sessions_per_year": SESSIONS_PER_YEAR,
                "ppy": PPY,
                "length": LENGTH,
                "signal": SIGNAL,
                "lag": LAG,
                "warm_up_bars": WARM_UP,
                "windows": list(windows),
                "committed_window": COMMITTED_VOL_WINDOW,
                "n_sims": N_SIMS,
                "n_permutations": N_PERMUTATIONS,
                "seed": SEED,
                "null_percentile": NULL_PERCENTILE,
                "min_pooled_trades": MIN_POOLED_TRADES,
                "min_entries_per_etf": MIN_ENTRIES_PER_ETF,
                "fresh_looks": FRESH_LOOKS,
                "verdict_count": VERDICT_COUNT,
                "units_contract": "D98: metric, sr and t are all per-period",
            },
            "panel": load_report,
            "n_bars_live": load_report["n_bars_joined"] - WARM_UP,
            "parent": parent,
            "cells": cells,
            "verdict": verdict(cells),
        }
        SUMMARY.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"wrote {SUMMARY.name} in {time.time() - t0:.1f}s")

    # ALWAYS render from the RE-READ artifact, never from the in-memory payload:
    # `sort_keys=True` reorders dicts on round-trip, and D217 published a page that
    # `--report-only` could not reproduce because of exactly that.
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    append_section(render(payload))
    v = payload["verdict"]
    print(f"rendered {RESULTS.name}")
    print(f"H cleared at windows {v['windows_clearing_H'] or 'none'}; "
          f"survivors {v['survivors'] or 'none'}; "
          f"contiguous {v['h_region_is_contiguous']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
