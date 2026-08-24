"""Unit gates for the terrain confluence gate (D214).

Both inputs are already look-ahead guarded — `test_terrain_field.py` has the field's
mutate-the-future pair *and* its potency companion, `test_structure.py` has the detectors'.
**Neither says anything about their composition**, and composition is where a leak gets
reintroduced: reading the field at the entry bar rather than the signal bar would be a
one-character change that no existing test can see.

The other three groups exist because of defects this project has already had:

- the calendar match is asserted, not assumed (D194: five hours of volatility under a map
  spanning years);
- a gate that keeps everything must reproduce the ungated book bit-identically, which is
  the pin that catches an off-by-one in the gate itself;
- kept plus rejected must equal the total, because a count that only appears as a
  subtraction is a count nobody checks (D206, D209).
"""

from __future__ import annotations

import importlib.util
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.structure import market_structure
from backtest_framework.research.structure_setups import ATR_WINDOW_15M, find_setups
from backtest_framework.research.structure_strategies import Wrapper, run_arm
from backtest_framework.research.terrain_field import (
    FieldParams,
    build_grid,
    confirmed_swings,
    local_imbalance,
)
from backtest_framework.simulator.fills import Bar

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "run_structure_terrain_gate.py"

_spec = importlib.util.spec_from_file_location("terrain_gate", SCRIPT)
assert _spec is not None and _spec.loader is not None
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

EPOCH = datetime(2020, 1, 1)


def wandering(n: int, seed: int, start: float = 100.0) -> list[TimestampedBar]:
    rng = random.Random(seed)
    out, px = [], start
    for i in range(n):
        o = px
        px *= math.exp(rng.gauss(0.0, 0.004))
        c = px
        h = max(o, c) * (1.0 + abs(rng.gauss(0.0, 0.001)))
        lo = min(o, c) * (1.0 - abs(rng.gauss(0.0, 0.001)))
        out.append(TimestampedBar(EPOCH + timedelta(minutes=15 * i), Bar(o, h, lo, c)))
    return out


# --------------------------------------------------------------- the calendar match (D194)

def test_the_field_windows_are_calendar_matched_to_fifteen_minute_bars():
    """D202 ran daily. Leaving `atr_window` at 20 here would put five hours of volatility
    under a map spanning years — D194's defect, which cost that study a re-run."""
    assert gate.BARS_PER_DAY == 96
    assert gate.FIELD.atr_window == 20 * 96 == ATR_WINDOW_15M
    assert gate.FIELD.vol_norm_bars == 90 * 96
    assert gate.FIELD.erase is False, "D202's raw field"
    assert (gate.FIELD.k, gate.FIELD.cluster_atr) == (2, 0.5)


def test_the_annualisation_matches_the_bar_size():
    assert gate.PPY == 96 * 365


# ------------------------------------------------------------------------ the gate itself

@pytest.mark.parametrize("direction", (1, -1))
def test_aligned_and_inverted_are_exact_complements_on_a_non_zero_reading(direction):
    """Every trade with an opinionated reading lands in exactly one of the two arms. If
    both could reject the same trade the two arms would not sum to the book and the
    counterfactual would be meaningless."""
    for reading in (0.4, -0.4, 1.0, -1.0):
        a = gate.gate_keeps(reading, direction, +1, 0.0)
        i = gate.gate_keeps(reading, direction, -1, 0.0)
        assert a != i


def test_a_flat_reading_is_refused_by_both_arms():
    """Zero carries no opinion. Assigning it to one side would put every flat-field trade
    into whichever arm the sign convention happened to favour — an arbitrary tiebreak
    deciding a verdict, which is D173's tie rule applied one level up."""
    for direction in (1, -1):
        assert not gate.gate_keeps(0.0, direction, +1, 0.0)
        assert not gate.gate_keeps(0.0, direction, -1, 0.0)


def test_a_non_finite_reading_is_refused_rather_than_imputed():
    for direction in (1, -1):
        assert not gate.gate_keeps(math.nan, direction, +1, 0.0)
        assert not gate.gate_keeps(math.inf, direction, -1, 0.0)


def test_the_magnitude_floor_excludes_weak_readings_from_both_arms():
    assert gate.gate_keeps(0.5, 1, +1, 0.4)
    assert not gate.gate_keeps(0.3, 1, +1, 0.4)
    assert not gate.gate_keeps(-0.3, 1, -1, 0.4)


