"""The forward data recorder — Track 2 of the settlement-flow ledger, D608.

THE SPEC, QUOTED VERBATIM from `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md`
§13A.3 "Track 2: forward data recorder":

    **Storage rules:**
    - Save the **raw response** (HTML/CSV/JSON) unmodified, plus a parsed Parquet copy.
    - Every record carries `fetched_at` (UTC) and, where the source states it, `published_at`.
    - **Never overwrite.** New fetches are new files. Store a checksum per file.
    - Gap detection: alert if any daily job misses its window. Log gaps in
      `data/recorder/GAPS.md`. Gaps are **never** filled with estimates.
    - For forward tests, **`fetched_at` is the availability time** (conservative; decision D23).

    **Hosting:** an always-on machine or small server with scheduled jobs (Q17). The recorder
    must survive reboots and log its own health.

and the three unit tests it names, §12 items 31–33, verbatim:

    31. Recorder never overwrites: a second fetch on the same day creates a new file; checksums
        differ only if content differs.
    32. Recorder availability: a forward test reading a record uses `fetched_at`, not
        `published_at`, as the time it became usable.
    33. Gap detection flags a missed daily job, and no downstream code fills the gap.

WHAT IS HERE AND WHAT IS NOT
----------------------------
Here: the write side (`Recorder.record`), the read side (`Recorder.records`,
`availability_time`), the schedule (`Job`, `load_jobs`), gap detection (`check_gaps`,
`append_gaps`), the health line (`health_line`), and an HTTP primitive (`http_get`,
`RateLimiter`) with the retry shape of `_get` in `scripts/fetch_release_calendar.py` (its line 131).

NOT here, deliberately, and each omission is a decision recorded in D608:

  * **No scheduler, service, cron entry or startup item.** Q17 — which always-on machine, with
    what backup — is the principal's open question. `scripts/recorder.py --run` is ONE PASS and
    exits, the shape `scripts/run_futures_acquisition.py:57` states as "one pass; the harness
    re-invokes on exit", so whatever the host turns out to be only has to invoke a command.
  * **No `fill_gap`, no `backfill`, no `impute`, no `interpolate`.** §13A.3 says gaps are never
    filled with estimates. A guarantee about code that does not exist can only be tested as an
    assertion about this module's namespace, and `tests/unit/test_recorder.py` makes it.
  * **No Parquet.** The spec asks for "a parsed Parquet copy" and this checkout has no Parquet
    engine at all (`pyarrow` is in neither the project dependencies nor the dev group), and
    `.gitignore` excludes `/data/**/*.parquet` from the index besides. `record(parse=...)`
    therefore writes the parsed copy as UTF-8 CSV beside the raw file, under the same stamp.
    The disagreement is recorded rather than papered over; the raw response — the thing that
    cannot be recomputed — is unaffected either way.

THE BYTES ARE NEVER NORMALISED. `validation/frozen.py` (D594) LF-pins text before hashing
because code is text and a checkout's newline handling must not move a frozen identity. A
recorded response is NOT source: it is what a server sent, and normalising it would mean the
bytes on disk no longer hash to the checksum stored beside them. Every digest here is over the
bytes exactly as they arrived, and every raw file is written with `open(..., "xb")`.

Governing rule: D191 — cache the raw, commit the derived, verify hashes loudly. `data/raw/` is a
gitignored CACHE and is not disposable (`CLAUDE.md`, "Files"); `temp/` is the disposable
directory and nothing here writes to it.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

__all__ = [
    "ChecksumMismatch",
    "FILL_IS_FORBIDDEN",
    "Gap",
    "Job",
    "JobConfigError",
    "ManifestError",
    "MissingRawFile",
    "OverwriteRefused",
    "RateLimiter",
    "Record",
    "Recorder",
    "RecorderError",
    "Run",
    "RunOutcome",
    "append_gaps",
    "append_health",
    "availability_time",
    "check_gaps",
    "check_gaps_scope",
    "fetcher",
    "gap_line",
    "health_line",
    "http_get",
    "iso_utc",
    "load_jobs",
    "sha256_bytes",
    "stamp_of",
]

SCHEMA = "recorder/1"
HEALTH_SCHEMA = "recorder-health/1"

ET = ZoneInfo("America/New_York")

#: `scripts/fetch_release_calendar.py:88`, unchanged — one user agent for this repository.
UA: dict[str, str] = {
    "User-Agent": "backtest-framework-fetch/1.0 (personal research; contact via repository)",
    "Accept": "text/html,application/json",
}
TIMEOUT = 120
ATTEMPTS = 4
BACKOFF_SECONDS = 3.0

CADENCES = ("daily", "weekly", "intraday")
STATUSES = ("ready", "needs_source", "needs_key")
#: Gap detection covers these two. §13A.3's rule is written for a job with ONE window a day
#: ("alert if any daily job misses its window"); an intraday job's own miss rate is a different
#: statistic and this module does not invent one for it. `check_gaps_scope` names what is skipped.
GAP_CHECKED_CADENCES = ("daily", "weekly")

FILL_IS_FORBIDDEN = (
    "Gaps are NEVER filled with estimates (SETTLEMENT_FLOW_LEDGER_PREREG.md §13A.3). "
    "There is no fill_gap in this module and there must never be one."
)
#: Any public name matching this is a violation of the line above. Asserted in the unit tests.
FORBIDDEN_NAME_RE = re.compile(r"fill|backfill|impute|interpolate|estimate|synthes", re.I)

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_EXT_RE = re.compile(r"^[A-Za-z0-9]{1,12}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_HHMM_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

GAPS_HEADER = (
    "# `data/recorder/GAPS.md` — every recorder window that closed without a record\n"
    "\n"
    "*D608. **Append-only**: a line is added and never rewritten, and no gap is ever filled\n"
    "with an estimate — `SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.3, \"Gaps are **never** filled\n"
    "with estimates\". Written by `backtest_framework.data.recorder.append_gaps`; the module has\n"
    "no `fill_gap` and must never acquire one. A line here is a hole in the record that stays a\n"
    "hole.*\n"
    "\n"
    "| date (ET) | job | cadence | window (ET) | window closed (UTC) | reason | logged (UTC) |\n"
    "|---|---|---|---|---|---|---|\n"
)


# --------------------------------------------------------------------------------------- errors
class RecorderError(Exception):
    """Base for every loud failure in this module. D48: no silent default, ever."""


class OverwriteRefused(RecorderError):
    """A write was attempted at a path that already exists. §13A.3: never overwrite."""


class ChecksumMismatch(RecorderError):
    """A raw file's bytes no longer hash to the checksum the manifest stores for it (D191)."""


