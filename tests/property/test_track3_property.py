"""Property tests for `validation/track3.py` (D605).

Conventions per D78 (derandomized hypothesis; seeding owned by the library rather than a
hand-rolled seed parameter) as amended by D537 (`derandomize=True` fixes the seed but NOT the
examples drawn -- since hypothesis 6.156.6 the constant pool is harvested from `sys.modules` at
test time, so a failure here reproduces within a run but the example set is not byte-stable
between a full-suite run and a single-file run; reproduce a failure with the whole suite).
`max_examples=40` and `deadline=None` keep the file inside the default gate.

WHAT IS WORTH A PROPERTY HERE. The hand-worked numbers are pinned by
`tests/golden/test_track3_ledger.hand.txt` and the closed cases by `tests/unit/test_track3.py`.
What no finite set of examples covers is the SHAPE of the three failures this module exists to
prevent:

  * **AN INVERTED SIGN.** D280 was inverted by a sign asserted in prose. The property is
    algebraic and holds at every price: reading the same fill as the opposite side negates the
    shortfall, an exit negates it again, and the sign is positive exactly when the fill was
    worse for the side.
  * **A LOG THAT DOES NOT ROUND TRIP.** A fill price that changes by one bit between the write
    and the read is a slippage measurement of the CSV writer. Quantified over prices,
    quantities, timestamps and the optional exit.
  * **A DECISION THAT DEPENDS ON THE UNIT.** "Mean net return per trade" has no declared unit
    in the deposit, so `t`, `futility()` and `efficacy()` must be invariant to a positive
    rescale of every return -- otherwise the verdict would depend on whether the model reports
    in points, ticks or dollars.

No fixture is read, no strategy return is computed, and every price below is drawn from a
synthetic range around 5000. No real fill exists.
"""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import pytest
from hypothesis import assume, given, settings, strategies as st

from backtest_framework.instruments.future import Future
from backtest_framework.validation.track3 import (
    Track3Error,
    TradeLog,
    TradeRow,
    TrialCounter,
    cost_review,
    exit_shortfall_ticks,
    latency_bars,
    latency_report,
    quantile_nearest_rank,
    shortfall_ticks,
    shortfall_usd,
)

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)

MES = Future(root="MES", tick_points=0.25, usd_per_point=5.0, tick_usd=1.25)
T0 = dt.datetime(2026, 10, 1, 14, 30)

# Text fields are read back STRIPPED, inheriting `d364_slippage.read_log`'s behaviour, so the
# round-trip property quantifies over already-stripped text. That is a real (small) lossiness
# and it is named here rather than hidden behind a narrower strategy.
TEXT = st.text(
    alphabet=st.characters(blacklist_categories=("Cc", "Cs", "Zl", "Zp"), blacklist_characters=" "),
    min_size=1,
    max_size=12,
)
PRICES = st.floats(min_value=4000.0, max_value=6000.0, allow_nan=False, allow_infinity=False)
TICKS = st.integers(min_value=-40, max_value=40)
QTY = st.integers(min_value=1, max_value=20)
SIDES = st.sampled_from(["long", "short"])
OFFSETS = st.integers(min_value=0, max_value=3600)


def _row(**over: object) -> TradeRow:
    base: dict[str, object] = dict(
        trade_id="P1",
        model="prop",
        stage="A",
        frozen_sha256="0" * 64,
        root="MES",
        size_label="micro",
        side="long",
        qty=1,
        signal_ts=T0,
        model_fill_px=5000.0,
        order_sent_ts=T0 + dt.timedelta(seconds=10),
        fill_ts=T0 + dt.timedelta(seconds=60),
        fill_px=5000.25,
        simulated=False,
        venue="SYNTHETIC",
    )
    base.update(over)
    return TradeRow(**base)  # type: ignore[arg-type]


# ------------------------------------------------------------------- 1. the sign is algebra


