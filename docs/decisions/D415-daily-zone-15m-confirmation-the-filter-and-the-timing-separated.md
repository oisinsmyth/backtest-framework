# D415 — daily zone, 15-minute confirmation: the filter and the timing, separated

**Status:** design and bar committed BEFORE the runner exists (R8). Result separately.
**Date:** 2026-09-10
**Area:** Strategy research · execution

**Number.** `D415`, by PICKUP's three-command procedure: D400–D414 used, `D407–D410` reserved
(`044f839`), `D390–D399` reserved for `worktree-signal-hunt-part2` (`945cbb5`, live 13 hours ago).
Master takes D415.

---

## 1. Why, and what D414 makes this

[D414](D414-RESULT-the-15m-touch-is-35bp-too-early-in-the-one-cell-that-mattered.md) found the
first 15-minute touch has no timing value pooled and is **35 bp too early in cell 2** at 4.9 SE,
because cell 2 selects straight-line momentum into the zone and that momentum runs through the
close. The daily close wins by being *after* the continuation.

**This asks whether an intraday confirmation can enter after the continuation exhausts without
waiting for the close** — the entry decision still made on daily bars (the zone, the cell), the
entry *moment* taken from 15-minute bars. If it works it beats both entries D414 compared.

**Same scope as D414, stated once more so it is not forgotten: this does not test the signal.** The
32 survivor names from 2018 do not show the daily edge (cell-2 gross −2.20 ± 17 bp). It tests
execution structure on the same 3,023 paired events D414 built, so the two records are directly
comparable.

---

## 2. THE TRAP, AND THE DESIGN THAT REMOVES IT

**A confirmation rule is a filter as well as a timing.** The events that never confirm are the ones
where price kept going — so the confirmed subset is **positively selected by construction**, and
"confirmed entry beats the daily close on confirmed events" would flatter any rule at all, including
a coin flip that fires late. Two controls are therefore built in, and **a rule that cannot beat both
has found nothing:**

1. **The time-matched unconditional entry.** For each rule, `k` = its median confirmation lag in
   bars among the events it confirms. The control enters at bar `j + k` after the first-touch bar
   `j`, **on the same events, with no condition.** The paired difference `rule − control` is the
   information in the *pattern* beyond the information in *waiting* — which D414 already priced.
2. **The dropped trades, accounted.** For every event the rule declines, the daily-close strategy's
   own 5-day return is reported. A rule that discards the winners is a worse strategy even if its
   confirmed entries are better — and that number is shown beside the delta, not hidden in a
   footnote.

---

## 3. THE RULES — three, declared, one primary

For a **demand** zone (price came down into it; long). Supply is the mirror in every clause.
Scanning starts at the bar **after** the first-touch bar `j` and runs to the session's last bar.
Entry is at the **close** of the confirming bar. Exit is the close of daily bar `t + 5`, held fixed
for every arm so exits cancel and every delta is entry-only, exactly as D414.

| | rule | enter at the close of the first bar after `j` whose … | mechanism |
|---|---|---|---|
| **R1 — PRIMARY** | up-bar | `close > open` | the first sign the selling has paused |
| R2 — shape | higher low | `low > previous bar's low` | a two-bar reversal |
| R3 — shape | re-cross | `close > hi_u`, back above the zone's upper edge | the zone repelled price |

**R1 is primary because it is the simplest and the least parametric** — one comparison, no lookback,
no threshold. R2 and R3 **cannot clear** (R14); they are read for shape. **Three rules at 2 SE is
three chances, and that is why only one can clear.**

A confirmation that lands on the session's last bar enters at that bar's close, which is the daily
close by the definition of `phi` — its delta is zero by construction. The share of such trivial
confirmations is reported (§6, P1).

**Quantities, per event:**

```
delta_R     = sign * (log C[t] - log P_R)          confirmed entry vs the daily close, confirmed events
delta_ctrl  = sign * (log C[t] - log P_{j+k})      the time-matched entry vs the daily close, same events
info_R      = delta_R - delta_ctrl                 the pattern's contribution beyond waiting
dropped_R   = r_daily on UNCONFIRMED events        what the daily-close strategy made on trades R declined
```

