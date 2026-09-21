# D584 STAGE 0 DESIGN — **basis momentum's M1, M2 and the negative control: is the D564 book stronger in the less liquid roots, stronger in the sessions after a volatility spike, and uncorrelated with commercial hedging positioning?** Three mechanism tests on the seen in-sample book, each against an exact null of its own construction — the 24,310 splits of the 17 roots, the enumerated shift of the spike state, and declared correlation bars — with three separate verdicts; no reserved session read and no construction follows

**Stage 0 design, committed before the runner exists. Diagnostic on 2011-07 → 2023-12-29; no
session from 2024-01-01 on is read (that slice is spent for this line, D574); no cost, no book
beyond the one D564 already scored.** Nothing admitted (R15). Whatever the verdicts, no
construction follows: the basis-momentum line has no unread slice on these roots, so this record
buys knowledge of the mechanism, not a component. Run on the principal's word of 2026-09-21,
reopening one item of the D582-closed list for its stated purpose.

*2026-09-21. `BASIS_MOMENTUM.md` §3 lists seven implications of the arbitrage-loop mechanism.
M6 held (D564 P-4); M7 failed on every part (D583). Three more read only what is on disk: **M1**,
stronger in less liquid markets, "where intermediary capacity is thinner relative to flow" (§2.3);
**M2**, stronger after volatility spikes, "with a lag reflecting how quickly risk limits respond"
(§2.8); and the **§7.6 negative control**, that the book's correlation with changes in COT
commercial positioning "should be low, if the authors' claim that the effect is not hedging
pressure holds". Each has a direction written here before any number is read. The deposit's own
note says these test the mechanism, not the returns, and consume no selection budget; the D578,
D580 and D583 lessons are carried — era and years, the window sized to a profile, overlapping
placements named, and the count of years holding each state declared as a bar
([[slow-conditioners-have-n-eff-in-years]]). The §4.5 lead-lag caution is built in: every
conditioner is measured strictly before the sessions it conditions.*

**What is on disk.** The breadth fixture (D555) with hourly volume on the front-by-volume
contract for all 17 commodity roots; the settlement strip (D556); D564's machinery and artifact;
the COT fixture (`cftc_cot_raw`, legacy report, commercials' long and short and the market open
interest) for **16 of the 17 roots — BZ has no COT series**, as D573 found; the negative control
runs on those 16 and says so. The contract specifications (USD per point of the full-size
contract) in the breadth meta.

---

## 1. The quantities

- **The book.** D564's primary cell, EW High4/Low4 under `FFILL_FORMATION = 5`, rebuilt by
  D583's `build_book`; daily gross return `r_t` on the positioned sessions 2011-07-01 →
  2023-12-29. **Harness before any statistic:** its PRIMARY-window gross Sharpe equals D564's
  artifact to 1e-9 (D583: +0.692157).
- **The per-root leg return.** `c_{i,t} = held_{i,t} · r1d_{i,t}` on the root-days where root
  *i* is positioned, in bp per root-day — the root's own contribution signed by the book, free of
  the book's normalisation. Its mean over the root's positioned days is `μ_i`.
- **Liquidity (M1).** Per root, the **median session dollar volume** of the front contract over
  the positioned span: the fixture's hourly volumes summed over the session × the session close
  × the full-size USD per point. One number per root, fixed for the sample, the ranking printed
  in the RESULT before the statistic. The **8 least liquid** roots against the **9 most liquid**.
  Beside: a within-root time version, the root's trailing-252-session median dollar volume
  against its own trailing three-year median, low = below 0.8 of it (declared here).
- **The spike state (M2).** `VOL_t` = the cross-root mean of the 21-session realised volatility
  of `r1d` over the roots live at *t*. `S_t = 1` when `VOL_t` exceeds the **80th percentile of
  its own trailing 756 sessions** (at least 252 present) — a trailing threshold, no look-ahead.
  **Treated sessions** are those with `S_{t−k} = 1` for some `k ∈ [1, 21]`: the 21 sessions
  after any spike session, returns strictly after the state. The width is a hypothesis about
  the response time; the profile at lags 1–5, 6–10, …, 61–65 after each spike *entry* (the
  first ON session after ≥ 21 OFF) is reported regardless, and the "risk-limit lag" window
  6–26 is reported beside.
