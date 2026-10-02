# D770 STAGE 0 PRE-REG — gold's China-open fade with real order flow and a passive entry: does aggressive one-sided flow mark the opens that reverse, and can a resting MGC order collect the reversal without paying the spread?

*2026-10-02. The principal:*
- *"Order flow?";*
- *"get a size-and-price quote now";*
- *"we only download the full sizes and only the data we need around the china open? Then we estimate the Micro from the full?";*
- *"Ok go for the \$98 one";*
- *"Draft D770, pre-reg it, build and run it".*

- **What it is:** a Stage 0 premise check on one base construction, gold's China-open fade (D765/D767). It admits
  nothing.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the
  result separately.
- **The prop book's rules:** one MGC, flat before 16:10 ET (exits at 02:00/03:00 ET), fully algorithmic, one position.

## 0. What is known, and what this test cannot claim

- **D765:** the opening half-hour after 09:00 Beijing reverses on gold.
  - ρ −0.063 (p 0.007); the fade grosses +\$3.14 a trade on every session (t 2.49).
  - That is below the \$5.93 micro round trip, and the sign was read in-sample.
- **D767:** a confirmation filter (the AUD and the other metals) had NEGATIVE accuracy. The oracle's winners sit
  evenly across months and years.
- **The partial-oracle curve (gold, keep the top third):** break-even needs ρ ≈ 0.05, and net t ≈ 2 needs ρ ≈ 0.13.
- **The data** (`data/raw/databento/china_window_2016_2023/`, PAID, read-only; manifest
  `data/china_window_tbbo_manifest.csv`):
  - **GC `tbbo`** (every trade with its aggressor side, `B` = buyer-initiated / `A` = seller-initiated, and the best
    bid and ask before it) and **GC `bbo-1m`** (the best bid and ask at each minute boundary):
    - 2016-01-04 → 2023-12-29;
    - 18:30 ET (the evening before) → 03:15 ET.
  - **MGC `tbbo` + `bbo-1m`** for 2022-01-03 → 2023-12-29, the calibration sample.
- **What this test cannot claim:** everything is in-sample (2016–2023), and the fade's sign came from D765. A pass
  earns only a confirmation on unseen data (the joint vault or the forward recorder, on the principal's word).
- **Fills are modelled from prints, not queue position.**
  - The conservative rule credits a resting order only when the market trades THROUGH its price.
  - A queue-position model is not possible from L1 data. The touch rule (filled when the market trades AT the price)
    is the optimistic bound.

## 1. The candidates and the base trade (unchanged from D765)

- **The candidates:** D765's MGC-eligible sessions (2016-01-04 → 2023-12-29; China's holidays, the roll week, missing
  prices, isolated prints and two-contract sessions excluded), with x ≠ 0.
- **A session is also dropped (and counted)** when the GC `tbbo` file has more than one instrument in the window, or
  its last trade before 09:30 Beijing differs from D765's bar price P(09:30) by more than 2 ticks (a contract
  mismatch).
