"""GDELT hourly news counts — the DOC 2.0 API forward route, and the file-derived sample. D621.

    uv run python scripts/fetch_gdelt_hourly.py --selftest
    uv run python scripts/fetch_gdelt_hourly.py --probe
    uv run python scripts/fetch_gdelt_hourly.py --from-files
    uv run python scripts/fetch_gdelt_hourly.py --api 20191104000000 20191106000000
    uv run python scripts/fetch_gdelt_hourly.py --gates

WHY AN HOURLY GDELT SERIES AT ALL, WHEN D612 ALREADY HAS A 15-MINUTE ONE
------------------------------------------------------------------------
D621 pairs the news series with a DAILY creation series, so the news side needs an hourly (or
coarser) bucket to be comparable, and the API's bucket width autoscales with the span asked for:
anything wider than a few days answers `"date_resolution": "hour"`. D612's
`attention.refuse_coarse_resolution` refuses exactly that, correctly, because the deposit's
`headline_burst` is *"1 if z_news > 3 in any 15-min block since 09:30"* and an hourly bucket
cannot answer it.

So there are two resolutions and they belong to two different features. **The forward recorder
job stays 15-minute** — `data/recorder/jobs.json`'s `attention` job, D612's — and the deposit's
features are computed from it. **D621's hourly series is a separate object**, parsed by
`retail_attention.news_n_hourly(..., accept_hourly=True)`, which calls
`refuse_coarse_resolution` FIRST and only then admits an hourly spelling. "day" and "month" still
raise, from the original function, unwidened.

THE API IS RATE-LIMITED AND WAS COOLING DOWN WHEN THIS WAS WRITTEN
------------------------------------------------------------------
GDELT's DOC 2.0 API states *"Please limit requests to one every 5 seconds"* and answers HTTP 429
with a long cooldown after any burst. D612 probed it on 2026-09-22 and never got a 200 all day.
**D621 probed it once more the same day, at 2026-09-22, and got 429 again** — the body is
recorded byte for byte under `data/raw/recorder/gdelt_hourly/` and quoted in the record.

`--api` is therefore BUILT AND NOT RUN, and `data/fixtures/gdelt_hourly_sample.csv.gz` is built
by `--from-files` instead: D612's own `attention_sample.csv.gz` holds the 15-minute file-derived
counts for 2019-11-04..05, and this script sums them to the hour. That is a real hourly GDELT
series from the route D612 established, and it is the object the API series will be compared
against when the API answers. **The two need not agree**, and the record says why before either
is measured: `timelinevolraw` counts documents in GDELT's own DOC index matching a DOC-query
grammar, while the 15-minute route counts GKG rows matching `QUERIES.md` §2b's title/url/theme
rules. Different corpora, different matchers. What is worth measuring is whether they move
together, not whether they are equal, and the fixture's `source` column keeps them apart so that
nobody sums one into the other.

EVERY NETWORK READ GOES THROUGH D608's `Recorder` under the job `gdelt_hourly`, including the
429 refusal — a logged block names the tool, the URL and the headers, or the next reader repeats
the probe to find out what happened.

No return is computed, no price bar is read, and the sample window is 2019, four years before
this repository's 2024-01-01 reserved slice.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import math
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.attention import (  # noqa: E402
    GDELT_SLOT,
    AttentionError,
    ResolutionRefused,
    gdelt_available_at,
    load_queries,
)
from backtest_framework.data.recorder import RateLimiter, Recorder, iso_utc, utc_now  # noqa: E402
from backtest_framework.data.retail_attention import (  # noqa: E402
    RetailAttentionError,
    news_n_hourly,
)
from backtest_framework.validation.frozen import sha256_file  # noqa: E402

UTC = dt.timezone.utc

QUERIES = REPO / "data" / "attention" / "QUERIES.md"
RECORDER_ROOT = REPO / "data" / "raw" / "recorder"
SAMPLE_IN = REPO / "data" / "fixtures" / "attention_sample.csv.gz"
SAMPLE_META_IN = REPO / "data" / "fixtures" / "attention_sample.meta.json"
OUT = REPO / "data" / "fixtures" / "gdelt_hourly_sample.csv.gz"
META = REPO / "data" / "fixtures" / "gdelt_hourly_sample.meta.json"

REQUIRED_OUTPUTS = (OUT, META)

JOB = "gdelt_hourly"
DOC = "https://api.gdeltproject.org/api/v2/doc/doc"
#: GDELT's own stated limit, quoted from its 429 body. D612's constant, same value, same source.
DOC_MIN_INTERVAL = 5.0
UA = {
    "User-Agent": "BacktestFramework research script research@backtest-framework.org",
    "Accept": "*/*",
}
TIMEOUT = 120

COLUMNS = ("source", "qid", "hour_utc", "available_at_utc", "n_articles", "tone")

#: The two `source` values the fixture may carry. They are kept in ONE file with a source column
#: rather than in two files, so that a consumer must choose which corpus it is reading; and they
#: are never summed, because they count different objects (see the module docstring).
SOURCE_FILES = "files_15m_summed"
SOURCE_API = "doc_api_hourly"

#: D612's sample window, which is what `--from-files` can cover.
SAMPLE_START = dt.date(2019, 11, 4)
SAMPLE_END = dt.date(2019, 11, 5)

#: **THE API BLOCK, LOGGED WHERE A LATER READER WILL LOOK.** The memory rule is "a logged block
#: names the tool": the tool, the URL, the two outcomes and their order, so that nobody repeats
#: the probe to find out what happened. Both attempts below were made on 2026-09-22 from this
#: machine, roughly twelve minutes apart, with the same URL and the same User-Agent.
API_STATE_DEFERRED: dict[str, object] = {
    "state": "DEFERRED - the live hourly series has NOT been fetched",
    "tool": "urllib.request.urlopen, GET, User-Agent "
            "'BacktestFramework research script research@backtest-framework.org'",
    "url": "https://api.gdeltproject.org/api/v2/doc/doc"
           "?query=%22natural+gas%22&mode=timelinevolraw"
           "&startdatetime=20191104000000&enddatetime=20191106000000&format=json",
    "attempts": [
        {
            "when_utc": "2026-09-22",
            "outcome": "HTTP 429",
            "body": "Please limit requests to one every 5 seconds or contact "
                    "kalev.leetaru5@gmail.com for larger queries. All high-traffic users should "
                    "switch to our ngrams dataset ... For trend analysis, please see our daily "
                    "newsletter briefings ...",
        },
        {
            "when_utc": "2026-09-22, about twelve minutes later",
            "outcome": "NO RESPONSE - TCP connect timed out",
            "body": "urllib.error.URLError: <urlopen error [WinError 10060] A connection attempt "
                    "failed because the connected party did not properly respond after a period "
                    "of time>. No status line, so no bytes; nothing was written into data/raw/.",
        },
    ],
    "reading": "The host escalates: a refusal BODY first, then a dropped connection. D612 never "
               "got a 200 from it all day either. The raw 15-minute files remain the historical "
               "route (D612) and this API is the forward route only; --api is built, its parser "
               "is proved on a payload of the documented response shape, and it has not been run.",
}


def P(*a: object) -> None:
    print(*a, flush=True)


def expect_raise(fn, exc_type, what: str) -> None:
    try:
        fn()
    except exc_type as exc:
        P(f"    RAISES on {what}: {type(exc).__name__}: {str(exc)[:110]}")
        return
    raise AssertionError(f"guard did not raise {exc_type.__name__} on {what}")


# ------------------------------------------------------------------------------------ transport
def doc_url(query: str, start: str, end: str, mode: str) -> str:
    return DOC + "?" + urllib.parse.urlencode(
        {
            "query": query,
            "mode": mode,
            "startdatetime": start,
            "enddatetime": end,
            "format": "json",
        }
    )


class TransportRefused(RetailAttentionError):
    """The host did not answer at all — no status line, so no bytes to record.

    Kept distinct from an HTTP error on purpose. **A 429 is a response and is recorded; a dropped
    connection is not a response and nothing is written into `data/raw/`**, because the only
    bytes available would be this script's own rendering of an exception and D608's cache holds
    responses byte for byte or it holds nothing. The failure is logged in the record and in
    `gdelt_hourly_sample.meta.json`'s `api_state` instead, naming the tool, the URL and the OS
    error — which is where a later reader looks to find out what happened.
    """


def get(url: str, *, limiter: RateLimiter | None = None) -> tuple[int, bytes, dict[str, str]]:
    """GET `url` once and return `(status, body, headers)`, **including for an HTTP error**.

    A 429 body is EVIDENCE and not an exception to swallow: it carries the limit in the host's
    own words and it is what the record quotes. One attempt, no retry ladder — retrying into a
    cooldown is how the cooldown gets extended, which is exactly what D612 measured.

    A transport failure — no status line at all — raises `TransportRefused` naming the tool.
    """
    if limiter is not None:
        limiter.wait()
    req = urllib.request.Request(url, headers=UA, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return int(r.status), bytes(r.read()), {
                str(k).lower(): str(v) for k, v in dict(r.headers).items()
            }
    except urllib.error.HTTPError as exc:
        return int(exc.code), bytes(exc.read()), {
            str(k).lower(): str(v) for k, v in dict(exc.headers or {}).items()
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise TransportRefused(
            f"urllib.request.urlopen(timeout={TIMEOUT}) did not get a status line from {url}: "
            f"{type(exc).__name__}: {exc}. No response means no bytes, and nothing is written "
            f"into data/raw/ that the host did not send."
        ) from exc


def probe(rec: Recorder, *, query: str = '"natural gas"',
          start: str = "20191104000000", end: str = "20191106000000") -> int:
    """ONE request, recorded whatever it ANSWERS. The 429 path is the documented outcome."""
    url = doc_url(query, start, end, "timelinevolraw")
    P(f"[probe] GET {url}")
    try:
        status, body, headers = get(url, limiter=RateLimiter(DOC_MIN_INTERVAL))
    except TransportRefused as exc:
        P(f"[probe] NO RESPONSE: {exc}")
        P("[probe] nothing recorded — a dropped connection is not a response. The live sample is "
          "DEFERRED; data/fixtures/gdelt_hourly_sample.csv.gz is built by --from-files.")
        return 0
    ext = "json" if status == 200 else "txt"
    r = rec.record(
        JOB,
        f"probe_{status}",
        lambda: (body, headers),
        ext=ext,
        source_url=url,
        method=(
            "one DOC 2.0 request, recorded whatever it answered. A refusal body is evidence: it "
            "carries the host's own statement of its limit and is what the D621 record quotes."
        ),
    )
    P(f"[probe] HTTP {status}, {len(body):,} bytes -> {r.path}")
    P(f"[probe] body: {body[:400].decode('utf-8', 'replace')}")
    if status != 200:
        P(f"[probe] the API is REFUSING. --api is built and not run; the live sample is DEFERRED "
          f"and data/fixtures/gdelt_hourly_sample.csv.gz is built by --from-files instead. "
          f"Response headers: {sorted(headers)}")
        return 0
    payload = json.loads(body.decode("utf-8"))
    series = news_n_hourly(payload, accept_hourly=True)
    P(f"[probe] resolution {series.resolution!r}, {len(series.points)} points, "
      f"total {series.total:,.0f}")
    return 0


def from_api(rec: Recorder, start: str, end: str) -> int:
    """**Built, and not run on 2026-09-22.** Every §2c query, both modes, at >= 5 s spacing.

    `timelinevolraw` because `timelinevol` is a normalised intensity and a count is wanted;
    `timelinetone` beside it because the deposit's `news_tone` is a mean tone. The resolution is
    read from the response's own `query_details.date_resolution` on every call and an hourly
    bucket is admitted only through `news_n_hourly(accept_hourly=True)`, which refuses anything
    coarser through D612's own function.
    """
    qs = load_queries(QUERIES)
    encodings = _doc_encodings(QUERIES)
    limiter = RateLimiter(DOC_MIN_INTERVAL)
    calls = 2 * len(encodings)
    P(f"[plan] {len(encodings)} queries x 2 modes = {calls} requests at >= "
      f"{DOC_MIN_INTERVAL:.0f} s spacing -> PROJECTED {calls * DOC_MIN_INTERVAL / 60:.1f} min "
      f"wall, and the host 429s with a long cooldown after any burst.")
    P(f"[plan] queries sha256 {qs.sha256}")

    rows: list[tuple[str, ...]] = []
    for qid, encoded in encodings:
        counts = _one_api_series(rec, qid, encoded, start, end, "timelinevolraw", limiter)
        tones = _one_api_series(rec, qid, encoded, start, end, "timelinetone", limiter)
        tone_by_hour = dict(tones.points)
        for when, value in counts.points:
            tone = tone_by_hour.get(when)
            rows.append(
                (
                    SOURCE_API,
                    qid,
                    iso_utc(when),
                    iso_utc(when + dt.timedelta(hours=1)),
                    repr(value),
                    "NaN" if tone is None else repr(tone),
                )
            )
    P(f"[api] {len(rows)} rows over {len(encodings)} queries")
    return _write(rows, mode="api", api_span=(start, end))


def _one_api_series(rec: Recorder, qid: str, encoded: str, start: str, end: str,
                    mode: str, limiter: RateLimiter):
    url = doc_url(encoded, start, end, mode)
    status, body, headers = get(url, limiter=limiter)
    rec.record(
        JOB, f"{mode}_{qid}_{start}_{end}", lambda: (body, headers),
        ext="json" if status == 200 else "txt", source_url=url,
        method="DOC 2.0 timeline, recorded whole and unmodified",
    )
    if status != 200:
        raise RetailAttentionError(
            f"DOC 2.0 answered HTTP {status} for {qid} {mode}. The body is recorded; it is not "
            f"parsed as data. Body: {body[:200].decode('utf-8', 'replace')}"
        )
    return news_n_hourly(json.loads(body.decode("utf-8")), accept_hourly=True, mode=mode)


def _doc_encodings(path: Path) -> list[tuple[str, str]]:
    """`QUERIES.md` §2c's `(id, query=)` table, URL-decoded back into what to send.

    Read from the hashed file rather than retyped: §2c is the only place the DOC-API spelling of
    each query is fixed, and a second copy here could drift from the object `load_queries`
    verifies. The four THEME queries have no §2c spelling on purpose — theme search on the API
    uses a different operator and `QUERIES.md` declines to write an encoding that has never been
    sent — so this returns ten of the fourteen ids, and that is not a parse failure.
    """
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    out: list[tuple[str, str]] = []
    seen = False
    for line in text.split("\n"):
        if line.startswith("#") and "2c." in line:
            seen = True
            continue
        if seen and line.startswith("#"):
            break
        if not seen:
            continue
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            continue
        cells = [c.strip() for c in s[1:-1].split("|")]
        if len(cells) != 2:
            continue
        qid, encoded = (c.strip("`") for c in cells)
        if qid in ("id", "") or set(encoded) <= set("-: "):
            continue
        out.append((qid, urllib.parse.unquote_plus(encoded)))
    if not out:
        raise RetailAttentionError(f"{path}: section 2c holds no `query=` table")
    return out


# ------------------------------------------------------------------- the file-derived half
def from_files() -> int:
    """Sum D612's 15-minute file-derived counts to the hour. No network.

    Four slots make an hour — `h:00`, `h:15`, `h:30`, `h:45` — and all four must be present or
    the hour RAISES. D612's own gate asserts every slot of its window is in the fixture, so a
    missing slot here means the fixture has been edited, which is worth a loud failure rather
    than an hour that is quietly three quarters of an hour.

    `n_articles` is the plain sum of the four document counts. `tone` is the COUNT-WEIGHTED mean
    of the slots that had a tone at all, and an hour with no matched document has NO tone,
    written `NaN` and never `0.0` — a zero tone is neutral coverage and an absent tone is no
    coverage (`QUERIES.md` §2b, D612).

    `available_at_utc` is the LATEST of the four slots' own `gdelt_available_at`, which is
    `h + 1 hour` — derived from D612's rule rather than asserted here, so that if that rule is
    ever replaced by a measurement this column moves with it.
    """
    qs = load_queries(QUERIES)
    meta_in = json.loads(SAMPLE_META_IN.read_text(encoding="utf-8"))
    if meta_in["queries_sha256"] != qs.sha256:
        raise AssertionError(
            f"attention_sample was built under queries {meta_in['queries_sha256']} and "
            f"{QUERIES.name} now hashes to {qs.sha256}. Deposit line 116: the query list is "
            f"fixed before any feature is computed."
        )
    found = sha256_file(SAMPLE_IN, text_normalise=False)
    if found != meta_in["sha256"]:
        raise AssertionError(f"{SAMPLE_IN.name} hashes to {found}, its meta says {meta_in['sha256']}")

    slots: dict[tuple[str, dt.datetime], tuple[int, float | None]] = {}
    with gzip.open(SAMPLE_IN, "rt", encoding="utf-8", newline="") as fh:
        header = tuple(fh.readline().rstrip("\n").split(","))
        want = ("kind", "key", "observed_at_utc", "available_at_utc", "value", "tone")
        if header != want:
            raise AssertionError(f"{SAMPLE_IN.name} header {header}, want {want}")
        for line in fh:
            kind, key, observed, _avail, value, tone = line.rstrip("\n").split(",")
            if kind != "gdelt_15m":
                continue
            when = dt.datetime.strptime(observed, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            slots[(key, when)] = (int(value), None if tone == "NaN" else float(tone))

    qids = [q.qid for q in qs.queries]
    hours = sorted({w.replace(minute=0) for _k, w in slots})
    rows: list[tuple[str, ...]] = []
    for qid in qids:
        for hour in hours:
            members = [hour + k * GDELT_SLOT for k in range(4)]
            missing = [iso_utc(m) for m in members if (qid, m) not in slots]
            if missing:
                raise AssertionError(
                    f"{qid} at {iso_utc(hour)}: {len(missing)} of the 4 slots are absent from "
                    f"{SAMPLE_IN.name}: {missing}. An hour is four slots or it is not an hour."
                )
            counts = [slots[(qid, m)][0] for m in members]
            tones = [(slots[(qid, m)][1], slots[(qid, m)][0]) for m in members]
            weighted = [(t, c) for t, c in tones if t is not None and c > 0]
            total = sum(counts)
            if weighted:
                num = math.fsum(t * c for t, c in weighted)
                den = math.fsum(float(c) for _t, c in weighted)
                tone_text = repr(num / den)
            else:
                tone_text = "NaN"
            avail = max(gdelt_available_at(m) for m in members)
            rows.append((SOURCE_FILES, qid, iso_utc(hour), iso_utc(avail), str(total), tone_text))
    P(f"[from-files] {len(rows)} rows: {len(hours)} hours x {len(qids)} queries, summed from "
      f"{len(slots):,} 15-minute rows of {SAMPLE_IN.name}")
    return _write(rows, mode="from_files", api_span=None)


def _write(rows: list[tuple[str, ...]], *, mode: str, api_span: tuple[str, str] | None) -> int:
    for parent in {p.parent for p in REQUIRED_OUTPUTS}:
        if not parent.is_dir():
            raise AssertionError(f"declared outputs cannot be written: {parent} does not exist")
    ordered = sorted(rows, key=lambda r: (r[0], r[1], r[2]))
    with open(OUT, "wb") as fb, gzip.GzipFile(
        filename="", mode="wb", fileobj=fb, mtime=0, compresslevel=9
    ) as gz:
        gz.write((",".join(COLUMNS) + "\n").encode("utf-8"))
        for r in ordered:
            gz.write((",".join(r) + "\n").encode("utf-8"))

    qs = load_queries(QUERIES)
    meta = {
        "spec": "D621; SETTLEMENT_FLOW_LEDGER_PREREG.md section 3.3c and P3.7 lines 251, 265",
        "record": "D621",
        "builder": f"scripts/fetch_gdelt_hourly.py --{mode.replace('_', '-')}",
        "built_utc": iso_utc(utc_now()),
        "columns": list(COLUMNS),
        "column_units": {
            "source": f"{SOURCE_FILES} | {SOURCE_API} -- WHICH CORPUS. Never summed across.",
            "qid": "a QUERIES.md section 2b id",
            "hour_utc": "the START of the hour the count covers",
            "available_at_utc": "the first instant the hour's count may be used",
            "n_articles": "COUNT OF DOCUMENTS matching the query in that hour",
            "tone": "count-weighted mean document tone, or NaN when no document matched",
        },
        "queries_sha256": qs.sha256,
        "rows": len(ordered),
        "rows_by_source": {
            SOURCE_FILES: sum(1 for r in ordered if r[0] == SOURCE_FILES),
            SOURCE_API: sum(1 for r in ordered if r[0] == SOURCE_API),
        },
        "queries": [q.qid for q in qs.queries],
        "low_precision_keys": [q.qid for q in qs.queries if q.precision == "low"],
        "api_span": list(api_span) if api_span is not None else None,
        "api_state": "fetched" if api_span is not None else API_STATE_DEFERRED,
        "resolution_note": (
            "This series is HOURLY and the deposit's news_n is a 60-minute count over 15-MINUTE "
            "blocks (its lines 251, 265). The forward recorder job stays 15-minute. An hourly "
            "bucket is admitted only through retail_attention.news_n_hourly(accept_hourly=True), "
            "which calls attention.refuse_coarse_resolution first; 'day' and 'month' still raise."
        ),
        "corpus_note": (
            f"{SOURCE_FILES} counts GKG rows matching QUERIES.md section 2b's title/url/theme "
            f"rules. {SOURCE_API} counts documents in GDELT's DOC index matching a DOC-query "
            f"grammar. DIFFERENT CORPORA AND DIFFERENT MATCHERS: they are expected to move "
            f"together and are not expected to be equal. The source column keeps them apart."
        ),
        "encoding": "utf-8, LF, deterministic gzip (mtime=0, no stored filename)",
        "date_col": "hour_utc",
        "sha256": sha256_file(OUT, text_normalise=False),
        "bytes": OUT.stat().st_size,
        "holdout": "NEWS COUNTS ONLY -- no price, no return, no signal. The window is 2019, four "
                   "years before this repository's 2024-01-01 reserved slice.",
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


# --------------------------------------------------------------------------------------- gates
def gates() -> int:
    """Every gate RAISES. Header exact; every row's `available_at` strictly after its hour;
    counts non-negative integers; tone finite or NaN; every hour on an hour boundary; every qid
    known to `QUERIES.md`; the fixture's bytes hashing to its meta."""
    qs = load_queries(QUERIES)
    meta = json.loads(META.read_text(encoding="utf-8"))
    if meta["queries_sha256"] != qs.sha256:
        raise AssertionError(
            f"the fixture was built under queries {meta['queries_sha256']}, {QUERIES.name} now "
            f"hashes to {qs.sha256}"
        )
    found = sha256_file(OUT, text_normalise=False)
    if found != meta["sha256"]:
        raise AssertionError(f"{OUT.name} hashes to {found}, the meta says {meta['sha256']}")

    known = {q.qid for q in qs.queries}
    n = 0
    per_source: dict[str, int] = {}
    with gzip.open(OUT, "rt", encoding="utf-8", newline="") as fh:
        header = tuple(fh.readline().rstrip("\n").split(","))
        if header != COLUMNS:
            raise AssertionError(f"fixture header {header}, want {COLUMNS}")
        for line in fh:
            n += 1
            source, qid, hour, avail, count, tone = line.rstrip("\n").split(",")
            if source not in (SOURCE_FILES, SOURCE_API):
                raise AssertionError(f"row {n}: unknown source {source!r}")
            per_source[source] = per_source.get(source, 0) + 1
            if qid not in known:
                raise AssertionError(f"row {n}: qid {qid!r} is not in {QUERIES.name}")
            h = dt.datetime.strptime(hour, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            if (h.minute, h.second) != (0, 0):
                raise AssertionError(f"row {n}: hour {hour} is not on an hour boundary")
            a = dt.datetime.strptime(avail, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            if a <= h:
                raise AssertionError(f"row {n}: available_at {avail} is not after the hour {hour}")
            value = float(count)
            if value < 0 or not math.isfinite(value):
                raise AssertionError(f"row {n}: n_articles {count!r}")
            if tone != "NaN" and not math.isfinite(float(tone)):
                raise AssertionError(f"row {n}: tone {tone!r} is neither NaN nor finite")
    if n != meta["rows"]:
        raise AssertionError(f"{n} rows on disk, the meta says {meta['rows']}")
    P(f"[gates] {n:,} rows, sources {per_source}; every hour on a boundary, "
      f"available_at after the hour on every row, counts non-negative, tone finite or NaN")
    state = meta["api_state"]
    P(f"[gates] api_state: {state if isinstance(state, str) else state['state']}")
    return 0


# ------------------------------------------------------------------------------------ selftest
#: A `timelinevolraw` payload OF THE DOCUMENTED RESPONSE SHAPE. **This is not a recorded live
#: response** and the record says so plainly: the API answered 429 to every request D612 and
#: D621 made. Its shape is the one `scripts/fetch_attention.py:gdelt_doc` already reads —
#: `query_details.date_resolution` and `timeline[0].data[{date, value}]` — and the parser is
#: proved against it here. The moment a 200 arrives, `--probe` records the real bytes and this
#: literal is replaced by them rather than kept beside them.
API_SHAPE = {
    "query_details": {"query": '"natural gas"', "date_resolution": "hour"},
    "timeline": [
        {
            "series": "Volume Raw",
            "data": [
                {"date": "20191104T000000Z", "value": 12},
                {"date": "20191104T010000Z", "value": 9},
                {"date": "20191104T020000Z", "value": 0},
            ],
        }
    ],
}


def selftest() -> int:
    """The GOOD case first, then every guard proved to fire on a deliberate break. No network."""
    P("[selftest] 1. the GOOD case: an hourly payload parses when hourly is asked for")
    series = news_n_hourly(API_SHAPE, accept_hourly=True)
    assert series.resolution == "hour", series.resolution
    assert len(series.points) == 3 and series.total == 21.0, series
    assert series.points[0][0] == dt.datetime(2019, 11, 4, 0, 0, tzinfo=UTC)
    P(f"    resolution {series.resolution!r}, {len(series.points)} points, total {series.total}")

    P("[selftest] 2. the SAME payload is REFUSED when the deposit's 15-minute rule applies")
    expect_raise(lambda: news_n_hourly(API_SHAPE, accept_hourly=False), ResolutionRefused,
                 "an hourly bucket where headline_burst needs 15-minute blocks")

    P("[selftest] 3. a DAILY bucket is refused even with accept_hourly=True")
    daily = {**API_SHAPE, "query_details": {"date_resolution": "day"}}
    expect_raise(lambda: news_n_hourly(daily, accept_hourly=True), ResolutionRefused,
                 "date_resolution 'day', which no widening admits")

    P("[selftest] 4. a 15-minute bucket is accepted by BOTH settings, unwidened")
    fine = {**API_SHAPE, "query_details": {"date_resolution": "15min"}}
    assert news_n_hourly(fine, accept_hourly=False).resolution == "15min"
    assert news_n_hourly(fine, accept_hourly=True).resolution == "15min"
    P("    '15min' passes accept_hourly=False and accept_hourly=True alike")

    P("[selftest] 5. a response with no resolution at all RAISES rather than defaulting")
    expect_raise(lambda: news_n_hourly({"timeline": API_SHAPE["timeline"]}, accept_hourly=True),
                 RetailAttentionError, "a payload with no query_details")
    expect_raise(lambda: news_n_hourly({"query_details": {"date_resolution": "hour"}},
                                       accept_hourly=True),
                 RetailAttentionError, "a payload with no timeline")

    P("[selftest] 6. an unparseable stamp and a non-monotone timeline RAISE")
    bad_stamp = {**API_SHAPE, "timeline": [{"data": [{"date": "2019-11-04 00:00", "value": 1}]}]}
    expect_raise(lambda: news_n_hourly(bad_stamp, accept_hourly=True), RetailAttentionError,
                 "a stamp that is not YYYYMMDDTHHMMSSZ")
    backwards = {**API_SHAPE, "timeline": [{"data": [
        {"date": "20191104T010000Z", "value": 1}, {"date": "20191104T000000Z", "value": 2}]}]}
    expect_raise(lambda: news_n_hourly(backwards, accept_hourly=True), RetailAttentionError,
                 "a timeline that goes backwards")

    P("[selftest] 7. the URL this script would send, and the queries it reads from QUERIES.md")
    enc = _doc_encodings(QUERIES)
    ids = [q for q, _ in enc]
    assert ("natural_gas", "\"natural gas\"") in enc, enc[:3]
    assert not any(q.startswith("theme_") for q in ids), ids
    P(f"    {len(enc)} DOC-API spellings, no theme query among them: {ids}")
    url = doc_url('"natural gas"', "20191104000000", "20191106000000", "timelinevolraw")
    assert url.startswith("https://"), url
    assert "mode=timelinevolraw" in url and "format=json" in url
    P(f"    {url}")

    P("[selftest] 8. the rate limiter really waits")
    ticks: list[float] = []
    limiter = RateLimiter(DOC_MIN_INTERVAL, sleep=ticks.append)
    limiter.wait()
    limiter.wait()
    assert ticks and 0 < ticks[0] <= DOC_MIN_INTERVAL, ticks
    P(f"    the second call asked to sleep {ticks[0]:.2f} s against a {DOC_MIN_INTERVAL:.0f} s limit")

    P("[selftest] PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--probe", action="store_true", help="ONE request; record whatever it answers")
    ap.add_argument("--from-files", action="store_true",
                    help="build the hourly fixture from D612's 15-minute sample; no network")
    ap.add_argument("--api", nargs=2, metavar=("START", "END"),
                    help="every QUERIES.md section 2c query, both modes, >= 5 s apart")
    ap.add_argument("--gates", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", type=Path, default=RECORDER_ROOT)
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if args.gates:
        return gates()
    if args.from_files:
        return from_files()
    if args.probe:
        return probe(Recorder(args.root))
    if args.api:
        return from_api(Recorder(args.root), *args.api)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
