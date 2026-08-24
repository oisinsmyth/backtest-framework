"""Gates on the D217 Stage-1 runner and its published numbers.

Three jobs, in descending order of how much they matter:

  1. **Pin the runner's portfolio arithmetic against `PositionResult`.** The runner
     rewrites `PositionResult.equity_curve` additively in numpy so 57 symbols x
     400 null sims x 12 cells finishes in a minute. A rewritten cost path is
     exactly the defect D212 records — one path charging per round trip while
     another charged per side, a 2x discrepancy across one study — so the two are
     pinned against each other rather than believed.

  2. **Pin the headline numbers in MACD_RESULTS.md against the JSON artifact**,
     by REGENERATING each figure in the page's own format rather than retyping it.
     Re-running the study and forgetting to re-render is then a red suite instead
     of a page that quietly lies.

  3. Pin the ledger arithmetic, because the study already got it wrong once.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.terrain_strategies import PositionResult
from backtest_framework.simulator.fills import Bar

REPO = Path(__file__).resolve().parents[2]
SUMMARY = REPO / "data" / "macd_ladder_summary.json"
RESULTS = REPO / "MACD_RESULTS.md"


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_macd_ladder", REPO / "scripts" / "run_macd_ladder.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Registered before exec: the runner defines a @dataclass, and dataclasses
    # resolves `cls.__module__` through sys.modules while processing the class.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


R = _load_runner()


@pytest.fixture(scope="module")
def payload():
    if not SUMMARY.exists():  # pragma: no cover - the artifact is committed
        pytest.skip("run scripts/run_macd_ladder.py first")
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page():
    if not RESULTS.exists():  # pragma: no cover - the ledger is committed
        pytest.skip("run scripts/run_macd_ladder.py first")
    return RESULTS.read_text(encoding="utf-8").replace("−", "-")


# --------------------------------------------------------------------------
# 1. The cost path, pinned against the implementation it replaces
# --------------------------------------------------------------------------


def test_the_numpy_portfolio_agrees_with_position_result_on_one_symbol():
    """D212's defect, made impossible rather than promised against."""
    rng = np.random.default_rng(7)
    n_bars = 400
    rets = rng.normal(0.0, 0.01, n_bars)
    rets[0] = 0.0
    pos = np.sign(rng.normal(0.0, 1.0, n_bars))
    cost_bps = 4.0

    panel = R.Panel(
        symbols=("X",),
        closes=np.exp(np.cumsum(rets))[None, :] * 100.0,
        log_returns=rets[None, :],
        cost_fraction=np.asarray([cost_bps / 1e4]),
        dates=tuple(str(i) for i in range(n_bars)),
        total_log_returns=rets[None, :],
    )
    mine = R.portfolio_log_returns(panel, pos[None, :])

    theirs = PositionResult(
        position=tuple(float(p) for p in pos),
        returns=tuple(float(r) for r in rets),
        cost_bps=cost_bps,
        periods_per_year=R.PPY,
    ).equity_curve()

    theirs_log = np.diff(np.log(np.asarray(theirs)))
    assert mine[1:] == pytest.approx(theirs_log, abs=1e-12)
    # ...and the level, not just the increments.
    assert float(np.exp(np.sum(mine))) == pytest.approx(theirs[-1], rel=1e-12)


def test_a_long_short_flip_is_charged_twice_because_per_side_is_the_authority():
    """D212: per side. A flip changes two units of exposure and pays for both."""
    panel = R.Panel(
        symbols=("X",),
        closes=np.ones((1, 3)) * 100.0,
        log_returns=np.zeros((1, 3)),
        cost_fraction=np.asarray([100.0 / 1e4]),  # 100 bp per side, for legibility
        dates=("a", "b", "c"),
        total_log_returns=np.zeros((1, 3)),
    )
    flip = R.portfolio_log_returns(panel, np.asarray([[1.0, -1.0, -1.0]]))
    assert flip[1] == pytest.approx(math.log1p(-0.02), abs=1e-15)  # 2 units x 100bp
    entry = R.portfolio_log_returns(panel, np.asarray([[0.0, 1.0, 1.0]]))
    assert entry[1] == pytest.approx(math.log1p(-0.01), abs=1e-15)  # 1 unit


def test_the_ibkr_minimum_binds_at_retail_size_and_not_at_institutional_size():
    """The finding that made the cost a function of book size rather than a number."""
    institutional = R.per_side_bps(100.0, R.PRIMARY_CAPITAL / 57)
    retail = R.per_side_bps(100.0, R.RETAIL_CAPITAL / 57)
    # $0.005/share on 1,754 shares is $8.77 -> the $1.00 minimum is nowhere near.
    assert institutional == pytest.approx(0.5 + R.HALF_SPREAD_BPS, rel=1e-9)
    # $0.005/share on 17.5 shares is $0.09 -> the minimum binds and dominates.
    assert retail == pytest.approx(1e4 * 1.0 / (R.RETAIL_CAPITAL / 57) + R.HALF_SPREAD_BPS, rel=1e-9)
    assert retail > institutional


