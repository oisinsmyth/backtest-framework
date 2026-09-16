# D259 — The extended session, and what is inside the overnight gap

**Status:** Measurement record — no rule proposed, no cell scored, no hurdle claimed
**Date:** 2026-09-01
**Area:** Data layer / Strategy research

---

## Why this record exists

[D247](D247-the-short-side-at-fifteen-minutes.md) measured **+8.59%/yr overnight against
−0.36%/yr intraday** and that measurement now carries weight it was never built to carry.
[R11](../RULES.md)'s amendment established that MyFundedFutures permits a position opened at
the 18:00 ET Globex open and held to 16:10 ET the next day, which makes
[D258](D258-the-prop-track-candidates.md)'s candidate C1 live rather than a loophole — and
which moves the binding constraint from P2 to **P1, a 4% trailing drawdown measured on OPEN
equity.**

**P1 measures the path. D247's +8.59% has no path.** It is a close-to-open gap with no
interior, so it cannot say anything about what a position living through that period would
have experienced. R11 stated the gap in the evidence explicitly: *"the drift may be the same
while the path — which is what P1 measures — is entirely different."*

`docs/alpha_vantage_api.md` then established, by probe, that `TIME_SERIES_INTRADAY` with
`extended_hours=true` serves **~64 bars/session over 04:00–19:45 ET** back to 2010, against
the 26 bars over 09:30–15:45 the existing `etf_intraday_15m` fixture holds. **The overnight
gap has an interior after all, for 16 of its 24 hours.** This record is the measurement of
that interior.

**It is a measurement and nothing else.** No rule is proposed, no cell is counted, no hurdle
is claimed cleared, and the ledger does not move.

---

## What was built

`scripts/fetch_index_extended.py`, a sibling of `fetch_etf_intraday.py` in the same
`--plan / --probe / --fetch / --actions / --build` shape, sharing the same raw slice cache.

| | |
|---|---|
| symbols | **SPY, QQQ, IWM, DIA** — the index products with futures analogues ES/NQ/RTY/YM |
| span | **2010-01 → 2026-08**, 200 months, one request per (symbol, month) |
| fixture | `index_extended_15m_raw.csv.gz` — **958,217 bars, 16,748 symbol-sessions** |
| session | **04:00–19:45 ET, 64 slots**, median **62** bars/session against 26 for regular hours |
| requests | 800 planned, **421 already cached** by the 57-ETF fetch, **379 newly fetched**, 0 failures |

**The 57-ETF fetch had already paid for half of this.** `fetch_etf_intraday.py` fetches with
`extended_hours=true` and *builds* regular-hours-only, so the extended bars for 2018-01
onward were sitting in the cache unused. Only 2010-01 → 2017-12 was new: six minutes at the
66/min pacing rather than the ~10 estimated.

---

## The gates, and the one that fired for the right reason on the wrong thing

Four gates, because two of the failure modes here are **silent**, and a fixture that quietly
contained regular hours only would be worse than no fixture at all — everything downstream
would look fine and be wrong.

| gate | result |
|---|---|
| **the extended session arrived** — median bars/session materially above 26, pre- AND post-RTH bars on essentially every session | **PASS** (median 62; pre 100.0%, post 99.9%) |
| **04:00 and 19:45 bars exist** | **PASS** |
| **`month` was honoured** — every returned bar inside the month requested | **PASS**, 0 foreign bars across 800 slices |
| **no unexplained single-bar move above 15%** (D226) | **PASS** at 6.82% |

### `month` is honoured for equities. It was verified, not assumed.

`FX_INTRADAY` **silently ignores `month`** and returns the trailing weeks instead — no error,
no note, just the wrong data. Equities were *believed* to honour it. The fetcher checks every
slice at fetch time and refuses one whose returned dates leave the requested month, and the
build recomputes it from what was actually written. **0 violations in 800 slices.**

### The first version of the extended-session gate was wrong, and the way it was wrong matters

It was set at "median ≥ 55 bars/session", and it fired on IWM 2010-01 (48) and DIA 2010-01
(46). **That looked like the failure it was designed to catch and was not.** Probed:
pre-market and post-market bars on **19 of 19 sessions**, regular hours **exactly 26**. The
extended session had arrived; it is simply *thinner* on the less liquid names in 2010, because
an extended-hours bar exists only where something actually traded.

A gate calibrated on SPY had been about to reject a correct fetch. It was restated as
**"materially wider than regular hours, in both directions, on essentially every session"** —
which is the thing that actually matters — and the raggedness was moved from a rejection
criterion to a first-class disclosure. That disclosure turned out to be the most important
number in the fixture.

