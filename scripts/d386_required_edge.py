"""What EDGE does a prop account need before it is worth buying?

D386 computed V at zero edge. Zero edge is the null, not a claim about anyone. This sweeps real
edge and finds where V crosses zero.

Edge raises BOTH terms, so the break-even pass rate quoted in D386 is not a fixed target:
  - P(pass) rises      -- the drifted evaluation is more likely to reach its target
  - P(reach the lock)  -- same, on the funded account's pre-lock climb
  - E[extracted] rises -- each payout cycle survives more often; theta = 2*mu/sigma^2

so all three are recomputed at each edge rather than held at their zero-edge values.

Edge is quoted as an ANNUAL SHARPE on the account's own P&L, mu*252/(sigma*sqrt(252)), which is
the units the strategy record uses. Daily vol is held at the risk level stated per row.
"""

import math
import sys

sys.path.insert(0, "scripts")
from d386_pass_rate import Geometry, simulate  # noqa: E402
from d386_account_value import ACCOUNTS, e_extracted  # noqa: E402

N, SPD, HORIZON, CHUNK = 60_000, 8, 756, 2_500

# per account: (eval target, eval dd, eval lock, climb-to-lock, funded dd, daily vol)
GEO = {
    "Apex 50K EOD": (3000.0, 2000.0, None, 2100.0, 2000.0, 250.0),
    "Apex 150K EOD": (9000.0, 4005.0, None, 4105.0, 4005.0, 750.0),
    "Topstep 50K XFA": (3000.0, 2000.0, 2000.0, 2000.0, 2000.0, 250.0),
}


def v_at(a, sharpe: float) -> dict:
    tgt, dd, lock, climb, fdd, vol = GEO[a.name]
    mu = sharpe * vol / math.sqrt(252.0)          # daily drift in dollars
    theta = 2.0 * mu / (vol ** 2)                  # 1/dollar

    p_pass = simulate(Geometry(target=tgt, drawdown=dd, floor_kind="eod_trailing", lock_at=lock),
                      daily_vol=vol, daily_drift=mu, n_paths=N, steps_per_day=SPD,
                      horizon_days=HORIZON, chunk=CHUNK)["pass_rate"]
    p_lock = simulate(Geometry(target=climb, drawdown=fdd, floor_kind="eod_trailing"),
                      daily_vol=vol, daily_drift=mu, n_paths=N, steps_per_day=SPD,
                      horizon_days=HORIZON, chunk=CHUNK)["pass_rate"]
    ex, _ = e_extracted(a.buffer, a.caps, drift_ratio=theta)
    if a.lifetime_cap:
        ex = min(ex, a.lifetime_cap)
    payout = ex * p_lock
    return {
        "sharpe": sharpe, "p_pass": p_pass, "p_lock": p_lock, "E_extracted": ex,
        "payout": payout,
        "V_list": p_pass * (payout - a.fee_activation) - a.fee_eval,
        "V_disc": p_pass * (payout - a.fee_activation) - a.fee_eval_net,
    }


print("WHAT EDGE DOES A PROP ACCOUNT NEED? V = P(pass) x E[payout|funded] - fee\n")
print("Edge = annual Sharpe on the account's own P&L. All three terms recomputed at each edge.\n")

for a in ACCOUNTS:
    print(f"--- {a.name}  (fees ${a.fee_eval:,.0f} + ${a.fee_activation:,.0f}"
          f"{f', or ${a.fee_eval_net:,.0f} discounted' if a.discount else ''}) ---")
    print(f"{'Sharpe':>8}{'P(pass)':>10}{'P(lock)':>10}{'E[extr]':>10}"
          f"{'E[payout]':>11}{'V list':>10}{'V disc':>10}")
    rows = []
    for s in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0):
        r = v_at(a, s)
        rows.append(r)
        print(f"{s:>8.1f}{r['p_pass']:>10.4f}{r['p_lock']:>10.4f}{r['E_extracted']:>10,.0f}"
              f"{r['payout']:>11,.0f}{r['V_list']:>10,.0f}"
              f"{r['V_disc']:>10,.0f}" if a.discount else
              f"{s:>8.1f}{r['p_pass']:>10.4f}{r['p_lock']:>10.4f}{r['E_extracted']:>10,.0f}"
              f"{r['payout']:>11,.0f}{r['V_list']:>10,.0f}{'':>10}")

    for key, label in (("V_list", "list price"),
                       *((("V_disc", "discounted"),) if a.discount else ())):
        below = [r for r in rows if r[key] < 0]
        above = [r for r in rows if r[key] >= 0]
        if not above:
            print(f"  break-even Sharpe ({label}): ABOVE 4.0 -- not reached in this sweep")
        elif not below:
            print(f"  break-even Sharpe ({label}): ZERO or below -- positive with no edge")
        else:
            lo, hi = below[-1], above[0]
            f = -lo[key] / (hi[key] - lo[key])
            print(f"  break-even Sharpe ({label}): approx "
                  f"{lo['sharpe'] + f * (hi['sharpe'] - lo['sharpe']):.2f}")
    print()

print("For scale: the personal book's admitted arms are not at capital, and D378 put the")
print("entry-timing increment at 0.19-0.47x a round trip. An annual Sharpe of 2+ sustained on")
print("a single account is not a number this programme has ever produced.")
