# Opening prize-sizing: the three source reports (2026-09-28)

Three research agents sourced flow sizes for the opening prize-sizing table (D661), one lane each. Their reports are
reproduced below as written, apart from light formatting. They are model output from web research, so every figure
carries the source tag the agent gave it. D661 uses them as ranges, not as point facts.

**Keys used by `scripts/diag_opening_prize_table.py`:** C1 = options and dealer hedging; C2 = systematic and
rebalancing flows; C3 = auctions, market size, the impact law and microstructure.

**Seal disclosure.** C3 measured some descriptive statistics from fixtures that run past 2025-03-01, the vault's
start. These were 2025 ES and NQ volume and volatility, micro-contract shares over 2025-09 → 2026-09, and 10:00-release
move sizes over 2016–25. My prompts did not state the seal. D661 uses none of those figures: its market inputs come
from `data/opening/prize_bar.json`, in-sample to 2025-02-28. See D661 §5.

---

## C1 — Options and dealer hedging

**How I sourced this.** Each figure is marked [ACAD] for peer-reviewed work, [WP] for academic working papers, [EXCH]
for exchange data or exchange research, [BANK] for bank notes, [VEND] for vendors or blogs, and [JOUR] for
journalism. I read the full text of Amaya et al., Dim/Eraker/Vilkov, Baltussen et al., Barbon/Buraschi,
Golez/Jackwerth, Beckmeyer et al., the SqueezeMetrics white paper and the Cboe fee schedule. I did this by fetching the
public PDFs into the scratchpad. I also fetched SqueezeMetrics' free public `DIX.csv`, a daily GEX series from 2011 to
2026-09-25, and computed its distribution. Nothing was signed up for, logged into or purchased. SSRN returned 403, so
the Adams et al. papers and Brogaard/Han/Won are taken from abstracts and summaries only. That is flagged where it
matters.

### 1. Aggregate dealer gamma (SPX complex), in $ per 1% move

**Unit caveat first.** "GEX" is conventionally quoted as "$ of underlying traded per 1% move". The SqueezeMetrics
white paper (March 2016, revised December 2017) gives Γ·OI·±100 and only says "we denominate GEX in dollars". The unit
is never stated precisely. The sign convention is naive: dealers are assumed long every call and short every put.

- **SqueezeMetrics public series, 2016-01 to 2026-09 (2,698 days) [VEND, my computation]:**
  - Distribution: median **+$3.2B**, mean +$3.6B, p5 −$0.8B, p1 −$2.2B, p95 +$8.9B, p99 +$14.8B. Negative on 10% of
    days.
  - Extremes: min **−$7.5B** (2022-01-20), −$7.2B (2026-03-27), max **+$24.2B** (2021-04-12).
  - By year: 2022 was the outlier, with median +$0.5B and 41% of days negative. Other years had medians of $1.9–6.0B.
  - Recent stress days: 2020-03-12 at −$2.2B; 2025-04-04 to 04-08 at about −$1.9B; 2024-08-05 at +$0.5B.
- **Amaya, Garcia-Ares, Pearson & Vasquez, "0DTE Index Options and Market Volatility: How Large is Their Impact?"**
  (January 2025, hosted by Cboe) [WP]. This is the only reconstruction that signs positions from actual
  trade-capacity data (all SPX/SPXW trades, one-minute gamma, July 2020 to June 2023).
  - Mean of daily means is 341.2 "billions". My reading is dollar gamma Γ·S², which gives **about +$3.4B per 1%**.
    This is my inference about the units, not the paper's statement.
  - It matches SqueezeMetrics over the same window: $3.8B mean. By period it is $4.1B vs $5.45B before May 2022 and
    $2.3B vs $1.25B after.
  - Gamma was negative at some point on at least 25% of days, and on at least half of days after May 2022.
  - Intraday extremes: min about **−$54B**, max about **+$167B** per 1%. These are near-expiry spikes.
- **Goldman Sachs note (10 June 2020, reposted by SpotGamma) [BANK via VEND]:** SPX *gross* gamma was **$80B per 1%**.
  Soon-to-expire gross gamma was "$20–50bln on a typical day". Gross is an upper bound, not the net dealer figure.
- **SpotGamma (12 September 2026) [VEND]:** "dealers holding 8 to 10 billion of negative gamma" before OPEX. No unit
  is stated.
- **Reliability:** vendor figures depend on a sign assumption. The only trade-signed academic series (Amaya) agrees
  with SqueezeMetrics on level to within 2×, so a typical net of **+$2–6B per 1%** is reasonably corroborated. The
  single-day extremes (−$7.5B, +$24B) are SqueezeMetrics-only.

### 2. 0DTE options

**Share and size**
- **Share of SPX volume [EXCH, Cboe]:** 5% in 2016, about 50% in August 2023, and **59% in full-year 2025** (2.3M
  contracts a day). Q4 2025 was 2.6M a day.
- **Notional per day:**
  - Cboe (Xu, 8 September 2023): 1.23M contracts, about **$500B notional a day** [EXCH].
  - JPMorgan/Kolanovic (Reuters, 15 February 2023): about $1T a day [BANK via JOUR].
  - Dim/Eraker/Vilkov Table 1 (SPY+SPXW, after April 2022): mean **$542B notional a day**, and **$129B delta-dollar
    volume** a day [WP].

**Net dealer 0DTE gamma: the estimates disagree by more than 2×**
- **Cboe (Xu 2023) [EXCH]:**
  - Market-maker 0DTE net gamma at 3:30 pm has a median of **+$173M per 1%**, an interquartile range of
    **−$1.1B to +$2.4B**, and extremes of **−$5B to +$7.7B**.
  - Against S&P futures at about $400B a day, the average day is 0.04–0.17% and the extremes 1.3–1.9%.
  - In May 2025 Cboe called it "de minimis", at best 0.2% of daily SPX liquidity.
- **JPMorgan (Kolanovic, February 2023) [BANK via JOUR]:** a "large move" could spark about **$30B** of buying or
  selling. That is 4–6× Cboe's extreme, and the size of the move is unspecified.
