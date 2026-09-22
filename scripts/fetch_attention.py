"""The attention layer's fetchers — D612, ledger doc §3.3c and §P3.7.

    uv run python scripts/fetch_attention.py --selftest
    uv run python scripts/fetch_attention.py --wiki-daily Natural_gas 20191104 20191110
    uv run python scripts/fetch_attention.py --wiki-hourly-dump 2019-11-04 13
    uv run python scripts/fetch_attention.py --gdelt-files 20191104001500
    uv run python scripts/fetch_attention.py --gdelt-doc '"natural gas"' 20191104000000 20191104060000
    uv run python scripts/fetch_attention.py --sample
    uv run python scripts/fetch_attention.py --gates

EVERY NETWORK READ GOES THROUGH D608's `Recorder.record`, so every byte this script fetches is
kept under `data/raw/recorder/<job>/` beside a sha256 and the `fetched_at` that is its availability
time (deposit decision D23). The four jobs are `wiki_daily`, `wiki_hourly_dump`, `gdelt_files` and
`gdelt_doc`. `backtest_framework.data.attention` itself has no writer at all.

TWO SOURCES ARE STORED AS A FILTERED RESIDUE RATHER THAN WHOLE, AND THE REASON IS SIZE:

  * **the Wikimedia hourly dumps.** One hour is ~47 MB gzipped and ~168 MB decompressed, and it
    covers every project and every article on earth; the eight titles in `QUERIES.md` account for
    of the order of 16 lines of it. Keeping 168 files whole would put ~8 GB in the cache for ~3 kB
    of content. The residue kept is **a strict subsequence of the original file's lines, byte for
    byte** — no reformatting, no decoding, no re-ordering — under the job's own `fetched_at` name,
    with the source URL in the manifest. The full file is **not** kept and does not need to be:
    `dumps.wikimedia.org` is a permanent archive and re-fetching it is free.
  * **the GDELT GKG slots**, for the same reason at a tenth the scale (~4.2 MB zipped, ~13 MB of
    tab-separated text per 15 minutes, of which the matched documents are a few dozen rows). The
    residue here is a derived TSV of the five fields `QUERIES.md` §2b reads, because a GKG row is
    ~11 kB of GCAM vectors and image URLs that no feature in P3.7 touches.

  The `export` files are kept **whole and unmodified** — they are ~80 kB each — and they are the
  evidence for unit test 23 on real data: `DATEADDED` is the publication slot and `SQLDATE` is the
  event date, and they differ.

`data/raw/` is a gitignored CACHE and is NOT disposable (`CLAUDE.md`, "Files"); `temp/` is the
disposable directory and nothing here writes to it.

WHAT IS NOT FETCHED, AND WHY

  * **`mentions`.** `news_n` is a count of DOCUMENTS matching the query in the last 60 minutes
    (ledger `:251`). GKG has one row per document; `mentions` has one row per (event, outlet)
    re-mention, so counting it would count re-mentions and inflate a burst by the size of the
    syndication network. It is not needed and is not fetched.
  * **any backfill.** The price of the deposit's hourly spec is recorded in D612 and is not paid
    here: Wikipedia hourly 2016-2023 is ~2.5 TB over 70,128 files, GDELT GKG ~1.64 TB over 280,320.
    `--sample` fetches three days.
  * **the DOC 2.0 API as a historical route.** It is the FORWARD route. One request per 5 seconds
    is its stated limit and it 429s with a long cooldown after any burst, so 288 slots of history
    would be 24 minutes of waiting for a series the static files give in eight.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import importlib.util
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.attention import (  # noqa: E402
    AttentionError,
    GdeltItem,
    InsufficientHistory,
    LookaheadRefused,
    QuerySet,
    QueriesTampered,
    ResolutionRefused,
    TrialRow,
    att_accel,
    att_breadth,
    att_level,
    available,
    gdelt_available_at,
    headline_burst,
    iter_gkg_rows,
    load_queries,
    parse_dump_line,
    parse_gkg_row,
    parse_trial_line,
    queries_hash,
    refuse_coarse_resolution,
    slot_datetime,
    trial_header,
    trial_line,
    wiki_available_at,
    wiki_is_available,
    zscore_matched,
)
from backtest_framework.data.recorder import (  # noqa: E402
    RateLimiter,
    Recorder,
    iso_utc,
    utc_now,
)
from backtest_framework.validation.frozen import sha256_file  # noqa: E402


def _load_fast_null():
    """`parallel_map` lives in `scripts/fast_null.py` and is the repository's one fan-out, so its
    `[SPEED]` line is the one every runner prints. Loaded by path because `scripts/` is not a
    package; the module body only defines functions and loads `ragged_panel.py`."""
    spec = importlib.util.spec_from_file_location("fast_null", REPO / "scripts" / "fast_null.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


QUERIES = REPO / "data" / "attention" / "QUERIES.md"
ROOT = REPO / "data" / "raw" / "recorder"
FIXTURE = REPO / "data" / "fixtures" / "attention_sample.csv.gz"
META = REPO / "data" / "fixtures" / "attention_sample.meta.json"

#: D48 / "declared outputs need a guard, not prose": `--sample` declares what it must produce and
#: RAISES first if it cannot, rather than reporting a success nobody checked.
REQUIRED_OUTPUTS = (FIXTURE, META)

#: `scripts/d331_edgar_deals.py`, its line 73 — this repository's descriptive user agent. A
#: contact string is Wikimedia's stated condition for using its APIs and dumps; GDELT states none
#: and gets the same one. No cookie, no login, no personal data, GET and HEAD only.
UA = {
    "User-Agent": "BacktestFramework research script research@backtest-framework.org",
    "Accept": "*/*",
}
TIMEOUT = 600
ATTEMPTS = 4
BACKOFF = 3.0

#: MEASURED THREE TIMES ON ONE DAY, AND THE ANSWER MOVED. `dumps.wikimedia.org` answered HTTP 429
#: to four concurrent connections; two then ran at `[SPEED] 1.96x, 98%` and 2.23 MB/s against
#: 1.69 MB/s serial, so the first build used two. **After ~17 minutes of sustained traffic the
#: pair collapsed to 0.09 MB/s** — one 47 MB file took 547 s — and a re-measurement immediately
#: after found **one connection at 1.79 MB/s and two at 1.54 MB/s aggregate, slower than one**,
#: while a control fetch from GDELT on the same link held 2.32 MB/s. The host throttles sustained
#: concurrency and the throttle is not visible in a short probe.
#:
#: **One worker. A measurement taken once is a guess with a decimal point** (`CLAUDE.md`: every
#: guess here has been wrong), and the honest reading of three measurements is that this host
#: gives one connection's worth of bandwidth however many you open.
WIKI_WORKERS = 1
#: GDELT's static archive served four concurrent connections without complaint, at 91% efficiency
#: and the SAME 2.34 MB/s aggregate as one — the link is the binding constraint here, not the host,
#: so the four workers buy latency hiding and nothing else. Recorded so nobody reads the 3.65x as
#: a speed-up.
GDELT_WORKERS = 4

WIKI_REST = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
    "all-access/user/{article}/daily/{start}00/{end}00"
)
WIKI_DUMP = "https://dumps.wikimedia.org/other/pageviews/{y}/{y}-{m}/pageviews-{ymd}-{hh}0000.gz"
#: **Fetched over TLS.** Probed 2026-09-22: `https://data.gdeltproject.org/gdeltv2/…` answers 200
#: for `lastupdate.txt`, `masterfilelist.txt` and a 2019 GKG slot, so there is no reason to move
#: bytes in clear — and `tests/unit/test_recorder.py` requires every ready job's URL to be https.
GDELT_BASE = "https://data.gdeltproject.org/gdeltv2/"
GDELT_MASTER = GDELT_BASE + "masterfilelist.txt"
GDELT_LAST = GDELT_BASE + "lastupdate.txt"
#: THE INDEX'S OWN SPELLING, WHICH IS NOT OURS TO CHOOSE. Every line of `masterfilelist.txt` and
#: `lastupdate.txt` spells its URL with a plain `http://` scheme. The md5 index is therefore keyed
#: on the FILE NAME rather than on a URL: a lookup keyed on the URL string would have to guess
#: which of the two spellings the other side used, and a checksum that fails to find its entry is
#: as bad as one that does not match.
GDELT_INDEX_BASE = "http://data.gdeltproject.org/gdeltv2/"
GDELT_DOC = "https://api.gdeltproject.org/api/v2/doc/doc"
#: GDELT's own stated limit, quoted from its 429 body: "Please limit requests to one every 5
#: seconds". `--gdelt-doc` is the only command that touches the API.
DOC_MIN_INTERVAL = 5.0

#: The sample window. **TWO DAYS**, and both cuts below the full week are measurements rather than
#: preferences. The week projects to 93 minutes; three days projected 40 and the GDELT half alone
#: then took 17 against 9, after which the pageview host throttled (see `WIKI_WORKERS`) and three
#: days re-projected at one worker to 56. Two days project to 38 and that is what is built.
#: In-sample by construction — 2019 is five years before the 2024-01-01 holdout and nothing here
#: computes a return of any kind.
SAMPLE_START = dt.date(2019, 11, 4)
SAMPLE_END = dt.date(2019, 11, 5)

FIXTURE_COLUMNS = (
    "kind",
    "key",
    "observed_at_utc",
    "available_at_utc",
    "value",
    "tone",
)

_SLOT_RE = re.compile(r"^\d{14}$")
_MASTER_RE = re.compile(r"^(\d+) ([0-9a-f]{32}) (\S+)$")


def P(*a: object) -> None:
    """Every line flushes: a backgrounded run redirects stdout to a FILE (never a pipe — the
    memory note "background output through a pipe is invisible"), and Python block-buffers off a
    tty, so without this a healthy run looks hung."""
    print(*a, flush=True)


def expect_raise(fn, exc_type, what: str) -> None:
    """`scripts/recorder.py`'s self-test idiom. A guard that has never been seen to fire is a
    guard nobody has tested."""
    try:
        fn()
    except exc_type as exc:
        P(f"    RAISES on {what}: {type(exc).__name__}: {str(exc)[:100]}")
        return
    raise AssertionError(f"guard did not raise {exc_type.__name__} on {what}")


# ------------------------------------------------------------------------------------ transport
def _request(url: str, method: str = "GET") -> urllib.request.Request:
    return urllib.request.Request(url, headers=UA, method=method)


def http_bytes(url: str, *, limiter: RateLimiter | None = None) -> tuple[bytes, dict[str, str]]:
    """GET `url` whole. The retry ladder of `backtest_framework.data.recorder.http_get` — four
    attempts, a backoff doubling from 3 s, and **a 404 is never retried** — carried here only
    because this script needs its own `User-Agent` and the recorder's is fixed at module level."""
    delay = BACKOFF
    for attempt in range(ATTEMPTS):
        if limiter is not None:
            limiter.wait()
        try:
            with urllib.request.urlopen(_request(url), timeout=TIMEOUT) as r:
                body = r.read()
                heads = {str(k).lower(): str(v) for k, v in dict(r.headers).items()}
                return bytes(body), heads
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
                raise
            if attempt == ATTEMPTS - 1:
                raise RuntimeError(
                    f"GET {url} failed after {ATTEMPTS} attempts (urllib.request.urlopen): "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"GET {url}: attempts exhausted without a result")


