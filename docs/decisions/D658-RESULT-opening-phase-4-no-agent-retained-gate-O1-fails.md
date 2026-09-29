# D658 — RESULT: no agent adds information to the opening model, its final stage is S-A, and Gate O1 fails on H-O2; the trade rules would pay on a known label, and the model cannot see continuation

*2026-09-28. The principal: "give it to me sooner". One Phase 4-5 run of `scripts/run_opening_stages.py --run --phase
4-5` (`a295a5a`: `scripts/opening_phase45.py` as committed before the run) under D645 (`17c2b05`), OA-A1 … OA-A9.
In-sample 2016-01-04 → 2025-02-28 (2,030 out-of-sample sessions); nothing on or after 2025-03-01 was read. 10.8 min.
Output: `data/opening/phase45.json`, 14 trials in `data/opening/trials.csv` (`9b0086b`).*

*A7 entered as S-B: its exchange-flag check passed (`a295a5a`: day-level r 0.947 against the bar of 0.8). Recorded
before the run: its prior-20-day 90th-percentile cut falls over the in-sample (ES 5–8 lots in 2015–17, 2–3 from 2022;
NQ 2, then 1 from 2019), so A7 moves from large-trade flow towards all signed flow. O0-H passed for both markets, so
S-H (A4, dealer gamma) ran.*

*After the run, one runner fix, no statistic touched:* the run wrote `phase45.json` and stopped at the trial log.
S-A's two H-O2 trials were already logged by Phase 3 (D646), and `trials.csv` is append-only, so nothing was
appended. S-A is the same model on the same rows, and its numbers equal Phase 3's to six decimals. `log_trials45()`
now skips a logged trial only if its n, mean and t are identical, and raises otherwise (checked on a changed number).
`--log-trials --phase 4-5` logged the other 14 from the written file. The model did not run again.

## Retention: every agent fails criterion 1

The rule (D645 §5), at 10:00: log loss falls ≥ 2% relative **and** the H-O2 HAC t does not fall. Each stage adds one
agent to S-A, the last retained set.

| stage | agent | log loss (S-A 0.90700) | change | H-O2 t (S-A 2.744) | kept |
|---|---|---:|---:|---:|---|
| S-B | A7, large-lot signed flow | 0.90772 | −0.08% | 2.70 | no |
| S-C | A1, stop holders | 0.90797 | −0.11% | 2.81 | no |
| S-D | A2, trend followers | 0.90959 | −0.28% | 2.72 | no |
| S-E | A3, vol-target funds | 0.90701 | −0.00% | 2.81 | no |
| S-F | A5, macro reactors | 0.91118 | −0.46% | 2.81 | no |
| S-G | A6, index arbitrage | 0.90597 | **+0.11%** | 2.65 | no |
| S-H | A4, dealer gamma | 0.90681 | +0.02% | 2.77 | no |

(change: positive = log loss lower.)

- **Five of seven make the out-of-sample log loss worse.** The best, A6, improves it by a twentieth of the 2% bar.
- With nothing retained, S-I (the alignment summary N, D) had no agents to summarise and did not run. H-O5's agent
  shuffle had nothing to shuffle.
- **The final stage is S-A**, Phase 3's model (D646).

## The final stage's tests (S-A)

