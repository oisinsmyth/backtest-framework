"""`validation/hurdle_p.py` against every published number it inherits — D590.

R16: a quantity quoted from an earlier record is not a constant, it is the output of a
pipeline that has since moved, and the only way to know the object is the one that was
published is to reproduce it EXACTLY on the original build. Four reproduction guards,
each named in the D590 record:

  (a) `max_drawdown_life` / `p3` vs `scripts/d501_worst_day_frequency.py` on D501's OWN
      input path — NQ AGREE M=5 rebuilt through `d495.build_panel` + `d491.simulate`,
      1,873 sessions 2016-01-07..2023-12-29. IN-SAMPLE ONLY: `d484.series_for` raises on
      any row past 2023, which is the holdout guard, and it is left where it is.
  (b) `p4_life` vs `data/d440_lifecycle.json`'s published MFFU Rapid EOD 50K / SPY /
      voltgt cell, and `simulate_provider` vs `d386_full_lifecycle.simulate`
      bit-identically (D440's own [P1] gate, 12 cells x 5 fields).
  (c) `hurdle_p` vs `scripts/d503_forward_book.py:hurdle_p`, function against function
      on random series — D503's daily series is not committed and its inputs are the
      2024+ forward slice, which nothing here reads — plus every key of D503's STORED
      dicts that its stored summaries determine.
  (d) `p5_recognised` vs `scripts/d495_agree_confluence.py`; the quantified form is in
      `tests/property/test_hurdle_p_property.py`.

Reference runners are imported with `importlib.util.spec_from_file_location` and are
never edited.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from dataclasses import fields
from pathlib import Path

import numpy as np
import pytest

from backtest_framework.validation import hurdle_p as HP

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts"
DATA = REPO / "data"

SLUG = {"Apex": "apex", "MFFU Rapid": "mffu_rapid", "MFFU Rapid EOD": "mffu_rapid_eod",
        "Topstep": "topstep", "Take Profit Trader": "take_profit_trader"}


def _load(name: str, filename: str):
    """The house pattern: import a runner by path, never by editing it."""
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def d386():
    return _load("d386_full_lifecycle", "d386_full_lifecycle.py")


@pytest.fixture(scope="module")
def d440():
    return _load("d440_lifecycle", "d440_lifecycle.py")


@pytest.fixture(scope="module")
def d495():
    return _load("d495_agree_confluence", "d495_agree_confluence.py")


@pytest.fixture(scope="module")
def d503():
    return _load("d503_forward_book", "d503_forward_book.py")


def _key_for(plan) -> str:
    return f"{SLUG[plan.firm]}_{plan.size // 1000}k"


# ============================================================ the venue file


def test_every_d386_plan_loads_from_prop_venues_json_field_by_field(d386):
    """The library's `Plan` duplicates d386's; the duplication is checked, not trusted."""
    assert len(d386.PLANS) == 14
    keys = set()
    for p in d386.PLANS:
        key = _key_for(p)
        assert key not in keys, f"{key} is not unique across PLANS"
        keys.add(key)
        got = HP.load_venue(key)
        for f in fields(p):
            a, b = getattr(p, f.name), getattr(got, f.name)
            assert a == b, f"{key}.{f.name}: d386 {a!r}, prop_venues.json {b!r}"
    assert keys == set(HP.venue_keys())


def test_the_library_plan_has_d386s_fields_in_d386s_order(d386):
    assert [f.name for f in fields(HP.Plan)] == [f.name for f in fields(d386.Plan)]
    assert (HP.EOD, HP.INTRA, HP.STATIC) == (d386.EOD, d386.INTRA, d386.STATIC)


def test_every_plan_field_carries_its_own_provenance():
    for key in HP.venue_keys():
        rec = HP.venue_record(key)
        for name, cell in rec["plan"].items():
            assert set(cell) == {"value", "provenance"}, (key, name)
            assert cell["provenance"], (key, name)


def test_the_four_assumed_fields_name_the_d386_assumption_they_come_from(d386):
    """D386's ASSUMPTIONS list is the only place these four values come from."""
    assert HP.venue_record("take_profit_trader_100k")["plan"]["qual_threshold"][
        "provenance"].startswith("assumed (D386 ASSUMPTIONS #1)")
    assert HP.venue_record("take_profit_trader_150k")["plan"]["qual_threshold"][
        "provenance"].startswith("assumed (D386 ASSUMPTIONS #1)")
    assert HP.venue_record("topstep_50k")["plan"]["safety_net"][
        "provenance"].startswith("assumed (D386 ASSUMPTIONS #2)")
    for k in ("apex_25k", "apex_50k", "apex_100k", "apex_150k"):
        assert HP.venue_record(k)["plan"]["min_total"][
            "provenance"].startswith("assumed (D386 ASSUMPTIONS #3)")
    # the 25K and 50K Take Profit Trader thresholds are PUBLISHED, not assumed
    for k in ("take_profit_trader_25k", "take_profit_trader_50k"):
        assert not HP.venue_record(k)["plan"]["qual_threshold"][
            "provenance"].startswith("assumed")
    assert len(d386.ASSUMPTIONS) == 5


