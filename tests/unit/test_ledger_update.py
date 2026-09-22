"""`backtest_framework.ledger.update` -- Section 5.2's update and Section 7.1's timing (D610).

Covers the settlement flow ledger's required unit tests 5 (line 711), 8 (line 714, the
`S_norm` clause) and 9 (line 715). The hand-worked case for number 6 lives in
`tests/golden/test_ledger_flows_ledger.py`.

`W_start` is NEVER hardcoded here. It is pulled from `data/settlement_windows.csv` through
`scripts/settlement_windows.py:147 window_for` (D586), which raises rather than defaulting --
NG and CL are 14:28:00-14:30:00 ET from 2009-06-01 under SER-4867. The script is loaded by
PATH under a private module name, the way `tests/unit/test_settlement_windows.py` does it,
because `src/` may never import `scripts/` (`tests/unit/test_import_boundaries.py`) and the
library therefore takes `w_start` as an argument.

Offline: no network, no fixture beyond that one committed CSV, no strategy return.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

from backtest_framework.ledger.flows import LedgerError
from backtest_framework.ledger.update import (
    CANDIDATE_T0,
    ENTRY_CLEARANCE_MIN,
    entry_decision,
    kalman_update,
    s_pre_z,
    trailing_mean_20,
)

REPO = Path(__file__).resolve().parents[2]
SETTLEMENT_WINDOWS = REPO / "scripts" / "settlement_windows.py"


def _load_settlement_windows():
    """Import the D586 script by PATH under a private name (D546: pytest imports any path)."""
    spec = importlib.util.spec_from_file_location("_d610_settlement_windows", SETTLEMENT_WINDOWS)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


SW = _load_settlement_windows()
#: NG's sourced window on a day inside the SER-4867 period. Read, never typed.
NG_W_START = SW.window_for("NG", "2026-03-16").start_et


def _series(days: int = 20, value: float = 100.0, start: int = 1) -> dict[str, float]:
    return {f"2026-01-{start + i:02d}": value for i in range(days)}


# --------------------------------------------------------------------- the settlement window


def test_the_window_used_here_is_the_sourced_one_and_not_a_literal() -> None:
    """The test's own input is pinned to the committed table, not to the deposit's guess.

    Section 3.4 called 14:28-14:30 "currently understood" and asked for it to be verified;
    D586 verified it. If the table ever changes, this file's expectations move with it.
    """
    assert NG_W_START == "14:28:00"
    assert SW.window_for("MNG", "2026-03-16").start_et == NG_W_START  # micros inherit
    assert SW.window_for("CL", "2026-03-16").start_et == NG_W_START


# ------------------------------------------------------------------- required unit test 8


def test_ledger_8_s_norm_excludes_the_evaluation_day_and_everything_after_it() -> None:
    """Line 714: "V_d, sigma_d, S_norm and the fund data used on day t exclude data from day
    t onward."

    `S_norm` is line 371's "trailing 20-day mean for the same interval", and this is its
    guard. The refusal is loud rather than a filter, because a filter leaves the caller
    believing a guard ran.
    """
    prior = _series()
    assert trailing_mean_20(prior, "2026-02-01") == 100.0

    same_day = dict(prior)
    same_day["2026-02-01"] = 1e6
    with pytest.raises(LedgerError, match="at or after the evaluation day"):
        trailing_mean_20(same_day, "2026-02-01")

    later = dict(prior)
    later["2026-03-15"] = 1e6
    with pytest.raises(LedgerError, match="Required unit test 8"):
        trailing_mean_20(later, "2026-02-01")

    with pytest.raises(LedgerError, match="only 19 prior day"):
        trailing_mean_20(_series(days=19), "2026-02-01")

    # Exactly the 20 most recent prior days enter; an older 21st does not move the mean.
    longer = {f"2026-01-{i + 1:02d}": (1e6 if i == 0 else 100.0) for i in range(21)}
    assert trailing_mean_20(longer, "2026-02-01") == 100.0

    # The mean is fsum-based, so the order the days arrived in cannot change it.
    uneven = {f"2026-01-{i + 1:02d}": float(i) * 0.1 for i in range(20)}
    assert trailing_mean_20(uneven, "2026-02-01") == trailing_mean_20(dict(reversed(list(uneven.items()))), "2026-02-01")

    # z is the difference, line 368. Not a standardisation, despite the name.
    assert s_pre_z(1400.0, 100.0) == 1300.0
    assert s_pre_z(-50.0, 100.0) == -150.0


# ------------------------------------------------------------------- required unit test 5


def test_ledger_5_p_zero_leaves_the_prior_alone_and_infinite_R_kills_the_gain() -> None:
    """Line 711: "with p = 0 the posterior equals the prior and Q_rem = mu_total; with
    R -> infinity, K -> 0."

    Both halves are EXACT here and are asserted with `==`. The second is an IEEE-754
    identity, not a limit: a finite double divided by infinity is a zero.
    """
    mu, var, z = 137.5, 400.0, -900.0

    u = kalman_update(mu, var, 0.0, 100.0, z)
    assert u.k == 0.0
    assert u.q_hat == mu
    assert u.var_post == var
    assert u.q_rem == mu
    assert u.sigma_rem == math.sqrt(var)

    inf = kalman_update(mu, var, 0.5, math.inf, z)
    assert inf.k == 0.0
    assert inf.q_hat == mu
    assert inf.var_post == var
    assert inf.q_rem == 0.5 * mu

    # A large but finite R approaches it from above without reaching it.
    big = kalman_update(mu, var, 0.5, 1e18, z)
    assert 0.0 < big.k < 1e-12

    # p = 1 means every contract has already traded: nothing remains and nothing is traded.
    done = kalman_update(mu, var, 1.0, 100.0, z)
    assert done.q_rem == 0.0
    assert done.sigma_rem == 0.0

    # The update can only ever shrink the variance -- (1 - Kp) is in [0, 1] by construction.
    for p in (0.0, 0.1, 0.5, 0.9, 1.0):
        out = kalman_update(mu, var, p, 100.0, z)
        assert 0.0 <= out.k * p <= 1.0
        assert out.var_post <= var
        assert out.q_rem == (1.0 - p) * out.q_hat


def test_kalman_update_refuses_what_section_eight_constrains() -> None:
    """p in [0, 1] and R > 0 are Section 8's constraints (line 472), asserted not clipped."""
    for bad_p in (-0.01, 1.01):
        with pytest.raises(LedgerError, match="p must lie in"):
            kalman_update(100.0, 400.0, bad_p, 100.0, 60.0)
    # A nan p is refused one step earlier, by the finiteness check, and the message says so
    # rather than reporting a range comparison that is False for every nan.
    with pytest.raises(LedgerError, match="p is not finite"):
        kalman_update(100.0, 400.0, float("nan"), 100.0, 60.0)
    with pytest.raises(LedgerError, match="R must be positive"):
        kalman_update(100.0, 400.0, 0.5, 0.0, 60.0)
    with pytest.raises(LedgerError, match="R must be positive"):
        kalman_update(100.0, 400.0, 0.5, -1.0, 60.0)
    with pytest.raises(LedgerError, match="R is nan"):
        kalman_update(100.0, 400.0, 0.5, float("nan"), 60.0)
    with pytest.raises(LedgerError, match="var must be non-negative"):
        kalman_update(100.0, -1.0, 0.5, 100.0, 60.0)
    with pytest.raises(LedgerError, match="z is not finite"):
        kalman_update(100.0, 400.0, 0.5, 100.0, float("inf"))


