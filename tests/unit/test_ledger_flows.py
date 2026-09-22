"""`backtest_framework.ledger.flows` -- Section 4's participant flow terms (D610).

Covers the settlement flow ledger's required unit tests 2 (line 708), 3 (line 709), 12
(line 718) and 47 (line 753). The hand-worked cases for numbers 1 and 6 live in
`tests/golden/test_ledger_flows_ledger.py`, beside their arithmetic.

Offline: no fixture, no network, no strategy return. Every input is synthetic or typed from
the deposit document's own worked examples.
"""

from __future__ import annotations

import math

import pytest

from backtest_framework.ledger.flows import (
    FlowTerm,
    LARGE_LOT_LOOKBACK_DAYS,
    LedgerError,
    aggregate,
    held_months,
    held_return,
    is_large,
    large_lot_threshold,
    q1_notional,
    q1_rebalance,
    q2_swap,
    route,
    var_q1,
)

AUM = 1e9
MULT, PRICE = 10_000.0, 3.00


def _sizes(days: int = LARGE_LOT_LOOKBACK_DAYS, start: int = 1) -> dict[str, list[float]]:
    """`days` consecutive January days, each carrying the ten trade sizes 1..10 lots."""
    return {f"2026-01-{start + i:02d}": [float(v) for v in range(1, 11)] for i in range(days)}


# --------------------------------------------------------------------------- the return


def test_held_return_is_the_documents_line_146() -> None:
    # 3.3/3.0 - 1 is 0.09999999999999987, not 0.1: neither operand is a binary fraction and
    # the subtraction of 1 cancels the leading bits. Pinned as the double it is, because a
    # test written as `== 0.1` would be asserting a number this formula cannot produce.
    assert held_return(3.30, 3.00) == 0.09999999999999987
    assert held_return(3.00, 3.00) == 0.0
    assert held_return(1.50, 3.00) == -0.5  # exact
    for bad in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(LedgerError):
            held_return(bad, 3.0)
        with pytest.raises(LedgerError):
            held_return(3.0, bad)


# ------------------------------------------------------------------- required unit test 2


def test_ledger_2_l_plus_one_funds_contribute_zero_rebalance_flow() -> None:
    """Line 708: "L = +1 funds contribute zero rebalance flow."

    The coefficient is L(L-1), which is 0 at L = 1 for EVERY AUM, return and futures share --
    so the assertion sweeps them rather than picking one triple. UNG and USO are the L = +1
    funds of table 3.1 and are in the universe for creations only (line 64: "Creations only
    (L(L-1) = 0)").
    """
    for aum in (0.0, 1e6, 1e9, 4.2e10):
        for r in (-0.37, -0.05, 0.0, 0.05, 0.19):
            for f in (0.0, 0.31, 1.0):
                assert q1_notional(aum, 1.0, r, f) == 0.0
                assert q1_rebalance(aum, 1.0, r, f, MULT, PRICE) == 0.0
                assert q2_swap(aum, 1.0, r, f, 0.0, MULT, PRICE) == 0.0
    # L = 0 is the coefficient's other root and gives zero for the same reason.
    assert q1_notional(AUM, 0.0, 0.05, 1.0) == 0.0
    # The variance term vanishes with it: a fund that never rebalances carries no rebalance
    # uncertainty, which is line 160 read at L = 1.
    assert var_q1(AUM, 1.0, 1.0, 0.02) == 0.0
    # ... while an L = -2 fund at the same AUM does not.
    assert var_q1(AUM, -2.0, 1.0, 0.02) > 0.0


# ------------------------------------------------------------------- required unit test 3


