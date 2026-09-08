# D382 RESULT — Stage 0: the reclaim is worth LESS than no reclaim, and the apparent edge was the event bar itself

**Status:** RESULT. Stage 0 only. **NO NULL WAS RUN. STAGE 1 IS NOT AUTHORISED AND WAS NOT RUN.**
**Date:** 2026-09-08 · **Area:** signal research · **personal track**
Pre-registration: [D382](D382-the-undercut-and-reclaim.md), committed before the runner existed.
Runner: `scripts/run_d382_undercut_reclaim.py` · Artifact: `data/d382_stage0.json`
**Build (R16):** today's panel, `load_ragged(dividend_bound=True)`. Nothing inherited.

**Holdout reads spent: 0. Programme total: 1** (D371).

---

## 0. The verdict

**H3 fails by SIGN, not by margin, and no null was needed to establish it.**

| hedged forward-20 drift, per name-bar, **starting at t+1** | n | mean | median |
|---|--:|--:|--:|
| **the event — undercut and RECLAIM** | 143,985 | **+6.0** | +1.6 |
| **the B_r pool — undercut and closed BELOW** | 446,462 | **+13.5** | +9.3 |
| all undercuts | 590,447 | +11.7 | +7.2 |
| **reclaim − no-reclaim** | | **−7.6 bp** | |

**A name that takes out a fresh pivot low and closes back above it goes on to do WORSE than one
that takes out the same level and closes below it.** The pre-registration's §8 stop clause fires:
*"H3 fails → the level is the signal and the reclaim is decoration. Record it and stop."* It is
worse than *inside* `B_r` — it is on the wrong side of it.

---

## 1. The correction that decided the record, and how it was caught

**The first execution reported reclaim − no-reclaim = +110.5 bp.** That number was an artifact of
the diagnostic's alignment, and the sequence that caught it is the point:

1. **Q2 was FALSIFIED first.** The pre-registration predicted 5,000–60,000 events and declared
   *"a count outside that means the event definition is not what I think it is, and the record
   checks the definition before reading any P&L."* The run produced **144,657**.
2. **Checking the definition surfaced the alignment.** `r1T[t]` is the return earned **during** bar
   t. D361's `forward20` pairs it with a gate lagged to t−1, where that is correct. **This study's
   event is known only at bar t's close — and its two arms are DEFINED by where that close sits:**
   the reclaim arm closes above its level, the pool arm below it.
3. **So including bar t's return hands the reclaim arm an up-day and the pool arm a down-day by
   construction.** The forward window now starts at **t+1**, where the kernel's next-open entry
   starts, and the runner prints both:

```
starting t+1 (the money):        -7.6 bp
starting t   (the definition): +110.5 bp
the artifact:                  +118.1 bp
```

**The entire apparent edge, and then some, was the event's own definition.** This is D279's error
in a new place — *the quantity is lagged correctly in the kernel and the diagnostic beside it is
not* — and it is the third time in this programme a lag has decided a verdict.

**The runner now asserts the alignment matters** (`[LAG]`: the unlagged read must differ), so the
choice is demonstrated rather than assumed.

### A defect of mine, disclosed

**The first execution also died with a `KeyError` in its print loop** — D371's exact failure — and
it did so in the file whose own assertion list contains *"[P] the JSON is persisted BEFORE it is
rendered."* I had written the assertion and then placed the write *after* the section-4 prints.
Fixed; the write now precedes every print that reads the ledger, and the run was recoverable only
because the pivots were cached.

---

## 2. Stage 0's other three readings

**1. Exposure — Q1 held, emphatically.** 144,657 events over 4,124 bars = **35.08 entries a bar.**

| cap | 5 | 10 | 20 | 40 | 60 |
|---|--:|--:|--:|--:|--:|
| open positions on the average bar | 175 | 351 | **701** | 1,403 | 2,105 |

**At the primary cap of 20 the book would hold ~701 names against ~700 eligible: it is the
universe.** This is not a flat-by-default sleeve and never could have been — D358's arithmetic
again, on a structural event rather than a cross-sectional one.

**2. The split.** 24.4% of qualifying undercuts reclaim. Both arms are large; the control had a
population, which is what §2 asked.

