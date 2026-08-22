"""The cross-sectional portfolio on 57 ETFs — the out-of-sample test. (D188)

D183 found that holding the long breakout book across 62 coins at once lifts it from a
median single-coin Sharpe of +0.44 to a portfolio Sharpe of +1.28. D185 charged the
rebalancing cost and D186/D187 charged market impact; the edge over a daily-rebalanced
equal-weight basket survived both at **+0.075**, dying around $66M of capacity.

Every one of those numbers is **one crypto cross-section over one bull-dominated decade**.
D180 is the standing lesson: E1 cleared its bar five times on BTC and ETH and failed on 62
coins, because those two sat at the 97th and 85th percentile of the variable that decided
the outcome. A result measured on a favourable sample is not a result about the world.

This runs the SAME long baseline, unchanged, on a different asset class.

    uv run python scripts/run_etf_universe.py

## What had to change, and what deliberately did not

**The strategy does not change.** 40-bar entry channel, 10-bar exit, `baseline_variant()`
itself — the same object the crypto universe study runs.

**Four things had to.** Each is a fact about the instruments, not a tuning choice:

- **`periods_per_year = 252`**, not 365. Equities do not trade weekends.
- **Volume is SHARES**, not quote-currency notional (D187). Stated explicitly, because
  getting it wrong scales every impact charge by the square root of the price.
- **Dividends are paid.** 2,285 of them across 53 of the 57 symbols, plus 14 splits. A
  price-only run would understate every total return — and would understate the BENCHMARK's
  more than the strategy's, because the strategy is flat about half the time and collects
  fewer of them. Omitting them would flatter the strategy.
- **Two crypto-specific screens are disabled**, see `ETF_POLICY`.

## What this cannot be

**These 57 ETFs all survived.** Identical 2,515-bar spans, no staggered listings, no
failures. The crypto universe was deliberately built to contain the assets that died; this
one is survivorship-clean by construction, which is the opposite property. It tests whether
the mechanism generalises to another asset class. It does not test the crypto numbers.
"""

from __future__ import annotations

import dataclasses
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research import breakout_study as bs
from backtest_framework.research import breakout_universe as bu

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_portfolio_universe import _charge, _equal_weight_arm, dated_returns  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw_events.json"
REGISTRY_PATH = REPO / "data" / "etf_universe_registry.sqlite"
RESULTS = REPO / "docs" / "results" / "etf_universe.md"
SUMMARY_JSON = REPO / "data" / "etf_universe_summary.json"

NL = "\n"
WARMUP = 252

ETF_POLICY = dataclasses.replace(
    bu.DEFAULT_POLICY,
    min_median_abs_daily_return=0.0,
    min_median_daily_volume_usd=0.0,
)
"""The D140 policy with its two CRYPTO-SPECIFIC screens disabled, and only those.

**The peg screen is dropped because it has no equity referent.** It exists to exclude
stablecoins — instruments whose *design* pins their price. Applied verbatim it would drop
12 of 57 ETFs: `SHY`, `AGG`, `TIP`, `HYG`, `IEF`, `LQD`, `XLP`, `VIG`, `DIA`, `VYM` and two
more, at 0.04%–0.47% median daily move. A bond fund is genuinely low-volatility, not
pegged, and `DIA` is the Dow. Dropping the screen ADMITS the instruments a breakout book
should find hardest, so it is the conservative direction, not the flattering one.

**The liquidity floor is dropped because its units do not apply.** It compares the raw
volume column against a USD threshold, and ETF volume is in SHARES (D187). Comparing shares
to dollars is exactly the error D187 records. It is also non-binding here, and that was
measured rather than assumed: every one of the 57 clears a $5M *notional* floor by a wide
margin, the thinnest being `VYM` at $99.7M/day.

`min_bars` is untouched and every symbol clears it — all 57 carry 2,515 bars."""

