"""D505 -- what a Sharpe-0.7 strategy's year SHOULD look like, and what MFFU actually pays.

    uv run python scripts/d505_yearly_expectation_and_payout.py --self-test
    uv run python scripts/d505_yearly_expectation_and_payout.py --run [--json]

**An ANALYSIS of committed numbers, not a study.** No fixture is read, no signal is computed, no
parameter is chosen. It reads `data/d504_arm_full_history.json` and runs D386's published-rules
lifecycle model at the arm's measured Sharpe and its FORCED size. Nothing admitted (R15).

WHY IT EXISTS
-------------
The principal, on D504's yearly table:

> *"Not sure I am too happy about this result? Would you not expect the yearly profit break down
> to at minimum have only one negative and should be close to zero? Am I expecting too much?"*

Two separable questions -- the MAGNITUDE of the negative years and their COUNT -- plus one I owe
an answer to because my own economics were wrong: what the rules actually pay.

AND A CORRECTION THIS RUNNER EXISTS TO MAKE
-------------------------------------------
D503 s9d and D504 s5 reported "+$21,935 net of fees, 4.4%/yr" by summing the strategy's realised
P&L and subtracting one account fee per breach. **That is an upper bound on a quantity the rules
do not let you have.** MFFU Rapid EOD requires a $3,000 EVALUATION target first, then funds you at
zero with a $2,000 safety net you may not withdraw below, 5 qualifying days at >= $150 each, and a
$500 minimum payout -- all against a $2,000 trailing drawdown. D386 already models every one of
those, and its answer is `V` = expected dollars PAID OUT minus fees, per evaluation purchased.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from math import comb, erf, sqrt
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

SRC = REPO / "data" / "d504_arm_full_history.json"
OUT = REPO / "data" / "d505_yearly_expectation_and_payout.json"
ACCOUNT = 50_000.0
VOL_GRID = (60.0, 75.0, 100.0, 125.0, 150.0, 185.0, 233.0, 300.0, 386.0, 500.0)
N_PATHS = 15_000
DAYS = 750


def P(*a, **k):
    print(*a, **k, flush=True)


def load_d386():
    """D386 must be registered in sys.modules before exec: it uses a frozen dataclass, whose
    field introspection looks the module up by name and fails with a bare module_from_spec."""
    s = importlib.util.spec_from_file_location("d386", REPO / "scripts"
                                               / "d386_full_lifecycle.py")
    m = importlib.util.module_from_spec(s)
    sys.modules["d386"] = m
    s.loader.exec_module(m)
    return m


def Phi(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def p_year_negative(sharpe: float) -> float:
    """P(a calendar year's return < 0) when the annual return ~ N(S*sigma_a, sigma_a)."""
    return 1.0 - Phi(sharpe)


def p_at_least_k_negative(n_years: int, sharpe: float, k: int) -> float:
    p = p_year_negative(sharpe)
    return float(sum(comb(n_years, j) * p ** j * (1 - p) ** (n_years - j)
                     for j in range(k, n_years + 1)))


def sharpe_for_expected_negatives(n_years: int, target: float) -> float:
    """The Sharpe at which the EXPECTED count of negative years equals `target`."""
    lo, hi = 0.0, 6.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if n_years * p_year_negative(mid) > target:
            lo = mid
        else:
            hi = mid
    return hi


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:62} {detail}")
        if not cond:
            fails.append(label)

    chk("a Sharpe of 0 makes half of all years negative",
        abs(p_year_negative(0.0) - 0.5) < 1e-12, f"{p_year_negative(0.0):.4f}")
    chk("Sharpe 1 -> ~15.9% of years negative (the standard normal tail)",
        abs(p_year_negative(1.0) - 0.158655) < 1e-5, f"{p_year_negative(1.0):.6f}")
    chk("Sharpe 2 -> ~2.3%", abs(p_year_negative(2.0) - 0.0227501) < 1e-6,
        f"{p_year_negative(2.0):.6f}")
    chk("[X] a HIGHER Sharpe cannot make negative years more likely",
        p_year_negative(1.5) < p_year_negative(0.7))

    chk("the binomial tail at k=0 is exactly 1",
        abs(p_at_least_k_negative(11, 0.7, 0) - 1.0) < 1e-12)
    chk("P(>= 11 of 11 negative) = p^11",
        abs(p_at_least_k_negative(11, 0.7, 11) - p_year_negative(0.7) ** 11) < 1e-15)
    chk("the tail is monotone decreasing in k",
        all(p_at_least_k_negative(11, 0.7, k) >= p_at_least_k_negative(11, 0.7, k + 1)
            for k in range(11)))
    chk("[X] a 5-of-11 tail at Sharpe 0.7 is NOT significant, and at Sharpe 2 it is",
        p_at_least_k_negative(11, 0.7, 5) > 0.05
        and p_at_least_k_negative(11, 2.0, 5) < 0.001,
        f"{p_at_least_k_negative(11, 0.7, 5):.3f} vs "
        f"{p_at_least_k_negative(11, 2.0, 5):.2e}")

    s1 = sharpe_for_expected_negatives(11, 1.0)
    chk("the inversion round-trips: 11 x P(neg | S) = 1.0 at the returned S",
        abs(11 * p_year_negative(s1) - 1.0) < 1e-6, f"S={s1:.4f}")
    chk("a tighter target needs a HIGHER Sharpe",
        sharpe_for_expected_negatives(11, 0.5) > s1,
        f"{sharpe_for_expected_negatives(11, 0.5):.3f} > {s1:.3f}")
    chk("[X] the inversion is not a constant -- it moves with the horizon",
        abs(sharpe_for_expected_negatives(11, 1.0)
            - sharpe_for_expected_negatives(30, 1.0)) > 0.2)

    # --- D386 loads, and its MFFU plan carries the rules this analysis turns on --------------
    m = load_d386()
    mffu = [p for p in m.PLANS if p.firm.startswith("MFFU") and p.size == 50000
            and "EOD" in p.firm][0]
    chk("D386's MFFU 50K EOD plan is the one BOOK_PROP names",
        mffu.fee_eval == 209.0 and mffu.target == 3000.0 and mffu.dd_fund == 2000.0,
        f"fee ${mffu.fee_eval:.0f}, target ${mffu.target:.0f}, dd ${mffu.dd_fund:.0f}")
    chk("and it carries the payout gates my earlier economics ignored",
        mffu.safety_net == 2000.0 and mffu.qual_threshold == 150.0 and mffu.qual_days == 5
        and mffu.min_payout == 500.0,
        f"safety ${mffu.safety_net:.0f}, qual ${mffu.qual_threshold:.0f}x{mffu.qual_days}, "
        f"min payout ${mffu.min_payout:.0f}")
    r0 = m.simulate(mffu, 0.0, 233.0, n_paths=3000, days=DAYS)
    rp = m.simulate(mffu, 1.0, 233.0, n_paths=3000, days=DAYS)
    chk("V rises with Sharpe at a fixed size", rp["V"] > r0["V"],
        f"V(S=0) ${r0['V']:.0f} -> V(S=1) ${rp['V']:.0f}")
    chk("[X] a zero-edge account still pays its fee, so V(S=0) is well below the gross payout",
        r0["V"] < r0["paid_mean"], f"V ${r0['V']:.0f} < paid ${r0['paid_mean']:.0f}")
    chk("P(paid) <= P(pass the evaluation) -- you cannot be paid without being funded",
        rp["p_paid"] <= rp["p_pass"] + 1e-12,
        f"{rp['p_paid']:.3f} <= {rp['p_pass']:.3f}")

    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


