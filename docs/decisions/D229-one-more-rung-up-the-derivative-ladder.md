# D229 — One more rung up the derivative ladder

**Status:** Pre-registered — committed BEFORE any runner exists
**Date:** 2026-08-27
**Area:** Strategy research

---

## The question

D217 and D218 established one transferable result, twice, on constructions that share no
arithmetic: **trend acceleration beats trend level.** `I1 − I2 = +0.628` long-short and
`+0.529` long-flat on Impulse MACD, against D217's `R1 − R2 = +0.285` and `+0.209` on plain
MACD.

That is a statement about a **derivative ladder**:

| rung | series | measures |
|---|---|---|
| I2 | `md` | trend **level** |
| **I1** | `hist = md − sma(md, 9)` | trend **acceleration** — the current arm |
| **I0** | `Δhist = hist[t] − hist[t−1]` | **jerk** — proposed here |

**Does the ladder keep paying one rung further up?**

The hypothesis is not mined. It is the programme's own established mechanism, extended by one
step, and it was proposed from that mechanism rather than from any number.

---

## The rung

```
score[t] = hist[t] − hist[t−1]
position = 1 if score > 0 else 0        # long-flat; ties flat
```

Memoryless, exactly as `macd.positions` writes every other rung. **No threshold.**

The proposal that prompted this was *"enter when hist is at or close to zero and increasing,
exit when it decreases."* The "close to zero" clause is dropped deliberately: it introduces a
free parameter, and it encodes nothing new, because `hist` crossing upward through zero **is**
`Δhist > 0` in the neighbourhood of zero. A threshold would buy looks, not information. If the
clean form fails, a thresholded form is not a rescue — it is a second study.

### The tie policy, stated up front because it carries more weight here

`macd.positions` treats `score == 0.0` as flat. For a level rule that is a rounding-order
curiosity. For a **difference** rule it is a live case, and the measurement below shows how
live. It is a stated policy, not an accident of floating point, and it is not revisited after
seeing the result.

### Warm-up

