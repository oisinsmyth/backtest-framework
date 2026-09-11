# Free, point-in-time, dead-inclusive fundamentals from SEC XBRL

[← data index](00-index.md) · next: [filing text and timestamps](02-filing-text-and-timestamps.md)

**The answer round 1 gave, stated before its evidence:**

> **The data gap IS closable from the SEC's own products — but the obvious endpoint is a silent
> look-ahead.**

---

## The three products, and which one is point-in-time `[EXT]` `A1`

| product | point-in-time? | the catch |
|---|---|---|
| **Financial Statement Data Sets** (quarterly ZIPs) | **PIT by construction** — *"all numeric data is as filed"* | carries **`prevrpt`** — see below |
| **`companyfacts`** | **PIT-reconstructible** — every vintage stamped with accession, form and filing date; verified on six named as-of dates | the successor-entity defect — `E11` |
| **`frames`** | **NO — RESTATED**, with **no `filed` and no `form`** | **`A1`'s central negative, and the most reused finding of the campaign** |

> **`frames` is the obvious endpoint and it is the silent look-ahead.** Used twice since: round 2's
> record flagged `B2`'s tag census as exposed to it; round 3's `C1` addressed it directly.

## `prevrpt` — a vintage file that carries knowledge of its own future `[EXT]` `C1`

The Financial Statement Data Sets carry **`prevrpt`**, a flag that a submission **was subsequently
amended.** So a vintage file knows something that had not happened when it was filed.

**`C1` then measured it unusable as an amendment flag anyway:** **2.41% (2013q2) → 0.80% (2019q3) →
0.00% of 5,249 submissions (2025q3).**

> **The numeric-data claim stands. One metadata column is hindsight.** `A1`'s *"PIT by construction"*
> is qualified, not overturned.

## `E11` — "latest filed wins" does not reconstruct a vintage

**CIK 895126 reports the instant `2019-02-01` as BOTH 717,376,170 and 3,600,000** — wrong by **199×,
fourteen months before the split.** **The successor-entity defect defeats both vintage rules.**
**Both readings stand**; this extends `A1`'s own spin-off identity defect rather than contradicting
its method. → [share count and issuance](../signals/06-share-count-and-issuance.md)

## `D10` — the free data gives the STRONGER result, which nobody expected

**The usual assumption, and this programme's own worry:** vendor-standardised data is cleaner.

> **`A1` `[read in full]`: the accruals hedge pays 0.673%/month AS-FILED against 0.296%/month and
> INSIGNIFICANT on the standardised vendor's data.** 4 of 19 anomalies affected, **15 unaffected.**

**Recorded as a conflict with an assumption, not with a source.**

## What is in it, and what is not

- **§4 · dead issuers** — the reason this route matters at all for a dead-inclusive fixture.
- **§5 · taxonomy stability 2010–2026** — whether a tag means the same thing across the window.
- **§6 · what is NOT in XBRL that the standard vendor has** — and **§6.3 records two places where
  the SEC's own documentation disagrees with the SEC's own data.**
- **§7 · which signals become computable** — the payoff section, and the one to read against
  [what anomalies pay](../cost/02-what-anomalies-pay.md)'s *"zero of the ten strongest are
  computable"*.

**No split history is the hard one** — `A1` said none exists anywhere in XBRL; `B4` found the tag and
then rejected it on five measured defects (`E8`). → [corporate actions and splits](03-corporate-actions-and-splits.md)

## `E5` — one encoding discrepancy in an otherwise exact replication

`A1`'s census records `CostOfGoodsSold` as **`0`** in later years; `B2`'s independent census of the
same tag-years records **`HTTP 404`**. **Both mean no filers** — but **`A1`'s own brief warned against
coercing a 404 to a zero.** **Every other shared cell between the two censuses matches exactly**,
which makes this a replication with one encoding discrepancy. **Recorded, not adjudicated.**

## Two free point-in-time routes were actually BUILT `[EXT]` `K`-round

Round 6 §1.8 records **two free PIT data routes built**, not merely proposed. **Start there before
designing a third.**

## The open call that would settle the listing map `[OPEN]`

**One call:** `LISTING_STATUS` with `date=`, cross-checked against SEC MIDAS. **Not executed — no key
was used and none was registered for.** Item 10 of [`../../README.md`](../../README.md).

## The privacy rule attached to all EDGAR work

A round-3 agent's first `sec.gov` fetch used a User-Agent containing **the principal's personal email
address** before switching to a neutral string; the agent disclosed it itself. **The committed code is
clean.** **Any future EDGAR work must use the project contact string** — SEC fair-access requires an
email-shaped token, which is why an agent reached for one.

---

**Sources.** [`R1-01`](../../Scan-100926/R1-01-free-fundamentals.md) ·
[`R3-01` §9](../../Scan-100926/R3-01-the-quarterly-variant-and-the-lag.md) ·
[`R2-04`](../../Scan-100926/R2-04-shares-outstanding-and-float.md) ·
[`the-reversal-round.md` §1.8](../../the-reversal-round.md) ·
[`the-plumbing-round.md` §1.8](../../the-plumbing-round.md).
