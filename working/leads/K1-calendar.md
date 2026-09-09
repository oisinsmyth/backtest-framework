# K1 — the calendar screen: external evidence

*External-literature scout. No code run, no backtest written. Every claim below is
tagged with its sample period, universe and provenance; where I could not verify a
number behind a paywall I say so explicitly.*

## 1. Verdict

**Spend the twenty minutes, but on one hypothesis and one statistic, and expect a
negative.** The two effects worth anything (K1a turn-of-month, K1c FOMC) are both
documented as **market-beta / index-level** phenomena, not cross-sectional selectors —
Lucca–Moench show a single market factor explains 64% of the cross-section of FOMC-day
returns with an insignificant alpha, and the turn-of-month is measured on VW and EW
*index* returns. That means neither can produce a name-selecting signal in this
programme; both would be **beta-timing overlays** on a book that has no market-timing
mandate. Worse for transfer: both are documented **weaker where this programme lives**.
Lucca–Moench's FOMC differential is 36 bp value-weighted but only **25 bp
equal-weighted and 20 bp in the smallest CRSP decile** — the equal weighting that
protects K1 from the price-tercile nuisance is the same weighting that shrinks the
effect. And the turn-of-month, while *not confined* to small/low-price names, is
explicitly **more pronounced** in them (0.25% vs 0.15% daily small vs large;
0.27% vs 0.19% low- vs high-price) — i.e. the strong version sits inside the cost wall.
Add the decay evidence: peer-reviewed work says the TOM effect **disappears entirely
after 2001** (Han, Han & Tian, FRL 2025) and the pre-FOMC drift **collapsed from 44.5 bp
to 9.2 bp after 2015** (Kurov, Wolfe & Gilbert, FRL 2020) — both breaks fall *inside*
this fixture's 2010–2026 window, and the literature is genuinely split rather than
settled. Finally, Sullivan–Timmermann–White's verdict stands: across a universe of
**9,452 calendar rules on 100 years of DJIA data, no calendar rule beat the benchmark
once data-snooping was accounted for**, with Reality Check p-values of 0.20–0.24 against
nominal p-values below 0.002. K1b (day of week) should be dropped or kept only as a
multiplicity denominator — it is the single most-snooped rule in that universe and it is
the one STW showed collapses first. If a screen is run, run it **gross, on the
equal-weighted universe mean, with the time-rotation null enumerated exactly**, and
treat a null result as the expected outcome rather than a surprise.

---

## 2. Turn of month

### 2.1 Original documentation and magnitude

| Study | Sample | Universe | Window | Result |
|---|---|---|---|---|
| **Ariel (1987)**, JFE 18(1) 161–174 | **1963–1981** | CRSP EW and VW portfolios | first half of month = last trading day of prior month + first 9 trading days | Mean return positive **only** in the first half; **indistinguishable from zero** in the last half. A shift in the *mean* of the return distribution, not variance. Independent of the January effect. |
| **Lakonishok & Smidt (1988)**, RFS | **1897–1986 (90 years)** | DJIA (30 large liquid names) | **day −1 to day +3** (4 days) | Four TOM days: **+0.473%** cumulative; whole month **+0.349%** → returns over the *other* 16 days were on average **negative**. |
| **McConnell & Xu (2008)**, FAJ 64(2) 49–64 | **1926–2005**, plus post-L&S subsample **1987–2005** | CRSP all US equities, VW and EW | day −1 to +3 | 1987–2005 VW: **0.15% per day** over TOM vs **≈0.000% (−0.001%)** on the other 16 days. Effect found in **31 of 35** countries. |

The canonical claim is therefore: *the entire equity risk premium is earned on four days
a month.* That is the strong form, and it is what makes the effect famous — which is
precisely the STW warning in §5.

### 2.2 Post-2000 and post-2010 evidence — the decisive question

**The strongest published negative:**

> **Han, L., Han, Y., & Tian, S. (2025), "The disappearing turn-of-month effect",
> Finance Research Letters, vol. 71.** [PEER-REVIEWED]
> Abstract verbatim: *"We document that the turn-of-the-month (TOM) effect, historically
> a highly significant regularity where the market yields higher returns around the turn
> of the month, disappears entirely after 2001. The liquidity-based explanation proposed
> by Ogden (1990) no longer holds over the past two decades. We hypothesize and provide
> evidence that the drastic reduction in transaction costs after 2001 likely diminishes
> the TOM effect, by enabling arbitragers to trade against it more effectively and
> allowing investors to trade more frequently rather than concentrating their activity
> at the end of the month."*

