# D409 RESULT — the effect is real at the expiry, absent over the quarter, and both my predictions that mattered were wrong

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D409-RESULT-the-effect-is-real-at-the-expiry-and-absent-over-the-quarter.md`. The H1 above is the full title.*

**FAILS THE BAR. R2 NOT MET.** Pre-registration `db8de4e` predates the runner and this file (R8).
**The ledger does not move. Nothing was admitted. No holdout was read.** 26 seconds on data pulled
in `37ba4fe`.

---

## 1. The primary cell

`w = 2.0`, `h = 4` (Monday's close → the third Friday's close), `|move| / σ√h`, on the `expiry`
set: **36 snapshots, 5,991 rows, 204 names, 0 dates shared with either spent set** (`[DISJOINT]`
asserted against `d406` **and** `oos`).

```
                Q1      Q2      Q3      Q4      Q5     spread
w=2.0  h=4   0.7536  0.7741  0.7329  0.7342  0.6552   -0.0984   (-13.5% of pooled)
```

| | condition | outcome |
|---|---|---|
| **T1** | monotone DECREASING | **FAIL** — and worse than before: **only 2 of 4 steps hold** (Q1→Q2 and Q3→Q4 both rise) |
| **T2** | Q1 − Q5 ≥ 10% of pooled | **PASS** — +0.0984 against 0.0730 |
| **T3** | survives within vol terciles | **FAIL** — none of the three is monotone |
| **R2** | `h = 63` spread ≤ −0.0569 | **NOT MET** — −0.0286, **0.38×** |

**D409 FAILS.** `[EXPIRY]` held on all 36 snapshots — `t + 4` is that month's third Friday every
time, nothing dropped, nothing re-anchored.

---

## 2. BOTH PREDICTIONS THAT MATTERED WERE WRONG, IN OPPOSITE DIRECTIONS

| | prediction | outcome |
|---|---|---|
| X-a | T1 fails | correct |
| X-b | the `h = 4` spread is negative | correct |
| **X-c** | **the `h = 4` spread is SMALLER than `h = 63`** — *"the only prediction that separates pinning from the general conditional"* | **WRONG.** −13.5% against −3.6%, **3.7× larger at the expiry** |
| **X-d** | **R2 is met** — the magnitude replicates a second time | **WRONG.** 0.38×, not met |
| X-e | Dg1 between −0.15 and −0.40 | correct — **−0.2837** |

Three of five, and the two misses are the two the record singled out. They are wrong in *opposite*
directions, and together they say something neither says alone: **the effect concentrates at the
horizon the mechanism names and disappears at the horizon that had been carrying the line.**

---

## 3. The term structure, across all three slices

`w = 2.0` spread as a percentage of its own pooled mean — the only scale-free way to compare
horizons, since the σ√h normalisation differs:

| set | h = 4 | h = 21 | h = 63 |
|---|---|---|---|
| `d406` (spent) | — | −7.7% | −10.1% |
| `oos` (spent) | — | −12.1% | −10.2% |
| **`expiry`** | **−13.5%** | −9.7% | **−3.6%** |

**`h = 21` is consistent across all three sets** (−7.7 / −12.1 / −9.7). It is `h = 63` alone that
collapses on the expiry dates, and R2 was declared on `h = 63`.

**That observation cannot rescue R2 and is not offered as one.** R2 named its horizon in advance,
it failed, and noticing afterwards that a different horizon behaved would be exactly the
post-hoc horizon selection this ladder exists to prevent. It is recorded because §4 makes it
interpretable, not because it changes the verdict.

---

## 4. THE MATCHED NULL THIS LINE HAS NEVER HAD

D406 and D408 each reported a spread **against no null at all** — three studies quoting −0.0759,
−0.0811, −0.0286 with nothing to say how large a spread the construction produces by construction.
Permuting `dens` **inside each snapshot** holds the cross-section, the calendar, every name's σ and
every forward move fixed, and destroys only the density ordering (200 draws, `scripts/run_d409_extras.py`):

```
   h    observed        p5       p50       p95    beats p5?
   4    -0.0984    -0.0395   -0.0006   +0.0467    YES,  +31.7 SE
  21    -0.0647    -0.0411   -0.0016   +0.0394    YES,  +13.3 SE
  63    -0.0286    -0.0426   -0.0036   +0.0447    NO,   -7.4 SE
