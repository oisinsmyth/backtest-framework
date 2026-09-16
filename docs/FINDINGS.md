# Findings

**What this programme has established that outlives any individual study.**

Unlike [decisions](decisions/README.md), which record one call each, and
[RULES.md](RULES.md), which binds future conduct, this file holds the **substantive
results** — the things we now know about markets, instruments and this book, with the
measurement that established each.

**Every claim here names the study that produced it.** A claim without one does not belong.

---

## 1. The arithmetic of a short position

**`gross = exposure x edge − short-leg convexity`**

Both terms have been measured, and together they explain every short failure in this
programme.

### 1a. `exposure x edge` is invariant to selectivity

**Tightening a threshold raises the conditional edge and shrinks the population it is
measured on, in exact opposition.** [D250](decisions/D250-the-overnight-gap-pre-screen.md)
measured it directly — as the cut moved from `z <= -1.5` to `z <= -3.0` the held-bar edge
tripled from −0.56% to −37.52% and the gross return **did not move**, pinned at ~0.4%/yr:

| cut | % of cells | held-bar edge | **gross** |
|---|---:|---:|---:|
| z ≤ −1.5 | 6.72% | +0.56% | −0.04% |
| z ≤ −2.0 | 3.51% | −11.53% | **+0.39%** |
| z ≤ −2.5 | 1.88% | −21.99% | **+0.40%** |
| z ≤ −3.0 | 1.07% | −37.52% | **+0.39%** |

**Selectivity cannot create gross return.** It redistributes the same return into fewer,
larger trades — which helps costs and nothing else.

**Corollary, and it is a rule for screening:** a screening target must be stated as the
**product**, never as the edge alone. D250 set a target of "−15%/yr held-bar edge"; the tail
cleared it at −37.52% and was still worth +0.29%/yr, because the cut that produced it holds
1.07% of cells.

**Independently confirmed three more times the same day**, on unrelated candidates: short VXX
(edge ~47 points over borrow, capped at **+2.35%/yr** by a 90% maintenance margin),
specialised-ETF underperformance (−3%/yr but possibly 0–5 qualifying names → **0.1–0.45%/yr**),
and the wedge (see §5).

### 1b. A short pays a variance tax that scales with sigma-squared

**A daily-rebalanced short earns `log(2 − e^r)`, whose expectation is approximately
`−mu − sigma^2`.** Found independently from two directions:

- [D251](decisions/D251-the-cross-sectional-dollar-neutral-pre-screen.md) measured the drag at
  **6.2 to 14.9 points/yr** on ETFs, and it is why **five cells cleared as a spread table and
  zero cleared as a book**. *A spread table is stated in a coordinate system where shorting is
  free of variance drag.*
- [D253](decisions/D253-the-book-short-sides-on-crypto.md) tested the formula against a
  measurement:

| | |
|---|---:|
| crypto universe vol 77.6% → `sigma^2` | 0.602 |
| geometric drift `mu` | −4.17% |
| **predicted** `−mu − sigma^2` | **−56.05%** |
| **measured** `SHORT_ALL` | **−58.90%** |

**Within 2.85 points.** The same convexity with the sign reversed is why a daily-rebalanced
equal-weight basket returned **+32.55%** while the median coin returned **−9.12%** — variance is
a tax on the short side and a rebalancing subsidy on the long side. **The two sides of a universe
are not mirror images.**

#### The approximation degrades where `sigma^2` is large — measured, 2026-09-01

[D264](decisions/D264-the-intraday-short-on-single-names.md) tested the formula a third time, on
eight single names at 15 minutes, split by volatility:

| stratum | `sigma^2` | predicted | **measured `SHORT_ALL`** | error |
|---|---:|---:|---:|---:|
| **LOW** — PG LMT PM MO | 0.033 | −11.75% | **−14.60%** | **−2.85 pts** |
| ALL | 0.073 | −12.82% | −27.08% | −14.25 pts |
| **HIGH** — CLF SM YELP RH | 0.209 | −21.60% | **−37.73%** | **−16.13 pts** |

**At low volatility it reproduces D253's crypto error exactly — −2.85 points, the same number. At
high volatility it understates the drag by 16 points.** `log(2 − e^r)` is being approximated to
second order, so higher-order terms bite as `|r|` grows, and **the formula is a floor on the drag
rather than an estimate of it.** Quote it as universal only at moderate volatility.

**And the practical form of the same point:** on D264's best cell the variance tax took **59% of
the linear `exposure × edge`** — +8.31%/yr gross became +3.43%/yr realisable — **before a single
basis point of trading cost was charged.** A short's gross edge is not what a conditional-return
table says it is.

### 1c. Consequences

- **A short is not survivable at full notional on a high-volatility universe.** D253's guard
  (written for D238) fired on **BTG-USD +215.1%, 2025-06-13**, an equity multiple of **−1.15**.
  Maximum survivable per-name notional: **0.46x**.
- **Gap-through is a base rate, not a tail story.** **62.9% of crypto names** produced at least
  one bar above +50%, against **0% of ETFs**.

---

## 2. The instrument decides more than the signal

**The hypothesis** (proposed by the principal, 2026-08-28): an ETF is a weighted average, so
diversification removes idiosyncratic variance by construction; what remains is the common
factor, and the common factor is exactly what carries the risk premium. **Diversification removes
the component where an edge could live and leaves the component you are paid to bear.**

### Confirmed for shorts

[D253](decisions/D253-the-book-short-sides-on-crypto.md): S1's short mirror has **real timing
skill on crypto** — 98.7th percentile of its matched-count rotation null — where the identical
rule has none on ETFs. The buy-the-dip premium reverses sign between the universes:

| forward 21-bar return of names that have fallen | ETFs | crypto |
|---|---:|---:|
| low idiosyncratic share | **+39.77%** | **−50.57%** |
| high idiosyncratic share | +5.33% | −61.43% |

### Falsified for breakouts

[D254](decisions/D254-the-wedge-breakout-on-crypto.md): down-breaks outperform up-breaks in
**both** universes — ETF spread −6.96 to −10.05, crypto −20.22 to −62.50. **Diversification
cancelling asset-specific continuation is not what killed the ETF wedge.**

### The refinement that matters

**The operative variable is between-universe, not within-universe.** Idiosyncratic share does
**not** predict shortability inside a universe — `corr = −0.195` (n.s.) on 46 equity ETFs,
`−0.006` on 62 crypto names. What matters is whether **a risk premium attaches to the thing that
fell**.

**And 1−R² does not measure idiosyncratic risk for an ETF.** GDX at 0.85 is gold-beta, not company
risk. **There is no such thing as a high-idiosyncratic ETF** — every ETF is *some* factor; the only
question is which.

### The two effects oppose each other

**Idiosyncratic variance is where the short edge lives, and it is also what makes a short bleed
at `sigma^2`.** Crypto has enough of the second to swamp the first by an order of magnitude. **A
single-name equity universe sits between the two extremes**, which is what makes it the deciding
test rather than an extension.

---

## 3. Beating a null is not having a strategy

Two results on opposite sides of one lesson, from the same day:

- [D253](decisions/D253-the-book-short-sides-on-crypto.md): **S1_short cleared hurdle H at the
  98.7th percentile on both legs and returned −10.12%/yr.**
- [D254](decisions/D254-the-wedge-breakout-on-crypto.md): **both long cells made money and
  neither beat its null** — the +32.55% pooled buy-and-hold was doing the work.

**Hurdle H is a SKILL test. It cannot see structural drag, and it cannot distinguish return from
exposure.** D254 therefore introduced **hurdle V**: a cell is not a success unless it also posts a
**positive net CAGR** after fees, financing and borrow. **H without V is a measurement, not a
result.**

---

## 4. Breadth is the recurring binding constraint, and headcount cannot fix it

**Effective independent instruments saturate at `1/rho` regardless of `n`:**

| universe | n | rho | effective |
|---|---:|---:|---:|
| the 57 ETFs | 57 | 0.47 | **2.2** |
| the wide ETF universe | 486 | 0.48 | **2.1** |
| US single names | ~3,000 | 0.25 | **~4** |
| single names, factor removed | ~3,000 | 0.02 | **~50** |

**Universe size buys almost nothing on its own — correlation is the ceiling.** Confirmed
empirically in [BOOK.md](BOOK.md): going from 57 to 486 ETFs *lowered* effective breadth.
D251 measured the factor-removal gain directly: the eigenvalue participation ratio rises from
**3.61 raw to 11.55 on market-neutral residuals**.

**Two consequences the programme had to absorb:**

- **Hurdle E has failed in every study of the last two sessions.** The wedge gives a minimum of
  **5** entries/symbol on 57 ETFs over 12.8 years and **3** on crypto. **Entries scale with span,
  not universe size.**
- **Instrument holdouts are much weaker evidence than their headcount suggests.** S1's 385-ticker
  ETF holdout contains roughly **two** independent tests. Headcount is not sample size.

---

## 5. Exit overlays have a measured ceiling on this book

[D255](decisions/D255-stops-and-targets-on-the-book.md) did not merely fail to clear a bar; it
**measured the maximum any exit rule of this form could achieve**:

> **The single best level out of 600, chosen with perfect hindsight, improves S1 by +0.017
> Sharpe** — because **97.2% of its trades never travel far enough to be cut.**

**Reachability is the reason**, and it is a property of the book rather than of the overlay:

| arm | trades | **median max gain** | median max loss | reach +20% |
|---|---:|---:|---:|---:|
| S1 | 2,374 | **+2.37%** | −1.55% | **2.8%** |
| S2 | 393 | +5.89% | −3.19% | 9.7% |

**The asymmetry is real and reproduces on two independent controls:** take-profits help, stops
hurt. A stop on a rule that buys dips cuts the signal — D236's mechanism, now measured from the
universe side at **+89.74%** forward after a −20% five-bar move.

**CORRECTION, from [D256](decisions/D256-the-book-on-single-names.md):** the ceiling above is real
but **the reason given for it was wrong.** D255 attributed it to reachability. On single names
reachability is **2–3x higher** (S1 reaches +20% on 9.0% of trades against 2.8%) and **all nine
take-profit cells still hurt**, monotonically in tightness, approaching neutral only by ceasing to
fire. **Reachability was never the binding constraint — a take-profit on these rules is simply a
bad exit.**

**One row is not dead:** **61.8% of all stop levels beat S2's base** (best +0.121), so a stop
generically helps the trend arm — but **no particular level is special**, so the effect is *having
a stop*, not *having a 10% stop*.

---

## 6. Measured effects are frequently one era

**Three instances in a single day**, which is why era-splitting is now reflexive:

- [D250](decisions/D250-the-overnight-gap-pre-screen.md): the gap tail's sign **inverts** without
  2020 — `z <= -3.0` goes from −37.52% to **+13.54%**.
- **The overnight/intraday decomposition itself.** [D247](decisions/D247-the-short-side-at-fifteen-minutes.md)
  reported +8.59% overnight against −0.36% intraday, and the programme quoted it as structural.
  **Split by era it does not hold:**

  | | intraday drift |
  |---|---:|
  | full sample | −0.33% |
  | excluding 2020 | **+1.44%** |
  | **2021 onward** | **+3.05%** |

  **A book deployed today faces a positive intraday headwind, not a negative one.** The gap is
  stable across boundary placements (6.8–8.0% from 10:00 onward), so this is not the microstructure
  artifact Lachance (2021) describes — it is era dependence.
- Rapach et al.'s aggregate short-interest timing, per the literature review: the entire result
  disappears without 2008.

### The same decomposition is ALSO cross-sectional — [D264](decisions/D264-the-intraday-short-on-single-names.md), 2026-09-01

**It is not one era *and* not one asset class. It is a property of VOLATILITY**, measured on eight
single names over the same 2018–2026 span D247 used:

| | overnight/yr | intraday/yr | swing |
|---|---:|---:|---:|
| **LOW vol** — PG LMT PM MO, 14–16% | +4.36% | **+5.56%** | **−1.21 pts** |
| **HIGH vol** — CLF SM YELP RH, 54–78% | +13.81% | **−8.97%** | **+22.78 pts** |
| *57 ETFs — D247* | *+8.59%* | *−0.36%* | *+8.95 pts* |

**In the low-volatility names the drift accrues INTRADAY and the sign reverses.** The ETF figure
is not an asset-class constant; it is an average across instruments whose volatility differs, and
the effect is concentrated at the high-volatility end.

**Two consequences.** First, **any construction justified by "the overnight carries the drift" must
name which instruments it means** — the claim is false for defensive mega-caps. Second, the queued
wide extended-hours study (`c25218d`), which asks where untraded-window drift accrues across 11
instruments, **should carry a volatility split**; [`PICKUP.md`](internal/PICKUP.md) already records SPY and QQQ disagreeing
(33% against 91%), and this says that disagreement has a measurable axis.

---

## 7. The objective is Sharpe, not return

From the prop-firm review (`research/shorts/05-prop-firm-reality.md`):

- **Netting $50,000/yr requires a Sharpe near 2.14**, not the 0.92 this book runs at. Modelled as
  ABM against a trailing barrier, 20 funded accounts at S=0.9 yield **~$24,200 after tax** — half
  the target — with the correlated book dying every ~3.85 years.
- **Every major futures prop firm auto-liquidates at the close.** No plan permits an overnight
  hold, which makes **both existing arms structurally unportable**.
- **Automation is banned at the funded stage** by Apex and Take Profit Trader; only Topstep and
  MyFundedFutures permit it.
- Own capital needs ~**$1.03m** unlevered, or ~**$350k** at 3x.

**Return = Sharpe x volatility x leverage, and leverage is available from both routes — but only
above a Sharpe that survives the drawdown constraint.** The research problem is therefore
**roughly doubling Sharpe**, which re-values a near-zero-correlation arm above a high-return one.

---

## 8. What is closed

**Do not revisit without a new mechanism, not merely a new parameter:**

| | closed by |
|---|---|
| directional shorts on liquid ETFs | D238, D240, D247, D248, D249 — structural, see §1 and §2 |
| the wedge breakout | D249, D254 — three distinct claims, two universes |
| stops and targets on this book | D235, D236, D240, D249, **D255** — ceiling measured |
| cross-sectional dollar-neutral on ETFs | D251 — nothing cleared stage 1 |
| structural-decay instruments (VXX, leveraged pairs, contango) | `research/shorts/02` — best case +2.35%/yr with instrument-termination risk |
| classic short anomalies for liquid names | `research/shorts/01` — the premium is absent, not merely expensive, in value-weighted liquid names |
| the Impulse MACD at intraday frequencies | D247, D248 — four constructions |
| the volume regime gate | D226 — the spike moved between asset classes; a fitted parameter |

## 9. What is live

**One test, and it decides two questions at once:** the single-name equity fixture
(`us_shorts_daily_raw.csv.gz`, 231 names, **32.5% dead**, ragged, split-adjusted, per-symbol
pre-live screen).

1. **The short hypothesis** — enough idiosyncratic variance to carry an edge, without crypto's
   `sigma^2` swamping it and its 62.9% gap-through rate.
2. **Take-profit reachability** — the exact quantity that closed D255, and the one that should
   differ most between a basket and a single name.

