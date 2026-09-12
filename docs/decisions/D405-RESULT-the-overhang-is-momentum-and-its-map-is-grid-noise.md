# D405 RESULT — the overhang is momentum, and the one quantity that looked independent is grid noise

**STAGE 0 ABANDONS. STAGE 1 DOES NOT OPEN.** Pre-registration `fdcaf30` predates the runner
`8b20c43`, which predates this file (R8). No forward return was computed. Nothing is scored,
nothing is admitted to either book, no holdout was read.

Total cost: about forty minutes of compute and one afternoon.

---

## 1. The verdict

| gate | quantity | statistic | abandon at | outcome |
|---|---|---|---|---|
| **6.1 VOL-SHUF** | `g` | corr with volume-shuffled twin **+0.9717** | > 0.90 | **ABANDON** |
| | `OS` | **+0.9768** | > 0.90 | **ABANDON** |
| | `FP` | +0.7951 | > 0.90 | pass — but see §4 |
| **6.2 A1** | `g` | worst \|rho\| **+0.7939** vs `trailing_return` | > 0.50 | **ABANDON** |
| | `OS` | **−0.8527** vs `rsi` | > 0.50 | **ABANDON** |
| | `FP` | −0.1457 vs `rsi` | > 0.50 | pass — but see §4 |
| **6.3 PERSIST** | `g` | half-life 26.0 bars, `ac1` +0.9688 | < 1 bar | pass |
| | `OS` | 17.0 bars, `ac1` +0.9486 | < 1 bar | pass |
| | `FP` | **1.00 bars**, `ac1` +0.5407, 14.5% of names under a bar | < 1 bar | pass, at the boundary |

