# D669 STAGE 0 DESIGN — where the admitted MACD arm's returns come from: drift or timing, the horizon of its direction, lookback momentum, trend days, the price level, and the search it was chosen from

*Drafted 2026-09-29 on the principal's word. Committed alone, before its runner exists (R8). **None of these
decompositions has been computed:** no long/short split, no direction permutation, no lookback agreement, no
neighbourhood cell and no deflated Sharpe exists for the arm on disk (checked against every record D484–D667 and
their JSON files). Prop book, measurement only. Numbered D669 because the other session's unmerged branch already holds the number before it.*

## 0. Why, and what it can and cannot decide

The principal, 2026-09-29, closing D667:

> "Close after then investigate the MACD. We have learned a lot since we admitted that arm, can you do our usual test
> and see if you can find the mechanism to its returns?"

Earlier the same day: "I think the MACD arm has a high chance of being overfitted."

**What is known, and why it motivates this record:**
- **The arm was chosen from a search.** D484 → D488 → D491 (24 costable cells) → D495 (111 cells, 37 of them AGREE).
  The admitted cell, NQ AGREE M=5, was the family maximum of D495, and M=5 sat at the edge of its grid.
- **It does not transplant.** D506 found 15 of 28 roots gross-positive but only NQ and HG clearing their own nulls.
- **Its conditioners rank years, not sessions** (D508, D509). The one that survived a within-year control (D512)
  does not transfer (D513).
- **Four years carry it.** 2020, 2022, 2025 and 2026 make 96 % of the full-history P&L (D504).
- **It is in practice one trade a day.** 66.6 % of entries are at 10:00 and 75 % of exits are the forced 16:00 flat
  (D527).
- **Its edge is about three points of accuracy.** Hit rate 50.5 % against a price-path-preserving rotation null's p95
  of 49.3 %, while the payoff sits inside its null (D529).
- **Never split:** the arm's P&L into long and short, drift and timing, or signal and a simpler lookback. Its
  parameter neighbourhood has never been scored, and no deflated Sharpe has been computed.

**What this can decide.** It names which of five candidate sources carries the arm's in-sample returns, and whether
the arm's Sharpe survives the search that selected it.

**What it cannot decide.**
- **It cannot admit or retire anything.** A finding here is an interpretation for the principal. Any change to
  `BOOK_PROP.md` is the principal's word, written there (R15).
- **Nothing from 2024 on is read.** The window is D508's, 2016-01-04 → 2023-12-29. The arm's 2024+ slice was spent by
  D503, and no unread NQ slice remains, so no mechanism found here can be confirmed out of sample on NQ.

## 1. The arm, frozen and imported

The admitted arm exactly as `BOOK_PROP.md` specifies it:
- NQ front month by volume, one MNQ, day session only;
- decide at each hour's close from h09 and execute at the next open;
- enter when the log Impulse MACD (34/9) and the log MACD histogram (12/26/9) agree in sign;
- exit when the signal turns, after a 5-hour minimum hold; forced flat at the h15 close;
- $3.50 a round trip.

**It is built through D504's `build()` and clipped to the window as D508's `load_arm()` clips it.** It is simulated
trade by trade with D503's `simulate_trades()`, which D503 asserted is the same machine as D491's `simulate()`.

**The runner first asserts:**
- the per-session sums of the trade rows equal `load_arm()`'s net and gross exactly;
- 1,876 sessions and $15,423 net (D508).

**Notation.** For trade i:
- d_i = ±1 is the direction;
- m_i = exit price − entry price, in MNQ dollars (points × $2), is the window's move, signed long;
- the gross is g_i = d_i·m_i;
- the net is g_i − $3.50.

## 2. The five questions

### Q1 — Drift or timing, and at what horizon does the direction information live?

**The statistic** is the arm's total gross G = Σ d_i m_i, split into long trades and short trades (count, share of
trades, gross, hit rate, mean per trade).

**The matched-exposure long control, C0:** long in every one of the arm's own windows, Σ m_i. It holds the same
sessions and hours at the same cost, and carries no direction information.

**The direction-permutation null, N1.** Keep every trade's session, entry hour, exit hour and cost. Permute only the
labels d_i among the trades of a stratum.
- Every stratum keeps its long share exactly, so drift is preserved.
- Only the link between a direction and its own window's move is broken.
- This randomises the partner (the window a direction is paired with), not the membership (which windows are held).

**Five strata, from coarse to fine:**
- the whole window;
- calendar year;
- calendar quarter;
- calendar month;
- ISO week.

**Each stratum gets 10,000 draws, seed 669.** Reported: p50, p95, the p95's bootstrap SE (1,000 resamples of the
draws), and G's percentile.

