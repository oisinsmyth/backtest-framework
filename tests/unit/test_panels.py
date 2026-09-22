"""The panel catalogue and the loader chokepoint (D609).

Three kinds of test, and the order inside each pair is deliberate: **the good case runs before
the break.** A guard proved only by its raise could be raising for the wrong reason.

  * **catalogue** — every manifest panel has a spec, every spec's declared column is in that
    panel's own header, and no column declared a WRONG cut is ever a date column. The header
    checks skip per panel when the file is absent (a clone) or when its reader is unavailable
    (`.parquet` needs pyarrow, which this venv has not got); they never pass vacuously, because
    `test_the_header_check_actually_read_something` counts how many ran.
  * **the loader**, on a synthetic repository built in `tmp_path` with its own manifest and its
    own seal date. **The synthetic cut is 2020-01-01, never this repository's 2024-01-01** — a
    unit test carrying the real seal date is one copy-paste away from being a reason to read
    the real reserved slice.
  * **two real reads**, of the two smallest panels, both blocked and both under
    `requires_panel`.

No row dated 2024-01-01 or later is read from any real fixture here, and `word=True` is only
ever passed to a synthetic one.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from backtest_framework.data import panel_catalogue as CAT
from backtest_framework.data import panels as P
from backtest_framework.data.panel_catalogue import CatalogueError, PanelSpec, SPECS, spec_for
from backtest_framework.data.panels import (
    PanelAbsent,
    PanelCutError,
    PanelDigestError,
    PanelError,
    PanelRefused,
    absent_reason,
    convert_cut,
    load_panel,
    panel_status,
    unlisted_message,
)

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "data" / "data_manifest.json"
CUT = "2020-01-01"
WORD = "the principal's word, 2026-09-22, for this test and nothing else"


# ------------------------------------------------------------------ the catalogue


def _manifest_paths() -> set[str]:
    return {f["path"] for f in json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]}


def test_every_manifest_panel_has_a_spec_and_every_spec_is_a_manifest_panel():
    manifest, catalogue = _manifest_paths(), {s.path for s in SPECS}
    assert manifest - catalogue == set(), "manifest panels with no catalogue row"
    assert catalogue - manifest == set(), "catalogue rows that are not manifest panels"
    assert len(SPECS) == len(manifest) == 134


def test_no_wrong_cut_is_ever_a_date_column_anywhere_in_the_catalogue():
    """The cross-panel form of the per-spec check. `prev_day` is a wrong cut on eight panels;
    if any panel declared it as ITS date column, a cut would let one reserved session through
    there while being right everywhere else, which is the hardest kind of defect to see."""
    date_cols = {s.date_col for s in SPECS if s.date_col}
    wrong = {c for s in SPECS for c in s.wrong_cuts}
    assert wrong, "the catalogue declares no wrong cuts at all, which would mean it lost them"
    for spec in SPECS:
        assert spec.date_col not in spec.wrong_cuts, spec.name
    # And the two sets do overlap across panels, which is the point: `report_date` is the right
    # column on cftc_cot_raw and `report` is the wrong one on d456_8k_events.
    assert "prev_day" in wrong and "prev_day" not in date_cols


def _parquet_footer(path: Path) -> bytes:
    """The parquet footer's raw bytes, WITHOUT pyarrow, which this venv has not got.

    The last four bytes are the magic `PAR1` and the four before them are the footer's length,
    little-endian. Asserting the magic is what makes a substring search over the footer a check
    rather than a guess: it proves the bytes searched are the schema block.
    """
    import struct

    with path.open("rb") as handle:
        handle.seek(-8, 2)
        length = struct.unpack("<I", handle.read(4))[0]
        magic = handle.read(4)
        assert magic == b"PAR1", f"{path.name} does not end with the parquet magic: {magic!r}"
        handle.seek(-(8 + length), 2)
        return handle.read(length)


def _has_column(path: Path, reader: str, column: str) -> bool:
    if reader == "csv":
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            return column in handle.readline().rstrip("\r\n").split(",")
    if reader == "npz":
        import numpy as np

        with np.load(path, allow_pickle=False) as archive:
            return column in list(archive.files)
    try:
        import pyarrow.parquet as pq
    except ImportError:
        # Thrift compact encodes a short string as one length byte then the bytes, so
        # `\x03day` is the column path as the footer spells it. `_parquet_footer` has already
        # asserted the magic, and a name that is not a column does NOT match (proved below).
        return bytes([len(column)]) + column.encode("ascii") in _parquet_footer(path)
    return column in list(pq.ParquetFile(path).schema_arrow.names)


@pytest.mark.parametrize("spec", SPECS, ids=[s.name for s in SPECS])
def test_the_declared_date_column_is_in_the_panels_own_header(spec, requires_panel):
    path = REPO / spec.path
    requires_panel(path)
    if spec.date_col is not None:
        assert _has_column(path, spec.reader, spec.date_col), (
            f"{spec.name}: the catalogue declares date_col={spec.date_col!r} and the panel's "
            "own header does not carry it"
        )
    for col in spec.wrong_cuts:
        assert _has_column(path, spec.reader, col), (
            f"{spec.name}: declared wrong cut {col!r} is not in the header"
        )


def test_the_header_check_can_fail_and_did_not_pass_vacuously():
    """Two halves. A column that is NOT in a panel must be reported absent by each of the three
    readers — otherwise the parametrised test above is 126 green assertions of nothing. And the
    csv majority must actually be on disk here, which is what makes a skip a statement about a
    clone rather than about this run."""
    csvs = [s for s in SPECS if s.reader == "csv" and (REPO / s.path).exists()]
    assert len(csvs) >= 100, f"only {len(csvs)} csv panels on disk; the header check is hollow"
    assert not _has_column(REPO / csvs[0].path, "csv", "no_such_column_anywhere")
    for reader in ("parquet", "npz"):
        present = [s for s in SPECS if s.reader == reader and (REPO / s.path).exists()]
        assert present, f"no {reader} panel on disk to prove the check fires"
        assert not _has_column(REPO / present[0].path, reader, "no_such_column_anywhere")


def test_a_spec_that_contradicts_itself_raises():
    good = PanelSpec("ok", "data/x.csv.gz", "day", "iso_day", "csv", ("prev_day",))
    assert good.read_dtypes() == {"day": "str", "prev_day": "str"}
    with pytest.raises(CatalogueError, match="wrong cut"):
        PanelSpec("x", "data/x.csv.gz", "prev_day", "iso_day", "csv", ("prev_day",))
    with pytest.raises(CatalogueError, match="disagree"):
        PanelSpec("x", "data/x.csv.gz", None, "iso_day", "csv")
    with pytest.raises(CatalogueError, match="disagree"):
        PanelSpec("x", "data/x.csv.gz", "day", "none", "csv")
    with pytest.raises(CatalogueError, match="unknown date_format"):
        PanelSpec("x", "data/x.csv.gz", "day", "epoch", "csv")  # type: ignore[arg-type]
    with pytest.raises(CatalogueError, match="POSIX"):
        PanelSpec("x", "data\\x.csv.gz", "day", "iso_day", "csv")


def test_an_unknown_panel_name_raises_and_suggests():
    assert spec_for("fut_breadth_hourly").date_col == "day"
    with pytest.raises(CatalogueError, match="did you mean"):
        spec_for("breadth_hourly")
    with pytest.raises(CatalogueError, match="no catalogue entry"):
        spec_for("zzz_not_a_panel")


def test_the_dtype_hints_are_the_zero_padded_identifiers():
    """Four panels carry a zero-padded CIK that pandas reads as an int, losing the padding."""
    hinted = {s.name: dict(s.dtype_hints) for s in SPECS if s.dtype_hints}
    assert hinted == {
        "d444_issuance_panel": {"cik": "str"},
        "d454_insider_events": {"cik": "str"},
        "d454_insider_owner_rows": {"RPTOWNERCIK": "str"},
        "d456_8k_events": {"cik": "str"},
    }


# ------------------------------------------------------------------ the cut


def test_convert_cut_per_format():
    assert convert_cut("iso_day", CUT) == CUT
    assert convert_cut("iso_ts", CUT) == CUT
    assert convert_cut("date32", CUT) == CUT
    assert convert_cut("yyyymm", CUT) == "202001"
    assert convert_cut("yyyy_mm", CUT) == "2020-01"
    assert convert_cut("year_prefix", CUT) == "2020"
    assert convert_cut("yyyymm", "2020-07-01") == "202007"


def test_a_cut_a_format_cannot_express_raises_rather_than_rounding():
    with pytest.raises(PanelCutError, match="first of a month"):
        convert_cut("yyyymm", "2020-01-15")
    with pytest.raises(PanelCutError, match="YEAR"):
        convert_cut("year_prefix", "2020-07-01")
    with pytest.raises(PanelCutError, match="no date"):
        convert_cut("none", CUT)
    with pytest.raises(PanelError, match="NO DEFAULT"):
        convert_cut("iso_day", "2020-1-1")
    with pytest.raises(PanelError, match="not a real date"):
        convert_cut("iso_day", "2020-02-30")


# ------------------------------------------------------------------ panel_status


def test_panel_status_has_three_answers_and_the_two_messages_are_the_old_ones(tmp_path):
    present = REPO / "data" / "fixtures" / "fut_index_rolls.csv.gz"
    if present.exists():
        assert panel_status(present) == "present"
    listed_absent = tmp_path / "fut_index_rolls.csv.gz"
    unlisted_absent = tmp_path / "not_a_panel_at_all.csv.gz"
    assert panel_status(listed_absent) == "absent_listed"
    assert panel_status(unlisted_absent) == "absent_unlisted"
    assert "left the index in D536" in absent_reason(listed_absent.name)
    assert "Skipping here would report a bug as absent data" in unlisted_message(unlisted_absent)


def test_the_conftest_adapter_still_draws_the_same_line(requires_panel, tmp_path):
    """`requires_panel` is now four lines over `panel_status`. Same three branches."""
    with pytest.raises(FileNotFoundError, match="does not list it"):
        requires_panel(tmp_path / "not_a_panel_at_all.csv.gz")
    with pytest.raises(pytest.skip.Exception):
        requires_panel(tmp_path / "fut_index_rolls.csv.gz")


# ------------------------------------------------------------------ the synthetic repository


def _write(path: Path, header: str, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join([header, *rows]) + "\n"
    raw = open(path, "wb")
    try:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            gz.write(body.encode("utf-8"))
    finally:
        raw.close()


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    """A repository with two panels, a manifest, and a catalogue of five specs."""
    fixtures = tmp_path / "data" / "fixtures"
    days = fixtures / "t_days.csv.gz"
    _write(days, "root,day,prev_day,close", [
        "ES,2019-12-30,2019-12-29,3200.0",
        "ES,2019-12-31,2019-12-30,3230.0",
        "ES,2020-01-02,2019-12-31,3260.0",
    ])
    months = fixtures / "t_months.csv.gz"
    _write(months, "period,x", ["2019-11,1.0", "2019-12,2.0", "2020-01,3.0"])
    stacked = fixtures / "t_stacked.csv.gz"
    _write(stacked, "freq,period,x", ["M,201912,1.0", "Q,20194,2.0", "M,202001,3.0"])

    files = []
    for path in (days, months, stacked):
        files.append({
            "path": f"data/fixtures/{path.name}", "bytes": path.stat().st_size,
            "sha256": _sha(path), "git_blob": None, "sidecars": [],
        })
    d32 = fixtures / "t_d32.parquet"
    d32.write_bytes(b"PAR1-not-really-a-parquet-file")
    files.append({"path": "data/fixtures/t_d32.parquet", "bytes": d32.stat().st_size,
                  "sha256": _sha(d32), "git_blob": None, "sidecars": []})
    files.append({"path": "data/fixtures/t_gone.csv.gz", "bytes": 0, "sha256": "0" * 64,
                  "git_blob": "deadbeef", "sidecars": []})
    manifest = tmp_path / "data" / "data_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"files": files, "count": len(files)}, indent=2) + "\n")

    specs = {
        "t_days": PanelSpec("t_days", "data/fixtures/t_days.csv.gz", "day", "iso_day", "csv",
                            ("prev_day",)),
        "t_months": PanelSpec("t_months", "data/fixtures/t_months.csv.gz", "period", "yyyy_mm",
                              "csv"),
        "t_stacked": PanelSpec("t_stacked", "data/fixtures/t_stacked.csv.gz", "period",
                               "year_prefix", "csv"),
        "t_gone": PanelSpec("t_gone", "data/fixtures/t_gone.csv.gz", "day", "iso_day", "csv"),
        "t_never": PanelSpec("t_never", "data/fixtures/t_never.csv.gz", "day", "iso_day", "csv"),
        "t_nodate": PanelSpec("t_nodate", "data/fixtures/t_nodate.npz", None, "none", "npz"),
        "t_d32": PanelSpec("t_d32", "data/fixtures/t_d32.parquet", "date", "date32", "parquet"),
    }
    monkeypatch.setattr(P, "REPO", tmp_path)
    monkeypatch.setattr(P, "MANIFEST", manifest)
    monkeypatch.setattr(P, "spec_for", lambda n: specs[n])
    monkeypatch.setattr(CAT, "spec_for", lambda n: specs[n])
    P._manifest.cache_clear()
    P.panel_names.cache_clear()
    P._entries_by_name.cache_clear()
    yield tmp_path
    P._manifest.cache_clear()
    P.panel_names.cache_clear()
    P._entries_by_name.cache_clear()


def test_the_blocked_read_is_the_good_case_and_it_comes_first(fake_repo):
    loaded = load_panel("t_days", reserved_from=CUT)
    assert list(loaded.frame["day"]) == ["2019-12-30", "2019-12-31"]
    assert loaded.record["first_session_read"] == "2019-12-30"
    assert loaded.record["last_session_read"] == "2019-12-31"
    assert loaded.record["reserved_from"] == CUT
    assert loaded.record["cut_applied"] == CUT
    assert loaded.record["sessions_read"] == 2
    assert loaded.record["distinct_sessions_read"] == 2
    assert loaded.record["reserved_rows_read"] == 0
    assert loaded.record["opened_on_the_word"] is False
    assert loaded.status == "present"
    assert loaded.sha256 == _sha(fake_repo / "data" / "fixtures" / "t_days.csv.gz")


def test_a_panel_whose_bytes_moved_under_the_manifest_raises_naming_both_digests(fake_repo):
    path = fake_repo / "data" / "fixtures" / "t_days.csv.gz"
    before = _sha(path)
    _write(path, "root,day,prev_day,close", ["ES,2019-12-30,2019-12-29,9999.0"])
    after = _sha(path)
    assert before != after
    with pytest.raises(PanelDigestError) as excinfo:
        load_panel("t_days", reserved_from=CUT)
    assert before in str(excinfo.value) and after in str(excinfo.value)


def test_usecols_may_project_a_wrong_cut_but_never_away_the_date_column(fake_repo):
    kept = load_panel("t_days", reserved_from=CUT, usecols=["day", "close"])
    assert list(kept.frame.columns) == ["day", "close"]
    with pytest.raises(PanelError, match="Projecting it away"):
        load_panel("t_days", reserved_from=CUT, usecols=["close"])


def test_absent_listed_is_a_skip_and_absent_unlisted_is_a_bug(fake_repo):
    with pytest.raises(PanelAbsent) as listed:
        load_panel("t_gone", reserved_from=CUT)
    assert listed.value.status == "absent_listed"
    assert "left the index in D536" in str(listed.value)
    with pytest.raises(PanelAbsent) as unlisted:
        load_panel("t_never", reserved_from=CUT)
    assert unlisted.value.status == "absent_unlisted"
    assert "wrong path" in str(unlisted.value)
    assert isinstance(unlisted.value, FileNotFoundError)


def test_a_panel_with_no_date_column_is_refused(fake_repo):
    with pytest.raises(PanelError, match="no date column"):
        load_panel("t_nodate", reserved_from=CUT)


def test_the_two_period_formats(fake_repo):
    months = load_panel("t_months", reserved_from=CUT)
    assert list(months.frame["period"]) == ["2019-11", "2019-12"]
    assert months.record["cut_applied"] == "2020-01"
    assert months.record["reserved_from"] == CUT
    with pytest.raises(PanelCutError, match="first of a month"):
        load_panel("t_months", reserved_from="2020-01-15")


def test_a_stacked_frequency_column_is_cut_on_the_year_the_two_share(fake_repo):
    """`hkm_factors`'s shape, reproduced small: monthly `201912` beside quarterly `20194`."""
    stacked = load_panel("t_stacked", reserved_from=CUT)
    assert list(stacked.frame["period"]) == ["201912", "20194"]
    assert stacked.record["cut_applied"] == "2020"
    assert stacked.record["first_session_read"] == "2019"
    with pytest.raises(PanelCutError, match="YEAR"):
        load_panel("t_stacked", reserved_from="2020-04-01")


