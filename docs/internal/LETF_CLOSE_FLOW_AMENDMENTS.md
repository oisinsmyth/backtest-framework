# LETF close-flow: amendments beside the read-only deposit

*The spec is `docs/internal/User-Doc-Deposit/LETF_CLOSE_FLOW_PREREG.md` v1.2, which stays read-only (its §0.2:
"any agreed change is made as a versioned edit … before code changes"). The agreed changes live here, each with its
source.*

## LETF-A1. The in-sample is run as written, with the prior reads disclosed

*Source: the principal, 2026-09-27 ("Run the deposit as written"), asked whether D530's prior test of the same
mechanism should move the test to the unread slice.*

- **The prior reads, stated in every result:**
  - **D530** (2026-09-14, "avenue 3", closed on the principal's word): the reset flow `L(L−1)·A·r` on ES/NQ/YM/RTY,
    2016-01-04 → 2023-12-29. Continuation did not rise with |return-of-day| (quintile 1 → 5: 47.2% → 50.6%, Q5
    z ≈ 0.49); the equity-index hit rate was 50.03% (z = +0.1). The closing-hour volume hump is real (1.10–1.48×).
  - **D463**: last-30-minute intraday momentum on 2010–2023: NQ −0.01, ES −0.29 net Sharpe.
  - **D487**: ES/NQ intraday continuation on 2016–2023 is a property of 2018 and 2022.
- **So** the deposit's H1 and H2 on 2016–2023 are not blind: their direction was read on close proxies (return-of-day
  in place of AUM-weighted flow, one entry time). The verdicts are computed and reported exactly as the deposit
  specifies; each result carries this disclosure, and a pass on 2016–2023 alone is weighed against it.
- **What is new relative to D530:** real AUM weights, the volume normalisation and the impact gate, entries at
  14:30 and 15:00, H3 (AUM scaling), H4 (the 11:00 placebo), H5, and the 2024-01-02 → 2025-02-28 slice, which none
  of D463, D487 or D530 read.

## LETF-A2. The programme split applies (A10)

*Source: the programme rule A10 (the principal, 2026-09-26).*

- **In-sample:** 2016-01-01 → 2025-02-28 (the deposit's "2016-01-01 to latest", cut at the vault).
- **Vault:** 2025-03-01 → 2026-09-18, scored only in the programme's joint vault run.
- **Forward:** from 2026-09-19 (Track 2 recorder; Track 3 as the deposit specifies).
- Every AUM, NAV or futures read uses `reserved_from="2025-03-01"`.

## LETF-A3. Direxion SPXL/SPXS: estimated from N-PORT, or sourced by the principal

*Source: the principal, 2026-09-27 ("Estimate from N-PORT, if it does not work then I will source").*

- **Checked 2026-09-27:** Direxion Shares ETF Trust (CIK 1424958; SPXL series S000022767, SPXS S000022765) files
  NPORT-P from 2019-12 (1,728 filings to 2024-12). Each carries the quarter-end `netAssets` and, for each of the three
  months, `monNFlow` (sales, redemptions, reinvestment) and `monthlyTotReturn`. So month-end net assets are rebuilt
  from 2019-Q3 onward.
- **The daily estimate:** from each month-end anchor, AUM carried by the fund's own NAV path (L × the index return,
  less fees) plus that month's net flow spread evenly. **Its error band is measured, not assumed:** the same
  procedure is run on the eight ProShares funds, whose daily truth is known, and the per-day error distribution is
  the band.
- **Before 2019-Q3:** N-SAR (monthly sales and redemptions, to mid-2018) and N-CSR (semi-annual) are checked next.
  If they do not close the gap, the principal sources it (their ruling); until then Direxion is excluded from the
  years it cannot cover, with its share of the S&P complex measured and reported.
