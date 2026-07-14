# Pairs trading vs. real frictions: a five-study measurement

**Status: DRAFT (skeleton — all numbers final, prose marked `[TODO prose]` where
narrative polish is pending) · 2026-07-14**

Every result in this document is produced by a committed, deterministic,
offline-reproducible script against one frozen data snapshot
(`54d4e476c0560d473fc1539e8540e0fa1ab371a69dad2f02b9bc6eae9cd671fd`), and every
headline number below is cross-checked against its source artifact by the test
suite (`tests/unit/test_writeup.py`) — if a study is ever re-run and a number
moves, this document fails CI rather than silently lying.

---

## 1. Abstract

We measure whether classical ETF pairs trading — Gatev-style distance selection
refined by cointegration filtering, traded with a z-score mean-reversion rule —
clears *real* trading frictions. Across five controlled studies on 57 liquid US
ETFs (2015–2024), each changing exactly one variable, the answer is two-sided
and precise: **a real, selection-driven gross edge exists (+19.03% over nine
out-of-sample years at 200% gross exposure), and no configuration of account
size or gross exposure lets it clear the full cost of capital.** At low gross,
where the margin-interest threshold vanishes, the edge just pays for its own
implementation (best cell: +0.12%/yr net at 100% gross, $300k) — but against a
4% risk-free rate its Sharpe is -1.61: it cannot pay for the capital it
occupies. Equally important is what produced these numbers: a simulator anchored
to hand-computed golden masters and reconciled penny-exact against an
independent engine, structural (not conventional) look-ahead prevention, and
pre-committed statistical honesty rules that make the negative result
believable.

## 2. The question

Does distance/cointegration pairs trading on liquid US sector ETFs clear real
trading frictions — commissions, spread, market impact, borrow, and margin
financing — at any account size and any gross exposure?

The question is deliberately negative-capable. The framework this program runs
on was built under one governing constraint (PHILOSOPHY.md): *it must be able to
say "no edge" and be believed.* Most backtests cannot — look-ahead, cost
optimism, and unlogged multiplicity make their positives unfalsifiable and their
negatives uninformative. The methodology section explains what "believed" means
mechanically here. `[TODO prose: one paragraph on why pairs trading is the
right vehicle for this demonstration — famous, simple, heavily mined.]`

## 3. Methodology: why these numbers can be trusted

This section precedes the results on purpose: for a strategy this well-known,
the trustworthiness of the measurement *is* the product.

- **The simulator is anchored to references we didn't write.** A hand-computed
  golden-master scenario asserts every fill, carry accrual, dividend flow, and
  NAV line against an independent calculator (the arithmetic lives in
  plain-text `.hand.txt` files beside the tests). Cross-engine reconciliation
  against vectorbt 1.1.0 on an identical weight schedule is penny-exact: 1,370
  trades in both engines over 2,515 bars, identical final value
  $159,233.023491, maximum relative curve divergence 1.30e-12
  ([full report](verification/cross_engine_reconciliation.md)).
- **Look-ahead is prevented structurally, not by convention.** Strategy code
  receives `DataView` objects that physically do not contain future bars — no
  reflection trick can read what was never stored. Walk-forward fitters receive
  views built from training slices only; the z-score window ends at the
  previous bar by construction.
- **Data is frozen and content-addressed.** All five studies run against the
  same snapshot, identified by the SHA-256 of its payload
  (`54d4e476…`). Cleaning is drop-and-report (it made zero changes to this
  universe and reported zero); validation gates quarantine data rather than
  papering over it.
- **Every trial is logged, append-only.** A SQLite registry records every
  (config, window, cost-multiplier) run under a deterministic hash — 2,170
  trials across the six study artifacts — and the Deflated Sharpe Ratio pulls
  its trial count N and variance V from the registry, never from a typed-in
  number: N counts each study's one-per-window real-cost trials (a
  cost-multiplier re-run is a sensitivity point, not an extra trial) and V is
  in the same per-period units as the observed Sharpe (D98). Our DSR
  implementation reproduces the Bailey–López de Prado worked example
  (N=46 → 0.9505; N=100 → 0.9004).
- **The result survives its own conventions.** Same-bar-close fills and
  full-sample impact calibration are the two optimistic conventions the
  studies inherit; re-running the strongest configuration (v2) with
  next-bar-open fills and train-window calibration retains most of the gross
  edge (+16.79% vs +19.03% at 0×) and deepens the real-cost loss slightly
  (-7.90% vs -6.43% at 1×) — the headline conclusion is not a fill-timing
  artifact ([artifact](results/convention_sensitivity.md), D103/D105).
- **One variable per study version.** Each study changes exactly one thing and
  holds everything else byte-identical (`None`-default hooks in the study
  runner preserve prior behavior exactly; the β=1 special case of study 3's
  machinery reproduces study 2's equity curve to the penny as a tested
  identity). Deltas between studies are therefore attributable, not suggestive.
- **Pre-registration, including one the data corrected.** The project's
  planning documents (committed before any code) predicted the capacity story
  as "doesn't clear costs at retail scale, clears at £X AUM." The measurement
  came back different — no size clears at full gross, and low gross clears
  implementation but not the capital hurdle. The prediction and its correction
  are both part of the record; that is what the discipline is for.

