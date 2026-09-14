# D531 ADDENDUM — the breakout loses to the base rate **48 of 48**, and the base rate is **not 50 %**

*2026-09-14/15, on the principal's challenges. Three of my statistics were referenced wrongly and he
caught all three. **This does not close the line** — it establishes that the UNCONDITIONAL breakout
carries nothing, which is a different claim from "no breakout carries anything". Nothing admitted
(R15); in sample only, the 2024+ slice unread.*

---

## 1. The premise checks the story asked for

**CHECK 1 — SIZE: passes, and it survives everything below.** Conditional on an opening-range exit,
the move over the next 60 minutes is **1.6–2.4× the unconditional move of the same length**, at
**5.6–11.4× the round trip** on the candidate roots (NQ 16.4×, against the admitted arm's 3.2×).
**The opening-range exit marks a moment of genuinely elevated movement.** Whatever else fails, this
is a real property of the event and is reusable by anything anchored there.

**CHECK 2 — SHAPE: reported wrongly, three times over.** It was meant to test the inventory-transfer
story's prediction of a hump at 60–120 minutes decaying to the close.

## 2. The three errors, in the order they were caught

**(a) Ties scored as misses.** The test was `sign(move) == direction`, and `sign(0) = 0` never equals
±1, so a move ending exactly unchanged counted as a **miss**. Tie rates run **4.56 % at 15 minutes
falling to ~1 % at 120** — so the artefact pushed the short horizons down and manufactured part of the
"monotone rising to the close" shape I reported. Excluding ties shifts the hit rate **+0.87 points**
on average; NG at 15 min goes 44.62 % → **46.49 %**.

**(b) Up-breaks pooled with down-breaks.** The pooled hit rate averaged two opposite behaviours. Split
out, **ES reads 53.01/52.13/55.08/52.92 on upside breaks against 45.33/45.76/45.81/43.81 on downside
ones** — a 7.7 to 9.3 point spread, on opposite sides of 50 % at every horizon, in **11 of 24 cells**.
Pooling cancelled it to the ~48–50 % I had called "nothing". *"A universe average hides sign flips"*,
for the second time.

**(c) — and this is the one that decides it — the reference was 50 %, and the base rate is not 50 %.**

## 3. The base rate, measured

`P(up move)` at the bar positions where breaks occur, on a **randomly rotated session** — which holds
the clock fixed and therefore absorbs the drift *and* the intraday shape:

| root | 15 min | 30 min | 60 min | 120 min |
|---|---:|---:|---:|---:|
| **ES** | 52.64 | 52.85 | **53.56** | **54.70** |
| **NQ** | 52.68 | 53.13 | 52.94 | **54.39** |
| CL | 50.26 | 50.74 | 50.79 | 50.90 |
| GC | 50.89 | 50.21 | 50.05 | 50.83 |
| SI | 51.24 | 50.77 | 50.16 | 49.95 |
| **NG** | **48.88** | **48.88** | **48.77** | **48.55** |

Estimated independently from the up-break and down-break event sets, the two agree to **0.2 points** —
an internal consistency check the table passes.

**So a 50 % reference is wrong by up to +4.7 points on the equity indices and −1.5 on natural gas**,
and it is wrong in the direction that flatters a long and punishes a short.

## 4. Against the correct reference, the breakout carries nothing

| | |
|---|---|
| mean lift over base rate, 48 cells | **−1.23 points** |
| cells clearing their own p95 | **0 of 48** |
| up-breaks | mean lift −1.21, clears 0 of 24 |
| down-breaks | mean lift −1.25, clears 0 of 24 |

My headline — ES upside breaks at 55.08 %, which I had called "+3.2 SE" against 50 % — is
**+1.53 points over a base rate of 53.56 %, with 18.3 % of rotated draws reaching it.** Inside.

**The direction of a raw opening-range break is marginally worse than doing nothing at that moment.**
This is a much firmer negative than D531's, which compared a pooled hit rate against 50 % and got
"about 50 %" for two wrong reasons that happened to cancel.

## 5. What is NOT established, and why the line stays open

**This measures `P(continuation | breakout)`. A strategy needs `P(continuation | breakout AND
condition)`.** The event supplies the trigger and the timing; the condition has to supply the edge.
That the *average* breakout is uninformative says nothing about whether an identifiable subset is —
and CHECK 1 says the event marks real movement, which is the half a conditioner would exploit.

The conditioners that follow mechanically from the story and are **not** tested by anything above:
the opening range's **volume** relative to its own norm (absorption versus vacuum), its **width**
relative to its own norm (a thin book beyond), and the interaction of the two. D531 tested the volume
gate as a *blanket* filter on all sessions, never as a conditioner on the break itself.

**The principal has not closed this line.** It continues under its own pre-registration.

## 6. Method: the base rate belongs in every directional study here

Recorded as **FINDINGS §74**. Any hit-rate statistic in this repo compared against 50 % inherits an
error of up to 4.7 points, root-specific and horizon-dependent. D529's rotation null happens to
control for it — rotating a signal against a fixed price path preserves the drift — but a naive
comparison does not, and the admitted arm is long-biased in a rising sample.

---

Reproduced by [`working/orb_premise_checks.py`](../../working/orb_premise_checks.py),
[`working/orb_check2_diagnostics.py`](../../working/orb_check2_diagnostics.py) and
[`working/orb_drift_control.py`](../../working/orb_drift_control.py).
