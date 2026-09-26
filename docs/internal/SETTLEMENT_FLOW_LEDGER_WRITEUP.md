# Settlement flow ledger: write-up (STOPPED 2026-09-25)

> **REOPENED 2026-09-26** by the first route in §7 below: aggressor-signed window trades for the in-sample, from
> Sierra Chart. D629 passed NG's H1 on signed flow (provisional) and D630 passed H2 on NG. Gate 1 is met on NG. NG's
> Stage A is frozen and waits for the joint vault run (amendment A10). This write-up stands as the record of the stop.

> The deposit (`User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md`, v1.9) prescribes "STOP → write-up" when Gate 1
> fails. This is that write-up. The deposit and `SETTLEMENT_FLOW_LEDGER_AMENDMENTS.md` (A1–A9) are the
> specification. The records cited here are the evidence. Nothing below is a new result: every number is quoted
> from a committed record.

## 1. The verdict

**The programme stops at Stage A. The pre-registered kill test failed on both instruments, and no follow-up line was
strong enough to spend the vault on.**

- **H1a** (D627): does the leveraged funds' predicted rebalance *size* show up as extra settlement-window volume? It
  FAILED on both roots, with **negative** slopes: CL β −0.74 (t −4.12) and NG β −0.10 (t −3.07). Under A8's kill
  row, that kills the premise.
- **The diagnosis** (D628, exploratory, with its rule committed first) corrected a flaw in D627's dependent:
  - CL's slope stayed negative, and its midday placebo carried the same slope;
  - NG's window line went flat;
  - no line reached the vault bar (80% power at half the exploratory effect).
- **The vault (2025-03-01 → 2026-09-18) was never read.**

## 2. What the ledger claimed

Leveraged commodity ETFs (BOIL/KOLD on NG, UCO/SCO on CL) must rebalance by AUM × L(L−1) × r each day, in the
futures their index holds, and they execute at the settlement. The ledger's premise:
- that flow is **predictable** from public data by mid-afternoon;
- it is **large** enough to arrive as visible volume in the 14:28–14:30 ET settlement window;
- it **moves the price** into the settlement, which H2 would test.

The staged design (Stages A–I) adds participants one at a time. Stage A is P1 alone, and its kill test decides
whether the rest is worth building.

## 3. What was built and what was tested

| step | record / commit | outcome |
|---|---|---|
| Item 1: fund holdings, held months, rolls | `9147920` | Held months proven. Gate 0b (iNAV within 5 bp of the official NAV on ≥ 95% of days) PASSES for BOIL 0.991 and KOLD 0.987. For UCO and SCO the pre-registered verdict FAILS (0.888 and 0.884), because of the 2020 benchmark transition. Its investigation passes at 0.997 and 0.995, using Bloomberg's documented Balanced WTI rule and excluding the transition (A1 excludes it). UCO's and SCO's futures share is estimated with measured bands (h = 0.162, A6) |
| Items 2–3: the seal and the sample | `892709b` (A6, A7) | The in-sample runs 2017-05-22 → 2025-02-28. The vault is 2025-03-01 → 2026-09-18, for one look |
| The data route | AITODO item 5 | The principal cannot buy more data (2026-09-24). Everything below uses free Databento (CME Standard) pulls, Alpha Vantage and IEX |
| D624: can one-second bars estimate signed window flow? | `6e1bfa4` → `589a7f9` | **No.** The sibling check (HO/RB, true trades) gave r −0.03 and −0.22 against a bar of 0.8. Stage A cannot run on estimated signed flow |
| D625: does the TAS price say which way the window flow went? | `158b2d2` → `305794c` | **No, as pre-registered:** the control fired on a base-rate effect. POST HOC: the TAS premium reads *backwards* (κ +0.33 to +0.49 reversed) |
| D626: the reversed TAS sign, on unread data | `9ee8142`, runner `fabb3fb` | **Pending:** read once by the scheduled task on 2026-10-10. Independent of the stop |
| A8: Stage A moves to H1a (size, not sign) | `305794c` | H1a against exact free window volume. Direction was left to H2 |
| Stage A's inputs, POWER, A9 | `4f34183` | Calendar, window-volume panel, P1 panel, the §7.2 gate, power, and A9's calibrated rotation control |
| D627: H1a | `505d83b` → `46e317d` → `17c6867` | **FAIL on both roots, negative slopes. Premise killed** |
| IEX: the ETF-premium bias | `c2aeb73` | Alpha Vantage closes sit within about 1 bp of the mid on average (C2 would have been viable) |
| D628: option D's diagnosis | `ee4d59e` → `7e099ad` | No line qualifies for the vault. **STOP** |

## 4. What held up: facts and machinery worth keeping

- **Fund mechanics are reproducible from public data.**
  - The index-holding rules replicate BOIL's and KOLD's official NAV to within 5 bp on 98.7–99.1% of days. They
    replicate UCO's and SCO's on 99.5–99.7% of days, once the 2020 transition is excluded.
  - The roll calendars of all four index funds, and UNG's and USO's own roll rules, are proven.
- **Window volume is exact from free data.** Databento's one-second bars match the 1-minute fixture's 14:28 and
  14:29 bars contract for contract, on every front day, for both roots.
- **The window really is special:**
  - its 2 minutes carry a median 3.4% (CL) and 5.9% (NG) of the day session's volume, against 0.67% if spread evenly;
  - the predicted P1 is large in the high-AUM years. From 2020 its median is 12–103% of the window volume in the
    largest-share contract: CL 14–74%, NG 12–103%.