def test_inverted_takes_the_trade_the_map_disagrees_with():
    """The pre-registered primary, stated as an assertion so the direction cannot silently
    flip. A bullish reading (+) on a short setup (−1) is disagreement, and `inverted` takes
    it."""
    assert gate.gate_keeps(+0.5, -1, -1, 0.0), "bullish map, short setup, inverted keeps it"
    assert not gate.gate_keeps(+0.5, +1, -1, 0.0), "bullish map, long setup, inverted drops it"
    assert gate.gate_keeps(+0.5, +1, +1, 0.0), "aligned is the mirror"


# ------------------------------------------------------------- composition and accounting

class _Trade:
    """The two fields `evaluate` reads off a trade, and nothing else."""

    def __init__(self, direction: int, r: float, entry: int, exit_: int) -> None:
        self.direction = direction
        self.r_multiple = r
        self.entry_index = entry
        self.exit_index = exit_
        self.entry_price = 100.0
        self.exit_price = 100.0 + r
        self.risk = 1.0
        self.reason = "target" if r > 0 else "stop"


def test_kept_plus_rejected_always_equals_the_book(monkeypatch):
    """A count that only ever appears as a subtraction is a count nobody checks. D206 lost
    9% of setups to an `if window:` and D209 lost 93% of them to a guard, both silently."""
    bars = wandering(400, seed=3)
    trades = [_Trade(1 if i % 2 else -1, (i % 7) - 3.0, 10 + i * 5, 12 + i * 5) for i in range(40)]
    readings = [((-1) ** i) * (0.1 * (i % 9)) for i in range(40)]
    for want in (+1, -1):
        for floor in (0.0, 0.2, 0.5):
            got = gate.evaluate(bars, trades, readings, want, floor)
            assert got["n_kept"] + got["n_rejected"] == got["n_all"] == len(trades)


def test_a_gate_that_keeps_everything_reproduces_the_ungated_book():
    """The pin that catches an off-by-one in the gate. With every reading agreeing and no
    floor, the kept book must be the ungated book — not close to it, the same."""
    bars = wandering(400, seed=5)
    trades = [_Trade(1, (i % 5) - 2.0, 10 + i * 6, 13 + i * 6) for i in range(30)]
    readings = [0.9] * 30  # every reading bullish, every trade long
    got = gate.evaluate(bars, trades, readings, +1, 0.0)
    assert got["n_kept"] == len(trades)
    assert got["n_rejected"] == 0
    assert got["advantage_gross_r"] == pytest.approx(0.0, abs=1e-12)
    for tier in ("zero", "10bp", "40bp"):
        assert got["kept"][tier] == got["ungated"][tier]


def test_the_two_arms_partition_the_book_between_them():
    """`aligned` and `inverted` at floor zero must together account for every trade with an
    opinionated reading, and for none twice."""
    bars = wandering(400, seed=7)
    trades = [_Trade(1 if i % 3 else -1, (i % 5) - 2.0, 10 + i * 6, 13 + i * 6) for i in range(30)]
    readings = [0.5 if i % 2 else -0.5 for i in range(30)]
    a = gate.evaluate(bars, trades, readings, +1, 0.0)
    i = gate.evaluate(bars, trades, readings, -1, 0.0)
    assert a["n_kept"] + i["n_kept"] == len(trades)


# ---------------------------------------------------------------------- the shuffle control

def test_the_shuffle_control_finds_nothing_when_outcomes_carry_no_pattern():
    """The mandatory false-positive check (D180). With outcomes independent of the readings,
    a permuted gate must sit around zero — if this distribution were biased the real gate
    would be measured against a shifted baseline."""
    rng = random.Random(11)
    trades = [_Trade(1 if i % 2 else -1, rng.gauss(0.0, 1.0), 10 + i, 11 + i) for i in range(400)]
    readings = [rng.gauss(0.0, 0.5) for _ in range(400)]
    out = gate.shuffle_control(trades, readings, -1, 0.0, n=200, seed=0)
    assert abs(out["p50"]) < 0.15, out
    assert out["p95"] > 0.0


def test_the_shuffle_control_is_deterministic_under_its_seed():
    trades = [_Trade(1, float(i % 5) - 2.0, 10 + i, 11 + i) for i in range(200)]
    readings = [0.3 if i % 2 else -0.3 for i in range(200)]
    a = gate.shuffle_control(trades, readings, -1, 0.0, n=50, seed=4)
    b = gate.shuffle_control(trades, readings, -1, 0.0, n=50, seed=4)
    assert a == b
    assert gate.shuffle_control(trades, readings, -1, 0.0, n=50, seed=5) != a


