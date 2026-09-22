"""D610 -- the settlement flow ledger's guards, each proved to FIRE.

    uv run python scripts/ledger_selftest.py --selftest

`backtest_framework.ledger` is Section 4, 5.2, 7.1, 8A.2 and 8A.5 of
`SETTLEMENT_FLOW_LEDGER_PREREG.md` as arithmetic. Every input it refuses, it refuses by
RAISING (D48), and this script exists because "a self-test that cannot fail is worse than
none" (CLAUDE.md). Each case below BREAKS WHAT THE GUARD READS -- a same-day trade in a
trailing window, a p outside [0, 1], a fund whose prospectus nobody sourced -- and the run
fails if any of them comes back without an exception.

The positive cases are here for the same reason in reverse: two of this module's contracts
are EQUALITIES at a boundary (`Q8b == 0.0` for a fund already in P8a, and `K == 0.0` at
R = infinity), and an implementation that returned 1e-17 instead would satisfy every
refusal in this file and still be wrong.

Reads no fixture, writes no file, and computes no strategy return. The settlement window it
prints comes from `scripts/settlement_windows.py`'s committed table, not from a literal.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import math
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.ledger.flows import (  # noqa: E402
    LedgerError,
    held_months,
    is_large,
    large_lot_threshold,
    q1_notional,
    route,
)
from backtest_framework.ledger.netting import (  # noqa: E402
    FundExposure,
    consistency_flag,
    cot_usable_from,
    fit_lambda,
    swap_exposure_predictor,
    swap_record_time,
)
from backtest_framework.ledger.rolls import (  # noqa: E402
    RollSchedule,
    UNG_SCHEDULE,
    q8b,
    roll_days,
    roll_legs,
    validate_roll,
)
from backtest_framework.ledger.update import (  # noqa: E402
    CANDIDATE_T0,
    entry_decision,
    kalman_update,
    trailing_mean_20,
)

SPEC = "D610"
#: 20 prior days, ten trade sizes each: the hand file's case 5.
PRIOR_SIZES = {f"2026-01-{i + 1:02d}": [float(v) for v in range(1, 11)] for i in range(20)}
PRIOR_SERIES = {f"2026-01-{i + 1:02d}": 100.0 for i in range(20)}


def _settlement_windows():
    """Load the D586 script by PATH. `src/` may never import `scripts/`; this IS a script."""
    path = REPO / "scripts" / "settlement_windows.py"
    spec = importlib.util.spec_from_file_location("_d610_settlement_windows", path)
    if spec is None or spec.loader is None:  # pragma: no cover - a missing file is a broken repo
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def expect_raise(fn, what: str, log=print) -> bool:
    """D581's idiom, as `settlement_windows.py:207` writes it: prove the guard RAISES."""
    try:
        fn()
    except LedgerError as e:
        log(f"    RAISES on {what}: {str(e)[:96]}")
        return True
    raise AssertionError(f"guard did not raise on {what}")


def expect_equal(got, want, what: str, log=print) -> bool:
    """An EQUALITY at a boundary. `==`, never a tolerance: see the module docstring."""
    if got != want or type(got) is not type(want):
        raise AssertionError(f"{what}: got {got!r} ({type(got).__name__}), want {want!r}")
    log(f"    EXACT  {what}: {got!r}")
    return True


