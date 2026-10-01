# D748 STAGE 0 RESULT — READY: the activity keeper is one M6E at 13:30, never worse than −\$41 a trade in-sample, and the index-only fallback is NOT READY

*2026-10-01.*
- *Pre-registration: [D748](D748-STAGE-0-PRE-REG-the-activity-keeper.md) (0de00296), with A1 (524c2a40): the crossing
  line is `d508_exec`.*
- *Runner: `scripts/stage0_d748_activity_keeper.py`.*
  - *It is committed before its run (30dbfbea, then 6d01982c per A1, then the books plumbing ca130515).*
  - *Two earlier `--run` attempts stopped before writing anything. The first was A1's missing cost key. The second
    was scipy, absent on the interpreter that reads the 5-minute fixture; it had already passed the known answer and
    the lag audit.*
- *Output: `data/stage0_d748_activity_keeper.json`. Component calendars: `data/d748_component_books.csv`.*
- *In-sample, 2018-05-14 → 2023-12-29: 1,457 ES sessions, 1,357 of them eligible (not FOMC, not an early close).*

## 0. The readings

| variant | K1 worst trade (≥ −\$50) | K2 worst 30 days (≥ −\$150) | K3 cost a year (≤ \$300) | K4 breaches | reading |
|---|---|---|---|---|---|
| **F, the selector (primary)** | **−\$40.55** | **−\$75.04** | **\$268.22** (NONE, C7) | **0** | **READY** |
| I, index micros only | −\$102.46 | −\$174.83 | \$99.62 | 0 | **NOT READY: K1, K2** |
| M, M6E always | −\$40.55 | −\$75.04 | \$292.09 | 0 | READY |

**The selector is M6E.**
- Variant F picked M6E on **97.2 %** of fires (mean over its cells), above the declared 95 %.
- Against M it reduces nothing: the same worst trade and worst 30 days.
- What it adds is **robustness:**
  - M missed 2–5 fires a cell on sessions where M6E's window was incomplete (roll days), and the backup session
    caught every one;
  - F fell back to M2K, MYM or MES on about 3 % of fires and failed none.

**The known answers reproduced** (13:30–14:00 σ\$, 2016–2023): M6E \$8.079 (1,983), M2K \$22.318 (1,598), MYM \$24.298
(1,970), MES \$31.971 (1,975), MNQ \$50.368 (1,972). The component books held their asserted counts, and the
keeper-off canary breached on every cadence.

## 1. How often it fires, variant F (fires a year)

| calendar | C7 | W1 | T5 | T10 | C30 |
|---|---|---|---|---|---|
| **FULL** (D737 + C1 + F2) | 0.4 | 0 | 0.4 | 0 | 0 |
| **NO_D737** (C1 + F2) | 33.1 | 16.9 | 32.2 | 5.9 | 0.5 |
| **NONE** (keeper alone) | 68.3 | 52.1 | 66.8 | 29.5 | 13.3 |

**What this shows:**
- **With D737 in the book the keeper almost never fires.** D737 trades 1,235 of the 1,457 sessions, so the two fires
  in 5.6 years come under C7 and T5 only.
- **Without D737 it is a real line, about 33 fires a year on the tight cadences.** 55 of C7's 186 fires were
  redundant: C1 or F2 traded later that session. The keeper cannot see their entries at 13:30, by declaration.
- **Under NONE, C7 fires more often than once a week** (68 against W1's 52). The one-session backup margin brings the
  fire forward of the 7-day deadline.

## 2. What a keeper trade looks like (variant F, NONE, C7; 384 trades)

| | |
|---|---|
| net per trade, mean / median | **−\$3.93** / −\$4.38 |
| gross per trade, mean | +\$0.44 (no edge, as declared) |
| worst / best net | −\$29.27 / +\$32.74 |
| stop-hit rate | 0.5 % |
| correlation of daily keeper P&L with the FULL book's daily net | 0.002 |

**What it costs:**
- Across F's NONE cells the mean net is −\$3.41 to −\$5.09 a trade, the cost line (\$4.38 on M6E) less a near-zero
  gross.
- The worst single trade in any F cell was −\$40.55 (W1). Against a 50K's \$2,000 buffer that is 2 %. The worst
  30 days, −\$75, is 3.8 %.

**The cost line is optimistic.** `d508_exec` was measured 2025-09 → 2026-09, and a tick is fixed in price terms
(the table's `window_caveat`). K3's \$268 a year sits \$32 under its bar under NONE × C7. A wider historical spread
could cross it, but only in the hypothetical keeper-alone book. On the FULL calendar the keeper costs about
\$1 a year.

## 3. The index-only fallback (variant I)

**NOT READY on K1 and K2.** M2K and MYM are about 3× M6E's σ\$:
- worst trade −\$102.46;
- worst 30 days −\$174.83.

Its mean net is near zero (−\$0.2 to −\$3.6). That is variance, not edge: gross +\$3.4–3.6 on n 166–293.

**It still never comes near killing a 50K** (5 % and 8.7 % of the buffer). But it misses the bars declared in
advance, so it is not recorded as ready. **A firm that does not permit M6E needs a new record,** for example a
smaller stop or another FX micro.

## 4. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | F picks M6E on ≥ 95 % (P 0.85) | **held:** 97.2 % |
| P2 | FULL ≤ 5 fires a year on every cadence; NONE × T5 about 50 | **held** (0.4 at most); NONE × T5 **66.8**, above (the backup margin) |
| P3 | READY (P 0.85) | **held** |
| P4 | mean net about −\$4 ± \$1.5 | **held:** −\$3.41 to −\$5.09 on F × NONE |
| P5 | I is INDEX-ONLY READY, worst near −\$40 to −\$50 | **missed:** −\$102.46, NOT READY |

## 5. What follows (§7 of the pre-registration)

**The keeper is recorded as an execution rule for the prop account.** It is not a component and has no slot:
- **When:** 13:30 ET.
- **What:** 1 contract of whichever of M6E / M2K / MYM / MES / MNQ has the smallest forecast σ\$ (in practice M6E).
- **How:**
  - direction is the move since 09:00;
  - a 4σ̂ stop and a 14:00 exit;
  - it fires only when the firm's activity deadline would lapse, with one backup session.

**Before it is relied on:**
- each firm's activity rule and permitted products are confirmed at the source;
- whether **Apex and MyFundedFutures permit M6E** in particular; only Topstep's is confirmed;
- the unverified cadences (Tradeify, Bulenox, Alpha, Lucid).

**Unchanged:** profit-day rules (Apex's two \$50 days per 30; payout winning days) remain out of scope. Only the
components can meet them.
