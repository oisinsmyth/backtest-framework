# D789 DIAG PRE-REG — signal strength against its own gate: do the six books earn more on the trades whose trigger is far past its threshold than on those just over it?

> **Renumbered from D787 on 2026-10-03.** Another session committed the China-open turned fade (D787-STAGE-0-...) to main under D787 first. Commit messages, the script names (`scripts/diag_d787_*.py`) and the data outputs (`data/diag_d787_*.json`) keep the old number.

*2026-10-03. The principal, after D788: "Signal strength vs its own gate".*

- **What it is:** step 2 of the abstention-principle formation. It is descriptive and in-sample (already read),
  like [D788](D788-DIAG-RESULT-the-abstention-oracle-across-six-books.md). No filter is built and nothing is gated or
  promoted.
- **The candidate principle:** a strategy trades only when its own trigger is well past the threshold that fires it.
  - It is general (one rule for every book), but the input is each book's own signal.
  - It is a property of the trade, not of the market. D788 found no market state that survives without 2020/2022.
- **The order:** this record is committed before the runner exists. The output is shown to the principal before
  any rule is designed.

## 1. The books and their trigger magnitudes (2016–2023, as D788; each known answer reproduced first)

| book | trigger magnitude m (larger = further past the gate) | the book's gate | source |
|---|---|---|---|
| D737 | \|Z\| of the NQ − YM spread at the trigger minute | \|Z\| ≥ 1.0 at the first crossing (D735's `trigger`) | D735's `spread`/`trigger` via D737's `cell`, on D746's text-restricted rth bars |
| NQ F2 | the tier `tc` | `tc` ≥ q (D707's `f2`) | `forward_f2_c1_ledgers.f2_rows` |
| C1 | −`ctier` (more compressed = stronger) | `ctier` < 1/3 | `forward_f2_c1_ledgers.c1_rows` |
| D776 | the impulse \|x\| (08:29 → 08:34) | none: every release trades | D775's `classify(sessions())` |
| L4 | the closing move \|c\| | \|c\| ≥ the trailing q80 | D778's `frame` |
| NG | the predicted flow \|I\| (`absI_usd`) | D630's own gate (its `traded` flag) | D723's `in_sample()` |

- **The strength:** the percentile of a trade's m among the book's own earlier trades (expanding, at least 30; before
  that, no value). This uses only earlier trades, and it puts all six books on one 0–1 scale whatever the trigger's
  units.
- **D737's trigger minute is its first crossing,** so its overshoot is usually small. Earliness (an earlier trigger
  minute) is reported beside it as a second measure for D737 only. It is not used in the cross-book rule.

## 2. The profiles

- **For each book:**
  - strength terciles (n, mean net ± 2 SE, win, total, share of losers);
  - the strong half against the weak half (strength ≥ 0.5 against < 0.5), with their spread and z;
  - all of it again without 2020 and 2022;
  - **the weak half's share by year,** the calendar check that exposed family A (D788 A1/A2);
  - **the correlation of strength with D788's NQ volatility percentile,** to show whether strength is volatility in
    disguise.
- **The cross-book table:** the strong-minus-weak spread and its z for all six books, with and without 2020/2022.
- **The reading rules (declared, not gates):**
  - **A candidate for discussion** needs:
    - the strong-minus-weak spread > 2 SE in at least two books;
    - the same sign in at least five of the six books, both with and without 2020/2022;
    - and the weak half spread across the years, with no year above 60% of the weak trades.
  - Everything else is reported as "no pattern" or "calendar".
  - Candidates go to the principal; nothing is built here.

## 3. Runner assertions

- **Each book's known answer first** (D788's counts; D737 1,699 trades on D735's cell).
- **Strength uses earlier trades only:** an explicit loop recomputes it for 20 sampled trades per book.
- **The magnitude matches its trade:** for 20 sampled trades per book, m is re-derived from the book's own row or
  frame.
- **The self-test:**
  - a planted strength effect is found;
  - shuffled outcomes are not candidates;
  - the strength audit raises on a strength that includes the current trade.

## 4. Output

- `scripts/diag_d787_signal_strength.py`;
- `data/diag_d787_signal_strength.json` (statistics only).
- The result is a separate record, shown to the principal before any rule is proposed.
