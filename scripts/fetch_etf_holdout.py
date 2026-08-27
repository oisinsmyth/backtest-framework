"""Fetch a HOLDOUT universe of ETFs outside the mined 57.

D230 established that no further work on `universe_daily_2015_2024_raw.csv.gz`
can narrow anything: the intervals there are a property of the sample, not of the
analysis. The only move that resolves anything is independent data.

THE SELECTION RULE IS PINNED IN THIS FILE AND COMMITTED BEFORE IT RUNS. That is
the whole point. A holdout chosen after looking at how the arm does on candidates
is not a holdout, it is a ninth filter; the rule below is mechanical and
outcome-blind, and the liquidity screen reads only PRE-LIVE bars.

    --plan     LISTING_STATUS, apply the filters, write the candidate pool
    --fetch    daily bars for the pool (cached, resumable, rate-limited)
    --select   rank by pre-live liquidity, take the top N with full coverage
    --actions  SPLITS + DIVIDENDS for the selected symbols only
    --build    split-adjust and write the fixture, events sidecar and meta

NOTHING IN THIS FILE RUNS A STRATEGY. The arm does not touch this fixture until a
pre-registration naming its hurdles is committed.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

KEY_FILE = Path.home() / ".config" / "alphavantage" / "key"
CACHE = REPO / "data" / "raw" / "alphavantage" / "daily"
POOL = CACHE / "_pool.json"
SELECTION = CACHE / "_selection.json"

PARENT_FIXTURE = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw.csv.gz"
FIXTURE = REPO / "data" / "fixtures" / "universe_holdout_daily_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "universe_holdout_daily_raw_events.json"
META = REPO / "data" / "fixtures" / "universe_holdout_daily_raw.meta.json"

BASE = "https://www.alphavantage.co/query"
REQUESTS_PER_MIN = 66  # the tier ceiling is 75; pace under it with margin
MIN_INTERVAL = 60.0 / REQUESTS_PER_MIN
MAX_CONSECUTIVE_FAILURES = 5
TIMEOUT = 90

# ---------------------------------------------------------------------------
# THE SELECTION RULE. Declared here, committed before `--select` is ever run.
# ---------------------------------------------------------------------------

# Needs full history over the parent fixture's span.
MIN_IPO_DATE = "2014-12-31"

# Leveraged and inverse products are excluded because a daily-reset levered ETF
# has path-dependent decay -- it is a DIFFERENT INSTRUMENT, not a different
# sample of the same one, and the arm assumes ordinary price dynamics.
EXCLUDE_TOKENS = ("2X", "3X", "ULTRA", "INVERSE", "BEAR", "BULL", "LEVERAGED", "-1X", " SHORT")

# The liquidity screen reads ONLY bars strictly before the parent fixture's first
# LIVE bar (2018-12-21, after its 1,000-bar warm-up). A screen that could see the
# test period would be selecting on the outcome.
SCREEN_START = "2015-01-02"
SCREEN_END = "2018-12-20"
MIN_SCREEN_BARS = 500

# Matched to the parent universe's 57 so the two fixtures are comparable in
# breadth as well as span.
N_SELECT = 60

# ---------------------------------------------------------------------------
# AMENDED RULE -- select for INDEPENDENCE, not size.
#
# The original rule ranked by dollar volume, and the fixture it produced
# correlated with the parent's equal-weighted book at +0.9739 -- 94.9% SHARED
# VARIANCE, and a LESS diverse universe than the parent (mean pairwise 0.560
# against 0.439; 1.76 effective independent instruments against 2.23).
#
# The cause is structural and should have been foreseen: RANKING BY LIQUIDITY
# SELECTS FOR SIZE, AND SIZE SELECTS FOR BROAD-MARKET BETA. The most liquid ETFs
# outside the 57 are the huge index funds -- IVV, VOO, VTI, VEA, VWO -- which are
# precisely the ones carrying the least independent information.
#
# Amended: liquidity becomes a FLOOR (tradeable) rather than a RANK (biggest),
# and the 60 are chosen greedily to minimise average pairwise correlation within
# the set. Correlation is a market description computed on PRE-LIVE bars only --
# it touches no strategy return, so this is free under D228's boundary and cannot
# see the test period.
# ---------------------------------------------------------------------------
LIQUIDITY_FLOOR_USD = 5_000_000.0  # median pre-live dollar volume, a floor not a rank

# The build span is the PARENT FIXTURE'S EXACT DATE GRID. Same period, different
# instruments -- so a difference in result is attributable to the instruments and
# not to the years. Data after 2024-12-30 is cached but NOT built: forward time is
# a different question and gets its own record.
BUILD_START = "2015-01-02"
BUILD_END = "2024-12-30"


def api_key() -> str:
    """Env first, then the file OUTSIDE the repo. The key is never logged."""
    key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if key:
        return key.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"No API key. Set ALPHAVANTAGE_API_KEY or create {KEY_FILE}.")


class RateLimiter:
    """A plain floor on the gap between requests -- the conservative choice, and
    the polite one: a fetcher that never trips the limit is faster than one that
    trips it and backs off."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = min_interval
        self.last = 0.0

    def wait(self) -> None:
        gap = time.monotonic() - self.last
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self.last = time.monotonic()


