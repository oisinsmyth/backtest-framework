# D786 DIAG PRE-REG — the abstention oracle across six books: where each book's losing trades sit, on four families of pre-trade state, before any abstention rule is designed

*2026-10-03. The principal: "Start on the abstention principle"; then "In-sample formation first", all four families
of principle, and the index books plus the NG line.*

- **What it is:** step 1 of the abstention-principle formation. It is a descriptive profile, not a test.
  - **The goal (the principal's words):** "some underlying principle by which a strategy abstains and then trades
    when it's profitable" (memory: the-goal-is-an-abstention-principle).
  - **Per the principal's filter rule:** the oracle is shown first; the candidate rules are designed with the
    principal afterwards; the books are scored at the micro size each trades.
- **What it is not:**
  - no filter is built, no gate is applied, nothing is promoted;
  - the in-sample is spent for confirming an abstention rule (the 2026-10-01 review: states that sort in-sample are
    mostly 2020 and 2022, n_eff about 5–10 episodes).
  - Confirmation, if any rule is chosen, belongs to the forward recorder or a later vault.
- **The order:** this record is committed before the runner exists. The runner's output is shown to the principal
  before any rule is proposed.

## 1. The books (in-sample, 2016-01-01 → 2023-12-31, each at its traded micro and cost)

| book | mechanism type | trades from | known answer the runner must reproduce first |
|---|---|---|---|
| **D737** (NQ leads the Dow, slot 1) | continuation | D747's `other_lines()` (D746's twin, via `forward_f2_c1_ledgers`) | 1,699 trades |
| **NQ F2** (D716, slot 7) | continuation | the same | 274 trades |
| **C1** (D680, slot 9) | continuation | the same | 328 trades |
| **D776** (the CPI/jobs-report fade, slot 2) | reversion (event) | D775's `classify(sessions())` | 186 trades, +\$34.88 gross |
| **L4** (D781, slot 10) | reversion (close) | D778's `frame`, base book | 280 trades, +\$15.84 gross |
| **NG** (D723, slots 3/8) | flow | D723's `in_sample()` (D630's frame), one MNG at \$5 | 1,028 traded rows through 2025-02 (D630), cut here to 2016–2023 |

- **The continuation books' daily series** come from D747's `other_lines()`. That route bounds every read at
  2024-01-01 (`forward_f2_c1_ledgers.L_from_bars`, not D711's whole-fixture `load_root`).
- **D649** (NG's projected-profit line, slot 8) is not a separate book. It is the existing instance of family A below
  (an own-payoff-versus-cost filter on D630's trades), and it is reported as such.
- **The common window is 2016–2023 for every book,** so that no shared state reads 2024+ index data (the vault).

## 2. The oracle, per book

- **Totals:** trades, market-time share, mean gross and net, net Sharpe and Sortino, net without the best two years,
  the share of net from 2020 and from 2022, and by year.
- **The oracle ceiling:** the book traded only on its net-positive trades. It is the upper bound; its job is to show
  how much any rule could recover, not to be traded.
- **The losers:** the share of trades and of gross loss in the worst decile, and their years.

## 3. The four families of pre-trade state (declared now; every value is known before the trade's entry)

**A. Own payoff versus cost (the expected-profit filter, generalised).**
- σ\$: the book root's 20-session standard deviation of daily close-to-close moves, in dollars at the book's micro,
  ending the session before the trade.
- **The projection:** proj = β × σ\$. β is the slope of gross on σ\$ over the book's own earlier trades only
  (expanding, at least 30; before that, no value).
- **Reported:** proj ÷ the round trip, and the profile by its terciles and by "proj ≥ 2 × cost".

**B. Self-referential.** The mean net of the book's own previous 20 trades (at least 10), and its sign.

**C. Mechanism-typed shared state.** The same two shared states as D, with the hypothesis declared now:
- **continuation books do better in trending, rising-volatility states;**
- **reversion books do better in high-volatility, non-trending states.**
- The table shows each type's books side by side.

**D. One shared market state.** On NQ (the common clock), and also on each book's own root:
- **volatility level:** the 20-session realised volatility's percentile in its own trailing 250 sessions;
- **trend:** D778's trend state (the back-adjusted close against its 200-session average, UP or DOWN).

- **The roots' daily closes:** the front contract's last close each session, from `fut_day1m`, through 2023-12-31.
  Returns are zeroed across a change of front, as D778 does.

## 4. The profiles (the output)

- **For each book × state:** terciles (or sign, or UP/DOWN), each with n, mean net ± 2 SE, win rate, total net, and
  the share of the book's losing trades in it.
- **The cross-book view:** each state's top-minus-bottom tercile mean net for all six books in one table. Its sign
  shows whether a state sorts books alike (family D), by type (C), or not at all.
- **The 2020/2022 check:** each profile again without 2020 and 2022. The review's warning was that in-sample states
  are those years in disguise.
- **Reading rules (declared, not gates):**
  - a state is reported as **a candidate for discussion** only if its top-minus-bottom spread exceeds 2 SE in at
    least two books AND keeps its sign without 2020 and 2022;
  - everything else is reported as "no pattern".
  - The candidates go to the principal; nothing is built from them here.

## 5. Runner assertions

- **Each book's known answer** is reproduced before any profile (table above).
- **Every trade date is in 2016–2023.** Every state uses data strictly before the trade's entry session (asserted by
  recomputing the state for 20 sampled trades from a truncated series).
- **β uses earlier trades only:** an explicit loop re-derives it on 20 sampled trades.
- **The self-test:**
  - a planted state that sorts a synthetic book is found;
  - a shuffled state is not reported as a candidate;
  - the truncation audit raises on a state that reads the entry day.

## 6. Output

- `scripts/diag_d786_abstention_oracle.py`;
- `data/diag_d786_abstention_oracle.json` (statistics only).
- The result is a separate record and is shown to the principal before any rule is proposed.
