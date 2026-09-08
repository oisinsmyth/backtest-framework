"""D386 -- full-lifecycle profitability of a prop account, under EVERY published rule.

    uv run python scripts/d386_full_lifecycle.py --selftest
    uv run python scripts/d386_full_lifecycle.py --report

Earlier D386 runners modelled the barrier and the payout ladder. They did NOT model the rules that
decide whether a payout may be REQUESTED, and the principal pointed out the omission: every firm
gates payouts on a minimum number of days each clearing a minimum PROFIT, and most add a
consistency rule on top. Those rules bind hardest on exactly the small-size play that maximises
survival, so a model without them recommends a policy the terms do not permit.

WHAT IS SIMULATED, per path, day by day:
  EVALUATION   profit target; drawdown of the stated TYPE (static / EOD-trailing / intraday-
               trailing) with its lock level; breach tested against the INTRADAY equity path,
               because every firm ratchets on one quantity and kills on another; minimum days.
  FUNDED       the funded phase's OWN geometry, which at several firms differs from the one that
               was bought; the qualifying-day counter at that firm's profit threshold; the
               consistency rule; the payout cap schedule; the maximum payout count; the minimum
               withdrawal; the safety net that must be maintained; and the post-payout change to
               the floor, which differs by firm.
  FEES         one-time or MONTHLY evaluation billing (a slow pass is not free), activation on
               promotion, charged only on paths that actually pass.

OUTPUT is V = E[total paid out] - E[total fees], per evaluation purchased, plus the median and the
probability of ever being paid. Risk size is a CHOICE, so V is maximised over a grid of daily
volatilities rather than quoted at one -- and the break-even Sharpe is the lowest Sharpe at which
SOME risk level makes V positive.

EVERY PARAMETER IS FROM A D386 LANE FILE. Assumptions are marked `ASSUMED` in the table and are
listed by --report.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field

import numpy as np

EOD, INTRA, STATIC = "eod", "intra", "static"


@dataclass(frozen=True)
class Plan:
    firm: str
    size: int
    fee_eval: float            # one-time, or per month if monthly=True
    monthly: bool
    fee_activation: float
    target: float
    dd_eval: float
    kind_eval: str
    lock_eval: float | None    # ref cap, relative to start; None = never locks
    dd_fund: float
    kind_fund: str
    lock_fund: float | None
    qual_threshold: float      # minimum daily profit for a day to count
    qual_days: int
    min_total: float           # minimum net profit since last payout
    caps: tuple                # payout cap schedule; last value repeats if max_payouts is larger
    max_payouts: int
    min_payout: float
    safety_net: float          # balance must stay at or above start + this to withdraw
    consistency: float | None  # best day <= consistency * profit-since-payout, else wait
    fund_start: float = 0.0    # funded balance relative to the account size (MFFU starts at 0)
    post_payout_floor: float | None = None   # if set, floor moves here after the first payout
    start_funded: bool = False   # test fixture only: skip the evaluation and its balance reset
    notes: str = ""


def _caps(p: Plan, k: int) -> float:
    return p.caps[k] if k < len(p.caps) else p.caps[-1]


def simulate(p: Plan, sharpe: float, daily_vol: float, *, n_paths: int = 15_000,
             days: int = 750, k: int = 4, seed: int = 20260908) -> dict:
    rng = np.random.default_rng(seed)
    mu = sharpe * daily_vol / math.sqrt(252.0)
    sd = daily_vol / math.sqrt(k)
    dmu = mu / k

    n = n_paths
    bal = np.zeros(n)
    ref = np.zeros(n)
    alive = np.ones(n, bool)
    funded = np.full(n, p.start_funded)
    qual = np.zeros(n, np.int32)
    prof = np.zeros(n)
    best = np.zeros(n)
    npay = np.zeros(n, np.int32)
    paid = np.zeros(n)
    months = np.zeros(n)
    paid_activation = np.zeros(n, bool)
    ever_funded = np.full(n, p.start_funded)
    d_eval = np.zeros(n)      # trading days spent in the evaluation
    d_fund = np.zeros(n)      # trading days spent FUNDED, which is the capital-at-work clock

    for d in range(days):
        live = alive
        if not live.any():
            break
        m = int(live.sum())
        d_fund[live & funded] += 1.0
        d_eval[live & ~funded] += 1.0
        inc = rng.normal(dmu, sd, size=(m, k))
        cum = np.cumsum(inc, axis=1)
        d_low, d_high, d_end = cum.min(1), cum.max(1), cum[:, -1]

        b = bal[live]
        r = ref[live]
        f = funded[live]

        dd = np.where(f, p.dd_fund, p.dd_eval)
        lock = np.where(f,
                        np.inf if p.lock_fund is None else p.lock_fund,
                        np.inf if p.lock_eval is None else p.lock_eval)
        base = np.where(f, p.fund_start, 0.0)
        r_eff = np.minimum(np.maximum(r, base), lock)
        floor = r_eff - dd
        if p.post_payout_floor is not None:
            moved = npay[live] > 0
            floor = np.where(moved, p.post_payout_floor, floor)

        breach = (b + d_low) <= floor

        kind = np.where(f, p.kind_fund, p.kind_eval)
        new_ref = r.copy()
        is_eod = kind == EOD
        is_in = kind == INTRA
        new_ref[is_eod] = np.maximum(r[is_eod], (b + d_end)[is_eod])
        new_ref[is_in] = np.maximum(r[is_in], (b + d_high)[is_in])
        b = b + d_end

        # --- evaluation: pass on reaching the target
        passed = (~f) & (b >= p.target) & (~breach)

        # --- funded: qualifying days, consistency, payout
        pnl = d_end
        q = qual[live] + ((f & (pnl >= p.qual_threshold)) & (~breach)).astype(np.int32)
        pr = prof[live] + np.where(f & (~breach), pnl, 0.0)
        bd = np.maximum(best[live], np.where(f & (~breach), pnl, 0.0))

        withdrawable = b - (p.fund_start + p.safety_net)
        cap_now = np.array([_caps(p, int(x)) for x in npay[live]])
        cons_ok = np.ones(m, bool) if p.consistency is None else (bd <= p.consistency * np.maximum(pr, 1e-9))
        eligible = (f & (~breach) & (q >= p.qual_days) & (pr >= p.min_total)
                    & cons_ok & (withdrawable >= p.min_payout))
        amount = np.where(eligible, np.minimum(cap_now, np.maximum(withdrawable, 0.0)), 0.0)
        b = b - amount
        np_new = npay[live] + eligible.astype(np.int32)
        q = np.where(eligible, 0, q)
        pr = np.where(eligible, 0.0, pr)
        bd = np.where(eligible, 0.0, bd)

        closed_out = np_new >= p.max_payouts
        still = (~breach) & (~closed_out)

        # --- write back
        idx = np.flatnonzero(live)
        bal[idx] = b
        ref[idx] = np.where(passed, p.fund_start, new_ref)
        qual[idx] = q
        prof[idx] = pr
        best[idx] = bd
        npay[idx] = np_new
        paid[idx] += amount
        alive[idx] = still
        newly = passed & still
        bal[idx[newly]] = p.fund_start
        funded[idx[newly]] = True
        ever_funded[idx[newly]] = True
        if p.monthly:
            months[idx[~funded[idx]]] += 1.0 / 21.0
        need_act = idx[newly & (~paid_activation[idx])]
        paid_activation[need_act] = True

    fees = (p.fee_eval * np.maximum(months, 1.0 / 21.0) if p.monthly
            else np.full(n, p.fee_eval)) + p.fee_activation * paid_activation
    v = paid - fees
    return {
        "V": float(v.mean()), "V_se": float(v.std(ddof=1) / math.sqrt(n)),
        "paid_mean": float(paid.mean()), "paid_median": float(np.median(paid)),
        "p_paid": float((paid > 0).mean()), "p_pass": float(ever_funded.mean()),
        "fees_mean": float(fees.mean()), "n_payouts_mean": float(npay.mean()),
        "p_alive_at_horizon": float(alive.mean()),
        "vol": daily_vol, "sharpe": sharpe,
        # the time distribution, conditional on ever being funded -- this is the capital-at-work
        # clock and, at a monthly-billing firm, the cost clock too
        "eval_days_mean": float(d_eval[ever_funded].mean()) if ever_funded.any() else float("nan"),
        "eval_days_med": float(np.median(d_eval[ever_funded])) if ever_funded.any() else float("nan"),
        "fund_days_mean": float(d_fund[ever_funded].mean()) if ever_funded.any() else float("nan"),
        "fund_days_med": float(np.median(d_fund[ever_funded])) if ever_funded.any() else float("nan"),
        "fund_days_p25": float(np.percentile(d_fund[ever_funded], 25)) if ever_funded.any() else float("nan"),
        "fund_days_p75": float(np.percentile(d_fund[ever_funded], 75)) if ever_funded.any() else float("nan"),
        "fund_days_p90": float(np.percentile(d_fund[ever_funded], 90)) if ever_funded.any() else float("nan"),
        "fund_censored": float((d_fund[ever_funded] >= days - d_eval[ever_funded] - 1).mean()) if ever_funded.any() else float("nan"),
    }


def best_over_risk(p: Plan, sharpe: float, vols, **kw) -> dict:
    out = [simulate(p, sharpe, v, **kw) for v in vols]
    return max(out, key=lambda r: r["V"])


def breakeven_sharpe(p: Plan, vols, lo=0.0, hi=5.0, tol=0.1, **kw) -> float:
    if best_over_risk(p, lo, vols, **kw)["V"] > 0:
        return lo
    if best_over_risk(p, hi, vols, **kw)["V"] < 0:
        return float("inf")
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if best_over_risk(p, mid, vols, **kw)["V"] < 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ==============================================================================================
# THE PLANS. Every value from a D386 lane file unless marked ASSUMED.
# ==============================================================================================

BIG = 10_000_000.0

ASSUMPTIONS = [
    "Take Profit Trader's qualifying-day threshold is published for 25K ($250) and 50K ($500). "
    "The 100K and 150K values are ASSUMED equal to the 50K's $500 (lane 04 field 18 gives no "
    "larger-size row).",
    "Topstep's payout rule is '50% of balance up to the cap'. The cap is modelled; the 50%-of-"
    "balance clause is APPROXIMATED by allowing withdrawal down to the start level, which is "
    "generous to Topstep when the balance is small.",
    "Apex states no minimum NET profit since last payout beyond its per-day threshold; min_total "
    "is set to 0 for it.",
    "Daily P&L is Gaussian. Real P&L is fat-tailed, which RAISES the chance of clearing a high "
    "daily-profit threshold at small size and LOWERS survival. Both effects are unmodelled.",
    "The 7-day (MFFU) and 30-day (Apex) inactivity rules are NOT modelled; at every risk level "
    "tested they are cleared comfortably, so they do not bind.",
]


def _apex(size, fee, act, target, dd, qual, caps):
    return Plan("Apex", size, fee, False, act, target, dd, EOD, target, dd, EOD, dd + 100.0,
                qual, 5, 0.0, caps, 6, 500.0, dd, 0.50,
                notes="one-time fee; 6 payouts then the PA is closed; floor locks at start+$100")


def _mffu(size, fee, target, dd, qual, kind_fund):
    return Plan("MFFU Rapid" + (" EOD" if kind_fund == EOD else ""), size, fee, False, 0.0,
                target, dd, EOD, dd + 100.0, dd, kind_fund, dd + 100.0,
                qual, 5, 500.0, (BIG,), 20, 500.0, dd, None,
                notes="one-time fee, $0 activation, NO payout cap, no funded consistency rule")


def _tpt(size, mo, target, dd, qual, assumed=False):
    return Plan("Take Profit Trader", size, mo, True, 130.0, target, dd, EOD, dd, dd, INTRA, dd,
                qual, 5, 0.0, (BIG,), 20, 0.0, dd, None,
                notes="MONTHLY billing; eval is EOD-trailed, funded is INTRADAY-trailed"
                      + (" ; qualifying threshold ASSUMED" if assumed else ""))


PLANS = [
    _apex(25_000, 450.0, 119.0, 1500.0, 1000.0, 100.0, (1000.0,) * 6),
    _apex(50_000, 550.0, 139.0, 3000.0, 2000.0, 250.0, (1500., 1500., 2000., 2500., 2500., 3000.)),
    _apex(100_000, 990.0, 149.0, 6000.0, 3000.0, 300.0, (2000., 2500., 2500., 3000., 4000., 4000.)),
    _apex(150_000, 1890.0, 159.0, 9000.0, 4005.0, 350.0, (2500., 3000., 3000., 3000., 4000., 5000.)),
    _mffu(25_000, 145.0, 1500.0, 1000.0, 100.0, EOD),
    _mffu(50_000, 209.0, 3000.0, 2000.0, 150.0, EOD),
    _mffu(50_000, 209.0, 3000.0, 2000.0, 150.0, INTRA),
    _mffu(100_000, 356.0, 6000.0, 3000.0, 150.0, INTRA),
    _mffu(150_000, 463.0, 9000.0, 4500.0, 150.0, INTRA),
    Plan("Topstep", 50_000, 49.0, True, 149.0, 3000.0, 2000.0, EOD, 2000.0, 2000.0, EOD, 2000.0,
         150.0, 5, 0.01, (2000.0,), 20, 125.0, 0.0, 0.50, post_payout_floor=0.0,
         notes="MONTHLY $49; a payout sets the MLL to $0, so the floor moves to the start level"),
    _tpt(25_000, 150.0, 1500.0, 1500.0, 250.0),
    _tpt(50_000, 170.0, 3000.0, 2000.0, 500.0),
    _tpt(100_000, 330.0, 6000.0, 3000.0, 500.0, assumed=True),
    _tpt(150_000, 360.0, 9000.0, 4500.0, 500.0, assumed=True),
]

RISK_FRACS = (0.002, 0.004, 0.007, 0.011)     # daily vol as a fraction of account size


def selftest() -> int:
    fails = []

    def check(tag, ok, detail):
        print(f"  [{tag}] {'PASS' if ok else 'FAIL'}  {detail}")
        if not ok:
            fails.append(tag)

    print("D386 full-lifecycle self-test\n")
    kw = dict(n_paths=6_000, days=500, k=4)

    # a degenerate plan: static floor, no qualifying-day rule, no cap -> E[paid] must be the buffer
    # E[paid] = buffer is a MARTINGALE identity and holds only at ABSORPTION. The first version of
    # this check ran 500 days at $250/day vol, where absorption is far from complete, and returned
    # $1,681 against $2,000 -- the same horizon-truncation defect the pass-rate runner's
    # [CF-PRECOND] exists to catch. The fraction still alive is now a PRECONDITION, not an
    # afterthought, and the vol is raised so absorption actually finishes.
    degen = Plan("degenerate", 50_000, 0.0, False, 0.0, 0.0, 2000.0, STATIC, 0.0,
                 2000.0, STATIC, 0.0, -BIG, 0, 0.0, (500.0,), 200, 0.0, 2000.0, None,
                 start_funded=True)
    # E[paid] = buffer holds for a CONTINUOUS path. A discrete step OVERSHOOTS the barrier, so the
    # balance at ruin is below -b and E[paid] comes in ABOVE the buffer by roughly half a step.
    # That is a discretisation, not an error, so the assertion is CONVERGENCE: refining the step
    # must move the estimate toward $2,000, and the fine estimate must sit within a bound set by
    # the step size rather than by taste.
    r4 = simulate(degen, 0.0, 500.0, n_paths=6_000, days=1500, k=4)
    r16 = simulate(degen, 0.0, 500.0, n_paths=6_000, days=1500, k=16)
    check("BUFFER-PRECOND", r4["p_alive_at_horizon"] < 0.01 and r16["p_alive_at_horizon"] < 0.01,
          f"{r4['p_alive_at_horizon']:.4f} / {r16['p_alive_at_horizon']:.4f} still alive; the "
          f"identity holds only at absorption")
    check("BUFFER-CONVERGES", abs(r16["paid_mean"] - 2000.0) < abs(r4["paid_mean"] - 2000.0),
          f"k=4 -> ${r4['paid_mean']:,.0f}, k=16 -> ${r16['paid_mean']:,.0f}; refining the step "
          f"moves it toward the buffer")
    step16 = 500.0 / math.sqrt(16)
    check("BUFFER", 0.0 < r16["paid_mean"] - 2000.0 < 2.0 * step16,
          f"E[paid] ${r16['paid_mean']:,.0f} vs buffer $2,000: excess ${r16['paid_mean']-2000:,.0f} "
          f"is POSITIVE and under two intraday steps (${2*step16:,.0f})")
    # The sign is the point and it is recorded rather than tuned away: a discrete step OVERSHOOTS
    # the floor, so the balance at death is below -b and E[paid] comes in ABOVE the identity.
    # Every V in --report therefore carries a few per cent of OPTIMISTIC bias from this alone.

    apex50 = PLANS[1]
    lo = simulate(apex50, 0.5, 250.0, **kw)
    hi = simulate(apex50, 2.5, 250.0, **kw)
    check("MONO-SHARPE", hi["V"] > lo["V"] and hi["p_pass"] > lo["p_pass"],
          f"Apex 50K V at Sharpe 0.5 ${lo['V']:,.0f} -> at 2.5 ${hi['V']:,.0f}")

    strict = Plan(*[getattr(apex50, f.name) for f in apex50.__dataclass_fields__.values()])
    strict = Plan(**{**{f: getattr(apex50, f) for f in apex50.__dataclass_fields__},
                     "qual_threshold": 2000.0})
    a = simulate(apex50, 1.5, 250.0, **kw)
    b = simulate(strict, 1.5, 250.0, **kw)
    check("QUAL-BINDS", b["p_paid"] < a["p_paid"],
          f"raising the qualifying threshold $250 -> $2,000 cuts P(ever paid) "
          f"{a['p_paid']:.3f} -> {b['p_paid']:.3f}")

    dear = Plan(**{**{f: getattr(apex50, f) for f in apex50.__dataclass_fields__},
                   "fee_eval": 5000.0})
    c = simulate(dear, 1.5, 250.0, **kw)
    check("FEE", c["V"] < a["V"] - 4000.0,
          f"a $5,000 fee moves V ${a['V']:,.0f} -> ${c['V']:,.0f}")

    check("CAN-FAIL", not (b["p_paid"] >= a["p_paid"]),
          "a model that ignored the qualifying rule would show no difference; this one does")

    print()
    if fails:
        print(f"FAILED: {', '.join(fails)}")
        return 1
    print("all assertions passed")
    return 0


def report(n_paths=8_000, days=600) -> int:
    kw = dict(n_paths=n_paths, days=days, k=4)
    print("D386 -- FULL-LIFECYCLE PROFITABILITY UNDER EVERY PUBLISHED RULE")
    print(f"  {n_paths:,} paths, {days} trading days, 4 intraday steps")
    print("  V = E[total paid out] - E[total fees], per EVALUATION PURCHASED")
    print("  risk size is a choice, so V is MAXIMISED over daily vol in "
          f"{[f'{100*f:.1f}%' for f in RISK_FRACS]} of account size\n")

    hdr = (f"{'firm':<20}{'size':>7}{'fee':>17}" +
           "".join(f"{f'V @ S={s}':>12}" for s in (1.0, 1.5, 2.0)) +
           f"{'best risk':>11}{'P(pass)':>9}{'P(paid)':>9}{'BE Sharpe':>11}")
    print(hdr)
    print("-" * len(hdr))

    rows = []
    for p in PLANS:
        vols = [f * p.size for f in RISK_FRACS]
        cells = {s: best_over_risk(p, s, vols, **kw) for s in (1.0, 1.5, 2.0)}
        be = breakeven_sharpe(p, vols, **kw)
        c15 = cells[1.5]
        fee = f"${p.fee_eval:,.0f}/mo" if p.monthly else f"${p.fee_eval:,.0f}"
        if p.fee_activation:
            fee += f"+${p.fee_activation:,.0f}"
        rows.append((p, cells, be))
        print(f"{p.firm:<20}{p.size//1000:>6}K{fee:>17}"
              + "".join(f"{cells[s]['V']:>12,.0f}" for s in (1.0, 1.5, 2.0))
              + f"{100*c15['vol']/p.size:>10.1f}%{c15['p_pass']:>9.3f}{c15['p_paid']:>9.3f}"
              + (f"{be:>11.2f}" if be != float('inf') else f"{'>5':>11}"))

    print("\n  BE Sharpe = the lowest Sharpe at which SOME risk level makes V positive.")
    print("  'best risk' and the P() columns are taken at the Sharpe-1.5 optimum.\n")

    print("DETAIL AT SHARPE 1.5 -- what the money actually looks like\n")
    print(f"{'firm':<20}{'size':>7}{'E[paid]':>10}{'median':>9}{'E[fees]':>9}"
          f"{'payouts':>9}{'V':>10}")
    print("-" * 74)
    for p, cells, _ in rows:
        c = cells[1.5]
        print(f"{p.firm:<20}{p.size//1000:>6}K{c['paid_mean']:>10,.0f}"
              f"{c['paid_median']:>9,.0f}{c['fees_mean']:>9,.0f}"
              f"{c['n_payouts_mean']:>9.2f}{c['V']:>10,.0f}")

    print("\nTIME, AT SHARPE 1.5 -- trading days, conditional on ever being funded")
    print("  the funded clock is capital-at-work, and at a monthly-billing firm it is cost too\n")
    print(f"{'firm':<20}{'size':>7}{'eval med':>10}{'FUNDED med':>12}{'mean':>8}"
          f"{'p25':>7}{'p75':>7}{'p90':>7}{'censored':>10}")
    print("-" * 88)
    for p, cells, _ in rows:
        c = cells[1.5]
        print(f"{p.firm:<20}{p.size//1000:>6}K{c['eval_days_med']:>10.0f}"
              f"{c['fund_days_med']:>12.0f}{c['fund_days_mean']:>8.0f}"
              f"{c['fund_days_p25']:>7.0f}{c['fund_days_p75']:>7.0f}{c['fund_days_p90']:>7.0f}"
              f"{c['fund_censored']:>9.1%}")
    print("\n  'censored' = share still alive when the 600-day simulation ended; those accounts'")
    print("  true lifetimes are LONGER than shown, so the means are understated.\n")

    print("ASSUMPTIONS AND UNMODELLED RULES")
    for a in ASSUMPTIONS:
        print(f"  - {a}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--paths", type=int, default=8_000)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.report:
        return report(n_paths=a.paths)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
