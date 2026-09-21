"""Golden tests for `data/recorder.py` (D608) — the forward data recorder, ledger doc §13A.3.

Hand arithmetic in `test_recorder_ledger.hand.txt`, written BEFORE the module existed, per
CONTRIBUTING step 2. Every digest there was produced by two calculators that never import this
codebase — GNU `sha256sum` fed by `printf`, and .NET `System.Security.Cryptography.SHA256` over a
literal `[byte[]]` — and they agreed on every line. The anchor case asserts the published SHA-256
of the empty string, so a suite where `hashlib` had been swapped for something else fails on the
first assertion rather than on a subtle one.

Three things belong in this tier rather than in unit tests, because each is an exact STRING that
a future reader depends on:

  * the checksum of the bytes as they arrived (§13A.3: "Store a checksum per file");
  * the filename, because it carries `fetched_at` and because a second fetch must produce a
    SECOND NAME (unit test 31);
  * the `GAPS.md` line, because that file is the artefact a human reads to learn a window closed
    empty, and it is appended to forever (unit test 33).

No network, no fixture, no strategy return, and no date from 2024-01-01 on outside the synthetic
September 2026 schedule — which is a clock, not a price.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

from backtest_framework.data.recorder import (
    Gap,
    Job,
    Record,
    Recorder,
    append_gaps,
    availability_time,
    check_gaps,
    gap_line,
    sha256_bytes,
)

# --- transcribed from test_recorder_ledger.hand.txt ------------------------------------------
SHA_EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
PAYLOAD_1 = b"schedule v1\n"
PAYLOAD_2 = b"schedule v2\n"
SHA_1 = "f06956244779abde350c97ff5e18c909ea39bdbb7a9894d026fa1ac3600c6a34"
SHA_2 = "ccd1d9f0f9906c9fe6964faed96e985bf66f65765d780b675620ff4248ed2b39"

NAME_1 = "bls_cpi__20260921T143000Z.html"
NAME_2 = "bls_cpi__20260921T143000Z-1.html"
NAME_3 = "bls_cpi__20260921T143100Z.html"

FETCHED_1 = "2026-09-21T14:30:00Z"
FETCHED_3 = "2026-09-21T14:31:00Z"
PUBLISHED = "2026-09-18T08:30:00Z"

UTC = dt.timezone.utc
T1430 = dt.datetime(2026, 9, 21, 14, 30, 0, tzinfo=UTC)
T1431 = dt.datetime(2026, 9, 21, 14, 31, 0, tzinfo=UTC)

NOW = dt.datetime(2026, 9, 22, 4, 0, 0, tzinfo=UTC)
SINCE = dt.date(2026, 9, 16)

GAP_LINES = [
    "| 2026-09-17 | daily_probe | daily | 09:00-17:00 ET | 2026-09-17T21:00:00Z | no record in window | 2026-09-22T04:00:00Z |",
    "| 2026-09-18 | weekly_probe | weekly | 15:30-23:00 ET | 2026-09-19T03:00:00Z | no record in window | 2026-09-22T04:00:00Z |",
    "| 2026-09-19 | daily_probe | daily | 09:00-17:00 ET | 2026-09-19T21:00:00Z | no record in window | 2026-09-22T04:00:00Z |",
    "| 2026-09-20 | daily_probe | daily | 09:00-17:00 ET | 2026-09-20T21:00:00Z | no record in window | 2026-09-22T04:00:00Z |",
]

DAILY_PROBE = Job(
    name="daily_probe",
    cadence="daily",
    window_et=("09:00", "17:00"),
    source_url="https://example.invalid/daily",
    parser=None,
    status="ready",
    window_basis="synthetic, declared in the hand ledger Case 3",
)
WEEKLY_PROBE = Job(
    name="weekly_probe",
    cadence="weekly",
    weekday=4,
    window_et=("15:30", "23:00"),
    source_url="https://example.invalid/weekly",
    parser=None,
    status="ready",
    window_basis="synthetic, declared in the hand ledger Case 3",
)
DAILY_STAMPS = (
    "2026-09-16T14:00:00Z",  # 10:00 ET, inside
    "2026-09-17T22:00:00Z",  # 18:00 ET, one hour LATE — 09-17 is still a gap
    "2026-09-18T20:59:00Z",  # 16:59 ET, inside with a minute to spare
    "2026-09-21T13:00:00Z",  # 09:00 ET, exactly at the open
)


class _Clock:
    """A hand-driven clock. Nothing in this file depends on the wall clock."""

    def __init__(self, *instants: dt.datetime) -> None:
        self.instants = list(instants)
        self.n = 0

    def __call__(self) -> dt.datetime:
        when = self.instants[min(self.n, len(self.instants) - 1)]
        self.n += 1
        return when


def _fetch(payload: bytes):
    return lambda: (payload, {})


def _stub(job: str, fetched_at: str) -> Record:
    return Record(
        job=job, key=job, path=f"{job}.html", fetched_at=fetched_at, published_at=None,
        bytes=1, sha256=SHA_EMPTY, source_url=None, method="fetched",
    )


# ------------------------------------------------------------------ Case 0: the anchor + payloads
def test_case0_anchor_and_payload_digests() -> None:
    assert hashlib.sha256(b"").hexdigest() == SHA_EMPTY
    assert sha256_bytes(b"") == SHA_EMPTY
    assert len(PAYLOAD_1) == 12 and len(PAYLOAD_2) == 12
    assert PAYLOAD_1.hex(" ").upper() == "73 63 68 65 64 75 6C 65 20 76 31 0A"
    assert PAYLOAD_2.hex(" ").upper() == "73 63 68 65 64 75 6C 65 20 76 32 0A"
    assert sha256_bytes(PAYLOAD_1) == SHA_1
    assert sha256_bytes(PAYLOAD_2) == SHA_2
    # one byte apart, 0x31 -> 0x32, and the digests share no prefix
    assert sum(a != b for a, b in zip(PAYLOAD_1, PAYLOAD_2, strict=True)) == 1
    assert SHA_1[0] != SHA_2[0]


def test_case0_bytes_are_not_normalised() -> None:
    """A response is not source: D594 LF-pins text before hashing, this module never does."""
    crlf = b"schedule v1\r\n"
    assert sha256_bytes(crlf) != SHA_1
    assert sha256_bytes(crlf) == hashlib.sha256(crlf).hexdigest()


# ------------------------------------------------- Case 1: unit test 31, three records, three files
def test_ledger_31_second_fetch_is_a_new_file_and_the_first_is_untouched(tmp_path: Path) -> None:
    """Ledger doc unit test 31: "Recorder never overwrites: a second fetch on the same day creates
    a new file; checksums differ only if content differs.\""""
    rec = Recorder(tmp_path, clock=_Clock(T1430, T1430, T1431))

    r1 = rec.record("bls_cpi", "bls_cpi", _fetch(PAYLOAD_1), ext="html")
    r2 = rec.record("bls_cpi", "bls_cpi", _fetch(PAYLOAD_1), ext="html")
    r3 = rec.record("bls_cpi", "bls_cpi", _fetch(PAYLOAD_2), ext="html")

    assert [r1.path, r2.path, r3.path] == [NAME_1, NAME_2, NAME_3]
    assert [r1.sha256, r2.sha256, r3.sha256] == [SHA_1, SHA_1, SHA_2]
    assert [r1.fetched_at, r2.fetched_at, r3.fetched_at] == [FETCHED_1, FETCHED_1, FETCHED_3]

    jdir = tmp_path / "bls_cpi"
    assert (jdir / NAME_1).read_bytes() == PAYLOAD_1          # record 1 untouched by records 2, 3
    assert sha256_bytes((jdir / NAME_1).read_bytes()) == SHA_1
    assert sorted(p.name for p in jdir.glob("*.html")) == sorted([NAME_1, NAME_2, NAME_3])

    man = json.loads((jdir / "_manifest.json").read_text(encoding="utf-8"))
    paths = [e["path"] for e in man["records"]]
    digests = [e["sha256"] for e in man["records"]]
    assert paths == [NAME_1, NAME_2, NAME_3]                   # 3 entries, 3 distinct paths
    assert len(set(paths)) == 3 and len(set(digests)) == 2     # 2 distinct digests
    assert all(e["bytes"] == 12 for e in man["records"])


def test_ledger_31_the_suffix_lands_on_the_stamp_so_the_extension_survives(tmp_path: Path) -> None:
    """And the hand ledger's CORRECTION: a name sort orders records between seconds, not within
    one, because `-` is 0x2D and `.` is 0x2E."""
    rec = Recorder(tmp_path, clock=_Clock(T1430, T1430, T1430, T1431))
    names = [rec.record("j", "j", _fetch(PAYLOAD_1), ext="html").path for _ in range(4)]
    assert names == ["j__20260921T143000Z.html", "j__20260921T143000Z-1.html",
                     "j__20260921T143000Z-2.html", "j__20260921T143100Z.html"]
    assert all(n.endswith(".html") for n in names)

    assert names != sorted(names)                       # the correction, made into an assertion
    assert sorted(names)[0] == "j__20260921T143000Z-1.html"
    assert ord("-") == 0x2D and ord(".") == 0x2E
    assert names[2] < names[3]                          # between seconds the name sort is right

    # and the READ order is the WRITE order, which is what the sort key exists for
    assert [r.path for r in rec.records("j")] == names


# ------------------------------------------------------------- Case 2: unit test 32, availability
def test_ledger_32_availability_is_fetched_at_not_published_at(tmp_path: Path) -> None:
    """Ledger doc unit test 32: "Recorder availability: a forward test reading a record uses
    `fetched_at`, not `published_at`, as the time it became usable." (deposit D23)"""
    rec = Recorder(tmp_path, clock=_Clock(T1430))
    r = rec.record("bls_cpi", "bls_cpi", _fetch(PAYLOAD_1), ext="html", published_at=PUBLISHED)

    assert r.published_at == PUBLISHED
    assert r.fetched_at == FETCHED_1
    assert availability_time(r) == FETCHED_1
    assert availability_time(r) != r.published_at

    lag = dt.datetime.strptime(FETCHED_1, "%Y-%m-%dT%H:%M:%SZ") - dt.datetime.strptime(
        PUBLISHED, "%Y-%m-%dT%H:%M:%SZ")
    assert lag.total_seconds() == 280_800          # 3 days 6 hours, and the answer is the LATER

    # unconditional: with no published_at at all, still fetched_at, never a fallback
    r2 = rec.record("bls_cpi", "bls_cpi", _fetch(PAYLOAD_1), ext="html")
    assert r2.published_at is None
    assert availability_time(r2) == r2.fetched_at


