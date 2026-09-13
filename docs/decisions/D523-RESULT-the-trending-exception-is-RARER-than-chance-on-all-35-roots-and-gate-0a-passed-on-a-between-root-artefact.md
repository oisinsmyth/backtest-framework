# D523 RESULT — the trending exception is **RARER than chance on all 35 roots**, and Gate 0a passed on a **between-root artefact**

**Result of D523** (spec `de26b79`, runner `5a3fb1e`). `scripts/d523_oracle_stage0.py --run`
(`--self-test` passes, 45 checks; 11.3 min), artefact
[`data/d523_oracle_stage0.json`](../../data/d523_oracle_stage0.json).
**35 roots, 2011-01-03 → 2023-12-29, 6,687,262 bars, 84,776 root-sessions. 2024+ NOT READ.**
**No return is read as P&L, no cost, no position. Nothing admitted (R15).**

## 0. The two gates, as pre-registered

| gate | statistic | value | reference | verdict |
|---|---|---:|---:|---|
| **0b** | exception rate − mean(`b0`) at H = 8 | **−1.095 pp** | SE 0.018 → **−61 SE** | **FAIL** |
| **0a** | split-half Spearman of mean `z`, odd vs even blocks | **+0.0264** | null p95 +0.0055 (SE 0.0003) | **PASS** |

**Pre-registered outcome: PROCEED TO STAGE 1**, because the stop rule required *both* to fail.
**§3 shows that reading is wrong, and why.**

## 1. The ladder

| H | blocks | sessions | mean `z` | excess (pp) | reliability | null p95 |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 2,118,947 | 84,764 | 0.4831 | *undefined* | +0.0414 ± 0.0034 | +0.0055 |
| 4 | 1,579,753 | 84,761 | 0.4786 | *undefined* | +0.0427 ± 0.0034 | +0.0056 |
| 6 | 1,031,957 | 84,752 | 0.4732 | −0.400 ± 0.011 | +0.0337 ± 0.0032 | +0.0055 |
| **8** | **790,588** | **84,722** | **0.4706** | **−1.095 ± 0.018** | **+0.0264 ± 0.0036** | **+0.0055** |
| 12 | 474,798 | 84,543 | 0.4707 | −1.491 ± 0.024 | +0.0126 ± 0.0034 | +0.0055 |
| 16 | 387,875 | 68,195 | 0.4670 | −1.677 ± 0.027 | +0.0256 ± 0.0037 | +0.0065 |
| 20 | 303,276 | 65,719 | 0.4661 | −1.780 ± 0.031 | +0.0219 ± 0.0040 | +0.0067 |

H = 3 and H = 4 carry no excess because `b0 = 0` there exactly — the degeneracy the
pre-registration found before the runner existed. The session count falls at H = 16 and H = 20
because a session needs ≥ 4 blocks and the 58-slot grains yield only 3.

## 2. Gate 0b: mean reversion, monotone in the horizon, on every single root

**`mean z` is below 0.5 at every horizon and falls monotonically with H** (0.4831 → 0.4661), and
the excess falls monotonically with it (−0.400 → −1.780 pp). Under sign exchangeability `mean z`
is *exactly* 0.5, so this is a direct, assumption-free statement:

> **A five-minute futures path is straighter than a coin flip LESS often than a coin flip is,
> and the longer the block the truer it gets.**

**The excess is negative on 35 of 35 roots**, from BTC −2.018 pp to ZT −0.517 pp. There is no
subset, no asset class and no era carve-out where trending blocks are commoner than chance.

**This gate needs no confirmatory test and cannot get one.** Its null is the *enumerated* atom set
of each block's own `|r|` — exact, not asymptotic, with no distributional assumption to validate —
and the finding points **opposite** to the hypothesis. A negative excess is not a weak positive.

This extends D471 from ES at 1 s–300 s to **35 roots at five minutes**, and it agrees with D502's
daily variance ratio being below 1 on seven roots of eight. Three independent constructions now say
the same thing on the intraday and daily clocks.

## 3. Gate 0a passed, and the PASS IS AN ARTEFACT

The principal asked, before the result was known, whether these nulls would be enough or whether a
separate test would be needed. **For 0a the answer is that the pre-registered null cannot carry the
claim, and the decomposition below is the separate test.**

The null makes `z` iid across **all** blocks, so it destroys between-root and between-era level
differences along with the within-session structure it was meant to test. It therefore answers
*"is ρ distinguishable from zero at n = 84,722?"* — where **the p95 is simply `1.645/√(n−1)` =
0.00565**, matching the measured +0.0055 to the printed precision. At that n almost any structure
clears.

**The confound is real and large. Mean `z` varies enormously across roots:**

    ZT 0.3926 · SR3 0.4062 · ZN 0.4518 · ZF 0.4594 · SI 0.4623   ...
    HO 0.4895 · ES 0.4898 · YM 0.4923 · NQ 0.4956 · RTY 0.4976
    range 0.3926 .. 0.4976, sd across roots 0.0210

A session inherits its root's level in **both** halves, which manufactures a positive pooled ρ with
**no session-level state at all**. Computing the reliability **inside each root**, where no
between-root difference can leak:

| | pooled | within-root |
|---|---:|---:|
| reliability | **+0.0264** | mean **+0.0069**, **median −0.0031** |
| sign | positive | positive on **15 of 35** roots |
| clears its own null p95 | yes, by 5× | **6 of 35 roots** |

**The pooled +0.0264 is essentially all between-root. The median root is NEGATIVE.**

