"""`backtest_framework.ledger.netting` -- 8A.2's swap-dealer calibration and its clocks (D610).

Covers the settlement flow ledger's required unit tests 41 (line 747), 43 (line 749) and 44
(line 750). The hand-worked case for number 42 is in
`tests/golden/test_ledger_flows_ledger.py`.

Required unit test 41's rule is not invented here: `cot_usable_from` re-implements
`scripts/fetch_cftc_cot.py:397 release_date_of` (the Friday of the report's week, not a flat
+3 days), and this file PINS the two against each other by compiling that one function out of
the runner's committed source. It is compiled rather than imported for D606's reason -- a
one-shot runner's module body is written to do work, not to be imported -- and read as bytes
with CRLF normalised first, per D550.

Offline: the COT fixture is never read; only the runner's source text is.
"""

from __future__ import annotations

import ast
import datetime as dt
from pathlib import Path

import numpy as np
import pytest

from backtest_framework.ledger.flows import LedgerError
from backtest_framework.ledger.netting import (
    COT_RELEASE_WEEKDAY,
    COT_TUESDAY_CONVENTION_FROM,
    FundExposure,
    consistency_flag,
    cot_usable_from,
    fit_lambda,
    swap_exposure_predictor,
    swap_record_time,
)

REPO = Path(__file__).resolve().parents[2]
COT_FETCHER = REPO / "scripts" / "fetch_cftc_cot.py"


def _release_date_of_from_the_runner():
    """Compile ONLY `release_date_of` out of the fetcher, into a namespace holding `date`,
    `timedelta` and the two module constants it reads.

    D606: importing a runner runs its module body. This one builds a rate limiter and a
    Socrata client at import; compiling the single FunctionDef keeps the pin on the runner's
    own committed bytes without any of that.
    """
    src = COT_FETCHER.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    tree = ast.parse(src)
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "release_date_of"]
    assert len(fns) == 1, f"expected exactly one release_date_of in {COT_FETCHER.name}, got {len(fns)}"
    consts = {n.targets[0].id: ast.literal_eval(n.value)
              for n in tree.body
              if isinstance(n, ast.Assign)
              and isinstance(n.targets[0], ast.Name)
              and n.targets[0].id in ("TUESDAY_CONVENTION_FROM", "RELEASE_WEEKDAY")}
    ns: dict[str, object] = {"date": dt.date, "timedelta": dt.timedelta, **consts}
    exec(compile(ast.Module(body=fns, type_ignores=[]), str(COT_FETCHER), "exec"), ns)
    return ns["release_date_of"], consts


# ------------------------------------------------------------------ required unit test 41


def test_ledger_41_a_cot_week_is_usable_only_from_its_friday_release() -> None:
    """Line 747: "COT availability: a weekly record is usable only at or after its Friday
    release timestamp."

    Line 128 is the rule -- "COT data is usable only after its Friday release" -- and R9 is
    why it matters: keying on `report_date` reads Tuesday's positions on Tuesday and is three
    days of look-ahead in a conditioning variable.
    """
    runner_fn, consts = _release_date_of_from_the_runner()
    assert consts["RELEASE_WEEKDAY"] == COT_RELEASE_WEEKDAY == 4
    assert consts["TUESDAY_CONVENTION_FROM"] == COT_TUESDAY_CONVENTION_FROM.isoformat()

    # An ordinary Tuesday survey releases on that week's Friday, three days later.
    tue = dt.date(2026, 3, 17)
    assert tue.weekday() == 1
    assert cot_usable_from(tue) == dt.date(2026, 3, 20)
    assert cot_usable_from(tue).weekday() == COT_RELEASE_WEEKDAY

    # The holiday-shift case the fetcher measured: 2007-01-03 is a WEDNESDAY because
    # 2007-01-02 was the National Day of Mourning for President Ford. A flat +3 days would
    # put that release on a Saturday; the Friday-of-the-week rule puts it on 2007-01-05.
    wed = dt.date(2007, 1, 3)
    assert wed.weekday() == 2
    assert cot_usable_from(wed) == dt.date(2007, 1, 5)
    assert wed + dt.timedelta(days=3) == dt.date(2007, 1, 6)  # a Saturday, and wrong

    # A report dated ON a Friday pushes to the FOLLOWING Friday: a report cannot be published
    # before it is surveyed, and erring late is the only safe direction.
    fri = dt.date(1997, 12, 19)
    assert fri.weekday() == 4
    assert cot_usable_from(fri) == dt.date(1997, 12, 26)

    # THE PIN. The library agrees with the runner on every report date across thirty years.
    d = dt.date(1993, 1, 1)
    checked = 0
    while d < dt.date(2027, 1, 1):
        assert cot_usable_from(d).isoformat() == runner_fn(d.isoformat())
        assert cot_usable_from(d) > d
        d += dt.timedelta(days=1)
        checked += 1
    assert checked > 12_000

    # Before the weekly convention existed the runner returns "" and this function RAISES,
    # because a function that must return a date cannot say "we do not know" any other way.
    assert runner_fn("1986-05-16") == ""
    with pytest.raises(LedgerError, match="no weekly Tuesday survey schedule"):
        cot_usable_from("1986-05-16")
    with pytest.raises(LedgerError, match="not an ISO date"):
        cot_usable_from("not-a-date")
    # Strings and datetimes are accepted and agree with the date form.
    assert cot_usable_from("2026-03-17") == cot_usable_from(tue)
    assert cot_usable_from(dt.datetime(2026, 3, 17, 15, 30)) == cot_usable_from(tue)


