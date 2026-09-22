"""The six energy funds' Robinhood holder counts, extracted from the Robintrack archive — D621.

    uv run python scripts/build_robintrack_funds.py --selftest
    uv run python scripts/build_robintrack_funds.py --build
    uv run python scripts/build_robintrack_funds.py --gates

WHAT THIS IS, AND WHY IT IS THE VALIDATION SERIES FOR CREATIONS
---------------------------------------------------------------
`data/raw/robintrack/popularity_export/` holds 8,597 tickers' hourly Robinhood holder counts
from 2018-05-02 to 2020-08-13 — the archive behind Barber, Huang, Odean and Schwarz, already on
disk (`docs/data-available.md` §3; D485 used it to settle whether micro futures identify retail).
It is the only series in this repository that counts RETAIL ACCOUNTS rather than dollars or
contracts.

D621 replaces the deposit's hourly-Wikipedia row with CREATIONS as the retail-demand measure.
A replacement that is only argued is not a replacement, so the claim is measured: over the
archive's overlap with `data/fixtures/fund_nav_daily.csv.gz` the daily change in Robinhood
holders is correlated against the daily creation, per fund, same-day and at +/-1 day.
`scripts/retail_attention_report.py` does that; this script builds the input.

**This is a data-quality measurement and not a signal test.** No return is computed, no null is
run, and nothing here is scored against anything. The archive ends 2020-08-13, five and a half
years before this repository's 2024-01-01 reserved slice, so the holdout is untouched by
construction rather than by a filter.

WHAT THE FIXTURE HOLDS AND WHAT IT DOES NOT
-------------------------------------------
Three columns — `ticker, ts_utc, holders` — for six tickers: the four ProShares funds the
settlement-flow ledger names (BOIL, KOLD, UCO, SCO) and the two USCF ones (UNG, USO). The four
ProShares funds have a daily share count on disk and are therefore the ones with a TRUTH to
correlate against; UNG and USO are carried because the ledger names them and because their
holder series is the only retail measure available for them at all (USCF publishes no free NAV
history — D619).

**The archive's timestamps are treated as UTC, and that is a measurement rather than an
assumption.** The hour-of-day histogram of every one of the six files is flat across all 24
hours (the smallest bucket is hour 12 at ~80% of the mean, which is the archive's own daily
maintenance window and not a market session). A series stamped in US local time could not be
flat across the 24 hours and could not run at the same cadence at 03:00 as at 15:00.

**The two site outages are named, not filled.** Measured here on all six funds: the longest two
gaps in every file are the same two, 152.5 h ending 2019-01-30 and 238.0 h ending 2020-01-16,
which is `docs/data-available.md`'s "two ~10-day site outages". They are recorded in the meta,
they are listed by `--gates`, and `retail_attention.robinhood_holders` returns `None` inside
them. **A zero there would be the largest fictional flow in the sample** — USO reading 0 holders
for ten days and 144,000 the day the site came back.

**BOIL's series ends early, on 2020-04-21, and this is the one per-fund surprise in the build.**
The other five run to 2020-08-13. The archive simply stops carrying BOIL after that date; the
fixture records the fund's own span rather than padding it to the archive's, and the D621 record
says so, because a study that assumed a common end date would silently drop four months of the
other five funds or invent four for BOIL.

NOTHING IS FETCHED. The input is already in `data/raw/`, which `CLAUDE.md` names a gitignored
cache that is NOT disposable; this script only reads it.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.retail_attention import (  # noqa: E402
    HOLDER_COLUMNS,
    OUTAGES,
    ROBINTRACK_SPAN,
    HolderObs,
    RetailAttentionError,
    read_holder_fixture,
)
from backtest_framework.validation.frozen import sha256_file  # noqa: E402

UTC = dt.timezone.utc

SRC = REPO / "data" / "raw" / "robintrack" / "popularity_export"
OUT = REPO / "data" / "fixtures" / "robintrack_energy_funds.csv.gz"
META = REPO / "data" / "fixtures" / "robintrack_energy_funds.meta.json"

#: D48 / "declared outputs need a guard, not prose": declared first, checked before and after.
REQUIRED_OUTPUTS = (OUT, META)

#: The six. The first four are the ledger's ProShares funds and the two the creation truth exists
#: for; UNG and USO are USCF and have no free NAV history (D619), so they carry holders alone.
TICKERS = ("BOIL", "KOLD", "UCO", "SCO", "UNG", "USO")
PROSHARES = ("BOIL", "KOLD", "UCO", "SCO")

#: The fixture's columns. Imported from the library rather than retyped: the reader that parses
#: this file back is `retail_attention.read_holder_fixture`, and a writer and a reader with two
#: copies of one header is this repository's most repeated defect.
COLUMNS = HOLDER_COLUMNS

#: A gap at or above this many hours is reported as an OUTAGE candidate by `--gates`. Chosen from
#: the measurement rather than to fit it: the archive's median cadence is 1.00 h and its ordinary
#: long gaps run to ~33 h (a maintenance day), while the two real outages are 152.5 h and 238.0 h.
#: 48 h sits in the empty band between the two populations.
OUTAGE_GAP_HOURS = 48.0

#: THE ARCHIVE'S OWN CANADIAN GAP, recorded because the ledger's P9 arm asks for it and the
#: answer is no. HNU and HOU are the two Canadian leveraged natural-gas ETPs P9 names; neither
#: has a file in the export, which is what a TSX listing on a US retail broker's universe looks
#: like. `--gates` asserts their absence so that a later reader does not go looking.
P9_NOT_ON_ROBINHOOD = ("HNU", "HOU")


def P(*a: object) -> None:
    """Every line flushes: a backgrounded run redirects stdout to a FILE, never a pipe, and
    Python block-buffers off a tty."""
    print(*a, flush=True)


def expect_raise(fn, exc_type, what: str) -> None:
    """`scripts/recorder.py`'s idiom. A guard nobody has seen fire is a guard nobody has tested."""
    try:
        fn()
    except exc_type as exc:
        P(f"    RAISES on {what}: {type(exc).__name__}: {str(exc)[:110]}")
        return
    raise AssertionError(f"guard did not raise {exc_type.__name__} on {what}")


