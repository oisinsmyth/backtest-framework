# D331 RESULT — the events find the pinned names; what is left of `skew_63`'s short leg does not pay its cost under either convention

**Status:** RESULT. Pre-registered at `56863e3`, runner at `997786b` — both
before this file existed (R8). Run on the committed first-pass EDGAR pull
(`2abcb72`).
**Date:** 2026-09-05
**Area:** Strategy research · **personal track** · cost model

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. One signal is retired as a short.**

---

## 1. Part A — the instrument works, and the label it was tested against was wrong

| definition | filings applied | live name-bars excluded | pinned caught | caught among resolved | survivors removed | lead (median) |
|---|--:|--:|--:|--:|--:|--:|
| **F0** target-specific forms | 1,617 | **2.36%** | 71.2% | 83.9% | **27.1%** | 28 bars |
| **F1** F0 + 8-K Item 1.01 merger language | 9,874 | **24.44%** | 78.8% | **92.8%** | **45.4%** | 45 bars |
| F2 F1 + 425 | 23,569 | 25.39% | 78.8% | 92.8% | 46.8% | 45 bars |

**The catch rate is the good news.** Among the 180 pinned trades in resolved
names, F1 finds **92.8%** and F0 alone **83.9%** — with a median lead of 28–45
bars, so the filing precedes the entry by one to two months. The event source
does what the tape filter (D330 B, 71%) could not. Coverage caps the overall
number at 78.8%: the missing fifth is in names EDGAR could not resolve.

**The survivor-removal number is the finding, and it is not what it looks
like.** F1 "removes" 45% of the survivors — but F1 excludes **a quarter of all
live name-bars**, because an 8-K Item 1.01 is filed for any material
agreement and the merger-language filter keeps every acquirer's bolt-on and
every credit facility that mentions an earlier merger. F1 is not a deal
filter; it is a corporate-activity filter. **F0 is the defensible
definition**: target-specific forms only, 2.4% of the universe — and it still
"removes" **27.1%** of the survivors.

**Because D330 A's "survivor" label was wrong.** It called a name a survivor
if it was still trading 60 bars after entry. A US public deal takes four to
six months to close. **A quarter of the "survivors" in `skew_63`'s short leg
are pinned takeover targets whose deal had not yet closed** — they carry a
DEFM14A or a tender-offer form within 63 bars of entry. D330's "+47.3 bp gross
on the 727 survivors, a genuine post-jump reversal" was partly deal targets
that had not delisted yet, and D330's finding is amended accordingly.

So Q1 is **falsified on the survivor half for the right reason**: the events
separate deals from non-deals correctly, and the label did not. Q6 is falsified
too — the target-specific proxy does *not* lag: 71% of pinned trades already
have one before entry. Q7 falsified: 425 adds nothing.

## 2. Part B — with the deals removed, the short leg loses under both conventions

`skew_63`'s short leg at k=20, per trade, per-leg costed:

| | trades' held ½-spread | **PB net** | **PUB net** |
|---|--:|--:|--:|
| S — unfiltered | 7.7 / 16.3 | +16.6 | −0.6 |
| **S_F0 — target forms removed** | 11.9 / — | **−29.8** | **−64.7** |
| S_F1 — F0 + 8-K removed | 14.0 / 33.1 | −3.7 | −41.9 |
| S_F2 | 13.6 / — | −0.2 | −40.3 |

Three things happen at once when the deal names go:

1. **The cheapness goes.** The held half-spread nearly doubles under PB and
   doubles under PUB. The pinned names *were* the cheap names (D330, FINDINGS
   §16). Q2 confirmed.
2. **The big winners go.** The trimmed-both mean *rises* +46.8 → +62.4 (Q3
   falsified upward), while the mean gross falls +32.0 → +24.3. That is a
   leg losing its top tail and its zero-return middle together — **the top
   tail of a short leg full of deal targets is the deals that broke.** A
   deal-break short is a lottery ticket the filter throws away with the
   pinned ones.
