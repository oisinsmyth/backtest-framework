# Producer Hedging Flow in WTI: A Derivation from Mechanics

**Status:** first-pass derivation, pre-registration draft
**Scope:** US independent E&P hedging of crude oil, expressed in NYMEX WTI
**Sourcing:** covenant terms from credit agreements filed with the SEC; cost and expectation
data from the Dallas Fed Energy Survey; aggregate hedge ratios from published surveys
(Standard Chartered, Evaluate Energy, Wood Mackenzie, Haynes Boone). Figures below are
as found in September 2026 and should be re-verified before use.

The goal is to separate what is **derived** (from published constraints), what is
**bounded** (by documents or aggregation), and what must be **estimated** (from data), so
that the estimated part is as small as possible and the multiplicity budget is spent only there.

---

## 0. Summary of the result

Hedging demand from a producer with a mean-reverting price belief and mean-variance risk
preferences is:

```
h*(F) = clip( 1 − (μ − F) / (2λσ²) ,  h_min ,  h_max )
```

where `F` is the strip price at the hedge tenor, `μ` the producer's expected spot, `σ` the
volatility at that tenor, `λ` risk aversion, and `h_min`, `h_max` the covenant floor and
policy/lender ceiling.

Everything qualitative about producer hedging follows from this one expression:

- **Hedge into strength:** `∂h*/∂F > 0` whenever `μ` is anchored below the strip.
- **Saturation:** flow → 0 as `h → h_max` regardless of price.
- **Floor-binding at low prices:** below the anchor, unconstrained `h*` falls toward zero and the covenant floor is the only thing holding the hedge on.
- **Asymmetry / ratchet:** lender approval is required to lift hedges, so `h` moves up easily and down slowly.
- **Calendar concentration:** covenant compliance is tested at semi-annual redeterminations, so floor-driven flow clusters before them.

The aggregate flow decomposes into four components, three of which are derivable in sign and
two in magnitude. **One free parameter** (`λ`, or equivalently the slope `∂h*/∂F`) and one
partially-observable one (`μ`) carry the estimation burden. The price impact of the flow is a
separate, empirical layer.

---

## 1. The mechanics, from primary sources

### 1.1 Population

The hedging population is US and Canadian independent E&Ps. Majors (ExxonMobil, Chevron,
ConocoPhillips) largely do not hedge crude and are excluded. Surveys of the hedging
population consistently cover roughly 30–40 companies:

- Standard Chartered (March 2025): 40 independents, combined **5.03 mb/d**
- Evaluate Energy (Q4 2025): 30 producers, ~**800 kb/d hedged ≈ 35%** of production for Q4 2025 / Q1 2026
- Wood Mackenzie (2023): ~40 independents

Private producers are missing from disclosure-based surveys but are partially captured in the
bank channel (§1.7) and in COT.

### 1.2 Covenant floor — `h_min`

Reserve-based lending (RBL) agreements contain minimum hedging covenants. Actual filed terms:

| Source | Requirement | Tenor |
|---|---|---|
| Riley Exploration Permian credit agreement (2019) | ≥ 45% of PDP production, rolling | 24 months |
| Breitburn Energy credit agreement (2017–18) | ≥ 50% of PDP + ≥ 20% of PDNP/PUD | 33 months |
| RBL amendment filed 2021 (EDGAR 1655020) | tiered: ≥ 65% / 50% / 25% by forward year | months 1–12 / 13–24 / 25–36 |
| Industry guide (2026) | typically 50–75% of PDP | 12–24 months |

The **tiered structure** is the important finding: `h_min` is not a scalar but a declining
function of time-to-delivery. This is the covenant origin of the hedge-ratio term structure
(§3.3). The floor binds only on RBL borrowers, which is a subset of the population — larger,
better-rated independents may have no such covenant.

Post-2014 crash, minimum hedge requirements were added or tightened across the sector
(Columbia CGEP, 2017). The floor is therefore itself regime-dependent.

### 1.3 Ceiling — `h_max`

