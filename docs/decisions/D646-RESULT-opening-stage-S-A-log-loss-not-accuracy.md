# D646 — RESULT: stage S-A of the opening model passes H-O1 by the letter, on log loss and a 0.1-point accuracy edge; its decision value is the baselines' cost, not the policy's gain

*2026-09-28. The principal: "build the runner and run it please". One Phase 3 run of `scripts/run_opening_stages.py`
(`7339bfe`) under D645 (`17c2b05`), OA-A1 … OA-A7, O-D4 kept. In-sample 2016-01-04 → 2025-02-28 (2,285 sessions,
33 walk-forward windows, 2,030 out-of-sample sessions); nothing on or after 2025-03-01 was read. Output:
`data/opening/phase3_S-A.json`, `data/opening/trials.csv` (3 rows). `--check` rebuilds it byte for byte.*

*Recorded before the run (`7339bfe`), from the dry run on synthetic random-walk bars:*
- *H-O1 fails on noise: accuracy equals the base rate, permutation p 0.44, log loss 0.3% below the base rate;*
- *H-O2's paired t is +6.1 / +5.1 on noise, because the policy barely trades while the baselines pay the cost every
  day. Only D645's second condition (the policy's own net > 0) stops a false pass.*

## Stage S-A: the five observables and the market dummy

### H-O1, at 10:00: PASS as D645 defines it, and read in full it is thin

| | model | base rate | |
|---|---:|---:|---|
| log loss | **0.907** | 0.933 | 2.8% lower (noise: 0.3%) |
| accuracy | **0.6181** | 0.6171 | **+0.1 point: 4 more correct days of 4,032** |
| permutation (1,000, within market × year) | p 0.000 | null p50 0.605, p95 0.609 | |
| Brier | 0.530 | | calibration flag: no |

- **The accuracy edge is a nineteenth of POWER's MDE** (1.8 points at t = 2). What passes is the permutation. Its null
  shuffles the labels against a model that predicts RANGE 97% of the time, so the null sits *below* the base rate
  (0.605 against 0.617), and any model that matches the base rate beats it. D645 fixed the test, so the verdict
  stands. But **the permutation measures association, not lift over the base rate**, and the record says so.
- **What the model does:** it predicts RANGE on 97.0% of rows, FADE on 2.9% and CONT on 0.05%.
  - Its FADE calls are right 40% of the time (47 of 117), against FADE's 20% base rate.
  - It never usefully calls CONT: 2 calls, both wrong.
- **The log loss is where the information is.** The model's probabilities beat the base rate's by 2.8%, nine times
  the noise run's 0.3%. It knows something about how likely each day type is. It is almost never sure enough to
  move the argmax off RANGE.

### H-O3, progression (diagnostic): the information grows through the morning, as §9 expects

| checkpoint | accuracy | base | log loss | base | gain | predicted not-RANGE |
|---|---:|---:|---:|---:|---:|---:|
| 09:45 | 0.626 | 0.627 | 0.898 | 0.920 | 2.4% | 2.6% |
| 10:00 | 0.618 | 0.617 | 0.907 | 0.933 | 2.8% | 3.0% |
| 10:30 | 0.607 | 0.600 | 0.917 | 0.954 | 3.8% | 7.3% |
| 11:00 | 0.602 | 0.591 | 0.910 | 0.964 | **5.7%** | 10.0% |

- The argmax changes on 2.8%, 5.4% and 6.7% of session-markets between consecutive checkpoints.
- Accuracy over the base rate rises from −0.1 to +1.1 points by 11:00, which is when trading has mostly passed.

### H-O2, S-A's decision value (the retention rule's reference): NOT a within-document pass

| t0 | traded rows | policy net / day | per traded row: mean, median, win | best baseline (net/day) | difference | HAC t | Holm p |
|---|---:|---:|---|---|---:|---:|---:|
| 09:45 | 62 of 4,017 | −0.13 bp | −8.8, −24.2 bp, 26% | B1 −1.88 bp | +1.75 bp | 2.71 | 0.012 |
| 10:00 | 82 of 4,032 | −0.05 bp | −2.5, −7.2 bp, 44% | B1 −2.04 bp | +1.99 bp | 2.74 | 0.012 |

- **The difference is the dry run's artefact, measured on real data.** The policy trades 1.5–2% of rows, almost all
  FADE. Every baseline loses to cost every day (B1 −1.9 to −2.0, B2 −3.0 to −3.9, B3 −2.6 bp a day). So "policy
  minus best baseline" is positive with t ≈ 2.7 while the policy itself is net negative. D645's second condition
  fails, and S-A does not pass H-O2 within the document. It would not have reached the programme's bar either
  (p ≤ 0.005).
- **What the policy trades loses:**
  - at 09:45 (62 FADE trades): mean −8.8 bp, median −24.2 bp, 26% winners;
  - at 10:00 (82 trades): mean −2.5 bp, median −7.2 bp, 44% winners.
  - These are small samples, and POWER called a per-traded-day test underpowered (MDE 3.1 bp).
- **The retention reference:** S-A's H-O2 t at 10:00 is 2.74. A later stage passes criterion 2 by not lowering it.
  That criterion rewards trading less (the dry run's note), so criterion 1 (log loss −2%) is the one that says
  whether an agent adds information.

## What it means

1. **The open's observables carry probabilistic information about the day type:** a log-loss gain 9× noise's, which
   grows through the morning. They do not carry enough to move a decision off "range day".
2. **Two properties of the pre-registered tests are now measured, not suspected:**
   - H-O1's permutation passes any model that matches the base rate;
   - H-O2's paired difference rewards not trading when the baselines lose to cost.
   Both stand (D645 is fixed). Every later stage is read with them: **H-O1 is judged by its log loss and its
   accuracy lift against POWER's MDE, and H-O2 by the policy's own net and per-trade numbers beside the paired t.**
3. The agents (Phase 4) have to move the probabilities far enough to change decisions, not only the log loss.

## Next

Phase 4 (S-B → S-I) runs once A7 is resolved (D645 §2):
- the Sierra ES/NQ pull finishes;
- then its signed flow is checked against the exchange flag on post-vault sessions, which needs ES/NQ `trades` from
  2026-09-19. That is free under the subscription, and it is asked for before it is pulled.
