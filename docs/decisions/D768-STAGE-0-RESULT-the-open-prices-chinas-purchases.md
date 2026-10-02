# D768 STAGE 0 RESULT — NO DIRECTION on ZS and ZC: China's purchases are news, and the 09:30 open prices them (the break gap is +$1.44 per micro on soybean sale days, p 0.001); the day session then adds nothing (+$0.41 against a $5.50 cost on ZS, −$0.09 on ZC)

*2026-10-02. Prop book.*
- *Pre-registration: [D768](D768-STAGE-0-PRE-REG-china-buys-soybeans-and-the-cbot-day.md) (`6e6ab35c`).*
- *Runner: `scripts/stage0_d768_usda_china_sales.py` (`916edbe7`; fix `c44adfe4`).*
- *Output: `data/stage0_d768_usda_china_sales.json`. Extraction 2.8 minutes; run 2.0 seconds.*

**The first run stopped before any result.** The break guard raised, and nothing was printed or written.
- **The bug:** the code counted bars starting in [08:45, 09:30) ET, but the pre-registration's assertion is an *open*
  interval, (08:45, 09:30).
- **What it flagged:** 27 ZS and 18 ZC sessions. All but one were a single bar starting at exactly 08:45:00, the
  overnight session's closing minute (07:45 CT, 1–104 contracts).
- **The fix** (`c44adfe4`) opened the interval and added a self-test. It was committed and disclosed before the one
  complete run.

**The checks:**
- **the break:** 99.95% of sessions on both roots print nothing between the overnight close and the 09:30 open. The
  one exception is a 09:29 bar on 2018-08-06;
- **units:** the median close is 1,018 cents (ZS) and 387 cents (ZC);
- **delivery:** the nearest a front came to its first notice day was 5 days (ZS) and 4 days (ZC);
- **the lag audit:** a csv-module second implementation agreed on 60 sessions per cell;
- **the rotation's offset 0** reproduced A;
- **the seal:** nothing on or after 2024-01-01 was decoded;
- **the extraction:** the serial re-decode of the largest file equalled its process result.

**The sessions:**
- **ZS:** 1,991 eligible, 486 of them events. 6 announcements fell on days CBOT was shut or had no price. 2016-04-14/15
  were dropped as an ambiguous dateline.
- **ZC:** 1,983 eligible, 171 events. 2 were lost the same way. Nine 2016 days and 2022-07-15 (a same-day retraction)
  were dropped.

## 1. The reading

| | ZS (soybeans) | ZC (corn) |
|---|---|---|
| **G1: A = mean y on event days** (09:30 → 14:15, $ per micro) | **+$0.41** | **−$0.09** |
| the exact rotation p2.5 / p50 / p97.5 | −7.81 / −3.06 / +1.73 | −4.58 / −0.27 / +3.98 |
| two-sided p (Holm over two) | 0.158 (no) | 0.933 (no) |
| G2: the long's gross against $5.50; NW t | +$0.41; 0.16 | −$0.09; −0.03 |
| G3 | 1 of 8 years positive | 0 of 8 |
| **reading** | **NO DIRECTION** | **NO DIRECTION** |

**The soybean day session drifts down in-sample.** It averages −$3.03 per micro on all days (t −2.3) and −$4.15 on
days without a sale.
- That is why the rotation's median is −$3.06. Event days sit about $4.6 above the other days, inside the band.
- **In money the long nets −$5.09 a trade** (t −2.0). The day after a China sale is no worse than a flat day; it is not
  a good one.

## 2. The sale is news: the open prices it

The break gap is g_break = O − P(08:45), the move across the break in which the announcement lands.

| | ZS | ZC |
|---|---|---|
| g_break on event days / other days | **+$1.27 / −$0.17** | **+$1.04 / +$0.04** |
| Δ, rotation p5 / p50 / p95, p | **+$1.44**; −0.49 / −0.01 / +0.50; **p 0.001** | **+$1.00**; −0.36 / −0.01 / +0.38; **p 0.001** |
| overnight g_night: Δ, p | −$0.04, p 0.98 (no anticipation) | **+$4.38**, p 0.03 (anticipated) |
| cancellation days: g_break / y (n) | −$3.85 / −$8.33 (12) | −$3.25 / −$15.75 (10) |
| sales to other destinations: g_break / y (n) | −$0.42 / +$1.46 (42) | +$0.21 / −$0.71 (202) |

**The footprint is real and specific:**
- **The market moves at the open on a sale to China or unknown destinations.** It does not move on sales to Mexico,
  Japan and the rest (the placebo), and it moves the other way on a cancellation.
- **Corn's buying is also seen overnight,** before the announcement (rumour, or the sale itself trading). Soybeans'
  is not.

**The footprint is small.** +$1.44 per micro is about 0.29 cents a bushel. That is less than one micro tick ($2.50),
and a quarter of a round trip.

