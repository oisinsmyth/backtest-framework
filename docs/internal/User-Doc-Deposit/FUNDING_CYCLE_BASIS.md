# Funding-Cycle Basis: Study Design

**Status:** study design and pre-registration draft
**Instruments:** MBT (Micro Bitcoin), MET (Micro Ether) on CME
**External reference:** perpetual swap funding rates on the major venues (Binance, Bybit, OKX)
**Horizon:** minutes to an hour around each funding timestamp; flat by default
**Novelty:** moderate — the funding cycle is well known to crypto-native traders; the CME
micro-basis expression is a regulated-futures-only angle few of them use.

**Companions:** `OVERNIGHT_IMBALANCE.md` (template), `EVENT_PORTFOLIO.md` (stacking).

---

## 1. The mechanism

### 1.1 Funding is a scheduled, mandatory cash flow

Perpetual swaps have no expiry. To tether them to spot, venues charge a **funding payment**
between longs and shorts at fixed intervals — typically **every 8 hours** at 00:00, 08:00 and
16:00 UTC. The rate is published ahead of each settlement and is set by the perp–spot premium.

At the funding timestamp, one side pays the other. That is a **mandatory, price-insensitive
cash flow** at a **published time**, and the population subject to it is the entire leveraged
perp market.

### 1.2 The behavioural response

Traders on the paying side have an incentive to **close or reduce before funding** and re-open
after. Traders on the receiving side have the opposite incentive. Both produce **flow clustered
around the funding timestamp**, in a direction determined by the funding sign.

### 1.3 Transmission to CME

CME's MBT and MET are dated futures with **no funding**. Their fair value relative to spot is
set by interest and time-to-expiry, not by the funding cycle. So:

```
basis_CME = F_CME − S                    # slow, driven by rates and expiry
basis_perp = F_perp − S                  # fast, driven by funding
spread = basis_perp − basis_CME          # carries the 8-hour cycle
```

Flow around funding moves the perp price relative to spot; arbitrageurs transmit part of that to
CME with a lag. The **CME micro basis therefore carries a periodic, calendar-known component**
at 8-hour intervals.

### 1.4 Why it passes the filter

- **Named population:** leveraged perp traders
- **Published constraint:** funding rate and settlement time, both public before the event
- **Derivable direction:** sign of funding → sign of the pre-settlement flow
- **Three events per day, two instruments** — the highest breadth in the programme

### 1.5 Why the edge should persist

Crypto-native traders trade the funding cycle on the venues themselves. The **CME expression**
is one they largely cannot or do not use — different account, different regulation, different
capital. And the micro contracts are far below the size anyone arbitraging CME–perp
professionally would trade.

---

## 2. Derivation

Expected pre-settlement flow direction:

```
funding_rate > 0  →  longs pay  →  longs reduce before settlement  →  selling pressure on perp
funding_rate < 0  →  shorts pay →  shorts reduce                    →  buying pressure on perp
```

Magnitude scales with |funding_rate| × open interest (both published). Post-settlement, the
incentive reverses and positions are re-established — **the predicted pattern is a
pre-settlement move in the funding-sign direction and a post-settlement reversion.**

Transmission to CME is partial and lagged; **the lag is the one estimated parameter.**

---

## 3. Features

| ID | Feature | Definition |
|---|---|---|
| F1 | **Funding sign and magnitude** | Published rate for the upcoming settlement, cross-venue average |
| F2 | **Time to funding** | Minutes to next 8-hour timestamp |
| F3 | **Perp–CME spread deviation** | `spread` (§1.3) z-scored against its trailing distribution |
| F4 | **Pre-settlement flow** | Signed aggressive volume in MBT over the prior 15–30 min |
| F5 | **Open interest × funding** | Published perp OI × |F1| — expected flow magnitude |

**Signal:**
- **Pre-settlement (F2 < 30 min):** position in the funding-sign direction on MBT/MET, sized by F5
- **Post-settlement (F2 just reset):** reverse — position against the funding-sign direction
- Or, cleaner: **fade F3** — when the spread deviates in the funding-predicted direction, position
  for its reversion after settlement

---

## 4. The discriminator

The perp–CME spread mean-reverts for many reasons. This study has an edge only if **the
reversion is concentrated around funding timestamps and signed by the funding rate.**

**Pre-registered test:** compare F3 reversion in the 30 minutes after funding against the same
window at random non-funding times. **Prediction:** larger, more reliable, and directionally
consistent with F1 at funding times.

