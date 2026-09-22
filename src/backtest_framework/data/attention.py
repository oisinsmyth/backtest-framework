"""The attention layer — P3.7 of the settlement-flow ledger, D612.

THE SPEC, QUOTED VERBATIM from `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md`
(an untracked, read-only deposit; line numbers are that file's). §3.3c, its line 116:

    Query definitions (keyword lists, article titles, tickers) are fixed in
    `data/attention/QUERIES.md` **before** any feature is computed, and not changed afterwards
    without a doc edit.

§P3.7, its lines 251-252, 255, 261-265 and 267:

    - `news_n(t)`: GDELT article count matching the fixed query in the last 60 min.
      `news_tone(t)`: mean tone of those articles.
    - `wiki_n(h)`: pageviews summed over the fixed article list in the last completed hour.

    **Normalisation:** each series is converted to a z-score against the same hour-of-day and
    day-of-week over the trailing 60 days (prior data only): `z_news`, `z_wiki`, `z_social`.

    | `att_level`      | Mean of available z-scores |
    | `att_accel`      | Change in `att_level` over the last 3 hours vs the prior 3 hours |
    | `att_breadth`    | Count of sources with z > 2 |
    | `headline_burst` | 1 if `z_news` > 3 in any 15-min block since 09:30 |

    **Point-in-time rules:** only data published before t is used. Hourly pageviews enter only
    after the hour completes plus a 15-min publication buffer. GDELT enters with its publication
    timestamp, not the event time.

and the five unit tests it names, §12 items 21-25, its lines 727-731, verbatim:

    21. Attention z-scores on day t use only data from days t-60 ... t-1 for the same hour-of-day
        and day-of-week.
    22. Publication-time guard: an hourly pageview for 13:00-14:00 is unavailable at tau = 14:10
        and available at tau = 14:15 or later.
    23. GDELT items are keyed on publication timestamp; items published after tau are excluded
        even if their event time is earlier.
    24. `att_accel` on a synthetic step increase in attention is positive during the ramp and
        returns to about zero once the level is flat.
    25. Query lists are loaded from `QUERIES.md` and hashed. The hash is stored with every trial
        in `trials.csv`.

WHAT IS HERE AND WHAT IS NOT
----------------------------
Here: the query file's loader and its tamper guard (`load_queries`, `queries_hash`), the two
parsers (`parse_dump_line` for a Wikimedia hourly pageview dump, `parse_gkg_row` for a GDELT GKG
row), the point-in-time guards (`wiki_available_at`, `available`, `zscore_matched`), the four
detector features, and the `trials.csv` row shape that carries the query digest.

NOT here, and each omission is a decision recorded in D612:

  * **No writer of any kind.** This module reads and computes; it never opens a file for writing.
    Every byte fetched for the attention layer is kept by D608's `Recorder`, which is the one
    place in this repository that writes a raw response, and `scripts/fetch_attention.py` routes
    every network read through it. `tests/unit/test_attention.py` asserts this module's namespace
    holds no writer, the same way D608 asserts it holds no `fill_gap`: a guarantee about code
    that does not exist can only be tested as an assertion about the namespace.
  * **No interpolation and no gap filling.** A missing hour in an hourly series is a hole.
    `att_accel` over six hours RAISES when one of the six is absent rather than carrying the
    last value forward, and `zscore_matched` RAISES below a stated minimum of matched
    observations rather than scoring on two.
  * **No social series.** Deposit `:113` and `:253` gate `social_n` on Q12, which is unresolved.
    `QUERIES.md` lists the two social ids as `disabled (Q12)` and this module has no code path
    that would read them.
  * **No feature is computed from Google Trends.** Deposit `:114` excludes it from modelling.

THE DEPOSIT'S LINE 112 IS WRONG AS WRITTEN, and D612 records it as an erratum rather than editing
the deposit. Its 3.3c table says *"Wikimedia hourly pageviews | Hourly, from 2015"*. The Wikimedia
REST per-article endpoint serves **daily and monthly only** -- an hourly request answers HTTP 400,
`granularity should be equal to one of the allowed values: [daily, monthly]`. Per-article hourly
data exists only in the `dumps.wikimedia.org` hourly pageview dumps, one file per hour covering
every project and every article. That is why `parse_dump_line` exists and why there is no
per-article hourly REST reader here.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

__all__ = [
    "ACCEL_HOURS",
    "AttentionError",
    "BREADTH_Z",
    "BURST_SINCE_ET",
    "BURST_Z",
    "GDELT_SLOT",
    "GKG_FIELDS",
    "GdeltItem",
    "InsufficientHistory",
    "LookaheadRefused",
    "MIN_MATCHED_OBS",
    "NO_WRITER_HERE",
    "Query",
    "QuerySet",
    "QueriesMalformed",
    "QueriesTampered",
    "ResolutionRefused",
    "TRIAL_FIELDS",
    "TRAILING_DAYS",
    "TrialRow",
    "WIKI_BUFFER",
    "WikiHourly",
    "att_accel",
    "att_breadth",
    "att_level",
    "available",
    "gdelt_available_at",
    "gkg_haystacks",
    "headline_burst",
    "iter_gkg_rows",
    "load_queries",
    "matched_queries",
    "parse_dump_line",
    "parse_gkg_row",
    "parse_trial_line",
    "queries_hash",
    "refuse_coarse_resolution",
    "slot_datetime",
    "trial_header",
    "trial_line",
    "wiki_available_at",
    "wiki_is_available",
    "zscore_matched",
]

ET = ZoneInfo("America/New_York")

# --------------------------------------------------------------------- the deposit's constants
#: Deposit line 267, "the hour completes plus a 15-min publication buffer".
WIKI_HOUR = dt.timedelta(hours=1)
WIKI_BUFFER = dt.timedelta(minutes=15)

#: One GDELT v2 slot. The raw files arrive every 15 minutes, and the deposit's line 265 counts
#: `z_news` in 15-minute blocks.
GDELT_SLOT = dt.timedelta(minutes=15)

#: Deposit line 255, "the trailing 60 days (prior data only)"; unit test 21 spells the window
#: `t-60 ... t-1`, so both ends are inclusive and day `t` itself is outside it.
TRAILING_DAYS = 60

#: A FLOOR THIS REPOSITORY CHOSE, and it is not the deposit's. 60 days of one weekday-hour is at
#: most ceil(60/7) = 9 observations, so the matched window is small by construction and a z-score
#: over two of them is a ratio of two noisy numbers. Five is the smallest n at which the sample
#: sd has more than a couple of degrees of freedom; below it `zscore_matched` RAISES rather than
#: returning a number nobody should read.
MIN_MATCHED_OBS = 5

#: Deposit line 262, "over the last 3 hours vs the prior 3 hours".
ACCEL_HOURS = 3

#: Deposit line 263, "Count of sources with z > 2". Strictly greater.
BREADTH_Z = 2.0

#: Deposit line 265, "1 if `z_news` > 3 in any 15-min block since 09:30". Strictly greater.
BURST_Z = 3.0

#: Deposit line 265's "since 09:30" — the US cash open, a WALL CLOCK in New York, which is why it
#: is a `datetime.time` and never a UTC offset: 09:30 ET is 13:30 UTC in winter and 14:30 UTC in
#: summer, and a study that hard-codes either is wrong for half the year.
BURST_SINCE_ET = dt.time(9, 30)

#: The 27 tab-separated fields of a GDELT 2.1 GKG row, in order, so that an index in this module
#: is readable rather than a magic number. Verified against the 2019-11-04 00:15 slot, which has
#: exactly 27 fields on every row.
GKG_FIELDS: tuple[str, ...] = (
    "GKGRECORDID",
    "V2.1DATE",
    "V2SOURCECOLLECTIONIDENTIFIER",
    "V2SOURCECOMMONNAME",
    "V2DOCUMENTIDENTIFIER",
    "V1COUNTS",
    "V2.1COUNTS",
    "V1THEMES",
    "V2ENHANCEDTHEMES",
    "V1LOCATIONS",
    "V2ENHANCEDLOCATIONS",
    "V1PERSONS",
    "V2ENHANCEDPERSONS",
    "V1ORGANIZATIONS",
    "V2ENHANCEDORGANIZATIONS",
    "V1.5TONE",
    "V2.1ENHANCEDDATES",
    "V2GCAM",
    "V2.1SHARINGIMAGE",
    "V2.1RELATEDIMAGES",
    "V2.1SOCIALIMAGEEMBEDS",
    "V2.1SOCIALVIDEOEMBEDS",
    "V2.1QUOTATIONS",
    "V2.1ALLNAMES",
    "V2.1AMOUNTS",
    "V2.1TRANSLATIONINFO",
    "V2EXTRASXML",
)
_IDX_DATE = GKG_FIELDS.index("V2.1DATE")
_IDX_URL = GKG_FIELDS.index("V2DOCUMENTIDENTIFIER")
_IDX_THEMES = GKG_FIELDS.index("V1THEMES")
_IDX_TONE = GKG_FIELDS.index("V1.5TONE")
_IDX_EXTRAS = GKG_FIELDS.index("V2EXTRASXML")

NO_WRITER_HERE = (
    "This module never writes a file. Raw responses are kept by "
    "backtest_framework.data.recorder.Recorder (D608) and by nothing else; a derived fixture is "
    "written by scripts/fetch_attention.py. There is no writer in this namespace and there must "
    "never be one."
)
#: Any public name matching this would be a violation of the line above. Asserted in the tests,
#: the shape D608 uses for `fill_gap`: the only public name that may match is the constant that
#: states the rule.
FORBIDDEN_NAME_RE = re.compile(r"write|save|dump_to|upload|post_|put_|persist|store", re.I)

_TITLE_RE = re.compile(rb"<PAGE_TITLE>(.*?)</PAGE_TITLE>", re.S)
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_GKG_STAMP_RE = re.compile(r"^\d{14}$")
_ARTICLE_RE = re.compile(r"^[A-Za-z0-9][\w().,'%\-/]*$")
_PROJECT_RE = re.compile(r"^[a-z]{2,3}(\.[a-z]{1,8})*$")


# ------------------------------------------------------------------------------------- errors
class AttentionError(Exception):
    """Base for every loud failure here. D48: no silent default, ever."""


class QueriesTampered(AttentionError):
    """`QUERIES.md` does not hash to the digest committed beside it. Deposit line 116."""


class QueriesMalformed(AttentionError):
    """`QUERIES.md` is missing a section, a column, or holds a value this module cannot read."""


class LookaheadRefused(AttentionError):
    """An input carried information from at or after the instant being scored."""


class InsufficientHistory(AttentionError):
    """Fewer matched observations than `MIN_MATCHED_OBS`, or a hole in an hourly window."""


class ResolutionRefused(AttentionError):
    """A GDELT DOC-API response is coarser than the 15 minutes the deposit's features need."""