# ------------------------------------------------------------------ required unit test 43


def test_ledger_43_the_swap_predictor_never_sees_futures_held_exposure() -> None:
    """Line 749: "The swap-exposure predictor includes only swap-routed exposure (1 - f_fut)
    and P9, never futures-held exposure."

    Line 495 is the formula. The failure this guards is not a crash: including futures-held
    exposure inflates DeltaSX on exactly the high-f_fut funds, biases lambda DOWN and the
    implied netting fraction UP -- towards the conclusion that quietly removes P2.
    """
    funds = [
        FundExposure("BOIL", "us_fund", 100e6, f_fut=0.75),
        FundExposure("KOLD", "us_fund", -40e6, f_fut=0.50),
        FundExposure("3NGL", "p9", 8e6),
    ]
    # 0.25 x 100m + 0.50 x -40m + 8m = 25m - 20m + 8m = 13m, exact (all binary fractions).
    assert swap_exposure_predictor(funds) == 13e6
    assert swap_exposure_predictor(list(reversed(funds))) == 13e6  # fsum: order independent

    # A fund wholly in futures contributes nothing at all, which is the point of (1 - f_fut).
    assert swap_exposure_predictor([FundExposure("UCO", "us_fund", 1e9, f_fut=1.0)]) == 0.0

    with pytest.raises(LedgerError, match="NEVER futures-held"):
        swap_exposure_predictor(funds + [FundExposure("SCO", "us_fund", 5e6, f_fut=0.2,
                                                      futures_held_change=1e6)])
    # Even a zero futures-held term raises: the field's presence is the defect, not its size.
    with pytest.raises(LedgerError, match="NEVER futures-held"):
        swap_exposure_predictor([FundExposure("SCO", "us_fund", 5e6, f_fut=0.2,
                                              futures_held_change=0.0)])
    with pytest.raises(LedgerError, match="carries no f_fut"):
        swap_exposure_predictor([FundExposure("SCO", "us_fund", 5e6)])
    with pytest.raises(LedgerError, match="p9 product and carries"):
        swap_exposure_predictor([FundExposure("3NGL", "p9", 5e6, f_fut=0.2)])
    with pytest.raises(LedgerError, match="exactly two groups"):
        swap_exposure_predictor([FundExposure("X", "swap_dealer", 5e6)])
    with pytest.raises(LedgerError, match="appears twice"):
        swap_exposure_predictor([FundExposure("BOIL", "us_fund", 1.0, f_fut=0.5),
                                 FundExposure("BOIL", "us_fund", 2.0, f_fut=0.5)])
    with pytest.raises(LedgerError, match="no funds"):
        swap_exposure_predictor([])


# ------------------------------------------------------------------ required unit test 44


