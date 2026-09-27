# D637 — RESULT: LETF close-flow Gate 0. The Nasdaq set PASSES; the S&P set is estimated from 2019-10 and MISSING 39% of its flow before that

*2026-09-27. The principal: "Yes, build Phase 1 and Gate 0". Spec: `LETF_CLOSE_FLOW_PREREG.md` v1.2 §3.2 and §9
(read-only), with LETF-A1..A4 (`docs/internal/LETF_CLOSE_FLOW_AMENDMENTS.md`). No return of any kind was computed.
Nothing dated on or after 2025-03-01 was parsed (A10).*

Reproduce: `uv run python scripts/build_letf_aum.py --selftest`, `--fetch` (EDGAR, cached under
`data/raw/letf/nport/`), `--build` → `data/letf/letf_aum_daily.csv.gz` (+ `.meta.json`), `data/letf/gate0.json`,
`data/letf/nport_reports.json`. The deposit asks for Parquet; the uv environment has no parquet engine, so the panel
is `.csv.gz` with the deposit's columns plus `estimated`.

## Verdict

| set | funds | span | Gate 0 |
|---|---|---|---|
| **Nasdaq-100 (NQ)** | TQQQ SQQQ QLD QID (issuer data) | 2016-01-04 → 2025-02-28 | **PASS** |
| **S&P 500 (ES)**, ProShares | UPRO SPXU SSO SDS (issuer data) | 2016-01-04 → 2025-02-28 | **PASS** |
| **S&P 500 (ES)**, Direxion | SPXL SPXS (estimated, LETF-A3) | 2019-10-31 → 2025-02-28 | **FAILS the 1% spot-check bar LETF-A4 proposed; that bar is miscalibrated (below)** |
| | SPXL SPXS | 2016-01-04 → 2019-10-30 | **NO DATA** |

**By the deposit's §0.3 this is a stop-and-report at Gate 0 for the ES cells.** The NQ cells have a complete,
verified AUM panel.

## The eight ProShares funds: every check passes

- **Source:** the issuer's all-funds historical NAV file (the principal's). 2,303 rows per fund, the in-sample span.
- **G1 gaps:** none. Every fund has a row on every one of the 2,303 SPY trading days (Alpha Vantage calendar,
  independent of the issuer), and no row off it.
- **G2 |ΔAUM| > 25%:** 26 days across the eight (QID 12, UPRO 4, TQQQ/SQQQ/SPXU 3, SDS 1). Each is explained,
  either by a split within 3 days (ProShares' split file) or by NAV return plus creations to within 1%.
- **G3 spot checks:** 22 per fund against ProShares Trust's own N-PORT quarter-end net assets (EDGAR,
  2019-11 → 2025-02). **The largest miss is 0.011%**, once the two bases are aligned (below).
- **Identity (diagnostic, not a gate):** NAV × shares = the published AUM within 1 bp on ≥ 99% of rows for seven
  funds. SQQQ reads about 0.33% low on 684 rows in 2016–2019: its NAV and share columns are restated for later
  reverse splits and rounded. The model uses the published AUM, which G3 verifies.

### Found and fixed on the way, each shown on the data

1. **N-PORT's `<repPdEnd>` is the fund's FISCAL YEAR-END, not the report date** (`<repPdDate>`). The first fetch
   keyed on it. Because every filing it parsed had a fiscal year-end before the seal, no sealed period was read.
   But the report dates were wrong, and up to 3 of 22 quarters per fund were dropped. Fixed and re-fetched.
2. **Direxion files redemptions as negative numbers, ProShares as positive.** Net flow now subtracts the
   magnitude.
3. **The issuer's AUM and a fund's books count shares on different days.** ProShares' shares and AUM for day t
   already include day t's creation and redemption orders; the books (and N-PORT) take them in on t+1. So
   N-PORT = NAV(t) × shares(t−1). Checked by hand on TQQQ and QID at 2020-11-30, 2021-02-26 and 2021-05-28: equal to
   the digits filed. Unaligned, the spot checks missed by up to 25% (QID) and looked like a data failure. **The
   issuer's figure is the model's A[t−1]**: it includes the orders the fund hedges at that close.