# --------------------------------------------------------------------------
# 2. No look-ahead in the runner's own shift
# --------------------------------------------------------------------------


def test_the_position_is_shifted_so_no_arm_earns_its_own_signal_bar():
    """The runner's one hand-written causality step, checked directly."""
    closes = [100.0 + 10.0 * math.sin(i / 9.0) + 0.03 * i for i in range(700)]
    bars = [
        TimestampedBar(datetime(2015, 1, 1) + timedelta(days=i), Bar(c, c, c, c))
        for i, c in enumerate(closes)
    ]
    panel = R.Panel(
        symbols=("X",),
        closes=np.asarray([closes]),
        log_returns=np.zeros((1, len(closes))),
        cost_fraction=np.asarray([0.0]),
        dates=tuple(str(i) for i in range(len(closes))),
        total_log_returns=np.zeros((1, len(closes))),
    )
    start = R.ladder_start(12, 26, 9)
    by_symbol = {"X": bars}
    for lag in (1, 2):
        pos = R.arm_positions(
            panel, by_symbol, "zero_line", 12, 26, 9,
            long_short=True, gated=False, start=start, lag=lag,
        )
        assert np.all(pos[0, :lag] == 0.0)
    one = R.arm_positions(
        panel, by_symbol, "zero_line", 12, 26, 9,
        long_short=True, gated=False, start=start, lag=1,
    )
    two = R.arm_positions(
        panel, by_symbol, "zero_line", 12, 26, 9,
        long_short=True, gated=False, start=start, lag=2,
    )
    # lag 2 is lag 1 delayed by exactly one more bar, nothing else.
    assert np.array_equal(two[0, 1:], one[0, :-1])


def test_every_arm_starts_on_the_same_bar():
    assert R.ladder_start(12, 26, 9) == max(393, R.M.MATCHED_MOMENTUM_LOOKBACK) == 393


# --------------------------------------------------------------------------
# 3. The published numbers, regenerated rather than retyped
# --------------------------------------------------------------------------


def present(page: str, needle: str, label: str) -> None:
    assert needle in page, f"{label}: {needle!r} is not in MACD_RESULTS.md"


def test_the_census_counts_are_the_published_ones(payload, page):
    c = payload["census"]
    present(page, str(c["common_start_bar"]), "common start bar")
    present(page, str(c["live_bars"]), "live bars")
    present(page, c["first_live_date"], "first live date")
    for name, a in c["arms"].items():
        present(page, f"`{name}`", f"census row {name}")
        present(page, f"{a['median_bars_held']:.1f}", f"{name} bars held")


def test_the_cost_figures_are_the_published_ones(payload, page):
    cost = payload["census"]["cost"]
    present(page, f"{cost['primary_per_side_bps_median']:.2f} bp", "institutional bps")
    present(page, f"{cost['retail_per_side_bps_median']:.1f} bp", "retail bps")
    present(page, f"{cost['retail_minimum_binds_on']} of 57", "minimum binds count")


def test_every_ladder_delta_is_the_published_one(payload, page):
    for d in payload["deltas"]:
        present(page, f"{d['signal_minus_zero']:+.3f}", f"R1-R2 {d['book']}/{d['gate']}")
        present(page, f"{d['zero_minus_momentum']:+.3f}", f"R2-R3 {d['book']}/{d['gate']}")


def test_the_lag_bracket_is_published_for_every_cell(payload, page):
    assert len(payload["lagged"]) == len(payload["core"])
    for a, al in zip(payload["core"], payload["lagged"]):
        present(page, f"{al['sharpe']:+.3f}", f"lag-2 sharpe {a['rung']}/{a['book']}")


def test_the_dsr_floors_are_the_published_ones(payload, page):
    for name, f in payload["multiplicity"]["counts"].items():
        present(page, str(f["n_trials"]), f"{name} n_trials")
        present(page, f"{f['expected_max_sharpe_annualised']:.3f}", f"{name} SR0")


def test_the_verdict_is_the_published_one(payload, page):
    v = payload["verdict"]
    present(page, f"{len(v['survivors'])} of {len(v['rows'])} cells", "survivor count")
    assert v["stage_2_runs"] == bool(v["survivors"])
    if not v["survivors"]:
        present(page, "does not run", "programme stop")


# --------------------------------------------------------------------------
# 4. The ledger, which this study already got wrong once
# --------------------------------------------------------------------------


