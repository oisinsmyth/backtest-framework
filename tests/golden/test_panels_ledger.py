"""Golden: the loader reproduces D555's own numbers on D555's own panel (D609).

`tests/golden/test_panels_ledger.hand.txt` was written first and every number here is quoted
from it. The hand file's numbers came from sources that existed before
`src/backtest_framework/data/panels.py` did: `data/d555_tsmom_replication.json` (committed
2026-09-19), `data/data_manifest.json`, and `scripts/run_d555_tsmom_replication.py`'s own
`load_fixture()` run out of its committed source.

WHY THE RUNNER IS COMPILED AND NOT IMPORTED
-------------------------------------------
D606's lesson, applied: importing a runner runs its module body, and `run_d365_momentum_buffer`
installs an `sys.addaudithook` that CPython cannot remove, which poisoned an unrelated gate for
the rest of the process. `run_d555_tsmom_replication.py` installs no hook today — checked — but
"today" is the whole of the argument against relying on it. `_load_fixture_from_runner` parses
the runner's source and compiles ONLY `load_fixture` plus the two module constants it closes
over, in a namespace holding pandas and numpy. The pin is unchanged in strength: it is still
the runner's committed bytes.

Source is read as BYTES with CRLF normalised to LF before parsing (D550): `.gitattributes` pins
`eol=lf` in the index and this worktree carries CRLF.

No row dated 2024-01-01 or later is read. Both routes cut at 2024-01-01 and both are asserted
to have read zero reserved rows.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backtest_framework.data.panels import WINDOW_KEYS, load_panel

REPO = Path(__file__).resolve().parents[2]
HAND = Path(__file__).with_suffix(".hand.txt")
FIX = REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz"
MANIFEST = REPO / "data" / "data_manifest.json"
D555_ARTEFACT = REPO / "data" / "d555_tsmom_replication.json"

FIXTURE_SHA = "c64dfe70211242368772da005e05e11ed2f2e779e6599d0e0a6a2bbabee355de"
ROWS_LOADER = 140_814
ROWS_D555 = 118_214
DROPPED_NO_CLOSE = 22_531
DROPPED_WEEKEND = 69
FIRST_DAY = "2010-06-07"
LAST_DAY = "2023-12-29"
DISTINCT_DAYS = 4_217
RESERVED_FROM = "2024-01-01"


def _load_fixture_from_runner():
    """`run_d555_tsmom_replication.load_fixture`, compiled alone. See the module docstring."""
    path = REPO / "scripts" / "run_d555_tsmom_replication.py"
    source = path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    tree = ast.parse(source, filename=str(path))
    namespace: dict[str, object] = {"pd": pd, "np": np, "FIX": FIX}
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") in (
            "SEGS",
            "RESERVED_FROM",
        ):
            namespace[node.targets[0].id] = ast.literal_eval(node.value)
    for name in ("SEGS", "RESERVED_FROM"):
        if name not in namespace:
            raise AssertionError(f"{path.name} no longer defines {name} at top level")
    assert namespace["RESERVED_FROM"] == RESERVED_FROM
    found = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "load_fixture"]
    if len(found) != 1:
        raise AssertionError(
            f"{path.name} defines load_fixture {len(found)} times at top level; a silently "
            "absent function would make this golden pass by testing nothing"
        )
    exec(compile(ast.Module(body=found, type_ignores=[]), str(path), "exec"), namespace)
    return namespace["load_fixture"], namespace["SEGS"]


@pytest.fixture(scope="module")
def both_routes(requires_panel):
    requires_panel(FIX)
    load_fixture, segs = _load_fixture_from_runner()
    theirs = load_fixture()
    cols = ["root", "day", "contract", "same_front", "h18_o"] + [s + "_c" for s in segs]
    mine = load_panel("fut_breadth_hourly", reserved_from=RESERVED_FROM, usecols=cols)
    return mine, theirs


def test_hand_file_is_present_and_names_its_sources():
    text = HAND.read_text(encoding="utf-8")
    assert FIXTURE_SHA in text
    assert "run_d555.load_fixture()" in text
    assert f"{ROWS_LOADER:,}" in text and f"{ROWS_D555:,}" in text


# ------------------------------------------------------------------ SS1


def test_the_digest_reproduces_d555s_published_fixture_sha256(both_routes):
    """Three routes to one number: the loader, the manifest, and D555's artefact (R16)."""
    mine, _ = both_routes
    manifest = {f["path"]: f for f in json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]}
    published = json.loads(D555_ARTEFACT.read_text(encoding="utf-8"))["fixture_sha256"]
    assert mine.sha256 == FIXTURE_SHA
    assert manifest["data/fixtures/fut_breadth_hourly.csv.gz"]["sha256"] == FIXTURE_SHA
    assert published == FIXTURE_SHA


# ------------------------------------------------------------------ SS2


def test_the_row_counts_reconcile_through_the_runners_own_drop_counts(both_routes):
    """`load_panel` cuts and nothing else; `load_fixture` cuts and then drops two classes of
    non-session row, recording both counts itself. The identity is exact."""
    mine, theirs = both_routes
    assert len(mine.frame) == ROWS_LOADER
    assert len(theirs) == ROWS_D555
    assert theirs.attrs["rows_dropped_no_close"] == DROPPED_NO_CLOSE
    assert theirs.attrs["rows_dropped_weekend_stub"] == DROPPED_WEEKEND
    assert len(mine.frame) - DROPPED_NO_CLOSE - DROPPED_WEEKEND == len(theirs)


