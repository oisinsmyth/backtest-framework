# The profitability family — the one characteristic family this programme could compute

[← signals index](00-index.md) · next: [long leg vs short leg](02-long-leg-versus-short-leg.md)

**Why this family and no other.** `Scan-100926` round 1 narrowed the field to **two persistent
characteristic families**, and **one of them is not computable** from permitted free data (see
[share count and issuance](06-share-count-and-issuance.md)). Everything after round 1 is about this
one.

**Nothing here is a recommendation, and nothing here was measured on this fixture.**

---

## The definitions, and they are not one signal `[EXT]` `D3`

| | numerator | deflator |
|---|---|---|
| **gross profitability** (Novy-Marx 2013) | revenue − COGS | **total assets** |
| **operating profitability** (Fama–French 2006/2015) | revenue − COGS − SG&A − interest | **book equity** |
| **`CbOP`** — cash-based operating profitability | accrual-adjusted | either |

**`D3` names ten differences separating the first two** and reports the correlation *"nobody
publishes"*, measured three ways with controls that fired. **Its own preference is labelled a view,
not a finding.**

**This is not pedantry — the two definitions produce opposite answers to the campaign's central
question.** `F1`'s two lanes differ on definition, dataset **and** cut.

## The four load-bearing conflicts, all open

### `F2` · does the lagged deflator kill it? — **a SCOPE finding, not a contradiction**

| | result |
|---|---|
| `B2` — **annual** | `t` falls from 3+ to **1.04–1.85** |
| `C1` — **quarterly** | **0.51 [`t` 3.40]** with one-quarter-lagged assets |
| `C4` — **post-2014** | lagged still gives **+0.256 [`t` 2.23]** |

**All three stand.** `B2`'s collapse is **an annual, pre-2014 result.**

**And the ranking inverts.** `C1` recovered Hou–Xue–Zhang's own both-frequency table:

| | annual | quarterly |
|---|---|---|
| gross profits / lagged assets | 0.16 **[t 1.04]** | **0.51 [3.40]** |
| operating profits / lagged assets | 0.20 [1.07] | **0.72 [3.35]** |
| **`CbOP`** — round 2's recommended definition | 0.53 [3.02] | **0.49 [3.02]** |

**The definition round 2 recommended gains nothing from the frequency, and the two it wrote off
recover.** `C1` also recovered Novy-Marx's Table A6 in full: **the annual strategy is completely
subsumed by the quarterly one** (α −0.03, `t` −0.23) while the quarterly earns **α +0.42 [t 3.10]**
against the annual — **identical in the 2012 draft and the published JFE**, so the
draft-versus-published check ran and passed.

### `G1` · …but a second lane measured the same construction and got nothing

**`C1`: 0.51 [`t` 3.40]** — read from a **published table** (1967–2016, NYSE breakpoints, VW deciles).
**`D2`: 0.163 [`t` 1.43], insignificant** — **its own measurement** of the same construction (TTM
numerator, quarterly-refreshed, one-quarter-lagged deflator), 1963–2010, different library,
breakpoints and weighting, **three for three across gross, operating and operating-to-equity.**

**`D2`'s position — recorded as `D2`'s, not adopted:** round 3's headline should be *"marked
provisional on the deflator, not on the season."* **Both stand. `F2` is directly affected.**

### `F3` · which assets does the deflator paper deflate by? — **corrected, with provenance intact**

`B2` could not obtain the paper by four named routes and rested on **three second-hand restatements
that agreed with each other: lagged.** `C1` obtained it and read it: **CURRENT assets.**
**`B2`'s own quoted code comment agreed with `C1` all along** — *"OP 2016 JFE seems to lag assets, but
2015 JFE does not"* — and its headline followed the restatements over the code comment it had quoted.

> **Everything this campaign holds from that paper is the 6 May 2014 working paper.** The published
> JFE 117(2) 2015 has now **failed in three consecutive rounds**, five routes logged with byte counts,
> including a **wrong-200 serving a 404 page at a `.pdf` URL**.

### `E3`/`E4` · is `CbOP` subsumed, and does a paper agree with itself?

`E3`: `CbOP` survives both deflator conventions, both weightings, big stocks alone, post-2005
(`t` 3.02–3.44) — **against** an R&D-adjusted operating profitability that **subsumes it, `t` 6.99 vs
0.42**, post-2000 fully. **But that paper changes deflator, estimator AND numerator at once, and both
sides are interested parties.**

`E4`: one paper's **Table 3** gives gross profitability netting **0.37 at `t` 2.74**; **the same
paper's text** lists the strategies achieving significant net excess returns **and gross
profitability is not among them.** `B2` read both and **did not resolve which the paper intends.**

## Seasonality — the hypothesis failed, the contamination is real `[EXT]` `D2`

`C1`'s post-bar conjecture was that a single-quarter sort is an **unadjusted seasonal sort**. `D2`
found **the other half of the passage `C1` had only half of**: the seasonality-controlled variant is
**stronger** (0.76 [`t` 5.43] vs 0.69 [3.07]).

**But the contamination is real and located:** within-firm phase-`R²` gap **+0.0700**, Wilcoxon
`p` = 1.3 × 10⁻³⁸, **concentrated in retail and wholesale — the two industries most likely to have a
non-December fiscal year end.**

## What would have to be true for any of it to matter here

1. The tags must be computable at the needed frequency → [SEC XBRL](../data/01-sec-xbrl-fundamentals.md)
2. The **long leg alone** must pay, because this programme cannot hold the short one →
   [long vs short](02-long-leg-versus-short-leg.md)
3. The construction must be pinned, because **dispersion across defensible constructions runs 68–96%
   of the premium** → [construction dispersion](03-construction-dispersion.md)
4. It must not already be dead → [decay and era](04-decay-and-era.md)

---

**Sources.** [`R2-02`](../../Scan-100926/R2-02-profitability-deep.md) ·
[`R3-01`](../../Scan-100926/R3-01-the-quarterly-variant-and-the-lag.md) ·
[`R4-02`](../../Scan-100926/R4-02-is-the-quarterly-advantage-seasonal.md) ·
[`R4-03`](../../Scan-100926/R4-03-are-these-two-signals-the-same-signal.md) ·
records [`R2-99` §2.1–2.2](../../Scan-100926/R3-99-record.md), [`R3-99`](../../Scan-100926/R3-99-record.md), [`R4-99`](../../Scan-100926/R4-99-record.md).
