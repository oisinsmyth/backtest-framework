# D787 STAGE 0 RESULT: NOTHING. Whether the China open has turned 5–30 minutes later does not sort the fade. No cell of 30 clears its own null (best rank 0.78; family p 0.76); the opens still at their extreme earn as much as the ones that turned

*2026-10-03. One completed run of `scripts/stage0_d787_china_open_turned_fade.py --run` (78 seconds), under the
amended grid of the [pre-registration](D787-STAGE-0-PRE-REG-fade-the-china-open-only-once-it-has-turned.md) (`35badac6`,
amended `90cc4aac` before any read).*
- **Output:** `data/stage0_d787_china_open_turned_fade.json` (statistics only).
- **Two launches stopped before any statistic was computed or written.** Both are disclosed, with their fixes
  committed before the next launch:
  - **`bc845c9a`:** 14 workers ran out of memory on the tape reads; now 8.
  - **`3c964c5c`:** the right-quantity check fired. Voiding a session on any isolated print among the 09:01–09:30
    closes dropped 19 large sessions: the L = 0 taker book read 1,678 at +\$2.23, against D767's 1,697 at +\$3.14.
    - A session is now voided only on the prices the trade uses, as in D765. An isolated print inside the window is
      skipped when finding the extreme.
    - L = 0 then reproduced D767 exactly before the grid ran.

## 0. Checks

- **Right quantity:**
  - L = 0, unconditional, reproduces D767's taker book (1,697; +\$3.14) and D770's passive book at the 09:30 touch
    (1,466 filled; +\$2.12; fill rate 92.1%; filled +\$2.56 against unfilled +\$10.44), through this runner's own
    re-implementation of D770's fill at a movable clock;
  - the 09:46 book differs from the 09:31 book.
- **The lag audits passed:**
  - the resting level and the fill on 40 sampled (session, delay) pairs, by explicit loops over the raw tbbo and
    bbo-1m records;
  - K1h on 40 sessions, by explicit loops over the bar highs and lows.
- **Outcome-blind:** every flag was built by a reader that raises on any price after the check time (proven in the
  self-test).
- **The seal:** nothing on or after 2024-01-01.
- **The null:**
  - each cell's flag was rotated over all 1,696 offsets;
  - the family-max null applied each offset to all 30 cells at once.

## 1. The controls: waiting alone (every valid session)

| entry | passive: n, gross, net (t gross) | taker: gross, net (t gross) |
|---|---|---|
| 09:30 / 09:31 (D770 / D767) | 1,466; +\$2.12; −\$0.92 (1.52) | +\$3.14; −\$2.79 (2.49) |
| check 09:35, enter 09:36 | 1,458; +\$1.80; −\$1.23 (1.32) | +\$2.88; −\$3.05 (2.31) |
| 09:40 / 09:41 | 1,455; +\$1.99; −\$1.05 (1.46) | +\$3.24; −\$2.69 (2.64) |
| 09:45 / 09:46 | 1,457; +\$2.02; −\$1.01 (1.51) | +\$3.26; −\$2.67 (2.67) |
| 09:50 / 09:51 | 1,442; +\$1.87; −\$1.17 (1.41) | +\$3.76; −\$2.17 (3.15) |
| 10:00 / 10:01 | 1,451; +\$1.83; −\$1.21 (1.40) | +\$3.73; −\$2.20 (3.13) |

- **Waiting helps the taker book slightly and the passive book not at all.**
  - Taker gross rises from +\$3.14 to about +\$3.75 by 09:51: the open's 45-minute drift (D765's +0.017) is skipped.
  - Passive gross falls slightly, because the adverse selection gets worse later (§3).
- **Every book stays net negative.**

## 2. The grid (passive and taker, the condition kept against the same-clock control)

