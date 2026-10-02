# D769 STAGE 0 RESULT — NO DIRECTION on the AUD and copper: the PBOC's hidden lean is visible and is news, since a stronger-yuan fix surprise lifts the AUD within 15 minutes (ρ −0.083, p 0.001), but it is priced there; from the fix to 03:00 ET nothing follows (ρ +0.022, p 0.38), and the expected-sign trade loses $5.65 net per M6A

*2026-10-02. Prop book.*
- *Pre-registration: [D769](D769-STAGE-0-PRE-REG-the-yuan-fix-residual-and-the-aud.md) (`d6dc1d2a`), with
  Amendment 1 (the G2 position sign) committed with the runner.*
- *Runner: `scripts/stage0_d769_yuan_fix_residual.py` (`08023250`; fixes `ebfda6a0` and `64ddc679`).*
- *Output: `data/stage0_d769_yuan_fix_residual.json`. Extraction 3.0 minutes; run 2.5 seconds.*

**Two launches stopped before any result.** Nothing was printed or written either time.

| launch | what stopped it | the fix |
|---|---|---|
| first | the delivery guard raised. On 32 Thursdays the 6A volume front is still the expiring contract, two business days before its last trading day. The pre-registration makes such days ineligible, but the runner asserted they could not occur | exclude them (27 remained after the other eligibility filters) and keep the guard on every kept day (`ebfda6a0`) |
| second | a missing scipy. The reported rank correlations called pandas' Spearman, which needs scipy, absent on the system Python (the D763 lesson) | a local Spearman, self-tested equal to the rotation's ρ (`64ddc679`) |

Both fixes were committed and are disclosed here, before the one complete run.

**The checks:**
- **the lag audit:** a normal-equations second implementation re-derived the walk-forward residual on 30 days; it raises when day t enters its own window;
- **the units:** median 6A 0.722, HG 2.95;
- **delivery:** the nearest kept front was 3 business days from its last day;
- **the rotation's offset 0** reproduced ρ;
- **the seal:** nothing on or after 2024-01-01 was read;
- **the extraction:** chunk == whole.

**The sessions:**
- 2,091 fixes; 2,015 with all inputs.
- After the 250-day model burn-in and the 20-day surprise window, the cells run **2016-08-10 → 2023-12-29**: 1,718 AUD days and 1,742 copper days.
- The August 2015 devaluation sits in the burn-in.

## 1. The model: the hidden lean is real and visible

| | |
|---|---|
| walk-forward out-of-sample R² of log(fix / noon rate) on the basket moves | **0.21** |
| AR(1) of the residual | **0.80**: the lean is a persistent stance |
| mean residual by year (bp; negative = a stronger yuan than the model) | 2016 +10 · 2017 −3 · 2018 +2 · 2019 −10 · 2020 +11 · 2021 +1 · 2022 −14 · **2023 −30** |
| residual sd by year (bp) | 2016 19 · 2017 13 · 2018 17 · 2019 27 · 2020 18 · 2021 11 · 2022 39 · **2023 60** |

**The residual recovers the known history:**
- the weak-side fixes of 2016 and of the 2020 rally;
- the defence near 7 in 2019;
- **2023's record strong bias,** the most negative year by a factor of two. P3 held.

Its size doubled in 2022–23, when Beijing leaned hardest.

## 2. The reading

The signal is the surprise s, the residual minus its 20-day mean. The window is the fix + 1 minute → 03:00 ET.

| | AUD (M6A) | copper (MHG) |
|---|---|---|
| **G1: Spearman ρ(s, y)** | **+0.022** | **+0.002** |
| the exact rotation p2.5 / p50 / p97.5 | −0.046 / −0.000 / +0.047 | −0.046 / 0.000 / +0.043 |
| two-sided p (Holm) | 0.375 (no) | 0.925 (no) |
| G2: the top third of \|s\|, expected sign (long on a strong-yuan surprise): gross, NW t | **−$1.65**, −1.99 (557 trades) | +$1.64, 0.65 (570) |
| G3: years net positive | 0 of 7 | 3 of 7 |
| **reading** | **NO DIRECTION** | **NO DIRECTION** |

## 3. It is news, priced in minutes

The immediate reaction is the move from the minute before the fix to 15 minutes after it.

