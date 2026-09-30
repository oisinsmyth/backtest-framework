# D710 STAGE 0 DESIGN — the Treasury auction-day intraday V on Treasury futures: does the dealers' pre-auction concession and post-auction reversal (FRBNY Staff Report 1188) appear in ZT, ZF, ZN and UB at the magnitude the paper reports for cash, and if it does, is either leg a trade?

*2026-09-30. The design record only. Committed before the calendar builder and the runner exist (R8). The builder will
be `scripts/fetch_treasury_auctions.py` and the runner `scripts/stage0_d710_auction_v.py`, each committed separately
before its one run.*
- **What it is:** in-sample, 2010-06-07 → 2023-12-29 on `fut_day1m.parquet`. Nothing dated 2024-01-01 or later is read
  from any bar or price. No slice is spent. The vault (2025-03-01 → 2026-09-18) and D626's CL/NG sample stay sealed.
- **What it is not:** a premise check first. The trade (§8) runs only if the premise passes (§7). Nothing is admitted.
- **Filenames:** every path this line adds is at most 85 characters (`test_public_cut`).

## 1. The question

On a coupon auction day, do Treasury futures fall from 10:00 to the 13:00 competitive close and recover from 13:05 to
16:00, relative to the same clock on matched non-auction days, by at least half of what the paper's cash numbers imply
for each future? Per tenor, pooled in σ units, and per era (2010–2014 against 2015–2023).

## 2. Why, and the reopen

**The principal approved looking at it** (2026-09-30). The record's only earlier mention is
`docs/research/Prop-Firm-080926/13-documented-intraday-effects.md` row R11 (Lou, Yan & Zhang 2013), set aside there as
"a **multi-day** effect" for the personal book. SR 1188 moves the effect into a six-hour intraday window.

**D499 closed the hourly clock** on eight roots, ZN and ZB among them: 16 cells, none clearing the family bar or the
fee; ZN's cells netted −$4.73 to −$24.51 a trade (D499 RESULT §0). **The principal reopened it for this one use on
2026-09-30, in chat: "Reopen hourly clock for C".** The reopen is narrow:
- a hold of about three hours, tied to the Treasury's published auction schedule;
- not a price-path fade: the side is fixed by the calendar, not by the last hour's move;
- D499's own cells stay closed as it left them. This record is the reopen's only home; no addendum to D499 is written
  in this phase.

**The precedent to fear is D685–D687.** A published, mechanism-backed flow on the same roots (month-end rebalancing)
replicated and then faded: its response per unit of flow fell from −15.8 (2010–15) to −5.9 (2019–23) while the flow
grew, and ZB's leg (+8.6, t 2.09 in 2010–15) went flat (D687 §1). SR 1188 reports the same shape: the post-2015 V is
"less than half the earlier magnitudes" (p. 20). So the era split is part of the gate (§7), and 2019–2023 is reported
on its own.

**D640's lesson is carried as a placebo** (§6 N3): the LETF close flow passed at 14:30 and died because the same rule at
11:00 was also significant.

## 3. The mechanism and the paper's numbers, verified

**Source.** Fleming, Liu & Nguyen, "Intraday Price Pressure and Order Flow Around U.S. Treasury Auctions", FRBNY Staff
Report 1188, March 2026, revised July 2026, https://doi.org/10.59576/sr.1188. Page
https://www.newyorkfed.org/research/staff_reports/sr1188; PDF
https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr1188.pdf (77 pages, 3,844,475 bytes), both
fetched 2026-09-30T10:05:15Z. Page numbers below are the printed ones, with the PDF page in brackets.

**The mechanism (pp. 24–25 [26–27]).** Primary dealers sell ahead of the auction to make room for the supply they expect
to take down, and buy back after allocation. Net order flow on auction days is negative for three hours before the close
and positive after, different from control days at 5% and 1% (Figure 3). FOMC and payroll releases show no such flow and
no pre-event yield move (p. 25 [27]). Pressure rises with the MOVE index (+0.43 yield bp per 1 SD; the only proxy
significant jointly, pp. 30–31 [32–33]) and falls with the lagged investment-fund share of the auction (p. 32 [34]).

**The paper's windows (p. 18 [20], Table 3 note).** Pre = the 180 minutes to the minute before the competitive close.
Post = from the minute after the results release to 180 minutes later. Price pressure = post-return − pre-return, in bp,
from the log best-bid-ask mid on the on-the-run security. The results are robust to starting the post window 10 minutes
after the release (footnote 13, p. 19 [21]). Results have been released "just a few minutes" after the close for nearly
all auctions since late 2001 (p. 14 [16]).

**Table 3 (p. 48 [50]), price pressure in price bp, on-the-run cash:**

| | 2y | 3y | 5y | 7y | 10y | 30y |
|---|---:|---:|---:|---:|---:|---:|
| full 1991–2024 V | 1.336\*\*\* | 2.255\*\*\* | 4.615\*\*\* | 4.020\*\*\* | 9.905\*\*\* | 17.106\*\*\* |
| pre-auction return | −0.733\*\*\* | −1.134\*\*\* | −2.523\*\*\* | −1.204 | −3.822\*\*\* | −12.075\*\*\* |
| post-auction return | +0.603\*\* | +1.120\*\*\* | +2.107\*\*\* | +2.816\*\*\* | +6.084\*\*\* | +5.031 |
| **S2 2007–2014 V** | 1.852\*\*\* | 3.660\*\*\* | 6.518\*\*\* | 5.628\*\*\* | 15.222\*\*\* | 25.514\*\*\* |
| **S3 2015–2024 V** | 0.887\*\*\* | 1.216\*\* | 4.482\*\*\* | 2.509 | 5.165\* | 14.224\* |
| pre share of full V | 55% | 50% | 55% | 30% | 39% | 71% |

(Stars as printed: one \* p < .1, two < .05, three < .01; Newey-West SEs.)

**What the research agent quoted, checked:**
- **S3 magnitudes: correct** (0.89, 1.22, 4.48, 2.51, 5.17, 14.22 are Table 3 Panel B, S3, rounded).
- **Pre/post splits 10y 39/61, 5y 55/45, 7y 30/70: correct, but they are FULL-SAMPLE** (Table 3 Panel A). The paper
  reports no per-era split.
- **30y "~80/20": wrong. It is 71/29** (12.075 of 17.106). Its post-leg (+5.031) is not significant.
- **Two facts the quote left out:** S3's V is significant at 10% only for 10y and 30y and not at all for 7y; the
  post-2015 decline is formally significant only for 3y and 10y (F-tests, Table 2).

