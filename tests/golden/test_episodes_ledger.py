"""Golden tests for `validation/episodes.py` (D592).

The ledger of record is the deposit's programme control 5 (`SETTLEMENT_FLOW_LEDGER_PREREG.md`
§13A.8(5), `OPENING_AGENT_STATE_PREREG.md` §12A(5)) and its unit test 69. Every constant
below was worked out in `test_episodes_ledger.hand.txt` before the module was run.

THE D504 ANCHOR IS A CODE IDENTITY, NOT A RECOMPUTATION, and the reason is in Part 0 of
the .hand.txt: `data/d504_arm_full_history.json` publishes the `concentration_usable`
block but NOT the daily series it was computed from, and D504's `_usable` window runs
2016-01-04 → 2026-09-09, i.e. through the spent 2024+ slice, so re-deriving the series
would mean reading 2024+ fixture rows. Instead the block's own source text is extracted
from `scripts/d504_arm_full_history.py` and exec'd beside `symmetric_trim` on a synthetic
series — a stronger check than a stored number, and it reads no bar at all.

No market fixture is read by any test in this file.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import numpy as np
import pytest

from backtest_framework.validation.episodes import (
    drop_best_days,
    drop_best_year,
    episode_checks,
    sessions_to_half_pnl,
    shared_period,
    symmetric_trim,
)

REPO = Path(__file__).resolve().parents[2]
D504_SCRIPT = REPO / "scripts" / "d504_arm_full_history.py"
D504_JSON = REPO / "data" / "d504_arm_full_history.json"

TOL = 1e-12  # one sqrt and one division; the exact quantities below use `==`

# --------------------------------------------------------------- the synthetic series

DATES = [f"{y}-{m:02d}-{d:02d}" for y in (2020, 2021) for m in range(1, 7) for d in (5, 20)]
A = [-20, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 100, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, -60]
B = [-10, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 50, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, -40]
C = A[:-1] + [-130]

SQRT252 = 15.874507866387544


def test_the_series_is_what_the_hand_file_says_it_is():
    """If the fixture drifts, every number below is about a different object."""
    assert len(DATES) == len(A) == len(B) == len(C) == 24
    assert len(set(A)) == 24 and len(set(B)) == 24, "ties would pin numpy's unstable argsort"
    assert sum(A) == 251 and sum(B) == 231 and sum(C) == 181
    assert sum(v * v for v in A) == 17311 and sum(v * v for v in B) == 7511
    assert sum(A[:12]) == 190 and sum(A[12:]) == 61


# ------------------------------------------------------------------ Part 2: the trim


def test_symmetric_trim_hand_values():
    got = symmetric_trim(A, frac=0.01)
    # k = max(1, int(24 * 0.01)) = max(1, 0) = 1 — the clamp is the point of n = 24
    assert got["n_trimmed_each_side"] == 1
    assert got["sessions_to_half_pnl"] == 3
    assert got["top1"] == 100 / 251
    assert got["top5"] == 178 / 251
    assert got["top10"] == 253 / 251
    assert got["top1pct"] == 100 / 251
    assert got["bottom1pct"] == -60 / 251
    assert got["pnl_ex_both_1pct_usd"] == 211.0
    assert got["share_ex_both_1pct"] == 211 / 251
    assert got["pnl_ex_both_top10_usd"] == 42.0
    assert set(got) == {
        "sessions_to_half_pnl", "top1", "top5", "top10", "top1pct", "bottom1pct",
        "pnl_ex_both_1pct_usd", "share_ex_both_1pct", "pnl_ex_both_top10_usd",
        "n_trimmed_each_side",
    }


def test_a_one_sided_share_above_one_is_ordinary_arithmetic():
    """top10 = 253/251 > 1 because the two worst sessions carry -80. CLAUDE.md §2: the
    one-sided share is a flag, never a verdict, which is why both tails are computed in
    the same call."""
    got = symmetric_trim(A)
    assert got["top10"] > 1.0
    assert got["bottom1pct"] < 0.0
    assert got["share_ex_both_1pct"] == pytest.approx(0.8406374501992032, abs=TOL)


def test_sessions_to_half_pnl_hand_value():
    assert sessions_to_half_pnl(A) == 3  # 100, +21 = 121 < 125.5, +20 = 141 >= 125.5


# ---------------------------------------------------------- Parts 3-5: the two removals


def test_drop_best_year_hand_values():
    got = drop_best_year(A, DATES)
    assert got["year_dropped"] == "2020"  # $190 against 2021's $61, in DOLLARS
    assert got["total_before"] == 251.0
    assert got["total_after"] == 61.0
    assert got["sharpe_before"] == pytest.approx(6.5701535925513115, abs=TOL)
    assert got["sharpe_after"] == pytest.approx(3.7621023692280557, abs=TOL)


def test_drop_best_days_hand_values():
    got = drop_best_days(A, frac=0.01)
    assert got["n_dropped"] == 1
    assert got["total_before"] == 251.0
    assert got["total_after"] == 151.0
    assert got["mean_before"] == 251 / 24
    assert got["mean_after"] == 151 / 23
    assert got["sharpe_before"] == pytest.approx(6.5701535925513115, abs=TOL)
    assert got["sharpe_after"] == pytest.approx(6.149136505765647, abs=TOL)


def test_the_two_removals_are_not_interchangeable():
    """Dropping the best DAY costs 0.42 of Sharpe here; the best YEAR costs 2.81. That is
    why the deposit asks for both, "and, separately"."""
    year, days = drop_best_year(A, DATES), drop_best_days(A)
    assert (days["sharpe_before"] - days["sharpe_after"]) == pytest.approx(0.4210170867857, abs=1e-9)
    assert (year["sharpe_before"] - year["sharpe_after"]) == pytest.approx(2.8080512233233, abs=1e-9)


def test_episode_checks_can_come_back_true_and_false():
    """A boolean that cannot be False is not a check. C differs from A by $70 in one
    session and fails the year removal while passing the day removal."""
    passing = episode_checks(A, DATES)
    assert passing["edge_positive_after_both"] is True
    assert passing["drop_best_year"]["total_after"] == 61.0
    assert passing["drop_best_days"]["total_after"] == 151.0

    failing = episode_checks(C, DATES)
    assert failing["edge_positive_after_both"] is False
    assert failing["drop_best_year"]["year_dropped"] == "2020"
    assert failing["drop_best_year"]["total_after"] == -9.0
    assert failing["drop_best_days"]["total_after"] == 81.0


def test_episode_checks_reports_and_does_not_judge():
    got = episode_checks(A, DATES)
    assert set(got) == {
        "n_days", "total_usd", "mean_usd", "sharpe", "drop_best_year", "drop_best_days",
        "symmetric_trim", "edge_positive_after_both",
    }
    assert "verdict" not in got and "pass" not in got
    assert got["symmetric_trim"] == symmetric_trim(A)  # the symmetric trim travels with it


# ------------------------------------------------------------ Part 6: the shared period


def test_shared_period_hand_values():
    got = shared_period(A, B, DATES)
    # r = (n*Sxy - Sx*Sy) / sqrt((n*Sxx - Sx^2)(n*Syy - Sy^2)), all integers
    num = 24 * 10526 - 251 * 231
    den = float(np.sqrt(float((24 * 17311 - 251**2) * (24 * 7511 - 231**2))))
    assert num == 194643 and (24 * 17311 - 251**2) == 352463 and (24 * 7511 - 231**2) == 126903
    assert got["rho"] == pytest.approx(num / den, rel=1e-15)
    assert got["rho"] == pytest.approx(0.9203352968604872, abs=TOL)
    assert got["top10_overlap"] == 6
    assert got["same_month_share_a"] == 156 / 251
    assert got["same_month_share_b"] == 99 / 231
    assert got["flag"] is True


def test_the_flag_needs_all_three_terms():
    """B's month share is 0.4286, barely over the 0.40 bar, at rho 0.92. Move one term
    under its bar and the flag must drop."""
    got = shared_period(A, B, DATES)
    assert got["same_month_share_b"] == pytest.approx(0.42857142857142855, abs=TOL)
    # a second book that is anti-correlated with A: rho fails, so no flag whatever the months
    anti = [-v for v in A]
    other = shared_period(A, anti, DATES)
    assert other["rho"] < 0.0 and other["flag"] is False


# ---------------------------------------------------------------- Part 0: the D504 anchor


def _d504_concentration_block() -> str:
    """The source text of D504's `concentration_usable` block, by its marker comment."""
    lines = D504_SCRIPT.read_text(encoding="utf-8").splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip() == "# ---- concentration")
    stop = next(i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("P("))
    return textwrap.dedent("\n".join(lines[start:stop]))