---

## The disclosure that reshaped the measurement: the clock anchors are liquidity-conditioned

Share of sessions printing the **exact** bar named:

| | 04:00 | 18:00 | 19:45 |
|---|---:|---:|---:|
| SPY 2010-2019 | 91.6% | 99.0% | 99.0% |
| SPY 2021-2026 | 100.0% | 99.3% | 99.3% |
| QQQ 2010-2019 | 66.1% | 94.2% | 96.9% |
| IWM 2010-2019 | **41.6%** | 65.3% | 76.9% |
| **DIA 2010-2019** | **22.1%** | 53.2% | 56.7% |
| DIA 2021-2026 | 89.8% | 90.1% | 92.4% |

**DIA prints no 04:00 bar at all in some 2010–2014 months.** Keying the decomposition on the
clock would silently restrict DIA's early era to the 22% of sessions with an *active*
pre-market — **selecting on activity, and then measuring returns.** That is R9's error wearing
different clothes: the conditioning variable is liquidity rather than the return itself, but
the shape is the same, and it lives in exactly the kind of analysis script R9's corollary
warns about.

**So the boundaries are PRINTS, not clock times** — the last print of the post-market and the
first print of the pre-market. This is also the economically correct choice for P1: the
untraded window becomes *the stretch between the last price you could have sold at and the
first price you could have sold at*, which is the thing that cannot be stopped out of.
**The realised boundary times are reported per symbol per era**, and the literal-clock version
is reported separately so the two readings can be compared. They differ, and the difference is
a finding rather than a nuisance.

---

## The finding nobody was looking for: the post-market is full of bad prints

QQQ, 2025-06-16 16:45 ET, as delivered:

```
open 534.1800   high 534.2500   low 447.2455   close 447.2455
```

`open` and `high` are the real price. `low` and `close` are **16% away**, and the same bogus
value repeats across the 16:45, 17:00 and 17:15 bars. Across the whole fixture the **worst raw
lower wick is +907.9%.**

**The RTH fixture never saw this because it threw the extended session away.** Three facts
decided the treatment:

1. **It is a post-market pathology.** Bars with an uncorroborated wick above 5%: **1,290
   post-market, 71 pre-market, 16 regular-hours.**
2. **It is recent.** 4–12 a year through 2022, then **200 / 455 / 797 / 460** in 2023–2026.
   That is a feed change, not a market change.
3. **The regular-hours cases are mostly REAL** — 2010-05-06 (the Flash Crash), 2015-08-24,
   2018-02-06, 2025-04-07 and 2025-04-09 all appear. A filter that erased those would be
   deleting **precisely the tail a drawdown study exists to measure.** The RTH cases that are
   *not* real cluster on **half-days**, on bars stamped after a 13:00 close.

**The rule is therefore CORROBORATION, not magnitude.** An extreme is suspect when no
neighbouring bar's body comes near it; in a real dislocation the adjacent bars also trade at
the extreme and nothing is flagged. SPY 2020-03-16 09:30, a limit-down open, is **not**
flagged. **2,113 bars (0.22%) are flagged, 1,923 of them post-market and zero in regular
hours.**

Three judgement calls inside that rule, each stated because each could have gone otherwise:

- **Extremes are filtered in the extended session only.** In regular hours the contamination
  is 16 bars in 435,166 and the large wicks are dominated by genuine dislocations. The
  **close** test runs everywhere, because a bad close corrupts a window boundary wherever it
  lands.
- **The fixture ships raw prices plus a `suspect` flag.** No price is modified, so D24's
  immutability holds and the judgement is visible rather than baked in.
- **The first and last bar of each symbol are exempt** — a corroboration rule needs
  corroborators, and a one-sided band flags the last bar of any falling series. Eight bars in
  958,217, but wrong by construction rather than by luck.

**What the rule cannot do, stated because it bounds every path number below:** an isolated
*real* spike that reverses inside one 15-minute bar is indistinguishable from a bad print
without a second data source. In the extended session that trade is accepted, and the raw and
closes-only variants are reported alongside so the reader sees the bracket.

**D226's gate had to be moved off the raw series to survive this.** Run raw it fires on QQQ
2025-06-16 at +19.43% — a true positive for a *different* question, and useless for the one it
is named for. It runs on non-suspect bars; the bad prints have their own census.

---

## Result 1 — the four windows

