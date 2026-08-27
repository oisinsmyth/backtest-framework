# D226 — Does the volume regime gate survive 57 instruments?

**Status:** Committed (R1, R2, R5 confirmed; R3 and R4 falsified) — **the spike moved**
**Date:** 2026-08-27
**Category:** Validation & research integrity
**Source:** The generalisation question D227 could not answer, redirected to breadth

> A result section will be appended and nothing above it edited.

## Provenance, stated first

**The design was fixed and approved before any code was written.** The runner
(`scripts/run_etf_intraday_gate.py`) was then built to it and has run **only a 3-symbol,
2-window smoke test** on separate `*.smoke.*` paths, producing no verdict and no cell that
enters this ledger.

**But the runner exists before this record does**, which is not the order D217–D224 used, and
saying so is cheaper than being caught. What that costs is small — every parameter, hurdle and
grid below was settled in the approved plan before implementation, so nothing was chosen after
seeing a number. What it does not cost is nothing, and D225's provenance section is the
template.

## The question

D224 and D225 established that a **volume regime gate** — `EMA(n) > SMA(n)` on volume, gating
trade entries only, never exiting — beats its matched-count random null on BTC and ETH, at two
sampling rates, by roughly six times the mechanical benefit of trading less.

D225 also found the damaging thing: **the working window is one point wide.** Across
`[12, 24, 36, 50, 72, 100, 140, 200, 300, 480]` hours only 50h is positive-net on BTC, both
neighbours are negative, and at 200h the identical construction **inverts** into a significant
anti-signal at the 0.5th percentile of its own null.

So: **is that a property of the method, or of two coins over one span?**

D227 tried to answer it by splitting the crypto span in time and was abandoned on power — the
proposed stop would have closed the study 93% of the time on an effect that is real by
assumption. Its conclusion was explicit: **the answer is more instruments, not thinner slices
of the same two.**

## The test bed

`data/fixtures/etf_intraday_15m_raw.csv.gz` — fetched, split-adjusted and committed for this
study.

| | |
|---|---|
| 57 ETFs, 3,194,849 rows | 2018-01-02 → 2026-08-26, 2,174 sessions |
| 15m bars, 26 per session (09:30–15:45) | **PPY = 26 × 252 = 6,552** |
| **zero-volume bars: 0 (0.0000%)** | 18 half-days derived and dropped |
| 12 splits back-adjusted, prices *and* volumes | 1,955 dividends, so both return bases exist |

**Why the numbers make this the right fixture**, measured before designing:

| | daily ETF | **intraday ETF** |
|---|---:|---:|
| live span | 6.01 y | **7.94 y** |
| entries per ETF | 34 (min) | **359** (median) |
| pooled trades | 2,418 | **20,463** |
| after a 50% gate | 8–17 | **179** |
| mean pairwise correlation | 0.468 | **0.282** |
| effective independent instruments | 2.10 | **3.40** |
| **effective trades** | **~89** | **~1,219** |

Two consequences that decided the design rather than being worked around:

1. **Hurdle E is NOT redefined.** The original D217/D218 conjunction — *"≥100 signals pooled
   per arm, and ≥30 entries per ETF"* — passes on both legs and **still passes after a 50%
   gate** (179 against 30). The redefinition debated earlier is unnecessary, which is a far
   better outcome than winning the argument for it.
2. **D220's stop is NOT overridden.** It is scoped to *"this fixture"* — the daily one. This
   is a different fixture, so the stop stands.

## The arms

**Parent.** Impulse MACD `(136, 36)` long-flat, `lag=1`. This is *literally* the crypto arm:
D221 established the indicator is scale-free in bars, so 136 bars at 15m is the same estimator
on both fixtures. Warm-up 4,049 bars, leaving **52,007 live bars = 7.94 years**.

**Gate.** `EMA(w) > SMA(w)` on volume, evaluated at the entry bar only, never exiting. A
blocked trade skips the whole run. `ok[:, 1:] = live_gate[:, :-1]` — the exposure held through
bar *t* is decided from bar *t−1*, so the newest legitimately available volume is `volume[t−1]`.

