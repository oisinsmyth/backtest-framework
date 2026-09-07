# NOTE — one clause in `docs/FINDINGS.md` §52's corollary overreaches

**STATUS: NOT APPLIED. `docs/FINDINGS.md` is untouched by the session that wrote this.**
Raised by the principal, 2026-09-08. §52's *substance* is unaffected; one sentence is loose.

## The clause

§52's corollary currently reads:

> *"Variations on winner-selection cannot diversify each other: **at ρ ≈ 0.92 two such
> constructions are the same strategy for portfolio purposes**, and gate 1d′ is blind in that
> region — it rejects every pair on structure alone (D376 L2). Independence inside a cohort must
> be established some other way, or not claimed."*

## Why the bolded clause does not follow

**ρ is computed on mean-removed, volatility-normalised series.** It constrains the co-movement of
*deviations*; it is silent on *levels*. Two books can correlate at **0.92 and earn very
differently** — say +12 bp a bar against +1 — and ρ registers none of that gap. Where it happens
the correct action is to hold the better one, which is the opposite of treating the two as
interchangeable. **"The same strategy" is a statement about level and shape together; ρ supplies
only shape.**

## What §52 should say instead

The section already contains the statistics that carry the claim, so the fix is to attribute each
consequence to the measurement that supports it:

| claim | statistic | in §52 |
|---|---|---|
| ~80% of the winners'-dip edge is cohort exposure | **difference in means** — `B_c` at +126.54 of +160.55; the cohort hedge taking the mean to +34.08 and the median to **−30.74** | D373, D377 — **load-bearing, unaffected** |
| two winner-selection variants **cannot diversify each other** | **ρ = +0.923** | D376 — **correct, and ρ is the right instrument for exactly this** |
| ~~two such constructions are **the same strategy**~~ | — | **not supported by ρ; withdraw or re-derive from means** |

### Proposed replacement sentence

> *Variations on winner-selection cannot diversify each other: at ρ ≈ 0.92 holding both buys
> almost no variance reduction, so they compete for the same slot rather than sharing it — and
> which one to hold is a question about their MEANS that ρ cannot answer. Gate 1d′ is blind in
> that region: it rejects every pair on structure alone (D376 L2). Independence inside a cohort
> must be established some other way, or not claimed.*

## The constructive half, worth adding

A high ρ makes a level comparison **easier**, not harder:

```
Var(A − B) = σ²_A + σ²_B − 2ρ σ_A σ_B
```

At ρ ≈ 0.92 with comparable volatilities that difference series is small, so a **paired**
comparison of two books' means on matched bars carries a tight standard error. **The right test
for "does this selector add anything over its pool" is a paired difference of means, and it should
be run BECAUSE the correlation is high.** That is a stronger form of what `B_c` already does per
trade, available per bar.

## Where this bites next

`docs/research/the-signal-hunt-part2.md` §4.1a made the identical error and has been corrected in
place (commit on `worktree-signal-hunt-part2`): it used ρ ≈ 0.92 to argue an ER-refined winner
book "could not have added anything", when ρ only establishes it could not have *diversified*. The
retirement of that use stands on `B_c` and the hedge, which are level measurements.

**Anything downstream that cites §52's corollary to dismiss a construction on correlation alone
should be re-read against this note.**

## What the principal is asked to decide

1. Replace the clause, or leave it and let this note stand as the qualification?
2. If replaced — amendment in place with a date, per the append-only convention, rather than a
   quiet edit?
3. Is the paired-difference test worth adding to the stage-1 gates as the standard way to ask
   "does this selector beat its own pool"? It is cheaper and more powerful than the per-trade
   `B_c` where both books exist as bar series.