def test_a_mixed_width_period_column_declared_monthly_raises(fake_repo, monkeypatch):
    """The check that caught `hkm_factors`. Declared `yyyymm`, the stacked panel must refuse."""
    spec = PanelSpec("t_stacked", "data/fixtures/t_stacked.csv.gz", "period", "yyyymm", "csv")
    monkeypatch.setattr(P, "spec_for", lambda n: spec)
    with pytest.raises(PanelError, match="mixes widths"):
        load_panel("t_stacked", reserved_from=CUT)


def test_opening_needs_the_word_and_the_words(fake_repo):
    with pytest.raises(PanelRefused, match="REFUSED"):
        load_panel("t_days", reserved_from=CUT, instruction="let me in")
    with pytest.raises(PanelError, match="verbatim"):
        load_panel("t_days", reserved_from=CUT, word=True)
    with pytest.raises(PanelError, match="verbatim"):
        load_panel("t_days", reserved_from=CUT, word=True, instruction="   ")
    with pytest.raises(PanelError, match="must be a bool"):
        load_panel("t_days", reserved_from=CUT, word=1)  # type: ignore[arg-type]


def test_an_opening_on_the_word_reads_the_whole_panel_and_records_the_reserved_rows(fake_repo):
    opened = load_panel("t_days", reserved_from=CUT, word=True, instruction=WORD)
    assert list(opened.frame["day"]) == ["2019-12-30", "2019-12-31", "2020-01-02"]
    assert opened.record["reserved_rows_read"] == 1
    assert opened.record["last_session_read"] == "2020-01-02"
    assert opened.record["opened_on_the_word"] is True