**Sweep, declared here and counted in full.** Windows in **bars**:
`(48, 96, 144, 200, 288, 400, 560, 800, 1200, 1920)`. **200 is D224's committed `VOL_WINDOW`**,
so the gate matches the crypto study in the same units. Every window is defined everywhere the
arm trades — the longest is inside the 4,049-bar warm-up — so there is **no per-window start
and no span truncation**, and all ten cells are directly comparable.

**The sweep is the point of the study.** D225's one-point-wide spike is the strongest argument
against the gate, and 57 instruments is the only way to test whether that fragility is a
property of the method.

## Hurdles

- **H — carries the verdict.** Beat the **matched-count random null** at ≥95th percentile on
  **both** net Sharpe and net total return. On a book whose average trade is fee-negative, any
  removal gains money mechanically; this is the only control separating a real effect from
  having traded less.
- **E — unchanged.** ≥100 pooled **and** ≥30 entries per ETF. Both legs reported.
- **P.** Beat the unfiltered parent on both metrics.
- **G.** Clear `expected_max_sharpe`, with **`var_trials` from the simulated null**, never from
  the study's own cells (D224's correction — cells gave an unusable +4.9).

## Three things named before the run

1. **Effective sample beside the raw count.** 20,463 pooled trades are **~1,219 effective** at
   ρ = 0.282. Both are reported so nobody quotes the pooled number as a sample size.
2. **Bar-time and calendar-time diverge.** 136 bars is 34 *continuous* hours on crypto (1.4
   days) but 34 *trading* hours here (5.2 calendar days, with overnight gaps). Bar counts match;
   calendar spans do not. D221's invariance is a bar-count statement, so bars is the right
   match — and D219's amendment already requires cross-fixture comparison on
   **`arm − matched buy-and-hold`**, never raw Sharpe.
3. **Both return bases.** WP0 supplied dividends, so price-only *and* dividend-adjusted are
   reported, the way D218's hurdle D named both metrics up front rather than in an addendum.
   Direction: a long-flat arm invested ~50% of the time collects ~50% of dividends while
   buy-and-hold collects 100%, so omitting them would understate the benchmark roughly twice
   as much as the arm. **Hurdle H is unaffected either way** — arm and null share a basis.

## Ledger

| count | N | what it includes |
|---|---:|---|
| fresh | **10** | the declared window sweep |
| + hypothesis lineage | **78** | D220's 12, D224's 10, D225's 46 |
| **+ disclosed ETF prior** | **45,819** | plus 45,346 registry configs + the 395 structure/terrain bar |

**Count 3 carries the verdict.** D225's 40-cell sweep attaches specifically, because the
200-bar gate is used *because* that sweep pointed there.

**What does not transfer: D225's crypto prior of 3,739.** It was logged on Binance data and has
no bearing on an ETF study; carrying it here would be arithmetic theatre. An early draft of the
runner declared 3,879 — exactly that mistake — and it is recorded because the error is easy and
looks diligent.

Zero-look: the fixture census, the oracle bound, the matched-count null, the effective-sample
calculation.

## Predictions, committed before the run

| | Prediction | Confidence |
|---|---|---|
| **R1** | The gate clears H on the pooled 57-ETF book at **some** window | **moderate** |
| **R2** | **The 200-bar window is not special here.** If D225's spike were a property of the method it should reappear at the same bar count; I expect it will not | **moderate** |
| **R3** | The window-response profile is **flatter** than crypto's — no single-point spike, no inversion at the long end. 57 instruments average away what two coins expressed | **moderate-high** |
| **R4** | No cell clears G at the verdict count of 45,819 | **high** |
| **R5** | The gate cuts exposure roughly in half and improves net Sharpe while **reducing total return**, the pattern every filter in this programme has produced | **moderate-high** |

**R2 and R3 are the study.** If the profile is flat and positive across many windows, the gate
is a real regime effect and D225's spike was two coins being noisy. If it is spiky *and* the
spike is somewhere else, the gate is curve-fitting and this is where it dies. **If the spike
reappears at 200 bars specifically, that is the most interesting outcome available** and would
be the first evidence that the window itself means something.

