"""D386 -- the DISTRIBUTION of extraction, not just its mean. CLAUDE.md reporting group 2.

    uv run python scripts/d386_extraction_distribution.py --selftest
    uv run python scripts/d386_extraction_distribution.py --report

WHY. D386 reports E[extracted] = b and stops there. A mean without its median is not a result --
and this distribution is about as skewed as they come, because extraction is a product of survival
probabilities. "Most funded accounts extract nothing, a few extract several times the buffer" was
asserted in the record and never computed. This computes it.

THE DISTRIBUTION IS EXACT, NOT SIMULATED. Under the renewal model the trader either survives cycle
k or does not, so extraction is supported on the partial sums of the cap schedule:

    P(exactly k payouts) = (PROD_{j<=k} p_j) * (1 - p_{k+1})     for k < n_max
    P(exactly n_max)     =  PROD_{j<=n_max} p_j
    extraction at k      =  SUM_{j<=k} c_j

with p_j the drifted two-sided exit probability, b/(b+c_j) at zero edge.

THREE CONDITIONING LEVELS, all reported, because they differ by an order of magnitude and the
sector quotes whichever flatters:

    1. given the funded floor has LOCKED       -- the renewal model's own frame
    2. given FUNDED                            -- adds P(reach the lock); failing it extracts $0
    3. per EVALUATION PURCHASED                -- adds P(pass); this is what a buyer actually faces

SCOPE. Apex only. Apex's funded floor locks at start + $100 and does not move, and the Safety Net
"must be maintained for the lifetime of the Performance Account" -- which is exactly the constant-b
renewal this models. TOPSTEP IS DELIBERATELY EXCLUDED: lane 02 found that a payout there sets the
MLL to $0 and "the remaining balance becomes your effective loss floor", so the buffer is NOT
constant across cycles and the renewal model does not describe it. D386 §2's Topstep column used a
constant b = $2,000 and that is a stated limitation of it, not a result.
"""

from __future__ import annotations

import argparse
import math
import sys

sys.path.insert(0, "scripts")
from d386_account_value import APEX_50K_EOD, APEX_150K_EOD, e_extracted  # noqa: E402

ACCOUNTS = (APEX_50K_EOD, APEX_150K_EOD)

# P(reach the lock) at zero edge, from temp/d386_prelock.py, 150k paths each
P_LOCK = {"Apex 50K EOD": 0.3743, "Apex 150K EOD": 0.3936}
# and at Sharpe 1.0, from scripts/d386_required_edge.py
P_LOCK_S1 = {"Apex 50K EOD": 0.5843, "Apex 150K EOD": 0.5372}
P_PASS_S1 = {"Apex 50K EOD": 0.4689, "Apex 150K EOD": 0.2652}


def distribution(buffer: float, caps, drift_ratio: float = 0.0):
    """Exact pmf over extraction. Returns [(extraction, probability), ...] from 0 payouts up."""
    _, ps = e_extracted(buffer, caps, drift_ratio)
    out, prod, cum = [], 1.0, 0.0
    out.append((0.0, 1.0 - ps[0]))
    for k, (c, p) in enumerate(zip(caps, ps)):
        prod *= p
        cum += c
        nxt = ps[k + 1] if k + 1 < len(ps) else 0.0
        out.append((cum, prod * (1.0 - nxt)))
    return out


def _quantile(pmf, q: float) -> float:
    acc = 0.0
    for v, p in pmf:
        acc += p
        if acc >= q - 1e-12:
            return v
    return pmf[-1][0]


def summarise(pmf, scale: float = 1.0):
    """scale multiplies the probability of every NON-zero outcome, the rest going to zero."""
    if scale != 1.0:
        head = [(0.0, 1.0 - scale * (1.0 - pmf[0][1]))]
        pmf = head + [(v, p * scale) for v, p in pmf[1:]]
    mean = sum(v * p for v, p in pmf)
    return {
        "mean": mean,
        "median": _quantile(pmf, 0.50),
        "p25": _quantile(pmf, 0.25), "p75": _quantile(pmf, 0.75),
        "p90": _quantile(pmf, 0.90), "p95": _quantile(pmf, 0.95),
        "p_zero": pmf[0][1],
        "top10_share": (sum(v * p for v, p in pmf if p > 0 and v >= _quantile(pmf, 0.90))
                        / mean if mean > 0 else float("nan")),
        "pmf": pmf,
    }