**3. The ledger at cap 20**, reported because it was computed, **and it is not evidence:**
61,835 trades, mean **+43.02** bp, median **+31.13**, win 51.8%, t **+10.47**; symmetric 1% trim
**+39.18** (the honest one — ex-top alone is +0.58 and ex-bottom +81.66, and dropping only winners
always frightens on a two-sided book). **Top trade GME, entered 2021-01-08, +30,814 bp = 1.2% of
the ledger.** Deployed PUB hedged: gross **+1.988** bp/bar, net **−4.041**.

**Why +43.02 is not evidence, and the mirror says so plainly:** the **short** mirror — a failed
breakout, `high > last_high` and `close < last_high` — earns **+43.73 bp per trade over 67,397
trades**, a mean indistinguishable from the long's. **Two opposite constructions on opposite
signals earn the same thing**, which is what a 20-bar hold on this universe pays before any
control. Neither number is a signal; that is the whole reason `B_r` exists and why §2 is read
before §4.

---

## 3. Predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | *(against)* exposure ≥ 90% — not a flat sleeve | **HELD** — 701 open positions of ~700 eligible |
| **Q2** | 5,000–60,000 trades | **FALSIFIED** — 144,657 events. **And it did its job**: it forced the definition check that found the lag |
| **Q3** | *(load-bearing)* the book beats `B_r`'s p95 | **FALSIFIED BY SIGN** — −7.6 bp, on the wrong side before any null |
| **Q4** | `mean > median > 0` | **HELD** (+43.02 > +31.13 > 0) — on a ledger whose premise had already failed |
| **Q5** | top trade ≤ 10% | **HELD** — 1.2% |
| **Q6** | *(against)* the short mirror fails its controls | **NOT TESTED** — no controls were run on it. It earns +43.73, and that fact is used only as evidence about the *base rate*, not about §33 |
| **Q7** | ρ to S1/S2 below 0.3 | **NOT REACHED** |

**Five of seven scored. The load-bearing one failed, and the one that failed first is what made the
result trustworthy.**

---

## 4. What this closes, and what it does not

**CLOSES:** the undercut-and-reclaim as a long candidate on this fixture, in the form §1 froze.
The reclaim does not carry information beyond the level — **it carries less.**

**DOES NOT CLOSE, and none of it is proposed here:**

- **The B_r pool as a SHORT.** Names that undercut a fresh pivot and close below it earn **+13.5 bp**
  over 20 bars — *positive*, so that is not a short either. Both arms rise; the whole undercut
  population drifts up at +11.7. **FINDINGS §39's finding again — on this floored universe the
  beaten-down pool rises** — and it is stated as consistency, not identity.
- **The undercut DEPTH profile**, which §1 declared owed and not run. A deeper undercut is a
  different event; this record scored *any* undercut and says so.
- **The structure × intrabar cross in general.** One two-part condition was tested. §4.4 of
  `docs/research/the-signal-hunt-part2.md` named others.
- **Only the principal closes a research avenue (R15).**

---

## 5. What is worth carrying

1. **A diagnostic beside a correctly-lagged kernel is not automatically lagged.** The ledger here
   was right all along — D340's next-open fill — and the number that would have been reported as
   the finding was wrong by **+118 bp**. **Every forward-drift read paired with a close-defined
   event must start at t+1**, and the runner should assert that the choice changes the answer.
2. **A count prediction is worth writing.** Q2 looked like bookkeeping and it is what caught the
   defect: 144,657 against 5,000–60,000 forced a definition check before any P&L was read, exactly
   as the pre-registration instructed.
3. **`last_low` from `market_structure` is not a scarce level.** 24% of eligible name-bars undercut
   one. The state machine updates it on every confirmed pivot, so in a downtrend "below the last
   pivot low" is nearly continuous — **it is a moving average of lows wearing a structural name**,
   and any future study using it must state the base rate first.
4. **Two opposite constructions earning +43 bp is a base rate, not two signals.** Where a long and
   its mirror both pay the same, the number belongs to the hold and the universe.

---

**Status footer.** No null was run. Stage 1 was not run and is not authorised. `docs/BOOK.md`
holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty. Nothing in this record is a
signal (R15).
