# D441 — quoted spreads on the names B trades: is the modelled half-spread a quote or a range, and what does B net at the quote

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D441-quoted-spreads-on-the-names-B-trades-is-the-modelled-half-spread-a-quote-or-a-range.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. **No
quote has been seen; the pull needs the principal's TWS session and is not run by this record's
author.** Companion to D336, which it does not alter: D336 decides the estimator *convention* on a
stratified sample of 100 names; this record measures the estimator's *level* on the names one
construction actually trades and re-costs that construction at the quote. Both pulls are run in the
same session, D336 first. In-sample on the mining fixture; **no holdout is read by this record.**

## 0. Why

D440 closed on cost, not on signal: B (a 3× volume bar in a top-price-tercile name, sold short)
carries +21 bp per trade over its state-matched control and clears the rotation null by 64 SE,
and nets −18 per trade under the kernel's crossed line, +7 under D439's passive line. Every one
of those net numbers charges a Corwin–Schultz half-spread, and D439 found that estimator reads
17–55 bp a side on names whose quoted half-spread is one or two — it is a range estimator, right
where range and quote converge and an order of magnitude high where they do not. B's names are
$100–$500 mid-caps (RH, KALU, ALGT, CACC, SAM, BURL …): thinner than D439's megacaps, thicker
than the small names the estimator was validated on. **Whether their modelled 26 bp a side (52
round trip) is a quote or a range is the unmeasured thing that decides B, and nothing on OHLC can
measure it.** A quote can.

## 1. The sample, declared (written to `data/d441_sample.json` before any quote is seen)

The names B trades at cap 20 on the mining fixture — the D440 book, 9,851 trades on 661 names —
restricted to what IBKR can quote today:

- `cohort == "alive"` and `last_bar == "2026-08-26"` in the fixture meta (478 names);
- **not padded**: at least one non-zero volume bar and at least five distinct closes in the last
  21 fixture bars. The fixture carries ten B names as "alive" with a constant close and zero
  volume since their acquisition (SPLK at 156.9, SGEN at 228.74, KRTX, …); the meta counts a
  name whose delisting date falls after the span end as alive. These are excluded here and
  **the same test is disclosed for D336's sample, where AVNS is padded** (21 constant closes) —
  it will come back unresolved or fail D336's `[G]`, and D336's compare treats a missing CSV as
  missing, not as a failure;
- **≥ 10 B trades at cap 20** in the D440 book. Splits are *not* excluded (D336 excluded them):
  the quoted half-spread `(ask − bid)/2/mid` and the log-range estimators are both invariant to a
  split adjustment except on the split bar itself, and the `[G]` guard on the last common date is
  kept.

That is **272 names carrying 6,883 of the 9,851 trades (70%) and 1,982 of the 3,174 wide-tercile
trades (62%)**; 33 of them are already in D336's sample and their bars are shared (one cache).
Pull order: wide-tercile trade count descending, so an interrupted pull keeps the names that
carry the increment. **Per name, recorded before any quote:** trade count by D438 tercile, the
median modelled PUB half at the name's B trades, and the median modelled PUB half over the last
252 bars (the year the quote will cover).

## 2. The pull (the principal runs it; D336's instrument, unchanged)