3. **What remains does not pay.** Under the narrowest, most defensible filter
   the short leg nets **−29.8 per trade at the programme's old cost basis and
   −64.7 at the published one.** Q4 falsified: it got worse, not better.

The symmetric `skew_63` book follows: +12.60 bp/bar (PB, unfiltered) →
**−9.13 (F0)**, and −17.88 under PUB.

## 3. Q5 is confirmed as written and it is not good news

| k=20 | per trade PB | per trade PUB | bp/bar PB | bp/bar PUB | Sharpe PUB |
|---|--:|--:|--:|--:|--:|
| LW (D329) | +63.26 | +35.99 | +17.49 | +5.58 | +0.139 |
| **LW_F1** | +56.07 | **+20.04** | +1.33 | **−10.80** | **−0.236** |
| S_F1 | −9.85 | −55.06 | −9.48 | −17.95 | −0.563 |
| H | −0.89 | −59.39 | −3.97 | −18.58 | −0.383 |

LW_F1 beats both parents per trade under PUB, as predicted. **It does so
because its long leg (+62.5 per trade) is carrying a short leg that loses
41.9, and both parents are worse.** As a book it nets −10.80 bp/bar. The
leg-wise *construction* stands — the long leg is genuinely `hist_L`'s and the
short leg genuinely `skew_63`'s, and the pairing is less bad than either — but
**with its short leg retired the specific pairing has no short leg.**

## 4. Predictions

| | | outcome |
|---|---|---|
| **Q1** | catch > 75% / 85% resolved; survivors removed < 10% *(load-bearing)* | **FALSIFIED** on survivor removal — 45.4% (F1), 27.1% (F0). Catch confirmed: 78.8% / 92.8%. §1 says why |
| **Q2** | filtered half-spread PB ≥ 8.5, PUB ≥ 20 | **CONFIRMED** — 14.0 / 33.1 |
| **Q3** | trimmed-both mean moves < 10 bp | **FALSIFIED** — +46.8 → +62.4, upward; the deal-break winners left with the pinned names |
| **Q4** | S_F1's short leg nets more than S's under PUB | **FALSIFIED** — −0.6 → −41.9 |
| **Q5** | LW_F1 beats both parents per trade under PUB *(load-bearing)* | **CONFIRMED** — +20.04 vs −55.06 / −59.39; and the book is −10.80 bp/bar |
| **Q6** | F0 catches < 50% *(against F0)* | **FALSIFIED** — 71.2%. The proxy does not lag |
| **Q7** | F2 removes > 3× F1's survivors for < 5 pts *(against F2)* | **FALSIFIED** — 425 adds 1.4 pts of removal and 0 of catch |
| **Q8** | F1 removes < 2% of the long leg | **FALSIFIED** — 27.7%, because F1 is a corporate-activity filter |
| **Q9** | median lead > 5 bars | **CONFIRMED** — 45 |

Three of nine. Both load-bearing predictions resolved in the direction that
ends the question.

## 5. The stop condition, invoked

The pre-registration: *Q1 fails on survivor removal → deals and reversals are
not separable by events either; `skew_63` is retired as a short signal.*

**Invoked, with the reasoning stated rather than the rule cited.** The
premise — inseparability — is only half true: the events *do* separate deals
from non-deals; what failed is the label. But the retirement follows from
Part B on its own: **under the narrowest target-only filter, on both cost
conventions, `skew_63`'s short leg loses money per trade, and its symmetric
book is negative.** Its +16.6, its 7.7 bp half-spread, its "first of 44" in
D329's enumeration, and its 4.53× cost coverage in D326 were all the pinned
deal targets. **`skew_63` is retired as a short signal.** It is not retired as
a *detector*: it is the best takeover-target finder in the 51, which is a
different instrument for a different book.

## 6. What this establishes

1. **SEC EDGAR target-specific forms identify pinned takeover targets on this
   fixture, causally, with a one-to-two-month lead.** F0 is the filter; F1 is
   not a deal filter and should not be used as one.
