# D716 PRE-REGISTRATION — NQ F2 for the joint vault run, with a fixed-sequence takeover by "NQ F2 only when ES F2 agrees"; ES F2 (D707) withdrawn before any look

*2026-09-30.*
- *The principal:*
  - *"I would like to register F2 on NQ only and with a secondary of when NQ and ES agree, for the vault run";*
  - *"Remove ES F2 from the vault run and keep NQ F2 and NQ F2 only when ES F2 agrees. I would like it to be calculated
    with programme α. But it will take over NQ F2 if and only if, the t for the secondary for the whole tested range >
    2.5-3";*
  - *then, on the recommended form (§4): "Ok I agree with your recommendations, write it up please."*
- *Numbered D716: D715 is the other session's, and it was told before writing.*
- ***Committed alone, before its runner exists.** Nothing here reads a price dated 2024-01-01 or later on any root.*

## 0. What changes in the joint vault run

| | before | after this record |
|---|---|---|
| ES F2 (D707, frozen, slot 7) | one look at 2024-01-01 → 2026-09-18 | **WITHDRAWN before any look.** Slot 7 is released with a recorded reason; D707's `--vault` mode must never be run |
| NQ F2 | not registered | **registered in slot 7** (the lowest free), with the agreement book as a fixed-sequence takeover |
| slot 10 | free | free |

**What the withdrawal costs, stated now:**
- **The agreement book needs ES F2's daily decision as an input.** So this family's vault run reads ES's 2024+ last-hour
  prices.
- **After that, ES F2 has no unread sample left.** It can never have a clean vault look of its own.
- **D707's record, runner and freeze stay as committed,** and their hashes still verify. They are superseded by this
  record, not edited.

**The selection, disclosed:**
- NQ was one of three roots named in advance by D711's pre-registered transfer test (A2), with the rule unchanged.
- **But the principal chose NQ over ES after seeing both books in-sample.** NQ's in-sample +$20.67 a trade is
  therefore an upper estimate. The rule itself came from ES's in-sample search (D702 → D705).
- **The agreement book was found by looking** (D711 addendum 1), and it failed its in-sample test: D714, NO INCREMENT,
  efficiency rank 0.856; drawdown rank 0.64.

## 1. The construction: NQ F2, in its entirety

**It is D707 §1 with the contract changed:**

