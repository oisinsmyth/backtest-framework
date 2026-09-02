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

**What is live after D279 and D280:**

1. **[D281](decisions/D281-the-unfiltered-ranking.md) — rank the whole universe, removing the
   filter/ranking collision and changing nothing else.** Pre-registered; **result pending.**
2. **[D282](decisions/D282-the-overnight-only-short.md) — the cost arithmetic of the overnight construction part 4 implies**, ~252 round trips a
   year against D265's `2c` bar. Pre-registered by another agent; **result pending, and nothing here
   predicts it.**
3. **The volatility tilt of D280 part 4C** — `zh + zv + za + zr` at IC **−0.01373 (t −5.07)**, the
   only other statistic in that record to clear its own multiplicity. **It is a volatility tilt, not
   a stronger `hist_L`**: flip `zr`'s sign and the IC goes positive, it does nothing on the
   qualifying set, `zr` alone was never scored, and no book, cost model or `sigma^2` tax has touched
   it.
4. **The factor-neutral branch of §9, still untouched** after D256, D264, D279 and D280.
5. **Nothing reaches [R8](RULES.md#r8).** D279 produced no candidate, so there is nothing to take out
   of sample, and **D246's reserved wide-universe cohort remains unspent** — which is the one good
   outcome of catching the defect before a holdout was designed around it.