class MissingRawFile(RecorderError):
    """The manifest names a file that is not on disk. `data/raw/` is a cache, not disposable."""


class ManifestError(RecorderError):
    """The per-job manifest is absent, malformed, or of an unknown schema."""


class JobConfigError(RecorderError):
    """A job definition, key or extension is not usable. Never repaired, always raised."""


# ---------------------------------------------------------------------------------- time + bytes
def utc_now() -> dt.datetime:
    """The default clock. Injectable everywhere so a test never depends on the wall clock."""
    return dt.datetime.now(dt.timezone.utc)


def _assert_aware_utc(when: dt.datetime, what: str) -> dt.datetime:
    if when.tzinfo is None:
        raise JobConfigError(f"{what} is naive: {when!r}. Every instant here is tz-aware UTC.")
    return when.astimezone(dt.timezone.utc)


def stamp_of(when: dt.datetime) -> str:
    """`2026-09-21 14:30:00+00:00` -> `20260921T143000Z`, the filename stamp of
    `scripts/fetch_release_calendar.py:193`. Resolution is ONE SECOND, which is why
    `Recorder.record` carries a collision suffix rather than trusting the clock."""
    return _assert_aware_utc(when, "stamp_of(when)").strftime("%Y%m%dT%H%M%SZ")


def iso_utc(when: dt.datetime) -> str:
    """`2026-09-21T14:30:00Z`. The shape `scripts/settlement_windows.py:70-82` asserts on every
    `accessed_utc`: ends with `Z`, exactly 20 characters, no offset and no fractional second."""
    return _assert_aware_utc(when, "iso_utc(when)").strftime("%Y-%m-%dT%H:%M:%SZ")


def assert_iso_z(value: str, what: str) -> str:
    """The provenance-timestamp guard, copied from `scripts/settlement_windows.py`'s
    `accessed_utc` assertion: `endswith("Z") and len(...) == 20`, and parseable."""
    if not isinstance(value, str) or not value.endswith("Z") or len(value) != 20:
        raise JobConfigError(f"{what} must be an ISO-Z instant of 20 chars ending Z, got {value!r}")
    if not _ISO_Z_RE.match(value):
        raise JobConfigError(f"{what} is not YYYY-MM-DDTHH:MM:SSZ: {value!r}")
    try:
        dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise JobConfigError(f"{what} is not a real instant: {value!r} ({exc})") from exc
    return value


def parse_iso_z(value: str, what: str = "instant") -> dt.datetime:
    """The inverse of `iso_utc`, through the same guard."""
    assert_iso_z(value, what)
    return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)


def _as_int(value: object, what: str) -> int:
    """A manifest field that must be a whole number. A float or a string RAISES rather than
    being coerced — a byte count that arrived as `"12"` means the writer was not this module."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ManifestError(f"manifest field {what} must be an int, got {type(value).__name__}: {value!r}")
    return value


def sha256_bytes(body: bytes) -> str:
    """sha256 of exactly these bytes. No newline normalisation: a response is not source."""
    if not isinstance(body, bytes | bytearray):
        raise TypeError(f"sha256_bytes wants bytes, got {type(body).__name__}")
    return hashlib.sha256(bytes(body)).hexdigest()


def _write_new_bytes(path: Path, body: bytes) -> None:
    """Exclusive create. `"xb"` is the guarantee, not a preceding `exists()` check — between the
    check and the write there is a window, and §13A.3's rule has no exceptions."""
    try:
        with open(path, "xb") as fh:
            fh.write(body)
    except FileExistsError as exc:
        raise OverwriteRefused(
            f"{path.name} already exists and this recorder never overwrites "
            f"(SETTLEMENT_FLOW_LEDGER_PREREG.md §13A.3). A new fetch is a NEW FILE."
        ) from exc