- **Commercial positioning (NC).** D573's `hp = long / (long + short)` of the legacy
  commercials, the mean of the last 4 reports released on or before each month-end
  (`release_date_nominal`, D573's rule, rows released before 2024-01-01 only); `ΔHP_12` its
  change over 12 month-ends (the BM lookback); and the weekly **signed commercial flow**
  `F_w = mean_i held_{i} · Δ(net_i / OI_i)` over the positioned roots, net = long − short, per
  report week.

## 2. The tests, with predictions

| # | test | statistic | predicted | falsifier |
|---|---|---|---|---|
| **M1** — less liquid markets | `Δ_LIQ = mean μ_i over the 8 least liquid − mean μ_i over the 9 most liquid`, bp per root-day; null = **every split of the 17 roots into 8 and 9, C(17,8) = 24,310, enumerated (SE 0)**; the observed split reproduces | **Δ_LIQ > 0, rank ≥ 0.95**; the Spearman of `μ_i` on the liquidity rank negative | Δ_LIQ ≤ 0 or inside the null → the loop gain does not scale with the market's depth; M1 fails |
| **M1b** (beside) | `μ` on root-months in the root's own low-liquidity state minus the rest; null = the state series shifted by k month-ends, all roots together, k = 12 … K−12, enumerated | > 0, rank ≥ 0.95 | reported; not a gate |
| **M2** — after volatility spikes | `Δ_VOL = mean r_t on treated − mean r_t on untreated`, bp/day; null = **the state series `S` shifted circularly by every offset within the positioned span (Td−1 ≈ 3,200, enumerated, SE 0)**; the zero shift reproduces; the offsets within 42 sessions overlap the window and are named; rank among the rest beside | **Δ_VOL > 0, rank ≥ 0.95**; the lag profile peaks inside 1–21 | Δ_VOL ≤ 0 or inside the null → volatility does not amplify the effect at this lag; M2 fails |
| **M2 coverage** (a bar, not a prediction) | the number of full years 2012–2023 with ≥ 21 treated sessions | **≥ 6 of 12**, else M2 is UNRESOLVED regardless of the rank | the state is too rare to test on this span |
| **M2 years** | among years with ≥ 21 treated sessions, the share with Δ_VOL > 0; eras 2011–2015 and 2016–2023 | ≥ 2/3 of those years; post-2016 not weaker | carried by two years → not a regularity; reported as PARTIAL |
| **NC1** — the signal | mean cross-sectional Spearman over month-ends of BM with `HP` and with `ΔHP_12`, year-block bootstrap SE; the mean per-root time-series Spearman beside | **|ρ| < 0.3 on both** | |ρ| ≥ 0.5 on either → basis momentum on these roots is a hedging-pressure sort in disguise (and D573 says that sort lost) |
| **NC2** — the returns | Pearson and Spearman of the weekly book return with `F_w` and with `F_{w−1}`, year-block SE | **|ρ| < 0.3 on all** | |ρ| ≥ 0.5 → the book's P&L rides the commercials' flow |

**Nulls.** M1's is the choice of roots, exact; M2's is the placement of the state in time, exact;
both are the construction's own placements. NC's bars are declared; its year-block SEs say
whether a value inside the bar is resolved. Beside them, the quarter-block bootstrap gives Δ_VOL
an SE and the era and year splits say what carries each number.

**Decision rule, declared — three verdicts, never one.**
- **M1:** SUPPORTED if Δ_LIQ > 0 at rank ≥ 0.95; NOT SUPPORTED otherwise.
- **M2:** UNRESOLVED if fewer than 6 of 12 years carry the state; else SUPPORTED if Δ_VOL > 0 at
  rank ≥ 0.95 and the year share ≥ 2/3; PARTIAL if the rank holds and the year share fails; NOT
  SUPPORTED otherwise.
- **NC:** HOLDS if every |ρ| < 0.3; FAILS if any |ρ| ≥ 0.5; UNRESOLVED between, or when a
  value inside the bar sits within 2 SE of it.

**Chance.** M1 has one direction and one exact null. M2 has one direction, one exact null, one
threshold (the 80th percentile) and one window (21 sessions), each chosen once here and never
varied except as the reported profile. NC has two bars declared before reading. Nothing is
selected on, and the three verdicts are reported however they fall.

## 3. Reported beside, diagnostic, unpromotable

The liquidity ranking with each root's median dollar volume and `μ_i`, its SE and its positioned
days; `Δ_LIQ` by era and by year, and with the split at the median (8/9) replaced by terciles
(6 / 5 / 6) as a robustness read; the `VOL_t` series' spike sessions by year, the number of
spike entries, and the lag profile; `Δ_VOL` on the as-pre-registered variant (`ffill = 1`) and
the terciles cell; the contemporaneous relation of `r_t` with `VOL_t` (§2.8's "increasing in
volatility"), reported as a level not a prediction because it regresses losses on losses; the
Spearman of the monthly book return on the prior month's `VOL`; the NC statistics by era; the
trimmed (1 % both tails) means beside each mean where a mean is compared.

**Audits, each proven to RAISE on a break that hits what the assertion reads:** (a) the harness
— PRIMARY-window Sharpe equals D564's artifact to 1e-9; break = the series rolled one session;
(b) the per-root leg return by a second path — a pandas groupby on a long-format frame of
(root, session, held, r1d), never the numpy masked mean; break = `held` shifted one session;
(c) the spike state by a second path — pandas rolling quantile of `VOL_t` against the numpy
trailing percentile; break = the state shifted one session; (d) the observed split reproduces
Δ_LIQ inside the 24,310 and the zero shift reproduces Δ_VOL inside the enumerated offsets;
(e) sign in money — a synthetic leg-return grid with +x on the 8 least liquid roots gives Δ_LIQ
> 0 at rank 1.0 and its negation < 0; a synthetic series with +x on the 21 sessions after
synthetic spikes gives Δ_VOL > 0 at rank 1.0 and its negation < 0; (f) the COT read by D573's
own second path (`hp_cells_pandas` against `hp_at_month_ends`) on 50 seeded cells; (g)
correlation known-answer — ρ of HP with itself is 1 and with a permuted copy is within 0.05 of
0; (h) right quantity — the two root sets are disjoint and cover the 17; treated and untreated
sessions are disjoint and cover the positioned span; `REQUIRED_OUTPUTS` guard first.

## 4. What is read, and what is not

The breadth fixture (closes and hourly volumes) and the settlement strip to 2023-12-29 for the
17 commodity roots; the COT fixture's legacy commercial rows released before 2024-01-01 for the
16 roots it carries; the contract specifications; D564's artifact. **Not read: any session,
settlement, volume or COT release from 2024-01-01 on.** **Seen-ness declared:** the book's
daily returns on 2011–2023 were read by D564, D574 and D583; this record reads them again
conditioned on three quantities the mechanism named in advance.

## 5. What this record does not do

It does not run M3 (a maturity decomposition, a construction choice), M4 (the He–Kelly–Manela
capital ratio, a fetch — the test that would separate a wrong mechanism from a wrong instrument
after D583, and still not recommended because nothing on this line could use the answer) or M5
(inventories, a fetch with point-in-time alignment). It does not build any liquidity- or
volatility-conditioned construction, on this line or another; it does not vary the spike
threshold, the window or the split. It does not read the funding or option fixtures.

**Runtime.** The book takes D583's three seconds; the 24,310 splits are means over 17 numbers;
the ~3,200 shifts are masked means over ~3,200 sessions; the COT read is D573's. Under a minute.
