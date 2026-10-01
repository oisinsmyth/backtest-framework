# D722 DIAG RESULT — no measured variable explains 2022. Each line's 2022 is a different thing (HO scale, NQ F2 direction, D699 only in 2022 at all in volatility units); the index lines' 2022 was January to mid-May; the lines are separate day to day but share the year

*2026-10-01. Pre-registered in [D722](D722-DIAG-PRE-REG-why-2022-scale-regime-or-one-bet.md) (`f25e4726`), with
D722-A1 (`7880c5a0`) and D722-A2 (`2818bb17`).*
- *Phase 0, the builders, is `d48f9032`. The four Part runners are `8a8c99f8`, run once each.*
- *Outputs: `data/diag_d722_part_{a,b,c,d}.json`.*
- *In-sample 2016 → 2023-12-29. No vault and no 2024+ value read. No slot spent, and no line changed.*
- *The principal: "Ok, lets take on the 'Why 2022' question"; "for execution send out an opus agent for each part and I
  would like you to orchestrate".*

## 0. The answer in five lines

1. **No variable known before the trade explains 2022 on any line.** That covers every hypothesis we listed: realised
   and implied vol, dealer gamma, rates volatility, oil volatility, trend, direction, macro days, stimulus windows, the
   micro share and the chip cycle. **All six objects read UNEXPLAINED.** No single cell passes Holm.
2. **The lines are not one story:**
   - **Heating oil's 2022 is scale.** Bigger moves; per unit of volatility, 2018–19 were better years.
   - **The MACD arm's 2022 is scale.**
   - **NQ F2's 2022 is direction:** the only REGIME reading.
   - **ES F2 is mixed.**
   - **D699 V1 is positive in volatility units only in 2022** (and faintly in 2016–17).
3. **The index lines' 2022 is really January → mid-May 2022.**
   - The unfiltered last half-hour earned **all** of its 2022 before 2022-05-16 (the daily-0DTE date), and lost after.
   - ES F2 and NQ F2 took **56 of their 65–66 2022 trades** in that stretch.
   - **Rates volatility stayed high through 2023, when these lines earned little.**
4. **Macro-event days carry nothing.** On the unfiltered base they are net negative. The war's first ten weeks carry the
   ES base's 2022 (76 %, CONCENTRATED); heating oil there is borderline.
5. **Day to day the lines are SEPARATE, but they share the year.** The equal-weight index book (ES F2 + NQ F2 + D699)
   earns **77 % of its net in 2022**, with daily correlations of 0.13–0.15 between F2 and D699.

## 1. The lines' 2022 against the rest (Part A; per trade, one micro, or one HO)

| line | 2022: n, net (gross) a trade | ex-2022: n, net (gross) | 2022 net Sharpe (Sortino) | ex-2022 net Sharpe (Sortino) | 2022's share of net |
|---|---|---|---|---|---:|
| L1 ES F2 | 66, +$30.22 (+$34.64) | 186, +$7.17 (+$11.59) | 2.01 (3.84) | 0.54 (0.88) | 60 % |
| L2 NQ F2 | 65, +$58.03 (+$62.10) | 206, +$9.01 (+$13.08) | 2.75 (5.39) | 0.50 (0.79) | 67 % |
| L3 D699 V1 | 146, +$30.68 (+$35.10) | 426, +$3.55 (+$7.97) | 1.36 (2.69) | 0.25 (0.39) | 75 % |
| L4 HO F2 | 60, +$285.62 (+$295.82) | 179, +$50.08 (+$60.28) | 1.59 (3.18) | 0.78 (1.21) | 66 % |
| K1 MACD arm (control) | 213, +$26.41 (+$30.32) | 1,495, +$6.55 (+$10.47) | 1.09 (1.56) | 0.62 (0.94) | 36 % |
| K2 ES take-everything | 244, +$5.65 (+$10.07) | 1,116, −$1.53 (+$2.89) | 1.14 (1.84) | −0.44 (−0.65) | > 100 % |
| K2 NQ take-everything | 246, +$15.03 (+$19.10) | 1,143, −$1.08 (+$2.99) | 2.12 (3.56) | −0.23 (−0.34) | > 100 % |

