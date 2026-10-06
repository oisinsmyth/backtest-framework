"""The main event loop, `run_backtest`.

Per aligned bar: carry accrual on every held position -> a DataView per
instrument per strategy -> signal -> target weight -> orders (pipeline.sizing)
-> trade costs (CostStack) -> PortfolioState updates -> per-bar risk check ->
an equity-curve point.

Instruments are aligned by inner join (data.alignment.align_bars); a single
instrument is the N=1 case. A bar missing on one leg means no trading for any leg
that step. Carry is driven by consecutive aligned timestamps, so it still accrues
across the full calendar gap. Per-leg carry uses each leg's own notional as its
base; margin interest on the borrowed portion of the book is charged separately
at portfolio level.

Capital is reallocated from current NAV every bar. RiskMonitor violations are
recorded in the result but not acted on (no corrective orders, no halting);
post-trade enforcement is up to the caller. The optional pre-trade gate
(`enforce_pretrade`) rejects orders before they fill.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Mapping, Sequence

from ..costs.stack import CostStack
from ..data.alignment import align_bars
from ..data.bars import TimestampedBar
from ..instruments.base import Instrument
from ..pipeline.sizing import Order, Sizer, TargetWeight, apply_virtual_orders, net_orders
from ..registry.trial_registry import TrialRegistry
from ..simulator.fills import Bar, StopSide, stop_fill_price
from .allocator import Allocator
from .dataview import DataView, build_data_view, normalise_volumes
from .portfolio import PortfolioState
from .risk import RiskLimits, RiskMonitor, RiskViolation, gross_exposure
from .strategy import Strategy


@dataclass
class BacktestResult:
    equity_curve: list[tuple[datetime, float]] = field(default_factory=list)
    violations: list[RiskViolation] = field(default_factory=list)
    final_positions: dict[str, float] = field(default_factory=dict)
    final_cash: float = 0.0
    fills: list[tuple[datetime, str, float, float, float]] = field(default_factory=list)
    """(timestamp, instrument_id, signed quantity, fill price, trade cost) per
    broker-facing fill. The golden master asserts these line by line and the
    simulator invariants reconcile them against positions."""
    cash_curve: list[tuple[datetime, float]] = field(default_factory=list)
    """(timestamp, cash) at each bar close, after all carry/flows/fills."""
    virtual_fills: list[tuple[datetime, str, str, float, float]] = field(default_factory=list)
    """(timestamp, strategy_id, instrument_id, signed quantity, price) per
    strategy-level virtual order, as if filled in full at that bar's price
    regardless of netting. Sleeve-level attribution is built from this stream.
    Trade costs are charged on the netted broker fills only and are not
    attributed here."""
    final_virtual_positions: dict[tuple[str, str], float] = field(default_factory=dict)
    """(strategy_id, instrument_id) -> quantity: each strategy's virtual book at the
    end of the run. Summed across strategies it equals final_positions when no
    orders were rejected."""
    stop_fills: list[tuple[datetime, str, str, float, float, float]] = field(default_factory=list)
    """(timestamp, strategy_id, instrument_id, quantity, fill price, stop price) per
    intrabar stop fill.

    Kept separately because `fills` cannot tell a stop exit from an ordinary exit
    that happened to close beyond the stop level. `fill price != stop price` marks a
    gap: the position filled at the bar's open because the market never traded at
    the stop."""

    @property
    def final_nav(self) -> float:
        return self.equity_curve[-1][1] if self.equity_curve else self.final_cash


def _event_flow_with_splits(
    cost_stack: CostStack,
    instrument: Instrument,
    pre_split_quantity: float,
    splits_in_gap: Sequence[tuple[datetime, float]],
    prev_timestamp: datetime,
    curr_timestamp: datetime,
) -> float:
    """Return the event flows across a gap that may contain split ex-dates.

    The gap is segmented at each split so a dividend pays on the share count held on
    its ex-date. A dividend on a split's ex-date pays the post-split count, because
    its per-share amount is already in the post-split frame (as_declared_dividends
    scales only by splits with an ex-date strictly after the dividend). Each segment
    boundary therefore sits one microsecond before the split's ex-date."""
    if not splits_in_gap:
        return cost_stack.event_flow(instrument, pre_split_quantity, prev_timestamp, curr_timestamp)
    total, quantity, segment_start = 0.0, pre_split_quantity, prev_timestamp
    for ex_date, ratio in splits_in_gap:
        boundary = ex_date - timedelta(microseconds=1)
        if boundary > segment_start:
            total += cost_stack.event_flow(instrument, quantity, segment_start, boundary)
        quantity *= ratio
        segment_start = max(segment_start, boundary)
    total += cost_stack.event_flow(instrument, quantity, segment_start, curr_timestamp)
    return total


