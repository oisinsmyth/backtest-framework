# D398 — the structural state premise check: how often is a single name in a two-sided structural trend, and what do the overlays leave?

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **Nothing here is a
result.** No strategy is scored, no P&L is computed, no null is drawn, nothing is admitted (R15).
**Ledger contribution: 0.**

**Date:** 2026-09-09 · **Area:** signal research · **personal track** · Requested by the principal.
**Number:** D398, in this branch's reserved D390–D399 block.

**No holdout testing. Holdout reads spent by this record: 0. Programme total: 1** (D371).

**Build (R16):** `us_shorts_daily_raw.csv.gz` via `load_ragged(dividend_bound=True)`, D333's
default. **Daily bars only. No 15-minute bar is read by this record.**

---

## 0. What this is, and what it is not

**A MEASUREMENT (D280's class), and specifically a premise check.** The principal has specified a
construction — a two-sided structural trend state on daily bars, overlaid with path efficiency and
a volatility band, with entries, stops and targets set at 15 minutes. **This record measures the
premise of that construction and nothing else: how often the state is on, how long it lasts, and
how much of it the overlays leave.**

It exists because the design cannot be written without those numbers. Three things depend on them
and none can be guessed:

1. **Whether the sample exists at all.** A rough estimate off S2's ETF exposure (13.9%, 63-bar cap)
   gives ~0.56 entries per name-year — **~115 long onsets over 8.6 years on the 24-name cohort4
   panel.** If that order of magnitude is right, onset entry cannot support a study on the names
   that have 15-minute bars, and the construction has to use state entry instead.
2. **What each overlay costs in events.** Each filter multiplies, and D366 is the precedent for
   discovering that too late: 164 standard errors in sample, failed out of sample.
3. **How much survivorship would bias the short leg.** §6 Q6 measures this directly.

> **This record proposes no rule, chooses no threshold, and computes no return.** Choosing the
> operating point is the principal's, on the numbers this produces.

---

## 1. The universe, and why it is the dead-inclusive one

| | names | dead | span |
|---|--:|--:|---|
| **`us_shorts_daily_raw`** — the measurement universe | **1,573** | **35.7%** (562 delisted, 122 collapsed) | 2010-01-04 → 2026-08-26 |
| **the 15m-reachable slice**, reported separately | **48** | 0% — survivor-only | 2018-01 → 2026-08 at 15m |

The 48 are every single name in this programme that has 15-minute bars, in three sets with **zero
overlap**: cohort4 (24), cohort3 (8), and the file named `holdout_intraday_15m` (16).

**Two facts about that slice are recorded here because they constrain everything built on it:**

- **All 16 names in `holdout_intraday_15m` are in the DAILY MINING fixture and none is in the daily
  holdout 803.** It is a holdout with respect to the *intraday* work only. **For a daily-signal
  construction it is not a holdout at all**, and no record should treat it as one.
- **The 15m fixture is survivor-only and cannot be otherwise on this API tier.** Its own metadata
  records the probe: `TIME_SERIES_INTRADAY` returns `Invalid API call` for TWTR, FRC, SIVB and
  AABA, while the daily endpoint serves them. **41.6% of the 2013–2017 cohort is unreachable at 15
  minutes.**

**The measurement therefore runs dead-inclusive on all 1,573**, and the 48-name slice is reported
beside it so the gap between them is visible rather than assumed.

---

## 2. The state, frozen — S2's definition unmodified, plus its mirror

```
For each name, on DAILY bars, in LOG space, on that name's OWN live bars:

    lows  = confirmed swing lows  in the trailing 252 bars   (k = 3)
    highs = confirmed swing highs in the trailing 252 bars

    g_lo  = OLS slope of log(price) on bar index, over lows
    g_hi  = OLS slope of log(price) on bar index, over highs

    UP   := g_lo > 0 AND g_hi > 0          S2's rule, unchanged
    DOWN := g_lo < 0 AND g_hi < 0          the mirror -- NEW, and it is one sign flip
```

**Every constant is inherited, not chosen here:** `k = 3` from D173's `SWING_K`; `WINDOW = 252`;
`MIN_PIVOTS = 3` — all three are `run_uptrend_onset.py:70-72`.

**Nothing is reimplemented.** `pivots` (via `research.structure`) and `rolling_fit` are imported
from S2's own runner. The causality that makes them safe is theirs: a pivot at index `i` is
knowable only at `i + k`, so the window usable at `t` is `[t − 252, t − k]` and **not** `[t − 252,
t]`. That offset is D173's, and getting it wrong reads the future invisibly.

**DOWN is a new state and this record measures its frequency, not its profitability.** Whether a
short leg on liquid names is worth building is a separate question the record does not touch —
FINDINGS §8 lists *"directional shorts on liquid ETFs"* as closed by five records, and **only the
principal reopens an avenue (R15).**

---

## 3. The two overlays, declared with their levels before anything is counted

### 3a. Path efficiency

`a1_er_stage0.er_grid(closes, live, w)` — imported, not restated, including its
**direct-denominator-sum** requirement (a difference of cumulative sums broke the triangle
inequality on 329 of 11.86M cells and the fix was exactness, not a tolerance).

- **Windows, declared now: `w ∈ {10, 21, 63}`.**
- **Retention reported at `ER ≥ {0.3, 0.5, 0.7}`**, and the full within-state ER distribution
  beside it.

### 3b. The volatility band

The principal's specification: *"percentage based +/−X% centred on a SMA(300) of volatility."*

```
    v[t]  = rvol21[t]                                   the programme's standard measure
    s[t]  = SMA(v, 300) over the name's OWN live bars
    r[t]  = v[t] / s[t]
    IN-BAND := |r[t] - 1| <= X
```

- **`X ∈ {0.10, 0.25, 0.50}`, declared now.**
- **Warm-up is 21 + 300 = 321 of a name's own bars** before `r` is defined, on top of the 252 the
  trend window needs. The intersection is reported, not assumed.
- **`rvol21` is primary because it is the programme's standard.** S2's own `atr_log(·, 21)` is a
  different object; their rank correlation within the state is reported as **one number**, so the
  choice is visible rather than silent. No cell is scored on ATR.

### 3c. This is 27 retention numbers per direction per universe, and that is NOT a search

3 ER windows × 3 ER thresholds × 3 band widths. **No P&L is computed anywhere in this record**, so
no cell can be picked on performance. Retention is a descriptive count and **all of it is reported
(R14).** The operating point is chosen later, by the principal, on a stated criterion.

---

## 4. What the runner reports — per direction, per universe

1. **episodes**, total **bars-in-state**, and the share of live-and-eligible bars
2. **episode length** — median, p25, p75, p90, max
3. **onset count** (S2's entry rule) against **bars-in-state** (state entry) — *the fork the design
   turns on*
4. names ever in state; names with ≥ 1 episode; the per-name distribution
5. **retention** under each overlay separately and under the intersection
6. **long/short symmetry** on every quantity above
7. **the 48-name 15m-reachable slice**, same table, beside the 1,573

---

## 5. Predictions, written before the runner exists

| | prediction |
|---|---|
| **Q1** | **DOWN is rarer than UP** on this universe — DOWN bars-in-state between **0.5× and 0.9×** of UP |
| **Q2** | *(against the construction)* **onsets on the 48 names are too few**: fewer than **400** across both directions over the whole span |
| **Q3** | but **bars-in-state on the 48 exceeds 20,000 per direction**, so state entry is viable where onset entry is not |
| **Q4** | **median episode length exceeds 63 bars**, so S2's quarter-long cap binds rather than expires |
| **Q5** | the two overlays are **approximately independent** — the intersection's retention is within **5 percentage points** of the product of the marginals |
| **Q6** | **the dead cohort is over-represented in DOWN**: its share of DOWN bars-in-state **exceeds its 35.7% share of names**, which is the direct measure of how much a survivor-only 15m fixture would bias a short leg |

**Q2 is declared against the construction as the principal specified it.** If it holds, onset entry
on the 15m-reachable names is not a study that can be run, and the record says so.

**Q6 is the one that matters most for the design.** If dead names carry materially more of the DOWN
state than their headcount, then a short leg measured on 48 survivors is measuring the downtrends
that *recovered* — and a "long works, short doesn't" verdict would be what survivorship predicts
rather than what the market did.

---

## 6. Assertions the runner must carry

- **[L]** **causality**: `g_lo`/`g_hi` at bar `t`, recomputed from a panel truncated at `t`,
  equals the full-panel value — D391's `[PIV]`, adapted, on a sample of (name, bar) pairs.
- **[X]** the causality check **raises** on a slope grid shifted the wrong way, via
  `lag_audit.raises_on_broken`.
- **[S2]** the UP state reproduced on the **57 ETFs** is **bit-identical** to
  `run_uptrend_onset.signals`' own — the assertion that pins the reuse. If it fails, this record is
  measuring something other than S2 and stops.
- **[E]** every state bar sits on a bar that is **live** and passes the declared eligibility
  (`keep_v2`, F0), so the counts are not the excluded tail (D351).
- **[W]** the warm-up intersection is computed, not assumed: no state bar precedes the name's own
  252nd bar, nor its 321st for a banded cell.
- **[P]** the JSON is persisted **before** it is rendered (D371; D391 repeated it).
- **[C]** the pivot/slope cache is keyed on the fixture **and** every module whose edit changes a
  pivot, per CLAUDE.md and D391's `pivot_key`.

---

## 7. What this record will NOT do

- **It will not compute a return, a Sharpe, or a cost.** It is counts and durations.
- **It will not choose an operating point** — not `X`, not the ER window, not the entry rule.
- **It will not read a 15-minute bar.**
- **It will not open or close a research avenue (R15).**
- **It will not treat `holdout_intraday_15m` as a holdout.** §1 records why it is not one.

---

**Status footer.** No runner exists. `docs/BOOK.md` holds S1 and S2, neither at capital;
`docs/BOOK_PROP.md` is empty. Nothing here is a result.

---

## 9. AMENDMENT, 2026-09-09 — the LEVEL dead band, declared before its runner exists

**Committed after the §1–§8 result, before any δ cell is computed.** Still a MEASUREMENT: counts
and durations, no P&L, admits nothing.

### 9a. Why, and the distinction it turns on

The result found the state is on **58.5% (UP) / 36.2% (DOWN)** of addressable bars — together ~95%.
The principal's response was to ask for stricter lines via **a dead band on the gradient's CHANGE**
(hysteresis, so the held gradient does not update until a refit moves it by more than the band).

**Hysteresis does not reduce state frequency, and the record should say so before it is built.**
`UP := g_lo > 0 AND g_hi > 0`. Making `g` stickier does not make it less often positive. Two
different objects share the name "dead band":

| dead band on | effect |
|---|---|
| **Δg — the change** | reduces line churn; **stabilises the level**. State frequency essentially unchanged |
| **\|g\| — the level** | **this is what cuts the 95%**: the trend must be *steep*, not merely positive |

**This amendment measures the second.** The first is a state machine that belongs in the
construction record, not here.

### 9b. The sweep, frozen

```
    UP(δ)   := g_lo >  δ  AND  g_hi >  δ
    DOWN(δ) := g_lo < -δ  AND  g_hi < -δ
```

**δ ∈ {0, 1e-4, 2e-4, 5e-4, 1e-3, 2e-3}**, in log-return per bar — δ = 0 reproduces §1 exactly and
is the control. Annualised equivalents (`exp(252δ) − 1`) are reported beside every row so the grid
is readable: **0%, 2.6%, 5.2%, 13.4%, 28.7%, 65.3% per year.**

Reported per δ, per direction, per universe: bars-in-state, share of addressable, episodes, median
and p90 episode length. **Same two universes, same warm-up, same eligibility.**

### 9c. Predictions

| | prediction |
|---|---|
| **Q7** | **δ has to be large before it bites**: at δ = 1e-4 (2.6%/yr) UP is still on **more than 50%** of addressable bars |
| **Q8** | the δ that **halves** UP frequency (to ≈29%) lies between **5e-4 and 2e-3** |
| **Q9** | **episode COUNT rises before it falls** — a level threshold fragments long episodes before it eliminates them, so the count peaks at an *interior* δ rather than falling monotonically |
| **Q10** | **DOWN needs a smaller δ than UP** to reach any given frequency, since DOWN starts rarer |

**Q9 is the one that is not arithmetic.** Frequency must fall monotonically in δ because the masks
are nested — that is a tautology and is not predicted. **Episode count need not**, and if it peaks
in the interior then a level dead band *buys* onsets while it removes bars, which changes what the
entry rule should be.

### 9d. What this does not do

It does not implement the hysteresis or the ratchet, does not choose δ, computes no return, and
opens or closes nothing (R15).
