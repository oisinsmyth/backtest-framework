"""One-time (manual, NETWORK) fetch of the broad crypto universe fixture (D140).

Same shape as every other fixture in this repo (D70/D88/D108): raw OHLCV + an events
sidecar + a meta sidecar, committed to git so the data is immutable-by-diff. Everything
downstream of this script is offline and deterministic.

## Why this fixture exists

`BREAKOUT_RESULTS.md` says, in its own caveats, that BTC and ETH are "the two crypto
assets that survived to be worth studying ... the single largest un-deflatable bias in
this document". A universe of today's twenty largest coins would be that same bias at
greater scale. So the candidate roster is built from **point-in-time prominence** — what
was large at the top of the 2017/18 mania and at the top of the 2021 mania — plus a
cohort of tokens sought out precisely **because they failed**: Terra/LUNA, TerraUSD,
FTX's FTT, Celsius's CEL, Serum, and the 2018 alt-coins that never came back.

**A ticker yfinance will not serve is recorded as a fetch failure in the meta, with the
attempt.** A documented "could not obtain" is evidence; a silent omission is the bias
itself.

## The selection policy (D140)

Stated before any of it was run, and applied mechanically by
`research.breakout_universe.apply_policy` — the same function the study re-applies to
the committed fixture, so a symbol that fails the screen cannot reach the engine:

0. **The screen runs on CLEANED bars** (D25's `clean`), not raw ones — the engine
   trades cleaned bars, so the screen must describe cleaned bars. What is *written* to
   the fixture is still the raw series (D6); cleaning happens again, identically, when
   the study freezes the fixture into a snapshot.
1. **All prices strictly positive.** Log returns and inverse-vol sizing are undefined
   otherwise. Applied after cleaning, so a symbol is not lost to a single bad print the
   cleaner's spike-and-revert rule already removes — only to a series that is genuinely
   part-zero.
2. **Peg screen: median absolute daily return >= 0.5%.** A pegged stablecoin never
   prints a 40-bar high, so a trend follower never trades it and its Sharpe is
   undefined rather than bad. See `UniversePolicy.min_median_abs_daily_return`, which
   also records that this clause was added after the policy's first run and why.
3. **Minimum history: 520 bars** — the shortest history that yields four walk-forward
   windows and a full year of out-of-sample data. See `UniversePolicy.min_bars` for
   why the mechanical floor (315) is not the chosen one.
4. **Liquidity floor: median daily volume >= 5,000,000 USD** over the symbol's own
   history. See `UniversePolicy.min_median_daily_volume_usd` for the derivation from
   the study's own capital.

Nothing in the screen touches a return, a Sharpe, a drawdown or a trade count. The
`survived` / `collapsed` / `delisted` labels in the meta are hindsight by construction
and are used only to SPLIT results after the fact, never to decide what is traded.

## Crypto-specific checks, inherited from D108

- Bars must all be stamped 00:00 (UTC midnight, stored naive). A symbol whose bars are
  not is excluded and said so.
- Spot crypto has no dividends and no splits, so the events sidecar is empty by
  construction. A symbol for which the provider returns either is excluded loudly
  rather than having its events silently dropped — an empty sidecar must not be a lie
  (D48).

Symbols are NOT inner-joined: each runs as its own single-instrument backtest (the N=1
case of D64), so no coin is truncated to another's inception by D45 alignment.

Run: uv run python scripts/fetch_crypto_universe.py
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import CorporateActions, save_events_json
from backtest_framework.data.csv_fixture import save_fixture_csv
from backtest_framework.data.yfinance_source import EquityDataSource
from backtest_framework.research.breakout_universe import DEFAULT_POLICY, align_volumes, apply_policy

# --------------------------------------------------------------- candidate roster
#
# THE HONEST STATEMENT ABOUT THIS LIST, up front and in the meta: it is assembled by
# hand, in 2026, from recollection of what was large at two past moments. It is NOT a
# reconstruction from an archived point-in-time index — no such archive is wired into
# this repo — and the study must not claim otherwise. What it IS is a roster built
# without conditioning on the outcome: two-thirds of it was chosen for what it was
# worth at a past date, and the last third was chosen *because* it failed. That is a
# materially different object from "the twenty largest coins today", and the
# survived-vs-collapsed split is what turns the difference into a measurement.

COHORTS: dict[str, tuple[str, ...]] = {
    "top30_at_2018_01": (
        # Roughly the top of the market-cap table at the peak of the first mania.
        # Includes the ones that died, which is the point.
        "BTC-USD", "ETH-USD", "XRP-USD", "BCH-USD", "ADA-USD", "LTC-USD", "XEM-USD",
        "XLM-USD", "MIOTA-USD", "DASH-USD", "XMR-USD", "TRX-USD", "ETC-USD", "NEO-USD",
        "EOS-USD", "QTUM-USD", "BTG-USD", "LSK-USD", "ZEC-USD", "OMG-USD", "STEEM-USD",
        "SC-USD", "DGB-USD", "WAVES-USD", "BTS-USD", "ZRX-USD", "DCR-USD", "BAT-USD",
        "ICX-USD",
    ),
    "prominent_at_2021_peak": (
        # Roughly the top of the market-cap table at the peak of the second mania,
        # plus the DeFi and metaverse tokens that were unavoidable that year.
        "BNB-USD", "DOGE-USD", "SOL-USD", "DOT-USD", "MATIC-USD", "LINK-USD", "UNI-USD",
        "AVAX-USD", "ATOM-USD", "ALGO-USD", "VET-USD", "FIL-USD", "ICP-USD", "THETA-USD",
        "XTZ-USD", "AAVE-USD", "CRO-USD", "SHIB-USD", "HBAR-USD", "EGLD-USD", "MKR-USD",
        "KSM-USD", "COMP-USD", "SNX-USD", "NEAR-USD", "GRT-USD", "MANA-USD", "SAND-USD",
        "AXS-USD", "CRV-USD", "SUSHI-USD", "YFI-USD", "APE-USD",
    ),
    "sought_failures": (
        # Chosen BECAUSE they failed, or because they are the surviving control for
        # something that failed. LUNA1/LUNC are the two tickers under which the
        # provider serves the original Terra; UST/USTC likewise for TerraUSD; LUNA is
        # the post-collapse Terra 2.0 listing. FTT is FTX's exchange token and OKB/LEO
        # are the exchange tokens that did not go to zero — the direct control.
        "LUNC-USD", "LUNA1-USD", "LUNA-USD", "USTC-USD", "UST-USD", "FTT-USD", "CEL-USD",
        "SRM-USD", "HT-USD", "OKB-USD", "LEO-USD", "BSV-USD", "SNT-USD", "REP-USD",
        "ONT-USD",
    ),
}

COHORT_BY_SYMBOL: dict[str, str] = {}
for _cohort, _symbols in COHORTS.items():
    for _symbol in _symbols:
        COHORT_BY_SYMBOL.setdefault(_symbol, _cohort)

SYMBOLS: tuple[str, ...] = tuple(COHORT_BY_SYMBOL)

START, END = date(2015, 1, 1), date(2025, 12, 31)
"""The same calendar range as the BTC/ETH fixture (D108), so the two studies' BTC and
ETH numbers are directly comparable rather than nearly comparable."""

OUT = (
    Path(__file__).resolve().parent.parent
    / "data" / "fixtures" / "crypto_universe_2015_2025_raw.csv.gz"
)


def main() -> int:
    source = EquityDataSource()
    fetched: dict[str, tuple] = {}
    failures: dict[str, str] = {}

    for symbol in SYMBOLS:
        for attempt in (1, 2):
            try:
                bars, volumes, dividends, splits = source.get_raw_history(symbol, START, END)
                if not bars:
                    failures[symbol] = "provider returned an empty series (delisted or unknown ticker)"
                    break
                hours = {tb.timestamp.hour for tb in bars}
                if hours != {0}:
                    failures[symbol] = f"bars not all stamped 00:00 — saw hours {sorted(hours)}"
                    break
                if dividends or splits:
                    # Loud rather than silently dropped: spot crypto having a corporate
                    # action means the provider frame is not what this fixture assumes,
                    # and the empty events sidecar would become a lie (D48/D108).
                    failures[symbol] = (
                        f"provider returned {len(dividends)} dividend(s) / {len(splits)} split(s) "
                        "for spot crypto — refusing to carry it under an empty events sidecar"
                    )
                    break
                fetched[symbol] = (bars, volumes)
                break
            except Exception as exc:  # noqa: BLE001 — report, never crash the batch
                if attempt == 2:
                    failures[symbol] = f"{type(exc).__name__}: {exc}"
                else:
                    time.sleep(2.0)
        time.sleep(0.5)  # politeness, as in scripts/fetch_universe.py

    if not fetched:
        print("ERROR: every symbol failed to fetch", file=sys.stderr)
        return 1

    bars_by_symbol = {s: v[0] for s, v in fetched.items()}
    volumes_by_symbol = {s: v[1] for s, v in fetched.items()}

    # Screen the CLEANED series (D25) — the engine trades cleaned bars, so a symbol
    # must not be excluded over a bad print the cleaner already drops. The fixture
    # itself still stores RAW bars (D6); the study re-cleans them identically.
    cleaned, cleaning_report = clean(bars_by_symbol, volumes_by_symbol)
    cleaned_volumes = {
        s: align_volumes(cleaned[s], bars_by_symbol[s], volumes_by_symbol[s]) for s in cleaned
    }
    selection = apply_policy(cleaned, cleaned_volumes, DEFAULT_POLICY, END)

    included_bars = {s: bars_by_symbol[s] for s in selection.included}
    included_volumes = {s: volumes_by_symbol[s] for s in selection.included}

    save_fixture_csv(OUT, included_bars, included_volumes)
    save_events_json(
        OUT.parent / "crypto_universe_2015_2025_raw_events.json",
        CorporateActions(
            dividends_by_symbol={s: [] for s in selection.included},
            splits_by_symbol={s: [] for s in selection.included},
        ),
    )

    meta = {
        "study": "breakout_universe_v1",
        "symbols_requested": list(SYMBOLS),
        "cohorts": {c: list(s) for c, s in COHORTS.items()},
        "cohort_by_symbol": COHORT_BY_SYMBOL,
        "roster_provenance": (
            "Hand-assembled in 2026 from recollection of the market-cap table at the 2017/18 "
            "and 2021 peaks, PLUS a cohort sought out because it failed. NOT reconstructed "
            "from an archived point-in-time index — no such archive is wired into this repo. "
            "Selection-time honesty (D140): the roster is hindsight-assembled, and the "
            "survived-vs-collapsed split is what makes the residual bias measurable rather "
            "than merely disclaimed."
        ),
        "symbols_included": list(selection.included),
        "symbols_excluded": dict(selection.excluded),
        "fetch_failures": failures,
        "status_by_symbol": dict(selection.status),
        "coverage": {s: c.to_dict() for s, c in selection.coverage.items()},
        "cleaning_at_screen_time": {
            "ruleset": cleaning_report.ruleset,
            "n_changes": len(cleaning_report.changes),
            "changes": [
                {"symbol": c.symbol, "timestamp": c.timestamp.isoformat(),
                 "rule": c.rule, "detail": c.detail}
                for c in cleaning_report.changes
            ],
        },
        "selection_policy": {
            **DEFAULT_POLICY.to_dict(),
            "description": (
                "Applied mechanically by research.breakout_universe.apply_policy, in order: "
                "(1) all prices strictly positive; (2) at least min_bars daily bars — the "
                "shortest history yielding four walk-forward windows and a full year out of "
                "sample; (3) median daily volume (provider units = USD notional for X-USD "
                "pairs) at or above the liquidity floor, derived from the study's own "
                "100,000 USD capital at 2% of a typical day. No return, Sharpe, drawdown or "
                "trade count enters the screen."
            ),
            "classification": (
                "delisted = last bar more than delisted_gap_days before the fixture end date; "
                "collapsed = final close at or below (1 - collapse_terminal_drawdown) of the "
                "symbol's own peak close; survived = neither. HINDSIGHT BY CONSTRUCTION, used "
                "only to split results after the fact."
            ),
        },
        "start": START.isoformat(),
        "end": END.isoformat(),
        "interval": "1d",
        "bar_boundary": "00:00 UTC, fixed (D108) — timestamps stored naive, meaning UTC midnight",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": (
            "yfinance Ticker.history(auto_adjust=False, actions=True); spot crypto has no "
            "dividends or splits, so the events sidecar is empty by construction (D108) and "
            "any symbol the provider returns one for is excluded rather than silently trimmed"
        ),
        "alignment_note": (
            "NOT inner-joined across symbols — every symbol runs as its own single-instrument "
            "backtest (the N=1 case of D64), so no coin is truncated to another's inception by "
            "D45 alignment"
        ),
    }
    (OUT.parent / "crypto_universe_2015_2025_raw.meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    print(
        f"requested {len(SYMBOLS)}, fetched {len(fetched)}, included {len(selection.included)}, "
        f"excluded {len(selection.excluded)}, fetch-failed {len(failures)}"
    )
    for symbol, reason in sorted(failures.items()):
        print(f"  FETCH FAILED {symbol}: {reason}")
    for symbol, reason in sorted(selection.excluded.items()):
        print(f"  EXCLUDED      {symbol}: {reason}")
    by_status: dict[str, list[str]] = {}
    for symbol in selection.included:
        by_status.setdefault(selection.status[symbol], []).append(symbol)
    for status, symbols in sorted(by_status.items()):
        print(f"  {status}: {len(symbols)} — {', '.join(sorted(symbols))}")
    volumes_median = statistics.median(
        selection.coverage[s].median_daily_volume for s in selection.included
    )
    print(f"median of per-symbol median daily volume: {volumes_median:,.0f} USD")
    print(f"wrote {OUT.name} ({OUT.stat().st_size / 1e6:.2f} MB) + events + meta")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