def run_selftest(log=print) -> int:
    checks = 0
    sw = _settlement_windows()
    w_start = sw.window_for("NG", "2026-03-16").start_et
    log(f"  W_start for NG on 2026-03-16, from {sw.TABLE.name}: {w_start} ET (never a literal here)")

    log("  -- the ledger's algebra, on the deposit's own numbers --")
    expect_equal(q1_notional(1e9, 2.0, 0.05, 1.0), 1e8, "Q1 notional at L = +2 (line 707)", log)
    expect_equal(q1_notional(1e9, -2.0, 0.05, 1.0), 3e8, "Q1 notional at L = -2 (line 707)", log)
    u = kalman_update(100.0, 400.0, 0.5, 100.0, 60.0)
    expect_equal((u.k, u.q_hat, u.var_post, u.q_rem), (1.0, 110.0, 200.0, 55.0),
                 "update step K, Q_hat, sigma^2_post, Q_rem (line 712)", log)
    expect_equal(roll_legs(0.25, 400.0, 1.0, 3.0, 4.0), (-100.0, 75.0),
                 "a long fund's roll legs (line 744)", log)
    expect_equal(roll_legs(0.25, 400.0, -2.0, 3.0, 4.0), (100.0, -75.0),
                 "an inverse fund's roll legs (line 338)", log)
    f = fit_lambda([2.0, 3.0, 1.0, 2.0, 4.0], [1.0, 1.0, 1.0, 1.0, 2.0])
    expect_equal((f.lam_unconstrained, f.lam, f.se), (2.0, 1.0, 0.25),
                 "lambda projected onto [0, 1] with its unconstrained slope (line 748)", log)
    expect_equal(consistency_flag(n_hat=1.0, se_n=0.25, lam=0.75, se_lam=0.25), True,
                 "the consistency flag beyond 2 combined SE (line 499)", log)
    expect_equal(large_lot_threshold(PRIOR_SIZES, "2026-02-01"), 9.0,
                 "L_min by nearest rank over 20 prior days (line 518)", log)
    expect_equal(is_large(9.0, 9.0), True, "a trade EXACTLY at L_min is large (line 753)", log)
    expect_equal(roll_days(dt.date(2026, 3, 30))[0], dt.date(2026, 3, 16),
                 "day one is 14 calendar days before near-month expiry (line 327)", log)
    expect_equal(entry_decision(passes=dict(zip(CANDIDATE_T0, (False, True, True))),
                                w_start=w_start, entry_minutes=2), "14:00",
                 "earliest-pass picks the first passing t0 (line 430)", log)
    checks += 11

    log("  -- the two EQUALITIES at a boundary, which no refusal would catch --")
    expect_equal(q8b(1, 1.0, 1e9, fund="UNG", p8a_funds=("UNG", "USO")), 0.0,
                 "Q8b for a fund already in P8a (line 746 / line 352)", log)
    expect_equal(kalman_update(100.0, 400.0, 0.5, math.inf, 60.0).k, 0.0,
                 "K at R = infinity (line 711)", log)
    checks += 2

    log("  -- each guard must be able to FIRE; break what the guard reads --")
    expect_raise(lambda: large_lot_threshold({**PRIOR_SIZES, "2026-02-01": [500.0]}, "2026-02-01"),
                 "a SAME-DAY trade in L_min's trailing window (8A.5 line 518)", log)
    expect_raise(lambda: trailing_mean_20({**PRIOR_SERIES, "2026-02-01": 1e6}, "2026-02-01"),
                 "day-t data in S_norm's trailing mean (line 371, required test 8)", log)
    expect_raise(lambda: kalman_update(100.0, 400.0, 1.1, 100.0, 60.0),
                 "p = 1.1, outside Section 8's [0, 1] constraint", log)
    expect_raise(lambda: kalman_update(100.0, 400.0, 0.5, 0.0, 60.0),
                 "R = 0, a measurement asserted to have no noise", log)
    expect_raise(lambda: RollSchedule.for_fund("USO"),
                 "USO, whose roll schedule line 328 says not to assume", log)
    expect_raise(lambda: held_months({"2026-04": 1.0}, default_to_front=True),
                 "held_months asked to default to the FRONT month (line 718)", log)
    expect_raise(lambda: swap_exposure_predictor(
                     [FundExposure("SCO", "us_fund", 5e6, f_fut=0.2, futures_held_change=1e6)]),
                 "a futures-held term in the swap predictor (line 749)", log)
    expect_raise(lambda: swap_record_time(dt.datetime(2026, 3, 17, 12, 0),
                                          dt.datetime(2026, 3, 17, 11, 0)),
                 "a swap disseminated BEFORE it was executed (line 750)", log)
    expect_raise(lambda: cot_usable_from("1986-05-16"),
                 "a COT report predating the weekly Tuesday convention (line 747)", log)
    expect_raise(lambda: validate_roll([0.25, 0.25, 0.25]),
                 "three observed days against a four-day schedule (line 745)", log)
    expect_raise(lambda: route(1e9, 2.0, 0.05, 1.5, 0.0, 10_000.0, 3.0),
                 "f_fut = 1.5, outside [0, 1]", log)
    expect_raise(lambda: fit_lambda([1.0, 2.0, 3.0], [0.0, 0.0, 0.0]),
                 "a constant-zero DeltaSX, which identifies no lambda (line 496)", log)
    checks += 12

    log("  -- and the failing CASE must fail: a validation that passes on a broken roll --")
    bad = validate_roll([1.0, 0.0, 0.0, 0.0])
    expect_equal((bad.passes, bad.fallback_to_p8b), (False, True),
                 "a one-day roll fails and falls back to P8b (line 340)", log)
    ok = validate_roll(list(UNG_SCHEDULE.fractions))
    expect_equal((ok.passes, ok.fallback_to_p8b), (True, False),
                 "a 25%-a-day roll passes and does not (line 745)", log)
    checks += 2
    return checks


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selftest", action="store_true",
                   help="run every guard and prove each one raises")
    a = p.parse_args(argv)
    if not a.selftest:
        p.error("nothing to do: pass --selftest")
    t0 = time.time()
    print(f"[{SPEC} selftest] backtest_framework.ledger")
    checks = run_selftest()
    print(f"[done] {checks} checks, {round(time.time() - t0, 2)}s -- every guard fired")
    return 0


if __name__ == "__main__":
    sys.exit(main())