Annualised in log space against each symbol's own calendar span, then averaged equal-weighted
across symbols (D247's frame). **16,648 session pairs, 2010-01-05 → 2026-08-26.**

| window | annualised | ann. vol | share of overnight drift |
|---|---:|---:|---:|
| 16:00 → 20:00 post-market | **+1.70%** | 4.4% | 19.4% |
| 20:00 → 04:00 **untraded** | **+5.88%** | 7.6% | **66.0%** |
| 04:00 → 09:30 pre-market | **+1.27%** | 7.7% | 14.6% |
| 09:30 → 16:00 regular hours | **+3.12%** | 14.7% | — |
| *= overnight total* | *+9.04%* | *12.0%* | *100%* |
| *= close-to-close* | *+12.44%* | *19.1%* | — |

**D247 reproduces.** The overnight/intraday split here is **+9.04% / +3.12%** against D247's
+8.59% / −0.36% — a different universe (4 index ETFs against 57) over a different span
(16.6 years against 8.3), so the levels are not expected to match, and the *shape* does.

### By era, and the era split is why this is trustworthy

| era | post | **untraded** | pre | regular | overnight |
|---|---:|---:|---:|---:|---:|
| **2010-2019** | +0.61% | **+6.41%** | +1.39% | +3.14% | +8.55% |
| **2020** | +9.25% | **+3.88%** | +4.77% | +2.19% | +18.91% |
| **2021-2026** | +2.34% | **+5.32%** | +0.47% | +3.25% | +8.28% |

**The overnight total is era-stable** — +8.55% and +8.28% either side of 2020 — which is more
than D247's intraday leg managed (−0.33% full-sample, +1.44% ex-2020, +3.05% from 2021). 2020
is a distinct regime and reallocates the drift toward the post-market rather than changing the
total much.

### And the pooled 66% is partly an artefact — this is the qualification that matters

**The four symbols do not agree, and the disagreement tracks the boundary coverage.** On the
literal clock, restricted to sessions printing an actual 19:45 and an actual 04:00 bar, in the
two cells where coverage is ~100% and nothing is being selected on:

| | kept | post-market | **untraded** | pre-market |
|---|---:|---:|---:|---:|
| **SPY 2021-2026** | 99% | +2.29% (31%) | **+2.49% (33%)** | +2.66% (36%) |
| **QQQ 2021-2026** | 99% | +3.29% (34%) | **+9.02% (91%)** | −2.33% (−25%) |

**SPY splits almost three ways. QQQ puts nearly everything in the untraded window and has a
negative pre-market.** Same era, same coverage, opposite readings.

Part of the pooled 66% is mechanical: DIA's first pre-market print in 2010-2019 lands at
**06:00 median and 08:00 at the 90th percentile**, so DIA's "untraded" window is absorbing
20:00→06:00 while its "pre-market" is only 06:00→09:30 — which is why DIA's untraded share
reads 87.7% and its pre-market share reads −13.2%.

**What survives all of it:** the untraded window is **never the small piece**. Across the clean
cells it runs 33–91% of the overnight drift, and the post-market — the one window a position
can comfortably be exited in — is consistently among the smallest.

---

## Result 2 — the path, which is what P1 actually measures

A long opened at the 18:00 ET print and held to the 16:00 ET close the next day. **12,985
holds.** Trailing drawdown on open equity with the running peak **including the current bar's
high**, since within a 15-minute bar the high may precede the low — the adverse assumption,
and the right direction for a ratcheting barrier.

### Maximum adverse excursion

| era | holds | mean | p50 | p90 | p95 | p99 | worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| **ALL** | 12,985 | 0.81% | 0.55% | 1.87% | 2.44% | 3.98% | **13.85%** |
| 2010-2019 | 7,758 | 0.70% | 0.47% | 1.65% | 2.17% | 3.48% | 13.85% |
| **2020** | 792 | **1.31%** | 0.88% | 3.12% | 4.11% | **7.05%** | 11.29% |
| 2021-2026 | 4,435 | 0.92% | 0.68% | 2.03% | 2.51% | 3.90% | 6.87% |

**The typical hold is quiet and the tail is not.** A median MAE of 0.55% against a 4% floor
looks comfortable; the 99th percentile at 3.98% sits exactly on it.

### Breach rates against a 4% trailing floor

| era | holds | 1x | 2x | 3x |
|---|---:|---:|---:|---:|
| **ALL** | 12,985 | **2.07%** | **16.47%** | **34.73%** |
| 2010-2019 | 7,758 | 1.06% | 11.34% | 26.46% |
| **2020** | 792 | **11.36%** | **35.10%** | **56.57%** |
| 2021-2026 | 4,435 | 2.19% | 22.10% | 45.30% |

Per symbol: SPY 1.41 / 12.43 / 28.81, QQQ 2.76 / 20.09 / 39.83, **IWM 3.00 / 23.95 / 47.57**,
DIA 1.10 / 9.22 / 22.43.

**At 1x notional, roughly one hold in 48 breaches. At 3x, better than one in three.** And the
era split does the work it was required to do: the 2021-2026 rate is **double** the 2010-2019
rate at every notional, so a full-sample figure would understate the current regime.

### Worst single sessions, dated

| symbol | session | max trailing DD | MAE | of which the untraded gap | hold return |
|---|---|---:|---:|---:|---:|
| **QQQ** | **2010-05-06** | **14.03%** | 13.85% | 0.19% | −3.42% |
| IWM | 2020-03-12 | 12.31% | 11.29% | **5.07%** | −11.20% |
| DIA | 2020-03-12 | 11.37% | 10.20% | **5.86%** | −10.10% |
| IWM | 2020-03-18 | 11.18% | 10.22% | 4.45% | −5.96% |
| SPY | 2020-03-12 | 10.86% | 9.68% | **5.01%** | −9.53% |

**The worst hold in sixteen years is the Flash Crash**, and it is a *regular-hours* event that
a stop could in principle have caught. The March 2020 cluster is the opposite: roughly half of
each drawdown was already delivered by the gap before the market opened.

---

## Result 3 — how much of the excursion falls where it cannot be exited

**This is what the record was written for, and the answer is more equivocal than the framing
in R11 expected.**

| | 1x | 2x | 3x |
|---|---:|---:|---:|
| **first breach occurs in the untraded window** (share of breaching holds) | 3.72% | 2.53% | 3.04% |
| first breach in pre-market (thin, technically exitable) | 15.99% | 22.36% | 30.84% |
| first breach in regular hours (exitable) | 79.18% | 72.17% | 62.66% |
| **the untraded gap ALONE breaches** (share of all holds) | **0.10%** | **0.55%** | **1.42%** |
| the same, 2020 only | 1.39% | 4.29% | **8.59%** |

The untraded gap's own drawdown: **mean 0.18%, p99 1.58%, worst 6.50%.**

**Read plainly: on this data the untraded window is not where the breaches happen.** Roughly
97% of first breaches occur somewhere a position could have been exited, and the gap on its own
breaches a 4% floor in one hold in a thousand at 1x. R11's caution — *"a gap through the
untraded window cannot be stopped out of"* — is correct in mechanism and **small in
magnitude**, except in 2020, where the gap alone breached 8.59% of holds at 3x.

**Three reasons that finding is weaker than it looks, and they all point the same way.**

1. **The untraded window contributes exactly ONE observation to the path** — the price it
   reopens at. Any excursion *inside* it is invisible to this fixture. **Every number above is
   a LOWER BOUND**, and a continuously-traded futures position lived through the whole
   stretch.
2. **Pre-market is counted as exitable and barely is.** Fold the 15.99–30.84% of first breaches
   that occur there into "could not realistically be stopped" and the picture changes
   materially.
3. **The 20:00–04:00 window is the quiet one by construction.** The measurement confirms that
   it is quiet; it cannot confirm that it is *safe*, because the two are the same observation
   here.

The statistic "where the maximum drawdown is realised" (83% regular hours) is reported but
**should not be quoted** — regular hours supply 26 observations and the untraded window one, so
its shape is a bar count, not a fact about risk.

---

## Sensitivity — how much is the bad prints

| variant | mean MAE | p99 MAE | worst MAE | breach 1x | 2x | 3x |
|---|---:|---:|---:|---:|---:|---:|
| **corroborated** (headline) | 0.81% | 3.98% | 13.85% | 2.07% | 16.47% | 34.73% |
| raw (bad prints included) | 0.86% | 4.76% | **35.84%** | 2.96% | 17.17% | 35.21% |
| closes only (strict lower bound) | 0.69% | 3.72% | 11.20% | 1.35% | 11.15% | 24.94% |

**The raw variant's 35.84% worst MAE is the bad prints, not the market**, and it inflates the
1x breach rate by 43%. Without the filter this record would have reported a materially
different number for the headline question. **The truth for a continuously-traded instrument
sits above all three rows, because the untraded window is dark in every one of them.**

---

## Every judgement call, in one place

1. **Boundaries are prints, not clock times** — because exact anchors are liquidity-conditioned
   (DIA 22.1% at 04:00 in the early era). The literal-clock version is reported separately.
2. **Bars stamped 20:00 and later are dropped.** They appear in ~half of sessions at 20:00 and
   5–9% beyond, are past the documented session end, and a ragged tail would make
   "16:00 → 20:00" mean different things on different days. 7,505 bars.
3. **Half-days are kept in the fixture and excluded by the consumer.** A 13:00 close has no
   16:00 print and therefore no 16:00→20:00 window. 23 sessions. `fetch_etf_intraday.py` drops
   them; here the grid is ragged by construction so rectangularity is unavailable and dropping
   would discard real sessions for a property that cannot be attained.
4. **Bad-print filtering by corroboration, extremes in the extended session only**, closes
   everywhere, series edges exempt. Raw prices retained plus a flag.
5. **Friday→Monday holds are excluded from the path.** Globex is shut on Friday evening, and
   the Sunday-evening hold that replaces it has **no equity bars at all**. Monday exits are
   therefore absent from every path number — and **Monday's overnight is the one most likely to
   carry weekend news**, so this is a real gap, not a rounding.
6. **A session with no evening print after 17:00 is not entered**, rather than entered at a
   stale 16:15 price.
7. **The trailing peak includes the current bar's high**, so a bar can lift the floor and then
   breach it. The alternative under-counts breaches, which is the direction that manufactures
   comfort.
8. **Annualisation is per-symbol against that symbol's own calendar span, then averaged.** The
   first version summed log returns across four symbols against one shared span and read a
   close-to-close drift of **+59.85%/yr**. Caught by it being obviously absurd; recorded because
   the next such error might be only mildly absurd.

---

## What this does NOT establish

- **No rule is proposed and no cell is counted.** The ledger does not move.
- **No hurdle is claimed.** P1 is not evaluated here — a hold is not a strategy, and R6 forbids
  claiming a hurdle without running the test that defines it. What this supplies is the *input*
  a P1 evaluation would need.
- **This is still cash equity.** R11's second caution stands in full: ETFs are not futures, the
  extended session is thin, and **the 20:00–04:00 window is unobserved rather than measured**.
  ES trades continuously through it. Everything here bounds the futures path from below and
  does not describe it.
- **Monday holds are missing entirely**, and they are the ones carrying weekend news.
- **SPY and QQQ disagree** about where the overnight drift accrues in the same era with the same
  coverage. Any construction built on the untraded window's dominance is building on QQQ, not
  on a robust fact.

---

## Verification

- `uv run pytest tests/unit/test_index_extended_fixture.py` — **25 tests, all green.**
- **The extended session arrived**: median bars/session ≥ 55 and > 2× the RTH count, an 04:00
  and a 19:45 bar exist, pre- and post-RTH bars on > 99% of sessions — asserted **from the
  data**, not from the meta, because the meta is written by the same code that would be wrong.
- **`month` was honoured**: all 200 months present, span is the declared one, 0 foreign bars.
  The detector is also tested against a synthetic payload shaped like the `FX_INTRADAY` failure.
- **The RTH-fallback detector is tested in both directions** — it must reject a 26-bar
  09:30–15:45 payload and **accept** a thin-but-genuine 48-bar extended session, which is the
  case that caught the first gate out.
- **No unexplained bar move above 15%** among non-suspect bars, and the events sidecar is
  asserted to record **zero** splits for all four symbols — checked, not assumed.
- **The bad-print filter is tested on the transcribed QQQ 2025-06-16 bars** (flags three of
  five) and on a monotone fall (flags none), and **six named real dislocations are asserted
  NOT flagged**, so the filter cannot quietly become a beautifier.
- **The key never appears** in `--plan` output, the fixture, the meta or the sidecar; the plan
  names the *source* of the key, never its value.
- The four windows are asserted in code to multiply exactly to the close-to-close return.

## Artifacts

| | |
|---|---|
| fetcher | `scripts/fetch_index_extended.py` |
| runner | `scripts/run_overnight_decomposition.py` |
| fixture | `data/fixtures/index_extended_15m_raw.csv.gz` + `.meta.json` + `_events.json` |
| results | [`OVERNIGHT_DECOMPOSITION_RESULTS.md`](../results/OVERNIGHT_DECOMPOSITION_RESULTS.md) |
| tests | `tests/unit/test_index_extended_fixture.py` |
| raw cache | `data/raw/alphavantage/15min/` — **not committed** (D191) |

## Ledger

| count | N |
|---|---:|
| fresh cells | **0** — this is a measurement, nothing was scored |
| rules proposed | **0** |
| hurdles claimed | **0** |