Per search-result summary of the paper's body (I could **not** open the full text —
ScienceDirect returned HTTP 403 — so treat these two numbers as [UNVERIFIED]): TOM days
ran **~0.10%/day above rest-of-month days** in earlier subperiods and were
**completely insignificant** in the final subperiod **2 Jan 2001 – 31 Dec 2020**. The
attributed cause is **decimalisation (2001)** cutting the cost of arbitraging it away.
Note that this dates the death to 2001, which means **the entire 2010–2026 fixture sits
inside the dead zone.**

**Corroborating negative, longer horizon:**

> **Plastun, Sibande, Gupta & Wohar (2019), "Rise and fall of calendar anomalies over a
> century", North American Journal of Economics and Finance 49, 181–205.**
> [PEER-REVIEWED] DJIA, **1900–2018**. Tests day-of-week, turn-of-month, turn-of-year and
> holiday effects with t-tests, ANOVA, Kruskal–Wallis, Mann–Whitney and a trading
> simulation. Verdict: the *"golden age"* of calendar anomalies was mid-20th century;
> **since the 1980s all four calendar anomalies have disappeared.**

**The contrary evidence, stated fairly — the literature is split, not settled:**

- A 2026 paper, *"Infrequent rebalancing, risk deferral, and equity returns at the turn
  of the month"* (Journal of International Financial Markets, Institutions & Money,
  S1042443126000259) reports a **conditional** TOM effect surviving in recent data:
  TOM-day mean **+7.8 bp** higher following high-volatility periods and **+20 bp** higher
  during recessions, both significant. [PEER-REVIEWED, abstract-level only — paywalled,
  numbers taken from search summary, **UNVERIFIED**]. This is a *conditional* revival,
  which is itself another layer of specification search.
- *Turn-of-the-Month Strategies: Do They Still Work?* (quantseeker.com, 2025)
  [NOT PEER-REVIEWED — independent quant newsletter, not a broker or vendor, but no
  referee]. Tests 37 ETFs (SPY/QQQ/IWM, 11 sector, 9 country, bonds, FX, commodities,
  BTC). Finding: on the **classical [0,+3] window, none of the equity differences are
  statistically significant** in recent data — *"returns now indistinguishable from
  returns on other days"*; on a **widened [−3,+3] window**, most equity ETFs show a
  significant **5–12 bp/day** excess. Rolling averages show a **consistent downtrend over
  the past decade, materially weaker since 2015**. **Read that as a warning, not as
  support**: the effect survives only under a window redefinition, which is exactly the
  degree of freedom STW's 9,452-rule universe was built to price.

**Bottom line for Q1.** There *is* credible peer-reviewed post-2000 evidence, and it is
negative: the classical window is dead after 2001. Post-2010 evidence specifically is
thinner and mostly rides inside the 2001–2020 subsample of Han et al. plus non-refereed
ETF tests. I found **no** peer-reviewed paper that isolates 2010–2026 US equities and
reports a surviving classical TOM effect.

### 2.3 Small-cap / low-price concentration — yes, documented, and it is the bad kind

McConnell & Xu (2008), CRSP 1926–2005, VW daily returns:

- **Largest decile:** TOM **0.15%/day** vs other days **0.01%**, t = 7.81.
- **Smallest decile:** TOM **0.25%/day** vs other days **0.03%**, t = 8.54. (Note: their
  smallest market-cap portfolio contains ~50% of all CRSP firms.)
- **High-price stocks:** TOM **0.19%** vs **0.04%**, t = 8.22.
- **Low-price stocks:** TOM **0.27%** vs (higher) other-day return.

Their headline is that the effect is *"not confined to small-capitalization or low-price
stocks"* — true, and it is the honest reading. But the gradient is unambiguous: **the
effect is ~65% larger in the smallest decile and ~40% larger in low-price names.** For
this programme, where cost in bp scales *inversely* with price under IBKR per-share
charging, the strongest version of the effect is exactly the part that cannot be
harvested. This is the same trap that killed D284.

---

## 3. The proposed mechanism — payroll flows, index rebalancing, month-end marking

**Ogden (1990)** is the canonical mechanism paper: the "standardisation of payment
dates" at month-end concentrates cash inflows, which get invested, lifting prices. This
is the "payday hypothesis".

**Direct evidence AGAINST, from the same-window data:** McConnell & Xu ran two direct
tests and both failed.

1. **Trading volume.** Trading volume is **no higher** at the turn of the month than on
   other days. If concentrated buying caused it, volume should spike. It does not.
2. **Daily mutual-fund net flows.** Using **TrimTabs** daily net flows, **Feb 1998 –
   Dec 2005**, 1,694 funds from 86 families (~20% of total mutual-fund dollars): flows
   were **negative on day −2, positive on day −1, negative on day +1, positive on days
   +2 and +3**. Their words: *"No pattern in net funds flow to equity mutual funds is
   discernible to support the payday hypothesis."* They confirm the return effect was
   present in that same 1998–2005 window (VW difference 0.12 pp vs 0.15 pp for
   1926–2005), so it is not a power problem with the sample.

