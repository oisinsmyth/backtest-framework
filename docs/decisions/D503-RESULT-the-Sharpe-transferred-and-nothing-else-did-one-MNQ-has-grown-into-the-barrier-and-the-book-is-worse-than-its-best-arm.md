# D503 — RESULT: the Sharpe transferred and **nothing else did**. One MNQ has grown into the barrier, and the book is **worse than its best arm**.

**2026-09-13.** Runner [`scripts/d503_forward_book.py`](../../scripts/d503_forward_book.py) ·
artifact [`data/d503_forward_book.json`](../../data/d503_forward_book.json) ·
K8's own guarded read [`data/d498_k8_forward.json`](../../data/d498_k8_forward.json) ·
pre-registration [D503 PRE-REG](D503-PRE-REG-the-one-pass-forward-read-K8-the-MACD-component-and-the-assembled-two-arm-book-on-the-sealed-2024-slice.md).

**THE HOLDOUT IS SPENT.** 2024-01-02 → 2026-09-09 on the NQ day session is now spent for both
components and for the book. 652 union sessions. **Nothing may be re-read, re-scored or
sharpened on it.**

**Nothing is admitted.** `BOOK_PROP.md` still has no arm.

---

## 1. The headline

| | in-sample | **forward** | |
|---|---:|---:|---|
| **MACD component, net Sharpe** | +0.723 | **+0.736** | transferred |
| MACD daily σ | $180 | **$340** | **+89%** |
| MACD skew | −0.05 | **+0.68** | flipped |
| MACD kurtosis | ~3 | **12.1** | |
| **K8, net Sharpe** | +0.595 | **−0.160** | **gone** |
| K8 gross per trade | +$17.87 | **−$4.46** | **gone** |
| **the assembled book, net Sharpe** | +0.856 | **+0.364** | **worse than its best arm** |
| ρ(MACD, K8) | +0.190 | **+0.197** | held, remarkably |

**One number transferred and it is the least informative one.**

## 2. The MACD component passes its declared rule and should not be trusted on it

**Verdict by the pre-registered rule: FULL** — net Sharpe +0.736 > C-a's +0.5, gross +$19.68 a
trade > 0. **Three things say otherwise, and all three were pre-registered as required
reporting.**

**It does not clear its own rotation null on the forward slice.**

| | observed | null p50 | null p95 | margin |
|---|---:|---:|---:|---:|
| MACD arm, signal rotated, 2,000 draws | +0.736 | −0.284 | **+0.758** | **−0.8 SE → UNRESOLVED** |

**The edge is carried by a handful of sessions.**

    sessions to half the P&L        3   (of 632)
    top 1 session                   25.9% of total P&L
    top 5 sessions                  80.9%
    top 10 sessions                 128.8%   -- so the other 622 sessions are net NEGATIVE
    mean per trade, net             +$16.18
    mean per trade, EX-TOP 1%       -$0.59   <-- remove six trades and the arm earns nothing
    mean per trade, trimmed both    +$11.33

**And the year split says it is not stationary**: 2024 **−$21**, 2025 **+$5,484**, 2026
**+$4,810**. The first forward year was flat.

This is precisely the pattern [[tail-carried per-trade edge does not book]] was written for, and
it is the opposite of the in-sample character — where skew was −0.05, the best day was 6.7% of
the total, and P5's haircut was zero. **Forward, the best day is 84.9% of the book's total and
P5's haircut is $4,383.**

## 3. K8 did not transfer, and its own rule keeps it alive on a technicality

From its own guarded command, on 308 trades:

    gross -$4.46 a trade (in-sample +$17.87)   hit 50.6% (was 57%)   net Sharpe -0.16 (was +0.595)
    after-down minus after-up  +0.2 bp, z +0.02   (in-sample z +2.89)
    total -$2,297   by year: 2024 -$3,506   2025 +$4,658   2026 -$3,449
    its own N1 null: p95 +7.7 bp against an observed +0.9 bp -- does NOT clear

**Verdict by D498 §3's rule: PROVISIONAL** — REMOVED requires net Sharpe < −0.3 *or* a negative
difference, and it reads −0.16 with a difference of +0.2 bp. **The rule says PROVISIONAL; the
evidence says the edge is gone.** A negative *gross* mean is the strongest possible statement of
non-transfer: this is not a cost failure, the signal itself stopped paying. I am recording the
rule's verdict as declared and my reading of it beside it, because the rule was pre-registered
and I will not rewrite it after seeing the number.

The instructive detail: **ES, the arm dismissed in-sample as "the same sign at half the size",
was the one that worked forward** (+4.4 bp, net Sharpe +0.22). That is what noise looks like.

## 4. The book is worse than its best arm, and that is arithmetic

| | MACD | K8 | **book** |
|---|---:|---:|---:|
| net Sharpe | +0.736 | −0.160 | **+0.364** |
| mean $/session | +15.76 | −3.52 | +12.23 |
| daily σ | $340 | $350 | **$534** |
| total | +$10,274 | −$2,297 | +$7,977 |
| max drawdown | $7,298 | $6,566 | **$9,932** |
| worst day | −$1,761 | −$1,825 | **−$2,724** |
| skew | +0.68 | +1.91 | **+3.10** |

