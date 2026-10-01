# D727 STAGE 0 PRE-REG — the trend detection curve: from what clock does NQ's drift since the open predict the rest of the day, how much of the move is left, and does joining then pay one MNQ?

*2026-10-01. The principal: "Trend detection my old foe, how shall we conquer thy?", then "Ok pre-reg build and run
please".*
- **This is step 1 of the plan given in reply.** Stop forecasting trend days before the open; that failed in D720,
  D724 and D725, because a size forecast finds volatility, not trend. Instead, measure how fast a trend is
  recognisable once it is under way, and what is left of it.
- **The order (R8):** this record is committed before the runner exists, and the runner before its one run. The
  result is a separate record.
- **What it is:** a premise map, oracle first. It chooses no rule.

## 0. What the record already fixes (and this design obeys)

- **Drift, not path efficiency.** Path efficiency rewards only monotone paths, and real trends retrace about half
  (D471, D523). Every statistic here is a displacement scaled by volatility.
- **A null that sees a day-long drift.** A within-day permutation is blind to it (D487). The null here pairs one
  day's morning with ANOTHER day's afternoon.
- **The bounce is negligible on NQ at one minute** (lag-1 −0.030 trade against −0.029 mid; D526). Trade prices are
  used.
- **Transfer before belief** (D474/D475: the sign flipped on unseen roots). YM and RTY have never been examined for
  this question, and they are the declared transfer check, in the same run.

## 1. Data, seal, conventions

- **Data:** the day sessions of NQ (primary), YM and RTY, 2016-01-04 → 2023-12-29, from `fut_{root}_rth_1m`. Days
  need ≥ 380 bars; roll days are excluded.
- **The seal:** nothing dated 2024-01-01 or later is read. NQ's 2024+ last hour is D716's joint-vault look.
- **Prices:** the price at t is the close of the bar starting t−1, as-of. The open O is the 09:30 bar's open. The
  close is the 15:59 bar's close.
- **The scale:** σ_oc is the root mean square of the open-to-close move over the prior 20 sessions, in points
  (prior days only).
- **The clocks:** t ∈ {10:00, 10:30, …, 15:00}, eleven of them. The elapsed share of the session is u = (t −
  09:30)/390 minutes.
- **The objects, per day and clock:**
  - the drift so far, z_t = (P_t − O)/(σ_oc·√u);
  - the move so far, x_t = (P_t − O)/σ_oc;
  - the rest of the day, y_t = (C − P_t)/σ_oc.
- **The money:** one micro at D711's cost line for the root (MNQ $4.07; MYM and M2K from the same table).

## 2. What is measured, per root and clock

**S1, the curve (primary):**
- **The statistic:** β_t, the OLS slope of y_t on x_t with an intercept (the intercept absorbs the clock's own drift),
  one observation per day, with a Newey–West t (5 lags).
  - β_t > 0: the move since the open continues into the rest of the day.
  - β_t < 0: it reverses.
- **The null:** the enumerated rotation of y_t across days against x_t (offsets 20 … n − 20; the SE of the p95 is 0).
  It breaks the same-day link between the morning and the afternoon, which is the trend day itself, and keeps both
  distributions.
- **Reported beside:**
  - the continuation probability P(sign y_t = sign x_t) by |z_t| bin (< 0.5, 0.5–1, 1–1.5, ≥ 1.5);
  - the mean of sign(x_t)·y_t in each bin.

**S2, what is left, against the oracle:**
- **Trend days** (the oracle label, unknowable in advance) are the top third of |C − O|/σ_oc within each year.
- **The share of the move remaining:** for trend days, E[sign(C − O)·(C − P_t)] / E[|C − O|] at each clock. It answers
  how late a fully certain entry would be.
- **Detection:** for |z_t| ≥ k (k ∈ {0.5, 1.0, 1.5}), the precision P(trend day and sign z_t = sign(C − O)) against
  its base rate. The recall is the share of trend days caught by t.

**S3, the money (reported; nothing chosen):**
- **Per clock and k:** if |z_t| ≥ k, one micro in sign(z_t) at P_t, held to the 15:59 close.
- **The practical book, per k:** the first clock at which |z_t| ≥ k, one trade a day.
- **Reported for each:**
  - trades, mean and median gross, net per micro;
  - net and gross Sharpe and Sortino (daily, all sessions, √252), with max drawdown;
  - win rate, skew, kurtosis, the symmetric 1% trims;
  - profitable years, and the largest year's share.
- **The ceiling:** the same entries restricted to the oracle's trend days with the right sign, which is the most any
  detector could add.

## 3. Readings (declared now)

**Per clock, on NQ:**
- **CONTINUATION:** β_t is above its rotation's p95 and the NW t is ≥ 2.
- **REVERSAL:** β_t is below its rotation's p05 and the NW t is ≤ −2.
- **NONE** otherwise.

**The NQ curve:**
- **RECOGNISABLE FROM t\*:** t\* is the earliest clock that starts a run of at least two consecutive CONTINUATION
  clocks. A single isolated clock is not a run, which guards the eleven-clock multiplicity.
- **NOT RECOGNISABLE:** no such run exists.

**Transfer (YM, RTY), for NQ's CONTINUATION clocks:**
- **TRANSFERS:** on at least one of YM and RTY, β_t has the same sign and ranks ≥ 0.90 in its own rotation at a
  majority of those clocks.
- **DOES NOT TRANSFER** otherwise.
- If NQ has no CONTINUATION clock, transfer is reported per clock only.

**The go/no-go for step 2 (cross-asset agreement) and a rule design with the principal:**
- **GO** iff NQ is RECOGNISABLE, the curve TRANSFERS, and NQ's practical book at some k grosses ≥ 2 × $4.07 a trade
  with net > 0.
- **Otherwise** the map is written up. Whether step 2 still runs is the principal's call: cross-asset agreement may
  supply what the own-price curve lacks.

## 4. Runner assertions

- **Lag:**
  - P_t, O and σ_oc are re-derived at sampled (day, clock) by a second implementation reading only bars starting
    before t, and prior sessions for σ_oc;
  - a canary reading the t bar must fire;
  - no index may wrap (D724's 10:00 lesson), and the self-test shows the audit catching a wrap.
- **Sign, in money:** a long when z_t > 0 that rises to the close pays +$2 a point on MNQ, and a short when z_t < 0
  that falls pays the same.
- **Right quantity:**
  - y_t runs from P_t to the close, not from the open;
  - x_t and y_t sum to (C − O)/σ_oc, which is asserted;
  - the rotation's offset 0 equals the observed β_t.
- **The self-test (synthetic):**
  - a series with a day-level drift reads CONTINUATION and beats its rotation;
  - a pure random walk does not;
  - a within-day permutation null would miss the drift, which is shown, to document why it is not used.
