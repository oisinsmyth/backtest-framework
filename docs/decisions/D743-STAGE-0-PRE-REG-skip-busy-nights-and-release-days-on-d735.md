# D743 STAGE 0 PRE-REGISTRATION — a skip layer for D735's NQ-against-the-market legs: abstain after a busy two-way night and on 08:30 CPI and jobs days

*2026-10-01.*
- *The principal: "Ok lets try Idea 1" — idea 1 of the post hoc C1 mechanism diagnostic (an Opus analysis and an
  independent Fable 5.1 agent's, compared; scratch notes in `temp/c1_opus/` and `temp/c1_fable/`).*
- *Design choices, both the principal's:*
  - **the target is D735's legs** (the honest test: nobody has cut them by these vetoes), not NQ's or ES's range breaks,
    where the idea was found;
  - **the vetoes are a busy overnight and CPI / employment-report days.** FOMC and the large-gap veto were offered and
    not chosen.
- *Numbered D743, the next free number in `docs/internal/AITODO.md`.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29).*

## 0. Context and what is already known

**The idea.** In the C1 diagnostic, NQ's yesterday's-range breaks that C1 does *not* take lost on exactly the
sessions where the day's information had arrived before 09:30 (post hoc, on the data the idea came from):
- after a busy two-way overnight (the top third of the overnight range): −4.1 bp net a trade (t −1.5);
- on CPI days: −15.5 (t −4.0; −10.1, t −2.2, on Opus's wider set of breaks);
- on ES's yesterday's-range breaks the busiest third was −1.2 against +5.7.

**The mechanism offered** (a story, not a measurement): when the information has been priced before the open
(D506: "the open prices the night"), a move after the open is the tail of a spent move,
not the start of a new one. A skip layer cannot create edge; it can only stop the book trading where it does not earn
— the principal's standard ([D736](D736-STAGE-0-RESULT-only-the-compression-break-earns-and-abstains.md)).

**What is NOT known.** Neither veto has been cut on D735's trades by anyone. D735's legs trade NQ's move against the
market at about 10:00 (93–97 % of entries), not a break of yesterday's extreme, so the transfer is a genuine question.

**What a pass can and cannot do.**
- YM k1.0 1σ_rem is [D737](D737-PRE-REG-nq-leads-the-dow-for-the-joint-vault.md), **frozen in programme slot 1.**
  Nothing here changes it. A SUPPORTED veto on its in-sample twin could become, on the principal's word, a forward
  monitor on the recorder's D737 ledger or a layer pre-registered after D737's vault reads.
- EQ k1.5 1σ_rem is D735's best cell after the fact, in no vault. A pass is in-sample evidence only; NQ's 2024+ is
  spent by D716/D680/D737, so its only clean confirmation is forward.

## 1. The objects

**The two cells**, rebuilt with D735's own functions (`B.panels`, `minute_x`, `align_rows`, `spread`, `trigger`,
`e1_tables`, `g_at`) on panels from D738's `read_cut` (a chunked read keeping day ≤ 2023-12-29) and D727's
`panel_from_raw`:

| cell | rule | known answer, checked first |
|---|---|---|
| **YM k1.0 1σ_rem** | D737's `cell(pnN, pnY)` | D737's `check_known`: 1,699 trades, mean net D735's to 1e-9 |
| **EQ k1.5 1σ_rem** | the leg is the mean of ES / YM / RTY's x, as D735's runner | 1,131 trades, mean net +\$18.1118766142761 to 1e-9 |

One MNQ, at D735's cost line (\$4.0671 a round trip, `M711.cost_line("NQ")`).

**The window** is every trade whose overnight percentile is defined (§2). The count dropped by the 250-session
burn-in is reported; those trades are not scored. Every statistic, including the take-all baseline, is on that window.

## 2. The vetoes (fixed rules, no fitted parameter)

**V1 — a busy two-way overnight.** Skip iff p_on ≥ 2/3.
- on_range = (Globex high − Globex low over 18:00 → 09:29 − |09:30 open − prior close|) / ATR20, NQ's own: D671's
  `overnight` and `session_features` unchanged. It is C1's overnight half: the two-way range net of the gap.
- p_on = D671's `tiers`: its walk-forward percentile among the previous 250 finite sessions (strictly earlier).
- Loaded through D680's Globex chain under D720's `lowered_cut`, with D680's CUT held at 2024-01-01 (the recipe of
  the C1 diagnostic, which reproduced D672's per-year C1 counts).

**V2 — a release day.** Skip iff the CME session calendar marks the session `cpi` or `empsit` (NQ rows; 96 + 96
sessions in 2016–23, never the same day).

**V3 — either.** Skip iff V1 or V2.

**Six tests:** 2 cells × 3 vetoes.

## 3. Step 1 — the oracle and the size of the prize (reported first)

Per cell, on the window:
- **O1, the ceiling:** keep only trades with net > 0.
- **O2, the same-size ceiling:** for each veto, skip the same number of trades, choosing the worst by net. A veto's
  **capture** = its Δtotal ÷ O2's Δtotal.
- **The take-all book:** the baseline every veto is compared with.

## 4. Step 2 — the statistics

For each (cell, veto): the kept book (skipped sessions are zero-P&L days, counted as abstention) against the take-all
book.

