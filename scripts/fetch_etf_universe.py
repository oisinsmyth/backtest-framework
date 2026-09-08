"""The wide ETF daily universe, fetched and GATED -- the prerequisite D382 is blocked on.

    uv run python scripts/fetch_etf_universe.py --pool        write the ETF pool from D245's cache listing (no requests)
    uv run python scripts/fetch_etf_universe.py --fetch       TIME_SERIES_DAILY_ADJUSTED for the pool (cached, resumable)
    uv run python scripts/fetch_etf_universe.py --select      the pinned pre-live screen, per symbol
    uv run python scripts/fetch_etf_universe.py --actions     derive splits/dividends from the cache (NO requests)
    uv run python scripts/fetch_etf_universe.py --build       split-adjust, run the gates, write fixture + events + meta

WHY THIS EXISTS. `ragged_panel.load_ragged` refuses a fixture whose meta does not assert its own gates passed, because D256 ran
against a build that had printed GATES FAILED and been left on disk -- it carried x300 and x66.7 fabricated single-bar returns. Every
ETF fixture in this repo predates that gate: `universe_wide_w1_raw.csv.gz` has NO meta at all, and `universe_daily_2015_2024`,
`universe_holdout_daily`, `etf_intraday_15m_raw` and `wide_extended_15m_raw` all carry a meta whose `gates` block is EMPTY. So there
is no gated ETF fixture, daily or intraday, and D382 cannot load one.

AND THE CACHED ETF DATA COULD NOT BE GATED AS IT STOOD. D245's 1,276 symbols are on disk under `data/raw/alphavantage/daily/` but were
fetched as TIME_SERIES_DAILY -- raw OHLCV, no adjusted close, no split coefficient, no dividend amount. gate_a is defined on confirmed
splits at their effective dates and simply cannot be evaluated against that, and neither can D333's dividend bound, which found thirty
fabricated return days in the single-name fixture and halved the incumbent book. Hence the re-fetch, authorised 2026-09-08.

THE GATES ARE IMPORTED, NOT COPIED. This module loads `fetch_short_universe.py` and re-points its module globals at ETF paths, so
`do_actions`, `do_build`, `apply_screen`, gate_a, gate_b, the split-confirmation test and the dividend bound are LITERALLY THE SAME
CODE OBJECTS the single-name fixture was built with -- not "the same by inspection". Nothing about the adjustment or gate logic is
re-implemented here, and the single-name paths are never written.

THE ONE CONTRACT CHANGE, AND IT IS DELIBERATE. `MIN_DEAD_SHARE = 0.15` refuses a single-name fixture that is materially all survivors,
because survivorship bias runs AGAINST a short book (D141-D144). A liquid ETF universe has no such cohort -- ETFs rarely delist -- and
a 15% floor would refuse every honest build of it. So the floor is set to ZERO and the dead share is REPORTED instead, prominently, in
the meta and on the console. Survivorship bias in a LONG-flat ETF book runs the other way and must be read as a caveat on the result,
not silently absorbed: `[DEAD]` prints it and the meta records `min_dead_share_enforced: 0.0` so no reader mistakes this fixture's
contract for the short universe's.

THE POOL IS D245's, NOT A NEW SELECTION. The symbol list is exactly the 1,276 tickers already cached by D245's wide-universe work, so
no new universe criterion is invented here and no listings request is made. The screen (252-bar warm-up, $3 median close, $1M median
dollar volume) is `apply_screen` unchanged.
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S = _load("fetch_short_universe", "fetch_short_universe.py")

LEGACY = REPO / "data" / "raw" / "alphavantage" / "daily"          # D245's TIME_SERIES_DAILY cache -- the symbol list only
CACHE = REPO / "data" / "raw" / "alphavantage" / "daily_adjusted_etf"
FIXTURE = REPO / "data" / "fixtures" / "etf_wide_daily_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "etf_wide_daily_raw_events.json"
META = REPO / "data" / "fixtures" / "etf_wide_daily_raw.meta.json"


def repoint() -> None:
    """Re-point the imported module at ETF paths. The single-name fixture's paths are never written by this script."""
    CACHE.mkdir(parents=True, exist_ok=True)
    S.CACHE = CACHE
    S.POOL = CACHE / "_pool.json"
    S.SELECTION = CACHE / "_selection.json"
    S.EVENTS_FULL = CACHE / "_events_full.json"
    S.FIXTURE, S.EVENTS, S.META = FIXTURE, EVENTS, META
    S.POOL_SIZE = 10_000                      # take the whole ETF pool; there is no holdout slice here
    S._HOLDOUT = S._HOLDOUT2 = False
    S.MIN_DEAD_SHARE = 0.0                    # see the module docstring: reported, not enforced
    assert S.FIXTURE != REPO / "data" / "fixtures" / "us_shorts_daily_raw.csv.gz", "[SAFE] refusing to write the single-name fixture"


