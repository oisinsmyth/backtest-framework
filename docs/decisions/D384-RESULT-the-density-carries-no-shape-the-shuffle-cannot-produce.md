# D384 RESULT — the EMA-centred density carries no shape a volatility-matched shuffle cannot produce

**The family is CLOSED, at §9's own instruction, before a single feature was built.**

Pre-registration `0b492cd`, amendments `af4a7ad` / `61e8c0f`, runner `0c4189c` (fix `bf17839`) — all
committed before this file (R8). Stage 0: no cell scored, no strategy admitted, no holdout read.

Fixture `data/fixtures/etf_wide_daily_raw.csv.gz` (551 names, gated `e22350a`), 60 names × 6
half-lives × 3 bandwidths × 25 null draws, mining window to 2019-12-31, reserved window untouched.

---

## 1. The verdict

**P1 fails at every half-life and every bandwidth. Not one of the 1,080 name-cells clears the
pre-registered bar.**

| criterion | bar | cells clearing |
|---|---|---|
| **P1 as pre-registered** | observed TV > N2 p95 **by more than 2 SE** | **0 / 1,080** |
| P1 with the 2 SE margin dropped | observed TV > N2 p95 | 46 / 1,080 = **4.3%** (chance = 5.0%) |
| the same against the loose null N1 | observed TV > N1 p95 | 30 / 1,080 = **2.8%** |

The margin is not narrow. Per cell the median observed density sits **1.3 to 2.0 SE below** the
null's p95, and the single best name anywhere in the study reaches **+1.27 SE** against a bar of
+3.65. Against the loose null the clearing rate is *lower* than against the strict one.

§9: *"P1 fails at every half-life → the density carries no shape a volatility-matched shuffle cannot
produce. Close the family here, before any feature is built, and write it as the close."* That is
this record.

---

## 2. The full grid

`obs TV` is the total-variation distance from the N2 null's mean density; `null p95` is the
leave-one-out distance a null draw itself achieves.

```
    half-life    bw    n   obs TV  null p95   CLEARS    TV N1  modes    AC1
            5   0.5   60   0.4035    0.5776    8/60    0.4347   1.28  0.852
            5   1.0   60   0.2874    0.4727    2/60    0.3365   1.00  0.852
            5   2.0   60   0.1727    0.3254    3/60    0.1965   1.00  0.852
           10   0.5   60   0.4224    0.6022    4/60    0.4664   1.58  0.917
           10   1.0   60   0.3527    0.5317    4/60    0.3849   1.03  0.917
           10   2.0   60   0.2379    0.4151    4/60    0.2710   1.00  0.917
           20   0.5   60   0.4323    0.6097    2/60    0.4732   2.05  0.954
           20   1.0   60   0.3647    0.5801    4/60    0.4155   1.20  0.954
           20   2.0   60   0.2615    0.4752    1/60    0.3163   1.00  0.954
           40   0.5   60   0.3967    0.6242    1/60    0.4505   2.40  0.974
           40   1.0   60   0.3633    0.5963    0/60    0.4042   1.22  0.974
           40   2.0   60   0.2886    0.5131    1/60    0.3209   0.98  0.974
           80   0.5   60   0.4149    0.6182    3/60    0.4528   2.72  0.984
           80   1.0   60   0.3761    0.5881    3/60    0.4013   1.35  0.984
           80   2.0   60   0.3153    0.5445    3/60    0.3458   1.02  0.984
          160   0.5   60   0.3733    0.5938    2/60    0.4121   3.03  0.990
          160   1.0   60   0.3441    0.5767    1/60    0.3918   1.45  0.990
          160   2.0   60   0.2926    0.5175    0/60    0.3220   0.98  0.990
```

**P2 — is it a scale or an artefact?** Neither. There is no clearing anywhere, so there is no shape in
the clearing to read. Per §5 this is not a knife-edge and not a hump; it is a flat floor. The `CLEARS`
column is chance noise, and reading a trend in it would be reading noise.

---

## 3. Where the small difference sits, and why it is not the difference we wanted

The excess-mass profile (§4.2) exists to make the difference *visible* rather than inferred, and it
earns its place here — it shows the difference is real but is not structure.

```
  hl   5: peak excess +0.0193  at u = +0.88%   frac of names peaking at |u|<1%: 0.47
  hl  10: peak excess +0.0208  at u = +1.69%                                    0.27
  hl  20: peak excess +0.0181  at u = +2.44%                                    0.22
  hl  40: peak excess +0.0135  at u = +2.44%                                    0.23
  hl  80: peak excess +0.0091  at u = +2.00%                                    0.08
  hl 160: peak excess +0.0071  at u = +1.38%                                    0.20
```

**The excess sits on the positive side at every half-life — above the EMA, never below.** A
one-sided excess above a moving average is drift, which is what D382 already found on daily ETFs and
already retired as an edge. It is not the bimodality-with-price-in-a-valley that §4.1 was written to
detect.

