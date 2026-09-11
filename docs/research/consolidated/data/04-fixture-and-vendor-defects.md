# Fixture and vendor defects — what is wrong with the data we already hold

[← data index](00-index.md) · prev: [corporate actions and splits](03-corporate-actions-and-splits.md) · next: [futures data sources](05-futures-data-sources.md)

**This is the highest-yield page in the tree.** *"The plumbing outlives the leads"* — three rounds
running, the data lanes returned more than the signal lanes beside them, and **`G6` was the strongest
single return of round 3.**

---

## The vendor documents TWO adjustment bases on one page `[CONFLICT C6]` ▲

> **The API documentation says the daily-adjusted endpoint returns RAW as-traded OHLCV** with
> adjustment confined to a separate column. **The same vendor's support FAQ says it adjusts open,
> high, low, close AND volume.**

**`G6` found both. The vendor contradicts itself, and neither statement has been tested against the
data here.**

**`[REPO]` this is the source-side mechanism behind a defect already on our record:** the two fixtures
disagree on corporate-action basis — **15m fully adjusted, daily not** — which put one name at 5× its
own prices and which `raw_price_factor` could not fix, because it was a spin-off. *(Standing memory.)*

> **The cheapest known fix, and it is one parameter:** `adjusted=false` on the intraday endpoint
> **puts both fixtures on one corporate-action basis.** `[OPEN]`, item 11 of
> [`../../README.md`](../../README.md).

## Ticker reuse — the folklore was wrong `[BRIEF]` `G6`

**Measured**, not assumed. [`the-plumbing-round.md` §1.3](../../the-plumbing-round.md).

## The closed-end-fund contamination — found outside, measured here `[REPO]`

**Found in passing by an agent working an unrelated lead**, then re-derived here with a rule declared
before the counts were read: [FINDINGS §60](../../../FINDINGS.md).

| | |
|---|---|
| CEF distribution signature | **150 of 551 = 27.2%** (an independent count in the brief: **31.2%**) |
| the mortality cohort | **23 of 24 dead names are closed-end funds.** The one exception paid no distributions at all |
| distributions absent from `close` | fixture median **3.06%/yr**; **CEF cohort median 10.54%/yr** |
| terminal-wealth understatement over 16 years | **5.37×** on that cohort |

**And the source-side mechanism is live today** — [`the-plumbing-round.md` §1.4](../../the-plumbing-round.md).

**The rule it earned `[REPO]`:** *a fixture's NAME is not its composition, and a status count is not a
cause of death.* **Census instrument types and death causes when a fixture is built, not when an
unrelated agent trips over them.**

## The delisting-return question is ONE code check `[EXT]` `G2` — and both answers flatter a long book

**Reduced from a research question to a single check on our own code.** `[OPEN]`, and note the
asymmetry: **whichever way it resolves, the direction favours a long book** — which is a reason to
check it rather than a reason to relax.

**Adjacent and also open:** *"the Chapter 11 crash is after the last print"* was the commissioner's
premise and **it is wrong — the crash is normally INSIDE the tape**, 131 trading days from filing to
delisting on average.

## No free second price source exists `[EXT]` `H5` — measured across nine sources

**Not inferred. Measured.** So **cross-validating this fixture against an independent vendor is not
available at zero cost**, and every internal consistency check has to do that job instead.

## The bar calendar `[OPEN]` — the first externally-derived arithmetic prediction

**No trade occurred anywhere in US equities on 2012-10-29, 2012-10-30, 2018-12-05 or 2025-01-09.**
Our measured **4,187** matches the absent case; **4,191** would mean present. **Two lines.**
[vs repo R8](../conflicts/02-versus-repo-measurements.md).

**And one more `[OPEN]`, cheap:** **does the fixture preserve entirely missing sessions or forward-fill
them?** It decides whether a multi-day halt is even visible, and it is a prerequisite for counting
them. Item 4.

## The nine flavours of wrong HTTP 200 `[EXT]`

**An HTTP 200 can be wrong, and the catalogue reached nine flavours by round 6.** The two that
fabricated whole harvests:

1. **A CDN cache that ignores a query parameter and silently replays another query's results** — it
   fabricated two entire harvests before a negative control caught it.
2. **A price source that returns a DIFFERENT COMPANY's prices at HTTP 200** — **23.4% of a 64-ticker
   delisting panel.**
3. **A host returning a 404 page at a `.pdf` URL**, `text/html`, 1,651 bytes, `<title>404Handler</title>`
   — committed as evidence at `data/k5_rotman_blume_stambaugh_404_at_http200.html`.
4. **A retrieval path that silently ignores the parameter the whole census depends on** — an
   impossible code returned the identical count to no filter at all. **`K3`'s mandated negative
   control caught it before it produced a brief.**

> **The defence generalises and costs nothing: when harvesting a parameterised endpoint, census a
> value that MUST return zero.**

## The undischarged fixture claim `[OPEN]`

**The USO/UNG `+733%` bar.** → [structural decay instruments](../signals/08-structural-decay-instruments.md)
and [vs repo R12](../conflicts/02-versus-repo-measurements.md).

---

**Sources.** [`the-plumbing-round.md` §1.2–§1.6, `G6`](../../the-plumbing-round.md) ·
[`the-timestamp-round.md` §1.3, §1.5](../../the-timestamp-round.md) ·
[`the-selection-round.md` §1.12](../../the-selection-round.md) ·
[`the-reversal-round.md` §1.9](../../the-reversal-round.md) ·
repo: [FINDINGS §18, §60](../../../FINDINGS.md).
