# D265 — The entry-time reconciliation

**Status:** **RUN AND CLOSED.** Gate G passed; the discrepancy is fully explained.

**Everything above the RESULT heading was committed in `6b5f729`, BEFORE the check was written.**
**Date:** 2026-09-01
**Area:** Strategy research · **personal track** ([BOOK.md](../BOOK.md))

**This record exists because two measurements on the same data disagree, and I do not yet know
which is right.** It is a reconciliation, not a candidate search.

---

## The disagreement

| | |
|---|---|
| **[D264](D264-the-intraday-short-on-single-names.md) scored `LOW:S2_short_intra`** | **−0.89% CAGR**, excess Sharpe −0.208, linear gross **+1.43%/yr** |
| **The D265 decay profile of the same entries** | **+8.24 bp** mean cumulative at bar 18 against a **4.00 bp** round-trip cost — **2.06×** |

**A profile clearing its cost bar by 2× and a book losing money cannot both be describing the same
thing correctly.** One of them is measuring something other than what it appears to.

### What has already been ruled out

**The clock.** The first explanation offered was a time-of-day confound: the profile's long-hold
columns only contain trades that *had* that many bars left before the close, which selects
early-session entries. A matched control — **same symbol, same bar-of-day, a different session
drawn at random** — was run against it. For `LOW:S2_short_intra` the control came back **flat
(≈0 bp)** and the signal carried essentially the entire 8.3 bp, at **2.07×** the bar.

**So the confound as originally stated is disproven, and the discrepancy is still there.** That is
why this needs registering rather than one more look.

### What has NOT been ruled out, and is what this tests

The control matched *which* bar-of-day. It did not address **selection into the column**: at bar 18
only **82%** of trades survive, and the missing 18% are late-session entries that ran out of session
before reaching that horizon. **If the edge is concentrated in early-session entries, the profile is
correct about early entries and the book is correct about the average, and both numbers stand.**

There is a second candidate cause and it is tested at the same time: **the book's exits are
signal-driven, not fixed-horizon.** S2 exits at age 63 or state end and is then flattened at the
close, so a book trade is not the fixed-horizon hold the profile measures.

---

## The measurement

Two arms over the **same entries**, both partitioned by **entry bar-of-day**.

```
ARM A — what the BOOK actually earns
        P&L per trade from entry to the book's OWN exit (signal end, or the
        session close, whichever comes first).

ARM B — what the PROFILE measures
        P&L per trade from entry to the session close, fixed horizon.
```

**Buckets, fixed here before anything is read.** Bar-of-day at entry, 26 bars per session, and
entries cannot occur at bar 0 because the intraday book is flat at every session open:

| bucket | bars | clock |
|---|---|---|
| **EARLY** | 1–8 | 09:45 – 11:30 |
| **MID** | 9–17 | 11:45 – 13:45 |
| **LATE** | 18–25 | 14:00 – 15:45 |

**Three buckets, equal-width, not swept.** No threshold will be tuned, no fourth bucket added, and
no alternative boundary tried. Committed here so that a bucket edge cannot be chosen after seeing
which one carries the result.

**Cost bar:** `2c = 4.00 bp` per round trip on the LOW stratum, the same signal-independent bar the
decay profile used. A bucket "clears" if its mean P&L per trade exceeds it.

---

## THE VALIDATION GATE — this check is void if it fails

**G. Arm A must reproduce D264's committed `gross_linear_pa` for `LOW:S2_short_intra` (+1.43%/yr)
to within ±0.30 percentage points**, when trade-level P&L is aggregated back to an annual figure.

**Because if the per-trade decomposition does not rebuild the number the book already reported, then
I have not understood what the book is doing and no bucket reading means anything.** This is the
leg that can fail, and it is stated first deliberately — R6's lesson is that a hurdle naming a test
is not cleared until that test is run, and a reconciliation that never reconciles anything is worse
than no reconciliation.

**If G fails, the discrepancy is recorded as UNEXPLAINED and this record closes with that verdict.**
No bucket table is interpreted, and the decay profile's 2.06× is marked as not understood rather
than quietly retained.

