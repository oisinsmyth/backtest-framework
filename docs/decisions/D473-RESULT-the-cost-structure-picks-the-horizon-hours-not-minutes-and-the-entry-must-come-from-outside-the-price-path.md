# D473 — RESULT: the cost structure picks the horizon (hours, not minutes), and the entry must come from outside the price path

**2026-09-12.** Runner [`scripts/d473_optimal_horizon.py`](../../scripts/d473_optimal_horizon.py) ·
artifact [`data/d473_optimal_horizon.json`](../../data/d473_optimal_horizon.json)

**A COST-GEOMETRY CALCULATION, NOT A STUDY.** No entry rule, no signal, no forecast, no
backtest. It answers a **conditional**: *if* a rule had directional accuracy `a` above a coin
flip, what holding period maximises Sharpe and what Sharpe would that be. Nothing is opened,
closed or admitted ([R15](../RULES.md#r15)). **No rule may be scored off this without a
pre-registration ([R8](../RULES.md#r8)).**

The question this answers is the principal's: *what sort of entry rule could work.* Most of the
answer turns out to be arithmetic, and the arithmetic rules out more than it admits.

---

## 1. The cost structure picks the horizon, and there is a closed form

Cost is **fixed per round trip** (3.409 MES ticks) so a longer hold amortises it; but a longer
hold means **fewer trades** and Sharpe scales with √count. CLAUDE.md names the trap: *"a longer
hold lifts breakeven by amortising one round trip; per-bar edge usually FALLS, so Sharpe can
drop as cost coverage rises."* Resolving both at once:

    Sharpe(h) ∝ a/√h − C/(2k·h)      with E|M|(h) = k·√h

    dSharpe/dh = 0   ⟹   **E|M|(h*) = C / a**   ⟹   **p_be(h*) = ½ + a/2**

**The optimum is where the mean absolute move equals cost divided by skill — equivalently,
where you are running at exactly twice the breakeven excess.** Verified against a numerical
argmax of the exact (non-asymptotic) Sharpe at three skill levels, agreeing to 0.02%.

And the last self-test check is the one that explains *why* an optimum exists at all: **at zero
cost, shorter is always better and there is no interior optimum.** The horizon question is
created entirely by the fixed fee.

## 2. Measured on the in-sample window

ES RTH, 2016-01-04 → 2023-12-29, non-overlapping single-contract windows:

| horizon | windows | E\|M\| ticks | RMS | trades/yr | **breakeven accuracy** |
|---|---:|---:|---:|---:|---:|
| 5 min | 155,754 | 8.01 | 13.12 | 19,656 | **71.27%** |
| 15 min | 51,918 | 13.73 | 22.14 | 6,552 | **62.41%** |
| 30 min | 25,957 | 19.55 | 31.40 | 3,276 | 58.72% |
| 60 min | 11,982 | 27.24 | 42.52 | 1,638 | 56.26% |
| 120 min | 5,991 | 39.01 | 60.52 | 819 | 54.37% |
| 195 min | 3,990 | 53.05 | 81.79 | 504 | 53.21% |
| 390 min (session) | 1,993 | 78.07 | 116.52 | 252 | **52.18%** |

`E|M| ≈ 3.36·h^0.520` — a random walk is 0.5, and D469 fitted 0.50 independently on tick data.

## 3. The answer, conditional on skill

| skill `a` | accuracy | E\|M\| wanted | **optimal horizon** | p_be there | **Sharpe** | Sharpe at 15 min |
|---:|---:|---:|---|---:|---:|---:|
| 1.0% | 51.0% | 341 tk | 18.4 sessions | 50.5% | 0.02 | **−11.46** |
| 2.0% | 52.0% | 170 tk | 4.9 sessions | 51.0% | 0.09 | **−10.46** |
| 3.0% | 53.0% | 114 tk | 2.2 sessions | 51.5% | 0.20 | −9.46 |
| **5.0%** | **55.0%** | 68 tk | **325 min** | 52.5% | **0.55** | −7.46 |
| 7.5% | 57.5% | 45 tk | 149 min | 53.8% | 1.23 | −4.95 |
| 10.0% | 60.0% | 34 tk | 86 min | 55.0% | 2.17 | −2.44 |

**Three things fall out of that table.**

**(a) The 15-minute horizon is dead, and not marginally.** Its in-sample breakeven is 62.41%, so
**even a 60%-accurate rule loses money there** (Sharpe −2.44). 15 minutes is the optimal horizon
only near **a = 24.8%, i.e. 74.8% accuracy.** The thread that started at "15 minutes looks
doable" ends here: it looked doable only because D469 measured a recent, high-price,
high-volatility year (D472 §2).

**(b) C-a's Sharpe > 0.5 wants ≈5 percentage points of skill held ≈5 hours.** That is the
specification a candidate entry has to hit: **55% directional accuracy on a most-of-a-session
hold.** Not 62% on fifteen minutes.

**(c) Multi-day horizons lower the accuracy bar but cannot deliver C-a.** At 2% skill the
optimum is 4.9 sessions for Sharpe **0.09** — the trade count is too low. There is a floor on
how little skill can be made to work, and it is around 3–5%.

## 4. What the measurements RULE OUT for an entry — and this is the useful half

**The price path itself carries nothing.** D471 AMENDMENT 1 and 2: the variance ratio is
**0.82–1.02 across five time grids and four volume grids, never above 1.02**. ES has no trend
structure at intraday scale on either clock. So **breakout, momentum and trend-continuation
entries on ES's own intraday price have no raw material** — that is measured, not argued.

**Path-shape filters are dead.** Path efficiency fails as a conditioner on two clocks, nine
sampling rates, two window lengths (ρ never past 2.5 SE, sign unstable).

**And "let winners run, cut losers short" is provably neutral, not merely unproven.** For a
driftless walk a W/L bracket has `P(hit +W before −L) = L/(W+L)` **exactly** — simulated here at
three bracket shapes, matching to 3 decimals, expected gross within ±0.06 ticks of zero every
time. **Asymmetry buys nothing for free**; the hit rate adjusts precisely to offset the payoff.
Only the **sum** W+L helps, and only through the same fixed-cost channel as a longer horizon
(the required excess is `cost/(W+L)`). Skew is a risk-shaping choice, not an edge.

## 5. What is NOT ruled out

Since the price path is a random walk at this scale, **direction has to come from outside the
price path.** That is the structural conclusion, and it is consistent with the only thing on
this track that has ever worked:

- **Clock and session structure.** The price path carries nothing but the *clock* does. C1 /
  K1 — an overnight hold — is exactly this, and is the best result the prop track has (net
  Sharpe **+0.37** at micro size, D466), sitting naturally in the hours-to-a-session zone §3
  points at. D466's K2 (last 30 minutes of NQ) is the same family. **This is the class with
  actual evidence behind it.**
- **Volatility state, for TIMING and not direction.** The one forecastable quantity measured
  anywhere in this sequence (ρ = +0.31 wall clock, +0.14 volume clock). It cannot tell you
  which way, but it raises E|M| and therefore lowers the bar — D469's 57.5% → 54.8%.
- **Cross-instrument and lead-lag.** Untested here; 41 roots and 16 years of `ohlcv-1m` are on
  disk for it.
- **Calendar and event structure.** `definition` and `statistics` cover 16 years and have never
  been read for this.
- **Order-flow imbalance.** `mbo` is on disk, but only ~1 month, and it speaks to short
  horizons — which §3 says are the ones cost forbids. Weakest of the five on this arithmetic.

## 6. Limitations, all in the artifact

1. **Sub-session rows are measured; multi-session rows are EXTRAPOLATED** through the fitted
   exponent from an RTH-only fixture, which also omits overnight moves. The 18.4- and
   4.9-session rows are the least reliable in the file, and they are conservative for that
   reason.
2. **The ±|M| model assumes the rule captures the full move signed by its call** — an upper
   bound on any exit rule, so every Sharpe here is optimistic.
3. **Skill is assumed constant across horizons.** This is the strongest assumption in the file
   and is almost certainly false; it is what makes §3 a *conditional* rather than a forecast.
4. Trades assumed independent and always-in; a selective rule trades less and scales by √(its
   own count). No slippage beyond the measured half-spread, no queue position.

## 7. What this does not do

- **It proposes no entry rule and scores none.** It states the specification any candidate must
  meet (§3b) and eliminates three families on measurement (§4).
- **It does not close the 15-minute horizon or any other** — R15. §3a is arithmetic about a
  cost structure, and a construction that broke the ±|M| model's assumptions would sit outside
  it.
- **Nothing is elevated** into `FINDINGS.md`, `RULES.md` or either book, and nothing is entered
  in `COMPONENTS_PROP.md`.
