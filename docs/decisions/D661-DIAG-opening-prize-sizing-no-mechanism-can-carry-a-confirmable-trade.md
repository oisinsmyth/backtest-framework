# D661 — DIAG: sizing the prize — no known mechanism can carry a confirmable trade after the opening range, and the biggest flows land at the close

*2026-09-28. The principal: "Can we not find a theoretical maximum impact on price and look at the biggest ones?",
then "Yes, run the prize-sizing table". Post hoc, after D660. No construction, no registered statistic, no verdict of
D658–D660 changed.*

**Sources:**
- market inputs: `scripts/diag_opening_prize_bar.py` → `data/opening/prize_bar.json` (in-sample only; the runners'
  sealed loader);
- flow sizes: three research agents, reports verbatim in `docs/research/opening-prize-sizing-sources.md` (C1
  options/dealers, C2 systematic flows, C3 auctions, impact law and microstructure);
- the table: `scripts/diag_opening_prize_table.py` → `data/opening/prize_table.json`.

## 1. The bar: what a mechanism must be able to do

Suppose a mechanism pushes the price by I, with standard deviation s across days, and suppose the push were known
perfectly. Trading its sign earns E|I| = 0.8 s per trade gross.

Market inputs, in-sample ES, 2023-03 → 2025-02:
- day-session volume: $284bn a day;
- σ: daily 82 bp; 10:00 → 11:00, 30 bp; 10:30 → close, 56 bp;
- the micro round trip: 2.2 bp.

NQ is similar in bp.

| design | push sd needed | one-way unanticipated flow, square-root law (Y 1 → 0.5) |
|---|---:|---|
| break even at micro cost | 2.8 bp | ~$0.3bn |
| **confirmable, daily trade, 60-min hold** (390 vault sessions, 80% power) | **8.2 bp** | **$2.8–11bn** |
| confirmable, daily, hold to close | 12.7 bp | $7–28bn |
| confirmable, a 40-event design | 19.6 bp per event | $16–65bn |

**A mechanism that fires on k days a year gets its own bar.** It has k × 390/252 events in the vault, and needs
(2.80 σ₆₀/√n + c)/0.8. That is 27–30 bp at 15–19 events, 41 bp at 8, and 57 bp at 4.

## 2. The ceiling for mechanisms that predict SIZE, not direction

D645's own breakout baseline B3:
- range 09:30–10:00;
- entry on the first close beyond it by 11:29;
- stop at half the range;
- 60-minute hold, micro cost.

It was run on all 4,570 in-sample session-markets and bucketed by the ex-post expansion (the 10:00–16:00 range over
the opening range).

| perfect foresight of | net per trade | t | vault power |
|---|---:|---:|---:|
| none (every breakout) | −3.15 bp (gross −0.09) | | |
| the top 50% expansion days | +0.51 | 0.69 | 5% |
| the top 20% | **+4.65** | 3.76 | **34%** |
| the top 10% | +6.44 | 3.64 | 32% |

**Even a perfect size forecast gives a breakout trade only about a third of the vault power it needs.** The trade's
own noise (37 bp per trade) swamps it. Every mechanism that predicts only size therefore fails as the source of an
opening-range edge. That covers 10:00 releases, compression against the expected range, the volatility regime, the
calendar, and dealer gamma as a follow-through modulator. Such mechanisms can still filter a direction signal; they
cannot be one.

## 3. The prize-sizing table

The impact band runs:
- LOW: Y 0.5 and V = the linked complex, taken as 3× ES;
- HIGH: Y 1 and V = ES alone.

"Lands after 10:00" is my reading of each source's timing.

