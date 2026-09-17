# D353 RESULT — `rev_5` entering the bottom decile is real at 200 draws on every control, nets nothing at the published spread, and a slot cap on it is a sample of its most extreme events

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D353-RESULT-rev-5-is-real-at-200-draws-and-a-slot-cap-on-it-is-a-sample-of-its-worst-events.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `b1ba11c`, runner and the kernel's hedged-series option
at `112003b` — both before this file existed (R8). `keep_v2`, F0, next-open fill, hedged
against the floored market, D345's kernel, PUB primary, PB beside.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. `rev_5`/E1 is the pair book's long trigger (D354), carrying both cost lines.**

---

## 1. The verdict

**Seven of nine, and the load-bearing one held.** `rev_5` entering the bottom decile, every
event taken on the cap exit: **+43.4 bp a trade** on 27,316 trades, above the p95 of its own
names at random eligible times (A′ +28.6 at 200 draws), of a random same-day same-bucket
name (B +35.8 at 200), and of random direction (C +15.2). Mean equal to median, symmetric
trim +35.3, 27 names to half the P&L, ten of fourteen years, positive in every down-year,
top trade 1.3%. **It nets −18.6 after the PUB round trip and +17.9 after the PB one.**

| every event taken, long, bp per trade | n | mean | median | t | hold | net PUB | net PB | breakeven half-spread |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| **cap 40** | 27,316 | **+43.4** | +41.8 | 4.8 | 39.9 | **−18.6** | **+17.9** | 20.5 bp/side |
| invalidation (`pct` crosses 50) | 55,226 | +24.2 | +95.5 | 8.7 | 6.6 | −43.3 | −3.7 | 10.8 |
| target (D303) | 43,894 | +31.3 | +232.5 | 7.2 | 14.4 | −33.8 | +5.5 | 14.4 |
| mirror, cap | 27,596 | −7.2 | +6.9 | −0.8 | 39.9 | −68.8 | −38.5 | — |

| control, cap exit | draws | p50 | p95 | max | above |
|---|--:|--:|--:|--:|---|
| **A′** own names, random eligible times | 200 | +19.0 | +28.6 | +37.3 | yes |
| **B** same day, same `rsi` bucket | 200 | +26.6 | +35.8 | +38.2 | yes |
| **C** random direction | 1,000 | 0.0 | +15.2 | +31.1 | yes |

## 2. The exits and the hedge

The invalidation exit holds 6.6 bars and earns +24 a trade, +3.7 per bar held against the
cap's +1.1 — the reversal pays fastest in its first week and the cap then sits through
thirty more bars for the remaining +19. On a per-trade cost basis the cap is the only exit
that nets positive under PB; on a per-bar basis the invalidation exit is three times as
productive and pays a round trip every seven bars. D303's target sits between them. Beta
adjustment takes +43.4 to +37.2 (median β 0.97): the hedge is not carrying beta.

## 3. The interaction, the fifth table

Bucket by `rsi` percentile at t−1: the interaction is −65 in the bottom 2%, −57, −45, −24,
−10, −10 through the middle, and **+66 and +150 in the (75, 95] buckets**. A one-week
reversal on a name whose two-week `rsi` is neutral or high is a pullback and recovers; on
a name oversold on both it is a falling knife. This is the fifth table across D347, D349,
D350 and here to say that the bottom of the `rsi` ranking is where a long signal does
worst. The pair book uses the ranking only to choose the hedge (D354).

## 4. The variant lens — the slot-capped event book, hedged

| K | exit | entries | gross bp/bar | net PUB | net PB | net Sharpe PUB | A′ gross p50 / p95 | above | skipped |
|--:|---|--:|--:|--:|--:|--:|--:|---|--:|
| 2 | cap | 161 | −1.75 | −5.82 | −4.67 | −0.40 | +0.5 / +6.3 | **no** | 99.8% |
| 2 | invalidation | 887 | +6.60 | −17.32 | −10.66 | −1.07 | −0.8 / +4.9 | yes | 98.8% |
| 4 | cap | 322 | **+7.79** | **+3.47** | +5.27 | +0.31 | −0.5 / +3.1 | yes | 99.6% |
| 4 | invalidation | 1,760 | +5.97 | −17.07 | −8.85 | −1.36 | +0.1 / +3.3 | yes | 97.6% |

**Q4a and Q4b falsified for K=2**, and the reason is the construction, not the signal. A
two-slot cap on 72,677 events with a 40-bar hold admits 161 entries in sixteen years —
99.8% of the signal is skipped — and admits them **most extreme first**: the two names with
the deepest five-day crash on each day a slot is free. Those are the events the invariant
lens' own interaction table says do worst. The two-slot book is not the signal; it is a
sample of its most extreme two percent, and it loses. At K=4 the cap-exit book nets +3.5
bp/bar under PUB with a Sharpe of 0.31, above its own time-rotation null on gross and on net
— **on 322 entries**, one of four cells, with no rank rotation to face because there is no
gate. It is recorded, not built on. The capital series are hedged as the ledger is ([HX]
reconciles them per bar to 1e-15), which D345 could not do; D346's `rev_5` slot-book cell
(+1.20 at k=20, −1.30 at k=40 PUB) is the ranking construction on the same score and is not
comparable on any statistic.

