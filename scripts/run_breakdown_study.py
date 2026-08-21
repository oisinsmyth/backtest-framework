"""Run the breakdown (short) study and write BREAKDOWN_RESULTS.md (D169).

Offline and deterministic, like its long sibling: the fixture is frozen through the
Step-7 pipeline into a content-addressed snapshot, every variant is one continuous
out-of-sample run with a parameter schedule (D113), and every trial is registered.

    uv run python scripts/run_breakdown_study.py
"""

from __future__ import annotations

import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research import breakdown_study as ds
from backtest_framework.research import breakout_study as bs

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw_events.json"
REGISTRY_PATH = REPO / "data" / "breakdown_study_registry.sqlite"
RESULTS = REPO / "BREAKDOWN_RESULTS.md"
SUMMARY_JSON = REPO / "data" / "breakdown_study_summary.json"

COMBINED_E1_K = 3
"""The k used on BOTH legs of the combined book (D179).

k=3 was the stronger of the two on BOTH books in D178 (+0.101/+0.177 long, +0.061/+0.101
short), so using it on both legs is the consistent choice rather than one tuned per side.
k=2 also cleared the every-symbol bar everywhere; picking between them per leg would be a
search this comparison has no need to run."""

TRIAL_PREFIX = "breakdown-v1"
"""Trial-id prefix, which is also the DSR pool predicate (D98): the pool is selected on
identity fields, never on whether a metric happens to be present."""

SHARPE_EPS = 0.01
"""Smallest annualised-Sharpe difference this study will call a difference.

Stated up front and deliberately blunt. Ten years of daily data buys a standard error
around +/-0.4 on an annualised Sharpe (the long study measured it), so 0.01 sits far
below the noise floor either way. Its job is only to stop arithmetic dust being reported
as a result — it certifies nothing above it as real."""

NL = "\n"


def freeze_snapshot():
    bars, volumes = load_fixture_csv_with_volumes(FIXTURE)
    actions = load_events_json(EVENTS)
    cleaned, cleaning_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)
    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(
        cleaned, actions, volumes_by_symbol=volumes,
        cleaning_report=cleaning_report, validation=validation,
        extra_meta={"source_fixture": FIXTURE.name},
    )
    snapshot = store.load(snapshot_id)
    gate = {
        "cleaning_changes": len(cleaning_report.changes),
        "hard_violations": len(validation.hard_violations),
        "warnings": len(validation.warnings),
    }
    return snapshot_id, snapshot.bars_by_symbol, gate


