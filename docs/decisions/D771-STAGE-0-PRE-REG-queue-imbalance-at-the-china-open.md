# D771 STAGE 0 PRE-REG — the queue imbalance at the touch on gold's China-open fade: does the book's lean at 09:30 Beijing predict the next minute, how fast does that fade, and does any of it reach the 15:00 exit?

*2026-10-02. The principal:*
- *"So even if we had the whole order book we could not predict price because of market orders?";*
- *"Pre-reg the queue imbalance check as D771".*

- **What it is:** a Stage 0 premise check on one base construction, gold's China-open fade (D765, D767, D770). It
  admits nothing. The line stays open (the principal, 2026-10-02: "we will not be closing this line, yet").
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the
  result separately.
- **The prop book's rules:** one MGC, flat before 16:10 ET (exits at 02:00/03:00 ET), fully algorithmic, one position.

## 0. What is known, and what this test cannot claim

- **D765:** the opening half-hour after 09:00 Beijing reverses on gold (ρ −0.063, p 0.007); the fade grosses about
  +\$3.1 a trade, below the \$5.93 micro round trip.
- **D767:** confirmation from the AUD and the other metals had negative accuracy.
- **D770, on the paid window:**
  - real aggressor flow over 09:00–09:30 does not sort the reversals (ρ +0.016);
  - a passive fade nets −\$0.92 (gross +\$2.12) and earns only December–March;
  - the cost line is about right at this clock; MGC is quoted within 0.2 ticks of GC.
- **The partial-oracle curve (keep the top third):** break-even needs ρ ≈ 0.05.
- **What the book is known to predict (the literature):** the imbalance between the sizes at the best bid and the
  best ask predicts the direction of the next mid-price change, most strongly where the spread is usually one tick
  (Cont, Kukanov and Stoikov 2014; Gould and Bonart 2016). That information is measured in seconds. **The expected
  failure is the horizon:** a 09:30 snapshot carries little about 15:00.
- **The data** (`data/raw/databento/china_window_2016_2023/`, PAID, read-only; manifest
  `data/china_window_tbbo_manifest.csv`):
  - GC `bbo-1m`, 2016-01-04 → 2023-12-29; MGC `bbo-1m`, 2022-01-03 → 2023-12-29; each 18:30 ET (the evening before)
    → 03:15 ET.
  - Each record holds the best bid and ask, the **size** at each (`bid_sz_00`, `ask_sz_00`) and the **order count**
    at each (`bid_ct_00`, `ask_ct_00`). Checked on one GC and one MGC file before this record: the GC touch holds
    about 20 contracts a side (median), MGC about 5. No outcome was read.
  - The `bbo-1m` record stamped on the minute (`ts_recv`) is the book at that minute (D770).
- **What this test cannot claim:** everything is in-sample (2016–2023), and the fade's sign came from D765. A pass
  earns only a confirmation on unseen data (the joint vault or the forward recorder, on the principal's word). The
  top of book is one level: depth beyond the touch is not in this data.

## 1. The candidates and the base trades (unchanged from D770)

- **The candidates:** D770's used sessions: D765's MGC-eligible sessions with x ≠ 0, less D770's exclusions (a
  contract mismatch over 2 ticks, two instruments, no quote).
- **Also dropped (and counted):** fewer than 8 of the 10 snapshots below valid (a record within 3 minutes, bid and ask
  finite with ask > bid, both sizes > 0).
- **x** = P(09:30) − P(09:00) Beijing (D765's bars). **The fade's side d** = −sign(x).
- **The taker fade:** D765's trade, gross in dollars at one MGC, net of \$5.93.
- **The passive fade:** D770's primary (a resting order at the 09:30 touch on side d, filled on a trade-through within
  30 minutes, the exit at the 15:00 touch), net of \$3.00 plus D770's MGC exit adjustment.

## 2. The score

- **The imbalance at minute t** (GC `bbo-1m`, the latest record at or before t, within 3 minutes):
  I(t) = (bid size − ask size) / (bid size + ask size), in [−1, 1]. Positive: the book leans to the bid (more resting
  buyers at the touch), which predicts an up-tick.
- **The primary score:** Q = d · mean of I(t) over the snapshots at 09:21, 09:22, …, 09:30 Beijing (the valid ones
  among the ten). Positive Q: the book leans in the fade's direction.