**Then nothing follows.** The fade of the gap grosses +$2.50 on ZS (t 1.1) and −$0.12 on ZC, and ρ(g_break, y) on
event days is −0.09 and +0.05. The purchase is priced at the open and stays priced.

## 3. Splits (reported, never gating; event-day y per micro)

| | ZS | ZC |
|---|---|---|
| China / unknown destinations | +$0.23 (283) / −$1.12 (284) | **−$10.39** (55, t −1.75) / **+$4.55** (123, t 1.87) |
| a sale of 500,000 t or more | −$6.88 (24) | −$15.66 (34) |
| before the trade war / trade war / Phase One / 2022–23 | −1.22 / −7.71 / +2.28 / +4.44 | +2.84 / +7.42 / −6.21 / +3.45 |
| Thursdays (weekly report) / other days | −1.05 / +0.76 | +2.50 / −0.64 |
| WASDE days / the rest | +8.29 (30) / −0.11 | 0.00 (7) / −0.09 |
| Sep–Nov events / other months / Sep–Nov non-event days | +3.58 / −1.12 / −2.57 | +1.55 / −0.54 / +2.10 |
| \|y\| ratio, event/other (rotation p95) | 0.93 (1.14) | 1.06 (1.23) |
| days with both a soybean and a corn event (47) | −$5.32 | +$5.32 |

- **Corn sold to China *by name* falls on the day,** and the large sales most (2020–21, April 2022, March 2023). This
  is post hoc and small. The worst three corn days are 2021-05-10/13/14, inside China's run of 0.68–1.7 Mt purchases
  announced almost daily from 7 to 20 May 2021.
- **Event days are not larger:** the size ratio is 0.93 and 1.06, both inside the null.

## 4. The trade (one micro, long at the open on event days; four groups)

| | ZS | ZC |
|---|---|---|
| trades (exposure) | 486 of 1,991 sessions, 4.75 h each | 171 of 1,983 |
| gross mean (median) | +$0.41 (−$1.25) | −$0.09 (+$2.50) |
| **net mean (median)** | **−$5.09** (−$6.75) | **−$5.59** (−$3.00) |
| net with one extra tick | −$7.59 | −$8.09 |
| win (net); payoff | 43%; 1.01 | 42%; 0.84 |
| skew / kurtosis | 0.08 / 4.1 | −0.93 / 10.1 |
| net trims: ex-top 1% / ex-bottom 1% / both | −6.71 / −3.21 / −4.84 | −6.54 / −4.38 / −5.34 |
| daily net Sharpe (Sortino); gross | −0.72 (−0.96); +0.06 (+0.08) | −0.76 (−0.92); −0.01 (−0.02) |
| max drawdown; break-even cost | $3,008; $0.41 | $1,003; none |
| net by year | 2022 +$382 the only positive year | none positive |
| best and worst trades | 2023-06-30 +$301; 2016-07-07 −$262 | 2021-05-27 +$157; 2021-05-14 −$211 |
| ρ with D737 / F2 / C1 | −0.01 / −0.00 / +0.03 | −0.01 / +0.05 / +0.00 |

**The component line:** net Sharpe −0.72 and −0.76. Neither is a component.

## 5. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | ZS Δg_break above its rotation p95 (P 0.7) | **held:** +$1.44 against +$0.50, p 0.001 (ZC too) |
| P2 | NO DIRECTION on both cells (P 0.6) | **held** |
| P3 | cancellation days have a negative g_break (P 0.6) | **held:** −$3.85 (ZS, 12 days) and −$3.25 (ZC, 10 days) |
| | P(PREMISE HOLDS) ≈ 0.08 / 0.05 | NO DIRECTION / NO DIRECTION |

## 6. What it shows

**China's demand leaves a footprint, and it is the efficient kind.**
- A publicly announced purchase moves the price at the first print after it, by about a third of a cent a bushel. It
  is specific to China and unknown destinations, and it reverses sign on cancellations.
- The rest of the day carries nothing. The market prices a known purchase at the open.

**The footprint is in the gap, not in the session,** and the gap is not tradable on this clock: the announcement
lands while CBOT is shut, and the gap is sub-tick for a micro.

**On the principal's idea:** a demand economy's buying is visible and does move price. But once it is public, it is
priced in a single print. The tradable part would have to come before publication (corn's overnight anticipation, Δ
+$4.38, p 0.03), and that is the sale itself trading, not a signal anyone holds at 08:45.

**What follows:**
- No trading pre-registration in-sample.
- **The principal's call:** close the USDA-sales line, or test a different footprint:
  - the corn overnight (anticipation);
  - the Chinese holiday calendar (the buyer absent).
- **POST HOC, not a finding:** corn sold to China by name, and the large sales, fell on the day (n 55 and 34). It would
  need its own pre-registration and a low prior.

## 7. CLOSED (2026-10-02)

**The principal: "Close that construction. Lets continue on this demand economy line."**
- The USDA daily-sales construction is closed for the prop book.
- The demand-economy line stays open.
- The fixture `usda_daily_export_sales.csv` remains available.
