# D571 STAGE 0 DESIGN — the cross-root placement profiles: the same short-spread construction placed at every calendar month on **corn, wheat, soybean oil and soybean meal**, with the **best placement and its sign predicted from the soybean profile before any of them is read**

**Stage 0 design, committed before the runner exists. Diagnostic on 2011 → 2023; the 2024+
slice is not read on any source.** Nothing admitted (R15). *This design is a pre-registration in
substance for one declared construction per root: the placement is predicted here from another
root's profile, the construction is fixed in writing, and the runner reports the full line — the
statistic, the enumerated placement null, the control, the dollar book. The RESULT is the record
any ledger disposition stands on.*

*2026-09-20. D570 pre-registered the soybean harvest spread on the F/H pair and it did not pass
because its own twelve-placement null found the real window two months earlier: the same
construction — a survivable nearby pair, short the nearer, held three months — earns +1.24 on
2016–2023 formed at the end of June and +0.40 formed at the end of August, and loses at every
winter and spring placement. That profile is now seen for soybeans, so nothing on soybeans has
an in-sample test left. But the thing the profile describes is a mechanism, not a window: a
short spread on the new-crop contract against the next deferred, formed while the crop's size is
still open, pays into harvest and loses the rest of the year. That claim has unseen data on
every other row crop on the strip. This design writes the prediction down for each of them,
then reads them once.*

