# Corporate actions — splits, ex-dates, and why a second source cannot exist

[← data index](00-index.md) · prev: [filing text and timestamps](02-filing-text-and-timestamps.md) · next: [fixture and vendor defects](04-fixture-and-vendor-defects.md)

**`[REPO]` this is the class that has cost this programme most.** Thirty fabricated return days
reaching fifteen studies ([FINDINGS §18](../../../FINDINGS.md)); two fixtures on different adjustment
bases with one name sitting at 5× its own prices; a quarter of an "ETF" fixture being closed-end funds
([§60](../../../FINDINGS.md)). **Everything below is the outside world's version of the same problem.**

---

## The ex-date convention has THREE regimes, a hole and a doubled day `[EXT]` `J6` / `K4`

**And FINRA Rule 11140 sets it — not the SEC settlement releases**, which is where the commissioner
had been looking.

| | reading |
|---|---|
| **declared ex-dividend holes** `[CONFLICT C10]` | `J6`: **one** (2017-09-05) · `K4`: **two** — 2017-09-05 **and** 2024-05-28, **both verbatim primary** |
| **the doubled day** `[CONFLICT C9]` | `J6`: a doubled **ex-date** · `K4`: a doubled **settlement** date (2017-09-07, 2024-05-29), **no primary found declaring a doubled ex-date**, and both recovered transition mappings **injective** |

**`K4` names a one-line check on this programme's own file, and it is the cheapest high-value check
available:**

> **Assert the two declared ex-dividend holes are EMPTY.** `K4`'s discriminator: **a recomputed
> ex-date column cannot produce them; a published one cannot avoid them.** `[OPEN]`, item 19 of
> [`../../README.md`](../../README.md) — **it tells you which kind of column you have.**

**And one more regime boundary may exist:** does a **2010-12-15 amendment to Rule 10b-17** create a
**fourth** boundary, eleven days after the first bar? **One primary document away.** Item 20.

## A second source for the EX-DATE is unavailable IN PRINCIPLE `[EXT]` `K6`-round §1.5

> **10b-17 does not require the issuer to state the ex-date. The exchange designates it.**

**So it cannot be recovered from EDGAR — not "not found", but not obtainable.** This closes a route
the programme had assumed was open, and it is the strongest kind of negative: **a rule, not a search.**

## Splits — the tag exists, and it still fails `[CONFLICT E8]`

`A1`: **no split history anywhere in XBRL.** `B4`: `us-gaap:StockholdersEquityNoteStockSplitConversionRatio1`
**exists, carried by 2,280 CIKs 2009–2026**, correct for seven named issuers — **then rejected on five
measured defects.**

> **Both stand. The practical conclusions coincide; the factual claims do not.**

**And the detectors that infer splits from price ratios FABRICATE events** — `B4` §7 measures the
rate. **`B4` §5 gives the split-free formulation, which is the actual answer.**
→ [share count and issuance](../signals/06-share-count-and-issuance.md)

## The inverted factor `[CONFLICT E9]` — the sharpest single hazard in the tree

**Documentation: `shrout / cfacshr`. Shipped code: `shrout * cfacshr`.**

> **An inverted factor turns a 7:1 split into a 49-fold error.**

**Documentation versus code, with the code right.** Five instances of that class now
→ [tooling hazards](../method/04-tooling-hazards.md).

## A scalar factor cannot express a spin-off `[EXT]` R2, corroborated `[REPO]`

**Date-dependent by construction, and the child has no pre-when-issued history.** The commissioner's
own withdrawn premise: *"the spin-off-as-split mechanism explained our 5× shape."* **It did not** —
that was a genuine 5:1 split across two fixture bases. Withdrawn in
[`the-forced-seller-and-the-cost-wall.md` §1.4](../../the-forced-seller-and-the-cost-wall.md).

## Odd lots entered consolidated volume on 2013-12-09 `[EXT]` `J`-round §1.4

> **`V` breaks, `OHLC` does not — and the asymmetry IS the finding.**

**It hits the dollar-volume screen price-dependently**, which is exactly the screen this programme
uses to define its universe (D339's dv28). **Never checked here.**

## And a "daily return" may not be a one-day return `[EXT]` §1.9

Read it there. It is a definitional trap in published series, not in ours — **but any external series
used as a benchmark inherits it.**

---

**Sources.** [`the-selection-round.md` §1.4, §1.5, §1.9](../../the-selection-round.md) ·
[`the-reversal-round.md` §1.5](../../the-reversal-round.md) ·
[`R2-04`](../../Scan-100926/R2-04-shares-outstanding-and-float.md) ·
repo: [FINDINGS §18, §60](../../../FINDINGS.md), D339.
