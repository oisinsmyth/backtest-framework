# D602 PRE-REG — **basis momentum on the six CME FX roots, measured in covered-parity space** — the deposit's T2 with its open questions 1 and 2 decided: quarterly deliveries only, and the signal built on the calendar spread's deviation from covered interest parity so that a raw-settlement pass cannot be rate-differential momentum in disguise; in-sample 2011-07 → 2023-12 against D564's nulls, the raw-settlement cell beside as the named failure mode, the 2024+ slice on these six roots **reserved, unread, and read only on the principal's word if the primary passes**

**Pre-registration, committed before the runner exists (R8). A trial on a universe this line has
not scored: the six FX roots' 2024+ slice is unseen by basis momentum (holdout multiplicity is
per line; D574 spent the commodity slice, not this one).** In-sample only here; the forward read
is a separate step. Nothing admitted (R15); the component line is reported at micro size
whatever the verdict.

*2026-09-21, on the principal's word ("FX with a rates fetch"). `BASIS_MOMENTUM.md` §2.9 makes
the extension principled: there is no storage, no convenience yield and no producer hedging in
an FX future, so if the effect appears there the mechanism cannot be physical. §8 blocks the
naive port: an FX curve is an interest-rate differential, and cumulated changes in its shape are
rate-differential momentum unless the parity component is removed — "the FX analogue is to work
in basis-versus-covered-parity space rather than raw forward points". The rates are on disk (the
D601 OECD fixture, seven currencies, monthly); the curves are the settlement strip (D556), on
which every one of the six roots has at least four eligible deferred contracts at every
month-end. Equity index is excluded (its curve is financing minus expected dividends, and the
dividend-residualised data the deposit requires is not on disk).*

---

## 1. Universe, cycle, rates

**Roots.** 6E 6B 6J 6A 6C 6S — every one quoted in USD per unit of foreign currency in the strip
(6J ≈ 0.0095). **Delivery cycle, decided (open question 1):** the column set passed to
`choose_nearby` is restricted to the quarterly deliveries {3, 6, 9, 12}. The strip lists serial
months only from 2014/2017 on five of the six roots and none on 6S; serial settlements are the
quarterly plus a deterministic carry adjustment; without the restriction the T1–T2 gap would
flip between one and three months across the sample and across the year. T1 = the first
quarterly delivery ≥ *m*+2, T2 = the next, three months later; tenors τ1, τ2 from the actual
third Wednesday of each contract month (2–4 and 5–7 months at formation).

**Rates.** The D601 OECD monthly 3-month interbank averages: at month-end *t* the value dated
*t−1* (the last one published by *t*; OECD publishes month *m* in the first half of *m*+1), no
interpolation; the one filled cell (USD 2020-04) treated as present and named. Day count 360 for
USD, EUR, JPY, CHF, CAD legs and 365 for GBP and AUD.

**Eligibility.** As D564 — all twelve monthly R1 and R2 finite, neither contract stale (the
settlement unchanged over the three sessions ending at formation) — plus the twelve lagged rate
observations present for both legs. First eligible month-end 2011-06-30; positioned sessions
2011-07-01 → 2023-12-29; PRIMARY window 2016–2023 beside the LONG one; nothing from 2024-01-01.

## 2. The construction — the spot-free pair form

In logs, the month-*s* contribution to the commodity signal is ln(1+R1_s) − ln(1+R2_s) =
−Δ_s ln(F2/F1): basis momentum is minus the cumulated change of the log calendar spread. Covered
parity gives the spread's fair value on the pair chosen at *s−1*,

`D_s = [ln(1 + r_usd τ2) − ln(1 + r_fx τ2)] − [ln(1 + r_usd τ1) − ln(1 + r_fx τ1)]`,

in which spot cancels identically. **The primary signal:**

`BM_fx(t) = Σ_{s=t−11..t} [ ln(1+R1_s) − ln(1+R2_s) + ΔD_s ]`,

ΔD_s the change of D over month *s* on the pair chosen at *s−1*, each month's own tenors and
rates. Since τ2 − τ1 is fixed per pair, ΔD_s ≈ (τ2 − τ1)·Δ_s(r_usd − r_fx): **on raw settlements,
FX basis momentum is minus a quarter of the twelve-month change in the 3-month rate
differential plus the basis term** — the deposit's objection made exact, and why the raw cell
cannot be the primary. The additive log form is used (a basis is a log quantity); the paper's
product form on raw settlements is the diagnostic cell.

**Declared limitation.** With a single 3-month tenor, D also carries the 3-to-6-month slope of
each rate curve (the expected policy path); BM_fx removes the spot-differential drift, not
expected-path changes. No keyless 6-month foreign rate exists. The monthly-average rate against
a month-end settlement adds noise of order a few basis points in policy months; it washes out in
the twelve-month sum and does not bias the sign.