| delay | condition | passive: kept (share), net, t; **skipped gross**; vs control; rank | taker: net, t; skipped gross; rank |
|---|---|---|---|
| 5 | K1c | 1,072 (0.74), −\$1.36, −0.83; **+\$2.15**; −0.13; 0.44 | −\$3.28, −2.19; +\$3.51; 0.39 |
| 5 | K1h | 1,178 (0.81), −\$1.52, −0.98; **+\$3.01**; −0.29; 0.33 | −\$3.43, −2.42; +\$4.38; 0.27 |
| 5 | K2 | 708 (0.49), −\$1.40, −0.63; **+\$1.95**; −0.16; 0.42 | −\$3.25, −1.62; +\$3.06; 0.41 |
| 10 | K1c | 988 (0.68), −\$1.41, −0.87; **+\$2.76**; −0.36; 0.35 | −\$3.35, −2.28; +\$4.63; 0.23 |
| 10 | K1h | 1,096 (0.75), −\$0.88, −0.54; **+\$1.47**; +0.17; 0.57 | −\$2.62, −1.80; +\$3.02; 0.53 |
| 10 | K2 | 693 (0.48), **−\$0.02**, −0.01; **+\$1.06**; **+1.02**; **0.78** | −\$1.96, −1.14; +\$2.55; 0.74 |
| 15 | K1c (the original idea) | 975 (0.67), −\$0.94, −0.61; **+\$1.88**; +0.07; 0.55 | −\$2.71, −1.91; +\$3.34; 0.52 |
| 15 | K1h | 1,040 (0.71), −\$0.84, −0.53; **+\$1.59**; +0.17; 0.59 | −\$2.40, −1.68; +\$2.60; 0.66 |
| 15 | K2 | 705 (0.48), −\$2.33, −1.30; **+\$3.26**; −1.32; 0.17 | −\$3.94, −2.40; +\$4.46; 0.17 |
| 20 | K1c | 940 (0.65), −\$1.02, −0.62; **+\$1.59**; +0.15; 0.58 | −\$2.08, −1.43; +\$3.60; 0.57 |
| 20 | K1h | 1,012 (0.70), −\$1.33, −0.84; **+\$2.25**; −0.16; 0.42 | −\$2.33, −1.66; +\$4.16; 0.43 |
| 20 | K2 | 693 (0.48), −\$1.83, −0.93; **+\$2.48**; −0.67; 0.31 | −\$3.19, −1.81; +\$4.71; 0.22 |
| 30 | K1c | 901 (0.62), −\$1.84, −1.12; **+\$2.86**; −0.63; 0.28 | −\$2.49, −1.67; +\$4.21; 0.43 |
| 30 | K1h | 966 (0.67), −\$2.26, −1.44; **+\$3.93**; −1.06; 0.13 | −\$2.84, −2.00; +\$5.01; 0.27 |
| 30 | K2 | 688 (0.47), −\$2.16, −1.10; **+\$2.69**; −0.95; 0.25 | −\$2.43, −1.37; +\$3.94; 0.45 |

- **Every cell reads NO EFFECT or NOT ABOVE NULL. No cell clears the triage bar.**
- **The best cell, L10 K2 passive** (past the 09:30 price at 09:40):
  - rank 0.78 against its own rotation (p95 needs Σg/Σ|g| 0.122; it has 0.087);
  - **family p 0.76** (the family-max p95 is a within-cell rank of 0.996);
  - net −\$0.02 on 693 trades, gross t 1.58, 4 of 8 years profitable;
  - +\$4.60 in Dec–Mar against −\$2.41 in Apr–Nov, the season again.
- **The skipped sessions earn positive gross in every one of the 30 cells:** +\$1.06 to +\$5.01, often more than the
  kept ones on the taker book.
  - The opens still at their extreme 5–30 minutes later are not continuing. The fade earns on them about as it does on
    the rest.
  - The premise, "an open still at its extreme is a trend, and fading it is fading a trend", is not borne out at any
    delay.
