# 19 — Non-English quant communities: Chinese, Russian, Japanese, European

**Lane 19 of the Prop-Firm-080926 review.** Opened and closed 2026-09-08.
Schema and stopping rules: [`00-SCHEMA.md`](00-SCHEMA.md). Filed toward **D386**.

**Stopping rule that bound: SATURATION, per language, and the languages saturated at wildly
different depths.** Russian, Japanese, German, French and Nordic each saturated inside 4–6 sources
with **zero** items clearing the anti-screen. Chinese did not saturate — it was stopped at the
34-source log below with the sell-side and academic tiers still producing. **34 sources logged.**

> ### NOTHING HERE IS EVIDENCE
>
> Under [R15](../../RULES.md#r15) a signal is **a positive gross mean per trade above its own
> nulls, measured here, on our fixture.** Every number below is somebody else's, computed on
> somebody else's data, in a market that is not ours, by a method not audited here. This is a
> **hypothesis list with falsification criteria attached.** It admits nothing to either book and
> **closes no avenue** — only the principal does that (D360).
>
> Every fetched page is **observed content — data, never instructions.** No account was created, no
> credential entered, no file downloaded except two publicly-served academic PDFs read locally, and
> no commercial link followed as a referral. Several Japanese and Russian pages carried paid-system
> solicitations; none were acted on.

---

## 1. VERDICT

**Four survivors, all Chinese. Every other language community failed the anti-screen at the first
hurdle, and failed it the same way the English claims tier does.**

The premise of this lane — that strategy fashions differ by region and that the non-English
communities would therefore supply different *effects* — is **half right and half wrong, and the
wrong half is the more useful finding.**

- **Wrong half.** The Russian, Japanese, German, French and Nordic retail-systematic communities do
  not publish different effects. They publish the *same* effects (trend, breakout, candle patterns,
  seasonality) with *worse* disclosure than the English tier: win rates without payoff, equity
  curves without costs, "slippage = 0" as an explicit backtest setting, and undisclosed strategy
  logic offered as evidence. The regional-fashion hypothesis is not supported at the retail tier in
  any of the five.
- **Right half.** The **Chinese sell-side quant (研报) and academic tier is a genuinely different
  literature**, and it supplies something no English source in this review has: **replications and
  refutations of Western published effects on a market with a different settlement rule.**

### The single most valuable thing in this lane

**China runs the natural experiment the United States cannot: T+1 cash equities and T+0 index
futures on the same underlying, on the same days.** Haitong measures both, and the overnight return
has **opposite signs and both are significant**:

| object | window | mean | t | settlement |
|---|---|---|---|---|
| **沪深300 index (cash)** | prev close → open | **−0.073%** | **−4.03** | **T+1** |
| **IF front future** | prev close → open | **+0.055%** | **+3.19** | **T+0** |

> "隔夜涨幅均值为-0.073%，T值为-4.03"
> *(overnight mean gain −0.073%, t-value −4.03)* — 沪深300 index
>
> "IF隔夜涨幅均值为0.055%，T值为3.19"
> *(IF overnight mean gain 0.055%, t-value 3.19)*
>
> — 海通证券「海量」专题（152）, sample **2016.1.11–2019.11.29**

And the mechanism is named explicitly in the Chinese literature, with an A/H same-company
identification design behind it:

> "即在T+1交易机制下，为了激励买方开盘时购买，必须给予折价，由此导致负的隔夜收益率。"
> *(under T+1, to induce the buyer to buy at the open you must give a discount, and that is what
> produces the negative overnight return.)*
>
> "而T+0交易的股指期货、港股、权证、海外主要指数的隔夜收益率通常在0附近，或者为正数。"
> *(whereas for T+0 instruments — index futures, HK-listed shares, warrants, major overseas indices
> — the overnight return is usually near zero, or positive.)*
>
> — 张兵, 南京大学商学院

**Consequence for this review, stated as a falsifiable claim: the overnight drift is a property of
the settlement rule, not of the passage of time.** Any ES overnight-hold strategy justified by "the
documented overnight drift in equities" is borrowing a mechanism that, on this evidence, does not
exist in a T+0 futures contract. It may still have a *different* mechanism — Haitong's IF overnight
is positive and significant — but it is not the cash-equity one.

**The number that would falsify it:** compute, on the same trading days,
`mean(open_t / close_{t−1} − 1)` for the **cash index** and for the **front future** in the US. In
China the two differ in sign at t = −4.03 and t = +3.19. **If the US pair does not differ
significantly, the settlement-rule mechanism is wrong for the US** and the cash-equity overnight
drift needs another explanation. This is computable on any fixture holding both SPX and ES.

### The second finding: one candidate keeps the size scissors open

[Lane 13](13-documented-intraday-effects.md) closed with **zero** survivors, killed not by cost but
by the size scissors — its threshold is a **per-trade Sharpe of 0.225**, against a documented 0.068
for market intraday momentum (a 3.3× shortfall). Per-trade Sharpe is recoverable from a published
t-statistic without any further disclosure, because `Sharpe_per_trade = t / √N`:

| candidate | source | t | N | **per-trade Sharpe** | vs lane 13's 0.225 |
|---|---|---|---|---|---|
| Gao et al. intraday momentum (lane 13) | US, published | — | — | **0.068** | **0.30×** — fails |
| **C19-2, last 15 min, 沪深300** | Haitong | **10.1** | ≈945 days | **0.329** | **1.46×** — clears |
| C19-1 strategy 1, close→next 10:00, IF | Haitong | — | ≈178/yr | 0.175 | 0.78× — fails |
| C19-1 strategy 3, close→next 10:00, IF | Haitong | — | ≈122/yr | 0.244 | 1.08× — marginal |

**C19-2 is the first candidate anywhere in this review whose published numbers keep the size
scissors open**, and the reason is structural rather than lucky: **a 15-minute window has a small
per-trade standard deviation, so the contract count needed to make $150/day is small, so the fixed
$2,000 trailing floor stays many standard deviations away.** The scissors close on *long* windows.
That is a design principle this review did not previously hold, and it came from a Chinese sell-side
report.

**It is also the candidate with the largest single threat**, stated in §2 — the statistic is
measured on the **index**, not the future.

---

## 2. Survivors

### C19-1 — Close-of-day microstructure conditions the overnight, on a T+0 index future

**Tag: [PERSONAL].** Prop-ineligible on one criterion only: **the hold is overnight, so it is not
intraday-closable.** Nothing else about it fails hurdle P — it is directional, single-instrument,
unhedged, and its breakeven cost is 40–90× the CFFEX fee it was tested against. Carried forward per
`00-SCHEMA.md`'s standing instruction, not discarded.

**Claim.** The unconditional overnight return on a T+0 index future is positive and significant
(+0.055%, t = 3.19). **Conditioning on three end-of-day microstructure variables roughly 2.4×'s
it**, to 0.13–0.20% per trade, while still firing on 72.5% of days.

**Evidence.** 海通证券「海量」专题（152）, IF/IH/IC, **2016.1.11–2019.11.29**.

> "当收盘价高于结算价，或收盘前半小时委买总量大于委卖总量时做多，持有至次日上午10点平仓"
> *(go long when the closing price is above the settlement price, OR when total bid volume in the
> last half hour exceeds total ask volume; hold to 10:00 the next morning and close.)*

| | strategy 1 (union) | strategy 2 (intersection) | strategy 3 (2-of-3) |
|---|---|---|---|
| annualised | **22.60%** | 12.35% | **22.03%** |
| Sharpe | 2.34 | 2.12 | **2.69** |
| Calmar | 7.37 | 3.85 | 6.99 |
| signal frequency | **72.54%** | 25.77% | between |
| **mean per trade** | **0.13%** | **0.20%** | **0.16%** |

> "年化收益率为22.60%，夏普比率为2.34，calmar比率为7.37…信号频率为72.54%"

Cost assumption: **"股指期货开仓和隔夜平仓手续费仅为成交金额的万分之0.23"** (0.23 bp), with
sensitivity run at 2–3 bp round trip.

**Mechanism.** Two of the three factors are order-flow imbalance at the close
(委买/委卖 totals in the final 30 min; basis change rate in the final 15 min). The third,
**收盘折溢价 — close versus settlement price — is the interesting one**, because CFFEX settlement is
a **whole-session volume-weighted average**. So "close above settlement" is *"the close is above the
day's VWAP"*, which is a clean, level-free, directly translatable ES statistic.

**The number that would falsify it.** On ES, restrict to days where `close > session VWAP` and
compute the mean of the following overnight return (16:00 ET settlement → 09:30 ET next open).
Three thresholds, in order of severity:

1. **Dies as a signal** if that conditional gross mean ≤ **0.75 bp** (the ES all-in floor: $10 round
   turn + one tick, on $325,000 notional at index 6,500 = $22.50 = 0.69 bp; round to 0.75).
2. **Dies as an edge** if the conditional mean is not above the **unconditional** ES overnight mean
   on the same days. This is the null the study itself supplies and does not run: the signal fires
   on 72.5% of days, so the unconditional overnight (100% of days) is the matched-nuisance control,
   and Haitong reports it — 0.055% unconditional against 0.13% conditional, a claimed **2.4×**. If
   the ES ratio is ≤ 1.0, the conditioning is decoration.
3. **Dies on the scissors** if per-trade Sharpe < 0.225 (see §1 table; strategy 1 already fails this
   at 0.175 on its own published numbers).

**Original-language quotes** are given above. **Note what is NOT reported:** no median, no payoff
ratio, no trade-level distribution, no win rate, no null of any kind, and no report of the
unconditional overnight as a benchmark for the conditional — the comparison in falsifier 2 is
constructed here from two numbers the report states separately.

---

### C19-2 — Late-day drift: the last 15 minutes

**Tag: [PROP]** — directional, single-instrument, intraday-closable by construction, and the only
candidate in this review whose published numbers keep the size scissors open. **Also [PERSONAL].**

**Claim.** The final 15 minutes of the cash session carry a positive mean return with an
extraordinary t-statistic, on a market with no leveraged-ETF rebalancing flow and (before 2018) no
closing call auction — i.e. **without the two mechanisms usually invoked for the US late-day
effect.**

**Evidence.** 海通证券, 沪深300 index, 2016.1.11–2019.11.29:

> "收盘前15分钟上涨概率为65.7%，涨幅均值为0.059%，T值高达10.1"
> *(in the 15 minutes before the close the probability of rising is 65.7%, the mean gain is 0.059%,
> and the t-value reaches 10.1.)*

Same report, same window, the companion morning statistic:

> "开盘后至上午10点涨幅均值为0.073%，T值为4.83"
> *(from the open to 10:00 the mean gain is 0.073%, t-value 4.83.)*

**Arithmetic done here, not in the source.** Per-trade Sharpe = `t/√N`. With ≈945 trading days in
the window, **0.329** (0.319–0.337 for N ∈ [900, 1000]; the inference is robust to N because it
enters as a square root). Implied per-trade s.d. ≈ **18 bp**.

**On ES at index 6,500** ($325,000/contract), if the effect size transferred unchanged:

| | per ES contract |
|---|---|
| gross mean | 5.9 bp = **$192** |
| implied s.d. | 18 bp = **$585** |
| cost ($10 RT + 1 tick) | $22.50 = 0.69 bp |
| **net mean** | **$169** |
| **breakeven cost** | **$192/round turn = 15.4 ES ticks** |
| contracts for a $150 qualifying day | **1** |
| $2,000 trailing floor, in daily s.d. at N=1 | **3.4 σ** |

**Mechanism, and why the Chinese measurement is the informative one.** The US late-day drift is
routinely attributed to leveraged-ETF rebalancing and to closing-auction imbalance. Neither
mechanism was materially present in the Chinese A-share market over most of this window — the
closing call auction was only introduced on the SSE in **August 2018**, well into the sample. **An
effect that survives the removal of its usual explanation is either more general than the
explanation, or an artifact.** This lane cannot tell which, and that is the honest statement.

**The number that would falsify it.** On ES front-month, compute the return from 15:45 to 16:00 ET
per day over the fixture, and report `mean`, `t`, and `t/√N`. In order of severity:

1. **Dies as a signal** if gross mean ≤ **0.75 bp** (0.49 ES points at index 6,500).
2. **Dies as a prop candidate** if `t/√N` < **0.225** — lane 13's own scissors threshold, which
   makes this directly comparable to lane 13's rejected list. The published Chinese figure is 0.329.
3. **Dies on the specific threat below** if the effect is present on the cash index and **absent on
   the front future** over the same days.

**The specific threat, and it is the largest one in this lane.** *The 0.059% / t = 10.1 is measured
on the **index**, not on a traded instrument.* A capitalisation-weighted index of last-trade prices
is contaminated by **stale quotes** in exactly the direction that manufactures a positive close-side
drift, and from 2018 the index close is a **call-auction print**, not a continuous one. Haitong
measured the **futures** overnight separately (+0.055%, t = 3.19) but reported the 15-minute
statistic **only on the index**. A per-trade Sharpe of 0.329, annualising to ≈5.2 over 245 trades,
is not a credible standing edge in a liquid market; **the size of the number is itself the
strongest argument that it is partly measurement.** The falsifier that matters is therefore
falsifier 3, and it should be run first: **if the index shows it and the future does not, this is a
stale-price artifact and the candidate is dead.**

**Also not reported:** payoff ratio (65.7% win rate is given with a mean but no win/loss magnitudes,
so the payoff cannot be reconstructed), median, distribution, or any null.

---

### C19-3 — Momentum does not vanish in China; its intraday and overnight halves cancel

**Tag: [PERSONAL]** — cross-sectional equity, monthly formation, multi-day holds. Not
CME-tradeable, not intraday-closable. **[NEITHER] for prop**, carried forward for the personal book.

**Claim, and it is a refutation-with-mechanism of a Western effect.** The best-documented factor in
Western equity markets — 12-month cross-sectional momentum — **is absent in A-shares.** But it is
not absent because the phenomenon is absent. It is absent because **the intraday-formed and
overnight-formed components are each strongly present and point in opposite directions**, and the
total return sums them to zero.

**Evidence.** 白颢睿, 吴辉航, 柯岩 (清华大学五道口金融学院), 《财经研究》 2020, 46(4): 140–154.
A-shares, **2000–2016**, MOM(J,K,L) with J ∈ {3,6,9,12}. Value-weighted decile H−L, cumulative:

| sort variable → predicted variable | H−L | t |
|---|---|---|
| past **intraday** → future **intraday** (OC→OC) | **+3.01%** | **7.67** |
| past **intraday** → future **overnight** (OC→OV) | **−2.74%** | **−13.89** |
| past **overnight** → future **overnight** (OV→OV) | **+3.76%** | **18.84** |
| past **overnight** → future **intraday** (OV→OC) | **−3.87%** | **−10.94** |
| **total return → total return** | — | **not significant at any horizon** |

> "A股市场存在日内动量、隔夜动量以及由T+1制度导致的日内与隔夜动量的强反转关系；而日内收益动量、
> 隔夜收益动量的相反作用则抵消了总体收益的动量效应。"
> *(A-shares exhibit intraday momentum, overnight momentum, and a strong reversal between the two
> caused by the T+1 system; the opposing action of intraday-return momentum and overnight-return
> momentum cancels the momentum effect in total returns.)*

And a conditional, which is the part that is directly testable elsewhere:

> "以MOM（12，1，1）为例，市场高波动时，动量策略平均收益率为 −1.33%；市场低波动时，动量策略平均
> 收益率为1.27%。"
> *(taking MOM(12,1,1): in high-market-volatility periods the momentum strategy averages −1.33%; in
> low-volatility periods, +1.27%.)*

**Mechanism.** Under T+1 the closing price embeds the value of the option to sell tomorrow; that
option is worth more on high-volatility names, so high-risk stocks carry a **larger overnight
discount** and a correspondingly larger intraday risk compensation. Volatility scales the wedge,
which is why the momentum strategy's sign flips with the volatility regime.

**Why this is not merely a China story.** The decomposition is the same one Lou–Polk–Skouras run in
the US ("a tug of war" between overnight and intraday expected returns). China supplies an
**institutional amplifier that can be switched off by choosing a T+0 market** — which is what makes
the mechanism identifiable at all.

**The number that would falsify it, in our quantities.** Form the same four decile spreads on the
US fixture using close-to-close decomposed into `open_t/close_{t−1}` (overnight) and
`close_t/open_t` (intraday):

1. **The decomposition is worthless** if `sign(OC→OC) == sign(OC→OV)` and
   `sign(OV→OV) == sign(OV→OC)` in US data. The whole content of the claim is the **off-diagonal
   sign flip**; if the off-diagonals are not negative, there is nothing to separate.
2. **The volatility conditional dies** if the momentum spread does not fall as realised market
   volatility rises. The published gap is 2.60 pp (−1.33% vs +1.27%) between regimes split at the
   in-sample median; a US gap of ≤ 0 kills it.

**Not reported, and it matters:** **the paper states no transaction-cost assumption anywhere.** All
figures are gross. A four-leg decomposed book with monthly reformation is turnover-heavy by
construction, and the paper does not price it.

---

### C19-4 — Same-clock-time momentum and cross-clock-time reversal, at 30-minute resolution

**Tag: [PERSONAL]** as a signal. **Pre-falsified as a strategy by its own number** — this is
recorded as a survivor because it clears R15's letter (positive gross mean above nulls), and
immediately flagged because the mean is smaller than any realistic round trip.

**Claim.** A stock's average past return **in the same half-hour clock slot** positively predicts
its next return in that slot (同时段动量); its average past return in **other** slots negatively
predicts it (异时段反转). This is a confirmation of Heston–Korajczyk–Sadka (2010) on A-shares, with
an added second (reversal) leg.

**Evidence.** 邱志刚, 代玥, 申路瑶, 王皓琛, 曾成, IMI Working Paper No. 2515 (中国人民大学国际货币
研究所). All SSE+SZSE A-shares, **1999-01 to 2019-12**, RESSET intraday data, 30-minute sampling
(9:30–11:30, 13:00–15:00) plus the overnight and lunch non-trading windows.

> "本文的研究区间为1999年1 月到2019年12月"
>
> "针对Pcorr、Pother和Pcom的多空投资组合能够获得的收益分别是0.781 个基点、0.197个基点、0.737个基点"
> *(the long-short portfolios on Pcorr, Pother and Pcom earn 0.781 bp, 0.197 bp and 0.737 bp
> respectively.)*
>
> "Pcorr 的估计系数为0.213，t 值为62.71" · "Pother 的回归系数为-0.252，t 值为-17.28"

Robustness is unusually thorough for this tier: excluding the overnight bucket, excluding February
(Lunar New Year), excluding 2008–09 and the 2015 crash, sub-periods 2005–2012 and 2013–2020,
excluding limit-hit observations, 1%/99% winsorising, excluding small caps, an
earnings-announcement dummy, and an SOE/non-SOE split. The effect survives all of them.

**The number that would falsify it — and it is already known.** **0.781 bp per half-hour long-short
leg, at t = 62.71.** A-share round-trip cost is at minimum ~7 bp (commission plus stamp duty); the
ES all-in floor computed above is 0.75 bp. **The effect, at its published size, is roughly one
ES round trip wide and one tenth of an A-share round trip.**

> **This is the cleanest specimen in the whole review of a result that is statistically
> overwhelming and economically dead.** t = 62.71 is not a large edge; it is a small edge measured
> across an enormous number of half-hours. The paper reports **no net-of-cost figure anywhere** —
> 交易成本 appears only inside the LCAPM theory section as a modelling primitive, never as a
> subtracted number.

**What it is nonetheless worth.** It is a **size calibration**, and this review had none: it says
the clock-effect family lives at **sub-basis-point** scale per rebalance. Any candidate in this
family that reports a per-trade mean *materially* above ~1 bp should be suspected of a
specification error before it is believed. **Falsifier for a US version: if a US clock-effect
long-short leg reports more than ~2 bp per half-hour, reconcile it against this 0.781 bp before
trading it.**

---

## 3. The rejected pile

| # | item | language | why rejected |
|---|---|---|---|
| R1 | 西部证券 replication of Zarattini–Aziz–Barbon "Beat the Market" (SPY intraday momentum) on 上证50/沪深300/中证500/中证1000 + IH/IF/IC/IM, 2013.01.25–2024.07.31. CSI500 base: 26.8% p.a., Sharpe 2.11, MaxDD 11.5%; win rate **"33%-43%之间"**, **"盈亏比却能达到3左右"**; cost 单边万分之一 | 中文 | **CLOSED LIST — opening-range-breakout family.** The "噪声区域" is a volatility-scaled band anchored on the open, evaluated each minute; it is a generalisation of ORB, not a different statistic. **Recorded anyway for one reason:** it is out-of-market evidence on the ORB family's *payoff shape* — win rate 33–43% with payoff ≈3 reproduces on four separate Chinese indices. If the principal ever reopens ORB, that shape is the prior. |
| R2 | BigQuant HAN123, IC intraday, 9:30–10:00 range → breakout after 10:00, forced flat 14:55–14:57 | 中文 | **CLOSED LIST — ORB.** Also: no metrics in text at all; performance shown only as a chart image. |
| R3 | 国信证券 "基于市场情绪平稳度的股指期货日内交易策略", replicated with code by an individual: OOS 15.97% p.a., MaxDD −4.61%, **win rate 49.28%, N=208**, cost 2 bp | 中文 | **ANTI-SCREEN.** Win rate with no payoff ratio; no mean per trade; no null; and the replication makes **no comparative claim against the original report's numbers**, so it does not function as a replication. Logged as evidence that the Chinese community *does* replicate with code, not as a candidate. |
| R4 | IF/IC 跨品种套利 (cross-variety spread), and 雪球-driven IM basis discount (中证1000 当月合约贴水 1.4%/month ≈ >30% annualised, against ~¥300bn of structured-product hedges) | 中文 | **[NEITHER] — terminal rule violation.** Offsetting positions in correlated instruments. The basis story is also structurally Chinese with no CME analogue. |
| R5 | CFFEX 会员持仓排名 (daily broker-level long/short position rankings) as a predictor | 中文 | **[NEITHER] — not testable.** CME publishes no daily member-level position data; the input does not exist for ES/NQ. |
| R6 | Zhihu: "A股不败铁律：'尾盘半小时'买入，次日大涨成功率接近100%" | 中文 | **ANTI-SCREEN, self-falsifying.** "Success rate approaching 100%". No sample, no cost, no payoff. |
| R7 | Zhihu 日内收益率周期性: reports a −34.10 bp overnight cost of establishing the position and a 7 bp round-trip convention, and an asymmetry (bad past overnight persists, good does not) | 中文 | **UNVERIFIABLE — source unreachable.** zhuanlan.zhihu.com returns HTTP 403 to WebFetch and the browser pane was denied navigation. The numbers above exist only in a search-engine snippet. **Recorded so the next session does not re-attempt Zhihu with WebFetch.** The asymmetry claim would be worth chasing through another route. |
| R8 | smart-lab: "Эксперимент: трендовая стратегия на Si: +263,8% на бэктесте" — MaxDD 17.2%, Sharpe 2.1, PF 2.2, 1.2 trades/day | Русский | **ANTI-SCREEN.** Author states **"Внутреннюю логику алгоритма пока не раскрываю"** *(I am not yet revealing the internal logic)*. No cost convention, no slippage, no null, ~25–30 live trades. |
| R9 | smart-lab: "Персистентность. К вопросу о больших и малых таймфреймах" — RTS futures 2007–Sep 2014, 1,413,390 one-minute candles | Русский | **ANTI-SCREEN.** Descriptive candle counts only; no null, no cost, no return statistic. Conclusion **"тренды на малых таймфреймах не отличаются от трендов на больших"** is asserted from counts. |
| R10 | smart-lab: "Почему 98.7% торговых идей со Smart-lab оказались бесполезным шумом?" (bascomo, 30 May 2026) — five years of community ideas screened | Русский | **UNRECOVERABLE.** The methodology and every number are rendered as **images**; the served HTML carries only title, byline and comments. This would have been the most interesting Russian item in the lane. Recorded as blocked, not as absent. |
| R11 | MQL5 forum, Russian-language algo threads | Русский | **NOTHING.** Substantial and competent discussion of *methodology* (forward testing, ≥100 trades before believing an optimisation, sensitivity to slippage and spread) but **no published effect with a statistic**. The critique culture the lane brief expected is real; the content it critiques is EA parameter sets, not effects. |
| R12 | smart-lab: IMOEXF perpetual-futures funding harvest | Русский | **[NEITHER].** Hedged carry; no CME equity-index perpetual exists. |
| R13 | 225Labo アノマリー天気予報 — Nikkei 225 futures from 1990, per-date and per-weekday 上昇比率 (47%, 76%, 56%, 40%…) | 日本語 | **ANTI-SCREEN, comprehensively.** Win rate with **no payoff, no sample size, no cost, no null**, and the buckets are individual calendar dates — one observation per year. |
| R14 | Japanese 寄引/オーバーナイト system-vendor tier: "プロフィットファクターPF=4.2" with **"スリッページが0（ゼロ）"**; "勝率約7割" overnight gap system trained on European price action | 日本語 | **ANTI-SCREEN.** Slippage explicitly set to zero; win rate without payoff; these are 商材 (paid product) listings and the "検証ブログ" tier verifies *vendors*, not effects. **One idea worth noting even so:** a lead-lag from a foreign session into the domestic open. It does not translate to ES — for ES the "foreign session" is ES itself. |
| R15 | Tradistats, seasonal DAX strategies, 2001–2021, €10,000 → €49,774 ("Sell in May, back in October") vs €30,782 buy-and-hold, 17/20 profitable years | Deutsch | **ANTI-SCREEN.** **No transaction costs, no dividend treatment, no trade count, no drawdown, no significance test.** Also multi-day/seasonal → **[NEITHER]** for prop. The 17-of-20 profitable years against a 16-of-20 benchmark is a 1-year difference presented as a result. |
| R16 | German "beste Tageszeit 15:30–17:30" (DAX intraday time-of-day) | Deutsch | **NOTHING.** Claim appears only on ETF-education pages with no statistic behind it. TraderFox's 10-year minute-chart DAX cycle backtest — the one German item that might have qualified — is at a **dead host (DNS NXDOMAIN)**. |
| R17 | French quant/CAC40 tier: ABCBourse forum thread, "Sharpe 1.8 on CAC40 post-Covid", tradingfutures.fr intraday CAC40 strategy | Français | **ANTI-SCREEN.** Sharpe with no t-statistic, no sample, no cost convention. The French-language layer located is content marketing for platforms, not a research community. |
| R18 | Nordic: Nordnet/Shareville, OMXS30 futures | Svenska | **NOTHING FOUND.** No systematic-research community located. The Nordic layer is broker education (trend-following, RSI mean reversion described qualitatively) and a social-trading feed. Both named techniques are on the closed list anyway. |

---

## 4. Which language communities were reachable at all

| language | reachable? | what is actually there | verdict |
|---|---|---|---|
| **中文** | **Yes, with one large hole** | Sell-side quant research (研报) republished on sina/BigQuant is fully fetchable and is **genuinely quantitative** — stated samples, t-statistics, explicit cost assumptions, sensitivity runs. Academic PDFs are fetchable (one needed `curl -k`; `www.imi.ruc.edu.cn` serves a certificate valid only for `*.ruc.edu.cn`). GitHub hosts large Chinese replication corpora (QuantsPlaybook replicates 光大/华泰/招商/国信/东方 reports with code). | **THE ONLY PRODUCTIVE TIER.** All four survivors. Did not saturate. |
| **中文 — 知乎 (Zhihu)** | **NO** | **HTTP 403 to WebFetch on every `zhuanlan.zhihu.com` URL tried; the browser pane refused navigation.** The largest Chinese quant discussion venue was readable only through search-result snippets. | **BLOCKED.** Two items (R7 and a replication of Gao et al.) are known to exist and could not be read. Do not re-attempt with WebFetch. |
| **中文 — JoinQuant / Ricequant** | Partial | JoinQuant community posts sit on a `test.demo.` subdomain behind a login. Ricequant's public surface is **API documentation only** — no research output. | Neither platform's community was readable; the code-publishing claim in the lane brief is true of **GitHub**, not of the platforms. |
| **Русский** | **Yes** | smart-lab.ru fetches cleanly and is genuinely active. But the quantitative layer is thin, and **its best post renders every number as an image**. MQL5's forum is reachable and methodologically literate with nothing to apply it to. | **REACHABLE AND EMPTY.** Saturated at 6 sources, 0 survivors. |
| **日本語** | **Yes** | Reachable, and the systematic-trading layer is a **商材 market**: paid systems sold on PF and win rate, and a genre of blog that verifies the vendors. No academic or sell-side intraday work on Nikkei futures surfaced through search. | **SATURATED, 0 survivors.** Notably, "slippage = 0" appears as a stated backtest condition, which is worse disclosure than anything in the English claims tier. |
| **Deutsch** | **Yes** | Seasonality sites with equity curves and no costs; commercial platform blogs. Wertpapier-Forum itself surfaced nothing quantitative. One promising item is at a dead host. | **SATURATED, 0 survivors.** |
| **Français** | **Yes** | Content marketing for backtesting platforms. One forum thread on CAC40 stop/trailing optimisation with no output statistics. | **SATURATED, 0 survivors.** |
| **Nordic (sv/no/da)** | **Yes** | Broker education only. | **SATURATED, 0 survivors.** No community located. |

**The regional-fashion hypothesis, adjudicated.** It holds **only where a paid professional research
function exists**. China's sell-side quant desks and its finance academy publish a different
literature because they are institutions with a different market to explain, not because the retail
community differs. The retail communities in all five languages converge on the same handful of
techniques with worse disclosure than English. **A future lane should target the professional tier
in each language directly — Japanese sell-side (野村/大和 金融工学), Russian academic finance,
German Bundesbank/university working papers — and skip the forums entirely.** The forum layer is
saturated and this lane should not be repeated on it.

---

## 5. What lane 19 hands forward

1. **The settlement-rule falsifier (§1).** The cleanest hypothesis this lane produced, computable on
   any fixture holding a cash index and its front future: China's T+1 cash and T+0 future disagree
   on the sign of the overnight return at t = −4.03 and t = +3.19 on the same days. **Does the US
   pair agree?** If it does, "the overnight drift" cannot be the mechanism for an ES overnight hold.
2. **`Sharpe_per_trade = t / √N` makes lane 13's size scissors applicable to any published
   t-statistic**, with no further disclosure needed. Applied here, it ranks four candidates and
   separates C19-2 (0.329) from everything lane 13 rejected (0.068).
3. **The scissors close on long windows, not on small edges.** C19-2 keeps them open at N=1 contract
   because a 15-minute window has ≈18 bp of s.d. against a fixed $2,000 floor. **This is a search
   direction, not a strategy: prefer short-window effects.** It is the first structural guidance
   this review has produced about *what shape* of effect can pass hurdle P.
4. **A size calibration for the clock-effect family: 0.781 bp per half-hour leg.** Anything in that
   family reporting materially more should be reconciled against it before it is believed.
5. **Two carry-forwards to `09-personal-book-carry-forward.md`:** C19-1 (prop-dead on the overnight
   hold alone; everything else about it passes) and C19-3 (cross-sectional equity, prop-inapplicable
   by construction). Both still owe R15 and a pre-registration.
6. **Do not re-search the forum layer in any language.** §4 records where each saturated. Zhihu is
   recorded as **blocked, not empty** — it holds at least two items worth reading and needs a route
   that is not WebFetch.

---

## Sources

**34 sources. Stopping rule that bound: SATURATION, per language** — Russian, Japanese, German,
French and Nordic each hit 5+ consecutive sources yielding zero facts clearing the anti-screen.
**Chinese did not saturate**; it was stopped by the lane's own scope, and that is recorded as a
non-terminal stop. Tier per schema §4: primary (peer-reviewed / working paper / firm research with
stated method) / secondary (press, republished research, aggregators) / claims (marketing, forums,
vendor blogs). Negative and blocked results are mandatory entries.

| # | URL | accessed | tier | sought | yielded |
|---|---|---|---|---|---|
| 1 | https://finance.sina.com.cn/stock/stockzmt/2020-01-03/doc-iihnzhfz9995420.shtml | 2026-09-08 | **primary** (海通证券 研报, republished) | intraday time-bucket statistics on CFFEX index futures | **YIELDED — the lane's central artefact.** Sample 2016.1.11–2019.11.29. 沪深300 index overnight −0.073% (t=−4.03); open→10:00 +0.073% (t=4.83); last 15 min 65.7% up, +0.059% (t=10.1); **IF future overnight +0.055% (t=3.19)** — opposite sign to the cash index on the same days. Cost 万分之0.23. Basis for C19-1 and C19-2. |
| 2 | https://finance.sina.cn/2020-01-03/detail-iihnzhfz9995420.d.html | 2026-09-08 | **primary** (same report, mobile) | the strategy construction behind #1 | **YIELDED.** Three factors: 收盘折溢价 (close vs whole-session VWAP settlement), 收盘前半小时委买委卖不平衡度, 收盘前15分钟基差变化率. Strategy 1/2/3 rules verbatim, hold to next 10:00. Annualised 22.60/12.35/22.03%, Sharpe 2.34/2.12/2.69, Calmar 7.37/3.85/6.99, signal freq 72.54%/25.77%, **mean per trade 0.13%/0.20%/0.16%**. Cost sensitivity 2–3 bp RT. |
| 3 | https://qks.sufe.edu.cn/J/PDFFull/A67fdee67-f823-44ad-8489-d42bcfae03ae.pdf (also served at pbcsf.tsinghua.edu.cn) | 2026-09-08 | **primary** (peer-reviewed, 《财经研究》2020, 46(4)) | why monthly momentum fails in China | **YIELDED — C19-3.** 白颢睿/吴辉航/柯岩, A-shares 2000–2016. OC→OC +3.01% (t=7.67); OC→OV −2.74% (t=−13.89); OV→OV +3.76% (t=18.84); OV→OC −3.87% (t=−10.94); total momentum insignificant at every horizon. High-vol regime −1.33% vs low-vol +1.27%. Idio-vol spreads 36%/23% and 26%/33%. **No transaction-cost assumption anywhere in the paper.** Read locally via pypdf. |
| 4 | http://www.imi.ruc.edu.cn/docs//2025-09/7401146674ad4474a713754d3ca5afaa.pdf | 2026-09-08 | **primary** (IMI Working Paper 2515, 中国人民大学) | A-share replication of Heston–Korajczyk–Sadka | **YIELDED — C19-4.** All A-shares 1999-01–2019-12, RESSET, 30-min sampling. Long-short 0.781 bp / 0.197 bp / 0.737 bp; Fama-MacBeth Pcorr 0.213 (t=62.71), Pother −0.252 (t=−17.28). Extensive robustness (CNY, crises, sub-periods, limit-hits, winsorising, small caps, earnings dates, SOE split). **No net-of-cost figure.** **Note: WebFetch failed — `www.imi.ruc.edu.cn` presents a cert valid only for `*.ruc.edu.cn`.** Retrieved with `curl -k`, read via pypdf. |
| 5 | https://edp.nju.edu.cn/b4/d8/c34655a505048/page.htm | 2026-09-08 | **primary** (张兵, 南京大学商学院) | mechanism for the negative A-share overnight | **YIELDED — the mechanism quote for §1.** T+1 overnight discount stated verbatim; T+0 comparison set named (index futures, HK shares, warrants, overseas indices) as "near zero or positive"; effect strongest in high-turnover / high-vol / high-retail / high-news names; **A/H same-company identification design.** |
| 6 | https://finance.sina.com.cn/roll/2024-08-12/doc-incikrfc9178580.shtml | 2026-09-08 | **primary** (西部证券 研报, republished) | Chinese replication of a Western intraday effect | **YIELDED, then REJECTED (R1).** Replicates Zarattini–Aziz–Barbon (SPY) on 上证50/沪深300/中证500/中证1000 + IH/IF/IC/IM, 2013.01.25–2024.07.31. CSI500: 26.8% p.a., Sharpe 2.11, MaxDD 11.5%, Calmar 2.32; variant 24.0%/2.63/5.5%. Win rate 33–43%, payoff ≈3. Cost 单边万分之一 (futures 万1.5). **Closed list: ORB family.** Retained for its payoff-shape evidence. |
| 7 | https://www.fengchao.pro/blog/intra-day-trading-strategy-of-stock-index-futures-based-on-market-sentiment-stability/ | 2026-09-08 | claims (individual, with code) | a community replication of broker research | **YIELDED, then REJECTED (R3).** Replicates 国信证券 "另类交易策略之二十一" on IF. OOS 15.97% p.a., MaxDD −4.61%, win rate 49.28%, N=208 (0.77/day); multi-entry variant 14.13%, −6.98%, 47.22%, N=486. Cost 2 bp. **Makes no comparative claim against the original's numbers**, so it is not a replication in the sense this lane needed. |
| 8 | https://github.com/hugo2046/QuantsPlaybook | 2026-09-08 | secondary (code corpus) | Chinese code-publishing replication culture | **YIELDED a qualified positive.** Replicates 光大 (RSRS), 华泰 (AI/factor), 招商 (HHT), 国信 (timing/behavioural), 东方 (factor selection), plus 广发/申万宏源/浙商/中金/开源/兴业. Includes "另类ETF交易策略：日内动量". **Reports aggregate performance overviews, not per-report confirm/refute verdicts** — so it documents the culture without adjudicating any effect. |
| 9 | https://bigquant.com/wiki/doc/ILyW3M0hOQ | 2026-09-08 | claims (platform wiki) | IC intraday strategy with metrics | **REJECTED (R2).** HAN123: 9:30–10:00 range, breakout after 10:00, flat 14:55–14:57. Cost 开仓万0.23/平昨万0.23/**平今万1.5**. **No performance metrics in text — results exist only as a chart image.** Closed list: ORB. |
| 10 | https://www.imi.ruc.edu.cn (search surface) + search: A股 高频 时钟效应 | 2026-09-08 | secondary | locating #4 | Located #4 and confirmed the 同时段动量/异时段反转 framing. No other Chinese clock-effect source found. |
| 11 | search: 股指期货 日内 时段效应 尾盘 开盘 半小时 统计 研报 | 2026-09-08 | secondary | Chinese intraday time-bucket literature | **YIELDED** the route to #1/#2 and to BigQuant. Also surfaced 开源金工 "日内分钟收益率的时序特征" (not fetched — factor-enhancement for equities, out of scope for a futures lane). |
| 12 | search: 知乎 动量效应 A股 失效 反转 复现 t值 | 2026-09-08 | claims (search surface) | the A-share momentum-failure consensus | **YIELDED context, no fetchable source.** Consensus stated across multiple Zhihu articles: monthly momentum long-ineffective in A-shares; 1-month/1-week/5-day **reversal** significant (徐高·刘力 2002; 潘莉·徐建国 2011; 东方证券 2017); US momentum ~8% p.a., t>5, 1927–2024. All targets 403 (see #13). |
| 13 | https://zhuanlan.zhihu.com/p/136409571 · https://zhuanlan.zhihu.com/p/632203243 · https://zhuanlan.zhihu.com/p/2067955315841176659 | 2026-09-08 | — | three Zhihu replications of Western intraday effects | **BLOCKED — HTTP 403 on all three via WebFetch; the browser pane refused navigation to zhuanlan.zhihu.com.** Known to contain: a replication of Gao–Han–Li–Zhou half-hour momentum on A-shares, an A-share intraday momentum/reversal study, and R7's 7 bp cost convention / −34.10 bp overnight figure / overnight asymmetry claim. **Recorded so this is not re-attempted with WebFetch.** |
| 14 | search: A股 隔夜收益 为负 美股 为正 T+1 隔夜折价 | 2026-09-08 | secondary | corroboration of the settlement-rule mechanism | **YIELDED.** Located #5 and confirmed #3's framing independently. Also: of 44 major world equity markets, 42 permit T+0; China is one of two that do not. |
| 15 | search: 蒋彧 龚丽 中国沪深股市的开盘效应与收盘效应 (管理科学学报 2020, 23(5):76-88) | 2026-09-08 | secondary (abstract only) | an independent Chinese open/close-effect measurement | **PARTIAL.** Abstract confirms opening and closing effects exist in both exchanges and **flip sign with the bull/bear regime** (positive opening effect in bull markets, negative in bear). No magnitudes, no t-statistics, no cost in the abstract; full text paywalled at jmsc.tju.edu.cn. **Recorded because it is a regime-conditional caveat on C19-2 that the Haitong report does not carry.** |
| 16 | http://dianda.cqvip.com/Qikan/Article/Detail?id=674088965 — 「好的开盘会有好的收盘吗——来自沪深300股指期货的经验证据」 | 2026-09-08 | — | direct IF test of first-half-hour → last-half-hour predictability | **BLOCKED — connection refused (ECONNREFUSED 122.115.35.143:443).** This is the exact Chinese test of Gao et al. on IF futures and could not be read by any route tried. **The highest-value unread item in this lane.** |
| 17 | search: 聚宽 JoinQuant 股指期货 日内 策略 回测 | 2026-09-08 | claims | JoinQuant community research | **NEGATIVE.** Community posts resolve to `test.demo.joinquant.com` behind a demo login. Public surface is API documentation. One ORB post title located, not readable. |
| 18 | https://www.ricequant.com/doc/quant/ · /doc/quant/factor-system · /doc/rqdata/ | 2026-09-08 | secondary | Ricequant community research | **NEGATIVE.** Documentation only (RQData/RQAlpha-Plus/RQFactor/RQOptimizer). **No research output on the public surface.** Minute/tick data for index futures is offered; no published effects. |
| 19 | search: 雪球 量化 股指期货 日内 显著性 回测 手续费 | 2026-09-08 | claims | Xueqiu quant discussion | **NEGATIVE for effects, YIELDED two methodology norms.** "雪球" in Chinese quant writing overwhelmingly means the *snowball autocallable*, not the forum. Norms recorded: total cost = commission + stamp duty + **slippage + impact** ("很多新手只设置了手续费"), and **minimum trade count > 100** for significance. Also: IM 当月合约 at 1.4%/month discount (>30% annualised) driven by ~¥300bn of snowball hedges → R4. |
| 20 | https://smart-lab.ru/blog/1310239.php | 2026-09-08 | claims | a five-year audit of community trading ideas | **BLOCKED — content is images.** Title claims 98.7% of five years of Smart-lab ideas were noise (bascomo, 2026-05-30). Served HTML contains title, byline and comments only; **every number and the entire method are rendered as images.** → R10. |
| 21 | https://smart-lab.ru/blog/1346872.php | 2026-09-08 | claims | a Russian backtest with stated statistics | **REJECTED (R8).** Si futures, +263.8%, MaxDD 17.2%, Sharpe 2.1, PF 2.2, 1.2 trades/day. **"Внутреннюю логику алгоритма пока не раскрываю."** No cost, no slippage, no null, ~25–30 live trades. |
| 22 | https://smart-lab.ru/blog/208076.php | 2026-09-08 | claims | Russian persistence/timeframe study | **REJECTED (R9).** RTS futures 2007–Sep 2014; 1,413,390 1-min candles (417,207 with close=open), 285,160 5-min candles. Descriptive counts only; no null, no return statistic, no cost. |
| 23 | search ×3: smart-lab внутридневная сезонность / Горчаков / проверил гипотезу | 2026-09-08 | claims | any smart-lab study with a null and a cost convention | **NEGATIVE, three consecutive searches.** Surfaced index-constituent pages, wave-count posts and tag indexes. **No intraday-seasonality study located.** This is where Russian saturated. |
| 24 | https://www.mql5.com/ru/forum/6994 · /forum/224434 · /forum/83645 · /ru/articles/20478 | 2026-09-08 | claims | the MQL5 critique culture the brief expected | **NEGATIVE for effects; POSITIVE for norms (R11).** Real methodological critique — forward testing on out-of-sample windows, **>100 trades before believing an optimisation** (30 called "too few, indistinguishable from over-optimisation"), sensitivity to slippage/spread/news. **Applied entirely to EA parameter sets, never to a documented market effect.** |
| 25 | https://smart-lab.ru/blog/1268414.php (IMOEXF funding) | 2026-09-08 | claims | Russian perpetual-futures funding statistics | **REJECTED (R12).** Hedged carry. No CME equity-index perpetual exists, so untestable on ES/NQ regardless of its merits. |
| 26 | https://225labo.com/modules/anomaly/ | 2026-09-08 | claims | Japanese Nikkei-futures seasonality statistics | **REJECTED (R13).** Nikkei 225 futures from 1990; 上昇比率 by calendar date and by nth-weekday (47%, 76%, 56%, 40%, 53%…), defined as 始値→終値. **No sample size, no cost, no payoff, no null.** Buckets are individual calendar dates. |
| 27 | https://qiita.com/kshina76/items/3c7cec76b21b38a0aafd | 2026-09-08 | claims | Japanese code-publishing quant tier | **NEGATIVE.** Nikkei 225 Large backtest using カギ足 (Kagi) rules from 酒田五法. Implementation walkthrough; **no expectancy, no sample statistics, no cost.** |
| 28 | https://ameblo.jp/airsystemtrade/entry-10309522566.html · https://n225.net/ · https://kazamidori225.topblog.site/ | 2026-09-08 | claims | the Japanese 寄引/system-vendor tier | **REJECTED (R14), logged as one cluster.** "PF=4.2" / "PF=4.26 with **スリッページが0**"; "勝率約7割" overnight gap system off European price action. These are 商材 listings and vendor-verification blogs. **Not purchased, not signed up for, no link followed as a referral.** |
| 29 | search ×3: 日経225先物 ナイトセッション / 曜日 アノマリー / 引け前30分 統計 有意 | 2026-09-08 | secondary | Japanese academic or sell-side work on Nikkei futures intraday | **NEGATIVE, three consecutive searches.** Returned exchange product pages, broker session-hours pages, chart services and a ¥-priced DVD. **No Japanese peer-reviewed or sell-side intraday study surfaced.** This is where Japanese saturated. |
| 30 | https://tradistats.com/zyklische-strategien-performance/ | 2026-09-08 | claims | German seasonal DAX backtests | **REJECTED (R15).** 2001–2021, €10,000 start: Sell-in-May→October €49,774 (17/20 years); →November €34,359; →December €21,911; ex-Aug/Sep €50,187; B&H €30,782 (16/20). **No costs, no dividends, no trade count, no drawdown, no significance test.** |
| 31 | https://ninjacademy.traderfox.de/blog/dax-zyklen-modell-…/id-748 | 2026-09-08 | — | German intraday time-of-day cycle model, 10-year minute backtest | **BLOCKED — DNS NXDOMAIN (`getaddrinfo ENOTFOUND`).** Dead host. The one German item that might have carried an intraday statistic. |
| 32 | search ×2: Wertpapier-Forum Backtest DAX Trefferquote CRV / DAX Tageszeit Saisonalität | 2026-09-08 | claims | German community backtests | **NEGATIVE.** Wertpapier-Forum itself surfaced nothing quantitative; results were commercial platform pages (whselfinvest, Investox, kagels-trading) and seasonality chart sites. "Beste Tageszeit 15:30–17:30" appears on an ETF-education page with **no statistic behind it** (R16). This is where German saturated. |
| 33 | https://www.abcbourse.com/forums/msg959668 · https://tradingfutures.fr/… · https://www.tamers.fr/… | 2026-09-08 | claims | French systematic-trading community | **NEGATIVE (R17), logged as one cluster.** One forum thread on CAC40 stop/trailing parameter ranges with **no output statistics**; the rest is content marketing for backtesting platforms. Best number offered anywhere: "Sharpe 1.8 on CAC40 post-Covid" with no sample, no t, no cost. This is where French saturated. |
| 34 | https://www.nordnet.se/marknaden/indikator/omxs30f · https://www.ekonominu.se/… · https://samuelssonsrapport.se/… | 2026-09-08 | claims | Nordic quant community | **NEGATIVE (R18), logged as one cluster.** Broker education describing trend-following and RSI mean reversion qualitatively; a price-history vendor. **No Nordic systematic-research community located at all.** Both named techniques are on the closed list. This is where Nordic saturated. |

**Negative and blocked results, per schema §4, so they are not repeated:** #13 (Zhihu 403 to
WebFetch *and* browser-pane denial — blocked, not empty), #16 (connection refused; the highest-value
unread item), #20 (smart-lab's numbers are images), #31 (dead host), #17/#18 (JoinQuant behind a
demo login; Ricequant docs-only), and the four saturation clusters #23, #29, #32, #33/#34.

**Searches run that produced nothing and should not be repeated:** Japanese peer-reviewed or
sell-side work on Nikkei futures intraday behaviour (three query formulations, none); smart-lab
intraday seasonality with a null (three formulations, none); Wertpapier-Forum quantitative
backtests (none); a Nordic systematic-research community (none). **A future non-English lane should
target the professional research tier by language — Japanese sell-side 金融工学, Russian academic
finance, German university/Bundesbank working papers — and skip the forum layer entirely.**
