"""Gates on the CME session calendar fixture (D584).

Offline and deterministic: every test reads the committed artifacts or a hand-built frame, and none
touches the network or the 400 MB minute panel.

WHAT THESE TESTS ARE DEFENDING

Every failure mode of a session calendar is silent. A DST-blind clock shifts the whole summer by an
hour and every bar still parses. A 09:00-15:59 template applied to gold reads 150 minutes of
post-settlement Globex as the close of the session, which is how D530 got a z = -12.6 "closing
reversion" out of the bid-ask bounce. A feed dropout that truncates 22 roots looks exactly like a
market-wide early close on counts alone, and calling it one would delete real sessions from every
study that excludes early closes. A front month re-elected here rather than joined would let this
fixture and `fut_breadth_hourly` disagree about what was held. So the tests pin those, and they pin
them on the scalar the builder compares, not on a message.
"""

from __future__ import annotations

import csv
import gzip
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "data" / "fixtures" / "cme_session_calendar.csv.gz"
META = REPO / "data" / "fixtures" / "cme_session_calendar.meta.json"
ROLLS = REPO / "data" / "fixtures" / "fut_sessions_rolls.csv.gz"

COLUMNS = ["root", "day", "is_trading", "session_open_et", "session_close_et", "rth_bars",
           "is_early_close", "front_contract", "roll_day", "expiry_day", "days_to_expiry",
           "quad_witching", "month_end", "quarter_end", "fomc", "cpi", "empsit", "dst_transition_week"]