| item | definition |
|---|---|
| instrument | **NQ**, traded as **one MNQ** ($2 a point) |
| data | `data/fixtures/fut_NQ_rth_1m.csv.gz`: one-minute RTH bars. Sessions have at least 380 bars; each session's modal contract; a session whose contract differs from the previous session's (a roll session) is never traded |
| price at hh:mm | the close of the bar that starts one minute earlier; P09:30 is the open of the 09:30 bar |
| signal | F5 = 10⁴ · ln(P15:30 / P14:30); d = sign(F5); F5 = 0 is not a candidate |
| trade | at 15:30 in direction d, exit at 16:00 (the close of the 15:59 bar); no stop, flat every day |
| a | \|F5\| / σ_F5, with σ over the previous 252 sessions of the frame (at least 60), shifted one session |
| b | ln √(Σ r²) of the 5-minute log returns (bp) from P09:30 to P15:30 |
| rule | tₐ = tiers(a), t_b = tiers(b), t_c = tiers((tₐ + t_b) / 2), each over NQ's candidates in order from the frame's start. **TAKE when t_c ≥ 0.8.** D671's `tiers` is the share of the previous 250 finite values strictly below |
| cost | **$4.07 a round trip** (D668-A2's MNQ single line: $3 plus the measured crossing, `cost_lines("NQ")["cost_single_usd"]`) |
| code | D711's `load_root`, `clock_frame` and `f2_on` at T = 15:30, unchanged |

**The in-sample record** (D711 and its addenda; the NQ window runs 2018-04-20 → 2023-12-29):

| | NQ F2 |
|---|---:|
| trades (a year) | 274 (48) |
| gross / net a trade | +$24.74 / **+$20.67** |
| net HAC t | 2.95 |
| hit, median net, skew | 0.555, +$11.43, +0.57 |
| daily Sharpe (Sortino) | **0.92 (1.56)** |
| max drawdown | $990 |
| net at a two-tailed trim of 10 % | +$18.94 (t 4.00) |
| before / after 2022-05-16 | +$21.92 / +$14.15 |
| 2022's share of the net | 67 % |
| efficiency rotation rank (D711-A1's null) | 0.984 |
| ρ with ES F2 / with the MACD arm | 0.87 / +0.02 |

## 2. The secondary: the agreement book

**A = NQ F2's trades on the sessions where ES F2 takes, with sign(F5_ES) = sign(F5_NQ).**
- ES F2 is D707 §1 exactly: one MES, 15:30, the same tiers over ES's own candidates.
- A session where ES is not a candidate (a roll session, a short session, or F5_ES = 0) is not an agreement day.

**In-sample** (D714, 2018-05-14 → 2023-12-29):

| book | trades | net a MNQ trade | daily Sharpe (Sortino) | max drawdown |
|---|---:|---:|---:|---:|
| A | 216 | +$25.58 | 0.98 (1.71) | $837 |
| B (NQ F2) | 271 | +$20.77 | | |

## 3. The unseen span

**Every candidate from 2024-01-01 through 2026-09-18, on NQ (traded) and ES (the input), read once in the joint run.**

| part | span | status |
|---|---|---|
| the held slice | 2024-01-01 → 2025-02-28 | never read for NQ F2, ES F2 or the agreement book |
| the vault | 2025-03-01 → 2026-09-18 | sealed; read only in the joint run (A10) |

- **The fixtures end 2026-09-09** (NQ: 694 unseen sessions, counted from the dates alone).
- The walk-forward tiers run continuously from the in-sample frames.
- **Expected:** about 130 NQ F2 trades, and about 105 agreement trades.

## 4. The test: a fixed sequence inside one programme family

**Step 1, the primary (NQ F2), at the family's full slot α** (D705 §3's rule, as D707):

| verdict | condition |
|---|---|
| **PASS** | at least 30 trades, mean net > 0 and one-sided HAC t (Newey–West, 5 lags) ≥ 1.2816 |
| **FAIL** | at least 30 trades, otherwise |
| **UNRESOLVED** | fewer than 30 trades |

**Step 2, the takeover. Tested only if step 1 PASSES.** The agreement book A **replaces** NQ F2 as the family's result
**if and only if both** hold:

| # | condition |
|---|---|
| (ii) | A has at least 30 trades, and its **net HAC t ≥ 2.576** over the whole unseen span |
| (iii) | **A beats count-matched random deletion.** 20,000 random \|A\|-subsets of NQ F2's unseen trades, without replacement (seed 716). A's direction efficiency Σnet / Σ\|net\| exceeds the null's p95 by at least 2 bootstrap SEs of that p95, and A's mean net exceeds NQ F2's (D714's INCREMENT rule, repeated on unseen data) |

- Otherwise NQ F2 stands.
- **The family's result is one of:** FAIL / UNRESOLVED (step 1); **NQ F2** (step 1 PASS, no takeover); **THE AGREEMENT
  BOOK** (step 1 PASS and takeover).

**Why this shape:**
- **The fixed sequence keeps the family's false-positive rate at the slot's α** without splitting it. The takeover is
  a choice between two books after one has passed, not a second family.
- **Condition (iii) is what decides a takeover.** A is about 80 % of NQ F2's trades, so (ii) alone would mostly re-ask
  whether NQ F2 did well. (iii) asks whether dropping the non-agreement days helped.

