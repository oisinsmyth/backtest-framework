# D288 RESULT — the mine is closed, and the two floors disagree

**Status:** CLOSED. Pre-registered at [`fa098a2`](D288-the-mine-with-a-mechanism-gate.md),
committed before the runner existed. This record is separate, per [R8](../RULES.md#r8).
**Date:** 2026-09-02
**Area:** Strategy research · **personal track**

---

## The result in one line

**Nothing cleared gate A. The mine is closed**, and the holdout was never read.

Of 31 pre-registered candidates on the 1,573-name dead-inclusive daily panel,
**zero** cleared the best-of-31 floor. The stop condition written at `fa098a2`
applies as written: no thirty-second candidate, no second cut of the axes, no
re-run at a different N.

## The screen validated first, exactly

The calibration is not "close". `hist_L` came back at **+25.6 / +56.3 / +28.3 bp
at N = 10 / 25 / 50, peak horizons k = 3 / 25 / 16, best t +2.86** — D286's
published band and its published best-t, to the decimal, from an independent
runner reading a cache built by eight separate processes. Gate B recorded the
calibration delta as **0.0 bp against a 15 bp tolerance**.

That matters more than any other number here: the pre-registration said a
calibration miss makes the run **void, not negative**. It did not miss.

## Predictions

| | prediction | outcome |
|---|---|---|
| **M1** | A1 reproduces D286's band | **CONFIRMED, exactly** — delta 0.0 bp, and t +2.86 also matched |
| **M2** | Gate 0 returns ≥ 3.0 effective families | **CONFIRMED** — 12.72 effective of 31 |
| **M3** | No candidate clears Gate A | **CONFIRMED** — 0 of 31 |
| **M4** | Every candidate shows BOTH LEGS POSITIVE | **FALSIFIED** — 16 cells carry a negative short leg at k ≥ 5 |
| **M5** | Anything clearing A fails B | **NOT REACHED** — nothing cleared A |

**M4 was the load-bearing one and it is dead.** The pre-registered falsifier was
stated as *"any candidate with a short leg negative at k = 5 and beyond, at any
N"*, and 16 cells qualify. The sharpest:

| axis | candidate | N | k | short leg | spread | t |
|---|---|---:|---:|---:|---:|---:|
| A | `macd_line` | 10 | 8 | **−35.2 bp** | +71.0 | +2.22 |
| A | `macd_hist` | 10 | 13 | **−23.7 bp** | +85.0 | +2.79 |
| B | `close_in_range` | 10 | 5 | **−8.1 bp** | +65.8 | **+9.70** |

This is the first evidence in D264–D288 that a score on this data **sorts losers**
rather than sorting *rises less* from *rises more*. It does not produce a
strategy — none of these cleared the floor — but the programme's central claim
was that the failure was universal, and it is not.

---

## The two floors disagree, and that is the finding

Gate A was run on **two statistics from the same 200 shared-offset draws**. This
is a **disclosed departure**: the pre-registration fixed the construction
("best-of-31, one shared offset vector, D277's construction") without naming the
statistic. The change was made **after seeing the observed values and before
seeing either floor**, and it makes the test HARDER — a survivor must clear both.

| floor (p95) | value | null max: mean / p50 / max | clears it |
|---|---:|---|---|
| **spread** | **+231.6 bp** | +139.1 / +129.0 / +306.4 | **none** |
| **t** | **+7.53** | +5.13 / +4.96 / +9.34 | `close_in_range` +15.88, `lower_wick` +8.70 |

**Why it was needed.** Maximising raw spread crowns the noisiest cell. It ranked
`md` first at +163.1 bp on a t of +1.31, while `close_in_range` — the strongest
candidate in the study by six times the signal-to-noise — placed nowhere. The
null's *median* draw is +129.0 bp: chance routinely manufactures a bigger number
than anything real in the mine. A magnitude floor on this statistic is close to
uninformative.

**`close_in_range` at t +15.88 is 1.70× the null's single largest draw of +9.34**,
not merely its 95th percentile. And its magnitude, +90.6 bp at the peak-spread
cell, sits **below the null's median**. Both statements are true at once. It
fails the gate and stays failed.

## R7: the null distribution, not the percentile alone

Both nulls are wide and both are decisive in the direction they measure. The
spread null's max (+306.4) exceeds every observed candidate, so the spread test
has **no power to distinguish anything here** — that is a property of the
statistic, not of the candidates. The t null is tight (p50 +4.96, max +9.34) and
does separate: two candidates sit outside it, one by a wide margin.

---

## All 31, at their PEAK-t cell

Both legs, always. The peak-**spread** cell and the peak-**evidence** cell are
different cells, and reporting only the first is how `md` outranks
`close_in_range`. Reproduce with `scripts/d288_summary.py`.

| ax | candidate | N | k | long | short | spread | t | cov | what it measures |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| B | **close_in_range** | 10 | 1 | +29.6 | **−21.1** | +50.7 | **+15.88** | 99.6% | where the session settled in its range |
| B | **lower_wick** | 25 | 1 | +13.9 | −2.6 | +16.5 | **+8.70** | 99.6% | rejection of lower prices |
| B | body_frac | 10 | 1 | +11.4 | −6.6 | +18.1 | +4.82 | 99.6% | how much of the range the body took |
| A | macd_hist | 50 | 20 | +93.3 | +38.9 | +54.4 | +4.16 | 100% | MACD line minus its signal |
| F | id_mean | 10 | 1 | +27.8 | −18.5 | +46.3 | +3.36 | 100% | trailing mean INTRADAY return |
| A | macd_line | 50 | 5 | +28.4 | −2.3 | +30.7 | +3.24 | 100% | fast EMA minus slow EMA |
| A | *hist_L* | 25 | 5 | +66.0 | +13.5 | +52.5 | +2.86 | 100% | *calibration — D286's score* |
| D | dist_lvn | 25 | 10 | +78.5 | +38.6 | +39.9 | +2.81 | **82.1%** | distance to nearest low-volume node |
| A | md | 25 | 2 | +58.6 | +4.3 | +54.3 | +2.62 | 100% | level inside the Impulse log band |
| F | on_persist | 10 | 30 | +172.7 | +100.6 | +72.1 | +2.60 | 100% | does the gap direction repeat |
| F | on_share | 10 | 30 | +201.0 | +106.9 | +94.1 | +2.15 | 99.7% | overnight share of total move |
| D | dist_hvn | 10 | 13 | +91.9 | +51.6 | +40.3 | +1.89 | 99.9% | distance to nearest high-volume node |
| C | signed_vol | 25 | 20 | +136.3 | +118.5 | +17.8 | +1.66 | 99.6% | participation signed by direction |
| F | on_mean | 25 | 5 | +50.5 | +21.8 | +28.6 | +1.64 | 100% | trailing mean OVERNIGHT return |
| A | trailing_return | 10 | 5 | +99.7 | +44.6 | +55.1 | +1.48 | 100% | plain trailing return |
| D | mass_here | 10 | 1 | +4.9 | +3.0 | +2.0 | +0.69 | 99.9% | volume traded at the current price |
| B | gap_frac | 25 | 10 | +77.7 | +70.9 | +6.8 | +0.67 | 100% | the overnight leg alone |
| F | on_minus_id | 25 | 20 | +135.9 | +117.8 | +18.1 | +0.66 | 100% | overnight minus intraday |
| E | vol_ratio | 10 | 8 | +44.7 | +38.9 | +5.8 | +0.33 | 99.8% | volatility REGIME, not level |
| C | vol_trend | 50 | 30 | +179.9 | +178.4 | +1.5 | +0.13 | 99.6% | participation building or fading |
| D | mass_imbalance | 10 | 40 | +189.2 | +188.0 | +1.2 | +0.04 | 99.9% | traded mass above minus below |
| E | cs_spread | 25 | 1 | +4.5 | +4.5 | −0.0 | −0.01 | 100% | trailing Corwin–Schultz half-spread |
| E | rvol21 | 10 | 20 | +41.3 | +55.2 | −13.8 | −0.16 | 100% | 21-bar return volatility |
| E | range_over_atr | 50 | 13 | +68.1 | +71.5 | −3.3 | −0.61 | 99.7% | today's range vs its own norm |
| E | atr_norm | 25 | 2 | +6.4 | +25.9 | −19.5 | −1.25 | 100% | volatility LEVEL |
| C | dollar_vol | 50 | 13 | +73.8 | +83.1 | −9.3 | −1.47 | 99.6% | participation in money |
| C | vol_z | 10 | 13 | +71.9 | +90.1 | −18.2 | −1.61 | 99.6% | rel_vol over its own dispersion |
| B | wick_asym | 25 | 30 | +148.2 | +166.4 | −18.2 | −1.79 | 99.6% | which side did the rejecting |
| B | range_frac | 50 | 1 | +3.8 | +10.6 | −6.8 | −2.07 | 100% | intrabar range over close |
| B | upper_wick | 50 | 30 | +153.0 | +170.1 | −17.2 | −2.20 | 99.6% | rejection of higher prices |
| C | rel_vol | 50 | 13 | +70.6 | +88.7 | −18.1 | −2.99 | 99.6% | log volume vs trailing median |

**A negative spread is not a failure, it is an inverted ranking** — `rel_vol`'s
−18.1 bp says high-participation names outperform low. D288 pre-registered ONE
direction per candidate; reading the other way is a second look per candidate
that no floor here prices, so it is **reported and not scored**.

### The k = 1 cluster is the bid–ask bounce, not an edge

The largest |t| values in the whole study sit at **k = 1**: `rel_vol` −37.6 bp
(t −6.49), `dollar_vol` −40.9 (t −6.71), `wick_asym` −22.6 (t −8.54),
`upper_wick` −15.9 (t −5.40). D285 measured the held names' Corwin–Schultz
spread at **33.81 bp per side**. A 40 bp one-day effect does not clear a ~67 bp
round trip. Microstructure, priced out before it starts.

---

## Gate 0 — independence, and one surprise

**PASS: 12.72 effective candidates of 31** against a bar of 3.0. Per axis:
B 4.24/7, F 3.55/5, E 2.86/5, D 2.63/4, A 2.54/5, C 2.00/5. First component
holds 16.8% of variance.

Ranked **within bar**, not within symbol — a declared departure from D268, whose
convention suits a consensus rule that ranks per name. This book is purely
cross-sectional, and D280 G2 already reported a pooled correlation for a
cross-sectional book and had to withdraw it.

Two between-axis pairs breached ρ 0.70:

- `range_frac` (B) vs `atr_norm` (E) at **+0.757** — **disclosed in advance**.
- `md` (A) vs `mass_imbalance` (D) at **−0.844** — **not disclosed, and a genuine
  surprise.** A price-band level and a volume-profile mass imbalance are
  near-mirror rankings. Nothing in D268, D270, D272 or D280 predicted it, and it
  means the volume-profile axis is closer to a price transform than its
  construction suggests.

## Ledger

| | |
|---|---:|
| fresh — 31 candidates | **31** |
| **second gate-A statistic (disclosed departure)** | **+1** |
| carried under [R13](../RULES.md#r13) | **145** |
| **total** | **177** |

D280's 165 statistics remain disclosed and not carried; they shaped the search
space and no floor prices that.

---

## What this cost and what it bought

Eleven closures now sit on this fixture. D288 differs from the ten before it in
one respect: **it was the first to state, in advance and in writing, what would
make it wrong — and one of those conditions fired.** M4 is dead. That is worth
more than another negative.

## Stop, and the one thing carried forward

**The mine is closed.** The holdout (`us_shorts_daily_holdout.csv.gz`, 803 names,
272 dead, 2,156,127 rows, built at `2bdf6c5`) **was never read and remains
unspent.** That is the correct outcome, not a consolation: it is the asset the
whole design existed to protect.

**Not promoted, and recorded as an open question rather than a lead:**
`close_in_range` is evidenced at **1.70× the null's largest draw** while being
too small to matter, and its short leg goes **negative at k = 5 with t +9.70**. A
future study wanting to test it must **pre-register it on its own terms** with a
statistic chosen before the data is seen — reusing D288's numbers to justify
D289 would be exactly the post-hoc selection this design was built to refuse.

**No book entry.** [`docs/BOOK.md`](../BOOK.md) is unchanged; the prop book
remains empty.