They also note the effect appears in **31 of 35 countries**, which have quite different
payroll and pension calendars — further evidence against a US-payroll story.

**Direct evidence FOR, but of a different mechanism:**

> **Etula, Rinne, Suominen & Vaittinen (2020), "Dash for Cash: Monthly Market Impact of
> Institutional Liquidity Needs", Review of Financial Studies 33(1), 75–111.**
> [PEER-REVIEWED] Abstract verbatim: *"We present broad-based evidence that the monthly
> payment cycle induces systematic patterns in liquid markets around the globe. First,
> we document temporary increases in the costs of debt and equity capital that coincide
> with key dates associated with month-end cash needs. Second, we present direct and
> indirect evidence on the role of institutions in the genesis of these patterns and
> derive estimates of the associated costs borne by market participants. Third, and
> finally, we investigate the limits to arbitrage that prevent markets from functioning
> efficiently. Our results indicate that many investors and their agents, including
> mutual funds, suffer from liquidity-related trading."*

Note the sign of the mechanism: Etula et al. describe **institutions being forced to
RAISE cash near month-end** — a price-*insensitive forced seller* pushing the cost of
capital temporarily up before month-end, with reversal after. That is a genuine
forced-participant mechanism of the kind this programme values, and it is supported by
direct institutional evidence rather than told after the fact. But it is **not** Ogden's
inflow story — it is nearly its mirror image, and it predicts a **pre-month-end dip then
reversal**, which maps to a window like [−3,+3] rather than [−1,+3]. I could not verify
the paper's exact sample period or per-day magnitudes (SSRN and the RFS full text both
403'd); the abstract above is verified verbatim from EconPapers.

**Honest verdict on Q2:** Ogden's payday story is **directly contradicted** by both the
volume test and the fund-flow test, and Han et al. (2025) state flatly that the
liquidity explanation *"no longer holds over the past two decades."* The one mechanism
with direct institutional evidence behind it (Dash for Cash) is a **month-end
liquidity-demand** story, not a payroll-inflow story, and it implies a different window
and a partly *negative* pre-month-end sign. Index-reconstitution flows are a separate,
mostly quarterly/annual phenomenon and I found no study attributing the monthly TOM
effect to index rebalancing. **Treat the payroll mechanism as a story told after the
fact; treat month-end liquidity demand as the only mechanism with direct evidence.**

---

## 4. Day of week / the Monday effect

- **Original**: French (1980), Gibbons & Hess (1981), Cross (1973), Keim & Stambaugh
  (1984) etc. — negative Monday returns, formally "discovered" ~1973–1980.
- **Smith & Robins** (cited via ASU News, 2017) [SECONDARY / PRESS RELEASE — the
  underlying paper I did not open]: a structural break in **1975**. Monday returns
  averaged **−18.1 bp for 1926–1974** but only **−5 bp for 1975–2014**, *not*
  statistically significant. Their framing: *"All these studies that try to explain this
  weird 'weekend effect' are explaining something that disappeared in 1975"* — i.e. the
  anomaly was gone **before** the papers documenting it were published.
- **Olson, Mossman & Chou (2015), "The evolution of the weekend effect in US markets",
  Quarterly Review of Economics and Finance 58, 56–63** [PEER-REVIEWED]: cointegration
  and Bai–Perron breakpoint analysis. The weekend effect **declined immediately after its
  formal discovery in 1973**, then went through periods of **reappearance and even
  reversal**. Their breakpoint tests explain *why* researchers keep reaching conflicting
  conclusions — the Monday differential has regime-shifted repeatedly, so any given
  sample can find any given sign.
- **Plastun et al. (2019)**: day-of-week effect gone in the DJIA since the 1980s.
- **STW (1998/2001)**, decisively: the *optimal rule in the full 1897–1996 sample* is
  "neutral on Mondays, long Tuesday–Friday" — i.e. the Monday effect is the max of the
  search, which is what you would expect if it were the luckiest of thousands of rules.
  When they evaluated the Monday rule against **only the 20 core day-of-the-week rules**
  (not the full 9,452), the p-value rose to **0.062** in both samples starting 1953 and
  to **over 0.21** in 1962–1978. Their conclusion: *"Evaluating the Monday effect in the
  context of only the core day-of-the-week rules renders the statistical significance of
  the Monday effect doubtful, even in the period during which the Monday effect was
  discovered."*

**Post-2010 evidence specifically: I found essentially none that is peer-reviewed,
US-equity, and positive.** Olson et al. runs to ~2014 and reports a regime-varying,
non-persistent differential. There is a 2022 FRL paper "Sentiment changes and the Monday
effect" [PEER-REVIEWED, not opened — paywalled] which conditions the effect on sentiment,
i.e. another conditional revival.