def test_the_flatten_times_are_r11s_and_take_profit_traders_is_unverified():
    got = {k: HP.venue_record(k)["flatten_time_et"]["value"] for k in HP.venue_keys()}
    assert all(got[k] == "16:59" for k in got if k.startswith("apex"))
    assert all(got[k] == "16:10" for k in got if k.startswith("mffu"))
    assert got["topstep_50k"] == "16:10"          # 15:10 CT
    assert all(got[k] is None for k in got if k.startswith("take_profit"))


def test_p6_matches_r11_exactly_two_firms_permit_automation():
    permit = {HP.venue_record(k)["firm"] for k in HP.venue_keys()
              if HP.p6(k)["automation_permitted_funded"]}
    assert permit == {"Topstep", "MFFU Rapid", "MFFU Rapid EOD"}
    assert all(not HP.p6(k)["p6_pass"] for k in HP.venue_keys()
               if HP.venue_record(k)["firm"] in ("Apex", "Take Profit Trader"))


def test_no_venue_carries_a_daily_loss_limit_and_every_one_says_it_is_unverified():
    """R11's 2026-09-13 amendment flagged P3's provenance; nothing has verified it since."""
    for key in HP.venue_keys():
        cell = HP.venue_record(key)["daily_loss_limit"]
        assert cell["value"] is None
        assert cell["provenance"].startswith("unverified, R11 2026-09-13")


def test_an_unknown_venue_raises_rather_than_defaulting():
    with pytest.raises(KeyError, match="unknown venue"):
        HP.load_venue("apex_75k")


# ============================================================ (b) D386 / D440