def test_ledger_44_swap_records_are_keyed_on_dissemination_not_execution() -> None:
    """Line 750: "Swap dissemination records are keyed on dissemination time, not execution
    time, for any predictive use." Line 504 aggregates "by day and time of dissemination".

    Section 0 item 6 is the reason: "Everything used at t0 must be computable from data
    strictly available at the t0 bar close." Execution time is not available to anyone outside
    the trade.
    """
    exec_ts = dt.datetime(2026, 3, 17, 11, 4, 12, tzinfo=dt.timezone.utc)
    diss_ts = dt.datetime(2026, 3, 17, 11, 19, 3, tzinfo=dt.timezone.utc)
    assert swap_record_time(exec_ts, diss_ts) is diss_ts
    # Equal timestamps are permitted: a same-instant dissemination is a fast report, not a
    # corrupt row.
    assert swap_record_time(exec_ts, exec_ts) is exec_ts

    with pytest.raises(LedgerError, match="precedes execution"):
        swap_record_time(diss_ts, exec_ts)
    with pytest.raises(LedgerError, match="timezone-aware"):
        swap_record_time(exec_ts, dt.datetime(2026, 3, 17, 11, 19, 3))
    with pytest.raises(LedgerError, match="must be a datetime"):
        swap_record_time(exec_ts, "2026-03-17T11:19:03Z")  # type: ignore[arg-type]

    # Naive-to-naive is accepted and ordered the same way, so a study that has not yet chosen
    # a timezone is not blocked -- only a MIXED pair is.
    a = dt.datetime(2026, 3, 17, 11, 4)
    b = dt.datetime(2026, 3, 17, 11, 19)
    assert swap_record_time(a, b) is b
    with pytest.raises(LedgerError, match="precedes execution"):
        swap_record_time(b, a)


# --------------------------------------------------------------------- the lambda fit


def test_fit_lambda_refuses_what_cannot_be_identified() -> None:
    """The fit is one slope through the origin; a design that does not pin it is refused."""
    with pytest.raises(LedgerError, match="cannot be fitted"):
        fit_lambda([1.0, 2.0, 3.0], [0.0, 0.0, 0.0])
    with pytest.raises(LedgerError, match="One week is one paired observation"):
        fit_lambda([1.0, 2.0], [1.0])
    with pytest.raises(LedgerError, match="week"):
        fit_lambda([1.0], [1.0])
    with pytest.raises(LedgerError, match="must be finite"):
        fit_lambda([1.0, float("nan")], [1.0, 2.0])
    # A design whose Sum x^2 underflows pins nothing, and the SE overflows to infinity rather
    # than reporting it. Refused, because line 498 would carry it forward as a PRIOR.
    with np.errstate(over="ignore"):  # the overflow is the point of this case
        with pytest.raises(LedgerError, match="overflowed"):
            fit_lambda([1e6, -1e6, 1e6], [1e-150, 2e-150, 3e-150])

    # A negative relationship projects to 0: the dealer book moved the other way, which under
    # line 496 reads as complete internal netting rather than as a negative pass-through.
    neg = fit_lambda([-2.0, -3.0, -1.0, -2.0, -4.0], [1.0, 1.0, 1.0, 1.0, 2.0])
    assert neg.lam_unconstrained == -2.0
    assert neg.lam == 0.0
    assert neg.clipped is True


def test_consistency_flag_reports_and_never_resolves() -> None:
    """Line 499: "Neither estimate overrides the other automatically." It returns a bool."""
    assert consistency_flag(n_hat=0.25, se_n=0.1, lam=0.75, se_lam=0.1) is False
    assert consistency_flag(n_hat=1.0, se_n=0.25, lam=0.75, se_lam=0.25) is True
    # Perfect agreement never flags, whatever the standard errors.
    assert consistency_flag(n_hat=0.4, se_n=0.0, lam=0.6, se_lam=0.0) is False
    # ... and with zero SEs on both sides, any disagreement at all does.
    assert consistency_flag(n_hat=0.41, se_n=0.0, lam=0.6, se_lam=0.0) is True
    # Wide SEs absorb a large disagreement, which is line 500's "lambda is expected to be
    # noisy. That's why it's used as a prior, not as a replacement."
    assert consistency_flag(n_hat=1.0, se_n=0.5, lam=0.0, se_lam=0.5) is False
    for bad in (-0.01, 1.01):
        with pytest.raises(LedgerError, match="must lie in"):
            consistency_flag(n_hat=bad, se_n=0.1, lam=0.5, se_lam=0.1)
        with pytest.raises(LedgerError, match="must lie in"):
            consistency_flag(n_hat=0.5, se_n=0.1, lam=bad, se_lam=0.1)
    with pytest.raises(LedgerError, match="non-negative"):
        consistency_flag(n_hat=0.5, se_n=-0.1, lam=0.5, se_lam=0.1)
