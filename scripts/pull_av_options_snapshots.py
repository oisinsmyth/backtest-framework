"""Pull quarterly HISTORICAL_OPTIONS snapshots for the option-dense end of the mining universe.

    uv run python scripts/pull_av_options_snapshots.py --plan
    uv run python scripts/pull_av_options_snapshots.py --pull

DATA ACQUISITION ONLY. No statistic is computed here and no bar is stated here -- the screen's
design and its bar are committed separately, BEFORE the screen runs (D263's inversion).

The key is read from env then ~/.config/alphavantage/key and is NEVER printed or logged.
Chains cache to data/raw/alphavantage/options/, gitignored (D191: raw caches not committed,
derived fixtures are). Resumable: a cached (symbol, date) is never re-requested.
Paced at 66/min under the 75 ceiling, the house convention.

UNIVERSE. The probe measured open-interest density collapsing below the second dollar-volume
decile -- 43 and 19 strikes with OI>=100 in deciles 1 and 2, then 2 to 8 below that. Four strikes
is not a price-level map. So this pulls the top two deciles for HEADROOM; the binding universe
filter is the per-date OI density applied at SCREEN time, which keeps the universe causal and
dynamic rather than pre-selected.

Ranking is by median dollar volume over each name's FIRST 252 ELIGIBLE BARS in the window --
causal, and the same convention the fixture's own build screen uses.

SNAPSHOT DATES are mid-quarter (15 Feb / May / Aug / Nov), DELIBERATELY away from the third-Friday
quarterly expiry where open interest mechanically collapses.
"""
import argparse
import gzip
import importlib.util
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
API = "https://www.alphavantage.co/query"
KEY_FILE = pathlib.Path.home() / ".config" / "alphavantage" / "key"
CACHE = REPO / "data" / "raw" / "alphavantage" / "options"
MANIFEST = CACHE / "_manifest.json"
FIX = REPO / "data/fixtures/us_shorts_daily_raw.csv.gz"
EVJ = REPO / "data/fixtures/us_shorts_daily_raw_events.json"

N_NAMES = 210
YEARS = range(2015, 2024)
MONTHS = (2, 5, 8, 11)
MIN_INTERVAL = 60.0 / 66.0
TIMEOUT = 60
RETRIES = 3


def api_key():
    k = os.environ.get("ALPHAVANTAGE_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"No API key. Set ALPHAVANTAGE_API_KEY or create {KEY_FILE}.")


_last = [0.0]


def _pace():
    gap = time.monotonic() - _last[0]
    if gap < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - gap)
    _last[0] = time.monotonic()


def path_of(symbol, date):
    return CACHE / symbol / f"{date}.json.gz"


def fetch(symbol, date, key):
    """(status, n_contracts). Cached and resumable; a cached pair is never re-requested."""
    p = path_of(symbol, date)
    if p.exists():
        try:
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                d = json.load(fh)
            return "cached", len(d.get("data") or [])
        except (OSError, EOFError, json.JSONDecodeError):
            p.unlink(missing_ok=True)                 # a truncated cache file is not a result
    params = {"function": "HISTORICAL_OPTIONS", "symbol": symbol, "date": date, "apikey": key}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    for attempt in range(RETRIES):
        _pace()
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
                payload = json.loads(r.read().decode("utf-8", errors="replace"))
            break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt == RETRIES - 1:
                return f"error: {type(e).__name__}", 0
            time.sleep(2.0 * (attempt + 1))
    for flag in ("Error Message", "Note", "Information"):
        if flag in payload:
            return f"{flag}", 0
    rows = payload.get("data")
    if not isinstance(rows, list):                    # structural success test, not a status code
        return "no data key", 0
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return "ok", len(rows)


def universe_and_dates(verbose=True):
    s = importlib.util.spec_from_file_location("rp", REPO / "scripts" / "ragged_panel.py")
    RP = importlib.util.module_from_spec(s)
    sys.modules["rp"] = RP
    s.loader.exec_module(RP)
    panel, cleaned = RP.load_ragged(FIX, EVJ, fee_bps=0.0)
    lo, hi = f"{min(YEARS)}-01-01", f"{max(YEARS)}-12-31"
    liq = {}
    for sym in panel.symbols:
        v = [st.bar.close * st.bar.volume for st in cleaned[sym]
             if lo <= st.timestamp[:10] <= hi and st.bar.volume and st.bar.close]
        if len(v) >= 252:
            liq[sym] = float(np.median(v[:252]))       # FIRST 252 bars -- causal
    syms = sorted(liq, key=lambda x: -liq[x])[:N_NAMES]
    grid = list(panel.dates)
    arr = np.array(grid)
    dates = []
    for y in YEARS:
        for m in MONTHS:
            want = f"{y}-{m:02d}-15"
            j = int(np.searchsorted(arr, want, side="right")) - 1   # nearest PRIOR trading day
            if 0 <= j < len(grid):
                dates.append(grid[j])
    dates = sorted(set(dates))
    if verbose:
        print(f"  universe {len(syms)} names of {len(liq):,} rankable   "
              f"median $vol {np.median([liq[x] for x in syms]):,.0f}")
        print(f"  snapshots {len(dates)}  {dates[0]} -> {dates[-1]}")
    return syms, dates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--pull", action="store_true")
    a = ap.parse_args()
    print("AV OPTIONS SNAPSHOT PULL -- acquisition only, no statistic, no bar\n")
    syms, dates = universe_and_dates()
    todo = [(s, d) for s in syms for d in dates if not path_of(s, d).exists()]
    total = len(syms) * len(dates)
    print(f"  {total:,} pairs, {total - len(todo):,} already cached, {len(todo):,} to fetch")
    print(f"  projected {len(todo) * MIN_INTERVAL / 3600:.2f} h at 66/min")
    if a.plan:
        return 0
    if not a.pull:
        ap.error("pass --plan or --pull")
    key = api_key()
    CACHE.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    stats, done = {}, 0
    for sym, d in todo:
        st, n = fetch(sym, d, key)
        stats[st] = stats.get(st, 0) + 1
        done += 1
        if done % 250 == 0:
            el = time.time() - t0
            print(f"    {done:,}/{len(todo):,}  {el/60:.0f}m elapsed, "
                  f"{(len(todo)-done)*el/done/60:.0f}m left   {stats}", flush=True)
    MANIFEST.write_text(json.dumps(dict(symbols=syms, dates=dates, stats=stats,
                                        n_pairs=total, fetched=len(todo)), indent=1), encoding="utf-8")
    print(f"\n  done in {(time.time()-t0)/60:.0f}m   {stats}")
    print(f"  wrote {MANIFEST.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