| | AUD | copper |
|---|---|---|
| ρ(s, y_imm), all days; rotation p | **−0.083; p 0.001** | **−0.050; p 0.039** |
| the same on top-third days | −0.111 | −0.107 |
| the rest of the day (entry → 15:00 ET), ρ | +0.032 | +0.023 |
| the stance level r instead of the surprise, ρ(r, y) | +0.044 | +0.009 |
| excluding August 2015 | +0.022 (no August 2015 in the sample) | +0.002 |

- **The sign is the one predicted.** A fix stronger than the market model lifts the AUD and copper at once. P1 held.
- **After the first 15 minutes the sign is, if anything, slightly reversed** (+0.02 to +0.03), and not significantly.
  The expected-sign AUD trade therefore grosses −$1.65.
- **The move a micro would chase has already happened.** The window this design needed (after the fix, before London)
  carries nothing.

**By regime:** ρ(s, y) never leaves ±0.11 on either cell. The trade loses in every AUD regime.

| regime (days) | AUD ρ | copper ρ |
|---|---|---|
| CCF on, 2017-05 → 2018-01 (147–150) | −0.018 | −0.111 |
| CCF off, 2018-01 → 07 (130–132) | +0.055 | +0.087 |
| CCF on, 2018-08 → 2020-10 (516–524) | −0.008 | +0.007 |
| CCF off, 2020-10 → 2022 (508–516) | +0.081 | +0.005 |
| 2023 (233–234) | −0.035 | −0.026 |

## 4. The trade (one micro, the top third of |s|, expected sign; four groups)

| | AUD (M6A, $4.00) | copper (MHG, $4.25) |
|---|---|---|
| trades | 557 of 1,718 days, about 6 h each | 570 of 1,742 |
| gross mean (median) | −$1.65 (−$0.50) | +$1.64 (+$2.50) |
| **net mean (median)** | **−$5.65** (−$4.50) | **−$2.61** (−$1.75) |
| net at the alternative cost ($4.41) / one extra tick | −$6.06 / −$6.65 | — / −$3.86 |
| win; payoff | 40%; 0.73 | 48%; 0.96 |
| skew / kurtosis | −0.41 / 1.07 | 0.21 / 3.28 |
| net trims: ex-top 1% / ex-bottom 1% / both | −6.14 / −5.01 / −5.50 | −4.65 / −0.69 / −2.73 |
| daily net Sharpe (Sortino); gross | −2.32 (−2.69); −0.69 (−0.89) | −0.39 (−0.55); +0.25 (+0.36) |
| max drawdown; break-even cost | $3,229; none | $2,551; $1.64 |
| best and worst trades | 2023-11-07 +$55; 2020-03-19 / 03-25 −$85 | 2020-03-18 +$311; 2021-10-21 −$265 |
| \|y\| on top-third days against the others | $16.37 against $16.07 | $42.94 against $40.92 |
| ρ with D737 / F2 / C1 | −0.04 / −0.04 / +0.02 | −0.03 / −0.05 / +0.02 |

**The component line:** net Sharpe −2.32 and −0.39. Neither is a component.

## 5. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | the residual is news; ρ(s, y_imm) on the AUD negative with p < 0.05 (P 0.65) | **held:** −0.083, p 0.001 (copper −0.050, p 0.039) |
| P2 | NO DIRECTION on both cells (P 0.6) | **held** |
| P3 | 2023 has the most negative mean residual (P 0.8) | **held:** −30 bp, against −14 bp in 2022 |
| | P(PREMISE HOLDS) ≈ 0.06 / 0.04 | NO DIRECTION / NO DIRECTION |

## 6. What it shows

**The hidden action is detectable from public prices.**
- A plain walk-forward model separates the PBOC's lean from the market. It recovers 2019's defence of 7 and 2023's
  record strong bias.
- The market reads the lean: the AUD and copper move with it inside 15 minutes.

**It is priced as fast as an announcement.** D768 (China's grain purchases) and D769 (Beijing's yuan lean) have the
same shape.
- The demand economy's action, public or inferred, is real and is news.
- The first print after it carries the information.
- The hours after carry nothing tradable at micro cost.

**On the line:** for these actors, the trace becomes visible at the same moment it is priced. An edge would need a
trace the market cannot see when it appears. These two constructions found none.

**What follows:**
- No trading pre-registration in-sample.
- **The principal's call:** close the yuan-fix construction, and decide whether the demand-economy line continues.

## 7. CLOSED (2026-10-02)

**The principal: "Close that".**
- The yuan-fix residual construction is closed for the prop book.
- The fixtures `cny_central_parity.csv` and `fred_dexchus.csv` remain available.
