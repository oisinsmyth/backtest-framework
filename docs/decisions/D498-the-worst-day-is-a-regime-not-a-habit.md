# D498 — ADDENDUM to D497: the bad days are a **regime**, not a habit

**2026-09-12.** Runner [`scripts/d498_worst_day_frequency.py`](../../scripts/d498_worst_day_frequency.py) ·
artifact [`data/d498_worst_day_frequency.json`](../../data/d498_worst_day_frequency.json).
Same cell, window and cost line as [D497](D497-hurdle-P-on-the-D495-candidate-P3-fails.md).
No search, no new grid, no new signal. Nothing opened, closed or admitted ([R15](../RULES.md#r15)).

---

## 1. Why it exists

D497 asked a binary — does the worst day clear $1,000 — and answered no. The principal's reading
was that the extremum is the wrong statistic:

> *"the worst day is not the end of the world? If its a one off it does not matter but if it
> happens all the time then thats a different story"*

That is a question about a **rate**, and a rate is a different object from a max. D497 also never
**named** the days, which is this repo's own standing lesson.

## 2. The rate, and the year table beside it

| threshold | days | % of sessions | one every | per year |
|---|---:|---:|---:|---:|
| ≤ −$250 | 97 | 5.18% | 0.08 yr | 13.05 |
| ≤ −$500 | 20 | 1.07% | 0.37 yr | 2.69 |
| ≤ −$750 | 6 | 0.32% | 1.24 yr | 0.81 |
| **≤ −$1,000** | **2** | **0.11%** | **3.72 yr** | **0.27** |
| ≤ −$1,250 | 1 | 0.05% | 7.43 yr | 0.13 |

| year | worst day | days ≤ −$500 | days ≤ −$1,000 |
|---|---:|---:|---:|
| 2016 | −155 | 0 | 0 |
| 2017 | −131 | 0 | 0 |
| 2018 | −394 | 0 | 0 |
| 2019 | −285 | 0 | 0 |
| 2020 | −523 | 2 | 0 |
| 2021 | −852 | 2 | 0 |
| **2022** | **−1,315** | **13** | **2** |
| 2023 | −682 | 3 | 0 |

**In six of eight years the worst day never reached −$550.** The two breach days are
**2022-05-20** (−$1,315, NQ −1.62% over the traded window) and **2022-10-13** (−$1,042, NQ
**+5.12%** — a reversal day, with the position on the wrong side of it).

The worst day is **−7.28 σ** on a daily σ of $180; a normal would put 3×10⁻¹⁰ such days in 1,873
sessions. **Excess kurtosis +6.6.** So the tail is fat, and D496's Brownian barrier model cannot
see it — which is why §4 computes the empirical life beside the model's.

## 3. The account-life table is the finding

| bought | died | sessions | worst day in that life |
|---|---|---:|---:|
| 2016-01-07 | 2019-07-08 | **817** | −394 |
| 2019-07-09 | 2021-11-03 | **553** | −523 |
| 2021-11-04 | 2022-01-12 | 43 | −852 |
| 2022-01-13 | 2022-01-21 | **6** | −888 |
| 2022-01-24 | 2022-02-16 | 18 | −812 |
| 2022-02-17 | 2022-08-09 | 112 | −1,315 |
| 2022-08-10 | 2023-08-18 | 240 | −1,042 |
| 2023-08-21 | (alive) | 84 | −482 |

**Two accounts cover 2016–2021. Four die inside 2022.** The construction is not fragile on
average; it is fragile **in one regime** — and a mean over the window hides that completely.

## 4. Three corrections to what D496 and D497 published

1. **E[life] is 256 sessions empirically, not 177.** D496's Brownian model was *pessimistic* on
   life despite having no fat tail: 7 deaths in 1,873 sessions. **256 sessions is 1.02 years**,
   which meets the principal's preferred ≥ 1 year where the model said 0.70 — with an enormous
   spread across regimes.
2. **P3 costs 22% of the account's life, not 16%.** Drawdown alone: 7 deaths, 256 sessions.
   Drawdown **or** a P3 breach: 9 deaths, **199 sessions**. D497's hazard addition understated it
   because the breaches land *inside long lives* — 2022-05-20 truncates a 112-session life at 62,
   and 2022-10-13 truncates a 240-session life at 42.
3. **A same-day stop at the P3 level buys ZERO life.** Capping every breaching day at −$1,000 —
   the best such a stop could do — leaves the life at **256 against 256** and the deaths at
   **7 against 7**. **The two extreme days are not what kills the account**; strings of moderate
   2022 losses are. That is the opposite of what D497 §4 assumed: a stop is worth building to
   satisfy P3 *as a rule*, and worth nothing for survival.

## 5. And P3's provenance needs checking before it decides anything

R11 justifies P3 with a generic *"daily loss limits run 2–3%"*. **The five MFFU plans and Topstep
as encoded in [`scripts/d386_full_lifecycle.py`](../../scripts/d386_full_lifecycle.py) carry no
daily-loss-limit field at all** — only a trailing drawdown, EOD or intraday. Whether a daily
limit is a real term at either of the two venues P6 permits is **unverified** and needs the terms
pages read. If it is not a term, P3 is a prudence rule of ours and the 22% above is its entire
cost.

## 6. Checks

15 checks. The drawdown walker is proven to trail from the running **peak** rather than from zero
(a from-zero reading sees +600 on `[1000, −400]` and never dies), to restart flat after each
death, and to return contiguous segments. **Two series with the same worst day and a 40× rate
difference are proven to give different account lives** — the addendum's premise, made checkable.
The date vector is proven to name the right day, and a roll of one is proven to name the wrong one.

One expectation of mine was wrong and the code right: I asserted a mean life of 2 on lives of 1
and 2 sessions; `int()` was truncating 1.5, so the mean is now returned unrounded.

## 7. What this does not do

- In-sample only; **2024+ sealed**.
- **An order statistic is the figure most exposed to fill optimism** — open-of-next-segment at the
  measured half-spread, no queue, no partial fills — so −$1,315 is an upper bound on the P&L and a
  lower bound on the breach.
- **The empirical life is one realised path**, so its own standard error is large; seven deaths
  is a small count.
- **Nothing here licenses a 2022 filter.** A stand-down rule chosen *because* 2022 is the bad
  year is in-sample selection. Any vol or regime gate has to be specified on prior grounds and
  read on the sealed slice.