**Table 2 (p. 47 [49]), yield pressure in yield bp:** full 0.712 / 0.749 / 1.038 / 0.659 / 1.192 / 0.869; S3 0.419 /
0.340 / 0.919 / 0.417 / 0.593 / 0.592. **The 30y post-leg in yields is −0.235, not significant; the text calls it
"negligible" (p. 19 [21]).** Somogyi et al. (2026), cited on p. 6 [8], find post-auction appreciation in long-term
Treasuries disappears after 2010. **So the 30y trades the pre-leg only** (§8).

**Table 4 (p. 49 [51]), spillovers in yield bp, full sample** (the auctioned tenor in rows, the security in columns).
It sets the tenor-to-future mapping (§5):
- 3y auctions: 2y column 0.677\*\*\*, 3y 0.749\*\*\*, 5y 0.347 (not significant);
- 10y auctions: 7y column 0.796\*\*\*, 10y 1.192\*\*\*;
- 30y auctions: 30y 0.869\*\*\*, every other column below 0.40 and not significant.

**Control days (p. 15 [17]).** Same weekday one week before and one week after. A control that falls on an FOMC day, an
early close or "the auction of another note or bond" is replaced by the nearest preceding (following) clean day. On
control days the window yield changes are "not statistically different from zero" (p. 20 [22]; the paper calls these
unreported results).

**Not fetched:** Lou, Yan & Zhang (RFS 2013) is quoted only as SR 1188 reports it (yields +2–3 bp into the auction and
about −2 bp after, 1980–2008, p. 10 [12]). **Smales (2021) is not cited by SR 1188**, so it is outside this phase's
internet scope and is recorded as `not_fetched`.

## 4. Data, the calendar and the seals

**Bars: `data/fixtures/fut_day1m.parquet`** (1-minute, 09:00–15:59 ET, front month by volume from
`fut_breadth_hourly`, flags `same_front` and `present`). What I inspected, with no price column read and every query cut
to `day < 2024-01-01` and asserted (max day 2023-12-29):
- the meta's coverage per root;
- the per-year share of sessions holding the four anchor bars (09:59, 12:59, 13:04, 15:59);
- the median bars present in each window;
- roll and `present=False` counts;
- bar counts on 2020-02-20 → 2020-07-02.

| root | sessions 2011–2023 | meta `first_clean_year` | anchor bars present | median bars pre / post (of 180 / 175) |
|---|---|---|---|---|
| ZF | 252–259 a year | 2011 | 94–100% | 177–180 / 168–175 |
| ZN | 239–259 | 2011 | 96–100% | 180 / 174–175 |
| ZB | 244–259 | 2011 | 95–100% | 178–180 / 170–175 |
| UB | 244–259 | **2013** | 85–100% (2014: 85% at 13:04) | 170–180 / 158–175 |
| ZT | 252–259 | **2019** (slot fill 0.07–0.53 before 2018) | 76–100% before 2019, 93–100% after | 145–170 before 2019, 178–180 after / 138–174 |
| TN | none 2013–2015; 18 in 2012 | **2021** | 85–99% from 2016 | 167–180 / 149–175 |

**Three things the inspection found:**
- **The rate roots have no broken March-2020 session.** Every session in March 2020 holds at least 400 of 420 bars on
  all six roots. The broken sessions are **2020-02-27** (stops near 13:20; the Feb-2020 7-year auction was that day),
  **2020-06-30** (stops at 10:10) — both D589's archive dropouts — and **2020-02-28, 60 of 420 bars on all six roots with
  the last bar at 15:59: a hole, not an early stop. It is not in D589's list and is recorded here.**
- **ZT is thin at one minute before 2019.** Its bars are missing where no trade printed. Its events rest on last trades
  up to 5 minutes stale (§5).
- **ZF, ZN and ZB are usable from the fixture's first day (2010-06-07):** slot fill is 0.99–1.00 in 2010.

**The auction calendar (new; the principal approved the fetch).** Source: Fiscal Data "Treasury Securities Auctions
Data", keyless. One schema request was made:
`https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query?filter=auction_date:eq:2013-02-13&page[size]=3`,
2026-09-30T10:13:26Z, HTTP 200, 15,106 bytes, 1 record, 114 fields. The fields this study needs:

| field | type | example (10y, 2013-02-13) | use |
|---|---|---|---|
| `auction_date` | DATE | 2013-02-13 | the event day |
| `closing_time_comp` | STRING | `01:00 PM` | the competitive close, ET (the event clock) |
| `closing_time_noncomp` | STRING | `12:00 PM` | reported only |
| `security_type` / `security_term` / `original_security_term` | STRING | Note / 10-Year / 10-Year | tenor (a reopening's `security_term` is the remaining term, so the tenor is `original_security_term`) |
| `reopening` | STRING | No | reopenings included, flagged |
| `inflation_index_security` / `floating_rate` / `cash_management_bill_cmb` | STRING | No / No / No | TIPS, FRN, CMB flags |
| `primary_dealer_accepted` / `comp_accepted` | NUMBER | 11,436,760,000 / 23,960,836,000 | the takedown share (§8.4) |
| `direct_bidder_accepted` / `indirect_bidder_accepted` / `total_accepted` / `soma_accepted` | NUMBER | | reported |
| `offering_amt`, `high_yield`, `bid_to_cover_ratio`, `announcemt_date`, `cusip` | | 24,000,000,000; 2.0460 | high_yield sets the duration used in §5 |
| `pdf_filenm_announcemt` / `pdf_filenm_comp_results` | STRING | A_20130206_3.pdf / R_20130213_1.pdf | provenance, and the fallback for a missing close time |

**There is no results-release-time field.** The fixed 13:05 post-window start rests on the paper's "a few minutes"
(p. 14 [16]).

**FOMC days: a gap the brief did not know about.** D585's calendar (`data/calendar/events.csv`) and
`data/macro_release_calendar.json` both start in 2016-01; `cme_session_calendar`'s `fomc` flag is null before 2016
(data-available.md, D589 (iv)). **2010-06 → 2015-12 has no FOMC list on disk.** The source D585 used,
`federalreserve.gov/monetarypolicy/fomchistorical{year}.htm`, was outside the design phase's internet scope. **The
principal approved extending that fetch back to 2010 (§12, choice (a)).**

**Seals, asserted in code:**
- every bar row has `day < 2024-01-01`, filtered at read and asserted after;
- the auction calendar is fetched in full (a schedule, not a price) and cut to `auction_date < 2024-01-01` before any
  join, and the cut is asserted;
- the ρ inputs (the admitted MACD arm, F2) are built from inputs cut below 2024-01-01 (§9).

## 5. The event, the mapping and the windows

**An event** is one nominal fixed-rate coupon auction:
- `security_type` Note or Bond; not TIPS, not an FRN, not a CMB;
- `original_security_term` in {2, 3, 5, 7, 10, 20, 30}-Year, new issue or reopening;
- `closing_time_comp` = 01:00 PM.

**Excluded, on the event day and in every control pool:**
- an FOMC statement day (§12 for 2010–2015);
- a **shared day** (below);
- the mapped root's roll session (`same_front` False), a `present=False` session, an `is_early_close` session;
- D589's rejected sessions, 2020-02-28, and the Treasury-market dysfunction fortnight 2020-03-09 → 2020-03-20 (below);
- any event whose four anchor prices are not all in the same contract, within 5 minutes' staleness;
- the first 60 eligible sessions of each root, the σ burn-in.

Auctions that close at another time (11:30, 11:00) are not events. They are counted and listed.

**Shared days.** If two fixed-rate coupon auctions with duration (nominal or TIPS) fall on one day, the day is dropped,
both auctions and as a control.
- **Why drop and not keep the 13:00 auction:** the 11:30 auction's post-reversal lands inside the 13:00 auction's
  pre-window, and Table 4 shows 5-, 7- and 10-year pressure spilling across the whole curve. The contamination runs
  against the pre-leg, but it is not measurable per event.
- **Sensitivity:** the 13:00 auction on a shared day is reported as a sensitivity.
- **FRN-shared days are kept and flagged.** A floating-rate note has near-zero duration, so it creates no duration to
  hedge. Their count is reported.

**March 2020.** The brief asked to exclude "the broken March-2020 sessions". On the rate roots none is broken (§4).
The fortnight 2020-03-09 → 2020-03-20 is excluded instead, and declared now: the Treasury market was dysfunctional and
the Fed was the marginal buyer, which is not the dealer-inventory state the paper measures. It removes three auctions
(the 3y, 10y and 30y of 2020-03-10/11/12). They are reported as a sensitivity.

**The mapping.** CME deliverable baskets by remaining maturity: ZT 1y9m–2y, ZF ≥ 4y2m, ZN 6y6m–10y, TN 9y5m–10y,
ZB 15–25y, UB ≥ 25y. **These rules are from memory, not fetched:** cmegroup.com is outside scope and returns 403 to this
machine (D589 (viii)). The ratios below move by about ±7% for ±0.5 years of CTD maturity.

| tenor | future | role | why | sector factor (Table 4) | span |
|---|---|---|---|---:|---|
| 2y | **ZT** | primary | the 2y on-the-run is deliverable | 1.000 | 2010-06 → |
| 3y | **ZT** | primary | not deliverable anywhere; the pressure is at the short end (2y column 0.677\*\*\* vs 5y 0.347 ns) | 0.904 | 2010-06 → |
| 5y | **ZF** | primary | the 5y on-the-run is deliverable | 1.000 | 2010-06 → |
| 7y | **ZN** | primary | ZN's cheapest-to-deliver sits at 6.5–7y, the 7y sector | 1.000 | 2010-06 → |
| 10y | **ZN** | primary | the only 10y-sector future over the full span; ZN prices the 7y sector | 0.668 (0.796/1.192) | 2010-06 → |
| 10y | TN | secondary | TN's basket is the 10y sector | 1.000 | 2021-01 → (meta) |
| 30y | **UB** | primary | only UB's basket (≥ 25y) holds the 30y | 1.000 | 2013-01 → (meta) |
| 30y | ZB | secondary | the long-end spillover | n/a | 2010-06 → |
| 20y | **ZB**, not UB | secondary | a 20y bond (19y10m) is in ZB's 15–25y basket, not UB's | n/a (the paper excludes 20y) | 2020-05 → |

**The transfer ratio** T = sector factor × D(future) / D(cash on-the-run). D is the par modified duration
(1/y)(1 − (1 + y/2)^(−2n)). y is the auction's own `high_yield`. n is the tenor for cash, and the CTD's remaining
maturity for the future: ZT 1.9y, ZF 4.3y, ZN 6.6y, TN 9.6y, UB 25.5y, near each basket's short end. At y = 2.5%, and
barely moved from 1.5% to 4.5%:

| | 2y→ZT | 3y→ZT | 5y→ZF | 7y→ZN | 10y→ZN | 10y→TN | 30y→UB |
|---|---:|---:|---:|---:|---:|---:|---:|
| T at 2.5% | 0.951 | 0.580 | 0.867 | 0.947 | **0.459** | 0.965 | 0.893 |
| T at 1.5% / 4.5% | 0.951 / 0.952 | 0.577 / 0.586 | 0.864 / 0.873 | 0.946 / 0.951 | 0.452 / 0.473 | 0.963 / 0.968 | 0.877 / 0.921 |

**The windows** (a bar's close is the last trade before the next minute). Anchor prices are the closes of the 09:59,
12:59, 13:04 and 15:59 bars.
- pre r_pre = ln P(12:59) − ln P(09:59): 10:00:00 → 13:00:00, the paper's 180 minutes;
- post r_post = ln P(15:59) − ln P(13:04): 13:05:00 → 16:00:00, 175 minutes. It is flat through the close and the release;
  the paper runs from release + 1 minute to + 180 (§3), and the fixture ends at 16:00;
- V = r_post − r_pre, in bp (× 10⁴). The mechanism predicts r_pre < 0, r_post > 0, V > 0.

**The control** for each event: the paper's rule (§3), in the mapped root's eligible non-auction sessions. A day with any
coupon, TIPS or FRN auction at any clock is not a control; bills are ignored. V_c is computed at the same clock. The
difference is Δ = V_event − ½(V_before + V_after).

**σ units:** z = Δ / σ̂. σ̂ is the sd of V over the 60 most recent eligible non-auction sessions of that root strictly
before the event (ddof 1, at least 40 present, prior-only).

## 6. The premise statistic, its predictions and its nulls

**Statistics, all reported per tenor pair, per era (E1 2010-06 → 2014-12, E2 2015-01 → 2023-12, and 2019–2023 on its
own) and pooled:**
- mean Δ in price bp and mean z;
- r_pre and r_post separately, each against its control;
- raw event-day V and control-day V separately;
- the pooled mean z over the six primary pairs, events weighted equally;
- the expected z: for each event, E[z] = T × V_cash(tenor, era) / σ̂, with S2 for E1 and S3 for E2 (Table 3 Panel B);
- the achieved share: pooled mean z ÷ pooled mean E[z];
- **the SE:** Newey-West on the date-ordered series with the paper's lag ⌊4(T/100)^(2/9)⌋, and clustered by ISO week
  (2y/5y/7y share a week and their controls overlap). **The gate uses the larger.**

**Free predictions from the paper, fixed now:**

| # | prediction | source |
|---|---|---|
| F1 | pooled mean z > 0 | Tables 2–3 |
| F2 | pooled Δr_pre < 0 and Δr_post > 0; the 30y post-leg near 0 | Table 3; p. 19 [21] |
| F3 | **UB (30y) has the largest price-bp Δ of the six pairs** | Table 3: 30y largest in every era; T keeps it largest (§8.1) |
| F4 | E1 pooled z > E2 pooled z; per pair, E2/E1 in bp near the paper's S3/S2 ratio (0.33–0.69 in Table 3; the text's "less than half", p. 20 [22], is not true of 5y or 30y) | Table 3 |
| F5 | per-pair price-bp Δ near T × V_cash (the E2 expectations in §8.1) | §5 |
| F6 | the 11:00-centred placebo Δ ≤ 0 on auction days (§6 N3) | the mechanism: 09:05 → 12:59 is all pre-auction selling |
| F7 | Δ rises with the previous same-tenor auction's primary-dealer share (standardised, prior-only) | p. 32 [34], the non-dealer share lowers pressure |

**Nulls, each reported with p05, p50, p95 and the observed percentile:**
- **N1, the gate: exact enumeration of the event schedule over non-auction days.**
  - For each root, S_f is its ordered list of eligible non-auction sessions. Event e maps to position p_e: the first
    session in S_f after its date.
  - At offset j every event is moved to S_f[(p_e + j) mod |S_f|] and scored by the identical Δ rule and σ̂. Its
    controls are that day's own ±1-week clean days.
  - j runs over every offset with |j| ≥ 10 sessions: about 2,200. The p95's SE is exactly zero.
  - Tenor mix, event count, clock and control rule are held; only the auction link is broken.
- **N2, the ±1-week placebo:** pseudo-events on the week-before and week-after days, scored by the same Δ rule. Their
  controls are drawn from clean non-auction days, so the auction day is never a control. The pooled z and its t are
  reported.
  - **Reading:** t ≥ 2 with the same sign means an auction-WEEK pattern, Lou et al.'s multi-day cycle, not the
    intraday dealer V. Reported, not a kill.
  - Also reported: the raw control-day V against zero; the paper found no V there.
- **N3, the 11:00-centred placebo V (D640):** on the same auction days, pre = 09:05 → 11:00 and post = 11:05 → 13:00
  (the closes of the 09:04, 10:59, 11:04 and 12:59 bars), with the same controls.
  - **KILL** if its pooled Δ z is at least half the 13:00 statistic with t ≥ 2: a V that also appears at 11:00 is not
    centred on the auction close.
- **N4, the week-clustered sign flip:** each ISO week's events flip sign together. 100,000 draws, seed 710. The p95
  carries its bootstrap SE, and a margin within 2 SE is UNRESOLVED (D373).

## 7. The premise gates and the kill (fixed now)

**PRESENT** needs all five:
- **G1, exists:** pooled mean z > 0 with t ≥ 2 (the larger SE), on the full span.
- **G2, above its null:** pooled mean z above N1's p95.
- **G3, magnitude:** the achieved share ≥ 0.5 on the full span, against the transfer-adjusted expectation.
- **G4, the recent era carries it:** the achieved share ≥ 0.5 on E2 alone. This is the D685 guard: a V that lives only
  before 2015 is not a trade now.
- **G5, centred on the close:** N3 does not fire.

**The outcomes:**
- **ABSENT:** G1 or G2 fails, or N3 fires. **STOP.** Stage 2 does not run.
- **BELOW HALF:** G1 and G2 pass, but G3 or G4 fails. **STOP.** Stage 2 does not run. The record says which era.
- **PRESENT:** stage 2 runs.

Per the brief, the study goes no further on a STOP. Under R15 the avenue's closure is the principal's; the record states
what the construction showed.

**Reported, not gated:** each pair's Δ with t, F1–F7 each marked held or missed, the three sensitivities (shared-day
13:00 auctions, March 2020, ZT from 2019 only), and the secondary pairs.

