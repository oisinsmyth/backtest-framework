# D289 — The promotion pipeline: what each stage must prove

**Status:** STANDARD. Not a study; it scores no cell and tests no hypothesis.
It defines the requirements every future candidate is held to.
**Date:** 2026-09-02
**Area:** Method · applies to **both tracks**

---

## The flow, as the principal specified it

> signal hunt → sharpen the signal with stop-loss and take-profit types → turn the
> signal into a strategy → test the strategy as 100% of a book → add to
> `BOOK.md` as another arm if correlation is low

**This is the HAPPY PATH — the route when things go well — not a licence to keep
working on a candidate that failed.** That distinction is the whole reason this
record exists: written down, the flow is a promotion ladder; left implicit, it
becomes a reason never to stop.

## The question it raises

Does having stages 2–5 *weaken* what stage 1 has to prove? If a stop can be added
later, does the raw signal need to clear as much now?

**Answer: it relaxes exactly one requirement and tightens two. Net, the bar on
the initial signal goes UP.**

---

## What it legitimately relaxes: SUFFICIENCY becomes EXISTENCE

Stage 1 no longer has to produce a *tradeable* signal, only a **real** one.
Magnitude-versus-cost is a later problem, so the stage-1 test is that the effect
is **there**, not that it is **enough**.

This is not a technicality. D288 killed `close_in_range` on a **magnitude** floor
(+90.6 bp against a null median of +129.0) while its **evidence** stood at
**1.70× the null's single largest draw** (t +15.88 against a null max of +9.34).
Under this pipeline that profile is a stage-1 pass, and D288's spread floor was
the wrong instrument for an existence test.

**D288 is not reopened by that observation.** Its gate was pre-registered and it
failed; reinterpreting a failed gate because a pipeline exists is precisely the
move the design forbids. The correction is prospective: **future stage-1 gates
are t-based, declared as such in advance.**

## What it tightens, and why the net is stricter

### 1. Multiplicity compounds MULTIPLICATIVELY across stages

A four-stage pipeline with five choices per stage is `5^4 = 625` looks before a
single stop is chosen. Worse, a stage-1 selection made on the same fixture as
stages 2–3 **contaminates everything downstream** — the floor that matters at the
end prices the whole tree, not the last branch. D277 died at 300 cells; D288 at
31 with a floor its best candidate could not reach.

### 2. Stops and take-profits CANNOT create edge, and this repo has measured it

A stop or a target is a **nonlinear transform of the return distribution**. It
changes shape, and it moves the mean only through (a) cost — fewer bars held, or
more round trips — or (b) genuine path-dependence in the signal. (b) is real but
it is a **separate hypothesis needing its own evidence**, not a free parameter.

Three measurements here, none of them favourable:

- **D286** — the exit rule carried **no information**, and `disp`, the rule nobody
  designed, beat all three deliberate alternatives.
- **D285** — the cap genuinely **cut losers** (touched trades ended **−860 bp**,
  only **23.2%** profitable). That is the *favourable* case for a stop, and it
  still produced no viable book.
- **CLAUDE.md**, earned rather than assumed: *"Cost-cutting ≠ edge-sharpening"* —
  and the exit that worked fired on **displacement by unrelated names**, not on
  its own signal reverting.

**The empirical prior on stage-2 uplift in this programme is therefore ~1.0×
— nothing.** Stage 2 is expected to supply *margin*, never *rescue*. A signal
failing cost by a factor of two at stage 1 will not be saved at stage 2, and any
study assuming otherwise is arguing against every measurement taken here.

---

## The stages, and the gate at each

### Stage 1 — the signal exists

