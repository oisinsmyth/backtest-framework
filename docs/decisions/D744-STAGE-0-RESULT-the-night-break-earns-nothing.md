# D744 STAGE 0 RESULT — NOT SUPPORTED: NQ's consolidation break at the European open earns nothing, and the ungated night break goes against itself

*2026-10-01.*
- *Spec:* [D744-STAGE-0-PRE-REG](D744-STAGE-0-PRE-REG-the-consolidation-break-at-the-european-open.md), committed
  before its runner, with A1 (the C1 known answer) committed before the scored run.
- *Runner:* `scripts/stage0_d744_european_open_break.py` (`--selftest` passed; `--run` 0.6 min).
- *Output:* `data/stage0_d744_european_open_break.json`.
- *In-sample only:* nothing dated 2024-01-01 or later was read.

## 0. Checks

**The first `--run`** stopped at D680's `known_answer` (D672's window to 2025-02), before any trade was built, and
wrote nothing. The fix is A1.

**The known answer (A1):** D672's C1 is reproduced under the 2024 cut.
- 328 trades;
- per-year net +5.3 / +0.7 / +5.8 / +10.0 / +12.0 / +4.1 for 2018–23, exactly D672's §3.

**Audits, all passed:**
- **Lag:**
  - the asia range reads no bar at or after 03:00, and the canary that includes the 03:00 bar fired;
  - `tier_audit` passed on p_rv, p_asia and ctier, and the leaky canary fired on all three.
- **Second implementation:** every trade agreed exactly with D666's own `plain_break` / `exit_trade` (entry bar,
  direction, entry, exit). The 09:28-close canary disagreed on 109 trades.
- **Sign:** a rising night pays the long and not the short.
- **Right quantity:**
  - the 03:00-inside condition binds: 169 sessions were already beyond the level, and 3 had no 03:00 bar;
  - P ⊂ U;
  - the night cost (\$4.60) exceeds the day cost (\$4.07).

**The window:** 2018-01-09 → 2023-12-29, 1,492 sessions.
- **The trades:** P 96 (13–18 a year), U 298, R 202.

## 1. The result

One MNQ at the night cost.

| book | trades | gross bp (HAC t) | net bp | total \$ | net Sharpe / Sortino | gross Sharpe | max DD | median \$ | win |
|---|---:|---|---:|---:|---|---:|---:|---:|---:|
| **P (gated, ctier < 1/3)** | 96 | **−0.30 (−0.09)** | −2.53 | −453 | −0.21 / −0.31 | −0.01 | 1,007 | −10.05 | .40 |
| U (every fresh crossing) | 298 | **−4.48 (−2.08)** | −6.78 | −4,450 | −1.22 / −1.69 | −0.85 | 4,996 | −22.91 | .35 |
| R (the rest) | 202 | −6.46 (−2.11) | −8.81 | −3,997 | −1.34 / −1.82 | −1.04 | 4,371 | −28.06 | .33 |

**At the other cost lines** (P / U / R net bp): day cost −2.27 / −6.52 / −8.53; 2× cost −2.78 / −7.05 / −9.08. The
result does not depend on the cost.

**The gate's null** (exact rotation of P's mask over U's 298 trades):
- S2 efficiency −0.002 against p50 −0.170 and p95 +0.031, **p 0.104**;
- S1 mean net −\$4.72 against p50 −\$15.27 and p95 −\$2.53.

## 2. The four groups (P)

- **Performance:**
  - mean gross −\$0.12 a trade, against 2c of \$9.20, so the breakeven cost is negative;
  - exposure 6.4 % of sessions;
  - Calmar −0.08; worst day −\$289.
- **Trade distribution:**
  - mean −\$4.72, median −\$10.05, payoff 1.32, skew 0.45, kurtosis 4.65;
  - trimmed both −\$4.55, ex-top −\$7.54, ex-bottom −\$1.73;
  - exits: 51 at the 09:29 close, 45 stopped;
  - entries by hour (03:00–08:00): 35 / 21 / 14 / 8 / 10 / 8.
- **What it depends on:**
  - net by year −171 / −32 / **+408** / −225 / −124 / −308: only 2020 is positive;
  - D736's label is RESTS ON ITS BEST YEARS (ex-2 −\$207 a year);
  - long −\$4.79 (59 trades), short −\$4.61 (37);
  - the top trade is 2022-02-03, short, +\$263.
- **Power:** P's minimum detectable gross at t 1.28 is 4.8 bp, against an observed −0.3. That is not a near miss.

## 3. The decision

- **Condition 1 (≥ 30 trades):** holds.
- **Condition 2 (D680's bar):** fails (t −0.09, net −2.53).
- **Condition 3 (the gate's rotation):** fails (p 0.104).
- **Condition 4 (the standard):** fails.
- U alone does not meet the bar, so there is no U lead. There is no COST-FRAGILE label.

**NOT SUPPORTED.**

## 4. The component line

P: net Sharpe −0.21, hit rate .40, skew 0.45, gross Sharpe −0.01; daily ρ with C1 −0.04, with D737's twin +0.01, with
NQ F2 +0.04.

**On 60 of P's 96 sessions C1 also trades at 09:30, in the same direction on 98 % of them.** The night crossing
leaves the price beyond the level at the open, and C1 then fills as a gap-through. This is the open-fill class the C1
diagnostic found weakest (+2.3 bp against +9.6 for the other fills).

## 5. Predictions against the outcome

- **Opus:** P(SUPPORTED) ≈ 0.15 → not supported ✓. "U's gross is near zero" ✗: it is −4.5 bp at t −2.1, in the
  middle of D677's −5.3 to +1.6 for fresh breaks on a foreign clock.
- **The Fable agent:** no quantified prediction.

## 6. Reading

**NOT SUPPORTED.** The post-shock consolidation break does not work on the European clock.
- **The gate does what C1's tier does:** it lifts the break from about −6.5 bp to about 0, and avoids where the night
  break gives back most. But it has nothing positive to select.
- **C1's edge belongs to the cash session.** A crossing made at night is not continued at night, and when C1 receives
  it at 09:30 as a gap-through, it is C1's weakest class. Both readings say the same thing: the information that
  makes a consolidation crossing hold arrives with the US cash open (NQ's clock, D727), not before it.

**An observation, not a lead, and not tested:** the ungated night break *reverses* (U gross −4.48 bp, t −2.08; R −6.46,
t −2.11).
- It is the reverse of no declared hypothesis.
- A fade of it would gross about +4.5 bp against a night cost of about 2.3 bp, so it would be thin under the fee and
  barrier constraint.
- It is recorded so that nobody re-proposes the continuation version. Pursuing a fade is the principal's call and
  would need its own pre-registration.

## 7. Next

The C1 comparison's ideas are spent: idea 1 (D743) and idea 2 (D744) are NOT SUPPORTED, and idea 3 (FOMC 14:00) was
underpowered by its author's own account. C1 stays as frozen, in vault slot 9.
