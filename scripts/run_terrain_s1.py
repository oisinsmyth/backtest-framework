"""S1's null test — the verdict that opens or closes the terrain programme. (D189)

`TERRAIN_IMPLEMENTATION_PLAN.md` WP1 + WP2. The stop condition is the plan's own:

    If S1 fails its null, STOP the terrain programme and report — do not proceed to WP3+
    on the theory that other sensors will save it.

    uv run python scripts/run_terrain_s1.py

## The primary configuration is named before the run

The spec permits lookback in {90, 180}, bucket width in {0.25, 0.5} ATR and touch band k in
{0.5, 1.0} — eight combinations per symbol, on three metrics, across two symbols. That is
forty-eight looks, and a 5% test taken forty-eight times is not a 5% test.

So ONE configuration carries the verdict and the other seven are sensitivity. The primary is
**(180, 0.5, k=0.5)**, chosen on stated grounds rather than results: the longest lookback and
the coarsest buckets give the most stable map with the fewest nodes, hence the fewest looks;
the tightest k gives the strictest touch definition. Every combination run is counted in
TERRAIN_RESULTS.md's multiplicity ledger, sensitivity rows included, because the terrain
programme's deflated Sharpe at WP7 has to pay for all of it.

**And it must pass on BOTH symbols** — the every-symbol rule this project has applied since
Phase 1. One of two is a coin flip.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backtest_framework.data.cleaner import clean
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.research import breakout_universe as bu
from backtest_framework.research.terrain import (
    BUCKET_ATR,
    DAILY_LOOKBACKS,
    VolumeProfileSensor,
)
from backtest_framework.research.terrain_nulls import (
    TERRAIN_METRICS,
    TOUCH_ATR,
    run_null,
    verdict,
)

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw.csv.gz"
RESULTS = REPO / "TERRAIN_RESULTS.md"
SUMMARY_JSON = REPO / "data" / "terrain_s1_summary.json"

NL = "\n"
N_SIMS = 500
SEED = 0

PRIMARY = {"lookback": 180, "bucket_atr": 0.5, "k": 0.5}
"""Named before the run, on stated grounds — see the module docstring."""

VOLUME_UNITS = "quote_notional"
"""Every `X-USD` crypto pair in this repo reports quote-currency notional, not units
(D187). So this is a dollars-traded-at-price map, which is declared rather than inferred."""


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
        RESULTS.write_text(build_report(payload), encoding="utf-8")
        print(f"re-rendered {RESULTS.name} from {SUMMARY_JSON.name}")
        return 0

    started = time.time()
    raw, raw_volumes = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)
    volumes = {s: bu.align_volumes(cleaned[s], raw[s], raw_volumes[s]) for s in cleaned}

    runs: dict[str, dict[str, Any]] = {}
    for symbol in sorted(cleaned):
        bars = cleaned[symbol]
        for lookback in DAILY_LOOKBACKS:
            for bucket in BUCKET_ATR:
                sensor = VolumeProfileSensor(lookback, bucket, VOLUME_UNITS)
                for k in TOUCH_ATR:
                    key = f"{symbol}|{lookback}|{bucket}|{k}"
                    print(f"  {key} ...", flush=True)
                    result = run_null(bars, volumes[symbol], sensor, k, N_SIMS, SEED)
                    result["verdict"] = verdict(result)
                    runs[key] = result

    payload = build_payload(runs, cleaned)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RESULTS.write_text(build_report(payload), encoding="utf-8")
    print(f"ran {len(runs)} configurations in {time.time() - started:.0f}s")
    print(f"wrote {RESULTS.name} and {SUMMARY_JSON.name}")
    return 0


def _key(symbol: str, cfg: dict[str, Any]) -> str:
    return f"{symbol}|{cfg['lookback']}|{cfg['bucket_atr']}|{cfg['k']}"


def build_payload(runs: dict[str, dict[str, Any]], cleaned) -> dict[str, Any]:
    symbols = sorted(cleaned)
    primary = {s: runs[_key(s, PRIMARY)] for s in symbols}
    passed = {s: bool(r["verdict"]["passed"]) for s, r in primary.items()}
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "fixture": FIXTURE.name,
        "volume_units": VOLUME_UNITS,
        "n_sims": N_SIMS,
        "seed": SEED,
        "primary": PRIMARY,
        "symbols": symbols,
        "spans": {
            s: [cleaned[s][0].timestamp.date().isoformat(),
                cleaned[s][-1].timestamp.date().isoformat(), len(cleaned[s])]
            for s in symbols
        },
        "primary_passed": passed,
        "every_symbol_pass": all(passed.values()),
        "multiplicity": {
            "configurations": len(runs),
            "metrics_per_configuration": len(TERRAIN_METRICS),
            "total_looks": len(runs) * len(TERRAIN_METRICS),
        },
        "runs": runs,
    }


def build_report(p: dict[str, Any]) -> str:
    return f"""# TERRAIN_RESULTS.md — the terrain programme's ledger