def run_backtest(
    bars_by_instrument: Mapping[str, Sequence[TimestampedBar]],
    instruments: Mapping[str, Instrument],
    strategies: list[Strategy],
    cost_stack: CostStack,
    allocator: Allocator,
    starting_cash: float,
    risk_limits: RiskLimits | None = None,
    enforce_pretrade: bool = False,
    fill_timing: str = "close",
    trial_registry: TrialRegistry | None = None,
    trial_id: str | None = None,
    config: dict | None = None,
    snapshot_id: str = "unspecified",
    seed: int = 0,
    splits_by_instrument: Mapping[str, Sequence[tuple[datetime, float]]] | None = None,
    view_bars_by_instrument: Mapping[str, Sequence[TimestampedBar]] | None = None,
    volumes_by_instrument: Mapping[str, Sequence[float | None]] | None = None,
) -> BacktestResult:
    """Run the strategies over the aligned bars and return a BacktestResult.

    `bars_by_instrument` is the execution series (raw prices used for fills,
    commissions, carry and NAV). `view_bars_by_instrument`, when given, is what
    strategies see instead (e.g. split-adjusted for signal continuity) and must cover
    every aligned execution timestamp. `splits_by_instrument` scales broker and
    virtual positions on ex-dates.

    `volumes_by_instrument`, when given, exposes per-bar volume to strategies through
    the DataView. Each series is matched by timestamp against the aligned bars, as the
    view bars are; an aligned timestamp missing from an instrument's volumes raises
    ValueError. Instruments absent from the mapping get no volume series (correct for,
    say, an index level). Volumes are in the view frame; see `build_data_view` for why
    that matters for split-sensitive share volume.

    `enforce_pretrade=True` (off by default, requires `risk_limits`) runs
    RiskMonitor.pretrade_check on each netted order before it fills. A rejected order
    does not execute, the strategies' virtual orders for that instrument are dropped
    so the virtual books stay reconciled with the broker book (the strategies retry
    next bar), and the violation is recorded.

    `fill_timing`:

    - "close" (default): fill at the close of the bar that generated the signal. This
      matches vectorbt in the cross-engine reconciliation and is optimistic for mean
      reversion, since the entry always gets the close that triggered it.
    - "next_open": fill each bar's decisions at the next bar's open. Orders decided on
      the final bar never fill. Carry still accrues close-to-close on positions held at
      the previous close (an approximation: fills land at the open, inside the gap).
      The pre-trade gate is evaluated at decision time against decision-bar closes."""
    if trial_registry is not None and (trial_id is None or config is None):
        raise ValueError(
            "trial_registry was given without trial_id and config; "
            "pass both, or omit trial_registry to skip logging."
        )
    if enforce_pretrade and risk_limits is None:
        raise ValueError("enforce_pretrade=True requires risk_limits")
    if fill_timing not in ("close", "next_open"):
        raise ValueError(f"fill_timing must be 'close' or 'next_open', got {fill_timing!r}")

    aligned = align_bars(bars_by_instrument)
    if not aligned:
        raise ValueError(
            "alignment produced zero common bars: the instruments share no timestamps, "
            "or no bars were provided."
        )
    aligned_bar_series = {
        instrument_id: tuple(ab.bars[instrument_id] for ab in aligned) for instrument_id in bars_by_instrument
    }

    # Pure functions: match caller-supplied series to the aligned timestamps without
    # touching portfolio state. Both raise ValueError on a missing timestamp.
    view_bar_series = _align_view_bars(aligned, bars_by_instrument, view_bars_by_instrument, aligned_bar_series)
    volume_series = _align_volumes(aligned, bars_by_instrument, view_bars_by_instrument, volumes_by_instrument)

    splits_by_instrument = splits_by_instrument or {}

    sizer = Sizer()
    risk_monitor = RiskMonitor(risk_limits) if risk_limits is not None else None

    portfolio = PortfolioState(cash=starting_cash)
    virtual_positions: dict[tuple[str, str], float] = {}
    pending_virtual: dict[tuple[str, str], Order] = {}  # next_open mode only
    live_stops: dict[tuple[str, str], float] = {}  # (strategy, instrument) -> stop price
    strategies_by_id = {s.strategy_id: s for s in strategies}
    strategy_ids = [s.strategy_id for s in strategies]

    result = BacktestResult()
    prev_timestamp: datetime | None = None

    for i, ab in enumerate(aligned):
        prices = {instrument_id: bar.close for instrument_id, bar in ab.bars.items()}

        # Step 1 reads these. Bound before either step's guard so neither can see an
        # unbound name; empty dicts are correct on the first bar.
        pre_split_positions: dict[str, float] = {}
        splits_in_gap: dict[str, list[tuple[datetime, float]]] = {}

        # 0. Scale positions (broker and every virtual book) by any split with an
        #    ex-date in the gap. This bar's raw price is post-split, so the share
        #    count must be too before anything marks NAV. Pre-split quantities are
        #    captured first so event flows in the gap pay on the shares held on their
        #    ex-date: pre-split before the split, post-split on or after it.
        if prev_timestamp is not None:
            pre_split_positions = dict(portfolio.positions)
            splits_in_gap = _apply_gap_splits(
                portfolio, virtual_positions, pending_virtual, splits_by_instrument, prev_timestamp, ab.timestamp
            )

        # 1. Accrue carry on every held instrument over the calendar gap since the
        #    previous aligned bar (timestamp-driven, so it spans bars dropped by
        #    alignment). All base amounts come from one start-of-bar snapshot taken
        #    before any carry is deducted, so the result does not depend on the order
        #    legs are charged in. Event flows (dividends) are applied in the same step.
        if prev_timestamp is not None:
            _accrue_gap_carry(
                portfolio, cost_stack, instruments, prices,
                pre_split_positions, splits_in_gap, prev_timestamp, ab.timestamp,
            )

        # 1b. next_open: orders decided at the previous bar's close fill at this
        #     bar's open, before this bar's signal step, so sizing sees the updated
        #     books.
        if fill_timing == "next_open" and pending_virtual:
            opens = {instrument_id: bar.open for instrument_id, bar in ab.bars.items()}
            for instrument_id, order in net_orders(pending_virtual).items():
                if order.quantity != 0:
                    trade_cost = cost_stack.trade_cost(
                        instruments[instrument_id], order.quantity, opens[instrument_id]
                    )
                    portfolio.apply_fill(instrument_id, order.quantity, opens[instrument_id], trade_cost)
                    result.fills.append(
                        (ab.timestamp, instrument_id, order.quantity, opens[instrument_id], trade_cost)
                    )
            virtual_positions = apply_virtual_orders(virtual_positions, pending_virtual)
            for (strategy_id, instrument_id), order in pending_virtual.items():
                result.virtual_fills.append(
                    (ab.timestamp, strategy_id, instrument_id, order.quantity, opens[instrument_id])
                )
            pending_virtual = {}

        # 1c. Intrabar stops, checked after any next_open fill and before the
        #     strategy runs: a position opened at this bar's open can be stopped out on
        #     the same bar, and the decision step sees a book that reflects the stop.
        #     Every other exit is decided at a close, so the stop always wins a bar in
        #     which both would fire (adverse fill first). stop_fill_price fills a bar
        #     that gaps through the stop at the bar's open, not at the stop price.
        if live_stops:
            _sweep_intrabar_stops(
                ab, live_stops, virtual_positions, pending_virtual,
                portfolio, result, cost_stack, instruments, strategies_by_id,
            )

        # 2. Build this bar's DataView per instrument from its aligned view series
        #    if one was supplied (split-adjusted signals), else the execution bars.
        views: dict[str, DataView] = {
            instrument_id: build_data_view(
                view_bar_series[instrument_id],
                i,
                volumes=volume_series.get(instrument_id),
                instrument_id=instrument_id,
                volumes_already_normalised=True,
            )
            for instrument_id in bars_by_instrument
        }
        targets: list[TargetWeight] = []
        for strategy in strategies:
            targets.extend(strategy.generate_targets(views))

        # 2b. Stops are re-declared every bar, so a trailing stop moves and a target
        #     without a stop disarms any previous level.
        _refresh_stop_registry(targets, live_stops, splits_by_instrument)

        # 3. Capital is reallocated from current NAV every bar.
        current_nav = portfolio.nav(prices, instruments)
        capital_by_strategy = allocator.allocate(current_nav, strategy_ids)

        # 4. Signal -> target weight -> orders: size, net, update virtual books.
        virtual_orders = sizer.size_targets(
            targets,
            current_positions=virtual_positions,
            capital_by_strategy=capital_by_strategy,
            prices=prices,
            instruments=instruments,
        )
        external_orders = net_orders(virtual_orders)

        # 4b. Optional pre-trade gate: reject a netted order that would breach limits,
        #     and drop that instrument's virtual orders too (strategies retry next bar).
        if enforce_pretrade and risk_monitor is not None and external_orders:
            external_orders, virtual_orders = _apply_pretrade_gate(
                external_orders, virtual_orders, risk_monitor,
                portfolio, prices, instruments, result, i,
            )

        if fill_timing == "next_open":
            # 5. Decisions become pending orders that fill at the next bar's open
            #    (step 1b). Orders decided on the final bar never fill.
            pending_virtual = virtual_orders
        else:
            virtual_positions = apply_virtual_orders(virtual_positions, virtual_orders)
            for (strategy_id, instrument_id), order in virtual_orders.items():
                result.virtual_fills.append(
                    (ab.timestamp, strategy_id, instrument_id, order.quantity, prices[instrument_id])
                )

            # 5. Apply every netted (broker-facing) fill with its trade cost.
            for instrument_id, order in external_orders.items():
                if order.quantity != 0:
                    trade_cost = cost_stack.trade_cost(instruments[instrument_id], order.quantity, prices[instrument_id])
                    portfolio.apply_fill(instrument_id, order.quantity, prices[instrument_id], trade_cost)
                    result.fills.append(
                        (ab.timestamp, instrument_id, order.quantity, prices[instrument_id], trade_cost)
                    )

        # 6. Risk check every bar, whether or not an order fired.
        if risk_monitor is not None:
            violation = risk_monitor.evaluate(portfolio.positions, prices, instruments, bar_index=i)
            if violation is not None:
                result.violations.append(violation)

        result.equity_curve.append((ab.timestamp, portfolio.nav(prices, instruments)))
        result.cash_curve.append((ab.timestamp, portfolio.cash))
        prev_timestamp = ab.timestamp

    result.final_positions = dict(portfolio.positions)
    result.final_cash = portfolio.cash
    result.final_virtual_positions = dict(virtual_positions)

    if trial_registry is not None:
        _log_trial(
            trial_registry, result, starting_cash, len(aligned), len(bars_by_instrument),
            trial_id, config, snapshot_id, seed,
        )

    return result


