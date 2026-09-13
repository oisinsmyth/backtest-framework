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

---

# 7. AMENDMENT, same day — **§2's HEADLINE IS RETRACTED. The test had no power, and it was measuring the bid-ask bounce**

**The principal rejected the finding on the ground that trending markets demonstrably exist, so the
detection must be wrong. That objection is correct and this section is the diagnosis.** Diagnostic
`working/d523_diagnose_why.py`, log `temp/d523_why.log`. Four candidate defects were tested; **all
four are real, and two of them are disqualifying.**

## 7.1 DEFECT ONE — a realistic trend is INVISIBLE at the horizons that were swept

Simulated, 20,000 blocks a cell: a session that moves X% with 5-minute σ of 0.05% has per-bar
drift `mu = X/84`. **Mean `z`, where 0.5 is no signal:**

| drift, as a daily move | H = 8 | H = 20 | H = 42 | H = 83 |
|---|---:|---:|---:|---:|
| 0.0% (pure noise) | 0.5010 | 0.4976 | 0.4992 | 0.4965 |
| **0.5%** | **0.5211** | 0.5420 | 0.5865 | 0.6564 |
| **1.0%** | **0.5651** | 0.6448 | 0.7575 | **0.8827** |
| 2.0% | 0.7075 | 0.8666 | 0.9676 | 0.9973 |
| 4.0% | 0.9213 | 0.9952 | 1.0000 | 1.0000|

**A genuine 1%-per-session trend moves the statistic by +0.064 at H = 8 and by +0.386 at H = 83.**
A drift accumulates ∝ H while noise accumulates ∝ √H, so detectability rises ∝ √H — and
**the swept ladder stopped at H = 20, in the regime where drift is swamped.**

**The cap was self-inflicted and unnecessary.** H ≤ 20 comes from needing a non-overlapping
past/future PAIR inside one session (`2H ≤ 84`) — which constrains **Stage 1**. Gate 0b needs a
single block and could have run at H = 42 or H = 83 all along. I carried Stage 1's constraint into
Stage 0 without noticing.

## 7.2 DEFECT TWO — the statistic demands MONOTONICITY, and real trends retrace

| path | net | path length | eff | `z` | reads as |
|---|---:|---:|---:|---:|---|
| straight line, 8 up | +8 | 8 | 1.000 | 0.995 | **TRENDING** |
| trend, 25% retrace `(+3,−1)×4` | +8 | 16 | 0.500 | 0.793 | ordinary |
| **trend, 50% retrace `(+2,−1)×4`** | **+4** | **12** | **0.333** | **0.607** | **ordinary** |
| one big leg then chop | +7 | 13 | 0.538 | 0.636 | ordinary |
| pure chop `(+1,−1)×4` | 0 | 8 | 0.000 | 0.135 | REVERTING |

**A path that nets +8 against a path length of 16 — a textbook trend — is scored "ordinary",**
because the sign shuffle can rearrange those same magnitudes into a straight line. And **D471
measured `adverse/|move| = 0.45–0.50 in every cell of every table`**: a winning move goes about
half its size against you first. That is precisely the 50%-retrace row, which reads 0.607.

**So the 95th-percentile-of-efficiency threshold selects for near-monotone paths, which is not what
a trend is.** D471's own conclusion — *use the variance ratio, efficiency fails as a conditioner* —
applies directly, and §1.2 of the pre-registration **declared the variance ratio as a secondary
label with an explicit tie-break rule. The Stage 0 runner never computed it.** That is a
pre-registered statistic left uncomputed, the same failure recorded against D506.

## 7.3 DEFECT THREE — the label is biased DOWNWARD by bid-ask bounce, by construction

With `r_t = r*_t + u_t − u_{t−1}` for bounce `u`, **the numerator telescopes** (`Σr` picks up only
`u_H − u_0`) while **the denominator accumulates** (`Σ|r|` gains a bounce term in every bar). The
sign shuffle is computed on the *observed* `|r|`, so **the null's spread is inflated by the same
bounce that is absent from the signal** — and `z` sits below 0.5 at every horizon on every root,
by an amount set by the half-spread over the per-bar σ.

