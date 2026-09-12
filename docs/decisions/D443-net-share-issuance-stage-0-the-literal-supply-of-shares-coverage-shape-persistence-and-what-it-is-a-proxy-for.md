# D443 — net share issuance, stage 0: the literal supply of shares — coverage, shape, persistence, and what it is a proxy for

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. **Stage 0
reads NO forward return.** Number D443 taken after `ls docs/decisions` and `git log --all` on
2026-09-11 showed D440–D442 used on both branches (D440 and D442 twice each — one by the
`worktree-signal-hunt-part2` branch) and nothing at D443.

## 0. Why this, and why a stage 0

Six price-level programmes and the departure-zone line died the same way: every one was a function
of the past price path, and a rotation control that preserves the path and destroys the alignment
killed them (PICKUP 0d2). The state file names five sources that carry information the path cannot
and have zero decision files: short interest, insider transactions, **issuance and buybacks**, 13F
changes, index flows. Issuance is the one on the existing Alpha Vantage key. It is also the literal
thing the principal has been asking for — supply of shares — and it has a robust literature (net
issuers lag repurchasers by several percent a year, Pontiff–Woodgate 2008; Daniel–Titman 2006).

**A stage 0 because D405 taught the order:** the capital-gains overhang was abandoned at stage 0
when it turned out to be momentum in disguise, before a forward return was read. Issuance is
known to follow high past returns and to concentrate in small volatile names, so the first
question is whether, in this universe, it is anything beyond the axes the repo has already tested.
The stage-0 premise check (memory: measure the conditioner's own persistence before conditioning
on it) is the second.

## 1. Data, declared

For every one of the fixture's 1,573 names (`us_shorts_daily_raw`, dead-inclusive: 562 dead,
122 collapsed, 889 survived): Alpha Vantage `BALANCE_SHEET` and `CASH_FLOW`, quarterly reports.
3,146 requests at the key's 66/min, ≈ 50 min, paced and resumable; raw JSON cached under
`data/raw/alphavantage/fundamentals/` (git-ignored, D191: cache the raw, commit the derived).
**Probe before this record, disclosed:** three names were requested to learn the field names —
RH (81 quarters, 2003–2026), SPLK and SGEN (both acquired in 2024; both served to their last
filed quarter). No statistic was computed. The key is read from `~/.config/alphavantage/key` and
never printed or logged.

Fields used: `fiscalDateEnding`, `commonStockSharesOutstanding` (balance sheet);
`proceedsFromIssuanceOfCommonStock`, `paymentsForRepurchaseOfCommonStock` (cash flow; `"None"`
is missing, not zero). Splits: `commonStockSharesOutstanding` is as-reported, so it is put on a
constant basis with the cumulative `8. split coefficient` from the repo's `daily_adjusted` cache
(6,289 names cached) between fiscal dates.

**Point in time.** Alpha Vantage stamps the fiscal period end, not the filing date. **Every value
is usable only from `fiscalDateEnding + 90 calendar days`.** That is conservative for large filers
(10-Q due in 40–45 days) and about right for the smallest. Stage 1, if there is one, may tighten it
with the `EARNINGS` endpoint's `reportedDate`. Whether the values are as-first-reported or
restated is not documented by the vendor and is disclosed as unknown.

## 2. The measures (per name, per fiscal quarter q)

- **NS_q** = ln(SO_q / SO_{q−4}), split-adjusted shares outstanding, one year — the Pontiff–
  Woodgate net issuance.
- **NIY_q** = (Σ_{4Q} issuance proceeds − Σ_{4Q} repurchases) / (SO_q × raw close on the last
  fixture bar ≤ fiscalDateEnding) — the dollar net issuance yield; split-invariant by construction.
- Both attach to the fixture calendar at `d_q + 90` and are held until the next quarter's value
  arrives. A name-quarter is **usable** when SO_q and SO_{q−4} are both present and positive.
- **[S] jump guard:** a quarter where |ln(SO_q / SO_{q−1})| > ln 1.5 with no split coefficient ≠ 1
  inside the interval is *flagged* (counted and listed, kept in the panel with a flag; the
  stage-0 tables are printed with and without them).

