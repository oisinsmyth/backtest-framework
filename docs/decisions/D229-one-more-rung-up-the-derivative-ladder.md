# D229 — One more rung up the derivative ladder

**Status:** Committed (P1–P5 all confirmed) — **the derivative ladder closes at I1**, and D218's headline fails the bootstrap leg it stated
**Date:** 2026-08-27
**Area:** Strategy research

---

## The question

D217 and D218 established one transferable result, twice, on constructions that share no
arithmetic: **trend acceleration beats trend level.** `I1 − I2 = +0.628` long-short and
`+0.529` long-flat on Impulse MACD, against D217's `R1 − R2 = +0.285` and `+0.209` on plain
MACD.

That is a statement about a **derivative ladder**:

| rung | series | measures |
|---|---|---|
| I2 | `md` | trend **level** |
| **I1** | `hist = md − sma(md, 9)` | trend **acceleration** — the current arm |
| **I0** | `Δhist = hist[t] − hist[t−1]` | **jerk** — proposed here |

**Does the ladder keep paying one rung further up?**

The hypothesis is not mined. It is the programme's own established mechanism, extended by one
step, and it was proposed from that mechanism rather than from any number.

---

## The rung

```
score[t] = hist[t] − hist[t−1]
position = 1 if score > 0 else 0        # long-flat; ties flat
```

Memoryless, exactly as `macd.positions` writes every other rung. **No threshold.**

The proposal that prompted this was *"enter when hist is at or close to zero and increasing,
exit when it decreases."* The "close to zero" clause is dropped deliberately: it introduces a
free parameter, and it encodes nothing new, because `hist` crossing upward through zero **is**
`Δhist > 0` in the neighbourhood of zero. A threshold would buy looks, not information. If the
clean form fails, a thresholded form is not a rescue — it is a second study.

### The tie policy, stated up front because it carries more weight here

`macd.positions` treats `score == 0.0` as flat. For a level rule that is a rounding-order
curiosity. For a **difference** rule it is a live case, and the measurement below shows how
live. It is a stated policy, not an accident of floating point, and it is not revisited after
seeing the result.

### Warm-up

