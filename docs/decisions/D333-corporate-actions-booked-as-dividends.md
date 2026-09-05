# D333 — corporate actions booked as dividends: a bound on what the panel may add to a return

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-05
**Area:** Data integrity · **every study since the ragged panel (D285+)**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. What was found

`ragged_panel.load_ragged` applies every event-file dividend as
`total[i, t] += log1p(amount / close[i, t])`, **with no bound on the amount**
(`ragged_panel.py:174`). The events file records at least five corporate
actions as cash dividends with the price left at its post-transaction level:

| symbol | date | "dividend" | close that day | price move that day | implied return |
|---|---|--:|--:|--:|--:|
| **PNK** | 2016-04-29 | $38.86 | $11.04 | +0.9% | **+356%** |
| **GCI** | 2015-06-29 | $18.58 | $14.13 | −5.2% | +120% |
| CLH | 2011-07-27 | $53.75 | $53.75 | −3.0% | +94% |
| MMP | 2012-10-15 | $44.30 | $44.30 | +0.6% | +101% |
| GOCOQ | 2026-07-21 | $0.384 | $0.337 | +8.7% | +132% |

PNK is the Pinnacle/GLPI consideration; GCI the Gannett/TEGNA spin-off; CLH
and MMP are 2-for-1 splits booked as a dividend equal to the price. **PNK
alone is 14.1% of the incumbent's P&L and GCI 5.0%** (D331 §11) — the two
largest trades in the book STACK §0 has reported since D318.

**Most large dividends are fine.** The census (`d333_dividend_census.py`,
`data/d333_dividend_census.txt`): of 35,713 applied, 62 are 25% of price or
more, and for most of those the price fell by the distribution the same day
(HLSS −96.1% on a 24.8× payout; PENN −76.7% on 3.32×; BAX −44.4% on 0.82×), so
the total return is correct. **What separates a real distribution from a
mis-booking is whether the price fell.**

## 1. The rule, declared

For a dividend of amount `a` on a bar with close `c_t` and previous own-bar
close `c_{t−1}`, with `r = a / c_t`:

- the distribution **implies** a price move of `−r / (1 + r)`
  (`c_{t−1} = c_t + a`);
- the dividend is **applied** if `r < 0.10`, **or** the actual move
  `c_t / c_{t−1} − 1` is at or below **half** the implied move;
- otherwise it is **dropped** and logged: symbol, date, amount, close, ratio,
  actual move, implied move.

Two parameters, both round: **10%** (below it the price noise swamps the test
and the worst case is a 10% error), and **½** (a real distribution moves the
price by roughly all of it; half is a generous tolerance for same-day noise
and the ex-date timing). Neither is fitted to the five cases: PNK, GCI, CLH,
MMP and GOCOQ are inconsistent by 30 to 350 points, and HLSS, PENN, MTW, BAX
and the rest are consistent within 2.

**The fix lives in `load_ragged`**, so every runner inherits it, and the
panel's `meta` gains `dividends_dropped` and the list. A `--no-bound` path
keeps the old behaviour for the identity assertion.

## 2. Not a split problem

The incumbent's other large trades were checked (D331 §11): **VSA** 2025-01-31
is a +330% day on 500× volume with a 670 intraday high, back-adjusted for three
later reverse splits that are on file — real. **AHT** 2020-03-19 is +155% with
no split on that date and adjustment factors consistent across the window —
not a split artefact. **DRYS**, **WNW**, **CHK**, **KODK** are the manias and
bankruptcies they look like. Those are lottery days, not data.

## 3. Predictions

Q2 and Q4 are load-bearing. Q6 is against.

| | prediction |
|---|---|
| **Q1** | **Fewer than 15** of the 35,713 dividends are dropped. |
| **Q2** | **The incumbent's PB net at N=2/target/k=5 falls by at least 2 bp/bar** from +14.57, and its top-1 trade share falls below 14.1%. *Load-bearing.* |
| **Q3** | `retrace_leg` at k=20 moves by **less than 1 bp/bar** on either convention. |
| **Q4** | **`hist_L`'s long leg per-trade net at k=20 falls by at least 20 bp** from +97.0 (PB) — the PNK entry is in it. *Load-bearing.* |
| **Q5** | D323's thirteen at k=20 keep the same top-2 on both conventions. |
| **Q6** | *(against)* At least one of D323's thirteen moves by **more than 3 bp/bar** at k=20 — the price-momentum family (`hist_L`, `md`, `macd_*`) holds jump days. |
| **Q7** | Concentration (N=2 − N=19 on the incumbent) moves by **less than 3 bp/bar**. |

## 4. Stop conditions

- **Q2 and Q4 confirm** → STACK §0 is rewritten a third time, the incumbent's
  numbers carry a "post-D333" tag, and every FINDINGS number quoting the
  incumbent's P&L since D318 is annotated. **The books stay empty.**
- **Q1 fails high** (many drops) → the rule is catching real distributions;
  the ½ tolerance is re-examined *before* anything is repriced, and the record
  says which cases.
- **Q3 fails** → `retrace_leg` was carrying the same defect; its status as the
  best symmetric book is re-read.
- **Nothing here is promoted or demoted on its own.** It is a data fix.

## 5. Assertions

1. **[1] identity without the bound** — with the rule disabled the panel's
   `total_log_returns` is bit-identical to the current one, and the incumbent
   reproduces D332's PB cell (+14.57, +0.334) to 1e-9.
2. **[D] the dropped set** — every dropped dividend has `r ≥ 0.10` and an
   actual move above half the implied move; every applied dividend with
   `r ≥ 0.10` has a move at or below it; PNK, GCI, CLH, MMP and GOCOQ are in
   the dropped set; HLSS, PENN, BAX are not.
3. **[Z] nothing below 10% is touched** — every dividend with `r < 0.10` is
   applied exactly as before.
4. **[S] the sign audit, in money** (CLAUDE.md) — on the PNK bar, the old
   panel pays a long +356% and a short −356%; the new panel pays both the
   price move alone. Checked on the return arrays, not in prose.
5. **[L] the ledgers** — the incumbent's trade *entries* are unchanged by the
   fix except where a dropped dividend altered a score (dividend-adjusted
   returns feed some signals); the count of changed entries is reported.
6. **[6]** the self-test raises on a panel handed a free dividend.

## 6. Scope

**In:** the rule, the repricing of the incumbent (N=2, N=19, dv28), `hist_L`,
`retrace_leg`, D323's thirteen at k=20, and D329's four arms, under both
spread conventions. **Out:** every other cell (they inherit the fix and are
re-read as needed); split detection beyond §2; the holdout.

## 7. Files

`docs/decisions/D333-corporate-actions-booked-as-dividends.md` (this record) ·
`scripts/d333_dividend_census.py` and `data/d333_dividend_census.txt` (stage-0,
`72f3e89`) · `scripts/ragged_panel.py` (the fix, to follow) · runner and data
to follow.
