# D792 PRE-REGISTRATION — the assembled prop book: the five live components, one micro each, built from whichever members pass their own frozen vault lines, scored once in the joint run and again on a year of forward trades

*2026-10-03.*
- *The principal: "Pre-reg the assembled book".*
- *The design is the principal's, from four choices:*
  - *members: "The five live components";*
  - *admission: "Passes only (D734 style)";*
  - *window: "2024-01-01 → 2026-09-18";*
  - *forward: "Yes, at 12 months".*
- *Numbered D792: the China-open session holds D791 and was told.*
- ***Committed alone, before its runner exists.** Nothing here reads a price dated 2024-01-01 or later.*

## 0. What this is

**The rule it serves.** CLAUDE.md: "Choosing components after seeing their Sharpes is selection. The assembled book is
confirmed only on a slice no component has seen." The programme (AITODO A10) scores each model in one joint run, "and
the assembled book is scored on the same period".
- [D734](D734-PRE-REG-the-nq-f2-and-compression-book-for-the-joint-vault.md) declared the NQ pair (F2 + C1).
- Three components entered the ledger after it (#6, #7, #8). No declared rule says how they combine.
- **This record fixes the whole book before any member's vault is read.** After the joint run, any assembly would be
  chosen on the results.

**It takes no programme slot and adds no significance claim.** α lives in the members' own lines (slots 1, 2, 7, 9
and 10). The book's gates are economic and the venue's.

## 1. The members

The components ledger's live prop components (`COMPONENTS_PROP.md`, 2026-10-03), each exactly as its own frozen record
defines and scores it:

| member | frozen line | slot | instrument, cost | clock |
|---|---|---|---|---|
| **F** | NQ F2 ([D716](D716-PRE-REG-nq-f2-for-the-joint-vault.md)): book B, or book A if D716's step-2 takeover fires; ledger #5 | 7 | 1 MNQ, \$4.067121 | 15:00 → 16:00 |
| **D** | NQ leads the Dow ([D737](D737-PRE-REG-nq-leads-the-dow-for-the-joint-vault.md)); ledger #6 | 1 | 1 MNQ, \$4.07 | first trigger 10:00–14:30 → 15:59 or stop |
| **R** | the CPI/jobs-report fade ([D776](D776-PRE-REG-the-cpi-and-jobs-report-fade-for-the-joint-vault.md)); ledger #7 | 2 | 1 MNQ, \$4.07 | 08:34 → 11:00, release days |
| **C** | the NQ compression break C1 ([D680](D680-PRE-REG-the-nq-compression-break-for-the-joint-vault.md)); a component line | 9 | 1 MNQ, D680's cost line | the morning break |
| **L** | base L4, the M2K closing-auction fade ([D781](D781-PRE-REG-the-m2k-closing-auction-fade-for-the-joint-vault.md)); ledger #8 | 10 | 1 M2K, \$3.76 | 18:05 reopen → 10:00 |

**Left out, and why:**
- the NG projected-profit line (D649, slot 8): it was never entered in the components ledger, and it has no forward
  ledger;