- Breitburn: aggregate hedges may not exceed **90% of PDP** (plus a fraction of PDNP/PUD).
- Federal Reserve SR 16-17: institutions should **limit hedging to total production** to avoid over-hedging.
- Board hedging policies in disclosures typically cap at 50–85% of expected production.

`h_max` is a hard upper bound at 90–100% of PDP, with a softer policy ceiling below it.

### 1.4 Lifting restriction — the ratchet

SR 16-17: covenants should require **lender approval before lifting hedges** on which the
lender relies. Hedges can be added freely but removed only with consent or at maturity. This
is the source of the asymmetry in §2.4.

### 1.5 Calendar

Borrowing bases are redetermined **semi-annually**, spring (April–May) and fall
(October–November), against reserve reports effective January 1 and July 1. Haynes Boone
surveys the industry ahead of each season. Covenant compliance is assessed against the most
recent reserve report, so floor-driven hedging concentrates in the weeks before each
redetermination.

### 1.6 Cost structure and expectations — `c` and `μ`

Dallas Fed Energy Survey, Q1 2026 and Q1 2025:

| Quantity | Value | Role |
|---|---|---|
| Operating breakeven, existing wells (avg) | ~$41–43/bbl | absolute floor on willingness to hedge |
| Operating breakeven, large producers | ~$31/bbl | |
| New-well breakeven (avg) | ~$65–67/bbl; Permian $63–70 | threshold above which hedging locks in *growth* economics |
| WTI price used for 2026 capex planning | $59–60/bbl (mean/median/mode) | **direct proxy for `μ`** |
| Expected WTI, two years out (Q1 2026) | ~$73/bbl | alternative `μ` proxy |
| Expected WTI, five years out | ~$79/bbl | |

The planning price and the two-year expectation are quarterly, free, and are as close to a
direct measurement of the anchor `μ` as exists.

### 1.7 Execution channel — critical for measurement

Producers hedge predominantly **OTC with their lending banks** (swaps, costless collars,
puts). The bank then lays off its exposure in NYMEX futures. Consequently:

- Bank-intermediated producer hedges appear in the COT **Swap Dealer** short, not the Producer/Merchant/Processor/User category.
- Direct exchange hedges appear in **Producer/Merchant**.
- The measured hedger footprint is approximately `PM_short + SD_short`, with SD contaminated by non-producer swap clients (index products, consumer hedges on the long side, etc.).

Any test of this model that reads only the Producer/Merchant line will miss most of the flow.

---

## 2. The individual producer's problem

### 2.1 Setup

Per barrel of expected production at tenor `T`:

```
π = (1 − h)·S_T + h·F − c
```

`S_T` uncertain with `E[S_T] = μ`, `Var[S_T] = σ²`. The producer maximises `E[π] − λ·Var[π]`.

```
E[π]   = (1 − h)μ + hF − c
Var[π] = (1 − h)²σ²
```

### 2.2 First-order condition

```
∂/∂h [ E − λVar ] = (F − μ) + 2λ(1 − h)σ² = 0
```

```
h* = 1 − (μ − F) / (2λσ²)
```

Define the producer's **expectation premium** `p ≡ μ − F` (how far above the strip the
producer expects spot to land). Then:

```
h* = 1 − p / (2λσ²)
```

Read-off:

- `p = 0` (no view): `h* = 1`. A pure risk-averter with no view hedges everything.
- `p > 0` (bullish vs strip): `h* < 1`, declining linearly in `p`. Reaches zero at `p = 2λσ²`.
- `p < 0` (strip above expectation): `h* > 1`, capped at `h_max`.

The empirical fact that producers hedge 20–50% rather than 100% is therefore a statement
that `p` is **systematically positive** — producers are on average bullish relative to the
strip. Haynes Boone surveys confirm this directly: reduced hedging in 2022–23 was attributed
to producers expecting further upside and not wanting to "leave money on the table."

### 2.3 Response to the strip

Let the anchor partially track the strip: `∂μ/∂F = ρ`, with `ρ ∈ [0, 1)`. Then

```
∂h*/∂F = (1 − ρ) / (2λσ²)  >  0
```

