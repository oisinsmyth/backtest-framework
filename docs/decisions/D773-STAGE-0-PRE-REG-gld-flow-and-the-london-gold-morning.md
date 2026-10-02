# D773 STAGE 0 PRE-REGISTRATION — forced bullion flow: when yesterday's GLD holdings rose (creations) or fell (redemptions), does gold move that way through the London morning into the LBMA PM auction? (GC prices scored at one MGC; prop book)

*2026-10-02. Prop book.*
- *The principal: "Let's look at gold, what moves it intraday?". They then chose "ETF flow → PM auction (Recommended)"
  and approved the download.*
- *Numbered D773, reserved with the documentation-review session (D772 is theirs).*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29). No gold price has been read for this
  study.*

## 0. The mechanism and what is on file

**The forced flow.** SPDR Gold Trust (GLD) holds 630–1,280 t of bullion, 2015–2023.
- When investors buy more GLD than the market makers can supply, the authorised participants (APs) create shares. To do
  that they must deliver bullion to the trust, and when investors sell, they redeem and take bullion back.
- GLD is valued at the LBMA Gold Price PM, the auction at 15:00 London. So the APs' bullion purchases cluster in the
  London morning and at that auction.
- **Forced:** a creation must be backed by metal. **Sign known:** creations buy, redemptions sell. **Slow:** flows run
  in streaks.
  - The daily change in tonnes has a lag-1 autocorrelation of **+0.23** (2015-06 → 2023-12). This was measured when the
    fixture was built, from holdings only.
  - So yesterday's published flow signs part of today's forced flow before it trades.

**What is on file:**
- **D751 (the gold fix on MGC): NOTHING.**
  - Gold moves enough around the PM auction to pay (\|move\| 1.6–2.0 × the bar).
  - But its first US half-hour predicted neither the move into the fix nor a reversal after it.
  - It noted that real flow data was not on disk.