def _get(params: dict, key: str, limiter: RateLimiter) -> str:
    limiter.wait()
    url = BASE + "?" + urllib.parse.urlencode({**params, "apikey": key})
    with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", "replace")


def parent_symbols_and_dates() -> tuple[set[str], list[str]]:
    """The 57 to exclude, and the exact date grid the holdout must match."""
    syms, dates = set(), set()
    with gzip.open(PARENT_FIXTURE, "rt") as f:
        for row in csv.DictReader(f):
            syms.add(row["symbol"])
            if BUILD_START <= row["timestamp"][:10] <= BUILD_END:
                dates.add(row["timestamp"])
    return syms, sorted(dates)


def do_plan(key: str, limiter: RateLimiter) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    body = _get({"function": "LISTING_STATUS", "state": "active"}, key, limiter)
    rows = list(csv.DictReader(io.StringIO(body)))
    etfs = [r for r in rows if r["assetType"] == "ETF"]
    existing, grid = parent_symbols_and_dates()

    pool = []
    for r in etfs:
        if r["symbol"] in existing:
            continue
        if not r.get("ipoDate") or r["ipoDate"] > MIN_IPO_DATE:
            continue
        if any(tok in r["name"].upper() for tok in EXCLUDE_TOKENS):
            continue
        pool.append({"symbol": r["symbol"], "name": r["name"], "ipoDate": r["ipoDate"]})

    POOL.write_text(json.dumps({"pool": pool, "grid_bars": len(grid)}, indent=1), encoding="utf-8")
    print(f"active listings   {len(rows):,}")
    print(f"ETFs              {len(etfs):,}")
    print(f"not in the 57     {len(etfs) - sum(1 for r in etfs if r['symbol'] in existing):,}")
    print(f"ELIGIBLE POOL     {len(pool):,}")
    print(f"parent date grid  {len(grid):,} bars  {grid[0][:10]} .. {grid[-1][:10]}")
    print(f"\nestimated fetch   {len(pool) / REQUESTS_PER_MIN:.1f} min")


def daily_path(symbol: str) -> Path:
    return CACHE / f"{symbol}.json.gz"


