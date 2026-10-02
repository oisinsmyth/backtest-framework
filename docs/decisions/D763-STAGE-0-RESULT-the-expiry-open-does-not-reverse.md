# D763 STAGE 0 RESULT — NO EFFECT on every root: the expiry open does not reverse. If anything it continues, and expiry-day opens are quieter than other Fridays', not more pressured

*2026-10-02. Prop book.*
- *Pre-registration: [D763](D763-STAGE-0-PRE-REG-the-expiry-open-fade.md) (`d7f00423`).*
- *Runner: `scripts/stage0_d763_expiry_open.py` (`839e2bb0`), committed before its one run (system python).*
- *Output: `data/stage0_d763_expiry_open.json`. Wall 4 s.*
- *Checks:*
  - *the calendar check passed: 96 monthly expiry days, 32 quarterly; the Good Friday Thursdays 2019-04-18 and
    2022-04-14; 96 VIX days, including the Tuesdays 2019-03-19 and 2022-03-15; the three published VIX dates
    reproduced;*
  - *the lag audit (a raw-row loop on 40 sessions per root, half of them expiry days) passed;*
  - *the rotation's offset 0 reproduced Δ;*
  - *nothing dated 2024-01-01 or later was read.*

**Disclosed before the run** (the runner's commit and its self-test):
- **The expiry label recurs near-periodically**, so many rotations re-select expiry days. Here the median offset
  re-selects 25% of them, and the 90th percentile about 33%.
- **The full rotation is exact (a group) but loses power.** Dropping the overlapping offsets would have narrowed the
  null: noise passed it 22 times in 100. **The pre-registered full rotation was kept;** noise fails it 97 times in 100.

## 1. The readings: monthly expiry Fridays against other Fridays (the decision family)

x = P₀₉:₄₀ − P₀₉:₃₀ (pre-cash); y = P₁₀:₄₀ − P₀₉:₄₀.

| root | ρ_E (n) | ρ_C (n) | Δ (rotation p05 / p50 / p95; Holm p) | E2 fade gross (t) against cost | control-Friday fade | reading |
|---|---|---|---|---|---:|---|
| ES | +0.078 (96) | +0.058 (281) | +0.020 (−0.191 / −0.003 / +0.217; 1.00) | −$4.89 (−0.82) against $4.42 | −$2.51 | **NO EFFECT** |
| NQ | +0.175 (96) | −0.042 (285) | +0.217 (−0.213 / −0.006 / +0.227; 1.00) | −$7.21 (−0.74) against $4.07 | +$10.24 | **NO EFFECT** |
| YM | +0.041 (96) | +0.034 (279) | +0.007 (−0.228 / −0.001 / +0.213; 1.00) | −$2.69 (−0.55) against $3.80 | −$4.10 | **NO EFFECT** |
| RTY | +0.046 (78) | +0.028 (226) | +0.018 (−0.222 / +0.009 / +0.225; 1.00) | −$4.40 (−0.86) against $3.76 | −$2.35 | **NO EFFECT** |

- **Δ is positive on every root.** On expiry Fridays the opening move continues to 10:40 at least as much as on
  other Fridays. On NQ, Δ (+0.217) sits just below the null's upper p95 (+0.227).
- **The fade loses gross everywhere.**

**The premise itself fails.** The mechanism needs the expiry open to carry extra, non-informational pressure, but it
carries less:

| root | mean \|x\| per micro, expiry / other Fridays | sd(y), expiry / other |
|---|---|---|
| ES | $21.3 / $26.5 | $57 / $79 |
| NQ | $41.2 / $50.3 | $94 / $135 |
| YM | $22.4 / $20.4 | $47 / $59 |
| RTY | $20.6 / $26.0 | $46 / $60 |

The expiry opening ten minutes, and the hour after them, are calmer. That is consistent with long-gamma dealer
positioning into expiry damping the open, not with a settlement imbalance pushing it.

## 2. The E2 fades (monthly; one micro; four groups)

| root | trades | net mean (median) | win | skew | daily net Sharpe (Sortino) | gross Sharpe (Sortino) | max DD |
|---|---:|---|---:|---:|---|---|---:|
| ES | 94 | −$9.31 (−$10.04) | 34.0% | +0.63 | −0.55 (−0.75) | −0.29 (−0.42) | $930 |
| NQ | 95 | −$11.27 (−$7.07) | 45.3% | −0.15 | −0.41 (−0.53) | −0.26 (−0.35) | $1,495 |
| YM | 95 | −$6.49 (−$5.80) | 44.2% | +0.22 | −0.47 (−0.62) | −0.20 (−0.27) | $816 |
| RTY | 78 | −$8.15 (−$12.51) | 38.5% | +0.87 | −0.63 (−0.85) | −0.34 (−0.49) | $783 |

- **The 1% trims are empty:** below 100 trades, 1% is zero trades, so the ex-top, ex-bottom and both-trim means equal
  the mean.
- **The break-even cost is negative** (the gross is below zero).
- **ρ with F2, C1 and D737** lies within ±0.06 on every root.
- **The extremes are the 2020 and 2022 expiries:** ES +$164 on 2022-06-17 and −$146 on 2023-10-20; NQ −$279 on
  2022-04-14. By-year ρ_E swings in sign (ES +0.30 in 2019, −0.54 in 2023).

## 3. VIX Wednesdays (the reported family; their own Holm)

| root | ρ_E (n) | ρ_C (n) | Δ (p05 / p95) | fade gross (t) | reading |
|---|---|---|---|---|---|
| ES | +0.169 (95) | −0.056 (318) | **+0.225** (−0.186 / +0.209) | **−$10.56 (−2.12)** | NO EFFECT |
| NQ | +0.228 (95) | −0.032 (318) | **+0.261** (−0.226 / +0.225) | −$7.91 (−0.88) | NO EFFECT |
| YM | +0.067 (95) | −0.039 (318) | +0.106 | −$1.82 (−0.48) | NO EFFECT |
| RTY | +0.130 (77) | −0.054 (255) | +0.184 | −$4.73 (−0.83) | NO EFFECT |

**The opening move on VIX expiry continues to 10:40 on every root.** On ES and NQ, Δ lies above the rotation's p95,
in the tail opposite the one the test was built for. Following the move from 09:40 to 10:40 would have grossed
+$1.82 to +$10.56 per micro.
- **This is POST HOC:** a one-sided test read for the other side.
- **It does not last to the close:** ρ(x, y_close) on ES and NQ VIX days is −0.08 and −0.09.
- **It is not a lead for the prop book.** There are about 12 events a year, so the held slice holds about 14, which
  cannot confirm it.

## 4. Reported, never gating

**Quarterly against the other monthly expiries** (ρ; fade gross):

| | ES | NQ | YM | RTY |
|---|---|---|---|---|
| quarterly | −0.01; −$1.12 | +0.06; +$0.77 | −0.05; +$0.23 | **−0.30; +$14.12** |
| other monthly | +0.10; −$6.66 | +0.25; −$11.25 | +0.05; −$4.17 | +0.29; −$13.65 |

- **RTY's quarterly expiry reverses** (about 26 events). D762 also found RTY's quarterly expiry reversing after the
  cash close (ρ −0.32, n 26).
- **Two post hoc cells on the same 26 days point the same way.** It is a curiosity, not evidence: about 4 events a
  year.

**The other horizons and pressures:**
- **The y_close horizon** (09:40 → 16:00): the monthly fade loses on every root (gross −$4.78 to −$29.34).
- **The gap as the pressure:** ρ(gap, y) is within ±0.10 on expiry days and on control days.

## 5. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | E1 fails on every root (P 0.6) | **held** |
| P2 | if any root passes, ES or RTY | moot (none passed) |
| P3 | E2 below the cost everywhere (P 0.7) | **held**: every E2 gross is negative |
| | P(PREMISE HOLDS) ≈ 0.08 | none |

## 6. What it shows

**The forced-settlement story does not show up at the expiry open.**
- The expiry opens are smaller, not larger.
- The opening move continues at least as much as on other Fridays, and on VIX Wednesdays it continues more.
- A plausible reading: the AM-settlement imbalance is small and pre-hedged, while dealers' long gamma into expiry
  dampens the open.

**Across the scheduled-flow candidates, only the auctions and settlement windows clear their comparisons:**

| record | where the flow is | what was found |
|---|---|---|
| D710 | the Treasury auction | its gross clears; its net does not |
| D630 | commodity settlement windows | its gross clears; its net does not |
| D762 | the index cash close | barely reverses |
| D763 | the index expiry open | does not reverse |

On the index micros, the clock-tied reversals are either absent or below the fee.

**The principal's call:** whether to close the expiry line. The post hoc VIX-Wednesday continuation and the
RTY-quarterly reversal are recorded and not pursued.