---

## Predictions, declared before the run

| | prediction | confidence |
|---|---|---|
| **P-1** | **Mean P&L per trade is HIGHER for EARLY entries than for LATE entries**, in both arms. This is the hypothesis under test and its direction is declared so it cannot be re-read | **moderate** |
| **P-2** | **Arm A's all-bucket mean is BELOW the 4.00 bp bar**, consistent with the book losing money | **high** |
| **P-3** | **Arm B exceeds Arm A** — the fixed-horizon hold beats the signal's own exits, because the decay profile showed marginal return still positive when the signal turns off | **moderate** |
| **P-4** | **The gap between the profile and the book is mostly ARM (A vs B), not BUCKET.** i.e. the exit discipline explains more of the discrepancy than entry timing does | **low-moderate — this is the one I expect to be wrong**, since entry timing was the proposed explanation |

**P-4 is registered against my own stated hypothesis on purpose.** The entry-time story is the one I
offered; declaring the opposite as a live possibility is what stops the check from being a search
for confirmation.

---

## What a positive would and would not license

**If EARLY entries clear the 4.00 bp bar on their own, that is NOT a result and NOT a rule.** It is
a candidate, and it carries two defects that must be stated with it:

1. **The bucket boundary is a free parameter that has now been used.** Fixed in advance here, but
   one look at three buckets is still three cells, and a future entry-time rule inherits them.
