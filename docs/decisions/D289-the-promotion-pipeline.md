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
