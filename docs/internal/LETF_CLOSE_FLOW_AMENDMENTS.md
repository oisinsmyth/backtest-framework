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

## LETF-A4. Open questions Q1 and Q2: defaults unless the principal says otherwise

*Source: proposed, 2026-09-27; the deposit asks for them before Phase 6.*

- **Q1 (costs):** the existing CostStack for MNQ/MES at the close, stated explicitly in the report; the ledger's
  dollar-at-micro-size standard (CLAUDE.md) applies to the component line.
- **Q2 (prop constraints):** the account parameters already used by the prop lifecycle runner and `BOOK_PROP.md`.
