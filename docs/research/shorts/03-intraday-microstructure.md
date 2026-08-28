# 03 — Intraday Microstructure: Candidate Short Signals for an Intraday-Only Book

**Status:** web research only. No backtests run. No repo code touched.
**Date:** 2026-08-28
**Question:** we have established on our own data that +8.59%/yr of equity drift accrues overnight and
intraday (open→close) is −0.36%/yr, so an intraday-only book faces no drift headwind. The structural door
is open. What does the literature offer as an intraday short signal?

---

## 0. Bottom line up front

1. **The cost hurdle is the binding constraint, and it kills most of the literature outright.** At 1.85 bp/side,
   a position that opens and closes within a session costs **3.70 bp per round trip**. Expressed per trade
   rather than per year, this is the single number that decides everything. The three best-documented
   market-level intraday effects — Gao et al. (2018) intraday momentum, Baltussen et al. (2021) intraday
   momentum, Baltussen–Da–Soebhag (2025) end-of-day reversal — deliver **2.65, 2.72 and 3.78 bp per round
   trip gross** respectively. All three are *below* 3.70 bp. They are not marginal; they are arithmetically
   dead as standalone daily-traded strategies at our cost level. The papers' own authors say so
   (§2.1, §2.2, §3.1 below).

2. **The effects that DO clear the hurdle live in the cross-section of individual stocks, not in a
   57-name liquid-ETF panel.** The magnitudes that beat 3.70 bp/trade — Lou–Polk–Skouras' −1.96%/mo
   intraday alpha on the high-past-overnight decile, Hendershott–Livdan–Rösch's −7.7 bp/day-per-unit-beta
   day-time security market line — are driven by cross-sectional *dispersion* in beta, volatility and retail
   attention that a universe of 57 liquid ETFs simply does not have. This is a dispersion problem, not a
   mechanism problem: the mechanism replicates, the spread does not.

3. **There is a serious prior threat to the premise itself that must be tested before any signal work.**
   Lachance (2021, *Journal of Financial Markets*) shows that positive order imbalance at the open plus
   wider overnight spreads **artificially inflate ETF overnight returns by 2.54 bp/day = 6.61%/yr**, and
   that correcting for microstructure **eliminates three quarters of the ETF overnight/intraday return
   gap**. Our measured gap is 8.59 − (−0.36) = **8.95 points**. Three quarters of 8.95 is 6.7 — which
   matches Lachance's 6.61%/yr almost exactly. **Our headline finding may be predominantly a trade-price
   artifact.** §1 gives a concrete diagnostic runnable on data we already have.

4. **Two candidates are worth pursuing** (full detail §8): a **volatility-regime-conditioned cross-sectional
   day/night risk sort**, and a **lagged overnight/intraday-persistence name selector**. Both are
   cross-sectional, both are computable from data we already hold, and — crucially — the second adds
   **zero incremental turnover**, because it only decides *which* names go in a book that is paying the
   round trip anyway.

---

## 1. PREREQUISITE: is our +8.59%/yr overnight drift real, or a trade-price artifact?

This is the most important thing in this document. It is not a candidate signal; it is a test that should
run before any of the candidates.

### The claim

Lachance (2021), *"ETFs' high overnight returns: The early liquidity provider gets the worm"*,
Journal of Financial Markets.
<https://www.sciencedirect.com/science/article/abs/pii/S138641812030032X>

- ETF order flow at the open carries a **structural positive imbalance exceeding 10%**.
- Positive imbalance biases *trade* prices upward relative to mid, and the bias scales with the spread.
- Spreads around the open are **three to four times higher** than during the day.
- Net effect: an **artificial +2.54 bp/day (6.61%/yr)** added to measured ETF overnight returns.
- Correcting for microstructure **removes about three quarters of the ETF overnight/intraday gap.**

Companion result: Lachance (2022), "ETFs' two-sided trading costs and order imbalances",
*Financial Review* — imbalances bias midpoint quotes as well as trade prices, producing observed
premiums/discounts. <https://onlinelibrary.wiley.com/doi/10.1111/fire.12292>

Elm Wealth's practitioner replication reaches the same place from the other direction: opening and closing
prints "are simply not reflective of actual prices available to market participants", and
**"round-trip transaction costs of 1 basis point ... reduce returns by about 5% per annum"**, so that
**"a trader executing small sizes and paying only 1bps per trade would not have made any money in the last
8 years."** <https://elmwealth.com/night-moves-overnight-drift/>

### Why this bites us specifically

Our 15-minute OHLCV bars are built from **trade prints**. The 09:30–09:45 bar's open is the first print (or
the opening auction), which is exactly the price Lachance shows is inflated. Our "overnight return"
(prev close print → open print) therefore inherits the full bias; our "intraday return" (open print →
close print) inherits it with the opposite sign.

The strategic consequence is *not* symmetric and it cuts against us:

- The measured intraday leg of −0.36%/yr is **biased downward** by the same amount the overnight leg is
  biased upward. The true tradable intraday drift is **less negative** — i.e. more of a headwind for a
  short book than we currently believe.
- A backtested short entered at the open print sells at an **inflated** price it could not actually have
  hit (you sell at the bid, not at the buy-imbalance-driven print). Backtested intraday shorts are
  therefore **optimistic**, possibly by several percent per year.

This is a plausible re-reading of our own D-series result: the short arm's held bars moving from
+4.72%/yr to −4.27%/yr on removing the overnight gap is exactly what a 6–9 point measurement wedge between
the two legs would produce, whether or not any economic effect exists.

### The diagnostic (runnable now, no new data)

Recompute the overnight/intraday split three ways and compare:

| Variant | "Open" price used | What it tests |
|---|---|---|
| A (current) | 09:30 print | baseline |
| B | **close of the 09:45 bar** | removes the opening-auction/imbalance print entirely |
| C | **VWAP of the first two 15-min bars** | Lou–Polk–Skouras' own robustness check (they use first-half-hour VWAP "to ensure tradability") |

Symmetrically, test skipping the last 15-minute bar at the close (Bogousslavsky & Muravyev's closing-price
concern; Baltussen–Da–Soebhag re-run their whole result skipping the last 5 minutes for this reason).

**Kill criterion:** if the overnight leg drops from +8.59%/yr toward ~+2%/yr under variants B/C, the
premise "an intraday-only book faces no drift headwind" is substantially a measurement artifact and every
candidate below should be re-scoped against the corrected baseline before any capital is modelled.

### Second prior threat: the overnight drift may simply be decaying

- **Boyarchenko, Larsen & Whelan (2026), "The Disappearing Overnight Drift"**, NY Fed Liberty Street
  Economics / SSRN 7035838. The 02:00–03:00 ET window (European open) that produced **3.7%/yr in
  1998–2020 and >60% of the ES contract's 5.9%/yr close-to-close return has averaged close to zero since
  January 2021**, across ES, NQ and YM. Their diagnosis: the dispersion of end-of-day order imbalances
  collapsed — **stdev of end-of-day relative signed volume fell from 6.5% to 2.9%** — so liquidity
  providers no longer carry the inventory risk they were being paid for. Volatility and overnight
  liquidity were roughly unchanged.
  <https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/>
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7035838>
- Elm Wealth's long-short overnight-vs-intraday portfolio: ~38%/yr gross over 1995–2022, but five-year
  rolling returns show a clear break — **post-2012 performance deteriorates markedly**.

Caveat, stated fairly: the NY Fed result is about a *specific one-hour window in futures*, not the full
close-to-open ETF return. But the mechanism they identify (compressed closing imbalances) is the same
mechanism Lachance identifies as the source of the ETF overnight premium. If closing/opening imbalances
are structurally smaller post-2021, both the artifact and the economic effect shrink together. Our sample
is 2018–2026: **roughly 60% of it is post-2021.** A split-sample test of the overnight/intraday gap
(2018–2020 vs 2021–2026) is cheap and should be run alongside the diagnostic above.

---

## 2. Intraday momentum / the "last half hour" effect

### 2.1 Gao, Han, Li & Zhou (2018), "Market intraday momentum", *JFE* 129(2), 394–414