# ------------------------------------------------------------------- required unit test 9


def test_ledger_9_earliest_pass_signals_at_the_first_passing_t0_and_never_re_enters() -> None:
    """Line 430's earliest-pass rule under line 445's three-minute hard constraint.

    Hand file case 7. `w_start` comes from `window_for`, never from a literal in this file.
    """
    assert CANDIDATE_T0 == ("13:50", "14:00", "14:10")
    assert ENTRY_CLEARANCE_MIN == 3

    def decide(p1: bool, p2: bool, p3: bool, entry_minutes: int = 2) -> str | None:
        return entry_decision(
            passes=dict(zip(CANDIDATE_T0, (p1, p2, p3))),
            w_start=NG_W_START,
            entry_minutes=entry_minutes,
        )

    # The EARLIEST passing t0, not the best and not the last.
    assert decide(True, True, True) == "13:50"
    assert decide(False, True, True) == "14:00"
    assert decide(False, False, True) == "14:10"
    assert decide(False, False, False) is None

    # A pass at 13:50 is taken even when later candidates also pass: "at most one entry per
    # instrument per day", and the function has no state to re-enter from.
    assert decide(True, False, False) == "13:50"

    # Line 445. entry_minutes = 16 puts 14:10's completion at 14:26, past the 14:25 deadline,
    # and the rule does NOT fall back to an earlier t0 whose criteria already failed.
    assert decide(False, False, True, entry_minutes=16) is None
    assert decide(False, True, True, entry_minutes=16) == "14:00"
    # At the boundary: completing exactly 3 minutes before W_start is permitted (">= 3").
    assert decide(False, False, True, entry_minutes=15) == "14:10"
    assert decide(False, False, True, entry_minutes=16) is None

    # Section 7.1's fixed-time variant is the same function with one candidate.
    assert entry_decision(("14:10",), passes={"14:10": True}, w_start=NG_W_START, entry_minutes=2) == "14:10"


def test_entry_decision_refuses_a_grid_or_a_verdict_set_nobody_registered() -> None:
    with pytest.raises(LedgerError, match="not strictly increasing"):
        entry_decision(("14:10", "13:50"), passes={"14:10": True, "13:50": True},
                       w_start=NG_W_START, entry_minutes=2)
    with pytest.raises(LedgerError, match="no verdict for"):
        entry_decision(passes={"13:50": True}, w_start=NG_W_START, entry_minutes=2)
    with pytest.raises(LedgerError, match="not candidates"):
        entry_decision(("13:50",), passes={"13:50": True, "14:00": True},
                       w_start=NG_W_START, entry_minutes=2)
    with pytest.raises(LedgerError, match="non-zero second"):
        entry_decision(passes=dict.fromkeys(CANDIDATE_T0, True), w_start="14:28:30", entry_minutes=2)
    with pytest.raises(LedgerError, match="must be a bool"):
        entry_decision(passes={"13:50": 1, "14:00": 0, "14:10": 0},  # type: ignore[dict-item]
                       w_start=NG_W_START, entry_minutes=2)
    with pytest.raises(LedgerError, match="entry_minutes must be non-negative"):
        entry_decision(passes=dict.fromkeys(CANDIDATE_T0, True), w_start=NG_W_START, entry_minutes=-1)
