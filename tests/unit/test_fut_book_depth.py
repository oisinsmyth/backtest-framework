"""Unit tests for the order-book depth fixture and its replay (D604).

The panel `data/fixtures/fut_book_depth_1m.csv.gz` is a bulk artefact: gitignored by suffix, and
registered in `data/data_manifest.json` by the integrator. **That window has closed** -- the
manifest row exists -- so the transitional second skip rule this file carried is gone (D609).

One rule applies: `requires_panel` (tests/conftest.py) skips when the file is absent and the
manifest lists it, and RAISES when a missing file is not a manifest panel, because a wrong path
must never be reported as absent data. `_panel(...)` below asserts the listing first, so the
message names the manifest rather than the file if the row ever disappears. The decision itself
lives once, at `backtest_framework.data.panels.panel_status`.

The replay tests need no panel at all: they push hand-built message sequences through the same
`replay_messages` the builder runs, so the arithmetic is gated on every machine.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from backtest_framework.costs.futures_impact import FuturesImpactError, depth_bar
from backtest_framework.data.panels import panel_status

REPO = Path(__file__).resolve().parents[2]
PANEL = REPO / "data" / "fixtures" / "fut_book_depth_1m.csv.gz"
META = REPO / "data" / "fixtures" / "fut_book_depth_1m.meta.json"
MANIFEST = REPO / "data" / "data_manifest.json"


def _builder():
    """`scripts/build_fut_book_depth.py` by explicit path.

    `scripts/` is not a package and pytest imports any path you name, so the module is loaded by
    location and registered in `sys.modules` before execution (its dataclasses need it). Its
    import-time work is reading nothing; `databento` is imported inside `replay`, which these
    tests never call, so this runs in the venv that has no databento.
    """
    path = REPO / "scripts" / "build_fut_book_depth.py"
    sys.path.insert(0, str(REPO / "scripts"))
    spec = importlib.util.spec_from_file_location("d604_build_fut_book_depth", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["d604_build_fut_book_depth"] = module
    spec.loader.exec_module(module)
    return module


B = _builder()


def _panel(requires_panel):
    """Skip when the panel is absent. See the module docstring: there is one rule again."""
    assert panel_status(PANEL) != "absent_unlisted", (
        f"{PANEL.name} is not in data/data_manifest.json. The transitional double-skip this "
        "file carried until D609 is gone, so an unlisted absence is now a loud failure -- "
        "which is the right answer once the manifest row exists."
    )
    requires_panel(PANEL)
    import pandas as pd

    return pd.read_csv(PANEL, dtype={"root": str, "day": str, "minute_et": str, "contract": str})


# ------------------------------------------------------------------ the replay arithmetic


def test_known_answer_book_matches_the_hand_worked_depth():
    """The hand-worked sequence in `synthetic_messages`'s docstring, through the production
    replay. A known-answer case first, before anything measured is believed."""
    msgs = B.synthetic_messages("2026-08-11", "09:29")
    out = B.replay_messages([msgs], "2026-08-11", ["09:30"], {7: ("ES", "ESU6")},
                            {7: int(round(0.25 / B.PX))})
    assert out["rows"] == [("ES", "2026-08-11", "09:30", "ESU6", 100.125, 1.0, 5, 7, 6, 9, 2, 2, 11)]


def test_a_trade_and_a_fill_do_not_move_resting_depth():
    """The one convention the replay rests on. Dropping the T and F messages must change nothing;
    if they moved depth, this row would differ."""
    msgs = B.synthetic_messages("2026-08-11", "09:29")
    kept = msgs[(msgs["action"] != b"T") & (msgs["action"] != b"F")]
    a = B.replay_messages([msgs], "2026-08-11", ["09:30"], {7: ("ES", "ESU6")},
                          {7: int(round(0.25 / B.PX))})["rows"][0]
    b = B.replay_messages([kept], "2026-08-11", ["09:30"], {7: ("ES", "ESU6")},
                          {7: int(round(0.25 / B.PX))})["rows"][0]
    assert a[:12] == b[:12]
    assert a[12] == 11 and b[12] == 9        # only n_events, the liveness counter, differs


def test_a_clear_empties_the_book_and_the_emit_guard_then_raises():
    msgs = B.synthetic_messages("2026-08-11", "09:29")
    cleared = msgs.copy()
    cleared[-1]["action"] = b"R"
    with pytest.raises(B.DepthError, match="one-sided book"):
        B.replay_messages([cleared], "2026-08-11", ["09:30"], {7: ("ES", "ESU6")},
                          {7: int(round(0.25 / B.PX))})


def test_the_band_is_five_ticks_of_the_mid_on_each_side_and_excludes_the_sixth():
    """`98.50` sits 6.5 ticks below the mid and `101.75` 6.5 above, so both are out; widening the
    band to 7 ticks pulls both in. The band is what 8A.4 fixes, so the test moves it deliberately
    rather than trusting that 5 was applied."""
    msgs = B.synthetic_messages("2026-08-11", "09:29")
    tick = {7: int(round(0.25 / B.PX))}
    narrow = B.replay_messages([msgs], "2026-08-11", ["09:30"], {7: ("ES", "ESU6")}, tick)["rows"][0]
    assert (narrow[8], narrow[9], narrow[10], narrow[11]) == (6, 9, 2, 2)
    old = B.BAND_TICKS
    try:
        B.BAND_TICKS = 7
        wide = B.replay_messages([msgs], "2026-08-11", ["09:30"], {7: ("ES", "ESU6")},
                                 tick)["rows"][0]
    finally:
        B.BAND_TICKS = old
    assert (wide[8], wide[9], wide[10], wide[11]) == (15, 15, 3, 3)


def test_a_minute_with_no_message_repeats_the_book_and_reports_zero_events():
    msgs = B.synthetic_messages("2026-08-11", "09:29")
    out = B.replay_messages([msgs], "2026-08-11", ["09:30", "09:31", "09:32"],
                            {7: ("ES", "ESU6")}, {7: int(round(0.25 / B.PX))})
    rows = out["rows"]
    assert len(rows) == 3
    assert [r[2] for r in rows] == ["09:30", "09:31", "09:32"]
    # everything but the minute label and the liveness counter repeats
    assert rows[0][3:12] == rows[1][3:12] == rows[2][3:12]
    assert [r[12] for r in rows] == [11, 0, 0]


def test_the_minute_grid_is_the_ET_session_and_the_settlement_extension_is_computed():
    minutes, note = B.minute_grid("2026-08-11")
    assert minutes[0] == "09:30" and minutes[-1] == "16:00" and len(minutes) == 391
    assert note["settlement_window_end_et"] == {"ES": "16:00", "NQ": "16:00", "CL": "14:30"}
    # ZN, ZB, RTY and YM have no row in the D586 table at all; GC has one whose effective_from is
    # after this pull. Two different absences, and the builder reports which.
    assert note["no_effective_window"] == {"RTY": "no_row", "YM": "no_row", "GC": "not_effective",
                                           "ZN": "no_row", "ZB": "no_row"}


def test_the_boundaries_are_UTC_nanoseconds_of_the_ET_minutes():
    import pandas as pd

    minutes, _ = B.minute_grid("2026-08-11")
    ns = B.boundaries_ns("2026-08-11", minutes)
    assert len(ns) == 391
    assert ns[0] == pd.Timestamp("2026-08-11 13:30", tz="UTC").value      # EDT is UTC-4
    assert ns[-1] == pd.Timestamp("2026-08-11 20:00", tz="UTC").value
    # and in January the same ET labels land an hour later in UTC, because the grid is tz-aware
    assert B.boundaries_ns("2026-01-05", minutes)[0] == pd.Timestamp(
        "2026-01-05 14:30", tz="UTC"
    ).value


def test_a_non_contiguous_minute_list_raises_rather_than_being_silently_accepted():
    with pytest.raises(B.DepthError, match="not one minute apart"):
        B.boundaries_ns("2026-08-11", ["09:30", "16:00"])


def test_sunday_files_carry_no_day_session_and_are_not_replayed():
    days = {d for d, _ in B.session_days()}
    import pandas as pd

    assert all(pd.Timestamp(d).dayofweek < 5 for d in days)
    assert "2026-08-16" not in days and "2026-09-06" not in days


def test_every_gate_raises_on_a_break_that_hits_the_value_it_reads():
    """The builder's own `--selftest`, run here so a red gate is a red test rather than a script
    nobody remembered to invoke."""
    B.selftest()


# ------------------------------------------------------------------ the panel itself


def test_the_panel_has_one_row_per_root_minute_day_and_passes_its_own_gates(requires_panel):
    d = _panel(requires_panel)
    minutes, _ = B.minute_grid(str(d["day"].iloc[0]))
    report = B.gates(d, minutes)
    assert report["minutes_per_day"] == 391
    assert report["days"] == 21           # 22 session files, less Labor Day -- see below
    assert report["rows"] == 391 * 21 * len(B.ROOTS) == 65_688


def test_labor_day_is_excluded_by_the_liveness_rule_and_its_numbers_are_recorded(requires_panel):
    """2026-09-07 is the one US holiday in the pull. Every root's front contract goes silent for
    part of the 09:30-16:00 grid, so the day is not a day session and is dropped WHOLE. The rule
    is liveness; that the same day also holds every crossed and locked minute in the whole replay
    is recorded as a coincidence, not used as the definition."""
    d = _panel(requires_panel)
    assert "2026-09-07" not in set(d["day"])
    meta = json.loads(META.read_text(encoding="utf-8"))
    excluded = meta["excluded_days"]
    assert list(excluded) == ["2026-09-07"]
    assert excluded["2026-09-07"]["minutes_with_no_message"] == 917
    assert excluded["2026-09-07"]["crossed_or_locked_minutes"] == 538
    assert excluded["2026-09-07"]["roots_affected"] == sorted(B.ROOTS)


def test_the_band_empty_minutes_are_enumerated_rather_than_deleted(requires_panel):
    """Seven minutes across 21 days have a spread wider than the band itself, so NOTHING rests
    within +/-5 ticks and the depth is exactly zero. That is the correct answer to the question
    the column asks, so the rows stay and are listed -- five of the seven are at 10:00 ET."""
    d = _panel(requires_panel)
    meta = json.loads(META.read_text(encoding="utf-8"))
    listed = meta["gates"]["band_empty_minutes"]
    assert len(listed) == 7
    assert sum(1 for r in listed if r["minute_et"] == "10:00") == 5
    wide = d[d["spread_ticks"] > 10]
    assert len(wide) == 7
    assert (wide["bid_depth_5tk"] == 0).all() and (wide["ask_depth_5tk"] == 0).all()


def test_the_meta_digest_matches_the_panel_on_disk(requires_panel):
    import hashlib

    _panel(requires_panel)
    meta = json.loads(META.read_text(encoding="utf-8"))
    assert hashlib.sha256(PANEL.read_bytes()).hexdigest() == meta["sha256"]
    assert meta["record"] == "D604"
    assert meta["band_ticks"] == 5
    assert "vault" in meta["holdout"]


def test_the_panel_is_written_with_LF_endings(requires_panel):
    """D550: the author's OS is not the runner's. A CRLF in a gzipped csv changes every byte of
    the digest above."""
    _panel(requires_panel)
    with gzip.open(PANEL, "rb") as fh:
        head = fh.read(4096)
    assert b"\r\n" not in head


def test_the_panel_holds_no_bar_from_outside_the_MBO_pull(requires_panel):
    d = _panel(requires_panel)
    assert d["day"].min() == "2026-08-11"
    assert d["day"].max() == "2026-09-09"


# ------------------------- ledger required unit test 45, against the fixture


def _series(d, root: str, minute: str):
    """(day, two-sided depth) at ONE root and ONE minute -- 8A.4's 'same-time' series."""
    rows = d[(d["root"] == root) & (d["minute_et"] == minute)].sort_values("day")
    return [(str(r.day), float(r.bid_depth_5tk + r.ask_depth_5tk)) for r in rows.itertuples()]