| # | mechanism | flow on the day ($bn, one way) | impact band (bp) | vault events | push needed | lands after 10:00 | verdict |
|---|---|---|---:|---:|---:|---|---|
| 8 | opening-auction imbalance (the WHOLE auction as the ceiling) | 0.2–4.4 | 0.6–10.2 | 390 | 8.2 | **no**: 09:30, published from 08:00 | **fails timing**; realistically a fraction of the ceiling |
| 6a | dealer gamma, typical day (+$2–6bn per 1%) | 0.5–2.0 | 1.0–6.8 | 390 | 8.2 | yes | fails size; and it damps moves |
| 6b | dealer gamma, negative tail (p5–p1) | 0.8–2.2 | 1.2–7.2 | 16 | 29.8 | yes | fails size |
| 6c | dealer gamma, extreme (−$7.5bn per 1%) | 7.5 | 3.8–13.3 | 4 | 56.7 | yes | fails size |
| 7 | 0DTE hedging in the morning, amplifying side | 0.44–2.0 | 0.9–6.8 | 390 | 8.2 | yes (weakest in the first hour) | fails size |
| 9a | CTAs, ordinary day | 0.2–1.0 | 0.6–4.8 | 390 | 8.2 | unestablished | fails size; anticipated |
| 9b | CTAs, trigger day | 1.2–3.6 | 1.5–9.2 | 16 | 29.8 | unestablished | fails size; triggers are published |
| 10 | vol-control, stress | 8–57 | 4.0–36.5 | 8 | 40.9 | **no**: close, 1–2 day lag | fails size at its frequency, and timing |
| LETF | leveraged ETFs on a 1% day (index products, net of fund flows) | 0.7–2.7 | 1.2–8.0 | 390 | 8.2 | **no**: last 30–60 min | fails size; D640 null |
| PEN | pension month/quarter-end, US | 3–10 | 2.4–15.3 | 19 | 27.4 | mostly **no** (close overlays; T−3 morning) | fails size at its frequency |
| IDX | index reconstitution | 0–0.5 | 0–3.4 | 6 | 45.4 | no (closing auction) | fails; net index flow ≈ 0 |
| BB | buybacks, one morning hour | 0.8–1.2 | 1.2–5.3 | 279 | 9.2 | yes | fails size; single-stock, VWAP |
| 11 | executed stops (0.9% of ES volume) | 0.1–0.5 | 0.4–3.4 | 390 | 8.2 | yes | fails size (Osler's FX cascade: +0.7 bp per 15 min) |
| 12 | forced deleveraging episode | 20–50 | 6.2–34.2 | 0.5 | 158.5 | yes | fails: under one event per vault |

**Nothing survives.** Every candidate fails on size at its frequency, on timing, or both. Three of the four
"promising" mechanisms from the enumeration fall:
- #6, dealer gamma measured properly: it damps on typical days, and its negative tail is too rare;
- #8, the opening auction: its whole value is small, and it is priced at 09:30;
- #16/#17, stops and round numbers: executed stops are 0.9% of ES volume, and the only measured cascade is 0.7 bp.

#25, compression, falls with §2's size family.

## 4. Caveats, which cut both ways

1. **The law is for patient flow.** A fast, concentrated flow peaks far higher. On 6 May 2010 a $4.4bn sale over 19
   minutes moved ES 5.1%, over 25× the law's figure (C3). But such peaks reverse, and they are unannounced. That is a
   different trade (reversal after a liquidity shock), and the programme closed its shock line (D643).
2. **Most flow sizes are bank scenario models seen through journalism** (C2), and some disagree by 5×. The bands take
   each source's range. Where a measured effect exists it is the better evidence:
   - Harvey, Mazzoleni & Melone: −16/−17 bp over the next day per 1-SD rebalancing signal;
   - Baltussen et al.: +6.6 bp in the last 30 minutes per 1% prior move, on negative-gamma days.

   **Both are at the close or across days, not after the open.**
3. **Y and V span 2–4× in both directions.** The bands use the favourable end (Y 1, ES alone) for the verdict. So a
   "fails size" here fails at the mechanism's best case.
4. **The timing and direction readings in the table are my judgment of the sources,** stated per row. #9 (CTA
   timing) is genuinely unknown, and it fails on size either way.

## 5. Disclosure: vault-period data read by an agent

- **What was read.** Agent C3 measured market size from fixtures running past 2025-03-01, the vault's start:
  - 2025 ES and NQ volume and σ;
  - micro-contract shares over 2025-09 → 2026-09;
  - 10:00-release move sizes over 2016–25.
- **Nature.** These were descriptive counts in its scratchpad (`mkt_size.py`, `ten_am.py`, `etf_size.py`). There was
  no construction and no registered statistic, and nothing was written to the repository.
- **Cause.** My prompt to the agents did not state the seal. The error is mine.
- **Containment.** This record uses none of those figures. Every market input comes from `prize_bar.json`, which ends
  2025-02-28. The figures appear in the sources file only inside C3's verbatim report, marked.