## Direxion SPXL/SPXS (39% of the S&P set's flow)

- **Weight:** Direxion is **39%** of the S&P set's rebalance weight Σ L(L−1)A over 2019-10 → 2025-02 (p05 31%,
  p95 45%; 30% in 2019, rising to 45% in 2024). So it cannot be dropped without changing the ES signal materially.
- **Source:** Direxion Shares ETF Trust N-PORT (CIK 1424958), 22 quarterly filings per fund, 2019-10-31 → 2025-01-31.
  The issuer offers no history.
- **Estimator** (after a first form, a monthly walk-back, broke in 2020-Q1, where −47% and +37% months met $843m of
  March inflow):
  - from each filed quarter-end, compound the same-benchmark ProShares NAV (SPXL ← UPRO, SPXS ← SPXU);
  - add each month's filed net flow evenly over its trading days;
  - compare with the next filing (the check);
  - spread the residual geometrically over the quarter, so every filing is hit exactly.
  - After the last usable filing (2025-01-31, since the next one's period includes the vault), February 2025 is
    carried on the path alone and flagged.
- **The path proxy is close:** each fund's filed monthly return against the proxy's month differs by p95 0.27%
  (SPXL) and 1.85% (SPXS).
- **The checks:** SPXL misses > 1% in 8 of 21 quarters (max 12.7%), SPXS in 10 of 21 (max 6.6%).
- **The same estimator on the ProShares funds' own filings, where the daily truth is known:**

| | quarter-end check before correction | daily error after correction (vs issuer AUM) |
|---|---|---|
| ProShares, 168 quarters / 10,552 days | median 0.64%, p90 3.3%, max 13.3%, **58 of 168 over 1%** | median 1.8%, p95 10.7%, p99 19.9% |
| SPXL / SPXS, 21 quarters each | 8 and 10 over 1%, max 12.7% / 6.6% | (not observable) |

  **So Direxion's residuals are the method's own**, of the same size on funds whose data is known to be right. The
  error is flow timing within the quarter, not the filings. LETF-A4's proposed "1%" bar would reject the method on
  the ProShares funds too, so it was set without this measurement and should be replaced.
- **What the band does to the model:** at Direxion's mean share, the daily band moves Q_SPX by 0.7% (median),
  4.2% (p95) and 7.8% (p99). It moves the predicted impact I ∝ √|q| by **0.35%, 2.1% and 3.9%**. The flow's SIGN
  never depends on A: every fund's ΔH has the sign of r.

## Before 2019-10: what exists

Direxion filed no N-PORT before 2019. Its trust (checked 2026-09-27, form counts only):
- N-SAR A/B through 2017, carrying monthly flows and period-end net assets;
- N-Q in 2015–2019 (January and July quarter-ends);
- N-CSR/N-CSRS (October and April).

So quarter-end net assets exist for the whole gap, and monthly flows to 2017. They sit in multi-fund HTML documents:
about 28 numbers per fund to transcribe with citations, and the band would have to be re-measured with quarterly (not
monthly) flows after 2017.

## Rulings needed from the principal

1. **Direxion 2019-10 → 2025-02:** accept the estimate with its measured band, replacing LETF-A4's 1% bar with
   "residuals within the method's own distribution on the ProShares funds"; or exclude it, or source daily data.
2. **Direxion 2016-01 → 2019-10** (39% of the ES flow): transcribe the N-Q/N-CSR/N-SAR anchors (cited, band
   re-measured), or source it yourself, or start the ES in-sample at 2019-11 (the deposit's Q3, which needs a written
   answer).
3. **The NQ cells** can proceed to Phase 2 now on a complete panel, or wait so both instruments move together.

## Addendum, 2026-09-27: Direxion 2016-01 → 2019-10 from the pre-N-PORT filings (LETF-A5). Gate 0 PASSES on every row

*The principal: "Accept the estimate, transcribe the pre-2019 filings, start NQ Phase 2".*

**Transcription.** `scripts/fetch_direxion_pre2019.py` → `data/letf/direxion_pre2019_filings.csv`, 398 rows from 24
EDGAR filings (N-CSR, N-CSRS, N-Q, NSAR-A/B, one NPORT-EX), each with its accession, locator and a quote of 14 words or
fewer. `--check` re-finds every quote in the cached bytes and re-parses its value (all 398 pass).
- **Coverage:** every quarter-end 2015-10-31 → 2019-10-31 has net assets for both funds (17 of 17).
- **Statement identity:** exact to the dollar in all 20 periods.
- **N-SAR 74T vs the statements:** within $897.
- **Monthly flows:** N-SAR's monthly flows end at **October 2017** (LETF-A3's "to mid-2018" is wrong). The 2019-07-31
  schedule is an NPORT-EX, not an N-Q (§ "Before 2019-10" above is wrong on that one date).
