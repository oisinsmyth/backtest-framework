# D404 PRE-REGISTRATION — the cross-asset state: does a series from OUTSIDE the equity universe forecast anything, before any gate is designed?

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **Nothing here is a
result.** No cell is scored, no book is built, no null has been drawn, no holdout is touched.
The runner is deliberately not written.
**Date:** 2026-09-09 · **Area:** strategy research · **personal track**
**Holdout reads spent by this record: 0. Programme total: 1** (D371, 2026-09-07).

**Number.** `D404`, taken by the three-command procedure in `PICKUP.md` §"READ THIS BEFORE YOU
PICK A DECISION NUMBER", **not** by `ls docs/decisions/`:
`git log --all --oneline | grep -iE "\bD40[4-9]\b|\bD41[0-9]\b"` returns **empty**;
`grep -i RESERVE` shows the only reserved block is **D390–D399**
(`945cbb5`, `worktree-signal-hunt-part2`); `git branch -a` shows two live branches, master and
that worktree. **Master takes D400 and upward; D400–D403 are used, so this is D404.**

**Provenance.** This is lead **R1** of
[`docs/research/the-negative-space-scan.md`](../research/the-negative-space-scan.md) (`bbc2790`),
which scored it 18/21 and ranked it first. That record is a lead list and opens nothing; this is
the pre-registration it earns.

---

## 1. The question, and there are two

**Q_A — the gate question.** Does a market state built from **an asset class the equity book does
not trade** forecast the equity universe's forward drift, at a strength comparable to the four
states this programme already measured?

**Q_B — and it is worth more than Q_A.** Is that state **the unidentified factor of
[D389](D389-RESULT-the-floor-is-ONE-factor-and-none-of-the-four-candidates.md)**?

**This study is DESCRIPTIVE and it is Stage 0.** It reads forward returns — a premise check must —
but it reads them as **cohort drift, never as a strategy's P&L**, exactly as D361's and C1's Stage 0
did. **No gate is designed here, no threshold is chosen here, and §11 says what this deliberately
does not do.**

---

## 2. R13 LEDGER — this is the FIFTH market-level state, and the FIRST from outside the universe

The ledger transfers and is stated before the design, not after.

| # | state | built from | disposition |
|---|---|---|---|
| 1 | **G1** — 63-bar trailing compounded return | the floored equity market | **DECISIVE**, and it forecasts a **rebound, not a fall** (D361) |
| 2 | **G2** — index vs its 200-bar mean | the floored equity market | measured, **not decisive** (block corr −0.094 vs p95 0.157) |
| 3 | **BREADTH** — share of names above their own 50-bar mean | the equity cross-section | measured, **not decisive** (−0.145 vs p95 0.154) |
| 4 | **DISPERSION** — cross-sectional IQR of the 21-bar return | the equity cross-section | decisive at +0.205, then **WITHDRAWN by C1b** — *"dispersion is not direction, but it very much is volatility"*, and volatility alone was decisive and more strongly |

**All four are functions of the equity universe being traded.** C1's own overlap matrix says what
that costs: **G1, G2 and BREADTH are Spearman 0.56–0.73 correlated with each other** — C1's phrase
is *"one state in three sets of clothes"* — and only DISPERSION sits outside them at −0.10 to −0.17,
and DISPERSION is the one that was withdrawn.

> **A gate is informative only to the extent it knows something the book does not. Four gates,
> three of them the same gate, and all four know only what the book already sees.**

**C1b is the load-bearing precedent and this record inherits its test rather than rediscovering
it.** C1 compared dispersion against three *direction* measures and never against *volatility*, and
that hole cost the finding. **Q3 below is C1b's Q3, applied in advance to a new state.**

---

## 3. THE GAP IN THE REPO, MEASURED — and it is one array, not a project

**Every claim in this section is measured, and the probe is committed.**
`scripts/probe_negative_space_census.py` → `data/negative_space_census.json`, plus the grid
alignment measured for this record (§3b).

### 3a. The catalogue cannot express this, structurally

