# D523 — the oracle label: is the trending exception a **detectable state**, and can a **causal** statistic see it coming?

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D523-the-oracle-label-is-the-trending-exception-a-detectable-state-and-can-a-causal-statistic-see-it-coming.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
**Fixture `data/fixtures/fut_day5m.parquet`. 35 roots, 2011-01-03 → 2023-12-29 in sample.
2024-01-01 → 2026-09-09 is RESERVED AND NOT READ by this record.**

**No return is read as a P&L, no cost is charged, no position is taken.** The output of this study
is a **label** and a ranking of **causal features** against it. Nothing can be admitted from it
(R15), and nothing here is a construction.

---

## 0. The question, in the principal's four words

The principal specified the oracle's design as **intraday clock, unsigned, non-overlapping, predict
the trending exceptions**, and corrected an earlier draft of mine with the decisive sentence: *"For
the oracle I wanted it to measure mean reversion-ness using future information that then can help us
form a causal one."* So this is an **oracle LABEL, not an oracle trade** — a statistic computed with
the future in hand, whose only purpose is to define the target a causal statistic is then asked to
hit. And: *"The truth is I would like to filter out exceptions"* — the default state is the random
walk, and what is being hunted is the **minority of blocks that trend**.

That framing makes the study three questions in order, and **the first two can close it before any
feature is tested**:

1. **Is there a state at all?** If trendiness is an independent coin flip per block, no session-level
   or bar-level feature can predict it, and the line closes on arithmetic rather than on a search.
2. **Is the state an EXCESS over noise?** A block can look trending simply because three coin flips
   came up the same way. The exception must be commoner than sign-exchangeability alone produces.
3. **Only then:** does a causal statistic see it coming?

## 0.1 The prior is strongly negative, and this record must be able to land there

**Four findings on the record argue that the answer is no**, and they are recorded here so the
result cannot be dressed up afterwards:

- **D471: ES is the random walk.** Path efficiency sat at the random-walk value in every bucket of
  volatility and of efficiency itself, and the variance ratio ran **0.82 at 1 s to 1.02 at 60 s** —
  at or below 1, i.e. mildly *mean-reverting*, never trending.
- **D502: the daily variance ratio is below 1 on seven roots of eight**, with NQ above 1 in 0.4% of
  sessions.
- **Price-path momentum has failed at every horizon tested here** — 10 s to 5 h, two clocks, eight
  roots — and D474's ES gradient turned out to be selection and flipped on seven unseen roots.
- **D471 called path efficiency a failed conditioner explicitly**, and that is the very statistic
  this label is built from.

**So why run it.** Each of those measured a different object. D471 conditioned **trailing efficiency
to predict forward |move|** — a *magnitude* question — on **ES alone**, at 1 s–300 s grids. This asks
whether the **trending STATE is a persistent property**, on **35 roots at 5 minutes**, against a
null that D471's own §4 got wrong. If the answer is no, the record is still worth having: it
**confirms D471 on 34 more roots and closes the mean-reversion-detection line on a premise rather
than on a construction**, which is cheaper than the four studies that would otherwise be written to
find it out.

## 0.2 The defect in D471 that dictates the label's design

D471 §4 divided measured efficiency by `1/√n` and reported a comforting ratio of 1.00. Its own
AMENDMENT 2 retracted that: for any iid step distribution the truth is

    E[efficiency] = C / sqrt(m),      C = sqrt(2/pi) * sigma_r / E|r|

and `C = 1` **only** for Gaussian steps. Measured `C` on ES was **1.17–1.21 at every grid**, so the
benchmark ran ~20% low and the 1.00 was two errors cancelling; against the correct benchmark the
ratio was 0.78–0.87.

**The lesson taken here is not to estimate `C` better. It is to need no `C` at all.** Efficiency is
**resolution-dependent** and its benchmark depends on the step-size distribution, which varies by
root, by era and by hour. So the label below is a **percentile inside each block's own
sign-shuffle distribution**, which conditions on that block's exact step sizes, is exactly uniform
under the null by construction, and inherits none of `C`'s fragility.

---

## 1. The oracle label

For a contiguous run of `H` five-minute log returns inside **one session** of one root, with
`r = (r_1 … r_H)`:

    eff = |sum(r)| / sum(|r|)                    in [0, 1]; 1 = a straight line, 0 = a round trip

**This is unsigned** (`eff` is invariant to a global sign flip) as the principal specified, so the
label is a *state*, never a direction.