**The brief's literal reading (T = 1, the raw cash price bp as the bar) is reported beside G3 and G4.** It is not the
gate, because it would fail ZN on 10y auctions by construction: ZN's expected share of the cash 10y V is 0.459 (§5).

## 8. Stage 2, declared now, run only on PRESENT: the two-leg trade

### 8.1 Size the prize (paper numbers only; no bar read)

Expected futures legs, in price bp, are T × V_cash(era) × the full-sample pre/post share. The dollars use indicative
2015–2023 prices; the runner uses each event's own price. The cost is `data/futures_costs.json`
`roots.<R>.full.runner_lines.d556_min_size`, verified: $6 commission + one tick.
- ZT and ZF $13.8125;
- ZN and TN $21.625;
- UB and ZB $37.25;
- 2c = twice the round trip.

| era | pair | E[V] bp | pre bp / $ | post bp / $ | cost / 2c | clears 2c |
|---|---|---:|---|---|---|---|
| E2 | 2y→ZT ($21.6/bp) | 0.84 | 0.46 / 10.0 | 0.38 / 8.2 | 13.81 / 27.63 | neither |
| E2 | 3y→ZT | 0.71 | 0.35 / 7.7 | 0.35 / 7.6 | 13.81 / 27.63 | neither |
| E2 | 5y→ZF ($11.8/bp) | 3.89 | 2.12 / 25.0 | 1.77 / 20.9 | 13.81 / 27.63 | neither (both clear 1c) |
| E2 | 7y→ZN ($12.7/bp) | 2.38 | 0.71 / 9.0 | 1.67 / 21.1 | 21.63 / 43.25 | neither |
| E2 | 10y→ZN | 2.37 | 0.91 / 11.6 | 1.46 / 18.5 | 21.63 / 43.25 | neither |
| E2 | 10y→TN ($13.5/bp) | 4.98 | 1.92 / 26.0 | 3.06 / 41.3 | 21.63 / 43.25 | neither (post near) |
| E2 | **30y→UB ($18.0/bp)** | 12.70 | **8.97 / 161.4** | 3.74 / 67.3 (not traded) | 37.25 / 74.50 | **pre-leg** |
| E1 | 5y→ZF | 5.65 | 3.08 / 36.4 | 2.57 / 30.4 | 13.81 / 27.63 | both |
| E1 | 7y→ZN | 5.33 | 1.60 / 20.3 | 3.74 / 47.4 | 21.63 / 43.25 | post |
| E1 | 10y→ZN | 6.99 | 2.70 / 34.2 | 4.29 / 54.5 | 21.63 / 43.25 | post |
| E1 | 30y→UB | 22.79 | 16.09 / 289.5 | 6.70 / 120.6 | 37.25 / 74.50 | pre-leg |