- **x** = P(09:30) − P(09:00) Beijing (D765's bars). **The fade's side** = −sign(x).

## 2. Q1, reported: the real cost of a taker round trip at the China open

- **On GC quotes, every candidate session:**
  - entry at the touch at 09:31 Beijing (selling at the bid, or buying at the ask);
  - exit at the touch at 15:00 Beijing (the latest `bbo-1m` record stamped at or before the time, within 3 minutes);
  - crossing cost = (ask − bid) at entry + (ask − bid) at exit, in ticks.
- **The same on MGC quotes, 2022–2023.**
- **Reported:** the mean and median quoted half-spread at 09:31 and at 15:00 for GC and MGC, and MGC − GC in ticks.
  This replaces the cost file's 2.93 crossing ticks with a measurement at this clock.

## 3. Q2: the real-flow filter (a taker fade, the cost model's \$5.93)

- **The flow over x's window:** B = Σ size of `B` trades and S = Σ size of `A` trades on GC in [09:00, 09:30)
  Beijing (`N` trades are ignored).
- **The score:** A = sign(x) · (B − S) / (B + S), in [−1, 1].
  - High A: the move was pushed by aggressive orders in its own direction, which is a demand for liquidity.
  - Low or negative A: the price moved on little or opposing aggressive flow, which is quotes repricing.
- **The mechanism (Campbell, Grossman and Wang 1993):** price pressure from liquidity demand reverses, and
  repricing does not. **The predicted sign:** ρ(A, the fade's gross) > 0.
- **The selection:** A's walk-forward top third (the 2/3 quantile of the prior 250 candidates' finite A, at least 100,
  strictly prior; D767's function).
- **The gates** (as D767):
  - **G1:** the unfiltered fade's mean gross > 0 at t ≥ 2;
  - **N:** the selected book's mean net above the p95 of the exact rotation of A against the candidates;
  - **B1:** the month shares within 5 points of the pool's;
  - **B2:** net > 0 outside December–March;
  - **G2:** mean net > 0, t ≥ 2, Holm (over Q2 and Q3) below 0.05, and net > 0 without its best two years.
- **The readings:** NO MECHANISM / NOT ABOVE NULL / UNBALANCED / MECHANISM ONLY / SUPPORTED.
- **Reported:**
  - the Spearman of A with gross (the partial-oracle curve);
  - the AUC against the oracle label;
  - an impact variant (|x| per unit |B − S|);
  - A's month and year shares.

## 4. Q3: the passive fade (liquidity provision, every candidate session)

- **The order:** at 09:30 Beijing (x known), rest a limit order on the fade's side.
  - When x > 0: SELL at the best ask (GC `bbo-1m` at 09:30, the ask).
  - When x < 0: BUY at the best bid.
- **The fill (conservative, the primary):**
  - filled at the limit price at the first GC trade in [09:30, 10:00) Beijing priced THROUGH the limit by at least
    one tick (≥ ask + 0.1 for a sell, ≤ bid − 0.1 for a buy);
  - otherwise unfilled, and no trade that session.
- **The exit:** at 15:00 Beijing at the touch (a short buys at the ask, a long sells at the bid; GC `bbo-1m`).
- **The cost:** the gross is explicit in quotes, so the cost is the micro's commission alone, \$3.00 a round trip.
  - An MGC adjustment (below) adds the micro's extra half-spread at the exit.
  - gross = side × (exit − entry) × 10; net = gross − \$3.00 − the MGC adjustment.
- **Also reported:**
  - the touch fill (filled at the first trade AT the limit), the optimistic bound;
  - the fill rate;
  - **adverse selection:** the taker fade's gross on the filled sessions against the unfilled ones;
  - a 10-minute order life;
  - the passive book with A's top third (Q2's filter);
  - the "cross at 10:00 if unfilled" variant.
- **N:**
  - every session's outcome is computed for BOTH sides (a passive sell and a passive buy);
  - the fade picks side −sign(x);
  - the exact rotation reassigns side −sign(x_{i+k}) to session i for every k = 1 … n − 1, using each session's
    precomputed outcome for that side;
  - **the passive fade must beat the rotation's p95 mean net.** This asks whether the fade's direction earns, beyond
    passive mechanics and spread capture.
- **The MGC calibration (2022–2023, every candidate session there):**
  - **Fill agreement:** the share of sessions whose GC trade-through fill decision equals the MGC decision (the MGC
    rule uses MGC's own quotes and trades).
  - **The exit spread:** mean (MGC half-spread − GC half-spread) at 15:00 in dollars at one MGC. This is the MGC
    adjustment applied to every year.
  - **The MGC book itself** (MGC quotes and trades, 2022–2023) is reported beside the GC-proxy book for the same
    sessions.
- **Q3's gates:**
  - **N:** the passive fade's mean net above the rotation p95;
  - **B1 / B2** as in Q2;
  - **C:** fill agreement ≥ 85% and the MGC book's mean net within 2 SE of the GC proxy's on 2022–2023;
  - **G2:** mean net > 0 at t ≥ 2, Holm (over Q2 and Q3) below 0.05, and net > 0 without its best two years.
- **The readings, in order:**

  | reading | condition |
  |---|---|
  | **NOT ABOVE NULL** | N fails |
  | **UNBALANCED** | B1 or B2 fails |
  | **CALIBRATION FAILS** | C fails (the micro does not behave as the full-size proxy says) |
  | **NO PRIZE** | G2 fails |
  | **SUPPORTED** | all pass |

## 5. GO, priors, reporting

- **GO = SUPPORTED on Q2 or Q3.** It starts a confirmation conversation (the vault or the forward recorder). It
  admits nothing.
- **The priors:** Q2 SUPPORTED about 5%; Q3 SUPPORTED about 8%. Adverse selection is the expected failure: a resting
  fade fills when the move continues.
- **All four groups for each traded book:**
  - **Performance:** gross and net, Sharpe and Sortino, maximum drawdown, the mean |move| against the cost, and the
    breakeven cost.
  - **Trade distribution:** count, mean, median, win rate, payoff, skew, kurtosis, the symmetric 1% trims, and the
    five largest trades named.
  - **What the winners depend on:** years, months, EDT against EST, long against short, and the 2020
    night-suspension sub-era.
  - **Nulls:** p50, p95 and the rank.
- **The component line:** net Sharpe, Sortino, hit rate, skew, gross beside net, and the daily ρ with D737's twin,
  NQ F2 and C1.

## 6. Runner assertions

- **Lag:**
  - the flow window ends strictly before 09:30, and the order rests from 09:30;
  - quotes are read at or before their time;
  - a second implementation (explicit loops over the raw records) re-derives B, S, the 09:30 quotes and the fill
    decision on 40 sampled sessions;
  - D767's flag audit re-derives every selection flag.
- **Sign, in money:**
  - a filled passive sell followed by a fall pays;
  - `B` trades add to B;
  - a mirrored book raises.
- **Right quantity:**
  - the trade-through fill is a subset of the touch fill;
  - the passive book differs from the taker book;
  - rotation offset 0 equals the observed;
  - no record on or after 2024-01-01;
  - one instrument per session file;
  - sessions read = used + each exclusion.
- **The self-test:**
  - a synthetic session where the price trades through a resting sell fills at the limit, and one that only touches
    does not (under the primary rule);
  - chunk = whole for the rotations on processes.

## 7. Output

- `scripts/stage0_d770_china_open_flow_passive.py`;
- `data/stage0_d770_china_open_flow_passive.json` (statistics only).
- It reads D765's extraction cache (`temp/d765/`) and the paid window (read-only, never modified).
- The result is a separate record.