# ---------------------------------------------------------------------------------
# Loop helpers for run_backtest. Do not reorder their float operations: the golden
# masters reconcile to the cent and the cross-engine test to 1e-12.
#
# Most mutate caller state in place (portfolio, result and the per-run dicts) and
# return None; only the _align_* pair and _apply_gap_splits return values. The loop
# rebinds `virtual_positions` and `pending_virtual`, so a helper may item-assign, pop
# or scale them but must not rebind them.
# ---------------------------------------------------------------------------------


def _align_view_bars(
    aligned: Sequence,
    bars_by_instrument: Mapping[str, Sequence[TimestampedBar]],
    view_bars_by_instrument: Mapping[str, Sequence[TimestampedBar]] | None,
    aligned_bar_series: Mapping[str, tuple[Bar, ...]],
) -> dict[str, tuple[Bar, ...]]:
    """Return the per-instrument bar series strategies see, aligned to execution timestamps.

    Uses the view series when given (split-adjusted signals) and raises ValueError if
    it lacks an aligned timestamp. With no view series the execution bars are used."""
    if view_bars_by_instrument is None:
        return dict(aligned_bar_series)
    view_lookup = {
        instrument_id: {tb.timestamp: tb.bar for tb in series}
        for instrument_id, series in view_bars_by_instrument.items()
    }
    try:
        return {
            instrument_id: tuple(view_lookup[instrument_id][ab.timestamp] for ab in aligned)
            for instrument_id in bars_by_instrument
        }
    except KeyError as exc:
        raise ValueError(
            f"view_bars_by_instrument is missing a bar for an aligned execution timestamp: {exc}"
        ) from exc