def stream_lines(url: str, *, gzipped: bool, keep) -> tuple[list[bytes], int, int]:
    """Stream `url`, decompressing if asked, and return `([kept lines], raw bytes, plain bytes)`.

    **Nothing is decoded to `str` and no line is split** unless `keep` says the block is worth
    looking at. The block is scanned by `bytes.__contains__`, which is memchr, so 168 MB of
    pageviews costs a memory scan rather than 8 million `str` objects — which is what keeps one
    worker's resident set at ~31 MB and keeps the GIL free for the other worker's socket.
    """
    dec = zlib.decompressobj(31) if gzipped else None
    raw = plain = 0
    buf = b""
    kept: list[bytes] = []
    with urllib.request.urlopen(_request(url), timeout=TIMEOUT) as r:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            raw += len(chunk)
            out = dec.decompress(chunk) if dec is not None else chunk
            if not out:
                continue
            plain += len(out)
            buf += out
            cut = buf.rfind(b"\n")
            if cut < 0:
                continue
            block, buf = buf[: cut + 1], buf[cut + 1 :]
            kept.extend(keep(block))
    if dec is not None:
        tail = dec.flush()
        if tail:
            plain += len(tail)
            buf += tail
    if buf.strip():
        kept.extend(keep(buf if buf.endswith(b"\n") else buf + b"\n"))
    return kept, raw, plain


