# D752 STAGE 0 PRE-REGISTRATION — the YM open-reversal fade: at 11:00 ET, fade the Dow's move since the open on one MYM, with a bracket to the open (B1) and a high-win-rate bracket (B2)

*2026-10-01.*
- *The principal asked: "Are there any high win rate strategies, I would not mind having lots of small net wins in
  certain regimes". Offered D727's YM reversal as the one untested lead, the principal replied: "Pre-reg the YM open
  reversal fade, I am sceptical".*
- *Numbered D752; claimed with the documentation-review session, which holds D749 and D751.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29).*

## 0. Why, what is already read, and what this reopens

**The source** (D727):
- YM's β of the rest of the day on the move since the open is **negative from 10:00 to 13:00**. The most negative
  point is **11:00 (β −0.047, rotation rank 0.07)**.
- That is not significant on its own (rank 0.07 is not ≤ 0.05).
- **D728:** NQ leads, and YM "gives back its own move".

**What is already read on this data:**

| prior | object | result |
|---|---|---|
| **D727 §2** | YM, first clock with \|z\| ≥ k, **follow** to 15:59 | gross −\$2.99 / −\$3.84 / −\$1.72 (k 0.5 / 1.0 / 1.5). The **mirror (a fade) is therefore about +\$1.7 to +\$3.8 gross**, against a \$3.80 round trip |
| **D746**, primary | YM stretch fade, \|z\| ≥ 2 / 2.5 / 3 from the open, 10:00–14:30, a 1:1 bracket to the VWAP | gross −\$1.30 / −\$1.56 / −\$1.34; **NO ROOM**, Holm 1.00 |
| **D746**, its E2 leg | the same fades held to 15:59, no stop | gross +\$4.50 / +\$7.61 / +\$8.08 (t 1.06–1.47), flagged POST HOC as "not a lead" |

**What is new here:**
- **a fixed clock** (11:00, D727's most negative point), not the first crossing or a stretch trigger;
- **a lower trigger** (\|z\| ≥ 1.0);
- **brackets anchored on the open**: the price the reversal is said to return to.

**The in-sample is nonetheless heavily read.** A GO here is weak evidence. It would need a forward read on the
recorder's YM bars (from 2026-09-21), or another slice on the principal's word, before anything is built on it.

**What it reopens.** D747's result says that "with D746, intraday mean reversion on the index micros is closed for
the prop book". **This record reopens that closure for this one construction, on the principal's instruction
above.** Nothing else about D746 or D747 changes.

## 1. Data and the panel (D727's, read-only)

- **The panel:** `scripts/stage0_d727_trend_curve.py`'s `load_root("YM", DATA)` and `objects()`, on
  `fut_YM_rth_1m`, 2016-01-04 → 2023-12-29.
  - Roll days are dropped.
  - σ_oc is the prior-20 RMS of open → close.
  - x_t = (P_t − O) / σ_oc and z_t = x_t / √(t/390), exactly as D727.
- **The bars inside the session:** the 1-minute high and low from the same file (`raw`), for the brackets.
- **Cost:** MYM's `d508_exec` line from `data/futures_costs.json` (\$3 + 1.594 ticks × \$0.50 = \$3.80, D727's line).
- **Run under the project venv.**

## 2. The construction (fixed now)

**Entry:**
- At **11:00 ET**: P = D727's P_t for t = 90 minutes, the 10:59 bar's close.
- **The trigger is \|z₁₁\| ≥ 1.0.**
- **Side = −sign(x₁₁):** short after a rise from the open, long after a fall.
- One MYM, filled at P.

**The move:** m = \|P − O\| in points.

**Exits, checked on each 1-minute bar from 11:00 to 15:58:**
- **The order within a bar:** if the target and the stop are both inside the same bar, **the stop is assumed first**.
- **The target is a resting limit.** It fills only if the bar trades **through it by one tick**, at the target price.
- **The stop** fills at the stop price **less one tick** of slippage.
- **The time exit** is 15:59's close.