**And the mode count runs the wrong way.** Observed against the N2 null, at bandwidth 1.0:

```
  hl   5: observed 1.00   null 1.00   diff +0.00
  hl  20: observed 1.20   null 1.17   diff +0.03
  hl  80: observed 1.35   null 1.57   diff -0.22
  hl 160: observed 1.45   null 1.73   diff -0.28
```

**At the long half-lives the volatility-matched shuffle is *more* multimodal than the market is.**
The hypothesis was that real price structure would show modes a shuffle could not; the observed
density is the *smoother* of the two. Whatever the second mode in the null is, clustering alone
produces it, and the market produces less of it.

---

## 4. P3 — the coordinate half-works, and the half that fails names its own fix

**P3 PASSES on the claim as written.** The spread of `x` across names is materially tighter than the
spread of price across names:

| | coefficient of variation across names |
|---|---|
| absolute price (median close per name) | **1.082** |
| `x` spread, half-life 5 | 0.567 |
| `x` spread, half-life 20 | 0.606 |
| `x` spread, half-life 160 | 0.733 |

The coordinate does what §4.5 proposed: it removes the level. **But it does not remove the scale, and
the residual is large.** At half-life 20 the widest name's `x` spread is **357× the tightest** —
SHV at 0.03% against ELON at 11.57%. Ex-tails (5th to 95th percentile) it is still 8.2×.

**So `x` is price-invariant and volatility-variant.** Pooling or ranking densities across names in
this coordinate would still be dominated by which names are volatile, which is the objection the
coordinate was built to answer, displaced one level down rather than removed. The obvious repair —
divide `x` by its own EW standard deviation — is a *successor's* declared choice under R14, not
something to adopt here: it would be a function chosen after seeing this result, which is the
definition of fitted.

---

## 5. P4 — monotone, and it falsifies my own §2

```
    half-life    5: x AC1 +0.8519   x sd 0.0197
    half-life   10: x AC1 +0.9172   x sd 0.0282
    half-life   20: x AC1 +0.9537   x sd 0.0395
    half-life   40: x AC1 +0.9735   x sd 0.0545
    half-life   80: x AC1 +0.9842   x sd 0.0735
    half-life  160: x AC1 +0.9897   x sd 0.0990
```

**Strictly monotone in both columns. There is no interior optimum.** §2 of the pre-registration
claimed: *"There is a genuine optimum rather than a monotone, because a fast EMA makes x stationary
and trivial while a slow one makes it informative and non-stationary."* **That claim is wrong.**
Persistence rises smoothly and spread rises smoothly; nothing trades off against anything, so the
return-blind criterion cannot select a half-life at all. It was offered as the way to pick `λ`
without touching returns, and it does not pick one.

This matters beyond D384: any successor proposing to select a memory parameter on return-blind
stationarity should be told that on this data the criterion is monotone and therefore vacuous.

---

## 6. Assertions

All held on the final run.

| tag | value |
|---|---|
| `[REC]` recursive EW density vs direct EW sum | **3.44e-16** (tol 1e-9) |
| `[FRAME]` scalar-offset form vs from-scratch re-accumulation | **0.00e+00**, exact |
| — the naive per-bar `np.interp` form, for contrast | 7.36e-03 |
| — ignoring the frame entirely | 2.72e-01 |
| `[NULL]` \|r\| autocorrelation: observed 0.1426, **N2 keeps 0.0943**, N1 destroys 0.0294 | as specified |
| `[CAUSAL]`, `[SPLIT]`, `[GATE]`, `[X]` | held; `[X]` raises on every deliberate break |

`[NULL]` is the load-bearing one and it does what §3 required: N2 preserves the volatility clustering,
so the failure of P1 is not the failure of a null that quietly destroyed the thing it claimed to keep.
That was the outcome that would have made this whole result uninterpretable.

---

## 7. The implementation fix that inverted the reading — recorded because it nearly was not caught

The first completed run implemented P1 as *observed TV against the null's mean* with **no null
reference distribution**, comparing a single number to a single number. It would have been reported as
roughly **27 SE of structure at every half-life** — a spectacular and entirely artefactual result,
because the observed density is one draw and the null mean is an average of 25, so the observed is
*guaranteed* to sit further from the mean than the mean sits from itself.

**The tell was in the diagnostics, not the headline: the null mean had more modes (4.47) than the
observed density (3.03).** A null more structured than the market is not a null that is losing.
Chasing that inconsistency found the missing leave-one-out reference. Fixed in `bf17839`; the reading
inverted from decisive pass to decisive fail.

The general lesson, and it is the same one as `[X]`'s three dud breaks this session: **a distance
needs a reference distribution of the same distance, computed the same way.** Comparing an observed
statistic to a null *point estimate* rather than to the null's *own spread* is a fixed, silent,
one-directional bias in favour of the hypothesis.

---

## 8. Disclosed post-hoc observation — and it does not reopen anything

Reading the grid raised a question P1 does not answer: the observed density is inside the null's
spread, but is it centred on the null?

