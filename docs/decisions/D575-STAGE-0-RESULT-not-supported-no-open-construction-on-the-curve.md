# D575 STAGE 0 RESULT — the livestock avatars are **not supported**: hogs' supply-calendar prediction is **falsified** (the three predicted placements are all negative; the best is December → February), cattle's best placement sits outside both the supply-calendar set and the feedlot-hedge set (February → April on M/Q, +0.63 / +0.84, a null cell); neither declared construction is best of its twelve; **the closing clause fires — the seasonal-spread line on the commodity curve has no open construction**

*2026-09-20. Design committed in D575 (`892b177`) before this ran. Diagnostic: 2011 → 2023,
thirteen windows a placement; nothing from 2024-01-01 on was read on any source. Runner
`scripts/stage0_d575_livestock_placements.py`, output `data/stage0_d575_livestock.json`, 29 s.
Six audits on each declared construction, each proven to raise; held-contract share 100 % on
both roots.*

---

## 1. The predictions against the profiles

Sharpe of the short spread, 2011–2023 (2016–2023 beside), by placement month; the declared
construction in bold.

| root | *m*1 → *m*12 | best (set predicted) | negatives predicted | control bp/day |
|---|---|---|---|---:|
| **HE** | +0.06 −0.10 +0.11 −0.40 −0.49 +0.23 −0.16 **−0.19** −0.29 +0.07 +0.10 **+0.46** | ***m*12** ({7, 8, 9}: −0.16, −0.19, −0.29) — **falsified** | *m*3 +0.11 fails; *m*2, *m*4 hold | **−2.72** (Sharpe −0.49) |
| **LE** | +0.04 **+0.63** +0.16 **−0.05** −0.22 +0.18 +0.40 +0.10 −0.19 +0.21 +0.05 −0.03 | ***m*2** ({3, 4, 5}); hedge set {10, 11}: no | *m*10 +0.21 fails | **+0.05** (Sharpe +0.02) |

**Decision rule:** supply calendar **NOT SUPPORTED**, refuted on hogs; cattle's feedlot-hedge
avatar not supported either; no candidates; **no declared construction is best of twelve**.

## 2. The declared constructions, in full

| | **HE *m*8**, Aug → Oct, Z/G | **LE *m*4**, Apr → Jun, Q/V |
|---|---:|---:|
| gross Sharpe / Sortino 2016–23 (SE) | **−0.28 / −0.38** (0.27) | −0.08 / −0.11 (0.25) |
| net | −0.29 | −0.11 |
| 2011–23 gross | −0.19 | −0.05 |
| 24 positioned months: hit · worst | 0.42 · **−7.75 %** | 0.62 · −2.78 % |
| per month 2011–23 (mean · hit) | Aug +0.26 % · 0.54; **Sep −1.34 % · 0.31**; Oct −0.01 · 0.46 | Apr −0.02 · 0.38; May −0.31 · 0.46; Jun +0.23 · 0.77 |
| worst window | **2020 −17.2 %** (the spring-2020 hog collapse into the fall) | 2012 −1.65 % |
| rank of twelve, 2011–23 / 2016–23 | 3 / 2 | 2 / 2 |
| dollar: net Sharpe · skew · σ positioned · total | −0.15 · −0.25 · $187 · **−$1,786** | −0.08 · −0.50 · $130 · −$666 |
| ledger | fails C-a | fails C-a |
| **candidate** | no | no |

**Hogs.** The three placements the supply calendar named — the nearby delivering into the
October → December glut against a deferred past it — are the three of the twelve that lose most
consistently, and the declared August → October construction lost 17 % in its 2020 window.
The always-on short spread loses 2.7 bp a day: on hogs, as on every grain, the nearby
strengthens against the deferred on average. The one positive placement of size, December →
February on the April/May pair (+0.46 / +0.22, +2.0 % a window, 8 of 13), was not predicted by
either avatar and is a null cell.

**Cattle.** The profile is flat: eleven of twelve placements between −0.22 and +0.40, and the
always-on control is the one in the programme that neither loses nor earns (+0.05 bp a day).
The supply calendar's set reads −0.05 / −0.22 / +0.16 and the feedlot-hedge set +0.21 / +0.05;
neither avatar's placements are where the return is. The best placement, February → April on
June/August (+0.63 / +0.84, +1.4 % a window, 10 of 13), sits one month before the supply set
and was predicted by nothing.

**The COT producer/merchant diagnostic** (no prediction was made): on hogs the producer net
short at formation orders the declared window's return (Spearman +0.52, p 0.07) and its change
through the window orders it the other way (−0.48, p 0.10) — a relation with two signs on
thirteen observations; on cattle +0.10 and −0.03. Recorded.

## 3. What this settles

- **The livestock avatars as written are not supported**, hogs' outright refuted. Two cells
  now exist on livestock — hogs December → February, cattle February → April — seen, unlicensed,
  each with two forward windows as its only test, like the three on the grains.
- **The closing clause fires.** No declared construction on any commodity root — corn, soybeans,
  wheat, oil, meal, hogs, cattle — is best of its own twelve placements. The seasonal-spread line
  on the commodity curve has **no open construction**. Whether it closes is the principal's
  (R15); the record's part is to say that after twenty records the line holds five seen cells
  and nothing pre-registrable with a clean test.
- **What every root shares** is not a schedule but a sign: the always-on short nearby spread
  loses on corn, soybeans, wheat, oil, meal and hogs, and is flat on cattle. The nearby
  strengthens against the deferred on average across the agricultural curve. That is a
  statement about carry, and the carry line is closed (D563).

**Lesson, recorded:** a mechanism-derived placement prediction with a named alternative is the
right shape for a Stage 0, and it was refuted cleanly here; when the prediction fails and the
profile's best cell was named by no avatar, the cell is a null result, not a lead.
