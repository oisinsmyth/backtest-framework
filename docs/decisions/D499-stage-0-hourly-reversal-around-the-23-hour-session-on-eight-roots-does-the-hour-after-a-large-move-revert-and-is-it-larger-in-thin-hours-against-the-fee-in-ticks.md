# D499 — stage 0: hourly reversal around the 23-hour session on eight roots. Does the hour after a large move revert, is the reversal larger in thin hours, and does it clear the fee in ticks?

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
In-sample **2016-01-04 → 2023-12-29** on D467's hourly session tables
(`data/fixtures/fut_sessions_hourly.csv.gz`, eight roots that pass its gates; RTY held back on
G2); **2024+ unread** (the runner raises past 2023). A stage 0 measurement in the sense of
D487 and D495: the premise is measured with its nulls before any component is declared; no
component line is scored here, so nothing enters the ledger from this record.

## 0. Why

The prop ledger has one entry (K8, NQ day session, PROVISIONAL and parked). A second component
must be on a different instrument or a different clock (ledger rule 4; C-b ρ < 0.3). The
principal's direction on 2026-09-12: look at a 24-hour future, with a construction that is not
limited to the off-hours but prefers and excels in them.

**What is closed and what is open.** BOOK_PROP's closure of the overnight line (2026-09-12)
forbids *any gate, window or size on the index overnight leg at micro cost*: a hold across the
18:00 → 09:00 leg on ES/NQ/YM, gated or not. It does not close the off-hours as a clock for a
construction whose horizon is an hour or two and whose sign is not the drift, and it does not
touch CL, GC, 6E, ZN, ZB. This record stays outside the closure: every trade here is opened
and closed inside the session, no trade holds the 18:00 → 09:00 leg, the sign is the
*opposite* of the last hour's move, and the roots include the five the closure never named.
The flatten rule of the plan (flat by 16:10 ET) is honoured by construction: no exit later than
the 15:59 close.

**The mechanism the record has.** In a thin book a move is more likely to be transitory price
impact than information, and transitory impact reverts (the inventory / liquidity-premium
literature; the closing-imbalance drift of Boyarchenko–Larsen–Whelan is the same mechanism at
one clock). Off-hours books on CME are an order of magnitude thinner than the day session on
the index roots, while CL, GC, 6E have real European sessions. So the hypothesis is *not* "the
overnight drifts" (closed) but "the hour after a large move reverts, more so in thin hours".
What the record also has against it: D471 (ES path efficiency is the random-walk value past
15 s), D487 (the intraday continuation on the index roots is regime-bound and its reversal is
in the last half-hour, worth a tick), D490/D492 (range reversion loses), and the cost
specification of FINDINGS §69 (the fee is a fraction of the move; a per-hour trade pays $3
against an hourly move, not a daily one). This stage 0 measures whether the premise is even
there at a size the fee can carry.

## 1. Data and definitions

- Session = D467's 18:00 → 16:59 ET table; hours `h18 … h23, h00 … h16` (23 segments), each
  with o/h/l/c/v/n. Same-front sessions only. A session enters the sample only if every hour
  used has a print (o and c not NaN); rows are otherwise dropped, never filled.
- Hourly move **r_h = (c_h / o_h − 1) · 1e4** bp, for entry hours h ∈ {h18 … h14} (an entry
  after hour h fills at o_{h+1}; the last permitted exit is the 15:59 close, so h14 is the last
  entry hour at k = 1 and h(15 − k) at hold k).
- Forward return at hold k: **f_h^k = (c_{h+k} / o_{h+1} − 1) · 1e4**; k ∈ {1, 2, 3}; primary
  **k = 1** (R14, one primary), k = 2 and 3 reported.
- **Large move**: |r_h| ≥ the 90th percentile of |r_h| over the trailing 250 same-front sessions
  *for that hour-of-day* (causal; the first 250 sessions are warm-up and not traded). One
  trigger per (session, hour); positions do not stack — the runner takes at most one trade per
  session per hour and the k-hour trades are scored as separate cells, not overlapped.
- **Trade**: sign = −sign(r_h); P&L in $ at one minimum contract = sign · (c_{h+k} − o_{h+1}) ·
  MULT; cost line A = the fee ($3 a round trip on the micros; $6 on ZN/ZB at full size, the
  ledger's C-a line); cost line B = fee + one tick crossed (the memory's rule that a passive
  line and a crossed line are reported side by side). MULT and tick as in D468 (MES 5, MNQ 2,
  MYM 0.5, MGC 10, MCL 100, M6E 12,500, ZN 1,000, ZB 1,000; ticks 0.25, 0.25, 1, 0.1, 0.01,
  0.0001, 1/64, 1/32).