**What would change my mind:** R4 failing — a cell clearing a floor built from 45,819 looks.
Nothing in this programme has ever done that.

## Pre-committed stops

- **No parameter search.** Ten windows, one book, one parent. If the gate fails, the answer is
  not an eleventh window.
- **The random-null gate.** A cell that improves net PnL without clearing its matched-count
  null is reported as a **failure**, in those words.
- **Nothing is promoted without unmined data**, whatever the result (D215/D216).

---

## RESULT

*Appended after the run. Nothing above this line was edited.*

**Produced:** 2026-08-27 · **Reproduce:** `uv run python scripts/run_etf_intraday_gate.py`
(offline, deterministic, seed 0, 9.4 min) · Page:
[`ETF_INTRADAY_RESULTS.md`](../../ETF_INTRADAY_RESULTS.md) · Artifact:
`data/etf_intraday_gate_summary.json`

### The one-sentence version

**The gate clears its selectivity null on 57 ETFs — at exactly one window, and it is not the
one that worked on crypto: 96 bars here against 200 bars there, with 200 landing at the 45th
percentile on this fixture. Two spiky profiles with their spikes in different places is what
a fitted parameter looks like, not a discovered one.**

### The sweep

Dividend-adjusted, the primary basis. Parent: **+0.307** net Sharpe, **+24.9%** total, 49.7%
exposure.

