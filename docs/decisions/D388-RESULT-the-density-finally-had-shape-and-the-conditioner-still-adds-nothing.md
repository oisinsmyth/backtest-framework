# D388 RESULT — the density finally had shape, and the conditioner still adds nothing

**This is the clean test the line has needed since D384.** The density is demonstrably shaped, every
arm uses one gate, the events are genuinely rare, and **the observed still does not beat a rotated
density.** §6's fourth abandon condition is met. **Under R15 the decision to close is the
principal's.**

Pre-registration `1c168f3`, runner `8f1dced` + `85e9171` — all predate this file (R8).
600 names, 17,511 cells in 3,182 s at **5.98× on 6 workers, 100% efficiency**.

---

## 1. P3 — the density HAS shape, and rarity is what produced it

```
      type     k  lam  names  rate/100   TV(f,g)  ratio CV  modes    h/DX
      move   2.0   60    600      5.16    0.2573     0.727    3.0    13.4
      move   2.5   60    571      2.67    0.3615     0.964    3.0    13.0
      move   2.5  250    560      2.67    0.2307     0.659    3.0    16.0
  reversal   1.0   60    582      3.86    0.2720     0.766    2.0    13.3
  reversal   1.5   60    207      1.17    0.5104     1.307    2.0     9.6
  reversal   1.5  250    207      1.17    0.3442     0.968    3.0    12.5
```

**Against D387's worst bucket — TV 0.039, ratio CV 0.096, 0 modes — this is 4.5–13× the structure
and 2–3 modes in every cell.** Q1 predicted TV > 0.12 and CV > 0.35 and it held everywhere.

**And it is monotone in rarity**: `move` k=2.5 beats k=2.0, `reversal` k=1.5 beats k=1.0, at every λ.
**The σ threshold was the right diagnosis** — D387's density was flat because its "rare" events fired
on a median 28.3% of bars, and fixing the threshold fixed the object.

---

## 2. P1 — the observed beats a shuffled PATH, and does not beat a rotated DENSITY

```
      type     k  lam   H    n  GROSS bp   net bp   N2 p50   z N2    sign p    A p50    z A   signA p
      move   2.0  120  20  597       8.7   -120.0    -29.9   0.32   3.9e-11     68.1  -0.19   1.0e+00
      move   2.0  250  20  570      38.2    -91.7    -26.2   0.22   4.4e-07    133.1  -0.19   1.0e+00
  reversal   1.0  120  20  576      13.2   -112.4    -36.4   0.33   7.2e-11     42.0  -0.02   6.8e-01
  reversal   1.0  250  20  545      61.2    -68.4    -36.1   0.29   1.2e-07     48.7  -0.01   5.3e-01
  reversal   1.5  120  10  201      23.5    -73.7    -15.5   0.55   2.2e-09     11.2   0.20   7.9e-02
  reversal   1.5  250  20  201      50.7    -48.9    -40.3   0.50   1.4e-10     37.2   0.01   5.0e-01
```

**Against N2 the displacement is emphatic** — positive in 34 of 36 cells, sign tests to **7.2e-11**.
**Against A′ it is gone:**

- **6 of 36 cells** have a positive A′ margin at all; **best +0.19 SE**, worst −0.48.
- **Not one is significant** — the best sign test is `p = 0.079`.
- **All six sit in the `reversal k=1.5` cell**, which is the thinnest in the study (207 names).

**This is D387's finding, replicated on a density that demonstrably has shape.** N2 destroys the real
price path; A′ destroys only the density's **alignment with the current price**. Beating the first and
not the second means the edge is trading a real path at extreme `x` and betting on reversion —
**a misaligned density does just as well, so the event-density conditioner adds nothing to what `x`
already carries.**

**And the six positive cells are selected, not neutral.** `reversal k=1.5` fires on 1.17% of bars, so
`MIN_EVENTS` drops 375 of 582 names — and the survivors are the **most event-rich**: median 166
`k=1.0` events against 85 for the dropped. The only cells with a positive A′ margin are the ones
where the sample was filtered toward event-dense names.