<https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351> ·
SSRN: <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866>

**Claim.** The first half-hour return (prev close → 10:00), `r1`, predicts the last half-hour return
(15:30 → 16:00), `r13`, on SPY. Sample 1993–2013.

**Effect size (their numbers).**

| Strategy | Ann. return | Std dev | Sharpe | Success rate |
|---|---|---|---|---|
| η(r1) — long if r1>0, short if r1<0, held 15:30–16:00 | **6.67%** | 6.19% | **1.08** | 54.37% |
| η(r12) — using the 12th half-hour | 1.77% | — | 0.29 | 50.93% |
| η(r1, r12) — trade only when signs agree | 4.39% | — | — | **77.05%** |
| *Always Long* the last half hour | — | 6.21% | **−0.18** | 50.42% |
| Buy-and-hold | — | 20.57% | 0.29 | — |

**Is there a short side?** Yes — η(r1) is explicitly symmetric, long on positive-r1 days and short on
negative-r1 days, and the two sides are roughly 50/50. The paper does not report the legs separately.
Note the important structural fact hidden in the table: ***Always Long* in the last half hour has a
NEGATIVE Sharpe of −0.18.** The unconditional 15:30–16:00 window is a mildly negative-drift window. That
is a genuine structural tailwind for a short, but it is small.

**Conditioning — and this is the useful part.** Sorting days into terciles by first-half-hour realised
volatility:

| First-half-hour volatility tercile | R² (joint predictors) |
|---|---|
| Low | 0.6%, r1 coefficient insignificant |
| Medium | intermediate, significant |
| **High** | **3.3% — more than 5× the low tercile** |

Same qualitative pattern for volume terciles, recession days, low-trade-size days, and major macro
release days. Terciles are 33% of sessions each, so the high-vol tercile has real breadth.

**Costs.** They model the quoted spread from TAQ. Post-2005 (spread stabilised near **1.2 bp**),
η(r1) delivers **6.52%/yr net vs 7.96%/yr gross — a drag of ~1.44%/yr**. They conclude intraday momentum
"survives transaction costs."

**Costs at OUR level — this is the decisive arithmetic.** Their ~1.44%/yr drag over 252 daily round trips
implies an effective ~0.57 bp/round trip. Ours is **3.70 bp**, i.e. **6.5× theirs**. Redoing their own
post-2005 sum with our costs:

```
7.96%/yr gross  −  252 × 3.70 bp  =  7.96%  −  9.32%  =  −1.36%/yr net
```

Per-trade view: **2.65 bp gross per round trip vs a 3.70 bp hurdle.** Fails by 28%.
The selective variant η(r1, r12) trades only when r1 and r12 agree; even generously assuming that halves
the trade count, 4.39%/yr over ~126 trades is **3.48 bp/trade** — still under the hurdle.

**Other ETFs (their Table 12).** In-sample R² ranges 1.16% (DIA) to 8.54% (EEM); out-of-sample 0.70% (QQQ)
to 6.53% (EEM). Annualised timing returns: IWM 11.72%, QQQ 7.75%, DIA 3.46%, TLT 4.03%. Also XLF, IYR,
EEM, FXI, EFA, VWO. Only IWM's 11.72%/yr clears 9.32%/yr — and by 2.4 points, on one name, in-sample,
ending 2013.

**Look-ahead:** clean. `r1` closes at 10:00 and predicts a 15:30–16:00 return.
**Concurrency:** severe. This is a **pure market timer**, not a diversified book. A single signal derived
from SPY's morning return sets the position on every name simultaneously. It should be scored as one bet
per day, not 57.

### 2.2 Baltussen, Da, Lammers & Martens (2021), "Hedging demand and market intraday momentum", *JFE* 142, 377–403

<https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598> ·
PDF: <https://academicweb.nd.edu/~zda/intramom.pdf>

**Claim.** The *rest-of-day* return `rROD` (prev close → 15:30) predicts the last half hour better than
`rONFH` does. 60+ futures across equities, bonds, commodities, FX, **1974–2020**. Mechanism: **short-gamma
delta hedging** by option market makers and **leveraged-ETF rebalancing**, both of which force trading in
the direction of the day's move into the close.

**Effect size (Table 6, equity index futures, 1/N portfolio).**

| Strategy | Ann. ret | Std dev | Sharpe | Success |
|---|---|---|---|---|
| η(rONFH) | 4.21% | 3.95% | 1.07 | 0.55 |
| η(rONFH, rROD) | 5.47% | 3.42% | 1.60 | 0.61 |
| **η(rROD)** | **6.86%** | 3.96% | **1.73** | 0.55 |
| Always Long (last 30 min) | 0.44% | 4.20% | 0.11 | 0.53 |
| Buy & Hold | 8.76% | 17.29% | 0.51 | 0.54 |

Bonds SR 1.62, commodities 1.42, FX 0.87. Effect present in both 1974–1999 and 2000–2020 subsamples.

**Per-trade:** 6.86%/yr over 252 daily round trips = **2.72 bp/trade vs 3.70 bp hurdle. Fails.**
Note also that the strategy's 6.86%/yr gross is *below* futures buy-and-hold's 8.76%/yr; only its Sharpe
is better, because it is exposed for 30 minutes a day.

The authors are explicit: *"we do not consider transaction costs ... the strategy as presented might not be
exploitable to many investors after accounting for transaction costs."* Their own positive case is that
**S&P 500 futures at one tick** yields a positive net Sharpe — a cost level (~0.5 bp) we do not have on
ETFs.

**Gamma conditioning.** Regressing `rLH` on `rROD` conditional on the sign of net gamma exposure (NGE):
intraday momentum is **much more pronounced on negative-NGE days and statistically absent on positive-NGE
days.** Breadth: **2,930 negative-NGE days vs 3,158 positive** in 1996–2020, so ~48% of sessions.
Conditioning roughly doubles the per-trade edge while halving the trade count — which is exactly the right
shape for a cost-constrained book. **But NGE requires OptionMetrics or SqueezeMetrics data. We do not have
it.** (Partial workaround in §7.)

**Reversal.** `rLH` reverses over the following days: equity futures coefficient −14.51 (t=−1.70) at 1 day,
−29.05 (t=−3.16) at 2 days, −27.98 (t=−2.61) at 3 days. **But R² is 0.13–0.27%.** This is a
mechanism-confirming result, not a tradable multi-day signal.

**Look-ahead:** clean. **Concurrency:** total — it is a market timer by construction.

### 2.3 Post-publication and replication evidence

- **Limkriangkrai, Chai & Zheng (2023), "Market intraday momentum: APAC evidence"**, *Pacific-Basin
  Finance Journal* 80, 102086 (open access).
  <https://researchmgt.monash.edu/ws/files/519509174/494419119_oa.pdf>
  Tests ETFs in China, Hong Kong, Japan, Singapore, Korea. **Present in China and Japan, weak in Korea,
  ABSENT in Hong Kong and Singapore.** Volatility matters more than volume. Notably, the effect is
  **weaker during COVID-19** in the markets where it exists — the opposite of the "stronger in crises"
  story, and directly relevant to our own 2020-concentration concerns. Conclusion: "not as pervasive in
  the APAC markets when compared to the US evidence."
