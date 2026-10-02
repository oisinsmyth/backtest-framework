# D756 STAGE 0 PRE-REGISTRATION — mean-reverting days on the index micros: the prize if they were known, then whether anything known before the open can find them

*2026-10-02.*
- *The principal asked "Can we find mean reverting days?", chose "Yes, index micros" when offered an oracle-first
  study, and specified "Not for the personal book for the prop book".*
- *Numbered D756, claimed with the documentation-review session (D755 is theirs).*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29).*

## 0. Scope, and what this reopens

**The prop book's intraday mandate:** one micro per root, every position opened and closed inside the session, out
by 15:59, before the 16:10 flat.

**A classification study, not a trading test.** It asks two questions:
1. On days *known after the fact* to have reverted, what would a simple intraday fade have earned? This is the
   prize.
2. Does any variable known before the open find those days better than chance, and by enough to pay?

**Any trading rule needs its own record,** and only if §4 reads PREDICTABLE AND WORTH IT.

**It reopens the closure of intraday mean reversion on the index micros** (D746, D747, D752) **for classification
only,** on the principal's word.

**What is already read, and shapes the predictor list:**

| prior | finding |
|---|---|
| D727 | trend-day precision at 10:00 is 0.37 against a base of 0.33 |
| D720, D722, D745 | no pre-trade regime sorts the books |
| D691, D665 | implied/realised volatility and gamma predict a day's *size* |
| D683–D688 | the long-gamma intraday fade is real but tiny |
| D528 | reversion probability is forecastable (vol_ratio), but 4–8× below cost |
| D724 | NQ respects no intraday mean |

**The label (E) and the oracle's prize are new.** Each predictor is a plain split, declared now, and none is fitted.

## 1. Data

**Bars.** D727's panels: `scripts/stage0_d727_trend_curve.py`'s `load_root` and `objects` over
`fut_{ES,NQ,YM,RTY}_rth_1m`.
- Front month; roll days dropped.
- σ_oc is the prior-20 RMS of open → close.
- 2016-02 → 2023-12; RTY from 2017-08.
- The day's high and low come from the 1-minute file.

**Overnight range.** `fut_breadth_hourly`, the session's hourly bars from 18:00 the evening before through 08:59
ET (segments h18 … h08), on the same front contract.

**Event flags** (`cme_session_calendar`): `fomc`, `cpi`, `empsit` on the session.

**Dealer gamma.** `data/raw/squeezemetrics/DIX.csv` (`gex`): the value dated at the **previous session's close**,
read as positive or negative. The ES book is set at the prior close (the GEX timing memory). It is one market-wide
state, applied to all four roots.

**Cost per round trip:** the micro's `default_line` in `data/futures_costs.json` (D748-A1's rule): MES \$4.418,
MNQ \$4.067, MYM \$3.797, M2K \$3.757.

## 2. The label and the prize

