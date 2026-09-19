# Five Published Futures Strategies, With Discounted Expectations

**Status:** reference document for the replication phase
**Selection criteria:** peer-reviewed or equivalent; multi-decade, multi-asset evidence; rules
simple enough to state in a sentence; parameters given in the paper rather than optimised by
the reader; authors with no product to sell the reader.
**Not included:** anything from a course, a signal service, a blog with a funnel, or a single
asset over a single regime.

Every performance figure is labelled as either **[paper]** — reported in the source — or
**[estimate]** — my discounting of it. Do not confuse the two.

---

## 0. Why these five and not others

Robust futures strategies collapse onto a small number of mechanisms. What the literature
actually supports, at the level of "works across decades and asset classes, published by
people who report their failures," is:

1. **Trend** — prices continue for 1–12 months, then partially reverse
2. **Carry** — the curve slope predicts returns, in the direction of the roll
3. Combinations of the two

That is nearly the whole list. Hedging pressure (Basu & Miffre 2013) is the other documented
commodity premium, and it is parked for the reasons already covered elsewhere. Skewness,
basis-momentum and value in commodities exist in the literature but have shorter evidence
and are more sensitive to construction; they are not first-pass candidates.

So the five below are two mechanisms in two expressions (time-series and cross-sectional),
plus one documented combination. **That is deliberate.** Five strategies with five
independent mechanisms would be a fantasy; five expressions of two robust mechanisms is
what actually exists.

---

## 1. Discounting methodology

Published numbers are in-sample, institutional-cost, large-universe figures. Four haircuts
apply, and the evidence for each is stated so the multipliers are not arbitrary.

### 1.1 Publication decay

McLean & Pontiff (2016), 97 equity predictors: returns **26% lower out-of-sample** and
**58% lower post-publication** [paper]. Falck, Rej & Thesmar (2021), 72 factors across
asset classes: post-publication Sharpe ≈ **0.57 × in-sample Sharpe**, i.e. a **43% drop**,
with median discount ratio 0.55 [paper].

The trend literature is the exception worth noting: Baltas & Kosowski and Lempérière et al.
find post-2008 time-series momentum Sharpes broadly comparable to pre-2008. But Hurst, Ooi &
Pedersen's own decade table shows the most recent decade as the weakest in 137 years.

**Multiplier: 0.55–0.70** on any published Sharpe, lower end for anything published before
2010 in a market with heavy institutional participation.

### 1.2 Recent-decade reality check

Where the paper reports by decade, use the most recent decade rather than the full sample.
HOP 2017, 1/3/12-month trend ensemble, gross of fees, net of cost:

| Period | Excess return | Vol | Sharpe (gross fee, net cost) |
|---|---|---|---|
| 1880–2016 full | 11.0% | 9.7% | **1.13** [paper] |
| 2000–2009 | 9.9% | 10.3% | 0.96 [paper] |
| 2010–2016 | 6.2% | 8.1% | **0.77** [paper] |

The recent-decade figure is ~68% of the full-sample figure. This is partly the publication
decay in §1.1 arriving in the data, so do not apply both multipliers at full strength.

### 1.3 Universe size

Diversified Sharpe ≈ per-market Sharpe × √(effective N). HOP report an average per-market
Sharpe of ~0.4 across 67 markets [paper]; the diversified gross Sharpe of ~1.1–1.3 implies
an effective N around 8–10 after correlation. A 20–30 instrument micro-contract universe
with no agricultural depth has an effective N closer to 4–5.

**Multiplier: ~0.75–0.85** relative to a 60-market institutional universe [estimate].

### 1.4 Retail cost

HOP's cost assumptions, one-way as % of notional, 2003–2016 [paper]:

| Asset class | One-way cost |
|---|---|
| Equities | 0.06% |
| Bonds | 0.01% |
| Commodities | 0.10% |
| Currencies | 0.03% |

Retail micro-contract costs are roughly 2–3× these once commission is included as a
percentage of a small notional. For a monthly-rebalanced trend strategy turnover is low
enough that this matters little; for anything rebalanced weekly or using a 1-month signal
it matters a lot.

**Multiplier: 0.85–0.95** for monthly-rebalanced strategies; 0.6–0.8 for weekly [estimate].

### 1.5 Combined