- slots 3–6 (the deposit's settlement-ledger and index-reweight families): multi-day or full-size holds, not prop
  components.

**Every member is flat at the venues' 16:10 ET flatten.** L opens at 18:05, after the flatten, and closes at 10:00, before
the next one.

**The in-sample correlations are already on file** (all |ρ| ≤ 0.06, `COMPONENTS_PROP.md` #6–#8, D732). They chose
nothing here.

## 2. The book

**Membership is set by the members' own vault verdicts (passes only).**
- **The book is the set of members whose own frozen vault line reads PASS.** A member reading FAIL or UNRESOLVED is out.
- F's verdict is D716's family verdict (step 1 PASS, whichever line step 2 leaves). The others are their records' own
  PASS.
- **Disclosed:** the members are selected on the same vault data the book is then scored on. The book's vault figures
  are therefore biased upward. That is why §5's forward read exists.

**Sizes:** one micro per member, whole contracts, no weights.

**The daily series:**
- Each member's daily net is the sum of its trades' nets on that day, and 0 on days without a trade.
- **Each trade is booked on the venue trading day of its exit.** L's trade, entered at 18:05 on session S's evening
  and closed at 10:00, belongs to session S+1.
- **The calendar is the union of the passing members' own session frames** inside the window: D716's NQ frame,
  D737's sessions, D776's sessions, D680's `book()` sessions and D778's M2K frame.
- **The book's daily net is the sum of the members' daily nets.**
  - Positions in the same instrument at the same time net out on one account.
  - The P&L is linear, so the sum is unchanged.
  - The runner reports the most MNQ held at once.

**The window: 2024-01-01 → 2026-09-18** (the principal's choice).
- F, D, R and L have this whole window unseen.
- **C's in-sample runs to 2025-02-28** (D680), so C contributes nothing before 2025-03-01. A C PASS adds C only from
  2025-03-01; its 2024-01 → 2025-02 days are 0, not read.
- **Reported beside, never gating:** the same book on 2025-03-01 → 2026-09-18, the span every member has unseen.

**The account:**
- a \$50,000 account at the intersection of `topstep_50k` and `mffu_rapid_50k`, the 50k venues that permit automation
  when funded (R11 P6);
- the flatten time is 16:10 ET (`data/prop_venues.json`).

## 3. The gates (all must hold for ADMITTED)

| gate | standard |
|---|---|
| **G1** | **at least two members PASS their own frozen vault lines** |
| **G2** | **the book's vault net is > 0** over the window |
| **G3** | **the principal's standard** (a strategy earns while it trades): the book's net is > 0 in **each half** of the window's sessions, split by session count |
| **G4** | **hurdle P** at the declared account, through `backtest_framework.validation.hurdle_p` at R11's operative readings, as D734 reads it. **P2** (no position across the 16:10 flatten, from each trade's exit time), **P3** (`p3`: ≤ 1.0 breach of 2 % a year **and** ≤ 33 % of the account's life lost, with [D734-A1](D734-PRE-REG-the-nq-f2-and-compression-book-for-the-joint-vault.md)'s censored P3b) and **P4** (`expected_profit_before_breach_usd` exceeds the account's cost) must pass. **P1** (`p1_size`) and **P5** (the 30 % single-day convention) are reported. **P6** is the venues' fact |

**The outcomes:**

| outcome | when | consequence |
|---|---|---|
| **ADMITTED** | G1–G4 all hold | the book is the candidate for BOOK_PROP at one micro per passing member, by a written entry on the principal's word; §5's forward read then confirms or removes it |
| **NOT ADMITTED** | any gate fails | the failing gates are named; the prop book stays as it was |
| **ONE MEMBER** | exactly one PASS | its line is reported as a one-member book (G2–G4 computed beside, not read). This record admits nothing; that would need a new record on the principal's word |

**Reported beside, never gating:**
- the fixed book of all five, whatever the verdicts (the unselected book);
- every member's line on the book's calendar;
- the daily ρ matrix;
- CLAUDE.md's four groups for the book: net and gross Sharpe and Sortino, exposure, vol, max drawdown, the trade
  distribution with the symmetric 1 % trim, P&L by year and by member, and the largest days.

**D734.** D734 is read as frozen, on its own gates, and reported beside.
- When both read ADMITTED, this record's book is the candidate: it contains every member D734 could hold.
- When only one reads ADMITTED, that one's book is the candidate.
- Either way, the entry is on the principal's word.

## 4. Order and seals

1. **The vault read runs in the joint run only,** on the principal's word, **after** all five members' own vault runs
   (and D734's).
2. **The runner opens no data those runs did not open.**
   - It rebuilds each passing member's vault trades through the member's own frozen functions, imported unchanged.
   - **Before scoring, it asserts that each rebuild reproduces that member's recorded vault result exactly:** trade
     count and mean net, to the member's own precision.
   - It reads each verdict from the member's recorded output, not from its own rebuild.
3. **It refuses:**
   - without the principal's word;
   - unless this record, its runner and every hashed import match the freeze;
   - unless every member's own freeze still verifies;
   - unless all five members' vault outputs exist;
   - if its own vault output exists (run once).
4. **It is frozen with `scripts/freeze.py` before the joint run,** after a once-only in-sample rehearsal.
   - **The rehearsal window:** 2018-05-14 → 2023-12-29, the span every member holds in-sample.
   - **The rehearsal first reproduces each member's in-sample known answer exactly:**
     - D737's 1,699 trades at +\$14.869…;
     - D776's 186 trades at +\$34.879032 gross;
     - D781's 280 trades at +\$15.844642… gross;
     - D716 book B's 271 trades at +\$20.768672… net;
     - D680's C1 as its runner computes it.
   - It then scores the five-member book on that window, all members in. This is the gates' machinery proved, not
     evidence.
5. **No member's record, runner or frozen file is edited.** The book imports them.

## 5. The forward read (the confirmation; the principal: "Yes, at 12 months")

**When:** on or after **2027-09-30**, once, on the principal's word.

**What it reads:** each member's forward ledger over **2026-09-21 → 2027-09-30**:
- D737's (inside the recorder);
- D776's (`forward_d776_ledger.py`);
- F2's and C1's (`forward_f2_c1_ledgers.py`);
- L4's (`forward_l4_ledger.py`).

**The book:** the **same members as the vault book**, one micro each, built and booked as in §2 on that window.
Nothing about its membership is re-chosen.

**The gates:** G2, G3 and G4 as in §3, on the forward window.

**The outcomes:**

| vault | forward | consequence |
|---|---|---|
| ADMITTED | G2–G4 hold | **CONFIRMED**: the book stands |
| ADMITTED | any fails | the book is **retired** from BOOK_PROP, on the principal's word; the failing gates are named |
| NOT ADMITTED with ≥ 2 PASS | either | reported as evidence for a later record; this record admits nothing |
| fewer than 2 PASS | — | not scored as a book; the members' forward lines are reported |

**Reported beside:** the fixed five-member book on the forward window.

**The ledgers' seals stand.** L4's, F2's and C1's ledgers run only after the joint run, as their records require.

## 6. Power and predictions (stated before the runner exists)

**G1's power.** It is computed from the members' recorded pass rates, assuming the members are independent (in-sample
|ρ| ≤ 0.06):

| edge kept in the vault | D737 | D776 | D716 | D680 | D781 | **G1 (≥ 2 PASS)** | expected passes |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 % | 0.63 | 0.57 | 0.69 | 0.66 | 0.52 | **0.93** | 3.1 |
| 50 % | 0.16 | 0.24 | 0.61 | 0.30 | 0.20 | **0.48** | 1.5 |
| 0 % | 0.01 | 0.07 | 0.13 | ≤ 0.18 | 0.04 | **≤ 0.06** | 0.3 |

- **Sources:** `data/vault_d737_power.json` (in-sample σ), `vault_d776_power.json` (G1),
  `vault_d716_power.json` (primary pass), `vault_d680_power.json`, `vault_d781_power.json` (G0/G1).
- **D680's file has no zero-edge row,** so its 25 % row (0.18) stands in as an upper bound.
- D776's and D781's rates are G1 only; their rotation gate cuts them further.

**What follows:**
- G1 is likely to hold if the edges are mostly real.
- Under no edge, G1 is unlikely to hold (≤ 6 %).
- G2 and G3 then decide. They are read on a book already selected on its members' passes, so they will rarely fail
  after G1 holds. **G4 and the forward read are the binding tests.**

**Predictions:**

| # | prediction |
|---|---|
| 1 | G1 holds with 2 or 3 PASS members, not 5 |
| 2 | if G1 holds, G2 and G3 hold (selection makes them easy) |
| 3 | the book's vault net Sharpe is below the in-sample book's (the rehearsal's) |
| 4 | the fixed five-member book's vault net is below the passes-only book's |
| 5 | the reading is ADMITTED, at about even odds (G1 is 0.48 at half the in-sample edge, before G4) |
| 6 | the forward read's net Sharpe is below the vault book's |
