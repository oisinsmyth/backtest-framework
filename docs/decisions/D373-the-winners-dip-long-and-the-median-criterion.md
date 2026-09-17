# D373 — the winners' dip long, and the median trade as a selection criterion

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **Nothing here is a
result.** No null has been run on this arm, no four-group report has been read for it, and its
top trade has never been named.
**Date:** 2026-09-07
**Area:** signal research · **personal track**

**No holdout testing. Holdout reads spent by this record: 0. Programme total: 1** (D371,
2026-09-07 — `us_shorts_daily_holdout.csv.gz`, spent and not to be re-read).

---

## 0. Why this record exists, and what is new in it

Two things, and the second is the point.

**First, an owed test.** [D359 §6](D359-RESULT-the-loser-cohort-does-not-drift-down-on-the-floored.md)
reported the **mirror** of its failed short — a fresh `rev_5` dip on a name in the **top** decile
of 12-month momentum, entered **long** — as a mechanism check, counted it in no multiplicity, and
closed with *"it becomes a finding only under its own pre-registration with A′, B, B_c and C, the
four groups with the top trade named, and the deployed base, and STACK §6 puts that first."*
It was never run. The momentum lineage (D365–D371) is why.

**Second, and this is the new part: the criterion itself is under test.**
[R15](../RULES.md#r15) defines a signal as a positive gross **mean** per trade above its nulls.
[D371](D371-RESULT-the-momentum-holdout-read.md) is the only out-of-sample evidence this
programme owns, and it says what that criterion selects for:

| D371, holdout, 803 unseen names | |
|---|--:|
| mean per trade | **+114.97** bp |
| **median per trade** | **−36.57** bp |
| skew / excess kurtosis | 1.64 / 9.87 |
| top trade (CAR, 2021-04-19, held to cap) | **30% of all P&L** |
| top-1 / 5 / 10 name share | **36 / 142 / 231%** |
| names to half the P&L | **2 of 255** |

**A book whose mean is +115 and whose median is −37 is a book where the typical trade loses and
a handful of names carry everything.** The mean criterion cannot see that shape. `CLAUDE.md`
already requires the median to be *reported*; nothing in this programme has ever *selected* on
it. This record does, and it says so before the run rather than after.

**The mirror is the first candidate in the record whose median is positive**, which is why it is
the right one to test the criterion on.

### The principal's ruling on mining the spent fixture, 2026-09-07

Raised and settled before this record was written: **a brand-new construction may be mined on
the same in-sample fixture, provided there is no cross-contamination with the holdout.** This is
consistent with [R14's first amendment](../RULES.md#amendment-to-r14-2026-09-02--both-tightenings-were-wrong-and-the-principal-was-right)
— selection on spent data is not a statistical invalidity; *"the mining fixture does not become
more spent."*

**What it costs is the PRIOR**, and the principal's own qualification is recorded with it: that
cost **rises slowly as a percentage on its own** as the programme continues and learns, and is
acceptable at today's level. It is not zero and it is not fixed. This record therefore states
its search cost in §7 rather than treating the fixture as free.

## 1. The construction, frozen

Identical to [D359 §1](D359-the-bear-market-rally-short-a-spike-inside-the-loser-cohort.md)'s
mirror. All conditions on the lagged, floored (`keep_v2`), deal-filtered (F0), warm-based
cross-sectional percentile at **t−1** (D347's closure; `pct` undefined below 50 finite names),
on eligible bars after the hedge is defined.

- **Cohort:** `pct_mom[t] ≥ 100 − c` on `mom_252_21` (the 252-day return less the last 21 days;
  high is a winner). **c = 10** → the top decile.
- **Trigger:** a fresh dip of `rev_5` into the bottom: `pct_rev[t] ≤ 100 − s` **and**
  `pct_rev[t−1] > 100 − s`. **s = 90** → `pct_rev ≤ 10`.
- **Entry:** **LONG at the next open** ([D340](D340-execution-lag-a-next-open-fill.md)), every event taken,
  no slot cap, hedged against the floored universe's equal-weight return, truncated at delisting.
- **Exit:** **cap 40** is the primary. Cap 10 and invalidation-capped-10 are the two other cells
  D359 showed and are scored here, not reported beside — see §7.
- **Borrow:** none. The arm is long. The hedge's borrow is charged as D359 charged it.

**Direction is declared before the run ([gate 1h](../RULES.md#fourth-amendment-to-r14-2026-09-02--a-score-is-a-ranking-its-direction-is-a-choice)): LONG.**
The mechanism is *a sharp fall bounces best in a name that is not beaten down*, which is D347's,
D350's and D358's finding taken to its end. A result in the opposite direction is reported as
**DIRECTION-INVERTED** and counts against the mechanism even if the number is good.

### What already exists in code

`scripts/run_d359_loser_rally_short.py` carries `mirror_signal(P, c, s)`, `run_mirror(...)` and
the `arm_report` path that produced D359's table. **What has never been run against the mirror is
the null suite.** D373's runner re-points A′, B, B_c and C onto this arm; it does not rebuild the
signal. The runner must state, from D359's own artifacts, exactly which mirror quantities were
previously computed and which were not, rather than restating this paragraph.

## 2. What is already known, and is therefore not a prediction

From D359 §6, on the cell this record makes primary. **These numbers exist; nothing below claims
credit for them.**

| mirror, long, bp per TRADE | n | mean | median | t | 2c PUB | 2c PB | net PUB | net PB | era 1 | era 2 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **10 / 90, cap 40** | 3,932 | **+160.5** | **+51.5** | 5.1 | 77.7 | 31.6 | **+82.9** | +129.0 | **+16.9** | **+227.4** |
| 10 / 90, cap 10 | 7,290 | +68.6 | +36.6 | 5.9 | 83.6 | 36.9 | −15.0 | +31.7 | +7.9 | +95.0 |
| 10 / 90, inv 10 | 8,190 | +47.2 | +123.4 | 5.8 | 85.5 | 36.9 | −38.3 | +10.3 | −0.5 | +67.5 |
| 10 / 95, cap 10 | 4,955 | +74.5 | +36.1 | 4.8 | 88.4 | 32.1 | −13.9 | +42.4 | −8.4 | +108.0 |
| 20 / 90, cap 10 | 12,486 | +52.1 | +31.1 | 6.4 | 73.7 | 32.9 | −21.6 | +19.2 | +5.5 | +72.6 |

**The premise is already confirmed and is not under test.** D359 §7 measured the top decile's own
hedged drift at **+3.85 bp/bar** over the span. The cohort rises. What is under test is whether
the *dip* adds timing on top of that — which is exactly what B_c asks, and why B_c is
load-bearing here.

**Two arithmetic facts computable from the table above, stated now so no result can present them
as discoveries:**

1. **Era 1 does not cover its own round trip.** +16.9 gross against a 77.7 bp PUB round trip is
   **−60.8 net per trade in era 1**. Under R15 that does not disqualify the signal — cost is
   engineered afterwards — but the *gross* era-1 number is small enough that H3 is a real bar and
   not a formality.
2. **The era ratio is 13.5×** (+227.4 / +16.9). The construction that just failed out of sample
   ran **26×** (+12.10 / +0.46 bp/bar, D366). **This candidate has the same signature at half the
   severity**, and §5 is written around that.

## 3. Stage 0 — the concentration shape, before any null

Run first, on the primary cell's existing ledger, and read before the nulls: the **four groups**
with the top trade **named and its bar printed** (`name-the-top-trade`; D322 reported a share,
never looked, and fifteen studies ran on thirty fabricated days).

Specifically: count, mean, median, win rate, payoff, holding run, skew, kurtosis; the 1% trim
from **both** tails with all three means (ex-top, ex-bottom, trimmed); names to half the P&L as a
**share of distinct names traded**; top-1/5/10 name share; profitable years; and the splits on
dead-vs-alive, era, and **price**.

**This is a diagnostic and admits nothing.** It is run first because if the shape is D371's —
median negative, top trade a fifth of the ledger — the nulls are beside the point and the record
stops at §3 with that finding. D359 reports the median as +51.5, so the expectation is that it is
not D371's shape; stage 0 is what confirms that on the full ledger rather than on one summary row.

## 4. The nulls

All on the primary exit, per cell. Every null's events must satisfy **the observed events'
eligibility mask** — D351's correction, and the standing trap: a null centred far from the base
rate is a broken null, not a mechanism.

- **A′** — each name's events rotated in time within its **eligible** bars (D351). **2,000 draws**
  (see the amendment below).
- **B_c** — **load-bearing.** Each event's name replaced by a random eligible name **in the same
  top-decile cohort** that day (`pct_mom ≥ 90`, and not itself an event name); **2,000 draws.**
  This is the null that asks whether the **dip** carries information or whether **being a
  12-month winner is the whole story**. Given that the momentum book has just failed out of
  sample, a candidate that turns out to be the winner cohort wearing a trigger is the single most
  likely way this record produces a false positive.
- **B** — each event's name replaced by a random eligible name in the same `rsi` bucket that day,
  defined-percentile pool; **2,000 draws.** Breaks the cohort by design.
- **C** — random direction on the per-trade ledger; **2,000 draws.**

**Draw counts and their resolution.** [D369](D369-RESULT-the-null-precision-rerun.md) found a
200-draw p95 carries a bootstrap SE of **0.301** and that three studies decided verdicts inside
it. The margins here are tens of bp per trade rather than tenths of a bp per bar, so 10,000 is
expected to be generous — but **the bootstrap SE of every reported p95 is printed beside it**, and
any hurdle whose margin is within 2 SE of its bar is recorded **UNRESOLVED**, never passed. That
is D369's actual lesson and it is cheap to honour.

**The distribution, not the percentile alone**: p50 and p95 reported for every null, with a
statement of whether the null is decisive (four cases in this programme of a *losing* random
control at the 100th percentile — R7).

### AMENDMENT to §4, 2026-09-07 — the draw counts, set before the runner was built and before any result

**This record was drafted asking for 10,000 draws on A′ and B_c. That was not costed, and it is
not affordable.** D359's own artifacts measure the same null machinery at **0.54 s/draw (A′),
0.69 (B), 0.35 (B_c)** at cap 10. Cap 40 holds four times as long, and the best-of-5 floor
multiplies by five cells: 10,000 draws lands near **40 hours serial**, roughly 5 on eight
processes, for a margin that does not need it.

**Revised: A′ and B_c at 2,000 draws, B at 1,000, C at 2,000.** The basis is D369's own
arithmetic rather than a preference. D369 measured the p95's bootstrap SE at **0.301 on 200
draws**, falling to 0.020–0.056 at 10,000 — SE scales as `1/sqrt(n)`, so 2,000 draws sits at
roughly **0.095** on a bp/bar statistic. D369's problem was a **0.1 bp/bar** margin, where that
SE is fatal. **This study's primary margin is per TRADE and roughly 140 bp** (+160.5 observed
against a null centred near the cohort's own drift), which is hundreds of SE at any draw count
above a few hundred. Spending 5 hours to move a 200-SE verdict to a 400-SE one buys nothing.

**Where the precision actually matters is H3**, whose observed era-1 value is +16.9 on half the
trades, and 2,000 draws is chosen for that hurdle rather than for H1.

**The guard is unchanged and it is the real one:** every reported p95 carries its bootstrap SE,
and any hurdle whose margin falls within **2 SE** of its bar is recorded **UNRESOLVED**, never
passed. If H3 lands inside that band at 2,000 draws, the answer is to spend more draws on that
one hurdle, and the record will say so rather than rounding it to a verdict.

**Nothing else in the pre-registration is touched.** No hurdle, statistic, cell, prediction or
construction changes; this is a resource decision, made before the runner existed and before any
number was seen.

### NOTE on the null implementation, same date

`CLAUDE.md` directs every runner to be built on `scripts/fast_null.py`. **It does not apply
here, and the reason is the rule's own.** `fast_null` accelerates *rotation nulls over a position
matrix* — the D256–D285 book lineage. This study's controls are the **event-signal** family
(`EB.rotate_signals`, `EB.simulate_event`, `V47.control_b_signal`) that D348, D351, D358 and D359
established and D371 used. Re-implementing them on different machinery would risk exactly what
`assert_matches_scorer` exists to prevent: **a null that is not comparable to the study it
controls, or to D359's published draws.** The established path is used unchanged, and this
paragraph is the disclosure.

## 5. The hurdles — pre-registered, and H2/H3 are the new ones

**All of H1–H5 must hold.** H6 and H7 are reported in full and gate nothing, per R15.

| | hurdle | why it is here |
|---|---|---|
| **H1** | **Signal (R15).** Gross mean per trade > 0 **and** above the p95 of A′, B, B_c and C — measured against the **best-of-5 floor** of §7, not against a single cell's control | the standing criterion |
| **H2** | **The shape chain: `mean > median > 0`.** Gross **median** per trade > 0, **and** above the p95 of the same four controls' **medians**, **and** the gross mean strictly exceeds the gross median | **NEW, and tightened at the principal's ruling, 2026-09-07.** See §5a |
| **H3** | **Era 1 standalone.** Era 1's gross mean per trade > 0 **and** above the p95 of A′ and B_c **recomputed within era 1** | **NEW.** The retired book paid +0.46 in era 1 against +12.10 in era 2 and failed out of sample. §2 shows this candidate at 13.5×. **This is the hurdle I expect to fail** — see Q3 |
| **H4** | **Breadth.** Names to half the P&L ≥ **10% of distinct names traded**; top-1 name share ≤ **15%**; top-5 ≤ **50%** | breadth-relative, not a flat count — the mis-specification D371 §6a found in H5. The thresholds are calibrated **to exclude the shape that just failed** (D371: 0.8%, 36%, 142%) and that is stated rather than presented as neutral |
| **H5** | **Capturability (gate 1e).** Open-entry t ≥ **2.0** and retention ≥ **50%** against the close-signal version | R14's second amendment; fifteen of D290's 51 collapsed on it |
| **H6** | **Cost, reported not gating.** Net PUB and PB; the held names' **measured** half-spread (Corwin–Schultz off the OHLC, not an assumption); breakeven half-spread; the 4-crossing line primary for an event book with the 2-crossing beside (FINDINGS §38 rule 4); **turnover per bar, mean holding run and dead-name share** (gate 1g) | R15: cost decides nothing at the signal stage. D285 missed a guessed 15 bp/side bar by 0.65 |
| **H7** | **Independence, measured at stage 1** (R14's fixed ordering). Correlation of the deployed bar series to the **retired** S6/C9 momentum books, and to S1 and S2 | the arm selects on `mom_252_21`'s top decile. If it is the retired book re-expressed we should learn it on day one, not at stage 5 |

**Both lenses, never on the same statistic** (`CLAUDE.md`, FINDINGS §10): the path-invariant
per-trade reading and the path-variant deployed book in bp/bar, reported separately, with the
opportunity cost of the slot named as unmeasured.

**The horizon profile is REPORTED and NOT PICKED.** Cap ∈ {5, 10, 20, 40, 60} scored and shown
in full, per [R14's fourth amendment of 2026-09-03](../RULES.md#fourth-amendment-to-r14-2026-09-03--the-holding-period-is-a-deployment-variable-not-a-research-one)
— hold length trades gross against edge density and that is a capital decision, not a signal one.
Cap 40 is primary here **only because it is the cell D359 reported**, and §7 prices that choice.
Whether the profile's peak is interior or at the grid edge is reported (gate 1i); an edge peak is
**unresolved, not concluded**.

### 5a. Why H2 is a chain and not a single inequality

**The principal's ruling, 2026-09-07: the hurdle is `mean > median > 0`, not `median > 0`.**
It is strictly stronger than the version this record was drafted with, and it closes both tails
rather than one:

- **`median > 0`** — the typical trade wins. This is the anti-lottery condition, and it is what
  D371's book failed: mean +114.97 against a median of **−36.57**, with one trade at 30% of the
  ledger. A positive mean over a negative median means the median trade is being carried.
- **`mean > median`** — the right tail, not the left, supplies the asymmetry. `CLAUDE.md` already
  names the converse as a defect: *"a mean below its median is the tell that the left tail is
  doing the work."* On a long book that is the dangerous ordering — the book wins most days and
  gives it back in rare large losses, which is the shape that survives a backtest and ruins an
  account.

**Together they demand: the typical trade is profitable, AND what deviation there is points
up.** Neither inequality alone gets that. `median > 0` permits a book whose mean is dragged under
its median by a fat left tail; `mean > median` alone is satisfied by every lottery book in this
programme, D371's included.

**The chain bites on data already in the record**, which is the test of whether a hurdle is real.
Of D359's five mirror cells in §2, **`10 / 90, inv 10` fails it**: mean +47.2 against a median of
**+123.4**, median above mean, exactly the left-tail ordering `CLAUDE.md` flags. The primary cell
passes as drafted — +160.5 > +51.5 > 0 — so the hurdle is not vacuous and not tailored to admit
the candidate.

**Recorded as a ruling, not as my own tightening.** The version committed before this amendment
required only `median > 0` above its controls.

## 6. Assertions the runner must carry

The three standing ones, in the patterns of `scripts/run_overnight_long.py`:

- **[L] Lag audit** — re-derive the held set from `score[:, t−1]` in a **second implementation
  that never calls the selection function.** ~93% of D279's apparent edge was this bug.
- **[S] Sign audit, in money** — a favourable move pays **positively** on the long; +50 bp on one
  name moves exactly one trade by +50.000 and no other bar; a dividend moves long and short
  oppositely. A sign asserted in prose inverted D280.
- **[Q] Right-quantity** — the compounded grid differs from the one not meant to be scored.

And specific to this study:

- **[E]** every null event satisfies the **observed events' eligibility mask** (D351). Assert it
  per null, per draw batch — not once.
- **[N]** each null's centre is reported against the cohort **base rate**, and a null centred far
  from it fails the run rather than earning a mechanism (D347 → D351, twice).
- **[Bc]** B_c draws **only** from names with `pct_mom ≥ 90` on that bar, and **never** an event
  name; pool membership asserted per draw.
- **[P]** the result JSON is **persisted before it is rendered.** D371's first execution computed
  its evidence and lost it to a `KeyError` in the print loop; recovery was luck.
- **[X]** the self-test **RAISES** on (a) the mirror's sign flipped, and (b) an event drawn
  outside the eligible mask. **A self-test that cannot fail is worse than none.**

## 7. The search cost, stated

**Multiplicity 5, and the primary cell was chosen after seeing all five.** D359 §6 printed five
mirror rows; cap 40 is the best of them on mean, net PUB and net PB. Choosing it after the fact is
a look, and pricing it is not optional:

**H1 is therefore measured against a best-of-5 floor** — every one of the five cells scored
against its own controls, the maximum of the five null draws taken per draw, exactly as
[D367](D367-RESULT-the-gate-deconstructed-and-the-book-without-its-winners.md) built its
best-of-46 control. A single-cell p95 would flatter the chosen cell by construction.

**Under [R13](../RULES.md#r13), what carries and what does not.** D359's four *short* cells do not
carry: different direction, different cohort, a hypothesis this record is not testing. D352's
`rev_5` event matrix **does** carry — the mirror is its shape restricted to the top cohort, and
D359's own check ties the two together bit-identically. The count stated for this record is
therefore **5 cells × the D352 `rev_5` lineage**, disclosed rather than summed into a floor no
measurement could clear (R13's corollary).

**In-sample looks are bookkeeping, not a bar** (R14's first amendment). **The ledger counts
holdout reads, and this record spends none.**

## 8. Predictions

Committed before the runner exists. Each is written in the runner's own quantities so it can be
scored mechanically rather than argued. Q1 is load-bearing; Q3 is **against**.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* the primary cell's gross mean per trade is **above the p95 of B_c** — the dip carries timing **inside** the winner pool, and is not the cohort's own +3.85 bp/bar drift re-expressed |
| **Q2** | the full chain `mean > median > 0` holds on the primary cell, with the median above the p95 of all four controls' medians — H2 clears. §2's row gives +160.5 > +51.5 > 0 **before** any control, so the live part of this prediction is the median's margin over its nulls, not its sign |
| **Q3** | *(against)* **H3 FAILS**: era 1's gross mean is either ≤ 0 or inside the p95 of A′ or B_c recomputed within era 1. §2 puts era 1 at +16.9 against era 2's +227.4, and that is the signature of the book that just died |
| **Q4** | H7's correlation of the deployed series to the retired S6/C9 books is **between 0.2 and 0.5** — related by cohort, not identical. Below 0.2 would surprise me; above 0.5 retires the record under §9 |
| **Q5** | H5 clears: retention ≥ 50%. The trigger is a close-to-close percentile crossing entered at the next open, so it is not the one-bar artifact gate 1e was built to catch |
| **Q6** | the horizon profile's peak on **gross per trade** sits at the **grid edge (cap 60)**, not interior — drift accumulating with horizon, and therefore **horizon-unresolved** (gate 1i) rather than a maximum at 40 |
| **Q7** | the top trade is **≤ 15%** of the ledger (H4's bar). D371's was 30% and D366's GME was 11.7% |

## 9. What would make me abandon this

- **H3 fails** (Q3, which I expect) → the construction is an era-2 phenomenon sharing the retired
  book's signature. **Record it and stop.** Do not sweep for an era-1 variant: that is the search
  that produced D366's gate, and it cleared 164 standard errors before failing out of sample.
- **H7 > 0.5** → it is the momentum book re-expressed, and the momentum book has been read out of
  sample and retired. Nothing further is owed.
- **The median is inside its controls** → the criterion this record exists to test has answered
  its own question in the negative on the one candidate that looked most likely to pass it. That
  is a finding about **the programme's selection rule**, and it is worth more than the candidate.
- **Any hurdle needs a holdout read to settle** → **do not spend it.** The second slice
  (`order[5100:]`, never fetched, never scored) is not cut for a stage-1 signal test, and D357's
  short candidate has a prior claim on it.

---

**Status footer.** No runner exists. No null has been run on this arm. No book is proposed.
`docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty. Nothing in this
record is a result, and **only the principal closes a research avenue (R15).**
