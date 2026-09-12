# D453 — issuance stage 1b: the same book, beta-hedged and volatility-scaled — one declared change, the same three controls, the same bar

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. In-sample
on the mining fixture; **no holdout is read.** D453 taken after `ls docs/decisions` and `git log
--all` showed D447–D452 used by the other session (D449 as uncommitted files) and nothing above.

## 0. What changes and what does not

D446 found the issuance effect per trade on both sides against state-matched names (2.5–2.6
control-SDs above the control median) and a book that failed four tests. Two of the four look like
*accounting* artefacts of the construction rather than signal failures: **the rotated persistent
selector earned +1.1 bp/bar with no issuance information**, because a unit-beta hedge of big
low-volatility longs and small high-volatility shorts has its own positive base rate; and **six
trades were most of the P&L**, because equal weight in small volatile names held six months is a
lottery by construction. This record changes the accounting and nothing else:

- **Selection is D446's, bit for bit.** The same score panel, the same masks, the same kernel,
  `cap = 126`, `n_max = 40` a side, the same trade ledger (row, entry bar, bars held, side).
  Nothing is re-selected; the runner asserts the ledger is D446's.
- **The mark changes.** Each position's hedged return per bar becomes `w_i · sgn · (v_it − β_i · m_t)`
  instead of `sgn · (v_it − m_t)`, with the kernel's own `v` (open-to-close on the entry bar,
  close-to-close after) and `m` (the floored market, `mkt_oc` on the entry bar, `mkt` after).
- **β_i** = OLS slope of the name's daily close-to-close return on the market over the **252 bars
  ending the bar before entry** (≥ 126 finite pairs; else 1), clipped to **[0, 3]**. Fixed for the
  life of the trade.
- **w_i** = `clip(σ_med(t) / σ_i(t), 0.25, 4)`, σ_i the standard deviation of the name's daily
  return over the **63 bars ending the bar before entry** (≥ 40 finite; else w = 1), σ_med the
  cross-sectional median σ among eligible names on that bar. Fixed for the life of the trade;
  the book is weight-normalised: `book_dep_x[t] = Σ_held w·sgn·(v − β m) / Σ_held w`.
- **[K2] identity, asserted before anything else is printed:** with β ≡ 1 and w ≡ 1 the re-
  accounting reproduces the kernel's `book_dep_x` on every bar and every trade's pnl to 1e-9.
- **Costs** per bar = Σ_entries w_j · (2·hs_j + commission_j + borrow_j) / Σ_t Σ_held w — the
  weighted round-trip cost per weighted deployed capital-bar, on the same PUB half-spread, the same
  commission, the same gc_htb borrow as D446; the passive line as D440. At w ≡ 1 this is printed
  beside D446's constant (the kernel used medians; the difference is disclosed, not hidden).

## 1. The three controls, unchanged in selection, re-accounted the same way

C1 (state-matched names at the real entry days, per cell, 100 draws), C2 (the score panel rolled
by a common offset, every 21 bars, exact on the grid), C3 (the persistent random selector on the
empirical transition matrix, 100 draws) — each produces a kernel ledger exactly as in D446, and
each ledger is marked with the same β and w rule. The controls therefore carry the same
accounting; nothing about them is easier or harder than the real book.

## 2. The bar — D446's, verbatim

Primary: the combined book, cap 126, n_max 40, crossed line, weighted.
**T1** gross > C2 p95 (exact) and > C3 p95 by 2 SE; **T2** net crossed > 0 by 2 SE; **T3** per-trade
gross > C1 p95 by 2 SE, short side required, long reported; **T4** era-2 net > 0 by 2 SE; **T5** ≥ 20
names to half the P&L and top 1% of trades ≤ 50%. Candidate: T1 ∧ T2 ∧ T3(short) ∧ T4 ∧ T5. The
per-trade control distances are reported **in the control's own draw SD** as well as the D373
margin (the D446 addendum's correction).

## 3. Predictions (computed from D446's ledger and controls; MODERATE)

- **X-a [K2]** holds to 1e-9 (an identity; if it fails the runner is wrong, not the thesis).
- **X-b the composition base rate collapses:** C2 p50 falls from +1.12 to **+0.2..+0.7**, within
  0.4 of C3's p50; C2 p95 from +3.77 to **+1.5..+2.6**.
- **X-c the real book:** gross from +2.30 to **+1.2..+2.0** (the unit-beta base rate was part of
  it), SE from 1.51 to **0.9..1.2** (vol scaling), net crossed **+0.3..+1.2** — **T2 fails at 2 SE
  more likely than not**; T1 becomes a coin on C2 and passes C3.
- **X-d concentration:** names to half from 5 to **12..25**, top 1% from 85% to **30..55%**;
  GameStop's share of the long leg from 29% to **under 15%** (its σ in October 2020 was high) —
  T5 a coin.
- **X-e per trade:** C1 baselines move toward zero — short p50 from −97 to **−30..0**, long from
  +34 to **−10..+20**; the real weighted means short **+30..+70**, long **+80..+150**; increments
  shrink to +60..+120 and keep their sign on both sides; T3 passes on at least the short side.
- **X-f** the mean β on the short side is **> 1.2** and on the long side **< 0.9** (the tilt the
  unit hedge mis-priced); the mean w on the short side < 0.8, on the long side > 1.1.

X-b is the study: if the rotated selector's base rate does not fall, the +1.1 was not the beta
tilt and the composition is doing something the hedge does not name.

## 4. Not in scope

Any re-selection (decile, cap, slots, score); any holdout; sizing beyond the declared w rule; any
second hedge instrument. Forty-fifth look by object; look #2 of the issuance line's forward-return
ledger, on the *same* trades as look #1 — the multiplicity is in the accounting rule, declared
once here.

## 5. Files

This record · `scripts/run_d453_beta_vol_book.py` (`--run`, `--selftest`; imports D446's
selection) · `data/d453_beta_vol_book.json` · RESULT.
