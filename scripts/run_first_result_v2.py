"""THE FIRST REAL NUMBER, v2 — through the hardened Step 7 data layer (D72-D76).

Same strategy, same pair, same sweep as v1 (docs/results/first_real_number.md, which
stays untouched as the historical milestone) — but the data path is now the real one:

  committed RAW fixture -> cleaner (D25) -> validator (D26) -> SnapshotStore (D24)
  -> engine reads the SNAPSHOT (never the fetch): split-adjusted views for signals,
  reconstructed as-traded prices for execution (D6/D75), explicit dividend flows
  (longs credited / shorts debited), split-scaled positions through XOP's 2020-03-30
  1-for-4 reverse split.

Offline and deterministic; the snapshot_id is content-addressed, so anyone can
reproduce it from the committed fixture.

Run: uv run python scripts/run_first_result_v2.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.equity_bricks import (
    BorrowFee,
    DividendFlow,
    IBKRCommission,
    ImpactParams,
    MarginInterest,
    SqrtImpact,
)
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import (
    as_declared_dividends,
    as_traded_from_adjusted,
    load_events_json,
)
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import Snapshot, SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.sweep import render_sweep_table, run_cost_sweep
from backtest_framework.instruments.equity import Equity
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "data" / "fixtures" / "xle_xop_daily_2015_2024_raw.csv"
EVENTS = REPO / "data" / "fixtures" / "xle_xop_daily_2015_2024_raw_events.json"
RESULTS = REPO / "docs" / "results" / "first_real_number_v2.md"
SNAPSHOT_ROOT = REPO / "data" / "snapshots"

STARTING_CASH = 100_000.0

# From scripts/fetch_fixture_v2.py on the committed fixture: sigma on the (already
# split-adjusted) provider closes; ADV = full-sample mean share volume in the
# provider's volume frame. Static full-sample calibration - same caveat as v1 (D66,
# D70); pre-split XOP impact is additionally approximate because ADV's share frame
# differs from as-traded shares by the split ratio (stated in the results doc).
IMPACT_PARAMS = {
    "XLE": ImpactParams(sigma_daily=0.018965, adv_shares=41_843_064),
    "XOP": ImpactParams(sigma_daily=0.026689, adv_shares=5_399_803),
}

STRATEGY_PARAMS = dict(lookback=60, entry_z=2.0, exit_z=0.5, leg_weight=1.0)

CONFIG = {
    "strategy": {"type": "zscore_pairs", "pair": ["XLE", "XOP"], **STRATEGY_PARAMS},
    "data_pipeline": "raw fixture -> clean-v1 -> validate-v1 -> snapshot; adjusted views / as-traded execution; dividend flows + split scaling (D72-D76)",
    "cost_stack": {
        "trade": [
            {"type": "ibkr_commission_fixed", "per_share": 0.005, "min": 1.00, "cap_pct": 0.01},
            {
                "type": "sqrt_impact",
                "coefficient": 1.0,
                "params": {s: {"sigma_daily": p.sigma_daily, "adv_shares": p.adv_shares} for s, p in IMPACT_PARAMS.items()},
            },
            {"type": "pct_of_notional_spread", "bps": 1.0},
        ],
        "carry_per_leg": [{"type": "borrow_fee", "annual_rate": 0.0025}],
        "carry_portfolio": [{"type": "margin_interest", "annual_rate": 0.06}],
        "event_flows": [{"type": "dividend_flow", "source": "snapshot events, as-declared frame"}],
    },
    "starting_cash": STARTING_CASH,
}


def create_and_load_snapshot(store_root: Path = SNAPSHOT_ROOT) -> Snapshot:
    """Fixture -> clean -> validate -> freeze -> LOAD (the engine only ever sees the
    loaded snapshot, D24/D72). Content-addressed: rerunning is idempotent."""
    bars, volumes = load_fixture_csv_with_volumes(FIXTURE)
    actions = load_events_json(EVENTS)

    cleaned, cleaning_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)

    store = SnapshotStore(store_root)
    snapshot_id = store.create(
        cleaned,
        actions,
        volumes_by_symbol=None,  # volumes not needed downstream yet; kept in the fixture
        cleaning_report=cleaning_report,
        validation=validation,
        extra_meta={"source_fixture": FIXTURE.name},
    )
    return store.load(snapshot_id)


def build_run_inputs(snapshot: Snapshot):
    execution = {
        symbol: as_traded_from_adjusted(series, snapshot.actions.splits_by_symbol.get(symbol, ()))
        for symbol, series in snapshot.bars_by_symbol.items()
    }
    views = snapshot.bars_by_symbol  # provider frame: split-adjusted, signal-continuous
    declared_dividends = {
        symbol: tuple(as_declared_dividends(divs, snapshot.actions.splits_by_symbol.get(symbol, ())))
        for symbol, divs in snapshot.actions.dividends_by_symbol.items()
    }
    splits = {symbol: list(s) for symbol, s in snapshot.actions.splits_by_symbol.items() if s}
    return execution, views, declared_dividends, splits


def build_cost_stack(declared_dividends) -> CostStack:
    return CostStack(
        trade_bricks=(
            IBKRCommission(),
            SqrtImpact(params_by_symbol=IMPACT_PARAMS),
            PercentOfNotionalSpread(bps=1.0),
        ),
        carry_bricks=(BorrowFee(annual_rate=0.0025),),
        portfolio_carry_bricks=(MarginInterest(annual_rate=0.06),),
        event_flow_bricks=(DividendFlow(dividends_by_symbol=declared_dividends),),
    )


def make_strategies():
    return [ZScorePairsStrategy(strategy_id="zscore_pairs", instrument_a="XLE", instrument_b="XOP", **STRATEGY_PARAMS)]


def main() -> int:
    snapshot = create_and_load_snapshot()
    execution, views, declared_dividends, splits = build_run_inputs(snapshot)
    instruments = {"XLE": Equity(symbol="XLE"), "XOP": Equity(symbol="XOP")}

    registry = TrialRegistry(REPO / "trial_registry.sqlite")
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    sweep = run_cost_sweep(
        bars_by_instrument=execution,
        instruments=instruments,
        make_strategies=make_strategies,
        base_cost_stack=build_cost_stack(declared_dividends),
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
        trial_registry=registry,
        trial_id_prefix=f"first-real-number-v2-{run_stamp}",
        config=CONFIG,
        snapshot_id=snapshot.snapshot_id,
        seed=0,
        splits_by_instrument=splits,
        view_bars_by_instrument=views,
    )

    cleaning = snapshot.meta["cleaning_report"]
    validation = snapshot.meta["validation"]
    n_bars = len(sweep.runs[0].result.equity_curve)
    warnings = [v for v in validation["violations"] if not v["hard"]]

    doc = f"""# The First Real Number, v2 — XLE/XOP through the hardened data layer

