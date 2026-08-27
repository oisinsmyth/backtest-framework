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

**Produced:** 2026-08-27 · **Reproduce:** `uv run python scripts/run_etf_intraday_gate.py`
(offline, deterministic, seed 0) · Record: **D226**, pre-registered; the
pre-registration is restated in the runner's module docstring · Artifact:
`data/etf_intraday_gate_summary.json`

57 ETFs · 15m bars · Impulse acceleration `(136, 36)` long-flat, lag 1 · gate `EMA(w) > SMA(w)` on VOLUME at the ENTRY bar only · **PPY = 6,552** (26 bars x 252 sessions).

Panel: **55,726 bars** inner-joined on timestamp from raw counts [55778, 56034, 56043, 56053, 56054, 56055, 56056] · 2018-01-02 09:30:00 .. 2026-08-26 15:45:00 · warm-up 4,049 bars, leaving 51,677 live · 1,955 dividends matched (0 unmatched), 12 of 12 recorded splits verified absent from the prices · median cost 1.69 bp per side at $175,439 a name.

### The parent, and the space a gate has to work in

`Impulse(136, 36)` long-flat: **20,186 trades**, win rate **37.72%**, mean win 2.25% against mean loss -1.24%, median hold 56 bars, exposure 49.67%. Minimum 326 entries on the thinnest ETF, median 356.

| base | Sharpe | total return | max drawdown |
|---|---:|---:|---:|
| dividend adjusted | +0.307 | 24.93% | -17.97% |
| price only | +0.199 | 15.54% | -18.19% |

**ORACLE** — remove the worst k% of trades by realised PnL. Look-ahead by
construction, never a strategy (D181), and the ceiling for ANY gate at that
removal count.

| remove | n | ORACLE Sharpe | ORACLE total | (price-only Sharpe) |
|---:|---:|---:|---:|---:|
| 10% | 2,019 | +2.421 | 344.45% | +2.301 |
| 20% | 4,037 | +3.587 | 712.75% | +3.468 |
| 30% | 6,056 | +4.413 | 1106.73% | +4.302 |
| 50% | 10,093 | +5.470 | 1731.88% | +5.372 |

### The sweep — dividend-adjusted (primary)

| window | hours | removed | Sharpe | total | ORACLE Sh | null p50 / p95 | pct in null (Sh / $) | capture Sh | perm |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 48 | 12 | 9,037 (45%) | +0.239 | 10.83% | +5.271 | +0.302 / +0.434 | 24 / 28 | -1% | 27 |
| 96 | 24 | 9,601 (48%) | +0.467 | 20.34% | +5.386 | +0.295 / +0.435 | 98 / 98 | +3% | 98 |
| 144 | 36 | 9,413 (47%) | +0.368 | 16.95% | +5.351 | +0.304 / +0.434 | 79 / 86 | +1% | 87 |
| 200 * | 50 | 8,765 (43%) | +0.288 | 14.52% | +5.213 | +0.299 / +0.438 | 45 / 62 | -0% | 63 |
| 288 | 72 | 8,792 (44%) | +0.392 | 20.46% | +5.218 | +0.305 / +0.438 | 87 / 95 | +2% | 96 |
| 400 | 100 | 9,431 (47%) | +0.314 | 15.22% | +5.353 | +0.299 / +0.438 | 57 / 74 | +0% | 77 |
| 560 | 140 | 9,544 (47%) | +0.008 | 0.40% | +5.375 | +0.306 / +0.440 | 0 / 0 | -6% | 0 |
| 800 | 200 | 9,356 (46%) | +0.176 | 10.02% | +5.339 | +0.302 / +0.437 | 6 / 22 | -3% | 24 |
| 1,200 | 300 | 9,634 (48%) | +0.320 | 18.52% | +5.392 | +0.297 / +0.428 | 59 / 96 | +0% | 96 |
| 1,920 | 480 | 9,522 (47%) | +0.209 | 12.18% | +5.371 | +0.308 / +0.436 | 12 / 42 | -2% | 46 |

`*` = **200**, D224's committed `VOL_WINDOW` and the point D225 found the effect inverts at.
`capture` is the fraction of the ORACLE-minus-random-median space the gate took,
at its own removal count. `perm` is the label-permutation percentile: the removed
set's mean PnL against the kept set's, holding the trade population and the
removal count fixed.