| bracket | target (from P, toward the open) | stop (from P, away from the open) | driftless P(win) |
|---|---|---|---|
| **B1, to the open** | m: the open itself | m | ≈ 1/2 |
| **B2, high win rate** | 0.5 m | 1.0 m | ≈ 2/3 |

**Context, not in the rule:** **E0**, the same entries held to 15:59 with no bracket (the fixed-clock mirror of D727's
book).

## 3. The tests, per bracket (B1, B2; Holm over the two)

**SIGNAL (R15).**
- Gross mean per trade above the **exact circular rotation of the fade's side labels** over the triggered sessions.
  Each session keeps its entry, m and bracket geometry; only the side shifts.
- Every offset is enumerated. p_high is the share of offsets with gross mean ≥ the observed, offset 0 included.
- **Holm-adjusted p ≤ 0.05.**
- p50 and p95 are reported.

**ECONOMICS (the principal's standards):**

| | criterion |
|---|---|
| **N1** | net mean > 0 at **t ≥ 2** |
| **N2** | **median net ≥ 0** (the principal's, D750) |
| **N3** | skew of net per trade **≥ −0.5** (the components ledger's C-c: a high-win-rate shape must not hide a tail) |
| **N4** | D736's earn-when-trading standard: G1 net without the two best years > 0; G2 positive in ≥ ⌈2/3 · n⌉ years; G3 ≥ \$209 a year without the two best years |

**The reading per bracket:**
- **GO:** SIGNAL and N1–N4 all hold.
- **SIGNAL ONLY:** SIGNAL holds and some N fails; they are named.
- **NOTHING:** SIGNAL fails.

**Reported for every cell (E0 included):**
- **The four groups:**
  - net and gross per trade, Sharpe and Sortino, max drawdown, breakeven cost;
  - trades, mean, median, **win rate**, payoff, skew, kurtosis, and the 1 % trims (ex-top, ex-bottom, both);
  - years positive and the largest year's share;
  - the rotation's p50 and p95.
- **How trades end:** the shares that ended at the target, at the stop and at the time exit.
- **The component line:**
  - net Sharpe at one MYM, hit rate, skew, gross beside net;
  - the daily-P&L correlation with D737, F2 and C1 (`data/d748_component_books.csv`, the in-sample calendars).
- **Hedge exposure:** the share of fade sessions on which D737 also trades. D737 holds an MNQ position, and a fade
  in MYM on the opposite side would be a correlated hedge (Apex). Sides are not in the books file, so this is the
  co-trading share; a live rule would skip on conflict.

## 4. Assertions (each canary must raise in the self-test)

1. **The known answer:** the YM panel reproduces D727's YM figures exactly:
   - the 11:00 β of −0.047 (to the JSON's precision) and its session count (1,938);
   - the follow-to-close book at k 1.0: 1,450 trades, gross −\$3.84.
2. **Lag:**
   - the trigger and the side use only bars up to 10:59 and σ_oc from prior sessions;
   - a second implementation from the raw minutes agrees on 40 sampled sessions;
   - a canary using 11:00's close instead must disagree.
3. **Sign in money:** a short after a rise pays positively when the price falls back; the target and stop distances
   are on the correct sides for both directions.
4. **The bracket:**
   - on planted minute paths, target-first, stop-first, same-bar (stop assumed) and time-exit cases each resolve as
     declared;
   - a target touched but not traded through by a tick does not fill.
5. **The rotation:**
   - offset 0 equals the observed;
   - a planted side that always matches the outcome gives p < 0.01;
   - the vector form equals a loop on 50 offsets.
6. **The seal:** nothing on or after 2024-01-01 is read.

## 5. Predictions (Opus; the principal is sceptical and so am I)

- **P1:** E0's gross at 11:00 is +\$1 to +\$4 a trade (D727's mirror and β).
- **P2: B1 is NOTHING.** Its gross is near zero: the bracket gives back what the held fade gets in its tail (D746's
  primary against its E2).
- **P3: B2 wins 60–68 % of trades,** near its geometric 2/3, and its skew is below −0.5. **NOTHING.**
- **P4:** no cell's net mean is above zero at t ≥ 2.
- **P(any GO) ≈ 0.05.**