**The label is the block's own sign-shuffle percentile.** Hold `|r_1| … |r_H|` fixed and range over
all sign vectors `s ∈ {−1,+1}^H`:

    eff(s) = |sum(s_i * |r_i|)| / sum(|r_i|)
    z      = P(eff(s) < eff_obs) + 0.5 * P(eff(s) = eff_obs)        [mid-p]

**`z ∈ [0,1]`, and under within-block sign exchangeability its mean is exactly 0.5.** `eff(s)` is
invariant to `s → −s`, so the group has **2^(H−1) distinct elements** and is **enumerable exactly**
at the horizons that matter:

| H | 2^(H−1) | null CDF granularity | how the null is computed |
|---:|---:|---:|---|
| 3 | 4 | 0.250 | **exact enumeration** |
| 4 | 8 | 0.125 | **exact enumeration** |
| 6 | 32 | 0.031 | **exact enumeration** |
| **8** | **128** | **0.0078** | **exact enumeration — THE PRIMARY** |
| 12 | 2,048 | 0.00049 | **exact enumeration**, chunked over blocks |
| 16 | 32,768 | — | **8,192 sampled sign vectors**, sampling SE reported |
| 20 | 524,288 | — | **8,192 sampled sign vectors**, sampling SE reported |

This follows CLAUDE.md's rule — *where the null's group is finite and small, enumerate it instead of
sampling, and the SE is then exactly 0* — and declares the two horizons where it is not feasible
rather than quietly sampling everywhere.

**Why a sign shuffle and not a rotation.** The house rule is that a smoothed series is **rotated**,
never shuffled, because shuffling destroys autocorrelation and makes the null too narrow. **The
exception is exactly this statistic:** the claim under test *is* the sign arrangement, `sum(|r|)` is
held identically fixed, and a rotation of a within-block sign vector is not even well defined for
`H = 3`. A rotation null appears in Stage 2, where the object rotated is a **feature series across
sessions**, and there the house rule applies in full.

**THE EXCEPTION** — the trending block — is

    exception  iff  eff_obs > q95(block),   q95 = the smallest atom of the block's null with CDF >= 0.95
    b0(block)  =    the block's EXACT null probability of exceeding q95        (<= 0.05 by construction)

`b0` is **computed per block and pooled**, never assumed to be 0.05. The **excess** is
`observed_rate − mean(b0)`, in percentage points.

### 1.1 THE EXCEPTION IS DEGENERATE AT H = 3 AND H = 4, and is therefore not defined there

This was found by computing `b0` before writing the runner, and it is the reason the threshold is
stated as an atom of the null rather than as "the top 5%":

| H | atoms | CDF of the atom below `q95` | **`b0` = exact P(eff > q95)** |
|---:|---:|---:|---:|
| **3** | 4 | 0.7500 | **0.0000 — CANNOT FIRE** |
| **4** | 8 | 0.8750 | **0.0000 — CANNOT FIRE** |
| 6 | 32 | 0.9375 | 0.0312 |
| **8** | 128 | 0.9453 | **0.0469 — the primary** |
| 12 | 2,048 | 0.9497 | 0.0498 |
| 16 | 32,768 | 0.9500 | 0.0500 |
| 20 | 524,288 | 0.9500 | 0.0500 |

At `H = 3` and `H = 4` the smallest atom with CDF ≥ 0.95 **is `eff = 1`** — the all-same-sign path —
so nothing can exceed it and the exception rate is identically zero **whatever the data does**. A
gate whose threshold its own null makes unreachable has happened here before and is exactly what a
premise check is for.

**So: the exception and the lift are reported only for `H ≥ 6`.** At `H = 3` and `H = 4` only the
**continuous `z`** statistics are computed — the Spearman bridge and the split-half reliability,
both of which are well defined at every horizon. The runner **raises** if an exception rate is
requested below `H = 6` (§7 check 7), rather than silently reporting a zero.

**And note the gate moves with the horizon** — `b0` runs 0.0312 → 0.0500 across the usable ladder —
so a raw exception rate is not comparable across horizons and only the **excess over `mean(b0)`**
ever is.

### 1.2 The secondary label, because D471 says the robust instrument is the variance ratio

Alongside `z`, every cell also reports the block **variance ratio**
`VR = Var(r_k)/(k·Var(r_1))` in D471's form, which is **free of the step-shape problem that broke
`C`**. `z` is primary because it is the principal's chosen construction and is exactly
self-normalising; **but if the two labels disagree about a root or an era, the variance ratio
wins on D471's evidence**, and the record will say so rather than choosing after the fact.

---

## 2. The causal twin, and the bridge

