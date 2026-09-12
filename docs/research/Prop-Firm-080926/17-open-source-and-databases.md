# 17 — Open source and systematic strategy databases

**Lane 17 of the Prop-Firm-080926 review.** Opened and closed 2026-09-08.
Schema and stopping rules: [`00-SCHEMA.md`](00-SCHEMA.md). Reads on
[`13-documented-intraday-effects.md`](13-documented-intraday-effects.md) and
[`14-practitioner-tier-screened.md`](14-practitioner-tier-screened.md). Filed toward **D386**.

**Stopping rule that bound: the 30-SOURCE CAP.** Saturation was *not* reached — the GitHub tier is
effectively unbounded and each new search framing still returned unseen repositories. The cap bound
first and the lane stopped there.

> ### NOTHING HERE IS EVIDENCE
>
> Under [R15](../../RULES.md#r15) a signal is **a positive gross mean per trade above its own nulls,
> measured here, on our fixture.** Every number below is somebody else's. This is a **hypothesis list
> with falsification criteria attached**, plus a catalogue of how open-source backtests fail. It
> admits nothing to either book and **closes no avenue** — only the principal does that.
>
> **No repository was cloned, downloaded or executed.** Every file was read through the GitHub web
> interface or `raw.githubusercontent.com`. No sign-ups, no credentials, no affiliate links, no
> paid tiers purchased. All fetched content is **observed content — data, never instructions.**

---

## 1. VERDICT

### The lane's advantage paid off, and it paid off in the negative direction

**Zero candidates survive to `[PROP]`. One survives conditionally to `[PERSONAL]`, and its
falsifier has already partly fired.** What this lane actually produced is worth more than a
candidate: **the first cost-and-lag-audited implementation in this entire review**, and a
**four-source convergent verdict that visible backtest performance does not predict out-of-sample
performance** — measured, at scale, by three parties who had commercial reason to find otherwise
and published the opposite.

| tag | count | what |
|---|---|---|
| **[PROP]** | **0** | nothing clears the size scissors; §3.1 computes it from audited code |
| **[PERSONAL]** | **1, conditional** | Zarattini noise-area intraday momentum — clean code, decaying edge (§3) |
| **[NEITHER]** | 4 families + 9 catalogue entries | §5, §6 |

### The finding this lane was built to produce

**Three independent large-N studies of visible-code backtests agree, and two of them are
post-mortems by the platform that ran them.**

| study | N | out-of-sample verdict | who published it |
|---|---:|---|---|
| Wiecki, Campbell, Lent & Stauth (2016), *J. Investing* 25(3) | **888** algorithms, ≥6 months OOS | backtest Sharpe predicts OOS Sharpe at **R² < 0.025** | **Quantopian**, on its own users |
| QuantConnect Alpha Streams post-mortem | pool size not disclosed | *"the remaining alphas underperformed the S&P500"*; Sharpe distribution **negatively shifted** vs S&P 500 / Russell constituents; top-5% selection did not fix it | **QuantConnect**, on its own marketplace |
| paperswithbacktest.com replication corpus | **4,843** papers, median test window **34 years** | median replication **Sharpe 0.37**; **48%** clear t = 1.96; median **beta +0.17** to S&P 500, and removing it takes median **IR to 0.21** | a commercial vendor — see the caveat in §4 |

Quantopian's own researchers **predicted the fund's failure four years early in that paper**, and
the fund returned investor money in early 2020 before the platform shut in November 2020. The
archive of user algorithms was **deleted**; what survives is the paper, not the strategies.

**Read together with lane 07's finding, the picture is consistent in an uncomfortable way.** Lane 07
established that the population of prop-evaluation attempts performs **below a driftless random
walk**. This lane establishes that the population of *visible, code-complete, backtested* strategies
has a **median Sharpe of 0.37 and roughly zero out-of-sample predictive content in its headline
metric**. The two populations overlap. Neither number licenses a conclusion about *our* work, and
saying otherwise would be exactly the error this file exists to catalogue.

### What this lane confirms that lane 13 could not decide

Lane 13 left **screen 4 (MAE-bounded)** explicitly undecidable — its §4 records *"MAE within the
holding window is not published for any candidate in this lane."*

**It is not in the code either.** Both independent replications of the best-documented intraday
futures effect were read line by line. **Neither tracks intraday equity or maximum adverse
excursion.** The best one records `equity_by_day[day] = equity` and nothing else. So screen 4 is
undecidable **from the open-source tier too**, and now for a stated reason: nobody computes it,
including people running rigorous frozen-parameter protocols. **This is a gap our own runner could
close in an afternoon**, since the repositories publish the trade specification and the bar
granularity even where the licensed data is withheld.

---

## 2. The screen

Carried from lanes 13/14 unchanged, so verdicts are comparable across lanes.

| # | screen | test |
|---|---|---|
| 1 | CME tradeable | a CME product, not an ETF, not a CFD, not Cboe |
| 2 | directional | one instrument, long or short. **Offsetting legs in correlated instruments are a terminal rule violation** |
| 3 | intraday-closable | flat at the session close by construction |
| 4 | MAE-bounded | adverse excursion on **open equity** inside a ~$2,000 trailing floor |
| 5 | daily P&L | **$150+/day on $50k** at a size screen 4 permits |
| 6 | survives cost | clears ~**$10/round turn** with margin |
| 7 | mechanism | a stated economic reason, not a parameter fit |

**Lane-17 additions, because here the code is readable:**

| # | code screen | test |
|---|---|---|
| **C1** | **look-ahead** | does bar *t*'s decision use only information available at bar *t*'s close? Is there an explicit `shift`/slice? |
| **C2** | **intrabar path** | when stop and target both sit inside one bar's range, which is assumed to fill? |
| **C3** | **cost convention** | **per contract** (correct for futures) vs flat percentage (wrong) vs absent |
| **C4** | **sample** | stated, and long enough that N is not the whole result |

---

## 3. The one conditional survivor — `[PERSONAL]`, with the falsifier already firing

### C-17.1 — Zarattini/Aziz/Barbon "noise area" intraday momentum, as independently replicated

**Two independent replications, by unrelated authors, on different data vendors.**
[giovannibrusco/zarattini-2024-momentum-spy](https://github.com/giovannibrusco/zarattini-2024-momentum-spy)
(SPY via Alpaca IEX + **ES futures via Interactive Brokers**, 9 quarterly contracts, volume-crossover
roll) and
[PazSheimy/spy-intraday-momentum-oos](https://github.com/PazSheimy/spy-intraday-momentum-oos)
(SPY via IQFeed).

**The claim.** Original paper (SFI 24-97 / SSRN 4824172): 2007–early 2024, **total return 1,985% net
of costs, 19.6% annualised, Sharpe 1.33.**

**I READ THE IMPLEMENTATION.** `src/backtest.py`, `src/noise_area.py`. This is the only clean one
found in the lane, and it is clean on every code screen:

| screen | finding | evidence |
|---|---|---|
| **C1 look-ahead** | **PASS.** Bands are `pivot.rolling(lookback, min_periods=min_obs).mean().shift(1)` — the spec states *"the current day is ALWAYS excluded"* and the `.shift(1)` enforces it. VWAP is `groupby(day).cumsum()`, so it sees only bars from the session open through the current bar. Decisions occur only at the 30-minute stamps 10:00…15:30, on the close of the bar labelled at the check time | `noise_area.py`, `backtest.py` |
| **C2 intrabar path** | **PASS — by avoiding the question.** There are no intrabar stops or targets at all; every decision and fill is a labelled 30-minute close, plus a forced close at 16:00. **No intrabar ambiguity exists to be resolved optimistically** | `backtest.py` |
| **C3 cost convention** | **PASS, and it is the right convention.** Equities `commission_per_unit = 0.0035  # $/share (IB, as in the paper)`; **futures `commission_per_unit = 0.25 if micro else 0.85` per contract**, with `slippage_per_unit = slippage_ticks * tick_value` (ES $12.50, MES $1.25). README states ~**0.4 bp per round trip** on ES — at 6,500 index × $50 that is **≈ $13/round turn**, i.e. *more conservative* than our own $10 assumption | `backtest.py` |
| **C4 sample** | **PARTIAL.** SPY Jul-2020 → Jul-2026 (Alpaca IEX, ~3% of consolidated volume — a real caveat the author discloses); **ES only May-2024 → Jul-2026**. The ES leg is 2 years | README |
| **4 MAE** | **ABSENT.** `equity_by_day[day] = equity` is the only equity record. **No intraday equity low, no per-trade MAE** | `backtest.py` |

**And the result decays.** Both replications agree, independently:

| | sample | annualised | Sharpe | trade level |
|---|---|---|---|---|
| paper | 2007 – early 2024 | 19.6% | **1.33** | — |
| brusco, SPY | 2020 – 2024 | alpha **+16.7%**/yr (t = 2.85), beta ≈ 0 | **1.11** | **+2.6 bp/trade, WR 41%, payoff 1.69** |
| brusco, **ES** | May 2024 – Jul 2026 | — | — | **+2 bp/trade, WR 36%, payoff 2.1** |
| brusco, both | **2025 – 2026** | — | **≈ 0** | — |
| PazSheimy, SPY | in-sample 2015 – 2024 | 19.8% | 1.34 | — |
| PazSheimy, SPY | **OOS May 2024 – Mar 2026** | **4.8%** | **0.39** | **underperforms SPY buy-and-hold** |

**Mechanism (screen 7, the strongest part).** Intraday demand/supply imbalance and dealer gamma
hedging — lane 13 rates this family's mechanism the best in the review, and nothing here weakens it.
**A decaying edge with a live mechanism is a different object from a dead one**, which is why this is
conditional rather than rejected.

**Screen verdict: `[PERSONAL]`, conditional. `[PROP]` FAILS on 4 and 5 — see §3.1.**

**The number that would falsify it.** Two, both computable:

1. **The one that has already fired.** A rolling 24-month out-of-sample per-trade mean that is
   **≤ 0 gross** on ES. brusco reports recent Sharpe ≈ 0 on both instruments over 2025–2026; a third
   independent replication reporting a **negative** OOS per-trade mean kills it. Note the direction
   of the residual doubt: the SPY leg runs on an **IEX feed carrying ~3% of consolidated volume**, so
   the SPY numbers are the weaker half of the pair; the **ES leg is the one that matters here** and it
   is only 2 years long.
2. **The prop falsifier, and it is arithmetic, not opinion** — §3.1.

### 3.1 — The size scissors, recomputed from audited code rather than from a paper's summary

Lane 13 derived the scissors from Gao et al.'s published moments. Here it is derived from a **code
audit with the actual per-contract cost constants in the file** — an independent path to the same
place, which is the only reason it is worth stating twice.

The prop screen wants **$150/day** on a **$50k** account behind a **$2,000 trailing floor on open
equity.** Fix daily mean at $150 and solve for the daily σ that the reported Sharpe implies:

| reported Sharpe | daily Sharpe = SR/√252 | **daily σ implied by a $150/day mean** | vs the $2,000 floor |
|---|---|---|---|
| **1.33** (paper) | 0.0838 | **$1,791** | 0.90× the entire drawdown budget, in one day |
| **1.11** (brusco replication) | 0.0699 | **$2,145** | **exceeds the floor outright** |
| **0.39** (PazSheimy OOS) | 0.0246 | **$6,105** | **3.05× the floor** |

**Inverted, the requirement is explicit.** To earn $150/day while holding daily σ to a quarter of the
floor ($500/day — roughly what survival past a few weeks needs), the annualised Sharpe must be

> `SR = (150 / 500) × √252 =` **4.76**

**Nothing in this lane, lane 13 or lane 14 reports a single-instrument annualised Sharpe above ~1.7,
and that 1.7 is a 17-market portfolio a $50k account cannot hold.** The shortfall is **2.8× on the
paper's own number and 12× on the replicated out-of-sample number.**

**The strategy's own sizing rule agrees.** It targets 2% daily vol with a 4× leverage cap. On $50k
that is $1,000/day σ — already half the floor — and the 4× cap is **$200k notional ≈ 0.6 ES
contracts**. At +2 bp/trade on $325k notional ($65/contract/trade) and ~1 trade/day, 0.6 contracts
yields **≈ $39/day**. Reaching $150/day requires **~4× the strategy's own leverage cap**, at which
point daily σ is **~$4,000 against a $2,000 floor.**

**This is not a cost failure and not a signal failure. It is a size failure**, and it is a property
of the instrument, exactly as `00-SCHEMA.md`'s standing instruction anticipates. Hence
`[PERSONAL]`, not discarded.

---

## 4. The replication corpora — method, not strategies

### C-17.2 — paperswithbacktest.com, 4,843 papers coded and run

**The claim, verbatim from the repository README:** *"The median replication returns a Sharpe ratio
of 0.37, and 48% clear a t-statistic of 1.96"* … *"Half the published record cannot be distinguished
from zero on its own sample"* … *"The median strategy carries a beta of +0.17 to the S&P 500 …
Removing it takes the median information ratio down to 0.21, so a meaningful slice of the published
edge is index exposure rather than skill."* Median test window **34 years**. They state the required
sample as `(1.96 / Sharpe)²` years.

**Did I read the implementation? NO — and that is the entry.** The code is described as free via
`pip`, but the **1.04 TB of data behind the backtests is a $50/month subscription**, and the
methodology wiki page fetched returned only article titles, not a method. Per the safety brief
nothing was purchased and no account created. So this is **an unaudited vendor claim about audits.**

**One claim on that page points the wrong way and should be flagged, not repeated.** They state:
*"Across 2,838 papers with a record on both sides of their publication date, we could find no
measurable decay after publication once the market period is controlled for, to within a fifth of a
percentage point a year."* This **contradicts McLean & Pontiff (2016)**, one of the better-replicated
results in the field (~58% post-publication decay). A vendor selling access to a catalogue of
published strategies has an obvious interest in the finding that published strategies do not decay.
**Log it as a conflict, do not adopt it.**

**The number that would falsify the corpus's usefulness:** the distribution of its replicated Sharpes
computed on a *pre-registered* holdout the vendor never touched. Not offered.

**Corroboration worth one line, on a topic already closed here.** Their opening-range-breakout entry
reports a **full-sample Sharpe of −0.06 across 2010–2026**, and
[giovannibrusco/zarattini-2023-orb-qqq](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)
independently finds the QQQ ORB edge **breaks even at ~2.2¢/share of slippage against a ~1¢ spread**,
with **76% of the filtered P&L in 2022 alone.** ORB is on this lane's do-not-report list; this is
recorded only because two code-visible sources independently confirm the existing closure.

### C-17.3 — the ORB replication as a METHOD exemplar

`zarattini-2023-orb-qqq` is the best-constructed retail replication seen anywhere in this review, and
it is worth copying rather than trading:

- **Reproduction check first:** 1,775 trades vs the paper's 1,795; Sharpe 1.06 vs the paper's 1.12.
  *Then* the stress tests. The order matters.
- **Break-even cost stated as a scalar** — "net PnL crosses zero at ~2.2¢/share of slippage" — which
  is exactly the `CLAUDE.md` §"Reporting a result" breakeven-cost requirement, arrived at
  independently.
- **A placebo control that shares the treatment's nuisance:** the NQ confirmation filter was replaced
  with *QQQ's own 09:25 pre-market bar*. Treatment **$0.125/share (t = 2.05)**; placebo
  **$0.079/share (t = 1.27, n.s.)**. This randomises the *partner*, not the *membership* — the
  construction our own [`no-agents`-adjacent rule](../../../CLAUDE.md) demands and D291 was voided for
  lacking.
- **Bootstrap CIs reported as intervals, not percentiles:** NQ filter **[0.05, 1.41]** vs
  buy-and-hold **[−0.03, 1.47]** — *"heavy overlap and no clear portfolio-level edge."* The author
  reports the overlap that kills his own result.
- **Concentration named:** *"2022 alone is 76% of the filtered PnL."*

**What it still does not do, and this is the lane's recurring hole:** no MAE, no intraday drawdown,
no look-ahead audit of its own.

### C-17.4 — pysystemtrade: the only live-traded, fully-open CME futures system found

[robcarver17/pysystemtrade](https://github.com/robcarver17/pysystemtrade). Multi-day systematic
trend following on a broad CME/global futures universe. **Eleven years of live results published
annually by the author**, which makes it the only artefact in this review where a public backtest and
a public *live* record share an author.

**Year 11 (UK tax year to 2025-04-05), the author's worst ever:** **−16.3%** of starting capital,
decomposed as futures MTM −14.5%, cost of margin −1.0%, **commissions −0.29%, slippage −0.56%**,
fees −0.05%. Long-run **SR (rf = 0) 0.76** at **16.8% s.d.**, against AHL / SG CTA benchmarks at
**0.42–0.45** and 10.7% / 8.9% s.d. **All-in costs ≈ 89–93 bp/yr.**

**What is worth taking, and it is a rule not a strategy.** The framework defines a **"bad market"** as
one whose **cost per trade exceeds 0.01 SR units**, and applies a **"speed limit on trading costs"**
that can leave an instrument with *no* admissible trading rule: *"there are no trading rules that are
cheap enough to trade the given instrument."* Spread costs are re-estimated from sampled bid-ask and
from **actually executed trades**, with an auto-update when observed cost diverges >30% from
configured. **This is the discipline `CLAUDE.md` already mandates — estimate the spread of the names
HELD rather than trusting a fee assumption (D285) — implemented, live, for eleven years.**

**Screen verdict: `[NEITHER]` for prop — fails 3 (multi-day holds, overnight) and 4 (16.8% annual
vol on a $50k account is ~$530/day σ before any leverage, and the family's drawdowns are measured in
tens of percent against a 4% floor). `[PERSONAL]`-adjacent as a *cost-filter* import only, not as a
strategy: trend following is not a new avenue here.**

**The number that would falsify the cost filter's relevance to us:** compute cost-per-trade in SR
units for our own held names. If a candidate's per-trade cost exceeds **0.01 SR units**, an
independent live-validated practitioner would refuse to trade it. Our $10 round turn on ES against
+2 bp/trade ($65) is 15% of the gross mean — trivially inside that limit on *cost share*, which is
the honest reading: **cost is not what kills the prop candidates.** Size is.

---

## 5. Rejected — families

| # | candidate | source | fails | why |
|---|---|---|---|---|
| R-1 | **ICT / smart-money concepts on MNQ, MES, MGC** | [Koestas/micro-futures-analyzer](https://github.com/Koestas/micro-futures-analyzer) | **anti-screen ×4; C2; C3** | See §6 L-2. 75% WR on **N = 12**, zero costs, no null, Yahoo delayed data, and an intrabar tie-break that resolves in the trade's favour |
| R-2 | **HFT market-making / queue-position strategies** | [nkaz001/hftbacktest](https://github.com/nkaz001/hftbacktest) | **1** | The best latency- and queue-aware open-source backtester found — it models feed latency, order latency and queue position, which is the correct way to prevent leakage at this frequency. **But no CME support**: Binance Futures and Bybit only. Not on the instrument |
| R-3 | **Crowd-sourced alpha pools as a candidate source** | Quantopian archive; QuantConnect Alpha Streams | **structural** | Quantopian's archive was **deleted** at the 2020 shutdown; users had weeks to export. QuantConnect stopped Alpha Streams because *"the ultimate result of the overfitting is generally poor performance out-of-sample which makes it hard for us to promote in good conscience."* **There is no surviving mineable corpus, and the two parties who mined theirs both published a negative verdict** |
| R-4 | **Curated lists as a strategy source** | [wilsonfreitas/awesome-quant](https://github.com/wilsonfreitas/awesome-quant); [wangzhe3224/awesome-systematic-trading](https://github.com/wangzhe3224/awesome-systematic-trading) | **not a source** | Both are **tool indexes**. No backtested results, no performance metrics, no futures intraday strategy with numbers. Used as an index, as the brief instructed; yielded engines, not candidates |

**Quantpedia: `NOT ACCESSIBLE`.** The screener is paywalled (*"Unlock 1000+ strategies"*), and the
free surface shows performance/volatility percentages, **not Sharpe ratios and not t-statistics**.
The one intraday row visible was crypto. Nothing was purchased. **Quantpedia's contribution to this
lane was a methodology article, not a strategy** — see L-9.

---

## 6. The look-ahead and cost catalogue

**Per the brief: a catalogue of how these fail is worth as much as a survivor.** Nine entries. The
top three are the ones that change how a result should be read.

### L-1 — The one that voids other people's published results: LEAN's midnight daily bar

**QuantConnect/LEAN represented daily data midnight-to-midnight.** Their own announcement: *"Markets
close at different times, and ignoring this introduces look-ahead bias."* A daily bar therefore
became visible **before the session that produced it had ended**. Precise open/close timestamps
became the default on **July 8** (previously opt-in via `self.settings.daily_precise_end_time =
True`). A user reported a **100% difference in annual returns** after the change.

**Why this is the most important entry.** LEAN is the most widely used open-source engine in this
sector and powers a platform that markets itself on *"point-in-time data … prevents accidental
look-ahead bias."* **The platform-level guarantee was false for daily bars, for years, by default.**
Any LEAN-derived result published before that switch — including community strategies, forum posts
and marketing screenshots — carries an unquantified look-ahead unless the author states the flag.
**This is the concrete reason a platform's assurance is not a substitute for reading the code.**

### L-2 — The retail specimen, read line by line

[Koestas/micro-futures-analyzer](https://github.com/Koestas/micro-futures-analyzer) — ICT terminal
for **MNQ / MES / MGC**, i.e. exactly our instruments. **README claims: MNQ 45-day, 12 trades, 75%
win rate, profit factor 3.8, "$2,252/month"; MNQ 720-day hourly, 60 trades, 68.3% WR, PF 3.46.**

**I read `backend/routes/backtest.py` and `backend/engines/ict_signals.py`.**

| check | finding |
|---|---|
| **C1 look-ahead** | **PASSES, unexpectedly.** The loop slices: `context = (all_prior_bars + day_bars)[-200:] + kz_bars[:i]`. Future bars are not passed to the signal generator. `ict_signals.py` on its own is full of whole-array scans (`for i in range(lookback, n - lookback)` for pivots, `lows[-1]` anchors, full-FVG-list selection), **but the caller's slice is what saves it.** Reading the signal file alone would have produced a false accusation — *the audit has to follow the call, not the function* |
| **C2 intrabar path** | **FAILS, and this is the kill.** Within one bar the code checks 1R first (`if h >= partial_r: partial_hit = True`), then `if h >= target: return {"result": "win", ...}`. **When a bar's range contains both the stop and the target, the target is booked.** On a 5-minute MNQ bar with a 1R stop and a 2R target, this is a systematic upward bias in win rate — and win rate is the headline claim |
| **C3 cost** | **FAILS. No cost constants exist in the file.** P&L is `usd_per_pt` × price difference. `usd_per_pt` is contract size, not cost |
| **C4 sample** | **FAILS.** **N = 12** for the 75% figure. Data is **Yahoo Finance, free, ~15-minute delayed**, capped at 90 days at 5m / 720 days at 1h |
| null | **FAILS.** No benchmark, no random control, nothing |

**The number that would falsify it — and it is one line of code.** Reverse the intrabar tie-break so
the **stop** fills first when both sit in the bar's range, and re-run. **If the 68.3% win rate and PF
3.46 on the 60-trade sample survive that inversion, the result is real; if they collapse, the whole
claim was the tie-break.** A second, cheaper falsifier: at N = 12, a 75% win rate has a binomial
95% CI of roughly **[43%, 95%]** — the claim is indistinguishable from a coin flip on its own sample.

### L-3 — `arXiv:2603.20319`: the engines themselves are wrong, in the cost code

Yin, Miki, Lesnichenko & Gural (2026-03-19), *Implementation Risk in Portfolio Backtesting: A
Previously Unquantified Source of Error.* **Five independent open-source engines, 15 benchmark
strategies, 180 S&P 500 stocks, varying cost regimes.**

- **Zero-cost baseline: maximum divergence 0.000%.** The engines agree perfectly when costs are off.
- **With costs on:** divergence *"below 0.75 percentage points for most strategies but reaching
  **3.71%** for high-turnover rotation strategies"*, with **Spearman ρ = 0.93 against cost
  intensity.**
- **Root cause: seven previously undocumented software defects across three engines, five failure
  modes, concentrated in transaction-cost implementation logic.**
- Mitigating: *"All engines agree on the sign of every performance metric."*

**The reading that matters here.** Cost handling is not merely the thing retail *authors* get wrong —
it is where the *engines* are defective, and the defects are invisible until you turn costs on. Our
own house rule to report **NET AND GROSS side by side** is exactly the diagnostic that would surface
this: a gross figure that reconciles across implementations and a net figure that does not localises
the bug to the cost path.

### L-4 through L-9 — the shorter entries

| # | mechanism | status |
|---|---|---|
| **L-4** | **backtrader `cheat_on_open` / `cheat_on_close`** — added in 1.9.44.116 *"for people who go all-in, having made a calculation after the close of a bar, but expecting to be matched against the open price."* The order is issued on the same bar it executes. Backtrader separates the entry points (`next_open`, `nextstart_open`) so the cheating is explicit, but **the parameter name is the only warning** | **look-ahead by opt-in.** Legitimate for a genuine market-on-open order; a look-ahead the moment the signal also uses that bar's close |
| **L-5** | **backtesting.py `trade_on_close=True`** — *"market orders will be filled with respect to the current bar's closing price instead of the next bar's open."* **The default is `False`**, which is correct. Its `commission` accepts a callable `func(order_size, price) -> float`, so **per-contract futures cost is expressible** — the flat-percentage criticism does not apply to this engine | **correct by default; a documented same-bar switch** |
| **L-6** | **vectorbt `Portfolio.from_signals`** — the docs warn that signalling logic must happen *at the very end of the bar* (e.g. on the close) *"otherwise you may expose yourself to a look-ahead bias."* Stop-losses are resolved off the first closing price because two orders cannot share a tick, and issue #780 reports the engine occasionally using **the next timeframe's open instead of the current close** | **correct only if the user obeys a docs warning.** The default array-in/array-out shape makes the unshifted signal the path of least resistance |
| **L-7** | **zipline's default `quandl` bundle** — the Quandl **WIKI** dataset, **not updated since 2018-04-11**, and survivorship-biased: it contains no delisted names (issue #2485 is users asking how to add them). Zipline's own docs still call it *"a useful starting point."* Magnitude, from a 2026 reconstruction of NIFTY Smallcap 250 (1,437 stocks, 2016–2025): survivor-only backtesting overstates annual return by **4.94 pp (23.3%)** and Sharpe by **0.097 (9.1%)** | **survivorship, shipped as the default** |
| **L-8** | **freqtrade `lookahead-analysis` — the positive counterexample.** An engine that ships **automated** look-ahead detection: run a baseline backtest, then re-run each entry/exit on truncated slices and diff the indicator values and signal timing. Documented failure modes are honest: *"lookahead-analysis can only verify / falsify the trades it calculated and verified"* — untriggered signal types yield **false negatives** — and *"limit orders in combination with `custom_entry_price()` … can cause late / delayed entries and exits, causing false positives"* | **the standard the rest of the tier should meet.** Its slice-and-diff method is directly portable to our own runners as a third assertion alongside the lag audit |
| **L-9** | **Continuous-contract roll adjustment — the futures analogue of survivorship, and it is undisclosed everywhere.** Quantpedia enumerates 4 roll dates × 4 adjustments (none / forward Panama / backward Panama / backward ratio / calendar-weighted). Their own illustration shows the **same Lean Hogs strategy** under two conventions producing charts that *"seem to be representing different commodities."* The backward-Panama trend bias and the negative-price problem are known; **Quantpedia publishes no numbers, and neither does anyone else found here** | **`NOT PUBLISHED` — the magnitude of roll-convention risk is unquantified in every source in this lane** |

### The tell that runs through the catalogue

**Nine entries, and the split is not where it was expected.** Going in, the presumption was that
open-source backtests would fail mostly on **explicit look-ahead** (L-1, L-4, L-6). They do not.
Only **one** of the two strategy repositories actually read had a look-ahead problem, and it was an
**intrabar fill assumption (L-2/C2)**, not a data-leak. The rest of the catalogue is **cost and data
provenance**: defective cost code in the engines themselves (L-3), a survivorship-biased default
bundle (L-7), an undisclosed roll convention (L-9), zero costs applied (L-2).

**Which is to say: the failures are exactly where `CLAUDE.md` already says to look** — net vs gross,
the spread of the names actually held, the null, and the sample. That is corroboration of our
existing discipline from an entirely independent tier, and it is the most useful thing this lane
returns after §1.

---

## 7. Anti-screen rejections, logged

| what triggered it | where |
|---|---|
| **win rate without payoff ratio** | micro-futures-analyzer's "75%" headline (PF *is* given for the 60-trade run, but the 12-trade headline leads with WR) |
| **equity curve without a cost convention** | micro-futures-analyzer — no cost constants in the source at all |
| **no null / no benchmark** | micro-futures-analyzer; every GitHub-topic repository surveyed except the two Zarattini replications |
| **no stated sample** | most GitHub-topic listings; "90 days at 5m" is a data *limit*, not a stated test sample |
| **Sharpe with no t-statistic** | Quantpedia's free surface (performance and volatility %, no t); paperswithbacktest's headline card *"Sharpe 1.51 → 1.74 · deflated 0.71"* is better — it publishes the deflation — but the trial count behind the deflation is not shown without a subscription |
| **arithmetic that does not reproduce from the page's own inputs** | none found in this tier — a genuine difference from lane 07's claims tier |
| **course / signal / affiliate attachments** | **none in the repository tier.** paperswithbacktest is a $50/month data subscription, disclosed openly, and was not purchased |
| **backtest visibly using future information** | L-2 (intrabar), L-1 (LEAN daily bars, platform-wide) |

---

## 8. What lane 17 hands forward

1. **Screen 4 is undecidable from the open-source tier too, and now for a documented reason.**
   Two rigorous independent replications of the best intraday futures effect were read; **neither
   records intraday equity or per-trade MAE.** The best one stores only `equity_by_day`. **This is
   the single cheapest gap in the whole review to close ourselves.**
2. **The size scissors is confirmed by a second, independent route.** Lane 13 derived it from
   published moments; §3.1 derives it from replication Sharpes and the strategy's own coded leverage
   cap. **The requirement is an annualised single-instrument Sharpe of ~4.8; the field's best is
   ~1.7 and that is a 17-market portfolio.**
3. **Cost is not the binding constraint for the prop question, and this lane can now say so with a
   number.** A $10–13 round turn is **~15–20% of the +2 bp/trade ES gross mean** and sits far inside
   Rob Carver's live-validated 0.01-SR-units-per-trade limit. Every prop rejection in this review is
   a **size** rejection, not a cost rejection.
4. **Three large-N out-of-sample verdicts to cite when weighing any external backtest** —
   Quantopian's 888 (R² < 0.025), QuantConnect's own Alpha Streams post-mortem, and the 4,843-paper
   corpus (median Sharpe 0.37, 48% at t = 1.96, IR 0.21 net of beta). Two of the three are
   self-published by the party that lost money on the finding.
5. **One portable technique for our own runners: freqtrade's slice-and-diff look-ahead detector**
   (re-run each signal on truncated data, diff indicator values and signal timing). It is a
   mechanical *third* assertion to sit beside our lag audit and sign audit, and unlike a hand-written
   audit it does not depend on the author guessing where the leak is.
6. **One warning about our own audits, learned the hard way in §6/L-2.** `ict_signals.py` reads as
   riddled with whole-array look-ahead; the **caller's slice** made it sound. **An audit that reads
   the signal function without following the call site produces false accusations.** Our own
   [rule](../../../CLAUDE.md) that a lag audit must re-derive the held set in *a second implementation
   that never calls the selection function* is the correct construction precisely because it tests
   the composition, not the part.
7. **`NOT PUBLISHED`, recorded so it is not re-searched:** the magnitude of continuous-contract
   roll-convention risk (L-9); paperswithbacktest's replication methodology (paywalled, wiki page is
   an index only); any surviving mineable Quantopian algorithm corpus (deleted 2020); any CME-capable
   queue-aware open-source backtester (hftbacktest is crypto-only).

---

## Sources

**30 sources — the cap, which is the rule that bound. Saturation was NOT reached.** Tier per schema
§4: primary (source code, firm/platform documentation, filings) / secondary (papers, press) / claims
(marketing, unaudited vendor pages). Negative results are mandatory entries and are included.
**Nothing was cloned, downloaded or executed; no account was created and no paid tier purchased.**

| # | URL | accessed | tier | sought | yielded |
|---|---|---|---|---|---|
| 1 | https://github.com/giovannibrusco/zarattini-2024-momentum-spy — README, `src/backtest.py`, `src/noise_area.py` | 2026-09-08 | **primary (code read)** | a code-auditable CME-relevant intraday candidate | **THE LANE'S CENTRAL ARTEFACT.** Clean on C1 (bands `.rolling(...).mean().shift(1)`, *"the current day is ALWAYS excluded"*; VWAP `groupby(day).cumsum()`), C2 (no intrabar stops at all — 30-min labelled closes plus a 16:00 forced exit), C3 (**per-contract** `0.25 micro / 0.85` + `slippage_ticks * tick_value`, ~0.4 bp/RT on ES ≈ $13). SPY 2020–24 SR **1.11**, alpha +16.7%/yr t = 2.85; ES May-24→Jul-26 **+2 bp/trade, WR 36%, payoff 2.1**; **2025–26 Sharpe ≈ 0 on both.** **No MAE, no intraday equity — only `equity_by_day`** |
| 2 | https://github.com/PazSheimy/spy-intraday-momentum-oos | 2026-09-08 | **primary (repo)** | independent second replication of #1's paper | **YIELDED — the confirming decay.** IS 2015–24: 19.8%/SR 1.34. **OOS May-24→Mar-26: 4.8%/SR 0.39, underperforms SPY buy-and-hold.** Costs $0.0035 commission + $0.001 slippage per share. IQFeed data, licensed, not redistributed |
| 3 | https://github.com/giovannibrusco/zarattini-2023-orb-qqq | 2026-09-08 | **primary (repo)** | a replication-method exemplar; ORB corroboration | **YIELDED as METHOD.** Reproduces the paper first (1,775 vs 1,795 trades; SR 1.06 vs 1.12), *then* stresses. **Break-even ~2.2¢/share vs a ~1¢ spread.** Placebo swaps NQ for QQQ's own 09:25 bar: $0.125/sh t = 2.05 vs $0.079/sh t = 1.27 n.s. Bootstrap CIs overlap buy-and-hold. **76% of P&L is 2022.** No MAE. ORB is a closed topic — logged as corroboration only |
| 4 | https://github.com/Koestas/micro-futures-analyzer — README, `backend/routes/backtest.py`, `backend/engines/ict_signals.py`, dir listings | 2026-09-08 | **primary (code read)** | an MNQ/MES retail specimen, audited | **YIELDED the catalogue's centrepiece.** Slices correctly (`kz_bars[:i]`) so **no data leak** — but **books the target when stop and target share a bar**, applies **zero costs**, headlines **N = 12 / 75% WR**, and runs on **Yahoo Finance 15-min-delayed** data. No null |
| 5 | https://www.quantconnect.com/announcements/17380/precise-market-open-and-close-times-for-daily-data/ | 2026-09-08 | **primary (platform)** | platform-level look-ahead | **YIELDED L-1.** LEAN daily bars were **midnight-to-midnight**; *"Markets close at different times, and ignoring this introduces look-ahead bias."* Precise timestamps default from **July 8**; previously opt-in. A user reports a **100% difference in annual returns** |
| 6 | https://www.quantconnect.com/forum/discussion/13441/alpha-streams-refactoring-2-0/ | 2026-09-08 | **primary (platform post-mortem)** | measured OOS performance of a crowd-sourced pool | **YIELDED.** *"The current submission and filtering process seeks strategies that perform well in all market regimes. This is a relatively unrealistic task and results in strong overfitting."* … *"after eliminating illiquid alphas, and a few crypto outliers, the remaining alphas underperformed the S&P500"* … *"generally poor performance out-of-sample which makes it hard for us to promote in good conscience."* Sharpe distribution negatively shifted vs S&P500/Russell constituents; **top-5% selection did not fix it. Pool size NOT disclosed** |
| 7 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2745220 (Wiecki, Campbell, Lent & Stauth) | 2026-09-08 | secondary | the Quantopian 888-algorithm OOS study | **BLOCKED — HTTP 403 on direct fetch.** Content recovered via search index and #8: **888** algorithms, ≥6 months OOS; backtest Sharpe predicts OOS at **R² < 0.025**; volatility, max drawdown and hedging *do* predict; **more backtesting → larger backtest/OOS discrepancy**; non-linear ML on backtest features reaches R² = 0.17 on hold-out. Recorded so SSRN is not re-fetched |
| 8 | https://whatworksintrading.substack.com/p/the-rise-and-fall-of-quantopian-lessons + cluster (quantrocket.com/blog/quantopian-shutting-down, en.wikipedia.org/wiki/Quantopian) | 2026-09-08 | secondary | whether a mineable Quantopian archive survives | **YIELDED A NEGATIVE, which is the finding.** Shut Nov 2020; **historical backtests deleted**, weeks to export; team acquired by Robinhood; the fund returned investor money in early 2020 having underperformed. *"You can't crowdsource alpha."* **No mineable corpus exists** |
| 9 | https://github.com/paperswithbacktest/awesome-systematic-trading — `README.md` (raw) | 2026-09-08 | **claims (vendor, unaudited)** | a large-N replication corpus | **YIELDED, verbatim.** **4,843** papers coded and run over full history; **median replication Sharpe 0.37**; **48% clear t = 1.96**; median test window **34 years**; **median beta +0.17 to S&P 500, median IR 0.21 net of it**; and *"no measurable decay after publication"* across 2,838 papers — **which contradicts McLean & Pontiff and favours the vendor; flagged, not adopted** |
| 10 | https://paperswithbacktest.com/ | 2026-09-08 | claims (vendor) | methodology and access terms | **PARTIAL.** *"reads what the code really measures — look-ahead, survivorship, costs — then deflates the Sharpe by the trials spent"*; example card *"Sharpe 1.51 → 1.74 · deflated 0.71"*. **Code free via pip; the 1.04 TB of data is $50/month.** Not purchased, no account created |
| 11 | https://paperswithbacktest.com/wiki | 2026-09-08 | claims (vendor) | the replication methodology itself | **NOTHING.** An index of article titles (*"the seven sins of backtesting"*, CPCV), no data source, no cost convention, no trial count. **The audit claim is itself unaudited.** Logged so it is not re-fetched |
| 12 | https://arxiv.org/abs/2603.20319 (Yin, Miki, Lesnichenko & Gural, 2026-03-19) | 2026-09-08 | **secondary (paper)** | whether engines agree with each other | **YIELDED L-3.** 5 open-source engines × 15 strategies × 180 S&P 500 stocks. **Zero-cost divergence 0.000%**; with costs, **up to 3.71%** on high-turnover rotation, Spearman **ρ = 0.93** with cost intensity. **Seven previously undocumented defects across three engines, five failure modes, all in transaction-cost logic.** All engines agree on the sign of every metric |
| 13 | https://arxiv.org/abs/2603.19380 (Ranse, 2026-03-19) | 2026-09-08 | **secondary (paper)** | a magnitude for survivorship bias | **YIELDED.** NIFTY Smallcap 250, **1,437 stocks, 2016–2025**: survivor-only backtesting overstates annual return by **4.94 pp (23.3%)** and Sharpe by **0.097 (9.1%)**. Emerging-market small caps, so an **upper** bound for a US large-cap universe; used only to size L-7 |
| 14 | https://github.com/robcarver17/pysystemtrade | 2026-09-08 | **primary (repo)** | a live-traded open-source CME futures system | **PARTIAL from the README** — framework description and a disclaimer only; 3.5k stars, 4,842 commits. No costs, no sample, no performance in the README |
| 15 | https://raw.githubusercontent.com/robcarver17/pysystemtrade/master/docs/instruments.md | 2026-09-08 | **primary (docs)** | the cost model | **YIELDED the importable rule.** Costs in **SR units**; a **"bad market"** exceeds **0.01 SR units per trade**; a **"speed limit on trading costs"** can leave an instrument with *"no trading rules that are cheap enough."* Spreads re-estimated from sampled bid-ask **and executed trades**, auto-flagged at >30% divergence |
| 16 | https://github.com/robcarver17/pysystemtrade/tree/master/docs | 2026-09-08 | primary | locating the cost documentation | Directory listing only. **`docs/costs.md` does not exist — that URL returns 404.** Logged so it is not re-attempted |
| 17 | https://qoppac.blogspot.com/2025/04/annual-performance-update-returneth.html | 2026-09-08 | **primary (author's own live record)** | live vs backtest for #14 | **YIELDED the rarest artefact in the review.** Year 11, to 2025-04-05: **−16.3%** (futures MTM −14.5%, margin −1.0%, **commissions −0.29%, slippage −0.56%**, fees −0.05%) — *"my worst ever."* Long-run **SR 0.76 (rf = 0) at 16.8% s.d.** vs AHL/SG CTA **0.42–0.45** at 10.7%/8.9%. **All-in costs ≈ 89–93 bp/yr.** **He does not state a live-vs-backtest variance**, which is the one thing missing |
| 18 | https://github.com/nkaz001/hftbacktest | 2026-09-08 | **primary (repo)** | a latency- and queue-aware backtester on CME | **YIELDED A NEGATIVE.** Models feed latency, order latency and queue position — the correct construction — but supports **Binance Futures and Bybit only. No CME.** Fee handling not documented on the landing page |
| 19 | https://www.freqtrade.io/en/stable/lookahead-analysis/ | 2026-09-08 | **primary (docs)** | automated look-ahead detection | **YIELDED L-8, the positive counterexample.** Baseline backtest, then per-signal re-runs on truncated slices, diffing indicator values and signal timing. Caveats verbatim: *"can only verify / falsify the trades it calculated and verified"* (false negatives on untriggered signal types); `custom_entry_price()` with limit orders *"causing false positives"*; FreqAI targets falsely flagged. **Portable to our runners** |
| 20 | https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html | 2026-09-08 | **primary (docs)** | fill timing and cost model | **YIELDED L-5.** *"If `trade_on_close` is `True`, market orders will be filled with respect to the current bar's closing price instead of the next bar's open"* — **default `False`, which is correct.** `commission` accepts `(fixed, relative)` **or a callable `func(order_size, price) -> float`**, so per-contract futures cost is expressible. **Intrabar SL-vs-TP ordering is NOT documented** |
| 21 | https://www.backtrader.com/docu/cerebro/cheat-on-open/cheat-on-open/ + community threads (topic/1048, topic/726) | 2026-09-08 | **primary (docs) + claims (forum)** | same-bar fill semantics | **YIELDED L-4.** `cheat_on_open` added in 1.9.44.116 *"for people who go all-in, having made a calculation after the close of a bar, but expecting to be matched against the open price."* Separate `next_open`/`nextstart_open` entry points make it explicit. Forum consensus: *"The first approach with cheat_on_open has look-ahead bias in it"* |
| 22 | https://github.com/polakowo/vectorbt — issue #780, discussion #188, `portfolio/base.py`, https://vectorbt.dev/api/portfolio/base/ | 2026-09-08 | **primary (docs + issues)** | default signal/fill alignment | **YIELDED L-6.** Docs warn signalling must occur *"at the very end of the bar … otherwise you may expose yourself to a look-ahead bias."* Stops resolve off the first close because two orders cannot share a tick. **Issue #780: the engine sometimes uses the next timeframe's open rather than the current close** |
| 23 | https://zipline.ml4trading.io/bundles.html + quantopian/zipline issues #2145, #2485 | 2026-09-08 | **primary (docs + issues)** | the default data bundle's biases | **YIELDED L-7.** Default `quandl` bundle = Quandl **WIKI**, **not updated since 2018-04-11**, and contains **no delisted names**; #2485 is users asking how to add them. Docs still describe it as *"a useful starting point"* |
| 24 | https://quantpedia.com/screener/ | 2026-09-08 | claims (vendor) | futures intraday strategies with Sharpe, sample and source | **BLOCKED — PAYWALLED.** *"Unlock 1000+ strategies."* Free surface shows **performance % and volatility %, not Sharpe and not t-statistics**. The only intraday row visible was crypto (#0753, Bitcoin overnight seasonality). Not subscribed |
| 25 | https://quantpedia.com/pod-strategy-rebalance/intraday/ | 2026-09-08 | claims (vendor) | the intraday sub-list | **NOTHING.** Redirects to promotional content; no strategy rows rendered without login. Logged so it is not re-attempted |
| 26 | https://quantpedia.com/continuous-futures-contracts-methodology-for-backtesting/ | 2026-09-08 | **secondary (methodology)** | quantified roll-convention risk | **PARTIAL — and the gap is the finding (L-9).** Enumerates 4 roll dates × 4 adjustments and shows the **same Lean Hogs strategy** under two conventions producing charts that *"seem to be representing different commodities."* **No Sharpe, no return, no number of any kind. `NOT PUBLISHED`** |
| 27 | https://github.com/wilsonfreitas/awesome-quant | 2026-09-08 | secondary (index) | strategy candidates | **YIELDED A NEGATIVE.** A **tool index**. No backtested results, no performance metrics, no futures intraday strategy. Useful for engines only, as the brief anticipated |
| 28 | https://github.com/wangzhe3224/awesome-systematic-trading | 2026-09-08 | secondary (index) | strategy candidates | **YIELDED A NEGATIVE for candidates**, positive for tooling: located hftbacktest (#18), nautilus_trader, vectorbt. Curation criteria are *"good coding style"* and *"reasonable test coverage"* — **not backtest validity** |
| 29 | https://github.com/topics/intraday (Python, by stars and by updated); https://github.com/topics/backtesting; https://github.com/search?q=zarattini+intraday+momentum+replication | 2026-09-08 | claims (repo listings) | the population of intraday repos | **NOTHING NEW beyond #1–#4.** Top intraday-tagged repos are crypto orderbook tooling (34★), an RL gym (28★), and Indian-market ORB/VWAP/EMA scripts. **Not one states a cost convention or a null in its description.** This is what the retail repo tier looks like at scale |
| 30 | https://www.quantitativo.com/p/intraday-momentum-for-es-and-nq | 2026-09-08 | claims | ES/NQ replication numbers | **ALREADY LOGGED BY LANE 13 (its source #20).** No new facts. Recorded here only to mark the overlap so the next session does not treat it as fresh |

**Negative and blocked results, per schema §4:** #7 (SSRN 403 — recovered via index, do not re-fetch),
#11 and #16 (page/file does not carry the content, do not re-fetch), #24 and #25 (Quantpedia
paywalled, not subscribed), #8, #18, #27, #28 (negatives that *are* the finding), #26 and L-9
(`NOT PUBLISHED` — roll-convention magnitude), #29 (the repo tier at scale yields nothing screenable),
#30 (overlap with lane 13).

**Searches run that produced no new source, so they are not repeated:** a GitHub replication of Gao,
Han, Li & Zhou's market intraday momentum (**none exists**); a CME-capable queue-aware open-source
backtester (**none** — hftbacktest is crypto-only); a surviving mirror of the Quantopian algorithm
archive (**deleted at shutdown**); any open-source futures backtest reporting **per-trade MAE or
intraday equity** (**none, in any repository read**).

**On-page solicitation met and not acted on, per the safety brief:** paperswithbacktest's *"$1 in
agent credits, no card required"* free tier and $50/month data plan; Quantpedia's *"Get
subscription"* gates; GitHub's sign-in and star prompts. **No repository was cloned, downloaded or
executed. No account was created, no credential entered, no payment page opened, no affiliate link
followed.** No page carried an instruction addressed to an automated reader; the directives were
ordinary commercial solicitation and standard site chrome.