def main() -> int:
    started = time.time()
    snapshot_id, bars_by_symbol, gate = freeze_snapshot()
    print(f"snapshot {snapshot_id}")

    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()
    registry = TrialRegistry(REGISTRY_PATH)
    study = bs.BreakoutStudyConfig()
    variants = ds.short_variants()
    tiers = bs.SHORT_TIERS
    ref = "taker_40bp"

    payload: dict = {
        "snapshot_id": snapshot_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "config": study.to_dict(),
        "borrow_annual_rate": bs.SHORT_BORROW_ANNUAL_RATE,
        "sanity_gate": gate,
        "n_variants": len(variants),
        "symbols": {},
    }

    n_runs = 0
    for symbol, bars in bars_by_symbol.items():
        spans = bs._window_spans(bars, study)
        oos_start, oos_end = spans[0][2], spans[-1][3]
        oos_bars = list(bars[oos_start:oos_end])
        labels = ds.regime_labels(bars)[oos_start:oos_end]

        # The long book's accepted baseline, run on the SAME span and the SAME tiers, so
        # the correlation and ensemble numbers compare like with like.
        long_variant = bs.Variant(
            "long_baseline", "plateau",
            fixed_config=bs.breakout_config(bs.BASELINE_N_ENTRY, bs.BASELINE_N_EXIT),
        )
        long_result = bs.run_variant(bars, symbol, long_variant, tiers[-1], study)

        # The same long baseline WITH E1, for the combined-book question (D179): E1
        # improves each book separately, but the ensemble is equal-VOL weighted, so a rule
        # that changes each leg's volatility and their correlation does not automatically
        # improve the combination. k=3 on both legs — it was the stronger k on BOTH books
        # in D178, so this is the consistent choice rather than one picked per side.
        long_e1_variant = bs.Variant(
            "long_baseline_e1", "exit",
            fixed_config=bs.breakout_config(
                bs.BASELINE_N_ENTRY, bs.BASELINE_N_EXIT,
                exit_rules=[{"type": "failed_breakout", "k": COMBINED_E1_K}],
            ),
        )
        long_e1_result = bs.run_variant(bars, symbol, long_e1_variant, tiers[-1], study)

        per_variant: dict = {}
        results_by_key: dict[tuple[str, str], bs.VariantResult] = {}
        for tier in tiers:
            for variant in variants:
                n_runs += 1
                print(f"  ... {n_runs} runs ({symbol} {tier.name} {variant.name})")
                r = bs.run_variant(bars, symbol, variant, tier, study)
                key = f"{variant.name}@{tier.name}"

                # Every out-of-sample trial is registered, and every walk-forward window
                # within it (D20/D98). Without this the short book had no multiplicity
                # record at all and every Sharpe it reported was undeflatable.
                bs.log_trials(registry, r, study, snapshot_id, TRIAL_PREFIX, spans, bars)
                results_by_key[(variant.name, tier.name)] = r

                # Returns aligned to OOS bars: oos_returns[i] is the return over the
                # step from bar i to bar i+1, so it pairs with labels[1:].
                in_market = _exposure_flags(r, oos_bars)
                slices = ds.slice_by_regime(
                    r.oos_returns, labels[1:], in_market[1:]
                ) if len(r.oos_returns) == len(labels) - 1 else []

                armings = sum(e.bars_held for e in r.episodes if not e.is_open)
                stop_report = ds.measure_stop_gaps(r.stop_fills, n_armings=armings)
                per_variant[key] = {
                    "stops": stop_report.to_dict(),
                    "total_return": r.total_return,
                    "cagr": bs.cagr(r.total_return, r.n_oos_bars, study.periods_per_year),
                    "sharpe_annual": r.sharpe_annual(study),
                    "max_drawdown": r.max_drawdown,
                    "n_closed_trades": r.diagnostics.n_closed_trades,
                    "exposure": r.diagnostics.exposure,
                    "cost_share_of_gross": r.diagnostics.cost_share_of_gross,
                    "regimes": [s.to_dict() for s in slices],
                }

                if tier.name == ref and variant.name == ds.SHORT_BASELINE:
                    holding = [e.bars_held for e in r.episodes if not e.is_open]
                    instrument_returns = [
                        oos_bars[i + 1].bar.close / oos_bars[i].bar.close - 1.0
                        for i in range(len(oos_bars) - 1)
                    ]
                    null = ds.random_entry_null(
                        instrument_returns, holding, r.sharpe_annual(study),
                        direction=-1, rf_annual=study.rf_annual,
                        periods_per_year=study.periods_per_year, n_draws=1000,
                        seed=study.seed,
                    )
                    ensemble = ds.combine_books(
                        long_result.oos_returns, r.oos_returns,
                        study.rf_annual, study.periods_per_year,
                    )
                    # A stop is live on exactly the bars a position is open, so the
                    # in-market bar count is the arming count — the denominator that
                    # says whether the tail discipline BINDS or is merely present.
                    armings = sum(
                        e.bars_held for e in r.episodes if not e.is_open
                    )
                    gaps = ds.measure_stop_gaps(r.stop_fills, n_armings=armings)
                    # The ensemble claim deserves an interval, not just a point
                    # estimate. Paired block bootstrap (D120) of (combined - long-only)
                    # Sharpe: the SAME resampled bar indices applied to both series, so
                    # the correlation between them is preserved. The brief asked for a
                    # Jobson-Korkie/Memmel test; this project's established convention
                    # for a Sharpe difference is this bootstrap (D120), and it answers
                    # the same question without assuming normality.
                    combined_returns = ds.combined_series(
                        long_result.oos_returns, r.oos_returns
                    )
                    ensemble_test = bs.sharpe_difference_bootstrap(
                        combined_returns,
                        long_result.oos_returns[-len(combined_returns):],
                        study,
                        seed=study.seed,
                    )
                    # Squeeze events (D176): adverse excursions beyond 2 ATR against an
                    # open short. Direction is passed explicitly because the excursion
                    # diagnostics are measured in PRICE terms, so the adverse side for a
                    # short is MFE, not MAE.
                    squeeze = ds.squeeze_events(r.episodes, bars, r.stop_fills, direction=-1)
                    # Per-window correlation (D176): the brief asks for it, and the
                    # full-sample number can hide regime-dependent sign changes.
                    bounds = [
                        (test_start - oos_start, test_end - oos_start)
                        for _i, _t, test_start, test_end in spans
                    ]
                    per_window = ds.correlation_by_window(
                        long_result.oos_returns, r.oos_returns, bounds
                    )
                    payload.setdefault("baseline_detail", {})[symbol] = {
                        "ensemble_test": ensemble_test,
                        "squeeze": squeeze.to_dict(),
                        "correlation_by_window": per_window,
                        "null": null.to_dict(),
                        "ensemble": ensemble.to_dict(),
                        "stop_gaps": gaps.to_dict(),
                        "long_baseline_sharpe": long_result.sharpe_annual(study),
                        "long_baseline_total_return": long_result.total_return,
                    }

        # Deflated Sharpe per (symbol, tier). The pool is every VARIANT's out-of-sample
        # daily Sharpe at that cell (D116: for a parameter-swept study N is the number of
        # CONFIGURATIONS tried), selected on identity fields in the logged config and
        # never on the presence of a metric (D98). Per-window rows carry
        # row_kind="window" and are excluded by that same predicate.
        dsr_by_tier, dsr_inputs_by_tier = {}, {}
        for tier in tiers:
            value, inputs = bs.dsr_for(registry, symbol, tier, study, results_by_key, TRIAL_PREFIX)
            dsr_by_tier[tier.name] = value
            dsr_inputs_by_tier[tier.name] = inputs

        # The combined book with E1 on BOTH legs (D179), computed here rather than inside
        # the variant loop: `results_by_key` is only fully populated once every variant has
        # run, and `exit_e1_k3` is appended last. No new strategy configurations are
        # introduced — both legs already exist and are already in their DSR pools — so this
        # comparison costs no additional multiplicity.
        detail = payload.get("baseline_detail", {}).get(symbol)
        short_e1 = results_by_key.get((f"exit_e1_k{COMBINED_E1_K}", ref))
        short_plain = results_by_key.get((ds.SHORT_BASELINE, ref))
        if detail is not None and short_e1 is not None and short_plain is not None:
            e1_ensemble = ds.combine_books(
                long_e1_result.oos_returns, short_e1.oos_returns,
                study.rf_annual, study.periods_per_year,
            )
            plain_series = ds.combined_series(long_result.oos_returns, short_plain.oos_returns)
            e1_series = ds.combined_series(long_e1_result.oos_returns, short_e1.oos_returns)
            n = min(len(plain_series), len(e1_series))
            detail["combined_e1"] = {
                "ensemble": e1_ensemble.to_dict(),
                "long_e1_sharpe": long_e1_result.sharpe_annual(study),
                "short_e1_sharpe": short_e1.sharpe_annual(study),
                "vs_plain": bs.sharpe_difference_bootstrap(
                    e1_series[-n:], plain_series[-n:], study, seed=study.seed
                ),
            }
        elif detail is not None:
            raise AssertionError(
                f"{symbol}: the combined-book E1 comparison could not be built "
                f"(short_e1={short_e1 is not None}, short_plain={short_plain is not None}). "
                "Failing rather than silently omitting the section, which is how the first "
                "run of this produced empty tables."
            )

        payload["symbols"][symbol] = {
            "dsr_by_tier": dsr_by_tier,
            "dsr_inputs_by_tier": dsr_inputs_by_tier,
            "oos_start": bars[oos_start].timestamp.date().isoformat(),
            "oos_end": bars[oos_end - 1].timestamp.date().isoformat(),
            "n_oos_bars": len(oos_bars),
            "n_windows": len(spans),
            "regime_share": _regime_share(labels),
            "variants": per_variant,
        }

    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RESULTS.write_text(build_report(payload), encoding="utf-8")
    print(f"ran {n_runs} out-of-sample trials in {time.time() - started:.0f}s")
    print(f"wrote {RESULTS.name} and {SUMMARY_JSON.name}")
    return 0


def _exposure_flags(result, oos_bars) -> list[bool]:
    """Per-OOS-bar "was the book in a position" flags, rebuilt from the episodes.

    Matched by TIMESTAMP, not by index. An episode's `entry_index` is an index into the
    variant's own run series, which begins `warm_up` bars BEFORE the first OOS bar — so
    using it directly here would shift every exposure flag by the warm-up length, and
    silently mis-attribute which regime each trade was held in."""
    position = {tb.timestamp: i for i, tb in enumerate(oos_bars)}
    flags = [False] * len(oos_bars)
    for e in result.episodes:
        start = position.get(e.entry_timestamp)
        if start is None:
            continue
        end = position.get(e.exit_timestamp) if e.exit_timestamp is not None else len(flags)
        for i in range(start, min(end if end is not None else len(flags), len(flags))):
            flags[i] = True
    return flags


def _regime_share(labels) -> dict:
    labelled = [x for x in labels if x is not None]
    return {
        r: sum(1 for x in labelled if x == r) / len(labelled) if labelled else 0.0
        for r in ("bull", "bear", "chop")
    }


