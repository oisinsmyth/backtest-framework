"""D245 — build the wide-universe daily fixtures.

Two cells, both liquidity screens chosen for COST-MODEL reasons and never for
returns:

    W5   median daily dollar volume >= $5,000,000   ~245 symbols  (primary)
    W1   median daily dollar volume >= $1,000,000   ~496 symbols  (breadth)

W5 is the level at which the committed 1 bp half-spread in `per_side_bps` stays
credible. W1 is registered because whether breadth or cost realism dominates is
the actual question, and guessing it would be worse than measuring it.

SPAN IS FIXED TO THE EXTENDED FIXTURE'S: 2009-11-11 onward, so the wide universe
scores on the identical bars as D243 and the comparison is clean. Symbols without
history back to that date are excluded -- a history screen, not a survivorship one.

MEMORY. The naive build holds every row of a 496 x 4,222 panel in Python objects.
This streams symbol-by-symbol and writes in symbol-major order, which is the
fixture's own layout, so only one symbol is resident at a time.

THE GRID IS INTERSECTED AFTER CLEANING and iterated to a fixed point -- `clean`
drops bars per symbol and `load_panel` refuses a ragged panel. Same pattern as
`run_book_crypto` and `build_intraday_panel`.

    uv run python scripts/build_wide_universe.py
"""

from __future__ import annotations

import csv
import glob
import gzip
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


L = _load("d217_ladder", "run_macd_ladder.py")
H = _load("holdout_fetch", "fetch_etf_holdout.py")

FIX = REPO / "data" / "fixtures"
DAILY = REPO / "data" / "raw" / "alphavantage" / "daily"
ACTIONS = REPO / "data" / "raw" / "alphavantage" / "_actions_full.json"

START = "2009-11-11"          # the extended fixture's first bar
END = "2026-08-26"

CELLS = {"W5": 5_000_000.0, "W1": 1_000_000.0}

# Structural exclusions, asserted rather than assumed. None are expected to be
# present -- the cache was built without them -- but a silent reappearance would
# corrupt a long-only book, so the check is explicit.
BANNED = {
    "TQQQ", "SQQQ", "SPXU", "UPRO", "SPXL", "TNA", "TZA", "SOXL", "SOXS", "LABU",
    "LABD", "FAS", "FAZ", "UVXY", "SVXY", "VIXY", "TMF", "TMV", "NUGT", "DUST",
    "JNUG", "JDST", "YINN", "YANG", "ERX", "ERY", "GUSH", "DRIP", "BOIL", "KOLD",
    "UCO", "SCO", "AGQ", "ZSL", "UGL", "GLL", "QLD", "SSO", "SDS", "QID", "DOG",
    "SH", "PSQ", "RWM", "TWM", "SDOW", "UDOW",
}


def survey():
    """One pass over the cache: history, liquidity and the date set per symbol."""
    out = {}
    for f in sorted(glob.glob(str(DAILY / "*.json.gz"))):
        sym = os.path.basename(f).replace(".json.gz", "")
        if sym in BANNED:
            raise SystemExit(f"a leveraged/inverse ticker is in the cache: {sym}")
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            d = json.load(fh)
        if min(d) > START:
            continue
        dates, dv = [], []
        for k, b in d.items():
            if START <= k <= END:
                dates.append(k)
                dv.append(float(b["4. close"]) * float(b["5. volume"]))
        if not dates:
            continue
        out[sym] = (set(dates), float(np.median(dv)))
    return out