| Study | The one variable changed | Held fixed |
|---|---|---|
| v1 | — (baseline) | universe, windows, costs, trading rule |
| v2 | pair selection (+ cointegration filter) | everything else, byte-identical |
| v3 | hedge ratio (fitted β instead of 1:1) | selection from v2, byte-identical |
| capacity | account size ($10k–$100M) | v2 configuration at every level |
| gross | gross exposure (50%–200%) | v2 configuration at every cell |

`[TODO prose: a short paragraph on the gate discipline — 12 verification steps,
each closed only by its passing gate — with a link to VERIFICATION_SCHEME.md.]`

## 4. Data

57 liquid US ETFs (sector SPDRs, industry, country, commodity, rates), daily
bars 2015–2024, one provider (yfinance), committed to the repository as a
frozen fixture (2,285 dividends, 14 splits — including XOP's 1-for-4 on
2020-03-30, OIH's 1-for-20, and XLF's 1.231 ratio encoding the XLRE spin-off).
Corporate actions use a two-frame model: signals see the provider's
split-adjusted (return-continuous) frame; fills, costs, and NAV use a
reconstructed as-traded frame, with splits scaling positions and declared-frame
dividends flowing as explicit cash (shorts pay them). Walk-forward: 252-bar
train / 63-bar test / 63-bar step → 35 out-of-sample windows, 2,205 OOS bars,
stitched with NAV chaining so the curve compounds like one account.
`[TODO prose: universe table as an appendix.]`

## 5. The cost model

Five friction bricks, each individually gate-tested, composed in a stack:

| Brick | Economics | Scale behavior |
|---|---|---|
| IBKR commission | $0.005/sh, min $1.00/order, cap 1% of value | minimums bind SMALL accounts |
| Spread | 1bp of notional | scale-invariant |
| √-impact | fraction = σ·√(Q/ADV); dollars ∝ Q^1.5 | binds LARGE accounts |
| Borrow fee | 25bp/yr on short notional | scale-invariant |
| Margin interest | 6%/yr on max(gross − NAV, 0) | a THRESHOLD in gross |

σ and ADV are calibrated from the full sample — a mild, documented look-ahead
in cost parameters (never in signal), restated in every artifact. The standard
robustness tool is a uniform cost multiplier sweep (0×–4×); studies 4–5 exist
because the sweep is structurally blind to the two scale-dependent rows above,
which only a direct account-size / gross-exposure measurement can see.

## 6. Five studies, one variable each

### 6.1 Study v1 — the Gatev baseline: tracking is not mean reversion

Top-5 pairs by normalized-price distance (of 1,596 candidates per window),
z-score rule (lookback 30, enter |z|>2, exit |z|<0.5, hysteresis), 200% gross.
**Gross +3.45% over nine years (~0.4%/yr — essentially nothing), -13.01% at
real costs.** ([artifact](results/pairs_study_v1.md)) The distance score
selects pairs that *tracked*; it cannot distinguish a stationary spread from a
slowly diverging one.

### 6.2 Study v2 — cointegration filtering: the edge appears

One change: selection becomes Gatev prefilter (top 50) → Engle-Granger β with a
[0.7, 1.3] coherence window → ADF-statistic rank (statistic-only, rank not
threshold) → top 5. **Gross +3.45% → +19.03%. Profitable at half costs
(+5.70%); -6.43% at full retail costs.** ([artifact](results/pairs_study_v2.md))
The v1→v2 delta is attributable to selection alone: asking "does the spread
mean-revert?" instead of "did the prices track?" is worth ≈1.6%/yr gross on
this universe.

### 6.3 Study v3 — trading the fitted hedge: estimation error costs more than it saves

One change: each pair trades its train-window β (spread = ln A − β·ln B, legs
in the β ratio, weights normalized so gross is identical to v1/v2). **Gross
+19.03% → +6.12%; real-cost net -6.43% → -16.53%.**
([artifact](results/pairs_study_v3.md)) A train-window β carried out-of-sample
imports more estimation noise than hedge benefit — unsurprising in hindsight,
since the selector already restricts to β ≈ 1, leaving the hedge little room to
help while its noise costs in full. **This result is also why the program
stopped short of the originally planned Kalman-filter hedge stage**: a dynamic
hedge re-estimates continuously exactly the parameter whose one-time estimation
already out-cost its benefit. An evidence-based cut, not a timeout.

### 6.4 Study 4 — capacity: no account size clears at full gross

One change: account size, $10k–$100M, with the real unscaled cost stack (the
bricks themselves produce the size dependence). The predicted hump appears —
commission minimums punish the small end, impact the large end — and the whole
curve sits below zero:

| AUM | $10k | $30k | $100k | $300k | $1M | $3M | $10M | $30M | $100M |
|---|---|---|---|---|---|---|---|---|---|
| Net /yr | -2.53% | -1.28% | -0.76% | -0.68% | -1.07% | -1.91% | -3.51% | -5.86% | -9.70% |