1,449 names built; 1,198 carried enough eligible overlap for 6.1; 1,104 for 6.3. Gate 6.2 ran
over 3,935 within-bar cross-sections (D268's lens 1).

**Both pre-registered failure modes fired at once** — §7's outcome 2 (*momentum renamed*) and
outcome 3 (*the volume is decorative*) — on the same two quantities.

---

## 2. The scalars are momentum, and the volume does nothing

`g` (capital-gains overhang) and `OS` (share of held stock underwater) correlate **0.97 and 0.98
with their own volume-shuffled twins.** Permuting every volume in a name's history, leaving the
price path untouched, barely moves them. Whatever they measure, they measure it from prices.

And they are not new: `g` sits at **+0.79 against `trailing_return`**, `OS` at **−0.85 against
`rsi`**. **D272's `dist_hvn` was killed at 0.555 after a full study had been built on it. These are
worse.** `g`'s correlation with explicit 12-month momentum is +0.5941 — over the gate on its own.

D272's second standard fails too. **Effective inputs go 6.52 of 13 → 6.12 of 16** when the overhang
family is added: adding three scores *reduced* the effective count, which is what redundancy looks
like. A2 required a rise of at least 0.5.

The controls behaved, so the instrument is sound: `ctrl_noise` +0.0009 (passes, as it must),
`ctrl_blend` +1.0000 (fails, as it must). Either misbehaving would have voided the run.

---

## 3. The construction was sound. That is what makes the result clean.

Nothing here failed for want of care, which is why the answer can be believed:

- **The bar shape was measured, not chosen.** 122,892 ETF sessions gave
  `low 0.2482 / body 0.5215 / high 0.2303` against a uniform null of `0.2800 / 0.4713 / 0.2487` —
  the body carries **1.11×** its width share. The principal proposed 25/50/25 from first principles
  and the data agreed to within two points. Committed before the run (`8b20c43`) so it could not
  be retuned after.
- **No bandwidth anywhere.** The intra-bar shape is exact and piecewise-constant.
- **`[MASS]`** places exactly `V` shares in all five cases — normal, no upper wick, no lower wick,
  doji, and a bar narrower than one grid cell.
- **`[DECAY]`** — a bar turning over a full half-life moves the map by 0.805 in `F(P)` afterwards
  and by **exactly 0.0** before, proving causality and non-inertness in one check.
- **`[SPLITVOL]`** — volume is correctly split-adjusted in this fixture: **8.4%** of real splits at
  the mis-adjustment signature against **36.9%** at zero, and \|jump\| at splits is 1.297× the same
  statistic at random dates in the same names. The `[X]` proves the check bites: fed deliberately
  un-adjusted volume it reports **37.8% at the signature against 6.3% at zero** and raises.

---

## 4. `FP` LOOKED LIKE A SURVIVOR AND IS AN ARTEFACT

`FP` — the normalised map height at the current price, and the object the principal actually asked
for — passed 6.1 (0.795) and 6.2 (0.146). It was the only quantity that did.

`FP` is read as `F[j] / max(F)` on a `GRID_N`-cell axis, and price moving one cell changes `j`. So
its de-correlation from the shuffled twin and its weak persistence could equally be **discretisation
noise**. §3.5 of the pre-registration required a `[GRID]` check for exactly this. **The first runner
declared it and did not build it.** Built and run:

```
   grid    FP ac1   FP shuf |    g ac1   g shuf |   OS ac1  OS shuf
    128   +0.6174   +0.8276 |  +0.9699  +0.9731 |  +0.9450  +0.9768
    256   +0.5731   +0.8029 |  +0.9699  +0.9730 |  +0.9489  +0.9769
    512   +0.5398   +0.7939 |  +0.9699  +0.9729 |  +0.9503  +0.9768
   1024   +0.5110   +0.7800 |  +0.9699  +0.9730 |  +0.9508  +0.9766

   drift 128 -> 1024:   FP  ac1 -0.1065   shuf -0.0476
                        g   ac1 +0.0001   shuf -0.0001
                        OS  ac1 +0.0058   shuf -0.0001
```

**`g` is flat to four decimal places across an eight-fold change in resolution. `OS` likewise. `FP`
moves monotonically in both statistics, in the direction predicted for noise** — coarser cells
average it away, so `ac1` and the shuffle correlation both rise as the grid coarsens.

`FP`'s apparent independence and apparent volume-sensitivity are **a measurement of how finely the
axis was chopped.** Evidence: `data/d405_grid_check.json`.

**With `[GRID]` included the abandon is unanimous.** Two quantities are momentum with decorative
volume; the third is noise.

---

## 5. Two assertions were wrong before they were right

Recorded because both were caught by measurement rather than by luck, and both were mine.

**`[SPLITVOL]` first fired on a real event.** Its first form asserted no split date carried a
dollar-volume jump above half the split's log-ratio. It stopped the run on **DRYS 2016-11-01** — a
genuine 400× squeeze that happens to sit on a reverse-split date, where volume moved **+5.471**
against a mis-adjustment signature of **−2.708**: opposite sign, twice the size. **A check that
fires on real market events is a check that cries wolf.** Replaced with the distributional test in
§3, which asks whether jumps *cluster at* the ratio rather than whether they are merely large.

**`[GATE 6.3]` could not fail.** `half_life` floored its answer at 1.0 whenever lag-1
autocorrelation was already below 0.5 — putting the floor exactly on the abandon threshold. `FP`
reported "1.0" at both p10 and p50, which could have meant anything below a bar. Fixed to
interpolate (`ac1^h = 0.5`) and to report `ac1` beside it. **A self-test that cannot fail is worse
than none**, and this one was gating a verdict.

---

## 6. What this settles, and what it does not

**Settles.** The disposition effect, operationalised as a volume-weighted purchase-price
distribution decayed in volume-time, **does not supply an independent conditioner on this data.**
The scalar form is momentum under another name — the specific failure the pre-registration named as
most likely, at §6.2. The map form carries nothing a finer grid does not dissolve.

**Does not settle.** The *thesis* — that supply and demand means **unfilled** interest, and that
every price-history map measures absorbed interest instead — is untouched by this. What failed is
one operationalisation of "holders with a reason", and it failed partly on a known weakness stated
in the pre-registration: **true turnover is volume over shares outstanding, and this repo has no
shares-outstanding series**, so `theta` is a relative-volume proxy. A cleaner turnover measure might
behave differently. That is not a recommendation to try one.

**The pre-registration's own §7 outcome 3 says what should follow**, written before the run:

> The volume is decorative. Then "absorbed vs remaining" is wrong, or not repairable with volume,
> and the whole supply-and-demand line should close rather than produce an eighth look.

Half of that condition fired exactly: the volume is decorative for both scalars. **The
recommendation is therefore to close the supply-and-demand line**, and it is the principal's to
make. What remains parked in PICKUP §0d2 is of a different kind — resting liquidity, options open
interest, execution anchors — objects that observe *obligations* rather than inferring them from
price history. Those are not eighth looks at the same idea.

---

## 7. R13 — THE LEDGER NOW CARRIES SEVEN

| # | programme | disposition |
|---|---|---|
| 1 | TERRAIN, D189–D203 | CLOSED terminal — 259 looks |
| 2 | STRUCTURE, D173, D204–D211 | CLOSED — 86 looks |
| 3 | D272, D273 — the profile as an input | run and CLOSED |
| 4 | BREAKOUT family | off-thesis, dormant; wedge CLOSED |
| 5 | DENSITY line, D384–D388 | RETIRED by the principal |
| 6 | D403 — the wick-stack potential | CLOSED by the principal, 2026-09-09 |
| 7 | **D405 — the capital-gains overhang** | **ABANDONED AT STAGE 0, 2026-09-09** |

Seven programmes, seven closes, none paid.

**Evidence:** `data/d405_overhang_stage0.json`, `data/d405_grid_check.json`,
`data/d405_bar_shape_calibration.json`. Runner `scripts/run_d405_overhang_stage0.py`.