For a monthly-rebalanced strategy with a published gross Sharpe of `S`:

```
S_expected ≈ S × 0.68 (recent decade, includes most of decay)
              × 0.80 (universe)
              × 0.90 (cost)
            ≈ 0.49 × S
```

**Rule of thumb: expect half the published Sharpe.** This is the same conclusion Falck et
al. reach empirically, arrived at by a different route, which is mildly reassuring.

---

## 2. Strategy 1 — Time-series momentum (trend)

**Sources:** Moskowitz, Ooi & Pedersen (2012), *Journal of Financial Economics* 104;
Hurst, Ooi & Pedersen (2017), *Journal of Portfolio Management*.

### Rule, as published

For each instrument, at month-end:
1. Compute the past 12-month excess return.
2. Positive → long; negative → short. Always in the market.
3. Size each position to a constant volatility target using a trailing volatility estimate
   (MOP: ex-ante 40% per instrument; HOP: 10% at portfolio level, with a 3-year rolling
   covariance matrix for the portfolio scaling).
4. Hold one month. Rebalance.

HOP extend to an **equal-weighted ensemble of 1-, 3- and 12-month lookbacks**, each
constructed as above, then combined and scaled to 10% portfolio vol.

### Published performance [paper]

- MOP: 58 instruments, 1985–2009, 12-month/1-month. Positive TSMOM returns in **every one of
  the 58 contracts**. Diversified portfolio Sharpe ≈ 1.0 gross. Individual markets 0.3–0.5.
- HOP: 67 markets, 1880–2016. Net of 2/20 fees and costs: 7.3% excess return, 9.7% vol,
  **Sharpe 0.76**. Gross of fees, net of cost: **1.13**. Positive in every decade.
- HOP by signal, gross Sharpe, full sample: 1-month **1.38**, 3-month **1.19**, 12-month
  **1.32**. With a one-month execution lag: 1-month **0.45**, 3-month **0.64**, 12-month **1.04**.
- HOP by signal, gross Sharpe, 2010–2016: 1-month **0.06**, 3-month **0.30**, 12-month **0.73**.

### Robustness evidence

- Positive in every decade since 1880, across recessions/booms, high/low inflation, war/peace.
- Positive returns in 8 of the 10 largest 60/40 drawdowns over 137 years.
- Best performance when cross-market correlations are low; worst when high (2008–2014
  risk-on/risk-off period).

### Known failure modes [paper]

- **Max drawdown ~25%** at 10% vol target, with peak-to-trough of up to 40 months and
  recoveries of up to 26 months. This is not a strategy that passes a trailing-drawdown
  evaluation unless run at materially lower vol.
- **The 1-month signal has effectively died.** 2010–2016 gross Sharpe of 0.06, and it
  collapses from 1.38 to 0.45 with a single month of execution lag. Do not include it.
- Sharp reversals across many markets simultaneously (1987, March 2020 initially).
- Kim, Tse & Wald (2016) find TSMOM underperformed buy-and-hold 2009–2013.

### Discounted expectation [estimate]

Using the 12-month signal alone, or a 3/12-month ensemble, monthly rebalance, ~25 micro
contracts:

```
1.13 (recent-published, gross fee net cost) → ×0.68 → ×0.80 → ×0.90 ≈ 0.55
```

**Expected net Sharpe: 0.45–0.65.** Max drawdown at 10% vol: plan for 20–30%.

### Prop-firm fit

| Dimension | Assessment |
|---|---|
| Directional | Yes — one position per instrument, no opposing positions |
| Activity | Monthly rebalance is *too slow* for most minimum-activity rules; daily vol-update rebalancing fixes this without changing the signal |
| Drawdown | Poor fit at 10% vol; acceptable at 4–5% vol |
| Gap exposure | Always in the market, overnight and weekend — full exposure to gaps |
| Turnover | Low; cost-tolerant |

### Implementation notes

- Use the 12-month signal, optionally with 3-month, equally weighted. **Drop 1-month.**
- Vol estimate: EWMA, ~32-day half-life for the instrument-level scaling; a shrunk
  covariance matrix for portfolio-level scaling (HOP use a 3-year rolling window).
- Rebalance positions daily to the vol target while updating the *signal* monthly. This
  satisfies activity rules and keeps risk constant without adding trades to the signal.
