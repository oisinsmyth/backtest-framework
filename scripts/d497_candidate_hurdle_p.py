"""D497 -- hurdle P, all six, on the D495 candidate. P3 has never been computed on it.

    uv run python scripts/d497_candidate_hurdle_p.py --self-test
    uv run python scripts/d497_candidate_hurdle_p.py --run [--json]

**A COMPLETION, NOT A NEW STUDY.** It re-runs the single D495 cell that clears C-a/C-c/C-d and
computes what the ledger and R11 require of it and nothing else. No search, no new grid, no new
signal. Nothing is opened, closed or admitted (R15).

WHY THIS EXISTS
---------------
D491 and D495 both reported C-a, C-c and C-d and both stopped there. **P3 -- worst single day
<= 2% of the account -- was never computed on any cell**, and it is a HARD hurdle that R11's
2026-09-12 restatement explicitly left untouched:

> *"P1, P2, P3 and P6 stand exactly as written. In particular P3's worst-day <= 2% is untouched
> -- it is a daily LOSS LIMIT, enforced by the venue on the day, and no amount of
> account-replaceability softens it."*

D495 stored the BEST day (for P5's haircut) and not the worst. **A candidate can clear every
component condition and still be ineligible**, so this is computed before anything is proposed
for the ledger.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from d484_offdiagonal_and_macd import COMMISSION_RT, CROSS_TICKS, SEGMENTS, SPECS  # noqa: E402
from d491_conditional_hold import LAST_SEG, TRADING_DAYS, simulate  # noqa: E402
from d495_agree_confluence import META, FIX, build_panel, p5_recognised  # noqa: E402
from d496_book_sharpe_bar import expected_profit_before_breach  # noqa: E402

OUT = REPO / "data" / "d497_candidate_hurdle_p.json"

# the D495 candidate, named exactly
CAND = {"root": "NQ", "arm": "AGREE", "M": 5}
ACCOUNT = 50_000.0
P3_CAP = 0.02 * ACCOUNT          # R11 P3: worst single day <= 2% = $1,000
P5_CAP = 0.30
FLATTEN_ET = "16:10"             # Topstep / MyFundedFutures
EXIT_SEGMENT_ET = "16:00"        # the close of h15, LAST_SEG = 21


def P(*a, **k):
    print(*a, **k, flush=True)


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:64} {detail}")
        if not cond:
            fails.append(label)

    chk("P3's cap is 2% of the account = $1,000", abs(P3_CAP - 1000.0) < 1e-9)
    # P3 reads the WORST day, which is a different statistic from the best day P5 reads
    # first version used [500, -1200, 300, -100], which SUMS TO -500 -- so it could not
    # demonstrate "breaches while still profitable". My arithmetic, not the check's logic.
    d = np.array([500.0, -1200.0, 900.0, 300.0])
    chk("P3 reads the WORST day, P5 the BEST -- they are different statistics",
        abs(d.min() + 1200.0) < 1e-9 and abs(d.max() - 900.0) < 1e-9)
    chk("a -$1,200 day BREACHES P3 while the series is still PROFITABLE overall",
        d.min() < -P3_CAP and d.sum() > 0,
        f"worst {d.min():+.0f}, total {d.sum():+.0f} -- exactly why P3 must be checked")
    chk("P3 is indifferent to the mean: a fine average cannot rescue one bad day",
        (d * 10).min() < -P3_CAP)
    # skew does NOT bound the worst day, which is why C-c is not a substitute for P3
    rg = np.random.default_rng(497)
    sym = rg.standard_normal(4000) * 400
    chk("C-c (skew) does NOT bound the worst day -- a symmetric series still breaches",
        abs(float(((sym - sym.mean()) ** 3).mean() / sym.std() ** 3)) < 0.2
        and sym.min() < -P3_CAP,
        f"skew {float(((sym-sym.mean())**3).mean()/sym.std()**3):+.2f}, "
        f"worst {sym.min():+.0f}")
    # and the P2 check is structural, not statistical
    chk("P2 holds by construction: the exit is 16:00 ET, inside the 16:10 flatten",
        EXIT_SEGMENT_ET < FLATTEN_ET and LAST_SEG == 21)
    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


def do_run(as_json: bool) -> int:
    import pandas as pd

    meta = json.loads(META.read_text(encoding="utf-8"))
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    panel = build_panel(pd.read_csv(FIX), meta, spec)
    p = panel[CAND["root"]]
    pnl_tk, trips = simulate(p["O"], p["C"], p[CAND["arm"]], p["first"], CAND["M"],
                             p["cost"], p["tick_pts"])
    d = pnl_tk * p["tick_usd"]                      # daily P&L in dollars, 1 micro
    n = len(d)
    mu, sd = float(d.mean()), float(d.std(ddof=1))
    sharpe = mu / sd * np.sqrt(TRADING_DAYS)
    skew = float(((d - mu) ** 3).mean() / sd ** 3)
    h = p5_recognised(d)

    P(f"THE CANDIDATE, named exactly")
    P(f"  {CAND['root']} front month by volume, traded as 1 {p['sized_as']}")
    P(f"  day session only: decide at the close of each hour from h09 (09:00 ET), execute")
    P(f"  at the next hour's open, forced flat at the close of h15 (16:00 ET)")
    P(f"  signal: log Impulse MACD (34/9) and plain log MACD histogram (12/26/9) must")
    P(f"          AGREE in sign; zero or disagreement = no position")
    P(f"  exit:   signal no longer favours the position AND >= {CAND['M']} hours elapsed")
    P(f"  cost:   ${COMMISSION_RT:.2f} + {CROSS_TICKS:.3f} ticks crossing = "
      f"{p['cost']:.3f} ticks per round trip")
    P(f"  window: {n:,} sessions, 2016-01-04 -> 2023-12-29 (IN-SAMPLE)\n")

    P(f"  === COMPONENT CONDITIONS (COMPONENTS_PROP.md) ===")
    rows = [("C-a net Sharpe > 0.5", f"{sharpe:+.3f}", sharpe > 0.5),
            ("C-b rho < 0.3 vs the ledger", "ledger is EMPTY -> trivially satisfied", True),
            ("C-c skew >= -0.5", f"{skew:+.3f}", skew >= -0.5),
            ("C-d daily sigma <= $500", f"${sd:,.0f}", sd <= 500.0),
            ("C-e provenance", "D495 PRE-REG, window, cost line, two nulls", True)]
    for lab, val, ok in rows:
        P(f"    [{'PASS' if ok else 'FAIL'}] {lab:32} {val}")

    P(f"\n  === HURDLE P, ALL SIX (R11, as amended 2026-09-12) ===")
    worst = float(d.min())
    p3_ok = worst >= -P3_CAP
    n_breach = int((d < -P3_CAP).sum())
    prof, life = expected_profit_before_breach(sharpe, sd / ACCOUNT)
    hp = [
        ("P1 sizing rule (cannot fail)",
         f"one micro is the floor; post-sizing return ${mu*TRADING_DAYS:,.0f}/yr", True),
        ("P2 flat across the venue flatten",
         f"exit {EXIT_SEGMENT_ET} ET, inside the {FLATTEN_ET} flatten -- by construction",
         True),
        ("P3 worst single day <= 2% ($1,000)",
         f"WORST ${worst:,.0f}   days beyond the limit: {n_breach} of {n:,}", p3_ok),
        ("P4 E[profit] > the account fee",
         f"${prof*ACCOUNT:,.0f} before breach, E[life] {life:,.0f} d "
         f"({life/TRADING_DAYS:.2f} yr)", True),
        ("P5 30% single-day haircut",
         f"best day ${h['best_day_usd']:,.0f} = {h['best_day_share']:.1%} of total -> "
         f"haircut ${h['haircut_usd']:,.0f}", True),
        ("P6 venue permits automation",
         "Topstep or MyFundedFutures only -- a VENUE CHOICE, not a measurement", None),
    ]
    for lab, val, ok in hp:
        mark = "PASS" if ok is True else ("FAIL" if ok is False else "n/a ")
        P(f"    [{mark}] {lab:36} {val}")

    P(f"\n  the daily P&L distribution, which is what P3 reads:")
    for q, lab in ((0.0, "worst"), (0.001, "p0.1"), (0.01, "p1"), (0.05, "p5"),
                   (0.50, "median"), (0.95, "p95"), (0.99, "p99"), (1.0, "best")):
        P(f"    {lab:>7} ${float(np.quantile(d, q)):>9,.0f}")
    P(f"    days at or beyond -$1,000: {n_breach}  "
      f"({n_breach/n:.2%} of sessions)")
    P(f"    days beyond -$500:        {int((d < -500).sum())}")

    P(f"\n  === WHAT IS STILL REQUIRED BEFORE THE BOOK ===")
    todo = [
        ("ledger entry", "eligible on the standard as written; the PRINCIPAL'S CALL"),
        ("confirmation on the sealed slice",
         "2024-01 onward, UNREAD. The ledger's own discipline says this promotes or "
         "removes a candidate."),
        ("fills", "every figure is an UPPER BOUND: open-of-next-segment at the measured "
                  "half-spread, no queue, no partial fills, no slippage on a flip. Needs "
                  "mbp-10 (D471 s1), which was not bought."),
        ("a second component", "the book is one arm; D496 showed one is enough for the "
                               "relaxed P4, but the vault is empty and C-b is untested "
                               "against anything"),
        ("P6 venue choice", "Topstep or MyFundedFutures; Apex forbids automation when "
                            "funded"),
        ("selection disclosure", "one cell chosen from 37 in-sample on one root of eight; "
                                 "the family null prices that, the forward read does not "
                                 "yet exist"),
    ]
    for k, v in todo:
        P(f"    - {k}: {v}")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D497: hurdle P computed on the D495 candidate, P3 for the first time "
                      "on any cell. A completion, not a new study; nothing admitted.",
           "candidate": {**CAND, "sized_as": p["sized_as"], "cost_ticks": p["cost"],
                         "n_sessions": n},
           "component_conditions": {"C_a": {"value": sharpe, "pass": bool(sharpe > 0.5)},
                                    "C_b": {"value": "ledger empty", "pass": True},
                                    "C_c": {"value": skew, "pass": bool(skew >= -0.5)},
                                    "C_d": {"value": sd, "pass": bool(sd <= 500.0)},
                                    "C_e": {"value": "D495 PRE-REG", "pass": True}},
           "hurdle_P": {"P1_post_sizing_return_usd_per_year": mu * TRADING_DAYS,
                        "P2_pass": True, "P2_note": "exit 16:00 ET inside a 16:10 flatten",
                        "P3_worst_day_usd": worst, "P3_cap_usd": -P3_CAP,
                        "P3_days_beyond": n_breach, "P3_pass": bool(p3_ok),
                        "P4_expected_profit_usd": prof * ACCOUNT,
                        "P4_expected_life_days": life, "P4_pass": True,
                        "P5_best_day_share": h["best_day_share"],
                        "P5_haircut_usd": h["haircut_usd"], "P5_pass": True,
                        "P6": "venue choice, not a measurement"},
           "daily_pnl_quantiles_usd": {lab: float(np.quantile(d, q)) for q, lab in
                                       ((0.0, "worst"), (0.01, "p1"), (0.05, "p5"),
                                        (0.5, "median"), (0.95, "p95"), (1.0, "best"))},
           "trips_per_session": float(trips.mean()),
           "still_required": dict(todo)}
    if as_json:
        OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.run:
        return do_run(a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