`impulse_warm_up_bars() + 1`. The ladder start stays at the common **1,000 bars** so all rungs
cover the same span (D217's rule — different spans are not a comparison); the extra bar the
difference needs is already inside it.

---

## What is already known, and it is measurement, not prediction

Measured before this record and stated here so it cannot be re-sold as foresight. All of it is
**free under D228's boundary** — it describes the indicator and the position series, and
touches no return.

Pooled across 57 ETFs, 86,355 live bars:

| rule | exposure | turnover | vs parent |
|---|---:|---:|---:|
| I1 `sign(hist)` | 49.93% | 4,824 | 1.00× |
| **I0 `sign(Δhist)`** | **48.53%** | **16,422** | **3.40×** |

- `md == 0.0` (the dead zone) on **11.84%** of bars
- `hist == 0.0` exactly on **3.08%**
- `Δhist == 0.0` exactly on **3.10%** — one bar in 32 is a tie, and the tie policy decides it

**Three consequences, declared in advance:**

1. **A cost headwind of roughly −0.06 Sharpe.** ~2,733 sides/yr against the parent's ~803, at
   ~1.65 bp/side on a book equal-weighted across 57 names, is about **+56 bp/yr** of extra
   cost against a 7.23% CAGR at 8.8% vol. **I0 starts in a hole and has to climb out of it.**
2. **The dividend deficit is not fixed.** Exposure moves 49.93% → 48.53%, so D228's finding
   holds — the arm still collects ~half the yield, and hurdle D fails the same way unless the
   Sharpe gain is large. The "early stop" intuition does not reduce time in market here,
   because the rule also **enters earlier**.
3. **Ties are structural.** 3.10% of bars, concentrated in the dead zone, resolved flat.

---

## The statistic — and why this study can clear a bar D218 could not

D218's absolute floor was **+1.420** and its own record says nothing on this universe can
clear it. But D218's headline result was never tested against that floor. It was tested as a
**delta between nested rungs**, against `DELTA_HURDLE = 0.10`.

That is the right statistic and it is the reason this study is worth running: nested rungs
read the **same series on the same bars**, so almost all variance is common and the difference
is estimated far more precisely than either level. **The bar is lower because the statistic is
paired, not because a new record was opened.** Multiplicity is unchanged — the 45,803
inherited looks attach to the fixture either way.

### A defect inherited from D217 and D218, fixed here

Both records state hurdle A as *"≥ +0.10 Sharpe … **above the paired bootstrap's p95**"*, and
D217 names `trade_bootstrap` as its source. Two problems:

1. **Neither runner ever called it.** `ladder_deltas` compares the point estimate to `+0.10`
   and stops. Grep confirms no bootstrap call in `run_macd_ladder.py` or
   `run_impulse_macd.py`. **The bootstrap leg of hurdle A was never computed in either study.**
2. `breakout_nulls.trade_bootstrap` is a **single-arm terminal-wealth** bootstrap over closed
   trades. It is not paired and could not have supplied that leg.

The phrasing is also unachievable as literally written: a bootstrap of the observed data
centres on the observed delta, so requiring the delta to exceed *its own* p95 is impossible by
construction.

**Made precise here, in the strict direction:** a **paired block bootstrap over the live bar
index**, block length 21 (`block_shuffle_null`'s default, repo precedent), 1,000 sims, seed 0.
Each replication resamples blocks of **dates** and recomputes **both rungs on the identical
resampled dates** — that is what makes it paired — then takes the delta.

> **Hurdle A: the p05 of the bootstrapped `I0 − I1` distribution must exceed +0.10.**

A one-sided 95% lower confidence bound above the hurdle. This is **stricter** than what D218
applied to itself, and that is deliberate: a point estimate above +0.10 with a p05 well below
it is not a result.

---

## Hurdles

- **A (carries the verdict).** `I0 − I1 ≥ +0.10` **and** bootstrap p05 `> +0.10`, at the
  primary cell.
- **D.** Beat buy-and-hold on **excess Sharpe at `rf = 4%`, charged on the exposed fraction**
  (D228's correction), *and* on dividend-adjusted total return. Expected to fail the second
  leg; reported anyway, both legs, both bases.
- **E.** ≥100 pooled signals and ≥30 entries per ETF.
- **Gross and net reported separately**, so the cost headwind is visible rather than
  entangled with the signal.

**Primary cell: `I0 / long_flat / gate = none`** — the same cell D218 named. The other three
(`long_short` × `{none, 200ma}`) are run and reported but are not the verdict.

---

## Predictions

Committed before any runner exists. The turnover, exposure and dead-zone figures above are
**measurements** and are deliberately not listed here.

| | prediction | confidence |
|---|---|---|
| **P1** | **`I0 − I1 < 0` at the primary cell** — jerk does *not* beat acceleration. Differencing an already-differenced smoothed series amplifies noise | **moderate-high** |
| **P2** | The **gross** delta is more favourable than the net by **0.04–0.09 Sharpe**, bracketing the declared −0.06 headwind | **moderate-high** |
| **P3** | I0 still **loses to buy-and-hold on dividend-adjusted money**, because exposure barely moved | **high** |
| **P4** | The bootstrap **p05 sits ≥0.15 below the point estimate**, i.e. these deltas are far less precisely estimated than D218's point-estimate-only hurdle implied | **moderate-high** |
| **P5** | **I0 beats I2** (`level`) even while losing to I1 — the ladder is not monotone but both derivative rungs beat the level rung | **moderate** |

P1 is the prediction that would hurt to be wrong about in the pleasant direction: if jerk
beats acceleration, the mechanism D217/D218 identified is stronger than either study claimed,
and P5 becomes the more interesting result.

---

## The stop

**If hurdle A fails, the derivative ladder closes at I1.** No thresholded variant, no smoothed
`Δhist`, no second signal length. The arm remains `sign(hist)` and the next question is
unmined data, not another rung.

**If hurdle A clears, it is not a result either.** It becomes a hypothesis with a mechanism
already written, and it goes to ETFs outside these 57 alongside whatever survives D228.

---

## Ledger

| count | N |
|---|---:|
| fresh — I0 × 2 books × 2 gates | **4** |
| + D218's inherited | **66** |
| + disclosed ETF prior | **45,807** |

The absolute floor at the verdict count is **expected to fail and is not the verdict** — the
paired delta is. Both are reported, and the reason the delta is the primary is stated above
rather than discovered afterwards.

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| the ladder, books, gates, costs, scoring | `arm_positions`, `score_arm`, `buy_and_hold`, `portfolio_log_returns`, `sharpe_of` | `run_macd_ladder.py` |
| the Impulse series and rungs | `impulse_macd_series`, `impulse_signal_score`, `impulse_band_score`, `positions` | `research/macd.py` |
| block length precedent | `block_shuffle_null` (block = 21) | `run_macd_ladder.py` |
| deflated Sharpe | `expected_max_sharpe` | `validation/dsr.py` |

**Written fresh:** the `I0` score (`hist[t] − hist[t−1]`, NaN-safe at the first live bar) and
the **paired block bootstrap**, which does not exist in the repo — established above, not
assumed.