- Cap any single instrument's risk contribution.

---

## 3. Strategy 2 — Carry timing (time-series carry)

**Source:** Koijen, Moskowitz, Pedersen & Vrugt (2018), *Journal of Financial Economics*
127. Sample roughly 1972–2012 depending on asset class.

### Rule, as published

Carry is the return an asset earns if its price does not change. For futures:

```
carry = (F_front − F_next) / F_next × (12 / months_between)    [annualised]
```

KMPV compute commodity carry from the two nearest contracts because spot is unreliable.

Carry *timing*: for each instrument, go **long when carry is positive** (backwardation)
and **short when negative** (contango) — or long/short relative to the instrument's own
historical mean carry. Vol-scale. Monthly rebalance.

### Published performance [paper]

- Carry timing strategies produce positive Sharpe ratios averaging **0.6** across asset
  classes.
- A global carry timing strategy combining all asset classes: Sharpe **0.9**.
- Carry predicts returns both in the cross-section and in time series for equities,
  bonds, currencies, commodities, Treasuries, credit and options.

### Robustness evidence

- Works across seven asset classes with different economics, which is the strongest
  possible argument that it is a genuine premium rather than a commodity quirk.
- Low unconditional correlation across asset-class carry strategies — but they lose
  together in global recessions, liquidity crises and volatility spikes.

### Known failure modes [paper and estimate]

- **Negative skew.** Carry earns small steady premia and gives them back in crises. The
  worst periods coincide with global recessions and liquidity events. This is the classic
  "picking up nickels" profile and it is the opposite of trend's crisis behaviour.
- Commodity carry alone is weaker than the diversified number; the 0.6 average leans on
  currencies and bonds.
- Seasonality in agricultural and gas curves contaminates the carry measure unless
  handled.

### Discounted expectation [estimate]

Commodities-only carry timing, monthly, ~15 micro contracts with usable curves:

```
0.6 (per-class average) → ×0.60 (decay; older sample) → ×0.85 → ×0.90 ≈ 0.28
```

Adding rates, FX and equity micros to get closer to the diversified version:

```
0.9 (global timing) → ×0.60 → ×0.80 → ×0.90 ≈ 0.39
```

**Expected net Sharpe: 0.25–0.45.** Lower than trend, but that is not the point of it.

### Prop-firm fit

| Dimension | Assessment |
|---|---|
| Directional | Yes |
| Activity | Same as trend — daily vol rebalancing |
| Drawdown | Moderate; crisis losses are sharp and fast |
| Gap exposure | Full |
| Turnover | Very low — carry changes slowly |

### Why include it at all

Trend and carry have historically been near-uncorrelated and fail in opposite conditions:
trend does well in long crises, carry does badly. This is the decorrelation that makes a
combined book's drawdown shallower than either alone. Its role is not return; it is the
shape of the combined equity curve.

---

## 4. Strategy 3 — Cross-sectional term structure (commodities)

**Sources:** Erb & Harvey (2006), *Financial Analysts Journal*; Fuertes, Miffre & Rallis
(2010), *Journal of Banking & Finance* 34; Gorton, Hayashi & Rouwenhorst (2013).

### Rule, as published

Each month, rank commodities by roll yield (front vs next contract, as in §3). Go **long the
most backwardated** and **short the most contangoed**. Erb & Harvey: long 6 / short 6 of 12.
FMR: top and bottom quintiles or terciles of ~37 commodities. Equal-weight the legs. Hold
one month.

### Published performance [paper]

- FMR: term-structure strategy annualised alpha **12.66%**, before their double sort.
- Erb & Harvey: backwardated-minus-contangoed strategy earns a substantial spread over the
  1982–2004 sample; not reported as a Sharpe in a form I would cite precisely.
- GHR: the basis (term structure) is the primary fundamental predictor of commodity futures
  returns, via inventories.

### Robustness evidence

- Grounded in theory of storage — low inventories → backwardation → high expected return —
  which is a mechanism rather than a pattern.
- Consistent across the three studies with different universes and periods.

### Known failure modes [estimate]

- **Small cross-section.** With 12–37 commodities, the legs are 2–8 names each. Idiosyncratic
  risk dominates; a single squeeze or weather event in one leg dominates the month.