(E1 2y→ZT and 3y→ZT: legs $17–23, below 2c.) **On the paper's own numbers, in the recent era only the 30-year pre-leg
is worth trading.**

**In-sample power, if the effect is entirely real.** The paper gives stars, not SDs, so the effect per event is bounded
as d = t/√N, with N ≈ 115 auctions per tenor in S3 (2015-01 → 2024-07).
- **S3 bounds:** d ≥ 0.240 for 2y and 5y; 0.183–0.240 for 3y; 0.153–0.183 for 10y and 30y; < 0.153 for 7y.
- **The transfer to futures:** each d is multiplied by the sector factor.
- **The event count:** about 97 events a pair in E2 and 50 in E1 (UB 22), after an assumed 10% exclusion.

| object | expected t, low / mid bound |
|---|---|
| **premise pooled, E2** | **2.96 / 3.75** |
| premise pooled, E1 (S2, every tenor three-star) | ≥ 3.48 |
| premise pooled, full span | ≥ 4.57 |
| a single pair, E2 | 0.0–1.93 / 0.9–2.25 (7y and 10y→ZN the weakest) |
| **the UB pre-leg alone, gross, E2** | **1.51 / 1.80** |
| UB pre-leg, net Sharpe by trade count (11 a year) | 0.39 / 0.47 |
| the 2024-01 → 2026-09 slice: the premise pooled | 1.62 / 2.05 |
| the 2024-01 → 2026-09 slice: the UB pre-leg alone (about 30 auctions) | 0.83 / 0.99 |

**What it means:**
- The premise is testable in-sample and marginally confirmable forward.
- **No single leg is confirmable on the unseen slice even if real.** A trade that passes here would need a pooled-book
  confirmation design, not a leg-by-leg one.
- The expected component Sharpe (≈ 0.4–0.5) sits at C-a's bar, not above it.

### 8.2 The legs

- **Pre-leg (short):** sell at the close of the 10:00 bar (10:01:00); buy back at the close of the 12:58 bar (12:59:00),
  flat before the competitive close.
- **Post-leg (long):** buy at the close of the 13:05 bar (13:06:00); sell at the close of the 15:59 bar (16:00:00).
- **Fills and cost:** each entry fills one minute inside the premise window, and every leg pays the full d556 round trip.
- **Size and the 30y:** one full contract. No Treasury micro is in the cost table or the fixture; CME's micro yield
  futures are a different, cash-settled contract. **The 30y trades the pre-leg only** (§3). Its post-leg is reported as
  a diagnostic.
- **Hurdle P2:** every leg is flat by 16:00, inside MFFU's 16:10 flatten.
- **The delivery ruling:** the traded contract must be before its first position day (two business days before the last
  business day of the month before delivery). This is asserted on every leg. The volume-elected front never breaks it,
  and the assertion makes sure.

### 8.3 The books and their gates

**Book U, unfiltered:** every primary leg of every event, eleven tenor-legs.
- **Gate 1, the mechanism (gross; R15, D666):** mean gross per trade > 0 with NW t ≥ 2, and above the p95 of N1 applied
  to the leg schedule (the same exact enumeration).

**Book F, the expected-profit filter** (k = 2, the D649 template). Trade a leg only when its projected gross is at least
2 × its round trip.
- **The projection:** T × V_cash(tenor, era) × pre/post share × the event's $ per bp. $ per bp = the 09:59 price ×
  usd_per_point × 10⁻⁴, known before the entry.
- **Why the paper supplies the pass-through, not our own earlier trades:** a per-leg expanding mean over 24 events has an
  SE of about 0.2σ against an effect near 0.15σ. That is D693's noise-dominated cell (memory: before a per-cell filter,
  compare its differences with the noise).
- **Disclosure:** S3's cash estimate overlaps 2015–2023. The projection is a prior for forward use, not out-of-sample
  here.
- **Its scope:** it mostly selects the UB pre-leg (§8.1).
- **Gate 2, net:** mean net per trade > 0 with NW t ≥ 2. Fewer than 60 trades is UNRESOLVED.
- **The oracle first (D690):** `validation/filter_oracle.py` gives the oracle take (net > 0), the partial-oracle curve,
  and the filter's calibration slope, which must be > 0.

**The verdict (D666):** SUPPORTED (Gates 1 and 2), MECHANISM ONLY (Gate 1 alone), NOT SUPPORTED. **No leg or tenor is
chosen after the run. The filter is the only selection device, and it was fixed before the run.**

**Two lenses:** events never overlap in time (one per day after the shared-day rule), so the per-trade lens and the daily
book differ only in how two legs on one day aggregate. Both are reported, never on the same statistic.

### 8.4 The declared secondary: the post-leg confirmation

The research agent's rule. Take the post-leg only if both hold:
- the pre-leg's concession printed (r_pre < 0 that day);
- the primary-dealer share is at or above its trailing median over the 12 previous auctions of the same tenor, strictly
  earlier.

The PD share is `primary_dealer_accepted / comp_accepted`, public at the results release, before the 13:06 fill. Scored
beside Book U's post-legs, with its own N1. Not a gate.

### 8.5 The four reporting groups (CLAUDE.md), for Books U and F, per leg and per era

1. **Performance, net and gross side by side:**
   - trades a year and exposure (held minutes ÷ session minutes);
   - mean $ a trade with NW t;
   - daily Sharpe and Sortino (every trading day, √252) and the trade-count-annualised Sharpe;
   - vol and maxDD in $;
   - mean move a trade against 2c;
   - breakeven round trip in $ and in ticks.
   - **The cost context:** D507's quoted spreads for these roots (1.00–1.02 ticks, 2025–26) are stated, and so is the
     window caveat: a tick is cheaper in bp at the older, higher prices. The runner measures each year's minimum price
     increment per root. Where it differs from today's tick (ZT's tick history is not verified here), a measured-tick
     cost line is reported beside d556. Corwin-Schultz is not used; it is a range model that overstates about tenfold
     here (memory).