**Verdict on K1b: drop it.** It is the most-mined rule in the most-mined dataset in the
social sciences, it failed its own discovery-era significance test under a 20-rule
correction, and there is no clean post-2010 positive. Its only remaining use is as an
honest denominator when disclosing multiplicity.

---

## 5. FOMC drift

### 5.1 The original result

> **Lucca & Moench, "The Pre-FOMC Announcement Drift"**, Journal of Finance 70(1), 2015;
> the NBER/NY Fed draft of 28 Feb 2013 is free and is what I read in full.
> [PEER-REVIEWED / WORKING PAPER]

Verified numbers from the paper's own text:

- **Sample 1994–2011**, **131 scheduled announcements**. The **S&P 500 rose on average
  49 bp (48.8 bp) in the 24 hours before the announcement** (2 p.m. to 2 p.m. ET, since
  announcements were made at ~2:15 p.m. from Sept 1994 to March 2011).
- Returns **do not revert** afterwards; **~80% of the annual realised excess return since
  1994** is earned in those 24 hours; a hold-only-pre-FOMC strategy had an **annualised
  Sharpe above 1.1**.
- **1980–2011**: 36.6 bp, t = 4.86, Sharpe 0.92, >half of realised excess returns.
  **1980–1993**: 20 bp. **1960–1979: essentially zero.** Over the full 1960–2011 sample,
  **524 scheduled meetings**, the differential is only **16.7 bp** vs 0.9 bp on non-FOMC
  days.
- **Absent in US Treasuries and other fixed income**, and absent before other US macro
  announcements. Present in other major international equity indices.
- They ran their **own White (2000) Reality Check** across the ten macro announcements
  they consider: 99.98% of bootstrapped max-|t| values fell below their 4.51. **This is
  a much smaller snooping universe than STW's** — it prices search across
  *announcement types*, not across the calendar-rule universe.

**The meetings are ~8 per year** (since the early 1980s). For the fixture window
2010-01-04 → 2026-08-26 that is **≈133 scheduled announcements** (16 full years × 8, plus
5 meetings in 2026 through August). Your ~130 estimate is right, and it is thin: at a
per-event standard deviation of roughly 1%, the standard error on a mean of 130 events is
~9 bp, so a 20–25 bp effect is a t ≈ 2.2–2.8 *at best* even if it is entirely real.

### 5.2 The strongest published negative — post-publication decay

> **Kurov, A., Wolfe, M. H., & Gilbert, T. (2021), "The disappearing pre-FOMC announcement
> drift", Finance Research Letters 40 (published online Sept 2020).** [PEER-REVIEWED]

Verified numbers:

- Instrument: **E-mini S&P 500 nearby futures** (from 10 Sept 1997), S&P 500 futures
  earlier. Original L&M window: **Sept 1994 – March 2011, 131 meetings**. Their extension:
  **April 2011 – December 2019, 70 meetings** (40 with press conferences, 30 without).
- **Press-conference meetings, Apr 2011 – Dec 2015: 44.5 bp** — the drift was still alive
  for the first half of this programme's fixture.
- **Press-conference meetings, Jan 2016 – Dec 2019: 9.2 bp.** A Wilcoxon rank-sum test
  rejects equal central tendency between the two subperiods at the **1% level**.
- Attributed cause: **reduced uncertainty**. Mean VIX fell from **17.7** before the
  December 2015 ZLB liftoff to **14.7** after (significant at 1%); the post-ZLB indicator
  goes insignificant once VIX is included.

So the decay is documented, it is peer-reviewed, and **the break is 2015/2016 — inside
the fixture.** The effect was publicised in 2011 (the working paper) and 2015 (the JF
publication); the collapse follows publication closely enough to be the textbook decay
pattern, though the authors attribute it to VIX rather than to arbitrage.

**Contrary evidence, stated fairly:**

- **NY Fed Liberty Street Economics (Nov 2018), "The Pre-FOMC Announcement Drift: More
  Recent Evidence"** [CENTRAL-BANK BLOG, NOT PEER-REVIEWED — and written under the
  original authors' institution, so it is a follow-up on their own finding]: reports
  continued large excess returns, but **only for meetings featuring a press conference by
  the Chair**. Since 2019 *every* meeting has a press conference, which dissolves that
  conditioning variable going forward.
- *"The pre-FOMC announcement drift: short-lived or long-lasting?"*, Applied Economics
  (2024) [PEER-REVIEWED, not opened]: finds the pre-announcement drift but reports the
  FOMC influence is **short-lived, insignificant shortly after disclosure**.