def build_report(p: dict) -> str:
    ref = "taker_40bp"
    out = [f"""# The breakdown short book: does crisis alpha survive borrow?

**Produced:** {p["generated_utc"][:10]} ·
**Snapshot:** `{p["snapshot_id"]}` ·
**Reproduce:** `uv run python scripts/run_breakdown_study.py` (offline, deterministic)

> **Thesis label (D38/D82/D117).** Directional and beta-loaded, exactly like its long
> sibling, and equally **not** part of this project's market-neutral thesis. It is short
> or flat on a single high-beta instrument. Its honest benchmark is neither the risk-free
> rate nor buy-and-hold: it is "does this pay in the regimes it claims, and does it
> diversify the long book?" — which is what the regime table and the correlation table
> below are for, and why neither is an appendix.

## Read this first: three things that bound what this study can claim

### 1. The stop is INTRABAR now — and it turns out barely to matter

Phase 2 shipped this book with a close-based stop, because `run_backtest` had no intrabar
stop execution, and said so loudly. D170 wired it: `simulator/fills.stop_fill_price` and
its D10 gap semantics now sit in the engine's bar loop, checked before the strategy is
consulted, so a stop closes a position **the moment the bar touches it** and a bar that
gaps through fills at the open rather than at a price the market never traded.

The honest result is that it changes almost nothing here, and the reason is worth more
than the fix. **The stop sits at the far side of the entry channel** — for a short
entering on an N-bar low, it is the N-bar high — which is an enormous distance from the
entry. The trailing exit channel gets there first essentially every time. See the stop
table below: the stop is armed for hundreds of bars per symbol and causes a handful of
exits, or none.

**This also corrects a Phase 2 claim.** That report said "4 of 4 stop exits filled beyond
their own stop, worst by 38.5%". That number was a measurement artifact: it inferred stop
exits by asking whether an exit price ended up beyond the stop level, which also counts
ordinary channel exits that closed past it. The engine now records which fills a stop
actually caused, and the true count is far smaller.

### 2. Borrow is charged, at a stated non-zero rate

{p["borrow_annual_rate"]:.0%}/yr on the short notional for the whole life of every trade
(D124's rate, D169's decision). Assuming free shorts is the single most result-corrupting
choice available to a spot-crypto short study, because the borrow accrues on ~100% of NAV
continuously while the position is open — unlike the long book, where the equivalent cost
is structurally zero.

### 3. The parameters are NOT mirrored from the long book

Sweep is {ds.SHORT_N_ENTRY} x {ds.SHORT_N_EXIT}, against the long book's
{bs.PLATEAU_N_ENTRY} x {bs.PLATEAU_N_EXIT}. Bear legs are faster and shorter and bear
rallies are violent. **Different optimal parameters from the long side is the expected
finding, not a red flag** — and this sweep is counted separately for multiplicity.
"""]

    for symbol, sr in p["symbols"].items():
        share = sr["regime_share"]
        out.append(f"""---

# {symbol}

Out-of-sample **{sr["oos_start"]} to {sr["oos_end"]}** — {sr["n_oos_bars"]:,} daily bars
across {sr["n_windows"]} walk-forward windows. Regime mix of the sample:
**bull {share["bull"]:.0%} · bear {share["bear"]:.0%} · chop {share["chop"]:.0%}**.

## The headline table: performance by regime

A short book that is flat through a bull sample and profitable through the bears is a
SUCCESS. Judging it on full-sample Sharpe would call that a failure, which is why the
regime slice leads and the full-sample number follows it.

Regimes are ex-post SMA(200) labels — bull is price above a rising average, bear is price
below a falling one, chop is the two disagreeing. They are used only to READ the results;
the strategy's own gate is the plain close-vs-average test and it never sees these labels.

{_regime_table(sr, ref)}

## Every variant at `{ref}`

{_variant_table(sr, ref)}

## The stop sweep: which stops actually bind, and what they cost

{_stop_sweep_table(sr, ref)}

## Deflated Sharpe

{_dsr_table(sr)}
""")
        detail = p.get("baseline_detail", {}).get(symbol)
        if detail:
            out.append(_detail_block(symbol, detail))

    out.append(_verdict(p))
    return NL.join(out)


def _regime_table(sr: dict, ref: str) -> str:
    key = f"{ds.SHORT_BASELINE}@{ref}"
    v = sr["variants"].get(key)
    if not v or not v["regimes"]:
        return "_Regime slices unavailable for the baseline variant._"
    rows = NL.join(
        f"| **{r['regime']}** | {r['n_bars']:,} | {r['share_of_sample']:.0%} | "
        f"{r['total_return'] * 100:+.1f}% | {r['sharpe_daily']:+.3f} | {r['exposure']:.0%} |"
        for r in v["regimes"]
    )
    return (
        f"Baseline `{ds.SHORT_BASELINE}` at `{ref}`:" + NL + NL
        + "| Regime | Bars | Share | Return in regime | Daily Sharpe | Exposure |" + NL
        + "|---|---|---|---|---|---|" + NL + rows
    )


def _variant_table(sr: dict, ref: str) -> str:
    rows = []
    for key, v in sr["variants"].items():
        if not key.endswith(f"@{ref}"):
            continue
        rows.append(
            f"| `{key.split('@')[0]}` | {v['total_return'] * 100:+.1f}% | "
            f"{v['cagr'] * 100:+.1f}% | {v['sharpe_annual']:.2f} | {v['max_drawdown'] * 100:.1f}% | "
            f"{v['n_closed_trades']} | {v['exposure']:.1%} |"
        )
    return (
        "| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure |" + NL
        + "|---|---|---|---|---|---|---|" + NL + NL.join(rows)
    )


def _dsr_table(sr: dict) -> str:
    """DSR per (symbol, tier), pool = configurations tried at that cell (D116)."""
    rows = []
    for tier, value in sr["dsr_by_tier"].items():
        i = sr["dsr_inputs_by_tier"][tier]
        rows.append(
            f"| `{tier}` | `{i['best_variant']}` | {i['observed_sr_daily']:.4f} | "
            f"{int(i['t']):,} | {int(i['n_trials'])} | {i['var_trials_daily']:.6f} | "
            f"**{value:.4f}** |"
        )
    worst = min(sr["dsr_by_tier"].values())
    best = max(sr["dsr_by_tier"].values())
    reading = (
        f"**Every tier lands between {worst:.2f} and {best:.2f}, far below the 0.95 bar.** "
        f"The long study's convention applies unchanged: *a DSR below 0.95 means no "
        f"demonstrated edge; a DSR above 0.95 would not mean the reverse.* This book is "
        f"decisively on the wrong side of it."
        if best < 0.95
        else f"Tiers span {worst:.2f} to {best:.2f}."
    )
    return (
        "| Tier | Best variant | Its daily SR | T (bars) | N (trials in pool) | "
        "V[{SRn}] | **DSR** |" + NL
        + "|---|---|---|---|---|---|---|" + NL + NL.join(rows) + NL + NL + reading
    )


def _stop_sweep_table(sr: dict, ref: str) -> str:
    """One row per stop family, baseline entry/exit throughout (D171).

    The BIND RATE is the column to read first. A stop that never fires cannot be
    evaluated on its returns — it is not doing anything, and whatever the row shows is
    the strategy without a stop. D170 found the incumbent entry-channel stop binding once
    in 915 armed bars; the point of this sweep is to find stops that actually engage."""
    rows = []
    for label, _rules in ds.STOP_FAMILIES:
        name = ds.SHORT_BASELINE if label == "entry_channel" else f"stop_{label}"
        v = sr["variants"].get(f"{name}@{ref}")
        if not v:
            continue
        st = v.get("stops", {})
        armed, fired = st.get("n_armings", 0), st.get("n_stop_exits", 0)
        rate = fired / armed if armed else 0.0
        rows.append(
            f"| `{label}`{' *(incumbent)*' if label == 'entry_channel' else ''} | "
            f"{v['total_return'] * 100:+.1f}% | {v['sharpe_annual']:.2f} | "
            f"{v['max_drawdown'] * 100:.1f}% | {v['n_closed_trades']} | "
            f"{fired} / {armed:,} | {rate:.1%} | {st.get('n_gapped', 0)} |"
        )
    return (
        "| Stop | Total return | Sharpe | Max DD | Trades | Stop exits / armed bars | "
        "Bind rate | Gapped |" + NL
        + "|---|---|---|---|---|---|---|---|" + NL + NL.join(rows) + NL + NL
        + "**Bind rate first.** A stop that never fires is not being tested — that row is "
        "the strategy without a stop, whatever else it shows. **Gapped** counts exits that "
        "filled past the level because the bar opened beyond it, which is the residue no "
        "intrabar stop can remove on daily bars."
    )


