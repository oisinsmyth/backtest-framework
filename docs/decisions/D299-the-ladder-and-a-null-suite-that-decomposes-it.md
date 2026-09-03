# D299 — the ladder, and a null suite that decomposes it

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**The holdout is not read. Holdout reads spent: 0.**

---

## The question

Every exit tested so far has been a rule about **one position**. D298 showed
that on this book such a rule is largely inert:

```
S=reversion + P=stop    vs S=reversion alone:  0.00% of held bars differ
S=reversion + P=target  vs S=reversion alone:  0.00% of held bars differ
S=reversion + P=both    vs S=reversion alone:  0.00% of held bars differ
```

**19 slots and 19 selected: an exit frees a slot that the same name refills.**
The price axis did not fail — it was never able to act.

**The ladder is the smallest change that unpins it.** Instead of asking *should
this position leave*, ask **how many pairs should the book hold** — and when the
answer is 18, `free = N_SLOTS − len(held)` is zero and the vacating name does
not come back.

This record specifies that family and, because it has two separable mechanisms
rather than one, **a suite of five nulls that decomposes it** instead of a single
control that would confound them.

## 1. The construction

### 1.1 The statistic

```
m[t]     = mean r1 over ALL live names at t          the market
x[i,t]   = r1[i,t] − m[t]                            the name's spread move
cum[i]   = Σ σ·x[i,τ]  over τ = entry+1 … t          σ = +1 long, −1 short
u[i]     = trailing sd of x[i,·]                     IDIOSYNCRATIC vol
z[i]     = cum[i] / (u[i]·√age[i])                   age-normalised
D[t]     = mean z over all 38 positions              the book's convergence, in σ
```

**`m` is the whole live cross-section, never the leg mean.** The mean of the 19
longs *is* the edge; netting against it deletes the signal. This was corrected
once already, in D297's premise, and never propagated to the position rules —
D295's `adverse_stop` and `profit_target` compare a **raw** single-name return to
**total** vol, so both fire partly on market beta. This family does not inherit
that.

**`u` is the sd of `x`, not of `r1`.** Beta is removed from the numerator, so it
must be removed from the denominator, or a high-beta name silently gets a wider
band than a low-beta one.

**`√age` is not cosmetic.** A cumulative sum over `a` bars has sd growing like
`u·√a`, so a flat band gets mechanically easier to hit as positions age. At k=5
that is mild; at k=20 a flat band degenerates into "exit at a random early bar",
and any k comparison built on it would measure the artefact.

**`m` cancels exactly in the book return.** `mean(r_long − m) − mean(r_short − m)
= mean(r_long) − mean(r_short)`, because both legs are equal-weighted 19-name
means. **The reference changes when positions leave and changes nothing else.**
Assertion [2b] holds the runner to that bit-identically.

### 1.2 The shadow

**`D` and `peak_D` are computed on the SHADOW book — the full 19 that would have
been held, i.e. the control book — not on what the ladder actually holds.**

This is the load-bearing choice in the design, and it fixes two separate defects:

**The feedback loop.** If `D` were the mean `z` of the *held* positions, dropping
the highest-`z` name would lower `D` by construction — the rule would cancel its
own trigger. The move is `(z_max − D)/N`, so the divisor shrinks as the ladder
descends: about 0.1σ at 19 slots, 0.2σ at 10, 0.4σ at 5. **The rule would become
most self-cancelling exactly where it is most engaged**, and would oscillate:
drop, un-trigger, refill, re-trigger. On a book where turnover is already the
binding constraint, that is a churn machine.

**The freeze.** A statistic keyed on realised state stops evolving once the rule
de-risks — no new peak can arrive, so `peak_D − D` never clears and the ladder
never comes back up. This is D297's argument for shadow equity, unchanged.

**Accepted cost, stated:** the ladder is blind to what it actually holds. At
N=10 a shadow in drawdown keeps it down even if those 10 are doing fine. The
hybrid — `D` on the held book, `peak_D` on the shadow — was considered and
rejected: it re-imports the feedback loop for part of the benefit.

### 1.3 The rules

