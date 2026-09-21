# D583 STAGE 0 DESIGN — **basis momentum's M7: is the basis-momentum book stronger into the quarter-end and year-end reporting dates, when regulatory snapshots shrink the dealer balance sheets the mechanism says are its loop gain?** A mechanism test on the seen in-sample book against the construction's own placement nulls — 63 session offsets within the quarter and the 495 four-month subsets of the year — with the year-end ordering and the year count declared; no reserved session read and no construction follows

**Stage 0 design, committed before the runner exists. Diagnostic on 2011-07 → 2023-12-29; no
session from 2024-01-01 on is read (that slice is spent for this line, D574); no cost, no book
beyond the one D564 already scored.** Nothing admitted (R15). Whatever the verdict, no
construction follows from it: the basis-momentum line has no unread slice on these roots, so
this record buys knowledge of the mechanism, not a component.

*2026-09-21. `BASIS_MOMENTUM.md` §2 says the commodity curve clears maturity by maturity through
an arbitrage loop whose gain is intermediary balance-sheet capacity; basis momentum measures how
long a disturbance has been failing to dissipate. Its §3 lists seven implications of that
mechanism, each with a direction to be pre-registered before looking; M6 was run inside D564 (P-4)
and held. **M7 (§4.2), the one the file ranks second only to the canonical capital-ratio series
and calls "the highest-value derivative of the mechanism"**: G-SIB and leverage-ratio reporting
are snapshot-based, so dealers shrink balance sheets into quarter-ends and re-expand after; loop
gain drops into the reporting date; disturbances persist longer; **basis momentum is stronger
around those dates, and year-end more than quarter-end.** It costs nothing, the calendar is
public, and the direction and ordering are both written here before any number is read. The
D578 lesson is carried: the effect is read by year and by era, and its count of years is a
declared bar. The D580 lesson is carried: the window is a hypothesis about the effect's
duration, the profile is reported at session resolution, and the placements that overlap the
window are named.*

**What is on disk.** The settlement strip (D556) and the breadth fixture (D555) for the 17
commodity roots, 2010-06 → 2023-12-29 in sample; the D564 machinery that builds the nearby
series, the BM(11,0) signal, the High4/Low4 membership and the equal-weight book; D564's
artifact with the primary cell's gross Sharpe as the harness target (D574 rebuilt it to 1e-9).

---

## 1. The quantities

- **The book.** D564's primary cell — EW High4/Low4, published rule, under the formation
  amendment D574 carried forward (`FFILL_FORMATION = 5`) — rebuilt by the same functions:
  `nearby_series`, `signals_at_month_ends`, `membership_fixed`, `hold_from_month_ends`,
  `book_return`. Its daily gross return `r_t` (a fraction; reported in bp/day) on the LONG window
  from the first month-end with ≥ 12 eligible roots (2011-07) to 2023-12-29, PRIMARY 2016–2023
  beside. **Harness before any calendar statistic:** the PRIMARY-window gross Sharpe of `r_t`
  must equal D564's artifact for that cell to 1e-9, as D574's did.
- **The calendar.** The reporting dates are the last session of March, June, September and
  December — the quarterly regulatory snapshots; the December one is the year-end. Over 2011-07
  → 2023-12 that is **50 quarter-ends, of which 12 are year-ends**: the sample is in quarters,
  and the record says so before reading anything ([[slow-conditioners-have-n-eff-in-years]]).
  The **PRE window** is the 10 sessions ending at the quarter-end session inclusive (the run
  into the snapshot, when the shrinkage happens); the **POST window** the 5 sessions after (the
  re-expansion; reported, no prediction). The width is a hypothesis about the effect's duration;
  the profile is read at session resolution regardless.