- *Trading the Fed: The Pre-FOMC Drift is Alive* (quantseeker.com, 2025) [NOT
  PEER-REVIEWED]: claims persistence through **December 2024** across ETFs, stronger in
  high-volatility environments — consistent with Kurov et al.'s VIX mechanism rather than
  contradicting it, since 2020–2024 contains two high-VIX regimes.

### 5.3 A related, distinct calendar effect worth knowing about

> **Cieslak, Morse & Vissing-Jorgensen (2019), "Stock Returns over the FOMC Cycle",
> Journal of Finance 74(5), 2201–2248.** [PEER-REVIEWED] **Since 1994**, the equity
> premium is earned entirely in **weeks 0, 2, 4 and 6 in FOMC-cycle time** (even weeks
> from the last meeting). Causally tied to the Fed via intermeeting target changes, Fed
> funds futures and internal Board of Governors meetings.

This is a *different* and broader calendar gate than K1c (it covers roughly half of all
trading days rather than 130 single days, so it is far less thin), it has a stated causal
mechanism, and it was published in 2019 — recent enough that decay evidence is scarce. **I
did not find a credible published out-of-sample failure of it.** If the principal wants
one FOMC-flavoured hypothesis with better statistical footing than a 130-event window,
this is the better candidate — but it is still an index/beta-timing effect, so §6 and §7
apply to it unchanged.

---

## 6. The data-snooping critique — the honest verdict

> **Sullivan, R., Timmermann, A. & White, H. (2001), "Dangers of data mining: the case of
> calendar effects in stock returns", Journal of Econometrics 105, 249–286.**
> I read the free 1998 UCSD working-paper version in full. [PEER-REVIEWED / WORKING PAPER]

Verified numbers:

- **Universe: 9,452 calendar rules** (they also report a restricted **244-rule** universe
  of "the best-known calendar effects"). **100 years of daily DJIA data, 1897–1996**,
  bootstrap with 500 resamples (so p-value granularity is 1/500 = 0.002).
- Full sample 1897–1996: market **4.63%/yr**, best calendar rule **8.66%/yr** (the rule is
  "neutral on Mondays, long Tue–Fri"). **Nominal p < 0.002. Reality Check p = 0.24**
  (0.20 in the 90-year subsample).
- In the shorter subsamples the best rule beats the market by **3.05 to 11.71 percentage
  points per year**, nominal p-values are significant at 10% in **all seven** periods, and
  the **Reality Check p-value is always above 0.21**.
- Out-of-sample check on DJIA and S&P 500 futures: best rule beat the index by **3.6%/yr**,
  **nominal p = 0.12, Reality Check p = 0.87**; on the Sharpe criterion, **0.30 and 0.99**.
  Reality Check p **> 0.91** for both price series on another criterion.
- Conclusion verbatim: *"Using Reality Check P-values that adjust for the effects of
  data-snooping, no calendar rule appears to be capable of outperforming the benchmark
  market index. This is true in all of the individual sample periods, in the
  out-of-sample experiment with the DJIA and S&P 500 Futures data, and in the full sample
  using a century of daily data."*

**Two caveats STW themselves flag, and they cut both ways for K1:**

1. They deliberately used the **DJIA** — very liquid, low transaction costs — so that a
   finding *would* challenge EMH. They explicitly did **not** test small firms or foreign
   equities, and note the January small-firm effect is *"likely to be robust with respect
   to data-snooping"* but *"cannot be exploited to generate economic profits because of
   the presence of high transaction costs."* That is a precise description of this
   programme's dilemma: the surviving calendar effects live where costs eat them.
2. Their universe is **calendar rules only**, on **one index**. It does not price search
   across assets, weighting schemes, or conditioning variables — so the true multiplicity
   facing a modern practitioner is **larger** than 9,452, not smaller.

**Blunt verdict:** the honest reading is that **calendar effects do not survive correction
for the search that produced them**. K1a/K1b/K1c are not three fresh hypotheses — they are
**the three loudest survivors of a century of mining by thousands of people**, which is
exactly the selection STW modelled. Pre-declaring them together and disclosing the
multiplicity of three does *not* address this: the relevant denominator is the historical
search, not the three you chose to run. The only clean answers to that are (i) a genuinely
out-of-sample fixture the effect has never seen, and (ii) requiring a much larger effect
than nominal significance would demand. Lucca–Moench's own Reality Check is a partial
defence for K1c — but it prices search over **ten macro announcements**, not over the
calendar-rule universe.

---

## 7. Effect location: index vs cross-section

This is the question that decides K1, and the answer is clear.

**FOMC — a pure market-beta effect.** Lucca–Moench, 1994–2011, verified from the paper:

- CRSP **value-weighted**: **36 bp** differential, Sharpe 0.92 on an FOMC-only strategy.
- CRSP **equal-weighted**: **25 bp** — *smaller*.
- **Smallest size decile: 20 bp.** All remaining deciles: **31–46 bp**, Sharpes 0.80–1.07.
- 49 industry portfolios: **36 of 49** significant at 5%, coefficients from **23 bp**
  (household goods) to **69 bp** (trading firms); 10 industries insignificant.
- Regressing the 59 industry + size portfolio mean FOMC-day returns on their market betas:
  slope **λ = 49 bp**, highly significant; **intercept α not different from zero**;
  **adjusted R² = 64%**. Their words: the observed cross-sectional variation *"is well
  captured by exposure to aggregate market risk."*

**Read that literally: on FOMC days the CAPM works, and there is no alpha.** The entire
cross-sectional spread is beta. A cross-sectional selector conditioned on FOMC dates is
therefore not selecting anything — it is buying beta on a schedule. And the
equal-weighted, small-tilted version this programme is built on gets the **weakest** slice
of it.

**Turn of month — also index-level.** Every canonical measurement (L&S on the DJIA,
McConnell–Xu on CRSP VW and EW indices, the ETF tests) is a **time-series** statement
about the market portfolio. It is not a cross-sectional ranking signal. Present in
**31/35 countries**, present in both VW and EW, present across price and size buckets —
that is the signature of a market-wide time effect, not a name-selection edge.

**Consequence.** A market-wide effect is tradeable through **one instrument at low cost**
(SPY, or an S&P future). The programme's stated breadth constraint — ~2.2 effective
independent instruments across 57 ETFs — is not the binding issue here; the binding issue
is that trading it as an equal-weighted 1,573-name book pays **1,573 round trips to
express one bet you could express with one**. That is strictly dominated.

---

## 8. Does it transfer to OUR universe — bluntly

**No, not in the form the programme is built to trade. Here is the arithmetic.**

1. **The cost wall settles K1a before any test.** Take the *historically strongest*
   classical TOM number — 15 bp/day over four days ≈ **60 bp gross per month**, market
   level. A monthly in-and-out on an equal-weighted single-name book is **one round trip
   per month**. The programme's own measured spread on the names it actually held (D285,
   Corwin–Schultz off the OHLC) was **33.8 bp/side ≈ 68 bp round trip**. That is
   **negative gross-minus-cost using the pre-2001 magnitude**, before per-share commission
   and before the post-2001 decay takes the gross number to roughly zero. The only
   cost-viable expression is a single index instrument — where per-share IBKR charging is
   negligible in bp because SPY-class prices are high — and that is a market-timing
   overlay this programme does not currently run.

2. **Equal weighting hurts K1c specifically.** The property that makes K1 attractive here
   — a calendar rule selects no names, so it escapes the 36.8 bp price-tercile nuisance —
   is the *same* property that hands you Lucca–Moench's equal-weighted **25 bp** and
   smallest-decile **20 bp** instead of the value-weighted 36 bp. And 20–25 bp per event
   is below a 68 bp round trip by a factor of ~3. **Breakeven for K1c on this universe is
   roughly 10–12 bp/side; the measured regime is 33.8 bp/side.** It does not clear.

3. **The event count is thin and the decay lands mid-fixture.** ~133 scheduled FOMC
   announcements in 2010-01-04 → 2026-08-26. Kurov et al.'s documented break is **Jan
   2016**, which splits the fixture into a live-ish first half (44.5 bp on
   press-conference meetings, ~2011–2015) and a dead second half (9.2 bp, 2016–2019). Any
   full-sample number will be a blend of a decayed and a decaying regime, and the
   subsample that "works" is the one that ends before the fixture is half over. **Expect
   the split-by-era report (Reporting group 3) to be the whole story.**

4. **The dead-inclusive, $5-floor, EW universe is the *worst* case for TOM's documented
   gradient.** TOM is strongest in small and low-price names (0.25%/0.27% vs 0.15%/0.19%)
   — exactly the names where per-share cost in bp is largest. This is the D284 failure
   mode restated: the effect and the cost are the same variable.

5. **Daily bars are adequate for K1c but not exactly.** Lucca–Moench's window is
   **2 p.m. to 2 p.m. ET**, which straddles two daily bars. The daily analogue is
   close(t−1) → close(t) on the announcement day, which is what their **36 bp VW /
   25 bp EW** figures actually measure, and which is fine — the paper reports the index is
   *"essentially flat"* around and after the 2:15 p.m. release, so the daily bar does not
   lose much. But note the **announcement time changed twice inside the fixture**:
   ~2:15 p.m. through March 2011; **12:30 p.m. for statement / 2:00 p.m. SEP through
   2012**; **2:00 p.m. jointly since March 2013**, press conference ~2:30 p.m. On daily
   bars this is harmless; do not build any intraday-flavoured assumption on it.