`scripts/d336_ibkr_quoted_spreads.py`'s `pull()` over this sample: `Stock(sym, "SMART", "USD",
primaryExchange)`, `reqContractDetails`, one daily `BID_ASK` `reqHistoricalData` (`1 Y` to
2026-08-26, RTH), the 30-per-600-s bucket, `+PACEAPI`, `readonly=True`, the bar-semantics gate
(close ≥ open on ≥ 99% of bars), raw bars to `data/raw/ibkr/<sym>.csv` (git-ignored, exchange-
licensed, never committed), resumable. **~80 minutes for the 239 names D336 has not already
pulled; D336's own 100 are ~35 minutes; both together ≈ 2 hours in one session.**

## 3. The comparison and the re-cost

Per name, on exactly the quoted dates (inner join, no look-ahead, D336's `[W]`): quoted half =
median over days of `(close − open)/2/mid`; **PUB** and **PB** on the fixture OHLC over the same
dates (D336's `ohlc_estimates`); `[N]` ≥ 200 quoted days; `[G]` `|ln(IB mid / fixture close)| <
0.05` on the last common date; `[U]` units. Per name the **ratio ρ = quoted / PUB** (and /PB),
and its median by the name's D438 tercile (assigned by the median modelled PUB at the name's B
trades — the tercile the trade was costed in).

**Re-cost of B at the quote** (D440's book, cap 20 primary, cap 40 reported; `[F]` events are
D436's 12,597; `[P2]` gross equals D440's to 1e-9):

- **Crossed at the quote**: each trade's 2c = 2 × (its own PUB half at t−1 × ρ of its name) +
  the kernel's commission + borrow. **For names in the sample ρ is measured; for the 389 names
  outside it ρ is imputed as the median ρ of the sampled names in the same D438 tercile — and
  every table prints the sampled-names-only line beside the imputed-all line.** This is the
  conservative line at the quote (both sides crossed).
- **Passive at the quote**: quoted half × 0.34 per side + 9 bp chase per order + borrow
  (D439's fractions). Reported, not gated on.

**The assumption, stated once:** ρ is measured on 2025-08 to 2026-08 and applied to trades from
2010 to 2023 — the estimator's *bias* per name is taken as stable over time even though its
*level* is not (the sampled names' modelled PUB is 29 at their trades and 37 over the last year).
Nothing on this data can test that; it is the assumption a quoted history would retire.

## 4. The bar

- **T1q** median ρ on the wide tercile < 1 by more than its bootstrap 2 SE — the modelled
  spread on B's carrying names is not a quote.
- **T3q** the book's net per bar under **crossed at the quote (imputed-all)** > 0 by 2 SE at cap
  20 (monthly block bootstrap, D440's).
- **T4q** the second half of the sample (2018-06 on) under the same line > 0 by 2 SE.
- **T2q** reported: the sampled-names-only per-trade net under crossed-at-quote > 0 by 2 SE.

**Candidate for the holdout reads (holdout 1 then 2, once each, both unseen by this line, only
on the principal's explicit word): T3q ∧ T4q, on the crossed line, not the passive one.** If the
book fails T3q at the quote, B is closed on its own noise and no cost measurement reopens it.

## 5. Predictions (computed from D438–D440 and this record's §1 facts; MODERATE on X-a/X-b, HIGH on X-e)

- **X-a** median quoted half-spread over the 272 names: **5–15 bp/side**; the sample's modelled
  PUB over the same year has median ≈ 37.
- **X-b** median ρ (quoted/PUB) **0.15–0.40**; ρ against PB higher by ~1.4× (PB is the smaller
  estimate, D336 §8a).
- **X-c** ρ **rises with the tercile** — wide-tercile median ρ ≥ 1.3 × narrow — because range and
  quote converge as names thin; T1q passes.
- **X-d** per trade at cap 20 under crossed-at-quote, sampled names only: gross ≈ +39 ± 10 on
  ~6,900 trades; 2c at the quote ≈ 0.28 × 52 + 1 commission ≈ 15–16; borrow 5; **net +15 to +25**,
  and T2q passes.
- **X-e** the book at cap 20 under crossed-at-quote (imputed-all): gross +2.24, cost ≈ 0.05 ×
  (16 + 5) ≈ 1.0, **net +1.0 to +1.4 per bar against an SE of 0.89 — T3q FAILS at 2 SE more
  likely than not**; cap 40: +1.0 to +1.3 against 0.59, a coin at 2 SE. **Even a favourable
  quote does not shrink the book's noise; what it decides is whether B is closed on cost or on
  noise, and whether the wide tercile is a per-trade object at all.**
- **X-f** the wide tercile under crossed-at-quote: **+60 to +80 per trade** (gross 106.5, 2c at
  the quote ≈ 0.35 × 84 ≈ 30, borrow 5).

X-e is the honest one: the pull retires an assumption that sits under every net verdict in the
second-zone and shock lines, and D336's convention question outranks B's; on B itself it most
likely converts "not a book at modelled cost" into "not a book at its own noise."

## 6. Not in scope

The holdouts (this record does not open them); any change to D336's design, sample or
predictions; any estimator beyond PB and PUB; intraday quotes; a quoted history before 2025-08
(IBKR's `BID_ASK` daily bars go back further, but a longer pull is a different pacing budget and
is declared, if at all, after this one returns). Forty-first look by object; no forward return
is newly examined — the re-cost uses D440's trades.

## 7. Files

`docs/decisions/D441-…md` (this record) · `scripts/run_d441_b_quotes.py` (to follow: `--plan`,
`--pull`, `--compare`, `--selftest`) · `data/d441_sample.json` (written by `--plan` before any
quote) · `data/d441_comparison.json` and a RESULT record after the principal's pull.