- **Annualisation:** Sharpe and Sortino are per trade × √(trades per 252 calendar sessions) (D722-A2).
- **Medians in 2022:** L1 +$24.33, L2 +$52.93, **L3 −$10.67 (below its +$30.68 mean: its 2022 is carried by the right
  tail)**, L4 +$120.
- **Lines scored by year only** (their runners read 2024+, so they were not rerun). 2022's share of net through 2023:

  | line | 2022's share |
  |---|---:|
  | NG D630, full size | 101 % |
  | CL D648 | 54 % of gross; 258 % of a thin net |
  | ES D717 | 74 % |
  | YM F2 | 53 % |
  | RTY F2 | 203 % of a thin net |
  | NQ compression C1 | 40 % |
  | D689, full ES | 27 % |
  | D708 | net-negative overall |

  **Most of the repo's surviving lines lean on 2022.**

## 2. Part A — bigger dollars, more trades, or better direction?

**The decomposition.** G_2022/G_R = (count rate) × (mean \|gross\|) × (efficiency Σg/Σ\|g\|). The shares are of the
log excess, and Δe/SE comes from a week-block bootstrap (10,000 draws).

| line | count | size | efficiency | Δe (SE, z) | reading | 2022's share of gross, in \$ → in vol units |
|---|---:|---:|---:|---|---|---|
| L1 ES F2 | 0.27 | 0.26 | 0.47 | +0.21 (0.16, 1.30) | **MIXED** | 51 % → 47 % |
| L2 NQ F2 | 0.17 | 0.22 | 0.62 | +0.34 (0.16, **2.18**) | **REGIME** | 60 % → 57 % |
| L3 D699 V1 | 0.37 | 0.21 | 0.42 | +0.15 (0.12, 1.28) | **MIXED** | 60 % → the only large positive year |
| L4 HO F2 | 0.20 | **0.54** | 0.27 | +0.13 (0.16, 0.81) | **SCALE** | 62 % → **30 %** |
| K1 MACD arm | 0.00 | **0.92** | 0.09 | +0.01 (0.10, 0.10) | **SCALE** | 29 % → 18 % |
| K2 ES | 0.01 | 0.43 | 0.56 | +0.09 (0.10, 0.94) | MIXED | 43 % → 38 % |
| K2 NQ | 0.01 | 0.31 | 0.68 | +0.17 (0.09, 1.81) | MIXED | 58 % → 61 % |

**What the table says:**
- **Heating oil and the arm made their 2022 on bigger moves.**
  - HO's direction efficiency in 2022 (0.32) was below 2018's and 2019's (0.43 and 0.55).
  - In volatility units, its best years are 2018–19.
- **NQ F2 is the one line whose direction was genuinely better in 2022:** efficiency 0.49 against 0.12–0.17 in
  2019–2023's other years.
- **D699 V1 is negative in volatility units** in 2018, 2019, 2020, 2021 and 2023 (mean u −0.06 to −0.16), and positive
  in 2022 (+0.11) and faintly in 2016–17. Over 2016–2023 its sum in volatility units is negative (−20.2). **Its edge,
  measured per unit of risk taken, is a 2022 phenomenon.**
- **2018, the other tightening year, is no rerun of 2022:**
  - it reads COUNT on L1 and L4, MIXED on L2 and L3, and SCALE on K1 and both K2s;
  - on L2, L3, K1 and both K2s, 2018 is below the line's other years.

## 3. Part B — which variable carries it? None.

**The method.** For each object and variable:
- fit u (the volatility-normalised gross) on X outside the held-out year;
- predict 2022 out of year;
- φ = the share of 2022's excess the prediction recovers;
- the slope's t comes from the fit without 2022, clustered by week, with Holm across each object's variables.

**The results:**

| object | 2022 excess in u | variables passing Holm | joint model leaves | reading |
|---|---:|---|---:|---|
| K2 ES | +0.088 | none | 100 % | UNEXPLAINED |
| K2 NQ | +0.128 | none | 100 % | UNEXPLAINED |
| L1 ES F2 | +0.284 | none | 100 % | UNEXPLAINED |
| L2 NQ F2 | +0.353 | none | 100 % | UNEXPLAINED |
| L3 D699 V1 | +0.197 | none | 100 % | UNEXPLAINED |
| L4 HO F2 | +0.038 | none | 100 % | UNEXPLAINED |

