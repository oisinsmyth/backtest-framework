# D694 — STAGE 1 DESIGN: does the break of yesterday's range carry on "coiled" days, quiet in realised range but priced for a move by the options market? (ES and NQ; the follow-on to D691)

*2026-09-29.*
- *The principal: "Write the Stage 1 pre-reg", after [D691](D691-STAGE-0-RESULT-implied-vol-adds-size-beyond-realised.md)
  confirmed that implied volatility carries size information on both roots.*
- *Numbered D694: the highest number on every branch and in every commit subject is D693. The other session was told
  before writing.*
- ***Committed alone, before its runner exists.***
- *In-sample development on 2018-01-09 → 2025-02-28. The vault (2025-03-01 → 2026-09-18) is not read. Dealer gamma
  (GEX) is SqueezeMetrics', read to < 2025-03-01, credited, and never written per date.*

## 0. Where this comes from, and what is already known

**D691 (size only; no break P&L read):**
- ln(IV / RV20) at the prior close cuts the out-of-sample error of D671's size forecast by 10.7 % (ES) and 9.2 % (NQ).
- It works only relative to realised volatility. About a third (ES) to a half (NQ) of that is the RV20 denominator.
- Implied volatility adds 7.5 % / 5.1 % beyond it (post hoc).

**The trade, already read on this window:**
- **D668's plain break** (single-count friction, D668-A2, 2016-01 → 2025-02):
  - ES: gross at the level +2.71 bp, net −0.03;
  - NQ: +4.80 bp, net +2.48 (t 2.06).
- **D672's compression tier C1** (2018-01-09 → 2025-02-28, single count):
  - NQ: 387 trades, gross at the level +9.42 bp, net +7.56 (t 2.62), frozen as D680 in programme slot 9;
  - ES: 385 trades, net +2.78 (t 1.26).
- **This record reads nothing new about the trade. Only the IV label is new.** No record has split the break's P&L by
  implied volatility.

**The hypothesis, declared in D691 §8:** a quiet day that the options market still prices for a move is coiled, and
the break follows through on it. A quiet day that the options market also prices as quiet is not.

**What was measured before writing this (conditioner only):** session labels were counted
(`scripts/diag_d694_conditioner_count.py`, output `data/diag_d694_conditioner_count.json`). No trade, return or range
outcome was read.
- **The two labels are positively correlated:** corr(compression tier, IV/RV percentile) = 0.52 (ES), 0.47 (NQ). A
  plausible mechanism: when realised range has been quiet, IV has usually already fallen while RV20 lags, so the ratio
  is low.
- **The coiled cell is therefore the minority off-diagonal:** 147 (ES) and 173 (NQ) of 587 C1 sessions have an IV/RV
  percentile ≥ 1/2, and 76 and 88 have one ≥ 2/3. At D672's fill rate of about two breaks in three C1 sessions, the
  1/2 split gives **about 100 (ES) and 115 (NQ) coiled trades.** 2/3 would give about 50 (ES) and 58 (NQ), and is not
  used.

**A correction to D691 §8.** D691 said "ES has no unread index slice"; that had no basis.
- **ES's 2025-03-01 → 2026-09-18 window is sealed and unread for any break construction.** Its options fixture runs to
  2026-09-09.
- **Other lines read ES prices in that window, and those reads are disclosed as prior exposure:**
  - D562's trend book (to 2026-09-09);
  - D473 K7's overnight leg;
  - D485's micro-flow year;
  - D617's option flow (not return-bearing).
- NQ's options past 2025-02-28 are on disk (the approved pull of 2026-09-27), but no fixture is built.

## 1. Objects (all known before the session's first bar)

**The trade.** D668's E4 plain break, built as D680's runner builds it (the same functions, with each root's own
tick and cost):
- **Entry:** a stop at the prior RTH high + 0.25·ATR20 or low − 0.25·ATR20, live from 09:30. The first to fill is the
  day's only trade, with no entry after 15:29.
- **Exit:** an initial stop at the broken level, trailing 0.25·ATR20 behind the best price and never loosening; else
  flat at the 15:59 close.
- **Size and cost:** one MES / MNQ, scored at the level with friction charged once (D668-A2): **$4.418 (MES), $4.067
  (MNQ)** a round trip, in bp at the level price.

**The realised label R:** D672's compression tier, unchanged.
- `ctier = tiers((tiers(rv5) + tiers(on_range)) / 2)`, walk-forward over the previous 250 sessions.
- **C1 = ctier < 1/3.**

**The implied label V:** `p_iv = tiers(ivrv)`, walk-forward over the previous 250 finite values.
- `ivrv = ln(IV / RV20)`, exactly as D691 builds it: the same functions and the same cached, gated IV table. G1–G4
  passed in D691.

