# D305 — the self-replacing exit, and whether re-entry should be a decision

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## The question

[D304](../../scripts/d304_two_lenses.py) counted it directly:

| | |
|---|--:|
| exits on a name **still in the top 19** | 51.6% |
| exits that **re-entered the same name on the same bar** | **38.0%** (11,493 of 30,222) |
| replacement premium when the departing name had **drifted out** | **+29.29 bp**, t +3.24 |
| replacement premium when it was **still selected** | +9.22 bp, t +0.96 |

**The exit earns where a name has gone stale and does nothing where it has not**,
and over a third of its exits sell a name and buy it straight back the same bar.

## THE THING I NEARLY GOT WRONG, STATED FIRST

**Suppressing a self-replacing exit is NOT a no-op.** Exiting and re-entering
**resets the position's age and its accumulator**:

- the `k`-cap clock restarts, so the name can be held longer in total;
- `cum_x` returns to zero, so the target needs a *fresh* 0.9627 × u move to fire
  again.

Holding through keeps both running. **The holdings are identical on that bar and
diverge from the next one onward.** So this is a rule change with a gross effect,
not a free cost saving, and the study must measure gross and turnover together
rather than assuming one is fixed.

**And Arm S is a new rule shape, not a tweak:** "exit on the target *and* only if
the name has left the selected set" is `target AND NOT selected` — a conjunction
of the price rule with the signal rule, which no cell in D295 or D298 tested.

## The arms

| arm | rule | levels |
|---|---|---|
| **CONTROL** | the adopted rule, unchanged: `excess @ 0.9627`, flat band | 1 |
| **S — suppress** | exit only if the name has also left the top 19; otherwise hold through, age and accumulator running | 1 |
| **C — cooldown** | exit as now, but bar the name from re-entry for `c` bars, forcing the slot elsewhere | c ∈ {1, 3, 5} |
| **R — re-entry bar** | exit as now, and re-enter only if the name is ranked **better than it needs to be to hold** | rank ≤ {5, 10} |

**7 cells.** Everything else inherited: gate 25, 19 slots, k = 5, the D293
triple, D303's adopted rule and multiplier. Nothing re-searched.

**C and R exist because of the principal's point** — the exit rule demonstrably
improves the edge (+12.49 against the control's +7.54, p = 0.005 in three
scorings), so the question is not only "stop the waste" but "should re-entry be a
*decision* rather than an accident of the refill loop". S removes the swap, C
delays it, R conditions it. They are three different answers and only S leaves
the holdings unchanged on the exit bar.

## Statistic

**Gross bp/bar AND turnover, reported side by side**, because the whole point is
the trade between them. Net at the **robust** round trip (106.7 bp, D302), with
the mean figure carried as the truncation artefact it is.

**Nulls:** each cell against its own holding-run-matched null (D303's machinery),
200 draws. **Plus the paired per-bar difference against the control**, which is
the within-book comparison with no nuisance to match.

**And both lenses** (FINDINGS §10): the path-variant book in bp/bar, and the
path-invariant trade ledger scored per trade — never quoted on the same statistic.

## Predictions

Three are against.

| | prediction |
|---|---|
| **Q1** | Arm S cuts turnover by 30–40%, close to D304's 38.0% same-bar re-entry share — a mechanical check that the arm does what it is named |
| **Q2** | **Arm S's gross falls, it does not hold flat.** *Against the obvious reading of D304* — the accumulator no longer resets, so a held-through name is harder to exit later, and the k-cap no longer restarts |
| **Q3** | **Arm S improves NET at the robust round trip.** This is the study's actual question, and the one thing it is for |
| **Q4** | **every cooldown level hurts gross**, monotonically in `c`. D304 measured the cap as a *filter* rather than a tax — removing it lowered the mean trade from +24.2 to +18.1 bp — so the name a cooldown forces the slot toward is worse than the one it displaced |
| **Q5** | the re-entry bar hurts gross more than it saves in cost at both levels, so Arm R is net-worse than Arm S. *Against the principal's suggestion*, and stated that way so it can be wrong |
| **Q6** | **no arm beats the control on GROSS.** All of the available gain is in cost, and any arm that appears to raise gross is doing so through the accumulator reset rather than through better selection |
| **Q7** | the suppressed exits are the low-value ones — S's mean *replacement premium* over the swaps it keeps exceeds the control's +9.22/+29.29 blend |

Q1 and Q3 are load-bearing. **Q1 failing means the arm is not implemented as
described**; Q3 is the decision.

## Decision rule, declared before the numbers

- **S improves net and gross is within 10%** → adopt S. It is strictly less
  trading for the same holdings-on-the-day.
- **S improves net but gross falls more than 10%** → report both and do not adopt
  on net alone; a cost saving bought with edge is the trade this programme keeps
  finding and keeps declining.
- **C or R beats S on net** → re-entry is worth conditioning, and the winning
  level gets its own pre-registered confirmation before adoption.
- **nothing beats the control on net** → the churn is real but not recoverable by
  these three mechanisms, and it closes.

## Assertions

D303's set carries over unchanged — bit-identity of the control cell against
D303's adopted book, the lag audit and its peeking variant, the sign audit, the
market reference cancelling, right quantity, `[5]` every cell a distinct book,
`[C]` cost dimensions against d295's published 52.19, and a self-test that raises
on a book handed free money.

**Two this study adds:**

- **[8] Arm S must suppress exactly the exits D304 counted.** The number of exits
  it removes must match the control's same-bar re-entry count to within 2%, and
  **the arm must not suppress an exit on a name that has left the top 19.**
- **[9] Arm S's holdings must equal the control's on every suppressed bar** — the
  claim that the holdings are unchanged *on that bar* is checkable, and if it
  fails the arm is doing something other than what this record says.

## Scope

**Out:** book width, the holding period, the overlay, the pool axis, and any
change to the entry signal or the gate. **The pool axis in particular is out
because D304 showed it is inert on its own** — a 19-slot book drawing from the
25-name gate is bit-identical to one drawing from the top 19, since a drifted-out
name holds its slot and the bench is never consulted.

## Files

`docs/decisions/D305-the-self-replacing-exit-and-re-entry.md` (this record) ·
runner and data to follow, in separate commits.