def do_fetch(key: str, limiter: RateLimiter) -> None:
    pool = json.loads(POOL.read_text(encoding="utf-8"))["pool"]
    todo = [p["symbol"] for p in pool if not daily_path(p["symbol"]).exists()]
    print(f"pool {len(pool):,}  cached {len(pool) - len(todo):,}  to fetch {len(todo):,}")
    consecutive, done = 0, 0
    t0 = time.time()
    for sym in todo:
        try:
            body = _get(
                {"function": "TIME_SERIES_DAILY", "symbol": sym, "outputsize": "full"},
                key, limiter,
            )
            payload = json.loads(body)
            # Alpha Vantage returns HTTP 200 on errors, so success is decided
            # STRUCTURALLY: no series key means failure however healthy the
            # status line looks. Writing an error body into a cache is the
            # failure mode this guards.
            if "Time Series (Daily)" not in payload:
                raise ValueError(str(payload)[:120])
            with gzip.open(daily_path(sym), "wt", encoding="utf-8") as f:
                json.dump(payload["Time Series (Daily)"], f)
            consecutive = 0
        except (urllib.error.URLError, ValueError, TimeoutError) as e:
            consecutive += 1
            print(f"  MISS {sym}: {type(e).__name__}")
            if consecutive >= MAX_CONSECUTIVE_FAILURES:
                raise SystemExit(
                    f"{consecutive} consecutive failures -- stopping rather than "
                    f"hammering the API. Re-run to resume from the cache."
                )
            continue
        done += 1
        if done % 100 == 0:
            rate = done / (time.time() - t0) * 60
            left = (len(todo) - done) / max(rate, 1e-9)
            print(f"  {done:,}/{len(todo):,}  {rate:.0f}/min  ~{left:.1f} min left", flush=True)
    print(f"fetched {done:,} in {(time.time() - t0) / 60:.1f} min")


def do_select() -> None:
    """Rank by pre-live median dollar volume, then take the top N that cover the
    parent's date grid COMPLETELY.

    Full coverage is not a nicety: `run_macd_ladder.load_panel` refuses a panel
    whose symbols have different bar counts, and sharing the parent's exact grid
    makes the two fixtures aligned bar-for-bar."""
    pool = json.loads(POOL.read_text(encoding="utf-8"))["pool"]
    _, grid = parent_symbols_and_dates()
    grid_dates = {t[:10] for t in grid}

    ranked = []
    for p in pool:
        path = daily_path(p["symbol"])
        if not path.exists():
            continue
        with gzip.open(path, "rt", encoding="utf-8") as f:
            series = json.load(f)
        screen = [
            float(v["4. close"]) * float(v["5. volume"])
            for d, v in series.items()
            if SCREEN_START <= d <= SCREEN_END
        ]
        if len(screen) < MIN_SCREEN_BARS:
            continue
        covered = grid_dates.issubset(series.keys())
        ranked.append({
            "symbol": p["symbol"],
            "name": p["name"],
            "median_dollar_volume": statistics.median(screen),
            "screen_bars": len(screen),
            "full_coverage": covered,
        })

    ranked.sort(key=lambda r: -r["median_dollar_volume"])
    selected = [r for r in ranked if r["full_coverage"]][:N_SELECT]
    SELECTION.write_text(
        json.dumps({"ranked": ranked, "selected": [r["symbol"] for r in selected]}, indent=1),
        encoding="utf-8",
    )
    print(f"ranked            {len(ranked):,} (>= {MIN_SCREEN_BARS} pre-live bars)")
    print(f"full coverage     {sum(r['full_coverage'] for r in ranked):,}")
    print(f"SELECTED          {len(selected)}")
    for i, r in enumerate(selected[:10], 1):
        print(f"  {i:2d}. {r['symbol']:6s} ${r['median_dollar_volume'] / 1e6:8.1f}M  {r['name'][:44]}")
    if len(selected) < N_SELECT:
        print(f"\nWARNING: only {len(selected)} of {N_SELECT} met full coverage.")