def _write_text_atomic(path: Path, text: str) -> None:
    """`.part` then replace — `scripts/run_futures_acquisition.py:157`, so a killed run never
    leaves a truncated manifest. UTF-8 and LF pinned (D550)."""
    tmp = path.with_suffix(path.suffix + ".part")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    tmp.replace(path)


# --------------------------------------------------------------------------------------- Record
@dataclass(frozen=True)
class Record:
    """One fetch. Frozen, because a record of what arrived when must not be editable in place.

    Units and conventions:
      `fetched_at`   ISO-Z UTC, the instant `record()` took its stamp. **The availability time.**
      `published_at` ISO-Z UTC or None. Recorded ONLY when the caller passes it; never inferred.
      `bytes`        length of the raw response in bytes, as received.
      `sha256`       hex digest of those bytes, unnormalised.
      `path`         POSIX-style, relative to the job directory.
      `parsed_path`  the derived copy beside the raw file, or None. Derived, never evidence.
    """

    job: str
    key: str
    path: str
    fetched_at: str
    published_at: str | None
    bytes: int
    sha256: str
    source_url: str | None
    method: str
    headers: tuple[tuple[str, str], ...] = ()
    parsed_path: str | None = None
    parsed_rows: int | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "job": self.job,
            "key": self.key,
            "path": self.path,
            "fetched_at": self.fetched_at,
            "published_at": self.published_at,
            "bytes": self.bytes,
            "sha256": self.sha256,
            "source_url": self.source_url,
            "method": self.method,
            "headers": [list(pair) for pair in self.headers],
            "parsed_path": self.parsed_path,
            "parsed_rows": self.parsed_rows,
        }

    @staticmethod
    def from_dict(raw: Mapping[str, object]) -> Record:
        missing = [k for k in ("job", "key", "path", "fetched_at", "bytes", "sha256") if k not in raw]
        if missing:
            raise ManifestError(f"manifest entry is missing {missing}: {dict(raw)!r}")
        headers = raw.get("headers") or []
        if not isinstance(headers, list):
            raise ManifestError(f"manifest entry has a non-list `headers`: {headers!r}")
        published = raw.get("published_at")
        if published is not None:
            assert_iso_z(str(published), "published_at")
        return Record(
            job=str(raw["job"]),
            key=str(raw["key"]),
            path=str(raw["path"]),
            fetched_at=assert_iso_z(str(raw["fetched_at"]), "fetched_at"),
            published_at=None if published is None else str(published),
            bytes=_as_int(raw["bytes"], "bytes"),
            sha256=str(raw["sha256"]),
            source_url=None if raw.get("source_url") is None else str(raw["source_url"]),
            method=str(raw.get("method", "fetched")),
            headers=tuple((str(p[0]), str(p[1])) for p in headers),
            parsed_path=None if raw.get("parsed_path") is None else str(raw["parsed_path"]),
            parsed_rows=None if raw.get("parsed_rows") is None else _as_int(raw["parsed_rows"], "parsed_rows"),
        )

    @property
    def fetched_dt(self) -> dt.datetime:
        return parse_iso_z(self.fetched_at, "fetched_at")


def availability_time(record: Record) -> str:
    """**The time a forward test may first use this record: `fetched_at`, always.**

    Ledger doc §13A.3: *"For forward tests, `fetched_at` is the availability time (conservative;
    decision D23)."* Deposit decision D23: *"`fetched_at` used as availability time in forward
    tests — Conservative: publication timestamps can be optimistic."*

    Unconditional by design. It does not compare the two timestamps, does not take a maximum, and
    does not fall back to `published_at` when that field is None — a rule with a branch in it is a
    rule that can take the wrong branch, and the wrong branch here is a look-ahead. `published_at`
    is carried for provenance and for measuring publication lag; it is never the availability time.
    """
    if not isinstance(record, Record):
        raise TypeError(f"availability_time wants a Record, got {type(record).__name__}")
    return record.fetched_at


# ------------------------------------------------------------------------------------- Recorder
FetchFn = Callable[[], tuple[bytes, Mapping[str, str]]]
ParseFn = Callable[[bytes], Sequence[Mapping[str, object]]]