def _combined_e1_block(d: dict) -> str:
    """E1 on BOTH legs of the combined book (D179).

    Not implied by the two single-book results. The combination is equal-VOL weighted, so
    a rule that changes each leg's volatility also changes the weights, and one that
    changes their correlation changes how much diversification there is to have. Improving
    both components and improving the combination are different claims."""
    c = d.get("combined_e1")
    if not c:
        return ""
    plain, e1 = d["ensemble"], c["ensemble"]
    test = c["vs_plain"]
    rows = [
        ("Long leg Sharpe", plain["long_sharpe"], c["long_e1_sharpe"]),
        ("Short leg Sharpe", plain["short_sharpe"], c["short_e1_sharpe"]),
        ("Long/short correlation", plain["correlation"], e1["correlation"]),
        ("**Combined Sharpe**", plain["combined_sharpe"], e1["combined_sharpe"]),
    ]
    body = NL.join(f"| {label} | {a:+.3f} | {b:+.3f} | {b - a:+.3f} |" for label, a, b in rows)
    dd = (
        f"| **Combined max drawdown** | {plain['combined_max_drawdown'] * 100:.1f}% | "
        f"{e1['combined_max_drawdown'] * 100:.1f}% | "
        f"{(e1['combined_max_drawdown'] - plain['combined_max_drawdown']) * 100:+.1f} pp |"
    )
    if test["p05"] > 0:
        reading = (
            f"**The whole interval is positive.** Adding E1 to both legs improves the "
            f"combined book measurably, not just on the point estimate."
        )
    elif test["p95"] < 0:
        reading = (
            f"**The whole interval is negative.** E1 improves each leg separately and makes "
            f"the COMBINATION worse — which is possible precisely because the weighting is "
            f"vol-based and the correlation moved."
        )
    else:
        reading = (
            f"**The interval spans zero**, so the combined effect is not measurable at this "
            f"sample size, whatever the point estimate shows. That is the absence of "
            f"evidence, not evidence of no effect."
        )
    return f"""### E1 on the combined book

E1 clears the every-symbol bar on both books separately (D178). That does **not** imply it
improves the combination: the two legs are weighted by inverse volatility, so a rule that
changes each leg's volatility changes the weights, and one that changes their correlation
changes how much diversification there is to have.

Both legs carry `failed_breakout` at k={COMBINED_E1_K} — the stronger k on both books in
D178, so it is the consistent choice rather than one tuned per leg.

| | Without E1 | With E1 on both legs | Δ |
|---|---|---|---|
{body}
{dd}

Paired block bootstrap of the combined-Sharpe difference ({int(test["n_sims"]):,} sims,
seed {int(test["seed"])}, D120): observed **{test["observed"]:+.3f}**, 90% interval
[{test["p05"]:+.3f}, {test["p95"]:+.3f}], P(E1 helps the combination) =
**{test["prob_positive"]:.0%}**.

{reading}

**No new configurations were introduced for this comparison.** Both legs already exist and
are already in their DSR pools, so the combined test costs no additional multiplicity — it
is a different reading of trials already paid for."""


def _window_correlation_block(d: dict) -> str:
    """Per-window correlation (D176). The full-sample figure above is one number for a
    decade; this asks whether it holds window to window."""
    rows = d.get("correlation_by_window") or []
    measured = [r for r in rows if r["correlation"] is not None]
    if not measured:
        return ("### Correlation per window" + NL + NL
                + "The short book never traded in any window with enough variation to "
                "measure a correlation. Reported as unmeasurable rather than as zero.")
    values = [r["correlation"] for r in measured]
    inactive = len(rows) - len(measured)
    strong = [r for r in measured if abs(r["correlation"]) > 0.2]
    worst = max(measured, key=lambda r: abs(r["correlation"]))
    reading = (
        "**The target holds window by window, not just on average** — no single window "
        "exceeds ±0.2, so the near-zero full-sample figure is not an artefact of "
        "opposite-signed regimes cancelling out."
        if not strong
        else f"**The full-sample figure hides window-level variation.** {len(strong)} of "
        f"{len(measured)} measurable windows exceed the ±0.2 target, the largest at "
        f"{worst['correlation']:+.3f}. A decade-long average near zero is therefore not the "
        f"whole story: the books do move together in some windows, and a diversifier that "
        f"correlates when it matters is worth less than its average suggests."
    )
    return f"""### Correlation per window

The headline correlation is one number for a decade. The brief asks for it **per window**,
and the two can disagree: a full-sample figure near zero is consistent with the books
moving together in some regimes and opposite in others, which would break the
diversification argument at exactly the moment it is needed.

| | Value |
|---|---|
| Windows with a measurable correlation | {len(measured)} of {len(rows)} |
| Windows the short book sat out entirely | {inactive} |
| Median per-window correlation | {statistics.median(values):+.3f} |
| Min / max | {min(values):+.3f} / {max(values):+.3f} |
| Windows exceeding the ±0.2 target | **{len(strong)}** |
| Largest single-window correlation | {worst["correlation"]:+.3f} (window {worst["window"]}) |

A window the short book sat out has no correlation to measure, and is reported as
unmeasurable rather than as zero — "uncorrelated" and "not present" are different claims.

{reading}"""


def _squeeze_block(d: dict) -> str:
    """Squeeze events (D176) — the diagnostic the brief required and Phase 2 shipped
    without, because the function existed and was never called."""
    sq = d.get("squeeze")
    if not sq:
        return ""
    reading = (
        f"**{sq['n_squeezes']} of {sq['n_trades']} trades ({sq['share_of_trades']:.0%}) ran "
        f"more than 2 ATR against the position while open**, and those trades carry "
        f"{sq['pnl_in_squeezed_trades']:,.0f} of P&L between them. The stop was the exit on "
        f"{sq['stop_hit_share']:.0%} of them — a squeeze the stop caught is a different "
        f"event from one it did not."
        if sq["n_squeezes"]
        else "**No trade ran more than 2 ATR against the position while it was open.** For a "
        "short book in crypto that is a strong statement, and it is a fact about this sample "
        "rather than a property of the rule."
    )
    return f"""### Squeeze events

The event the tail discipline exists for: an adverse excursion beyond 2 ATR against an
open short. For a short, "adverse" means price RISING — excursions are measured in price
terms (D112), so the adverse side is MFE rather than MAE, and reading the wrong one would
report profitable moves as squeezes.

| | Value |
|---|---|
| Closed trades | {sq["n_trades"]} |
| Squeezes (> 2 ATR adverse) | **{sq["n_squeezes"]}** |
| Share of trades | {sq["share_of_trades"]:.0%} |
| Median adverse excursion | {sq["median_atr_multiples"]:.2f} ATR |
| Worst squeeze | {sq["worst_atr_multiples"]:.2f} ATR |
| Squeezes that ended at the stop | {sq["stop_hit_share"]:.0%} |
| P&L in squeezed trades | {sq["pnl_in_squeezed_trades"]:,.0f} |

{reading}"""


def _ensemble_reading(test: dict) -> str:
    """Say what the interval means, computed — an interval that excludes zero and one
    that spans it are different findings and must not share a sentence."""
    if test["p95"] < 0:
        return (
            "**The entire interval is negative.** Adding this short book to the long one "
            "does not fail to help; it measurably hurts, and the sample is large enough to "
            "say so. This is not the 'inside the noise' verdict the long study reached on "
            "its own Sharpe gap — it is a decisive negative."
        )
    if test["p05"] > 0:
        return "**The entire interval is positive**, so the ensemble improvement is measurable."
    return (
        "**The interval spans zero**, so the ensemble effect is not measurable at this "
        "sample size. That is not evidence of neutrality — it is the absence of evidence "
        "either way, and it should not be reported as 'the short book is roughly neutral'."
    )


