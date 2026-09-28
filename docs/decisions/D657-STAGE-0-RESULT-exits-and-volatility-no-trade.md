# D657 STAGE 0 RESULT — a CME margin increase forces positions out and is followed by two weeks of volatility nobody forecast, but the price it moves does not come back: an input for strategies, not a trade

*Design: [D657](D657-STAGE-0-DESIGN-margin-hikes-forced-exit-and-reversion.md) (`65d7682`), amended by A1 (`ed24889`,
the source) before any margin file was downloaded; both were committed before the runner existed (R8). Builder
`scripts/build_cme_margin_events.py`, fetcher `scripts/fetch_cme_margin_archive.py`, runner
`scripts/stage0_d657_margin.py`. Numbers: [`data/stage0_d657_margin.json`](../../data/stage0_d657_margin.json); events
[`data/d657_margin_changes.csv`](../../data/d657_margin_changes.csv), coverage
[`data/d657_margin_coverage.csv`](../../data/d657_margin_coverage.csv), gates
[`data/d657_margin_build.json`](../../data/d657_margin_build.json), notice dates
[`data/d657_margin_notices.csv`](../../data/d657_margin_notices.csv). **The last settlement read is 2023-12-29**; every
event has E ≤ 2023-12-15. No construction was built: this record tests premises.*

## The answer in one line

**M1 passes: margin increases force positions out** (open interest −1.50 % against matched controls, t −3.03).
**M3 passes: realised variance over the next ten sessions runs 29 % above a forecast made before the notice**
(t 4.79). **M2 fails: the move during the forced-exit window does not revert** (β −0.0003, t −0.48; the expected move
is below three round trips). This is Hedegaard's finding on a wider universe and a longer sample: the exits happen and
the volatility comes, and neither leaves a price move to trade. **Routing: M2 closes; M3 routes to an overlay test.
The principal closed the line and recorded M1 and M3 as an input for strategies (§8).**

## 1. The events

**Source.** CME's own per-product margin histories, as archived by the Internet Archive (A1: CME refuses scripted
clients and routing around that is not done). 124 files for the 33 roots, fetched sequentially at 2 s intervals, every
file logged with its capture timestamp and sha256; plus 1,772 archived clearing advisories (2010–2016) for notice dates.
Three layouts, all extracted with pypdf: CME's change log (2008 to about 2015–2017), daily tables by roll index (the
2009–2013 and 2014–2017 zips, 2019/2020 onwards), each read for the **front** tier's maintenance margin. In the change
logs the speculator's initial margin is 1.1 × maintenance (1.35 in some years), so a percentage change in one is the
percentage change in the other.

**Coverage has a hole.** For most roots the archive holds 2008 → 2015–2017 and 2020-06 → onwards; the rates products,
CL and RB have files from 2019. **No event is inferred inside a hole**; March 2020 is covered only for rates, CL, RB and
the index futures. RTY, BZ and PA have no history and are out; **BTC has no scored event** (its history starts in 2020
and no event had 20 matched control sessions).

**The build gates (G0).**

| gate | outcome |
|---|---|
| G0-a, every root parses | **pass**: 33 of 33 (14 files not parsed, all post-SPAN 2 or truncated, listed in the build JSON) |
| G0-b, hand check | **pass**: 40 draws (seed 657; GC, CL, ZC and pre-2014) printed beside their source text, all correct. Checked against pypdf's text of the page, not a rendering (no renderer on this machine) |
| G0-c, overlapping files agree (A1) | **pass**: 96.4 % of 663 increases agree on date and new amount between files quoting one contract; the 22 in pairs where the change log quotes the big index contract and the daily table the E-mini agree 100 % on date and percentage (their amounts cannot agree by construction) |
| G0-d, ≥ 100 events | **pass**: 882 increases ≥ 5 % in sample before merging, 580 after merging within 10 sessions |

**What the gates caught** (all fixed before any price was read, and listed in the build JSON):
- **the archived corn change log is soybeans' file**, line for line (29 shared steps; 14 % agreement with corn's own
  daily table, 100 % for soybeans'): excluded;