def _aware_utc(when: dt.datetime, what: str) -> dt.datetime:
    if not isinstance(when, dt.datetime):
        raise AttentionError(f"{what} must be a datetime, got {type(when).__name__}")
    if when.tzinfo is None:
        raise AttentionError(f"{what} is naive: {when!r}. Every instant here is tz-aware UTC.")
    return when.astimezone(dt.timezone.utc)


# ------------------------------------------------------------------------------- the query file
@dataclass(frozen=True)
class Query:
    """One fixed query from `QUERIES.md` §2b. Frozen: a query definition is not editable in place.

    `qid`        the stable id, used as the fixture's `key` and as a `matched_queries` member.
    `kind`       phrase | theme | ticker. Decides which haystacks the literal is looked for in.
    `literal`    lowercased for phrase and ticker; the exact uppercase token for a theme.
    `precision`  high | low, copied from the file. `low` travels with every row it produces.
    """

    qid: str
    kind: Literal["phrase", "theme", "ticker"]
    literal: str
    precision: Literal["high", "low"]

    @property
    def fields(self) -> tuple[str, ...]:
        return _FIELDS_BY_KIND[self.kind]


#: WHICH HAYSTACKS EACH KIND IS LOOKED FOR IN. This is code's copy of a rule whose prose lives in
#: `QUERIES.md` §2b's `rule` column, and the two are cross-checked at load time rather than left
#: to drift: `load_queries` asserts that each row's prose mentions the fields named here, and
#: raises `QueriesMalformed` when it does not. Two copies of one fact is this repository's most
#: repeated defect; a copy that is checked against its original is not one.
_FIELDS_BY_KIND: dict[str, tuple[str, ...]] = {
    "phrase": ("title", "url"),
    "theme": ("themes",),
    "ticker": ("title",),
}
_RULE_MUST_MENTION: dict[str, tuple[str, ...]] = {
    "phrase": ("title", "url"),
    "theme": ("V1THEMES",),
    "ticker": ("title only",),
}


