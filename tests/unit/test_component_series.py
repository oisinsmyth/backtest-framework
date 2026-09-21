"""`validation/component_series.py` — D590.

WHY THIS MODULE HAS TO BE CHECKED AGAINST A SCRIPT. `docs/COMPONENTS_PROP.md` is scored
by `scripts/run_d466_components.py`. If this module's estimators differ from that one's
by so much as a divisor, the ledger acquires two conventions and every ρ computed here
is incomparable with every Sharpe computed there — which is the failure CLAUDE.md names
("a component number computed outside the runner"). So `sharpe`, `sharpe_boot`,
`series_on`/`align`, the correlation matrix and the C-a/C-c/C-d flags are all held
against the script itself, imported by path and never edited.

No market fixture is read: every series here is synthetic or declared.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backtest_framework.validation import component_series as CS

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts"


@pytest.fixture(scope="module")
def d466():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "run_d466_components", SCRIPTS / "run_d466_components.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_d466_components"] = mod
    spec.loader.exec_module(mod)
    return mod


def _series(name="K9", n=40, seed=0, spec="D590"):
    rng = np.random.default_rng(seed)
    dates = tuple(str(d.date()) for d in pd.bdate_range("2016-01-04", periods=n))
    vals = tuple(float(round(v, 6)) for v in rng.normal(4.0, 120.0, n))
    return CS.DailyPnL(name=name, dates=dates, usd=vals, size_label="1 MNQ",
                       cost_line_usd_rt=3.0, window=(dates[0], dates[-1]), spec=spec,
                       source_sha256="a" * 64)


# ============================================================ the artefact


def test_write_then_read_returns_an_equal_object(tmp_path):
    s = _series()
    p = s.write(tmp_path)
    assert p.name == "K9_daily_usd.csv"
    assert (tmp_path / "K9_daily_usd.meta.json").exists()
    back = CS.read(p)
    assert back == s
    assert back.usd == s.usd          # exact floats, not approximately equal
    assert CS.read(s.meta_path(tmp_path)) == s


def test_the_values_round_trip_bit_exactly_on_awkward_floats(tmp_path):
    awkward = (0.1 + 0.2, -1e-17, 1234567.8901234567, -0.0, 1e300)
    dates = tuple(f"2016-01-{i + 4:02d}" for i in range(len(awkward)))
    s = CS.DailyPnL(name="awk", dates=dates, usd=awkward, size_label="1 MES",
                    cost_line_usd_rt=3.0, window=(dates[0], dates[-1]), spec="D590",
                    source_sha256="b" * 64)
    back = CS.read(s.write(tmp_path))
    assert back.usd == awkward
    assert math.copysign(1.0, back.usd[3]) == -1.0


def test_the_newline_is_pinned_to_lf_on_every_platform(tmp_path):
    """D550: the author's OS is not the runner's; a sha256 over CRLF is a different hash."""
    p = _series().write(tmp_path)
    assert b"\r\n" not in p.read_bytes()
    assert b"\r\n" not in _series().meta_path(tmp_path).read_bytes()


def test_a_csv_edited_after_it_was_written_is_refused(tmp_path):
    s = _series()
    p = s.write(tmp_path)
    text = p.read_text(encoding="utf-8")
    first_value = text.splitlines()[1].split(",")[1]
    p.write_text(text.replace(first_value, "999.0", 1), encoding="utf-8", newline="\n")
    with pytest.raises(ValueError, match="changed after it was written"):
        CS.read(p)


def test_a_csv_without_its_sidecar_cannot_satisfy_c_e(tmp_path):
    s = _series()
    p = s.write(tmp_path)
    s.meta_path(tmp_path).unlink()
    with pytest.raises(FileNotFoundError, match="C-e"):
        CS.read(p)


def test_the_meta_records_everything_c_e_asks_for(tmp_path):
    s = _series()
    s.write(tmp_path)
    meta = json.loads(s.meta_path(tmp_path).read_text(encoding="utf-8"))
    assert meta["size_label"] == "1 MNQ"
    assert meta["cost_line_usd_rt"] == 3.0
    assert meta["window"] == list(s.window)
    assert meta["spec"] == "D590"
    assert meta["source_sha256"] == "a" * 64
    assert len(meta["csv_sha256"]) == 64


@pytest.mark.parametrize("kwargs,match", [
    (dict(dates=("2016-01-04", "2016-01-04")), "strictly increasing"),
    (dict(dates=("2016-01-05", "2016-01-04")), "strictly increasing"),
    (dict(dates=("2016-01-04",), usd=(1.0,)), "at least 2 sessions"),
    (dict(usd=(1.0, float("nan"))), "not finite"),
    (dict(usd=(1.0,)), "dates against"),
    (dict(cost_line_usd_rt=-1.0), "must be >= 0"),
    (dict(window=("2016-01-06", "2016-01-04")), "not \\(first, last\\)"),
    (dict(window=("2016-01-05", "2016-01-05")), "outside"),
    (dict(spec=""), "spec is empty"),
    (dict(source_sha256="XYZ"), "64 lowercase hex"),
    (dict(name="a/b"), "not file-safe"),
])
def test_a_malformed_series_raises_at_construction(kwargs, match):
    base = dict(name="K9", dates=("2016-01-04", "2016-01-05"), usd=(1.0, 2.0),
                size_label="1 MNQ", cost_line_usd_rt=3.0,
                window=("2016-01-04", "2016-01-05"), spec="D590",
                source_sha256="c" * 64)
    base.update(kwargs)
    with pytest.raises(ValueError, match=match):
        CS.DailyPnL(**base)


def test_sha256_of_hashes_the_bytes(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("abc", encoding="utf-8", newline="\n")
    # sha256("abc"), a value from outside this codebase
    assert CS.sha256_of(f) == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


# ============================================================ the estimators


def test_sharpe_and_sharpe_boot_are_the_scripts(d466):
    rng = np.random.default_rng(7)
    dates = [str(d.date()) for d in pd.bdate_range("2016-01-04", "2018-12-31")]
    x = rng.normal(3.0, 90.0, len(dates))
    assert CS.sharpe(x) == d466.sharpe(x)
    assert CS.sharpe_boot(x, dates) == d466.sharpe_boot(x, dates)
    assert CS.LEDGER_BARS.sharpe == d466.BAR_SHARPE
    assert CS.LEDGER_BARS.rho == d466.BAR_RHO
    assert CS.LEDGER_BARS.skew == d466.BAR_SKEW
    assert CS.LEDGER_BARS.sigma == d466.BAR_SIGMA == 500.0
    assert CS.ACCOUNT_DEFAULT == d466.ACCOUNT


def test_sharpe_boot_can_fail_a_different_seed_gives_a_different_se(d466):
    rng = np.random.default_rng(8)
    dates = [str(d.date()) for d in pd.bdate_range("2016-01-04", "2017-12-29")]
    x = rng.normal(3.0, 90.0, len(dates))
    assert CS.sharpe_boot(x, dates, seed=7) != CS.sharpe_boot(x, dates, seed=8)
    with pytest.raises(ValueError, match="dates against"):
        CS.sharpe_boot(x, dates[:-1])


def test_sortino_on_a_hand_case():
    """x = [8, -2, -2, -2]: mean 1/2, sd 5, downside sqrt(12/3) = 2 (R17)."""
    x = np.array([8.0, -2.0, -2.0, -2.0])
    assert float(x.std(ddof=1)) == 5.0
    assert CS.sharpe(x) == pytest.approx(0.1 * math.sqrt(252), abs=1e-12)
    assert CS.sortino(x) == pytest.approx(0.25 * math.sqrt(252), abs=1e-12)
    # the two share a ddof=1 divisor, so they differ only in WHICH deviations count
    assert CS.sortino(x) > CS.sharpe(x)


def test_sortino_is_nan_when_nothing_ever_loses_and_raises_on_a_single_session():
    assert math.isnan(CS.sortino(np.array([1.0, 2.0, 3.0])))
    with pytest.raises(ValueError, match="at least 2 sessions"):
        CS.sortino(np.array([1.0]))


# ============================================================ alignment


def test_align_is_series_on_column_by_column(d466):
    a, b = _series("A", n=30, seed=1), _series("B", n=30, seed=2)
    cal = pd.Index(sorted(set(a.dates) | set(b.dates)))
    frame = CS.align(a, b, calendar=cal)
    for s in (a, b):
        want = d466.series_on(cal, list(s.dates), list(s.usd))
        assert np.array_equal(frame[s.name].to_numpy(), want.to_numpy())


def test_align_zero_fills_a_component_that_did_not_trade_that_day():
    a = CS.DailyPnL(name="A", dates=("2016-01-04", "2016-01-06"), usd=(10.0, -5.0),
                    size_label="1 MES", cost_line_usd_rt=3.0,
                    window=("2016-01-04", "2016-01-06"), spec="D590",
                    source_sha256="d" * 64)
    b = CS.DailyPnL(name="B", dates=("2016-01-05", "2016-01-06"), usd=(3.0, 7.0),
                    size_label="1 MNQ", cost_line_usd_rt=3.0,
                    window=("2016-01-05", "2016-01-06"), spec="D590",
                    source_sha256="e" * 64)
    f = CS.align(a, b)
    assert list(f.index) == ["2016-01-04", "2016-01-05", "2016-01-06"]
    assert list(f["A"]) == [10.0, 0.0, -5.0]
    assert list(f["B"]) == [0.0, 3.0, 7.0]
    assert list(f.sum(axis=1)) == [10.0, 3.0, 2.0]


def test_align_refuses_to_drop_a_session_silently(d466):
    """`series_on` drops out-of-calendar rows; dropped P&L appears nowhere (D48)."""
    a = _series("A", n=10, seed=3)
    short = pd.Index(list(a.dates[:-2]))
    with pytest.raises(ValueError, match="outside the calendar"):
        CS.align(a, calendar=short)
    lenient = CS.align(a, calendar=short, strict=False)
    assert len(lenient) == 8
    assert np.array_equal(lenient["A"].to_numpy(),
                          d466.series_on(short, list(a.dates), list(a.usd)).to_numpy())


@pytest.mark.parametrize("bad,match", [
    ("dupe_name", "duplicate component names"),
    ("dupe_cal", "duplicate dates"),
    ("unsorted_cal", "not sorted"),
])
def test_align_guards_raise(bad, match):
    a = _series("A", n=8, seed=4)
    if bad == "dupe_name":
        with pytest.raises(ValueError, match=match):
            CS.align(a, _series("A", n=8, seed=5))
    elif bad == "dupe_cal":
        with pytest.raises(ValueError, match=match):
            CS.align(a, calendar=list(a.dates) + [a.dates[0]])
    else:
        with pytest.raises(ValueError, match=match):
            CS.align(a, calendar=list(reversed(a.dates)))


def test_correlation_matrix_is_the_scripts_corr():
    a, b = _series("A", n=60, seed=6), _series("B", n=60, seed=7)
    f = CS.align(a, b)
    assert np.allclose(CS.correlation_matrix(f).to_numpy(), f.corr().to_numpy(),
                       atol=0.0, rtol=0.0, equal_nan=True)
    assert CS.correlation_matrix(f).loc["A", "A"] == pytest.approx(1.0)


def test_c_b_needs_two_series_and_component_line_says_so():
    line = CS.component_line(_series(n=30, seed=9))
    assert "not computable from one series" in line["C_b_note"]


# ============================================================ the component line


def test_component_line_matches_the_scripts_score_field_for_field(d466):
    rng = np.random.default_rng(11)
    n = 300
    dates = tuple(str(d.date()) for d in pd.bdate_range("2016-01-04", periods=n))
    vals = rng.normal(5.0, 150.0, n)
    vals[rng.random(n) < 0.25] = 0.0
    s = CS.DailyPnL(name="K9", dates=dates, usd=tuple(float(v) for v in vals),
                    size_label="1 MNQ", cost_line_usd_rt=3.0,
                    window=(dates[0], dates[-1]), spec="D590", source_sha256="f" * 64)
    ser = pd.Series(s.values, index=pd.Index(dates))
    theirs = d466.score({"K9": ser}, {"K9": ser != 0.0}, pd.Index(dates))["K9"]
    mine = CS.component_line(s)
    assert mine["n_sessions"] == theirs["days"]
    assert mine["active_days"] == theirs["active_days"]
    assert mine["net_sharpe"] == theirs["sharpe"]
    assert mine["net_sharpe_se"] == theirs["sharpe_se"]
    assert mine["mean_usd"] == theirs["mean_usd"]
    assert mine["sd_usd"] == theirs["sd_usd"]
    assert mine["hit_active"] == theirs["hit_active"]
    assert mine["skew"] == theirs["skew"]
    assert mine["ann_usd"] == theirs["ann_usd"]
    assert mine["worst_day_usd"] == theirs["worst_day_usd"]
    assert mine["sigma_pct_account"] == theirs["sigma_pct_account"]


def test_component_line_flags_are_the_ledgers_three_bars():
    n = 260
    dates = tuple(str(d.date()) for d in pd.bdate_range("2016-01-04", periods=n))
    rng = np.random.default_rng(12)
    base = rng.normal(0.0, 100.0, n)

    def line(vals):
        s = CS.DailyPnL(name="X", dates=dates, usd=tuple(float(v) for v in vals),
                        size_label="1 MES", cost_line_usd_rt=3.0,
                        window=(dates[0], dates[-1]), spec="D590",
                        source_sha256="1" * 64)
        return CS.component_line(s)

    strong = line(base - base.mean() + 100.0 * 0.8 / math.sqrt(252) * 3.0 + 6.0)
    assert strong["net_sharpe"] > 0.5 and strong["C_a_pass"] is True
    weak = line(base - base.mean() + 1.0)
    assert weak["net_sharpe"] < 0.5 and weak["C_a_pass"] is False

    big = base * 8.0                       # sd ~ 800 > the $500 bar
    assert line(big)["C_d_pass"] is False
    assert line(base)["C_d_pass"] is True

    skewed = base.copy()
    skewed[5] = -3_000.0                   # a long left tail
    assert line(skewed)["skew"] < -0.5
    assert line(skewed)["C_c_pass"] is False


def test_component_line_reports_gross_beside_net_and_names_its_convention():
    s = _series(n=50, seed=13)
    line = CS.component_line(s)
    assert line["gross_sharpe_one_rt_per_active_day"] > line["net_sharpe"]
    assert line["cost_usd_total_one_rt_per_active_day"] == 3.0 * line["active_days"]
    assert "one_rt_per_active_day" in " ".join(line)


def test_component_line_carries_a_sortino_beside_every_sharpe():
    """R17, the principal's mandate of 2026-09-19."""
    line = CS.component_line(_series(n=60, seed=14))
    assert math.isfinite(line["net_sortino"])
    assert math.isfinite(line["gross_sortino_one_rt_per_active_day"])
    # R17 binds on a REPORTED Sharpe. `bar_sharpe` is the ledger's threshold (C-a), not
    # a measurement of this series, and C-a has no Sortino counterpart in the standard.
    measured = [k for k in line
                if "sharpe" in k and not k.startswith("bar_") and not k.endswith("_se")]
    assert measured, line.keys()
    for k in measured:
        assert k.replace("sharpe", "sortino") in line, k