- Highly correlated with carry timing (§3) by construction — same signal, different
  expression. Treat as one mechanism for correlation purposes.
- Agricultural seasonality distorts roll yields.

### Discounted expectation [estimate]

Published Sharpe not reliably quotable; from the 12.66% alpha and typical long-short
commodity vol of ~15–20%, in-sample Sharpe is plausibly **0.6–0.8** [estimate].

```
0.7 → ×0.60 → ×0.75 (tiny cross-section at micro scale) → ×0.85 ≈ 0.27
```

**Expected net Sharpe: 0.2–0.4.**

### Prop-firm fit

| Dimension | Assessment |
|---|---|
| Directional | **No.** Long some commodities, short others simultaneously. **Check the firm's hedging and correlated-position rules before building.** Many prohibit this. |
| Activity | Monthly rebalance; augment with daily vol updates |
| Drawdown | Moderate; concentrated legs produce lumpy P&L |
| Gap exposure | Full |
| Turnover | Low–moderate |

### When to prefer this over carry timing

Only if the firm permits long/short across instruments and you have enough commodity
micros to form legs of at least 4–5 names. Otherwise carry timing (§3) delivers the same
mechanism in a compliant form.

---

## 5. Strategy 4 — Cross-sectional momentum (commodities)

**Sources:** Miffre & Rallis (2007), *Journal of Banking & Finance*; Fuertes, Miffre &
Rallis (2010); Asness, Moskowitz & Pedersen (2013), *Journal of Finance*.

### Rule, as published

Each month, rank commodities by past 12-month return (AMP use 12 months skipping the most
recent month; Miffre & Rallis test 1–12 month ranking and holding periods). Long the top
group, short the bottom group. Equal weight. Hold 1 month.

### Published performance [paper]

- Miffre & Rallis: identify 13 profitable momentum strategies across ranking/holding
  combinations, average ~9% annualised; long-term contrarian strategies do *not* work.
- FMR: momentum strategy annualised alpha **10.14%**.
- AMP: momentum works in commodities alongside equities, bonds and currencies, and is
  negatively correlated with value across all of them.

### Robustness evidence

- Documented across eight markets in AMP with the same construction.
- Miffre & Rallis note that momentum profits are concentrated in backwardated markets —
  i.e. momentum and term structure interact, which motivates §6.

### Known failure modes [paper and estimate]

- Miffre & Rallis tested 32 ranking/holding combinations and report the 13 that worked.
  **That is a multiple-testing problem in the source**, and the 13 are not independent.
  Discount accordingly.
- Same tiny-cross-section issue as §4.
- Momentum crashes: sharp reversals after prolonged trends destroy the short leg.

### Discounted expectation [estimate]

From the 10.14% alpha, in-sample Sharpe plausibly **0.5–0.7**.

```
0.6 → ×0.55 (decay + source multiple testing) → ×0.75 → ×0.85 ≈ 0.21
```

**Expected net Sharpe: 0.15–0.35.** The weakest of the five as a standalone.

### Prop-firm fit

Same as §4: long/short across instruments, check the rules. Directional TSMOM (§2)
captures most of the same information — MOP show that time-series momentum is not
explained by cross-sectional momentum, but the two are strongly correlated.

---

## 6. Strategy 5 — Momentum × term structure double sort

**Source:** Fuertes, Miffre & Rallis (2010), *Journal of Banking & Finance* 34.

### Rule, as published

Sort commodities on momentum, then within momentum groups sort on term structure. Long
commodities that are **both** high-momentum and backwardated; short those that are **both**
low-momentum and contangoed. Monthly rebalance.

### Published performance [paper]

- Double-sort abnormal return **21.02%** annualised, versus 10.14% (momentum alone) and
  12.66% (term structure alone).
- Authors report the performance is not explained by lack of liquidity, data mining or
  transaction costs.

### Why to be sceptical of that number specifically

- A double sort on ~37 commodities leaves **very few names per leg** — often 2–4. The 21%
  is the return on a highly concentrated portfolio and its volatility is correspondingly
  high; the Sharpe uplift over the single sorts is much smaller than the return uplift
  suggests.
- The combination was chosen and reported in-sample. It is the best of the things they
  tried.
