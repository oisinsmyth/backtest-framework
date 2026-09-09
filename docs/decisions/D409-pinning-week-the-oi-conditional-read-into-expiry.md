# D409 PRE-REGISTRATION — expiry week: the OI conditional read into the expiry itself

**R8: committed before the runner exists. Result separately.**

**Number.** `D409`, from the block `D407–D410` reserved on master in `044f839`.

---

## 1. Why this exists

[D408](D408-RESULT-the-magnitude-replicates-the-shape-does-not.md) left the line in an
uncomfortable place and named this study as the other half of it:

> The effect's **size replicates out of sample** at 1.07×, which kills the selection explanation.
> Its **shape fails** in the same way twice. Its **sign is not stable within volatility strata**.
> The `expiry` set (D409) is untouched and is the other half of this question — **pinning is
> classically claimed at expiry, which is exactly where neither `d406` nor `oos` sampled.**

Both spent slices sampled **mid-quarter, deliberately away from expiry** (D406 §3), because OI
mechanically collapses at the roll and that would have confounded the density measurement. That
choice was right for the general conditional and it means **the one date where the mechanism is
classically claimed has never been looked at.**

The claim being tested is the ordinary one: **open interest concentrated at spot pins price into
the expiry.** If it is real anywhere, it is real over the four sessions from the Monday of expiry
week to the third Friday, on the chain that is about to expire.

**This is a PRE-SCREEN, not a pre-registration of a strategy.** D263's inversion — measure the
conditional against a bar stated before looking, and only pay for a full pre-registration if it
clears. **The ledger does not move. Nothing is admitted to any book.**

---

## 2. The slice — the third disjoint set

| set | dates | status |
|---|---|---|
| `d406` | 15 Feb / May / Aug / Nov, 2015–2023 | **SPENT** |
| `oos` | 15 Jan / Apr / Jul / Oct, 2015–2023 | **SPENT** (D408) |
| **`expiry`** | **Monday of quarterly expiry week, Mar / Jun / Sep / Dec, 2015–2023** | **36 snapshots, 7,555 chains. This study.** |

Same 210 names, same years, **disjoint dates from both spent sets** — asserted at runtime by
`[DISJOINT]` against both manifests, not assumed. Pulled by
`scripts/pull_av_options_snapshots.py --set expiry` (`044f839` / `37ba4fe`), which computes no
statistic and states no bar.

**No pooling with `d406` or `oos` for anything that can clear.** A pooled table may be reported
descriptively.

---

## 3. WHAT IS DECLARED PRIMARY, IN ADVANCE

**`w = 2.0`, horizon `h = 4`, outcome `|forward move| / (σ√h)`.**

- **`w = 2.0` is carried forward, not re-chosen.** It was declared primary in D408 §3 *before*
  that run, and it is the only cell with any out-of-sample support. Re-opening the window choice
  here would be the D197–D203 refinement ladder.
- **`h = 4` is the expiry itself.** Monday's close to the third Friday's close. It is not a free
  parameter: it is the horizon the mechanism names.

Everything else is D406's construction unchanged, imported rather than restated so the studies are
provably the same object: density is the share of a name's total open interest within `w` daily
sigmas of spot, **calls and puts summed and never netted**, names below 10 strikes at OI ≥ 100
excluded per snapshot, snapshots below 50 names dropped, levels on `RAW_CLOSE` with `[ALIGN]`
against the delta-0.5 strike.

`w = 1.0`, `w = 0.5`, `h = 21`, `h = 63` and the signed return are **shape and cannot clear.**

### 3a. `[EXPIRY]` — an assertion, because the horizon is the whole claim

`h = 4` is four *panel positions*, not four calendar days. A holiday inside expiry week would
silently push `t + 4` past the expiry into the following Monday and the study would measure the
wrong window while reporting the right name. **The runner asserts that `dates[t + 4]` is the third
Friday of that month for every snapshot used, and aborts otherwise.** If some snapshots fail, they
are dropped and the count is reported; the study does not quietly re-anchor.

---

## 4. THE BAR — D406's, unchanged

| | condition |
|---|---|
| **T1** | mean \|forward move\| / σ√h **monotone DECREASING** across Q1→Q5 of density |
| **T2** | Q1 − Q5 ≥ **10% of the pooled mean** |
| **T3** | T1 **survives within volatility terciles** |

