# D734 PRE-REGISTRATION — the assembled book NQ F2 + the NQ compression break, one MNQ each, scored once in the joint vault run after both components' own runs; the gates for its admission to the prop book

*2026-10-01.*
- *The principal: "write the arm's retirement and pre-register the F2 + compression book for the joint run", after
  [D732](D732-STAGE-0-RESULT-go-but-the-book-is-two-years-and-compression.md) and the arm's retirement
  ([BOOK_PROP](../BOOK_PROP.md#the-macd-arm-retired-by-the-principal-2026-10-01--the-prop-book-is-empty-again)).*
- *Numbered D734 after telling the other session (it holds D733).*
- ***Committed alone, before its runner exists.** Nothing here opens the vault.*

## 0. What this is

**The programme's rule** (AITODO, amendment A10): each model is scored in one joint run on its own criteria, "and the
assembled book is scored on the same period". This record declares that book, before the vault opens, so the book
itself gets one honest test on data none of its components has seen.

**The book's components already hold programme slots:**
- NQ F2 is [D716](D716-PRE-REG-nq-f2-for-the-joint-vault.md), slot 7.
- The compression break is [D680](D680-PRE-REG-the-nq-compression-break-for-the-joint-vault.md), slot 9.

**The book adds no significance claim and takes no slot.** Its gates are the components' own vault verdicts (where α
lives) plus economic and venue gates.

**Disclosed selection:**
- The pair was chosen after D732's post hoc table, which showed the book doing better without the MACD arm (Sharpe 1.38
  against 1.22; drawdown \$1,360 against \$4,920).
- The vault is unseen for both components, so the test is clean of that choice. The in-sample figures are upper
  estimates.

## 1. The book

| part | definition | size, cost |
|---|---|---|
| **F** | D716's line **as its frozen vault run resolves it**: book B (NQ F2), or book A (NQ F2 when ES F2 agrees) if D716's step-2 takeover fires | 1 MNQ, \$4.067121 a round trip (D716) |
| **C** | D680's NQ compression C1 as frozen: single-count net (D672-A1), scored through the joint wrapper `scripts/joint_d680_vault.py` | 1 MNQ, D680's cost line |

**How the daily series is built:**
- Each part's daily net is the sum of its trades that session, and 0 without one, on NQ's day-session calendar.
- **The book's daily net is F + C.** No weights are chosen, and the sizes are whole micros.

**The window: the vault, 2025-03-01 → 2026-09-18.**
- F's own unseen window starts 2024-01-01, but 2024-01 → 2025-02 is in-sample for C.
- So the book is scored only on the span neither part has seen.

**The account:**
- a \$50,000 account at the intersection of `topstep_50k` and `mffu_rapid_50k`, the 50k venues that permit automation
  when funded (R11 P6; hurdle P is scored at the intersection, per R11's amendment of 2026-09-13);
- the in-sample book's maximum drawdown (\$1,360, D732 post hoc) sits inside the \$2,000 trailing barrier.

## 2. The gates (all must hold for the book to be ADMITTED)

| gate | standard |
|---|---|
| **G1** | **both components PASS their own frozen vault criteria.** F: D716's family verdict (step 1 PASS, whichever line step 2 leaves). C: D680's PASS (≥ 30 C1 trades, gross one-sided HAC t ≥ 1.2816, net > 0) |
| **G2** | **the book's vault net is > 0** |
| **G3** | **the principal's standard** (a strategy earns while it trades): the book's net is > 0 in **each half** of the vault's sessions, split by session count |
| **G4** | **hurdle P** at the declared account, through `backtest_framework.validation.hurdle_p` at R11's operative readings: P2 (no position across either venue's flatten time, from each trade's exit time), P3 (`p3`: ≤ 1.0 breach of 2 % a year **and** ≤ 33 % of the account's life lost) and P4 (`expected_profit_before_breach_usd`: the expected profit before a breach exceeds the account's cost) must pass; P1 (`p1_size`) and P5 (the 30 % single-day convention) are reported; P6 is the venues' fact |

**The outcomes:**

| outcome | when | consequence |
|---|---|---|
| **ADMITTED** | G1–G4 all hold | the book enters BOOK_PROP at one MNQ each on the \$50k account, by a written entry on the principal's word |
| **NOT ADMITTED** | any gate fails | the failing gates are named; the prop book stays empty |

**If exactly one component passes G1,** its own line is reported as a one-component book (G2–G4 computed beside, not
read). This record does not admit it; that would need a new record on the principal's word.

## 3. Order and seals

1. **The book is scored in the joint run only,** on the principal's word, **after** D716's `--vault` and D680's
   joint-wrapper `--run-vault` have each run once.
2. **The book's runner opens no data those runs did not open.** It rebuilds each part's vault trades through the parts'
   own frozen functions (D716's `build`/`masks`; D680's frozen `book()` under the wrapper's held cut). Before scoring
   the book it asserts that the rebuild reproduces **each component's recorded vault result exactly**: D716's
   `parts.vault` score of the line that survives, and D680's vault C1 count and net.
3. **It refuses a second opening:** it is run-once on its output file.
4. **It is frozen with `scripts/freeze.py`** (runner, this record and every imported module hashed) before the joint
   run, with an in-sample rehearsal: on 2018-05-14 → 2023-12-29 it must reproduce D732's F and C daily totals exactly
   (F \$5,628.31; C as D732's runner computes it).

## 4. Power and predictions (stated before the runner exists)

**Power.** G1 needs two independent passes (in-sample ρ 0.02). From the components' recorded powers:

| share of the in-sample edge | D716 PASS | D680 PASS | G1 (both) |
|---:|---:|---:|---:|
| 100 % | 0.69 | 0.66 | **about 0.46** |
| 50 % | 0.61 | 0.30 | **about 0.18** |

G2 and G3 cut that further. **This test is more likely to say NOT ADMITTED than ADMITTED, even if both edges are
partly real,** and a NOT ADMITTED is weak evidence against the book.

**Predictions:**

| # | prediction |
|---|---|
| 1 | G1 fails: at least one component fails its own vault criterion |
| 2 | if G1 holds, G2 holds |
| 3 | the book's vault Sharpe is below its in-sample 1.38 |
| 4 | the reading is **NOT ADMITTED** |