def test_guard_b1_the_injected_gaussian_reproduces_d386_bit_identically(d386):
    """D440's own [P1] gate, through this module's port. 12 cells x 5 fields, `!=`."""
    plan_386 = [p for p in d386.PLANS
                if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    plan = HP.load_venue("mffu_rapid_eod_50k")
    n = 0
    for sharpe in (0.0, 1.0, 1.5):
        for frac in d386.RISK_FRACS:
            vol = frac * plan.size
            want = d386.simulate(plan_386, sharpe, vol, n_paths=2_000, days=300, k=4,
                                 seed=12345)
            mu = sharpe * vol / math.sqrt(252.0)
            got = HP.simulate_provider(plan, HP.gauss_provider(mu, vol, 4),
                                       n_paths=2_000, days=300, seed=12345)
            for key in ("V", "paid_mean", "p_paid", "p_pass", "n_payouts_mean"):
                assert want[key] == got[key], (sharpe, frac, key, want[key], got[key])
                n += 1
    assert n == 60


def test_guard_b1_can_fail_a_changed_plan_gives_a_different_number(d386):
    """An identity check that cannot fail is worse than none."""
    eod = HP.load_venue("mffu_rapid_eod_50k")
    intra = HP.load_venue("mffu_rapid_50k")
    assert (eod.kind_fund, intra.kind_fund) == (HP.EOD, HP.INTRA)
    a = HP.simulate_provider(eod, HP.gauss_provider(0.0, 200.0, 4),
                             n_paths=1_500, days=300, seed=7)
    b = HP.simulate_provider(intra, HP.gauss_provider(0.0, 200.0, 4),
                             n_paths=1_500, days=300, seed=7)
    assert a["V"] != b["V"]


@pytest.fixture(scope="module")
def spy_holds(requires_panel):
    requires_panel(DATA / "d440_holds.csv.gz")
    import pandas as pd
    h = pd.read_csv(DATA / "d440_holds.csv.gz")
    return h[h["symbol"] == "SPY"]


def test_guard_b2_p4_life_reproduces_d440s_published_cell(spy_holds):
    """`data/d440_lifecycle.json`, MFFU Rapid EOD 50K / SPY / voltgt / f* = 0.007.

    The artefact was written by `pandas.to_json`, which rounds to 10 decimal places, so
    10 dp IS the published precision and the comparison is exact at it (R16: reproduce
    exactly on the original build, never at a tolerance chosen after seeing the gap).
    """
    plan = HP.load_venue("mffu_rapid_eod_50k")
    out = HP.p4_life(spy_holds["d_end"].to_numpy(float), plan, basis="return",
                     lows=spy_holds["d_low"].to_numpy(float),
                     highs=spy_holds["d_high"].to_numpy(float),
                     target_dollar_vol=0.007 * 50_000, rule="voltgt",
                     n_paths=8_000, days=600, seed=HP.SEED_D440)
    rows = json.loads((DATA / "d440_lifecycle.json").read_text(encoding="utf-8"))
    bar = [r for r in rows if r.get("kind") == "BAR"][0]
    cell = [r for r in rows
            if r.get("symbol") == "SPY" and r.get("plan") == "MFFU Rapid EOD/50"
            and r.get("rule") == "voltgt" and r.get("provider") == "MEASURED"
            and r.get("frac") == 0.007][0]
    assert out["n_observations"] == int(cell["n_holds"])
    assert round(out["net_per_cycle_usd"], 10) == bar["V"] == cell["V"]
    assert round(out["expected_funded_life_years"], 10) == bar["life_years"]
    assert out["p_alive"] == bar["p_alive"] == 0.0
    for mine, theirs in (("expected_profit_usd", "paid_mean"),
                         ("expected_fees_usd", "fees_mean"),
                         ("net_per_cycle_usd_se", "V_se"),
                         ("p_paid", "p_paid"), ("p_pass", "p_pass"),
                         ("p_breached", "p_breached"),
                         ("n_payouts_mean", "n_payouts_mean"),
                         ("expected_life_days", "life_days_mean"),
                         ("expected_funded_life_days", "fund_days_mean")):
        assert round(out[mine], 10) == cell[theirs], (mine, out[mine], cell[theirs])


def test_guard_b2_can_fail_a_different_risk_grid_point_does_not_reproduce(spy_holds):
    plan = HP.load_venue("mffu_rapid_eod_50k")
    other = HP.p4_life(spy_holds["d_end"].to_numpy(float), plan, basis="return",
                       lows=spy_holds["d_low"].to_numpy(float),
                       highs=spy_holds["d_high"].to_numpy(float),
                       target_dollar_vol=0.011 * 50_000, rule="voltgt",
                       n_paths=8_000, days=600, seed=HP.SEED_D440)
    rows = json.loads((DATA / "d440_lifecycle.json").read_text(encoding="utf-8"))
    bar = [r for r in rows if r.get("kind") == "BAR"][0]
    assert round(other["net_per_cycle_usd"], 10) != bar["V"]


# ============================================================ (a) D501


@pytest.fixture(scope="module")
def d501_series(requires_panel, d495):
    """D501's candidate daily P&L, rebuilt through D501's own input path.

    IN-SAMPLE ONLY. `d484.series_for` refuses any row past 2023 and `build_panel` goes
    through it, so this reads 2016-01-07..2023-12-29 and nothing from 2024-01-01 on.
    """
    requires_panel(REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz")
    import pandas as pd
    d484 = sys.modules["d484_offdiagonal_and_macd"]
    d491 = sys.modules["d491_conditional_hold"]
    meta = json.loads(d495.META.read_text(encoding="utf-8"))
    spec = json.loads(d484.SPECS.read_text(encoding="utf-8"))
    d_all = pd.read_csv(d495.FIX)
    p = d495.build_panel(d_all, meta, spec)["NQ"]
    pnl_tk, _ = d491.simulate(p["O"], p["C"], p["AGREE"], p["first"], 5,
                              p["cost"], p["tick_pts"])
    return pnl_tk * p["tick_usd"]


@pytest.fixture(scope="module")
def d501_artefact():
    return json.loads((DATA / "d501_worst_day_frequency.json").read_text(encoding="utf-8"))


def test_guard_a_the_rebuilt_series_is_d501s(d501_series, d501_artefact):
    """Before any statistic: the input reproduces, or nothing below means anything."""
    d = d501_series
    assert len(d) == d501_artefact["candidate"]["n_sessions"] == 1873
    assert float(d.std(ddof=1)) == d501_artefact["daily_sigma_usd"]
    assert float(d.min()) == d501_artefact["worst_12_days"][0]["pnl"]


def test_guard_a_max_drawdown_life_reproduces_d501_exactly(d501_series, d501_artefact):
    n_deaths, life, episodes = HP.max_drawdown_life(d501_series, 2_000.0)
    assert n_deaths == d501_artefact["empirical_trailing_dd_deaths"] == 7
    assert life == d501_artefact["empirical_trailing_dd_life_sessions"]
    assert [e[2] for e in episodes] == [r["sessions"] for r in d501_artefact["account_lives"]]


def test_guard_a_p3_reproduces_d501s_rate_life_and_worst_day(d501_series, d501_artefact):
    g = HP.p3(d501_series, 50_000.0)
    art = d501_artefact
    assert g["p3a_breaches"] == art["frequency_by_threshold"]["-1000"]["days"] == 2
    assert g["p3a_breaches_per_year"] == art["frequency_by_threshold"]["-1000"]["per_year"]
    assert g["p3a_recurrence_years"] == art["frequency_by_threshold"]["-1000"][
        "recurrence_years"]
    assert g["life_with_p3_sessions"] == art["life_if_P3_enforced_sessions"]
    assert g["deaths_with_p3"] == art["deaths_if_P3_enforced"] == 9
    assert g["p3c_worst_day_usd"] == art["worst_12_days"][0]["pnl"]
    assert g["p3c_in_sigma"] == art["worst_day_in_sigma"]
    assert g["p_breach_in_252"] == art["p_breach_in_252_sessions"]
    # D501's own finding, reproduced: capping every breaching day at the P3 limit -- the
    # best a same-day stop could do -- buys ZERO account life.
    capped = np.where(d501_series <= -1_000.0, -1_000.0, d501_series)
    nd_c, life_c, _ = HP.max_drawdown_life(capped, 2_000.0)
    assert (nd_c, life_c) == (art["deaths_if_P3_days_were_capped"],
                              art["life_if_P3_days_were_capped"])
    assert (nd_c, life_c) == (7, art["empirical_trailing_dd_life_sessions"])


def test_guard_a_can_fail_one_session_rolled_changes_the_life(d501_series, d501_artefact):
    rolled = np.roll(np.asarray(d501_series, dtype=float), 1)
    _, life, _ = HP.max_drawdown_life(rolled, 2_000.0)
    assert life != d501_artefact["empirical_trailing_dd_life_sessions"]


def test_guard_a_p1_sizing_on_d501s_series_says_what_d503s_p1_key_does_not(d501_series):
    """The correction D590 records: D503's `P1_post_sizing_usd_per_year` is not sized."""
    s = HP.p1_size(d501_series, 2_000.0)
    assert s["max_trailing_dd_usd"] > 2_000.0
    assert s["size_multiplier"] < 1.0
    assert abs(s["post_sizing_usd_per_year"]) < abs(s["usd_per_year_at_traded_size"])


# ============================================================ (c) D503


def _same(a, b) -> bool:
    if a is None or b is None:
        return a is b
    if isinstance(a, float) and math.isnan(a):
        return isinstance(b, float) and math.isnan(b)
    return bool(a == b)


D503_SHARED_KEYS = (
    "P1_post_sizing_usd_per_year", "P3a_breaches_per_year", "P3a_bar", "P3a_pass",
    "P3a_breaches", "P3a_recurrence_years", "P3b_life_cost", "P3b_bar", "P3b_pass",
    "P3c_worst_day_usd", "P3c_worst_day_in_sigma", "P3c_share_of_loss_budget",
    "life_dd_only_sessions", "life_with_P3_sessions", "deaths_dd_only", "deaths_with_P3",
    "P4_expected_profit_usd", "P4_expected_life_days", "P5_best_day_share",
    "P5_haircut_usd", "P5_pass", "p_breach_in_252",
)


def test_guard_c1_hurdle_p_equals_d503s_function_on_random_series(d503):
    """Function against function. D503's own daily series is not committed and its
    inputs are the 2024+ forward slice, which nothing here reads."""
    rng = np.random.default_rng(590)
    for _ in range(12):
        n = int(rng.integers(60, 700))
        s = rng.normal(rng.uniform(-8, 20), rng.uniform(80, 400), n)
        s[rng.random(n) < 0.3] = 0.0
        theirs = d503.hurdle_p(s, "x")
        mine = HP.hurdle_p(s, "mffu_rapid_eod_50k", 50_000.0, run_lifecycle=False)
        for k in D503_SHARED_KEYS:
            assert _same(theirs[k], mine[k]), (k, theirs[k], mine[k])


def test_guard_c1_every_d503_key_is_present(d503):
    s = np.concatenate([np.full(200, 5.0), np.full(52, -50.0)])
    theirs = d503.hurdle_p(s, "x")
    mine = HP.hurdle_p(s, "mffu_rapid_eod_50k", 50_000.0, run_lifecycle=False)
    missing = set(theirs) - set(mine)
    assert missing == set(), f"D503 keys this module drops: {sorted(missing)}"


def test_guard_c1_can_fail_a_perturbed_series_disagrees(d503):
    s = np.concatenate([np.full(200, 5.0), np.full(52, -50.0)])
    theirs = d503.hurdle_p(s, "x")
    mine = HP.hurdle_p(s + 1.0, "mffu_rapid_eod_50k", 50_000.0, run_lifecycle=False)
    assert theirs["P1_post_sizing_usd_per_year"] != mine["P1_post_sizing_usd_per_year"]


def test_guard_c2_d503s_stored_dicts_reproduce_from_their_stored_summaries():
    """Every key of D503's committed `hurdle_p` block that its stored summaries determine.

    The path-dependent keys (`life_*_sessions`, `deaths_*`) are NOT reproducible without
    the daily series, which D503 did not commit; they are excluded by name rather than
    passed over, and D590 records that the artefact cannot be fully re-derived.
    """
    art = json.loads((DATA / "d503_forward_book.json").read_text(encoding="utf-8"))
    checked = 0
    for arm in ("macd", "k8", "book"):
        hp, perf = art["hurdle_p"][arm], art["performance"][arm]
        n, nbr = perf["n_sessions"], hp["P3a_breaches"]
        want = {
            "P1_post_sizing_usd_per_year": perf["mean_usd"] * 252,
            "P3a_breaches_per_year": nbr / n * 252,
            "P3a_recurrence_years": HP.recurrence_years(nbr, n),
            "P3c_worst_day_usd": perf["worst_day_usd"],
            "P3c_worst_day_in_sigma": perf["worst_day_usd"] / perf["daily_sigma_usd"],
            "P3c_share_of_loss_budget": -perf["worst_day_usd"] / 2_000.0,
            "p_breach_in_252": HP.p_at_least_one(nbr, n, 252),
            "P3b_life_cost": 1.0 - hp["life_with_P3_sessions"] / hp["life_dd_only_sessions"],
        }
        if perf["sharpe"] > 0:
            ep, el = HP.expected_profit_before_breach_usd(
                perf["sharpe"], perf["daily_sigma_usd"], 50_000.0, 2_000.0)
            want["P4_expected_profit_usd"] = ep
            want["P4_expected_life_days"] = el
        for k, v in want.items():
            assert hp[k] == v, f"{arm}.{k}: published {hp[k]!r}, recomputed {v!r}"
            checked += 1
    assert checked == 28


def test_guard_c2_the_headline_figures_d503_published_are_the_ones_checked():
    """The three numbers the D503 record quotes, pinned so a drift is visible."""
    art = json.loads((DATA / "d503_forward_book.json").read_text(encoding="utf-8"))
    book = art["hurdle_p"]["book"]
    assert book["P3a_breaches_per_year"] == pytest.approx(6.957055214723926, abs=1e-12)
    assert book["P3c_worst_day_usd"] == pytest.approx(-2724.0089999999564, abs=1e-9)
    assert book["P3c_share_of_loss_budget"] == pytest.approx(1.362004499999978, abs=1e-12)
    assert book["life_dd_only_sessions"] == 31.05
    assert book["deaths_dd_only"] == 20


# ============================================================ (d) D495


def test_guard_d_p5_recognised_equals_d495s(d495):
    rng = np.random.default_rng(495)
    for _ in range(50):
        x = rng.normal(0, 100, int(rng.integers(2, 200))) * float(rng.choice([1.0, 0.0, -1.0]))
        a, b = d495.p5_recognised(x), HP.p5_recognised(x)
        assert set(a) == set(b)
        assert all(_same(a[k], b[k]) for k in a), (a, b)
    assert HP.P5_CAP == d495.P5_CAP == 0.30


# ============================================================ the rest of the API


def test_p2_flatten_converts_nothing_it_reads_the_et_column():
    """Topstep's rule is 15:10 CT; the venue file stores 16:10 ET, converted once."""
    assert HP.venue_record("topstep_50k")["flatten_time_et"]["value"] == "16:10"
    assert "3:10 PM CT" in HP.venue_record("topstep_50k")["flatten_time_et"]["provenance"]
    assert HP.p2_flatten(["16:10"], "topstep_50k") is True
    assert HP.p2_flatten(["16:11"], "topstep_50k") is False


@pytest.mark.parametrize("exits,venue,exc", [
    ([], "topstep_50k", ValueError),
    (["9:35"], "topstep_50k", ValueError),
    (["24:00"], "topstep_50k", ValueError),
    (["15:59"], "take_profit_trader_25k", ValueError),
    (["15:59"], "nope", KeyError),
])
def test_p2_flatten_guards_raise(exits, venue, exc):
    with pytest.raises(exc):
        HP.p2_flatten(exits, venue)


def test_p4_life_refuses_a_unit_mismatch_rather_than_scaling_silently():
    plan = HP.load_venue("mffu_rapid_eod_50k")
    d = np.tile(np.array([100.0, -50.0, 25.0, -75.0]), 30)
    with pytest.raises(ValueError, match="ALREADY dollars"):
        HP.p4_life(d, plan, basis="usd", target_dollar_vol=350.0)
    with pytest.raises(ValueError, match="target_dollar_vol"):
        HP.p4_life(d / 50_000.0, plan, basis="return")
    with pytest.raises(ValueError, match="vol-targeted"):
        HP.p4_life(d, plan, basis="usd", rule="voltgt")
    with pytest.raises(ValueError, match="basis must be"):
        HP.p4_life(d, plan, basis="points")


def test_p4_life_on_a_close_only_series_names_its_optimism():
    plan = HP.load_venue("mffu_rapid_eod_50k")
    d = np.tile(np.array([100.0, -50.0, 25.0, -75.0]), 30)
    out = HP.p4_life(d, plan, basis="usd", n_paths=200, days=150)
    assert "OPTIMISTIC" in out["path_basis"]
    assert out["account_cost_usd"] == plan.fee_eval + plan.fee_activation
    assert set(out) >= {"expected_profit_usd", "expected_life_years",
                        "P4_binding_profit_exceeds_cost", "P4_preferred_life_pass"}


def test_p4_life_a_measured_intraday_path_is_never_kinder_than_the_close_only_one():
    """The venue kills on the intraday LOW; adding one makes the account die sooner."""
    plan = HP.load_venue("mffu_rapid_eod_50k")
    rng = np.random.default_rng(3)
    d = rng.normal(20.0, 250.0, 800)
    flat = HP.p4_life(d, plan, basis="usd", n_paths=400, days=400, seed=11)
    deep = HP.p4_life(d, plan, basis="usd", lows=np.minimum(d, 0.0) - 400.0,
                      highs=np.maximum(d, 0.0), n_paths=400, days=400, seed=11)
    assert deep["expected_life_days"] < flat["expected_life_days"]
    assert deep["path_basis"] == "measured intraday path"


def test_measured_provider_rejects_a_path_that_is_not_a_path():
    with pytest.raises(ValueError, match="d_low must be"):
        HP.measured_provider(np.array([1.0, -1.0]), np.array([1.0, 0.0]),
                             np.array([2.0, 0.0]), target_dollar_vol=None,
                             rule="static", n_paths=2, shuffle=False, seed=1)
    with pytest.raises(ValueError, match="outside"):
        HP.measured_provider(np.array([5.0, -1.0]), np.array([-1.0, -2.0]),
                             np.array([1.0, 0.0]), target_dollar_vol=None,
                             rule="static", n_paths=2, shuffle=False, seed=1)


def test_sigma_series_never_sees_the_current_observation():
    """D440's lag audit, ported with the estimator."""
    rng = np.random.default_rng(1)
    r = rng.normal(0, 0.01, 200)
    s = HP.sigma_series(r)
    r2 = r.copy()
    r2[HP.VOL_WINDOW] += 10.0
    assert np.isclose(HP.sigma_series(r2)[HP.VOL_WINDOW], s[HP.VOL_WINDOW], atol=1e-12)
    assert np.isnan(s[: HP.VOL_WINDOW]).all()
    # and a second implementation agrees where it is defined
    alt = np.array([math.sqrt(sum((v - sum(r[t - 21:t]) / 21) ** 2 for v in r[t - 21:t]) / 20)
                    for t in range(HP.VOL_WINDOW, len(r))])
    assert np.allclose(s[HP.VOL_WINDOW:], alt, atol=1e-12)


def test_per_year_recomputes_every_p3_number_inside_the_year():
    """D503/D504: sigma at a fixed micro tracks the price level, so a window-wide P3c
    describes no year in the window."""
    dates = [f"2020-01-{i + 1:02d}" for i in range(20)] + \
            [f"2021-01-{i + 1:02d}" for i in range(20)]
    d = np.concatenate([np.full(20, 10.0), np.full(20, 10.0)])
    d[5] = -1_500.0          # 2020's only breach
    d[25] = -1_500.0
    d[26] = -1_500.0         # 2021 has two
    rows = HP.per_year(d, dates, 50_000.0)
    assert [r["year"] for r in rows] == ["2020", "2021"]
    assert rows[0]["p3a_breaches"] == 1
    assert rows[1]["p3a_breaches"] == 2
    assert rows[0]["p3a_breaches_per_year"] != rows[1]["p3a_breaches_per_year"]
    assert all("sortino" in r for r in rows)          # R17
    with pytest.raises(ValueError, match="dates against"):
        HP.per_year(d, dates[:-1], 50_000.0)


def test_hurdle_p_reports_a_sortino_beside_every_sharpe():
    """R17, the principal's mandate of 2026-09-19."""
    rng = np.random.default_rng(17)
    d = rng.normal(5.0, 200.0, 300)
    h = HP.hurdle_p(d, "topstep_50k", 50_000.0, run_lifecycle=False)
    assert math.isfinite(h["sharpe"]) and math.isfinite(h["sortino"])
    for row in HP.per_year(d, [f"2020-01-{1 + i % 28:02d}" for i in range(300)]):
        assert "sharpe" in row and "sortino" in row


def test_hurdle_p_runs_the_lifecycle_when_asked_and_names_the_binding_clause():
    rng = np.random.default_rng(4)
    d = rng.normal(30.0, 200.0, 500)
    h = HP.hurdle_p(d, "mffu_rapid_eod_50k", 50_000.0, n_paths=500, days=400)
    assert h["P4_lifecycle_account_cost_usd"] == 209.0
    assert isinstance(h["P4_lifecycle_P4_binding_profit_exceeds_cost"], bool)
    assert h["P4_lifecycle_expected_life_years"] > 0.0


@pytest.mark.parametrize("bad", [np.array([1.0]), np.array([1.0, np.nan])])
def test_hurdle_p_raises_on_an_unusable_series(bad):
    with pytest.raises(ValueError):
        HP.hurdle_p(bad, "topstep_50k", 50_000.0, run_lifecycle=False)


def test_the_constants_are_r11s_as_amended():
    assert (HP.DD_FRACTION, HP.P3_CAP_FRACTION) == (0.04, 0.02)
    assert (HP.P3A_BAR, HP.P3B_BAR) == (1.0, 0.33)
    assert HP.P5_CAP == 0.30                       # NOT the header table's 40%
    assert HP.P4_LIFE_PREFERRED_YEARS == 1.0       # preferred, not binding
    assert HP.TRADING_DAYS == 252