---

## 3. Cost, unchanged and decisive

**Net is negative in all 36 cells**, −48.6 to −141.2 bp, against gross of −19.4 to +61.2 bp. Best
gross **61.2 bp** against a measured spread of ~110–130 bp on the held names.

**Q3 is falsified in its first half**: the gross did **not** rise relative to D387 (61.2 against
88.1). D387's larger figure came from a flat density on half its universe and was reversion from `x`,
not from the conditioner — so the fall is what a cleaner test should produce, not a regression.

---

## 4. Trade distribution — best A′ cell (`reversal` k=1.5, λ 120, H 10, n=201)

```
    mean 23.5 bp   median 26.8 bp   trimmed 1% both 28.4 bp
    ex-top 1% -4.8 bp     ex-bottom 1% +56.6 bp
    win rate 0.520   skew -0.291   kurtosis 9.673
    13 of 201 names to half the P&L; top-10 41.9%
    by PRICE: cheap +4.1 bp   dear +42.7 bp  (median $42.23)
```

**Removing the top 1% of trades turns the edge negative (−4.8 bp).** Both tails are large — kurtosis
9.673 — and the symmetric trim (28.4) sits *above* the raw mean, so the left tail costs more than the
right earns. Concentration is real here in a way it was not in D387: **13 of 201 names carry half the
P&L**, against 30 of 508 there.

**Reported all three ways per CLAUDE.md**, because the one-sided cut alone always frightens on a
two-tailed fat-tailed book (D307).

---

## 5. Predictions scored

| | prediction | outcome |
|---|---|---|
| **Q1** | the density now has shape: TV > 0.12, ratio CV > 0.35 | **HELD in every one of 12 cells**, 4.5–13× D387's worst, 2–3 modes |
| **Q2** | **P1 still fails against A′** | **HELD.** 6/36 cells positive, best +0.19 SE, none significant, all in the thinnest cell |
| **Q3** | the gross rises relative to D387 but by less than the spread | **HALF FALSIFIED.** It *fell*, 88.1 → 61.2 bp. The second half held: nowhere near the spread |
| **Q4** | `k = 2.5` beats `k = 2.0` — rarer is better, the premise of the fix | **HELD on the A′ margin** (rarer better at every λ and H) and **falsified on gross** (38.2 vs 21.3 at λ 250, H 20). Rarity improved the OBJECT, not the P&L |
| **Q5** | **AGAINST myself: count drift from one gate exceeds 20%** | **HELD.** 0.68–1.03, so up to 32% |
| **Q6** | **AGAINST myself: at least one assertion fires on the first run** | **HELD.** `[LAG]` fired at 5 bars and `[RARE]` was found vacuous. **Four studies running, and the first time this prediction was right — because it predicted failure** |

---

## 6. Assertions

`[RARE]` worst rarity spread **1.89** (bound 2.0), worst single-name rate 8.0% ·
`[SIGMA]` 0.000e+00 · `[FAST]` **3.553e-15** and **6.217e-15** on a tie-heavy path ·
`[GATE1]` one gate, asserted by function identity · `[POOL]` 1.36× · `[MASS]` 4.996e-16 ·
`[LAG]` 0 bars · `[SIGN]` +0.1379 · `[REC]` 0.000e+00 · `[SPLIT]` holdout refused ·
`[X]` all five raise, including the new thin-data break.

**Two self-tests were found broken before the run, both passing when they should have failed:**
`[RARE]` returned zeros on thin data, and D387's `[LAG]` audited a different gate-opening rule than
the runner used and passed by luck (fixed `36bab8c`; D387's decisions were causal either way, so its
result stands).

---

## 7. Speed

**3,182 s at 5.98× on 6 workers — 100% efficiency**, after the run was killed at 64/600 and
re-optimised on the principal's budget. The fix was an identity: under plain decay `f` is scaled by
`λ^gap` between events, so the **normalised** shape is constant between events and the dense
(T, GRID_N) accumulation was never needed — 39.0 ms → 1.6 ms, **24×**. My first version of that
identity decayed λ per *event* instead of per *bar* and was wrong by 3.87; `[FAST]` catches it.