def do_run(as_json: bool) -> int:
    a = json.loads(SRC.read_text(encoding="utf-8"))
    py, live = a["per_year"], a["usable_years"]
    S = a["overall_usable"]["sharpe"]
    vol = a["overall_usable"]["daily_sigma_usd"]
    n = len(live)

    P("D505 -- what a Sharpe-0.7 year SHOULD look like, and what MFFU actually pays\n")

    P("=== 1. THE NEGATIVE YEARS, IN MONEY AND AS A SHARE OF THE ACCOUNT ===")
    P("     year      total$    % of $50k")
    neg, pos = [], []
    for y in live:
        t = py[y]["total_usd"]
        (neg if t < 0 else pos).append(t)
        P(f"     {y}{t:>12,.0f}{t / ACCOUNT:>13.2%}" + ("   <- negative" if t < 0 else ""))
    P(f"\n  the {len(neg)} negative years together: ${sum(neg):,.0f} = "
      f"{sum(neg) / ACCOUNT:+.2%} of the account")
    P(f"  the {len(pos)} positive years together: ${sum(pos):,.0f} = "
      f"{sum(pos) / ACCOUNT:+.2%}")
    P(f"  WORST year ${min(neg):,.0f} = {min(neg) / ACCOUNT:.2%}   "
      f"BEST ${max(pos):,.0f} = {max(pos) / ACCOUNT:+.2%}")
    P("\n  So the MAGNITUDE half of the expectation is already met: every negative year is")
    P("  inside 1.6% of the account, and all five together are 3.1%.")

    P("\n=== 2. THE COUNT: WHAT SHOULD A SHARPE-0.70 STRATEGY DELIVER? ===")
    p = p_year_negative(S)
    tail = p_at_least_k_negative(n, S, len(neg))
    P(f"  measured pooled Sharpe {S:+.3f}")
    P(f"  P(any given year negative) = Phi(-S) = {p:.1%}")
    P(f"  EXPECTED negative years in {n} = {n * p:.2f}")
    P(f"  OBSERVED {len(neg)}.  P(>= {len(neg)} | S={S:.2f}) = {tail:.1%}  -> "
      f"{'NOT unusual' if tail > 0.05 else 'unusual'}")
    inv = {t: sharpe_for_expected_negatives(n, t) for t in (1.0, 0.5)}
    P(f"\n  to EXPECT at most 1 negative year in {n} you need Sharpe ~ {inv[1.0]:.2f}")
    P(f"  to expect at most 0.5                      you need Sharpe ~ {inv[0.5]:.2f}")
    P(f"  we have {S:+.2f}. The expectation describes a strategy roughly TWICE as good,")
    P(f"  which is what CLAUDE.md's layering arithmetic was for: five components at")
    P(f"  0.4-0.6 with rho < 0.3 reach 1.5. We have one.")

    P("\n=== 3. AND THE CORRECTION: WHAT THE RULES ACTUALLY PAY ===")
    m = load_d386()
    mffu = [q for q in m.PLANS if q.firm.startswith("MFFU") and q.size == 50000
            and "EOD" in q.firm][0]
    P(f"  {mffu.firm}: fee ${mffu.fee_eval:.0f} | EVAL TARGET ${mffu.target:,.0f} | "
      f"dd ${mffu.dd_fund:,.0f}")
    P(f"  | safety net ${mffu.safety_net:,.0f} you may not withdraw below | "
      f"{mffu.qual_days} qualifying days at >= ${mffu.qual_threshold:.0f} | "
      f"min payout ${mffu.min_payout:.0f}")
    P("\n  V = expected dollars PAID OUT minus fees, per evaluation purchased.")
    P("  The arm cannot choose its size -- one MNQ is the floor -- so vol is GIVEN.\n")
    P("     scenario              Sharpe   vol$      V$    SE   paid$  P(paid)  P(pass)  "
      "med fund days")
    scen = [("pooled 2016-2026", S, vol),
            ("in-sample 2016-23", 0.7229, 180.5),
            ("2026 alone", py["2026"]["sharpe"], py["2026"]["daily_sigma_usd"]),
            ("2025 alone", py["2025"]["sharpe"], py["2025"]["daily_sigma_usd"]),
            ("a flat year (2024)", py["2024"]["sharpe"], py["2024"]["daily_sigma_usd"])]
    rows = {}
    for lab, sh, v in scen:
        r = m.simulate(mffu, sh, v, n_paths=N_PATHS, days=DAYS)
        rows[lab] = {k: r[k] for k in ("V", "V_se", "paid_mean", "paid_median", "p_paid",
                                       "p_pass", "fees_mean", "n_payouts_mean",
                                       "fund_days_med")} | {"sharpe": sh, "vol": v}
        P(f"     {lab:<21}{sh:>+7.2f}{v:>7.0f}{r['V']:>9.0f}{r['V_se']:>6.0f}"
          f"{r['paid_mean']:>8.0f}{r['p_paid']:>8.1%}{r['p_pass']:>9.1%}"
          f"{r['fund_days_med']:>14.0f}")

    best = m.best_over_risk(mffu, S, VOL_GRID, n_paths=N_PATHS, days=DAYS)
    P(f"\n  if size were free, D386 would pick vol ${best['vol']:.0f} for V ${best['V']:.0f};")
    P(f"  we are FORCED to ${vol:.0f} pooled and ${py['2026']['daily_sigma_usd']:.0f} in 2026,")
    P(f"  which costs {1 - rows['pooled 2016-2026']['V'] / best['V']:.0%} of V.")

    P("\n=== 4. SO WHAT IS ACTUALLY WORTH BEING UNHAPPY ABOUT ===")
    r = rows["pooled 2016-2026"]
    P(f"  NOT the five negative years -- they are -0.04% to -1.51% of the account.")
    P(f"  NOT five-of-eleven as a count -- the expectation is 2.67 and 5 has p = {tail:.0%}.")
    P(f"  IT IS THIS: P(pass the ${mffu.target:,.0f} evaluation) = {r['p_pass']:.0%}, and")
    P(f"  P(EVER being paid a cent) = {r['p_paid']:.0%}. Four accounts in five pay nothing.")
    P(f"  V is +${r['V']:.0f} per ${mffu.fee_eval:.0f} account -- positive, ~"
      f"{r['V'] / mffu.fee_eval:.1f}x the fee -- but the MODE is zero.")
    P(f"\n  and my earlier '+$21,935, 4.4%/yr' was an upper bound on a quantity the rules do")
    P(f"  not permit: it summed realised P&L and charged one fee per breach, ignoring the")
    P(f"  eval target, the safety net and the qualifying days. D386's V is the honest figure.")

    art = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D505: the principal asked whether one negative year near zero is a "
                      "reasonable expectation. An analysis of committed numbers plus D386's "
                      "published-rules lifecycle at the arm's FORCED size. Nothing admitted.",
           "pooled_sharpe": S, "pooled_daily_sigma_usd": vol, "n_years": n,
           "negative_years": {y: py[y]["total_usd"] for y in live if py[y]["total_usd"] < 0},
           "positive_years": {y: py[y]["total_usd"] for y in live if py[y]["total_usd"] >= 0},
           "negative_years_total_usd": sum(neg),
           "negative_years_share_of_account": sum(neg) / ACCOUNT,
           "worst_year_share_of_account": min(neg) / ACCOUNT,
           "p_year_negative_at_pooled_sharpe": p,
           "expected_negative_years": n * p, "observed_negative_years": len(neg),
           "p_at_least_observed": tail,
           "sharpe_needed_for_expected_negatives": inv,
           "plan": {"firm": mffu.firm, "fee": mffu.fee_eval, "eval_target": mffu.target,
                    "dd_fund": mffu.dd_fund, "safety_net": mffu.safety_net,
                    "qual_threshold": mffu.qual_threshold, "qual_days": mffu.qual_days,
                    "min_payout": mffu.min_payout},
           "lifecycle": rows,
           "best_if_size_were_free": {"vol": best["vol"], "V": best["V"]},
           "supersedes": "D503 s9d and D504 s5's '+$21,935 net, 4.4%/yr' -- that summed "
                         "realised P&L less one fee per breach and ignored the $3,000 eval "
                         "target, the $2,000 safety net and the qualifying-day gates. V is "
                         "the figure the rules permit.",
           "limitations": [
               "D386 simulates BROWNIAN paths at a given (Sharpe, vol); the real series is "
               "fat-tailed and regime-clustered, so a real account breaches SOONER and V is "
               "optimistic (D440: clustering, not kurtosis, carried five sixths of that gap)",
               "every D386 parameter is from its lane files; assumptions are marked there",
               "the arm's own figures carry D504's limitations: 2024+ spent, fills are upper "
               "bounds, a one-year Sharpe carries SE ~1.0"]}
    OUT.write_text(json.dumps(art, indent=2, default=float), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}")
    if as_json:
        P(json.dumps(art, indent=2, default=float))
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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
