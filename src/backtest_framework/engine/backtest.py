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
from datetime import datetime, timedelta
from typing import Mapping, Sequence

from ..costs.stack import CostStack
from ..data.alignment import align_bars
from ..data.bars import TimestampedBar
from ..instruments.base import Instrument
from ..pipeline.sizing import Order, Sizer, TargetWeight, apply_virtual_orders, net_orders
from ..registry.trial_registry import TrialRegistry
from ..simulator.fills import StopSide, stop_fill_price
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
    broker-facing fill (D77) — what THE golden master asserts line-by-line and the
    D40 invariants reconcile against positions."""
    cash_curve: list[tuple[datetime, float]] = field(default_factory=list)
    """(timestamp, cash) at each bar close, after all carry/flows/fills (D77)."""
    virtual_fills: list[tuple[datetime, str, str, float, float]] = field(default_factory=list)
    """(timestamp, strategy_id, instrument_id, signed quantity, price) per
    strategy-level virtual order (D46/D101): each strategy's own order as if filled
    in full at that bar's price, regardless of netting — the strategy-tagged fill
    stream sleeve-level attribution is built from. Trade costs are charged on the
    NETTED broker fills only (D27) and are deliberately not attributed here."""
    final_virtual_positions: dict[tuple[str, str], float] = field(default_factory=dict)
    """(strategy_id, instrument_id) -> quantity: each strategy's virtual book at the
    end of the run (D46/D101). Sums across strategies to final_positions exactly
    when no orders were rejected."""
    stop_fills: list[tuple[datetime, str, str, float, float, float]] = field(default_factory=list)
    """(timestamp, strategy_id, instrument_id, quantity, fill price, stop price) per
    INTRABAR STOP fill (D170).

    Recorded separately because "this exit was caused by the stop" is not recoverable
    from `fills` afterwards, and guessing it is how a measurement goes wrong: Phase 2
    inferred stop exits by asking whether an exit price ended up beyond the stop LEVEL,
    which also catches ordinary channel exits that happened to close past it, and it
    reported those as stops that failed. Only the engine knows which fill a stop caused,
    so only the engine should say.

    `fill price != stop price` is exactly the gap case (D10) — the position filled at the
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
    """Event flows across a gap that may contain split ex-dates (D99): the gap is
    segmented at each split so a dividend pays on the share count actually held on
    its ex-date. A dividend exactly ON a split's ex-date pays the POST-split count —
    its per-share amount is already in the post-split frame (as_declared_dividends
    scales only by splits with ex-date strictly after the dividend, D75) — so each
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
    """`bars_by_instrument` is the EXECUTION series (raw prices — fills, commissions,
    carry, NAV all use it, per D6). `view_bars_by_instrument`, when given, is what
    strategies see instead (e.g. split-adjusted for signal continuity, D75); it must
    cover every aligned execution timestamp. `splits_by_instrument` scales broker and
    virtual positions on ex-dates (D75).

    `volumes_by_instrument`, when given, makes per-bar volume visible to strategy code
    through the same DataView guard the bars ride in (D168). It is keyed by instrument
    and each series is `{timestamp: volume}`-matched against the aligned bars, exactly
    as the view-bar path is; a timestamp present in the aligned bars but absent from an
    instrument's volume map is a loud error rather than a silent gap. Instruments absent
    from the mapping simply get no volume series, which is the correct silent state for
    something like an index level. **Volumes are in the VIEW frame** — see
    `build_data_view` on why share volume's split sensitivity makes that load-bearing.

    `enforce_pretrade=True` (D101, off by default) runs RiskMonitor.pretrade_check
    on each netted order before it fills: a rejected order does not execute, the
    corresponding strategies' virtual orders for that instrument are dropped too
    (so virtual books stay reconciled with the broker book and the strategies
    re-attempt next bar), and the violation is recorded. Requires `risk_limits`.

    `fill_timing` (D103): "close" (default) fills orders at the close of the bar
    that generated the signal — the historical convention, matched to vectorbt in
    the D79 reconciliation, optimistic for mean reversion because the entry always
    catches exactly the close that triggered it. "next_open" fills each bar's
    decisions at the NEXT bar's open: the strategy never trades at the price that
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
        raise ValueError("enforce_pretrade=True requires risk_limits — there is no gate without limits (D101)")
    if fill_timing not in ("close", "next_open"):
        raise ValueError(f"fill_timing must be 'close' or 'next_open', got {fill_timing!r} (D103)")

    aligned = align_bars(bars_by_instrument)  # D45
    if not aligned:
        raise ValueError(
            "alignment produced zero common bars — the instruments share no timestamps "
            "(or no bars were provided). Refusing to return a silently-empty backtest "
            "whose final NAV would equal starting cash (D99)."
        )
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

    # Volume rides the same timestamp-matching path as the view bars, and fails the
    # same way. align_bars is deliberately NOT changed: volume is looked up against the
    # already-aligned series rather than participating in the inner join itself, so the
    # set of tradeable timestamps cannot shift because a volume column had a hole.
    volume_series: dict[str, tuple[float | None, ...] | None] = {}
    if volumes_by_instrument is not None:
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

    splits_by_instrument = splits_by_instrument or {}

    sizer = Sizer()
    risk_monitor = RiskMonitor(risk_limits) if risk_limits is not None else None

    portfolio = PortfolioState(cash=starting_cash)
    virtual_positions: dict[tuple[str, str], float] = {}
    pending_virtual: dict[tuple[str, str], Order] = {}  # next_open mode only (D103)
    live_stops: dict[tuple[str, str], float] = {}  # (strategy, instrument) -> stop price (D170)
    strategies_by_id = {s.strategy_id: s for s in strategies}
    strategy_ids = [s.strategy_id for s in strategies]

    result = BacktestResult()
    prev_timestamp: datetime | None = None

    for i, ab in enumerate(aligned):
        prices = {instrument_id: bar.close for instrument_id, bar in ab.bars.items()}

        # 0. Splits with an ex-date in the gap scale positions FIRST (D75): this
        #    bar's raw price is post-split, so the share count must be too before
        #    anything marks NAV — broker book and every strategy's virtual book alike.
        #    Pre-split quantities are captured before scaling, because event flows
        #    inside the same gap must pay on the share count actually held on their
        #    ex-date (D99): a dividend BEFORE the split pays pre-split shares; one
        #    on/after it pays post-split shares.
        if prev_timestamp is not None:
            pre_split_positions = dict(portfolio.positions)
            splits_in_gap: dict[str, list[tuple[datetime, float]]] = {}
            for instrument_id, splits in splits_by_instrument.items():
                in_gap = sorted(
                    (ex_date, ratio)
                    for ex_date, ratio in splits
                    if prev_timestamp < ex_date <= ab.timestamp
                )
                if in_gap:
                    splits_in_gap[instrument_id] = in_gap
                for ex_date, ratio in in_gap:
                    portfolio.apply_split(instrument_id, ratio)
                    for key in list(virtual_positions):
                        if key[1] == instrument_id:
                            virtual_positions[key] *= ratio
                    # Pending next_open orders were sized in pre-split share terms;
                    # they scale with everything else (D103).
                    for key, pending_order in list(pending_virtual.items()):
                        if key[1] == instrument_id:
                            pending_virtual[key] = Order(instrument_id, pending_order.quantity * ratio)

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
                    # Carry base is split-invariant (qty x price is the same notional in
                    # either frame), so the post-split snapshot is correct here.
                    base_amount = quantity * prices[instrument_id]
                    carry = cost_stack.carry_cost(
                        base_amount,
                        prev_timestamp,
                        ab.timestamp,
                        components=instruments[instrument_id].carry_components(),  # D100
                    )
                    portfolio.accrue_carry(carry)
                    flow = _event_flow_with_splits(
                        cost_stack,
                        instruments[instrument_id],
                        pre_split_positions.get(instrument_id, 0.0),
                        splits_in_gap.get(instrument_id, []),
                        prev_timestamp,
                        ab.timestamp,
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

        # 1b. next_open fill timing (D103): orders decided at the PREVIOUS bar's
        #     close fill now, at THIS bar's open — the strategy never trades at the
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

        # 1c. INTRABAR STOPS (D170). Checked here — after any next_open fill, before
        #     the strategy is consulted — for two reasons. A position opened at THIS
        #     bar's open can still be stopped out on this same bar, which is real and
        #     must be allowed; and the strategy's decision step then sees a book that
        #     already reflects the stop.
        #
        #     D42's adverse-fill-first convention is satisfied by construction: the stop
        #     is an intrabar order and every other exit in this engine is a decision
        #     taken at a close, so the stop is always evaluated first and always wins a
        #     bar in which both would have fired.
        #
        #     D10 lives inside stop_fill_price: a bar that GAPS through the stop fills at
        #     the bar's open, not at the stop price. That is the whole point of routing
        #     through it rather than assuming the stop price — filling at the stop when
        #     the market never traded there is free money and fantasy risk numbers.
        if live_stops:
            for (strategy_id, instrument_id), stop_price in list(live_stops.items()):
                held = virtual_positions.get((strategy_id, instrument_id), 0.0)
                if held == 0.0:
                    del live_stops[(strategy_id, instrument_id)]
                    continue
                side = StopSide.SELL_STOP if held > 0 else StopSide.BUY_STOP
                fill_price = stop_fill_price(side, stop_price, ab.bars[instrument_id])
                if fill_price is None:
                    continue

                quantity = -held
                trade_cost = cost_stack.trade_cost(instruments[instrument_id], quantity, fill_price)
                portfolio.apply_fill(instrument_id, quantity, fill_price, trade_cost)
                result.fills.append((ab.timestamp, instrument_id, quantity, fill_price, trade_cost))
                virtual_positions[(strategy_id, instrument_id)] = 0.0
                result.virtual_fills.append(
                    (ab.timestamp, strategy_id, instrument_id, quantity, fill_price)
                )
                result.stop_fills.append(
                    (ab.timestamp, strategy_id, instrument_id, quantity, fill_price, stop_price)
                )
                del live_stops[(strategy_id, instrument_id)]

                # A stateful strategy does not otherwise learn it was stopped out: it
                # would keep emitting the same target and re-enter on the next bar,
                # turning a bounded loss into a repeated one. Optional by design so
                # every pre-D170 strategy still conforms to the protocol.
                on_stop_filled = getattr(strategies_by_id.get(strategy_id), "on_stop_filled", None)
                if on_stop_filled is not None:
                    on_stop_filled(instrument_id)

                # A pending next_open order for this key is now stale — it was sized
                # against a position the stop has just closed.
                pending_virtual.pop((strategy_id, instrument_id), None)

        # 2. Build this bar's DataView per instrument (D32, D56) from each
        #    instrument's own ALIGNED series — the VIEW series when one was supplied
        #    (split-adjusted signals, D75), never the raw frame either way.
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

        # Refresh the stop registry from this bar's targets (D170). Re-declared every
        # bar, so a trailing stop simply moves; a target that stops declaring one drops
        # its entry rather than leaving a stale level armed.
        for target in targets:
            key = (target.strategy_id, target.instrument_id)
            if target.stop is None:
                live_stops.pop(key, None)
                continue
            if splits_by_instrument.get(target.instrument_id):
                # The stop was computed in the VIEW frame and is enforced against
                # EXECUTION prices. Those are the same series only when the instrument
                # has no splits (D75). Rather than silently compare two frames, refuse.
                raise ValueError(
                    f"instrument {target.instrument_id!r} carries splits and cannot use an "
                    "intrabar stop: the stop is declared in the view frame and enforced "
                    "against execution prices, which diverge across a split (D75/D170)"
                )
            live_stops[key] = target.stop

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

        # 4b. Optional pre-trade gate (D101, audit F12): reject a netted order that
        #     would breach limits BEFORE it fills. The rejected instrument's virtual
        #     orders are dropped too, so virtual books stay reconciled with the
        #     broker book and the strategies simply re-attempt next bar.
        if enforce_pretrade and risk_monitor is not None and external_orders:
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
                            bar_index=i,
                        )
                    )
                    virtual_orders = {
                        key: vo for key, vo in virtual_orders.items() if key[1] != instrument_id
                    }
            external_orders = approved

        if fill_timing == "next_open":
            # 5. (D103) Decisions become pending orders; they fill at the NEXT
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

        # 6. Per-bar risk check across every instrument (D30), regardless of whether
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
