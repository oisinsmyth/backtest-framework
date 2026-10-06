"""run_backtest: the main event loop.

Wires together, per aligned bar: carry accrual on every held position -> a
DataView per instrument per strategy -> signal -> target weight -> orders
(pipeline.sizing) -> cost application (CostStack) -> PortfolioState updates -> a
per-bar risk check -> an equity-curve point.

Multi-instrument via inner-join alignment (data.alignment.align_bars); one
instrument is the N=1 case, same as Strategy. A bar missing on one leg means no
trading for any leg that step; carry still accrues across the real calendar gap,
because it's driven by consecutive aligned timestamps, not bar count. Per-leg carry
accrues per instrument independently (each leg's own notional as its own base
amount); margin interest on the book's borrowed portion is charged separately at
portfolio level.

Capital is reallocated from current NAV every bar, not fixed at the start.
RiskMonitor violations are recorded in the result, not acted on: no corrective orders
or halting are implemented here, so a caller inspecting BacktestResult.violations is
the only post-trade enforcement. The optional pre-trade gate (`enforce_pretrade`)
rejects orders before they fill.
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
    broker-facing fill: what the golden master asserts line-by-line and the
    simulator invariants reconcile against positions."""
    cash_curve: list[tuple[datetime, float]] = field(default_factory=list)
    """(timestamp, cash) at each bar close, after all carry/flows/fills."""
    virtual_fills: list[tuple[datetime, str, str, float, float]] = field(default_factory=list)
    """(timestamp, strategy_id, instrument_id, signed quantity, price) per
    strategy-level virtual order: each strategy's own order as if filled
    in full at that bar's price, regardless of netting — the strategy-tagged fill
    stream sleeve-level attribution is built from. Trade costs are charged on the
    netted broker fills only and are deliberately not attributed here."""
    final_virtual_positions: dict[tuple[str, str], float] = field(default_factory=dict)
    """(strategy_id, instrument_id) -> quantity: each strategy's virtual book at the
    end of the run. Sums across strategies to final_positions exactly
    when no orders were rejected."""
    stop_fills: list[tuple[datetime, str, str, float, float, float]] = field(default_factory=list)
    """(timestamp, strategy_id, instrument_id, quantity, fill price, stop price) per
    intrabar stop fill.

    Recorded separately because "this exit was caused by the stop" is not recoverable
    from `fills` afterwards. Inferring stop exits by checking whether an exit price
    ended up beyond the stop level also catches ordinary exits that happened to close
    past it. Only the engine knows which fill a stop caused.

    `fill price != stop price` is exactly the gap case: the position filled at the
    bar's open because the market never traded at the stop."""

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
    """Event flows across a gap that may contain split ex-dates: the gap is
    segmented at each split so a dividend pays on the share count actually held on
    its ex-date. A dividend exactly on a split's ex-date pays the post-split count —
    its per-share amount is already in the post-split frame (as_declared_dividends
    scales only by splits with ex-date strictly after the dividend) — so each
    segment boundary sits a microsecond before the split's ex-date, putting that
    ex-date in the post-split segment."""
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
    """`bars_by_instrument` is the execution series (raw prices — fills, commissions,
    carry, NAV all use it). `view_bars_by_instrument`, when given, is what
    strategies see instead (e.g. split-adjusted for signal continuity); it must
    cover every aligned execution timestamp. `splits_by_instrument` scales broker and
    virtual positions on ex-dates.

    `volumes_by_instrument`, when given, makes per-bar volume visible to strategy code
    through the same DataView guard the bars ride in. It is keyed by instrument
    and each series is `{timestamp: volume}`-matched against the aligned bars, exactly
    as the view-bar path is; a timestamp present in the aligned bars but absent from an
    instrument's volume map is a loud error rather than a silent gap. Instruments absent
    from the mapping simply get no volume series, which is the correct silent state for
    something like an index level. Volumes are in the view frame; see
    `build_data_view` on why share volume's split sensitivity makes that matter.

    `enforce_pretrade=True` (off by default) runs RiskMonitor.pretrade_check
    on each netted order before it fills: a rejected order does not execute, the
    corresponding strategies' virtual orders for that instrument are dropped too
    (so virtual books stay reconciled with the broker book and the strategies
    re-attempt next bar), and the violation is recorded. Requires `risk_limits`.

    `fill_timing`: "close" (default) fills orders at the close of the bar
    that generated the signal — the historical convention, matched to vectorbt in
    the cross-engine reconciliation, optimistic for mean reversion because the entry always
    catches exactly the close that triggered it. "next_open" fills each bar's
    decisions at the next bar's open: the strategy never trades at the price that
    produced its signal. In next_open mode, orders decided on the final bar never
    fill, carry still accrues close-to-close on positions held at the previous
    close (fills land at the open, one calendar-instant into the gap — a stated
    approximation), and the pre-trade gate is evaluated at decision time against
    decision-bar closes."""
    if trial_registry is not None and (trial_id is None or config is None):
        raise ValueError(
            "trial_registry was given but trial_id and/or config was not — "
            "pass both, or omit trial_registry if you don't want this run logged."
        )
    if enforce_pretrade and risk_limits is None:
        raise ValueError("enforce_pretrade=True requires risk_limits — there is no gate without limits")
    if fill_timing not in ("close", "next_open"):
        raise ValueError(f"fill_timing must be 'close' or 'next_open', got {fill_timing!r}")

    aligned = align_bars(bars_by_instrument)
    if not aligned:
        raise ValueError(
            "alignment produced zero common bars — the instruments share no timestamps "
            "(or no bars were provided). Refusing to return a silently-empty backtest "
            "whose final NAV would equal starting cash."
        )
    aligned_bar_series = {
        instrument_id: tuple(ab.bars[instrument_id] for ab in aligned) for instrument_id in bars_by_instrument
    }

    # Both marshalling steps below are pure: they read the caller's mappings and the
    # aligned timestamps and return series, touching no portfolio state. They are the
    # only two places a caller-supplied series is matched to the aligned clock, and
    # they fail the same way — loudly, on a missing timestamp.
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

        # Step 0 produces two values that step 1 consumes, and the two steps guard
        # themselves separately. Both values are bound unconditionally here, before
        # either guard, so changing one guard cannot leave the other reading an
        # unbound name. An empty dict is the correct first-bar value for both: step 1
        # does not run on the first bar either.
        pre_split_positions: dict[str, float] = {}
        splits_in_gap: dict[str, list[tuple[datetime, float]]] = {}

        # 0. Splits with an ex-date in the gap scale positions first: this
        #    bar's raw price is post-split, so the share count must be too before
        #    anything marks NAV — broker book and every strategy's virtual book alike.
        #    Pre-split quantities are captured before scaling, because event flows
        #    inside the same gap must pay on the share count actually held on their
        #    ex-date: a dividend before the split pays pre-split shares; one
        #    on/after it pays post-split shares.
        if prev_timestamp is not None:
            pre_split_positions = dict(portfolio.positions)
            splits_in_gap = _apply_gap_splits(
                portfolio, virtual_positions, pending_virtual, splits_by_instrument, prev_timestamp, ab.timestamp
            )

        # 1. Carry accrues on every currently-held instrument, on the calendar-
        #    day gap since the previous aligned bar — this correctly spans any bar
        #    dropped by alignment, since it's driven by timestamps, not bar count.
        #    All base amounts come from one start-of-bar snapshot taken before any
        #    carry is deducted — otherwise per-leg deductions would shrink NAV
        #    and change the portfolio-level margin base mid-step, making the result
        #    depend on application order. Event flows (dividends) land in the
        #    same snapshot step, on post-split quantities.
        if prev_timestamp is not None:
            _accrue_gap_carry(
                portfolio, cost_stack, instruments, prices,
                pre_split_positions, splits_in_gap, prev_timestamp, ab.timestamp,
            )

        # 1b. next_open fill timing: orders decided at the previous bar's
        #     close fill now, at this bar's open — the strategy never trades at the
        #     price that generated its signal. Fills precede this bar's signal step,
        #     so today's sizing sees the updated books.
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

        # 1c. Intrabar stops. Checked here — after any next_open fill, before
        #     the strategy is consulted — for two reasons. A position opened at this
        #     bar's open can still be stopped out on this same bar, which is real and
        #     must be allowed; and the strategy's decision step then sees a book that
        #     already reflects the stop.
        #
        #     The adverse-fill-first convention is satisfied by construction: the stop
        #     is an intrabar order and every other exit in this engine is a decision
        #     taken at a close, so the stop is always evaluated first and always wins a
        #     bar in which both would have fired.
        #
        #     Gap handling lives inside stop_fill_price: a bar that gaps through the
        #     stop fills at the bar's open, not at the stop price. Filling at the stop
        #     when the market never traded there would understate losses.
        if live_stops:
            _sweep_intrabar_stops(
                ab, live_stops, virtual_positions, pending_virtual,
                portfolio, result, cost_stack, instruments, strategies_by_id,
            )

        # 2. Build this bar's DataView per instrument from each instrument's own
        #    aligned series — the view series when one was supplied
        #    (split-adjusted signals), otherwise the execution bars.
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

        # Refresh the stop registry from this bar's targets. Re-declared every
        # bar, so a trailing stop simply moves; a target that stops declaring one drops
        # its entry rather than leaving a stale level armed.
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

        # 4b. Optional pre-trade gate: reject a netted order that
        #     would breach limits before it fills. The rejected instrument's virtual
        #     orders are dropped too, so virtual books stay reconciled with the
        #     broker book and the strategies simply re-attempt next bar.
        if enforce_pretrade and risk_monitor is not None and external_orders:
            external_orders, virtual_orders = _apply_pretrade_gate(
                external_orders, virtual_orders, risk_monitor,
                portfolio, prices, instruments, result, i,
            )

        if fill_timing == "next_open":
            # 5. Decisions become pending orders; they fill at the next
            #    bar's open (step 1b). Orders decided on the final bar never fill.
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

        # 6. Per-bar risk check across every instrument, regardless of whether
        #    an order fired this bar.
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
# Helpers extracted from run_backtest's loop. Each body keeps the original order of
# operations and the same float arithmetic: nothing here hoists a sum out of a loop
# or reorders an accumulation. The golden masters reconcile to the cent and the
# cross-engine test to 1e-12, so any change to either is a regression.
#
# Most of them mutate caller state in place (portfolio, result, and the three
# per-run dicts) and return None; only the _align_* pair and _apply_gap_splits return
# values. That is deliberate — `virtual_positions` and `pending_virtual` are rebound
# inside the loop, so a helper may only item-assign, pop or scale them, never rebind
# them.
# ---------------------------------------------------------------------------------