def _load_builder():
    path = REPO / "scripts" / "build_cme_session_calendar.py"
    spec = importlib.util.spec_from_file_location("build_cme_session_calendar", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_cme_session_calendar"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load_builder()


@pytest.fixture(scope="module")
def rows(requires_panel):
    requires_panel(FIXTURE)
    with gzip.open(FIXTURE, "rt", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def meta(requires_panel):
    requires_panel(META)
    return json.loads(META.read_text())


@pytest.fixture(scope="module")
def es(rows):
    return {r["day"]: r for r in rows if r["root"] == "ES"}


# --------------------------------------------------------------------------- the clock
def test_january_and_july_both_open_at_0930_et():
    """14:30 UTC in January and 13:30 UTC in July are the SAME wall clock in ET.

    A fixed -5 offset passes the January case and fails the July one by an hour, which is exactly
    the error that would silently move every summer session in this fixture.
    """
    import pandas as pd

    jan = pd.Timestamp("2019-01-15 14:30", tz="UTC").tz_convert("US/Eastern")
    jul = pd.Timestamp("2019-07-15 13:30", tz="UTC").tz_convert("US/Eastern")
    assert (jan.strftime("%H:%M"), jan.tzname()) == ("09:30", "EST")
    assert (jul.strftime("%H:%M"), jul.tzname()) == ("09:30", "EDT")
    assert pd.Timestamp("2019-07-15 13:30", tz="UTC").tz_convert("Etc/GMT+5").strftime("%H:%M") == "08:30"


def test_bar_index_maps_to_the_declared_window(mod):
    assert (mod.hhmm(0), mod.hhmm(mod.N_BARS - 1)) == ("09:00", "15:59")
    assert mod.N_BARS == 420


def test_dst_weeks_run_forward_from_the_transition(mod):
    import pandas as pd

    w = mod.dst_transition_weeks(pd.DatetimeIndex(pd.date_range("2019-01-01", "2019-12-31")))
    assert len(w) == 14
    assert {"2019-03-10", "2019-03-16", "2019-11-03", "2019-11-09"} <= w
    assert "2019-03-04" not in w and "2019-03-17" not in w and "2019-11-10" not in w
    assert mod.dst_transition_weeks(pd.DatetimeIndex(pd.date_range("2019-04-01", "2019-09-30"))) == set()


# --------------------------------------------------------------------------- the derived rules
def test_holiday_observance_is_asymmetric(mod):
    """Christmas on a Saturday moves back to the Friday; New Year's Day on a Saturday does not.

    2021-12-24 is a closure in the archive and 2021-12-31 trades a full session. A symmetric rule
    gets one of the two wrong whichever way it is written.
    """
    h = mod.full_closure_days([2021, 2022])
    assert h["2021-12-24"] == "Christmas Day"
    assert "2021-12-31" not in h
    assert h["2021-04-02"] == "Good Friday" and h["2022-04-15"] == "Good Friday"
    assert h["2022-12-26"] == "Christmas Day"


def test_easter_matches_known_dates(mod):
    for y, d in ((2019, "2019-04-21"), (2021, "2021-04-04"), (2024, "2024-03-31"), (2026, "2026-04-05")):
        assert mod.easter(y).strftime("%Y-%m-%d") == d


def test_the_close_comes_from_the_cliff_not_the_window(mod):
    """A settlement spike is found; a flat profile falls back to the window edge and says so."""
    import numpy as np

    v = np.full(mod.N_BARS, 100.0)
    v[329] = 2000.0
    v[330:] = 20.0
    bar, ratio = mod.band_close_from_profile(v)
    assert (mod.hhmm(bar), ratio > mod.CLIFF_RATIO) == ("14:29", True)

    bar2, ratio2 = mod.band_close_from_profile(np.full(mod.N_BARS, 100.0))
    assert bar2 == mod.N_BARS - 1 and ratio2 is None

    with pytest.raises(AssertionError):
        mod.band_close_from_profile(np.zeros(mod.N_BARS - 1))


def test_a_feed_dropout_is_not_an_early_close(mod):
    """The 2020-06-30 shape: 22 of 36 roots stop together, but not on a five-minute boundary.

    Counts and concentration cannot tell it from a holiday; the boundary can, because an exchange
    session ends on one and a dropout does not.
    """
    import pandas as pd

    def frame(stop):
        return pd.DataFrame({"root": [f"R{i}" for i in range(12)], "day": "2020-06-30",
                             "last": [stop] * 6 + [419] * 6, "band_close": [419] * 12})

    acc, _ = mod.market_wide_early_closes(frame(254))          # 13:14 -> a 13:15 close
    assert "2020-06-30" in acc and acc["2020-06-30"]["modal_close_et"] == "13:14"

    acc2, rej2 = mod.market_wide_early_closes(frame(70))       # 10:10 -> a dropout
    assert acc2 == {}
    assert rej2[0]["modal_stop_et"] == "10:10" and rej2[0]["on_five_minute_boundary"] is False


def test_a_thin_root_is_not_an_early_close(mod):
    import pandas as pd

    thin = pd.DataFrame({"root": [f"R{i}" for i in range(12)], "day": "2019-06-03",
                         "last": [254] * 2 + [419] * 10, "band_close": [419] * 12})
    assert mod.market_wide_early_closes(thin)[0] == {}


def test_required_outputs_guard_refuses_an_incomplete_meta(mod):
    mod.check_required({k: None for k in mod.REQUIRED_OUTPUTS})
    with pytest.raises(AssertionError, match="refusing to write"):
        mod.check_required({k: None for k in mod.REQUIRED_OUTPUTS if k != "gates"})


# --------------------------------------------------------------------------- the gates, on a synthetic calendar
def test_every_gate_passes_a_clean_case_and_raises_on_a_break(mod):
    """A self-test that cannot fail is worse than none, and the break must hit the scalar compared."""
    import pandas as pd

    cal = mod._synth()
    rolls = pd.DataFrame([dict(root="ES", day="2019-12-12", from_contract="ESZ9", to_contract="ESH0",
                               from_volume=1, to_volume=2)])

    assert mod.g4_rolls(cal, rolls)["passes"]
    broken = cal.copy()
    broken.loc[(broken["root"] == "ES") & (broken["day"] == "2019-12-12"), "roll_day"] = False
    assert not mod.g4_rolls(broken, rolls)["passes"]

    assert mod.g3_full_bars(cal)["passes"]
    b3 = cal.copy()
    b3.loc[(b3["root"] == "ES") & (b3["rth_bars"] == 390), "rth_bars"] = 387
    assert not mod.g3_full_bars(b3)["passes"]

    assert mod.g2_early_close(cal)["passes"]
    b2 = cal.copy()
    b2.loc[(b2["root"] == "ES") & (b2["day"] == "2019-11-29"), "is_early_close"] = False
    assert not mod.g2_early_close(b2)["passes"]

    assert mod.g1_holidays(cal)["passes"]
    b1 = cal.copy()
    b1.loc[(b1["root"] == "ES") & (b1["day"] == "2019-12-13"), "is_trading"] = False
    assert not mod.g1_holidays(b1)["passes"]

    assert mod.g6_cme_page({"2019-11-29": {}}, {"2019-11-29": "x"})["passes"]
    assert not mod.g6_cme_page({"2019-11-29": {}, "2019-12-24": {}}, {"2019-11-29": "x"})["passes"]
    assert mod.g6_cme_page({"2019-11-29": {}}, None)["passes"] is None


# --------------------------------------------------------------------------- the committed fixture
def test_shape_and_columns(rows, meta):
    assert list(rows[0]) == COLUMNS
    assert len(rows) == meta["rows"] == 205428
    assert {r["root"] for r in rows} == set(meta["roots"]) and len(meta["roots"]) == 36


def test_one_row_per_root_day_and_the_grid_is_contiguous(rows):
    import pandas as pd

    keys = [(r["root"], r["day"]) for r in rows]
    assert len(set(keys)) == len(keys)
    by_root: dict[str, list[str]] = {}
    for root, day in keys:
        by_root.setdefault(root, []).append(day)
    for root, days in by_root.items():
        want = pd.date_range(min(days), max(days), freq="D").strftime("%Y-%m-%d").tolist()
        assert days == want, f"{root}: the calendar grid skips days"


def test_the_named_early_closes_and_the_full_session(es):
    """The facts a consumer will check first: the two 13:15 closes and the 390-bar session beside them."""
    assert es["2019-11-29"]["is_early_close"] == "True"
    assert es["2019-12-24"]["is_early_close"] == "True"
    assert es["2019-11-29"]["session_close_et"] == es["2019-12-24"]["session_close_et"] == "13:14"
    assert es["2019-11-27"]["is_early_close"] == "False"
    assert es["2019-11-27"]["rth_bars"] == "390"
    assert es["2019-11-27"]["session_close_et"] == "15:59"


def test_thanksgiving_day_itself_is_a_trading_day(es):
    """CME equity index trades 09:00-13:00 ET on Thanksgiving however shut the cash market is.

    Marking it a holiday would be the natural mistake and would delete a real session.
    """
    for day in ("2019-11-28", "2021-11-25", "2023-11-23"):
        assert es[day]["is_trading"] == "True"
        assert es[day]["is_early_close"] == "True"
        assert es[day]["session_close_et"] == "12:59"


def test_full_closures_are_not_trading_days(es):
    for day in ("2019-12-25", "2020-01-01", "2020-04-10", "2021-12-24", "2023-01-02"):
        assert es[day]["is_trading"] == "False"
        assert es[day]["session_close_et"] == ""


def test_roll_day_equals_the_rolls_fixture(rows, requires_panel):
    requires_panel(ROLLS)
    with gzip.open(ROLLS, "rt", newline="") as fh:
        want: dict[str, set] = {}
        for r in csv.DictReader(fh):
            want.setdefault(r["root"], set()).add(r["day"])
    got: dict[str, set] = {}
    for r in rows:
        if r["roll_day"] == "True":
            got.setdefault(r["root"], set()).add(r["day"])
    for root, days in want.items():
        assert got.get(root, set()) == days, f"{root}: roll_day disagrees with fut_sessions_rolls"


def test_the_session_close_is_the_root_s_own_not_the_template(meta, mod):
    """D530: applying 09:00-15:59 to a commodity root reads post-settlement Globex as the session."""
    band = meta["bands"]["per_root"]
    for root, close in (("GC", "13:29"), ("SI", "13:24"), ("HG", "12:59"), ("PL", "13:04"), ("PA", "12:59"),
                        ("CL", "14:29"), ("HO", "14:29"), ("RB", "14:29"), ("NG", "14:29"), ("BZ", "14:29"),
                        ("ZC", "14:19"), ("ZS", "14:19"), ("ZW", "14:19"), ("ZL", "14:19"), ("ZM", "14:19"),
                        ("HE", "13:59"), ("LE", "13:59")):
        assert band[root]["close_et"] == close, f"{root} close"
        assert band[root]["cliff_ratio"] >= mod.CLIFF_RATIO, f"{root} cliff"
    for root in ("ES", "NQ", "YM", "RTY"):
        assert band[root]["close_et"] == "15:59" and band[root]["cliff_ratio"] is None
    for root in ("ZC", "ZS", "ZW", "ZL", "ZM", "HE", "LE"):
        assert band[root]["open_et"] == "09:30"


def test_the_documented_special_sessions(meta, es):
    s = meta["special_sessions"]
    for day, v in s["march_2020_circuit_breakers"].items():
        assert v["is_trading"] and not v["is_early_close"] and v["rth_bars"] < 390
        assert es[day]["is_early_close"] == "False"
    assert s["2021-05-31_memorial_day"]["is_early_close"] and es["2021-05-31"]["session_close_et"] == "12:59"
    assert {x["day"] for x in s["archive_truncations_rejected"]} == {"2020-06-30", "2020-02-27"}
    assert all(not x["on_five_minute_boundary"] for x in s["archive_truncations_rejected"])
    assert es["2020-06-30"]["is_early_close"] == "False"
    assert s["btc_weekend_sessions"]["first"] >= "2026-05-01"
    assert s["btc_weekend_sessions"]["other_roots_with_weekend_sessions"] == 0


def test_quad_witching_comes_from_the_expiry_file_not_the_third_friday_rule(rows, meta):
    """2026-06-18 is a THURSDAY quad witching, because the third Friday of June 2026 is Juneteenth."""
    import pandas as pd

    qw = set(meta["quad_witching_days"])
    assert "2026-06-18" in qw and "2026-06-19" not in qw
    assert pd.Timestamp("2026-06-18").dayofweek == 3
    assert all(d[5:7] in ("03", "06", "09", "12") for d in qw)
    flagged = {r["day"] for r in rows if r["quad_witching"] == "True"}
    assert flagged <= qw


def test_release_flags_are_null_outside_the_sourced_span_not_false(rows, meta):
    """A False in 2012 would say 'no CPI that day'. The source starts in 2016, so it says nothing.

    The committed build joins the D585 events file (`data/calendar/events.csv`); the meta records
    which source it was and the span each flag covers, and the flags are non-null exactly inside
    that span. The span itself is data and is not pinned here beyond its 2016 start.
    """
    src = meta["sources"]["events"]
    cov = src["covers"]
    for r in rows:
        for f in ("fomc", "cpi", "empsit"):
            lo, hi = cov[f]
            inside = lo <= r["day"] <= hi
            assert (r[f] != "") == inside, f"{r['root']} {r['day']} {f}"
    assert src["kind"] == "events csv" and src["path"].replace("\\", "/").endswith("data/calendar/events.csv")
    assert all(cov[f][0] >= "2016-01-01" for f in ("fomc", "cpi", "empsit"))


def test_a_flagged_day_is_a_trading_day_where_that_is_required(rows):
    for r in rows:
        if r["is_early_close"] == "True" or r["month_end"] == "True" or r["quarter_end"] == "True":
            assert r["is_trading"] == "True", f"{r['root']} {r['day']}"
        if r["is_trading"] == "False":
            assert r["session_open_et"] == "" and r["rth_bars"] == ""


def test_expiry_day_is_the_root_calendar_and_days_to_expiry_is_the_front(rows, meta):
    """They are different objects on purpose, and the meta says so rather than letting a reader assume."""
    assert "NOT days_to_expiry == 0" in meta["flag_notes"]["expiry_day / days_to_expiry"]
    zero = [r for r in rows if r["days_to_expiry"] == "0"]
    assert not zero, "the front is elected by volume and rolls early; it should never reach expiry"
    assert min(meta["days_to_expiry_min_per_root"].values()) >= 1


def test_the_meta_records_every_gate_and_does_not_claim_an_unsourced_pass(meta):
    assert set(meta["gates"]) == {"G1", "G2", "G3", "G4", "G5", "G6"}
    ran = [k for k, v in meta["gates"].items() if v["passes"] is not None]
    assert meta["all_gates_pass"] is True and ran == ["G1", "G2", "G3", "G4", "G5"]
    g6 = meta["gates"]["G6"]
    assert g6["passes"] is None and g6["status"] == "not_fetched" and meta["gates_not_run"] == ["G6"]
    assert len(g6["attempts"]) >= 4
    for a in g6["attempts"]:
        assert a["source_url"].startswith("https://") and a["accessed_utc"].endswith("Z") and a["result"]
    assert meta["holiday_disagreements"] == "not_fetched -- G6 did not run"


def test_every_required_output_is_present(mod, meta):
    mod.check_required(meta)
