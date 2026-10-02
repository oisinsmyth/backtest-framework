# D769 STAGE 0 PRE-REGISTRATION — a hidden hand with a public trace: when the PBOC's 09:15 yuan fix comes in stronger or weaker than a market model predicts, do the Australian dollar and copper keep moving that way through the Asian session? (M6A and MHG at one micro; prop book)

*2026-10-02. Prop book.*
- *The principal:*
  - *"Lets continue on this demand economy line … take advantage of the perverse incentives that demand economies
    have";*
  - *then "There are too few events there, how about traces of no-public actions?";*
  - *they chose "Yuan fix residual" and approved both downloads.*
- *Numbered D769, claimed with the documentation-review session.*
- *That session notes the principal declined "the yuan fix + copper" when it was proposed in an earlier session. The
  principal has now chosen it.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29). No CME price has been read for this
  study.*

## 0. The mechanism and what is on file

**The hidden action.** Every CFETS business day at **09:15 Beijing**, the PBOC sets the USD/CNY central parity, the
"fix".
- The published method is the previous close plus a move that keeps the CFETS currency basket stable. From May 2017
  to October 2020 it also included an undisclosed "counter-cyclical factor".
- In practice the fix departs from what that rule implies whenever Beijing wants to lean.
  - It was set **stronger** than the market to resist depreciation: 2018–19, and all of 2023, when fixes ran up to
    about 1,300 pips stronger than the market.
  - It was set **weaker** to let the currency go: August 2015.
- **The lean itself is never announced. The fix is.** The gap between the fix and a model built from public prices is
  the trace of a non-public decision.

**Why the AUD and copper.** These are China's two most sensitive CME micros.
- D765/D767: they co-move at the China open (ρ 0.30–0.35).
- A stronger-than-model fix signals Beijing defending the yuan and, read as risk appetite, Chinese demand. A weaker one
  signals tolerance of outflows.

**The clock fits the prop book.** 09:15 Beijing is **20:15 ET in winter (EST) and 21:15 ET in summer (EDT)**. CME FX
and copper trade then. A position opened after the fix and closed in the same CME trade date is intraday by the
book's rule.

**On file:**
- **New fixtures,** built by `scripts/build_cny_fix.py` from `scripts/fetch_cny_fix.py`. That download was approved,
  used an honest client, and was not retried after CFETS refused it.
  - **`data/fixtures/cny_central_parity.csv`:** SAFE's daily central-parity table, the same CFETS series. 2,091 fixes,
    2015-06-01 → 2023-12-29.
    - **The checks:** 2015-06-01 = 6.1207 agrees with CFETS. The 2015-08-11 devaluation (6.2298), the first fix
      above 7 on 2019-08-08, and the 2023 strong bias (7.2150 against 7.343 on 2023-09-08) are all present.
  - **`data/fixtures/fred_dexchus.csv`:** the Federal Reserve's noon New York USD/CNY rate (H.10), 2,144 days. It is
    the free official market rate. The CFETS 16:30 onshore close, the textbook input, is not free; this record
    accepts the noon rate instead.
- **CME minute bars, all hours:** 6A, 6E, 6J, 6B, 6C, 6S and HG, from the raw GLBX archive.
- **Nothing on file tests the fix.** D765's "the 09:16 re-based x" found the fix moment is not what drives the China
  open on metals. That tested the fix's *timing*, not its *surprise*.

**The mechanism's history.** Splits are reported (§3) by:
- the 2015-08-11 reform;
- the 2016 close-plus-basket rule;
- the counter-cyclical factor: on 2017-05-26, off 2018-01-09, on from early August 2018, off 2020-10-26;
- onshore hours: 23:30 Beijing from 2016-01-04, 03:00 Beijing from 2023-01-03;
- the yearly basket reweights.

## 1. Data and quantities (fixed now)

**For each fix day t** (a SAFE fix date; Beijing calendar):
- **The fix minute F_t:** 09:15 Beijing, as a UTC minute. Its CME trade date is t.
- **The market rate M_t:** the most recent FRED noon-New-York USD/CNY strictly before F_t, at noon ET of that US
  date. Ineligible if more than 4 calendar days old.