All entries cross the spread at a bar close, as the daily-close baseline does, so **every delta above
is already net of matched costs.** No limit arm: D414 established its value is the spread and nothing
else.

**Path-invariant throughout.** Every event is its own trade; no slot cap, no book.

---

## 4. Data and basis — D414's, inherited

Same 32 names, **mining 2018-01-02 → 2023-12-31, 2024-01-01 onward RESERVED and untouched.**
Same `phi` repair; `[ALIGN]`, `[BASIS]` at the 2% step gate, `[SAME-DAY]` at 10%, `[RESERVED]` —
all inherited from D414's runner, imported not restated.

---

## 5. THE BAR

Applied to **R1 only.** The pooled population is the gate; the cell-2 stratum is the declared
secondary (§5a).

| | condition |
|---|---|
| **G1** | D414's assertions hold; **R1 confirms at least 30% of events**, else it is not evaluated |
| **T1** | `delta_R1 > 0` by more than **2 paired SE** — the confirmed entry beats the daily close |
| **T2** | `info_R1 > 0` by more than **2 paired SE** — it beats the time-matched control |
| **T3** | `mean dropped_R1` is **not higher than** `mean r_daily` on confirmed events by more than 2 SE of the difference — the filter is not discarding the winners |

**All three must hold.** T1 without T2 is "later is better", which is D414's result restated. T1 and
T2 without T3 is a better entry on a worse book.

### 5a. The cell-2 stratum — declared secondary, cannot clear

Cell 2 is *why this study exists* and it is ~900 events, of which R1 will confirm fewer. The same
three tests are reported on the stratum at the same 2 SE, **labelled secondary and unable to clear
D415 on their own** — D408's R1 pattern. If the pooled bar fails and the stratum passes all three,
that is a finding about *where* confirmation works and it earns a design of its own, nothing more.

---

## 6. Stage 0

| | check |
|---|---|
| **P1** | per rule: fire rate, confirmation-lag distribution in bars, **share confirming on the last bar** (trivial), and `k` |
| **P2** | D414's `[ALIGN]` / `[BASIS]` / `[SAME-DAY]` counts, reproduced — the event set must be D414's 3,023 exactly |
| **P3** | fire rate and lag **within cell 2** against outside it — if cell 2 confirms far less often, that is the selection trap showing itself before any delta is read |
| **P4** | **look at the object** — one event printed end to end: touch bar, confirming bar, entry, control entry, close |

---

## 7. Predictions

| | prediction | confidence |
|---|---|---|
| **X-a** | R1 fires on **more than 80%** of events with a median lag **≤ 3 bars** — an up-bar inside a session is common | high |
| **X-b** | **pooled T1 fails** — within 2 SE of zero. D414's pooled delta was flat and a short delay will not move it | moderate-high |
| **X-c** | **cell-2 R1 delta is materially better than D414's −35, but still not positive** — confirmation absorbs part of the continuation, not all of it | moderate |
| **X-d** | **T2 fails for R1** — the up-bar's information is mostly "wait k bars" | moderate |
| **X-e** | R3 fires on **fewer than 40%** and has the best delta and the worst dropped-trade profile — it declines exactly the events that went through | moderate |

**X-c against X-d is the study.** If cell 2 improves *and* the improvement survives the
time-matched control, the pattern carries information about exhaustion. If it improves only as much
as waiting does, the right rule is a clock, not a candle.

---

## 8. What this does not do

- **Does not test the signal.** §1.
- **Does not read 2024+ or any holdout.**
- No book, no slot cap. No limit arm.
- **Does not sweep rule parameters.** Three rules as written; none has a knob.
- **Does not recommend a disposition.** That is the principal's.

---

## 9. R13

Fifteenth look by object; second on execution. Same 3,023 events as D414 — no new data is spent,
and the two records are one population read twice.

**Cost: minutes on fixtures already on disk.**