def test_ledger_3_f_fut_routes_wholly_to_p1_or_to_p2() -> None:
    """Line 709: "`f_fut = 0` routes all rebalance to P2; `f_fut = 1` routes all to P1."

    Both endpoints are EXACT and are asserted with `==`. The interior is one ulp wide and is
    measured in the golden, not here.
    """
    total = q1_rebalance(AUM, -2.0, 0.05, 1.0, MULT, PRICE)

    q1, q2 = route(AUM, -2.0, 0.05, 1.0, 0.0, MULT, PRICE)
    assert q1 == total and q2 == 0.0

    q1, q2 = route(AUM, -2.0, 0.05, 0.0, 0.0, MULT, PRICE)
    assert q1 == 0.0 and q2 == total

    # Netting scales only P2, and n = 1 removes it entirely (line 168).
    q1, q2 = route(AUM, -2.0, 0.05, 0.0, 1.0, MULT, PRICE)
    assert q1 == 0.0 and q2 == 0.0
    q1, q2 = route(AUM, -2.0, 0.05, 0.0, 0.5, MULT, PRICE)
    assert q2 == total * 0.5

    # n is ASSERTED into [0, 1] (Section 8's constraint), never clipped: a fitted n outside
    # the range is a fitting failure, and clipping would launder it into a plausible flow.
    for bad_n in (-0.01, 1.01, float("nan")):
        with pytest.raises(LedgerError):
            q2_swap(AUM, -2.0, 0.05, 0.5, bad_n, MULT, PRICE)
    for bad_f in (-0.01, 1.01):
        with pytest.raises(LedgerError):
            route(AUM, -2.0, 0.05, bad_f, 0.0, MULT, PRICE)


def test_var_q1_refuses_half_a_unit_conversion() -> None:
    """Line 160 is in notional squared and line 156 is in contracts; the caller must choose.

    The document never reconciles them and Section 5.1 sums both into quantities Section 5.2
    divides, so the conversion is explicit at the call site or it does not happen.
    """
    notional_sq = var_q1(AUM, -2.0, 1.0, 0.02)
    assert notional_sq == (AUM * 6.0 * 1.0) ** 2 * 0.02**2
    contracts_sq = var_q1(AUM, -2.0, 1.0, 0.02, multiplier=MULT, p_held=PRICE)
    assert contracts_sq == notional_sq / (MULT * PRICE) ** 2
    with pytest.raises(LedgerError, match="Half a conversion"):
        var_q1(AUM, -2.0, 1.0, 0.02, multiplier=MULT)
    with pytest.raises(LedgerError, match="Half a conversion"):
        var_q1(AUM, -2.0, 1.0, 0.02, p_held=PRICE)
    with pytest.raises(LedgerError, match="standard deviation"):
        var_q1(AUM, -2.0, 1.0, -0.02)


# --------------------------------------------------------------------------- aggregation


def test_aggregate_sums_only_active_terms_and_is_order_independent() -> None:
    """Section 5.1 lines 361-362, with `math.fsum` so the total does not depend on an order."""
    terms = [
        FlowTerm("P1", 1200.0, 400.0),
        FlowTerm("P2", -300.0, 900.0),
        FlowTerm("P5", 50.0, 25.0),
        FlowTerm("P8b", 999.0, 1e6, active=False),
    ]
    mu, var = aggregate(terms)
    assert mu == 950.0
    assert var == 1325.0
    assert aggregate(list(reversed(terms))) == (mu, var)

    with pytest.raises(LedgerError, match="appears twice"):
        aggregate([FlowTerm("P1", 1.0, 1.0), FlowTerm("P1", 2.0, 1.0)])
    with pytest.raises(LedgerError, match="negative variance"):
        aggregate([FlowTerm("P1", 1.0, -1.0)])
    with pytest.raises(LedgerError, match="no active terms"):
        aggregate([FlowTerm("P1", 1.0, 1.0, active=False)])


# ------------------------------------------------------------------ required unit test 12