def test_an_opening_whose_in_sample_rows_differ_from_the_blocked_read_raises(fake_repo, monkeypatch):
    """run_d574:106-108's assert, made generic — and BROKEN at what it reads.

    The break is in the SECOND read, in the `close` column, which no hand-written comparison
    list would have named; the whole-frame comparison catches it anyway.
    """
    real = P._read_frame
    calls = {"n": 0}

    def flaky(spec, path, usecols):
        frame = real(spec, path, usecols)
        calls["n"] += 1
        if calls["n"] == 2:
            frame = frame.copy()
            frame.loc[0, "close"] = frame.loc[0, "close"] + 1.0
        return frame

    monkeypatch.setattr(P, "_read_frame", flaky)
    with pytest.raises(PanelError, match=r"\[OPEN\]"):
        load_panel("t_days", reserved_from=CUT, word=True, instruction=WORD)
    assert calls["n"] == 2, "the opened path must read the file twice, independently"


def test_the_read_log_appends_one_json_line_per_read(fake_repo, tmp_path):
    log = tmp_path / "logs" / "reads.jsonl"
    load_panel("t_days", reserved_from=CUT, read_log=log)
    load_panel("t_months", reserved_from=CUT, read_log=log)
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["panel"] == "t_days" and first["reserved_from"] == CUT
    assert first["instruction"] is None and first["read_utc"].endswith("Z")
    assert first["sha256"] == _sha(fake_repo / "data" / "fixtures" / "t_days.csv.gz")
    assert log.read_bytes().count(b"\r\n") == 0, "the log is LF-pinned (D550)"


