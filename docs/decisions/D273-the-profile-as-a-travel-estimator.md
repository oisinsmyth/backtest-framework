# D273 — The volume profile as a travel estimator

**Status:** **RUN AND CLOSED.** The mechanism is falsified directly, not merely unproven.

**Everything above the RESULT heading was committed in `241c304`, BEFORE the runner was written.**
**Date:** 2026-09-01
**Area:** Strategy research · **personal track**

---

## The claim, and it is the principal's

> *"If we get a short signal and we are just above a support that could be a breakdown? Or if
> we are near some resistance we might guess that the price will fall to the next support?"*

**Conditional on a short signal having fired, does the room below — the distance to the next
high-volume node — predict how far the trade travels?**

## Why this is a different question from D272, and not a re-entry to its stop

[D272](D272-the-volume-profile-as-a-positional-input.md) closed the profile **as an input**: a
standalone score, quintiled unconditionally, asked whether it predicts forward returns. Its stop
forbids a fifth such score.

**This asks something else.** Not *"does the score predict direction"* but *"conditional on a
signal, does the room predict magnitude"* — a target estimator in a different functional role.
**And magnitude is the only thing that matters**, because [D265](D265-the-entry-time-reconciliation.md)
reduced the entire cost problem to `mean move per trade ≥ 2c`, in which the trade count cancels
and hit rate never appears.

**It is also the first construction in this programme that could make selectivity work.**
[D267](D267-the-magnitude-calibration-screen.md) killed selection on *signal strength*. This
selects on *available travel*, which D267 never tested.

**The stop question was put to the principal explicitly and they called it a new construction.**
Recorded so the decision is visible rather than assumed.

## The terrain evidence points TOWARD this, which is the reverse of D272

`TERRAIN_RESULTS.md`'s mechanism, restated:

> Inventory accumulates below price exactly when price has been *falling into* it, so trading it
> **fades a decline**. Fading lost 16/16, 16/16, 8/8, **11 years of 11**.

**They were fading — buying support and expecting a bounce. This shorts into the gap and targets
the next node, which is continuation.** Terrain's four negatives are evidence *for* this
direction, not against it, and D272's prediction X-c declared exactly that continuation shape
before failing to reach a test.

---

## Construction

**Signals:** the committed short books, unchanged — `S1_short_intra` and `S2_short_intra`.
**Profile:** D272's sensor and constants exactly — lookback 180 bars, `bucket_atr` 0.5,
`atr_window` 182, units `shares`, rebuilt once per session. **Nothing is re-tuned.**

```
room_down = (entry price − highest HVN strictly BELOW entry price) / ATR
```

Already ATR-normalised, because `bucket_width = 0.5 × ATR`. A trade with no mapped HVN below is
**excluded and counted**, never bucketed as zero — an unmapped level is not a near one.

**`resistance_above` is NOT tested**, and the omission is deliberate. It is an *entry-quality*
claim ("is this a good place to short"), whereas the cost bar is a *travel* bar. Adding it would
double the cells to answer a different question. Named here so its absence is a choice.

**Outcomes.** The hurdles run on **realised P&L per trade**, because that is what pays. **Maximum
favourable excursion** and **the rate at which price actually reaches the mapped support** are
reported as diagnostics — they say *why*, and they are not hurdled.

---

## THE CONTROL, and it is the reason this design exists

**Node spacing scales with ATR by construction.** "Lots of room" may simply mean "high ATR", and
high ATR trivially means large moves. That would produce a strong relationship that is volatility
restated.

**This programme has been caught by exactly that twice in two days:** `rel_vol` turned out to be a
volatility selector (D270), and `mass_imbalance` turned out to be `impulse_md` at ρ = −0.83
(D272). **So the control is a hurdle, not a robustness check.**

| | standard |
|---|---|
| **T1** | **Monotone** mean P&L across `room_down` quintiles |
| **T2** | **Top quintile mean P&L ≥ 2c** — 4.00 bp LOW, 12.84 bp HIGH, 8.42 bp ALL |
| **T3** | **Beats a shuffle floor** — `room_down` permuted across trades within symbol, best-of-N with one shared draw |
| **T4** | **SURVIVES THE ATR CONTROL** — trades split into ATR terciles, then quintiled on `room_down` *within* tercile. The top-minus-bottom spread must be **positive in at least 2 of 3 terciles** |

**All four.** T4 is the one that separates a travel estimate from a volatility restatement.