**Drift carry,** computed exactly for each stratum s:
- D_s = Σ over strata of (trade count × the stratum's mean d × its mean m). This is N1's expectation, and the runner
  asserts the mean of the draws is within 3 SE of it.
- **The drift share is D_global / G.**
- The timing share is 1 − D_global / G.

**Reading the horizon.**
- A permutation within a stratum preserves any direction information that is constant across that stratum.
- If the arm's direction is right because it is long through rising months, a within-month permutation keeps that and
  the arm cannot beat it.
- **So the finest stratum the arm still beats is the shortest horizon at which its direction information varies.**

| bar | declared |
|---|---|
| **Q1-T** | G > N1(whole window)'s p95 by more than 2 SE → the arm times direction beyond drift |
| **Q1-D** | drift share < 0.5 → timing dominates; ≥ 0.5 → drift dominates |
| **Q1-H** | the finest of week < month < quarter < year < whole at which G > that stratum's p95 by more than 2 SE; "none" if it fails even the whole window |

A margin within 2 SE of a p95 is UNRESOLVED (D373).

### Q2 — Is the direction just the sign of a recent return?

**The lookbacks.** At each trade's decision bar t (the entry bar, a segment index into the continuous 23-segment
hourly log-close series that the MACD itself reads, overnight included), the sign of the log return over L bars back:

| name | L (bars) | meaning |
|---|---|---|
| R1h | 1 | the last hour |
| RON | t + 2 | since the prior session's h15 close (overnight plus the morning) |
| R1d | 23 | one session |
| R2d | 46 | two sessions |
| R5d | 115 | one week |
| R20d | 460 | one month |

A zero or undefined return counts as no direction; such trades are counted and excluded from that lookback's
agreement.

**For each lookback:**
- **Agreement:** the share of trades whose d_i equals the lookback's sign.
- **Substitution gross:** Σ sign_L,i · m_i on the arm's own windows, and its share of G.
- **The disagreement split:** on trades where d_i ≠ sign_L,i, the arm's own gross Σ d_i m_i. Positive means the MACD
  wins where it departs from the lookback: it carries information beyond it.
- **The free-running book:** the same state machine (M=5, h09 first decision, h15 flat, $3.50) with signal =
  sign(lookback) at every bar. Reported: net and gross Sharpe and Sortino, trades, and hit rate. **This is a scored
  construction, so it gets a component line** (§4).

| bar | declared |
|---|---|
| **Q2-R** | the arm "reduces to lookback L" if, for some L, agreement ≥ 80 % AND substitution gross ≥ 80 % of G |
| **Q2-A** | the MACD "adds beyond L" for every L whose disagreement-split gross is positive with a trade-level t > 2 |

**Six lookbacks are tried.** If Q2-R fires for more than one L, all are named; the one with the highest substitution
share is reported as the nearest, and the selection over six is disclosed.

### Q3 — Trend days or volatility?

For every session the arm trades:
- the move M_d = log(C[d, h15] / O[d, h10]) is NQ's 10:00 → 16:00 return;
- the realised volatility v_d = √Σ r² over the six hourly segment returns h10…h15 (r = log C/O of each segment);
- the efficiency e_d = |Σ r| / Σ |r| over the same six.

**Q3a, the move profile.** Quintiles of |M_d|, globally and within calendar year. Per quintile: trades, hit rate,
gross per trade, share of G, and N1(whole window)'s expected gross per quintile beside it.

**Q3b, trend against volatility.** An OLS of the arm's session gross on z(e_d) and z(v_d), z-scored within year,
with Newey-West standard errors (5 lags). Beside it, the 2 × 2 table of mean session gross by above/below the
within-year median of e_d and of v_d.

**Q3c, the month.** An OLS of the arm's monthly gross on |the month's NQ return| (close to close of the daily level)
and the month's daily-return standard deviation. 96 months, Newey-West 3 lags.

| bar | declared |
|---|---|
| **Q3-T** | "trend-day capture" if the top global \|M\| quintile carries > 100 % of G AND its hit rate exceeds the bottom quintile's by more than 2 binomial SE |
| **Q3-V** | "trend, not volatility" if in Q3b the efficiency coefficient has t > 2 and the volatility coefficient has \|t\| < 2 |

### Q4 — Is the year concentration the price level?

Per year, for the gross per trade:
- in dollars;
- in basis points of the entry price (m_i / entry price × 10⁴, signed by d_i);
- the round-trip fee in bp of the entry price;
- the mean |M_d| in bp.

**Also:** the share of total gross from 2020 plus 2022, in dollars and in bp (the in-window share of D504's four
years).

| bar | declared |
|---|---|
| **Q4-P** | "the price level explains the concentration" if the 2020 + 2022 share in bp is below two-thirds of their share in dollars |

### Q5 — Does the Sharpe survive the search that chose it?

**Q5a, the deflated Sharpe** (Bailey and López de Prado 2014). All Sharpes are per session (annualised ÷ √252), over
T = 1,876 sessions.
- The trial set is the finite net Sharpes among D495's 111 cells (`data/d495_agree_confluence.json`, `cells[*].net_sharpe`);
  N is their count.
