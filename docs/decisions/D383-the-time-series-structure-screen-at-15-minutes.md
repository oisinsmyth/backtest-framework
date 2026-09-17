# D383 — the time-series market-structure screen at 15 minutes

**Date:** 2026-09-08
**Kind:** **STAGE-1 SCREEN (R14), signal hunt under R15.** Admits nothing. **Reads no holdout, and installs a guard that cannot.**
**Pre-registered under R8 — committed before the runner exists. Result committed separately.**
**Prerequisite, already done:** `etf_intraday_15m_raw` gated by `scripts/gate_intraday_fixture.py` (`3c9d57c`) — the first intraday fixture in this repo to carry a gate the loader accepts.

---

## 0. Why this is not a rerun of D382

[D382](D382-RESULT-nothing-clears-on-the-stable-statistic-and-the-books.md) screened
these same 19 features and closed: nothing cleared on the segmentation-stable statistic, and **the
permutation floor sat above the rotation floor at every hold** — randomising *which names* occupy the
extreme decile produced a **better** per-bar book than the real feature.

**That is specifically a CROSS-SECTIONAL failure**, and it is why this study changes the hypothesis
rather than the frequency alone:

| | D382 | **D383** |
|---|---|---|
| the comparison | this ETF's `lower_wick` against **the other 550 ETFs today** | this ETF's `lower_wick` against **its own trailing W bars** |
| what an event means | a cross-sectional rank | a time-series extreme |
| what D382's failure says about it | **nothing** — it tested the other one | |

**And the cross-section here would be hopeless anyway:** 57 symbols, so an "extreme decile" is ~6
names, against D382's ~55. **The cross-sectional test is not merely redundant at 15m, it is weaker.**

**A wick rejection is a property of that bar in that name.** It is not a rank against 56 other ETFs,
and it never was — D382 tested the only version the daily panel's breadth supported.

---

## 1. The fixture and the split

**`data/fixtures/etf_intraday_15m_raw.csv.gz`** — 57 ETFs, **3,194,849 rows**, 15-minute RTH bars,
**2018-01-02 → 2026-08-26**, ~56,056 bars per symbol, median 26 bars per session, short-session rate
0.000%. Gated `3c9d57c`: `gate_i1` grid, `gate_i2` OHLC, `gate_i3` intra-session move, `gate_i5`
overnight gap — **all clean**, with three flagged moves adjudicated against evidence and recorded.

| | |
|---|---|
| **MINING** | first bar → **2023-12-31** |
| **RESERVED** | **2024-01-01 → 2026-08-26. Untouched.** |

**`[SPLIT]` is default-deny with no override**, as in D382: the panel is truncated at the boundary and
**the bar lists are cut as well as the grids**, because the structure machine and the gap scan read
`cleaned` rather than the grids. R14 puts the holdout at stage 4 or not at all, and this is stage 1.

### AMENDMENT to §1, 2026-09-08 — **the fixture and the loader named above are the wrong pair, and the pairing FAILS SILENTLY. The fixture is the PANEL and the loader is `load_panel`.**

*Written before the runner exists, so it is still a pre-registration under R8 rather than a
correction to a result. §1 above is left standing because it has already been quoted.*

**THE DEFECT.** §1 names `etf_intraday_15m_raw.csv.gz` and the design assumes
`ragged_panel.load_ragged`. **`load_ragged` builds its date grid from `timestamp[:10]`** —

```python
rows.setdefault(r["symbol"], []).append((r["timestamp"][:10], ...))
grid = sorted({d for s in symbols for d, *_ in rows[s]})
```

— the **calendar date**. Fed a 15-minute fixture it collapses every intraday bar of a session into
**one grid slot and keeps the last write.** Counted directly, distinct timestamps against distinct
dates:

| | symbols | union **timestamps** | union **dates** | bars per symbol | through `load_ragged` |
|---|---:|---:|---:|---:|---:|
| `etf_intraday_15m_raw` | 57 | **56,056** | **2,156** | 55,778 – 56,056, **ragged** | **57 × 2,156** |
| `etf_intraday_15m_panel` | 57 | **55,726** | **2,156** | 55,726, **rectangular** | **57 × 2,156** |

