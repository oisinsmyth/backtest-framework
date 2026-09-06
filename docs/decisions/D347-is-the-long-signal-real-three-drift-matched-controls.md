# D347 — is the long signal real? Three drift-matched controls, two hedges, the splits drift cannot pass, and the `rsi`-rank interaction

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. Nothing here is a book: the output is which long signal, if any, has edge that
survives every control, and in which `rsi`-rank buckets.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

The principal wants a real long signal to trigger the spread book, and D290's long-only
verdict — fifty of fifty-one long books are market drift — has never been re-asked of a
long *signal* under the current conventions. D346 found two long legs that pay their cost
uncapped, `hist_L` and `rev_21`, but against no control. A long signal is drift until it
is measured against something that carries the same drift. This record measures three
candidate long signals against three controls that each carry it, under two hedges, on
the splits drift cannot pass, and reports where in the `rsi` ranking the edge sits.

## 1. The signals, as events

All scores floored (`keep_v2`), deal-filtered (F0), on the warm base, lagged one bar; the
event day t is the fill day and everything it reads is known at the close of t−1.
`pct[t, i]` is the score's cross-sectional percentile among floored live names at t−1.

| signal | long event at t | short mirror |
|---|---|---|
| **`hist_L`** | `pct` **enters the bottom decile**: `pct[t] ≤ 10` and `pct[t−1] > 10` | enters the top decile |
| **`rev_21`** | same | same |
| **`rsi` turn** *(reference)* | `rsi[t−1] > 30` and `rsi[t−2] ≤ 30` — the conventional cross back up | cross back down through 70 |
| **`rsi` decile** *(reference)* | `pct` enters the bottom decile | enters the top decile |

Every event is entered at the **next open**. Two exits, both reported: **cap** — a fixed
40-bar hold, side-independent and name-independent, **the exit every control uses**; and
**invalidation** — `pct` crosses 50 (or `rsi` crosses 50 for the turn), the book exit.
Every event is taken (the invariant lens); nothing is slot-capped.

## 2. The hedge, two ways

Every trade's P&L is `sgn · Σ (v − m)`. Here **m is the floored universe's own
equal-weight return** — the opportunity set the book actually has — not the whole
panel's. Beside it, **beta-adjusted**: `Σ (v − β·m)` with β the name's trailing-63-bar OLS
slope on that market, lagged, fixed at entry. If the two disagree by much, the signal is
buying beta.

## 3. The three controls — each carries the drift, so drift cancels

