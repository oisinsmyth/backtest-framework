# D322 — the four-group report, and where the P&L actually comes from

**Status:** REPORT. Scores no new rule, closes nothing, needs no pre-registration
(R8 does not apply).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

> **Provenance.** `scripts/d322_four_group_report.py` and
> `data/d322_four_group_report.json` were produced by a delegated agent working
> from a written brief. **This record was written from its data file** because the
> agent had not filed one; every number below is read out of that JSON. Its
> caveats are reproduced rather than summarised away.

---

## 0. Why this exists

CLAUDE.md mandates all four reporting groups, and **groups 2 and 3 have been
carried as "inherited from D310" since D313** — never computed for the book the
programme actually holds. D307's withdrawn "lottery book" verdict came from
exactly this analysis, so it is not optional before anything is taken further.

Two cells, fixed in advance: **BASE** = D306's `N=2/target`, and **BASE+dv28** =
the same with D321's dollar-volume exclusion. Costed per D318, turnover on the
names **held** per D321's `[F]`.

## 1. Group 1 — performance, net and gross

| | **BASE** | **BASE+dv28** |
|---|--:|--:|
| gross bp/bar | +32.89 | +32.93 |
| cost bp/bar | 18.33 | **14.56** |
| **net bp/bar** | **+14.57** | **+18.37** |
| vol bp/bar | 692.2 | 575.4 |
| **gross Sharpe** | +0.754 | **+0.908** |
| **net Sharpe** | +0.334 | **+0.507** |
| maxDD bp | 13,478 | 12,382 |
| exposure (bars in panel) | 76.1% | 72.8% |
| held per bar / fill | 4.00 / 100% | 3.66 / **91.5%** |
| turnover (held) | 0.2409 | 0.2391 |
| round trip: spread + commission | 73.25 + 2.83 | 58.15 + 2.74 |
| **mean move per trade vs `2c`** | 68.10 vs 38.04 = **1.79×** | 68.29 vs 30.44 = **2.24×** |
| **breakeven half-spread, bp/side** | **33.43** vs a held 18.31 | **33.74** vs a held 14.54 |
| **breakeven multiple** | **1.83×** | **2.32×** |
| held price / held dollar volume | $70.70 / $40.1M | $73.02 / $60.5M |

**Both cells clear `2c` and both have real headroom on the spread** — the book
tolerates 33.4 bp/side against the 18.3 it faces. **dv28's fill is 91.5%**, so it
is mildly confounded with width; the numbers above already use held-name turnover,
which prices that.

## 2. Group 2 — the trade distribution, and the book SURVIVES it

| | BASE | BASE+dv28 |
|---|--:|--:|
| trades | 3,067 | 2,734 |
| **mean** | **+68.10** | +68.29 |
| **median** | **+94.40** | +88.44 |
| **mean below median?** | **YES** | **YES** |
| ex-top-1% | +2.51 | +12.75 |
| ex-bottom-1% | +117.83 | +101.89 |
| **symmetric trim (1% both tails)** | **+52.08** | **+46.13** |
| win rate | 56.2% | 56.0% |
| payoff | 0.984 | 1.040 |
| holding run mean / median / max | 4.15 / 5 / 5 | 4.18 / 5 / 5 |
| skew / kurtosis | 10.17 / 270.3 | 14.55 / 470.7 |
| top-1% share of P&L | +96.3% | +81.5% |
| bottom-1% share | −71.3% | −47.7% |

**The mean sits below the median in both cells** — CLAUDE.md's stated tell that
the *left* tail is doing the work, not the right. **And the symmetric trim is
strongly positive at +52.08 and +46.13.**

**This is not a lottery book**, and D307's withdrawn verdict is confirmed
withdrawn on the current construction. A one-sided trim would read ex-top-1% at
+2.51 and call it carried by its winners; the two-sided trim shows the central
mass earning +52 bp against a raw +68, with a 56% win rate and a payoff near 1.0.

**It is violently fat-tailed on both sides** — skew 10.2, kurtosis 270 — and that
is a sizing fact, not a validity problem.

## 3. Group 3 — TWO PROBLEMS, and they are the report's real output

### 3a. Six names of 718 make half the P&L

| | BASE | BASE+dv28 |
|---|--:|--:|
| distinct names traded | 718 | 650 |
| **names to reach half the P&L** | **6** | **7** |
| top-1 name share | 17.1% | 17.1% |
| top-5 name share | 47.5% | 45.8% |
| top-10 name share | 64.7% | 58.9% |

