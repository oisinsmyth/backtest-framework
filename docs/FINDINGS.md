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
instruments, **should carry a volatility split**; PICKUP.md already records SPY and QQQ disagreeing
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
