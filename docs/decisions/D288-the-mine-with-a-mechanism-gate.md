# D288 — The mine, with a mechanism gate

**Status:** PRE-REGISTERED. Committed **before the runner exists**. Nothing here is a result.
**Date:** 2026-09-02
**Area:** Strategy research · **personal track**

---

## Why: the signal is the thing to replace, not the construction

Eight constructions closed on one fixture — D256, D279, D281, D282, D283, D284, D285, D286 — and
the last of them established *why*, with the portfolio stripped out entirely:

**D286's event study**, no slots and no exit rule, measured the long-minus-short spread of `hist_L`
at **+25.6 / +56.3 / +28.3 bp** peak (N = 10 / 25 / 50), at horizons that **wander** (k = 3, 25, 16)
and a best `t` of **+2.86 over 36 looks**. **Both legs are positive at every horizon and every N** —
`hist_L` sorts *rises less* from *rises more*, not winners from losers.

So this study mines for a different signal, on the one construction that has ever produced a
positive gross Sharpe here (D285's factor-neutral book, +0.440 / +0.348 / +0.217).

## The failure being designed against

[D277](D277-the-mine.md) crossed `3 bases × 35 filters × 3 strata = 300` cells. Its best result was
**+0.392 against its own best-of-300 floor of +0.605.** It did not fail for want of ideas — **it
failed because searching 300 things raises the bar you have to clear.** Any method that does not
confront that arithmetic is D277 again on a bigger fixture.

---

## The candidate list — 31, and it is NOT padded to a round number

The plan said "~40". **The honest inventory is 31.** Padding to 40 with interaction terms would add
looks without adding independence, and **a smaller count is a LOWER floor** — so the count follows
the inventory rather than the other way round.

All are computed on `us_shorts_daily_raw.csv.gz` (1,573 names, 35.7% dead, ragged). All are
returned **unlagged** and lagged once by the book builder (R9). All are turned into the **same**
dollar-neutral long/short book: long the N lowest, short the N highest, N ∈ {10, 25, 50}.

### A — calibration, 5. These validate the screen and are counted like anything else

| | score | exact binding |
|---|---|---|
| **A1** | `hist_L` | **`signals_ragged(...)[1]`, the array named `hs`** — D286's own score, bound by index and not by name so there is no ambiguity about what is being reproduced |
| **A2** | `md` (Impulse log-band level) | `signals_ragged(...)[0]` |
| **A3** | `macd_hist` | `ragged_price_scores.PRICE_SCORES` |
| **A4** | `macd_line` | `ragged_price_scores.PRICE_SCORES` |
| **A5** | `trailing_return` | `ragged_price_scores.PRICE_SCORES` |

**A1 must land in D286's measured band. If it does not, the screen is wrong and no other result
from it means anything** — the run is void, not merely negative. A2–A5 are near-duplicates by
D268's measurement (nine price scores → **2.87 effective inputs**) and should cluster with A1;
if they scatter widely, the independence gate is reading something the correlation does not.

### B — intrabar shape, 7. The axis D280 measured as genuinely independent

**13.50–15.76 effective inputs of 16** (D280 G3), against 2.87 for the price family. My prediction
that they would collapse was **wrong**, which is why this axis is here rather than more price
transforms.

| | score | mechanism |
|---|---|---|
| **B1** | `upper_wick` | rejection of higher prices — supply met the bid intrabar |
| **B2** | `lower_wick` | rejection of lower prices — demand appeared intrabar |
| **B3** | `wick_asym` | which side did the rejecting, net |
| **B4** | `body_frac` | conviction: how much of the range the close-to-open captured |
| **B5** | `close_in_range` | where the session settled — the classic close-strength proxy |
| **B6** | `range_frac` | realised intrabar volatility, scale-free |
| **B7** | `gap_frac` | the overnight leg alone — D280 part 4's window |

### C — volume structure, 5

| | score | mechanism |
|---|---|---|
| **C1** | `rel_vol` | participation against the name's own trailing norm |
| **C2** | `vol_z` | the same, scaled by its own dispersion |
| **C3** | `dollar_vol` | participation in money rather than shares |
| **C4** | `vol_trend` | is participation building or fading |
| **C5** | `signed_vol` | participation signed by the direction it accompanied |

**Declared, not inherited:** `rel_vol` normalises against the trailing 20 sessions *at the same
bar-of-day*. Daily bars have one bar per session, so **this is a plain trailing 20-bar window and
NOT the estimator D270 measured.** D270's result is not carried.

### D — volume profile, 4

| | score | mechanism |
|---|---|---|
| **D1** | `dist_hvn` | distance to the nearest high-volume node, in ATR/2 |
| **D2** | `dist_lvn` | distance to the nearest low-volume node |
| **D3** | `mass_here` | how contested the current price is |
| **D4** | `mass_imbalance` | is the traded mass above or below |

**D2 selects from a 71%-populated grid** against ~86% for the other three, because an LVN needs a
strict local extremum *and* non-zero mass. It is solving a different selection problem and that is
stated with it.

### E — range and volatility, 5

| | score | mechanism |
|---|---|---|
| **E1** | `atr_log` / price | volatility level, scale-free |
| **E2** | trailing Corwin–Schultz half-spread | **liquidity, and the axis that killed D284 and D285** |
| **E3** | realised vol, 21 bars | the conventional measure, as a control on E1 |
| **E4** | vol ratio, 5-bar / 63-bar | volatility *regime* rather than level |
| **E5** | `range_frac` / `atr_log` | today's range against the name's own norm |

### F — overnight versus intraday, 5

D280 part 4 found the whole `hist_L` effect sat overnight; D286 found the intraday session
reversing it. This axis asks whether the *split itself* carries information.

| | score | mechanism |
|---|---|---|
| **F1** | trailing mean overnight return | who is repriced while shut |
| **F2** | trailing mean intraday return | who is repriced while open |
| **F3** | overnight share of absolute move | where this name's risk is expressed |
| **F4** | F1 − F2 | divergence between the two windows |
| **F5** | overnight return sign persistence | does the gap direction repeat |

**Total: 5 + 7 + 5 + 4 + 5 + 5 = 31.**

### Provenance — 21 of the 31 already exist and are proven bit-identical; **10 do not**

| | candidates | status |
|---|---|---|
| A1–A2 | 2 | `signals_ragged`, unchanged since D279 |
| A3–A5 | 3 | `ragged_price_scores` — ported at `95dd6b4`, **bit-identical** |
| B1–B7 | 7 | `ragged_features` — lifted at `8bc0bf6`, verbatim formulae |
| C1–C5 | 5 | `ragged_features` — ported at `17a7cbc`, **bit-identical** |
| D1–D4 | 4 | `ragged_profile` — ported at `9f009f8`, **bit-identical** |
| **E1–E5, F1–F5** | **10** | **NEW CODE.** Only `atr_log` (E1) and `corwin_schultz` (E2's kernel) exist; the trailing wrappers, the vol ratio and the whole overnight/intraday split are written for this study |

**Stated because new code is where the bugs have come from.** Every defect in this
programme — the `top_n` look-ahead, D286's 10×-small move, D271's overlap `t` — entered through a
runner written for one study. **The ten new scores get the same three runner assertions as anything
else** (lag audit in a second implementation, sign audit in money, right-quantity), and the intrabar
lift is the precedent: its assertion found **5 malformed bars in 4,137,239** that both build gates
had missed.

**One shared input, disclosed for Gate 0:** B6 `range_frac` and E5 `range_frac / atr_log` are built
from the same numerator, and E1/E3 both measure volatility level. If Gate 0 collapses E into B, that
is the measurement working, not a surprise.

---

## The screen

**Two-leg event response**, `scripts/d286_event_study.py`'s instrument: every fresh entry into the
bottom N or top N is an event, **taken whether or not anything else is open**, so there are no slots
to compete for and no exit is caused by another name. Cumulative forward return to k = 40.

**Both legs are reported separately, always.** D286's headline is why: a candidate whose short leg
is genuinely negative is worth more than one with a wider spread, and the spread alone hides which
you have.

**The t-statistic is computed ACROSS BARS — one observation per bar, not per event.** D271 counted
overlapping windows as independent trades and turned a `t` of 2.31 into 5.30. Events here overlap
by construction.

**Effective sample is counted in WARM cells, not finite ones.** `impulse_nodz` needs 992 own bars
and **34.7% of the finite values it produces on this panel are seed transient**; `macd_line` loses
13.8%; `rsi` and `trailing_return` lose nothing, being FIR. Two candidates compared on finite cells
are compared on different samples.

---

## The gates, in order

| | gate | standard |
|---|---|---|
| **0** | **independence** | ≥ **3.0 effective families** across the 31, by `d268_score_independence`'s instrument (`rankify`, `BETWEEN_FAMILY_LIMIT = 0.70`). **If the 31 carry fewer, a best-of-31 floor is dishonest** — it prices looks that were not taken — and the count is restated before anything else is read |
| **A** | **the floor** | best-of-31, one shared offset vector, the construction in `d277_mine.py` |
| **B** | **the re-derivation** | each Gate-A survivor checked against **its own** pre-declared shape below. Every mismatch reported, including for candidates that pass |

**Promotion.** Several clear both → the one whose shape was **pre-ranked most specific**. None
clears B but some clear A → **the best on A goes forward, and the record states it went WITHOUT
mechanism support**, which weakens whatever the holdout then says. None clears A → closed.

---

## The shape predictions — numeric, per axis, declared now

A candidate is promotable only if it clears the floor **and fails in none of the ways its own
mechanism forbids.**

| axis | if the mechanism is real | **falsified even if the number is good, when** |
|---|---|---|
| **A** | A1 lands within ±15 bp of D286's +56.3 at N = 25 | A1 misses that band — **the run is VOID, not negative** |
| **B** | the effect is **larger at short horizons** (k ≤ 5), because an intrabar shape is a one-session statement | peak spread sits at k ≥ 20 — that is a slow factor, not a shape |
| **C** | the effect **strengthens with N**, because participation is a crowd measure and needs breadth | spread at N = 10 exceeds N = 50 |
| **D** | the effect is **monotone in the distance score**, not confined to the extreme deciles | the middle three quintiles carry ≥ 60% of the spread |
| **E** | **the SHORT leg is negative**, since these select risk rather than direction | both legs positive at every horizon — the D286 signature, i.e. nothing new |
| **F** | F1 and F2 have **opposite** signs, since D280/D286 measured the two windows opposing | F1 and F2 share a sign — the split carries nothing the total does not |

**Specificity rank, declared now to settle ties without a post-hoc choice:**
**E** (a signed-leg prediction is the riskiest) > **F** (a sign-opposition prediction) > **B** (a
horizon-location prediction) > **D** (a monotonicity prediction) > **C** (a direction-of-N
prediction) > **A** (calibration, which cannot be promoted at all).

**A1–A5 are not promotable.** They exist to validate the screen. They are counted in the ledger and
in the floor — D228 does not care what a cell was built to prove — but a calibration score winning
its own calibration is not a discovery.

---

## Predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **M1** | **A1 reproduces D286's band**, validating the screen | neutral — *not scored as a success* | **very high** |
| **M2** | **Gate 0 returns ≥ 3.0 effective families.** The axes were chosen on measured independence, so this should hold — if it fails, the choosing was wrong | **for** | **moderate-high** |
| **M3** | **No candidate clears Gate A.** D277 found 0 of 300; the honest prior after eight closures is that 31 does not change the answer | **AGAINST** | **moderate-high** |
| **M4** | **Every candidate shows BOTH LEGS POSITIVE**, as `hist_L` did — the fixture's drift dominates every score, and no score sorts winners from losers | **AGAINST** | **moderate** |
| **M5** | **If anything clears Gate A it fails Gate B**, i.e. the number arrives without the shape its mechanism requires — which is what a false positive looks like | **AGAINST** | **moderate** |

**M3, M4 and M5 are declared against the construction.** **M4 is load-bearing:** it says the
programme's central finding generalises beyond `hist_L` to every axis available on this fixture.
**What would falsify it: any candidate with a short leg negative at k = 5 and beyond, at any N.**
That would be the first evidence in D264–D288 that a score on this data sorts losers.

---

## Ledger

| | |
|---|---:|
| fresh — 31 candidates | **31** |
| carried under [R13](../RULES.md#r13) — D256 21, D279 20, D281 10, D282 19, D283 26, D284 13, D285 18, D286 18 | **145** |
| **total** | **176** |

**Disclosed and NOT carried:** D280's 165 statistics are measurements that scored no cell, but they
**shaped this search space** — the five axes were chosen on D268's, D270's, D272's and D280's
independence findings. **No best-of-31 floor prices that**, and saying so is the point rather than a
formality.

---

## The holdout, built BEFORE the mine and untouched

`us_shorts_daily_holdout.csv.gz` — **803 names, 272 dead (33.9%), 2,156,127 rows**, built at
`2bdf6c5` from `order[3400:5100]` of the same pinned permutation. Same seed, same screen, same span,
same gates; disjointness asserted, not trusted. **Nothing reads it until one candidate is promoted.**

**D246's reserved ETF cohort is NOT used** and stays reserved for S3 — it holds zero single names,
was already scored by D245, screens survivorship in the opposite direction, and carries ~1.9
effective instruments against this panel's 10.06.

---

## Stop

**If nothing clears Gate A, the mine is closed** — no thirty-second candidate, no second cut of the
axes, no re-run at a different N. **31 is the count and the floor prices it.**

**If a candidate clears and is promoted, the holdout is spent ONCE.** Under [R8](../RULES.md#r8) a
pass there is still not a book entry; it is one pre-registered out-of-sample result carrying its own
falsification conditions.
