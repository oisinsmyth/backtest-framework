# D645 — PRE-REG: the opening agent-state model's stages and tests, Phases 3–5 (S-A → S-I, H-O1 … H-O6, Gate O1)

*2026-09-28. The principal: "Write it. I would still like the Testable at t = 2 tested." Committed ALONE, before any
runner exists (R8). Spec: `OPENING_AGENT_STATE_PREREG.md` v1.1 (read-only), with OA-A1 … OA-A7, the ruling that O-D4
stands, D644 (Gate O0, labels) and POWER (`b6f8f29`). **No model has been fitted and no mean return read:** Phases
1–2 and POWER read labels, pressures and the dispersion of the raw move only. Where this record and the deposit
differ, the deposit wins unless an amendment says otherwise.*

## 1. The object

- **Days:** D644's usable sessions, 2016-01-04 → 2025-02-28, excluding its logged exclusions and d0 = 0 days (§5.2).
  ES and NQ are pooled, with shared coefficients and a market intercept (§7.1).
- **States:** CONT, FADE and RANGE. REV is merged into RANGE (O-D4, D644; the principal kept the rule). RANGE is the
  base class.
- **Checkpoints:** t ∈ {09:45, 10:00, 10:30, 11:00}. The trading t0 are 09:45 and 10:00 (§6.1).
- **Labels** are per (session, t0), relative to d0(t0) (OA-A6.6), and are targets only.

## 2. Features (§7.2), all direction-relative (× d0 where signed)

**Observables (S-A, five),** each computed from bars up to the checkpoint's close:
1. `gap × d0 / ATR20`;
2. `loc_with`: 1 if the open is beyond the prior RTH extreme in d0's direction (above the prior high when d0 = +1,
   below the prior low when d0 = −1), else 0;