## 5. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* above A′, B and C on the cap exit at 200 draws | **CONFIRMED** — +43.4 vs +28.6 / +35.8 / +15.2 |
| **Q2** | negative under PUB on every exit; positive under PB on the cap | **CONFIRMED** — −18.6 / −43.3 / −33.8; +17.9 |
| **Q3** | invalidation below the cap per trade, above it per bar held | **CONFIRMED** — +24.2 vs +43.4; +3.67 vs +1.09 |
| **Q4a** | K=2 hedged deployed series above A′ p95 on gross | **FALSIFIED** — −1.75 vs +6.25 |
| **Q4b** | *(against)* K=2 nets > 0 under PUB | **FALSIFIED** — −5.82 |
| **Q5** | trim within 10 bp of the mean; top trade < 3% | **CONFIRMED** — +35.3 vs +43.4; AAOI 1.3% |
| **Q6** | *(against)* era 1 positive on the cap | **CONFIRMED** — +0.2 on 8,987 trades; era 2 +64.5 |
| **Q7** | interaction negative in the bottom decile, positive above the 75th | **CONFIRMED** — −52.4 / +51.4 |
| **Q8** | beta-adjusted within 15% of equal-weight | **CONFIRMED** — 14.2% |
| *check* | identity with D350; the hedged series reconciles | held: 72,677 events, 27,316 trades, +43.38 to 0.0; [HX] to 1.3e-15 |

Seven of nine.

## 6. Stop conditions, executed

- **Q1 holds → `rev_5`/E1 is the pair book's long trigger** (D354), carrying this record's
  four groups and both cost lines. Nothing is admitted to any book.
- **Q4a fails → the slot-capped event book at K=2 has no edge on this signal**, for the
  reason §4 gives; the record does not say the signal has none. The K=4 cell is noted with
  its sample size and its multiplicity of four.
- Nothing is promoted. Book: empty.

## 7. Deviations and what the run found

- **The kernel option is additive and proven so**: [KX] reproduces D347's `hist_L` control
  draws and D350's `rev_5` observed statistic to 0.0 with the option absent, and every
  common output is identical with it present. The option adds `signed_x`, `book_dep_x` and
  `book_tot_x` and nothing else.
- **Total-base costing:** `G22.costed`'s turnover is on the deployed basis; applied to the
  total series it overstates cost by `U / mean_held`, so the total base is costed with the
  event kernel's own `entries / bars / U`, and the two deployed costings are asserted equal
  to 1e-9 per cell.
- **Control B's pool differs between parts:** D350's part 0 drew from `elig`; part 1 from
  `elig ∧ defined percentile`. Both are concatenated and the report says so; the p95 moved
  by 0.1.
- **The era-1 clause was confirmed by 0.2 bp on 8,987 trades.** It is not evidence of an
  era-1 edge; the pre-registered "against" read barely lost.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** · **[F]** | via the shared prep; grid == direct recomputation to 1.3e-14 |
| **[G]** · **[ID]** | 72,677 events == D350's member, dense == sparse == D347's rule; 27,316 trades, +43.3806, to 0.0 |
| **[KX]** | D347 `hist_L` p0 first 3 draws to 0.0 from its seed; D350 `rev_5` to 0.0; with/without the option every common key equal, three keys added |
| **[HX]** | the hedged deployed and total series equal the ledger per bar to 5.6e-17 (K=2, 4; both exits) and 1.3e-15 (invariant), open tail excluded and asserted contiguous |
| **[A′]** · **[B]** · **[C]** · **[P]** | eligibility and counts kept; B 99.95% changed, 36 kept == the counted pool shortfall; C +0.005 ± 0.286; part 0 == D350's file |
| **[S]** | 300 A′ trades and 300 mirror trades to 0.0 |
| **[X]** · **[V]** | Σ n_b (E_sb − E_s) = −2.3e-11; K=2 max 2, 161 = 159 + 2 open, 72,184 skipped counted |
| **[6]** | [HX] raises with the market term left in; [S] raises on a ledger handed +50 bp |

**Speed:** self-test 17 s; A′ 1.0–1.7 s a draw, B 1.2–1.9; variant 0.4–1.1 s a draw; report
12 s; peak working set under 1 GB per process.

## 9. What this establishes

1. **`rev_5` entering the bottom decile is a real long trigger** on the floored universe:
   above every honest control at 200 draws, clean in distribution, positive in the
   down-years, with the ranking's neutral-to-high buckets as its best ground.
2. **It does not pay the published spread** at any exit, and pays the estimated one on the
   cap exit. The pair book (D354) runs under both.
3. **A slot cap on an event signal is a sample of its most extreme events**, not the
   signal, when the cap is small against the event count; the two-slot version of this
   signal loses. Any capped book on it must be read against its own skipped share.
4. **The hedged capital series exists** in the kernel now, additive and reconciled, which
   is the second of D345's three retry changes done.

## 10. Files

`data/d353_ctrl_p1.json` · `data/d353_variant_k{2,4}_p0.json` · `data/d353_rev5_record.json` ·
`scripts/run_d353_rev5_record.py` · `scripts/d345_event_book.py` (the option) · reuses
`data/d350_ctrl_rev_5-E1_p0.json` as part 0
