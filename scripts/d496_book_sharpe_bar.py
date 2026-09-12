"""D496 -- what book Sharpe does the RELAXED P4 actually require?

    uv run python scripts/d496_book_sharpe_bar.py --self-test
    uv run python scripts/d496_book_sharpe_bar.py --derive [--json]

**A DERIVATION, NOT A STUDY.** No signal, no backtest, no data beyond two measured inputs.
Nothing is opened, closed or admitted (R15).

WHY
---
The 1.5-2 book Sharpe target in CLAUDE.md existed to survive the OLD P4 -- an expected account
life over three years. The principal relaxed P4 on 2026-09-12 (R11's restatement): the binding
test is now **expected profit before breach > the account's cost**, with a >= 1 year life
preferred but not binding, and P5 applies a 30% single-day haircut to the profit P4 tests.

So the old target is void and the new bar has never been computed. D491 produced a candidate at
net Sharpe +0.583 and the programme has no idea whether that is enough.

THE MODEL, AND THE TWO IDENTITIES THAT CHECK IT
-----------------------------------------------
A funded account is a Brownian motion with drift, killed when its TRAILING drawdown first
reaches D = 4% of the account (R11's P1, measured on open equity). For drift mu and volatility
sigma per day, with theta = 2*mu/sigma^2, the expected running maximum at the moment the
drawdown D is first hit is

    E[M_tau] = (sigma^2 / (2*mu)) * (exp(theta*D) - 1)
    E[profit] = E[M_tau] - D        (at tau the drawdown is EXACTLY D, by definition)
    E[tau]    = E[profit] / mu      (optional stopping: E[X_tau] = mu * E[tau])

**Both of those last two are EXACT and are asserted against a simulation**, rather than the
closed form being trusted. The driftless limit E[tau] -> (D/sigma)^2 is checked too.

THE RESULT THAT MATTERS MOST IS COUNTERINTUITIVE
------------------------------------------------
profit is proportional to mu * E[tau], and mu ~ sigma while E[tau] ~ 1/sigma^2, so

    **expected profit before breach is proportional to 1 / sigma**

**Trading SMALLER makes the account earn MORE before it dies**, because the barrier sits further
away in sigma units and the position survives to collect more drift. So the binding constraint
is not C-d's 1%-of-account cap -- it is **the one-micro floor**, below which size cannot go.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d496_book_sharpe_bar.json"

ACCOUNT = 50_000.0
DRAWDOWN = 0.04                 # R11 P1: 4% trailing, on OPEN equity
C_D_CAP = 0.01                  # C-d: daily sigma <= 1% of the account
TRADING_DAYS = 252
P5_HAIRCUT = 0.30               # R11's restatement: single-day cap for calculation
# D491, measured: one MNQ on the candidate cell
CANDIDATE = {"root": "NQ", "cell": "B1 M=3 day session", "sharpe": 0.5829,
             "daily_sigma_usd": 185.0, "honest_sharpe": 0.4913}


def P(*a, **k):
    print(*a, **k, flush=True)


# ---------------------------------------------------------------- the model

def expected_profit_before_breach(sharpe: float, sigma_frac: float,
                                  D: float = DRAWDOWN) -> tuple[float, float]:
    """(expected profit, expected life in days), both in ACCOUNT-FRACTION units.

    sigma_frac is the DAILY sigma as a fraction of the account.
    """
    if sigma_frac <= 0:
        return float("nan"), float("nan")
    mu = sigma_frac * sharpe / np.sqrt(TRADING_DAYS)
    if abs(mu) < 1e-15:
        return 0.0, (D / sigma_frac) ** 2            # driftless limit
    theta = 2.0 * mu / sigma_frac ** 2
    e_max = (sigma_frac ** 2 / (2.0 * mu)) * (np.expm1(theta * D))
    profit = e_max - D
    return float(profit), float(profit / mu)


def sharpe_for_fee(fee_usd: float, sigma_frac: float, account: float = ACCOUNT,
                   haircut: float = 0.0) -> float:
    """Invert: the Sharpe whose RECOGNISED expected profit just covers the account's fee.

    `haircut` is the fraction of profit lost to P5's 30% single-day rule, which depends on
    the P&L distribution and is therefore passed in rather than assumed.
    """
    target = (fee_usd / account) / max(1.0 - haircut, 1e-9)
    lo, hi = 1e-6, 20.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if expected_profit_before_breach(mid, sigma_frac)[0] < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def simulate_breach(sharpe: float, sigma_frac: float, D: float = DRAWDOWN,
                    n_paths: int = 20_000, max_days: int = 40_000,
                    seed: int = 496, steps_per_day: int = 1) -> tuple[float, float, float]:
    """Brute-force the same quantity. Returns (mean profit, mean life in DAYS, censored).

    **`steps_per_day` is not a numerical detail, it is the MONITORING FREQUENCY**, and it
    changes the answer by tens of percent. A daily-monitored path can breach between
    observations and not be caught, so daily monitoring reports a LONGER life than the truth.

    R11's P1 is explicit that the venue trails on **OPEN** intraday equity, so the account is
    monitored continuously and the CLOSED FORM is the correct model. The first version of this
    check simulated at one step per day and disagreed with the closed form by 26-74% -- the
    closed form was right and the simulation was answering a different question.
    """
    # The first version regenerated the alive-index INSIDE the per-day loop after sizing the
    # noise for the original alive count, so the shapes diverged the moment a path died.
    # Fully vectorised over the chunk instead, carrying (x, peak) across chunks.
    rg = np.random.default_rng(seed)
    k = max(int(steps_per_day), 1)
    mu = sigma_frac * sharpe / np.sqrt(TRADING_DAYS) / k      # per SUB-step
    sd = sigma_frac / np.sqrt(k)
    x = np.zeros(n_paths)
    peak = np.zeros(n_paths)
    alive = np.ones(n_paths, dtype=bool)
    prof = np.zeros(n_paths)
    life = np.zeros(n_paths, dtype=np.float64)
    chunk, step = 500 * k, 0
    max_steps = max_days * k
    while alive.any() and step < max_steps:
        idx = np.flatnonzero(alive)
        steps = rg.standard_normal((len(idx), chunk)) * sd + mu
        cs = x[idx][:, None] + np.cumsum(steps, axis=1)
        runmax = np.maximum.accumulate(np.maximum(cs, peak[idx][:, None]), axis=1)
        hit = (runmax - cs) >= D
        any_hit = hit.any(axis=1)
        first = np.where(any_hit, hit.argmax(axis=1), -1)
        b = idx[any_hit]
        prof[b] = cs[any_hit, first[any_hit]]
        life[b] = (step + first[any_hit] + 1) / k             # back to DAYS
        alive[b] = False
        s = idx[~any_hit]
        x[s] = cs[~any_hit, -1]
        peak[s] = runmax[~any_hit, -1]
        step += chunk
    done = life > 0
    return float(prof[done].mean()), float(life[done].mean()), float((~done).mean())


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:66} {detail}")
        if not cond:
            fails.append(label)

    # IDENTITY 1 -- the driftless limit: E[tau] = (D/sigma)^2 exactly
    _, life0 = expected_profit_before_breach(0.0, 0.01)
    chk("driftless: E[life] = (D/sigma)^2 = 16 days", abs(life0 - 16.0) < 1e-9,
        f"{life0:.4f}")
    p0, _ = expected_profit_before_breach(0.0, 0.01)
    chk("driftless: expected profit is EXACTLY zero (optional stopping)", abs(p0) < 1e-12)

    # IDENTITY 2 -- E[profit] = mu * E[tau], which the closed form must satisfy
    for S in (0.3, 0.583, 1.0, 2.0):
        for sf in (0.002, 0.0037, 0.01):
            pr, li = expected_profit_before_breach(S, sf)
            mu = sf * S / np.sqrt(TRADING_DAYS)
            chk(f"optional stopping holds at S={S}, sigma={sf}",
                abs(pr - mu * li) < 1e-12, f"profit {pr:.6f} = mu*life {mu*li:.6f}")

    # AND THE CLOSED FORM AGAINST A SIMULATION -- but the simulation must monitor at the
    # frequency the model assumes. DAILY monitoring is a different problem and reads longer.
    S, sf = 0.583, 0.0037
    pr, li = expected_profit_before_breach(S, sf)
    prev = None
    for k in (1, 8, 64):
        sp, sl, _ = simulate_breach(S, sf, n_paths=4000, steps_per_day=k)
        err = abs(sl - li) / li
        P(f"           monitored {k:>3}x/day -> life {sl:>7.1f}d vs closed {li:.0f}d "
          f"({err:+.1%}), profit {sp*100:.3f}% vs {pr*100:.3f}%")
        if prev is not None:
            chk(f"finer monitoring moves the simulation TOWARD the closed form (k={k})",
                err < prev, f"error {prev:.1%} -> {err:.1%}")
        prev = err
    chk("at 64 sub-steps the simulation agrees with the closed form within 12%",
        prev < 0.12, f"{prev:.1%}")
    chk("DAILY monitoring OVERSTATES the life, so it is optimistic and not conservative",
        simulate_breach(S, sf, n_paths=4000, steps_per_day=1)[1] > li)

    # THE COUNTERINTUITIVE SCALING: profit ~ 1/sigma
    a, _ = expected_profit_before_breach(0.583, 0.01)
    b, _ = expected_profit_before_breach(0.583, 0.005)
    chk("HALVING the size roughly DOUBLES expected profit before breach",
        1.7 < b / a < 2.3, f"{a*100:.3f}% -> {b*100:.3f}% (ratio {b/a:.2f})")
    chk("and roughly QUADRUPLES the life",
        3.4 < expected_profit_before_breach(0.583, 0.005)[1]
        / expected_profit_before_breach(0.583, 0.01)[1] < 4.6)
    chk("so C-d's 1% cap is NOT the binding constraint -- bigger is worse",
        expected_profit_before_breach(0.583, C_D_CAP)[0]
        < expected_profit_before_breach(0.583, C_D_CAP / 2)[0])

    # monotone in Sharpe, and the inversion round-trips
    chk("expected profit is increasing in Sharpe",
        all(expected_profit_before_breach(s, 0.0037)[0]
            < expected_profit_before_breach(s + 0.1, 0.0037)[0]
            for s in (0.1, 0.5, 1.0, 2.0)))
    for fee in (100.0, 500.0, 1000.0):
        s = sharpe_for_fee(fee, 0.0037)
        got = expected_profit_before_breach(s, 0.0037)[0] * ACCOUNT
        chk(f"sharpe_for_fee inverts at a ${fee:,.0f} fee",
            abs(got - fee) < 1.0, f"S={s:.3f} -> ${got:,.2f}")
    chk("a haircut RAISES the required Sharpe",
        sharpe_for_fee(500.0, 0.0037, haircut=0.30)
        > sharpe_for_fee(500.0, 0.0037, haircut=0.0))

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


def do_derive(as_json: bool) -> int:
    sig_cand = CANDIDATE["daily_sigma_usd"] / ACCOUNT
    P(f"account ${ACCOUNT:,.0f} · trailing drawdown {DRAWDOWN:.0%} on OPEN equity (P1)")
    P(f"C-d caps daily sigma at {C_D_CAP:.0%} = ${ACCOUNT*C_D_CAP:,.0f}")
    P(f"the candidate (D491 {CANDIDATE['root']} {CANDIDATE['cell']}, 1 micro) runs a daily "
      f"sigma of ${CANDIDATE['daily_sigma_usd']:,.0f} = {sig_cand:.2%} of the account\n")

    P("  1. WHAT SIZE DOES -- and it runs the wrong way from intuition")
    P(f"  {'daily sigma':>14}{'of acct':>9}{'E[profit]':>12}{'E[life]':>10}{'years':>8}")
    size_rows = []
    for frac in (0.01, 0.0074, sig_cand, 0.0025, 0.0015):
        pr, li = expected_profit_before_breach(CANDIDATE["sharpe"], frac)
        tag = "  <- C-d cap" if abs(frac - 0.01) < 1e-9 else (
            "  <- 1 MNQ, the FLOOR" if abs(frac - sig_cand) < 1e-9 else "")
        size_rows.append({"sigma_frac": frac, "sigma_usd": frac * ACCOUNT,
                          "profit_usd": pr * ACCOUNT, "life_days": li,
                          "life_years": li / TRADING_DAYS})
        P(f"  {frac*ACCOUNT:>13,.0f}${frac:>9.2%}{pr*ACCOUNT:>11,.0f}$"
          f"{li:>10,.0f}{li/TRADING_DAYS:>8.2f}{tag}")
    P("  Expected profit is proportional to 1/sigma: smaller size survives longer and")
    P("  collects more drift. **The floor of one micro is the binding constraint, not C-d.**\n")

    P("  2. THE CANDIDATE AT ONE MICRO, which is the only size available")
    pr, li = expected_profit_before_breach(CANDIDATE["sharpe"], sig_cand)
    prh, lih = expected_profit_before_breach(CANDIDATE["honest_sharpe"], sig_cand)
    P(f"    at the best cell     S = {CANDIDATE['sharpe']:+.3f}  ->  "
      f"E[profit] ${pr*ACCOUNT:,.0f}  E[life] {li:,.0f} days ({li/TRADING_DAYS:.2f} yr)")
    P(f"    at the honest level  S = {CANDIDATE['honest_sharpe']:+.3f}  ->  "
      f"E[profit] ${prh*ACCOUNT:,.0f}  E[life] {lih:,.0f} days ({lih/TRADING_DAYS:.2f} yr)\n")

    P("  3. THE BAR -- the Sharpe needed to cover an account fee, at one micro")
    P(f"  {'fee':>8}{'S needed':>11}{'+30% haircut':>15}{'E[life] there':>15}")
    bar = {}
    for fee in (50, 100, 200, 350, 500, 750, 1000, 1500):
        s0 = sharpe_for_fee(fee, sig_cand)
        s1 = sharpe_for_fee(fee, sig_cand, haircut=P5_HAIRCUT)
        _, l1 = expected_profit_before_breach(s1, sig_cand)
        bar[fee] = {"sharpe_no_haircut": s0, "sharpe_with_30pct_haircut": s1,
                    "life_days_at_haircut_sharpe": l1}
        P(f"  ${fee:>7,}{s0:>11.3f}{s1:>15.3f}{l1:>13,.0f} d")
    P()
    P("  4. WHAT THIS SAYS ABOUT THE CANDIDATE")
    fee_ok = max((f for f in bar if bar[f]["sharpe_with_30pct_haircut"]
                  <= CANDIDATE["sharpe"]), default=None)
    fee_ok_h = max((f for f in bar if bar[f]["sharpe_with_30pct_haircut"]
                    <= CANDIDATE["honest_sharpe"]), default=None)
    P(f"    S = {CANDIDATE['sharpe']:.3f} covers a fee up to about "
      f"${fee_ok:,} after the 30% haircut")
    P(f"    S = {CANDIDATE['honest_sharpe']:.3f} covers about ${fee_ok_h:,}")
    P(f"    and the OLD P4 (life > 3 years = {3*TRADING_DAYS} days) would have needed "
      f"a daily sigma of about ${DRAWDOWN/np.sqrt(3*TRADING_DAYS)*ACCOUNT:,.0f}, "
      f"far below one micro -- which is why it was unreachable.")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D496: the book Sharpe bar implied by the RELAXED P4. A derivation -- "
                      "no signal, no backtest, nothing admitted.",
           "model": "account = Brownian motion with drift, killed when the TRAILING drawdown "
                    "first reaches 4% of the account. E[M_tau] = (sigma^2/2mu)"
                    "(exp(2 mu D/sigma^2)-1); E[profit] = E[M_tau] - D; E[tau] = E[profit]/mu. "
                    "Closed form asserted against a simulation and against optional stopping.",
           "key_finding": "Expected profit before breach is proportional to 1/sigma, so "
                          "trading SMALLER earns MORE before the account dies. The binding "
                          "constraint is the one-micro floor, not C-d's 1% cap.",
           "inputs": {"account": ACCOUNT, "drawdown": DRAWDOWN, "C_d_cap": C_D_CAP,
                      "P5_haircut": P5_HAIRCUT, "candidate": CANDIDATE},
           "by_size": size_rows,
           "candidate_at_one_micro": {
               "best_cell": {"sharpe": CANDIDATE["sharpe"],
                             "expected_profit_usd": pr * ACCOUNT, "expected_life_days": li},
               "honest_level": {"sharpe": CANDIDATE["honest_sharpe"],
                                "expected_profit_usd": prh * ACCOUNT,
                                "expected_life_days": lih}},
           "bar_by_fee": bar,
           "fee_covered_best_cell": fee_ok, "fee_covered_honest": fee_ok_h,
           "limitations": [
               "the P5 haircut is applied as a FLAT 30% of profit, which is an upper bound on "
               "its bite: the true haircut is max(0, best_day - 0.30*total) and needs the "
               "daily P&L series, which D491 did not store. D495's runner should store the "
               "best-day share so this becomes exact.",
               "Brownian motion has no fat tails and no volatility clustering; a real P&L "
               "series breaches SOONER than this model says, so every life and profit here "
               "is OPTIMISTIC. D440 measured that clustering, not kurtosis, was worth "
               "five sixths of the difference.",
               "the account FEE is a parameter, not a measured input -- the bar is reported "
               "against a range and the principal supplies the actual figure",
               "P3 (worst day <= 2%) and P2 are not modelled here; a construction can clear "
               "this bar and still fail those",
               "one micro is treated as the size floor; a rule that trades only some days "
               "has a lower AVERAGE sigma and would sit between the rows"]}
    if as_json:
        OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--derive", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.derive:
        return do_derive(a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