All **52 scores** across nine families are functions of **one name's own OHLCV window**. The single
exception is `beta_63`, and `ragged_anomaly_scores`' own docstring records that its market return is
built from **the panel's own equal-weighted cross-section**. **Not one score, and not one gate, reads
a series from outside the fixture.** A grep across 478 decision records, `FINDINGS.md`, `STACK.md`
and `scripts/` returns **four doc hits and five script hits for `TLT`/`HYG`, and every one is
universe membership** — D188's ETF cross-section, D239/D240's TSMOM arms, D263's COT pairing, and
fetcher symbol lists. **No study has ever conditioned an equity book on another asset class.**

### 3b. The join is free, and this is the fact that makes R1 actionable

`ragged_panel.load_ragged` builds its grid as `sorted({d for s in symbols for d, *_ in rows[s]})` —
the union of every name's dates. Reproducing both grids directly from the two fixtures:

```
equity grid : 4,187 bars   2010-01-04 -> 2026-08-26
etf    grid : 4,187 bars   2010-01-04 -> 2026-08-26
identical   : True
in equity not etf : 0        in etf not equity : 0
```

**The two grids are IDENTICAL, bar for bar, not merely coincident at the endpoints.** And every
series this record names is defined on **every one of the 4,187 bars**, with zero missing:
`TLT IEF SHY HYG JNK LQD XLU XLP XLY XLK` — all `bars=4,187`, all `missing from equity grid: 0`.

**That matters for a specific reason.** `c1_gate_stage0.state_pack` asserts the state is defined
**contiguously** from `d0`, because *"a hole would silently change the block grid and make the
correlation a different object than D361's"*. **A cross-asset state on these series has no holes**,
so it enters the existing machinery without a single new convention.

### 3c. What already exists and is reused unchanged

