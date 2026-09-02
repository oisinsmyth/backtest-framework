# D282 — The overnight-only short

**Status:** PRE-REGISTERED. Committed **before the runner exists**. Nothing here is a result.
**Date:** 2026-09-02
**Area:** Strategy research · **personal track**

---

## Why this exists — the edge is entirely overnight and the intraday session reverses it

`scripts/d280_combined_forecast.py` · `data/d280_combined_forecast.json`. Cross-sectional
Information Coefficient — **Spearman, within bar**, the **R9-lagged** `hist_L` against each **part**
of the next bar, out of sample from **2018-01-01**, on the dead-inclusive daily fixture. The book
ranks **ascending**, so **a negative IC is tradeable for a short**:

| universe | target | mean IC | t |
|---|---|---:|---:|
| ALL | total | −0.00524 | −1.79 |
| **ALL** | **gap** | **−0.01531** | **−4.71** |
| ALL | intraday | +0.00168 | +0.65 |
| QUAL | total | +0.00462 | +1.43 |
| **QUAL** | **gap** | **−0.01255** | **−3.45** |
| **QUAL** | **intraday** | **+0.00868** | **+2.85** |

where `gap(t+1) = open(t+1)/close(t) − 1` and `intraday(t+1) = close(t+1)/open(t+1) − 1`.

**The whole of the signal lives in the overnight gap, and the intraday session pushes back against
it.** On the qualifying set the two legs carry **t −3.45 and t +2.85 in opposite directions** and
the close-to-close total is **+0.00462, wrong-signed and insignificant.**

**That is why every close-to-close study in this programme read as noise.**
[D256](D256-the-book-on-single-names.md) held everything that qualified,
[D279](D279-the-concentrated-short-on-dead-inclusive-names.md) held the top N of it, and
[D281](D281-the-unfiltered-ranking.md) holds the top N of everything — **all three book both halves
of the bar and let a real overnight edge be cancelled by a wrong-signed intraday move.**

**D282 changes exactly one thing: which part of the bar is earned.** Same fixture, same universe,
same score, same N, same controls, same constants as D281. **Enter at the close, exit at the next
open, never hold through a session.**

**The best score against the gap is `h / lagged range` at IC −0.01625, t −5.97** — stronger than raw
`hist_L`'s −0.01531 — so it is carried as a **second, declared ranking arm** below, *in this
pre-registration*, rather than added after a result is seen.