- V is their variance.
- The expected maximum is SR₀ = √V · ((1 − γ) Φ⁻¹(1 − 1/N) + γ Φ⁻¹(1 − 1/(N e))), with γ Euler's constant.
- The deflated Sharpe is DSR = Φ((SR̂ − SR₀) √(T − 1) / √(1 − γ₃ SR̂ + (γ₄ − 1)/4 · SR̂²)), where γ₃ and γ₄ are the
  skew and (non-excess) kurtosis of the arm's daily net.

**Two sensitivities:**
- N = 37 with the AGREE cells' own variance (lenient: counts only the family the arm won);
- N = 250 with the primary V (the survey's count of cells looked at from D484 on).

The trial Sharpes are correlated (the same root across M), so the primary N overstates the independent trials. That
makes the primary strict, and the N = 37 row is its lenient bound.

**Q5b, the neighbourhood.** The same machine, the same sessions and the same cost across a grid:
- MACD fast ∈ {9, 12, 15}, slow ∈ {20, 26, 32}, signal ∈ {7, 9, 11};
- impulse length ∈ {26, 34, 42};
- M ∈ {3, 4, 5, 6, 7, 8}.

That is 486 cells, one of them the arm.
- The impulse signal length stays 9, and the contract-purity window stays 78 bars, so every cell trades the identical
  session set.
- The parameterised indicators are asserted to reproduce D484's `impulse_macd` and `macd_hist` exactly at the defaults,
  and the default cell is asserted to reproduce the arm.

Reported:
- the median net Sharpe of the 485 neighbours;
- the share that are net positive;
- the arm's rank;
- one-at-a-time profiles along each axis through the default.

| bar | declared |
|---|---|
| **Q5-D** | DSR ≥ 0.95 on the primary trial set |
| **Q5-N** | "plateau" if the median neighbour's net Sharpe ≥ 0.5 × the arm's; otherwise "spike" |

## 3. Predictions

1. Longs are 52–65 % of trades.
2. The drift share is below 0.30, and Q1-T passes.
3. **Q1-H is coarser than a week:** the arm does not beat the within-week permutation by 2 SE.
4. Q3-T holds: the top |M| quintile carries more than 100 % of G, with the hit rate rising across quintiles.
5. R1d's sign agrees with the arm's direction on at least 75 % of trades.
6. Q5-D fails (DSR < 0.95) while Q5-N reads "plateau".

## 4. Reported in full (CLAUDE.md's four groups)

**For the arm:**
- net and gross side by side, Sharpe and Sortino together, exposure, σ, maximum drawdown;
- the mean move per trade against 2c, and the breakeven cost;
- the trade distribution: count, mean, median, win rate, payoff, holding run, skew, kurtosis, and the three means
  after a 1 % trim of each tail and of both;
- profitable years, the sessions needed to reach half the P&L, and the top trade named;
- the nulls as distributions (p50 and p95 with SE).

**All of it again, split long and short.** The headline is repeated at D527's measured $4.21 a round trip.

**Component line.** The arm is the ledger's only component, and this record builds no new one. Each free-running
lookback book of Q2 is a scored construction and gets its line:
- net Sharpe at one MNQ and $3.50;
- hit rate, skew, gross beside net;
- correlation with the arm's daily net.

**Power, stated before the run.**
- 1,908 trades put the SE of the hit rate at about 1.1 points; a quintile of about 380 trades puts it at about 2.6.
- Eight years carry no year-level inference: Q4 and the per-year rows are description.
- N1's spread sets the smallest timing value distinguishable from drift, and the runner prints it before G.

## 5. Runner assertions and self-test

`scripts/stage0_d669_macd_mechanism.py` (`--selftest`, `--run`) → `data/stage0_d669_macd_mechanism.json`.

**`scripts/fast_null.py` does not apply** (a label permutation over trades, not a panel rotation). Its exactness rule
stands: the permutation scorer is asserted equal to the trade-loop scorer on the unpermuted book.

**The self-test must show:**
- **the reproduction:** trade rows sum to `load_arm()` per session, 1,876 sessions and $15,423; no row after
  2023-12-29;
- **the lag audit, a second implementation:** each trade's direction equals the AGREE signal at its entry bar t, and
  its entry price equals the open of t + 1, re-derived without calling `simulate_trades`;
- **the sign audit, in money:** a long trade over a rising window pays positively and a short trade negatively;
- **the right quantity:** gross ≠ net, and the permuted G differs from the unpermuted G on a draw;
- **the permutation:** preserves every stratum's long count exactly, and its draw mean sits within 3 SE of the
  analytic drift carry;
- **the primary can fire:** an oracle book (d_i = sign(m_i)) sits above every stratum's p95, and a random-direction
  book sits near p50;
- **causality:** every lookback reads only bars ≤ t, checked by perturbing a bar after t;
- **the neighbourhood:** the default cell equals the arm exactly;
- **the deflated Sharpe:** with N = 1 it equals the probabilistic Sharpe against zero, and it falls as N rises.

**Every assertion must raise on a deliberately broken input.**

**Projected runtime:** five strata × 10,000 permutations of 1,908 labels, plus 486 simulations of 1,876 × 23 bars,
plus 81 indicator builds on the full fixture. A few minutes.