The causal twin is **the same statistic on the block immediately before**, so the pair is adjacent,
**non-overlapping**, and wholly inside one session:

    x_t = z computed on  r[t-H+1 .. t]        CAUSAL: known at the close of bar t
    y_t = z computed on  r[t+1   .. t+H]      THE ORACLE LABEL: the future

**`y_{t−1}` is NOT causal** — it ends at bar `t + H − 1`, which is in the future at `t`. This is
written down because it is the single easiest error to make here, and the runner asserts it (§7).

**The bridge is `corr(x_t, y_t)`.** Both `x` and `y` are uniform by construction, so **Spearman** is
the natural coefficient and is the one reported; Pearson is reported beside it.

---

## 3. The primary statistic — ONE (R14)

**`rho = Spearman(x_t, y_t)` at H = 8, pooled over the 35 eligible roots, in sample.**

**Why H = 8.** It is the geometric middle of the declared sweep; 8 five-minute bars is 40 minutes,
comfortably past the 15-second scale at which D471 showed bid-ask bounce stops contaminating the
path; `84 / (2·8) = 5` pairs per session balances block length against per-session count; and **its
null is enumerated exactly at 128 atoms, so the primary cell carries ZERO null sampling error.**

**Reported beside it, always:** the **lift**
`P(y is an exception | x in its top quintile) / P(y is an exception)`, which is the interpretable
form of the same claim, and `n_eff`.

**`n_eff` is counted in SESSIONS, not blocks.** Blocks inside one session are non-overlapping but
they are *not* independent if a session-level state exists — which is precisely what Stage 0a tests.
So every SE and every confidence statement uses a **session-level block bootstrap** (resample
root-sessions with replacement, 2,000 draws), and the naive block count is reported only as a
denominator. In sample there are **84,776 root-sessions** and, at H = 8, **388,378 contiguous pairs**.

---

## 4. The stages, in order, each with a gate that can stop the study

### Stage 0a — is trendiness a SESSION-LEVEL state at all? *(split-half reliability)*

The principal asked whether a null matters on an oracle and suggested *"maybe on the split-half
correlation?"* — **that is exactly where it matters most**, and this is the stage it governs.

Within each root-session, take the session's non-overlapping forward blocks in clock order, split
them into **odd-indexed and even-indexed** blocks, and average `z` within each half. Then across
root-sessions:

    reliability = Spearman( mean z over odd blocks , mean z over even blocks )

**If trendiness is an independent coin flip per block, this is zero.** If sessions carry a
trendiness regime, it is positive. Sessions yielding fewer than 4 blocks are excluded and the count
reported.

