"""The `Future` instrument (D587): specification loading, the tick grid, and the protocol.

Gate U for the quantity rules, per CONTRIBUTING.md's "adding a brick" table. The money side
— fills — is gated in `tests/golden/test_futures_fills_ledger.py`.

**No panel is read here.** The two specification files are small committed JSON, not bulk
data, so nothing in this file needs `requires_panel`.
"""

import json
from pathlib import Path

import pytest

from backtest_framework.instruments import Future as FutureFromPackage
from backtest_framework.instruments.base import Instrument
from backtest_framework.instruments.future import (
    FALLBACK_SPECS_PATH,
    SPECS_PATH,
    Future,
)

MES = Future(root="MES", tick_points=0.25, usd_per_point=5.0, tick_usd=1.25)
ZN = Future(root="ZN", tick_points=0.015625, usd_per_point=1000.0, tick_usd=15.625)
CL = Future(root="CL", tick_points=0.01, usd_per_point=1000.0, tick_usd=10.0)


# ---------------------------------------------------------------- loading the specs


@pytest.mark.parametrize(
    "root, tick_points, usd_per_point, tick_usd",
    [
        ("ES", 0.25, 50.0, 12.5),
        ("MES", 0.25, 5.0, 1.25),
        ("NQ", 0.25, 20.0, 5.0),
        ("CL", 0.01, 1000.0, 10.0),
        ("ZN", 0.015625, 1000.0, 15.625),
    ],
)
def test_from_specs_reads_the_cme_file(root, tick_points, usd_per_point, tick_usd):
    f = Future.from_specs(root)
    assert (f.root, f.tick_points, f.usd_per_point, f.tick_usd) == (root, tick_points, usd_per_point, tick_usd)
    assert f.quote_currency == "USD"


def test_from_specs_falls_back_to_the_definition_snapshot_for_mbt():
    """MBT is absent from the CME file — the case `run_d555_tsmom_replication.py` handles by hand."""
    assert "MBT" not in json.loads(SPECS_PATH.read_text(encoding="utf-8"))
    f = Future.from_specs("MBT")
    assert (f.tick_points, f.tick_usd) == (5.0, 0.5)
    assert f.usd_per_point == pytest.approx(0.1)


def test_unknown_root_raises_key_error_naming_what_is_known():
    with pytest.raises(KeyError) as exc:
        Future.from_specs("NOT_A_ROOT")
    assert "ES" in str(exc.value) and "D48" in str(exc.value)


def test_from_specs_paths_are_overridable(tmp_path: Path):
    primary = tmp_path / "primary.json"
    primary.write_text(json.dumps({"XX": {"tick_points": 0.5, "usd_per_point": 4.0, "tick_usd": 2.0}}))
    fallback = tmp_path / "fallback.json"
    fallback.write_text(json.dumps({"specs": {}}))
    f = Future.from_specs("XX", specs_path=primary, fallback_path=fallback)
    assert (f.tick_points, f.usd_per_point, f.tick_usd) == (0.5, 4.0, 2.0)


def test_every_root_in_both_files_builds_and_is_self_consistent():
    """The `_provenance` note claims `usd_per_point * tick_points == tick_usd` for every entry.

    `Future.__post_init__` is the assertion; this test is what makes it run over the whole file
    rather than over whichever root a study happened to load.
    """
    cme = [k for k in json.loads(SPECS_PATH.read_text(encoding="utf-8")) if not k.startswith("_")]
    definition = json.loads(FALLBACK_SPECS_PATH.read_text(encoding="utf-8"))["specs"]
    built = [Future.from_specs(r) for r in cme]
    assert len(built) >= 20
    present = [r for r, v in definition.items() if v.get("present")]
    assert len(present) >= 30
    for root in present:
        f = Future.from_specs(root)
        assert f.tick_points > 0 and f.usd_per_point > 0


# ------------------------------------------------------------------- construction


def test_tick_usd_that_disagrees_with_the_other_two_is_rejected():
    with pytest.raises(ValueError, match="tick_usd"):
        Future(root="ES", tick_points=0.25, usd_per_point=50.0, tick_usd=13.0)


@pytest.mark.parametrize("kwargs", [
    {"tick_points": 0.0}, {"tick_points": -0.25}, {"usd_per_point": 0.0}, {"tick_usd": float("nan")},
])
def test_non_positive_or_non_finite_specs_are_rejected(kwargs):
    base = {"root": "ES", "tick_points": 0.25, "usd_per_point": 50.0, "tick_usd": 12.5}
    with pytest.raises(ValueError):
        Future(**{**base, **kwargs})


def test_empty_root_is_rejected():
    with pytest.raises(ValueError, match="root"):
        Future(root="", tick_points=0.25, usd_per_point=50.0, tick_usd=12.5)


# ---------------------------------------------------------------------- the grid


