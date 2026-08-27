# ETF INTRADAY RESULTS — the volume regime gate off its home fixture (D226)

The results ledger for D226. **Its own file, deliberately.** `MACD_RESULTS.md`'s
appenders splice around a parking-lot anchor and would have to rewrite that
document to take this section; the D218 and D220 sections live there and are not
worth the risk. This study also does not share a fixture, a bar size or a
calendar with anything in that ledger.

**Inherited disclosure.** D226 does not open a fresh ledger. It is the third look
at one mechanism — D224 proposed the gate, D225 found its window one point wide
and inverting — so the verdict count carries D224's declared 3,833 plus D225's 36
plus this study's 10 windows.

## D226 — the volume regime gate on 57 ETFs at 15 minutes

> **SMOKE RUN — NOT THE STUDY.** A reduced universe and a reduced grid, run
> only to prove the code path executes. No number below is a result.

**Produced:** 2026-08-27 · **Reproduce:** `uv run python scripts/run_etf_intraday_gate.py`
(offline, deterministic, seed 0) · Record: **D226**, pre-registered; the
pre-registration is restated in the runner's module docstring · Artifact:
`data/etf_intraday_gate_summary.smoke.json`

3 ETFs · 15m bars · Impulse acceleration `(136, 36)` long-flat, lag 1 · gate `EMA(w) > SMA(w)` on VOLUME at the ENTRY bar only · **PPY = 6,552** (26 bars x 252 sessions).

Panel: **56,056 bars** inner-joined on timestamp from raw counts [56056] · 2018-01-02 09:30:00 .. 2026-08-26 15:45:00 · warm-up 4,049 bars, leaving 52,007 live · 224 dividends matched (0 unmatched), 12 splits recorded and verified absent from the prices · median cost 1.48 bp per side at $3,333,333 a name.

### The parent, and the space a gate has to work in

`Impulse(136, 36)` long-flat: **1,083 trades**, win rate **37.30%**, mean win 1.38% against mean loss -0.76%, median hold 54 bars, exposure 49.10%. Minimum 340 entries on the thinnest ETF, median 371.

| base | Sharpe | total return | max drawdown |
|---|---:|---:|---:|
| dividend adjusted | +0.220 | 14.19% | -16.90% |
| price only | +0.067 | 4.11% | -18.73% |

**ORACLE** — remove the worst k% of trades by realised PnL. Look-ahead by
construction, never a strategy (D181), and the ceiling for ANY gate at that
removal count.

| remove | n | ORACLE Sharpe | ORACLE total | (price-only Sharpe) |
|---:|---:|---:|---:|---:|
| 10% | 108 | +1.868 | 158.95% | +1.688 |
| 20% | 217 | +2.767 | 277.91% | +2.602 |
| 30% | 325 | +3.341 | 378.91% | +3.182 |
| 50% | 542 | +3.972 | 509.11% | +3.835 |

### The sweep — dividend-adjusted (primary)

| window | hours | removed | Sharpe | total | ORACLE Sh | null p50 / p95 | pct in null (Sh / $) | capture Sh | perm |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 200 * | 50 | 464 (43%) | +0.141 | 6.39% | +3.806 | +0.171 / +0.551 | 44 / 46 | -1% | 44 |
| 400 | 100 | 502 (46%) | +0.360 | 16.57% | +3.889 | +0.185 / +0.522 | 80 / 82 | +5% | 83 |

`*` = **200**, D224's committed `VOL_WINDOW` and the point D225 found the effect inverts at.
`capture` is the fraction of the ORACLE-minus-random-median space the gate took,
at its own removal count. `perm` is the label-permutation percentile: the removed
set's mean PnL against the kept set's, holding the trade population and the
removal count fixed.

### The sweep — price-only (the same books, dividends withheld)

| window | Sharpe | total | pct in null (Sh / $) | H |
|---:|---:|---:|---:|:--:|
| 200 | +0.010 | 0.44% | 42 / 42 | FAIL |
| 400 | +0.207 | 9.22% | 76 / 77 | FAIL |

Reported because D217's addendum turned a tie into a 17-point loss the moment
dividends were put back, and a gate whose verdict depends on which base it is
read at has not shown anything. Bases agree on hurdle H at every window: **yes**.

### Hurdle E — powered, both legs

The ORIGINAL conjunction: **>= 100 pooled trades AND >= 30 entries per ETF**. Both legs shown so a failure can
be attributed to the leg that caused it — a gate can keep thousands of pooled
trades while starving the thinnest ETF below the point where its column means
anything.

| window | pooled trades | >= 100 | min entries / ETF | >= 30 | **E** |
|---:|---:|:--:|---:|:--:|:--:|
| 200 | 619 | PASS | 199 | PASS | PASS |
| 400 | 581 | PASS | 183 | PASS | PASS |

### Hurdle G — the multiplicity floor

**`var_trials` is taken from the simulated null, not from this study's own
cells.** D219's amendment recorded that a sweep containing real effects inflates
it; D224 showed the inflation is not marginal. The matched-count null IS the null
distribution, so its variance is the right estimate, and it is a DIFFERENT
estimate at every window because every window removes a different count.

| window | Sharpe | null sd | floor @ 10 (fresh) | floor @ 3,879 (verdict) | G |
|---:|---:|---:|---:|---:|:--:|
| 200 | +0.141 | 0.223 | +0.350 | +0.806 | FAIL |
| 400 | +0.360 | 0.215 | +0.338 | +0.778 | FAIL |

### Verdict

| window | H | E | P (> parent) | G | **survives** |
|---:|:--:|:--:|:--:|:--:|:--:|
| 200 | FAIL | PASS | FAIL | FAIL | FAIL |
| 400 | FAIL | PASS | PASS | FAIL | FAIL |

**0 of 2 windows clear hurdle H. 0 clear every hurdle.**

- Windows clearing H: none.
- D224's committed 200: H FAIL, survives no.
- The clearing region is contiguous: **no**, width 0 of 2 grid points.

**The D225 reading.** A gate that clears H in a contiguous band across a grid
spanning a factor of forty is a real scale. A gate that clears H at one isolated
point, or at scattered points, on 57 instruments from a different asset class is
the shape of noise, and D224/D225's two-coin result should be read as such.

### The disclosure that belongs beside the verdict, not in a footnote

**ETF volume is a weak instrument.** ETF liquidity comes from the
creation/redemption mechanism and the underlying basket, so on-exchange volume is
a poor proxy for interest — a quiet tape can simply mean the authorised
participants did not need to trade. A NEGATIVE result here is therefore **weaker
evidence against the gate as a concept** than the same result on single names or
crypto would be. A positive is not weakened by it at all.

**The costs are the daily study's costs.** `per_side_bps` is the IBKR schedule at
each ETF's median close plus a 1 bp half-spread,
derived at $3,333,333 a name — and it was derived for
DAILY rebalancing. At 15 minutes the half-spread is the optimistic part of that
estimate; it is charged per side on every unit of exposure changed either way.