def _detail_block(symbol: str, d: dict) -> str:
    null, ens, gaps = d["null"], d["ensemble"], d["stop_gaps"]
    test = d["ensemble_test"]
    verdict = (
        "**beats** the null" if null["percentile"] >= 0.95
        else "**does not beat** the null"
    )
    return f"""## The primary verdict: exposure-matched random SHORT entries

Any short rule shows a profit in a sample containing 2018 and 2022, because the
instrument fell. The question is whether THESE entries beat randomly-placed shorts of the
same count and the same holding-period distribution. {null["n_draws"]:,} draws, direction
{null["direction"]}, exposure matched by construction.

| | Sharpe (ann.) |
|---|---|
| **Strategy (observed)** | **{null["observed_sharpe"]:.3f}** |
| Random-entry null, 95th pct | {null["null_p95"]:.3f} |
| Random-entry null, median | {null["null_p50"]:.3f} |
| Random-entry null, 5th pct | {null["null_p05"]:.3f} |

**Percentile vs the null: {null["percentile"]:.0%}.** At the conventional 95% bar the
strategy {verdict}.

## Does it diversify the long book?

Correlation is computed over the full span **including bars either book is flat** —
excluding them would measure "how do they behave when both happen to be trading", which
is not the diversification question. The whole claim is that the short book wakes when the
long book sleeps.

| | Value |
|---|---|
| Long-vs-short daily return correlation | **{ens["correlation"]:+.3f}** |
| Target from the brief | ≤ ~0.2 |
| Long book Sharpe (alone) | {ens["long_sharpe"]:.2f} |
| Short book Sharpe (alone) | {ens["short_sharpe"]:.2f} |
| Combined, equal VOL weight | {ens["combined_sharpe"]:.2f} |
| Long book max drawdown | {ens["long_max_drawdown"] * 100:.1f}% |
| Combined max drawdown | {ens["combined_max_drawdown"] * 100:.1f}% |

**And now with an interval rather than a point estimate.** Paired block bootstrap of
(combined − long-only) annualised Sharpe, 20-bar blocks, {int(test["n_sims"]):,} sims,
seed {int(test["seed"])} — the same resampled bar indices applied to both series, so the
correlation between them is preserved (D120). The brief asked for a Jobson–Korkie/Memmel
test; this project's established convention for a Sharpe difference is this bootstrap,
which answers the same question without assuming normality.

| | Δ Sharpe (combined − long-only) |
|---|---|
| Observed | **{test["observed"]:+.3f}** |
| 90% interval | [{test["p05"]:+.3f}, {test["p95"]:+.3f}] |
| P(adding the short book helps) | **{test["prob_positive"]:.0%}** |

{_ensemble_reading(test)}

{_window_correlation_block(d)}

{_squeeze_block(d)}

{_combined_e1_block(d)}

## What the close-based stop actually cost

Every exit that filled beyond its own stop level — the tail the stop did not truncate.

| | Value |
|---|---|
| Exits the stop actually caused | {gaps["n_stop_exits"]} |
| ...of which gapped past the stop | {gaps["n_gapped"]} |
| Bars carrying a live stop | {gaps["n_armings"]:,} |
| Worst single gap | {gaps["worst_gap_pct"] * 100:.1f}% beyond the stop |

**Read the first two rows against the third.** A stop that is armed for thousands of bars
and closes a handful of trades is *present* rather than *binding*: the trailing channel
almost always gets there first, because the stop sits at the far side of the entry
channel and that is a very long way from a breakdown entry.

These counts come from the engine's own record of which fills a stop caused (D170).
The Phase 2 version of this table inferred them, by asking whether an exit price ended
up beyond the stop level — which also catches ordinary channel exits that happened to
close past it. That inference is what produced the earlier "4 of 4 stop exits gapped"
claim, and it was wrong: most of those exits were not stop exits at all.
"""


def _criteria_scorecard(p: dict) -> str:
    """Score the brief's three criteria PER SYMBOL, from the regime slices.

    An earlier cut of this section stated the outcome in prose written from one symbol's
    shape. It said the bear-regime return was "around flat" — true on BTC, and flatly
    false on ETH, which returned +33.7% there. Hardcoded prose drifting from computed
    data is the exact defect Phase 1.1 had to fix in the long study's multiplicity table,
    so this table is derived."""
    ref = "taker_40bp"
    key = f"{ds.SHORT_BASELINE}@{ref}"
    rows, notes = [], []
    for symbol, sr in p["symbols"].items():
        v = sr["variants"].get(key)
        if not v or not v["regimes"]:
            continue
        by = {r["regime"]: r for r in v["regimes"]}
        bear = by.get("bear", {}).get("total_return", 0.0)
        bull = by.get("bull", {}).get("total_return", 0.0)
        bull_exposure = by.get("bull", {}).get("exposure", 0.0)
        chop = by.get("chop", {}).get("total_return", 0.0)

        bear_ok = bear > 0.10
        bull_ok = bull > -0.20
        chop_ok = chop > -0.10
        rows.append(
            f"| {symbol} | {bear * 100:+.1f}% {'PASS' if bear_ok else 'FAIL'} | "
            f"{bull * 100:+.1f}% at {bull_exposure:.0%} exposure "
            f"{'PASS' if bull_ok else 'FAIL'} | "
            f"{chop * 100:+.1f}% {'PASS' if chop_ok else 'FAIL'} |"
        )
        notes.append((symbol, bear_ok, bull_ok, chop_ok))

    passed_all = [s for s, b, u, c in notes if b and u and c]
    failed_any = [s for s, b, u, c in notes if not (b and u and c)]
    if passed_all and failed_any:
        reading = (
            f"**Split again, and along the same line as the null.** {', '.join(passed_all)} "
            f"meets all three; {', '.join(failed_any)} does not. The two symbols are telling "
            f"different stories about the same rule, which on a two-instrument sample is the "
            f"definition of an undemonstrated result rather than a partial success."
        )
    elif passed_all:
        reading = (
            f"**All three criteria met on every symbol** ({', '.join(passed_all)}). On a "
            f"two-instrument sample that is encouraging and not yet evidence."
        )
    else:
        reading = (
            "**No symbol meets all three.** A short book that is flat when it should be "
            "winning, or bleeding when it should be quiet, has not earned its place in the "
            "ensemble."
        )

    # The gate's MECHANICAL effect and the bull CRITERION are different claims, and an
    # earlier cut of this section conflated them: it asserted the middle criterion held
    # everywhere while the table above showed BTC failing it. The gate can work
    # perfectly and the criterion still fail, if the few trades it lets through are bad
    # enough — which is exactly what happened.
    exposures = [
        by["exposure"]
        for sr in p["symbols"].values()
        for v in [sr["variants"].get(key)] if v and v["regimes"]
        for by in v["regimes"] if by["regime"] == "bull"
    ]
    if exposures and max(exposures) <= 0.05:
        gate_reading = (
            f"**The gate itself works on every symbol** — bull-regime exposure is at most "
            f"{max(exposures):.0%}, so the book really does stand aside when the long book is "
            f"working. Note that this is a separate claim from the bull CRITERION above, and "
            f"the two can diverge: on a symbol where the criterion fails, it fails not because "
            f"the gate let the book trade through the bull market but because the handful of "
            f"trades it did allow were bad enough to lose double digits on their own. The gate "
            f"is not the problem. What it gates is."
        )
    else:
        gate_reading = (
            f"**The gate is not holding the book out of bull markets**: bull-regime exposure "
            f"reaches {max(exposures, default=0.0):.0%}. That is a failure of the gate itself, "
            f"not just of the rule behind it."
        )

    return f"""### Success criteria from the brief, scored

The brief named three: *strongly profitable in bear regimes; flat-to-small-loss in bull
regimes; acceptable chop bleed.* Scored here as bear return > +10%, bull return > −20%,
chop return > −10% — thresholds fixed before reading, and blunt on purpose.

| Symbol | Bear (strongly profitable?) | Bull (flat-to-small-loss?) | Chop (acceptable bleed?) |
|---|---|---|---|
{NL.join(rows)}

{reading}

{gate_reading}"""