**Hedging into strength is derived, not assumed.** It follows from any anchored belief plus
risk aversion. The slope has one free parameter (`λ`) and one measurable one (`ρ`, from the
co-movement of survey expectations with the strip).

Note the `σ²` in the denominator: **higher implied vol reduces the response to price**. This
is a second, less obvious prediction — hedging is *less* price-sensitive in volatile
markets, because the variance-reduction motive dominates the price motive.

### 2.4 Constraints and the ratchet

Apply the bounds:

```
h_t = clip( h*_t , h_min(τ)·𝟙[RBL] , h_max )
```

with `h_min(τ)` the tiered floor as a function of time-to-delivery `τ`.

Then apply the lifting restriction. Hedges roll off at maturity but cannot be lifted early
without approval, so the realised ratio is:

```
h_t = max( h*_t (clipped) ,  h_{t−1} − r_t )
```

where `r_t` is the fraction rolling off in the period. The ratio rises immediately when
`h*` rises and decays only at the roll-off rate when `h*` falls. **Flow is asymmetric:**
rallies produce selling quickly; sell-offs produce no buying, only a slow cessation of selling.

### 2.5 Price-regime structure

Combining the cost thresholds from §1.6 with the FOC gives three regimes:

| Strip vs cost | Behaviour |
|---|---|
| `F < c_op` (~$41) | Hedging locks in a loss. `h*` → 0. Only the covenant floor holds any hedge on. Flow ≈ floor-compliance only. |
| `c_op < F < c_new` (~$41–66) | Hedging protects existing cash flow. `h*` rising in `F`. Moderate flow. |
| `F > c_new` (~$66) | Hedging locks in growth economics and supports borrowing base. Strongest response; this is where "rush to hedge" episodes occur (June 2025, March 2026). |

This is a **piecewise-linear reaction function with derivable breakpoints**. The breakpoints
are survey-observable; only the slope within each segment is estimated.

---

## 3. Aggregation

### 3.1 Sector hedge ratio

```
h̄_t = Σ_i h_{i,t} Q_i  /  Σ_i Q_i
```

With ~40 producers and dispersed `λ_i`, `p_i`, the aggregate is far tighter than any
individual — the averaging argument. But **timing is correlated** (everyone watches the same
strip), so the aggregate *flow* does not benefit from averaging the way the aggregate
*level* does.

### 3.2 Volume in contracts

For hedgeable production `Q` (bbl/d) over a forward window of `T` months:

```
V_hedged = h̄ · Q · 30.4 · T / 1000      [contracts]
```

Using `Q ≈ 5 mb/d` (Standard Chartered population) and a 12-month window:

| h̄ | Contracts hedged (12m) |
|---|---|
| 4% (2026 volumes, as of March 2025) | ~73k |
| 21% (2025 volumes, as of March 2025) | ~380k |
| 35% (Q4 2025 / Q1 2026, Evaluate Energy) | ~640k |
| 52% (entering 2020) | ~950k |

For scale: total WTI open interest across tenors is on the order of 2m contracts, and
daily volume on the order of 1m. A swing from 4% to 35% is ~570k contracts of net selling
spread across the 12–24 month tenors — large relative to open interest at those tenors,
modest relative to front-month volume. **The flow matters where it lands on the curve, not
at the front.** This is why it should be tested against the 12–24 month spread, not the
front contract.

### 3.3 Term structure of the hedge ratio

The tiered covenant (65/50/25% by forward year) plus opportunistic layering produces a
hedge-ratio curve declining in time-to-delivery. Observed shape from the data points above:

| Time to delivery year | Typical h̄ |
|---|---|
| 21–24 months out | ~0–10% (2026 at 4%, March 2025) |
| 9–12 months out | ~20–35% |
| Entering the year | ~35–52% |

**Confound:** the hedge ratio for a given calendar year rises as that year approaches
*regardless of price*, through maintenance flow. Any estimate of `∂h*/∂F` from
year-over-year hedge ratio changes must first remove this time-to-delivery effect, or it
will be badly overstated.

---

