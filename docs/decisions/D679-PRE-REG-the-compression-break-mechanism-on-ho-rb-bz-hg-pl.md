# D679 — PRE-REGISTRATION: is the compression break's mechanism real? D672's compression tier on HO, RB, BZ, HG and PL, judged on gross, where no break construction has been read

*2026-09-29.*
- *The principal:*
  - *"I am worried about the underlying mechanism if its real or not. What would confirm it for me is wether the other
    roots have a gross edge but not a net edge";*
  - *then: "I also want a similar study done on the compression break".*
- *A sibling of D678 (`7914bfde`, A1 `ebbe30fb`), on the same five roots and the same fixture, which is still being
  built.*
- ***Committed alone, before its runner and before any outcome on these roots is read.***

## 1. The claim and the record so far

**D672's compression break:** D666's plain break of yesterday's range plus E4, traded only on the **compressed third**
of sessions.
- **Compression** = the mean of the walk-forward percentiles of **rv5** (the previous five sessions' mean day range in
  ATR units) and the **overnight two-way range** ((overnight high − low − |open − prior close|) / ATR). Then comp's own
  walk-forward percentile. C1 = the bottom third.
- **The mechanism story:** a market that has been quiet, recently and overnight, holds unresolved positioning. When
  yesterday's range finally breaks, the move has room to run: compression, then expansion.

**The record:**

| where | read | result |
|---|---|---|
| NQ (development, D672) | C1 net +6.93 bp (t 2.40); +7.56 with single-count friction (D672-A1); a monotone C1 > C2 > C3 ladder | spent |
| ES (development, D672) | C1 about 0; C3 (busy) −5.66 | spent |
| YM, RTY (evidence, D682) | NOT SUPPORTED; on RTY C1 was the worst third (−8.07 net) | spent |
| CL, NG, GC, SI (D676's secondary, overnight input only) | quiet − rest +0.3 to +2.9% of ATR on all four, none above its rotation's p95 | spent |

**The index roots split, and energy and metals lean positive.** HO, RB, BZ, HG and PL have never been read by any break
construction.

## 2. The rule, per root; nothing fitted

**Sessions, contracts, costs, R2 and seals are D678's** (§2–3 there): full size, friction counted once ($6 + the
measured `d507_exec` crossing), the delivery buffer on HO, RB, HG and PL (BZ is cash-settled), and the same fixture and
gates.