**Cells: 2 arms × 3 strata = 6.** Trade counts per quintile are reported so thinness is visible;
LOW:S2 has only ~1,500 trades, so its quintiles hold ~300 each.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **Y-a** | **`room_down` predicts realised P&L monotonically in at least one cell** — the mechanism is plausible and untested | **moderate** |
| **Y-b** | **The effect does NOT survive T4.** Room and ATR are mechanically linked, and this programme has been fooled by exactly this twice in two days | **moderate-high** |
| **Y-c** | **No cell clears all four** | **moderate-high** |
| **Y-d** | **MFE shows a stronger relationship to `room_down` than realised P&L does.** If so, the profile predicts *travel* while the exit rule fails to capture it — which would point at the exit, not the entry, and is the most actionable thing this study could produce | **moderate** |

**Y-d is the one worth being right about**, because it is the only outcome that names a fix
rather than closing a door.

---

## Stop

**If no cell clears all four, the profile is closed as a travel estimator** — no second room
definition, no alternative node quantile, no third arm, no re-cut quintiles. Together with D272
that closes the volume profile on this fixture entirely.

**If T1–T3 clear and only T4 fails, the verdict is "it is ATR"** and is reported in those words —
not as a near miss.

**Nothing is promoted under any outcome.** R8 governs.

---

## Ledger

| count | N |
|---|---:|
| fresh — 2 arms × 3 strata | **6** |
| + MFE and target-reached diagnostics | 12 |
| carried from D272 | 46,221 |
| **total** | **46,233** |

**Terrain's 259 remain disclosed and not summed**, on the reasoning D272 settled: multiplicity
corrects for looks at the same hypothesis, and this is not that hypothesis.

---

## RESULT — the profile predicts whether price *reaches* a level, and that is arithmetic

`uv run python scripts/run_travel_estimator.py` · `data/d273_travel_summary.json`

**Zero of six cells clear all four hurdles.** But the interesting part is not the hurdle table.

### The two measurements, side by side

**Whether price reaches the mapped support — monotone falling in ALL SIX cells:**

| cell | Q1 (least room) | Q2 | Q3 | Q4 | Q5 (most room) |
|---|---:|---:|---:|---:|---:|
| ALL S1 | **62.6%** | 39.0% | 20.0% | 9.0% | **1.3%** |
| ALL S2 | **75.6%** | 57.7% | 50.0% | 31.2% | **12.4%** |
| HIGH S1 | 64.2% | 38.7% | 21.8% | 10.3% | 1.4% |
| LOW S2 | 74.8% | 58.9% | 45.3% | 25.2% | 11.9% |

**Six of six monotone, with a 60-point separation.** Nothing else in this programme has produced
an ordering that clean.

**And maximum favourable excursion — how far the trade ACTUALLY TRAVELS — is flat:**

| cell | Q1 | Q5 | **Q5 − Q1** |
|---|---:|---:|---:|
| ALL S1 | 56.6 bp | 55.7 bp | **−0.9 bp** |
| HIGH S1 | 87.1 bp | 78.0 bp | **−9.1 bp** |
| LOW S1 | 30.3 bp | 33.9 bp | +3.6 bp |
| ALL S2 | 81.7 bp | 91.1 bp | +9.4 bp |
| LOW S2 | 48.5 bp | 56.7 bp | +8.2 bp |
| HIGH S2 | 117.4 bp | 128.4 bp | +11.4 bp |

**No trend, on bases of 30 to 138 bp.** Trades with five times the room travel the same distance
as trades with almost none.

### THE FINDING, and it falsifies the hypothesis rather than failing to support it

**Travel is roughly constant. So whether price reaches a level depends only on how far away the
level is.**

The 62.6% → 1.3% ordering is not the profile predicting anything — it is the arithmetic of a
fixed-length move against a variable-distance target. **Any distance measure would reproduce it,
including a randomly placed level.** The node is a location, not a barrier and not a magnet.

**So the claim under test — "if there is room below, the short will travel to the next support"
— is measured and it is false.** The room does not determine the travel; the travel is set
elsewhere and the room only determines whether that travel happens to cross a line we drew.

### The predictions, scored

| | outcome |
|---|---|
| **Y-a** room predicts P&L monotonically in ≥1 cell | **FALSIFIED** — 0 of 6 monotone |
| **Y-b** the effect fails the ATR control | **PREMISE DID NOT ARISE.** There is no effect to control, and my confound worry was unfounded: **ρ(room, ATR) runs −0.005 to −0.076**. The ATR normalisation in the sensor's bucket width already handled it |
| **Y-c** no cell clears all four | **CONFIRMED** |
| **Y-d** MFE tracks room more strongly than P&L does | **FALSIFIED.** MFE is flat. This was the outcome that would have pointed at the exit rule rather than closing a door, and it is not there |

