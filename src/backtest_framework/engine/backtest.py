"""run_backtest: the production loop generalizing Step 3's test-only mini-backtest.

Wires together, per bar: carry accrual (D33) -> a DataView per strategy (D32) ->
signal -> target weight -> orders (D27, pipeline.sizing) -> cost application
(CostStack, D1/D2) -> PortfolioState updates -> a per-bar risk check (D30) -> an
equity-curve point.

Single instrument only for now — bars is one price series. Multi-instrument alignment
(D45, e.g. a real XLE/XOP pair) is bigger scope than this chunk covers; see D59.

Capital is reallocated from current NAV every bar (D61), not fixed at the start.
RiskMonitor violations are recorded in the result, not acted on — no corrective orders
or halting are implemented here (D62); a caller inspecting BacktestResult.violations is
the only enforcement that exists right now.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, Sequence

from ..costs.stack import CostStack
from ..data.bars import TimestampedBar
from ..instruments.base import Instrument
from ..pipeline.sizing import Sizer, TargetWeight, apply_virtual_orders, net_orders
from ..registry.trial_registry import TrialRegistry
from .allocator import Allocator
from .dataview import build_data_view
from .portfolio import PortfolioState
from .risk import RiskLimits, RiskMonitor, RiskViolation
from .strategy import Strategy


@dataclass
class BacktestResult:
    equity_curve: list[tuple[datetime, float]] = field(default_factory=list)
    violations: list[RiskViolation] = field(default_factory=list)
    final_positions: dict[str, float] = field(default_factory=dict)
    final_cash: float = 0.0

    @property
    def final_nav(self) -> float:
        return self.equity_curve[-1][1] if self.equity_curve else self.final_cash


def run_backtest(
    bars: Sequence[TimestampedBar],
    instrument_id: str,
    instruments: Mapping[str, Instrument],
    strategies: list[Strategy],
    cost_stack: CostStack,
    allocator: Allocator,
    starting_cash: float,
    risk_limits: RiskLimits | None = None,
    trial_registry: TrialRegistry | None = None,
    trial_id: str | None = None,
    config: dict | None = None,
    snapshot_id: str = "unspecified",
    seed: int = 0,
) -> BacktestResult:
    if trial_registry is not None and (trial_id is None or config is None):
        raise ValueError(
            "trial_registry was given but trial_id and/or config was not — "
            "pass both, or omit trial_registry if you don't want this run logged."
        )

    all_bars = tuple(tb.bar for tb in bars)
    sizer = Sizer()
    risk_monitor = RiskMonitor(risk_limits) if risk_limits is not None else None

    portfolio = PortfolioState(cash=starting_cash)
    virtual_positions: dict[tuple[str, str], float] = {}
    strategy_ids = [s.strategy_id for s in strategies]

    result = BacktestResult()
    prev_timestamp: datetime | None = None

    for i, tb in enumerate(bars):
        price = tb.bar.close
        prices = {instrument_id: price}

        # 1. Carry accrues on the position held coming into this bar (D33), on the
        #    calendar-day gap since the previous bar, before any trade this bar.
        current_qty = portfolio.positions.get(instrument_id, 0.0)
        if prev_timestamp is not None and current_qty != 0:
            base_amount = current_qty * price
            carry = cost_stack.carry_cost(base_amount, prev_timestamp, tb.timestamp)
            portfolio.accrue_carry(carry)

        # 2. Build this bar's DataView (D32, D56) and let every strategy see it —
        #    never the raw bar series.
        view = build_data_view(all_bars, i)
        targets: list[TargetWeight] = []
        for strategy in strategies:
            targets.extend(strategy.generate_targets(view))

        # 3. Capital is reallocated from current NAV every bar (D61).
        current_nav = portfolio.nav(prices, instruments)
        capital_by_strategy = allocator.allocate(current_nav, strategy_ids)

        # 4. Signal -> target weight -> orders (D27): size, net, update virtual books.
        virtual_orders = sizer.size_targets(
            targets,
            current_positions=virtual_positions,
            capital_by_strategy=capital_by_strategy,
            prices=prices,
            instruments=instruments,
        )
        external_orders = net_orders(virtual_orders)
        virtual_positions = apply_virtual_orders(virtual_positions, virtual_orders)

        # 5. Apply the broker-facing (netted) fill, if any, with its trade cost.
        order = external_orders.get(instrument_id)
        if order is not None and order.quantity != 0:
            trade_cost = cost_stack.trade_cost(instruments[instrument_id], order.quantity, price)
            portfolio.apply_fill(instrument_id, order.quantity, price, trade_cost)

        # 6. Per-bar risk check (D30), regardless of whether an order fired this bar.
        if risk_monitor is not None:
            violation = risk_monitor.evaluate(portfolio.positions, prices, instruments, bar_index=i)
            if violation is not None:
                result.violations.append(violation)

        result.equity_curve.append((tb.timestamp, portfolio.nav(prices, instruments)))
        prev_timestamp = tb.timestamp

    result.final_positions = dict(portfolio.positions)
    result.final_cash = portfolio.cash

    if trial_registry is not None:
        metrics = {
            "final_nav": result.final_nav,
            "total_return": result.final_nav - starting_cash,
            "num_bars": len(bars),
            "num_violations": len(result.violations),
        }
        trial_registry.add_trial(
            trial_id=trial_id,  # type: ignore[arg-type]
            config=config,  # type: ignore[arg-type]
            params={},
            metrics=metrics,
            snapshot_id=snapshot_id,
            seed=seed,
        )

    return result