**RESOLVED, 2026-08-28, by [D256](decisions/D256-the-book-on-single-names.md) — and the answer was
neither of the two expected.** The fixture built out at **1,580 names, 35.7% dead**. Both parts
closed: no short cell cleared H (best 90.2nd against crypto's 98.7th), and every take-profit cell
hurt despite three times the reachability.

> **An equal-weighted book over 1,580 single names IS a diversified basket.** Idiosyncratic
> variance exists at the **name** level and averages away at the **book** level — the book holds
> **76.5% of live names at once**, against ~72% for the ETF wedge. **We rebuilt the very
> diversification the hypothesis identified as the problem.**

**So the operative variable is not the instrument's listing status — it is how many you hold at
once.** Crypto's 34-name book showed skill at the 98.7th percentile; a 1,580-name book shows none.

**And that exposes a tension with no universe-level solution:** *the same averaging that buys
statistical confidence destroys the idiosyncratic edge being measured.* Concentration preserves the
edge and collapses the sample; breadth preserves the sample and averages out the edge. **Hurdle E
and the short hypothesis pull in opposite directions.**

**What is live now** is therefore a question of **construction**, not universe: a concentrated
book (colliding with hurdle E), or a factor-neutral one — which D251 closed on ETFs at breadth 2.2
but which this fixture's 1,580 names could genuinely support.

### The concentrated branch was taken, and it answered — [D264](decisions/D264-the-intraday-short-on-single-names.md), 2026-09-01

**Eight names instead of 1,580, flat at every session close.** The concentration worked, in the sense
the hypothesis required, and the construction failed anyway on arithmetic.

**Concentration did what §4 said it could not.** Effective independent instruments came in at
**3.02 of 8** — against **2.23** on the 57 ETFs and 1.80 of 35 on crypto. **Eight single names carry
more independent breadth than fifty-seven ETFs, so §4's saturation near 2.2 is a property of that
universe, not a ceiling on equities.** Hurdle E cleared in all sixteen cells.

**And the idiosyncratic edge survived the concentration**, which is exactly what D256's diluted
1,580-name book could not show. The intraday-flat S1 short on the high-volatility stratum holds bars
returning **−28.87%/yr** — the most negative held-bar return this programme has measured, against
D247's −4.27% — and clears hurdle H on **both** legs at the **96.9th / 99.7th** percentile.

**It still loses 15.84% a year, and the identity says why:**

| | %/yr, continuously compounded |
|---|---:|
| `exposure × edge` | **+8.31%** |
| − the `sigma^2` variance tax (§1b) | −4.87% |
| **= realisable gross** | **+3.43%** |
| − trading cost, 324 turns/yr | **−20.68%** |
| = net | **−17.24%** |

**So the tension in §9 is real but it was not the binding one.** Concentration did preserve the edge
*and* the sample. **What binds is turnover cost at 6.0× the realisable gross** — and it binds
without needing any assumption, because **commission alone is 1.92 bp/side against a 1.06 bp
breakeven.** The cell loses at a zero spread.

**The cost wall does move with volatility, and not far enough.** Breakeven rose **8.2×** from D247's
ETF figure while charged cost rose **4.0×**, halving the shortfall from **12.3× to 6.1×**.

**R12's escape hatch does not apply to this family.** A construction excluded on ETF cost arithmetic
is supposed to be re-costed on futures before being discarded. **This one cannot be** — its edge is
single-name idiosyncratic variance, and no retail futures contract exists on a single name. The ~20×
cost reduction that rescues other intraday constructions is structurally out of reach here.

**Bounded closure.** D264 closes *that construction on those eight survivor names*. It does not close
the intraday short: `TIME_SERIES_INTRADAY` serves no delisted ticker, so **41.6% of the 2013–17
cohort is unreachable at this frequency**, and the bias runs *against* the short.

**What is live after D264:**

1. **The factor-neutral branch of §9 is still untouched.**
2. **Cost per basis point is a function of PRICE, not just liquidity** — IBKR charges per share, and
   commission ranged **0.20 bp (RH) to 4.15 bp (CLF)** inside one stratum. A high-priced,
   high-volatility name gets the edge at a fraction of the commission. Invisible on price-clustered
   ETFs. Recorded post-hoc, deliberately not tested inside D264, and eligible only as its own
   pre-registration under D246 Constraint 3.
3. **Overnight drift is a property of volatility, not of equities** — see §6.

### And the DAILY concentrated branch answered too — [D279](decisions/D279-the-concentrated-short-on-dead-inclusive-names.md), corrected 2026-09-02

**Same construction question, same fixture as D256, one change: hold only the top N.** D264 above
took the concentrated branch at *fifteen minutes* and lost to turnover. D279 took it on *daily bars*,
where S1's ~15-day hold puts the move-to-cost ratio roughly twelve times higher.

**Zero of fourteen cells survive.** Every cell has a negative net CAGR, so hurdle V fails everywhere;
the best-of-14 floor is **−0.178** against a best cell of **−0.337**, so F fails too; and **every
breakeven borrow rate is negative** — the book does not survive borrow at *zero*.

**The number that decides it is GROSS.** Re-scored at zero fees, zero borrow and zero `rf`,
`S1_short|top25` posts **−0.432 Sharpe and −0.26% CAGR.** Every intraday record from D264 to D278
closed on `mean move per trade ≥ 2c`; **this one never reaches the cost question. It loses before a
basis point is charged, at every N, on both arms.** *On this fixture the binding constraint is the
drift, not the toll.*

**D279 first reported two survivors at +2.250 and +1.865 Sharpe and they were look-ahead.** That
result, the breakeven-borrow figures, the P&L attribution and the claim that a strength ranking had
beaten its own matched control are **all withdrawn.** The corrected record carries the defect as its
primary finding.

**Four lessons, and the first is new:**

1. **A LAGGED POSITION BUILT FROM AN UNLAGGED RANKING IS STILL LOOK-AHEAD, AND THE BASE BEING
   CORRECTLY LAGGED IS WHAT HIDES IT.** `hold_book` shifts the qualifying mask by one bar and always
   did, so D256 is untouched and *which names qualified* was honest. But `top_n` chose *which N of
   the qualifiers to hold* with `score[:, t]` — `hist_L` computed from the close of the very bar the
   position was about to be paid for. `corr(hist_L[t], return[t]) = +0.0737`; lagged, **−0.0103**.
   **The score is 98.05% the same number one bar earlier and the entire result lived in the other
   1.95%**: `top25` went **+2.250 → −0.638** and `top50` **+1.865 → −0.659**.

   **Every look-ahead guard this programme owns points at `hold_book`, and `hold_book` was right.**
   The defect entered one layer above it, in a function that *filters* an already-lagged book — a
   place nothing was watching, because filtering a lagged book feels like it cannot introduce a lag
   error. **[R9](RULES.md#r9)'s third appearance**, after D224's stop and D248's quintile anatomy,
   and the second on `hist_L` specifically.

2. **A CONTROL MUST DIFFER FROM THE TREATMENT IN EXACTLY ONE WAY, AND "matched count" IS NOT
   "matched turnover".** D279's pre-registered `random-N` re-drew every bar while the ranked book
   held its picks — the control churned **5.6–6.0×** harder on S1 and **12.2–15.3×** on S2, and paid
   that multiple of the fees. Against a **turnover-matched, persistent** control at zero cost, S1's
   ranking is worth **+0.20** Sharpe and S2's is worth **less than nothing.** **Check what else moved
   when you moved the one thing.**

   **And a control scored on a single draw is not a control.** `rnd-N` is one RNG sequence, not a
   distribution: the same cell scored **−1.528** in the runner and **−1.633** in the decomposition.
   `rotation_nulls` takes 300 draws; hurdle C took one, and its margin moves by up to 0.16 Sharpe on
   the seed alone.

3. **A hurdle can be computed, printed, and never applied to the thing it names.** E′ was specified
   "over the held book" and measured over the whole 1,573-name panel — **5.44 for every cell**, so a
   ten-name book and a 1,200-name book scored identically on the hurdle whose job was to separate
   them. Third appearance of this pattern after D230 and D270; see [R6](RULES.md#r6). **The runner
   still has it**; the corrected summary carries an `Eprime_panel_defect` flag on every cell and the
   honest values come from a separate script.

4. **An effective-instrument count degenerates on a rotating book.** `top25` scores **28.00 on 28
   names** — the correlation matrix is the identity, because almost no *pair* shares the 250-bar
   overlap minimum. The metric silently becomes "how many names were held ≥250 bars", and on that
   reading `top10` scores **1.00 on one name.** **Any independence measure with an overlap floor
   needs that floor checked against the book's holding pattern before its number is trusted.**

**What is NOT claimed.** Hurdle H is **failed for this study** under [R7](RULES.md#r7)'s corollary —
`S1_short|all` scores the **100th percentile on both legs with −0.757 Sharpe and −2.45% CAGR**, and
**seven of fourteen cells clear it while all fourteen lose money.** A null that the worst book in the
grid tops is broken, not passed, and it must not be reused unmodified.

### THE EDGE IS ENTIRELY OVERNIGHT — [D280](decisions/D280-the-forecast-precheck.md), 2026-09-02

**This is the largest result of the D264–D280 sequence and it explains the whole programme.**
Cross-sectional IC of the R9-lagged `hist_L` against each **part** of the next bar — Spearman,
within each bar, out of sample from 2018-01-01. **A short ranks ascending, so negative is
tradeable:**

| universe | total | **gap** | intraday |
|---|---:|---:|---:|
| **all live names** | −0.00524 (t −1.79) | **−0.01531 (t −4.71)** | +0.00168 (t +0.65) |
| **qualifying set** | +0.00462 (t +1.43) | **−0.01255 (t −3.45)** | **+0.00868 (t +2.85)** |

> **There is a real, correctly-signed OVERNIGHT edge and a wrong-signed INTRADAY move that cancels
> it. Close-to-close — the only quantity D256 and D279 ever measured — is the SUM OF THE TWO, which
> is why it read as noise.**

**Three consequences, and the first two are closures:**

- **No intraday stop, target, partial exit or overlay of any kind can reach an edge that does not
  accrue while the market is open**, and the position cannot be taken at the open to shed overnight
  risk either — that discards the edge and keeps the leg fighting it. Arrived at independently of
  [R11](RULES.md#r11)'s record that **86.6% of the book's return is overnight timing** (D247), on a
  different fixture at a different frequency.
- **It is not an ex-dividend artefact.** `gap` is built from raw OHLC and a short *owes* the
  dividend, so the confound was measured directly: dividend-adjusted the IC is **−0.01498 (t −4.59)**
  and excluding ex-dates gives **−0.01494** — a 2–3% move, because only **0.834%** of bars go ex next
  session. *On those 216 bars alone the IC is **−0.05197**, 3.4× the average, so the mechanism is
  real and localised and a book built on this must charge dividends explicitly.*
- **AN IC IS NOT MONEY, and the gap between them is an order of magnitude of turnover.** An
  overnight book trades a full round trip **every night** — roughly **252 a year against ~17** for
  D279's ~15-day holds — so [D265](decisions/D265-the-entry-time-reconciliation.md)'s bar
  (`mean move per trade ≥ 2c`, 10 bp at 5 bp/side) must be cleared **15× more often**. A rough
  prior, **not computed from these artefacts**, puts the per-night edge near 4 bp against that 10 bp
  toll. **[D282](decisions/D282-the-overnight-only-short.md) is pre-registered to measure it; no result is referenced or predicted here.**

### And WHY the ranking was worth so little — the same record

**D256 and D279 both filter on `hist_L < 0 & md_L >= 0` and then rank the survivors by `hist_L`
again. The filter and the ranking are the same variable, so the signal is spent by the time the
ranking runs, and what remains inside the filtered set reverses.**

Measured cross-sectionally — Spearman IC **within each bar** against the **next** bar's return, out
of sample from 2018-01-01:

| `hist_L`, lagged | mean IC | t | bars |
|---|---:|---:|---:|
| over **all live names** | **−0.00524** | −1.79 | 2,173 |
| over the **qualifying set** | **+0.00462** | +1.43 | 2,147 |

**Correctly signed for a short over the universe — a short ranks ascending, so negative is tradeable
— and the WRONG SIGN inside the set the ranking actually operates on.** That is the whole of why
D279's ranking bought +0.203 gross Sharpe on a book sitting at −0.432.

**Three more things D280 established, each of which outlives it:**

- **The DEMA + velocity/acceleration/jerk extrapolation is dead.** It loses to **naive persistence**
  in all 48 level comparisons, all nine delta comparisons and all nine range comparisons.
  DEMA-alone is worst everywhere and the derivatives claw back *toward* persistence without passing
  it — **they are correcting the smoother's own lag, not forecasting.** Longer `n` is monotonically
  worse; jerk hurts in 8 of 12 cells, as its `C(2k,k) = 20` noise multiplier predicts.
- **16 OHLC derivative terms carry 13.50–15.76 EFFECTIVE inputs**, not the sub-3 collapse predicted
  from D268's 2.87-of-9. **The intrabar axis is real and independent — and it carries no predictive
  power.** *Independence is a statement about covariance and not about signal: sixteen independent
  useless inputs are sixteen independent sources of noise, with no redundancy left to average away.*
  **This is the mirror image of D268's lesson and belongs beside it.**
- **`open(t+1) := close(t)` is not free.** Median |gap| **0.5263%**, mean **0.9393%**, and
  **|gap|/|body| = 0.515.** Anchoring the open does not remove a term from the forecast; it smuggles
  in an unforecast one about half the size of the term being forecast. *Range is separately
  predictable at correlation **+0.87** — and persistence-of-range still beats the DEMA stack on MAE
  in all nine cells, so it is a sizing input at best and never a signal.*

**And the honesty that has to travel with it:** D280 reports **165 statistics across five parts, 161
of them distinct.** Under the null the largest of 161 independent `|t|`s has a **median near 2.86**,
so the best *extrapolation* result (**|t| = 2.29**) is a best-of and is **not evidence** — and the
only un-searched baseline, `hist_L` alone over all names at **t = −1.79**, is not significant at
conventional levels either. **The overnight result is the exception and it is said explicitly rather
than assumed: `|t|` of 4.71, 5.07 and 5.97 clear a best-of-161 correction comfortably**, and part
4's gap leg was declared in the script before it ran rather than surfaced by a sweep.

**The `t`-statistic is small on 2.2M name-bars because the IC is computed within each bar and
averaged, so `n` is 2,173 BARS** — the 1,573 names inside a bar are one cross-section, not 1,573
draws.

### D281 to D284 resolved all four, and the answer is one sentence in four parts

**[D281](decisions/D281-the-unfiltered-ranking.md), [D282](decisions/D282-the-overnight-only-short.md),
[D283](decisions/D283-the-descending-ranking.md) and [D284](decisions/D284-the-overnight-long.md)
all returned SURVIVORS NONE.** Together they take the overnight finding apart completely.

**1. The overnight effect is real, and it is a TAIL TAX rather than a signal.** D283 split the
overnight move into a direction-blind part and a directional part, on the unfiltered universe, in
short bp:

```
        asc      dsc      c = (asc+dsc)/2      d = (asc-dsc)/2
N=10  -19.42   -9.93          -14.68               +4.75
N=25  -14.46   -5.14           -9.80               +4.66
N=50  -10.17   -2.98           -6.58               +3.60
```

**`hist_L` is SIGNED acceleration, so BOTH of its tails are the volatile names, and volatile names
rise overnight whichever way they moved.** Shorting *either* tail loses. **Symmetry fails by SIGN,
not by degree** — the +14.64 bp a mirror would have implied does not exist.

**2. The directional component is real, small, and confirmed twice independently.** D283's
decomposition puts it at **+4.66 bp** at N = 25; D284 measured **+4.18 bp** against a
volatility-matched control. **It is the first evidence in D264–D284 that the SIGN of `hist_L` adds
information over a control drawn from the same tail** — and it is under half of D265's 10 bp round
trip.

**3. A per-trade move can clear its cost bar and still be untradeable.** D284's `lng10` is the
**first construction in this programme to exceed `2c`** — **+24.10 bp, 2.41×** — with **+0.27% CAGR
at +0.960 net Sharpe** and a −0.82% drawdown. It fails anyway, on a hurdle written in advance to
catch it: **breakeven half-spread 11.36 bp/side against a 15 bp floor**, because the book holds a
**$13.19 median stock with a $1.92 tenth percentile and 25.7% of positions under five dollars.**
**On a $1.92 name one cent of spread is 26 bp per side.** The effect is bid-ask bounce in cheap,
just-fallen names.

**4. A CONTROL MUST SHARE THE TREATMENT'S NUISANCE, not just its count.** This is the session's
most transferable lesson and it cost three studies to learn. D279's `random-N` differed in count
*and turnover*. D284's first control set — random, persistent-random, and long-everything — differed
in *volatility* too, and all three would have been beaten by the tail tax alone. **Adding
`tail-N` — random selection from within the same extreme-|score| tail — is what separated a 4 bp
signal from a 14 bp nuisance.** Without it, D284 would have reported "selection beats random".

**On the ledger.** D281 10 cells, D282 19, D283 26, D284 13 — with D256's 21 and D279's 20 that is
**109 carried**, on top of D280's 165 statistics. **No best-of floor computed from a study's own
cells can price a DIRECTION chosen after 165 statistics**, and every one of these records says so
rather than implying the F hurdle handles it.

**What is live after D284:**

1. **The factor-neutral branch of §9 — still untouched** after D256, D264, D279, D280, D281, D282,
   D283 and D284. **It is the only remaining idea that is a different MECHANISM rather than a
   variation on one already measured to fail**, and the arithmetic points at it: every construction
   tested has been net directional in a market with positive drift, paying `−μ − σ²` before costs.
   D279 loses **−0.432 gross**; D282's `base|all` loses **−21.92% CAGR gross**. **These are not cost
   failures.** A factor-neutral book removes the `−μ` term by construction — the short leg only has
   to underperform the long leg. D251 closed it on ETFs at breadth 2.2, which was the *universe*
   failing; this fixture carries 1,573 names and 10.06 effective independent instruments over a held
   book.
2. **The 4 bp directional component is a MEASUREMENT, not a candidate.** It is under half its own
   cost bar and would need a different instrument, not a different parameter.
3. **Nothing reaches [R8](RULES.md#r8).** No study has produced a candidate, so there is nothing to
   take out of sample, and **D246's reserved wide-universe cohort remains unspent.** `cohort3`
   (8 names, 448,861 rows, gates passed, all 28 steps REAL) is also unspent — and is 15-minute
   intraday, so it is the wrong instrument for anything daily.

---

## 10. The book has no bench, so most of its turnover is unpriced

**The refill pool IS the slot count, by construction:**

```python
ctx[side] = dict(rank=rank, sel=rank < N_SLOTS, ...)      # run_d295_exits.py:348
cand = np.flatnonzero(sel[:, t] & np.isfinite(r1[:, t]))  # run_d295_exits.py:211
```

`sel` is *defined* as `rank < N_SLOTS`. **The gate holds 25 names and only the top
19 are ever eligible for refill** — the 6 bench names cannot be drawn on. Every
book since [D293](decisions/D293-the-confluence-book-as-a-candidate.md) has run
this way.

**So an exit on a still-selected name re-enters that name on the same bar.**
[D298](decisions/D298-RESULT-combining-adds-little-and-the-price-axis-is-void.md)
measured it directly: `reversion + price exit` differs from `reversion` alone on
**0.00% of held bars** — not "under 5%", zero.

### Opportunity cost therefore splits in two, and only one half is zero

| | opportunity cost | what the exit buys |
|---|---|---|
| exit on a **still-selected** name | **exactly zero** | nothing — pure churn, cost with no benefit |
| exit on a name that has **drifted out** of the top 19 | positive | the slot refills with a still-selected name |

**The second case is the entire mechanism by which the profit target earns**, and
it has never been measured directly. D295 asked whether the book was better with
the rule on; nothing has asked what each individual swap paid.

**And small per-decision differences compound into different books.**
[D303](decisions/D303-RESULT-the-reference-is-adopted-and-the-band-is-not.md):
two rules agreeing on **73%** of the decisions they both face end up sharing only
**56%** of their positions, because one divergent exit frees a slot that refills
differently and the paths separate from there.

### THE TWO LENSES — report both, never on the same statistic

A path is part of the strategy, so a result measured through only one of these is
half a result.

**Path-invariant — the unconstrained ledger.** No slot cap: every gated name not
already held opens a position and runs to the exit rule or the cap. This is the
full set of decisions the rule faces, free of contention, and it answers *is this
a good rule*. **It is not a tradeable book** — unbounded capital, uncontrolled
exposure — so it is scored at the **trade** level and must never be quoted in
bp/bar beside a real book.

**Path-variant — the constrained book.** The slot-limited book, walking a subset
of the invariant ledger's trades. Scored in bp/bar and Sharpe as now. It answers
*what did we actually earn*.

**The difference between them is the opportunity cost**, and it decomposes into
three quantities that should be reported separately:

1. **Contention drag** — mean trade P&L over all candidates minus over the held
   subset. Positive means the path systematically holds the worse names.
2. **The turned-away ledger** — at each bar the book is full, what the best
   eligible unheld name earned over the next `k` bars.
3. **The replacement premium** — for each exit, the incoming name's return minus
   what the outgoing name *would* have earned had it stayed. **This prices each
   exit decision directly** and is the sharpest of the three.

### What this invalidates in a study design

**A book-width study that lets the pool track the slot count measures nothing
about the bench.** If `sel = rank < N_SLOTS` is inherited while `N` is varied,
the bench stays empty at every depth and concentration is welded to bench depth.

**CORRECTION, from [D304](../scripts/d304_two_lenses.py), 2026-09-03: widening
the pool ALONE is inert.** A 19-slot book drawing from the 25-name gate is
**bit-identical** to one drawing from the top 19 — same 30,242 trades, same
+24.2 bp/trade, same +12.00 bp/bar. The reason is that refill only runs when a
slot is free, and a drifted-out name **holds its slot**, so the bench is never
consulted. **The bench is unreachable unless something evicts the drifted-out
holders** — a reversion exit, or a rank-based eviction. Pool width and eviction
are one change, not two, and the earlier claim here that the pool was "a one-line
change" was wrong.


## 11. Forecast the book's risk from the UNIVERSE, never from the book

**From [D312](decisions/D312-RESULT-the-estimator-not-the-premise.md),
2026-09-04.**

D312 targeted the book's volatility using **the book's own trailing 63-bar sd** —
one series, 63 numbers, off a two-name spread. Correlation with the **next** 63
bars' realised book vol:

```
N_eff = 2     -0.016      the width that earns: nothing at all
N_eff = 19    +0.347
```

**That reads as "the book's risk cannot be timed". It is not.** The same forward
quantity, forecast instead from the **cross-sectional dispersion of the whole
live universe** — ~1,019 names a bar against the gate's 50:

| predictor | N=2 | N=5 | N=10 | N=19 | own lag-63 ρ |
|---|--:|--:|--:|--:|--:|
| the book's own trailing sd | **−0.016** | +0.056 | +0.185 | +0.347 | **−0.016** |
| **dispersion, whole universe** | **+0.352** | +0.374 | +0.405 | +0.410 | **+0.616** |
| **dispersion, names OUTSIDE the gate** | **+0.355** | +0.371 | +0.403 | +0.411 | +0.598 |
| dispersion, the 25-name gate only | +0.242 | +0.300 | +0.334 | +0.342 | +0.588 |
| mean \|r\|, whole universe | +0.136 | +0.202 | +0.291 | +0.381 | +0.477 |
| trailing sd of the market reference | +0.104 | +0.165 | +0.250 | +0.349 | +0.312 |

**At the width that earns, the forecast goes from −0.016 to +0.352 by changing
nothing but where the estimate is read from.** The book's forward volatility is
forecastable. A two-name realised series is simply too starved to see it, and the
starvation is worst exactly where the book is most concentrated — the column
where `own` collapses and the universe predictor does not.

### The names you never hold carry the regime better than the ones you do

**Dispersion over the ~969 names OUTSIDE the gate (+0.355) beats the whole
universe (+0.352) and beats the 50 gate names outright (+0.242).** The gate is
chosen on the signal, so its dispersion is contaminated by the selection; the
unheld remainder is a clean read on the regime. **Nothing requires a risk
estimator to be built from tradeable names, and here it is actively better not
to.**

**Generalise past volatility:** any regime quantity this programme conditions on
should be estimated from the widest set that carries it, not from the held book.
The held book is the smallest, most selected, most noise-dominated sample
available.

### The trap that produced the wrong reading

**Estimating a quantity well in-sample is not forecasting it.** D311 measured
that vol is estimated about fifteen times better than the mean — `t = 6.37`
against `t = 0.42` — and D312 took that as licence to condition on it. The
in-sample precision was real; the **out-of-sample** content of that particular
estimator was zero. The predictor's own persistence is the check that separates
them: `own` has lag-63 ρ = **−0.016**, universe dispersion **+0.616**. **A
conditioner whose own level does not persist cannot forecast anything, and that
costs one line to check before a study is designed.**

### Two further traps, both priced in D312

**Vol targeting against a FULL-SAMPLE-sd target is structurally a leverage rule.**
A full-sample sd exceeds the average of rolling sds whenever vol varies over time,
so `target / v_trail` averages **above 1** before any forecasting happens.
Measured: ratios 1.15–1.27, realised mean exposure **1.34–1.53**. **A third of
such an arm is leverage, not risk control**, and leverage on a book that does not
cover its costs scales cost linearly against an unchanged gross-per-unit-exposure
— at `N_eff` = 2 it bought +2.25 bp of gross for +10.78 bp of cost. **Report mean
realised exposure beside any vol-targeted result** or the arm cannot be
attributed.

**Breadth is a priced risk lever, not a free one.** Widening cuts volatility and
gross together, roughly one for one — D312's dynamic arm bought an 11% vol cut
for 14% of gross, the same trade D300 and D310 priced statically. **Dynamic
breadth pays the static breadth price on every bar it widens.** Any risk rule
that works by widening must beat that price, not merely produce less volatility.

## 12. The width optimum is a corner, and that is why every variable-N study closed

**From [D314](decisions/D314-the-algebra-of-width.md), 2026-09-04.** Descriptive
fits to already-published cells, not a study.

Three curves, fitted to all sixteen widths of the `none` family:

```
vol(N)^2 = 2,396 + 1,201,745/N     R^2 = 0.9994
gross(N) = 29.47 - 6.50 ln N       R^2 = 0.9774
cost(N)  = 23.51 - 4.12 ln N       R^2 = 0.9522
```

**The implied average pairwise correlation is rho = 0.0020** -- statistically
zero, and negative when fitted on N <= 10 alone. Single-name spread vol is
~1,097 bp and the systematic floor `sigma*sqrt(rho)` is **49 bp against 237 bp at
the widest width ever tested**. This is a *spread* book, so it nets out even the
6.1% of variance D297 attributed to the market.

**So `vol(N) = sigma/sqrt(N)` almost exactly, and Sharpe collapses to one term:**

```
Sharpe(N) = net(N)/vol(N) = sqrt(N) * net(N) / sigma
```

**And `net(N) = 5.96 - 2.38 ln N`: the edge dilutes 1.58x faster than the cost
falls.** That single ratio is why net is monotone down in width everywhere.

### The optimum is closed-form and it is a corner

```
d/dN [ sqrt(N) * net(N) ] = 0   =>   ln N* = -n0/n1 - 2   =>   N* = 1.66
```

**below the grid floor of 2, and robust at 1.54-1.70 across every subset.**

> **CORRECTION, from [D315 Stage A](decisions/D315a-RESULT-the-corner-is-real-the-formula-is-not.md),
> 2026-09-04: `N* = 1.66` IS WITHDRAWN and the closed form does not locate this
> book's optimum.** The seven widths below the floor were run. **The log-linear
> net curve does not extend below N = 2** -- gross turns down at `N_eff` 1.15 and
> net at 1.45 -- so 1.66 was an invalid extrapolation, and refitting on [1,25]
> makes the gross fit worse (R^2 0.9774 -> 0.9143) for an equally meaningless
> 4.75. `ln N* = -n0/n1 - 2` is still the right first-order condition **for a
> log-linear net curve**; this book's is not log-linear across the full range.
>
> **The corner itself survives and is now MEASURED rather than extrapolated:**
> net Sharpe peaks at `N_eff` = 2.00 on a surface sampled from 1.00 to 25.00, the
> best cell below it beats N=2 by 0.0%, and no width below 2 is distinguishable
> from 2 on net (largest paired t = **0.12**, win rate 47.8%). **The
> diversification law was verified at the boundary** -- at `N_eff` = 1 measured
> vol is 1,089 bp against an implied sigma of 1,095, refitted rho = 0.0088.
>
> **The lesson to keep is the one below, plus this: a fitted form is evidence
> only inside its fitted range.** The optimum sat outside it, which is precisely
> when a closed form must be checked rather than quoted.

**A rule that varies N can only move AWAY from a corner, and moving away from a
corner can only hurt.** That is one explanation for five closed studies -- D299's
ladder, D308's discrete width, D311's continuous lambda, D312's vol target and
D313's universe-conditioned vol target. They were not five failures of five
mechanisms; they were five ways of leaving a corner. It retro-explains details
each reported without connecting: D312's arm pinned at the tightest level for
80.6% of bars, D311's oracle gain reproduced 100-124% by noise, D313's arm
raising gross at the wide end and still losing.

**D315 Stage A is not a sixth** -- it varied nothing, and instead measured the
static surface below the corner to check that the corner is where the algebra put
it. It is the confirmation, not another casualty.

### What width should key on, if anything

Writing `gross = sigma*ghat(N)` while cost does not scale with sigma:

```
Sharpe(N) = sqrt(N) * ( ghat(N) - cost(N)/sigma )
```

**sigma cancels except through cost/sigma.** The optimal width moves with the
**cost-to-opportunity ratio**, never with the volatility level itself. **A vol
target varies N with sigma(t) directly, which is the wrong argument** -- the
algebra predicts D312 and D313 fail before either is run. Doubling the
opportunity ratio moves the best width from 2 to 8, so the sensitivity is real.

The derived rule has **no free parameters**: `ln N*(t) = -n0(t)/n1(t) - 2`, so
the whole question reduces to **how often -n0(t)/n1(t) exceeds ln 2 + 2 =
2.693.** It currently sits at 2.509.

### The general lesson

**Fit the surface before searching it.** Five studies searched a surface whose
shape was recoverable in an afternoon from cells already published. The check
costs three regressions on numbers already in `data/`, and it says both whether
an interior optimum exists and what argument the optimum actually takes. Related:
[[stage-0-premise-check]] -- a premise needs measuring before a design; this is
the same discipline applied to the objective's shape.

## 13. Reach a tilt through a well-measured variable, not through the noisy one

**From [D321](decisions/D321-RESULT-the-hump-is-real-and-the-optimum-moved.md),
2026-09-04.**

The book's cost problem is its held spread -- 26.31 bp against the universe's
13.20 (D302). The obvious fix is to filter on spread. **It destroys the book.**

D321 built a SPREAD-MATCHED control at every one of nineteen thresholds: a direct
spread filter calibrated to reach the SAME held half-spread as a dollar-volume
filter. Net Sharpe, against a control of +0.334:

```
                          dv        direct spread filter, same held spread
20th percentile        +0.327                 -0.186
25th                   +0.433                 -0.075
28th                   +0.507                 -0.075
30th                   +0.519                 +0.021
```

**Dollar volume wins at all nineteen, by +0.060 to +0.582.** Identical tilt,
opposite outcome.

**The mechanism is estimation noise.** The per-name Corwin-Schultz half-spread is
noisy -- D302 measured its clamp as a left truncation and its per-name values as
unstable -- so filtering on it discards good names that merely MEASURED wide.
Dollar volume is cleanly measured and correlates with spread, so it buys the same
tilt without the noise.

**Generalise it:** when a nuisance variable is worth conditioning on but is badly
measured, look for a well-measured variable that correlates with it. The tilt you
want is not always best reached through the quantity you want to change.

**This is [FINDINGS section 11](#11-forecast-the-books-risk-from-the-universe-never-from-the-book)
from the other side** -- there, a starved estimator made a rule fail; here, a
clean proxy makes the same rule succeed. Both say the same thing: **how well an
input is measured decides more than what the input is.**

### And the caution that arrived with it

**D319 is the counter-example and it must travel with this.** Replacing the
overlay's noisy own-book volatility denominator with D313's better-forecasting
universe predictor made that rule WORSE at every width. **Forecasting a quantity
well and using it well are different things.** The rule here works because dollar
volume is a better-measured PROXY for the same tilt; D319's failed because a
better FORECAST was substituted into a rule that needed a SCALE.

### Multiplicity: a sweep is one hypothesis, not N

**D321 nearly discarded its own result on a BH bar computed over nineteen tests
that do not exist.** The nineteen threshold books correlate at a median of
**0.892**, the first eigenvalue explains **90%** of the variance, and the
effective independent count is **3.0 (Li-Ji) to 4.7 (Cheverud-Nyholt)**. The bar
for the smallest p moves from 0.00526 to 0.020-0.033, and the cell clears.

**The precedent was already here:** D297 applied BH to its EIGHT pre-registered
cells and reported its 25-point fine sweep separately as a count against chance.
**Correct a sweep for its effective width, not its nominal one -- and say which
you used.**

## 14. A cross-sectional ranking on a quantity that carries units ranks those units

**From [D328](decisions/D328-RESULT-the-lenses-are-inverted-and-two-signals-rank-price.md),
2026-09-04.**

`macd_hist` is `ema(12) - ema(26)` minus its signal line, computed on **raw
closes** (`research/macd.py:185`) and returned unchanged. It is denominated in
**dollars**. A $3,000 stock's histogram is ~100x a $30 stock's for the same
*percentage* move, so **ranking it across names ranks price**, and most
strongly exactly where a concentrated book looks -- the extremes.

Median price by rank bucket, over the whole live cross-section:

```
rank        L0     L1   L2-3   MID   S2-3     S1     S0
macd_hist 2706    798    438    22    477   1002   3020
```

**Both tails are the expensive names and the middle is the cheap ones.** The
demeaned compounded forward edge follows: **-557 bp at L0 and -650 at S0, t =
-12.58 and -4.61 at ranks 0 and 1** -- one number, measured twice, in a book that
longs one end and shorts the other. **Long-minus-short leaves +18 bp.**

**The test is dimensional, and it is free:** before ranking a score across names,
ask what units it carries. A price-denominated score, a dollar-volume-denominated
score and a variance-denominated score all rank their denominator at the extremes.
`hist_L` passes it -- built entirely on **log** high/low/close
(`run_activation_threshold.py:69`), it is scale-free.

**Applied to all 51 of D290's candidates**
([D328 AUDIT](decisions/D328-AUDIT-units-of-the-51-candidate-scores.md)):
**three carry dollars by accident** -- `macd_line`, `macd_hist`, `impulse_nodz`,
all from `research/macd.py` on raw closes -- and two by design, `amihud_21`
(1/$) and `price_log`. `impulse_nodz` and `hist_L` are the *same instrument* in
dollar and log units, screened side by side in D290 without the difference being
stated. The other 46 are dimensionless, though several rank volatility or
liquidity deliberately, which is a cost statement rather than a defect.

### Passing it is not enough: `hist_L` is dimensionless and still tilts

Same measurement on the incumbent's own primary:

```
rank          L0    L1   L8-15   MID   S8-15    S1    S0
price ($)     10    10      17    41      17     9     8
half (bp)   46.7  39.4    28.4  11.3    28.1  38.5  40.9
```

Scale-free, and its extremes are still **$8-10** names at **4x its own middle's
spread** and 3.3x the **14.2 bp** universe median -- a **volatility** tilt,
because percentage moves are largest in the cheapest names. **Dimensionlessness
buys you the absence of one artefact, not the absence of tilt.** The three
signals that hold near the universe in both price and spread -- $19-27, 9.6-16.4
bp -- are the three whose books make money.

**Measure the price and the spread of what each rank bucket HOLDS**, not only
what it returns. Section 3 of the D328 record is the worked case, and it is
[section 13](#13-reach-a-tilt-through-a-well-measured-variable-not-through-the-noisy-one)
arriving from a third direction: **what an input is made of decides more than
what it is called.**

### The test is INDEPENDENCE of price and rank, and correlation is not it

The natural way to state the standard is "rank should not be correlated with
price." **Measured, that statistic points backwards.** Correlation between bucket
index and median price, against the book it produces:

```
              corr(rank, price)   max |log p/p_MID|   net/trade
hist_L                  -0.074                1.61       -1.97
macd_hist               +0.079                4.93       -6.36
skew_63                 +0.323                0.58      +45.49
rsi                     +0.784                0.66      +37.33
retrace_leg             +0.812                0.40      +47.10
price_log               +1.000                5.12    (control)
```

**rho(correlation, net per trade) = +0.800. rho(max log deviation, net per trade)
= -1.000.** The correlation test **passes both losing books and fails both
winning ones.** *(The deviation column is against the profile's own middle,
which the subsection below says never to use -- it is shown only to make the
contrast with correlation, and on n=5 it is a separation of two from three,
not a ranking. The mechanism-derived statistic is the common-mode half-spread
further down.)*

**Because the fatal shape is SYMMETRIC, and a correlation cannot see it.**
`macd_hist` runs $2,706 / $22 / $3,020 and `hist_L` runs $10 / $41 / $8 -- a U
and an inverted U, whose halves cancel to corr ~ 0 by construction.
`retrace_leg` runs $25 / $37 / $43, a mild monotone ramp, and corr = +0.81.

### And the two shapes do OPPOSITE things, which is the mechanism

**Return cancels between the legs. Cost adds across them.**

A **monotone** price relation is a directional factor bet -- long the cheap end,
short the expensive end. On this fixture cheap outperforms, so it **pays**.
`retrace_leg` and `rsi` carry it and are two of the three winners. Price it and
keep or drop it deliberately.

A **symmetric** price relation pays **nothing** and costs **double**. Both legs
carry the same price penalty, so long-minus-short differences it away exactly:

```
macd_hist  long leg  (rank 0)   -557  =  signal  +43  +  price penalty -600
           short leg (rank 0')  -650  =  signal  -50  +  price penalty -600
           book spread = -557 - (-650) = +93 = +43 - (-50)   <- the -600 CANCELS
           averaged over ranks 0 and 1 the spread is +18
```

The exposure was carried on both legs and collected on neither. **The spread it
must pay does not cancel, it sums**: 2 x 32.7 + 2 x 40.2 = **146 bp** of round
trip against **+18 bp** of spread. `hist_L` is the same shape: 2 x 46.7 +
2 x 40.9 = **175 bp** against a book realising **+94** gross per name.

**A symmetric tilt is the worst available structure -- all of the cost, none of
the return.** `macd_hist` at its extremes is, once compounded, **nothing at all**
carrying 146 bp of cost. Whatever information it holds is in the middle of its
ranking (t = +9.6 there), where a composite's 25-name gate compresses the price
dispersion that its full-cross-section extremes sort on.

### Two P&L conventions, and the difference between them is a finding

A book that sets `ret[t] = mean(one-bar returns of the held names)` is
**equal-weight, rebalanced daily**, and over a hold it earns the **sum** of the
one-bar simple returns. Buy-and-hold with constant shares earns the
**compound**. **Every book runner from D295 to D326 uses the sum**, per bar and
per trade (`run_d306_width_exits.py:184` and its siblings), so the summed
trade `cum` is exactly right for those books. D327's rank profile matched them.
D328's compounded re-run is the buy-and-hold view. **Neither is "the right
quantity"; a comparison must use one convention on both sides**, and D328's
first correction did not (D328 section 9 against section 11).

**With convention and scale both matched** -- per-leg summed edge against
D326's per-name gross and net, k=20 -- **rho = +0.300 with gross and -0.800
with net.** The anti-correlation with net is real and it is *cost*: the signals
with the largest depth-free edge hold the most expensive names. Not resolution,
not a paradox.

**The difference between the conventions is the REBALANCING PREMIUM**, summed
minus compounded per leg at k=20, and on `hist_L`'s $8-10 names it is the size
of the whole effect:

```
                long leg   short leg          held price
hist_L             +78         -85            $8-10
rsi                +10         -30            $19-37
skew_63            +20          -2            $21-33
retrace_leg         +0          -3            $25-38
```

A long topped up after every fall and trimmed after every rise harvests
volatility; a short rebalanced the same way pays it. **163 bp over 20 bars
between the two legs of one signal, from position sizing alone.** So
**`hist_L`'s short leg loses under the book's convention (D327 section 2
stands), and the reason is that it is short the rebalancing premium on bouncy
names** -- a sizing artefact, not a signal failure. D283's "symmetry fails BY
SIGN" has its mechanism: a rebalanced long and a rebalanced short on the same
volatile names are not symmetric. The fix is constant shares on the short leg,
or shorts in names that do not bounce -- not dropping the leg.

**And the rebalancing is uncosted in every one of those runners.** They charge
entry and exit and earn the daily-rebalanced sum; the daily trades that realise
it are free. On `hist_L`'s names that is of order 30 bp per name over a hold
against a `two_c` of 96 -- second-order, not nothing, and it belongs beside
[section 10](#10-the-book-has-no-bench-so-most-of-its-turnover-is-unpriced).

**What was withdrawn and stays withdrawn:** the "unrealised ratio" and the
price-deviation hypothesis on it (a mixed-convention, mixed-scale comparison;
the residual it was chasing is the rebalancing premium above, now measured
directly); and the proposed D290 test of it. **What was withdrawn and is
reinstated:** D327 section 2.

**CLAUDE.md's right-quantity assertion exists for exactly this** and no runner
in the D304-D327 chain had one. D328's asserts the two grids differ and reports
both; the requirement is to say which convention is scored and why, and to
compare like with like.

### What the per-bar edge across horizons can and cannot say

Edge per bar at rank 0, compounded, across k = 10, 20, 40:

```
              k=10    k=20    k=40
macd_hist    -23.7   -27.9   -24.0   <- CONSTANT: a standing tilt, not a forecast
hist_L       +20.1   +10.5    +2.0      decaying: real, and reversing by k=40
retrace_leg   +9.9    +5.6    -2.2      decaying
rsi          +13.1    +2.9    +3.2      decaying
skew_63       +5.1    -2.4    -4.8      decaying
price_log     +7.4    +5.4    +2.1      NOT flat at rank 0 -- sub-$1 bounce
```

A constant per-bar edge at a fixed rank means the same names sit there day after
day drifting at a constant rate. **It separates `macd_hist` from the four
signals.** It is **not** a general instrument: the known-bad control's rank-0
names are sub-$1 and dominated by bounce, and its tilt shows at ranks 2-3
(+473 bp at k=20), not rank 0.

### What the depth-free lens has established, and what it has not

**Established:** which constructions rank price at the depth the book trades,
what those names cost, and why a symmetric tilt cannot pay. All of that is
measured on price and spread, and none of it moved when the return quantity was
corrected.

**Established, convention-matched:** the extreme-rank *return* edge predicts
the book's **cost**, not its net -- rho = +0.300 with gross and **-0.800 with
net** on five signals. The lens that says what the #1 name returns says which
signals hold expensive names; the things that separate the books are the tilt
structure, the cost, and the rebalancing premium, and only the last is a return
quantity. **D329 -- an ADDITIVE composite predicted from single-signal profiles
-- does not run on this basis.** What the per-leg profile does motivate is a
**leg-wise** composite -- one signal owning the long leg, another the short --
which the rebalancing mechanism makes a construction with a reason rather than
a search; see D328 section 11.6.

### The statistic for price-independence, derived from the mechanism

The book trades the two ends, so decompose their prices against the **live
universe median** ($30.7) -- never the profile's own middle, which for
`macd_hist` is its cheap tail. The **common mode** is the symmetric tilt, cost
without return; the **differential** is the factor bet. Measured directly on the
cost channel:

```
common-mode half-spread at ranks 0-1, both ends, x the 14.2 bp universe median
   hist_L 2.91   macd_hist 2.22   |   retrace_leg 1.17   skew_63 0.83   rsi 0.82
```

**A threshold near 2x separates the two losing books from the three winners.**
On n=5 that is a separation, not a ranking; ordering within either group is
noise. Neither a rank-price correlation (blind to a U) nor a deviation from
neighbouring buckets (blind to a *smooth* U, which `macd_hist`'s is) can see it.

## 15. A signal can own ONE leg, and the two legs of a spread book need not come from the same signal

**From [D329](decisions/D329-RESULT-the-short-leg-is-specific-and-the-long-leg-is-not.md),
2026-09-04.**

Every composite before D329 re-ranked one gate symmetrically. D329 handed the
long leg to `hist_L` and the short leg to `skew_63`. **The simulator processes
the two sides independently, so the leg-wise book is bit-identically the union
of its parents' legs in both lenses** -- per-leg additivity is an assertion,
not a finding, and everything that is a sum over trades composes exactly. What
does not compose is the book's path, and the partner enumeration.

At the operating point, k=20, on both lenses:

```
                     invariant net/trade    variant net Sharpe    round trip
hist_L symmetric              -0.89              -0.082              189.9
skew_63 symmetric            +44.83              +0.421               32.3
hist_L long / skew_63 short  +63.26              +0.434              120.0
the reverse pairing          -29.63              -0.062              102.3
```

**It beats both parents on both lenses at k=20 and k=40, and loses to
`skew_63` at k=10.** Every pre-registered "every k" form failed on that one
cell, and the record says so rather than re-cutting the claim.

### The short leg is SPECIFIC; the long leg is not

`hist_L`-long was paired with each of 44 costable partners short: **`skew_63`
is first of 44 on both lenses, above the control's p95 on both** (+63.26
against p50 +5.47 / p95 +54.82; Sharpe +0.434 against +0.099 / +0.362). Then
each of 45 costable partners long was paired with `skew_63`-short: **`hist_L`
is fifth per trade and fourteenth as a book.** Its long leg has the highest
gross per trade of any leg measured here, +201.7, and pays 52.3 bp a name for
it in $10.8 stocks. Thirteen cheaper long legs make a better book on top of
`skew_63`'s short.

**The construction is real; the long-leg choice is open**, and having seen all
45, any choice from that table is post-hoc. It needs its own pre-registration
from the profile side.

### The rebalancing premium per TRADE is a third of the rank-0 snapshot's

D328 section 11 put it at +78 / -85 bp on `hist_L`'s legs from a fixed-window
rank-0 profile; per trade it is **+23.5 / -45.9**. The profile counts a
persistent name once per bar it sits at rank 0, the ledger once per entry, so
**the premium concentrates in the persistent names.** Every leg has the
predicted sign. `hist_L`'s short leg nets **-98.4 per trade**, the worst leg in
the study; `skew_63`'s short leg is the cheapest at 7.7 bp and still pays
-23.5 -- cheap is not un-bouncy.

### A leg the cost model cannot price is not a free leg

Three enumeration cells -- `cs_spread`'s long leg, `on_share`'s and
`dist_52w_high`'s short legs -- select names whose held median Corwin-Schultz
half-spread is exactly **zero**, and D322's breakeven divides by it. That is
D302's clamp arriving as a blind spot. They are recorded as degenerate and
excluded, with the count beside every rank. Until the spread estimator's zero
clamp is fixed, any partner whose leg lands there is unscoreable.

## 16. The fixture contains pinned takeover targets, and a range-based spread estimator prices them as free

**From [D329 section 10](decisions/D329-RESULT-the-short-leg-is-specific-and-the-long-leg-is-not.md),
2026-09-05.** Diagnostic, not pre-registered.

`skew_63` -- sample skewness of the last 63 daily log returns -- is on 63
observations a **single-jump detector**: the name it ranks first from the short
end has a +41% day in its window and is otherwise quieter than the universe.
**29% of its short leg's trades are in a name that leaves the tape within 60
bars**, against 1% for the universe -- and **96% of those end within +/-5% of
the entry price with a median daily range of 0.28%**, zero below -30%. Those
are cash takeovers: a gap on announcement, two months pinned at the offer,
delisting at the deal price.

**Three things follow, and the second is the one that reaches back:**

1. **A short earns nothing on a pinned name** -- -5.6 bp per trade gross on
   the 297 -- and in practice cannot be put on: announced deal targets are the
   most crowded short in the market, borrow is scarce, and the residual risk is
   a deal break, which gaps *up* against the short.
2. **Corwin-Schultz estimates the spread from the daily range, and a pinned
   stock has none.** 6.2 bp on the dying names against 9.0 on the survivors.
   **This is D326's unexplained 4.5x cost coverage, D327/D328's "cheapest names
   in the study," and section 15's three zero-spread cells** -- one cause. A
   range-based estimator reads the least tradeable names on the tape as the
   cheapest.
3. **`max_ret_21` is the same detector by construction** and inherits all of
   it. Any short leg built on a biggest-day score does.

**The edge that survives is real and it is a two-sided lottery.** The 727
survivor trades earn +47.3 bp gross -- a genuine post-jump reversal -- but on
the whole leg the top 1% of trades is 159% of the P&L and the bottom 1% is
-203%; the mean (+32) is a quarter of the median (+126). The symmetric trim at
+46.8 is the honest central estimate (rule 2) and it is positive, but the book
lives in its tails.

**What a pre-registration must now carry for any jump-detecting short:** a
declared exclusion -- no name whose window holds a single day above +X%, or an
event-driven deal filter, which this fixture cannot supply (its event file has
dividends and splits only) -- **and a borrow-cost term**, which no runner here
has. Both sit beside [section 10](#10-the-book-has-no-bench-so-most-of-its-turnover-is-unpriced)'s
unpriced turnover as costs the model does not charge.

### Where the pinned names are, mapped across all 46 signals (D330 A)

**Short legs: median 1.5% pinned. `skew_63` is 21%**, the next signal 12%,
and `hist_L` 1.2%. The artefact on the short side is one signal's.

**Long legs: every volatility score is 24-35% pinned** -- `atr_norm` 35%,
`park_vol_21` 34%, `rvol21` 31%, `ivol_21` 31%, `max_ret_21` 29%,
`range_frac` 29% -- **and their surviving names carry a held half-spread of
exactly 0.0.** The lowest-volatility name on the tape is a stock pinned at a
deal price, so the "quiet" end of any vol ranking selects takeover targets
almost by definition. Those legs net -45 to -60 per trade. **Axis E's long
side was never a book, and every D290 reading of it is a reading of deals.**

**Collapses -- the short edge a dead-inclusive fixture exists to include --
are 0-4% of trades, pay +1,300 to +3,500 each, and sit in the high-vol short
legs.** `skew_63` has none.

### The tape cannot separate a deal from a reversal (D330 B)

A causal filter -- a +20% day between 5 and 63 bars ago and a median 5-bar
range under 0.75%, acting on the score so the removed name is replaced --
**catches 71% of the pinned trades and removes 39% of the survivors.** "A jump,
then quiet" is the signature of a pinned deal and of a post-jump reversal
candidate that has calmed, and on price and range alone they are the same
object. The filtered `skew_63` short leg nets **-8.0** per trade at an honest
11.1 bp; the unfiltered one +16.6 at a fictitious 7.7.

**So the leg-wise book's number is a bound**: net per trade **+51.05 to
+63.26**, Sharpe **+0.224 to +0.434** -- and it beats both parents at either
end, which is what says leg ownership was not the artefact. **`skew_63`'s short
leg is unresolved, not retired**: the filter's bluntness confounds the
separability test, and only a deal-event source can settle it. Until one
exists, no short leg built on a jump detector can be costed honestly on this
fixture.

### The event source settled it (D331): `skew_63` is retired as a short

SEC EDGAR was pulled for all 1,573 names (1,465 resolved). **Target-specific
deal forms -- DEFM14A, PREM14A, SC 14D9, SC TO-T, SC TO-C -- find 84% of the
pinned trades in resolved names, with a median lead of 28 bars before entry**,
and exclude only 2.4% of the universe. (An 8-K Item 1.01 with merger language
is NOT a deal filter: it excludes a quarter of all live name-bars, because
every acquirer's bolt-on and every credit facility files one.)

**And a 60-bar survival window does not identify a non-deal.** A quarter of
the "survivors" above carry a target-specific form within 63 bars of entry --
pinned targets whose deal had not closed yet. The "+47.3 gross survivor edge"
was partly deals.

With the deals removed by target forms, `skew_63`'s short leg nets **-24 to
-30 per trade at the old cost basis and -61 to -65 at the published one**
(second and first EDGAR passes); the cheap half-spread doubles, and the top
tail -- deal breaks, a short leg's lottery tickets -- leaves with the pinned
names. **Its +16.6 net, its 7.7 bp
half-spread, its first-of-44 in D329 and its 4.53x coverage in D326 were the
takeover targets, entirely. Retired as a short signal.** It remains the best
takeover-target detector in the 51, which is a different instrument.

**The leg-wise construction stands with its short leg vacant.** Under the deal
filter and the published convention the `hist_L`/`skew_63` pairing is +20 per
trade and **-10.8 bp/bar** -- a long leg carrying a losing short. D329's
enumeration is re-run under those before any partner is named.

**Two rules from this:** a name's death date is not a deal label -- use the
filings; and **a jump-detecting short on a dead-inclusive fixture must be run
with the target-form exclusion from the first study, not after.**

## 17. The spread estimator has a published convention, and the programme was not using it

**From [D332](decisions/D332-RESULT-under-the-published-convention-the-incumbent-is-negative.md),
2026-09-05.**

The single two-day Corwin-Schultz estimate is **clamped to exactly zero on
43.2% of all live name-bars**, uniformly across price and uncorrelated bar to
bar. That is the authors' own convention -- a negative estimate is set to
zero -- applied to an estimate that is negative nearly half the time on every
kind of stock. **The zeros are noise, not a property of any name.** Every
runner since D318 has charged the *median at entry* of that coin flip, so a
leg whose entries land above 50% zeros is charged nothing, and a leg near 50%
is charged by which side it fell.

**Corwin and Schultz never use the single estimate. They average the clamped
daily estimates over a month.** This codebase already computes that as the
axis-E score `cs_spread`. Its universe median is **31.7 bp per side against
14.2** for the per-bar median -- and across the 92 legs D329 and D330
measured, the published convention charges **2.03x** the programme's at the
median (p10 1.40x, p90 3.31x). D285 reported the mean (33.8 held); later
runners used the per-bar median; no record explains the switch.

Repriced with one array swapped and every ledger bit-identical:

```
                                   PB (used since D318)   PUB (published)
incumbent N=2/target, k=5              +14.57 bp/bar         -5.16
incumbent N=19                         -15.02                -37.09
retrace_leg k=20                       +20.91                +16.06
skew_63 k=20                           +12.60                 +4.97
leg-wise hist_L/skew_63, per trade     +63.26                +35.99
```

**The incumbent's headline was a cost-convention artefact.** Every relative
finding survives -- concentration (+32 bp N2-N19, basis-immune as Axis B
said), the leg-wise book beating its parents, the D323 order -- and every level
falls 8 to 20 bp/bar. `retrace_leg` at k=20 is the only cell above +10 that
stays above +10.

**Which convention is TRUE is not decided**, and cannot be from OHLC alone.
The default is the published one, because it is what the estimator's authors
specify and the other was adopted without a record. The test that decides it
is quoted BID_ASK bars from IBKR on a stratified sample of live names, against
PB, PUB and Abdi-Ranaldo, by lowest median absolute log error, declared in
advance. **Until then every net number in this programme is a PB / PUB pair.**

**Three generalisations:**

1. **An estimator's convention is part of the cost model and must be
   recorded.** A programme that had written down "per-bar median at entry"
   would have had to say why, and the 43% would have come out then.
2. **A clamp at zero on a noisy estimate turns a median into a coin flip.**
   Check the clamp rate before summarising with a median; if it is anywhere
   near half, the median is measuring the clamp.
3. **The published convention does not fix the pinned-name problem** (section
   16). A deal stock's spread really is tiny; the estimator is right about
   what it measures and silent about borrow.

## 18. The fixture carried thirty fabricated return days, and a concentration report is not finished until the top trade is named

**From [D333](decisions/D333-RESULT-thirty-fabricated-days-and-half-the-incumbent.md),
2026-09-05.**

`load_ragged` applied every event-file dividend as `log1p(amount / close)`
with no bound. The events file records corporate actions -- spin-off
consideration, merger consideration, 2-for-1 splits, returns of value on
stitched series -- as cash dividends with the price left at its
post-transaction level. **Thirty of them, 0.08% of 35,713 dividends, became
return days of +9% to +356%**: PNK 2016-04-29 closed 10.94 to 11.04 and was
paid +356%; TMUS 2013-05-01 rose 39.5% on the tape and was paid 49% more.

**The rule (pre-registered, two round parameters):** a dividend of at least
10% of the close is applied only if the price fell at least half of what the
distribution implies (`-r/(1+r)`); otherwise it is dropped and logged. It drops
the thirty, keeps every real distribution (HLSS -96% on a 24.8x payout, PENN,
BAX), and names one borderline case (IDT 2013-08-01, 48% of the implied move).

**What thirty days were worth, same trades, thirty bars corrected:**

```
                                  before      after
incumbent N=2/target, PB         +14.57      +7.15   bp/bar   -- half its book
incumbent, PUB                    -5.16     -12.68
concentration N2 - N19           +29.59     +22.93            -- a quarter of the premium
hist_L's long leg, per trade      +97.0      +63.9
skew_63 / dist_lvn / rev_21 / rev_5   -5 bp/bar each
retrace_leg k=20, PB / PUB       +20.91     +18.78  /  +16.06 -> +13.76
```

**`retrace_leg` remains the best symmetric book under either convention and
the only one above +10 under the published one.** The incumbent's headline
since D318 was half fabricated; concentration's premium was a quarter
fabricated and still wins by 23.

**The rule this leaves, and it is about reporting, not data.** D322 -- the
four-group report -- said "six names of 718 make half the P&L" and "top-1% of
trades = 96.3% of P&L". Reporting rule 3 was followed. **Nobody asked which
six, and one of them was PNK.** Fifteen studies then ran on the unbounded
panel. **A concentration report is not finished until the top trade is named,
its bar is printed -- open, high, low, close, volume, return -- and any event
on that bar is shown beside it.** A +356% day with a +0.9% price move is
visible in one line, and would have been in D322.

**Two more, on the data:** an events file's total-return adjustment must be
checked against the price -- a distribution that came out of the price moved
the price, and one that did not is not a distribution; and **a derived-array
cache must be keyed on the panel builder**, or a data fix reproduces the old
numbers silently. `run_d303_reference` now is; `d290_build_cache` was not, and
D334 rebuilt it: 48 of 51 scores bit-identical, `signed_vol` moved on 86 cells,
`ivol_21` on 12.7% of all cells and `beta_63` on **30.3%** (max 0.16 in a beta)
-- thirty fabricated days reached every name through the cross-sectional
market return. The three symmetric books moved by under half a basis point per
bar (D335 Q6). Two published references are still on the unbounded panel --
`d300_width.json` and D331's `S_F0` cells -- and are owed a re-base beside the
old file (D337 §9-10).

## 19. The short side of this programme is a cost failure, and neither sizing nor borrow changes the verdict

**From [D335](decisions/D335-RESULT-one-short-leg-pays-and-no-pairing-beats-the-symmetric-book.md)
and [D337](decisions/D337-RESULT-constant-shares-is-worth-46-bp-and-does-not-rescue-the-short-leg.md),
2026-09-05.** Both pre-registered.

**Every one of the 46 dimensionless signals, symmetric at depth 2 and k=20, F0
deal windows removed, published spread convention, per trade: one short leg in
forty-six nets above zero** -- `close_in_range`, at +4.9 bp against a p95 of
-13.3 and a p50 of -132.9. The long legs' p50 is -57.8 with six positive. Under
the old per-bar median six of the top ten shorts were positive; **PUB alone
turns the short side from a signal question into a cost question**, and it is
the first time that has been stated across every signal at once.

**Sizing does not change it.** Section 12's mechanism -- a rebalanced short
pays a variance premium -- is exactly measured: holding the name in constant
shares is worth **+45.85 bp a trade** on `hist_L`'s short leg (the identity
compound = summed - premium holds to 2e-14) and the leg still nets **-53 PB /
-135 PUB**. Where the premium is largest, 55-58 bp on `skew_63`'s fixed-hold
short, the leg is retired for takeover targets. **And the premium is a property
of what the target exit SELECTS, not of how long the book holds**: the fixed
20-bar hold's premium is -33.8 against the target exit's -45.8 at 11 bars. The
exit fires on the paths that moved, and those are the paths a rebalanced short
pays on. D328/D329 wrote it as a duration effect; withdrawn.

**Borrow does not change it either.** At declared stress rates -- GC 50 bp/yr,
hard-to-borrow 500 on names in an F0 deal window or below $5 at entry -- the
incumbent pays **0.25 bp/bar**; the house 300 bp/yr flat is 1.19. D332's
convention gap on the same book is 20. The F0 filter removes most of the
hard-to-borrow cohort from a jump-detecting short by itself (44% -> 7% of
`skew_63`'s short bars).

**The leg-wise construction is a per-trade result without a book** (D331,
D335, D337). Every top-3 x top-3 pairing beats `retrace_leg` symmetric per
trade and none beats it per bar (+14.80 best against +18.93): pairings hold
19-22 names a bar against 14, so section 10's opportunity cost -- still
unmeasured -- eats the per-trade edge. Under compound accumulation the
`hist_L`/`skew_63`-F0 book falls further, because the flag applies to both
legs and the long leg gives back its +25 bp harvest. Only a mixed convention
-- rebalanced long, constant-shares short -- puts it above zero, at +1.87 PUB
after borrow; post-hoc, and not a result.

**What stands: `retrace_leg` symmetric at k=20 under F0 and PUB, +18.93
bp/bar, Sharpe +0.546** -- the best book in the programme for the third study
running. `hist_L`'s long leg is third-best per trade (+44.8 PUB) and zero as a
book, at 69 bp a name in $11 stocks. `rsi`'s long leg is first per trade
(+63.9) and its book is -2.55. **The leg that wins per trade is not the leg
that makes a book**; the two lenses are never compared on the same statistic,
and the book is the one that trades.

**Three rules:**

1. **Charge the published convention before ranking legs.** The per-bar
   median made six short legs look positive that are not.
2. **A mechanism's size is not its sign.** The rebalancing premium was named
   in D328, measured in D329 and tested in D337, and at every step it was
   real; it never decided a leg. Test whether a mechanism *orders the
   outcome* before building on it.
3. **A per-trade winner needs a book-level check in the same study.** D329
   and D335 both produced per-trade results whose books were flat or negative.

## 20. The best book in the programme is five names, and four of them could not have been bought

**From [D338](decisions/D338-RESULT-five-names-and-a-18-cent-stock.md), 2026-09-05.**
Pre-registered; three of nine predictions.

`retrace_leg` symmetric at k=20 under the deal filter -- +18.93 bp/bar PUB,
Sharpe 0.546, the best book for three studies running -- got its four-group
report. **It orders the gate**: +32.4 bp/bar gross against a rank-rotation
null whose maximum in 200 draws is +15.2, gross Sharpe 0.94 against 0.65, above
every draw on every statistic. **And what it orders the gate toward is the
illiquid tail.** Five names of 673 are half the P&L. The top trade is VSA, long,
2025-01-31, one bar, +330%, **15.9% of the ledger**: a real move with no
dividend, in a stock trading at about $0.18 (two later reverse splits inflate
the adjusted close to $90.55) on **2,738 shares the day before**, at the 4th
percentile of the universe by dollar volume. Four of the five largest trades
are sub-$2 names in the bottom 7% by dollar volume, bought at the close on the
day before a +68% to +330% gap, three of them held one bar. All four fall below
dv28's cut -- **which is why D323 found `retrace_leg` peaks with dv28 OFF.**

The core pays: the symmetric 1% trim is +125.9 bp a trade against a 68 bp round
trip. The headline needs the tails: the ex-top-1% mean is +70.3, at breakeven.
Eight of fourteen years are net-positive; 2016-2019 are four losing years in a
row; the second half of the sample is 76% of the P&L and 2025-2026 carry two of
the five names. It is **not declared a candidate.**

**Three things that generalise:**

1. **Cost in bp scales with 1/price; fillability scales with dollar volume, and
   no cost model here charges it.** A rank book on a dead-inclusive universe
   with no price or volume floor will find the sub-$2 names on the day they gap,
   and a same-close fill will book the gap. The held *median* dollar volume
   ($20.5M here) says nothing; the top trades' entry-day dollar-volume
   percentile says everything. **The four-group report now prints it beside the
   top trade's bar** -- section 18's rule, extended.
2. **A null's teeth requirement belongs on the statistic that tests the
   signal.** Under the published cost convention, a matched-cost rotation null
   goes negative at p95 on net Sharpe because a random 4-name book does not pay
   13 bp/bar -- the cost is large, the null is not broken. D338 put the teeth
   clause on net under both conventions and a correct null failed a correct
   test. Gross null for the signal; matched-cost net null beside it for the
   cost; R7's flag on the gross null's p95.
3. **A cell in another study's table is not a book.** `retrace_leg` was "the
   best book in the programme" in three records off a bp/bar and a Sharpe.
   Nothing about it was wrong; nothing about it was a book until the top trade
   was named. The order of work is: four groups and the top trade first, then
   the comparisons.

## 21. The fill convention credited the overnight gap to every entry, and it was worth more than the spread

**From [D340](decisions/D340-RESULT-the-same-close-fill-was-three-quarters-of-the-best-book.md),
2026-09-05.** Pre-registered; four of six.

Every D300-family book computes its signal at the close of t-1, ranks on it,
and opens the position at bar t **earning close[t-1] -> close[t]**: a fill at
the signal's own close. No book can do that; the earliest honest fill is the
next open, and the gap between the two accrues to a position that could not
have existed. With a `fill="open"` flag on the simulator -- entry bar earns
close[t]/open[t] - 1 against an open-to-close market, every later bar as
before, default bit-identical -- the same cell, gate and exit rule give:

```
                                   close fill     OPEN fill
retrace_leg F0 k=20, PUB net         +18.93         +5.14     bp/bar   (-73%)
  gross                              +32.37        +18.06
  invariant PUB per trade            +10.02        -18.27
  long leg per trade                 +46.23        -12.03
incumbent C0, PUB net                -12.68        -15.90              (-3.2)
```

**The gap credited per entry was +44.8 bp on retrace_leg's long leg and +27.2
on its short** -- larger than the published half-spread on either leg. Both legs
were flattered: names that broke below their swing low gap UP at the next open,
names above their swing high gap DOWN. **A structure-breakdown signal at the
close is partly a forecast of the next open**, and the convention booked the
forecast as if it were tradeable. The incumbent's premium is +20.6 per long
entry; at 2.4x the turnover it costs nearly as much per bar.

**It is not only the entry-bar mark.** Only 378 of 1,256 trades recur across
fills: the target reads the accumulated excess, the entry bar's excess differs,
the first exit fires on a different day, a slot frees on a different day, and
the books walk apart. D338's top trade is not held under the open fill at all --
both long slots were taken. The gaps left and the squeezes stayed: the top-5
share ROSE from 42% to 54%. Under the open fill the cell is above its null on
gross bp/bar and inside it on Sharpe.

**Three rules:**

1. **A simulator's timing convention is part of the cost model and is declared
   like one.** Forty studies inherited "mark with r1[:, t]" from D295 without
   naming it as a choice. Every net number before D340 is a same-close-fill
   number and carries an open-fill companion where it is next quoted.
2. **Test the fill on the top trades first.** Three of D338's five largest
   trades were one-bar holds; the question "what did the entry bar earn, and
   from which price?" answers itself off the bar the top-trade rule already
   prints. Section 18's rule now includes it.
3. **The family's rotation null has 24 distinct values.** `shift` runs 1..24,
   so 200 draws are 24 books and p95 is the maximum whenever the top value
   recurs. "p = 0.005" means "above all 24" and its floor is 1/25. A finer null
   is owed before another p is quoted at three decimals.

## 22. The illiquid tail was every book's top trade and none of their edge; the universe now has a floor

**From the D339 census and [D339](decisions/D339-RESULT-the-ordering-survives-the-floor-and-the-book-is-three-basis-points.md),
2026-09-05.** Census: stage 0, no predictions. Study: pre-registered, six of nine.

**The census** cut every trade of 46 symmetric F0 books and the incumbent on an
as-traded prior close below $5 and on the dv28 cut at entry. **25 of 47 books
take more than half their P&L below the floor; 35 of 47 top trades fail it;
nine names -- VSA, TAOP, AHT, RLOC, PRMW, WATT, CYCN, KODK, DRYS -- supply the
top trade of 30 books.** The floor fails 29.3% of live name-bars; the sub-$5
share of the universe went from 3% in 2010 to 13% in 2025. That is a property
of a dead-inclusive fixture with no floor, not of any signal: an extreme-rank
selector finds the junk tail first, and the junk tail gaps.

**The floor** -- as-traded close at t-1 >= $5 (the adjusted close times the
split ratios dated after the bar; a floor on the ADJUSTED close would look
through future reverse splits, and VSA's $90.55 was $0.18) AND the dv28 pass,
both inherited round numbers -- applied to the score before ranking so the name
is REPLACED:

```
                              unfloored     floored      maxDD
retrace_leg F0 k=20, PUB     +18.93         +3.14       13,829 -> 8,406
rsi F0 k=20                   -2.55         +4.05       30,751 -> 6,751
hist_L F0 k=20               -26.79        -11.56       50,981 -> 19,880
incumbent C0                 -12.68        -13.02       top trade VSA -> KODK
```

**The tail the floor removes was not edge.** Three books improve, the fourth is
unchanged on net and loses its fabricated-looking top trade. `retrace_leg`
loses five-sixths of its net and still orders the liquid gate -- above its
rotation null's maximum on gross -- but at +3.14 bp/bar, Sharpe 0.16, seven of
fourteen years positive, and **-24.5 a trade on the invariant lens with both
legs negative**: the two lenses disagree in sign, which is section 10's
opportunity cost with its sign finally visible. It is the first book here whose
LEFT tail does the work (mean +75 below median +223, bottom 1% -49% against top
+44%), reporting rule 2's tell seen in the direction it was written for.

**Replace beats starve.** A universe definition fills the vacated slot with the
next liquid name and is worth 3-6 bp/bar over dv28's hole. **From D339 on the
floor is the declared universe**; a study on the unfloored one says so and
reports both.

**And with section 21 beside it, run together (D341): the best book in the
programme, scored under the floor AND an honest fill, is +2.68 bp/bar PUB.** The
prediction written in STACK section 6 before the run said "at or below zero";
section 23 is about why it was wrong.

**Two rules:**

1. **Fillability is a cost no spread model charges.** Cost in bp scales with
   1/price; whether a book can exist at all scales with dollar volume. The
   four-group report prints the top trades' entry-day dollar-volume percentile
   and as-traded price beside the bar, and a held MEDIAN says nothing about it.
2. **Run the census before the study.** Twenty minutes of stage-0 measurement
   turned "is this one book's problem?" into a number (25 of 47) before any
   prediction was written, fixed two of the predictions, and made the floor a
   definition rather than a variant. [[stage-0-premise-check]] applied.

## 23. Corrections that share a cause do not add: the honest number is +2.7, not zero

**From [D341](decisions/D341-RESULT-honestly-scored-retrace-leg-is-2-7-bp-a-bar.md),
2026-09-05.** Pre-registered; five of eight; the load-bearing prediction wrong.

Sections 21 and 22 each moved `retrace_leg` from +18.93 to about +4. STACK
predicted that together they would take it to zero or below. **Together they
take it to +2.68 bp/bar PUB, +2.46 after borrow** -- the two corrections overlap
by 13.3 bp/bar. The overnight gap the fill credited was three-quarters in the
sub-$5, bottom-decile-volume names the floor removes: the long-leg premium per
entry falls from +44.8 to +11.2 once the floor is on. The short leg's does not
(+27.2 -> +29.2): liquid names above their swing high still gap down at the next
open, and a floored book pays that under an honest fill.

```
PUB net bp/bar          none/close  floor/close  none/open  FLOOR/OPEN  interaction
retrace_leg F0 k=20        +18.93       +3.14      +5.14       +2.68       +13.33
incumbent C0               -12.68      -13.02     -15.90      -13.41        +2.82
rsi F0 k=20                 -2.55       +4.05      -3.85       +3.52        +0.77
hist_L F0 k=20             -26.79      -11.56     -14.88      -10.28       -10.63
```

**What the honest retrace_leg is:** gross +13.87 against a rotation null whose
maximum over all 24 distinct shifts is +12.28 -- the ordering of the liquid gate
is real and this is the strongest statement the family's null can make -- and a
book with a 0.14 Sharpe, -27 bp a trade on both legs, nine names to half its
P&L, CHK's bankruptcy at 9.9%, and 44% of its P&L in names that later delisted.
By D339's letter it is the first cell to survive every convention the programme
owns; D341 recommends against spending the one holdout read on it.

**`rsi` is the better liquid book.** +3.52 under both conventions, Sharpe 0.18,
fourteen names to half, a 5.5% top trade, and NO gap premium on either leg once
floored (+0.7 / -7.7) -- the open fill barely touches it. Its unfloored book was
negative. It is the first book here to gain from honest scoring, and it gets the
next candidate record.

**Three rules:**

1. **Corrections with a common mechanism do not add.** Predict the interaction
   or predict nothing; a sum of marginal effects is a prediction that the
   mechanisms are disjoint, and here they were the same names.
2. **A fill change makes a different book when the exit reads the mark.**
   `hist_L`'s unfloored book IMPROVED by 12 bp/bar under the open fill though
   its long leg had been credited +92 bp a trade. The per-entry premium says
   what the convention credited; only the re-run says what it did.
3. **Say the null's resolution on every line.** "Above 24 of 24" is the
   ceiling of a 24-shift rotation and the honest form of p = 0.005.

## 24. The programme has a declared candidate, and it is three and a half basis points a bar whose every trade loses money uncapped

**From [D342](decisions/D342-RESULT-rsi-is-the-declared-candidate-at-three-and-a-half-basis-points.md),
2026-09-05.** Pre-registered; six of eight; the two that decide held.

`rsi` symmetric at k=20 -- under the deal filter, the dividend bound, the
published spread, the universe floor, a next-open fill and GC+HTB borrow -- is
**+3.52 PUB bp/bar, +3.32 after borrow, Sharpe 0.18**, above all 24 rotations of
its liquid gate on gross (+14.72 against a null maximum of +14.64) and on PUB
net Sharpe (+0.181 against +0.149, with the matched-cost null's p95 negative).
Fourteen names to half the P&L, a 5.5% top trade that is a real eighteen-bar
decline in a liquid biotech, no overnight-gap premium on either leg, eight of
fourteen years positive. It is the personal track's first **declared
candidate**. Its out-of-sample design is written and not run.

**Three things about it that a candidate record must say:**

1. **Every trade loses money uncapped.** The invariant lens is -4.8 bp a trade
   with both legs negative (-7.9 long, -1.6 short); the variant book is +3.5 a
   bar. The book earns through the slot cap's selection of the two most extreme
   names per side -- D300's concentration finding, now the whole edge. Section
   10's opportunity cost has its sign on both candidates, and it is the book.
2. **The left tail does the work, more than on any book before it.** Skew
   -1.69, the bottom 1% of trades -54% of P&L against +40% for the top, a 0.51
   payoff carried by a 72% win rate. The twelve worst trades are squeezed
   shorts (MSTR in the bitcoin run, SMCI in the AI run) and cheap longs; two of
   the twelve are shared with `retrace_leg`'s left tail, so the two candidates
   lose on different events.
3. **The floor leaked at re-listings, and the leak cost money.** NBIS's first
   day back after an eight-month halt was 4.4% of the book. Its trailing dollar
   volume had fewer than 21 observations, and D320's rule -- a missing estimate
   never excludes, written so a filter cannot become a liveness proxy -- passed
   it into a liquidity-floored universe. **D343 closed it**: the dollar-volume
   clause now requires its 21 observations (`keep_v2`, 30.9% of live name-bars
   fail, the universe from here). The 35 trades the hole had admitted across
   three books **lost 134 bp a trade on net** -- the one relisting pop was
   outweighed by names re-entering the tape against the book. `rsi` under
   `keep_v2` is +3.10 PUB, +2.90 after borrow, Sharpe 0.16, and its margin over
   the null's best rotation widened from 0.09 to 1.3 bp/bar, because the best
   rotation had held a relisting pop too. `retrace_leg` is bit-identical under
   the clause. A rule from the record: **a prediction about a symbol is not a
   prediction about a trade** -- the fixture stitches Yandex and Nebius under
   one ticker, and "NBIS is not in the ledger" was false for eight Yandex trades
   from 2022 the clause was never meant to touch.

**On the read.** A 0.18-Sharpe book whose annual nets are noise around +3.5 bp
cannot be distinguished from zero on one holdout of a few years, and the holdout
has one read. D342 recommends against spending it until the rotation null has
more than 24 values and the cell still clears it, and until the re-listing hole
is closed. Both are owed before the read, not after. The decision is the
principal's; the programme total stays at zero reads.

**One rule, from the way this record was built:** a second runner writing the
same assertion found that the first's could not fail -- D341's floor-share check
had a fallback that defaulted to the value under test. **An assertion with a
default is an assertion that cannot fail.** Raise on a missing key.

## 25. The hold is a cost lever, and under a target exit k is a cap, not a hold

**From [D344](decisions/D344-RESULT-the-hold-is-a-cost-lever-k40-nets-5-and-turnover-is-not-1-over-k.md),
2026-09-05.** Pre-registered; four of eight; the load-bearing one held.

The candidate pays 11.3 of its 14.4 gross in cost at k=20. At **k=40 it pays
7.6**, gives up 1.7 of gross, and nets **+5.14 PUB bp/bar, +4.93 after borrow,
Sharpe 0.27**, with drawdown down a quarter, nine of fourteen years positive,
and the ordering **above all 24 rotations of its gate on every statistic** --
gross, gross Sharpe, both net Sharpes -- the only cell in the programme to
manage that. k=10 is -5.89 and inside its null. D323 had ranked rsi's holds the
other way on the unfloored universe with the same-close fill and the per-bar
spread; under honest costs the arithmetic reverses.

```
rsi, keep_v2, open fill          k=10      k=20      k=40
gross bp/bar                   +11.52    +14.36    +12.70
cost bp/bar PUB                 17.40     11.26      7.56
NET bp/bar PUB                  -5.89     +3.10     +5.14
NET Sharpe PUB                  -0.29     +0.16     +0.27
turnover per bar               0.1480    0.0955    0.0664
invariant PUB per trade         -16.6      -3.7     -11.8
above k of 24 on gross         22 of 24  24 of 24  24 of 24
```

**Both mechanism predictions were wrong, for one reason.** Turnover was
predicted to scale as 1/k (D296) and gross to fall monotonically in k. Turnover
ratios came in at 1.55 and 1.44, and gross PEAKS at k=20. D296's 1/k is a
fixed-hold result; here **k is a cap under the D303 target exit**, most
positions close before it, the realised hold rises sub-linearly in the cap
(roughly 7, 10 and 15 bars), and a ten-bar cap truncates the reversion before
it completes. Cost per bar is the round trip over the REALISED hold.

**The two lenses disagree in direction on k.** Per trade, k=40 is worse than
k=20 (-11.8 against -3.7); per bar it is better, because it pays the round trip
a third less often. Section 10's opportunity cost again, with a new sign
pattern: a parameter that hurts every trade and helps the book.

**Two rules:**

1. **A cost lever that needs no new data comes before any signal work.** The
   hold moved the candidate more than anything since the floor, and cost half
   of one study.
2. **Read a mechanism on the construction it was measured on.** 1/k is true of
   a fixed hold and false of a cap; the pre-registration carried it across
   without checking which one the book had.

**Multiplicity three.** k=40 was chosen from three cells after seeing them; it
is written into the out-of-sample design as such and quoted beside k=20 and
never alone. Sharpe 0.27 still cannot be told from zero on any holdout this
fixture has.

## 26. The event book failed as calibrated, and taught three things the slot book could not

**From [D345](decisions/D345-RESULT-the-event-book-fails-as-calibrated-and-the-target-exit-was-the-wrong-exit.md),
2026-09-06.** Pre-registered; five of ten; the load-bearing prediction failed.
Axis C reopened at the principal's decision and closed again.

The construction: flat by default, long when the floored `rsi` at t-1 is at or
below a threshold, short when at or above its mirror, filled at the next open,
at most two per side (most extreme first), a unit of capital per position on a
base of four, cash otherwise; three exit arms. The threshold was calibrated on
exposure -- two concurrent positions per side under a fixed hold -- and never on
return. **It landed at 11 / 89**: on this universe the oversold tail is rare and
the overbought tail is not, so the book was short three times as often as long,
fired nine times a year, and could not be separated from a per-name time
rotation of its own signal dates (gross Sharpe at the null's median). Deployed
PUB Sharpe -0.25 against the slot book's +0.27 at k=40.

```
arm                lens       trades  mean/trade  net/trade   TOTAL net  DEPLOYED net
target             variant       192      +52.6       -2.2       -1.66        -5.87
invalidation       variant       146     +237.6     +182.4       +0.69        -0.09
cap                variant       126     +209.0     +155.0       -0.01        +1.13
target             invariant     279      +68.3      +12.9       -1.45       -10.60
```

**Three things the slot book could never have shown:**

1. **The target exit belongs to the always-invested construction.** D303's
   rule fires at the first move; in the slot book that freed a slot for the
   next name. In a book with no refill it cuts the winner: +52.6 a trade under
   the target, +237.6 under signal invalidation, +209.0 under a bare cap.
   **D295's "stops, displacement, idle conditions, the ladder: dead" is a fact
   about a book that refills behind every exit**, not about exits. Amended.
2. **A threshold entry cannot be calibrated to a slot book's exposure.** Two per
   side is a property of always being invested; asking a threshold to produce it
   sends the threshold to where the signal barely fires. A threshold is
   calibrated on an entry rate.
3. **A capital series for an unbalanced book must carry the hedge its ledger
   carries.** Every ledger P&L here is `sgn * sum(v - m)`; the slot book's bar
   series is hedged by being two-and-two; the event book's raw signed sum was
   not, and its 0.31-long / 0.81-short tilt hid a market drag of roughly 0.8 to
   1.3 bp/bar. The per-trade lens and the per-bar lens disagreed in sign partly
   for that reason.

**What is kept.** The event kernel, proven bit-identical to the slot
simulator's uncapped lens on 4,021 trades -- the slot book's invariant lens IS
an event book whose signal is "ranked in the top two this bar". **The first
positive invariant lens in the programme**: every `rsi <= 11 / >= 89` signal,
held to the target or 40 bars, nets +12.9 a trade under PUB, at p = 0.055
against the first null here with more than 24 values (200 distinct per-name
rotations). Thin, borderline, honest. And a null construction -- rotate the
signal per name in time -- that fits the slot book too.

**The rule:** a closure is a fact about the construction it was measured on
(D344's 1/k, D295's exits), and a pre-registration protects against reading a
result, not against designing a study that answers the wrong question. If the
event book is retried it is a new record with three changes: threshold on
trade count, hedged series, invalidation exit.

## 27. The corrections compressed the signal table rather than shifting it, and the incumbent's primary is the best book under honest scoring

**From [D346](decisions/D346-RESULT-two-long-legs-pay-uncapped-and-hist-L-at-k40-is-the-best-book.md),
2026-09-06.** Pre-registered; five of seven. Multiplicity 46 per leg per hold,
92 books; every number below is one of 92.

D335's per-leg table -- every dimensionless signal's long and short leg per
trade -- re-run under the universe floor and the next-open fill, at k=20 and
k=40:

```
PUB net per trade, invariant        k=20                          k=40
long legs positive of 46            2  (hist_L +31, rev_21 +6)    3  (rev_21 +60, hist_L +44, trailing_return +30)
long-leg p50 / p95                  -47 / -6                      -45 / +22
short legs positive of 46           2  (on_share +21, rsi +4)     1  (on_share +31)
best variant book, PUB bp/bar       rsi +3.10 (Sharpe 0.16)       hist_L +12.42 (Sharpe 0.40)
variant books positive of 46        4                             6
```

**Two things, neither predicted.**

1. **The corrections compressed the table.** Twenty-nine of 46 long legs
   IMPROVED against D335 (median +7.9 bp a trade) while the best legs fell
   hardest: rsi +64 -> -11, id_mean +35 -> -67, retrace_leg +46 -> -23. The
   long-leg 95th percentile fell from +42 to -6 and the median rose from -58 to
   -47. The legs that looked best were harvesting the sub-$5 tail and the
   overnight gap; the legs that looked worst were losing in the same tail.
   **A ranking of signals measured on the unfloored, same-close universe was
   mostly a ranking of exposure to one tail**, and D290's tier list -- the
   programme's map of signal quality since the shortlist -- was drawn on it.
2. **The incumbent's primary comes back at the longer hold.** hist_L -- the
   signal D338 called "a per-trade signal in names too expensive to hold" and
   D341 found at -11.6 bp/bar -- is, at k=40 under the floor and the open fill,
   **+12.42 bp/bar with a Sharpe of 0.40**, its long leg +44 a trade uncapped,
   holding $23 names instead of $11. Two and a half times the declared
   candidate. It is the maximum of 46 at one of two holds, unnulled, with no
   top trade named; FINDINGS section 20 says what that is not yet, and it gets
   the next candidate record before anything is built on it.

**Two smaller things.** The hold is signal-specific: k=40 hurt rsi's per-trade
lens (D344) and helped hist_L's and rev_21's. And of the three signals proposed
for the event book -- rsi's turn, retrace_leg's reclaim, rev_5's reversal --
none has a long leg that pays uncapped; rev_5's grosses +71 a trade at t = 3.0
and pays 90 of it in spread on $12 names. The conditional-profile study's long
signals are hist_L and rev_21.

**The rule:** re-run the whole table when the conventions change, not the cells
you were looking at. Four cells had been re-measured under the corrections and
they happened to be four that fell; the other 42 mostly rose, and the best book
in the programme was among them.

## 28. The long excess is cohort membership, not timing: no long signal beats its own names at random times

**From [D347](decisions/D347-RESULT-no-long-signal-beats-its-own-names-at-random-times.md),
2026-09-06.** Pre-registered; zero of eight.

Four long signals as events on the floored, deal-filtered universe -- hist_L
and rev_21 entering their bottom decile, rsi's turn and decile as references --
every event taken at the next open, hedged against the floored universe's own
equal-weight return, held 40 bars. Each earns a positive excess per trade
(hist_L +60 bp, t 4.8, 15,889 trades). Then three controls that each carry the
drift:

```
                     observed   A: same names, random dates   B: same day, same rsi bucket, random name   C: random side
hist_L                 +60.4    p50 +70.8  p95 +90.8  NO       p50 +24.0  p95 +39.7  yes                  p95 +21.7  yes
rev_21                 +46.5    p50 +59.6  p95 +80.1  NO       p50 +29.0  p95 +42.0  yes                  p95 +21.5  yes
rsi turn               +16.0    p50 +45.2  p95 +60.3  NO       p50 +26.3  p95 +36.7  NO                   p95 +20.5  NO
rsi decile             +30.4    p50 +48.0  p95 +65.9  NO       p50 +20.2  p95 +26.4  yes                  p95 +18.1  yes
```

**Every signal earns less than its own names held at random times.** The names
these signals touch are a cohort that earns +45 to +71 bp per forty bars over
the floored market whenever it is held; the signals' timing subtracts 10 to 29
of it. Three of four beat a random same-day, same-bucket name -- the name
selection is real -- and control A says it is STATIC. **A market hedge cannot
remove a per-name mean**: neither the floored equal-weight hedge nor a rolling
63-bar beta (which moved hist_L from +60 to +52 and lifted the rsi references)
took the cohort's excess out. The hedge for cohort drift is the name's own
unconditional excess, which is what control A measures.

**The pairing design is reversed on its own terms.** The interaction with the
rsi ranking -- E[signal, bucket] - E[bucket] - E[signal] + E[all] -- is most
negative in the most oversold rsi bucket for every signal and positive in the
middle: hist_L's events on names in the bottom 2% by rsi earn +1 bp, on names
in the middle half +103. A momentum-histogram extreme on a name that is also
deeply oversold is a name in free fall; on a neutral name it is a pullback.
Running the long signal on the top of the rsi ranking would run it where it
does worst.

**And the rsi ranking's own profile is a base rate.** Forward-40 hedged excess
of every floored name-bar, by rsi percentile: +23, +10, +21, +32, +27, +22
below the 75th percentile; +6, -8, -12, -31 above. Low-rsi names earn 20-30 bp
over forty bars with no signal firing at all. That is the slot book's long side
as a cohort property, and whether it survives ITS control A is the next study.

**What this does to the record so far.** The slot books' null since D300
rotates names within the gate on the same day -- D347's control B, which these
signals beat. The per-name time rotation -- D290's original "rotation" null --
was dropped when the programme moved to the gate family, and **no slot cell has
faced it**: every per-trade "long leg pays" in D335, D344 and D346, and both
candidates' bp/bar, are unmeasured against cohort drift. D290's long-only
verdict stands for long signals, sharpened: not market drift (the ledger is
hedged) but cohort drift.

**Three rules:**

1. **A null that rotates names is not a null that rotates time.** Cohort drift
   only shows against the second. Every candidate carries both from here.
2. **Hedging is not a substitute for a control.** The market hedge and the beta
   hedge left a 45-70 bp per-name mean in place; the control found it in one
   run.
3. **Test the interaction before designing around it.** The pair book's
   premise -- a long signal is best on the extreme of the ranking -- was
   measurable in one table and false.

**Amended by §29 and §30 (2026-09-06).** The scope claim above -- that every
slot-book positive was unmeasured against the time rotation and might fall to
it -- was tested in D348: the slot books survive it, and their long legs are
timing. The base-rate line "+6, -8, -12, -31 above" carries an artefact: the
-31 was names with no rsi rank digitised into the top bucket; the top 2% earns
+11 long (D349 §6).

**Withdrawn by §32 (D351, 2026-09-06).** The headline of this section is
withdrawn: control A rotated events within every priced bar and 11-13% of
them landed on the excluded tail at +226 to +316 bp per forty bars. Rotated
within the floor, hist_L, rev_21 and the rsi decile are ABOVE their own names
at random times, B and C. The cohort premium is +7 to +24, not +45 to +71. The
interaction reversal and the rsi turn's failure stand. Rules 1 and 3 stand;
rule 2's numbers do not.

## 29. The slot books survive the time rotation: the depth-2 long leg is timing, and on a slot book the rank rotation is the harder null

**From D348, 2026-09-06.** Pre-registered; four of seven, the load-bearing one
held.

**The null.** Each name's score rolled in time within its own finite bars --
the NaN pattern, the floor, the deal filter and every per-bar count untouched
-- then the unchanged pipeline: lag, rank, gate, both simulates, both costings.
200 draws, offsets independent per name. Beside it, the 24-shift rank
rotation the slot books have always faced.

**The result.** `rsi` k=40 (+5.14 PUB), `hist_L` k=40 (+12.42) and
`retrace_leg` k=20 (+2.68) are above every one of 200 draws on gross bp/bar,
PUB and PB net, net after borrow, gross and net Sharpe, and both legs' per-trade
means. Control A's PUB net is centred at -11 to -14 bp/bar with a p95 of -4 to
-9; the zero-offset draw reproduces D346 and D343 to 0.0.

**The long leg is timing.** Control A's long leg is centred at -13 (`rsi`) and
-10 (`hist_L`) bp a trade against observed +39 and +141. D347 found the
opposite on the event ledger because it rotated *events* -- 23,491 decile
entries across ~1,500 names, weighted by how often each fired -- while this
rotates the *score* and re-ranks: at a random date the depth-2 gate selects
whichever names' rotated scores are most extreme, which over-selects names
with long extreme stretches held at moments unrelated to their true state, and
those lose. ~~**Cohort drift is a property of the decile-entry event, not of the
depth-2 selection.**~~ **Withdrawn by §32:** D347 and D348 disagreed because
D347's null was rotating events onto the excluded tail, not because the
constructions differ; under a null confined to the floor, the event ledger and
the slot book agree that the long side has timing. The numbers of this section
stand; this paragraph's mechanism does not.

**The rank rotation is the harder null on a slot book.** Its p95 on gross is
above the time rotation's on all three cells (+8.5 vs +4.5, +10.1 vs +8.1,
+11.3 vs +4.5) because it keeps the day -- the gate, the cross-section, the
regime -- and permutes only the preference order inside it; the time rotation
breaks those too. Both are carried from here; the rank rotation binds.

**`hist_L`'s short leg is a cohort premium.** Under control A it is centred
at +17 and the observed +33 sits at the 70th percentile: names with the
highest `hist_L` fall at random times. `hist_L`'s book is its long leg, and
its candidate record must say so.

**Turnover as a signature.** The observed cells enter less often than any
rotated book (847 against 901-985 for `rsi`; 771 against 914-995 for
`hist_L`): an aligned score holds to the cap or the target, a rotated one is
displaced sooner. Noted, not built on.

**Rules:**

1. **A control's finding belongs to the construction it was measured on.**
   The same words -- "the same names at random times" -- named two different
   nulls in D347 and D348, and they gave opposite answers about the same
   signals. Say which object is rotated.
2. **On a slot book, carry both rotations and expect the rank rotation to
   bind.** The time rotation is the one that carries per-name drift; the rank
   rotation is the one that carries the day.

## 30. Every short signal beats its own names at random times and still loses: the names it shorts rise

**From D349, 2026-09-06.** Pre-registered; three of eight, the load-bearing
one falsified.

**Five short events** -- `on_share`, `skew_63`, `close_in_range`, the `rsi`
decile and the `rsi` turn, each a fresh entry into the top decile of the lagged
floored percentile (or the cross down through 70) -- every event taken, next
open, hedged against the floored market, 40-bar cap, PUB and borrow in the net.

| short, cap, bp/trade | observed | A p50 | B p50 | timing (obs - A p50) | mirror (long) |
|---|--:|--:|--:|--:|--:|
| `on_share` | -40.9 | -66.6 | -23.7 | +25.6 | +40.9 |
| `skew_63` | -3.6 | -70.5 | -17.7 | +66.9 | +3.6 |
| `close_in_range` | -11.5 | -56.3 | -17.1 | +44.9 | +11.5 |
| `rsi` decile | -1.8 | -67.0 | -9.4 | +65.2 | +1.8 |
| `rsi` turn | -18.6 | -69.1 | -11.1 | +50.5 | +18.6 |

~~**Every one beats control A** (above all 100 draws)~~ **Amended by §32:**
control A here carried D347's defect; within the floor the names rise 22-41 bp
at random eligible times (not 56-70), on_share's timing is +0.4, skew_63 is
inside A', and three of five are above it by 11-33. **Every one loses in mean
before cost** -- that stands, and so does the rest of this section. Not enough: none beats the
random-direction control, and the long of every short event pays. This is
D238's "real skill, cannot be traded" in the current conventions, with the
reason corrected: **it is the cohort's rise that eats the timing, not the
cost.** Borrow is 8 bp a trade; HTB is structurally rare (0.0-0.1% of trades,
because F0 windows are removed from the score and the floor removes sub-$5
names); no half-spread makes a cap-exit short pay.

**The extreme of the ranking is where a signal does worst on both sides.**
`on_share`'s interaction with the `rsi` ranking is +52 in the middle buckets
and -46 in the top 2%; `skew_63`'s is -107 there. §28's reversal was not a
long-side fact. The pair book as designed -- a signal at the extreme of the
ranking, hedged with the extreme of the other side -- fails on the short side
too. **It has no trigger on either side under these conventions.**

**The event lens and the slot lens disagree on the short leg as they did on
the long.** D346's `on_share` short leg paid +21 and +31 a trade at depth 2;
the decile-entry event on the same score loses 41. Neither record speaks for
the other (§29).

**Erratum to D347.** `np.digitize` sends NaN to the last bin: 961,819 eligible
name-bars with no `rsi` percentile (nearly all off the warm base) were counted
in the top bucket's base rate and drawn into its control-B pool. Confined to
defined ranks, the (98, 100] bucket earns +11 bp long, not -31; (90, 95] and
(95, 98] are -8 and -12. D347's events sat in buckets 0-2, so its verdict is
untouched. D349 masks the NaNs and asserts it.

**Rules:**

1. **A short's control A is not centred at zero, so report "beats its own
   names" and "pays" separately.** Here every signal does the first and none
   does the second.
2. **Mask NaNs before `digitize`.** A bucket that silently collects the
   undefined is a cohort of its own -- here, young listings -- and it will
   look like a signal.

## 31. Three long triggers beat every honest control, and none pays the published spread

**From D350, 2026-09-06.** Pre-registered; one of eight on the letter, every
failure the one §32 predicts.

**The screen.** 46 scores x 3 percentile-event shapes = 138 long events, each
scored on the cached forward-40 hedged grid against its own names at random
ELIGIBLE times (control A, 1,000 draws) and a random same-day same-rsi-bucket
name (B, 1,000). 43 of 138 above A at p <= 0.05 against 7-9 from false
discovery (M_eff Li-Ji 108, Cheverud-Nyholt 136); BH at q = 0.10 rejects 34;
the family-wise grid-max p of the best member is 0.000; the oracle clears and
the noise does not. **Every E1 member on a reversal-type score has positive
timing** (hist_L +46, md +56, rsi +23, rev_5 +42, rev_21 +38, mom_252_21 +39,
dist_52w_high +123 bp over its own names at random times).

**The kernel, on the five gate survivors.** Under the pre-registered control
(D347's rotation within every priced bar) none passes; under the same rotation
confined to the floor, three pass A', B and C:

| long, cap, bp/trade | n | mean / median | t | A' p50 / p95 | trimmed | net PUB / PB |
|---|--:|--:|--:|--:|--:|--:|
| **rev_5/E1** | 27,316 | +43.4 / +41.8 | 4.8 | +19 / +30 | +35 | -19 / +18 |
| gap_reversal/E1 | 18,714 | +47.1 / +27.0 | 4.0 | +27 / +42 | +38 | -22 / +17 |
| cs_spread/E2 | 7,812 | +71.6 / +31.1 | 3.4 | +12 / +46 | +61 | -35 / +28 |

**rev_5/E1 is the cleanest signal on the programme's event record**: a
one-week reversal entering the bottom decile, mean equal to median, 27 names
to half the P&L, ten of fourteen years, positive in the down-years, top trade
1.3%. gap_reversal/E1's top trade -- and two other survivors' -- is GME in
January 2021; it earns +95 below the median price and -1 above, and its top 1%
carries more than all of it (symmetric trim +38). cs_spread/E2 is a name
entering the top decile of SPREAD: the floor's own illiquid edge, half its P&L
in twelve names.

**None nets positive after the PUB round trip** (62-106 bp); all three do under
PB. The invalidation exit is worse for every one. The long side's problem is
cost, as it has been since D285.

**The interaction, fourth table.** rev_5/E1 is -65 in the bottom 2% by rsi and
+66 / +150 in the (75, 95] buckets: a one-week reversal on a name that is not
oversold on the two-week rsi is a pullback; on one oversold on both it is a
falling knife. On every long signal in D347 and here, the bottom of the rsi
ranking is where the signal does worst. **The pair book's long trigger must
not be selected by the ranking's long extreme.**

**Rules:**

1. **Print both controls when a pre-registered one is found defective before
   the result is read.** The letter of Q1 closed a real signal; the record
   takes the corrected control and prints the defective one beside it in every
   table, and says why.
2. **A screen on a cached grid with sparse nulls costs seconds per member**;
   the kernel confirms the ranking. Screen wide, confirm narrow.

## 32. A null must live in the universe the strategy trades: D347's control A was trading the excluded tail

**From D351, 2026-09-06.** Pre-registered; four of seven, the load-bearing one
held.

**The defect.** D347's `rotate_confined` rolled each name's events within
finT -- every priced bar -- while the observed events sat on elig = finT &
keep_v2 after the hedge is defined. A rotated event could land on a bar the
strategy is forbidden to trade (close under $5, dollar volume below the cut,
no dollar-volume estimate yet), and the kernel traded it because it checks
finT and not keep. On the names these signals touch, those bars earn **+226 to
+318 bp** per forty bars -- the rebounds of cheap names, the tail D339 found to
be every book's top trade and none of its edge -- and 8-13% of every signal's
rotated events landed there. Reproduced to 0.0 from the studies' own seeds by
their own code path.

| kernel, cap, bp/trade | side | observed | A as run p50 | **A' p50 / p95** | above A' / B / C |
|---|---|--:|--:|--:|---|
| hist_L | long | +60.4 | +70.8 | **+23.9 / +41.8** | **yes / yes / yes** |
| rev_21 | long | +46.5 | +59.6 | **+12.9 / +26.5** | **yes / yes / yes** |
| rsi turn | long | +16.0 | +45.2 | +6.9 / +28.0 | no / no / no |
| rsi decile | long | +30.4 | +48.0 | **+10.6 / +24.4** | **yes / yes / yes** |
| on_share | short | -40.9 | -66.6 | -41.4 / -22.3 | no / no / no |
| skew_63 | short | -3.6 | -70.5 | -33.1 / -0.3 | no / no / no |
| close_in_range | short | -11.5 | -56.3 | -22.7 / -16.4 | yes / yes / no |
| rsi decile | short | -1.8 | -67.0 | -35.2 / -23.9 | yes / yes / no |
| rsi turn | short | -18.6 | -69.1 | -37.0 / -20.3 | yes / no / no |

**What changes.** §28's headline is withdrawn: three of four long signals beat
their own names at random eligible times, a same-day same-bucket name, and a
random direction; the cohort premium is +7 to +24 over a universe base rate of
+1.7, not +45 to +71. §30's verdict stands with its timing values cut (on_share
+0.4; skew_63 inside A'). §29's numbers stand and its mechanism is withdrawn:
D348 and D347 disagreed because one null was broken. D290 is not re-opened:
its rotation and its universe agreed. hist_L still nets -3.1 after PUB (+33.4
after PB): the edge is real and the published spread eats it.

**Why the assertions missed it.** [A] checked that every name's event count
was kept and that no trade carried a NaN; it never asked whether a rotated
event was a bar the observed events could have occupied. The tell -- a null
centred at +45 to +71 over a base rate of +1.7 -- was explained by a mechanism
("cohort drift") that this document, STACK item 18, and a memory rule then
carried for three records. The check was one line on the cached grid:
`mean(F[fin & ~elig])`.

**Rules:**

1. **Every null asserts `null_events ⊆ elig`** -- the same mask the observed
   events satisfy -- and reports the share that would not have been. Rotation,
   permutation, replacement, all of them.
2. **A null centred far from the base rate is the first thing to explain.**
   Suspect the null before writing the mechanism; never carry a mechanism into
   a rule until the null has passed its own construction check.
3. **When two studies disagree about the same signal, check the nulls are the
   same object on the same universe** before explaining the disagreement by
   construction.

## 33. No short event at any extreme beats random direction: the short side's timing is real and worth less than its names' rise

**From D352, 2026-09-06.** Pre-registered; two of eight, the load-bearing one
falsified.

139 short events -- 46 scores at the top 2%, 5% and 10% of the lagged floored
percentile, plus the rsi turn -- on the negated grid against the corrected time
rotation and a same-day same-bucket name from the defined-percentile pool. 23
beat their own names at random eligible times against 7-9 from false
discovery; BH rejects 13; four pass the gate. Under the kernel every survivor
is above the time rotation, two are above the same-day name, and **none is
above random direction**: the means are -11.5 to +25.6 bp a trade.

| short, cap, bp/trade | n | mean | A' p50 | B p50 | C p95 | above A'/B/C |
|---|--:|--:|--:|--:|--:|---|
| retrace_leg top decile | 23,108 | -3.8 | -30.2 | -10.8 | +14.6 | yes / no / no |
| on_persist top 2% | 5,968 | +25.6 | -21.0 | -19.2 | +30.3 | yes / yes / no |
| close_in_range top decile | 38,313 | -11.5 | -22.7 | -16.7 | +11.4 | yes / no / no |
| wick_asym top 2% | 20,660 | +2.6 | -17.9 | -18.3 | +17.0 | yes / yes / no |

**What it says.** A short on the signal's day is 11 to 47 bp better than a short
on the same name on a random day, and the same name's rise takes all of it. The
one positive member, on_persist at the top 2%, has six names to half its P&L
and a $4.95 top trade worth 13%. **on_share and skew_63 pass at no shape**: the
slot book's short leg at depth 2 (D346, +21 to +31 a trade) has no counterpart
in any event on the same score, as D348 found for the long leg. Cost is not the
problem; the means are near zero before it.

**Rules:**

1. **The short side of this universe has no event trigger.** Any pair book's
   short leg is the ranking's own extreme or nothing.
2. **The slot book's leg and the event on the same score are different
   objects on both sides.** Neither speaks for the other.

## 34. rev_5 entering the bottom decile is real at 200 draws on every control; a slot cap on it is a sample of its most extreme events

**From D353, 2026-09-06.** Pre-registered; seven of nine, the load-bearing one
held.

**The signal:** +43.4 bp a trade on 27,316 cap-exit trades, above its own names
at random eligible times (A' p95 +28.6 at 200 draws), a same-day same-bucket
name (B +35.8), and random direction (C +15.2); mean equal to median; symmetric
trim +35.3; 27 names to half the P&L; ten of fourteen years; positive in every
down-year; beta-adjusted +37.2. **-18.6 net under PUB, +17.9 under PB** on the
cap exit; negative under PUB at every exit. The invalidation exit holds 6.6
bars for +24 a trade -- +3.7 per bar held against the cap's +1.1. The fifth
table: the interaction is -65 in the bottom 2% by rsi and +66 / +150 in
(75, 95].

**The slot-capped event book on it, hedged.** The kernel's capital series is
now hedged as its ledger is (an additive option, every existing output
bit-identical, reconciled per bar to 1e-15 -- the second of D345's three retry
changes). At K=2 the book loses (-1.75 gross, -5.8 PUB), inside its own time
rotation: a two-slot cap on 72,677 events admits 161 entries in sixteen years,
**most extreme first** -- the deepest crashes each day a slot is free, the
events the interaction table says do worst. At K=4 it nets +3.5 PUB (Sharpe
0.31) on 322 entries, above its null, one cell of four.

**Rules:**

1. **A slot cap small against the event count samples the signal's extreme,
   not the signal.** Read every capped event book against its skipped share
   (99.8% here), and declare the K grid before the run.
2. **rev_5/E1 is a real long trigger and does not pay the published spread.**
   Its tradeability is D336's question, not another study's.

## 35. Hedging a trigger with the ranking's opposite extreme costs the pair most of what the trigger earns, and the ranking chooses no hedge

**From D354, 2026-09-06.** Pre-registered; two of seven, the load-bearing one
falsified; long arm only (D352 found no short trigger).

The principal's pair book: a rev_5 trigger long, hedged with a short
equal-weight basket of the three highest-rsi names that day, exiting together
on the trigger's cap or invalidation, slot-capped, costed per leg with borrow,
no market term. Two nulls that keep the membership: the trigger rotated in time
within eligible bars, and a random partner from the same-day 25-name gate.

| long arm, deployed | pairs | gross | net PUB | net PB | vol | per pair | trigger leg | basket leg | above N1 / N2 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|---|
| K=2, cap | 159 | -1.4 | **-4.9** | -4.0 | 285 | -55 | +126 | **-181** | no / no |
| K=4, cap | 318 | +9.6 | +5.9 | +7.2 | 222 | +381 | +488 | -107 | yes / no |

**The basket costs the pair 107-181 bp per pair** whichever gate names fill it:
the random-partner null is centred within a basis point of the extreme basket
at both K. The top 2% by rsi earns +11 long at random times (D349's corrected
base rate) and more on the days a five-day crash fires. **The pair is more
volatile than a market hedge** (285 vs 232 bp/bar): three names are not a
market. At K=2 the book is negative under both cost lines. At K=4 it nets
positive and sits inside the random-partner null, so what it earns is the
trigger.

**Rules:**

1. **The ranking chooses no hedge.** A random name from its top gate hedges as
   well as its three most extreme; the "move the basket to the (90, 98] band"
   retry is not written.
2. **Hedge a trigger with the market, not with a few names.** The pair
   construction added cost, vol and a losing leg to a real signal. Any retry of
   a pair design starts from the kernel and the random-partner null that are
   now in the tree.
3. **The pair book is closed on this construction; what survives of it is the
   trigger** (§34).

## 36. On a refilled slot book the target fires first: a signal-invalidation exit lengthens the hold and gives back gross

**From D355, 2026-09-06.** Pre-registered; zero of seven.

The slot simulator gained a signal exit -- leave when the name's lagged floored
percentile crosses back through the median -- added additively (every published
cell reproduces to 0.0 with it absent) and proven identical to the event
kernel's invalidation exit bit-for-bit on the invariant lens. On the two
candidate books it loses to the target:

| PUB net bp/bar | target | invalidation | both |
|---|--:|--:|--:|
| rsi k=40 | **+5.14** | +0.54 | +2.04 |
| hist_L k=40 | **+12.42** | +10.34 | -7.75 |

**The mechanism.** On the event lens (§26, §34) the invalidation exit beat the
cap because there was no target: the cap sat through thirty bars after the
reversal had paid. On the slot book the target already fires on the first move
-- a median hold of 15 bars on rsi -- and the slot refills; the median crossing
comes at 27. The swap lengthens the hold, halves the entries, and holds through
the part of the path the target would have banked; the long leg's mean per
trade rises (+39 to +62) and its mean per bar held falls. Exiting on whichever
fires first gives the shortest holds and the most entries, and on hist_L the
churn's cost (17.7 bp/bar) exceeds its gross (9.9). **The target is the exit
that matches the refill.** rsi under invalidation falls inside the rank
rotation (15 of 24); hist_L under invalidation stays above both nulls -- a real
book, worse than the target.

**Rules:**

1. **On a refilled slot book, an exit that fires later than the target only
   delays a refill the book wanted, and one that fires earlier adds a round
   trip.** D295's closure of the exit family is reinstated for the slot book
   with its mechanism; D345's amendment stands for the event book.
2. **An exit finding, like a selection finding, belongs to its construction**
   (§29, §33). The event lens and the slot book have now disagreed on
   selection, on both sides, and on exits.

## 37. The two candidate books blend to a higher Sharpe than either: the covariance is real and the arithmetic is exact

**From D356, 2026-09-06.** Pre-registered; four of six, the load-bearing one
held.

| PUB, bp/bar | gross | cost | net | vol | net Sharpe | max DD (net) |
|---|--:|--:|--:|--:|--:|--:|
| rsi k=40 | 12.70 | 7.56 | +5.14 | 305 | 0.268 | 10,471 |
| hist_L k=40 | 26.73 | 14.31 | +12.42 | 491 | 0.401 | 23,208 |
| **blend 50/50** | 19.71 | 10.93 | **+8.78** | 315 | **0.442** | 15,004 |

The 50/50 capital blend, each book at its own cost per bar, on a correlation of
the gross series of **+0.21**: net Sharpe 0.442 against 0.268 and 0.401, above
100 of 100 paired time rotations (p95 -0.45) and 24 of 24 paired rank
rotations. The worst 1% of bars overlap on two dates; the worst 1% of trades
share one name; **the two books hold the same name on the same side on 46% of
bars** and still correlate at 0.21 -- the diversification is in timing, not in
names. The drawdown sits between the parents' (capital blending halves hist_L's
left tail, it does not remove it). The arithmetic prediction from the parents'
net, vol and correlation reproduces the realised Sharpe to four decimals,
because a linear blend's Sharpe IS that arithmetic; the pre-registered
prediction that the blend would beat it was an identity and is recorded as an
error.

**Rules:**

1. **A portfolio of two books that each clear both nulls is a Sharpe lever
   with no new look**; the only prediction worth making about it is the
   correlation, and 0.21 between two reversal selectors on the same universe
   is the number to remember.
2. **The blend is the construction the holdout read is spent on** (D357), with
   both parents reported beside; nothing is admitted until that read.

## 38. A cross-sectional trigger on a wide universe is always on: the flat-by-default sleeve has to be gated in time, and its hedged alpha is half its own round trip

**From D358, 2026-09-06.** Pre-registered; four of eight, the load-bearing one
failed. Six cells: `rev_5` and `hist_L` entering the bottom 2%, 5% and 10%,
every event long at the next open, no slot cap, hedged by the floored market,
scored on the deployed base (hedged return per bar over open positions).

| cap exit, deployed base, PUB | exposure | open | entries/yr | gross | cost | net | net PB | per trade |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `rev_5` 2% | **100%** | 120 | 762 | +1.85 | 3.78 | −1.93 | −0.22 | +78 |
| `rev_5` 10% | 100% | 345 | 2,191 | +1.11 | 3.12 | −2.01 | −0.17 | +43 |
| `hist_L` 2% | 100% | 58 | 370 | +2.89 | 3.98 | −1.09 | **+0.70** | +123 |
| `hist_L` 10% | 100% | 200 | 1,271 | +1.46 | 3.20 | −1.73 | +0.10 | +60 |

**The arithmetic.** A fresh entry into the bottom 2% of ~1,000 eligible names
fires 5.2 times a bar; entries per bar × hold = open positions, so a 40-bar
hold is 120 open on the average bar and never zero. To be flat half the time
the product would have to be 0.7 — five entries a year — which is not a
signal. Under the 7-bar invalidation exit the book still holds 30 names on
every bar. **Rarity in the cross-section says which names; it cannot say
when.** Flatness has to come from a time-series condition, and in a
multi-strategy book that condition is the allocator's; the sleeve's series
tells it what the trigger earns while on.

**What it earns while on.** The hedged alpha is +1.1 to +2.9 bp/bar on the
deployed base — the trigger's per-trade mean spread over its hold — against the
held names' own round trip of 1.6 to 2.0 bp/bar at that turnover. The unhedged
series is +5.8 to +7.6 gross: **about 70% of a long-only sleeve's gross is the
floored market**, and the hedged Sharpe is below the unhedged on every cell
because what the hedge removes paid over this span. Per trade the trigger is a
post-2019 result: −26 bp in era 1 and +127 in era 2 at 2%.

**The trigger selects wide names.** Held half-spread 30–38 bp a side under PUB
(the names have just fallen hard). A random same-day same-`rsi`-bucket name
earns less gross (p95 +1.19 against +1.85), less per trade (+50 against +78)
and a lower Sharpe, and holds cheaper names: on net PUB alone the two are
inside each other's p95 at 2% and 5%. The cost line decides, and D336's quoted
spreads decide the cost line.

**The cost convention on a hedged single name, stated.** D345's `costed_event`
and the slot books' `G22.costed` charge each entry a *paired* round trip — four
crossings at the held names' median half-spread — which on a hedged single
name prices the market hedge at the name's spread. At the names' own round
trip (two crossings, the per-trade `2c`) the deployed cost halves and `hist_L`
2% is +0.90 PUB; the other five stay at or below zero. Both lines are printed
from D358 on.

**Rules:**

1. **A cross-sectional trigger on a wide universe is always on.** Any
   "flat-by-default" construction must name its time-series gate and test
   the gate with its own null (rotate the gate, keep the trigger).
2. **Compute a pre-registered exposure from the record before predicting it**:
   entries per bar × hold. D350's file already held the number.
3. **A long-only sleeve's gross is mostly the market's.** Report hedged and
   unhedged side by side and let the allocator size the beta; the sleeve's
   claim is the hedged line.
4. **State which round trip the cost line charges** — the pair's or the
   name's — whenever a single name is hedged by something cheaper than itself.

## 39. On the floored universe the short side has no drifting pool: the loser decile rises, and every short since D335 has been timing inside a pool that rises

**From D359, 2026-09-06.** Pre-registered; two of nine, the premise failed.

The record's short signals fail one way: the names they pick rise at random
times (§30, §33). D359 reasoned the fix — short inside a pool that drifts
*down* ex ante, the bottom decile of 12-month momentum, on a fresh `rev_5`
spike, hedged, held ten bars — and measured the pool before timing anything
in it.

| Stage 0, hedged next-bar drift, bp/bar | span | era 1 | era 2 | down-years |
|---|--:|--:|--:|--:|
| bottom momentum decile | **+0.64** | −2.36 | +2.09 | −2.88 |
| top momentum decile | +3.85 | +1.64 | +4.92 | +4.40 |

**The loser decile drifts up on this universe.** The floor (D339, D343) admits
only names above $5 with a passing dollar-volume window; the losers whose
continued fall the momentum literature measures leave the universe as they
fall, and what remains of the decile bounces. The timing inside it — the
primary cell, 8,085 trades — is +8.9 a trade, inside A′ (p95 +21.7), inside
B, inside the cohort-matched B_c (p95 +9.3: a random same-day name from the
same decile does as well) and inside random direction; three names are half
its P&L, the top trade DBI in March 2020 at 12%. The complement earns +4.8,
the wider cohort earns more than the narrower, HTB is 0.1% (the borrow rule
keys on the F0 window and a $5 close, and losers above $5 are not flagged).
It earned only where the cohort fell: era 1 +27, down-years +45 a trade —
and 2c under PUB is 91 bp on names 45 bp a side wide.

**The mirror, beside and not read.** A fresh dip in a 12-month *winner*,
entered long: +68.6 a trade at cap 10 (7,290 trades, t 5.9), +160.5 at cap 40
(3,932, t 5.1), **+82.9 net PUB** at cap 40. No null was run on it; it is an
observation until it is pre-registered.

**Rules:**

1. **A pool is a property of the universe under its floor.** The literature's
   drifting losers are unfloored; the programme's universe removes them. Any
   short here is timing inside a pool that rises, and the record has now shown
   that on 139 single-score events (§33) and one reasoned conjunction.
2. **The short side's value is regime-conditional**: it exists where the loser
   cohort falls (era 1, the down-years), which is the allocator's gate, not a
   signal's.
3. **Measure the pool before timing inside it** — Stage 0 turned "timing
   exists, cost eats it" into "the pool is not there", which is a different
   next study.
4. **The winners' dip is the next long to pre-register**, with nulls, before
   any number from it is quoted as a finding.

## 40. A tape-identified news day reverses, in both directions: the short side has no tape signal on the floored universe

**From D360, 2026-09-06.** Pre-registered; zero of nine, the check held.

The last kind of short the tape can express: an event in an ordinary name. A
gap in the bottom 2% of the day on top-decile relative volume, in a name still
above the floor after the gap, shorted at the next open, hedged, held ten
bars — the post-announcement drift read off the tape.

| the NAME's hedged forward return, bp per event | 10 bars | 20 bars | 10, down-years | 20, down-years |
|---|--:|--:|--:|--:|
| after a volume gap down (23,332 events) | −1.6 | **+7.0** | **+16.8** | **+37.7** |
| after a no-volume gap down (12,681) | +13.4 | +33.4 | +3.8 | +15.8 |
| the same names, random eligible days | −7.3 | −26.0 | −7.0 | −26.3 |

**The gapped name bounces against its own baseline** by 6 bp at ten bars and 33
at twenty, hardest in crashes; the gap *up* on volume reverses as well (the
mirror, long, −15 a trade on every cell, t −2 to −4). The short is −0.4 a trade
on 20,059, inside A′ (p95 +14.4), inside the same-day control and inside random
direction; no cell, exit or arm is above any control. The names are what was
argued — $35, 31 bp a side under PUB, 97% general collateral — and there is
nothing to earn in them. `rev_5`'s own bottom-decile long earns 6.75 bp less
on entries that arrived by a volume gap, so the gap is a slightly worse *long*
entry, not a short.

**Three constructions, one universe, one answer.** Levels select the wide
names whose drift is smaller than their cost (§33); loser rallies sit inside a
pool that rises (§39); news gaps reverse (this). Every short the tape can
express has been timing inside names that rise or bounce.

**Rules:**

1. **No unconditional tape short has cleared its controls on the floored
   universe** — levels (§33), loser rallies (§39), news gaps (this). *Amended
   the same day at the principal's ruling:* this is a statement of what was
   tested, not a closure; the avenue is the principal's to close. Untested
   and queued: the regime gate on the existing triggers (the loser cohort
   falls in era 1 and the down-years, §39) and the gap-up fade under its own
   controls (D361). **The criterion for a signal is a positive gross mean per
   trade above the nulls; cost is tuned afterwards.**
2. **A sharp move bounces, gap or no gap.** The long side's rule (§29, §34,
   §38) covers tape-identified news days; an argued exemption must be tested
   as the premise before the timing is read (STACK §7 item 30).
3. **On clustered events the same-day name control runs out of pool** (21%
   kept here); report the shortfall and let A′ and C carry the verdict.

## 41. A negative trailing market return forecasts a rebound, not a fall; and the gap-up fade with the market below its 200-day mean is the first short above every control

**From D361, 2026-09-06.** Pre-registered; two of eight, the premise and the
load-bearing prediction failed, a non-primary cell passed every control.

**The regime, as a state.** Gate on = the floored market's 63-bar compounded
return below zero (28.5% of bars, 98 episodes, median run 3 bars).

| hedged forward-20 return, bp | gate on | gate off |
|---|--:|--:|
| loser cohort (bottom decile of 12-month momentum), per name-bar | **+96.2** | −15.9 |
| the floored market itself | +188 | +80 |

Block correlation of the gate's level with the cohort's forward drift −0.23
on 159 non-overlapping 20-bar blocks; shuffled |r| p95 0.16. **The gate
forecasts, and what it forecasts is a rebound.** D359's era and down-year
splits were averages over both halves of drawdowns; the gated loser-rally
short is −4.5 a trade inside every control (+22.5 with the gate off), and by
episode it is +47,206 bp in the second half of 2015 and −44,591 in the first
quarter of 2016: it pays while the market falls and gives it back when the
market turns, and the gate is on for both.

**The cell that passed.** The gap-up fade — a gap in the top 2% of the day on
top-decile volume, shorted at the next open, held ten bars — with the market
**below its 200-day mean**:

| G2 × gap-up fade, cap 10 | n | gross | t | ROT p95 (200) | A′ p95 | B p95 | C p95 | net PB | net PUB | exposure |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| gated | 3,977 | **+42.3** | 2.5 | +36.0 | +25.8 | +37.7 | +25.2 | **+3.3** | −47.2 | 28% |
| gate off | 16,808 | +9.6 | 1.3 | | | | | | | |

A random gate of the same shape earns the fade +14.7 at the median (the
ungated number) and +36.0 at the p95; the gate is worth about +27 a trade
over chance and the trigger about +40 over its own names in the regime.
Era 2 +55, down-years +50; 2020 +208, 2021 +209, 2022 +46, 2023 −69. Held
names 42 bp a side under PUB, 19 under PB, general collateral on 96%. **It is
the first short in the record above all its nulls, it is the third cell of
four, the primary failed, and the p95 margins are 5 to 6 bp.**

**Rules:**

1. **A split by era or year is not a state.** A gate's premise is the block
   correlation of its level with the target over the next horizon, measured
   before the design is written (STACK §7 item 31).
2. **On this universe a negative trailing market return is a long-side
   object** — the loser cohort's +96 bp per 20 bars after it is unmeasured
   against controls and is listed, not read.
3. **The gap-up fade below the 200-day mean is a candidate for its own
   record**, multiplicity one, with its neighbours (the 100- and 150-bar
   means; the 5% gap) reported beside so a cell can be told from a region.
   Whether to write it is the principal's (R15).
4. **A gated event book is flat by default** (28 to 42% exposure here), which
   the ungated books never were (§38).

## 42. Two of five losing conditions found in the trade export are timing and beat a name-matched rotation of their own flags; the calm-market one takes over part of the gate's job

**From D362, 2026-09-06.** Pre-registered; eight of ten, the load-bearing one
held. Within-sample with nulls — the five conditions were selected from about
forty entry-time features on this same sample's trades (the D361 export) with
thresholds fixed from era 1 — and the holdout was not read.

| gated gap-up fade, cap 10, short | trades | gross | t | trim 1% | era 1 / era 2 | net PB / PUB |
|---|--:|--:|--:|--:|--:|--:|
| unfiltered (D361) | 3,977 | +42.3 | 2.5 | +35 | +19 / +55 | +3 / −47 |
| **sinks 1–2 removed, re-simulated** | 3,079 | **+61.7** | 3.2 | +57 | +59 / +63 | **+20 / −30** |
| all five removed | 1,868 | +83.6 | 3.9 | | +75 / +88 | +44 / 0 |
| every trade, size 0.5 per hit | 3,977 | +66.1 per unit capital | 3.9 | | +50 / +74 | +27 / −24 |

**The filter's own nulls.** Two-sink arm: above 200 removals of the same
number of events at random (p95 +55.7, p50 +41.8) and above 200 rotations of
each name's hit flags across its own events (p95 +54.3, p50 +43.4) — the
right events and the right times within a name. Five-sink arm: above the
random removal, inside the flag rotation (p95 +89.8) — high beta, a thin
volume node and overnight-driven volatility describe *names*, and rotating a
name's flags removes much the same trades. Re-simulation and row-drop agree
to 0.7 bp: concurrency carries nothing.

**The gate, after the filter.** Unfiltered, the 200-day gate was worth about
+27 a trade over a random gate of the same shape (§41). With the calm-market
sink on, the filtered cell is **inside the gate rotation's p95** (+79.3, p50
+30.6): a calm-market condition is a market state, and it does part of what
the gate did. Which of the two is the state variable is one cell the record
has not run — the trigger with the calm-market condition alone and no gate.

**Rules:**

1. **A filter found by screening a ledger needs two nulls, not one**: the
   same number of events removed at random (does it remove the right events)
   and each name's flags rotated in time (does it remove the right times,
   not the right names). D362's five-sink arm passes the first and fails the
   second.
2. **A filter on a market-level variable is a gate**, and it must be tested
   against the gate it sits behind; the two can explain the same trades.
3. **Sizing per hit is the safer form of a screened filter** — every trade
   kept, the highest t, two thirds of the gain — because it does not bet on
   a threshold.
4. **Screen numbers quoted in a pre-registration must be computed under the
   thresholds the record fixes** (STACK §7 item 32).

## 43. The entry-day spread does not move the fade's cost; charging each trade its own spread does; and the remaining cost question is what the auctions cost

**From D363, 2026-09-06.** Pre-registered; two of eight. D362's two-sink ledger
(3,079 trades, +61.7 gross), unchanged, costed four ways on the record's own
Corwin–Schultz; no quoted spread (D336 on hold); the holdout not read.

| per-trade line, bp | entry ½-spread median / mean | round trip | net | net at half crossing | net at auction |
|---|--:|--:|--:|--:|--:|
| PUB, trailing 21 bars | 42.9 / 51.7 | 107.7 | −48.7 | +3.0 | +54.7 |
| PB, the single pair | 17.9 / 60.4 | 125.1 | −66.1 | −5.7 | +54.7 |
| EW, three bars around entry | 34.6 / 52.4 | 105.1 | −46.1 | +4.3 | +54.7 |

**The estimator's day is not the lever.** On top-decile volume days the
spread is a fifth narrower at the median and unchanged at the mean; the
wide tail — where this ledger's gross is (the widest quintile +225 a trade
on names at $20 with a 94 bp half-spread; the middle three quintiles +13)
— does not compress. Three bp on the round trip.

**The convention is.** The record's per-trade `2c` has charged every trade
the ledger's median half-spread since D285. Charging each trade its own
spread at its own entry and exit bars costs this ledger 108 under PUB
against the median's 89, and 125 under PB against 39: PB's single-pair
estimate is zero on 43% of bars with a fat right tail, so its median is
small and its mean is the largest line. The net is −49 / −66, not D362's
−30 / +20.

**Execution is the open question.** If both sides cross the spread the fade
loses 46 to 66 a trade; if one side does, about zero; if neither does —
the kernel's fills are the opening and closing prints, which are auction
prints — +55 before impact. Impact is unmodelled. The number the programme
does not have is what an auction order in a name like these costs, and
daily bars cannot supply it.

> **Amended by §44, 2026-09-07.** This section originally read *"liquidity
> is not the constraint: at $25k a position the trade is 0.04% of the entry
> day's dollar volume at the median and under 1% on 99.8% of trades."* The
> whole-day figure is correct and it is **the wrong denominator for a fill
> that happens in an auction**. The opening minute is a median 1.44% of the
> day, so the same $25k order is **2.5% of it**, and 4.2% in the widest
> quintile that carries the edge. The clause is withdrawn; the three bounds
> stand.

**Sizing does not rescue the net.** Inverse-cost sizing halves the gross
(+30 per unit capital, t 1.8): the edge is not cheap. The in-sample U shape
is above 200 within-name permutations of its weights by 1.7 bp and is still
negative under every line at full crossing.

**Rules:**

1. **A per-trade net charges each trade its own spread at its own bars**,
   with the ledger-median line printed beside for comparability with the
   record. The median flatters any ledger whose gross is concentrated by
   spread (STACK §7 item 33).
2. **PB is not a per-trade charge.** The single-pair estimate is a
   distribution with a 43% zero mass and a fat tail; use it only through a
   window statistic.
3. **Cost engineering on this fade is order placement, not selection or
   estimation.** A spread ceiling removes the signal; the entry-day estimate
   moves 3 bp; crossing against the auction is 100 bp. That needs quoted
   spreads for the level (D336) and fills or intraday quotes for the
   auction, and it is the principal's to pursue. *(The "liquidity is not the
   constraint" clause that stood here is withdrawn — see §44.)*

## 44. The opening minute is 1.4% of the day and the closing minute 7.9%, so the fade's order is 2.5% of the auction it actually fills in

**From D364, 2026-09-07.** A measurement, not a hypothesis test: no predictions
were registered. One-minute bars with extended hours for a stratified sample of
the fade's own trades (100 drawn, 20 per PUB half-spread quintile, **78 complete
on all four measures**), reading the 09:30 bar (opening auction plus a minute of
continuous trade) and the 16:00 bar (closing auction plus a minute). **Both are
upper bounds on the auction's own size, so every figure below is a lower bound
on the truth.**

| minute / whole-day dollar volume | p25 | median | p75 | p90 |
|---|--:|--:|--:|--:|
| 09:30 minute | 0.88% | **1.44%** | 2.36% | 4.09% |
| 16:00 minute | 2.73% | **7.85%** | 13.58% | 28.44% |

| at $25k a position, median participation | entry | exit |
|---|--:|--:|
| whole day (§43's denominator) | 0.024% | 0.053% |
| **the minute the fill happens in** | **2.494%** | **0.645%** |

Two thirds of entries are above 1% of the opening minute at $25k and a third
above 5%; at $50k it is 81% and 50%. **And the widest PUB quintile — the one
carrying the whole edge (+225 gross a trade against +13 for the middle three,
§43) — is the thinnest**: 4.20% median participation, 87% above 1%, 47% above
5%, on an opening minute of $596k against $1.3M in the tightest quintile.

**What it does not say.** Participation is not slippage. This record has no
fills and makes no claim about what a print moves by. What it removes is the
premise: §43's +55 is the arithmetic of a fill *at the print with no impact*,
and "0.04% of the day" was the argument that such a fill was plausible. At
2.5% of the opening minute it is not, so **the auction cost is unmeasured and
is not zero**.

**What the measurement costs itself**, all stated: the endpoint carries a
median 82% of the consolidated day (86% on complete sessions), so participation
is overstated by about 1.22× — which runs the same way through both
denominators and does not touch the ratio; the extreme share-ratio outliers are
the split frame (`dollar / share` recovers the factor: ORLY 14.86, MSTR 10.2)
and the assertion uses the split-invariant dollar ratio; the intraday endpoint
refuses delisted tickers so 22.3% of the arm is unreachable, though the tilt is
small (gross +61.31 kept against +59.81 excluded, half-spread 51.95 against
50.81); 17 of 97 exit sessions have no 16:00 bar and are dropped and named,
never replaced by 15:59.

**Rules:**

1. **Measure participation against the bar the fill happens in**, not the day.
   A whole-day denominator understates an auction fill by 69× at the open and
   13× at the close on this universe.
2. **An execution bound that assumes a fill at the print must state its
   participation** at that print, or it is arithmetic wearing a claim.
3. **Where the edge is, the auction is thinnest** — the widest-spread names
   have the smallest opening minute. Spread and depth are the same problem
   here, and a spread ceiling that removes the signal (§43) removes the depth
   problem with it.
4. **The next number is a fill, not another estimate.**

## 45. The cost problem is a turnover problem: the same momentum signal loses 1.5% a year refreshed daily and earns 6.5% behind a rank buffer

**From D365, 2026-09-07.** Pre-registered; five of eight, the load-bearing one held. A
within-sample confirmation — the cell came from an eleven-combination screen on the same
fixture — with nulls, in the shape of §42. Cross-sectional momentum is the most published
anomaly there is; what is new to *this record* is the shape.

**The construction.** Buy the top 5% of twelve-month momentum, hold until a name falls out
of the top 20%, equal-weight, hedged, next-open fill. No stop, no target, no clock, no slot
cap. About 53 names, 99-bar holds, 1% of the book replaced a day.

| primary cell 95/80, open fill | gross | cost | net PUB | net PB | Sharpe | %/yr |
|---|--:|--:|--:|--:|--:|--:|
| behind the buffer | +3.37 | 0.77 | **+2.59** | +3.05 | 0.417 | +6.5 |
| the same signal, refreshed daily | +3.84 | 4.43 | **−0.59** | +2.03 | −0.109 | −1.5 |

**That is the finding.** Turnover falls from 5.93% a day to 1.01%, so the toll falls sixfold
while the gross falls a tenth. The jitter across the rank boundary was noise, not
information. It is the same arithmetic as §43 read the other way: the toll is paid per round
trip and the edge accrues per bar, so the shape that survives is broad, slow and reluctant
to trade. A corollary: the next-open fill costs this book 1.8% of its gross, where it cost
the event books 13.8 bp/bar — **a slow book is nearly immune to the convention that
destroyed the fast ones.**

**It clears every null**: above the p95 of 24 rank rotations (−2.75, and on gross +0.72
against +3.37), 200 per-name time rotations (+1.78), random direction (+2.85), and a
grid-max null under shared offsets (p = 0.040).

**It is not size and not beta.** Against a dollar-volume-decile-matched hedge that excludes
the name itself, the top-decile drift is +3.97 against +3.87 — **103% survives**. The
identical buffer construction ranked on volume earns −0.99 gross, and on the volume *level*
−0.10. Beta is 1.15 and beta-adjusting leaves the drift unchanged.

**What it costs to say so honestly.** The two-factor intercept is +2.856 bp/bar at **t =
1.74**, missing conventional significance: a Sharpe of 0.42 over twelve years cannot reach
it. Era 1 is −0.38 and era 2 is +3.99, so this is a six-year result with a seven-year null
attached. Nine of thirteen years are positive. And **thirteen names are half the P&L of 709
that traded** — holding 53 names produced the same concentration as this record's two-name
books. The median trade *loses* 141 bp while the mean makes 335, with skew +3.85; the
symmetric trim is +216 and the ex-top-1% mean is +138, still 1.4× the round trip. Top trade
GME, entered November 2020 at $11.49, held 305 bars, 8.6% of the P&L — the buffer working as
designed, on the most anomalous episode in the sample.

**Rules:**

1. **Attack turnover before attacking the signal.** When gross is small against a fixed
   round trip, hysteresis on the selection boundary is worth more than any improvement to
   the selection rule. Enter on one rank, exit on a lower one.
2. **A programme's construction conventions can hide a result.** D300 fixed the book at two
   names per side for a *spread* construction and it propagated into everything after; a
   diversified premium cannot be seen through a two-name window. When importing a
   convention, ask which construction earned it (STACK §7 item 16).
3. **Breadth of holdings is not breadth of outcome.** Fifty-three names produced thirteen
   names to half the P&L. Report the concentration of the P&L, never the position count.
4. **Permutation nulls and a time-series t ask different questions.** This cell clears every
   null and has a t of 1.74. Report both; the flattering one alone is not a result.

## 46. A gate found by search clears its own rotation null, and half of what it buys is being out of the market rather than being out at the right times

**From D366, 2026-09-07.** Pre-registered; six of eight, the load-bearing one held — and so
did the one written *against* the construction. Five nulls. Still within sample: the
construction is the endpoint of roughly a hundred constructions searched on this one fixture
(D365's eleven plus this session's eighty-nine), and this record exists to price that search.

**The construction.** D365's momentum buffer — buy the top 5% of twelve-month momentum, hold
until a name falls out of the top 20%, equal-weight, next-open fill — plus a nine-condition
market gate that must be open to *enter* but never forces a liquidation, a 252-bar cap on the
holding period, and a short of the eligible universe **dollar-volume weighted**, with the
hedge's own borrow and rebalancing charged. The gate is shut on 90.8% of bars.

| | gross | cost | net PUB | Sharpe | %/yr | maxDD | era 1 | era 2 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| gated, capped | +9.65 | 1.56 | **+8.09** | 0.887 | +20.4 | 3,158 | +0.46 | +12.10 |
| ungated (D365's cell) | +3.37 | 0.77 | +2.59 | 0.417 | +6.5 | — | — | — |

**The trigger is real and the nulls are decisive about it.** The rank rotation's *entire*
distribution is negative — its best of 24 shifts is −0.24 against the observed +8.09 — and the
per-name time rotation centres on zero with a p95 of +1.98. Neither comes close.

**The gate is a different story, and it is the finding.** Rotate the gate in time, preserving
its on-share and its circular run structure exactly and leaving the trigger untouched, and it
still earns **+4.10 bp/bar at the median** — half the observed. The real gate clears that
null's p95 (+8.09 against +7.02), so it is not nothing; but two of two hundred randomly-timed
gates beat it outright. **Roughly half of what a market-timing gate appears to buy here is not
timing at all: it is the mechanical effect of holding a concentrated momentum book only 9% of
the time, in runs of that shape.**

**And the margin over a random gate is ten names.** Removing the top ten names of 515 from the
eligible universe and rebuilding the book — so the freed slot refills — leaves **+4.60**,
which *is* the random gate's median. The single largest contributor is **GME, entered
2020-11-16 at $12.06 five weeks before the squeeze and held to the 252-bar cap for +55,259 bp,
11.7% of all P&L**. Twelve names of 515 reach half the P&L, against a pre-registered ≥15.

**The typical trade loses.** Median −28.3 bp against a mean of +477.5, a 48.6% win rate,
skew +5.3, excess kurtosis +62 — the mirror of §33's tell, with the *right* tail carrying the
book. Trimming 1% from both tails leaves +342.8 against a 96.8 bp round trip, so the edge is
not one or two trades even though the concentration is real.

**The searched cap has no plateau.** The 252-bar cap beats no cap (Sharpe 0.887 vs 0.678), but
moving it ten bars either way swings Sharpe from 0.735 to 0.922 — a range comparable to the
whole gate-rotation null — and the frozen value is not even the local maximum (242 is). This is
not driven by the GME trade: the sweep has the same shape with that name removed.

**What it means.**

1. **A gate needs a rotation null, and it needs one because a gate does two things at once.**
   It picks *when* to be in, and it decides *how much* to be in at all. Only the first is a
   forecast; the second is exposure reduction wearing a forecast's clothes. Rotating the gate
   in time holds the second fixed and prices the first, and here the first is worth about half
   the headline. A matched-count control is not enough — a gate's nuisance is its on-share
   **and** its run structure (R7).
2. **Report a null's rank, not just "above p95".** Clearing a control by two draws in two
   hundred and clearing it by all two hundred are different results, and "above p95" prints
   the same for both. Rank separates them.
3. **A ladder null whose observed is the ladder's own maximum tests nothing.** Report the
   ladder's shape instead. Here it is monotone across all seven steps, which is a pattern to
   be suspicious of rather than reassured by.
4. **A swept parameter's neighbours are part of its result.** A single-point optimum with no
   plateau is a draw from a jagged surface, not the value of a constant, and reporting it
   without the neighbours overstates it.

## 47. Six of a nine-condition gate were logically implied by the seventh, and an entry gate does not reduce exposure

**From D367, 2026-09-07.** Pre-registered; five of eight, one load-bearing prediction held and
one failed. Forty-six gates — nine single conditions, all thirty-six pairs, the combined gate —
each against its own time rotation, plus a shared-offset control pricing the best of forty-six.

**Each gate is scored on its TIMING PREMIUM — net less the median of its OWN rotation** — because
the nine conditions have on-shares from 9.5% to 89.1% and raw net cannot compare them. A gate does
two things at once: it chooses *when* to hold and it rations *how often* holding may begin. Only
the first is a forecast, and only the rotation separates them.

**The redundancy is the finding.** D366's gate was the conjunction of nine conditions. Six of them
change the result *identically* — to the last decimal — because they are implied by the ninth:

| gate | open% | net | premium |
|---|--:|--:|--:|
| C9 alone, index at a 252-bar high | 9.5% | +6.93 | +2.91 |
| C9 + any of the six trend conditions | 9.5% | **+6.93** | **+2.91** |
| C9 + index 12-month momentum > 0 | 9.3% | +8.06 | +4.14 |
| all nine | 9.2% | +8.09 | +4.15 |

An index at a 252-bar high is *necessarily* above its 200- and 50-day means, has positive 63- and
21-day returns, is not in a crash state, and has broad participation. **The nine-condition gate is
one condition plus one more, and the whole difference between them is ten gate-open bars and about
twenty trades.** The added condition has *negative* standalone timing content — 113 of 200 randomly
timed versions of it beat the real one.

**Multiplicity splits the two.** Against a shared-offset best-of-46 null (p95 +2.96), the full gate
clears at +4.15 with 0 of 200 draws beating it; the one-condition gate at +2.91 falls 0.05 short.
**The cheaper construction is weaker in evidence, and the same ten bars decide both verdicts.**

**An entry gate does not reduce exposure — the correction this study forced.** The gate is shut on
90.8% of bars, and the book is invested **91.6%** of them, holding 22.5 names on average, because
the gate blocks *entry* only and positions run to the 252-bar cap. Every earlier description of
this construction as flat most of the time was wrong. Decomposed properly: ungated **+1.85** → a
randomly timed gate **+4.10** → the real gate **+8.09**; a third is entry rationing any gate of that
shape delivers, two thirds is this gate's timing.

**And the gate's edge is the same thing as the P&L concentration.** Removing the ten best names —
a look-ahead diagnostic, with the universe genuinely re-ranked — leaves a book that still beats its
rank rotation 0-for-24 and its time rotation 0-for-200, but **fails its gate rotation** (+3.91
against a p95 of +4.47, 30 of 200 draws beating it). The real gate lost 4.18 bp/bar when those names
went; a random gate lost 2.45. **43% of the gate's timing value lived in ten names.** The trigger
survives; the overlay does not.

**Concentration is a property of the signal, not of those names.** The reduced universe's own new
top ten take **45% of its P&L — identical to the full universe's 45%**, 12 names to half the P&L
against 12 before. It cannot be diversified away by removing whoever happened to win.

**What it means.**

1. **Check a conjunction for logical implication before searching over it.** Six conditions here
   were not weak, they were *entailed*; a ladder that adds them looks monotone and informative and
   is neither. One line of set algebra — is this gate a subset of that one? — would have shown it
   before ninety constructions were searched.
2. **Score a gate on its own rotation, never on raw net.** On-share is a nuisance parameter and
   conditions differ on it by a factor of nine here.
3. **A gate that blocks entry is not a flatness mechanism.** If flatness is the goal, the exit has
   to be gated too; entry gating changes which trades are taken, not how long capital is deployed.
4. **Concentration and timing can be one finding rather than two.** When both point at the same
   names, fixing either by diversification is unavailable.

## 48. A 200-draw rotation null cannot resolve a 0.1 bp/bar margin, and three studies decided verdicts on exactly that

**From D368, 2026-09-07.** Pre-registered; one of eight, the load-bearing one failed and the
one written *against* the construction failed too. One parameter swept: D367's surviving gate
condition — the index at a 252-bar high — relaxed to *within d% of the high*, d = 0 … 10.

**Neither of the two outcomes the record was written to distinguish.** Relaxing by half a percent
nearly doubles the on-share (9.5% → 18.1%) and keeps **83%** of the timing premium, so the gate is
**not** a knife-edge at the high. But only d = 0 clears its own rotation, and the premium curve
wanders rather than decaying: **+3.11 → +2.58 → +1.91 → +2.33 → +2.39 → +0.08**.

| d% | 0 | 0.5 | 1 | 2 | 5 | 10 |
|---|--:|--:|--:|--:|--:|--:|
| on-share | 9.5 | 18.1 | 25.5 | 38.1 | 60.3 | 76.1 |
| net | +6.95 | +6.01 | +5.30 | +5.46 | +5.04 | +2.29 |
| clears own p95 | **YES** | no | no | no | no | no |

**THE METHODOLOGICAL FINDING, which matters more than the sweep.** The same gate, the same 200-draw
rotation design, two independent runs differing only in a **dead** parameter (net moves 0.02):

| | net | rot p50 | rot p95 | margin |
|---|--:|--:|--:|--:|
| D367's C9 | +6.93 | +4.02 | **+6.43** | clears by 0.50 |
| D368's C9 | +6.95 | +3.84 | **+6.83** | clears by 0.12 |

**The null's p95 moved 0.40 bp/bar purely from redrawing 200 rotations** — and D366→D367 showed the
same gate's p95 move from +7.02 to +6.42 with the draws beating it going 2 → 0. Meanwhile the
verdicts these studies turned on were decided by margins of **0.05 to 0.56**: C9 clearing its
rotation (0.12), C9 *failing* the best-of-46 control (0.05), the reduced universe *failing* its gate
rotation (0.56). **Every one of those sits inside the null statistic's own run-to-run spread.**

**Capacity closes negatively.** No relaxation with an on-share of 20% or more clears its rotation —
not at 26%, 38%, 60% or 76%. The effect is demonstrable only while the gate is nearly shut.

**And the discarded conditions are not useful at any d where they are not redundant.** At d = 0 the
eight others add +1.13 while being logically entailed (§47); at d = 5, where they genuinely bind and
exclude a fifth of the sample, they add **−0.04**.

**What it means.**

1. **Report a null's p95 with its own sampling error, or run enough draws that it has none worth
   reporting.** 200 draws is fine for a verdict decided by 3 bp/bar and useless for one decided by
   0.1. This programme has been using one draw count for both.
2. **A verdict inside the null's own spread is not a verdict.** "Clears p95" and "fails p95" printed
   identically for margins of 0.05 and for margins of 3.0; the rank and the draws-beating count
   (§46) help, but only the draw count fixes it.
3. **Three sweeps on this fixture have produced three wandering surfaces** — the 252-bar cap, the
   ten-bar C4 contribution, and now the relaxation curve. A fourth sweep would produce a fourth.
   Sweeping is no longer informative here; precision and out-of-sample are.
4. **A relaxation sweep is the right test for "is this a point effect?"** and it answered cleanly in
   the construction's favour even as everything else failed. Keep the instrument.

## 49. At 10,000 draws the ranking clears its null by 164 standard errors and the gate by 3.2, and one verdict is undecidable at any draw count

**From D369, 2026-09-07.** Pre-registered; seven of eight. **These verdicts supersede the 200-draw ones in
D366, D367 and D368**, as committed before any number was seen. Seven arms at 10,000 draws each,
on the two gates that remained live — not on D368's sweep settings, which nobody plans to trade.

**§48's precision problem is fixed and quantified.** The rotation p95's own bootstrap standard error is
**0.301 bp/bar at 200 draws** and **0.020–0.056 at 10,000**. D368's two independent 200-draw runs of
the same gate differed by 0.40 — exactly what a 0.30 SE predicts.

**THE FINDING IS THE GAP BETWEEN TWO KINDS OF EVIDENCE.** Same construction, same draws:

| | margin over its null's p95, in SEs of that p95 | draws beating it |
|---|--:|--:|
| the trigger, per-name time rotation | **143 – 164** | **0 of 10,000** |
| the nine-condition gate, time-rotated | 32.9 | 62 of 10,000 |
| the one-condition gate, time-rotated | **3.2** | 439 of 10,000 |
| the one-condition gate vs best-of-ten | **−1.0 — UNRESOLVED** | 522 of 10,000 |

**Cross-sectional 12-month momentum on this floored universe is established and needs no further null
work.** Everything unresolved is the market-timing overlay.

**AND ONE VERDICT CANNOT BE REACHED BY ADDING DRAWS.** The one-condition gate clears its own rotation
but ties a best-of-ten multiplicity control at −0.034 with an SE of 0.035. **The margin and the
standard error are the same size — so this is not sampling noise that precision removes; the effect
and the multiplicity penalty are the same magnitude.** A gate chosen as the best of ten conditions
performs exactly like the best of ten conditions at random timing. D367's "it fails by 0.05" was
noise and is superseded by "undecidable".

**What it means.**

1. **Report a margin in standard errors of the null statistic, and create the UNRESOLVED category
   BEFORE seeing numbers.** Written after the fact it is special pleading; written before, it caught
   exactly the case it was built for. "Clears p95" printed identically for a 164-SE result and a
   1-SE one.
2. **Precision cannot rescue a comparison whose effect equals its multiplicity penalty.** Ask what
   draw count would settle a margin before spending it: if the SE needed is smaller than the effect,
   no count is enough and the question has to change instead.
3. **Distinguish what is established from what is not, and stop re-proving the established part.**
   Four studies re-ran the trigger's null; it was never in doubt at any draw count. The draws belonged
   on the gate.
4. **A null kernel can be made 2.7x faster and stay BIT-IDENTICAL** — hoist the invariant, skip what
   nothing reads, index sparsely into a pre-zeroed buffer *of the same shape* so the dense sum reduces
   the same values in the same order. Summing only the held entries reorders a float sum: pairwise
   summation groups by index block, and interspersed zeros change how the non-zeros are parenthesised.

## 50. Removing a book's best names tests nothing unless every null draw loses ITS OWN best names — the verdict reverses when it does

**From D370, 2026-09-07.** Pre-registered; every prediction confirmed, including the one written
*against* the earlier conclusion. **§47's claim that "the trigger survives and the overlay does not"
is RETRACTED.**

D367 removed the ten names the observed book earned most from and compared what remained against
rotated gates that never produced those names. Made symmetric — **each draw losing its own ten** —
the verdict flips:

| test | draws | p50 | p95 | observed | margin | in SE | verdict |
|---|--:|--:|--:|--:|--:|--:|---|
| **symmetric**, each draw loses its own ten | 2,000 | +0.679 | +3.617 | **+4.219** | **+0.602** | **+10.3** | **CLEARS** |
| asymmetric, every draw loses the same ten | 10,000 | +1.562 | +4.230 | +3.919 | −0.311 | −15.8 | FAILS |

**Two separate defects, both measured.**

1. **The hedge was shorting names the book could not trade — worth +0.300 bp/bar.** D367 and D369
   rebuilt the *ranking* on the reduced universe but left the dollar-volume hedge spanning the full
   one. A third of the margin by which the book was judged to fail was that inconsistency.
2. **The null was spared the penalty the observed book paid.** Removing one book's winners takes its
   whole tail and only part of every other book's. Once each draw loses its own, the null's p95 falls
   from +4.230 to +3.617 and its median from +1.562 to +0.679.

The sets genuinely differ — a draw's own ten overlaps the observed book's on a **median of 5 of 10**
— so the earlier test was not absurd, merely unfair. The gate's premium survives at **83% retained**
(+3.54 against the full universe's +4.288), not the 57% §47 reported.

**What it means.**

1. **A control set selected from the treatment's own outcome is not a control.** Ask, before running:
   *would this comparison be different if the null had produced this result?* If yes, the selection
   has to happen inside every draw.
2. **PRECISION CANNOT DETECT BIAS.** §49 ran this exact test at 10,000 draws and returned a confident,
   well-resolved, tightly-bounded, **wrong** answer at −15.8 standard errors. More draws make a biased
   estimator more precisely biased. Spend effort on whether the comparison is fair before spending it
   on how many draws it gets.
3. **When a reduced universe is tested, reduce everything the universe touches** — the ranking, the
   eligibility *and* the hedge. Leave the market index alone: the market still contains those names
   whether or not this book trades them, and reducing it per draw would make the gate a different
   object in every draw.
4. **Concentration and timing are separable after all.** Twelve names still reach half the P&L and a
   fresh top ten still takes 45% (§47 Q8, unaffected) — but the gate's *timing* does not depend on
   which ten they are.

## 51. The momentum book did not travel: on 803 unseen names its top five contribute 142% of P&L, and everything outside them loses money

**From D371, 2026-09-07. THE PROGRAMME'S FIRST HOLDOUT READ. Reads spent: 1.** Pre-registered with
twelve predictions committed before the fixture was touched — eight mine, four the principal's.
**Both constructions failed four of six hurdles and are RETIRED.**

| | in sample (1,573 names) | **holdout (803 names)** |
|---|--:|--:|
| net PUB bp/bar | +8.11 | **+3.19** |
| Sharpe | 0.887 | **0.344** |
| annualised | +20.4% | **+8.0%** |
| max drawdown | 3,158 bp | 6,234 bp |
| names to half the P&L | 12 of 515 | **2 of 255** |
| top 1 / 5 / 10 name share | 11 / 30 / 45% | **36 / 142 / 231%** |

**THE TOP-NAME SHARES ABOVE 100% ARE THE FINDING.** The top five names contribute 142% of total
P&L, so **everything outside them is net negative**; outside the top ten the remainder loses 131% of
what the book makes. One trade — CAR, entered 2021-04-19, held to the 252-bar cap for +19,325 bp —
is **30% of all P&L**. And the 1% trimmed mean per trade is **+63.9 against a 94.8 bp round trip**:
strip both tails and the average trade does not cover its own costs.

**BOTH NULLS FAIL, NOT JUST THE GATE.** I predicted in writing, twice, that the time rotation would
clear and only the gate rotation would fail — that the trigger travelled and the overlay did not.
It did not travel:

| null | p95 | p97.5 (the pre-registered bar) | observed | percentile | in sample |
|---|--:|--:|--:|--:|--:|
| A′ time rotation | +2.804 | +3.513 | +3.187 | **96.2nd** | 100th, 164 SE |
| GATE-ROT | +3.388 | +3.927 | +3.187 | **93.9th** | 99.4th, 32.9 SE |

The trigger clears the *conventional* p95 and fails only the Bonferroni p97.5 fixed in advance for
testing two constructions on one sample. It is **borderline, not intact**. The gate fails below even
the unadjusted bar.

**AND POOLING WITH THE TRAINING SET DOES NOT RESCUE IT.** The date-aligned 50/50 of the two books
returns Sharpe **0.716** against mining-alone's 0.911 — better than the holdout, worse than the
fixture it was selected on. The reason is that two universes sharing **zero names** over the same
days still correlate **+0.545**, both being long US-equity momentum: far too correlated for
diversification to offset a holdout mean less than half the mining mean.

**One surprise in the construction's favour:** era 1 was fine (+2.98 vs era 2's +3.31). The
in-sample era-1 weakness that no gate could fix did not reappear.

**What it means.**

1. **In-sample null strength does not forecast out-of-sample survival.** This construction cleared
   its time rotation at **164 standard errors with zero of 10,000 draws beating it** (§49), cleared
   a best-of-ten multiplicity control, and cleared a symmetric winner-removal test (§50). It still
   failed. Permutation nulls test whether a pattern is real *in the data you have*; they say nothing
   about whether it recurs.
2. **Report the top-name share, not just names-to-half.** "Two names to half the P&L" understates
   it; "the top five are 142% of P&L" says the rest of the book loses money, which is a different
   and worse fact.
3. **A trimmed mean below the round trip is disqualifying on its own.** It says the edge lives
   entirely in the tails, and tails are exactly what does not repeat.
4. **Pooling a failed holdout with its training set is not evidence and cannot be**, because the
   pooled mean is pinned between the two by arithmetic. Declare that arm as context *before* the
   read, or the temptation is available afterwards.

---

## 51. Every cross-sectional book is equal-weighted and nothing has ever been run against it: sizing was never chosen

**From [D372](decisions/D372-equal-weight-is-the-incumbent-sizing-and-the-hurdle.md), 2026-09-07.
PRE-REGISTRATION ONLY. No cell has been scored under any sizing scheme but the incumbent, and
D372's stage-0 diagnostic has not been run. This section records a verified property of the code
and a declared gap — it is NOT a result.**

The kernel sizes by equal weight within each leg, renormalised per bar
([`scripts/run_d306_width_exits.py:240`](../scripts/run_d306_width_exits.py)):

> the book is `mean(long) - mean(short)`, so a trade's weight at bar t is **`1/n_t` for its own
> leg, NOT `1/depth`** — the two differ whenever a delisting leaves the leg short of its slots.

`1/n_t` rather than `1/depth` is load-bearing on a dead-inclusive fixture (D252): a leg thinned by
a delisting must not silently hold cash at the dead name's weight. **That is the only sizing
decision this programme has ever made.** Every number in this file — every null, every cost
convention, every era split — was produced under equal weight, and no record selected it.

**The two lineages have never met.** Inverse-volatility sizing is built and swept in the
breakout/crypto work — D110's `InverseVolatilityWeight` brick, D118's swept target, D119's
risk-equalised benchmark — and has never been run on a single-name cross-sectional book.

**Why it is worth naming rather than assuming.** Equal weight ignores volatility, ignores
correlation entirely, ignores conviction (rank 1 and rank 20 take identical weight though the
score is continuous), and — the one specific to this programme — **ignores price, and therefore
cost. Cost in bp scales inversely with price (§ the D284 kill), so equal weight is unequal cost
drag**: the cheap names carry the heaviest bp burden for the same notional.

**And why the prior still favours it.** It has no parameters, so it cannot be overfit, needs no
multiplicity correction and no null of its own; a swept challenger needs all three. Estimation
error in a covariance matrix routinely exceeds the optimisation gain (DeMiguel, Garlappi and
Uppal 2009: `1/N` beat fourteen optimised models out of sample across seven datasets).

**The confound that makes this non-obvious.** Low price correlates with high realised volatility,
so inverse-vol sizing *partially re-implements the D339 floor* by shrinking the same names the
floor excludes. A win for vol sizing may be the floor arriving a second time under a new name.
D372 §5 forces a price-rank-only comparison to separate them.

**What is actually next, and it may end the question.** D372's stage 0 is a volatility-decile
split of contribution P&L on the existing census machinery — a diagnostic with no predictions.
D339's census already found `retrace_leg` taking **61.3% of its P&L from the 12.2% of trades
entered below $5** (+805 bp against +76). Those are the high-volatility names. If P&L is monotone
increasing in volatility decile, inverse-vol sizing is arithmetically guaranteed to remove most of
the book's earnings, nothing needs building, and **the books are harvesting a volatility premium
rather than exercising selection skill** — a different object, priced differently, with different
capacity. D210 ("nothing survives holding leg size constant") is the precedent for that outcome.

**The rule.** *An implicit default is not a decision, and it has never been tested.* Equal weight
was not chosen over alternatives; it is what the kernel happened to do. Anything that has never
been named cannot have been beaten, and the absence of a challenger is not evidence the incumbent
won.

---

## 52. The cohort was the strategy: three independent methods agree that ~80% of the winners'-dip edge is momentum-decile exposure, and the avenue is retired

**From [D373](decisions/D373-RESULT-the-winners-dip-is-the-retired-book-and-one-GME-trade.md),
[D376](decisions/D376-RESULT-two-unrelated-books-here-correlate-at-0.48-and-two-cohort-books-at-0.92.md)
and [D377](decisions/D377-RESULT-the-beta-hedge-is-adopted-and-it-fixes-seven-percent-of-the-problem.md),
2026-09-07. AVENUE RETIRED BY THE PRINCIPAL, 2026-09-08 (R15).**

> **CLOSED DEFINITIVELY BY THE PRINCIPAL, 2026-09-09 —
> [D401](decisions/D401-the-principal-closes-the-winners-dip-and-the-15m-structure-avenues.md).** The
> avenue was retired on 2026-09-08, **reopened narrowly** for
> [D378](decisions/D378-RESULT-the-entry-day-does-matter-and-it-survives-losing-its-best-trade.md),
> and its exit half was then closed by
> [D380](decisions/D380-RESULT-no-exit-overlay-beats-not-cutting-and-R7s-control-inherits-the-rule.md)
> and [D381](decisions/D381-RESULT-a-stop-is-a-late-trigger-and-the-median-mean-exchange-rate-is-fixed.md).
> **It is now shut in both directions and will not be reopened again.**
>
> **The entry-timing finding is NOT withdrawn and stands as truth**: D378's T1 passed at **+26.9 SE**
> and its largest-trade-removed gate at **+9.8 SE**. What is closed is the avenue, not the fact. The
> increment's deployability turns on cost — **D336's quoted-spread pull** — which is a separate,
> still-open item that this closure does not touch and whose answer does not reopen this.

The winners'-dip long entered a fresh `rev_5` dip inside the `mom_252_21` **top** decile. It posted
a gross **+160.55 bp per trade** over 3,932 trades, and the question was always what that number was
paying for.

**Three unrelated methods answered it the same way.**

| study | lens | measurement |
|---|---|---|
| **D373** | **return**, per trade | the same-day same-cohort swap `B_c` centres at **+126.54** of the observed **+160.55** — available to a *random* name drawn from the same decile on the same day |
| **D376** | **covariance**, per bar | two books sharing **nothing but cohort membership** — different names, different days, different timing — correlate at **ρ = +0.923** (p05 +0.916; 124,750 pairs from 500 books) |
| **D377** | **hedge** | subtracting the cohort's own equal-weight return collapses the gross mean to **+34.08** and the **median to −30.74**: with the cohort removed, the typical trade loses money |

**The three are not restatements of one another.** D373 asks what a random cohort name earns, D376
asks what two cohort books share, D377 asks what is left when the cohort is subtracted. Different
statistics, different nulls, different arithmetic.

### CORRECTION, 2026-09-08 — two of these measure the LEVEL, one measures CO-MOVEMENT, and the section's first heading over-claimed

*Raised by the principal, and the objection is right.*

**Correlation does not bound a difference in means.** Two series can correlate at ρ = 0.92 and have
very different average returns — ρ is computed after removing each series' mean and dividing by its
own volatility, so it is a statement about **shape**, not **level**. D376 therefore does **not**
measure "80% of anything".

| | what it actually establishes |
|---|---|
| **D373** (+126.54 of +160.55) | **LEVEL.** A random cohort name on the same day earns most of the return |
| **D377** (+160.55 → +34.08) | **LEVEL.** Removing the cohort's own return removes ~79% of the mean |
| **D376** (ρ = +0.923) | **CO-MOVEMENT ONLY.** Two cohort books rise and fall together; it says nothing about whether one earns more than the other |

**So the "~80%" rests on D373 and D377 — two measurements, not three.** D376 supports a different and
narrower claim: **cohort books cannot diversify one another**, because a portfolio of two of them
carries almost the risk of one. Both conclusions stand; they are not the same conclusion, and the
heading of this section states the level claim as though all three supported it. **They do not.**

**What this leaves open, explicitly:** ρ = 0.92 is fully compatible with one cohort book earning
materially more per trade than another. **Nothing here shows that entry and exit timing inside the
cohort cannot raise per-trade return.** See §52a.

**The dip timing survives as a real but marginal increment.** D373's H1 passed: +160.55 cleared
`B_c`'s p95 of +155.60. But the margin was **+4.95 bp**, and removing the single largest trade — GME
entered 2021-01-04 at $17.25, +40,029 bp, 6.34% of the ledger — takes the mean to +150.41, **below
that p95**. An increment one January-2021 squeeze can carry is not a signal.

**And it was the retired book.** D373's H7 measured ρ = **0.9346** against D365's momentum buffer,
which D371 retired out of sample. D376 then showed the *excess* over the cohort baseline is only
**+0.011** — so D373 was not unusually similar to D365, it was **about as similar as any two cohort
books are**, which is the same finding by a fourth route.

### The rule

> **A construction that selects inside a narrow cohort inherits that cohort's return and that
> cohort's covariance. Before crediting a selector, measure what a random member of the same pool on
> the same day earns — and if the answer is most of it, the cohort is the strategy.**

#### AMENDMENT to the rule, 2026-09-08 — the original wording said *"the selector is a rounding error on a factor exposure."* **That was too strong and is withdrawn.**

**[D378](decisions/D378-RESULT-the-entry-day-does-matter-and-it-survives-losing-its-best-trade.md)
measured the selector directly** with the cohort-conditioned rotation §52a specified, and it is not a
rounding error:

| | |
|---|---|
| A′_c's centre | **+116.91** of the observed +160.55 — a **third** independent measurement that most of the return is cohort (73%, against D373's 79% and D377's 79%) |
| the increment | **+15.98 bp per trade, +26.9 SE** above A′_c's p95 |
| **leave-one-out** | **survives** — dropping GME still clears p95 by **+9.8 SE**. Not one trade |
| per-bar rate at cap 5 | **3.9×** the control's, and the decay across the horizon belongs to **the dip**, not the cohort |

**The level claim stands and the dismissal does not.** A real effect that is small relative to cost is
**a small real effect**, not a rounding error, and the two must not be written as the same thing.
D378 §4 puts the increment at **0.19–0.47× a round trip under PUB** and **0.50–1.21× under PB** — so
whether it can fund itself turns on a spread measurement nobody has taken (D336).

**What survives unchanged:** the level evidence, the corollary below about diversification, and the
instruction to measure the pool before crediting the selector. **What changes is the verdict on what
the measurement then means.**

**The corollary closes a style of work rather than one book.** Variations on winner-selection cannot
diversify each other: at ρ ≈ 0.92 two such constructions are the same strategy for portfolio
purposes, and gate 1d′ is **blind** in that region — it rejects every pair on structure alone
(D376 L2). **Independence inside a cohort must be established some other way, or not claimed.**

**What is NOT retired.** The in-sample measurements stand as made. The `rev_5` dip's *existence*
inside the winner pool is not disproved — D373's H1 cleared its controls as pre-registered, and this
section retires the **avenue** on the size and provenance of the increment, not on a failed null.
The four nulls, the capturability pass (H5: open-entry t 5.11, retention 98.7%) and the segmentation
diagnostic all stand. So does D374's correction: **D373's H4 breadth failure was the bar's fault**,
and by its own null it was the best-diversified book available.

## 52a. The null that was never run: does the entry DAY matter, holding the name and the cohort fixed?

**Declared gap, 2026-09-08. NOT a result — nothing here has been measured.** Raised by the principal
against §52 and the objection survives scrutiny.

**Neither existing control answers it.**

| control | rotates | holds fixed | why it cannot answer |
|---|---|---|---|
| **A′** per-name time rotation | the entry time, to **any** eligible bar | the name, its trade count | a random eligible bar is usually one where the name was **not** in the top decile, so A′ conflates *timing* with *cohort membership*. Its centre is +59.42 for exactly that reason |
| **B_c** same-day same-cohort swap | the **name** | the **day**, cohort membership | it never varies the day, so it is silent on day choice by construction |

**The missing control, and it is one line of new logic:**

> **A′_c — a COHORT-CONDITIONED time rotation.** Rotate each entry to a random **other** bar on which
> **that same name** was eligible **and in the `mom_252_21` top decile**. Name fixed, cohort
> membership fixed, trade count fixed; **only the day moves.**

If the observed book beats A′_c, entry timing adds something **inside** the cohort and §52's rule
does not reach it. If it does not, the dip is picking days that a dart would have picked.

**There is already a reason to think the answer is not trivially "no."** D373's own horizon profile,
converted to a per-bar rate:

| cap | trades | mean bp | hold | **bp per bar held** |
|---:|---:|---:|---:|---:|
| 5 | 8,665 | +39.11 | 5.0 | **+7.82** |
| 10 | 7,290 | +68.62 | 10.0 | +6.86 |
| 20 | 5,450 | +122.36 | 20.0 | +6.12 |
| 40 | 3,932 | +160.55 | 39.9 | +4.02 |
| 60 | 3,210 | +235.73 | 59.8 | +3.94 |

**The per-bar rate halves from entry to bar 60.** The edge is **front-loaded**, which is what an
entry-timing effect looks like and is not what pure exposure to a drifting cohort looks like. **The
missing measurement is the same profile for B_c**: if a random cohort name on the same day is
*equally* front-loaded, the decay is a property of the cohort and not of the dip.

**Two cautions that bound how much this could be worth.**

- **Win rate is a dial on the exit, not evidence.** D373 sits at 51.6% with payoff 1.195. Any
  cap-and-target structure can raise win rate by taking profits earlier, at a matching cost in
  payoff. **The per-trade mean already nets the two**, so "raise the win rate" is not a goal — raise
  the mean per unit of exposure, against the cohort's own mean per unit of exposure at the same hold.
- **`CLAUDE.md`'s standing warning applies directly:** cost-cutting is not edge-sharpening, and a
  change in hold length moves breakeven and per-bar edge in *opposite* directions. Any result here
  must say which moved.

**Status — ANSWERED 2026-09-08 by
[D378](decisions/D378-RESULT-the-entry-day-does-matter-and-it-survives-losing-its-best-trade.md).**
A′_c was built as specified above, run over 2,000 draws, and **the entry day does matter.**

| | |
|---|---|
| A′_c centre | **+116.91** vs observed **+160.55** |
| **T1** mean per trade > p95 | **PASS** — margin +15.98, **+26.9 SE** |
| **T3** the same with the largest trade removed | **PASS** — +150.41, **+9.8 SE**. Not one trade |
| **T2** the same on the **median** | **FAIL** — +51.55 against p95 +64.00 |
| **the front-loading question this section asked** | **ANSWERED: it is the dip's.** The observed per-bar rate halves from 7.82 to 3.94 across caps 5→60 while A′_c's barely moves, 2.01 → 2.75 |

**So the mechanism proposed here was right, and the caution recorded beside it was also right.** The
gain is **in the mean, not the median** — dip timing makes the good trades bigger, it does not lift
the typical trade, and **win rate is the median's neighbour.** The pre-registration's own warning
that win rate is a dial on the exit stands: nothing here shows a better win rate is available.

**The reopening's abandon condition did not fire** — it required T1 to fail outright. Under
[R15](RULES.md#r15) the avenue's status is the principal's, and this file does not presume it.

---

## 53. The EMA-centred log-space density is closed: no shape a volatility-matched shuffle cannot produce, and a distance compared to a point estimate is a guaranteed false positive

**D384**, stage 0, 60 ETFs × 2,516 daily bars × 6 half-lives × 3 bandwidths × 25 null draws.
Pre-registration `0b492cd`, result `docs/decisions/D384-RESULT-the-density-carries-no-shape-the-shuffle-cannot-produce.md`.

**THE RESULT: 0 of 1,080 name-cells clear the pre-registered bar** (observed total-variation distance
> the N2 null's p95 by more than 2 SE). Dropping the 2 SE margin: 46/1,080 = **4.3%**, against a
chance rate of 5.0%. Against the *loose* null N1 the clearing rate is **2.8%** — lower still. The
best single name anywhere in the study reaches +1.27 SE against a bar of +3.65.

**N2 is the load-bearing null and it did what it claimed** — `|r|` autocorrelation observed 0.1426,
N2 keeps 0.0943, N1 destroys 0.0294 — so this is not a null failing to preserve the clustering it
was built to preserve.

### 53.1 What the diagnostics say that the distance alone does not

**The excess mass is one-sided and positive at every half-life** (peak at u = +0.88% to +2.44%, never
below the EMA). A one-sided excess above a moving average is drift, which D382 already found and
retired on daily ETFs. It is not the bimodality-with-price-in-a-valley the study was built to detect.

**The mode count runs the wrong way.** At long half-lives the *shuffle* is more multimodal than the
market: observed 1.45 vs null 1.73 at half-life 160. Volatility clustering alone produces a second
mode, and the market produces less of it than the shuffle does.

### 53.2 The coordinate is price-invariant and volatility-VARIANT — the residual is scale

P3 passes as written: the cross-name coefficient of variation of `x`'s spread is **0.61** against
**1.08** for absolute price. But at half-life 20 the widest name's `x` spread is **357×** the
tightest (SHV 0.03%, ELON 11.57%), still **8.2×** ex-tails. **Pooling or ranking densities in this
coordinate would be dominated by which names are volatile** — the objection the coordinate was built
to answer, displaced one level down rather than removed.

### 53.3 Return-blind stationarity is a VACUOUS selector for a memory parameter

The pre-registration's §2 claimed a genuine interior optimum in half-life, on the argument that a
fast EMA makes `x` stationary and trivial while a slow one makes it informative and non-stationary.
**That is wrong on this data.** Both quantities are strictly monotone — AC1 0.852 → 0.990 and spread
1.97% → 9.90% across half-lives 5 → 160. Nothing trades off against anything, so the criterion
selects nothing. **Any successor proposing to pick a memory parameter return-blind should be shown
this before it designs around the idea.**

### 53.4 THE TRAP, and it nearly produced a spectacular fake result

The first completed run compared the observed distance to the null's **mean density** with **no null
reference distribution** — one number against one number. It would have been reported as **~27 SE of
structure at every half-life.** The bias is fixed, silent, and one-directional in favour of the
hypothesis: the observed density is *one draw* and the null mean is an average of 25, so the observed
is **guaranteed** to sit further from the mean than the mean sits from itself.

**The tell was in a diagnostic, not the headline: the null mean had MORE modes (4.47) than the
observed density (3.03).** A null more structured than the market is not a null that is losing.
Fixed in `bf17839` with a leave-one-out null reference; **the reading inverted from decisive pass to
decisive fail.**

**The general rule: a distance needs a reference distribution of the SAME distance, computed the SAME
way.** Comparing an observed statistic to a null *point estimate* rather than to the null's own
*spread* is not a weak test — it is a test that cannot fail.

### 53.5 One disclosed post-hoc observation, which changes nothing

The observed density is inside the null's spread but is **not centred on it**: 43/60 names sit above
the null's centre at half-life 10 (sign test p = 5.3e-04, surviving Bonferroni over the 18 cells),
decaying monotonically to 28/60 (p = 0.74) at half-life 160. **Roughly +0.4 SE per name, against a
P1 bar of 3.65 SE.**

**This is post hoc and did not reopen the family.** The sign test was not pre-registered; reading a
weaker second test as a rescue after the declared one fails is what a pre-registration exists to
prevent.

**And the obvious mechanism does not survive the check.** Short-horizon serial dependence would
predict the displacement to order across names by their own return autocorrelation. At half-life 10,
where the displacement is *strongest*, `corr(return AC1, displacement)` is **−0.024**; at half-life 5
it is +0.270 (n = 60) and in the **momentum** direction, not the mean-reversion direction the story
needs. **Recorded as unexplained. No mechanism is filed.**

### 53.6 What survives

- **The construction is proved**: `[REC]` 3.4e-16, `[FRAME]` exact. A successor wanting the
  current-frame form inherits a proved component.
- **Translating a density every bar with `np.interp` is DIFFUSIVE** — 7.4e-03 over 900 bars. The
  scalar-offset form (accumulate in a fixed frame, carry an offset, interpolate once at read time) is
  exact.
- **Five of seven pre-registered predictions were falsified**, including both assertions predicted to
  hold on the first run.

**Nothing admitted to either book. No hurdle cleared. No holdout read. No multiplicity ledger touched
(R13) — the study scored no strategy cell.**

---

**AMENDED 2026-09-08 — §53 IS WITHDRAWN PENDING A RE-RUN.** The principal asked what was being
compared to the nulls. **It was one density per cell, at the final mining bar — not the per-bar
sampled-and-pooled statistic §4 of the pre-registration declared.** The measurement path called
`density_direct`, which is the ground-truth helper for `[REC]`/`[FRAME]`, instead of
`density_recursive`. Effective sample size of the compared density is **14.5 bars at half-life 5**
(94% of mass in the last 20) rising to 461.6 at half-life 160, on a 481-point grid — so P1 failed for
want of power and "no shape" is not established. **The family is NOT closed.** What survives:
§53.2 (P3, computed from `x`), §53.3 (P4, ditto), §53.4 (the reference-distribution trap), §53.6
(construction proved). What is withdrawn: §53 headline, §53.1. See the amendment in
`docs/decisions/D384-RESULT-the-density-carries-no-shape-the-shuffle-cannot-produce.md`.

---

## 54. Event mass over time spent carries no excess structure either — and the one emphatic signal in it was an artefact of the study's own tying rule

**D385**, stage 0, 60 ETFs × 2,516 daily bars × 4 event types × 4 sharpening powers × 3 event
half-lives × 25 draws. Pre-registration `63bf19a`, amendment `1fdd865`, runner `787fb24`, result
`docs/decisions/D385-RESULT-the-event-density-carries-no-excess-structure-and-the-close-condition-is-met.md`.

**THE RESULT: 1 of 2,592 name-cells clears the pre-registered bar** (observed TV > N2 p95 by >2 SE).
188/2,592 = 7.3% exceed p95 alone against a 5.0% chance rate; 4.6% against the loose null N1.

**AND `n_eff` WAS ADEQUATE, WHICH IS WHAT MAKES IT READABLE.** 57.7 / 115.4 / 227.6 across the three
half-lives, spread 0.1188 inside the 0.12 bound the `n ≥ 4·hl_ev` filter entails. **[§53](#53) failed
at `n_eff` 14.5 and could not tell "no shape" from "no data". This one can.** The pre-registered
close condition is met; under R15 the family's status is the principal's.

### 54.1 THE ARTEFACT, and the prediction that caught it

Against the null's *centre*, `highest in 20` looks emphatic — **44/51 names above centre at half-life
80, sign test p = 6.1e-08** — while `lowest in 20` shows nothing (21/59, p = 0.99).

**Prediction Q4 had said in advance: "lows and highs behave the SAME. If they differ I will suspect a
sign or masking error before I believe a directional claim."** They differed, so it was checked, and
it is an artefact **created by the study's own tying rule**:

```
        swing low: rate  24.0/100  ->  centring EMA half-life  167 bars
       swing high: rate  23.3/100  ->  centring EMA half-life  171 bars
     lowest in 20: rate   6.7/100  ->  centring EMA half-life  600 bars
    highest in 20: rate  18.3/100  ->  centring EMA half-life  218 bars
```

In a decade-long bull market **20-bar highs outnumber 20-bar lows 2.60×** (57 of 59 matched names).
Because `hl_bars = hl_ev / rate`, that rate gap becomes a **600-bar vs 218-bar centring EMA**, so the
two types are measured **in different coordinates** and were never the symmetric pair the comparison
assumed.

**The control is decisive: the swing types have a matched rate ratio of 1.000× and near-identical
tied half-lives (167 vs 171), and they behave IDENTICALLY — both 39/58 above centre at half-life 80,
p = 6.0e-03.** Where the two directions are genuinely comparable they agree; the asymmetry lives
entirely where the construction made them incomparable. **No directional mechanism is filed.**

**Carry forward: tying a centring half-life to an event rate makes rare and common event types
mutually incomparable.** Anything comparing types must fix the centring span across them.

### 54.2 A read-time power on a RATIO amplifies the thin denominator, not the overlaps

`s = normalise((f/g)^p)` was built to make coincident events beat isolated ones superlinearly, and on
synthetic data it does (pair/solo 1.60 → 120.76 across `p ∈ {1,2,4,8}`). **On real data it walks the
peak into the tail instead:**

```
  swing low, hl_ev 20:  p=1 peak -1.00%  |  p=2 -2.50%  |  p=4 -6.56%  |  p=8 -11.38%
```

`f/g` is largest where `g` is *smallest*, so the power preferentially amplifies the thin-denominator
tail. **A `g > 0.05·max g` support floor is not strong enough to contain it, and the synthetic checks
missed it because they used a smooth Gaussian `g` with no thin tail to amplify.** Displacement decays
monotonically in `p` (0.73 → 0.61 → 0.41 → 0.44): **the sharpening never helps at any point.**

**Any successor using a read-time power on a ratio needs a stronger denominator floor declared in
advance, and should treat `p > 2` as suspect without one.**

### 54.3 What the assertions caught before a number was read

- **`[STAT]`** (the assertion §53 died for not having) fired at **8.5e+01**: `scipy.lfilter` starts
  from zero state, so the log-price EMA began at 0.0153 against a log price of 3.456, and the
  transient outlived the warm-up — **14.3% of bars landed off the grid** where the kernel underflows
  to zeros and the bar silently vanishes.
- **`[CAUSAL]`** fired at **5.16**: `rate`, `hl_bars` and `h_eff` were full-sample, so shocking a
  future bar moved the event count → the tied half-life → the EMA → `x` at **every** bar. Fixed by
  warm-up-only estimation, which makes the construction causal rather than merely descriptive.
- **`[NEFF]`'s tolerance was derived, not fitted.** It fired at 0.068 against an arbitrary 0.02.
  `n_eff(n) = (1+λ)/(1−λ)·(1−λⁿ)²/(1−λ²ⁿ)`, and `n ≥ 4·hl_ev` pins `λⁿ = 0.0625`, entailing a
  worst-case 11.8% deficit. **0.12 is what the filter guarantees; it was not tuned to the observed
  0.068.**

### 54.4 What this does NOT establish

Rare event types (reversals 2.4/100, moves >2% 4.0/100) were **excluded by a narrowing I declared and
flagged for objection, and were never tested**. `lowest in 20` at half-life 80 kept **7 of 60 names**
and is not evidence. The principal's decay-coherence fork was parked with a scaffold and remains
open.

**Nothing admitted to either book. No hurdle cleared. No holdout read. No multiplicity ledger touched
(R13).**

---

**AMENDED 2026-09-08 — §54'S CLOSE CONDITION SHOULD NOT BE ACTED ON.** The principal asked whether
the D385 failure meant bad design rather than a dead idea. It means bad design, and worse than §54.1
and §54.2 record: **the stage-0 statistic cannot answer the question the family is for.** TV(density,
shuffle density) is a functional of the DENSITY ALONE; the signal is a functional of (DENSITY,
FORWARD RETURNS). Demonstrated by holding a real path -- hence the density, hence TV = 0.3288 -- 
exactly fixed and attaching two forward-return processes: one blind to the density (t = +0.25), one
depending on it (**t = +4.62**). **The statistic is identical in both and clears in neither.** So a
null TV licenses NO conclusion about the signal. What survives is the narrow claim that at p=1, on
the properly-matched swing types with adequate n_eff, the density's SHAPE is not unusual -- and every
measured design fault, which is mine. **The family needs a direct signal test (condition on the
density, measure forward returns, score per R15), not another premise check.** See the amendment in
`docs/decisions/D385-RESULT-the-event-density-carries-no-excess-structure-and-the-close-condition-is-met.md`.

**AMENDED AGAIN 2026-09-08 — THE OBJECT WAS BUILT CORRECTLY AND FED THE WRONG INPUT.** Neither D384
nor D385 ever LOOKED at the density; both reported only TV against a null. Looking: the per-bar `f`
is smooth and continuous (1-3 modes, ~19-cell bandwidth) — **the smudged-density construction worked
as designed.** But for the swing types the event density **reproduces its own calibration** — ratio
median 0.974, CV 0.21, peak 1.46x the median — because a 2-bar swing low on closes happens on **24%
of bars**, and an event that common cannot be distributed differently from time. `TV(f,g)` rises
monotonically as the event gets rarer (0.061 / 0.065 / 0.185 / 0.214). **§54 excluded the rare types
to protect `n_eff`, which was never the constraint — event-time decay had already fixed it at ~115
for every type — so the narrowing selected exactly the events least able to carry information.** Also
corrected: the `modes` field in `data/d385_event_density.json` (mean 24.9) is an artefact of
averaging `s` across bars with differing support cuts and does NOT describe the density. **The family
is UNTESTED, not refuted.**

---

## 55. The density line's first real signal test: no signal, the edge is reversion from `x` alone, and the two nulls disagreeing is the entire finding

**D387**, signal test under R15, path-invariant lens. 600 US single names, 2010-01-04 → 2026-08-26,
2 rare event types × 3 λ × 3 holds, N2 20 draws + A′ 40 rotations, 20,062 cells.
Pre-registration `b83ad16`, runner `b92d554`, result
`docs/decisions/D387-RESULT-no-signal-the-edge-is-reversion-from-x-alone-and-cost-buries-it.md`.

**0 of 18 cells clear. Best margin −1.18 SE.** Gross is positive at long holds (up to **88.1 bp**) but
**net is negative in all 18 cells**, −54 to −148 bp, against a **Corwin–Schultz spread of 127.9–142.1
bp measured on the names actually held**.

### 55.1 THE FINDING: beating a shuffled PATH is not beating a rotated DENSITY

```
        type  lam   H    n  gross bp   N2 p50  z vs N2    sign p    A p50  z vs A
reversal >1%  120  20  579      50.2    -28.9     0.36  1.16e-18     23.1    0.01
    move >2%  250  20  508      88.1     -5.7     0.28  1.53e-10    129.0    0.06
```

**Against N2 the displacement is overwhelming — sign tests to p = 1.2e-18 across 579 names. Against
A′ it vanishes, and A′ is often ahead.**

**N2 destroys the real price path. A′ destroys only the density's ALIGNMENT with the current price,
on the same real path.** Beating the first and not the second says the edge is **not in the
alignment**: it is trading a real path at extreme `x` and betting on reversion. A *misaligned* density
picks a different set of extreme-`x` bars and does just as well. **The event-density conditioner adds
nothing to what `x` already carries.**

**Without the persistent-selector control this study would have reported a 1e-18 headline.** That is
what R7 is for, and this is the cleanest demonstration of it in the programme.

### 55.2 Two defects the record discloses about itself

**THE PRE-REGISTERED BAR WAS UNREACHABLE.** N2's per-name draw-mean spread is **415 bp**, so
"p95 + 2 SE" sits at **1,975 bp** against an observed 88.1 bp. **N2 at 20 draws is not decisive at
the margin the bar demands** — D384's H4 problem again, a hurdle nothing could reach. The 0/18
carries less information than it looks like; the null-centre comparison is where the result lives.

**THE ARMS USED DIFFERENT GATES.** The observed used the pre-registered causal expanding quantile;
the nulls used a matched-count top-`R` gate introduced while optimising and called "conservative"
without measurement. **Measured: the top-n gate is worth up to +126 bp — larger than the entire
claimed edge.** Re-checked gate-matched on 98–117 names, **A′ still beats the observed in 6 of 8
cells**, so §55.1 survives on weaker evidence. **A clean re-run gives every arm one gate.**

### 55.3 A pre-registered test that was VACUOUS BY CONSTRUCTION

§3 declared continuation as a second look and §10 said that if it "clears equally, the conditioner
marks volatility, not direction." **For a symmetric signed trade it cannot**: `direction = −1` flips
the sign on the *same* decision bars, so continuation is the exact arithmetic negative —
`max |revert + continue| = 0.000e+00` across 10,025 cells. **The abandon condition could never fire.**
The right test is `|return|` or dispersion at eligible bars, and it was not run. **Check that a
declared alternative is not the arithmetic negative of the primary before pre-registering it.**

### 55.4 What the trades depend on

```
  mean 88.1 bp < median 134.0 bp   -- the LEFT tail is doing the work
  ex-top 1% 48.3   ex-bottom 1% 133.6   trimmed 93.8   win 54.3%   skew -0.172
  30 of 508 names to half the P&L; top-10 21.5%; 61.6% of names profitable
  ALIVE 366 names +142.4 bp    DEAD 142 names -51.8 bp   (28.0% dead)
  cheap half +106.0 bp   dear half +70.3 bp   (median price $31.38)
```

**Concentration is not the problem — survivorship is.** The whole edge sits in names still alive; the
dead 28% lose money. And the cheap half earns more while paying more in bp, so cost erodes it fastest
exactly where it is largest.

### 55.5 Speed, recorded because it was the reason for a rule

**3,044 s at 5.98× on 6 workers — 100% efficiency**, against D385's 55%. `parallel_map`'s `[SPEED]`
report (`dc30d00`) stayed silent, which is what passing looks like. The optimisation that got it
there was profile-driven: the bottleneck was **not** the densities but `expanding_threshold`, an
O(n²) scan called 126× per name; giving the nulls the matched-count gate they already needed removed
20 of 21 scans and took the projection from **3.7 hours to ~50 minutes**.

**Nothing admitted to either book. No hurdle cleared. No holdout read.**

**AMENDED 2026-09-08 — THE EVENTS WERE NOT RARE ON THIS UNIVERSE.** The principal asked whether the
density had shape. It did not, on half the sample. §2 justified the two event types from an **ETF**
measurement (5.0 and 7.0 per 100 bars) and then carried the same **absolute** thresholds to single
names at 3-5x the volatility: `move >2%` fires on a **median 28.3% of bars**, and on **282 of 600
names it exceeds 30%**. TV(f,g) then collapses 4x and ratio CV 5x as the event rate rises
(0.157/0.487 at a 0-15% rate, 0.039/0.096 above 50%) — **f IS g when the event is most bars**, which
is §54.1 verbatim. Silverman compounds it: bandwidth widens 4x on exactly those names (8.5 to 35.3
grid cells), one profiled name showing a 17%-wide kernel and ZERO modes. **"No signal" stands on the
trading evidence, but the study tested the idea DILUTED.** Fix: threshold in the name's own
volatility units. **Third time in this line the event definition was not matched to the instrument.**

---

## 56. The clean test: the density finally had shape, and the conditioner still adds nothing to `x`

**D388**, signal test under R15, 600 US single names, 2 event types × 2 σ-multiples × 3 λ × 3 holds,
N2 20 draws + A′ 40 rotations, 17,511 cells. Pre-registration `1c168f3`, runner `8f1dced`/`85e9171`,
result `docs/decisions/D388-RESULT-the-density-finally-had-shape-and-the-conditioner-still-adds-nothing.md`.

**This is the first clean test in the density line.** D384 measured the wrong statistic, D385 measured
a flat object, D387 measured a flat object on half its universe with mismatched gates. D388 fixes all
of it: rare events in σ units, one gate for every arm, and the density's shape reported as a
first-class output.

### 56.1 THE OBJECT WORKS — rarity is the mechanism for shape

```
      type     k  lam  rate/100   TV(f,g)  ratio CV  modes
      move   2.0   60      5.16    0.2573     0.727    3.0
      move   2.5   60      2.67    0.3615     0.964    3.0
  reversal   1.0   60      3.86    0.2720     0.766    2.0
  reversal   1.5   60      1.17    0.5104     1.307    2.0
```

Against [§55](#55)'s worst bucket — **TV 0.039, CV 0.096, 0 modes** — this is **4.5–13× the structure
with 2–3 modes everywhere**, and it rises **monotonically with rarity** at every λ. **The σ threshold
was the right diagnosis:** rarity spread across names collapses 4.37× → 1.37×, and the flat density
of §54 and §55 was an artefact of events that were not rare.

### 56.2 AND IT STILL ADDS NOTHING — the A′ result replicates on a shaped density

**Against N2** (shuffled path): positive in **34 of 36 cells**, sign tests to **7.2e-11**.
**Against A′** (rotated density, same path): **6 of 36 cells positive, best +0.19 SE, none
significant** (best `p` = 0.079) — and **all six sit in the thinnest cell**, `reversal k=1.5`, where
`MIN_EVENTS` drops 375 of 582 names and **the survivors are the most event-rich** (median 166 events
against 85 dropped). The only positive cells are the ones with a filtered sample.

**N2 destroys the price path; A′ destroys only the density's ALIGNMENT with the current price.
Beating the first and not the second means the edge is trading a real path at extreme `x` and betting
on reversion — a misaligned density does just as well.** Cost settles it regardless: **net negative in
all 36 cells**, best gross 61.2 bp against a ~110–130 bp measured spread.

**Two studies now agree on this with different event definitions, different universes and different
gates. It is the most replicated negative in the programme.**

### 56.3 The generalisable lessons

- **A threshold in percent is not a threshold in rarity.** Express event thresholds in the
  instrument's own units or measure the realised rate per name and report the spread.
- **Rarity improves the OBJECT, not the P&L.** Q4 held on the A′ margin at every λ and H, and was
  falsified on gross. A better-shaped conditioner did not become a better predictor.
- **Beating a path-shuffle null is nearly free; beating a persistent-selector null is the test.**
  Without A′ this study reports a 7.2e-11 headline. R7 exists for exactly this.
- **`f̂` is constant between events under plain decay.** `f` is scaled by `λ^gap`, a scalar, which
  cancels in the normalisation — so the dense (T, GRID_N) accumulation is unnecessary and the
  recursion runs over the ~110 event rows. **39.0 ms → 1.6 ms, 24×, exact to 1.2e-14.** The naive
  version of this (decaying λ per *event* rather than per *bar*) is wrong by 3.87 and `[FAST]`
  catches it.

### 56.4 Two self-tests that passed when they should have failed

**`[RARE]`** returned "spread 0.00, max 0.0%" when every key had fewer names than its minimum — it
skipped them all and reported success. **D387's `[LAG]`** opened its independent re-derivation at
`WARMUP` while the runner opened at `THR_MIN`, ~100 bars apart; it passed only because no crossing
fell in the gap on its probe name (fixed `36bab8c`; the decisions were causal either way, so §55
stands). **Both now raise, and both have their own `[X]` break.**

**Nothing admitted to either book. No hurdle cleared. No holdout read.**

**ADDENDUM 2026-09-09 — THE CONDITIONER IS INERT, NOT WEAK.** The principal asked whether these pass
their nulls and whether they have been traded. A sharper test than either: if the conditioner carries
information, names whose density is MORE structured should show MORE edge over A-prime. Measured per
name within each of the 36 cells, **corr(density shape, edge) has mean -0.027, median -0.022, range
-0.122 to +0.109, and is positive in only 10 of 36 cells — below chance.** A weak-but-real conditioner
would still show a gradient; there is none, across the whole cross-section of density quality rather
than only at the traded top decile. **What has been traded:** top-decile R, reversion, three holds,
path-invariant, gross and net — negative in all 36. **What has not:** a slot-limited book and
cross-sectional ranking (neither can create information a per-trade mean lacks), and the **R response
curve** — only the top decile in one direction was ever traded, so the low end of R and any monotone
gradient remain untested. That is the one live successor, and it is a THIRD look under R13.

---

## THE DENSITY LINE IS RETIRED — the principal's decision, 2026-09-09

**Retired by the principal after D388, under R15.** D384 → D388, five studies. **Written here rather
than edited in anywhere, per the append-only rule.**

### What was tested and what closed it

| | |
|---|---|
| **the idea** | the principal's: a price-structure density centred on a moving average, in log space, so it is price-invariant and reads in percentages |
| **the object** | **works.** Given a genuinely rare event it produces a smooth, causal, price-invariant, multi-modal density — TV(f,g) 0.18–0.51, ratio CV 0.51–1.31, 2–3 modes, proved bit-identical against an explicit loop |
| **what closed it** | **the conditioner is INERT.** It beats a shuffled-path null in 34/36 cells at `p` to 7.2e-11 and beats a **rotated-density** null in 0/36. `corr(density shape, edge)` across all 36 cells: **mean −0.027, positive in 10/36 — below chance.** Net negative in all 36 against a measured spread |

**The distinction that decided it:** N2 destroys the price path; A′ destroys only the density's
**alignment** with the current price. Beating the first and not the second means the edge was
reversion from `x` alone. **Without A′ this line reports a 7.2e-11 headline and admits a signal that
is not there.**

### What it cost, stated plainly

**Five studies and roughly 4.5 hours of compute, of which three were spent measuring the wrong
thing:**

- **D384** — measured a statistic (TV against a shuffle) that is a functional of the density **alone**
  and cannot see whether the density predicts returns. Close withdrawn.
- **D385** — measured a **flat object**: swing lows fire on 24% of ETF bars, so `f` reproduced its own
  calibration. Close withdrawn.
- **D387** — measured a flat object on **half** its universe (absolute thresholds carried from ETFs to
  single names at 3–5× the volatility) with **mismatched gates** worth up to 126 bp.
- **D388** — the clean test. Object shaped, one gate, rare events. **Still inert.**

**The principal had to ask "did the density have shape?" twice before it was looked at.** Both times
the answer was no, and both times a test statistic had already been reported as though it were.

### What survives and is worth keeping

- **The construction, proved and fast.** `[REC]`, `[MASS]` 5e-16, `[CAUSAL]`, `[FAST]` 3.6e-15.
  `scripts/run_d387_level_reversion.py` and `scripts/run_d388_rare_event_levels.py` stay.
- **`f̂` is constant between events under plain decay** — `λ^gap` is a scalar and cancels in the
  normalisation, so the dense (T, GRID_N) accumulation is unnecessary. **39.0 ms → 1.6 ms, 24×.**
  The naive form decays λ per *event* rather than per *bar* and is wrong by 3.87.
- **A threshold in percent is not a threshold in rarity.** σ units collapsed the cross-name rarity
  spread 4.37× → 1.37×.
- **Rarity improves the OBJECT, not the P&L.** Q4 held on the A′ margin at every λ and hold and was
  falsified on gross.
- **Beating a path-shuffle null is nearly free.** The persistent-selector control is the test.

**Nothing was admitted to either book. No hurdle was cleared. No holdout was read. The R13 ledger
carries two looks at "price reverts at levels where its own rare events cluster" and the line is
closed on both.**

---

## 57. The 0.44 correlation floor is ONE factor, it is none of the four candidates, and in the arm that matters it is 98.5% unexplained

**D389**, mechanism decomposition on the committed `data/d376_series.npz` (500 A′ + 250 B + 500 B_c
books × 4,187 bars). Pre-registration `5bd7d97`, result
`docs/decisions/D389-RESULT-the-floor-is-ONE-factor-and-none-of-the-four-candidates-explains-it.md`.
No cell scored, nothing admitted, no holdout read, nothing fetched.

### 57.1 It is ONE factor, and that makes the search well-posed

```
  [A'] PC1 variance share 0.449 vs pairwise rho 0.449   PC2 0.006   sign agreement 1.00
  [B]  PC1 variance share 0.478 vs pairwise rho 0.476   PC2 0.014   sign agreement 1.00
```

**PC1's variance share reproduces the observed pairwise correlation to three decimals in both arms**,
PC2 is an order of magnitude smaller, and all 500 books load with the same sign. **The floor is not
four small mechanisms adding up — a single correct identification would explain the whole thing.**

### 57.2 And it is NONE of the four candidates

```
                        driver     A' |corr|       B |corr|
       m (equal-weight market)         0.480          0.138
        |m| , m^2  (NONLINEAR)    0.070/0.066    0.087/0.009
     nlive (eligibility floor)         0.029          0.054
      d nlive (breadth change)         0.053          0.001
    cross-sectional dispersion         0.008          0.059
     1/nlive (equal-weighting)         0.031          0.052

  floor after removing EVERYTHING:  A' 0.4488 -> 0.3829     B 0.4759 -> 0.4688
```

**PICKUP's three named candidates — slot mechanics, equal-weighting, the eligibility floor — score
≤ 0.052, and so does the fourth D389 added, the shared hedge term.** Unattributed: **85% in A′,
98.5% in B**, against book-clustered SEs of 0.0014 and 0.0017. **We still do not know what the floor
is.**

### 57.3 THE FINDING WORTH CARRYING: the two arms disagree by 9×, and backwards

**A′** (same names, rotated times) correlates **0.480** with the equal-weight market.
**B** (same days, swapped names) correlates **0.138**, and with nothing else.

**A′ books share market exposure because they hold the same names on a similar schedule — a quarter
of their common factor. B books share the trading DAYS, and their common factor is almost entirely
something about those days that is NOT the market.**

**B is the arm that matters** — "two unrelated constructions", the arm [gate 1d′](#52) is calibrated
against — **and its floor is 98.5% unexplained.**

**Where to look next, and it follows directly:** the factor lives in **which days get traded**, not
in the market's behaviour on them. That points at the **entry-condition distribution** — what makes a
bar eligible — rather than at anything in the return generating process. It is a different object
from every driver tested here.

### 57.4 Gate 1d′ needs no restating — and why that was in doubt

The worry was that the floor might be an artefact of the scorer's own arithmetic, in which case 1d′
would be calibrated against nothing. **It is not: `1/nlive`, the denominator every book divides by,
scores 0.031 and 0.052.** So the gate measures something real. **It is calibrated against an
unidentified factor, which is not a defect — the pool-relative form of 1d′ is exactly the right shape
for a floor whose cause is unknown.**

### 57.5 Two guards fired, and the second was itself wrong

**`[SER]` fired first and caught MY error, not the data's**: the runner estimated the floor from a
capped 1,770-pair subsample and missed D376's committed B p50 by 0.008, pure sampling. Replaced with
the exact full-pair computation — **one matrix product**, because B and B_c masks are identical
across every book.

**`[FASTC]` then fired at 9.9e-3 and the guard was mis-specified.** It demanded individual-pair
equality between two estimators that genuinely differ for A′ (per-pair mask intersection against a
common mask, up to 3 bars of 4,124). **The study reads the arm's MEDIAN, so the guard now bounds the
median gap (9.87e-04), reports the worst pair, and demands exactness only where masks are identical
— where it gets 8.9e-16.** *Guard the statistic you actually use, not a stricter one you do not.*

---

## 58. D280's overnight gap is not an opening-print artefact — and 17.6% of bars carry one anyway

**D402**, measurement record, reusing D280's own module for fixture, signal, split and `ic_series`.
Pre-registration `6843a39`, result
`docs/decisions/D402-RESULT-the-overnight-gap-survives-and-the-contamination-is-real-but-elsewhere.md`.
Prompted by the prop-firm research folder's own prerequisite for its C19-2 row — *"run the
stale-price / closing-auction contamination test first"* — which had never been required of ours.

**`[REP]` reproduced D280's committed gap IC to five decimals before any filter: ALL −0.01531
(t −4.71), QUAL −0.01255 (t −3.45).**

### 58.1 The contamination is real, common, and detectable

```
  flagged share of 2,232,440 out-of-sample bars
    S1 open == prior close        5.84%     S4 zero/absent volume    0.54%
    S2 open==high==low==close     0.51%     S1-S4 combined          17.58%
    S3 open at session extreme   13.16%

  corr(gap, intraday)   contaminated -0.1564  (n 392,539)
                        clean        +0.0082  (n 1,838,232)
```

**One bar in seventeen has an opening print bit-identical to the previous close.** A stale print is
corrected by the first real trade, so an artefactual gap must reverse — and **the reversal is
confined almost exactly to the flagged bars.** This also explains D280's pooled
`corr(gap, body) = −0.0429`: it is the contaminated 17.6% showing through a pooled average.

**That is a reusable data-quality fact about this fixture, independent of D280.**

### 58.2 But the edge is not there — it is STRONGER without them

```
    ALL  CLEAN (neither S1-S4 nor S5-S6)  -0.01746  t -4.49  1.14x committed  n 1,349,269
   QUAL  CLEAN                            -0.01507  t -3.75  1.20x committed  n   327,060
```

**Removing every contaminated bar makes the edge larger, on 60% of the original sample.**

### 58.3 THE DISCRIMINATING TEST: the gradient runs the other way

```
    $ volume quintile:      Q1        Q2        Q3        Q4        Q5
                      -0.01231  -0.01154  -0.01616  -0.01543  -0.02194
```

**The gap IC is 1.8× stronger in the most liquid quintile than the thinnest**, and stronger in dear
names than cheap. **A print artefact must concentrate where prints are unreliable; this concentrates
where they are most reliable.** The two hypotheses predicted opposite gradients and the
pre-registration said so in advance.

**This falsified my own against-myself prediction** — I expected the gradient to invert, because
D284 was killed by exactly that. **Where the effect is strongest is new information and it is the
opposite of what the universe's cheap tail would suggest.**

### 58.4 What it does NOT touch, and the limit of the test

**Nothing about tradeability.** D280's own runner already records that the IC does not survive into
money at N=25 — *"the ascending short LOSES 11–18 bp per night overnight"*, and *"a rank IC describes
the WHOLE cross-section; a top-N book lives in ONE TAIL."* **That correction stands untouched. This
removes a doubt about the measurement, not about the money.**

**And S1 and S4's own ICs are unmeasured** — their bars are too scattered for a cross-sectional IC to
carry enough names per day. The 5.84% of `open == prior close` bars are excluded by the CLEAN cut,
but what they would have scored is not known.

---

## 59. A best-of-N permutation floor prices SELECTION and is blind to SIGN-FITTING: a composite of sixteen pure-noise signals clears it by 1.28

**Measured 2026-09-09.** `scripts/probe_signfit_floor.py` → `data/signfit_floor_probe.json`.
Closed form **and** a 200,000-draw simulation, required to agree. **No fixture is involved** —
this is sampling theory about a method, not a result about any data.

**Provenance, stated because it matters to how the finding should be weighted.** The claim
arrived in an external-evidence brief commissioned for lead C1 of
[`the-negative-space-scan.md`](../docs/research/the-negative-space-scan.md)
(`working/leads/C1-combination.md`). **It is recorded here because it was re-derived and
verified here, not because the brief said it.** The underlying algebra is attributed in the
brief to Novy-Marx (2016), which has **not** been read by this programme.

### The mechanism

For `k` uncorrelated, equal-volatility signals combined equal-weight,
`t_combo = √k · mean(t_i)`. **Orthogonality therefore multiplies detectability by `√k`.**
Signing each signal by its own in-sample `t` replaces `t_i` with `|t_i|`, so under the null of
`k` **worthless** signals:

```
E[t_combo] = √(2/π) · √k         sd[t_combo] = √(1 − 2/π) ≈ 0.603,  FREE OF k
```

The sd is `k`-free because the `√k` multiplier and the `1/√k` of the mean cancel exactly.

### The number that matters, at k = 16

| | p95 under pure noise |
|---|---:|
| **best-of-16 `\|t\|`** — what a best-of-N floor prices | **2.95** |
| **sign-fitted equal-weight composite** | **4.23** |
| signs **pre-declared in writing** | **1.65** |

> **A COMPOSITE OF SIXTEEN PURE-NOISE SIGNALS CLEARS THE SELECTION FLOOR BY +1.28.** Selection
> and sign-fitting are **different biases**, and a floor for one is not a floor for the other.
> The second exists **even when nothing is selected**.

### What this does and does not say about the D395 floor

**It does not say the floor is wrong.** [`CLAUDE.md`](../CLAUDE.md) records the exact
permutation floor in `run_d395_chop.py` — best-of-N for a cell picked from a grid, no
independence assumption — and says it should replace normal-approximation floors programme-wide.
**That stands. It is correct for what it prices.**

**It says the floor must be EXTENDED wherever a construction orients its own components in
sample:** the null must draw synthetic components and **sign them the same way the treatment
does**. Any composite, any voting rule, any "z-score the inputs and add them" construction is in
scope.

**And pre-declaring every sign in writing is worth a factor of ~2 in the hurdle (4.23 → 1.65)
for no computation at all** — the cheapest hurdle reduction this programme has been offered, and
a writing discipline rather than a method.

### The correction it forces on §-adjacent reasoning about D280

**[D280](decisions/D280-the-forecast-precheck.md)'s gloss on its own independence result was
backwards, and this record says so plainly.** The written position was that sixteen OHLC
derivative terms carrying 13.50–15.76 *effective* inputs and no individual predictive power were
*"sixteen independent sources of noise, with no redundancy left to average away."*

**Orthogonality is the thing that helps.** At 13.5–15.8 effective inputs the `√k` multiplier is
**3.7–4.0×**; the nine price scores at D268's **2.87** effective inputs buy only **1.69×**.
**By this programme's own two measurements, the family it dismissed is the better combination
candidate and the family it kept is the worse one.**

**What remains true from D280 is the empirical part** — those sixteen terms carry no predictive
power *as levels*, measured. **What is withdrawn is the inference** that independence makes
combination hopeless. **Nothing here says a combination works; it says the argument given for
why it could not was wrong, and that the honest test needs the sign-fitting null above.**

### Scope, so this is not over-read

The closed form assumes **uncorrelated, equal-volatility** components. Real signals are neither
— this programme's own catalogue collapses nine price scores to 2.87 effective inputs. **These
are calibration values for how a floor must be built, not a verdict on any actual study**, and
no study in this record has been re-floored against them.

---

## 60. `etf_wide_daily_raw` is not an ETF fixture: a quarter of it is closed-end funds and 23 of its 24 deaths are fund wind-ups

**Measured 2026-09-09.** `scripts/probe_etf_fixture_composition.py` →
`data/etf_fixture_composition.json`. **Found in passing** by an external-evidence agent working
on an unrelated lead, on a fixture **D382, D384 and D385 have already run on**.

### What was measured

The fixture carries no instrument-type field, so classification used a **distribution
signature** — closed-end funds characteristically pay **monthly** and at **high yields**, because
a managed-distribution policy is the product. **The rule was declared before the counts were
read** (≥10 payments/yr **and** ≥5% annualised yield) and is deliberately strict, so **every
count below is a LOWER BOUND.**

| | |
|---|---|
| CEF distribution signature | **150 of 551 = 27.2%** *(an independent count in the brief, using exchange listing flags, gave **172 = 31.2%**)* |
| the mortality cohort | **23 of 24 dead names are closed-end funds by inspection.** The single exception, `ELON`, paid no distributions at all |
| distributions absent from `close` | whole fixture median **3.06%/yr**, mean 5.15%; **CEF cohort median 10.54%/yr** |
| terminal-wealth understatement, 16 years | **5.37×** on the CEF cohort |

> **A "DEAD-INCLUSIVE" FIXTURE WHOSE DEATHS ARE FUND TERM MATURITIES AND MERGERS IS NOT
> MEASURING DELISTING RISK AT ALL.** The cohort that was supposed to remove survivorship bias is
> made of orderly fund wind-ups, which are not the failure mode the bias is about.

The fixture's `purpose` field also reads *"US single-name equity base for SHORT-SIDE research"* —
a copy-paste artefact from the equity fixture, on a file of 551 funds.

### What is at stake, checked rather than assumed

**All three studies pass the events file to `load_ragged`, so their P&L used `total_log_returns`
and is NOT affected.** What is affected is **anything reading `closes` as a price LEVEL** — which
is exactly the log-price axis [D384](decisions/D384-the-EMA-centred-log-space-structure-density.md)
and D385 built their density on, **bled by ~10.5%/yr across a quarter of the universe.**

**That line is retired**, so the live stake is **the fixture itself and any future study that
opens it.** No record is withdrawn here and no metadata was edited — **a correction to the
fixture, and any re-read of those three records, is the principal's call.**

### The rule this earns

**A fixture's NAME is not its composition, and a status count is not a cause of death.** The
`status_counts` field said `delisted: 22` and was believed; what it did not say, and what nothing
checked, was **what kind of instrument died and why.** This is the third place the programme has
been caught by an unexamined corporate-action or instrument basis, after the 15m-vs-daily
adjustment split and the thirty fabricated dividend days of §18. **Census the instrument types
and the death causes when a fixture is built, not when an unrelated agent trips over them.**


## 61. A departure-zone touch earns +10 to +13 bp gross on three disjoint name sets, and nothing built on it survived a holdout: the second-zone line is closed

**The principal closed the line on 2026-09-10** after D412–D433: twenty-two studies, two holdout
reads, both daily holdouts spent for the construction. Records: `D430-RESULT-*` (holdout 1) and
`D433-RESULT-*` (holdout 2).

**What reproduced.** D413's distance-armed departure zone — a ≥1-ATR candle whose zone the close
then clears by 1 ATR — touched and entered at the touch-day close, exited at `t+5`:

| | in-sample (1,573 names) | holdout 1 (803) | holdout 2 (576) |
|---|--:|--:|--:|
| all touches, gross bp | +9.8 | +10.1 | +13.0 |
| cell 2 (REV ≤ −2.47%, EFF > 0.237, ADV > $44M) | +30.3 | +18.1 | +18.0 |
| cell 2 ∧ top-ADV tercile | +37.9 | +21.3 | +13.4 |
| the same, 10-slot book, net Sharpe | +0.05 | −0.03 | −0.19 |

A real short-horizon reversal after a large move on a liquid name, worth a third of a 24–34 bp
round trip. **File it as a base rate** (a random trade after a zone touch earns ~+12 gross); it
is not a trade.

**What did not.** Every layer selected on the spent names after one look — the second touch
(+45 → +6 / +17), the cheap tercile (+86 → +17 / +28), long-only (+80 → −29 / −21), the gap
ordering, the ADV tercile's gross side, a breadth gate, nine exit constructions — and every
in-sample null they passed (within-day permutation, matched random pools, +5 to +10 SE). **Those
nulls test selection inside the spent names, not transfer.** The in-sample 2020 premium was the
names: on unseen names 2020 was −635 bp per cheap long.

**Two exits worth remembering as facts:** no ATR, structure or zone exit beats `t+5` with nothing
(inside the hold the expected remaining move is non-negative in every state, including at the
prior swing); the one exit that carried information — a limit at the *next live* opposite-side
zone — did so only on events the final construction dropped.

**Method that came out of it:** a fixture-parametrised pipeline with an in-sample `--proof` before
any out-of-sample read; the ladder printed on the holdout so a failure is located; Sharpe with a
monthly block-bootstrap SE; and the rule that a prediction on a date-defined subset must have its
sign computed from spent data before pre-registration — the breadth gate (D432) was pre-registered
with the wrong sign on a true stage-0 fact.

---

## 62. The repo's half-spread is a range estimator: 17–55 bp a side on names whose quote is one or two, and every net-of-cost verdict since D285 was made against it

**A measurement, D439 (2026-09-11), on the 15-minute fixtures' forty large and mid names.** The
PUB half-spread the kernel charges (Corwin–Schultz off daily high/low, the D332 convention) reads
**median 28 bp a side, terciles 22.7 / 35.0, wide tercile 55** on MSFT, JPM, CSCO, INTC, V, PG.
Their quoted half-spreads are one to two basis points. The estimator reads intraday *range*, and
range and quote converge only on small illiquid names. **Nothing in the repo has ever compared
the estimator to a quote** — D336's pull (built and dry-tested 2026-09-05) needs a TWS session
and has not run; D441 (2026-09-11) extends it to the 272 names one construction trades.

What was measured model-free on those names: a limit at the open that needs a 5 bp trade-through
**fills 92% of the time**; on the 8% of days it does not, the price is +112 bp away at the
half-hour, so the chase costs **~9 bp per order**; net of the chase a passive order recovers
**0.66 of the modelled half-spread** (0.72 in the wide tercile, 0.57 on volume-shock days).

**How to read every "net" in this file after D285:** it is net of a range, not a spread. On
small, thin, volatile names the two are close and the verdicts likely stand; on liquid names a
construction has been charged up to ten times its cost. Records since D439 print a second
"passive at the open" line (modelled half-spread × 0.34 per side + 9 bp chase), **labelled an
assumption**, beside the crossed line. The quote pull would retire the assumption on all of
them at once. It is the highest-value unrun measurement in the programme.

---

## 63. A 3× volume bar in a top-price name is followed by a continuation the state alone does not predict, at every horizon — and it is not a book at any cost line the repo can justify

**D434–D440, 2026-09-11, in-sample on the mining fixture; no holdout read; closed by the principal.**

**Volume as a universe average is nearly flat** (D434: five volume axes through the D392 atlas,
next-open fill, `[F]`-aligned after a first run that was one bar early). **Conditioned on the
atlas states it is not** (D435): a 3× volume day is **+38 bp** in top-momentum names and **−48 bp**
in top-price names over the kernel's horizon, and the average hid the sign flip. The principal
called for the conditional atlas; it is the method finding of the line.

**The one component that survived every stage** — B, `rv_x3 ∧ price_hi`, sold short — carries
**+13 bp at 5 bars to +37 at 60** above a state-matched control's p95 (random names in the same
price tercile, same day, no shock), and its increment lives in the widest spread tercile of its
names (D438). As a book at cap 20 (D440):

| line | per trade | book, bp/bar | SE |
|---|--:|--:|--:|
| gross | +38.8 | +2.24 | 0.89 |
| crossed (PUB 2c + borrow) | −18.3 | −0.63 | |
| passive at the open (§62's assumption) | +7.1 | +0.65 | 0.89 |

The passive line does what §62 says it does — 2c falls from 52 to 32 per trade — and the book is
+0.65 on an SE of 0.89, with 16 names to half the P&L and the top 1% of trades at 108% of it.
**Not distinguishable from zero on sixteen years; the object's edge is a median of +14 under a
mean of +39.** The line is parked on the quote pull (D441): if B's wide names' modelled 42 bp a
side is a range, the wide tercile's +64 passive net is closer to a crossed net; if it is a quote,
the line is closed on cost.

---

## 64. Net share issuance predicts the hedged return of the name per trade on both sides, on the dead-inclusive fixture, against the right control — and the book it makes is under one SE on thirteen years

**D443–D453, 2026-09-11/12, in-sample; no holdout read; parked by the principal as real and
unbookable.**

**The source.** Alpha Vantage's fundamentals serve **0 of 562 dead names** (D443, abandoned on its
pre-registered coverage condition); the SEC's XBRL companyfacts serve **433 of them** (D444), with
the filing date of every value and restatement on 0.1% of share counts, so first-filed is
point-in-time for free. 11% of the fixture (multi-class and foreign filers) has no undimensioned
share count in that API. Filers mis-scale counts on 0.2% of rows (a 50× guard). The vendor's
counts agree with the first filing within 1% on only 45% of overlapping name-quarters.

**The object** (one-year log change in split-adjusted shares, usable from the filing date):
persistence **0.54** a year out on 1,250 names, rank R² on the six axes the repo had tested
(momentum, 20-day return, price, size, volatility, dollar volume) **0.10**, correlation with
momentum **+0.04**. It is tilted to small, cheap, volatile, thin names and is not any of them.

**Per trade** (D446: decile slot book, 40 a side, 126-bar hold, 1,055 short / 1,063 long trades),
against random names in the same price × volatility × momentum cell on the same day:

| side | gross | cell baseline (C1 p50) | increment | distance |
|---|--:|--:|--:|--:|
| short, net issuers | +72 | −97 | +169 | 2.6 control-SD |
| long, net repurchasers | +208 | +34 | +174 | 2.5 control-SD |

**The cell baselines are the finding as much as the increments:** shorting small volatile
names loses 97 bp a half-year hedged and buying large low-volatility ones earns 34, so the raw
means overstate on both sides and a study without the cell control would have read +208 as
edge. The distances are in the control's own draw SD; the per-trade SE is not a sampling error
here because forty six-month positions overlap almost completely (D446 addendum).

**The book.** +2.30 ± 1.51 bp/bar gross (D446); the score panel rolled in time by a common
offset, exact on a 21-bar grid, earns **+1.12 with p95 +3.77** — a persistent selector on the
wrong dates still picks the same kind of name and that composition earns hedged. The name-
randomised persistent selector earns +0.39. The alignment term is therefore about **+1.2 bp/bar
on an SE of 1.5**; net of the crossed line +0.97 at 0.6 SE; five names to half the P&L,
GameStop's January-2021 squeeze (entered 2020-10-15 as a repurchaser) 29% of the long leg.

**Beta-hedging and vol-scaling the same trades (D453)** cut the SE to 1.17 at the same gross,
halved the lottery (9 names to half, GameStop 10%), and **did not touch the rotated base rate**
(+1.12 → +1.27) while the name-randomised one fell to +0.08: the composition premium is a factor
tilt of the deciles' names (low-volatility / quality), not a unit-beta hedge error. Verdict
unchanged: net +0.86 ± 1.17.

**What it is:** the literature's investment-factor premium, about 2% a year net at a Sharpe near
0.2 if every number were confirmed, on a sample too short to confirm it. Real; factor-grade; not
a strategy for either book here.

---

## 65. An insider's open-market purchase is followed by +89 bp hedged over the next quarter, +65 over its cell, in the body of the distribution — and nets zero at the crossed line

**D454–D455, 2026-09-12, in-sample; no holdout read; parked by the principal.**

**The source.** The SEC's Form 3/4/5 bulk data (81 quarterly archives, 2006–2026), mapped by CIK
through D331's resolution: **17,270 purchase filings 2010–2023 on 76% of the fixture and 71% of
the dead cohort**, 90% filed within the statutory two business days. Map by CIK, never by ticker
(17,709 filings match a fixture symbol that belongs to another company). Ten-percent owners are
18% of filings and nine of the ten largest dollar buys (Roche in FMI, Berkshire in BAC) — a
different mechanism, set aside. Hyster-Yale's sixty-odd family trusts each file as a reporting
owner and are every top "cluster" without a guard.

**The shape.** Insiders buy what has fallen (47% of purchases after a bottom-tercile 20-day
return), what is small, cheap and thin (60% in the bottom dollar-volume tercile), and a second
insider buys the same name within a week on 47% of filings. Sales outnumber purchases six to one.

**The event study** (D455: non-10%-owner filings ≥ $25k, entered at the next open, 63-bar hold,
4,086 trades):

| | per trade |
|---|--:|
| gross, hedged | +89 (median +96, 1%-trimmed mean +89) |
| state-matched cell baseline (C1 p50 / p95) | +24 / +72 |
| increment | +65, 2.35 control-SD above the median |
| clusters (≥ 2 distinct buyers) / single buyer | +120 / +54 |
| directors only / officers only | +101 / +58 |
| sales mirror, shorted | −23 ± 12 (sales carry no information) |

**The book:** +1.11 ± 0.56 bp/bar gross; the rotated calendar earns +0.66 (beaten-down small
names recover on average, hedged); the alignment adds +0.45; the crossed line costs 1.03; net
**+0.08**. Passive net +0.62 at 1.1 SE. Shortening the hold to 21 bars triples the gross and the
cost. The top name is 6% of the P&L across 865 names — this one is not tail-carried.

**Not overstated:** 2.35 SD is a p of roughly 0.01 on one look; the increment is +65 bp a
quarter; the trade lives where a quarter's round trip costs what the quarter earns.

---

## 66. No 8-K item type carries a ten-day drift after the next open: the reaction to a filed event is in the gap, the distress items rebound, and every 8-K filer drifts up ten basis points against quiet names

**D456–D457, 2026-09-12, in-sample 2010–2023; the 2024–2026 slice parsed and unread; closed at
stage 1 on its own family bar.**

**The source.** The EDGAR submissions index D331 cached: **154,970 8-Ks on 82% of the fixture and
81% of the dead** (the gap is foreign 6-K filers), filed the day of the event (earnings) to two
days after (most items), 15 item cells with ≥ 300 filings.

**The atlas** (17 cells × all/pure × both sides, 10-bar hold, the state-matched control — same
day, same cell, no 8-K of any item within ±5 bars — and the exact rotation of each cell's
calendar on every cell; a family of 34 tests with 0.85 chance clears on the first control and
0.04 on both): **0 cells clear both; 4 clear the first** (earnings 2.02 at z 4.8, other events
8.01, shareholder votes 5.07, delisting notices 3.01), **all on the long side**.

- **After any 8-K the name does +8 to +16 bp better over ten bars than a quiet name in the same
  cell** — and the rotated calendar earns the same +0.7 to +1.1 bp/bar, so it is the filers'
  composition, not the filing's timing. A tenth of the round trip.
- **The distress items are long-favoured after the next open** — impairments +59, delisting
  notices +103, auditor changes +92 per trade — with **negative medians**: the fall is in the gap
  the daily fixture cannot enter; what follows is a two-sided rebound on survival. Every
  pre-registered short-side sign was wrong.
- Officer departures (5.02): −5 bp over ten days, the one short below the rotation band; a
  twelfth of the cost.

**The one-line lesson of §63–§66 together:** on this fixture every information source outside
the price path — volume conditioned on state, share supply, insider demand, the corporate-event
calendar — produces a real per-trade effect against a control that was built to kill it, and
none of them survives either the cost of the names it lives in (a quarter's hold in thin names
costs ~1 bp/bar, the alignment term is ~1 bp/bar on an SE of 1) or the gap it is priced in. The
sentence that is true of all four is not "no signal"; it is "no book at this cost model on this
fixture," and §62 says the cost model is unmeasured.

---

## 67. Method: three controls for a persistent state, and what each one's median means

Out of D446–D457 (2026-09-11/12), a template now used on every line:

1. **State-matched random names, per trade.** Same day, same price × volatility × momentum
   cell, same count, no event of the kind under study nearby. **Its median is not zero and is
   the first number to read:** −97 and +34 per half-year trade on the issuance cells, +24 per
   quarter on insider cells, −3 to +22 per ten days on 8-K cells. Report the real mean's distance
   in the control's *draw SD*, not in the Monte-Carlo precision of its p95 (D446 addendum: "25
   SE" was that error; the true distance was 2.6 SD).
2. **The common-offset rotation of the whole panel or calendar, exact on a grid.** Keeps every
   name's own persistence and the composition; destroys alignment. **Its median is the
   composition's base rate** — +1.1 bp/bar on the issuance deciles, +0.7 on 8-K filers — and a
   beta hedge does not remove it (D453).
3. **The name-randomised persistent selector** (or per-name shuffle for events). Keeps the
   churn; destroys which name. The gap between (2)'s and (3)'s medians is the price of the
   state tilt; predict (2)'s median from (1)'s baselines, not as zero.

And one arithmetic rule from the same studies: with N concurrent positions held H bars, the
per-trade SE is not a sampling error of the mean — the block-bootstrap SE of the deployed book
is — and a filing-based event should have its expected crossed cost per bar computed from the
hold and the names' half-spread *before* it is pre-registered.

## 68. The daily channel line (D399–D483): its direction is worth nothing by any reading, and its level's one positive cell is a dip with no lines

**Closed by the principal, 2026-09-12** —
[closing record](decisions/D483-CLOSE-the-daily-channel-line-D399-to-D483.md).

A causal daily channel from confirmed pivots (D399), rebuilt three ways — the oracle's greedy
window search made causal (D478), with hysteresis and trend-side breaks (D479), and re-dialled
against the principal's own 140 hand-drawn lines (D480; sign agreement 92 / 87%, recall 69 / 71%)
— and traded three ways:

- **Direction** (target-and-trail D476; hold-while-a-trend D477, D478, D479, D481): five causal
  cells, long +1 to +17 bp gross, short −39 to −54, **every one below a within-name time rotation
  of its own trades** (the null's long p50 +37 to +59 against scores +1 to +17), and worse as the
  gradient floor rises in every sweep. The cell that draws the principal's lines and confirms
  five bars before the principal does trades the same (+12.3 ± 3.4). A confirmed direction is a
  late one however early it is confirmed.
- **The oracle** (D477): hindsight windows with their boundaries hidden from the trader earn
  +780 to +1,272 bp a trade at 84–93% win rates — a tautology, since a channel that exists at t
  was selected by what follows t. Not a ceiling.
- **Level** (D482): long on a close at or below the bottom tenth of the channel (support 4% under
  the pivot lows), held 5 bars: **+43.6 ± 5.6 gross, median +58, 41 SE above its null**, 52
  names to half the P&L, net −34; net +37 at 20 bars, 20 SE above its null there. The first
  channel cell to meet the programme's signal criterion.
- **The control** (D483): a close 4% below the previous 30 bars' low with **no lines at all**
  earns **+47.4 ± 10.1** over 5 bars (above its null), and inside a live channel +45.2. The channel
  adds nothing beyond the first day. The short side of the dip earns +24. What D482 found is
  short-horizon reversal after a sharp break of a range, both directions, ~5–9 bp a bar for
  twenty bars, net negative to ~15 — real here, not new, not the channel's.

**Method findings that outlast the line.** (i) A hindsight channel leaks the future through its
*existence*, not its boundary. (ii) "By eye" became a labelled set: 140 lines drawn one bar at a
time with the future hidden, each with its draw and end bar, and a scorecard against them —
the principal's anchors sit 4% outside the wicks, draw one bar after the second swing, live 26
bars, and end 45% on a break, 40% by replacement, 15% by drift; on that card the pivot
envelope over several confirmed pivots matches the eye's gradient and a two-point zigzag line
does not. (iii) Overstay must be scored only on ends that were ends: 40% of the principal's ends
were replacements. (iv) A within-name rotation null re-times events; it does not control for
what the event *is* — the dip control had to break the ingredient.


## 69. Measurement: what a prop day-session candidate must clear — the fee is 2.4% of the move, the barrier is 3–6 σ, and the two are one constraint

**A MEASUREMENT, not a verdict.** It opens and closes nothing ([R15](RULES.md#r15)); it states,
in the units the venues use, the specification any future prop candidate faces. Computed on
committed fixtures (D467's
hourly session tables and `data/futures_contract_specs.json`) plus
[D493](decisions/D493-RESULT-the-account-size-lever-fixes-the-fee-and-runs-into-the-barrier-a-full-contract-dies-in-weeks-at-every-plan-and-nothing-the-programme-holds-is-carryable.md).
The D467 fixture record is
`docs/decisions/D467-RESULT-eight-roots-of-hourly-session-tables-pass-five-gates-from-2016-after-two-gate-amendments-on-holiday-prints-and-the-partial-pre-2016-sessions.md`.

**(a) At day-session scale, cost is not the binding constraint.** Average 10:00→16:00 ET move
against the $3.00 + 1.009-tick round trip, 2016–2023:

| micro | avg move | cost / round trip | cost as a share of the move | daily σ |
|---|---:|---:|---:|---:|
| **MNQ** | $143.11 | $3.50 | **2.4%** | $219 |
| MES | $90.47 | $4.26 | 4.7% | $139 |
| MYM | $69.44 | $3.50 | 5.0% | $106 |
| MCL | $72.57 | $4.01 | 5.5% | $103 |
| MGC | $59.63 | $4.01 | 6.7% | $85 |
| M6E | $55.36 | $4.26 | 8.0% | $76 |

**The Nasdaq micro is the best hunting ground for any day-session rule, not crude.** Break-even
there is **51.2% directional accuracy**, and a component Sharpe of 0.5 at one micro needs
**53.6%** — about $10.40 of gross a session. The log MACD ([D484](decisions/D484-RESULT-the-log-MACD-is-a-real-signal-that-fails-only-on-cost-and-the-off-diagonal-ordering-is-confirmed.md))
reaches ≈ 50.7%. **The gap is three points of accuracy, not cost.**

**A corollary that kills a plausible lever.** Selecting high-volatility days to raise the move
against a fixed fee only pays where cost/E|M| is large — scalping, or the 15-minute bar
([D472](decisions/D472-RESULT-the-volume-clock-exit-replicates-8-of-8-years-but-the-15-minute-horizon-does-not-survive-its-own-scoring-window.md)).
At 2.4% there is almost nothing to win.

**(b) The fee and the trailing barrier are one constraint, seen from two sides.** D493 ran every
published plan × ES/NQ × micro/full × 1–5 contracts through D386's lifecycle: **0 of 448 cells
carry.** Leaving the micro fixes the fee (NQ's last-30 trade goes from a net Sharpe of −0.13 at
one micro to +0.48 at one full contract) and immediately exposes the barrier — a full contract's
daily σ is **3–6× the plan's $2,000–$4,500 trailing drawdown**, so funded life is **0.03–0.16
years on all fourteen plans**. The micro sits ~40 σ from the barrier and loses on the fee.
**The account's dollar drawdown fixes the σ per contract it can carry, and that σ fixes the fee
in ticks.** Positive-value cells are lottery tickets: a fast pass, one payout, then the breach.

**(c) What has been measured against this specification, and come up short.** Direction from
outside the instrument's own price path, at session resolution, is worth **at most one tick a
day**: eighteen declared cells in [D494](decisions/D494-RESULT-outside-the-price-path-on-the-day-session-eighteen-cells-no-pick-the-largest-is-the-euro-at-one-tick-and-the-release-day-MACD-is-worse-not-better.md)
— five cross-instrument overnight moves, index-level retail sentiment, and CPI / payroll / FOMC
gates — produced no pick, the largest being the euro into ES; and the scheduled prints make the
one real signal on the table earn *less*, because the day leg starts ninety minutes after 08:30.
The four-quadrant open-interest read ([D497](decisions/D497-RESULT-the-four-quadrant-open-interest-read-carries-nothing-the-open-interest-term-flips-sign-between-index-and-commodity-roots-and-the-textbook-reading-is-backwards-on-gold.md))
carries nothing on four roots, and on gold the quadrant the textbook says to fade is the most
positive one.

**Two method notes worth carrying.** Open interest is **distinguishable from volume** — the two
give answers differing by 3× and flipping sign — so neither may be dismissed as a proxy for the
other without testing. And twice in one session a check could not do its job: a shifted-predictor
control whose window **overlapped the outcome** (it measured spillover and came out above its
null), and a roll gate whose threshold its own series made **unreachable**. Both were withdrawn
in their records rather than reported as passes; CLAUDE.md's *"a self-test that cannot fail is
worse than none"* applies to gates and controls, not only to the deliberate `[X]` break.

## 70. Measurement: the hourly clock on eight CME roots — the off-hours reversal is real on the US clock, worth a tick, and the fee is 7–24% of the hourly move

**A MEASUREMENT, not a verdict** ([R15](RULES.md#r15)). From
[D499](decisions/D499-RESULT-stage-0-CLOSE-the-hour-after-a-large-move-reverts-in-the-US-off-hours-on-the-index-roots-and-is-worth-less-than-a-tick-no-cell-of-16-clears-the-family-bar-or-the-fee.md)
(stage 0 on D467's hourly session tables, eight roots, 2016–2023, 2024+ unread).

**(a) The reversal exists on the US clock and not on the volume partition.** Pooled β of the next
hour on the last hour, over h18 … h08 ET, against its exact rotation band (±0.014):

| root | off-hours β | day-session β | outside its band |
|---|---:|---:|---|
| ES | **−0.043** | +0.004 | yes |
| YM | **−0.037** | +0.012 | yes |
| NQ | **−0.028** | +0.007 | yes |
| CL | **+0.030** | −0.010 | yes — crude **continues** |
| ZN, ZB, GC, 6E | −0.012 … +0.007 | ≈ 0 | no |

Partition the same 21 entry hours by **volume** instead and the effect vanishes: the pooled β is
inside its band on seven of eight roots. The reason is that **London (h03, h04, h07, h08) is thick
by volume on every root** — ZN's h03 trades 45,097 contracts against h00's 7,012 — so the
volume-thin set and the US-off-hours set are different objects. A study that says "thin book" and
partitions by clock is not testing thinness.

**(b) And it is worth a tick.** Fading a top-decile hourly move through the off-hours: ES +$2.12 a
trade (1.7 ticks, +1.3 bp, z +2.10 against an exact-rotation p95 of +1.68), NQ +$2.44 (4.9 ticks,
+1.1 bp, z +1.82 vs +1.56). Both clear their own null; both are **net negative after the $3 fee**
(−$0.88, −$0.56) and further after the crossed tick. This is the same size as D487's last-half-hour
reversal and D494's best cross-instrument read: **one tick is what direction at session resolution
has been worth here, three times now, by three unrelated routes.**

**(c) The fee against the move, per horizon — the number that closes the clock.** Fee ($3, or $6 on
ZN/ZB) as a share of E|next-hour move|, averaged over the thin / thick hours, with the day-session
line of §69 beside it:

| | hourly, thin | hourly, thick | day session (§69) |
|---|---:|---:|---:|
| MNQ | **14.5%** | 7.1% | 2.4% |
| MES | 21.0% | 10.8% | 4.7% |
| MCL | 23.5% | 12.3% | 5.5% |
| MGC | 20.3% | 13.6% | 6.7% |
| MYM | 26.4% | 13.6% | 5.0% |
| M6E | 44.7% | 26.3% | 8.0% |

Break-even accuracy on MNQ's thin hours is **57.2%** (thick 53.5%) against the day session's 51.2%;
observed conditional hit rates across all sixteen cells are 46.5–53.1%. On ZN and ZB one crossed
tick is $15.63 / $31.25 against an expected hourly move of 2.8–4.5 and 3.3–5.6 ticks, so
fee-plus-tick is **19–80% (ZN) and 14–58% (ZB) of the move in every hour**. **Shortening the horizon multiplies the fee against the move
by 3–6× on the index micros and makes the large-tick roots untradeable; the accuracy needed rises
past anything measured in this programme.** The corollary of §69 (a) — that selecting bigger moves
cannot pay when cost/E|M| is already small — runs the other way here: at an hourly horizon the
ratio is large enough that only a per-trade move several times the hourly σ could carry it, which
is a different clock, not a better signal.

**(d) A mechanism claim that came out backwards.** The transitory-impact story predicts that a large
move on *low* relative volume reverts more. It reverts **less**, on seven of eight roots (YM −$6.19
a trade, z −2.1; the rest within 2 SE). A move that arrives on little volume in these markets is
more often the start of something than an inventory shock. **Whatever the off-hours reversal is, it
is not thin-book impact** — the one partition built to test that is the one that shows nothing.

## 71. Measurement: the Asian chip channel into US semiconductors is real, semis-specific, and clears ENTIRELY in the opening gap

**A MEASUREMENT, not a verdict** ([R15](RULES.md#r15)). From
[D504](decisions/D504-RESULT-stage-0-CLOSE-the-Asian-chip-channel-is-real-and-clears-entirely-in-the-gap-25-6-bp-into-the-gap-and-nothing-into-the-day-and-transports-beat-semis.md)
(1,324 sessions on the 15-minute ETF fixture, 2018-01-02 → 2023-12-29; 2024+ reserved and unread).

**(a) The channel is there and it is sector-specific.** The overnight gap of SMH relative to QQQ
loads **+0.45 on the EWT gap** (Taiwan, roughly half TSMC), +0.40 on EWY (Korea) and +0.37 on EWJ.
It is not a market-wide effect dressed up: the same Asian sessions load ≈ **0.50 on BOTH the NQ and
the ES** Tokyo-hours return, so an index-level or futures-only expression captures the market
component and only 0.20–0.30 of the tech tilt. **The Asian *level* signal and the Asian *relative*
signal are different objects and a study must say which it uses.**

**(b) And the gap is where it clears, completely.** One regression, Newey-West(5), n = 1,073, with
the Asian chip signal standardised causally and measured relative to QQQ:

| | bp per unit z | t |
|---|---:|---:|
| into the semis' relative opening GAP | **+25.65** | **+4.25** |
| into the relative DAY SESSION, 09:45 → 16:00 | **−1.65** | −0.64 |

**Twenty-six basis points of Asian information is in the price by 09:45 and nothing measurable is
left.** A conditioner measured to the close of the 09:30–09:45 bar, traded from the 09:45 open to
the close, earns +8.0 ± 8.4 bp before a crossed cost of 11.7 bp, with yearly means of +5, −27,
+39, −5. **This is the cleanest gap-versus-day decomposition in the repo, and it is the reason the
ADR-style "closed market" mechanism does not pay at a tradeable horizon: the US open is an auction
that prices exactly this.**

**(c) The control that beat the treatment.** On the same signal, **transports (IYT) against QQQ
earned +27.97 bp a trade, hit 61%, and cleared its own exact rotation at the 0.8th percentile** —
with no mechanism from Taiwanese semiconductor gaps whatsoever. Banks and homebuilders also beat
SMH. The eleven-cell family p95 is +2.56 against IYT's +2.26, so the family bar refuses it; single-
cell scoring would have called it a find. **Keep a mechanism-free sector control in any study whose
conditioner is a foreign market** — it is the cheapest way to see the family for what it is.

**(d) A sub-micro exposure exists, and it is a spread.** On the same window, the daily σ of the
unconditional MNQ/MES day-session pair is **$128 against $282 for one MNQ** ($135 vs $273 in 2023
alone), with zero days beyond −$1,000 in six years against the single micro's 0.2 a year. D503
established that one micro no longer fits a $50k account's $2,000 trailing floor at 2026 prices
([[one-micro-has-grown-into-the-prop-barrier]] in memory; §69 (b) for the identity). **A hedged
micro pair is the only construction that lowers the dollar σ without leaving the micro** — the
dollar beta of NQ on ES is 1.72, so 1:1 under-hedges and 1:2 over-hedges at $9 a round trip. This
closes nothing and sizes nothing; it says the vehicle question has at least one unexplored answer.

## 72. Measurement: selectivity is a drawdown instrument, not a selector — and by 09:30 the information is spent

**A MEASUREMENT, not a verdict** ([R15](RULES.md#r15)). From
[D506](decisions/D506-RESULT-stage-1-CLOSE-in-play-selection-costs-more-accuracy-than-the-fee-it-saves-but-it-cuts-the-breach-rate-3-to-5-fold.md),
eight roots × two signals, ~1,700 sessions each, 2016–2023; 2024+ not read. The conditioner is
causal and known before the open: the overnight leg's range and volume, each against its own
trailing 20-session median.

**(a) The fee lever is real and small, and it is measured.** Selecting the top causal decile raises
E|M| by ×1.15 to ×1.94 and cuts the fee's share of the move — ES 3.3% → 1.8%, NQ 2.1% → 1.2%, YM
4.4% → 2.3%, 6E 9.7% → 7.1%. In `(2p − 1)` terms that is **+0.85 points on average, positive in 16
of 16 cells**, worth about **+0.10 of Sharpe** at `√252/c` with `c = σ/E|M| ≈ 1.4`.

**(b) And directional accuracy falls by more than twice that.** `p(in play) − p(rest)` is **−2.09
points on average, negative in 11 of 16 cells**, so the primary statistic is negative in 9 of 16 and
no cell clears the family bar (p95 +0.2192 against an observed maximum of +0.0620; 97.8% of the
1,978 exact offsets beat the best real cell).

**(c) The reason, and it now has three independent confirmations.** A night that moved a lot has
already spent the information. [§71](#71) measured the Asian channel clearing entirely in the
opening gap (+25.65 bp into the gap, −1.65 into the day); [§70](#70) measured the off-hours move
partly reverting in the following hour; this measures the day session after a big night being
*harder* to call. **The US open is an auction that prices the night, and conditioning on a big night
selects the sessions with the least left to give.** The decisive figure is the *untradeable* bound:
conditioning on the day's **realised** range, which no one can do in advance, is **−0.0018** on the
primary. There was no prize to win even with perfect foreknowledge of the day's size.

**(d) But the same filter is a drawdown instrument, and a strong one.** R11's P3a bar is 1.0
breaches a year. Trading only the top decile cuts the rate three to five fold, because both prop
death mechanisms are counted in **exposure-days** and a filter that removes 90% of the sessions
removes 90% of the chances to die — even though each session it keeps is individually more
dangerous:

| | P3a, all sessions | P3a, top decile only |
|---|---:|---:|
| ZB | **14.00 a year** | **2.71** |
| ZN | 2.00 | 0.71 |
| NQ, the drift | 0.57 | 0.00 |

**Selectivity therefore belongs in the sizing and survival layer, not the signal layer.** It is
worth reaching for when a construction fails P3a and nothing else, and it is worth nothing as a way
to find direction.

**(e) A correction to §69's accuracy targets: they assume symmetric payoffs.** The long day-session
drift reaches **55.7% on ES, 55.2% on NQ, 54.4% on YM** — above §69's "53.6% for a component Sharpe
of 0.5" — and earns net Sharpes of **+0.02, +0.11 and −0.31**, because it wins often and loses big
(skew −0.30 to −0.38). `(2p − 1)·E|M|` overstates the realised edge by **2× to 13×** across these
sixteen cells. **Quote the payoff ratio beside any accuracy target, and never treat accuracy alone
as sufficient.**

**(f) And one more reason to distrust a pooled risk figure.** The traded day move's σ at one micro,
within the in-sample window alone: NQ $60 (2017) → $287 (2020) → **$452 (2022)** → $274 (2023); ES
$42 → $264 → $154; ZB $475 → $929. **A 4× to 7× swing inside one window.** D503 established the
point forward; this establishes it in sample. Every C-d, P3 and P4 number must be computed per year.

## 73. Method: a SLOW conditioner has n_eff in years, not sessions — count the years containing both of its states before designing anything around it

*From [D526](decisions/D526-the-curve-story-fails-stage-0-the-level-is-a-regime-and-the-change-carries-nothing.md),
which is the third record to hit this, and the first to name it. Closes nothing; it is a constraint
on how a conditioner may be tested.*

**The trap.** A conditioner is split into terciles over the pooled in-sample window, each cell gets
several hundred sessions, and the cells' outcomes are compared. If the conditioner is persistent
enough, **the terciles are calendar periods wearing state labels** and the comparison is between
eras — confounded with volatility regime, price level and every crisis in the window. The cell
counts look reassuring and are not independent observations.

**The measurement that exposes it, and it costs one line:** *how many years contain at least twenty
observations of BOTH extreme states?*

| record | conditioner | autocorr at 1 session | years containing both states |
|---|---|---|---|
| D508 | log(price / 200-day MA) | — | it *"ranks YEARS, not sessions"* |
| D512 | log(EMA50 / SMA200 of the range) | — | the effect was NQ's own history; did not transfer |
| **D526** | CL front-to-next settlement spread | **+0.943**, sign flips 3.8 % | **0 of 8** |
| **D526** | GC front-to-next settlement spread | +0.826, sign flips 5.7 % | 5 of 8 |

On CL the year-by-year payoff gap is computable in **no year at all**, and the pooled tercile
comparison that looked like a result (payoff 1.087 contango against 0.867 backwardation, skew +0.39
against −0.59) is an artefact of **2020 sitting inside the contango bucket** — that bucket's
day-session σ is 226 bp against 159 and 179 for the other two.

**The rule.** On a daily clock with an eight-year window, **a conditioner slower than about a month
cannot be tested cross-sectionally.** Where it fails, the testable object is its **change**, which
does have within-period variation — D526's `d(curve)` carries both extremes in **8 of 8** years —
and the change must then be scored **year by year and never pooled**: CL's steepening-minus-
flattening payoff gap reads −0.038 and is positive in 3 of 8 years, GC's −0.005 and 3 of 8, while
GC's *pooled* gap of +0.131 looks like something and is not.

**Second-order, and it decided D526's check 2.** A conditioner can look collinear with momentum on
Pearson and be independent on ranks: CL's curve against the trailing 60-day return reads **pearson
+0.498 against spearman +0.162**, the Pearson being a handful of extreme joint observations. **Report
both, and let the rank statistic decide** whether a conditioner is a price signal in disguise.


## 74. Measurement: the directional base rate is NOT 50 % — it runs to 54.7 % on the equity indices and BELOW 50 % on natural gas, and it is root- and horizon-specific

*From the [D531 addendum](decisions/D531-ADDENDUM-the-breakout-loses-to-the-base-rate-48-of-48-and-the-base-rate-is-not-50-percent.md),
on the principal's challenge. Closes nothing; it is a constraint on how a directional statistic may
be referenced.*

**The trap.** A directional hit rate is compared against 50 %, on the reasoning that a coin flip gets
50 %. It does not. Price drifts, the drift differs by root and it compounds with horizon, so the
reference for "no information" is the probability of that move **at that moment on a different day** —
not one half.

`P(up move)`, measured by holding the bar index fixed and rotating the session, which absorbs the
drift and the intraday shape together. In sample 2016-2023, five-minute bars:

| root | 15 min | 30 min | 60 min | 120 min |
|---|---:|---:|---:|---:|
| **ES** | 52.64 | 52.85 | **53.56** | **54.70** |
| **NQ** | 52.68 | 53.13 | 52.94 | **54.39** |
| CL | 50.26 | 50.74 | 50.79 | 50.90 |
| GC | 50.89 | 50.21 | 50.05 | 50.83 |
| SI | 51.24 | 50.77 | 50.16 | 49.95 |
| **NG** | **48.88** | **48.88** | **48.77** | **48.55** |

Estimated independently from two disjoint event sets, agreeing to **0.2 points**.

**The size of the error.** Referencing 50 % overstates a long on ES at two hours by **+4.7 points**
and understates a long on NG by **1.5**. It is always in the direction that flatters a long and
punishes a short — and this programme's admitted arm is long-biased in a rising sample.

**What it cost.** D531's addendum reported an ES upside-break hit rate of 55.08 % as "+3.2 SE"
against 50 %. Against its true base rate of 53.56 % the lift is **+1.53 points, with 18.3 % of
rotated draws reaching it** — inside the null. The finding evaporated on the reference alone. Across
48 cells the mean lift over base rate was **−1.23 points and nothing cleared**, where against 50 %
the same numbers had looked like a real asymmetry.

**The rule.** Reference a directional hit rate against the **rotated base rate at the same clock
position**, never against 50 %. A rotation null on a fixed price path (D529's) already does this
implicitly, because rotating the signal preserves whatever the price did; a bare hit rate does not.
Where a study cannot rotate, quote the base rate from this table beside the statistic.

## 75. Method: an EXIT rule scored on directional accuracy answers a different question from the same exit rule scored in dollars — and D533 got opposite answers from the two

**D533 pre-registered four conditions on one statistic: the directional hit rate against the rotated
base rate. Three were entry filters and one, C3, was an EXIT rule. On that statistic C3 was the worst
thing in the study — a lift of −3.95 and −3.03 points against the fixed 60-minute exit, the largest
single effect measured. In dollars at minimum tradable size the SAME rule raised gross Sharpe on all
four roots (book +0.80 → +1.03) and produced the only positive net book in the record.**

**Why the two disagree is not subtle, and it is D529 restated:** the exit cut the mean hold from 12.0
bars to 7.9 while raising gross dollars per trade (SI 2.24 → 3.48) and lowering the hit rate
(47.1 % → 39.8 %). It cuts losers faster than winners. **A hit rate cannot see that**, because it
scores the sign of each trade and is blind to the magnitudes the exit is rearranging. The hit rate is
the edge; the payoff ratio is exit geometry.

**Two corrections fall out, and the second is the one that bites:**

1. **Score an exit rule on the P&L distribution, never on a hit rate.** An entry filter changes which
   trades happen and a hit rate is a fair instrument for it. An exit rule changes the shape of trades
   that were happening anyway, which is the one thing a hit rate discards.
2. **The dollar reading was not pre-registered, so it is a lead and not a result.** The net book
   Sharpes are −0.11 and +0.09 against an SE of **0.36**, no null has been run against them, and the
   cell was picked out of a table read after the fact. **And the symmetric trim deflates it further:**
   C1+C3's advantage over C1 alone is entirely in the tails (trimmed +4.14 against +4.31), so C3 buys
   a shorter hold rather than a larger edge, and +.31 gross does not cover a .00–.00 round trip.

**The rule.** Declare the statistic that matches the OBJECT: hit rate for what selects trades, the
P&L distribution for what shapes them. Where a study declares both an entry and an exit — as D533
did — it needs both statistics pre-registered, or the exit arm of it cannot resolve.