| test | result | verdict |
|---|---|---|
| H-O1, 10:00 | log loss 0.907 vs 0.933 base; accuracy 0.6181 vs 0.6171; permutation p 0.000 (null p50 0.605, p95 0.609) | PASS by the letter (D646: the permutation passes any model that matches the base rate) |
| H-O2, 09:45 | policy **−0.135 bp/day net**, −0.093 gross; +1.75 bp over B1 (−1.88), HAC t 2.71, Holm p 0.012 | FAIL: the policy's own net < 0 |
| H-O2, 10:00 | policy **−0.051 net**, +0.007 gross; +1.99 over B1 (−2.04), t 2.74, Holm p 0.012 | FAIL: the same |
| H-O3 | the log-loss gain grows 2.4% → 5.7% from 09:45 to 11:00 (D646's table) | diagnostic |
| H-O4, 10:00 FADE (80 trades) | c5 −5.9 bp, c60 +5.8 bp | PASS on the rule; 09:45 FADE n/a (c60 −3.4); CONT: too few trades (0, 2) |
| H-O5, midday placebo | log loss 0.802 vs 0.814 base (**1.4% gain**); accuracy 0.699 vs 0.702 | half the 10:00 gain (2.8%) appears at noon with no opening in it |
| H-O6, 4,570 rows, joint OLS | no pressure moves r(09:31 → 10:30) as predicted: every Holm p ≥ 0.97; z1 (t −1.03), z2 (−0.48), z5 (−1.67) the wrong sign; z1 on 10:30 → 11:30 t −0.55; A7 on z2 t 1.23 | FAIL for every agent |

**Gate O1 = H-O1 and H-O2: FAILS.** H-O2 does not go to the vault.

**The per-trade book** (the policy trades 62 of 4,017 rows at 09:45 and 82 of 4,032 at 10:00, almost all FADE):

| t0 | n | mean | median | win | skew | kurtosis |
|---|---:|---:|---:|---:|---:|---:|
| 09:45 | 62 | −8.84 bp | −24.23 | 26% | +1.31 | 1.20 |
| 10:00 | 82 | −2.50 bp | −7.24 | 44% | −0.18 | 1.67 |

- **Component line:** the policy's net per session is below zero at both t0 (and gross ≈ 0), at the micro round trip
  the runner charges (OA-A5). So its component Sharpe is negative, and it does not enter `COMPONENTS_PROP.md`. The
  runner writes no per-session series, so the Sharpe, Sortino and correlations are not computed. The sign needs no
  series.

## OA-A8: where it fails

**The ceiling.** OA-A8's oracle trades each state's own rule on the days whose label IS that state (out-of-sample
rows, net at the micro cost):

| t0 | CONT oracle: n, net mean, t, median | FADE oracle: n, net mean, t, median |
|---|---|---|
| 09:45 | 635, **+8.3 bp**, 5.1, −2.2 | 862, **+6.9 bp**, 4.9, −3.3 |
| 10:00 | 682, **+12.6 bp**, 8.6, +10.5 | 862, **+6.4 bp**, 4.1, +1.7 |

**Can the model tell the states apart?** AUC, with a 95% CI from 2,000 session bootstraps:

| t0 | CONT | FADE | RANGE |
|---|---|---|---|
| 09:45 | **0.502** (0.472–0.530) | 0.639 (0.616–0.662) | 0.590 |
| 10:00 | **0.506** (0.478–0.534) | 0.655 (0.631–0.678) | 0.593 |

**Capture:** at 10:00 FADE's policy nets −2.09 bp per trade against the oracle's +6.39. At 09:45 it nets −8.84
against +6.91.

1. **The trade rules are not the failure.** With the label known, both states' 60-minute trades clear the micro cost
   by 6–13 bp a trade, at t 4–9.
2. **The model cannot see continuation at all.** CONT's AUC is 0.50 with a CI across 0.5, which D647 found by hand
   (S-A cannot see trend days). FADE is partly visible (AUC 0.64–0.66), but the calls it is sure enough to trade
   lose.
3. **The agents add nothing to either.** Not as features (retention), and not as causes (H-O6).

The v2 trigger (OA-A8.3: CONT AUC ≥ 0.55 with a CI above 0.5) does not fire. OA-A10 runs D652 regardless.

## What it means

- **The agent-state model's premise fails on this data.** The seven pressures do not predict the morning's type or
  its move. The observables' log-loss information is half generic: the midday placebo keeps 1.4% of the 2.8%.
- **The prize the research pointed at is real but unreached.** A known label pays 6–13 bp a trade net. Reaching it
  needs a model that sees continuation, which nothing here does.
- D652 (v2) was built on exactly this reading. It has binary per-trade targets, the fade to the prior close, the
  continuation held to the close, the expected-profit rule, and A4 scaled by liquidity. It is judged by its own
  pre-registered kill, not by this record.
- **Recommendation for the principal:** close H-O2 of the agent-state model (Gate O1 has failed as D645 registered
  it), and release programme slot 7.

## Next

- D652's in-sample run, once (launched after this run's commit).
- Slot 7 (H-O2) leaves the joint vault run's list unless the principal rules otherwise.

## CLOSED by the principal, 2026-09-29, and programme slot 7 released

**The principal:**
- "close opening model v1";
- on the slot: "Release it".

**Why:**
- Gate O1 failed as D645 registered it (above): no agent was retained, and H-O2's policy is net-negative at both t0
  (−0.135 and −0.051 bp a day).
- Its successor, v2 (D652/D659), was closed the same day without spending its vault look.

**What that means:**
- **H-O2 never goes to the joint vault run, and its vault look is not spent.**
- The agent-state model is not re-opened by re-tuning its agents or stages on the in-sample.
- **Programme slot 7 is released:**
  - `data/programme_registry.json` moves "opening H-O2" to its `released` list, with this ruling as the reason;
  - `Registry.release`, in `validation/programme.py`, records it and refuses a second release or a re-registration
    of the same family;
  - slots 7 and 10 are now free, and 0.040 of the programme α is allocated.
- **This is the principal's override** of the deposit's default that α is "never re-allocated retroactively for
  families already evaluated". It applies to this family only. LETF H1 (slot 1) and shock H1 (slot 2), also closed,
  keep their slots.
- **Superseded:** the "Next" line above ("D652's in-sample run, once") ran as D659, and v2 is closed.
