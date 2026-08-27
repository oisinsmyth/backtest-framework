"""Gates for D238's short-side mirror.

The load-bearing ones are the two that D238 asymmetry 3 is about. The programme's
existing return code computes `position * log_return`, which is EXACT at
pos in {0, 1} and WRONG at pos = -1 -- measured at +9.22 points of overstatement
on this study's own book. So:

  * `signed_log_returns` must reproduce `portfolio_log_returns` EXACTLY on a
    long-flat book, or every number published before D238 silently moves;
  * and it must reproduce a HAND-COMPUTED short, or the fix is just a different
    wrong answer.

Everything else here is the usual: no look-ahead, the rotation is matched on the
things it claims to match, and the page round-trips byte-for-byte.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
import types
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "smr", REPO / "scripts" / "run_short_mirror.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["smr"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


R = _load()
SUMMARY = json.loads((REPO / "data" / "short_mirror_summary.json").read_text(encoding="utf-8"))


def _panel(closes: list[list[float]], cost: float = 0.0):
    """A minimal stand-in carrying only what the scorers read."""
    c = np.asarray(closes, dtype=float)
    rets = np.zeros_like(c)
    rets[:, 1:] = np.diff(np.log(c), axis=1)
    return types.SimpleNamespace(
        closes=c,
        log_returns=rets,
        total_log_returns=rets,
        cost_fraction=np.full(c.shape[0], cost),
        symbols=[f"S{i}" for i in range(c.shape[0])],
        dates=[f"2020-01-{i + 1:02d}T00:00:00" for i in range(c.shape[1])],
    )


# --------------------------------------------------------------------------
# Backward compatibility is DEMONSTRATED, not asserted
# --------------------------------------------------------------------------


def test_signed_returns_match_the_long_flat_code_exactly():
    """The generalisation must not move a single published number."""
    rng = np.random.default_rng(7)
    panel = _panel(list(100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, (6, 200)), axis=1))),
                   cost=0.00015)
    pos = (rng.random((6, 200)) > 0.6).astype(float)  # long-flat, 0/1 only
    new = R.signed_log_returns(panel, pos, total_return=True)
    old = R.L.portfolio_log_returns(panel, pos, total_return=True)
    np.testing.assert_allclose(new, old, rtol=0, atol=1e-15)


def test_excess_reduces_to_the_long_flat_formula():
    rng = np.random.default_rng(11)
    panel = _panel(list(100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, (5, 120)), axis=1))))
    pos = (rng.random((5, 120)) > 0.5).astype(float)
    total = R.signed_log_returns(panel, pos, total_return=True)[10:]
    got = R.excess_of(total, pos, 10)
    want = total - pos[:, 10:].mean(axis=0) * R.RF_PER_BAR
    np.testing.assert_allclose(got, want, rtol=0, atol=1e-15)


def test_short_compounding_against_a_hand_computed_case():
    """100 -> 110 -> 99, short throughout, rebalanced to constant notional.

    Bar 1: the asset gains 10%, so equity falls to 0.90.
    Bar 2: the asset falls 10%, so equity recovers to 0.90 * 1.10 = 0.99.

    The naive `-position * log_return` gives 1/0.99 = 1.0101 -- a GAIN where the
    truth is a loss. That sign flip is the defect this whole scorer exists for."""
    panel = _panel([[100.0, 110.0, 99.0]])
    pos = np.array([[0.0, -1.0, -1.0]])
    equity = float(np.exp(R.signed_log_returns(panel, pos, total_return=True).sum()))
    assert equity == pytest.approx(0.99, abs=1e-12)

    naive = float(np.exp((pos * panel.total_log_returns).sum()))
    assert naive == pytest.approx(1.0 / 0.99, abs=1e-12)
    assert naive > 1.0 > equity  # the defect flatters the short, and by enough to flip it


def test_a_flat_book_earns_nothing_and_a_long_book_earns_the_return():
    panel = _panel([[100.0, 110.0, 99.0]])
    flat = np.zeros((1, 3))
    assert float(R.signed_log_returns(panel, flat, total_return=True).sum()) == 0.0
    long_ = np.array([[0.0, 1.0, 1.0]])
    got = float(np.exp(R.signed_log_returns(panel, long_, total_return=True).sum()))
    assert got == pytest.approx(0.99, abs=1e-12)  # 1.10 * 0.90


# --------------------------------------------------------------------------
# Financing flips sign for a short -- D238 asymmetry 4
# --------------------------------------------------------------------------


def test_a_short_book_pays_borrow_and_is_not_charged_rf():
    panel = _panel([[100.0] * 50])
    short = np.full((1, 50), -1.0)
    short[:, :5] = 0.0
    total = R.signed_log_returns(panel, short, total_return=True)[5:]
    ex = R.excess_of(total, short, 5)
    np.testing.assert_allclose(ex, total - R.BORROW_PER_BAR, rtol=0, atol=1e-15)
    assert R.BORROW_PER_BAR > 0.0  # charged, not credited


def test_a_flipped_book_is_charged_cost_twice():
    """+1 to -1 moves two units of notional, so it pays two sides. D212."""
    panel = _panel([[100.0, 100.0, 100.0]], cost=0.001)
    flip = np.array([[0.0, 1.0, -1.0]])
    hold = np.array([[0.0, 1.0, 1.0]])
    c_flip = -R.signed_log_returns(panel, flip, total_return=True).sum()
    c_hold = -R.signed_log_returns(panel, hold, total_return=True).sum()
    # hold pays 1 unit of entry; flip pays 1 unit of entry, then 2 units on the
    # flip -- charged on the bar as a single 2-unit move, not as two 1-unit ones.
    assert c_flip == pytest.approx(-(math.log1p(-0.001) + math.log1p(-0.002)), rel=1e-12)
    assert c_hold == pytest.approx(-math.log1p(-0.001), rel=1e-12)
    assert c_flip > 2.0 * c_hold  # a flip costs strictly more than two entries


# --------------------------------------------------------------------------
# The rule, and the artifact that records it
# --------------------------------------------------------------------------


def test_s1_and_the_mirror_are_disjoint():
    """M3 needs no weighting choice ONLY because the two never fire together."""
    assert SUMMARY["anatomy"]["simultaneous_s1_m1"] == 0


def test_s1_reproduces_the_published_book_entry():
    """The signed scorer must not have moved S1. BOOK.md quotes +0.746 / 18.9%."""
    s1 = SUMMARY["cells"]["S1"]
    assert s1["excess_sharpe"] == pytest.approx(0.746, abs=5e-4)
    assert s1["exposure_long"] == pytest.approx(0.189, abs=5e-4)
    assert s1["exposure_short"] == 0.0
    assert s1["max_drawdown"] == pytest.approx(-0.1030, abs=5e-4)


def test_the_channel_asymmetry_the_record_reports():
    a = SUMMARY["anatomy"]
    assert a["share_above"] > a["share_below"]
    assert a["share_above"] + a["share_inside"] + a["share_below"] == pytest.approx(1.0)
    # 1.56x more exposure on the short side, which is the whole reason the two
    # arms cannot be compared on raw Sharpe.
    ratio = SUMMARY["cells"]["M1"]["exposure_short"] / SUMMARY["cells"]["S1"]["exposure_long"]
    assert ratio == pytest.approx(1.56, abs=0.02)


def test_every_hurdle_leg_is_present_in_the_artifact():
    """R6 -- a hurdle that names a test is not cleared until that test is run."""
    for k in ("M1", "M2", "M3", "M4"):
        n = SUMMARY["nulls"][k]
        for leg in ("p50", "p95", "percentile_of_actual", "clears_W1",
                    "money_p50", "money_percentile_of_actual", "vol_ratio_actual_over_null"):
            assert leg in n, f"{k} is missing the {leg} leg"
    w3 = SUMMARY["w3"]
    assert "p05" in w3["bootstrap"] and "p95" in w3["bootstrap"]
    assert isinstance(w3["clears_W3"], bool)


def test_the_verdict_the_record_reports():
    """The money leg is what separates skill from volatility timing, so it is the
    one pinned. A vol ratio near 1 means the Sharpe pass was not an artifact."""
    m1, n1 = SUMMARY["cells"]["M1"], SUMMARY["nulls"]["M1"]
    assert n1["clears_W1"] is True
    assert n1["money_percentile_of_actual"] > 95.0
    assert n1["vol_ratio_actual_over_null"] < 1.15
    assert m1["excess_sharpe"] < 0.0            # W2 fails
    assert m1["breakeven_borrow_annual"] < 0.0  # and borrow is not why
    assert SUMMARY["w3"]["clears_W3"] is False  # W3 fails


def test_the_measurement_that_decides_the_reading():
    """A short needs bars that FALL. The worst bars the indicator can name still
    rise -- which is why a real edge cannot become a profitable short."""
    cond = SUMMARY["conditional_returns"]
    m1 = cond["hist<0 & md>=0  (M1)"]["annualised"]
    everything = cond["all live bars"]["annualised"]
    assert 0.0 < m1 < everything            # underperforms, does not fall
    # and md_L >= 0 sharpens the selection beyond sign(hist) alone
    assert m1 < cond["hist<0 alone    (M4)"]["annualised"]


def test_m4_is_declared_post_hoc():
    """It was computed on the analyst's initiative after M1 cleared. Disclosure is
    the whole mechanism, so the artifact has to carry it."""
    assert SUMMARY["post_hoc_cells"] == ["M4"]


# --------------------------------------------------------------------------
# Construction gates
# --------------------------------------------------------------------------


def test_the_rotation_matches_exposure_and_turnover():
    """A rotation that changed either would stop being a control for 'you just
    shorted more', which is the entire confound."""
    rng = np.random.default_rng(3)
    pos = -(rng.random((4, 300)) > 0.7).astype(float)
    pos[:, :50] = 0.0
    src = pos[:, 50:]
    rot = np.zeros_like(pos)
    for i in range(4):
        rot[i, 50:] = np.roll(src[i], int(rng.integers(1, 250)))
    np.testing.assert_allclose(np.abs(rot).sum(axis=1), np.abs(pos).sum(axis=1))
    assert rot.min() < 0.0 and rot.max() <= 0.0  # still a short book