### The sweep — price-only (the same books, dividends withheld)

| window | Sharpe | total | pct in null (Sh / $) | H |
|---:|---:|---:|---:|:--:|
| 48 | +0.137 | 6.04% | 25 / 28 | FAIL |
| 96 | +0.363 | 15.49% | 98 / 98 | PASS |
| 144 | +0.268 | 12.08% | 80 / 86 | FAIL |
| 200 | +0.188 | 9.26% | 47 / 59 | FAIL |
| 288 | +0.290 | 14.75% | 89 / 94 | FAIL |
| 400 | +0.209 | 9.88% | 57 / 68 | FAIL |
| 560 | -0.093 | -4.37% | 0 / 0 | FAIL |
| 800 | +0.085 | 4.72% | 9 / 16 | FAIL |
| 1,200 | +0.237 | 13.38% | 70 / 93 | FAIL |
| 1,920 | +0.141 | 8.04% | 23 / 47 | FAIL |

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
| 48 | 11,149 | PASS | 162 | PASS | PASS |
| 96 | 10,585 | PASS | 154 | PASS | PASS |
| 144 | 10,773 | PASS | 158 | PASS | PASS |
| 200 | 11,421 | PASS | 168 | PASS | PASS |
| 288 | 11,394 | PASS | 169 | PASS | PASS |
| 400 | 10,755 | PASS | 166 | PASS | PASS |
| 560 | 10,642 | PASS | 158 | PASS | PASS |
| 800 | 10,830 | PASS | 170 | PASS | PASS |
| 1,200 | 10,552 | PASS | 165 | PASS | PASS |
| 1,920 | 10,664 | PASS | 161 | PASS | PASS |

### Hurdle G — the multiplicity floor

**`var_trials` is taken from the simulated null, not from this study's own
cells.** D219's amendment recorded that a sweep containing real effects inflates
it; D224 showed the inflation is not marginal. The matched-count null IS the null
distribution, so its variance is the right estimate, and it is a DIFFERENT
estimate at every window because every window removes a different count.

| window | Sharpe | null sd | floor @ 10 (fresh) | floor @ 45,819 (verdict) | G |
|---:|---:|---:|---:|---:|:--:|
| 48 | +0.239 | 0.082 | +0.130 | +0.348 | FAIL |
| 96 | +0.467 | 0.082 | +0.129 | +0.347 | PASS |
| 144 | +0.368 | 0.083 | +0.130 | +0.349 | PASS |
| 200 | +0.288 | 0.078 | +0.123 | +0.330 | FAIL |
| 288 | +0.392 | 0.081 | +0.128 | +0.343 | PASS |
| 400 | +0.314 | 0.082 | +0.130 | +0.347 | FAIL |
| 560 | +0.008 | 0.083 | +0.130 | +0.348 | FAIL |
| 800 | +0.176 | 0.081 | +0.128 | +0.342 | FAIL |
| 1,200 | +0.320 | 0.084 | +0.132 | +0.354 | FAIL |
| 1,920 | +0.209 | 0.083 | +0.130 | +0.349 | FAIL |

### Verdict

| window | H | E | P (> parent) | G | **survives** |
|---:|:--:|:--:|:--:|:--:|:--:|
| 48 | FAIL | PASS | FAIL | FAIL | FAIL |
| 96 | PASS | PASS | FAIL | PASS | FAIL |
| 144 | FAIL | PASS | FAIL | PASS | FAIL |
| 200 | FAIL | PASS | FAIL | FAIL | FAIL |
| 288 | FAIL | PASS | FAIL | PASS | FAIL |
| 400 | FAIL | PASS | FAIL | FAIL | FAIL |
| 560 | FAIL | PASS | FAIL | FAIL | FAIL |
| 800 | FAIL | PASS | FAIL | FAIL | FAIL |
| 1,200 | FAIL | PASS | FAIL | FAIL | FAIL |
| 1,920 | FAIL | PASS | FAIL | FAIL | FAIL |

**1 of 10 windows clear hurdle H. 0 clear every hurdle.**

- Windows clearing H: [96].
- D224's committed 200: H FAIL, survives no.
- The clearing region is contiguous: **no**, width 1 of 10 grid points.

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
derived at $175,439 a name — and it was derived for
DAILY rebalancing. At 15 minutes the half-spread is the optimistic part of that
estimate; it is charged per side on every unit of exposure changed either way.