2. **The trade distribution:** count, mean, **median**, hit rate, payoff, the fixed hold, skew, kurtosis, and the 1%
   trims: ex-top, ex-bottom, trimmed.
3. **What the winners depend on:**
   - by year and era, and 2019–2023;
   - by tenor-leg;
   - new issue against reopening;
   - the auction in the month's last five trading days or not (the D685 overlap: the 2y/5y/7y cycle sits in month-end
     week);
   - CPI or payroll day (D494's gates);
   - the price tercile ($ per bp scales with price);
   - without 2020 and without 2022;
   - the top 1, 5 and 10 trades' share, the five largest trades named, and profitable years.
4. **Nulls:** N1 on the leg schedule (p05, p50, p95, percentile); N4; and the always-on control: the same legs at the same
   clock on the matched control days.

## 9. The component line (in the RESULT whether or not anything passes, once stage 2 runs)

For Book F and for Book U:
- **The standard's window, 2016-01-04 → 2023-12-29:** net Sharpe (SE, monthly block bootstrap) and Sortino, full
  contracts at d556 cost, computed by the runner in $;
- hit rate, skew, gross beside net, daily σ against C-d ($500);
- **ρ of the daily P&L with #2, the admitted MACD arm** (`BOOK_PROP.md`, `COMPONENTS_PROP.md` Entry #2, NQ hourly day
  session) over 2016–2023;
- **ρ with #4, F2 PROVISIONAL** (ES 15:30 → 16:00) over its own window, 2018-05-14 → 2023-12-29. K8 and the NG spread
  are closed or removed and are not live.

**The ρ inputs honour the seal.**
- **The arm:** its daily net is built through D504's path (`d674_resize_macd_arm.arm_daily`). The fixture frame is cut
  below 2024-01-01 before `D504.build`. Its 2016–2023 per-year totals must equal `data/d504_arm_full_history.json`
  `per_year` to the cent. If they do not, the runner raises and says the arm's build reads ahead.
- **F2:** built through D705's own functions on inputs cut below 2024-01-01. It must reproduce 252 trades and
  +$13.208968 a trade (`data/vault_d707_power.json`).

**Two constructions that share neither clock nor instrument diversify** (CLAUDE.md, the books, point 4): a rates future
on an auction clock against an NQ hourly MACD and an ES last half-hour. ρ is reported, not assumed.

## 10. The declared readings, in one place

| outcome | reading | what follows (a proposal for the principal) |
|---|---|---|
| ABSENT | the dealer V does not reach the futures bars at the auction clock | stop; the cash effect may live in the on-the-run basis rather than the futures |
| BELOW HALF (G3) | the V is in the futures, at under half the transfer-adjusted size | stop |
| BELOW HALF (G4 only) | real before 2015, faded since: D685's shape | stop; the E1/E2 numbers go on record beside D687 |
| PRESENT, then NOT SUPPORTED | the V is real and no leg carries it gross | stop |
| PRESENT, MECHANISM ONLY | gross passes, the filtered book does not clear net | R12: screen the personal track (TLT/EDV-type ETFs at about 3.8 bp a round trip) before any closure on cost |
| PRESENT, SUPPORTED | an in-sample pass | a separate confirmation design (§8.1: no single leg is confirmable forward) |

**Nothing is tuned after the run:** not the windows, the mapping, T, the CTD maturities, the controls, the exclusions,
the filter's k or the gates. Any change is a new design.

## 11. The runner and the calendar builder

### `scripts/fetch_treasury_auctions.py`

Stdlib only, in D585's pattern (`fetch_release_calendar.py`: cache the raw, commit the derived, a builder that refuses a
row it cannot source).
- **`--probe`:** one request; prints the fields and the total count. (Done by hand for this record: §4.)
- **`--fetch`:** `auctions_query` with `filter=security_type:in:(Note,Bond),auction_date:gte:2009-01-01`,
  `page[size]=10000`, paginated.
  - Raw JSON goes to `data/raw/treasury_auctions/` (gitignored cache, not temp), with `_manifest.json`: url,
    accessed_utc, HTTP status, bytes, sha256.
  - One second between requests; D585's User-Agent; resumable.
- **`--build`:** writes `data/calendar/treasury_auctions.csv` and `.meta.json`.
  - **One row a coupon auction:** auction_date; closing_time_comp parsed to HH:MM ET, with the ET and UTC datetimes;
    tenor from `original_security_term`; the flags; the §4 amounts; high_yield; the PD share; `source_url`;
    `method=fetched`; `accessed_utc`.
  - **A null or unparseable close time** is recovered only from the announcement PDF on TreasuryDirect
    (`pdf_filenm_announcemt`), with `method=fetched_pdf`. **Never assumed to be 13:00;** otherwise the row goes to
    `not_sourced` and is not an event.
- **The gates, each proven to RAISE by `--selftest`:**
  - **G1:** every row has `source_url`, `accessed_utc` and a method in {fetched, fetched_pdf}.
  - **G2:** per-year counts per nominal tenor are 12 from 2010, and the 20y is 0 before 2020-05. A short year must be
    named in the meta with a reason.
  - **G3:** every coupon close parses. Anything other than 13:00, 11:30 or 11:00 is listed.
  - **G4:** no duplicate (cusip, auction_date).
  - **G5:** shared days are listed by type (nominal–nominal, nominal–TIPS, nominal–FRN).
  - **G6:** an unknown `original_security_term` raises.
  - **G7:** the PD share lies in [0, 1] with comp_accepted > 0.
  - **G8, the second source:** 24 random auctions are cross-checked against TreasuryDirect's own securities API: date,
    close time, offering amount, PD accepted. Disagreements are listed, never overwritten.

**Not in this builder:** FOMC 2010–2015. It is D585's own fetcher, extended back to 2010 on the principal's choice (a)
(§12). The extension must reproduce D585's 2016–2023 dates exactly before its earlier years are used.

### `scripts/stage0_d710_auction_v.py` (`--selftest`, `--run`, `--data-root` as in D700)

**Output:** `data/stage0_d710_auction_v.json`, and `data/d710_events.csv.gz` (one row per event and control: no row
dated 2024 or later).

**Speed, designed in:**
- the six roots load through `parallel_map` (threads: pyarrow and numpy release the GIL), with a proof that the
  threaded load equals the serial one bit for bit;
