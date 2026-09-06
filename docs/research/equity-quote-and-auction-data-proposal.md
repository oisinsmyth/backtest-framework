# Equity quote and auction data: a proposal, not a purchase

**Nothing has been purchased and no key exists on this machine.** Every figure below is an estimate
produced offline by [`scripts/d364_databento_equity_plan.py`](../../scripts/d364_databento_equity_plan.py),
which imports its arithmetic from [`scripts/fetch_databento.py`](../../scripts/fetch_databento.py)
and cannot reach the network. Nothing here is a book entry ([R8](../RULES.md#r8)).

Companion: [`docs/databento_api.md`](../databento_api.md) · futures costing:
[`research/futures-data/data-purchase-proposal.md`](futures-data/data-purchase-proposal.md)

## 1. What the two jobs answer that OHLC cannot

The whole cost stack here is built on daily OHLC. D285's Corwin-Schultz estimator infers a spread
from the high-low range; D363's PUB and PB lines are two windowings of that inference. **The
estimator has never been checked against a quoted spread**, because no quote has ever been in this
repo. Nor has any auction print: the fixture's "open" and "close" are a daily vendor's fields, and
whether an MOO order would have printed at that open is a question the fixture cannot answer.

| job | schema | what it settles |
|---|---|---|
| **1. L1 quotes** | `mbp-1` | the *level* of the spread on the names and days this book holds — the number D285 flagged (a guessed 15 bp/side bar missed the held names' 33.8 by 0.65) and that D363's four cost lines still only estimate |
| **2. trades** | `trades` | the *auction print* at the open and close, with size — whether the fixture's open is the auction price, and how much went off in it |

`mbp-1` is named from the doc, not guessed: [`databento_api.md:138`](../databento_api.md) lists the
L1 tier as "trades, MBP-1, TBBO, BBO". A subsampled `bbo-1s` would be far cheaper, but
[`:248`](../databento_api.md) records that whether its 1-minute sibling exists is **still unknown**,
so nothing is priced on it. **Neither job changes a result** — both measure the cost model, and a
wrong cost model changes cost lines, not signals.

## 2. Equities are a separate product from the CME plans this repo costed

[`databento_api.md:186-191`](../databento_api.md) is explicit: plans cover **CME/CBOT/NYMEX/COMEX
only; equities and OPRA are separate products at every tier.** The $182 futures proposal buys
nothing here, the $28.00/GiB rate derived from Databento's GLBX.MDP3 worked example is **a different
dataset's price**, and no US-equity dataset code appears anywhere in this repo's reference. The
script applies that rate anyway and flags it ASSUMED on the line where it does;
`metadata.list_unit_prices` is free and replaces it with a quote.

## 3. The size, in symbol-days

The job is built from D362's **A2 row-drop arm** — `taken_G2 == 1` in
[`data/d361_trades_gap_up_fade.csv`](../../data/d361_trades_gap_up_fade.csv) less the S1 and S2 hits
at `run_d362_sink_filter.SINKS`' thresholds: **3,028 trades** (asserted against
`data/d362_sink_filter.json`'s committed `RD.A2.trades`), 993 names, **2011-08-03 to 2026-03-31**.

The futures job buys 26 contracts for 16 unbroken years, so symbol-*years* is its unit. This ledger
is a sparse scatter of dates, so the unit here is **symbol-days**: 3,028 entry sessions (open
auction) + 3,028 exit sessions (close auction) = **6,054 distinct traded symbol-days**. That is 24.0
symbol-years of calendar; buying it *as* symbol-years would overstate the bill about 41×.

## 4. The dollar figures — all estimates

Two ASSUMED numbers carry everything: the $/GiB rate above, and messages per symbol-day, which
nobody here has measured. Three scenarios, so the spread is visible:

| job | schema | low | **mid (headline)** | high |
|---|---|---:|---:|---:|
| 1 | `mbp-1` (80 B/msg, INFERRED) | $631 | **$3,157** | $12,630 |
| 2 | `trades` (48 B/msg, INFERRED) | $38 | **$189** | $758 |
| | **total** | **$669** | **$3,347** | **$13,387** |

Less the $125 new-user credit the headline is **$3,222 cash**. **The low-to-high spread is 20×**,
and it is the assumption, not the data: `metadata.get_billable_size` is free and returns the exact
byte count for any (symbols, schema, start, end).

## 5. The 12-month wall, which is the real constraint

Both jobs are L1. [`databento_api.md:138-142`](../databento_api.md) gives the usage-based ($0/mo)
tier **16+ years of L0 and the last 12 months of L1.** Against a ledger starting in 2011:

- **6 of 3,028 trades (0.20%)** fall inside today's 12-month window — 12 symbol-days, about **$7**.
- The other 3,022 are not purchasable at $0/mo at any volume. Standard ($199/mo) or Unlimited
  ($4,500/mo) is the gate — a subscription decision, not a data-volume one.

**So the free-tier version is a recent-window calibration, not a re-costing of the ledger.** It
answers "on the handful of 2025-26 events, how far is D285's estimator from a quoted spread, and did
the open print in the auction?" — and that calibration would then be *assumed* to hold back to 2011,
on a universe whose spreads have compressed for fifteen years. That assumption belongs written down
as an assumption, not absorbed into a cost line.

## 6. Why every figure stays an estimate until two free calls run

`fetch_databento.py` already implements `--verify` (seven free metadata calls) and `--cost`
(Databento's own quote, also free). **Neither has ever run**: there is no `DATABENTO_API_KEY` in the
environment and no `~/.config/databento/key` on this machine — the script checks and finds neither.
Two free calls would replace three flagged assumptions with quotes: the dataset code, the unit
price, and the billable size.

`--submit` is **deliberately not wired up**, and this proposal does not ask for it to be. The
futures client's note stands: a spending path that exists can be run by accident, so submission is
written in the same commit as the purchase decision. The new script adds no spending path at all —
it replaces `fetch_databento.call` with a raiser for the whole run and proves the raiser fires.

## 7. The decision

Four options, stated without a recommendation:

1. **Sign up, run `--verify` and `--cost`, buy nothing.** Free. Settles the dataset code, the unit
   price and the exact billable size, turning every ASSUMED number above into a quote. Costs a
   signup and the unresolved question of exchange licence fees ([`:245`](../databento_api.md)).
2. **Then buy the 12-month slice** (~$7 at the mid scenario, inside the $125 credit). A calibration
   on 6 trades: free in practice, and one event cluster wide.
3. **Subscribe for a month to reach the full ledger** ($199 Standard + usage, headline ~$3.3k, range
   $0.7k–$13.4k). The only option whose answer covers the period the record's results were measured on.
4. **Do none of it**, and write down that the spread and auction lines are estimated. Every net
   figure in the record then keeps a stated, unmeasured dependency.

Option 1 is free and strictly reduces the uncertainty in the other three. Nothing beyond it should
be decided on the numbers in this document, because those numbers are what option 1 exists to replace.
