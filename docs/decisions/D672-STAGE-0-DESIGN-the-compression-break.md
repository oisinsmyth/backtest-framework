# D672 — STAGE 0 DESIGN (development): the compression break. Trade the break of yesterday's range only when recent and overnight realised volatility are low, on ES and NQ

*2026-09-29.*
- *The principal: "Ok lets run that new construction from that thread on ES and NQ. I know there is nothing on ES but may
  as well run it on both".*
- *The thread is D671's diagnostic (`2dea28a3`). NQ's breaks on quiet-forecast days made +7.71 net against +0.11. The
  effect was carried by low recent realised range and low overnight range, not by |gap| or dealer gamma, which went the
  other way.*
- *Committed alone, before its runner.*

## 0. What this is

**DEVELOPMENT, on the sample where the thread was found.**
- On NQ this run is close to circular. It fixes the definitions and measures the construction; it cannot confirm it.
- ES is the in-sample contrast. The diagnostic already showed nothing there.
- No verdict is issued.
- Confirmation needs YM and RTY (a separate pre-registration, once their overnight data is built), then the vault.

## 1. The construction (nothing fitted)

1. **Direction and exit:** D666's plain break with E4, exactly as D668/D671. One micro, and D668's cost line.
2. **The compression score, known by 09:29:**
   - p_rv = the walk-forward percentile of rv5 (the mean RTH range/ATR20 over the 5 prior sessions) among the root's
     previous 250 sessions;
   - p_on = the same for the overnight two-way range, (Globex 18:00 → 09:29 high − low − |gap|)/ATR20;
   - comp = (p_rv + p_on)/2;
   - its tier = comp's percentile among the root's previous 250 comp values.
   - D671's functions compute all of these (`session_features`, `tiers`).
3. **The rule:** trade the break only when the compression tier is < 1/3 (the quietest third). One micro.

**Not in the rule:** gamma, |gap|, vetoes, calendar skips, side rules. Each is reported as a split only.

## 2. Reported

**The books,** on D671's evaluation window (where the tier exists):
- B0, every break;
- **C1, the construction;**
- C2 and C3, the middle and top thirds.

For each: trades a year, gross and net, HAC t, win rate, P(hold), $ a year per micro, daily Sharpe and Sortino, and
maximum drawdown.

**Nulls:**
- a within-year random subset of B0 of C1's count, 1,000 draws (seed 672): p50, p95 and its bootstrap SE, and C1's
  rank;
- an enumerated rotation of the tier series across sessions: C1 − rest, p50, p95 and the rank.

**The four groups and the component line** for C1: daily $ Sharpe at one micro, ρ with the rebuilt K8, and ρ between
the roots.

**By year:** C1 against B0.

**Splits of C1 (reported only):**
- long / short;
- dealer short gamma (SPX GEX < 0 prior row), and also above/below its walk-forward median;
- the open class;
- the E2 exit.

**Each input alone** (p_rv, p_on) as the tier, for comparison.

## 3. Expectations, written before the run

1. **NQ C1:** net +5 to +9 bp, about 50 trades a year, with the rotation rank above 0.95.
2. **NQ C1 beats B0** in daily Sharpe, and is within ±40% of B0 in $ a year.
3. **ES C1:** net within ±2 bp of zero, and inside the placebo.
4. **NQ C1:** positive in at least 5 of the 7 full years, 2018–2024.
5. **Within C1 on NQ,** short gamma is better than long gamma (the size effect, D665).

## 4. Outputs

- `scripts/stage0_d672_compression_break.py`;
- `data/stage0_d672_compression_break.json` (statistics only, licence-guarded);
- a RESULT record.
