# D388 PRE-REGISTRATION — the same question, with an event that is actually rare and one gate for every arm

**R8: committed before the runner exists. Result separately.** Signal test under
[R15](../RULES.md#r15): a positive **gross** mean per trade above the nulls. Admits nothing.

**This is D387 re-run with the two defects its own amendment disclosed, and nothing else changed.**
The hypothesis is unaltered: *price reverts at levels where its own rare events cluster.*

---

## 1. The two fixes, and only these two

### (a) The event threshold moves to the name's OWN SIGMA

D387 §2 justified its event types from a measurement on **ETFs** (5.0 and 7.0 per 100 bars) and then
carried the same **absolute** thresholds to single names at 3–5× the volatility. Measured
consequence: `move >2%` fired on a **median 28.3% of bars**, above 30% on **282 of 600 names**, and
91% on two profiled names. Where the event fires on most bars **`f` IS `g`** — ratio CV 0.096,
`TV(f,g)` 0.039 — so the density was flat and P1 could not have cleared whatever the market did.

**A threshold in percent is not a threshold in rarity.** Measured, return-blind
(`temp/d388_sigma_calibration.py`, the same 600 names):

```
       event     k     p10   median     p90     max   p90/p10  names>30%
        move   2.0    3.67     4.40    5.03    6.77      1.37          0
    reversal   1.5    2.47     3.44    4.25    5.54      1.72          0
    move >2%   abs   12.46    27.77   54.46   75.59      4.37        277
reversal >1%   abs    8.32    16.68   29.38   39.84      3.53         51
```

**`p90/p10` is the number that matters — how much rarity varies across names — and it collapses from
4.37 to 1.37.** No name exceeds 30% at any multiple.

**Declared:**
- **`move`**: `|r_t| > k·σ_t`
- **`reversal`**: `|r_t| > 1.0·σ_t` **and** `|r_{t-1}| > 1.0·σ_t` **and** the signs differ
- **`σ_t`**: causal EW standard deviation of returns, **half-life 60 bars**, warm-started

**`k` IS SWEPT, at two declared levels — 2.0 and 2.5 for `move`, 1.0 and 1.5 per leg for
`reversal`** — reported and never picked, per R14's addition. **The primary level was fixed by a
RETURN-BLIND rarity target (~4% of bars) measured above; no return was consulted in choosing it.**
The second level exists so the reader can see the shape rather than trust the target.

### (b) ONE GATE for every arm

D387 gave the observed a causal expanding quantile and the nulls a full-sample top-`R` gate.
**Measured: the top-n gate is worth up to +126 bp on the same signal — larger than the entire claimed
edge** — so "A′ matches the observed" was partly a statement about the gate.

**Every arm — observed, N2, A′ — now uses the identical causal expanding 90th-percentile gate.**
The signal must be causal to be a signal; the nulls face the same procedure or the comparison is not
a comparison.

**The cost is that entry counts no longer match exactly** (measured drift up to 34%). That is
accepted, and the reason is stated rather than assumed: **this is the path-invariant lens, scored per
TRADE.** A per-trade mean is count-normalised, so a count difference costs precision, not bias.
D291's count objection was about a control that **churned** — 2.4× the entries, distorting a
slot-limited book — which is a different failure and is still guarded (§4's `[POOL]`).

---

## 2. Everything inherited from D387 unchanged

Construction (a): `g` every bar, `f` on event bars, **one calendar λ** centring, calibrating and
decaying; `R_t = (f_t/∫f_t)(x_t) / g_t(x_t)`; `∫f` is exactly the EW event rate. **One declared
direction: reversion toward the EMA.** Universe `us_shorts_daily_raw.csv.gz`, 600 names, full date
range mined, holdout #2 untouched, `[SPLIT]` default-deny with no unlock.

**λ ∈ {60, 120, 250} · H ∈ {5, 10, 20} · 2 event types · 2 `k` levels = 36 primary cells.**

**Nulls unchanged:** **N2** regenerates the path and therefore the events, `σ`, EMA, `x`, `f`, `g`,
`R` and the trades by the identical code path. **A′** time-rotates the density, randomising the
partner rather than the membership.

---

## 3. What D387 already settled, and is NOT re-litigated

- **Cost.** Corwin–Schultz on the held names was **127.9–142.1 bp** against a best gross of 88.1 bp.
  **A rarer event will trade less often but there is no reason to expect a larger per-trade edge**;
  net is reported, but this study is about whether a signal EXISTS, not whether it pays.
- **The secondary direction is vacuous by construction** — for a symmetric signed trade,
  continuation is the exact arithmetic negative (`max |revert + continue| = 0.000e+00` over 10,025
  cells). **It is dropped.** The volatility-versus-direction question needs `|return|` and is
  explicitly out of scope here.
- **The N2 bar was unreachable** — its per-name draw-mean spread was 415 bp, putting "p95 + 2 SE" at
  1,975 bp. **P1 is therefore stated against the null's CENTRE with a sign test across names, and
  the p95 margin is reported beside it as a secondary.** A bar nothing can reach is not a test
  (D384's H4, D387 §1).

---

## 4. Decision rules and assertions

**P1 — is there an edge above the nulls?** The **gross mean per trade**, per name, against **each
null's centre**, with a sign test across names. **A′ is the load-bearing null**: N2 destroys the
whole price path, A′ destroys only the density's alignment. **D387's finding was that the observed
beat N2 at p = 1.2e-18 and did not beat A′.** If that survives a rare event and one gate, the
conditioner adds nothing and the line is finished.

**P2 — the shape across λ, H and `k`.** A single clearing cell with neighbours inside the null is a
knife-edge and is reported UNRESOLVED.

**P3 — did the density have SHAPE?** `TV(f, g)`, the ratio's CV, and the **mode count of `f` at a
real bar for named examples**, reported for every cell. **D385 and D387 both reported a test
statistic without ever looking at the object, and both times the object was flat.** This is now a
first-class output, not a diagnostic.

| tag | what it proves |
|---|---|
| **`[RARE]`** | the realised event rate's **p90/p10 across names is below 2.0**, and no name exceeds 15% — the fix, asserted rather than assumed |
| **`[GATE1]`** | observed, N2 and A′ all call the **same** threshold function; asserted by identity of the function object and by re-deriving one cell's decisions through each path |
| **`[FASTQ]`** | the fast expanding quantile equals the explicit `insort` scan it replaces, **exactly**, on a tie-heavy input |
| **`[POOL]`** | A′ enters only bars the observed could; count ratio **reported**, and asserted within 2× to catch D291-style churn |
| **`[MASS]`, `[LAG]`, `[SIGN]`, `[QTY]`, `[CAUSAL]`, `[NULL]`, `[REC]`, `[SPLIT]`, `[X]`** | as D387, unchanged — three of them fired there and each found a real defect |

---

## 5. Predictions

| | |
|---|---|
| **Q1** | **the density now has shape**: `TV(f,g)` above 0.12 and ratio CV above 0.35 at the median name, against D387's 0.039/0.096 in its worst bucket |
| **Q2** | **P1 still fails against A′.** The rare event fixes the object, not necessarily the idea, and D387's A′ result was the cleaner half of that study |
| **Q3** | **the gross per trade RISES** relative to D387 — fewer, better-selected trades — but by less than the 142 bp spread |
| **Q4** | **`k = 2.5` beats `k = 2.0`** for `move`, i.e. rarer is better, which is the whole premise of the fix. If it does not, rarity was never the mechanism |
| **Q5** | **AGAINST myself: the count drift from one gate exceeds 20%**, and I will have to report a null comparison on unequal counts |
| **Q6** | **AGAINST myself: at least one assertion fires on the first run.** Q7 has been made three times (D384, D385, D387) and been wrong every time; predicting the opposite is the only honest version |

---

## 6. What would make me abandon this

- **`[RARE]` fails** → the σ fix did not equalise rarity and the premise of this re-run is wrong.
- **`[GATE1]`, `[FASTQ]`, `[MASS]`, `[LAG]`, `[CAUSAL]` or `[NULL]` fails** → stop, fix, publish nothing.
- **P3 shows the density is STILL flat** → the construction cannot produce shape on daily bars at any
  rarity, and the line closes on the object rather than on the signal.
- **The observed does not beat A′ at any cell, with the density demonstrably shaped and one gate** →
  **the conditioner adds nothing to `x`, on a clean test.** That is the close, and unlike D385 and
  D387 it would be a close on a statistic that could have detected the thing, with an object that
  was actually built. **Under R15 the decision remains the principal's.**

---

*Pre-registered 2026-09-08. Runner does not exist at the time of this commit (R8). R13: 36 primary
cells on the hypothesis "price reverts at levels where its own rare events cluster" — **this is the
SECOND look at that hypothesis** and the ledger carries both.*