**The cells (per root):**

| cell | definition | role |
|---|---|---|
| **COILED** | C1 and p_iv ≥ 1/2 | **the object** |
| QUIET | C1 and p_iv < 1/2 | the comparison |
| B0 | every break | reported |

**The window:** sessions from 2018-01-09 to 2025-02-28 on which ctier, p_iv and D691's M1 forecast are all finite.
It is D672's window, less the sessions with no IV (NQ loses about 2 %).

**The size predictor for the filter (§2, Gate 2):**
- `P_T = exp(f1_T) · ATR20_T / prior_close_T · 1e4` bp, the day's projected range. f1 is D691's walk-forward M1
  forecast of ln(range/ATR20).

## 2. The test (per root, ES and NQ, nothing pooled)

**The principal's template (D666, "it should pass the gross bar not net"):** the unfiltered cell must show the
mechanism before costs, and the filtered cell must then clear net.

**Gate 1, the mechanism (COILED, gross at the level):**
- **(a) Edge:** mean gross > 0, one-sided Newey–West (5 lags) HAC t, **Holm across ES and NQ, p < 0.05.**
- **(b) The ingredient null: implied volatility, not what realised volatility already implies.**
  - Regress ln IV on the realised measures the labels are built from, by OLS over the window. The regressors are
    ln RV20, rv5, on_range and ln(ATR20 / prior_close). The regression serves only to build the null.
  - Rotate the residual u by every offset from 21 to n − 21, with the fitted part held fixed. Rebuild ln IV, ivrv and
    p_iv from it.
  - For each offset, take the k C1 trades with the highest rotated p_iv, where k is the actual COILED count. Ties go
    to the earlier session.
  - COILED's mean gross must exceed the **exact p95** of this enumerated distribution. The SE of that p95 is 0
    (CLAUDE.md).
  - The actual statistic under the same top-k rule is COILED itself, and the runner asserts that.
  - The null is **count-matched** by construction, and it keeps IV's correlation with realised volatility (memory:
    rotating a correlated regressor on its own is anti-conservative).
- **(c) The comparison:** COILED's mean gross > QUIET's mean gross. The sign gates; the Welch t is reported.
- **(d) Not one episode:** mean gross > 0 without February–April 2020.

**Gate 2, tradeability (only on a root that passes Gate 1):** the expected-profit filter on COILED trades.
- Take a trade when π̂ · P_T ≥ 2 × its cost in bp.
- π̂ is the mean of gross / P over **all earlier plain-break trades of the root** (B0, from 2016, with finite P), after a
  burn-in of 40. Using B0 rather than earlier COILED trades is declared here for power: COILED alone would spend 40 of
  its ~110 trades on burn-in.
- Pass: at least 30 filtered trades; filtered mean net > 0 with Holm p < 0.05 across roots; positive without Feb–Apr
  2020.

**Verdicts, per root:**

| verdict | condition |
|---|---|
| **SUPPORTED** | Gate 1 (all four) and Gate 2 |
| **MECHANISM ONLY** | Gate 1 only |
| **NOT SUPPORTED** | otherwise |
| **UNRESOLVED** | COILED has fewer than 60 trades on the root |

**Reported, never gating:**
- **The four groups for COILED, unfiltered and filtered:**
  1. gross and net side by side; Sharpe and Sortino together (per trade, annualised by the cell's own trade count,
     and daily over the window); exposure; vol; max drawdown; mean move per trade against 2c; breakeven cost in bp
     and $.
  2. count, mean, median, win rate, payoff, holding time, skew and kurtosis, plus the three 1 % trimmed means.
  3. the top trades named; top-1/5/10 share; profitable years; long against short; before and after 2022-05-16.
  4. every null's p50 and p95 beside the score.