# ------------------------------------------------------------------------------ wikipedia, daily
def wiki_daily(rec: Recorder, article: str, start: str, end: str) -> dict[str, object]:
    """The REST per-article DAILY series. **There is no per-article HOURLY route** — an hourly
    request answers HTTP 400 with `granularity should be equal to one of the allowed values:
    [daily, monthly]`, which is D612's erratum on the deposit's line 112. This command is what the
    `QUERIES.md` §1a probe column was produced by, and it is a validation route, not a feature
    route: `wiki_n` is hourly."""
    url = WIKI_REST.format(article=urllib.parse.quote(article, safe=""), start=start, end=end)
    body, _ = http_bytes(url)
    key = f"{article}_{start}_{end}"
    r = rec.record("wiki_daily", key, lambda: (body, {}), ext="json", source_url=url)
    payload = json.loads(body.decode("utf-8"))
    items = payload.get("items", [])
    P(f"    wiki_daily {article:32s} {len(items):3d} days, {r.bytes:>7,} bytes, {r.path}")
    return {"article": article, "days": len(items), "views": sum(i["views"] for i in items)}


# ---------------------------------------------------------------------------- wikipedia, hourly
def _dump_url(hour: dt.datetime) -> str:
    return WIKI_DUMP.format(
        y=f"{hour.year:04d}", m=f"{hour.month:02d}", ymd=hour.strftime("%Y%m%d"),
        hh=f"{hour.hour:02d}",
    )


def _wiki_keeper(articles: tuple[str, ...]):
    """A `keep` callable for `stream_lines`: the dump's lines for the fixed article list.

    The prefilter is `b" <Article> "` — the article is the line's SECOND space-separated field, so
    a space on each side is a whole-field test. On a block with no candidate (the overwhelming
    majority) the cost is one memchr per article and nothing is split.
    """
    pres = [(" " + a + " ").encode("utf-8") for a in articles]
    wanted = {a.encode("utf-8") for a in articles}

    def keep(block: bytes) -> list[bytes]:
        if not any(p in block for p in pres):
            return []
        out = []
        for line in block.split(b"\n"):
            parts = line.split(b" ")
            if len(parts) == 4 and parts[1] in wanted:
                out.append(line)
        return out

    return keep


def wiki_hourly_dump(rec: Recorder, qs: QuerySet, hour: dt.datetime) -> dict[str, object]:
    """Stream one hourly dump and record the matched lines — a strict subsequence, byte for byte."""
    url = _dump_url(hour)
    kept, raw, plain = stream_lines(url, gzipped=True, keep=_wiki_keeper(qs.articles))
    residue = b"\n".join(kept) + (b"\n" if kept else b"")
    key = "pageviews_" + hour.strftime("%Y%m%d_%H")
    rec.record(
        "wiki_hourly_dump", key, lambda: (residue, {}), ext="txt", source_url=url,
        method="filtered-residue: the matched lines of the source file, verbatim and in order",
    )
    return {"hour": hour, "lines": len(kept), "raw": raw, "plain": plain, "residue": len(residue)}


def _wiki_rows(qs: QuerySet, hour: dt.datetime, lines: list[bytes]) -> list[tuple[str, ...]]:
    """One fixture row per article: views summed over the §1d projects. An article with no line in
    the hour is a row with value 0 — a zero here is a MEASUREMENT (the dump lists every article
    with at least one view, so an absent article had none), unlike an absent tone."""
    per: dict[str, int] = dict.fromkeys(qs.articles, 0)
    for line in lines:
        w = parse_dump_line(line, hour)
        if w.project in qs.projects and w.article in per:
            per[w.article] += w.views
    avail = wiki_available_at(hour)
    return [
        ("wiki_hourly", a, iso_utc(hour), iso_utc(avail), str(per[a]), "NaN")
        for a in qs.articles
    ]


# ------------------------------------------------------------------------------------- GDELT
def _slots(start: dt.date, end: dt.date) -> list[dt.datetime]:
    out = []
    t = dt.datetime(start.year, start.month, start.day, 0, 0, tzinfo=dt.timezone.utc)
    stop = dt.datetime(end.year, end.month, end.day, 23, 45, tzinfo=dt.timezone.utc)
    while t <= stop:
        out.append(t)
        t += dt.timedelta(minutes=15)
    return out


def _hours(start: dt.date, end: dt.date) -> list[dt.datetime]:
    out = []
    t = dt.datetime(start.year, start.month, start.day, 0, 0, tzinfo=dt.timezone.utc)
    stop = dt.datetime(end.year, end.month, end.day, 23, 0, tzinfo=dt.timezone.utc)
    while t <= stop:
        out.append(t)
        t += dt.timedelta(hours=1)
    return out


def master_md5(rec: Recorder, stamps: set[str]) -> dict[str, tuple[int, str]]:
    """`{file name: (bytes, md5)}` for the wanted slots, from GDELT's `masterfilelist.txt`.

    The master list is 128 MB of `bytes md5 url`, one line per file since 2015-02-18. It is
    streamed and only the wanted slots' lines are kept — the same residue treatment as the
    pageview dumps, and for the same reason. **This is the provenance of every md5 this script
    checks**, so the residue is recorded rather than held in memory and forgotten.
    """
    pres = [(" " + GDELT_INDEX_BASE + s).encode("ascii") for s in sorted(stamps)]

    def keep(block: bytes) -> list[bytes]:
        if not any(p in block for p in pres):
            return []
        return [ln for ln in block.split(b"\n") if any(p in ln for p in pres)]

    kept, raw, _ = stream_lines(GDELT_MASTER, gzipped=False, keep=keep)
    residue = b"\n".join(kept) + (b"\n" if kept else b"")
    rec.record(
        "gdelt_files", "masterfilelist_residue", lambda: (residue, {}), ext="txt",
        source_url=GDELT_MASTER,
        method="filtered-residue: the sample window's lines of masterfilelist.txt, verbatim",
    )
    out: dict[str, tuple[int, str]] = {}
    for line in kept:
        m = _MASTER_RE.match(line.decode("ascii").strip())
        if m is None:
            raise AttentionError(f"masterfilelist line does not parse: {line[:120]!r}")
        out[m.group(3).rsplit("/", 1)[-1]] = (int(m.group(1)), m.group(2))
    P(f"    masterfilelist: streamed {raw:,} bytes, kept {len(kept)} lines for {len(stamps)} slots")
    return out