- **Contradictory out-of-sample record.** Some work finds ITSM survives out-of-sample globally
  (Elaut/Erdős et al. style, *Journal of International Financial Markets, Institutions & Money*,
  <https://www.sciencedirect.com/science/article/abs/pii/S138641812100001X>); other work documents that
  the predictability **disappears out-of-sample**. This is an unresolved literature, which is itself a
  reason for caution.
- **Wu (2023), "High Frequency Trading and Intraday Momentum"** (EFMA).
  <https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2023-UK/papers/EFMA%202023_stage-4455_question-Full%20Paper_id-31.pdf>
  Finds **HFT participation reduces intraday momentum** by speeding information digestion. This is a
  structural decay argument, not just a statistical one, and HFT share of ETF volume in 2018–2026 is far
  above the 1993–2013 sample that generated the original result.
- **Chen & Welch (2026), "What Useful Alphas?"** (Federal Reserve Board / UCLA) and Chen & Zimmermann's
  broader work put typical post-publication decay for published equity anomalies at **~26%** in-sample-to-
  post-publication, with 25–50% haircuts across pools. Applying even the mild 26% haircut to Gao et al.'s
  6.67%/yr gives **4.9%/yr — a 1.96 bp/trade edge against a 3.70 bp hurdle.**

### 2.4 The practitioner variant — Zarattini, Aziz & Barbon (2024)

*"Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)"*, SSRN 4824172.
<https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172>

Reported: 1,985% total, **19.6%/yr, Sharpe 1.33, net of costs, 2007–early 2024** on SPY. Mechanism:
"noise area" bands = opening price × (1 ± average intraday-return-to-this-minute over the last 14 days),
with the bands shifted by the prior overnight gap; enter on breakout, trailing stops, flat at close.

**Assess sceptically and do not pursue.** Reasons:
1. It trades **intraday breakouts with trailing stops**, i.e. **multiple round trips per session**. Our
   own arithmetic already excludes 5–20 round trips/day (31–187%/yr). This is squarely in that band.
2. The band construction has a **14-day lookback, a bar-of-day-conditional average, an overnight-gap
   adjustment, and a trailing-stop rule** — four fitted degrees of freedom, on one instrument, with no
   pre-registration. A follow-up (Maróy, SSRN 5095349) improves it further "using parameter optimization
   and different exit strategies", which is a tell rather than a corroboration.
3. Non-peer-reviewed, published by a firm that sells the strategy.

### 2.5 Corroborating negative result

**Mesfin (2026), "Structural Limits of OHLCV-Based Intraday Signals in MNQ Futures: A Systematic
Falsification Study"**, arXiv:2605.04004. <https://arxiv.org/abs/2605.04004>

Single-author, not peer-reviewed — weight accordingly — but methodologically close to our own programme
and worth reading. Tested **14 signal families** over **947 trading days of 5-minute MNQ data (2021–2025)**
under walk-forward validation with a pre-set bar: t ≥ 2.0, ≥30 trades, positive net of a 2-point round-trip
friction, consistent across years. **Nothing passed.** Max gross edge across all families: 0.07–1.50 points
per trade against a 2-point friction. His framing — *"the gross edge is real but too small to survive
friction"* — is the same conclusion this document reaches from the published literature.

Two of his results map directly onto ours:
- **Gap fill fade fails at every entry time** (09:30, 09:45, 10:00): mean net −1.31 to −2.24 pts,
  t = −0.32 to −0.59, win rate 47–48%. Indistinguishable from noise.
- **Gap continuation short** with a Kalman velocity filter: **t = +3.23, mean net +14.52 pts, 68.2% win
  rate — but only 22 trades in 947 days (2.3% of sessions)**, so he rejects it on his own N≥30 rule.

That last one is *precisely* the failure mode we killed our own gap-tail candidate on (z ≤ −3 → −37.52%/yr
being entirely COVID). Two independent studies, different instruments, same trap: **the overnight gap
produces a large conditional edge on a vanishingly small number of sessions.** `exposure × edge` is
negligible and the estimate is dominated by a handful of crisis days. Treat the gap-tail family as closed.

---

## 3. End-of-day reversal — the strongest *effect*, and still not tradable for us

**Baltussen, Da & Soebhag (2025), "End-of-Day Reversal"**, SSRN 5039009 (2nd place, Quantpedia Awards
2025). <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5039009> ·
PDF: <https://academicweb.nd.edu/~zda/EOD.pdf>

**Claim.** In the **cross-section of individual stocks**, the rest-of-day-to-15:00 return (`ROD3`) *negatively*
predicts the last-half-hour return. Note the deliberate design: they **skip the 15:00–15:30 half hour**
between predictor and predicted return, so this is not bid-ask bounce. Sample **1993–2019**, NYSE/NASDAQ/
AMEX, microcaps and sub-$5 stocks excluded.

**Effect size.**

| Portfolio | Gross |
|---|---|
| Value-weighted long-short (L−H) | **3.78 bp/day = 9.5%/yr**, t > 10 |
| Equal-weighted long-short | **6.86 bp/day = 17.3%/yr** |
| Smallest 20% of firms, 6-factor alpha | 14.71 bp/day, t = 27.20 |
| **Largest 20% of firms, 6-factor alpha** | **3.41 bp/day, t = 10.61** |

**Robustness is genuinely exceptional** — significant in almost every 3-year rolling window, across size,
volume, Amihud illiquidity, realised vol, overnight vol and mispricing-score quintiles, in trade prices and
in quote midpoints, robust to skipping the last 5 minutes.

**Where the profit comes from — and why this is bad news for a SHORT book.** The abstract is explicit:
the effect *"primarily comes from **positive price pressure on intraday losers**."* Over 27 years the
bottom decile of intraday losers gained ~400% while **the decile of intraday winners returned close to
zero**. The profitable leg is **long the losers**. The short leg (shorting intraday winners into the close)
is the weak half. For a short-only mandate this is close to the worst possible split.

**Costs.** The authors' own paragraph: the strategy *"requires frequent rebalancing"* and *"as presented
might not be exploitable by many investors after accounting for transaction costs"*, with the escape
hatches being market-makers/prop desks, more extreme deciles, and folding the signal into already-planned
trades.

**At our costs.** A long-short requires **two** round trips per day = **7.40 bp**.

| Variant | Gross bp/day | Cost bp/day | Net |
|---|---|---|---|
| Value-weighted L−S | 3.78 | 7.40 | **−3.62** |
| Equal-weighted L−S | 6.86 | 7.40 | **−0.54** |
| Largest-20% subsample | 3.41 | 7.40 | **−3.99** |

Every variant is negative, and the large-cap subsample — the only one whose liquidity resembles our
universe — is the worst. And this is a **30-minute holding period**, so the cost is paid against 30
minutes of edge.

**Does it transfer to ETFs at all?** Almost certainly not. The paper's own decomposition explains why:
*"positive cross-stock autocorrelations outweigh the positive autocorrelations for each individual stock
... individual stock (and market) returns display momentum in the time-series but due to strong cross-stock
autocorrelations display end-of-day reversal in the cross-section."* The reversal **is** the residual after
the common factor is netted out. In a 57-ETF panel where nearly all names load on one or two factors, the
idiosyncratic residual — which is the entire signal — is tiny. **At the market level this same paper
confirms MOMENTUM, not reversal.** Do not attempt an ETF version.

**Data:** TAQ second-level trades. **We do not have it.**
**Verdict: closed.** Strong science; wrong instrument, wrong side, wrong cost regime.

---

## 4. Overnight vs intraday decomposition — the literature closest to our own finding

### 4.1 Lou, Polk & Skouras (2019), "A tug of war: Overnight versus intraday expected returns", *JFE* 134, 192–213

<https://www.sciencedirect.com/science/article/abs/pii/S0304405X19300650> ·
PDF: <https://personal.lse.ac.uk/polk/research/TugOfWar.pdf>

This is the paper that most directly names conditions under which **the intraday leg is reliably negative**.
Sample **1993–2013**, US, excluding sub-$5 and bottom-NYSE-size-quintile stocks, value-weighted.

**(a) Strategy-level decomposition (their Table 2, monthly CAPM alphas).**

| Strategy | Overnight | Intraday |
|---|---|---|
| MOM (12-1 price momentum) | **+0.98%** (3.84) | −0.02% (−0.06) |
| INDMOM | **+1.07%** (6.47) | **−0.63%** (−2.03) |
| STR (short-term reversal) | **+0.93%** (4.28) | **−1.05%** (−3.25) |
| SUE | +0.56% (3.20) | +0.21% (0.70) |
| **BETA** (long low-β, short high-β) | **−0.49%** (−2.17) | **+0.70%** (2.40) |
| **IVOL** (long low-ivol, short high-ivol) | **−1.46%** (−5.23) | **+2.48%** (6.21) |
| ROE | −0.95% (−6.25) | +1.42% (5.58) |
| ISSUE | −0.52% (−3.27) | +1.13% (6.13) |
| ACCRUALS | −0.47% (−3.25) | +1.10% (4.73) |
| TURNOVER | −0.29% (−1.98) | +0.57% (2.58) |
| BM | −0.10% (−0.67) | +0.48% (2.21) |
| INV | −0.28% (−2.10) | +0.97% (4.39) |

Read the BETA and IVOL rows in the direction we care about. Both strategies are **long the low-risk decile
and short the high-risk decile**. Both earn **more than 100% of their premium intraday** and *lose* money
overnight. Restated as a short mandate:

> **Shorting high-beta names intraday earns +0.70%/mo; shorting high-idiosyncratic-volatility names
> intraday earns +2.48%/mo (t = 6.21, ≈ +29.8%/yr). Both lose money if held overnight.**

That is the literature's clearest statement of the structure we are trying to exploit, and it is a
**cross-sectional** statement — which is what makes it survivable, because it can be selective about names.

**(b) The persistence result — the highest-value finding in this document for a low-turnover signal.**

Their Table 1 sorts all stocks at month-end into deciles on **lagged one-month overnight** or **lagged
one-month intraday** returns and holds a value-weighted long-short:

*Panel A — sorted on lagged one-month OVERNIGHT return:*

| Decile | Overnight (3-factor α) | Intraday (3-factor α) |
|---|---|---|
| 1 (low past overnight) | −1.73% (−9.77) | **+1.06%** (4.15) |
| **10 (high past overnight)** | +1.74% (8.69) | **−1.96% (−9.03)** |
| 10−1 | +3.47% (16.83) | **−3.02% (−9.74)** |

*Panel B — sorted on lagged one-month INTRADAY return:*

| Decile | Overnight | Intraday |
|---|---|---|
| 1 | +1.35% (5.04) | −2.14% (−6.95) |
| 10 | −0.42% (−2.64) | +0.27% (1.57) |
| 10−1 | −1.77% (−7.89) | **+2.41% (7.70)** |

**The single most actionable line: decile 10 by lagged one-month overnight return earns a three-factor
intraday alpha of −1.96%/mo, t = −9.03 (≈ −23.5%/yr).** Shorting that decile, intraday only, is a
+23.5%/yr gross alpha against a 8.90%/yr cost.

**And it persists for years.** Their Fig. 2 plots the t-statistics of the persistence test at increasing
lags: **statistical significance up to five years later.** International evidence, using EWMA overnight and
intraday returns with a **60-month half-life**, forecasts subsequent overnight and intraday returns with
**t = 5.10 and 4.60** value-weighted. The signal is *slow*. That is exactly what a cost-constrained book
needs: a **name-selection** variable, not a timing variable.

**Mechanism.** Persistent clientele order flow — some investors habitually trade at the open (retail,
attention-driven, sentiment-loaded), others through the day and at the close (institutions, arbitrageurs).
Because the clienteles are persistent, so are their price footprints, and the two pull in opposite
directions — hence "tug of war."

**Look-ahead:** clean, and unusually so — the conditioning variable is a *lagged* realised return,
observable months or years before the return it predicts.
**Concurrency:** moderate. Sorting 57 ETFs on lagged overnight return will not produce independent bets;
it will persistently select the same high-beta/high-vol names (§8 treats this honestly).
**Data:** daily OHLC only. **We have this back to 2013**, which gives ~5 years of pre-sample for signal
formation before the 15-minute panel starts in 2018.

### 4.2 Hendershott, Livdan & Rösch (2020), "Asset pricing: A tale of night and day", *JFE* 138(3), 635–662

<https://www.sciencedirect.com/science/article/abs/pii/S0304405X20301732> ·
PDF: <http://faculty.haas.berkeley.edu/hender/CAPMday-night.pdf>

**Claim.** The security market line has **opposite signs day and night**. US 1992–2016, 39 non-US countries
1990–2014.

**Fama-MacBeth slopes on beta, ten beta-sorted portfolios:**

| | Slope (bp/day) | t | Intercept (bp/day) | Avg R² |
|---|---|---|---|---|
| **Day (open→close), value-weighted** | **−7.7** | −5.52 | +15.2 | 39.4% |
| Night (close→open), value-weighted | +6.4 | 7.77 | −0.8 | 41.7% |
| Day, equal-weighted | **−13.5** | −8.68 | — | — |
| Night, equal-weighted | +12.1 | 13.39 | — | — |

Decile extremes: **the highest-beta portfolio has the LOWEST day return (−8 bp/day) and the HIGHEST night
return (+20 bp/day).** Beta alone explains **92.2% of the cross-sectional variation in day returns and
96.2% at night**. A Patton–Timmermann test rejects non-monotonicity in both directions.

**Crucially for us: it holds for INDUSTRY portfolios.** Their Fig. 5 and §3.2 add 10 Fama-French industry
portfolios and 25 size/BM portfolios; beta accounts for **60% of the variation in day returns for the ten
industry portfolios**. This is the closest thing in the literature to a statement about **sector ETFs**,
which are the bulk of a 57-name liquid-ETF universe.

**Mechanism.** Leverage-constrained speculators/day-traders express bullishness by buying high-beta and
shorting low-beta at the open, then flatten before the close to avoid overnight margin and gap risk. The
same overnight-cost mechanism Bogousslavsky (2021) uses (see §4.3).

**Their headline strategy numbers, and why to discount them.** Betting-on-beta at night / against-beta by
day: individual-stock version **25.2%/yr, Sharpe 2.03**; portfolio version **108.4%/yr, Sharpe 3.78**.
Ignore these. They are gross, they are on decile portfolios of all US common stocks including the
extremes of the beta distribution, and they require two full round trips per day (flip at open, flip back
at close) plus short borrow on both legs.

**The number that transfers is the slope, and it is uncomfortably tight at our costs.** Note first that the
**+15.2 bp/day day intercept does not transfer** — it implies a beta-1 portfolio earning +7.5 bp/day
(≈ +19%/yr) intraday, which contradicts both the well-known near-zero intraday market return and our own
measurement of −0.36%/yr. That intercept is the CRSP-universe trade-price artifact of §1. **Use only the
slope**, anchored to our own measured intraday market return:

```
intraday return of ETF with beta β  ≈  (our measured intraday market return)  +  (−7.7 bp/day) × (β − 1)
```

| Construction | Gross bp/day | Cost bp/day | Net bp/day | Net %/yr |
|---|---|---|---|---|
| Short-only, β = 1.4 ETF | 7.7 × 0.4 = 3.08 | 3.70 | **−0.62** | ≈ −1.6% |
| Long-short, β = 1.4 vs β = 0.4 | 7.7 × 1.0 = 7.70 | 7.40 | **+0.30** | ≈ +0.8% |
| Long-short, equal-weighted slope (−13.5) | 13.5 | 7.40 | **+6.10** | ≈ +15% |

**Break-even beta spread at the value-weighted slope is Δβ = 0.96.** A 57-name liquid-ETF universe can
just about produce that (e.g. semiconductor/tech/small-cap growth at β ≈ 1.3–1.5 against utilities/staples/
long Treasuries at β ≈ 0.0–0.4), but with essentially **no margin**. This is why §8's candidate #1 is the
*volatility-conditioned* version rather than the unconditional one: the conditioning is what buys the
margin.

**Decay risk.** Sample ends 2016; published 2020. No post-publication test found. Bogousslavsky (2021)
reports the related end-of-day pattern **strengthens in the second half of his sample**, which is mildly
encouraging, but is not a test of this specific slope in 2018–2026.

### 4.3 Bogousslavsky (2021), "The cross-section of intraday and overnight returns", *JFE* 141(1), 172–194

<https://www.sciencedirect.com/science/article/abs/pii/S0304405X21000854> ·
SSRN: <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2869624>

Supplies the **mechanism for why intraday-only is structurally the right side of this trade**:

> Margin requirements are higher overnight, and stock-lending fees are charged only on positions held
> overnight. These institutional constraints, plus overnight gap risk, incentivise arbitrageurs to
> **reduce positions before the close**.

Consequently a mispricing factor earns positive returns through the day and **performs poorly at the end of
the day**, as arbitrageurs unwind. He also documents that profitability and idiosyncratic-volatility
anomalies **accrue gradually through the trading day and take large negative returns overnight** — the same
BETA/IVOL structure as Lou–Polk–Skouras Table 2, from independent data.

**The pattern strengthens in the second half of the sample.** This is the only positive time-trend evidence
found anywhere in this review, and it applies to the day/night cross-sectional family — i.e. to our two
recommended candidates, not to the intraday-momentum family.

**Caveat for us:** Baltussen–Da–Soebhag test this unwinding channel directly (bivariate sorts on the
Stambaugh–Yuan mispricing score) and find it does **not fully** explain end-of-day pricing — the reversal
is present in all mispricing quintiles, including unmispriced stocks. So arbitrageur unwinding is *a*
driver, not *the* driver.

### 4.4 Berkman, Koch, Tuttle & Zhang (2012), "Paying attention", *JFQA* 47(4), 715–741

<https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1625495>

13 years of US intraday data. **Positive overnight returns followed by intraday reversal**, driven by an
opening price that is **high relative to intraday prices**. Concentrated in stocks that have recently
attracted **retail attention**, which show high **net retail buying at the open**. Stronger for
hard-to-value, costly-to-arbitrage stocks and during high retail sentiment. The implicit cost to retail
buyers at the open frequently **exceeds the effective half spread**.

**Do not trade this directly, and here is the trap.** The reversal exists because the opening *print* is
inflated by buy-side imbalance. **You cannot short at the inflated print** — you sell at the bid. A
backtest that shorts at the open print and covers at the close will book the entire artifact as profit.
This is the same wedge as §1, and it is why the "contemporaneous overnight gap → intraday reversal" idea
must be tested against 09:45 prices, not 09:30 prices, before it is believed.

**One clarification worth flagging internally.** Our falsified gap candidate was described as quintiles on
the **lagged** gap z-score. Berkman et al. is about the **contemporaneous** gap — today's open vs
yesterday's close predicting *today's* 09:30→16:00 return. That is a different regression, and it is not
look-ahead (the gap is fully observed at 09:30). If we only tested the lagged version, the contemporaneous
version is technically still open — **but** §1 and the Mesfin gap-fill results (t = −0.32 to −0.59 at three
entry times) both argue it will not survive an honest entry price. Low priority; test it only as a
by-product of the §1 diagnostic.

---

## 5. Opening auction and order imbalance

**Does published imbalance predict intraday direction?** Yes, robustly, at short horizons.

- **Chordia & Subrahmanyam (2004), "Order imbalance and individual stock returns", *JFE* 72(3)**.
  <https://www.sciencedirect.com/science/article/abs/pii/S0304405X03001752> — positive contemporaneous
  imbalance/return relation; **predictable intraday reversal** following imbalance shocks; price impact of
  order flow is **elevated in the opening interval**.
- Decomposing order flow raises adjusted R² materially for **intraday open-to-close** stock returns
  (Cont et al. line of work; arXiv:2209.10334, arXiv:2508.06788).
- Closing-auction imbalance has been used to predict US stock returns (Imperial College MSc thesis,
  Morand — <https://www.imperial.ac.uk/media/imperial-college/faculty-of-natural-sciences/department-of-mathematics/math-finance/MORAND_CLEA_01805978.pdf>); note this is a student dissertation, not peer-reviewed.
- Boyarchenko–Larsen–Whelan's entire overnight-drift mechanism runs through **end-of-day order imbalance**,
  and its **disappearance is attributed to imbalance dispersion collapsing from 6.5% to 2.9%** (§1).

**Data availability — the disqualifier.** Auction imbalance is distributed as a paid, real-time exchange
feed:
- **Nasdaq Net Order Imbalance Indicator (NOII)** — disseminated from 09:28 (open) and 15:50 (close),
  Nasdaq proprietary feed, licensed.
- **NYSE Order Imbalance Information** — from 09:00 (open) and 15:50 (close), NYSE proprietary, licensed.
- **Cboe / IEX auction feeds** — similar.

There is **no free historical archive** of US opening-auction imbalance. Historical NOII is available only
through vendors (Nasdaq Data Link / historical TotalView-ITCH reconstruction), at institutional pricing,
and reconstructing it requires full ITCH message data.

**Verdict: real effect, wrong data regime.** Flagging as requested: this needs data we do not have and
cannot cheaply obtain. It is also intrinsically a *minutes-horizon* signal, which collides with the
no-scalping constraint. **Not pursuable.**

*Partial substitute we DO have:* the first 15-minute bar's **volume relative to its trailing median** is a
crude, freely computable proxy for opening imbalance intensity. It is a magnitude, not a direction, so at
best it is a regime gate — and we have already falsified one volume-regime gate. Treat as low prior.

---

## 6. Intraday reversal / VWAP reversion at hourly horizons

- **Heston, Korajczyk & Sadka (2010), "Intraday patterns in the cross section of stock returns",
  *Journal of Finance* 65(4)**. <https://arxiv.org/pdf/1005.3535> — the canonical result: return
  **continuation at half-hour intervals that are exact multiples of a trading day**, persisting ≥40 trading
  days; and short-horizon **reversal driven by temporary liquidity imbalances lasting less than an hour**
  plus bid-ask bounce.
- Baltussen–Da–Soebhag build directly on this and sharpen it: the intraday reversal is **"mostly present and
  especially strong at the end of the trading day"** (§3), which is why they skip the 15:00–15:30 window.

**Assessment.** Two independent reasons to decline:

1. **The reversal component lives at sub-hour horizons and is substantially bid-ask bounce.** Heston et al.
   say so explicitly ("less than an hour ... and bid-ask bounce"). Bounce-driven reversal is not tradable
   by anyone crossing the spread — it is the spread. At 1.85 bp/side we are the ones paying it.
2. **The tradable part of Heston et al. is the periodicity, not the reversal**, and the periodicity is a
   *continuation* at daily-multiple lags — which for a short book means shorting names that fell in the
   same interval yesterday. This is a real, well-replicated effect, but it is (a) cross-sectional in stocks,
   (b) documented at half-hour granularity, and (c) requires holding a specific 30-minute slot each day,
   i.e. one round trip per slot per day against a very small per-slot edge.

**VWAP reversion specifically:** no peer-reviewed support was found. Every source returned for "VWAP
reversion" is vendor/educational content (CrossTrade, TradingSim, Volatility Box, ChartsWatcher,
TradingView). The academic literature on VWAP is about **execution benchmarking**, not about VWAP as a
predictive signal. **Treat "VWAP reversion" as folklore until someone produces a peer-reviewed
specification.**

**Verdict: not pursuable at 15-minute granularity with 3.70 bp round trips.**

---

## 7. ETF-specific structure: creation/redemption, LETF rebalancing, sector dispersion

### 7.1 Creation/redemption and premium/discount

The AP arbitrage mechanism makes ETF premiums/discounts **small and short-lived** — 0.01–0.05% is normal
for a large liquid ETF, and deviations >1% signal something structural. APs face transaction costs and
execution risk, so small deviations persist precisely because they are **not worth arbitraging** — which
means they are not worth arbitraging by us either, at 3.70 bp. Intraday indicative value (IIV) is
disseminated only every 15 seconds and is itself stale for anything holding non-US or fixed-income assets.

**No peer-reviewed evidence was found of a systematic, sign-predictable intraday ETF pricing pattern
arising from creation/redemption in large liquid US equity ETFs.** The genuine ETF-specific structural
effect is Lachance's (§1), and it is a **measurement artifact plus a liquidity-provision premium**, not a
directional signal. **Nothing to pursue here.**

### 7.2 Leveraged ETF rebalancing — the one ETF-structural mechanism with real evidence

LETFs must rebalance daily to maintain constant leverage, mechanically buying on up days and selling on
down days, into the close. Magnitudes from Baltussen et al. (2021): as of end-February 2009, LETF
rebalancing was **16.8% of market-on-close volume on a 1% market move and 50.2% on a 5% move**, and because
MOC orders carry fill risk, the hedging can start as early as 30 minutes before the close.

Baltussen–Da–Soebhag's Table 8 confirms LETF demand as a driver at the stock level with coefficients of
**131.09, 131.79, 117.22 (all significant at 1%)**, and note **LETF demand contributes more than the
option-gamma measures.**

**Why this is worth noting even though it is not candidate #1:** the LETF rebalancing demand is
**computable without any paid feed**. Their construction (Appendix): using historical **daily NAV** of
leveraged ETFs on the S&P 500, Nasdaq 100, Russell 2000 and S&P 400 Midcap,

```
RD(index j, day t)  =  Σ over LETFs c on j  of   NAV(c,t) × x(c) × (x(c) − 1) × r(j,t)
```

where `x` is the leverage factor (−2, −1, 2, 3). NAV and AUM for ProShares/Direxion products are
published daily and freely available. **This is the only piece of the gamma-hedging mechanism we can
actually reconstruct.**

**Why it is not a candidate anyway:**
- It predicts a **last-30-minutes** price move in the direction of the day's move — a 30-minute holding
  period costing 3.70 bp against an edge that Baltussen et al. price at ~2.7 bp/trade at the *market* level.
- The direction depends on the sign of the day's return, so on down days it says **short**, on up days
  **long** — meaning as a short-only signal it fires only on down days, and its edge is the same magnitude
  as intraday momentum, which already failed.
- Total concurrency: it is one market-wide number per day.
- LETF AUM in 2018–2026 is far larger than the 2009 figures quoted, which cuts both ways — more flow, but
  also far more anticipatory front-running of it.

**Verdict: keep as a possible *conditioning variable* for candidate #1, not as a standalone signal.**
Specifically, `|RD|` is a free, look-ahead-clean proxy for "days when mechanical end-of-day flow is large",
which correlates with the negative-NGE days where Baltussen et al. find the effect concentrated.

### 7.3 Sector ETFs relative to the broad market — dispersion and lead-lag

- **Lead-lag: no.** CXO Advisory's test finds **little evidence that any US equity sector ETF reliably leads
  or lags the market over 23 years** (only utilities show a weak monthly lag).
  <https://www.cxoadvisory.com/economic-indicators/do-any-sector-etfs-reliably-lead-or-lag-the-market/>
  The physics literature agrees on the horizon: lead-lag is **strongest at 1-minute granularity, extends to
  1–4 minute lags, and by 15-minute granularity only the strongest relationships remain significant**
  (arXiv:1010.4917, arXiv:1402.3820). **Our sampling frequency is at or past the point where this
  evaporates.** Do not pursue.
- **Dispersion: an intraday seasonality, not a signal.** Cross-sectional dispersion measured on 15-minute
  scales shows **marked intraday seasonality — much larger at the open, decaying through the session**.
  That is a variance pattern with no directional content.
- **What IS there for sector ETFs** is §4.2: HLR's day/night SML holds for **10 Fama-French industry
  portfolios**, with beta explaining **60% of the cross-sectional variation in day returns**. The sector-ETF
  angle is the *beta ordering across sectors*, not lead-lag or dispersion. That is candidate #1.
- Corroborating (weak source, arXiv:2607.03669 split-session GARCH): **energy stocks show positive overnight
  and negative intraday intercepts; technology shows uniformly positive intraday intercepts** — i.e. the
  night/day split differs systematically by sector. Suggestive only; single non-peer-reviewed source.

---

## 8. Volatility-conditional intraday effects, and the ML upper bound

### 8.1 Does the intraday leg turn reliably negative in high-VIX regimes?

**No clean published result says this directly.** What the literature actually supports is weaker and
different: **predictability of the intraday leg rises with volatility**, not that its *level* turns
negative.

Evidence for the predictability-rises claim, with breadth:

| Source | Conditioning | Effect | Breadth |
|---|---|---|---|
| Gao et al. (2018) | first-half-hour realised vol tercile | R² 0.6% → **3.3%** (>5×) | top tercile = **33% of sessions** |
| Baltussen et al. (2021) | sign of net gamma exposure | significant on negative-NGE days, **insignificant on positive** | negative-NGE = **2,930 / 6,088 ≈ 48% of days** |
| Aleti, Bollerslev & Siggaard | economic uncertainty | "most of the superior performance traced to periods of **high economic uncertainty**" | not quantified as a fraction |
| Limkriangkrai et al. (2023) | COVID crisis | **effect is WEAKER during COVID** in APAC | — |

**Note the last row carefully.** It is the direct counter-evidence to a "crises are where the edge is"
story, and it comes from the one paper that explicitly tested a crisis subperiod on ETFs. Combined with
our own kill of the gap-tail candidate on COVID concentration, the honest position is: **high-volatility
regimes plausibly raise predictability, but the specific 2020 crash is not evidence for anything and
should be excluded from any regime test as a matter of course.**

Breadth is the attractive part here. A top-tercile volatility gate keeps **33% of sessions**, which cuts
annual cost from 8.90%/yr to ~2.94%/yr while (per Gao et al.) multiplying the per-session R² by ~5. That is
the right shape: `exposure × edge` improves because edge grows faster than exposure shrinks.

**Look-ahead warning.** First-half-hour realised volatility is observable at 10:00 and predicts a
15:30–16:00 return — clean for Gao et al.'s use. But if we want to gate a **full-session** open-to-close
short, first-half-hour vol is **not** available at 09:30. Use **previous-day realised volatility** or
**trailing VIX level/change**, both strictly lagged. This is a real constraint that will cost some of the
conditioning power.

### 8.2 The machine-learning upper bound — and why it disqualifies itself

**Aleti, Bollerslev & Siggaard, "Intraday Market Return Predictability Culled from the Factor Zoo"**,
*Management Science* (MS-FIN-2023-01657.R1).
<https://public.econ.duke.edu/~boller/Papers/HFML.pdf>

This is the strongest published intraday result at **exactly our sampling frequency**, so it deserves a
careful read as a benchmark.

- **Setup:** 15-minute returns on **218 characteristic-sorted factor portfolios** (169,965 intraday
  observations per factor), 1996–2020; separates continuous from jump components; ML regularisation
  (Ridge/Lasso/ENet/PCR/PLS/FNN/RF/GBRT/Ensemble); predicts the next 15-minute market return.
- **Result:** trading SPY on the Ensemble forecast, out-of-sample 2004–2020,
  **transaction-cost-adjusted Sharpe 1.37** and **FF6 alpha 20.83%/yr**, against an intraday SPY Sharpe of
  0.09 over the same window. Adjusted annualised return **5.78%**.
- **The short side matters:** adjusted Sharpe rises **0.99 → 1.37** and alpha "more than doubles" moving
  from the long-only `S-Positive` rule to the long-short `S-Sign` rule. They note the return roughly
  doubles too, arguing this is genuine predictability rather than factor-exposure reduction.
- **Cost management is the whole trick:** the winning `S-Sign`/`S-Positive` rules only rebalance when the
  forecast **exceeds the lagged half-spread** — a no-trade band. Naive `Sign`/`Positive` rules that
  rebalance on every sign flip perform materially worse net.
- Performance concentrated in **high economic uncertainty** and traced to **liquidity and tail-risk
  factors** — slow-moving capital.

**Why we cannot pursue it:**
1. **Data.** It needs 15-minute returns on 218 factor portfolios, i.e. a full CRSP/TAQ cross-section
   reconstructed intraday. We have 57 ETF price series. This is not a scaling problem; the signal *is*
   the high-frequency factor cross-section.
2. **Turnover.** Even with the no-trade band, it rebalances within a 26-interval trading day. Their cost
   model is "half the spread on each trade" using TAQ NBBO on SPY — roughly **0.5 bp/side**. Ours is
   **3.7× that**. The adjusted return of 5.78%/yr would not survive the multiplier.
3. It is a **market timer** on SPY — total concurrency.

**What to take from it:** two things. First, it establishes that **there is genuinely exploitable 15-minute
predictability in the aggregate market** — the door really is open, which is worth knowing. Second, its
`S-Sign` no-trade-band construction is the **right cost-control architecture** for any of our candidates:
*do not rebalance unless the signal exceeds the round-trip cost.* That idea is free and transferable even
though the signal is not.

---

## 9. Ranking

Hurdle throughout: **3.70 bp gross per round trip** (1.85 bp/side). "Breadth" = fraction of
sessions × fraction of names on which the signal is active. `gross ≈ exposure × edge`.

| # | Candidate | Gross edge | Breadth | RT/day | Net estimate | Data we lack | Verdict |
|---|---|---|---|---|---|---|---|
| **1** | **Vol-regime-conditioned cross-sectional day/night risk sort** (HLR + LPS BETA/IVOL + Gao vol terciles) | slope −7.7 to −13.5 bp/day per unit β; ×~2–5 in top vol tercile | top-tercile vol ≈ **33% of sessions**; ~12–20 of 57 names | 1 (2 if long-short) | **≈ +4 to +9%/yr**, wide error bars | none — runnable now | **PURSUE** |
| **2** | **Lagged overnight/intraday persistence name selector** (LPS Table 1 / Fig 2) | decile-10 intraday α **−1.96%/mo (t=−9.03)** in stocks; expect ⅓–⅕ of that in ETFs | ~6 of 57 names, **all sessions**; signal persists **5 yrs** | 1 (already paid) | **≈ +2 to +6%/yr**, *zero incremental turnover* | none — daily OHLC from 2013 | **PURSUE** |
| 3 | Gamma/LETF-rebalancing gate as a *conditioner* on #1 | effect concentrated on negative-NGE days | ~48% of days | — | improves #1 if it works | NGE needs OptionMetrics; **LETF `RD` is free** | Optional add-on |
| 4 | Market intraday momentum (Gao; Baltussen) | **2.65 / 2.72 bp per RT** | all sessions, 1 bet | 1 | **−1.4%/yr** | none | **Reject — fails hurdle** |
| 5 | Contemporaneous open-gap → intraday reversal (Berkman) | large in stocks | — | 1 | untestable honestly at 09:30 print | needs quote data to price entry | Test only inside §1 diagnostic |
| 6 | End-of-day cross-sectional reversal (Baltussen–Da–Soebhag) | 3.78 bp/day L−S needing 7.40 bp | 100% sessions, all names | 2 | **−3.6 bp/day** | TAQ; and it is a *stock* effect | **Reject** |
| 7 | Aleti–Bollerslev factor-zoo ML | Sharpe 1.37 net @ 0.5 bp | all sessions | many | negative at 1.85 bp/side | **218 HF factor portfolios** | **Reject — data** |
| 8 | Opening/closing auction imbalance | real, short-horizon | — | many | — | **NOII / NYSE imbalance feed (paid)** | **Reject — data** |
| 9 | Intraday reversal / VWAP reversion | sub-hour, largely bid-ask bounce | — | many | negative | — | **Reject** |
| 10 | Sector ETF lead-lag | evaporates by 15-min granularity | — | — | — | — | **Reject** |
| 11 | ETF creation/redemption premium/discount | 0.01–0.05% and short-lived | — | — | below costs by construction | intraday NAV | **Reject** |
| 12 | Practitioner breakout variants (Zarattini et al.) | 19.6%/yr claimed | — | **many** | excluded by our own scalping arithmetic | — | **Reject** |

---

## 10. The two to pursue

### Candidate 1 — Volatility-conditioned cross-sectional day/night risk sort

**The trade.** Rank the 57 ETFs on a strictly-lagged risk measure (trailing 12-month beta to SPY, or
trailing realised volatility, or both). On sessions where a **lagged** volatility-regime gate is on, short
the top risk quantile intraday and (if long exposure is permitted) hold the bottom quantile. Flat at every
close.

**Why this and not intraday momentum.** Three independent literatures converge on the same object from
different data:
- HLR (JFE 2020): day-time SML slope **−7.7 bp/day** per unit beta, t = −5.52, holding for **industry
  portfolios** as well as beta-sorted portfolios; **the highest-beta decile has the lowest day return
  (−8 bp) and the highest night return (+20 bp).**
- Lou–Polk–Skouras (JFE 2019): shorting high-beta intraday earns **+0.70%/mo**; shorting high-IVOL
  intraday earns **+2.48%/mo (t = 6.21)**; both **lose** overnight.
- Bogousslavsky (JFE 2021): the mechanism — overnight margin and lending fees push arbitrageurs to unwind
  before the close — and, uniquely in this review, the pattern **strengthens in the second half of his
  sample**.

**Effect size and breadth.** Unconditional: −7.7 bp/day per unit beta (value-weighted; −13.5 equal-weighted).
Break-even beta spread at our costs is **Δβ = 0.96** for a long-short — achievable in our universe but with
no margin. The volatility gate is what creates the margin: Gao et al. find R² rises **0.6% → 3.3%** from
the low to the high first-half-hour-volatility tercile. Gating to the top tercile keeps **33% of sessions**,
cutting annual cost to ~2.94%/yr. Names: top/bottom quintile of 57 = **~12 per side**.

**Data needed:** none we lack. Betas and realised vols from daily data 2013+; the intraday leg from the
15-minute panel 2018+.

**Look-ahead:** must use a **strictly lagged** gate. First-half-hour realised volatility is *not* available
at 09:30 for a full-session position — use previous-day realised vol or trailing VIX. Adopt Aleti et al.'s
`S-Sign` architecture: **do not change position unless the expected edge exceeds 3.70 bp.**

**Concurrency — flag it honestly.** The volatility gate is a **market-wide state variable**. When it fires,
it fires on every name at once. This is a market-timing overlay on a cross-sectional trade. The mitigation
is that the underlying trade is beta-*spread*, not beta-*level*, so the concurrent exposure is to
dispersion rather than direction — but if the long leg is not funded, a short-only version is a directional
market-timing bet and must be sized as one bet, not twelve.

**Biggest reason it fails:** *there is not enough beta dispersion in 57 liquid ETFs.* The published slopes
come from decile portfolios spanning the full CRSP beta distribution (β ≈ 0.4 to ≈ 2.0). Our achievable
spread is roughly β ≈ 0.0–0.4 (TLT/GLD/XLU/XLP) to β ≈ 1.3–1.5 (semis/tech/small-cap growth). At the
value-weighted slope that is a **+0.3 bp/day** long-short after costs — inside the noise. The entire case
rests on the volatility conditioning multiplying the slope, and **no paper measures the day-SML slope
conditional on volatility regime.** We would be extrapolating Gao et al.'s R² pattern (a *market-timing*
result) onto HLR's slope (a *cross-sectional* result). **That extrapolation is the single load-bearing
assumption and it is not directly supported by any source in this review.** Pre-register it as such.

