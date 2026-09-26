# AI TODO

> **The live task list, kept current from 2026-09-24 on the principal's instruction.** Update it
> at the end of every working session; an entry that is done or dropped is removed, not left to go
> stale. The build-phase list this file held until 2026-09-01 is in git history at `f78786e`
> (`git show f78786e:docs/internal/AITODO.md`).

## Settlement flow ledger — the full study, one problem at a time (opened 2026-09-24)

**The standard, the principal's, 2026-09-24:**
- The starting position: *"I dont want a partial test, I dont want any reason to handwave the
  results or doubt them."* So no Stage A-lite, no partial Gate 0, and no forward-only stand-in for a
  backtest stage.
- Relaxed the same day for inputs that cannot be observed for free: an estimate is acceptable if it
  is *"directionally correct"*. It must carry a measured band, smaller size and larger error bars.
  The binding form is the amendments A1–A5 in
  [`SETTLEMENT_FLOW_LEDGER_AMENDMENTS.md`](SETTLEMENT_FLOW_LEDGER_AMENDMENTS.md), which sit beside
  the read-only deposit.
- The document is `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md`. The
  infrastructure already built is in [`DEPOSIT_INFRASTRUCTURE_TRACKER.md`](DEPOSIT_INFRASTRUCTURE_TRACKER.md).

**Measured 2026-09-24, from free Databento metadata calls; nothing spent:**
- CME market-by-order history begins **2017-05-21**, so Stage H cannot start earlier from any source.
- Databento's consolidated equity NBBO begins in **2023**. The listing venue, NYSE Arca, where all six
  ETFs list, begins **2018-05-01**. A true NBBO from 2016 needs NYSE TAQ from another vendor.
- Aggressor-signed CL/NG trades are on disk only for 2025-09 → 2026-09, which is inside the vault.

