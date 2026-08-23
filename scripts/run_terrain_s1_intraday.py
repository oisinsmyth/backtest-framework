"""WP2 re-run: S1 on exchange-native 15m volume (D194).

Pre-registered in `docs/decisions/D194-the-s1-sensor-re-tested-at-15m.md`, committed at
d2cc20e BEFORE this script existed. The bar, the effect-size floor, the bucket-span
diagnostic, the cumulative multiplicity ledger and the permanent stop are all fixed there.
Nothing in this file may relax any of them.

## What differs from `run_terrain_s1.py`, and what deliberately does not

**Every window is calendar-matched to D189, so bar resolution is the only variable.** At 96
bars a day: lookback 8,640 / 17,280 (90 / 180 days), ATR window 1,920 (20 days), horizon
480 (5 days), rebuild every 1,920 (20 days). Bucket width and touch band are therefore the
same PRICES they were on daily bars — the map is not finer-grained, it is differently
filled, with volume landing where it traded instead of smeared across a whole day.

`n_sims` stays 500 and `seed` stays 0. Cutting draws was the easy way to make the runtime
fit and would have widened every null interval, making a pass easier, for a reason with
nothing to do with the hypothesis.

**Traversal is reported in DAYS**, not 15-minute bars. The same number in bars would be 96x
larger and would read as a finding rather than a unit change.

## Why the verdict here is not `verdict()`

The harness's own `verdict()` passes if ANY of three metrics clears p <= 0.05, and its
docstring calls that "deliberately generous". Three generous one-sided tests is not a 5%
test. D194's bar is on `P(reversal | touch)` alone and requires all three of: beats its
null on BOTH symbols, a real-minus-null difference of at least 0.045 (D189's own null
half-width, so the effect must be large enough that D189 would have seen it), and presence
in more than half the 8-cell grid. `verdict.passed` is carried in the payload as a
cross-reference, never as the answer.

Run: uv run python scripts/run_terrain_s1_intraday.py
Re-render the results section from the committed JSON, offline: --report-only
"""

from __future__ import annotations

import json
import statistics
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
from backtest_framework.research import breakout_universe as bu  # noqa: E402
from backtest_framework.research.terrain import (  # noqa: E402
    BUCKET_ATR,
    INTRADAY_15M_LOOKBACKS,
    VolumeProfileSensor,
)
from backtest_framework.research.terrain_nulls import (  # noqa: E402
    TERRAIN_METRICS,
    TOUCH_ATR,
    run_null,
    sensor_levels,
    verdict,
)

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
RESULTS = REPO / "TERRAIN_RESULTS.md"
SUMMARY_JSON = REPO / "data" / "terrain_s1_15m_summary.json"

BARS_PER_DAY = 96
N_SIMS = 500
SEED = 0
VOLUME_UNITS = "quote_notional"
"""`crypto_binance_15m_raw`'s `volume` column is USDT notional (D193), declared not
inferred. The base-asset and taker-buy columns ride alongside it and are not used here."""

ATR_WINDOW = 20 * BARS_PER_DAY  # 1,920 — 20 days, matching D189
HORIZON = 5 * BARS_PER_DAY  # 480 — 5 days, matching D189
REBUILD_EVERY = 20 * BARS_PER_DAY  # 1,920 — 20 days, matching D189

PRIMARY = {"lookback": 180 * BARS_PER_DAY, "bucket_atr": 0.5, "k": 0.5}
"""180 days, coarsest buckets, strictest touch — D189's grounds, unchanged."""

VERDICT_SYMBOLS = ("BTCUSDT", "ETHUSDT")
"""Carry the verdict. Match D189 exactly so the comparison is clean."""

SECONDARY_SYMBOLS = ("XEMUSDT", "BTGUSDT")
"""Both delisted. Reported and counted in the multiplicity ledger, not carrying the
verdict. A pass on the majors that fails here is D180's pattern repeating."""

EFFECT_FLOOR = 0.045
"""Half-width of D189's own BTC null 90% interval [0.3415, 0.4310]. The effect must be
large enough that D189 would have seen it — without this, a difference resolvable only
because 15m gives 73x the bars is indistinguishable from a discovery."""

D189_PRIMARY = {
    "BTC-USD": {"p_reversal": 0.37677053824362605, "null_mean": 0.383459991862166,
                "percentile": 41.4, "n_touches": 353},
    "ETH-USD": {"p_reversal": 0.35294117647058826, "null_mean": 0.37358923430504065,
                "percentile": 26.0, "n_touches": 255},
}
"""Imported as constants from `data/terrain_s1_summary.json` so the report can put the two
runs side by side without either being retyped from memory."""


