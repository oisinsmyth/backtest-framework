"""Unit gates for the cost-frequency frontier (D160-D165).

The load-bearing claim of the whole study is that **frequency is the only variable**.
That claim rests on three pieces of arithmetic, and these tests are what make them
theorems rather than hopes:

1. resampling is EXACT OHLCV aggregation on 00:00-UTC-aligned buckets, and an
   incomplete bucket is impossible rather than merely unlikely;
2. the calendar-scaled walk-forward produces the SAME number of windows at every
   frequency, by construction;
3. `periods_per_year` moves in BOTH places it appears — the metrics layer and the
   inverse-vol sizing brick — or the run is refused.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research import breakout_intraday as bi
from backtest_framework.research.trade_diagnostics import TradeEpisode
from backtest_framework.simulator.fills import Bar

START = datetime(2025, 1, 1)


def hourly(n_hours: int, *, start: datetime = START, drop: set[int] = frozenset()):
    """A deterministic hourly series whose OHLC values encode their own index, so an
    aggregation error shows up as a wrong number rather than a plausible one."""
    bars, volumes = [], []
    for i in range(n_hours):
        if i in drop:
            continue
        base = 100.0 + i
        bars.append(
            TimestampedBar(
                timestamp=start + timedelta(hours=i),
                bar=Bar(open=base, high=base + 2.0, low=base - 3.0, close=base + 1.0),
            )
        )
        volumes.append(float(10 * (i + 1)))
    return bars, volumes


# --------------------------------------------------------------- the frequency ladder


def test_frequency_must_divide_a_utc_day():
    with pytest.raises(ValueError, match="does not divide a UTC day"):
        bi.Frequency("7h", 420)


def test_periods_per_year_is_365_times_bars_per_day():
    expected = {"1h": 8760.0, "2h": 4380.0, "4h": 2190.0, "6h": 1460.0, "12h": 730.0, "1d": 365.0}
    assert {f.name: f.periods_per_year for f in bi.STUDY_FREQUENCIES} == expected


# ------------------------------------------------------------------- the day census


def test_census_separates_complete_days_from_short_ones():
    bars, _ = hourly(72, drop={30})  # a hole on day 2
    census = bi.census_days(bars)
    assert census.complete == (date(2025, 1, 1), date(2025, 1, 3))
    assert census.incomplete == ((date(2025, 1, 2), 23),)
    assert census.expected_bars_per_day == 24


# -------------------------------------------------------------------- the resampler


def test_resample_is_exact_ohlcv_aggregation():
    bars, volumes = hourly(24)
    out, out_volumes, report = bi.resample(bars, volumes, 360, [date(2025, 1, 1)])  # 6h
    assert len(out) == 4
    assert [tb.timestamp.hour for tb in out] == [0, 6, 12, 18]
    first = out[0].bar
    assert first.open == bars[0].bar.open  # first open
    assert first.close == bars[5].bar.close  # last close
    assert first.high == max(b.bar.high for b in bars[:6])
    assert first.low == min(b.bar.low for b in bars[:6])
    assert out_volumes[0] == sum(volumes[:6])
    report.check()


def test_resample_buckets_are_anchored_to_midnight_utc():
    bars, volumes = hourly(48)
    out, _v, _r = bi.resample(bars, volumes, 720, [date(2025, 1, 1), date(2025, 1, 2)])  # 12h
    assert [tb.timestamp for tb in out] == [
        datetime(2025, 1, 1, 0),
        datetime(2025, 1, 1, 12),
        datetime(2025, 1, 2, 0),
        datetime(2025, 1, 2, 12),
    ]


def test_an_incomplete_bucket_raises_rather_than_emitting_a_short_bar():
    """The day-level drop policy makes this unreachable in the study — which is the
    point. Forcing the reachable path proves the guard is real, not decorative."""
    bars, volumes = hourly(24, drop={3})
    with pytest.raises(ValueError, match="incomplete .* bucket"):
        bi.resample(bars, volumes, 360, [date(2025, 1, 1)])


def test_resample_refuses_a_target_that_is_not_a_multiple_of_the_source():
    bars, volumes = hourly(24)
    with pytest.raises(ValueError, match="whole multiple"):
        bi.resample(bars, volumes, 90, [date(2025, 1, 1)])


def test_resample_to_1d_reproduces_a_hand_built_daily_bar_exactly():
    bars, volumes = hourly(48)
    out, out_volumes, _r = bi.resample(bars, volumes, 1440, [date(2025, 1, 1), date(2025, 1, 2)])
    for day_index, tb in enumerate(out):
        members = bars[day_index * 24 : (day_index + 1) * 24]
        assert tb.bar.open == members[0].bar.open
        assert tb.bar.close == members[-1].bar.close
        assert tb.bar.high == max(m.bar.high for m in members)
        assert tb.bar.low == min(m.bar.low for m in members)
        assert out_volumes[day_index] == pytest.approx(
            sum(volumes[day_index * 24 : (day_index + 1) * 24])
        )


def test_frequency_series_gives_every_rung_the_same_calendar():
    bars, volumes = hourly(24 * 10, drop={24 * 3 + 5})  # one hole on day 4
    series, census, reports = bi.frequency_series(bars, volumes)
    assert len(census.complete) == 9  # the holed day is dropped everywhere
    for freq in bi.STUDY_FREQUENCIES:
        out_bars, _ = series[freq.name]
        assert len(out_bars) == 9 * freq.bars_per_day
        assert {tb.timestamp.date() for tb in out_bars} == set(census.complete)
        reports[freq.name].check()


# ------------------------------------------------- the walk-forward equality theorem


def test_window_count_does_not_depend_on_the_frequency():
    """`window_count` takes no frequency argument at all, and that independence is what
    the calendar-scaled walk-forward buys. Re-derived here from the bar-level sizes so
    the theorem is checked against the arithmetic the harness actually runs."""
    for n_days in (315, 316, 378, 441, 723, 724):
        expected = bi.window_count(n_days)
        for freq in bi.STUDY_FREQUENCIES:
            study = bi.study_config(freq)
            n_bars = n_days * freq.bars_per_day
            count, start = 0, 0
            while start + study.train_size + study.test_size <= n_bars:
                count += 1
                start += study.step
            assert count == expected, f"{freq.name} at {n_days} days"


def test_walk_forward_sizes_are_equal_calendar_duration():
    for freq in bi.STUDY_FREQUENCIES:
        study = bi.study_config(freq)
        assert study.train_size / freq.bars_per_day == bi.TRAIN_DAYS
        assert study.test_size / freq.bars_per_day == bi.TEST_DAYS
        assert study.step / freq.bars_per_day == bi.STEP_DAYS
        assert study.whipsaw_bars / freq.bars_per_day == bi.WHIPSAW_DAYS
        assert study.fill_timing == "next_open"


# ------------------------------------------------------- periods_per_year, both places


def test_variant_and_study_agree_on_periods_per_year_at_every_frequency():
    for freq in bi.STUDY_FREQUENCIES:
        study = bi.study_config(freq)
        for design in bi.DESIGNS:
            variant = bi.variant_for(design, freq)
            bi.assert_periods_per_year_agree(variant, study)  # must not raise
            assert variant.fixed_config["weight_source"]["periods_per_year"] == freq.periods_per_year
            assert study.periods_per_year == freq.periods_per_year


def test_a_mismatched_periods_per_year_is_refused():
    freq = bi.Frequency("1h", 60)
    study = bi.study_config(freq)
    variant = bi.variant_for(bi.DESIGN_A, freq)
    broken = dict(variant.fixed_config)
    broken["weight_source"] = {**broken["weight_source"], "periods_per_year": 365.0}
    with pytest.raises(ValueError, match="annualised on one"):
        bi.assert_periods_per_year_agree(
            bi.Variant("broken", "frequency", fixed_config=broken), study
        )


# ------------------------------------------------------------------------- designs


def test_design_a_holds_the_calendar_horizon_and_design_b_holds_the_bar_count():
    for freq in bi.STUDY_FREQUENCIES:
        a_entry, a_exit, a_vol = bi.DESIGN_A.windows(freq)
        b_entry, b_exit, b_vol = bi.DESIGN_B.windows(freq)
        assert (a_entry / freq.bars_per_day, a_exit / freq.bars_per_day) == (40, 10)
        assert (b_entry, b_exit, b_vol) == (40, 10, 20)
        assert a_vol / freq.bars_per_day == 20


def test_the_two_designs_coincide_exactly_at_daily():
    daily = bi.STUDY_FREQUENCIES[-1]
    assert daily.name == "1d"
    assert bi.variant_for(bi.DESIGN_A, daily).fixed_config == (
        bi.variant_for(bi.DESIGN_B, daily).fixed_config
    )


def test_design_b_at_1h_is_a_forty_hour_breakout():
    n_entry, n_exit, _ = bi.DESIGN_B.windows(bi.FREQ_1H)
    assert (n_entry / 24, n_exit / 24) == (40 / 24, 10 / 24)
    n_entry_a, _n_exit_a, _ = bi.DESIGN_A.windows(bi.FREQ_1H)
    assert n_entry_a == 960


# ------------------------------------------------------------ calendar-unit diagnostics


def episode(entry: datetime, exit_: datetime | None) -> TradeEpisode:
    return TradeEpisode(
        entry_timestamp=entry,
        exit_timestamp=exit_,
        entry_index=0,
        exit_index=None if exit_ is None else 1,
        bars_held=1,
        entry_price=100.0,
        exit_price=None if exit_ is None else 101.0,
        gross_pnl=1.0,
        costs=0.0,
        rebalance_costs=0.0,
        traded_notional=200.0,
        n_fills=2,
        mfe=0.01,
        mae=-0.01,
    )


def test_holding_periods_are_calendar_days_and_exclude_open_episodes():
    episodes = [
        episode(datetime(2025, 1, 1), datetime(2025, 1, 3)),  # 2 days
        episode(datetime(2025, 1, 5), datetime(2025, 1, 5, 6)),  # 6 hours
        episode(datetime(2025, 2, 1), None),  # still open
    ]
    held = bi.holding_periods_days(episodes)
    assert held == [2.0, 0.25]


def test_daily_equity_takes_the_last_nav_of_each_utc_day():
    curve = [
        (datetime(2025, 1, 1, 0), 100.0),
        (datetime(2025, 1, 1, 12), 101.0),
        (datetime(2025, 1, 1, 23), 102.0),
        (datetime(2025, 1, 2, 11), 103.0),
    ]
    assert [nav for _ts, nav in bi.daily_equity(curve)] == [102.0, 103.0]
    assert bi.daily_returns(curve) == pytest.approx([103.0 / 102.0 - 1.0])


def test_daily_returns_have_the_same_length_at_every_frequency():
    """The DSR pool's units contract (D164) needs one T for the whole pool. Two curves
    over the same calendar collapse to the same number of daily returns however many
    bars each contained underneath."""
    hourly_curve = [(START + timedelta(hours=i), 100.0 + i) for i in range(24 * 5)]
    daily_curve = [(START + timedelta(days=i), 100.0 + i) for i in range(5)]
    assert len(bi.daily_returns(hourly_curve)) == len(bi.daily_returns(daily_curve)) == 4


# ----------------------------------------------------------------------- rendering


def test_measurement_table_prints_n_a_rather_than_a_fabricated_hold():
    m = bi.TurnoverMeasurement(
        symbol="BTC-USD",
        frequency=bi.FREQ_1H,
        tier=bi.DEFAULT_TIERS[-1],
        n_bars=100,
        n_days=4.0,
        n_closed_trades=0,
        n_open_at_end=0,
        traded_notional=0.0,
        total_costs=0.0,
        annual_turnover=0.0,
        fee_drag_annual=0.0,
        median_hold_days=float("nan"),
        whipsaw_rate_3d=float("nan"),
        gross_pnl=0.0,
    )
    rendered = bi.render_measurement_table([m])
    assert "| n/a | n/a |" in rendered
    assert "nan" not in rendered


def test_the_crossover_rule_and_the_reference_edge_are_written_down():
    assert "COARSEST" in bi.CROSSOVER_RULE
    assert set(bi.REFERENCE_GROSS_SHARPE) == {"BTC-USD", "ETH-USD"}
    # Imported from BREAKOUT_RESULTS.md's maker_0bp plateau_40_10 rows, not re-measured.
    assert bi.REFERENCE_GROSS_SHARPE["BTC-USD"] == pytest.approx(1.27)
    assert bi.REFERENCE_GROSS_SHARPE["ETH-USD"] == pytest.approx(0.84)