def test_ledger_45_depth_is_measured_at_the_t0_bar_close_within_five_ticks(requires_panel):
    """The measurement half of 45: every minute close of the day session carries a +/-5-tick
    depth on both sides, and it is at least the best quote's own size -- on every minute whose
    best quotes are inside the band. The seven that are not are the band-empty minutes above, and
    their zero is the true answer, not a gap."""
    d = _panel(requires_panel)
    meta = json.loads(META.read_text(encoding="utf-8"))
    assert meta["band_ticks"] == 5
    assert "after every message with ts_recv strictly before it" in meta["shape"]
    inside = d[d["spread_ticks"] <= 10]
    assert len(inside) == len(d) - 7
    assert (inside["bid_depth_5tk"] >= inside["best_bid_lots"]).all()
    assert (inside["ask_depth_5tk"] >= inside["best_ask_lots"]).all()
    assert (inside["bid_depth_5tk"] > 0).all() and (inside["ask_depth_5tk"] > 0).all()


def test_a_five_tick_band_is_a_different_economic_width_on_every_root(requires_panel):
    """Why ZN's 74,717 median lots and NQ's 42 are not comparable numbers: the band is 7.20 bp
    wide on ZN and 0.42 bp on NQ, a factor of 17. The gate says ES is the deepest EQUITY-INDEX
    root, not the deepest of the eight, for exactly this reason."""
    _panel(requires_panel)
    bp = json.loads(META.read_text(encoding="utf-8"))["gates"]["band_half_width_bp_by_root"]
    assert max(bp.values()) / min(bp.values()) > 10.0
    assert bp["ZB"] > bp["ZN"] > bp["ES"] > bp["NQ"]
    usd = json.loads(META.read_text(encoding="utf-8"))["gates"]["median_two_sided_usd_by_root"]
    assert max(usd, key=usd.get) == "ZN"
    assert usd["ES"] > max(usd["NQ"], usd["RTY"], usd["YM"])