**The null — exact time rotation of the take mask** over the window's trades, every circular offset (D738's
`rotation`; the number of offsets is the trade count, so its p95 has no sampling error). It keeps the veto's share and
its persistence; it breaks the alignment of the veto with the trades.
- **S2, the primary statistic: the kept trades' gross efficiency Σg / Σ|g|.** V1 selects on a volatility input, and
  a mean-dollar statistic under an input rotation is anti-conservative for a size-selecting filter (D711-A1: a 17 %
  false-pass rate). Efficiency is scale-free.
- **S1, reported:** the kept trades' mean net in dollars.
- **S3, reported:** the kept trades' mean y, y = net / σ$ (σ$ = σ_oc × \$2, D727's), the σ-normalised view.

**The within-year permutation** (D740's `within_year`, 20,000 draws, seed 743): the kept count is held per year. It
answers whether the veto selects trades within a year or picks years. Reported; it is not in the rule.

**Multiplicity:** Holm across the six S2 rotation p-values.

## 5. The decision rule (declared now; book-level statistics included)

A (cell, veto) is **SUPPORTED** iff all four hold:
1. **Selection:** S2's Holm-adjusted rotation p ≤ 0.05.
2. **The skipped trades do not earn:** their total net ≤ \$0, so the kept book's total net is at least the take-all
   book's (Δtotal ≥ 0).
3. **The book improves:** the kept book's daily net Sharpe > the take-all book's AND its max drawdown ≤ the
   take-all book's.
4. **The kept book meets the principal's standard** (D736's G1–G3, abstention years as abstention):
   - net without its two best years > 0;
   - positive in ≥ ⌈2/3·n⌉ of the years it trades;
   - ≥ \$209 a year without the two best years.

**LEAD** if (1) holds at a raw (un-Holmed) rotation p ≤ 0.05, or (1) holds and (2) fails: the veto separates better
from worse trades, but the skipped ones still earn. That is a sizing input, not a skip, and it is reported as such.

**NOT SUPPORTED** otherwise.

**A label beside the reading, never overturning it:** "PICKS YEARS" if the within-year S2 p > 0.10.

## 6. Assertions (all must be able to fire; the self-test checks that each canary raises)

1. **Known answers:** both cells' trade counts and mean nets (§1); D671's `overnight_audit` (no overnight bar at or
   after 09:30).
2. **Lag audit:**
   - the overnight canary (`overnight(include_rth=True)`) must make `overnight_audit` raise;
   - p_on is re-derived for 40 sampled sessions by a second implementation (a loop over the strictly earlier finite
     values), and D671's `tier_audit` must raise on `tiers(leak=True)`;
   - **the join:** the session feature table is joined to D727's day index by date string. A join audit compares 50
     sampled days with a direct lookup, and the same audit on the days rolled by one session must raise.
3. **Sign audit, in money:** 40 sampled trades' gross re-derived by D735's loop implementation (`e1_loop`) to 1e-9;
   and on a hand-built rising panel, a long pays a positive number of dollars and a short the same amount negative.
4. **Right quantity:** the kept set differs from its complement; each veto's skip mask, rotated by one trade, differs
   from the observed; V3 = V1 ∪ V2 exactly.
5. **The rotation:** offset 0 reproduces the observed S1/S2; a planted veto (skip every trade with gross < 0) must
   come out at rotation p < 0.01, and a veto drawn at random must not be SUPPORTED, in the self-test.

## 7. The report (all four groups)

Per cell and veto, kept vs skipped vs take-all:
- **Performance, net and gross:** total, mean, net and gross Sharpe and Sortino, share of sessions traded, max
  drawdown, Calmar, worst day, mean move per trade against 2c, breakeven cost.
- **Trade distribution:** count, mean, median, win rate, payoff, skew, kurtosis, and the three 1 % trims.
- **What the result depends on:** net by year and trades by year; the kept book ex its two best years; the top trade
  named.
- **Nulls:** observed, p50, p95 and p for S1/S2/S3 under the rotation; the within-year p.
- **The component line:** the kept book is a gated subset of its cell (YM k1.0's is D737's), so the same component.
  Reported: net Sharpe at one MNQ, hit rate, skew, gross beside net, and daily ρ with D737's in-sample twin and with
  NQ F2 (`Z.build_f2`).
- **The minimum detectable effect:** 2.8 × sd(net) × √(1/n_kept + 1/n_skipped), beside each observed difference.

## 8. Predictions (checkable)

- **The Fable agent, for the range breaks it found this on:** about 35 % fewer sessions and +2–4 bp net a kept trade.
- **Opus, for D735's legs:**
  - V2 skips about 10 % of trades. V1 skips fewer than a third, because D735 trades on most sessions and the
    percentile is of all sessions.
  - **P(at least one of the six SUPPORTED) ≈ 0.2.** The most likely outcome is LEAD or NOT SUPPORTED with the
    skipped trades still earning. D735's edge is NQ moving against the market after the open; a busy night raises
    the day's volatility, but it is not obviously spent information for that spread.
  - If anything passes, V2 on EQ k1.5 is the likeliest: a release moves the whole market, so NQ's move against the
    market should carry less information then.

## 9. Runtime

The Globex load (~2 min), four RTH panels through `read_cut`, and 6 × (exact rotation over ≤ 1,699 offsets +
20,000 within-year draws) — about 6–8 minutes in all, a run-once job. Launched as it stands.

## 10. What follows

- **SUPPORTED:** the principal decides between a forward monitor (the recorder would need an overnight-range column,
  which is the other session's file) and a post-vault layer for D737. Nothing changes D737.
- **LEAD or NOT SUPPORTED:** recorded. Idea 2 (the same consolidation break at the European open) is next on the
  principal's word.
