"""Unit tests for the Allocator stand-in (D31), per VERIFICATION_SCHEME.md Step 4.

Also proves the loop D55 (Step 3) explicitly left open: ConstantSplitAllocator's output
plugs directly into pipeline.sizing.Sizer's capital_by_strategy parameter, unmodified.
"""

from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.instruments.equity import Equity
from backtest_framework.pipeline.sizing import Sizer, TargetWeight


def test_constant_split_sums_to_total_capital_across_n_strategies():
    allocator = ConstantSplitAllocator()
    shares = allocator.allocate(total_capital=300_000.0, strategy_ids=["a", "b", "c"])

    assert shares == {"a": 100_000.0, "b": 100_000.0, "c": 100_000.0}
    assert sum(shares.values()) == 300_000.0
    assert sum(v / 300_000.0 for v in shares.values()) == 1.0


def test_constant_split_with_empty_strategy_list_is_empty():
    allocator = ConstantSplitAllocator()
    assert allocator.allocate(total_capital=100_000.0, strategy_ids=[]) == {}


def test_capital_changes_propagate_on_next_call():
    allocator = ConstantSplitAllocator()  # stateless — nothing cached between calls

    first = allocator.allocate(total_capital=100_000.0, strategy_ids=["a", "b"])
    assert first == {"a": 50_000.0, "b": 50_000.0}

    second = allocator.allocate(total_capital=200_000.0, strategy_ids=["a", "b"])
    assert second == {"a": 100_000.0, "b": 100_000.0}  # reflects the new total immediately


# --- Wiring proof: Allocator output feeds Sizer.capital_by_strategy unmodified --------


def test_allocator_output_feeds_sizer_capital_by_strategy_unmodified():
    allocator = ConstantSplitAllocator()
    sizer = Sizer()
    aapl = Equity(symbol="AAPL")

    capital_by_strategy = allocator.allocate(total_capital=200_000.0, strategy_ids=["momentum", "pairs"])

    targets = [
        TargetWeight(strategy_id="momentum", instrument_id="AAPL", weight=0.5),
        TargetWeight(strategy_id="pairs", instrument_id="AAPL", weight=-0.2),
    ]
    virtual_orders = sizer.size_targets(
        targets,
        current_positions={},
        capital_by_strategy=capital_by_strategy,  # straight from the Allocator, no glue code
        prices={"AAPL": 100.0},
        instruments={"AAPL": aapl},
    )

    # momentum: 0.5 * 100,000 / 100 = 500 shares; pairs: -0.2 * 100,000 / 100 = -200 shares
    assert virtual_orders[("momentum", "AAPL")].quantity == 500.0
    assert virtual_orders[("pairs", "AAPL")].quantity == -200.0
