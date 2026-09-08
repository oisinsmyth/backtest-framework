# D381 RESULT — Stage 0: `zr` is *more* than the whole tilt, and the tail a book would trade goes the wrong way

**Status:** RESULT. Stage 0 only. **STAGE 1 IS NOT AUTHORISED AND WAS NOT RUN.**
**Date:** 2026-09-08 · **Area:** signal research · **personal track**
Pre-registration: [D381](D381-the-volatility-tilt-zr-scored-alone.md), committed before the runner
existed and amended once, also before it existed.
Runner: `scripts/run_d381_volatility_tilt.py` · Artifact: `data/d381_stage0.json`

**Holdout reads spent: 0. Programme total: 1** (D371). Nothing was fetched, no book was scored, and
under R15 nothing here is a signal.

---

## 0. The verdict in one line

**`zr` alone is STRONGER than the composite D280 built around it — and the decile a short would
actually hold RISES. Stage 0 fails S0-c′, the direction is DIRECTION-INVERTED, and §9's stop
clause applies: the record stops here.**

---

## 1. [ID] — and it caught a real reproducibility defect before any number was read

**The first run of `[ID]` FAILED at 1e-9**, and the cause was not float noise:

| | mean IC | t |
|---|--:|--:|
| D280 published (2026-09-02) | **−0.013726972** | −5.074623 |
| recomputed on today's default panel | −0.013728429 | −5.075204 |
| **relative difference** | **1.06e-04** | — |

**A summation-order artefact is ~1e-16. This is 1.06e-04, twelve orders larger.**

**The cause:** `ragged_panel.load_ragged` gained a **dividend bound** on 2026-09-05 —
[D333](D333-RESULT-the-relisting-clause-holds-and-the-hole-was-costing-money.md), commit
`3849274` — three days *after* D280's artifact was committed, and it defaults to `True`. A
dividend of ≥10% of the close is now applied only if the price fell at least half of what the
distribution implies. **D280's published numbers live on the unbounded panel, which no longer
exists by default.**

**The fix keeps the identity EXACT rather than tolerated**, which is D333's own convention (it
repriced the stack *"under both panels"* and asserted *"identity with D332 under the unbounded
panel"*):

- **[ID] runs on `dividend_bound=False`** — D280's own panel — and **reproduces its published
  −0.013727 / t −5.0746 to 1e-9.** The object is D280's.
- **Stage 0's measurement runs on today's bounded panel**, and both are reported.

**The tolerance was not widened.** Doing so would have buried a live fact: **a published IC in this
programme is not reproducible today without naming the panel it was computed on.**

**[Z]** also passed first: this runner's `zr` is bit-identical to D280's own construction on all
**4,135,181** finite cells, so the discrepancy was never in `zr`.

---

## 2. The measurement D280 said it could not make

**Cross-sectional Spearman IC of the lagged score against the next bar's total return, 2,173
out-of-sample bars, today's panel.**