**Secondary failure mode:** HLR's sample ends **2016** and no post-publication test exists. Given that the
adjacent overnight-drift literature has visibly decayed post-2021 (§1), a 2018–2026 test is genuinely
out-of-sample and could simply come back flat.

### Candidate 2 — Lagged overnight/intraday persistence as a name selector

**The trade.** At each month-end (or quarter-end), rank the 57 ETFs on their **trailing overnight return**
(EWMA, long half-life — Lou–Polk–Skouras use 60 months internationally). Names in the top quantile go into
the intraday-only short book; names in the bottom quantile are excluded or eligible for the long side.
This does **not** change *when* we trade — only *what* we hold.

**Effect size.** Lou–Polk–Skouras Table 1 Panel A: decile 10 by lagged one-month overnight return earns a
three-factor **intraday alpha of −1.96%/mo, t = −9.03 (≈ −23.5%/yr)**; decile 1 earns **+1.06%/mo**
intraday; the 10−1 spread is **−3.02%/mo, t = −9.74**. Sorting instead on lagged intraday returns gives a
**+2.41%/mo (t = 7.70)** intraday spread and a **−1.77%/mo (t = −7.89)** overnight spread — the tug of war
is identifiable from either component.

**Breadth and persistence.** Decile = **10% of names** (≈ 6 of 57), but active on **100% of sessions**.
Crucially, **Fig. 2 shows the persistence test significant up to five years of lag**, and the international
EWMA version (60-month half-life) forecasts with **t = 5.10 / 4.60**. The signal is slow enough that
rebalancing annually is defensible.