- It is, mechanically, "trend + carry, intersected" — which is the same two mechanisms
  again, with a filter architecture (§6.1 of `ALPHA_PROGRAMME.md` explains why filtering
  is weaker than combining).

### Discounted expectation [estimate]

```
In-sample Sharpe plausibly 0.9–1.1 → ×0.50 → ×0.70 (extreme concentration at micro scale) → ×0.85 ≈ 0.30–0.35
```

**Expected net Sharpe: 0.25–0.40** — roughly the same as either single sort, at higher
concentration risk. The paper's headline is the least reliable number in this document.

### What to take from it instead

The *insight* — momentum profits concentrate in backwardated markets — is robust and
useful. The right way to use it is not a double sort but a **combined continuous forecast**
of trend and carry z-scores, which achieves the same tilt without the concentration or the
filter parameters. That is what §8 below does.

---

## 7. What these actually are

| # | Strategy | Mechanism | Expression | Directional | Expected net SR [estimate] |
|---|---|---|---|---|---|
| 1 | TSMOM 12m (+3m) | Trend | Time-series | Yes | 0.45–0.65 |
| 2 | Carry timing | Carry | Time-series | Yes | 0.25–0.45 |
| 3 | XS term structure | Carry | Cross-sectional | No | 0.20–0.40 |
| 4 | XS momentum | Trend | Cross-sectional | No | 0.15–0.35 |
| 5 | Double sort | Trend × Carry | Cross-sectional | No | 0.25–0.40 |

**Two mechanisms.** For correlation purposes, 1 ≈ 4 and 2 ≈ 3 ≈ (5 partly both). The
diversification available is between trend and carry, not among five strategies.

Historical correlation between trend and carry is low — roughly 0 to 0.2 — and their
crisis behaviour is opposite. That is the entire diversification benefit on offer, and it
is a real one.

---

## 8. Recommended build: the compliant combined book

Given hedging restrictions are likely, and given the two-mechanism reality:

```
For each instrument i, at each rebalance:
    z_trend(i)  = standardised 12m (and 3m) TSMOM signal
    z_carry(i)  = standardised carry, relative to instrument's own history
    forecast(i) = 0.5 · z_trend(i) + 0.5 · z_carry(i)
    forecast(i) = clip(forecast(i), −2, +2)
    position(i) = forecast(i) × vol_target / σ_i, subject to portfolio-level vol cap
```

- **One position per instrument**, sign given by the combined forecast. Never long and
  short the same thing; never a paired trade. Compliant with the strictest hedging rules
  I am aware of, but **verify against the specific rulebook**.
- Signals update monthly; positions rebalance daily to the vol target. Satisfies activity
  rules without adding signal-driven trades.
- Equal weights between trend and carry. Do not optimise the weight on 10 years of data.

### Expected performance of the combination [estimate]

Two components at net Sharpe ~0.55 and ~0.35, correlation ~0.1:

```
SR_combined ≈ (0.55 + 0.35) / √(2 × 1.1) ≈ 0.61
```

Round down for everything not modelled: **0.5–0.7 net**, with a shallower drawdown than
trend alone because carry's losses do not coincide with trend's.

At a 5% vol target that is 2.5–3.5% expected annual return with an expected worst
drawdown around 8–12%. At 10% vol, double both. Refer to the first-passage table in
`ALPHA_PROGRAMME.md` §12 before choosing.

---

## 9. Universe at £50k — micro contracts

Diversification at this capital level depends on micro contracts. Full-size CL or GC
positions are unmanageable on a £50k account at any sensible vol target; the micro
equivalents are not. Verify current listings and, critically, **the prop firm's permitted
product list**, which is usually a subset.

| Sector | Micro contracts (verify listing) |
|---|---|
| Equity index | MES, MNQ, MYM, M2K |
| Energy | MCL; micro natural gas where listed |
| Metals | MGC, SIL (micro silver), MHG (micro copper) |
| Rates | Micro Treasury yield futures (2Y, 5Y, 10Y, 30Y) |
| FX | M6E, M6B, M6A, M6J and other micro FX pairs |
| Crypto | MBT, MET — high vol, treat with caution |
| Agriculturals | **No micros.** Mini corn/wheat/soybeans (XC/XW/XK, 1,000 bu) exist but are illiquid |

