"""Extend the daily fixtures back to each universe's own inception.

WHAT THIS IS AND IS NOT. The raw daily cache under `data/raw/alphavantage/daily/`
ALREADY holds full history to inception for all 117 symbols -- no price download
is needed. What IS missing is corporate actions: the committed events sidecars
span only 2015-01-16 .. 2024-12-23, and building a longer fixture against them
would leave splits unadjusted before 2015. D226 found twelve unadjusted splits in
a fixture built without them, the worst showing as a +1,772% single bar. So this
fetches SPLITS and DIVIDENDS over full history for all 117 symbols -- 234 calls --
and then rebuilds.

THE EXISTING FIXTURES ARE NOT TOUCHED. D24: a fixture is an immutable snapshot.
These are new files under new names, and every published number stays reproducible.

SAFETY, unchanged from `fetch_etf_holdout` and reused rather than restated:
env `ALPHAVANTAGE_API_KEY` first, then a key file OUTSIDE the repo; the key is
never logged and never appears in printed output; a plain floor between requests
at the polite rate; a hard stop after 5 consecutive failures rather than
hammering; and the raw cache is not committed (D191).

Resumable. Re-running costs nothing once the actions are cached.

    uv run python scripts/fetch_extended_history.py
"""

from __future__ import annotations

import csv
import gzip
import importlib.util
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


H = _load("holdout_fetch", "fetch_etf_holdout.py")

FIX = REPO / "data" / "fixtures"
DAILY = REPO / "data" / "raw" / "alphavantage" / "daily"
ACTIONS_CACHE = REPO / "data" / "raw" / "alphavantage" / "_actions_full.json"

SPAN_END = "2026-08-26"

UNIVERSES = {
    "universe_daily_extended": FIX / "universe_daily_2015_2024_raw.csv.gz",
    "universe_holdout_extended": FIX / "universe_holdout_daily_raw.csv.gz",
}

DONE_MESSAGE = (
    "Finish what you where doing then run the book on the new data "
    "only the book and nothing else until instructed"
)


def universe_of(path: Path) -> list[str]:
    syms = set()
    with gzip.open(path, "rt") as f:
        for row in csv.DictReader(f):
            syms.add(row["symbol"])
    return sorted(syms)


def fetch_actions(symbols: list[str]) -> dict:
    """SPLITS and DIVIDENDS over FULL history. Cached; re-runs are free."""
    cache = {"dividends": {}, "splits": {}}
    if ACTIONS_CACHE.exists():
        cache = json.loads(ACTIONS_CACHE.read_text(encoding="utf-8"))
    todo = [s for s in symbols if s not in cache["dividends"] or s not in cache["splits"]]
    if not todo:
        print(f"actions: all {len(symbols)} symbols already cached", flush=True)
        return cache

    key = H.api_key()
    limiter = H.RateLimiter(H.MIN_INTERVAL)
    print(f"actions: fetching {len(todo)} symbols ({2 * len(todo)} calls), "
          f"{H.MIN_INTERVAL:.2f}s apart", flush=True)
    consecutive = 0
    for i, sym in enumerate(todo, 1):
        try:
            for fn, bucket, amount_key, date_key in (
                ("DIVIDENDS", "dividends", "amount", "ex_dividend_date"),
                ("SPLITS", "splits", "split_factor", "effective_date"),
            ):
                payload = json.loads(H._get({"function": fn, "symbol": sym}, key, limiter))
                rows = payload.get("data", [])
                cache[bucket][sym] = [
                    [r[date_key] + "T00:00:00", float(r[amount_key])]
                    for r in rows if r.get(date_key)
                ]
            consecutive = 0
        except Exception as exc:                      # noqa: BLE001 - the key must not leak
            consecutive += 1
            print(f"  {sym}: {type(exc).__name__} ({consecutive} consecutive)", flush=True)
            if consecutive >= H.MAX_CONSECUTIVE_FAILURES:
                ACTIONS_CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True),
                                         encoding="utf-8")
                raise SystemExit(
                    f"{consecutive} consecutive failures -- stopping rather than hammering. "
                    "Progress is cached; re-run to resume."
                )
            continue
        if i % 20 == 0 or i == len(todo):
            print(f"  {i}/{len(todo)}", flush=True)
            ACTIONS_CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True),
                                     encoding="utf-8")
    ACTIONS_CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True), encoding="utf-8")
    return cache