```
DOWN, immediate, one rung:   D ≥ T_b               harvest — the book has converged
                        or:  peak_D − D ≥ S_b      protect — it has retraced

UP, one rung, after C_up consecutive bars with NEITHER condition true.

N ∈ [N_min, 19].  Mirrored: one long and one short per rung.
```

**Down fast, up slow.** The cooldown replaces a hysteresis band deliberately: it
is an integer rather than a third float, it rate-limits turnover directly, and it
matches exactly under rotation. With the shadow removing the feedback loop there
is no boundary chatter left for a band to suppress.

It cannot freeze and it cannot sawtooth badly. A persistent trigger ratchets to
`N_min` and holds; an intermittent one drifts back up; a flickering one is bounded
in both amplitude and turnover by `C_up`.

**Stepping up needs no new machinery** — `free` goes to 1 and refills from
`sel[:,t]` best-first, the existing path, and re-incurs the entry cost correctly.

**Mirroring has a cost and it is accepted, not hidden:** when only one leg has
converged, the mirror forces a drop on the other leg that the signal did not ask
for. That is the price of neutrality, and it is why the trigger is the pooled `D`
rather than `Z_L` and `Z_S` acting independently — independent legs would let the
counts diverge, and the book would stop being a spread.

### 1.4 Both directions are declared, because both have support

`T_b` and `S_b` are not alternatives and neither is the "obvious" one:

| | reading | evidence |
|---|---|---|
| **`T_b` harvest** | converged, take it off | D295 B6 profit target, +12.49 bp, t = +2.94, p = 0.005 |
| **`S_b` protect** | retraced from peak, de-risk | D297 X=12 overlay, +0.215 Sharpe, p = 0.015 |

They are not in conflict — one keys on **level from entry**, the other on
**drawdown from peak** — so both are knobs and either may be switched off.

## 2. Parameters

| axis | levels | note |
|---|---|---|
| `T_b` harvest | **q70 · q85 · off** | quantile of the observed `D` |
| `S_b` protect | **q70 · q85 · off** | quantile of the observed `peak_D − D` |
| `N_min` depth | **17 · 13 · 10** | 19→18→17 is a 10.5% exposure move — likely too shallow to detect |
| `C_up` | **1 · 5 · 20** | immediate · half a hold · one k=20 cycle |
| drop-choice | **highest own `z` · worst composite `rank`** | two different theories of *which* |
| `k` cap | **5 · 20** | |

**Thresholds are declared as quantiles of their own observed distribution, not
as σ values.** D297 declared X ∈ {1.0 … 3.0} daily vols when the book's median
drawdown was 4.6 daily vols, and assertion [3] caught it at 17.5% exposure — the
grid had to be amended to {8 … 30} before any result. **A quantile cannot make
that error.** The distribution of `D` and of `peak_D − D` is measured and printed
**before** the grid runs, and assertion [3] requires every declared threshold to
produce a fire rate strictly between 0% and 100%.

### The grid

**Stage 1** — `C_up = 5`, drop by `z`, `k = 5`:
8 trigger combinations (3×3 minus off/off) × 3 depths + 1 control = **25 cells**.

**Stage 2** — carried on stage 1's best cell:
`C_up` (3) × drop-choice (2) × `k` (2) = **12 cells**.

**37 declared cells.** Stage 2 conditions on stage 1's winner. That is a fork and
it is named here rather than glossed: multiplicity is counted across all 37, and
the stage-2 numbers are reported as conditional.

## 3. THE NULL SUITE — the substance of this record

The ladder has **two separable mechanisms**, and a single control confounds them:

- **A — the exposure path** `N(t)`: its levels, its persistence, its timing.
- **B — the selection**: which pair leaves when a rung drops.

D297's rotation null tests A and is completely blind to B — it still drops by the
treatment's own criterion. A single null would report "the ladder works" without
saying which half works, and the two have different implications: A is a
risk-management result, B is a signal result.

**Five nulls, each isolating one component.** Every one is rate- and
persistence-matched where it claims to be; none is count-matched only (D279).