```

**This resolves the ambiguity in §3.** The `h = 63` result on the expiry set is not a shrunken
effect, it is a **null result** — inside its own permutation distribution. The `h = 4` result is
**2.5× the null's p5 and 31.7 SE outside it.** The null is decisive in both directions, and the
p5's sampling SE is carried (D373) rather than the percentile quoted bare.

**Retro-fit, and it cuts both ways:** the null's p5 sits near −0.04 at every horizon, so `d406`'s
−0.0759 and `oos`'s −0.0811 were **roughly 2× p5** — real, and by a smaller margin than three
digits of spread made them look.

**The limitation is stated because it is not small.** A within-snapshot permutation is a null for
*"`dens` carries no cross-sectional information."* It breaks the pairing between a name's density
and that name's own forward move, so it does **not** control for `dens` proxying a persistent
name-level characteristic. §5 kills one such characteristic. It does not kill all of them.

---

## 5. The obvious rival explanation, tested, and it does not hold

Dg1 = **−0.2837** (inside the declared −0.40 bar, so the primary is *not* read as a restatement of
trailing quiet). But Dg1 is a correlation, and the correlation is not the rival. **The rival is
that realised-volatility autocorrelation decays**, so *"currently quiet against its own 63-day σ"*
predicts a 4-day move far better than a 63-day one — which would produce §2's entire result with
nothing whatever to do with open interest.

Sorting on trailing quietness **directly**, same rows, same normalisation:

```
quietness  h= 4   0.7098  0.7303  0.7480  0.7303  0.7308   spread +0.0210
quietness  h=21   0.6717  0.6727  0.6510  0.6634  0.6849   spread +0.0133
quietness  h=63   0.7643  0.7939  0.7777  0.7919  0.8058   spread +0.0415
```

**The wrong sign and a fifth of the size.** Quiet names go on to move slightly *less*, which is
ordinary volatility persistence, and it is the **opposite** of what `dens` orders. `dens` is not a
repackaging of trailing quiet.

And `dens` quintiled **within** terciles of trailing quietness, at `h = 4`:

```
quiet lo    0.7005  0.7761  0.6941  0.6982  0.5835   spread -0.1170   n 1690
quiet mid   0.7254  0.6900  0.6675  0.6933  0.7259   spread +0.0005   n 1698
quiet hi    0.8696  0.9535  0.8635  0.8762  0.7120   spread -0.1576   n 1367
```

**It survives conditioning in the outer terciles and vanishes exactly in the middle one.** That is
the third instance of this line's characteristic failure: the magnitude is robust, the shape is
not, and a sub-population goes flat or flips with no story attached. `d406` had six of six
uniform; `oos` flipped the low-vol tercile; here the middle quietness tercile is **+0.0005**.

**Both arms in §4 and §5 were run after the primary and could only hurt it.** That is why running
them after the fact is not a rescue — the direction of a post-hoc test is what makes it one.

---

## 6. Also reported, and cannot clear

**Signed return, `h = 4`:** `−0.0017 −0.0040 −0.0038 −0.0052 −0.0030`, spread **−0.0013** over four
sessions. No direction was declared in advance and it is not monotone, so it cannot clear — the
rule D263 applied to its own −7.32%/yr and D408 to its −5.6%/yr. It is also *small*, which is worth
saying plainly: an undeclared sign that is also economically thin is not a near-miss.

**`w = 1.0`:** −0.0300 at `h = 4` (−4.1%). **`w = 0.5` is degenerate for the third time** — Q1
holds **308 rows against ~1,200** elsewhere, because at half a σ many names carry zero OI in the
window and the tied zeros collapse the bottom quintile. Its `+0.0225` is that artefact, it cannot
clear, and it should not be read at all.

**`[ALIGN]`** held: 5,992 delta-implied spots, median **1.0198**, against `d406`'s 1.0190 and
`oos`'s 1.0180.

---

## 7. `[X]` — the assertions were shown to fail

Per CLAUDE.md, a self-test that cannot fail is worse than none, and the break must move **the
scalar the assertion reads**:

- **`[EXPIRY]`** at `h = 3` and `h = 5`: **0 of 36 snapshots kept**, against 36 of 36 at the
  declared `h = 4`. The check is load-bearing, not decorative — it is the difference between
  measuring the expiry and measuring four arbitrary sessions.
- **`[DISJOINT]`** against the `expiry` set itself: fires, 36 shared.
- **The primary reads `dens`:** permuting it within snapshots moves the spread from **−0.0984** to
  a mean of **+0.0047** — the scalar the verdict is computed from, not the name of the check.

---

## 8. Where this leaves the open-interest line

Three slices, three disjoint date sets, one construction, and the picture is **sharper and less
comfortable than after D408**:

1. **The effect exists at short horizons and is decisively outside a matched null there** — the
   first time this programme has produced a number with a control under it.
2. **It is strongest into the expiry**, which is where the mechanism is classically claimed, and it
   is **3.7× the same construction's quarter-horizon reading on the same dates.** That is the first
   *mechanistic* evidence in ten looks: the effect tracks the mechanism's own calendar.
3. **The quarter horizon is a null result on these dates**, so R2 failed and the general
   conditional does not replicate a second time.
4. **The shape has now failed three times out of three**, on a different step each time, and a
   sub-population has gone flat or flipped in each of the last two. Monotonicity is not a
   technicality here — it is the part that keeps not being there.

**What a full pre-registration would have to do**, if one is written: declare its direction in
advance; use **front-expiry-only open interest**, which §5 of the pre-registration deliberately
withheld and which is the sharpest available refinement; carry the permutation null from §4 as a
standing control rather than an afterthought; and confront the sub-population instability in §5
rather than pool past it.

**Disposition is the principal's.** This record states the result against the bar and nothing more.

---

## 9. R13

Tenth look by object on price levels; third on open interest. Marginal cost **26 seconds plus 28
for the extras**, on chains already pulled. The `expiry` set is now **SPENT** and cannot serve as
confirmation for anything else. **All three snapshot sets are now spent.**

**Evidence:** `data/d409_expiry_pinning.json` (the primary, against the committed bar) and
`data/d409_extras.json` (§4–§5, exploratory). Runners `scripts/run_d409_expiry_pinning.py` and
`scripts/run_d409_extras.py`, both importing D406's construction rather than restating it, so all
three studies are provably the same object measured on different dates.