| | gate |
|---|---|
| **1a** | **t-based best-of-N floor**, not a spread floor. One shared offset vector (D228). **Both legs reported separately, always** — D286's `hist_L` had both legs positive, which is not a short |
| **1b** | **mechanism and numeric shape declared BEFORE the run**, with a falsifier that can fire even when the number is good (D288's gate B, kept unchanged) |
| **1c** | **mean move per trade ≥ 1.0× the round trip**, with the cost **MEASURED** — Corwin–Schultz on the names actually HELD, not a fee assumption. D285 guessed 15 bp/side and the held names measured **33.81** |
| **1d** | **correlation to every existing book arm < 0.50**, at signal level |

**1c is the relaxation, stated numerically.** D288 required clearing a
best-of-N *magnitude* floor. This requires only clearing *cost*, because stage 2
is allowed to supply the margin — but only 1.0×, not 0.5×, because the measured
uplift from stage-2 work here is nil.

**1d is moved EARLY, and that is a change.** The principal's flow checks
correlation at the end. It is nearly free to compute at stage 1, and finding at
stage 5 that a candidate is 0.9 with S1 means four stages and possibly a holdout
read were spent to learn something available on day one.

### Stage 2 — sharpen

| | gate |
|---|---|
| **2a** | **say which moved: edge per unit exposure, or cost per trade.** A longer hold lifts breakeven by amortising one round trip while per-bar edge usually falls, so "Sharpe rose" is not an answer |
| **2b** | beat the **undesigned exit** (hold to the pre-declared horizon) **and** a **random exit with matched holding period**. D286 is the precedent: the undesigned rule won |
| **2c** | **≥ 1.5× the round trip**, measured as in 1c |
| **2d** | **report what the exit KEYS ON.** D285's fired on displacement by unrelated names. An exit that does not respond to its own signal reverting is a turnover rule wearing a risk rule's name |

### Stage 3 — the strategy

Full hurdle set under [R6](../RULES.md#r6); overlay nulls under
[R7](../RULES.md#r7) reporting **p50 and p95 beside the score**, not the
percentile alone; concurrency under [R10](../RULES.md#r10); and **all four
reporting groups** from `CLAUDE.md` — performance net AND gross, trade
distribution with the median and the mean after dropping the best 1%, what the
winners depend on, and the null distribution.

### Stage 4 — 100% of a book, out of sample

**One read of the holdout, pre-registered, [R8](../RULES.md#r8).** A pass is still
not an admission; it is one out-of-sample result carrying its own falsifiers.

**This is where the principal's flow is BETTER than D288's plan and it is adopted
deliberately.** D288 would have spent the holdout on a bare signal straight out
of the mine, before any strategy work. The holdout is the scarcest asset in the
programme — one clean read — and spending it on something that was always going
to need stages 2–3 is the worse trade. **The holdout is spent at stage 4 or not
at all.**

### Stage 5 — admission as a book arm

| | gate |
|---|---|
| **5a** | **a standalone IR that stands on its own.** Low correlation is **necessary and nowhere near sufficient** — a zero-edge strategy is uncorrelated with everything, and "it diversifies" is not an edge |
| **5b** | correlation re-measured at **strategy** level, not signal level |
| **5c** | prop track additionally clears **hurdle P** ([R11](../RULES.md#r11)), all six |

---

## What is required before stage 1 runs

**The whole tree is pre-registered, once, up front** — the stop family, the target
family, the strategy construction, the promotion rule and the stop conditions.
Registered stage by stage as results arrive, the pipeline becomes a licence to
keep trying things on a candidate that already failed, which is D277 with more
steps. This is [R14](../RULES.md#r14).

## Stop conditions, per stage

- **Stage 1 fails** → the signal is closed. No re-cut of axes, no thirty-second
  candidate.
- **Stage 2 fails** → the signal is closed. It does not go back to stage 1 for a
  different N or horizon; that is the same search wearing a new label.
- **Stage 3 fails** → closed, and the record states which hurdle and by how much.
- **Stage 4 fails** → closed, and **the holdout is spent.** A second candidate
  needs a second holdout, built by the same construction from the unfetched
  remainder of the pinned permutation (5,201 eligible names remain).
- **Stage 5 fails on 5a** → not a book arm, whatever its correlation.

## Ledger

**Looks multiply across stages and are carried under
[R13](../RULES.md#r13).** A candidate arriving at stage 3 carries stage 1's and
stage 2's looks, because both shaped which candidate arrived.

**Disclosed now:** the post-closure probes at `data/d288_postclosure_probes.json`
spent looks on the mining fixture *after* D288 closed, exploring overlays and
confluence on `close_in_range`. Any successor testing those constructions
**carries them**, on top of D288's 177.

---

## What this record does NOT do

It does not reopen D288, promote `close_in_range`, or authorise a holdout read.
D288 is closed with zero survivors and **the holdout remains unspent** — which is
the asset this whole pipeline exists to protect.

---

# AMENDMENT, 2026-09-02 — both "tightenings" above are wrong

The principal rejected both, and was right both times. The original text is left
standing because it has been quoted and the error is worth seeing.

## 1. Multiplicity does NOT compound across stages

**What the record said:** looks multiply, `5^4 = 625`, and a stage-1 selection
contaminates everything downstream.

**Why that is wrong:** selecting on data that is already burnt does not invalidate
a later test on data never touched. **The mining fixture does not become more
spent.** 625 in-sample combinations followed by ONE holdout test is still one test
at its stated level.

A wider search costs the **prior**, not the p-value — the survivor is likelier to
be noise, so a holdout read is likelier to be wasted. That is an economic cost on
a scarce resource, and the record stated it as a statistical invalidity.

**What survives — and it is the useful distinction:** in-sample numbers are **free
for selection and expensive as evidence.** Stages 1–3 are selection; only stage 4
is evidence. That makes an in-sample floor a **triage device** — *is this worth
one of my scarce holdout reads?* — not a verdict on whether the effect is real.

**This reframes D288's own closure.** Gate A read as a verdict on
`close_in_range`. It was a triage decision: *not worth a holdout read by that
criterion*. The signal is not thereby shown to be absent, and its t of +15.88
against a null max of +9.34 still stands as what it always was.

**The ledger counts HOLDOUT READS, not in-sample looks.** In-sample looks stay
disclosed — what shaped a search is worth knowing — but as bookkeeping, not a bar.
The 308 post-closure looks in D288's addendum are therefore disclosure, not a
floor anything must clear. Multiplicity compounds in exactly one place: iterating
*through* the holdout, which [R8](../RULES.md#r8) already governs.

## 2. Exits are not barred from creating edge — they are COUPLED to re-entry

**What the record said:** exits cannot create edge; the empirical uplift here is
~1.0×; stage 2 supplies margin, never rescue.

**Why that is wrong:** it cited D285's cap **cutting losers** — touched trades
ending −860 bp, only 23.2% profitable — as evidence against exits. That is a
measurement of an exit **working**. The inference does not follow from its own
citation.

**The correct reading:** the exit improved per-trade quality, and the money was
lost because **exiting forced re-entry into a weak signal** — earlier exit → more
noise → re-enter → repeat. That is a failure of the **entry** rule the exit handed
control back to.

**The real constraint is coupling, not prohibition. An exit cannot be evaluated at
trade level.** A stop that improves the average trade and hands the freed slot to
a coin flip is a book-level loss wearing a trade-level win. This is precisely why
D286's `disp` beat all three designed exits: it exited on **displacement**, so the
freed slot always went to a *better-ranked* name instead of back to the same weak
signal.

### Stage 2's gate, restated

| | gate |
|---|---|
| **2a** | report the exit's effect on **per-trade quality** AND on **the book including whatever re-enters**, and say which moved. An exit that improves trades while the book worsens has located a **re-entry** problem — a finding about the entry rule, not the exit |
| **2b** | beat the **undesigned exit** (hold to the pre-declared horizon) and a **random exit with matched holding period** — D286's precedent, where the undesigned rule won |
| **2c** | ≥ 1.5× the round trip, cost **measured** on held names |
| **2d** | report **what the exit keys on** — its own signal reverting, or displacement by unrelated names |

### And the stage-1 magnitude gate loosens with it

Gate **1c** was set at ≥ 1.0× the round trip on the reasoning that stage-2 uplift
is ~1.0×. That reasoning is withdrawn. Stage 2 can genuinely improve per-trade
quality, so **1c is not a hard floor** — it is reported, and a candidate below it
must state what stage-2 work is expected to close the gap and how that will be
measured on the book rather than on trades.

---

# SECOND AMENDMENT, 2026-09-02 — stage 1 gains a CAPTURABILITY gate

D290 ran stage 1 under this ladder and found that its own ranking statistic was
not sufficient. The correction is prospective and binding on every future stage 1.

## What went wrong

D290 ranked on **name-split cross-validation**, declared here as "the honest
column". It is honest about one thing and blind to another:

> **An entry artifact generalises across names perfectly well.**

`lower_wick` posted **CV +6.19** on the short book — second overall — on an
effect that keeps **−11%** of itself after one skipped bar and **+1%** when
entered at the next open. CV asks *does this hold on names I have not seen*. It
never asks *is any of this real*, and nothing else in stage 1 asked either.

Fifteen of D290's 51 collapsed on a test that was not in the pre-registration.

## GATE 1e — CAPTURABILITY. New, and binding

**A candidate must survive being entered one bar late.** Signal from close[t−1]
as before, but **enter at open[t]** rather than at the close that generated it.

| | threshold |
|---|---|
| **open-entry `t` ≥ 2.0** | there is evidence for an effect you could actually enter |
| **retention ≥ 50%** | the edge is not merely the print you traded on |

**Why open-entry and not skip-a-bar.** Skipping a whole bar removes an entry
artifact **and** a genuinely fast signal at the same time, so "the edge dies at
skip 1" is consistent with both. Open entry removes only the print, keeping the
information one bar old and unexploited. The skip test stays as a **reported
diagnostic**; it is not the gate.

## Two diagnostics that must be REPORTED with every stage-1 candidate

**The overnight / intraday split.** Assert that the two segments compose to the
price return (D290 measured 4.44e-16 across 4,135,181 cells) and report the share
earned between the close and the next open. A candidate earning ~100% overnight
is telling you where its edge lives, and it is the segment you cannot trade into.

**Liquidity-tercile scaling — and it is the only cut that identifies bid–ask
bounce specifically.** Bounce magnitude is proportional to the spread;
information is not. Split the universe by each name's own trailing
Corwin–Schultz half-spread, rebuild the book inside each tercile, and report
whether the edge scales like the spread does.

**This is how D290 corrected an over-confident claim of mine.** I labelled the
axis-B k=1 effects bid–ask bounce. Across terciles with a **5.2×** spread gap
they scale **1.2× / 2.0× / 0.8×** — nothing like bounce — while the *volume*
signals scale **3.0× / 3.1× / 4.2×**, which is. Without this cut the wrong
mechanism goes into the record.

**Note the degenerate bucket.** Corwin–Schultz clamps negative estimates to zero
by the authors' convention, so the tight tercile averages 0.3 bp/side and the
wide/tight ratio is unusable. Use **wide/mid**.

## Stage 1's gates, restated in full

| | gate |
|---|---|
| **1a** | t-based best-of-N floor. Both legs reported separately |
| **1b** | mechanism and numeric shape declared before the run, with a falsifier |
| **1c** | mean move vs the **measured** round trip — reported, not binding |
| **1d** | correlation to existing book arms |
| **1e** | **CAPTURABILITY — open-entry `t` ≥ 2 and retention ≥ 50%** |
| **1f** | **name-split CV > 0** — necessary, and now explicitly **not sufficient** |

**1e and 1f together, never 1f alone.** That pairing is the whole content of this
amendment.

---

# THIRD AMENDMENT, 2026-09-02 — turnover and holding run become reported

D290 ranked `price_log` first on the spread construction: tier 1, open-entry
t +4.48, 93% retained, and **1.96× its measured cost** — the only tier-1
candidate to clear cost on evidence. Measured afterwards:

| | turnover / bar | mean holding run | dead names LONG | dead names SHORT |
|---|--:|--:|--:|--:|
| **price_log** | **1.9%** | **51 bars** | **33.5%** | **10.7%** |
| close_in_range | 91.3% | 1 | 22.3% | 20.7% |
| rsi | 25.9% | 4 | 22.8% | 20.1% |

**`price_log` is not a signal. It is a static characteristic tilt.** A share price
barely moves day to day, so the bottom-fifty-by-price is nearly the same fifty
names for months. It never says *when* to do anything — it holds a near-permanent
book of cheap against expensive, which is the low-price premium, a documented
risk premium rather than an edge.

**And its cost ratio was flattered by exactly that.** 1.96× is one round trip
amortised over a 40-bar hold on a book that scarcely changes. The number that
made it rank best is partly an artifact of it not being a signal.

**Worse, the risk is one-sided.** 33.5% of the long leg is dead names against
10.7% of the short. On a 35.7%-dead fixture, "buy the cheapest fifty" is buying
the pre-bankruptcy tail, and nothing in D290 priced that.

## GATE 1g — turnover and holding run, REPORTED with every candidate

| | |
|---|---|
| **turnover per bar** | fraction of the held set that changes |
| **mean holding run** | bars a name stays in the book |
| **dead-name share, PER LEG** | asymmetry is the thing to look for |

**Reported, not thresholded.** A slow signal is not disqualified — `macd_hist`
turns 14.6% and holds 7 bars and is perfectly legitimate. What the gate prevents
is a **static characteristic presenting itself as a signal**, and a cost ratio
being read as good when it is really the product of inactivity.

**A cost ratio must be read beside turnover, never alone.** Cost per unit time is
`round trip × turnover`, and a book that never trades has a flattering ratio and
no timing content.

## And a null-design note this exposed

**Rotation is a WEAK null for a near-static score.** Rotating a symbol's score
through time barely changes a score that is almost constant per symbol, so the
rotated book resembles the real one and the z is inflated. `price_log`'s rotation
z of +3.64 is doing less work than the same number would for a fast signal; its
permutation z of +3.94 is the one carrying weight, because that shuffles *which
name* holds which price. **When turnover is under ~5% per bar, read the
permutation null first.**

---

# FOURTH AMENDMENT, 2026-09-02 — a score is a RANKING, and its direction is a choice

The book is hard-coded: `order[:N]` goes long, `order[cnt−N:cnt]` goes short,
every candidate, every N, every bar. **Nothing in D290 ever asked a score which
way round it should go.** The principal caught that the direction is therefore
imposed by the construction, not carried by the signal.

**Seven of D290's 51 came out NEGATIVE on the spread** — `range_frac` −140.3 bp,
`upper_wick` −17.2 (t −2.20), `wick_asym` −18.2 (t −1.79). Read the other way
round those are positive results, and D290 scored one direction and priced
neither.

## GATE 1h — both directions, DECLARED then DISCLOSED

**1b is extended: the mechanism must state WHICH END GOES LONG, before the run.**
That is the guard against sign-shopping. A direction chosen after seeing the sign
is a free parameter, and there is no floor that prices it.

**Then both directions are reported, and the ledger counts both.**

| | |
|---|---|
| **the point estimate is algebraically FREE** | `spread(−s) = −spread(s)` exactly. Ranking on the negated score reverses the order, so the legs simply swap. No re-sort, no re-run |
| **the NULL is not free** | `max(−t) ≠ −max(t)`. The best-of-grid statistic is asymmetric, so the reversed direction needs its own null max from the same draws |
| **the ledger doubles** | 2 × candidates, disclosed. Under D289's amended convention this is bookkeeping, not a bar — but an undisclosed direction flip is exactly the post-hoc selection the design exists to refuse |

**A result in the direction the mechanism did NOT predict is reported as
direction-inverted**, and that is a strike against the mechanism even when the
number is good — the same logic as D288's gate B, where a right number in the
wrong shape falsifies.

## Two consequences of "it is a ranking" that also need stating

**Monotone transforms are the SAME candidate.** `price_log` and raw price produce
an identical ordering, so they are one signal with two names. Any candidate list
must be deduplicated by ordering, not by formula — a rank book discards units,
zero point and shape, and keeps only the order.

**A rank book cannot say "nothing qualifies today".** It holds exactly N names
whether they are extreme or ordinary — on a quiet day the ten most ordinary, in a
crash the ten most extreme. **Level- or threshold-based selection is therefore
untested by this whole design**, and is a different construction requiring its own
pre-registration. The N sweep from 3 to 50 is the only crude proxy the study has
for "how extreme must a name be before it is worth holding".

---

# FIFTH AMENDMENT, 2026-09-02 — a peak at the edge of the sweep is not a result

Measured across D290's 51 candidates, by where each one's peak (N, k) sits:

| construction | corner (N=50, k=40) | edge | interior |
|---|---|---|---|
| **long-only** | **51 of 51**, 1 passes the nulls | — | — |
| **short-only** | — | **0 of 6 pass** | 19 of 45 pass |
| **spread** | 1 of 1 | 7 of 13 | 16 of 37 |

**Every long-only candidate peaks at the corner and essentially none survives.**
That is drift accumulating with horizon and variance shrinking with N — the
statistic was still climbing when the grid ran out. On short-only, edge peaks
pass **zero of six** against 42% for interior peaks.

**The spread does NOT show the pattern, and that is correct rather than an
exception:** a corner peak signals drift accumulation, and the spread
construction is defined by removing drift. The red flag belongs to the
constructions that carry exposure.

## GATE 1i — report where the peak sits, and treat a boundary peak as unresolved

| | |
|---|---|
| **interior peak** | the maximum is contained by the grid; the statistic is a maximum |
| **edge / corner peak** | the statistic was still rising when the sweep ended. **The result is unresolved, not concluded** |

**A separate caution applies to the spread even though the drift one does not.**
`t` rises with N through **averaging**, not through a larger edge:
`close_in_range` earns **+71.8 bp at N=3 and +20.4 at N=50** while its `t` rises.
So a peak at N=50 means *a small per-name effect rescued by breadth* — exactly
the constraint `FINDINGS.md` §4 and §9 describe. **Report the per-name effect at
the peak alongside `t`**, so breadth cannot masquerade as strength.

**And a peak at max k means the grid may be too short to contain the maximum.**
Either extend the sweep or record the result as horizon-unresolved.

---

# SIXTH AMENDMENT, 2026-09-08 — NO GATE IS AN ADMISSION ON ITS OWN: each is half of a pair

**This amendment adds no gate and moves no threshold. It names a property the set
already has**, so that the standard check on a hurdle becomes *"what is it paired
with?"* rather than *"is the number right?"* — the question that found two defects
this record did not know it had.

## What prompted it

The principal's challenge, 2026-09-08: **correlation does not bound a difference in
means.** ρ is computed on mean-removed, volatility-normalised series, so it
constrains the co-movement of *deviations* and is silent on *levels*. Two books can
correlate at 0.92 and earn +12 bp and +1 bp a bar; where that happens the right
action is to hold the better one, not to call them the same strategy.

Auditing the stage-1 set for that error turned up something better than a list of
defects: **the set is mostly immune, and the reason is structural rather than
lucky.**

## The property

> **THE STATISTIC IN A GATE IS ALWAYS BLIND TO SOMETHING. A gate is safe when
> another gate sees exactly what it is blind to. No gate in stage 1 is an
> admission on its own; each is half of a (SIGNIFICANCE, SIZE) pair, and a gate
> without its partner is a gate that can be passed — or failed — for the wrong
> reason.**

**This is not new to this record; it is twice-instantiated in it already, and this
amendment only generalises what those two passages assert:**

- **Second amendment:** *"1e and 1f together, never 1f alone. That pairing is the
  whole content of this amendment."*
- **Fifth amendment, gate 1i:** *"`t` rises with N through averaging, not through a
  larger edge … Report the per-name effect at the peak alongside `t`, **so breadth
  cannot masquerade as strength**."*

Both say the same thing about different pairs. The property is the pattern.

## The audit, gate by gate

| gate | statistic | blind to | its partner | status |
|---|---|---|---|---|
| **1a** | t vs its own null | **size** — scale-invariant, and grows as √n | **1c** | paired |
| **1b** | qualitative | — | — | procedural |
| **1c** | mean move ÷ measured round trip | **holding period** — *monotone* in it | **none** | **⚠ UNPAIRED** |
| **1d** | correlation to book arms | **level** | **none** | **⚠ UNPAIRED** |
| **1e** | open-entry t | size | **1c**; and retention beside it | paired |
| **1e** | retention ≥ 50% | level of both edges | 1a / 1c supply the level | paired |
| **1f** | name-split CV > 0 | **magnitude** — a sign test | **1e** (second amendment) | paired, and already flagged *necessary, not sufficient* |
| **1g** | turnover, holding run, dead share | — | reporting, no bar | n/a |
| **1h** | direction declared | — | procedural | n/a |
| **1i** | interior vs edge peak | **height of the peak** | the per-name effect at the peak, required by the fifth amendment | paired |

**Eight of ten are paired, and the two that are not are exactly where defects were
found.** That is the evidence for the property rather than a restatement of it.

## The two unpaired gates — IDENTIFIED HERE, NOT FIXED HERE

**Neither replacement is adopted by this amendment.** Both change what a gate
*does* and therefore need their own pre-registration; D375 already has 1d awaiting
one. They are recorded so the gap is not rediscovered.

**1d is blind to level.** It can only reject, and it rejects on shape. A candidate
correlating above the bar with an existing arm is turned away **whatever it
earns** — including when it earns materially more, where the correct outcome is to
**replace** the incumbent rather than reject the candidate. The partner it needs is
a **paired difference of means on matched bars**, and the arithmetic is favourable:
`Var(A − B) = σ²_A + σ²_B − 2ρσ_Aσ_B` is *small* at high ρ, so that test is **most
powerful exactly where 1d goes blind.** A high correlation does not obstruct
comparing levels; it sharpens the comparison.

**1c and 2c are monotone in holding period.** `mean move per trade ÷ round trip`
rises mechanically as the hold lengthens — the numerator accumulates with holding
time while the denominator stays one round trip per trade. **A candidate can clear
1c by holding longer while its per-bar edge falls.** `CLAUDE.md` states the
mechanism (*"a longer hold lifts breakeven by amortising one round trip; per-bar
edge usually falls … say which moved"*) and D373's segmentation diagnostic
confirmed it on a different per-trade statistic: re-cutting one book's own stored
paths, identical exposure and only the trade boundaries changed, took the
`mean > median > 0` chain from **PASS at 40 bars to FAIL at 100.** The partner it
needs is the **per-bar edge on the deployed base at the same hold**, which gate 1i's
horizon profile already produces.

**No past verdict is disturbed by either.** 1d has been applied once (D373 H7),
where the means evidence agreed independently; 1c and 2c have been applied at a
**fixed cap within each study**, so their comparisons were internally valid. The
exposure in both cases is *forward* — and, for 1c, *cross-study*.

## What this amendment requires

1. **A pre-registration that quotes a stage-1 gate must name that gate's partner
   and report both**, or state that the gate is unpaired and what is being done
   about it.
2. **A candidate cleared on one half of a pair is recorded as UNRESOLVED on that
   gate**, never as clearing it — the same convention D369's SE band and gate 1i's
   edge peak already use.
3. **A new gate is not admissible until its blind spot is named and its partner
   identified.** Writing down what a statistic cannot see is now part of proposing
   it.

## What this amendment does NOT do

- **It adopts no threshold and retires no gate.** 1c, 1d and 2c stand as written.
- **It does not adopt 1d″ or 1c′/2c′.** Those are the principal's, and belong in
  D375's outstanding calibration pre-registration.
- **It makes no claim about stages 2–5**, whose gates were not audited.
- **It does not touch `docs/FINDINGS.md`.** A related loose clause in §52's
  corollary — *"at ρ ≈ 0.92 two such constructions are the same strategy for
  portfolio purposes"* — carries the same overreach and is raised, with a proposed
  replacement, in `working/FINDINGS-52-corollary-NOTE.md` for the principal to
  accept or decline. **§52's substance is unaffected: it stands on `B_c` and the
  cohort hedge, which are level measurements.**

## Stage 1's gates, restated with their pairs

| | gate | paired with |
|---|---|---|
| **1a** | t-based best-of-N floor | **1c** |
| **1b** | mechanism and numeric shape declared before the run, with a falsifier | — *(procedural)* |
| **1c** | mean move vs the **measured** round trip — reported, not binding | **⚠ unpaired on holding period** |
| **1d** | correlation to existing book arms | **⚠ unpaired on level** |
| **1e** | **CAPTURABILITY — open-entry `t` ≥ 2 and retention ≥ 50%** | **1c**, and **1f** |
| **1f** | **name-split CV > 0** — necessary, and explicitly **not sufficient** | **1e** |
| **1g** | turnover and holding run, **reported** | — |
| **1h** | both directions, **declared then disclosed** | — |
| **1i** | interior vs edge peak, **and the per-name effect at the peak** | self-paired by the fifth amendment |

---

# SEVENTH AMENDMENT, 2026-09-08 — gates 1c and 2c gain their partner: HOLD-DRIVEN

**The sixth amendment identified 1c and 2c as unpaired on holding period and deferred the fix to
the principal. The principal has adopted it. This amendment supplies the partner and changes no
threshold.**

## The defect, restated in one line

**`mean move per trade ÷ measured round trip` rises mechanically as the hold lengthens** — the
numerator accumulates with holding time while the denominator stays one round trip per trade.
**A candidate can clear 1c by holding longer while its per-bar edge falls.**

The mechanism is already doctrine — `CLAUDE.md`: *"a longer hold lifts breakeven by amortising one
round trip; per-bar edge usually falls, so Sharpe can drop as cost coverage rises. **Say which
moved**"* — and it was confirmed on a different per-trade statistic by D373's segmentation
diagnostic, which re-cut one book's own stored paths with **identical exposure and only the trade
boundaries changed** and took `mean > median > 0` from **PASS at 40 bars to FAIL at 100.**
**Per-trade statistics inherit whatever the exit rule does to trade boundaries, and 1c and 2c are
per-trade statistics.**

## GATE 1c′ / 2c′ — the ratio keeps its threshold and gains a companion number

> **The per-trade cost ratio is reported beside the PER-BAR EDGE ON THE DEPLOYED BASE AT THE SAME
> HOLD. A candidate that clears the ratio while its per-bar edge FALLS relative to a shorter hold
> in its own profile is recorded HOLD-DRIVEN, not as clearing.**

**The threshold is unchanged** — 1.0× for 1c, 1.5× for 2c. What changes is that a pass now carries
the direction of the per-bar number with it.

**It costs nothing to compute.** Gate 1i already requires the horizon profile, and the deployed
base is already reported under 1g. **This is a column, not a run.**

## Why HOLD-DRIVEN rather than a failure

**Lengthening the hold is a legitimate deployment choice** — R14's fourth amendment of 2026-09-03
makes the holding period a deployment variable, not a research one, precisely because it trades
gross against edge density. A HOLD-DRIVEN pass is therefore **not a defect to be failed**; it is a
pass whose provenance must travel with it, so that a later reader can tell *"this cleared cost"*
from *"this cleared cost by holding four times as long."*

**The convention matches the ones already in use:** gate 1i's edge peak is *unresolved*, not
failed; D369's 2-SE band is *unresolved*, not failed. **HOLD-DRIVEN is the third member of that
family.**

## Scope, and what is not disturbed

- **No past verdict changes.** 1c was applied across D290's 51 candidates and 2c across
  D264–D284, but **each comparison was made at a fixed cap within its own study**, so every one
  was internally valid. **The exposure this closes is cross-study comparison, and any future
  candidate whose hold is a free parameter.**
- **This amendment does not touch 1d.** The sixth amendment identified 1d as unpaired on level and
  proposed 1d″; that remains the principal's, and D375's outstanding calibration pre-registration
  is where it belongs.

## Stage 1's gates, restated

| | gate | paired with |
|---|---|---|
| **1a** | t-based best-of-N floor | **1c′** |
| **1b** | mechanism and numeric shape declared before the run, with a falsifier | — *(procedural)* |
| **1c′** | mean move vs the **measured** round trip, **beside the per-bar edge at the same hold**; a pass on a lengthened hold is **HOLD-DRIVEN** | **the per-bar edge** ✔ |
| **1d** | correlation to existing book arms | **⚠ still unpaired on level — see the sixth amendment** |
| **1e** | **CAPTURABILITY — open-entry `t` ≥ 2 and retention ≥ 50%** | **1c′**, and **1f** |
| **1f** | **name-split CV > 0** — necessary, and explicitly **not sufficient** | **1e** |
| **1g** | turnover and holding run, **reported** | — |
| **1h** | both directions, **declared then disclosed** | — |
| **1i** | interior vs edge peak, **and the per-name effect at the peak** | self-paired by the fifth amendment |
| **2c′** | ≥ 1.5× round trip, **beside the per-bar edge at the same hold** | **the per-bar edge** ✔ |

**One of the two gaps the sixth amendment found is now closed. 1d remains open.**
