# D565 RESULT — **DOES NOT PASS by 0.007**: the NG withdrawal-season spread earns **+0.69 gross / +1.03 Sortino** at the **94.2nd percentile** of its placement null (p95 +0.699), beats its always-on control three to one per day, and **clears every ledger bar at one micro a leg (net +0.62, skew +1.98, σ $24 a day) — the ledger's second entry, PROVISIONAL**; the obligated-buyer avatar is **not visible in the COT**

*2026-09-20. Spec committed in `950b4b9` BEFORE the runner (R8). Primary window 2016-01-04 →
2023-12-29 (2,065 sessions, 849 positioned, 40 positioned months); long window 2011 → 2023
(65 positioned months) as the declared diagnostic; **the 2024+ slice was not read.** Nothing
admitted to any book (R15). Runner `scripts/run_d565_ng_winter_spread.py`, output
`data/d565_ng_winter_spread.json`, 18 s. The Stage 0 disclosure in the pre-registration stands:
five calendar windows were read before the season was declared from the EIA definition.*

**Six of eight predictions held, and the two that failed are the two that matter for what this
is.** The pass rule needed the primary above its placement null's p95 and it sits 0.007 below it,
on an exact null. The avatar prediction — that the obligated winter buyer shows up as a rise in
NG's commercial long share into the formation months — failed: 7 of 13 years, a difference of
0.006 in share. The premium is there, at the size and with the consistency Stage 0 said; who
pays it is not established by this record.

---

## 1. The declared verdicts

| | observed | null | |
|---|---:|---|---|
| **PRIMARY** — spread, Nov → Mar, gross Sharpe / Sortino 2016–2023 | **+0.692 / +1.034** (SE 0.28) | N1 placement (1,562 offsets): p05 −0.47, p50 +0.20, **p95 +0.699**; rank **0.942** | **INSIDE, by 0.007** |
| N2, family of two | best +0.692 (the spread) | p50 +0.27, p95 +0.726; rank 0.918 | inside |
| December outright (secondary, seen) | +0.691 / +1.205 | its own N1: p95 +0.629; rank **0.965** | clears its own null; not the primary |
| control, always on | +0.370 / +0.514; net **+0.002** | | |
| **verdict** | | | **DOES NOT PASS** · avatar **UNSUPPORTED** |

| # | prediction | value | |
|---|---|---|---|
| P-1 | primary > 0, above N1 p95; point 0.4–0.9 | +0.692 vs p95 +0.699 | **fails by 0.007**; inside the point range |
| P-2 | positioned months hit ≥ 0.60, median > 0 | **0.75**, +0.34 % | **holds** |
| P-3 | primary beats the control per positioned day and on Sharpe | **4.20 bp** vs 1.26 bp a day; 0.69 vs 0.37 | **holds** |
| P-4 | N1 rank ≥ 0.90 | 0.942 | **holds** |
| P-5 | primary worst month > −3 %; December worst < −10 % | **−3.48 %** (Jan 2022); −11.5 % | **fails** on the first clause |
| P-6 | commercial long share higher in Oct–Nov than Apr–Sep in ≥ 9 of 13 years | **7 of 13**; 0.396 vs 0.390 | **fails** |
| P-7 | dollar σ over positioned sessions < $150 | **$24** | **holds** |
| P-8 | December outright (seen): short pays ≥ 8 of 13 | 10 of 13; mean +11.6 % | **holds** |
| P-9 | falsifiers | primary above p50; control does not beat it; **avatar unsupported** | the third fires |

## 2. Performance — net and gross, the four groups

**The spread, Nov → Mar, one pair, 2016–2023:**

| | gross | net |
|---|---:|---:|
| Sharpe / Sortino, all sessions | **+0.692 / +1.034** | **+0.483 / +0.710** |
| Sharpe / Sortino, positioned sessions only | +1.080 / +1.612 | |
| ann. vol · total · max DD | 6.3 % · +35.6 % · −10.0 % | |
| cost | **27 bp a positioned month** (four sides at $2 on a ~$3,000 leg) | |
| breakeven | 22 bp/side against 6.7 modelled: **cost is a third of the gross** at one micro | |

**Group 2 — the 40 positioned months:** mean +0.89 %, **median +0.34 %**, hit **0.75**, sd 2.0 %,
worst −3.48 % (January 2022), best +6.28 % (January 2023). The mean is above the median: the
book earns steadily and its size comes from a few months. On 2011–2023, 65 months: mean +0.58 %,
hit 0.71, worst −9.84 % (January 2014, the polar vortex).

**Group 3 — by month of the season (2011–2023, 13 each):**

| | Nov | Dec | Jan | Feb | Mar |
|---|---:|---:|---:|---:|---:|
| mean | +0.30 % | +0.56 % | +0.62 % | +0.58 % | **+0.82 %** |
| hit | 0.77 | 0.62 | 0.77 | 0.69 | 0.69 |
| worst | −1.2 % | −3.1 % | **−9.8 %** | −0.5 % | −0.9 % |