def _verify_md5(url: str, body: bytes, index: dict[str, tuple[int, str]]) -> None:
    """RAISE when the bytes do not match the index. A checksum that is not compared is decoration.

    Keyed on the file NAME, not on the URL: we fetch over `https` and the index spells `http`
    (see `GDELT_INDEX_BASE`), and a lookup that has to guess a scheme is a lookup that can miss.
    """
    name = url.rsplit("/", 1)[-1]
    if name not in index:
        raise AttentionError(
            f"{name} has no line in the masterfilelist residue; there is no md5 to check it "
            f"against and an unverified file is not recorded as a verified one."
        )
    want_bytes, want_md5 = index[name]
    got = hashlib.md5(body).hexdigest()
    if got != want_md5 or len(body) != want_bytes:
        raise AttentionError(
            f"{name}: masterfilelist says {want_bytes} bytes md5 {want_md5}, the download is "
            f"{len(body)} bytes md5 {got}."
        )


def _gkg_residue(body: bytes, qs: QuerySet) -> tuple[bytes, list[GdeltItem]]:
    """Unzip a GKG slot, keep the matched documents, and render the five fields P3.7 reads."""
    zf = zipfile.ZipFile(io.BytesIO(body))
    names = zf.namelist()
    if len(names) != 1:
        raise AttentionError(f"a GKG zip holds one member, this one holds {names}")
    items: list[GdeltItem] = []
    rows: list[str] = ["publication_ts\ttone\tmatched\tsource_url"]
    for line in iter_gkg_rows(zf.read(names[0])):
        item = parse_gkg_row(line, qs.queries)
        if item is None:
            continue
        items.append(item)
        rows.append(
            f"{iso_utc(item.publication_ts)}\t"
            f"{'' if item.tone is None else repr(item.tone)}\t"
            f"{';'.join(item.matched_queries)}\t{item.source_url}"
        )
    return ("\n".join(rows) + "\n").encode("utf-8"), items


def gdelt_slot(rec: Recorder, qs: QuerySet, slot: dt.datetime,
               index: dict[str, tuple[int, str]], *, with_export: bool) -> list[GdeltItem]:
    """One 15-minute slot: the GKG file always, the `export` file when asked."""
    stamp = slot.strftime("%Y%m%d%H%M%S")
    gkg_url = f"{GDELT_BASE}{stamp}.gkg.csv.zip"
    body, _ = http_bytes(gkg_url)
    _verify_md5(gkg_url, body, index)
    residue, items = _gkg_residue(body, qs)
    rec.record(
        "gdelt_files", f"{stamp}.gkg", lambda: (residue, {}), ext="tsv", source_url=gkg_url,
        method="filtered-residue: the matched documents' five read fields, md5 of the source "
               "zip verified against masterfilelist.txt before filtering",
    )
    if with_export:
        exp_url = f"{GDELT_BASE}{stamp}.export.CSV.zip"
        exp, _ = http_bytes(exp_url)
        _verify_md5(exp_url, exp, index)
        rec.record(
            "gdelt_files", f"{stamp}.export", lambda: (exp, {}), ext="zip", source_url=exp_url,
            method="whole, unmodified: the evidence that DATEADDED (publication) and SQLDATE "
                   "(event) differ, which is ledger unit test 23 on real data",
        )
    return items


def _gdelt_rows(qs: QuerySet, slot: dt.datetime, items: list[GdeltItem]) -> list[tuple[str, ...]]:
    """One fixture row per query: matched document count and mean tone in this 15-minute slot."""
    avail = gdelt_available_at(slot)
    out = []
    for q in qs.queries:
        hit = [i for i in items if q.qid in i.matched_queries]
        tones = [i.tone for i in hit if i.tone is not None]
        tone = "NaN" if not tones else repr(sum(tones) / len(tones))
        out.append(("gdelt_15m", q.qid, iso_utc(slot), iso_utc(avail), str(len(hit)), tone))
    return out


def gdelt_doc(rec: Recorder, query: str, start: str, end: str,
              limiter: RateLimiter) -> dict[str, object]:
    """The DOC 2.0 API — **the FORWARD route**, polled at no more than one request per 5 seconds.

    `timelinevolraw` because `timelinevol` is a normalised intensity and `news_n` is a count. The
    response's own `query_details.date_resolution` is read and **anything coarser than 15 minutes
    is refused**: the API autoscales its bucket width with the span asked for, so a wide window
    silently answers a different question.
    """
    url = GDELT_DOC + "?" + urllib.parse.urlencode({
        "query": query, "mode": "timelinevolraw",
        "startdatetime": start, "enddatetime": end, "format": "json",
    })
    body, _ = http_bytes(url, limiter=limiter)
    key = "doc_" + re.sub(r"[^A-Za-z0-9]+", "_", query).strip("_")[:40] + f"_{start}_{end}"
    rec.record("gdelt_doc", key, lambda: (body, {}), ext="json", source_url=url)
    payload = json.loads(body.decode("utf-8"))
    details = payload.get("query_details") or {}
    resolution = refuse_coarse_resolution(details.get("date_resolution"))
    series = (payload.get("timeline") or [{}])[0].get("data", [])
    P(f"    gdelt_doc {query!r}: resolution {resolution!r}, {len(series)} points")
    return {"resolution": resolution, "points": len(series)}


# -------------------------------------------------------------------------------------- sample
def project(hours: int, slots: int) -> dict[str, float]:
    """The projection printed BEFORE anything is launched, from the 2026-09-22 measurements.

    An hourly dump averages **56.8 MB** gzipped over the four hours probed (00: 50.9, 01: 47.0,
    12: 63.4, 13: 66.0) and decompresses to ~4x that. **The rates here are the ones measured after
    the first build, not before it**: the pageview host sustains **1.79 MB/s on one connection**
    and less on two (see `WIKI_WORKERS`), and a GDELT slot costs **3.57 s measured end to end**
    — download, unzip and parse — against the 1.82 s its 4.25 MB alone would take at 2.34 MB/s,
    because the GKG parse is GIL-bound and four workers share one interpreter. The masterfilelist
    is 127.8 MB.

    **The mean hour is used rather than the smallest measured, and the end-to-end slot cost rather
    than its download**, because a projection built on the best sample is not a projection — the
    first build projected 40 minutes off download rates and its GDELT half alone took 17 against 9.
    """
    wiki_mb = hours * 56.8
    gdelt_mb = slots * 4.25 + 3 * 0.08
    master_mb = 127.8
    secs = wiki_mb / 1.79 + slots * 3.57 + master_mb / 2.34
    return {
        "wiki_mb": wiki_mb, "gdelt_mb": gdelt_mb, "master_mb": master_mb,
        "total_mb": wiki_mb + gdelt_mb + master_mb, "seconds": secs, "minutes": secs / 60.0,
    }


