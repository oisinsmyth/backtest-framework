# D532 — PRE-REGISTRATION: does a **condition** separate the breakouts that continue? Absorption versus vacuum

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D532-PRE-REG-does-a-condition-separate-the-breakouts-that-continue-absorption-versus-vacuum.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.**
**In sample 2016-01-04 → 2023-12-29. The 2024+ slice is RESERVED AND NOT READ.** Nothing admitted (R15).

*On the principal's instruction, 2026-09-15: "what you have is the probability a breakout will
happen, but for a strategy we need the probability a breakout happens GIVEN some condition."*

---

## 0. What the D531 addendum settled, and what it left open

**Settled:** the *unconditional* break carries nothing. Against the rotated base rate the mean lift is
**−1.23 points across 48 cells and 0 of 48 clear**. Referencing 50 % — which is wrong by up to
4.7 points (FINDINGS §74) — had made it look like an asymmetry.

**Left open, and it is the whole strategy question:** the event supplies a **trigger and a clock**;
a condition has to supply the **edge**. And CHECK 1 established the event is worth conditioning on —
the move after a break is **1.6–2.4× the unconditional move**, at **5.6–11.4× the round trip**. The
raw event has size without direction. This record asks whether a declared condition supplies the
direction.

## 1. The mechanism being tested, stated so it can fail

The opening range is where overnight inventory is transferred. The same range width means opposite
things depending on how much traded to build it:

- **Low OR volume** → little was absorbed → **the book beyond the range is thin** → a break continues.
- **High OR volume** → somebody large stood there → **a break is defended** → it reverts.

This is not a sweep for a filter. It is one mechanism with a **sign prediction on each side**, which
is what makes the dose-response below a real test rather than a search.

## 2. The conditioners, declared

All computed from the opening range only, therefore **known before the break** and causal:

| | definition |
|---|---|
| **V** — OR volume regime | `log(EMA_10(OR_vol) / SMA_50(OR_vol))` over sessions, same root |
| **W** — OR width regime | `log(EMA_10(OR_range) / SMA_50(OR_range))`, same form |
| **V×W** | the 2×2 of their terciles; the story's cell is **narrow W, low V** |

`V` is the principal's construction. Comparing today's opening range to previous opening ranges is
**time-of-day-matched by construction**, which is why this form needs none of the normalisation D528
required on 5-minute bars, where NQ's median volume swings 14.5× across the session.

## 3. The PRIMARY, declared before the run

> **PRIMARY: `V` in the LOW tercile, 60-minute horizon, pooled over CL/GC/SI/NG, both sides
> sign-adjusted — measured as LIFT OVER THE ROTATED BASE RATE.**

60 minutes because CHECK 1 put cost coverage at 9.5× there. The candidate roots are non-index because
an index arm beside the admitted NQ arm is a closure offence under the one-direction rule, not merely
a C-b failure.

**Secondary, and the sharper test: the DOSE-RESPONSE.** The mechanism predicts
`lift(low V) − lift(high V) > 0`. A single tercile clearing could be selection; a monotone ordering
across terciles, on the side the mechanism names, could not as easily.

## 4. Reference, nulls and the pass rule

**Reference: the rotated base rate**, never 50 % — hold the bar index fixed, draw the move from the
same bar on a different session. This absorbs the drift and the intraday profile together
(FINDINGS §74). **Ties are excluded, not scored as misses** — that error cost up to 2 points at the
short horizons in D531.

**Up-breaks and down-breaks are reported SEPARATELY** and only pooled after sign adjustment. Pooling
them raw cancelled a 9-point spread in D531.

- **N1** — per cell: the rotated base-rate distribution, 1,000 draws. A cell clears if its lift
  exceeds the p95 of that distribution.
- **N2** — family maximum over **every** cell computed (all conditioners × terciles × sides ×
  horizons × roots), one rotation per draw common to all cells so the family's correlation survives.

**PASS requires: the PRIMARY clears N1, the family maximum clears N2, AND the dose-response has the
predicted sign.** All three. Two of three is reported as not passing.

## 5. Predictions, written so they can be wrong

- **P-1 — the dose-response is positive**: low-V breaks continue better than high-V breaks. If it is
  **negative**, the absorption/vacuum mechanism is inverted and the story is wrong in the way that
  matters.
- **P-2 — W adds less than V.** Width is a proxy for how much was absorbed; volume measures it
  directly. If W dominates, the mechanism is about *range* rather than *transacted quantity*, which
  is a different story and would need its own record.
- **P-3 — the effect, if any, is larger on the non-index roots**, because ES and NQ carry the large
  directional base rate that FINDINGS §74 measured, and a conditioner has more room where the base
  rate is near neutral.

## 6. What a pass would and would not mean

A pass makes this a **candidate**, not a component. C-a through C-e in `COMPONENTS_PROP.md` are scored
by the runner in dollars at minimum tradable size under the cost that size pays — which for these
roots is **$4.00 CL, $5.00 GC, $8.00 SI, $5.00 NG**, from the measured median spreads, not a flat
assumption.

**The reserved slice is not read by this record under any outcome.**
