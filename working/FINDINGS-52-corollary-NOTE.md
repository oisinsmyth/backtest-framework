# NOTE — one clause in `docs/FINDINGS.md` §52's corollary overreaches

**STATUS: NOT APPLIED. `docs/FINDINGS.md` is untouched by the session that wrote this.**
Raised by the principal, 2026-09-08. §52's *substance* is unaffected; one sentence is loose.

> ### UPDATE, 2026-09-08 — the principal corrected §52 upstream, and **the clause this note is about survived**
>
> Commit **`d9ee2dd`** ("R11: P1 restated as a SIZING RULE, and FINDINGS §52 corrected —
> correlation does not bound a difference in means") reached the same conclusion independently and
> applied it. **What it fixed:** §52's *heading*, which claimed three independent methods measure
> the ~80%, when only two measure a **level** (D373 +126.54/+160.55 and D377 → +34.08); D376's
> ρ +0.923 is co-movement only. It also opened **§52a** as a declared gap and authorised D378's
> A′_c.
>
> **What it did not fix, and this note therefore remains live:** the corollary sentence itself.
> `docs/FINDINGS.md` on `master` still reads at line 3280 —
> *"at ρ ≈ 0.92 two such constructions are **the same strategy for portfolio purposes**"* —
> which is the clause below. **The heading is corrected; the corollary is not.**
>
> **Superseded by `d9ee2dd`:** the diagnosis, and the level/co-movement split. **Still open:** the
> replacement sentence, the paired-difference-of-means addition, and everything in the two gate
> sections, none of which appears upstream.

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

---

# Gate 1d′, checked at the principal's request — it has the MIRROR of the error, and being mechanical makes that worse

**Gate 1d** (D289 §92): *correlation to every existing book arm < 0.50, at signal level.* Applied
exactly once in the programme's history (D373 H7, failed at ρ = 0.935); D375 flagged it
**UNDER-TESTED** and recommended calibration; D376 replaced it with **1d′** — the same correlation
compared to the **p95 of the pair distribution among books from the candidate's own pool**,
resolving to **≤ 0.526** against the loose pool and **≤ 0.930** against the momentum top decile.

## What 1d′ gets right, and it should be said first

**The pool-relative scoping is a real fix and is orthogonal to this note's critique.** D376
established that a raw 0.50 bar means "independent" in one pool and "structurally identical" in
another, and benchmarking to the candidate's own pool corrects exactly that. **Nothing here
reopens it.**

**And 1d′ does NOT commit §52's error.** It never claims two high-ρ books are the same strategy —
D376 explicitly refuses to license the 0.930 threshold: *"not a licence … independence must be
established some other way there, or not claimed."* That instinct is right. What the record never
does is **say what the other way is.** This note supplies it.

## The gap: 1d′ can only reject, and it rejects on shape alone

| the candidate | ρ vs incumbent | its mean vs the incumbent's | 1d′'s verdict | the right verdict |
|---|---|---|---|---|
| genuinely redundant | high | same | **reject** | reject ✓ |
| **a better version of the incumbent** | **high** | **materially higher** | **reject** | **REPLACE the incumbent** ✗ |
| unrelated | low | anything | pass | pass ✓ |

**Row 2 is the failure, and it is this note's error pointed the other way.** A candidate
correlating +0.60 with an existing arm from the loose pool is rejected by 1d′ **whatever it
earns** — including when it earns twice as much. Two books at ρ 0.92 earning +12 and +1 bp a bar
are not interchangeable, and if the candidate is the +12 one the gate turns it away and keeps the
+1 incumbent. **That is backwards, and a mechanical gate does it silently where a prose claim at
least invites challenge.**

Note the asymmetry in consequence. My §4.1a error dismissed one candidate in a research record and
was caught by reading. **1d′ is an admission hurdle in the stage-1 stack**: the same reasoning,
applied automatically, to everything that reaches it.

## The fix, and it is the same instrument as the rest of this note

ρ and the mean answer **different questions**, and the gate currently asks only one:

- **"Can both be held?"** → ρ, pool-benchmarked. **1d′ as it stands. Keep it.**
- **"Which should be held?"** → a **paired difference of means on matched bars**, which ρ cannot
  answer and does not obstruct — `Var(A − B) = σ²_A + σ²_B − 2ρσ_Aσ_B` is *small* at high ρ, so
  the test is **more** powerful exactly where 1d′ goes blind.

> **Proposed 1d″.** A candidate fails only if **both**: (a) its correlation to an existing arm
> exceeds the p95 of the pair distribution in its own pool (1d′, unchanged), **and** (b) a paired
> difference of means on matched bars does not show it materially above that arm. **Failing (a)
> alone is a REPLACEMENT decision, not a rejection** — the two compete for one slot, and the
> paired test says which wins.

**This also fills D375's open recommendation.** D375 asked for gate 1d to be calibrated and left
it needing its own pre-registration; the missing piece was never only a threshold, it was a second
statistic. And it closes D376's own dangling clause — *"independence must be established some
other way there"* — with a named method rather than an instruction.

**Caveat, stated rather than buried:** a paired means test on two books needs their bar series on a
common mask, and the SE should be **book-clustered** as D376 already does for its correlation p95.
Where an incumbent's series is unavailable the gate degrades to 1d′ and should say so.

---

# The rest of the stage-1 gates, audited for the same one-sided error

**The error class, stated first so the audit is a test and not an impression:**

> **A gate commits it when its statistic is INVARIANT TO — or MONOTONE IN — a quantity the
> decision actually depends on.** ρ is invariant to the mean, and was used to decide about return.
> The audit question for each gate is therefore: *what is this statistic blind to, and does the
> decision depend on any of it?*

Applied to D375's table ([D289](../docs/decisions/D289-the-promotion-pipeline.md) + amendments):

| gate | statistic | blind to | does the decision depend on it? | verdict |
|---|---|---|---|---|
| **1a** | t vs its own null | **size** — t is scale-invariant and grows as √n | yes, but **1c is the complement** | **sound as a PAIR** |
| **1c** | mean move ÷ round trip | **holding period** — monotone in it | **YES, and unpaired** | **⚠ see below** |
| **1d** | correlation | **level** | yes | **⚠ addressed above (1d″)** |
| **1e** t | open-entry t | size | yes, paired with 1c | sound as a pair |
| **1e** retention | ratio of two edges | **level of both** | no — "does it survive open entry" is genuinely a ratio question | sound |
| **1f** | name-split CV t > 0 | **magnitude** — a sign test | yes — **already documented**: D289 calls it *necessary, not sufficient*, and half of pure noise passes | known, not new |
| **1g** | turnover / hold / dead share | — | reporting, no bar | n/a |
| **1h** | direction declared | — | procedural | n/a |
| **1i** | interior vs edge peak | **height of the peak** | no — "is the horizon resolved" is a shape question | sound |
| **2c** | ≥ 1.5× round trip | **holding period** | **YES, and unpaired** | **⚠ same as 1c** |
| **H4′** | names-to-half share vs A′ p05 | P&L level | no — concentration is a shape question, and D374 already fixed the denominator problem | sound |

## The finding: the set is safe because the gates come in COMPLEMENTARY PAIRS

**1a is one-sided — it tests whether an edge is distinguishable from its null, not whether it is
big enough to matter — and a large trade count makes a trivial edge significant.** That would be a
clean instance of the error if 1a stood alone. It does not: **1c is its complement**, and asks the
size question 1a cannot. The same is true of 1e's t and its retention ratio.

**So the rule the set already embodies, and which should be written down:** *no gate in this stack
is an admission on its own; each is half of a pair, and the pairs are (significance, size).*
**The two places the pairing breaks are exactly where the errors are** — 1d had no partner at all
(fixed above as 1d″), and 1c/2c have no partner on the axis below.

## ⚠ 1c and 2c are monotone in holding period, and nothing pairs with that

**`mean move per trade ÷ round-trip cost` rises mechanically as the hold lengthens**: the numerator
accumulates with holding time while the denominator is one round trip per trade regardless. **A
candidate can clear 1c by holding longer while its per-bar edge falls.**

**This is not speculation and it is not new doctrine** — `CLAUDE.md` already states it:

> *"A longer hold lifts breakeven by amortising one round trip; per-bar edge usually falls, so
> Sharpe can drop as cost coverage rises. Say which moved."*

**and it was confirmed on a different per-trade statistic four commits ago.** D373's segmentation
diagnostic (`7aa95aa`) re-cut D365's own stored paths — identical exposure, only the trade
boundaries changed — and the `mean > median > 0` chain **passed at 40 bars and failed at 100**.
Per-trade statistics inherit whatever the exit rule does to trade boundaries. **1c and 2c are
per-trade statistics.**

**What is missing is not the knowledge, it is the encoding.** The doctrine says "say which moved";
the gate does not require it, and **D375's audit marked 1c and 2c SOUND without noting the
dimension.** Their soundness *as cost tests* is not in question — the claim being flagged is
narrower:

> **"Clears 1c" is not comparable across candidates with different holding periods, and a
> candidate that clears it by lengthening its hold has not improved.**

**Proposed 1c′ / 2c′ — a pairing, not a re-thresholding**, in the same shape as 1d″ and H4′:

> The per-trade cost ratio is reported **beside the per-bar edge on the deployed base at the same
> hold**, and a candidate that clears the ratio while its per-bar edge falls versus a shorter hold
> is recorded as **HOLD-DRIVEN**, not as clearing. The horizon profile 1i already requires
> supplies both numbers, so the cost is a column and not a new run.

**Scope, stated honestly.** 1c has been applied to D290's 51 candidates and 2c across D264–D284,
so this is the most-used gate in the set — but the flag does not overturn any past verdict, because
those comparisons were made **at a fixed cap within each study**. The exposure is *cross-study*
comparison and any future candidate whose hold is a free parameter.

---

## What the principal is asked to decide

1. Replace the clause, or leave it and let this note stand as the qualification?
2. If replaced — amendment in place with a date, per the append-only convention, rather than a
   quiet edit?
3. Is the paired-difference test worth adding to the stage-1 gates as the standard way to ask
   "does this selector beat its own pool"? It is cheaper and more powerful than the per-trade
   `B_c` where both books exist as bar series.
4. **Does gate 1d′ become 1d″** — correlation *and* a paired difference of means, with a failure
   on correlation alone treated as a **replacement** decision rather than a rejection? This is the
   substantive one: 1d′ is an automatic hurdle, it has been applied once in the programme's
   history, and D375 already has it flagged UNDER-TESTED and awaiting a calibration
   pre-registration. **If 1d″ is wanted, that pre-registration is the place to put it** rather
   than amending a gate in a research note.
5. **Do 1c and 2c gain the HOLD-DRIVEN qualifier** (1c′/2c′ above)? It is a reporting column
   rather than a new measurement — 1i's horizon profile already produces both numbers — and it
   costs nothing to add to the next pre-registration that uses them.
6. **Should "no gate is an admission on its own; each is half of a (significance, size) pair" be
   written into D289 as a standing property of the stack?** It is what makes 1a and 1e safe, it is
   currently implicit, and both errors found in this audit are places where the pairing was
   missing rather than where a threshold was wrong. Writing it down turns "check the threshold"
   into "check the pair", which is the test that found them.
