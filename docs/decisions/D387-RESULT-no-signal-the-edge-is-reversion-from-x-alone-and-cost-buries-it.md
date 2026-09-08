# D387 RESULT — no signal: the edge is short-horizon reversion available from `x` alone, and cost buries it either way

**P1 fails at every cell. Under R15 there is no signal: the gross mean per trade is positive but is
NOT above the nulls.** §10's close condition is met. **Under R15 the decision to close is the
principal's.**

Pre-registration `b83ad16`, runner `b92d554` — both predate this file (R8). Signal test, path-invariant
lens, scored per TRADE. Admits nothing; holdout #2 untouched.

600 names of 1,325 eligible, `us_shorts_daily_raw.csv.gz`, 2010-01-04 → 2026-08-26. 20,062 cells in
3,044 s at **5.98× on 6 workers — 100% efficiency**.

---

## 1. The verdict

**0 of 18 cells clear.** Best margin **−1.18 SE** against a bar of +2.

```
        type  lam   H  names  trades  GROSS bp   net bp  spread  expo   N2 p95    A p95   vs N2
reversal >1%   60   5    584  139158       0.6   -127.3   127.9  0.374    147.0    127.1   -1.37
reversal >1%  120  20    579  115484      50.2    -80.5   130.7  1.196    584.4    482.8   -1.19
reversal >1%  250  20    495   63337      78.4    -59.3   137.7  0.716    755.9    607.6   -1.19
    move >2%   60   5    591  137993      -8.9   -147.7   138.8  0.370    158.2    134.7   -1.44
    move >2%  120  20    583  118014      28.5   -110.8   139.3  1.221    627.6    526.1   -1.29
    move >2%  250  20    508   71480      88.1    -54.0   142.1  0.797    788.6    672.5   -1.18
```
*(abridged; all 18 in `data/d387_level_reversion.json`)*

**THE PRE-REGISTERED BAR WAS UNREACHABLE AND THE RECORD SAYS SO.** The N2 null's per-name draw-mean
spread is **415 bp**, so "p95 + 2 SE" sits at **1,975 bp** against an observed 88.1 bp. **No realistic
edge on daily bars could ever clear that.** §6 required the record to say whether the null is
decisive: **N2 at 20 draws is NOT decisive at the margin the bar demands.** This is D384's H4 problem
again — a hurdle whose bar nothing could reach — and it means P1's failure carries less information
than the 0/18 suggests.

**The informative comparison is against the null's CENTRE, and it is where the result actually lives.**

---

## 2. The observed beats a shuffled PATH — and does not beat a rotated DENSITY

Per-name displacement against each null's centre, with a sign test across names:

```
        type  lam   H    n  gross bp   N2 p50  z vs N2    sign p    A p50  z vs A
reversal >1%  120  20  579      50.2    -28.9     0.36  1.16e-18     23.1    0.01
reversal >1%  250  20  495      78.4    -36.3     0.36  2.00e-13     49.2    0.28
    move >2%  120  20  583      28.5     -6.8     0.32  1.03e-13     73.6   -0.14
    move >2%  250  20  508      88.1     -5.7     0.28  1.53e-10    129.0    0.06
```

**Against N2 the displacement is overwhelming** — `p` down to 1.2e-18 across 579 names, every cell
positive, every sign test significant. **Against A′ it vanishes**, and in several cells A′ is *ahead*
(129.0 against 88.1 at the best cell).

**The two nulls destroy different things, and the difference is the whole finding.** N2 destroys the
real price path; A′ destroys only the density's **alignment with the current price**, on the same real
path. Beating N2 but not A′ says the edge is **not in the alignment** — it is in trading a real path
at extreme `x` and betting on reversion. **A misaligned density picks a different set of extreme-`x`
bars and does just as well.** The event-density conditioner adds nothing to what `x` already carries.

**That is exactly why R7 demands a persistent-selector control**, and it is the only reason this study
produced a readable answer rather than the 1e-18 headline.

---

## 3. A defect in my own comparison, sized rather than waved at

**The observed and the nulls did not use the same gate.** The observed used the pre-registered causal
expanding 90th percentile; the nulls used `decisions_topn` — the observed count at their own
highest-`R` bars — which I introduced when optimising and called "conservative" without measuring it.

**It is worth up to +126 bp**, which is larger than the entire claimed edge:

```
        type  lam   H    n  expanding bp   top-n bp  top-n edge   A p50 bp
reversal >1%  120  20  117          20.5       51.6        31.1       72.4
    move >2%  120  20  117         -23.7      102.8       126.5       96.3
    move >2%  250  20  100          -5.3       69.0        74.3       96.9
```

So "A′ matches the observed" was partly a statement about the **gate**, not the density. **Re-checked
gate-matched** — the observed run through the same top-n gate as A′, on 98–117 names:
**A′ still beats the observed in 6 of 8 cells.** §2's conclusion survives, on a smaller sample and
weaker evidence than the headline table implies.

**The clean re-run gives every arm one gate.** That the null was handed the better one also means
P1's failure was measured against a handicapped treatment — conservative, but not what the record
declared.

---

## 4. Cost buries it regardless of any of the above

**Corwin–Schultz on the names actually held: 127.9–142.1 bp.** Best gross **88.1 bp**. **Net is
negative in all 18 cells**, from −54.0 to −147.7 bp. Breakeven equals the gross by construction.

