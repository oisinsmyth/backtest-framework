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

---

## STAGE 2 — THE VERDICT

**Produced:** 2026-08-28 · `uv run python scripts/run_uptrend_withheld.py` · Page:
[`UPTREND_WITHHELD_RESULTS.md`](../results/UPTREND_WITHHELD_RESULTS.md)

*The runner reproduced the mined numbers before touching the holdout — A0 +0.610, A2 +0.822,
S1 +0.746 — so it is measuring the same rules.*

### The one-sentence version

**The entry rule generalised and grew; the stop did not.** A0 scored **+0.672** on 60 disjoint
tickers against **+0.610** on the training set, at the **99.7th percentile** of its rotation
null — while the −8% stop's edge collapsed from the 99.6th percentile to the **71.7th**, exactly
as R3 predicted.

### The books on withheld data

| | exposure | excess Sharpe | *mined* | change | CAGR | deployable | max DD | Calmar |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **A0** | 13.9% | **+0.672** | *+0.610* | **+10.1%** | 2.38% | 5.89% | −4.40% | 0.541 |
| **A2** | 12.5% | +0.699 | *+0.822* | −15.0% | 2.09% | 5.66% | **−2.71%** | 0.771 |
| **C0** | 31.1% | **+0.873** | — | — | 7.13% | **10.07%** | −9.52% | 0.749 |
| *S1* | *19.7%* | *+0.779* | — | — | *5.49%* | *8.87%* | *−9.04%* | *0.607* |
| *B&H* | *100%* | *+0.230* | — | — | *8.34%* | *8.34%* | *−37.92%* | *0.220* |

### H1–H3 — both entry rules clear everything

| | Δ vs B&H | floor | rotation null | percentile | money pct | H1 | H2 | H3 |
|---|---:|---:|---:|---:|---:|:--:|:--:|:--:|
| **A0** | **+0.442** | +0.147 | p95 +0.487 | **99.7th** | **99.9th** | ✓ | ✓ | ✓ |
| **A2** | **+0.469** | +0.147 | p95 +0.499 | 99.6th | 99.9th | ✓ | ✓ | ✓ |

**The delta over buy-and-hold is three times the anti-triviality floor.** The money leg of the
null — which volatility cannot inflate — sits at the **99.9th percentile** for both.

**A0 did not shrink. It grew, +0.610 → +0.672.** Out-of-sample results normally give back
30–70%. That is now the second rule in this programme to grow on an instrument holdout, after
S1 did the same thing in D237.

### H4 — the stop was fitted, and this was registered in advance

| trades cut | actual | null p50 | null p95 | **percentile** | H4 |
|---:|---:|---:|---:|---:|:--:|
| 57 of 241 | +0.699 | +0.667 | +0.765 | **71.7th** | ✗ |

**99.6th on mined data, 71.7th here.** The stop's *timing* carries no information beyond cutting
the same number of trades short at random points.

**This is exactly what R3 predicted and why H4 was registered separately from H1–H3.** The stop
was the best of four overlays at the 99.6th percentile with no multiplicity correction, and a
best-of-four with no correction is precisely what regresses.

**What the stop still does:** it lowers max drawdown from −4.40% to **−2.71%** and lifts Calmar
from 0.541 to 0.771. That is a *mechanical* benefit of holding less, not an informational one —
the same distinction D236 drew. **It is a risk control, not alpha, and it must not be described
as alpha.**

### H5 / H6 — the combined book

| | |
|---|---:|
| S1 alone | +0.779 |
| **C0 combined** | **+0.873** |
| **delta** | **+0.094** |
| bootstrap p05 | **−0.104** |
| **H5** point estimate | ✓ |
| **H6** interval | ✗ |

**The in-sample split repeated exactly**, as R5 predicted: the combination beats S1 on the point
estimate and the interval still contains zero.

**But C0 beat buy-and-hold on money *and* drawdown out of sample** — **10.07% against 8.34%**,
at **−9.52% against −37.92%**. D241 found that in-sample; it replicated.

**ρ between S1 and A2 held at +0.1749**, against +0.1586 on the mined fixture. **The
diversification is structural and it travels** — which R4 predicted from construction rather
than from the data.

### Scoring — four of five, and the miss was pessimistic

| | prediction | outcome |
|---|---|---|
| **R1** | A0's entry replicates | **CONFIRMED**, and it grew |
| **R2** | A2 shrinks to +0.35 to +0.60 | **FALSIFIED** — it landed at +0.699, *better* than I predicted |
| **R3** | H4 fails; the stop does not replicate | **CONFIRMED**, 99.6th → 71.7th |
| **R4** | ρ stays below 0.30 | **CONFIRMED**, +0.1749 |
| **R5** | H5 passes, H6 fails | **CONFIRMED** |

### The reading, as declared in advance

Both entry rules cleared H1–H3, so the pre-committed cell fires:

> **THE STRONGEST RESULT THE PROGRAMME HAS PRODUCED. Still one era and a +0.978-correlated
> universe — the next step is more forward time, not capital.**

**With the precision H4 forces, and which the reading table could not express:** the *entry*
generalised; the *stop* did not. **A0 is the finding.**

### What is wrong with it — at full strength

1. **Hurdle E fails worse than anything in the book: 2 entries per symbol**, from 217 entries
   across 60 ETFs. S1's 9 was already called its weakest point.
2. **This is an instrument holdout, not a time holdout.** ρ between the two universes is
   **+0.978**. It shows the rule is not fitted to 57 particular tickers. It shows nothing about
   independence from the 2018–2024 market, and D239 established that S1's edge is partly a bet
   on that market's character.
3. **The combined book's advantage over S1 still fails its interval**, on both fixtures.
4. **A0's own money is modest** — 5.89% deployable against buy-and-hold's 8.34%. It earns its
   place as a *diversifier*, not as a return engine.
5. **D240's headline was the wrong number to quote.** It reported A2 at +0.822 on the strength of
   a stop that has now failed its null out of sample.

### What this changes

**A0 is admitted to `BOOK.md` as S2**, per the pass condition committed above — carrying its own
falsification conditions and this full statement of weaknesses.

**A2 is NOT admitted.** Its stop failed H4 on withheld data. It is recorded as a variant that
reduces drawdown mechanically and adds no demonstrated timing information.

**D240's result section is corrected in writing** rather than edited, per the append-only rule.

**Nothing is promoted to capital.** R8's corollary binds and book sizing is explicitly deferred.

**The 2025–2026 forward window remains unspent for these rules**, and extending the fixture back
to ~2005 remains the only action that can close the interval.

### Ledger

| count | N |
|---|---:|
| fresh — 3 books on withheld data | 3 |
| + D241's 5, D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 39 |
| + the gradient anatomy | 60 |
| + disclosed ETF prior | **45,863** |