**One name is 17% of the P&L and ten names are 65% of it.** dv28 improves this
slightly and does not fix it.

### 3b. The P&L lives in the CHEAPEST names, where commission is 8× higher

| price tercile | share of P&L | mean bp/trade | median price | **commission rt** |
|---|--:|--:|--:|--:|
| **low** | **57.3%** | **+118.47** | $28.53 | **7.01 bp** |
| mid | 22.2% | +42.87 | — | — |
| high | 20.5% | +42.99 | $230.99 | **0.87 bp** |

**And dv28 makes this worse, not better:** its low tercile is **62.7%** of P&L at
a mean of **+134.54**.

**This is D284's grave.** That study died of discovering the price level, and
[D320](D320-RESULT-the-tilt-axis-closes-and-the-filters-were-width.md) guarded
against a filter that works by holding pricier names. **Here the edge itself is
concentrated in the low-price tercile**, where the per-share commission is
**8× the cost in basis points** — 7.01 against 0.87. The book is earning where it
is most expensive to trade.

**dv28 cuts the SPREAD without touching this.** It raises held dollar volume 40.1M
→ 60.5M and held price only $70.70 → $73.02, while *increasing* the low-tercile
share of P&L. **Whatever dv28 is doing, it is not de-risking the price
dependence.**

### 3c. What is healthy

- **Era: balanced.** First half 50.5% of P&L, second half 49.5%. No era
  dependence.
- **Dead names carry their weight and more.** 804 dead-name trades = 33.4% of P&L
  at a mean of **+75.95** against alive names' **+65.32**. The fixture's 596 dead
  names are *helping*, so this is not survivorship.
- **Years:** 11 of 14 profitable gross, **8 of 14 net** (BASE); 13 and 9 with
  dv28.

## 4. Group 4 — the nulls, distribution not percentile

Rank rotation inside the 25-name gate (D300/D306's construction), **re-run here**,
200 draws:

| | score | null p50 | **null p95** | **p** |
|---|--:|--:|--:|--:|
| **BASE** gross bp | +32.89 | +5.04 | +32.39 | **0.0050** |
| **BASE** gross Sharpe | +0.754 | +0.171 | **+0.955** | **0.0597** |
| **BASE** net Sharpe | +0.334 | −0.744 | +0.307 | **0.0050** |
| **+dv28** gross bp | +32.93 | +6.00 | +29.49 | **0.0050** |
| **+dv28** gross Sharpe | +0.908 | +0.165 | +0.886 | **0.0050** |
| **+dv28** net Sharpe | +0.507 | −0.562 | +0.283 | **0.0050** |

**BASE does NOT beat its rotation null on GROSS Sharpe** — 0.754 against a p95 of
0.955, p = 0.0597. **BASE+dv28 does**, at 0.908 against 0.886. That is a point in
dv28's favour that D321 could not see, because D321 scored net Sharpe only.

The null is decisive on the other statistics and is **not** the R7 pathology: its
gross-bp median is **positive** (+5.04, +6.00), so the rotated control makes money
and the book beats it anyway.

dv28's own exclusion-rotation null is **quoted from D321, not re-run**: p =
0.0100, +0.173 against a needed +0.112.

## 5. The ledger reconciles, with a residual that has a known cause

`pnl_over_contribution` = **2.0005** for BASE — trade P&L is twice the book
contribution, which is the two legs — and the residual is **0.1326 bp** (0.2107
with dv28). **That is the same shape as D307c's 0.1530 bp**, which was chased
through three fixes and turned out to be **positions still open at the end of the
run**, which the ledger never records. Reported, not chased again.

## 6. What this changes

**Group 2 clears and group 3 does not.** The book is not a lottery book, but:

1. **Six names of 718 make half the P&L.** Any capacity or robustness claim has to
   survive that, and it is the single most fragile number in the programme.
2. **57–63% of the P&L is in the cheapest third of names, where commission is 8×**
   — and **dv28 concentrates that dependence rather than relieving it.**

**Neither is a reason to stop; both are reasons that the next thing tested should
be the entry signal rather than another cost lever.** A cost lever that does not
move the price dependence is treating the symptom, and D323 is already running.

**Nothing is promoted. dv28 remains CARRIED, NOT PROMOTED** per D321's guard, and
§4 adds one point in its favour and §3b one against.

## 7. Files

`scripts/d322_four_group_report.py` · `data/d322_four_group_report.json`