`impulse_warm_up_bars() + 1`. The ladder start stays at the common **1,000 bars** so all rungs
cover the same span (D217's rule — different spans are not a comparison); the extra bar the
difference needs is already inside it.

---

## What is already known, and it is measurement, not prediction

Measured before this record and stated here so it cannot be re-sold as foresight. All of it is
**free under D228's boundary** — it describes the indicator and the position series, and
touches no return.

Pooled across 57 ETFs, 86,355 live bars:

| rule | exposure | turnover | vs parent |
|---|---:|---:|---:|
| I1 `sign(hist)` | 49.93% | 4,824 | 1.00× |
| **I0 `sign(Δhist)`** | **48.53%** | **16,422** | **3.40×** |

- `md == 0.0` (the dead zone) on **11.84%** of bars
- `hist == 0.0` exactly on **3.08%**
- `Δhist == 0.0` exactly on **3.10%** — one bar in 32 is a tie, and the tie policy decides it

**Three consequences, declared in advance:**

1. **A cost headwind of roughly −0.06 Sharpe.** ~2,733 sides/yr against the parent's ~803, at
   ~1.65 bp/side on a book equal-weighted across 57 names, is about **+56 bp/yr** of extra
   cost against a 7.23% CAGR at 8.8% vol. **I0 starts in a hole and has to climb out of it.**
2. **The dividend deficit is not fixed.** Exposure moves 49.93% → 48.53%, so D228's finding
   holds — the arm still collects ~half the yield, and hurdle D fails the same way unless the
   Sharpe gain is large. The "early stop" intuition does not reduce time in market here,
   because the rule also **enters earlier**.
3. **Ties are structural.** 3.10% of bars, concentrated in the dead zone, resolved flat.

---

## The statistic — and why this study can clear a bar D218 could not

D218's absolute floor was **+1.420** and its own record says nothing on this universe can
clear it. But D218's headline result was never tested against that floor. It was tested as a
**delta between nested rungs**, against `DELTA_HURDLE = 0.10`.

That is the right statistic and it is the reason this study is worth running: nested rungs
read the **same series on the same bars**, so almost all variance is common and the difference
is estimated far more precisely than either level. **The bar is lower because the statistic is
paired, not because a new record was opened.** Multiplicity is unchanged — the 45,803
inherited looks attach to the fixture either way.

### A defect inherited from D217 and D218, fixed here

Both records state hurdle A as *"≥ +0.10 Sharpe … **above the paired bootstrap's p95**"*, and
D217 names `trade_bootstrap` as its source. Two problems:

1. **Neither runner ever called it.** `ladder_deltas` compares the point estimate to `+0.10`
   and stops. Grep confirms no bootstrap call in `run_macd_ladder.py` or
   `run_impulse_macd.py`. **The bootstrap leg of hurdle A was never computed in either study.**
2. `breakout_nulls.trade_bootstrap` is a **single-arm terminal-wealth** bootstrap over closed
   trades. It is not paired and could not have supplied that leg.

The phrasing is also unachievable as literally written: a bootstrap of the observed data
centres on the observed delta, so requiring the delta to exceed *its own* p95 is impossible by
construction.

**Made precise here, in the strict direction:** a **paired block bootstrap over the live bar
index**, block length 21 (`block_shuffle_null`'s default, repo precedent), 1,000 sims, seed 0.
Each replication resamples blocks of **dates** and recomputes **both rungs on the identical
resampled dates** — that is what makes it paired — then takes the delta.

> **Hurdle A: the p05 of the bootstrapped `I0 − I1` distribution must exceed +0.10.**

A one-sided 95% lower confidence bound above the hurdle. This is **stricter** than what D218
applied to itself, and that is deliberate: a point estimate above +0.10 with a p05 well below
it is not a result.

---

## Hurdles

- **A (carries the verdict).** `I0 − I1 ≥ +0.10` **and** bootstrap p05 `> +0.10`, at the
  primary cell.
- **D.** Beat buy-and-hold on **excess Sharpe at `rf = 4%`, charged on the exposed fraction**
  (D228's correction), *and* on dividend-adjusted total return. Expected to fail the second
  leg; reported anyway, both legs, both bases.
- **E.** ≥100 pooled signals and ≥30 entries per ETF.
- **Gross and net reported separately**, so the cost headwind is visible rather than
  entangled with the signal.

**Primary cell: `I0 / long_flat / gate = none`** — the same cell D218 named. The other three
(`long_short` × `{none, 200ma}`) are run and reported but are not the verdict.

---

## Predictions

Committed before any runner exists. The turnover, exposure and dead-zone figures above are
**measurements** and are deliberately not listed here.

| | prediction | confidence |
|---|---|---|
| **P1** | **`I0 − I1 < 0` at the primary cell** — jerk does *not* beat acceleration. Differencing an already-differenced smoothed series amplifies noise | **moderate-high** |
| **P2** | The **gross** delta is more favourable than the net by **0.04–0.09 Sharpe**, bracketing the declared −0.06 headwind | **moderate-high** |
| **P3** | I0 still **loses to buy-and-hold on dividend-adjusted money**, because exposure barely moved | **high** |
| **P4** | The bootstrap **p05 sits ≥0.15 below the point estimate**, i.e. these deltas are far less precisely estimated than D218's point-estimate-only hurdle implied | **moderate-high** |
| **P5** | **I0 beats I2** (`level`) even while losing to I1 — the ladder is not monotone but both derivative rungs beat the level rung | **moderate** |

P1 is the prediction that would hurt to be wrong about in the pleasant direction: if jerk
beats acceleration, the mechanism D217/D218 identified is stronger than either study claimed,
and P5 becomes the more interesting result.

---

## The stop

**If hurdle A fails, the derivative ladder closes at I1.** No thresholded variant, no smoothed
`Δhist`, no second signal length. The arm remains `sign(hist)` and the next question is
unmined data, not another rung.

**If hurdle A clears, it is not a result either.** It becomes a hypothesis with a mechanism
already written, and it goes to ETFs outside these 57 alongside whatever survives D228.

---

## Ledger

| count | N |
|---|---:|
| fresh — I0 × 2 books × 2 gates | **4** |
| + D218's inherited | **66** |
| + disclosed ETF prior | **45,807** |

The absolute floor at the verdict count is **expected to fail and is not the verdict** — the
paired delta is. Both are reported, and the reason the delta is the primary is stated above
rather than discovered afterwards.

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| the ladder, books, gates, costs, scoring | `arm_positions`, `score_arm`, `buy_and_hold`, `portfolio_log_returns`, `sharpe_of` | `run_macd_ladder.py` |
| the Impulse series and rungs | `impulse_macd_series`, `impulse_signal_score`, `impulse_band_score`, `positions` | `research/macd.py` |
| block length precedent | `block_shuffle_null` (block = 21) | `run_macd_ladder.py` |
| deflated Sharpe | `expected_max_sharpe` | `validation/dsr.py` |

**Written fresh:** the `I0` score (`hist[t] − hist[t−1]`, NaN-safe at the first live bar) and
the **paired block bootstrap**, which does not exist in the repo — established above, not
assumed.

---

## RESULT

*Appended after the run. Nothing above this line was edited except the Status field.*

**Produced:** 2026-08-27 · **Reproduce:** `uv run python scripts/run_jerk_rung.py`
(offline, deterministic, seed 0, **6.8 s**) · Page:
[`JERK_RUNG_RESULTS.md`](../../JERK_RUNG_RESULTS.md) · Artifact: `data/jerk_rung_summary.json`

### The one-sentence version

**Jerk does not beat acceleration — `I0 − I1 = −0.218`, failing hurdle A in all four cells —
but building the bootstrap leg that D217 and D218 stated and never ran shows that D218's own
headline result fails it too, in all four cells, with a 90% interval spanning zero.**

### The three rungs, long-flat, no gate

| rung | Sharpe (price) | gross | excess @rf=4% | money | CAGR | max DD | exposure | turnover |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **I0 jerk** | +0.439 | +0.542 | **+0.335** | +34.94% | 5.11% | −13.01% | 48.5% | **16,421** |
| I1 acceleration | **+0.658** | +0.689 | **+0.570** | +52.12% | 7.23% | −11.78% | 49.9% | 4,835 |
| I2 level | +0.129 | +0.139 | +0.011 | +14.34% | 2.25% | −13.40% | 54.6% | 1,458 |
| buy and hold | +0.333 | — | +0.235 | +62.59% | 8.42% | −34.81% | 100% | — |

The pre-registration's free measurements land exactly: exposure **48.5%** against the 48.53%
measured in advance, turnover **16,421** against 16,422. Measuring the position series before
committing to predictions worked.

### Hurdle A — all four cells fail

| book | gate | I0−I1 | gross | excess | boot p05 | boot p95 | A |
|---|---|---:|---:|---:|---:|---:|:--:|
| long_flat | **none** | **−0.218** | −0.147 | −0.235 | −0.759 | +0.402 | **FAIL** |
| long_flat | 200ma | +0.006 | — | — | −0.554 | — | **FAIL** |
| long_short | none | −0.224 | −0.099 | −0.251 | −1.031 | +0.621 | **FAIL** |
| long_short | 200ma | −0.152 | — | — | −0.712 | — | **FAIL** |

**The basis for hurdle A is price-only, rf = 0** — chosen at implementation time, before the
run, because that is the basis D217's `+0.285` and D218's `+0.529 / +0.628` were computed on
and a ladder delta that is not comparable with the ladder it extends is not worth having. The
gross and excess-Sharpe deltas are reported beside it and agree on sign everywhere.

### Scoring the predictions

| | prediction | outcome |
|---|---|---|
| **P1** | `I0 − I1 < 0` at the primary cell | **CONFIRMED.** −0.218 |
| **P2** | Gross more favourable than net by 0.04–0.09 | **CONFIRMED.** −0.147 against −0.218, a gap of **0.071**, inside the declared range and bracketing the −0.06 cost headwind stated before the run |
| **P3** | I0 still loses to buy-and-hold on dividend money | **CONFIRMED.** +34.94% against +62.59% |
| **P4** | Bootstrap p05 sits ≥0.15 below the point estimate | **CONFIRMED, by 3.6×.** p05 is **0.540** below. These deltas are far less precisely estimated than D218's point-estimate-only hurdle implied |
| **P5** | I0 beats I2 even while losing to I1 | **CONFIRMED.** `I0 − I2 = +0.310`, `I1 − I2 = +0.529`. **Both derivative rungs beat the level rung; the ladder is not monotone** |

**Five of five.** Worth saying plainly: a clean sweep in a study that predicted its own failure
is the *easy* case. P1 and P3 were near-arithmetic given the pre-registration's measurements,
and predicting a negative correctly is cheap. P4 is the only one that carried information.

### The finding that outlives this study

P4 is not a footnote about precision. Applying the same correctly-specified test to **D218's
own headline** — the `I1 − I2` delta that this entire line of work rests on:

| book | gate | I1−I2 | boot p05 | clears the hurdle D218 wrote |
|---|---|---:|---:|:--:|
| long_flat | none | **+0.529** | −0.055 | **FAIL** |
| long_flat | 200ma | +0.096 | −0.322 | **FAIL** |
| long_short | none | **+0.628** | −0.133 | **FAIL** |
| long_short | 200ma | +0.366 | −0.076 | **FAIL** |

**D218's headline result fails the bootstrap leg D218 itself specified, in all four cells.**
The `+0.628` has a 90% interval of **−0.133 to +1.325** — it contains zero. Both parent studies
reported hurdle A as cleared while computing only its point-estimate half.

**Stated fairly, because this is the strongest claim in the record and it should not be
overstated:**

- A 90% interval containing zero means *not significant at the one-sided 5% level*. It does
  **not** mean the effect is zero, and **+0.529 remains the best point estimate.**
- D218's other argument is untouched by this. *"Two trend-acceleration rules built from
  unrelated arithmetic agree with each other"* — D217's `+0.285` and D218's `+0.628`, with
  `I1 − C ≈ 0` — is **independent evidence that a single-fixture bootstrap cannot see.**
  Replication across constructions and precision on one sample are different things.
- What is *not* defensible is the reported certainty. **The acceleration-beats-level result is
  a plausible point estimate on a wide interval, not the settled finding two records describe.**

The rule that follows: **a hurdle that names a test is not cleared until the test is run.**
Both parent runners omitted it and both records read as though it had passed.

### The primary cell against the other hurdles

**E clears** — 8,230 entries, minimum **125** per symbol, comfortably above 30. Tripling the
turnover buys sample size, which is the one thing it does buy.

**D fails, and in the now-familiar shape.** I0's excess Sharpe of **+0.335** *beats*
buy-and-hold's +0.235 — it clears the Sharpe leg — and it loses on money, +34.94% against
+62.59%. D228's mechanism again: exposure 48.5%, so roughly half the yield.

### Defects and disclosures

1. **The `I1 − I2` bootstrap was added after the run.** Defensible on the same grounds D218
   used for adding hurdle G post hoc: it can only make a **parent** study look worse and cannot
   launder D229's own failure. It spends no new looks — I1 and I2 are D218's cells, already in
   the ledger — and D229 is the record that discovered the missing leg, so reporting what the
   leg says is an obligation rather than an option.
2. **Hurdle A's basis was not pinned by the pre-registration.** Price-only rf = 0 was chosen at
   implementation time for comparability with D217/D218, with gross and excess reported beside.
   The choice does not change the verdict — all three bases agree on sign in every cell.
3. **An idempotency defect was found and fixed before the artifact was committed.**
   `json.dumps(sort_keys=True)` reorders the deltas dict on the round trip, so `--report-only`
   emitted the same content in a different row order. Third appearance of this defect after
   D220 and D222; now pinned by an explicit `CELL_ORDER` rather than dict iteration.
4. **D218's committed runner was not edited.** Four lines of rung dispatch are duplicated
   rather than patching `run_impulse_macd.arm_positions`, because adding a rung to a committed
   study's code after it reported is how a record stops describing what was run. Pinned by test.

### Ledger

| count | N | floor |
|---|---:|---:|
| fresh | 4 | +0.365 |
| + D218's inherited | 66 | — |
| + disclosed ETF prior | **45,807** | **+1.465** |

Not the verdict, as declared in advance — the paired delta is, and it fails on its own terms
without needing the floor.

### What this changes

**The pre-registered stop applies: the derivative ladder closes at I1.** No thresholded
variant, no smoothed `Δhist`, no second signal length. Differencing an already-differenced
smoothed series triples turnover, costs ~0.07 Sharpe in fees alone, and gives back 0.22.

**Two things survive, and the second is the larger.**

**The arm is unchanged and still the only live candidate** — `sign(hist)`, +0.570 excess Sharpe
against buy-and-hold's +0.235, untested on unmined data.

**And the programme now knows its central result is far less precise than it reported.** Every
ladder delta in D217 and D218 was a point estimate presented as though a bootstrap had endorsed
it. The bootstrap now exists. **It should be run against every delta this programme has
reported before any of them is carried further.**

---

## ADDENDUM — the claim above that D230 corrected

The RESULT above states that D218's cross-construction argument is *"untouched by this"*, and
names `I1 − C ≈ 0` as part of the evidence it leaves standing. **[D230](D230-the-bootstrap-sweep.md)
swept all twenty-four deltas and that statement was too generous, in two ways.**

1. **The `I1 − C ≈ 0` leg is not untouched — it is what the sweep dissolves.** Its four
   intervals span roughly ±0.3 around point estimates of −0.096 to +0.008. *"The two
   accelerations are the same measurement"* is not supported by the data used to make it. A
   near-zero estimate on an interval that wide is evidence of nothing, not evidence of absence.
2. **"Independent" overstates it.** D217 runs from bar 393 and D218 from bar 1,000 on the
   **same 57 ETFs** — D218's span is a subset of D217's. Two estimators on heavily overlapping
   data are correlated.

**What survives, at its real strength:** two structurally different trend estimators produced
same-signed positive deltas on overlapping data. That is corroboration, not independent
replication.

The rest of the RESULT stands. This addendum exists so the section above is not read as sound
on its own.