def _align_volumes(
    aligned: Sequence,
    bars_by_instrument: Mapping[str, Sequence[TimestampedBar]],
    view_bars_by_instrument: Mapping[str, Sequence[TimestampedBar]] | None,
    volumes_by_instrument: Mapping[str, Sequence[float | None]] | None,
) -> dict[str, tuple[float | None, ...] | None]:
    """Return per-instrument volumes matched to the aligned timestamps.

    Volumes are looked up against the already-aligned series rather than joining in
    align_bars, so a gap in a volume series cannot change the set of tradeable
    timestamps. Raises ValueError on a length mismatch or a missing timestamp.

    An instrument mapped to None gets an explicit None entry, recording that no
    volume was requested for that leg."""
    volume_series: dict[str, tuple[float | None, ...] | None] = {}
    if volumes_by_instrument is None:
        return volume_series
    for instrument_id in bars_by_instrument:
        supplied = volumes_by_instrument.get(instrument_id)
        if supplied is None:
            volume_series[instrument_id] = None
            continue
        source = view_bars_by_instrument or bars_by_instrument
        series = source[instrument_id]
        if len(supplied) != len(series):
            raise ValueError(
                f"volumes_by_instrument[{instrument_id!r}] has {len(supplied)} entries but "
                f"its bar series has {len(series)}; the two must align bar for bar"
            )
        by_timestamp = {tb.timestamp: v for tb, v in zip(series, normalise_volumes(supplied))}
        try:
            volume_series[instrument_id] = tuple(by_timestamp[ab.timestamp] for ab in aligned)
        except KeyError as exc:
            raise ValueError(
                "volumes_by_instrument is missing a volume for an aligned execution "
                f"timestamp on {instrument_id!r}: {exc}"
            ) from exc
    return volume_series


