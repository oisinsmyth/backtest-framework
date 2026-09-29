# D691 — STAGE 0 DESIGN: does implied volatility tell us how far ES and NQ will move, beyond what realised volatility and dealer gamma already say?

*2026-09-29.*
- *The principal:*
  - "Let go with more research Implied versus realised volatility as a size predictor";
  - on the pairing: the break of yesterday's range sets the direction, and this study decides only whether a size
    signal exists to pair with it;
  - "Yes write the Stage 0 pre-reg".
- *Numbered D691. The other session's branch `wt/after-d674` claimed 690 for its oracle filter (`cc7a69bc`), and
  this record was renumbered from 690 before its commit.*
- ***Committed alone, before its runner exists.***
- *A premise check: it admits nothing, trades nothing and reads no direction outcome.*

## 0. Where this comes from

**Confluences predict size, not direction.** When a break sets the direction, what a conditioner can add is the day's
|move|:
- D665: dealer gamma predicts the break's |follow-through| at t 8.7 and keeps t 5.9 beyond trailing volatility;
- D671: a realised-only size forecast (rv5, overnight range, |gap|, events, opex, SPX gamma) reaches an out-of-sample
  Spearman of 0.42 (NQ) and 0.46 (ES) with the day's range.

**The gap.** D671's forecast pointed the wrong way for the break: NQ's breaks paid on the days it called quiet (the
compression break, D672). Price history cannot tell a quiet day with nothing coming from a quiet day on which the
options market still prices a move. **Implied volatility can.** Nothing on the record has tested it: D404 "does not
reach implied volatility", and the deposit sweep lists it as untested.

**This stage asks only the premise:** does the prior close's at-the-money implied volatility carry information about
today's size that D671's forecast does not? If it does not, the line stops here. If it does, Stage 1 is a separate
pre-registration.

## 1. Objects (all known before the session opens)