def test_windows_update_merges_into_a_runners_block_and_refuses_a_changed_value(fake_repo):
    loaded = load_panel("t_days", reserved_from=CUT)
    existing = {"primary": ["2016-01-04", "2023-12-29"], "month_ends": 163, "reserved_from": CUT}
    merged = loaded.windows_update(existing)
    assert merged["primary"] == ["2016-01-04", "2023-12-29"] and merged["month_ends"] == 163
    assert set(merged) == set(existing) | set(P.WINDOW_KEYS)
    assert existing == {"primary": ["2016-01-04", "2023-12-29"], "month_ends": 163,
                        "reserved_from": CUT}, "windows_update must not mutate its argument"
    with pytest.raises(PanelError, match="would make it"):
        loaded.windows_update({"reserved_from": "2024-01-01"})


# ------------------------------------------------------------------ two real, blocked reads


def test_a_real_panel_reads_through_the_door_and_agrees_with_the_manifest(requires_panel):
    path = REPO / "data" / "fixtures" / "fut_index_rolls.csv.gz"
    requires_panel(path)
    loaded = load_panel("fut_index_rolls", reserved_from="2024-01-01")
    entry = {f["path"]: f for f in json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]}
    assert loaded.sha256 == entry["data/fixtures/fut_index_rolls.csv.gz"]["sha256"]
    assert loaded.record["reserved_rows_read"] == 0
    assert loaded.record["last_session_read"] < "2024-01-01"
    assert (loaded.frame["day"] < "2024-01-01").all()