def test_component_line_discharges_c_e_and_refuses_a_non_positive_account():
    line = CS.component_line(_series(n=20, seed=15, spec="D498"))
    assert line["C_e_provenance"].startswith("D498; 2016-01-04..")
    assert "1 MNQ" in line["C_e_provenance"] and "$3.00 RT" in line["C_e_provenance"]
    with pytest.raises(ValueError, match="positive dollar amount"):
        CS.component_line(_series(n=20, seed=16), account=0.0)


def test_default_dir_is_the_convention_this_module_establishes():
    assert CS.default_dir() == REPO / "data" / "components"


def test_an_ndarray_backed_series_round_trips_too(tmp_path):
    """Found on integration, 2026-09-21: `write` used `repr(v)` on each value, and under
    numpy >= 2 `repr(np.float64(1.0))` is "np.float64(1.0)", which `read` cannot parse.
    Every test above passes tuples of Python floats; every runner will pass an ndarray."""
    base = _series(n=12, seed=99)
    arr = np.asarray(base.usd, dtype=float)
    assert isinstance(arr[0], np.floating)
    s = CS.DailyPnL(name="nd", dates=base.dates, usd=arr, size_label="1 MES",
                    cost_line_usd_rt=3.0, window=base.window, spec="D590",
                    source_sha256=base.source_sha256)
    back = CS.read(s.write(tmp_path))
    assert np.asarray(back.usd).tobytes() == arr.tobytes()
    assert "np.float64" not in s.csv_path(tmp_path).read_text(encoding="utf-8")