2. **A 60-bar survival window does not identify non-deals.** Any future label
   for "not a deal" must use the event source, not the tape.
3. **`skew_63`'s short edge was deal targets, entirely.** Retired as a short.
4. **The leg-wise construction stands; its short leg is vacant.** D329's
   enumeration must be re-run under F0 and PUB before any partner is named.
5. **A short leg of deal targets carries a deal-break lottery.** Removing the
   deals removes the top tail. Whether that tail is tradeable on its own is a
   different study with a different framework.

## 7. What is owed

1. **D329's enumeration under F0 and PUB** — the honest ranking of short
   partners for `hist_L`-long, with the deal detector gone.
2. **The EDGAR second pass** (running) — a revision of this record if the
   resolved counts move the catch rate. The retirement is robust to it: more
   coverage removes more deals.
3. **Borrow**, now with the cohort identified: every name F0 flags.
4. **Deal breaks as a tail strategy**, if ever — out of scope here.

## 8. Assertions

All nine pass; all properties of the code, the data mapping, or a prior
record.

| | |
|---|---|
| **[K]** | deleting every filing dated after T0 = 2093 leaves the exclusion mask bit-identical through T0 |
| **[D]** | every applied filing sits in [first, last] live bar; F1 dropped 168 before-first, 0 after-death, 0 after-fixture |
| **[W]** | no exclusion runs past 189 bars from its filing or past the name's last live bar |
| **[I]** | D330 A's labels reproduce: 1,024 / 297 / 212 / 0 |
| **[1]** | the unfiltered arms reproduce D332's PB and PUB cells to 0.0e+00 |
| **[F]** | S_F1 differs from S on the short leg |
| **[L]** | LW_F1's long ledger is H's, its short ledger is S_F1's, both lenses |
| **[R]** | at all 2,022 bars where the rank-0 short name is excluded, a different name holds rank 0 |
| **[6]** | raises on a book handed free money |

**Speed:** 50 s.

## 9. Files

`data/d331_deal_filter.json` (second pass) · `temp/d331_deal_filter_v1.json`
(first pass, deletable) · `scripts/run_d331_deal_filter.py` ·
`data/fixtures/us_shorts_daily_raw_deals.json` (`c524dbf`; first pass at
`2abcb72`) · `data/d331_edgar_coverage.txt`

---

## 10. REVISION, same day — re-run on the EDGAR second pass (`c524dbf`)

§1–§8 were run on the first pass one minute before the second landed. The
second pass resolves 1,530 names (43 unresolved, all dead), adds 2,153
filings, and corrects one mismap (LNKD had been UBS). Every assertion passes
again, `[1]` to 0.0e+00. **Every conclusion above holds and every number moves
in the direction that firms it:**

| | first pass | **second pass** |
|---|--:|--:|
| F1 catch, overall / resolved | 78.8% / 92.8% | **87.3% / 90.7%** |
| F0 catch, overall / resolved | 71.2% / 83.9% | 76.9% / 79.9% |
| F1 survivors removed / F0 | 45.4% / 27.1% | 49.2% / 29.0% |
| F1 share of live name-bars excluded | 24.44% | 25.44% |
| `skew_63` short leg, F0, PB / PUB per trade | −29.8 / −64.7 | **−23.6 / −61.0** |
| `skew_63` short leg, F1, PB / PUB | −3.7 / −41.9 | −7.7 / −49.3 |
| LW_F1 per trade PUB / bp-bar PUB | +20.04 / −10.80 | +16.31 / −11.39 |
| trimmed-both mean, S → S_F1 | +46.8 → +62.4 | +46.8 → +56.4 |

**Q3 flips to CONFIRMED** (a 9.6 bp move) — four of nine on the second pass;
Q1, Q4, Q6, Q7, Q8 unchanged. The overall catch rate rises with coverage, as
§1 said it would; the resolved-name rate dips two points because the newly
resolved names are the harder ones. **The retirement in §5 stands on both
passes.**