- **"Does not work"** (proposed, not yet the principal's) means: the rebuilt month-ends miss N-PORT's own quarter-end `netAssets` by more than 1%, or the
  ProShares-measured band moves more than 10% of days' flow sign or impact gate.

## LETF-A5. Direxion's estimate is accepted; the spot-check bar is the method's own measured distribution

*Source: the principal, 2026-09-27 ("Accept the estimate, transcribe the pre-2019 filings, start NQ Phase 2"), on
D637. Replaces LETF-A3's proposed "does not work" bar (1% at every quarter-end), which the method fails on the
ProShares funds too (58 of 168 quarters over 1%, max 13.3%).*

- **Direxion's G3 (spot checks):** the forward check at each filed quarter-end (before correction) must lie within
  the same estimator's distribution on the ProShares funds' own filings: every |miss| at or below that
  distribution's maximum, and the share of quarters over 1% no higher than the ProShares share plus two binomial
  standard errors. Both numbers are computed by `scripts/build_letf_aum.py` and written into `gate0.json`.
- **2016-01 → 2019-10:** the pre-N-PORT filings (N-Q, N-CSR, N-CSRS, N-SAR) are transcribed with citations, and the
  band is re-measured for the flow granularity those filings allow.
- **NQ proceeds to Phase 2** on its complete panel; ES follows once the pre-2019 Direxion anchors are in.

## LETF-A6. How the pre-2019 Direxion filings are used (implementation of LETF-A5; D637 addendum)

*Source: implementation, 2026-09-27, after the transcription. Stated so a reader can reproduce or dispute it.*

- **Anchors on one basis:** N-CSR/N-CSRS net assets are converted to N-PORT's basis (receivable for shares sold
  removed, payable for shares redeemed added back; at 2019-10-31 this reproduces N-PORT to about $10k). N-Q and
  NPORT-EX totals are used as filed (their basis cannot be tested).
- **Flows:** N-SAR monthly to 2017-10 (walked forward, checked at each quarter-end). From 2017-11 to 2019-07 each
  quarter's flow is solved from its two anchors and checked against the half-year statement totals.
- **G3 per regime:** each check is judged against the same procedure's distribution on the ProShares funds, run on
  Direxion's quarter calendar and flow granularity.
- **The 2017-11 → 2019-07 stretch carries the wider measured band** (ProShares daily error p95 16% vs 10–11%
  elsewhere). The ES results are reported with and without it.
- **LETF-A3 corrected:** N-SAR's monthly flows end at October 2017, not mid-2018.

## LETF-A7. A second pre-registered reading: each cell against the model's OWN predicted impact

*Source: the principal, 2026-09-27 ("Yes, add LETF-A7, then build the runner"), on D639's POWER step
(`docs/results/LETF_CLOSE_FLOW_POWER.md`). Written after POWER, which read no return, and before any runner exists. It
adds a reading and changes no test, threshold or gate of D639.*

- **Why.** Against D639's default plausible effect (the cost, about 1.6 bp on NQ) every primary cell is
  underpowered, so an H1 null would be "inconclusive". But an active day is, by construction, one where the model
  predicts an impact I ≥ 3 × cost: about 10 bp on NQ, which the NQ cells can detect even at Holm 80% (MDE 5.4–8.3 bp).
  Without this reading, a null could never count against the mechanism the model claims.
- **The statistic, per primary cell** (and at τ = 11:00 for H4): the calibration ratio **β = mean(s) / mean(I_bp)**
  on the active days.
  - s is D639 §3's signed return in bp.
  - I_bp = I / P(t, τ) × 10⁴, the model's own predicted impact for that day.
  - The 90% confidence interval on mean(s) uses D639's HAC standard error and lag rule; I_bp's mean is treated as
    known (it is the model's claim).
- **The labels** (one-sided 5% each; across the six cells the "BELOW" and "ABOVE" labels are Holm-adjusted):
  - **BELOW THE CLAIM:** the upper 95% bound of β < 1. The move is smaller than the model predicts. With an H1 fail
    this is a POWERED NULL against the mechanism, not an inconclusive one.
  - **AT THE CLAIM:** the interval contains 1.
  - **ABOVE THE CLAIM:** the lower 95% bound of β > 1.
- **What it does not do:** it is not a gate, and it cannot turn an H1 fail into a pass or a pass into a fail. It is
  reported beside H1 for every cell. ES cells carry POWER's note that they are underpowered even for their own
  prediction (MDE 27–38 bp against about 15 bp).

## LETF-A4. Open questions Q1 and Q2: defaults unless the principal says otherwise

*Source: proposed, 2026-09-27; the deposit asks for them before Phase 6.*

- **Q1 (costs):** the existing CostStack for MNQ/MES at the close, stated explicitly in the report; the ledger's
  dollar-at-micro-size standard (CLAUDE.md) applies to the component line.
- **Q2 (prop constraints):** the account parameters already used by the prop lifecycle runner and `BOOK_PROP.md`.
