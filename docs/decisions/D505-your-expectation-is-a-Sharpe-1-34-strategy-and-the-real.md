# D505 — your expectation is a **Sharpe-1.34** strategy; the magnitude half is already met; and the thing actually worth being unhappy about is that **four accounts in five pay nothing**

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D505-your-expectation-is-a-Sharpe-1-34-strategy-and-the-real-problem-is-that-four-accounts-in-five-pay-nothing.md`. The H1 above is the full title.*

**2026-09-13.** Runner [`scripts/d505_yearly_expectation_and_payout.py`](../../scripts/d505_yearly_expectation_and_payout.py) ·
artifact [`data/d505_yearly_expectation_and_payout.json`](../../data/d505_yearly_expectation_and_payout.json).

**An analysis of committed numbers, not a study.** No fixture read, no signal computed, no
parameter chosen. It reads [D504](D504-the-MACD-arm-across-every-year-the-fixture-holds.md)'s
artifact and runs [D386](../../scripts/d386_full_lifecycle.py)'s published-rules lifecycle model at
the arm's measured Sharpe and its **forced** size. Nothing admitted ([R15](../RULES.md#r15)).

The principal, on D504's yearly table:

> *"Not sure I am too happy about this result? Would you not expect the yearly profit break down
> to at minimum have only one negative and should be close to zero? Am I expecting too much?"*

---

## 1. The magnitude half of the expectation is already met

| year | total | % of $50k |
|---|---:|---:|
| 2016 | −$140 | **−0.28%** |
| 2017 | −$316 | **−0.63%** |
| 2019 | −$757 | **−1.51%** |
| 2023 | −$300 | **−0.60%** |
| 2024 | −$21 | **−0.04%** |
| **all five** | **−$1,533** | **−3.07%** |
| the six positive years | +$27,230 | +54.46% |

**Every negative year is inside 1.6% of the account, and all five together are 3.1%.** The worst
year in eleven loses $757. "Close to zero" is satisfied comfortably — that half of the
expectation is not the problem.

## 2. The count half describes a strategy roughly twice as good as this one

| | |
|---|---:|
| measured pooled Sharpe | **+0.698** |
| P(any given year negative) = Φ(−S) | **24.3%** |
| **expected** negative years in 11 | **2.67** |
| **observed** | **5** |
| P(≥ 5 negatives given S = 0.70) | **10.3% — not unusual** |
| Sharpe needed to *expect* ≤ 1 negative year in 11 | **≈ 1.34** |
| Sharpe needed to expect ≤ 0.5 | ≈ 1.69 |

**So: not an unreasonable thing to want, but it is a different strategy class.** At Sharpe 0.70
five negative years in eleven is an ordinary draw — the expectation is 2.67 and 5 sits at p = 10%,
nowhere near surprising.

**And "at most one negative year, close to zero" ≈ Sharpe 1.34 is precisely what CLAUDE.md's
layering arithmetic exists for**: five components at 0.4–0.6 with ρ < 0.3 reach ~1.5. **We have
one at 0.70.** The expectation is reachable by a *book* and not by this arm — which is what the
components ledger was built to do and what D503 showed we are four components short of.

**What should still bother you about the shape, and it is not the sign count:** 2020 + 2022 +
2025 + 2026 carry **96%** of the total. It is a regime construction. The flat years are not
cheap — see §3.

## 3. THE CORRECTION — and it supersedes what I told you twice

**D503 §9d and D504 §5 reported "+$21,935 net of fees, 4.4%/yr".** That summed the strategy's
realised P&L and subtracted one account fee per breach. **It is an upper bound on a quantity the
rules do not let you have.**

MyFundedFutures Rapid EOD, from D386's encoding of the published terms:

    fee $209  |  EVALUATION TARGET $3,000 first  |  funded dd $2,000
    safety net $2,000 you may NOT withdraw below  |  5 qualifying days at >= $150 each
    minimum payout $500

You must make **$3,000 inside a $2,000 trailing drawdown** merely to become funded; then you must
build past a **$2,000 safety net** before a cent can be withdrawn, with five qualifying days and a
$500 minimum. **D386 models every one of those**, and its output `V` is expected dollars *paid
out* minus fees, per evaluation purchased.

**The arm cannot choose its size — one MNQ is the floor — so volatility is given, not optimised:**

| scenario | Sharpe | vol | **V** | paid | **P(paid)** | **P(pass eval)** | med funded days |
|---|---:|---:|---:|---:|---:|---:|---:|
| **pooled 2016–2026** | +0.70 | $233 | **+$600** | $809 | **20.4%** | **43.2%** | 94 |
| in-sample 2016–23 | +0.72 | $180 | +$859 | $1,068 | 25.3% | 48.1% | 169 |
| 2026 alone | +1.20 | $386 | +$851 | $1,060 | 23.0% | 45.8% | 41 |
| 2025 alone | +0.96 | $391 | +$576 | $785 | 19.1% | 41.4% | 36 |
| **a flat year (2024)** | −0.01 | $256 | **+$14** | $223 | 8.3% | 26.1% | 59 |

**If size were free, D386 would choose a daily vol of $150 for V = $817. Being forced to $233
costs 27% of V** — and 2026's $386 is further still from the optimum. That is §4 of D504's
crossover, priced.

## 4. So here is what is actually worth being unhappy about

**Not the five negative years** — they are −0.04% to −1.51% of the account.
**Not five-of-eleven as a count** — the expectation is 2.67 and 5 has p = 10%.

**It is that P(passing the $3,000 evaluation) is 43% and P(ever being paid a cent) is 20%.**
Four accounts in five return nothing at all. V is **+$600 per $209 account** — positive, ~2.9× the
fee — but **the mode of the payout distribution is zero**, and a flat year like 2024 returns
**+$14** against a $209 outlay.

**That is the honest shape of the opportunity**, and it is a much better reason to be unhappy than
the yearly sign column. The strategy's edge is real (D504: +35 SE over its rotation null). What is
thin is the *vehicle's* conversion of that edge into withdrawn money.

## 5. Checks

16 checks, all passing. The ones that carry the argument:

- **The normal tail is anchored at known values** — Sharpe 0 → 50.0000% of years negative,
  Sharpe 1 → 15.8655%, Sharpe 2 → 2.2750% — so §2's inversion is not a free parameter.
- **The binomial tail is proven monotone in k, exactly 1 at k = 0, and exactly p¹¹ at k = 11**,
  and a 5-of-11 tail is proven *insignificant* at Sharpe 0.7 (p = 0.102) and *significant* at
  Sharpe 2 (p = 2.5 × 10⁻⁶) — the comparison §2 rests on.
- **The Sharpe inversion round-trips** to 1e-6 and is proven to move with the horizon, so it is
  not a constant being quoted as a derivation.
- **D386's MFFU plan is asserted to carry the four gates my earlier economics ignored** — the
  $3,000 target, the $2,000 safety net, 5 × $150 qualifying days, and the $500 minimum payout —
  and the run refuses to proceed if the plan does not match what `BOOK_PROP.md` names.
- **P(paid) ≤ P(pass) is asserted**: you cannot be paid without being funded.

## 6. Limitations

- **D386 simulates Brownian paths** at a given (Sharpe, vol). The real series is fat-tailed and
  regime-clustered, so a real account breaches **sooner** and **V above is optimistic** — D440
  found clustering, not kurtosis, carried five sixths of that gap.
- Every D386 parameter comes from its lane files; assumptions are marked there. **The terms pages
  themselves have not been re-read** for this record.
- D504's limitations carry: 2024+ is spent, fills are upper bounds, and a one-year Sharpe carries
  SE ≈ 1.0.
