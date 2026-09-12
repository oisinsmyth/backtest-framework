# D494 — RESULT: outside the price path on the day session — eighteen cells, no pick; the largest is the euro at one tick, and the MACD on release days is worse, not better

**2026-09-12.** Spec [D494 PRE-REG](D494-PRE-REG-direction-from-outside-the-price-path-on-the-day-session-cross-instrument-overnight-moves-index-level-retail-sentiment-and-release-days-as-a-gate-on-the-MACD.md)
(`62404c7`, before the code). Runner `scripts/run_d494_outside_path.py`; numbers
`data/d494_outside_path.json`; log `temp/d494_run.log`. In-sample 2016-01-04 → 2023-12-29 on the
D467 hourly tables (ES day legs 1,975, NQ 1,972), Robintrack 2018-05 → 2020-08 (541 sessions,
11 dropped for the two outages and thin days), the recorded release calendar. **2024 onward
unread; no holdout of any line touched; nothing admitted.** 0.2 min.

## 0. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| 1 B1: no cell clears the 18-cell bar; largest is a bond predictor on NQ, $10–30; N1 p95 $15–25; family p95 $30–45 | | **No cell clears.** The largest is **the euro: 6E→ES −$16.9 (N1 \|p95\| 15.4), 6E→NQ −$21.2 (23.6)** — the euro, not bonds; bonds are ±$1–6. N1 p95 $12–24 (held); family p95 **$64.9** (missed high, see §2) |
| 2 B2 inside noise, \|side diff\| < $30 | | +$6.9 (ES), +$4.2 (NQ) against N1 p95 of $25 / $35 — held |
| 3 B3: event-day σ 1.4–2× the control; mean P&L not different at 2 SE on five of six; if one, FOMC on NQ | | σ ratio **0.85–1.4** (FOMC NQ 1.39, CPI ES 1.15, Employment 0.85) — missed low; **no cell different beyond its N1 p95; five of six are negative** (the MACD earns less on release days); FOMC on NQ is the one positive, +$15.9 against a \|p95\| of 65.7 — inside |
| 4 sub-family maxima below the 18-cell p95 | | B1 32.6, B2 36.1, B3 64.9 = the 18-cell p95 (B3's small-n cells set the bar) — held |

## 1. The cells (dollars at one micro; side difference = top tercile − bottom tercile of the predictor)

| cell | n | statistic | N1 exact \|p95\| | inside? |
|---|---|---|---|---|
| B1 ZN→ES / ZN→NQ | 1,948 / 1,945 | −0.7 / −3.2 | 14.4 / 24.3 | yes / yes |
| B1 ZB→ES / ZB→NQ | 1,947 / 1,944 | +5.6 / −0.5 | 15.0 / 23.7 | yes / yes |
| **B1 6E→ES / 6E→NQ** | 1,957 / 1,948 | **−16.9 / −21.2** | 15.4 / 23.6 | **no** / yes |
| B1 GC→ES / GC→NQ | 1,940 / 1,937 | −7.0 / −14.8 | 14.9 / 23.0 | yes / yes |
| B1 CL→ES / CL→NQ | 1,890 / 1,887 | −8.3 / −8.7 | 15.1 / 23.8 | yes / yes |
| B2 Robintrack→ES / →NQ | 541 / 539 | +6.9 / +4.2 | 24.8 / 34.5 | yes / yes |
| B3 CPI \| ES / NQ (gated − control) | 76 / 77 | −31.5 / −17.4 | 32.0 / 49.0 | yes / yes |
| B3 Employment \| ES / NQ | 91 / 90 | −13.3 / −27.0 | 28.4 / 44.4 | yes / yes |
| B3 FOMC \| ES / NQ | 43 / 43 | −16.0 / +15.9 | 42.6 / 65.7 | yes / yes |

Family maximum of |statistic| over the 18 cells (538 common offsets): **p50 38.2, p95 64.9.**
Sub-family p95: B1 32.6, B2 36.1, B3 64.9. **Picks: none.**

**The euro cell.** A stronger dollar overnight (6E down) is followed by a better ES day leg:
Spearman −0.044, terciles +$11.8 / −$2.0 / −$5.1 at one MES — $3.4 a session gross on the
tercile spread, about one tick of ES, against a $3 round trip. It sits 10% above its own exact
null and half the family bar. It is the textbook best-of-eighteen and it is one tick.

**The release days.** The MACD's day-leg P&L is *lower* on CPI and Employment days than on the
matched control on every cell (ES −$34 vs −$2 on CPI), and the event-day σ is not the 1.4–2× I
predicted — the 10:00 → 16:00 leg starts ninety minutes after the 08:30 print, so the print's
variance is already gone. FOMC on NQ is the one positive gate (+$15 vs −$1, 43 sessions, hit
65%) and is inside its own null by a factor of four.

## 2. Audits, including one that was mis-designed

[S] sign in money; [X] flipping the predictor negates the side difference exactly; [D] no
session after 2023-12-29 reached the runner; [C] the calendar: the three non-Wednesday FOMC days
(2018-11-08, 2020-11-05, 2024-11-07) and the one non-Friday Employment day (2020-07-02) are the
real exceptions, checked; [M] the gate control is a partner weighting by (weekday, year), not a
re-drawn subset. **[F] as designed did not test what it claimed:** the "shifted predictor"
control (session t+1's overnight move against session t's day leg) came out at +$26.8, *above*
the null — because the t+1 overnight begins at 18:00 on day t, two hours after the day leg
ends, and the day's move spills into it. That is a contemporaneous spillover, not a leak, and a
control that carries information is not a control. The no-future guarantee rests on the column
stamps (predictors end at the 09:00 open or earlier; entry is the 10:00 print), which is by
construction; the shifted control is withdrawn and recorded as a design error.

**A note on the family bar.** The 18-cell maximum is set by B3's 43-session FOMC cells, whose
nulls are wide; as declared it is one bar for the record, and it is what refused everything.
The sub-family bars would not have changed the verdict: the euro cell is under B1's 32.6.

## 3. What this settles

- **At session resolution, on this data, direction from outside the price path is worth at most
  a tick a day** on ES and NQ: bonds nothing, gold and crude a few dollars the wrong way for a
  momentum read, the euro one tick, index-level retail sentiment nothing, and the scheduled
  prints make the one real signal on the table earn less, not more.
- Read against **D493**: a day-session prop component needs several full-contract ticks a
  session to stand off the barrier. Nothing here is within an order of magnitude of that.
- Predictions 2 and 4 held; 1 held on the verdict and missed on which instrument and on the
  family p95; 3 missed on σ and on the sign of the event-day effect.

## 4. What it does not do

Nothing enters `COMPONENTS_PROP.md` or either book; the 2024+ slice stays sealed; the
single-name Robintrack test remains a personal-book draft; the ten-year RTAT version is not
run (no key). Closing the "outside the price path" question at this resolution is the
principal's call; my reading is that the day session on the index futures does not carry it
at hourly resolution, and the next place to look is not another predictor of the same leg.