# ------------------------------------------------------------------------------------- reading
def read_ticker(ticker: str, *, src: Path = SRC) -> list[HolderObs]:
    """One ticker's whole series, as `HolderObs`, in file order.

    The archive's format is `timestamp,users_holding` with the timestamp quoted and spelled
    `YYYY-MM-DD HH:MM:SS`. Anything else RAISES: a row this function cannot parse is a row whose
    instant would have to be guessed at, and a guessed instant is a series shifted in time.
    """
    path = src / f"{ticker}.csv"
    if not path.is_file():
        raise RetailAttentionError(f"no Robintrack export for {ticker} at {path}")
    out: list[HolderObs] = []
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != ["timestamp", "users_holding"]:
            raise RetailAttentionError(
                f"{path.name} has columns {reader.fieldnames}, want "
                f"['timestamp', 'users_holding']"
            )
        for n, row in enumerate(reader, start=2):
            raw = (row["timestamp"] or "").strip()
            try:
                when = dt.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
            except ValueError as exc:
                raise RetailAttentionError(
                    f"{path.name}:{n}: timestamp {raw!r} is not 'YYYY-MM-DD HH:MM:SS'"
                ) from exc
            text = (row["users_holding"] or "").strip()
            if not text.isdigit():
                raise RetailAttentionError(
                    f"{path.name}:{n}: users_holding {text!r} is not a non-negative integer. A "
                    f"holder count is a count of accounts; a fractional or negative one is a "
                    f"parse failure, not a datum."
                )
            out.append(HolderObs(ticker=ticker, ts_utc=when, holders=int(text)))
    return out


def gaps(series: list[HolderObs], *, hours: float = OUTAGE_GAP_HOURS
         ) -> list[tuple[str, str, float]]:
    """`(start, end, hours)` for every consecutive pair further apart than `hours`."""
    out: list[tuple[str, str, float]] = []
    for i in range(1, len(series)):
        span = (series[i].ts_utc - series[i - 1].ts_utc).total_seconds() / 3600.0
        if span >= hours:
            out.append((_iso(series[i - 1].ts_utc), _iso(series[i].ts_utc), round(span, 2)))
    return out


def _iso(when: dt.datetime) -> str:
    return when.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def hour_histogram(series: list[HolderObs]) -> list[int]:
    counts = Counter(o.ts_utc.hour for o in series)
    return [counts[h] for h in range(24)]


