# D757 STAGE 0 PRE-REGISTRATION — a reverting-day detector: strong long gamma AND a 10:30 impulse beyond realised volatility, on the index micros

*2026-10-02. Prop book.*
- *The principal asked "How about a better reverting day detector?" and proposed "Long-Gamma Days OR'd with large
  Impulse moves outside of predicted Vol".*
- *Shown that GEX > 0 holds on 88 % of days (1,708 of 1,941 on ES) at the 33 % base rate, so an OR would flag
  nearly every day, the principal chose **"AND, strong gamma"** and **"Prior-20 realised"** as the predicted
  volatility.*
- *Numbered D757, claimed with the documentation-review session.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29). **Development, not admission:** a
  pass here is confirmed only on the held 2024-01 → 2025-02 slice, on the principal's word.*

## 0. The idea, and what is already read

**The idea.** Dealers who are heavily long gamma sell rallies and buy dips. An early move that overshoots what
volatility predicts, on such a day, should come back, so the day closes as a reverting day.

**Read before this record:**

| source | finding |
|---|---|
| D756 | the GEX sign alone has no lift (GEX > 0: RD rate 0.336, Holm 0.65); the gap is the only declared pass (0.364); day types alternate; the 10:00 fade's prize and p\* 0.435 |
| D688 | the long-gamma half of ES's intraday gamma split is zero over 5–60 minutes |
| D727 | NQ continues from the open at every clock; YM reverses in the morning |
| D487, D697 | ES's early moves and bursts fade |
| D746 | the stretch fade (\|z\| ≥ 2.5, to the VWAP) has no room |

**What is new:** the AND of a *strong* long-gamma state with a time-scaled impulse, scored on D756's
reverting-day label, with a precision bar tied to the trade's own break-even.

**What this record does not read.** It reads neither the gap nor the previous day's type (efficiency). D756's
POST HOC lead (a small gap after a trending day) is left untouched for its own record.

**NQ.** D727 found continuation on NQ, so the decision is pooled over **ES, YM and RTY**, declared now. NQ is
reported beside them and is not in the rule.

## 1. Data and definitions

- **Panels, label and costs are D756's**, through `scripts/stage0_d756_reverting_days.py`'s functions, read-only:
  - D727's RTH panels, 2016-02 → 2023-12 (RTY from 2017-08);
  - RD = E = |C − O| / (H − L) in the bottom third of its root-year;
  - the micro default-line costs.
- **Strong long gamma (G):** GEX at the previous session's close (`DIX.csv`), in the **top tercile** of the previous
  250 sessions' GEX values, strictly before t.
- **The impulse (I):** **\|z₁₀:₃₀\| ≥ 1.5**. z is D727's time-scaled move: (P₁₀:₃₀ − O) / σ_oc ÷ √(60/390), with
  P₁₀:₃₀ the 10:29 bar's close (D727's clock index 1) and σ_oc the prior-20 RMS of open → close.
- **The detector: D = G AND I.**

## 2. The trade's break-even

**The trade:** the fade at **10:30**, side −sign(P₁₀:₃₀ − O), exit at 15:59's close, one micro, net of its cost.

**The prize is measured on the trade's own population, the impulse days (I),** over ES, YM and RTY:
- μ_RD and μ_non: mean net on impulse days that are and are not reverting days;
- **Z₁₀:₃₀:** μ_RD > 0 at t ≥ 2, and the mean |net| on impulse RD days ≥ 3× cost;
- **p\*:** −μ_non / (μ_RD − μ_non), when μ_RD > 0 > μ_non.

## 3. The tests (decision pooled over ES, YM, RTY)

| | criterion |
|---|---|
| **T1, gamma adds to the impulse** | precision P(RD \| G ∧ I) − P(RD \| ¬G ∧ I) > 0, against the **exact circular rotation of the G series** against the label (the impulse and the label stay on their days; a shared offset across the three roots, each by k mod its length). **One-sided, p ≤ 0.05** |
| **T2, worth it** | **P(RD \| G ∧ I) ≥ p\*** |
| **T3, enough days** | at least **150** detector days pooled |

**The reading:**
- **NO PRIZE:** Z₁₀:₃₀ fails.
- **DETECTOR WORTH IT:** T1, T2 and T3 all hold. Development only: a trading record on the held slice may follow,
  on the principal's word.
- **RECOGNISABLE, NOT WORTH IT:** T1 holds, T2 or T3 fails.
- **NOT A DETECTOR:** T1 fails.

**Reported, not in the rule:**
- per root, NQ included: n and RD precision for D, for I alone, for G alone, and for the ¬G ∧ I and G ∧ ¬I cells;
- the share of days in each cell;
- the rotation's p50 and p95.

The fade's net per detector cell is **not** reported: that is the trading test, for a later record.

## 4. Assertions (each canary must raise in the self-test)

1. **The known answer:** D756's label and prize reproduced. The RD count is 2,440 and the 10:00 fade's RD mean is
   +\$34.19, both against `data/stage0_d756_reverting_days.json`.
2. **Lag:**
   - z₁₀:₃₀ uses bars through 10:29 only;
   - GEX uses the last date strictly before t, and its tercile thresholds the previous 250 values;
   - a canary using day t's own GEX must differ on some session.
3. **Sign in money:** a short fade after a rise pays positively when the close is below P₁₀:₃₀.
4. **The rotation:**
   - offset 0 equals the observed;
   - a planted G equal to the label on impulse days gives p < 0.01;
   - the vector form equals a loop on 50 offsets.
5. **The seal:** nothing on or after 2024-01-01 is read.

## 5. Predictions (Opus)

- **P1:** Z₁₀:₃₀ holds (P 0.75). The 10:30 fade on known reverting impulse days pays.
- **P2:** impulse days alone revert *less* than the base rate on ES/YM/RTY pooled (P 0.5). D727's continuation is
  NQ's, but a large early move is usually a trend-day start.
- **P3:** T1 fails (P 0.7). D688 found the long-gamma half zero, and D756's GEX sign had no lift.
- **P(DETECTOR WORTH IT) ≈ 0.05.**
