# D764 STAGE 0 PRE-REGISTRATION — the CME bitcoin expiry window: on the last Friday of the month, when CME bitcoin futures settle to the CF Bitcoin Reference Rate (15:00–16:00 London), does the window's move reverse in the hour after it, more than on other Fridays? (BTC prices, scored at one MBT; prop book)

*2026-10-02. Prop book.*
- *The principal: "Lets look at MBT, are there any data sources that could move it?". They then chose "CME expiry
  window (Recommended)".*
- *Numbered D764, claimed with the documentation-review session.*
- ***Committed alone, before its runner exists.** In-sample only (2017-12-18 → 2023-12-29).*

## 0. The mechanism and what is on file

**The mechanism.** CME bitcoin futures (BTC, and MBT from 2021-05) settle at expiry to the **CME CF Bitcoin Reference
Rate (BRR)**, computed from spot-exchange trades between **15:00 and 16:00 London time**.
- **Expiry falls on the last Friday of the contract month,** or the previous joint UK–US business day.
- **The forced trade:** holders of expiring positions who want the settlement price trade spot through that window.
  That includes basis traders, long spot and short futures, unwinding their spot leg. Their flow is price-insensitive
  and clock-fixed, like the settlement windows of D630.
- **If it is temporary pressure,** the window's move should give back in the following hour.

**The control shares the daily fix.** The BRR is published every day at 16:00 London, so other Fridays' same window
also contains the daily benchmark. The expiry-day difference isolates the settlement flow.

**On file:**
- **D580:** the perp funding clock on CME bitcoin. NOT SUPPORTED.
- **D758:** the weekend gap. NOTHING, CLOSED.
- **D761:** round-number cascades on MBT. CLOSED.
- **The off-hours size table** (the documentation-review session, AITODO): MBT's US-day one-hour \|move\| is about
  1.6 × 2c, larger than its off-hours.
- **Nothing on file reads the expiry window.**

**The regime caveat.** US spot ETFs launched on 2024-01-11, and the CME basis trade grew sharply after it. This
in-sample window (2018–2023) is the pre-ETF era, likely the weakest for this flow. A result here may not transfer, in
either direction.

## 1. Data and the calendar (fixed now)

**Bars:** `fut_btc_1m.csv.gz`, root **BTC** (the full-size contract, liquid from 2018; it is the same price MBT
tracks).
- Rows dated on or after 2024-01-01 are dropped as text on read, and the cut is asserted.
- The front contract per trade date is the fixture's own.

**Prices:**
- **P_t** is the close of the last BTC front bar starting **before** t on that trade date.
- **Staleness guard:** if that bar started more than 10 minutes before t, the session is ineligible for that quantity.
- **London times** are converted to UTC with `zoneinfo` (Europe/London), so BST and GMT and the US–UK DST mismatch weeks
  are handled. In ET the window is usually 10:00–11:00, and 11:00–12:00 in the mismatch weeks.

| quantity | definition |
|---|---|
| t₀, t₁, t₂ | 15:00, 16:00 and 17:00 London on the session's date |
| **x, the window move** | P(t₁) − P(t₀) |
| **y, the response** | P(t₂) − P(t₁) |
| y₂ (reported) | P(t₁ + 2 h) − P(t₁) |
| pre (reported) | P(t₀) − P(t₀ − 1 h) |

**The expiry calendar E:**
- the last Friday of each month, 2018-01 → 2023-12 (72 days);
- if it is not a business day in both the UK and the US, the previous joint business day. On this window that is
  **2018-03-30 → 2018-03-29** (Good Friday) and **2020-12-25 → 2020-12-24** (Christmas).
- **The spot check:** 2018-01-26, the first BTC expiry, is in E.

**The control C:** every eligible Friday not in E, at the same London clock.

**Scored at one MBT:** $0.10 per point; cost $3.00 commission plus 2.62 ticks at $0.50, $4.31 a round trip (the
default line in `data/futures_costs.json`).

## 2. The checks

**E1 — the expiry effect.**
- **The statistic:** Δ = ρ(x, y \| E) − ρ(x, y \| C), Spearman within each set.
- **The null:** the exact enumerated **rotation of the expiry label** along the ordered list of eligible E-or-C days
  (offsets 1 … N−1; the full group, D763's lesson).
- **Passes:** Δ < 0 and below the rotation's p05 (one-sided, one root, no Holm).
- **Also reported:** Δ's two-sided rank.

**E2 — the prize.**
- **The fade:** on E days, take the side −sign(x) at P(t₁) and exit at P(t₂), one MBT.
- **Passes:** the mean gross ≥ $4.31, with t ≥ 2.
- **Reported:** the same fade on C days, and a Welch t of the difference.

**The readings:**

| reading | when |
|---|---|
| **NO EFFECT** | E1 fails |
| **EFFECT, NO PRIZE** | E1 passes; E2 fails |
| **PREMISE HOLDS** | both pass |

**What follows a PREMISE HOLDS:** a trading pre-registration read forward (about 12 expiries a year) and on the held
slice, on the principal's word. That slice is the ETF era, so the record would have to state the regime change.

## 3. Reported, never gating

- **The pressure's sign:** the mean x on E against C (the basis-unwind story predicts selling in the window).
- **The pressure's size:** mean \|x\| and the window's BTC volume, E against C.
- The y₂ horizon, and the pre-window hour.
- **By year;** the MBT era (2021-05 onward) alone.
- **The fade's four groups** at one MBT, with the top trades named.
- ρ of its daily net with F2, C1 and D737 (`data/d748_component_books.csv`).

## 4. Size and power (stated now)

- **The events:** about 72 E days against about 240 control Fridays.
- **The SE:** ρ_E has an SE of about 0.12, so E1 can see a Δ of about −0.3 or larger.
- **The prize:** a US-hours hour on MBT moves about $14 (1.6 × 2c). If a third of a window move reverses, the fade
  grosses perhaps $3–5, near the $4.31 cost.
- **So:** this tests for a large effect.

## 5. The runner's assertions (each proved to raise in `--selftest`)

1. **The calendar:**
   - 72 days, every one a Friday except the two substitutes;
   - 2018-01-26, 2018-03-29 and 2020-12-24 are present;
   - no E day is in C.
2. **The clock:** t₀ converts to 15:00 UTC in January and 14:00 UTC in July, and to 11:00 ET in a mismatch week (for
   example 2018-03-23).
3. **Lag audit, a second implementation:** for 40 sampled sessions (half of them E), a plain loop over the raw rows
   re-derives P(t₀), P(t₁), P(t₂), x and y. **Break:** taking the bar that starts AT t instead of before it must
   raise.
4. **Sign in money:** a favourable move pays long and short positively.
5. **The rotation's offset 0** equals the observed Δ.
6. **The seal:** a 2024-dated row injected into the input raises.
7. **Synthetic:** a planted expiry reversal passes E1, and noise fails it about 95% of the time.

**Speed:** a few seconds. **Output:** `data/stage0_d764_btc_expiry_window.json`.

## 6. Predictions (Opus)

- **P1: E1 fails** (P 0.65). In 2018–2023 the CME basis book was small next to spot volume, and the BRR averages
  over many venues, so settlement flow is diluted.
- **P2: \|x\| is larger on E days than on C days** (P 0.55): some settlement activity shows in size.
- **P3: E2's mean gross is below the cost** (P 0.8).
- **P(PREMISE HOLDS) ≈ 0.06.**
