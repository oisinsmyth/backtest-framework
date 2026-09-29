# D680 DIAG — why the month-end mechanism fails: the flow did not shrink, move earlier or get offset. Its price impact per unit collapsed in BOTH legs after 2018, while the flows grew

*2026-09-29, on the principal's word: "Can you do a diagnostic on why the underlying mechanism fails?" One run of
`scripts/diag_d680_month_end_mechanism.py`, committed before its run (`dbd85855`) with five hypotheses and their
fingerprints in its docstring. Output `data/d680_month_end_diag.json`. **Post hoc, on D677's in-sample (2010-07 →
2023-12), no verdict.** The eras are post hoc, taken from D677's per-year table: 2010–15, 2016–18 and 2019–23. D677's
B2 (+7.1732 bp) reproduces exactly. Numbered D680 because the other session holds number 679.*

## The answer in one line

**The rebalancing flow kept coming and got bigger, but prices stopped moving to it.**
- **Equities:** the response per 0.01 of drift fell from −15.8 (2010–15) and −19.7 (2016–18) to **−5.9** (2019–23).
- **The long bond:** it had responded as the mechanism says in 2010–15 (ZB +8.6, t 2.09) and went flat with the
  equity leg.
- **Three explanations are ruled out:** the flow was not anticipated into earlier days, not offset by the
  turn-of-month rally, and not smaller.
- **What is left in 2019–23 is quarter-ends,** where the flow is largest.
- **The reading this leaves:** predictable month-end flow is now absorbed without a price concession.

## 1. The five hypotheses and what the data says

| | hypothesis | fingerprint declared before the run | what the data shows | verdict |
|---|---|---|---|---|
| A | **anticipation** (front-running moves the impact earlier) | late-era slope moves to days −9…−5, and the window goes flat | late era, days −9…−5: **−2.0 (t −0.12)**; the window −4…0: −6.7 (t −0.90) | **not supported:** nothing moved earlier |
| B | **a turn-of-month rally offsets it** | the late loss sits in the sign book's drift part; the timing part keeps its sign | drift part −1.46 / −2.32 / **−1.93**; timing part +12.96 / +16.47 / **+0.16** | **not supported:** the conditional relationship itself vanished |
| C | **a smaller flow** | the response per unit of raw drift falls because \|drift\| falls, or stocks and bonds co-move | \|drift\| 0.0086 / 0.0076 / **0.0095** (larger). Response per 0.01 of drift −15.8 / −19.7 / **−5.9**. Square-root factor 3.2 / 3.1 / **5.7** ×10⁻⁴ | **the reverse:** the flow grew, and its response per unit collapsed |
| D | **information, not flow** | after month-end the slope keeps the window's sign in every era | days +1…+10: −5.3 / −2.6 / −2.7 bp a day, every t < 1 | **weak:** no reversal, but no reliable continuation either |
| E | **the bond leg lives elsewhere** | ZB responds where ZN does not | 2010–15: **ZB +8.6 (t 2.09)**, ZN +3.2 (t 1.59); 2016–18 and 2019–23 both about 0. Pooled ZB +4.05 (t 1.90); **ES−ZB −18.0 (t −3.27)** | **partly supported:** the bond leg was real, in duration, and faded with the equity leg |

**Per block of days relative to the month's last trading day** (bp per 1-SD of drift, t in brackets):

| era | days −15…−10 | days −9…−5 | window −4…0 | after, +1…+10 |
|---|---|---|---|---|
| 2010–15 | +3.1 (+0.41) | +0.1 (+0.02) | **−17.8 (−2.41)** | −5.3 (−0.98) |
| 2016–18 | +6.2 (+0.64) | +15.0 (+0.94) | **−22.3 (−2.77)** | −2.6 (−0.35) |
| 2019–23 | +23.1 (+0.97) | −2.0 (−0.12) | −6.7 (−0.90) | −2.7 (−0.34) |
| all | +11.2 (+1.08) | +1.4 (+0.16) | **−14.0 (−3.14)** | −3.5 (−0.80) |

