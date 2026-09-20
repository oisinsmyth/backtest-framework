# D571 STAGE 0 RESULT — the mechanism is **not supported**: the soybean placement profile predicted the best month on **corn and meal** and was **falsified on wheat and oil** — two of four, what chance gives; the profiles are root-specific. Corn's own structure is real and is a different pair: **short the old-crop September against the new-crop December, June → August, pays in 13 of 13** (+0.75 / +1.04) — a null cell, seen, not licensed. Meal's July placement is the one declared construction that is a candidate by the rule and it fails C-a (net +0.29). No entry.

*2026-09-20. Design committed in D571 (`935dfcf`) before this ran. Diagnostic: 2011 → 2023,
thirteen windows a placement; nothing from 2024-01-01 on was read on any source; no WASDE, no
COT. Runner `scripts/stage0_d571_cross_root_placements.py`, output
`data/stage0_d571_cross_root.json`, 19 s. The soybean source profile was recomputed and asserted
equal to D570's artifact to 1e-9. Six audits on each root's declared construction, each proven
to raise. **Erratum found and fixed here:** the shared contract-label helper printed a December
delivery month one year late (a December index is divisible by twelve); labels only — the
delivery-index arithmetic, every pair chosen and every return are unaffected, asserted by
re-running with the fix and comparing every number. D565's and D567's artifacts carry the
mislabel on December contracts in their pair tables; the numbers in them stand.*

---

## 1. The predictions against the profiles

Sharpe of the short spread, 2011–2023, by placement month (2016–2023 beside); the declared
construction in bold; the always-on control per positioned day.

| root | profile *m*1 → *m*12 | best (set predicted) | negatives predicted | control bp/day | Spearman with ZS |
|---|---|---|---|---:|---:|
| **ZC** | −0.52 −0.77 +0.16 −0.13 **+0.70 +0.75** +0.32 −0.12 −0.26 −0.13 −0.16 −0.74 | ***m*6** ({6, 7}) **holds** | *m*3 +0.16 fails; *m*9, *m*12, *m*1, *m*2 hold | −0.70 | +0.27 |
| **ZW** | +0.11 +0.18 +0.12 −0.02 +0.06 +0.11 +0.12 −0.06 −0.26 −0.13 −0.28 −0.19 | *m*2 ({4, 5}) **falsified** | *m*1–*m*3 positive: fail | −0.14 | −0.39 |
| **ZL** | −0.17 −0.55 +0.08 −0.22 −0.04 −0.40 **−0.69** −0.39 −0.29 +0.07 +0.33 +0.05 | *m*11 ({7, 8, 9}) **falsified**; *m*7 is the **worst** | fail | −0.80 | −0.14 |
| **ZM** | −0.24 +0.05 −0.02 −0.29 −0.36 −0.42 **+0.26** −0.67 −0.58 −0.16 +0.22 −0.03 | ***m*7** ({7, 8, 9}) **holds** | *m*2 +0.05 fails | −1.61 | +0.01 |

**Decision rule:** corn in its set (yes) *and* two of the other three in theirs (one) *and*
controls ≤ 0 (all four) → **NOT SUPPORTED.** Two hits of four is what a one-in-six and three
one-in-four chances deliver on average. The profiles' Spearman with soybeans' is +0.27, −0.39,
−0.14 and +0.01: no root's placement structure resembles the source's. The always-on short does
lose on every root — the nearby strengthens against the deferred on average in every grain — but
*when* it gives it back is the root's own calendar, and oil's calendar is the opposite of the
bean's.

## 2. The declared constructions, in full

