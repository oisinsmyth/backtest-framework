# D274 — The exit-timing diagnostic — RECONSTRUCTED POST-HOC

**Status:** **RECONSTRUCTED POST-HOC. RUN AND CLOSED.** A time-based exit does not rescue the
intraday short, and **a RANDOM exit bar beats a fixed one.**

> **THIS RECORD WAS WRITTEN AFTER THE RUN — 2026-09-02, from the committed script, the commit
> messages, and the records that cite it. It is NOT a pre-registration and carries NO
> pre-registration claim.** [R8](../RULES.md#r8) requires hurdles committed before the data is
> touched; **nothing of the sort exists for D274.** **Its Predictions section is OMITTED for that
> reason** — a prediction written after the answer is known is not a prediction, and back-filling
> one would be the worst thing this record could do. **Every figure below is traceable to the
> script, to `8d153ac`, or to a record that quoted D274 in advance of its own run** (`07bf541`,
> `9a3eec3`); where a figure is not, it is listed under *What is not recoverable* rather than
> estimated.
>
> **And this record is worse-supported than D271's**, for one specific reason recorded below:
> **`scripts/d274_exit_timing.py` writes NO artefact.** It prints to stdout. The k-curve does not
> exist anywhere on disk.

**Run:** 2026-09-01 · commit `8d153ac`
**Record written:** 2026-09-02
**Area:** Strategy research · **personal track**
**Ledger: 24** (12 k × 2 arms), counted retroactively in [D275](D275-the-change-of-character-on-single-names.md)'s ledger.

---

## The question, and who asked it

**Asked by the principal after [D273](D273-the-profile-as-a-travel-estimator.md): is the EXIT the
fixable problem?** The motivating gap, from `8d153ac`:

> **maximum favourable excursion runs 6–13× the cost bar while realised P&L keeps 3–6% of it.**

D273's own table is the source of the excursion side: **MFE runs 30.3 bp (LOW · S1) to 128.4 bp
(HIGH · S2)** against cost bars of 4.00 / 8.42 / 12.84 bp. **A trade that travels 87 bp in its
favour and books 5 bp looks, on its face, like a capture problem rather than a signal problem.**

## Why TIME, and why the three prior closures do not transfer

**Take-profits are closed three times over — and none of it transfers**, which the script's
docstring says in as many words:

| | what it closed | why it does not answer this |
|---|---|---|
| **D235** | seven stop/target overlays; against the correct matched-count random-exit null the **best sat at the 63rd percentile** and the trigger carried no information | levels were 10–30% |
| **D255** | the best level of 600 with perfect hindsight was worth **+0.017 Sharpe**, because **97.2% of trades never travel far enough to be cut** | levels were 10–30% |
| **D256** | every take-profit cell hurt | levels were 10–30% |

**Those levels were 10–30% against an intraday MFE of 30–128 bp — 10 to 100 times larger than the
entire excursion.** They were never testing this book. [FINDINGS §5](../FINDINGS.md) records the
overlay ceiling and D256's correction to the reason for it; **neither reaches the intraday
horizon.**

**Time was the untested lever, and it is structurally different from everything else in this
programme:**

```
turnover = sum |dpos|,  so one entry plus one exit is 2
           whether the hold is 3 bars or 30
```

**Exiting earlier costs NOTHING extra and lowers the variance tax
([FINDINGS §1b](../FINDINGS.md)). It is the only lever found in this programme that improves the
numerator without touching the denominator.** That is the whole reason the study was worth an hour.

---

## The construction

`scripts/d274_exit_timing.py`, on the same panel and the same two arms D271 anatomised:

```
arms     LOW:S2_short_intra   HIGH:S1_short_intra   (D264's constructions, unchanged)
paths    per trade, the cumulative short P&L path from entry to the book's own exit
sweep    exit at bar k for k in {1,2,3,4,6,8,10,12,16,20,26,40}      -- 12 points
rule     exit at  min(k, natural end)  -- applied to EVERY trade
null     R7: one exit bar drawn UNIFORMLY from [0, min(k, len))       -- rng seed 0
report   mean P&L per trade, gross bp, against the arm's own 2c bar
```

**No rule is proposed and no cell is promoted. The FULL k-curve is reported rather than a chosen
k** — the docstring is explicit that *"selecting one from a 12-point sweep is a search and would
need its own pre-registration."*

**Cost bars are the arms' own, from the panel:** **LOW 4.00 bp**, **HIGH 12.84 bp**.

---

## DEFECT — the first table had SURVIVORSHIP IN k, and it was caught before it was reported

**Stated first because it is the finding's load-bearing correction**, and it is now carried in the
script's docstring so it cannot be lost:

> *"The first version averaged only over trades that LASTED k bars, which selects trades whose
> signal stayed on, and that is not a rule anyone can trade."*

**5,338 trades shrinking to 781 by k = 20.** Conditioning "exit at bar 20" on *having survived to
bar 20* keeps only the trades whose signal was still on — **which is precisely the subpopulation
that was working** — and the resulting curve flattered a fixed exit at every large k.

**Corrected to `exit at min(k, natural end)` over EVERY trade, so the sample never shrinks and the
denominator is constant across the whole sweep.** The flattering curve vanished.

**This was caught and fixed before the table was reported.** It is recorded here anyway, because a
defect found by the author is still a defect and the pattern — a sweep whose sample composition
moves with the swept parameter — is worth the entry.

---

## RESULT — the corrected sweep kills it

**HIGH · `S1_short_intra`** — 5,338 trades, cost bar **12.84 bp**, signal's own exit **+5.13 bp**:

| | mean P&L | vs the 12.84 bp bar |
|---|---:|---:|
| **best fixed k — bar 8** | **+3.74 bp** | 0.29× |
| the signal's own exit | **+5.13 bp** | **0.40×** — the best of everything tested |

**The best fixed-k exit is WORSE than the signal's own exit, and nothing in the sweep reaches the
cost bar.** The best ratio anything achieves is **0.40×**, and it belongs to the rule that was
already there.

**LOW · `S2_short_intra`** — 1,507 trades, cost bar **4.00 bp**, signal's own exit **+3.12 bp**:

| | mean P&L | vs the 4.00 bp bar |
|---|---:|---:|
| **best fixed k — bar 8** | **+4.06 bp** | **1.01×** |
| the signal's own exit | +3.12 bp | 0.78× |

**This is the one cell where a fixed exit beat the signal's own, and it is not a finding.** It
clears the bar by **one percent**, and it is **the best of a 12-point sweep**. `8d153ac` labels it
correctly and in advance of anyone else reading it: *"taken from a 12-point sweep, so it is a
search result and not a finding."* **No best-of-12 floor was computed** — see *What is not
recoverable* — so 1.01× has no null to be measured against and must not be quoted as a pass.

### AND R7 REPRODUCES EXACTLY — a RANDOM exit bar beats a fixed one

On **HIGH · S1**, the random exit beats the fixed one at most k:

| k | fixed exit | **R7 random exit** | excess |
|---:|---:|---:|---:|
| 10 | +3.64 bp | **+6.29 bp** | **−2.65 bp** |
| 16 | +3.74 bp | **+7.45 bp** | **−3.71 bp** |
| 26 | +5.13 bp | **+8.18 bp** | **−3.05 bp** |

> **The exit TRIGGER carries no information.**

**This is [R7](../RULES.md#r7) reproducing on a third population.** R7 exists because D235's seven
overlays all beat their baseline and **none beat a matched random-exit control**; that was measured
on daily ETFs. **It is now measured on intraday single names, and it lands the same way.**

### So the MFE gap is not a defect — it is a property of maxima

The 6–13× excursion that motivated the study does not indicate a capture failure. From `8d153ac`:

> **a driftless walk over these holds produces 130–200 bp of expected MFE against the ~82
> observed.**

**The observed excursion is LOWER than a no-signal random walk would produce over the same holds.**
The maximum of a path is upward-biased by construction; comparing realised P&L to it and calling
the difference "money left on the table" is comparing a value to an order statistic.

> **There is no realisable rule found here that captures more than the signal's own exit does.**

---

## OTHER DEFECTS AND LIMITS, none of which change the verdict

Three of these are properties of the committed script and are visible in it now.

### 1. The R7 null is ONE draw per trade, not a distribution — so there is no percentile

`rng.integers(0, min(k, len(x)))` draws **a single** random exit bar per trade per k, and the arm's
null is the mean over those single draws. **No sampling distribution is built, no p95 is computed,
and no percentile verdict is available.** The comparison is a point estimate against a point
estimate.

**It does not change the reading here, because the sign and the size are not close** — the random
exit wins by 2.65 to 3.71 bp on means of 3.6 to 8.2 bp, across three separate k, on 5,338 trades.
**But it is weaker than R7's own standard as [D276](D276-the-leg-relative-exit.md) then applied it**
(hurdle L2 required a matched random-exit *null* and a percentile), and a reader should treat
D274's null as a **diagnostic comparison rather than a hurdle**.

### 2. The script writes no artefact

Everything above reaches this record through commit messages. **`data/` contains no D274 file**,
because the script's only output is `print`. That is why so much of the study is listed as
unrecoverable below, and it is the practical cost of `8d153ac` being the only record D274 had
until now.

### 3. `REPO = Path.cwd()`

Unlike `d271_trade_anatomy.py`, which resolves the repo from `__file__`, this script uses the
working directory. **It reproduces only when run from the repository root.**

### 4. The sweep is gross, and that is correct here but must be said

The k-curve is **gross** mean P&L per trade against the `2c` bar. Costs are not re-charged per k,
and they should not be: turnover is invariant to hold length, which was the entire premise. **The
comparison is therefore valid, and it is also the reason no CAGR, Sharpe or drawdown exists for any
of these cells.** Nothing here is a scored cell.

---

## What D274 closed, and how far the closure reaches

**Time-based exits are CLOSED on this fixture.** It is recorded as such in
[PICKUP.md §2](../internal/PICKUP.md) — *"exits, time-based | D274 | a random exit bar beats a fixed
one"* — and D274's verdict was then **used as a pre-registered input by a study that had not yet
run**, which is the strongest evidence the finding was believed rather than rationalised:

- **D276's pre-registration (`07bf541`) quotes D274's numbers before its own run**, and sets hurdle
  **L2** to the R7 matched-exit null *because of them*: *"beating the state rule only shows that
  less churn costs less, which is arithmetic."*
- **D276 then failed L2**, and its result (`9a3eec3`) states what the two say together:

> **A LATER exit than the signal's own loses (D274), and an EARLIER one loses more (D276). The
> signal's own exit is not leaving money on the table — it is already at the top of a flat curve.**

**D276's stop closes the exit question entirely on this fixture: D274 closed time exits, D276
closed structural ones, and no third exit family is registered.**

**What is NOT closed by this record:** D274 tested **two arms on eight survivor names at fifteen
minutes**. D264's bounding language applies unchanged — the sample is survivor-only and **41.6% of
the 2013–17 cohort is unreachable at this frequency** — and a fixed-time exit on a different
horizon or a different book is a separate question this never touched.

---

## Ledger

| count | N |
|---|---:|
| **fresh — 12 k × 2 arms** | **24** |
| carried from D273 | 46,233 |
| **total, as this study stood** | **46,257** |

**The 24 is not invented here.** D275's ledger row reads *"+ D274's exit sweep (12 k × 2 arms) and
the halt test's 6"*, taking 46,233 to **46,263** — **+30, of which 24 are D274's.** The count was
therefore registered contemporaneously even though the record was not.

**Convention:** [R13](../RULES.md#r13) is binding from 2026-09-01 but explicitly leaves **D247–D276
on the older single-cumulative convention**, unrestated. **This record keeps it** rather than
retroactively re-scoping a count, which would be exactly the kind of after-the-fact adjustment the
rest of this file exists to avoid.

---

## WHAT IS NOT RECOVERABLE FROM THE ARTEFACTS

**Substantially more than for D271, because the script writes nothing to disk.** Listed in full:

1. **Any pre-registration.** **There was none.** No commit before `8d153ac` contains a D274 design,
   hurdle set or prediction. **The Predictions section of this record is omitted, not empty.**
2. **The full 12-point k-curve, for either arm.** The script prints and exits. **Only the four
   points quoted in commit messages survive: HIGH · S1 at k = 8, 10, 16 and 26.** The values at
   k = 1, 2, 3, 4, 6, 12, 20 and 40 are **not recoverable**.
3. **The entire LOW · S2 curve except its best point.** Only *"best is bar 8 at 4.06 bp"* was ever
   written down. **Every other k on that arm is not recoverable.**
4. **Every random-exit value on LOW · S2, at every k.** `8d153ac` reports the R7 comparison **only
   for HIGH · S1**. **Whether a random exit also beat a fixed one on the low-vol arm is not
   recorded and cannot be recovered from the artefacts** — and the headline is therefore
   established on **one arm of two**, which is stated here rather than smoothed over.
5. **Any best-of-12 floor.** None was computed. **LOW · S2's 1.01× has no floor to be judged
   against**, which is precisely why `8d153ac` calls it a search result.
6. **Any percentile, p-value or bootstrap.** See defect 1 — the null is a single draw per trade.
7. **The pre-correction (survivorship-in-k) table.** Only **"5,338 shrinking to 781 by k = 20"**
   survives. Its actual numbers are gone.
8. **The MFE figures quoted in `8d153ac` as "6–13× the cost bar" and "~82 observed"** are not
   produced by this script; they come from D273's diagnostics. **The exact per-cell MFE values
   D274 was reasoning from are D273's table, and the "3–6% of it" capture ratio is not written to
   any artefact.**
9. **The "130–200 bp of expected MFE from a driftless walk"** is an analytic estimate stated in the
   commit message. **No script in the repository computes it**, and it should be read as an
   order-of-magnitude argument, not a measurement.
