# D342 — `rsi` under the floor and the open fill: the candidate record

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. **Nothing in this study can admit a strategy to the book** — R8 needs an
out-of-sample test on an unseen fixture and the holdout stays at zero reads. What it can
do is give `rsi` the record D338 gave `retrace_leg`, on the honest conventions, and say
whether it is a candidate.
**Date:** 2026-09-05
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D341 found the one book that *gained* from honest scoring. `rsi` symmetric at k=20 under
the F0 deal filter was −2.55 PUB bp/bar on the unfloored universe with the same-close
fill; under the declared floor and the next-open fill it is **+3.52**, Sharpe 0.18, and
its floored legs carry no overnight-gap premium at all (+0.7 long, −7.7 short), so the
fill barely touches it. It has fourteen names to half its P&L against `retrace_leg`'s
nine, a 5.5% top trade against 9.9%, and 12% of its P&L in dead names against 44%. It was
first per trade in D335 and has never had a record of its own. D341's stop condition on
Q5 says it gets one.

## 1. What is already known, and is therefore an identity here

From `data/d341_floor_and_open_fill.json`, cell `RSI/floor/open`, PUB: net **+3.52**
bp/bar (PB +8.53), gross +14.72, net Sharpe **+0.181**, maxDD 13,907, held half-spread
28.1 bp at $44, 1,215 trades, mean +76.1 against a median +221.3, symmetric trim
**+88.3**, top 1% +40% and bottom 1% **−54%** of P&L, 627 names, **14** to half, top-5
name share 25.2%, 8 of 14 years net-positive, dead names 12.1% of P&L, the cheapest
tercile 62%, invariant PUB **−4.8** a trade, top trade FPRX short entered 2020-11-13 at
5.5%. **None of these is a prediction.** The runner reproduces them to 1e-9 and the
record does not re-announce them as findings.

## 2. The cell, fixed

`rsi` symmetric · depth 2 · k=20 · D303 target · F0 deal windows removed from the score
· **the floor** (as-traded close ≥ $5 at t−1 and the dv28 pass, replace semantics) ·
**the open fill** · D333 panel · D334 cache · PUB primary, PB beside · GC+HTB borrow as
new keys · both lenses. `retrace_leg` under the same conventions is simulated beside it
for the tail comparison only.

Reported: the four groups via D322's functions with `contributions_fill`; the top-five
table with as-traded price and entry-day dollar-volume percentile; the top trade's bars
printed with open, high, low, close, volume, `r1`, the open-to-close return and any
dividend; the per-leg implementation-lag premium; a 200-draw rank-rotation null with
teeth on gross, the matched-cost net null beside it, and **the number of distinct
shifts drawn stated on every line** (D341 §3).

## 3. Predictions

Q1 is load-bearing. Q4 and Q6 are against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* gross bp/bar above the gross null's p95, p95 > 0, and above **at least 22 of the 24** distinct rotations. |
| **Q2** | net Sharpe under PUB above the matched-cost net null's p95. |
| **Q3** | *(data and liquidity gate)* on every one of the top five trades: no dividend ≥ 1% of the close on any bar of the hold, the biggest day's `r1` equals the raw close-to-close move within 1 pp, the as-traded price at entry ≥ $5 and the dollar-volume percentile > 0.28. |
| **Q4** | *(against)* the bottom 1% of trades (12) share **fewer than 4 names** with `retrace_leg` floor/open's bottom 1%. The two books' left tails are different names. |
| **Q5** | the long leg's invariant PUB net per trade **exceeds the short leg's** — `rsi`'s edge is on the oversold side, as D335 found unfloored. |
| **Q6** | *(against)* neither era half carries more than **65%** of the P&L. |
| **Q7** | GC+HTB borrow < 0.5 bp/bar and PUB net after it stays **> +3.0**. |
| **Q8** | breakeven half-spread per side ≥ **1.3×** the held PUB half-spread. |
| *check* | every number in §1 reproduced to 1e-9; `retrace_leg` floor/open reproduces D341 too. |

## 4. Stop conditions

- **Q1 fails** → `rsi` is not a candidate; the +3.52 is a book without an ordering,
  recorded as such.
- **Q3 fails on the dividend or `r1`-vs-raw clause** → nothing is read; the event is
  named and the panel is looked at first (D333's rule). Fails on liquidity → the floor
  has a hole and the record says where.
- **Q1 and Q2 hold** → `rsi` under the floor and the open fill is the personal track's
  **declared candidate**, frozen at these parameters; the R8 out-of-sample design is
  written here (a fixture disjoint in names or time; PUB net > 0 under the open fill;
  gross above its own null's p95; symmetric trim above the round trip; no trade above
  10% of the ledger; at least 10 names to half) and **not run**. Whether the one read
  is worth spending on a +3.5 bp/bar, 0.18-Sharpe book is stated plainly in the result
  and left to the principal. Book: still empty.
- **Q4 fails** (the left tails share ≥ 4 names) → the two books lose money on the same
  events, and a portfolio of them would not diversify the tail; recorded.
- **Q6 fails** → an era flag on the record, as D338 carried a concentration flag.

## 5. Assertions — properties of code

| | |
|---|---|
| **[K]** | cache key with `ragged_panel.py`; npz newer than the builder |
| **[F0]** | 1,719 filings, 2.54% |
| **[R]** | raw factor equals the census's; the floor's share equals the census's 29.2962% |
| **[F]** | fallback cells counted |
| **[1]** | `rsi` floor/open and `retrace_leg` floor/open reproduce D341's cells to 1e-9 on net, Sharpe, invariant per trade, both conventions; the §1 group-2 and group-3 numbers reproduce |
| **[A]** | lag audit: the floored `rsi` long gate rebuilt from the floored score at t−1 by a direct stable argsort equals the gate on 200 sampled bars; the unlagged rebuild differs on most |
| **[S]** | every trade equals `pnl_recomputed_fill` to 1e-12; a favourable excess path pays positively on every long and short |
| **[RQ]** | compound accumulation: same entries, different P&L; group 1 scores the summed ledger |
| **[2]** | reconciliation with `contributions_fill`; rejects a ledger missing a trade |
| **[3]** | symmetric trim; rejects an asymmetric one |
| **[N]** | rotation moves the book; distinct shifts counted |
| **[B]** | borrow reconciles to 1e-9; `net_bp` untouched |
| **[U]** | `rsi` is dimensionless: bounded in [0, 100] on every finite cell; unchanged on a synthetic path when every price is multiplied by 10 |
| **[6]** | [1] raises on a book handed +5 bp on 200 masked bars |

## 6. Scope

**In:** the one cell and its comparison cell, both lenses and conventions, borrow, the
four groups, the top trade's bars, the null. **Out:** any k, depth or threshold sweep
(D323 found `rsi` peaks at k=10 unfloored; k=20 is D335's choice and stays); the
holdout; the out-of-sample read.

## 7. Files

`docs/decisions/D342-rsi-under-the-floor-and-the-open-fill-the-candidate-record.md`
(this record) · `scripts/run_d342_rsi_candidate.py`, `data/d342_rsi_candidate.json` (to
follow). Prior evidence: `data/d341_floor_and_open_fill.json`.
