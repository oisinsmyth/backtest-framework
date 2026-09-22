"""D611 FUND MODEL SELFTEST -- every guard in `backtest_framework.ledger`'s fund model, fired.

    uv run python scripts/fund_model_selftest.py --selftest
    uv run python scripts/fund_model_selftest.py --table

NOTHING HERE READS DATA. The deposit's fund panel, its ETF quotes, its FX series and its P9
AUMs do not exist on disk (`docs/internal/DEPOSIT_INFRASTRUCTURE_TRACKER.md`), so every input
below is hand-typed from
`docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md`'s own examples. No file is
written, no fixture is opened, no strategy return is computed.

`--selftest` proves that each refusal in `ledger/funds.py`, `ledger/premium.py`,
`ledger/creations.py` and `ledger/non_us.py` RAISES on a real break -- an expense ratio that
was never sourced, a crossed quote, a minute at the settlement window, a third value of
`lag_c`, a negative `h1`, an FX rate struck on the day it is being used, a product whose index
month the document does not give. A guard that has never been seen to fire is a guard nobody
has tested (`CLAUDE.md`: "a self-test that cannot fail is worse than none").

`--table` prints the two tables the modules encode -- Section 3.1's six US funds and Section
3.1b's eight non-US products -- with every unsourced field shown as a dash, so that what is
MISSING is as visible as what is present.

DECLARED OUTPUTS. `REQUIRED_CHECKS` names the eleven blocks the selftest must run and the run
RAISES if one of them is missing from the log, rather than reporting a pass over a block that
silently did not execute.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")  # type: ignore[union-attr]

from backtest_framework.ledger.creations import (  # noqa: E402
    CreationError,
    create_flow,
    creation_term,
    delta_create,
    hedged_fraction,
    split,
)
from backtest_framework.ledger.funds import (  # noqa: E402
    BOIL,
    KOLD,
    US_FUNDS,
    FundModelError,
    gate_0b,
    inav,
)
from backtest_framework.ledger.non_us import (  # noqa: E402
    BETAPRO_HNU,
    NON_US_PRODUCTS,
    WT_3NGL,
    WT_3OIL,
    NonUsError,
    Restrike,
    aum_usd,
    delta_h,
    effective_leverage,
    index_month,
    product_value,
    q9,
)
from backtest_framework.ledger.premium import (  # noqa: E402
    Minute,
    PremiumError,
    PremiumWindowError,
    Quote,
    features,
    minute_feature,
    premium,
    stress,
)

#: The blocks this selftest promises. Checked against the log before it returns 0.
REQUIRED_CHECKS = (
    "[1] the fund table carries no invented fact",
    "[2] iNAV and its two day counts",
    "[3] Gate 0b",
    "[4] the premium reads the midpoint",
    "[5] the valid minute",
    "[6] the settlement-window guard",
    "[7] stress",
    "[8] the execution-day lag",
    "[9] the hedged fraction and the split",
    "[10] P9: leverage, FX and the index month",
    "[11] the restrike",
)

# Hand-typed inputs. ILLUSTRATIVE, not sourced: see the hand ledger's preamble.
NAV_PREV = 100.0
Y_CASH = 0.05
ER = 0.01
INAV_MINUTE = 25.0
P_HELD = 3.0
W_START = dt.datetime(2026, 9, 18, 14, 28)
DAY = dt.date(2026, 9, 18)


class SelftestFailure(AssertionError):
    """A declared check did not run, or a guard that must fire did not."""


def _expect_raise(
    thunk: Callable[[], Any], error: type[BaseException], what: str, log: Callable[[str], None]
) -> None:
    try:
        value = thunk()
    except error as exc:
        log(f"    RAISED on {what}: {str(exc).splitlines()[0][:96]}")
        return
    raise SelftestFailure(f"{what} did not raise {error.__name__}; it returned {value!r}")


def selftest() -> int:
    lines: list[str] = []

    def log(message: str) -> None:
        lines.append(message)
        print(message)

    log("D611 fund model selftest -- no data read, every input hand-typed from the deposit")

    log(REQUIRED_CHECKS[0])
    for fund in US_FUNDS.values():
        if fund.er is not None:
            raise SelftestFailure(f"{fund.name} carries an expense ratio nobody sourced: {fund.er}")
    log(f"    six funds, all er=None: {', '.join(US_FUNDS)}")
    _expect_raise(
        lambda: inav(NAV_PREV, 2, 0.0, Y_CASH, None), FundModelError, "an unsourced er", log
    )
    log(f"    L(L-1): BOIL {BOIL.rebalance_factor}, KOLD {KOLD.rebalance_factor}, "
        f"UNG {US_FUNDS['UNG'].rebalance_factor} (creations only)")

    log(REQUIRED_CHECKS[1])
    flat = inav(NAV_PREV, 2, 0.0, Y_CASH, ER)
    assert flat == NAV_PREV * (1 + (Y_CASH / 360 - ER / 365)), flat
    log(f"    zero move at y_cash 5.00%, er 1.00% (ILLUSTRATIVE): {flat!r}")
    log(f"    L=+2 r=+1%: {inav(NAV_PREV, 2, 0.01, Y_CASH, ER)!r}   "
        f"L=-2: {inav(NAV_PREV, -2, 0.01, Y_CASH, ER)!r}")
    _expect_raise(
        lambda: inav(0.0, 2, 0.0, Y_CASH, ER), FundModelError, "a zero prior NAV", log
    )

    log(REQUIRED_CHECKS[2])
    official = [1000.0] * 20
    passing = gate_0b([1000.2] * 19 + [1000.8], official)
    failing = gate_0b([1000.2] * 18 + [1000.8, 1000.8], official)
    assert passing.passes and not failing.passes
    log(f"    19 of 20 within 5 bp -> share {passing.share_within}, passes {passing.passes}; "
        f"18 of 20 -> {failing.share_within}, passes {failing.passes}")
    _expect_raise(lambda: gate_0b([], []), FundModelError, "an empty sample", log)
    _expect_raise(
        lambda: gate_0b([1.0, 2.0], [1.0]), FundModelError, "a length mismatch", log
    )

    log(REQUIRED_CHECKS[3])
    ts = dt.datetime(2026, 9, 18, 14, 20)
    same = {premium(Quote(25.02, 25.04, last, ts), INAV_MINUTE) for last in (25.02, 25.04, 25.10)}
    if len(same) != 1:
        raise SelftestFailure(f"the premium moved with the last trade: {same}")
    log(f"    three different last trades, one premium: {same.pop()!r}")
    _expect_raise(
        lambda: Quote(25.04, 25.02, 25.03, ts), PremiumError, "a crossed quote", log
    )
    _expect_raise(
        lambda: premium(Quote(25.02, 25.04, 25.03, ts), 0.0),
        PremiumError,
        "a zero iNAV denominator",
        log,
    )

    log(REQUIRED_CHECKS[4])
    # Distinct timestamps, because `features` also refuses a repeated minute and a break that
    # trips the wrong guard proves the wrong thing.
    ts21 = dt.datetime(2026, 9, 18, 14, 21)
    ts22 = dt.datetime(2026, 9, 18, 14, 22)
    fresh = Minute(ts, Quote(25.02, 25.04, 25.10, ts), INAV_MINUTE, 10.0, True, 100.0, 50.0)
    stale = Minute(ts21, Quote(25.02, 25.04, 25.10, ts21), INAV_MINUTE, 90.0, True, 100.0, 50.0)
    quiet = Minute(ts22, Quote(25.02, 25.04, 25.10, ts22), INAV_MINUTE, 10.0, False, 100.0, 50.0)
    if minute_feature(stale, INAV_MINUTE) is not None or minute_feature(quiet, INAV_MINUTE) is not None:
        raise SelftestFailure("an invalid minute returned a premium")
    log(f"    fresh -> {minute_feature(fresh, INAV_MINUTE)!r}; 90 s stale -> None; "
        f"no futures trade -> None (never 0.0)")
    _expect_raise(
        lambda: features([stale, quiet], w_start=W_START),
        PremiumError,
        "a day with no valid minute",
        log,
    )

    log(REQUIRED_CHECKS[5])
    at_window = Minute(
        W_START, Quote(25.02, 25.04, 25.10, W_START), INAV_MINUTE, 10.0, True, 100.0, 0.0
    )
    _expect_raise(
        lambda: features([fresh, at_window], w_start=W_START),
        PremiumWindowError,
        "a minute at W_start (line 201, decision D10)",
        log,
    )
    ok = features([fresh], w_start=W_START, trailing_volume_mean=400.0)
    log(f"    one valid minute before W_start: prem_twa {ok.prem_twa!r}, prem_frac "
        f"{ok.prem_frac!r}, vol_x {ok.vol_x!r}, sv_etf {ok.sv_etf!r}")

    log(REQUIRED_CHECKS[6])
    trailing = [
        (DAY - dt.timedelta(days=60 - i), 0.001 if i < 30 else 0.003) for i in range(60)
    ]
    log(f"    z of |prem_twa| = 0.004 against 60 prior days: {stress(0.004, trailing, day=DAY)!r}")
    _expect_raise(
        lambda: stress(0.004, trailing[1:] + [(DAY, 0.02)], day=DAY),
        PremiumError,
        "a trailing entry dated today",
        log,
    )
    _expect_raise(
        lambda: stress(0.004, trailing[:10], day=DAY),
        PremiumError,
        "a ten-day trailing window",
        log,
    )

    log(REQUIRED_CHECKS[7])
    realised = delta_create(6000000.0, 5600000.0, 25.0)
    log(f"    dCreate = (6,000,000 - 5,600,000) x 25.00 = {realised!r}")
    log(f"    lag_c=1 -> Q3_known {creation_term(1, realised, 99.0)!r}; "
        f"lag_c=0 -> forecast {creation_term(0, realised, 99.0)!r}")
    _expect_raise(
        lambda: creation_term(2, realised, 99.0), CreationError, "lag_c = 2", log
    )
    _expect_raise(
        lambda: creation_term(1, None, 99.0), CreationError, "lag_c = 1 with nothing known", log
    )

    log(REQUIRED_CHECKS[8])
    boil_flow = create_flow(BOIL.L, realised, BOIL.multiplier, P_HELD)
    kold_flow = create_flow(KOLD.L, realised, KOLD.multiplier, P_HELD)
    if not (boil_flow > 0 > kold_flow):
        raise SelftestFailure(f"the creation sign is wrong: BOIL {boil_flow}, KOLD {kold_flow}")
    log(f"    a $10m creation: BOIL {boil_flow!r} contracts, KOLD {kold_flow!r} "
        f"(the fund SELLS; the sign is L's)")
    h = hedged_fraction(1.0, 0.5, 0.0)
    window, intraday = split(h, boil_flow)
    log(f"    h(h0=1, h1=0.5, stress=0) = {h!r} -> window {window!r}, intraday {intraday!r}")
    log(f"    h at stress +2 = {hedged_fraction(1.0, 0.5, 2.0)!r} (non-increasing)")
    _expect_raise(
        lambda: hedged_fraction(1.0, -0.1, 0.0), CreationError, "h1 = -0.1 (line 472)", log
    )
    _expect_raise(
        lambda: hedged_fraction(1.0, 0.5, 0.0, g1=-0.1), CreationError, "g1 = -0.1", log
    )
    _expect_raise(
        lambda: hedged_fraction(40.0, 0.0, 0.0), CreationError, "a saturated logistic", log
    )
    _expect_raise(
        lambda: create_flow(2, realised, BOIL.multiplier, -37.63),
        CreationError,
        "a negative held price",
        log,
    )

    log(REQUIRED_CHECKS[9])
    measured = effective_leverage(140000000.0, 100000000.0, BETAPRO_HNU.stated_L)
    flagged = effective_leverage(None, 100000000.0, BETAPRO_HNU.stated_L)
    if flagged != (2.0, True):
        raise SelftestFailure(f"a missing notional did not flag: {flagged}")
    log(f"    HNU published notional / NAV -> {measured}; missing -> {flagged} (D19's flag)")
    log(f"    dH(+3x, $50m, +4%) = {delta_h(50000000.0, 3.0, 0.04)!r}; "
        f"(-3x) = {delta_h(50000000.0, -3.0, 0.04)!r}")
    log(f"    Q9 at n9=0.25 into NG contracts at $3.00: "
        f"{q9(36000000.0, 0.25, 10000.0, P_HELD)!r}")
    rates_ = {"2026-09-16": 0.73, "2026-09-17": 0.74, "2026-09-18": 0.75}
    log(f"    C$175m at the prior settlement: {aum_usd(175000000.0, rates_, DAY)!r}")
    _expect_raise(
        lambda: aum_usd(175000000.0, {"2026-09-18": 0.75}, DAY),
        NonUsError,
        "an FX rate struck on the day itself (line 288)",
        log,
    )
    curve = ["NGV6", "NGX6", "NGZ6"]
    log(f"    index month: HNU {index_month(BETAPRO_HNU, curve)}, "
        f"3NGL {index_month(WT_3NGL, curve)}")
    _expect_raise(
        lambda: index_month(WT_3OIL, curve), NonUsError, "a product with no index rule", log
    )
    _expect_raise(
        lambda: q9(1.0, 1.5, 10000.0, P_HELD), NonUsError, "n9 outside [0, 1]", log
    )

    log(REQUIRED_CHECKS[10])
    rest = Restrike(threshold=0.20, L=3)
    quiet_value = product_value(100.0, 3, -0.065)
    fired_value = product_value(100.0, 3, -0.067)
    if rest.check(quiet_value, 100.0) is not None:
        raise SelftestFailure("-6.5% fired a restrike and must not")
    event = rest.check(fired_value, 100.0)
    if event is None:
        raise SelftestFailure("-6.7% did not fire a restrike and must")
    log(f"    trigger {rest.underlying_trigger!r} of the underlying at 20% of the product")
    log(f"    -6.5% -> value {quiet_value!r}, no event; -6.7% -> value {fired_value!r}, "
        f"drawdown {event.drawdown!r}, new reset {event.new_reset_level!r}")
    _expect_raise(
        lambda: rest.check(80.0, 0.0), NonUsError, "a zero reset level", log
    )

    text = "\n".join(lines)
    missing = [check for check in REQUIRED_CHECKS if check not in text]
    if missing:
        raise SelftestFailure(f"declared checks that did not run: {missing}")
    log("  OK -- every guard fired on its break. No data was read and no file was written.")
    return 0


def table() -> int:
    """Print the two encoded tables, with every unsourced field as a dash."""
    print("Section 3.1, the six US funds (multipliers from data/futures_contract_specs.json)")
    print(f"  {'fund':6} {'L':>3} {'L(L-1)':>7} {'root':5} {'multiplier':>11} {'er':>6}")
    for fund in US_FUNDS.values():
        er = "-" if fund.er is None else f"{fund.er:.4f}"
        print(
            f"  {fund.name:6} {fund.L:>3} {fund.rebalance_factor:>7} {fund.underlying_root:5} "
            f"{fund.multiplier:>11.1f} {er:>6}"
        )
    print()
    print("Section 3.1b, the eight non-US products -- ALL FIGURES INDICATIVE (line 74)")
    print(f"  {'product':8} {'issuer':11} {'L':>3} {'ccy':4} {'index month':12} {'restrike':>8}")
    for p in NON_US_PRODUCTS.values():
        rule = p.index_month_rule or "-"
        restrike = "-" if p.restrike_threshold is None else f"{p.restrike_threshold:.2f}"
        print(f"  {p.name:8} {p.issuer:11} {p.stated_L:>3} {p.currency:4} {rule:12} {restrike:>8}")
    print()
    print("A dash is a fact the deposit marks 'to source' or 'verify'. Nothing fills it here.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--selftest", action="store_true", help="fire every guard and report")
    p.add_argument("--table", action="store_true", help="print the fund and product tables")
    a = p.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.table:
        return table()
    p.error("one of --selftest or --table is required")
    return 2  # unreachable; argparse exits


if __name__ == "__main__":
    raise SystemExit(main())
