"""run_backtest: the production loop generalizing Step 3's test-only mini-backtest.

Wires together, per aligned bar: carry accrual on every held position (D33) -> a
DataView per instrument per strategy (D32) -> signal -> target weight -> orders (D27,
pipeline.sizing) -> cost application (CostStack, D1/D2) -> PortfolioState updates -> a
per-bar risk check (D30) -> an equity-curve point.

Multi-instrument via inner-join alignment (D45, data.alignment.align_bars) — one
instrument is the N=1 case (D64), same as Strategy. A bar missing on one leg means no
trading for any leg that step; carry still accrues across the real calendar gap,
because it's driven by consecutive aligned timestamps, not bar count. Carry accrues
per instrument independently (each leg's own notional as its own base amount) — not
netted against aggregate gross exposure; that's D5's job in Step 5, not this chunk.

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
from ..data.alignment import align_bars
from ..data.bars import TimestampedBar
from ..instruments.base import Instrument
from ..pipeline.sizing import Sizer, TargetWeight, apply_virtual_orders, net_orders
from ..registry.trial_registry import TrialRegistry
from .allocator import Allocator
from .dataview import DataView, build_data_view
from .portfolio import PortfolioState
from .risk import RiskLimits, RiskMonitor, RiskViolation, gross_exposure
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
    bars_by_instrument: Mapping[str, Sequence[TimestampedBar]],
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
    splits_by_instrument: Mapping[str, Sequence[tuple[datetime, float]]] | None = None,
    view_bars_by_instrument: Mapping[str, Sequence[TimestampedBar]] | None = None,
) -> BacktestResult:
    """`bars_by_instrument` is the EXECUTION series (raw prices — fills, commissions,
    carry, NAV all use it, per D6). `view_bars_by_instrument`, when given, is what
    strategies see instead (e.g. split-adjusted for signal continuity, D75); it must
    cover every aligned execution timestamp. `splits_by_instrument` scales broker and
    virtual positions on ex-dates (D75)."""
    if trial_registry is not None and (trial_id is None or config is None):
        raise ValueError(
            "trial_registry was given but trial_id and/or config was not — "
            "pass both, or omit trial_registry if you don't want this run logged."
        )

    aligned = align_bars(bars_by_instrument)  # D45
    aligned_bar_series = {
        instrument_id: tuple(ab.bars[instrument_id] for ab in aligned) for instrument_id in bars_by_instrument
    }

    # Strategy views come from the view series when given (split-adjusted signals),
    # aligned 1:1 with execution timestamps — a missing timestamp is a loud error,
    # never a silently substituted raw bar (D75).
    if view_bars_by_instrument is not None:
        view_lookup = {
            instrument_id: {tb.timestamp: tb.bar for tb in series}
            for instrument_id, series in view_bars_by_instrument.items()
        }
        try:
            view_bar_series = {
                instrument_id: tuple(view_lookup[instrument_id][ab.timestamp] for ab in aligned)
                for instrument_id in bars_by_instrument
            }
        except KeyError as exc:
            raise ValueError(
                f"view_bars_by_instrument is missing a bar for an aligned execution timestamp: {exc}"
            ) from exc
    else:
        view_bar_series = aligned_bar_series

    splits_by_instrument = splits_by_instrument or {}

    sizer = Sizer()
    risk_monitor = RiskMonitor(risk_limits) if risk_limits is not None else None

    portfolio = PortfolioState(cash=starting_cash)
    virtual_positions: dict[tuple[str, str], float] = {}
    strategy_ids = [s.strategy_id for s in strategies]

    result = BacktestResult()
    prev_timestamp: datetime | None = None

    for i, ab in enumerate(aligned):
        prices = {instrument_id: bar.close for instrument_id, bar in ab.bars.items()}

        # 0. Splits with an ex-date in the gap scale positions FIRST (D75): this
        #    bar's raw price is post-split, so the share count must be too before
        #    anything marks NAV — broker book and every strategy's virtual book alike.
        if prev_timestamp is not None:
            for instrument_id, splits in splits_by_instrument.items():
                for ex_date, ratio in splits:
                    if prev_timestamp < ex_date <= ab.timestamp:
                        portfolio.apply_split(instrument_id, ratio)
                        for key in list(virtual_positions):
                            if key[1] == instrument_id:
                                virtual_positions[key] *= ratio

        # 1. Carry accrues on every currently-held instrument (D33), on the calendar-
        #    day gap since the previous ALIGNED bar — this correctly spans any bar
        #    dropped by D45 alignment, since it's driven by timestamps, not bar count.
        #    All base amounts come from one start-of-bar snapshot taken BEFORE any
        #    carry is deducted (D67) — otherwise per-leg deductions would shrink NAV
        #    and change the portfolio-level margin base mid-step, making the result
        #    depend on application order. Event flows (dividends, D6/D75) land in the
        #    same snapshot step, on post-split quantities.
        if prev_timestamp is not None:
            snapshot_positions = dict(portfolio.positions)
            snapshot_nav = portfolio.nav(prices, instruments)
            for instrument_id, quantity in snapshot_positions.items():
                if quantity != 0:
                    base_amount = quantity * prices[instrument_id]
                    carry = cost_stack.carry_cost(base_amount, prev_timestamp, ab.timestamp)
                    portfolio.accrue_carry(carry)
                    flow = cost_stack.event_flow(
                        instruments[instrument_id], quantity, prev_timestamp, ab.timestamp
                    )
                    if flow != 0:
                        portfolio.apply_cash_flow(flow)
            # Portfolio-level carry (D5, D67): margin interest accrues only on the
            # borrowed portion of the book — gross exposure beyond the equity backing it.
            margin_base = max(gross_exposure(snapshot_positions, prices, instruments) - snapshot_nav, 0.0)
            if margin_base > 0:
                portfolio.accrue_carry(
                    cost_stack.portfolio_carry_cost(margin_base, prev_timestamp, ab.timestamp)
                )

        # 2. Build this bar's DataView per instrument (D32, D56) from each
        #    instrument's own ALIGNED series — the VIEW series when one was supplied
        #    (split-adjusted signals, D75), never the raw frame either way.
        views: dict[str, DataView] = {
            instrument_id: build_data_view(view_bar_series[instrument_id], i)
            for instrument_id in bars_by_instrument
        }
        targets: list[TargetWeight] = []
        for strategy in strategies:
            targets.extend(strategy.generate_targets(views))

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

        # 5. Apply every netted (broker-facing) fill with its trade cost.
        for instrument_id, order in external_orders.items():
            if order.quantity != 0:
                trade_cost = cost_stack.trade_cost(instruments[instrument_id], order.quantity, prices[instrument_id])
                portfolio.apply_fill(instrument_id, order.quantity, prices[instrument_id], trade_cost)

        # 6. Per-bar risk check across every instrument (D30), regardless of whether
        #    an order fired this bar.
        if risk_monitor is not None:
            violation = risk_monitor.evaluate(portfolio.positions, prices, instruments, bar_index=i)
            if violation is not None:
                result.violations.append(violation)

        result.equity_curve.append((ab.timestamp, portfolio.nav(prices, instruments)))
        prev_timestamp = ab.timestamp

    result.final_positions = dict(portfolio.positions)
    result.final_cash = portfolio.cash

    if trial_registry is not None:
        metrics = {
            "final_nav": result.final_nav,
            "total_return": result.final_nav - starting_cash,
            "num_bars": len(aligned),
            "num_instruments": len(bars_by_instrument),
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