6. **K1b transfers nothing.** A weekday gate on a book with a 40-bar hold barely changes
   exposure, the effect is regime-flipping (Olson et al.), and STW showed it fails against
   20 rules let alone 9,452.

**What I would actually recommend, if twenty minutes are spent:** run **one** runner
computing the **gross** equal-weighted universe mean return by calendar bucket — TOM
[−1,+3], the five weekdays, and FOMC-announcement-day (close-to-close) vs all other days —
purely as a **descriptive measurement of the fixture**, with the time-rotation null
**enumerated exactly** (a single market-level series over ~4,190 bars gives ~4,190 offsets;
per the house rule that makes the p95 SE exactly zero and costs ~6 min). Report it split
2010–2015 vs 2016–2026, because the literature says that is where the break is. Do **not**
build a selector, and do **not** budget for a cost-survival stage — on the numbers above,
K1a and K1c fail breakeven on this universe by roughly 3x before the null is even
consulted. The value of the twenty minutes is a **documented negative with a
pre-registered break date**, plus the programme's first date-derived feature in the
codebase, not a candidate strategy.

---

## 9. Sources

**Read in full (PDF text extracted and quoted above):**

- Sullivan, Timmermann & White, *Dangers of Data-Driven Inference: The Case of Calendar
  Effects in Stock Returns*, UCSD Discussion Paper 98-16, June 1998 — published as
  Journal of Econometrics 105 (2001) 249–286.
  https://escholarship.org/content/qt2z02z6d9/qt2z02z6d9.pdf [PEER-REVIEWED / WORKING PAPER]
- McConnell & Xu, *Equity Returns at the Turn of the Month*, Financial Analysts Journal
  64(2), 2008, 49–64.
  https://business.purdue.edu/faculty/mcconnell/publications/Equity-Returns-at-the-Turn-of-the-Month.pdf
  [PEER-REVIEWED]
- Lucca & Moench, *The Pre-FOMC Announcement Drift*, draft 28 Feb 2013 (published Journal
  of Finance 70(1), 2015). https://conference.nber.org/confer/2013/MEs13/Lucca_Moench.pdf
  [PEER-REVIEWED / WORKING PAPER]

**Abstract or summary level only (full text paywalled — flagged where numbers are unverified):**

- Han, Han & Tian, *The disappearing turn-of-month effect*, Finance Research Letters 71
  (2025). https://ideas.repec.org/a/eee/finlet/v71y2025ics1544612324014909.html
  (abstract verbatim, verified) — https://www.sciencedirect.com/science/article/abs/pii/S1544612324014909
  (403, body unread) [PEER-REVIEWED; the "2001–2020 insignificant" and "0.10%/day" figures
  are **UNVERIFIED**, from search summary]
- Kurov, Wolfe & Gilbert, *The disappearing pre-FOMC announcement drift*, Finance Research
  Letters 40 (2021). https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/ [PEER-REVIEWED;
  numbers read from the open-access PMC copy]
- Etula, Rinne, Suominen & Vaittinen, *Dash for Cash: Monthly Market Impact of
  Institutional Liquidity Needs*, Review of Financial Studies 33(1), 2020, 75–111.
  https://econpapers.repec.org/article/ouprfinst/v_3a33_3ay_3a2020_3ai_3a1_3ap_3a75-111..htm
  (abstract verbatim) — https://academic.oup.com/rfs/article-abstract/33/1/75/5494694
  [PEER-REVIEWED; sample period and magnitudes **UNVERIFIED**]
- Plastun, Sibande, Gupta & Wohar, *Rise and Fall of Calendar Anomalies over a Century*,
  North American Journal of Economics and Finance 49 (2019) 181–205.
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3362148 ·
  https://repository.up.ac.za/bitstreams/1d1c2ddd-f5be-45b3-95f0-462abe301799/download
  [PEER-REVIEWED / WORKING PAPER; read at summary level]
- Olson, Mossman & Chou, *The evolution of the weekend effect in US markets*, Quarterly
  Review of Economics and Finance 58 (2015) 56–63.
  https://www.sciencedirect.com/science/article/abs/pii/S106297691500006X ·
  preprint: https://www.researchgate.net/profile/Dennis-Olson-3/publication/271141367_The_Evolution_of_the_Weekend_Effect_in_US_Markets
  [PEER-REVIEWED; read at summary level]
- Cieslak, Morse & Vissing-Jorgensen, *Stock Returns over the FOMC Cycle*, Journal of
  Finance 74(5), 2019, 2201–2248. https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12818 ·
  free draft: https://faculty.haas.berkeley.edu/morse/research/papers/cycle_paper_cieslak_morse_vissingjorgensen.pdf
  [PEER-REVIEWED; read at summary level]