@given(model_px=PRICES, ticks=TICKS, side=SIDES, qty=QTY)
@SETTINGS
def test_reading_the_same_fill_as_the_other_side_negates_the_shortfall(
    model_px: float, ticks: int, side: str, qty: int
) -> None:
    fill_px = model_px + ticks * MES.tick_points
    mine = _row(side=side, qty=qty, model_fill_px=model_px, fill_px=fill_px)
    other = _row(side="short" if side == "long" else "long", qty=qty,
                 model_fill_px=model_px, fill_px=fill_px)
    assert shortfall_ticks(mine, MES) == -shortfall_ticks(other, MES)
    assert shortfall_usd(mine, MES) == -shortfall_usd(other, MES)


@given(model_px=PRICES, ticks=TICKS, side=SIDES)
@SETTINGS
def test_positive_means_worse_for_the_side_at_every_price(
    model_px: float, ticks: int, side: str
) -> None:
    """The whole convention, stated as an inequality rather than as prose (D280)."""
    fill_px = model_px + ticks * MES.tick_points
    row = _row(side=side, model_fill_px=model_px, fill_px=fill_px)
    got = shortfall_ticks(row, MES)
    if side == "long":
        worse = fill_px > model_px  # a long paid up
    else:
        worse = fill_px < model_px  # a short sold down
    if fill_px == model_px:
        assert got == 0.0
    elif worse:
        assert got > 0.0
    else:
        assert got < 0.0


@given(model_px=PRICES, ticks=TICKS, side=SIDES)
@SETTINGS
def test_the_exit_negates_the_entry_rule_at_the_same_prices(
    model_px: float, ticks: int, side: str
) -> None:
    """An exit is the opposite trade, so the two rules differ by exactly a sign."""
    px = model_px + ticks * MES.tick_points
    entry = _row(side=side, model_fill_px=model_px, fill_px=px)
    closed = _row(
        side=side,
        model_fill_px=model_px,
        fill_px=px,
        exit_signal_ts=T0 + dt.timedelta(seconds=120),
        exit_fill_ts=T0 + dt.timedelta(seconds=180),
        exit_fill_px=px,
    )
    assert exit_shortfall_ticks(closed, MES, model_px) == -shortfall_ticks(entry, MES)


@given(model_px=PRICES, ticks=TICKS, side=SIDES, qty=QTY)
@SETTINGS
def test_the_dollars_are_the_ticks_times_the_tick_value_times_the_size(
    model_px: float, ticks: int, side: str, qty: int
) -> None:
    row = _row(side=side, qty=qty, model_fill_px=model_px,
               fill_px=model_px + ticks * MES.tick_points)
    assert shortfall_usd(row, MES) == shortfall_ticks(row, MES) * MES.tick_usd * qty


# ------------------------------------------------------------------ 2. the log round trip


@given(
    trade_id=TEXT,
    note=TEXT,
    venue=TEXT,
    side=SIDES,
    qty=QTY,
    model_px=PRICES,
    fill_px=PRICES,
    micros=st.integers(min_value=0, max_value=999_999),
    sent=OFFSETS,
    extra=OFFSETS,
    closed=st.booleans(),
    simulated=st.booleans(),
)
@SETTINGS
def test_a_row_survives_the_csv_exactly(
    tmp_path_factory: pytest.TempPathFactory,
    trade_id: str,
    note: str,
    venue: str,
    side: str,
    qty: int,
    model_px: float,
    fill_px: float,
    micros: int,
    sent: int,
    extra: int,
    closed: bool,
    simulated: bool,
) -> None:
    signal = T0.replace(microsecond=micros)
    sent_ts = signal + dt.timedelta(seconds=sent)
    fill_ts = sent_ts + dt.timedelta(seconds=extra)
    exit_kw: dict[str, object] = {}
    if closed:
        exit_kw = {
            "exit_signal_ts": fill_ts + dt.timedelta(seconds=1),
            "exit_fill_ts": fill_ts + dt.timedelta(seconds=2),
            "exit_fill_px": fill_px,
        }
    row = _row(
        trade_id=trade_id, note=note, venue=venue, side=side, qty=qty,
        model_fill_px=model_px, fill_px=fill_px, signal_ts=signal,
        order_sent_ts=sent_ts, fill_ts=fill_ts, simulated=simulated, **exit_kw,
    )
    path: Path = tmp_path_factory.mktemp("track3") / "p.csv"
    log = TradeLog(path)
    log.append(row)
    back = log.read()
    assert back == [row]
    assert b"\r\n" not in path.read_bytes()