**Null:** the within-block sign shuffle, applied to every block, which makes `z` uniform-iid by
construction and gives the reliability's finite-sample width at the true `n`. Enumerated at H = 8.
**GATE 0a:** reliability exceeds the null's p95 by more than **2 bootstrap SE** of that p95
(D373's rule; a margin inside 2 SE is recorded **UNRESOLVED**, not passed).

### Stage 0b — is the exception an EXCESS over noise? *(base rate)*

    excess = P(eff_obs > q95) - mean(b0),   in percentage points, per root and pooled
            reported at H in {6, 8, 12, 16, 20} only -- H = 3 and H = 4 are degenerate (&sect;1.1)

**GATE 0b:** the pooled excess **at H = 8** is positive by more than 2 session-bootstrap SE. The
other four usable horizons are reported beside it and are not the gate.

**This is the number that decides whether anything downstream is worth computing.** If the excess is
zero, trending blocks occur exactly as often as coin flips produce them and there is no exception to
detect. If it is **negative**, these markets are *choppier* than sign-exchangeability — the
bid-ask-bounce signature D471 found in RTH — and the exploitable asymmetry, if any, is on the
*reverting* side.

**STOP RULE.** If **both 0a and 0b fail**, the study ends at Stage 0, the line is closed on its
premise, and Stages 1–2 are **not run**. This is written in advance so that failing stages cannot be
re-read as exploratory.

### Stage 1 — the backward-efficiency baseline *(the primary)*

`rho` and the lift, at all seven horizons, per root and pooled. The full `35 × 7` ladder is reported.

**Null:** sign-shuffle the **forward** block only, holding `x` identically fixed. This **breaks
exactly the claimed ingredient** — the sign arrangement of the future — and preserves everything
else, including `x`, the volatility level and the session structure.

**GATE 1:** the primary `rho` differs from its null p95 (or p05, for a negative `rho`) by more than
2 bootstrap SE, **and** the lift is outside `[0.90, 1.10]`.

**BOTH SIGNS ARE A RESULT, and the reading differs.** `rho > 0` means a trending past predicts a
trending future — momentum, and a *selector*. `rho < 0` means a trending past predicts a reverting
future — which is the principal's **filter** in its most direct form. Neither is dressed as the
other after the fact.

### Stage 2 — the five declared causal features

All five are computed **only from bars up to and including `t`**. Declared now, in full, so the set
cannot grow:

| | feature | definition |
|---|---|---|
| **F1** | backward efficiency | `x_t` — Stage 1's statistic. **THE DECLARED PRIMARY of the family.** |
| F2 | volume rising or drying | `log(sum vol over [t−H+1,t]) − log(sum vol over [t−2H+1,t−H])`; needs `2H` bars before `t` |
| F3 | close position in range | `|2·(close_t − min low)/(max high − min low) − 1|` over `[t−H+1,t]` — **unsigned, to match the label** |
| F4 | realised volatility level | `sum |r| over [t−H+1,t]`, divided by that root-session's median block value |
| F5 | time of day | the session quarter containing `t` (4 levels) |

Per feature: Spearman with `y`, and the exception lift in the feature's **top quintile**, with **the
number of blocks AND THE NUMBER OF SESSIONS in that quintile reported** — because a degenerate cell
once beat a rotation null here at +37.7 SE on six traded sessions, and only a duty-cycle premise
caught it.

**Null for F1–F4: the enumerated session rotation.** Rotate the feature series by whole sessions
within a root, pairing session `i`'s feature with session `i+k`'s label, which preserves each
session's intraday feature shape and the feature's autocorrelation. Offsets common to all roots are
limited by the smallest root (**SR3, 756 sessions**), so **755 common offsets are enumerated
exactly and the SE is 0**.

**F5 CANNOT USE THAT NULL, and saying so is the point.** A session rotation preserves the bar index
exactly, so the rotated time-of-day feature **equals the original** and the null is degenerate — a
control that cannot break the claimed ingredient. F5 is therefore tested against its own null: a
**permutation of block labels within each session**, which destroys the clock while preserving the
session's set of `z` values.

**GATE 2 (family):** the family maximum over F1–F5 under **common** offsets, with the 2-SE
UNRESOLVED band. A feature clearing only its own single-feature null is reported as such and **not
claimed**.

---

## 5. Universe, window, and what is deliberately not read

- **35 roots** — every root in `fut_day5m` with a `first_clean_year`, each read **from its own clean
  year**. The coverage block in `fut_day5m.meta.json` supplies them: FX ×6, GC HG SI UB ZB ZF ZN ZT
  from 2011; the five grains 2014; BZ 2015; CL HE HO LE NG NKD PL RB TN and ES NQ YM 2016; RTY 2018;
  BTC 2020; SR3 2022.
- **PA is EXCLUDED.** It never reaches 90% slot fill in any year (0.798 at best) and its
  intermittent interior slots would put holes inside blocks.
- **Rows with `present = False` or `same_front = False` are dropped** — the holidays, half-days and
  thin sessions, and the rolls. Cost: 8,485,471 rows survive of 8,837,120 after the clean-year cut.
- **Blocks must be CONTIGUOUS.** A block is used only if all `H` bar slots are present and
  consecutive; 95.9% of sessions are a single unbroken run and the contiguity requirement costs
  **0.2% of pairs at H = 3 rising to 1.9% at H = 20**, reported per horizon.
- **In sample: 2011-01-03 → 2023-12-29**, 6,687,262 bars, **84,776 root-sessions**.
- **RESERVED AND NOT READ: 2024-01-01 → 2026-09-09**, 1,798,209 bars, 22,909 root-sessions. Any
  feature clearing Gate 2 earns **one** pre-declared confirmation read there, in a separate record.
  This is a **new line** — the oracle label — so its holdout is unspent (holdout multiplicity is per
  line), and it stays that way unless something clears.

## 6. Predictions, in the runner's own quantities

Written before the runner exists, each computable from the artifact, so the record can be scored
against them rather than reinterpreted:

| | prediction | why |
|---|---|---|
| **P1** | **Stage 0b pooled excess at H = 8 lands in `[−1.0, +1.5]` pp** (against `b0` = 0.0469), and is **negative on ES, NQ, YM** | D471's RTH efficiency ran *below* the random-walk value — bid-ask bounce makes index paths choppier than exchangeable signs |
| **P2** | **Stage 0a reliability is in `[0.00, 0.08]`** | `z` is vol-normalised inside each block, so the strongest intraday regime — volatility clustering — cannot feed it; little else is on offer |
| **P3** | **the primary `rho` is in `[−0.05, 0.00]`** — slightly **negative** | a variance ratio below 1 on 7 of 8 roots (D502) means a trending block is followed by a reverting one |
| **P4** | **the Stage 2 family maximum does not clear its rotation p95** | eight roots, two clocks and five horizons of price-path momentum have already failed here |
| **P5** | **the H ladder is monotone decreasing in \|rho\|**, with the largest \|rho\| at H = 3 | whatever survives at 5-minute resolution is microstructure, and microstructure decays with the block |

**If P1 and P2 both land, the study stops at Stage 0 and the line closes** — and that outcome is a
result, not a failure to find one.

## 7. Checks the runner must carry, each able to fire

1. **`eff` on paths whose answer is known by hand** — a straight line gives 1, a round trip 0, an
   out-and-two-thirds-back 0.2; sign-blind; bounded in [0,1]. D471's set, reused.
2. **The enumeration is the whole group.** For H = 8, exactly 128 distinct sign vectors are visited,
   `eff(s) == eff(−s)` for every one, and the enumerated set equals a brute-force `2^H` sweep
   deduplicated.
3. **`z` is uniform under the null.** On a synthetic iid-random-sign series, mean `z` = 0.5 and the
   exception rate equals `mean(b0)` within the session bootstrap SE. **[X]** the same check on a
   deliberately trending series must FAIL.
4. **Causality.** `x_t` reads no bar after `t` and `y_t` no bar before `t+1`, asserted by
   re-deriving both from index slices in **a second implementation that never calls the block
   builder** — the lag-audit pattern that killed D279's first result. **[X]** it must raise when
   `y_{t−1}` is substituted for `y_t`.
5. **Non-overlap.** No bar index belongs to both the `x` block and the `y` block of the same pair,
   and no two forward blocks of one session share a bar.
6. **Contiguity.** Every block's bar indices are consecutive; asserted on a session with a
   hand-punched hole.
7. **`b0` is exact, and the exception path REFUSES a degenerate horizon.** The per-block null tail
   probability equals the enumerated fraction of atoms above `q95`; `b0 <= 0.05` always; and
   `b0 == 0` exactly at H = 3 and H = 4 with `q95 == 1.0`, which the runner asserts and then
   **raises** on, rather than reporting a zero exception rate that looks like a measurement.
   **[X]** requesting an exception rate at H = 4 must raise.
8. **The rotation is exact and common.** 755 offsets, identical offsets across roots, and the
   observed cell is offset 0. **[X]** F5's rotation is asserted **degenerate** (rotated feature
   equals original), which is why F5 uses a different null.