## 4. Flow decomposition

Net hedging flow over `[t, t+Δ]`, in contracts, expressed as net *selling* of futures:

```
Flow = Maintenance + Reaction + Compliance + Unwind
```

### 4.1 Maintenance (derived; deterministic)

New months enter the rolling covenant window each period. To hold `h̄` constant:

```
Maintenance ≈ h̄ · Q · Δ_days / 1000
```

At `h̄ = 35%`, `Q = 5 mb/d`: **~52k contracts/month** of steady selling at the back of the
window (the month just entering the 12- or 24-month horizon). Sign fixed, magnitude
derivable from `h̄` and `Q`, both observable. This is the closest thing in the whole model
to a forced-flow term with no free parameters.

### 4.2 Reaction (derived sign; one estimated parameter)

```
Reaction ≈ Σ_i Q_i · (∂h*/∂F)_i · ΔF · 𝟙[h_min < h_i < h_max] · 𝟙[ΔF > 0]
```

Sign positive (selling) on rallies, zero on declines (ratchet). Magnitude carries `λ`.
Suppressed near `h_max` (saturation) and by high `σ`.

### 4.3 Compliance (derived calendar; bounded magnitude)

For RBL borrowers below the floor, concentrated in the 4–8 weeks before each redetermination:

```
Compliance ≈ Σ_{i ∈ RBL} max(0, h_min(τ) − h_i) · Q_i · window / 1000
```

Timing derivable from the redetermination calendar. Magnitude bounded above by the gap to
the floor; sign always selling. Largest when a rally has *not* occurred (nobody hedged
opportunistically) and a redetermination is approaching.

### 4.4 Unwind (tail; not derivable)

Monetising in-the-money hedges for liquidity in distress, or restructuring-driven lifts.
Requires lender consent, so it is rare and lumpy. This is the term that dominates flow in
the tail — and it is buying, not selling. Not modelled; flagged as the principal risk to
the sign predictions.

---

## 5. Measurement mapping

| Model quantity | Observable | Source | Frequency |
|---|---|---|---|
| `h̄` | disclosed hedge ratios | 10-K/10-Q, Evaluate Energy, Wood Mac, StanChart | quarterly |
| `h_min`, `h_max`, tenor | covenant text | credit agreements as SEC exhibits | per facility |
| Calendar | redetermination seasons | Haynes Boone, credit agreements | semi-annual |
| `c_op`, `c_new` | survey breakevens | Dallas Fed Energy Survey (Q1 each year) | annual |
| `μ` | planning price; 2-yr expectation | Dallas Fed Energy Survey | quarterly |
| `F` | 12- and 24-month WTI strip | CME settlements | daily |
| `σ` | implied vol at 12–24m | CL options | daily |
| Realised flow | `PM_short + SD_short` change | CFTC Disaggregated COT | weekly |
| `Q` | survey production | Standard Chartered, company guidance | quarterly |

Everything on the right-hand side is free except the aggregate hedge-ratio series, which is
partly reconstructable from filings at some effort.

---

## 6. Parameter table

| Parameter | Status | Range / value | Basis |
|---|---|---|---|
| `h_min(τ)` | derived | 45–65% yr 1, 50% yr 2, 25% yr 3, RBL borrowers only | filed covenants |
| RBL share of population | bounded | ~30–70% of hedgeable volume | needs a count from filings |
| `h_max` | derived | 90% PDP hard; 50–85% policy | Breitburn covenant, SR 16-17, disclosures |
| Tenor | derived | 12–36 months, rolling | covenants |
| Redetermination dates | derived | Apr–May, Oct–Nov | Haynes Boone, agreements |
| `c_op`, `c_new` | observed | ~$41–43, ~$65–67 (2026) | Dallas Fed |
| `μ` | observed (proxy) | $59–60 planning; ~$73 two-year | Dallas Fed |
| `ρ` (anchor tracking) | estimable from survey series | 0.3–0.7 plausible | expectations vs strip over time |
| `σ` | observed | implied vol | options |
| `Q` | observed | ~5 mb/d surveyed population | StanChart |
| **`λ` (equivalently slope `∂h*/∂F`)** | **estimated** | rough prior 1–3 pp per $1 | see §7 |
| Impact coefficient `Y` | estimated separately | 0.3–1.0 in √(Q/V) law | not part of this model |