@pytest.mark.parametrize(
    "price, down, nearest, up",
    [
        (5000.30, 5000.25, 5000.25, 5000.50),
        (5000.20, 5000.00, 5000.25, 5000.25),
        (5000.125, 5000.00, 5000.25, 5000.25),
        (5000.25, 5000.25, 5000.25, 5000.25),
    ],
)
def test_round_to_tick_directions(price, down, nearest, up):
    assert MES.round_to_tick(price, "down") == down
    assert MES.round_to_tick(price, "nearest") == nearest
    assert MES.round_to_tick(price, "up") == up


def test_round_to_tick_leaves_an_on_grid_price_alone_in_every_direction():
    """The tolerance exists for exactly this: 5000.25/0.25 must not land at 20000.9999."""
    for k in range(-40, 40):
        price = 5000.0 + k * 0.25
        for direction in ("down", "nearest", "up"):
            assert MES.round_to_tick(price, direction) == price


def test_round_to_tick_on_a_non_decimal_grid():
    on_grid = 110.0 + 3 / 64
    assert ZN.round_to_tick(on_grid, "nearest") == on_grid
    assert ZN.round_to_tick(110.05, "down") == pytest.approx(110.046875)
    assert ZN.round_to_tick(110.05, "up") == pytest.approx(110.0625)


def test_round_to_tick_up_and_down_mean_toward_infinity_not_away_from_zero():
    """CL settled at -37.63 on 2020-04-20; a rule that flips sense at zero is a trap."""
    assert CL.round_to_tick(-37.635, "down") == pytest.approx(-37.64)
    assert CL.round_to_tick(-37.635, "up") == pytest.approx(-37.63)
    CL.assert_on_grid(-37.63)


def test_bad_rounding_direction_raises():
    with pytest.raises(ValueError, match="nearest"):
        MES.round_to_tick(5000.0, "toward_zero")


def test_assert_on_grid_rejects_a_price_between_ticks():
    MES.assert_on_grid(5000.25)
    with pytest.raises(ValueError, match="off the 0.25 grid"):
        MES.assert_on_grid(5000.30)


def test_assert_on_grid_tolerance_is_in_ticks_not_in_price():
    """Half a tick of drift is off the grid on MES AND on ZN; an absolute epsilon would not be."""
    MES.assert_on_grid(5000.25 + 1e-10 * 0.25)
    with pytest.raises(ValueError):
        MES.assert_on_grid(5000.25 + 1e-6)
    ZN.assert_on_grid(110.0 + 3 / 64)
    with pytest.raises(ValueError):
        ZN.assert_on_grid(110.0 + 3 / 64 + 0.004)


def test_the_grid_tolerance_floors_at_the_prices_own_float_resolution():
    """A nanotick is tighter than a double can carry once price/tick gets large.

    6E's tick is 5e-05. At 5,000 — a price 6E never sees, but the guard must not invent a
    failure there — `5000 + k * 5e-05` carries 2.2e-09 ticks of representation error, so
    the unfloored rule declared a third of those k off their own grid. The floor is what
    makes the answer "as tight as the float can express" instead of a false alarm.
    """
    fine = Future.from_specs("6E")
    for base in (1.1, 5000.0):
        for k in range(-200, 201):
            fine.assert_on_grid(base + k * fine.tick_points)
    # the floor never LOOSENS the rule where the float has room: half a tick is still off
    with pytest.raises(ValueError):
        fine.assert_on_grid(1.1 + 0.5 * fine.tick_points)


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_prices_are_rejected(bad):
    with pytest.raises(ValueError):
        MES.assert_on_grid(bad)
    with pytest.raises(ValueError):
        MES.round_to_tick(bad)
    with pytest.raises(ValueError):
        MES.ticks(bad)


# ------------------------------------------------------------------- conversions


def test_ticks_and_usd_are_signed_and_not_rounded():
    assert MES.ticks(1.75) == 7.0
    assert MES.ticks(-1.75) == -7.0
    assert MES.ticks(0.30) == pytest.approx(1.2)
    assert MES.usd(1.75, 2) == 17.5
    assert MES.usd(-1.75, 2) == -17.5
    assert MES.usd(1.75, -2) == -17.5


def test_one_tick_is_worth_tick_usd_on_every_root():
    for root in ("ES", "MES", "NQ", "CL", "ZN"):
        f = Future.from_specs(root)
        assert f.usd(f.tick_points, 1) == pytest.approx(f.tick_usd)


def test_notional_carries_the_multiplier():
    assert MES.notional(3, 5000.25) == 75_003.75
    assert Future.from_specs("ES").notional(1, 4000.0) == 200_000.0
    assert MES.notional(-1, 5000.00) == -25_000.0


def test_tradeable_quantity_is_whole_contracts():
    assert MES.tradeable_quantity(2.4) == 2.0
    assert MES.tradeable_quantity(0.4) == 0.0
    assert MES.tradeable_quantity(-2.6) == -3.0


def test_a_future_has_no_carry_components():
    assert MES.carry_components() == ()


# --------------------------------------------------------------------- protocol


def test_future_satisfies_the_instrument_protocol():
    assert isinstance(MES, Instrument)


def test_future_is_exported_from_the_package():
    assert FutureFromPackage is Future


def test_future_is_frozen():
    with pytest.raises(Exception):
        MES.tick_points = 0.5
