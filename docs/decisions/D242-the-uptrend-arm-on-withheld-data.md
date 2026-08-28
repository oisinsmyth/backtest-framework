# D242 — The uptrend arm and the combined book on withheld data

**Status:** Pre-registered — committed BEFORE the withheld fixture is touched
**Date:** 2026-08-28
**Area:** Strategy research

---

## What this spends

**The 60-ETF holdout, for these rules, permanently.** It has been used once before — by
[D237](D237-the-recovery-rule-on-withheld-data.md), for S1, which scored **+0.779** on it. This
record spends it on **A0**, **A2** and the **combined book**, and there is no second holdout
behind it.

Under R8 this is the only route to `BOOK.md`, and the hurdles below are committed before any
number is produced.

---

## The rules, frozen

**Nothing may move.** If a single constant differs between the mined run and this one, the test
is void.

```
A0   UPTREND := g_lo > 0 AND g_hi > 0
     g_lo, g_hi = OLS slopes of log swing-LOW and swing-HIGH prices,
                  trailing 252 bars, pivots at k = 3 (D173's fixed set)
     ENTRY  the first bar of an UPTREND episode
     EXIT   the earliest of  age >= 63 bars  |  the state ends

A2   A0 plus a fixed stop at -8% from entry

C0   S1 + A2 on one shared capital pool at TOTAL = 100%
     (at full capital the allocator is inert, so this is the union — D241)

S1   position = +1 if hist_L > 0 AND md_L <= 0        the reference arm
```

| frozen constant | value |
|---|---|
| pivot half-width `k` | 3 |
| regression window | 252 bars |
| age cap | 63 bars |
| fixed stop | 8% |
| lag, warm-up, costs, dividend frame | unchanged |

---

## The fixture, and what it can and cannot show

`universe_holdout_daily_raw` — **60 ETFs sharing zero tickers with the mined 57**, same span,
**1,515 live bars**. Same power as the mined run, so unlike D237's T3 this test can actually
resolve a difference.

**What it shows:** whether the rules are fitted to those particular 57 tickers.

**What it does NOT show, stated before the run rather than as an excuse after it:** the two
universes correlate at **+0.978**. Both live inside the 2018–2024 market. **This is an
instrument holdout, not a time holdout**, and a pass leaves the regime question exactly where
D239 left it — with S1's edge partly a bet that reversals beat continuations.

---

## Hurdles

**On A2 (the headline) and A0 (the entry rule alone):**

- **H1.** Excess Sharpe **> 0** and **> buy-and-hold's** on this fixture.
- **H2.** Beats its **matched-count rotation null** at p95 — same exposure, turnover and holding
  periods, wrong bars.
- **H3 — anti-triviality.** The delta over buy-and-hold must reach **25% of the mined delta**.
  Mined A2 scored +0.822 against B&H's +0.235, so the floor is **+0.147**. Out-of-sample
  shrinkage of 30–70% is normal; this rules out "technically positive and worth nothing."
  D237's floor was set the same way.
- **H4 — the overlay, A2 only.** The −8% stop must again beat its **matched-exit-count overlay
  null** at p95 (R7). **This is the leg I expect to fail**, and it is registered separately from
  H1–H3 precisely so that "the entry replicated" and "the stop replicated" cannot be conflated.

**On the combined book:**

- **H5.** C0 beats **S1 alone** on excess Sharpe.
- **H6.** The same, with a **paired block bootstrap `p05 > 0`** (block 21, both books on
  identical resampled dates). **H5 and H6 are separate on purpose** — in-sample H5 passed at
  +0.178 and H6 failed at p05 −0.010, and D230 is why the interval leg is never optional.