| | **ZC *m*7**, Jul → Sep, Z/H | **ZW *m*4**, Apr → Jun, N/U | **ZL *m*7**, Jul → Sep, V/Z | **ZM *m*7**, Jul → Sep, V/Z |
|---|---:|---:|---:|---:|
| gross Sharpe / Sortino 2016–23 (SE) | +0.35 / +0.54 (0.25) | −0.01 / −0.01 (0.33) | **−1.13 / −1.42** (0.40) | **+0.42 / +0.77** (0.29) |
| net | +0.18 / +0.27 | −0.10 / −0.14 | −1.21 / −1.51 | +0.35 / +0.64 |
| 2011–23 gross | +0.32 | −0.02 | −0.69 | +0.26 |
| 24 positioned months: hit · median · worst | 0.50 · +0.03 % · −0.72 % | 0.58 · +0.03 % · −2.42 % | 0.33 · −0.15 % · −3.81 % | **0.67 · +0.26 % · −1.05 %** |
| per month, 2011–23 (mean · hit) | Jul +0.12 % · 0.62; Aug +0.25 % · 0.69; **Sep −0.01 % · 0.38** | Apr +0.11 · 0.62; May +0.21 · 0.77; Jun −0.37 · 0.46 | Jul −0.01 · 0.46; Aug −0.19 · 0.31; Sep −0.44 · 0.38 | Jul −0.13 · 0.38; Aug +0.00 · 0.69; **Sep +0.55 · 0.85** |
| rank of twelve, 2011–23 / 2016–23 | 9 / 9 | 5 / 4 | **0 / 0** | **11 / 11** |
| above the control per day | yes | no | no | yes |
| **candidate by the rule** | no | no | no | **yes** |
| dollar: net Sharpe · skew · σ positioned | +0.21 · +1.24 · $24 | +0.22 · −0.38 · $47 | −1.15 · −0.54 · $45 | **+0.29 · +6.95 · $68** |
| total · cost · max DD 2016–23 | +$329 · $296 · −$399 | +$679 · $296 · −$1,561 | **−$3,390** · $192 · −$3,504 | +$1,304 · $256 · −$2,154 |
| ledger | fails C-a | fails C-a | fails C-a, C-c | **fails C-a** |

**Meal** is the one declared construction that is positive, best of its twelve on both windows
and above its control: a candidate by the rule, and it fails C-a at +0.29 net with a dollar skew
of +6.95 that is one session. Its return is September (+0.55 % a month, hit 0.85); July loses;
and the placement one month later (*m*8, Aug → Oct) is the worst of its twelve at −0.67. A
construction whose neighbour is its own worst case is a September effect on meal, not a
three-month schedule, and the record enters it on the scored table and nowhere else.

**Oil** is the sharpest single fact here: the same crop, the same months, the opposite sign,
−1.13 on 2016–2023 with 2022 at −5.4 % and 2023 at −2.2 %. Soybean oil's nearby *strengthens*
against its deferred into harvest (biofuel demand against a seasonal crush, on the face of it;
not tested), and the bean profile said nothing about it.

## 3. What corn's profile says, seen now and not licensed

Corn's best placements are *m*5 and *m*6 — formed at the end of April or May, holding through
July or August — and the pair the rule picks there is **September against December: the
old-crop contract against the new-crop**, short the old crop. That is not the bean object (new
crop against the next deferred); it is the old-crop premium collapsing as the new crop's size
firms:

| corn placement | months | pair | Sharpe 2011–23 / 2016–23 | bp a day | window mean · short pays |
|---|---|---|---:|---:|---|
| ***m*6** | Jun–Aug | **U/Z** | **+0.75 / +1.04** | +3.45 | **+2.27 % · 13 of 13** |
| *m*5 | May–Jul | U/Z | +0.70 / +0.80 | +3.07 | +2.02 % · 10 of 13 |
| *m*7 (declared) | Jul–Sep | Z/H | +0.32 / +0.35 | +0.54 | +0.35 % · 10 of 13 |

Thirteen of thirteen at +2.3 % a window, on a pair whose two legs are two different crops. This
is D567's weather-premium decay (the new-crop December falls June → August in non-drought years)
seen from the spread side, where the drought years do not hurt because the old crop rallies
with the new. **It was not the declared construction, it is seen for every placement now, and it
is not licensed by this record.** If it is built on, it is written as seen with corn's 2024+
slice — two summers — as the only test, the position soybeans are in; the record says so.

## 4. What this settles

- **The soybean July placement was the soybean curve.** The prediction that its profile
  transfers to other row crops failed at chance level and was falsified outright on two of
  four. Placement profiles are root-specific; the mechanism as written in D571's design is not
  supported and the record closes *that claim*, not any root.
- **What every grain shares** is the always-on sign: the nearby strengthens against the deferred
  on average, so a short nearby spread held year-round loses on all five roots. That is a
  statement about the carry structure of grain curves, not a schedule.
- **Three seen, unlicensed cells now exist on the grains:** corn's U/Z June → August (13 of 13),
  soybeans' X/F July → September (+1.24), meal's V/Z September (hit 0.85). Each would be a
  pre-registration as seen with two forward windows to test it. None is asked for here.

**Lesson, recorded:** predicting one root's placement from another's profile is a real
out-of-sample test and it failed; the profile is a property of the root's contract calendar and
its crop, and the honest generalisation across roots was the sign of the always-on control, which
held on all four and was the one prediction that was not about a month.
