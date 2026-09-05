# D345 RESULT — the event book fails as calibrated: the exposure rule sent θ to 11, the book ran net short and unhedged, and the target exit cut its winners at the first move

**Status:** RESULT. Pre-registered at `dfd1c6b`, simulator + runner at `8922189` — both
before this file existed (R8). `rsi`, `keep_v2`, open fill, PUB primary.
**Date:** 2026-09-06
**Area:** Construction · strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Q1 fails: Axis C closes again, with this record as the reason. The slot book at k=40
stays the candidate cell. Nothing is promoted. Book: empty.**

---

## 1. The kernel is right; the book is not

**The identity held.** Fed "rank below two at t" with no holding cap and D303's target with
a 20-bar cap, the event simulator reproduces the slot book's invariant lens
**bit-identically** — 4,021 trades, `cnt0`, `cnt1`, `ent` and the per-side series — and
that lens is D343's `rsi` v2 invariant cell (−3.73 a trade). The first attempt failed on
the per-side series at the rounding level: the slot book averages its held positions
with `np.mean` over a buffer in gate order, and the kernel summed in a Python loop in row
order. Matching the order (longs by score ascending, shorts by score descending with the
ranker's reversed tie order) and the reduction made it exact. **Everything below is the
construction and its calibration, not the kernel.**

## 2. What the calibration did

θ was to be set on exposure: the value at which a fixed 40-bar hold averages two
concurrent positions per side. **It landed at θ = 11** — long when `rsi ≤ 11`, short when
`rsi ≥ 89` — with a fixed-hold concurrency of 1.07 long and 2.30 short. **Q10 falsified.**
On this universe the extreme-oversold tail is rare and the extreme-overbought tail is
not; no symmetric threshold gives two per side, and the nearest gives a book that is
short three times as often as it is long. Under the target exit the realised exposure is
0.31 long and 0.81 short per side, flat on a third of all bars, **192 trades in sixteen
years** on the primary arm. "Two per side" was the slot book's exposure and it is not a
natural exposure for a threshold entry on this signal; the rule forced the threshold into
a tail where the signal barely fires.

## 3. The six cells

| arm | lens | trades | mean / trade | **net / trade** | TOTAL gross | **TOTAL net** | TOTAL Sharpe | exposure | positions | TOTAL maxDD | DEPLOYED gross | **DEPLOYED net** | DEPLOYED Sharpe |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **A · target** | variant | 192 | +52.6 | −2.2 | −0.01 | **−1.66** | **−0.198** | 67% | 1.12 | 5,355 | +0.04 | **−5.87** | **−0.246** |
| A · target | invariant | 279 | +68.3 | +12.9 | +0.97 | −1.45 | −0.050 | 69% | 1.54 | 32,777 | −4.29 | −10.60 | −0.399 |
| **B · invalidation** | variant | 146 | **+237.6** | **+182.4** | +1.97 | +0.69 | +0.084 | 76% | 1.32 | 5,375 | +3.76 | −0.09 | −0.004 |
| B · invalidation | invariant | 269 | +210.2 | +154.7 | +6.16 | +3.81 | +0.090 | 80% | 2.45 | 42,601 | +1.56 | −2.28 | −0.115 |
| C · cap | variant | 126 | +209.0 | +155.0 | +1.07 | −0.01 | −0.001 | 82% | 1.57 | 7,170 | +3.86 | +1.13 | +0.054 |
| C · cap | invariant | 269 | +227.7 | +172.2 | +6.16 | +3.81 | +0.085 | 86% | 3.37 | 41,216 | +0.34 | −2.45 | −0.124 |

For comparison, D344's slot book at k=40: deployed PUB net +5.14, Sharpe +0.268, mean per
trade +102, maxDD 8,423, invariant per trade −11.8.

**Q1 falsified**, decisively: the primary arm nets −5.87 on deployed capital and −1.66 on
total, both Sharpes negative. **Q2 falsified** (the total-capital Sharpe is not within
0.10 of the slot book's; it is below zero). **Q3 falsified**: +52.6 a trade against +102.
**Q4 and Q5 confirmed**: the book is flat a third of the time, never above two per side,
and its total-capital drawdown is 5,355 against 8,423 — it is less risky because it is
mostly not there.

## 4. Two things the run found that the design did not anticipate

**The series were unhedged and the book was net short.** Every ledger P&L in this
programme is a market-hedged sum, `sgn·Σ(v − m)`. The slot book's bar series is hedged
by construction — two long, two short, always. The event book's total- and
deployed-capital series were defined as the raw signed position return, and with 0.31
long against 0.81 short the book carried a net short through a rising market. The
per-trade lens says arm B makes **+182 net a trade**; the per-bar lens says its total
capital nets +0.69. Reconstructed from the ledger (post hoc, open tail excluded, PUB),
the *hedged* total-capital gross is about +0.8 bp/bar for arm A (against −0.01 unhedged),
+2.7 for arm B and +2.1 for arm C — a market drag of roughly 0.8 to 1.3 bp/bar hidden in
the tilt. The per-bar numbers in §3 are therefore lower bounds on a hedged event book,
and **the construction as written did not carry the hedge its own ledger assumes.** Any
retry defines the capital series as hedged.

**The target exit is the wrong exit for an event book.** D303's rule fires when the
summed excess reaches 0.96 of the name's vol — the first move — and in the slot book that
freed a slot for the next name. In the event book there is no next name waiting, and
the target simply cuts the winner: arm A's mean per trade is +52.6, arms B and C's are
+237.6 and +209.0, with holds of about nineteen bars against thirty. **Q6 confirmed, and
D295's closure of the exit family is amended in writing**: exits were inert because the
slot refilled behind them, not because exits do not matter. Here the invalidation exit is
worth +185 bp a trade over the target.

## 5. The invariant lens and the null

**Q7 and Q8 confirmed, against**: every signal taken, arm A, nets **+12.9 a trade** under
PUB (+68.3 gross on a 2c of 55.4), the first positive invariant lens in the programme —
against the slot book's −11.8 at k=40 and −3.7 at k=20. A threshold at `rsi ≤ 11 / ≥ 89`
is a tighter cohort than rank 25, and it pays its own cost per trade.

But the null does not distinguish it from chance. Per-name time rotation of the signal,
200 draws, 200 distinct books:

| lens | statistic | score | p50 | p95 | max | p |
|---|---|--:|--:|--:|--:|--:|
| variant | deployed gross Sharpe | **+0.002** | −0.207 | +0.313 | +0.823 | **0.25** |
| variant | deployed net Sharpe PUB | −0.246 | −0.740 | −0.315 | +0.211 | 0.04 |
| variant | total gross bp/bar | −0.009 | −0.885 | +1.094 | +3.256 | 0.27 |
| invariant | mean per trade | +68.3 | −23.3 | +78.4 | +200.6 | **0.07** |
| invariant | net per trade PUB | +12.9 | −88.3 | +12.3 | +138.3 | 0.055 |

**Q9 falsified**: the variant's gross Sharpe is at the null's median. The invariant's
per-trade mean is inside its null's 95th percentile (p = 0.07) and its net is a hair
above (p = 0.055). At 192 to 279 trades the book is too thin to separate from a rotation
of its own signal dates. The null has teeth (200 distinct values, p95 > 0) — the first
null in the programme with more than 24.

Group 3's shares are undefined on this book: the total contribution P&L is within
rounding of zero, so every share is a large number of either sign. The top five by P&L
are all shorts — KODK 2020-07-30 (+9,083 bp, `rsi` 98.8 at signal), DRYS 2016-11-17
(+7,851), KALA, IBRX, CYCN — liquid names, every one, and the same squeeze days that
appear in every book here.

## 6. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* arm A variant deployed Sharpe > 0.268 | **FALSIFIED** — −0.246 |
| **Q2** | *(against)* total-capital Sharpe below 0.268, within 0.10 | **FALSIFIED** — −0.198 |
| **Q3** | mean per trade > +102 | **FALSIFIED** — +52.6 |
| **Q4** | ≤ 2 per side, flat > 10% | **CONFIRMED** — 0.31 / 0.81, flat 32.6% |
| **Q5** | total maxDD < 8,423 | **CONFIRMED** — 5,355 |
| **Q6** | arm B beats arm A on deployed Sharpe | **CONFIRMED** — −0.004 vs −0.246; +185 a trade |
| **Q7** | invariant net per trade > −11.8 | **CONFIRMED** — +12.9 |
| **Q8** | *(against)* invariant net per trade > 0 | **CONFIRMED** — +12.9 |
| **Q9** | arm A gross Sharpe above the null's p95 | **FALSIFIED** — at the median |
| **Q10** | θ in [15, 30] | **FALSIFIED** — 11 |
| *check* | kernel identity; the variant's entries | identity to 0.0; 92.7% of variant entries are invariant entries, the rest re-enter names the invariant still held |

Five of ten. The load-bearing one failed and the two "against" predictions on the
per-trade lens held.

## 7. Stop conditions, executed

- **Q1 fails → the event construction does not beat the slot book on the capital it
  deploys. Axis C closes again**, with this record as the reason, and the slot book at
  k=40 stays the candidate cell. **The reason is recorded precisely**: not that an event
  book cannot work, but that this one was calibrated to a slot book's exposure, which put
  its threshold in a tail where the signal fires nine times a year; it ran net short with
  an unhedged series; and it used an exit built for a construction that refills.
- **Q6 holds → D295's closure of the exit family is amended**: it was a property of the
  always-invested construction.
- **Q10 fails → flagged**: two per side is not a natural exposure for a threshold entry on
  `rsi`.
- **If the principal wants the construction retried**, it is a new pre-registration with
  three changes named here: θ calibrated on **trade count** (an entry rate, not a
  concurrency), the capital series **hedged** as the ledger is, and the **invalidation
  exit** as the primary arm. None of that is run here.

## 8. Deviations and wording

- Pre-registration [V] said the variant ledger is a subset of the invariant's as
  `(row, e0, side)`. That is false in general — the variant re-enters a name the invariant
  is still holding — so the runner asserts the correct property (every variant entry has
  the signal at t−1, never more than N_MAX held) and reports the subset share, 92.7%.
- The capital series are unhedged (§4). Recorded as a design defect of this record, not a
  code defect; the ledger and every per-trade number are hedged as always.

## 9. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | cache key; F0 counts; raw factor == census; `keep_v2` share == D343 |
| **[ID]** | the kernel reproduces D343's `rsi` v2 invariant ledger bit-identically — 4,021 trades as a sorted set, `cnt0`/`cnt1`/`ent`, the per-side series |
| **[T]** | the calibrator has no returns parameter and raised on one; θ chosen before any P&L existed |
| **[A]** | every one of 279 invariant entries has the signal on the raw floored score at t−1 (the unlagged score fails 144 of them); on 200 sampled bars every signalled name was entered or already held |
| **[S]** | every trade in all six ledgers equals the open-fill recomputation to 8.9e-16; favourable paths pay positively |
| **[V]** | never more than 2 per side in any arm; every variant entry has the signal; 182 signals skipped for a full side in arm A |
| **[X]** | mean positions == Σ`cnt`/bars; total == deployed × held / U on every held bar |
| **[RQ]** | total and deployed series differ; both reported, never compared |
| **[2]** | every ledger's contributions reconstruct the total-capital gross to < 1 bp; arm A variant residual 0.0000, 0 open at T |
| **[3]** | symmetric trim in every cell |
| **[N]** | the per-name rotation keeps every name's signal count and moves the book; 200 distinct draws |
| **[B]** | total-capital borrow equals the per-trade sum / bars / U on every cell |
| **[6]** | the costing raises on +5 bp handed |

**Speed:** 164 s including the null (102 s for 400 simulations).

## 10. What this establishes

1. **The event kernel exists and is trusted**: it is the slot simulator's uncapped lens
   with the entry signal made explicit, proven bit-identical.
2. **An exposure calibration is the wrong way to set a threshold entry.** It answered
   "how extreme must `rsi` be for two names per side to qualify" with "extreme enough
   that it rarely does", and the resulting book cannot be separated from a rotation of its
   own dates.
3. **The target exit belongs to the always-invested construction.** In a book with no
   refill it cuts winners at the first move; the invalidation exit is worth +185 bp a
   trade over it. D295's "exits are dead" is withdrawn as a general claim and kept as a
   fact about the slot book.
4. **The first positive invariant lens in the programme** — +12.9 net a trade on every
   `rsi ≤ 11 / ≥ 89` signal — and the first null with more than 24 values, which places it
   at p = 0.055. Thin, borderline, honest.
5. **A capital series for an unbalanced book must carry the hedge its ledger carries.**
   The slot book never needed the rule; the event book does.

## 11. Files

`data/d345_event_book.json` · `scripts/run_d345_event_book.py` · `scripts/d345_event_book.py`