# ------------------------------------------------------------------------------------- writing
def build() -> int:
    for parent in {p.parent for p in REQUIRED_OUTPUTS}:
        if not parent.is_dir():
            raise AssertionError(f"declared outputs cannot be written: {parent} does not exist")
    if not SRC.is_dir():
        raise AssertionError(
            f"{SRC} is not on disk. data/raw/ is a gitignored CACHE that is NOT disposable "
            f"(CLAUDE.md, 'Files'); the archive is re-fetchable from "
            f"robintrack-data.ameo.design while that mirror lives, and the 504 MB .tar.gz is "
            f"kept beside the extraction."
        )

    per: dict[str, dict[str, object]] = {}
    rows: list[tuple[str, str, str]] = []
    for ticker in TICKERS:
        series = read_ticker(ticker)
        if not series:
            raise AssertionError(f"{ticker}: the export parsed to zero rows")
        for i in range(1, len(series)):
            if series[i].ts_utc <= series[i - 1].ts_utc:
                raise AssertionError(
                    f"{ticker}: the archive is not strictly increasing at row {i + 2}: "
                    f"{_iso(series[i - 1].ts_utc)} then {_iso(series[i].ts_utc)}"
                )
        found = gaps(series)
        per[ticker] = {
            "rows": len(series),
            "span_utc": [_iso(series[0].ts_utc), _iso(series[-1].ts_utc)],
            "holders_min": min(o.holders for o in series),
            "holders_max": max(o.holders for o in series),
            "outage_gaps": [{"from": a, "to": b, "hours": h} for a, b, h in found],
            "hour_histogram_utc": hour_histogram(series),
        }
        rows.extend((o.ticker, _iso(o.ts_utc), str(o.holders)) for o in series)
        P(f"    {ticker:4s} {len(series):>6,} rows  {per[ticker]['span_utc']}  "
          f"holders {per[ticker]['holders_min']:,}..{per[ticker]['holders_max']:,}  "
          f"{len(found)} gaps >= {OUTAGE_GAP_HOURS:.0f}h")

    missing_p9 = [t for t in P9_NOT_ON_ROBINHOOD if (SRC / f"{t}.csv").is_file()]
    if missing_p9:
        raise AssertionError(
            f"{missing_p9} HAVE files in the Robintrack export. D621 records that P9's Canadian "
            f"ETPs are not in a US retail broker's universe; if that is now false the record is "
            f"wrong and must be amended rather than this assertion loosened."
        )

    rows.sort(key=lambda r: (r[0], r[1]))
    _write_rows(rows)

    meta = {
        "spec": "D621; SETTLEMENT_FLOW_LEDGER_PREREG.md section 3.3c line 112, as amended",
        "record": "D621",
        "builder": "scripts/build_robintrack_funds.py",
        "built_utc": _iso(dt.datetime.now(tz=UTC)),
        "source": {
            "path": "data/raw/robintrack/popularity_export/{TICKER}.csv",
            "archive": "data/raw/robintrack/robintrack-popularity-history.tar.gz (504 MB)",
            "provenance": "robintrack-data.ameo.design; the Barber-Huang-Odean-Schwarz Robinhood "
                          "holder-count archive, 8,597 tickers, already on disk before D621",
            "fetched": "NOTHING. This build reads the local cache only.",
        },
        "columns": list(COLUMNS),
        "column_units": {
            "ticker": "the US listing symbol, uppercase",
            "ts_utc": "the archive's own poll instant, treated as UTC -- see the builder's "
                      "docstring: every fund's hour-of-day histogram is flat across all 24 hours, "
                      "which a US-local series could not be",
            "holders": "COUNT OF ROBINHOOD ACCOUNTS holding the ticker at that poll. Not shares, "
                       "not dollars, not a position size.",
        },
        "tickers": list(TICKERS),
        "proshares_with_creation_truth": list(PROSHARES),
        "rows": len(rows),
        "per_ticker": per,
        "archive_span_declared": [ROBINTRACK_SPAN[0].isoformat(), ROBINTRACK_SPAN[1].isoformat()],
        "outages_declared": [[_iso(a), _iso(b)] for a, b in OUTAGES],
        "outage_note": "Two site outages, the same two in every one of the six files: 152.5 h "
                       "ending 2019-01-30 and 238.0 h ending 2020-01-16. They are NAMED AND NOT "
                       "FILLED; retail_attention.robinhood_holders returns None inside them and "
                       "never 0.",
        "boil_note": "BOIL's series ends 2020-04-21, not 2020-08-13 like the other five. The "
                     "archive stops carrying it; nothing is padded and the per-ticker span is "
                     "the fund's own.",
        "p9_not_on_robinhood": list(P9_NOT_ON_ROBINHOOD),
        "p9_note": "HNU and HOU, the ledger's P9 Canadian leveraged natural-gas ETPs, have NO "
                   "file in the 8,597-ticker export. They are TSX-listed and outside a US retail "
                   "broker's universe. Asserted in --build and --gates so nobody re-searches.",
        "encoding": "utf-8, LF, deterministic gzip (mtime=0, no stored filename), so the digest "
                    "is a fact about the rows and not about when the build ran",
        "date_col": "ts_utc",
        "sha256": sha256_file(OUT, text_normalise=False),
        "bytes": OUT.stat().st_size,
        "holdout": "HOLDER COUNTS ONLY -- no price, no return, no signal, no trade. The archive "
                   "ends 2020-08-13, five and a half years before this repository's 2024-01-01 "
                   "reserved slice, so no reserved row exists to read.",
    }
    with open(META, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=1, sort_keys=True)
        fh.write("\n")

    for p in REQUIRED_OUTPUTS:
        if not p.is_file():
            raise AssertionError(f"declared output {p} was not written")
    P(f"[out] {OUT}  {meta['bytes']:,} bytes  sha256 {meta['sha256']}")
    P(f"[out] {META}")
    return 0


