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

**Taken one at a time, in this order.** `[>]` means in progress. Each item names who owns it.

- **1. Daily holdings history. CLOSED 2026-09-24.** The record is in PICKUP.md, "SETTLEMENT LEDGER,
  ITEM 1", and the amendments A1–A5 are signed off.
  - What is left of it is 1f, which is placed after item 2 at the principal's word ("come back to
    1f after we deal with the next full item"), and the execution time of day, which is item 9.
- [ ] **2. The seal date** (principal). Choose between the repository's 2024-01-01 holdout and the
      deposit's vault, 2025-03-01 → 2026-09-18. Also record every earlier read this repository made of
      NG and CL in the vault window (deposit Q25): D562, D566, D574, D578, D604, and the tbbo
      censuses.
- [ ] **1f. Gate 0b from 2024 onward** (Claude, straight after item 2).
      - **If the vault's seal is chosen,** rerun `gate_0b_ng_nav.py` and `gate_0b_cl_nav.py` over
        2024-01 → the seal, under the same frozen rules.
      - **Needs first:**
        - swap-free proof for BOIL, KOLD and SCO is already in hand through 2025-Q4;
        - UCO's f_fut band past 2023;
        - the 2023-12-31 holdings, which were filed in 2024 and so are read only once the seal
          moves.
      - **If the 2024-01-01 seal stands,** 1f is moot and is removed.
- [ ] **3. The sample start** (principal; deposit Q6). No earlier than 2017-05-21, set by the
      order-book history. No earlier than 2018-05-01 unless TAQ is bought.
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
- [ ] **6. Databento purchases** (principal to approve; quoted 2026-09-24):
      - CL/NG trades 2016–2023: **$1,029.90**, plus $147.29 to 2025-03 if the vault's seal is chosen;
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
      - Q13, the query list, and Q12, social data;
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
