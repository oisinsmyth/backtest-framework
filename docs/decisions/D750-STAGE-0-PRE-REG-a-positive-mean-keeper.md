# D750 STAGE 0 PRE-REGISTRATION — a positive-mean keeper: D748's index-micro keeper with a \$40 stop cap, held to mean net > 0 at t ≥ 2 and to its rotation null

*2026-10-01.*
- *The principal's request: "scavenge a 'dead'/Closed strategy that has real gross edge nearly all the time but
  didn't profit and barely broke even … a strategy like that would have a mean trade of >= 0". Then "+mean".*
- *The principal's choices:*
  - **"Mean > 0, at t ≥ 2"**;
  - **"\$40 cap, keep the −\$50 limit"**;
  - then, asking "Why not both net median and mean >=0?", **"Both mean and median"**.
- *Numbered D750. D749 went to the documentation-review session (the principal's month-end fix oracle), which had the principal's word first.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29).*

## 0. Why this one, and what is already seen

**The goal.** D748's keeper is M6E, whose mean can only be its fee (about −\$4 a trade). A keeper with a positive mean
must carry an edge.

**The edge on file.** D736's screen of 174 on-file blocks shows that the ones with real gross edge and a high duty
cycle are NQ's continuation from the open:
- D727's follow at every clock;
- D731's 13:30 entry (+\$11.17 a trade held to the close);
- D735's legs.

**Why none of them can serve as a keeper as they stand.** They hold an index micro for hours, so a single trade risks
hundreds of dollars against the keeper's −\$50 limit.

**What D748 already showed (seen, POST HOC here).** Its variant I is exactly this direction rule at this clock: the
move since 09:00, 13:30–14:00, the index micro with the smallest forecast σ\$.
- **Uncapped:** gross +\$3.4 to +\$3.6 a trade on the keeper's fire days, mean net about −\$0.2 to −\$3.6.
- **But its worst trade was −\$102:** NOT READY.

**This record asks whether a hard \$40 stop keeps that worst case inside the limit while the mean stays above zero.**

**The contamination, stated plainly:**
- the direction and the clock come from D727/D731, which were read in-sample;
- D748 read this exact construction uncapped.

So an in-sample pass here is **weak evidence: selection of a known in-sample effect.** It makes a candidate, not a
replacement for M6E (§6).

**R15.** The NQ follow was closed **as a component** by the principal (D738–D742). It is reused here **as a keeper**,
at the principal's request. Nothing about the follow's status as a component changes.

## 1. Data, costs, and the frame (as D748, read-only)

**Everything is D748's frame, reused read-only:**
- the bars, calendar, costs (the `d508_exec` line, D748-A1), windows and forecasts;
- the deadline engine and the breach checker, through `scripts/stage0_d748_activity_keeper.py`'s functions, imported
  and not edited;
- the component calendars, `data/d748_component_books.csv`.

**Run on the system interpreter.**

## 2. The construction (fixed now)