def rss_mb() -> float:
    try:
        import psutil
    except ImportError:
        return -1.0
    return float(psutil.Process().memory_info().rss) / 1e6


def sample(start: dt.date, end: dt.date) -> int:
    missing = [p.parent for p in REQUIRED_OUTPUTS if not p.parent.is_dir()]
    if missing:
        raise AssertionError(f"declared outputs cannot be written: {missing} do not exist")

    qs = load_queries(QUERIES)
    P(f"[queries] {QUERIES.name} sha256 {qs.sha256}")
    P(f"[queries] {len(qs.articles)} articles, {len(qs.queries)} queries, projects {qs.projects}")

    hours = _hours(start, end)
    slots = _slots(start, end)
    proj = project(len(hours), len(slots))
    P(f"[plan] {start} .. {end}: {len(hours)} hourly dumps, {len(slots)} GDELT slots")
    P(f"[plan] PROJECTED {proj['total_mb']:,.0f} MB streamed, "
      f"{proj['minutes']:.1f} min wall "
      f"(wiki {proj['wiki_mb']:,.0f} MB at 1.79 MB/s on {WIKI_WORKERS} worker, "
      f"gdelt {len(slots)} slots at 3.57 s each end to end on {GDELT_WORKERS} workers, "
      f"master {proj['master_mb']:.0f} MB at 2.34 MB/s)")
    P(f"[plan] one worker's RSS before the pool: {rss_mb():.0f} MB")

    fast = _load_fast_null()
    rec = Recorder(ROOT)
    t0 = time.time()

    index = master_md5(rec, {s.strftime("%Y%m%d%H%M%S") for s in slots})
    days = [start + dt.timedelta(days=k) for k in range((end - start).days + 1)]
    first_of_day = dict.fromkeys(days, True)
    rows: list[tuple[str, ...]] = []

    P(f"[gdelt] {len(slots)} slots on {GDELT_WORKERS} workers")

    def _one_slot(stamp: str, _slot: dt.datetime) -> tuple[bytes, list[GdeltItem], int]:
        """THE WORKER RETURNS THE RESIDUE, NOT THE ZIP. 288 GKG zips are 1.2 GB and
        `parallel_map` holds every result until it returns, so a worker that handed back raw
        bodies would put the whole sample in resident memory ("measure the worker before the
        fan-out"). Verifying and filtering inside the worker keeps the peak at
        GDELT_WORKERS x 4.2 MB, and the parse is ~1,800 rows a slot — negligible GIL time
        against a network-bound fan-out."""
        url = f"{GDELT_BASE}{stamp}.gkg.csv.zip"
        body, _ = http_bytes(url)
        _verify_md5(url, body, index)
        residue, items = _gkg_residue(body, qs)
        return residue, items, len(body)

    got = fast.parallel_map(
        _one_slot, [(s.strftime("%Y%m%d%H%M%S"), s) for s in slots],
        workers=GDELT_WORKERS, progress=True,
    )
    for slot in slots:
        stamp = slot.strftime("%Y%m%d%H%M%S")
        url = f"{GDELT_BASE}{stamp}.gkg.csv.zip"
        residue, items, _n = got[stamp]
        rec.record(
            "gdelt_files", f"{stamp}.gkg", lambda: (residue, {}), ext="tsv", source_url=url,
            method="filtered-residue: the matched documents' five read fields, md5 of the "
                   "source zip verified against masterfilelist.txt before filtering",
        )
        if first_of_day.get(slot.date()):
            first_of_day[slot.date()] = False
            exp_url = f"{GDELT_BASE}{stamp}.export.CSV.zip"
            exp, _ = http_bytes(exp_url)
            _verify_md5(exp_url, exp, index)
            rec.record(
                "gdelt_files", f"{stamp}.export", lambda: (exp, {}), ext="zip",
                source_url=exp_url,
                method="whole, unmodified: the evidence that DATEADDED (publication) and "
                       "SQLDATE (event) differ, ledger unit test 23 on real data",
            )
        rows.extend(_gdelt_rows(qs, slot, items))
    gdelt_raw = sum(v[2] for v in got.values())
    export_raw = sum(index[f"{d.strftime('%Y%m%d')}000000.export.CSV.zip"][0]
                     for d in first_of_day)
    del got

    P(f"[wiki] {len(hours)} hourly dumps on {WIKI_WORKERS} worker "
      f"(four answered HTTP 429; two collapsed to 0.09 MB/s after ~17 min and then measured "
      f"SLOWER than one - see WIKI_WORKERS)")
    keep = _wiki_keeper(qs.articles)
    t_wiki = time.time()
    kept = fast.parallel_map(
        lambda k, v: stream_lines(_dump_url(v), gzipped=True, keep=keep),
        [(h.strftime("%Y%m%d_%H"), h) for h in hours],
        workers=WIKI_WORKERS, progress=True,
    )
    wiki_wall = time.time() - t_wiki
    wiki_raw = 0
    for hour in hours:
        lines, raw, _plain = kept[hour.strftime("%Y%m%d_%H")]
        wiki_raw += raw
        residue = b"\n".join(lines) + (b"\n" if lines else b"")
        rec.record(
            "wiki_hourly_dump", "pageviews_" + hour.strftime("%Y%m%d_%H"),
            lambda: (residue, {}), ext="txt", source_url=_dump_url(hour),
            method="filtered-residue: the matched lines of the source file, verbatim and in order",
        )
        rows.extend(_wiki_rows(qs, hour, lines))
    del kept

    wall = time.time() - t0
    # `parallel_map` prints no [SPEED] ratio at one worker (the ratio would be 1.00 by
    # construction and say nothing), so the wiki phase reports the number that IS informative.
    P(f"[speed] wiki phase: {wiki_raw / 1e6:,.0f} MB in {wiki_wall:.0f}s -> "
      f"{wiki_raw / wiki_wall / 1e6:.2f} MB/s on {WIKI_WORKERS} worker")
    P(f"[speed] MEASURED {wall / 60:.1f} min against a projection of {proj['minutes']:.1f} min; "
      f"RSS at the end {rss_mb():.0f} MB")

    write_fixture(rows)
    meta = {
        "spec": "D612",
        "record": "docs/decisions/D612-the-attention-layer-and-its-point-in-time-guards.md",
        "deposit": "SETTLEMENT_FLOW_LEDGER_PREREG.md sections 3.3c and P3.7, its lines 105-116 "
                   "and 249-267",
        "built_utc": iso_utc(utc_now()),
        "span_utc": [iso_utc(dt.datetime.combine(start, dt.time(0, 0), tzinfo=dt.timezone.utc)),
                     iso_utc(dt.datetime.combine(end, dt.time(23, 45), tzinfo=dt.timezone.utc))],
        "queries_sha256": qs.sha256,
        "columns": list(FIXTURE_COLUMNS),
        "rows": len(rows),
        "rows_by_kind": {
            "wiki_hourly": sum(1 for r in rows if r[0] == "wiki_hourly"),
            "gdelt_15m": sum(1 for r in rows if r[0] == "gdelt_15m"),
        },
        "hours": len(hours),
        "slots": len(slots),
        "articles": list(qs.articles),
        "queries": [q.qid for q in qs.queries],
        "low_precision_keys": [q.qid for q in qs.queries if q.precision == "low"],
        "sources": [WIKI_DUMP, GDELT_BASE + "{SLOT}.gkg.csv.zip",
                    GDELT_BASE + "{SLOT}.export.CSV.zip", GDELT_MASTER],
        "bytes_streamed": {"wiki_dumps": wiki_raw, "gdelt_gkg": gdelt_raw,
                           "gdelt_export": export_raw, "masterfilelist": 127845616},
        "bytes_stored": FIXTURE.stat().st_size,
        "sha256": sha256_file(FIXTURE, text_normalise=False),
        "wall_seconds": round(wall, 1),
        "projected_seconds": round(proj["seconds"], 1),
        "workers": {"wiki": WIKI_WORKERS, "gdelt": GDELT_WORKERS},
        "holdout": "attention counts, no return, no signal; in-sample week. No price bar is read "
                   "by this fixture's build and no row dated 2024-01-01 or later is touched.",
        "gdelt_available_at_note": "available_at_utc for a gdelt_15m row is the slot stamp plus "
                                   "one full slot (15 min) — a DECLARED conservative stand-in for "
                                   "an unmeasured file-posting lag, not the deposit's item-level "
                                   "publication rule, which attention.available() implements.",
    }
    with open(META, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=1, sort_keys=True)
        fh.write("\n")
    P(f"[out] {FIXTURE}  {meta['bytes_stored']:,} bytes  sha256 {meta['sha256']}")
    P(f"[out] {META}")
    for p in REQUIRED_OUTPUTS:
        if not p.is_file():
            raise AssertionError(f"declared output {p} was not written")
    return 0