**It is not.** Against the null's *centre* rather than its p95:

```
  hl   5: 42/60 names above the null centre   sign-test p = 1.3e-03   median z +0.30
  hl  10: 43/60 names above the null centre   sign-test p = 5.3e-04   median z +0.43
  hl  20: 38/60 names above the null centre   sign-test p = 2.6e-02   median z +0.37
  hl  40: 34/60 names above the null centre   sign-test p = 1.8e-01   median z +0.12
  hl  80: 32/60 names above the null centre   sign-test p = 3.5e-01   median z +0.09
  hl 160: 28/60 names above the null centre   sign-test p = 7.4e-01   median z -0.08
```

A small displacement, monotonically decaying in half-life, surviving Bonferroni over the 18 cells at
half-life 10. **It is a real difference and it is roughly 0.4 SE per name** — against a P1 bar of 3.65
SE.

**This is post hoc and it does not change the close.** The sign test was not pre-registered; running a
weaker second test after the declared one fails, and reading it as a rescue, is exactly the failure
mode a pre-registration exists to prevent. Under R15 only the principal reopens an avenue, and
anything built on this displacement needs its own record with the sign test declared **in advance**.

**And the obvious mechanism for it does not survive contact with the data.** Short-horizon serial
dependence would predict the displacement to order across names by their own return autocorrelation.
It does not: at half-life 10, where the displacement is *strongest*, `corr(return AC1, displacement)`
is **−0.024**. At half-life 5 it is +0.270 (n=60, ~2 SE) and in the *momentum* direction, not the
mean-reversion one the story requires. **The displacement is recorded as unexplained.** It is not
filed as a mechanism in `FINDINGS.md`, because the statistic does not order the outcome.

---

## 9. Predictions scored

| | prediction | outcome |
|---|---|---|
| **Q1** | the observed beats N1 at every half-life, and that proves nothing | **FALSIFIED.** It does not beat N1 distributionally at all — 2.8% of cells clear, *below* the 5% chance rate. The direction held (TV to N1 exceeds TV to N2 in every one of the 18 cells) but as a clearing claim it is wrong |
| **Q2** | against N2 the margin is smaller and clears at the **long** half-lives, not the short | **FALSIFIED, and backwards.** Nothing clears; and what displacement exists is concentrated at the **short** half-lives and gone by 160 |
| **Q3** | P2 shows a monotone trend, not a hump | **HELD, but vacuously on the pre-registered statistic** — the clearing rate is flat noise. It holds cleanly on the post-hoc displacement of §8, which is monotone and not a hump |
| **Q4** | P3 passes comfortably | **HELD as written** (CV 0.61 vs 1.08) **with a material caveat §4 did not anticipate**: the coordinate removes the level and leaves a 357× volatility spread |
| **Q5** | the kernel form cuts the single-bucket share below 3.3%, span analogue exceeds 3 | **NOT RUN.** The span-census analogue of §4.4 was not implemented. Recorded as an omission, not as a pass |
| **Q6** | AGAINST myself: P4's return-blind optimum disagrees with P1's best half-life | **UNRESOLVABLE, and its premise falsified.** Neither criterion selects anything — P4 is monotone (§5) and P1 has no best. The prediction assumed both would produce an optimum; §2's claim that P4 would is simply wrong |
| **Q7** | `[FRAME]` and `[REC]` both hold on the first run | **FALSIFIED.** `[FRAME]` fired twice — first at 2.1e-01 on a real specification error in §1 (two constructions conflated), then at 8.09e-03 on a diffusive implementation. §9 said stop-and-fix, and that is what happened. Both now hold exactly |

**Five of seven falsified.** The two that held, held with caveats.

---

## 10. The close

**The EMA-centred log-space structure density is closed as a signal family.** The coordinate is
sound, cheap, and does remove price level. It does not carry shape a volatility-matched shuffle
cannot produce, on 60 ETFs over 2,516 daily bars, at any of six half-lives or three bandwidths.

What survives and is worth keeping:

- **The construction is proved.** `[REC]` at 3.4e-16 and `[FRAME]` exact. A successor wanting the
  current-frame form (construction B) inherits a proved component. `scripts/run_d384_ema_density.py`
  stays in `scripts/`.
- **The naive per-bar `np.interp` translation is diffusive** (7.4e-03 over 900 bars) and the
  scalar-offset form is exact. Anyone building a moving-frame density needs this.
- **Return-blind stationarity is a vacuous selector for a memory parameter on this data** (§5).
- **A distance needs a reference distribution of the same distance** (§7).
- **`x` is price-invariant and volatility-variant** (§4) — the coordinate's residual is scale, and
  that is a real, measured constraint on any successor.

**Nothing is admitted to either book. No hurdle is cleared. No holdout was read.** The multiplicity
ledger is untouched under R13: this study scored no strategy cell.

---

*Result committed 2026-09-08, separately from the pre-registration, per R8. The reserved window
(2020-01-01 onward, 1,671 bars) remains unread.*
