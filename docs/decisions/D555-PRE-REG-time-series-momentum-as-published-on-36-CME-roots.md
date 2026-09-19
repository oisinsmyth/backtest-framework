# D555 — PRE-REGISTRATION: time-series momentum **as published** (Moskowitz–Ooi–Pedersen 2012) on the 36-root breadth fixture, checked against AQR's own series

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.**
**In sample 2016-01-04 → 2023-12-29 (the ledger's window). The long window 2011-01-03 → 2023-12-29
is a declared diagnostic. The 2024+ slice is RESERVED AND NOT READ.** Nothing admitted (R15).

*2026-09-19. First study taken from the deposit folder (`docs/internal/User-Doc-Deposit/`,
`PUBLISHED_STRATEGIES.md` §2 and §10). The principal chose to examine the deposit's programme and
to set aside its conflicts with this repository's record; the deposit's own instruction is that
TSMOM is replicated **first**, because "if the harness cannot reproduce trend and carry, it cannot
be trusted on anything else." This record is therefore two things at once: a calibration test of
the futures data layer against a published, free benchmark series, and a scored construction that
gets a component line like every other.*

---

## 0. The construction — one, fixed from the paper, nothing tuned

| | |
|---|---|
| **fixture** | `data/fixtures/fut_breadth_hourly.csv.gz` (36 roots, 2010-06-07 → 2026-09-09, front month by full-day volume; D520/D524 windowed ids) |
| **daily close** | the last finite hourly close in the session row, h18 → h16 in session order — each root's own session, never a template hour |
| **daily return** | `log(C_t / C_{t−1})` when `same_front` is true; **`log(C_t / O_h18,t)` on a front-change session** — every row is one contract, so the return never crosses a roll gap; the price paid is the 17:00→18:00 maintenance gap on each front change (65 sessions in 16 years on a quarterly root) |
| **signal** | at each **month-end session** m: sign of the sum of daily log returns over the trailing **12 calendar months** (sessions in (m−12 months, m]); requires ≥ 240 returns in the window, else flat |
| **ex-ante volatility** | MOP's exponentially weighted variance, centre of mass **60 days** (δ = 60/61), annualised by 261, with the EW mean subtracted; read at the month-end session |
| **position, published book** | `sign × 0.40 / σ_i`, set at the month-end and **held unchanged** until the next month-end (MOP; not HOP's daily re-scaling) |
| **portfolio, published book** | equal-weighted average over the roots live that month of each root's scaled return — MOP's "diversified TSMOM"; its own vol is whatever it is, the Sharpe is the object |
| **execution lag** | the position decided at month-end m earns from session m+1; there is no same-day fill |

Futures returns are excess returns; no financing is added and no collateral yield is credited.

**Lookbacks scored beside the primary, all published in HOP 2017:** 1-month, 3-month, the equal
ensemble of 3+12, and the equal ensemble of 1+3+12 (an ensemble averages the three signed,
scaled positions). The deposit says drop the 1-month; it is scored here so that HOP's own report
of its death (gross Sharpe 0.06 on 2010–2016) is a checkable prediction, not an inherited one.

## 1. Universe and live spans — from the fixture, on a non-return criterion

All **36** roots. A root is live from the first calendar year from which every year through 2025
carries ≥ 240 sessions with a finite close: **2011 for 32 roots; TN 2016; BTC and RTY 2018;
SR3 2019.** TN's 2010–2012 rows (47/187/25 sessions, then nothing to 2015) are excluded by that
rule and never read. A root with fewer than 240 daily returns in its trailing 12 months is flat.

**Two roots are excluded from the DOLLAR book only, on roll count:** BZ (802 front changes) and
SR3 (1,273) change front by volume more than twice a month, so "hold the front" is not a holdable
instruction under this fixture's front rule; every other root changes front 38–315 times in 16
years. They stay in the return-space book, where the within-contract return chain is a legitimate
volume-rule stitch. The rule is declared on the roll count, which is not a return.

## 2. The statistic

> **PRIMARY: gross annualised Sharpe of the published 12-month book's daily return, 2016-01-04 →
> 2023-12-29.** Sharpe = mean/sd × √252 on the daily series, with a monthly block-bootstrap SE.

**Family (the declared unit of selection): 10 cells** — {12m, 3m, 1m, 3+12, 1+3+12} ×
{published return-space book, dollar book at minimum size}. The primary is one of them and is
fixed here. Per-root, per-sector, per-era and per-year figures are **diagnostic and unpromotable**.

## 3. Nulls — exact, enumerated

**N1 — sign rotation, enumerated.** For each offset k in 1 … L−1 (L = sessions in the scored
window, ≈ 2,000 on the primary window), each root's **sign series** is rotated cyclically by k
**within that root's own live span** (k mod L_i for the four short roots) and re-multiplied by
the **in-place** vol scale `0.40/σ_i,t` and the in-place live mask. This destroys the alignment
between the trailing-12-month read and the month that follows it and nothing else: the sizing,
the return distribution, the cross-root correlation and the monthly holding structure all
survive. The offset is common to all roots and to all ten family cells. **Every offset is
scored, so the p95 carries SE exactly 0** (CLAUDE.md, *Reporting a result* §4).

**N2 — the family maximum**: at each offset, the best Sharpe across the 10 cells.

**PASS requires: the primary > 0, above its N1 p95, AND the family maximum above its N2 p95.**
p50 and p95 are reported beside the score. The null is decisive if the observed sits outside
[p05, p95]; a margin under 2 SE cannot arise because the SE is 0.

**Exactness guard.** The enumeration is checked bit-identical against a plain loop over the
rotated book on 20 offsets before any percentile is printed.

## 4. Predictions — in the runner's own quantities, checkable from what this record holds

| # | prediction | source |
|---|---|---|
| **P-1** (primary) | gross Sharpe of the 12m published book, 2016–2023: **> 0, above N1 p95**; point prediction **0.4 – 0.8** | HOP 2010–2016 12m gross 0.73; the deposit's universe haircut (effective N ≈ 4–5 against 8–10) |
| **P-2** (the harness check) | monthly correlation of the 12m published book with AQR's *Time Series Momentum: Factors, Monthly* (all assets) over **2011-01 → 2023-12** (156 months): **≥ 0.5**; point prediction **≈ 0.7** | same paper, same construction, 36 roots against ~58 |
| **P-3** (ordering) | on 2016–2023, gross Sharpe **12m > 3m > 1m**, and **1m < 0.3** | HOP by-signal 2010–2016: 0.73 / 0.30 / 0.06 |
| **P-4** (breadth) | 12m gross P&L positive on **≥ 21 of 34** roots live across 2011–2023 (P ≥ 21 of 34 under a coin ≈ 8.5%) | MOP: positive on 58 of 58 over 25 years; 13 years of a decayed effect earns a lower bar |
| **P-5** (component) | dollar book at minimum size, net of the declared cost, 2016–2023: net Sharpe **0.3 – 0.7**, gross − net **< 0.1**; the full dollar book **fails C-d** (daily σ > $500) | monthly rebalancing: ~15 round trips a root a year; ZB alone carries σ ≈ $700 a day (D468) |
| **P-6** (era, diagnostic) | of the three eras 2011–2015 / 2016–2019 / 2020–2023, **2016–2019 is the weakest** (gross Sharpe < 0.3) and **2020–2023 the strongest** | HOP's weakest decade; 2022 |
| **P-7** (falsifier) | if the primary is **below its N1 p50** while P-2 **holds**, trend did badly on this universe and window and the harness is fine. If P-2 **fails** (ρ < 0.5), **the data layer or the construction is wrong** and the Sharpe is uninterpretable — the record then reports the layer diagnosis, not the Sharpe | the deposit's reading of a failed replication |

A Sharpe above the prediction range is reported as a miss of the prediction, not as a better result.

## 5. Cost line — both lenses, declared before the run

**Published book (return space):** cost per side, in basis points of notional, per root per
session = `(commission/2 + 0.5 × tick_usd) / (price × usd_per_point)` at the minimum tradable
size; turnover = `Σ_i |w_i,t − w_i,t−1|` in notional units, charged at that rate. Reported: gross
and net Sharpe side by side, annual turnover, and the **breakeven cost in bp/side**.

**Dollar book (component line):** one minimum-size contract per root per sign — the micro where
one exists (MES MNQ M2K MYM MCL MGC M6E MBT SIL MNG MHG, from `data/futures_contract_specs.json`),
one full contract otherwise. P&L = `sign × (C_t − C_{t−1}) × usd_per_point` (same-contract, so
`(C_t − O_h18,t)` on a front change). Cost = **$3.00 a round trip on a micro, $6.00 on a full
contract (D468's convention), plus one tick crossed at the minimum-size tick value**, charged on
every sign change **and on every front change** (a roll is a round trip). Reported: gross and net
Sharpe with SE, hit rate, skew, daily σ (C-d), and ρ with the ledger's live entry (the MACD arm,
D504's daily P&L if on disk, else stated absent). The full 34-root dollar book and the sub-book of
roots that individually clear C-d are both reported; neither is chosen after the fact.

## 6. Runner assertions — all three, and each proven to fire

1. **Lag audit.** A second implementation, pandas month-end resampling → rolling 12-month sum →
   sign → shifted one month → reindexed to sessions, never calling the runner's signal function,
   must reproduce the held sign grid **exactly**; the self-test feeds the audit an **unlagged**
   grid and asserts it raises.
2. **Sign audit, in money.** On the session with the largest positive same-contract move in each
   root, a +1 position must contribute a positive dollar P&L equal to `ΔP × usd_per_point`; the
   self-test flips the book and asserts it raises.
3. **Right quantity.** The held sign grid changes value on no session that is not the first
   session after a month-end; the daily-rebalanced sign grid changes on more; the self-test hands
   the audit the daily grid and asserts it raises. And the scored P&L series differs from the
   unlagged one.

`REQUIRED_OUTPUTS` is declared in the runner and the runner raises before writing if any is
missing (memory: *declared outputs need a guard*).

## 7. What is read, and what is not

- The fixture from 2010-06-07 for signal warm-up; **scored from 2011-01-03 (diagnostic) and
  2016-01-04 (primary) through 2023-12-29**.
- AQR's monthly factor file, fetched 2026-09-19 (HTTP 200, 139,830 bytes), kept in
  `data/raw/aqr/` (gitignored, licensed) with its sha256 in the result; only statistics are
  committed, never the series. Its 2024+ months are **not** correlated against anything.
- **Not read: any session from 2024-01-02 onward.**

## 8. What this record does not do

It does not test carry, does not sweep a lookback, does not fit a vol target, and does not choose
a universe after seeing per-root results. If the harness check passes and the primary fails, that
is the finding: the published effect on this universe and window, at this construction, is what
it is — and the deposit's own discount ("expect half the published Sharpe") is what gets checked.