def write_fixture(rows: list[tuple[str, ...]]) -> None:
    ordered = sorted(rows, key=lambda r: (r[2], r[0], r[1]))
    with gzip.open(FIXTURE, "wt", encoding="utf-8", newline="\n") as fh:
        fh.write(",".join(FIXTURE_COLUMNS) + "\n")
        for r in ordered:
            fh.write(",".join(r) + "\n")


# --------------------------------------------------------------------------------------- gates
def gates() -> int:
    """Every hour present for every article; no slot missing; `available_at > observed_at` on every
    row; counts non-negative; tone finite or NaN. Each one RAISES."""
    qs = load_queries(QUERIES)
    meta = json.loads(META.read_text(encoding="utf-8"))
    if meta["queries_sha256"] != qs.sha256:
        raise AssertionError(
            f"the fixture was built under queries {meta['queries_sha256']} and {QUERIES.name} now "
            f"hashes to {qs.sha256}. Deposit line 116: the query list is fixed before any feature "
            f"is computed."
        )
    found = sha256_file(FIXTURE, text_normalise=False)
    if found != meta["sha256"]:
        raise AssertionError(f"{FIXTURE.name} hashes to {found}, the meta says {meta['sha256']}")

    seen_wiki: dict[str, set[str]] = {a: set() for a in qs.articles}
    seen_gdelt: dict[str, set[str]] = {q.qid: set() for q in qs.queries}
    n = 0
    with gzip.open(FIXTURE, "rt", encoding="utf-8", newline="") as fh:
        header = fh.readline().strip().split(",")
        if tuple(header) != FIXTURE_COLUMNS:
            raise AssertionError(f"fixture header {header}, want {list(FIXTURE_COLUMNS)}")
        for raw in fh:
            n += 1
            kind, key, observed, avail, value, tone = raw.rstrip("\n").split(",")
            if avail <= observed:
                raise AssertionError(f"row {n}: available_at {avail} is not after observed_at {observed}")
            count = int(value)
            if count < 0:
                raise AssertionError(f"row {n}: value {value} is negative")
            if tone != "NaN" and not _finite(tone):
                raise AssertionError(f"row {n}: tone {tone!r} is neither NaN nor finite")
            if kind == "wiki_hourly":
                if tone != "NaN":
                    raise AssertionError(f"row {n}: a pageview row carries a tone ({tone!r})")
                seen_wiki[key].add(observed)
            elif kind == "gdelt_15m":
                seen_gdelt[key].add(observed)
            else:
                raise AssertionError(f"row {n}: unknown kind {kind!r}")

    # THE SPAN COMES FROM THE FIXTURE'S OWN META, not from this module's constants: a gate that
    # re-reads the constant would pass a fixture built over a different window.
    first = dt.datetime.strptime(meta["span_utc"][0], "%Y-%m-%dT%H:%M:%SZ").date()
    last = dt.datetime.strptime(meta["span_utc"][1], "%Y-%m-%dT%H:%M:%SZ").date()
    hours = {iso_utc(h) for h in _hours(first, last)}
    slots = {iso_utc(s) for s in _slots(first, last)}
    if len(hours) != meta["hours"] or len(slots) != meta["slots"]:
        raise AssertionError(
            f"the meta says {meta['hours']} hours and {meta['slots']} slots; its own span "
            f"{meta['span_utc']} holds {len(hours)} and {len(slots)}"
        )
    for article, got in seen_wiki.items():
        if got != hours:
            raise AssertionError(
                f"{article}: {len(got)} hours against {len(hours)}; missing "
                f"{sorted(hours - got)[:5]}"
            )
    for qid, got in seen_gdelt.items():
        if got != slots:
            raise AssertionError(
                f"{qid}: {len(got)} slots against {len(slots)}; missing {sorted(slots - got)[:5]}"
            )
    P(f"[gates] {n:,} rows: {len(hours)} hours x {len(qs.articles)} articles, "
      f"{len(slots)} slots x {len(qs.queries)} queries")
    P("[gates] every hour present, every slot present, available_at > observed_at on every row, "
      "counts non-negative, tone finite or NaN, fixture sha256 matches its meta")
    return 0