| bars | hours | kept | removed | Sharpe | total | pct in null (Sh / $) | perm | H |
|---:|---:|---:|---:|---:|---:|---:|---:|:--:|
| 48 | 12 | 11,149 | 45% | +0.239 | +10.8% | 24 / 28 | 27 | |
| **96** | **24** | **10,585** | **48%** | **+0.467** | **+20.3%** | **98 / 98** | **98** | **PASS** |
| 144 | 36 | 10,773 | 47% | +0.368 | +17.0% | 79 / 86 | 87 | |
| **200** | **50** | 11,421 | 43% | +0.288 | +14.5% | **45 / 62** | 63 | *(D224's window)* |
| 288 | 72 | 11,394 | 44% | +0.392 | +20.5% | 87 / 95 | 96 | |
| 400 | 100 | 10,755 | 47% | +0.314 | +15.2% | 57 / 74 | 77 | |
| 560 | 140 | 10,642 | 47% | **+0.008** | +0.4% | **0 / 0** | 0 | |
| 800 | 200 | 10,830 | 46% | +0.176 | +10.0% | 6 / 22 | 24 | |
| 1200 | 300 | 10,552 | 48% | +0.320 | +18.5% | 59 / 96 | 96 | |
| 1920 | 480 | 10,664 | 47% | +0.209 | +12.2% | 12 / 42 | 46 | |

**One window of ten clears H. `h_region_width = 1`, `contiguous = False`.**

### Scoring my own predictions

| | Prediction | Outcome |
|---|---|---|
| **R1** | The gate clears H at some window | **CONFIRMED.** Window 96, at the 98th percentile on both metrics and on the permutation test |
| **R2** | **The 200-bar window is not special here** | **CONFIRMED.** D224's committed window lands at the **45th percentile** — indistinguishable from noise on this fixture |
| **R3** | The profile is flatter; 57 instruments average away what two coins expressed | **FALSIFIED.** It is exactly as spiky. One point wide, non-contiguous, and 560 bars is a near-total collapse to +0.008 at the 0th percentile |
| **R4** | No cell clears G at 45,819 looks | **FALSIFIED.** Three do — 96, 144 and 288. See below; this is a first for the programme |
| **R5** | Better Sharpe, less money — the pattern every filter here has produced | **CONFIRMED**, and it is what kills the study |

**Three of five.**

### What is actually true

**1. The spike moved, and that is the finding.**

D225 measured a one-point-wide spike at **200 bars** on crypto and an inversion at 800. Here
the spike is at **96 bars** and 200 is nothing. Both profiles are spiky; the spikes are in
different places.

> A real regime effect should live at a window with some physical meaning and degrade
> gracefully either side of it. **An effect that appears at one window per fixture, at a
> different window each time, is a parameter being fitted to noise.** That is the outcome
> this study was designed to be able to see, and it is the one that arrived.

The pre-registration named this branch in advance: *"If it is spiky and the spike is somewhere
else, the gate is curve-fitting and this is where it dies."*

**2. Three cells cleared the multiplicity floor — the first time anything in this programme
has.**

| | null sd | floor @ 10 | floor @ 45,819 | Sharpe |
|---|---:|---:|---:|---:|
| window 96 | 0.082 | +0.129 | **+0.347** | **+0.467** |
| window 144 | 0.083 | +0.130 | +0.349 | +0.368 |
| window 288 | 0.081 | +0.128 | +0.343 | +0.392 |

The reason is the fixture, not the effect: **57 instruments make the matched-count null far
tighter** (sd ≈ 0.082 against crypto's ≈ 0.24), so the floor falls from +0.88 to +0.35 even at
a *larger* look count. This is the cleanest demonstration yet of D219's amendment — the floor
is set by the null's dispersion, not by N.

**It does not rescue the gate.** Clearing a floor while failing selectivity at nine of ten
windows is evidence about the fixture's power, not about the method.

**3. Nothing survives, because the gate loses money to its own parent.**

Window 96 clears H, E and G — and fails **P**. It beats the parent on Sharpe (+0.467 against
+0.307) and loses on money (**+20.3% against +24.9%**). The programme's most consistent
finding, for the sixth study running.

**4. Fetching the dividends is what exposed that, and it changed the verdict.**

| window 96 | parent Sharpe | parent total | gate Sharpe | gate total |
|---|---:|---:|---:|---:|
| price-only | +0.199 | **+15.5%** | +0.363 | **+15.5%** |
| dividend-adjusted | +0.307 | **+24.9%** | +0.467 | **+20.3%** |

**On price-only the gate ties its parent on money. On dividend-adjusted it loses by 4.6
points.** The direction is exactly as predicted before the run: an arm invested ~50% of the
time collects ~50% of dividends while the parent collects 100%, so omitting them flatters the
gate.

**Had WP0 not fetched dividends, hurdle P would have been a tie rather than a failure**, and
the study would have reported a cell clearing H, E, G and drawing on P. D217 discovered this
in an addendum two days late; here it was named up front and the fetch was done because of it.

### Defects and disclosures

**The runner was written before this record**, disclosed in the provenance section above. Only
a 3-symbol smoke test preceded the pre-registration, on separate paths, and no cell from it
enters this ledger.

**An early draft of the runner declared `VERDICT_COUNT = 3879`** — D225's *crypto*-fixture
arithmetic carried into an ETF study, which would have applied a prior of 3,739 Binance looks
to a fixture they have nothing to do with. Corrected to 10 / 78 / 45,819 before the run.

**The parent is positive here where it was negative on crypto** (+0.307 against −0.284), and
the reason is costs: ~1.8 bp per side on ETFs against 10 bp on crypto. So the "any removal
gains money mechanically" dynamic that made hurdle H load-bearing on crypto is **weaker here**
— the ETF parent covers its fees. H is still the right hurdle, but it is doing less work.

**The run is fully sequential.** 9.4 minutes on one of sixteen cores; numpy's OpenBLAS
threading does not touch elementwise array work. `breakout_nulls.path_null` is the repo's
precedent for parallelising a null deterministically if a larger sweep ever needs it.

### Ledger

| count | N | floor |
|---|---:|---:|
| fresh | 10 | +0.129 |
| + hypothesis lineage | 78 | — |
| **+ disclosed ETF prior** | **45,819** | **+0.347** |

### What this changes

**The volume regime gate is closed.** It survived D224 and D225 on two coins and two sampling
rates. Given 57 instruments and its own pre-registered window sweep, it produced a spike at a
*different* window, at one point of ten, while losing money to the arm it filters.

Two studies found a one-point-wide effect. **The windows disagree.** That is the signature of
a parameter fitted to whichever sample it met, and it is a more useful negative than another
failed floor: it explains *why* D224 and D225 looked positive without needing them to be
wrong about their own numbers.

**What survives is the method, not the result.** The matched-count random null, the
floor-from-the-null correction, naming both metrics up front, and pre-registering the sweep
are what made a fitted parameter visible in one 9-minute run instead of surviving three more
studies.

**Nothing here is promoted, and nothing on this fixture continues.** A gate whose window moves
between asset classes does not get an eleventh window.

---

## ADDENDUM — 2026-08-27: the benchmark the study failed to compute

*Prompted by the obvious question the RESULT above does not answer: if the gate reaches
+0.467 Sharpe, why is that not good enough?*

### The defect

**D226 computed no buy-and-hold benchmark.** D219's amendment requires every cross-fixture
comparison to be made on **`arm − matched buy-and-hold`** rather than on raw Sharpe, and the
runner emits no such number. The RESULT above was accepted without checking that it did.

The verdict does not change. The reasoning behind it was incomplete, and the missing half is
the more direct half.

### The number

Equal-weighted 57 ETFs, same span, same cost path, dividend-adjusted:

| book | Sharpe | CAGR | vol | max DD |
|---|---:|---:|---:|---:|
| **buy and hold** | **+0.563** | **9.83%** | 16.6% | −35.6% |
| parent, no gate | +0.307 | 2.86% | 9.3% | — |
| **gate @ 96 bars** | **+0.467** | **2.38%** | 5.1% | — |

**The gate's Sharpe is below buy-and-hold's.** The best cell in the study, at the one window
that cleared selectivity, is worse risk-adjusted than owning the basket and doing nothing.

Vol-matching does not rescue it — the D219 leverage argument, applied honestly:

| book | leverage to B&H vol | levered CAGR |
|---|---:|---:|
| buy and hold | 1.00× | **9.83%** |
| parent, no gate | 1.79× | 5.12% |
| gate @ 96 bars | 3.26× | **7.77%** |

At matched risk the gate returns **7.77% a year against passive's 9.83%**, and that figure is
linear-approximate and ignores financing, so it is an **upper bound** (D219's disclosure rule).

### What this means, stated fairly

**+0.467 is not a bad Sharpe.** In isolation it is roughly what a diversified equity book
delivers, and treating it as obviously worthless would be wrong. The objection that prompted
this addendum was reasonable.

**It is not good enough here for one reason: the alternative was better.** Over 2018–2026 an
equal-weighted basket of these 57 ETFs beat it risk-adjusted, with no trading, no fees and no
20,463 round trips. This is D218's hurdle D restated — *"good Sharpe"* and *"beats the thing
you already had"* are different questions, and this programme has been caught by that
distinction before (D217's dividend addendum, for the same underlying reason).

**One genuine point in the gate's favour**, which the headline should not bury: it runs at
5.1% volatility against buy-and-hold's 16.6%. An investor who cannot tolerate a −35.6%
drawdown is not choosing between these on Sharpe alone. But they would be paying roughly two
points of annual return for that comfort, at 3.26× leverage, before financing.

### Why the RESULT above still stands

The closure rests on two independent arguments and only one of them was made:

1. **The window moved** — a one-point spike at 200 bars on crypto and at 96 bars here, which
   is a fitted parameter rather than a discovered one. This was argued.
2. **It loses to passive** — below buy-and-hold on Sharpe *and* on vol-matched return. This
   was not, because the number was never computed.

The second is simpler, more direct, and should have led. **A study that reports a Sharpe
without its benchmark is reporting half a number**, and the fix is not to argue the verdict
was still right — it is to record that the check was skipped and what it would have said.

### The correction that outlives this study

**Any future runner in this line must emit a matched buy-and-hold on the same panel, cost
path and return basis, and the verdict table must carry `arm − B&H` as a column.** D219's
amendment required it in prose; it was not enforced in code, and prose that is not enforced
gets skipped. `run_macd_ladder.buy_and_hold` already exists and is shape-agnostic — there was
no cost to doing this and no reason it was missed beyond not looking.