- **CL's change-log blocks list only the tiers that changed** (2010-05-21 lists months 2–4, 5–10 and 11–18, not month 1),
  so a block without the front tier is no front change, never a change to its first row;
- 4 holiday rows carrying a zero margin and 9 steps undone within three days (wheat 2,500 → 12,500 → 2,500 on
  2010-09-23; corn +10 % on 2010-01-04 and back the next day): removed as not margins;
- the rule that the post-SPAN 2 files (energy from 2023-10-20, index from 2024-10-18) are excluded was fixed before
  any series was looked at: under SPAN 2 the margin is a model output, not a set table.

**Notice dates.** 26 events take N from an archived advisory (89 performance-bond advisories carry both dates; the
effective date follows the notice by one calendar day in 53 of them, and one took effect after a Saturday close);
the other 485 take N as the session before E, as A1 declares.

## 2. The runner, and three data faults it found

Returns are settlement to settlement on the nearest contract whose guard (first notice for metals, Treasuries, grains
and LE; the last trading day elsewhere) is at least ten sessions after E+7, asserted per event. Controls: for each
event, sessions on the same root in the same within-root quintile of trailing 20-session volatility, with the same
trend sign, at least 20 sessions from any margin change, and inside the covered history (median pool 117); 2,000 draws
of one control per event (seed 657); cluster-robust t by notice date (272 distinct dates for 511 events).

Three faults were found and fixed while building, before the reported run, and each would have changed the answer:
1. **CME's definitions expiry map is incomplete.** It lacks a quarter of the Treasury contract-years, about 9 % of FX rows
   from 2017, 7–22 % of silver and platinum and most of BTC. Anything resolved through it vanished: the new ZF front
   (3.4 million contracts, September 2021) was missing from the open-interest total, and front months from the price
   panel. Contract decades are now read from the code and the session (a one-digit year is the first year ending in
   that digit whose delivery month is no more than three months before the session; SOFR codes name the start of their
   reference quarter). D655 and D656 resolved through the same map (flagged separately).
2. **Open interest before 2016 carries no reference session, and from 2016 each session is published twice** (the
   morning after, and again at the next evening open keyed to the next session). A first pass collapsed the early years
   and mixed the two publications; its M1 read open interest *rising* 2.6 % against controls. Uniformly for all years:
   morning publications, each describing the root's last session before its publication date — **99.5 % agreement with
   CME's own reference session** where the files carry one.
3. D654's expiry loader keeps its own 26 roots and would have dropped ES, NQ, YM, NKD, LE, HE, SR3 and BTC silently; this
   runner has its own, and its selftest asserts all 33.

**Disclosed runs.** Before the declared run, three preliminary runs were made: one crashed at the SOFR contract keys,
one produced the invalid open-interest M1 above, and one ran on corrected data with N from 22 advisories and without
NG. That last one read M1 −1.60 % (t −3.02), M2 β +0.0001 (t 0.20), M3 +0.256 (t 4.47): the same verdicts. The numbers
below are the declared run (N from advisories where they exist, NG included).

## 3. M1 — the forced exit (511 events)

