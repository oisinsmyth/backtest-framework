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
