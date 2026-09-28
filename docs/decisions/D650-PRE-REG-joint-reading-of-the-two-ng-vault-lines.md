# D650 PRE-REGISTRATION (addendum) — how the two NG vault lines are read together: the mechanism and the trade are separate verdicts

*Written 2026-09-28 on the principal's word, before the joint vault run (A10) and with no vault data read. The
principal: "if the gross survives and the net does not on the full mechanism without the trades, but the profit
projections work then that's a win?" This record fixes that reading in advance. It edits nothing frozen: D630's
vault criteria (D630 §8, `data/FROZEN_ledger_stage_a_ng.json`) and D649's (`data/FROZEN_ledger_vault_pp_ng.json`)
are applied exactly as written. It only names their parts and states how the combinations are read.*

## 1. D630's vault look, split into the two verdicts it already contains

D630 §8 passes the vault if (i) the vault's mean g (dollars per full NG contract, D630's primary trade on its gated
days) has the in-sample sign, (ii) one-sided p < 0.10 (t ≥ 1.2816), and (iii) the net mean is > 0 at 1× cost ($26).
Those three clauses are reported as two named verdicts:

| verdict | clauses | meaning |
|---|---|---|
| **MECHANISM** | (i) and (ii) | the funds' predicted rebalance still moves NG's price into the settlement, in the vault |
| **TRADE (full size, unfiltered)** | (iii), read only when MECHANISM holds | that move still covers a full contract's cost on every gated day |

D630's own verdict (PASS only if all three hold) is unchanged and is reported as D630 wrote it.

## 2. The joint reading, fixed now

D649 (the cost-filtered MNG line) is read as D649 wrote it: PASS / FAIL / UNRESOLVED (fewer than 15 trades).

| D630 MECHANISM | D630 TRADE | D649 | **the line's reading** |
|---|---|---|---|
| holds | net > 0 | PASS | **mechanism confirmed; the full-size trade and the cost-filtered MNG trade both confirmed** |
| holds | net > 0 | FAIL or UNRESOLVED | mechanism and the full-size trade confirmed; the filter is not confirmed |
| holds | net ≤ 0 | **PASS** | **mechanism confirmed; the cost-filtered MNG trade confirmed** — the line's success case, whatever the unfiltered full-size net shows |
| holds | net ≤ 0 | FAIL | mechanism confirmed; **real, not tradable** in the vault's regime |
| holds | net ≤ 0 | UNRESOLVED | mechanism confirmed; the filtered trade untested (too few trades); no trading conclusion |
| fails | — | PASS | **not confirmed.** A filtered pass without the mechanism is read as chance (D649's 9% false-pass rate at no edge); nothing is promoted |
| fails | — | FAIL or UNRESOLVED | the NG line closes |

- **"Confirmed" is R8's out-of-sample confirmation of that construction, not admission.** A confirmed trade enters
  a book only through that book's hurdles (for the prop book: the components ledger and hurdle P on the assembled
  book).
- **No reading is chosen after the run.** A combination not in the table is written up as UNRESOLVED and put to the
  principal.
- D630's MECHANISM verdict is also the vault's reading of the mechanism for the settlement ledger as a whole on NG.

## 3. What this does not touch

- No frozen file, criterion, parameter or code is changed; D630 and D649 are run exactly as frozen.
- No vault data is read; the joint run happens once, on the principal's word.
