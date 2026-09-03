# D303 — the market-referenced target

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**No holdout testing. The holdout is not read and this study does not read it.
Holdout reads spent: 0. Programme total: 0.**

---

## The question

`profit_target` is the strongest result in the programme — p = 0.005 in D295,
again in D298, again in D301, against three differently-constructed nulls. It is
also **mis-specified**:

```python
elif rule == "profit_target":
    trig = np.isfinite(u) and cum >= param * u
```

`cum` is a **raw** single-name cumulative return and `u` is that name's **total**
volatility. The book is a spread, so what a position is worth is its move
relative to what the other leg cancels. **There is no reference in the rule.**

### The size of the defect is already measured, and it is modest

`d297_spread_stop_premise.py`, on 121,106 held position-bars:

| | |
|---|--:|
| market share of a held position's variance | **6.1%** |
| corr(raw move, idiosyncratic move) | **0.969** |
| fires: raw / referenced / both / disagree | 9,375 / 8,661 / 7,556 / 2,924 |
| **Jaccard** | **0.721** |

**A referenced rule fires on 72% of the same trades.** This corrects ~28% of
firings; it does not change the character of the rule. It is done first not
because it is large but because **every later study in the sequence is measured
on this rule**, and it is cheaper to specify it once.

## The construction

```
m[t]     = mean r1 over ALL live names          the market, not the leg mean
x[i,t]   = r1[i,t] - m[t]
cum_x    = Σ σ·x[i,τ]  since entry              σ = +1 long, -1 short
u_x[i]   = trailing sd of x[i,·], 21 bars, lagged
```

**The reference is the market and never the leg mean** — the mean of the 19 longs
*is* the edge, and netting a position against it deletes the signal it was
selected for. This was corrected once already in D297's premise and is being
propagated here, not rediscovered.

**`m` cancels exactly in the book return** — `mean(r_long − m) − mean(r_short − m)
= mean(r_long) − mean(r_short)` when both legs hold equal counts. The reference
changes **when positions leave** and changes nothing else. Assertion [2b] holds
that bit-identically.

## The runner does NOT edit `run_d295_exits.py`

Four independent implementations of these rules exist — `run_d295_exits.py:163`,
`run_d298_combined.py:175` (`holdings_mask`, expressing `stop_and_target` as
`abs(cum) >= param*u` where d295 uses the two-sided form),
`run_d301_stack.py:189`, `d295_why_trailing_fails.py:74`. Editing d295 breaks
`run_d301_stack.py:313-322`'s bit-identity assertion and stops every published
number reproducing.

**New runner `scripts/run_d303_reference.py`**, carrying **both** accumulators so
raw and referenced rules run in one simulator and one pass. It reuses
`run_d299_ladder.market_reference`, `d295.roll_vol` (called on the excess series,
as `run_d299_ladder.py:161` already does — the one-bar lag is internal and no
caller re-lags it), `d295.build_inputs`, and D301's simulator and stat block.

## Cells

| axis | levels |
|---|---|
| **reference** | `raw @ 1.0` (incumbent) · `excess @ 1.0` (naive) · `excess @ matched` |
| **band** | `flat` = `X·u` · `√age` = `X·u·√age` |

**3 × 2 + control = 7 cells.**

### Why the band axis is here and not in the k study

A flat threshold on a **cumulative** sum is not a constant hurdle: the cum's own
sd grows like `u·√a`, so a flat band gets mechanically easier to hit as a
position ages. At k = 5 (mean run 4.0) that is mild; at k = 20 it degenerates
into "exit at a random early bar" and would corrupt D305's k sweep. The `√age`
form is a constant-Z band and the only one comparable across `k`. **Specifying
the rule once is cheaper than specifying it twice.**

### Why both a naive and a matched excess threshold

Idiosyncratic vol is smaller than total vol, so `1.0 × u_x` is a **tighter** band
than `1.0 × u`. A comparison at a common multiplier measures tightness and calls
it reference.

**`excess @ matched`** calibrates the multiplier so the referenced rule's
**trigger count** matches the raw rule's, and the calibrated value is **printed
before any book is scored**. It is a nuisance match on fire rate, not an
optimisation of any statistic — no return enters the search objective.
**`excess @ 1.0` is reported beside it** so the calibration's own effect is
visible rather than absorbed.

## Scoring

- **Statistic: gross bp/bar.** No overlay in this study, so exposure is 100%
  everywhere and Sharpe is not required.
- **Each cell against a holding-run-matched null** — d295's `sampled_runs`: the
  cell's own holding-run distribution resampled, so rate and persistence match.
  A count-matched control is not a control (D279), and a per-bar redraw churns
  where the treatment persists (D291). 200 draws.