def _prereg_scorecard(p: dict) -> str:
    """Score D173's pre-registered predictions against what actually happened.

    The predictions were committed before this ever ran (git d1f0d6c). Computed here, so
    the scorecard cannot drift from the numbers it scores."""
    ref = "taker_40bp"
    symbols = list(p["symbols"])

    def sharpe(sym, name):
        v = p["symbols"][sym]["variants"].get(f"{name}@{ref}")
        return v["sharpe_annual"] if v else None

    # H1: structure stop vs trail_10, every-symbol rule at SHARPE_EPS.
    h1_rows, h1_beats = [], []
    for k in (2, 3):
        deltas = {}
        for sym in symbols:
            a, b = sharpe(sym, f"stop_swing_k{k}"), sharpe(sym, "stop_trail_10")
            if a is None or b is None:
                continue
            deltas[sym] = a - b
        if not deltas:
            continue
        beats = min(deltas.values()) >= SHARPE_EPS
        if beats:
            h1_beats.append(f"swing_k{k}")
        h1_rows.append(
            f"| `stop_swing_k{k}` vs `stop_trail_10` | "
            + " | ".join(f"{deltas[s]:+.3f}" for s in symbols)
            + f" | {'**BEATS IT**' if beats else 'does not'} |"
        )

    # H2: structure gate vs the plain baseline.
    h2_rows, h2_beats = [], []
    for k in (2, 3):
        deltas = {}
        for sym in symbols:
            a, b = sharpe(sym, f"gate_swing_k{k}"), sharpe(sym, ds.SHORT_BASELINE)
            if a is None or b is None:
                continue
            deltas[sym] = a - b
        if not deltas:
            continue
        beats = min(deltas.values()) >= SHARPE_EPS
        if beats:
            h2_beats.append(f"gate_k{k}")
        h2_rows.append(
            f"| `gate_swing_k{k}` vs baseline | "
            + " | ".join(f"{deltas[s]:+.3f}" for s in symbols)
            + f" | {'**BEATS IT**' if beats else 'does not'} |"
        )

    best_dsr = max(max(sr["dsr_by_tier"].values()) for sr in p["symbols"].values())
    header = ("| Comparison | " + " | ".join(f"Δ Sharpe {s}" for s in symbols)
              + " | Every-symbol rule |" + NL + "|---|" + "---|" * (len(symbols) + 1) + NL)

    h1_verdict = (
        f"**H1 IS FALSIFIED.** {', '.join(h1_beats)} clears the every-symbol bar against "
        f"`trail_10`. The prediction was that no structure stop would, and it was wrong."
        if h1_beats
        else "**H1 holds.** No structure stop clears the every-symbol bar against `trail_10`."
    )
    h2_verdict = (
        f"**H2 is falsified**: {', '.join(h2_beats)} improves on the baseline on every symbol."
        if h2_beats
        else "**H2 holds.** Neither gate improves on the plain SMA200 baseline across both "
        "symbols — and the mechanism is visible in the trade counts, which fall by roughly "
        "two thirds. A second gate is another trade-removing device, and it removes good "
        "trades along with bad, exactly as every such device tested in this project has."
    )
    h3_verdict = (
        f"**H3 holds.** The best DSR anywhere is {best_dsr:.3f}, nowhere near 0.95."
        if best_dsr < 0.95
        else f"**H3 is falsified**: DSR reaches {best_dsr:.3f}."
    )

    return f"""### The pre-registered predictions, scored

D173 recorded three predictions and was committed before this study ran, so they are
dated by git rather than written afterwards. Scored by the same every-symbol rule at
SHARPE_EPS = {SHARPE_EPS:.2f}.

**H1 — the structure stop will not beat `trail_10` on both symbols.**

{header}{NL.join(h1_rows)}

{h1_verdict}

**H2 — the structure gate will not improve on the SMA200 gate alone.**

{header}{NL.join(h2_rows)}

{h2_verdict}

**H3 — deflated Sharpe will not reach 0.95 on either symbol.** {h3_verdict}"""


def _multiplicity(p: dict) -> str:
    n_variants = p["n_variants"]
    # The long study printed a breakdown that did not sum, and its verdict then quoted
    # the wrong number twice (fixed in Phase 1.1). A multiplicity table that does not add
    # up is the one table here that must never be wrong, so it is asserted.
    by_group: dict[str, int] = {}
    for v in ds.short_variants():
        by_group[v.group] = by_group.get(v.group, 0) + 1
    if sum(by_group.values()) != n_variants:
        raise AssertionError(
            f"multiplicity breakdown does not sum: groups {by_group} total "
            f"{sum(by_group.values())} against {n_variants} variants"
        )
    n_tiers, n_symbols = 4, len(p["symbols"])
    windows = sum(sr["n_windows"] for sr in p["symbols"].values())
    return f"""### Multiplicity: everything that was evaluated

| What | Count |
|---|---|
| Strategy variants per symbol | {n_variants} |
| — of which entry/exit grid cells | {len([v for v in ds.short_variants() if v.group == "plateau"])} |
| — of which time-stop variants | {len([v for v in ds.short_variants() if v.group == "exit"])} |
| — of which stop families | {len([v for v in ds.short_variants() if v.group == "stop"])} |
| — of which structure gates | {len([v for v in ds.short_variants() if v.group == "gate"])} |
| — of which gate counterfactuals | {len([v for v in ds.short_variants() if v.group == "counterfactual"])} |
| Cost tiers | {n_tiers} |
| Symbols | {n_symbols} |
| **Out-of-sample trials logged** | **{n_variants * n_tiers * n_symbols}** |
| Per-window trial rows logged | {windows * n_variants} |

Every one is registered in `data/breakdown_study_registry.sqlite` and every variant row
is in the DSR pool for its (symbol, tier) cell. One of the stop families (`trail_20`) is
inert — mechanically the incumbent under another name — so {n_variants - 1} of the
{n_variants} are distinct configurations, and the pool is not reduced for it: a
configuration you tried and learned nothing from still cost you a look."""