def test_the_panel_that_is_entirely_inside_the_reserved_slice_returns_nothing(requires_panel):
    """`fut_book_depth_1m` spans 2026-08-11..2026-09-09 — inside the deposit's vault window AND
    after this repository's seal. Zero rows is the correct answer, and it is the case that
    proves `reserved_from` must have no default."""
    path = REPO / "data" / "fixtures" / "fut_book_depth_1m.csv.gz"
    requires_panel(path)
    loaded = load_panel("fut_book_depth_1m", reserved_from="2024-01-01")
    assert len(loaded.frame) == 0
    assert loaded.record["sessions_read"] == 0
    assert loaded.record["first_session_read"] is None
    assert loaded.record["reserved_rows_read"] == 0


def test_a_coerced_datetime_would_have_slipped_the_guard():
    """The arithmetic behind the date32 branch, stated before the branch is tested.

    `frozen._day_strings` REFUSES a datetime dtype rather than coercing it, and this is why:
    stringified, a datetime64 sorts AFTER the bare day, so `>= cut` would be true for the row
    AT the cut under a `<` filter written the obvious way — and the reserved row would survive
    the filter that exists to drop it.
    """
    import numpy as np

    assert str(np.datetime64("2020-01-01", "ns")) == "2020-01-01T00:00:00.000000000"
    assert "2020-01-01T00:00:00.000000000" > "2020-01-01"
    assert str(pd.Timestamp("2020-01-01").to_datetime64()) > "2020-01-01"


def test_a_date32_column_is_converted_at_the_door_and_the_cut_then_bites(fake_repo, monkeypatch):
    """`D2_US_factors_SAS.parquet` is the only `date32[day]` panel. Its reader is monkeypatched
    here because the venv has no pyarrow; the code path under test — `_read_frame`'s date32
    branch, then the three layers — is the production one, unchanged."""
    frame = pd.DataFrame({"date": pd.to_datetime(["2019-12-31", "2020-01-01", "2020-06-30"]),
                          "ret": [0.1, 0.2, 0.3]})
    monkeypatch.setattr(pd, "read_parquet", lambda path, columns=None: frame.copy())
    loaded = load_panel("t_d32", reserved_from=CUT)
    assert list(loaded.frame["date"]) == ["2019-12-31"]
    assert loaded.record["last_session_read"] == "2019-12-31"
    assert loaded.record["reserved_rows_read"] == 0
    assert list(loaded.frame["ret"]) == [0.1]