- **Paired t on the per-bar difference between the raw and referenced books** —
  this is the study's actual question, and it is a within-book comparison with
  no nuisance to match.

**Cost is reported, not gating**, at the round trip on names actually held, with
the median-based figure primary and the mean reported as the truncation artefact
D302 showed it to be.

## Predictions

Committed before the runner exists. Three are against.

| | prediction |
|---|---|
| **Q1** | the referenced rule fires on 0.65–0.80 of the same position-exits (Jaccard), reproducing D297's premise measurement of 0.721 — a mechanical check that the implementation is the same object |
| **Q2** | **the referenced book's gross is within ±15% of the raw book's +12.49.** *Against a large effect* |
| **Q3** | **neither beats the other at p < 0.05 on the paired per-bar difference.** *Against the fix mattering at all* |
| **Q4** | both clear their own holding-run-matched null at p < 0.05 |
| **Q5** | the `√age` band fires **later** in a position's life than `flat`, and its trigger share is lower at k = 5 — mechanical; if it is not, the band is not the band it is labelled |
| **Q6** | **the referenced rule's advantage, if any, concentrates in the highest tercile of market volatility** — the only regime where the 6.1% variance share is large enough to move a decision. *Against the effect being uniform* |
| **Q7** | the calibrated multiplier lands **below 1.0**, since idiosyncratic vol is smaller than total vol |

Q1 and Q3 are load-bearing. **Q1 failing means the implementation is not the
rule D297 measured** and nothing else in the output is interpretable.

## Decision rule, declared before the numbers

- **referenced ≥ raw** → adopt the referenced rule as the base for D300, D304,
  D305, D306.
- **referenced < raw materially** → the incumbent's edge depends partly on beta
  the spread was supposed to cancel. **Report that plainly and decide in the
  open.** Do not silently keep the raw rule.
- **indistinguishable** → **adopt the referenced rule anyway**, on correctness
  grounds. Given Jaccard 0.721 this is the expected outcome, and it is stated
  here so that adopting it later is not a post-hoc rationalisation.

## Assertions

The standing three, plus three this study owes.

1. **Lag audit, second implementation** — the held set re-derived from
   `score[:, t-1]` by a loop that never calls the selection function.
   **1b.** and it must **fail** on a variant that peeks at bar `t`.
2. **Sign audit, in money** — a favourable move pays positively; a market-wide
   move moves the two legs oppositely.
   **2b. The reference must cancel:** with both legs at equal count, the
   excess-book return must be **bit-identical** to the raw-book return. If
   subtracting `m` changes the book's P&L, `m` is not a reference.
3. **Right quantity** — trigger share must fall monotonically as the multiplier
   rises, and each rule's holding run must be shorter than the no-exit book's.
4. **Bit-identity** — the `raw @ 1.0 / flat` cell must reproduce
   `d295.simulate`'s `profit_target` book exactly. If the incumbent cell is not
   the incumbent, no comparison means anything.
5. **[NEW] A parameter must move the BOOK, not only the ledger.** Every cell's
   book series must differ from every other cell's. **This is the guard D295
   lacked** — B5's three parameter levels returned 11.274806037178 identically
   while trade counts differed by 7,000, and it went unnoticed for three
   studies.
6. **[NEW] [C] Cost dimensions.** At k = 5, turnover must equal `1/k` to
   floating point and `cost_bar` must equal `rt × turn`, cross-checked against
   D295's published **52.19 bp at rt = 260.7, turn = 0.200** — and the assertion
   must **fail** on a doubled formula. **This is the guard that was missing when
   `turn * 2.0 * rt` shipped in two runners.**
7. **The self-test must raise on a deliberately broken book**, corrupting bars
   **inside the mask** — a slice by position lands in the panel's leading NaNs
   and is silently discarded, which is how one of these checks passed a book
   handed free money.

## Stop conditions

- **Q1 fails** → the implementation is not D297's object; fix it before reading
  anything else.
- **Both rules fail their own nulls** → the target does not survive being run in
  this harness at all, which would contradict three previous scorings and points
  at the harness rather than the rule.
- Otherwise the decision rule above applies and the sequence proceeds to D300.

## Scope

**Out:** every other exit, the overlay, book width, the holding period, and any
change to the entry signal or the gate. `N = 19`, `k = 5`, gate 25, the D293
triple — all inherited, none re-searched.

## Files

`docs/decisions/D303-the-market-referenced-target.md` (this record) · runner and
data to follow, in separate commits.