2. **It is post-hoc on data D264 already scored.** Any book built on it needs its own pre-registered
   out-of-sample test under [R8](../RULES.md#r8), on names or a period this fixture has not touched
   — which requires a fetch that has not been made.

**And [D246](D246-the-search-protocol-for-s3.md) Constraint 3 applies:** this arrives out of the
complement of a failed cell, so it is eligible only as its own registration with that provenance
stated. This record is that statement.

---

## Stop

**This record answers one question and stops.** No entry-time rule is built, no threshold swept, no
fourth bucket, no other arm, no other stratum. **If P-1 holds, the output is a candidate description
and a ledger entry — not a book.**

---

## Ledger

**The post-hoc looks since D264 closed are counted here in full, including the ones that produced
nothing**, because counting only the survivors is how a search gets mistaken for a test.

| count | N |
|---|---:|
| the cost-vs-size addendum (re-costing, no cell scored) | 0 |
| the churn feasibility screen — 6 arms × 3 turnover regimes | 18 |
| the decay profile — 6 arms × 26 horizons | 156 |
| the signal anatomy — 3 arms × 26 horizons, with the bar-of-day control | 78 |
| **this check — 2 arms × 3 buckets** | **6** |
| carried from D264 | 45,909 |
| **total** | **46,167** |

**258 fresh looks since D264's result was committed.** That is the honest cost of following a
discrepancy, and it is exactly the count a deflated-Sharpe floor would be computed against if
anything here were ever proposed as a rule.

---

## RESULT — the gate passed, the discrepancy is fully explained, and both numbers were right

`uv run python scripts/run_entry_time_reconciliation.py` · `data/d265_entry_time_summary.json`

### THE VALIDATION GATE FIRST, because it could have voided everything

| | |
|---|---:|
| D264's committed `gross_linear_pa` | **+1.4300%** |
| Arm A, rebuilt from 1,507 individual trades | **+1.4269%** |
| delta | **−0.003 pts**, against a ±0.30 tolerance |

**GATE G PASSES.** The per-trade decomposition reproduces the book to three decimal places, so the
bucket table below describes the same object D264 scored and may be read.

### The bucket table

*Round-trip cost `2c` = 4.00 bp. A bucket clears if its mean P&L per trade exceeds it.*

| bucket | bars | n | share | **Arm A** hold / bp / ×2c | **Arm B** hold / bp / ×2c |
|---|---|---:|---:|---|---|
| **EARLY** | 1–8 | 1,205 | **80.0%** | 20.0 · **+6.28 bp** · **1.57×** | 24.6 · +5.39 bp · 1.35× |
| **MID** | 9–17 | 144 | 9.6% | 12.6 · **−15.68 bp** · −3.92× | 13.0 · −15.43 bp · −3.86× |
| **LATE** | 18–25 | 158 | 10.5% | 4.6 · −3.84 bp · −0.96× | 4.6 · −4.06 bp · −1.01× |
| **ALL** | 1–25 | 1,507 | 100% | 17.7 · **+3.12 bp** · **0.78×** | 21.4 · +2.41 bp · 0.60× |

**The arithmetic closes exactly:** `0.800 × 6.28 + 0.096 × (−15.68) + 0.105 × (−3.84) = +3.12 bp`.
**Twenty percent of the trades destroy a third of the gross**, and MID alone — 144 trades — removes
1.51 bp of the 5.02 bp EARLY contributes.

### The predictions, scored

| | prediction | outcome |
|---|---|---|
| **P-1** | EARLY > LATE in both arms | **CONFIRMED**, and not marginally: +6.28 against −3.84 |
| **P-2** | all-bucket Arm A below the 4.00 bp bar | **CONFIRMED** — 3.12 bp, which is why the book loses |
| **P-3** | Arm B (fixed horizon) beats Arm A (the signal's exits) | **FALSIFIED** — 2.41 against 3.12 |
| **P-4** | the ARM gap explains more of the discrepancy than the BUCKET gap | **FALSIFIED** — arm gap −0.72 bp against bucket gap **9.44 bp** |

**Both falsifications point the same way, and P-4 was registered against my own hypothesis on
purpose.** Entry timing explains the discrepancy by more than thirteenfold over exit discipline. The
entry-time story was right.

**P-3's falsification is a finding in its own right.** The signal's own exits **beat** holding to
the close by 0.71 bp per trade, exiting 4.6 bars early on average. The decay profile suggested the
opposite — that marginal return was still positive when the signal turned off — and at the level of
individual trades it is not. **A conditional-mean profile and a per-trade P&L disagree here, and the
per-trade number is the one that pays.**

### So both original numbers were right

The decay profile's long-hold columns can only contain entries early enough to have that many bars
before the close — which **is** the EARLY bucket. **EARLY clears at 1.57×. The whole book comes to
0.78×.** The profile was correct about early entries; D264 was correct about the average; nothing
was broken.

### AND IT DOES NOT MATTER, WHICH IS THE POINT OF SIZING IT

An EARLY-only book, from this table, is arithmetic rather than a scored run:

| | |
|---|---:|
| trades per symbol per year | 36.5 |
| exposure | 11.2% |
| gross (linear) | **+2.30%** |
| − variance tax *(scaled from D264's measured figure)* | −0.45% |
| − trading cost | −1.46% |
| **= net** | **+0.38%/yr** |

**+0.38% a year.** Against D264's whole-book −0.89%, the entry-time cut is worth about 1.3 points —
real, and trivial.

**And it has to be read against the multiplicity floor.** D218 measured this programme's
deflated-Sharpe noise floor at **+1.42 Sharpe at ~45,800 looks**; the ledger now stands at
**46,167**. A book earning 0.38%/yr at 11% exposure is not within an order of magnitude of clearing
that, and **no arm anyone runs on this fixture can** — which was D218's standing conclusion and
remains it.

### What this licenses

**Nothing enters any book.** Under [R8](../RULES.md#r8) an entry-time rule would need its own
pre-registered out-of-sample test on names or a period this fixture has never touched, and the
three bucket boundaries used here are now spent looks that such a test would inherit.

**What it establishes instead is cleaner and worth more than the candidate:** the discrepancy that
prompted this record is **fully accounted for**, the gate proves the decomposition is faithful to
the book, and the size of the surviving effect is now known rather than guessed. **An idea that
looked like it might be worth a fetch is measurably worth 0.38%/yr.**

---

## Stop — fired

**This record answered one question and stops**, as registered. No entry-time rule is built, no
threshold swept, no fourth bucket, no other arm, no other stratum. The candidate is described and
costed; it is not pursued.