**Worth reading anyway:**
- **Rates volatility (X4) was about one log unit above normal in 2022 (and in 2023), but carries nothing.**
  - Its slopes are 0 ± 0.1, t −0.6 to +1.6.
  - φ is −0.26 on K2 ES and −0.06 on K2 NQ.
- **The trend variable points the wrong way.** On every index object, a trendier prior 60 sessions (X6) predicts
  *less* last-half-hour continuation:
  - K2 ES t −2.19;
  - on D487's 15-minute horizon, K2 ES t −2.26 and L2 t −2.64;
  - φ −0.2 to −0.75 on the 30-minute X6, and −0.3 to −1.3 on the 15-minute one.
  - **The "trending regime" story fails as a session-level predictor.**
- **The retail proxy** (micro share, X10) recovers φ 0.55 on K2 ES and 0.46 on L1, but at t 1.35 and 1.48. It is
  nowhere near Holm, and it rests on 2019-05 onward only.
- **Oil volatility (X5)** has L2 t +2.33 and L3 t +2.58, but φ −0.06 and +0.23, and neither survives Holm. On HO, φ is
  0.02.
- **Stimulus (X9)** is zero in 2022 by construction, and its φ is 0.03 or below everywhere.

## 4. Part C — event windows in 2022

**Macro-event days** (FOMC, CPI, jobs; HO adds the EIA report):
- **Not concentrated on any line.**
- On the unfiltered base they are **net negative** in 2022 (K2 ES −$138, K2 NQ −$766).
- The eight 2022 FOMC days carry 2–5 % of the F2 lines' 2022 net.

**The war's first ten weeks (2022-02-24 → 04-29):**

| line | share of 2022 net | random-trade rank | rotation rank | reading |
|---|---:|---:|---:|---|
| **K2 ES** | **76 %** | 0.961 | 0.963 | **CONCENTRATED** |
| K2 NQ | 42 % | 0.901 | 0.813 | NOT |
| L4 HO | 72 % | 0.832 | **0.967** | NOT (borderline: the rotation null is the fairer test for a block) |
| L1 ES F2 | 37 % | 0.640 | 0.803 | NOT |
| L2 NQ F2 | 33 % | 0.558 | 0.662 | NOT |
| L3 D699 | 27 % | 0.718 | 0.716 | NOT |
| K1 arm | 56 % | 0.842 | 0.836 | NOT |

