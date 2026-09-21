"""Unit tests for `validation/track3.py` (D605) -- the closed cases and every guard.

The hand-worked arithmetic lives in `tests/golden/test_track3_ledger.py` and its `.hand.txt`;
the shapes that no finite example set covers live in `tests/property/test_track3_property.py`.
What is here is the behaviour of the API at its edges: what raises, what the strict reader says
when a cell is wrong, what the counter does at a restart, and how the cost assumption reads off
the real cost table.

D48: every guard raises, and each raise is asserted on the case that breaks THE THING THE
GUARD READS, never on a nearby one.

EVERY NUMBER IS SYNTHETIC. No broker adapter exists, no order has been sent, and no real fill
has ever been recorded; `data/track3/` holds a schema and no trade file.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from backtest_framework.costs.futures_bricks import FuturesCostError
from backtest_framework.instruments.future import Future
from backtest_framework.validation.frozen import freeze
from backtest_framework.validation.power import TRACK3_TARGET_N
from backtest_framework.validation.track3 import (
    ADVERSE_TICKS_PER_ENTRY,
    COST_REVIEW_N,
    EXCEEDS_RATIO,
    FIELDS,
    SIDE_SIGN,
    Track3Error,
    Track3LogError,
    TradeLog,
    TradeRow,
    TrialCounter,
    cost_assumption_ticks,
    cost_review,
    latency_bars,
    latency_report,
    quantile_nearest_rank,
    shortfall_ticks,
)

MES = Future(root="MES", tick_points=0.25, usd_per_point=5.0, tick_usd=1.25)
T0 = dt.datetime(2026, 10, 1, 14, 30)


def make_row(**over: object) -> TradeRow:
    base: dict[str, object] = dict(
        trade_id="U1",
        model="unit",
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


# --------------------------------------------------------------------- the row's guards


def test_side_sign_is_d364s_convention() -> None:
    assert SIDE_SIGN == {"long": 1.0, "short": -1.0}
    assert make_row(side="long").side_sign == 1.0
    assert make_row(side="short").side_sign == -1.0


@pytest.mark.parametrize("name", ["trade_id", "model", "stage", "frozen_sha256", "root",
                                  "size_label", "venue"])
def test_a_blank_required_text_field_raises(name: str) -> None:
    with pytest.raises(Track3Error, match=f"TradeRow.{name}"):
        make_row(**{name: "   "})


def test_an_unknown_side_raises() -> None:
    with pytest.raises(Track3Error, match="must be 'long' or 'short'"):
        make_row(side="buy")


@pytest.mark.parametrize("qty", [0, -1, 1.5, True])
def test_qty_must_be_a_positive_whole_number_of_contracts(qty: object) -> None:
    with pytest.raises(Track3Error, match="positive whole number"):
        make_row(qty=qty)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_a_non_finite_price_raises(bad: float) -> None:
    with pytest.raises(Track3Error, match="finite"):
        make_row(fill_px=bad)
    with pytest.raises(Track3Error, match="finite"):
        make_row(model_fill_px=bad)


def test_simulated_must_be_a_bool_because_d24_is_a_flag() -> None:
    with pytest.raises(Track3Error, match="must be a bool"):
        make_row(simulated="yes")


def test_a_half_recorded_exit_raises_and_a_complete_one_does_not() -> None:
    with pytest.raises(Track3Error, match="half-recorded"):
        make_row(exit_fill_px=5005.0)
    with pytest.raises(Track3Error, match="half-recorded"):
        make_row(exit_signal_ts=T0 + dt.timedelta(minutes=5),
                 exit_fill_ts=T0 + dt.timedelta(minutes=6))
    closed = make_row(
        exit_signal_ts=T0 + dt.timedelta(minutes=5),
        exit_fill_ts=T0 + dt.timedelta(minutes=6),
        exit_fill_px=5005.0,
    )
    assert closed.is_closed is True
    assert make_row().is_closed is False


def test_mixing_aware_and_naive_timestamps_raises_at_the_row() -> None:
    with pytest.raises(Track3Error, match="mixes aware and naive"):
        make_row(fill_ts=dt.datetime(2026, 10, 1, 14, 31, tzinfo=dt.UTC))


def test_an_all_aware_row_is_accepted_and_its_latency_is_the_same_number() -> None:
    aware = make_row(
        signal_ts=dt.datetime(2026, 10, 1, 18, 30, tzinfo=dt.UTC),
        order_sent_ts=dt.datetime(2026, 10, 1, 18, 30, 10, tzinfo=dt.UTC),
        fill_ts=dt.datetime(2026, 10, 1, 18, 31, tzinfo=dt.UTC),
    )
    assert latency_bars(aware, 60.0) == latency_bars(make_row(), 60.0) == 1.0


def test_ordering_fault_names_the_first_violation_and_never_raises() -> None:
    assert make_row().ordering_fault() is None
    early = make_row(order_sent_ts=T0 - dt.timedelta(seconds=1))
    assert "precedes signal_ts" in (early.ordering_fault() or "")
    backwards = make_row(fill_ts=T0 + dt.timedelta(seconds=5))
    assert "precedes order_sent_ts" in (backwards.ordering_fault() or "")
    before_entry = make_row(
        exit_signal_ts=T0 + dt.timedelta(seconds=30),
        exit_fill_ts=T0 + dt.timedelta(seconds=90),
        exit_fill_px=5005.0,
    )
    assert "not yet held" in (before_entry.ordering_fault() or "")
    exit_backwards = make_row(
        exit_signal_ts=T0 + dt.timedelta(seconds=120),
        exit_fill_ts=T0 + dt.timedelta(seconds=90),
        exit_fill_px=5005.0,
    )
    assert "precedes exit_signal_ts" in (exit_backwards.ordering_fault() or "")


# --------------------------------------------------------------------------- the log


def test_the_header_is_written_once_and_the_file_is_append_only(tmp_path: Path) -> None:
    log = TradeLog(tmp_path / "u.csv")
    log.append(make_row(trade_id="A"))
    first = (tmp_path / "u.csv").read_text(encoding="utf-8")
    log.append(make_row(trade_id="B"))
    second = (tmp_path / "u.csv").read_text(encoding="utf-8")
    assert second.startswith(first), "an append must not rewrite what is already there"
    assert second.count(FIELDS[0]) == 1, "the header is written once"
    assert [r.trade_id for r in log.read()] == ["A", "B"]


def test_appending_a_non_row_raises(tmp_path: Path) -> None:
    with pytest.raises(Track3Error, match="takes a TradeRow"):
        TradeLog(tmp_path / "u.csv").append({"trade_id": "A"})  # type: ignore[arg-type]


def test_reading_an_absent_log_raises_rather_than_returning_no_trades(tmp_path: Path) -> None:
    with pytest.raises(Track3LogError, match="no such log"):
        TradeLog(tmp_path / "missing.csv").read()


def test_an_empty_file_and_a_wrong_header_both_raise(tmp_path: Path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8", newline="\n")
    with pytest.raises(Track3LogError, match="empty"):
        TradeLog(empty).read()
    wrong = tmp_path / "wrong.csv"
    wrong.write_text("trade_id,model\n", encoding="utf-8", newline="\n")
    with pytest.raises(Track3LogError, match="header is"):
        TradeLog(wrong).read()


def test_a_header_only_log_reads_as_no_rows(tmp_path: Path) -> None:
    path = tmp_path / "u.csv"
    path.write_text(",".join(FIELDS) + "\n", encoding="utf-8", newline="\n")
    assert TradeLog(path).read() == []


@pytest.mark.parametrize(
    ("field", "value", "fragment"),
    [
        ("qty", "two", "is not a whole number"),
        ("side", "buy", "is not 'long' or 'short'"),
        ("simulated", "yes", "is not 'True' or 'False'"),
        ("fill_px", "abc", "is not a number"),
        ("fill_px", "nan", "is not finite"),
        ("signal_ts", "yesterday", "is not an ISO-8601 datetime"),
        ("model", "", "is required and is blank"),
    ],
)
def test_a_malformed_cell_raises_naming_the_line_and_the_field(
    tmp_path: Path, field: str, value: str, fragment: str
) -> None:
    path = tmp_path / "u.csv"
    TradeLog(path).append(make_row())
    lines = path.read_text(encoding="utf-8").splitlines()
    cells = lines[1].split(",")
    cells[FIELDS.index(field)] = value
    path.write_text("\n".join([lines[0], ",".join(cells)]) + "\n",
                    encoding="utf-8", newline="\n")
    with pytest.raises(Track3LogError) as exc:
        TradeLog(path).read()
    assert "line 2" in str(exc.value)
    assert field in str(exc.value)
    assert fragment in str(exc.value)


def test_a_short_row_and_a_half_recorded_exit_raise_on_read(tmp_path: Path) -> None:
    path = tmp_path / "u.csv"
    TradeLog(path).append(make_row())
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([lines[0], "a,b,c"]) + "\n", encoding="utf-8", newline="\n")
    with pytest.raises(Track3LogError, match="3 fields, expected"):
        TradeLog(path).read()

    cells = lines[1].split(",")
    cells[FIELDS.index("exit_fill_px")] = "5005.0"
    path.write_text("\n".join([lines[0], ",".join(cells)]) + "\n",
                    encoding="utf-8", newline="\n")
    with pytest.raises(Track3LogError, match="half-recorded"):
        TradeLog(path).read()


def test_a_hand_reordered_row_raises_on_read_not_only_on_append(tmp_path: Path) -> None:
    path = tmp_path / "u.csv"
    TradeLog(path).append(make_row())
    lines = path.read_text(encoding="utf-8").splitlines()
    cells = lines[1].split(",")
    cells[FIELDS.index("fill_ts")] = T0.isoformat()
    cells[FIELDS.index("order_sent_ts")] = (T0 + dt.timedelta(seconds=30)).isoformat()
    path.write_text("\n".join([lines[0], ",".join(cells)]) + "\n",
                    encoding="utf-8", newline="\n")
    with pytest.raises(Track3LogError, match="precedes order_sent_ts"):
        TradeLog(path).read()


def test_blank_lines_are_skipped(tmp_path: Path) -> None:
    path = tmp_path / "u.csv"
    TradeLog(path).append(make_row())
    path.write_text(path.read_text(encoding="utf-8") + "\n\n", encoding="utf-8", newline="\n")
    assert len(TradeLog(path).read()) == 1


# ------------------------------------------------------------------------ shortfall


def test_the_shortfall_refuses_a_future_that_is_not_the_rows_root() -> None:
    with pytest.raises(Track3Error, match="logged on root"):
        shortfall_ticks(make_row(), Future("ES", 0.25, 50.0, 12.5))
    with pytest.raises(Track3Error, match="needs a Future"):
        shortfall_ticks(make_row(), "MES")  # type: ignore[arg-type]


def test_the_same_tick_count_is_different_money_on_a_different_contract() -> None:
    """The micro-size argument: 1 tick is $1.25 on MES and $12.50 on ES."""
    from backtest_framework.validation.track3 import shortfall_usd

    es_row = make_row(root="ES")
    es = Future("ES", 0.25, 50.0, 12.5)
    assert shortfall_ticks(make_row(), MES) == shortfall_ticks(es_row, es) == 1.0
    assert shortfall_usd(make_row(), MES) == 1.25
    assert shortfall_usd(es_row, es) == 12.5


# -------------------------------------------------------------------------- latency


@pytest.mark.parametrize("bad", [0.0, -60.0, float("nan"), float("inf")])
def test_bar_seconds_must_be_finite_and_positive(bad: float) -> None:
    with pytest.raises(Track3Error, match="bar_seconds"):
        latency_bars(make_row(), bad)


def test_the_quantile_is_nearest_rank_in_integer_arithmetic() -> None:
    values = [0.5, 1.0, 2.0, 6.0, 7.0, 8.0]
    assert quantile_nearest_rank(values, 1, 2) == 2.0
    assert quantile_nearest_rank(values, 19, 20) == 8.0
    assert quantile_nearest_rank(values, 1, 1) == 8.0
    assert quantile_nearest_rank([3.0], 19, 20) == 3.0
    with pytest.raises(Track3Error, match="empty sample"):
        quantile_nearest_rank([], 1, 2)
    with pytest.raises(Track3Error, match="0 < num <= den"):
        quantile_nearest_rank(values, 3, 2)


def test_a_fill_exactly_at_t0_plus_5_is_inside_the_assumption() -> None:
    at_five = make_row(fill_ts=T0 + dt.timedelta(seconds=300))
    beyond = make_row(trade_id="U2", fill_ts=T0 + dt.timedelta(seconds=301))
    rep = latency_report([at_five, beyond], 60.0)
    assert rep["n_beyond"] == 1
    assert rep["share_beyond_t0_plus_5"] == 0.5


def test_assumed_max_must_be_positive() -> None:
    with pytest.raises(Track3Error, match="assumed_max"):
        latency_report([make_row()], 60.0, assumed_max=0.0)


# ---------------------------------------------------------------- the cost assumption


def test_the_cost_assumption_is_half_a_round_trip_plus_one_adverse_tick() -> None:
    """Read off `data/futures_costs.json` (D591), not from a literal typed here."""
    table = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "futures_costs.json").read_text(
            encoding="utf-8"
        )
    )
    crossing = table["roots"]["NQ"]["micro"]["crossing_ticks_rt"]["d508_exec"]["value"]
    assert cost_assumption_ticks("MNQ", line="d508_exec") == crossing / 2.0 + 1.0
    assert cost_assumption_ticks("MNQ", line="d508_exec") == 2.0671211061113803
    assert cost_assumption_ticks("NQ", "full", "d508_exec") == 2.5227066433527296
    assert ADVERSE_TICKS_PER_ENTRY == 1.0


def test_the_one_tick_line_gives_exactly_one_and_a_half_ticks() -> None:
    """`d556_one_tick` is 1.0 tick per round trip, so half of it plus one adverse is 1.5."""
    assert cost_assumption_ticks("MNQ", line="d556_one_tick") == 1.5


def test_an_unmeasured_line_raises_rather_than_borrowing_another_roots_number() -> None:
    with pytest.raises(FuturesCostError):
        cost_assumption_ticks("MNQ", line="no_such_line")


# ------------------------------------------------------------------- the cost review


def test_the_cost_review_reads_the_first_n_rows_not_every_row() -> None:
    worse = [make_row(trade_id=f"W{i}", fill_px=5000.5) for i in range(3)]
    better = [make_row(trade_id=f"B{i}", fill_px=4999.75) for i in range(3)]
    rev = cost_review(worse + better, MES, 1.0, n=3)
    assert rev.n == 6, "n reports what is logged"
    assert rev.required_n == 3
    assert rev.mean_shortfall_ticks == 2.0, "the first three rows, not all six"
    assert rev.ratio == 2.0
    assert rev.exceeds_by_50pct is True


def test_the_trigger_is_strictly_greater_than_fifty_percent() -> None:
    assert EXCEEDS_RATIO == 1.5
    exactly = [make_row(trade_id=f"E{i}", fill_px=5000.375) for i in range(2)]
    rev = cost_review(exactly, MES, 1.0, n=2)
    assert rev.mean_shortfall_ticks == 1.5
    assert rev.ratio == 1.5
    assert rev.exceeds_by_50pct is False, "'more than 50%' is strict"


def test_the_cost_review_defaults_to_the_deposits_fifty() -> None:
    assert COST_REVIEW_N == 50
    rev = cost_review([make_row()], MES, 1.0)
    assert rev.required_n == 50
    assert rev.sufficient is False
    assert rev.to_dict()["mean_shortfall_ticks"] is None


def test_the_cost_review_refuses_a_non_positive_n_or_assumption() -> None:
    with pytest.raises(Track3Error, match="positive trade count"):
        cost_review([make_row()], MES, 1.0, n=0)
    with pytest.raises(Track3Error, match="assumption in ticks"):
        cost_review([make_row()], MES, -1.0)


# ------------------------------------------------------------------- the trial counter


def test_the_counters_defaults_are_the_deposits() -> None:
    counter = TrialCounter("m")
    assert counter.target == TRACK3_TARGET_N == 300
    assert counter.looks == (100, 200)
    assert counter.counts_as_efficacy is True
    assert counter.n == 0


@pytest.mark.parametrize("looks", [(200, 100), (100, 100), (100, 300), (100, 400), (1, 100)])
def test_bad_looks_raise(looks: tuple[int, ...]) -> None:
    with pytest.raises(Track3Error):
        TrialCounter("m", target=300, looks=looks)


def test_a_counter_with_no_model_name_or_a_tiny_target_raises() -> None:
    with pytest.raises(Track3Error, match="model name"):
        TrialCounter("  ")
    with pytest.raises(Track3Error, match="target must be an int"):
        TrialCounter("m", target=1, looks=())


def test_mean_sd_and_t_raise_below_their_own_sample_sizes() -> None:
    counter = TrialCounter("m")
    with pytest.raises(Track3Error, match="mean of no trades"):
        _ = counter.mean
    counter.add(1.0)
    assert counter.mean == 1.0
    with pytest.raises(Track3Error, match="sd is undefined at N = 1"):
        _ = counter.sd
    with pytest.raises(Track3Error, match="sd is undefined at N = 1"):
        _ = counter.t


def test_a_constant_series_has_no_t() -> None:
    counter = TrialCounter("m")
    counter.extend([0.25] * 10)
    assert counter.mean == 0.25
    assert counter.sd == 0.0
    with pytest.raises(Track3Error, match="sd = 0 and t is undefined"):
        _ = counter.t


def test_a_non_finite_return_is_refused() -> None:
    with pytest.raises(Track3Error, match="net_return_per_trade"):
        TrialCounter("m").add(float("nan"))


def test_futility_is_false_away_from_a_look_whatever_the_numbers() -> None:
    counter = TrialCounter("m", target=20, looks=(10,))
    counter.extend([-1.0] + [-0.25] * 8)
    assert counter.n == 9
    assert counter.mean < 0 and counter.t < -1
    assert counter.futility() is False
    counter.add(-0.25)
    assert counter.at_look() is True
    assert counter.futility() is True


def test_efficacy_is_false_when_the_flag_is_off_and_the_reason_is_required() -> None:
    with pytest.raises(Track3Error, match="needs an efficacy_reason"):
        TrialCounter("m", counts_as_efficacy=False)
    counter = TrialCounter(
        "m", target=4, looks=(2,), counts_as_efficacy=False,
        efficacy_reason="index unit test 28",
    )
    counter.extend([1.0, 1.0, 1.0, 1.5])
    assert counter.n == 4
    assert counter.mean > 0 and counter.t >= 2
    assert counter.efficacy() is False
    assert counter.to_dict()["efficacy"] is False


def test_a_t_exactly_on_the_bar_is_decided_by_the_last_bit() -> None:
    """A KNOWN LIMIT OF THE PRE-REGISTERED RULE, pinned rather than softened.

    `efficacy()` compares `t >= 2.0` exactly, as SETTLEMENT_FLOW_LEDGER_PREREG.md §13A.4 states
    it. The series `[0, d, d]` has t = 2 ALGEBRAICALLY for every d > 0 -- mean = 2d/3,
    sd = d/sqrt(3), t = mean*sqrt(3)/sd = 2 -- but the computed t depends on d's binary
    expansion. At d = 0.0546875 it computes to exactly 2.0 and the decision is True; multiply
    every value by that same 0.0546875 and it computes to 1.9999999999999998, one ULP lower,
    and the decision is False. `tests/property/test_track3_property.py` found this pair.

    The threshold is not moved and no tolerance is added: a pre-registered bar is not this
    module's to soften. What is recorded is that a t landing ON the bar is a coin toss, so a
    forward test finishing at t = 2.000000 should be reported as such rather than as a pass.
    """
    on_bar = TrialCounter("edge", target=3, looks=())
    on_bar.extend([0.0, 0.0546875, 0.0546875])
    assert on_bar.t == 2.0
    assert on_bar.efficacy() is True

    rescaled = TrialCounter("edge-scaled", target=3, looks=())
    rescaled.extend([v * 0.0546875 for v in [0.0, 0.0546875, 0.0546875]])
    assert rescaled.t == 1.9999999999999998
    assert rescaled.efficacy() is False
    assert rescaled.t < on_bar.t, "one ULP, and it is the whole verdict"


def test_an_explicit_restart_clears_the_count_and_is_recorded() -> None:
    counter = TrialCounter("m")
    counter.extend([0.1, 0.2, 0.3])
    record = counter.restart("upgraded to the best retained stage (13A.5)")
    assert counter.n == 0
    assert record.at_n == 3
    assert counter.restarts == [record]
    assert counter.to_dict()["restarts"][0]["reason"].startswith("upgraded")
    with pytest.raises(Track3Error, match="must name its reason"):
        counter.restart("")


def test_check_frozen_returns_none_when_clean_and_restarts_on_drift(tmp_path: Path) -> None:
    code = tmp_path / "model.py"
    code.write_text("ALPHA = 1\n", encoding="utf-8", newline="\n")
    frozen = tmp_path / "FROZEN_A.json"
    freeze(frozen, name="A", params={"alpha": 1}, code_paths=[code])

    counter = TrialCounter("m", frozen_path=frozen)
    counter.extend([0.1, 0.2, 0.3])
    assert counter.check_frozen({"alpha": 1}, [code]) is None
    assert counter.n == 3, "a clean check never touches the count"

    restart = counter.check_frozen({"alpha": 2}, [code])
    assert restart is not None
    assert restart.at_n == 3
    assert restart.reason == "frozen drift"
    assert "DRIFTED" in restart.message
    assert counter.n == 0, "13A.4: any change restarts the count at N = 0"
    assert len(counter.restarts) == 1


def test_check_frozen_without_a_frozen_path_raises() -> None:
    with pytest.raises(Track3Error, match="needs a frozen_path"):
        TrialCounter("m").check_frozen({}, [])


def test_the_route_delegates_to_power_and_is_never_retyped() -> None:
    from backtest_framework.validation.power import track3_route

    counter = TrialCounter("m")
    assert counter.route(0.2) == track3_route(0.2, n=300)
    assert counter.route(0.2).route == "efficacy_n300"
    assert counter.route(0.01).route == "combined_evidence"
    with pytest.raises(ValueError):
        counter.route(0.0)


# -------------------------------------------------------------------- the report script


def _report_module() -> object:
    """`scripts/track3_report.py`, by explicit path.

    Named by path rather than by import, because `scripts/` is not a package and pytest
    imports any path you hand it (the D546 defect).
    """
    import importlib.util
    import sys

    path = Path(__file__).resolve().parents[2] / "scripts" / "track3_report.py"
    spec = importlib.util.spec_from_file_location("track3_report", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["track3_report"] = module
    spec.loader.exec_module(module)
    return module


def test_the_report_scripts_selftest_returns_zero() -> None:
    """Every guard, once clean and once broken -- the whole thing, silently."""
    module = _report_module()
    assert module.selftest(log=lambda *a, **k: None) == 0  # type: ignore[attr-defined]


def test_the_report_emits_all_four_declared_sections(tmp_path: Path) -> None:
    """REQUIRED_OUTPUTS in the runner, not prose: the guard raises on a missing block."""
    module = _report_module()
    path = tmp_path / "mnq_trades.csv"
    log = TradeLog(path)
    for i in range(3):
        log.append(
            make_row(
                trade_id=f"R{i}",
                root="MNQ",
                signal_ts=T0 + dt.timedelta(minutes=10 * i),
                order_sent_ts=T0 + dt.timedelta(minutes=10 * i, seconds=10),
                fill_ts=T0 + dt.timedelta(minutes=10 * i, seconds=60),
                model_fill_px=20000.0,
                fill_px=20000.25,
            )
        )
    counter = TrialCounter("mnq", target=10, looks=(4,))
    counter.extend([0.5, -0.25, 0.75])
    lines: list[str] = []
    out = module.report(  # type: ignore[attr-defined]
        path, "MNQ", "micro", "d508_exec", 60.0, counter=counter, log=lines.append
    )
    text = "\n".join(lines)
    for section in module.REQUIRED_SECTIONS:  # type: ignore[attr-defined]
        assert section in text
    assert out["shortfall"]["mean_ticks"] == 1.0
    assert out["latency"]["n_beyond"] == 0
    assert out["cost_review"]["sufficient"] is False
    assert out["counter"]["n"] == 3


def test_the_report_refuses_a_log_with_a_header_and_no_trades(tmp_path: Path) -> None:
    module = _report_module()
    path = tmp_path / "empty.csv"
    path.write_text(",".join(FIELDS) + "\n", encoding="utf-8", newline="\n")
    with pytest.raises(Track3Error, match="header and no trades"):
        module.report(path, "MNQ", "micro", "d508_exec", 60.0)  # type: ignore[attr-defined]


def test_to_dict_is_readable_at_every_sample_size() -> None:
    counter = TrialCounter("m", target=10, looks=(4,))
    empty = counter.to_dict()
    assert empty["n"] == 0 and empty["mean"] is None and empty["t"] is None
    assert empty["futility"] is False and empty["efficacy"] is False
    counter.add(0.5)
    one = counter.to_dict()
    assert one["mean"] == 0.5 and one["sd"] is None and one["t"] is None
    counter.extend([0.5] * 3)
    flat = counter.to_dict()
    assert flat["sd"] == 0.0 and flat["t"] is None, "a constant series reports no t"
    assert flat["at_look"] is True and flat["futility"] is False