**Append-only.** Every work package adds a dated section; nothing above is rewritten. This
is the single results ledger `TERRAIN_IMPLEMENTATION_PLAN.md` requires, and it carries the
multiplicity count that feeds the deflated Sharpe if the programme ever reaches WP7.

---

## WP1 + WP2 — the S1 volume-profile sensor and its null test

**Produced:** {p["generated_utc"][:10]} ·
**Reproduce:** `uv run python scripts/run_terrain_s1.py` (offline, deterministic)

### What was built

`VolumeProfileSensor` (S1) and the reusable null-test harness, plus the sensor interface
every later sensor must implement. Data: `{p["fixture"]}`, volume declared as
**{p["volume_units"]}** (D187 — a crypto fixture's volume column is quote-currency notional,
so this is a dollars-traded-at-price map).

{_span_table(p)}

**S1 is built on DAILY bars, deviating from the spec's stated preference for intraday.** The
1h fixture reports zero volume on half its bars — the known yfinance defect for crypto — so
a volume-at-price map built there would be missing half its mass, non-randomly. Daily volume
is complete over eleven years against the intraday fixture's two, and it is the frequency the
accepted baselines trade at, which is what WP5 has to annotate. The spec wants intraday for
sharpness, not necessity.

### The verdict

{_verdict_block(p)}

### The primary configuration, both symbols

{_primary_table(p)}

### Sensitivity — every other configuration in the stated sets

{_sensitivity_table(p)}

### Multiplicity ledger

| | |
|---|---|
| Configurations run | {p["multiplicity"]["configurations"]} |
| Metrics per configuration | {p["multiplicity"]["metrics_per_configuration"]} |
| **Total looks** | **{p["multiplicity"]["total_looks"]}** |

Two symbols x two lookbacks x two bucket widths x two touch bands, on three metrics. **A 5%
test taken {p["multiplicity"]["total_looks"]} times is not a 5% test**, which is why one
configuration was named before the run and the rest are sensitivity. Every row counts here
regardless — retired and failed configurations included — because the deflated Sharpe at WP7
has to pay for all of them.

### Standing caveats

1. **The null matches count and range, not where price lingered.** A high-volume node is by
   construction a price the market spent time at, so price is more likely to be near one
   than near a uniformly-placed level. The pseudo-levels match the real map's count and span
   but cannot match that property without destroying the thing being tested. **If S1 passes,
   this confound is the first thing to check, not the last.**
2. **Daily bars are a coarse map.** A 0.5-ATR bucket on BTC is hundreds to thousands of
   dollars wide; intraday data would sharpen it and is unavailable at usable quality.
3. **A pass here is not evidence the terrain model works.** It is evidence that one sensor's
   levels beat randomly placed ones on reaction statistics. The ladder's actual go/no-go is
   WP5 — features on the existing trade population — which this phase does not touch.