# ------------------------------------------------------------------------- the three bars

def test_the_three_bars_are_ordered_and_the_combined_one_inherits_both_ledgers():
    """The deliverable. More looks must mean a higher bar and a lower DSR, and the combined
    count must be the sum `TERRAIN_RESULTS.md` forces: *anything that reuses these sensors
    inherits the count*."""
    assert gate.INHERITED["fresh"] == 0
    assert gate.INHERITED["structure only"] == 124
    assert gate.INHERITED["combined"] == 124 + 259

    table = gate.dsr_table(sharpe=1.5, t=294_336, var_trials=0.18)
    required = [table[k]["required_annual_sharpe"] for k in gate.INHERITED]
    observed = [table[k]["observed_dsr"] for k in gate.INHERITED]
    assert required == sorted(required), "more looks must never lower the bar"
    assert observed == sorted(observed, reverse=True), "more looks must never raise the DSR"
    assert table["combined"]["n_looks"] == 124 + 259 + gate.OWN_LOOKS


def test_the_pass_flag_agrees_with_the_required_sharpe():
    """The flag is what a reader acts on, so it is asserted rather than trusted to the
    comparison that produced it."""
    for sharpe in (0.2, 1.4, 1.75, 3.0):
        table = gate.dsr_table(sharpe, t=294_336, var_trials=0.18)
        for block in table.values():
            assert block["clears"] == (sharpe >= block["required_annual_sharpe"])


def test_a_higher_sharpe_can_clear_a_bar_a_lower_one_does_not():
    """Guards against a table that reports the same verdict whatever it is handed."""
    weak = gate.dsr_table(0.3, t=294_336, var_trials=0.18)
    strong = gate.dsr_table(4.0, t=294_336, var_trials=0.18)
    assert not any(b["clears"] for b in weak.values())
    assert all(b["clears"] for b in strong.values())

# ------------------------------------------------- the composition, which is the new risk

SHORT_FIELD = FieldParams(k=2, cluster_atr=0.5, erase=False, atr_window=200, vol_norm_bars=300)
"""The production field's windows are 1,920 and 8,640 bars, which would need tens of
thousands of synthetic bars to warm up. This shortens them so the CAUSALITY can be tested
in a unit test — the calendar match itself is asserted separately against the real
constants, so nothing is lost by not using them here."""


def _readings(bars, volumes, grid=None):
    """The production path, end to end: setups, trades, field, read at the signal bar.

    `grid` is injectable for the same reason `test_terrain_field.py` injects it — see
    `test_a_gate_decision_cannot_see_past_its_own_signal_bar`."""
    states = market_structure(bars, 2)
    setups = list(find_setups(bars, 2, 0.5, states=states, atr_window=200).setups)
    trades = run_arm(bars, setups, (), Wrapper(), allow_overlap=True)
    field = local_imbalance(
        bars,
        confirmed_swings(bars, volumes, SHORT_FIELD),
        SHORT_FIELD,
        grid or build_grid(bars, SHORT_FIELD.bucket_ln),
    )
    return trades, [field[t.entry_index - 1] for t in trades]


def _corrupt_after(bars, index, seed=17):
    rng = random.Random(seed)
    out = list(bars[: index + 1])
    px = bars[index].bar.close
    for i in range(index + 1, len(bars)):
        px *= math.exp(rng.gauss(0.0, 0.06))
        o, c = px, px * 1.02
        out.append(
            TimestampedBar(bars[i].timestamp, Bar(o, max(o, c) * 1.04, min(o, c) * 0.96, c))
        )
    return out


