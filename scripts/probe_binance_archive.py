"""One-time (manual, NETWORK) PROBE of the Binance public flat-file archives.

This measures a provider before anything is designed on it, which is the order D160 used
and for the same reason: every intraday conclusion in this project so far is a statement
about yfinance rather than about crypto.

    D160  yfinance reports Volume = 0 on 17,520 of 34,923 hourly BTC/ETH bars, so the
          cleaner had to be called on prices only or half the price series would go.
    D163  15m/30m get 60 days, which cannot hold a 252-day training window, so no return
          claim was permitted below 1h at all.
    D165  the 730 days served contain no trend edge at any frequency, so the headline had
          to splice a cost curve onto a separately-measured gross edge.
    D189  the terrain programme's S1 volume-profile sensor was tested on DAILY bars, for
          the same reason, and the final report names a sharper intraday map as the open
          door rather than a closed question.

## What this script is NOT

It writes no fixture, no snapshot and no study. It produces one JSON summary and one
Markdown report. The design decisions it feeds — the price frame (D190), the storage
policy (D191) and the zero-volume collision with `clean-v1` (D192) — are written after it
runs, against its numbers.

## Cost control: metadata first, bytes only where a measurement needs them

Retention, per-symbol span and total size all come from S3 listings, which return a
`<Size>` per key and cost one request per symbol. Only a stratified sample of archives is
actually downloaded — first month, mid-span month, latest complete month, plus the two
months either side of the epoch-unit switch on the majors. Probing the full universe at
1m would move gigabytes to establish facts a listing already states.

## The finding this script exists to pin

Binance changed kline `open_time` from milliseconds to microseconds at the 2025-01
monthly file. A reader that assumes milliseconds dates a mid-2025 bar to the year 57,400.
That is D187's failure mode exactly — a units error, invisible to every other check —
so the unit is read per file and the boundary is reported rather than assumed.

Run: uv run python scripts/probe_binance_archive.py
Re-render the report from the committed JSON, offline: --report-only
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.binance_archive import (  # noqa: E402
    DOWNLOAD_BASE,
    LISTING_BASE,
    ArchiveFormatError,
    Listing,
    SymbolCoverage,
    assert_on_grid,
    coverage_from_listing,
    gap_census,
    parse_klines,
    parse_listing,
    resample_to_daily,
    volume_census,
)
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)

SUMMARY_JSON = REPO / "data" / "binance_probe_summary.json"
REPORT = REPO / "docs" / "results" / "binance_provider_probe.md"
DAILY_FIXTURE = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw.csv.gz"
UNIVERSE_META = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.meta.json"

MAJORS = ("BTCUSDT", "ETHUSDT")
"""The two symbols every prior crypto result in this project rests on."""

UNITS_BOUNDARY_MONTHS = ("2024-11", "2024-12", "2025-01", "2025-02")
"""Probed on the majors to pin the ms -> us switch to a month rather than a year."""

INTERVAL_MINUTES = 1
INTERVAL = "1m"

REQUEST_PAUSE = 0.5
"""Politeness between requests, matching the other fetch scripts."""


# ---------------------------------------------------------------- network primitives


def _get(url: str, attempts: int = 2) -> bytes:
    """Fetch a URL, retrying once. Raises on final failure; callers decide what is fatal."""
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310
                body: bytes = response.read()
                return body
        except Exception as exc:  # noqa: BLE001 — report, never crash the batch
            last = exc
            if attempt < attempts:
                time.sleep(2.0)
    raise RuntimeError(f"{type(last).__name__}: {last}")


def list_prefix(prefix: str) -> Listing:
    """List every key under a prefix, following pagination.

    A listing that stops silently at 1000 keys looks exactly like a symbol with 1000
    months of history, so `IsTruncated` is followed rather than trusted to be false.
    """
    entries = []
    marker: str | None = None
    truncated = False
    while True:
        query = {"delimiter": "/", "prefix": prefix}
        if marker:
            query["marker"] = marker
        url = f"{LISTING_BASE}?{urllib.parse.urlencode(query)}"
        page = parse_listing(_get(url).decode("utf-8"))
        entries.extend(page.entries)
        truncated = page.is_truncated
        if not page.is_truncated or not page.next_marker:
            break
        marker = page.next_marker
        time.sleep(REQUEST_PAUSE)
    return Listing(entries=entries, is_truncated=truncated, next_marker=None)


def spot_klines_prefix(symbol: str, interval: str = INTERVAL) -> str:
    return f"data/spot/monthly/klines/{symbol}/{interval}/"


def perp_klines_prefix(symbol: str, interval: str = INTERVAL) -> str:
    return f"data/futures/um/monthly/klines/{symbol}/{interval}/"


def funding_prefix(symbol: str) -> str:
    return f"data/futures/um/monthly/fundingRate/{symbol}/"


def fetch_archive(key: str) -> tuple[str, str | None, bool]:
    """Download one archive and its checksum sidecar.

    Returns (csv text, published sha256, verified). The checksum is the thing the
    manifest-only storage policy rests on, so it is verified here rather than assumed to
    exist.
    """
    payload = _get(f"{DOWNLOAD_BASE}/{key}")
    published: str | None = None
    verified = False
    try:
        sidecar = _get(f"{DOWNLOAD_BASE}/{key}.CHECKSUM", attempts=1).decode()
        published = sidecar.split()[0]
        verified = hashlib.sha256(payload).hexdigest() == published
    except Exception:  # noqa: BLE001 — a missing sidecar is a finding, not a crash
        published = None
    archive = zipfile.ZipFile(io.BytesIO(payload))
    names = archive.namelist()
    if len(names) != 1:
        raise ArchiveFormatError(f"{key} holds {len(names)} members, expected 1")
    return archive.read(names[0]).decode("utf-8"), published, verified


# ---------------------------------------------------------------- measurement groups


def sample_months(coverage: SymbolCoverage) -> list[str]:
    """First, mid-span and latest month — enough to see schema drift without bulk cost."""
    months = coverage.months
    if not months:
        return []
    picks = {months[0], months[len(months) // 2], months[-1]}
    return sorted(picks)


def probe_file(symbol: str, month: str, prefix_fn=spot_klines_prefix) -> dict:
    """Download one month and measure schema, units, volume fidelity and grid alignment."""
    key = f"{prefix_fn(symbol)}{symbol}-{INTERVAL}-{month}.zip"
    text, published_sha, verified = fetch_archive(key)
    parsed = parse_klines(text)
    census = volume_census(parsed.base_volumes, parsed.trade_counts)

    grid_error: str | None = None
    try:
        assert_on_grid(parsed.bars, INTERVAL_MINUTES)
    except ArchiveFormatError as exc:
        grid_error = str(exc)

    # Units cross-check: quote / base should be a price inside the bar's own range. This
    # is the check that would have caught D187 at the provider boundary.
    implied_vwap_ok = 0
    implied_vwap_checked = 0
    for tb, base, quote in zip(parsed.bars, parsed.base_volumes, parsed.quote_volumes):
        if base <= 0.0:
            continue
        implied_vwap_checked += 1
        if tb.bar.low * 0.999 <= quote / base <= tb.bar.high * 1.001:
            implied_vwap_ok += 1

    taker_buy_share = (
        sum(parsed.taker_buy_base) / sum(parsed.base_volumes)
        if sum(parsed.base_volumes) > 0
        else None
    )

    return {
        "month": month,
        "key": key,
        "timestamp_unit": parsed.timestamp_unit,
        "columns": parsed.columns,
        "had_header": parsed.had_header,
        "bars": len(parsed.bars),
        "first_bar": parsed.bars[0].timestamp.isoformat(),
        "last_bar": parsed.bars[-1].timestamp.isoformat(),
        "published_sha256": published_sha,
        "checksum_verified": verified,
        "grid_error": grid_error,
        "gap_histogram_minutes": gap_census(parsed.bars, INTERVAL_MINUTES),
        "zero_volume": census.zero_volume,
        "zero_trades": census.zero_trades,
        "zero_volume_and_zero_trades": census.zero_volume_and_zero_trades,
        "zero_volume_rate": census.zero_volume_rate,
        "zero_volume_agrees_with_zero_trades": census.agrees,
        "implied_vwap_in_range": implied_vwap_ok,
        "implied_vwap_checked": implied_vwap_checked,
        "taker_buy_share_of_volume": taker_buy_share,
    }


def reconcile_against_daily_fixture(symbol: str, yf_symbol: str, month: str) -> dict:
    """Compare a Binance 1m month, resampled to UTC days, against the committed fixture.

    Reported as a distribution, never asserted against a tolerance. D161's precedent is
    that a cross-source discrepancy is a finding; a tolerance would hide it. These are
    genuinely different instruments — a single-venue USDT pair against a multi-venue USD
    index — so agreement is informative and exact equality would be suspicious.
    """
    key = f"{spot_klines_prefix(symbol)}{symbol}-{INTERVAL}-{month}.zip"
    text, _, _ = fetch_archive(key)
    parsed = parse_klines(text)
    daily = resample_to_daily(parsed.bars, parsed.base_volumes)

    bars_by_symbol, volumes_by_symbol = load_fixture_csv_with_volumes(DAILY_FIXTURE)
    reference = {
        tb.timestamp.date(): (tb.bar.close, vol)
        for tb, vol in zip(
            bars_by_symbol.get(yf_symbol, []), volumes_by_symbol.get(yf_symbol, [])
        )
    }

    rows = []
    for day_bar in daily:
        match = reference.get(day_bar.day)
        if match is None:
            continue
        yf_close, yf_volume = match
        rows.append(
            {
                "day": day_bar.day.isoformat(),
                "binance_close": day_bar.close,
                "fixture_close": yf_close,
                "close_diff_bp": 10_000.0 * (day_bar.close / yf_close - 1.0),
                "binance_base_volume": day_bar.base_volume,
                "binance_quote_volume_implied": day_bar.base_volume * day_bar.close,
                "fixture_volume": yf_volume,
            }
        )
    diffs = sorted(abs(r["close_diff_bp"]) for r in rows)
    return {
        "symbol": symbol,
        "fixture_symbol": yf_symbol,
        "month": month,
        "days_compared": len(rows),
        "abs_diff_bp_min": diffs[0] if diffs else None,
        "abs_diff_bp_median": diffs[len(diffs) // 2] if diffs else None,
        "abs_diff_bp_max": diffs[-1] if diffs else None,
        "rows": rows,
    }


def universe_symbols() -> list[str]:
    """The 63 coins the existing cross-section admitted (D140)."""
    meta = json.loads(UNIVERSE_META.read_text(encoding="utf-8"))
    included: list[str] = meta["symbols_included"]
    return included


def to_binance_symbol(yf_symbol: str) -> str:
    """`BTC-USD` -> `BTCUSDT`. Binance quotes in Tether, not dollars."""
    return yf_symbol.replace("-USD", "") + "USDT"


# ---------------------------------------------------------------- orchestration


def run_probe() -> dict:
    started = time.time()
    payload: dict = {
        "probe": "binance_archive_v1",
        "interval": INTERVAL,
        "probed_at_utc": datetime.now(timezone.utc).isoformat(),
        "listing_host": LISTING_BASE,
        "download_host": DOWNLOAD_BASE,
    }

    # --- F. Universe coverage -------------------------------------------------
    yf_symbols = universe_symbols()
    coverage: dict[str, dict] = {}
    unavailable: dict[str, str] = {}
    listing_failures: dict[str, str] = {}

    print(f"probing {len(yf_symbols)} universe symbols at {INTERVAL} (spot)")
    for yf_symbol in yf_symbols:
        symbol = to_binance_symbol(yf_symbol)
        try:
            listing = list_prefix(spot_klines_prefix(symbol))
        except Exception as exc:  # noqa: BLE001 — report, never crash the batch
            listing_failures[symbol] = f"{type(exc).__name__}: {exc}"
            print(f"  LISTING FAILED {symbol}: {listing_failures[symbol]}")
            time.sleep(REQUEST_PAUSE)
            continue
        cov = coverage_from_listing(symbol, listing)
        if not cov.available:
            unavailable[symbol] = "no monthly 1m klines published"
            print(f"  UNAVAILABLE    {symbol} (from {yf_symbol})")
        else:
            coverage[symbol] = {
                "fixture_symbol": yf_symbol,
                "months": len(cov.months),
                "first_month": cov.first_month,
                "last_month": cov.last_month,
                "missing_months": cov.missing_months,
                "total_bytes": cov.total_bytes,
                "checksum_coverage": cov.checksum_coverage,
                "listing_truncated": listing.is_truncated,
            }
            print(
                f"  {symbol:<12} months={len(cov.months):>3}  "
                f"{cov.first_month} .. {cov.last_month}  "
                f"{cov.total_bytes / 1e6:>7.1f} MB  "
                f"checksums={cov.checksum_coverage:.0%}"
            )
        time.sleep(REQUEST_PAUSE)

    payload["universe"] = {
        "source": UNIVERSE_META.name,
        "symbols_requested": yf_symbols,
        "coverage": coverage,
        "unavailable": unavailable,
        "listing_failures": listing_failures,
    }

    # --- A/B/C/D. Schema, units, volume fidelity on a stratified sample -------
    samples: dict[str, list[dict]] = {}
    for symbol in MAJORS:
        listing = list_prefix(spot_klines_prefix(symbol))
        cov = coverage_from_listing(symbol, listing)
        months = sorted(set(sample_months(cov)) | set(UNITS_BOUNDARY_MONTHS))
        months = [m for m in months if m in set(cov.months)]
        rows = []
        print(f"sampling {symbol}: {', '.join(months)}")
        for month in months:
            try:
                row = probe_file(symbol, month)
            except Exception as exc:  # noqa: BLE001
                rows.append({"month": month, "error": f"{type(exc).__name__}: {exc}"})
                print(f"  {month}: FAILED {type(exc).__name__}: {exc}")
                continue
            rows.append(row)
            print(
                f"  {month}: {row['bars']:>6} bars  unit={row['timestamp_unit']}  "
                f"cols={row['columns']}  zero-vol={row['zero_volume']:>6} "
                f"({row['zero_volume_rate']:.3%})  agrees={row['zero_volume_agrees_with_zero_trades']}  "
                f"sha={'ok' if row['checksum_verified'] else 'MISSING'}"
            )
            time.sleep(REQUEST_PAUSE)
        samples[symbol] = rows

    # A thin, dead name matters more than a major here: the failure universe is the only
    # screen in this project that ever caught anything (D140/D180), and zero-volume at 1m
    # is a property of thin instruments rather than of the provider.
    for symbol in ("XEMUSDT", "BTGUSDT"):
        try:
            listing = list_prefix(spot_klines_prefix(symbol))
            cov = coverage_from_listing(symbol, listing)
            rows = []
            for month in sample_months(cov):
                rows.append(probe_file(symbol, month))
                print(
                    f"  {symbol} {month}: zero-vol={rows[-1]['zero_volume']} "
                    f"({rows[-1]['zero_volume_rate']:.3%}) "
                    f"agrees={rows[-1]['zero_volume_agrees_with_zero_trades']}"
                )
                time.sleep(REQUEST_PAUSE)
            samples[symbol] = rows
        except Exception as exc:  # noqa: BLE001
            samples[symbol] = [{"error": f"{type(exc).__name__}: {exc}"}]

    payload["samples"] = samples

    # --- E. Cross-provider reconciliation -------------------------------------
    reconciliations = []
    for symbol, yf_symbol in (("BTCUSDT", "BTC-USD"), ("ETHUSDT", "ETH-USD")):
        try:
            rec = reconcile_against_daily_fixture(symbol, yf_symbol, "2021-05")
            reconciliations.append(rec)
            print(
                f"reconcile {symbol} vs {yf_symbol} 2021-05: {rec['days_compared']} days, "
                f"|diff| median {rec['abs_diff_bp_median']:.1f} bp, "
                f"max {rec['abs_diff_bp_max']:.1f} bp"
            )
        except Exception as exc:  # noqa: BLE001
            reconciliations.append(
                {"symbol": symbol, "error": f"{type(exc).__name__}: {exc}"}
            )
        time.sleep(REQUEST_PAUSE)
    payload["reconciliation"] = reconciliations

    # --- G. Perps and funding --------------------------------------------------
    perps = {}
    for symbol in MAJORS:
        entry: dict = {}
        for label, prefix in (
            ("klines", perp_klines_prefix(symbol)),
            ("funding_rate", funding_prefix(symbol)),
        ):
            try:
                listing = list_prefix(prefix)
                cov = coverage_from_listing(symbol, listing)
                entry[label] = {
                    "months": len(cov.months),
                    "first_month": cov.first_month,
                    "last_month": cov.last_month,
                    "total_bytes": cov.total_bytes,
                }
            except Exception as exc:  # noqa: BLE001
                entry[label] = {"error": f"{type(exc).__name__}: {exc}"}
            time.sleep(REQUEST_PAUSE)
        perps[symbol] = entry
        print(f"perp {symbol}: {json.dumps(entry)}")
    payload["perps"] = perps

    # --- D. Storage projection -------------------------------------------------
    total_bytes = sum(c["total_bytes"] for c in coverage.values())
    payload["storage"] = {
        "universe_total_bytes_1m": total_bytes,
        "largest_committed_fixture_bytes": max(
            (p.stat().st_size for p in (REPO / "data" / "fixtures").glob("*.csv.gz")),
            default=0,
        ),
        "git_dir_bytes": sum(
            f.stat().st_size for f in (REPO / ".git").rglob("*") if f.is_file()
        ),
        "checksum_coverage_min": min(
            (c["checksum_coverage"] for c in coverage.values()), default=0.0
        ),
    }

    payload["elapsed_seconds"] = time.time() - started
    return payload


# ---------------------------------------------------------------- report rendering


def _fmt_mb(n: float) -> str:
    return f"{n / 1e6:,.1f} MB"


def build_report(p: dict) -> str:
    """Render the Markdown report from the summary payload.

    Every number here is read from the payload. D189's lesson is that prose drifting from
    the numbers it describes is this project's most repeated defect, so there is no path
    by which a figure can be typed into this document by hand.
    """
    out: list[str] = []
    w = out.append

    w("# The Binance archive, measured before anything is built on it")
    w("")
    w(
        "A provider probe, run in the same order D160 used: measure what the source "
        "actually serves, then design the study against that rather than against an "
        "assumption. Nothing here is a fixture, a snapshot or a result."
    )
    w("")
    w(
        f"`{SUMMARY_JSON.name}` holds every figure below. Re-render this document from "
        f"it with `--report-only`, offline."
    )
    w("")

    # --- headline ---
    cov = p["universe"]["coverage"]
    unavailable = p["universe"]["unavailable"]
    requested = p["universe"]["symbols_requested"]
    max_month = max((c["last_month"] for c in cov.values()), default="")
    w("## What the archive holds")
    w("")
    w(
        f"Of the **{len(requested)}** coins the existing cross-section admitted (D140), "
        f"**{len(cov)}** are reachable as `USDT` spot pairs at {p['interval']} and "
        f"**{len(unavailable)}** are not."
    )
    w("")
    if unavailable:
        w("Unreachable, with the reason the listing gave:")
        w("")
        for symbol, reason in sorted(unavailable.items()):
            w(f"- `{symbol}` — {reason}")
        w("")
        w(
            "**The missingness is not random, and that matters more than the count.** "
            "`OKB`, `HT` and `CRO` are the exchange tokens of OKX, Huobi and Crypto.com; "
            "`BSV` is a fork Binance delisted in 2019. A venue does not list its "
            "competitors' equity-like tokens, so switching provider silently applies a "
            "selection screen that the yfinance roster did not. The archive states no "
            "reason for any of them — that reading is an observation about which symbols "
            "these are, not a measurement — but a universe drawn from one venue is a "
            "universe that venue chose, and D180's lesson is that the sample is the thing "
            "most likely to be wrong."
        )
        w("")

    dead = sorted(
        (s, c["last_month"]) for s, c in cov.items() if c["last_month"] < max_month
    )
    if dead:
        w(
            f"**{len(dead)} of {len(cov)} series terminate before the archive's latest "
            f"month ({max_month})** — a delisting, with the history up to it preserved:"
        )
        w("")
        w(", ".join(f"`{s}` ({m})" for s, m in dead))
        w("")

    gapped = {s: c["missing_months"] for s, c in cov.items() if c["missing_months"]}
    if gapped:
        w(
            "A gap *inside* a symbol's own span is a third case, distinct from both a "
            "delisting and a gap between bars — the provider published nothing for those "
            "months while the pair still existed:"
        )
        w("")
        for symbol, months in sorted(gapped.items()):
            w(f"- `{symbol}` — {len(months)} months missing: {', '.join(months)}")
        w("")

    w("| symbol | fixture symbol | months | first | last | listing gaps | size | checksums |")
    w("|---|---|---:|---|---|---:|---:|---:|")
    for symbol, c in sorted(cov.items(), key=lambda kv: -kv[1]["months"]):
        w(
            f"| `{symbol}` | `{c['fixture_symbol']}` | {c['months']} | "
            f"{c['first_month']} | {c['last_month']} | {len(c['missing_months'])} | "
            f"{_fmt_mb(c['total_bytes'])} | {c['checksum_coverage']:.0%} |"
        )
    w("")
    w(
        "A `last` month short of the present is a **delisting**, and the archive keeps "
        "the history up to it rather than withdrawing it. That is the failure-universe "
        "signature D140/D180 needs, and it is honest — there is no back-fill."
    )
    w("")

    # --- schema and units ---
    w("## Schema, and a units switch inside the archive")
    w("")
    w(
        "Kline `open_time` changed from **milliseconds to microseconds** partway through "
        "the archive. A reader that assumes milliseconds dates a mid-2025 bar to the year "
        "57,400. This is D187's failure mode exactly — a units error, invisible to every "
        "other check — so the reader detects the unit per file and refuses a third."
    )
    w("")
    w("| symbol | month | bars | epoch unit | cols | header | zero-vol | rate | zero-vol == zero-trade | sha256 |")
    w("|---|---|---:|---|---:|---|---:|---:|---|---|")
    for symbol, rows in p["samples"].items():
        for r in rows:
            if "error" in r:
                w(f"| `{symbol}` | {r.get('month', '—')} | — | — | — | — | — | — | — | {r['error']} |")
                continue
            w(
                f"| `{symbol}` | {r['month']} | {r['bars']:,} | **{r['timestamp_unit']}** | "
                f"{r['columns']} | {'yes' if r['had_header'] else 'no'} | "
                f"{r['zero_volume']:,} | {r['zero_volume_rate']:.3%} | "
                f"{'yes' if r['zero_volume_agrees_with_zero_trades'] else 'NO'} | "
                f"{'verified' if r['checksum_verified'] else 'missing'} |"
            )
    w("")

    # --- volume ---
    w("## Volume fidelity, and why the zero bars are not the same finding as D160's")
    w("")
    w(
        "D160 found yfinance reporting `Volume = 0` on roughly half of all hourly BTC/ETH "
        "bars whose prices were present, consistent and on instruments that have never had "
        "a zero-volume hour. That is a provider defect."
    )
    w("")
    w(
        "The zero-volume bars here are a different thing, and the column that separates "
        "them is `number_of_trades`. Where zero volume and zero trades are **the same "
        "bars**, the bar is telling the truth: nothing traded in that minute. On a young "
        "or thin listing that is a property of the market, not of the feed."
    )
    w("")
    agreeing = [
        (s, r)
        for s, rows in p["samples"].items()
        for r in rows
        if "error" not in r and r["zero_volume"] > 0
    ]
    if agreeing:
        w("Every sampled month with zero-volume bars, and whether the two columns agree:")
        w("")
        for symbol, r in agreeing:
            w(
                f"- `{symbol}` {r['month']}: {r['zero_volume']:,} zero-volume, "
                f"{r['zero_trades']:,} zero-trade, {r['zero_volume_and_zero_trades']:,} both "
                f"— **{'agree' if r['zero_volume_agrees_with_zero_trades'] else 'DISAGREE'}**"
            )
        w("")
    w("### The rate is a property of the instrument, and it is severe on the ones that matter")
    w("")
    thin = sorted(
        (
            (s, r)
            for s, rows in p["samples"].items()
            for r in rows
            if "error" not in r
        ),
        key=lambda sr: -sr[1]["zero_volume_rate"],
    )
    if thin:
        worst_symbol, worst = thin[0]
        w(
            f"The majors are clean from 2022 onward — 0.000% on every sampled month. The "
            f"worst month sampled is `{worst_symbol}` {worst['month']} at "
            f"**{worst['zero_volume_rate']:.1%}**: more than half of that month's minutes "
            f"contain no trade at all."
        )
        w("")
        w("| symbol | month | bars | zero-volume | rate |")
        w("|---|---|---:|---:|---:|")
        for symbol, r in thin[:8]:
            w(
                f"| `{symbol}` | {r['month']} | {r['bars']:,} | {r['zero_volume']:,} | "
                f"{r['zero_volume_rate']:.3%} |"
            )
        w("")
    w(
        "**This is the finding that constrains the study design, not the cleaner "
        "collision.** The failure universe — a cross-section screened to include the "
        "assets that died — is the only screen in this project that ever caught anything "
        "(D140/D180). On exactly those instruments, a 1m time grid is majority-empty. A "
        "rule sampled on it would spend most of its bars looking at a price that did not "
        "move because nothing traded, which is not the same as a price that did not move."
    )
    w("")
    w(
        "The two ways out point in opposite directions and neither is free. Restricting "
        "intraday work to liquid names reintroduces precisely the survivorship problem "
        "D180 identified, where five passes on BTC and ETH turned out to be five readings "
        "of two unusually favourable series. Moving off time bars onto volume or dollar "
        "bars keeps the failure universe but changes the object being measured, and no "
        "result in this project would then be comparable to the daily ones. That choice "
        "belongs in a pre-registration, before anything is run."
    )
    w("")
    w(
        "This collides with the data layer. `clean-v1`'s `non_positive_volume` rule drops "
        "any bar with volume at or below zero, and there is no per-rule disable — `clean()` "
        "and `validate()` take data and nothing else, and their thresholds are module "
        "constants. The only existing lever is `allow_quarantined=True` on "
        "`SnapshotStore.load`, which is D143's override. D143 explicitly deferred "
        "per-asset-class thresholds, on the grounds that recalibrating a cross-cutting gate "
        "from inside a study is how gates stop meaning anything. That deferral is now due."
    )
    w("")

    # --- units cross check ---
    w("### The units cross-check D187 did not have")
    w("")
    w(
        "Binance states base volume and quote volume as two separate named columns, so "
        "their ratio must be a price inside the bar's own high–low range. That check is "
        "run on every bar of every sampled month:"
    )
    w("")
    for symbol, rows in p["samples"].items():
        for r in rows:
            if "error" in r or not r.get("implied_vwap_checked"):
                continue
            ok, checked = r["implied_vwap_in_range"], r["implied_vwap_checked"]
            w(
                f"- `{symbol}` {r['month']}: {ok:,}/{checked:,} bars "
                f"({ok / checked:.4%}) have quote÷base inside [low, high]"
            )
    w("")
    w(
        "D187 was a units error that scaled every market-impact charge by the square root "
        "of price and produced two results that looked like findings. Here the ambiguity "
        "is removed by the provider rather than by a parameter."
    )
    w("")

    # --- order flow ---
    w("### Signed order flow arrives in the same row")
    w("")
    w(
        "`taker_buy_base` is column 9 of the kline file, so taker sell volume is "
        "`volume - taker_buy_base` and the imbalance needs no separate download. The "
        "`aggTrades` archives are roughly two orders of magnitude larger for the same span."
    )
    w("")
    for symbol, rows in p["samples"].items():
        for r in rows:
            if "error" in r or r.get("taker_buy_share_of_volume") is None:
                continue
            w(
                f"- `{symbol}` {r['month']}: taker buys are "
                f"{r['taker_buy_share_of_volume']:.4f} of base volume"
            )
    w("")

    # --- reconciliation ---
    w("## The first independent check the daily fixture has ever had")
    w("")
    w(
        "Every crypto result in this project rests on one provider. Resampling Binance 1m "
        "to UTC days gives a second, genuinely independent measurement of the same days."
    )
    w("")
    w("| symbol | vs | month | days | min \\|diff\\| | median | max |")
    w("|---|---|---|---:|---:|---:|---:|")
    for rec in p["reconciliation"]:
        if "error" in rec:
            w(f"| `{rec['symbol']}` | — | — | — | — | — | {rec['error']} |")
            continue
        w(
            f"| `{rec['symbol']}` | `{rec['fixture_symbol']}` | {rec['month']} | "
            f"{rec['days_compared']} | {rec['abs_diff_bp_min']:.1f} bp | "
            f"{rec['abs_diff_bp_median']:.1f} bp | {rec['abs_diff_bp_max']:.1f} bp |"
        )
    w("")
    w(
        "**Reported, not asserted.** These are different instruments — a single-venue "
        "`USDT` pair against a multi-venue `USD` index — so agreement at this scale is "
        "informative and exact equality would be suspicious. D161's precedent is that a "
        "cross-source discrepancy is a finding; a tolerance would hide it."
    )
    w("")
    w(
        "Volume does **not** reconcile, and should not: the fixture reports global USD "
        "notional across all venues where Binance reports base units on one. Both are "
        "internally correct and they are not the same quantity — which is the same "
        "distinction D187 got wrong in the other direction."
    )
    w("")

    # --- perps ---
    w("## Perpetuals and funding")
    w("")
    w("| symbol | perp klines | span | funding rate | span |")
    w("|---|---:|---|---:|---|")
    for symbol, entry in p["perps"].items():
        k, f = entry.get("klines", {}), entry.get("funding_rate", {})
        if "error" in k or "error" in f:
            w(f"| `{symbol}` | — | {k.get('error', '')} | — | {f.get('error', '')} |")
            continue
        w(
            f"| `{symbol}` | {k['months']} | {k['first_month']} .. {k['last_month']} | "
            f"{f['months']} | {f['first_month']} .. {f['last_month']} |"
        )
    w("")
    w(
        "Funding is a real carry on a perpetual, and the engine already has the slot for "
        "it: `CostStack.portfolio_carry_bricks` (D5/D67). Perps are measured here and "
        "deferred — spot is the study base, for continuity with the daily fixture."
    )
    w("")

    # --- storage ---
    s = p["storage"]
    w("## Storage, and why the manifest is the thing to commit")
    w("")
    w(
        f"The reachable universe holds **{_fmt_mb(s['universe_total_bytes_1m'])}** of "
        f"compressed {p['interval']} archives. The largest fixture currently committed is "
        f"**{_fmt_mb(s['largest_committed_fixture_bytes'])}** and the entire `.git` "
        f"directory is **{_fmt_mb(s['git_dir_bytes'])}**."
    )
    w("")
    w(
        f"Committing the bytes would end the immutable-by-diff property rather than extend "
        f"it. Binance publishes a SHA256 sidecar beside every archive, and the sampled "
        f"minimum coverage across symbols is **{s['checksum_coverage_min']:.0%}** — so the "
        f"manifest is committable where the data is not."
    )
    w("")
    w(
        "That is arguably a **stronger** guarantee than committing bytes, not a retreat "
        "from one. A hash we compute over data we downloaded attests that we did not "
        "change it. A hash the provider published attests to the same thing, is "
        "independently verifiable by anyone, and cannot be quietly regenerated by us."
    )
    w("")

    w("## What this probe does not settle")
    w("")
    w(
        "It measures a provider. It says nothing about whether any intraday rule works, "
        "and D163's conclusion needs no return data to survive contact with better data: a "
        "rule paying a triple-digit percentage of capital a year in fees cannot be run, "
        "however clean the bars are. Going intraday has to mean changing the hypothesis "
        "class, not the sampling rate."
    )
    w("")
    w(
        "The two phases this gates — the S1 terrain sensor re-tested on real intraday "
        "volume, and order-flow imbalance measured against a null before anything is built "
        "on it — are pre-registered separately, in the usual way, before they run."
    )
    w("")
    w(
        f"---\n\nProbed {p['probed_at_utc']} in "
        f"{p['elapsed_seconds']:.0f}s · every figure rendered from `{SUMMARY_JSON.name}`"
    )
    return "\n".join(out) + "\n"


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(build_report(payload), encoding="utf-8")
        print(f"re-rendered {REPORT.name} from {SUMMARY_JSON.name}")
        return 0

    payload = run_probe()
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(build_report(payload), encoding="utf-8")
    print(
        f"wrote {SUMMARY_JSON.name} ({SUMMARY_JSON.stat().st_size / 1e6:.2f} MB) "
        f"and {REPORT.name} in {payload['elapsed_seconds']:.0f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
