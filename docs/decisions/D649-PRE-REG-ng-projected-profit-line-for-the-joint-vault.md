# D649 PRE-REGISTRATION — the NG projected-profit line for the joint vault run: trade one MNG only when the projected move clears twice its cost

*Drafted 2026-09-28, on the principal's word: "We need to add this to the vault then - 'projected MNG ≥ 2 × $5'".
It is committed alone. Its runner (`scripts/ledger_vault_pp_ng.py`) exists and has produced the power study below and
the in-sample known answer; neither is evidence. The vault is read once, in the joint run (A10), and not before.*

## 0. Where this comes from — a post-hoc rule, disclosed as one

- **D630** passed H2 on NG ($66 a trade gross, t 5.01) and froze Stage A (`data/FROZEN_ledger_stage_a_ng.json`).
  Its vault look (D630 §8) is unchanged by this record.
- **The rule was chosen after reading NG's in-sample**, in today's exploratory scripts (all on D630's spent
  in-sample): `explore_d630_exits_micro.py`, `_by_year.py`, `_exits_prop.py`, `_component_full.py`, `_levers.py`,
  `_pit_check.py` and `_projected_profit.py` (outputs `data/ledger_d630_*.json`). The realized move was about 0.31 of
  the ledger's predicted impact |I|, so D630's gate (|I| ≥ 3 × cost) admits trades whose expected profit is about
  one cost. The projected-profit family was scored at k ∈ {1, 1.5, 2} at two sizes (six variants); the principal
  chose the strictest MNG cell.
- **Its in-sample numbers are therefore NOT evidence** (they are the reason to spend a look): 270 trades, $15.43 net
  a trade at one MNG, net Sharpe 1.39, without 2022 0.87; 165 of the 270 trades are 2022's.
- **The form is the ledger's own |I| (square-root impact, x_SR)**, the principal's choice. D648 found inventory risk
  (x_GM) the better form on CL and the better filter there; on NG's spent in-sample x_SR fits. That disagreement is
  recorded, not resolved.

## 1. The rule (point-in-time; `select` in the runner)

On D630's primary trade (fill at the close of bar t0+1, exit at the close of 14:29, no stop or target, D630's gate
and direction):

- **b_t** = Σ g_j·I_j / Σ I_j² over every traded day j **before** t (the in-sample's 1,028 traded days first, then the
  vault's own earlier traded days): the realized pass-through of |I|, OLS through the origin. A day's own outcome
  enters b only after its decision.
- **Projected MNG gross** P_t = b_t × |I_t| × 10,000 / 10.
- **Trade one MNG** when D630's gate passes **and P_t ≥ 2 × $5** (equivalently b_t × |I_t| × 10,000 ≥ $100).
- **Money:** one MNG earns g_t / 10 (g_t = D630's gross dollars per full contract) and pays **$5** a round trip ($3 +
  one $1 tick + $1 of entry slippage, D630's MNG line).

## 2. The vault read

- **Input:** D630's own vault trade table, built at the joint run by D630 §8's code with the cut moved: one row per
  business day 2025-03-01 → 2026-09-18 with `day`, `traded`, `absI_usd`, `g`. **If D630's vault inputs cannot be
  built, this line is not scored**, and the gap is written up.
- **PASS** if all hold: (i) **at least 15 trades**; (ii) the mean MNG gross is > 0 with **one-sided t ≥ 1.2816**
  (p < 0.10, D630 §8's bar); (iii) **the mean MNG net is > 0**. **FAIL** otherwise. **UNRESOLVED (too few trades)**
  below 15: the look is then spent and nothing is concluded.
- **Reported beside, never gating:** the full-size net; the trades by month; the path of b_t; D630's unfiltered vault
  line beside this filtered one (the same days); the net Sharpe and Sortino of the MNG daily P&L; the trade
  distribution (CLAUDE.md's groups).
- **One look.** `--vault` refuses without the principal's word, refuses unless this record's freeze verifies
  (`data/FROZEN_ledger_vault_pp_ng.json`: the runner's sha256, this record's, the parameters), and refuses a second
  opening.

## 3. Multiplicity and consequence

- **A new programme family, slot 8** (α 0.005, the first of the three reserved slots; no amendment needed):
  "ledger H2 projected-profit (NG)". Its promotion check at the programme level uses 0.005 and is reported.
- **A PASS** is the out-of-sample confirmation R8 requires for this construction. It admits nothing by itself: the
  books still need their hurdles (for the prop book, the components ledger and hurdle P). **A FAIL** closes the
  projected-profit line on NG; no re-tuning of k, the form or the size afterwards.

## 4. POWER (`data/ledger_vault_pp_ng_power.json`, seed 649)

The vault's 390 business days are drawn in 20-day blocks from the in-sample trade table (its traded share, |I| and g),
with the in-sample's expected move (b × |I| on traded days, b = 0.314) scaled by s; b_t is warmed on the whole
in-sample, as at the joint run. 2,000 draws per row.

| edge kept in the vault, s | PASS | FAIL | UNRESOLVED | trades, median (p10–p90) |
|---|---|---|---|---|
| 1 (the in-sample's) | **0.74** | 0.23 | 0.04 | 52 (24–87) |
| 0.5 | 0.41 | 0.56 | 0.03 | 49 (24–79) |
| 0.25 | 0.24 | 0.73 | 0.03 | 49 (23–78) |
| 0 (none) | 0.09 | 0.87 | 0.04 | 47 (24–75) |

- **Read it as:** the look is decisive only if the vault keeps most of the in-sample edge. At half the edge it is a coin
  toss, and the false-pass rate at no edge is 9%.
- **Optimistic in one way:** the blocks resample the in-sample's regimes, 2022 included. The vault's gas price and fund
  sizes are unknown (unread), and the trade count may be far from 50.

## 5. What this does not touch

- D630's frozen Stage A, its files and its vault criteria (§8) are unchanged; this line reads D630's vault trade
  table and applies a filter to it.
- No vault or post-vault NG data is read before the joint run.
- **Deviations** are listed in the output and never replace a verdict.