3. `loc_against`: 1 if it is beyond the extreme against d0, else 0;
4. `|r(09:30 → t)| / σ`, where σ is the standard deviation of the same window's return over prior sessions
   (OA-A7.3's window);
5. the z-score of log volume 09:30 → t against the same window over prior sessions (OA-A7.3's window).

**Agent stages add, in the deposit's order (§8):**

| stage | adds | note |
|---|---|---|
| S-B | A7 | the large-lot signed volume 09:30 → t over total volume, × d0 |
| S-C | z1 × d0 | |
| S-D | z2 × d0 | |
| S-E | z3 × d0 | |
| S-F | z5 × d0 | used as computed, including its release-day extremes, unless an amendment before S-F says otherwise |
| S-G | z6 × d0 | |
| S-H | z4 × d0 | only if O0-H passes for both markets; replaces one feature or waits for S-I, as §8 says |
| S-I | observables + A7 + N + D | the alignment summary (§4) over the retained agents |

- **A7 enters only after it passes its check.** Sierra Chart's signed flow must agree with the exchange flag on
  post-vault ES/NQ sessions at day-level r ≥ 0.8, the principal's bar for the ledger (OA-A3).
  - **If A7 fails, S-B is dropped.** The sequence runs S-A → S-C …, and S-I is the observables + N + D.
  - **Order:** Phase 3 (S-A) runs now. Phase 4 starts with S-B once A7 is resolved either way, so the deposit's
    order holds.
- **The budget (§7.3):** at most 11 features in any stage. The pipeline refuses more (deposit test 13).

## 3. The classifier and the walk-forward (§7.1, §11)

- **Model:** multinomial logistic regression, L2, with a market dummy.
- **Features:** standardised on each training window's own mean and standard deviation.
- **Walk-forward:** train on 252 sessions, test on the next 63, rolling by 63, over the union calendar of usable
  sessions. Both markets' rows of a session always fall in the same window.
- **The penalty** C ∈ {0.001, 0.01, 0.1, 1, 10} is chosen **inside each training window only**:
  - 5 contiguous blocks, no shuffling;
  - the lowest mean validation log loss wins;
  - ties go to the smaller C.
- **Base rate:** each training window's class frequencies per market, applied to its test window.
- **One model per (checkpoint t, label t0), for t ≥ t0:**
  - t = t0 gives H-O1, H-O2 and H-O4;
  - t > t0 gives the state-flip exit's probability at later checkpoints;
  - H-O3 uses t = t0 at each of the four checkpoints, with labels relative to d0(t).

## 4. The tests

**H-O1: classification lift, at t0 = 10:00, out of sample.** Pass on all three:
- the OOS log loss is below the base-rate log loss;
- the OOS accuracy is above the base-rate accuracy;
- the permutation p < 0.05: 1,000 shuffles of the OOS labels within market × year against the fixed predictions,
  seed 645, p = the share of shuffled accuracies ≥ the observed one.

Reported with it: the reliability curve (10 bins), the Brier score, and the calibration flag (the top bin's
predicted ≥ 0.6 against realised < 0.45).

**H-O3: progression (diagnostic).** At each checkpoint:
- OOS accuracy, log loss and the confusion matrix;
- how often the argmax state changes between consecutive checkpoints.

**H-O2: decision value, the core; at t0 = 09:45 and 10:00.**
- **The policy (§6.2, with REV merged):**
  - no trade if the argmax is RANGE or max p < θ = 0.45;
  - CONT trades d0;
  - FADE trades −sign(gap).
- **Execution (§6.3):**
  - the entry is the close of bar t0+1;
  - the stop is 0.5 × the 09:30 → t0 range from the entry, and a bar that touches both the stop and a later exit
    records the stop;
  - the state-flip exit: at each later checkpoint inside the hold, if the (t, t0) model's probability of the traded
    state is < 0.30, exit at that checkpoint's close;
  - the time stop is 60 minutes after the entry;
  - one trade per market per day, at 1 micro.
- **Cost (OA-A5):** D508's crossing + $3 + one adverse tick, charged per round trip in bp of the entry. The tick is
  in the cost, not added to the price.
- **Baselines (§6.4),** with the same stop and time stop:
  - B1 always trades d0 at t0;
  - B2 always trades −d0;
  - B3 enters at the close of the bar after the first bar (after t0, before 11:30) whose close is outside the
    09:30 → t0 range, in the break's direction.
- **The statistic:**
  - per session, the mean over the two markets of (policy net − baseline net) in bp, with 0 for a no-trade day on
    either side;
  - the baseline is **the one of B1–B3 with the highest OOS net mean at that t0**, the strongest simple comparator;
    all three are reported.
  - Newey-West HAC t, lag 5.
- **Pass (the deposit's within-doc test, run as the principal asked):** the difference is positive with t ≥ 2 after
  **Holm across the two t0**, **and** the policy's own OOS net mean is > 0.
- **POWER's labels travel with the verdict:**
  - testable at t = 2 (MDE 1.84 bp against a 2.79 bp cost);
  - **underpowered at the programme's α = 0.005 with 80% power** (MDE 3.35 bp);
  - per traded day, underpowered against the cost (MDE 3.10 bp).
  - A pass at t = 2 that misses the programme bar (12A.2, p ≤ 0.005) is reported as **"passes within the document;
    does not reach the programme's promotion bar"**, and not promoted.

**H-O4: timing, for each traded state at each t0.**
- The curve is the mean cumulative move in the trade's direction from the t0 close over k = 0 … 60 minutes, with a
  day-block-bootstrap 95% band (9,999 resamples, seed 645).
- **Pass:** at most 50% of the 60-minute move is realised by t0+5.
- The delay cost is reported. A fail is §14's "kill at current latency".

**H-O5: placebos.**
- **Label shuffle:** in H-O1.
- **Agent shuffle,** for each retained agent stage: the stage is refitted with its agent columns reassigned across
  sessions within year (seed 645). **It must lose its log-loss improvement.** Otherwise §14: revert to S-A/S-B.
- **The midday placebo (reported, not gating):**
  - the S-A observables with 12:00 as the open and 12:30 as t0 (the gap from the prior close to 12:00; the location
    against the prior RTH range; r and volume 12:00 → 12:30);
  - against §5.3's rules on 12:00 → 16:00, with IB = 12:00 → 13:00 and d0 = sign(price at 12:30 − 12:00);
  - its H-O1 metrics are reported.

**H-O6: agent signatures (validation, marginal).**
- **The regression:** OLS of the raw session return r(09:31 → 10:30), not direction-relative, on all computable
  z_i jointly, with HAC t (lag 5) and VIFs.
- **The predicted signs are all positive,** because every pressure is signed as buying: z1, z2, z3, z4 (−G × move),
  z5 and z6 (−basis).
- **A1's second half:** z1 on r(10:30 → 11:30), predicted negative.
- A7, once admitted, on the signed flow 09:30 → 10:30, predicted positive for z2 (§9's example).
- Holm across the agents is reported beside the unadjusted t.

**Robustness (report only, §9):**
- θ ∈ {0.40, 0.50};
- the stress fill (the worst close of t0+1 … t0+5 for the trade);
- 2× cost;
- with and without flagged days (FOMC, CPI, payrolls, quad witching, month-end, index rebalance, from D589);
- ES and NQ separately;
- by year.

## 5. The retention rule (§8), at t0 = 10:00

Stage k is kept against the last retained stage if **both** hold out of sample:
1. its log loss falls by ≥ 2% relative;
2. its H-O2 HAC t (at 10:00) does not fall.

S-I is kept if its log loss is within 1% of the best individual-agent stage, or better (simpler wins).

**The retained-stage table** records every stage's log loss, accuracy, H-O2 t at both t0 and the verdict, in the
order run.

## 6. Gates (§13)

- **Gate O1:** H-O1 **and** H-O2 pass for the final retained stage, with H-O2 as defined above, including its Holm.
- **The kill conditions (§14) apply as written:**
  - H-O1 fails at S-A and at every later stage → kill;
  - H-O1 passes and H-O2 fails → "classifiable but not tradable", write up;
  - the agent shuffle does not remove an agent stage's gain → revert;
  - H-O4 fails → kill at the current latency.
- **Phase 6** (the book frame, robustness, Monte Carlo) and **Phase 7** (walk-forward DSR, leave-one-year-out,
  episode and one-bar-delay checks, 12A) run only past Gate O1, under their own pre-registration.

## 7. Multiplicity and trials

- **Every configuration evaluated is a row** of `data/opening/trials.csv` through `validation.programme.TrialsCsv`:
  - `doc` OPENING_AGENT_STATE_PREREG.md, `family` "opening H-O2";
  - the columns `stage`, `t0`, `construction`, `n_obs`, `mean_net`, `t_hac`, `notes`, with `reads_2024_plus` in the
    notes.
- **H-O2 is the only inference.** Holm runs across the two t0.
- **Promotion additionally needs the programme's p ≤ 0.005** (registry slot 7, 12A.2) and the programme DSR (12A.3),
  in Phase 7.
- `tests/unit/test_programme.py`'s TRIALS_CSV_FILES is amended in the same commit as the rows.

## 8. The runner's assertions, each proved to fire in `--selftest`

1. **Lag:**
   - every feature at checkpoint t is built from bars truncated at t's close;
   - **the leak canary (deposit test 25):** a feature built from bar t+1 is rejected by the pipeline's check;
   - labels never enter the feature matrix (test 2);
   - the walk-forward never fits on a test-window row.
2. **Money:**
   - a favourable move pays long and short;
   - FADE trades toward the prior close (test 14);
   - the state-flip exit fires below 0.30 (test 15).
3. **Right quantity:**
   - the policy's return is net of the cost and differs from its gross;
   - the paired difference is policy minus baseline, not the reverse;
   - OOS predictions differ from in-window predictions on the same rows.

**Modes:**
- `--dry-run` on synthetic labels and prices;
- `--run --phase 3` (S-A: H-O1, H-O3, and S-A's H-O2 statistic for the retention rule), once;
- `--run --phase 4-5` after A7 is resolved, once;
- `--check`, which rebuilds each output byte for byte.

## 9. What is fixed from this commit

Every definition, grid, threshold, seed and output above. **A change is a versioned amendment (OA-A8 onward), written
before the code that uses it.** Nothing is chosen after a result is seen.
