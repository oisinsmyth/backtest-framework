# Structural Decay Instruments: Can We Short Something With Negative Expected Drift?

**Stream:** Shorts / 02
**Date:** 2026-08-28
**Status:** Web research only. No backtests run. No code touched.

---

## 0. Executive summary

The premise of this stream was: our shorts keep dying because they fight +8.59%/yr of overnight
equity drift, so find an instrument whose expected drift is mathematically negative and short that
instead.

**The research finds one genuinely negative-drift instrument class (volatility ETPs) and one
partially negative-drift class (contangoed commodity ETFs). Neither solves our problem, for three
separate reasons, and the leveraged-pair trade — the one the brief singled out — is worse than
"priced away": it is mathematically zero before any costs are applied.**

The four findings, in order of importance:

1. **The short-both-sides leveraged pair trade has exactly zero expected return, not a
   fee-eroded positive one.** If you hold matched notional in short TQQQ and short SQQQ, the daily
   P&L is identically zero before frictions. The "decay harvest" that appears in unrebalanced
   backtests is not decay at all — it is a disguised bet on negative serial correlation in the
   underlying index. See §2.2. This is the most important result in this document and it kills the
   idea outright, independently of borrow cost.

2. **Where decay is genuinely large (VXX, UVXY: ~50%/yr), the borrow market has *not* priced it
   away.** Real IBKR borrow on 2026-08-28 is 3.05% for VXX and 3.34% for UVXY against ~50%/yr of
   decay. The arbitrage argument fails here — but not because there is free money. It fails because
   the binding constraint is not borrow, it is **margin and tail risk**, i.e. exactly our
   `gross = exposure × edge` constraint. See §3.

3. **Every structural decay we found is a risk premium paid for bearing crash risk, which means
   shorting it is long-equity-beta in disguise.** A short VXX position is not a hedge against our
   long book; it is a levered doubling-down on it. This is a strategic finding that applies to the
   entire stream: the reason "negative drift" instruments exist at all is that someone is being paid
   to hold the other side of a crash. We would be selling that insurance. That does not diversify a
   long book — it concentrates it. See §6.

4. **Data integrity warning, actionable immediately: the +733% single bar in our USO/UNG fixture is
   almost certainly a reverse-split artifact, not a market move.** USO executed a 1-for-8 reverse
   split effective 2020-04-29 (an unadjusted +700% bar) and UNG has had multiple 1-for-4s. If our
   fixture shows a +733% bar, the series is not split-adjusted, and **every result our framework has
   ever produced touching USO or UNG is contaminated.** See §4.3. This should be verified before
   anything else in this document is acted on.

**Recommendation: do not pursue any of these as a short strategy.** The one candidate with a
defensible net edge (short VXX) is (a) a well-known crowded short-vol trade, (b) sizeable at only
~5% of book, yielding ~2.4%/yr gross of the tail, and (c) positively correlated with our existing
long exposure, so it fails the diversification test that motivated the shorts programme. Detail and
ranking in §7.

---

## 1. The mathematics of leveraged ETF decay

### 1.1 The closed form

For a fund targeting `L` times the daily return of an underlying with annualised volatility `σ`, the
expected drag relative to `L ×` the underlying's compound return is:

```
drag  ≈  0.5 · L · (L − 1) · σ²     per unit time
```

This is the standard result from Cheng & Madhavan (2009), reproduced in the Elm Wealth note and in
the SSRN literature. Note the two consequences that matter:

- **Drag scales with `L(L−1)`, not with `L`.** A 3x fund suffers 3x the drag of a 2x fund
  (`3·2 = 6` vs `2·1 = 2`), not 1.5x.
- **Drag scales with `σ²`.** Doubling volatility quadruples the drag. This is why SOXL/SOXS and
  LABU/LABD look far more attractive than SSO/SDS — and also why they are far more dangerous.
- **Inverse funds have `L = −1`, giving `L(L−1) = 2`.** A plain −1x inverse fund has the same drag
  coefficient as a +2x fund. It decays even though it is unlevered in magnitude. This is a real and
  underappreciated point: `SH`, `PSQ`, `DOG` all have structurally negative drift *relative to
  minus the index*, on top of fighting the index itself.

Worked magnitudes at realistic volatilities:

| Fund | L | σ (ann.) | `0.5·L(L−1)σ²` |
|---|---|---|---|
| SSO (2x S&P) | 2 | 18% | 3.2%/yr |
| SDS (−2x S&P) | −2 | 18% | 9.7%/yr |
| TQQQ (3x NDX) | 3 | 25% | 18.8%/yr |
| SQQQ (−3x NDX) | −3 | 25% | 37.5%/yr |
| SOXL (3x semis) | 3 | 45% | 60.8%/yr |
| SOXS (−3x semis) | −3 | 45% | 121.5%/yr |

Elm Wealth give the TQQQ case explicitly: at 6.5% expected underlying return and 25% vol, the ~19%
drag reduces a naively-expected 19.5% to roughly 0.5%.

**Note the asymmetry**: the inverse leg always has the larger drag coefficient
(`L(L−1)` for `−L` is `L(L+1)`). This matters in §2.