- **The ETF-premium input is sound.**
  - Alpha Vantage 1-minute bars are stamped at the minute's start.
  - The close-vs-mid bias is below 1.3 bp for every ETF, measured where IEX's quote is the national best.
- **A9's control is calibrated:** 4–7% size against a nominal 5%. The power harness, with pre-sample noise and block
  bootstrap, is reusable as it stands.

## 5. What failed, and why

1. **Signed flow is not free, and cannot be estimated** (D624, D625). The deposit's H1 needs aggressor-signed window
   flow. The estimates from one-second bars carried no sign information on the siblings, and the TAS price's
   pre-registered sign was wrong. That forced A8's retreat to a size-only test, which cannot tell buying from
   selling.
2. **The size link is absent or reversed** (D627, D628).
   - **On CL**, larger predicted rebalances go with *less* abnormal volume, at 14:28 *and* at midday. It survives
     year fixed effects and the life-cycle correction. It is a whole-day association, not settlement-window flow.
   - **On NG**, once the life-cycle drift is removed, the window shows no footprint at all.
3. **Two design errors of our own.** Both are now memory rules.
   - **The day shuffle A8 specified was anti-conservative.** Permuting days of an AUM-driven (autocorrelated)
     predictor destroyed the structure that widens the true null. It was caught by the power study before the
     pre-registration and replaced by A9's rotation.
   - **D627's "abnormal volume" was not mean-zero.** It compared each held contract with its own trailing mean, and a
     contract moving toward the front grows all the while it is held, so the dependent was positive on 74–77% of
     days. It was caught only after the run. D628 corrected it, and the conclusion did not change.

## 6. The lead worth carrying

**NG's TAS volume rises with the leveraged funds' predicted rebalance.** With year fixed effects, β +1.28, t 6.9,
Newey-West 5.45 (D628). NG's placebo is flat. This fits A8's own caveat that the funds may execute at the settlement
price through TAS rather than in the window.

It is POST HOC, and it is weaker than its t looks:
- it only ties the rotation null's p95 (6.93);
- its power on the vault at half effect would be 0.34.

CL's TAS goes the other way (t −3.7).

**Testing it needs data no one has read and that is recorded going forward.** That is the deposit's Phase 0
recorder: daily TAS volume per contract month, fund AUM, and the as-of prices at 13:50–14:10. It does not need
the vault.

## 7. What would reopen the programme

Any one of these would justify a new pre-registration. None is in hand:
- **Aggressor-signed window trades for the in-sample** (AITODO G1). The principal can source it. It would let the
  deposit's own H1 run as written, with the sign.
- **A forward TAS record** long enough for the NG lead to reach about 80% power.
  - At the full in-sample effect (t 6.9 on 1,871 days), 390 sessions give an expected t of about 3.2.
  - At half that effect, the expected t is about 1.6. Reaching 2.84 needs about 3.2× as many sessions: roughly 1,250,
    or five years of recording.
- **The fund execution clock** (deposit Q2, D4): a filing or issuer statement that the funds trade TAS, or trade in
  the window. The fund facts show this as unknown for all four funds.

## 8. The state of the data and the vault

- **The vault is unread.** Its one-second bars sit on disk in the main free pull's 2025 and 2026 year files. They
  have never been decoded for this study, and they remain available for a future pre-registered look.
- **The Databento CME Standard subscription lapses around 2026-10-11.**
  - The free post-vault top-up is scheduled for 2026-10-10, together with D626's single read.
  - After the lapse, no new CME one-second or trade data is free.
- **The raw caches** (`data/raw/databento/`, `data/raw/alphavantage/1min/`, `data/raw/iex/`) are gitignored and
  costly to rebuild. Keep them.

## 9. Inventory: reusable pieces

| piece | file | note |
|---|---|---|
| Business-day calendar and flags, CL/NG | `scripts/build_ledger_calendar.py` → `data/ledger_calendar_flags.csv` | index and fund rolls, expiry, EIA, the 2020 transition |
| Window, pre-window, placebo, whole-session and TAS volume; as-of prices | `scripts/build_window_volume_panel.py` | exact against the 1-minute fixture |
| P1 at five evaluation times; the §7.2 gate; τ\* | `scripts/build_predicted_flow_panel.py` | on Gate 0b's holdings, bit-identical to its index |
| Futures share, A6 | `scripts/estimate_fut_share.py --seal a6` | f_est, f_pit and bands; σ_q per A4 |
| Power harness and the calibrated rotation null | `scripts/ledger_power_h1a.py`, `scripts/run_h1a_stage_a.py` | pre-sample noise, block bootstrap, Rubin's rules |
| Life-cycle-matched volume norm | `scripts/explore_h1a_lifecycle.py` | the same distance to expiry across delivery months |
| ETF quote sample and the premium-bias check | `scripts/fetch_iex_tops_sample.py`, `scripts/check_etf_premium_bias.py` | 10 days of IEX TOPS, filtered to the six ETFs |
| Gate 0b NAV replication | `scripts/gate_0b_ng_nav.py`, `scripts/gate_0b_cl_nav.py` | BCOM §2.8 and Balanced WTI |

## 10. Lessons (also in memory)

1. Before a pre-registration fixes a control, measure the control's own false-pass rate in the power simulation.
2. Before a pre-registration fixes an "abnormal" dependent, compute its mean on pre-sample data built exactly as the
   runner builds it.
3. Commit the decision rule before the exploration that feeds it. D628's rule was committed in `ee4d59e` before
   `explore_h1a_lifecycle.py` produced a number, so the STOP was not chosen after seeing the data.