**What has been seen.** The full soybean profile (D570, all twelve placements, both windows);
D567's Stage 0 windows on corn (Z/H over Sep–Nov: the short *loses*, 4 of 13; Z/H over Jun–Aug:
the short pays 10 of 13, −0.39 %; H/K over Dec–Feb) and wheat (U/Z over Jun–Aug: 7 of 13,
−0.30 %; Z/H over Sep–Nov); D568's corn calendar profile of the *rolled* cousin (the long spread
pays in April and June, loses in July). **Not seen:** the fixed-pair construction's placement
profile on corn, wheat, oil or meal at any month; any statistic of oil or meal spreads at all.
The corn June and September placements are partly constrained by the seen windows (the design's
pairs differ from D567's at June — U/Z, not Z/H — and coincide at September); the predictions
below are made with that stated.

---

## 1. The construction, fixed

At the last session before calendar month *m*: **T1 = the first listed delivery month strictly
after the third holding month, T2 the next listed**; **short T1 / long T2**, one contract a leg,
held on every session of months *m*, *m*+1, *m*+2; flat otherwise; the pair fixed for the window
(D570's `fixed_pair_series`, D564's five-session formation read). Twelve placements a root,
*m* = 1 … 12. Daily return `−(r1 − r2)` with flat sessions as zeros. The **always-on control** is
the rule-rolled cousin (delivery ≥ *m*+2, re-read monthly), short, every month — the same object
D569 and D570 used — scored per positioned day.

Contract months: corn and wheat H K N U Z; oil and meal F H K N Q U V Z. Full contracts, no
micros (the breadth meta says so for all four); $50 a point on corn and wheat (tick $12.50),
$600 a point on oil (tick $6), $100 a point on meal (tick $10); $6 a round trip plus one tick a
leg a side, four sides a window.

## 2. The predictions, from the soybean profile, before reading

The soybean profile: best *m*7 (Jul → Sep, X/F: the new-crop November against January, formed
when the crop is planted and its size open), then *m*8, then *m*9; *m*5 and *m*6 flat; *m*10 flat;
*m*11 → *m*4 and *m*12 negative for the short. The always-on short loses. The mechanism reads:
the nearby is bid up against the deferred through the growing season and the new crop releases
it from the first new-crop delivery month backward.

| root | crop calendar | **declared construction** | predicted best placement (set) | predicted negative placements | falsifier |
|---|---|---|---|---|---|
| **ZC corn** | planted Apr–May, pollinates Jul, harvest Sep–Nov; new crop Z | ***m*7: Jul → Sep, Z/H** | **{6, 7}** (the June placement holds U/Z, old crop against new; the July placement holds Z/H, new against next) | *m*9 ≤ 0 (seen: the harvest spread narrows); *m*12, *m*1, *m*2, *m*3 ≤ 0 | best placement outside {5, 6, 7, 8}, or *m*7 ≤ 0 |
| **ZW wheat (SRW)** | planted Sep–Oct, heads Apr–May, harvest Jun–Aug; new crop N | ***m*4: Apr → Jun, N/U** | **{4, 5}** (formed at the end of March or April, the crop's size open into heading) | *m*1, *m*2, *m*3 ≤ 0 | best placement outside {3, 4, 5, 6}; **lower confidence, stated**: D567 found wheat at full carry at harvest in 8 of 13, and a curve already at full carry has less to widen |
| **ZL soybean oil** | the bean crop's calendar | ***m*7: Jul → Sep, V/Z** | **{7, 8, 9}** | *m*12 → *m*4 ≤ 0 | best outside {6, 7, 8, 9}; Spearman of the twelve-placement profile with soybeans' **< 0.3** |
| **ZM soybean meal** | the bean crop's calendar | ***m*7: Jul → Sep, V/Z** | **{7, 8, 9}** | *m*12 → *m*4 ≤ 0 | as oil; oil and meal share the crop and count as one and a half roots, not two |

All predictions on the 2011–2023 Sharpe of the twelve placements (the Stage 0 window; thirteen
windows a placement); the 2016–2023 values reported beside. **The always-on control is predicted
≤ 0 per positioned day on all four roots** (the nearby strengthens outside the window).

**Chance.** With twelve placements, a two-month set is right by chance one time in six, a
three-month set one in four. The joint chance of corn and wheat both landing in their sets and
oil and meal both in theirs is about 1 in 576; oil and meal are not independent of each other
and the record will say so.

## 3. The decision rule, declared

- **The mechanism is supported** if corn's best placement is in {6, 7} **and** at least two of
  wheat, oil and meal land in their sets, **and** the always-on control is ≤ 0 on those roots.
- **A root's declared construction is a candidate** if it is positive on 2016–2023, the best of
  its own twelve placements on 2011–2023, and above the always-on control per positioned day.
  For such a root the RESULT reports the full line — gross and net Sharpe / Sortino with monthly
  block-bootstrap SE, the positioned months, per window, per month, the dollar book at one
  contract with C-a / C-c / C-d — and enters it in `COMPONENTS_PROP.md` on its numbers, the
  twelve placements being its enumerated null (under D468, a component that clears C-a and is
  best of twelve is entered; one that clears C-a but is not best is PROVISIONAL at most).
- **Corn's best placement outside {5, 6, 7, 8}:** the soybean profile was the soybean curve;
  the line is recorded as a seen finding and nothing is built on it without the principal.
- **Placements not declared as constructions** (whatever their numbers) are null cells, seen
  once this runs, and not licensed.

## 4. Reported beside, diagnostic

Per root: the twelve-placement table (Sharpe 2011–2023 and 2016–2023, Sortino, mean per
positioned day, per-window hit, the pair of the first window, windows scored); the always-on
control's Sharpe and per-day return; the Spearman of each root's profile with soybeans'; the
soybean profile reprinted from D570's artifact as the source. The audits of D570 on each root's
declared construction (pair by a second path, survival, held-contract, lag, sign in money for a
short spread, right quantity), each proven to raise; the placement-*m* series asserted to
reproduce the declared construction's series exactly.

## 5. What is read, and what is not

The settlement strip for ZC, ZW, ZL, ZM (and ZS, seen, for the source profile) 2010-06 →
2023-12-29; the breadth fixture for the calendar and the specifications. No WASDE, no COT.
**Not read: anything from 2024-01-01 on, on any source.**

## 6. What this record does not do

No gate; no sizing; no netting across roots; no re-placement after reading. A construction that
is a candidate here is confirmed only by its root's 2024+ slice, on the principal's word.