**Layering only helps when the arms have comparable Sharpes.** `S·√k/√(1+(k−1)ρ)` assumes equal
S; add a −0.16 arm to a +0.736 arm and the sum is +0.364 whatever ρ does. **ρ behaved perfectly
(+0.197 forward against +0.190 in-sample, C-b cleared) and it did not help, because
decorrelation cannot rescue an arm with no edge.**

The book-level null confirms it from the other side: rotating K8's realised P&L against the
MACD's gives p50 **+0.398** against the observed **+0.364** — **the actual alignment of the two
arms is worse than a random alignment**, at −87.5 SE.

## 5. The real finding is not about either signal. One MNQ has grown into the barrier.

**Daily σ nearly doubled on an unchanged strategy: $180 → $340.** That is not the signal — it is
**the price level.** MNQ pays $2 an index point with a $0.50 tick, so as NQ's level roughly
doubled between the in-sample window and 2026, the same percentage move became twice the dollars
on the same one contract. The programme's own memory said this would happen:
[[the-15-minute-bar-is-only-viable-in-a-high-price-high-vol-regime]] — *never quote a futures
breakeven from a recent year; recompute E|M| in ticks year by year.* **I quoted C-d, P3 and P4
from a window averaging 2016–2023 price levels and they do not describe 2026.**

What that does to a $50,000 account with a $2,000 trailing floor:

| | MACD | K8 | book | bar |
|---|---:|---:|---:|---|
| **C-d** daily σ ≤ $500 | $340 PASS | $350 PASS | **$534 FAIL** | |
| **P3a** breaches/yr | **1.16 FAIL** | **3.87 FAIL** | **6.96 FAIL** | ≤ 1.0 |
| P3b life cost | 0.0% PASS | 15.1% PASS | 16.7% PASS | ≤ 33% |
| **P3c** worst day, share of the whole $2,000 budget | **88%** | **91%** | **136%** | reported |
| **empirical trailing-4% life** | **55 sessions** | 56 | **31 sessions** | |
| deaths in the 652-session slice | 11 | 11 | **20** | |

**The book's worst day is 136% of the account's entire loss budget — that single session ends the
account outright.** The empirical life is **31 sessions**: the book dies roughly every six weeks.
P4 gives $182 of expected profit before breach, which does not cover any venue's fee.

**And size cannot fix it**, which is [[fee-and-barrier-are-one-constraint]] arriving from the
other direction: D493 found the full contract too big, and now **the micro is too big as well**,
at 2026 price levels, for a 4%-of-$50k floor. There is nothing smaller than one MNQ.

## 6. Verdicts, and what is admitted

| | verdict | by |
|---|---|---|
| **MACD component** | **FULL** | the rule declared in D503 §3 — and see §2 for why I do not trust it |
| **K8** | **PROVISIONAL** | D498 §3's own rule, unchanged |
| **the book** | **ASSEMBLED** (neither arm REMOVED) but **NOT ADMITTED** | it fails P3a by 7×, fails C-d, and its worst day exceeds the whole loss budget |

**`BOOK_PROP.md` gains no arm.** The single admission gate — hurdle P, all six, on the assembled
book — fails on P3a.

## 7. Predictions

| | prediction | outcome | |
|---|---|---|---|
| **V-a** | both arms positive but lower | **BROKEN** | MACD was *higher* (+0.736); K8 went negative |
| **V-b** | MACD lands PROVISIONAL, Sharpe in (0, 0.5) | **BROKEN** | FULL at +0.736 |
| **V-c** | K8 lands FULL | **BROKEN** | PROVISIONAL, with negative gross |
| **V-d** | the book beats both arms | **BROKEN** | +0.364 against the MACD's +0.736 |
| **V-e** | forward ρ stays below 0.3 | **HELD** | +0.197 against +0.190 — the most stable number in the read |
| **V-f** | the book FAILS P3a | **HELD** | 6.96/yr against a bar of 1.0 |
| **V-g** | empirical life beats the Brownian estimate | **HELD** | 55 against 42 sessions on the arm; 31 against 15 on the book |

**Four of seven broken, and the three that held are the three about risk.** Every prediction I
made about *edge* was wrong in some direction; every prediction about *structure* — correlation,
daily limits, the barrier model's bias — held. That is worth remembering about which parts of
this programme's model are load-bearing.

## 8. Checks

18 checks, all passing, plus three in-run gates that would have stopped the read:

- **The holdout boundary raises** if any session before 2024-01-02 or after 2026-09-09 reaches
  the P&L path. 230 warm-up sessions were dropped from P&L and used only to warm the filters.
- **`simulate_trades` is asserted bit-identical to D491's `simulate`** on per-session P&L *and*
  trip count, and raises otherwise — the per-trade distribution in §2 is otherwise unverifiable.
