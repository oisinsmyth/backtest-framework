# Data purchase proposal

**Costed 2026-08-29** against [the twelve-lane free-data search](00-SYNTHESIS.md).
Supersedes `13-ACQUISITION-PROPOSAL.md`, which mis-read what a Databento subscription buys.

---
## 1. The governing principle

**Historical data is a stock, not a flow.** A subscription buys new bars, corrections, and things
you did not think to pull. Once sixteen years are on disk they stay on disk.

**So the correct shape is: subscribe, strip-mine, cancel** — and re-subscribe for a month if a
future study needs fresh data. This is a one-off cost, not a running one.

**The optimisation is therefore data-per-pound on a single pass**, with three constraints:
1. **Do not buy what Alpha Vantage already serves.**
2. **Do not buy what has no plausible future study** — speculative volume is how you end up with
   500 GB and no result.
3. **Do not buy the expensive instrument for a question a cheap one answers first.** This is the
   constraint that moved tick data from a $145 line item to a conditional step (§7), and it is the
   one most easily lost when a dataset is intrinsically interesting.

---

## 2. What we already hold — measured, not estimated

| | coverage |
|---|---|
| 57 ETFs, daily | 16.8 y (2009–2026), split and dividend adjusted |
| 57 ETFs, 15-minute | **regular hours only**, 2018–2026 |
| SPY/QQQ/IWM/DIA, 15-minute | **extended 04:00–19:45 ET**, 2010–2026 |
| **1,573 US single names, daily** | **2010–2026, 35.7% dead**, residual breadth **74** |
| 60-ETF instrument holdout, wide universe (~486) | daily |
| Crypto | 63 coins daily, 34-coin book, Binance 15m/30m/1h |

| | size | files |
|---|---:|---:|
| `data/fixtures` | 0.28 GB | 53 |
| `data/raw` | 0.90 GB | 11,282 |
| `.git` | 0.33 GB | 367 |
| **whole project** | **~2.0 GB** | |

---

## 3. What Alpha Vantage serves, and therefore what we must NOT buy

- **US equities and ETFs, daily**, adjusted, deep history
- **US equities and ETFs, intraday** 1m–60m, **including extended hours 04:00–20:00**, month by
  month, back to ~2005
- **`LISTING_STATUS`** — active *and* delisted rosters. **This is what made D252's 35.7%-dead
  universe possible**, and no market-data vendor replaces it
