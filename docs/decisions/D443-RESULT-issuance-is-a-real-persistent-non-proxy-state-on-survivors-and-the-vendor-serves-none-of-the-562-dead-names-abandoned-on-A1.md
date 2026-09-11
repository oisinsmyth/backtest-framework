# D443 RESULT — net share issuance is a real, persistent, non-proxy state on the survivors, and the vendor serves none of the 562 dead names: ABANDONED on A1, as pre-registered

**A1 FIRES: dead-cohort coverage is 0.0% (bar 50%). The line is abandoned on this vendor, as §4 of
the spec said it would be; the survivor-only study is not run here.** A2 and A3 do not fire. Spec
`0fa0d5c` predates the fetcher, the runner and the pull (R8). **No forward return was read.** Pull
51 min (3,146 requests); panel 1 min; tables 0.3 min.

```
[L] every value usable from fiscalDateEnding + 90 d (asserted on all 53,231 rows);  [M] market cap = SO_adj x CLOSE at the fiscal bar
[S] 1.60% of usable rows flagged (|q-jump| > ln 1.5);  [G2] re-used tickers: 0;  selftest: split adjustment, restated series, NIY, Spearman/R2
```

---

## 1. Coverage — the number that decides

```
                       n     any report   usable NS
cohort  alive       1011      97.7%        93.9%
cohort  DEAD         562       0.0%         0.0%      <- A1: 562 of 562 tickers return {} from BALANCE_SHEET and CASH_FLOW
status  collapsed    122      99.2%        95.9%
status  survived     889      97.5%        93.6%
all                 1573      62.8%        60.3%
live name-years with a fresh NS at year end: 69%  (59% in 2011 rising to 86% in 2023 -- the dead drop out of the denominator over time)
```

**Alpha Vantage's fundamentals endpoints do not serve a delisted ticker.** Every one of the 562
dead-cohort names came back as an empty object (1,132 empty responses = 566 names, plus 34 error
responses on ETF-style tickers). Names that were acquired but are still on the vendor's roster
(SPLK, SGEN, KRTX — the padded "alive" names of D441) are served to their last filing; a name that
actually delisted is not. The fixture is dead-inclusive by rule (D140, 36% dead) and a study
that can only see survivors is a different study — the spec put that at 50% and the answer is 0%.
**Under §4 this ends the line on this vendor.** The rest of this record is what the survivors
say, kept because it settles the two other abandon conditions and prices the next source.

---

## 2. What issuance is, on the 988 names the vendor serves (no forward return)

```
NS = ln(SO_q / SO_{q-4}), split-adjusted, 38,799 usable name-quarters 2010-2023
  p5 -7.7   p10 -4.7   p25 -1.5   p50 +0.2   p75 +2.5   p90 +13.1   p95 +25.7  %/yr;   NS > 0 on 57%
  net equity cash flow in the trailing year: repurchase 62% of name-quarters, issuance 27%; NIY p10 -8.0 p50 -0.5 p90 +7.4 % of market cap
persistence (cross-sectional Spearman, 52 quarters): one year +0.441 +- 0.006, one quarter +0.799; top-decile issuers still in the top 3 deciles a year later: 62%; NIY one year +0.611
proxy check (52 quarter ends, 528 names each):  mom12 +0.070   ret20 -0.005   log price -0.179   log mcap -0.170   vol60 +0.167   log DV -0.159   rank R2 on all six 0.098 +- 0.006
by atlas state (mean NS, %/yr): vol_hi +5.5  price_lo +4.0  ret20_lo +3.2  ...  price_hi +1.2  vol_lo +0.9;  mom_hi - mom_lo = +0.5
```

**A2 does not fire.** The six axes the repo has already tested explain **10% of the rank variance
of issuance**; the largest single correlation is −0.18 with price. Issuance is *tilted* toward
small, cheap, volatile, thin names — the direction the literature says and X-d predicted — and it
is not any of them. It is almost orthogonal to momentum (+0.07) and to the 20-day return (0.00),
which is what D405's overhang was not. **A3 does not fire:** a name's issuance rank a year later
is 0.44 correlated with today's, and the top decile stays in the top three deciles 62% of the
time. The conditioner persists; a stage 1 conditioning on it would be conditioning on a state.

**The shape is not the textbook one.** The median name-quarter is +0.2%/yr, not the +1 to +2
of compensation dilution; **62% of name-quarters show net repurchase** (spec: 35–50%). This is a
1,000-name universe of listed US mid-caps in 2010–2023, the buyback era, and the survivors of it:
the repurchasers are over-represented precisely because the heavy issuers are in the cohort the
vendor does not serve. **That is the direction of the survivorship:** a survivor-only issuance
study would be missing the names whose issuance was followed by delisting, which biases the
short leg of the effect *toward zero*, not away from it. The bias is conservative for the
thesis; it is still a bias, and the fixture's rule exists so that it is not argued about.