- **The D772 lead hunt** (the documentation-review session's reversion leads): the GLD/IAU **premium to NAV** as a
  stand-in for AP flow gave ρ 0.00. That lead was withdrawn.
  - **This test uses the actual metal:** the trust's tonnes, not a price premium.
- **The new fixture** `data/fixtures/gld_holdings_daily.csv`, built by `scripts/build_gld_holdings.py` from SPDR's
  official historical archive (fetched once with an honest client, on the principal's word):
  - 2,243 days, 2015-06-01 → 2023-12-29;
  - 719 rows dated 2024+ dropped unread;
  - holdings change on 59% of days; the median nonzero \|flow\| is 2.7 t and the 90th percentile 8.0 t.
- **Three rows are "AWAITED".** A date's holdings are published with a lag, so this study lags them a full business
  day.

## 1. Data and quantities (fixed now)

**For each CME trade date d** (ET date of wall time + 6 h), on weekdays 2015-06 → 2023-12:
- **The signal f_d:** the change in GLD tonnes between the two most recent holdings dates **strictly before d's ET
  calendar date**: f_d = tonnes(t₁) − tonnes(t₂), where t₁ is the latest date with a value before d and t₂ the one
  before it.
  - These holdings are published by the evening of t₁, ahead of the 03:00 ET London open.
  - Missing or "AWAITED" values make the day ineligible.
- **The London clock** (zoneinfo Europe/London):
  - L0 = 08:00 London (the London open);
  - FIX = 15:00 London (the PM auction).
- **Prices:** the GC front-month 1-minute bars, from the raw GLBX archive (all hours).
  - P(t) = the close of the last bar starting before t, ineligible if staler than 10 minutes;
  - E = the open of the first bar starting in [L0, L0 + 5 min];
  - one contract for every price of the day.
- **Outcome (primary):** y_d = (P(FIX − 1 min) − E) × $10. That is the London morning into the auction, in $ per MGC
  ($10 per $1/oz).
- **Reported outcomes:**
  - y_auc = P(FIX + 5) − P(FIX − 5), D751's leg A;
  - y_after = P(FIX + 30) − P(FIX + 5), the fade;
  - y_us = P(FIX − 1) − P(09:30 ET), the US morning into the auction.
- **The cost:** **$5.93** a round trip at one MGC, D751's line, so the two studies compare.

**Eligible days:** f_d and y_d valid. About 2,000, of which roughly 1,700 fall after the 250-day walk-forward burn-in
for the trade's tercile.

## 2. The gates (one cell)

| gate | what | passes when |
|---|---|---|
| **G1 direction** | Spearman ρ(f_d, y_d) on all eligible days | two-sided p < 0.05 against the **exact enumerated rotation** of f against y (offsets 1 … n−1) |
| **G2 prize** | the trade on days in the walk-forward **top third of \|f\|** (the threshold from the previous 250 eligible days): position = **sign(ρ) × sign(f_d)**, entered at E, exited at P(FIX − 1) | mean gross ≥ $5.93 with a Newey-West(5) t ≥ 2 |
| **G3 not one era** | the trade's net | positive in at least 5 of the 8 full years (2016–2023), and positive without its best year |

- **The readings:** NO DIRECTION (G1 fails), DIRECTION, NO PRIZE, EPISODIC, or PREMISE HOLDS.
- **The expected sign** (not gated): ρ > 0. Yesterday's creations are followed by gold rising into today's auction.
- **When G1 fails,** the reported trade uses the expected sign: long after inflows, short after outflows.
- **What follows a PREMISE HOLDS:** a trading pre-registration read on the held slice and forward, on the principal's
  word.

## 3. Reported, never gating

1. **The premise of the premise:** the lag-1 autocorrelation of the daily flow on the eligible days, and ρ(f_d, the
   flow dated d itself).
2. **A diagnostic, not tradable** (it uses same-day holdings, so it looks ahead): ρ(the flow dated d, y_d). Do creation
   days coincide with London-morning gold moves at all?
3. **The other windows:** ρ and the top-third trade's gross on y_auc, y_after and y_us.
4. **The withdrawn proxy:** ρ(the previous day's premium to NAV, y_d), for comparison with the D772 lead.
5. **The clock control** (D751's N3): in the weeks when London and New York daylight saving disagree, the y on the
   London clock against the same windows on a fixed 10:00 ET clock.
6. **By year;** inflow and outflow days separately; \|f\| quintiles.
7. **The four groups** of the trade, with the top trades named.
8. **The component line:** net Sharpe and Sortino, hit rate, skew, gross beside net, and ρ of the daily net with D737,
   F2 and C1.

## 4. Size and power (stated now)

- **G1:** about 2,000 days, so a two-sided 5% test detects \|ρ\| ≳ 0.045.
- **G2:**
  - about 570 top-third trades;
  - gold's London morning (08:00 → 15:00 London) moves with an sd of roughly 0.6–0.8%, about $10–15 per MGC at
    $1,200–2,000/oz, so the SE of the mean is about $0.5;
  - **the $5.93 bar needs a mean of about 11 SE,** a large predictable component. P(PREMISE HOLDS) is low.
- **The premise is modest.** With a flow autocorrelation of 0.23, yesterday's flow explains about 5% of today's. A
  price effect has to be large per tonne to show.

## 5. The runner's assertions (each proved to raise in `--selftest`)

1. **Lag:**
   - a second implementation re-derives f_d for 40 sampled days from the fixture's text with the `csv` module;
   - **the break:** using the holdings dated d itself must raise;
   - every holdings date used is < d's ET calendar date;
   - E ≥ L0.
2. **The clock:**
   - 15:00 London = 10:00 ET on 2021-01-15 and 2021-07-15;
   - 15:00 London = **11:00 ET** on 2021-03-22 (US daylight saving began 03-14, UK 03-28);
   - 08:00 London = 03:00 ET on 2021-01-15.
3. **Sign in money:** +$1/oz on MGC = +$10 long; a short loses the same.
4. **Units:** the median GC close lies in [1,000, 2,200] $/oz; tonnes in [500, 1,500].
5. **Delivery:** no GC front on or after its first notice day (the last business day before the delivery month).
6. **The seal:** a 2024-dated bar or holdings row raises.
7. **The rotation's offset 0** equals the observed ρ.
8. **Chunk == whole:** the largest extraction file re-decoded serially equals its process result.
9. **Synthetic:**
   - a planted ρ passes G1;
   - noise fails it about 95% of the time;
   - an AR(1) (0.25) signal against independent returns fails it about 95% of the time.
10. **Spearman** is computed locally (Pearson of ranks); the system Python has no scipy.

**Speed:** the extraction takes about 3 minutes (GC, four processes); the run takes seconds.
**Output:** `data/stage0_d773_gld_flow.json`.

## 6. Predictions (Opus)

- **P1: NO DIRECTION** (P 0.65). AP flow is real, but it is spread over the day, partly netted inside the APs' own
  books, and small against gold's daily volume.
- **P2:** the diagnostic ρ(the flow dated d, y_d) is **positive** with p < 0.05 (P 0.6). Creation days coincide with
  rising gold, but contemporaneously; that cannot be traded.
- **P3:** the lag-1 autocorrelation of the flow on the eligible days is between 0.15 and 0.30 (P 0.8).
- **P(PREMISE HOLDS) ≈ 0.04.**