def selftest() -> int:
    fails = []

    def check(tag, ok, detail):
        print(f"  [{tag}] {'PASS' if ok else 'FAIL'}  {detail}")
        if not ok:
            fails.append(tag)

    print("D386 extraction-distribution self-test\n")

    # [SUM] a pmf must sum to 1
    for b, caps in ((2000.0, APEX_50K_EOD.caps), (4005.0, APEX_150K_EOD.caps),
                    (2000.0, (1500.0,) * 12)):
        s = sum(p for _, p in distribution(b, caps))
        check("SUM", abs(s - 1.0) < 1e-12, f"b={b:,.0f}, {len(caps)} caps -> sum {s:.12f}")

    # [MEAN] the pmf's mean must equal the closed form it was built from
    for b, caps in ((2000.0, APEX_50K_EOD.caps), (4005.0, APEX_150K_EOD.caps)):
        cf, _ = e_extracted(b, caps)
        m = sum(v * p for v, p in distribution(b, caps))
        check("MEAN", abs(cf - m) < 1e-9, f"closed form {cf:,.2f} vs pmf mean {m:,.2f}")

    # [SKEW] the whole point: the median must sit strictly below the mean
    d = summarise(distribution(2000.0, APEX_50K_EOD.caps))
    check("SKEW", d["median"] < d["mean"],
          f"Apex 50K given lock: median ${d['median']:,.0f} < mean ${d['mean']:,.0f}")

    # [DRIFT] edge must lift the median, weakly
    a = summarise(distribution(2000.0, APEX_50K_EOD.caps, 0.0))["median"]
    b_ = summarise(distribution(2000.0, APEX_50K_EOD.caps, 0.0005))["median"]
    check("DRIFT", b_ >= a, f"median at theta 0 ${a:,.0f} -> at theta 5e-4 ${b_:,.0f}")

    # must be able to fail
    check("CAN-FAIL", not (d["median"] > d["mean"]),
          "a symmetric distribution would put median at the mean; this one does not")

    print()
    if fails:
        print(f"FAILED: {', '.join(fails)}")
        return 1
    print("all assertions passed")
    return 0


def report() -> int:
    print("D386 -- THE DISTRIBUTION OF EXTRACTION\n")
    print("Apex only. Topstep is excluded: a payout there sets the MLL to $0, so the buffer is")
    print("not constant across cycles and this renewal model does not describe it.\n")

    for a in ACCOUNTS:
        fees = a.fee_eval + a.fee_activation
        fees_d = a.fee_eval_net + a.fee_activation
        print(f"=== {a.name} — buffer ${a.buffer:,.0f}, caps {[int(c) for c in a.caps]} ===")
        for label, scale, sharpe in (
            ("1. given the floor has LOCKED", 1.0, 0.0),
            ("2. given FUNDED", P_LOCK[a.name], 0.0),
            ("3. per EVALUATION PURCHASED", P_LOCK[a.name] * a.pass_rate, 0.0),
            ("3b. per EVALUATION, at Sharpe 1.0", P_LOCK_S1[a.name] * P_PASS_S1[a.name], 1.0),
        ):
            theta = 0.0
            if sharpe:
                vol = 250.0 if "50K" in a.name else 750.0
                theta = 2.0 * (sharpe * vol / math.sqrt(252.0)) / vol ** 2
            d = summarise(distribution(a.buffer, a.caps, theta), scale)
            print(f"  {label}")
            print(f"      P(extract $0) {d['p_zero']:>7.1%}   median ${d['median']:>8,.0f}   "
                  f"mean ${d['mean']:>8,.0f}   p90 ${d['p90']:>8,.0f}   p95 ${d['p95']:>8,.0f}")
            print(f"      mean/median {'INFINITE' if d['median'] == 0 else f'{d['mean']/d['median']:.2f}x':>8}"
                  f"   top-decile share of all extraction {d['top10_share']:>6.1%}")
        print(f"  fees per evaluation: ${fees:,.0f} at list, ${fees_d:,.0f} discounted")
        pmf = summarise(distribution(a.buffer, a.caps), P_LOCK[a.name] * a.pass_rate)["pmf"]
        for tag, f in (("list", fees), ("discounted", fees_d)):
            p_win = sum(p for v, p in pmf if v > f)
            print(f"      P(an evaluation returns more than its {tag} fees) = {p_win:.1%}")
        print()
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