**The label: a reverting day (RD).** E = |C − O| / (H − L) over 09:30–15:59 (the day's efficiency).
- RD = E in the **bottom third of that root's sessions in the same calendar year**.
- The base rate is therefore 1/3 by construction.

**The oracle fade, declared now:**
- at 10:00, **side = −sign(P₁₀ − O)** (fade the move since the open), with P₁₀ D727's 10:00 price;
- exit at 15:59's close;
- one micro at its cost line;
- no stop. The prize is measured unconstrained, and a trading record would add risk rules.

**What is computed:**
- μ_RD and μ_non: the mean net of the fade on RD days and on other days, with t, median and win rate.
- **p\***, the break-even precision: −μ_non / (μ_RD − μ_non), when μ_RD > 0 > μ_non. A classifier must select RD
  days with at least this precision for the fade to break even on the days it selects.

**The prize bar (Z).** μ_RD > 0 at t ≥ 2, **and** the mean |net| on RD days is at least 3× the round-trip cost. If
Z fails, the reading is **NO PRIZE**; the predictors are still reported.

## 3. The predictors (seven, each declared with its expected direction)

Continuous predictors are split into **terciles by walk-forward thresholds** (that root's previous 250 sessions,
strictly before t). Binary predictors are their own two groups.

| | predictor (known before 09:30) | the cell expected to hold more RD days |
|---|---|---|
| **P-a** | overnight range ÷ the prior-20 mean RTH range | the bottom tercile (a quiet night) |
| **P-b** | \|open − previous close\| ÷ σ_oc (the gap) | the bottom tercile |
| **P-c** | the previous session's E | the bottom tercile (reversion persists) |
| **P-d** | the previous session's range ÷ the prior-20 mean range | the top tercile (after a big day) |
| **P-e** | σ_oc's walk-forward percentile (the volatility level) | the bottom tercile |
| **P-f** | event day (FOMC, CPI or employment) | not an event day |
| **P-g** | GEX at the previous close > 0 (dealers long gamma) | GEX > 0 |

**The statistic per predictor: the lift.** Lift = P(RD | the expected cell) − P(RD | the opposite cell). For a
tercile predictor the opposite cell is the other extreme tercile; for a binary, the other group.

**The test:**
- Pooled over the four roots: counts summed across roots, each root's own label and thresholds.
- **The null is the exact circular rotation of the predictor series against the label,** a shared offset k across
  roots, each root shifted by k mod its own length, every offset enumerated.
- **The test is two-sided:** p = the share of offsets with |lift| ≥ the observed. Wrong-signed lifts are reported
  as such.
- **Holm over the seven.**

**Root-aware:** every lift is also reported per root.

## 4. The reading

**NO PRIZE:** Z fails.

**Otherwise, for each predictor with a Holm-adjusted p ≤ 0.05 and its lift in the declared direction:**
- **PREDICTABLE AND WORTH IT:** precision in the expected cell ≥ p\*. A trading record may follow, under its own
  pre-registration, read on the held 2024-01 → 2025-02 slice only on the principal's word.
- **RECOGNISABLE, NOT WORTH IT:** precision below p\*.

**NOT PREDICTABLE:** no predictor passes.

**Reported for every predictor and root:** precision per cell, the lift, the null's p50 and p95, and the share of
sessions in each cell. The fade's net per predictor cell is **not** reported: that would be the trading test,
which belongs to a later record.

## 5. Assertions (each canary must raise in the self-test)

1. **The known answer:** D727's panel session counts reproduced (NQ 1,941; YM 1,938; RTY 1,557) from
   `data/stage0_d727_trend_curve.json`.
2. **Lag:**
   - every predictor at t uses only data through the previous close, or the overnight bars through 08:59;
   - a second implementation from raw sessions agrees on 40 sampled (root, t);
   - a canary using day t's own RTH range must disagree.
3. **The label:** within each root-year the RD share is 1/3 (to rounding), and E lies in [0, 1].
4. **Sign in money:** a short fade after a rise pays positively when the close is below P₁₀.
5. **The rotation:**
   - offset 0 equals the observed;
   - a planted predictor equal to the label gives p < 0.01;
   - the vector form equals a loop on 50 offsets.
6. **The seal:** nothing on or after 2024-01-01 is read from any futures fixture or from DIX.

## 6. Predictions (Opus)

- **P1:** Z holds (P ≈ 0.8). Foresight of a low-efficiency day makes a 10:00 fade pay on those days.
- **P2:** p\* is above 0.5. Fades lose more on trending days than they win on reverting ones, so a classifier needs
  high precision.
- **P3:** **NOT PREDICTABLE** or **RECOGNISABLE, NOT WORTH IT** (P ≈ 0.9). The repo has never predicted a day's
  shape before the open. If anything passes, it is a size variable (P-e, P-d, P-g), and in the size direction:
  quiet days revert more.
- **P(PREDICTABLE AND WORTH IT) ≈ 0.05.**