**2,156 is the trading-day count.** So `load_ragged` on either file returns a **daily panel of
session closes** — one bar in 25.8 discarded — **with no error, no warning, and every assertion in
§6 still passing.** `[LAG]`, `[TS]` and `[SPLIT]` are all true statements about a daily grid. A
15-minute study would have been run, reported and believed at daily resolution. **`assert_gates_passed`
already records why this class of defect lives at the loader — "THE LOADER IS THE CHOKEPOINT EVERY
STUDY GOES THROUGH" — and this is the same chokepoint failing on FREQUENCY rather than on gates.
`load_ragged`'s whole contract is written in dates (`RaggedPanel.dates`, "a symbol contributes only
between its own first and last bar", "no forward-filling"), it was built for D252's daily
dead-inclusive fixture, and it has no notion of a bar that is not a session. Nothing downstream can
notice.**

**THE CORRECTION.** Both lines of §1 are replaced, and nothing else in this record is:

| | **§1 as written** | **as amended** |
|---|---|---|
| fixture | `data/fixtures/etf_intraday_15m_raw.csv.gz` | **`data/fixtures/etf_intraday_15m_panel.csv.gz`** |
| events | `..._raw_events.json` | **`etf_intraday_15m_panel_events.json`** |
| loader | `ragged_panel.load_ragged` | **`run_macd_ladder.load_panel`** |

**`load_panel` is the right loader because it refuses what `load_ragged` accepts.** It requires
equal bar counts across symbols and raises otherwise — which is precisely why
`scripts/build_intraday_panel.py` exists and why it iterates its cleaned timestamp intersection to a
**fixed point** (removing a bar can change whether its neighbours clean). Verified by running it:
**57 × 55,726, 1,955 dividends matched and 0 unmatched.**

**Two things about `load_panel` that this study must handle rather than inherit:**

1. **It does NOT call `assert_gates_passed`.** `load_ragged` does; `load_panel` does not. So `[GATE]`
   in §6 is **an explicit call in the runner**, not a property of the load. It is not a weakening of
   the check — never `require_gates=False`, and the panel now has a gate to check (below).
2. **`panel.dates` is date-only** — `b.timestamp.date().isoformat()`, so it has the right length
   (55,726) and each value repeats ~26 times, losing the time of day. The 2023-12-31 boundary is a
   date comparison and is safe on it, but **anything needing bar-of-session or a calendar hold in
   §5.3 must read `cleaned[sym][j].timestamp`, never `panel.dates[t]`.**

**THE GATES. `3c9d57c` is unaffected and is not being reinterpreted.** `scripts/gate_intraday_fixture.py`
reads the CSV directly with its own row reader, so it genuinely saw all 3,194,849 raw rows; its
verdict on the raw fixture stands exactly as §1 records it. **What was missing is that the panel —
the file this study will actually load — carried no meta at all, so no loader would accept it.** It
now carries its own gate, recomputed from the panel and never read from a meta (D256), **with the
gate script unmodified**:

> 57 symbols, **3,176,382 rows**; `gate_i1` grid **0**, `gate_i2` OHLC **0**, `gate_i3` intra-session
> move **0**, `gate_i5` overnight gap **0**. Session shape, reported and not gated: 122,892 sessions,
> **median 26.0 bars**, p05 25.0, short-session rate **0.000%**.

**No new adjudication was required, and that was checked rather than assumed.** Re-run with the
allow-list emptied, the panel flags **exactly four** moves — GDXJ 2020-03-19 (|log| 0.168), USO
2020-04-02 (0.159), OIH 2020-03-09 (0.277), XOP 2020-03-09 (0.277) — **every one already adjudicated
against evidence for the raw fixture** and every one naming what corroborates it. Nothing was
excluded, no threshold was widened, and the fifth entry (USO 2020-03-09) is carried but inert here
because the cleaned intersection dropped the bar pair that produced it.

**THE SPLIT, RE-STATED AGAINST THE PANEL'S OWN BAR GRID.** The boundary is unchanged; what changes
is that it is now quoted in bars that exist:

| | | bars per symbol | sessions |
|---|---|---:|---:|
| **MINING** | first bar → **2023-12-31** (last bar present: 2023-12-29 15:45) | **38,648** | **1,497** |
| **RESERVED** | **2024-01-01 → 2026-08-26 15:45. Untouched.** | **17,078** | **659** |
| | | 55,726 | 2,156 |

**`[SPLIT]` stays default-deny with no override** — there is no flag that widens it. The **bar lists**
are cut, not merely the grids, and the cut must be **proved to have bitten** (a cut that removes
nothing guards nothing) and proved to have left nothing on or after 2024-01-01. Both checks, and
their deliberate failures, are already exercised in `scripts/d383_span_census.py --selftest`.