**Measured, and it orders the roots:**

    Spearman( median |5-minute return| in TICKS , mean z ) = +0.5886 on 35 roots

    coarsest relative to its move        finest relative to its move
    ZT   2 ticks   z 0.3926              NQ  17 ticks   z 0.4956
    SR3  2 ticks   z 0.4062              RB  16 ticks   z 0.4886
    ZF   2 ticks   z 0.4594              HO  15 ticks   z 0.4895
    ZB   2 ticks   z 0.4637              RTY 11 ticks   z 0.4976

**This retracts §3.1.** I attributed ZT's and SR3's behaviour to *tie structure in the atom set*.
The mechanism is **bid-ask bounce**, it is quantitative, and it explains the whole cross-root
ordering rather than two outliers.

## 7.4 And therefore DEFECT FOUR — THE TEST HAD NO POWER, so its negative is not evidence

On the finest-tick roots, where the bounce is smallest, `z` sits at **0.4956 (NQ)** and **0.4976
(RTY)** against the pure-noise value of **0.5010**. The residual bias is −0.003 to −0.012. Against
that:

| if this share of sessions trends at 1% | pooled mean `z` would be |
|---|---:|
| 5% | 0.5042 |
| 10% | 0.5074 |
| 20% | 0.5138 |

**The bounce bias on NQ (−0.0054) is the same size as the signal from 8% of sessions trending at
1%.** The two are not separable at H = 8. So the measurement is consistent with *no trends* **and**
with *trends existing and being invisible at this horizon and this price series* — it cannot
distinguish them.

**A test that cannot distinguish the hypothesis from its negation has not tested it.** §2's
statement that "a five-minute futures path is straighter than a coin flip less often than a coin
flip is" describes **the close-price series including its bounce**, not the market. **Withdrawn as a
claim about market behaviour.**

## 7.5 What survives, and what the corrected design has to be

**SURVIVES.** The arithmetic, the 45 checks, the fixture, the exact enumeration, the `b0`
degeneracy at H = 3/4, and **§3's finding that a pooled split-half correlation at n = 84,722 is a
between-root artefact whose null is merely `1.645/√n`** — that is a methodological result and it is
unaffected.

**DOES NOT SURVIVE.** Any claim that these markets mean-revert intraday, and Gate 0b's verdict as a
statement about trends. **Gate 0b is void, not failed.**

**THE CORRECTED DESIGN, four changes, none cosmetic:**

1. **Change the statistic from monotonicity to DRIFT.** The variance ratio `Var(r_k)/(k·Var(r_1))`
   or a drift t-statistic `Σr / (σ√H)` — both of which score the 50%-retrace path as trending, and
   the variance ratio is what §1.2 already declared and D471 already recommended.
2. **Remove the bounce rather than conditioning on it.** The variance ratio can be corrected
   explicitly; failing that, sample the path on a coarser bar (the bounce is additive, so ψ/σ falls
   as √k) or read a mid-price. The 12-month `bbo-1m` and full-year `tbbo` on disk give a true mid.
3. **Extend the horizon to where drift beats noise** — the session and beyond. Non-overlapping
   pairs cap H at 42 for Stage 1, but the label's own properties have no such cap, and a
   multi-session clock would need the principal's ruling since "intraday" was his specification.
4. **Stop pooling 13 years and 35 roots.** Trends are regime-clustered (2020 crude, 2022 rates);
   a pooled mean over 84,776 sessions dilutes a minority state by construction.

**Nothing about this amendment closes or opens anything.** The oracle-label line is **neither
confirmed nor refuted** — it is untested, and the next record must test it with a statistic that
can see a trend. The 2024+ slice is still unread, which matters more now than before: **no holdout
has been spent on a question that was never asked properly.**
