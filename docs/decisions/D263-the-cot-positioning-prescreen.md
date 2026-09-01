# D263 — CFTC positioning as a weekly signal: a pre-screen

**Status:** Screened and closed (no rule proposed, no hurdle run, no null computed)
**Date:** 2026-09-01
**Area:** Strategy research · prop track ([BOOK_PROP.md](../BOOK_PROP.md))

**The ledger does not move. Nothing was admitted to any book.**

---

## What this was

D250 and D251's inversion applied a third time: **measure the conditional first, against a bar
stated before looking, and only pay for a full pre-registration if it clears.** The design was
committed in `4dd6d3c` **before the screen ran**, so the bar could not be chosen after seeing the
data.

This is **rung 1** of [the proposal's ladder](../research/futures-data/data-purchase-proposal.md).
It is free, the data was committed by [D262](D262-the-futures-data-layer-and-the-free-rung.md), and
**if positioning carries nothing the ~$205 Databento purchase loses most of its motivation** — the
tick version tests the same premise at roughly an eighth of the statistical power.

## The panel, and it is the best-powered thing the prop track has had

COT has no returns in it, so each contract was paired with its tracking ETF:

> ES/SPY · NQ/QQQ · RTY/IWM · YM/DIA · GC/GLD · SI/SLV · CL/USO · NG/UNG · ZB/TLT · ZN/IEF · ZF/SHY

| | |
|---|---:|
| instruments | 11 |
| weekly observations | 9,232 |
| span | 16.2 y |
| mean pairwise ρ | 0.284 |
| **effective instruments** | **3.76** |
| **MDE on Sharpe** | **0.21** |

**D261's index spreads ran at effective breadth 1.17; the $145 tick option would have given MDE
1.65.** Two independent sanity checks: ρ = 0.284 against the 0.282 measured on D226's 57-ETF
intraday panel, and 3.76 against D261's 3.00 for a diversified futures complex.

## RESULT — CLOSED. Zero of eight cells clear, and the bodies are empty.

`uv run python scripts/prescreen_cot_positioning.py` · `data/cot_prescreen_summary.json`

| category | h | Q1…Q5 annualised % | spread | gross | monotone | bar |
|---|---|---|---:|---:|---|---|
| **leveraged_money** | 1w | +10.32 +3.80 +8.34 +6.51 +7.97 | +2.35 | +0.94 | ✗ | ✗ |
| leveraged_money | 4w | +6.47 +4.67 +7.44 +7.18 +7.72 | −1.24 | −0.50 | ✗ | ✗ |
| **managed_money** | 1w | −14.05 +1.87 −5.36 +8.74 −6.72 | **−7.32** | −2.93 | ✗ | ✗ |
| managed_money | 4w | −8.53 −1.78 −4.12 −2.02 −2.13 | −6.39 | −2.56 | ✗ | ✗ |
| nonreportable (TFF) | 1w | +8.82 +9.58 +7.98 +2.29 +8.28 | +0.54 | +0.22 | ✗ | ✗ |
| nonreportable (TFF) | 4w | +6.93 +9.59 +4.57 +3.87 +8.51 | −1.58 | −0.63 | ✗ | ✗ |
| nonreportable (disagg) | 1w | +1.83 −5.53 −19.33 +8.82 −1.32 | +3.15 | +1.26 | ✗ | ✗ |
| nonreportable (disagg) | 4w | −1.22 −10.09 −17.95 +13.62 −2.93 | +1.71 | +0.69 | ✗ | ✗ |

**All three conditions of the bar fail, and the first one fails hardest.**

1. **MONOTONICITY fails on all eight.** This is the decisive one. `nonreportable (disagg)` runs
   +1.83 / −5.53 / **−19.33** / +8.82 / −1.32 — a body with no order in it at all. `managed_money`
   at 1w runs −14.05 / +1.87 / −5.36 / **+8.74** / −6.72. **These are not weak signals, they are
   noise**, and D250 closed on exactly this shape.
2. **GROSS fails on all eight.** Best is **+1.26%/yr** against a 2% bar; three cells are negative.
3. **2020 is not the cause.** Seven of eight signs survive its removal, several strengthening. **The
   result is not a crisis artefact — it is simply empty**, which is a cleaner finding than a
   regime-dependent one.

### The largest spread has the wrong sign, and it is not a rescue

**`managed_money` at −7.32%/yr is the biggest number in the table and it is BACKWARDS.** The
direction was declared `+1` in advance — the classic COT reading that crowded professional longs
precede weakness. Measured, high managed-money positioning precedes *higher* returns.

**That reversed reading is disclosed and NOT claimed.** It is non-monotone, so it is not a signal in
either direction, and [D246](D246-the-search-protocol-for-s3.md) Constraint 3 forbids re-reading a
falsified direction as a result. **Declaring the direction in advance is what makes this legible**
rather than something to be quietly reinterpreted — the same guard D251 needed.

### R10 fired, and for once the answer is reassuring

| category | mean instruments in an extreme bucket | max of 11 |
|---|---:|---:|
| leveraged_money | 2.68 | 6 |
| nonreportable (TFF) | 2.73 | 7 |
| managed_money | 1.91 | 4 |
| nonreportable (disagg) | 1.82 | 4 |

**This is genuinely cross-sectional.** D249's wedge put **56 of 57** names in the extreme bucket at
once and was a market timer wearing a per-instrument signal's name. Positioning does not do that —
under 3 of 11 on average. **The construction was structurally sound; there was just nothing in it.**

## The stop applies

**Weekly category positioning is CLOSED for the prop track.** No threshold sweep, no second lookback,
no third category, no cointegration-style filter added afterwards. That would be the search this
design deliberately removed.

## What this does NOT close, stated precisely

- **Rung 2's free form** — the micro/mini split. A *different construction* on a *different
  quantity*, named on the ladder before any of this ran. Not tested here.
- **Rung 3** — open interest against volume.
- **Intraday order flow.** A weekly positioning survey says nothing about an hours-horizon tape
  signal. Rung 4's premise is untouched by this.

**But the cheapest rung came back empty**, which is evidence about the family and was bought for
nothing. That is exactly what §7.5's ladder was built to produce.

## What survives

**The panel itself.** 11 instruments, 16.2 years, effective breadth **3.76**, MDE **0.21** — assembled
free from two committed fixtures. **Any future weekly cross-sectional question can be asked here**,
and it is better powered than anything the prop track has run.

## Cost

About twenty minutes, against a full pre-registration's day. **Third time the inversion has paid.**

## Ledger

| count | N |
|---|---:|
| fresh — 4 categories × 2 horizons | 8 |
| + carried from D261 | 46,089 |
| **total** | **46,097** |