def _apply_gap_splits(
    portfolio: PortfolioState,
    virtual_positions: dict[tuple[str, str], float],
    pending_virtual: dict[tuple[str, str], Order],
    splits_by_instrument: Mapping[str, Sequence[tuple[datetime, float]]],
    prev_timestamp: datetime,
    curr_timestamp: datetime,
) -> dict[str, list[tuple[datetime, float]]]:
    """Loop step 0: apply splits whose ex-date falls in the gap.

    Scales the broker book, every virtual book and any pending next_open order, and
    returns the splits applied per instrument, sorted by ex-date. Step 1 uses them to
    segment the gap for event flows. The caller must capture `pre_split_positions`
    before calling."""
    splits_in_gap: dict[str, list[tuple[datetime, float]]] = {}
    for instrument_id, splits in splits_by_instrument.items():
        in_gap = sorted(
            (ex_date, ratio)
            for ex_date, ratio in splits
            if prev_timestamp < ex_date <= curr_timestamp
        )
        if in_gap:
            splits_in_gap[instrument_id] = in_gap
        for ex_date, ratio in in_gap:
            portfolio.apply_split(instrument_id, ratio)
            for key in list(virtual_positions):
                if key[1] == instrument_id:
                    virtual_positions[key] *= ratio
            # Pending next_open orders were sized in pre-split shares.
            for key, pending_order in list(pending_virtual.items()):
                if key[1] == instrument_id:
                    pending_virtual[key] = Order(instrument_id, pending_order.quantity * ratio)
    return splits_in_gap


