"""Golden-master ledger for the Track 3 logging layer (D605).

Every case's arithmetic is worked by hand in `test_track3_ledger.hand.txt`, next to this file,
per D39 and CONTRIBUTING.md's rule that the ground truth is produced by a calculator that never
imports this codebase. The six-trade log is defined once there and transcribed here; if the two
ever disagree, the hand file is right and this file is wrong.

An implementation shortfall is money -- it is the whole difference between a backtest's fill and
a real one -- so it belongs in `tests/golden/`.

EVERY NUMBER BELOW IS SYNTHETIC. No order has been sent from this repository, no broker adapter
exists and no real fill has ever been recorded.
"""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import pytest

from backtest_framework.instruments.future import Future
from backtest_framework.validation.track3 import (
    COST_REVIEW_ACTION,
    Track3Error,
    TradeLog,
    TradeRow,
    TrialCounter,
    cost_review,
    exit_shortfall_ticks,
    exit_shortfall_usd,
    latency_bars,
    latency_report,
    shortfall_ticks,
    shortfall_usd,
)

# Hand file, "THE HAND LOG".
MES = Future(root="MES", tick_points=0.25, usd_per_point=5.0, tick_usd=1.25)
DAY = dt.date(2026, 10, 1)


def _ts(hh: int, mm: int, ss: int = 0) -> dt.datetime:
    return dt.datetime(DAY.year, DAY.month, DAY.day, hh, mm, ss)


def _row(
    trade_id: str,
    side: str,
    qty: int,
    signal: tuple[int, int, int],
    sent: tuple[int, int, int],
    fill: tuple[int, int, int],
    model_fill_px: float,
    fill_px: float,
    simulated: bool = False,
    exit_signal: tuple[int, int, int] | None = None,
    exit_fill: tuple[int, int, int] | None = None,
    exit_fill_px: float | None = None,
) -> TradeRow:
    return TradeRow(
        trade_id=trade_id,
        model="mhand",
        stage="A",
        frozen_sha256="0" * 64,
        root="MES",
        size_label="micro",
        side=side,  # type: ignore[arg-type]
        qty=qty,
        signal_ts=_ts(*signal),
        model_fill_px=model_fill_px,
        order_sent_ts=_ts(*sent),
        fill_ts=_ts(*fill),
        fill_px=fill_px,
        exit_signal_ts=_ts(*exit_signal) if exit_signal else None,
        exit_fill_ts=_ts(*exit_fill) if exit_fill else None,
        exit_fill_px=exit_fill_px,
        simulated=simulated,
        venue="SYNTHETIC",
    )


T1 = _row("T1", "long", 1, (14, 30, 0), (14, 30, 10), (14, 31, 0), 5000.00, 5000.25,
          exit_signal=(14, 45, 0), exit_fill=(14, 46, 0), exit_fill_px=5005.00)
T2 = _row("T2", "long", 2, (14, 40, 0), (14, 40, 30), (14, 42, 0), 5010.00, 5010.50,
          exit_signal=(14, 55, 0), exit_fill=(14, 56, 0), exit_fill_px=5014.00)
T3 = _row("T3", "long", 1, (14, 50, 0), (14, 50, 5), (14, 50, 30), 4990.00, 4989.75)
T4 = _row("T4", "short", 1, (15, 0, 0), (15, 0, 10), (15, 6, 0), 5020.00, 5019.50,
          exit_signal=(15, 20, 0), exit_fill=(15, 21, 0), exit_fill_px=5016.25)
T5 = _row("T5", "short", 3, (15, 10, 0), (15, 10, 15), (15, 17, 0), 5030.00, 5029.25)
T6 = _row("T6", "short", 1, (15, 20, 0), (15, 20, 20), (15, 28, 0), 5040.00, 5040.25,
          simulated=True)
HAND_LOG = (T1, T2, T3, T4, T5, T6)

BAR_SECONDS = 60.0


# ------------------------------------------------------- 1. implementation shortfall


def test_ledger_35_shortfall_sign_long_and_short_hand_ticks() -> None:
    """Ledger unit test 35, hand file section 1: the sign on BOTH sides.

    "a long filled 2 ticks above the model price records +2 ticks of shortfall; a short
    filled 2 ticks below records +2" -- T2 and T4.
    """
    assert shortfall_ticks(T2, MES) == 2.0
    assert shortfall_ticks(T4, MES) == 2.0
    assert shortfall_ticks(T1, MES) == 1.0
    assert shortfall_ticks(T3, MES) == -1.0
    assert shortfall_ticks(T5, MES) == 3.0
    assert shortfall_ticks(T6, MES) == -1.0


def test_ledger_35_shortfall_sign_long_and_short_hand_usd() -> None:
    """Hand file section 1, the dollars column -- the size lives here, not in the ticks."""
    assert shortfall_usd(T1, MES) == 1.25
    assert shortfall_usd(T2, MES) == 5.00
    assert shortfall_usd(T3, MES) == -1.25
    assert shortfall_usd(T4, MES) == 2.50
    assert shortfall_usd(T5, MES) == 11.25
    assert shortfall_usd(T6, MES) == -1.25
    assert sum(shortfall_usd(r, MES) for r in HAND_LOG) == 17.50
    assert sum(shortfall_ticks(r, MES) for r in HAND_LOG) == 6.0