@dataclass(frozen=True)
class QuerySet:
    """Everything `QUERIES.md` fixes, plus the digest of the bytes it was read from."""

    path: str
    sha256: str
    articles: tuple[str, ...]
    unresolved: tuple[str, ...]
    excluded: tuple[str, ...]
    projects: tuple[str, ...]
    queries: tuple[Query, ...]
    social_disabled: tuple[str, ...]

    def query(self, qid: str) -> Query:
        for q in self.queries:
            if q.qid == qid:
                return q
        raise QueriesMalformed(f"no query {qid!r} in {self.path}")


def _normalise_newlines(body: bytes) -> bytes:
    """CRLF and lone CR to LF — the same one transform `validation/frozen.py` applies before
    hashing text, and for the same reason (D550/D551): `QUERIES.md` is text, so its identity must
    be a fact about its content rather than about a checkout's newline policy."""
    return body.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def queries_hash(path: str | Path) -> str:
    """sha256 of `QUERIES.md` with newlines pinned to LF. Deposit line 116's enforcement."""
    p = Path(path)
    if not p.is_file():
        raise QueriesMalformed(f"not a file: {p}")
    return hashlib.sha256(_normalise_newlines(p.read_bytes())).hexdigest()


def load_queries(path: str | Path, *, sha_path: str | Path | None = None) -> QuerySet:
    """Parse `QUERIES.md` and verify its digest against `QUERIES.sha256`.

    `sha_path` defaults to the query file's own name with `.sha256` in place of `.md`. A digest
    file that is absent RAISES: the deposit's line 116 is about a file that cannot be changed
    quietly, and a missing digest is exactly the state in which it can be.

    Every failure below raises. Nothing is defaulted, nothing is skipped, and an unreadable table
    is not treated as an empty one — an empty article list would make every downstream count zero
    and every gate pass, which is the failure mode six gates in this repository have already had.
    """
    p = Path(path)
    found = queries_hash(p)
    sp = Path(sha_path) if sha_path is not None else p.with_suffix(".sha256")
    if not sp.is_file():
        raise QueriesTampered(
            f"{p.name} has no committed digest at {sp}. Deposit line 116 fixes the query "
            f"definitions before any feature is computed; a query file with no digest beside it "
            f"is a query file that can be edited without anyone noticing."
        )
    want = sp.read_text(encoding="utf-8").split()[0].strip().lower()
    if want != found:
        raise QueriesTampered(
            f"{p.name} hashes to {found}, {sp.name} says {want}. The query definitions have "
            f"changed since the digest was written (deposit line 116: 'not changed afterwards "
            f"without a doc edit'). A doc edit rewrites BOTH files."
        )

    text = _normalise_newlines(p.read_bytes()).decode("utf-8")
    articles = _column(text, "1a.", "article", p)
    unresolved = _column(text, "1b.", "candidate", p)
    excluded = _column(text, "1c.", "candidate", p)
    projects = _projects(text, p)
    queries = _queries_table(text, p)
    social = _column(text, "3. Social", "id", p)

    if not articles:
        raise QueriesMalformed(f"{p}: §1a lists no article. A set that matches nothing is not a set.")
    if not projects:
        raise QueriesMalformed(f"{p}: §1d names no dump project.")
    if not queries:
        raise QueriesMalformed(f"{p}: §2b lists no query.")
    _no_duplicates(articles, "§1a article", p)
    _no_duplicates(projects, "§1d project", p)
    _no_duplicates([q.qid for q in queries], "§2b query id", p)
    overlap = sorted(set(articles) & (set(unresolved) | set(excluded)))
    if overlap:
        raise QueriesMalformed(
            f"{p}: {overlap} is listed both as in the article list and as unresolved/excluded. "
            f"An article is in the series or it is not."
        )
    for a in articles + unresolved + excluded:
        if not _ARTICLE_RE.match(a):
            raise QueriesMalformed(f"{p}: {a!r} is not a plausible en.wikipedia title")
    for proj in projects:
        if not _PROJECT_RE.match(proj):
            raise QueriesMalformed(f"{p}: {proj!r} is not a dump project code")

    return QuerySet(
        path=str(p),
        sha256=found,
        articles=tuple(articles),
        unresolved=tuple(unresolved),
        excluded=tuple(excluded),
        projects=tuple(projects),
        queries=tuple(queries),
        social_disabled=tuple(social),
    )


def _section(text: str, anchor: str, path: Path) -> str:
    """The body of the first heading whose text contains `anchor`, up to the next heading of the
    same or a shallower depth. Raises when the anchor is absent — a section that has been renamed
    must break the loader loudly, because the alternative is a silently empty list."""
    lines = text.split("\n")
    start = None
    depth = 0
    for i, line in enumerate(lines):
        if line.startswith("#") and anchor in line:
            start = i + 1
            depth = len(line) - len(line.lstrip("#"))
            break
    if start is None:
        raise QueriesMalformed(f"{path}: no heading containing {anchor!r}")
    out = []
    for line in lines[start:]:
        if line.startswith("#"):
            here = len(line) - len(line.lstrip("#"))
            if here <= depth:
                break
        out.append(line)
    return "\n".join(out)


