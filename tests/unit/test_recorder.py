"""Unit tests for `data/recorder.py` — the forward data recorder (D608), ledger doc §13A.3.

The three tests the deposit names by number are `test_ledger_31_*`, `test_ledger_32_*` and
`test_ledger_33_*`, here and in `tests/golden/test_recorder_ledger.py`. Everything else in this
file is a guard, and every guard is asserted to RAISE (D48) after the good case it protects has
been asserted to pass — a check that cannot fire is worse than none.

No network: every `fetch` is a literal. No fixture, no strategy return, and no date from
2024-01-01 on outside a synthetic September 2026 schedule, which is a clock and not a price.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from backtest_framework.data import recorder as mod
from backtest_framework.data.recorder import (
    CADENCES,
    FORBIDDEN_NAME_RE,
    GAP_CHECKED_CADENCES,
    STATUSES,
    ChecksumMismatch,
    Gap,
    Job,
    JobConfigError,
    ManifestError,
    MissingRawFile,
    OverwriteRefused,
    RateLimiter,
    Record,
    Recorder,
    Run,
    RunOutcome,
    append_gaps,
    append_health,
    assert_iso_z,
    availability_time,
    check_gaps,
    check_gaps_scope,
    gap_line,
    health_line,
    http_get,
    iso_utc,
    load_jobs,
    parse_iso_z,
    sha256_bytes,
    stamp_of,
)

REPO = Path(__file__).resolve().parents[2]
JOBS_JSON = REPO / "data" / "recorder" / "jobs.json"

UTC = dt.timezone.utc
T = dt.datetime(2026, 9, 21, 14, 30, 0, tzinfo=UTC)
NOW = dt.datetime(2026, 9, 22, 4, 0, 0, tzinfo=UTC)
PAY = b"payload\n"


def fixed(*instants: dt.datetime):
    seq = list(instants)
    state = {"n": 0}

    def clock() -> dt.datetime:
        when = seq[min(state["n"], len(seq) - 1)]
        state["n"] += 1
        return when

    return clock


def fetch(payload: bytes = PAY, headers: dict[str, str] | None = None):
    return lambda: (payload, headers or {})


def job(name: str = "j", **kw) -> Job:
    base = dict(cadence="daily", window_et=("09:00", "17:00"),
                source_url="https://example.invalid/x", parser=None, status="ready",
                window_basis="synthetic, unit test")
    base.update(kw)
    return Job(name=name, **base)  # type: ignore[arg-type]


def stub(name: str, fetched_at: str) -> Record:
    return Record(job=name, key=name, path=f"{name}.html", fetched_at=fetched_at,
                  published_at=None, bytes=1, sha256="0" * 64, source_url=None, method="fetched")


# ------------------------------------------------------------------------------- time primitives
def test_stamp_and_iso_are_the_two_spellings_of_one_instant() -> None:
    assert stamp_of(T) == "20260921T143000Z"
    assert iso_utc(T) == "2026-09-21T14:30:00Z"
    assert parse_iso_z(iso_utc(T)) == T


def test_a_non_utc_instant_is_converted_not_assumed() -> None:
    et = dt.datetime(2026, 9, 21, 10, 30, tzinfo=dt.timezone(dt.timedelta(hours=-4)))
    assert iso_utc(et) == "2026-09-21T14:30:00Z"


def test_a_naive_instant_raises() -> None:
    with pytest.raises(JobConfigError, match="naive"):
        iso_utc(dt.datetime(2026, 9, 21, 14, 30))
    with pytest.raises(JobConfigError, match="naive"):
        stamp_of(dt.datetime(2026, 9, 21, 14, 30))


@pytest.mark.parametrize("bad", [
    "2026-09-21T14:30:00",          # no Z
    "2026-09-21T14:30:00+00:00",    # an offset, not Z
    "2026-09-21T14:30:00.5Z",       # fractional, and 22 chars
    "2026-09-21 14:30:00Z",         # a space
    "2026-13-21T14:30:00Z",         # month 13, right shape
    "",
])
def test_assert_iso_z_raises_on_every_near_miss(bad: str) -> None:
    with pytest.raises(JobConfigError):
        assert_iso_z(bad, "under test")


def test_assert_iso_z_accepts_the_good_case_first() -> None:
    assert assert_iso_z("2026-09-21T14:30:00Z", "ok") == "2026-09-21T14:30:00Z"
    assert len("2026-09-21T14:30:00Z") == 20        # settlement_windows.py's own check


# --------------------------------------------------------------------------------------- hashing
def test_sha256_is_over_the_bytes_exactly() -> None:
    assert sha256_bytes(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert sha256_bytes(b"a\n") != sha256_bytes(b"a\r\n")    # a response is NEVER normalised


def test_sha256_refuses_a_str() -> None:
    with pytest.raises(TypeError, match="wants bytes"):
        sha256_bytes("a\n")  # type: ignore[arg-type]


# ------------------------------------------------------------------------------ record: the write
def test_ledger_31_a_second_record_never_overwrites(tmp_path: Path) -> None:
    """Deposit unit test 31. The golden pins the exact names and digests; this pins the mechanism
    on 20 consecutive records in one frozen second."""
    rec = Recorder(tmp_path, clock=fixed(T))
    made = [rec.record("j", "k", fetch(f"body {i}\n".encode()), ext="html") for i in range(20)]

    assert len({r.path for r in made}) == 20
    assert len({r.sha256 for r in made}) == 20
    assert len({r.fetched_at for r in made}) == 1
    assert sorted(p.name for p in (tmp_path / "j").glob("*.html")) == sorted(r.path for r in made)
    for i, r in enumerate(made):
        assert (tmp_path / "j" / r.path).read_bytes() == f"body {i}\n".encode()


def test_ledger_31_same_content_same_checksum_different_file(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    a = rec.record("j", "k", fetch(PAY), ext="html")
    b = rec.record("j", "k", fetch(PAY), ext="html")
    assert a.sha256 == b.sha256 and a.path != b.path
    assert a.bytes == b.bytes == len(PAY)


def test_record_writes_the_bytes_unmodified_including_crlf_and_nulls(tmp_path: Path) -> None:
    body = b"a\r\nb\x00\xff\n"
    rec = Recorder(tmp_path, clock=fixed(T))
    r = rec.record("j", "k", fetch(body), ext="bin")
    assert (tmp_path / "j" / r.path).read_bytes() == body
    assert r.sha256 == sha256_bytes(body)


def test_manifest_is_saved_after_every_record(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    for n in range(1, 4):
        rec.record("j", "k", fetch(), ext="html")
        man = json.loads(rec.manifest_path("j").read_text(encoding="utf-8"))
        assert len(man["records"]) == n
        assert man["schema"] == mod.SCHEMA and man["job"] == "j"


def test_headers_are_kept_lowercased_for_provenance(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    r = rec.record("j", "k", fetch(PAY, {"Content-Type": "text/html", "Date": "x"}), ext="html")
    assert dict(r.headers) == {"content-type": "text/html", "date": "x"}


def test_published_at_is_recorded_only_when_passed(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    bare = rec.record("j", "k", fetch(PAY, {"last-modified": "Fri, 18 Sep 2026 08:30:00 GMT"}),
                      ext="html")
    assert bare.published_at is None, "a Last-Modified header is NOT a published_at"
    given = rec.record("j", "k", fetch(), ext="html", published_at="2026-09-18T08:30:00Z")
    assert given.published_at == "2026-09-18T08:30:00Z"


@pytest.mark.parametrize("kwargs", [
    {"job": "../escape"}, {"job": "a/b"}, {"job": ""}, {"job": "-lead"},
    {"key": "..\\escape"}, {"key": "a b"},
])
def test_a_name_that_could_escape_its_directory_raises(tmp_path: Path, kwargs: dict) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    call = {"job": "j", "key": "k"} | kwargs
    with pytest.raises(JobConfigError):
        rec.record(call["job"], call["key"], fetch(), ext="html")


@pytest.mark.parametrize("ext", ["", "h tml", "html.gz", "../x", "a" * 13])
def test_a_bad_extension_raises(tmp_path: Path, ext: str) -> None:
    with pytest.raises(JobConfigError, match="alphanumerics"):
        Recorder(tmp_path, clock=fixed(T)).record("j", "k", fetch(), ext=ext)


def test_a_bad_published_at_raises_before_anything_is_written(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    with pytest.raises(JobConfigError):
        rec.record("j", "k", fetch(), ext="html", published_at="2026-09-18")
    assert not (tmp_path / "j").exists(), "the guard must fire BEFORE the directory is made"


@pytest.mark.parametrize("bad", [
    lambda: b"no tuple",
    lambda: (b"body",),
    lambda: ("str body", {}),
    lambda: (b"body", [("a", "b")]),
])
def test_a_fetch_that_breaks_its_contract_raises(tmp_path: Path, bad) -> None:
    with pytest.raises(TypeError):
        Recorder(tmp_path, clock=fixed(T)).record("j", "k", bad, ext="html")


def test_a_clock_returning_a_naive_instant_raises(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=lambda: dt.datetime(2026, 9, 21, 14, 30))
    with pytest.raises(JobConfigError, match="naive"):
        rec.record("j", "k", fetch(), ext="html")


def test_writing_over_an_existing_path_raises(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    r = rec.record("j", "k", fetch(), ext="html")
    with pytest.raises(OverwriteRefused, match="never overwrites"):
        mod._write_new_bytes(tmp_path / "j" / r.path, b"must never land")
    assert (tmp_path / "j" / r.path).read_bytes() == PAY


def test_the_collision_ladder_is_bounded(tmp_path: Path) -> None:
    (tmp_path / "j").mkdir()
    for n in range(3):
        suffix = "" if n == 0 else f"-{n}"
        (tmp_path / "j" / f"k__20260921T143000Z{suffix}.html").write_bytes(b"")
    with pytest.raises(OverwriteRefused, match="refusing to guess"):
        mod._free_name(tmp_path / "j", "k", "20260921T143000Z", "html", limit=3)


# ------------------------------------------------------------------------------- record: the read
def test_records_verifies_every_checksum_and_the_good_case_passes(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    rec.record("j", "k", fetch(b"one\n"), ext="html")
    rec.record("j", "k", fetch(b"two\n"), ext="html")
    got = rec.records("j")
    assert [r.bytes for r in got] == [4, 4]
    assert [r.sha256 for r in got] == [sha256_bytes(b"one\n"), sha256_bytes(b"two\n")]


def test_a_changed_byte_on_disk_raises_on_read(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    r = rec.record("j", "k", fetch(b"one\n"), ext="html")
    (tmp_path / "j" / r.path).write_bytes(b"onE\n")            # break the scalar the guard reads
    with pytest.raises(ChecksumMismatch, match="the bytes on disk hash to"):
        rec.records("j")
    assert rec.records("j", verify=False)[0].sha256 == r.sha256  # opt out is explicit


def test_a_missing_raw_file_raises_on_read(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    r = rec.record("j", "k", fetch(), ext="html")
    (tmp_path / "j" / r.path).unlink()
    with pytest.raises(MissingRawFile, match="NOT disposable"):
        rec.records("j")


def test_records_of_an_unknown_job_is_empty_not_an_error(tmp_path: Path) -> None:
    assert Recorder(tmp_path).records("never_recorded") == []


def test_a_manifest_of_the_wrong_schema_raises(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    rec.record("j", "k", fetch(), ext="html")
    rec.manifest_path("j").write_text(json.dumps({"schema": "other/9", "records": []}),
                                      encoding="utf-8")
    with pytest.raises(ManifestError, match="schema"):
        rec.records("j")


def test_a_manifest_that_is_not_json_raises(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    rec.record("j", "k", fetch(), ext="html")
    rec.manifest_path("j").write_text("{not json", encoding="utf-8")
    with pytest.raises(ManifestError, match="not JSON"):
        rec.records("j")


@pytest.mark.parametrize("mangle", [
    lambda e: e.pop("sha256"),
    lambda e: e.update(bytes="12"),
    lambda e: e.update(bytes=12.0),
    lambda e: e.update(fetched_at="2026-09-21 14:30"),
    lambda e: e.update(published_at="nope"),
    lambda e: e.update(headers="not a list"),
])
def test_a_mangled_manifest_entry_raises(tmp_path: Path, mangle) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    rec.record("j", "k", fetch(), ext="html")
    man = json.loads(rec.manifest_path("j").read_text(encoding="utf-8"))
    mangle(man["records"][0])
    rec.manifest_path("j").write_text(json.dumps(man), encoding="utf-8")
    with pytest.raises((ManifestError, JobConfigError)):
        rec.records("j")


def test_jobs_on_disk_lists_only_manifested_directories(tmp_path: Path) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    rec.record("b", "k", fetch(), ext="html")
    rec.record("a", "k", fetch(), ext="html")
    (tmp_path / "zzz_not_a_job").mkdir()
    assert rec.jobs_on_disk() == ["a", "b"]


# -------------------------------------------------------------------------------- availability
def test_ledger_32_availability_is_fetched_at(tmp_path: Path) -> None:
    """Deposit unit test 32, and deposit decision D23."""
    rec = Recorder(tmp_path, clock=fixed(T))
    r = rec.record("j", "k", fetch(), ext="html", published_at="2020-01-01T00:00:00Z")
    assert availability_time(r) == "2026-09-21T14:30:00Z" == r.fetched_at
    assert availability_time(r) > r.published_at    # string order is time order for ISO-Z


def test_ledger_32_there_is_no_fallback_branch(tmp_path: Path) -> None:
    """A rule with a branch can take the wrong branch, and the wrong branch is a look-ahead."""
    rec = Recorder(tmp_path, clock=fixed(T))
    with_pub = rec.record("j", "k", fetch(), ext="html", published_at="2026-09-18T08:30:00Z")
    without = rec.record("j", "k", fetch(), ext="html")
    assert availability_time(with_pub) == availability_time(without) == with_pub.fetched_at


def test_availability_time_refuses_a_dict() -> None:
    with pytest.raises(TypeError, match="wants a Record"):
        availability_time({"fetched_at": "2026-09-21T14:30:00Z"})  # type: ignore[arg-type]


# -------------------------------------------------------------------------------- the parsed copy
def test_a_parsed_copy_is_written_beside_the_raw(tmp_path: Path) -> None:
    rows = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    rec = Recorder(tmp_path, clock=fixed(T))
    r = rec.record("j", "k", fetch(), ext="html", parse=lambda _b: rows)
    assert r.parsed_path == "k__20260921T143000Z.parsed.csv" and r.parsed_rows == 2
    text = (tmp_path / "j" / r.parsed_path).read_text(encoding="utf-8")
    assert text == "a,b\n1,x\n2,y\n"
    assert (tmp_path / "j" / r.parsed_path).read_bytes().count(b"\r") == 0


def test_a_parsed_cell_with_a_comma_or_quote_is_quoted(tmp_path: Path) -> None:
    rows = [{"a": 'he said "hi", loudly', "b": None}]
    rec = Recorder(tmp_path, clock=fixed(T))
    r = rec.record("j", "k", fetch(), ext="html", parse=lambda _b: rows)
    assert (tmp_path / "j" / r.parsed_path).read_text(encoding="utf-8") == (
        'a,b\n"he said ""hi"", loudly",\n')


@pytest.mark.parametrize("rows", [[], [{}], [{"a": 1}, {"b": 2}], [{"a": 1}, {"a": 1, "b": 2}]])
def test_a_ragged_or_empty_parse_raises(tmp_path: Path, rows) -> None:
    rec = Recorder(tmp_path, clock=fixed(T))
    with pytest.raises(JobConfigError):
        rec.record("j", "k", fetch(), ext="html", parse=lambda _b: rows)


def test_no_parse_means_no_parsed_copy(tmp_path: Path) -> None:
    r = Recorder(tmp_path, clock=fixed(T)).record("j", "k", fetch(), ext="html")
    assert r.parsed_path is None and r.parsed_rows is None
    assert list((tmp_path / "j").glob("*.parsed.*")) == []


# -------------------------------------------------------------------------------------- Job guards
def test_a_good_job_is_accepted_first() -> None:
    j = job()
    assert j.cadence in CADENCES and j.status in STATUSES
    assert j.window_utc(dt.date(2026, 9, 17))[1] == dt.datetime(2026, 9, 17, 21, tzinfo=UTC)


@pytest.mark.parametrize("kw, match", [
    ({"cadence": "hourly"}, "cadence"),
    ({"status": "maybe"}, "status"),
    ({"window_et": ("9:00", "17:00")}, "not HH:MM"),
    ({"window_et": ("09:00", "24:00")}, "not HH:MM"),
    ({"window_et": ("09:00",)}, "2-tuple"),
    ({"window_et": ("17:00", "09:00")}, "closes before it opens"),
    ({"source_url": None}, "no source_url"),
    ({"status": "needs_source"}, "a source_url is set"),
    ({"cadence": "weekly"}, "weekday is required"),
    ({"weekday": 4}, "weekday is required"),
    ({"cadence": "weekly", "weekday": 7}, "not 0..6"),
    ({"window_basis": ""}, "window_basis is empty"),
    ({"ext": "h tml"}, "alphanumerics"),
])
def test_every_job_guard_raises(kw: dict, match: str) -> None:
    with pytest.raises(JobConfigError, match=match):
        job(**kw)


def test_a_job_name_that_is_a_path_raises() -> None:
    with pytest.raises(JobConfigError):
        job(name="../escape")


def test_from_dict_refuses_an_unknown_key() -> None:
    with pytest.raises(JobConfigError, match="unknown keys"):
        Job.from_dict({"name": "j", "cadence": "daily", "window_et": ["09:00", "17:00"],
                       "source_url": "https://example.invalid", "parser": None, "status": "ready",
                       "window_basis": "x", "windo_basis": "typo"})


def test_the_window_conversion_follows_dst() -> None:
    j = job()
    assert j.window_utc(dt.date(2026, 7, 1))[0].hour == 13     # EDT
    assert j.window_utc(dt.date(2026, 1, 15))[0].hour == 14    # EST


# ------------------------------------------------------------------------------------- load_jobs
def test_the_committed_schedule_loads_and_holds_the_deposits_ten() -> None:
    jobs = load_jobs(JOBS_JSON)
    names = {j.name for j in jobs}
    deposit_ten = {"fund_snapshot", "cme_settlement_prices", "tas_summary", "etf_quotes",
                   "attention", "restrike_check", "cftc_cot_weekly", "swap_dissemination",
                   "options_oi", "mbo_around_windows"}
    assert deposit_ten <= names
    assert len(jobs) == len(names)


def test_no_url_is_invented_in_the_committed_schedule() -> None:
    for j in load_jobs(JOBS_JSON):
        assert (j.source_url is not None) == (j.status == "ready"), j.name
        assert j.window_basis.strip(), j.name
        if j.status != "ready":
            assert j.note.strip(), f"{j.name} must say why it is not ready"


def test_every_ready_url_is_https_and_cites_where_it_was_copied_from() -> None:
    for j in load_jobs(JOBS_JSON):
        if j.status == "ready":
            assert j.source_url.startswith("https://"), j.name
            assert any(w in j.note for w in ("scripts/", "data/")), j.name


@pytest.mark.parametrize("payload, match", [
    ({"schema": "other/1", "jobs": []}, "schema"),
    ({"schema": "recorder-jobs/1", "jobs": []}, "non-empty"),
    ({"schema": "recorder-jobs/1"}, "non-empty"),
])
def test_a_bad_jobs_file_raises(tmp_path: Path, payload: dict, match: str) -> None:
    p = tmp_path / "jobs.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JobConfigError, match=match):
        load_jobs(p)


def test_a_duplicate_job_name_raises(tmp_path: Path) -> None:
    one = {"name": "j", "cadence": "daily", "window_et": ["09:00", "17:00"],
           "source_url": "https://example.invalid", "parser": None, "status": "ready",
           "window_basis": "x"}
    p = tmp_path / "jobs.json"
    p.write_text(json.dumps({"schema": "recorder-jobs/1", "jobs": [one, dict(one)]}),
                 encoding="utf-8")
    with pytest.raises(JobConfigError, match="duplicate job names"):
        load_jobs(p)


# ------------------------------------------------------------------------------------ gap detection
def test_ledger_33_a_missed_daily_window_is_flagged() -> None:
    """Deposit unit test 33: "Gap detection flags a missed daily job, and no downstream code fills
    the gap.\""""
    j = job("daily_probe")
    recs = {"daily_probe": [stub("daily_probe", "2026-09-21T14:00:00Z")]}
    gaps = check_gaps([j], recs, NOW, since=dt.date(2026, 9, 19))
    assert [g.date_et for g in gaps] == ["2026-09-19", "2026-09-20"]
    assert all(g.reason == "no record in window" for g in gaps)


def test_ledger_33_a_record_outside_the_window_does_not_satisfy_it() -> None:
    j = job("daily_probe")
    late = {"daily_probe": [stub("daily_probe", "2026-09-19T22:00:00Z")]}   # 18:00 ET, after close
    assert [g.date_et for g in check_gaps([j], late, NOW, since=dt.date(2026, 9, 19))] == \
        ["2026-09-19", "2026-09-20", "2026-09-21"]
    # the job RAN on 09-19 and produced a file; the day is still a gap, because the window is the
    # observation and a file that arrived after it closed is not that observation
    early = {"daily_probe": [stub("daily_probe", "2026-09-19T14:00:00Z")]}
    assert "2026-09-19" not in [g.date_et for g in
                                check_gaps([j], early, NOW, since=dt.date(2026, 9, 19))]


def test_ledger_33_a_window_still_open_is_not_a_gap() -> None:
    j = job("daily_probe")
    mid = dt.datetime(2026, 9, 21, 18, 0, tzinfo=UTC)         # 14:00 ET, window closes 21:00Z
    assert check_gaps([j], {"daily_probe": []}, mid, since=dt.date(2026, 9, 21)) == []


def test_ledger_33_the_window_is_closed_closed_at_both_ends() -> None:
    j = job("daily_probe")
    for stamp in ("2026-09-21T13:00:00Z", "2026-09-21T21:00:00Z"):
        recs = {"daily_probe": [stub("daily_probe", stamp)]}
        assert check_gaps([j], recs, NOW, since=dt.date(2026, 9, 21)) == [], stamp
    for stamp in ("2026-09-21T12:59:59Z", "2026-09-21T21:00:01Z"):
        recs = {"daily_probe": [stub("daily_probe", stamp)]}
        assert len(check_gaps([j], recs, NOW, since=dt.date(2026, 9, 21))) == 1, stamp


def test_ledger_33_a_weekly_job_is_checked_only_on_its_weekday() -> None:
    j = job("w", cadence="weekly", weekday=4, window_et=("15:30", "23:00"))
    gaps = check_gaps([j], {"w": []}, NOW, since=dt.date(2026, 9, 14))
    assert [g.date_et for g in gaps] == ["2026-09-18"]          # the one Friday whose window closed


def test_intraday_and_not_ready_jobs_are_never_gapped() -> None:
    intraday = job("i", cadence="intraday")
    pending = job("p", status="needs_source", source_url=None)
    paid = job("m", status="needs_key", source_url=None)
    assert check_gaps([intraday, pending, paid], {}, NOW, since=dt.date(2026, 9, 16)) == []
    scope = check_gaps_scope([job("r"), intraday, pending, paid])
    assert scope == {"checked": ["r"], "not_checked_intraday": ["i"],
                     "not_checked_not_ready": ["m", "p"]}
    assert set(GAP_CHECKED_CADENCES) < set(CADENCES)


def test_since_defaults_to_the_first_record_and_is_empty_with_no_records() -> None:
    j = job("daily_probe")
    assert check_gaps([j], {"daily_probe": []}, NOW) == []
    recs = {"daily_probe": [stub("daily_probe", "2026-09-19T14:00:00Z")]}
    assert [g.date_et for g in check_gaps([j], recs, NOW)] == ["2026-09-20", "2026-09-21"]


def test_a_since_after_now_raises() -> None:
    with pytest.raises(JobConfigError, match="is after the ET date"):
        check_gaps([job()], {}, NOW, since=dt.date(2026, 10, 1))


def test_a_naive_now_raises() -> None:
    with pytest.raises(JobConfigError, match="naive"):
        check_gaps([job()], {}, dt.datetime(2026, 9, 22, 4, 0))


# ----------------------------------------------------------------------------------- GAPS.md
def test_the_header_is_written_once_and_then_only_lines_are_appended(tmp_path: Path) -> None:
    p = tmp_path / "GAPS.md"
    g1 = Gap(job="a", cadence="daily", date_et="2026-09-17", window_et=("09:00", "17:00"),
             window_close_utc="2026-09-17T21:00:00Z")
    g2 = Gap(job="a", cadence="daily", date_et="2026-09-18", window_et=("09:00", "17:00"),
             window_close_utc="2026-09-18T21:00:00Z")
    assert append_gaps(p, [g1], now_utc=NOW) == 1
    first = p.read_text(encoding="utf-8")
    assert first.startswith("# `data/recorder/GAPS.md`")
    assert "never" in first and "13A.3" in first
    assert append_gaps(p, [g2], now_utc=NOW) == 1
    assert p.read_text(encoding="utf-8").startswith(first)     # nothing earlier was rewritten


def test_a_gap_already_logged_is_not_logged_twice(tmp_path: Path) -> None:
    p = tmp_path / "GAPS.md"
    g = Gap(job="a", cadence="daily", date_et="2026-09-17", window_et=("09:00", "17:00"),
            window_close_utc="2026-09-17T21:00:00Z")
    append_gaps(p, [g], now_utc=NOW)
    before = p.read_bytes()
    later = dt.datetime(2026, 12, 1, tzinfo=UTC)
    assert append_gaps(p, [g, g, g], now_utc=later) == 0
    assert p.read_bytes() == before


def test_a_duplicate_inside_one_batch_is_logged_once(tmp_path: Path) -> None:
    """Found by `tests/property/test_recorder_property.py`: the first draft deduplicated against
    the FILE only, so `append_gaps(path, [g, g])` wrote two lines for one window."""
    p = tmp_path / "GAPS.md"
    g = Gap(job="a", cadence="daily", date_et="2026-09-17", window_et=("09:00", "17:00"),
            window_close_utc="2026-09-17T21:00:00Z")
    assert append_gaps(p, [g, g, g], now_utc=NOW) == 1
    assert p.read_text(encoding="utf-8").count("| 2026-09-17 | a |") == 1


def test_append_gaps_with_nothing_still_makes_the_file_with_its_header(tmp_path: Path) -> None:
    p = tmp_path / "GAPS.md"
    assert append_gaps(p, [], now_utc=NOW) == 0
    assert p.exists() and p.read_text(encoding="utf-8").endswith("|---|---|---|---|---|---|---|\n")
    # and the committed GAPS.md is exactly this header, byte for byte
    committed = (REPO / "data" / "recorder" / "GAPS.md").read_bytes()
    assert committed == p.read_bytes()
    assert b"\r" not in committed


def test_append_gaps_defaults_its_logged_stamp_to_the_wall_clock(tmp_path: Path) -> None:
    """The stamp is injectable for determinism and optional for a caller that does not care."""
    p = tmp_path / "GAPS.md"
    g = Gap(job="a", cadence="daily", date_et="2026-09-17", window_et=("09:00", "17:00"),
            window_close_utc="2026-09-17T21:00:00Z")
    assert append_gaps(p, [g]) == 1
    logged = p.read_text(encoding="utf-8").rstrip("\n").rsplit("|", 2)[1].strip()
    assert assert_iso_z(logged, "logged") == logged


def test_gap_line_refuses_a_bad_logged_stamp() -> None:
    g = Gap(job="a", cadence="daily", date_et="2026-09-17", window_et=("09:00", "17:00"),
            window_close_utc="2026-09-17T21:00:00Z")
    assert gap_line(g, "2026-09-22T04:00:00Z").count("|") == 8
    with pytest.raises(JobConfigError):
        gap_line(g, "2026-09-22")


def test_gap_to_dict_round_trips_its_fields() -> None:
    g = Gap(job="a", cadence="daily", date_et="2026-09-17", window_et=("09:00", "17:00"),
            window_close_utc="2026-09-17T21:00:00Z")
    assert g.to_dict() == {"job": "a", "cadence": "daily", "date_et": "2026-09-17",
                           "window_et": ["09:00", "17:00"],
                           "window_close_utc": "2026-09-17T21:00:00Z",
                           "reason": "no record in window"}


# ------------------------------------------------------------------------------------- the health
def test_health_line_carries_every_declared_field() -> None:
    run = Run(start="2026-09-21T14:30:00Z", end="2026-09-21T14:31:00Z", host="host-a",
              outcomes=(RunOutcome("a", True, bytes_written=100),
                        RunOutcome("b", False, error="HTTPError", detail="404 " + "x" * 400)),
              gaps=(Gap(job="a", cadence="daily", date_et="2026-09-17",
                        window_et=("09:00", "17:00"), window_close_utc="2026-09-17T21:00:00Z"),))
    line = health_line(run)
    assert line["attempted"] == 2 and line["ok"] == 1 and line["bytes"] == 100
    assert line["ok_jobs"] == ["a"] and line["gaps"] == 1 and line["host"] == "host-a"
    assert line["failed"] == [{"job": "b", "error": "HTTPError", "detail": "404 " + "x" * 196}]
    assert len(line["failed"][0]["detail"]) == 200
    assert line["schema"] == "recorder-health/1"


def test_health_line_names_the_exception_class_not_a_traceback() -> None:
    try:
        raise TimeoutError("the socket gave up")
    except TimeoutError as exc:
        outcome = RunOutcome("j", False, error=type(exc).__name__, detail=str(exc))
    line = health_line(Run(start=iso_utc(T), end=iso_utc(T), outcomes=(outcome,), host="h"))
    assert line["failed"][0]["error"] == "TimeoutError"
    assert "Traceback" not in json.dumps(line)


def test_an_empty_run_is_still_a_line() -> None:
    line = health_line(Run(start=iso_utc(T), end=iso_utc(T), host="h"))
    assert line["attempted"] == 0 and line["ok"] == 0 and line["failed"] == [] and line["bytes"] == 0


def test_health_is_appended_one_json_object_per_line(tmp_path: Path) -> None:
    p = tmp_path / "health.jsonl"
    for n in range(3):
        append_health(p, {"n": n})
    lines = p.read_text(encoding="utf-8").splitlines()
    assert [json.loads(x)["n"] for x in lines] == [0, 1, 2]
    assert p.read_bytes().count(b"\r") == 0
    assert Recorder(tmp_path).health_path == p


# ------------------------------------------------------------------------------------------ http
def test_the_rate_limiter_sleeps_only_when_it_must() -> None:
    clock = {"t": 0.0}
    slept: list[float] = []
    lim = RateLimiter(2.0, sleep=slept.append, monotonic=lambda: clock["t"])
    lim.wait()                        # first call: last = 0.0, gap = 0 -> sleeps the full interval
    clock["t"] = 10.0
    lim.wait()                        # ten seconds later: no sleep
    assert slept == [2.0]


def test_http_get_never_retries_a_404() -> None:
    import urllib.error

    calls = {"n": 0}

    def opener(req, timeout=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)  # type: ignore[arg-type]

    with pytest.raises(urllib.error.HTTPError):
        http_get("https://example.invalid/x", opener=opener, sleep=lambda _s: None)
    assert calls["n"] == 1, "a 404 is an answer; asking four times is rude, not persistent"


def test_http_get_retries_then_succeeds_and_lowercases_the_headers() -> None:
    class Resp:
        headers = {"Content-Type": "text/html"}

        def read(self) -> bytes:
            return b"ok"

        def __enter__(self):
            return self

        def __exit__(self, *a) -> bool:
            return False

    calls = {"n": 0}
    delays: list[float] = []

    def opener(req, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise TimeoutError("slow")
        return Resp()

    body, headers = http_get("https://example.invalid/x", opener=opener, sleep=delays.append)
    assert body == b"ok" and headers == {"content-type": "text/html"}
    assert calls["n"] == 3 and delays == [3.0, 6.0]        # exponential, doubling from 3 s


def test_http_get_exhausts_and_names_the_tool_that_failed() -> None:
    def opener(req, timeout=None):
        raise OSError("refused")

    with pytest.raises(RuntimeError, match="urllib.request.urlopen"):
        http_get("https://example.invalid/x", opener=opener, sleep=lambda _s: None)


def test_the_user_agent_is_the_repositorys_one() -> None:
    assert mod.UA["User-Agent"].startswith("backtest-framework-fetch/1.0")


# ------------------------------------------------------------------------------- the standing rule
def test_nothing_in_this_module_fills_a_gap() -> None:
    assert not hasattr(mod, "fill_gap")
    public = [n for n in dir(mod) if not n.startswith("_")]
    assert [n for n in public if FORBIDDEN_NAME_RE.search(n)] == ["FILL_IS_FORBIDDEN"]
    assert "never" in mod.FILL_IS_FORBIDDEN.lower()
    assert set(mod.__all__) <= set(public)


SPEC = REPO / "docs" / "internal" / "User-Doc-Deposit" / "SETTLEMENT_FLOW_LEDGER_PREREG.md"

#: The five storage rules and the three unit tests, as §13A.3 and §12 write them.
SPEC_LINES = (
    "- Save the **raw response** (HTML/CSV/JSON) unmodified, plus a parsed Parquet copy.",
    "- Every record carries `fetched_at` (UTC) and, where the source states it, `published_at`.",
    "- **Never overwrite.** New fetches are new files. Store a checksum per file.",
    "- For forward tests, **`fetched_at` is the availability time** (conservative; decision D23).",
    "31. Recorder never overwrites: a second fetch on the same day creates a new file; "
    "checksums differ only if content differs.",
    "32. Recorder availability: a forward test reading a record uses `fetched_at`, not "
    "`published_at`, as the time it became usable.",
    "33. Gap detection flags a missed daily job, and no downstream code fills the gap.",
)


def test_the_docstring_quotes_the_spec_file_verbatim() -> None:
    """R16's shape for prose: a quotation is not verbatim because it was typed carefully, it is
    verbatim because it was compared. Skipped, loudly, if the deposit document is not on disk —
    the six pre-registrations are read-only sources this module does not own."""
    if not SPEC.exists():
        pytest.skip(f"{SPEC.name} is not on disk; the docstring quote cannot be compared")
    import re

    spec = SPEC.read_text(encoding="utf-8")
    flat_doc = re.sub(r"\s+", " ", mod.__doc__ or "")
    for line in SPEC_LINES:
        assert line in spec, f"the spec no longer contains: {line[:70]}"
        assert re.sub(r"\s+", " ", line) in flat_doc, f"the docstring has drifted: {line[:70]}"


def test_the_spec_is_quoted_verbatim_in_the_docstring() -> None:
    doc = mod.__doc__ or ""
    for sentence in (
        "Save the **raw response** (HTML/CSV/JSON) unmodified",
        "Every record carries `fetched_at` (UTC) and, where the source states it, `published_at`.",
        "**Never overwrite.** New fetches are new files. Store a checksum per file.",
        "Gaps are **never** filled with estimates.",
        "**`fetched_at` is the availability time**",
        "The recorder\n    must survive reboots and log its own health.",
    ):
        assert sentence in doc, sentence


def test_the_module_installs_no_scheduler() -> None:
    """Hosting is deposit Q17 and the principal's decision; D608 installs nothing.

    The schedulers are NAMED in `scripts/recorder.py`'s docstring, as the things a host might use.
    What this asserts is that neither file can INVOKE one: no subprocess, no registry, no
    `os.system`, no fork. A scheduler this repository installed would be a standing change to the
    principal's machine made by a research record, which is not D608's to make."""
    import ast

    for path in (REPO / "src" / "backtest_framework" / "data" / "recorder.py",
                 REPO / "scripts" / "recorder.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert not imported & {"subprocess", "winreg", "multiprocessing", "signal", "ctypes"}, \
            f"{path.name} imports {sorted(imported)}"
        for call in ("os.system", "os.fork", "os.execv", "os.startfile", "atexit.register"):
            assert call not in source, f"{path.name}: {call}"
        # `os` itself is not imported by either file, so no scheduler can be reached at all
        assert "os" not in imported, f"{path.name} imports os"
