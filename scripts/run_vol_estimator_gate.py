"""D195 step 1: does 15m realized volatility forecast better than the incumbent?

Pre-registered in `docs/decisions/D195-the-volatility-estimator-gate.md`, committed at
c27e671 BEFORE this script existed. The bar, the two-target design and step 2's Sharpe
floor are fixed there and nothing here may relax them.

No strategy, no costs, no trading. A forecasting comparison and nothing else.

Both estimators are computed from the SAME 15m fixture, with the daily series resampled
from it, so provider, span and calendar are identical and the estimator is the only
variable. Using the yfinance daily fixture for the incumbent would have put provider back
into a comparison whose entire content is like-for-like.

Run: uv run python scripts/run_vol_estimator_gate.py
Re-render the results doc from the committed JSON, offline: --report-only
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.research.vol_estimators import (  # noqa: E402
    fold_to_days,
    forecast_pairs,
    score,
)

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY_JSON = REPO / "data" / "vol_estimator_gate_summary.json"
RESULTS = REPO / "docs" / "results" / "vol_estimator_gate.md"

WINDOW = 20
"""Calendar days, matching `InverseVolatilityWeight.vol_window = 20` exactly."""

BARS_PER_DAY = 96
MIN_BARS_PER_DAY = 96
"""A full UTC day. A partial day's realized variance is a sum over fewer terms and is
biased low, which would read as a quiet day rather than as missing data. D193's fetch
already dropped short days, so this should exclude nothing — asserted, not assumed."""

GATE_SYMBOLS = ("BTCUSDT", "ETHUSDT")
SECONDARY_SYMBOLS = ("XEMUSDT", "BTGUSDT")

LOSS_REDUCTION_FLOOR = 0.30
"""D195's bar: the candidate must cut forecast loss by at least 30% on both symbols, both
targets and both losses. Labelled in D195 as a judgement call, grounded in the order the
realized-variance literature reports for intraday against daily-close estimators."""


def run_symbol(symbol: str, bars) -> dict[str, Any]:
    series = fold_to_days(bars, MIN_BARS_PER_DAY)
    short_days = len(set(tb.timestamp.date() for tb in bars)) - len(series)
    pairs = forecast_pairs(series, WINDOW)
    result = score(pairs)
    result["days"] = len(series)
    result["short_days_dropped"] = short_days
    result["first_day"] = series.days[0].isoformat()
    result["last_day"] = series.days[-1].isoformat()
    return result


def passes(result: dict[str, Any]) -> dict[str, Any]:
    """Every (target, loss) cell must clear the floor. Reported per cell, never averaged —
    an average would let a win on the shared-basis target carry a loss on the other."""
    cells = {}
    for target in ("realized", "close_to_close"):
        for loss in ("mse_log", "qlike"):
            cells[f"{target}/{loss}"] = result[target][loss]["reduction"]
    return {
        "cells": cells,
        "min_reduction": min(cells.values()),
        "passed": all(v >= LOSS_REDUCTION_FLOOR for v in cells.values()),
    }


def build_payload(results: dict[str, Any], elapsed: float) -> dict[str, Any]:
    verdicts = {s: passes(r) for s, r in results.items()}
    gate = [s for s in GATE_SYMBOLS if s in verdicts]
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": "D195-the-volatility-estimator-gate.md (commit c27e671)",
        "fixture": FIXTURE.name,
        "window_days": WINDOW,
        "bars_per_day": BARS_PER_DAY,
        "loss_reduction_floor": LOSS_REDUCTION_FLOOR,
        "gate_symbols": list(GATE_SYMBOLS),
        "secondary_symbols": list(SECONDARY_SYMBOLS),
        "results": results,
        "verdicts": verdicts,
        "gate_passed": bool(gate) and len(gate) == len(GATE_SYMBOLS)
        and all(verdicts[s]["passed"] for s in gate),
        "elapsed_seconds": elapsed,
    }


def build_report(p: dict[str, Any]) -> str:
    out: list[str] = []
    w = out.append
    w("# Does finer data give a better estimate? The volatility gate")
    w("")
    w(f"D195 step 1, pre-registered in `{p['preregistration']}` before this run existed. "
      f"A forecasting comparison: no strategy, no costs, no trading.")
    w("")
    w(f"**The question.** `InverseVolatilityWeight` sizes every position off "
      f"{p['window_days']} close-to-close daily returns. The same {p['window_days']} "
      f"calendar days at 15m hold {p['window_days'] * p['bars_per_day']:,} observations. "
      f"Does the finer estimator forecast the next {p['window_days']} days better?")
    w("")
    w("Both estimators come from the same 15m fixture with the daily series resampled "
      "from it, so provider, span and calendar are identical and the estimator is the only "
      "variable.")
    w("")
    w("**Two targets are scored, and that is the point of the design.** The accurate "
      "target is realized vol from 15m — but the candidate is built the same way, so any "
      "systematic component in 15m realized variance is inherited by both and flatters it. "
      "The incumbent's own basis is scored as a second target. The candidate must win on "
      "both; a win only on the shared-basis target is an artifact, not a result.")
    w("")

    w(f"## The bar: {p['loss_reduction_floor']:.0%} loss reduction, every cell")
    w("")
    w("| symbol | pairs | realized/MSE | realized/QLIKE | c2c/MSE | c2c/QLIKE | worst | verdict |")
    w("|---|---:|---:|---:|---:|---:|---:|---|")
    for symbol, v in p["verdicts"].items():
        c = v["cells"]
        w(f"| `{symbol}` | {p['results'][symbol]['n_pairs']:,} | "
          f"{c['realized/mse_log']:+.1%} | {c['realized/qlike']:+.1%} | "
          f"{c['close_to_close/mse_log']:+.1%} | {c['close_to_close/qlike']:+.1%} | "
          f"**{v['min_reduction']:+.1%}** | "
          f"{'**PASS**' if v['passed'] else 'FAIL'} |")
    w("")
    w(f"**Gate ({', '.join(p['gate_symbols'])}): "
      f"{'PASS' if p['gate_passed'] else 'FAIL'}.** A positive reduction means the "
      f"candidate's loss is lower.")
    w("")

    w("## The losses in full")
    w("")
    for symbol, r in p["results"].items():
        w(f"### `{symbol}` — {r['days']:,} days, {r['first_day']} to {r['last_day']}, "
          f"{r['n_pairs']:,} forecast pairs")
        w("")
        w("| target | loss | incumbent | candidate | reduction |")
        w("|---|---|---:|---:|---:|")
        for target in ("realized", "close_to_close"):
            for loss in ("mse_log", "qlike"):
                cell = r[target][loss]
                w(f"| {target} | {loss} | {cell['incumbent']:.5f} | "
                  f"{cell['candidate']:.5f} | {cell['reduction']:+.1%} |")
        for target in ("realized", "close_to_close"):
            w(f"| {target} | R² | {r[target]['r2']['incumbent']:.4f} | "
              f"{r[target]['r2']['candidate']:.4f} | — |")
        w("")

    w("## What a pass does not mean")
    w("")
    w("It means the incumbent sizing input is measurably worse than an available "
      "alternative. It does **not** mean the book improves — that is D195 step 2, and its "
      "bar of +0.10 Sharpe on both symbols was fixed before this ran. D195 predicts step 1 "
      "passes and step 2 fails, on the grounds that the sizing defect is structural in the "
      "weighting rule rather than an accuracy problem with its input.")
    w("")
    w(f"---\n\nGenerated {p['generated_utc']} in {p['elapsed_seconds']:.1f}s · "
      f"every figure rendered from `{SUMMARY_JSON.name}`")
    return "\n".join(out) + "\n"


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
        RESULTS.parent.mkdir(parents=True, exist_ok=True)
        RESULTS.write_text(build_report(payload), encoding="utf-8")
        print(f"re-rendered {RESULTS.name} from {SUMMARY_JSON.name}")
        return 0

    started = time.time()
    raw, _ = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)

    results: dict[str, Any] = {}
    for symbol in list(GATE_SYMBOLS) + list(SECONDARY_SYMBOLS):
        if symbol not in cleaned:
            print(f"{symbol}: absent from {FIXTURE.name}")
            continue
        r = run_symbol(symbol, cleaned[symbol])
        results[symbol] = r
        v = passes(r)
        print(
            f"{symbol}: {r['days']:,} days ({r['short_days_dropped']} short dropped), "
            f"{r['n_pairs']:,} pairs  worst reduction {v['min_reduction']:+.1%}  "
            f"{'PASS' if v['passed'] else 'FAIL'}"
        )
        for name, red in v["cells"].items():
            print(f"    {name:<28} {red:+.1%}")

    payload = build_payload(results, time.time() - started)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(build_report(payload), encoding="utf-8")
    print()
    print(f"GATE ({', '.join(GATE_SYMBOLS)}): "
          f"{'PASS' if payload['gate_passed'] else 'FAIL'}")
    print(f"wrote {SUMMARY_JSON.name} and {RESULTS.name} in {payload['elapsed_seconds']:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