### One structural observation worth keeping

**Half of S2's trades have no mapped support below the entry price at all** — 50%, against 5% for
S1. S2 shorts confirmed downtrends, so by the time it fires **price has usually already fallen
through everything the profile mapped.** The terrain mechanism showing up as a census fact rather
than a result: inventory sits above a downtrend, not below it.

---

## Stop — fired

**The volume profile is closed as a travel estimator**, and with
[D272](D272-the-volume-profile-as-a-positional-input.md) that closes the volume profile on this
fixture entirely — as an input and as a target estimator both. No second room definition, no
alternative node quantile, no third arm.

**And the closure is stronger than the usual one here.** Most stops in this programme fire because
an effect is too small to pay. **This one fires because the mechanism was measured and is absent:
the distance to the next node does not predict how far price goes.**

---

## ADDENDUM — the assertion, now measured. R6 defect closed.

**The result section above claimed "any distance measure would reproduce it, including a randomly
placed level" and never computed it.** That is a claim asserted rather than measured — the R6
defect — and the principal was right to press on it. `scripts/d273_halt_test.py`.

### What D273 could not distinguish, and what this can

`P(reach a level at distance d)` **is** `P(MFE ≥ d)`, which does not depend on *what* sits at that
price. **So the 62.6% → 1.3% ordering genuinely cannot tell an HVN from a random line, and that
half of the reading stands.**

**What it could not see is whether the excursion STOPS there.** `MFE / d_hvn` piles up at 1.0 if
the node halts price and passes smoothly through if the node is only a location. That distinction
is realisable, because the level's price is known in advance.

| | | | | |
|---|---|---|---|---|
| **H1** | density of `MFE/d` in [0.9, 1.1] | > | shuffled null p95 | *does the excursion pile up on the node* |
| **H2** | median overshoot among reachers | < | null's | *do reachers stop rather than run through* |

### The first null was confounded, and R7's corollary caught it

**H2 passed six of six.** Under R7 — *"a hurdle that everything clears is not evidence, it is a
broken hurdle"* — that is a tell, not six findings.

**The cause:** `d` here is a **raw** log distance, not D273's ATR-normalised `room_atr`, so it
scales with volatility and so does MFE. A plain within-symbol shuffle pairs a high-volatility MFE
with a low-volatility distance, inflating the null's overshoot for a reason with nothing to do with
nodes. **Re-run with the shuffle stratified within symbol × distance tercile**, which preserves the
distance–volatility pairing and destroys only the node-specific one.

### The result, under the corrected null

| cell | n | in [0.9,1.1] | null p95 | H1 | overshoot | null | H2 |
|---|---:|---:|---:|---|---:|---:|---|
| ALL S1 | 10,486 | **3.357%** | 3.930% | no | 1.301 | 1.369 | yes |
| LOW S1 | 5,402 | **3.369%** | 4.018% | no | 1.378 | 1.397 | yes |
| HIGH S1 | 5,084 | **3.344%** | 4.053% | no | 1.280 | 1.348 | yes |
| ALL S2 | 1,492 | 5.429% | 5.027% | **yes** | 1.803 | 1.794 | no |
| LOW S2 | 754 | 5.305% | 5.305% | no *(dead tie)* | 1.869 | 1.884 | yes |
| **HIGH S2** | **738** | 5.556% | 5.420% | **yes** | 1.691 | 1.715 | **yes** |

**One cell of six clears both — and it should not be believed.** It has the **smallest sample**
(738), its margin is **0.14 percentage points on a 5.4% base**, which is about **one trade**, and
**the same arm ties on LOW and fails H2 on ALL.** An effect that reverses across strata of the same
signal is not an effect.

**And S1 runs the other way in all three strata:** 3.34–3.37% against nulls of 3.93–4.05%. **The
excursion is LESS likely to stop at a node than at a random distance.**

### Verdict

**The node does not halt price.** D273's assertion was substantively correct, and it is now
measured rather than asserted.

**A limitation of this addendum, stated:** the stratum is the distance's own tercile, a *proxy* for
volatility rather than a measured ATR. It removed enough of the confound to drop H2 from 6/6 to
4/6, so it is doing real work — but a purpose-built volatility stratifier would be better, and
that is not run because the answer is not close.