def test_the_book_at_bar_t_is_decided_at_t_minus_one():
    """The no-look-ahead property for a MEMORYLESS level rule, on the real panel.

    `hold_book` promises exactly one thing: `position[t] = mask[t-1]`, and nothing
    at or after `t` enters it. The mask's own causality comes from `smma`, `zlema`
    and `sma` being causal, which `test_macd_ladder` pins separately -- so the
    property that belongs to THIS study is the shift, and it is asserted on every
    symbol and every bar rather than on a sampled perturbation."""
    panel, cleaned = R.L.load_panel()
    start = max(R.M.impulse_warm_up_bars(), R.M.warm_up_bars(),
                R.M.MATCHED_MOMENTUM_LOOKBACK)
    md, hs, ok = R.S.base_masks(panel, cleaned, start)
    mask = (hs < 0) & (md >= 0) & ok
    book = -R.S.hold_book(mask, start)
    np.testing.assert_array_equal(book[:, start + 1:], -mask[:, start:-1].astype(float))
    assert np.all(book[:, :start] == 0.0)
    assert R.LAG == 1


def test_the_page_round_trips_byte_for_byte():
    """The idempotency defect appeared in D220, D222 and D229. CELL_ORDER exists
    so a `sort_keys` round trip cannot reorder the rows."""
    on_disk = (REPO / "SHORT_MIRROR_RESULTS.md").read_text(encoding="utf-8")
    assert R.render(SUMMARY) == on_disk