**Programme promotion** is flagged separately at one-sided t ≥ 2.576 (p ≤ 0.005, the slot's α), as D680 and D707
did, on the family's result.
- **A disclosed discrepancy.** The deposit's §13A.8(2) glosses p ≤ 0.005 as "roughly t ≥ 2.8", which is the
  two-sided value (2.807).
- **The runner reports the promotion flag at both 2.576 and 2.807.** Which reading the programme uses is the
  principal's to fix. It does not touch the PASS or the takeover.

**The slot:** 7, released from ES F2 and registered to "last-hour F2 (NQ)" at freeze time. Slot 10 stays free.

## 5. Reported beside, never gating

- **Both books and the dropped set,** each in the four reporting groups at one MNQ, net and gross side by side:
  - Sharpe with Sortino, per trade and daily; max drawdown;
  - hit, median and payoff; skew; the 1 / 5 / 10 % two-tailed trims;
  - by year; long against short.
- **The held slice and the vault separately,** for each book.
- **The takeover's null in full:** p50, p95, its SE, A's rank, and the drawdown rank (D714's addendum).
- **The component line** for the family's result: net daily Sharpe, and ρ with the MACD arm wherever the arm's daily
  P&L exists on the span.
- **ES F2's own unseen book** (reported only, as information): its ES data is read anyway, and after this run it has
  no clean look left.
- **The 2022-style concentration check** (D705's (d)): the largest year's share of net, and the years positive.

## 6. Power (a rough estimate now; the runner computes it before the freeze)

**At NQ F2's in-sample per-trade figures** (sd about $133, per-trade Sharpe about 0.156; the agreement book's about
0.19), on about 130 / 105 unseen trades:

| effect kept | primary PASS | takeover, given the primary passes |
|---:|---:|---|
| 100 % | ≈ 0.69 | ≈ 0.25 on (ii) alone; lower with (iii) |
| 50 % | ≈ 0.35 | |

**The runner's `--power` states:**
1. **The primary test's size:** 20,000 draws of 130 trades resampled from NQ F2's demeaned in-sample net. The bar is at
   most 0.12, and the freeze refuses otherwise.
2. **The primary and takeover rates** on contiguous in-sample windows of 640 candidates (step 5). At 100 / 50 / 25 / 0 %
   of NQ F2's in-sample edge, every NQ trade is shifted by the same dollar amount, so A's increment over B is kept as
   observed.

**The rule is frozen on the principal's word whatever check 2 shows.**

## 7. The ledger

- **Entry #4 (ES F2):** its vault promotion path is withdrawn. It stays as scored, PARKED, with no unread sample left
  after this run.
- **NQ F2 enters as entry #5, PROVISIONAL, on the principal's ruling.** C-a (0.92), C-b (ρ +0.02 with #2, the MACD
  arm), C-c and C-d are met on the point estimates.
- **The joint run promotes or removes it:** the family's result (NQ F2, or the agreement book if it takes over) is
  kept on a PASS and removed on a FAIL.

## 8. Prerequisites for the vault look

1. **The price data is on disk** (both fixtures to 2026-09-09).
2. **The freeze:**
   - the LF-normalised sha256 of this record, the runner and every script it calls;
   - the in-sample known answers;
   - the power figures;
   - slot 7 released from ES F2 and registered to NQ F2.
3. **The principal's word** for the joint run, given on the command line.
4. **D707's vault mode is never run** (AITODO says so).

## 9. The runner's assertions (each shown to raise in `--selftest`, or proved before any statistic)

- **Known answers:**
  - D711's NQ book on its own window (274 trades, +$20.670105);
  - D714's books (B 271, A 216, +$25.578712);
  - D707's frozen ES F2 answer;
  - the loader through the vault's end reproduces all of these on its in-sample part, bit for bit (prefix stability),
    before one unseen trade is scored.
- **Lag and quantity:** D711's `rv_to` audit, σ and tier audits, and the right-quantity audit, on both roots.
- **Sign, in money,** on both multipliers.
- **The seal:**
  - in every mode except `--vault`, no session ≥ 2024-01-01 reaches a build;
  - `--vault` refuses without the principal's word, a verified freeze, and a first opening.
- **The sequence:**
  - the takeover is not computed when step 1 does not PASS (a canary that asks for it must raise);
  - the null's full-size subset reproduces B;
  - a planted agreement label that drops the losers takes over;
  - a random label does in about 5 % of worlds.

## 10. Predictions (about the unseen span, checked only in the joint run)

1. **NQ F2's mean net is positive but below +$20.67.** The 2022-05-16 → 2023 figure, +$14.15, is the better guide.
2. **The takeover does not happen:** (iii) fails, as it did in-sample.
3. **No calendar year holds more than half of NQ F2's net** (reported).
4. **ρ with the MACD arm stays below 0.1.**
