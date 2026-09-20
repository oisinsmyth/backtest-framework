# D568 RESULT — **DOES NOT PASS**: the corn post-harvest spread earns **+0.60 gross / +1.00 Sortino** at the **85th percentile** of its placement null (p95 +0.71), and **the always-on long spread earns more per positioned day than the window does** (1.11 bp against 0.90) — the window samples a year-round narrowing whose months are **April and June**, not December; **December itself loses 10 of 13**; the merchant avatar is **not in the COT** (net short falls through the window in 5 of 12); at one contract a leg the book is **net +0.43** and fails C-a; **not entered**

*2026-09-20. Spec committed in `752041d` BEFORE the runner (R8). Primary window 2016-01-04 →
2023-12-29 (2,065 sessions, 497 positioned, 24 positioned months); long window 2011 → 2023 (39
positioned months) as the declared diagnostic; **the 2024+ slice was not read on any source** —
the runner filtered the WASDE fixture to releases before 2024-01-01 as its first act on it (978
of 1,170 rows, 163 reports, last 2023-12-08, asserted). Nothing admitted to any book (R15).
Runner `scripts/run_d568_corn_post_harvest_carry.py`, output
`data/d568_corn_post_harvest_carry.json`, 27 s. The Stage 0 disclosure in the pre-registration
stands: the twelve per-window returns and their correlations were seen; the daily path, the
per-month split, the null, the control, the cost, the gate and the COT through the window were
not.*

**Four of nine numbered predictions held and the five that failed are the five that decide
what this is.** The primary is positive, inside its point range, and its positioned months are
tail-limited exactly as the mechanism said (worst month −0.61 %, σ $28 a day). But it sits
below its placement null's p95 on an exact null; the always-on control — the same long spread
held every month of the year — earns *more* per positioned day; the real-time stocks-to-use gate
raises the mean and lowers the hit; the merchant's hedge does not lift through the window; and
cost is 29 % of gross rather than the predicted quarter. The pre-registered falsifiers fire on
the control and on the avatar. **The post-harvest schedule adds nothing to a drift the corn
curve carries all year, and the party the design named is not the one moving it.**

---

## 1. The declared verdicts

| | observed | null | |
|---|---:|---|---|
| **PRIMARY** — spread, Dec → Feb, ungated, gross Sharpe / Sortino 2016–2023 | **+0.604 / +1.005** (SE 0.29) | N1 placement (1,562 offsets, exact): p05 −0.50, p50 +0.19, **p95 +0.706**; rank **0.848**; Sortino p95 +1.22 | **INSIDE, by 0.10** |
| secondary — the same spread gated on stocks-to-use | +0.510 / +0.902 (12 positioned months) | its own N1: p95 +0.635; rank 0.897 | inside |
| N2, family of two | best +0.604 (the primary) | p50 +0.25, p95 +0.746; rank 0.821 | inside |
| control, always on | **+0.502 / +0.784**; net +0.348 | | **1.11 bp a positioned day against the primary's 0.90** |
| **verdict** | | | **DOES NOT PASS** · avatar **UNSUPPORTED** · ledger **fails C-a** |

| # | prediction | value | |
|---|---|---|---|
| P-1 | primary > 0, above N1 p95; point 0.3–0.9 | +0.604 vs p95 +0.706 | **fails**; inside the point range |
| P-2 | positioned months hit ≥ 0.55, median > 0; windows 2011–22 hit ≥ 0.65 (seen) | **0.58**, +0.14 %; 9 of 12 | **holds** |
| P-3 | primary beats the always-on control per positioned day and on Sharpe | **0.90 vs 1.11 bp** a day; Sharpe 0.60 vs 0.50 | **fails** on the clause that matters |
| P-4 | N1 rank ≥ 0.90 | 0.848 | **fails** |
| P-5 | primary worst month > −2 %; worst window > −1 % | **−0.61 %** (Dec 2019); −0.48 % (2018–19) | **holds** |
| P-6a | seen: Spearman(S/U, window) ≤ −0.3, tight tercile above full | −0.44 (p 0.15); +1.07 / +0.75 / +0.25 % | **holds** (seen) |
| P-6b | unseen: the real-time gate's mean ≥ the ungated's **and** its hit ≥ | mean **+0.71 % vs +0.51 %**; hit **0.50 vs 0.70** | **fails** on the hit |
| P-7 | dollar σ over positioned sessions < $150 | **$28** | **holds** |
| P-8 | commercial net short share falls through the window in ≥ 8 of 12, ≥ 4 of 7 in sample | **5 of 12; 2 of 7**; mean change **+0.018** (it rises) | **fails** |
| P-9 | modelled cost < 25 % of the gross positioned-month mean | 5.4 bp a month against 18.7 bp: **29 %** | **fails** |
| P-10 | falsifiers | above p50; **control beats the primary per day**; **avatar unsupported**; state not a story by the letter (P-1 fails first) | two fire |

