# Futures data — where it comes from, and what it costs

[← data index](00-index.md) · prev: [fixture and vendor defects](04-fixture-and-vendor-defects.md) · next: [purchase proposals](06-purchase-proposals.md)

**A 13-lane exhaustive search.** The full survey is [`../../futures-data/`](../../futures-data/); this
page is the answer and the traps.

---

## The answer `[EXT]` — Databento's signup credit

**`GLBX.MDP3`, schema `ohlcv-1m`, paid for entirely by the `$125` new-user credit.**

| | |
|---|---:|
| one symbol-year | **~$0.51** |
| **ES + NQ + RTY + YM, 15 years** | **$30** |
| all eight symbols, 16 years | **$65** |
| what the credit buys | **~246 symbol-years** |

**The rate was DERIVED, not assumed.** Databento does not publish a per-schema `$/GB` table, but its
API reference publishes two worked examples of the same query — 99,219,648 bytes and
`$2.587353944778` — giving **exactly `$28.00/GiB`**, which also proves their "GB" means 2³⁰.
`OhlcvMsg` is a fixed 56 bytes and no bar prints without a trade, so
`1,380 × 252 × 56 B = 19.47 MB = $0.51`/symbol-year is an **upper bound.**

**One inferred step, flagged:** whether `ohlcv-1m` bills at the same rate as `trades`. The published
OPRA example prices `trades`, `ohlcv-1s` and `ohlcv-1m` **identically**, and it is confirmable in 30
seconds post-signup. **The conclusion survives a 2× error.**

**It is the real thing, not a proxy.** `GLBX.MDP3` is the raw MDP 3.0 capture — **full ~23-hour
Globex, no RTH filter** — from the official licensed CME distributor. **ES from 2010-06-06.**

**The schema choice is what makes it free.** Same ES, 15 years: `ohlcv-1m` **$7.62**, `ohlcv-1s`
~$457, `trades` ~$2,180.

## Three traps `[EXT]`

1. **Use `stype_in="continuous"` (`ES.c.0`). NEVER `parent`** — it resolves to every outright *plus*
   every calendar spread.
2. **Use `batch.submit_job`, not streaming.** **Streaming re-bills on retry**; batch bills once and
   allows 30 days of free re-downloads.
3. **The credit expires in 6 months**, one set per team, **and they police farming.**

**Caveat:** RTY reaches only ~9 years — the E-mini Russell moved to CME in 2017. **Market structure,
not a vendor limit**, and independently confirmed in two lanes.

## What is genuinely free with no credit `[EXT]` §2

**Dukascopy index CFDs — verified twice, independently, by download and decode.** Full cross-checks in
[`00-SYNTHESIS.md`](../../futures-data/00-SYNTHESIS.md) §2.

## The governing constraint, confirmed twice independently `[EXT]` §3

Read §3. It is the reason the survey ends where it does.

## The roll warning — applies to EVERY source `[EXT]` §6

**Not just the free ones.** A continuous series is a construction, and the construction is not the
vendor's problem.

## Two corrections to this programme's own prior assertions `[EXT]` §5

Recorded in the synthesis. **Read them before quoting anything the repo previously said about futures
data.**

## The structural argument `[EXT]` §8 — *"the strongest thing here"*

The synthesis says so itself. **If only one section of the futures survey is read, read §8, not §1.**

## Standing exclusion ground

**The overnight-venue survey inside `futures-data/` — Blue Ocean, IBEOS, Databento, Tiingo — is now
standing exclusion ground.** Do not re-commission it.

---

## The lane map, if a specific question needs answering

| | |
|---|---|
| [01](../../futures-data/01-reddit-and-forums.md) · [02](../../futures-data/02-ibkr.md) · [03](../../futures-data/03-broker-apis.md) | community claims · IBKR · broker APIs |
| [04](../../futures-data/04-free-api-tiers.md) · [05](../../futures-data/05-exchange-direct.md) · [06](../../futures-data/06-github-opensource.md) | free tiers · exchange direct · open source |
| [07](../../futures-data/07-datasets-and-academic.md) · [08](../../futures-data/08-yahoo-and-scrapers.md) · [09](../../futures-data/09-crypto-futures-proxy.md) | datasets · scrapers · crypto proxies |
| [10](../../futures-data/10-prop-and-platform-data.md) · [11](../../futures-data/11-aggregators-and-legacy.md) · [12](../../futures-data/12-substitutes-and-lateral.md) | prop platforms · aggregators · substitutes |

**And the IBKR note that generalises:** **every IBKR 403 was a User-Agent exclusion, not a host
block.** → [tooling hazards](../method/04-tooling-hazards.md)