STUDY = dataclasses.replace(bs.BreakoutStudyConfig(), periods_per_year=252.0)
"""252 trading days, not 365. Everything else — train 252 / test 63 / step 63, next-open
fills, the risk-free rate, the seed — is the crypto study's configuration untouched."""


@dataclasses.dataclass(frozen=True)
class EquityTier(bs.CostTier):
    """Equity trading costs, plus the dividend flow that holding an ETF actually pays.

    The trade bricks are the ones `pairs_study.py` established for this same fixture: an
    IBKR commission with its per-order minimum, and a spread. `fee_bps` carries the spread,
    so the crypto tiers' 40 bp can be run through the identical code path as a stated
    sensitivity rather than a separate implementation.

    No `borrow_fee` and no `margin_interest`: this is a long-only, unlevered book and
    charging it either would be inventing a cost it does not incur."""

    commission: bool = True

    def cost_stack_config(self) -> dict[str, Any]:
        trade: list[dict[str, Any]] = []
        if self.commission:
            trade.append({"type": "ibkr_commission"})
        trade.append({"type": "percent_spread", "bps": self.fee_bps})
        if self.impact_coefficient:
            trade.append(
                {
                    "type": "sqrt_impact",
                    "coefficient": self.impact_coefficient,
                    "calibration": "full_sample",
                    "volume_units": self.volume_units,
                }
            )
        return {
            "trade_bricks": trade,
            "carry_bricks": [],
            "portfolio_carry_bricks": [],
            # Dividends are an economic flow, not a cost model choice, so BOTH arms carry
            # them. Only the trading cost differs between the two tiers below.
            "event_flow_bricks": [{"type": "dividend_flow", "source": "snapshot_declared"}],
        }


TIERS = (
    EquityTier("equity_1bp", 1.0, "taker", volume_units="shares"),
    EquityTier("crypto_40bp", 40.0, "taker", volume_units="shares", commission=False),
)
"""Headline first, sensitivity second — both fixed before the run, neither chosen after.

`equity_1bp` is what these instruments actually cost. `crypto_40bp` is the crypto study's
own cost assumption applied here, so the obvious question — *what if you charged it what
you charged the coins?* — is answered rather than left open. 40 bp per trade on `SPY` is
not a real cost; it is a stated handicap."""


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
        RESULTS.write_text(build_report(payload), encoding="utf-8")
        print(f"re-rendered {RESULTS.name} from {SUMMARY_JSON.name}")
        return 0

    started = time.time()
    raw_bars, raw_volumes = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, cleaning_report = clean(raw_bars)
    actions = load_events_json(EVENTS)
    volumes = {
        s: bu.align_volumes(cleaned[s], raw_bars[s], raw_volumes[s]) for s in cleaned
    }
    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(
        cleaned,
        actions,
        volumes_by_symbol=volumes,
        cleaning_report=cleaning_report,
        validation=None,
        extra_meta={"source_fixture": FIXTURE.name, "study": "etf_universe_v1"},
    )
    snapshot = store.load(snapshot_id)

    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()
    registry = TrialRegistry(REGISTRY_PATH)

    arms: dict[str, Any] = {}
    for tier in TIERS:
        print(f"running {tier.name} across the ETF universe ...", flush=True)
        run = bu.run_universe_study(
            snapshot.bars_by_symbol,
            volumes,
            registry,
            snapshot_id,
            cohorts={s: "etf" for s in cleaned},
            study=STUDY,
            tiers=(tier,),
            policy=ETF_POLICY,
            end_date=datetime(2024, 12, 31).date(),
            trial_id_prefix=f"etf-universe-{tier.name}",
            variant=bu.baseline_variant(),
            progress=lambda m: None,
            actions=actions,
        )
        arms[tier.name] = run

    payload = build_payload(arms, snapshot, volumes, actions, snapshot_id)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RESULTS.write_text(build_report(payload), encoding="utf-8")
    print(
        f"ran {payload['n_symbols']} ETFs over {payload['n_dates']:,} dates in "
        f"{time.time() - started:.0f}s"
    )
    print(f"wrote {RESULTS.name} and {SUMMARY_JSON.name}")
    return 0


