# D379 — the prop account is a down-and-out call, and hurdle P is six screens with no objective function behind them

**Date:** 2026-09-08
**Kind:** **FRAMING.** This record makes **no measurement on any fixture.** It contains one toy
Monte Carlo, labelled as an illustration throughout, and one re-reading of a table this programme
already computed on real data. **No pre-registration is owed for a framing note; everything it
recommends needs one before it runs ([R8](../RULES.md#r8)).**

**Companion to [D375](D375-the-hurdle-audit-the-stage-one-gates-are-sound-and-hurdle-P-is-half-untested.md),**
which found hurdle P carrying three thresholds never computed and one that structurally cannot fail.
D375 audited whether the bars are *testable*. This asks a different question: **what are they bars
on, and what is the quantity they are approximating?**

---

## 0. Provenance, stated first because it is unflattering

The framing came out of a **YouTube transcript** — `[CLOSED] How Quant Finance Made Me $1.6M Trading
Prop Firms` — read under the review convention in [`youtube-lessons.md`](../youtube-lessons.md).
**The source is worth nothing as evidence and this record leans on none of it.** Its author presents
a 16-month live record as proof after correctly deriving `t = SR·√T` on screen, which by his own
hurdle gives **t = 1.15** against the t = 2 he says is the loosest defensible bar; he states he ran
"thousands" of uncounted backtests selecting patterns that had already worked, and never corrects
for it; and the whole thing terminates in a mentorship pitch. **His arithmetic on loss streaks and
t-statistics is exactly right** — P(≥4 losses in 100 at a 50% win rate) = 0.973 against his 97%,
0.810 against his 81%, 0.546 against his 55% — **and every strategy claim in the video carries no
number at all.**

**One idea in it is not recycled**, and it is the subject of this record. It arrived from a bad
source; it is kept because it survives being checked against **our own committed artifacts**, in §3,
which is the only reason it is here.

---

## 1. The framing

**A funded prop account is a down-and-out call.** Not by analogy — component for component:

| option | account |
|---|---|
| premium | evaluation fee + monthly subscription |
| underlying | cumulative trading P&L |
| strike | ~zero; you are paid a share of profit above it |
| **knock-out barrier** | the drawdown limit — extinguishes **all** future value, permanently |
| barrier monitoring | **continuous, on OPEN equity** — this is [P1](../RULES.md#r11) exactly |
| payoff **cap** | the payout ladder — so it is a **call spread**, not a call. §4 |
| path constraint on the payoff | consistency rules — this is **P5** |

Value therefore has two factors that pull against each other:

```
V  =  E[payouts | survival]  ×  P(survival)
```

**On own capital the second factor does not exist** — a dollar of P&L is a dollar, the objective is
linear in size, and only Kelly geometry bounds it. Here the objective is **non-linear in size, with
an interior optimum strictly below the unconstrained one.**

**This is what hurdle P is approximating and never states.** P1, P3 and P4 are thresholds on
components of `P(survival)`; P5 is a threshold on the shape of the payoff; none of them is a
statement about `V`, and **nothing in the prop track ranks candidates by anything.** Every one of
C1–C3 was screened pass/fail. A screen answers *is this eligible*. It does not answer *what should
this be sized at*, and it cannot order two eligible candidates.

---

## 2. Illustration — the barrier is what creates the optimum

**Toy GBM, not a study: no fixture, no null, iid normal daily P&L, 252 days, 400k paths.** It is here
to show a *shape*, and the shape is the only thing that should be read off it. Sharpe held **fixed at
1.0** in every row; only size varies; 4% trailing drawdown; 90% profit split.

| ann vol | P(survive) | **E[payout]** | E[P&L] with no barrier |
|---:|---:|---:|---:|
| 0.02 | 0.990 | 0.0195 | 0.0180 |
| 0.04 | 0.731 | 0.0355 | 0.0360 |
| **0.05** | 0.532 | **0.0369** ← peak | 0.0450 |
| 0.06 | 0.349 | 0.0328 | 0.0540 |
| 0.10 | 0.030 | 0.0066 | 0.0900 |
| 0.20 | 0.000 | 0.0000 | 0.1800 |

**The right column is monotone. The middle column peaks and then collapses.** The strategy is
identical in every row. Doubling size from the optimum destroys **82%** of the account's value while
doubling the P&L the same edge would have produced unconstrained.

**The uncomfortable implication for how effort is spent here:** no plausible improvement to a
Sharpe-1 edge recovers that 82%. In *this environment specifically*, sizing dominates edge work.
That is not true on the personal book and must not be carried across.

---

## 3. The programme already computed this objective and did not name it

**This is the part that does not depend on the toy.** [BOOK_PROP.md](../BOOK_PROP.md)'s C1-REOPENED
table, from [D260](D260-the-vol-targeted-overnight-hold.md) on the extended-hours fixture, carries a
column called **"profit before breach"**. That column **is** `E[payout]`, computed on real data:

| avg size | breach rate | **ann return** | **profit before breach** |
|---:|---:|---:|---:|
| **0.48x** | 0.06% | +4.41% | **28.20%** |
| 0.71x | 0.18% | +6.61% | 14.71% |
| 0.95x | 0.57% | +8.79% | 6.08% |
| 1.42x | 2.95% | +13.04% | 1.75% |

**Annual return rises monotonically with size. Value falls monotonically with size.** That is the
two-factor tension in §1, measured on our own fixture, and it was printed without comment.

**Two consequences, and both are live:**

1. **The optimum was never located.** Value is monotone decreasing across every size tested, so the
   maximum lies **at or below 0.48x — the boundary of the sweep.** The table was built to answer
   *"does it clear P4"*, so it stopped where the answer became yes. **The value-maximising size for
   C1 is unresolved and was never searched.**
2. **P4 and value are different objectives and can disagree.** P4 gates **expected life**. Value is
   life × rate. A candidate can clear P4 by dying slowly while earning nothing — which is precisely
   the failure mode BOOK_PROP already names for C1 standalone at +1.87%/yr and twenty accounts.

---

## 4. The payout cap resolves the degenerate case, and it cuts the other way

**§3 point 1 taken naively says "size to zero", which is obviously wrong.** The reason it is wrong is
already in BOOK_PROP, one line below the table: at 0.48x the expected 28.20% "**comfortably exceeds
the payout ladders these firms cap at**".

**So the payoff is capped, and the instrument is a down-and-out call SPREAD.** Past the ladder,
additional profit-before-breach is worth **zero** — sizing lower only buys account life you cannot
monetise.

> **The value-maximising size is the smallest size that reaches the payout ladder with high
> probability — not the smallest size that survives.**

**That is a different quantity from anything hurdle P computes,** it is computable from artifacts
D260 already produced, and it needs the ladder terms as an input — which this programme has never
recorded for any venue.

---

## 5. A prediction I made and the illustration falsified

**Stated before running it:** the marginal value of a volatile but +EV trade should turn **negative**
as the buffer shrinks, since it risks an account with value left in it.

**It does the opposite.** Paired draws (common random numbers, so the difference is a paired estimate
— SE ≈ 0.00006), one extra trade of mean +0.40% and sd 2.00%, at the vol optimum:

| buffer left | ΔE[payout] | ΔP(survive) |
|---:|---:|---:|
| 4.00% | +0.00087 | −0.036 |
| 2.00% | +0.00004 | −0.045 |
| 1.00% | +0.00340 | +0.011 |
| **0.30%** | **+0.01008** | +0.098 |

**The trade is worth 12× more with 0.3% of room left than with the full 4%.** Because a down-and-out
call near its barrier is nearly worthless, the downside is *already* truncated, and variance becomes
free. This is **gambling for resurrection**, the standard risk-shifting result for any knocked-out
claim, and it is a property of the instrument rather than a defect of the toy.

**It retro-justifies two hurdles this programme adopted from venue terms without a mechanism.**
[D375](D375-the-hurdle-audit-the-stage-one-gates-are-sound-and-hurdle-P-is-half-untested.md) records
P3 and P5 as **never computed on anything**. They are not arbitrary friction:

> **P3 (daily loss limit) and P5 (no day > 40% of trailing-year profit) are the firm's defence
> against the convexity of the instrument it sold you.**

**And that has a direct consequence for screening:** a construction tuned to exploit near-barrier
convexity would **clear P1 and P4 and be killed by P5** — so P5 cannot be left uncomputed while
P1/P4 are treated as the binding pair. It is the one hurdle that binds against the account's own
incentive gradient.

---

## 6. What this does and does not change

**Does not change:**

- **No candidate is reopened.** [D258](D258-the-prop-track-candidates.md) fixed C1–C4 in advance and
  BOOK_PROP records all four resolved. **C2 and C3 have negative or sub-bar edges, and no valuation
  framework rescues a negative edge** — the same argument BOOK_PROP already makes against sizing C2.
- **Hurdle P stands as written.** This is not an amendment to [R11](../RULES.md#r11) and no threshold
  is loosened. Under [R6](../RULES.md#r6) the three uncomputed legs stay uncomputed.
- **Nothing here transfers to the personal book,** where there is no barrier and the objective is
  linear in size.

**Does change, all of it owed a pre-registration before it runs:**

1. **C1's size sweep is unfinished.** Extend below 0.48x and locate the value peak, against the
   ladder cap of §4 rather than against P4.
2. **Record the payout ladder terms** for MyFundedFutures. §4 is not computable without them, and no
   record here holds them.
3. **A future C5 should be ranked, not only screened.** `E[payout]` orders candidates; hurdle P only
   admits them. The two are not the same and the record has only ever done the second.
4. **P5 should be computed** on anything that reaches the prop track, ahead of the uncomputed legs
   D375 lists, for the reason in §5.

**One caveat that limits all four.** The closed form and the toy both assume iid normal returns.
Real intraday P&L is fat-tailed and autocorrelated, so **both understate ruin** — every valuation
built on this frame is optimistic, and BOOK_PROP's own C1 evidence is a case in point: its tail was
regime-driven, which no iid model produces.

**And the honest bound on the whole record: this is a valuation framework, not an edge.** It
allocates a strategy you have. **The prop candidate list is exhausted, so there is currently nothing
to value.**

---

## Artifacts

The §2 and §5 illustration is a toy with no fixture and is **deliberately not committed to `data/`**
— under CLAUDE.md's file contract, `data/` is for evidence a record quotes as measurement, and this
is neither. **Both tables are reproducible from their stated parameters** (400k paths, seeds 20260908
and 7, GBM, 252 days, 4% trailing DD, 90% split). **§3 and §4 quote
[BOOK_PROP.md](../BOOK_PROP.md) and [D260](D260-the-vol-targeted-overnight-hold.md), which carry
their own artifacts.**