- **Reported beside it, not gated:**
  - Q₁ = d · I(09:30), the single snapshot;
  - Q_ct, the same as Q on order counts instead of sizes;
  - ρ(Q, D770's A), to show the two filters are different objects.
- **The predicted sign:** ρ(Q, the fade's gross) > 0.

## 3. P, the premise (must hold, or the readings below are void)

- **P:** ρ(I(09:30), mid(09:31) − mid(09:30)) > 0 on all candidate sessions, at a t-stat ≥ 3 (Spearman; the t from
  √(n−2)·ρ/√(1−ρ²)). The mid is (bid + ask)/2 from `bbo-1m`.
- This is the known short-horizon effect. If it fails, the score is not measuring what the literature measures (a
  field, a timestamp or a sign is wrong), and the reading is **PREMISE FAILS**.
- **The decay curve, reported:** ρ(I(09:30), mid(t) − mid(09:30)) for t = 09:31, 09:35, 09:45, 10:00, 11:30 and 15:00,
  each with its t-stat. **This is the answer to the principal's question:** how far ahead the book at the touch sees.
- **Reported:** the same curve for MGC on 2022–2023, and ρ(I_GC(09:30), I_MGC(09:30)) on the shared sessions.

## 4. Q1: the imbalance filter on the taker fade (\$5.93)

- **The selection:** Q's walk-forward top third (the 2/3 quantile of the prior 250 candidates' finite Q, at least
  100, strictly prior; D767's `wf_select` and `pool_mask`).
- **The gates** (as D767 and D770's Q2):
  - **G1:** the unfiltered fade's mean gross > 0 at t ≥ 2 (on these candidates);
  - **N:** the selected book's mean net above the p95 of the exact rotation of Q against the candidates (every offset
    k = 1 … n − 1; SE 0);
  - **B1:** the month shares within 5 points of the pool's;
  - **B2:** net > 0 outside December–March;
  - **G2:** mean net > 0, t ≥ 2, Holm (over Q1 and Q2) below 0.05, and net > 0 without its best two years.
- **The readings, in order:** NO MECHANISM (G1 fails) / NOT ABOVE NULL / UNBALANCED / MECHANISM ONLY (G2 fails) /
  SUPPORTED.
- **Reported:** ρ(Q, gross) on the pool and the AUC against the oracle label (net > 0); Q₁'s and Q_ct's ρ; Q's month
  and year shares.

## 5. Q2: the imbalance filter on the passive fade

- **The selection:** the same Q top-third flags, applied to D770's passive fade (filled sessions only trade).
- **The gates:**
  - **N:** the selected passive book's mean net above the p95 of the exact rotation of Q against the candidates;
  - **B1 / B2** as in Q1;
  - **C:** the MGC book on the selected 2022–2023 sessions within 2 SE of the GC proxy's (D770's calibration, on the
    selection);
  - **G2:** mean net > 0 at t ≥ 2, Holm (over Q1 and Q2) below 0.05, and net > 0 without its best two years.
- **The readings, in order:** NOT ABOVE NULL / UNBALANCED / CALIBRATION FAILS / NO PRIZE / SUPPORTED.
- **Reported:** the fill rate and the adverse-selection split (the taker fade's gross on filled against unfilled) on
  the selection, since the book's lean at 09:30 may change which resting orders fill.
- **Not tested:** Q combined with D770's A. D770's post hoc passive-with-A line (+\$1.68 on 402) stays unread.

## 6. GO, priors, predictions, reporting

- **GO = SUPPORTED on Q1 or Q2, with P holding.** It starts a confirmation conversation (the vault or the forward
  recorder). It admits nothing.
- **The priors:** P holds about 90%; Q1 SUPPORTED about 3%; Q2 SUPPORTED about 4%.
- **The predictions (checkable):**
  - ρ at 09:31 between +0.10 and +0.35;
  - the decay curve below +0.03 by 10:00, and |ρ| below 0.03 at 15:00;
  - |ρ(Q, the fade's gross)| below 0.03.
- **All four groups for each traded book:**
  - **Performance:** gross and net, Sharpe and Sortino, maximum drawdown, the mean |move| against the cost, and the
    breakeven cost.
  - **Trade distribution:** count, mean, median, win rate, payoff, skew, kurtosis, the symmetric 1% trims, and the
    largest trades named.
  - **What the winners depend on:** years, months, EDT against EST, long against short, and the 2020
    night-suspension sub-era.
  - **Nulls:** p50, p95 and the rank.
- **The component line:** net Sharpe, Sortino, hit rate, skew, gross beside net, and the daily ρ with D737's twin,
  NQ F2 and C1.

## 7. Runner assertions

- **Lag:**
  - every snapshot is stamped at or before 09:30, and the fade is entered at 09:30 or later;
  - a second implementation (explicit loops over the raw `bbo-1m` records) re-derives the ten imbalances, Q and the
    09:30/09:31 mids on 40 sampled sessions;
  - D767's flag audit re-derives every selection flag.
- **Sign, in money:**
  - a synthetic session with a bid-heavy book (I > 0) followed by a rise gives a positive P contribution;
  - for a fade short (x > 0), an ask-heavy book gives Q > 0;
  - a mirrored book raises.
- **Right quantity:**
  - Q differs from D770's A on the candidates;
  - Q₁ differs from Q;
  - rotation offset 0 equals the observed;
  - no record on or after 2024-01-01;
  - sessions read = used + each exclusion.
- **The self-test:**
  - the imbalance on hand-built records (including a zero side, which is invalid);
  - stale snapshots refused;
  - the second implementation raises on a broken size;
  - chunk = whole for the rotations on processes.

## 8. Output

- `scripts/stage0_d771_china_open_queue_imbalance.py`;
- `data/stage0_d771_china_open_queue_imbalance.json` (statistics only).
- It reads D765's extraction cache (`temp/d765/`), D770's functions, and the paid window (read-only, never
  modified).
- The result is a separate record.