def test_ledger_12_flow_lands_on_the_held_months_never_the_front() -> None:
    """Line 718: "flow is attributed to the held contract months per holdings, not the front
    month by default."

    Hand file case 6. The weights are exact here because 300/400 and 100/400 are binary
    fractions, so the assertions are `==`.
    """
    w = held_months({"2026-04": 300.0, "2026-05": 100.0})
    assert w == {"2026-04": 0.75, "2026-05": 0.25}
    assert math.fsum(w.values()) == 1.0

    # An inverse fund is short both months; the weights are identical, because the DIRECTION
    # of the flow is carried by L(L-1) and by r and taking it from holdings too would double
    # it. Same weights, opposite position.
    assert held_months({"2026-04": -300.0, "2026-05": -100.0}) == w

    # A fund holding the SECOND nearby only -- WisdomTree's NG index, line 289 -- puts all of
    # its flow there, and nothing puts any of it on the front month.
    assert held_months({"2026-05": 812.0}) == {"2026-05": 1.0}

    # A predicted flow splits by those weights.
    flow = 400.0
    assert {m: flow * s for m, s in w.items()} == {"2026-04": 300.0, "2026-05": 100.0}

    with pytest.raises(LedgerError, match="no front-month default"):
        held_months({"2026-04": 1.0}, default_to_front=True)
    with pytest.raises(LedgerError, match="empty holdings"):
        held_months({})
    with pytest.raises(LedgerError, match="both signs"):
        held_months({"2026-04": 300.0, "2026-05": -100.0})
    with pytest.raises(LedgerError, match="every holding is zero"):
        held_months({"2026-04": 0.0, "2026-05": 0.0})


# ------------------------------------------------------------------ required unit test 47


def test_ledger_47_large_lot_threshold_is_prior_days_only_and_ties_count_as_large() -> None:
    """Line 753: "Large-lot threshold uses the trailing 20 prior days only; trades exactly at
    L_min count as large."

    Hand file case 5: 20 prior days x the sizes 1..10 pools 200 trades, nearest rank
    ceil(0.9 x 200) = 180, and the 180th smallest is the last of the twenty 9s.
    """
    prior = _sizes()
    assert len(prior) == 20
    l_min = large_lot_threshold(prior, "2026-02-01")
    assert l_min == 9.0

    # The tie clause, which is the whole of line 753's second half.
    assert is_large(9.0, l_min) is True
    assert is_large(8.99, l_min) is False
    assert is_large(10.0, l_min) is True

    # A same-day trade RAISES rather than being filtered away -- `depth_bar`'s refusal shape.
    leaked = dict(prior)
    leaked["2026-02-01"] = [500.0]
    with pytest.raises(LedgerError, match="PRIOR days only"):
        large_lot_threshold(leaked, "2026-02-01")
    # ... and so does a FUTURE day, which is the same defect arriving from further away.
    leaked2 = dict(prior)
    leaked2["2026-03-01"] = [500.0]
    with pytest.raises(LedgerError, match="at or after"):
        large_lot_threshold(leaked2, "2026-02-01")

    # A short window raises: "a warm-up period becomes a result".
    with pytest.raises(LedgerError, match="only 19 prior day"):
        large_lot_threshold(_sizes(days=19), "2026-02-01")

    # Exactly 20 of a longer history are used, and the extra older days do not change L_min.
    longer = _sizes(days=25)
    assert large_lot_threshold(longer, "2026-02-01") == 9.0

    for bad in (0.0, -3.0, float("nan")):
        broken = dict(prior)
        broken["2026-01-05"] = [bad]
        with pytest.raises(LedgerError):
            large_lot_threshold(broken, "2026-02-01")
    with pytest.raises(LedgerError, match="quantile"):
        large_lot_threshold(prior, "2026-02-01", quantile=1.5)
    with pytest.raises(LedgerError, match="lookback_days must be positive"):
        large_lot_threshold(prior, "2026-02-01", 0)


def test_large_lot_threshold_nearest_rank_returns_an_observed_size() -> None:
    """The percentile convention is a CHOICE and this is what it buys.

    Nearest rank returns a size some trade actually had; linear interpolation between order
    statistics does not, and line 753's tie clause is a claim about a real trade.
    """
    pool = {f"2026-01-{i + 1:02d}": [1.0, 2.0, 3.0, 4.0, 100.0] for i in range(20)}
    l_min = large_lot_threshold(pool, "2026-02-01")
    observed = {v for sizes in pool.values() for v in sizes}
    assert l_min in observed
    # 100 trades, rank ceil(90) = 90; ranks 81..100 are the twenty 100s, so rank 90 is 100.
    assert l_min == 100.0
    assert is_large(100.0, l_min) is True