Sources:
- [Cheng & Madhavan-style derivation, Elm Wealth](https://elmwealth.com/double-short-etf/)
- [Lin, Lin, Wang & Yeh, "Volatility Decay and Arbitrage in Leveraged ETFs: Evidence from the US and Japan", SSRN 5421274](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5421274)
- [Balter, Garcia & Schweizer, "Daily leverage and long-term investing using leveraged ETFs", Netspar](https://www.netspar.nl/wp-content/uploads/paper_Balter_Garcia_Schweizer.pdf)

### 1.2 What the drag actually is

The drag is not a fee and nobody collects it. It is the arithmetic gap between the compound return of
a daily-rebalanced levered position and `L ×` the compound return of the underlying. It is the same
quantity as the convexity cost of any constant-leverage rebalancing rule.

This matters for our purposes because **there is no counterparty who pays it to you.** The
fund's daily rebalancing trades happen in the market at market prices. The decay is not a transfer;
it is a path-dependent accounting fact. That is the seed of the problem in §2.2.

---

## 2. The leveraged pair short (short TQQQ + short SQQQ)

### 2.1 What the empirical literature reports

This is a well-studied trade. The headline results:

**CXO Advisory, monthly-rebalanced, six 3x/−3x pairs (FAS/FAZ, TQQQ/SQQQ, TNA/TZA, UPRO/SPXU,
JNUG/JDST, ERX/ERY), end-2007 through Dec 2016:** four of six pairs produced average monthly returns
over 1%. **The paper states explicitly that these are gross, with no borrow or rebalancing costs
deducted.**
[Source](https://www.cxoadvisory.com/volatility-effects/monthly-rebalanced-shorting-of-leveraged-etf-pairs/)

**CXO Advisory update, inception through Jan 2020**, monthly rebalancing, −$100,000 short in each
leg funded from $200,000 cash:

| Pair | Avg monthly gain | SD | % losing months | Worst month |
|---|---|---|---|---|
| SSO / SDS (2x) | $514 | $1,977 | 38% | −$2,169 |
| UPRO / SPXU (3x) | $532 | $2,119 | 35% | −$4,275 |
| TQQQ / SQQQ (3x) | $600 | $2,883 | 35% | −$11,059 |

**The break-even carrying cost is stated at 0.25% per month for the 2x pairs and 0.30% per month
for TQQQ/SQQQ — i.e. approximately 3.0% to 3.6% annualised on the shorted notional.**
[Source](https://www.cxoadvisory.com/short-selling/leveraged-etf-pair-shorting-strategies/)

That break-even number is the single most useful figure in the empirical literature, and it should
be read against the actual borrow rates in §2.4. Note also the tail already visible in the gross
numbers: **TQQQ/SQQQ lost $11,059 in its worst month on $200,000 of gross short — a 5.5% monthly
loss on a strategy whose mean is 0.30%/month.** That is an 18-to-1 worst-month-to-mean ratio, in a
sample that ends in January 2020 and therefore *excludes the COVID crash entirely*.

**Tsalikis & Papadopoulos, "Can shorting leveraged exchange-traded fund pairs be a profitable
trade?", Journal of Investment Strategies.** Two years of S&P 500 leveraged ETFs, monthly holding
periods, both the 2x and 3x pairs. The abstract: the strategy produced a profit for both pairs,
**"however, after considering shorting fees for the funds, the profitability of this strategy for
both pairs was highly diminished."**
[Abstract](https://www.risk.net/journal-of-investment-strategies/6983576/can-shorting-leveraged-exchange-traded-fund-pairs-be-a-profitable-trade)
· [EconBiz record](https://www.econbiz.de/Record/can-shorting-leveraged-exchange-traded-fund-pairs-be-a-profitable-trade-tsalikis-george/10012140132)

> **Caveat on a widely-quoted number.** Secondary sources report this study's Jul-2015 to Aug-2017
> window as **4.90% annualised gross, falling to 0.27% annualised after shorting fees**. I could not
> verify those exact figures against the primary source (risk.net is paywalled). Treat the direction
> as confirmed by the abstract and the specific decimals as unverified.

**Kinlay (2018), "Investing in Leveraged ETFs — Theory and Practice."** This is the most useful
practitioner treatment because it isolates the rebalancing question. Kinlay tests four pairs under
two accounting conventions and deducts realistic borrow (ERX/ERY 14%, NUGT/DUST 16%, SPXL/SPXS 8%,
TNA/TZA 8%):

- Under continuous compounding (i.e. never rebalancing, letting the legs drift): NUGT/DUST shows
  124% CAGR at 8.4 Sharpe, ERX/ERY 4.5 Sharpe, TNA/TZA 20% CAGR. These numbers are absurd on their
  face and should be the tell.
- Under daily compounding (i.e. actually rebalancing to matched notional): **multiple pairs show
  negative CAGR.** Drawdowns to 75%. No clear relationship between rebalancing period and return.
- His conclusion: infrequent rebalancing means you carry directional market risk; frequent
  rebalancing means transaction costs eat the return. **"Either way, you lose."**

[Source](https://jonathankinlay.com/2018/11/investing-leveraged-etfs-theory-practice/)

### 2.2 Why the trade is zero — the decisive argument

Kinlay's empirical result has a clean analytical explanation, stated most directly by Elm Wealth in
their analysis of the proposed "Double Short Hedged" MSTR structure:

> At the start of each day, the Double Short ETF will effectively have a 2x short position in MSTR
> exactly offset by a 2x long position in MSTR. Whatever MSTR's return is for a given day, the daily
> profit in the Double Short ETF will be zero.

[Source](https://elmwealth.com/double-short-etf/)

Written out for our case. Short `$N` of TQQQ and `$N` of SQQQ. The index returns `r` on the day.

- TQQQ returns `+3r`; the short loses `3rN`.
- SQQQ returns `−3r`; the short gains `3rN`.
- **Net daily P&L: exactly zero.** For any `r`. Before borrow, before commissions, before slippage.

The decay is real, it is happening to both funds, and *you capture none of it*, because the two
decays are the two halves of a position that nets to zero exposure.

So where do the positive backtest numbers come from? From the notional drift you get if you *don't*
rebalance. After the up-day, the legs are no longer matched:

- TQQQ short is now `N(1+3r)`; SQQQ short is now `N(1−3r)`.
- Net index delta = `−3·N(1+3r) + 3·N(1−3r) = −18rN`.

**After an up move you are net short. After a down move you are net long.** The position makes money
if and only if the index reverses, and loses if the index trends. Concretely, the canonical
"proof" of the trade — index goes +10% then −9.09%, both funds fall, both shorts profit `$16.36` on
`$200` — smuggles in its own answer: *the index round-tripped.* That is mean reversion assumed, not
decay harvested. If day 2 had been another +10%, the trade loses.

This is exactly what the Journal of Investment Strategies framework says, and it is worth quoting
the mechanism as the authors describe it: the trade is a bet on mean reversion of the underlying
index, with expected return high when the average of daily autocorrelations across lags is negative
and volatility is high.

**Therefore:**

- Rebalance daily to matched notional → **expected gross return is identically zero**, and you pay
  borrow plus rebalancing costs. Guaranteed loss.
- Do not rebalance → you are running an unhedged, negatively-autocorrelated, short-trend position
  with 3x-levered legs. That is a momentum-reversal strategy wearing a costume, and it has nothing
  to do with structural decay. We should evaluate it as a mean-reversion signal on QQQ, where we can
  test it far more cheaply and without borrow.

This finding invalidates the entire premise of §2 as a *decay* trade. I consider it settled.

### 2.3 The cost of rebalancing, computed against our 1.85 bp

For completeness, since the answer is "zero minus costs," here is the cost.

Daily rebalance to matched notional. After a day with index return `r`, each leg is `N(1±3r)`;
restoring equality requires trading `3|r|N` on each leg, so `6|r|N` total turnover.

For QQQ, daily `σ ≈ 1.1%`, so `E|r| ≈ 0.8σ ≈ 0.88%`. Turnover per day `≈ 6 × 0.88% × N = 5.3%N`.

```
cost/day   = 5.3% · N · 1.85 bp  =  0.98 bp of N
cost/year  = 0.98 bp × 252       =  2.47% of N per year
```

On gross short notional of `2N`, that is **~1.23%/yr**. Not catastrophic in isolation — but it is
being paid against an expected gross of zero. Add borrow (§2.4) and the trade is a reliable loss of
roughly 3–4%/yr on gross short.

### 2.4 Actual borrow rates — the market has partially, but not fully, priced this

Live IBKR data via ChartExchange, all sampled **2026-08-28, 13:18 EDT**:

| Ticker | Borrow fee | Shares available |
|---|---|---|
| TQQQ | **0.81%** | 10,000,000 |
| SQQQ | **2.90%** | 1,700,000 |
| VXX | **3.05%** | 1,200,000 |
| UVXY | **3.34%** | 1,000,000 |

Sources:
[TQQQ](https://chartexchange.com/symbol/nasdaq-tqqq/borrow-fee/) ·
[SQQQ](https://chartexchange.com/symbol/nasdaq-sqqq/borrow-fee/) ·
[VXX](https://chartexchange.com/symbol/bats-vxx/borrow-fee/) ·
[UVXY](https://chartexchange.com/symbol/bats-uvxy/borrow-fee/)

Read this carefully, because it is more interesting than the naive arbitrage story:

- **Average TQQQ/SQQQ pair borrow is ~1.86%/yr on gross short.** That is *below* the CXO break-even
  of 3.0–3.6%/yr. On the CXO framing, the trade looks alive. It is not, because of §2.2 — the CXO
  gross number is a mean-reversion payoff from monthly non-rebalancing, not a decay yield.
- **The borrow market has not "priced away" the decay, because the decay was never a transferable
  yield.** There is nothing to arbitrage. Borrow prices *scarcity of shares*, and TQQQ has 10 million
  shares available at 81 bp because a very large retail long base lends freely.
- **These are calm-market snapshots and are the wrong number for risk purposes.** Practitioner
  reports describe leveraged and volatility ETF borrow jumping "from 24.46% to 47.53% in one day"
  and "from 10% one day to 50% the next." Borrow reprices violently in exactly the conditions where
  a short position is already losing.

Sources on borrow instability and recall:
[Leverage ETF short selling notes](http://lidzzh.blogspot.com/2017/11/leverage-etf-short-selling-why-not-hold.html) ·
[IBKR, The Risks of Shorting: Borrow Fees](https://www.interactivebrokers.com/campus/traders-insight/securities/short-selling/the-risks-of-shorting-series-part-ii-borrow-fees/) ·
[IBKR short sale cost methodology](https://www.interactivebrokers.com/en/pricing/short-sale-cost.php)

### 2.5 Margin — the binding constraint, and why `exposure` is small

FINRA Regulatory Notice 09-53, effective 2009-12-01, raised maintenance margin on leveraged ETFs
"by a percentage commensurate with the leverage of the ETF." Applied to the standard 30% short
maintenance requirement:

- Short a 3x leveraged ETF → **90% maintenance margin of market value.**
- Short a 2x → 60%.

[FINRA RN 09-53](https://www.finra.org/rules-guidance/notices/09-53) ·
[FINRA non-traditional ETF margin notice](https://www.finra.org/sites/default/files/NoticeDocument/p119906.pdf) ·
[FINRA Rule 4210](https://www.finra.org/rules-guidance/key-topics/margin-accounts)

House requirements on volatility ETP shorts are commonly higher still, sometimes 100%+. The
practical consequence for `gross = exposure × edge`: shorting a matched 3x pair at `$N` per leg ties
up roughly `1.8 × N` of equity to hold `2N` of gross short. **You cannot lever this into
significance.** Even if the edge were real rather than zero, the deployable exposure is capped near
1.1x book.

### 2.6 Recall and squeeze risk

- Shares can be recalled at any time, forcing a buy-in at the worst possible moment. This is not
  hypothetical for these names: they are structurally hard-to-borrow because the short side is a
  crowded retail trade.
- **Historical precedent for a supply shutoff: Barclays suspended new VXX issuance in 2012.** With
  creations halted, VXX traded like a closed-end fund; borrow availability collapsed and the ETN
  developed a persistent premium to indicative value. A short in place at that moment was
  squeezed by a mechanism entirely outside the price of the underlying index.
  [S3 Partners, "VXX Sales Suspended: Volatility Strikes ETFs"](https://www.s3partners.com/articles/vxx-short-selling)
- Practitioner reports that shorting UVXY is at times simply not possible because no borrow exists.

**This is a structural point worth internalising: the instrument itself can be withdrawn, restruck,
or re-levered by the issuer while you hold the position.** It happened to XIV (terminated, §3.2), to
SVXY (re-levered from −1x to −0.5x overnight, §3.2), to VXX (issuance suspended), and to USO (holdings
rewritten mid-crisis, §4.3). No equity short carries this class of risk.

---

## 3. Volatility ETP roll decay — VXX, UVXY, VIXY

This is where the decay is genuinely enormous and genuinely not offset by borrow. It is also where
the tail is genuinely capable of ending the fund.

### 3.1 The magnitude of the decay

- **VXX has averaged approximately a 52% annual loss since inception in January 2009** — roughly
  −6%/month. VXX has executed **eight 1-for-4 reverse splits**; an unbroken share-price series would
  put its January 2009 $100 start at roughly $102,400 in today's terms.
  [Six Figure Investing on VXX reverse splits](https://www.sixfigureinvesting.com/2013/08/next-vxx-reverse-split/) ·
  [VXX split history](https://www.splithistory.com/vxx/)
- Decay is regime-dependent: roughly 3.5%/month in the higher-vol 2014–2015 stretch, back to 7–9%/month
  in calm 2016. Practitioner estimates for UVXY (1.5x since 2018) run near 20%/month absent a
  correction.
- The mechanism is contango roll yield: the fund holds a constant-maturity blend of front two VIX
  futures and must sell the cheaper expiring contract to buy the more expensive later one. Reported
  roll cost in contango is roughly 5%/month, 3–8%/month depending on curve steepness.
  [Volatility Box on VIX ETFs](https://volatilitybox.com/research/vix-etfs-explained/) ·
  [See It Market, "Exposing the VXX"](https://www.seeitmarket.com/exposing-the-vxx-understanding-volatility-contango-and-time-decay/)

**Against a borrow cost of 3.05% (VXX) / 3.34% (UVXY), this is a gap of roughly 47 percentage points
per year.** On the face of it, this is the one candidate in the entire brief where the decay
massively exceeds the borrow.

**So why hasn't arbitrage closed it?** Because it is not an arbitrage. The contango is the variance
risk premium — the price of insurance against a volatility spike. Collecting it is selling that
insurance. The borrow market prices share *scarcity*, and shares are not scarce (a large retail long
base lends freely). The price of the risk is expressed in margin requirements and in the tail, not
in the lending fee. **This is a case where "the fee eats it" is the wrong answer and I want to be
precise about that — the fee does not eat it. The tail does.**

### 3.2 The tail: 2018-02-05, quantified

This is the canonical event and any honest assessment must state it in full.

| Fact | Value |
|---|---|
| VIX close 2018-02-02 → 2018-02-05 | 17.31 → 37.32, **+115.6%** — largest one-day rise in VIX history (prior record +64%, Feb 2007) |
| Front VIX futures blend | **+96–97%** from prior close |
| XIV (Credit Suisse −1x inverse VIX ETN) | $108.37 → $4.22, **−96%** |
| XIV AUM on 2018-02-01 | **$1.9 billion** |
| XIV acceleration trigger | prospectus clause: >80% single-day decline in indicative value → issuer terminates. Triggered. Fund liquidated. |
| SVXY (ProShares −1x) | **−91%** on the day; survived, but ProShares cut target exposure from −1x to **−0.5x** effective the next trading day |
| Aggregate inverse-vol ETP losses | **~$3 billion in roughly 50 minutes** |

Sources:
[AMF France, "Heightened volatility in early February 2018: the impact of VIX products"](https://www.amf-france.org/sites/institutionnel/files/contenu_simple/lettre_ou_cahier/risques_tendances/Heightened%20volatility%20in%20early%20February%202018%20the%20impact%20of%20VIX%20products.pdf) ·
[Cboe, "After the Volpocalypse"](https://cdn.cboe.com/resources/education/research_publications/after-the-volpocalypse-market-observation.pdf) ·
[Six Figure Investing, "What Caused Volmageddon"](https://www.sixfigureinvesting.com/2019/02/what-caused-the-february-5th-2018-volatility-spike-xiv-termination/) ·
[CNBC, 2018-02-06](https://www.cnbc.com/2018/02/06/the-obscure-volatility-security-thats-become-the-focus-of-this-sell-off-is-halted-after-an-80-percent-plunge.html) ·
[Macroption, VIX all-time spikes](https://www.macroption.com/vix-all-time-high/)

**Was anyone wiped out? Yes, comprehensively.** XIV holders lost essentially their entire principal
with no possibility of recovery — the termination clause converted a mark-to-market loss into a
realised, permanent one at the intraday low. A $1.9bn fund went to near-zero in a single session.
This is the cleanest available demonstration that short-volatility positions do not merely drawdown,
they terminate.

Note the asymmetry direction relative to our proposed trade: XIV holders were *long* an inverse
product. **A trader who was short VXX or short UVXY was on the losing side in the same event, and
worse off**, because a short has unbounded loss. Which brings us to:

### 3.3 The tail for a short position specifically

For a short seller of a long-vol ETP, the relevant number is not "the inverse fund fell 96%" but
"how much did the long fund rise."

| Episode | Long-vol ETP move | Loss on a 100%-of-notional short |
|---|---|---|
| Aug 2011 correction | **UVXY +550%** | −550% of notional |
| Feb–Mar 2020 COVID | **UVXY (1.5x) +over 10x** | roughly −900% of notional |
| 2008–09 (simulated 2x UVIX) | **+20x** | roughly −1,900% of notional |
| 2018-02-05 | VIX futures blend +96–97% in one day | roughly −100% of notional in a session (UVXY, 1.5x at the time, considerably more) |
| 2024-08-05 | VIX intraday high **65.73**, ~+180% intraday from prior close | large intraday, partially retraced |

Sources:
[Six Figure Investing, "Is Shorting UVXY, TVIX, VXX the Perfect Trade?"](https://www.sixfigureinvesting.com/2016/10/is-shorting-uvxy-tvix-vxx-the-perfect-trade/) ·
[BIS Bulletin 95, "Anatomy of the VIX spike in August 2024"](https://www.bis.org/publ/bisbull95.pdf) ·
[SEC DERA, "Demystify the Surge in VIX" (2025)](https://www.sec.gov/files/dera-vix-working-paper-2504.pdf)

The author of the most careful practitioner treatment concludes: **"I think considerably more is
lost on the long side, but the blowouts on the short side tend to be quick and vicious."**

**Sizing implication.** To survive a UVXY +550% event without ruin you can hold at most ~15% of book
short, and that assumes you survive the margin calls on the way — which you would not, because
maintenance requirements expand precisely during the spike. To survive a +10x event you can hold at
most ~10%. Realistic sizing is **5% of book**.

```
short VXX at 5% of book
gross  = 5% × 50%/yr decay            =  2.50%/yr
borrow = 5% × 3.05%                   = −0.15%/yr
net                                    ≈  2.35%/yr
```

Against a 2018-02-05-magnitude event: a ~2%–5% single-day book loss, and against a Feb–Mar 2020
repeat, a ~20%+ book loss, with borrow repricing to 10–50% while you hold it.

**2.35%/yr for a ~20% tail is a poor trade, and it is the *best* candidate in this document.**

### 3.4 Does the decay persist post-2018?

Yes, but the after-2018 record is materially worse for short-vol:

- SVXY (−0.5x since Feb 2018) reports **max drawdown −95.2%** over its history and long-run returns
  above SPY (~14.25% vs ~10.42%) with far higher volatility and drawdown.
- SVIX (−1x, launched 2021) reports **max drawdown −79.3%**, and suffered a severe hit on 2024-08-05.
  Sources note it was "down almost 40%" over a stretch following that event.
- The structural change matters: after Volmageddon the issuers themselves de-levered. **The market's
  own response to the tail was to reduce the exposure you are allowed to take** — which is precisely
  the `exposure` term in `gross = exposure × edge` being crushed by the regulator and the issuer
  rather than by us.

[PortfoliosLab SVXY](https://portfolioslab.com/symbol/SVXY) ·
[Composer SVIX metrics](https://www.composer.trade/etf/SVIX) ·
[ProShares SVXY](https://www.proshares.com/our-etfs/strategic/svxy) ·
[Volatility Trading Strategies, "Is SVXY broken?"](https://www.volatilitytradingstrategies.com/blog/is-svxy-broken-should-short-vol-traders-be-worried)

---

## 4. Commodity ETF contango decay — USO, UNG

### 4.1 The decay is real and very large

- **UNG has underperformed the front-month natural gas contract by approximately 23.1% per year
  since its April 2007 inception — roughly −1.9%/month.** Over the last ten years UNG has lost
  roughly 89–92% of its value. Expense ratio 1.24% on top.
- The mechanism is identical to VXX's: a monthly forward roll in a persistently contangoed curve
  forces the fund to sell the cheap expiring contract and buy the expensive next one.
- **BOIL (2x natural gas) is down 99.45% over five years and ~99.98% over ten**, split-adjusted —
  contango plus `L(L−1)σ²/2` on a `σ` near 80–100%.
- Control comparison, which is the useful one: over the same ten-year window in which UNG lost ~89%,
  FCG (natural gas *producers*, no roll) **gained 66%.**

Sources:
[24/7 Wall St. on UNG contango](https://247wallst.com/investing/2026/05/28/ung-holds-front-month-natural-gas-futures-and-contango-has-cost-holders-90-percent-over-a-decade-without-a-single-price-drop/) ·
[24/7 Wall St. on BOIL](https://247wallst.com/investing/2026/05/25/boil-promises-2x-natural-gas-but-contango-has-eaten-99-percent-of-its-value-over-the-past-decade/) ·
[TheStreet, "Why UNG Is Worst Investment in the World"](https://www.thestreet.com/investing/why-ung-is-worst-investment-in-the-world-opinion-11407750) ·
[US News, natural gas ETF lessons](https://money.usnews.com/investing/articles/natural-gas-etfs-lessons-from-boil-and-ung-funds-in-2023)

### 4.2 And it is completely swamped by spot risk

This is the decisive fact and it is very easy to state:

> **UNG returned +35.76% in 2021 and +12.89% in 2022** — while decaying at ~23%/yr.

A short UNG position lost money in both of those years, badly, despite the structural drift being as
negative as anything in this document. Spot moves are 2–5x the size of the roll drag, on annual
horizons, routinely.

The single-day tail:

> **Natural gas futures closed +46% on 2022-01-27 — the largest one-day percentage rise on record**,
> with contracts surging over 70% in the final half hour of the prior session's expiry.
> [etf.com](https://www.etf.com/sections/features/natural-gas-surges-41-lifting-ung-and-boil) ·
> [Nasdaq, "Natural Gas ETFs Soar on Cold Weather, Short Squeeze"](https://www.nasdaq.com/articles/natural-gas-etfs-soar-on-cold-weather-short-squeeze)

And the physical-market tail behind it: during Winter Storm Uri, Henry Hub spot went **$3.76/MMBtu on
2021-02-10 to $23.86 on 2021-02-17**, with Oklahoma wholesale printing as high as **$1,250/MMBtu**
against ~$3 the week before.
[EIA](https://www.eia.gov/todayinenergy/detail.php?id=50778) ·
[Oklahoma Natural Gas](https://www.oklahomanaturalgas.com/blog/2021/ong/winter-storm-uri-faqs)

Borrow on USO and UNG is *cheap* — both are general collateral, low single digits or under 1%
(general collateral typically ~30 bp). **The market prices the borrow cheaply precisely because the
decay is not harvestable: spot dominates.** This is the arbitrage argument working correctly, in the
opposite direction from the one the brief anticipated. Cheap borrow is not an opportunity signal
here; it is the market telling us the drift is not separable from the risk.
[S3 Partners, US stock borrow fees](https://www.s3partners.com/articles/us-stock-borrow-fees) ·
[Verdad, "Costly Shorts"](https://verdadcap.com/archive/costly-shorts)

### 4.3 USO 2020 — and an urgent data-integrity finding for our fixture

What happened:

- WTI front-month settled at approximately **−$37 to −$40/bbl on 2020-04-20**, the first negative
  print in history.
- USO closed at **$2.13 on 2020-04-28, down over 60% from 2020-03-19.**
- **USO executed a 1-for-8 reverse share split after the close on 2020-04-28; post-split shares
  began trading 2020-04-29.** Shares outstanding went 1,482,900,000 → 185,362,500. NAV/share went
  **$2.04 → $16.35**.
- USCF rewrote USO's holdings repeatedly during April 2020, moving the fund out of the front month
  and across the curve, "until it was fundamentally different from the strategy detailed in its
  offering's registration statement." **The SEC opened an investigation.**

Sources:
[USO Form 10-K FY2020, SEC EDGAR](https://www.sec.gov/Archives/edgar/data/1327068/000110465921029202/uso-20201231x10k.htm) ·
[USO Form 8-K, reverse split](https://www.sec.gov/Archives/edgar/data/1327068/000117120020000271/i20263_ex99-1.htm) ·
[USCF press release, 1-for-8 reverse split](https://www.prnewswire.com/news-releases/uscf-announces-one-for-eight-reverse-share-split-for-the-united-states-oil-fund-nyse-arca-uso-301045001.html) ·
[TheStreet, SEC investigation](https://www.thestreet.com/etffocus/market-intelligence/uso-being-investigated-by-sec-for-changes-made-during-oil-crash)

**Now the finding that matters for us.**

The brief notes our fixture contains a **+733% single bar** on USO/UNG. A 1-for-8 reverse split
produces exactly a **+700%** bar in an unadjusted price series. Combined with a same-day price move
of a few percent, +733% is within a hair of the arithmetic.

> **I assess with high confidence that the +733% bar is the USO 2020-04-29 reverse split appearing in
> an unadjusted price series, not a market move.**

This needs verification before anything else here is acted on, because if true:

1. Our USO/UNG price series is **not split-adjusted**.
2. UNG has had **multiple 1-for-4 reverse splits** (each a +300% phantom bar) in addition.
3. **Every backtest result our framework has produced that touched USO or UNG is contaminated**, in
   both directions: phantom gains for longs, phantom catastrophic losses for shorts, and corrupted
   volatility/correlation estimates for anything computed cross-sectionally over a universe
   containing them.
4. It also implies our adjustment pipeline may not be handling reverse splits generally. Forward
   splits are common and well-tested; reverse splits are rarer and are exactly where such pipelines
   break.

Suggested check (not run here, as instructed): locate the +733% bar's date. If it is 2020-04-29,
the diagnosis is confirmed. Then scan for bars near +300% in UNG and near +300%/+400% in VXX (eight
1-for-4s) — VXX would show the same pathology and would silently poison any volatility-related work.

**This is arguably the highest-value item in this document, because it is a correctness bug rather
than a strategy idea.**

---

## 5. Other structural-negative-drift candidates

Surveyed; none reaches the bar. Recorded for completeness so the stream is not re-opened.

**Plain inverse (−1x) ETFs: SH, PSQ, DOG, RWM.** These have genuinely negative expected drift on two
counts: they fight the +8.59% equity premium *and* they carry `L(L−1)σ²/2 = σ²` of decay (§1.1). SH
is therefore a legitimately negative-drift instrument. But shorting SH is just being long the S&P
with extra steps and a borrow fee — it produces no new edge, only a worse implementation of a long.
Rejected as circular.

**Currency-hedged equity ETFs (HEDJ, DXJ, HEFA).** The hedge is rolled monthly in FX forwards and
costs the interest-rate differential. When USD rates exceed foreign rates the carry is *positive*
for a USD investor, not negative — the sign flips with the rate cycle and is not a structural drift.
There is a persistent cost from bid/offer on the forward roll but it is on the order of 10–30 bp/yr,
far below any borrow cost. Rejected: edge too small.
[Fidelity, currency ETFs](https://www.fidelity.com/learning-center/investment-products/etf/using-etfs-invest-currencies) ·
[etfdb currency-hedged list](https://etfdb.com/etfs/investment-style/currency-hedged/)

**High-fee thematic ETFs.** Expense ratios of 0.75–1.00% are a real negative drift relative to the
benchmark, but they are dwarfed by the +8.59% beta you take on by shorting the fund, and by tracking
dispersion. To isolate the fee you would need to short the fund and buy the basket, at which point
you are running a replication trade for ~50 bp gross against ~1–2% borrow on a thematic fund.
Rejected: negative after borrow.

**Closed-end funds.** Discount/premium dynamics are a genuine documented anomaly, but the tradeable
version is *buying* discounted CEFs, not shorting. Shorting premium CEFs runs into: tiny float,
punitive borrow (frequently 20%+ on the persistently-overpriced names, which is exactly the
arbitrage argument working), high distribution yields payable by the short, and no reliable
convergence date. Rejected: the borrow market has clearly priced this one.

**Leveraged single-stock ETFs (MSTU/MSTZ, TSLL/TSLQ, NVDL).** Highest decay coefficients available
(`σ` of 60–120%, `L(L−1)/2 = 1` for 2x → 40–140%/yr of drag). But: §2.2 applies identically to the
pair short; borrow on the popular ones is punitive and volatile; and the Elm Wealth analysis of the
MSTU/MSTZ case is instructive — a Sept 2024 to Mar 2025 backtest showed 38% returns that came
**not from volatility drag but from the funds failing to deliver their stated 2x daily exposure**,
i.e. from issuer operational failure, which is neither forecastable nor persistent. Rejected.
[Elm Wealth](https://elmwealth.com/double-short-etf/)

---

## 6. The generalisable finding

Stepping back from the individual instruments, the research produces one insight that applies to the
whole shorts programme and is worth stating separately:

**Every instrument with reliably negative expected drift has that drift because it is an insurance
premium, and the premium is paid to whoever bears crash risk.**

- VXX decays because VIX futures are in contango, and VIX futures are in contango because holders
  are paying for crash protection.
- UNG decays because the natural gas curve is in contango, and it is in contango because consumers
  are paying for supply-shock protection.
- Leveraged ETFs decay because of rebalancing convexity, and that decay is not transferable at all.

Shorting the first two means **selling crash insurance**. The resulting position is:

- **Positively correlated with our existing long book**, not negatively. It loses when we lose,
  hardest, in the same weeks. It is not a hedge; it is leverage.
- **Sized down by margin rules and by ruin constraints to a few percent of book**, so `exposure` is
  tiny even where `edge` is large.
- **Exposed to instrument-level termination risk** that no equity short carries: XIV terminated,
  SVXY re-levered overnight, VXX issuance suspended, USO's holdings rewritten mid-crisis under SEC
  scrutiny.

The premise of the stream — "find a negative-drift instrument so the short is not fighting the
equity premium" — turns out to be self-defeating. **The negative drift *is* a risk premium, and
short-selling it puts us on the same side of the same trade we already hold.** There is no instrument
that has negative expected drift *and* is uncorrelated with equities *and* is large enough to size.
If there were, it would be the best trade in finance.

The 8.59% overnight drift is not an obstacle that a cleverer instrument routes around. It is the
compensation for bearing equity risk, and any negative-drift instrument is simply the same
compensation with the sign flipped and a fatter tail attached.

---

## 7. Ranking of candidates

Net rate is on *book*, after borrow, at a sizing that survives the stated tail. Tail is the worst
historical adverse move for the short side.

| Rank | Trade | Decay (gross, on notional) | Borrow | Max sizing | **Net on book** | Worst historical tail |
|---|---|---|---|---|---|---|
| 1 | **Short VXX** | ~50%/yr | 3.05% | ~5% | **≈ +2.35%/yr** | UVXY +550% (Aug 2011); 1.5x UVXY +10x (Feb–Mar 2020); VIX +115.6% in one day (2018-02-05). Borrow reprices to 10–50% during the event. |
| 2 | **Short UVXY** | ~60%+/yr | 3.34% | ~3% | **≈ +1.7%/yr** | As above but 1.5x levered. Realistically unholdable through a spike; margin expands as you lose. |
| 3 | **Short UNG** | ~23%/yr vs front month | ~GC, <1% | ~5% | **≈ +1.1%/yr, but negative in realised terms** | +46% in a single day (2022-01-27, record). UNG **+35.76% in 2021, +12.89% in 2022** — short lost in both years despite full decay running. |
| 4 | **Short USO** | contango-dependent, not persistent | ~GC | — | **negative** | −$37/bbl WTI (2020-04-20); 1-for-8 reverse split; **issuer rewrote the fund's holdings mid-position; SEC investigation.** Uninsurable — the instrument's rules changed while the trade was open. |
| 5 | **Short TQQQ + SQQQ pair, daily rebalanced** | **0.00%** (§2.2) | 1.86% avg | ~55% gross (90% margin) | **≈ −3.1%/yr** | Not a tail problem, a mean problem. Expected return is zero by construction; costs are certain. |
| 6 | **Short TQQQ + SQQQ pair, monthly rebalanced** | mean-reversion payoff, not decay | 1.86% | ~55% gross | **indeterminate; regime-dependent** | −$11,059 on $200k gross in one month (−5.5%) in a sample *ending Jan 2020*, i.e. excluding COVID. Kinlay reports drawdowns to 75% under realistic borrow. |
| 7 | Short SOXL+SOXS / LABU+LABD | 0.00% (same argument, higher `σ`) | high & volatile | small | **negative** | Higher `σ` means the *unrebalanced* version has proportionally larger trend losses, not larger decay gains. |
| 8 | CEFs / currency-hedged / high-fee thematics | 0.1–1%/yr | 1–20%+ | — | **negative** | Rejected in §5; borrow clearly prices these. |

### Which I would actually pursue

**None as a short strategy.**

The only candidate with a defensible positive net expectation is **short VXX at ~2.35%/yr on book**,
and I would not pursue it, for three reasons that I think are individually sufficient:

1. It fails the diversification test that motivated the shorts programme (§6). It is long-beta in
   disguise and it loses in the same weeks the long book loses.
2. 2.35%/yr on book is below what we would need to justify carrying a position with a demonstrated
   ability to lose 20% of book in a month and a documented instance of an entire competing fund
   going to zero in 50 minutes.
3. It is the most crowded trade in retail finance. There is no reason to believe we have an edge in
   it over the many dedicated short-vol funds, several of which have been destroyed.

**What I would pursue instead, from this research:**

- **Immediately: verify the +733% bar (§4.3).** If it is the USO reverse split, we have a
  reverse-split handling bug in the adjustment pipeline that silently corrupts USO, UNG, VXX, UVXY,
  and any other repeatedly-reverse-split instrument in the universe. That is a correctness fix with
  retroactive consequences for prior results, and it costs an afternoon.
- **Optionally: re-file the unrebalanced leveraged pair as what it actually is** — a mean-reversion
  signal on the underlying index (§2.2). If we believe QQQ has negative daily autocorrelation in
  some regime, we can test that directly on QQQ at 1.85 bp with no borrow, no 90% margin, and no
  recall risk. The leveraged ETFs add nothing but cost and leverage to that hypothesis. This is a
  reframing, not an endorsement — the signal should be tested on its own merits.

### Where the brief's prior was right and wrong

- **Right:** borrow cost is usually the whole game, and it does kill the CEF, thematic, and
  single-stock-LETF versions cleanly.
- **Wrong for the specific case flagged:** borrow does *not* kill the VXX trade — 3.05% against
  ~50% decay is nowhere near a fair price for the decay. The arbitrage argument fails there because
  the constraint is margin, ruin, and issuer termination risk rather than share supply.
- **Wrong about the mechanism for the leveraged pair:** it is not that the fee eats the decay. It is
  that **there is no decay to eat.** The trade's expected value is zero before any fee is charged.
  Anyone reporting positive backtested returns for it is reporting a mean-reversion result and
  mislabelling it.

---

## 8. Source list

**Academic and regulatory**
- [Tsalikis & Papadopoulos, "Can shorting leveraged ETF pairs be a profitable trade?", J. Investment Strategies](https://www.risk.net/journal-of-investment-strategies/6983576/can-shorting-leveraged-exchange-traded-fund-pairs-be-a-profitable-trade) (paywalled; abstract read)
- [Khadivar, Nikbakht & Walker, "Investigating Long-Term Short Pairing Strategies for Leveraged ETFs Using Machine Learning", SSRN 4405467](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4405467)
- [Nikbakht MSc thesis, Concordia (full text)](https://spectrum.library.concordia.ca/988717/1/Nikbakht_MSc_F2021.pdf) (PDF did not text-extract; listed for manual follow-up)
- [Lin, Lin, Wang & Yeh, "Volatility Decay and Arbitrage in Leveraged ETFs", SSRN 5421274](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5421274)
- [Balter, Garcia & Schweizer, Netspar](https://www.netspar.nl/wp-content/uploads/paper_Balter_Garcia_Schweizer.pdf)
- ["Investment performance of shorted leveraged ETF pairs", EFMA 2013](https://www.efmaefm.org/0efmameetings/efma%20annual%20meetings/2013-Reading/papers/EFMA2013_0539_fullpaper.pdf) (TLS cert error on fetch; listed for manual follow-up)
- [FINRA Regulatory Notice 09-53](https://www.finra.org/rules-guidance/notices/09-53)
- [FINRA non-traditional ETF margin notice](https://www.finra.org/sites/default/files/NoticeDocument/p119906.pdf)
- [SEC DERA, "Demystify the Surge in VIX" (2025)](https://www.sec.gov/files/dera-vix-working-paper-2504.pdf)
- [BIS Bulletin 95, "Anatomy of the VIX spike in August 2024"](https://www.bis.org/publ/bisbull95.pdf)
- [AMF France, "Heightened volatility in early February 2018: the impact of VIX products"](https://www.amf-france.org/sites/institutionnel/files/contenu_simple/lettre_ou_cahier/risques_tendances/Heightened%20volatility%20in%20early%20February%202018%20the%20impact%20of%20VIX%20products.pdf)
- [Cboe, "After the Volpocalypse"](https://cdn.cboe.com/resources/education/research_publications/after-the-volpocalypse-market-observation.pdf)

**SEC filings**
- [USO Form 10-K FY2020](https://www.sec.gov/Archives/edgar/data/1327068/000110465921029202/uso-20201231x10k.htm)
- [USO Form 8-K, reverse split announcement](https://www.sec.gov/Archives/edgar/data/1327068/000117120020000271/i20263_ex99-1.htm)
- [USO Form 10-Q Q1 2020](https://www.sec.gov/Archives/edgar/data/1327068/000110465920058624/uso-20200331x10q.htm)

**Borrow-rate data (IBKR-sourced, sampled 2026-08-28)**
- [TQQQ](https://chartexchange.com/symbol/nasdaq-tqqq/borrow-fee/) · [SQQQ](https://chartexchange.com/symbol/nasdaq-sqqq/borrow-fee/) · [VXX](https://chartexchange.com/symbol/bats-vxx/borrow-fee/) · [UVXY](https://chartexchange.com/symbol/bats-uvxy/borrow-fee/)
- [IBKR short sale cost methodology](https://www.interactivebrokers.com/en/pricing/short-sale-cost.php)
- [IBKR Campus, "The Risks of Shorting, Part II: Borrow Fees"](https://www.interactivebrokers.com/campus/traders-insight/securities/short-selling/the-risks-of-shorting-series-part-ii-borrow-fees/)
- [S3 Partners, US stock borrow fees](https://www.s3partners.com/articles/us-stock-borrow-fees)
- [S3 Partners, "VXX Sales Suspended"](https://www.s3partners.com/articles/vxx-short-selling)
- [Verdad, "Costly Shorts"](https://verdadcap.com/archive/costly-shorts)

**Practitioner (flagged as such — used where no academic source exists)**
- [Elm Wealth, "Inverse-Double-Short-Leveraged ETFs Have Arrived"](https://elmwealth.com/double-short-etf/) — source of the zero-expected-return argument
- [Kinlay, "Investing in Leveraged ETFs — Theory and Practice"](https://jonathankinlay.com/2018/11/investing-leveraged-etfs-theory-practice/)
- [CXO Advisory, "Update on Shorting Leveraged ETF Pairs"](https://www.cxoadvisory.com/short-selling/leveraged-etf-pair-shorting-strategies/)
- [CXO Advisory, "Monthly Rebalanced Shorting of Leveraged ETF Pairs"](https://www.cxoadvisory.com/volatility-effects/monthly-rebalanced-shorting-of-leveraged-etf-pairs/)
- [Six Figure Investing, "Is Shorting UVXY, TVIX, VXX the Perfect Trade?"](https://www.sixfigureinvesting.com/2016/10/is-shorting-uvxy-tvix-vxx-the-perfect-trade/)
- [Six Figure Investing, "What Caused Volmageddon"](https://www.sixfigureinvesting.com/2019/02/what-caused-the-february-5th-2018-volatility-spike-xiv-termination/)
- [Six Figure Investing, VXX reverse splits](https://www.sixfigureinvesting.com/2013/08/next-vxx-reverse-split/)
- [Houndstooth Capital, "Anatomy of a Blowup"](https://houndstoothcapital.com/2018/05/06/anatomy_of_a_blowup/)
- [Volatility Trading Strategies, "Is SVXY broken?"](https://www.volatilitytradingstrategies.com/blog/is-svxy-broken-should-short-vol-traders-be-worried)
- [24/7 Wall St., UNG contango](https://247wallst.com/investing/2026/05/28/ung-holds-front-month-natural-gas-futures-and-contango-has-cost-holders-90-percent-over-a-decade-without-a-single-price-drop/) · [BOIL](https://247wallst.com/investing/2026/05/25/boil-promises-2x-natural-gas-but-contango-has-eaten-99-percent-of-its-value-over-the-past-decade/)
- [etf.com, "Natural Gas Surges 41%"](https://www.etf.com/sections/features/natural-gas-surges-41-lifting-ung-and-boil)
- [PortfoliosLab SVXY](https://portfolioslab.com/symbol/SVXY) · [Composer SVIX](https://www.composer.trade/etf/SVIX)

---

## 9. Caveats on this research

- **Borrow rates are a single snapshot** (2026-08-28, 13:18 EDT, IBKR via ChartExchange). Borrow on
  these names is highly time-varying and reprices adversely during stress. Historical borrow time
  series are behind paywalls; the calm-market numbers here understate realised cost.
- **Two primary sources could not be read**: the EFMA 2013 paper (TLS certificate failure) and the
  Concordia thesis (PDF did not text-extract). Both are listed in §8 for manual follow-up. Neither
  is load-bearing for the §2.2 conclusion, which is analytical rather than empirical.
- **The "4.90% → 0.27% after fees" figure is unverified** against the primary source; see §2.1.
- **The +733% bar diagnosis in §4.3 is an inference**, not a measurement. It matches a 1-for-8
  reverse split to within a fraction of a percent, but it must be confirmed against our fixture's
  actual bar date. No backtests were run and no repo files other than this one were touched.
- SVXY's reported −95.2% max drawdown and SVIX's −79.3% come from data aggregators, not from issuer
  filings; treat as approximately correct.