- **`SPLITS` and `DIVIDENDS`** — without which [D226's +1,772% unadjusted split bar](00-SYNTHESIS.md)
  recurs
- **Options** (per the principal), FX daily, crypto daily, commodity macro series

**Alpha Vantage is therefore retained, not replaced.** Databento's plans cover
**CME/CBOT/NYMEX/COMEX only** — equities and OPRA are separate products at every tier, so a
subscription would not have bought equity coverage even if we wanted it.

**One dataset sits outside both vendors and costs nothing: the CFTC Commitment of Traders report** —
weekly institutional positioning, back to 1986, US-government public domain and therefore
**committable to the repo, unlike anything from CME.** It is rung 1 of §7.5 and step 0 of §11. **It
appeared in none of the twelve free-data lanes**, which searched for price data rather than
positioning data.

**One gap to close on the month already paid for:** extended-hours 15-minute for **all 57 ETFs**.
D259 fetched only four, and **the existing 57-ETF fixture discarded the extended session at build
time after the slices had already been paid for.** ~11,400 requests, ~3 hours, ~600 MB.

---

## 4. The plan-structure finding that sets the budget

Databento's tiers gate **schema depth**, not volume:

| tier | L0 (OHLCV 1s/1m/1h/1d, definition, statistics) | L1 (trades, MBP-1, TBBO, BBO) | L2/L3 |
|---|---|---|---|
| **Usage-based ($0/mo)** | **16+ years** | last 12 months | last 1 month |
| Standard ($199/mo) | 16+ years | 16+ years | last 1 month |
| Unlimited ($4,500/mo) | 16+ years | 16+ years | **16+ years** |

**Every schema this proposal wants is reachable on the usage-based tier**, so **no subscription is
required**. That corrects the earlier proposal, which recommended $199 Standard on the mistaken
assumption that a subscription included volume.

**Rate, derived rather than assumed.** Databento does not publish the per-schema $/GB table, but its
API reference publishes two worked examples of *the same query*:

- `get_billable_size(GLBX.MDP3, ESM2, trades, 2022-06-06 → 2022-06-10T12:10)` → **99,219,648 bytes**
- `get_cost(…same…)` → **$2.587353944778**

`99,219,648 / 2^30 = 0.0924055 GiB`; `2.587353944778 / 0.0924055 =` **exactly $28.00/GiB** — which
also proves their "GB" means 2^30. **One inferred step:** that `ohlcv-1m` bills at the same rate as
`trades`. The published OPRA `list_unit_prices` example prices `trades`, `ohlcv-1s` and `ohlcv-1m`
**identically**, and it is confirmable in 30 seconds post-signup. **The conclusion survives a 2x
error.**

**Derived unit costs.** `OhlcvMsg` is a fixed 56 bytes; `1,380 min/day x 252 days = 347,760` bars per
symbol-year is an upper bound, since no bar prints for a minute without a trade.

| schema | per symbol-year | why |
|---|---:|---|
| **`ohlcv-1m`** | **$0.51** | 19.5 MB |
| `ohlcv-1s` | **$30.60** | 60x the records |
| **`trades`** | **$145.33** | 5.19 GiB — measured from the worked example, not extrapolated |

**The credit is $125 and expires six months after signup.**

---

## 5. What to buy — the 1-minute complex

**`GLBX.MDP3`, schema `ohlcv-1m`, `stype_in="continuous"`, full ~23-hour Globex session.**

| group | symbols | years | symbol-years | cost |
|---|---|---:|---:|---:|
| **equity index** | ES, NQ, YM | 16 | 48.0 | $24.48 |
| equity index | RTY | 9 | 9.0 | $4.59 |
| **CME crypto** | BTC, MBT | 8.5 | 17.0 | $8.67 |
| energy | CL, NG | 16 | 32.0 | $16.32 |
| metals | GC, SI, HG | 16 | 48.0 | $24.48 |
| rates | ZB, ZN, ZF | 16 | 48.0 | $24.48 |
| FX | 6E, 6J, 6B | 16 | 48.0 | $24.48 |
| **micros** | MES, MNQ, M2K, MYM | 7 | 28.0 | $14.28 |
| **ags** | ZC, ZS, ZW | 16 | 48.0 | $24.48 |
| livestock | LE, HE | 16 | 32.0 | $16.32 |
| **total** | **26 symbols** | | **358.0** | **$182.58** |

**Plus `definition` and `statistics` schemas** — negligible in size, and **`definition` is not
optional**: it carries the roll calendar and contract metadata that make a correct continuous series
possible.

**Raw volume: ~6.8 GB.** Compressed, ~3 GB.

### Why each group is on the list

**Equity index (ES/NQ/YM/RTY).** The venue's liquid contracts, and the direct object of every prop
study. **RTY reaches only 9 years because the E-mini Russell moved to CME in 2017** — market
structure, not a vendor limit, confirmed independently in two research lanes.

**CME crypto (BTC/MBT) — the session bridge.** These are **genuine Globex contracts that ran the
exact ES session template from 2017-12-17 to 2026-05-28**, verified empirically: 2,117 daily bars
over that span show **zero Saturday or Sunday bars**. CME took crypto futures to 24/7 on 2026-05-30,
closing the window. **Real session breaks, real roll, real settlement** — a far better structural
proxy than any perpetual, and it costs $8.67.

**Micros (MES/MNQ/M2K/MYM) — these overturn a committed finding.** ES has a **$50 multiplier**; at an
S&P of 6,000 one contract controls **$300,000** of notional. **MES has a $5 multiplier — $30,000, one
tenth.** Same underlying, exchange, session and settlement.

> On a $50,000 prop account **one ES contract is already six times the account.**
> [D260](../../decisions/D260-the-vol-targeted-overnight-hold.md) concluded the size clearing the 2%
> daily limit is **0.21x of a full position** — and 0.21 of an ES contract does not exist. Contracts
> are integers. **D260 may therefore have measured the granularity of the instrument rather than the
> quality of the edge.** With MES, 0.21x is expressible as roughly two contracts.

Micros launched **May 2019**, so ~7 years. Their liquidity is thinner and the *relative* spread
wider, which is itself worth measuring rather than assuming.

**And micros carry a second payload that was not the reason for buying them.** Because MES exists
so retail can trade a tenth-size contract, **the MES-to-ES notional ratio is an economically
enforced read on retail participation** — which makes this $14.28 line the cheapest available test
of the smart-money hypothesis, at roughly **3x the statistical power of $145 of tick data.** See
**§7.4–7.5**. The micros justify their price twice over.

**Ags and livestock (ZC/ZS/ZW/LE/HE) — bought for correlation, not for a strategy.** Their drivers
are weather, planting and harvest cycles, export demand, biofuel mandates and herd dynamics. **None
of those is the equity risk premium, the level of rates, or the dollar.**

> [D261](../../decisions/D261-the-index-spread-pair.md) measured effective breadth of **3.00** for a
> diversified futures complex against **1.17** for equity indices alone. Since `IR ~ IC x
> sqrt(breadth)`, lifting effective breadth from 3 to 4.5 is worth **1.22x** on any edge,
> permanently and for free.

**The earlier exclusion of ags was inconsistent** — metals and FX were admitted on exactly this
argument, and **grains are less correlated with equities than metals are.** Their complication is
real: physical delivery, pronounced seasonality, and a roll structure messier than equity index,
where the front month is not always the liquid one. **Roll handling needs more care there.**

**Energy, metals, rates, FX.** Same breadth argument, plus these are what a prop firm actually
offers beyond the indices.

---

## 6. Quote-level snapshots — the highest-value item on the list

**`bbo-1m` (or `bbo-1s` if the 1-minute variant is unavailable) for ES and NQ, 12 months.**
Approximately **$1–2**, since it has the same record cardinality as `ohlcv-1m`.

**BBO means Best Bid and Offer** — the highest price anyone will pay and the lowest anyone will sell
at, at that instant. **OHLCV tells you where trades happened. BBO tells you what price was
available.** The gap is the **spread**, and it is a cost paid on every round trip, entirely separate
from commission.

**Why this matters more than any individual symbol on the list:**

Every futures conclusion in this programme rests on **~0.2 bp round-turn commission**. That number
reopened [D247's shorts under R12](../../decisions/D247-the-short-side-at-fifteen-minutes.md), voided
the ETF cost wall's applicability, and made [C2 and C3](../../BOOK_PROP.md) worth screening at all.

**But the ES bid-ask is typically one tick = 0.25 index points.** At a $50 multiplier that is
**$12.50 per contract** against ~$300,000 notional — roughly **0.4 bp per side crossed.**

> **If that holds, crossing the spread costs about four times the commission, and the true
> round-trip cost is nearer 1.0 bp than 0.2 bp.**

That would not overturn everything — futures would remain ~4x cheaper than ETFs rather than 20x —
**but it would move several marginal conclusions, and four separate studies have leaned on the 0.2
figure without anyone measuring it.**

Twelve months is ample: a spread distribution is a market-structure fact, not a slow-moving edge. It
should be characterised **by time of day, by volatility regime, and by contract — including
overnight, where spreads widen and where C1 lives.**

---

## 7. The smart-money question — a staged ladder, and why tick comes last

**This section replaces an earlier one that proposed `trades` for ES, 12 months, $145.33. Tick is
now DEFERRED, and the reasoning is worth keeping because it is not a cost argument.**

### 7.1 Two corrections, in order

**First, the price.** In discussion I put tick at "about $8 per symbol-year". The measured figure
from Databento's own worked example is **$145.33 per symbol-year** — **wrong by ~18x**. ES+NQ for
two years is **$581**, not $32.

| scope | symbol-years | cost | volume |
|---|---:|---:|---:|
| ES, 1 year | 1 | $145 | 5.2 GiB |
| ES + NQ, 2 years | 4 | $581 | 20.8 GiB |
| *ES, 15 years* | *15* | *$2,180* | *78 GiB* |

**Second, the case for buying it.** The argument that reopened tick was that **order flow is one of
the few signal families with the shape hurdle P wants** — many small observations, high hit rate,
tight tails — where every construction this programme has closed was directional and failed on
shape. **That argument still stands.** What changed is that a cheaper instrument answers the same
question better, and generic order-flow mining is, as originally judged, the most heavily contested
domain in the market.

### 7.2 The narrow question worth asking

Not *"does order flow predict returns"* — that is HFT's home ground. The narrow question is:

> **Can institutional participation be separated from retail participation, and does the separation
> carry information at an hours-to-days horizon?**

That is a **detector**, not a speed race. Nothing about it requires being fast; it requires being
able to tell two populations apart.

### 7.3 The levers on tick, measured — all three are weak

**Session filtering saves ~13%, not ~57%.** Measured on `index_extended_15m_raw`, 2010–2026:

| | volume outside 09:30–16:00 | bars outside |
|---|---:|---:|
| **SPY** | **12.82%** | 58.8% |
| QQQ | 9.85% | 56.8% |
| IWM | 10.45% | 53.5% |
| DIA | 5.21% | 47.3% |

**Databento bills bytes, and bytes track TRADES, not hours.** Cutting 57% of the clock removes 13%
of the tape: ES RTH-only is **~$126 instead of $145**. *(Caveat: this is equities on a 04:00–19:45
window, not futures on 23 hours. The futures overnight share is likely higher, but not by enough to
change the conclusion.)*

**No size filter exists.** There is no server-side predicate for "trades ≥ 50 lots", and the small
trades are needed anyway to establish what "large" means. **`tbbo` is MORE bytes than `trades`**,
not fewer, so the schema cannot be traded down either.

**Shortening the span breaks the study before it saves the money.** Standard error of an annualised
Sharpe over `T` years is `~sqrt(1/T)`:

| span | MDE on Sharpe, 95% one-sided |
|---|---:|
| 3 months | **3.29** |
| 6 months | **2.33** |
| **1 year** | **1.65** |
| 2 years | 1.16 |
| 3 years | 0.95 |
| 7 years | 0.62 |
| 16 years | 0.41 |

**At ES-only-for-one-year, a Sharpe of 1.65 is required to distinguish the signal from zero. $145 is
already the floor, not an opening price** — and [D227](../../decisions/README.md) was abandoned on
precisely this arithmetic, where halving a sample lifted the MDE onto the effect size.

**And breadth is priced badly for this idea.** Effective instruments for a pair is `2/(1+rho)`:

| pair | rho | effective instruments | $ per unit of breadth |
|---|---:|---:|---:|
| ES + NQ | +0.90 | **1.05** | $276 |
| ES + YM | +0.95 | 1.03 | $284 |
| ES + CL | +0.35 | 1.48 | $196 |
| ES + GC | +0.10 | 1.82 | $160 |
| ES + ZN | −0.30 | **2.86** | **$102** |

**ES+NQ costs $291 to move effective breadth from 1.00 to 1.05.** ZN is six times better value per
unit — **but it is exactly where the detector's premise collapses.** Treasury futures flow is almost
entirely institutional (dealers, pensions, central banks), so there is no retail population to
separate against. **The premise is strongest precisely where the breadth is worst.**

### 7.4 The decisive argument, and it is not about cost

**A trade-size threshold is a guessed cut, and execution algorithms exist specifically to defeat
it.** Hiding institutional size by slicing a parent order into child orders that look retail is the
entire job of a VWAP or implementation-shortfall algo. **The adversary in this game has been
actively attacking the detector's core assumption for twenty years.**

**That attack does not work on the contract choice.**

**MES exists so retail can trade a $30,000 contract instead of a $300,000 one.** Ten MES cost
roughly **3x the round-turn fees** of one ES for identical exposure, plus far worse aggregate spread
impact across ten times the contracts. **Anyone trading size uses ES, and that is not a preference,
it is arithmetic.** So the micro/mini split is an **economically enforced partition of the
participant pool**, not a heuristic:

```
micro notional share(t) = MES_vol(t) / ( MES_vol(t) + 10 * ES_vol(t) )
```

Rising micro share means retail crowding in. **Fading the retail crowd IS the smart-money signal** —
the same hypothesis the tick version tests, measured on a partition nobody can slice their way
across.

### 7.5 The ladder, cheapest first

**Rung 1 — CFTC Commitment of Traders. FREE, and it can be committed.**

Weekly, **back to 1986**, published by a US government agency and therefore **public domain** — so
unlike every CME product in this proposal, **the COT series is not subject to the redistribution
constraint in §12 and may live in the repo.** It reports open interest split into **commercial
(hedgers), non-commercial (managed money), and non-reportable (small traders)**, per contract, for
every symbol on the buy list.

**This is the official institutional-positioning series.** It is weekly and lagged three days, so it
is a slow positioning read rather than a tape read — a different animal from flow, and
complementary to it. **It surfaced in none of the twelve free-data lanes**, which searched for price
data.

**Rung 2 — the micro/mini notional ratio. $14.28, and ALREADY on the buy list.**

| | tick size-buckets | **micro/mini ratio** |
|---|---|---|
| cost | $145.33 | **$14.28 — already budgeted** |
| instruments | 1 (ES) | **4 pairs** — ES/MES, NQ/MNQ, RTY/M2K, YM/MYM |
| span | 1 year | **7 years** (MES launched May 2019) |
| effective instruments | 1.00 | **1.13** at rho ≈ 0.85 |
| effective T | 1.0 yr | **7.9 yr** |
| **MDE on Sharpe** | **1.65** | **0.59** |
| defeated by order slicing | **yes** | **no** |

**Ten times cheaper and roughly three times better powered, on the same hypothesis.**

**Its honest weakness:** it is coarse. Per-minute *participation share*, not per-trade aggressor
side — it cannot see absorption, and it cannot see who crossed the spread. **It is a weaker
instrument answering a better-posed question with far more power.**

**Rung 3 — open interest against volume. FREE with the purchase**, in the `statistics` schema (L0).
Rising price with rising OI is new positioning; rising price with falling OI is short covering.
**Conviction versus churn** — the same question again, at daily resolution, across all 26 symbols
and 16 years.

**Rung 4 — tick, CONDITIONAL.** Buy `trades` **only if rung 2 or rung 3 shows something**, at which
point it is a refinement of a live result rather than a punt, and worth **2–3 years rather than 1**
($291–$436). **If rungs 1–3 come back empty, that is meaningful evidence against the premise itself,
bought for $14 instead of $145.**

### 7.5b Amendment — cheaper tick routes, and what they do to the argument above

**Added after an r/algotrading sweep (four threads, 2022–2026). Two leads attack §7.3's power
argument directly, and one of its two legs does not survive.**

| route | claimed price | span |
|---|---|---|
| **Sierra Chart + Denali feed** | **~€40/mo** — download, export to text, cancel | **15 years, many symbols** |
| **MarketTick** | **$79** | **10 years, ES + NQ, L2** |

**§7.3 costed a ONE-YEAR sample because $145.33/symbol-year made anything longer unaffordable.
Affordability was the binding constraint, and these routes remove it:**

| span | MDE on Sharpe (95%, 1-sided) |
|---|---:|
| 1 yr — what §7.3 costed | **1.65** |
| 3 yr | 0.95 |
| **10 yr — MarketTick** | **0.52** |
| **15 yr — Sierra** | **0.42** |

**At 10–15 years the power objection largely dissolves. MDE 0.52 is workable, and this proposal
should not pretend otherwise.**

**What survives is §7.4, which price cannot touch:** a trade-size threshold is a guessed cut, and
hiding institutional size behind retail-looking child orders is the entire purpose of an execution
algo. The MES/ES partition is economically enforced and cannot be sliced across. **So the ladder's
ORDER is unchanged — rung 2 first because it is the better instrument, not because it is the
cheaper one — but the case for putting tick last is now one argument rather than two.**

**Three conditions before either route is bought:**

1. **Both prices are single unverified Reddit comments.** Confirm against the vendor directly.
2. **$79 for ten years of two-symbol L2 is implausible for licensed redistribution** — Databento
   gates L2 depth behind $4,500/mo. **Provenance must be established before purchase**, because §12's
   constraint binds regardless of what a vendor claims.
3. **Sierra's licence forbids redistribution** — the gitignored-cache pattern in §12 covers it, but
   `.scid` export across many symbol-years is **GUI work, plausibly days of it**, and that labour is
   the real price.

**Explicitly excluded:** a Reddit account offering CME data down to MBO through a private group
chat. **That is redistributed licensed exchange data, and no backtest built on it would be
defensible.** Recorded here so the lead is not re-found and re-considered.

### 7.6 If tick is ever bought — the parallel-backtest architecture

**Reduce the tape to per-minute flow features at build time.** Signed volume and trade count per
size bucket, CVD per bucket, large-trade aggressor imbalance, and an absorption proxy (volume per
unit of price range):

| features per minute | derived panel, per symbol-year | share of the 5.19 GiB raw |
|---:|---:|---:|
| 12 float32 | 16.7 MB | 0.30% |
| **20 float32** | **27.8 MB** | **0.50%** |
| 32 float32 | 44.5 MB | 0.80% |

**That is the same order as one `ohlcv-1m` symbol-year (19.5 MB), so it slots into the existing
`(n, T)` panel as extra columns** — same `ragged_panel` loader, same cost model, same matched-count
nulls, same hurdles. Raw trades stay on the external drive purely for re-derivation.

**The constraint to state plainly:** the complex is 26 symbols x 16 years, and the flow panel would
be **1 symbol x 1 year**. Any study touching flow features is a one-symbol one-year study at
effective breadth 1.00, **however much other data sits beside it. The rest of the complex cannot
lend it power.** That is the real reason tick is deferred, **and it is not solved by spending
more.**

---

## 8. What is excluded, and why

| | reason |
|---|---|
| **`ohlcv-1s`** | **$30.60/symbol-year — 60x the 1-minute rate.** ES+NQ over 16 years is **$980**, eight times the entire 1-minute complex. It answers no question we hold; the execution question it might serve is better answered by **`bbo`** at 1/20th the price |
| **`trades` — ALL scopes, deferred not excluded** | **$145.33/symbol-year.** Not price alone: at ES-only-1-year the **MDE is 1.65 Sharpe**, a trade-size cut is **what execution algos are built to defeat**, and the [micro/mini ratio](#75-the-ladder-cheapest-first) tests the same hypothesis for **$14.28 at 3x the power**. Bought only on a positive rung-2 or rung-3 result — see §7 |
| **OPRA options** | Not cost. [D84](../../decisions/D84-options-scoping-writeup.md) scoped it: chain data at **100–1000x volume**, *plus* **6–10 weeks of engine surgery** for expiry and assignment lifecycle, because D45's inner-join alignment silently truncates the whole portfolio at the shortest-lived contract's expiry. **Data without an engine sits unused.** Alpha Vantage also covers options |
| **Equity intraday** | **Alpha Vantage already serves it** — extended hours, back to ~2005. And it is not on Databento's CME plans at any tier |
| **L2 / L3 order book (MBP-10, MBO)** | **Unavailable, not expensive.** Capped at *one month* on every tier below Unlimited ($4,500/mo) |
| **Non-CME venues (ICE, Eurex)** | Separate datasets, not on these plans; prop firms trade CME |
| **Pre-2010 history** | `GLBX.MDP3` begins **2010-06-06**. Does not exist to buy |
| **Calendar-spread instruments** | Constructible from the legs, which is how D261 built its spreads. And equity-index calendar spreads are near-pure rate/dividend plays with little vol |

### Alternative vendors, priced and rejected

**From an r/algotrading sweep of four threads, 2022–2026. Databento is the top-voted answer in every
one of them, which is corroboration rather than a cheaper option.** Priced against **$0.51 per
symbol-year**:

| vendor | claimed price | the same coverage here | verdict |
|---|---|---:|---|
| **Kibot** | ~$150/symbol, 20 yr 1-min, ES *or* NQ | **$10.20** | **14.7x more.** Our 26-symbol complex would be **~$3,900** |
| **FirstRateData** | ~$200 one-off, liquid contracts | $182.58 for **358** symbol-years | more than the entire complex, for a subset |
| **tickmarketdata** | €380, NQ tick | — | 2.6x the whole plan, one symbol |
| **Quandl / Nasdaq CHRIS** | free | — | **dead** — stopped being free for CME data in 2018 |
| **yfinance** | free | — | **killed by our own measurement** (§12): a +2.77% spurious gap and `adjclose` a verbatim copy of `close` on 1258/1258 bars. Reddit independently reports inaccurate weekly closes |
| **Kinetick EOD** (NinjaTrader) | free | — | daily settlements only |
| **QuantConnect** | **free futures data** | — | **free data that cannot leave the platform.** Backtests run in LEAN on their cloud, so taking it means abandoning this engine, the 1,446-test suite, the matched-count and rotation nulls, D228's floor, and offline determinism. **Weeks of rewriting to save $60**, forfeiting the validation stack that is the actual asset |

**The rest of the forum lane is CLOSED, not pending.** r/FuturesTrading, r/quant and
r/systematictrading are deliberately unread: four threads spanning four years converged on one
vendor, priced every alternative above it, and independently reproduced this document's own roll
warning. **After that degree of convergence the expected yield does not justify the effort**, and
leaving the lane open would invite a future session to re-derive the same answer. Recorded in
[lane 01 §5.4](01-reddit-and-forums.md).

**Two confirmations from the same sweep**, both matching what the twelve lanes found independently: a
Databento staff account putting **CME minute bars at 2010-06-06**, and the repeated warning that
**raw per-contract data means you build the continuous series yourself** — which is precisely what
§12 exists for. **Every thread names continuous-contract stitching, not data availability, as the
real difficulty.** Several commenters also report **1-minute bars sufficing for intraday work, with
tick data not changing results** — anecdote, but pointing the same way as §7's ladder.

---

## 9. Storage

| | GB |
|---|---:|
| current project | 2.0 |
| 1-minute complex, raw | 6.8 |
| `bbo-1m`, ES + NQ, 12 months | ~0.03 |
| CFTC COT, full history, all contracts | ~0.05 |
| Alpha Vantage extended-hours top-up | 0.6 |
| derived fixtures, working space, 2x headroom | ~8 |
| **projected total** | **~18 GB** |
| *conditional — `trades`, ES, 12 months (rung 4)* | *+5.2* |
| *conditional — `trades`, ES + NQ, 3 years* | *+31.1* |

**Buy a 1 TB portable NVMe SSD, ~£55–75.** It is ~55x more than the projection needs and is still
the right unit: **it is the cheapest capacity point that is NVMe rather than a spinning disk**, and
it is the only thing on this list that absorbs rung 4 without a second purchase.

**Two specifics that matter:**

1. **NVMe, not a portable hard disk.** Fixtures are read sequentially and decompressed at load; a
   5,400 rpm USB drive would add minutes to every run. A USB 3.2 NVMe unit sustains 1,000+ MB/s.
2. **Put the RAW CACHE on the external drive; keep the git repo on internal storage** if there is
   any room at all. The cache is the bulk (11,282 files today) and is read sequentially; git does
   small random I/O and is much happier internal.

**Only go larger if tick expands past rung 4.** ES `trades` at 15 years is 78 GB and the full
complex ~2.7 TB — **a decision to make when a study needs it**, at which point a 4 TB unit is ~£180.

---

## 10. Total cost

| | |
|---|---:|
| 1-minute complex, 26 symbols, 358 symbol-years | $182.58 |
| `bbo-1m`, ES + NQ, 12 months | ~$2 |
| `definition` + `statistics` (carries open interest — **rung 3**) | negligible |
| CFTC Commitment of Traders (**rung 1**) | **$0** |
| **gross** | **~$185** |
| **less new-user credit** | **−$125** |
| **cash for data** | **~$60** |
| storage — 1 TB portable NVMe | ~$70 |
| Alpha Vantage | $0 extra — a month already paid for |
| **TOTAL, one-off** | **~$130** |

**Recurring: nothing.**

**Deferred, not budgeted:** `trades` for ES at 2–3 years, **$291–$436** — bought only on a positive
result from rung 2 or rung 3 (§7.5). **The smart-money hypothesis is tested for $14.28 before that
question is asked**, and the whole tick line is conditional on the answer.

**The credit is the binding constraint, not the wallet.** At $182.58 the 1-minute complex overruns
the $125 credit by **$57.58**, and every remaining item is $2 or free. **The only decision worth
making at this budget is rung 4, and this proposal recommends not making it yet.**

---

## 11. Sequencing

**Step 0 costs nothing and does not wait for any of the rest.**

0. **Fetch the CFTC Commitment of Traders history** — free, public domain, ~50 MB, no account and
   no purchase. **It is committable**, so it lands in `data/fixtures` under the normal convention
   rather than the gitignored cache. This is rung 1 of §7.5 and it can be screened before a penny
   is spent.
1. **Sign up and confirm the unit price** — `list_unit_prices(dataset="GLBX.MDP3")`. Thirty seconds,
   and it removes the one inferred number in this costing **before any money is spent.**
2. **Alpha Vantage top-up**, on the month already paid for: extended-hours 15-minute for all 57
   ETFs, plus a refresh of every existing fixture.
3. **Buy the drive**, move the raw cache, verify fixtures still load.
4. **Databento pull** — one `batch.submit_job` for the 1-minute complex plus `definition` and
   `statistics`; a second for `bbo-1m`. **No `trades` job.**
5. **Acceptance-test the roll before any study reads the fixture** (§12).
6. **Screen the ladder in order** — COT (rung 1), micro/mini ratio (rung 2), OI-vs-volume (rung 3).
   **Only a positive result there justifies returning for `trades`** (rung 4), which needs no new
   subscription and can be bought at any later date.
7. **Cancel nothing** — usage-based has no subscription to cancel. **Alpha Vantage is a separate
   decision** once the top-up is banked.

**Two traps carried forward from the free-data search, restated because they are cheap to hit:**

- **`stype_in="continuous"` (`ES.c.0`), never `parent`** — `parent` resolves to every outright *plus*
  every calendar spread, which is both wrong and far more expensive.
- **`batch.submit_job`, not streaming** — streaming re-bills on retry; batch bills once and allows
  30 days of free re-downloads.

---

## 12. Acceptance tests — mandatory before any study reads this data

**Yahoo's failure mode is subtle enough that a paid vendor could share it**, and it was only caught
because someone measured rather than assumed:

- `ES=F` close 2024-12-20 **5840.26** → Monday open **6001.75**: a **+161.49 pt (+2.77%) spurious
  gap** on a day SPY moved +0.60%
- **15 of the top 16 ES-vs-SPY divergences over five years fall on quarterly expiries**
- **`adjclose` was a verbatim copy of `close` on 1258/1258 bars**
- Rolling happens **at expiry, not at volume crossover**, so the last 4–5 days of each quarter track
  the dying contract (volume 1,996k → 532k) — **contaminating 7–8% of the sample**

**Therefore, before any study:**

1. **No unexplained single-bar move above a stated threshold** that is not on a documented list of
   real events — the gate D226 needed and D252 reused.
2. **Roll dates align with volume crossover**, not with expiry, and the adjustment is verifiable from
   `definition`.
3. **Session coverage asserted**: ~1,380 minute-bars per weekday, with the 17:00–18:00 ET maintenance
   break present and no other systematic hole.
4. **Cross-check against a free independent source** — Dukascopy `USA500.IDX/USD` on the overlapping
   window, and `Khanhpham1992/es-futures-1m` (2020-11 → 2024-07) where it overlaps.

**`pysystemtrade`'s `roll_calendars_csv` and its `PRICE_CONTRACT`/`FORWARD_CONTRACT`/`CARRY_CONTRACT`
schema is the best free reference implementation of correct stitching**, and is worth reading before
writing ours.

---

## 13. Open unknowns

| | how to resolve | cost |
|---|---|---|
| **`ohlcv-1m` unit price** — the one inferred number | `list_unit_prices` post-signup | 30 s, free |
| Whether **`bbo-1m`** exists as a schema, or only `bbo-1s` | schema list post-signup | free |
| Whether **CME licence fees** apply on top of usage-based historical | the licensing pages would not load for any research lane | ask at signup |
| Fair-use caps on bulk L0 under usage-based | not documented | ask at signup |
| **When MES volume became representative** — the contract launched 2019-05 and ramped, so the early months may not support the §7.5 rung-2 ratio | measure the micro share series itself and set the start where it stabilises | free, post-pull |
| Whether CME's **`statistics`** schema carries open interest at daily resolution for all 26 symbols | schema inspection post-pull | free |
| **CFTC COT contract-code mapping** to our symbols — the report uses its own market codes | one lookup against the CFTC code list | free, no purchase |
| **Polygon.io free futures tier** — a 2025 r/algotrading comment reported one listed as "coming soon". If it shipped with real history it displaces part of §10 | one page load on their pricing page | free. **Low probability a free tier carries 16 years, but the check is one minute** |
| Whether **Sierra Chart's** historical depth actually reaches 2010 for all 26 symbols, and whether `.scid` export can be scripted rather than driven by hand | vendor docs, before any subscription | free — see §7.5b |

**None of these blocks step 0 or step 1**, and step 1 resolves the first two.
