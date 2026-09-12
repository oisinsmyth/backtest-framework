# Data purchase proposals — what has been costed, and what is still a proposal

[← data index](00-index.md) · prev: [futures data sources](05-futures-data-sources.md)

**Neither of these has been bought.** Both are decisions for the principal, and both are recorded here
so a later reader does not re-cost them from scratch.

---

## Futures — [`13-ACQUISITION-PROPOSAL.md`](../../futures-data/13-ACQUISITION-PROPOSAL.md)

| part | what it proposes |
|---|---|
| **the principle** | stated first, before any number |
| **current footprint** | **measured**, not estimated |
| **part 1** | **Databento, one month** — the credit-funded route from [futures data sources](05-futures-data-sources.md) |
| **part 2** | **Alpha Vantage, one comprehensive top-up before pausing** |
| **part 3** | **storage** |
| | **total cost** and **sequencing** are the last two sections |

**The longer working document behind it:** [`data-purchase-proposal.md`](../../futures-data/data-purchase-proposal.md).

## Equity quotes and auctions — [`equity-quote-and-auction-data-proposal.md`](../../equity-quote-and-auction-data-proposal.md)

**Titled *"a proposal, not a purchase"*, and it means it.**

| § | what it says |
|---|---|
| **1** | **what the two jobs answer that OHLC cannot** — this is the section that matters, because it is the only route to settling the spread-convention question |
| **2** | **equities are a separate product from the CME plans this repo already costed.** Do not reason across them |
| **3** | the size, in **symbol-days** |
| **4** | the dollar figures — **all estimates** |
| **5** | **the 12-month wall, which is the real constraint** |
| **6** | **why every figure stays an estimate until two free calls run** |
| **7** | the decision |

> **§6 is the actionable one: two free calls would convert the whole proposal from estimate to
> quote, and they have not been made.**

## Why this matters more than it looks

**`[REPO]` D332 says the spread-convention question *"cannot be decided from OHLC alone."*** Its named
test is **quoted `BID_ASK` bars from IBKR on a stratified sample of live names**, scored against `PB`,
`PUB` and Abdi–Ranaldo by lowest median absolute log error, **declared in advance.** D336 is the
quoted-spread validation record.

> **Until that runs, every net number in this programme is a `PB`/`PUB` pair** — and the equity-quote
> proposal is the only costed route to ending that.
> → [spread estimation](../cost/01-spread-estimation.md)

## The related open item that costs nothing

**One call would settle the point-in-time listing map:** `LISTING_STATUS` with `date=`, cross-checked
against SEC MIDAS. **Not executed — no key was used and none was registered for.** Item 10 of
[`../../README.md`](../../README.md).

## The rule attached to any purchase

**`[EXT]` the roll warning applies to every source, free or paid** — a continuous series is a
construction. And **the vendor's own documentation may contradict its own FAQ** (`C6`), so
**a bought feed still needs the adjustment basis tested against the data.**
→ [fixture and vendor defects](04-fixture-and-vendor-defects.md)
