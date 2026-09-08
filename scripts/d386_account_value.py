"""D386 -- is the payout large enough for the risk? V = P(pass) x E[extracted] - fee.

    uv run python scripts/d386_account_value.py --selftest
    uv run python scripts/d386_account_value.py --report

THE QUESTION THIS ANSWERS, and it is the principal's, not the record's: every prop account
eventually hits the firm's constraints. What decides whether one is worth buying is whether the
payout is large enough to pay for the risk. D379 names the objective -- V = N x [P(pass) x
E[payout|funded] - fee] -- and could not evaluate it, because D379 §6 says no record held the
payout terms. The D386 lanes now hold them, so it can be evaluated.

THE MODEL, stated so it can be attacked.

Once the funded floor has locked, the account is a driftless-or-drifted walk with a STATIC floor
and a safety net the trader must maintain. Withdrawing profit but keeping the safety net means each
payout cycle is the SAME race repeated: from the safety-net balance, climb c_k (the k-th payout
cap) before falling b (the buffer to the floor). So the funded phase is a RENEWAL process and

    P(cycle k succeeds) = b / (b + c_k)          -- gambler's ruin, at zero edge
    E[extracted]        = SUM_k  c_k * PROD_{j<=k} p_j

with the product truncated at the firm's maximum payout count. This is exact for a driftless walk
with a static floor and fixed withdrawal sizes; [MC] checks it by simulation.

WHAT THE MODEL DELIBERATELY OMITS, because omitting it is CONSERVATIVE IN THE WRONG DIRECTION and
must be said: the PRE-LOCK phase. At Apex the funded floor starts one drawdown BELOW the balance and
trails up, locking only at start + $100, so a new funded account must first survive a climb of
(drawdown + $100) before the renewal model applies. That is an extra barrier race, it is not counted
here, and counting it can only LOWER E[extracted]. Every number below is therefore an UPPER BOUND
on the value of a funded account, and the conclusions are drawn accordingly.

Costs follow D379 A1: you buy evaluations until one passes, so the acquisition cost of one funded
account is fee_eval / P(pass) + fee_activation, and per evaluation purchased

    V = P(pass) x (E[extracted] - fee_activation) - fee_eval
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Account:
    name: str
    fee_eval: float           # per evaluation attempt, list price
    fee_activation: float     # one-time on passing
    buffer: float             # distance from the safety-net balance to the locked floor
    caps: tuple               # payout cap for each successive withdrawal
    pass_rate: float          # zero-edge P(pass) for this evaluation geometry, from d386_pass_rate
    lifetime_cap: float | None = None
    note: str = ""
    discount: float = 0.0     # fraction off the list evaluation fee actually transacted

    @property
    def fee_eval_net(self) -> float:
        return self.fee_eval * (1.0 - self.discount)


def e_extracted(buffer: float, caps, drift_ratio: float = 0.0) -> tuple[float, list]:
    """Expected lifetime extraction, and the per-cycle survival probabilities.

    drift_ratio is theta = 2*mu/sigma^2 in units of 1/dollar. At theta = 0 each cycle is
    gambler's ruin b/(b+c); otherwise it is the drifted two-sided exit probability.
    """
    ps, total, prod = [], 0.0, 1.0
    for c in caps:
        if abs(drift_ratio) < 1e-12:
            p = buffer / (buffer + c)
        else:
            # P(hit +c before -b) for BM with drift; theta = 2 mu / sigma^2
            t = drift_ratio
            p = (1.0 - math.exp(t * buffer)) / (math.exp(-t * c) - math.exp(t * buffer))
        ps.append(p)
        prod *= p
        total += c * prod
    return total, ps


def value_per_eval(a: Account, drift_ratio: float = 0.0, pass_rate: float | None = None,
                   net_of_discount: bool = False) -> dict:
    ex, ps = e_extracted(a.buffer, a.caps, drift_ratio)
    if a.lifetime_cap is not None:
        ex = min(ex, a.lifetime_cap)
    pr = a.pass_rate if pass_rate is None else pass_rate
    fee = a.fee_eval_net if net_of_discount else a.fee_eval
    v = pr * (ex - a.fee_activation) - fee
    return {"E_extracted": ex, "cycle_p": ps, "pass_rate": pr, "fee_eval": fee,
            "V_per_eval": v, "cost_per_funded": fee / pr + a.fee_activation}


def breakeven_pass_rate(a: Account, drift_ratio: float = 0.0,
                        net_of_discount: bool = False) -> float:
    ex, _ = e_extracted(a.buffer, a.caps, drift_ratio)
    if a.lifetime_cap is not None:
        ex = min(ex, a.lifetime_cap)
    fee = a.fee_eval_net if net_of_discount else a.fee_eval
    denom = ex - a.fee_activation
    return float("inf") if denom <= 0 else fee / denom


# ------------------------------------------------------------------------------------------
# the accounts, every term from a D386 lane file, list prices, 2026-09-08
# ------------------------------------------------------------------------------------------

APEX_50K_EOD = Account(
    name="Apex 50K EOD",
    fee_eval=550.0, fee_activation=139.0, buffer=2000.0,
    caps=(1500.0, 1500.0, 2000.0, 2500.0, 2500.0, 3000.0),
    lifetime_cap=13000.0, pass_rate=0.2495, discount=0.90,
    note="lane 03 fields 2/4/8/19; 6 payouts then the PA is closed; eval floor locks only at "
         "the profit target, so the eval is the no-lock EOD geometry",
)
APEX_150K_EOD = Account(
    name="Apex 150K EOD",
    fee_eval=1890.0, fee_activation=159.0, buffer=4005.0,
    caps=(2500.0, 3000.0, 3000.0, 3000.0, 4000.0, 5000.0),
    lifetime_cap=20500.0, pass_rate=0.1348, discount=0.90,
    note="drawdown 2.67% of 150K against a flat 6% target, so the ratio is 2.25 and the eval "
         "is harder than the 50K's",
)
TOPSTEP_50K = Account(
    name="Topstep 50K XFA",
    fee_eval=49.0, fee_activation=149.0, buffer=2000.0,
    caps=(2000.0,) * 12,
    lifetime_cap=None, pass_rate=0.2664, discount=0.0,
    note="lane 02 fields 2/4/19; $49/MONTH not one-time, so fee_eval understates a slow pass; "
         "cap is flat $2,000 with no ladder and no stated maximum count",
)
ACCOUNTS = (APEX_50K_EOD, APEX_150K_EOD, TOPSTEP_50K)


# ------------------------------------------------------------------------------------------
# assertions
# ------------------------------------------------------------------------------------------


def _mc_extracted(buffer: float, caps, n: int = 200_000, step: float = 25.0,
                  seed: int = 20260908) -> float:
    """Simulate the renewal directly: from 0, race to +c before -buffer, repeat."""
    rng = np.random.default_rng(seed)
    alive = np.ones(n, dtype=bool)
    total = np.zeros(n)
    for c in caps:
        idx = np.flatnonzero(alive)
        if idx.size == 0:
            break
        pos = np.zeros(idx.size)
        done = np.zeros(idx.size, dtype=bool)
        won = np.zeros(idx.size, dtype=bool)
        for _ in range(400_000):
            live = ~done
            if not live.any():
                break
            pos[live] += rng.choice((-step, step), size=int(live.sum()))
            hit = live & (pos >= c)
            won |= hit
            done |= hit
            done |= live & (pos <= -buffer)
        total[idx[won]] += c
        alive[idx[~won]] = False
    return float(total.mean())


def selftest() -> int:
    fails = []

    def check(tag, ok, detail):
        print(f"  [{tag}] {'PASS' if ok else 'FAIL'}  {detail}")
        if not ok:
            fails.append(tag)

    print("D386 account-value self-test\n")

    # [RUIN] one cycle must be gambler's ruin
    ex, ps = e_extracted(2000.0, (1500.0,))
    check("RUIN", abs(ps[0] - 2000 / 3500) < 1e-12 and abs(ex - 1500 * 2000 / 3500) < 1e-9,
          f"one cycle b=2000 c=1500 -> p {ps[0]:.6f} (want {2000/3500:.6f}), "
          f"E {ex:.2f} (want {1500*2000/3500:.2f})")

    # [MC] the renewal closed form against simulation of the same process
    caps = (1500.0, 1500.0, 2000.0)
    cf, _ = e_extracted(2000.0, caps)
    mc = _mc_extracted(2000.0, caps, n=40_000)
    se = 4.0 * 900.0 / math.sqrt(40_000)
    check("MC", abs(cf - mc) < se,
          f"closed form {cf:.1f} vs simulation {mc:.1f}, tol {se:.1f}")

    # [MONO] a bigger buffer or a smaller cap must raise E[extracted] per cycle
    a, _ = e_extracted(2000.0, (1500.0, 1500.0))
    b, _ = e_extracted(4000.0, (1500.0, 1500.0))
    c, _ = e_extracted(2000.0, (3000.0, 3000.0))
    check("MONO", b > a > 0 and c > 0,
          f"E: buffer 2000 -> {a:.0f}, buffer 4000 -> {b:.0f}; bigger caps but rarer -> {c:.0f}")

    # [DRIFT] positive drift must raise every cycle probability above the driftless value
    d0, p0 = e_extracted(2000.0, (1500.0,), drift_ratio=0.0)
    dp, pp = e_extracted(2000.0, (1500.0,), drift_ratio=0.0004)
    dn, pn = e_extracted(2000.0, (1500.0,), drift_ratio=-0.0004)
    check("DRIFT", pn[0] < p0[0] < pp[0],
          f"p at theta -4e-4 / 0 / +4e-4 = {pn[0]:.4f} / {p0[0]:.4f} / {pp[0]:.4f}")

    # [BE] break-even must invert value exactly
    be = breakeven_pass_rate(APEX_50K_EOD)
    v = value_per_eval(APEX_50K_EOD, pass_rate=be)["V_per_eval"]
    check("BE", abs(v) < 1e-8, f"V at the break-even pass rate {be:.4f} is {v:.2e}")

    # the checks must be able to fail
    bad, _ = e_extracted(2000.0, (1500.0,))
    check("CAN-FAIL", not abs(bad - 1500.0) < 1e-9,
          f"E[extracted] {bad:.1f} is NOT the cap {1500.0:.1f} -- a model that ignored ruin "
          f"would return the cap")

    print()
    if fails:
        print(f"FAILED: {', '.join(fails)}")
        return 1
    print("all assertions passed")
    return 0


def report() -> int:
    print("D386 -- IS THE PAYOUT LARGE ENOUGH FOR THE RISK?")
    print("Every term from a D386 lane file. List prices, 2026-09-08. ZERO EDGE.\n")
    print("UPPER BOUND: the pre-lock climb is not modelled, and counting it can only lower "
          "E[extracted].\n")

    for a in ACCOUNTS:
        r = value_per_eval(a)
        be = breakeven_pass_rate(a)
        print(f"--- {a.name} ---")
        print(f"  {a.note}")
        print(f"  buffer ${a.buffer:,.0f} · caps {[int(c) for c in a.caps[:6]]}"
              f"{' ...' if len(a.caps) > 6 else ''}")
        print(f"  per-cycle survival  {[f'{p:.3f}' for p in r['cycle_p'][:6]]}")
        print(f"  E[extracted | funded]        ${r['E_extracted']:>9,.0f}"
              f"   (lifetime cap ${a.lifetime_cap:,.0f})" if a.lifetime_cap
              else f"  E[extracted | funded]        ${r['E_extracted']:>9,.0f}")
        print(f"  zero-edge P(pass)             {r['pass_rate']:>9.4f}")
        print(f"  cost per funded account      ${r['cost_per_funded']:>9,.0f}"
              f"  (= {a.fee_eval:,.0f}/{r['pass_rate']:.4f} + {a.fee_activation:,.0f})")
        print(f"  V PER EVALUATION AT LIST     ${r['V_per_eval']:>9,.0f}")
        if a.discount:
            rd = value_per_eval(a, net_of_discount=True)
            print(f"  V at the {100*a.discount:.0f}% discount actually transacted "
                  f"(${a.fee_eval_net:,.0f})  ${rd['V_per_eval']:>9,.0f}")
        print(f"  break-even P(pass) at list    {be:>9.4f}"
              f"   vs zero-edge {a.pass_rate:.4f}"
              f"  -> {'edge REQUIRED' if be > a.pass_rate else 'positive at ZERO edge'}")
        if a.discount:
            bed = breakeven_pass_rate(a, net_of_discount=True)
            print(f"  break-even P(pass) discounted {bed:>9.4f}"
                  f"  -> {'edge REQUIRED' if bed > a.pass_rate else 'positive at ZERO edge'}")
        print()

    print("SENSITIVITY -- E[extracted] against the buffer, which is the term the lanes pin least")
    print(f"{'buffer':>10}" + "".join(f"{a.name:>22}" for a in ACCOUNTS))
    for bf in (1000.0, 1500.0, 2000.0, 3000.0, 4000.0, 6000.0):
        row = f"{bf:>10,.0f}"
        for a in ACCOUNTS:
            ex, _ = e_extracted(bf, a.caps)
            if a.lifetime_cap:
                ex = min(ex, a.lifetime_cap)
            row += f"{ex:>22,.0f}"
        print(row)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.report:
        return report()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