---

## 3. Data disclosures — three things the vendor does that the spec did not know

1. **The spec's two flow fields are "None" on every report of every name** (`proceedsFromIssuance-
   OfCommonStock`, `paymentsForRepurchaseOfCommonStock`: 0 finite values in 53,231 report-fields).
   The one populated equity flow is the *net* field `proceedsFromRepurchaseOfEquity` (+ = cash in).
   NIY uses it; "any repurchase / any issuance" are its sign. Not a design change: the measure is
   the same net quantity, from one field instead of two.
2. **Shares outstanding are restated for later splits on about half the names and not the other
   half.** Of 694 split events inside the reports, 380 are visible in the raw share series (AHT
   2020: 1,004,700 → 103,100 across a 1:10) and **314 are not** (the vendor already carries the
   post-split figure in the earlier quarters; adjusting those again would print a −322% "buyback").
   The runner adjusts only the visible splits (`visible_splits`: the raw ratio closer in log to the
   coefficient than to 1). The selftest proves both branches. 14.4% of rows sit on a restated basis.
3. **The vendor's share counts carry gross errors on a few names** (CNOOC at 900 shares; WNW,
   STIM, HWM 2009) — the ten largest and ten smallest NS in `data/d443_stage0.json` §5 are mostly
   these, and the [S] flag catches 1.6% of rows. Every table is printed with and without them and
   nothing moves (median +0.2 both; persistence 0.441 vs 0.457).

Also disclosed: **a ticker re-use guard** ([G2], reports outrunning a dead name's last bar by
400 days) found nothing, because no dead name has reports at all.

---

## 4. Predictions — three of six held, and the two that failed are the finding

| | prediction | outcome |
|---|---|---|
| X-a | survived ≥ 95%, dead 60–85%, all ≥ 80% | survived 94%, **dead 0%**, all 60% — **FAILED: the vendor does not serve delisted names** |
| X-b | median +1..+2%, >0 on 60–70%, repurchase 35–50% | median **+0.2**, 57%, repurchase **62%** — the survivors are net repurchasers |
| X-c | persistence 1y 0.30–0.50, 1q 0.70–0.85 | 0.441 / 0.799 ✓ |
| X-d | mom +.05..+.15, mcap −.15..−.30, px −.10..−.25, vol +.15..+.30, ret20 ±.05, R² .10–.25 | +0.07 ✓, −0.17 ✓, −0.18 ✓, +0.17 ✓, −0.005 ✓, **R² 0.098** (just under) |
| X-e | flagged < 3% | 1.6% ✓ |
| X-f | highest in vol_hi / price_lo, lowest in price_hi, mom gap < 2 | +5.5 / +4.0, +1.2, +0.5 ✓ |

---

## 5. What this leaves — the principal's call

- **The object is good and the source is not.** Issuance in this universe is persistent (0.44 a
  year out), 90% orthogonal to everything tested here, and orthogonal to momentum in particular.
  Nothing in the stage-0 tables argues against it; the only thing that ended the line is that a
  third of the fixture is invisible to the vendor.
- **The source that serves dead names is EDGAR itself:** the SEC's XBRL `companyfacts` /
  `frames` API is free, keyed by CIK not ticker, and carries `EntityCommonStockSharesOutstanding`
  and the equity cash-flow tags for every filer including the delisted, with the **filing date**
  (which retires the 90-day assumption). The fixture already carries filings for the F0 window
  (`V31.DEALS`, 1,719 filings), so a CIK map for the 1,573 names exists in part. That is a data
  acquisition, not a study, and it is a separate record if the principal wants it.
- **Not recommended on this vendor:** a survivor-only stage 1. The bias direction is known (§2)
  and conservative, but the fixture's dead-inclusive rule is not a preference to be waived when
  the bias happens to point the safe way.

**Disposition is the principal's.**

---

## 6. R13

Forty-second look by object; first look at share supply; no forward return, no holdout. The
vendor's raw JSON is cached under `data/raw/alphavantage/fundamentals/` (git-ignored); the
derived panel `data/d443_issuance_panel.csv.gz` (53,231 rows, 988 names) and
`data/d443_issuance_panel_info.json` are committed with `data/d443_stage0.json`.
Runner `scripts/run_d443_issuance_stage0.py`; fetcher `scripts/fetch_av_fundamentals.py`.