def do_select_diverse() -> None:
    """Select 60 for INDEPENDENCE rather than size. See the amended rule above.

    Greedy minimum-average-correlation. Starts from the fund least correlated
    with everything else, then repeatedly adds whichever fund is least correlated
    with what is already chosen. All correlations from PRE-LIVE bars only, so the
    selection cannot see the test period.

    Greedy rather than exhaustive because choosing 60 of ~1,100 to minimise mean
    pairwise correlation is combinatorial; greedy is the standard approximation
    and the rule is stated rather than tuned."""
    import numpy as np

    pool = json.loads(POOL.read_text(encoding="utf-8"))["pool"]
    _, grid = parent_symbols_and_dates()
    grid_dates = {t[:10] for t in grid}
    pre = [d for d in sorted(grid_dates) if SCREEN_START <= d <= SCREEN_END]

    syms, rets, liq = [], [], {}
    for p in pool:
        path = daily_path(p["symbol"])
        if not path.exists():
            continue
        with gzip.open(path, "rt", encoding="utf-8") as f:
            series = json.load(f)
        if not grid_dates.issubset(series.keys()):
            continue
        dv = [float(series[d]["4. close"]) * float(series[d]["5. volume"]) for d in pre]
        if len(dv) < MIN_SCREEN_BARS or statistics.median(dv) < LIQUIDITY_FLOOR_USD:
            continue
        closes = np.array([float(series[d]["4. close"]) for d in pre])
        syms.append(p["symbol"])
        liq[p["symbol"]] = statistics.median(dv)
        rets.append(np.log(closes[1:] / closes[:-1]))

    R = np.asarray(rets)
    print(f"eligible (floor ${LIQUIDITY_FLOOR_USD/1e6:.0f}M + full coverage)  {len(syms):,}")
    C = np.nan_to_num(np.corrcoef(R), nan=1.0)

    chosen = [int(np.argmin(C.mean(axis=1)))]
    while len(chosen) < min(N_SELECT, len(syms)):
        avg = C[:, chosen].mean(axis=1)
        avg[chosen] = np.inf
        chosen.append(int(np.argmin(avg)))

    sel = [syms[i] for i in chosen]
    sub = C[np.ix_(chosen, chosen)]
    iu = np.triu_indices_from(sub, 1)
    w = np.ones(len(chosen)) / len(chosen)
    SELECTION.write_text(
        json.dumps({"selected": sel, "rule": "diversity",
                    "mean_pairwise_prelive": float(sub[iu].mean()),
                    "effective_independent_prelive": float(1.0 / (w @ sub @ w))},
                   indent=1),
        encoding="utf-8",
    )
    print(f"SELECTED          {len(sel)}")
    print(f"  mean pairwise correlation (pre-live)  {sub[iu].mean():+.3f}")
    print(f"  effective independent instruments     {1.0 / (w @ sub @ w):.2f}")
    print("  first 10:", ", ".join(sel[:10]))


def do_actions(key: str, limiter: RateLimiter) -> None:
    selected = json.loads(SELECTION.read_text(encoding="utf-8"))["selected"]
    out = {"dividends": {}, "splits": {}}
    for i, sym in enumerate(selected, 1):
        for fn, bucket, amount_key in (
            ("DIVIDENDS", "dividends", "amount"),
            ("SPLITS", "splits", "split_factor"),
        ):
            payload = json.loads(_get({"function": fn, "symbol": sym}, key, limiter))
            rows = payload.get("data", [])
            out[bucket][sym] = [
                [r["ex_dividend_date" if fn == "DIVIDENDS" else "effective_date"] + "T00:00:00",
                 float(r[amount_key])]
                for r in rows
                if r.get("ex_dividend_date" if fn == "DIVIDENDS" else "effective_date")
            ]
        if i % 20 == 0:
            print(f"  actions {i}/{len(selected)}", flush=True)
    EVENTS.write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    n_div = sum(len(v) for v in out["dividends"].values())
    n_spl = sum(len(v) for v in out["splits"].values())
    print(f"events written: {n_div:,} dividends, {n_spl} splits")


def split_factor_at(stamp: str, splits: list) -> float:
    """Product of every split ratio effective AFTER this bar.

    PRICES ARE DIVIDED by this and VOLUMES MULTIPLIED, and the opposite
    directions are the point: a 2:1 split halves the price and doubles the share
    count. D226 found twelve unadjusted splits in a fixture built without this,
    the worst showing as a +1,772% single bar."""
    factor = 1.0
    for eff, ratio in splits:
        if eff[:10] > stamp[:10]:
            factor *= ratio
    return factor