Realistic compliant universe: **15–25 instruments**, weighted toward equity, energy, metals,
rates and FX, with agriculturals underrepresented. That is the source of the universe
haircut in §1.3 and it is worth being explicit about in the writeup.

---

## 10. Build and validation plan

Target: two to four weeks, because the parameters are published and the framework exists.

1. **Data.** Continuous series with proper roll adjustment for every instrument in the
   universe, plus the next-contract series for carry. Reconcile roll dates against the
   exchange calendar.
2. **Replicate TSMOM** on the full available history at the published parameters. It should
   show positive returns in most instruments and a diversified gross Sharpe in the 0.6–1.0
   range on the recent sample. If it does not, the data layer is broken — fix that before
   anything else.
3. **Replicate carry timing** likewise. Check correlation to trend; it should be low.
4. **Combine** per §8. Report: Sharpe, max drawdown, per-year returns, per-instrument
   contribution, correlation between components.
5. **Validate** with CPCV on the signal frame and walk-forward on the book frame, per
   `FEATURE_RESEARCH.md` §8. No sweeps. Trial budget: **2** (one per component), plus one
   for the combination.
6. **Size** via first-passage simulation with fat-tailed returns and parameter uncertainty
   propagated. Choose the vol target that maximises P(pass) for the specific firm's rules,
   not the one that maximises expected return.
7. **Forward log** from the first live day.

**No parameter optimisation at any step.** The whole point of this phase is that the
parameters are borrowed, so the trial count is tiny and the DSR discount is small.

---

## 11. Honest summary

- What the literature robustly supports for futures is **trend and carry**. Everything else
  is either a re-expression of those two, a shorter-evidence effect, or marketing.
- Expect **roughly half the published Sharpe** after decay, universe and cost. Falck et al.
  find this empirically; the decomposition in §1 reaches it from first principles.
- A compliant combined trend+carry book on 15–25 micros is plausibly **0.5–0.7 net**, with
  20–30% drawdowns at 10% vol and 8–12% at 5% vol. It is a real, documented, buildable
  strategy and it is not a high-Sharpe strategy.
- Its value in this programme is threefold: income at small scale, a demonstrated
  hypothesis-to-live process, and the **calibration baseline** against which anything
  novel (the hedging-pressure work) gets measured. If your harness cannot reproduce trend
  and carry, it cannot be trusted on anything else.

---

## 12. Sources

- Moskowitz, T., Ooi, Y.H., Pedersen, L.H. (2012). "Time Series Momentum." *JFE* 104(2), 228–250.
- Hurst, B., Ooi, Y.H., Pedersen, L.H. (2017). "A Century of Evidence on Trend-Following Investing." *JPM*. SSRN 2993026.
- Koijen, R., Moskowitz, T., Pedersen, L.H., Vrugt, E. (2018). "Carry." *JFE* 127(2), 197–225.
- Erb, C., Harvey, C. (2006). "The Strategic and Tactical Value of Commodity Futures." *FAJ* 62(2).
- Fuertes, A.M., Miffre, J., Rallis, G. (2010). "Tactical Allocation in Commodity Futures Markets." *JBF* 34, 2530–2548.
- Miffre, J., Rallis, G. (2007). "Momentum Strategies in Commodity Futures Markets." *JBF* 31.
- Asness, C., Moskowitz, T., Pedersen, L.H. (2013). "Value and Momentum Everywhere." *JF* 68(3).
- Gorton, G., Hayashi, F., Rouwenhorst, K.G. (2013). "The Fundamentals of Commodity Futures Returns." *Review of Finance*.
- McLean, R.D., Pontiff, J. (2016). "Does Academic Research Destroy Stock Return Predictability?" *JF* 71(1).
- Falck, A., Rej, A., Thesmar, D. (2021). "Why and How Systematic Strategies Decay." arXiv 2105.01380.
- Baltas, N., Kosowski, R. (2020). "Demystifying Time-Series Momentum Strategies." *JBF*.
- Kim, A.Y., Tse, Y., Wald, J. (2016). "Time Series Momentum and Volatility Scaling." *Journal of Financial Markets*.
- AQR Data Library — TSMOM original paper data, monthly factors 1985–2009, free. Use as a replication benchmark.
