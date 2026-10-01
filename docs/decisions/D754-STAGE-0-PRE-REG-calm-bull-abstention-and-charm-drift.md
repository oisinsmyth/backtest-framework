# D754 STAGE 0 PRE-REG — the calm bull: (A) do the NQ lines lose in calm markets within each year, or is it 2017? (B) does MES drift up on long-gamma Friday afternoons?

*2026-10-02. The principal: "What type of regime is the largest untraded from the vault coverage?"; "Have two fable
agents find calm bull strategy ideas one online and one by reasoning, then you reason while you wait"; "Pre-reg D754
and run both".*
- **The source:** a post hoc split of the three NQ vault lines' in-sample books (this session, 2026-10-01).
  - The "calm bull" (NQ 20-day realised volatility in its lowest third, S&P above its 200-day average, SqueezeMetrics
    SPX GEX long and above its 250-day median) held 25% of sessions.
  - The book made −\$3.44 a day there, against +\$28.31 a day elsewhere.
  - That three-variable label was chosen after looking, so Part A uses ONE variable, as the Fable agent advised.
- **Part B** is the reasoning agent's idea #5, which the online agent's evidence on dealer gamma supports in kind.
- **What it is:** a diagnostic (A) and a premise check (B). Neither changes a frozen line. A feeds the post-vault
  state-based allocation item; B, if it reads, goes to a design conversation with the principal.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the result
  separately.
- **The seal:** in-sample only. Every fixture and `DIX.csv` is restricted as text to rows before 2024-01-01, and no
  vault-window or 2024+ row is parsed.

## Part A — the calm-state abstention diagnostic

- **The books:** the daily net of D737's in-sample twin (D735 YM k1.0 1σ_rem), NQ F2 (D711's book) and C1 (D680's
  `book()`), one MNQ each, 2016-02 → 2023-12, from the same functions as D746, D747 and D749. Also their sum, the
  book.
- **The single variable:** rv20 = the standard deviation of NQ's 20 prior daily log returns (RTH close to close),
  known before the session.
- **The calm gate (walk-forward, causal):** a session is CALM when rv20's percentile among the previous 250 sessions'
  rv20 is < 1/3. Sessions without 250 prior values are not scored.
- **A1, the level:** the book's mean net on calm sessions and on the rest, per line and summed.
- **A2, within year (the decisive test, D740's lesson):**
  - Inside each calendar year, rank the scored sessions by rv20 and label the bottom third WY-CALM.
  - The statistic is the pooled within-year contrast Δ = mean(book net | rest) − mean(book net | WY-CALM), with year
    as a stratum (each year's contrast weighted by its sessions).
  - **The null:** the WY-CALM label permuted within each year, 20,000 draws, seed 754.
  - Reported: the per-year contrasts and the count of years with Δ > 0.
- **The reading:**
  - **ABSTAIN SUPPORTED:** A1's calm mean net ≤ \$0 for the book, **and** A2's Δ > 0 with a permutation p ≤ 0.05,
    **and** Δ > 0 in ≥ 5 of the scored years.
  - **YEAR ARTEFACT:** A1 holds, but A2 fails. Calm loses only because calm years (2017) lose.
  - **NOT SUPPORTED:** A1 fails.
- **Reported, and never part of the reading:** the same three tests per line, and the three-variable label.
- **This is not an admission or a gate on any frozen line.** A support moves the question to the state-based
  allocation item, to be confirmed on forward data.

## Part B — the long-gamma Friday-afternoon charm drift on MES

- **The mechanism (the reasoning agent's):**
  - Dealers are long puts that institutions bought as hedges, and hedge them with short futures.
  - As those puts decay into a Friday expiry, the hedge is bought back in the afternoon.
  - It should be strongest when dealers are long gamma and the market is calm and rising.
- **The data:** ES day session, one-minute bars (`fut_ES_rth_1m`), 2016-01-04 → 2023-12-29.
  - SPX GEX: the row strictly before the session (D663's `gex_prior`). The S&P level from `DIX.csv`'s price, at the
    prior close.
- **The state (primary):** GEX ≥ 0 and ≥ its 250-row median, and the S&P above its 200-day average (both at the prior
  close).
- **The trade:** long one MES from 14:00 (the close of the 13:59 bar) to 16:00 (the close of the 15:59 bar), on every
  Friday session in the state. One MES at \$4.42; the prize bar is 2c = \$8.84.
- **The controls:**
  - **B-C1, the day control:** the same window, state and side on Monday–Thursday. The drift must be
    Friday-specific: Friday − Mon–Thu, Welch t.
  - **B-C2, the clock control:** the same Fridays, 12:00 → 14:00. The mechanism names the afternoon.
  - **B-C3, the state control:** the same Friday window outside the state (the mechanism says the drift is weaker
    there).
- **Reported:**
  - the monthly-expiry Fridays (third Friday) against the other Fridays;
  - the pre-0DTE era (to 2022-05-10) against the 0DTE era (from 2022-05-11, when SPX options listed every weekday);
  - long against an always-long drift.
- **The reading:**
  - **DRIFT PRESENT:** the state's Friday mean gross > 0 at t ≥ 2 (Fridays are about independent; plain t), **and**
    Friday − Mon–Thu > 0 with Welch t ≥ 1.64, **and** the Friday afternoon above the Friday 12:00–14:00 window.
  - **GO to a design with the principal:** DRIFT PRESENT, and also:
    - mean net > 0 at one MES;
    - ≥ 5 of 8 years positive, and the largest year < 50% of the total;
    - the 0DTE era's mean gross > 0.
  - **NO ROOM:** the state's Friday mean |move| < \$8.84 (no sign rule could pay).
  - **NOTHING:** otherwise.

## Reported for both (all four groups where a trade exists)

- gross and net; Sharpe and Sortino (annualised by the trade count); max drawdown;
- the mean move against 2c, and the breakeven cost;
- count, mean, median, win rate, payoff, skew, kurtosis, and the symmetric trims;
- the years, and the nulls' p50 and p95.
- **The component line for B:** net Sharpe, hit rate, skew, gross beside net, and the daily ρ with the three NQ lines.

## Runner assertions

- **Lag:**
  - rv20 and its walk-forward percentile use only prior sessions, and a canary including the session's own return
    must change some labels;
  - GEX and the S&P are the rows strictly before the session, re-derived by a loop on a sample.
- **Sign, in money:** a synthetic rise pays the long MES.
- **Right quantity:**
  - the within-year label differs from the walk-forward one;
  - the Friday set and the Mon–Thu set do not overlap;
  - the 12:00 → 14:00 window ends where the trade starts.
- **The permutation null in A2** keeps each year's label count, so a canary that pools years must give a different
  null.

## Output

`scripts/stage0_d754_calm_bull.py` and `data/stage0_d754_calm_bull.json` (statistics only; no per-date GEX). The
result is a separate record.