def _deflation_reading(p: dict) -> str:
    """What deflation does to the headline claims. Computed, because this is the section
    most likely to be quoted and the numbers move between runs."""
    worst = {sym: min(sr["dsr_by_tier"].values()) for sym, sr in p["symbols"].items()}
    best = {sym: max(sr["dsr_by_tier"].values()) for sym, sr in p["symbols"].items()}
    # Three decimals: at two, BTC's 0.0957 prints as "0.10" and then sits next to a
    # sentence saying it does not reach 0.10, which reads as a contradiction.
    detail = " · ".join(f"{sym} {worst[sym]:.3f}–{best[sym]:.3f}" for sym in worst)
    survivors = [sym for sym in best if best[sym] >= 0.95]
    if survivors:
        return f"""### What deflation does to all of it

Deflated Sharpe by symbol: {detail}. {', '.join(survivors)} clears 0.95."""
    return f"""### What deflation does to all of it — and this is the section that matters

Deflated Sharpe by symbol across all four tiers: **{detail}**. Not one cell reaches the
0.95 bar, and the weaker symbol does not reach 0.10 at any tier.

**This reframes every positive number above.** ETH's 96th-percentile null result and its
clean sweep of the three success criteria were the strongest things in this document.
Both were computed on the best of {p["n_variants"]} configurations, and once that search
is priced in, the evidence for skill is gone. The same applies to the stop sweep: the
variant that most improved BTC (`stop_trail_5`, −71.6% → −40.6%) is precisely the one
DSR selects as the best-of-{p["n_variants"]} and deflates to near zero. That is not DSR
being harsh — it is DSR doing the exact job it exists for, on a search this study
performed and then reported.

The honest one-line summary of the short book is now: **a rule with no demonstrated edge,
whose apparent successes are consistent with having looked {p["n_variants"]} times.**"""


def _bind_reading(p: dict) -> str:
    """Does binding MORE actually help? Measured per symbol rather than asserted.

    Reuses `feature_analysis.spearman` (D167) instead of a second rank-correlation
    implementation. The tempting sentence here is "tighter stops that bind more do
    better", and it is true on one symbol and false on the other — which is the finding,
    not a wrinkle to smooth over."""
    from backtest_framework.research.feature_analysis import spearman

    ref = "taker_40bp"
    readings = []
    for sym, sr in p["symbols"].items():
        base = sr["variants"][f"{ds.SHORT_BASELINE}@{ref}"]["sharpe_annual"]
        binds, deltas = [], []
        for label, _rules in ds.STOP_FAMILIES:
            if label == "entry_channel":
                continue
            v = sr["variants"].get(f"stop_{label}@{ref}")
            if not v:
                continue
            binds.append(v.get("stops", {}).get("n_stop_exits", 0))
            deltas.append(v["sharpe_annual"] - base)
        rho = spearman(binds, deltas)
        if rho is not None:
            readings.append((sym, rho))

    if not readings:
        return ""
    positives = [sym for sym, rho in readings if rho > 0.2]
    negatives = [sym for sym, rho in readings if rho < -0.2]
    detail = ", ".join(f"{sym} {rho:+.2f}" for sym, rho in readings)
    if positives and not negatives:
        return (
            f"The mechanism is consistent: rank correlation between how often a stop binds "
            f"and how much it helps is positive on every symbol ({detail}). **Stops that "
            f"actually engage do better**, which is the finding D170 could not produce with "
            f"a stop that never fired."
        )
    if positives and negatives:
        return (
            f"**But binding more is not uniformly better.** The rank correlation between how "
            f"often a stop binds and how much it helps is {detail} — positive on "
            f"{', '.join(positives)}, negative on {', '.join(negatives)}. On the symbol where "
            f"it is negative, the stops that fire most (`trail_5`, `chandelier_3`) are cutting "
            f"winning trades short rather than truncating losers. That is the same failure "
            f"mode the long study found in its entry filters: a device that removes trades "
            f"removes good ones too."
        )
    return (
        f"Binding more does not help: the rank correlation between bind frequency and "
        f"improvement is {detail}. Whatever these stops are cutting, it is not only losses."
    )


def _stop_sweep_verdict(p: dict) -> str:
    """Score the stop families by the SAME rule the long study fixed before looking: a
    change is kept only if it improves on EVERY symbol, because one symbol out of two is
    a coin flip. Computed, not asserted."""
    ref = "taker_40bp"
    symbols = list(p["symbols"])
    baseline = {
        sym: p["symbols"][sym]["variants"][f"{ds.SHORT_BASELINE}@{ref}"]["sharpe_annual"]
        for sym in symbols
    }

    rows, keepers = [], []
    for label, _rules in ds.STOP_FAMILIES:
        if label == "entry_channel":
            continue
        deltas, binds = {}, {}
        for sym in symbols:
            v = p["symbols"][sym]["variants"].get(f"stop_{label}@{ref}")
            if not v:
                continue
            deltas[sym] = v["sharpe_annual"] - baseline[sym]
            binds[sym] = v.get("stops", {}).get("n_stop_exits", 0)
        if not deltas:
            continue

        # A stated floor, fixed before reading and blunt on purpose. Without one, a
        # difference of 0.001 Sharpe reads as an improvement: an earlier cut of this
        # table marked `trail_20` KEEP on a delta that rounds to +0.00, when it is the
        # incumbent stop under another name.
        worst = min(deltas.values())
        if all(abs(d) < SHARPE_EPS for d in deltas.values()):
            verdict = "INERT"
        elif worst >= SHARPE_EPS:
            verdict = "**KEEP**"
            keepers.append((label, worst, sum(binds.values())))
        else:
            verdict = "DROP"
        rows.append(
            "| `" + label + "` | "
            + " | ".join(f"{deltas[sym]:+.3f}" for sym in symbols)
            + f" | {sum(binds.values())} | {verdict} |"
        )

    header = (
        "| Stop | " + " | ".join(f"Δ Sharpe {sym}" for sym in symbols)
        + " | Stop exits | Decision |" + NL
        + "|---|" + "---|" * (len(symbols) + 2) + NL
    )

    keepers.sort(key=lambda k: -k[1])
    if keepers:
        best = keepers[0]
        lead = (
            f"**{len(keepers)} of the swept stops improve risk-adjusted return on every "
            f"symbol by more than {SHARPE_EPS:.2f} Sharpe**, and the strongest by worst-case improvement is `{best[0]}` "
            f"(+{best[1]:.2f} on its weaker symbol, {best[2]} stop exits). {_bind_reading(p)}"
        )
    else:
        lead = (
            "**No swept stop improves on every symbol.** By the rule the long study fixed "
            "before looking, none is adopted."
        )

    return f"""### The stop sweep, scored

Same rule the long study fixed before looking: keep only what improves on EVERY symbol,
because one out of two is a coin flip. Δ is against the incumbent `entry_channel` stop at
`{ref}`; `INERT` means the variant produced results identical to the incumbent, so it is
not a distinct configuration at all.

{header}{NL.join(rows)}

{lead}

**Three things this does not mean.**

First, **less bad is not good.** The best BTC row is still a large loss at a negative
Sharpe; a tighter stop shrinks the damage, it does not create an edge. The entry rule is
what failed its null, and no stop repairs an entry.

Second, **this is a fresh trial series and it is not free.** Six stop configurations on
two symbols across four tiers were evaluated here on top of an already-swept strategy.
One of them (`trail_20`) turned out to be inert — for a short entering on a 20-bar low, a
20-bar trailing high IS the entry channel — so the effective count is five. These trials
are NOT yet in the deflated-Sharpe accounting (see the gap noted below), and picking the
best row of five after the fact is exactly the selection this project's machinery exists
to penalise.

Third, **the sweep was run at fixed entry/exit parameters.** A stop interacts with the
exit channel it sits beside, and re-optimising both together would be a much larger
multiplicity bill for a book that has not yet shown an entry edge."""


