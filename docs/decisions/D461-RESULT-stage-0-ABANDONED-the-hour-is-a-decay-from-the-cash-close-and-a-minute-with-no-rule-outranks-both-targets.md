# D461 RESULT — stage 0 ABANDONED: the hour is a decay from the cash close, and a minute with no rule attached outranks both targets

**Pre-registration:** [`D461`](D461-PRE-REG-stage-0-prop-firm-forced-flow-at-the-flatten-minutes.md),
committed before the runner existed. **Runner:** `scripts/d461_flatten_flow.py`. **Fixture:**
`data/fixtures/micro_minute_volume.csv.gz` (693,524 root-minute-days, 2010-06-07 → 2026-09-09).
**Evidence:** `data/d461_flatten_flow.json`. **NO RETURN WAS READ.**

---

## THE ANSWER

> **`A1` FAILS. MES's 16:10 ranks 10th of 60 and 16:59 ranks 18th — neither in the declared top 5.
> ABANDONED at stage 0.**
>
> **And the reason is visible in one column: the 16:00–17:00 hour is a MONOTONE DECAY from the cash
> close. 16:00 alone is 21.05% of the hour. 16:10's "2.93× lift" is not a spike — it is where the
> decay curve happens to sit.**

## 1. The numbers

| cell | days | rank 16:10 | share | lift | rank 16:59 | share | lift |
|---|---:|---:|---:|---:|---:|---:|---:|
| **MES 2019–2026** | 1,832 | **10** | 2.35% | 2.93× | **18** | 1.24% | 1.55× |
| ES 2019–2026 | 1,917 | 11 | 2.34% | 4.24× | 17 | 1.32% | 2.39× |
| **ES 2010–2018** | 1,720 | **9** | 3.49% | **9.59×** | 17 | 0.80% | 2.20× |
| MNQ 2019–2026 | 1,832 | 10 | 2.66% | 2.87× | 23 | 1.17% | 1.26× |
| M2K 2019–2026 | 1,832 | 10 | 2.46% | 2.57× | 16 | 1.74% | 1.82× |
| MYM 2019–2026 | 1,831 | 10 | 2.42% | 2.62× | 18 | 1.67% | 1.80× |
| NQ 2019–2026 | 1,919 | 10 | 2.71% | 3.77× | 23 | 0.91% | 1.27× |

**The top eight minutes in MES 2019–2026:**

```
16:00  21.05%     16:03   3.94%
16:01   7.81%     16:04   3.58%
16:02   4.93%     16:14   3.10%   <- no rule attached
16:05   4.01%     16:06   2.95%
```

> **16:14 outranks 16:10.** A minute with no rule attached beats the minute two venues flatten at.
> **That is the placebo distribution doing exactly the job it was put there for** — a threshold
> would have called 2.93× a spike.

## 2. Three pieces of evidence that all point the same way

1. **The uniformity across instruments.** MES, MNQ, M2K, MYM and NQ **all rank 16:10 at 10th**, and
   ES at 11th. **If funded accounts drove this, the effect would differ across micros by their prop
   popularity — MES and MNQ carry far more prop volume than M2K and MYM. It does not differ at
   all.**
2. **The era runs the wrong way.** ES 2010–2018 has 16:10 at **rank 9 and a 9.59× lift** against
   the modern era's rank 11 and 4.24×. **The structure is OLDER and STRONGER before the prop
   industry existed**, which is the opposite of what the hypothesis needs.
3. **The decay explains the level without any rule.** The cash close at 16:00 empties into the
   futures tape and the hour bleeds down from 21.05%. **Every "lift" in the table is measured
   against a median that sits at the bottom of that decay**, which is why even a nothing-minute
   posts 2–3×.

## 3. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | **`A1` fails and the lane ends here** | **CONFIRMED** — rank 10 against a top-5 bar |
| **Q2** | 16:59 ranks **far above** 16:10 because of the 17:00 halt confound | **WRONG** — 16:59 ranks **18th, well below** 16:10's 10th. **The halt I pre-declared as the thing that would fake support does not generate a squaring spike at all** |
| **Q3** | ES 2010–2018 already shows structure in this hour | **CONFIRMED, and more of it** — 9.59× against 4.24× |
| **Q4** | if anything survives it is MES/MNQ not M2K/MYM | **moot, and informative anyway** — all four micros are identical at rank 10, which is §2.1 |

## 4. A defect in my own abandon conditions, and it matters more than the result

**`A2` and `A3` both "SURVIVED" — and both are meaningless.**

- **`A2`** (MES beats ES at the same minute): **10 vs 11 at 16:10.** One rank. And at 16:59 MES is
  **worse** (18 vs 17). **A one-rank margin on a 60-point scale identifies nothing.**
- **`A3`** (ES 2010–2018 differs at 16:10): **9 vs 11.** The condition is satisfied because the
  ranks differ — **and they differ in the direction that REFUTES the hypothesis.** I wrote
  *"differs"* when I meant *"is weaker in the old era."*

> **Only `A1` had a real bar — top 5 of 60 — and it is the only one of the three that decided
> anything.** `A2` and `A3` were written as bare inequalities with no margin and no direction, so
> both passed on noise. **A condition that cannot fail on a one-rank difference is not an abandon
> condition, and two of my three were not.**

**The stage-0 machinery worked because one condition was specified properly.** Had `A1` been written
the same loose way, this lane would have "survived" into a stage 1 on three meaningless passes.

## 5. What this closes, and what it does not

- **The prop-firm forced-flow hypothesis is dead at the flatten minutes, on volume.** Under
  [R15](../RULES.md#r15) the principal closes avenues; **this is the measurement, and it is
  unambiguous on its own terms.**
- **It does not say forced flow is absent** — it says it is **not visible in minute volume in the
  thinnest hour of the day**, which is where the pre-registration argued it would be most visible.
  **If it is not there, the places left to look are harder, not easier.**
- **It does not touch [lane 21](../research/Prop-Firm-080926/21-order-flow-microstructure.md)**,
  which closed the tape-reading version on cost arithmetic, and nothing here reopens it.
- **Cost: one pre-registration, one 12-minute extraction, one runner.** **The premise number was
  obtainable before any return was read, and no return was read.** That is what stage 0 is for.
