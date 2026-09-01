# Data purchase proposal

**Costed 2026-08-29** against [the twelve-lane free-data search](00-SYNTHESIS.md).
Supersedes `13-ACQUISITION-PROPOSAL.md`, which mis-read what a Databento subscription buys.

---

## 1. The governing principle

**Historical data is a stock, not a flow.** A subscription buys new bars, corrections, and things
you did not think to pull. Once sixteen years are on disk they stay on disk.

**So the correct shape is: subscribe, strip-mine, cancel** — and re-subscribe for a month if a
future study needs fresh data. This is a one-off cost, not a running one.

**The optimisation is therefore data-per-pound on a single pass**, with two constraints:
1. **Do not buy what Alpha Vantage already serves.**
2. **Do not buy what has no plausible future study** — speculative volume is how you end up with
   500 GB and no result.

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

## 7. Tick data — the contested item, and a correction

**`trades`, ES only, 1 year: $145.33, 5.19 GiB.**

**A correction first.** In discussion I priced tick at "about $8 per symbol-year" and quoted "ES+NQ,
two years, ~$32". **Both were wrong by roughly 18x.** The measured figure is **$145.33 per
symbol-year**, so ES+NQ for two years is **$581**, not $32. The proposal below uses the corrected
numbers.

| scope | symbol-years | cost | volume |
|---|---:|---:|---:|
| **ES, 1 year** | 1 | **$145** | 5.2 GiB |
| ES, 2 years | 2 | $291 | 10.4 GiB |
| ES + NQ, 2 years | 4 | $581 | 20.8 GiB |
| ES + NQ, 3 years | 6 | $872 | 31.1 GiB |
| *ES, 15 years* | *15* | *$2,180* | *78 GiB* |

**What it is:** every individual transaction — nanosecond timestamp, price, size, and the aggressor
side (who crossed the spread). Roughly **1–5 million trades per day** for ES.

**What it unlocks, and this is what the original exclusion under-weighted:**

- **Order-flow imbalance** — the running difference between aggressive buying and aggressive selling
- **Volume profile** — where volume concentrated by *price* rather than by time
- **Large-trade detection** — institutional footprints in the size distribution
- **Execution modelling** — how a real order would actually have filled

**The argument that changes the verdict:** every construction this programme has built and closed was
**directional**, and hurdle P rejected three of them on **shape** — negative skew, low hit rate, an
outsized worst trade. **Order flow is one of the few signal families with the shape P wants:** many
small observations, high hit rate, tight tails. *"No current question needs it"* was too narrow a
test, because the absence of a question was itself a consequence of never having had the data.

**The honest counterweight, which is not cost:** order flow is the most intensively mined domain in
finance — it is what co-located HFT firms do. A retail-latency reading starts with a poor prior.
**Though we would not be competing at their horizon**: a flow signal held for hours is a different
game from one held for microseconds, and the crowding argument is much weaker there.

**Recommendation: ES only, most recent 12 months, $145.** Not fifteen years — **order-flow
relationships track market structure, and 2015's book is not 2026's.** One symbol is enough to
establish whether anything is there; if it is, extending is cheap relative to having learned it.

**This single item is 43% of the total spend and 46% of the storage.** It is the one line worth
deciding deliberately rather than by default.

---

## 8. What is excluded, and why

| | reason |
|---|---|
| **`ohlcv-1s`** | **$30.60/symbol-year — 60x the 1-minute rate.** ES+NQ over 16 years is **$980**, eight times the entire 1-minute complex. It answers no question we hold; the execution question it might serve is better answered by **`bbo`** at 1/20th the price |
| **`trades` beyond ES 1 year** | $145/symbol-year. Extending is cheap **once we know there is something there** — buying fifteen years first is the wrong order |
| **OPRA options** | Not cost. [D84](../../decisions/D84-options-scoping-writeup.md) scoped it: chain data at **100–1000x volume**, *plus* **6–10 weeks of engine surgery** for expiry and assignment lifecycle, because D45's inner-join alignment silently truncates the whole portfolio at the shortest-lived contract's expiry. **Data without an engine sits unused.** Alpha Vantage also covers options |
| **Equity intraday** | **Alpha Vantage already serves it** — extended hours, back to ~2005. And it is not on Databento's CME plans at any tier |
| **L2 / L3 order book (MBP-10, MBO)** | **Unavailable, not expensive.** Capped at *one month* on every tier below Unlimited ($4,500/mo) |
| **Non-CME venues (ICE, Eurex)** | Separate datasets, not on these plans; prop firms trade CME |
| **Pre-2010 history** | `GLBX.MDP3` begins **2010-06-06**. Does not exist to buy |
| **Calendar-spread instruments** | Constructible from the legs, which is how D261 built its spreads. And equity-index calendar spreads are near-pure rate/dividend plays with little vol |

---

## 9. Storage

| | GB |
|---|---:|
| current project | 2.0 |
| 1-minute complex, raw | 6.8 |
| `bbo-1m`, ES + NQ, 12 months | ~0.03 |
| **`trades`, ES, 12 months** | **5.2** |
| Alpha Vantage extended-hours top-up | 0.6 |
| derived fixtures, working space, 2x headroom | ~8 |
| **projected total** | **~23 GB** |

**Buy a 1 TB portable NVMe SSD, ~£55–75.** It is 40x more than the projection needs and is still the
right unit: **it is the cheapest capacity point that is NVMe rather than a spinning disk.**

**Two specifics that matter:**

1. **NVMe, not a portable hard disk.** Fixtures are read sequentially and decompressed at load; a
   5,400 rpm USB drive would add minutes to every run. A USB 3.2 NVMe unit sustains 1,000+ MB/s.
2. **Put the RAW CACHE on the external drive; keep the git repo on internal storage** if there is any
   room at all. The cache is the bulk (11,282 files today) and is read sequentially; git does small
   random I/O and is much happier internal.

**Only go larger if tick expands.** ES `trades` at 15 years is 78 GB and the full complex ~2.7 TB —
**a decision to make when a study needs it**, at which point a 4 TB unit is ~£180.

---

## 10. Total cost

| | |
|---|---:|
| 1-minute complex, 26 symbols, 358 symbol-years | $182.58 |
| `bbo-1m`, ES + NQ, 12 months | ~$2 |
| **`trades`, ES, 12 months** | **$145.33** |
| `definition` + `statistics` | negligible |
| **gross** | **~$330** |
| **less new-user credit** | **−$125** |
| **cash for data** | **~$205** |
| storage — 1 TB portable NVMe | ~$70 |
| Alpha Vantage | $0 extra — a month already paid for |
| **TOTAL, one-off** | **~$275** |

**Without tick: ~$130 total** ($60 data + $70 drive).

**Recurring: nothing.**

---

## 11. Sequencing

1. **Sign up and confirm the unit price** — `list_unit_prices(dataset="GLBX.MDP3")`. Thirty seconds,
   and it removes the one inferred number in this costing **before any money is spent.**
2. **Alpha Vantage top-up first**, on the month already paid for: extended-hours 15-minute for all 57
   ETFs, plus a refresh of every existing fixture.
3. **Buy the drive**, move the raw cache, verify fixtures still load.
4. **Databento pull** — one `batch.submit_job` for the 1-minute complex plus `definition` and
   `statistics`; a second for `bbo-1m`; a third for `trades` if taken.
5. **Acceptance-test the roll before any study reads the fixture** (§12).
6. **Cancel nothing** — usage-based has no subscription to cancel. **Alpha Vantage is a separate
   decision** once the top-up is banked.

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

**None of these blocks step 1**, and step 1 resolves the first two.