**B0, every break (D676's break, single count):**
- armed at the open;
- the first bar to reach yesterday's day-session high + 0.25 A (or low − 0.25 A), same contract, **entered at the
  stop, or at the bar's open if it opens through it, with no extra tick**;
- no entry in the last 30 minutes before the flat time;
- E4: initial stop at yesterday's level, trail 0.25 A, flat at the flat time.
- Gap-through opens are included, as in D672. The overlap with D678's gap trades is reported.

**The tier (D671/D672 functions, unchanged):**
- R = (day high − low) / A;
- rv5 = the mean of R over the previous five sessions;
- on_range = (overnight high − low − |open − prior close|) / A, with the overnight from 18:00 to the minute before the
  root's open;
- p_rv, p_on = walk-forward percentiles among the previous 250 finite values;
- comp = (p_rv + p_on) / 2, and ctier = comp's own walk-forward percentile.
- **C1:** ctier < 1/3. C2 and C3 are the middle and top thirds.
- The percentiles run over each root's usable sessions from 2015-09. Trades count from the first session with a finite
  ctier (about 2017-10).

## 3. Statistics

**The unit:** gross per trade in % of that trade's A.

**Gate 1, the MECHANISM (family; gross only):**
- **(a) Δ = C1 − rest,** each root's mean gross (% of A) in C1 minus in C2 ∪ C3, averaged over the five roots:
  - against the **enumerated rotation** of the tier;
  - each root's ctier series is rotated by the **same** offset k over its own sessions, for every k from 21 to
    (shortest series − 21), so cross-root co-movement is kept;
  - Δ must exceed the rotation's exact p95.
- **(b)** C1's gross (% of A), as a date series averaged over the roots trading that day, > 0 by one-sided HAC t,
  α = 0.05.
- **(c)** Δ > 0 without February–April 2020.

**The mechanism reading** (the principal's criterion, as D678-A1):

| reading | condition |
|---|---|
| **CONFIRMED ACROSS ROOTS** | Gate 1 passes **and** each root's C1 − rest exceeds its own rotation's p50 on at least 4 of the 5 |
| **FAMILY ONLY** | Gate 1 passes, fewer than 4 |
| **NOT CONFIRMED** | Gate 1 fails |

- Net plays no part in the reading.
- The count's one-sided binomial p is reported (5 of 5: 0.031; 4 of 5: 0.19).

**Gate 2, TRADEABILITY** (per root, only if Gate 1 passes; Holm across the five):
- C1 net > 0, one-sided HAC t;
- net > 0 at +1 tick on every fill;
- at least 100 C1 trades;
- net > 0 without February–April 2020.

**Reported only:**
- D672's within-year random-subset placebo on C1 net;
- the C1 / C2 / C3 ladder;
- each input alone (p_rv, p_on) as the tier;
- long / short;
- by year;
- C1's share of gap-through fills, and its correlation with D678's gap book;
- the four groups;
- the component line: daily $ Sharpe net and gross at one full contract; ρ with the rebuilt K8, between the roots, and
  with D678.

**The runner's assertions, each raising in `--selftest` on a broken input:**
- the tier's lag (D671's canary);
- the overnight window ending before the open;
- a stop fill with an extra tick;
- a bar after the flat time;
- the delivery buffer;
- the rotation's offset 0 reproducing the actual Δ.

## 4. Power (rough, stated before the run)

**Assumptions:**
- about 150 breaks a root a year, less 15% for R2;
- the ctier is finite from about 2017-10, so about 7.4 years;
- so about 315 C1 and 630 rest trades a root, with per-trade σ ≈ 0.35 A (D677).

**Standard errors of C1 − rest:**
- per root ≈ 2.4% of A;
- family (five roots, co-moving; effective ≈ 3.5) ≈ 1.3% of A.

**Power:**
- at D676's energy/metals quiet-overnight effect (mean ≈ 1.9% of A), power ≈ 0.45 for Gate 1(a);
- at D672 NQ's size (≈ 4.8% of A), ≈ 0.99.

**This test can confirm a large mechanism. It will likely miss a small one, and a miss at the smaller size is not a
refutation.**

## 5. Predictions

1. **The family's Δ > 0.** Energy and metals leaned positive in D676.
2. **Each root's C1 − rest exceeds its own rotation's p50 on at least 4 of the 5.**
3. **No root passes Gate 2.**
4. **The family ladder is monotone:** C1 > C2 > C3 in gross (% of A).

## 6. Routing

- **CONFIRMED ACROSS ROOTS:** compression before a break is a mechanism of these markets as well as of NQ. The NQ vault
  case gains support from outside its own sample.
- **FAMILY ONLY:** recorded; the NQ result stays NQ-specific.
- **NOT CONFIRMED:** the compression break stays an NQ-specific in-sample finding, as D682 left it.

## Amendment D679-A1, before the run (2026-09-29): CL, NG, GC and SI added as a second family

**The principal:** "In-sample re-reads are not a big deal, its insample for a reason."

**Written before any data gate or outcome of this study.** The runner exists but has not been run.

**What is added.** The same statistics on CL, NG, GC and SI:
- D676's fixture (`fut_opening_globex_1m_cl_ng_gc_si`, gated in `0a6c033f`);
- D676's sessions and its R2 (D676-A1: CL/NG business days to expiry, GC/SI to first notice);
- full size, single count: $6 + the measured `d507_exec` crossing (CL 1.50, NG 1.26, GC 4.21, SI 4.30 ticks);
- B0 armed at the open, no R3 or EIA rule, exactly as §2 defines it for the five.

**Why they can count.** The compression break was found on NQ, not on these roots. D676 read only the overnight half of
the tier on them, as its secondary, and not the full tier or the rv5 half.
- **Family 2 is therefore evidence for the mechanism, but not clean evidence for the overnight input.** That is
  disclosed beside it.
- **Not added:** ES, NQ, YM and RTY. ES and NQ are where the idea came from, and YM and RTY are D682's evidence. Their
  existing C1 − rest reads (D672, D682) are quoted in the result for completeness only.

**How it enters:**

| | what it gets |
|---|---|
| **Primary (unchanged)** | Gate 1 and the mechanism reading on HO, RB, BZ, HG and PL |
| **Family 2** | its own Gate 1(a–c) in the same form: common-offset enumerated rotation over its four roots, and its own mechanism reading |
| **All nine, reported** | the count of roots whose C1 − rest exceeds their own rotation's p50, with a one-sided binomial p at ½ (9 of 9: 0.002; 8: 0.020; 7: 0.090) |

- Gate 2 on family 2 is reported, with Holm within the family. It is not a verdict.
- The four predictions (§5) stay on the primary five.
