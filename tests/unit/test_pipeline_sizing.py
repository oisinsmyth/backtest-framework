"""Unit + golden tests for the signal -> target weight -> orders pipeline (D27, D46),
per VERIFICATION_SCHEME.md Step 3.
"""

from backtest_framework.instruments.equity import Equity
from backtest_framework.pipeline.sizing import Order, Sizer, TargetWeight, apply_virtual_orders, net_orders

AAPL = Equity(symbol="AAPL")
INSTRUMENTS = {"AAPL": AAPL}
PRICES = {"AAPL": 100.0}


def test_target_weights_on_known_portfolio_produce_exact_expected_orders():
    # Strategy "s1" starts flat, wants 50% of $100,000 capital in AAPL @ $100.
    sizer = Sizer()
    targets = [TargetWeight(strategy_id="s1", instrument_id="AAPL", weight=0.5)]
    current_positions: dict[tuple[str, str], float] = {}
    capital_by_strategy = {"s1": 100_000.0}

    virtual_orders = sizer.size_targets(targets, current_positions, capital_by_strategy, PRICES, INSTRUMENTS)

    # desired_notional = 0.5 * 100,000 = 50,000; raw_qty = 50,000 / 100 = 500 (whole shares)
    assert virtual_orders == {("s1", "AAPL"): Order("AAPL", 500.0)}

    external_orders = net_orders(virtual_orders)
    assert external_orders == {"AAPL": Order("AAPL", 500.0)}


def test_already_at_target_produces_zero_orders():
    sizer = Sizer()
    targets = [TargetWeight(strategy_id="s1", instrument_id="AAPL", weight=0.5)]
    current_positions = {("s1", "AAPL"): 500.0}  # already holding the target quantity
    capital_by_strategy = {"s1": 100_000.0}

    virtual_orders = sizer.size_targets(targets, current_positions, capital_by_strategy, PRICES, INSTRUMENTS)

    assert virtual_orders == {}
    assert net_orders(virtual_orders) == {}


def test_offsetting_strategies_net_to_zero_external_orders_but_both_books_update():
    # Strategy A wants +10 shares of AAPL it doesn't currently hold; strategy B wants to
    # go from +10 to 0 (i.e. sell 10). Their external footprint should cancel exactly,
    # even though each strategy individually "traded".
    sizer = Sizer()
    # A: weight 1.0 * capital 1,000 / price 100 = 10 shares, current 0 -> delta +10.
    # B: weight 0.0 (exit) * capital 1,000 / price 100 = 0 shares, current 10 -> delta -10.
    current_positions = {("A", "AAPL"): 0.0, ("B", "AAPL"): 10.0}
    capital_by_strategy = {"A": 1_000.0, "B": 1_000.0}
    targets = [
        TargetWeight(strategy_id="A", instrument_id="AAPL", weight=1.0),
        TargetWeight(strategy_id="B", instrument_id="AAPL", weight=0.0),
    ]

    virtual_orders = sizer.size_targets(targets, current_positions, capital_by_strategy, PRICES, INSTRUMENTS)

    assert virtual_orders == {
        ("A", "AAPL"): Order("AAPL", 10.0),
        ("B", "AAPL"): Order("AAPL", -10.0),
    }

    external_orders = net_orders(virtual_orders)
    assert external_orders == {}  # zero net external orders (D27)

    updated_positions = apply_virtual_orders(current_positions, virtual_orders)
    assert updated_positions[("A", "AAPL")] == 10.0  # A's virtual book reflects its own buy
    assert updated_positions[("B", "AAPL")] == 0.0  # B's virtual book reflects its own sell


def test_same_sizer_drives_two_different_strategies_unmodified():
    sizer = Sizer()  # a single, stateless Sizer instance
    targets = [
        TargetWeight(strategy_id="momentum", instrument_id="AAPL", weight=0.3),
        TargetWeight(strategy_id="pairs", instrument_id="AAPL", weight=-0.2),  # short leg
    ]
    current_positions: dict[tuple[str, str], float] = {}
    capital_by_strategy = {"momentum": 100_000.0, "pairs": 50_000.0}

    virtual_orders = sizer.size_targets(targets, current_positions, capital_by_strategy, PRICES, INSTRUMENTS)

    assert virtual_orders[("momentum", "AAPL")] == Order("AAPL", 300.0)  # 0.3*100,000/100
    assert virtual_orders[("pairs", "AAPL")] == Order("AAPL", -100.0)  # -0.2*50,000/100