| | outcome | bar |
|---|---|---|
| mean ΔOI, N−1 → E+5 | −1.28 %; **abnormal (less the matched control) −1.50 %**, cluster t **−3.03**; median −0.68 % | B1 pass |
| control-draw null of the event mean | p05 −0.38 %, p50 +0.23 %, p95 +0.78 % (p05's SE 0.015 points) | B2 pass, decisive |
| leave one year out | −1.29 % to −1.64 %, negative in all 13 | B3 pass |

By class (a diagnostic, not a bar): index −4.9 % (43), FX −2.3 % (92), metals −2.1 % (64), grains −1.3 % (109),
energy −1.1 % (78); **rates +0.1 % (110) and livestock +0.1 % (15) show no exit.** FX and index carry a real, mechanical
drop at each quarterly expiry that the volatility-matched control does not align on, so their magnitudes are the least
clean. By era: −1.0 % (2010–2017), −2.1 % (2019–2023).

## 4. M2 — does the forced-window move revert? (511 events)

| | outcome | bar |
|---|---|---|
| β of Y (E+2 → E+7) on W/σ (N−1 → E+2) | **−0.00032**, cluster t **−0.48** | B1 FAIL |
| control-draw null of β | p05 −0.0015, p50 −0.0003, p95 +0.0009 | B2 FAIL (at the null's median) |
| leave one year out | −0.0001 to −0.0006, negative in all 13 | B3 pass |
| expected move, `|β| × median |W/σ|` | **4.9 bp** against 3 × the median full-size round trip (2.70 bp): 8.1 bp; micro (33 events) 7.3 bp a round trip | B4 FAIL |
| M1 passes | yes | B5 pass |

**The design's B4 formula carried a slip.** It wrote `|β| × median |W/σ| × median σ` with Y in returns, which is return
squared. The bar is applied to the dimensionally consistent form above. The other reading, β estimated on Y/σ and
multiplied back by σ, gives 0.1 bp and fails harder. Both are in the JSON.

## 5. M3 — volatility beyond its forecast (381 events)

| | outcome | bar |
|---|---|---|
| mean `u` = log mean RV(E+1 … E+10) − HAR forecast made at N−1 | **+0.258** (realised variance 1.29 × forecast), cluster t **4.79** | B1 pass |
| control-draw null of the mean `u` | p05 −0.036, p50 +0.008, p95 +0.053 (p95's SE 0.001) | B2 pass, decisive |
| leave one year out | +0.239 to +0.280, positive in all 11 | B3 pass |

The HAR model (daily, weekly and monthly log RV) is refitted each calendar quarter on rows whose target ended before
the quarter began (≥ 250 rows), so 2010 and early-2011 events have no forecast. By class: rates +0.43, grains +0.33,
energy +0.26, index +0.25, metals +0.11, livestock +0.09, FX +0.09. By era: +0.22 (2010–2017), +0.28 (2019–2023).

## 6. The predictions

| | prediction | outcome |
|---|---|---|
| 1 | G0-c passes | held, on the gate A1 put in its place (96.4 %) |
| 2 | M1 holds, open interest down 0.5–2 % against the control | held: −1.50 % |
| 3 | M2 fails at B2: β negative but not beyond the control | held: −0.0003 at the null's median |
| 4 | M3 holds at B1 and is borderline at B2 | **half**: B1 held; B2 is not borderline (+0.258 against p95 +0.053) |
| 5 | 2020 and 2022 hold at least 40 % of the events | **FAILED**: 26 % (the hole removes 2016–2020, and 2010–2015 is well covered) |
| 6 | at most one of M2 and M3 routes | held: M3 only |

## 7. Routing, as the design declared it

M1 passes, M2 fails (close the reversal premise), M3 passes: a pre-registered overlay test on the prop ledger's
components (halve size for ten sessions after an increase on the traded root). No personal-book construction.
Hedegaard's price-impact result (a 15 % rise after an increase) was not re-measured here.

## 8. CLOSED by the principal, 2026-09-28, and recorded as an input

"Record this as an input into a strategy, then finish off, close and merge." **The margin-deleveraging line is closed
under R15**: there is no margin-event trade, directional or reverting, and the 2024+ slice was never read for it.
**What is recorded, for any strategy to use as an input rather than a signal:**

- **A CME margin increase on a root is a public, dated forecast of about 29 % more realised variance over its next ten
  sessions than a volatility model would give** (M3), in every year and every asset class, largest in rates and
  grains. The effective date is known a day ahead.
- **It is accompanied by about 1.5 % of open interest leaving** (M1), in every class except rates and livestock, and
  (Hedegaard) by higher price impact.
- **Uses this supports:** a size-down or pause filter on any component trading the root in the ten sessions after an
  increase (the overlay M3 routes to), and a cost filter (trade less while impact is high). Whether the variance is
  already in option prices (realised after the notice against implied at it) is an open question for the personal book,
  not a task.
- The event table (`data/d657_margin_changes.csv`) and its builder are the reusable pieces.