- **Effect.** No registered cell reads volume, σ or 10:00-release sizes as its statistic. The joint vault run's
  statistics (D630, D649, the index H-R cells, D645 H-O2, D652) are unaffected. The principal should know it
  happened.

## 6. Pooling rare flows into one book

The principal: "Does the frequency really matter if we overlay the flow of different candidates? If we model lots of
large flows even if they are rare?", then "So long as we have signed flow?"

**How pooling works:**
- One pre-registered book trades every member's events on one clock. Its bar is set by the pooled event count.
- Each member enters at its best case.
- The count is taken two ways: with no overlap, and with the rare stress members sharing their days. Vol-control
  selling, the gamma tail, CTA triggers and deleveraging cluster in the same episodes.

| pool | clock (σ) | members (days a year) | frequency-weighted best-case push | vault events | push needed | clears? |
|---|---|---|---:|---:|---:|---|
| morning | 60 min after 10:00 (30.3 bp) | gamma tail 10, gamma extreme 2.5, CTA triggers 10, deleveraging 0.3 | 9.1 bp | 35 → 16 | 20.7 → 29.8 | **no** |
| close | last 30 min (22.2 bp) | gamma tail 10, gamma extreme 2.5, vol-control 5, pension 12, leveraged ETFs on ≥1% days 55 | 10.8 bp | 131 → 119 | 9.6 → 9.9 | **only at the best case** |

1. **Frequency matters less once rare members are pooled.** The bar falls as 1/√(total events).
2. **The hold should match the flow's execution window.** Noise grows with √hold, while a concentrated flow's impact
   does not. The close pool gains twice: from its count and from a 30-minute clock (σ 22 bp against 30).
3. **The morning pool still fails,** because the morning members are small at their best case.
4. **The close pool clears only at the favourable end** (Y 1, V = ES alone). At the low end (Y 0.5, the linked
   complex) every push is 3–4× smaller and it fails.
5. **Its frequency weight is mostly the leveraged-ETF member (55 of 84.5 days),** which in-house testing already found
   small (D640). Carried gamma also did not condition the last half-hour (D581).
6. **Pooling needs, per member:**
   - a sign known *before* the flow executes;
   - an edge of its own;
   - one clock for all members.

   A pooled result must be reported member by member. Otherwise one member carries it, as 2022 carried V2-F.

**"Signed flow" means a forecast of the sign before execution, not a measure of it during execution.** A7 is signed
flow observed as it trades: the impact has partly happened by the time it is seen. The close pool's members have signs
knowable in advance:
- leveraged ETFs trade with the day's move;
- vol-control sells after volatility rises;
- pensions sell whatever has outperformed into month-end.

One published number aggregates most of them: **the closing-auction imbalance,** released from about 15:50, signed
and sized before the auction. It covers the market-on-close orders from leveraged ETFs, index funds and pension
overlays. The data exists (Databento's imbalance schema from 2018; 2016–17 via NYSE TAQ; price not public). It is not
on disk.

## What it means

1. **The opening range after 10:00 is not where large, unanticipated flows land.**
   - The biggest documented flows either arrive before the open (the auction, overnight news) or arrive at the close
     (vol-control, leveraged ETFs, pension overlays, index events).
   - The ones that do trade through the morning (CTAs, buybacks, stops, dealer hedging) are too small, too
     anticipated or too rare to clear a confirmable bar.
2. **More participant data would not change this.** SPX/0DTE gamma is rows 6a–6c and 7. The auction imbalance is row
   8. Both fail at their best case.
3. **The close and month-end are where the measured effects are.** But the programme has already worked there:
   - leveraged-ETF close flow was killed by its placebo (D640);
   - intraday momentum was 1.2 bp in-house (D463);
   - carried gamma did not condition the last half-hour (D581).
   A new close or month-end line would start from those records, not from here.
4. **Pooling (§6) does not rescue the morning.** At the close it clears only at the best case. The one direct
   observation of the close pool, the closing-auction imbalance, is the natural first test of that idea if the
   principal wants one. It would be a new line: its own Stage 0, and a data-cost question first.
5. **Recommendation:**
   - close the opening line: D645 H-O2 (slot 7) and D652 v2 without its vault look (slot 9 never taken);
   - keep §1–§3 as the standard first step for any new mechanism line: size the prize before any test.