def test_the_sweep_grid_admits_eight_pairs_not_six():
    """The miscount the RESULT discloses. (12,13) and (24,26) are easy to miss."""
    pairs = [(f, s) for f in R.SWEEP_FAST for s in R.SWEEP_SLOW if f < s]
    assert len(pairs) == 8
    assert (12, 13) in pairs and (24, 26) in pairs


def test_the_fresh_look_count_is_the_arithmetic_it_claims(payload):
    sweep_cells = len(payload["sweep"])
    assert sweep_cells == 8 * len(R.SWEEP_SIGNAL) + 8 == 32
    assert payload["fresh_looks"] == 12 + (sweep_cells - 2) == 42
    assert payload["multiplicity"]["counts"]["fresh"]["n_trials"] == 42


def test_the_raw_row_count_is_never_used_as_a_trial_count(payload):
    """129,286 rows is a ceiling, not an N (D98/D116/D126/D142)."""
    m = payload["multiplicity"]
    ceiling = m["raw_row_ceiling"]
    for f in m["counts"].values():
        assert f["n_trials"] < ceiling


def test_the_verdict_is_taken_at_the_largest_count(payload):
    m = payload["multiplicity"]
    counts = [f["n_trials"] for f in m["counts"].values()]
    assert m["counts"][m["verdict_count"]]["n_trials"] == max(counts)


# --------------------------------------------------------------------------
# 5. The dividend adjustment (post-close addendum)
# --------------------------------------------------------------------------


def _tiny_panel(divs):
    closes = np.asarray([[100.0, 100.0, 100.0]])
    total = np.zeros_like(closes)
    total[:, 1:] = np.log((closes[:, 1:] + np.asarray([divs])[:, 1:]) / closes[:, :-1])
    return R.Panel(
        symbols=("X",),
        closes=closes,
        log_returns=np.zeros_like(closes),
        cost_fraction=np.asarray([0.0]),
        dates=("a", "b", "c"),
        total_log_returns=total,
    )


def test_a_long_position_receives_the_dividend_and_a_short_pays_it():
    """The sign is the whole point: a short book is SHORT the dividend too, which is
    why the long-short arms get WORSE when dividends are added back and the
    long-flat arms get better."""
    panel = _tiny_panel([0.0, 1.0, 0.0])  # $1 on a $100 close = 1%
    longed = R.portfolio_log_returns(panel, np.asarray([[1.0, 1.0, 1.0]]), total_return=True)
    shorted = R.portfolio_log_returns(panel, np.asarray([[-1.0, -1.0, -1.0]]), total_return=True)
    assert longed[1] == pytest.approx(math.log(1.01), abs=1e-12)
    assert shorted[1] == pytest.approx(-math.log(1.01), abs=1e-12)


def test_price_only_returns_ignore_the_dividend_entirely():
    panel = _tiny_panel([0.0, 1.0, 0.0])
    price = R.portfolio_log_returns(panel, np.asarray([[1.0, 1.0, 1.0]]), total_return=False)
    assert price[1] == 0.0


def test_the_dividend_adjustment_widens_the_gap_against_the_strategy(payload):
    """The reason this addendum exists. A part-time-exposed arm forgoes less of the
    dividend stream than a benchmark that is never out, so a price-only comparison
    flatters it — and adding the dividends back is the direction that hurts."""
    bh = payload["buy_and_hold"]
    best = next(
        c for c in payload["core"]
        if (c["rung"], c["book"], c["gate"]) == ("signal_line", "long_flat", "none")
    )
    assert bh["total_return_with_dividends"] > bh["total_return"]
    price_gap = best["total_return"] - bh["total_return"]
    div_gap = best["total_return_with_dividends"] - bh["total_return_with_dividends"]
    assert div_gap < price_gap, "dividends must widen the gap against the arm"
    assert div_gap < 0.0, "the best cell does not beat buy-and-hold on money"


def test_every_dividend_found_a_bar(payload):
    c = payload["census"]
    assert c["dividends_matched"] > 2000
    assert c["dividends_unmatched"] == 0


def test_the_published_pnl_table_is_the_artifact(payload, page):
    for a in payload["core"]:
        present(page, f"{a['total_return_with_dividends'] * 100:.2f}%", "arm total return")
        present(page, f"{a['cagr_with_dividends'] * 100:.2f}%", "arm CAGR")
    bh = payload["buy_and_hold"]
    present(page, f"{bh['total_return_with_dividends'] * 100:.2f}%", "B&H total return")
    present(page, f"{bh['cagr_with_dividends'] * 100:.2f}%", "B&H CAGR")


def test_no_cell_survives_under_either_reading_of_hurdle_d(payload):
    """The verdict does not move, which is what makes this a disclosure rather than
    a goalpost being shifted after the fact."""
    v = payload["verdict"]
    assert v["survivors"] == []
    assert v["survivors_under_pnl_reading"] == []