**Harness for the adjustment, pre-registered — the trial is void, not failed, if it fails:**
pooled over root-months, Spearman(BM_raw, Δ12 rate differential) < −0.5 **and**
|Spearman(BM_fx, Δ12 rate differential)| < 0.3. Beside: BM_fx with lag 0 (look-ahead, diagnostic
only) against lag 1; Spearman(BM_fx, BM_raw); a step check on the USD series across LIBOR's end
(2021-06 → 2023-12), reported, not patched.

## 3. Cells, legs, nulls

`membership_fixed` with **n_leg = 2, min_eligible = 4** (D557's tercile rule hard-codes a minimum
of nine and would flat every month on six roots; not reused). Ties by symbol, counted. A month
with fewer than four eligible roots is flat, counted.

| cell | | verdict weight |
|---|---|---|
| **PRIMARY** — BM_fx, EW High2/Low2 on the nearby return, gross | LONG 2011-07 → 2023-12; PRIMARY 2016–2023 beside | the verdict |
| time-series form — sign of BM_fx de-meaned by its expanding own mean (≥ 12 prior), 0.40/σ | D564's `positions_from_signs` | N2's second member |
| **BM_raw** — the paper's product form on raw settlements, quarterly-restricted, EW High2/Low2 | its own N1 null | **none** — the named failure mode |
| dollar High2/Low2 at minimum size (micros exist for the FX roots), $3/$6 RT + one tick, rolls charged | D555's `dollar_book` | the component line |

**Nulls.** N1: rotation within each root's live index, purge 252 both ends, every offset within
the PRIMARY window, the exactness guard on 20 offsets against `book_return_loop`. N2: the family
maximum over {primary, time-series}. N3: name-randomised membership, 2,000 draws, p95 with its
bootstrap SE and the D373 unresolved rule.

## 4. Predictions, in the runner's quantities

| # | prediction | falsifier |
|---|---|---|
| P-1 | primary gross Sharpe 2016–2023 > 0 and above N1 p95; the family max above N2 p95; **point prior 0.0–0.3** (a 13-year Sharpe has SE ≈ 0.28: a mechanism test, not a component candidate) | inside → NOT SUPPORTED on FX |
| P-2 | the adjustment harness holds (§2) | fails → the trial is VOID |
| P-3 | the named outcomes: BM_raw passes and BM_fx fails → "rate momentum, not imbalance" (the deposit's own falsifier: "run naively, T2 would likely return a positive result that means nothing"); both pass with Spearman(BM_fx, BM_raw) > 0.8 → the adjustment was immaterial and the effect exists in FX; BM_fx passes alone → the mechanism's prediction | — |
| P-4 | eligible roots ≥ 5 on ≥ 90 % of month-ends; flat month-ends ≤ 5 % | fails → the universe is too thin for a 2/2 sort; reported |
| P-5 | the PRIMARY-window Sharpe within 0.4 of the LONG-window one | fails → the effect is era-bound; the eras reported |
| P-6 | component line at micro size: net Sharpe, hit, skew, gross beside, ρ with D564's commodity book — no prediction on the level; ρ with D564 predicted < 0.3 (different curves, different clearing) | — |

**The forward slice.** The 2024-01-02 → 2026-09 sessions on the six FX roots are **reserved and
unread by this record**. If P-1 holds, the forward read is a separate step on the principal's
word, with the forward predictions written before it (the D574 pattern: the composition
predicted before the total).

## 5. Audits, each proven to RAISE on a break that hits what the assertion reads

(a) the FX nearby series by D564's functions on the quarterly-restricted columns, with R1/R2
recomputed by a pandas second path in `bm_pandas`'s style on 300 seeded cells to 1e-10; break =
the delivery threshold shifted one month; (b) the CIP correction by a second path (pandas on the
rate fixture, never the numpy loop); break = the rate lag removed; (c) sign in money on a
synthetic rate path — a rising USD differential lowers BM_raw and leaves BM_fx unchanged to
1e-12; break = the correction's sign flipped; (d) lag, sign-in-money and right-quantity audits
as D564 (the unlagged grid, the negated and mis-lagged dollar book, the daily grid); (e) the
leg membership by D557's second path; (f) the exactness guard; (g) `REQUIRED_OUTPUTS` first;
`encoding="utf-8"` on every text IO call.

## 6. What is read, and what is not

The settlement strip for the six FX roots to 2023-12-29; the breadth fixture for the live index
and the contract specifications; the D601 OECD rates fixture to 2023-12. **Not read:** any
session, settlement or rate from 2024-01-01 on; the commodity roots' anything beyond D564's
artifact for the correlation in P-6. **Runtime:** the strip for six roots is small; N1 over ~2,000
offsets × 3 cells and N3 2,000 draws — minutes.