**Round trips per day: one — and it is already paid.** This is the decisive advantage. An intraday-only
book pays 3.70 bp/session regardless of which names it holds. Candidate 2 adds **zero incremental
turnover**; it only reallocates a cost we are already incurring toward names with a better conditional
intraday return. `exposure × edge` is therefore evaluated against a **zero** marginal hurdle, not 3.70 bp.
Of everything in this review it is the only candidate with that property.

**Data needed:** none we lack. Daily OHLC from **2013** gives close-to-open and open-to-close series, which
means ~5 years of signal formation before the 15-minute panel begins in 2018 — no burn-in cost inside the
test window.

**Look-ahead:** the cleanest in this document. The conditioning variable is a realised return measured
months to years before the return it predicts.

**Biggest reason it fails — and it is a real one:** *it is probably the same trade as candidate 1.*
Sorting a 57-ETF panel on trailing overnight return will select the high-beta, high-volatility, retail-heavy
names — the same names candidate 1 selects on beta. In individual stocks the two sorts separate because
retail attention and beta are only loosely related; across 57 liquid ETFs they may be near-identical. If
so we have one candidate, not two, and the apparent corroboration between two literatures is illusory.
**Test explicitly: compute the rank correlation between the lagged-overnight sort and the lagged-beta sort
across the 57 names. If it exceeds ~0.7, treat them as one hypothesis and spend only one multiple-testing
budget on them.**