def write_fixture(path, syms, grid, splits):
    """Symbol-major, streaming one symbol at a time. Prices divided by the split
    factor and volumes multiplied -- D226's convention, `split_factor_at` reused."""
    with gzip.open(path, "wt", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["timestamp", "symbol", "open", "high", "low", "close", "volume"])
        for s in syms:
            with gzip.open(DAILY / f"{s}.json.gz", "rt", encoding="utf-8") as f:
                d = json.load(f)
            sp = splits.get(s, [])
            for k in grid:
                b = d[k]
                fac = H.split_factor_at(k, sp)
                w.writerow([
                    f"{k}T00:00:00", s,
                    f"{float(b['1. open']) / fac:.6f}", f"{float(b['2. high']) / fac:.6f}",
                    f"{float(b['3. low']) / fac:.6f}", f"{float(b['4. close']) / fac:.6f}",
                    f"{float(b['5. volume']) * fac:.1f}",
                ])


def build_cell(name, floor, info, actions):
    t0 = time.time()
    syms = sorted(s for s, (_, dv) in info.items() if dv >= floor)
    grid = sorted(set.intersection(*(info[s][0] for s in syms)))
    print(f"\n{name}: {len(syms)} symbols at >= ${floor:,.0f}/day, "
          f"raw grid {len(grid):,}", flush=True)

    fixture = FIX / f"universe_wide_{name.lower()}_raw.csv.gz"
    events = FIX / f"universe_wide_{name.lower()}_raw_events.json"
    saved = L.FIXTURE
    try:
        L.FIXTURE = fixture
        for it in range(1, 7):
            t1 = time.time()
            write_fixture(fixture, syms, grid, actions["splits"])
            cleaned, _ = L.clean(L.load_fixture_csv(fixture))
            keep = set.intersection(
                *(set(tb.timestamp.isoformat()[:10] for tb in cleaned[s]) for s in syms))
            nxt = [g for g in grid if g in keep]
            if not nxt:
                raise SystemExit(f"{name}: the cleaned intersection is empty")
            print(f"  pass {it}: {len(grid):,} -> {len(nxt):,} ({time.time() - t1:.0f}s)",
                  flush=True)
            if len(nxt) == len(grid):
                break
            grid = nxt
        else:  # pragma: no cover
            raise SystemExit(f"{name}: the cleaned grid did not converge")
        write_fixture(fixture, syms, grid, actions["splits"])
    finally:
        L.FIXTURE = saved

    events.write_text(json.dumps(
        {"dividends": {s: actions["dividends"].get(s, []) for s in syms},
         "splits": {s: actions["splits"].get(s, []) for s in syms}},
        indent=1, sort_keys=True), encoding="utf-8")

    n_div = sum(len(actions["dividends"].get(s, [])) for s in syms)
    n_spl = sum(len(actions["splits"].get(s, [])) for s in syms)
    print(f"  wrote {fixture.name}: {len(syms)} x {len(grid):,} bars "
          f"({grid[0]} .. {grid[-1]}), {n_div:,} dividends, {n_spl} splits "
          f"[{time.time() - t0:.0f}s]")
    return {"cell": name, "floor": floor, "symbols": syms, "n_symbols": len(syms),
            "bars": len(grid), "first": grid[0], "last": grid[-1],
            "dividends": n_div, "splits": n_spl}


def main() -> int:
    t0 = time.time()
    if not ACTIONS.exists():
        raise SystemExit(f"actions cache missing: {ACTIONS}")
    actions = json.loads(ACTIONS.read_text(encoding="utf-8"))
    print(f"actions cached for {len(actions['dividends']):,} symbols", flush=True)

    info = survey()
    print(f"{len(info):,} cached symbols with history back to {START}", flush=True)
    missing = [s for s in info if s not in actions["dividends"]]
    if missing:
        raise SystemExit(f"{len(missing)} symbols lack actions, e.g. {missing[:5]}")

    out = [build_cell(n, f, info, actions) for n, f in CELLS.items()]
    (REPO / "data" / "wide_universe_build.json").write_text(
        json.dumps({"start": START, "end": END, "cells": out,
                    "elapsed_seconds": round(time.time() - t0, 1)},
                   indent=1, sort_keys=True), encoding="utf-8")
    print(f"\ntotal {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
