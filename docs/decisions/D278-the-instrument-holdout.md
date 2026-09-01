# D278 — The instrument holdout

**Status:** PRE-REGISTERED. Committed **before the holdout bars are scored**. Nothing here is a result.
**Date:** 2026-09-01
**Area:** Strategy research · **personal track**

---

## What is being tested and why it needs a holdout

[D277](D277-the-mine.md) mined **300 combinations** on the original eight names. Its best cell
scored **+0.392** against a best-of-300 floor of **+0.605** — inside noise. But **five cells cleared
the cost bar with a positive CAGR**, the first anything has in this programme, and they agreed on
one mechanism:

> **Short a confirmed downtrend (`S2_short_intra`) when price is already low in its recent range.**

**A mined candidate cannot be assessed on the data that produced it.** [R8](../RULES.md#r8) requires
a pre-registered test on data the search never touched. This is that test.

## The holdout, and it is spendable once

`scripts/select_holdout_names.py` — **D264's selection rule unchanged**: same 2013-01-02 …
2017-12-29 window (disjoint from the 2018–2026 test span), same survivor requirement, ≥95%
coverage, ≥$50M median dollar volume, same volatility stratification. **The only change is depth —
ranks 5–12 of each stratum instead of 1–4.**

| stratum | names | ann. vol 2013–17 |
|---|---|---|
| **LOW** | RTX, VZ, COST, HD, DIS, SPG, CMCSA, SBUX | 16.3% – 19.6% |
| **HIGH** | CNX, BB, THC, ANF, NI, RIG, HLF, TRGP | 45.7% – 52.5% |

**Sixteen names, zero shared tickers with the in-sample eight**, asserted in code rather than
claimed. Never fetched, never scored, selected by a rule fixed before the mine existed.

**[D246](D246-the-search-protocol-for-s3.md) is explicit that clean data is this programme's
scarcest resource and a holdout used twice is not a holdout.** These are spent here, once, on the
construction frozen below.

**One difference from the in-sample fixture, and it is a real one:** three of the sixteen carry
splits in the span — RTX ×1.589 (the Raytheon/UTC merger), CMCSA ×1.067, HLF ×2.0 — where the
original eight had none. The build's back-adjustment is load-bearing here rather than merely
present, and the D226 residual-step gate must be read before anything is scored.

---

## The construction, frozen

```
base    S2_short_intra   -- DOWNTREND := g_lo < 0 AND g_hi < 0, short,
                            flat at every session close, lag 1
filter  hold only where the LAGGED score sits in its BOTTOM quintile,
        computed per symbol on the holdout's own history
```

**Three filter scores are tested, not one, and the reason is stated:** D277's five winners used
`impulse_hist`, `macd_line` and `mass_imbalance`, and picking the best of those *after* seeing the
mine would be selecting on the outcome twice. **All three are carried, on all three strata, plus
the unfiltered base.**

**Cells: (3 filters + 1 unfiltered) × 3 strata = 12.** Counted in full, and judged against a
**best-of-12 floor**, not individually.

**Every constant comes from the in-sample work unchanged** — S2's `k = 3`, window 252, age cap 63;
the quintile cut at 20%; costs, borrow and strata as D264 fixed them; the volume profile at D272's
parameters. **Nothing is re-tuned for the holdout, and no fourth filter may be added after seeing
it.**

---

## Hurdles

| | standard |
|---|---|
| **H1** | **Mean move per trade ≥ `2c`**, at the holdout's own measured cost |
| **H2** | **Positive net CAGR** after fees, financing and borrow |
| **H3** | **Matched-count rotation null ≥95th on BOTH legs**, Sharpe and money |
| **H4** | **Best-of-12 floor** (D228), one shared offset vector |
| **H5** | **The SIGN agrees with in-sample** — a filter that wins in-sample and loses out-of-sample has not replicated, whatever its magnitude |

**All five.** H5 exists because a mined candidate's most likely failure mode is sign reversal, and
without it a "pass" on a different filter than the one that won in-sample would be a second mine
dressed as a replication.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **P1** | **No cell clears all five.** The in-sample best sat below its own floor, so there was no established effect to replicate | **high** |
| **P2** | **At least one filter reverses sign** between in-sample and holdout | **moderate-high** |
| **P3** | **The unfiltered `S2_short_intra` base loses on the holdout too**, reproducing D264's result on sixteen fresh names — which is the one thing here I expect to replicate cleanly | **moderate-high** |
| **P4** | **The three filters DISAGREE with each other on the holdout**, as `mass_imbalance|bot` and its ρ = −0.83 correlate `impulse_md|top` already did in-sample (+0.392 against −0.481). **Measured after that comparison, their bar overlap is only 53%, so I over-stated it as "near-identical" and the correction is recorded** | **moderate** |

---

## Stop

**If no cell clears, the mined construction is closed and the single-name intraday short is closed
with it** — the in-sample search is spent, the holdout is spent, and no third sample will be
selected from this pool.

**If a cell does clear, it is still not a book entry.** It becomes a candidate carrying D277's 300
cells plus these 12 in its multiplicity count under [R13](../RULES.md#r13), and needing a forward
period nobody has touched.

---

## Ledger

| count | N |
|---|---:|
| fresh — 4 filters × 3 strata | **12** |
| carried: D277's mine, which selected this construction (R13 test 2) | 300 |
| carried: D264–D276, which built the bases and scores | ~118 |
| **total** | **~430** |

**The ETF programme's 45,783 is not carried**, per R13 and D218's own scoping of its floor to
*"this fixture"*.
