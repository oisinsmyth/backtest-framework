# D455 — insider purchases, stage 1: the event book through the kernel, with three controls declared and the 10% owners set aside

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D455-insider-purchases-stage-1-the-event-book-through-the-kernel-with-three-controls-declared-and-the-10-percent-owners-set-aside.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. **The
first forward-return look at insider demand in this repo.** In-sample on the mining fixture; **no
holdout is read** (the holdouts have no CIK map). D455 taken after `ls docs/decisions` and
`git log --all` showed D454 as the last number on either branch.

## 0. What is being tested

That an **insider's open-market purchase, public within two business days (D454)**, is followed by
a hedged excess return in the name over the next quarter, beyond what a random name in the same
price × volatility × momentum cell on the same day earns (the buys sit in beaten-down, small,
thin, volatile names — D454 §5 — and such cells have their own hedged drift, D446/D453), and
beyond what the same names earn on rotated dates.

## 1. The events (from `data/d454_insider_events.csv.gz`, frozen)

- **Primary set:** purchase filings 2010-01-01 to 2023-12-29 with **no 10% owner among the
  reporting owners** (Director / Officer / Other buyers only — the 10% owners are 18% of filings
  and most of the dollars, a different mechanism: Roche in FMI, Berkshire in BAC), **total value
  ≥ $25,000** (the p10 is $10k; a token purchase is not a signal), on a name **live and eligible**
  (the kernel's `elig`: price floor, F0 window) at the availability bar.
- **Availability bar** `t_av` = the first fixture bar strictly after `FILING_DATE` (D454). The
  event mask is `mask[t_av, name] = True`; the kernel fills at the open of `t_av`, so the filing
  is public before the fill. **[F] asserted: every event's bar date > its filing date.**
- Several filings on one name inside a hold: the kernel skips a name already held, so a name is
  entered once per hold and re-entered by the next filing after exit.
- **Reported, not gated:** the **10%-owner set** (its own book); the **cluster subset** (≥ 2 distinct
  non-10% owners within ±5 bars, family-trust guard: distinct owners capped at 5 per name-day);
  **officer-only** filings; **value terciles**; the **sales mirror** (S filings, shorted, same hold);
  holds of **21 and 126** bars.

## 2. The construction

D345's kernel through `run_d359` as in D437–D446: **long, `exit = "cap"`, `cap = 63` bars
(primary), `n_max = None` (every event; ~1,000 filings a year with a quarter's hold is a book of a
few hundred names, not a slot problem), hedged series, equal weight.** Score panel: constant
(no priority needed without slots). Sample: 2010-01-04 to 2023-12-29; era 2 from the midpoint.

## 3. The three controls, declared

- **C1 — state-matched random names, per trade.** Each event replaced by a random eligible name
  from the same **price × volatility × momentum tercile cell** (D392's `tercile_pools`) on the
  same day that has no purchase filing within ±5 bars; the same daily count; 100 draws; the
  per-trade mean's p50, p95, the p95's MC precision *and the draw SD* (the D446 addendum's rule).
  Destroys the insider; keeps the day, the count and the cell.
- **C2 — the event calendar rolled in time, exact.** The whole event mask rolled by one **common
  offset** for every name, offsets every 21 bars from 21 to T−21 (~160), the book re-run;
  p50 and p95 exact on the grid. Keeps every name's event count, the name composition and the
  clustering; destroys alignment with the return.
- **C3 — the name-preserving shuffle.** Each name's own events rolled by an **independent random
  offset** (D437's `rotate`), 100 draws; p50, p95, SE. Keeps each name's count; destroys the timing
  and the cross-name co-timing (the clusters).

Per-trade lens against C1; book lens against C2 and C3; **never across lenses**; the overlap
caveat of D446's addendum applies to the per-trade lens (a quarter's hold on ~250 concurrent
names), so the book's monthly block-bootstrap SE is the honest measure of the evidence.

## 4. Costs

Crossed (PUB half-spread × 2 + commission; no borrow on the long side) and passive at the open
(D439/D440's assumption), both on every table. The buys sit in thin, cheap, volatile names, where
the modelled half-spread is closest to a quote: **the crossed line decides.**

## 5. The bar (one primary, R14): the primary set, cap 63, crossed

- **T1** per-trade gross > C1 p95 by 2 MC-SE (and reported in draw SD).
- **T2** book gross > C2 p95 (exact) **and** > C3 p95 by 2 SE.
- **T3** book net crossed > 0 by 2 SE (monthly block bootstrap).
- **T4** era-2 net crossed > 0 by 2 SE.
- **T5** ≥ 20 names to half the P&L and top 1% of trades ≤ 50%.
**Candidate for a holdout: T1 ∧ T2 ∧ T3 ∧ T4 ∧ T5** — and a holdout read would first need a CIK
map and a Form 4 parse for the holdout names under a separate record, then the principal's word.

## 6. Predictions (MODERATE; literature, D454's shape, D446/D453's cell baselines)

- **X-a** per trade at 63 bars: gross **+120 to +260 bp**, median +40 to +120 (right-skewed, the
  recoveries); C1 p50 **+20 to +60** (the beaten-down cell's own quarter, hedged); increment
  **+80 to +200**, ≥ 2 draw-SD; T1 passes.
- **X-b** the book: ~200–300 names held; gross **+2.0 to +4.0 bp/bar**, SE **0.8–1.2**; crossed cost
  **1.2–2.2 bp/bar** (turnover ~1.6%/bar at 80–130 bp round trips in thin names); **net +0.3 to
  +2.2 — T3 a coin**; passive net ≥ +1.5.
- **X-c** C2 p50 **+0.5 to +1.2** (the composition of names that insiders buy earns hedged on any
  dates), p95 +1.5 to +2.5; C3 p50 within 0.3 of C2's, p95 within 0.4 — the co-timing carries
  little; T2 passes C3, a coin on C2.
- **X-d** the **cluster subset** beats singles by **+40 to +100 per trade**; **officer-only** beats
  director-only by +20 to +60; the **value top tercile** beats the bottom by +30 to +80; the
  **10%-owner** set's gross is **below** the primary's; the **sales mirror** shorted is **0 ± 40**
  per trade (sales carry no information, as the literature says).
- **X-e** holds: cap 21 gross per bar ≥ cap 63's (the effect is front-loaded); cap 126 per bar
  below.
- **X-f** era 2 positive and **below era 1** (the post-2015 literature finds the effect fading);
  T4 fails more likely than not. Concentration: ≥ 40 names to half, top 1% ≤ 40%; T5 passes.

## 7. Not in scope

Any holdout; derivative transactions; Forms 3 and 5; any sizing beyond equal weight; the 2024–
2026 quarters. Forty-seventh look by object; look #1 of the insider line's forward-return ledger.

## 8. Files

This record · `scripts/run_d455_insider_book.py` (`--run [--quick]`, `--selftest`) ·
`data/d455_insider_book.json` · RESULT.
