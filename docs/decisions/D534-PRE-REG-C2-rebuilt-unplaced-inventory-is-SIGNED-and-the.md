# D534 — PRE-REGISTRATION: C2 rebuilt. **Unplaced** inventory is SIGNED, and the statistic is the **gross mean per trade**

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D534-PRE-REG-C2-rebuilt-unplaced-inventory-is-SIGNED-and-the-statistic-is-the-gross-mean-per-trade.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.**
**In sample 2016-01-04 → 2023-12-29. The 2024+ slice is RESERVED AND NOT READ.** Nothing admitted (R15).

*On the principal's instruction, 2026-09-15: "if someone needs to get rid of inventory in the morning
why would they be accepting it at night?"*

---

## 0. Why D533's C2 could not have worked, independent of its result

D533's C2 was `log(night volume / night range)`, top tercile. **That state is consistent with two
opposite mechanical stories:**

- **completed transfer** — the inventory found its buyer overnight, so nothing is left for 09:30, and
  the break should NOT continue;
- **willing absorber** — a dealer took the whole lot and must shed it at the open, so everything is
  left for 09:30, and the break SHOULD continue.

**An observable consistent with both continuation and reversion has no predictive content.** That is
the diagnosis, and it is not a sign error. What separates the two readings is whether the absorber was
*willing*, and willingness shows up in **price**: absorbing while price holds still means well
compensated; absorbing while price runs against you means run over. Volume alone cannot see it.

**And the larger defect: C2 was an unsigned magnitude tercile applied identically to up- and
down-breaks.** An inventory position is long or short. The same night state makes an up-break and a
down-break different trades, so even a correct mechanic could only have been diluted — half the
qualifying sessions point the wrong way by construction. This is D531's pooling error in a new place.

**What D533's C2 measured: nothing.** −0.21 and −0.77 points against unfiltered, against an SE on a
rate difference at n≈1,250 of roughly 1.2–1.4 points. Both inside one SE. It separated nothing in
either direction, which is what an ambiguous observable should do.

## 1. The mechanism, stated so it can fail

**Who carries inventory into the US open:** overnight market makers quoting a thin Globex book who
accumulate against directional flow they cannot lay off until depth arrives; basis and hedging desks
that can only unwind when the cash market opens. The unifying feature is that they accumulate
**unwillingly** and unwind **when liquidity arrives at the open**.

So the state that means *someone is stuck* is:

> **price displaced materially overnight, and it was CHEAP to displace** — nobody stood there at a
> good price, so whoever took the other side did it unwillingly and still holds it.

They are short if the night ran up. They buy at the open. **So the day should continue in the
direction the night already moved.**

## 2. C2′, declared

All three parts from `fut_breadth_hourly.csv.gz` (hourly O/H/L/C/V, session 18:00→16:59 ET), night =
**h18 → h08**, which ends exactly where the 5-minute day session begins at 09:00 ET. **No new data.**

| | definition |
|---|---|
| **drift** | `z = log(C[h08] / O[h18])` ÷ its own trailing 50-session sd (`min_periods=25`) |
| **thin** | `log(night volume)` less its trailing 50-session mean **< 0** — below its own normal |
| **sign** | the break's side **relative to `sign(z)`**: **WITH** or **AGAINST** |

**Gate:** `|z| > 1.0` (materially displaced) **and** `thin` (cheaply displaced).
Thresholds are declared here and are not tuned afterwards.

Breaks, sessions, the opening range (first 6 bars), the entry at the bar after the break and the
both-sides skip are **D531's, unchanged**. **Exit: the fixed 60 minutes (12 bars) only.** No exit
rule is tested in this record — D533 established that an exit scored on entry statistics answers the
wrong question (FINDINGS §75), and mixing one in again would repeat it.

## 3. The statistic — the gross mean per trade, which is what a signal is

**D533's lesson applied: the hit rate is not the thing being claimed here.** A signal in this
programme is a **positive gross mean per trade above the nulls**, and C1 is currently sitting inside
a hit-rate null while its dollar quantity has never been nulled at all. This record nulls the dollar
quantity.