| | null | what is randomised | what is held EXACTLY | isolates |
|---|---|---|---|---|
| **N0** | control | — | `N ≡ 19` | *(baseline, not a null)* |
| **N1** | memoryless | `N(t)` redrawn i.i.d. each bar | mean exposure only | **deliberately invalid** |
| **N2** | rotation | phase of `N(t)` | level histogram, episode lengths, transition count, cyclic order | **timing** |
| **N3** | episode permutation | order of constant-`N` runs | level histogram, episode-length multiset | **sequencing** |
| **N4** | selection | *which pair* is dropped — uniform over held | **`N(t)` bit-identical to treatment** | **selection** |
| **N5** | joint | order **and** selection | level histogram, episode lengths | the floor |

**N4 is the one a single-null design would have missed.** It shares the entire
exposure path with the treatment — same rungs, same bars, same turnover, same
cost — and randomises only *which* pair leaves. **Every nuisance is matched
except the thing under test.**

**N1 is included precisely because it is invalid.** It re-draws every bar where
the treatment persists, so it churns — the defect that voided D291's veto arm and
that CLAUDE.md now warns about. Reporting it beside N2 **prices how much easier
the wrong control is**, in this study's own units, instead of asserting it.

### 3.1 The decomposition

Because N2 shares B with the treatment and N4 shares A exactly, the differences
read off directly, in Sharpe:

```
value of TIMING       =  treat − N2
value of SELECTION    =  treat − N4
value of SEQUENCING   =  N2 − N3      (both hold the level histogram; only N2 holds order)
total structure       =  treat − N5
```

**And the sum is a testable claim.** If `treat − N5` substantially exceeds
`(treat − N2) + (treat − N4)`, the two mechanisms interact and neither number
stands alone; the runner reports the residual explicitly rather than leaving it
to be inferred.

### 3.2 Which nulls run on which cells

Running five nulls on 37 cells at 200 draws is ~37,000 book simulations. The
allocation is declared here so it is not chosen later:

- **N2 and N4 on all 37 cells** — the two load-bearing components, ~14,800 draws.
- **N1, N3, N5 on exactly two cells** — stage 1's winner, and a **fixed declared
  reference cell** (`T_b=q85, S_b=q85, N_min=13, C_up=5, drop=z, k=5`) so the
  decomposition panel is not entirely results-chosen. ~1,200 draws.

200 draws per cell per null, matching D298.

## 4. Nuisance, multiplicity and the winner's curse are THREE instruments

The nulls above handle **nuisance**. They do not handle the fact that 37 cells
were run. Conflating the two is how a screen turns into a promotion claim.

**Per cell — beating its own null is the bar.** This is a screening stage on
mined data; R14's fourth amendment and the principal's standing ruling both hold.
Cost is **reported, not gating**.

**Across the family — Benjamini–Hochberg at q = 0.10** over the 37 declared
cells, on the treatment-vs-N2 p-values and again on treatment-vs-N4. FDR, not a
family-wise floor: a MIN-p floor was applied at a screen twice (D291, D295) and
was the wrong instrument both times.

**For the headline — a grid-max null.** The max statistic over the whole grid
under N2, so "we ran 37 cells and reported the best" is priced the way D296b
priced the k search. **Reported alongside the winner, not used as a gate.**

## 5. Assertions

All three of the standing ones, plus four this family needs.

1. **Lag audit, second implementation.** `N(t)` and the held set re-derived by an
   independent accumulation loop that never calls the ladder function, from state
   through `t−1` only. Must agree on every bar.
   **1b.** And it must **fail** on a variant that lets the ladder see bar `t`'s
   own return — an audit that cannot fail proves nothing.
2. **Sign audit, in money.** A favourable move pays positively; a market-wide
   move moves the long and short legs oppositely.
   **2b.** **And the reference must cancel:** with the ladder pinned at `N ≡ 19`,
   the book return must be **bit-identical** to the D295 control book. If
   subtracting `m` changes the book's P&L, `m` is not a reference.