def test_ledger_45_depth_bar_over_the_fixture_uses_prior_days_only(requires_panel):
    d = _panel(requires_panel)
    series = _series(d, "ES", "15:59")
    assert len(series) == 21
    evaluation_day = series[10][0]
    prior = [row for row in series if row[0] < evaluation_day]
    assert len(prior) == 10
    value = depth_bar(prior, evaluation_day, lookback_days=10)
    assert value > 0.0
    # and it is the median of exactly those ten days, computed here without the helper
    ten = sorted(v for _, v in prior)
    assert value == 0.5 * (ten[4] + ten[5])


def test_ledger_45_a_same_day_row_from_the_fixture_raises(requires_panel):
    d = _panel(requires_panel)
    series = _series(d, "ES", "15:59")
    evaluation_day = series[10][0]
    leaky = [row for row in series if row[0] <= evaluation_day]
    with pytest.raises(FuturesImpactError, match="at or after the evaluation day"):
        depth_bar(leaky, evaluation_day, lookback_days=11)


def test_the_median_and_the_mean_of_a_real_depth_window_are_not_the_same_number(requires_panel):
    """8A.4 says median, D604's brief said mean. On a right-skewed depth series they differ, which
    is why the module offers both and defaults to the document's."""
    d = _panel(requires_panel)
    series = _series(d, "ES", "15:59")
    prior = series[:20]
    day = series[20][0]
    assert depth_bar(prior, day, 20, stat="median") != depth_bar(prior, day, 20, stat="mean")