- V, Δ and σ̂ are per-session arrays computed once;
- N1 is one axis-wise gather over (offset × event), proven equal bit for bit to the plain loop it replaces, probed on a
  tie-heavy synthetic input;
- stage 2 reuses the same arrays.
- **Projected wall time: under 3 minutes**, of which the arm and F2 rebuilds are most. `fast_null.NullContext` does not
  apply (it is a per-name panel null). Its principle is kept: offset 0 of N1 must reproduce the observed statistic
  exactly.

**The assertions (CLAUDE.md), each shown to RAISE in `--selftest` on a deliberately broken book:**
- **Lag audit, a second implementation:** a plain Python loop over events, reading bars through a dict keyed on
  (root, day, bar) and never calling the vectorised functions. It re-derives every event's eligibility, controls, anchor
  prices, Δ and legs, and must match the trade list exactly.
  - **Broken book 1:** a post-window that starts at 13:00, straddling the release.
  - **Broken book 2:** a pre-leg exit read after 13:00.
  - **Broken book 3:** a trailing PD-share median that includes the current auction.
  - **Broken book 4:** a σ̂ that includes the event day.
- **Sign audit, in money:** a short pre-leg over a falling price pays positively, and a long post-leg over a rising one
  pays positively. On a synthetic V both legs earn; on the inverted path both lose. $ = Δpoints × usd_per_point (ZT
  $2,000, the others $1,000). A flipped leg raises.
- **Right quantity:**
  - the 13:05 post return differs from the 13:00 one on the real data (the release jump exists and is excluded);
  - Δ differs from the raw event-day V (controls were subtracted);
  - no control is an auction day, an FOMC day or a roll session;
  - every window is inside one contract;
  - T is recomputed from its formula at three yields and matches the table in §5.
- **Window guard:** a 2024-dated bar or calendar row injected into the self-test's input raises.
- **The self-test's known answers:**
  - synthetic bars with a planted V of known size on the event days: G1–G4 PASS, and the recovered mean lies within
    2 SE of the plant;
  - the same bars with no plant: G1 fails (|t| < 2), and N1's p50 is within 2 SE of zero;
  - an FOMC day left in the events raises.

## 12. Decisions I made that the proposal did not fix, and what could make the study infeasible

**Decisions:**
1. **20y → ZB, not UB.** A 20-year bond is in ZB's 15–25y basket; UB needs ≥ 25y remaining. Secondary only: the paper
   has no 20y.
2. **3y → ZT, not ZF.** Table 4 puts the 3y pressure at the short end.
3. **10y → ZN primary** (the full span), **TN secondary from 2021** (meta clean year; 36 auctions at most, underpowered).
4. **The magnitude bar is transfer-adjusted** (duration × Table 4 sector factor). The brief's literal cash-price-bp bar
   is reported beside it; it would fail ZN on 10y auctions by construction.
5. **Post window 13:05 → 16:00 (175 minutes)** against the paper's release + 1 → + 180; the fixture ends at 16:00.
6. **Controls by the paper's own rule,** including "no auction of another note or bond" (TIPS and FRN included).
7. **Shared days dropped** (nominal or TIPS pairs). FRN-shared days kept and flagged.
8. **Only 13:00 closes are events;** 11:30 and early closes are counted, not measured.
9. **March 2020:** no rate-root session is broken there, so the dysfunction fortnight 2020-03-09 → 03-20 is excluded
   instead, and 2020-02-27, 2020-02-28 (newly found) and 2020-06-30 fall to the staleness rule.
10. **σ units from the prior 60 non-auction sessions' V,** so the pooled statistic weights tenors by their own noise.
11. **Spans:** ZF, ZN and ZB from 2010-06-07; UB from 2013; ZT from 2010-06 on ≤ 5-minute-stale prices, with a 2019+
    sensitivity.
12. **The gate needs the recent era (G4),** because of D685.
13. **The 11:00 placebo is a kill,** because of D640.
14. **Stage 2 runs only on PRESENT.** Per the brief, a STOP goes no further; R15 leaves the closure to the principal.
15. **The expected-profit filter takes its pass-through from the paper,** not from our earlier trades (the D693 noise
    argument).