If reversion is no different at funding times, the cycle is not transmitting to CME at a
tradeable magnitude, and the study stops.

---

## 5. Data

| Data | Use | Status |
|---|---|---|
| MBT/MET intraday, Databento GLBX | F3, F4, targets, cost | Held |
| Perp funding rates and OI, three venues, 8-hourly | F1, F5 | Free via venue APIs; history available |
| Perp mark price, intraday | F3 | Free via venue APIs |
| Spot reference (CME CF index) | Basis | CME published |

**Sample:** MBT from May 2021, MET from December 2021. **Four to five years, ~4,500 funding
events per instrument.** Short in calendar time, deep in event count — the best event-count
sample of the five.

**Timestamp discipline:** three venues, three timezones, three settlement conventions. UTC
throughout, verified against the venues' own published schedules. This is the place a fake
signal is most likely to be manufactured by alignment error.

---

## 6. Targets

| Target | Window |
|---|---|
| R1 | Settlement → +15 min |
| R2 | Settlement → +30 min — primary |
| R3 | Settlement → +60 min |
| R4 | Settlement −30 min → settlement — the pre-move |

---

## 7. Cost

MBT is 0.1 BTC; the tick is $5. Spreads are wide relative to the full-size BTC contract, and
the 00:00 UTC settlement lands in thin US-evening liquidity. **Cost is likely the binding
constraint**, and the 00:00 UTC event may fail the gate while 16:00 UTC (US morning) passes.
Test cost **per settlement time**, not pooled.

---

## 8. Trial budget

**7 trials.** F1–F5 (5), the §4 discriminator (1), the per-settlement-time cost split (1).

---

## 9. Kill criteria

1. Cost gate fails at all three settlement times.
2. §4 shows no funding-time concentration. **Terminal.**
3. Reversion present but **sign-inconsistent with F1** — mechanism not as derived.
4. Effect confined to 2021–22 (peak leverage era) — decayed with deleveraging of the perp market.

---

## 10. Constraint fit

| Constraint | Fit |
|---|---|
| Futures only | Yes — CME MBT/MET |
| Prop rules | Directional, single instrument, flat by default. **Verify the firm permits crypto micros** — not all do |
| Trailing DD | Minutes of exposure |
| Minimum activity | Three events per day |
| Algorithmic | Fully — timestamps are fixed |

**Weekend note:** funding settles seven days a week. CME crypto futures trade Sunday evening to
Friday afternoon. Weekend settlements have no CME expression, so the tradeable set is ~15 events
per week per instrument, not 21.

**Forced-flat cutoff note, added 18 Sep 2026.** Major firms require accounts flat daily —
Topstep by 3:10 PM CT, Apex by 4:59 PM ET — with no overnight holds. The 00:00 UTC settlement
(20:00 ET) falls in the post-cutoff evening session. Whether a position opened after the Globex
reopen and closed within minutes is permitted depends on how each firm's rule is worded
(daily-flat requirement versus trading-hours restriction). **Verify per firm before counting the
00:00 UTC event.** If it is excluded, tradeable events fall to ~10 per week per instrument, and
the 00:00 UTC event — already the one most likely to fail the cost gate — is out regardless.
On personal capital none of this applies.

---

## 11. Sequence

1. Build the aligned perp/CME dataset in UTC; verify alignment on known events.
2. Cost gate **per settlement time** on F3 → R2.
3. §4 discriminator.
4. Estimate the transmission lag (the one free parameter) on training folds only.
5. Full harness, CPCV with days as groups.

---

## 12. Open questions

1. Has the perp market's deleveraging since 2022 reduced funding-driven flow below detectability?
2. Is the transmission lag stable, or does it depend on CME liquidity at the time of day?
3. Do MBT and MET move together at funding (one bet) or independently (two)?
4. Does venue-specific funding (Binance vs Bybit) diverge enough that the cross-venue average
   loses information?

---

## 13. Honest position

Highest event count and cleanest calendar of the five. The mechanism is genuine and the
population large.

Against that: the CME micro expression is thin, cost at 00:00 UTC is probably prohibitive, and
the perp market has deleveraged substantially since the sample began. The realistic outcome is
that one or two of the three daily settlements are tradeable and the others are not — which is
still a high-breadth strategy, just less than the headline suggests.

Also worth noting for the portfolio: this is the one event study **entirely uncorrelated with
the equity-index ones** by asset class, which makes it disproportionately valuable in
`EVENT_PORTFOLIO.md` even at a modest standalone Sharpe.
