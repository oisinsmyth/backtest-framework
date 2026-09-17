# D456 RESULT — 154,970 8-Ks on 82% of the fixture and 81% of the dead, 15 item cells clear 300, filed the same or next day: no abandon condition fires; the atlas with returns is the next record

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D456-RESULT-155k-8-Ks-on-82-percent-of-the-fixture-and-81-percent-of-the-dead-15-cells-clear-300-filed-the-same-day-the-atlas-with-returns-is-next.md`. The H1 above is the full title.*

**A MEASUREMENT (R15): admits nothing. NO forward return was read.** Spec `5f8899e` predates the
parser (R8). Parse 0.1 min from D331's cached index (2,351 documents read, **0 fetched** — every
document the window needed was already in the cache); tables 0.6 min.

```
8-K rows 194,679 on 1,323 names through 2026-08-26;  28,492 rows after 2023-12-29 parsed and FLAGGED UNREAD (the stage-1 confirmation slice)
while-live 2010-2023: 154,970 filings;  legacy-coded filings 0;  reportDate present on 100.0%
selftest: item parsing, the pure flag, legacy exclusion, business-day lag, the unread flag, no duplicate (name, accession)
```

---

## 1. Coverage — A1 does not fire

```
                        n     >= 1 8-K while live 2010-2023