| universe | score | mean IC | t |
|---|---|--:|--:|
| ALL | `zh` (D280's baseline) | −0.00525 | −1.79 |
| **ALL** | **`zr` alone** | **−0.01856** | **−4.47** |
| ALL | `zh + zv + za + zr` (the composite) | −0.01373 | −5.08 |
| QUAL | `zh` | +0.00462 | +1.43 |
| **QUAL** | **`zr` alone** | **−0.00515** | **−1.16** |
| QUAL | composite | −0.00185 | −0.60 |

### `zr` carries 135.2% of the composite's mean IC — the other three terms DILUTE it

**D280 said *"the gain is entirely `zr`"*. It is more than entirely.** On mean IC, `zr` alone
(−0.01856) is **35% stronger** than the composite it sits inside (−0.01373); adding `zh + zv + za`
makes the ranking *worse*. The composite's higher |t| (5.08 vs 4.47) is a **variance** effect, not
a stronger signal — the same distinction D280 drew for `h / ATR` in its own part 4B and which must
not be described as improving the ranking.

**S0-a CLEARS** (|IC| 0.01856 ≥ 0.006). **S0-b CLEARS** (|t| 4.47 ≥ 2.86, D280's own best-of-161
floor).

---

## 3. S0-c′ FAILS — the IC and the money point opposite ways

**The check that killed it exists only because of the amendment made before the run.** S0-c′
refused to take the direction from D280's prose and required it be demonstrated in money.

| ALL, next-bar realised return by `zr` decile | |
|---|--:|
| **top decile — the most volatile names** | **+11.42 bp** |
| bottom decile — the calmest names | +2.88 bp |
| spread | +8.54 bp |

**The IC is negative, which implies a short on the high-`zr` end. That decile earns +11.42 bp.
Shorting it loses.** Both deciles are positive; there is no end of this score a short can take.

### This reproduces D280's own fourth correction on a new score

D280's sign audit found exactly this shape and wrote the rule:

> *"**a rank IC describes the WHOLE cross-section, a top-N book lives in ONE TAIL**" —
> the same class of error as D279's E′.*

**A Spearman IC over ~1,000 names can be decisively negative while both tails rise**, because it
measures monotone association across the whole distribution and a book lives in ten percent of it.
**`zr` is a real cross-sectional statistic and an untradeable tail book, and only the money test
separates those.**

**Q3′ splits, and the record says so rather than claiming it:** its first clause **held** — `zr`'s
own IC is negative — and its consequence, *"so the implied short is on the volatile end"*, is
**falsified by the money.** D280's part-4C prose ("shorts the quieter names") is **not vindicated
either**: the calm decile also rises, just by less.

---

## 4. Consistent with something already known — stated as consistency, not identity

**PICKUP §3.3** records overnight drift as a property of volatility: high-vol names ran
**+13.81% overnight against −8.97% intraday**, low-vol the reverse. **A positive next-bar return on
the most volatile decile is consistent with that**, and shorting it is fighting a drift the
programme has already measured.

**This record does not claim they are the same object.** It measured a cross-sectional decile on a
daily close-to-close return; PICKUP §3.3 measured an overnight/intraday split on eight names. The
resemblance is a reason to expect the sign, not evidence about the mechanism. *(Two claims of the
form "same object" were withdrawn in this programme today; this one is not being made.)*

---

## 5. What this closes and what it does not

**CLOSES:** `zr` as a directional short candidate on this fixture. **Stage 1's frozen construction
is not run** — §9's stop clause fires (*"the sign inverts → DIRECTION-INVERTED, and the record says
so rather than re-deriving a mechanism for the other direction"*), and the §3 construction is
abandoned rather than re-pointed at the long side.

**DOES NOT CLOSE, and is not proposed here:**

- **The long side.** +11.42 bp on the volatile decile against +2.88 on the calm one is a **measured
  spread of +8.54 bp with no null, no cost, no hedge and no book**, and it is DIRECTION-INVERTED
  relative to a declared short. Under gate 1h that **counts against the mechanism**, and turning it
  into a long candidate is a new hypothesis needing its own pre-registration. **It is also the
  σ² tax's own territory** (FINDINGS §1b: 59% of D264's gross), so a long on the volatile decile
  starts with a known bill.
- **D280's composite as a whole.** This scored `zr`; `zh`, `zv` and `za` were measured only as they
  appear in the artifact.
- **C1b's `VOL_XS` market state.** A different axis, explicitly not this record (§0a of the
  pre-registration).

---

## 6. Predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | Stage 0 clears S0-a: \|mean IC\| ≥ 0.006 | **HELD** — 0.01856, three times the bar |
| **Q2** | *(load-bearing)* the book beats `B_v` | **NOT REACHED** — Stage 1 unauthorised |
| **Q3′** | `zr`'s IC is negative → short the volatile end | **SPLIT: sign held, consequence FALSIFIED** (§3) |
| **Q4** | *(against)* the σ² tax takes ≥ 40% | **NOT REACHED** |
| **Q5** | ρ to S1/S2 below 0.3 | **NOT REACHED** |
| **Q6** | interior peak on the cap profile | **NOT REACHED** |

**Two of six scored, and the one that decided the record is the amended one.**

---

## 7. What is worth carrying

1. **A published IC is not reproducible without naming its panel.** D280's number needed
   `dividend_bound=False` to reproduce exactly. **Any record re-deriving a pre-D333 quantity must
   say which panel it is on**, and D333's flag makes that cheap.
   **This is now [R16](../RULES.md#r16)**, added 2026-09-08 — the lesson is general (every study
   here inherits numbers, and the pipeline has moved under them at least twice on record), so it
   is a standing rule rather than a footnote to this result.
2. **`zr` alone beats the composite that was built around it.** A unit-weight combination can be
   *worse* than its best component, and D280's own framing — that its combination was the finding —
   understated `zr` and overstated the sum.
3. **The money test is not a formality.** It was added by amendment, before the run, because
   D280's prose contradicted D280's correction — and it is the only check here that failed.
   **A rank IC and a decile book are different objects, and this is the third time in this
   programme that distinction has decided a verdict** (D279's E′, D280's own audit, now this).

---

**Status footer.** Stage 1 was not run and is not authorised. `docs/BOOK.md` holds S1 and S2,
neither at capital; `docs/BOOK_PROP.md` is empty. **Only the principal closes a research avenue
(R15)** — this record reports a failed stage-0 gate and stops, as its pre-registration required.