def _tables(body: str) -> list[list[dict[str, str]]]:
    """Every pipe table in `body`, each as a list of row dicts keyed on its own header cells."""
    tables: list[list[dict[str, str]]] = []
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in body.split("\n"):
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s[1:-1].split("|")]
            if header is None:
                header = [c.lower() for c in cells]
                rows = []
                continue
            if all(set(c) <= set("-: ") for c in cells) and cells:
                continue
            if len(cells) == len(header):
                rows.append(dict(zip(header, cells, strict=True)))
            continue
        if header is not None:
            tables.append(rows)
            header, rows = None, []
    if header is not None:
        tables.append(rows)
    return tables


def _unbacktick(cell: str) -> str:
    m = re.search(r"`([^`]+)`", cell)
    return m.group(1) if m else cell.strip()


def _rows(text: str, anchor: str, path: Path) -> list[dict[str, str]]:
    tables = _tables(_section(text, anchor, path))
    if not tables or not tables[0]:
        raise QueriesMalformed(f"{path}: section {anchor!r} has no table rows")
    return tables[0]


def _column(text: str, anchor: str, column: str, path: Path) -> list[str]:
    """The backticked value of `column` in the first table of the section named by `anchor`,
    in file order. A missing column raises rather than yielding an empty list."""
    rows = _rows(text, anchor, path)
    if column not in rows[0]:
        raise QueriesMalformed(
            f"{path}: section {anchor!r} table has columns {sorted(rows[0])}, wanted {column!r}"
        )
    return [v for v in (_unbacktick(row[column]) for row in rows) if v]


def _projects(text: str, path: Path) -> list[str]:
    """§1d's project table: the dump project codes whose lines are SUMMED into `wiki_n`.

    Every row must say `yes` or `no` in the second column, and only the `yes` rows are summed. A
    `no` row is kept in the file and dropped here — which is what makes this a filter that can
    fire, rather than a loop over a table that happens to be all-yes today.
    """
    rows = _rows(text, "1d.", path)
    keys = [k for k in rows[0] if k != "project"]
    if "project" not in rows[0] or len(keys) != 1:
        raise QueriesMalformed(
            f"{path}: §1d wants a two-column table `project | summed into wiki_n`, got "
            f"{sorted(rows[0])}"
        )
    flag = keys[0]
    out: list[str] = []
    for row in rows:
        decision = _unbacktick(row[flag]).strip().lower().strip("*")
        if decision not in ("yes", "no"):
            raise QueriesMalformed(
                f"{path}: §1d row {row['project']!r} says {row[flag]!r}; want exactly yes or no"
            )
        if decision == "yes":
            out.append(_unbacktick(row["project"]))
    return out


def _queries_table(text: str, path: Path) -> list[Query]:
    tables = _tables(_section(text, "2b.", path))
    if not tables or not tables[0]:
        raise QueriesMalformed(f"{path}: §2b has no table rows")
    out: list[Query] = []
    for row in tables[0]:
        for col in ("id", "kind", "literal", "rule", "precision"):
            if col not in row:
                raise QueriesMalformed(f"{path}: §2b row is missing column {col!r}: {row}")
        kind = _unbacktick(row["kind"]).strip().lower()
        if kind not in _FIELDS_BY_KIND:
            raise QueriesMalformed(f"{path}: §2b kind {kind!r} not in {sorted(_FIELDS_BY_KIND)}")
        precision = _unbacktick(row["precision"]).strip().lower().strip("*")
        if precision not in ("high", "low"):
            raise QueriesMalformed(f"{path}: §2b precision {precision!r} is not high|low")
        rule = row["rule"]
        missing = [w for w in _RULE_MUST_MENTION[kind] if w.lower() not in rule.lower()]
        if missing:
            raise QueriesMalformed(
                f"{path}: §2b row {row['id']!r} is kind {kind!r}, which this module matches on "
                f"{_FIELDS_BY_KIND[kind]}, but its rule column never mentions {missing}. The "
                f"file's prose and the code's mapping disagree; one of them is wrong."
            )
        literal = _unbacktick(row["literal"])
        out.append(
            Query(
                qid=_unbacktick(row["id"]),
                kind=kind,  # type: ignore[arg-type]
                literal=literal if kind == "theme" else literal.lower(),
                precision=precision,  # type: ignore[arg-type]
            )
        )
    return out


def _no_duplicates(values: Sequence[str], what: str, path: Path) -> None:
    dupes = sorted({v for v in values if list(values).count(v) > 1})
    if dupes:
        raise QueriesMalformed(f"{path}: duplicate {what} {dupes}")


# ------------------------------------------------------------------------ Wikimedia hourly dumps
@dataclass(frozen=True)
class WikiHourly:
    """One line of a `dumps.wikimedia.org` hourly pageview file, keyed on the hour it covers.

    `hour_start_utc` is the START of the hour the file is named for: `pageviews-20191104-130000.gz`
    holds the hour 13:00:00Z .. 14:00:00Z, and this field is 13:00:00Z. The file is not available
    at 13:00 — see `wiki_available_at`, which is the whole of unit test 22.
    """

    article: str
    project: str
    hour_start_utc: dt.datetime
    views: int


def parse_dump_line(line: bytes, hour_start_utc: dt.datetime) -> WikiHourly:
    """`b"en Natural_gas 42 0"` -> `WikiHourly`. Raises on anything else.

    The dump's line format is `<project> <article> <views> <bytes_returned>`, space separated,
    where `bytes_returned` has been the literal `0` since 2015 and is not read. The article is
    kept EXACTLY as the dump spells it: the dump resolves no redirects and neither does this.
    """
    if not isinstance(line, bytes | bytearray):
        raise AttentionError(f"parse_dump_line wants bytes, got {type(line).__name__}")
    parts = bytes(line).strip().split(b" ")
    if len(parts) != 4:
        raise AttentionError(
            f"a pageview dump line has 4 space-separated fields, this one has {len(parts)}: "
            f"{bytes(line)[:120]!r}"
        )
    try:
        views = int(parts[2])
    except ValueError as exc:
        raise AttentionError(f"views field {parts[2]!r} is not an integer: {exc}") from exc
    if views < 0:
        raise AttentionError(f"views field is negative ({views}) in {bytes(line)[:120]!r}")
    return WikiHourly(
        article=parts[1].decode("utf-8", "surrogateescape"),
        project=parts[0].decode("ascii", "strict"),
        hour_start_utc=_aware_utc(hour_start_utc, "hour_start_utc"),
        views=views,
    )