cohort  alive        1011        82.3%
cohort  DEAD          562        80.6%
all                  1573        81.7%     (CIK high 83.5%, low 85.5%, unresolved 0%)
8-Ks per live name-year: p10 0   p50 10   p90 20;   zero on 17% of name-years
```

**The dead file 8-Ks at the same rate as the living.** The 18% without any 8-K is not a cache
gap (0 documents fetched, 0 missing): 186 mapped CIKs have no 8-K at all, and those are the
**foreign private issuers** in the fixture (AMX, BTI, AFYA …), which file **6-K** instead. The
atlas is a domestic-filer atlas; a 6-K cell would be a separate record. X-a's 95% / 85% assumed
every issuer files 8-Ks, and that was wrong by the foreign share.

---

## 2. Counts — 15 cells

```
item     filings   pure     item     filings   pure     item     filings   pure
1.01     18,785   4,677     2.05        827     334     4.01        462     382
1.02      1,990     293     2.06        326      70     4.02        170      98   (below 300: not a cell)
2.01      2,557     710     3.01        636     275     5.02     29,093  19,342
2.02     48,921  36,590     3.02      1,855     259     5.03      4,537   1,528
2.03      9,004     461     3.03      1,284      33     5.07     11,914   7,558
2.04        192      42   (not a cell)                  8.01     36,344  23,204
excluded as cells: 9.01 (exhibits) 120,450;  7.01 (Reg FD) 35,686
```

Earnings (2.02) are 32% of all 8-Ks and officer changes (5.02) 19%, as X-b said. **Four of the
six "distress" items are cells** (2.05 exit costs, 2.06 impairments, 3.01 delisting notices, 4.01
auditor changes); **restatements (4.02, 170) and debt triggers (2.04, 192) are not** — too rare
on 1,573 names in fourteen years to be scored as cells, and they will be reported inside the
stage-1 atlas as sub-300 cells with no bar.

---

## 3. Timeliness — the index date is the event date

```
business days, reportDate -> filingDate:  all p50 0  p90 4  beyond four days 3.4%
2.02 0 / 1 / 1%   8.01 0 / 3 / 3%   1.01 2 / 4 / 4%   5.02 2 / 4 / 5%   3.01 2 / 4 / 6%   2.05 1 / 4 / 9%   2.01 1 / 5 / 13%   4.01 3 / 9 / 15%
```

An earnings 8-K is filed **the day of the release** (median 0); the rest are filed inside the
four-business-day rule on 85–97%. **Availability the bar after filing loses one to two days of
the reaction on most items and none on earnings.** The kernel's fill at the next open is the
honest entry; the stage-1 atlas will say how much of each cell's move is already gone by then.

---

## 4. Co-occurrence — the atlas double-counts, and by how much

1.01 (material agreement) carries 2.03 (a debt obligation) on 43% and an exhibit on 89%; 8.01
(other events) is the catch-all it was predicted to be (23–44% of every other cell carries it);
**5.02 is pure on 66%** — an officer change is usually filed alone. Only 2.05 and 2.06 co-occur
with earnings (25% each: exit costs and impairments are announced with results). The **pure**
counts in §2 are the clean versions of each cell and stage 1 scores both.

---

## 5. What each item sits in

```
cell    n        price lo/mid/hi   mom lo/mid/hi    ret20 lo/mid/hi   DV lo/mid/hi    dead share (base 36%)
2.02   48,921    32/34/35          33/33/34         35/31/34          50/24/26        26%      <- flat, as predicted
5.02   29,093    32/34/34          35/33/32         36/30/34          48/24/28        28%
8.01   36,344    32/32/36          32/33/35         33/31/36          44/24/32        29%
2.05      827    41/33/26          47/29/23         41/28/32          48/22/30        33%      <- exit costs: cheap, falling
2.06      326    44/32/24          54/27/19         42/27/31          33/22/45        26%      <- impairments: cheapest, worst momentum, but LIQUID
3.01      636    40/28/32          27/31/42         44/24/32          70/16/15        51%      <- delisting notices: thin, dead, and NOT low-momentum
3.02    1,855    42/30/28          34/23/44         38/20/42          59/23/18        33%      <- unregistered equity sales: thin, bimodal momentum
4.01      462    36/32/32          34/27/39         38/26/36          72/17/11        33%      <- auditor changes: the thinnest cell
```

**Every 8-K cell sits in the thin half of the universe** (44–72% in the bottom dollar-volume
tercile against a base of 33%): the fixture's 8-K filers skew small because the largest names
are a minority of 1,573. **The distress items are where predicted on price and, for 2.05 and
2.06, on momentum**; 3.01's momentum is bimodal (27% bottom, 42% top — a delisting notice for a
late filing hits a name that has often just spiked) and its dead share is 51% against 36%, not
the 75% predicted (half the names that get a notice survive it). **2.06 impairments are the one
distress cell in liquid names** (45% top-DV tercile) — the cell where a several-percent move
would clear the cost line.

---

## 6. The tails, named

Most 8-Ks 2010–2023: SHPG 745 (Shire, serial acquirer, delisted into Takeda), BFH 703, AHT 681
(Ashford, the D446 issuer), NWS 590, OKE 539, AAL 510, C 454, JPM 451 — acquirers, REITs and
banks, as X-f said. Most 3.01 notices: SCOR ×10 and HYZN ×9 (collapsed), SMCI ×9 and OFIX ×9
(survived) — **the delisting-notice cell is a late-filing cell as much as a distress cell**, and
stage 1 should read it with that in mind.

---

## 7. Predictions — three of six

| | prediction | outcome |
|---|---|---|
| X-a | alive ≥ 95%, dead ≥ 85%; 6–10 per name-year | **82% / 81%** (foreign 6-K filers); p50 10 ✓ |
| X-b | 12–16 cells; 2.02 30–40%, 5.02 12–20%; 4.02 < 250; 3.01 300–800; 2.06 300–600 | 15 ✓; 32% ✓, 19% ✓; 170 ✓; 636 ✓; 326 ✓ |
| X-c | lag p50 1–2, > 4 on < 10%, tightest on 2.02 | **p50 0**, 3.4% ✓, 2.02 tightest ✓ |
| X-d | 1.01 with 2.03 or 9.01 ≥ 60%; 5.02 pure ≥ 40%; 8.01 broad | 89% ✓; 66% ✓; ✓ |
| X-e | distress items bottom price & momentum ≥ 55%, dead ≥ 60% (3.01 ≥ 75%); 2.02 flat | price 40–44% (below), 2.05/2.06 momentum 47–54% ✓, **3.01 momentum bimodal**; dead **33–51%**; 2.02 flat ✓ |
| X-f | most 8-Ks acquirers/REITs; most 3.01 collapsed | ✓; **half survived** |

---

## 8. What this leaves — the principal's call

**No abandon condition fires and the stage-1 atlas is the next record**, as declared in the spec's
§6: every one of the 15 cells (plus 2.04 and 4.02 reported without a bar), long and short both
scored, cap 10, the state-matched control per cell (same day, same price × volatility ×
momentum cell, no 8-K of any item within ±5 bars), the enumerated rotation of each cell's
calendar, both cost lines, **and reproduction on the unread 2024-01 to 2026-08 slice of the same
names as the family's multiplicity control** — opened only with the principal's word. Three
things stage 0 adds to that design: (i) score **pure** and **all** versions of each cell; (ii) the
2.06 cell is the one distress item in liquid names and the likeliest to clear a cost line; (iii)
3.01 is two populations (late filers who survive, distressed names that do not) and the atlas
should split it by the dead flag — *after* the fact, disclosed, since the flag is hindsight.

**Disposition is the principal's.**

---

## 9. R13

Forty-eighth look by object; look #0 of the corporate-event line; no forward return, no holdout.
Files: `scripts/run_d456_8k_atlas_stage0.py`, `data/d456_8k_events.csv.gz` (194,679 rows,
28,492 flagged unread), `data/d456_build_info.json`, `data/d456_stage0.json`.