def coverage_frontier(series: dict) -> list[tuple[str, int]]:
    """How far back the fixture could start against how many symbols it keeps.

    The date grid is the INTERSECTION -- `load_panel` refuses a panel whose
    symbols have different bar counts -- so ONE late arrival caps the whole
    universe. This is the design input for a later decision about 2008, and it is
    reported rather than acted on."""
    starts = sorted((min(v), s) for s, v in series.items())
    out = []
    for cut in ("2004-01-01", "2006-01-01", "2008-01-01", "2010-01-01",
                "2012-01-01", "2014-01-01", "2015-01-02"):
        out.append((cut, sum(1 for st, _ in starts if st <= cut)))
    return out, starts


def build(name: str, symbols: list[str], actions: dict) -> dict:
    series = {}
    for s in symbols:
        with gzip.open(DAILY / f"{s}.json.gz", "rt", encoding="utf-8") as f:
            series[s] = json.load(f)

    frontier, starts = coverage_frontier(series)
    grid = sorted(set.intersection(*(set(v) for v in series.values())))
    grid = [d for d in grid if d <= SPAN_END]
    binding = starts[-1]

    out = FIX / f"{name}_raw.csv.gz"
    with gzip.open(out, "wt", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["timestamp", "symbol", "open", "high", "low", "close", "volume"])
        for s in symbols:
            sp = actions["splits"].get(s, [])
            for d in grid:
                b = series[s][d]
                f_ = H.split_factor_at(d, sp)
                w.writerow([f"{d}T00:00:00", s,
                            f"{float(b['1. open']) / f_:.6f}", f"{float(b['2. high']) / f_:.6f}",
                            f"{float(b['3. low']) / f_:.6f}", f"{float(b['4. close']) / f_:.6f}",
                            f"{float(b['5. volume']) * f_:.1f}"])

    ev = {"dividends": {s: actions["dividends"].get(s, []) for s in symbols},
          "splits": {s: actions["splits"].get(s, []) for s in symbols}}
    (FIX / f"{name}_raw_events.json").write_text(
        json.dumps(ev, indent=1, sort_keys=True), encoding="utf-8")

    years = len(grid) / 252.0
    return {"name": name, "symbols": len(symbols), "bars": len(grid),
            "first": grid[0], "last": grid[-1], "years": years,
            "live_years": max(years - 1000 / 252.0, 0.0),
            "binding_symbol": binding[1], "binding_start": binding[0],
            "frontier": frontier,
            "dividends": sum(len(v) for v in ev["dividends"].values()),
            "splits": sum(len(v) for v in ev["splits"].values())}


def main() -> int:
    t0 = time.time()
    print("=" * 72)
    print("EXTENDING THE DAILY FIXTURES -- prices already cached, actions are not")
    print("=" * 72, flush=True)

    universes = {n: universe_of(p) for n, p in UNIVERSES.items()}
    everyone = sorted({s for v in universes.values() for s in v})
    missing = [s for s in everyone if not (DAILY / f"{s}.json.gz").exists()]
    if missing:
        raise SystemExit(f"not cached: {missing}")
    print(f"{len(everyone)} symbols across {len(universes)} universes, all prices cached\n")

    actions = fetch_actions(everyone)
    print()

    results = []
    for name, syms in universes.items():
        r = build(name, syms, actions)
        results.append(r)
        print(f"{r['name']}")
        print(f"  {r['symbols']} symbols x {r['bars']:,} bars   "
              f"{r['first']} .. {r['last']}   {r['years']:.1f}y raw, "
              f"{r['live_years']:.1f}y live after warm-up")
        print(f"  capped by {r['binding_symbol']} (inception {r['binding_start']})")
        print(f"  {r['dividends']:,} dividends, {r['splits']} splits")
        print("  coverage frontier -- symbols retained if the fixture started at:")
        for cut, n in r["frontier"]:
            print(f"    {cut}: {n}/{r['symbols']}")
        print(flush=True)

    (REPO / "data" / "extended_history_summary.json").write_text(
        json.dumps({"produced": "extend", "span_end": SPAN_END,
                    "elapsed_seconds": round(time.time() - t0, 1),
                    "universes": results}, indent=1, sort_keys=True),
        encoding="utf-8")

    print("=" * 72)
    print(f"DONE in {time.time() - t0:.0f}s. Existing fixtures untouched (D24).")
    print("=" * 72)
    print()
    print(DONE_MESSAGE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