**DATA GAPS REGISTER (2026-09-24; the principal can't buy more data, and will source some items).**
"Weakened" means a free substitute exists, as an estimate or a proxy. "Missing" means there is no free
source.

| # | information | stage / test | status | free substitute or note |
|---|---|---|---|---|
| G1 | aggressor side of CL/NG trades, 2017-05 → 2025-09-24 | **A (the kill test)**, B, I, H5 | **MISSING: the estimate FAILED (D624 RESULT, 2026-09-25)** | One-second bars cannot sign settlement-window flow (sibling r −0.22 to −0.03 against the 0.8 bar). **The principal will source it.** The cheapest real route is window-only `trades` (14:28–14:30 plus 11:50–12:20 ET): ~$108 in-sample, ~$7.50 vault |
| G2 | aggressor side of TAS trades | D | WEAKENED | estimated from one-second bars |
| G3 | ETF bid/ask (NBBO) quotes before 2023-03-28 | C2 premium | WEAKENED | see the ETF-premium options in the reply of 2026-09-24; the principal is choosing |
| G4 | ETF trades with aggressor side | C1 features, C3 H11a | WEAKENED | estimated from Alpha Vantage 1-minute bars; thin funds have sparse minutes |
| G5 | CL/NG order book (depth) history | **H** | MISSING | only the last month is free. **Principal will source it** |
| G6 | daily futures/swap split and months held | A (f_fut), E, F | WEAKENED | estimated with a band (item 1). Proven where it can be |
| G7 | UNG/USO daily shares outstanding | C1 creations | WEAKENED | exact month-ends and monthly creation totals; daily figures interpolated |
| G8 | USO's weights by contract month, 2020-04 → 2023 | F rolls, P1 held month | WEAKENED | documented allocations and the ladder estimate (±2.7 pp) |
| G9 | each fund's execution time of day (settlement, TAS or earlier) | A (where the flow lands), D | MISSING | the filings are silent (item 9). Not for sale |
| G10 | whether the funds use TAS (Q2, D4) | D, F (P6 split) | MISSING | the filings are silent |
| G11 | 10 other fund facts (D619) | several | MISSING / to source | item 9 |
| G12 | social-media archives (Q12) | C3 social part | MISSING | **kept OPEN: the principal will source it** |
| G13 | hourly Wikipedia views | C3 | FREE but ~2.5 TB | daily views under D621's amendment, or the full download |
| G14 | swap dissemination history (DTCC) | E netting, H15 | **FREE, partial (checked 2026-09-25)** | DTCC's public daily cumulative commodity files, no files downloaded yet. See the note below the table |
| G15 | non-US products (BetaPro, WisdomTree): NAV, units, leverage, restrikes | G | **PARTIAL (checked 2026-09-25)** | See the note below the table |
| G16 | official intraday NAV (IIV) history | validation only | MISSING | not needed: the rebuilt iNAV passes Gate 0b |
| G17 | vault trades with aggressor side, 2025-03-01 → 2025-09-24 | the vault look | WEAKENED | the same one-second estimate, which keeps the method consistent |
| G18 | CL 2020-04-01 → 09-16 | all CL stages | EXCLUDED | A1 |
| G19 | USO roll days 2017 → 2020-04 | F | **PROVEN 2026-09-25** | `check_uso_monthly_rolls.py`: exact NAV÷shares 0.81 bp against 3.11, sign test 33–5 (p 2e-6), both controls fire; UNG's known answer re-identified |
| G20 | the item-1 estimates run only to 2023-12 | A–F | **Stage A's part DONE 2026-09-25** | See the note below the table. UNG/USO month-ends, AUM and USO weights past 2023 are still to extend; Stage A doesn't need them |

**G14, the detail.** DTCC's public daily cumulative commodity files are free.
- `…/slices/CUMULATIVE_COMMODITIES_YYYY_MM_DD.zip` returns 200 from 2013-06 to 2020-11; `…/cftc/eod/…` from
  2020-11 onward.
- The whole 2017 → 2026 span is ~0.3–0.5 GB.
- It covers DTCC-reported swaps only. ICE Trade Vault needs its terms accepted, and CME's SDR blocks scripts.

**G15, the detail.**
- BetaPro (betapro.ca) has free daily NAV back to 2008, embedded in each product page. Units outstanding and
  leverage are current values only. The leverage changes are dated from press releases: HOU/HOD went to 1x on
  2020-04-22, to 1.5x on 2020-11-10 and back to 2x on 2021-01-20; HNU/HND changed index on 2020-08-27.
- WisdomTree's NAV history is behind an investor-type and terms dialog. Its restrike history is public only
  from 2024-08 (GlobeNewswire), with earlier events likely in LSE RNS. The ISINs changed, so series need
  chaining.
- FX is free: the Bank of Canada Valet API, the ECB data API and the Bank of England database.

**G20, the detail.** Both extensions run under `--seal a6` (`reserved_from="2025-03-01"`), and both original
outputs stay byte-identical.
- **f_fut, to 2025-02-28** (`estimate_fut_share.py --seal a6`):
  - BOIL, KOLD and SCO are proven through 2024; UCO is interpolated through 2024.
  - January–February 2025 are carried from 2024-12-31, which was filed 2025-02-28.
  - h is now 0.162 (70 quarter-ends; it was 0.151).
  - UCO's 2024-Q2 is newly flagged DISFAVOURED.
- **NG contract counts** (`check_ng_contract_counts.py --seal a6`): reading C matches 57 of 57 futures-only
  quarter-ends, a maximum error of 0.13%.
| G21 | live feeds for Tracks 2 and 3 | forward | COSTS | CME $199/month; ETF live quotes not checked |

**Taken one at a time, in this order.** `[>]` means in progress. Each item names who owns it.

- **1 and 2 are CLOSED (2026-09-24).** Their records are in PICKUP.md, "SETTLEMENT LEDGER, ITEMS 1
  AND 2". The amendments A1–A6 are in `SETTLEMENT_FLOW_LEDGER_AMENDMENTS.md`.
  - **The seal is the deposit's vault (A6).** In-sample runs to 2025-02-28, and every read uses
    `reserved_from="2025-03-01"`.
  - Gate 0b passes on 2024-01 → 2025-02 for all four ProShares funds (1f).
  - **Carried forward to item 11:** extend `estimate_fut_share.py` and the USCF estimates from
    2023-12 to 2025-02 under the new cut. The 2023-12-31 schedules are now readable.
  - Carried forward to item 9: the execution time of day.
- **3. The sample start. CLOSED 2026-09-24 (amendment A7, the principal's "choice one").**
  - The in-sample is 2017-05-22 → 2025-02-28: NG 1,955 business days, CL 1,839.
  - C2 and C3's ETF-volume test run on a declared 2018-05-01 sub-sample, on Arca's best bid and
    offer.
  - Before C2 runs, Arca is checked against the NBBO on 2023-03 → 2025-02.
- [ ] **4. ETF quote history for the premium in Stage C2** (Claude to price, principal to approve;
      deposit Q8). A true NBBO means NYSE TAQ, not yet priced. The Arca-only option (bbo-1m plus
      trades, 2018-05 → 2023) costs **$11.10**, but a listing venue's quote is not the NBBO the
      document specifies.
- [ ] **5. UNG and USO daily shares for creations** (Claude; Stage C1).
      - **Now in hand (item 1):**
        - exact month-end NAV and shares, 2017–2023, from the monthly statements;
        - a daily AUM estimate with shares linear between month-ends, band −12% to +18%.
      - **Still missing:** a DAILY shares count, which C1's creation flow differences. The
        interpolated series must not be differenced for flow.
      - **What C1 can use:**
        - the monthly shares_added and shares_withdrawn (exact, but month totals);
        - or a free daily source, not yet found. USCF's history endpoint needs its site API key,
          which is not used.
      - This does not affect P1: at L = +1, P1 is zero.
- [>] **4 + 6. RE-QUOTED 2026-09-24 under A6 and A7** by `scripts/quote_ledger_pulls.py`
      (`data/ledger_pull_quote.json`). Metadata calls only; nothing was submitted.
      - **In-sample:**
        - ETF Arca best bid/offer (1-minute) plus trades, 2018-05 → 2025-02: $14.38;
        - consolidated best bid/offer for the Arca check, 2023-03-28 → 2025-02: $0.54;
        - TAS trades: $2.67;
        - CL/NG trades, whole days $1,024.23, or WINDOWED (13:30–14:45 plus 10:30–12:30 ET)
          about $397;
        - CL/NG order book, whole days $7,232.23, or WINDOWED (13:30–14:35 ET) about $916.
      - **Vault, bought only for the one look:** Arca $9.01, consolidated $0.47, trades windowed
        about $28, TAS $0.23, order book windowed about $231.
      - **Why the subscription doesn't cover it** (Databento's pricing page, checked 2026-09-24, and
        confirmed by quotes):
        - CME Standard ($199/month) includes the full history for OHLCV, definitions, statistics
          and status.
        - It includes only the **last 12 months** for trades, TBBO and BBO: $0 from 2025-09-25,
          and billed before that.
        - It includes only the **last month** for MBO and MBP-10: $0 from 2026-08-25, and $110
          for July 2026.
        - Full trade history needs Plus ($1,750/month, annual contract). Full MBO history needs
          Unlimited ($4,500/month, annual).
        - NYSE Arca is equities and isn't in the CME plan at all.
        - The vault's trades from 2025-09-11 are already on disk: `tbbo`, every instrument.
      - **THE PRINCIPAL CANNOT BUY MORE DATA (2026-09-24). Free route approved ("go for the free
        data pulls"):**
        - Databento `ohlcv-1s` for CL, NG, CLT and NGT, 2017-05-21 → 2026-09-19, $0 under the
          subscription. Signed flow will be ESTIMATED from these bars.
        - Databento `trades` after the vault, 2026-09-19 →, free (last 12 months). This is the
          ground truth for validating the estimate, outside both the in-sample and the vault.
          **Top it up before the subscription lapses (~2026-10-11).**
        - Alpha Vantage 1-minute bars for the six ETFs, 2017-05 → 2026-09, on the principal's paid
          key. They stand in for the NBBO quotes and signed ETF trades.
        - Script: `scripts/fetch_ledger_free.py`. Job record: `data/ledger_free_pull_jobs.json`.
        - **ON DISK 2026-09-24, every job billed $0.00:**
          - `ohlcv-1s` CL, 2.20 GB, and NG, 1.09 GB, compressed;
          - `ohlcv-1s` TAS, 0.02 GB;
          - post-vault `trades` 2026-09-19 → 09-23, 0.03 GB;
          - all under `data/raw/databento/<job id>/`.
          - Alpha Vantage: 678 slices, no failures, under `data/raw/alphavantage/1min/`. Regular-hours
            minutes with a bar: USO 99%, UNG 95%, UCO 94%, SCO 91%, BOIL 77%, KOLD 67%.
      - **DECIDED 2026-09-24 (principal):**
        - **The Stage A bar:** Stage A's kill test may run on the one-second estimate of signed flow
          only if, per root, the day-level correlation between estimated and true signed flow in
          the settlement window is **≥ 0.8**.
          - It is measured on the post-vault true trades, topped up before ~2026-10-11.
          - Below 0.8, the principal sources the real data.
          - This bar is fixed before any validation number is computed.
        - **The ETF premium:** Alpha Vantage 1-minute bars, time-averaged, anchored on the exact
          daily closing premium. **IEX's free historical quotes** measure the trade-price bias on a
          sample of days. The principal accepts IEX's terms for this use. The file names and sizes
          are stated before downloading.
          - **DONE 2026-09-25.** IEX TOPS on 10 days, 2018-06-13 → 2024-07-17: 24.3 GB streamed = listed on every
            day, and every packet's message count checked. Filtered to the six ETFs under `data/raw/iex/`. Record:
            `data/ledger_iex_sample_pull.json`.
          - Bias check (`scripts/check_etf_premium_bias.py` → `data/ledger_etf_premium_bias_check.json`):
            - Alpha Vantage bars are stamped at the minute's START (exact matches 25.7% against 10.3%).
            - The close's mean bias against the mid is below 1.3 bp for every ETF, and below 0.5 bp wherever
              the sample gives an SE under 1 bp (USO +0.06 ± 0.11; UNG +0.04 ± 0.16). Per-minute noise has an sd of
              3–10 bp.
            - The primary measure uses one-tick IEX minutes only, where IEX's quote is the national best. That
              covers USO 23%, UNG 15%, SCO 13%, BOIL 6%, and KOLD and UCO under 1%, which rest on the ≤ 3-tick
              sample.
            - **So the close stands in for the mid in a time-averaged premium.**
      - **D624 RESULT (2026-09-25): the siblings do NOT agree.**
        - E2 was chosen at a first-half mean r of 0.33. On the second half it scored r −0.03 (HO) and
          −0.22 (RB).
        - **So neither CL nor NG runs Stage A on the estimate.**
        - The NG/CL gate phase is moot for the decision. The free top-up is SCHEDULED for Sat 2026-10-10 08:00 (task `d624-ng-cl-free-topup`; it also reads D625), as
          a record only, and it is the principal's call.
        - Record: `docs/decisions/D624-RESULT-one-second-bars-cannot-carry-settlement-window-flow.md`.
      - **The Stage A validation, as planned** (pre-registration committed `6e1bfa4`, 2026-09-24).
        Runner `scripts/validate_flow_estimate.py`, which passes its selftest.
        - **Sibling phase (HO/RB):** runs when the free sibling pull lands
          (`data/ledger_sibling_pull_jobs.json`).
        - **NG/CL gate:** read ONCE, after the top-up. **Top-up scheduled Sat 2026-10-10 08:00 (15 sessions incl. Fri 10-09):** free `trades` and
          `ohlcv-1s` for CL/NG/CLT/NGT from 2026-09-19. Its job record must be
          `data/ledger_topup_pull_jobs.json`, with labels `topup-trades` and `topup-ohlcv1s`.
        - **Outcomes:** PASS ≥ 0.8; UNRESOLVED near miss 0.70–0.80; FAIL < 0.70; UNRESOLVED below 15
          sessions. The siblings must agree.
      - **A8 WRITTEN 2026-09-25** (it replaces the held draft):
        - **Stage A's H1 becomes H1a:** does the predicted flow's SIZE explain abnormal window volume
          (free one-second bars, exact), with controls for |return|, activity and calendar flags?
          - It must beat an 11:50–12:20 placebo and a day shuffle.
          - τ is the earliest-pass time. TAS volume is reported beside it.
        - **Direction rests on H2.**
        - C2 runs on Alpha Vantage bars.
        - Stage H is forward-only.
        - Stage B, Stage I, H8a and H9 are blocked until real signed flow exists.
        - **Option 2, done 2026-09-25:** D625 did not pass, because its control fired on a base-rate
          effect. Post hoc, the TAS level reads backwards (κ +0.33 to +0.49, reversed sign).
          - **D626** (committed `9ee8142`) tests the reversed sign on data no one has read: pooled κ ≥ 0.2
            over CL, NG, HO and RB, with CL and NG each > 0.
          - Runner `scripts/validate_tas_sign.py`, uncommitted until its result.
          - **Read once by the scheduled task on Sat 2026-10-10.** A pass writes H1b, after its own
            pre-registration.
        - **H1a's inputs, BUILT 2026-09-25 (uncommitted), in-sample 2017-05-22 → 2025-02-28 under A6:**
          - Step 1: f_fut and the NG contract counts to 2025-02 (`estimate_fut_share.py --seal a6`,
            `check_ng_contract_counts.py --seal a6`).
          - Step 2: calendar flags, `scripts/build_ledger_calendar.py` → `data/ledger_calendar_flags.csv`
            (1,957 days per root). Window-volume panel, `scripts/build_window_volume_panel.py` →
            `data/ledger_window_volume_daily.csv.gz` + summary; `--check` reproduces byte for byte.
            - Known answer: window volume = the 1-minute fixture's 14:28 and 14:29 bars on all 1,966 front
              days per root, exactly (CL 12,661,012; NG 7,487,344 contracts).
            - The window is a median 3.4% (CL) and 5.9% (NG) of the 09:30–14:30 volume, against 0.67% if
              spread evenly.
            - The panel also has 51 CME holiday sessions per root, with no settlement; H1a joins on the
              calendar, so they drop out. 2020-02-28 is a Databento gap (NYMEX at about 4% of a normal
              day's volume in both bar fixtures; ES complete). It is the same event as the EIA-filled
              settlement hole, so it drops from H1a.
          - Step 3: P1 at 11:30/13:50/14:00/14:10/14:28, `scripts/build_predicted_flow_panel.py` →
            `data/ledger_predicted_flow_{daily,contracts}.csv.gz` + summary. `--check` reproduces byte for
            byte.
            - Holdings are Gate 0b's, imported, not re-derived. The ratio at the settlement equals Gate 0b's
              `index_returns` bit for bit on 3,708 days per root.
            - Q equals `ledger.flows.q1_rebalance` on every single-component row. It uses f_pit[t−1] and
              AUM[t−1], and carries q_lo/q_hi at f_lo/f_hi.
            - The sign audit raises.
            - Median |Q| was 2–3% of the traded contract's window volume in 2017–19, then 14–74% from 2020,
              and about 100% for NG in 2023. That is AUM growth, which the within-year shuffle controls.
            - **CL era B has no single traded contract:** the three Balanced WTI components each carry
              about ⅓ (the largest has a median of 34.4%).
          - **DECIDED 2026-09-25 (principal):** (1) H1a's dependent is the window volume SUMMED over the held
            contracts, for every root and era, with the largest-share contract reported beside it. (2) τ's
            §7.2 gate uses FULL-SIZE CL and NG on the repo's default cost line: CL $21.46 (D508 effective), NG
            $16.00 (the one-tick convention). The micro-size τ is reported beside it.
          - **Correction:** A4's primary f reading is f_est, not f_pit. The panel now stores Q at f = 1 per fund
            plus f_est, f_pit, f_lo, f_hi and σ_q (h = 0.162; DISFAVOURED quarters at h), so the runner forms any
            reading, or A4's draws, exactly.
          - **The §7.2 gate and τ\*, BUILT:**
            - V_d uses the new `vol_ses` (whole-session screen volume, added to the window panel; the old columns
              are unchanged). Screen volume is 64–76% of cleared on the front month and 19–39% on the held months:
              spread legs, TAS and blocks make up the rest.
            - Evaluable on 1,936 days per root. It signals on CL 798 and NG 1,028 days, mostly first at 13:50.
            - **The binding criterion is |I| ≥ 3 × cost, and it tracks AUM:** CL passes 7–12% of days in
              2017–19 and 91% in 2022; NG 8–13% in 2017–19 and 89–98% from 2022. SNR ≥ 1.5 passes 73–79%.
            - **Note for the pre-registration:** D5 treats BOIL's and KOLD's (and UCO's and SCO's) errors as
              independent. They are perfectly correlated through r, so SNR is inflated by a factor from 1 to √2
              (measured: the maximum departure is exactly √2 − 1).
        - **POWER, BUILT 2026-09-25** (`scripts/ledger_power_h1a.py` → `docs/internal/SETTLEMENT_FLOW_LEDGER_POWER.md` +
          `data/ledger_power_h1a.json`; `--check` reproduces).
          - Noise comes from the PRE-SAMPLE (the principal): front-month window volume 2015-06-29 → 2017-05-19, 465 days
            (the 1-minute fixture's day session is absent 2011–14). No in-sample vol_win is read, and a guard raises
            if it is.
          - n = 1,819 (CL, A1 transition excluded) and 1,936 (NG). At the plausible β = 0.25 (a quarter of predicted
            P1 lands in the window), power is CL 0.92 HC1 / 0.85 Newey-West and NG 1.00. NG detects β = 0.1 at 98%.
            Recovery within ±0.15: CL 94%, NG 100%. CL is an upper bound: A4's imputation is not simulated.
          - **FINDING: A8's day shuffle is anti-conservative.** The null's p95 of t is 1.90–2.04. The within-year shuffle
            gives 0.94–1.43, because permuting days destroys the autocorrelation of |Q| (AUM) and of the noise
            (AC(1) 0.2). 13–19% of null datasets beat it. HC1's size is 4.4–5.5% against a nominal 2.3%; Newey-West's
            is 1.4–2.8%. So t ≥ 2 binds, and the shuffle adds nothing.
          - **RESOLVED by A9 (the principal, 2026-09-25):** residualise |Q| on the controls, then rotate it within
            instrument-year (offsets ≥ 20 days). Calibrated: 4–7% of null datasets beat their own p95, and the
            combined gate rejects 0–2%. Power at β = 0.25 (kept): CL 0.87, NG 1.00. A9 also records the summed
            dependent, the full-size cost line and the Newey-West report.
        - **D627: pre-registration `505d83b`, runner `46e317d`, RESULT `17c6867` → FAIL on BOTH roots, with NEGATIVE slopes** (CL β −0.74, t −4.12; NG β −0.10, t −3.07). **The premise is KILLED under A8's kill row.** POST HOC: the dependent drifts (A_t > 0 on 74–77% of days), and NG's TAS volume rises with |Q| (t 3.9 with year FE).
        - **OPTION D (the principal, 2026-09-25): diagnose first, then decide.** `scripts/explore_h1a_lifecycle.py` is EXPLORATORY: it compares each contract with the previous 6 months' contracts at the same days-to-expiry, then refits the window and TAS lines. **The vault rule, committed before the run:** a line qualifies if β > 0 and its vault power ≥ 0.80 at HALF its exploratory effect (it needs t ≈ 12.7 with year FE, over 390 vault days). If no line qualifies → STOP → write-up, and the vault stays unread.
        - **D628 (2026-09-25): NO LINE QUALIFIES → the settlement flow ledger STOPS, and the vault stays unread.** The life-cycle correction leaves CL's window slope negative (t −3.97, and the placebo too) and NG's window flat. NG's TAS line is the strongest (t 6.9 with year FE) but only ties the rotation p95 (6.93), and its vault power at half effect is 0.34. The lead carried forward: NG TAS volume against predicted rebalance, testable only on forward-recorded data. **Next:** the programme write-up.
        - **SIGNED FLOW, A POSSIBLE REOPEN (2026-09-26): Sierra Chart's historical tick data carries the exchange's aggressor side.** The principal installed Sierra Chart (trial to 2026-10-17; Package 3 costs $26/month after). It is driven from here by `scripts/sierra_ui.py` (Win32 window messages; refuses anything trade-related) and its UDP port 22903 (opens charts). Its DTC API excludes CME.
          - **Known answer on the sibling year** (`scripts/check_sierra_aggressor.py` → `data/sierra_aggressor_check_{ho,rb}.json`): window total volume equals Databento's exactly. Net flow r = 0.877 (HO, 686 sessions) and 0.875 (RB, 694); sign agreement 80%. B/A match the exchange flag exactly; the error is the ~29% of window volume with NO aggressor (spread legs), which Sierra Chart signs by its own rule and marks with no field (tested). **Both siblings clear the principal's r ≥ 0.8 bar (2026-09-24).** It fails the stricter "is it the exchange flag" test (r ≥ 0.99).
          - **Still to check:** CL/NG against true trades, only AFTER D626's one read on 2026-10-10 (the post-vault CL/NG trades are its sample).
          - **Next:** bulk-download the CL/NG contracts held 2017–2025 (1-tick, download depth set to 500 days), then a signed-H1 pre-registration that states the measured error and discloses D627/D628's reads.
        - Signed flow estimated from one-second bars, carried with a measured band.
        - C2 on Alpha Vantage trade bars, full in-sample; this replaces A7's Arca clause.
        - Stage H forward-only.
      - The quote superseded by this is kept below for the record.
- [ ] **6 (superseded quote). Databento purchases** (principal to approve; quoted 2026-09-24):
      - CL/NG trades 2016–2023: **$1,029.90**, plus **$147.29** to 2025-03, which now applies since
        the vault's seal was chosen (A6); the order-book quote below also ends at 2023 and needs
        re-quoting to 2025-02;
      - TAS trades: **$3.17**;
      - CL/NG order book 2017-05 → 2023: **$6,126.34** (3.65 TB).
      CL/NG options open interest is already on disk from the free pull of 2026-09-22.
- [ ] **7. The non-US products for Stage G** (Claude; deposit Q14–Q16): BetaPro and WisdomTree NAV,
      units, leverage history and restrike terms, plus FX from free central-bank series.
- [ ] **8. Swap dissemination history** (Claude; deposit Q21, §8A.3, H15): DTCC public data;
      coverage not yet verified.
- [ ] **9. The remaining fund facts** (Claude; deposit Q4, Q9–Q11, Q19, Q20).
      - 10 of the 40 facts are unknown (D619). This includes the **time of day of each fund's
        trade**: settlement, TAS or earlier. That decides whether the flow lands in the 14:28–14:30
        window.
      - Item 1 proved the roll DAYS, not the clock time.
      - The T-bill yield for iNAV comes from FRED.
- [ ] **10. The principal's other decisions:**
      - Q7, the NG execution contract;
      - Q5, the prop constraints;
      - Q18, the Track 3 mode;
      - Q17, the recorder host;
      - the attention design: accept D621's amendment as a document edit, or run the full hourly
        backfills (about 2.5 TB of Wikipedia dumps and 1.64 TB of GDELT, free, weeks to download);
      - Q13, the query list, and Q12, social data. **Q12 stays OPEN: the principal is sourcing
        social data (2026-09-24). Do not close or disable it;**
      - Q2 and decision D4, TAS usage, on which the filings are silent;
      - Q24, the COT report choice;
      - the budget.
- [ ] **11. Build** (Claude, once the data has landed):
      - calendar flags for EIA report days and index roll days. Roll days are known:
        - NG: BCOM closes of BD5–9;
        - CL: BD2–3 from 2020-09-17, BCOM's rule before that;
        - UNG: D0..D0+3;
        - USO: D0..D0+3, then BD1–10 from May 2020.
      - the business-day calendar drops holiday republications and fills the 2020 holes from
        `data/ledger_settle_holes_2020.csv`;
      - the §9B validation toolkit, with unit tests 54–58, which D588 declined, and 61;
      - panels for held months, prices and settlements, signed window flow, TAS, depth, the ETF
        premium, creations, the non-US products, swap timing and attention;
      - Stage A–I runners, reading through `load_panel`, with REQUIRED_OUTPUTS and the canonical
        Sortino, and A4's multiple imputation and A5's var_Q1 term wherever f_fut is estimated;
      - the documents that come before any runner: POWER.md with parameter recovery, TRACK_MAP.md
        with every stage on Track 1, the PROGRAMME_REGISTRY entry, and the pre-registration record
        committed before its runner;
      - Gate 0 and Gate 0b, fully passed.
- [ ] **12. Phase 0:** the recorder runs for five clean days on the chosen host. This waits on item 10.
