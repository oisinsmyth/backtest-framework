# D448 RESULT — the direct test: the overnight drift is in the T+0 future too, at 0.9944 correlation, and the settlement kill-check is DISCHARGED

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D448-RESULT-the-direct-test-the-drift-is-in-the-T0-future-too-and-the-settlement-kill-check-is-discharged.md`. The H1 above is the full title.*

**MEASUREMENT record. No hurdle is claimed and no candidate is admitted.** The falsifier named in
[`docs/research/prop-firm-leads/01`](../research/prop-firm-leads/01-prop-lead.md) §5.1 — *"computable on any
fixture holding both SPX and ES"* — is now run. **Runner:** `scripts/d448_es_front_month.py`.
**Fixture built:** `data/fixtures/es_front_1m_boundaries.csv.gz`. **Evidence:**
`data/d448_direct_settlement_test.json`, `data/d448_es_spy_pairs.json`.
**Predictions were written into the runner before it ran; two of three hold, and the third fails
for an identifiable reason.**

---

## AMENDMENT, 2026-09-12 — **§3's `+1.49%/yr` WAS HALF A RATE CYCLE. THE HEADLINE IS UNCHANGED.**

**Re-run on the completed acquisition (2010-06-06 → 2026-09-09) as
[D451](D451-RESULT-the-complete-acquisition-T1-is-testable-and-the-cash.md).**

**What changed:** this record's `ES − SPY` overnight of **`+0.59 bp/day, t +3.54`** reads
**`−0.11 bp/day, t −0.82` — INSIGNIFICANT — on the full sample.** This record ended at 2022-08,
inside the low-rate era, and therefore measured **one half of a rate cycle.** `q − r` averages to
about zero across a whole one, which is what a financing spread does and what a settlement effect
would not. **§3's mechanism stands; its LEVEL does not, and should not be quoted as a standing
number.**

**What did not change, and is now better supported: the T+1 era is testable at last (432 pairs),
and the settlement hypothesis fails on it in the direction opposite to its own prediction** —
the cash-futures gap GROWS as the settlement lag shortens (+1.09 → −0.31 → −1.66 bp/day), and is
largest exactly where cash is closest to futures. **§4's "the T+1 regime has ZERO pairs" is
discharged.**

---

## THE ANSWER

> **ES — the T+0 instrument — carries a POSITIVE overnight drift of +6.55%/yr over the same clock
> window, against SPY's +5.65%. Both positive, correlated 0.9944. The settlement mechanism does
> not operate in the US, and China's opposite-signs result does not replicate here.**

**For the prop track: C1's overnight drift EXISTS IN THE INSTRUMENT THAT WOULD BE TRADED.** The
kill-check that had been hanging over D440's entire input series is discharged.

| series | ann% | bp/day | t | n |
|---|---:|---:|---:|---:|
| `spy_overnight` | **5.65%** | 3.91 | 2.47 | 1,747 |
| **`es_overnight`** | **6.55%** | **4.51** | **2.83** | 1,747 |
| `spy_rth` | 3.64% | 2.71 | 1.41 | 1,747 |
| `es_rth` | 3.66% | 2.73 | 1.40 | 1,747 |

**China's result was T+1 cash −0.073% (t −4.03) against T+0 futures +0.055% (t +3.19) — opposite
signs. The US gives the same sign, the same magnitude, and a 0.9944 correlation.**

## 1. Why this needed no roll adjustment, which is why it was safe to run now

**The acquisition prompt names the roll as the gate that matters most** — *a synthetic gap in an
adjusted continuous series scored as a price move that never happened*, and this study's downstream
statistic is an overnight return, exactly the quantity a roll gap would forge.

**So no adjusted series was built.** Every return takes **both endpoints from the same contract**,
and any session pair whose front month differs between the two days is **dropped** — 33 pairs.
**There is no stitching, so there is no synthetic gap, so there is nothing for an adjustment to get
wrong.**

**Front month is the highest-volume contract on the day — measured, not a calendar rule.**

## 2. The validation gate, which is the part that makes the rest credible

> **`[Y2]` corr(ES, SPY) = 0.9944 overnight and 0.9995 RTH.**

**That is the *"is this the instrument I think it is"* check** — the one the acquisition prompt made
its final gate, because it is the only test that catches a wrong-200 or a mis-mapped symbol rather
than a malformed file. **4.87M ES bars were filtered from 625M raw rows across 15 files; the symbol
regex excludes options (`ESF1 C0375`) and calendar spreads (`ESM0-ESU0`) and keeps 40 outright
contracts.** A correlation of 0.9944 is not something a mis-extraction produces.

**Conventions matched to SPY exactly:** `p0930` is the **open** of the 09:30 bar and `p1600` the
**close** of the 15:59 bar, whose interval `[15:59,16:00)` makes its close the 16:00 print —
the one-minute analogue of the equity fixture's 15:45 bar. Timestamps converted US/Eastern with DST.

## 3. The one real difference, and it is carry, not settlement

**ES minus SPY overnight: +0.59 bp/day, t +3.54** — small, significant, and **+1.49%/yr**.

**That is the cost-of-carry term, not a settlement effect.** For a futures, `F = S·e^{(r−q)(T−t)}`,
so the futures **price** return exceeds the spot **price** return by `q − r`. Over 2010–2022 the S&P
dividend yield ran ≈1.9% against an average short rate ≈0.6%, giving **`q − r` ≈ 1.3%/yr against
the measured 1.49%.**

**And it lands in the overnight window because that is where ex-dividend price drops occur** — at
the open. **SPY's fixture is split-adjusted with dividends supplied separately, by its own meta**, so
SPY's price drops on ex-dates and ES's does not.

**The year pattern fits the same story** and was not fitted to it: the gap is **+2.4% to +3.6%/yr in
the ZIRP years 2013–2016**, falls to **+1.1% / +0.27% / −0.22% across the 2017–2019 hiking cycle**,
returns to **+1.99% in 2020** when rates were cut, and is **−0.61% in 2022**. `[NOT MEASURED HERE —
q and r were not extracted, and this is an arithmetic consistency check, not a decomposition.]`

## 4. Coverage, stated plainly

**1,747 matched pairs.** ES panel covers **2010-06-07 → 2022-08-16**, 2,492 sessions.

| | 2010 | 2011 | 2012 | 2013 | 2016–2021 | 2022 |
|---|---:|---:|---:|---:|---:|---:|
| ES sessions | 30 | 67 | 105 | 210 | 248–251 | 156 |
| matched | 0 | 8 | 42 | 137 | 190–196 | 122 |

**The sample is solid from 2013 and thin before it** — the early ES front month does not reliably
print at both 09:30 and 15:59, and SPY's own pair construction requires a post-market and a
pre-market print. **Nothing was interpolated to fix this.**

### THE LIMITATION THAT MATTERS MOST

> **The T+1 regime has ZERO pairs.** ES data ends **2022-08-16** and T+1 began **2024-05-28**.
> **The direct test cannot speak to the regime [D447](D447-the-settlement-hypothesis-is-not-supported-the-drift-runs-the.md)
> found most anomalous** — the one whose SPY overnight reads 52.48%/yr.

**The acquisition's final chunk, 2022-08-17 → 2026-09-11, is still `submitted`. When it lands this
test should be re-run**, and it is the only thing that would close the T+1 question on both sides.

**What the two regimes it does cover show:** SPY 1.88% vs ES 3.21% under T+3 (791 pairs), SPY 10.59%
vs ES 10.95% under T+2 (956 pairs). **ES tracks SPY under both rules, and ES's own rule never
changes** — which is the within-study control for D447's era confound.

## 5. Predictions

| | prediction | outcome |
|---|---|---|
| **Y1** | ES carries a **positive** overnight drift, not the zero-or-negative the settlement story needs | **CONFIRMED** — +6.55%/yr, t 2.83 |
| **Y2** | ES and SPY overnight correlate **above 0.90** — a validation gate, not a finding | **CONFIRMED** — **0.9944** |
| **Y3** | ES's drift is **smaller** than SPY's, because SPY's overnight carries the microstructure D402 measured | **WRONG** — ES is **larger**, by +0.59 bp/day at t +3.54, **and §3 identifies the reason: the difference is `q − r`, which I failed to account for when writing the prediction** |

**Y3's failure is the useful one.** I reasoned about microstructure and forgot the carry term
entirely — and the carry term is both larger and in the opposite direction. **The measured +1.49%/yr
against a predicted `q − r` ≈ 1.3%/yr is a stronger check on the extraction than the correlation
is**, because it is a number that had to come out right for a reason external to the data.

## 6. What this settles

- **The settlement mechanism is rejected on US data by two independent routes.** D447 rejected it
  **within cash**, across two rule changes, with a clean RTH placebo. **D448 rejects it across
  instruments**, at the same clock, on the same days. **Neither is decisive alone; together they
  leave the hypothesis with no US support.**
- **C1's kill-check is discharged.** The drift is in the future.
- **It does NOT rescue C1**, and nothing here touches
  [D440](D440-RESULT-the-gaussian-was-worth-five-sixths-of-the-value-and-it.md):
  **the account still fails P4 by 12×** under the [R11 ruling](../RULES.md#r11). **What is removed is
  a reason to doubt the input, not a reason the book failed.**
- **It says nothing about C1's PATH in the instrument.** This measures two boundary prices per
  session. **D440's MAE is a path statistic and ES trades the 20:00–04:00 window that the equity
  proxy cannot see** — re-running D440 on ES remains owed, and §4's coverage is the constraint on it.

## 7. Provenance and hygiene

**`databento` is installed in the system interpreter and is NOT a project dependency**, so the build
step runs under bare `python` and the record says so. **`pyproject.toml` was not touched** — adding
that dependency belongs to the acquisition session.

**The raw DBN under `temp/databento/` was read only.** The acquisition's own manifest says
*"Acquisition only — no fixture was built and no study was run"*; **this record builds the first
fixture from it, into `data/fixtures/`, so nothing downstream depends on a deletable directory.**