**Secondary failure modes:**
- **Dispersion again.** −1.96%/mo is a stock-decile number. Expect one-third to one-fifth in ETFs, i.e.
  −0.4% to −0.65%/mo (≈ 5–8%/yr). Against 8.90%/yr of cost that is not obviously positive as a *standalone*
  short book — it is positive only as a *selector* within a book already paying that cost.
- **Concurrency.** ~6 names, all high-beta, will fall together. Six names is not six bets. Size accordingly.
- **Post-publication decay.** Sample ends **2013**; Elm Wealth's related long-short deteriorates markedly
  post-2012, and §1's decay evidence applies to the overnight leg that generates this sort.

---

## 11. Suggested order of work

1. **§1 diagnostic first.** Re-measure the overnight/intraday split using the 09:45 bar close and the
   first-half-hour VWAP as "open", and skipping the last 15-minute bar at the close. Split 2018–2020 vs
   2021–2026. If the +8.59%/yr overnight leg collapses, everything downstream is re-scoped.
2. **Rank-correlation test** between the lagged-beta sort and the lagged-overnight sort across the 57 names.
   Decides whether candidates 1 and 2 are one hypothesis or two, *before* either is tested.
3. **Candidate 2** next, because it is the cheaper test: it needs no regime gate, no volatility
   conditioning, and no new parameters — a single lagged sort with a pre-registered quantile.