3. **Right quantity.** Exposure must be monotone in `N_min` and in `T_b`, and
   every declared threshold must fire strictly between 0% and 100% of bars. A
   ladder whose exposure does not move with its own parameter is not the rule it
   is labelled — this is the assertion that caught D297's mis-scaled grid.
4. **The nulls must match what they claim, and the checks must bite.**
   - N2: level histogram, episode-length multiset and transition count all
     identical to the treatment's.
   - N3: same histogram and multiset, transition **order** demonstrably different.
   - N4: `N(t)` **bit-identical** to the treatment, dropped names demonstrably
     different.
   - **N1 must FAIL N2's persistence check** — if the matching test passes the
     memoryless control, it is not testing persistence.
5. **Reconciliation.** Book total equals the position ledger total to relative
   1e-10. This is D295's assertion [5], which caught the entry-bar double count
   worth ±73–85 bp on numbers of magnitude 7–77.
6. **Unpinning, measured not argued.** Share of held bars on which the ladder's
   roster differs from the control's. D298's price axis measured 0.00%; if this
   one does too, the family has failed mechanically and no cell means anything.
7. **The self-test must raise on a deliberately broken book.**

## 6. Predictions

Committed before the runner exists. Three are against.

| | prediction |
|---|---|
| **Q1** | the ladder beats the control on Sharpe in at least one cell — *weak, expected true* |
| **Q2** | **timing matters**: `treat − N2 > 0` at p < 0.05 in at least one cell |
| **Q3** | **selection does NOT matter**: `treat − N4` is indistinguishable from zero everywhere. *Against.* The value is in reducing exposure at the right time, not in choosing which name — which would also make the drop-choice axis and stage 2 half redundant |
| **Q4** | **sequencing does not matter**: `N2 ≈ N3`, so the ratchet's monotone structure is not load-bearing. *Against* the design's own shape |
| **Q5** | the invalid control is much easier: N1's p-value is below 0.01 in cells where N2's exceeds 0.05 |
| **Q6** | depth matters — `N_min = 10` beats `N_min = 17`; two rungs is too shallow to clear a null |
| **Q7** | **harvest beats protect** — `T_b` cells beat `S_b` cells. *Against D297*, whose overlay was a protect rule and worked; for D295, whose target worked while its stop did not |
| **Q8** | **the unpinning works** — the ladder changes ≥ 5% of held bars against the control, versus D298's 0.00% |

Q3 and Q8 are load-bearing. **Q8 failing means the family is mechanically inert
and the study is void**, which is worth learning in one run.

## 7. Stop conditions

- **Q8 fails (< 5% of held bars differ)** → the family is inert; nothing else in
  the output is interpretable and no cell is reported as a finding.
- **Q3 fails to reject** (selection worthless) → the ladder is a pure
  risk-management overlay in graduated form, the drop-choice axis is dead, and it
  should be compared directly against D297's binary overlay rather than treated
  as a new signal result.
- **Nothing clears N2 or N4** → the family closes; the position-level `(T, S)`
  band becomes the next construction rather than the follow-up.

## 8. Scope

**Out:** D297's binary overlay — this supersedes it in graduated form, and
running both would confound them. **The position-level `(T, S)` band** —
market-referenced take-profit plus a trail that starts as a hard stop and
ratchets — is held back as the follow-up that *composes* with this one: the band
says which positions are eligible to leave, the ladder says how many go.

**The statistic is Sharpe**, because the ladder changes exposure and a mean test
would penalise it for being out of the market. D297's reason, unchanged.

**Cost is reported, not gating.** It is measured with Corwin–Schultz half-spreads
on the names actually held, and reported at both the mean and robust round-trip
estimates, since those still disagree by a factor of 2.5 across the programme.

**Speed:** ~16,000 book simulations. The simulator is GIL-bound pure Python, so
processes over strided cell indices, per CLAUDE.md; `assert_matches_scorer` once
before the grid; the shadow book and the `x` / `u` / `z` arrays cached in `temp/`
keyed on the fixture and every estimator module's mtime.

## Files

`docs/decisions/D299-the-ladder-and-a-null-suite-that-decomposes-it.md`
(this record) · runner and data to follow, in separate commits.