One genuinely free parameter in the flow model. That is the point of the exercise.

---

## 7. Rough calibration of the slope, with confounds stated

Data points found (hedge ratio for the *following* calendar year, roughly one year ahead):

| Period | Strip (approx) | h̄ for next year | Source |
|---|---|---|---|
| Early 2015 → early 2016 | mid-$50s → ~$40 | 32% → <15% | Hart Energy, small/mid-caps |
| Entering 2020 | ~$55–60 | 51.7% | StanChart |
| March 2025 | 2025 strip ~$65; 2026 strip ~$62 | 21% (2025); 4% (2026) | StanChart |
| June 12–13 2025 | spike on Israel–Iran strikes | record hedging volume on Aegis platform | Oilprice |
| March 2026 | 2-yr strip ~$76 after Iran war spike | Diamondback ~45%, Coterra ~35%, Permian Res. ~30% for 2026 | East Daley |

Naive slope from 2015→2016: ~17 pp / ~$12 ≈ **1.4 pp per $1**.
Naive slope from March 2025 → March 2026 for 2026 volumes: ~30 pp / ~$14 ≈ 2 pp per $1 —
but this is heavily contaminated by the time-to-delivery effect (§3.3), so the true price
slope is lower, plausibly ~1 pp per $1.

**Prior for `∂h̄/∂F`: 1–2 percentage points per $1 of strip, above `c_new`.** At `Q = 5 mb/d`
on a 12-month window, that is roughly **18–37k contracts of selling per $1 rally**, spread
over days to weeks. This is the estimation target; everything else is structure.

---

## 8. Pre-registerable predictions

Each has a derived sign. Each is a single test.

| # | Prediction | Derived from | Test |
|---|---|---|---|
| P1 | Δ(PM+SD short) over 2–4 weeks increases with Δ(12–24m strip) | §2.3 | regression, weekly COT |
| P2 | Response is asymmetric: positive on rallies, ~zero on declines | §2.4 ratchet | split-sample by sign of ΔF |
| P3 | Response is larger when strip > `c_new` than below it | §2.5 | interaction with breakeven threshold |
| P4 | Response shrinks as `h̄` approaches `h_max` | saturation | interaction with disclosed h̄ |
| P5 | Response shrinks when implied vol is high | `σ²` in denominator | interaction with IV |
| P6 | Hedger short rises in the 4–8 weeks before April–May and Oct–Nov | §4.3 | calendar dummies |
| P7 | `h̄` level tracks `(F − survey expectation)` | §2.2 | quarterly regression on Dallas Fed series |
| P8 | The flow lands in the 12–24m tenors: back spread weakens relative to front on hedging weeks | §3.2 | calendar-spread response to COT changes |
| P9 | The flow appears predominantly in Swap Dealers, not Producer/Merchant | §1.7 | compare categories |

P1–P3 are the core. P8 is the one that connects to something tradeable. P9 is a data-layer
check that should be run first, because if it fails the measurement mapping is wrong and
nothing else can be interpreted.

---

## 9. Sign-stability check (before estimating anything)

Monte Carlo over the parameter ranges in §6, propagating to predicted flow sign and
magnitude for representative scenarios:

| Scenario | Expected result |
|---|---|
| +$10 rally, `h̄ = 20%`, `F > c_new` | selling; sign-stable across all draws; magnitude varies ~3–4× |
| +$10 rally, `h̄ = 80%` | small selling; sign-stable; magnitude near zero in many draws |
| −$10 decline | ~zero flow; sign-stable (no buying) except via Unwind tail |
| Pre-redetermination, `h̄ < h_min` | selling; sign-stable; magnitude depends on RBL share |
| Pre-redetermination, `h̄ > h_min` | ~zero; sign-stable |

