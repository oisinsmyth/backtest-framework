# Share count, float and issuance — the family that died on a dependency

[← signals index](00-index.md) · prev: [arrival and drawdown](05-arrival-and-drawdown.md) · next: [short-side cross-section](07-short-side-cross-sectional.md)

**Round 1 narrowed the field to two persistent-characteristic families. This is the other one, and it
is the cheaper one.** It died on a **dependency**, not on a return — which is exactly the
premise-first design working.

---

## `D9` — the dependency failure, stated as both lanes had it right

| | |
|---|---|
| `A2` | the **share-issuance family is the cheapest non-free candidate**, needing *"only a split-adjusted share count"* |
| `A1` | **net share issuance is NOT computable — there is no split history anywhere in XBRL** |

> **Not a contradiction. The two lanes are right about different halves, and together they close the
> route unless a split source is found elsewhere.** Recorded as **answered by `B4`** — and under
> [R15](../../../RULES.md#r15) **only the principal closes an avenue.**

## `B4` sent at exactly that, and both horns fail in the same direction

**`E8` — the tag exists.** `us-gaap:StockholdersEquityNoteStockSplitConversionRatio1` is carried by
**2,280 CIKs, 2009–2026**, with correct ratios for seven named issuers. **`A1`'s factual claim was
wrong; its practical conclusion was right** — `B4` then rejected the route on **five measured
defects**. **Both stand.**

**`E10` — and the signal does not need it.** Daniel & Titman state it verbatim in print (p. 1614):
*"corporate actions such as splits and stock dividends leave ι unchanged"*, and the reference
implementation of `CompEquIss` takes only `[ret, mve_c]` — **no share count, no split factor.**
**`A2`'s own gloss of its own entry already said it needs *"market cap and total return"*** — an
internal tension inside one list, **resolved in `B4`'s direction by a primary source, with `A2`'s
entry left standing as written.**

> **So the route closes twice over: the split gap cannot be closed from free data, AND the signal
> does not need it closed.**

## `E9` — the inverted factor, and it is the sharpest data hazard in the tree

**Documentation:** the share count is **`shrout / cfacshr`**. **The shipped CODE:** **`shrout *
cfacshr`**.

> **An inverted factor turns a 7:1 split into a 49-fold error.**

**A documentation-versus-code disagreement in an external source, not an error by the lane that quoted
the documentation accurately.** With `F3` and `G6`×3 this class is now **five instances and should be
assumed, not discovered** → [tooling hazards](../method/04-tooling-hazards.md).

## `E11` — "latest filed wins" does not reconstruct a vintage

`A1`: `companyfacts` is **PIT-reconstructible** — every vintage stamped with accession, form and
filing date, verified on six named as-of dates. **`B4`: CIK 895126 reports the instant `2019-02-01` as
both 717,376,170 and 3,600,000** — so *"latest filed wins"* is **wrong by 199×, fourteen months before
the split.** The **successor-entity defect defeats both vintage rules.** **Both stand**; this extends
`A1`'s own spin-off identity defect rather than contradicting its method.

## The coverage finding the lane was not commissioned to find

**Multi-class issuers** — `B4` §3. Read there.

## What `B4` returned that is usable

- **`§5` — the split-free formulation**, taken first *because it is the answer*.
- **`§6` — the measured error rate**, which is the number the lane exists to produce.
- **`§7` — the detectors, and the fabrication they produce.** A detector that infers splits from price
  ratios manufactures events; the section quantifies it.
- **`§8` — the lane's own premise was WRONG**, recorded as such.

## `[REPO]` what this programme already knows about splits

- A **scalar factor cannot express a spin-off** — date-dependent by construction, and the child has no
  pre-when-issued history.
- **The two fixtures disagree on corporate-action basis** — 15m fully adjusted, daily not; a name sat
  at 5× its own prices and `raw_price_factor` could not fix a spin-off. *(Standing memory.)*
- **[FINDINGS §18](../../../FINDINGS.md):** thirty fabricated return days reached fifteen studies.

**Every one of those is the same class as `E9` and `E11`.** → [corporate actions and splits](../data/03-corporate-actions-and-splits.md)

---

**Sources.** [`R2-04`](../../Scan-100926/R2-04-shares-outstanding-and-float.md) ·
[`R1-01`](../../Scan-100926/R1-01-free-fundamentals.md) ·
[`R1-02`](../../Scan-100926/R1-02-persistent-characteristics.md) ·
records [`R1-99` `D9`](../../Scan-100926/R1-99-record.md), [`R2-99` `E8`–`E11`](../../Scan-100926/R2-99-record.md).
