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
| G1 | aggressor side of CL/NG trades, 2017-05 → 2025-09-24 | **A (the kill test)**, B, I, H5 | WEAKENED | estimated from one-second bars; validated after the vault. **Principal: if Stage A can't be tested on the estimate, they will source the data** |
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
| G14 | swap dissemination history (DTCC) | E netting, H15 | UNVERIFIED | item 8 |
| G15 | non-US products (BetaPro, WisdomTree): NAV, units, leverage, restrikes | G | UNVERIFIED | item 7. Likely free on the issuers' sites |
| G16 | official intraday NAV (IIV) history | validation only | MISSING | not needed: the rebuilt iNAV passes Gate 0b |
| G17 | vault trades with aggressor side, 2025-03-01 → 2025-09-24 | the vault look | WEAKENED | the same one-second estimate, which keeps the method consistent |
| G18 | CL 2020-04-01 → 09-16 | all CL stages | EXCLUDED | A1 |
| G19 | USO roll days 2017 → 2020-04 | F | WEAKENED | rest on the documented rule; USO's monthly NAV could check them for free (not run) |
| G20 | the item-1 estimates run only to 2023-12 | A–F | TO EXTEND | free work (item 11) |
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
      - **HELD by the principal ("not yet"):** amendment A8.
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