# ------------------------------------------------------------------- Case 3: unit test 33, the gaps
def test_ledger_33_gap_table_for_the_two_job_schedule() -> None:
    """Ledger doc unit test 33: "Gap detection flags a missed daily job, and no downstream code
    fills the gap." The hand ledger's Case 3 table, asserted row for row."""
    records = {"daily_probe": [_stub("daily_probe", s) for s in DAILY_STAMPS], "weekly_probe": []}
    gaps = check_gaps([DAILY_PROBE, WEEKLY_PROBE], records, NOW, since=SINCE)

    assert [(g.date_et, g.job, g.cadence, g.window_close_utc) for g in gaps] == [
        ("2026-09-17", "daily_probe", "daily", "2026-09-17T21:00:00Z"),
        ("2026-09-18", "weekly_probe", "weekly", "2026-09-19T03:00:00Z"),
        ("2026-09-19", "daily_probe", "daily", "2026-09-19T21:00:00Z"),
        ("2026-09-20", "daily_probe", "daily", "2026-09-20T21:00:00Z"),
    ]
    # the counting check from the hand ledger: 7 eligible windows, 3 satisfied, 7 - 3 = 4
    assert len(gaps) == 4
    # 2026-09-22's window has not closed at 04:00Z and is therefore not a gap
    assert all(g.date_et != "2026-09-22" for g in gaps)
    # 2026-09-17 ran and produced a file; it is still a gap, because the file arrived late
    assert "2026-09-17" in {g.date_et for g in gaps}