**Dollars are computed by the runner at minimum tradable size** (MCL $100/pt, MGC $10/pt, SIL
$1,000/pt, MNG $1,000/pt) under the pre-registered measured round trip (**$4.00 CL, $5.00 GC, $8.00
SI, $5.00 NG**).

**Roots normalised before pooling.** SI's gross per trade ran 5× CL's in D533, so a dollar pool is an
SI pool. Each trade's gross P&L is divided by **that root's own per-trade sd over the in-sample
window**, and the four roots are **equal-weighted**. Dollars per root and pooled are reported beside
it, and so is net, but they are not the primary.

> **PRIMARY: the CONTRAST — mean(WITH) − mean(AGAINST) in per-root σ units, equal-weighted over
> CL/GC/SI/NG, gated on `|z| > 1` AND `thin`, at the 60-minute fixed exit.**

The contrast is the primary rather than the WITH cell alone because **it is internally referenced**:
both sides are breaks on gated nights, so anything that lifts breaks generally — drift, volatility,
the session's own profile — cancels. A tercile against a base rate does not do that, which is what
made D533's C2 unfalsifiable in practice.

## 4. Nulls — what each destroys, and what it preserves

**N1 — the night-state rotation.** Per root, cyclically rotate the night-state vector `(z, thin)`
**as a coupled pair** by a random offset, so session *i*'s night is attached to session *j*'s day.

- **Destroys:** the link between the night and the day that follows it — the claimed ingredient, and
  nothing else.
- **Preserves:** the day's break structure and its moves, the night state's own distribution and
  serial correlation, and the coupling between displacement and volume.

1,000 draws. A cyclic rotation rather than a permutation, because night drift is autocorrelated and a
permutation would destroy that too — a control must break the claimed ingredient and nothing more.

**N2 — the family maximum.** **The family is the 6 pooled contrast cells:** {gate = drift+thin, drift
only} × {30, 60, 120 minutes}. One rotation offset per root per draw, common to every cell, so the
family's correlation survives. **Per-root and per-side numbers are diagnostic and may never be
promoted** — committed here, not judged afterwards.

**PASS requires: the primary contrast > 0, clearing its N1 p95, AND the family maximum clearing N2.**

## 5. Predictions, in the runner's own quantities

- **P-1 (primary).** contrast > 0 and above the N1 p95.
- **P-2.** `mean(WITH)` exceeds the **unfiltered** break's gross mean per trade — the gate must add
  something, not merely sort.
- **P-3 — THE DISCRIMINATING ONE.** **drift + thin beats drift alone.** If the thin gate adds
  nothing, this is not an inventory story at all: it is plain overnight-to-day momentum, a different
  and already-known mechanism, and it would have to be recorded as such. The thin gate is the *only*
  thing that makes this about unwilling absorption.
- **P-4 — the falsifier.** If `mean(AGAINST) ≥ mean(WITH)`, the mechanism is inverted: a displaced
  thin night predicts the day *fading* it, which would be a reversion story and not this one.

## 6. Premise checks that run BEFORE anything is scored, and can stop the record

1. **[F] alignment.** The night must be the one that PRECEDES the scored session. Assert the
   correlation between `C[h08]` on day D and the day5m session's first open on day D is > 0.99 and
   the median gap is under one session's range — if the night is off by a day, everything else is
   noise.
2. **Duty cycle.** Report n per cell and the WITH/AGAINST split. D533's duos thinned to ~400 trades;
   **a cell under 200 trades is not scored**, and a degenerate cell has beaten a rotation null here
   before.
3. **Coverage.** Print `finite n of m` for `z` and for the volume deviation, per root, and **raise**
   if the primary's gate selects nothing — the `min_periods` trap emptied D533's C2 silently.

## 7. What a pass would mean

A **candidate**, not a component, and not an admission. The component line (C-a…C-e, in dollars at
minimum size under the cost that size pays, with its correlation against the ledger) is computed by
the runner whatever the outcome.

**The reserved slice is not read by this record under any outcome.**