- **Thin / thick hours**: per root, the 22 entry hours are ranked by their median volume
  (2016–2023); the lower half are *thin*, the upper half *thick*. Fixed by the clock, so the
  partition is not a fit. The US-clock split (off-hours = h18 … h08 and h16; RTH = h09 … h15)
  is reported beside it as a secondary read.
- **Relative volume of the move**: v_h / (trailing 250-session median of v_h for that
  hour-of-day); *low* < 1, *high* ≥ 1. Reported as a split within every cell.

## 2. Measurements

- **M1 the unconditional premise.** For each root and entry hour: β_h = cov(f_h^1, r_h) /
  var(r_h) and the correlation, pooled by thin / thick and by off-hours / RTH; the pooled
  β with its rotation band.
- **M2 the conditional premise (the trade).** For each root × {thin, thick} × k: N trades,
  gross mean $ per trade, mean bp, median, trimmed mean, hit rate, skew, the mean in **ticks of
  the minimum contract**, and the two net lines A and B. The z of the gross mean (mean / SE,
  block-bootstrapped by month, 500 draws).
- **M3 the yardstick of FINDINGS §69, by hour.** E|f_h^1| in ticks per root and hour; fee A and
  fee B as a fraction of it; break-even accuracy 0.5 + fee / (2 E|f|). This is the table that
  says whether an hourly clock can carry $3 at all, before any signal.
- **M4 the relative-volume split.** M2's gross mean for low- vs high-relative-volume moves
  within each cell; the difference and its SE. The mechanism predicts low > high.

## 3. Nulls

- **N1 exact common rotation.** For each root, the forward-return matrix F (sessions × hours)
  is rotated by d sessions against the signal matrix, d = 1 … T−1, enumerated (≈ 1,740 offsets
  after warm-up; SE of the p95 exactly 0). Each offset keeps the hour-of-day structure of both
  matrices, so the null carries the volatility seasonality and the thin/thick partition; what it
  destroys is the alignment of a move with the hour that follows it. Per cell: the p50 and p95
  of the gross mean $ per trade and of its z.
- **N2 family maximum.** The 16 primary cells (8 roots × thin/thick, k = 1) share each offset
  d; the maximum z across the family per offset gives the family p95. Secondary k and the
  relative-volume splits are reported against N1 only and are not used for the decision.

## 4. Decision rule (pre-registered)

- **PROCEED** to a declared stage-1 component (one cell, one root, k fixed here) if some primary
  cell has gross mean ≥ 1.5 × cost line B, z above the family p95, hit rate > 50%, and the
  same sign in both halves (2016–2019, 2020–2023). The stage-1 record would then declare that
  cell and score its component line at one micro on the ledger's standard.
- **PICK** if a cell clears N1 and cost line B but not the family bar: recorded, not pursued
  without a mechanism test.
- **CLOSE** the hourly-reversal line as a prop component otherwise. As always, the principal
  closes an avenue; the runner's verdict is a recommendation.

## 5. Predictions (checkable in the runner's quantities)

- **X-a** Unconditional β at k = 1 is negative in thin hours on the index roots, between −0.02
  and −0.08 (a 100 bp hour is followed by 2–8 bp back), and within ±0.02 in thick hours;
  |β| < 0.03 on ZN, ZB, 6E in both. The pooled thin-hour β sits outside its rotation band on at
  least two roots.
- **X-b** The conditional fade (thin, k = 1) on NQ: gross +4 to +10 bp a trade (+$6 to +$15 at
  one MNQ), hit 52–55%, ≈ 200–260 trades a year (10% of 11 thin hours × ~250 sessions); on ES
  +2 to +6 bp; thick hours within ±3 bp on both.
- **X-c** The family p95 of the z sits at +2.4 to +2.9 and **no primary cell clears it: the
  verdict is CLOSE.** The record's prior is D471 and D487: the hourly clock on these roots is
  near a random walk and the only reversal it has found was worth a tick.
- **X-d** Fee A is 4–9% of E|f^1| in thin hours on MNQ/MES/MCL/MGC and 2–4% in thick hours;
  fee B on ZN is above 30% of E|f^1| in every hour, so ZN/ZB fail the yardstick before any
  signal. Break-even accuracy in thin hours is above 52%.
- **X-e** Low-relative-volume moves revert more than high-relative-volume moves (M4 difference
  > 0) in at least 5 of 8 roots, but the difference is within 2 SE on all but at most one.

## 6. Files

This record · `scripts/run_d499_hourly_reversal_stage0.py` (`--run`, `--selftest`) ·
`data/d499_hourly_reversal_stage0.json` · trade file per root `data/d499_trades_<root>.csv.gz` ·
RESULT (separate). Runtime: seconds; the enumeration is 1,740 offsets × 16 cells, vectorised.