def test_the_last_and_first_session_agree_as_strings(both_routes):
    """Not implied by the counts: it says the last session survives both of D555's drops, so
    the cut is what binds at the right-hand end in BOTH routes."""
    mine, theirs = both_routes
    assert mine.frame["day"].max() == theirs["day"].max() == LAST_DAY
    assert mine.frame["day"].min() == theirs["day"].min() == FIRST_DAY
    assert (mine.frame["day"] < RESERVED_FROM).all()
    assert (theirs["day"] < RESERVED_FROM).all()


# ------------------------------------------------------------------ SS3


def test_the_window_record_is_the_hand_files_six_numbers(both_routes):
    mine, _ = both_routes
    assert {k: mine.record[k] for k in WINDOW_KEYS} == {
        "first_session_read": FIRST_DAY,
        "last_session_read": LAST_DAY,
        "reserved_from": RESERVED_FROM,
        "sessions_read": ROWS_LOADER,
        "distinct_sessions_read": DISTINCT_DAYS,
        "reserved_rows_read": 0,
    }


def test_the_distinct_day_count_is_larger_than_both_of_d555s_windows(both_routes):
    """4,217 must exceed 3,353 and 2,065: it counts every day in the file from 2010-06-07,
    including the Sundays and holidays `load_fixture` drops and the pre-2011 days neither of
    D555's windows covers. A distinct count that came out SMALLER would mean the loader had
    lost days the study had."""
    mine, _ = both_routes
    windows = json.loads(D555_ARTEFACT.read_text(encoding="utf-8"))["windows"]
    assert windows["sessions_long"] == 3353 and windows["sessions_primary"] == 2065
    assert mine.record["distinct_sessions_read"] == DISTINCT_DAYS > windows["sessions_long"]


# ------------------------------------------------------------------ SS4


def test_windows_update_merges_into_d555s_committed_block_without_losing_a_key(both_routes):
    mine, _ = both_routes
    committed = json.loads(D555_ARTEFACT.read_text(encoding="utf-8"))["windows"]
    assert set(committed) == {"primary", "long", "reserved_from", "sessions_primary",
                              "sessions_long", "month_ends"}
    assert set(committed) & set(WINDOW_KEYS) == {"reserved_from"}
    merged = mine.windows_update(committed)
    assert len(merged) == 11
    for key, value in committed.items():
        assert merged[key] == value, key
    for key in WINDOW_KEYS:
        assert merged[key] == mine.record[key], key


# ------------------------------------------------------------------ SS5


def test_the_panel_that_is_entirely_reserved_reads_as_zero_rows(requires_panel):
    depth = REPO / "data" / "fixtures" / "fut_book_depth_1m.csv.gz"
    requires_panel(depth)
    loaded = load_panel("fut_book_depth_1m", reserved_from=RESERVED_FROM)
    assert len(loaded.frame) == 0
    assert {k: loaded.record[k] for k in WINDOW_KEYS} == {
        "first_session_read": None,
        "last_session_read": None,
        "reserved_from": RESERVED_FROM,
        "sessions_read": 0,
        "distinct_sessions_read": 0,
        "reserved_rows_read": 0,
    }


# ------------------------------------------------------------------ SS6


def test_the_catalogues_counts_are_the_hand_files_counts():
    from collections import Counter

    from backtest_framework.data.panel_catalogue import SPECS

    # 126 at D609; 128 after round 4's integration added D612's attention sample and D619's
    # fund NAV panel to the manifest (2026-09-22) -- both csv, one iso_ts, one iso_day; 132 after round 4b
    # added D620's quarterly holdings and projected UNG/USO panels and D621's Robinhood holders and
    # GDELT hourly sample (the same day) -- four csv, two iso_day, two iso_ts.
    assert len(SPECS) == 132
    assert Counter(s.date_format for s in SPECS) == {
        "iso_day": 79, "iso_ts": 32, "none": 19, "date32": 1, "year_prefix": 1
    }
    assert Counter(s.reader for s in SPECS) == {"csv": 109, "npz": 16, "parquet": 7}
    assert sum(1 for s in SPECS if s.date_col) == 113
    assert Counter(s.date_col for s in SPECS if s.date_col) == {
        "day": 59, "timestamp": 29, "session": 5, "filing": 3, "ref": 3, "date": 4,
        "avail_date": 2, "report_date": 1, "date_entry": 1, "filed": 1, "period": 1,
        "observed_at_utc": 1, "filed_date": 1, "hour_utc": 1, "ts_utc": 1,
    }
    assert sum(1 for s in SPECS if s.wrong_cuts) == 25
    assert sorted({c for s in SPECS for c in s.wrong_cuts}) == [
        "anchor_filed_date", "anchor_period_end", "available_at_utc", "bucket_start", "date_g", "delist_date", "expiry_date",
        "fetched_at", "fiscal_date", "last_live_date", "oi_pub_et", "period_end", "prev_day",
        "published_at_et", "published_et", "ref_session", "release_date_nominal", "report",
        "trans", "trans_max", "trans_min", "ts_utc",
    ]