def _stats(returns: list[float]) -> dict[str, float]:
    nav, peak, worst = 1.0, 1.0, 0.0
    for r in returns:
        nav *= 1.0 + r
        peak = max(peak, nav)
        worst = max(worst, 1.0 - nav / peak) if peak > 0 else worst
    return {
        "sharpe": bs.sharpe(returns, STUDY.rf_annual, STUDY.periods_per_year),
        "total_return": nav - 1.0,
        "max_drawdown": worst,
        "n_bars": len(returns),
    }


def build_payload(arms, snapshot, volumes, actions, snapshot_id) -> dict:
    out_arms: dict[str, Any] = {}
    dates_ref: list[str] = []
    per_symbol_sharpe: dict[str, dict[str, float]] = {}
    for tier in TIERS:
        run = arms[tier.name]
        per_symbol = {}
        sharpes = {}
        for symbol, srun in run.runs.items():
            v = srun.by_tier[tier.name].variant
            dated, _ = dated_returns(v.oos_equity)
            per_symbol[symbol] = dict(dated)
            sharpes[symbol] = v.sharpe_annual(STUDY)
        per_symbol_sharpe[tier.name] = sharpes
        dates = sorted({d for s in per_symbol.values() for d in s})
        dates_ref = dates_ref or dates
        gross, turn = _equal_weight_arm(dates, per_symbol)
        net = _charge(gross, turn, tier.fee_bps)
        out_arms[tier.name] = {
            "fee_bps": tier.fee_bps,
            **_stats(net[WARMUP:]),
            "median_single_sharpe": statistics.median(list(sharpes.values())),
            "mean_single_sharpe": statistics.fmean(list(sharpes.values())),
            "mean_daily_turnover": statistics.fmean(turn[WARMUP:]),
        }

    # ---- benchmarks, charged the same way ------------------------------------------
    # Price returns PLUS declared dividends, so the benchmark is a total-return basket.
    # A price-only benchmark would be the easier thing to build and would hand the
    # strategy a free ~2%/yr, since it is flat about half the time and collects fewer.
    raw: dict[str, dict[str, float]] = {}
    for symbol, bars in snapshot.bars_by_symbol.items():
        divs = dict(
            (ts.date().isoformat(), amt)
            for ts, amt in actions.dividends_by_symbol.get(symbol, ())
        )
        r = {}
        for a, b in zip(bars, bars[1:]):
            if a.bar.close <= 0:
                continue
            d = b.timestamp.date().isoformat()
            r[d] = (b.bar.close + divs.get(d, 0.0)) / a.bar.close - 1.0
        raw[symbol] = r
    bench_gross, bench_turn = _equal_weight_arm(dates_ref, raw)
    spy = [raw.get("SPY", {}).get(d, 0.0) for d in dates_ref]

    benchmarks = {}
    for tier in TIERS:
        benchmarks[tier.name] = {
            "equal_weight": _stats(_charge(bench_gross, bench_turn, tier.fee_bps)[WARMUP:]),
            # Buy and hold trades once and never again; charging it a daily rate would
            # invent a cost it does not pay.
            "spy_hold": _stats(spy[WARMUP:]),
        }
    edges = {
        t.name: out_arms[t.name]["sharpe"] - benchmarks[t.name]["equal_weight"]["sharpe"]
        for t in TIERS
    }
    return {
        "snapshot_id": snapshot_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "periods_per_year": STUDY.periods_per_year,
        "warmup_bars": WARMUP,
        "n_symbols": len(per_symbol_sharpe[TIERS[0].name]),
        "n_dates": len(dates_ref),
        "first_date": dates_ref[0],
        "last_date": dates_ref[-1],
        "policy": {
            "peg_screen_disabled": True,
            "liquidity_floor_disabled": True,
            "min_bars": ETF_POLICY.min_bars,
        },
        "arms": out_arms,
        "benchmarks": benchmarks,
        "edges": edges,
        "per_symbol_sharpe": per_symbol_sharpe,
    }