def _align_view_bars(
    aligned: Sequence,
    bars_by_instrument: Mapping[str, Sequence[TimestampedBar]],
    view_bars_by_instrument: Mapping[str, Sequence[TimestampedBar]] | None,
    aligned_bar_series: Mapping[str, tuple[Bar, ...]],
) -> dict[str, tuple[Bar, ...]]:
    """Strategy views come from the view series when given (split-adjusted signals),
    aligned 1:1 with execution timestamps — a missing timestamp is a loud error, never
    a silently substituted raw bar. With no view series the execution bars are
    the view."""
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
    """Volume rides the same timestamp-matching path as the view bars, and fails the
    same way. Volume does not pass through align_bars: it is looked up against the
    already-aligned series rather than participating in the inner join itself, so the
    set of tradeable timestamps cannot shift because a volume column had a hole.

    An instrument mapped to None gets an explicit None entry rather than being absent —
    `volume_series.get(id)` returns None either way, but the distinction is what lets a
    reader see that "no volume for this leg" was asked for, not merely not asked
    about."""
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
                f"its bar series has {len(series)} — the two must align exactly"
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
    """Loop step 0. Scales the broker book, every strategy's virtual book and any
    pending next_open order by each split whose ex-date falls in the gap, and
    returns the splits it applied, per instrument, sorted by ex-date.

    Step 1 needs the return value to segment the gap so a dividend pays on the
    share count actually held on its ex-date. Caller-side,
    `pre_split_positions` must be captured before this runs — this function has already
    scaled the book by the time it returns."""
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
            # Pending next_open orders were sized in pre-split share terms;
            # they scale with everything else.
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

    The snapshot must not be inlined away: per-leg carry is
    deducted from cash inside the loop, so reading live positions and NAV for the
    portfolio-level margin base would make it depend on the order the legs were
    charged in."""
    snapshot_positions = dict(portfolio.positions)
    snapshot_nav = portfolio.nav(prices, instruments)
    for instrument_id, quantity in snapshot_positions.items():
        if quantity != 0:
            # Carry base is split-invariant (qty x price is the same notional in
            # either frame), so the post-split snapshot is correct here.
            #
            # Uses the instrument's `notional()` rather than `quantity * price`, so the
            # carry base agrees with `portfolio.nav` and `gross_exposure`, which both
            # ask the instrument. They differ for any instrument with a contract
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
    # Portfolio-level carry: margin interest accrues only on the
    # borrowed portion of the book — gross exposure beyond the equity backing it.
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
    """Loop step 1c: every armed stop, evaluated against this bar's OHLC.

    Iterates a list copy of live_stops because it deletes from it in both exit paths —
    the already-flat sweep and the filled sweep. Every mutation here is in place:
    `virtual_positions` and `pending_virtual` are rebound by the caller later in the
    same bar, so rebinding them here would silently discard this sweep's work."""
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

        # A stateful strategy does not otherwise learn it was stopped out: it
        # would keep emitting the same target and re-enter on the next bar,
        # turning a bounded loss into a repeated one. The hook is optional so
        # strategies that never declare stops still conform to the protocol.
        on_stop_filled = getattr(strategies_by_id.get(strategy_id), "on_stop_filled", None)
        if on_stop_filled is not None:
            on_stop_filled(instrument_id)

        # A pending next_open order for this key is now stale — it was sized
        # against a position the stop has just closed.
        pending_virtual.pop((strategy_id, instrument_id), None)


