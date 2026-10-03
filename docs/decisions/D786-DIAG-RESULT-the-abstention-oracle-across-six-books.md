# D786 DIAG RESULT — no state is a candidate by the declared rule, but one family points the same way in all six books, with and without 2020/2022: a book's own projected payoff against its cost. The self-referential gate and the shared trend do not, and volatility level is mostly 2020/2022

*2026-10-03. One completed run of `scripts/diag_d786_abstention_oracle.py --run` (273 seconds).*
- **The order:** the [pre-registration](D786-DIAG-PRE-REG-the-abstention-oracle-across-six-books.md) (`510fd96e`)
  came before the runner (`8df27240`).
- **The first launch stopped on its own guard while loading the books,** before any profile was computed. D737's
  gross − net differed in the sixth decimal (float noise). The fix, rounding to 4 dp, is `a0550bab`.
- **Output:** `data/diag_d786_abstention_oracle.json`. Descriptive only: nothing is built or gated.

## 0. Checks

- **Every book's known answer was reproduced before any profile:** D737 1,699 trades, NQ F2 274, C1 328, D776 186
  (+\$34.88), L4 280 (+\$15.84), and NG's D630 table (1,028, D723's `check_known`). NG is then cut to 2016–2023
  (770 trades).
- **The lag audit:** each book's σ\$ was recomputed for 20 sampled trades from closes truncated at the state's last
  session; all equal. β was recomputed by explicit loop for 20 sampled trades; all equal.
- **The self-test:**
  - a planted state is found;
  - shuffled outcomes give at most one spurious candidate;
  - the audit raises on a state that reads the entry day;
  - β uses earlier trades only.

## 1. The oracle

| book | type | trades | market time | mean net (t) | net without its best two years | 2022's share of net | oracle (winners only) |
|---|---|---|---|---|---|---|---|
| D737 | continuation | 1,699 | 82% | +\$14.87 (3.07) | +\$6,933 | 51% | +\$128,643 on 855 |
| NQ F2 | continuation | 274 | 13% | +\$20.67 (2.57) | +\$671 | 67% | +\$15,465 on 152 |
| C1 | continuation | 328 | 16% | +\$15.66 (2.26) | +\$1,672 | 38% | +\$17,882 on 138 |
| D776 | reversion | 186 | 9% | +\$30.81 (2.41) | +\$2,040 | 13% | +\$13,596 on 102 |
| L4 | reversion | 280 | 17% | +\$12.08 (1.88) | −\$14 | −17% | +\$12,766 on 152 |
| NG | flow | 770 | 37% | +\$2.37 (1.39) | −\$1,404 | 176% | +\$12,604 on 370 |

- **The oracle ceilings are 2.2–22 times each book's actual net.** A rule with even a little accuracy is worth a lot.
  None has been found that is stable.
- **The worst decile of trades carries 38–67% of each book's gross loss.**

## 2. The four families: the top-minus-bottom spread in mean net per trade (z), and the same without 2020 and 2022

| state | D737 | NQ F2 | C1 | D776 | L4 | NG |
|---|---|---|---|---|---|---|
| **A. projected payoff ≥ 2 × cost** | +14.4 (1.8); **+6.8** | +24.9 (1.0); **+7.7** | +9.0 (0.7); **+4.4** | +19.6 (0.9); **+22.1** | +7.9 (0.5); **+12.4** | +24.4 (**3.6**); **+10.0** |
| A. projection terciles (high − low) | +22.8 (1.8); +16.3 | +24.9 (1.1); +16.8 | +7.6 (0.4); +7.4 | +45.4 (1.3); +53.9 | +21.6 (1.3); +18.5 | +15.0 (**3.2**); +7.3 |
| B. own trailing-20 net > 0 | +8.5 (0.9); +9.3 | −1.5 (−0.1); **−46.0** | +9.1 (0.6); −7.7 | +0.2 (0.0); +7.0 | −8.0 (−0.5); **−44.8** | +10.7 (**2.9**); +4.3 |
| D. NQ volatility percentile (high − low) | +24.9 (2.0); +13.2 | +35.9 (1.7); +3.1 | +5.4 (0.3); +1.1 | +19.6 (0.6); +1.0 | +17.7 (1.1); −2.1 | +10.7 (**2.4**); +2.4 |
| D. NQ in a downtrend | +27.4 (1.5); +35.0 | +36.7 (1.8); −23.0 | +10.4 (0.5); −14.0 | +28.9 (0.6); +44.5 | +1.6 (0.1); +16.5 | +14.2 (**3.1**); +3.1 |
| D. own root in a downtrend | as NQ | as NQ | as NQ | as NQ | +16.4 (1.3); +9.6 | −11.9 (**−3.3**); −2.3 |

- **The declared rule** (> 2 SE in at least two books, the same sign without 2020/2022) **finds no candidate.** Every
  significant sort is inside NG alone.
- **Family A is the one consistent pattern.** Trading only when the book's own projected payoff clears 2 × its
  round trip:
  - is better in all six books;
  - **and still better in all six without 2020 and 2022** (+\$4.4 to +\$22.1 a trade).
  - It is significant only in NG (z 3.6), where D649 (slot 8) already uses it.
- **Family B (the self-referential gate) fails.** Without 2020/2022, NQ F2 and L4 do much better after a losing
  stretch than after a winning one (−\$46 and −\$45). A book's recent edge does not predict its next trades.
- **Family C (mechanism-typed) is not supported.** Continuation and reversion books respond to volatility with the
  same sign, not opposite ones.
- **Family D (one shared state):**
  - the volatility level's spread mostly disappears without 2020/2022 (NQ F2 +3.1, C1 +1.1, D776 +1.0, L4 −2.1):
    it is those years again (the 2026-10-01 review's warning);
  - the trend's sign flips across books without them.

## 3. What family A is, and what it is not

- **Where it abstains in the index books, the trades still earn a little.** Without the filter's "below 2 × cost"
  trades, D737 drops 523 trades earning +\$5.10 each, NQ F2 49 at +\$3.33, C1 40 at +\$8.76, D776 27 at +\$21.36,
  and L4 19 at +\$6.21.
  - So it is a market-time and drawdown instrument there: fewer trades, the same direction.
  - In NG, the 594 abstained trades lose (−\$2.12 each); it is a profit instrument.
- **The confound to separate before it is called a principle:** σ\$ is a dollar volatility, and dollar volatility
  grows with the index's price. NQ roughly quadrupled over 2016–2023, so "projected payoff high" partly means "later
  years". Against a fixed micro round trip, that is itself economic (CLAUDE.md: cost in bp scales inversely with
  price). But a price-level drift and a volatility state are different principles. The two can be separated by the
  same projection with σ in basis points against the cost in basis points.
- **The in-sample cannot confirm it.** The consistency is six books' signs, not six independent tests: four trade NQ,
  and every book's σ\$ shares the same 2016–2023 rise.

## 4. Reading

- **No candidate by the declared rule; the families B, C and D are not supported in-sample.**
- **Family A, a book's own projected payoff against its cost, is the one family consistent across all six books,
  with and without 2020/2022.** It is the formation's lead.
- **Its next step is the principal's to design:** the form of the projection (dollar or basis point), the bar (2 ×
  cost or another), and where it is confirmed (the joint vault's frozen-line trades, pre-registered before the run,
  or the forward recorder).
