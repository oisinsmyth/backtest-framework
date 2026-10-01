# D752 STAGE 0 RESULT — NOTHING on both brackets: YM's open reversal does not carry a fade, and the high-win-rate bracket wins 60 % of trades with a median of +\$9.58 while losing \$5.47 a trade on average

*2026-10-01.*
- *Pre-registration: [D752](D752-STAGE-0-PRE-REG-the-ym-open-reversal-fade.md) (7af83e82).*
- *Runner: `scripts/stage0_d752_ym_open_fade.py` (8f159a51), committed before its one run.*
- *Output: `data/stage0_d752_ym_open_fade.json`.*
- *The known answers held exactly: D727's YM 11:00 β −0.047419 on 1,938 sessions, its first-crossing k1.0 book
  (1,450 / −\$3.842 gross), and its per-clock 11:00 k1.0 book (790 / −\$2.659). E0 is that book's exact mirror.
  D727's lag audit passed and its canary fired.*
- *790 sessions triggered (\|z₁₁\| ≥ 1.0) of 1,938, 2016-02-02 → 2023-12-29. One MYM at \$3.80.*

## 0. The readings

| | gross (median) | net | t | median net | win | skew | worst | years + | rotation p_high (p50, p95) | reading |
|---|---|---|---|---|---|---|---|---|---|---|
| **B1**, to the open, 1:1 | −\$1.23 (−\$0.50) | **−\$5.03** | −2.03 | −\$4.30 | 48.0 % | −0.09 | −\$267 | 1/8 | 0.659 (−0.17, +3.80); Holm 1.00 | **NOTHING** |
| **B2**, target 0.5 m, stop 1.0 m | −\$1.68 (**+\$13.38**) | **−\$5.47** | −2.68 | **+\$9.58** | **59.5 %** | **−0.99** | −\$267 | 2/8 | 0.663 (−0.92, +1.97); Holm 1.00 | **NOTHING** |
| E0, held to 15:59 (context; D727's mirror, read) | +\$2.66 (+\$0.50) | −\$1.14 | −0.32 | −\$3.30 | 48.2 % | +0.68 | −\$475 | 3/8 | 0.237 | — |

**The fade direction carries nothing.** Under both brackets the gross sits at the rotation's median: a random side
with the same clustering does as well. The held version's +\$2.66 (rank 0.76 in its own rotation) is D727's weak
reversal, already read, and does not pay the fee either.

**Each N criterion:**
- **N1** (net > 0 at t ≥ 2) fails on both brackets: the net is significantly **negative**.
- **N2** (median ≥ 0) holds on B2 only.
- **N3** (skew ≥ −0.5) holds on B1 only.
- **N4** (D736's G1–G3) fails on both: without their two best years, B1 is −\$789 a year and B2 −\$891 a year.

## 1. The high-win-rate question, answered by B2

**B2 is the shape the principal asked about ("lots of small net wins"):**
- **59.5 % of trades win;**
- the **median trade nets +\$9.58;**
- **the mean loses \$5.47.**

**Why:**
- The payoff is 0.53: the average loss is about twice the average win.
- The skew is −0.99, and the 1 % trims (ex-top −\$6.88, ex-bottom −\$3.26) show the left tail doing the work.
- How trades ended: 54 % at the target, 25 % at the stop, 21 % at the time exit. The stops pay for every target.

**The mechanism.** The win rate is the bracket's geometry, not the market's: the driftless value is about 2/3 (D528,
addendum 4). The fee and a slight drift against the fade take the rest. **A positive median beside a negative mean
is the signature of a bought win rate.**

## 2. The component line (one MYM, in-sample)

- **Net Sharpe:** B1 −0.73 (Sortino −0.97); B2 −0.96 (Sortino −1.14). Gross Sharpe −0.18 and −0.30.
- **Max drawdown:** \$4,201 and \$4,482.
- **Daily correlation:** with D737 +0.13 / +0.11; with C1 −0.05 / −0.04; with F2 −0.01.
- **Hedge exposure:** **D737 trades on 90 %** of the fade's sessions. D737 holds MNQ, so a live MYM fade would often
  sit against it, a correlated hedge at Apex. Even a GO would have needed a conflict rule.

## 3. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | E0 gross +\$1 to +\$4 | **held** (+\$2.66; read in D727, so not evidence) |
| P2 | B1 NOTHING, gross near 0 | **held** (−\$1.23; the bracket gives back the held fade's tail) |
| P3 | B2 wins 60–68 %, skew below −0.5, NOTHING | win 59.5 % (just under); skew −0.99 **held**; NOTHING **held** |
| P4 | no net mean above 0 at t ≥ 2 | **held** |
| | P(any GO) ≈ 0.05 | NOTHING |

## 4. What follows

- **The reopened closure stands again.** With D746 and D747, intraday mean reversion on the index micros is closed
  for the prop book. This record reopened it for one construction on the principal's word; that construction is
  NOTHING.
- **The principal's question gets a measured answer.** A high win rate with a positive median is available on demand
  from the bracket. On this market it comes with a negative mean and negative skew, the shape hurdle P's C-c and the
  never-kills rule exclude.
- **What does not change:**
  - D727's YM reversal stays a description. Its held mirror nets −\$1.14 and its rotation rank is 0.76.
  - D737 (which trades the NQ–YM divergence, not YM's own reversal) is untouched.

## 5. CLOSED

*2026-10-01, the principal: "close D752".*
- **D752 is closed:** no fade of YM's move since the open at 11:00, with either bracket.
- **Don't re-propose** a bracketed fade of an index micro's move since the open, on any target or stop geometry. The
  direction carries nothing (rotation p 0.66), and the brackets only trade the mean for the win rate.
- **The closure of intraday mean reversion on the index micros for the prop book (D746, D747) stands.** The
  multi-day ideas stay parked for the personal book.
- **A survey of every mean-reversion study since the repo began was commissioned with this closure,** on the
  principal's word. It is an inventory, not a reopening.