- **Beckmeyer, Branger & Gayda (working paper, December 2023) [WP]:**
  - Market makers' 0DTE order imbalance is consistently negative, between −0.5% and −1% of their volume, and below −1%
    after May 2022. That implies a small *short* 0DTE gamma.
  - Market makers are net *long* in longer-dated options after May 2022.
- **Adams, Fontaine & Ornthanalai (SSRN 4881008, May 2024) and Adams, Dim, Eraker, Fontaine, Ornthanalai & Vilkov
  (SSRN 5641974, October 2025) [WP, from abstracts and a Quantpedia summary]:**
  - Market-maker net gamma is **positive** on 0DTE days.
  - This comes from positions accumulated earlier that *become* 0DTE: "24 bps" of hedging needs from those, against
    "3 bps" from new same-day positions. I could not open the paper to confirm the units of those two figures.

**Amplify or dampen?**
- **Dampen:**
  - Adams et al.: realized volatility is lower by about **60–61 bp annualized** (about 7% of baseline) on days with
    0DTE. The effect runs over the next 10 minutes and fades after about 1 hour, with stronger reversals in E-mini
    order flow.
  - Dim/Eraker/Vilkov (May 2024 version): 0DTE open-interest gamma does not propagate volatility. The difference in the
    volatility response between early and late samples is 0.15 SD, "economically negligible".
  - Amaya et al.: the median effect cuts daily volatility by 0.08 vol points. The **maximum** effect *raises*
    annualized daily volatility by **3.3 points**, and by **6.4 points** on 30-minute windows, when gamma is negative.
- **Amplify:**
  - Brogaard, Han & Won (SSRN 4426358, 2023) [WP, abstract only]: +1 SD in 0DTE trading gives **+9.1% of mean
    volatility**, identified from the staggered weekly-expiry rollout and attributed to retail speculation.
  - This is the outlier against three studies that use signed positions.

**Gross, unsigned 0DTE gamma (an upper bound)**
- Dim/Eraker/Vilkov, SPY+SPXW open-interest dollar gamma at 10:00: mean $1,376B per 100%, which is **about $13.8B per
  1%**. The maximum is about $72B per 1%.

**Timing**
- 0DTE gamma scales as 1/√T. For an ATM option, gamma with one hour left is about 25× the one-month gamma (DEV).
- After the open (about 6.5 h left), an ATM 0DTE has about 2.5× *less* gamma than the same option at 15:00. The 0DTE
  mechanism is structurally weakest in the first hour and strongest from 15:00 to 16:00.
- Amaya's 9:30 gamma includes overnight trades.

### 3. Measured price impact of hedging

- **Baltussen, Da, Lammers & Martens, "Hedging demand and market intraday momentum", JFE 142 (2021) 377–403 [ACAD]:**
  - Last-half-hour return on rest-of-day return, S&P 500 futures, 1996–2020, NGE-conditioned (Table 7).
  - On **negative-NGE days** the slope is **0.0663** (t 4.78, R² 3.6%). On positive-NGE days it is 0.0082 (t 1.03, not
    significant). A 1% rest-of-day move predicts about **+6.6 bp in the last 30 minutes** under negative gamma, and
    roughly zero otherwise.
  - Table 8 adds interaction terms (NGE×r_ROD −123, t −3.42). The effect reverts over the following days.
  - NGE used OptionMetrics to 2017 and SqueezeMetrics after (naive signs); negative on 2,930 of 6,088 days.
  - The paper gives no single "share attributable to gamma" figure. The evidence is conditional: momentum exists only
    when NGE < 0.
  - **Timing: last 30 minutes, not the open.**
- **Barbon & Buraschi, "Gamma Fragility" (SIBF working paper 2020/05, November 2020) [WP]:**
  - For the index-option panel (S&P 500, Dow, NDX, Russell), +1 SD of gamma imbalance goes with **more than 20 bp lower
    daily absolute index return**, about 20% of an SD.
  - Negative imbalance times illiquidity gives intraday momentum; positive gives reversal.
  - Their Figure 5 example, 2018-11-15: SPX gamma flipped sign 2.3% above spot.
- **Ni, Pearson, Poteshman & White, RFS 34(4) 2021 [ACAD]:** single stocks only. As reported in the abstract, **12% of
  daily absolute returns** of optioned stocks come from market-maker rebalancing. I could not open the RFS text itself.
- **Pinning:** Golez & Jackwerth, "Pinning in the S&P 500 futures", JFE 106 (2012) [ACAD].
  - On serial ES-option expiry days, 1992–2009, futures are pulled toward the ATM strike: a shift of **at least 11 bp**
    from Thursday pm to Friday pm, at least $115M of notional.
  - **About half ($59M of $115M) happens in the last 30 minutes.**
  - Before AM-settled SPX expiry there is "anti-cross-pinning" (a push *away* from the strike).
  - This is pre-0DTE evidence.
- **In-house (D581, `docs/FINDINGS.md` §77):** the ES-options carried-gamma regime did **not** condition
  last-half-hour continuation (interaction −0.023, t −0.66, rank 0.32). Carried OI sees at most 8.5% of same-day gamma.

### 4. Retail flow (only as it reaches dealers)

- Cboe (May 2025) [EXCH]: retail is **50–60% of SPX 0DTE** volume. Over 95% of it is limited-risk (long options or
  spreads), and customer buys and sells are "extremely balanced".
- Beckmeyer et al. [WP] identify retail more narrowly: **about 6% of 0DTE volume** (2022), with 75% of retail SPX
  trades being 0DTE. Retail lost $350k a day after May 2022.
- **The two retail shares differ by about 10×.** The difference is definitional (broker-routed versus identified
  retail), but there is no reconciliation.
- Amaya et al. Table 1: customer-to-customer trades are a larger share of 0DTE than of longer maturities. Of all
  SPX/SPXW volume, customers bought 17.2% and sold 16.0% as 0DTE. The net is small, so little retail flow reaches the
  dealer hedge.

