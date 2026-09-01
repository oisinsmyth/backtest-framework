# D278 — The instrument holdout

**Status:** **RUN AND CLOSED.** 0 of 12. **All five in-sample winners reverse sign.**

**Everything above the RESULT heading was committed in `f8407c3`, and the fixture in `681723a`, BEFORE the holdout was scored.**
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

---

## ADDENDUM, committed BEFORE the holdout bars exist — the cost preview, and one hurdle clarified

`scripts/d278_precompute_costs.py`, run while the fetch was still going. **Prices from the
committed daily fixture; no intraday bar was read. The study's final cost still comes from the
intraday panel's own median close, as D264's did.**

### The holdout HIGH stratum is a 29% harder test than the study it replicates

| stratum | holdout `2c` | in-sample `2c` | ratio |
|---|---:|---:|---:|
| LOW | 4.13 bp | 4.00 bp | 1.03× |
| **HIGH** | **16.50 bp** | 12.84 bp | **1.29×** |
| ALL | 10.32 bp | 8.42 bp | 1.22× |

**[D264](D264-the-intraday-short-on-single-names.md)'s post-hoc price finding is now binding.**
Commission is charged per *share*, so in basis points it is inversely proportional to price:

| | median price | commission alone |
|---|---:|---:|
| **RIG** | $4.62 | **10.82 bp/side** |
| **BB** | $5.32 | **9.40 bp/side** |
| CNX | $16.20 | 3.09 bp/side |
| *COST, for contrast* | *$490.06* | *0.10 bp/side* |

**RIG and BB each pay more in commission alone than the in-sample HIGH stratum's entire cost bar
per side** — a 108× spread across sixteen names, from price alone.

**This is not corrected and the names are not excluded.** The selection rule was fixed before any
of this was visible and selected on volatility; dropping a name now for a cost property seen
afterwards is precisely the post-hoc adjustment this programme forbids. **It is recorded here so
that a HIGH-stratum failure is read as 29% toll and not 100% signal.**

### H1 clarified: `2c` is TRADE-WEIGHTED

D278 states H1 as *"mean move per trade ≥ 2c, at the holdout's own measured cost"* and **does not
say whether `2c` is the unweighted symbol mean or trade-weighted.** In-sample the two barely
differed — costs spanned 1.8× across four names. **On the holdout HIGH they span 2.9×** (5.27 to
15.32 bp), so the choice now changes the answer.

**It is TRADE-WEIGHTED, and the reason is correctness rather than convenience:** the left-hand side
*mean move per trade* is trade-weighted, so the right-hand side must be weighted the same way or
the comparison is between two differently-weighted quantities. **Declared here, before the bars
exist, so it is a specification rather than a choice made after seeing which reading passes.**

### The splits, resolved from the sidecar

| symbol | effective | factor | bars before are divided by |
|---|---|---:|---:|
| HLF | 2018-05-15 | ×2.0 | **2.0000** |
| RTX | 2020-04-03 | ×1.589 | 1.5890 |
| CMCSA | 2026-01-05 | ×1.067 | 1.0670 |

**336 dividends across 11 names**, reinvested on the ex-date bar by `load_panel`. The original
eight carried **no splits at all**, so the back-adjustment path is exercised here for the first
time on this fixture family — and D226's residual-step gate is the check that it worked.

---

## RESULT — every one of the five reverses sign

`uv run python scripts/run_holdout_test.py` · `data/d278_holdout_summary.json` · 16 names ×
56,115 bars, 2,160 sessions, 500 rotations.

**Zero of twelve cells clear all five hurdles. All twelve have a negative CAGR.**

### The five winners, in-sample against holdout

| cell | in-sample CAGR | **holdout CAGR** | H5 |
|---|---:|---:|---|
| LOW · `macd_line` | +0.73% | **−1.87%** | **fail** |
| LOW · `impulse_hist` | +0.69% | **−0.71%** | **fail** |
| HIGH · `mass_imbalance` | +0.58% | **−1.22%** | **fail** |
| ALL · `mass_imbalance` | +0.38% | **−0.81%** | **fail** |
| LOW · `mass_imbalance` | +0.17% | **−0.40%** | **fail** |

**All five reverse.** P2 predicted *at least one*; every one did.

### The full table