## 2. Performance — net and gross, the four groups

**The spread, Dec → Feb, one pair, 2016–2023:**

| | gross | net |
|---|---:|---:|
| Sharpe / Sortino, all sessions | **+0.604 / +1.005** | **+0.421 / +0.666** |
| Sharpe / Sortino, positioned sessions only | +1.233 / — | |
| ann. vol · total · max DD | 0.91 % · +4.48 % · −1.30 % | +3.03 % · −1.81 % |
| cost | **16.1 bp a window** (four sides at $3 + $6.25 on a ~$25,000 leg; no pair change inside any window) | |
| breakeven | 12.4 bp/side against 4.0 modelled: **cost is 29 % of the gross** at one contract | |
| 2011–2023 | +0.723 / +1.233 | |

**Group 2 — the 24 positioned months:** mean +0.19 %, **median +0.14 %**, hit **0.58**, sd 0.5 %,
worst −0.61 % (December 2019), best +1.55 % (February 2021). On 2011–2023, 39 months: mean
+0.21 %, median +0.08 %, hit 0.54, worst −0.61 %, best +2.46 % (February 2013). The twelve
complete windows 2011–22: mean **+0.69 %**, 9 of 12 positive — the seen Stage 0 table,
reproduced on the daily book.

**Group 3 — by month of the window (2011–2023, 13 each), the split the pre-registration had
not seen:**

| | Dec | Jan | Feb |
|---|---:|---:|---:|
| mean | **−0.02 %** | +0.12 % | **+0.53 %** |
| hit | **0.23** | 0.62 | **0.77** |
| worst | −0.61 % | −0.44 % | −0.45 % |

**December — the month the mechanism names as the start of the merchant's selling — loses in
10 of 13 years.** The window's return is a February effect: the March contract gaining on May
in the month before it goes into delivery. By window: 2011-12 +0.98 %, 2012-13 **+2.16 %**,
2013-14 +0.65, 2014-15 −0.13, 2015-16 +0.56, 2016-17 +0.20, 2017-18 +0.26, 2018-19 **−0.48**,
2019-20 +0.73, 2020-21 **+2.19**, 2021-22 +1.48, 2022-23 −0.35; the two partial windows (Jan–Feb
2011, Dec 2023) +0.05 and −0.15. Two windows (2012-13, 2020-21) are 53 % of the twelve's total.
By year, Sharpe: 2016 +1.41, 2017 −0.60, 2018 +0.23, 2019 −1.14, 2020 +2.00, 2021 +1.16, 2022
+1.00, 2023 −0.44. The formation basis was never at full carry (ratio 0.2–0.7 of D567's
convention; inverted in 2012 and 2022) and the window's return does not order on it (ρ −0.41,
p 0.19, seen).

**Group 4 — the nulls, and the control that is the finding.** A three-month long-spread schedule
placed anywhere in the calendar earns a median +0.19 and a p95 of +0.71; the post-harvest
placement is the 85th percentile. The reason is in the always-on control: **long the
first-nearby spread by the same rule, every month, is +0.50 gross / +0.35 net, 1.11 bp a
positioned day, and the off-window months alone are +1.17 bp a day (Sharpe +0.47).** By calendar
month, 2011–2023, bp a day: Jan +0.5, Feb +2.7, Mar +0.8, **Apr +6.4**, May −2.0, **Jun +7.0**,
**Jul −5.8**, Aug −1.8, Sep +0.1, Oct +1.6, Nov −0.3, Dec −0.1. The corn curve's front gains on
its deferred in April and June and gives it back in July — an old-crop / new-crop spring
pattern, seen here in a diagnostic, not licensed by this record, and not a post-harvest story.
The window the design named catches the tail of a drift, not a schedule.

## 3. The state variable and the gate — seen ordering, no real-time rule

