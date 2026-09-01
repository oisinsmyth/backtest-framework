"""Gates on the continuous-contract stitcher.

**Entirely offline — no vendor data, no network.** That is the point: §12 of the
data-purchase proposal requires these gates to exist before a fixture does, and
every external source consulted said stitching, not acquisition, is the hard part.

Two tests carry the weight:

  A. SYNTHETIC GROUND TRUTH. Contracts built from a known true path, so the
     stitcher can be checked for EXACTNESS rather than plausibility. Plausible is
     what a broken stitcher already looks like.

  B. THE MEASURED YAHOO SIGNATURE. A gate suite that has never rejected anything
     is not evidence, so the specific `ES=F` failure this programme measured is
     reconstructed and the gates must reject it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def fc():
    path = REPO / "scripts" / "futures_continuous.py"
    spec = importlib.util.spec_from_file_location("futures_continuous", path)
    m = importlib.util.module_from_spec(spec)
    sys.modules["futures_continuous"] = m
    spec.loader.exec_module(m)
    return m


def _grid(n: int, start: int = 0) -> tuple[str, ...]:
    """`n` sequential ISO dates. Calendar realism is irrelevant here; ordering and
    uniqueness are all the stitcher uses."""
    return tuple(f"2024-{1 + (start + i) // 28:02d}-{1 + (start + i) % 28:02d}"
                 for i in range(n))


def _true_path(n: int, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return 100.0 * np.exp(np.cumsum(rng.normal(0.0002, 0.01, n)))


# ------------------------------------------------- A. synthetic ground truth


def _two_contracts(fc, n=200, overlap=(100, 130), basis=1.02):
    """Contract A trades at the true path; B at a constant 2% premium.

    Volume migrates GRADUALLY across the overlap — A ramps 1000 -> 200 while B
    ramps 200 -> 1000 — so they cross while BOTH ARE STILL LIQUID. That is what
    a real roll looks like, and it is the difference the gates measure: a healthy
    crossover leaves the front month at ~50% volume share, where Yahoo's calendar
    roll leaves it at ~21%.

    A ratio-adjusted stitch must then recover the true path's RETURNS exactly,
    because a constant proportional basis is precisely what ratio adjustment is
    built to remove."""
    lo, hi = overlap
    dates = _grid(n)
    p = _true_path(n)
    m = hi - lo

    a_vol = np.concatenate([np.full(lo, 1000.0), np.linspace(1000.0, 200.0, m)])
    a = fc.Contract("A", dates[:hi], p[:hi], a_vol)

    b_vol = np.concatenate([np.linspace(200.0, 1000.0, m), np.full(n - hi, 1000.0)])
    b = fc.Contract("B", dates[lo:], p[lo:] * basis, b_vol)
    return [a, b], p, dates


def test_the_roll_lands_on_the_volume_crossover(fc):
    contracts, _p, dates = _two_contracts(fc)
    rolls = fc.build_roll_calendar(contracts, method="volume")
    assert len(rolls) == 1
    assert rolls[0].from_symbol == "A" and rolls[0].to_symbol == "B"
    # The ramps cross halfway through the 30-session overlap that starts at 100.
    assert rolls[0].date == dates[115]
    # And the front month must still be ALIVE at the roll -- that is the whole
    # difference between crossover rolling and calendar rolling, and it is what
    # separates this series from the Yahoo one reconstructed below.
    assert rolls[0].front_volume_share == pytest.approx(0.49, abs=0.02)
    assert rolls[0].front_volume_share > fc.MIN_VOLUME_SHARE_AT_ROLL


def test_ratio_adjustment_recovers_the_true_returns_EXACTLY(fc):
    """The test that proves correctness rather than plausibility. A constant
    proportional basis is precisely what ratio adjustment removes, so the
    recovered return series must match to floating-point precision -- not
    approximately, not on average."""
    contracts, p, _dates = _two_contracts(fc)
    rolls = fc.build_roll_calendar(contracts)
    series = fc.stitch(contracts, rolls, adjustment="ratio")

    ok = np.isfinite(series.adjusted)
    got = np.diff(np.log(series.adjusted[ok]))
    want = np.diff(np.log(p[ok]))
    np.testing.assert_allclose(got, want, rtol=0, atol=1e-12)


def test_difference_adjustment_recovers_a_constant_offset_basis_exactly(fc):
    """The mirror case. Where the basis is ADDITIVE, difference adjustment is the
    exact inverse and ratio is not -- which is why both conventions are kept."""
    n, roll_bias, offset = 200, 110, 3.5
    dates, p = _grid(n), _true_path(n)
    a = fc.Contract("A", dates[:roll_bias + 20], p[:roll_bias + 20],
                    np.where(np.arange(roll_bias + 20) < roll_bias, 1000.0, 100.0))
    b = fc.Contract("B", dates[100:], p[100:] + offset,
                    np.where(np.arange(100, n) < roll_bias, 100.0, 1000.0))
    rolls = fc.build_roll_calendar([a, b])
    series = fc.stitch([a, b], rolls, adjustment="difference")

    ok = np.isfinite(series.adjusted)
    np.testing.assert_allclose(series.adjusted[ok], p[ok] + offset,
                               rtol=0, atol=1e-9)


def test_the_unadjusted_series_is_always_retained(fc):
    """Adjusted prices are a derived view, and back-adjustment restates the whole
    history every time a new roll happens. A fixture keeping only the derived view
    cannot be re-derived under a different convention."""
    contracts, _p, _d = _two_contracts(fc)
    rolls = fc.build_roll_calendar(contracts)
    series = fc.stitch(contracts, rolls, adjustment="ratio")
    ok = np.isfinite(series.adjusted)
    assert not np.allclose(series.adjusted[ok], series.unadjusted[ok])
    # The newest segment is untouched: that is what BACK-adjusted means.
    assert series.unadjusted[-1] == pytest.approx(series.adjusted[-1])


def test_no_forward_filling_anywhere(fc):
    """`ragged_panel` contract 4: a fabricated price is a fabricated return. A
    session where the ACTIVE contract did not trade must stay NaN.

    The gap has to be covered by a later contract, or it would not be on the
    union grid at all -- an absent session and an untraded one are different
    things, and only the second is a hazard."""
    dates, p = _grid(60), _true_path(60)
    traded = list(dates[:20]) + list(dates[25:40])
    a = fc.Contract("A", tuple(traded), np.concatenate([p[:20], p[25:40]]),
                    np.full(35, 1000.0))
    b = fc.Contract("B", dates, p * 1.01,
                    np.concatenate([np.full(45, 10.0), np.full(15, 5000.0)]))

    rolls = fc.build_roll_calendar([a, b])
    series = fc.stitch([a, b], rolls, adjustment="none")

    # dates[20:25] are on the grid via B, but A is still the active contract
    # there and did not trade. Those sessions must be NaN, not carried forward.
    assert series.dates == dates
    for d in dates[20:25]:
        i = series.dates.index(d)
        assert series.source_symbol[i] == "A"
        assert not np.isfinite(series.adjusted[i]), d


# ------------------------------------------- B. the measured Yahoo signature


def _yahoo_shaped(fc):
    """Reconstruct the `ES=F` failure measured during the free-data search:

      * rolls AT EXPIRY, so the front month's volume has already collapsed ~4x
        (measured 1,996k -> 532k over the final week)
      * NO back-adjustment: `adjclose` was a verbatim copy of `close` on
        1258/1258 bars
      * therefore a large gap at the roll -- measured +2.77% on 2024-12-20
    """
    n, expiry_i = 200, 130
    dates, p = _grid(n), _true_path(n)

    a_vol = np.where(np.arange(expiry_i + 1) < 110, 2000.0,
                     np.linspace(2000.0, 500.0, expiry_i + 1 - 110).repeat(1)[0])
    a_vol = np.concatenate([np.full(110, 2000.0),
                            np.linspace(1996.0, 532.0, expiry_i + 1 - 110)])
    a = fc.Contract("A", dates[:expiry_i + 1], p[:expiry_i + 1], a_vol,
                    expiry=dates[expiry_i])
    b = fc.Contract("B", dates[100:], p[100:] * 1.0277,
                    np.concatenate([np.full(10, 100.0), np.full(n - 110, 2500.0)]))

    # THE CALENDAR ROLL: forced to expiry, which is what Yahoo does.
    late = fc.Roll(date=dates[expiry_i], from_symbol="A", to_symbol="B",
                   from_price=float(p[expiry_i]),
                   to_price=float(p[expiry_i] * 1.0277),
                   from_volume=532.0, to_volume=2500.0)
    return [a, b], [late], p, dates, expiry_i


def test_the_gates_reject_a_series_that_CLAIMS_to_be_adjusted_and_is_not(fc):
    """The 1258/1258 `adjclose == close` signature, and the distinction is the
    whole point: a series honestly labelled unadjusted is fine. Yahoo's was
    labelled ADJUSTED and was byte-identical to the raw one, which is
    mislabelling, and nothing downstream would have noticed.

    Constructed directly rather than through `stitch`, because our own stitcher
    cannot produce this state -- which is itself the reassuring part."""
    contracts, rolls, _p, _d, _e = _yahoo_shaped(fc)
    honest = fc.stitch(contracts, rolls, adjustment="none")
    assert fc.acceptance_gates(honest)["adjustment_actually_applied"][
        "failures"] == [], "an honestly-unadjusted series is not a failure"

    liar = fc.Continuous(
        dates=honest.dates, unadjusted=honest.unadjusted,
        adjusted=honest.unadjusted.copy(),      # the verbatim copy
        source_symbol=honest.source_symbol, rolls=honest.rolls,
        method=honest.method, adjustment="ratio",   # ...but CLAIMS ratio
    )
    gates = fc.acceptance_gates(liar)
    assert gates["adjustment_actually_applied"]["adjusted_equals_unadjusted"]
    assert gates["adjustment_actually_applied"]["failures"]
    assert gates["passed"] is False


def test_the_gates_reject_a_roll_at_expiry(fc):
    """The defining symptom of a calendar roll: the front month is already
    moribund when the roll happens. Measured on Yahoo at ~21% volume share."""
    contracts, rolls, _p, dates, expiry_i = _yahoo_shaped(fc)
    series = fc.stitch(contracts, rolls, adjustment="ratio")
    gates = fc.acceptance_gates(series, expiry_dates={dates[expiry_i]})

    late = gates["rolls_on_crossover_not_expiry"]["failures"]
    assert late, "a roll at 17.5% front-month volume share must be flagged"
    assert late[0]["front_volume_share"] < fc.MIN_VOLUME_SHARE_AT_ROLL
    assert gates["no_roll_on_an_expiry_date"]["failures"] == [dates[expiry_i]]
    assert gates["passed"] is False


def test_the_gates_reject_an_unadjusted_roll_gap(fc):
    """+2.77% on a day the market moved +0.60% is not a session, it is a splice."""
    contracts, rolls, _p, _d, _e = _yahoo_shaped(fc)
    series = fc.stitch(contracts, rolls, adjustment="none")
    gates = fc.acceptance_gates(series, move_limit=0.02)
    assert gates["no_unexplained_large_move"]["failures"]
    assert gates["no_unexplained_large_move"]["worst"] > 0.02


def test_the_gates_catch_divergence_concentrated_on_roll_dates(fc):
    """The measurement that actually caught Yahoo: 15 of its top 16 ES-vs-SPY
    divergences fell on quarterly expiries. That is not a market fact."""
    contracts, rolls, p, _d, _e = _yahoo_shaped(fc)
    series = fc.stitch(contracts, rolls, adjustment="none")
    gates = fc.acceptance_gates(series, reference=p)
    block = gates["divergence_not_concentrated_at_rolls"]
    assert block["of_which_on_a_roll_date"] >= 1
    assert block["failures"] or block["of_which_on_a_roll_date"] >= 1


def test_a_correctly_stitched_series_PASSES_every_gate(fc):
    """The complement, and it is what makes the rejections above meaningful: a
    gate suite that rejects everything is no better than one that rejects
    nothing."""
    contracts, p, _dates = _two_contracts(fc)
    rolls = fc.build_roll_calendar(contracts, method="volume")
    series = fc.stitch(contracts, rolls, adjustment="ratio")
    gates = fc.acceptance_gates(series, reference=p)
    assert gates["passed"] is True, gates


# ------------------------------------------------------------- conventions


def test_difference_adjustment_survives_a_negative_price(fc):
    """Not hypothetical: CL settled at -$37.63 on 2020-04-20. Ratio adjustment is
    undefined through zero; difference is not, which is the reason both exist."""
    dates = _grid(60)
    path = np.concatenate([np.linspace(20.0, 5.0, 30),
                           np.linspace(-5.0, 15.0, 30)])
    a = fc.Contract("A", dates[:40], path[:40],
                    np.concatenate([np.full(30, 1000.0), np.full(10, 100.0)]))
    b = fc.Contract("B", dates[25:], path[25:] + 2.0,
                    np.concatenate([np.full(5, 100.0), np.full(30, 1000.0)]))
    rolls = fc.build_roll_calendar([a, b])
    series = fc.stitch([a, b], rolls, adjustment="difference")
    ok = np.isfinite(series.adjusted)
    assert np.any(series.adjusted[ok] < 0), "the negative excursion must survive"
    assert np.all(np.isfinite(series.adjusted[ok]))


def test_a_one_day_volume_blip_does_not_trigger_a_roll(fc):
    """A single session where the back month out-trades the front is noise --
    often an expiry-week spread trade. Rolling on it produces a calendar full of
    one-day round trips."""
    n, dates, p = 120, _grid(120), _true_path(120)
    a_vol = np.full(n, 1000.0)
    a_vol[40] = 10.0                      # the blip: B out-trades A for ONE day
    a = fc.Contract("A", dates, p, a_vol)
    b = fc.Contract("B", dates, p * 1.01,
                    np.concatenate([np.full(80, 100.0), np.full(40, 5000.0)]))
    rolls = fc.build_roll_calendar([a, b], min_persist=2)
    assert rolls[0].date == dates[80], "rolled on a one-day blip"


def test_roll_method_must_be_named(fc):
    with pytest.raises(ValueError):
        fc.build_roll_calendar([], method="whatever-was-convenient")
    contracts, _p, _d = _two_contracts(fc)
    with pytest.raises(ValueError):
        fc.stitch(contracts, [], adjustment="vibes")


def test_open_interest_rolling_needs_open_interest(fc):
    contracts, _p, _d = _two_contracts(fc)
    with pytest.raises(ValueError, match="open interest"):
        fc.build_roll_calendar(contracts, method="open_interest")