### 5. Data availability (public pages only)

- **Databento OPRA.PILLAR:**
  - History from **2013-04-01** for trades, OHLCV, **statistics (which carries open interest)**, definitions and
    cbbo-1m, added 2025-05-21.
  - The documented example unit prices are statistics $11/GB, definition $5/GB, trades and ohlcv-1m $280/GB,
    ohlcv-1d $600/GB. They are quoted in `docs/research/futures-data/04-free-api-tiers.md`.
  - OPRA Standard plan $199/month (from 2025-06-03).
  - OI here is total per series, not by participant, so it gives only naive-sign GEX.
- **Cboe DataShop:**
  - "Option EOD Summary" (OHLC, volume, **open interest**, optional Greeks) runs from **January 2012**. Price is not
    shown publicly.
  - **Open-Close Volume Summary** splits volume by customer, professional, broker-dealer and market maker, and by open
    or close. Cboe Options (C1, where SPX trades) runs from **2005-01-03**. This is what signed-position studies need.
  - The Cboe fee schedule (2026-09-15) lists Open-Close products from about $300 to $12,000 a month. It also lists
    academic ad-hoc rates ($1,500 a year plus $125 a month; $3,000 a year plus $250; $12,000 a year plus $1,000) and a
    free July–December 2022 sample. The PDF table extracts scrambled, so I cannot reliably map each price to its
    product.
  - An index-data licence ("CGI", from $1k a month) is needed for SPX bid/ask.