4. **Candidate 1** last, and pre-register the load-bearing extrapolation (that Gao et al.'s
   volatility-conditioned R² gain transfers to HLR's cross-sectional slope) as the explicit thing being
   tested.

---

## Sources

**Peer-reviewed**
- Gao, Han, Li & Zhou (2018), "Market intraday momentum", *JFE* 129(2), 394–414 — <https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351> · SSRN <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866>
- Baltussen, Da, Lammers & Martens (2021), "Hedging demand and market intraday momentum", *JFE* 142, 377–403 — <https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598> · <https://academicweb.nd.edu/~zda/intramom.pdf>
- Lou, Polk & Skouras (2019), "A tug of war: Overnight versus intraday expected returns", *JFE* 134, 192–213 — <https://www.sciencedirect.com/science/article/abs/pii/S0304405X19300650> · <https://personal.lse.ac.uk/polk/research/TugOfWar.pdf>
- Hendershott, Livdan & Rösch (2020), "Asset pricing: A tale of night and day", *JFE* 138(3), 635–662 — <https://www.sciencedirect.com/science/article/abs/pii/S0304405X20301732> · <http://faculty.haas.berkeley.edu/hender/CAPMday-night.pdf>
- Bogousslavsky (2021), "The cross-section of intraday and overnight returns", *JFE* 141(1), 172–194 — <https://www.sciencedirect.com/science/article/abs/pii/S0304405X21000854> · SSRN <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2869624>
- Berkman, Koch, Tuttle & Zhang (2012), "Paying attention: Overnight returns and the hidden cost of buying at the open", *JFQA* 47(4), 715–741 — <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1625495>
- Lachance (2021), "ETFs' high overnight returns: The early liquidity provider gets the worm", *Journal of Financial Markets* — <https://www.sciencedirect.com/science/article/abs/pii/S138641812030032X>
- Lachance (2022), "ETFs' two-sided trading costs and order imbalances", *Financial Review* — <https://onlinelibrary.wiley.com/doi/10.1111/fire.12292>
- Lachance (2023), "Night trading: Lower risk but higher returns?", *Review of Financial Economics* — <https://onlinelibrary.wiley.com/doi/full/10.1002/rfe.1180>
- Limkriangkrai, Chai & Zheng (2023), "Market intraday momentum: APAC evidence", *Pacific-Basin Finance Journal* 80, 102086 (open access) — <https://researchmgt.monash.edu/ws/files/519509174/494419119_oa.pdf>
- "Intraday time series momentum: Global evidence and links to market characteristics", *JIFMIM* (2021) — <https://www.sciencedirect.com/science/article/abs/pii/S138641812100001X>
- Heston, Korajczyk & Sadka (2010), "Intraday patterns in the cross section of stock returns", *Journal of Finance* 65(4) — <https://arxiv.org/pdf/1005.3535>
- Chordia & Subrahmanyam (2004), "Order imbalance and individual stock returns: Theory and evidence", *JFE* 72(3) — <https://www.sciencedirect.com/science/article/abs/pii/S0304405X03001752>
- Aleti, Bollerslev & Siggaard, "Intraday Market Return Predictability Culled from the Factor Zoo", *Management Science* (forthcoming) — <https://public.econ.duke.edu/~boller/Papers/HFML.pdf>

**Working papers / official**
- Baltussen, Da & Soebhag (2025), "End-of-Day Reversal", SSRN 5039009 — <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5039009> · <https://academicweb.nd.edu/~zda/EOD.pdf> · Quantpedia Awards 2025 coverage <https://www.eur.nl/en/news/end-day-reversal-pattern-second-place-quantpedia-awards-2025>
- Boyarchenko, Larsen & Whelan (2026), "The Disappearing Overnight Drift", NY Fed Liberty Street Economics — <https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/> · SSRN <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7035838>
- Boyarchenko, Larsen & Whelan, "The Overnight Drift", NY Fed Staff Report 917 — <https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf>
- Wu (2023), "High Frequency Trading and Intraday Momentum", EFMA — <https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2023-UK/papers/EFMA%202023_stage-4455_question-Full%20Paper_id-31.pdf>
- Chen & Welch (2026), "What Useful Alphas?", Federal Reserve Board / UCLA
- Chen & Zimmermann, "Publication Bias in Asset Pricing Research" — <https://arxiv.org/pdf/2209.13623>
- Mesfin (2026), "Structural Limits of OHLCV-Based Intraday Signals in MNQ Futures: A Systematic Falsification Study", arXiv:2605.04004 — <https://arxiv.org/abs/2605.04004> *(single author, not peer-reviewed)*

**Practitioner (treat with caution)**
- Elm Wealth, "Night Moves: Is the Overnight Drift the Grandmother of All Market Anomalies?" — <https://elmwealth.com/night-moves-overnight-drift/>
- Zarattini, Aziz & Barbon (2024), "Beat the Market: An Effective Intraday Momentum Strategy for SPY", SSRN 4824172 — <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172>
- CXO Advisory, "Do Any Sector ETFs Reliably Lead or Lag the Market?" — <https://www.cxoadvisory.com/economic-indicators/do-any-sector-etfs-reliably-lead-or-lag-the-market/>