At the $300k optimum (-5.77% over the study): ≈+2.01%/yr gross edge vs 2.68%/yr
total drag, roughly half of it the scale-invariant floor of a ~200% gross book
(margin 0.87%/yr + spread 0.38% + borrow 0.11%).
([artifact](results/capacity_analysis.md)) Cross-checks: the $100k row
reproduces v2's -6.43% exactly; gross at $100M is +19.04% vs v2's +19.03%.

### 6.5 Study 5 — gross exposure: the margin threshold pays; the hurdle doesn't

One change: gross exposure (leg_weight 0.25–1.0, i.e. 50%–200% gross). Margin
interest is a threshold cost — max(gross − NAV, 0) — and it collapses exactly
as the piecewise arithmetic predicts (0.866%/yr at 200% gross → 0.220% at 150%
→ 0.000% at ≤100%). **Five low-gross cells turn absolutely net-positive — the
program's first — best: +0.12%/yr at 100% gross, $300k, against a +1.03%/yr
gross edge. But the best cell's Sharpe against the 4% risk-free rate is -1.61:
it underperforms T-bills by ≈3.9%/yr.**
([artifact](results/gross_exposure_study.md)) At low gross the edge can just
pay for its own implementation; it cannot pay for the capital it occupies.

## 7. Statistical honesty

Every study's real-cost Deflated Sharpe Ratio is 0.0000, with N and V pulled
from the trial registry (2,170 logged trials program-wide; per-study N counts
one real-cost trial per window in daily units, D98). Beyond the
registry count, each window scores 1,596 candidate pairs, and the program has
now run five studies on the same snapshot — so even the registry-fed DSR is
optimistic, and we treat it as one-directional: DSR < 0.95 means "no
demonstrated edge"; a DSR ≥ 0.95 could not have been taken at face value. The
gross sweep's thin positives illustrate why the rule exists: +0.12%/yr on nine
years of daily data is far inside the noise band that five studies of
multiplicity can manufacture. `[TODO prose: one paragraph walking a
non-specialist reader through DSR intuition.]`

## 8. Limitations

- **Single data source** (yfinance), validated but not cross-checked against a
  second provider.
- **Full-sample σ/ADV calibration** in the v1–v3/capacity/gross artifacts — a
  mild look-ahead in cost parameters, never in signal. Now measured rather than
  assumed: per-window train-slice calibration (D102) moves the v2 real-cost
  result by ~0.15pp ([artifact](results/convention_sensitivity.md)) —
  immaterial to every conclusion.
- **No interest on idle cash.** Material for the low-gross studies: a ≤100%
  gross book is mostly idle cash, so real absolute returns would sit closer to
  the risk-free rate — but that return belongs to rf, not to the strategy; the
  Sharpe-vs-rf conclusion is unaffected in direction.
- **√-impact extrapolation.** Participation is reported per capacity level;
  the $100M row trades up to 143.33% of one symbol's ADV — extrapolation,
  flagged as such.
- **Retail rate assumptions at every scale** (6% margin, 25bp borrow).
  Institutional funding shrinks the floor; the drag tables say by how much.
- **Universe selection is itself meta-in-sample.** Liquid, famous,
  sector-coherent ETFs are where pairs trading is *known* to have worked; a
  positive result here would have needed out-of-universe confirmation. (The
  negative result is strengthened, not weakened, by this bias.)
- **Daily bars only**; execution at the close with cost models, not intraday
  microstructure.

## 9. Conclusions & what would change the answer

The program's headline: **selection quality creates a real gross edge;
estimation error destroys attempts to refine it; and the full cost of
capital — not any single friction — is what the edge finally cannot pay.**
The drag decompositions identify the exact levers: at the gross-sweep optimum
the binding items are commission + impact (≈0.5%/yr combined at low gross) and
the opportunity cost of capital (4%/yr). `[TODO prose: quantify the
institutional-assumptions scenario (rf-earning cash sweep, sub-1% funding,
per-share-only commissions) honestly WITHOUT running it as if it were a
result — it is arithmetic on the drag tables, and it still lands near zero
excess.]`

## 10. Future work

- Per-window σ/ADV calibration (closes the D66 caveat).
- An idle-cash interest brick (the one cost-model gap the gross sweep exposed
  as material).
- Parameter sensitivity study (lookback/entry/exit grids, every variant
  registry-logged so the DSR machinery prices the search honestly).
- The options extension, scoped but deliberately not built
  ([scoping decision](options_extension.md)) — trigger conditions include this
  writeup's completion.

## Appendices

- A. The five study artifacts: [v1](results/pairs_study_v1.md) ·
  [v2](results/pairs_study_v2.md) · [v3](results/pairs_study_v3.md) ·
  [capacity](results/capacity_analysis.md) ·
  [gross exposure](results/gross_exposure_study.md)
- B. [Cross-engine reconciliation](verification/cross_engine_reconciliation.md)
- C. [Options extension scoping](options_extension.md)
- D. [Design decision index](decisions/README.md) (D1–D97) ·
  [PHILOSOPHY.md](../PHILOSOPHY.md) · [TUTORIAL.md](TUTORIAL.md)
