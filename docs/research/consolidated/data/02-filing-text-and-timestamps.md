# Filing text, EDGAR timestamps, and the look-ahead that keeps coming back

[← data index](00-index.md) · prev: [SEC XBRL](01-sec-xbrl-fundamentals.md) · next: [corporate actions and splits](03-corporate-actions-and-splits.md)

**One theme runs through four rounds: knowing WHEN a filing became public is harder than getting the
filing.** Every fix proposed so far has itself been broken by the next round.

---

## The chain of broken fixes — read in order

| round | what it established |
|---|---|
| **R3** | **two live bugs in `scripts/d331_edgar_deals.py`** — a **look-ahead**, and a filter that **silently returns zero.** `[REPORTED, NOT REPAIRED]` |
| **R3** | the recommended fix: use `acceptanceDateTime` |
| **R4** | **that fix is itself broken.** `acceptanceDateTime` has a **MIXED TIMEZONE** — **35 of 60** hand-checked filings are ET mislabelled `Z` |
| **R4** | R3's stated *mechanism* for the bug is **wrong for 8-K**; `H1` corrected it, and **the bug survives in a different and smaller form** |
| **R5** | **the obvious fix to R3's bug is ALSO wrong**: match either `SC 13D` **or** `SCHEDULE 13D` — both strings coexist through 2024 Q1–Q3, legacy rows persist into 2025 Q1, **and the daily `form.idx` truncated the value to `SCHEDULE 1` for about a year** |
| **R6** | the timezone defect **independently reproduced** (§1.12) |

> **The route that is not broken:** key the look-ahead on the **SGML `<ACCEPTANCE-DATETIME>` header,
> not on the submissions JSON.** The JSON field's timezone is mixed; **the header reproduced
> `filingDate` on 60 of 60.** `[OPEN]` — item 9 of [`../../README.md`](../../README.md).

## `D3` — four readings of the defect rate, and the fourth offers a mechanism

| reading | rate |
|---|---|
| prior rounds | **35/60 (58%)** and **32/51 (62.7%)** |
| `A4` | **1/11 (9%)**, weighting the priors on sample size while confirming the defect is present |
| **`A1`** | **37/92 (40.2%) in 2021q2 and 0/88 in 2026q2**, settled with 26 late filings whose `filed` rolled |

> **`A1` is the first reading to offer a MECHANISM that could reconcile the others: the defect may be
> ERA-DEPENDENT and may have been fixed.** **Recorded as a candidate explanation, NOT an
> adjudication. All four readings stand.**

**And `K3` reproduced it at 62.7% and found neither filer agent nor era predicts it** — so
`acceptanceDateTime` needs a **per-filing header check, not a rule.** `[OPEN]`, item 21.

## The 22:00 cut-off applies to 13D/13G only

**The commissioner generalised it to 8-K when writing round 4's prompt.** Amended in
[`the-plumbing-round.md` §1.1](../../the-plumbing-round.md). **Recorded as his error, not an agent's.**

## `D4` — byte-range behaviour is path-dependent

Round 6: SEC ignores `Range` headers, flatly. **`A4`: path-dependent** — `master.idx` returns **200
with the full 32 MB despite advertising `Accept-Ranges: bytes`**, while the feed tarball honours 206.
**A conflict with this programme's own carried-forward finding, not with another source.**

## Filing text at scale `[EXT]` `A4` — the answer, stated first

**What is free and bulk-retrievable** (§1) is not the constraint. **The crux is extraction** (§3), and
**the second problem is look-ahead in the text itself** (§4).

| | |
|---|---|
| extraction precision | **67–78%, converging across four independent sources**, one of which is this programme's own measurement |
| what has been published using filing text | §2, and `A4` reports it **biased toward the negative** |
| feasibility arithmetic | §5 |
| licensing and terms | §6 |
| **what would have to be true for this lane to change anything** | §7 — the section to read first if the lane is ever revived |

## The earnings-absorption finding, and what it does and does not generalise to

**`[EXT]` R5's meta-finding:** **the earnings release is absorbing dated corporate events** — 60–80%
of dividend actions, 36–68% of splits, **and rising.** Both of round 5's signal lanes died on it.

**`[EXT]` R6's `K3` could NOT generalise it by item code, and that does not refute it** `[NOT A
CONFLICT]`: **dividend and split announcements carry no 8-K item code at all.** The two measurements
are of **different objects at different granularities.**

**What `K3` did find:** **Item 7.01 is the one large clean absorption trend** — **12.85% → 24.04%, up
in 16 of 16 steps.** `K3`'s recommendation: **treat any 8-K Item 7.01 filing as earnings-contaminated
by default.** `[OPEN]`, item 22.

> **A text-level measurement is what would generalise round 5's finding.** An item-code census
> structurally cannot. Item 23.

## `data.sec.gov/submissions/` is survivors-only for tickers

**Two agents, two rounds** ([plumbing §1.5](../../the-plumbing-round.md)), and
**`company_tickers.json` reached a sixth confirmation with a new failure mode** in round 6 (§1.11).
**Assume it; do not rediscover it.**

---

**Sources.** [`R1-04`](../../Scan-100926/R1-04-filing-text-at-scale.md) ·
[`the-plumbing-round.md` §1.1, §1.5](../../the-plumbing-round.md) ·
[`the-timestamp-round.md` §1.1, §1.2](../../the-timestamp-round.md) ·
[`the-selection-round.md` §1.2, §1.6](../../the-selection-round.md) ·
[`the-reversal-round.md` §1.6, §1.7, §1.11, §1.12](../../the-reversal-round.md).