def test_exit_shortfall_inverts_the_sign() -> None:
    """Hand file section 2. An exit is the opposite trade."""
    assert exit_shortfall_ticks(T1, MES, 5005.25) == 1.0
    assert exit_shortfall_usd(T1, MES, 5005.25) == 1.25
    assert exit_shortfall_ticks(T2, MES, 5014.00) == 0.0
    assert exit_shortfall_usd(T2, MES, 5014.00) == 0.0
    assert exit_shortfall_ticks(T4, MES, 5016.00) == 1.0
    assert exit_shortfall_usd(T4, MES, 5016.00) == 1.25
    assert exit_shortfall_ticks(T4, MES, 5016.50) == -1.0
    assert exit_shortfall_usd(T4, MES, 5016.50) == -1.25


def test_exit_shortfall_of_an_open_trade_raises() -> None:
    """Hand file section 2: T5 is open, so it has no exit shortfall -- not a zero one."""
    with pytest.raises(Track3Error, match="no exit fill recorded"):
        exit_shortfall_ticks(T5, MES, 5029.00)


# ------------------------------------------------------------------------ 2. latency


def test_latency_bars_per_row() -> None:
    """Hand file section 3."""
    assert [latency_bars(r, BAR_SECONDS) for r in HAND_LOG] == [1.0, 2.0, 0.5, 6.0, 7.0, 8.0]


def test_latency_report_distribution_and_share_beyond_t0_plus_5() -> None:
    """Hand file section 3: nearest-rank quantiles, and 3 of 6 fills beyond t0+5."""
    rep = latency_report(HAND_LOG, BAR_SECONDS)
    assert rep["n"] == 6
    assert rep["min"] == 0.5
    assert rep["p50"] == 2.0
    assert rep["p95"] == 8.0
    assert rep["max"] == 8.0
    assert rep["n_beyond"] == 3
    assert rep["share_beyond_t0_plus_5"] == 0.5
    assert rep["assumed_max"] == 5.0


def test_latency_report_on_an_empty_log_raises() -> None:
    """Hand file section 3: the share of an empty sample is not 0.0."""
    with pytest.raises(Track3Error, match="empty log"):
        latency_report([], BAR_SECONDS)


# -------------------------------------------------------------------- 3. cost review


def test_cost_review_ratio_and_the_fifty_percent_trigger() -> None:
    """Hand file section 4, cases A and B. mean = 1.0 tick over the six hand trades."""
    case_a = cost_review(HAND_LOG, MES, 0.5, n=6)
    assert case_a.sufficient is True
    assert case_a.n == 6
    assert case_a.mean_shortfall_ticks == 1.0
    assert case_a.assumption_ticks == 0.5
    assert case_a.ratio == 2.0
    assert case_a.exceeds_by_50pct is True
    assert case_a.action == COST_REVIEW_ACTION

    case_b = cost_review(HAND_LOG, MES, 2.0, n=6)
    assert case_b.mean_shortfall_ticks == 1.0
    assert case_b.ratio == 0.5
    assert case_b.exceeds_by_50pct is False
    assert case_b.action != COST_REVIEW_ACTION


def test_cost_review_below_fifty_trades_is_insufficient_never_a_verdict() -> None:
    """Hand file section 4, case C. Six trades against the deposit's n = 50."""
    case_c = cost_review(HAND_LOG, MES, 0.5)
    assert case_c.sufficient is False
    assert case_c.n == 6
    assert case_c.required_n == 50
    assert case_c.mean_shortfall_ticks is None
    assert case_c.ratio is None
    assert case_c.exceeds_by_50pct is None
    assert "INSUFFICIENT: 6 of 50" in case_c.action


# ---------------------------------------------------------- 4. the log round trip


def test_the_hand_log_round_trips_through_the_csv_exactly(tmp_path: Path) -> None:
    """Written and read back: the same six rows, bit for bit, LF-terminated."""
    path = tmp_path / "mhand_trades.csv"
    log = TradeLog(path)
    for row in HAND_LOG:
        log.append(row)
    assert log.read() == list(HAND_LOG)
    raw = path.read_bytes()
    assert b"\r\n" not in raw, "the log is LF on every platform (D550)"
    assert raw.decode("utf-8").splitlines()[0].startswith("trade_id,model,stage,frozen_sha256")
    assert len(raw.decode("utf-8").splitlines()) == 7