| | |
|---|---|
| `c1_gate_stage0.state_pack` | **owns the lag** — `level[t] = raw[t-1]`, in one place, so no consumer can forget it (D279's lesson) |
| `c1_gate_stage0.block_corr` | D361's premise statistic, independently implemented, with its own 999-draw shuffle p95 |
| `c1_gate_stage0.trailing_median_rule` | the causal threshold rule, unchanged, so on/off lines stay comparable |
| `run_d361_regime_gated_short.forward20` | the forward-20 hedged drift grid `F` |
| `run_d361_regime_gated_short.stage0_groups` | `bottom_10`, `top_10`, `elig_all` on the eligible mask |
| `d348_prep.prep` | the memoised panel prep |

> **THE WHOLE OF THE NEW CODE IS THE `raw` ARRAY.** C1 builds `raw` from the equity cross-section
> via `cross_state`. This builds it from two ETF closes. **Everything downstream — the lag, the
> contiguity assertion, the block premise, the shuffle null, the era frame — is already written,
> already regression-tested against D361's published numbers, and is not touched.**

---

## 4. THE STATES — declared before the run, and not searched

Three, each a log ratio of two series the fixture already holds, each reduced by
`trailing_median_rule` so the on/off line is causal and comparable to DISPERSION's:

```
CREDIT     log(HYG / IEF)              high yield against duration-matched governments
CURVE      log(IEF / SHY)              the belly against the front end
DEFENSIVE  log((XLU + XLP) / (XLY + XLK))   defensive against cyclical rotation
```

**`CREDIT` is the PRIMARY and it is named now.** The other two are secondary and reported beside it.
**All three are declared here so that none can be promoted after the fact** (D246 Constraint 3).

**A ratio, not a level, and the reason is FINDINGS §14.** A cross-sectional rank on a quantity
carrying units ranks those units. These are market-level states rather than cross-sectional ranks,
but the same discipline applies: **a log ratio of two prices is unit-free and drift-free in a way
neither leg is**, and `HYG` alone is a bond price with a sixteen-year trend in it.

**Why the ratios are formed against a duration match rather than against cash.** `HYG` minus a
government leg of similar duration isolates the *credit* component; `HYG` alone is credit **plus**
rates and would make `CREDIT` and `CURVE` the same variable. Stated here because a reader would
otherwise reasonably ask why the simpler construction was not used.

### 4a. Direction, declared in advance — and the declaration is unfavourable to the lead

**D361 established the contrarian sign on this fixture**: G1's block correlation with the loser
cohort's forward drift is **−0.231**, i.e. *a market that has fallen forecasts a rebound.*

> **Declared: `CREDIT` will correlate NEGATIVELY with forward drift, the same sign as G1** — a
> high `CREDIT` level (spreads already tight, risk-on already happened) forecasting *lower*
> forward drift.

**That declaration is deliberately the one that is bad news for the lead.** If `CREDIT` carries
G1's sign *and* sits inside G1's 0.56–0.73 correlation cluster, then it is **G1 in different
clothes** and the lead is worth much less than 18/21 suggested — which is precisely what §5's Q3 is
written to detect and what C1b's history says will happen if nobody looks. **Declaring the
uncomfortable direction first is the point of declaring it at all.**

`CURVE` and `DEFENSIVE` carry the same declared sign, and the prior on both is explicitly weaker.

---

## 5. THE MEASUREMENT — four questions, and only the third and fourth decide anything

**Q1 — DOES THE STATE PERSIST?**
Median and maximum episode run, episode count, and the acf of the level itself.
**This is the standing rule and it runs first: measure the conditioner's own persistence BEFORE
designing anything that conditions on it.** A state with a one-bar half-life cannot gate a 40-bar
hold, and the record has designed on an unmeasured conditioner before.

**Q2 — DOES IT PARTITION FORWARD RETURNS?**
`block_corr` of the lagged level against the forward-20 hedged drift, over non-overlapping 20-bar
blocks, against **three targets** — `elig_all`, `bottom_10`, `top_10` — **with the era split
reported beside it.** FINDINGS §6: measured effects here are frequently one era, and a state that
lives only in 2020 is not a state.

**Q3 — DOES IT SURVIVE THE VOLATILITY CONTROL? THIS IS THE PRIMARY AND IT IS C1b's TEST.**
The block premise recomputed with volatility **partialled out** of the state level — both the
closed-form partial correlation and a **residual-and-shuffle version carrying its own p95**, because
*a partial correlation with no null is a number without a bar* (C1b's sentence). The two volatility
states are C1b's own, unchanged so the comparison is to a measured thing:

```
VOL_XS    the cross-sectional MEDIAN of rvol21 over eligible names
VOL_MKT   the trailing 21-bar sd of the floored market's own return m_f
```

**And the orthogonality frame, which is Q3's other half.** Spearman of `CREDIT`/`CURVE`/`DEFENSIVE`
against `G1`, `G2`, `BREADTH`, `DISPERSION`, `VOL_XS`, `VOL_MKT`, plus the gate Jaccard — **the same
matrix C1 published**, extended by three rows. **Measure independence on day one, not at stage 5**
(PICKUP §0e, after D373's H7 found a "different" construction holding 70% of the same name-bars).

**Q4 — IS IT THE D389 FACTOR? See §6. It is nearly free and it is the reason this record exists.**

---

## 6. Q4 — the D389 factor, and why it costs almost nothing

**What D389 established**, quoted rather than glossed: two unrelated books here co-move at
**0.476**; it is **ONE factor** (PC1 reproduces the pairwise rho to three decimals, PC2 is 0.006);
and **none of four candidates explains it** — slot mechanics 0.029, equal-weighting 0.031,
eligibility floor 0.052, shared hedge likewise. **Unattributed: 85% in arm A′, 98.5% in arm B.**
`PICKUP.md` §0d ranks it the most promising open lead in the programme and says where to look:
**"the factor lives in WHICH DAYS GET TRADED, not in the market on them."**

> **Every one of D389's four candidates was internal to the book's own machinery. A cross-asset
> state is external to all four, and "which days get traded" is exactly what a market-level state
> indexes.** No driver D389 could reach was of this kind.

**And the series are already on disk.** `data/d376_series.npz` holds the book matrices on the
**same 4,187-bar grid** — `A_x (500, 4187)`, `B_x (250, 4187)`, `Bc_x (500, 4187)`, `obs_x (4187,)`.
**Nothing needs rebuilding.** The measurement is: extract PC1 of arm **B** — the arm that is 98.5%
unexplained and the one gate 1d′ is calibrated against — and correlate it against each state level
on the shared index.

**[REG] anchors, named now so the reproduction is not chosen afterwards.** From
`data/d389_correlation_decomposition.json`: `base.B.p50 = 0.47588598570894936`,
`arms.B.share = 0.4782311976474094`, `arms.B.pc2 = 0.013976611005808028`, `arms.B.bars = 3185`.
**The runner reproduces these from the committed `.npz` before it reads a single new number.**

**What a positive answer would and would not mean, stated before the answer exists.** A high
correlation between PC1(B) and `CREDIT` would **identify** the factor, not remove it — the books
would still co-move, and D376's gate 1d′ would still need its floor. **Identification is worth
having on its own terms** and it is what D389 asked a successor to find. **A null answer is worth
almost as much**, because it strikes the most plausible external candidate off a list that
currently has nothing on it at all.

---

## 7. THE CALIBRATION FRAME — what "decisive" means here, measured rather than guessed

**A threshold you have never calibrated is not a hurdle, it is a guess** (PICKUP §0e, after H4 was
unreachable by a factor of four). So the bar is read off the states that already ran, on the same
grid, the same horizon and the same group:

All four recomputed by C1's own block code against `bottom_10`, so the column is one object.
**Each row's p95 is that file's own shuffle seed** — D361's G1/G2 p95s are 0.1615 / 0.1567 under
their seed, and C1's recomputation of the same correlations gives 0.1608 / 0.1532 under its own.
**The correlations are identical to 0.0 across the two files; only the shuffle draw differs.**

| state | `d0` | block corr (bottom_10) | shuffle p95 | n_blocks | decisive |
|---|---:|---:|---:|---:|---|
| **G1** | 126 | **−0.2311** | 0.1608 | 159 | **yes** |
| G2 | 263 | −0.0937 | 0.1532 | 159 | no |
| BREADTH | 64 | −0.1453 | 0.1543 | 159 | no |
| DISPERSION | 64 | **+0.2047** | 0.1508 | 159 | yes, **then withdrawn by C1b** |

**SE is 0.0796 on 159 blocks, so the decisive line sits at |r| ≈ 0.15–0.16, and two of the four
existing states do not clear it.** That is the frame: **R1 is not being asked to beat noise, it is
being asked to beat G1** — and if it clears the shuffle but sits inside G1's correlation cluster,
Q3 says it has cleared nothing.

**Episode counts, for the breadth caveat the scan record flagged.** G1 runs **98 episodes**, median
run 3 bars, max 101, on-share 0.285; G2 runs **62 episodes**, median 2, max 160. **A market-level
gate on this fixture is judged by tens of episodes, not by 4,187 bars, and the runner reports
`n_eff` EPISODES beside every correlation.** Quoting a `t` built on the bar count is D280's error
shape — *"`n` is 2,173 BARS; the 1,573 names inside a bar are one cross-section, not 1,573 draws"* —
and it would overstate the precision here by an order of magnitude.

---

## 8. PREDICTIONS, in the runner's own quantities and computable from what the record already holds

Written this way deliberately: a prediction that cannot be checked against a number the runner
prints is not a prediction.

1. **Block arithmetic.** `block_corr` iterates `range(d0, T - H + 1, H)`. The ETF series are
   complete from bar 0, so `state_pack` gives **`d0 = 1`**, and with `T = 4187`, `H = 20` the
   total block count is `ceil(4167 / 20) = 209`. C1's `bottom_10` empties were 47 on the same
   grid and group, so **`n_blocks` lands in [154, 169] and `empty_blocks` in [40, 55].**
   *The model is verified on all four existing states, where `n_blocks + empty_blocks` equals
   `ceil((4168 − d0) / 20)` exactly: G1 `d0 = 126` → 203 = 159 + 44 · G2 `d0 = 263` → 196 =
   159 + 37 · BREADTH and DISPERSION `d0 = 64` → 206 = 159 + 47. ✓*
2. **The shuffle p95 lands in [0.145, 0.165]**, since it is a function of `n_blocks` and the four
   published values span 0.151–0.162 at `n = 159`.
3. **`CREDIT` correlates with `G1` at Spearman |ρ| > 0.4** — it joins the cluster. **This is the
   prediction against the lead**, per §4a.
4. **`CURVE` is the most orthogonal of the three** to the existing four states, because the front
   end is set by policy rather than by risk appetite. Declared as the weaker prior.
5. **Q1 will show `CREDIT` is MORE persistent than G1** — median run above 3 bars — because a
   credit ratio is a slower object than a 63-bar return. **If it is not, Q1 has found something
   surprising and the design question changes.**

**If prediction 3 holds and Q3 also fails, the honest reading is that the lead is largely spent**,
and the record should say so in those words rather than retreating to `CURVE`.

---

## 9. ASSERTIONS — all of them, and each proved able to fail

Patterns from `scripts/run_overnight_long.py` and `scripts/lag_audit.py`.

| tag | assertion |
|---|---|
| **[REG]** | this file's `block_corr` reproduces **D361's published G1 and G2** numbers — corr, block count, shuffle p95 — from `data/d361_stage0.json` at their own recorded seed, **to 0.0**, before any new state is read. Same object or no comparison. |
| **[REG2]** | the D389 anchors in §6 reproduce from `data/d376_series.npz` to `1e-12` before any state is correlated against PC1. |
| **[JOIN]** | the ETF grid and the panel grid are **identical as date lists**, asserted element-wise — **never joined by positional index.** A refetch that moves either fixture must raise here, not silently produce a state offset by a holiday. |
| **[L]** | the level at `t` is unchanged when every bar from `t` onward is deleted, **rebuilt by a second implementation that never calls the vectorised one** — C1's `[L]`, extended to the ETF series. |
| **[E]** | every state is reported with the count of bars on which each leg is finite; a bar missing either leg is undefined, never forward-filled. **A forward-filled state reads a stale price and calls it today's.** |
| **[U]** | the log ratio is finite everywhere it is defined, and both legs are strictly positive — a split or a bad print gives a negative price and `log` returns `nan` silently. |
| **[P]** | the JSON is persisted **before** it is rendered (D371's `KeyError` in a print loop lost a whole execution's evidence). |
| **[X]** | the self-test **RAISES** on (i) a level that reads bar `t`, (ii) a partial correlation that fails to remove a planted confound, and (iii) a grid join offset by one bar. **A self-test that cannot fail is worse than none — and the break must hit the SCALAR the assertion compares, not its name.** |

---

## 10. THE ABANDON CONDITION — and it does not close anything

**Stated in advance so it cannot be negotiated afterwards.** The premise fails if, **on the
primary `CREDIT` × `elig_all` cell**:

- Q2's block correlation is **inside its own shuffle p95**, **and**
- Q3's partial correlation, with `VOL_XS` and `VOL_MKT` removed, is inside its residual-shuffle p95.

**If both hold, no gate should be designed on this state and the record says so.**

**Under [R15](../RULES.md#r15) that is not a closure.** Only the principal closes a research
avenue. A failed premise here retires **this construction of a cross-asset state**, not the
category — the scan record's §1 audit stands either way, and `CURVE`, the volatility ETPs and the
dollar (both absent from the fixture, §11) would remain unmeasured.

---

## 11. WHAT THIS DELIBERATELY DOES NOT DO

1. **It does not design a gate.** No threshold is chosen, no book is gated, no cell is scored.
   C1's own words apply unchanged: *"if this record ever becomes a gate the threshold is a design
   decision that must be made in its own pre-registration."*
   **And the ENUMERATED ROTATION NULL belongs to that record, not to this one** — the scan entry
   noted that a market-level gate's time rotation is a finite group of `Td − 1` ≈ 4,000 offsets and
   is therefore exactly enumerable, with sampling SE of exactly zero (C2b's method contribution,
   after all four of D361's exact p95s came in **above** their published 200-draw values).
   **That applies to rotating a GATE against a book. Stage 0 rotates nothing** — its null is
   `block_corr`'s 999-draw permutation of block-level `x` against `y`, and a permutation of 209
   blocks is not an enumerable group. **Said here so the omission reads as scope, not oversight.**
2. **It does not touch a holdout.** Neither fixture is a holdout and no holdout path is opened.
3. **It does not reach implied volatility or the dollar.** `VXX`, `VIXY`, `UUP`, `UDN`, `MTUM` and
   `USMV` are **absent from the fixture** (measured, `data/negative_space_census.json`). Those are
   the two states a reader will most expect and **they are out of reach without a pull, which the
   principal's 2026-09-07 deferral of auxiliary data sources governs.** Said here so the omission
   is visible rather than discovered mid-study.
4. **It does not sweep.** Three states, three targets, one horizon, one threshold rule inherited
   unchanged from C1. **No parameter in this record is fitted.**
5. **It does not use the 15-minute panel.** D383 measured `n_eff` instruments at **2.17 of 57** at
   15 minutes against ~2.2 daily — *26× more sampling buys no breadth* — so there is nothing at
   that frequency this design would gain.

---

## 12. MULTIPLICITY LEDGER

**Declared before the run, per R13 and R14.**

| | count |
|---|---:|
| states | 3 (`CREDIT` primary, `CURVE`, `DEFENSIVE`) |
| targets | 3 (`elig_all` primary, `bottom_10`, `top_10`) |
| **block correlations in Q2** | **9** |
| Q3 partial correlations | 3 states × 2 volatility controls = **6** |
| Q4 correlations against PC1 | 3 states × 2 arms (A′, B) = **6** |
| **total statistics** | **21** |

**The primary is `CREDIT` × `elig_all`, named in §4 and §10 before anything ran.** Under the null
the largest of 21 independent `|t|`s has a median well above 2, so **no secondary cell in this
record can be read as a result** — D280's discipline, which reported 165 statistics and said in
terms which of them survived a best-of correction and which did not. **The primary is not a
best-of; the other twenty are descriptive.**

---

## 12a. AMENDMENT, 2026-09-09, BEFORE THE RUNNER EXISTS — one alleged defect is FALSE, one is CONFIRMED, and the measurement found a THIRD that neither party had

An external-evidence brief was commissioned on this lead
(`working/leads/R1-cross-asset-regime.md`) and alleged two mechanical defects in §4's
construction. **They are claims about OUR construction, not about the literature, so they were
measured here rather than accepted.** Probe: `scripts/probe_d404_construction.py` →
`data/d404_construction_probe.json`. **All three findings below are `[MEASURED HERE]`.**

### (i) The distribution-drift claim is FALSE as stated, and it runs the OTHER WAY

The brief alleged `log(HYG/IEF)` drifts down **2–5%/yr** on unadjusted closes, biasing the gate
toward risk-off. Measured over the fixture's own 16.6 years:

| state | drift %/yr | above its own trailing 252-bar median |
|---|---:|---:|
| `CREDIT` | **−0.92%** | **56.8%** |
| `CURVE` | **−0.00%** | **49.8%** |

**The drift is a fifth of the low end of the alleged range, and the resulting imbalance is
56.8% risk-ON — the opposite direction to the one predicted.** `CURVE` is as close to balanced
as a measured series gets. **The brief's figures came from current dividend-yield aggregators it
tagged `[UNVERIFIED]`, and they do not transfer to the realised 2010–2026 path** — IEF yielded
far less for most of that decade than it does now. *A quoted yield is not a measured drift.*

**But the distribution question is NOT closed, and the reason is a flaw in my own check.** The
probe compared the price ratio against "cumulated log-return differences" and got **identical**
numbers — because for price series those two objects are *algebraically the same thing*. **That
comparison isolated nothing.** The fixture carries an events file with dividend records for
every leg (`HYG` 233, `IEF` 289, `SHY` 289, `XLU` 108, `XLP` 107, `XLY` 107, `XLK` 84), and the
real test is to rebuild the states on total return and re-measure. **That remains open and the
runner must do it.**

### (ii) The price-sum defect is CONFIRMED, and it is severe

`(XLU+XLP)/(XLY+XLK)` sums **share prices**, so each leg's weight is whatever its price happens
to be:

```
XLU 33.5% / XLP 66.5%  of the defensive leg      XLY 39.1% / XLK 60.9%  of the cyclical leg
```

**A synthetic 2-for-1 split of `XLY` alone moves the level by 0.338 log units on average.** That
is not a state variable, it is a price-weighted index — **FINDINGS §14's problem, committed in a
pre-registration that cites §14 as its reason for using ratios.** §4 is amended: `DEFENSIVE`
becomes the cumulated **equal-weighted log-return difference**
`0.5(r_XLU + r_XLP) − 0.5(r_XLY + r_XLK)`, which is split-invariant by construction, and the
runner asserts invariance under a synthetic split of each leg.

### (iii) THE DEFECT NEITHER PARTY HAD, and it is the one that matters most

**Equal-weighting does not fix `DEFENSIVE`'s imbalance, and that is the finding.** The
price-sum version sits above its trailing median on **28.5%** of bars; the corrected
equal-weighted version sits above it on **28.7%**. The imbalance is not a construction artefact
at all — **it is a real 16-year trend** (−7.6%/yr price-sum, −7.9%/yr equal-weighted: cyclicals
beat defensives over this entire fixture).

> **A TRAILING-MEDIAN RULE APPLIED TO A TRENDING SERIES IS A TREND RULE, NOT A STATE
> CLASSIFIER.** On a series drifting at −7.9%/yr the "gate" spends 71% of its life on one side,
> and what it is mostly reading is *"tech has outperformed staples since 2010"* — a momentum
> signal wearing a regime label. **This is the programme's own §14 failure in the time domain
> rather than the cross-section**, and it applies to any state built as a ratio of two
> differently-trending assets.

**Consequence, and it is a genuine tightening of the design.** §4's threshold rule was inherited
from C1 unchanged *for comparability*, and that inheritance was wrong for this class of state.
**The runner must report, for every state, the drift per year and the above-median share, and
`[BAL]` must FAIL any state whose above-median share falls outside 40–60%** — a state that
cannot spend a comparable amount of time on each side is not a classifier. **On today's numbers
`DEFENSIVE` fails that assertion and `CREDIT` and `CURVE` pass it**, which is exactly the
information a pre-registration is supposed to surface before the runner exists rather than after.

### (iv) The horizon question, recorded but NOT yet acted on

The brief's headline is that the documented predictability of credit spreads and the curve lives
at **quarters to years**, not weeks, and that a 20-day gate sits an order of magnitude inside
that band. **That is a literature claim, not a measurement, and none of the cited papers has
been read here** — under `working/leads/README.md`'s rule an agent's summary of a paper is not a
reading of it. **It is therefore recorded, not adopted.**

**One addition from it IS adopted, because it costs nothing and converts a pass/fail into a
test that can agree or disagree with the outside world:** the runner reports the block
correlation at **h ∈ {5, 10, 20, 40, 60, 125, 252}**, not at h = 20 alone. **h = 20 remains the
declared primary** for comparability with G1/G2/BREADTH/DISPERSION, and the curve is
descriptive. **A new pre-declared reading, added to §8: if h = 20 is the PEAK of that curve,
that is an overfitting flag, not a confirmation** — nothing in the outside evidence predicts a
20-day peak, and a rise into 125 days would be the strongest corroboration this fixture can
offer.

---

## 13. What this record does not claim

- **Nothing has been run.** The runner does not exist. Every number above is quoted from a
  committed artefact and attributed, or is a measured fixture census with its probe named.
- **No candidate is proposed and no book changes.** `BOOK.md` remains S1 and S2, neither at
  capital; `BOOK_PROP.md` remains empty.
- **Clearing this premise does not license a gate**, and clearing a gate would not admit a
  strategy — R8 needs a separate pre-registered out-of-sample test on a fixture it has never seen.
- **A positive Q4 identifies the D389 factor; it does not remove it**, and it does not restate
  gate 1d′, whose floor D389 showed is not a scorer artefact.