If the sign is stable across the plausible parameter range — which the structure suggests it
should be for Maintenance, Reaction and Compliance — then the precision of `λ` does not
matter for direction, only for size. That is the result the previous discussion predicted,
and it should be verified numerically rather than asserted.

---

## 10. What this derivation does not give you

1. **Price impact.** Flow → return requires an impact function. The square-root law provides
   the shape; the coefficient is empirical and market-specific. One additional parameter.
2. **Anticipation.** Every energy desk models this. Impact is likely shifted earlier and
   flattened relative to the raw flow timing. Not derivable; observable only in the data.
3. **Absorption.** Dealer capacity to warehouse the other side varies with balance-sheet
   conditions. Not derivable.
4. **The Unwind tail.** Distress-driven lifting is the largest single flow type and it has
   the opposite sign. Not modelled.
5. **Basis.** Some producers hedge in Brent, in basis swaps, or in gas-linked structures.
   The WTI-only mapping is incomplete by an unknown fraction.
6. **Natural gas contamination.** Swap Dealer positions in CL are clean, but the same banks
   hedge gas producers in NG; when checking §1.7, use the CL report only.

---

## 11. Natural experiments within the available sample

Episodes where the model makes a sharp prediction and the outcome is observable:

- **2015–16 collapse:** strip below `c_new`, falling toward `c_op`. Model predicts hedging
  collapse to floor levels. Observed: <15% for 2016 vs 32% for 2015. ✓ (qualitative)
- **Late 2019:** rising covenant pressure, hedge levels rising (Haynes Boone). Compliance term.
- **Entering 2020:** 51.7% hedged, then the crash — hedges *held* (ratchet), no unwind flow
  until distress. Test of §2.4.
- **2022–23:** strip well above `c_new`, yet hedging *fell* — producers bullish, `p` large.
  This is the case that distinguishes the anchored-belief model from a naive
  "hedge-into-strength" rule: the `p` term dominated the `F` term. Model accommodates it;
  a rule without `μ` does not.
- **June 12–13 2025:** sharp rally, record hedging volume within two days. Reaction term,
  fast response. Test of speed and of the `F > c_new` regime.
- **March 2026:** war-driven spike to ~$85 with the 2-yr strip ~$76 vs survey expectation
  ~$73 — `p` turned negative, model predicts heavy hedging. Observed: 30–45% coverage of
  2026 volumes across major independents. ✓ (qualitative)

These are qualitative confirmations and are worth exactly that much. The quantitative test
is P1–P9 on the full weekly COT series.

---

## 12. Recommended order of work

1. **P9 first** — confirm the flow appears in Swap Dealers. If not, stop and fix the mapping.
2. **P7** — check `h̄` against `(F − expectation)` on the quarterly series. Cheap, and it
   validates the anchored-belief structure before the flow model is built on it.
3. **P1–P3** as a single pre-registered regression with interaction terms, on disaggregated
   COT from 2009 onwards, with the time-to-delivery confound removed.
4. **Sign-stability Monte Carlo** (§9), to establish whether `λ` needs to be pinned down at all.
5. **P8** — only if P1–P3 survive. This is the only step that produces a feature for the
   harness, and it should be evaluated there under the standard admission criteria.

Total pre-registered trial count for this programme: **9**, plus one for the feature in P8.

---

## 13. Honest assessment

The derivation is stronger than expected on structure: the reaction function, the ratchet,
the saturation bound, the calendar, and the maintenance flow all follow from documents rather
than from fitting, and the breakpoints are survey-observable. The one free parameter has a
usable prior from historical episodes.

It is weaker than hoped on tradeability. The flow is large relative to back-tenor open
interest but small relative to front-month volume, it is anticipated by well-resourced
participants, and the tail is dominated by an unmodelled term with the opposite sign. The
realistic outcome is a slow, small, decorrelating feature in the 12–24 month curve, not a
timing signal at the front.

That is consistent with everything earlier in this conversation. It is also, as a piece of
work, exactly the kind of mechanism-first derivation with a stated free-parameter count that
distinguishes a research portfolio from a strategy collection — regardless of whether P8
survives.
