# D353 — `rev_5` entering the bottom decile: the full record on the event lens, and the slot-capped event book with a hedged capital series

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. Nothing here is a book: the output is a candidate-trigger record for the pair book,
with its cost stated both ways.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D350 screened 138 long events and, under the corrected control, `rev_5` entering the bottom
decile was the cleanest signal on the programme's event record: +43.4 bp a trade, t = 4.8 on
27,316 trades, mean equal to median, profitable in ten of fourteen years, top trade 1.3% of
P&L, above A′, B and C. It was one of 138 looks with 100 control draws. This record gives it
the full design D347 gave its signals, at 200 draws, with every exit, both hedges, the four
groups, and — new — the slot-capped event book scored on a **hedged** capital series, which
D345's retry asked for and no record has yet built.

## 1. The event

`rev_5` — the trailing five-bar sum of log returns — floored, deal-filtered, on the warm base,
lagged, as a cross-sectional percentile `pct`. Long event at t: `pct[t] ≤ 10` and
`pct[t−1] > 10`, confined to eligible bars after the hedge is defined. It must equal D350's
`rev_5`/E1 member exactly: 72,677 events, 27,316 cap-exit trades, observed +43.4.

## 2. The invariant lens — every event taken, per trade

**Exits:** cap 40 (primary; the controls' exit), invalidation (`pct` crosses 50), and D303's
target (`x = 0.9627`), beside. **Hedges:** the floored universe's equal-weight return, and
beta-adjusted (trailing 63-bar OLS, lagged, fixed at entry). **Controls:** A′ — per-name time
rotation within eligible bars, **200 draws**; B — same-day same-`rsi`-bucket random name from
the defined-percentile pool, **200 draws**; C — random direction, 1,000. D350's 100 draws of
each carry over as part 0 (their observed statistic must match to 1e-9); part 1 adds 100.
**Splits:** down-years, era halves, dead/alive, price halves, by year. **Mirror.**
**Interaction** with the `rsi` ranking, ten buckets, with the identity [X]. **Cost:** PUB and
PB round trips at the held median half-spread plus commission; net per trade and breakeven
half-spread per exit. **Four groups** with the symmetric trims and the top trade named.
Multiplicity: 138 nominal, `M_eff` 108 (D350), stated.

## 3. The variant lens — the slot-capped event book, hedged

`simulate_event(…, n_max = K)` for K ∈ {2, 4} concurrent longs (the book is one-sided), cap
and invalidation exits, most extreme first, over-cap events dropped and counted. **The
capital series is hedged as the ledger is:** an additive option in the kernel accumulates
`Σ sgn·(v − m)` per bar beside the existing raw sum, returned as a deployed series (per
position held) and a total series (per U = 4 slots); **every existing kernel output is
bit-identical with the option present** ([KX]). Scored as the slot books are (`G22.costed`:
held median half-spread, turnover on names held, PUB and PB): gross and net bp/bar, Sharpe,
max drawdown, exposure, mean positions, skipped share. **Null:** A′ re-simulated at the same
`n_max`, 100 draws per K. Beside it, D346's `rev_5` slot-book cell (k=20 +1.20, k=40 −1.30
PUB): the ranking construction's number on the same score, never on the same statistic.

## 4. Predictions

Q1 is load-bearing. Q4b and Q6 are against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* above the p95 of A′, B and C on the cap exit at 200 draws. |
| **Q2** | nets **negative under PUB** on every exit and **positive under PB** on the cap exit. |
| **Q3** | the invalidation exit's mean per trade is below the cap's, and its mean per bar held is above it. |
| **Q4a** | the K=2 hedged deployed series is above A′'s p95 on gross bp/bar. |
| **Q4b** | *(against)* the K=2 hedged deployed series nets **> 0 bp/bar under PUB**. |
| **Q5** | the symmetric 1% trim is within 10 bp of the mean and the top trade is < 3% of P&L. |
| **Q6** | *(against)* era 1 is positive on the cap exit (D350: +0). |
| **Q7** | the interaction is negative in the bottom `rsi` decile and positive above the 75th percentile. |
| **Q8** | beta-adjusted excess is within 15% of equal-weight. |
| *check* | identity with D350's member on events, trades and observed mean; the hedged series reconciles to the ledger. |

## 5. Stop conditions

- **Q1 holds** → `rev_5`/E1 is the pair book's **long trigger** (D354), carrying this record's
  four groups and both cost lines; nothing is admitted to any book.
- **Q1 fails** → the D350 survivor was the screen's maximum and not a signal; D354's long
  arm is withdrawn before it runs.
- **Q4a holds and Q4b fails** → the slot-capped event book has edge and the published spread
  eats it, like every book in this programme; the record says so and waits for D336.
- Nothing is promoted. Book: empty.

## 6. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** · **[F]** | via the shared prep |
| **[G]** | the event matrix equals D350's `rev_5`/E1 exactly; **[ID]** the kernel reproduces D350's 27,316 trades and +43.4 |
| **[KX]** | with the hedged-series option present, every existing kernel output (trades, series, counts) is bit-identical on D347's `hist_L` run and D350's `rev_5` run |
| **[HX]** | the hedged deployed and total series equal the per-trade ledger summed per bar to 1e-12 |
| **[A′]** / **[B]** / **[C]** | as D352; **[P]** part 0 equals D350's stored file |
| **[S]** | sign in money on an A′ ledger; favourable paths pay positively |
| **[X]** | the buckets partition the trades; `Σ n_b (E_sb − E_s) = 0` |
| **[V]** | the slot-capped book holds at most K per bar; skipped events counted |
| **[6]** | [HX] raises with the market term left in; [S] raises on a ledger handed +50 bp |

## 7. Files

`docs/decisions/D353-rev-5-entering-the-bottom-decile-the-full-record.md` (this record) ·
`scripts/run_d353_rev5_record.py` (stages `--selftest`, `--controls --draws N --part p`,
`--variant --draws N --part p`, `--report`) · `scripts/d345_event_book.py` (the additive
option) · `data/d353_*.json` (to follow). Reuses `scripts/run_d350_long_timing_screen.py`,
`scripts/run_d347_long_signal_controls.py`, `scripts/d348_prep.py`.