def build_report(p: dict) -> str:
    rows = []
    for name, a in p["arms"].items():
        b = p["benchmarks"][name]
        rows.append(
            f"| `{name}` | {a['sharpe']:+.3f} | {a['total_return'] * 100:+,.1f}% | "
            f"{a['max_drawdown'] * 100:.1f}% | {b['equal_weight']['sharpe']:+.3f} | "
            f"{b['equal_weight']['total_return'] * 100:+,.1f}% | "
            f"{b['equal_weight']['max_drawdown'] * 100:.1f}% | **{p['edges'][name]:+.3f}** |"
        )
    spy = p["benchmarks"][list(p["arms"])[0]]["spy_hold"]
    return f"""# The cross-sectional portfolio on 57 ETFs

**Produced:** {p["generated_utc"][:10]} ·
**Snapshot:** `{p["snapshot_id"]}` ·
**Reproduce:** `uv run python scripts/run_etf_universe.py` (offline, deterministic)

## What this is

The same long breakout baseline — 40-bar entry, 10-bar exit,
`breakout_universe.baseline_variant()` itself — run unchanged on a different asset class.
D183's portfolio result and everything built on it (D185's rebalancing cost, D186/D187's
capacity) are **one crypto cross-section over one bull-dominated decade**. D180 is the
standing lesson on what that is worth.

{p["n_symbols"]} ETFs, {p["n_dates"]:,} dates, {p["first_date"]} to {p["last_date"]}.
`periods_per_year = {p["periods_per_year"]:.0f}`. The first {p["warmup_bars"]} bars are
weighting warm-up and are excluded from every figure, all arms alike.

**Dividends are paid.** 2,285 of them across 53 symbols, plus 14 splits, applied through
`DividendFlow` on both the strategy and the benchmark. A price-only run would have handed
the strategy a free ~2%/yr, because it is flat about half the time and collects fewer.

## The result

| Cost tier | Strategy Sharpe | Return | Max DD | Basket Sharpe | Return | Max DD | Edge |
|---|---|---|---|---|---|---|---|
{NL.join(rows)}

**SPY buy & hold** over the same span: Sharpe {spy["sharpe"]:+.3f}, return
{spy["total_return"] * 100:+,.1f}%, max drawdown {spy["max_drawdown"] * 100:.1f}%.

{_verdict(p)}

{_single_symbol_block(p)}

## Standing caveats

1. **These 57 ETFs all survived.** Identical 2,515-bar spans, no staggered listings, no
   failures. The crypto universe was built to contain the assets that DIED; this one is
   survivorship-clean by construction. That is the opposite property, and it means a good
   result here would be the easier kind.
2. **Two crypto-specific screens are disabled** — the peg screen, which has no equity
   referent, and the liquidity floor, whose units do not apply (D187). Both are stated in
   `ETF_POLICY` with the measurement behind them. `min_bars` is untouched.
3. **It is a return-aggregation portfolio, not a portfolio backtest** — no shared capital
   constraint and no cost for rebalancing between symbols beyond the flat charge above
   (D183's caveat, unchanged).
4. **Market impact is OFF here.** This asks whether the effect exists out of sample, not
   what it costs at size; D186/D187 answered that for crypto. Turning it on would vary two
   things at once.
5. **57 correlated index funds are not 57 independent tests**, any more than 62 coins were.
"""