| cell | move | ×cost | CAGR | Sharpe | H1 | H2 | H3 | H4 | H5 |
|---|---:|---:|---:|---:|---|---|---|---|---|
| ALL `none` | +1.89b | 0.19× | −4.99% | −1.268 | no | no | **YES** | no | YES |
| ALL `impulse_hist` | −0.55b | −0.05× | −1.92% | −1.287 | no | no | no | no | YES |
| ALL `macd_line` | −1.00b | −0.10× | −2.71% | −1.224 | no | no | no | no | YES |
| ALL `mass_imbalance` | −2.40b | −0.25× | −0.81% | −1.528 | no | no | no | no | no |
| LOW `none` | −1.60b | −0.39× | −3.17% | −0.941 | no | no | no | no | YES |
| LOW `impulse_hist` | +0.46b | 0.11× | −0.71% | −0.462 | no | no | no | no | no |
| LOW `macd_line` | −4.00b | −0.96× | −1.87% | −0.911 | no | no | no | no | no |
| LOW `mass_imbalance` | −1.42b | −0.35× | −0.40% | −0.746 | no | no | no | no | no |
| HIGH `none` | +5.56b | 0.33× | −6.77% | −1.133 | no | no | **YES** | no | YES |
| HIGH `impulse_hist` | −1.59b | −0.10× | −3.11% | −1.372 | no | no | no | no | YES |
| HIGH `macd_line` | +2.06b | 0.12× | −3.54% | −1.079 | no | no | no | no | YES |
| HIGH `mass_imbalance` | −3.57b | −0.22× | −1.22% | −1.364 | no | no | no | no | no |

**Best-of-12 floor +0.100; best cell −0.462.** Nothing is close.

### THE FINDING — the base's skill replicates and the filters do not

**Two cells clear the rotation null on BOTH legs, and they are the UNFILTERED base**: `ALL|none`
and `HIGH|none`. The same `S2_short_intra` that cleared hurdle H at the 97.2nd/97.9th percentile
in-sample clears it again on sixteen names it has never seen — **while losing 4.99% and 6.77% a
year.** [FINDINGS §3](../FINDINGS.md) for the fourth time this session: real timing, comprehensively
unprofitable.

**And the filters degrade it.** On the quantity that decides viability — move per trade — the
unfiltered base beats its own filtered versions in **7 of 9** comparisons:

| stratum | `none` | `impulse_hist` | `macd_line` | `mass_imbalance` |
|---|---:|---:|---:|---:|
| ALL | **+1.89b** | −0.55b | −1.00b | −2.40b |
| HIGH | **+5.56b** | −1.59b | +2.06b | −3.57b |
| LOW | −1.60b | **+0.46b** | −4.00b | −1.42b |

**In-sample every one of these filters improved the base. Out-of-sample, seven of nine make it
worse.** That is what a mined filter looks like when the mine is measured.

### Predictions

| | outcome |
|---|---|
| **P1** no cell clears all five | **CONFIRMED** — 0 of 12 |
| **P2** at least one filter reverses sign | **CONFIRMED — all five did** |
| **P3** the unfiltered base loses on the holdout too | **CONFIRMED** — −4.99% / −3.17% / −6.77%, reproducing D264 on sixteen fresh names |
| **P4** the three filters disagree with each other | **CONFIRMED** — on LOW they run +0.46, −4.00, −1.42; on HIGH −1.59, +2.06, −3.57 |

### A defect caught during the run, and it would have flattered the result

`load_panel` builds `cost_fraction` from `L.per_side_bps`, which adds the **ETF half-spread of
1.0 bp** — not D264's 1.5 (low) / 4.5 (high). Repointing the stratum map without repointing the
cost vector would have costed the holdout's high stratum **2.5× too cheaply** and made H1 trivially
easier. **It surfaced because `borrow_vector` raised `KeyError: 'ANF'`** — a guard failing loudly
rather than a number quietly being wrong, which is the whole design intent of D226's guard style.

Costs as actually charged, from the holdout panel's own median close: **RIG 15.31 bp/side**, CNX
7.59, HLF 6.31, NI 6.32 — against COST at **1.60** and HD at 1.66.

---

## Stop — fired, and it closes the family

**The mined construction is closed, and per D278's stop the single-name intraday short closes with
it.** The in-sample search is spent, the holdout is spent, and **no third sample will be selected
from this pool.**

**What replicated:** `S2_short_intra`'s timing, on sixteen unseen names, at the 95th percentile of
both null legs — and it loses 5–7% a year. **What did not:** every filter the mine found, all five
reversing sign.