**Q4 predicted exactly this** — "the gross edge is smaller than the round trip" — and it held
emphatically. Even granting the whole gross edge as real, it does not pay for one round trip.

---

## 5. Trade distribution and dependence — best cell (`move >2%`, λ 250, H 20)

```
              mean:   88.1 bp        win rate: 0.543        skew: -0.172
            median:  134.0 bp        kurtosis: 3.903
   trimmed 1% both:   93.8 bp        ex-top 1%: 48.3 bp     ex-bottom 1%: 133.6 bp
```

**The mean sits BELOW the median (88.1 against 134.0): the LEFT tail is doing the work.** Removing the
top 1% halves the mean; removing the bottom 1% raises it. **Q6 predicted the opposite** — that a few
big winners would carry it — and is falsified in direction.

**What it depends on:**

```
  names to half the P&L: 30 of 508    top-1 3.8%   top-5 12.7%   top-10 21.5%
  ALIVE 366 names: +142.4 bp     DEAD 142 names: -51.8 bp     (28.0% dead)
  cheap half +106.0 bp   dear half +70.3 bp   (median price $31.38)
  trade-weighted +105.0 bp vs equal-weighted +88.1 bp   profitable names 61.6%
```

**Concentration is NOT the problem here** — 30 names to half the P&L out of 508 is diffuse, and 61.6%
of names are profitable. **Survivorship is**: the whole edge is in the names still alive, and the dead
28% lose money. And the cheap half earns more while paying more in bp, so cost erodes it fastest
exactly where it is largest.

---

## 6. The secondary direction test was VACUOUS BY CONSTRUCTION — my error

§3 declared continuation as a second look, and §10 said that if it "clears equally, the conditioner
marks volatility, not direction."

**It cannot.** For a symmetric signed trade, `direction = −1` flips the sign on the *same* decision
bars, so continuation is the exact arithmetic negative of reversion — measured across 10,025 cells,
`max |revert + continue| = 0.000e+00`. **The second look adds no information and §10's third abandon
condition can never fire.**

The right test for "marks volatility, not direction" is `|return|` or the dispersion of returns at
eligible bars against the nulls. **It was not run**, so that question is open.

---

## 7. Predictions scored

| | prediction | outcome |
|---|---|---|
| **Q1** | the primary clears N2 somewhere | **FALSIFIED.** 0 of 18, and the bar was unreachable anyway |
| **Q2** | `move >2%` beats `reversal >1%` | **SPLIT.** `move >2%` wins on gross at the long holds (88.1 vs 78.4) and loses at every short hold (−8.9 vs +0.6). No clean ordering |
| **Q3** | **A′ is the harder null** | **HELD, and it decided the study.** A′ p95 is below N2's in every cell, but A′ is the null the observed cannot beat — the one that matters |
| **Q4** | the gross edge is smaller than the round trip | **HELD.** 88.1 bp gross against a 142.1 bp measured spread |
| **Q5** | shorter holds beat longer | **FALSIFIED, cleanly and monotonically.** Gross rises with hold in all six type/λ combinations. A level is not a local object on this evidence |
| **Q6** | **AGAINST myself: mean exceeds median, a few winners carry it** | **FALSIFIED in the opposite direction.** Mean 88.1 sits *below* median 134.0 — the left tail does the work |
| **Q7** | `[LAG]` and `[CAUSAL]` hold first time | **HELD for those two** — but `[QTY]`, `[POOL]` and `[SPLIT]` each fired first. **Third study running where the underlying hope was wrong** |

**Four of seven falsified**, two of them (Q5, Q6) in the direction opposite to the prediction.

---

## 8. Assertions

`[REC]` 0.000e+00 · `[MASS]` **4.996e-16** · `[LAG]` 0 bars vs an independent re-derivation ·
`[SIGN]` +0.1379, legs exactly opposite in money · `[QTY]` · `[CAUSAL]` 0.000e+00 · `[POOL]` 0.00% ·
`[NULL]` observed 0.143 / N2 keeps 0.160 / sd ratio 0.945 · `[SPLIT]` guard refused 1 by probe, no
unlock in the module · `[X]` all five breaks raise.

**Three fired during construction and each found a real defect**, all in the runner commit: the
warm-up spike making the gate unreachable for the whole sample (`[QTY]`), the control eligible on bars
the treatment was not (`[POOL]`), and a self-referentially broken guard check (`[SPLIT]`).

---

## 9. What this establishes

**Establishes:**
- **No signal under R15.** Gross is positive at long holds but not above the nulls, and net is
  negative in all 18 cells against a measured spread.
- **The edge that exists is short-horizon reversion from `x` alone.** A time-rotated density does as
  well or better, gate-matched. **The event-density conditioner adds nothing.**
- **`∫f` is exactly the EW event rate** (4.996e-16) — the fork-(a) identity holds in production.

**Does NOT establish:**
- Anything about **volatility conditioning** — §6's test was vacuous by construction.
- A clean null comparison: **the arms used different gates, worth up to 126 bp** (§3).
- Anything about the **path-variant book lens**, intraday frequency, or the other cousins.

**Nothing admitted to either book. No hurdle cleared. No holdout read.** R13 ledger: 18 primary cells
plus one vacuous secondary, on the hypothesis *"price reverts at levels where its own rare events
cluster."*

---

*Result committed 2026-09-08, separately from the pre-registration, per R8. §10's close condition is
met; under R15 the decision is the principal's.*