- Ariel, *A monthly effect in stock returns*, Journal of Financial Economics 18(1), 1987,
  161–174. https://econpapers.repec.org/RePEc:eee:jfinec:v:18:y:1987:i:1:p:161-174
  [PEER-REVIEWED; read at summary level]
- Lakonishok & Smidt (1988) — numbers taken **second-hand from McConnell & Xu's**
  description of it (0.473% vs 0.349%, DJIA 1897–1986). Original not opened.
  [PEER-REVIEWED, second-hand]
- *Infrequent rebalancing, risk deferral, and equity returns at the turn of the month*,
  J. Int. Fin. Markets Inst. & Money (2026).
  https://www.sciencedirect.com/science/article/abs/pii/S1042443126000259
  [PEER-REVIEWED; +7.8 bp / +20 bp figures **UNVERIFIED**, from search summary]
- *Calendar anomalies: Real patterns or data-mining artifacts?*, North American Journal of
  Economics and Finance (2026).
  https://www.sciencedirect.com/science/article/pii/S1062940826000756 — **403, could not
  open.** Search summary indicates it concludes several calendar anomalies were real
  historically but with diminished economic relevance in recent decades. [PEER-REVIEWED;
  **UNVERIFIED**, and directly on-topic — worth a second attempt with library access.]

**Primary data documentation:**

- Federal Reserve, *Meeting calendars and information* (2021–2027):
  https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm [PRIMARY DATA DOC]
- Federal Reserve, *Historical Materials by Year* (per-year pages back to 1936, e.g.
  https://www.federalreserve.gov/monetarypolicy/fomchistorical2020.htm):
  https://www.federalreserve.gov/monetarypolicy/fomc_historical_year.htm [PRIMARY DATA DOC]

**Non-refereed / commercial — treat as sales or opinion instruments:**

- *Turn-of-the-Month Strategies: Do They Still Work?* —
  https://www.quantseeker.com/p/turn-of-the-month-strategies-do-they [NOT PEER-REVIEWED,
  independent newsletter]
- *Trading the Fed: The Pre-FOMC Drift is Alive* —
  https://www.quantseeker.com/p/trading-the-fed-the-pre-fomc-drift [NOT PEER-REVIEWED]
- NY Fed Liberty Street Economics, *The Pre-FOMC Announcement Drift: More Recent Evidence*
  (Nov 2018) —
  https://libertystreeteconomics.newyorkfed.org/2018/11/the-pre-fomc-announcement-drift-more-recent-evidence/
  [CENTRAL-BANK BLOG, NOT PEER-REVIEWED, and a follow-up on the authors' own result]
- FPA Journal, *The Turn-of-the-Month Anomaly in the Age of ETFs* (Apr 2011) —
  https://www.financialplanningassociation.org/article/journal/APR11-turn-month-anomaly-age-etfs-reexamination-return-enhancement-strategies
  [PRACTITIONER PUBLICATION — not read, listed for completeness]
- Quantpedia, *Turn of the Month in Equity Indexes* —
  https://quantpedia.com/strategies/turn-of-the-month-in-equity-indexes
  [SALES INSTRUMENT — subscription strategy database; not used for any claim above]
- ASU News, *ASU research helps debunk myth of stock market 'weekend effect'* (Feb 2017) —
  https://news.asu.edu/20170201-discoveries-asu-research-debunks-myth-stock-market-weekend-effect
  [UNIVERSITY PRESS RELEASE — the Smith & Robins −18.1 bp / −5 bp figures come from here,
  not from the paper itself; **UNVERIFIED**]
- borisjoffe/FOMC-dates.js — https://github.com/borisjoffe/FOMC-dates.js
  [UNVERIFIED THIRD PARTY — covers only post-2020, last updated 2024-04-11, does not
  distinguish scheduled from unscheduled. **Do not use.**]

**What I could not verify.** ScienceDirect, SSRN and Oxford Academic all returned HTTP
403 to this environment, so five relevant papers (Han/Han/Tian body, Dash-for-Cash body,
the 2026 *Calendar anomalies: real patterns or data-mining artifacts?*, the 2026
infrequent-rebalancing paper, and Olson et al. body) were read only at abstract or
search-summary level. Every number sourced that way is tagged **UNVERIFIED** above. I did
not open Lakonishok & Smidt (1988) or Ogden (1990) directly — both are quoted second-hand
through McConnell & Xu and Han et al. respectively.

**Safety note.** No page, PDF or search result encountered during this research contained
text addressed to the agent or instructions to take any action. Nothing was downloaded
beyond three research PDFs auto-cached by the fetch tool into the session's tool-results
directory (Sullivan–Timmermann–White, McConnell–Xu, Lucca–Moench), which were read
locally for text extraction and are outside the repository.