def test_ledger_33_the_window_conversion_is_through_the_zone_not_a_constant() -> None:
    sep_open, sep_close = DAILY_PROBE.window_utc(dt.date(2026, 9, 17))
    assert (sep_open.isoformat(), sep_close.isoformat()) == (
        "2026-09-17T13:00:00+00:00", "2026-09-17T21:00:00+00:00")           # EDT, +4h
    nov_open, nov_close = DAILY_PROBE.window_utc(dt.date(2026, 11, 17))
    assert (nov_open.isoformat(), nov_close.isoformat()) == (
        "2026-11-17T14:00:00+00:00", "2026-11-17T22:00:00+00:00")           # EST, +5h
    _, wk_close = WEEKLY_PROBE.window_utc(dt.date(2026, 9, 18))
    assert wk_close.isoformat() == "2026-09-19T03:00:00+00:00"              # close rolls over


# ------------------------------------------------------------------------ Case 4: the GAPS.md lines
def test_ledger_33_gaps_md_lines_are_exact(tmp_path: Path) -> None:
    records = {"daily_probe": [_stub("daily_probe", s) for s in DAILY_STAMPS], "weekly_probe": []}
    gaps = check_gaps([DAILY_PROBE, WEEKLY_PROBE], records, NOW, since=SINCE)
    assert [gap_line(g, "2026-09-22T04:00:00Z") for g in gaps] == GAP_LINES

    path = tmp_path / "GAPS.md"
    assert append_gaps(path, gaps, now_utc=NOW) == 4
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n".join(GAP_LINES) + "\n")
    assert "\r" not in text                                   # LF pinned (D550)
    assert path.read_bytes().count(b"\r\n") == 0