The seen Stage 0 ordering reproduces (Spearman −0.44 on the daily-book windows; tight tercile
+1.07 %, full +0.25 %, cut points 0.110 / 0.140). The declared real-time rule — open when the
November stocks-to-use is at or below the median of every prior November's — opened **four of
ten decidable windows** (2018-19, 2020-21, 2021-22, 2022-23) and stayed flat for 2013–2017 and
2019 and 2023, because the fixture's first three Novembers (2010–2012, the drought-era
stocks-to-use of 0.06–0.07) set an early median no later year could reach. The open windows
average +0.71 % against +0.51 % for all ten, and **two of the four are the window's two losers**
(2018-19 −0.48 %, 2022-23 −0.35 %), so the hit falls from 0.70 to 0.50. The gated cell is +0.51
gross on twelve positioned months at rank 0.897 of its own placement null. **An in-sample
tercile ordering is not a rule**: the ordering was real and the one declared cut on it did not
select. P-6(b) fails.

## 4. The avatar — the merchant's hedge does not lift

The mechanism said the merchant, long cash and short futures at harvest, sells the crop through
the winter and buys the hedge back. Measured on the legacy report: corn commercial net short
share (short − long over open interest) at the last report before February's last session is
below its value at formation in **5 of 12 windows** (2 of 7 in sample), and on average it
**rises** by 0.018 of open interest; the change does not order the window's return (ρ +0.15,
p 0.63). With D567's harvest finding — the harvest carry is priced by August and stocks-to-use
does not order it — **the merchant-at-harvest avatar has now failed on corn in both halves of
its year, as the pre-registered falsifier said it would if P-8 failed.** The record closes the
avatar as its falsifier declared; the root is not closed, and any further corn construction is
a new Stage 0 with the always-on control in it.

## 5. The component line — C-a fails; not entered

| | one ZC long H / one ZC short K, Dec → Feb |
|---|---:|
| **C-a** net Sharpe / Sortino, all sessions | **+0.426 / +0.694** (gross +0.59 / +1.00) |
| **C-c** skew | +2.10 |
| **C-d** daily σ, positioned · all sessions | **$28 · $14** |
| total · cost · max DD, 2016–2023 | **+$760** · $314 · −$361 |
| hit (positioned sessions) | 0.34 |
| by window, $ | 2015-16 (Jan–Feb) +94, 16-17 −25, 17-18 −12, 18-19 −112, 19-20 +101, 20-21 **+513**, 21-22 +426, 22-23 −162, 23-24 (Dec) −62 |
| **C-b** ρ with entry #2 (the MACD arm) | **not computable**: the arm's daily P&L is not on disk; expected near zero by instrument and clock, an expectation |
| **C-e** | this record; the placement null; the always-on control |

**Not entered.** C-a fails on the point estimate (+0.43 against 0.5); the construction is below
its family null; and under this ledger's own rule the D468 provisional path needs C-a first. The
number is recorded in `COMPONENTS_PROP.md` on the scored-constructions table, as every scored
construction is. Two things the row must carry: the book is tail-limited and cheap in σ terms —
one pair is $28 a day and eighteen would fit inside C-d — and the money is $95 a window, of
which a third is cost.

## 6. What was not done, and what is still wrong with this

- **The finding is the control, and it is diagnostic.** The corn curve's average carry narrowing
  through the year — and its April / June / July shape — is seen in a control cell, not in a
  pre-registered one. It may be a spring old-crop story worth its own Stage 0 with a control
  of its own; nothing here licenses building on it.
- **December is negative 10 of 13**, which is where the design put the mechanism's start. That
  number was not seen before this run and is not a licence to re-window.
- **The gate's median was set by three drought years.** A different prior window would decide
  differently; that is precisely why one cut was declared and why the failure stands as it is.
- **Cost is 29 % of gross** on a full-size grain spread — smaller than NG's third, still a
  round-trip-dominated line at one pair.
- **The ZC 2024+ slice is unread** (January–February 2024 and two full windows, eight positioned
  months). Nothing in this record asks for it.
- The seven audits ran and each was proven to raise; the declared gate break "a median that
  includes the current year" was **inert on this data** (it changes no decision, and the json
  records that), so the proof of that audit is the shifted-decisions break, which fired.

**Lesson, recorded for the next Stage 0:** a per-window read must carry the same construction
held always-on, per positioned day, before any window in it is pre-registered. D567's Stage 0
did not, and the window that led was the drift sampled in its third month.