- **The basket move:** for i ∈ {6E, 6J, 6B, 6A, 6C, 6S}, b_i,t = log P_i(F_t − 1 min) − log P_i(noon ET of M_t's date).
  - P is the close of the last front-month bar starting before that time.
  - Each P must be at most 30 minutes stale and on one contract; otherwise the day is ineligible.
- **The model:** Δ_t = log(fix_t) − log(M_t) is regressed on (1, b_6E, b_6J, b_6B, b_6A, b_6C, b_6S) over the
  **previous 250 eligible fix days only**, by ordinary least squares.
  - The **residual** r_t = Δ_t − the prediction from those coefficients. It is walk-forward and out of sample.
  - Days before the 250th eligible fix are burn-in.
- **The signal:** s_t = r_t − the mean of the previous 20 eligible residuals. This is the **surprise** relative to the
  recent stance, since the stance itself is persistent (2023).
  - **Negative s_t:** a stronger yuan than the model and recent practice imply.
  - The level r_t is reported (§3).

**Outcomes (per cell: AUD = 6A, scored at M6A; copper = HG, scored at MHG):**
- **The entry** E_t = the open of the first bar starting in [F_t + 1, F_t + 5] minutes.
- **Primary, y_t:** the close of the last bar starting before **03:00 ET** of trade date t, minus E_t. That ends the
  Asian session, before London.
  - $ per micro: 10,000 × Δ for M6A; 2,500 × Δ for MHG.
  - Ineligible if staler than 10 minutes or on two contracts.
- **Reported:**
  - y_imm = P(F_t + 15) − P(F_t − 1), the immediate reaction ("is the residual news?");
  - y_day = P(15:00 ET) − E_t, the rest of the trade date.

**Eligible days:** fix days 2015-06-01 → 2023-12-29 with r_t, s_t, E_t and y_t valid, after the burn-in. About 1,750.

**Costs:**
- **M6A:** $3.00 commission + one $1.00 tick = **$4.00** a round trip. Also reported at the full-size 6A's measured
  spread of 1.41 ticks (**$4.41**).
- **MHG:** $3.00 + one $1.25 tick = **$4.25**.

## 2. The gates (each cell: AUD and copper)

| gate | what | passes when |
|---|---|---|
| **G1 direction** | Spearman ρ(s_t, y_t) | two-sided p < 0.05 against the **exact enumerated rotation** of s against y (offsets 1 … n−1), **Holm over the two cells** |
| **G2 prize** | the trade: on days in the walk-forward **top third of \|s\|** (the threshold from the previous 250 eligible days), position = −sign(ρ) × sign(s_t), entered at E_t and exited at the 03:00 ET price | mean gross ≥ the cell's cost with a Newey-West(5) t ≥ 2 |
| **G3 not one era** | the trade's net | positive in at least 5 of the 9 calendar years (2015 is partial), and positive without its best year |

**The readings, per cell:** NO DIRECTION (G1 fails), DIRECTION, NO PRIZE, EPISODIC, PREMISE HOLDS.

**The expected sign** (not gated): ρ < 0. A stronger-yuan surprise is followed by a firmer AUD and copper.

**What follows a PREMISE HOLDS:** a trading pre-registration read on the held slice and forward, on the principal's
word.

## 3. Reported, never gating

1. **Is the residual news?** ρ(s_t, y_imm) on each cell, and on the trade's top third, with the same rotation. If the
   AUD does not react within 15 minutes, the market does not read the fix as information.
2. **The model's quality:**
   - the walk-forward R² of Δ_t;
   - the residual's standard deviation by year;
   - the AR(1) of r_t;
   - the mean r_t by year (2023 should be the most negative).
3. **The stance:** ρ(r_t, y_t), using the level instead of the surprise.
4. **By regime:**
   - 2015-06 → 2016-12;
   - 2017-01-01 → 2017-05-25;
   - CCF on 2017-05-26 → 2018-01-08;
   - CCF off 2018-01-09 → 2018-07-31;
   - CCF on 2018-08-01 → 2020-10-26;
   - CCF off 2020-10-27 → 2022-12-31;
   - 2023.
5. **Excluding August 2015,** the devaluation.
6. **The rest of the day:** ρ(s_t, y_day).
7. **Size:** mean \|y_t\| on top-third days against the others.
8. **The four groups** of each cell's trade, with the top trades named.
9. **The component line:** net Sharpe and Sortino, hit rate, skew, gross beside net, and ρ of the daily net with D737,
   F2 and C1.

## 4. Size and power (stated now)

- **G1:** about 1,750 days, so a two-sided 5% test detects \|ρ\| ≳ 0.05. That is a weak bar for "something", and the
  reason G2 exists.
- **G2:**
  - about 580 top-third trades;
  - the AUD's fix → 03:00 ET move has an sd of roughly 0.3–0.4%, about $20–28 per M6A, so the SE of the mean is
    about $1.0;
  - **the $4.00 bar needs a mean of about 4 SE,** a strong predictable component in a 6-hour FX move. P(PREMISE
    HOLDS) is low.

## 5. The runner's assertions (each proved to raise in `--selftest`)

1. **Lag:**
   - a second implementation (a plain per-day loop calling `numpy.linalg.lstsq` on the previous 250 rows) re-derives
     r_t for 30 sampled days;
   - **the break:** including day t in its own window must raise;
   - M_t's timestamp < F_t;
   - the basket bars end before F_t;
   - E_t ≥ F_t + 1 minute.
2. **The clock:** 09:15 Beijing = 20:15 ET on 2021-01-15 (EST) and 21:15 ET on 2021-07-15 (EDT), the previous ET
   calendar day.
3. **Sign in money:** +0.0001 on M6A = +$1.00 long; +0.0005 on MHG = +$1.25 long; a short loses the same.
4. **Units:**
   - the median 6A lies in [0.55, 0.85];
   - HG in [1.8, 5.2] $/lb;
   - the fix in [6.0, 7.4];
   - the FRED rate in [6.0, 7.5].
5. **Delivery:** no FX front within 2 business days of its last trading day; no HG front on or after its first notice
   day.
6. **The seal:** a 2024-dated bar, fix or FRED row raises.
7. **The rotation's offset 0** equals the observed ρ.
8. **Chunk == whole:** the largest extraction file re-decoded serially equals its process result.
9. **Synthetic:**
   - a planted ρ passes G1;
   - noise fails it about 95% of the time;
   - an AR(1) (0.9) signal against independent returns fails it about 95% of the time.

**Speed:** the extraction is about 10 minutes (seven roots, four processes); the run is under a minute.
**Output:** `data/stage0_d769_yuan_fix_residual.json`.

## 6. Predictions (Opus)

- **P1: the residual is news.** \|ρ(s, y_imm)\| on the AUD has p < 0.05 with a negative sign (P 0.65).
- **P2: NO DIRECTION** on the primary window on both cells (P 0.6). It is priced within minutes.
- **P3: 2023 has the most negative mean residual** of any year (P 0.8). This checks the model against the known
  strong-bias regime.
- **P(PREMISE HOLDS):** about 0.06 on the AUD and 0.04 on copper.