January, the month the pre-registration had not read, is the second-best month and carries both
tail losses (2014, 2022). By season: 11 of 14 positive; 2013–14 **−10.3 %**, 2021–22 −2.6 %,
2023–24 −2.8 % on its two months; 2022–23 **+12.7 %**, 2018–19 +8.7 %, 2011–12 +7.0 %. The
off-season, had the spread been held, earned **−0.78 bp a day** (Sharpe −0.26): the schedule is
not a drawdown filter on a positive always-on book, it is where the whole return sits, which is
P-3 by another route.

**Group 4 — the nulls.** The placement null's median is +0.20 — five months of short spread
placed anywhere in the calendar earns a little, which is the contango bleed the always-on control
also shows — and its p95 is +0.699. The season is the 94th percentile of placements. The December
outright clears its own placement null (rank 0.965) but is the secondary, seen in Stage 0, and
its worst month is −11.5 %.

## 3. The component line — every bar clears, and the ledger's rule applies

| | one MNG short T1 / one MNG long T2, Nov → Mar |
|---|---:|
| **C-a** net Sharpe / Sortino, all sessions | **+0.618 / +0.975** (gross SE 0.28) |
| **C-c** skew | **+1.98** |
| **C-d** daily σ, positioned · all sessions | **$24 · $16** |
| total · cost · max DD, 2016–2023 | **+$1,261** · $320 · −$344 |
| hit (sessions, all) | 20.5 % (positioned 41 % of sessions) |
| by season, $ | 2016–17 +130, 17–18 +12, 18–19 +309, 19–20 +100, 20–21 +76, 21–22 −50, 22–23 **+679**, 23–24 −49 (two months) |
| **C-b** ρ with entry #1 (K8, NQ day session) | **not computable**: K8's daily P&L is not on disk; by instrument and clock (a NG calendar spread held a month against an NQ day session) it is expected near zero, and that is an expectation |
| **C-e** | this record; the placement null; the always-on control |

**Under the ledger's standard, this is a component**: C-a on the point estimate (+0.62 > 0.5),
C-c, C-d with a factor of twenty to spare, C-e. It sits below its family null's p95, so the
ledger's own rule (D468) makes it a **PROVISIONAL** entry: it counts for C-b against later
entries, it goes into the assembled book, and only the unread slice promotes or removes it. It is
entered as **#2**. Two things the row must carry: the money is small — one spread is $160 a
season on average, and the account could carry twenty pairs inside C-d (σ $480 a day) — and the
gross-to-net gap is a third, so the component's Sharpe is a function of the $3 round trip more
than any other here.

**Correction, same day.** The first draft of this section said entry #1 (K8) was parked awaiting
a second entry. That was stale: K8 was taken forward in D503 on 2026-09-13, did not transfer, and
was closed by the principal that day; the MACD day-session arm was admitted as the ledger's entry
#2 and the prop book's first arm. **This spread is therefore entry #3**, and the assembled book it
joins is the MACD arm plus this spread. The NQ day-session 2024+ slice is spent for the MACD arm
(D503); the NG 2024+ slice is unread and offers thirteen positioned months (January–March 2024
and two full seasons). The joint read of the spread forward and of the assembled book, with
hurdle P, is the principal's call and is pre-registered separately as D566 when taken.

## 4. The avatar — the premium is there; the buyer is not in the data

The mechanism named the obligated winter buyer and predicted a rise in commercial long share into
October–November. Measured on the legacy report: 0.396 against 0.390, higher in 7 of 13 years,
net commercial share +0.075 against +0.072. That is nothing. Three readings, none of which this
record can choose between: the legacy "commercial" category nets producers against consumers, so
a rise in utility longs offset by a rise in producer shorts is invisible in it; the winter
premium is paid by a different party (managed money short-covering, storage owners' forward sales
schedules); or the premium is not hedging pressure at all but a risk premium for the cold-shock
tail, which needs no identifiable hedger and is consistent with January 2014 and 2022 being where
the spread loses. The disaggregated report (on disk for NG from 2009) separates producer/merchant
from managed money but still nets buyers and sellers inside the commercial-like category; the
avatar test that would settle it is the CFTC's *Supplemental* report, not fetched, or the FERC
Form 552 buyer data, not on the list. **The record enters the component on its numbers and
records the avatar as unsupported.**

## 5. What was not done, and what is still wrong with this

- **Two months of the 65 are the tail**: January 2014 (−9.8 %) and January 2022 (−3.5 %). A
  spread with a $24 daily σ can take a month of that size without breaching anything, which is
  why C-c and C-d hold; the outright December short cannot (−11.5 %, and 2018's +40 % against a
  short in November is outside the season by one month and inside it by two days of formation).
- **The Stage 0 read.** Five windows were seen. The declared season contained one unseen month,
  January, and it held. The forward slice is the only clean confirmation and it has two seasons.
- **Cost is a third of gross at one micro.** At two or more pairs the fixed part of the round
  trip halves per unit; the record scores one micro because that is the standard.
- **No state gate**, by declaration; the storage state added nothing beyond the calendar in Stage
  0. **No other root.** The next avatars in the plan — grains at harvest with WASDE stocks-to-use,
  livestock with the disaggregated COT — each get their own pre-registration.
- The five audits ran and each was proven to raise; all in the json.