def do_build() -> None:
    selected = json.loads(SELECTION.read_text(encoding="utf-8"))["selected"]
    if not EVENTS.exists():
        raise SystemExit("REFUSING TO BUILD AN UNADJUSTED FIXTURE. Run --actions first.")
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    splits = events["splits"]
    _, grid = parent_symbols_and_dates()

    rows = 0
    adjusted = 0
    max_move = {"symbol": None, "timestamp": None, "move": 0.0}
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(FIXTURE, "wt", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["timestamp", "symbol", "open", "high", "low", "close", "volume"])
        for sym in selected:
            with gzip.open(daily_path(sym), "rt", encoding="utf-8") as f:
                series = json.load(f)
            prev = None
            for stamp in grid:
                b = series[stamp[:10]]
                fct = split_factor_at(stamp, splits.get(sym, []))
                if fct != 1.0:
                    adjusted += 1
                c = float(b["4. close"]) / fct
                if prev:
                    move = abs(c / prev - 1.0)
                    if move > max_move["move"]:
                        max_move = {"symbol": sym, "timestamp": stamp, "move": move}
                prev = c
                w.writerow([
                    stamp, sym,
                    f"{float(b['1. open']) / fct:.6f}",
                    f"{float(b['2. high']) / fct:.6f}",
                    f"{float(b['3. low']) / fct:.6f}",
                    f"{c:.6f}",
                    f"{float(b['5. volume']) * fct:.1f}",
                ])
                rows += 1

    meta = {
        "symbols": selected,
        "n_symbols": len(selected),
        "rows": rows,
        "first": grid[0],
        "last": grid[-1],
        "bars_per_symbol": len(grid),
        "split_adjusted": True,
        "split_adjusted_bars": adjusted,
        "dividends": "in the sidecar, SAME split-adjusted frame as the prices (D75)",
        "date_grid": "the parent fixture's exact grid -- aligned bar-for-bar",
        "selection_rule": {
            "source": "LISTING_STATUS active ETFs, minus the parent 57",
            "min_ipo_date": MIN_IPO_DATE,
            "excluded_tokens": list(EXCLUDE_TOKENS),
            "liquidity_screen": f"median close*volume over {SCREEN_START}..{SCREEN_END}",
            "screen_is_pre_live": True,
            "min_screen_bars": MIN_SCREEN_BARS,
            "n_select": N_SELECT,
            "committed_before_run": True,
        },
        "largest_single_bar_move": max_move,
    }
    META.write_text(json.dumps(meta, indent=1, sort_keys=True), encoding="utf-8")
    print(f"rows          {rows:,}  ({len(selected)} symbols x {len(grid):,} bars)")
    print(f"splits        applied to {adjusted:,} bars")
    print(f"largest move  {max_move['move'] * 100:.2f}%  ({max_move['symbol']} {max_move['timestamp'][:10]})")
    if max_move["move"] > 0.35:
        print("  WARNING: a >35% single-bar move survived adjustment. Check before use.")


def main() -> int:
    ap = argparse.ArgumentParser()
    for flag in ("plan", "fetch", "select", "select-diverse", "actions", "build"):
        ap.add_argument(f"--{flag}", action="store_true")
    args = ap.parse_args()

    limiter = RateLimiter(MIN_INTERVAL)
    needs_key = args.plan or args.fetch or args.actions
    key = api_key() if needs_key else ""
    if needs_key:
        src = "env ALPHAVANTAGE_API_KEY" if os.environ.get("ALPHAVANTAGE_API_KEY") else str(KEY_FILE)
        print(f"key       {src}")  # the SOURCE, never the value

    if args.plan:
        do_plan(key, limiter)
    if args.fetch:
        do_fetch(key, limiter)
    if args.select:
        do_select()
    if getattr(args, 'select_diverse', False):
        do_select_diverse()
    if args.actions:
        do_actions(key, limiter)
    if args.build:
        do_build()
    if not any(vars(args).values()):
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
