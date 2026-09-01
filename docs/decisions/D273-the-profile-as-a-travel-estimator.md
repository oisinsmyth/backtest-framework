# D273 — The volume profile as a travel estimator

**Status:** PRE-REGISTERED. Committed **before the run**. Nothing here is a result.
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