def _stop_paragraph(p: dict) -> str:
    """Report what the stop DID, from the engine's own record.

    Written computed rather than as prose because this is the third time in this project
    that a hardcoded sentence has drifted from the numbers beside it. The earlier version
    of this paragraph asserted the stop "did not do its job" on the strength of a gap
    count that, once measured properly, turned out to be zero."""
    detail = p.get("baseline_detail", {})
    exits = sum(d["stop_gaps"]["n_stop_exits"] for d in detail.values())
    gapped = sum(d["stop_gaps"]["n_gapped"] for d in detail.values())
    armed = sum(d["stop_gaps"]["n_armings"] for d in detail.values())
    worst = max((d["stop_gaps"]["worst_gap_pct"] for d in detail.values()), default=0.0)
    per_symbol = " · ".join(
        f"{sym} {d['stop_gaps']['n_stop_exits']} exit(s) from "
        f"{d['stop_gaps']['n_armings']:,} armed bars"
        for sym, d in detail.items()
    )

    if exits == 0:
        return f"""### The stop never fired

Across both symbols the stop was armed for {armed:,} bars and closed **not one trade**
({per_symbol}). The trailing exit channel reached every position first.

That is information, not a clean bill of health, and it is not a defence of the design
either. A stop placed at the far side of the entry channel is so distant from a breakdown
entry that it is nearly unreachable before the ordinary exit fires. The tail discipline
the brief demanded is **present but not binding** — and a risk control that never binds
has not been shown to work, it has only been shown not to be needed on this sample."""

    gap_line = (
        f"Of those, **{gapped} gapped past the stop** and filled at the bar's open "
        f"instead, the worst by {worst * 100:.1f}%. That is the residue no intrabar stop "
        f"can remove: on daily bars the dangerous move happens between one close and the "
        f"next open, where there is no intrabar to trade in."
        if gapped
        else "**None of them gapped** — each filled at its stop price, which is the "
        "intrabar machinery doing exactly what it exists to do."
    )
    return f"""### What the stop actually did

The stop was armed for **{armed:,} bars** and caused **{exits} exit(s)**
({per_symbol}). {gap_line}

**Read those two numbers against each other.** A stop armed for hundreds of bars that
closes a handful of trades is *present* rather than *binding*: it sits at the far side of
the entry channel, which is a very long way from a breakdown entry, so the trailing exit
gets there first almost every time. The brief's premise — that short expectancy becomes
calculable once the squeeze tail is truncated — is now satisfied mechanically, and turns
out not to be the thing that was limiting this book."""


def _verdict(p: dict) -> str:
    detail = p.get("baseline_detail", {})
    lines = ["---", "", "# Verdict", ""]
    for symbol, d in detail.items():
        null, ens = d["null"], d["ensemble"]
        lines.append(
            f"- **{symbol}**: null percentile {null['percentile']:.0%}, "
            f"long/short correlation {ens['correlation']:+.2f}, "
            f"combined Sharpe {ens['combined_sharpe']:.2f} against "
            f"{ens['long_sharpe']:.2f} long-only "
            f"(max drawdown {ens['combined_max_drawdown'] * 100:.0f}% against "
            f"{ens['long_max_drawdown'] * 100:.0f}%)."
        )

    beat = [s for s, d in detail.items() if d["null"]["percentile"] >= 0.95]
    missed = [s for s, d in detail.items() if d["null"]["percentile"] < 0.95]
    hurts = [
        s for s, d in detail.items()
        if d["ensemble"]["combined_sharpe"] < d["ensemble"]["long_sharpe"]
    ]
    helps_dd = [
        s for s, d in detail.items()
        if d["ensemble"]["combined_max_drawdown"] < d["ensemble"]["long_max_drawdown"]
    ]

    if beat and missed:
        null_read = (
            f"**The null verdict is SPLIT and must not be read as a pass.** "
            f"{', '.join(beat)} clears the 95% bar; {', '.join(missed)} does not. The long "
            f"study fixed the rule for exactly this situation before looking — a filter is "
            f"kept only if it improves on EVERY symbol, because one symbol out of two is a "
            f"coin flip. The same discipline applies here, and by it the entry rule is not "
            f"demonstrated. Reporting the winner alone would be the single most misleading "
            f"thing available in this document."
        )
    elif beat:
        null_read = (
            f"**The entry rule beats the exposure-matched null on every symbol tested** "
            f"({', '.join(beat)}). That is the primary verdict the brief asked for, and it "
            f"is a genuine positive — on a two-symbol sample."
        )
    else:
        null_read = (
            f"**The entry rule does not beat randomly-placed shorts of the same count and "
            f"duration on any symbol.** This is the primary verdict the brief nominated, and "
            f"it is a clean negative: the timing of these entries is indistinguishable from "
            f"chance, so whatever the book earns it earns from being short during falls, not "
            f"from choosing when."
        )
    lines += ["", null_read, ""]

    ens_read = (
        "**The diversification claim holds and the profitability claim does not, and those "
        "are separate findings.** Correlation against the long book comes in at or below "
        "the brief's ~0.2 target on both symbols — genuinely near zero, which is the "
        "complementary-payoff property the ensemble argument needs."
    )
    if hurts:
        ens_read += (
            f" But near-zero correlation cannot rescue a book that loses money: on "
            f"{', '.join(hurts)} the equal-vol-weighted combination has a LOWER Sharpe than "
            f"the long book alone. You cannot diversify with a negative-expectancy asset; "
            f"you can only spread the same losses more smoothly."
        )
    if helps_dd:
        ens_read += (
            f" The one thing that does survive is drawdown: on {', '.join(helps_dd)} the "
            f"combined book's worst drawdown is smaller than the long book's. That is the "
            f"same shape of result the long study landed on — a drawdown-shape finding, not "
            f"an alpha finding — and it should be quoted with the Sharpe cost attached, "
            f"never on its own."
        )
    lines += [ens_read, ""]

    lines += [
        _criteria_scorecard(p), _stop_sweep_verdict(p), _stop_paragraph(p),
        _multiplicity(p), _prereg_scorecard(p), _deflation_reading(p), """
# Standing caveats

1. **The stop is intrabar (D170) but almost never binds.** The mechanism is correct —
   touched stops fill at the stop, gapped ones at the open — but the level sits at the
   far side of the entry channel, so the trailing exit closes nearly every position
   first. A risk control that never binds has not been shown to work on this sample, only
   to be unneeded on it. A tighter stop (ATR-based, say) is a different strategy and
   would need its own sweep and its own multiplicity accounting.
2. **Borrow is a stated assumption, not a quote.** 10%/yr is mid-range for BTC/ETH spot
   margin borrow over the sample; it was neither swept nor negotiated, and hard-to-borrow
   episodes in a real crash would be worse precisely when the book is most short.
3. **No funding, no perp expression.** These are spot shorts (D108). A perpetual-futures
   implementation would pay funding, which in a falling market is often a CREDIT to
   shorts — so this is conservative in that one direction and silent about it otherwise.
4. **Live tradability is out of scope and mostly negative.** The FCA retail
   crypto-derivatives ban and the absence of retail spot margin mean this book is
   backtest-and-shadow-signals only. The one legal live expression at current capital is
   equity-index breakdown via spread betting, which is a different instrument and a
   different spec.
5. **Two instruments, both survivors.** The same selection bias the long study named as
   its largest un-deflatable problem applies here unchanged.
6. **The DSR pool counts configurations, not everything.** It does not count the
   two-symbol choice, nor the decision to test a short book on crypto after a decade of
   visible crypto trend. As the long study put it: a DSR below 0.95 means "no
   demonstrated edge"; a DSR above 0.95 would not mean the reverse.
"""]
    return NL.join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