def wiki_available_at(hour_start_utc: dt.datetime) -> dt.datetime:
    """**When an hourly pageview count may first be used.** Deposit line 267, verbatim: *"Hourly
    pageviews enter only after the hour completes plus a 15-min publication buffer."*

        available_at = hour_start + 1 hour + 15 minutes

    Unconditional, with no branch in it. The 13:00-14:00 hour is available at 14:15:00Z and at no
    earlier instant, which is unit test 22. A rule with a branch is a rule that can take the wrong
    branch, and the wrong branch here is a look-ahead (R9).
    """
    return _aware_utc(hour_start_utc, "hour_start_utc") + WIKI_HOUR + WIKI_BUFFER


def wiki_is_available(hour_start_utc: dt.datetime, tau: dt.datetime) -> bool:
    """True iff `tau` is at or after `wiki_available_at(hour_start_utc)`.

    `>=` and not `>`: the buffer is stated as a duration to wait, so the instant the wait ends the
    datum is usable. Test 22 says *"available at tau = 14:15 or later"*, which is the same word.
    """
    return _aware_utc(tau, "tau") >= wiki_available_at(hour_start_utc)


# -------------------------------------------------------------------------------- GDELT GKG rows
@dataclass(frozen=True)
class GdeltItem:
    """One GKG document.

    `publication_ts` is **the file slot's own timestamp**, which is what the deposit's line 267
    means by *"GDELT enters with its publication timestamp, not the event time"*. `event_ts` is
    what the accompanying `export` file dates the underlying EVENT to, and it is carried for the
    record and used by nothing: `available()` never looks at it, which is unit test 23.
    """

    publication_ts: dt.datetime
    event_ts: dt.datetime | None
    tone: float | None
    source_url: str
    matched_queries: tuple[str, ...]