**[D280](D280-the-forecast-precheck.md) is a measurement and scores no cell.** It admits no
candidate and clears no hurdle. Under [R13](../RULES.md#r13) it is disclosed in the ledger because
it **shaped this search space**, which is the test that matters.

---

## The fixture

`us_shorts_daily_raw.csv.gz` — **1,573 names, 4,137,239 rows, 2010-01-04 → 2026-08-26, RAGGED.**
**562 carry a delisting date (35.7%)**, 122 more collapsed while listed. Loaded through
`RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)` where `B = scripts/run_book_single_names.py`
— per-symbol live windows, **equal weight over LIVE names**, delisting as an exit with no
foreknowledge, no forward-filled prices.

D252's own caveat is carried rather than paraphrased: the fixture *"deliberately contains dead
companies and is still not free of survivorship bias"* — provider coverage records 40–76 delistings
a year for 2009–2012 against 700–1,000 after 2016, so **the dead cohort is materially
under-sampled early in the span.**

**Two fixture properties this study leans on that no previous study on it did**, because none of
them ever read the open:

1. **The split adjustment must cover the OPEN, not just the close.** It does:
   `fetch_short_universe.py` divides `1. open`, `2. high`, `3. low` and `4. close` by the *same*
   `split_factor_at(d)` and multiplies volume by it. **A factor applied to the close alone would
   inject a fabricated gap on exactly one night per split** — the single most dangerous defect
   available to an overnight study. The runner reports the **largest 25 overnight moves** as a
   standing check, in the same spirit as the fixture's own `largest_25_moves` gate.
2. **The sidecar dividends are in the same split-adjusted frame as the prices** (D75), so
   `amount / open` is frame-consistent.

---

## The construction, frozen

```
universe  every LIVE, WARM name with a finite (md_L, hist_L) pair. NO value
          filter -- exactly D281's unfiltered base:
              base = -hold_book(ok, warm),  ok = finite(md_L, hist_L) & warm
          D281 established why: the filter and the ranking are the same
          variable, and inside the qualifying set the sign flips.

TIMING    ENTER at close(t).  EXIT at open(t+1).  OVERNIGHT ONLY.
          NO INTRADAY EXPOSURE, EVER. The position exists between the closing
          auction and the next opening auction and at no other time.

score     ARM 1  hist_L                      ascending  (D280 gap IC -0.01531)
          ARM 2  hist_L / lagged range       ascending  (D280 gap IC -0.01625,
                 range = (high-low)/close                 t -5.97, the stronger
                                                          gap predictor)
          BOTH LAGGED ONE BAR. See the lag section.

arm       short the N lowest-scoring names each night. N in {10, 25, 50}.

frozen    5 bp/side, borrow 3%/yr, rf 4%, PPY 252, Impulse 34/9, window 252,
          seed 0, 300 null draws. Nothing is varied, nothing is re-tuned.
```

**Arm 2 is declared here, before the runner exists, and it is declared because D280 measured it as
the stronger gap predictor.** Reporting only whichever arm wins would be selecting on the outcome
twice — D278's H5 exists for exactly that failure mode. **Both arms are carried, at all three N,
against both controls, and both are counted in the ledger.**

**Arm 2 is passed to `top_n` UNLAGGED as `hist_L / range`, because `top_n` lags internally.** Lag
and division commute, so `lag1(h/range) = lag1(h)/lag1(range)` — which is exactly the
`h / safe(rng_l)` quantity D280 measured. Stated because getting it wrong would silently score a
different arm from the one the motivating measurement priced.

---

## THE TECHNICAL RISK THAT COULD INVALIDATE THE WHOLE STUDY — close-to-close scoring

**`RP.score` and `RP.pooled_returns` compound `panel.total_log_returns`, which is a CLOSE-TO-CLOSE
return. AN OVERNIGHT BOOK DOES NOT EARN THAT.** It earns `open(t+1)/close(t) − 1`. Reusing the
default scorer would book a full session of exposure this construction never takes, and every
number in the study would be a different strategy's.

**The runner therefore ships its own scorer and states the compounded quantity in its module
docstring.** The quantity is, at column `t`:

```
overnight_total_log[i, t] = log( open[i, t+1] / close[i, t] )        the price gap
                          + log1p( dividend[i, t+1] / open[i, t+1] ) the ex-div charge
```

**Column `t` is THE NIGHT AFTER THE CLOSE OF BAR `t`.** The last column is identically zero — there
is no next bar. A cell is valid only where the name is live on **both** `t` and `t+1` **and both
prices are finite and positive**; **the position is forced to zero on every night that cannot be
priced**, so no exposure is ever charged a fee for a return that does not exist.

**Adjacency is required on the grid, and it is stricter than the loader.** `load_ragged` diffs a
symbol's own bars and so books a return *across* an internal provider hole; **a multi-day hole is
not an overnight return** and this study drops those name-nights instead. The count is reported.

**Three consequences that had to be handled rather than inherited:**

| default | why it is wrong here | what the runner does |
|---|---|---|
| `RP.pooled_returns` turnover `|diff(pos)|` | **a name held two nights running shows zero turnover** — but it was covered at the open and re-shorted at the close. It is TWO round trips, not one | charges **`2 × |pos|` units EVERY night**, unconditionally |
| `C.per_symbol_concentration` | reads `panel.total_log_returns` | rewritten against the overnight grid |
| `EP.eff_over_book` | correlates `panel.log_returns` | fed a **shim panel whose `log_returns` IS the overnight grid**, so E′ measures co-movement of the thing actually earned |

**`EP.eff_over_book` itself is used unmodified** — the pre-registered estimator, over the **HELD
BOOK**, never `RP.effective_instruments(panel, ...)`, which D279 recorded as a defect that scored a
ten-name book and a 1,200-name book identically at 5.44.

---

## Periods per year, and the study's central tension

**PPY stays 252.** There is still exactly one overnight period per trading day, so the annualisation
is unchanged and the Sharpe is comparable to D256, D279 and D281.

**But every night is a full round trip**, and that is the whole problem:

| | round trips/yr | toll at `2c` = 10 bp | gross needed to break even, per unit exposure |
|---|---:|---:|---:|
| D279 `S1_short`, ~15-day holds | **~17** | 10 bp | **~1.7%/yr** |
| **D282, one night per name-night held** | **~252** | 10 bp | **~25.2%/yr** |

**The overnight book pays roughly fifteen times the annual toll of the daily book for the same
`2c`.** D279 and D281 fail on drift with costs barely mattering; **D282 will live or die on cost.**
That inversion is the reason this study is worth running and the reason it is expected to fail.

---

## The cost bar — this is what the study is really about

[D265](D265-the-entry-time-reconciliation.md) reduced the cost problem to one condition in which
**trade count cancels and hit rate never appears**:

```
mean move per trade  >=  2c        (the round-trip cost)
```

**At 5 bp/side, `2c` = 10 bp per night.** That is the bar. **The runner's PRIMARY reported
statistic is the measured mean move per trade printed beside `2c`** — not the Sharpe, not the CAGR.
Everything else in the grid is commentary on that number.

### The pre-run arithmetic, and it says this fails

Linear-normal (Grinold) reading. Expected move per trade `= IC × E[z | selected] × σ`, with the
cross-sectional σ of the overnight gap at roughly **1.2%** and ~800–1,200 live names per bar:

| N | tail | `E[z|selected]` | at IC 0.0153 | at IC 0.0163 (arm 2) |
|---:|---|---:|---:|---:|
| 10 | top ~1% | −2.67 | **4.9 bp** | 5.2 bp |
| 25 | top ~2.5% | −2.34 | **4.3 bp** | 4.6 bp |
| 50 | top ~5% | −2.06 | **3.8 bp** | 4.0 bp |
| *1* | *the single worst name* | *−3.24* | ***5.9 bp*** | *6.3 bp* |

**Against a 10 bp toll, every cell falls short by roughly a factor of two — and so does the deepest
cut that exists.** To reach 10 bp at IC 0.0153 requires `|E[z]| = 5.45`, a tail no 1,000-name
cross-section contains. **Concentrating harder cannot fix this**, because `E[z]` grows
logarithmically in the cut while the toll is fixed. It is [FINDINGS §1a](../FINDINGS.md) in a new
costume: **selectivity redistributes return into fewer, larger trades — which helps costs and
nothing else — and here the help is not enough.**

**The one channel by which this arithmetic could be wrong, declared in advance:** it assumes
normality and reads a **Spearman** IC as though it were Pearson. **Overnight gaps are fat-tailed**,
and the tail is exactly where a top-N cut lives, so the realised move could exceed the normal
prediction. **That is why the study measures the quantity instead of asserting it.** The estimate
above is a prior, not a result, and the runner is what settles it.

### And the breakeven fee, reported the way D264 reported it

**`breakeven_bps` — the per-side fee at which the book's net excess return reaches zero**, borrow
held at 3%/yr. A property of the book rather than of my cost assumption, so a reader who disagrees
with 5 bp can substitute their own and re-read the verdict without re-running anything.

**5 bp/side is carried unchanged from D256/D279/D281 for comparability, and it is probably
optimistic here.** This construction exits into the **opening auction** — the widest-spread,
highest-imbalance print of the session — where D279's book exited at a close. **Nothing is adjusted
for that**, because re-costing a construction to a number chosen after seeing it fail is the move
this programme does not make. **`breakeven_bps` is the statistic that carries the objection.**

---

## A KNOWN CONFOUND, DECLARED BEFORE THE RUN — ex-dividend drops live in the overnight gap

**A stock goes ex-dividend at the open. The drop is therefore inside `open(t+1)/close(t)`, and a
short OWES the dividend rather than earning it.** D280's −0.01531 gap IC was measured on **raw
OHLC**, which contains those drops — and its own docstring says so: *"`gap` and `intraday` are built
from RAW OHLC and therefore exclude dividends"*.

**So part of the measured gap edge may be nothing but dividend mechanics**, and it would be
**exactly the wrong sign for a short**: a rule that ranks down-accelerating names ascending will
tend to hold high-yield, falling names on their ex-dates.

**What the runner does about it, specified here rather than discovered later:**

1. **The short is CHARGED the dividend, correctly.** `overnight_total_log` adds
   `log1p(dividend(t+1) / open(t+1))` to the gap, and the position is negative, so the short pays
   it. The sidecar `B.EVENTS` carries the amounts; the runner parses **both shapes**
   (`["2016-11-08T00:00:00", 0.09]` and `{"date":…, "amount":…}`) exactly as `load_ragged` does.
2. **The parse is cross-checked against the loader and the run aborts if it disagrees.**
   `panel.total_log_returns − panel.log_returns` is, by construction, the loader's own
   `log1p(amount/close)` on every ex-date bar. The runner rebuilds that quantity from its own parse
   and asserts equality to 1e-9. **A dividend parse that silently drops a symbol would understate
   the charge on precisely the names this book holds.**
3. **Both readings are reported side by side** — mean move per trade **on the raw gap** and **after
   the dividend charge**. The difference, in bp per night, is the dividend drag on this book, and it
   is a number this programme has never measured.

**AND THIS STUDY HAS A DECLARED DEPENDENCY.** A concurrent check is measuring how much of the
−0.01531 gap IC survives dividend adjustment. **If that check materially reduces the gap IC, D282 is
probably not worth running at all** — the arithmetic above already fails by a factor of two at the
IC as measured, and a dividend-shrunken IC fails by more. **The dependency is declared rather than
ignored, and the decision to run belongs to whoever reads that check.**

---

## The look-ahead self-check — mandatory, and it has already failed once on this fixture

**D279's first result did not exist.** `top_n` ranked with `score[:, t]` — `hist_L` from the close of
the very bar the position was about to earn — and `top25` scored **+2.250 Sharpe unlagged against
−0.638 lagged**. `corr(hist_L at t, return at t) = +0.0737`; `corr(hist_L at t−1, return at t) =
−0.0103`. **The score is 98.05% the same number one bar earlier and the entire result was in the
other 1.95%.**

`C.top_n` and `C.lag1` now lag internally and unconditionally. **A fix in a dependency is not a
guarantee in a caller.** The runner carries **three** checks, all of which must pass before anything
is scored:

| | check | what it asserts |
|---|---|---|
| **L1** | `audit_lag` | for every bar, the held set is **re-derived from `score[:, t−1]` in a SECOND, INDEPENDENT implementation** and asserted equal to the book actually scored. It deliberately does not call `top_n` — a check that shares the code it checks cannot disagree with it |
| **L2** | `audit_return_window` | for a random sample of held cells, the credited return is **recomputed directly from the raw `Stamped`/`Bar` objects** and asserted equal to `open(t+1)/close(t)` plus the ex-dividend charge. **This is what proves the earned quantity is the overnight leg and not the bar** |
| **L3** | `assert_not_close_to_close` | the earned grid is asserted **materially different** from `panel.total_log_returns`, with the correlation printed. **A silent reuse of close-to-close scoring is the one defect that would invalidate the entire study, and it would be invisible in the output** |

**A failed assertion aborts the run.** All three are reported with the result whether or not they
pass.

**The separation this buys, stated plainly:** the information used to choose the held set ends at
**close(t−1)**; the earned quantity begins at **close(t)**. **A full trading session separates
them.**

### One thing deliberately left on the table, and it is declared so it cannot be taken later

**A book that enters at close(t) could legitimately rank on `hist_L[t]`** — close(t) precedes the
overnight leg, so that is not look-ahead *for this construction*. **D282 does not do it.** D280's IC
was measured with the lagged score, and swapping in the contemporaneous score after seeing that
measurement would be a fresh arm dressed as an implementation detail. **The runner prints
`corr(hist_L[t], overnight[t])` beside the lagged version so the size of what is being forgone is
visible — and using it requires its own pre-registration.**

---

## The controls — matched count is NOT matched turnover

D279 learned this the expensive way. **Both** controls are pre-registered.

| | control | what it matches | why it is not enough alone |
|---|---|---|---|
| **`rnd-N`** | N names drawn at random **each night** | count, nights, N | **churns 5–6× harder on a close-to-close book** and pays that multiple in fees. It differs from the treatment in *two* ways |
| **`per-N`** | **persistent** random — draw at random, then HOLD the draw while the name is live, refilling only vacancies | count, nights, N, **and name persistence** | the control hurdle C should always have carried. `persistent_rnd` copied unchanged from `scripts/d279_turnover_decomposition.py` |

**One thing about `rnd-N` changes on an overnight book and it is recorded now, not after the
result:** because **every** night is a round trip for **every** book, `rnd-N`'s fee disadvantage
largely disappears. Its turnover ratio against `top-N` should be **near 1.0×, not 5–6×**. **If it is
not near 1.0×, the runner's cost model is wrong** and that is a falsification of the implementation,
not a finding about the market. **This is a stated pass/fail check on my own code.**

**Both controls are drawn independently for each of the two ranking arms.** They are
arm-independent by construction, so the two draws are a crude read on D279's third recorded defect —
*"`rnd-N` is one draw, not a distribution … C's margin moves by up to 0.16 Sharpe purely on the
seed."* **Both draws are counted as looks in the ledger.**

### Every cell is reported NET and GROSS

**GROSS = zero fees, zero borrow, zero rf**, on a rebuilt panel with `cost_fraction` zeroed — the
same construction `d279_turnover_decomposition.py` uses. **Here, unlike D279 and D281, gross and net
are expected to disagree**, because cost is the binding constraint on this construction rather than
an afterthought. **A cell that clears gross and fails net is the expected outcome and is not a
success.**

---

## Hurdles

| | standard |
|---|---|
| **M** | **Mean move per trade ≥ `2c` = 10 bp**, dividend-charged, measured over held name-nights. **THE DECISIVE ONE** |
| **V** | **Positive net CAGR** after fees, financing and **one night of borrow per night held** |
| **C** | **Beats BOTH controls — `rnd-N` and `per-N` — on Sharpe AND money, GROSS AND NET.** Four legs per control, **eight per cell, all required** |
| **F** | **Best-of-K floor** ([D228](D228-mining-the-mined-fixture.md)), one shared offset vector, **K = 19**, this study's total cell count |
| **E′** | **Effective independent instruments ≥ 3.0 over the HELD BOOK**, via `eff_over_book` from `scripts/d279_fix_eprime.py` fed the **overnight** return grid — **NOT** `RP.effective_instruments(panel, …)` — and **≥ 500 trades**, a trade being one held name-night |
| **H** | Rotation null, **REPORTED BUT NOT DECISIVE.** See below |

**M and V are two readings of the same arithmetic**, and **M is the one that generalises**: D265
established that in the `move ≥ 2c` form the trade count cancels and the hit rate never appears, so
M is a statement about the construction rather than about this fixture's realised path. **A cell
must clear both; if they disagree, the disagreement is itself reported.**

**`trades` is redefined for this construction and the redefinition is declared.** `RP.score`'s
`entries` counts position *initiations* via `diff(pos) > 0`, which on a nightly book undercounts
badly — a name held four nights running is four round trips and one "entry". **Here a trade is one
held name-night.** E′'s 500-trade leg is read against that count.

### Hurdle H is broken on this fixture and carries no verdict

D279 established it under [R7](../RULES.md#r7)'s corollary — *a hurdle that everything clears is not
evidence, it is a broken hurdle*:

> `S1_short|all` scored the **100th percentile on both legs** with **−0.757 Sharpe** and **−2.45%
> CAGR**, against a null sitting at **p50 −1.058 / p95 −0.986**. Seven of fourteen cells cleared it
> and all fourteen lost money.

**A per-symbol rotation null on a near-always-on book is close to the identity**, and D282's base
holds nearly every live name every night. **H is computed, printed, and explicitly excluded from
every verdict.** The verdicts rest on **M, V, C and F**, with **E′** as a disclosed side condition
whose known weakness — in a rotating book almost no *pair* shares 250 held bars, so it degenerates
into *"how many names accumulated 250 held nights"* — is declared here rather than discovered
afterwards. **Per-symbol P&L concentration is reported beside every cell** as the thing E′ was
supposed to guard.

---

## Predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **O1** | **Hurdle M fails in every one of the 18 ranked cells** — mean move per trade stays **below 10 bp** at every N, on both arms, dividend-charged. **V fails with it and the stop fires** | **AGAINST** | **high** |
| **O2** | **The gross edge is REAL and CORRECTLY SIGNED** — mean move per trade is **positive** at N = 10 and N = 25 on both arms, and `top-N` beats `per-N` on **gross** Sharpe at all three N | **for** | **moderate** |
| **O3** | **Move per trade DECLINES monotonically in N** (10 > 25 > 50) on both arms, because a wider cut samples a shallower tail. **And no N reaches the bar**, so the failure is structural rather than a matter of tuning | neutral | **moderate-high** |
| **O4** | **The dividend charge costs at least 1 bp per night** of the raw-gap move on the held book — **a quarter or more of the expected ~4 bp edge** — so any "raw gap" reading of this construction overstates it | **AGAINST** | **moderate** |

**The honest prior, written down before the run: this FAILS ON COST while showing a genuine,
correctly-signed gross edge.** ~4 bp of move against a 10 bp toll, 252 times a year, is roughly
**+10%/yr gross against a 25%/yr toll per unit of exposure**. **O1 and O2 are the two halves of that
sentence and they are pre-registered together**, so the result cannot be read as either a vindication
or a wipe-out without both.

**What would falsify each:**

- **O1** — any cell with a dividend-charged mean move per trade at or above 10 bp. **That would mean
  the fat tail beats the normal approximation by more than a factor of two**, and it would be the
  finding, ahead of any cell's CAGR.
- **O2** — a non-positive mean move per trade, or a loss to `per-N` gross at any N. **That says the
  −0.01531 gap IC does not survive translation into a top-N book** — most likely because the IC is a
  whole-cross-section statistic and the extreme tail behaves differently from the body. It would
  close the overnight branch harder than O1's cost failure does, because a cost failure leaves a
  cheaper venue open and a sign failure does not.
- **O3** — a flat or increasing profile in N. That would say the signal is **not** concentrated in
  the tail, which contradicts the whole rationale for a top-N construction and would point back at
  the unconcentrated base.
- **O4** — a dividend drag under 0.5 bp/night. That would mean the confound is real but immaterial,
  and the concurrent gap-IC dividend check should come back close to unchanged.

---

## Stop

**If no cell clears M and V, the overnight-only short is closed on this fixture.** No fourth N, no
third ranking arm, no re-cut of the universe, no alternative exit time. **Nothing is tuned after a
result is seen.**

**Together with D256 (the universe), D279 (the concentrated construction) and D281 (the unfiltered
ranking), a failure here closes the dead-inclusive daily fixture for `hist_L`-ranked directional
shorts in EVERY decomposition of the bar** — the whole bar, and now each of its two halves
separately.

**Two things a failure explicitly does NOT close, and they are named now so neither can be claimed
as a rescue afterwards:**

1. **The cost venue.** A construction that clears gross and fails on a 10 bp nightly toll is exactly
   what [R12](../RULES.md#r12) says must be **re-costed** before being discarded. **It cannot be
   re-costed onto futures** — the edge is single-name idiosyncratic and no retail single-name futures
   contract exists, the same wall [FINDINGS §9](../FINDINGS.md) recorded for D264. **What it would
   license is a cheaper execution question, not a new signal**, and that is a different study.
2. **The intraday leg.** D280 measured the QUALIFYING set's intraday IC at **+0.00868, t +2.85** —
   significant, and pointing the **other way**. **A long intraday arm is NOT licensed by this
   record**, has never been pre-registered, and would need its own. It is written down here so that
   a D282 failure is not quietly converted into a D283 that mines the other half of the same
   measurement.

**If a cell clears, it is not a book entry.** Under [R8](../RULES.md#r8) admission requires a
pre-registered out-of-sample test, and **this fixture has no untouched cohort left.** D246's reserved
wide-universe cohort is a different fixture and is not spent here.

---

## Ledger

Under [R13](../RULES.md#r13) — scoped to a hypothesis, carried where it shaped the search.

| count | N | why |
|---|---:|---|
| **fresh — 2 ranking arms × 3 N × 3 modes (`top`/`rnd`/`per`), + 1 unranked base** | **19** | controls are counted like anything else; D228's floor does not care what a cell was built to prove |
| carried: **D279**, 14 pre-registered + 6 persistent controls | 20 | same fixture, same arm family, same score |
| carried: **D256** | 21 | same fixture, same arms, and D279 and D281 both carried it for the same reason |
| **total** | **60** | |

**D280 is disclosed and scores NO cell.** It is a cross-sectional IC measurement that admits no
candidate and clears no hurdle — but it **shaped this search space entirely**, including the choice
of the overnight leg and the second ranking arm. R13's second test is what matters, not whether a
look produced a return.

**[D281](D281-the-unfiltered-ranking.md)'s 10 fresh cells are DISCLOSED and NOT carried, and the
judgement is a close one.** D281 and D282 are **siblings, not parent and child**: both descend from
D280, and D282's universe, score and controls were fixed by D280's part-A measurement rather than by
anything D281 found. R13 test 2 asks whether the earlier work shaped this search space, and D281's
did not. **The conservative reading, in which every look on this fixture since D279 is carried, is
70, and it is stated here so the exclusion cannot be mistaken for an oversight.** Neither number
changes a verdict: **the ledger is bookkeeping and the empirical best-of-19 floor is the test.**

**NOT carried:** the single-name **intraday** programme (D264–D278, ~430) — different fixture,
different frequency, and the construction tested here was named by
[FINDINGS §6](../FINDINGS.md) and D280 rather than by that programme. The ETF programme's 45,783 is
not carried for the reasons R13 already records.

---

## What the runner must produce, so R6 cannot be satisfied by prose

Every hurdle above names a test, and **[R6](../RULES.md#r6) says a hurdle is not cleared until that
test is run and its output points at an artifact field.** The runner writes
`data/d282_overnight_summary.json` carrying, per cell: `mean_move_bp` and `two_c_bp` beside each
other, `mean_move_bp_raw_gap`, `dividend_drag_bp`, `breakeven_bps`, `breakeven_borrow`, net and
gross Sharpe/CAGR/money, all **eight** C legs stored individually rather than only their
conjunction, `eff_book` with its held-name count, `top_name_share`, `trades`, `turnover_units`, the
rotation-null percentiles with the null's own p50 and p95, and the three lag/return audits with
their verification counts. **A conjunction that hides which leg failed is not a reported hurdle.**
