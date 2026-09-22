"""D609 -- the panel catalogue's audit and the loader's self-test.

    uv run python scripts/panel_catalogue_check.py --audit     # every manifest panel: status,
                                                               # declared column, header check
    uv run python scripts/panel_catalogue_check.py --selftest   # prove every guard RAISES

`--audit` reads each panel's HEADER ONLY -- the first line of a `.csv.gz`, the arrow schema of a
`.parquet`, the key list of an `.npz`. It reads no data row, which matters because
`data/fixtures/fut_book_depth_1m.csv.gz` begins on 2026-08-11: a "sample the first row" audit
would read a reserved row to check a column name.

PARQUET NEEDS pyarrow, WHICH THE VENV HAS NOT GOT -- so the seven `.parquet` rows fall back to
a FOOTER SCAN: the file's own trailer, length-prefixed and magic-checked, searched for the
thrift-encoded column name. That confirms a name and cannot list them, which is weaker and is
not nothing. Under the system python (`python scripts/panel_catalogue_check.py --audit`) the
schema is read outright. Both invocations are recorded in D609 and both report 0 disagreements.

`--selftest` builds its own panels in a temporary directory with its own manifest, so every
raise below is proved on a frame this script constructed. NOTHING IT READS IS A REAL FIXTURE and
no row dated 2024-01-01 or later is read from one.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data import panel_catalogue as CAT  # noqa: E402
from backtest_framework.data import panels as P  # noqa: E402


def say(*a: object) -> None:
    print(*a, flush=True)


# ------------------------------------------------------------------ the audit


def parquet_footer(path: Path) -> bytes:
    """The parquet footer's raw bytes, without pyarrow.

    The last four bytes are the magic `PAR1`; the four before them are the footer's length,
    little-endian. The magic is checked, which is what makes a substring search over these
    bytes a check on the schema block rather than a guess about the file.
    """
    import struct

    with open(path, "rb") as handle:
        handle.seek(-8, 2)
        length = struct.unpack("<I", handle.read(4))[0]
        magic = handle.read(4)
        if magic != b"PAR1":
            raise ValueError(f"{path.name} does not end with the parquet magic: {magic!r}")
        handle.seek(-(8 + length), 2)
        return handle.read(length)


def header_columns(path: Path, reader: str) -> tuple[list[str] | None, str]:
    """The panel's column names, read from its header and nothing else.

    With pyarrow absent the parquet branch returns None and the caller falls back to
    `has_column`, which searches the footer for the thrift-encoded name. Weaker -- it can
    confirm a name and cannot list them -- and it is never nothing.
    """
    if reader == "csv":
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            line = handle.readline().rstrip("\r\n")
        return line.split(","), ""
    if reader == "parquet":
        try:
            import pyarrow.parquet as pq
        except ImportError:
            return None, "footer scan (no pyarrow)"
        return list(pq.ParquetFile(path).schema_arrow.names), ""
    if reader == "npz":
        import numpy as np

        with np.load(path, allow_pickle=False) as z:
            return list(z.files), ""
    return None, f"header_unreadable (no reader for {reader!r})"


def has_column(path: Path, reader: str, cols: list[str] | None, column: str) -> bool:
    if cols is not None:
        return column in cols
    if reader == "parquet":
        # Thrift compact encodes a short string as one length byte then the bytes.
        return bytes([len(column)]) + column.encode("ascii") in parquet_footer(path)
    return False


def cmd_audit() -> int:
    manifest_paths = {f["path"] for f in json.loads(P.MANIFEST.read_text(encoding="utf-8"))["files"]}
    catalogue_paths = {s.path for s in CAT.SPECS}
    say(f"  manifest {len(manifest_paths)} panels, catalogue {len(catalogue_paths)} rows")
    only_manifest = sorted(manifest_paths - catalogue_paths)
    only_catalogue = sorted(catalogue_paths - manifest_paths)
    for p in only_manifest:
        say(f"  UNDECLARED  {p}  -- in the manifest, not in panel_catalogue.py")
    for p in only_catalogue:
        say(f"  ORPHAN      {p}  -- in panel_catalogue.py, not in the manifest")

    say("")
    say(f"  {'panel':<34}{'status':<17}{'fmt':<12}{'date_col':<22}header")
    disagreements = len(only_manifest) + len(only_catalogue)
    unreadable = 0
    counts: dict[str, int] = {}
    for spec in CAT.SPECS:
        path = REPO / spec.path
        status = P.panel_status(path)
        counts[status] = counts.get(status, 0) + 1
        if status != "present":
            note = "not on disk"
        else:
            cols, why = header_columns(path, spec.reader)
            if cols is None and spec.reader != "parquet":
                note = why
                unreadable += 1
            else:
                if cols is None:
                    unreadable += 1
                bad = [c for c in spec.wrong_cuts if not has_column(path, spec.reader, cols, c)]
                if spec.date_col is not None and not has_column(path, spec.reader, cols, spec.date_col):
                    note = f"*** DISAGREES: header has no {spec.date_col!r}"
                    disagreements += 1
                elif bad:
                    note = f"*** DISAGREES: declared wrong_cuts absent from header {bad}"
                    disagreements += 1
                elif spec.date_col is None:
                    note = "no date column declared"
                else:
                    seen = f"{len(cols)} columns" if cols is not None else why
                    note = f"ok, {seen}, {len(spec.wrong_cuts)} wrong cut(s)"
        say(f"  {spec.name:<34}{status:<17}{spec.date_format:<12}{str(spec.date_col):<22}{note}")

    say("")
    say(f"  status: {counts}")
    say(f"  full schemas unreadable here: {unreadable} (parquet needs pyarrow; those rows were "
        "checked by a footer scan, and the system python reads their schema outright)")
    say(f"  DISAGREEMENTS: {disagreements}")
    return 1 if disagreements else 0


# ------------------------------------------------------------------ the self-test


class SelftestError(AssertionError):
    pass


def expect_raise(fn, exc, what: str, fragment: str = "") -> None:
    try:
        fn()
    except exc as e:  # noqa: PERF203 - the point is the raise
        if fragment and fragment not in str(e):
            raise SelftestError(f"{what}: raised {exc.__name__} but not about {fragment!r}: {e}")
        say(f"    RAISES {exc.__name__} on {what}: {str(e)[:96]}")
        return
    raise SelftestError(f"NO RAISE on {what} -- a guard that cannot fire is worse than none")


def _write_panel(path: Path, header: str, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join([header, *rows]) + "\n"
    with gzip.GzipFile(filename="", mode="wb", fileobj=open(path, "wb"), mtime=0) as gz:
        gz.write(body.encode("utf-8"))


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_selftest(tmp: Path) -> int:
    """Build a synthetic repository, then prove each refusal on it.

    Every date here is synthetic and the cut is 2020-01-01, NOT this repository's 2024-01-01:
    a self-test that used the real seal date would be one copy-paste away from becoming a
    reason to read the real reserved slice.
    """
    import pandas as pd

    say("[0] a synthetic repository, its own manifest, its own seal date 2020-01-01")
    data = tmp / "data" / "fixtures"
    ok_path = data / "selftest_ok.csv.gz"
    _write_panel(
        ok_path,
        "root,day,prev_day,close",
        [
            "ES,2019-12-30,2019-12-29,3200.0",
            "ES,2019-12-31,2019-12-30,3230.0",
            "ES,2020-01-02,2019-12-31,3260.0",
            "ES,2020-01-03,2020-01-02,3240.0",
        ],
    )
    period_path = data / "selftest_period.csv.gz"
    _write_panel(period_path, "period,x", ["2019-11,1.0", "2019-12,2.0", "2020-01,3.0"])
    manifest = {
        "built_at": "1970-01-01T00:00:00Z",
        "note": "synthetic, D609 selftest",
        "suffixes": [".csv.gz"],
        "files": [
            {"path": "data/fixtures/selftest_ok.csv.gz", "bytes": ok_path.stat().st_size,
             "sha256": _sha(ok_path), "git_blob": None, "sidecars": []},
            {"path": "data/fixtures/selftest_period.csv.gz", "bytes": period_path.stat().st_size,
             "sha256": _sha(period_path), "git_blob": None, "sidecars": []},
            {"path": "data/fixtures/selftest_listed_absent.csv.gz", "bytes": 0,
             "sha256": "0" * 64, "git_blob": None, "sidecars": []},
        ],
    }
    manifest["count"] = len(manifest["files"])
    manifest["total_bytes"] = sum(f["bytes"] for f in manifest["files"])
    man_path = tmp / "data" / "data_manifest.json"
    man_path.parent.mkdir(parents=True, exist_ok=True)
    with open(man_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, indent=2) + "\n")

    specs = (
        CAT.PanelSpec("selftest_ok", "data/fixtures/selftest_ok.csv.gz", "day", "iso_day", "csv",
                      ("prev_day",)),
        CAT.PanelSpec("selftest_period", "data/fixtures/selftest_period.csv.gz", "period",
                      "yyyy_mm", "csv", ()),
        CAT.PanelSpec("selftest_listed_absent", "data/fixtures/selftest_listed_absent.csv.gz",
                      "day", "iso_day", "csv", ()),
        CAT.PanelSpec("selftest_unlisted", "data/fixtures/selftest_unlisted.csv.gz", "day",
                      "iso_day", "csv", ()),
        CAT.PanelSpec("selftest_nodate", "data/fixtures/selftest_nodate.npz", None, "none",
                      "npz", ()),
    )
    by_name = {s.name: s for s in specs}
    real_repo, real_manifest = P.REPO, P.MANIFEST
    real_spec_for = CAT.spec_for
    P.REPO, P.MANIFEST = tmp, man_path
    P._manifest.cache_clear()
    P.panel_names.cache_clear()
    P._entries_by_name.cache_clear()
    CAT.spec_for = lambda n: by_name[n]
    P.spec_for = CAT.spec_for
    try:
        return _selftest_body(tmp, ok_path, pd)
    finally:
        P.REPO, P.MANIFEST = real_repo, real_manifest
        CAT.spec_for = real_spec_for
        P.spec_for = real_spec_for
        P._manifest.cache_clear()
        P.panel_names.cache_clear()
        P._entries_by_name.cache_clear()


def _selftest_body(tmp: Path, ok_path: Path, pd) -> int:
    CUT = "2020-01-01"

    say("[1] the good case FIRST -- the loader must return the right frame before any raise")
    loaded = P.load_panel("selftest_ok", reserved_from=CUT)
    assert list(loaded.frame["day"]) == ["2019-12-30", "2019-12-31"], loaded.frame
    assert loaded.record["reserved_rows_read"] == 0
    assert loaded.record["distinct_sessions_read"] == 2
    assert loaded.sha256 == _sha(ok_path)
    say(f"    2 of 4 rows kept, record {loaded.record['first_session_read']}.."
        f"{loaded.record['last_session_read']}, sha {loaded.sha256[:12]}")

    say("[2] reserved_from has NO DEFAULT")
    expect_raise(lambda: P.load_panel("selftest_ok"), TypeError,  # type: ignore[call-arg]
                 "load_panel without reserved_from", "reserved_from")

    say("[3] layer 2 fires on a row AT the cut when layer 1 is bypassed")
    # BREAK WHAT THE ASSERTION READS: the frame is built here, not filtered, so the assert is
    # handed exactly the row it exists to catch. Filtering and then checking with the same
    # expression would prove only that the expression is self-consistent.
    at_cut = pd.DataFrame({"day": ["2019-12-31", "2020-01-01"], "close": [1.0, 2.0]})
    from backtest_framework.validation.frozen import ReservedSliceError, assert_none_at_or_after

    expect_raise(lambda: assert_none_at_or_after(at_cut, "day", CUT), ReservedSliceError,
                 "a row exactly AT the cut", "2020-01-01")
    before = pd.DataFrame({"day": ["2019-12-30", "2019-12-31"], "close": [1.0, 2.0]})
    assert_none_at_or_after(before, "day", CUT)
    say("    ...and does NOT fire one day earlier (2019-12-31 passes)")

    say("[4] a digest that does not match the manifest")
    with gzip.GzipFile(filename="", mode="wb", fileobj=open(ok_path, "ab"), mtime=0) as gz:
        gz.write(b"ES,2019-12-27,2019-12-26,3100.0\n")
    P._manifest.cache_clear()
    P._entries_by_name.cache_clear()
    expect_raise(lambda: P.load_panel("selftest_ok", reserved_from=CUT), P.PanelDigestError,
                 "a panel whose bytes moved under the manifest", "data_manifest.json records")

    say("[5] a wrong_cuts column refused as a date column, at construction")
    expect_raise(
        lambda: CAT.PanelSpec("x", "data/x.csv.gz", "prev_day", "iso_day", "csv", ("prev_day",)),
        CAT.CatalogueError, "prev_day declared as BOTH date_col and wrong cut", "wrong cut")

    say("[6] word and instruction")
    expect_raise(lambda: P.load_panel("selftest_period", reserved_from=CUT, instruction="do it"),
                 P.PanelRefused, "an opening asked for without the word", "REFUSED")
    expect_raise(lambda: P.load_panel("selftest_period", reserved_from=CUT, word=True),
                 P.PanelError, "word=True with no instruction", "verbatim")

    say("[7] an opening whose in-sample rows differ from the blocked read")
    word = "the principal's word, 2026-09-22, for this self-test and nothing else"
    good = P.load_panel("selftest_period", reserved_from=CUT, word=True, instruction=word)
    assert len(good.frame) == 3 and good.record["reserved_rows_read"] == 1, good.record
    say(f"    the good case first: opened 3 rows, {good.record['reserved_rows_read']} of them "
        "reserved, and the blocked comparison passed")
    # BREAK WHAT THE ASSERTION READS. The check compares the SECOND read's in-sample rows
    # against the FIRST read's filtered frame, so the break is a second read that differs by
    # one value in a column no hand-written comparison list would have named.
    real_read = P._read_frame
    calls = {"n": 0}

    def flaky(spec, path, usecols):
        frame = real_read(spec, path, usecols)
        calls["n"] += 1
        if calls["n"] == 2:
            frame = frame.copy()
            frame.loc[0, "x"] = frame.loc[0, "x"] + 1.0
        return frame

    P._read_frame = flaky
    try:
        expect_raise(
            lambda: P.load_panel("selftest_period", reserved_from=CUT, word=True,
                                 instruction=word),
            P.PanelError, "an opened read whose in-sample rows differ by one value", "[OPEN]")
    finally:
        P._read_frame = real_read

    say("[8] absent: listed is a skip, unlisted is a bug")
    expect_raise(lambda: P.load_panel("selftest_unlisted", reserved_from=CUT), P.PanelAbsent,
                 "a panel the manifest does not list", "wrong path")
    try:
        P.load_panel("selftest_listed_absent", reserved_from=CUT)
    except P.PanelAbsent as e:
        if e.status != "absent_listed":
            raise SelftestError(f"[8] listed-absent reported status {e.status!r}")
        say(f"    status 'absent_listed' -> a SKIP, reason: {str(e)[:70]}")
    else:
        raise SelftestError("[8] no raise on a listed-but-absent panel")

    say("[9] a panel with no date column is refused, not waved through")
    expect_raise(lambda: P.load_panel("selftest_nodate", reserved_from=CUT), P.PanelError,
                 "a panel declaring date_format='none'", "no date column")

    say("[10] a cut the panel's own format cannot express")
    expect_raise(lambda: P.load_panel("selftest_period", reserved_from="2020-01-15"),
                 P.PanelCutError, "a mid-month cut on a monthly panel", "first of a month")
    per = P.load_panel("selftest_period", reserved_from=CUT)
    assert list(per.frame["period"]) == ["2019-11", "2019-12"], per.frame
    assert per.record["reserved_from"] == CUT and per.record["cut_applied"] == "2020-01"
    say("    ...and a month-start cut converts to '2020-01' and keeps 2 of 3 rows")

    say("[11] usecols may not drop the date column")
    expect_raise(lambda: P.load_panel("selftest_ok", reserved_from=CUT, usecols=["close"]),
                 P.PanelError, "usecols without the date column", "Projecting it away")

    say("[12] windows_update merges and refuses a changed value")
    merged = per.windows_update({"primary": ["2016-01-04", "2023-12-29"], "reserved_from": CUT})
    assert merged["primary"] == ["2016-01-04", "2023-12-29"] and len(merged) == 7, merged
    expect_raise(lambda: per.windows_update({"reserved_from": "2024-01-01"}), P.PanelError,
                 "a windows block already cut at a different date", "would make it")

    say("\n  all guards raised on their break; the good case ran first in every pair")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.audit:
        return cmd_audit()
    if args.selftest:
        import tempfile

        with tempfile.TemporaryDirectory(prefix="d609_selftest_") as td:
            return cmd_selftest(Path(td))
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
