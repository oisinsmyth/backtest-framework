# Open questions — nothing here is measured, and all are the principal's to authorise

[← consolidated index](00-INDEX.md)

**Source of truth for the full list:** [`../README.md`](../README.md) §"What is open" — **23 items,
stated as questions.** This page **re-sorts them by what they cost and what they decide**, and adds
the ones that only became visible when the tree was consolidated. **It adds no new claims.**

> Under [R15](../../RULES.md#r15) **nothing in the research tree closes or admits anything**, and
> nothing is elevated without the principal's explicit permission.

---

## Tier 1 · Minutes, on data we already hold, and each settles something downstream

| | question | what it decides | where |
|---|---|---|---|
| **1** | **Do the four no-trade dates exist as rows?** 2012-10-29, 2012-10-30, 2018-12-05, 2025-01-09 | **4,187 vs 4,191.** The first externally-derived arithmetic prediction about this fixture | [R8](conflicts/02-versus-repo-measurements.md) |
| **2** | **Are the two declared ex-dividend holes empty?** 2017-09-05, 2024-05-28 | **whether our ex-date column is RECOMPUTED or PUBLISHED** — a recomputed one cannot produce them, a published one cannot avoid them | [data/03](data/03-corporate-actions-and-splits.md) |
| **3** | **Does a held name falling through `$5` get EJECTED or CARRIED?** | ejected = **an undeclared stop-loss at `$5` truncating every trade's left tail.** Carried = the Shumway delisting bias applies | [cost/03](cost/03-price-floor-and-screens.md) |
| **4** | **Does the weight array get recomputed from the current bar's close for names already held, or only at entry?** | whether a multi-bar book carries the **large** equal-weight bias or `1/H` of it | [cost/04](cost/04-equal-weight-bias.md) |
| **5** | **MEASURE THE DAILY AUTOCORRELATION OF AN EQUAL-WEIGHTED BOOK** | **the single input that decides whether the block-length finding bites at all.** `H6`'s two halves point in opposite directions and **which applies is one number, not a judgement** | [method/02](method/02-nulls-and-block-length.md) |
| **6** | **Does the fixture preserve entirely missing sessions, or forward-fill them?** | whether a multi-day halt is visible at all; prerequisite for counting them | [data/04](data/04-fixture-and-vendor-defects.md) |
| **7** | **Reconcile 1,573 against 1,580** | an inconsistency **inside our own record**, noticed from outside | [R9](conflicts/02-versus-repo-measurements.md) |
| **8** | **Does the fixture carry a `+733%` bar on USO or UNG?** | if yes, **the series is not split-adjusted and every result touching those names is contaminated** | [R12](conflicts/02-versus-repo-measurements.md) |

## Tier 2 · One run, and each sets the SIGN of something

| | question | why it is not tier 1 |
|---|---|---|
| **9** | **Recompute D285's `33.8 bp/side` under EDGE** | closed-form drop-in on the same OHLC inputs — *"it sets the SIGN of every cost conclusion downstream"* → [cost/01](cost/01-spread-estimation.md) |
| **10** | **Measure the compounded-daily-minus-buy-and-hold equal-weighted gap** | needs no external series, and `J3` gives a **pre-registrable band: 0.3–1.3%/yr if the floor binds, ~6–7%/yr if it does not** |
| **11** | **Re-block this session's regime-conditioner calibration** | it used **~26 bars per block** where the selector wants **~157**. If the conditioners are as persistent as they appeared, **that probe's decisive line is too lenient** |
| **12** | **The cause-of-death census on the EQUITY fixture** | [FINDINGS §60](../../FINDINGS.md)'s own rule, **never applied to it** |

## Tier 3 · Standing guidance that research contradicts — the principal's call, not a measurement

| | | |
|---|---|---|
| **13** | **`CLAUDE.md` says per-name rotations carry an irreducible p95 bias. `H6` says they do not** — draws with the identity included and `p = (1+b)/(1+w)` are **exact for any `w`**. *"The fix is one character of code."* | [method/02](method/02-nulls-and-block-length.md) |
| **14** | **`50/P` is the COMMISSION, not the spread.** The rule to split results on price stands empirically; **which channel it measures is in doubt** | [cost/03](cost/03-price-floor-and-screens.md) |
| **15** | **Whether [FINDINGS §59 and §60](../../FINDINGS.md) should stand.** They are the same class of elevation as the reverted §61–63, **committed before the ruling existed. Left standing and flagged** | — |

## Tier 4 · Repairs and known-broken code

| | |
|---|---|
| **16** | **The two `d331_edgar_deals.py` bugs** — a look-ahead and a filter that silently returns zero. **Reported, not repaired** |
| **17** | **Match either `SC 13D` OR `SCHEDULE 13D`** — both coexist through 2024 Q1–Q3, legacy rows persist into 2025 Q1, **and the daily `form.idx` truncated the value to `SCHEDULE 1` for about a year.** *The obvious fix to the bug is also wrong* |
| **18** | **Key the EDGAR look-ahead on the SGML `<ACCEPTANCE-DATETIME>` header, not the submissions JSON** — the JSON's timezone is mixed; **the header reproduced `filingDate` on 60 of 60** |
| **19** | **`acceptanceDateTime` needs a PER-FILING header check, not a rule** — reproduced at 62.7%, and **neither filer agent nor era predicts it** |
| **20** | **`adjusted=false` on the intraday endpoint** puts both fixtures on **one corporate-action basis** — the cheapest fix for a mismatch that has already cost this programme once |

## Tier 5 · Needs an external call or a purchase

| | |
|---|---|
| **21** | **One call settles the point-in-time listing map:** `LISTING_STATUS` with `date=`, cross-checked against SEC MIDAS. **Not executed — no key was used and none was registered for** |
| **22** | **Quoted `BID_ASK` bars from IBKR** on a stratified sample, scored against `PB`, `PUB` and Abdi–Ranaldo, **declared in advance.** The only thing that ends the `PB`/`PUB` pair → [data/06](data/06-purchase-proposals.md) |
| **23** | **`P(MAE ≤ $2,000/contract)` for the last-30-minute trade** — one query, ~`$8` of Databento, **inside the existing signup credit.** The one quantity the funded account is priced on and **the literature does not publish it anywhere** |
| **24** | **Does a 2010-12-15 amendment to Rule 10b-17 create a FOURTH ex-date regime boundary**, eleven days after the first bar? **One primary document away** |

## Tier 6 · Research questions, not repo measurements

| | |
|---|---|
| **25** | **Reconcile D343's "eight-month halt" against a public record that looks like ~32 months.** *Neither figure verified here* |
| **26** | **A TEXT-level measurement is what would generalise round 5's earnings-absorption finding** — an item-code census structurally cannot, because **dividend and split announcements carry no item code at all** |
| **27** | **Treat any 8-K Item 7.01 filing as earnings-contaminated by default** — 12.85% → 24.04%, **up in 16 of 16 steps** |

---

## The two that would move the most, if only two are ever run

> **#5 — the daily autocorrelation of an equal-weighted book.** It is minutes of work, and it is the
> *only* thing that decides whether every null in this programme is calibrated on a block length that
> is six times too short. **Two research rounds looked for it in the literature and the best modern
> figure found is indistinguishable from zero on a different object.** *We are the ones who can
> measure it.*

> **#9 — D285's 33.8 under EDGE.** Three independent defects are now recorded in the estimator that
> produced this programme's cost bar, and **the repo's own D332 already replaced the convention
> without re-measuring the level.** Every breakeven in both the research tree and the record is
> quoted against a number nobody has re-derived.