9. **The runner computes the PRE-REGISTERED statistic.** A guard asserts the primary reported is
   Spearman(x, y) at H = 8 pooled over 35 roots, because D506's runner compared a different quantity
   than its pre-registration declared and a 30% gap went unnoticed.
10. **Duty cycle.** Every reported cell carries its block count **and its session count**.
11. **Speed.** `parallel_map` from `scripts/fast_null.py` for the per-root fan-out, with its
    `[SPEED]` efficiency line. `assert_matches_scorer` does **not** apply — it takes a positions
    panel and this study has no positions — so the equivalent guarantee is provided instead: the
    vectorised sign-enumeration is asserted **bit-identical** to a reference loop on a **tie-heavy**
    input (blocks whose `|r|` values are equal, where a rewrite is most likely to disagree).

## 8. Decision rule, pre-registered

- **LINE CLOSED ON PREMISE** — both Gate 0a and Gate 0b fail. Stages 1–2 are not run. The finding is
  that the trending exception is neither a session-level state nor commoner than exchangeable signs,
  on 35 roots, which extends D471 from ES to the whole liquid CME day session.
- **STATE WITHOUT PREDICTABILITY** — a gate at Stage 0 clears but Gate 1 fails. The label is real
  and the nearest causal statistic cannot see it; Stage 2 runs, and if its family also fails the
  line closes with the label kept as a measurement instrument.
- **A CAUSAL DETECTOR** — Gates 0, 1 and 2 all clear. Then and only then: one confirmation read on
  the reserved 2024+ slice, pre-declared in a separate record. **Even that does not admit anything**
  — a detector is not a construction, and any construction built on it needs its own
  pre-registration, its own cost line at the size the account trades, and hurdle P.
- **UNRESOLVED** wherever a margin sits within 2 SE of a null percentile. Recorded as unresolved,
  never rounded into a pass.

## 9. What this record does not do

No P&L, no cost model, no position, no flatten, no hurdle P, no component line — because there is no
construction to score. Nothing enters `FINDINGS.md`, `RULES.md`, `COMPONENTS_PROP.md` or either
book on this record's own authority (R8, R15). The reserved slice stays unread unless Gate 2 clears.