## 3. Measured (no forward return)

1. **Coverage.** Names with ≥ 1 quarterly balance sheet; by cohort (dead / collapsed / survived);
   share of fixture name-years (2011–2023) with a usable NS; the first and last usable date per
   cohort. For dead names, the gap between the last filed quarter and the delisting date.
2. **Shape.** NS and NIY at every usable name-quarter: p5/p10/p25/p50/p75/p90/p95, share > 0,
   share with any repurchase, share with any issuance, by year.
3. **Persistence (the premise check).** Cross-sectional Spearman of NS_q with NS_{q+4} (one year)
   and NS_{q+1}, averaged over quarters; the same for NIY. Decile transition: the share of top-
   decile issuers still in the top three deciles a year later.
4. **Proxy check — the abandon test.** At each calendar quarter end, the cross-sectional Spearman
   of NS with the axes the repo has tested: 12-1 momentum, 20-day return, log price, log market
   cap (SO × raw close), 60-day realised volatility, log dollar volume; each averaged over
   quarters with its SE across quarters. Then the **rank R²** of NS on all six jointly (OLS on
   ranks, per quarter, averaged). Then NS's decile mean by atlas state (`mom_hi/lo`, `price_hi/lo`,
   `ret20_lo`, the D392/D434 terciles at that bar).
5. **The tails, named.** The ten largest NS name-quarters and the ten most negative, with the
   split flag, so the object is looked at before it is summarised.

## 4. Abandon conditions, written before the fetch

- **A1** dead-cohort coverage (≥ 1 usable NS) **< 50%** → the vendor cannot serve the dead-inclusive
  fixture; the line is abandoned on this vendor (a survivor-only issuance study is not run here).
- **A2** rank R² of NS on the six tested axes **> 0.50**, or |Spearman| with any single axis
  **> 0.40** → issuance is a proxy of something already tested; abandoned, as D405 was.
- **A3** one-year persistence **< 0.10** → the conditioner does not persist; a stage 1 would be an
  event study on the *change* in shares, not a state — the design is re-written, not proceeded.
- Otherwise stage 1 is drafted separately, with its state-matched control, its enumerated time
  rotation and its persistent-selector control declared at pre-registration.

## 5. Predictions (MODERATE; from the literature and the fixture's shape, none from this data)

- **X-a** coverage: survived ≥ 95%; dead 60–85% (acquisitions served, bankruptcies partly);
  overall ≥ 80%. Fixture name-years with a usable NS: 70–85%.
- **X-b** NS per name-quarter: median **+1% to +2%** (compensation dilution is near-universal),
  share > 0 **60–70%**, p10 ≈ −4%, p90 ≈ +15%, p95 > +25% (secondaries and stock acquisitions).
  Share with any repurchase in the trailing year 35–50%.
- **X-c** one-year persistence Spearman **0.30–0.50**; one-quarter 0.70–0.85 (overlapping windows).
- **X-d** Spearman with 12-1 momentum **+0.05 to +0.15** (issuers time run-ups); with log market cap
  **−0.15 to −0.30**; with log price **−0.10 to −0.25**; with 60-day volatility **+0.15 to +0.30**;
  with 20-day return within ±0.05; joint rank R² **0.10–0.25** — A2 does not fire.
- **X-e** flagged jumps < 3% of name-quarters; the ten largest NS are acquisitions-for-stock and
  secondaries, not data errors.
- **X-f** by atlas state: NS is highest in `vol_hi` and `price_lo`, lowest in `price_hi`; the
  `mom_hi` − `mom_lo` difference is under 2 points of NS.

## 6. Not in scope

Any forward return; any trade; any holdout; insider transactions, short interest (different
records if ever). First look at share supply by object (R13); look #0 of this line's ledger.

## 7. Files

This record · `scripts/fetch_av_fundamentals.py` (the paced, cached pull) ·
`scripts/run_d443_issuance_stage0.py` (panel build + the tables; `--selftest`) ·
`data/d443_issuance_panel.csv.gz` (derived, committed) · `data/d443_stage0.json` · RESULT.
