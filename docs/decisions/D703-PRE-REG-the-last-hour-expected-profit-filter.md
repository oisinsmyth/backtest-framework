# D703 PRE-REGISTRATION — an expected-profit filter on the reopened ES last-hour continuation at MES: trade only when the projected gross covers twice the cost, from a size model of the prior hour's move, dealer gamma and implied vol

*2026-09-30.*
- *The principal chose the design after [D702](D702-DIAG-the-last-hour-edge-is-big-move-shaped.md)'s oracle profile:*

  | choice | the principal's answer |
  |---|---|
  | inputs | "Prior hour's size \|F5\|/σ, Dealer gamma (short gamma), Implied vol (ln IV)" |
  | rule | "Expected-profit template" |
  | restrictions | "None" |
  | confirmation | "Pre-register, hold the slice" |

- *The line was reopened by the principal on 2026-09-30
  ([D618](D618-STAGE-0-RESULT-the-band-around-the-price-was-the-signal.md), appended section).*
- *Numbered D703: D702 is the highest on every branch and in every commit subject, and the other session was told.*
- ***Committed alone, before its runner exists.***

## 0. What is known, and what this adds

**The mechanism (Gate 1 of the principal's template) is D618 §3c's.** The unfiltered continuation earns gross +$3.47
a MES trade, which ranks 0.999 against an enumerated rotation. D702 reproduced it. That was a disclosed look, not a
pre-registered test, so it is stated here rather than re-scored.

**What D702 showed** (hindsight; nothing fitted):
- **The edge is big-move-shaped.** The size-only oracle's top 20 % nets +$12.78 a trade.
- **The prior hour's own size keeps most of it:** +$8.87.
- **Short gamma helps:** with a big prior hour, +$14.18 gross.
- **Implied vol forecasts size** (Spearman 0.48) but is monotone only weakly on P&L.

**This record freezes one filter built from those three inputs,** scores it walk-forward in-sample as development,
and freezes the confirmation rule for data it has not seen.

**The inputs were chosen after seeing D702's profile, so the in-sample score is optimistic by construction.** Only
the held slice can confirm.

## 1. The objects

**The candidates** (D618 §3c; D702's population):
- **The trade:** at 15:30, sign(F5) with F5 = ln(P15:30 / P14:30), held 15:30 → 16:00.
- **The sessions:** every non-roll ES session with F5 ≠ 0.
- **Pricing at 1 MES:** gross = sign(F5) × (P16:00 − P15:30) × $5; net = gross − $4.42.
- **The window:** 2016-01-04 → 2023-12-29.

**The size model: a projected |15:30 → 16:00 move| in $, known at 15:30.**
- **The target:** y = |P16:00 − P15:30| × $5.
- **The features and their declared signs:**

  | feature | what it is | sign |
  |---|---|---|
  | x1 = ln(\|F5\| / σ_F5) | σ_F5 is the trailing standard deviation of F5 over the previous 252 sessions (minimum 60, shifted one session) | + |
  | x2 = G_SUM | dealer gamma: SPX GEX plus the ES book, through D688's panel | − (short gamma is a bigger move) |
  | x3 = ln IV | D691's prior-close at-the-money implied vol | + |

- **The fit:** walk-forward. D671's `size_forecast`: standardised features times their declared signs, non-negative
  slopes on demeaned data, a free intercept, and an expanding fit on earlier candidates only. **Burn-in: 250
  candidates.**
- **The output:** P_T, the projected $ move, floored at $1.25 (one MES tick).

**The expected-profit rule (D649 / D666's template):**
- **π̂_T:** the mean of gross / P over earlier candidates with finite P, after a burn-in of 40.
- **The rule:** take the trade when **π̂_T × P_T ≥ 2 × $4.42 = $8.84.**
- **Projected gross** = π̂_T × P_T.

## 2. Development scoring (in-sample, walk-forward; declared here, run once)

**The development verdict.** The filter PASSES DEVELOPMENT if all of the following hold on the evaluated candidates
(those with finite P and π̂ past its burn-in):

| # | condition |
|---|---|
| (a) | **calibration** (D690, `filter_oracle.calibration`): the slope of realised gross on projected gross is **> 0**, over all evaluated candidates, 10 bins |
| (b) | **the filtered book:** mean net > 0 at MES, with one-sided HAC t ≥ 1.645 |
| (c) | **the rotation control** (D442's lesson): the filtered mean net exceeds the **exact p95** of an enumerated rotation of the three features, jointly, against the candidates |
| (d) | **not one episode:** filtered mean net > 0 without Feb–Apr 2020 |

**How (c) is built.**
- Rotate the three features jointly by every offset from 21 to n − 21, against the candidates' outcomes.
- Refit P, rebuild π̂ and re-filter walk-forward at each offset.
- The trades and their outcomes never move.

**Otherwise** the verdict is DEVELOPMENT FAIL, and the line closes again with the reason recorded.

**Reported, never gating:**
- **The four groups for the filtered book at MES,** net and gross side by side:
  - Sharpe with Sortino, per trade (annualised by its own count) and daily;
  - max drawdown; trades a year; hit, median and payoff; the trimmed means;
  - by year; before and after 2022-05-16; long against short.
- **The component line:** net Sharpe at one MES, $ cost, hit, skew, gross beside net, and ρ with the MACD arm (entry
  #2).
- **D690's placement:**
  - the Spearman of projected gross with realised gross, placed on D702's partial-oracle curve;
  - `assess()` against the oracle label (AUC, confusion, capture).
- **The size model's own accuracy:** the Spearman of P with realised |move|, and its final slopes.
- **Ablations:** each feature alone as the size model, the same rule. Reported only.
- **The take-everything line** on the same evaluated candidates.
- **2016–17 is declared in advance as the known weak era** (D618 §3c). It is inside the window and is not excluded.

## 3. The confirmation rule (frozen now; held until the principal releases it)

**The slice:** 2024-01-01 → 2025-02-28, never read for this trade. Forward data from 2026-09-19 is added if the
principal chooses. The vault is not used.

**The rule, unchanged from §1:**
- the size model and π̂ are refit walk-forward through the slice, using only earlier sessions;
- the same take rule, at MES.

| verdict | condition |
|---|---|
| **CONFIRM** | filtered mean net > 0 with one-sided HAC t ≥ 1.2816, **and** calibration slope > 0 on the slice's candidates |
| **FAIL** | otherwise |
| **UNRESOLVED** | fewer than 30 filtered trades |

**Power, stated before anything is spent** (from D702):
- At about 48 filtered trades a year and a per-trade sd near $85, the slice alone (about 56 trades) has an expected
  t of **about 0.8** if the in-sample effect is entirely real.
- Reaching the 1.2816 bar at full effect needs about 150 trades, about three years at this rate.
- **So the slice is held, per the principal's choice,** until the power case exists: the slice plus forward data
  reaching the needed count.
- This record states that count; the principal releases the read.

## 4. Runner assertions (each shown to raise in `--selftest`)

- **Known answers:**
  - D618 §3c (+0.6795 points, hit 0.4929 on 1,960 non-roll sessions);
  - D702's take-everything and pre-entry top-20 % lines, reproduced from the same candidates;
  - D691's d̄;
  - D688's β_G.
- **Lag:**
  - D671's `forecast_audit` on P, which refits by date on a second path;
  - a date-keyed second implementation of π̂;
  - a canary that lets σ_F5 include session T must raise.
- **Sign, in money:** a long continuation into a rising close pays; a short into a falling close pays.
- **Right quantity:** the target is |P16:00 − P15:30|, not |F5|.
- **The rotation:** offset 0 reproduces the filtered book exactly; chunk == whole across processes.
- **The seal:** no session ≥ 2024-01-01 is read in the development run. The confirmation mode refuses to run without
  the principal's word on the command line.

## 5. Speed

- The size model is one walk-forward NNLS over about 1,900 candidates.
- The rotation is about 1,850 offsets, each with its own refit. It fans out over processes on `offsets[i::N]`.
- **Projected:** under 15 minutes. Measured on a few offsets and stated before launch.

## 6. Predictions

1. **The calibration slope is positive but below 1.** π̂ × P understates the big-move days, because the direction is
   more reliable after a big hour (D702).
2. **The filtered book keeps 30–60 trades a year** at a mean net between +$3 and +$9 a MES trade.
3. **Gate (c) passes;** the rotation p95 of the filtered net sits near $0.
4. **The prior-hour-size ablation alone does about as well as the three-feature model.** Gamma and ln IV add little
   beyond it on P&L (D702's Spearmans).
5. **2016–17 and the post-2022-05-16 era are the weakest periods of the filtered book.**