def slot_datetime(stamp: str) -> dt.datetime:
    """`"20191104001500"` -> 2019-11-04 00:15:00+00:00. GDELT v2 stamps are UTC."""
    if not _GKG_STAMP_RE.match(stamp):
        raise AttentionError(f"{stamp!r} is not a 14-digit GDELT v2 slot stamp")
    return dt.datetime.strptime(stamp, "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)


def gdelt_available_at(slot_utc: dt.datetime) -> dt.datetime:
    """**When a GDELT slot file may first be read — one full slot after its stamp.**

    THIS IS NOT THE DEPOSIT'S RULE AND IT IS NOT PRETENDING TO BE. The deposit's rule is about an
    ITEM (line 267: keyed on its publication timestamp, which `available()` implements literally
    and unit test 23 pins). This function answers a different question, the operational one: the
    file named `20191104001500.gkg.csv.zip` is posted to `data.gdeltproject.org` some time AFTER
    00:15, and this repository has not measured how long after. **One full slot is a declared
    conservative stand-in** — never optimistic, in the same shape as line 267's own 15-minute
    buffer for pageviews — and the sample fixture's `available_at_utc` column uses it so that the
    column is a time this repository could actually have read the bytes.

    The measured posting lag is an open item in the D612 record. If it is ever measured this
    constant is replaced by the measurement, not by a guess in the other direction.
    """
    return _aware_utc(slot_utc, "slot_utc") + GDELT_SLOT


def gkg_haystacks(fields: Sequence[bytes]) -> tuple[str, str, frozenset[str]]:
    """`(title, url, themes)` for one GKG row, normalised as `QUERIES.md` §2b defines it.

    Title and url are lowercased, every run of characters outside `[a-z0-9]` becomes one space,
    and the result is padded with one leading and one trailing space, so a whole-phrase test is a
    plain substring test for `" natural gas "`. Themes are exact uppercase tokens.
    """
    if len(fields) < len(GKG_FIELDS):
        raise AttentionError(
            f"a GKG row has {len(GKG_FIELDS)} tab fields, this one has {len(fields)}"
        )
    m = _TITLE_RE.search(bytes(fields[_IDX_EXTRAS]))
    title = (m.group(1) if m else b"").decode("utf-8", "replace")
    url = bytes(fields[_IDX_URL]).decode("utf-8", "replace")
    themes = frozenset(
        t.decode("ascii", "replace")
        for t in bytes(fields[_IDX_THEMES]).split(b";")
        if t
    )
    return _norm(title), _norm(url), themes


def _norm(text: str) -> str:
    return " " + _NON_ALNUM.sub(" ", text.lower()).strip() + " "


def matched_queries(
    title: str, url: str, themes: frozenset[str], queries: Iterable[Query]
) -> tuple[str, ...]:
    """Which queries this document matches, in the order `QUERIES.md` lists them.

    A document matches a query **at most once**, so a count of these is a DOCUMENT count and never
    a mention count — which is what the deposit's line 251 asks for.
    """
    out: list[str] = []
    for q in queries:
        if q.kind == "theme":
            hit = q.literal in themes
        elif q.kind == "phrase":
            needle = " " + q.literal + " "
            hit = needle in title or needle in url
        else:  # ticker: title only, per QUERIES.md §2b and the reason stated there
            hit = (" " + q.literal + " ") in title
        if hit:
            out.append(q.qid)
    return tuple(out)


#: A GKG record's first field, `GKGRECORDID`: the 14-digit slot stamp, a hyphen, an optional `T`
#: for a translingual record, and the record's index in the slot, followed by the first tab.
_GKG_ID_RE = re.compile(rb"^\d{14}-T?\d+\t")


def iter_gkg_rows(blob: bytes) -> list[bytes]:
    """Split a GKG file into RECORDS. **A record is not a line.**

    Found by running this on the 2019-11-04 12:15 slot: `V2EXTRASXML` carries `<PAGE_LINKS>`
    verbatim from the source page, and a source page's link list can contain a raw newline. A
    `blob.split(b"\\n")` therefore hands back fragments like
    `b'&HomeUrl=http://patft.uspto.gov/netacgi/nph-Parser?...'` with one tab field, and a parser
    that trusts the line delimiter either raises on them (which is what happened) or, worse,
    silently skips them and undercounts.

    The real record boundary is `GKGRECORDID`, so a line that does not begin one is a
    continuation and is joined back on with the newline it was split at — the record is
    reassembled byte for byte. A file whose first line is not a record id RAISES: that is not a
    GKG file and guessing where it starts would be inventing data.
    """
    lines = bytes(blob).split(b"\n")
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return []
    if not _GKG_ID_RE.match(lines[0]):
        raise AttentionError(
            f"a GKG file's first line must begin with a GKGRECORDID (14 digits, '-', an index); "
            f"this one begins {lines[0][:80]!r}"
        )
    out: list[bytes] = []
    cur: list[bytes] = []
    for line in lines:
        if _GKG_ID_RE.match(line):
            if cur:
                out.append(b"\n".join(cur))
            cur = [line]
        else:
            cur.append(line)
    if cur:
        out.append(b"\n".join(cur))
    return out


def parse_gkg_row(row: bytes, queries: Sequence[Query]) -> GdeltItem | None:
    """One tab-separated GKG line -> a `GdeltItem`, or None when it matches no query.

    `publication_ts` is taken from field `V2.1DATE`, which is the slot's own stamp. `event_ts` is
    left None here: the GKG file carries no event date, and the one that does — the `export`
    file's `SQLDATE` — is a different file with a different key. Inventing an event time from the
    publication stamp would make unit test 23 untestable by making the two always equal.
    """
    fields = bytes(row).rstrip(b"\r\n").split(b"\t")
    if len(fields) < len(GKG_FIELDS):
        raise AttentionError(
            f"a GKG row has {len(GKG_FIELDS)} tab fields, this one has {len(fields)}: "
            f"{bytes(row)[:120]!r}"
        )
    title, url, themes = gkg_haystacks(fields)
    hits = matched_queries(title, url, themes, queries)
    if not hits:
        return None
    return GdeltItem(
        publication_ts=slot_datetime(fields[_IDX_DATE].decode("ascii", "replace")),
        event_ts=None,
        tone=_first_tone(fields[_IDX_TONE]),
        source_url=fields[_IDX_URL].decode("utf-8", "replace"),
        matched_queries=hits,
    )


def _first_tone(cell: bytes) -> float | None:
    """The first comma-component of `V1.5TONE` — the document tone. An empty or unparseable cell
    is None and NEVER 0.0: a zero tone is neutral coverage, an absent tone is no measurement, and
    collapsing the second into the first biases every mean that reads it toward neutral."""
    head = bytes(cell).split(b",")[0].strip()
    if not head:
        return None
    try:
        value = float(head)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def available(items: Sequence[GdeltItem], tau: dt.datetime) -> tuple[GdeltItem, ...]:
    """**The items a model at `tau` may see: those whose PUBLICATION is at or before `tau`.**

    Deposit line 267: *"GDELT enters with its publication timestamp, not the event time."* Unit
    test 23: *"items published after tau are excluded even if their event time is earlier."*

    `event_ts` is not read by this function. It is not compared, not maximised against, and not
    used as a fallback when `publication_ts` is missing — `publication_ts` cannot be missing,
    because `GdeltItem` has no default for it. An item whose event predates `tau` by a year and
    whose publication is one second after it is excluded.
    """
    t = _aware_utc(tau, "tau")
    out: list[GdeltItem] = []
    for i, item in enumerate(items):
        if not isinstance(item, GdeltItem):
            raise AttentionError(f"items[{i}] is a {type(item).__name__}, not a GdeltItem")
        if _aware_utc(item.publication_ts, "publication_ts") <= t:
            out.append(item)
    return tuple(out)


def refuse_coarse_resolution(date_resolution: object) -> str:
    """Raise unless a DOC 2.0 response's `query_details.date_resolution` is 15 minutes or finer.

    The API autoscales its bucket width with the span asked for and reports the width it chose.
    The deposit's features are a 60-minute count (line 251) built out of 15-minute blocks (line
    265), so an hourly bucket is not a coarser version of the right number, it is a different
    number. `--gdelt-doc` refuses it rather than recording it as a feature value.
    """
    text = str(date_resolution).strip().lower()
    if text in ("15min", "15 min", "15 minutes", "15m", "quarterhour", "quarter hour"):
        return text
    if text in ("min", "minute", "1min", "1 minute"):
        return text
    raise ResolutionRefused(
        f"query_details.date_resolution is {date_resolution!r}. The deposit's news_n is a "
        f"60-minute count over 15-minute blocks (lines 251, 265); anything coarser than 15 "
        f"minutes is a different statistic and is not recorded as a feature value. The "
        f"historical route is the raw 15-minute files, not this API."
    )


# --------------------------------------------------------------------------------- the z-score
def zscore_matched(
    observations: Sequence[tuple[dt.date, int, float]],
    day: dt.date,
    hour: int,
    *,
    trailing_days: int = TRAILING_DAYS,
    min_obs: int = MIN_MATCHED_OBS,
) -> float:
    """z of `day`'s own value at `hour`, against the SAME hour-of-day and weekday over the trailing
    `trailing_days` days, using prior data only.

    Deposit line 255 and unit test 21. `observations` is `(day, hour, value)`; the value scored is
    the one dated `day` at `hour`, and the reference set is every observation with

        obs.hour == hour   and   obs.day.weekday() == day.weekday()
        and   day - trailing_days <= obs.day <= day - 1

    **Any observation dated at or after `day` RAISES `LookaheadRefused`.** It is not filtered.
    Filtering is indistinguishable from a window that never had one, and R9 is this repository's
    record of what that costs: a 465-point monotone relationship that vanished entirely once the
    conditioner was lagged by one bar, in a script that had no look-ahead guard because nobody
    thought a descriptive cut needed one. The single exception is the observation for `day` at
    `hour` itself, which is the value being SCORED and must be supplied.

    An observation older than the window is DROPPED, not an error — it is not a leak, it is old.

    The denominator is the SAMPLE standard deviation (ddof = 1). The deposit says "z-score" and
    does not say which; the choice and its size are written out in
    `tests/golden/test_attention_ledger.hand.txt`, Case 2.
    """
    if not isinstance(day, dt.date) or isinstance(day, dt.datetime):
        raise AttentionError(f"day must be a datetime.date, got {type(day).__name__}")
    if not 0 <= int(hour) <= 23:
        raise AttentionError(f"hour {hour!r} is not 0..23")
    if trailing_days < 1:
        raise AttentionError(f"trailing_days must be >= 1, got {trailing_days}")

    first = day - dt.timedelta(days=trailing_days)
    scored: float | None = None
    matched: list[float] = []
    for i, obs in enumerate(observations):
        if not isinstance(obs, tuple) or len(obs) != 3:
            raise AttentionError(f"observations[{i}] must be (day, hour, value), got {obs!r}")
        obs_day, obs_hour, value = obs
        if not isinstance(obs_day, dt.date) or isinstance(obs_day, dt.datetime):
            raise AttentionError(f"observations[{i}][0] must be a date, got {type(obs_day).__name__}")
        v = float(value)
        if not math.isfinite(v):
            raise AttentionError(f"observations[{i}] value {value!r} is not finite")
        if obs_day == day and int(obs_hour) == int(hour):
            if scored is not None:
                raise AttentionError(f"two observations for the scored instant {day} {hour:02d}")
            scored = v
            continue
        if obs_day >= day:
            raise LookaheadRefused(
                f"observations[{i}] is dated {obs_day}, at or after the scored day {day}. The "
                f"z-score window is days t-{trailing_days} to t-1 (deposit line 255, unit test "
                f"21); an observation from the present is not filtered here, it is refused."
            )
        if int(obs_hour) != int(hour) or obs_day.weekday() != day.weekday():
            continue
        if obs_day < first:
            continue
        matched.append(v)

    if scored is None:
        raise AttentionError(
            f"no observation for the scored instant {day} hour {hour:02d}; there is nothing to "
            f"score against the matched window."
        )
    if len(matched) < min_obs:
        raise InsufficientHistory(
            f"{len(matched)} matched observations for {day} hour {hour:02d} (same hour-of-day and "
            f"weekday in the prior {trailing_days} days), below the stated minimum of {min_obs}. "
            f"A z-score over {len(matched)} points is a ratio of two noisy numbers."
        )
    n = len(matched)
    mean = math.fsum(matched) / n
    var = math.fsum((x - mean) ** 2 for x in matched) / (n - 1)
    sd = math.sqrt(var)
    if sd == 0.0:
        raise InsufficientHistory(
            f"the {n} matched observations for {day} hour {hour:02d} are all {mean}; a z-score "
            f"has no denominator. This is a constant series, not a quiet one."
        )
    return (scored - mean) / sd


# ------------------------------------------------------------------------------- the features
def att_level(zs: Mapping[str, float]) -> float:
    """Deposit line 261: *"Mean of available z-scores"*.

    `zs` maps a SOURCE name (`news`, `wiki`, `social`) to its z. A source with no data is absent
    from the mapping and contributes nothing — it does not contribute a zero, because a zero z is
    "exactly average attention" and an absent source is "no measurement". An empty mapping raises.
    """
    values = [float(v) for v in zs.values()]
    for name, v in zs.items():
        if not math.isfinite(float(v)):
            raise AttentionError(f"z for source {name!r} is not finite: {v!r}")
    if not values:
        raise InsufficientHistory("att_level over no available z-scores; there is no mean of none")
    return math.fsum(values) / len(values)


def att_accel(levels_by_hour: Mapping[dt.datetime, float], hour: dt.datetime) -> float:
    """Deposit line 262: *"Change in `att_level` over the last 3 hours vs the prior 3 hours"*.

        accel(h) = mean(level[h-2], level[h-1], level[h]) - mean(level[h-5], level[h-4], level[h-3])

    All six hours must be present. A missing hour RAISES `InsufficientHistory` rather than being
    carried forward or interpolated: the series is hourly, a hole is a hole, and D608's
    `data/recorder/GAPS.md` exists so that holes stay holes.

    On a constant series the two means are computed from the same doubles in the same order, so
    the result is EXACTLY 0.0 — no tolerance needed, and a rewrite that reorders the sum breaks it.
    """
    h = _aware_utc(hour, "hour")
    span = 2 * ACCEL_HOURS
    wanted = [h - dt.timedelta(hours=k) for k in range(span - 1, -1, -1)]
    keys = {_aware_utc(k, "levels_by_hour key"): float(v) for k, v in levels_by_hour.items()}
    missing = [w.isoformat() for w in wanted if w not in keys]
    if missing:
        raise InsufficientHistory(
            f"att_accel at {h.isoformat()} needs the {span} hours {wanted[0].isoformat()}.."
            f"{wanted[-1].isoformat()}; {len(missing)} are absent: {missing}. A missing hour is "
            f"not interpolated."
        )
    values = [keys[w] for w in wanted]
    for v in values:
        if not math.isfinite(v):
            raise AttentionError(f"att_accel: a level in the window is not finite ({v})")
    prior = values[:ACCEL_HOURS]
    last = values[ACCEL_HOURS:]
    return math.fsum(last) / ACCEL_HOURS - math.fsum(prior) / ACCEL_HOURS


def att_breadth(zs: Mapping[str, float], *, threshold: float = BREADTH_Z) -> int:
    """Deposit line 263: *"Count of sources with z > 2"*. Strictly greater, and only over sources
    that are PRESENT: a disabled source (`social`, gated on Q12) has no z and cannot be counted,
    so the reachable maximum is the number of live sources rather than three."""
    for name, v in zs.items():
        if not math.isfinite(float(v)):
            raise AttentionError(f"z for source {name!r} is not finite: {v!r}")
    return sum(1 for v in zs.values() if float(v) > threshold)


def headline_burst(
    z_news_by_block: Mapping[dt.datetime, float],
    day_et: dt.date,
    *,
    since: dt.time = BURST_SINCE_ET,
    tau: dt.datetime | None = None,
    threshold: float = BURST_Z,
) -> int:
    """Deposit line 265: *"1 if `z_news` > 3 in any 15-min block since 09:30"*.

    `since` is a NEW YORK wall clock, so `day_et` says which ET day's 09:30 is meant and the UTC
    instant is derived through `America/New_York`. 09:30 ET is 13:30 UTC in winter and 14:30 UTC
    in summer; a constant offset is wrong for half the year.

    `tau` caps the scan: a block at or before `tau` may be read, a block after it may not. Left
    None every block in the mapping is scanned, which is the historical case where the mapping has
    already been truncated by the caller.
    """
    start = dt.datetime.combine(day_et, since, tzinfo=ET).astimezone(dt.timezone.utc)
    cap = _aware_utc(tau, "tau") if tau is not None else None
    for block, z in z_news_by_block.items():
        b = _aware_utc(block, "z_news_by_block key")
        if b < start:
            continue
        if cap is not None and b > cap:
            continue
        zz = float(z)
        if not math.isfinite(zz):
            raise AttentionError(f"z_news at {b.isoformat()} is not finite: {z!r}")
        if zz > threshold:
            return 1
    return 0


# -------------------------------------------------------------------------------- trials.csv
#: The settlement-flow document's own `trials.csv` columns, its line 700, verbatim —
#:
#:   trial_id, timestamp, instrument, stage, timing_rule, t0, fill_model, cost_mult, flag_filter,
#:   sizing, n_trades, flow_corr_oos, mean_gross, mean_net, t_clustered, sharpe_net, notes
#:
#: plus TWO provenance columns. `frozen_sha256` is spelled exactly as `validation/track3.py`'s
#: `TradeRow` spells it (D605), so the two logs join without a rename. `queries_sha256` is unit
#: test 25's requirement — *"The hash is stored with every trial in `trials.csv`"* — and it sits
#: beside `frozen_sha256` because they answer the same question about two different objects: what
#: code ran, and what it was asked to count.
TRIAL_FIELDS: tuple[str, ...] = (
    "trial_id",
    "timestamp",
    "instrument",
    "model",
    "stage",
    "frozen_sha256",
    "queries_sha256",
    "timing_rule",
    "t0",
    "fill_model",
    "cost_mult",
    "flag_filter",
    "sizing",
    "n_trades",
    "flow_corr_oos",
    "mean_gross",
    "mean_net",
    "t_clustered",
    "sharpe_net",
    "notes",
)
_TRIAL_REQUIRED = ("trial_id", "timestamp", "instrument", "model", "stage", "frozen_sha256", "queries_sha256")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class TrialRow:
    """One row of `results/settlement_flow/trials.csv`. **D612 writes none.**

    This is the SHAPE, declared here so that unit test 25 has an object to assert against and so
    that whichever runner eventually logs a trial cannot forget the query digest: `queries_sha256`
    has no default, so a row built without it does not construct.

    Everything after `stage` is a string, including the numeric cells, because a trial log is a
    record of what was run rather than a numeric fixture — and because a float rendered by two
    different writers is two different strings, which is the drift a log exists to prevent.
    """

    trial_id: str
    timestamp: str
    instrument: str
    model: str
    stage: str
    frozen_sha256: str
    queries_sha256: str
    timing_rule: str = ""
    t0: str = ""
    fill_model: str = ""
    cost_mult: str = ""
    flag_filter: str = ""
    sizing: str = ""
    n_trades: str = ""
    flow_corr_oos: str = ""
    mean_gross: str = ""
    mean_net: str = ""
    t_clustered: str = ""
    sharpe_net: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        for name in _TRIAL_REQUIRED:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise AttentionError(f"TrialRow.{name} is required and non-empty, got {value!r}")
        for name in ("frozen_sha256", "queries_sha256"):
            value = getattr(self, name)
            if not _SHA_RE.match(value):
                raise AttentionError(
                    f"TrialRow.{name} must be 64 lowercase hex characters, got {value!r}. Unit "
                    f"test 25: the query hash is stored with EVERY trial, so a placeholder here "
                    f"is a trial whose query list cannot be recovered."
                )

    def to_dict(self) -> dict[str, str]:
        return {f: str(getattr(self, f)) for f in TRIAL_FIELDS}


def trial_header() -> str:
    """The `trials.csv` header line, without a trailing newline."""
    return ",".join(TRIAL_FIELDS)


def trial_line(row: TrialRow) -> str:
    """One `trials.csv` line, without a trailing newline. RFC-4180 quoting, minimal."""
    values = row.to_dict()
    return ",".join(_csv_cell(values[f]) for f in TRIAL_FIELDS)


def _csv_cell(text: str) -> str:
    if any(ch in text for ch in (",", '"', "\n", "\r")):
        return '"' + text.replace('"', '""') + '"'
    return text


def parse_trial_line(header: str, line: str) -> TrialRow:
    """The inverse of `trial_line`, through the same guards. A header that is not `TRIAL_FIELDS`
    raises: a log read under the wrong column order is worse than one that cannot be read."""
    cols = tuple(c.strip() for c in header.strip().split(","))
    if cols != TRIAL_FIELDS:
        raise AttentionError(f"trials header is {cols}, want {TRIAL_FIELDS}")
    cells = _split_csv(line.rstrip("\r\n"))
    if len(cells) != len(TRIAL_FIELDS):
        raise AttentionError(f"trials row has {len(cells)} cells, want {len(TRIAL_FIELDS)}")
    return TrialRow(**dict(zip(TRIAL_FIELDS, cells, strict=True)))


def _split_csv(line: str) -> list[str]:
    out: list[str] = []
    cur: list[str] = []
    quoted = False
    i = 0
    while i < len(line):
        ch = line[i]
        if quoted:
            if ch == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    cur.append('"')
                    i += 2
                    continue
                quoted = False
            else:
                cur.append(ch)
        elif ch == '"':
            quoted = True
        elif ch == ",":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    out.append("".join(cur))
    return out