def _write_rows(rows: list[tuple[str, str, str]]) -> None:
    """A DETERMINISTIC gzip stream, `scripts/build_fund_panel.py:588`'s pattern: `mtime=0` and an
    empty stored filename make the bytes a pure function of the rows rather than of when the
    build ran, so the digest identifies the CONTENT (D550/D551)."""
    with open(OUT, "wb") as fb, gzip.GzipFile(
        filename="", mode="wb", fileobj=fb, mtime=0, compresslevel=9
    ) as gz:
        gz.write((",".join(COLUMNS) + "\n").encode("utf-8"))
        for r in rows:
            gz.write((",".join(r) + "\n").encode("utf-8"))


def read_fixture(path: Path = OUT) -> list[HolderObs]:
    """The fixture back as `HolderObs`. **The reader is the library's**
    (`retail_attention.read_holder_fixture`) and this is a one-line alias kept so that this
    script's own gates and self-test read through exactly what a consumer reads through."""
    return read_holder_fixture(path)


# --------------------------------------------------------------------------------------- gates
def gates() -> int:
    """Every gate RAISES. Six tickers present; timestamps strictly increasing per ticker;
    holders a non-negative integer on every row; the two outage gaps present in every ticker;
    the fixture's bytes hashing to what its meta records."""
    meta = json.loads(META.read_text(encoding="utf-8"))
    found = sha256_file(OUT, text_normalise=False)
    if found != meta["sha256"]:
        raise AssertionError(f"{OUT.name} hashes to {found}, the meta says {meta['sha256']}")

    series = read_fixture()
    by_ticker: dict[str, list[HolderObs]] = {}
    for obs in series:
        by_ticker.setdefault(obs.ticker, []).append(obs)

    if tuple(sorted(by_ticker)) != tuple(sorted(TICKERS)):
        raise AssertionError(f"tickers in the fixture: {sorted(by_ticker)}, want {sorted(TICKERS)}")
    for ticker, rows in by_ticker.items():
        for i in range(1, len(rows)):
            if rows[i].ts_utc <= rows[i - 1].ts_utc:
                raise AssertionError(
                    f"{ticker}: timestamps are not strictly increasing at row {i}: "
                    f"{_iso(rows[i - 1].ts_utc)} then {_iso(rows[i].ts_utc)}"
                )
        for obs in rows:
            if not isinstance(obs.holders, int) or obs.holders < 0:
                raise AssertionError(f"{ticker} at {_iso(obs.ts_utc)}: holders {obs.holders!r}")
        found_gaps = gaps(rows)
        if len(found_gaps) != 2:
            raise AssertionError(
                f"{ticker}: {len(found_gaps)} gaps of >= {OUTAGE_GAP_HOURS:.0f} h, want exactly "
                f"the two declared site outages: {found_gaps}"
            )
        ends = [g[1][:10] for g in found_gaps]
        if ends != ["2019-01-30", "2020-01-16"]:
            raise AssertionError(f"{ticker}: outage gaps end {ends}, want the two declared dates")
        P(f"[gates] {ticker:4s} {len(rows):>6,} rows, monotone, holders >= 0, "
          f"outages {found_gaps[0][2]:.1f} h and {found_gaps[1][2]:.1f} h")

    for t in P9_NOT_ON_ROBINHOOD:
        if (SRC / f"{t}.csv").is_file():
            raise AssertionError(f"{t} now HAS a Robintrack export; D621's P9 note is wrong")

    P(f"[gates] {len(series):,} rows over {len(by_ticker)} tickers; the two site outages are "
      f"present in every one of them and are NOT filled; HNU and HOU are absent as recorded")
    return 0