# ------------------------------------------------------------------------- 3. latency


@given(seconds=st.integers(min_value=0, max_value=7200),
       bar=st.sampled_from([1.0, 15.0, 60.0, 300.0]))
@SETTINGS
def test_latency_scales_inversely_with_the_bar_length(seconds: int, bar: float) -> None:
    row = _row(order_sent_ts=T0, fill_ts=T0 + dt.timedelta(seconds=seconds))
    assert latency_bars(row, bar) * bar == pytest.approx(float(seconds), abs=1e-9)
    assert latency_bars(row, bar) >= 0.0


@given(
    seconds=st.lists(st.integers(min_value=0, max_value=1200), min_size=1, max_size=25),
    assumed=st.floats(min_value=0.5, max_value=12.0, allow_nan=False, allow_infinity=False),
)
@SETTINGS
def test_the_latency_report_is_ordered_and_its_share_counts_the_right_rows(
    seconds: list[int], assumed: float
) -> None:
    rows = [
        _row(trade_id=f"P{i}", order_sent_ts=T0, fill_ts=T0 + dt.timedelta(seconds=s))
        for i, s in enumerate(seconds)
    ]
    rep = latency_report(rows, 60.0, assumed_max=assumed)
    assert rep["min"] <= rep["p50"] <= rep["p95"] <= rep["max"]
    lat = list(rep["latency_bars"])
    assert rep["p50"] in lat and rep["p95"] in lat, "a nearest-rank quantile is a sample member"
    assert rep["n_beyond"] == sum(1 for x in lat if x > assumed)
    assert 0.0 <= rep["share_beyond_t0_plus_5"] <= 1.0
    assert rep["share_beyond_t0_plus_5"] == rep["n_beyond"] / rep["n"]


@given(
    values=st.lists(st.floats(min_value=-50.0, max_value=50.0, allow_nan=False,
                              allow_infinity=False), min_size=1, max_size=30),
    num=st.integers(min_value=1, max_value=20),
)
@SETTINGS
def test_a_nearest_rank_quantile_is_always_a_member_and_is_monotone(
    values: list[float], num: int
) -> None:
    got = quantile_nearest_rank(values, num, 20)
    assert got in values
    assert min(values) <= got <= max(values)
    if num < 20:
        assert quantile_nearest_rank(values, num, 20) <= quantile_nearest_rank(values, num + 1, 20)


# --------------------------------------------------------------- 4. the cost review


@given(
    ticks=st.lists(TICKS, min_size=1, max_size=20),
    assumption=st.floats(min_value=0.25, max_value=8.0, allow_nan=False, allow_infinity=False),
)
@SETTINGS
def test_the_ratio_and_the_flag_agree_with_their_own_definitions(
    ticks: list[int], assumption: float
) -> None:
    rows = [
        _row(trade_id=f"P{i}", model_fill_px=5000.0, fill_px=5000.0 + k * MES.tick_points)
        for i, k in enumerate(ticks)
    ]
    rev = cost_review(rows, MES, assumption, n=len(rows))
    assert rev.sufficient is True
    assert rev.mean_shortfall_ticks is not None and rev.ratio is not None
    assert rev.ratio * assumption == pytest.approx(rev.mean_shortfall_ticks, rel=1e-12, abs=1e-12)
    assert rev.exceeds_by_50pct == (rev.ratio > 1.5)


@given(have=st.integers(min_value=0, max_value=8), need=st.integers(min_value=1, max_value=60))
@SETTINGS
def test_too_few_rows_never_produce_a_verdict(have: int, need: int) -> None:
    rows = [_row(trade_id=f"P{i}") for i in range(have)]
    rev = cost_review(rows, MES, 2.0, n=need)
    if have < need:
        assert rev.sufficient is False
        assert rev.mean_shortfall_ticks is None
        assert rev.ratio is None
        assert rev.exceeds_by_50pct is None
        assert "INSUFFICIENT" in rev.action
    else:
        assert rev.sufficient is True
        assert rev.exceeds_by_50pct is not None


