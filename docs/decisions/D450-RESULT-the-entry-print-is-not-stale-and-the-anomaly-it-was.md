# D450 RESULT — the proxy's entry print is not stale, and the anomaly it was sent to explain was a BUG IN D449

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D450-RESULT-the-entry-print-is-not-stale-and-the-anomaly-it-was-sent-to-explain-was-a-bug-in-D449.md`. The H1 above is the full title.*

**MEASUREMENT record.** Closes D449 §6 item 1. **Runner:** `scripts/d450_entry_prints.py`.
**Evidence:** `data/d450_entry_prints.json`, `data/d450_entry_pairs.json`.
**One of three predictions holds — and the two that failed did so because the thing they were
sent to explain does not exist.**

---

## THE ANSWER

> **The proxy's 18:00 entry print is NOT stale. It sits `+0.18 bp/day` above its own 16:00 close,
> D259's fallback branch NEVER FIRES, and 1,746 of 1,747 entries are real prints at exactly 18:00.**
>
> **And the −1.74%/yr anomaly D449 sent this study to explain was an artefact of a bug in D449's
> own pairing. Corrected, the same window reads +1.13%/yr.**

## 1. The decomposition, exact in logs

For either instrument, with `c16` the 16:00 close on the entry day, `e18` the 18:00 entry and `x`
the exit: `hold = x/e18`, `step = e18/c16`, `full = x/c16`, and `log full ≡ log hold + log step`.

**1,747 matched holds, 2011-03-15 → 2022-08-16:**

| term | SPY bp/day | ES bp/day | ES−SPY bp | ES−SPY %/yr |
|---|---:|---:|---:|---:|
| hold | 6.46 | 6.91 | +0.44 | **+1.11%** |
| **step** | **+0.18** | **+0.35** | **+0.17** | **+0.42%** |
| full | 6.65 | 7.27 | +0.61 | **+1.54%** |

**Identity residual: −2.49 × 10⁻¹³ bp.**

> **The step term is +0.42%/yr and it runs the WRONG WAY for the staleness hypothesis** — ES's
> entry sits further above its close than SPY's does, not the reverse. **The entry print explains
> nothing, and what there is to explain is the full 16:00→16:00 window, which is carry.**

**`full` = +1.54%/yr reproduces [D448](D448-RESULT-the-direct-test-the-drift-is-in-the-T0-future-too-and.md)'s
+1.49%/yr on the overnight leg** — the two windows differ by the RTH leg, which D448 measured at
**+0.00 bp** difference. **D448's carry reading stands.**

## 2. The cross-fixture gate

**`full` is computed twice by independent routes** — as `hold × step` from D449's holds panel, and
directly from D448's boundary panel, **built in a separate pass over the raw DBN.**

> **Max absolute difference: 4.44 × 10⁻¹⁶.**

**That gate is what made the bug findable.** It passed on the first run too — the two extractions
agreed with each other while *both* were being fed a sample that silently excluded every Friday.
**An agreement gate proves consistency, not correctness**, and that distinction is the lesson here.

## 3. THE BUG IN D449, AND IT IS MINE

**Found by asking why D450's sample was 1,316 when D448's was 1,747.** The 431 missing pairs were
**418 Fridays, 11 Thursdays and 2 Tuesdays** — and the contract never changed across them, they were
consecutive calendar days, and both days were present in every panel.

**The cause:**

```python
days = sorted(set(ev) & set(front))      # ev = days WITH 18:00+ bars
for a, b in zip(days, days[1:]):         # pair consecutive ENTRIES OF THAT LIST
```

> **ES is SHUT on Friday evening.** A Friday therefore has no 18:00+ bars, never enters `ev`, and
> never appears in `days`. **Pairing consecutive entries of that list skipped Thursday→Friday
> entirely — every Friday hold in the sample.**

**D259's rule excludes Friday→MONDAY, because Globex is shut over the weekend. It does not exclude
Thursday→Friday, which is a perfectly tradeable hold.** I implemented the right rule at the wrong
place: as a property of the *list*, not of the *calendar*.

**The fix pairs by calendar** — for each exit day, the entry day is the previous calendar day, which
must carry evening bars and the same contract. **2,068 holds → 3,067.**

### What it cost, attributed

| | n | hold diff | p99 MAE ratio | breach 1× ratio |
|---|---:|---:|---:|---:|
| **buggy**, ≤2022-08-16 | 1,362 | **−1.74%/yr** | 1.05 | 1.00 |
| **corrected**, same window | 1,808 | **+1.13%/yr** | 0.98 | 0.96 |
| corrected, full window | 2,208 | +0.22%/yr | 1.01 | 0.90 |

> **The Friday exclusion alone flipped the sign on an identical window.** And the corrected value
> **agrees with D448's carry estimate**, where the buggy one contradicted it — **the contradiction
> between two of my own records was the symptom, and I treated it as a finding for one full
> record before treating it as a bug.**

## 4. What this does to D449

**[D449](D449-RESULT-the-untraded-window-was-not-the-problem-the-proxy.md)
is amended in place.** Specifically:

- **§3 — "what it actually flatters is the ENTRY" — is WITHDRAWN.** It was the Friday exclusion.
- **`Z3` (V falls on ES) inverts:** corrected, ES `V` is **167 / 99** against the proxy's
  **95 / 63**. **ES is worth MORE, not less.**
- **`Z4`'s sign failure disappears:** the corrected hold difference is **+1.13%/yr**, which is the
  carry `Z4` predicted, so **`Z4` was right and the data was wrong.**
- **§1's conclusion STRENGTHENS.** MAE ratios move from 1.03–1.07 to **0.98–1.02**, and the 1×
  breach ratio from 1.00 to **0.90**. **The untraded window matters even less than D449 said.**

**D449's headline — *"the untraded window was not the problem"* — survives and is now better
supported. Its explanation for the residual does not.**

## 5. Predictions

| | prediction | outcome |
|---|---|---|
| **W1** | SPY's step is systematically negative relative to ES's and carries most of the −1.74%/yr | **WRONG twice over** — the step is **+0.42%/yr the other way**, and the −1.74%/yr did not exist |
| **W2** | the gap concentrates where D259's fallback fired | **WRONG** — **the fallback never fires**: 1,747 of 1,747 are real prints, 1,746 at exactly 18:00 |
| **W3** | the full-window term goes the other way, **+1 to +2%/yr**, being D448's carry | **CONFIRMED** — **+1.54%/yr** |

**W2 is worth keeping as a finding in its own right: D259's `ENTRY_STALE_FLOOR` guard has never
bound on this sample.** The guard is sound and the hazard it was written for does not occur here.

## 6. A hazard in the data source, recorded because it bit mid-study

**`temp/databento/` is a LIVE directory.** Between D449's build and D450's re-run the acquisition's
fourth chunk landed and the ES panel extended from **2022-08-16 to 2024-08-28** — four new files
appeared while this study was running, and the manifest still shows three chunks `submitted`.

**Every ES number in D448, D449 and D450 is a snapshot of an incomplete acquisition**, and the
committed fixtures are dated accordingly. **The 2024-05-28 T+1 boundary is now inside the ES range
for the first time, by three months** — **not enough to test, and not tested here.**

## 7. What this leaves

1. **Re-run D448 and D449 when the acquisition completes.** The T+1 era is the reason, and the
   window is now partially covered.
2. **D449's corrected lifecycle numbers were produced on a sample that grew mid-study.** §3's
   attribution table separates the Friday fix from the data extension, but the committed
   `d449_es_lifecycle.json` reflects the full corrected window and **should be regenerated once the
   source stops moving.**
3. **The generalisation, and it is the expensive one:** *a gate that proves two extractions agree
   does not prove either is right.* The cross-fixture check passed at 4×10⁻¹⁶ while both sides were
   missing a fifth of the sample. **What caught it was a sample-size discrepancy against a THIRD
   record built by a different route — and I only looked because two of my own numbers disagreed
   in sign.**