**Implied volatility, IV_T.** From `fut_es_options_eod` / `fut_nq_options_eod`, the rows with `session == T`: each
option's settlement from the previous business day, usable on T (D497/D521).
- **The underlying F:** the settlement of the option's own `underlying` at the previous session, from
  `fut_settle_strip` (D581 and D688's convention).
- **Tenor:** the first expiry at least 2 sessions after T, expiring at 16:00 ET. This excludes same-day and next-day
  options, and the AM-settled quarterly on its expiry day. That expiry exists in every era: the Friday weeklies.
- **Time to expiry:** τ = (n + 1)/252, with n the number of CME ES trading days from T to the expiry (D688's calendar,
  which counts half days).
- **Rate:** 0 (Black-76, as D581 and A4).
- **The IV itself:** at the two strikes bracketing F, the mean of the call and put implied vols where both invert
  (`implied_vol`, `src/backtest_framework/opening/agents.py`, D581's bracket [0.01, 4.0]), linearly interpolated in
  strike to F. Annualised.
- A session with no bracketing pair is NaN, excluded, and counted.

**Realised volatility, RV20_T:** the standard deviation of daily close-to-close log returns over the 20 sessions
before T (D663's `sig20`), annualised by √252.

**The new feature:** `ivrv_T = ln(IV_T / RV20_T)`, the implied-to-realised ratio. `ln IV_T` alone is reported beside it.

**The size target (D671's):** `y_T = ln(R_T)`, with R_T = (RTH high − low)/ATR20 and ATR20 from the 20 prior sessions.
This target was read by D671; the feature was not.

**Secondary targets (reported):**
- |open → 15:59 close| / ATR20;
- D665's object: the |60-minute follow-through| after D662's break, on break days only.

## 2. The test (per root; ES and NQ; nothing pooled)

**M0 is D671's realised-only forecast, unchanged:**
- `size_forecast` in `scripts/stage0_d671_break_construction.py`;
- expanding window, walk-forward, BURN 250;
- standardised features times declared sign, `nnls` slopes, free intercept;
- SIZE_FEATS (g, on_range, rv5, abs_gap, event, opex).

**M1 is M0 plus `ivrv`, with declared sign +.** A higher implied-to-realised ratio means a larger day. Both are fitted
walk-forward on the same sessions.

**Window:** D671's evaluation window, 2018-01-09 → 2025-02-28 (about 1,780 sessions a root).
- **Seal:** ES rows on or after 2025-03-01 are dropped before anything is computed; NQ ends 2025-02-28.
- **SPX gamma:** read to < 2025-03-01, as in D663/D671 (SqueezeMetrics, credited; no per-date series is tracked).

**Gate S (the premise), per root:**
- **(a) Diebold–Mariano:** the out-of-sample loss differential d_T = e0_T² − e1_T² (M0's squared forecast error minus
  M1's). Mean > 0 with one-sided HAC t ≥ 2.0 (Newey–West, 5 lags); **Holm across ES and NQ.**
- **(b) Enumerated rotation:** `ivrv`'s series is rotated against the sessions by every offset from 21 to n − 21, and M1
  is refitted walk-forward each time. Mean d_T must exceed the rotation's exact p95. This is a time rotation of one
  series, so it is enumerable, and the p95's SE is 0 (CLAUDE.md).
- **(c)** Mean d_T > 0 without February–April 2020.

**Verdicts, per root:**

| verdict | condition |
|---|---|
| **SIZE INFORMATION CONFIRMED** | (a), (b) and (c) all pass |
| **NOT CONFIRMED** | otherwise |

- NOT CONFIRMED on both roots closes the implied-volatility line on ES and NQ.
- CONFIRMED on a root permits a Stage 1 pre-registration on that root, and nothing more.

**Reported only, never gating:**
- the out-of-sample Spearman of M0, of M1, of `ln IV` alone and of rv5 alone;
- M1's final slope on `ivrv`;
- d_T by year;
- d_T before and after 2022-05-16 (the daily-expiry era);
- the IV coverage;
- the secondary targets;
- M1 against M0 **without** g, to show whether implied volatility and dealer gamma carry the same information.

**Stage 0 reads NO break-trade P&L by IV tier.** The direction pairing is Stage 1's, and it must be declared before it
is read.

## 3. Data gates (before any outcome)

- **G1, coverage:** IV is defined on ≥ 95 % of the window's sessions per root. Missing sessions are listed by year.
- **G2, inversion:** D581's `audit_iv_roundtrip` (price → IV → price) on a sample of the selected options.
- **G3, point-in-time:** a second implementation re-derives IV_T for 30 sessions from option rows and strip settles
  dated strictly before T, without calling the first. It must match to 1e-10. A canary must fire on an IV built from
  T's own settles.
- **G4, seal:** the IV table holds no session ≥ 2025-03-01, asserted.
- **G5, sanity (reported):** the median IV by year (2020 must stand out), and IV against RV20's correlation.

## 4. The runner's assertions (each shown to raise in `--selftest` on a broken input)

- **the IV lag audit** (G3);
- **the forecast's lag** (D671's `forecast_audit`, which refits by date on a second path);
- **the sign audit:** on synthetic data where the target is built to rise with `ivrv`, M1's slope is positive and
  d > 0; on noise, d ≈ 0;
- **the right quantity:** the target is range / ATR20, not the close-to-close return, asserted against a deliberately
  swapped column;
- **the rotation's offset 0** reproduces the actual statistic exactly;
- **chunk == whole:** the rotation, fanned out over processes by `offsets[i::N]`, equals the serial run bit for bit.

## 5. Speed (designed in, per CLAUDE.md)

- The IV table is built once per root, vectorised over the day's selected options, and cached in `temp/`. The cache
  is keyed on the fixtures' and the strip's mtimes and this runner's.
- The rotation (about 1,740 offsets a root, one walk-forward refit each) fans out over processes, striding the offsets.
- **Projected wall time:** under 15 minutes on 12 processes. It is measured on the first 50 offsets and stated before
  the full launch.

## 6. Power (rough, stated before the run)

- About 1,780 out-of-sample sessions a root.
- **Why a large effect is plausible:** implied volatility is the market's own forecast of the variance ahead, and it
  carries scheduled information (events, expiries) and positioning that trailing ranges do not.
- **Why it may be small:** M0 already holds the event and opex flags, SPX gamma and two realised measures, so the
  incremental R² could be small.
- A Diebold–Mariano t of 2 needs d̄ at about 2 SE. At this n, that is roughly a 1–2 % reduction in out-of-sample MSE.

## 7. Predictions

1. **M1 beats M0 on ES:** Gate S passes. ES's options book is the deep one.
2. **The gain on NQ is smaller than on ES.** NQ's options OI is 2–5 % of ES's, so its IV is noisier.
3. **`ln IV` alone beats rv5 alone** in out-of-sample Spearman on both roots.
4. **M1's final slope on `ivrv` is positive** (non-zero under NNLS) on both roots.
5. **Implied volatility and dealer gamma overlap only partly:** M1's gain over M0 is larger when g is removed from both.

## 8. Routing

- **CONFIRMED on a root:** Stage 1 is pre-registered separately. It is the plain break (D668's E4, friction counted
  once, D668-A2) split by the declared "coiled" hypothesis: **breaks on days with a low realised range but a high
  implied-to-realised ratio carry; breaks with both low do not.**
  - It states its overlap with D680 (the NQ compression break, frozen in slot 9): a filter on NQ's break is a subset
    of the same signal, so on NQ it can only refine D680.
  - Its confirmation route is D680's vault look for NQ. ES has no unread index slice.
- **NOT CONFIRMED on both:** the line closes. FINDINGS records that implied volatility adds nothing to size beyond
  realised volatility and dealer gamma on these roots.
- **Deviations** are listed in the output and never replace a verdict.