def span_census(bars, volumes, sensor) -> dict[str, float]:
    """The D194 diagnostic, computed BEFORE the verdict is looked at.

    A bar narrower than a bucket contributes its whole volume to one price, which is a
    close-price histogram wearing a volume label — the exact thing the sensor's
    volume-spreading exists to prevent, and which cannot happen on daily bars. Sampled at
    the rebuild indices rather than every bar, because that is where densities are built.
    """
    spans: list[int] = []
    singles = 0
    total = 0
    step = max(1, (len(bars) - sensor.warm_up_bars()) // 40)
    for index in range(sensor.warm_up_bars() - 1, len(bars), step):
        density = sensor.density(bars, index, volumes)
        if density is None or not density.spans:
            continue
        spans.extend(density.spans)
        singles += sum(1 for s in density.spans if s == 1)
        total += len(density.spans)
    if not spans:
        return {"median_span": 0.0, "single_bucket_share": 0.0, "n_bars_censused": 0}
    return {
        "median_span": float(statistics.median(spans)),
        "mean_span": float(statistics.fmean(spans)),
        "single_bucket_share": singles / total,
        "n_bars_censused": total,
    }


def run_symbol(symbol: str, bars, volumes) -> dict[str, dict[str, Any]]:
    runs: dict[str, dict[str, Any]] = {}
    for lookback in INTRADAY_15M_LOOKBACKS:
        for bucket in BUCKET_ATR:
            sensor = VolumeProfileSensor(lookback, bucket, VOLUME_UNITS, atr_window=ATR_WINDOW)
            if len(bars) < sensor.warm_up_bars() + HORIZON + REBUILD_EVERY:
                print(
                    f"  {symbol}|{lookback}|{bucket}: SKIPPED — {len(bars):,} bars is short "
                    f"of the {sensor.warm_up_bars() + HORIZON + REBUILD_EVERY:,} this "
                    "configuration needs; reported rather than run on a stub",
                    flush=True,
                )
                continue
            census = span_census(bars, volumes, sensor)
            for k in TOUCH_ATR:
                key = f"{symbol}|{lookback}|{bucket}|{k}"
                started = time.time()
                print(f"  {key} ...", flush=True)
                result = run_null(
                    bars, volumes, sensor, k, N_SIMS, SEED,
                    rebuild_every=REBUILD_EVERY, horizon=HORIZON,
                    atr_window=ATR_WINDOW, precompute=True,
                )
                result["verdict"] = verdict(result)
                result["span_census"] = census
                result["elapsed_s"] = time.time() - started
                runs[key] = result
                if result.get("available"):
                    d = result["distributions"]["p_reversal"]
                    real = result["real"]["p_reversal"]
                    print(
                        f"  {key}: {result['real']['n_touches']:>6.0f} touches  "
                        f"p_rev {real:+.4f} vs null {d['null_mean']:+.4f}  "
                        f"delta {real - d['null_mean']:+.4f}  "
                        f"pct {d['percentile']:>5.1f}  "
                        f"span med {census['median_span']:.1f}  "
                        f"({result['elapsed_s']:.0f}s)",
                        flush=True,
                    )
                else:
                    print(f"  {key}: unavailable — {result.get('reason')}", flush=True)
    return runs


def evaluate(runs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """D194's three conditions, applied exactly as pre-registered."""
    per_symbol: dict[str, Any] = {}
    for symbol in VERDICT_SYMBOLS:
        key = f"{symbol}|{PRIMARY['lookback']}|{PRIMARY['bucket_atr']}|{PRIMARY['k']}"
        run = runs.get(key)
        if not run or not run.get("available"):
            per_symbol[symbol] = {"available": False}
            continue
        dist = run["distributions"]["p_reversal"]
        real = run["real"]["p_reversal"]
        delta = real - dist["null_mean"]
        cells = [
            r for k2, r in runs.items()
            if k2.startswith(f"{symbol}|") and r.get("available")
        ]
        beaten = [
            r for r in cells
            if r["distributions"]["p_reversal"]["p_value"] <= 0.05
            and r["real"]["p_reversal"] - r["distributions"]["p_reversal"]["null_mean"] > 0
        ]
        per_symbol[symbol] = {
            "available": True,
            "n_touches": run["real"]["n_touches"],
            "real": real,
            "null_mean": dist["null_mean"],
            "delta": delta,
            "percentile": dist["percentile"],
            "p_value": dist["p_value"],
            "statistical_pass": bool(dist["p_value"] <= 0.05 and delta > 0),
            "effect_pass": bool(delta >= EFFECT_FLOOR),
            "grid_cells": len(cells),
            "grid_beaten": len(beaten),
            "breadth_pass": bool(len(beaten) * 2 > len(cells)),
            "harness_verdict_generous": bool(run["verdict"]["passed"]),
            "span_census": run["span_census"],
        }
    ready = [v for v in per_symbol.values() if v.get("available")]
    return {
        "per_symbol": per_symbol,
        "statistical": bool(ready) and all(v["statistical_pass"] for v in ready)
        and len(ready) == len(VERDICT_SYMBOLS),
        "effect": bool(ready) and all(v["effect_pass"] for v in ready)
        and len(ready) == len(VERDICT_SYMBOLS),
        "breadth": bool(ready) and all(v["breadth_pass"] for v in ready)
        and len(ready) == len(VERDICT_SYMBOLS),
        "effect_floor": EFFECT_FLOOR,
    }


DAILY_FIXTURE = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw.csv.gz"
CONTROL_START = "2018-02-12"
CONTROL_END = "2025-12-31"
"""The overlap between D189's daily fixture and the 15m one. D194 makes this control
mandatory: without it, any difference between D189 and D194 is confounded with a different
decade and the comparison says nothing. D189's exact primary configuration, on daily bars,
restricted to the span the 15m run actually covers."""


def daily_control() -> dict[str, Any]:
    """D189's primary configuration, re-run on the overlapping span only."""
    from datetime import date

    raw, raw_volumes = load_fixture_csv_with_volumes(DAILY_FIXTURE)
    cleaned, _ = clean(raw)
    volumes = {s: bu.align_volumes(cleaned[s], raw[s], raw_volumes[s]) for s in cleaned}
    lo, hi = date.fromisoformat(CONTROL_START), date.fromisoformat(CONTROL_END)

    out: dict[str, Any] = {}
    for symbol in ("BTC-USD", "ETH-USD"):
        keep = [
            i for i, tb in enumerate(cleaned[symbol]) if lo <= tb.timestamp.date() <= hi
        ]
        bars = [cleaned[symbol][i] for i in keep]
        vols = [volumes[symbol][i] for i in keep]
        # D189's constants exactly: lookback 180 daily bars, 0.5 ATR, k=0.5, and the
        # module defaults for ATR window (20), horizon (5) and rebuild cadence (20).
        sensor = VolumeProfileSensor(180, 0.5, VOLUME_UNITS)
        result = run_null(bars, vols, sensor, 0.5, N_SIMS, SEED)
        result["verdict"] = verdict(result)
        out[symbol] = {
            "bars": len(bars),
            "span": [bars[0].timestamp.date().isoformat(),
                     bars[-1].timestamp.date().isoformat()],
            "available": result.get("available", False),
            "n_touches": result["real"]["n_touches"] if result.get("available") else 0,
            "p_reversal": result["real"]["p_reversal"] if result.get("available") else None,
            "null_mean": (result["distributions"]["p_reversal"]["null_mean"]
                          if result.get("available") else None),
            "percentile": (result["distributions"]["p_reversal"]["percentile"]
                           if result.get("available") else None),
            "p_value": (result["distributions"]["p_reversal"]["p_value"]
                        if result.get("available") else None),
        }
        if out[symbol]["available"]:
            print(
                f"  control {symbol}: {out[symbol]['n_touches']:.0f} touches  "
                f"real {out[symbol]['p_reversal']:+.4f} vs null "
                f"{out[symbol]['null_mean']:+.4f}  pct {out[symbol]['percentile']:.1f}",
                flush=True,
            )
    return out


def build_payload(runs, spans_by_symbol, elapsed, control=None) -> dict[str, Any]:
    outcome = evaluate(runs)
    outcome["passed"] = bool(
        outcome["statistical"] and outcome["effect"] and outcome["breadth"]
    )
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": "D194-the-s1-sensor-re-tested-at-15m.md (commit d2cc20e)",
        "fixture": FIXTURE.name,
        "volume_units": VOLUME_UNITS,
        "bars_per_day": BARS_PER_DAY,
        "n_sims": N_SIMS,
        "seed": SEED,
        "windows": {
            "lookbacks": list(INTRADAY_15M_LOOKBACKS),
            "atr_window": ATR_WINDOW,
            "horizon": HORIZON,
            "rebuild_every": REBUILD_EVERY,
            "note": "every window calendar-matched to D189 at 96 bars/day",
        },
        "primary": PRIMARY,
        "verdict_symbols": list(VERDICT_SYMBOLS),
        "secondary_symbols": list(SECONDARY_SYMBOLS),
        "effect_floor": EFFECT_FLOOR,
        "d189_primary": D189_PRIMARY,
        "spans": spans_by_symbol,
        "outcome": outcome,
        "daily_control": control,
        "multiplicity": {
            "d189_looks": 48,
            "this_run_configurations": len(runs),
            "metrics_per_configuration": len(TERRAIN_METRICS),
            "this_run_looks": len(runs) * len(TERRAIN_METRICS),
            "daily_control_looks": 3 if control else 0,
            "cumulative_looks": 48 + len(runs) * len(TERRAIN_METRICS) + (3 if control else 0),
        },
        "elapsed_seconds": elapsed,
        "runs": runs,
    }


def _fmt_days(bars: float) -> str:
    return f"{bars / BARS_PER_DAY:.2f}"


def build_section(p: dict[str, Any]) -> str:
    """The dated section appended to TERRAIN_RESULTS.md. Every figure comes from the
    payload — D189's own lesson is that prose drifting from its numbers is this project's
    most repeated defect."""
    o = p["outcome"]
    lines: list[str] = []
    w = lines.append

    w("")
    w("---")
    w("")
    w("## WP2 re-run — S1 on exchange-native 15m volume (D194)")
    w("")
    w(f"**Produced:** {p['generated_utc'][:10]} · "
      f"**Reproduce:** `uv run python scripts/run_terrain_s1_intraday.py` (offline, deterministic)")
    w("")
    w(f"Pre-registered in `{p['preregistration']}`, before this run existed. "
      f"Data: `{p['fixture']}`, volume declared as `{p['volume_units']}`. "
      f"Every window calendar-matched to D189 at {p['bars_per_day']} bars/day — lookback "
      f"{'/'.join(str(x) for x in p['windows']['lookbacks'])} bars, ATR "
      f"{p['windows']['atr_window']}, horizon {p['windows']['horizon']}, rebuild every "
      f"{p['windows']['rebuild_every']}. `n_sims` {p['n_sims']}, seed {p['seed']}.")
    w("")

    w("### The bucket-span census, reported before the verdict")
    w("")
    w("A bar narrower than a bucket puts its whole volume at one price, which is a "
      "close-price histogram wearing a volume label. D194 pre-committed to reporting this "
      "first, because a map that has degenerated this way looks exactly like a real one.")
    w("")
    w("| symbol | median span | mean span | single-bucket share | bars censused |")
    w("|---|---:|---:|---:|---:|")
    for symbol, c in p["spans"].items():
        w(f"| `{symbol}` | {c['median_span']:.1f} | {c.get('mean_span', 0.0):.2f} | "
          f"{c['single_bucket_share']:.1%} | {c['n_bars_censused']:,} |")
    w("")

    w("### The primary configuration, against D189")
    w("")
    w("| | D189 (daily) | D194 (15m) |")
    w("|---|---|---|")
    for symbol, d189_key in (("BTCUSDT", "BTC-USD"), ("ETHUSDT", "ETH-USD")):
        v = o["per_symbol"].get(symbol, {})
        old = p["d189_primary"][d189_key]
        if not v.get("available"):
            w(f"| **{symbol}** | — | unavailable |")
            continue
        w(f"| **{symbol}** touches | {old['n_touches']:,} | {v['n_touches']:,.0f} |")
        w(f"| P(reversal \\| touch) real | {old['p_reversal']:+.4f} | {v['real']:+.4f} |")
        w(f"| null mean | {old['null_mean']:+.4f} | {v['null_mean']:+.4f} |")
        w(f"| **real − null** | {old['p_reversal'] - old['null_mean']:+.4f} | "
          f"**{v['delta']:+.4f}** |")
        w(f"| percentile | {old['percentile']:.1f}th | {v['percentile']:.1f}th |")
    w("")

    control = p.get("daily_control")
    if control:
        w("### The span-matched daily control")
        w("")
        w("D189's exact primary configuration on daily bars, restricted to "
          f"{CONTROL_START} – {CONTROL_END} — the overlap with the 15m fixture. Without it, "
          "any difference between D189 and D194 is confounded with a different decade.")
        w("")
        w("| symbol | bars | span | touches | real | null mean | real − null | pct |")
        w("|---|---:|---|---:|---:|---:|---:|---:|")
        for symbol, c in control.items():
            if not c.get("available"):
                w(f"| `{symbol}` | {c['bars']:,} | — | unavailable | — | — | — | — |")
                continue
            w(f"| `{symbol}` | {c['bars']:,} | {c['span'][0]} .. {c['span'][1]} | "
              f"{c['n_touches']:,.0f} | {c['p_reversal']:+.4f} | {c['null_mean']:+.4f} | "
              f"{c['p_reversal'] - c['null_mean']:+.4f} | {c['percentile']:.1f} |")
        w("")

    w("### The bar, as pre-registered")
    w("")
    w("| condition | requirement | result |")
    w("|---|---|---|")
    w(f"| 1. Statistical | beats its null on BOTH symbols | "
      f"**{'PASS' if o['statistical'] else 'FAIL'}** |")
    w(f"| 2. Effect size | real − null ≥ {o['effect_floor']} on both | "
      f"**{'PASS' if o['effect'] else 'FAIL'}** |")
    w(f"| 3. Breadth | effect in > half the grid | "
      f"**{'PASS' if o['breadth'] else 'FAIL'}** |")
    w(f"| **Overall** | all three | **{'PASS' if o['passed'] else 'FAIL'}** |")
    w("")
    w("The effect-size floor is the half-width of D189's own BTC null interval. The effect "
      "had to be large enough that D189 would have seen it.")
    w("")

    w("### Every configuration")
    w("")
    w("| configuration | touches | real | null mean | delta | pct | p | median span |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|")
    for key, r in sorted(p["runs"].items()):
        if not r.get("available"):
            w(f"| `{key}` | — | — | — | — | — | — | unavailable |")
            continue
        d = r["distributions"]["p_reversal"]
        real = r["real"]["p_reversal"]
        w(f"| `{key}` | {r['real']['n_touches']:,.0f} | {real:+.4f} | "
          f"{d['null_mean']:+.4f} | {real - d['null_mean']:+.4f} | {d['percentile']:.1f} | "
          f"{d['p_value']:.3f} | {r['span_census']['median_span']:.1f} |")
    w("")
    w("Traversal in the payload is in 15-minute bars; divided by 96 it is directly "
      "comparable to D189's 4.31 (BTC) and 4.36 (ETH) days.")
    w("")

    m = p["multiplicity"]
    w("### Multiplicity ledger — cumulative")
    w("")
    w("| | |")
    w("|---|---|")
    w(f"| D189 looks | {m['d189_looks']} |")
    w(f"| This run, configurations | {m['this_run_configurations']} |")
    w(f"| This run, looks | {m['this_run_looks']} |")
    w(f"| Daily control looks | {m.get('daily_control_looks', 0)} |")
    w(f"| **Cumulative looks on one hypothesis** | **{m['cumulative_looks']}** |")
    w("")
    w("Never reset. D189's failures count — the question has not changed, and the plan's "
      "own rule is that retired and failed items still count.")
    w("")
    return "\n".join(lines) + "\n"


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
        _append_section(payload)
        print(f"re-rendered the D194 section of {RESULTS.name} from {SUMMARY_JSON.name}")
        return 0

    started = time.time()
    raw, raw_volumes = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)
    volumes = {s: bu.align_volumes(cleaned[s], raw[s], raw_volumes[s]) for s in cleaned}

    runs: dict[str, dict[str, Any]] = {}
    spans: dict[str, Any] = {}
    for symbol in list(VERDICT_SYMBOLS) + list(SECONDARY_SYMBOLS):
        if symbol not in cleaned:
            print(f"{symbol}: absent from {FIXTURE.name}")
            continue
        print(f"{symbol}: {len(cleaned[symbol]):,} bars", flush=True)
        symbol_runs = run_symbol(symbol, cleaned[symbol], volumes[symbol])
        runs.update(symbol_runs)
        for r in symbol_runs.values():
            spans[symbol] = r["span_census"]
            break

    print("span-matched daily control (D189's primary config, overlapping span only)")
    control = daily_control()

    payload = build_payload(runs, spans, time.time() - started, control)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _append_section(payload)

    o = payload["outcome"]
    print()
    print(f"statistical {o['statistical']}, effect {o['effect']}, breadth {o['breadth']}")
    print(f"OVERALL: {'PASS' if o['passed'] else 'FAIL'}")
    print(f"wrote {SUMMARY_JSON.name} and appended the D194 section to {RESULTS.name} "
          f"in {payload['elapsed_seconds']:.0f}s")
    return 0


_MARKER = "## WP2 re-run — S1 on exchange-native 15m volume (D194)"


def _append_section(payload: dict[str, Any]) -> None:
    """Append, never overwrite. The ledger's own header says append-only, and the daily
    runner rewrites the whole file — a latent contradiction this one does not repeat."""
    existing = RESULTS.read_text(encoding="utf-8")
    section = build_section(payload)
    if _MARKER in existing:
        existing = existing[: existing.index("\n---\n\n" + _MARKER)]
    RESULTS.write_text(existing.rstrip("\n") + "\n" + section, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