**The bar is not relaxed because the horizon is short.** T3 remains the most likely killer and the
reason is unchanged: density is mechanically higher for low-volatility names, and low-volatility
names move less.

### 4a. R2 — a second replication of the magnitude, declared now

D408's R1 was met at 1.07× on one disjoint set. One replication is a fact; two is a property.

> **R2 — the `w = 2.0`, `h = 63` spread on `expiry` is negative and ≤ −0.0569**, the same
> `0.75 ×` `d406`'s `−0.0759` that D408 used, unchanged.

**R2 clearing does not clear D409 and admits nothing.** It is the same ladder rung: a cheap test
earns the right to pay for an expensive one and never substitutes for it. It is stated separately
because the primary here is the `h = 4` pinning arm, and R2 is about the *general* conditional
measured on a third slice.

### 4b. Dg1 — the contamination diagnostic, with its reading declared

D406 §1 argued that open interest is worth a look precisely because **it is not a function of the
price path**, which is what killed all seven price-level programmes. That argument has never been
checked on this object.

> **Dg1 — `corr(dens, trailing |21-day move| / σ)` over pooled rows**, reported for the primary
> cell.

**Declared reading, so it cannot be re-read afterwards:** open interest accumulates at strikes
where price has been trading, so a strongly negative correlation would mean `dens` is substantially
a restatement of *"this name has been quiet"* — D403's TERRAIN check, applied to OI. **A
correlation more negative than −0.40 means any T1 pass is reported as a restatement of trailing
quiet rather than as evidence about open interest**, regardless of the bar. D403 measured −0.009 to
−0.109 for its map and that was the one durable positive it produced; this is the same test.

---

## 5. Explicitly out of scope, and why — stated now so it is not reached for after a fail

- **Distance to the max-OI strike.** This is the *literal* pinning statistic and it is not run.
  It is [D273's trap](D273-the-profile-as-a-travel-estimator.md): reachability is arithmetic, and any
  random line reproduces a monotone distance ordering. It would need a distance-matched random
  level (`LVL`) — the control D403 pre-registered and failed to build, which is why three of its
  arms were unreportable. **If it is worth running it is worth running with its control, in a
  design of its own.**
- **Front-expiry-only OI.** The pinning mechanism is about contracts expiring *this* Friday, and
  the derived chain summary aggregates OI across all expiries. This is the sharpest available
  refinement and it is deliberately **not** taken, because taking it after seeing a pooled failure
  is exactly the D197–D203 ladder. Recorded here as the first thing a full pre-registration would
  do if one is warranted.
- **Signed or gamma-weighted aggregation**, excluded by D406 §4 as inference.
- **No holdout read.** Nothing here touches a holdout fixture.

---

## 6. Predictions, so they cannot be re-read afterwards

| | prediction | confidence |
|---|---|---|
| **X-a** | **T1 fails** — full monotonicity across five quintiles has now failed twice, on a different step each time | **high** |
| **X-b** | The `h = 4` spread is **negative** — the direction has been negative in six of six cells on `d406` and in the pooled and two of three terciles on `oos` | **moderate** |
| **X-c** | **The `h = 4` spread is SMALLER in σ-units than the `h = 63` spread.** If pinning were the mechanism it would be *larger* at expiry, where the mechanism is claimed and where the spent slices could not see it | **moderate** |
| **X-d** | **R2 is met** — the magnitude has replicated once at 1.07× and I now expect it to replicate again | **moderate** |
| **X-e** | **Dg1 is between −0.15 and −0.40** — some contamination, not enough to explain the conditional | **low** |

**X-c is the one that matters.** It is the only prediction that separates *pinning* from *the
general conditional D406 found*. If the effect is no stronger into the expiry than it is over a
random quarter, then whatever `dens` measures, it is **not** the pinning mechanism — and the line's
open question becomes what else it could be. If the effect is materially **stronger** at `h = 4`,
that is the first mechanistic evidence this programme has produced in nine looks.

---

## 7. What this does not do

- No position, no book consequence, no admission. **The ledger does not move.**
- Does not reuse `d406`'s or `oos`'s dates for anything that can clear.
- **Does not recommend a disposition for the line.** The outcome is reported against the bar
  stated above and what follows from it is the principal's call, not the runner's.

---

## 8. R13

Tenth look by object on price levels; third on this one. Marginal cost is **one screen on data
already pulled** — 7,555 chains fetched in `37ba4fe`, ~25 seconds of compute — which is why it is
worth running rather than assuming the answer.