"""


def _span_table(p: dict[str, Any]) -> str:
    rows = NL.join(
        f"| `{s}` | {v[0]} | {v[1]} | {v[2]:,} |" for s, v in p["spans"].items()
    )
    return f"| Symbol | From | To | Bars |{NL}|---|---|---|---|{NL}{rows}"


def _verdict_block(p: dict[str, Any]) -> str:
    passed = p["primary_passed"]
    names = ", ".join(f"`{s}` {'PASS' if v else 'FAIL'}" for s, v in passed.items())
    if p["every_symbol_pass"]:
        return (
            f"**S1 PASSES its null on both symbols** ({names}) at the primary configuration.\n\n"
            "The terrain programme continues to WP3/WP4. That is the only thing this "
            "establishes — see caveat 1, which is now the first question rather than a "
            "footnote."
        )
    if any(passed.values()):
        return (
            f"**S1 passes on one symbol and not the other** ({names}).\n\n"
            "By the every-symbol rule this project has applied since Phase 1, that is a "
            "FAIL: one of two is a coin flip. The stop condition applies."
        )
    return (
        f"**S1 FAILS its null on both symbols** ({names}).\n\n"
        "The stop condition in `TERRAIN_IMPLEMENTATION_PLAN.md` applies: the terrain "
        "programme stops here and is reported as a negative result. Volume-profile levels "
        "do not beat levels scattered at random over the same range."
    )


def _primary_table(p: dict[str, Any]) -> str:
    cfg = p["primary"]
    out = []
    for s in p["symbols"]:
        r = p["runs"][_key(s, cfg)]
        if not r.get("available"):
            out.append(f"**`{s}`** — unavailable: {r.get('reason')}")
            continue
        rows = NL.join(
            f"| {m.label} | {r['real'][m.name]:+.4f} | {d['null_mean']:+.4f} | "
            f"[{d['null_p05']:+.4f}, {d['null_p95']:+.4f}] | {d['percentile']:.1f}th | "
            f"{d['p_value']:.4f} | {m.direction} |"
            for m in TERRAIN_METRICS
            if (d := r["distributions"].get(m.name))
        )
        out.append(
            f"**`{s}`** — {int(r['real']['n_touches']):,} touches over {r['n_rebuilds']} "
            f"rebuilds, {r['mean_levels_per_rebuild']:.1f} levels each; "
            f"{r['n_sims']} null draws.\n\n"
            f"| Metric | Real | Null mean | Null 90% | Percentile | p | Tail |\n"
            f"|---|---|---|---|---|---|---|\n{rows}"
        )
    return (f"{NL}{NL}".join(out)) + (
        f"{NL}{NL}Primary: lookback {cfg['lookback']}d, bucket {cfg['bucket_atr']} ATR, "
        f"touch band k={cfg['k']}. Each metric's tail was declared before the run — "
        "`MetricSpec.direction` exists so the direction is the hypothesis rather than "
        "something chosen once the numbers are in."
    )


def _sensitivity_table(p: dict[str, Any]) -> str:
    rows = []
    for key in sorted(p["runs"]):
        r = p["runs"][key]
        sym, lb, ba, k = key.split("|")
        if not r.get("available"):
            rows.append(f"| `{sym}` | {lb} | {ba} | {k} | — | unavailable | — |")
            continue
        v = r["verdict"]
        beaten = ", ".join(v["beaten"]) if v["beaten"] else "none"
        star = " **(primary)**" if (int(lb), float(ba), float(k)) == (
            p["primary"]["lookback"], p["primary"]["bucket_atr"], p["primary"]["k"]
        ) else ""
        rows.append(
            f"| `{sym}`{star} | {lb} | {ba} | {k} | {int(r['real']['n_touches']):,} | "
            f"{'PASS' if v['passed'] else 'fail'} | {beaten} |"
        )
    return (
        f"| Symbol | Lookback | Bucket (ATR) | k | Touches | Verdict | Metrics beaten |"
        f"{NL}|---|---|---|---|---|---|---|{NL}" + NL.join(rows)
    )


if __name__ == "__main__":
    raise SystemExit(main())