def _finite(text: str) -> bool:
    try:
        v = float(text)
    except ValueError:
        return False
    return v == v and v not in (float("inf"), float("-inf"))


# ------------------------------------------------------------------------------------ selftest
GOOD_ROW = (
    b"20191104001500-1\t20191104001500\t1\tsrc.com\thttps://src.com/a-natural-gas-story\t\t\t"
    b"ENV_OIL;TAX_FNCACT\t\t\t\t\t\t\t\t1.5,2.0,0.5,2.5,10.0,0.5,100\t\t\t\t\t\t\t\t\t\t\t"
    b"<PAGE_TITLES>x</PAGE_TITLES><PAGE_TITLE>Henry Hub cash prices fall</PAGE_TITLE>"
)


def selftest(tmp: Path) -> int:
    """The GOOD case first, then every guard proved to fire on a deliberate break. No network."""
    P("[selftest] 1. the GOOD case: the real QUERIES.md loads and hashes")
    qs = load_queries(QUERIES)
    assert qs.sha256 == queries_hash(QUERIES)
    assert "Natural_gas" in qs.articles and "KOLD" not in qs.articles
    assert "KOLD" in qs.excluded and "BOIL" in qs.unresolved
    assert qs.projects == ("en", "en.m")
    P(f"    {len(qs.articles)} articles, {len(qs.queries)} queries, sha256 {qs.sha256[:16]}...")

    P("[selftest] 2. the pageview publication boundary (ledger unit test 22)")
    hour = dt.datetime(2019, 11, 4, 13, 0, tzinfo=dt.timezone.utc)
    assert wiki_available_at(hour) == dt.datetime(2019, 11, 4, 14, 15, tzinfo=dt.timezone.utc)
    for probe, want in ((dt.time(14, 10), False), (dt.time(14, 14, 59), False),
                        (dt.time(14, 15), True), (dt.time(14, 15, 1), True)):
        tau = dt.datetime.combine(hour.date(), probe, tzinfo=dt.timezone.utc)
        assert wiki_is_available(hour, tau) is want, (probe, want)
        P(f"    tau {probe} -> {'available' if want else 'UNAVAILABLE'}")

    P("[selftest] 3. a GKG row parses, matches, and carries the slot as its publication time")
    item = parse_gkg_row(GOOD_ROW, qs.queries)
    assert item is not None
    assert item.publication_ts == slot_datetime("20191104001500")
    assert item.tone == 1.5
    assert set(item.matched_queries) == {"natural_gas", "henry_hub", "theme_env_oil"}
    P(f"    matched {item.matched_queries}, tone {item.tone}, published {iso_utc(item.publication_ts)}")
    # A RECORD IS NOT A LINE: V2EXTRASXML carries a source page's <PAGE_LINKS> verbatim and those
    # can hold a raw newline. Two records, the first split across three physical lines.
    split = GOOD_ROW.replace(b"<PAGE_TITLES>x</PAGE_TITLES>", b"<PAGE_LINKS>a\nb\n</PAGE_LINKS>")
    both = split + b"\n" + GOOD_ROW.replace(b"20191104001500-1", b"20191104001500-2")
    assert len(iter_gkg_rows(both)) == 2, iter_gkg_rows(both)
    assert iter_gkg_rows(both)[0] == split
    expect_raise(lambda: iter_gkg_rows(b"not-a-record\tfoo\n"), AttentionError,
                 "a GKG file whose first line is not a GKGRECORDID")
    P("    a record split over three physical lines is reassembled byte for byte")

    P("[selftest] 4. publication AFTER tau is excluded, event time notwithstanding (test 23)")
    tau = dt.datetime(2019, 11, 4, 0, 30, tzinfo=dt.timezone.utc)
    early = GdeltItem(publication_ts=dt.datetime(2019, 11, 4, 0, 15, tzinfo=dt.timezone.utc),
                      event_ts=dt.datetime(2019, 11, 3, tzinfo=dt.timezone.utc), tone=0.0,
                      source_url="a", matched_queries=("natural_gas",))
    late = GdeltItem(publication_ts=dt.datetime(2019, 11, 4, 0, 45, tzinfo=dt.timezone.utc),
                     event_ts=dt.datetime(2019, 11, 1, tzinfo=dt.timezone.utc), tone=0.0,
                     source_url="b", matched_queries=("natural_gas",))
    out = available([early, late], tau)
    assert out == (early,), out
    P("    the item whose EVENT is three days older and whose publication is 15 min later: excluded")

    P("[selftest] 5. a same-day observation in the z-score window RAISES (test 21)")
    mondays = [(dt.date(2019, 9, 30) + dt.timedelta(days=7 * k), 14, 10.0 + 2 * k) for k in range(5)]
    scored = [(dt.date(2019, 11, 4), 14, 20.0)]
    z = zscore_matched(mondays + scored, dt.date(2019, 11, 4), 14)
    assert abs(z - 1.8973665961010275) < 1e-15, z
    P(f"    the good case: z = {z!r} on the hand ledger's five Mondays")
    expect_raise(
        lambda: zscore_matched(
            mondays + scored + [(dt.date(2019, 11, 4), 15, 99.0)], dt.date(2019, 11, 4), 14),
        LookaheadRefused, "an observation dated ON the scored day")
    expect_raise(lambda: zscore_matched(mondays[:4] + scored, dt.date(2019, 11, 4), 14),
                 InsufficientHistory, "four matched observations against a floor of five")

    P("[selftest] 6. att_accel on a step: positive on the ramp, EXACTLY zero once flat (test 24)")
    base = dt.datetime(2019, 11, 4, 9, 0, tzinfo=dt.timezone.utc)
    ramp = {base + dt.timedelta(hours=k): v
            for k, v in enumerate([0.5, 0.5, 0.5, 1.5, 2.5, 3.5])}
    accel = att_accel(ramp, base + dt.timedelta(hours=5))
    assert abs(accel - 2.0) < 1e-15, accel
    flat = {base + dt.timedelta(hours=6 + k): 3.5 for k in range(6)}
    assert att_accel(flat, base + dt.timedelta(hours=11)) == 0.0
    P(f"    ramp {accel!r}, flat {att_accel(flat, base + dt.timedelta(hours=11))!r}")
    expect_raise(lambda: att_accel({k: v for k, v in list(ramp.items())[1:]},
                                   base + dt.timedelta(hours=5)),
                 InsufficientHistory, "a hole in the six-hour window")

    P("[selftest] 7. a TAMPERED QUERIES.md fails the hash")
    fake = tmp / "QUERIES.md"
    with open(fake, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(QUERIES.read_text(encoding="utf-8") + "\n<!-- one more byte -->\n")
    with open(tmp / "QUERIES.sha256", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(queries_hash(QUERIES) + "  QUERIES.md\n")
    expect_raise(lambda: load_queries(fake), QueriesTampered, "a query file edited after its digest")
    expect_raise(lambda: load_queries(tmp / "absent.md"), AttentionError, "an absent query file")

    P("[selftest] 8. a coarse DOC-API resolution is refused")
    assert refuse_coarse_resolution("15min") == "15min"
    expect_raise(lambda: refuse_coarse_resolution("hour"), ResolutionRefused,
                 "date_resolution 'hour', which is not the deposit's 15-minute block")
    expect_raise(lambda: refuse_coarse_resolution("day"), ResolutionRefused, "date_resolution 'day'")

    P("[selftest] 9. an md5 mismatch RAISES, and the key is scheme-insensitive")
    index = {"20191104001500.gkg.csv.zip": (3, hashlib.md5(b"abc").hexdigest())}
    _verify_md5(GDELT_BASE + "20191104001500.gkg.csv.zip", b"abc", index)       # https
    _verify_md5(GDELT_INDEX_BASE + "20191104001500.gkg.csv.zip", b"abc", index)  # http
    expect_raise(lambda: _verify_md5(GDELT_BASE + "20191104001500.gkg.csv.zip", b"abd", index),
                 AttentionError, "bytes that do not hash to the index's md5")
    expect_raise(lambda: _verify_md5(GDELT_BASE + "20191104003000.gkg.csv.zip", b"abc", index),
                 AttentionError, "a file with no line in the index")

    P("[selftest] 10. the module exposes no writer")
    from backtest_framework.data import attention as mod
    bad = [n for n in dir(mod) if not n.startswith("_") and mod.FORBIDDEN_NAME_RE.search(n)]
    assert bad == ["NO_WRITER_HERE"], bad
    assert not hasattr(mod, "write_fixture") and not hasattr(mod, "save")
    P(f"    {mod.NO_WRITER_HERE}")

    P("[selftest] 11. a trial row carries the query digest (test 25)")
    row = TrialRow(trial_id="T1", timestamp=iso_utc(utc_now()), instrument="NG", model="C3",
                   stage="stage1", frozen_sha256="0" * 64, queries_sha256=qs.sha256,
                   notes="selftest, no trial was run")
    back = parse_trial_line(trial_header(), trial_line(row))
    assert back == row and back.queries_sha256 == qs.sha256
    P(f"    round trip holds; queries_sha256 {back.queries_sha256[:16]}...")

    P("[selftest] 12. the remaining features")
    assert att_level({"news": 1.0, "wiki": 3.0}) == 2.0
    assert att_breadth({"news": 2.0, "wiki": 2.5}) == 1  # strictly greater than 2
    # 2019-11-04 is EST, so 09:30 ET is 14:30 UTC. The 13:00 block is BEFORE the open and its
    # z of 9.0 must not fire; the 15:00 block is after it and its 3.5 must.
    pre_open = dt.datetime(2019, 11, 4, 13, 0, tzinfo=dt.timezone.utc)
    post_open = dt.datetime(2019, 11, 4, 15, 0, tzinfo=dt.timezone.utc)
    assert headline_burst({pre_open: 9.0}, dt.date(2019, 11, 4)) == 0
    assert headline_burst({pre_open: 9.0, post_open: 3.5}, dt.date(2019, 11, 4)) == 1
    assert headline_burst({pre_open: 9.0, post_open: 3.0}, dt.date(2019, 11, 4)) == 0
    P("    att_level 2.0, att_breadth 1 (strictly > 2); a z of 9.0 at 13:00 UTC does NOT burst "
      "(09:30 ET is 14:30 UTC in November) and a 3.5 at 15:00 UTC does")

    P("[selftest] PASS")
    return 0


# ------------------------------------------------------------------------------------------ main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wiki-daily", nargs=3, metavar=("ARTICLE", "START", "END"))
    ap.add_argument("--wiki-hourly-dump", nargs=2, metavar=("DATE", "HH"))
    ap.add_argument("--gdelt-files", metavar="SLOT")
    ap.add_argument("--gdelt-doc", nargs=3, metavar=("QUERY", "START", "END"))
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--gates", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args(argv)

    if args.selftest:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            return selftest(Path(td))
    if args.gates:
        return gates()
    if args.sample:
        return sample(SAMPLE_START, SAMPLE_END)

    rec = Recorder(args.root)
    if args.wiki_daily:
        wiki_daily(rec, *args.wiki_daily)
        return 0
    if args.wiki_hourly_dump:
        day, hh = args.wiki_hourly_dump
        hour = dt.datetime.fromisoformat(day).replace(hour=int(hh), tzinfo=dt.timezone.utc)
        qs = load_queries(QUERIES)
        got = wiki_hourly_dump(rec, qs, hour)
        P(f"    {got['lines']} matched lines from {got['raw']:,} raw / {got['plain']:,} plain bytes")
        return 0
    if args.gdelt_files:
        stamp = args.gdelt_files
        if not _SLOT_RE.match(stamp):
            raise SystemExit(f"--gdelt-files wants a 14-digit slot stamp, got {stamp!r}")
        qs = load_queries(QUERIES)
        index = master_md5(rec, {stamp})
        items = gdelt_slot(rec, qs, slot_datetime(stamp), index, with_export=True)
        P(f"    {len(items)} matched documents in {stamp}")
        return 0
    if args.gdelt_doc:
        gdelt_doc(rec, *args.gdelt_doc, limiter=RateLimiter(DOC_MIN_INTERVAL))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