# ------------------------------------------------------------- 5. the counter's decisions


RETURNS = st.lists(
    st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    min_size=2,
    max_size=40,
)


@given(values=RETURNS, scale=st.floats(min_value=0.05, max_value=40.0, allow_nan=False,
                                       allow_infinity=False))
@SETTINGS
def test_t_and_both_decisions_are_invariant_to_a_positive_rescale(
    values: list[float], scale: float
) -> None:
    """The deposit never fixes a unit for "mean net return per trade", so a verdict that moved
    when the model switched from points to dollars would be a verdict about the unit."""
    plain = TrialCounter("p", target=len(values), looks=())
    scaled = TrialCounter("s", target=len(values), looks=())
    plain.extend(values)
    scaled.extend([v * scale for v in values])
    assume(plain.sd > 0.0)
    assume(scaled.sd > 0.0)
    assert scaled.t == pytest.approx(plain.t, rel=1e-9, abs=1e-9)
    assert (plain.mean < 0) == (scaled.mean < 0)
    # AWAY FROM THE BAR ONLY, and the exclusion is the finding rather than a convenience:
    # `efficacy()` compares `t >= 2.0` exactly, so a series whose true t IS 2 is decided by the
    # last bit. This property found one -- [0, d, d] has t = 2 algebraically for every d, and at
    # d = 0.0546875 it computes to 2.0 while d * 0.0546875 computes to 1.9999999999999998, one
    # ULP below. `tests/unit/test_track3.py::test_a_t_exactly_on_the_bar_is_decided_by_the_last_bit`
    # pins that pair; D605 records it. The threshold is the deposit's and is not softened here.
    if abs(plain.t - 2.0) > 1e-9 and abs(scaled.t - 2.0) > 1e-9:
        assert plain.efficacy() == scaled.efficacy()


@given(values=RETURNS)
@SETTINGS
def test_futility_is_true_only_at_a_look_and_only_with_both_conditions(
    values: list[float],
) -> None:
    counter = TrialCounter("p", target=len(values) + 5, looks=(len(values),))
    for i, v in enumerate(values, start=1):
        counter.add(v)
        if i < 2:
            continue
        if counter.sd == 0.0:
            continue
        verdict = counter.futility()
        if verdict:
            assert counter.n in counter.looks
            assert counter.mean < 0.0
            assert counter.t < -1.0
        elif counter.n in counter.looks:
            assert not (counter.mean < 0.0 and counter.t < -1.0)
        else:
            assert verdict is False


@given(values=RETURNS)
@SETTINGS
def test_efficacy_exists_at_exactly_one_sample_size(values: list[float]) -> None:
    target = len(values)
    counter = TrialCounter("p", target=target, looks=())
    counter.extend(values)
    assume(counter.sd > 0.0)
    assert counter.efficacy() == (counter.mean > 0.0 and counter.t >= 2.0)
    counter.add(values[-1])
    assume(counter.sd > 0.0)
    assert counter.efficacy() is False, "N = target + 1 is not the efficacy decision"


@given(values=RETURNS)
@SETTINGS
def test_the_counter_mean_and_sd_match_their_textbook_definitions(values: list[float]) -> None:
    counter = TrialCounter("p", target=len(values) + 1, looks=())
    counter.extend(values)
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    assert counter.mean == pytest.approx(mean, rel=1e-12, abs=1e-12)
    assert counter.sd == pytest.approx(math.sqrt(var), rel=1e-12, abs=1e-12)
    if counter.sd == 0.0:
        with pytest.raises(Track3Error):
            _ = counter.t
    else:
        assert counter.t == pytest.approx(mean * math.sqrt(n) / math.sqrt(var),
                                          rel=1e-9, abs=1e-9)
