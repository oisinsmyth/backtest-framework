"""The cross-engine reconciliation, extracted bar by bar instead of summarised.

    uv run python scripts/run_cross_engine_residuals.py --build    # writes data/cross_engine_residuals.json
    uv run python scripts/run_cross_engine_residuals.py --verify   # re-runs both engines, compares
    uv run python scripts/run_cross_engine_residuals.py --status

WHY AN ARTIFACT AT ALL
----------------------
`tests/integration/test_cross_engine.py` asserts the two engines agree and then throws the
evidence away: `pytest.approx` returns a bool, not a residual. The reconciliation document
(`docs/verification/cross_engine_reconciliation.md:40`) therefore quotes three numbers -- 1,370
trades, `$159,233.023491`, a max divergence of `$0.0000002186` -- that nothing in the repository
can re-derive. This writes them down as PRIMITIVES: the whole per-bar residual series, both
fill-bar index lists, both final values. The figure and its test each recompute what they need
from those lists, so neither is quoting the other.

The raw residuals are ~60 KB. That is the point of storing them rather than a five-number
summary: a summary is a thing a figure can only repeat, and a figure that repeats a summary is
an illustration rather than evidence.

THE SCHEDULE LIVES HERE, AND THE TEST IMPORTS IT
------------------------------------------------
`_ma_cross_weights` was in the integration test. Copying it here would have left two definitions
of the schedule being reconciled, and the day they drifted the figure would depict a
reconciliation nobody ran -- while both files still passed. The test now loads this module by
`importlib` (the `test_readme_counts_are_current.py:32` idiom) and calls this function, so there
is exactly one schedule.

WHAT THIS IS NOT
----------------
It is not a widening of the comparison. `scope` below is carried into the JSON and onto the
figure's face because `README.md:12` says "penny-exact | the simulator reconciled against
vectorbt" with no qualifier, and the reconciliation is one instrument, long-flat, proportional
fees only. Carry, dividends, splits and margin are ours alone.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.costs.bricks import PercentOfNotionalSpread  # noqa: E402
from backtest_framework.costs.stack import CostStack  # noqa: E402
from backtest_framework.data.csv_fixture import load_fixture_csv  # noqa: E402
from backtest_framework.engine.allocator import ConstantSplitAllocator  # noqa: E402
from backtest_framework.engine.backtest import run_backtest  # noqa: E402
from backtest_framework.engine.strategy import ScheduledWeightStrategy  # noqa: E402
from backtest_framework.instruments.equity import Equity  # noqa: E402

FIXTURE = REPO / "data" / "fixtures" / "xle_xop_daily_2015_2024.csv"
ARTIFACT = REPO / "data" / "cross_engine_residuals.json"

SYMBOL = "XLE"
TOLERANCE = 1e-6
"""D47, and `tests/integration/test_cross_engine.py:27`. Named in one place per process."""
FEE_BPS = 5.0
STARTING_CASH = 100_000.0

SCOPE = (
    "One instrument (XLE daily closes), long-flat only, fractional shares, proportional fees "
    "only, and no carry, dividends, splits, margin or multi-leg netting — the shared subset of "
    "both engines' capabilities. Everything outside that subset is ours alone and is anchored "
    "by the golden master, not by this reconciliation."
)

# The lists written on one line each rather than one element per line. An indent=2 dump of 5,030
# floats is 10,000 lines of diff nobody reads; the residuals are a panel, and a panel's diff is
# useful only as "this line changed".
COMPACT = ("abs_residuals", "rel_residuals", "fill_bars_ours", "fill_bars_theirs")


def _ma_cross_weights(
    closes: list[float], fast: int = 10, slow: int = 30, weight: float = 0.6
) -> list[float]:
    """Computed ONCE; consumed by both engines. Weight 0.6 (not 1.0) deliberately:
    at ~full investment vectorbt reserves fees from the purchase while we pay fees
    from cash — below that boundary the sizing conventions are identical (D79).

    Lives here rather than in `tests/integration/test_cross_engine.py`, which imports it, so the
    schedule the test reconciles and the schedule the figure is drawn from cannot be two things.
    """
    weights = []
    for i in range(len(closes)):
        if i + 1 < slow:
            weights.append(0.0)
        else:
            f = sum(closes[i - fast + 1 : i + 1]) / fast
            s = sum(closes[i - slow + 1 : i + 1]) / slow
            weights.append(weight if f > s else 0.0)
    return weights


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def reconcile() -> dict:
    """Run both engines on the identical schedule and return everything measured.

    Deliberately returns primitives only -- no max, no argmax, no bucket counts. Those are
    derived in `scripts/figures/build_cross_engine.py` and re-derived independently in
    `tests/unit/test_figure_cross_engine.py`; putting a max in here would let both read it and
    agree about a number neither had computed.
    """
    started = time.time()
    warnings.filterwarnings("ignore")

    import numpy as np
    import pandas as pd
    import vectorbt as vbt

    bars = load_fixture_csv(FIXTURE)[SYMBOL]
    closes = [tb.bar.close for tb in bars]
    weights = _ma_cross_weights(closes)

    ours = run_backtest(
        bars_by_instrument={SYMBOL: bars},
        instruments={SYMBOL: Equity(symbol=SYMBOL, quantity_precision=8)},
        strategies=[
            ScheduledWeightStrategy(strategy_id="ma", weights_by_instrument={SYMBOL: weights})
        ],
        cost_stack=CostStack(trade_bricks=(PercentOfNotionalSpread(bps=FEE_BPS),)),
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
    )
    our_curve = [nav for _, nav in ours.equity_curve]

    close_s = pd.Series(closes)
    pf = vbt.Portfolio.from_orders(
        close_s,
        size=pd.Series(weights),
        size_type="targetpercent",
        fees=FEE_BPS / 10_000.0,
        init_cash=STARTING_CASH,
        price=close_s,
    )
    their_curve = [float(v) for v in pf.value()]

    if len(our_curve) != len(their_curve):  # pragma: no cover - the fixture is committed
        raise SystemExit(f"curve lengths differ: {len(our_curve)} vs {len(their_curve)}")

    # Bar index, not timestamp: the figure's second panel is one column per bar and vectorbt's
    # order records are indexed positionally, so the two lists have to be comparable as sets.
    bar_of = {tb.timestamp: i for i, tb in enumerate(bars)}
    fill_bars_ours = [bar_of[ts] for ts, *_ in ours.fills]
    if len(set(fill_bars_ours)) != len(fill_bars_ours):  # pragma: no cover - one instrument
        raise SystemExit("two of our fills landed on one bar; the per-bar panel would be a lie")
    fill_bars_theirs = [int(i) for i in pf.orders.records["idx"]]

    abs_residuals = [abs(a - b) for a, b in zip(our_curve, their_curve)]
    # Relative to THEIRS, because vectorbt is the reference engine; dividing by ours would make
    # the denominator the thing under test.
    rel_residuals = [d / abs(b) if b != 0.0 else 0.0 for d, b in zip(abs_residuals, their_curve)]

    return {
        "produced": time.strftime("%Y-%m-%d"),
        "generator": "scripts/run_cross_engine_residuals.py",
        "reference_engine": f"vectorbt {vbt.__version__}",
        "versions": {
            "vectorbt": vbt.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "python": platform.python_version(),
        },
        "fixture": FIXTURE.relative_to(REPO).as_posix(),
        "fixture_sha256": sha256_of(FIXTURE),
        "symbol": SYMBOL,
        "schedule": "MA(10)/MA(30) cross, target weight 0.6 when fast > slow else 0",
        "fee_bps_per_side": FEE_BPS,
        "starting_cash": STARTING_CASH,
        "scope": SCOPE,
        "tolerance": TOLERANCE,
        "tolerance_source": "D47; `TOLERANCE`, tests/integration/test_cross_engine.py:29",
        "bars": len(our_curve),
        "fills_ours": len(fill_bars_ours),
        "fills_theirs": len(fill_bars_theirs),
        "final_ours": our_curve[-1],
        "final_theirs": their_curve[-1],
        "fill_bars_ours": sorted(fill_bars_ours),
        "fill_bars_theirs": sorted(fill_bars_theirs),
        "abs_residuals": abs_residuals,
        "rel_residuals": rel_residuals,
        "elapsed_seconds": round(time.time() - started, 1),
    }


def dumps(payload: dict) -> str:
    """`indent=2`, except the four panel-shaped lists, which go on one line each."""
    stub = {k: (f"@@{k}@@" if k in COMPACT else v) for k, v in payload.items()}
    text = json.dumps(stub, indent=2)
    for key in COMPACT:
        text = text.replace(f'"@@{key}@@"', json.dumps(payload[key]))
    return text + "\n"


def load() -> dict:
    if ARTIFACT.exists():
        return json.loads(ARTIFACT.read_text(encoding="utf-8"))
    return {}


def _summarise(payload: dict) -> str:
    rel = payload["rel_residuals"]
    worst = max(range(len(rel)), key=lambda i: rel[i])
    return (
        f"bars {payload['bars']}  fills {payload['fills_ours']}/{payload['fills_theirs']}  "
        f"final ${payload['final_ours']:,.6f} / ${payload['final_theirs']:,.6f}  "
        f"max absolute ${max(payload['abs_residuals']):.10f}  "
        f"max relative {rel[worst]:.3e} at bar {worst}"
    )


def cmd_build() -> int:
    payload = reconcile()
    ARTIFACT.write_text(dumps(payload), encoding="utf-8", newline="\n")
    print(f"wrote {ARTIFACT.relative_to(REPO).as_posix()} in {payload['elapsed_seconds']}s")
    print(_summarise(payload))
    return 0


def cmd_verify() -> int:
    """Re-run both engines and compare the measurement, not the provenance.

    `produced`, `elapsed_seconds` and `versions` are expected to move -- a different machine has
    a different clock and a different vectorbt. They are REPORTED, because a residual series that
    still matches under a new vectorbt is a stronger statement than one that does not know it
    changed, but only the measured fields fail this command.
    """
    committed = load()
    if not committed:
        print("no artifact -- run --build first")
        return 1

    fresh = reconcile()
    measured = (
        "bars",
        "fills_ours",
        "fills_theirs",
        "final_ours",
        "final_theirs",
        "fill_bars_ours",
        "fill_bars_theirs",
        "abs_residuals",
        "rel_residuals",
        "fixture_sha256",
    )
    drifted = [k for k in measured if committed.get(k) != fresh[k]]
    for key, old, new in (
        ("versions", committed.get("versions"), fresh["versions"]),
        ("produced", committed.get("produced"), fresh["produced"]),
    ):
        if old != new:
            print(f"note     {key}: {old} -> {new}")

    if drifted:
        for key in drifted:
            if key in COMPACT:
                print(f"CHANGED  {key} ({len(committed.get(key, []))} -> {len(fresh[key])} items)")
            else:
                print(f"CHANGED  {key}: {committed.get(key)!r} -> {fresh[key]!r}")
        print("the reconciliation moved. Rebuild and rebuild the figure that quotes it.")
        return 1

    print("the residual series reproduces exactly")
    print(_summarise(fresh))
    return 0


def cmd_status() -> int:
    payload = load()
    if not payload:
        print("no artifact")
        return 1
    print(f"produced   {payload['produced']}  ({payload['reference_engine']})")
    print(f"fixture    {payload['fixture']}  {payload['fixture_sha256'][:16]}")
    print(f"tolerance  {payload['tolerance']:g}  ({payload['tolerance_source']})")
    print(_summarise(payload))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    if args.build:
        return cmd_build()
    if args.verify:
        return cmd_verify()
    if args.status:
        return cmd_status()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
