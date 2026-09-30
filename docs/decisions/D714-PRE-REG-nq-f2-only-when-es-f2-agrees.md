# D714 PRE-REGISTRATION — an in-sample test: trade NQ F2 only when ES F2 also takes, in the same direction. Does requiring ES's agreement beat dropping the same number of NQ trades at random?

*2026-09-30.*
- *The principal: "I would like one in sample test, to trade NQ- only when last construction agrees to trade on both NQ
  and ES?"*
- *Numbered D714: D713 is the highest on every branch, and the other session was told before writing.*
- ***Committed alone, before its runner exists.** In-sample to 2023-12-29; nothing dated 2024-01-01 or later is read.*

## 0. What this can and cannot show (read first)

**The rule was found by looking.** D711's first addendum split NQ F2's trades by whether ES F2 also took them, and
those numbers are already on record:

| NQ F2 trades | n | NQ net a trade |
|---|---:|---:|
| on days ES also takes (any direction) | 217 | +$24.43 |
| on days ES also takes, same direction | 216 | +$25.58 |
| on days only NQ takes | 52 | +$4.29 |

**So this record cannot "discover" the rule's in-sample mean.** Its one honest question is:

> Is dropping the NQ-only days better than dropping the same NUMBER of NQ F2 trades at random?

- If not, the agreement rule is ordinary sampling luck in a 52-trade split, and not worth carrying anywhere.
- **If it is, the rule is still in-sample and post hoc.** A PASS here makes it worth a look on unseen data, on the
  principal's word. **It does not make it a result.**
- **Nothing here touches D707** (ES F2's vault look) or any programme slot.

## 1. The objects

- **The base book B: NQ F2**, exactly D711 §1 at 15:30 on NQ (one MNQ, $4.07 a round trip):
  - its trades from **2018-05-14** (the start of the ES/NQ common window in D711's addenda) to 2023-12-29;
  - about 270 trades.
- **ES F2** is exactly D707 §1, reproduced by D711's generic loader against D707's frozen answer.
- **The agreement book A:** the trades of B on sessions where **ES F2 takes and sign(F5_ES) = sign(F5_NQ)**.
  - A session where ES is not a candidate counts as no agreement: a roll day, a short session, or F5_ES = 0.
  - About 216 trades.
- **The dropped set** is B minus A.

## 2. The test

**The null: count-matched random deletion.**
- Draw 20,000 random subsets of B, each of size |A|, without replacement (seed 714).
- Each subset keeps B's trades, sizes and time spread. Only the choice of which ones to drop is random.

**The statistic, gating: direction efficiency E = Σ net / Σ |net|** of the book.
- **This follows D711-A1's lesson.** Agreement days may be bigger-move days, and a mean-P&L statistic against
  ordinary-size random subsets would then be anti-conservative. E is size-invariant.
- The mean net is reported against the same null.

**The verdict:**

| verdict | condition |
|---|---|
| **INCREMENT** | E(A) > the null's p95 of E, **and** mean net(A) > mean net(B) |
| **UNRESOLVED** | E(A) exceeds the p95 by less than 2 of the p95's bootstrap SEs (D373's rule) |
| **NO INCREMENT** | otherwise |

## 3. Reported beside, never gating

- **For A, B, the dropped set and ES F2's own agreement book** (ES trades on the same agreement days):
  - the four reporting groups at one micro, net and gross side by side;
  - Sharpe with Sortino, per trade and daily; max drawdown;
  - hit, median and payoff; skew; the 1 / 5 / 10 % two-tailed trims;
  - by year and the 2022 share; before and after 2022-05-16; long against short.
- **The null on the mean net:** p50, p95 and A's rank.
- **The component line:** A's net daily Sharpe, ρ with ES F2 and with the MACD arm.
- **The per-year increment:** A's mean net minus B's, by calendar year.

## 4. The runner's assertions

- **Known answers:**
  - D707's frozen ES F2 answer (252 trades, +$13.208968);
  - D711's NQ 15:30 book on its own window (274 trades, +$20.670105 net);
  - D711 addendum 1's overlap counts (217 / 33 / 52).
- **The null:**
  - a subset of size |B| reproduces B exactly;
  - on synthetic data, a planted agreement label that picks winners gives INCREMENT;
  - a random label gives INCREMENT in about 5 % of worlds.
- **The seal:** no session ≥ 2024-01-01 is read.

## 5. Predictions

**The power, before the run** (B's per-trade sd is about $133):
- dropping 52 of about 270 trades at random moves the mean by an SE of about $3.9;
- A's expected lift over B is about $3.9;
- so **E(A) should rank near the 85th percentile, short of the 95th.**

| # | prediction |
|---|---|
| 1 | **NO INCREMENT:** A's efficiency ranks between 0.80 and 0.94 |
| 2 | A's mean net beats B's by $3–5 a trade |
| 3 | A holds up at a 10 % trim, as B does |
| 4 | A's 2022 share is above B's (67 %) |