@pytest.mark.parametrize("n", [137, 250, 2508])
def test_symmetric_trim_is_bit_identical_to_d504s_own_source(n):
    """The strong anchor: D504's block, exec'd from its own file, key for key and bit for
    bit against the port. Reads no market data. `n = 2508` is D504's own session count."""
    block = _d504_concentration_block()
    rng = np.random.default_rng(504)
    d_live = rng.normal(5.0, 50.0, n)
    assert float(d_live.sum()) > 0.0, "the agreement is pinned on a positive total"
    namespace: dict = {"np": np, "d_live": d_live}
    exec(compile(block, str(D504_SCRIPT), "exec"), namespace)  # noqa: S102
    theirs, mine = namespace["conc"], symmetric_trim(d_live)
    assert sorted(theirs) == sorted(mine)
    for key in theirs:
        assert theirs[key] == mine[key], (key, theirs[key], mine[key])
    assert mine["n_trimmed_each_side"] == max(1, n // 100)


def test_the_one_documented_divergence_from_d504():
    """On a NEGATIVE total D504's loop returns 1 (a running sum clears a negative
    threshold at the first session); the port returns None. D504 ran on +$25,697.0565, so
    the published block is unaffected — but the divergence is pinned, not assumed."""
    block = _d504_concentration_block()
    rng = np.random.default_rng(504)
    d_live = -rng.normal(5.0, 50.0, 137)
    assert float(d_live.sum()) < 0.0
    namespace: dict = {"np": np, "d_live": d_live}
    exec(compile(block, str(D504_SCRIPT), "exec"), namespace)  # noqa: S102
    assert namespace["conc"]["sessions_to_half_pnl"] == 1
    assert symmetric_trim(d_live)["sessions_to_half_pnl"] is None
    with pytest.raises(ValueError, match="positive total"):
        sessions_to_half_pnl(d_live)


def test_the_published_block_satisfies_the_ports_identities_exactly():
    """R16 on what IS in the artifact. Three relations the port guarantees, checked
    against `data/d504_arm_full_history.json` with `==` and no tolerance."""
    published = json.loads(D504_JSON.read_text(encoding="utf-8"))
    conc, overall = published["concentration_usable"], published["overall_usable"]

    assert conc["share_ex_both_1pct"] == conc["pnl_ex_both_1pct_usd"] / overall["total_usd"]
    assert conc["top1"] == overall["best_day_usd"] / overall["total_usd"]
    assert conc["n_trimmed_each_side"] == max(1, overall["n_sessions"] // 100)

    # the published values themselves, so a drift in the artifact is caught here too
    assert conc["sessions_to_half_pnl"] == 10
    assert conc["n_trimmed_each_side"] == 25
    assert conc["share_ex_both_1pct"] == 0.9169861341900946
    assert conc["top1pct"] == 0.9822092853319135
    assert conc["bottom1pct"] == -0.8991954195220087


def test_the_fourth_relation_is_float_noise_and_is_not_asserted_as_an_identity():
    """1 - top1pct - bottom1pct is 5 ulp from the published share. Recorded, not widened."""
    conc = json.loads(D504_JSON.read_text(encoding="utf-8"))["concentration_usable"]
    reconstructed = 1.0 - conc["top1pct"] - conc["bottom1pct"]
    assert reconstructed != conc["share_ex_both_1pct"]
    assert reconstructed == pytest.approx(conc["share_ex_both_1pct"], rel=1e-15)


def test_sessions_to_half_pnl_is_consistent_with_the_published_shares():
    """top5 = 0.323 < 0.5 <= top10 = 0.526, so the crossing is in sessions 6..10, and the
    published 10 lies there. Weak, but derivable from the artifact alone."""
    conc = json.loads(D504_JSON.read_text(encoding="utf-8"))["concentration_usable"]
    assert conc["top5"] < 0.5 <= conc["top10"]
    assert 6 <= conc["sessions_to_half_pnl"] <= 10


def test_d504s_usable_window_is_not_in_sample_which_is_why_nothing_is_recomputed():
    """The premise behind Part 0, asserted rather than asserted in prose: D504's `_usable`
    window runs through 2026, so re-deriving its series would read 2024+ fixture rows."""
    published = json.loads(D504_JSON.read_text(encoding="utf-8"))
    assert published["spec"]["usable_start"] == "2016-01-04"
    assert published["spec"]["span"][1] >= "2024-01-01"
    assert "2024" in published["usable_years"]
    assert published["overall_usable"]["n_sessions"] == 2508