**I mis-projected the runtime twice before this** (60 min against 3.1 hours; 41 min against 53 min),
both times by costing the parts I had thought about instead of timing the assembled loop.

---

## 8. What this establishes

**Establishes, on a clean test for the first time in this line:**
- **The construction works.** Given a genuinely rare event, it produces a shaped, multi-modal,
  price-invariant density — TV 0.18–0.51, ratio CV 0.51–1.31, 2–3 modes.
- **Rarity is the mechanism for SHAPE**, monotonically, and the σ threshold delivers it (rarity spread
  across names 4.37× → 1.37×).
- **The conditioner still adds nothing to `x`.** A rotated density does as well, with the density
  shaped, one gate, rare events and 600 names. **Cost is negative in every cell besides.**

**Does NOT establish:** anything about the path-variant book lens, intraday frequency, the remaining
cousins, or volatility conditioning (`|return|`, still not run).

**Nothing admitted to either book. No hurdle cleared. No holdout read.** R13: 36 cells, and this is
the **second look** at this hypothesis; the ledger carries both.

---

*Result committed 2026-09-09, separately from the pre-registration, per R8. §6's fourth abandon
condition is met — the close is available and, under R15, it is the principal's to take.*

---

## ADDENDUM, 2026-09-09 — the conditioner is INERT, not weak: density shape does not predict edge at all

**The principal asked whether these pass their nulls and whether they have been traded. Both answers
are in §2 and §3, but they invite a sharper test than either: if the conditioner carries information,
names whose density is MORE structured should show MORE edge over A′.**

Measured on the committed rows, per name, within each cell:

```
      type     k  lam   H    n  corr(TV, edge)  corr(CV, edge)  top-tercile TV edge   bottom
      move   2.0  120  20  597           0.017           0.041               -0.190   -0.294
      move   2.5  120  20  570          -0.060          -0.036               -0.206   -0.034
  reversal   1.0  120  20  577           0.109           0.092                0.128   -0.087
  reversal   1.5  120  20  207           0.029           0.030                0.315    0.189

  ACROSS ALL 36 CELLS
    mean -0.027   median -0.022   range -0.122 to +0.109
    cells with a positive correlation: 10/36  -- BELOW chance
```

**How much shape a name's density has is unrelated to whether its trades work.**

**This is a mechanism test, and it is stronger than §2's outcome test.** A weak-but-real conditioner
would still produce a gradient: the names where the density resolves structure best would earn most.
There is no gradient. **The conditioner is INERT, not merely small** — and that holds across the
whole cross-section of density quality, not only at the top decile of `R` that §2 traded.

### What has and has not been traded

**Traded:** top-decile `R`, reversion direction, three holds, path-invariant lens, scored per trade,
gross and net against a Corwin–Schultz spread measured on the held names. **Net negative in all 36
cells.**

**Not traded, and now ranked by whether it could change anything:**

- **A slot-limited book (path-variant lens) — NOT worth running.** It changes opportunity cost and
  slot mechanics; it cannot create information a per-trade mean does not have. FINDINGS §10 keeps the
  lenses separate precisely so a book is not mistaken for evidence about a signal.
- **Cross-sectional ranking — NOT worth running.** Same reason, and it additionally requires `R` to be
  comparable across names, which this programme has not established.
- **The `R` RESPONSE CURVE — the only remaining live test.** Only the top decile was ever traded, and
  only in one direction. The low end of `R` (levels carrying FEWER past events than their time-share
  predicts — "air pockets") is untouched, as is whether returns vary monotonically across `R`
  quintiles. **The correlation above weakens this but does not close it**: "how structured a density
  is" does not predict edge, which is not the same claim as "where in `R` price stands" not
  predicting returns.

**Any such test is a THIRD look at this hypothesis and the R13 ledger must carry all three.** My
expectation is that it is null; it is recorded as available, not recommended.