def test_a_gate_decision_cannot_see_past_its_own_signal_bar():
    """The load-bearing test in this file.

    The field has its own mutate-the-future pair and the detectors have theirs. Neither says
    anything about their COMPOSITION, and reading the field at `entry_index` instead of
    `entry_index - 1` is a one-character change no existing test can see — it would leak one
    bar into every gate decision and produce an entirely plausible equity curve, which is
    D173's warning exactly.
    """
    bars = wandering(2_400, seed=21)
    volumes = [1_000.0 + (i % 37) * 10.0 for i in range(len(bars))]

    grid = build_grid(bars, SHORT_FIELD.bucket_ln)
    trades, real = _readings(bars, volumes, grid)
    assert len(trades) > 30, "the fixture must produce a population worth asserting on"

    probe = 1_600
    fake_bars = _corrupt_after(bars, probe)
    # The SAME axis is passed to both arms, exactly as `test_terrain_field.py` does with
    # the comment "same axis, or the buckets alone would differ". `build_grid` spans the
    # whole series' high and low, so the price AXIS is not causal even though the field
    # walked on it is. Holding it fixed isolates the thing this test is about; the axis's
    # own non-causality is measured separately, in the test below.
    fake_trades, fake = _readings(fake_bars, volumes, grid)

    # Every trade whose SIGNAL bar is at or before the probe must be unchanged, in the
    # reading and in the resulting decision.
    checked = 0
    fake_by_entry = {t.entry_index: r for t, r in zip(fake_trades, fake)}
    for trade, reading in zip(trades, real):
        if trade.entry_index - 1 > probe:
            continue
        assert trade.entry_index in fake_by_entry, "a settled trade disappeared"
        assert fake_by_entry[trade.entry_index] == reading
        for want in (+1, -1):
            assert gate.gate_keeps(reading, trade.direction, want, 0.0) == gate.gate_keeps(
                fake_by_entry[trade.entry_index], trade.direction, want, 0.0
            )
        checked += 1
    assert checked > 10, f"only {checked} settled trades to check"


def test_the_corruption_actually_reaches_a_later_gate_decision():
    """The potency companion. A mutation test that changes nothing proves nothing, and
    `test_terrain_field.py` carries the same pair for the same reason: without this, the
    test above would pass just as well against a corruption that never bit."""
    bars = wandering(2_400, seed=21)
    volumes = [1_000.0 + (i % 37) * 10.0 for i in range(len(bars))]
    probe = 1_600

    grid = build_grid(bars, SHORT_FIELD.bucket_ln)
    trades, real = _readings(bars, volumes, grid)
    fake_trades, fake = _readings(_corrupt_after(bars, probe), volumes, grid)

    later_real = {t.entry_index: r for t, r in zip(trades, real) if t.entry_index - 1 > probe}
    later_fake = {t.entry_index: r for t, r in zip(fake_trades, fake) if t.entry_index - 1 > probe}
    shared = set(later_real) & set(later_fake)
    moved = sum(1 for k in shared if later_real[k] != later_fake[k])
    assert moved > 0 or later_real.keys() != later_fake.keys(), (
        "the corruption never reached a single later reading, so the guard above is vacuous"
    )

def test_the_price_axis_is_not_causal_and_that_does_not_move_a_gate_decision():
    """An inherited non-causality, measured rather than assumed away.

    `build_grid` spans the whole series: `ln_min` is the log of the lowest low and the
    bucket count follows the highest high. So the axis a reading is discretised onto knows
    the eventual price range, and a field computed on a prefix grid differs numerically
    from one computed on the full grid — at every bar, including early ones.

    `test_terrain_field.py` knew: its look-ahead test passes the same grid to both arms with
    the comment "same axis, or the buckets alone would differ". That is the right call for a
    *signal*, where the axis is a discretisation choice. It matters more for a **gate**,
    which reads only the SIGN — so the question is not whether the number moves but whether
    the sign does.

    It does not. The readings shift by ~0.04 on average and no decision flips. This is the
    number that says the inherited non-causality is immaterial to D214's verdict, and it is
    asserted rather than argued.
    """
    bars = wandering(2_400, seed=21)
    volumes = [1_000.0 + (i % 37) * 10.0 for i in range(len(bars))]
    probe = 1_600

    swings = confirmed_swings(bars, volumes, SHORT_FIELD)
    full = local_imbalance(bars, swings, SHORT_FIELD, build_grid(bars, SHORT_FIELD.bucket_ln))
    prefix = local_imbalance(
        bars, swings, SHORT_FIELD, build_grid(bars[: probe + 1], SHORT_FIELD.bucket_ln)
    )

    trades, _ = _readings(bars, volumes)
    settled = [t for t in trades if t.entry_index - 1 <= probe]
    assert len(settled) > 10

    # The axis really does move the number — otherwise this test proves nothing.
    moved = [abs(full[t.entry_index - 1] - prefix[t.entry_index - 1]) for t in settled]
    assert max(moved) > 1e-6, "the two grids produced identical readings; test is vacuous"

    # And it moves no decision, which is what the gate depends on.
    for t in settled:
        a, b = full[t.entry_index - 1], prefix[t.entry_index - 1]
        for want in (+1, -1):
            assert gate.gate_keeps(a, t.direction, want, 0.0) == gate.gate_keeps(
                b, t.direction, want, 0.0
            )