## 2. What the pieces add up to

1. **Through 2018 the mechanism behaved as the flow story says, in both legs:**
   - equities fell (−18 to −22 bp per 1-SD) in the last five days when they were overweight;
   - in 2010–15 the long bond rose (+8.6, t 2.09);
   - ZN barely moved. Pensions buy duration, not the 10-year.
   - **D677's "no bond leg" was a ZN artefact plus the fade.**
2. **After 2018 the price concession per unit of flow fell by 63–70%** (from −15.8 or −19.7 to −5.9 bp per 0.01 of
   drift), in both legs.
   - This happened while the flow grew: larger average drifts.
   - It also happened while the square-root law predicted almost twice the impact per unit: higher volatility,
     relatively thinner ES volume.
   - Nothing moved earlier in the month (A), and the unconditional window drift did not change (B).
3. **What survives in 2019–23 is at quarter-ends:** −14.1 (t −1.54, 100 days), against **+4.3** (t +0.38, 200 days)
   in the other months.
   - In 2010–15 it was the other way round: other months −20.5 (t −2.50), quarter-ends −9.2 (t −0.68).
   - The residual effect now sits only where the flow is largest.

**The reading these facts leave** is not tested here, and it is the only one they do not contradict. **The month-end
flow became predictable enough to be absorbed without a price concession.** Liquidity suppliers, or the rebalancers'
own execution (overlays, internalised or netted at the dealers, spread across the day), now take the other side of
ordinary month-ends at close to fair value. That is the prediction of trading on announced, predictable flow ("sunshine
trading": predictable demand is cheap to absorb). Absorbers with limited capacity would still be overwhelmed at
quarter-ends, which is where the residual sits.

**Not testable with the data here:** whether execution moved to cash equities, ETFs or swaps; whether published bank
estimates of month-end flow (widely circulated before the paper) coincide with the 2019 break.

## 3. Caveats

- **The eras were chosen after D677's per-year table**, so the late era's weakness is partly defined by selection.
  But the decomposition (B) and the response per unit (C) are new measurements, not a re-reading of that table.
- **Per-era and per-day cells are small:** 60–330 days, and every per-day profile value is noise. The block and era
  figures are the evidence; the 26-day profile in the JSON is not.
- **Multiplicity:** 5 hypotheses × 3 eras × several statistics. Only a few cells reach |t| ≥ 2: ZB 2010–15, the window
  in 2010–15 and 2016–18, and the pooled blocks. The verdicts rest on the pattern across eras, not on one t.

## 4. What this decides

**The fade is the mechanism's own erosion, not a construction error that a better filter could fix.** That agrees
with D678: no projection could rescue a price response that disappeared. Two things are worth keeping:
1. **The mechanism was two-legged and duration-specific:** ES−ZB −18.0, t −3.27, pooled. Any future flow study should
   pair equities with the long bond, not ZN.
2. **The residual is at quarter-ends.** If a successor is wanted, it is the **quarter-end-only** book on ES−ZB, with
   its own pre-registration and power, and a slice nobody has read.
   - At 4 events a year × 5 days its power is low. 2024-01 → 2025-02 holds four quarter-end windows, and the vault
     holds six (2025-03 → 2026-06): 50 days together.
   - At −14 bp per 1-SD against ES's 107 bp daily σ, that is an expected t of about 0.9 even if the residual is
     entirely real.
   - So it is a forward-accrual question, not an in-sample one.

**Proposal (R15, the principal's):**
- close the month-end line as a strategy (D677, D678 and D680);
- record these facts: the two-legged mechanism, and its post-2018 absorption;
- optionally, pre-register the quarter-end ES−ZB book **forward only**: it would accrue from the next quarter-end,
  with no historical slice spent.