def test_the_log_refuses_a_duplicate_and_an_out_of_order_row(tmp_path: Path) -> None:
    path = tmp_path / "mhand_trades.csv"
    log = TradeLog(path)
    log.append(T1)
    with pytest.raises(Track3Error, match="already in"):
        log.append(T1)
    backwards = _row("T7", "long", 1, (14, 30, 0), (14, 29, 0), (14, 31, 0), 5000.0, 5000.0)
    with pytest.raises(Track3Error, match="precedes signal_ts"):
        log.append(backwards)
    unfilled = _row("T8", "long", 1, (14, 30, 0), (14, 31, 0), (14, 30, 30), 5000.0, 5000.0)
    with pytest.raises(Track3Error, match="precedes order_sent_ts"):
        log.append(unfilled)


# ------------------------------------------------- 5. the counter: ledger unit test 36


def _series(m: float, d: float, n: int) -> list[float]:
    """Hand file section 5's construction: one outlier at m - (n-1)d, then (n-1) at m + d.

    mean = m and sd = d * sqrt(n) EXACTLY, so t = m / d. The outlier goes FIRST so that the
    n - 1 prefix is itself a usable sample (the N = 99 case).
    """
    return [m - (n - 1) * d] + [m + d] * (n - 1)


def test_ledger_36_futility_stops_at_n100_only_when_mean_negative_and_t_below_minus_one() -> None:
    """Ledger unit test 36, hand file section 5, cases A, B and C."""
    a = TrialCounter("hand-A")
    a.extend(_series(-0.125, 0.0625, 100))
    assert a.n == 100
    assert a.mean == -0.125
    assert a.sd == 0.625
    assert a.t == -2.0
    assert a.futility() is True

    b = TrialCounter("hand-B")
    b.extend(_series(-0.0625, 0.25, 100))
    assert b.mean == -0.0625
    assert b.sd == 2.5
    assert b.t == -0.25
    assert b.futility() is False

    c = TrialCounter("hand-C")
    c.extend(_series(0.125, 0.0625, 100))
    assert c.mean == 0.125
    assert c.sd == 0.625
    assert c.t == 2.0
    assert c.futility() is False


def test_ledger_36_n99_is_not_a_look_even_though_both_conditions_hold() -> None:
    """Hand file section 5, case A's n = 99 sub-case: mean < 0, t < -1, verdict still False."""
    counter = TrialCounter("hand-A99")
    counter.extend(_series(-0.125, 0.0625, 100)[:99])
    assert counter.n == 99
    assert counter.mean < 0.0
    assert counter.t < -1.0
    assert counter.t == pytest.approx(-1.99, rel=1e-12)
    assert counter.at_look() is False
    assert counter.futility() is False


def test_the_second_look_at_n200_fires_on_the_same_rule() -> None:
    """Both looks, not just the first: `looks=(100, 200)` is a tuple and both are read."""
    counter = TrialCounter("hand-A200")
    counter.extend(_series(-0.125, 0.0625, 100))
    assert counter.futility() is True
    counter.extend(_series(-0.125, 0.0625, 100))
    assert counter.n == 200
    assert counter.mean == -0.125
    assert counter.futility() is True


# ------------------------------------------------------------ 6. the efficacy decision


def test_efficacy_only_at_n300_with_mean_positive_and_t_at_least_two() -> None:
    """Hand file section 6. mean is exact; t is 2.5 up to sqrt(300)'s rounding."""
    short = TrialCounter("hand-E299", target=300)
    short.extend(_series(0.15625, 0.0625, 299))
    assert short.n == 299
    assert short.efficacy() is False, "the decision exists at exactly N = 300"

    counter = TrialCounter("hand-E", target=300)
    counter.extend(_series(0.15625, 0.0625, 300))
    assert counter.n == 300
    assert counter.mean == 0.15625
    assert counter.sd == pytest.approx(0.0625 * math.sqrt(300), rel=1e-12)
    assert counter.t == pytest.approx(2.5, rel=1e-12)
    assert counter.efficacy() is True
    counter.add(0.21875)
    assert counter.n == 301
    assert counter.efficacy() is False


def test_index_unit_28_january_trades_never_count_as_efficacy_evidence() -> None:
    """INDEX_REWEIGHT_FLOW_PREREG.md unit test 28, hand file section 6.

    The same winning series, with the flag off, is never efficacy -- and futility is
    unaffected, because a January book can still be shown to be losing.
    """
    index = TrialCounter(
        "index-R1",
        target=300,
        counts_as_efficacy=False,
        efficacy_reason=(
            "INDEX_REWEIGHT_FLOW_PREREG.md 8B: about 5 execution days a year, so Track 3 "
            "January trades are a fill, latency and cost check, never independent proof."
        ),
    )
    index.extend(_series(0.15625, 0.0625, 300))
    assert index.n == 300
    assert index.mean == 0.15625
    assert index.t == pytest.approx(2.5, rel=1e-12)
    assert index.efficacy() is False
    assert "never independent proof" in index.efficacy_reason

    losing = TrialCounter(
        "index-R1-losing",
        counts_as_efficacy=False,
        efficacy_reason=index.efficacy_reason,
    )
    losing.extend(_series(-0.125, 0.0625, 100))
    assert losing.futility() is True
