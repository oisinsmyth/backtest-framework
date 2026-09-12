# D440 — C1's measured path through D386's lifecycle model: what a real path is worth against a Gaussian one

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. **No
holdout of any kind is read, and none exists to read** — §1. Equity extended-hours bars, the same
fixture D259 used.

## 1. What this is, and what it is NOT

**[D386](D386-the-prop-account-is-worth-its-buffer.md) values a Gaussian trader.**
`d386_full_lifecycle.simulate()` draws `inc = rng.normal(dmu, sd, size=(m, k))` and maximises `V`
over a grid of daily vols, which is what makes break-even Sharpe well-defined. **It answers what edge
is required. It has never been shown a measured path.**

**[D259](D259-the-extended-session-and-the-overnight-interior.md) measured one** — C1's
18:00→16:10 ET session-boundary hold, 12,985 holds, **median MAE 0.55%, p99 3.98% sitting exactly on
the 4% floor, worst 13.85%, and 2020's p99 at 7.05%.** Fat-tailed and regime-dependent.

**This study runs the second through the first.** Nothing else changes: same plans, same rules, same
fee schedule, same `V`.

**What it is NOT, stated before any result:**

- **NOT an admission test.** [R8](../RULES.md#r8) admission needs hurdles committed before the
  withheld data is touched. **D259 read the whole 2010–2026 window, so no honest holdout exists on
  this fixture.** The out-of-sample test is the futures re-run once acquisition lands, and it is a
  **separate** pre-registration.
- **NOT a new candidate, and NOT a reopening.** C1 is already open as a component. C2 and C3 stay
  closed.
- **NOT a change to hurdle P, to the venue choice, or to D386's terms.**
- **The vol target is swept, not chosen** — §2. D259's 0.4% was picked **after** seeing breach data
  and is therefore unusable as a pre-registered value; it appears below only as a prediction.

**The load-bearing claim being tested is the prop research's own:** *"every screen-4 verdict is a
σ-based lower bound on severity, not a measurement."* **If a Gaussian at matched vol reproduces `V`,
that claim is wrong and D386's table stands as written.**

## 2. The construction

**The inputs exist and are named, because one of them is not what it looks like.**

| | |
|---|---|
| **the fixture** | `data/fixtures/index_extended_15m_raw.csv.gz` — **958,217 bars, 16,748 symbol-sessions**, 04:00–19:45 ET back to 2010, with `.meta.json`, `_events.json` and 25 green tests |
| **the lifecycle model** | `scripts/d386_full_lifecycle.py`, **unedited** |
| **D259's 12,985 holds** | **DO NOT EXIST AS A COMMITTED ARTIFACT.** No `d259_*.py` and no `data/d259_*`. **The holds and their MAE must be RE-DERIVED from the fixture**, which makes §5's `[REP]` gate load-bearing rather than a formality |

```
PATHS    D259's 12,985 measured holds, RE-DERIVED from the fixture above, each carrying its
         INTRABAR path, in order.
         Primary: the historical sequence, rolling start at every hold, run to breach or 600 days.
         No distributional assumption anywhere in the primary.
SIZING   D259's rule -- k = target_vol / trailing_vol, trailing vol over the PRIOR 21 HOLDS only
         (R9), capped at 4x. The RULE is pre-specified; the TARGET is swept.
GRID     target_vol over D386's existing risk grid. V is reported at every point and the argmax
         is taken, exactly as D386 does -- so the multiplicity is paid in the same currency.
PLANS    MFFU Rapid EOD 50K (primary; D386's named vehicle) + Rapid EOD 25K, Rapid 50K/100K/150K.
         Unchanged from d386_full_lifecycle lines 248-271.
MONEY    every quantity in DOLLARS, because the MLL is a dollar limit ($2,000 on a 50K).
```

**`d386_full_lifecycle.py` is not edited.** The runner injects a path provider; the Gaussian provider
is retained as the control and **must reproduce D386's published cells bit-identically** — `[P1]`.

## 3. The controls, and what each destroys

| | what it destroys | what it preserves |
|---|---|---|
| **GAUSS** — D386's own draw at matched mean and matched daily vol | **the whole path shape** — tail, clustering, regime | mean, vol |
| **SHUF** — the measured holds shuffled independently | **serial structure and regime clustering** | the exact marginal distribution, including the tail |

**The two together separate a fat marginal tail from clustering in time**, which is the only way to
attribute a difference to either. **Every control draws from the same hold set as the treatment** —
asserted, not assumed.

## 4. Measured

**Per plan, per grid point:** `V` per evaluation purchased; `P(ever paid)`; mean and **median**
payouts per evaluation; `P(pass)`; expected life in sessions and years; breach rate; and the
**P4 verdict** at the `V`-maximising size.

**The four-group report on the primary cell**, per `CLAUDE.md`: performance net and gross with
exposure and maxDD; the trade distribution with **median** beside mean and the **1% two-tailed trim
reported all three ways**; what the winners depend on, **with the top contributing hold named and
its bars read**; and the nulls as **distributions — p50 and p95, with the p95's bootstrap SE, and a
margin inside 2 SE recorded UNRESOLVED** (D373).

**Era split, because D259 found the tail is regime-driven:** 2010–2019 / 2020 / 2021–2026, `V` and
breach rate in each.

**Block length:** the primary is the historical sequence and needs none. **Bootstrap SE uses the
stationary bootstrap with `b` chosen by the selector ON THE INFLUENCE SERIES OF `V`, not on
returns** — `V` is a path functional and `CLAUDE.md`'s inherited 20 is calibrated for the return
case. **`b ∈ {1, 20, 60, selector}` reported as sensitivity**, and if they disagree materially that
is a finding about the estimator and is reported as one.

## 5. Runner assertions — all three, plus two this study needs

1. **Lag audit** — re-derive the size series from the prior-21-hold vol in **a second implementation
   that never calls the sizing function**; assert identical. A sizing rule that peeks is this
   study's D279.
2. **Sign audit, in money** — assert a favourable hold pays **positively in dollars**; assert the
   trailing floor **ratchets on gains only and never on losses**; assert a breach is triggered by a
   **decline** in equity.
3. **Right-quantity** — assert the plan scored is **Rapid EOD and not Rapid intraday**. D386 puts
   them **$73 apart at the 50K**, so the two are distinguishable and a mix-up would be silent.
4. **`[P1]` reproduction, MODEL SIDE** — the Gaussian provider reproduces D386's published cells
   bit-identically before any measured path is run. **If it does not, the study stops.**
5. **`[REP]` reproduction, PATH SIDE — and this one is load-bearing, because the holds are not
   committed.** The re-derived holds must reproduce **D259's published numbers before any new
   quantity is computed**: **12,985 holds**, median MAE **0.55%**, p99 **3.98%**, worst **13.85%**,
   the era table (**2010–19 p99 3.48% / 2020 p99 7.05% / 2021–26 p99 3.90%**) and the static-1×
   breach rates (**2.07% ALL, 1.06%, 11.36%, 2.19%**). **Any mismatch is a reconstruction failure,
   not a finding, and the study stops.** This is D402's `[REP]` discipline applied to a record whose
   evidence was never committed as data.
6. **Control eligibility** — assert every `SHUF` draw comes from the observed hold set, and that
   `GAUSS` matches the measured mean and vol to within a stated tolerance.

**And the re-derived holds ARE committed this time**, to `data/`, with the reproduction table beside
them. **A file a record quotes is evidence; D259's were not, and that is why this study begins by
rebuilding them.**

**Each of the five is checked to RAISE on a deliberately broken input, and the break must hit the
SCALAR the assertion compares, not the name of the thing it reads.**

## 6. The bar — MFFU Rapid EOD 50K, at the `V`-maximising size

- **T1** `V` per evaluation purchased **> 0 by 2 SE** under the **measured** path.
- **T2** **P4 still clears** — expected life **> 3 years** — at that same size, not at a different
  one.
- **T3** `V` **> 0 by 2 SE in 2021–2026** taken alone, the era that is neither the calm decade nor
  the 2020 event.

**T1 ∧ T2 ∧ T3 makes C1 a valued candidate rather than a surviving one** — the first quantity in
this track that **orders** rather than gates, which is [D379](D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no-objective-function.md)'s
stated complaint. **It is not admission. §1.**

## 7. Predictions (MODERATE — the direction is near-certain, the magnitude is not)

- **X-a** `V` under the measured path is **BELOW** `V` under `GAUSS` at matched vol, at every grid
  point. **Direction is the claim; if it inverts, the σ-lower-bound reading is wrong and that is
  the finding.**
- **X-b** the shortfall at the primary cell is **25–60%** of the Gaussian `V`.
- **X-c** `SHUF` lands **between** `GAUSS` and the measured path — the fat marginal explains more of
  the gap than clustering does, but not all of it.
- **X-d** the `V`-maximising target vol lands **between 0.3% and 0.5%**, i.e. near both D259's 0.4%
  and D386's 0.4% best-risk cell for this plan. **Two routes to one number, and they were computed
  independently.**
- **X-e** the era split: **2020 supplies most of the `GAUSS`-to-measured gap**; 2021–2026's measured
  `V` is within 25% of its Gaussian.
- **X-f** breach rate under the measured path at matched size is **1.5–4×** the Gaussian's.
- **X-g** **T1 passes and T3 is the one at risk**, because 2021–2026 is 4,435 of 12,985 holds and
  the SE scales accordingly.

## 8. Speed

**Projected wall time before any launch, per `CLAUDE.md`.** The primary is 12,985 rolling starts ×
a grid × 5 plans, with no RNG in the treatment. **Build on `scripts/fast_null.py` and call
`assert_matches_scorer` once.** The path array is cached in `temp/`, keyed on the fixture **and** on
the mtime of every module that produces it. **If projected wall exceeds ~10 minutes: state the
number, do one optimisation pass, say what was done, and only then launch with
`run_in_background: true`.** `parallel_map`'s `[SPEED]` line must clear 70% or the work moves to
processes over `items[i::N]`. **One worker's RSS is printed before any fan-out.**

## 8a. What the fixture cannot see, inherited from D259 and not repaired here

**The 20:00–04:00 window is UNOBSERVED, not measured.** The fixture covers 04:00–19:45 ET, so any
excursion inside the untraded window is invisible and contributes **one observation per hold**.
**D259 quantified the cost of that**: only **3.72%** of 1× first-breaches occur in the untraded
window and the gap alone breaches on **0.10%** of holds — *"right in mechanism and small in
magnitude"* — **with three caveats that all make it a LOWER bound.**

**Every MAE in this study therefore understates the true excursion, and `V` is correspondingly an
upper bound.** That is the same direction as D386's own stated conservatism and it is stated here so
the two are not mistaken for independent margins. **The futures re-run is what removes it**, because
the instrument trades that window continuously.

**Also inherited:** half-days are kept in the fixture and excluded by the consumer (23 sessions), and
the fixture ships **raw prices plus a `suspect` flag** with no price modified.

## 9. Not in scope

No futures data. No holdout. No new candidate, no reopening of C2 or C3, no disposition. No change
to hurdle P, to the venue, to D386's terms or to D259's measured holds. **No claim about ES** — the
proxy covers 16 of 23 hours and the instrument question is a separate pre-registration, which is
**also a kill-check on this study's input**: if the overnight drift is a T+1 settlement artefact,
C1's path has no counterpart in the instrument that would be traded.
