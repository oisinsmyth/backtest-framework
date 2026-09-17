# D514 — does the Dow's gross turn positive without the five-hour minimum hold?

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D514-does-the-Dows-gross-turn-positive-without-the-five-hour-minimum-hold.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
**2016-01-04 → 2023-12-29 only.** No root's 2024+ slice is read.

## 0. The question, and why it is worth one record

D513's addendum split the six transplant roots into two groups with opposite diagnoses: **cost-dead**
(ZN, ZB, GC — a real gross edge killed by the tick) and **signal-dead** (YM, CL, 6E — gross itself
negative). The principal asks whether YM's negative gross is a property of the signal or of **the
exit**: the frozen arm carries a **five-hour minimum hold**, and the day-session window is only seven
segments wide, so a five-hour floor leaves almost no room for the conditional exit to act.

**That is not a rhetorical worry. D491 measured it and said so:** at its best cell trips were 1.17 a
session, *"on 83% of sessions the construction IS a fixed day-session hold"*, and *"the minimum hold
did almost nothing on the index roots, because the closure's six-hour window leaves nearly no scope
for an early exit… the idea is untested rather than refuted."* If the hold is what suppresses the
exit, removing it is the single change most likely to move YM's gross.

**What D491 does and does not already answer.** It laddered M ∈ {1, 2, 3, 5} on YM, but only for the
**single** indicators B1 and B2 separately, and only **net**. The admitted arm is the **AGREE**
construction — both MACDs agreeing — and its gross on YM across the ladder is unmeasured. D491's YM
net figures worsen as M falls (B1: −0.771 at M=5 to −0.995 at M=1; B2: −0.399 to −0.795), which is
what more trips do to a net line and says nothing about gross.

## 1. What is scored

**The frozen arm's machinery, unchanged**, imported from `d506_macd_breadth` (`build_root`,
`simulate_window`) — the AGREE signal, the decide-at-close/execute-at-next-open convention, the
forced flat at the session's last segment. **The only thing varied is M**, the minimum hold.

- **M ladder:** 0, 1, 2, 3, 4, 5. The frozen value is 5.
- **M = 0 and M = 1 are expected to be identical** and the runner asserts it: a position entered at
  decision `t` has `entry_t = t`, and the exit test `elapsed = t' − entry_t ≥ M` is first evaluated
  at `t' = t + 1`, so `elapsed` is never 0 at an exit opportunity. "No minimum hold" therefore means
  M ≤ 1, and the record will say so rather than quoting M = 0 as if it were distinct.
- **Roots:** **YM** (the question), plus **CL** and **6E**, the other two signal-dead roots, so the
  answer is not a single draw. **NQ is reported as a reference row only** and is **not** a declared
  cell: nothing here re-specifies the admitted arm, whose 2024+ is spent in any case.

## 2. The primary statistic, one (R14)

**YM's GROSS mean dollars per session at no minimum hold (M ≤ 1), at one MYM.** Gross, because the
question is about the signal and not the fee; per session rather than per trade, because lowering M
raises the trade count and a per-trade figure would hide that.

**Reported beside it, always:** gross and net per trade and per session, gross and net Sharpe, trips
per session, and the mean realised hold in segments — the quantity that shows whether M was binding
at all.

## 3. Nulls

- **N1, exact enumerated rotation of the signal.** The AGREE grid is rolled along the **session**
  axis by `k = 1 … T−1` against the price grid, and the machine is re-run at every offset. Rolling
  whole sessions preserves each session's intraday signal shape and its autocorrelation, which is
  what `log-MACD-is-a-real-signal` requires: **rotate a smoothed signal, never shuffle it.**
- **N2, family maximum** over the **18 declared cells** (3 roots × 6 M values) under common offsets.
  The primary must clear this, not only N1.

## 4. Decision rule (pre-registered)

- **POSITIVE** if YM's gross per session at M ≤ 1 is above zero **and** clears both N1 and the N2
  family p95. The answer to the principal's question is then yes, and a net line and a cost study
  would follow in a separate record.
- **POSITIVE BUT INSIDE THE NULL** if the gross is above zero and fails either bar: the sign is
  reported and claimed as nothing.
- **NEGATIVE** if the gross stays at or below zero. The exit is then exonerated and YM is
  signal-dead at this clock, as D513's addendum read it.

**No outcome changes the admitted arm**, and no outcome reads a forward slice.

## 5. Predictions (checkable in the runner's quantities)

- **X-a** M binds hard on these roots: trips per session rise from about **1.0 at M = 5 to between
  1.3 and 1.8 at M ≤ 1**, and the mean realised hold falls from near the full window to **2 to 4
  segments**.
- **X-b** YM's gross at M ≤ 1 is **still negative**, between **−$3 and 0** a session. The exit is not
  what is wrong with YM.
- **X-c** Gross **falls monotonically as M falls** on at least two of the three roots: a shorter hold
  gives the move less time to develop, so per-trade gross shrinks faster than the trade count grows.
- **X-d** NQ's gross stays **clearly positive at every M**, between **+$8 and +$16** a session,
  because its signal is the one that is actually alive.
- **X-e** The N2 family p95 over eighteen cells lands between **+$1 and +$4** a session, and **no YM
  cell clears it**.
- **X-f** The verdict is **NEGATIVE**.

## 6. Files

This record · `scripts/run_d514_hold_ladder.py` (`--run`, `--selftest`) ·
`data/d514_hold_ladder.json` · RESULT (separate). Runtime under three minutes: 18 cells × ~1,870
enumerated offsets, each a re-run of a six-segment vectorised machine.