class Recorder:
    """Raw-first, append-only storage under `<root>/<job>/`.

    Layout, all of it gitignored (`/data/raw/` in `.gitignore`) and none of it disposable:

        <root>/health.jsonl                       one line per run (Q17's "log its own health")
        <root>/<job>/_manifest.json               every record for that job, in write order
        <root>/<job>/<key>__<stamp>.<ext>         the raw response, byte for byte
        <root>/<job>/<key>__<stamp>.parsed.csv    the derived copy, when a parser was supplied
    """

    def __init__(self, root: Path, *, clock: Callable[[], dt.datetime] | None = None) -> None:
        self.root = Path(root)
        self.clock = clock or utc_now

    # -- paths ------------------------------------------------------------------------------
    def job_dir(self, job: str) -> Path:
        return self.root / _checked_name(job, "job")

    def manifest_path(self, job: str) -> Path:
        return self.job_dir(job) / "_manifest.json"

    @property
    def health_path(self) -> Path:
        return self.root / "health.jsonl"

    # -- manifest ---------------------------------------------------------------------------
    def load_manifest(self, job: str) -> dict[str, object]:
        path = self.manifest_path(job)
        if not path.exists():
            return {"schema": SCHEMA, "job": job, "records": []}
        try:
            man = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ManifestError(f"{path} is not JSON: {exc}") from exc
        if not isinstance(man, dict) or man.get("schema") != SCHEMA:
            raise ManifestError(f"{path} has schema {man.get('schema') if isinstance(man, dict) else '?'!r}, want {SCHEMA!r}")
        if not isinstance(man.get("records"), list):
            raise ManifestError(f"{path} has no `records` list")
        return man

    def save_manifest(self, job: str, man: Mapping[str, object]) -> None:
        self.job_dir(job).mkdir(parents=True, exist_ok=True)
        _write_text_atomic(self.manifest_path(job), json.dumps(man, indent=1, sort_keys=True) + "\n")

    # -- write ------------------------------------------------------------------------------
    def record(
        self,
        job: str,
        key: str,
        fetch: FetchFn,
        *,
        ext: str,
        published_at: str | None = None,
        source_url: str | None = None,
        method: str = "fetched",
        parse: ParseFn | None = None,
    ) -> Record:
        """Fetch once and keep the bytes unmodified under a `fetched_at` name. Never overwrites.

        `fetch` is a zero-argument callable returning `(body, headers)` — the network is the
        caller's, so a test passes a literal and a runner passes `fetcher(url)`. `ext` is the raw
        file's extension (`html`, `json`, `csv`), `published_at` is recorded only if the SOURCE
        states it, and `parse` — if given — writes a derived CSV copy beside the raw file.

        Unit test 31 lives here: a second call for the same key produces a NEW file. The stamp
        resolves to the second, so a collision inside one second appends `-1`, `-2`, … to the
        stamp; nothing is ever written over.
        """
        job = _checked_name(job, "job")
        key = _checked_name(key, "key")
        if not _EXT_RE.match(ext):
            raise JobConfigError(f"ext {ext!r} is not 1-12 alphanumerics")
        if published_at is not None:
            assert_iso_z(published_at, "published_at")

        body, headers = _checked_response(fetch())
        when = _assert_aware_utc(self.clock(), "Recorder.clock()")
        stamp = stamp_of(when)

        jdir = self.job_dir(job)
        jdir.mkdir(parents=True, exist_ok=True)
        name = _free_name(jdir, key, stamp, ext)
        _write_new_bytes(jdir / name, body)

        parsed_name: str | None = None
        parsed_rows: int | None = None
        if parse is not None:
            rows = parse(body)
            parsed_name = f"{name.rsplit('.', 1)[0]}.parsed.csv"
            parsed_rows = _write_parsed_csv(jdir / parsed_name, rows)

        rec = Record(
            job=job,
            key=key,
            path=name,
            fetched_at=iso_utc(when),
            published_at=published_at,
            bytes=len(body),
            sha256=sha256_bytes(body),
            source_url=source_url,
            method=method,
            headers=tuple((str(k).lower(), str(v)) for k, v in headers.items()),
            parsed_path=parsed_name,
            parsed_rows=parsed_rows,
        )
        man = self.load_manifest(job)
        records = man["records"]
        assert isinstance(records, list)  # load_manifest raised otherwise
        records.append(rec.to_dict())
        self.save_manifest(job, man)  # saved after EVERY record (fetch_release_calendar.py:200)
        return rec

    # -- read -------------------------------------------------------------------------------
    def records(self, job: str, *, verify: bool = True) -> list[Record]:
        """Every record for `job`, sorted by `fetched_at` (then by path, so the `-1` collision
        suffix orders deterministically).

        `verify=True` re-hashes each raw file and RAISES on a mismatch or a missing file. D191:
        verify hashes loudly. A recorder whose checksums are decorative is a recorder that cannot
        tell a truncated download from a complete one two years later.

        THE SORT IS NOT A PLAIN NAME SORT, and the reason is one byte. `-` is 0x2D and `.` is
        0x2E, so `k__S-1.html` sorts BEFORE `k__S.html` and a lexicographic sort would put the
        second record of a second ahead of the first. The collision index is therefore extracted
        and sorted numerically, which makes the read order the write order.
        """
        man = self.load_manifest(job)
        raw_records = man["records"]
        assert isinstance(raw_records, list)
        out: list[Record] = []
        jdir = self.job_dir(job)
        for entry in raw_records:
            if not isinstance(entry, Mapping):
                raise ManifestError(f"{self.manifest_path(job)} holds a non-object record: {entry!r}")
            rec = Record.from_dict(entry)
            if verify:
                path = jdir / rec.path
                if not path.exists():
                    raise MissingRawFile(
                        f"{path} is in the manifest and not on disk. data/raw/ is a CACHE and is "
                        f"NOT disposable (CLAUDE.md, 'Files'); re-fetching it is a new record, "
                        f"not a repair of this one."
                    )
                found = sha256_bytes(path.read_bytes())
                if found != rec.sha256:
                    raise ChecksumMismatch(
                        f"{rec.path}: manifest says {rec.sha256}, the bytes on disk hash to {found}. "
                        f"The file has changed since it was recorded (D191)."
                    )
            out.append(rec)
        out.sort(key=lambda r: (r.fetched_at, _collision_index(r.path), r.path))
        return out

    def jobs_on_disk(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(p.name for p in self.root.iterdir() if p.is_dir() and (p / "_manifest.json").exists())

    # -- health -----------------------------------------------------------------------------
    def append_health(self, line: Mapping[str, object]) -> None:
        append_health(self.health_path, line)


def _checked_name(value: str, what: str) -> str:
    if not isinstance(value, str) or not _NAME_RE.match(value) or "/" in value or "\\" in value:
        raise JobConfigError(
            f"{what} {value!r} must match {_NAME_RE.pattern} — it becomes a directory or a "
            f"filename, and a name that can escape its directory is not a name."
        )
    return value


def _checked_response(got: object) -> tuple[bytes, Mapping[str, str]]:
    """The `fetch` callable's contract, enforced at the door (D399: guard the door, raise)."""
    if not isinstance(got, tuple) or len(got) != 2:
        raise TypeError(f"fetch() must return (bytes, headers); got {type(got).__name__}")
    body, headers = got
    if not isinstance(body, bytes | bytearray):
        raise TypeError(f"fetch() returned a {type(body).__name__} body; the raw response is bytes")
    if not isinstance(headers, Mapping):
        raise TypeError(f"fetch() returned {type(headers).__name__} headers; want a Mapping")
    return bytes(body), headers


_COLLISION_RE = re.compile(r"__\d{8}T\d{6}Z-(\d+)\.")


def _collision_index(path: str) -> int:
    """0 for `k__S.ext`, n for `k__S-n.ext`. See `Recorder.records` on why this is not the
    name's own sort order."""
    m = _COLLISION_RE.search(path)
    return int(m.group(1)) if m else 0


def _free_name(jdir: Path, key: str, stamp: str, ext: str, *, limit: int = 1000) -> str:
    """`{key}__{stamp}.{ext}`, and on a within-second collision `{key}__{stamp}-1.{ext}`, `-2`, …

    The suffix lands on the STAMP, not after the extension, so every file keeps its real
    extension. It does NOT make a plain name sort a fetched_at sort inside one second: `-` is
    0x2D and `.` is 0x2E, so `-1` sorts first. `Recorder.records` sorts on the extracted index
    instead. Across different seconds a name sort is a time sort, because the stamp is fixed
    width and zero padded."""
    for n in range(limit):
        suffix = "" if n == 0 else f"-{n}"
        name = f"{key}__{stamp}{suffix}.{ext}"
        if not (jdir / name).exists():
            return name
    raise OverwriteRefused(f"{limit} records for {key} in the second {stamp}; refusing to guess")


def _write_parsed_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> int:
    """The derived copy (§13A.3's "parsed ... copy"; CSV here, see the module docstring on why not
    Parquet). Every row must carry the same keys in the same order, or the header would be a
    statement about row 0 alone — so a ragged parser RAISES instead of silently dropping columns."""
    if not rows:
        raise JobConfigError("parse() returned no rows; a parsed copy of nothing is not a copy")
    header = list(rows[0].keys())
    if not header:
        raise JobConfigError("parse() returned rows with no columns")
    lines = [",".join(_csv_cell(c) for c in header)]
    for i, row in enumerate(rows):
        if list(row.keys()) != header:
            raise JobConfigError(f"parse() row {i} has keys {list(row.keys())}, row 0 has {header}")
        lines.append(",".join(_csv_cell(row[c]) for c in header))
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return len(rows)


def _csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if any(ch in text for ch in (',', '"', "\n", "\r")):
        return '"' + text.replace('"', '""') + '"'
    return text


# ------------------------------------------------------------------------------------------ Job
@dataclass(frozen=True)
class Job:
    """One recorder job, as declared in `data/recorder/jobs.json`.

      `name`          the directory under `<root>/`, and the key in `GAPS.md`.
      `cadence`       daily | weekly | intraday. `weekly` requires `weekday`.
      `window_et`     ("HH:MM", "HH:MM") ET wall clock, closed-closed, converted through the
                      IANA zone `America/New_York` so DST needs no special case.
      `source_url`    required when `status == "ready"`, forbidden otherwise — a job that cannot
                      name where the bytes come from is not ready, and no URL is ever invented.
      `parser`        the dotted name of a parser, or None. None means the raw response is kept
                      and nothing derived is written.
      `status`        ready | needs_source | needs_key.
      `weekday`       0 = Monday … 6 = Sunday. Required iff cadence == "weekly".
      `window_basis`  WHERE THE TWO CLOCK TIMES CAME FROM. Non-empty, always. A window copied
                      from a source cites it; a window this repository chose says so, so that a
                      declared operational band is never mistaken for a published release clock.
      `frequency`     the deposit's own Frequency cell, verbatim, where the job is one of its ten.
      `content`       the deposit's own Content cell, verbatim.
      `ext`           the raw file's extension.
      `note`          why a job is not ready, or anything that bites a reader of its files.
    """

    name: str
    cadence: Literal["daily", "weekly", "intraday"]
    window_et: tuple[str, str]
    source_url: str | None
    parser: str | None
    status: Literal["ready", "needs_source", "needs_key"]
    weekday: int | None = None
    window_basis: str = ""
    frequency: str = ""
    content: str = ""
    ext: str = "html"
    note: str = ""

    def __post_init__(self) -> None:
        _checked_name(self.name, "job name")
        if self.cadence not in CADENCES:
            raise JobConfigError(f"{self.name}: cadence {self.cadence!r} not in {CADENCES}")
        if self.status not in STATUSES:
            raise JobConfigError(f"{self.name}: status {self.status!r} not in {STATUSES}")
        if not isinstance(self.window_et, tuple) or len(self.window_et) != 2:
            raise JobConfigError(f"{self.name}: window_et must be a 2-tuple, got {self.window_et!r}")
        for t in self.window_et:
            if not _HHMM_RE.match(t):
                raise JobConfigError(f"{self.name}: window time {t!r} is not HH:MM 24-hour ET")
        if _minutes(self.window_et[0]) > _minutes(self.window_et[1]):
            raise JobConfigError(
                f"{self.name}: window {self.window_et[0]}-{self.window_et[1]} ET closes before it "
                f"opens. A window crossing midnight is not supported and is not guessed at."
            )
        if self.status == "ready" and not self.source_url:
            raise JobConfigError(
                f"{self.name}: status 'ready' with no source_url. A job whose URL this repository "
                f"does not hold is 'needs_source' — a URL is never invented."
            )
        if self.status != "ready" and self.source_url:
            raise JobConfigError(f"{self.name}: status {self.status!r} but a source_url is set")
        if (self.cadence == "weekly") != (self.weekday is not None):
            raise JobConfigError(
                f"{self.name}: weekday is required iff cadence == 'weekly' "
                f"(cadence={self.cadence!r}, weekday={self.weekday!r})"
            )
        if self.weekday is not None and not 0 <= self.weekday <= 6:
            raise JobConfigError(f"{self.name}: weekday {self.weekday!r} is not 0..6 (0 = Monday)")
        if not self.window_basis.strip():
            raise JobConfigError(
                f"{self.name}: window_basis is empty. Every clock time says where it came from, so "
                f"a band chosen here is never read as a published release time."
            )
        if not _EXT_RE.match(self.ext):
            raise JobConfigError(f"{self.name}: ext {self.ext!r} is not 1-12 alphanumerics")

    @staticmethod
    def from_dict(raw: Mapping[str, object]) -> Job:
        known = {f for f in Job.__dataclass_fields__}
        unknown = sorted(set(raw) - known - {"_comment"})
        if unknown:
            raise JobConfigError(f"job {raw.get('name')!r} carries unknown keys {unknown}")
        window = raw.get("window_et")
        if not isinstance(window, (list, tuple)) or len(window) != 2:
            raise JobConfigError(f"job {raw.get('name')!r}: window_et must be a 2-element list")
        kwargs = {k: v for k, v in raw.items() if k in known and k != "window_et"}
        return Job(window_et=(str(window[0]), str(window[1])), **kwargs)  # type: ignore[arg-type]

    def window_utc(self, day: dt.date) -> tuple[dt.datetime, dt.datetime]:
        """The ET window on `day`, in UTC. Closed-closed. The close may land on the NEXT UTC date
        (23:00 ET = 03:00 UTC next day) and that is not a special case, it is the conversion."""
        open_et = dt.datetime.combine(day, _hhmm(self.window_et[0]), tzinfo=ET)
        close_et = dt.datetime.combine(day, _hhmm(self.window_et[1]), tzinfo=ET)
        return open_et.astimezone(dt.timezone.utc), close_et.astimezone(dt.timezone.utc)


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _hhmm(hhmm: str) -> dt.time:
    h, m = hhmm.split(":")
    return dt.time(int(h), int(m))


def load_jobs(path: Path) -> list[Job]:
    """`data/recorder/jobs.json` -> the schedule. Raises on a duplicate name or an unknown key."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema") != "recorder-jobs/1":
        raise JobConfigError(f"{path}: want schema 'recorder-jobs/1', got {raw.get('schema') if isinstance(raw, dict) else '?'!r}")
    entries = raw.get("jobs")
    if not isinstance(entries, list) or not entries:
        raise JobConfigError(f"{path}: `jobs` must be a non-empty list")
    jobs = [Job.from_dict(e) for e in entries]
    names = [j.name for j in jobs]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise JobConfigError(f"{path}: duplicate job names {dupes}")
    return jobs


# ----------------------------------------------------------------------------------------- gaps
@dataclass(frozen=True)
class Gap:
    """One window that closed with no record inside it. A hole, and it stays a hole."""

    job: str
    cadence: str
    date_et: str
    window_et: tuple[str, str]
    window_close_utc: str
    reason: str = "no record in window"

    def to_dict(self) -> dict[str, object]:
        return {
            "job": self.job,
            "cadence": self.cadence,
            "date_et": self.date_et,
            "window_et": list(self.window_et),
            "window_close_utc": self.window_close_utc,
            "reason": self.reason,
        }


def check_gaps_scope(jobs: Iterable[Job]) -> dict[str, list[str]]:
    """Which jobs `check_gaps` looks at, and which it does not — named, never implied.

    A gap report that silently omits a job reads exactly like a job with no gaps. The three lists
    partition the jobs: a job that is both not-ready and intraday is reported under
    `not_checked_not_ready`, because not being ready is the earlier reason."""
    checked, intraday, not_ready = [], [], []
    for job in jobs:
        if job.status != "ready":
            not_ready.append(job.name)
        elif job.cadence not in GAP_CHECKED_CADENCES:
            intraday.append(job.name)
        else:
            checked.append(job.name)
    return {
        "checked": sorted(checked),
        "not_checked_intraday": sorted(intraday),
        "not_checked_not_ready": sorted(not_ready),
    }


def check_gaps(
    jobs: Iterable[Job],
    records_by_job: Mapping[str, Sequence[Record]],
    now_utc: dt.datetime,
    *,
    since: dt.date | None = None,
) -> list[Gap]:
    """Every window that has CLOSED without a record inside it, sorted by `(date_et, job)`.

    §13A.3: *"Gap detection: alert if any daily job misses its window."* A window still open is
    not a gap — it is a job that still has time — so a window is only eligible once its close
    instant is at or before `now_utc`.

    `since` is the first ET date to check. Left None it is the earliest ET date on which ANY
    checked job recorded; with no records anywhere the answer is `[]`, because nothing is known to
    have been missed before anything was ever recorded. Pass it explicitly to check from a
    declared start date.

    Nothing in this function, or anywhere in this module, fills a gap.
    """
    now_utc = _assert_aware_utc(now_utc, "now_utc")
    checked = [j for j in jobs if j.status == "ready" and j.cadence in GAP_CHECKED_CADENCES]
    if not checked:
        return []

    if since is None:
        firsts = [
            min(r.fetched_dt for r in records_by_job.get(j.name, ()))
            for j in checked
            if records_by_job.get(j.name)
        ]
        if not firsts:
            return []
        since = min(firsts).astimezone(ET).date()

    last_et = now_utc.astimezone(ET).date()
    if since > last_et:
        raise JobConfigError(f"since {since} is after the ET date of now_utc ({last_et})")

    gaps: list[Gap] = []
    for job in checked:
        stamps = [r.fetched_dt for r in records_by_job.get(job.name, ())]
        day = since
        while day <= last_et:
            if job.cadence == "weekly" and day.weekday() != job.weekday:
                day += dt.timedelta(days=1)
                continue
            opened, closed = job.window_utc(day)
            if closed > now_utc:
                day += dt.timedelta(days=1)
                continue
            if not any(opened <= s <= closed for s in stamps):
                gaps.append(
                    Gap(
                        job=job.name,
                        cadence=job.cadence,
                        date_et=day.isoformat(),
                        window_et=job.window_et,
                        window_close_utc=iso_utc(closed),
                    )
                )
            day += dt.timedelta(days=1)
    gaps.sort(key=lambda g: (g.date_et, g.job))
    return gaps


def gap_line(gap: Gap, logged_utc: str) -> str:
    """One `GAPS.md` row. Seven columns; `logged` is when the line was WRITTEN, which is a
    different fact from the window close — it is how long the gap went unnoticed."""
    assert_iso_z(logged_utc, "logged_utc")
    return (
        f"| {gap.date_et} | {gap.job} | {gap.cadence} | "
        f"{gap.window_et[0]}-{gap.window_et[1]} ET | {gap.window_close_utc} | "
        f"{gap.reason} | {logged_utc} |"
    )


def _gap_key(gap: Gap) -> str:
    return f"| {gap.date_et} | {gap.job} |"


def append_gaps(path: Path, gaps: Sequence[Gap], *, now_utc: dt.datetime | None = None) -> int:
    """APPEND gap lines to `data/recorder/GAPS.md`. Returns how many lines were added.

    Append-only in the strong sense: the existing bytes are read but never rewritten, the file is
    opened `"a"`, and a gap whose `(date_et, job)` key is already present is NOT appended again —
    so a recorder that runs every hour does not turn one missed Thursday into twenty-four lines,
    and the ORIGINAL `logged` column survives, which is the one that says when it was first seen.

    The de-duplication covers the BATCH as well as the file. `check_gaps` cannot emit one window
    twice, but this function is public and the invariant `GAPS.md` offers a reader — one line per
    (date, job) — must not depend on who called it. (A property test found this: the first draft
    deduplicated against the file only, and `append_gaps(path, [g, g])` wrote two lines.)
    """
    logged = iso_utc(now_utc if now_utc is not None else utc_now())
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if not existing:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(GAPS_HEADER)
        existing = GAPS_HEADER
    fresh: list[Gap] = []
    seen: set[str] = set()
    for g in gaps:
        key = _gap_key(g)
        if key in existing or key in seen:
            continue
        seen.add(key)
        fresh.append(g)
    if not fresh:
        return 0
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        for gap in fresh:
            fh.write(gap_line(gap, logged) + "\n")
    return len(fresh)


# --------------------------------------------------------------------------------------- health
@dataclass(frozen=True)
class RunOutcome:
    """One job's result in one pass. `error` is the exception CLASS NAME, never a traceback."""

    job: str
    ok: bool
    error: str | None = None
    detail: str | None = None
    bytes_written: int = 0


@dataclass(frozen=True)
class Run:
    start: str
    end: str
    outcomes: tuple[RunOutcome, ...] = ()
    gaps: tuple[Gap, ...] = ()
    host: str = ""

    @staticmethod
    def begin(now: dt.datetime) -> str:
        return iso_utc(now)


def health_line(run: Run) -> dict[str, object]:
    """The one JSON object appended to `<root>/health.jsonl` per pass.

    §13A.3's hosting clause: *"The recorder must survive reboots and log its own health."* Surviving
    a reboot is the host's job (Q17, the principal's); SAYING SO is this line's. A monitor that can
    read `start`, `attempted` and `failed` off the last line can tell a host that stopped invoking
    the recorder from a recorder that ran and failed — which a silent recorder cannot.
    """
    ok = [o.job for o in run.outcomes if o.ok]
    failed = [
        {"job": o.job, "error": o.error, "detail": (o.detail or "")[:200]}
        for o in run.outcomes
        if not o.ok
    ]
    return {
        "schema": HEALTH_SCHEMA,
        "start": run.start,
        "end": run.end,
        "attempted": len(run.outcomes),
        "ok": len(ok),
        "ok_jobs": ok,
        "failed": failed,
        "bytes": sum(o.bytes_written for o in run.outcomes),
        "gaps": len(run.gaps),
        "host": run.host or platform.node(),
    }


def append_health(path: Path, line: Mapping[str, object]) -> None:
    """One JSON object per line, appended. Never rewritten, LF-pinned (D550), UTF-8."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(line, sort_keys=True) + "\n")


# ----------------------------------------------------------------------------------------- http
class RateLimiter:
    """A floor on the gap between request starts — `scripts/run_futures_acquisition.py:130`,
    unchanged. Not a token bucket: a client that trips a limit and backs off is slower than one
    that never trips it, and ruder."""

    def __init__(self, min_interval: float, *, sleep: Callable[[float], None] | None = None,
                 monotonic: Callable[[], float] | None = None) -> None:
        self.min_interval = float(min_interval)
        self.last = 0.0
        self._sleep = sleep or time.sleep
        self._monotonic = monotonic or time.monotonic

    def wait(self) -> None:
        gap = self._monotonic() - self.last
        if gap < self.min_interval:
            self._sleep(self.min_interval - gap)
        self.last = self._monotonic()


def http_get(
    url: str,
    *,
    timeout: int = TIMEOUT,
    attempts: int = ATTEMPTS,
    limiter: RateLimiter | None = None,
    opener: Callable[..., object] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> tuple[bytes, dict[str, str]]:
    """GET `url` and return `(body, headers)`.

    the retry shape of `_get` in `scripts/fetch_release_calendar.py` (its line 131), unchanged: `attempts` tries, an
    exponential backoff doubling from 3 s, and **a 404 is never retried** — an absent page is an
    answer, and asking four times is rude rather than persistent. The final failure raises
    `RuntimeError` naming the tool and the exception class, per the logged-block rule.

    `opener` and `sleep` are injected so the retry ladder is testable without a network.
    """
    _open = opener or urllib.request.urlopen
    _sleep = sleep or time.sleep
    req = urllib.request.Request(url, headers=UA)
    delay = BACKOFF_SECONDS
    for attempt in range(attempts):
        if limiter is not None:
            limiter.wait()
        try:
            with _open(req, timeout=timeout) as r:  # type: ignore[union-attr]
                body = r.read()
                headers = {str(k).lower(): str(v) for k, v in dict(r.headers).items()}
                return bytes(body), headers
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
                raise
            if attempt == attempts - 1:
                raise RuntimeError(
                    f"GET {url} failed after {attempts} attempts (urllib.request.urlopen): "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            _sleep(delay)
            delay *= 2
    raise RuntimeError(f"GET {url}: attempts={attempts} exhausted without a result")


def fetcher(url: str, **kwargs: object) -> FetchFn:
    """`Recorder.record(..., fetch=fetcher(url))`. The network stays behind a callable so a test
    passes a literal and nothing in `record()` knows the difference."""

    def _fetch() -> tuple[bytes, Mapping[str, str]]:
        return http_get(url, **kwargs)  # type: ignore[arg-type]

    return _fetch