**Everything else in this record is unchanged**: the hypothesis, the 25 feature-directions × 6
windows × 4 holds, the two nulls, the §5 reporting set, the §6 assertions and the §7 predictions.
What changes is the object they are computed on — **57 × 55,726 fifteen-minute bars, not 57 × 2,156
daily closes.**

---

## 2. The construction

**Long-flat, equal-weighted, per name, `lag = 1`** — exposure through bar *t* is decided on *t−1*'s
close. Flat by default, in on a signal, out on a fixed hold. The shape the principal asked for, and
S1's shape.

**The event.** For feature `x`, name `i`, window `W`: the **percentile of `x[i,t]` within that name's
own trailing `x[i, t−W .. t−1]`** crosses into the declared extreme decile. **No cross-sectional
comparison is made anywhere.**

**The lookback windows — six, log-spaced, REPORTED AND NEVER PICKED:**

| bars | 26 | 52 | 130 | 260 | 390 | 780 |
|---|---|---|---|---|---|---|
| **sessions** | 1 | 2 | 5 | 10 | 15 | 30 |
| **calendar** | 1 day | 2 days | 1 week | 2 weeks | 3 weeks | 6 weeks |

**Six rather than three, on [R14's addition of 2026-09-08](../RULES.md#r14).** The window is a free
parameter and the point of sweeping it is to **read the shape**: monotone, smooth hump, or knife-edge.
Three points can only distinguish monotone from not. **And the multiplicity cost is sublinear because
neighbouring windows are near-duplicates** — measured in D382, whose best-of-38 floor ran p50 +185.02
/ p95 +190.01 / max +192.32, a 4% spread from median to maximum across 38 correlated cells.

**Holds, reported in CALENDAR units per [D163](D163-sub-hourly-is-a-turnover-measurement-not-a-result.md):**
**4 bars (1 hour), 13 (half session), 26 (one session), 78 (three sessions).** **Reported, never
picked** (R14, 2026-09-03). **26 is nominated primary in advance** so one number can be quoted
without selection.

---

## 3. Gate 1h, declared properly this time

**D382 failed gate 1h** — it declared the book long and never said which *end of each feature* goes
long, so both tails were scored and the floor doubled. **Here every direction is declared from the
feature's own definition in code, with its mechanism, before the run.**

| feature | long end | mechanism |
|---|---|---|
| `upper_wick` = (H−max(O,C))/rng | **LOW** | a large upper wick is a rejection of the highs — bearish |
| `lower_wick` = (min(O,C)−L)/rng | **HIGH** | a large lower wick is a rejection of the lows — bullish |
| `wick_asym` = (upper−lower)/rng | **LOW** | positive is upper-dominant, i.e. bearish |
| `body_frac` = (C−O)/rng | **HIGH** | positive is an up bar; continuation |
| `close_in_range` = (C−L)/rng | **HIGH** | closed near the high |
| `gap_frac` = O/prevC − 1 | **LOW** | buy the gap down; gap reversion |
| `struct_trend` ∈ {−1,0,+1} | **HIGH** | +1 is the uptrend state |
| `retrace_leg` | **HIGH** | a deeper retracement inside structure is the dip to buy |
| `fvg_signed` | **HIGH** | an unfilled gap below is support |
| `dist_hvn` = (px−HVN)/bw | **LOW** | price below the high-volume node — below value, which acts as a magnet |
| `mass_imbalance` = (above−below)/tot | **LOW** | negative means more volume below: support beneath, not supply above |
| `gap_reversal` = −intraday/gap | **HIGH** | the overnight gap reversed during the session |
| `mass_here` | **HIGH** | price sits where volume has been accepted — value support |

**Six features are UNDECLARED, and that is stated rather than guessed:**
`range_frac`, `park_vol_21`, `gk_minus_cc` (volatility magnitudes and an overnight-contribution probe
— **not directional quantities at all**), and `fvg_dist`, `choch_dist`, `dist_lvn` (**unsigned or
genuinely ambiguous distances**). **Both tails are scored for these six and priced as a best-of-2 for
those features only** — the gate-1h cost is localised rather than paid across the whole grid.

**Grid: 13 declared + 6 × 2 undeclared = 25 feature-directions × 6 windows × 4 holds = 600 cells.**

---

## 4. The nulls, and why they are not D382's

**D382's within-bar permutation tested a cross-sectional claim and does not apply here.** Permuting a
score across names says nothing about a signal that never compares names. Substituted:

| | what it randomises | what it catches |
|---|---|---|
| **rotation** | each name's position series, rolled **within its own live window** | a signal whose timing carries nothing |
| **matched-count random entry** | *which bars* a name enters on, at **that name's own entry count** | a signal that picks no better bar than a dart |

**The floor is best-of-150 WITHIN EACH HOLD** (25 feature-directions × 6 windows), under **one shared
draw** per iteration. **Never across holds** — D382's correction, because a 78-bar hold earns roughly
20× a 4-bar hold per trade by construction and a cross-hold max is set entirely by the longest.

---

## 5. What is measured

**Primary (R15):** gross mean per trade, against the §4 floors.

**Reported beside it, and the first two are not optional:**

1. **bp per BAR HELD.** D382 found the per-trade mean is inflated by **event density** as well as
   hold — overlapping events merge into one run, and a nominal 40-bar hold produced **306-bar** runs.
   The per-bar rate is the segmentation-stable companion and both are always shown.
2. **Excess over BUY-AND-HOLD at matched exposure.** D290: fifty of fifty-one long-only books are
   market drift. `[BH]` refuses to report an excess without a matched comparator.
3. **Turnover, entries per year, and median hold in CALENDAR time, before any performance number** —
   [D163](D163-sub-hourly-is-a-turnover-measurement-not-a-result.md)'s standing requirement for
   sub-hourly work, and at 15m it binds hard: a 4-bar hold is ~1 hour and pays a full round trip.
4. **The SHAPE across the six windows**, per feature — monotone, hump, or knife-edge. **A cell that
   survives at one window and dies either side is reported UNRESOLVED, not as a result.**
5. Gate 1e capturability, and gate 1d′ against S1/S2 with the pool named — **only if something
   survives §4**, and reported as not-computed otherwise rather than silently omitted.

---

## 6. Assertions

`[SPLIT]` (bar lists cut, not only grids; default-deny), `[GATE]` (the loader's own check, on a
fixture gated `3c9d57c`), `[LAG]` (exposure through *t* decided on *t−1*, re-derived by a second
implementation that never calls the position builder), `[TS]` (**the trailing percentile reads only
`t−W..t−1` and never bar `t` itself** — the look-ahead this construction invites, proved on a probe
where bar `t` is set to an extreme and the percentile must not move), `[DIR]` (each declared direction
scored as declared; the reversed book reported separately), `[BH]`, `[POS]` (the fast position builder
equals the loop builder), `[X]` — **every audit raises on a deliberately broken book, including a
percentile that peeks at bar `t` and a panel carrying a reserved-window bar.**

---

## 7. Predictions

| | |
|---|---|
| **Q1** | **nothing clears both floors on bp-per-bar at any hold.** D382's negative was cross-sectional, so this is a genuinely new test — but the prior from D290, D382 and every long-only book here is drift |
| **Q2** | **the window sweep is FLAT, not humped.** If these features carry information it should not live at one scale; a hump would be the interesting outcome and a knife-edge the suspicious one |
| **Q3** | **the shortest hold (4 bars ≈ 1 hour) has the best bp-per-bar and the worst net**, because D378 found the edge front-loaded and D380 found short holds annihilated by turnover — at 15m both effects are stronger |
| **Q4** | **turnover kills any survivor before cost is even a gate.** Entries per year at hold 4 will be an order of magnitude above the daily study's |
| **Q5** | **at least one UNDECLARED feature scores better reversed than declared** — a direct check that the §3 declarations are honest rather than fitted |
| **Q6** | `[TS]` and `[SPLIT]` both hold on the first run |
| **Q7** | **AGAINST myself: if anything survives, it is axis D (volume profile)**, which topped D382's excess table and is the axis never screened anywhere before that study |

---

## 8. What would make me abandon this

- **`[TS]` fails** → the trailing percentile reads bar `t`. That is look-ahead in the signal itself;
  stop, fix, publish nothing.
- **`[SPLIT]` fails** → a reserved bar reached a score; treat the reserved window as compromised.
- **Nothing clears §4 on bp-per-bar** → the features carry nothing at this frequency either, and the
  family is closed on both constructions. **Write it as the close; do not sweep more windows.**
- **Everything clears** → R7's corollary: a hurdle everything clears is a broken hurdle, not a
  discovery. Suspect the null before the result.

---

*Pre-registered 2026-09-08. Runner does not exist at the time of this commit (R8). The reserved
window is guarded default-deny with no override.*
