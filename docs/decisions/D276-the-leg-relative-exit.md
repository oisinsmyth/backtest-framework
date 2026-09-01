# D276 — The leg-relative exit

**Status:** PRE-REGISTERED. Committed **before the run**. Nothing here is a result.
**Date:** 2026-09-01
**Area:** Strategy research · **personal track**

---

## Why

[D275](D275-the-change-of-character-on-single-names.md) measured the largest capture gap in this
programme: **the post-CHoCH down-legs run a median 182.7 bp and 99.1% of them exceed the cost bar,
while the tradeable arm captured +0.57 bp — three tenths of one percent.**

**The mechanism was turnover: 474 round trips a year at 47% exposure.** At `k = 2` on 15-minute
bars the trend state flips constantly, so the book churns *around* the legs instead of riding them.

D275's stop forbade an alternative exit **and named this as the construction that would need its
own registration.** This is that registration.

## What is being changed, and it is only the exit

**The entry is D275's, unchanged: a `CHOCH_DOWN` event at `k = 2`.** The rule differs in one
place — **hold the leg, not the state.**

```
enter   short at the bar after CHOCH_DOWN fires          (lag 1)
exit    at the first bar where the state machine emits a NEW Leg
        -- i.e. when the leg's end pivot CONFIRMS -- or at the
        session close, whichever comes first
```

**This is causal and parameter-free.** The leg's end pivot at `end_index` confirms at
`end_index + k`, so the exit bar is knowable in real time. `structure.Leg` is deliberately built so
that *"nothing may be measured against a leg whose end is still in the future"*, and that property
is what makes this rule tradeable rather than a hindsight target.

**No target, no stop, no threshold.** One exit condition, taken from the machinery that already
defines the leg.

---

## THE HURDLE THAT CAN KILL IT, and it is not the cost bar

[D274](D274-the-exit-timing-diagnostic.md) tested time-based exits on S1 and S2 four hours ago and
found **a random exit bar beats a fixed one** — 6.29 bp against 3.64 at k=10, 7.45 against 3.74 at
k=16. That is [R7](../RULES.md#r7)'s finding reproduced: **the exit trigger carried no
information.**

**So the leg exit must beat a matched random exit, not merely beat the state rule.** Beating the
state rule only shows that less churn costs less, which is arithmetic.

| | standard |
|---|---|
| **L1** | **Mean move per trade ≥ `2c`** — 4.00 bp LOW, 12.84 bp HIGH, 8.42 bp ALL |
| **L2** | **BEATS THE R7 MATCHED-EXIT NULL** — exiting at a *random* bar drawn from the same hold-length distribution, same entries, same trade count. **This is the leg that D274 says will fail** |
| **L3** | **Matched-count rotation null at ≥95th on BOTH legs**, Sharpe and money |
| **L4** | **Positive net CAGR** |
| **L5** | **Paired bootstrap p05 > 0** (R6 / D230) |

**All five.** L2 is stated second because it is the one that decides whether anything here is
information rather than cost arithmetic.

**Cells: 1 arm × 2 directions × 3 strata = 6**, with the long control included for the same reason
D247 requires it.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **L-a** | **Turnover falls by more than 5× against D275's 474/yr.** Mechanical — one round trip per CHoCH instead of one per state flip | **high** |
| **L-b** | **The captured move rises materially above D275's +0.57 bp**, because the cost of churn is removed | **moderate-high** |
| **L-c** | **It still fails L1.** The pivot confirmation lag means the exit lands `k = 2` bars *after* the actual low, giving back the turn — and every construction in this session has failed this bar | **moderate** |
| **L-d** | **It does NOT beat the R7 random-exit null (L2).** D274 measured exactly this on two other arms, and R7 exists because seven overlays beat their baselines and none beat this control | **moderate-high** |

**L-d is the one that matters and it is declared against the construction.** If the leg exit beats
a random exit at matched hold lengths, that is the first exit trigger in this programme to carry
information, and it would be a real result even if L1 still failed.

---

## Stop

**If L2 fails, the leg exit is closed and so is the exit question on this fixture** — D274 closed
time exits, this closes structural ones, and no third exit family will be registered.

**If L2 passes but L1 fails**, the verdict is *"the trigger carries information and the move is
still too small"*, which is a genuine finding and is reported in those words.

**Nothing is promoted under any outcome.** R8 governs, and a passing cell would need its own
out-of-sample test on names this fixture has never touched.

---

## Ledger

| count | N |
|---|---:|
| fresh — 1 arm × 2 directions × 3 strata | **6** |
| carried from D275 | 46,272 |
| **total** | **46,278** |

**The structure programme's 86 looks remain disclosed and not summed**, on the reasoning
established in D272.