- **K8's two artifacts are cross-checked** — trade CSV against JSON, on both the gross mean and
  the trade count — so its numbers come from its own guarded read by two paths, not from a
  reimplementation of mine.

**One assertion of mine was wrong and the code was right.** I asserted every hold satisfies the
5-segment minimum; it fired on a 1-segment hold. The forced 16:00 flatten (P2) legitimately
overrides the minimum hold, so the real invariant is *signal* exits ≥ M with the flatten exempt.
Rewritten that way, with both branches checked and the flatten proven to produce shorter holds.

**Two slips in the run itself**, both reporting-path bugs caught by crashes after the read: a
wrong key into K8's artifact, and dollars passed to a helper that works in account-fraction
units. Neither touched a number that had already printed; §7's block was produced by completing
the same pre-registered read with no change to its specification.

## 9. CORRECTION, 2026-09-13 — §2 overstated the case against the MACD component

**Added after the principal asked why I thought the component was not a fit.** §2 above stands as
written for the record, but **three of the things it leans on do not carry the weight I gave
them**, and one of them is a statistic this repo's own rules tell me not to lead with.

### 9a. I led with the asymmetric trim, which CLAUDE.md calls a flag and not a verdict

> *"Dropping only winners is a flag, not a verdict — on a two-sided fat-tailed book it always
> frightens."*

| per trade | |
|---|---:|
| raw mean | +$16.18 |
| **ex-top 1%** | **−$0.59** ← what §2 quoted |
| ex-bottom 1% | +$28.15 |
| **symmetric trim, both tails** | **+$11.33** |
| cost | $3.50 |

**The symmetric trim is 70% of the raw mean and 3.2× the cost**, and gross is 5.6× the cost. Both
tails are large and roughly offsetting — the textbook two-sided fat-tailed book the rule was
written about. **The edge survives symmetric trimming**, and §2 quoted the one number that
conceals that.

### 9b. "Does not clear its rotation null" is the absence of evidence, not evidence against

    652 sessions = 2.59 years  ->  Sharpe SE ~ 0.70
    observed +0.736            ->  1.05 SE from zero
    rotation null p50 -0.284, p95 +0.758  ->  spread 1.04, which IS that SE

**On 2.59 years a Sharpe of +0.74 cannot be distinguished from noise in either direction.** That
is a fact about the slice's length, not about the construction, and §2 presented it as though the
null had returned a verdict.

### 9c. P3a's failure is against a bar calibrated one day earlier from stale prices

The arm reads **P3a 1.16/yr against a bar of 1.0 — a 16% miss** — while **P3b, the substantive
half of the amended rule, reads 0.0%: the breaches cost the account no life at all.** The 1.0 bar
was set on 2026-09-13 from an in-sample rate of 0.27/yr measured at roughly **half** today's index
level (§5's point turned against my own hurdle).

### 9d. And the economics, which §1–§8 never computed

Run as replaceable accounts over the forward slice — profit realised inside each life, every fee
paid, a breach forfeiting what was still open:

    11 dead lives, realised          +$6,372     (5 of the 11 ended negative)
    the still-open life              +$3,902
    11 account fees x $209           -$2,299
    NET over 2.51 years              +$7,975  =  ~$3,180/yr  =  6.4% on $50k
    mean realised per dead life         $579  against a $209 fee

**Under the relaxed P4 that is a pass, not a failure**, and no section above said so.

**The caveat that actually decides it:** this accounting assumes profit is *withdrawn* before the
breach. One life made **$7,671 in 39 sessions** and carries most of the total. Whether it works
therefore turns on whether MyFundedFutures' withdrawal mechanics permit banking inside a
~53-session life — **a terms question, not a data question, and those pages have not been read.**

### 9e. The corrected position

**What fails is the vehicle, not the signal.** §5's notional table is the whole argument: one MNQ
was 0.18× a $50k account in 2016 and is **1.10×** in 2026, behind a stop 3.6% wide. At σ $340 a
one-year expected life needs a floor of ~$5,400 — a **~$135k account at 4%**.

**So: the component is marginal at $50k/4% and a reasonable fit at roughly $135k-at-4% or any
floor above ~$5,400. It is not disqualified, and §2 should not have been written as though the
tail statistics disqualified it.** Full per-year history in
[D504](D504-the-MACD-arm-across-every-year-the-fixture-holds.md).

## 10. What this does not do

- **It does not close the construction.** Only the principal closes an avenue. What it closes is
  *this account geometry*: one MNQ, $50k, 4% trailing, at 2026 price levels.
- **It does not blame the signal for §5.** Gross per trade is +$19.68 forward against a $3.50
  cost. The signal pays; the *barrier* does not fit the contract any more.
- **It does not test netting or weighting.** An un-netted two-arm book is what the two frozen
  specifications produce side by side. A netted book pays less cost and would have a different
  σ — untested, and it cannot repair a −0.16 arm.
- Fills remain open-of-next-segment / open-plus-a-tick at the measured half-spread. **The worst
  day, which P3 reads, is the figure most exposed to that optimism**, so −$2,724 is an upper
  bound on the P&L and a lower bound on the breach.
