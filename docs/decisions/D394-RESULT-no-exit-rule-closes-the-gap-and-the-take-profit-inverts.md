# D394 RESULT — none of the 126 exit-rule cells closes the cost gap, and the take-profit arm is DIRECTION-INVERTED

**Status:** RESULT. **Q1 HELD, so §5's kill condition fires: the record stops WITHOUT spending a
single null draw.** Admits nothing (R15). Nothing retired.
**Date:** 2026-09-08 · Pre-registration: [D394](D394-exit-rules-on-the-low-hold.md) + amendment
2a′, **both committed before the runner existed** (R8) · Runner:
`scripts/run_d394_exit_grid.py` · Artifact: `data/d394_exit_grid.json` · **45 s** ·
**Holdout reads: 0.**

---

## 0. The verdict

| | trades | gross | 2c | net | **ratio** |
|---|--:|--:|--:|--:|--:|
| **baseline cap 10** (no rule) | 22,855 | +10.52 | 61.40 | −50.88 | 0.17× |
| **best of all 126 cells** — `cap10/T:p10` | 22,855 | **+13.05** | 61.40 | **−48.35** | **0.21×** |
| baseline cap 5 | 24,777 | +4.72 | 61.48 | −56.76 | 0.08× |
| best at cap 5 — `cap5/T:p10` | 24,777 | +4.90 | 61.48 | −56.57 | 0.08× |

**§0 of the pre-registration set the bar before anything ran: gross must reach ~61 bp for gate 1c's
1.0×. The best of 126 cells reaches +13.05.**

> **NO CELL CLEARS. The best exit rule in the whole grid closes 5% of a 50.88 bp gap.**
> **Q1 predicted the best would stay under 0.6×; it is 0.21×.**

**§5's kill condition therefore fires as written: the exit-rule route to profitability on the low
hold is answered NO, and no null was drawn. The best-of-63 floor was never needed, because nothing
reached a bar it could be measured against.**

---

## 1. Predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | *(against)* no cell above 0.6× | **HELD** — best 0.21× |
| **Q2** | *(against)* the take profit REDUCES gross at every level | **FAILED — DIRECTION-INVERTED** |
| **Q3** | *(against)* the trailing stop REDUCES gross at every level | **HELD** |
| **Q4** | the stop raises gross at 20% and reduces it at 5% | **FAILED in sign, held in order** |
| **Q6** | median rises where mean falls on T | **not applicable** — the mean rose too |

**Change in gross versus the baseline, primary cap 10:**

| arm | 5% | 10% | 20% |
|---|--:|--:|--:|
| **stop** | −5.65 | −3.67 | −3.67 |
| **take profit** | **+1.69** | **+2.52** | **+1.59** |
| **trailing stop** | −4.39 | −1.11 | −2.32 |

---

## 2. THE ONE REAL FINDING, and it is against my own declared mechanism

**§1 declared: *"A TAKE PROFIT truncates the right tail and should REDUCE gross. This is declared
against the take-profit arm."* It raised gross at all three levels.** Under §1's own rule that is
**DIRECTION-INVERTED and counts against the mechanism I stated**, even though the number is
favourable.

**Why the declaration was wrong, and it is a transferable lesson.** The mechanism was derived from
the **cap-20** ledger, where dropping the top 1% takes the mean from +22.06 to −19.82 — the right
tail unambiguously carries that book. **I applied a tail structure measured at one hold to a
different hold.** At cap 10 the mean is +10.52, the window is half as long, and only **6.8%** of
trades ever reach +10%.

**What the inversion says about the book:** on the 10-bar window, a name that has gained 10%
**gives back more than it goes on to make**. Taking the profit and standing aside is worth
**+2.52 bp**. That is a genuine, if tiny, mean-reversion finding about this book's winners.

**And `T:p5` shows what a target really trades.** Firing on 22.5% of trades, it lifts the **median
from +6.78 to +34.68** while lifting the mean only +1.69. **A target buys consistency, and it is
priced in the mean.**

**The stop is the clearest negative.** It reduces gross at **every** level, most at the tightest
(−5.65 at 5%). A stop does not avoid a loss — it realises one — and on this book the names that
breach keep no adverse drift worth capturing.

---

## 3. A CORRECTION: the identical cost across cells is a MODEL PROPERTY, not a measurement

Every one of the 63 cap-10 cells reports a round trip of **exactly 61.40**. It would be easy —
and wrong — to read that as confirming §0's premise that an exit rule cannot change cost per trade.

**`two_c` reads only `(row, entry_bar)`** (`run_d347_long_signal_controls.py:146-149`): the median
half-spread and median close **at entry**, times a fixed crossing count. **It cannot vary with the
hold.** The runner passed rebuilt trade tuples carrying each cell's new hold, and that was a no-op.

**The premise is still right** — one round trip per trade, and these rules move only the exit, never
the entries or the trade count — but it is **encoded in the cost model, not demonstrated by this
run**, and the record says so rather than claiming a confirmation it did not earn.

---

## 4. What was NOT done, and why the kernel was never touched

**`d345_event_book.simulate_event` is unmodified.** Eighteen scripts import it. Amendment 2a′
adopted D380's insight that per-trade P&L is the sum of a trade's own per-bar path, so all 126
cells are **re-cuts of one stored cumulative-sum matrix**. `trade_paths`, `pnl_at`, `assert_CUT`
and `assert_OVL` are imported from `run_d380_exit_rules`, not reimplemented.

**`[CUT]` matched the kernel to exactly 0.00e+00** on both holds (22,855 and 24,777 trades) — the
re-cut *is* the kernel's arithmetic, not a resemblance. **`[B]`** confirmed that with every level
off, each arm reproduces the plain cap ledger **bit-identically**.

**Intrabar stops remain out of scope** (§2a). These are **market-on-close** rules on the firing bar
— D380's convention, adopted in 2a′ because next-open is not representable in a close-to-close
path matrix. **MOC is the more favourable of the two**, so these results are, if anything,
generous.

**Assertions:** `[CUT] [B] [OVL] [M] [H] [X] [P]`. `[X]` proves a one-bar look-ahead would give a
*different* hold, so the test can distinguish one; `[H]` pins all three rules on a constructed path
before the fixture touches anything.

---

## 5. What this closes and what it does not

**Closes, on the evidence:** the question the principal asked — *can a stop, a take profit, a
trailing stop, their pairs, or all three together make the low hold pay?* **No.** Not at 5%, 10% or
20%, not in any of 7 families, not at either low hold. The gap is 50.88 bp and the best rule
recovers 2.53 of it.

**Does not close:**

1. **The avenue itself — only the principal closes one (R15).**
2. **Intrabar stops**, which are strictly better than these bar-close ones and untested. A separate
   record with its own fill audit; and note that the *direction* of every arm here would have to
   reverse by an order of magnitude to matter.
3. **D393's open items are untouched:** the best-of-10 floor is still uncomputed, and B's binding
   margin is still +0.91 bp.

**And it does not change the shape of the problem.** [Addendum 6](D393-ADDENDUM-6-the-ten-cells-and-the-price-split.md)
found the whole edge sits in the cheapest price tercile, which is the most expensive to trade.
**Exit rules cannot reach that, because they do not touch cost.**

---

**Status footer.** No null drawn, no holdout read, nothing admitted, nothing retired.
`docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty.