**Reported, not hurdles:** ρ between S1 and A2 on this fixture, exposure, deployable return,
Calmar, max drawdown, the null's money and volatility legs, and **hurdle E**, which is expected
to fail at roughly 2 entries per symbol and is stated here rather than discovered.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **R1** | **A0's entry replicates** — positive, beats buy-and-hold, clears its rotation null. The mechanism is simple and it cleared at the 97.3rd/99.2nd percentile on mined data | **moderate-high** |
| **R2** | **A2 shrinks to +0.35 to +0.60** from +0.822. Ordinary out-of-sample regression | **moderate** |
| **R3** | **H4 FAILS — the stop's edge does not replicate.** It was the best of four overlays at the 99.6th percentile, and a best-of-four with no multiplicity correction is exactly what regresses | **moderate** |
| **R4** | **ρ stays below 0.30.** The two rules avoid each other by construction — an ETF below its channel is rarely in a confirmed year-long uptrend — and construction should travel | **moderate-high** |
| **R5** | **H5 passes and H6 fails**, repeating the in-sample split | **moderate** |

**R3 is the prediction I care most about**, because it is registered against the result I most
want to be true. If the entry replicates and the stop does not, the honest reading is that **A0
is the finding and A2 was a fitted embellishment** — and D240's headline number was the wrong
one to quote.

---

## The reading, declared in advance

All four outcomes for (A0 clears H1–H3, A2 clears H1–H3), so none can be storied afterwards:

| A0 | A2 | reading |
|:--:|:--:|---|
| ✓ | ✓ | **The strongest result the programme has produced.** Still one era and a +0.978-correlated universe — the next step is more forward time, not promotion to capital |
| ✓ | ✗ | **The entry generalises; the stop was fitted.** A0 is the candidate, A2 is retired, and D240's headline is corrected in writing |
| ✗ | ✓ | **Incoherent** — a stop cannot rescue an entry that does not generalise. Treat as failure and investigate the overlay null before believing anything |
| ✗ | ✗ | **The arm does not generalise. Closed**, with no variant and no third fixture |

---

## What a pass earns, and what it does not

**A pass admits A0 or A2 to `BOOK.md` as S2**, carrying its own falsification conditions and a
full statement of its weaknesses, per R8.

**A pass does NOT promote anything to capital.** R8's corollary is binding: sizing and capital
allocation are separate decisions, recorded separately. And the user has explicitly deferred
book sizing.

**A pass also does not close the sample-size problem.** Hurdle E will still fail at ~2 entries
per symbol, and six years is still six years against the ~8.8 needed.

---

## Stop

**If A0 fails H1–H3, the uptrend arm is closed** — no variant, no third fixture, no re-cut of
the age cap. Committed here so that "the last reading wasn't the right one" cannot be pulled
later.

**The 2025–2026 forward window is NOT touched by this record.** It was spent by D237 for S1 and
remains unspent for these rules.

---

## Ledger

| count | N |
|---|---:|
| fresh — 3 books on withheld data | 3 |
| + D241's 5, D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 39 |
| + the gradient anatomy | 60 |
| + disclosed ETF prior | **45,863** |

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| repointing the loader at the holdout fixture | `run_test`'s `L.FIXTURE` / `L.EVENTS` pattern | `run_withheld_test.py` |
| the uptrend signal, walk, ATR, rolling fit | `signals`, `walk` | `run_uptrend_onset.py` |
| the capital allocator | `allocate` | `run_combined_book.py` |
| S1's book | `base_masks`, `hold_book` | `run_stops_targets.py` |
| signed scorer, rotation null with money/vol legs | `score`, `rotation_nulls` | `run_short_mirror.py` |
| the matched-exit-count overlay null | `null_book` | `run_uptrend_onset.py` |
| the paired block bootstrap | `paired_block_bootstrap` | `run_jerk_rung.py` |

**Written fresh: nothing.** Every component exists and is tested. That is the point — a holdout
test that needed new code would be a holdout test whose code had never been checked.

## Verification

- Full suite green, offline, deterministic; `--report-only` re-renders byte-for-byte.
- **The frozen constants are asserted equal to `run_uptrend_onset`'s**, so the rule cannot drift
  between the mined run and this one without the runner failing loudly.
- **The mined numbers must still reproduce** when the runner is pointed at the mined fixture —
  +0.746 for S1, +0.822 for A2. A holdout runner that cannot reproduce the training result is
  measuring something else.
- **Hurdle E is computed, not assumed**, and reported whichever way it lands.