def test_ledger_33_append_only_a_rerun_adds_nothing_and_a_new_gap_adds_one(tmp_path: Path) -> None:
    records = {"daily_probe": [_stub("daily_probe", s) for s in DAILY_STAMPS], "weekly_probe": []}
    gaps = check_gaps([DAILY_PROBE, WEEKLY_PROBE], records, NOW, since=SINCE)
    path = tmp_path / "GAPS.md"
    append_gaps(path, gaps, now_utc=NOW)
    before = path.read_bytes()

    later = dt.datetime(2026, 9, 25, 12, 0, 0, tzinfo=dt.timezone.utc)
    assert append_gaps(path, gaps, now_utc=later) == 0
    assert path.read_bytes() == before                        # byte-identical, original `logged`

    fifth = Gap(job="daily_probe", cadence="daily", date_et="2026-09-21",
                window_et=("09:00", "17:00"), window_close_utc="2026-09-21T21:00:00Z")
    assert append_gaps(path, [fifth], now_utc=later) == 1
    after = path.read_bytes()
    assert after.startswith(before)                           # the four earlier lines untouched
    assert after.decode("utf-8").rstrip("\n").endswith("| 2026-09-25T12:00:00Z |")


def test_no_fill_anywhere_in_the_module() -> None:
    """§13A.3: "Gaps are **never** filled with estimates." A guarantee about code that does not
    exist can only be an assertion about the namespace."""
    from backtest_framework.data import recorder as mod

    assert not hasattr(mod, "fill_gap")
    offenders = [n for n in dir(mod) if not n.startswith("_") and mod.FORBIDDEN_NAME_RE.search(n)]
    assert offenders == ["FILL_IS_FORBIDDEN"], offenders
    assert "never" in mod.FILL_IS_FORBIDDEN.lower()


def test_the_hand_ledger_is_beside_this_file() -> None:
    hand = Path(__file__).with_suffix("").with_name("test_recorder_ledger.hand.txt")
    text = hand.read_text(encoding="utf-8")
    for constant in (SHA_EMPTY, SHA_1, SHA_2, NAME_1, NAME_2, NAME_3, *GAP_LINES):
        assert constant in text, constant
    with pytest.raises(AssertionError):
        assert "a digest that is not in the ledger" in text