def _accrue_gap_carry(
    portfolio: PortfolioState,
    cost_stack: CostStack,
    instruments: Mapping[str, Instrument],
    prices: Mapping[str, float],
    pre_split_positions: Mapping[str, float],
    splits_in_gap: Mapping[str, list[tuple[datetime, float]]],
    prev_timestamp: datetime,
    curr_timestamp: datetime,
) -> None:
    """Loop step 1: per-leg carry and event flows, then portfolio-level carry.

    Positions and NAV are snapshotted before the loop because per-leg carry is
    deducted from cash inside it; reading them live would make the margin base
    depend on the order the legs are charged in."""
    snapshot_positions = dict(portfolio.positions)
    snapshot_nav = portfolio.nav(prices, instruments)
    for instrument_id, quantity in snapshot_positions.items():
        if quantity != 0:
            # Notional is split-invariant, so the post-split snapshot is fine here.
            # `notional()` (not quantity * price) keeps the base consistent with
            # `portfolio.nav` and `gross_exposure` for instruments with a contract
            # multiplier (e.g. `OptionStub`'s x100).
            base_amount = instruments[instrument_id].notional(quantity, prices[instrument_id])
            carry = cost_stack.carry_cost(
                base_amount,
                prev_timestamp,
                curr_timestamp,
                components=instruments[instrument_id].carry_components(),
            )
            portfolio.accrue_carry(carry)
            flow = _event_flow_with_splits(
                cost_stack,
                instruments[instrument_id],
                pre_split_positions.get(instrument_id, 0.0),
                splits_in_gap.get(instrument_id, []),
                prev_timestamp,
                curr_timestamp,
            )
            if flow != 0:
                portfolio.apply_cash_flow(flow)
    # Margin interest accrues on the borrowed portion: gross exposure above NAV.
    margin_base = max(gross_exposure(snapshot_positions, prices, instruments) - snapshot_nav, 0.0)
    if margin_base > 0:
        portfolio.accrue_carry(
            cost_stack.portfolio_carry_cost(margin_base, prev_timestamp, curr_timestamp)
        )


def _sweep_intrabar_stops(
    ab: object,
    live_stops: dict[tuple[str, str], float],
    virtual_positions: dict[tuple[str, str], float],
    pending_virtual: dict[tuple[str, str], Order],
    portfolio: PortfolioState,
    result: BacktestResult,
    cost_stack: CostStack,
    instruments: Mapping[str, Instrument],
    strategies_by_id: Mapping[str, Strategy],
) -> None:
    """Loop step 1c: evaluate every armed stop against this bar's OHLC.

    Iterates a copy of live_stops because entries are deleted both for flat
    positions and for filled stops. All mutation is in place, since the caller
    rebinds `virtual_positions` and `pending_virtual` later in the same bar."""
    for (strategy_id, instrument_id), stop_price in list(live_stops.items()):
        held = virtual_positions.get((strategy_id, instrument_id), 0.0)
        if held == 0.0:
            del live_stops[(strategy_id, instrument_id)]
            continue
        side = StopSide.SELL_STOP if held > 0 else StopSide.BUY_STOP
        fill_price = stop_fill_price(side, stop_price, ab.bars[instrument_id])  # type: ignore[attr-defined]
        if fill_price is None:
            continue

        quantity = -held
        trade_cost = cost_stack.trade_cost(instruments[instrument_id], quantity, fill_price)
        portfolio.apply_fill(instrument_id, quantity, fill_price, trade_cost)
        result.fills.append((ab.timestamp, instrument_id, quantity, fill_price, trade_cost))  # type: ignore[attr-defined]
        virtual_positions[(strategy_id, instrument_id)] = 0.0
        result.virtual_fills.append(
            (ab.timestamp, strategy_id, instrument_id, quantity, fill_price)  # type: ignore[attr-defined]
        )
        result.stop_fills.append(
            (ab.timestamp, strategy_id, instrument_id, quantity, fill_price, stop_price)  # type: ignore[attr-defined]
        )
        del live_stops[(strategy_id, instrument_id)]

        # Tell the strategy it was stopped out, so a stateful one does not re-enter
        # on the next bar with the same target. The hook is optional.
        on_stop_filled = getattr(strategies_by_id.get(strategy_id), "on_stop_filled", None)
        if on_stop_filled is not None:
            on_stop_filled(instrument_id)

        # A pending next_open order was sized against the position just closed.
        pending_virtual.pop((strategy_id, instrument_id), None)