def _verdict(p: dict) -> str:
    head_name = list(p["arms"])[0]
    a = p["arms"][head_name]
    b = p["benchmarks"][head_name]["equal_weight"]
    spy = p["benchmarks"][head_name]["spy_hold"]
    edge = p["edges"][head_name]
    other = list(p["arms"])[1]
    dd = a["max_drawdown"] - b["max_drawdown"]
    if edge > 0:
        head = (
            f"**The effect transfers.** At realistic equity costs the portfolio scores "
            f"{a['sharpe']:+.3f} against the equal-weight basket's {b['sharpe']:+.3f}, an "
            f"edge of **{edge:+.3f}** — on an asset class the strategy was never developed "
            f"on, with the same configuration and no refitting. That is the first evidence "
            f"in this project that anything here belongs to the RULE rather than to the "
            f"sample it was found on."
        )
    else:
        head = (
            f"**The effect does not transfer.** At realistic equity costs the portfolio "
            f"scores {a['sharpe']:+.3f} against the equal-weight basket's {b['sharpe']:+.3f} "
            f"— an edge of **{edge:+.3f}**. The crypto portfolio's +0.075 does not reproduce "
            f"on an asset class the strategy was not developed on, which is what an "
            f"out-of-sample test is for."
        )
    dd_note = (
        f" **Drawdown still improves**, {b['max_drawdown'] * 100:.1f}% → "
        f"{a['max_drawdown'] * 100:.1f}% ({dd * 100:+.1f} pp) — the one property that has "
        f"survived every test in this project, and it survives this one too."
        if dd < 0
        else f" **And drawdown does not improve either**: {b['max_drawdown'] * 100:.1f}% → "
        f"{a['max_drawdown'] * 100:.1f}% ({dd * 100:+.1f} pp). The drawdown result was the "
        f"strongest thing the crypto work found, and it is absent here."
    )
    spy_note = (
        f"{NL}{NL}Against **SPY buy & hold** ({spy['sharpe']:+.3f} Sharpe, "
        f"{spy['total_return'] * 100:+,.0f}%, {spy['max_drawdown'] * 100:.1f}% drawdown) the "
        f"portfolio returns {a['total_return'] * 100:+,.0f}%. A single-asset benchmark is "
        f"not the like-for-like one — the strategy is a 57-name basket — but it is the one "
        f"a reader will ask about."
    )
    sens = (
        f"{NL}{NL}At the crypto study's own 40 bp the edge is "
        f"**{p['edges'][other]:+.3f}**, against {p['arms'][other]['sharpe']:+.3f} for the "
        f"strategy and {p['benchmarks'][other]['equal_weight']['sharpe']:+.3f} for the "
        f"basket. That tier is a stated handicap, not a real cost for these instruments."
    )
    return head + dd_note + spy_note + sens


def _single_symbol_block(p: dict) -> str:
    """The diversification claim, restated on this asset class.

    D183's finding was not that the breakout rule is good on one instrument — it is that
    holding many of them at once lifts the book far above the median single one. Whether
    THAT reproduces is a separate question from whether the edge does."""
    head_name = list(p["arms"])[0]
    a = p["arms"][head_name]
    lift = a["sharpe"] - a["median_single_sharpe"]
    sharpes = sorted(p["per_symbol_sharpe"][head_name].items(), key=lambda kv: -kv[1])
    best = ", ".join(f"`{s}` {v:+.2f}" for s, v in sharpes[:4])
    worst = ", ".join(f"`{s}` {v:+.2f}" for s, v in sharpes[-4:])
    return f"""## Does the diversification lift reproduce?

D183's actual finding was not that the breakout rule works on any one instrument. It was
that **holding many of them at once** lifts the book far above the median single one —
+0.44 → +1.28 on crypto. That is arithmetic, so it should reproduce anywhere the errors are
less than perfectly correlated.

| | Median single ETF | Mean single ETF | Portfolio | Lift |
|---|---|---|---|---|
| Sharpe | {a["median_single_sharpe"]:+.3f} | {a["mean_single_sharpe"]:+.3f} | **{a["sharpe"]:+.3f}** | **{lift:+.3f}** |

Best single names: {best}. Worst: {worst}.

The lift is the part of the crypto result that was never in doubt — averaging
partially-independent books reduces variance whatever they hold. Whether the strategy beats
a passive basket is the separate question the table above answers."""


if __name__ == "__main__":
    raise SystemExit(main())