**Date produced:** {datetime.now(timezone.utc).date().isoformat()} · **Snapshot:**
`{snapshot.snapshot_id}` (content-addressed, D72 — reproducible from the committed
`{FIXTURE.name}`) · **Bars:** {n_bars} aligned daily bars, 2015–2024 · **Starting
capital:** ${STARTING_CASH:,.0f} · **Seed:** 0 · Trials logged as
`first-real-number-v2-{run_stamp}-<multiplier>x`.

Same strategy, pair, parameters, and sweep as
[v1](first_real_number.md) — v1 stays as the historical Phase C milestone (D76). What
changed is the data path (Step 7, D72–D75): cleaner → sanity gate → frozen snapshot;
**split-adjusted prices for signals, reconstructed as-traded prices for execution**
(commissions on the ~$8 XOP shares actually traded pre-split, not the $32 phantom
ones); **explicit dividend cash flows** (long leg credited, short leg debited — 81
ex-dates across the pair); XOP's 2020-03-30 1-for-4 reverse split scales positions
mid-run.

## Pipeline provenance (attached to the snapshot, D24/D25/D26)

- Cleaning (`{cleaning["ruleset"]}`): {len(cleaning["changes"])} change(s) on 5,030 raw bars.
- Validation (`{validation["version"]}`): passed = {validation["passed"]},
  {len(warnings)} warning(s) recorded (genuine 2020 crash-day moves and volume
  anomalies — see D74's calibration note; warnings never quarantine).

## The sweep (D8)

{render_sweep_table(sweep)}

## v1 → v2

| | v1 (adjusted prices, no flows) | v2 (hardened path) |
|---|---|---|
| 0× | +13.21% | {sweep.net_pnls()[0][1] / STARTING_CASH:+.2%} |
| 1× | −22.70% | {sweep.net_pnls()[2][1] / STARTING_CASH:+.2%} |
| 4× | −76.43% | {sweep.net_pnls()[4][1] / STARTING_CASH:+.2%} |

Differences come from: dividend economics now explicit (the short leg *pays* ~1–3%/yr
in dividends it previously escaped; the long leg receives them), commissions/impact on
true as-traded notionals, the split handled as an event rather than baked into prices,
and slightly different signal values (split-adjusted-only views vs v1's
dividend-and-split-adjusted closes).

## Caveats closed by v2 (were v1 caveats 3–4)

- ~~Adjusted prices corrupting cost notionals~~ → as-traded execution (D75).
- ~~Dividend flows unmodeled~~ → explicit DividendFlow, both legs (D6).
- ~~No snapshot/cleaning/sanity gate~~ → full D24/D25/D26 pipeline, provenance in
  the snapshot meta.

## Caveats that remain (R3: labeled, not hidden)

1. **Famous-pair selection bias (D22)** — unchanged; honest pair selection is Step 12.
2. **Full-sample σ/ADV calibration (D66/D70)** — unchanged; and ADV's share frame is
   the provider's, so pre-split XOP impact is approximate (≤2× in √-terms).
3. **Single-source data (D26's deferred second-source cross-check)** — the events
   table and prices both come from yfinance; the dividend/split values were
   sanity-checked for internal consistency (frame continuity) but not against an
   independent source.
4. **No fitted parameters / no train-test split** — unchanged from v1 (D69).

## Reproduction

`uv run python scripts/run_first_result_v2.py` — offline, deterministic; recreates the
same content-addressed snapshot and identical numbers. Asserted in
`tests/integration/test_first_result_v2_e2e.py`.
"""
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(doc, encoding="utf-8")
    registry.close()

    print(f"snapshot: {snapshot.snapshot_id}")
    print(f"cleaning changes: {len(cleaning['changes'])}, validation warnings: {len(warnings)}")
    print(render_sweep_table(sweep))
    print(f"\nwrote {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