16. **The 30y post-leg is not traded:** the paper calls it negligible, and Somogyi et al. find it gone after 2010.
17. **Stage-2 fills sit one minute inside the windows,** and the pre-leg is flat at 12:59:00.
18. **A delivery-window assertion on every leg** (the principal's standing ruling names ZN and ZB).
19. **Month-end and CPI/payroll splits are reported** (D685, D494). The 10:00 releases (ISM and the like) stay in both
    event and control windows, as in the paper.
20. **The gate's SE is the larger of NW and week-clustered.**

**What could make it infeasible, or weaker than the brief assumed:**
- **FOMC 2010-06 → 2015-12 is not on disk,** and its source (federalreserve.gov, D585's) is outside this phase's
  internet scope. **The principal chose (a) on 2026-09-30 ("Fetch them").** D585's FOMC fetch is extended back to 2010
  (the `fomchistorical` pages, the same parser, cached under `data/raw/`). FOMC days are excluded from events and
  controls over the whole span, 2010-06 → 2023-12. The options were:
  - **(a)** approve extending D585's FOMC fetch back to 2010: six `fomchistorical` pages plus the statements, the same
    parser;
  - **(b)** run E1 without the FOMC exclusion, disclosed (the paper itself excludes FOMC days only from controls);
  - **(c)** drop 2010–2015. The span becomes 2016–2023, **E1 disappears, G4 and F4 cannot be tested, and the premise's
    expected t falls to about 2.8** (E2's 2.96 over 8 of its 9 years).
- **Per-pair power is low.** In E2 no single pair's expected t exceeds about 2.25 even if real, so the gate is pooled by
  necessity. The UB pre-leg, the only leg the paper's numbers say is worth trading now, has an expected gross t of
  1.5–1.8 in E2 and 0.8–1.0 on the unseen slice.
- **ZT before 2019** rests on sparse one-minute trades.
- **TN** has too few clean years to say anything on its own.
- **The CTD maturities and basket rules are from memory,** not fetched. The ratios move about ±7% per half-year of CTD
  maturity.
- **No release-time field exists.** A release later than 13:05 would put the post-leg's entry before the information,
  which is conservative for the statistic but not for the PD-share secondary. The paper says release has come within a
  few minutes since 2001.

## Amendment A1 (2026-09-30, before the run)

*Written after the calendar builders ran and the runner was written, before `--run`. No Treasury bar price has been
read: the builders read only the Fiscal Data, TreasuryDirect and federalreserve.gov responses. The runner has run only
its synthetic `--selftest` and `--components-only` (the arm and F2; no Treasury bar loaded). The coordinator relayed
the rulings on points 1–3 below.*

**1. The delivery window (a correction to §8.2 and decision 18).**
- **The design said the volume-elected front never breaks the delivery rule. It is wrong on this fixture.** The front
  rolls ON first notice day, for example ZNU0 → ZNZ0 on 2010-08-31. So a late-month auction in Feb, May, Aug or Nov can
  fall on or after the held contract's first position day: the second-to-last session of the month before delivery,
  from the root's own session list.
- **The handling, accepted:**
  - premise events on those days are KEPT and counted (a measurement, not a position);
  - stage-2 legs on those days are EXCLUDED;
  - the assertion covers traded legs only: no traded leg sits inside its contract's delivery window.

**2. The control-day rule (making §5 precise), accepted.**
- The week-before control is the last clean non-auction session on or before d − 7. The week-after control is the first
  on or after d + 7.
- Each must lie within 14 calendar days of its target.
- An event missing either control is dropped and counted. The events of late December 2023 lose their week-after
  control to the seal.

**3. The leg-level N1 (making §8.3 precise), accepted.**
- It uses the same enumeration as the premise's N1.
- A pseudo day's leg is scored only where its fill prices exist (a mean over the available days), and the range of the
  per-offset count is reported.

**4. What an auction's tenor is: the term it was SOLD as.**
- A routine reopening carries its remaining term ("9-Year 10-Month"), so its tenor is the original term.
- But Treasury has met a standard auction by reopening an older issue. There, `security_term` is itself a whole
  standard term that differs from the original. Examples: 2015-05-26 "2-Year" on a 5-year CUSIP; 2019-11-05 "3-Year"
  on a 10-year CUSIP; 2013-08-28 "5-Year" on a 7-year CUSIP.
- **19 rows (2013–2026)** are those auctions, and their tenor is `security_term`. Without this rule, the builder's
  12-a-year gate (G2) fails in 11 tenor-years.
- **Five small-value contingency auctions of $25m** (2019-06-21 10y, 2019-12-06 2y, 2020-07-10 5y, 2021-12-02 20y,
  2022-07-14 2y) are flagged and are not supply events. They are not counted, not events, not shared days and not
  control exclusions. SR 1188 excludes the 2019 one (footnote 10).

**5. The FOMC extension's form.**
- `scripts/fetch_fomc_2010_2015.py` imports D585's fetcher unmodified. It writes a SEPARATE file,
  `data/calendar/fomc_2010_2015.csv`, which the runner merges with `events.csv`'s FOMC and FOMC_UNSCHEDULED dates at
  read. D585's committed outputs are unchanged.
- **Before any 2010–2015 row is used, the builder reproduces D585's 2016–2023 FOMC rows exactly,** 69 rows and every
  column, three ways:
  - D585's own builder over its own cache;
  - the same builder with the extension parser in place of D585's;
  - the extension's date builder on D585's 2016–2020 pages.
- **Why the extension needed its own parser:** the 2010 pages use an older layout with legacy statement links (the
  canonical URL is fetched and cited), and 2010–2012 carry "Conference Call" and month-spanning headings that D585's
  parser refuses.
- **No clock:** every 2010–2015 statement page reads "For immediate release" and states no time. The extension
  therefore writes the sourced DATE with an empty clock, and each page's own dateline is checked. D710 excludes whole
  sessions, so the date suffices.
- **The result:** 8 scheduled statements a year for 2010–2015, plus one unscheduled (2010-05-09). Five meetings issued
  no statement and have no row.

**6. The calendar's actual counts.** `data/calendar/treasury_auctions.csv` holds 1,716 Note and Bond auctions,
2009-01-06 → 2026-09-24, all fetched, none `not_sourced`.
- **Close times:** 13:00 on 1,501; 11:30 on 211; 11:00 on 3; 10:00 on 1.
- **G8:** TreasuryDirect agrees on date and close time for 24 of 24 sampled auctions, with no amount disagreement.

Shared days in the study span (2010-06-07 → 2023-12-29):

| type | days |
|---|---:|
| nominal + nominal (mostly 2y 11:30 with 5y 13:00, and 3y 11:30 with 10y 13:00, from 2016) | 36 |
| nominal + TIPS | 1 |
| FRN + nominal (kept and flagged) | 102 |
| FRN + nominal + TIPS | 1 |
| FRN + TIPS | 1 |

Primary pairs in the span, calendar level only (before the session exclusions: roll, early close, anchors, σ burn-in,
controls):

| pair | auctions | 13:00 closes | shared at 13:00 | kept after shared, FOMC and root span |
|---|---:|---:|---:|---:|
| 2y → ZT | 163 | 144 | 0 | 143 |
| 3y → ZT | 163 | 148 | 1 | 145 |
| 5y → ZF | 163 | 156 | 18 | 130 |
| 7y → ZN | 163 | 155 | 4 | 146 |
| 10y → ZN | 163 | 162 | 16 | 144 |
| 30y → UB (from 2013) | 163 | 162 | 0 | 132 |
| **total** | | | **39** | **840** |

- The shared-day rule drops 39 events at 13:00, more than §5 assumed.
- The FOMC coincidences, before any other rule, are: 2y 1, 3y 2, 5y 12, 7y 5, 10y 3, 30y 1.
- The 2012-09-13 30y was moved to 11:30 on an FOMC day. It is not an event.

**7. The run environment.** The run is made from THIS worktree, so no output lands in the shared main checkout's
working tree:

`uv run --with pyarrow python scripts/stage0_d710_auction_v.py --run --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"`

- Fixtures are read from the data root, and the component builders' fixture paths are pointed there (D709's
  `load_components` move).
- Outputs go to the worktree's `data/`.
- `--components-only` (run 2026-09-30) reproduced both components' known answers from inputs cut below 2024-01-01:
  - **the arm's 2016–2023 per-year totals equal D504's to the cent:** −140.05, −316.07, +751.91, −757.04, +8,743.93,
    +1,815.40, +5,624.93, −299.59;
  - **F2 is 252 trades at +$13.208968 a trade.**

**8. The N1 calibration check.** On 400 synthetic no-effect datasets, N1's p95 was beaten on 26 (6.5%). That is inside
the 99% binomial band of 10–32 at the nominal 5%. G1 fired on 11 of the 400 (2.8%). The synthetic data carries slow
volatility regimes and 30% noisier mid-week sessions, the nuisance a rotation null could mishandle.