| | |
|---|---|
| **clock** | enter at bar 54's open (13:30 ET), time exit at bar 59's close (14:00) |
| **roots** | M2K, MYM, MES, MNQ: the one with the smallest forecast σ̂\$ (D748's forecast) among those whose window is complete and not early-close |
| **direction** | sign(open₅₄ − open₀) on the chosen root, long on zero (D748's rule) |
| **stop** | **min(4 σ̂\$, \$40)** converted to points, checked on bars 54–59's high and low; exit at the stop **minus one tick** |
| **cost** | one round trip at the micro's `d508_exec` line |

**The known answer:** the cap is the only change. With it disabled (an infinite cap), the runner must reproduce
D748's variant-I readings exactly:
- K1 −\$102.46094;
- K2 −\$174.82524;
- K3 \$99.61942;
- K4 0;
- and I|NONE|C7's 384 fires.

## 3. The tests

**The edge, on every eligible session** (more power than the fire days alone):
- **Eligible:** an ES trading session, not FOMC, not an early close, with a candidate whose window is complete and
  whose forecast has 20 prior sessions.
- **The span:** from the first session with a warm forecast (bars from 2016-01-01) to 2023-12-29.

| | criterion |
|---|---|
| **E1** | mean net per trade **> 0 with t ≥ 2** (t = mean ÷ (sd ÷ √n); sessions do not overlap) |
| **E2** | the observed mean net beats the **exact circular rotation of the direction series** over the eligible sessions. Each session keeps its root, window and stop, and only the direction label shifts. Every offset is enumerated; p_high = the share of offsets with mean ≥ the observed (offset 0 included) **≤ 0.05** |
| **M1** | the **median net per trade ≥ 0** on the same sessions (the principal's: more trades win than lose after the fee). A point statistic, with no test attached; its rotation-null p50 and p95 are reported beside it |

**The keeper's limits, on D748's calendars and cadences** (2018-05-14 → 2023-12-29): D748's K1 worst trade ≥ −\$50,
K2 worst 30 days ≥ −\$150, K3 ≤ \$300 a year on the most frequent cadence under NONE, and K4 zero breaches.

## 4. The reading (declared now)

- **POSITIVE KEEPER:** E1, E2, M1 and K1–K4 all hold.
- **NOT POSITIVE:** any fails; the failing ones are named. The keeper stays M6E, as written in `BOOK_PROP.md`.

**Reported, not in the rule:**
- **The four groups:**
  - net and gross per trade, with Sharpe and Sortino of the all-session line;
  - mean, median, win rate, the stop-hit rate, the 1 %-trimmed means (ex-top, ex-bottom, both);
  - per-year mean net and the years positive;
  - E2's null p50 and p95.
- **The same statistics on the keeper's fire days**, per calendar, beside D748's M6E (variant M).
- **The uncapped version** beside the capped one: what the cap costs in mean.
- **The root shares.**

## 5. Assertions (each canary must raise in the self-test)

1. **The known answer:** D748's variant I reproduced exactly with the cap disabled (§2).
2. **The cap:** on a planted path whose adverse excursion exceeds \$40, the loss is exactly \$40 + one tick + cost.
   On a path inside 4σ̂, the cap is not touched.
3. **Sign in money** (a long trade on a rising window pays positively), through D748's `trade_pnl` logic with the cap.
4. **The rotation:**
   - offset 0 equals the observed mean;
   - a planted series whose direction always matches the window's move gives p_high < 0.01;
   - the vectorised rotation equals a loop over 50 offsets exactly.
5. **The seal:** nothing on or after 2024-01-01 is read (D748's assertions).

## 6. After the reading

**POSITIVE KEEPER:**
- It is a **candidate** to replace M6E in the BOOK_PROP execution rule.
- **It is not switched on this record.** The evidence is contaminated (§0). It needs:
  - a **forward read** on the recorder's bars, once at least 100 eligible forward sessions exist (the recorder keeps
    NQ, YM and ES, so the forward root set is MYM, MES and MNQ, reported as such);
  - and the principal's word.
- **An index keeper falls under BOOK_PROP's precedence amendment:** an arm's call always comes first, and same-root
  calls are resized and handed over.

**NOT POSITIVE:** M6E stays. The record names what failed:
- **E1/E2:** the edge does not survive a 30-minute hold at a \$40 cap net of the fee;
- **M1:** most trades lose after the fee, even if the mean does not;
- **K1–K4:** the risk.

## 7. Predictions (Opus)

- **P1:** gross mean on all eligible sessions +\$2 to +\$4 (D748 I's fire-day gross was +\$3.4 to +\$3.6, uncapped).
- **P2:** the cap raises the stop-hit rate to 3–8 % (from about 1 %) and lowers gross by \$0.5–1.5.
- **P3:** **E1 fails.**
  - Cost is about \$3.8 on M2K/MYM, so net is near −\$1 to +\$0.5.
  - With sd about \$25 and n about 1,800, SE is about \$0.6, so t ≥ 2 needs net ≥ +\$1.2.
  - P(E1) ≈ 0.2.
- **P4:** E2 passes on gross if not on net, P ≈ 0.5. The follow is a real effect on NQ, but this is a different window
  and root mix.
- **P5:** K1–K4 hold. The cap makes K1 about −\$44 by construction; K2 is close to −\$150.
- **P6: M1 fails.** The median gross of a small continuation tilt sits near its mean, below the \$3.8 fee; D748's
  uncapped index version had a median net of −\$0.76 to −\$1.05 on its fire days. P(M1) ≈ 0.15.
- **P(POSITIVE KEEPER) ≈ 0.08.**