- **N-SAR vs statement half-years:** three disagree, all flagged in the CSV. NSAR-B 2015 (both funds) reports the fiscal
  year, not the half; this is outside the window used. SPXL's NSAR-B 2017 sales exceed the statements by $2.05m (0.3% of
  net assets).

**The anchors' basis.** An N-CSR/N-CSRS net-assets figure includes creations and redemptions traded but not settled.
At 2019-10-31 the N-CSR differs from N-PORT by −1.44% (SPXL) and +4.10% (SPXS). Removing the receivable for shares sold
and adding back the payable for shares redeemed reproduces N-PORT to −$4,094 and −$11,202. So every N-CSR/N-CSRS anchor
is converted to the books' basis before use. The N-Q and NPORT-EX totals are used as filed: their basis cannot be
tested, since no filing overlaps them. The statement-basis gap, where it could be measured, was a median of 0.008%
(SPXL) and 0.0% (SPXS), with maximums of 1.1% and 5.2%.

**Two flow regimes, each banded on the ProShares funds by the identical procedure (Jan/Apr/Jul/Oct anchors):**

| span | flows | Direxion check | ProShares, same procedure: check | ProShares daily error vs issuer AUM |
|---|---|---|---|---|
| 2015-11 → 2017-10 | N-SAR monthly, walked | quarter-end miss: SPXL max 5.8%, SPXS max 4.8% | median 1.3%, max 19.8% | median 1.7%, p95 10.0%, p99 18.5% |
| 2017-11 → 2019-07 | none monthly; each quarter's flow SOLVED from its two anchors | solved half-year flow vs statement: 0.4–8.4% (SPXL), 2.6–10.4% (SPXS) of net assets | median 2.3%, p90 9.9%, max 33% | **median 3.0%, p95 16.0%, p99 30.7%** |
| 2019-08 → 2025-02 | N-PORT monthly (unchanged) | as above | as above | median 1.8%, p95 10.7% |

A first form of the middle regime spread each half-year total evenly. It hit every half-year total, but split it
between the two quarters wrongly (SPXL +31.8% then −27.9%), so it was replaced by the solved form.

**Gate 0 (LETF-A5 rule, per regime):** SPXL and SPXS PASS. The worst |miss| is 0.95× the ProShares maximum for SPXL and
0.50× for SPXS. The share of checks over 1% is 58.8% and 52.9%, against an expected 44.1% + 2 SE (16.4%). **All ten
funds now pass on every row, 2016-01-04 → 2025-02-28; the ES set is complete from 2016-01.**

**The caveat that travels with ES:** from 2017-11 to 2019-07, Direxion's daily AUM (39% of the S&P flow) carries the
wider band: p95 16% at the fund, so p95 about 3% on predicted impact at the mean share. Phase 3 reports the ES cells
with and without that stretch.