def _refresh_stop_registry(
    targets: Sequence[TargetWeight],
    live_stops: dict[tuple[str, str], float],
    splits_by_instrument: Mapping[str, Sequence[tuple[datetime, float]]],
) -> None:
    """Loop step 2b: rebuild the armed-stop registry from this bar's targets."""
    for target in targets:
        key = (target.strategy_id, target.instrument_id)
        if target.stop is None:
            live_stops.pop(key, None)
            continue
        if splits_by_instrument.get(target.instrument_id):
            # The stop was computed in the view frame and is enforced against
            # execution prices. Those are the same series only when the instrument
            # has no splits. Rather than silently compare two frames, refuse.
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
    """Loop step 4b. Returns the approved broker orders and the
    surviving virtual orders, and appends a violation per rejection.

    Both dicts come back because a rejection has to reach both books: dropping only the
    broker order would leave the rejecting strategy believing it holds a position the
    broker never took, and the virtual books would stop reconciling to `final_positions`
    from that bar onward. `simulated` accumulates the approved orders as it goes, so
    each order is checked against the book the earlier approvals in this same bar would
    have produced — not against the bar's opening book."""
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
    """The trial-registry write. `trial_id` and `config` are Optional in the
    signature only because run_backtest's are — the guard at the top of run_backtest
    has already refused the run if either is None alongside a registry, which is why
    the ignores below are safe and stay narrow."""
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