# ------------------------------------------------------------------------------------ selftest
def selftest(tmp: Path) -> int:
    """The GOOD case first, then every guard proved to fire on a deliberate break. No network,
    and no dependence on the fixture existing."""
    P("[selftest] 1. the GOOD case: a two-row export parses")
    good = tmp / "AAA.csv"
    with open(good, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('timestamp,users_holding\n"2018-05-02 04:54:15",106\n"2018-05-02 06:39:27",108\n')
    series = read_ticker("AAA", src=tmp)
    assert len(series) == 2, series
    assert series[0].ts_utc == dt.datetime(2018, 5, 2, 4, 54, 15, tzinfo=UTC)
    assert series[1].holders == 108
    P(f"    {len(series)} rows, first {_iso(series[0].ts_utc)} holders {series[0].holders}")

    P("[selftest] 2. a missing export RAISES rather than yielding an empty series")
    expect_raise(lambda: read_ticker("ZZZ", src=tmp), RetailAttentionError, "an absent ticker file")

    P("[selftest] 3. a wrong header RAISES")
    bad = tmp / "BBB.csv"
    with open(bad, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("timestamp,holders\n\"2018-05-02 04:54:15\",106\n")
    expect_raise(lambda: read_ticker("BBB", src=tmp), RetailAttentionError,
                 "an export whose second column has been renamed")

    P("[selftest] 4. a non-integer and a negative holder count RAISE")
    for text, what in (("10.5", "a fractional holder count"), ("-3", "a negative holder count")):
        broken = tmp / "CCC.csv"
        with open(broken, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(f'timestamp,users_holding\n"2018-05-02 04:54:15",{text}\n')
        expect_raise(lambda: read_ticker("CCC", src=tmp), RetailAttentionError, what)

    P("[selftest] 5. an unparseable timestamp RAISES rather than being guessed at")
    stamped = tmp / "DDD.csv"
    with open(stamped, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('timestamp,users_holding\n"02/05/2018 04:54",106\n')
    expect_raise(lambda: read_ticker("DDD", src=tmp), RetailAttentionError,
                 "a timestamp in a different format")

    P("[selftest] 6. the gap finder separates an ordinary long gap from an outage")
    base = dt.datetime(2019, 1, 23, 23, 45, tzinfo=UTC)
    run = [
        HolderObs("AAA", base, 1),
        HolderObs("AAA", base + dt.timedelta(hours=33), 2),     # a maintenance day: NOT an outage
        HolderObs("AAA", base + dt.timedelta(hours=33 + 152), 3),  # an outage
    ]
    found = gaps(run)
    assert len(found) == 1 and found[0][2] == 152.0, found
    P(f"    33 h is not a gap at the {OUTAGE_GAP_HOURS:.0f} h line; 152 h is: {found}")

    P("[selftest] 7. the deterministic gzip is a function of the rows alone")
    import hashlib
    import io
    digests = set()
    for _ in range(2):
        buf = io.BytesIO()
        with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0, compresslevel=9) as gz:
            gz.write(b"ticker,ts_utc,holders\nAAA,2018-05-02T04:54:15Z,106\n")
        digests.add(hashlib.sha256(buf.getvalue()).hexdigest())
    assert len(digests) == 1, digests
    P(f"    two writes, one digest: {digests.pop()[:16]}...")

    P("[selftest] 8. the round trip: rows written and read back are the same objects")
    rows = [("AAA", "2018-05-02T04:54:15Z", "106"), ("AAA", "2018-05-02T06:39:27Z", "108")]
    tmp_out = tmp / "round.csv.gz"
    with open(tmp_out, "wb") as fb, gzip.GzipFile(
        filename="", mode="wb", fileobj=fb, mtime=0, compresslevel=9
    ) as gz:
        gz.write((",".join(COLUMNS) + "\n").encode("utf-8"))
        for r in rows:
            gz.write((",".join(r) + "\n").encode("utf-8"))
    back = read_fixture(tmp_out)
    assert back == series, (back, series)
    P(f"    {len(back)} rows round-tripped identically")

    P("[selftest] PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--build", action="store_true", help="extract the six tickers into the fixture")
    ap.add_argument("--gates", action="store_true", help="check the built fixture")
    ap.add_argument("--selftest", action="store_true", help="prove every guard fires; no IO")
    args = ap.parse_args(argv)

    if args.selftest:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            return selftest(Path(td))
    if args.build:
        return build()
    if args.gates:
        return gates()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