- **The disturbance.** Per root and month, `d_m = R1_m − R2_m`, the front-nearby monthly
  return less the second-nearby's — the monthly increment of the very quantity the signal
  cumulates (D564's `R1`, `R2`).

## 2. The tests, with predictions

| # | test | statistic | predicted | falsifier |
|---|---|---|---|---|
| **T1 — the run into the snapshot** (M7) | `ΔPRE = mean r_t on PRE sessions − mean r_t on all other sessions`, bp/day, with a **quarter-block bootstrap SE**; against **the construction's own placement null: the 10-session window shifted by k sessions relative to every quarter-end, k = −31 … +31 within the quarter, 63 placements enumerated (SE 0)**, offset 0 the reporting calendar | **ΔPRE > 0, rank ≥ 0.95** in the 63 placements; the 19 placements within 9 sessions overlap the window and are named, the rank among the 44 non-overlapping reported beside; the session profile −30 … +15 peaks inside PRE | ΔPRE ≤ 0 or inside the null → the reporting calendar does not order the book; M7 fails |
| **T1b — quarter-ends against the other month-ends** | the same ΔPRE with the PRE window at the **other eight month-ends** as the comparison: `ΔQ = mean r_t on quarter-end PRE − mean r_t on non-quarter month-end PRE`; the null is the **495 four-month subsets of the twelve months**, enumerated, {3, 6, 9, 12} the observed | **ΔQ > 0, rank ≥ 0.95** among the 495 (top 25) | the quarter-ends are no better than any four month-ends → what T1 found is a month-end effect (index rolls, rebalancing), not the reporting calendar |
| **T2 — year-end above quarter-end** (§4.2's ordering) | the December PRE mean against the mean of the March, June and September PRE means; and, per year, whether December's PRE beats that year's other three | **December > the other three pooled; ≥ 8 of 12 years** | ordering fails → the snapshot size does not scale the effect; reported as PARTIAL |
| **T3 — the persistence the mechanism names** | the correlation of `d_m` with `d_{m+1}` across the 17 roots, for months m ending at a quarter-end against the others; year-block bootstrap SE | **higher after quarter-end months** (a disturbance in the reporting run persists into the next month) | no difference → the book's calendar effect, if any, is not persistence; diagnostic, no gate |
| **T4 — era and years** (the D578 lesson) | ΔPRE by year (2012–2023, 12 full years) and by era, 2011-07–2015 against 2016–2023; the book's own bp/day by year beside it (the level path) | **≥ 8 of 12 years with ΔPRE > 0**; the post-2016 era not weaker than the pre-2016 (M6's direction) | ΔPRE carried by two or three years → not a calendar regularity |
| **T5 — what else sits on the calendar** | ΔPRE recomputed with the **POST window** (index rolls fall on business days 5–9 after the month-end) and with the last session of each quarter excluded (the settlement of the roll itself) | reported | diagnostic |

**Nulls.** T1's is the shift of the window within the quarter, exact; T1b's is the choice of
months, exact; both are the construction's own placements, neither a random draw. Beside them the
quarter-block bootstrap gives ΔPRE its SE, and T2 and T4 are counts of declared signs.

**Decision rule, declared.**
- **SUPPORTED** — T1 and T1b both above 0.95, T4's year count ≥ 8 of 12, T2's ordering holds.
  The mechanism's calendar prediction is in the data; the record says so and stops, because the
  line's forward slice is spent and a calendar-window construction on it would have no unread
  test (the deposit's §8.3 bridge is for a future line on a future slice).
- **PARTIAL** — T1 and T1b hold, T2 or the year count fails. The reporting calendar orders the
  book but not in the way the snapshot size predicts, or not in enough years to call it regular.
- **NOT SUPPORTED** — T1 or T1b inside its null. M7 fails; the record says which of the two
  and what the profile showed.

**Chance.** T1 has one direction and an exact 63-placement null; T1b one direction and an exact
495-subset null; T2 and T4 are declared counts. The joint claim is a window, a month set, an
ordering and a year count.

## 3. Reported beside, diagnostic, unpromotable

The session profile of mean `r_t` from 30 sessions before to 15 after each quarter-end, pooled
and by year-end against the other three; the same for the non-quarter month-ends; the trimmed
means (1 % both tails) of the PRE-session returns beside the mean and median; the ten largest
|r_t| PRE sessions named; the profile from the as-pre-registered variant (`ffill = 1`) beside
the amended one; the terciles cell beside High4/Low4; and, for the mechanism's other half, the
book's own bp/day by year so the calendar effect is read against the level it sits on.

**Audits, each proven to RAISE on a break that hits what the assertion reads:** (a) the harness
— the PRIMARY-window Sharpe of the rebuilt daily series equals D564's artifact to 1e-9; break =
the series rolled one session; (b) the calendar by a second path — the quarter-end sessions
found by a pandas groupby on the session strings' year-month taking the last session of each
{3, 6, 9, 12} month, never the runner's index arithmetic; break = the mask shifted one session;
(c) the placement null's zero offset reproduces the observed ΔPRE, and the subset {3, 6, 9, 12}
reproduces the observed ΔQ; (d) sign in money — a synthetic return series with +x on PRE
sessions and 0 elsewhere gives ΔPRE > 0 at rank 1.0 and its negation ΔPRE < 0; (e) right
quantity — the PRE and POST masks are disjoint and neither equals the other; `REQUIRED_OUTPUTS`
guard first.

## 4. What is read, and what is not

The breadth fixture and the settlement strip to 2023-12-29 for the 17 commodity roots, as D564
read them; D564's artifact for the harness. **Not read: any session from 2024-01-01 on** (spent
for this line by D574). **Seen-ness declared:** the daily returns of this very book on 2011–2023
were read by D564 and D574; this record reads them a second time, conditioned on a public
calendar the mechanism named in advance. That is a mechanism test on a seen outcome, and it can
inform nothing that trades: the deposit's own note (§3) says M1–M7 test the mechanism, not the
returns, and do not consume the selection budget.

## 5. What this record does not do

It does not run M1–M5 (M1 and M3 need a volume and full-curve decomposition; M2 a vol series;
M4 the He–Kelly–Manela capital ratio, a fetch; M5 inventory data, a fetch) — each is a separate
design if M7 gives a reason to continue. It does not build the equity-index-futures financing
rate (§4.1) or the calendar-spread liquidity measure (§4.3). It does not pre-register any
calendar-window construction, on this line or another. It does not read the funding or option
fixtures.

**Runtime.** The nearby series and the book take D564's build time, about a minute; the 63
placements and 495 subsets are means over masks, seconds.
