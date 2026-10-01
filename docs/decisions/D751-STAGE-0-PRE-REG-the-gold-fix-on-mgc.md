# D751 STAGE 0 PRE-REG — the gold fix on MGC: does gold keep moving into the LBMA PM price auction (15:00 London) in the direction of its first US half-hour, and give it back after?

*2026-10-01. The principal: "Close D749 and pre-reg the gold fix as D751". The idea is the Fable 5.1 agent's #3 from
the same round as D749.*
- **What it is:** a premise check, oracle first. It chooses no rule.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the result
  separately.
- **The prop book's rules:** one MGC, held at most 30 minutes inside the day session.

## 0. The mechanism and what is known

- **The mechanism (the agent's):**
  - US-listed gold ETFs (GLD, IAU) strike their NAV at the LBMA Gold Price PM, set by an auction at 15:00 London.
  - Their authorised participants absorb US investors' ETF flow from the 09:30 equity open.
  - They hedge it in COMEX gold before the auction, then create or redeem at NAV and unwind the hedge.
- **The prediction:** pressure into the fix in the direction of the morning's US flow (proxied by gold's 09:30 →
  fix − 5 minutes move), and a reversion after.
- **Literature:** Caminschi & Heaney (2014) found abnormal returns and volume in the gold fix window. The phone fixing
  became an electronic ICE auction on 2015-03-20.
- **Nothing in this repo has scored it.** "LBMA" and "fix" appear only in D634 (a BCOM proxy) and D709 (silver funds'
  settlement flow, which FAILED: silver moved into its COMEX settlement, but not because of the funds). D719 (F2 at
  commodity settlement windows) did not transfer. The 15:00 London window has never been read.
- **The prior** (before any run): the Fable agent 25%; this session about 15%.
  - MGC's round trip is \$5.93 (its d508_exec crossing is 2.93 ticks), so the bar is \$11.87, higher than the agent
    sized.
  - Short legs on gold may not move that much.

## 1. Data, seal, conventions

- **Bars:** `fut_day1m.parquet`, GC (front contract, 09:00–16:00 ET), read with a parquet filter on root ∈ {GC} and
  day < 2024-01-01.
  - Sessions need `present` and `same_front`. GC's first clean year is 2011, and the window is
    **2011-01-01 → 2023-12-31**.
- **The seal:** nothing dated 2024-01-01 or later is read.
- **The fix clock:** 15:00 Europe/London converted to America/New_York per date. That is 10:00 ET normally, and 11:00
  ET in the US/UK daylight-saving mismatch weeks. Prices are as in D749: the open of a bar, or the close of the bar
  before a minute (carried forward).
- **The signal:** s = sign(P(fix − 5) − P(09:30)), gold's move from the US equity open to 5 minutes before the fix.
- **The gate (primary):** |that move| > the median of the previous 250 sessions' |move| (strictly earlier sessions;
  walk-forward). Sessions without 250 prior values are burn-in and are not scored.
- **The legs:**
  - **A, into the fix:** s from fix − 5 to fix + 5 (09:55 → 10:05).
  - **B, after the fix:** −s from fix + 5 to fix + 30 (10:05 → 10:30), the reversion.
  - **Reported:** A and B ungated, and A over fix − 15 → fix + 5 as a sensitivity.
- **Size and cost:** one MGC (10 oz; \$1 a 0.1 tick).
  - The round trip is \$3 + 2.933 × \$1 = **\$5.93**.
  - **The prize bar is 2 × cost = \$11.87.**

## 2. Controls and nulls

- **N1, the sign rotation (primary, enumerated, SE 0):** the s series is rotated circularly over the scored sessions
  (offsets 20 … n − 20), and the statistic is each leg's mean signed gross.
- **N2, the placebo clock:**
  - the same construction with the fix moved to 11:30 ET (no auction), with its own gate;
  - each leg must beat its placebo twin (Welch t ≥ 1.64).
- **N3, the daylight-saving control (reported):** on the mismatch sessions, the legs at the real fix (11:00 ET)
  against the same legs at 10:00 ET.
- **Eras (reported):** the phone fixing (to 2015-03-19) and the ICE auction (from 2015-03-20).

## 3. Oracles (first; they can kill a leg)

- **O1, per leg:** the mean |move| in dollars. If it is < 2 × cost (\$11.87), no sign rule can pay that leg: **NO ROOM**
  for the leg.
- **O3:** the |move| quartiles.

## 4. Readings (declared now; per leg)

| reading | condition |
|---|---|
| **NO ROOM** | the leg's mean \|move\| < \$11.87. Recorded first |
| **FLOW PRESENT** | the gated leg's mean signed gross > 0 at a NW t ≥ 2 (sessions in date order, 5 lags), **and** above N1's p95, **and** above its N2 placebo twin (Welch t ≥ 1.64) |
| **NOTHING** | otherwise |

- **Holm over the two legs** (A, B), each p from N1.
- **GO to a rule design with the principal** requires, for a leg:
  - FLOW PRESENT and not NO ROOM;
  - a Holm p ≤ 0.05;
  - mean net > 0 at one MGC;
  - ≥ 8 of 13 years positive, and the largest year < 50%;
  - the auction era (from 2015-03-20) positive.
- GO starts the design conversation; it admits nothing.

**Reported, all four groups, per leg:**
- gross and net; Sharpe and Sortino (annualised by the leg's own trade count); max drawdown;
- the mean move against 2c, and the breakeven cost;
- count, mean, median, win rate, payoff, skew, kurtosis, and the symmetric trims;
- the years, long against short, and the eras;
- N1's p50 and p95, N2, and N3;
- **the component line:** net Sharpe, hit rate, skew, gross beside net, and the daily ρ with D737's twin, NQ F2 and
  C1. Their daily nets come from D749's `--other-lines` mode under the project interpreter, written to a temp CSV
  before the run and read by the runner. The run itself is under the system interpreter, for pyarrow.

## 5. Runner assertions

- **The clock:** the zoneinfo fix equals the statutory-rule implementation (UK and US daylight-saving dates) on every
  scored session. There are mismatch sessions (> 0), at 11:00 ET.
- **Lag:**
  - the signal reads no bar starting at or after fix − 5, and a canary reading the fix − 5 bar must change some s;
  - the gate's median uses strictly earlier sessions, and a canary including the session's own |move| must change
    some gate.
- **Sign, in money:** a synthetic rise pays a long A leg and costs a short one.
- **Right quantity:** A ≠ B; the gated set is a strict subset of the ungated; the placebo clock never equals the fix
  clock.

## 6. Output

`scripts/stage0_d751_gold_fix.py` and `data/stage0_d751_gold_fix.json` (statistics only). The result is a separate
record.