def _refresh_stop_registry(
    targets: Sequence[TargetWeight],
    live_stops: dict[tuple[str, str], float],
    splits_by_instrument: Mapping[str, Sequence[tuple[datetime, float]]],
) -> None:
    """Loop step 2b: rebuild the armed-stop registry from this bar's targets.

    Raises ValueError for a stop on an instrument with splits."""
    for target in targets:
        key = (target.strategy_id, target.instrument_id)
        if target.stop is None:
            live_stops.pop(key, None)
            continue
        if splits_by_instrument.get(target.instrument_id):
            # Stops are declared in the view frame and enforced against execution
            # prices; the two match only when the instrument has no splits.
            raise ValueError(
                f"instrument {target.instrument_id!r} carries splits and cannot use an "
                "intrabar stop: the stop is declared in the view frame and enforced "
                "against execution prices, which diverge across a split"
            )
        live_stops[key] = target.stop


def _apply_pretrade_gate(
    external_orders: dict[str, Order],
    virtual_orders: dict[tuple[str, str], Order],
    risk_monitor: RiskMonitor,
    portfolio: PortfolioState,
    prices: Mapping[str, float],
    instruments: Mapping[str, Instrument],
    result: BacktestResult,
    bar_index: int,
) -> tuple[dict[str, Order], dict[tuple[str, str], Order]]:
    """Loop step 4b: return the approved broker orders and the surviving virtual orders.

    Appends a violation per rejection. A rejection drops the instrument's virtual
    orders as well, so the virtual books keep reconciling to `final_positions`. Each
    order is checked against the book as updated by the earlier approvals in the
    same bar."""
    simulated = dict(portfolio.positions)
    approved: dict[str, Order] = {}
    for instrument_id, order in external_orders.items():
        violation = risk_monitor.pretrade_check(
            simulated, prices, instruments, instrument_id, order.quantity
        )
        if violation is None:
            approved[instrument_id] = order
            simulated[instrument_id] = simulated.get(instrument_id, 0.0) + order.quantity
        else:
            result.violations.append(
                RiskViolation(
                    rule=violation.rule,
                    limit=violation.limit,
                    observed=violation.observed,
                    bar_index=bar_index,
                )
            )
            virtual_orders = {
                key: vo for key, vo in virtual_orders.items() if key[1] != instrument_id
            }
    return approved, virtual_orders


def _log_trial(
    trial_registry: TrialRegistry,
    result: BacktestResult,
    starting_cash: float,
    num_bars: int,
    num_instruments: int,
    trial_id: str | None,
    config: dict | None,
    snapshot_id: str,
    seed: int,
) -> None:
    """Record the run in the trial registry.

    `trial_id` and `config` are Optional only to match run_backtest's signature;
    run_backtest has already raised if either is None with a registry, so the type
    ignores below are safe."""
    metrics = {
        "final_nav": result.final_nav,
        "total_return": result.final_nav - starting_cash,
        "num_bars": num_bars,
        "num_instruments": num_instruments,
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
