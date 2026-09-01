# D277 — The mine

**Status:** **RUN AND PRICED.** 0 of 300 cells clear the best-of-300 floor.
**Date:** 2026-09-01
**Area:** Strategy research · **personal track**

**THIS IS A SEARCH AND IT IS LABELLED AS ONE.** No hypothesis was pre-registered, no hurdle is
claimed, and **nothing may enter any book from it.** The output is a *ranked candidate list with a
multiplicity price* — a different object from a result.

**Requested by the principal in those terms:** *"even if it's not best practice, try to find some
way or strategies that when combined give good results."* Mining is a legitimate research act when
it is counted. This counts it.

---

## What was crossed

| | |
|---|---|
| **bases** | `S1_short_intra`, `S2_short_intra`, `choch_short` |
| **filters** | 17 scores × {top quintile, bottom quintile}, plus none = **35** |
| **strata** | ALL, LOW, HIGH |
| | **300 cells** *(15 of 315 produced no positions and were dropped)* |

The 17 scores are the session's whole inventory: 9 price ([D267](D267-the-magnitude-calibration-screen.md)),
4 volume ([D270](D270-volume-structure-retest.md)), 4 profile ([D272](D272-the-volume-profile-as-a-positional-input.md)).
All lagged one bar. Costs, borrow and strata exactly as D264 fixed them.

**Ledger, under [R13](../RULES.md#r13):** 300 fresh + ~118 carried from D264–D276 = **~418**. The
ETF programme's 45,783 is **not** carried — D218 scopes its own floor to *"this fixture"*, meaning
57 ETFs daily. R13 was written in this session, in response to the principal, and records the
reasoning.

---

## RESULT — the mine priced its own output at zero

| | |
|---|---:|
| **best-of-300 floor (p95)** | **+0.605** |
| best cell in the mine | **+0.392** |
| **cells clearing the floor** | **0 of 300** |

**The best thing 300 combinations produced is comfortably inside what a pure noise search of the
same size returns.** That is the whole verdict on the mine as a search.

### But five cells clear the cost bar with a positive CAGR — the first this session

| cell | move vs `2c` | CAGR | Sharpe | exposure | trades |
|---|---:|---:|---:|---:|---:|
| LOW · S2 · `impulse_hist` bot | **2.19×** | +0.69% | +0.348 | 1.9% | 556 |
| LOW · S2 · `macd_line` bot | **2.10×** | +0.73% | +0.286 | 3.6% | 697 |
| HIGH · S2 · `mass_imbalance` bot | 1.70× | +0.58% | +0.341 | 0.5% | 251 |
| ALL · S2 · `mass_imbalance` bot | 1.67× | +0.38% | **+0.392** | 0.4% | 508 |
| LOW · S2 · `mass_imbalance` bot | 1.64× | +0.17% | +0.196 | 0.4% | 257 |

**Every construction in this session has failed `mean move ≥ 2c`. These five clear it.** That is
worth stating plainly before it is taken apart.

### And they are one finding, not five

**Every one is `S2_short_intra` with a BOTTOM-quintile filter**, and the filter scores are the same
quantity wearing different names — measured, in this session, before the mine ran:

| pair | ρ | measured in |
|---|---:|---|
| `impulse_md` ~ `mass_imbalance` | **−0.83** | D272 |
| `macd_line` ~ `impulse_md` | +0.78 | D268 |
| `impulse_hist` ~ `macd_line` | +0.57 | D268 |

**All three filters select the same bars: price low in its recent range.** So the finding is
singular — *short a confirmed downtrend when price is already depressed within it* — and it appears
five times because the score library is redundant, which [D268](D268-score-independence.md)
measured at **2.87 effective inputs from nine scores.**

**Counting five hits from a redundant library is exactly how a mine manufactures confidence.**

### And the size is trivial

**CAGRs of 0.17% to 0.73%, at exposures of 0.4% to 3.6%.** The best-Sharpe cell holds **0.4% of
capital** and returns **0.38%/yr**. At 251–697 trades over 8.25 years that is 30–85 trades a year
across four names — and [hurdle E](D256-the-book-on-single-names.md) requires 30 per *symbol*.

---

## The reading

**The mine found the SHAPE and not the SIZE.** It is not noise-free — five cells clear a cost bar
that 300 constructions before them failed, and they agree on a single mechanism. But:

1. **Nothing clears the best-of-300 floor.** +0.392 against +0.605.
2. **The five are one thing**, inflated by a score library with 2.87 effective inputs.
3. **The returns are fractions of a percent** at exposures under 4%.

**What it would take to become a candidate:** the same construction, pre-registered, on names this
fixture has never touched — and it would inherit all 300 cells into its multiplicity count under
R13's second test, because this search is what would have selected it.

**What it does NOT do is reopen anything.** Every closure in D264–D276 fired on a hurdle failure,
not on multiplicity, so R13's rescoping leaves them exactly where they were.

---

## ADDENDUM — what the five do under sizing

`scripts/d277_sizing.py`. **Sharpe is invariant to constant leverage** (D201/D202), so the
best-of-300 floor of **+0.605** is not reachable by sizing at any scale. What sizing changes is
return, volatility, drawdown, and survival.

### Reading (a) — full deployment per trade: 100% into the name when the signal fires

| cell | scale | CAGR | vol | max DD | Sharpe |
|---|---:|---:|---:|---:|---:|
| ALL · S2 · `mass_imbalance` | 8× | **+3.04%** | 7.64% | **−16.13%** | +0.392 |
| LOW · S2 · `macd_line` | 4× | +2.96% | 10.18% | **−23.01%** | +0.286 |
| LOW · S2 · `impulse_hist` | 4× | +2.79% | 7.90% | −16.72% | +0.348 |
| HIGH · S2 · `mass_imbalance` | 4× | +2.33% | 6.75% | −14.10% | +0.341 |
| LOW · S2 · `mass_imbalance` | 4× | +0.70% | 3.55% | −6.31% | +0.196 |

**This is the sensible reading and it produces the first thing in the session that reads like a
book rather than a rounding error — roughly 3%/yr at 7.6% vol.** It is still below its own noise
floor, and −16% of drawdown for 3%/yr is a poor exchange against [R12](../RULES.md#r12)'s ~20%
tolerance; the `macd_line` cell at −23.01% is already outside it.

**Caveat on my own figures: drawdown is scaled LINEARLY here, which UNDERSTATES it.** A levered
book's drawdown compounds worse than linearly because the variance drag bites hardest on the way
down. The true numbers are worse than the table.

### Reading (b) — 100% average exposure: ruinous in all five

| cell | leverage needed | implied vol | worst adverse bar | **max survivable** |
|---|---:|---:|---:|---:|
| LOW · `impulse_hist` | 52× | 102% | +5.57% | **17.9×** |
| LOW · `macd_line` | 27× | 70% | +5.57% | **17.9×** |
| HIGH · `mass_imbalance` | 217× | 366% | +2.76% | **36.2×** |
| ALL · `mass_imbalance` | 227× | 217% | +2.76% | **36.2×** |
| LOW · `mass_imbalance` | 239× | 212% | +1.27% | **78.5×** |

**Every cell requires more leverage than its own worst adverse bar survives**, by margins of 1.5×
to 6×. These books hold 0.42–3.65% average exposure precisely because the signal is rare, so
reaching 100% means 27× to 239× — and a single bar each book *actually held* takes the account to
zero.

**[FINDINGS §1c](../FINDINGS.md) reproduced on equities:** *"a short is not survivable at full
notional."* Crypto's maximum survivable per-name notional was 0.46×; these are more forgiving at
18–79×, and the leverage required is far past it regardless.
