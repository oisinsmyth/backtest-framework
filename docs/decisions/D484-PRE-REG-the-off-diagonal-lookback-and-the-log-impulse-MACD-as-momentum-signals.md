# D484 — PRE-REG: the off-diagonal lookback, and the log impulse MACD as a momentum signal

**2026-09-12, committed before the runner exists** (CLAUDE.md, [R8](../RULES.md#r8)).
Both parts requested by the principal.

---

## 0. The design error this corrects, stated plainly

[D474](D474-RESULT-the-pre-registered-bar-was-not-met-but-four-of-five-predictions-broke-toward-the-hypothesis-and-the-test-was-underpowered-where-it-mattered.md)
and [D475](D475-RESULT-NO-TRANSFER-the-ES-gradient-was-in-sample-selection-and-the-sign-flips-on-seven-unseen-roots.md)
both locked the signal's **lookback equal to the holding period**. I took that from the
canonical time-series-momentum form (Moskowitz-Ooi-Pedersen: sign of the past 12 months, held
12 months) and never asked whether it suited this application.

**It does not. A signal's measurement window and its decay horizon are independent quantities.**
How long it takes to *measure* a trend has no necessary relation to how long that trend then
persists. Locking them tested a single line through a two-dimensional space and called the space
empty. That is the same error as *construction vs axis*, and the principal caught it.

**What is and is not spent.** D474 (ES) and D475 (7 roots) examined **only the diagonal**, both
with volatility buckets. The **off-diagonal has never been looked at on any root**, and **no
MACD variant has been looked at on any root at any horizon**. So:

- **off-diagonal cells (L ≠ H): PRIMARY**, on all 8 roots.
- **diagonal cells (L = H): DESCRIPTIVE ONLY**, reported as a replication of D475, carrying no
  evidential weight.
- **MACD: PRIMARY on all 8 roots**, wholly unspent.

## 1. Data, fixed now

| | |
|---|---|
| fixture | `data/fixtures/fut_sessions_hourly.csv.gz` + `.meta.json` (spec `59a151d`) |
| series | per root, the 23 hourly segments per session **concatenated in session order** into one continuous hourly series. Sessions abut with a **one-hour gap** (16:59 → 18:00); that gap is left in place and not interpolated. |
| roots (8) | **ES, NQ, YM, ZN, ZB, GC, CL, 6E** — RTY excluded, it fails gate **G2** (reverting roll 2020-06-14) |
| window | **2016-01-04 → 2023-12-29**, honouring each root's `usable_start`. **2024+ sealed**; a gate raises if any row past 2023 is reached. |
| contract | `same_front` sessions only, **and** every bar used must have the same contract across its whole lookback *and* holding window. For the EMA constructions, the trailing **78 bars (3 × slow)** must be one contract. |
| gates | every root's own G1–G5 read and required to pass |

## 2. PART A — the off-diagonal lookback, fixed now

**Signal:** `sign( p[t] − p[t−L] )` on log close, where `p = log(close)` and L is the lookback
in hours. **Trade that sign, entered at the open of hour t+1, held H hours, exited at the close
of hour t+H.**

- **Lookback L ∈ {1, 2, 3, 5, 8, 13} hours**
- **Hold H ∈ {1, 2, 3, 5} hours**
- **24 (L, H) cells; the 4 with L = H are descriptive, leaving 20 primary cells per root.**

Entries are formed at **every hour** t, so windows overlap. That is deliberate — it is what
buys the power D474 lacked — and it is why the null in §4 must be a rotation rather than a
per-observation shuffle.

## 3. PART B — the log impulse MACD, fixed now

**Both readings of the name are implemented, and which is primary is declared here, not after
seeing results.**

**B1 (PRIMARY) — Impulse MACD on log prices**, LazyBear's construction, the one whose
distinctive feature is a **zero state**:

    p_h, p_l, p_c = log(high), log(low), log(close)          hourly
    mi = ZLEMA( (p_h + p_l + p_c)/3 , 34 )
    hi = SMMA( p_h , 34 )
    lo = SMMA( p_l , 34 )
    md = mi − hi   if mi > hi
         mi − lo   if mi < lo
         0         otherwise            <-- the impulse: no signal inside the band
    sb = SMA( md , 9 )
    hist = md − sb

**Signal = sign(hist), and `md == 0` is a NO-TRADE state, not a flat position.** The share of
bars in the zero state is reported; it is the indicator's own timing filter and is the reason
this variant is interesting rather than being a re-parameterised MACD.

**B2 (SECONDARY) — plain MACD histogram on log close:**

    macd = EMA(p_c, 12) − EMA(p_c, 26);  sig = EMA(macd, 9);  hist = macd − sig
    Signal = sign(hist)

**PARAMETERS ARE THE CANONICAL ONES AND ARE NOT TUNED.** 12/26/9 for B2, 34/9 for B1 — the
published defaults, declared now. MACD has three free parameters and tuning them is the classic
overfit; **any other parameter set is a separate pre-registration, not a variant of this one.**

**Hold H ∈ {1, 2, 3, 5} hours** for both, giving 4 primary cells per root for B1.

Definitions used: `SMMA(x,n)` is the Wilder/running mean `s[t] = s[t−1] + (x[t] − s[t−1])/n`;
`ZLEMA(x,n)` is `EMA(2·x[t] − x[t − lag], n)` with `lag = (n−1)//2`. Both are stated here so the
runner cannot quietly pick a different smoother.

## 4. The nulls, fixed now — and why a rotation, not a shuffle

**Both parts produce AUTOCORRELATED signals**: Part A's overlapping windows share data, and
MACD is a smoothed series by construction. **A per-observation sign shuffle would destroy that
autocorrelation and give a null that is far too narrow** — the standing error being
*a control must break the claimed ingredient* and nothing else.

- **R1 (PRIMARY NULL) — circular rotation of the SIGNAL series** against the return series,
  within each root, by a random offset. Preserves the signal's own autocorrelation, the return
  series' volatility clustering, and both marginal distributions **exactly**; destroys only the
  alignment between them. Which object is rotated is stated: **the signal**, on the root's own
  valid-bar mask.
- **R2 (SECONDARY NULL) — per-observation sign randomisation**, reported alongside so the gap
  between R1 and R2 is visible. **R2 is expected to be the more lenient of the two**, and if it
  is not, that is itself a finding about the signal's autocorrelation.

**2,000 draws each. Report p50 and p95, and carry the bootstrap SE of the p95.** An observed
statistic within **2 SE** of the p95 is recorded **UNRESOLVED** (D373's rule). One-sided:
momentum predicts a positive edge.

## 5. Two declared statistics per part, with two separate bars

Because "is there anything on average" and "is any cell exceptional" are different questions,
**both are declared now with their own bars.** Clearing either is a distinct claim; clearing
neither is a failure.

Per cell, the statistic is the **gross edge in σ units**: `mean( signal · r_fwd ) / σ(r_fwd)`,
which is dimensionless and comparable across roots and horizons (this is why 6E's missing tick
size does not matter here).

| | statistic | bar |
|---|---|---|
| **P1 pooled** | mean of the per-cell edge over all primary cells and all 8 roots | exceeds **R1**'s p95 by > 2 SE |
| **P2 family max** | the largest per-cell edge, where a cell is (root, L, H) | exceeds **R1**'s family-max p95 by > 2 SE — the null's own maximum over the same number of cells |

**TRADEABLE** additionally requires, for a cell on a root with a committed micro contract
(ES/NQ/YM): net edge > 0 in ticks at that micro's cost — and note MNQ's cost is **7.009 ticks**
against MES's 3.409, computed in D475, so NQ faces roughly twice the bar.

**COMPONENT** requires `COMPONENTS_PROP.md` C-a–C-e on a daily P&L series at minimum size, its
own runner and its own record. **Nothing enters the ledger or either book off this runner, and
2024+ stays sealed regardless of outcome.**

## 6. Predictions

- **Z-a.** Part A's pooled P1 **fails** R1's p95. *Reason: the diagonal failed at 68 SE on 7
  roots, and going off-diagonal changes the measurement window, not the fact that the variance
  ratio never exceeds 1.02 on any grid or clock.*
- **Z-b.** Part A's family max P2 **fails** too, once the null's own family maximum over the
  same 160 cells is used as the comparator rather than a per-cell threshold.
- **Z-c.** **The off-diagonal will beat the diagonal**, i.e. the best off-diagonal cells will
  have L > H — a longer measurement window than holding period. *This is the principal's point
  and I expect it to be right about the ORDERING even if every cell fails its bar.*
- **Z-d.** B1's **zero state will cover more than 40% of bars**, and B1 will score better than
  B2 on the pooled statistic — the no-trade filter helping even if neither clears.
- **Z-e.** R2 (sign shuffle) gives a **narrower** null than R1 (rotation), so the naive null
  would have produced a false pass somewhere that R1 refuses. *If this breaks, my reason for
  choosing the rotation was wrong.*
- **Z-f.** No cell is TRADEABLE at micro cost on any root.

## 7. What would make me wrong

Either P1 or P2 clearing R1's corresponding p95 by more than 2 SE. **I expect Part A to fail and
Part B to fail, and I expect Z-c to hold** — that the off-diagonal ordering is real even where
the levels are not significant. If Z-c holds and the bars fail, the honest reading is that the
principal's structural point is correct and the effect is still not there.

## 8. Stated limitations, before any number exists

1. **Hourly resolution**, and the one-hour inter-session gap is left in the series rather than
   interpolated — an EMA crossing it mixes 16:59 and 18:00 bars.
2. **EMA warm-up cannot be contract-pure.** An EMA has infinite memory; requiring the trailing
   78 bars to be one contract is a pragmatic cut, declared, not exact.
3. **Overlapping windows** in Part A mean the naive SE is meaningless. Only the rotation null's
   distribution is used for inference, never a t-statistic on overlapping data.
4. **Canonical parameters only.** 12/26/9 and 34/9. No search, and no claim that these are the
   best; a parameter search is a different and much more dangerous study.
5. **The volume-clock exit (D472, +1.18 pp) is not applied**, so net figures understate.
6. **In-sample.** 2024+ is the confirmation slice and is not read.
7. **Eight roots are not eight independent draws** — ZN/ZB are both US rates, NQ/YM/ES all
   equity index. Effective breadth is nearer 5.