**Before and after 2022-05-16** (the date every weekday first carried a same-day SPX expiry):
- **The unfiltered base earned all of 2022 before it.**
  - K2 ES: +$1,793 before, −$414 after (130 % of the year's net before; rank 0.986, rotation 0.930).
  - K2 NQ: +$3,911 before, −$213 after (106 %; rank 0.999, rotation 0.959).
  - Both read **CONCENTRATED.**
- **The F2 lines took 56 of their 66 and 65 2022 trades before that date.** Their shares match their trade counts
  (87–88 % of net on 85–86 % of trades), so they read NOT concentrated per trade. **F2's 2022 is a January → mid-May
  2022 year.**
- D699 took only 54 of its 146 there.

**Heating oil's curve.** **Every one of HO's 60 trades in 2022 fell on a day whose curve was steeper than the 90th
percentile of 2016–2021** (front over next, at or above 0.41 %). The whole 2022 HO book sat in a backwardation squeeze.

**The top trades.** 2022's ten largest trades per line are named in the JSON.

## 5. Part D — one bet or several?

**Reading: SEPARATE.**
- **L1–L3:** 2022 Pearson ρ 0.146. The top-decile overlap is 4 of 6 against 1.29 expected, with the declared
  (conditional) p **0.013**, just above the 0.01 bar. The unconditional p is 0.0002.
- **L1–L4:** ρ 0.033, with zero overlap.
- L1–L2 (ρ 0.94) is the same trade and is not read.

**Other facts:**
- **ES F2's and D699's daily P&L are less correlated in 2022 (0.15) than in the other years (0.30).**
- The K2 regression accounts for 8 % of D699's 2022 net and 5 % of HO's (R² ≤ 0.02).
- **The book** (L1 + L2 + L3, one micro each) earns **77 % of its net in 2022**, with a diversification ratio of 0.70
  in 2022 against 0.56 in other years.

**So the lines don't win on the same days, but they win in the same year.** Diversifying across them does not
diversify away 2022.

## 6. Predictions (§8)

| # | prediction | outcome |
|---|---|---|
| 1 | L1 and L2 REGIME, with m under half | **half**: L2 REGIME (z 2.18); L1 MIXED (z 1.30); m under half on both |
| 2 | L3 COUNT with REGIME, n ≥ ⅓ | **failed**: MIXED; n 0.37 ≥ ⅓ held, but COUNT needs ½, and z 1.28 |
| 3 | L4 SCALE | **held** (m 0.54) |
| 4 | K2 REGIME on ES and NQ | **failed** (z 0.94 and 1.81) |
| 5 | X4 EXPLAINS K2 on ES or NQ | **failed** (φ −0.26, −0.06) |
| 6 | X9 and X10 explain nothing | held (X9 near-vacuous, as A1 said) |
| 7 | X5 EXPLAINS or PARTIAL on L4, NO on the index objects | **failed** on L4 (φ 0.02); NO on the index objects held |
| 8 | C1 CONCENTRATED on an index line | **failed**: macro days carry 2–5 %, negative on the base |
| 9 | SEPARATE | held (L1–L3 p 0.013, near the bar) |
| 10 | a variable that EXPLAINS 2022 predicts 2018 | vacuous: none EXPLAINS |

**My central guess** (the Fed-tightening regime, carried by rates volatility) **is wrong at the session level:** rates
volatility stayed high through 2023, and the lines earned little in 2023.

## 7. What it means (per §6)

- **2022 is not one measurable regime these lines share.** It is a stretch of calendar (January → mid-May for the index
  lines) that no pre-trade variable here identifies. **In-sample, 2022 is a one-off, and the ex-2022 figures are the
  better guide to each line's size.**
- **NQ F2 (D716, programme slot 7):**
  - Its 2022 is REGIME: direction, not scale. Nothing measured tells when that regime is on.
  - Its ex-2022 net is +$9.01 a MNQ trade (net Sharpe 0.50, Sortino 0.79). After 2022-05-16 it was +$14.15 (D716 §0).
  - **D716's recorded power at 50 % of the edge (0.61) is the relevant line, not 100 %.**
  - **D716 is unchanged; nothing here re-tunes it.**
- **Heating oil (closed) and the MACD arm are scale:**
  - their 2022 dependence is the size of the moves;
  - in volatility units HO's concentration halves (62 % → 30 %);
  - **the method note of §6 follows:** a year-concentration gate should be scored in volatility units as well as
    dollars.
- **D699 V1 has no edge per unit of risk outside 2022.** Its option list (vault pre-registration, a filter, or stop)
  should be weighed on the ex-2022 figure (+$3.55 net, Sharpe 0.25).
- **The book:**
  - The components' full-sample correlations (COMPONENTS_PROP) are honest day to day. They are lower in 2022 than
    elsewhere.
  - **The book's year dependence is not diversified by adding these lines.** A book built from them is a bet that a
    2022-like stretch recurs.

## 8. Disclosures

- **The seal breach of §0.1** (one vault-dated row of three microstructure fixtures, displayed by an inventory reader).
- **The real figures seen before the runs** (D722-A2): two whole-window variances, L1's war-window net and one 2018 u.
  None enters a reading.
- **Part C's random-trade null is anti-conservative for contiguous windows.** The exact rotation null is beside it, and
  I read both.
- **HO's and K2's 2022 nets have t below 2 or near it** (flagged `denominator_unstable`), so their shares are noisy.
- **The encoding fix.** After the runs, `scripts/diag_d722_lines.py` took `encoding="utf-8"` at its two text-IO calls
  (the repo's ceiling test). The rebuilt table is bit-identical: sha256 `55a65a9d…`.