- **The component line** (CLAUDE.md):
  - net Sharpe at one micro and its $ cost;
  - hit rate, skew, and gross beside net;
  - ρ with every ledger entry: the MACD arm (entry #2, the only admitted one);
  - **on NQ, ρ with D680's C1 daily series.** COILED is a gated subset of C1: it shares its clock and signal, so it
    refines C1 rather than diversifying it.
- **The 3 × 2 grid** (ctier terciles × p_iv halves): n, gross and net in every cell.
- **B0 split by p_iv halves**, on all breaks.
- **The realised-only label**, C1 with tiers(−ln RV20) ≥ 1/2: the denominator's own cell, to show what IV adds.
- **The secondary null:** D691's rotation of ivrv as a whole, through the same top-k rule.
- **The manipulation check:** mean ln(range/ATR20) on COILED sessions against QUIET, to confirm the label does inside
  C1 what D691 says it does overall. This is a size statistic D691 already read, not P&L.
- **The drift control:** always-long open → 15:59 on COILED sessions, and COILED's long trades against its short
  ones.
- d by year.

## 3. The runner's assertions (each shown to raise in `--selftest` on a broken input)

- **Known answers:**
  - D672's C1 is reproduced on NQ: 387 trades, at-level gross +9.42, single-count net +7.56.
  - D672's C1 is reproduced on ES: 385 trades, single-count net +2.78.
  - D691's d̄ is reproduced from the same IV table, which fixes the feature's identity.
- **Lag:**
  - D691's IV lag audit and its canary;
  - `tier_audit` on ctier and p_iv;
  - D671's `forecast_audit` on f1 before P is used;
  - π̂ is built only from trades with earlier sessions, checked by a second, date-keyed implementation.
- **Sign, in money:** on a synthetic day, a long break into a rising path pays positively and a short break pays the
  same amount negatively.
- **Right quantity:**
  - the gross is at the level, not with the fill tick. The assertion compares both and requires them to differ by the
    tick drag;
  - the cost is the single count, not D668's double count.
- **The null:**
  - offset 0 reproduces COILED's actual mean exactly;
  - the top-k rule at offset 0 returns exactly the COILED set;
  - chunk == whole across processes, bit for bit.

## 4. Speed (designed in)

- Frames, trades and the IV table are built once and cached in `temp/`, keyed on the fixtures' and every imported
  module's mtimes.
- The rotation is about 2,250 offsets a root. Each is a re-tier and a top-k over C1's trades, with no refit. It fans
  out over processes on `offsets[i::N]`.
- **Projected:** under 15 minutes in all, measured on a few offsets and stated before launch.

## 5. Power (stated before the run)

| | ES | NQ |
|---|---:|---:|
| expected COILED trades | ~100 | ~115 |
| per-trade gross SD (from D668 / D672) | ~35 bp | ~74 bp |
| SE of the mean | ~3.5 bp | ~6.9 bp |
| 80 %-power minimum detectable mean (one-sided 5 %) | **~9 bp** | **~17 bp** |

- **For comparison:** C1's whole-tier gross is +9.4 bp on NQ (at the level) and +3.6 on ES (with the fill tick; its
  at-level figure is not on the record).
- **Gate 1(a) finds only a large IV effect.** NQ's coiled breaks would need to earn nearly twice C1's average, and ES's
  more than twice.
- **A NOT SUPPORTED verdict therefore does not exclude a modest effect.** The RESULT reports the 95 % upper bound on
  COILED's mean and on COILED − QUIET.

**The vault cannot confirm a pass with useful power.**
- 2025-03-01 → 2026-09-18 is about 385 sessions. At the in-sample rates, that is about 130 C1 sessions and **about 23
  coiled trades a root.** The SE of a 23-trade mean is about 15 bp on NQ and 7 bp on ES.
- **That power is computed and stated before any vault slot is asked for** (memory: compute the holdout's power before
  spending it).

## 6. Predictions

1. **The manipulation check holds on both roots:** COILED sessions have a larger mean ln(range/ATR20) than QUIET
   sessions.
2. **On NQ, COILED's mean gross exceeds QUIET's.** This is the hypothesis.
3. **ES fails Gate 1(a).** ES's whole C1 tier earns about +3.6 bp gross, so its coiled quarter would need well over
   twice that to reach the ~9 bp it takes.
4. **No root passes Gate 2.** At ~110 trades the filter has too little to work with.
5. **On NQ, COILED clears the ingredient null's p95 (Gate 1b).**

## 7. Routing

**SUPPORTED on a root does not queue it for the joint vault by itself.** First:
1. **The vault power is computed** from the in-sample effect and the vault's expected coiled count (§5). A PASS
   probability under 0.5 at the full in-sample effect routes the line to **forward recording** (Track 2, from
   2026-09-19), not to a vault slot.
2. **The prerequisites are stated and are not built:**
   - the vault-input bar path for ES and NQ (D644's fixture past the cut; AITODO);
   - an NQ options fixture past 2025-02-28 from the raw pull on disk;
   - ES's options end on 2026-09-09, so the vault's last sessions have no label;
   - a free programme slot (7 or 10);
   - the principal's word.
3. **On NQ, a vault family would be a second look at a subset of D680's trades.** It is disclosed as such and needs its
   own slot.

**Other verdicts:**
- **MECHANISM ONLY:** a scored-not-entered row in `COMPONENTS_PROP.md`, and no vault.
- **NOT SUPPORTED on both roots:** the implied-volatility line closes for the break on ES and NQ. FINDINGS §99 gains
  the sentence: "IV predicts the day's size but does not select the break's trades."
- **Deviations** are listed in the output and never replace a verdict.