### 3.1 And the two roots that do carry a within-root signal identify the mechanism

    SR3  +0.2770  on 275 sessions   (own null p95 0.0994)   mean z 0.4062
    ZT   +0.2009  on 3,201 sessions (own null p95 0.0291)   mean z 0.3926

**These are the two coarsest-tick instruments in the universe and the two lowest mean `z`.** That is
not a coincidence, and it was the third confound named in advance: `z` is a percentile inside a
**discrete** atom set whose coarseness depends on **ties in `|r|`**. Where a five-minute bar moves
0 or 1 tick — SOFR and the 2-year note — many `|r|` coincide, many atoms collapse, and `z` takes few
distinct values **in both halves of the session**. A quiet session is coarse in both halves and an
active one is fine in both.

**So what the within-root split-half is detecting on SR3 and ZT is persistence of TICK
DISCRETENESS, not persistence of trendiness.** And SR3's 275 sessions are a thin cell of the kind
that has beaten a null here before on duty cycle alone.

### 3.2 The test that would settle it, if the principal wants 0a settled

A **block-relabelling permutation within (root, era) strata**: keep each block's `z` exactly as
computed and reassign blocks to sessions inside the same root and year. This preserves each root's
*exact* marginal distribution of `z` — discreteness, ties and all — and destroys only the session
grouping, so it kills all three confounds at once. Plus ρ recomputed **within volatility strata**,
which is what separates trendiness-persistence from tick-discreteness-persistence.

**It is not obvious this is worth running.** The within-root decomposition already puts the median
root at −0.0031 with 6 of 35 clearing, and the two that clear strongly are explained by a mechanism
that is not the one under test. The permutation would sharpen a number whose sign is already
known.

## 4. Predictions, scored

| | predicted | measured | |
|---|---|---|---|
| **P1** | excess in [−1.0, +1.5] pp, **negative** on ES/NQ/YM | **−1.095 pp**, negative on **35 of 35** | sign right, **magnitude 0.095 pp outside the band** |
| **P2** | reliability in [0.00, 0.08] | pooled **+0.0264**, within-root mean **+0.0069** | **inside**, on both readings |
| P3–P5 | Stage 1 and 2 quantities | not run | — |

**P1 missed its band, and in the direction that matters**: I predicted the excess might be
positive and it is negative everywhere, more so than the band allowed. **P2 landed**, and its
reasoning — that `z` is vol-normalised within each block so vol clustering cannot feed it — turns
out to have been *incomplete* rather than right: vol clustering feeds it through the **tie
structure**, which §3.1 shows on the two coarse-tick roots. The prediction was correct about the
number and wrong about the mechanism.

## 5. Defects found in this record's own instruments

1. **A UNIT BUG IN MY OWN REPORTING, caught mid-run.** The excess is in percentage points; its
   session bootstrap returned a **fraction**, so the published SE would have been 100× too small
   and the gate compared pp against a fraction. The verdict was unaffected — a negative excess
   fails either way — but the run was stopped, the bug fixed, and the SE is now asserted to be
   centred on the point estimate in pp.
2. **Two of my own self-tests were duds.** The hole check asserted a block-count drop; 20 bars give
   19//4 = 4 blocks and two 9-bar runs give 2+2 = 4, **the same number**, so it could not
   discriminate — it now asserts every bar a block *reads* is present. And the bit-identity check
   required the recomputed efficiency to *differ* from the enumerated one; 0 of 500 differed, so it
   failed on a correct implementation. Replaced by the actual invariant plus a one-ULP break.
3. **`add.reduceat` and `bincount` do not sum in the same order**, differing by 1 ULP on ~8% of
   sessions. Reordering a float sum is forbidden, so the rewrite is held to the invariant that
   decides the statistic: **Spearman reads only ranks**, and the ranks are asserted bit-identical,
   with a break that fires when two sessions genuinely swap.
4. **A cache-locality optimisation I predicted would help gave 16% and was not adopted** — the
   gather is bandwidth-bound on its output, not input locality. Third time this session that
   profiling contradicted me.

**Speed:** 40 min projected → **11.3 min**. Labelling 6.8× (one order statistic instead of a sort;
the full mid-rank table computed only where a null draw reads it), the null loop 2.6× (a vectorised
tie-walk replacing an 84,000-iteration Python loop, and batched draws), and the per-root frame split
hoisted out of a 245-scan loop.

## 6. What this record does and does not settle

**SETTLED.** The trending exception is **rarer than chance at every horizon on every root**, by an
exact null, monotonically in H. Gate 0b fails and cannot be rescued.

**NOT SETTLED, AND NOT CLOSED HERE.** Gate 0a cleared its pre-registered bar, so by the letter of
the stop rule Stage 1 is authorised. But the pass is a between-root artefact, the median root is
negative, and the two roots that do carry it are explained by tick discreteness rather than
trendiness. **Whether to spend Stage 1, run the stratified permutation of §3.2 first, or close the
line is the principal's call** — only the principal closes an avenue.

**One asymmetry worth stating plainly for whatever comes next.** The principal's framing was to
*filter out exceptions*. This result says the exceptions are **rarer** than chance, which is the
opposite of a trending tail — but it is also, read the other way, a **mean-reversion state that is
commoner than chance and strengthens with horizon**. That is a finding about the state, not a
construction, and it earns no position: a fade book is negative skew, which `BOOK_PROP.md` calls
fatal, and nothing here has been costed.

Nothing enters `FINDINGS.md`, `RULES.md`, `COMPONENTS_PROP.md` or either book on this record (R8,
R15). The 2024+ slice remains unread.