- **Already on disk:** ES-family options OI by strike, 2016-01 to 2026-09-09 (`fut_es_options_eod`). NQ options, 2016
  to 2025-02 (OI 2–5% of ES's). ES 0DTE volume by ET bucket, 2016–2023. One year of ES signed option flow. **SPX,
  SPXW, SPY, QQQ and NDX are not held.**
- **NQ/NDX:** no academic estimate found. Vendor QQQ figures disagree by about 19× (−$0.25B against −$4.68B per 1%),
  so they are unreliable.

### Summary table (C1)

| Mechanism | Flow size ($, range) | Timing in day | Measured impact (bp) | Source quality | Notes |
|---|---|---|---|---|---|
| Aggregate net dealer gamma (all SPX expiries) | Typical +$2–6B per 1%; p5 −$0.8B, p1 −$2.2B; extremes −$7.5B to +$24B (daily). Intraday −$54B to +$167B | All session; carried from the prior close | Negative-gamma days: last-30-min drift +6.6 bp per 1% of prior move (JFE); +1 SD imbalance gives >20 bp lower daily \|return\| (WP) | Vendor series plus one trade-signed WP (units inferred); JFE, WP | Net is usually long gamma (dampening). ES volume about $400B a day, so the typical flow is about 1% of daily volume per 1% move |
| Gross SPX gamma (upper bound) | $80B per 1% (Goldman, 2020); 0DTE gross open-interest gamma about $14B per 1% (max about $72B) | n/a | not found | Bank via vendor; WP | Not a hedging flow unless one side is all dealers |
| 0DTE net dealer hedging | Median +$0.17B per 1% at 15:30; IQR −$1.1B to +$2.4B; extremes −$5B to +$7.7B. JPM: $30B in a "large move" | Grows as 1/√T: weak after the open, strongest 15:00–16:00 | Average: vol **−60 bp annualized** (about −7%). Worst case: **+3.3 vol points** daily, **+6.4** on 30-minute windows | Exchange; WP; bank via journalism | Estimates disagree by >2× (JPM against Cboe). Brogaard/Han/Won find +9% vol (amplify), the outlier |
| Expiry pinning (ES options on futures) | At least $115M to $240M notional shift per expiry | About half in the last 30 minutes | At least 11 bp absolute shift (1992–2009) | JFE | Pre-0DTE; SPX shows anti-pinning before AM settlement |
| Retail options flow | 6% (identified) to 50–60% (Cboe) of 0DTE volume; net small | Intraday | Indirect only | WP against exchange (about 10× apart) | Mostly balanced customer trading, so little reaches the hedge |

**For the square-root sizing:** gamma flow is not exogenous. It equals G × (the move itself), so it amplifies or
damps moves rather than creating one. Only the negative-G tail (below about −$2B per 1%, roughly 1–5% of days) is a
plausible after-the-open "prize". The measured effects cluster at the close, not the open.

---

## C2 — Systematic and rebalancing flows

Source-quality tags: **PR** = peer-reviewed. **WP** = working paper, central bank or regulator. **EX** = exchange or
index-provider data. **BANK** = bank research reported second-hand, via Bloomberg, Reuters, Yahoo or a blog. **VEN** =
vendor or marketing, unsourced. **PROJ** = this repo's own measurement.

Nearly every flow size below comes from sell-side desks (Goldman, JPM, Nomura, MS, BofA) that I could only see through
journalism. Treat those as scenario models, not observations.

### 1. CTAs / trend followers

**AUM**
- BarclayHedge puts managed-futures AUM at **$339.4bn at Q4 2024** (vendor database, all CTAs rather than trend
  followers only).
- For scale, the SG Trend Index needed $4.64bn of AUM to be a member in 2026 (Alternatives Watch, SG indices).

**Equity positioning and flows (Goldman CTA desk, BANK)**
- 2 June 2026: CTAs were **$93bn long global equities, of which $34bn in S&P 500 futures** (about 37%).
- Next-week scenarios in that note: +$5.5bn flat, more than +$7bn up, and "limited" selling down. One-month
  scenarios: +$18bn flat, more than +$37bn in a rally, **more than $100bn of selling** in a sustained decline.
- A separate Goldman note (Investing.com/StreetInsider, 2026) had about $7.5bn of global selling next week, **$4.5bn
  of it in the S&P**, and up to $31.5bn in a down tape. Its one-month tail was **$185bn**, with published S&P trigger
  levels of 7,455, 7,204 and 6,765.
- Aug 2024: Nomura (McElligott, via Bloomberg 5 Aug 2024) said equity CTAs sold **$12.5bn over two weeks**, and could
  sell $36bn more on a further −4%.
- A second-hand Goldman figure for the same episode was about $32bn of global selling in one week. I could not confirm
  it at source.
- A blog claim of "$150bn of CTA selling in three days (Goldman PB)" is **unverified and conflicts with the above by
  more than 4×**. Discard it.

**Anticipated?** Yes, heavily. Goldman, Nomura, BofA and others publish trigger levels and scenario flows at least
weekly, and the press re-circulates them.

**Execution timing: no authoritative source found.**
- Two claims say CTAs trade mostly in the morning. One is "industry lore" repeated by Alpha Architect. The other is an
  arXiv preprint (2607.01550, July 2026, **not peer-reviewed**) finding that "the first 20% of daily volume" behaves
  differently, which it reads as morning CTA execution.
- I found no measured price impact of CTA flows on ES in the peer-reviewed literature.

### 2. Vol-control / vol-targeting and risk parity

**AUM**
- ECB Financial Stability Review (May 2020, box, WP): **"up to USD 2 trillion"** in some form of volatility strategy,
  and **about $300bn in ~100 risk-parity funds**. The ECB itself says the aggregate size is not known precisely.
- Barclays (2018, via Heisenberg Report, BANK): **$350bn** in vol-target funds.

**Rebalancing size**
- Chandumont, "The Volatility Regime", *The Actuary* (SOA, 2016, practitioner model): assumes **$275bn benchmarked to a
  10% vol-target S&P index**. It models selling of **$44.9bn / $56.7bn / $36.5bn on 24, 25 and 26 Aug 2015**, which
  is **9%, 16% and 11% of SPX futures volume**, with a peak of 41% of volume on 14 Oct 2013. These are simulated
  flows, not observed ones.
- Aug 2024: Nomura said vol-control funds sold **$83.6bn of US equity futures over two weeks** (Bloomberg, 5 Aug 2024).
  Bloomberg's headline figure for the possible further selling was $170bn.
- **No clean public "$ per 1% move" figure was found.**

**Timing:** usually at or near the close. Vol-target indices rebalance at the close, often with a one- or two-day lag;
the *Actuary* piece says "the second business day after" the trigger. Some managers rebalance intraday.

**Anticipated?** Yes. Nomura, DB and JPM publish estimates, and the rule (realised-vol windows) can be replicated.

### 3. Leveraged and inverse ETFs

**Mechanics.** The rebalance equals prior-day NAV × (L² − L) × the day's index return (Cheng & Madhavan 2009). Every
leveraged or inverse fund trades in the direction of the day's move. A 3× fund carries a weight of 6 and a −3× fund a
weight of 12.

**Size, index products only.** This is this repo's own sum of L(L−1) × AUM over ten issuer AUM series (D640, PROJ):
- **Nasdaq-100 products: $192bn in 2025**, i.e. **about $1.9bn per 1% NDX move**. That is up elevenfold from $17bn in
  2016.
- **S&P 500 products: $81bn**, i.e. **about $0.8bn per 1% SPX move** (was $38bn).

**Size, all LETFs including single-stock and sector funds (BANK)**
- Morgan Stanley (2024): about **$7bn per 1% move**.
- JPM: **about $15bn sold on 3 Sep 2024** when the NDX fell 3%, about $5bn per 1%.
- A Nomura figure of about $10bn per 1% at the June-2026 peak came only via a secondary blog. Unverified.
- The whole-market figure is 3.5 to 9 times the index-only one. **For ES/NQ use the index-only numbers.** The
  single-stock component lands on single names, not on the index future.

**Timing:** the last 30–60 minutes, largely through market-on-close orders. Shum et al. (2016) argue fill risk pushes
hedging as early as 30 minutes before the close. The BIS saw VIX-product rebalancing bid up from about 15:30.

**Anticipated?** Yes. The size is deterministic from AUM and the day's return, and desks publish it intraday.

**Measured impact**
- **Cheng & Madhavan**, "The Dynamics of Leveraged and Inverse Exchange-Traded Funds", *J. Investment Management* 7
  (2009), PR. Rebalancing was **16.8% of market-on-close volume on a 1% day and 50.2% on a 5% day** (Feb 2009; figure
  as quoted by Baltussen et al.).
- **Tuzun**, "Are Leveraged and Inverse ETFs the New Portfolio Insurers?", Fed FEDS 2013-48, WP.
  - Rebalancing was **$1.04bn per 1% move on $20bn of NAV**, about 0.84% of daily stock volume (Dec 2011).
  - Implied end-of-day price reaction per 1% index move: **6.9 bp for an average large stock** and 13 bp for a
    financial. The model is *linear* in flow share, not square-root.
- **Shum, Hejazi, Haryanto & Rodier**, "Intraday Share Price Volatility and Leveraged ETF Rebalancing", *Review of
  Finance* 20(6) 2016, PR. End-of-day volatility correlates with potential rebalancing as a share of volume over
  2006–11. The effect is "not all economically significant" and is largest on the most volatile days.
- **Ivanov & Lenkey**, "Do leveraged ETFs really amplify late-day returns and volatility?", *J. Financial Markets* 41
  (2018), PR.
  - Investor inflows and outflows to the funds offset much of the mechanical rebalance.
  - The companion paper (FEDS 2014-106) finds rebalancing demand falls **by up to 74% for +3× funds** once those flows
    are counted.
  - Their verdict is that the late-day impact is "economically insignificant".
  - The top two estimates of impact disagree by far more than 2×.
- **Observed episode (BANK/journalism):** on 3 Sep 2024, Nomura noted **ES fell 34 points (about 0.6%) in 17 minutes**
  near the close. That is confounded with everything else trading into the close.
- **PROJ D640:** an NQ close-flow effect of +5.6 bp (14:30 cell) was killed by its own 11:00 placebo (+3.3 bp, t 2.08).
  It **did not grow as the NDX leveraged-ETF exposure grew elevenfold**. This is local evidence that the LETF price
  impact on the index future is small.

### 4. Pension and balanced-fund rebalancing

**Bank quarter-end estimates (BANK via Bloomberg/Yahoo)**
- JPM: **$150bn** of equity selling (June 2023) and **$165bn** (June 2026, of which US defined-benefit plans about
  $55bn, GPIF about $60bn, Norges about $40bn).
- Goldman (Flood): **$26bn** (Sept 2022), **$32bn** (Mar 2024) and **about $30bn** (June 2026, "89th percentile" of
  three years). Month-end buys of $14bn have also been reported.
- **JPM and Goldman differ by about 5×.** JPM counts global balanced funds and sovereign funds; Goldman counts US
  pensions only. For ES, the US-pension figure is the relevant one, and a large share of the global total is not
  traded in ES.

**Academic evidence**
- **Harvey, Mazzoleni & Melone**, "The Unintended Consequences of Rebalancing", NBER WP 33554 (2025), WP.
  - A 1-SD rebalancing signal predicts equity returns **−16 bp (threshold) / −17 bp (calendar) over the next trading
    day**, reverting within about two weeks.
  - The calendar effect concentrates in the last week of the month.
  - Rebalancing is often done "synthetically" through futures overlays at or near month-end (pension memos).
  - Assets affected: over $20tn. Estimated cost: $16bn a year.
- **Etula, Rinne, Suominen & Vaittinen**, "Dash for Cash", *RFS* 33(1) 2020, PR; figures below from the working paper.
  - Returns turn around the last monthly settlement day, **T−3**. Annualised S&P return is **−3.4% over T−8 to T−4
    versus +28.6% over T−3 to T+3**.
  - Institutions are net sellers **in the morning of T−3**.

**Timing:** month-end and quarter-end, spread over the last week or the final days, often into the close via futures
overlays. Fully anticipated.

### 5. Index reconstitution

- **Russell reconstitution (EX, Nasdaq press releases):** **$102.5bn** in the Nasdaq Closing Cross on 27 Jun 2025,
  versus $95.3bn in 2024.
- **S&P 500 quarterly rebalance:** about **0.8% of index cap** per rebalance, 1995–2023. This is S&P DJI Indexology from
  a search snippet; the page returned 403, so it is unverified. S&P estimates about $16tn benchmarked to the index.
- Both trade in the closing auction, on the third Friday or at Russell recon, and are announced weeks ahead.
- **The net index-level flow is roughly zero** (adds funded by deletes and weight changes), so the pressure falls
  across stocks rather than on ES.
- Measured ES impact: not found.

### 6. Buybacks

**Size (EX)**
- S&P DJI (Silverblatt): **Q1 2025 $293.5bn (record), Q2 $234.6bn, Q3 $249.0bn**, and **$1.020tn over the 12 months to
  Sep 2025**. That averages **about $4bn per trading day**.
- Goldman's corporate desk (BANK via Tickmill/Advisor Perspectives): **more than $6bn a day** in open-window VWAP
  demand (Nov 2025), and **$4.5–5.5bn a day** disappearing during blackout. Up to about 85% of the S&P is in quiet
  periods late in the quarter.

**Timing (regulator):** SEC Rule 10b-18's safe harbour forbids the **opening trade** and the **last 10 minutes** for
liquid names, and caps volume at 25% of ADTV. In practice execution is VWAP through the day.

**Measured impact on ES:** not found. The flow is single-stock and spread through the day.

### 7. Forced-deleveraging episodes

**Feb 2018**
- Estimates of systematic selling disagree by more than 2×. JPM (Kolanovic): about **$100bn**. BofAML: **about $200bn**
  (CTAs plus risk parity). Barclays: **$225bn** from vol-target funds. All BANK, via Heisenberg Report.
- BIS Quarterly Review, Mar 2018 (WP), on the S&P's −4.1% day:
  - VIX exchange-traded products held about **$4bn** in assets.
  - **115,862 VIX futures traded in one minute at 16:08**.
  - Rebalancing ran "right before 16:15".
  - The BIS gives no equity-selling figure.

**Mar 2020:** the ECB model has a levered risk-parity book selling assets worth **about 225% of capital**. A measured
dollar figure was not found; a "$150bn over a month" claim is unverified.

**Aug 2024:** Nomura has vol-control funds at $83.6bn and CTAs at $12.5bn over two weeks, with Bloomberg's headline
"$170bn" of further possible selling.

### 8. Intraday momentum

- **Gao, Han, Li & Zhou**, "Market intraday momentum", *JFE* 129 (2018) 394–414, PR.
  - Sample: SPY 1993–2013. The first half-hour return predicts the last half-hour with **R² 1.6%**, rising to **2.6%
    with the 12th half-hour** added.
  - Timing strategy: **6.67% a year, Sharpe about 1.08, 54.37% hit rate, about 2.7 bp per trade**.
  - Stronger on volatile, high-volume and news days.
  - Explained as infrequent rebalancing and late-informed trading; the paper makes no flow attribution.
- **Baltussen, Da, Lammers & Martens**, "Hedging demand and market intraday momentum", *JFE* 142 (2021) 377–403, PR.
  - Sample: 60+ futures, 1974–2020. **ES β 6.18 (×100), t 4.97, out-of-sample R² 2.29%.**
  - Attributes the effect to **options market-maker gamma and LETF rebalancing** into the close. It is stronger when
    net gamma exposure is negative and increases with LETF market share across markets.
  - The effect reverses over the following days, and the paper does **not** cost the strategy.
- **PROJ D463:** on ES over 2016–23 the effect is **+1.18 bp per trade with β +1.8**, about a third of the published
  figure. The last half-hour itself drifted negative, and an a priori tertile split on Gao's first half-hour signal
  had the wrong sign.

### Summary table (C2)

For LETFs, use the index-only amounts. Other LETF figures (Tuzun's $1.04bn per 1% in 2011, the $5–7bn per 1%
whole-market figure) are not ES/NQ flow.

| mechanism | flow size ($, range) | timing | anticipated? | measured impact (bp) | source quality | notes |
|---|---|---|---|---|---|---|
| CTAs, normal week | ±$3–8bn global/week; S&P ≈ 35–60% | not established (claims of morning) | yes, weekly desk notes | not found | BANK | S&P holding $34bn of $93bn (Jun 2026) |
| CTAs, trigger/tail | $12.5–36bn per 2 wks (Aug 2024); $100–185bn/month in scenarios | multi-day | yes, trigger levels published | not found | BANK | the $150bn-in-3-days claim is unverified; discard |
| Vol-control | $37–57bn/day in 2015 model; $84bn per 2 wks (Aug 2024) | near close, 1–2 day lag | yes | not found (model: 9–41% of SPX futures volume) | practitioner model + BANK | AUM $300bn–2tn (uncertain) |
| Risk parity | AUM about $300bn; selling not measured | days | partly | not found | WP (ECB) | model: about 225% of capital sold in Mar 2020 |
| LETF, NDX products (TQQQ/SQQQ etc.) | **about $1.9bn per 1% NDX move** (2025) | last 30–60 min, MOC | yes, deterministic | ≤ a few bp; D640 null | PROJ + PR | flows offset up to 74% (Ivanov-Lenkey) |
| LETF, SPX products (UPRO/SPXU etc.) | **about $0.8bn per 1% SPX move** | last 30–60 min | yes | 6.9 bp per large stock per 1% (Tuzun, 2011 size) | PROJ + WP | 16.8% of MOC volume per 1% (2009) |
| Pension month/quarter-end | US pensions $14–32bn; global $150–165bn (JPM) | last week of month; T−3 morning; close via overlays | yes, published | −16/−17 bp next day per 1-SD signal | WP + PR + BANK | JPM vs GS about 5× apart |
| Index recon/rebalance | Russell $102.5bn in the closing cross; S&P about 0.8% of cap | closing auction | fully (weeks ahead) | not found for ES | EX | net index flow ≈ 0 |
| Buybacks | about $4bn/day average; $4.5–6bn/day open window; about 0 in blackout | VWAP through the day; no open trade or last 10 min | seasonality yes | not found | EX + regulator + BANK | single-stock, spread thin |
| Feb 2018 deleveraging | $100–225bn (bank spread more than 2×) | days; VIX ETPs 15:30–16:15 | partly | S&P −4.1% day (not attributed) | BANK + WP (BIS) | |
| Intraday momentum | n/a | last 30 min | yes | ES 2.7 bp/trade published; **1.2 bp in D463** | PR + PROJ | gamma plus LETF attribution |

**Main caveat for the sizing table:** the bank flow figures are scenario outputs whose method the press does not
disclose, and in the peer-reviewed work the measured impact is small or disputed. For the one flow the repo has tested
directly (LETF on NQ), the effect did not scale with LETF asset growth (D640).

---

## C3 — Auctions, market size, the impact law and microstructure

### Scope and method

Web sources were read at the primary text wherever I could get it. Several WebFetch summaries invented content, so I
extracted those PDFs myself: Osler, the two CFTC papers, Almgren, Tóth, and Kyle–Obizhaeva. Where published figures
were missing, I measured from on-disk fixtures: `data/fixtures/fut_index_sessions.csv.gz`, `fut_{ES,NQ}_rth_1m.csv.gz`,
`fut_micro_flow_5m.csv.gz`, `etf_wide_daily_raw.csv.gz` and `index_extended_15m_raw.csv.gz`. The scripts are in the
session scratchpad (`mkt_size.py`, `ten_am.py`, `etf_size.py`). I read no 2024+ futures slice for any construction;
these are descriptive counts only. *(D661 §5: several of these counts run past 2025-03-01, the vault's start. The
seal was not stated in the prompt, and D661 uses none of them.)*

### 1. Square-root impact law

- **Tóth, Lempérière, Deremble, de Lataillade, Kockelkoren & Bouchaud, "Anomalous price impact and the critical nature
  of liquidity", Phys. Rev. X 1, 021006 (2011), peer-reviewed.**
  - Form: Δ = Yσ√(Q/V), with σ and V the daily vol and daily volume "measured contemporaneously". The paper says "Y is
    of order unity".
  - Data: CFM's own futures metaorders, about 500,000 trades, June 2007 to December 2010.
  - Exponent δ ≈ 0.5 for small-tick contracts and ≈ 0.6 for large-tick contracts, valid for Q/V from a few 10⁻⁴ to a
    few %. ES is a large-tick contract, so δ ≈ 0.6 may fit it better than 0.5.
  - Their own gloss: 1% of daily volume moves price by a tenth of daily vol, which implies Y ≈ 1.
- **Sato & Kanazawa, PRL 135, 257401 (2025), peer-reviewed.** Eight years of Tokyo Stock Exchange data. δ = 1/2 within
  error, and the mean prefactor across stocks is ⟨c⟩ = 0.842.
- **Almgren, Thum, Hauptmann & Li, "Direct estimation of equity market impact", Risk (2005), practitioner journal.**
  - Data: about 700,000 Citigroup US large-cap orders, Dec 2001 to Jun 2003, 29,509 after filters.
  - Fits: temporary exponent β = 0.600 ± 0.038 (they reject 1/2 at 95%); permanent impact linear; γ = 0.314,
    η = 0.142.
  - Their IBM example, buying 10% of ADV, gives a realized cost of 32 / 25 / 18 bp over 0.1 / 0.2 / 0.5 days, with
    σ = 157 bp. That implies Y ≈ 0.64 / 0.50 / 0.36. So effective Y falls as execution slows, which the pure
    square-root form ignores.
- **Goyal, Jegadeesh & Wu, JFQA 2026, peer-reviewed.** For a 1%-ADV order the square-root fit gives 17.7 bp against
  2.35 bp from a linear fit, and impact is smallest in closing auctions. One discrepancy: the search abstract ties
  17.7 bp to the closing-auction fit, while repo notes call it "pooled". I did not resolve which.
- **Decay: Bucci, Benzaquen, Lillo & Bouchaud, arXiv 1901.05332 (Market Microstructure & Liquidity 2019),
  peer-reviewed.** Over 8 million ANcerno equity metaorders. By the end of the same day impact is ≈ 2/3 of peak. It
  then converges over about 50 days to ≈ 1/2 of the end-of-day-1 value, so roughly 1/3 of peak is permanent. I found
  no futures-specific decay figure.
- **Which V to use.**
  - Kyle & Obizhaeva, "Large Bets and Stock Market Crashes" (Review of Finance; I read a working-paper draft) put the
    combined futures-plus-stock volume in the denominator. For the Flash Crash that was $132bn/day of E-mini plus
    $161bn/day of stock.
  - Tomas, Mastromatteo & Benzaquen, "Cross impact in derivative markets" (arXiv 2102.02834, published venue not
    verified) find, on E-mini futures, options and VIX futures, that no-arbitrage cross-impact pools order flow across
    derivatives and underlying.
  - Using the combined complex lowers Q/V by roughly 2–4× and the impact by about √ of that.
- **Stress case: 6 May 2010 (Kyle & Obizhaeva).** A $4.37bn sale of 75,000 ES contracts, run over 19 minutes, was
  3.31% of futures ADV and 1.49% of the combined complex.
  - Actual decline: **5.12%, transitory**.
  - Their invariance prediction: 0.61% (range 0.44–0.73%).
  - My arithmetic, square-root with Y = 1 at σ = 1.07%: 0.19% on futures volume only, 0.13% on the combined complex.
  - So for fast execution the law understates the peak by more than 25×. Kyle & Obizhaeva also argue that impact per
    fraction of volume grows with the cube root of dollar volume, which contradicts a universal Y. That is a
    disagreement of more than 2×.

### 2. Market size (measured unless noted)

**ES**, front month, full Globex day, mean contracts/day:

| Year | Contracts/day | Notional/day | Daily σ (16:00–16:00, roll days dropped) |
|---|---|---|---|
| 2023 | 1.53M | $339bn | 83 bp |
| 2024 | 1.37M | $383bn | 80 bp |
| 2025 | 1.37M | $439bn | 119 bp |

**NQ**, same basis:

| Year | Contracts/day | Notional/day | Daily σ |
|---|---|---|---|
| 2023 | 606k | $178bn | 114 bp |
| 2024 | 569k | $224bn | 114 bp |
| 2025 | 535k | $248bn | 149 bp |

These are front-month only, so roll weeks understate slightly.

**Micros** (fixture window 2025-09 to 2026-09):
- MES was 0.89× ES contracts, which is **8.2% of combined notional**. MNQ was 3.8× NQ contracts, **27.6% of combined
  notional**.
- CME's 2025 press release gives MES ADV of 1.2M (exchange data). The fixture gives MNQ about 2.06M/day.

**ETFs** (2023/24/25):
- SPY mean $/day: $35bn / $31bn / $45bn.
- QQQ mean $/day: $18bn / $17bn / $27bn.

**All US equities** (Cboe 2025 Year in Review, exchange data): 17.6bn shares and **$1.1T/day** in 2025, up 43% year
on year. The implied 2024 figure is about $0.77T.

**Intraday U-shape, 2023–25:**

| Instrument | 09:30–10:00 | 10:00–11:00 |
|---|---|---|
| ES, share of 09:30–16:00 volume | 13.3% (10.7% of full day) | 19.8% (16.0% of full day) |
| NQ, share of RTH volume | 15.7% (12.3% of day) | 21.2% (16.6% of day) |
| SPY, share of RTH volume | 11.2% | 16.2% |
| QQQ, share of RTH volume | 14.1% | 18.4% |

- ES first minute: 1.06% of RTH volume.
- Median first-30-minute dollar volume: ES $38.7bn, NQ $25.6bn.

### 3. Opening auctions

- **NYSE opening auction** (NYSE Data Insights, May 2024, exchange data): **44M shares, $2.4bn/day** over Jan–Apr 2024.
- **Share of volume** (Tethys "Auction Volume Report: Americas", Aug 2025, 6 months, vendor), notional-weighted:
  - Opening auction: NYSE **1.25%**, Nasdaq **0.99%**.
  - Closing auction: NYSE 14.0%, Nasdaq 9.2%.
- **Older figure** (Greenwich, 2017, vendor): opening auctions went from 1.1% to 1.25% of volume.
- **Closing auctions** (secondary summaries of BMLL and NYSE): about $50bn/day and about 9% in 2024, 9.44% in Q2 2024.
  The Nasdaq Closing Cross averages about $25.6bn/day (Nasdaq).
- **Aggregate S&P 500 opening imbalance in $: not found**, either typical or extreme. An upper bound is that total
  opening-auction value is about $2.4bn on NYSE plus an unpublished amount on Nasdaq.
- **Is imbalance published before 09:30?** Yes.
  - NYSE: opening imbalance every second from **08:00 ET** (NYSE).
  - Nasdaq NOII: every second from **09:28** (SEC Release 34-91096, Feb 2021). That filing proposed an abbreviated
    EOII starting at 09:25; I did not verify whether it was adopted.
- **Databento, public pages only** — an `imbalance` schema exists:
  - NYSE Integrated (`XNYS.PILLAR`) history starts **2018-05-01**. Arca and American carry it too, and historical
    imbalance was released January 2025.
  - `XNAS.ITCH` history starts in 2018.
  - **2016–2017 are not available from Databento.** NYSE TAQ Order Imbalance would be the route for those years.
  - Historical per-GB prices are not published per schema. The imbalance-only licence (real-time) "start[s] at
    $1,000/month". Live data needs Plus or Unlimited.
- **Does opening imbalance predict the index's post-open return?** Not found at index level. The only evidence is
  stock-level: Chordia & Subrahmanyam (JFE 2004), and Lachance (JFM 2021), who finds opening imbalance inflates ETF
  overnight returns by 2.54 bp/day.

### 4. Stops and cascades

- **Osler (2003, JF 58(5)).** Take-profit orders cluster at round numbers and stop-losses just beyond them. Data:
  executed orders at one large FX dealing bank, Sep 1999 to Apr 2000.
- **Osler (2005, JIMF 24(2)).**
  - Orders: 9,655 orders, $55bn face value, 1999–2000; stops were 43% of orders by volume.
  - Tests: Reuters one-minute quotes for DEM, JPY and GBP, New York hours, 1996–1998.
  - DEM moved **0.061% in the 15 minutes after crossing a round number vs 0.054%** after an arbitrary number. That is
    about 0.7 bp, or 13% extra.
  - Reversal rate: 59.3% at round numbers vs 54.8% elsewhere.
  - Significant for hours but not for days. The effect is real but small.
- **ES directly: Fett & McPhail, "Stop Orders in Select Futures Markets", CFTC OCE 2017-009 (regulator staff paper).**
  - Executed stop orders were **0.9% of ES volume** in 2014–2016: 22.8M of 2.48bn contracts. 98% of them were
    stop-limit orders.
  - Stop usage is "highly correlated with intraday price volatility".
  - I found no ES round-number cascade estimate.

### 5. Who trades

- **CFTC OCE, Haynes & Roberts, 2012–14.**
  - ES volume: 43.4% automated vs automated, 42.6% automated vs manual, **13.8% manual vs manual**.
  - NQ: 6.9% manual vs manual.
- **Ferko, Mixon & Onur, CFTC 2024.** Retail traders most often hold Micro E-mini S&P and Nasdaq contracts. Retail
  share of volume was not reported; open-interest share appears only as a chart.
- **CME marketing claim:** retail participation in micros "grew 22%". Treat as marketing.
- **Trade size in the fixture:** one-lot trades are 54–55% of ES and MES trades, and 63% of MNQ and 76% of NQ trades.
  Micro volume is not a clean retail proxy (repo memory).
- **Opening-range-breakout or intraday-momentum volume: not found.**

### 6. 10:00 ET releases

- **Andersen, Bollerslev, Diebold & Vega (J. Int. Econ. 73, 2007), peer-reviewed.** Five-minute S&P futures data,
  1994–2002. Responses sit almost entirely in the first five minutes. For equities the full sample shows "almost no
  significant responses", and the sign flips between expansions and contractions. No bp volatility figure is
  tabulated.
- **Measured here (ES and NQ, 2016–25).** Release days were assigned by calendar rule: ISM manufacturing = first
  trading day, n = 120; Conference Board = last Tuesday; "other" days, n = 2,218, include other 10:00 releases, which
  biases the gap toward zero.

| ES | ISM mfg days | Other days |
|---|---|---|
| Median \|10:00→10:05\| | **8.2 bp** | 5.3 bp |
| 90th percentile | 24.6 bp | 18.8 bp |
| 10:00–10:30 range | 40 bp | 28 bp |
| Realized vol | 24 bp | 18 bp |

- NQ: 11.8 vs 7.9 bp; range 54 vs 41 bp.
- Conference Board days are indistinguishable from other days (5.4 bp).
- ISM services days (third trading day, a weaker rule) show 8.2 bp.
- The first trading day also carries turn-of-month flows, so this attribution is not clean.

### Summary table (C3)

| item | number (range) | timing | source quality | notes |
|---|---|---|---|---|
| Y prefactor | 0.4–1.0 (central ~0.7–0.85) | any | peer-reviewed (Tóth; Sato–Kanazawa 0.842); Almgren-implied 0.36–0.64 | Y falls with slower execution |
| Exponent δ | 0.5 small-tick; 0.6 large-tick (ES) | — | Tóth 2011 | Almgren β = 0.6 |
| Impact decay | ~2/3 of peak by close; ~1/3 of peak permanent at ~50 d | days | peer-reviewed, equities | no futures figure found |
| Fast-execution peak | 5.12% actual vs 0.19% (sqrt) / 0.61% (invariance) | 19 min | Kyle–Obizhaeva | reverted; >25× understatement |
| Which V | futures alone vs complex: 2–4× difference in V | — | K–O; Tomas et al. | use combined for permanent impact |
| ES ADV | 1.37–1.53M contracts; $339–439bn | 2023–25 | measured (front month) | σ 80–119 bp |
| NQ ADV | 535–606k; $178–248bn | 2023–25 | measured | σ 114–149 bp |
| Micro share of notional | ES 8.2%, NQ 27.6% | 2025–26 | measured; CME MES 1.2M | micro ≠ retail |
| SPY / QQQ $/day | $31–45bn / $17–27bn | 2023–25 | measured | |
| US equities $/day | $1.1T (2025); ~$0.77T (2024) | — | Cboe | all names |
| 09:30–10:00 share | ES 13.3% RTH (10.7% day); NQ 15.7%; SPY 11.2% | — | measured | ES first-30-min ≈ $38.7bn |
| 10:00–11:00 share | ES 19.8%; NQ 21.2%; SPY 16.2% | — | measured | |
| Opening auction | NYSE $2.4bn/day; 1.25% NYSE, 0.99% Nasdaq | 09:30 | exchange / vendor | closing 9–14% |
| Aggregate opening imbalance $ | not found | pre-09:30 | — | bounded by auction size |
| Imbalance feed | NYSE from 08:00; NOII from 09:28 | pre-open | exchange / SEC | Databento from 2018 only |
| Opening imbalance → index return | not found | — | — | stock-level only |
| ES stop-order volume | 0.9% (2014–16) | intraday | CFTC staff | 98% stop-limit |
| Round-number cascade | +0.7 bp per 15 min (FX, DEM) | 15 min–hours | Osler, JIMF | small |
| Manual-only ES volume | 13.8% (NQ 6.9%) | 2012–14 | CFTC staff | dated |
| ISM mfg 10:00 move (ES) | 8.2 vs 5.3 bp (5 min); range 40 vs 28 bp | 10:00–10:30 | measured, rule-dated | NQ 11.8 vs 7.9 bp |
| Conference Board 10:00 | no measurable effect | 10:00 | measured | |