| control | construction | what it removes |
|---|---|---|
| **A · per-name time rotation** | each name's event series rolled by a random offset within its priced bars (D345's null) | timing: same names, same count, same holding, same beta |
| **B · same-date, same-cohort name** | each event's name replaced by a random floored live name in the **same `rsi`-rank bucket** on the same day | name selection within the cohort: same day, same regime, same cohort |
| **C · tail-randomised direction** | the same events, each assigned long or short at random (D290's third null) | the directional claim itself |

**100 draws each** for A and B (each draw is a full simulation; four signals × two
controls × 100), 1,000 for C (no simulation). The statistic under every control is the
**mean per-trade hedged excess under the cap exit**. Each control's p95 and its number of
distinct draws are stated. **A signal is real only if it is above the p95 of all three.**

## 4. The splits drift cannot pass

- **Down-years**: the calendar years in which the floored market's return is negative
  (determined from the data and named; 2018 and 2022 are expected). Excess reported in
  those years alone.
- **Era halves.**
- **The mirror**: the short version of the same event. Drift makes a long leg look good and
  a short leg look equally bad; a cross-sectional effect pays something on both.

## 5. The interaction with the `rsi` ranking

Events are split by the `rsi` percentile at t−1 into ten buckets — [0, 2], (2, 5], (5, 10],
(10, 25], (25, 50], (50, 75], (75, 90], (90, 95], (95, 98], (98, 100]. For each bucket:
the events' mean excess (cap exit), the **base rate** — the forward-40 hedged excess of
every floored live name in that bucket on every bar, with the open fill on the first bar
and truncation at delisting exactly as the kernel does — and the interaction
`E[signal, bucket] − E[bucket] − E[signal] + E[all]`. That is where the edge sits after the
cohort's own drift is removed.

## 6. Predictions

Q1 is load-bearing. Q5, Q7 and Q8 are against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* at least one of `hist_L` and `rev_21` long events is **above the p95 of all three controls** on mean hedged excess, cap exit. |
| **Q2** | *(pattern)* the `rsi` turn beats control A (timing) and **fails control B** (same-cohort name): its edge is the cohort, not the name — which is what D346's −11 a trade for its long leg says. |
| **Q3** | *(the hedge works)* every control-A distribution is centred within **±10 bp** of zero: the same names at random times have no hedged excess. If a rotation null is centred well above zero the hedge is leaving beta in. |
| **Q4** | beta-adjusted excess is **below** equal-weight excess for every long event (extreme names carry β > 1), by **less than 30%** of it. |
| **Q5** | *(against)* for the surviving signal(s), excess in the bottom `rsi` decile exceeds excess in the middle half (25–75) by **more than 20 bp** — the ranking adds to the signal. |
| **Q6** | the surviving signal(s) have **positive** hedged excess in the down-years. |
| **Q7** | *(against)* the mirror of the surviving signal(s) has mean hedged excess **> 0**. |
| **Q8** | *(against)* at least one long event signal nets **> 0 per trade after the PUB round trip** under the invalidation exit. |
| *check* | the kernel is D345's, already proven; the cap-exit trade count equals the event count minus events at bars with no priced forward path. |

## 7. Stop conditions

- **Q1 holds** → the survivor is the long signal for the pair book, and §5 says which
  `rsi` buckets it fires in profitably; the pair-book pre-registration is written on it.
- **Q1 fails** → no long signal among the three is real against drift-matched controls
  under the current conventions; D290's verdict stands for signals as it stood for books,
  and the pair book waits for a signal that earns it.
- **Q3 fails** for any signal → the equal-weight hedge leaves beta in the measurement;
  the beta-adjusted excess becomes primary for that signal and the record says so.
- **Q2 fails** in the direction of the `rsi` turn beating all three → the reference is a
  real signal in its own right and joins the survivors.
- Nothing is promoted. Book: empty.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | cache key; F0 counts; raw factor == census; `keep_v2` share == D343 |
| **[ID]** | D345's kernel identity re-asserted (the kernel is unchanged): fed rank < 2 with the slot exit it reproduces D343's invariant ledger |
| **[E]** | every event has the defining condition on the raw lagged percentile (or `rsi`) at t−1 and not at t−2; event counts per signal reported; the unlagged rebuild differs on most |
| **[H]** | the floored market equals the equal-weight mean of `r1T` over `keep & finT` on every bar with ≥ 20 names, recomputed independently; β on a synthetic name with returns 2m + noise recovers 2 within 0.05 |
| **[S]** | every trade equals the open-fill recomputation against the floored market to 1e-12; favourable paths pay positively |
| **[A]**/**[B]** | control A keeps every name's event count; control B keeps every event's date and `rsi` bucket and changes its name |
| **[C]** | control C's distribution has mean within 2 standard errors of zero |
| **[F]** | the base-rate grid equals a direct per-cell recomputation on 3,000 sampled cells |
| **[X]** | the interaction identity: Σ over buckets of event counts equals the event count; the interaction summed with event weights is zero to 1e-9 |
| **[6]** | the check raises on events handed +50 bp |

## 9. Files

`docs/decisions/D347-is-the-long-signal-real-three-drift-matched-controls.md` (this
record) · `scripts/run_d347_long_signal_controls.py` (stages: `--selftest`, `--controls
<signal>`, `--report`), `data/d347_*.json` (to follow). Reuses `scripts/d345_event_book.py`.