- **The original idea (L15 K1c, passive):**
  - keeps 67%; net −\$0.94 against the control's −\$1.01, i.e. +\$0.07;
  - skipped +\$1.88 gross; rank 0.55.

## 3. Adverse selection at the later clocks (the passive book's unfilled sessions)

| rest at | fill rate | taker gross: filled / unfilled |
|---|---|---|
| 09:30 | 92.1% | +\$2.56 / +\$10.44 |
| 09:35 | 91.6% | +\$2.06 / +\$11.78 |
| 09:40 | 91.3% | +\$2.42 / +\$11.75 |
| 09:45 | 91.5% | +\$2.47 / +\$12.01 |
| 09:50 | 90.6% | +\$2.19 / +\$20.13 |
| 10:00 | 91.2% | +\$2.38 / +\$17.56 |

- **The resting order's problem does not go away by waiting; it sharpens.** Later in the session the sessions that
  turn without filling are larger reversals: about 9% of sessions, +\$12 to +\$20 gross each.
- **This is where the passive book loses its edge,** at every clock.

## 4. The best cells in detail (four groups)

| | L10 K2 passive | L10 K2 taker |
|---|---|---|
| trades (a year) | 693 (87) | 817 (102) |
| gross / net; t net | +\$3.01 / −\$0.02; −0.01 | +\$3.97 / −\$1.96; −1.14 |
| median net; win rate; payoff | −\$1.03; 49.0%; 1.04 | −\$2.93; 48.0%; 0.96 |
| skew; excess kurtosis | +0.47; 6.2 | +0.50; 6.0 |
| trimmed: ex-top / ex-bottom / both | −\$2.19 / +\$1.78 / −\$0.38 | −\$4.00 / −\$0.28 / −\$2.32 |
| net Sharpe / Sortino (gross Sharpe) | −0.00 / −0.01 (0.56) | −0.40 / −0.57 (0.82) |
| max drawdown; total net | \$1,087; −\$16 | \$2,415; −\$1,598 |
| breakeven cost a round trip | \$3.01 | \$3.97 |
| profitable years; net without the best | 4 of 8; −\$1.31 | 2 of 8; −\$3.03 |
| EST / EDT net | +\$3.74 / −\$2.07 | +\$2.57 / −\$4.37 |
| \|x\| terciles, kept / skipped net | small −3.77 / −4.02; mid +2.71 / −2.09; large +0.83 / +0.31 | small −4.75 / −4.73; mid +0.61 / −4.28; large −1.82 / −1.13 |
| after the SHFE auction (2023-05-26) | 57 trades, −\$1.30 | 65, −\$3.39 |

- **The mid-|x| tercile is the only place kept beats skipped by much** (passive +\$2.71 against −\$2.09). It is one of
  three terciles, of one cell, of thirty, and is noted, not taken.
- **The component line:** daily ρ with the unfiltered D765 fade 0.62–0.65; with D775 0.01–0.03; with D777's MNQ book
  0.04. D755's other-lines file no longer exists. No ledger row: net Sharpe is at most 0.00.

## 5. What this decides

- **No 2024+ read is recommended.** Nothing in the grid clears its own null, let alone the family's.
- **The open's 09:30–10:00 path carries no usable information about the rest of the session's reversal,** for this
  fade: not whether it has turned, not whether it is still at its extreme, at any delay from 5 to 30 minutes.
  - This agrees with D765's shape (ρ to 10:15 +0.017).
  - It also agrees with D786: the pre-entry inputs that sort the fade at all do so at 0.04–0.06, which is not enough.
- **Waiting to enter is a small taker improvement** (+\$0.60 by 09:51). On the passive book it is not an improvement,
  because the missed reversals grow larger.
- **The China-open fade's in-sample stays where D770 left it:** positive gross (t 2.5 taker), negative net at micro
  cost on either book, and concentrated in Dec–Mar (itself a post hoc split of about 2.3 SE).
