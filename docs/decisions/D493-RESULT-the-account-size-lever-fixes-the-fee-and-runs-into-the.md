# D493 — RESULT: the account-size lever fixes the fee and runs into the barrier — a full contract dies in weeks at every plan, and nothing the programme holds is carryable

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D493-RESULT-the-account-size-lever-fixes-the-fee-and-runs-into-the-barrier-a-full-contract-dies-in-weeks-at-every-plan-and-nothing-the-programme-holds-is-carryable.md`. The H1 above is the full title.*

**2026-09-12.** Spec [D493 PRE-REG](D493-PRE-REG-the-account-size-lever-through-the-lifecycle-which.md)
(`62404c7`, before the code). Runner `scripts/run_d493_account_size.py`; numbers
`data/d493_account_size_lifecycle.json`; log `temp/d493_run.log`. **Arithmetic on committed
objects: 448 lifecycle cells (14 plans × ES/NQ × micro/full × 1/2/3/5 contracts × two providers),
8,000 paths × 600 days each, 1.4 min. Nothing measured anew; nothing opened, closed or admitted.**
[P1] the Gaussian provider reproduces D386 bit-identically; [S] a +$100-a-day series passes every
evaluation and a −$100 one passes none.

## 0. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| 1 no cell clears V > 2 SE ∧ P3 ∧ life ≥ 3 y; P(pass) < 25% | | **0 of 448 clear.** P(pass) at one full NQ on the measured series 13–31% by plan (four plans above 25%) — held in substance, the number missed at the top |
| 2 net Sharpe rises from < 0 at one micro to +0.3–0.5 at one full NQ; P3 breaches on the 150k plans | | **micro −0.13 ± 0.42 → full +0.48 ± 0.39** (ES −0.69 → +0.14); at one full NQ the worst day is **−3.5% of a 150k account and ten days breach −2%** — held |
| 3 MACD moments, one full NQ on 150k: V > 0 at MFFU, < 0 at Apex and TPT | | MFFU **+189 ± 32**, Apex **−1,570 ± 22**, TPT **+182 ± 35** — two of three; the order is the fee structure, as predicted; **and every one of them has a funded life of 0.13–0.16 years** |
| 4 micros never reach V > 0 | | **12 of 224 micro cells do** (max +$216), all at 3–5 micros on the cheapest evaluations — lottery cells that pass fast and die; the letter missed, the reading holds |

## 1. What the fee lever does (plan-independent, the measured last-30 series)

| | ES micro | ES full | NQ micro | **NQ full** |
|---|---|---|---|---|
| net $/day at one contract | −2.2 | +4.5 | −0.6 | **+21.5** |
| net annualised Sharpe (monthly-block SE) | −0.69 ± 0.46 | +0.14 ± 0.40 | −0.13 ± 0.42 | **+0.48 ± 0.39** |
| worst day, % of $50k | −1.6 | −16.1 | −2.1 | −20.9 |

Getting off the micro does exactly what D486 said: on NQ it moves the last-30 trade from losing
to a net Sharpe of +0.48, at the edge of C-a and inside one SE of it. **Contract count does not
change Sharpe** (scale-free, D486 §1), so the four sizes read identically on that line.

## 2. What the barrier then does (every plan)

At one full NQ on the measured series: **P(pass) 13–31%, funded life 0.03–0.15 years, alive at
600 days 0% on all 14 plans**, V from −$1,881 (TPT 150k) to +$132 (Topstep 50k). At the MACD
moments (one trade a session, gross 3.85 ticks, σ 217 ticks): P(pass) 17–47%, funded life
0.03–0.16 years, alive at 600 days ≤ 1%, V positive at MFFU, Topstep and TPT (+$180 to +$560) and
negative at Apex (its evaluation fee is $1,890 at 150k).

**Why.** A funded account's trailing drawdown is a fixed dollar amount — $2,000 to $4,500 — and a
full NQ contract's daily σ is $705 on the last-30 trade and $1,085 on the MACD's. **The barrier is
three to six daily σ from the running high.** A drift of a few dollars a day against a
trailing barrier that close is hit in weeks: that is the funded life the table shows, on every
plan, at every size that makes the fee small. The micro sits forty σ from the barrier and lives
for years — and loses money on the fee. **The fee and the barrier are the same constraint seen
from two sides: the account's dollar drawdown fixes the σ per contract-day it can carry, and
that σ fixes the fee in ticks.** No plan on the list separates them.

The positive-V cells are what they look like: evaluations passed quickly by variance, one
payout, then the breach. They are lottery tickets priced by the fee, not carry.

## 3. A discrepancy for the MACD lane, recorded not resolved

D486 quotes the full-NQ MACD at net Sharpe +0.35 (+0.57 with passive fills). At **one round trip a
session**, the declared prop shape, the same moments give **+0.16**: net 2.24 ticks × $5 = $11.2 a
day against σ $1,085. D486's figure counts the hourly entries of a five-hour hold as separate
trades; on the day session they are one. That lane owns the reconciliation.

## 4. What this settles for the prop book

- **The size lever is real and insufficient.** It fixes the fee (86% of the micro's cost) and
  exposes the barrier. Nothing the programme holds — the last-30 trade at +0.48 or the MACD at
  +0.16 per session — survives a funded account for a year at any plan.
- **The specification for any prop signal is now a number in the account's units:** a daily
  mean large enough that the trailing drawdown sits far from the running high in *drift*
  terms, not just in σ. With D386's geometry that is a daily Sharpe near 0.1 (annualised ~1.5)
  at whatever size makes the fee small — the book-level target CLAUDE.md already states, now
  shown to bind at the component level because the barrier is per account, not per book.
- D494 (direction from outside the price path) is scored against this: a day-session cell is
  worth pursuing only if its gross per session is several ticks on the full contract, not the
  fraction of a tick a rotation null can produce.
- Predictions 1–2 held; 3 half; 4 missed in letter. Nothing enters `COMPONENTS_PROP.md` or
  either book. The principal decides what, if anything, to buy; this record says not yet.
