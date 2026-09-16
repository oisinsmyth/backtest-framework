"""D237 — the recovery rule on withheld data.

    position = 1  if  hist_L > 0  AND  md_L <= 0

Three tests that decompose the question:

    T1  60 new ETFs,  2015-2024   isolates INSTRUMENTS  (period fixed)
    T3  the SAME 57,  2025-2026   isolates PERIOD       (instruments fixed)
    T2  60 new ETFs,  2025-2026   both -- corroboration only, NO VERDICT

T1 carries the verdict. T3 has 414 live bars against T1's 1,515, so its standard
errors are 1.91x larger and its interval on arm-minus-B&H is roughly +/-2.5. IT
IS A SANITY CHECK -- did the rule catastrophically break -- NOT a confirmation.

THE RULE IS UNTOUCHED FROM D234. If so much as a parameter moves between the
mined run and this one, the test is void.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research import macd as M  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


L = _load("d217_ladder", "run_macd_ladder.py")
E = _load("d231_dial", "run_exposure_dial.py")
S = _load("d235_stops", "run_stops_targets.py")
J = _load("d229_jerk", "run_jerk_rung.py")
H = _load("holdout_fetch", "fetch_etf_holdout.py")

SUMMARY = REPO / "data" / "withheld_test_summary.json"
RESULTS = REPO / "docs" / "results" / "WITHHELD_TEST_RESULTS.md"
FIX = REPO / "data" / "fixtures"

SEED = 0
N_SIMS = 1000
MINED_DELTA = 0.511          # arm - B&H on the mined fixture, the H3 anchor
H3_FLOOR = 0.25 * MINED_DELTA
FORWARD_START = "2025-01-02"
SPAN_END = "2026-08-26"

TESTS = {
    "T1": {"fixture": "universe_holdout_daily_raw", "events": "universe_holdout_daily_raw_events",
           "score_from": None, "isolates": "instruments", "verdict": True},
    "T2": {"fixture": "universe_holdout_forward", "events": "universe_holdout_daily_raw_events",
           "score_from": FORWARD_START, "isolates": "both (confounded)", "verdict": False},
    "T3": {"fixture": "universe_parent57_forward", "events": "universe_parent57_forward_events",
           "score_from": FORWARD_START, "isolates": "period", "verdict": True},
}


def build_fixture(symbols, events_path: Path, out: Path) -> None:
    """A forward fixture on the parent's CSV schema, so `load_panel` is reused.

    Split-adjusted from the events sidecar the same way `fetch_etf_holdout.do_build`
    does it -- prices divided, volumes multiplied. The date grid is the INTERSECTION
    across the universe, because `load_panel` refuses a panel whose symbols have
    different bar counts."""
    if out.exists():
        return
    splits = json.loads(events_path.read_text(encoding="utf-8"))["splits"]
    series = {}
    for s in symbols:
        with gzip.open(REPO / "data" / "raw" / "alphavantage" / "daily" / f"{s}.json.gz",
                       "rt", encoding="utf-8") as f:
            series[s] = json.load(f)
    grid = sorted(set.intersection(*(set(v) for v in series.values())))
    grid = [d for d in grid if "2015-01-02" <= d <= SPAN_END]
    with gzip.open(out, "wt", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["timestamp", "symbol", "open", "high", "low", "close", "volume"])
        for s in symbols:
            for d in grid:
                b = series[s][d]
                f_ = H.split_factor_at(d, splits.get(s, []))
                w.writerow([f"{d}T00:00:00", s,
                            f"{float(b['1. open']) / f_:.6f}", f"{float(b['2. high']) / f_:.6f}",
                            f"{float(b['3. low']) / f_:.6f}", f"{float(b['4. close']) / f_:.6f}",
                            f"{float(b['5. volume']) * f_:.1f}"])
    print(f"  built {out.name}: {len(symbols)} x {len(grid):,} bars "
          f"({grid[0]} .. {grid[-1]})")


def universe_of(fixture: Path) -> list[str]:
    syms = set()
    with gzip.open(fixture, "rt") as f:
        for r in csv.DictReader(f):
            syms.add(r["symbol"])
    return sorted(syms)


def run_test(key: str) -> dict:
    cfg = TESTS[key]
    L.FIXTURE = FIX / f"{cfg['fixture']}.csv.gz"
    L.EVENTS = FIX / f"{cfg['events']}.json"
    panel, cleaned = L.load_panel()

    warm = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    if cfg["score_from"] is None:
        start = warm
    else:
        start = next(i for i, d in enumerate(panel.dates) if d[:10] >= cfg["score_from"])
        assert start >= warm, f"{key}: scoring would begin inside the warm-up"

    md, hs, ok = S.base_masks(panel, cleaned, start)
    arm = S.hold_book((hs > 0) & (md <= 0) & ok, start)
    ones = np.ones_like(arm)
    ones[:, :start] = 0.0

    a = E.score(panel, arm, start)
    b = E.score(panel, ones, start)
    delta = a["excess_sharpe"] - b["excess_sharpe"]

    nl = E.rotation_nulls(panel, {"arm": arm}, start, b["excess_sharpe"])
    ar = (L.portfolio_log_returns(panel, arm, total_return=True)[start:]
          - arm[:, start:].mean(axis=0) * E.RF_PER_BAR)
    br = L.portfolio_log_returns(panel, ones, total_return=True)[start:] - E.RF_PER_BAR
    bt = J.paired_block_bootstrap(ar, br)

    return {
        "test": key, "isolates": cfg["isolates"], "carries_verdict": cfg["verdict"],
        "n_symbols": len(panel.symbols), "live_bars": len(panel.dates) - start,
        "first_live_date": panel.dates[start], "last_date": panel.dates[-1],
        "arm": a, "buy_and_hold": b, "delta_vs_bh": delta,
        "rotation_null_p95": nl["per_cell_p95"]["arm"],
        "bootstrap": bt,
        "clears_H1": bool(delta > 0.0),
        "clears_H2": bool(delta > nl["per_cell_p95"]["arm"]),
        "clears_H3": bool(delta >= H3_FLOOR),
        "clears_E": bool(a["entries"] >= 100 and a["min_entries_per_symbol"] >= 30),
    }


def build() -> dict:
    t0 = time.time()
    print("building forward fixtures...")
    hold = universe_of(FIX / "universe_holdout_daily_raw.csv.gz")
    build_fixture(hold, FIX / "universe_holdout_daily_raw_events.json",
                  FIX / "universe_holdout_forward.csv.gz")
    parent = universe_of(FIX / "universe_daily_2015_2024_raw.csv.gz")
    build_fixture(parent, FIX / "universe_parent57_forward_events.json",
                  FIX / "universe_parent57_forward.csv.gz")

    out = {}
    for k in ("T1", "T2", "T3"):
        print(f"running {k}...", flush=True)
        out[k] = run_test(k)

    t1, t3 = out["T1"], out["T3"]
    reading = {
        (True, True): "STRONGEST RESULT THE PROGRAMME HAS PRODUCED. Still one span and one short "
                      "forward window -- not proof. Next step is more forward time, not promotion.",
        (True, False): "INSTRUMENT-GENERAL, PERIOD-SPECIFIC. The 2018-24 regime made it. Weak, and "
                       "consistent with the +0.978 correlation between the two universes.",
        (False, True): "PERIOD-GENERAL, INSTRUMENT-SPECIFIC -- fitted to those 57 names. Given "
                       "T3's power, more likely noise than signal.",
        (False, False): "THE RULE DOES NOT GENERALISE. CLOSED.",
    }[(t1["clears_H1"], t3["clears_H1"])]

    return {
        "produced": "D237", "stage": "verdict", "seed": SEED,
        "mined_delta": MINED_DELTA, "h3_floor": H3_FLOOR,
        "tests": out,
        "verdict_reading": reading,
        "rule_closed": not t1["clears_H1"],
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    o = ["# D237 — the recovery rule on withheld data\n"]
    o.append("**STAGE 2 — THE VERDICT.** T1 carries it; T3 is a sanity check, not a confirmation.\n")
    o.append(f"*seed {p['seed']}, {p['elapsed_seconds']}s. The rule is untouched from D234.*\n")
    o.append("## The three tests\n")
    o.append("| | isolates | symbols | live bars | arm | B&H | **Δ** | boot p05 | boot p95 | rot p95 | H1 | H2 | H3 |")
    o.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|")
    for k in ("T1", "T2", "T3"):
        t = p["tests"][k]
        star = "**" if t["carries_verdict"] else ""
        o.append(
            f"| {star}{k}{star} | {t['isolates']} | {t['n_symbols']} | {t['live_bars']:,} | "
            f"**{t['arm']['excess_sharpe']:+.3f}** | {t['buy_and_hold']['excess_sharpe']:+.3f} | "
            f"**{t['delta_vs_bh']:+.3f}** | {t['bootstrap']['p05']:+.3f} | "
            f"{t['bootstrap']['p95']:+.3f} | {t['rotation_null_p95']:+.3f} | "
            f"{'✓' if t['clears_H1'] else '✗'} | {'✓' if t['clears_H2'] else '✗'} | "
            f"{'✓' if t['clears_H3'] else '✗'} |"
        )
    o.append("")
    o.append(f"*H3 floor is {p['h3_floor']:+.3f} — 25% of the mined delta of "
             f"{p['mined_delta']:+.3f}.*\n")
    o.append("## Detail\n")
    o.append("| | CAGR | vol | max DD | exposure | entries | min/sym |")
    o.append("|---|---:|---:|---:|---:|---:|---:|")
    for k in ("T1", "T2", "T3"):
        t = p["tests"][k]
        for lab, s in ((f"{k} arm", t["arm"]), (f"{k} B&H", t["buy_and_hold"])):
            o.append(
                f"| {lab} | {s['cagr'] * 100:.2f}% | {s['vol'] * 100:.1f}% | "
                f"{s['max_drawdown'] * 100:+.2f}% | {s['exposure'] * 100:.1f}% | "
                f"{s['entries']:,} | {s['min_entries_per_symbol']} |"
            )
    o.append("")
    o.append("## The reading, as declared in advance\n")
    o.append(f"> **{p['verdict_reading']}**\n")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    if args.report_only:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    else:
        payload = build()
        SUMMARY.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    RESULTS.write_text(render(payload), encoding="utf-8")

    print()
    print(f"{'':4s} {'isolates':22s} {'bars':>6s} {'arm':>8s} {'B&H':>8s} {'delta':>8s} "
          f"{'p05':>8s} {'p95':>8s}  H1 H2 H3")
    for k in ("T1", "T2", "T3"):
        t = payload["tests"][k]
        print(f"{k:4s} {t['isolates']:22s} {t['live_bars']:6,} "
              f"{t['arm']['excess_sharpe']:+8.3f} {t['buy_and_hold']['excess_sharpe']:+8.3f} "
              f"{t['delta_vs_bh']:+8.3f} {t['bootstrap']['p05']:+8.3f} "
              f"{t['bootstrap']['p95']:+8.3f}  "
              f"{'Y' if t['clears_H1'] else 'N'}  {'Y' if t['clears_H2'] else 'N'}  "
              f"{'Y' if t['clears_H3'] else 'N'}")
    print()
    print(payload["verdict_reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