def do_pool() -> None:
    """[POOL] the symbol list is D245's cached ETF universe, verbatim. No listings request, no new universe criterion.

    `cohort` is derived from each symbol's LAST CACHED BAR against the span end -- a symbol whose series stops early is dead. That is
    the same distinction the single-name pool carries; here it is read from the data rather than from a listings roster, because the
    legacy cache has no delisting dates.
    """
    syms = sorted({p.name.split(".")[0] for p in LEGACY.glob("*.json.gz")})
    assert syms, f"[POOL] no cached ETF symbols under {LEGACY}"
    order, alive, dead = [], 0, 0
    for s in syms:
        try:
            d = json.loads(gzip.open(LEGACY / f"{s}.json.gz", "rt").read())
            last = max(d) if d else None
        except Exception:
            last = None
        is_alive = bool(last and last >= "2026-06-01")
        alive, dead = alive + is_alive, dead + (not is_alive)
        order.append(dict(symbol=s, name=None, exchange=None, ipoDate=None,
                          delistingDate=None if is_alive else last, cohort="alive" if is_alive else "dead"))
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "_pool.json").write_text(json.dumps(
        dict(order=order, seed=None, pool_size=len(order),
             counts=dict(alive=alive, dead=dead),
             source="D245's cached wide ETF universe (data/raw/alphavantage/daily), verbatim -- no listings request",
             note="cohort derived from the last cached bar; the legacy cache carries no delisting dates"), indent=1))
    print(f"[POOL] {len(order):,} ETF symbols from D245's cache -- {alive:,} alive, {dead:,} dead ({dead / len(order):.1%})")
    print(f"       wrote {CACHE / '_pool.json'}")


def report_dead(tag: str) -> None:
    """[DEAD] the contract change, printed every time so it cannot be missed."""
    p = CACHE / "_selection.json"
    if not p.exists():
        return
    sel = json.loads(p.read_text())["selected"]
    n = sum(1 for r in sel if r.get("cohort") == "dead")
    print(f"  [DEAD] {tag}: {n:,} of {len(sel):,} selected symbols are dead ({n / max(len(sel), 1):.1%}). "
          f"MIN_DEAD_SHARE is 0.0 here, NOT the single-name fixture's 0.15 -- survivorship bias in a LONG-flat "
          f"ETF book runs in your favour and is a caveat on every result, not a build failure.")


def main() -> int:
    ap = argparse.ArgumentParser()
    for f in ("pool", "fetch", "select", "actions", "build"):
        ap.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    print("ETF wide daily universe -- fetched and GATED (D382 prerequisite)")
    repoint()
    t0 = time.time()
    if a.pool:
        do_pool()
    elif a.fetch:
        key = S.api_key()
        S.do_fetch(key, S.RateLimiter(S.MIN_INTERVAL), a.limit)
    elif a.select:
        S.do_select(a.limit)
        report_dead("after --select")
    elif a.actions:
        S.do_actions()
    elif a.build:
        report_dead("before --build")
        S.do_build()
        m = json.loads(META.read_text())
        real = [k for k, v in m.get("gates", {}).items() if isinstance(v, dict) and "failures" in v]
        print(f"\n  [GATE] the built meta declares gates {real} -- ragged_panel.load_ragged will accept it: "
              f"{'YES' if real else 'NO'}")
        report_dead("after --build")
    else:
        ap.error("one of --pool, --fetch, --select, --actions, --build")
    print(f"  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
