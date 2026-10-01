# D736 STAGE 0 PRE-REGISTRATION — a screen of the ES/NQ index-futures constructions already scored, under the principal's standard that a strategy must earn when it trades

*2026-10-01.*
- *The principal: "Ok lets start with #1". Option #1 was: rank every ES/NQ construction already scored here by the
  principal's standard (market-time share, net without its two best years, one micro).*
- *Numbered D736 after telling the other session (D735/D737 are theirs).*
- ***Committed alone, before its runner exists.** In-sample results only; nothing here opens the vault, the held
  2024-01 → 2025-02 slice or any data file.*

## 0. What this is, and what it is not

**The standard** (the principal, 2026-10-01, retiring the MACD arm): "I don't mind if a strategy does not trade when
the conditions are not right, in fact that is the best, but using capital to trade when you don't make money, even if
you don't lose money is shit."

**The question:** which constructions on file, if any, besides the NQ compression break, meet that standard in-sample at
one micro? The answer is a **shortlist**. The aim is to decide whether anything on file is worth a new pre-registration
before new constructions are designed.

**What this is not:**
- **Not a test, and not evidence of edge.** Every input is a recorded in-sample result. Most cells come from
  multi-cell families, and many were chosen post hoc in their own records. A construction on the shortlist has
  survived a robustness filter on numbers already seen. It has not been confirmed.
- **Admits nothing,** to any ledger or book, and takes no programme slot. A shortlisted construction goes further only
  through its own pre-registration, on the principal's word, on data it has not seen.

**Disclosed before the run:** I have seen many of these numbers (D732's series, D735's cells, and a reader's inventory
that computed several ex-best-two sums). The gates below were chosen with that knowledge. G3's floor is anchored to an
existing figure (§2), not tuned to the table.

## 1. The universe (declared; the runner reads exactly these)

Every block below carries **net dollars by calendar year at one micro contract**, in-sample, with no year after 2023.
Each is read from its committed result JSON:

| source | blocks | instrument, clock | window |
|---|---|---|---|
| D732 `stage0_d732_year_robust_book.json` | `series/{A,F,C,E,T1,T1.5}` (the MACD arm, NQ F2 book B, NQ compression C1, ES F2, D727 follow at k 1.0 and 1.5) | MNQ/MES | 2018-05-14 → 2023-12-29 |
| D735 `stage0_d735_nq_breaks_from_the_market.json` | `cells/*/book` (20 cells) | MNQ, 10:00–14:30 entry | 2016 → 2023 |
| D727 `stage0_d727_trend_curve.json` | `roots/{NQ,YM,RTY}/books/{per_clock,first_crossing}/*` (**not** `ceiling_*`, which are oracles) | micro of the root | 2016 (RTY 2017) → 2023 |
| D728 `stage0_d728_cross_asset.json` | `groups/*/S2_book/*/full_book` | MNQ | 2016 → 2023 |
| D731 `stage0_d731_flat_u.json` | `roots/NQ/S2/*/a_all` | MNQ | 2016 → 2023 |
| D733 `stage0_d733_pullback_entry.json` | `cells/*/book` | MNQ | 2016 → 2023 |
| D721 `diag_d721_quiet_day_f2.json` | `roots/*/{M0,M1_reported}/books/F2` | micro of the root | 2018 (RTY 2019) → 2023 |
| D711 `stage1_d711_f2_mechanism.json` | `A1/clocks/*/book` (ES F2 at six clocks), `A2/roots/*/line/book` | MES; MNQ/MYM/M2K | 2018 (RTY 2019) → 2023 |
| D699 `d699_gamma_macd_long.json` | `variants/*/2_book` (annual aggregates only; no per-date output, per the SqueezeMetrics licence) | MES | 2016 → 2023 |
| D689 `d689_short_gamma_continuation.json` | `cells/*/books/unfiltered_mes` | MES | 2016 → 2023 |

**Excluded, with the reason:**
- **D466, D468, D473 and D498** record yearly Sharpe or basis points, not yearly micro dollars.
- **D668/D672 per-root break tables and D640/D658/D659** have windows through 2025-02 and no yearly dollar block cut
  at 2023. NQ C1 enters through D732's cut series.
- **Constructions with no yearly block** (D724, D725, D730 and the others listed in the inventory).
- **Oracle and ceiling books.**

**The runner's input checks:**
- **The year check.** It asserts that every included block's years are ≤ 2023. A later year anywhere is a raise, not a
  silent drop.
- **The sum check.** It asserts that each block's yearly nets add up to its recorded total, wherever the record has
  one: `total_net`, or `trades × mean_net` / `mean_net_per_mnq`, to $0.01 per year of the window. A block that fails
  is reported as UNREADABLE and is not screened.

## 2. Per construction: the statistics and the gates

**Computed from the yearly nets:**
- `n_years`; total net;
- the two best years, and the net without them (**ex-2**);
- ex-2 per year (ex-2 / (n_years − 2));
- years positive;
- the worst year;
- the two best years' share of the total.

A partial first year counts as a year.

**Reported beside, as recorded** (not recomputed):
- trades; net Sharpe and Sortino; max DD; mean net per trade;
- correlation with NQ F2 or the arm, where recorded;
- **market-time share** = days with a position / sessions in the window.
  - Where the source gives no session count, it is trades per year / 252, marked *approx*.
  - D689 uses `days_traded`.

**The gates.** A construction **earns when it trades** if all three hold:

| gate | rule | why |
|---|---|---|
| **G1** | ex-2 net > 0 | it does not rest on its two best years |
| **G2** | net > 0 in at least ⌈2/3 × n_years⌉ years (6 years → 4, 8 → 6, 5 → 4, 7 → 5) | it earns in most of the years it trades, not only on average |
| **G3** | ex-2 per year ≥ **$209** at one micro | that is the MFFU 50k account's cost, hurdle P's P4 figure (`data/prop_venues.json`). A line that cannot pay for one prop account a year outside its two best years is, in the principal's sense, break-even |

**Labels:**
- **EARNS:** G1, G2 and G3 all hold.
- **RESTS ON ITS BEST YEARS:** G1 fails.
- **INTERMITTENT:** G1 holds and G2 fails.
- **BREAK-EVEN:** G1 and G2 hold and G3 fails.

**The shortlist** is every EARNS construction, ranked by ex-2 per year divided by (252 × market share): the ex-2
dollars per session in the market, the principal's "earn when it trades" made per unit of capital time. Each row is
tagged with its family (source and root), its status in its own record (CLOSED / DECLINED / QUEUED / open), and
**PRIMARY** where the record names it the pre-registered primary; otherwise it is **POST HOC**.

**Families.** A family with several EARNS cells is one candidate, not several. The count of EARNS **families** is the
headline.

## 3. Known answers (the runner checks these before screening)

| block | known answer |
|---|---|
| D732 `F` (NQ F2 book B) | yearly nets −13, −29, +1,220, +509, +3,772, +169 (to the dollar); ex-2 = **$636** |
| D732 `C` (C1 cut) | 251, 152, 385, 1,537, 1,930, 700; ex-2 = **$1,488**; 6 of 6 positive |
| D735 `YM_k1.0_1s` | 1,699 trades; ex-2 = **$6,933** (from the inventory; the runner recomputes it) |

A canary must raise on each of: a block with a 2024 key; a block whose yearly sum disagrees with its total; and a
deliberately swapped best-year pick (ex-2 computed by dropping the two *worst* years).

## 4. Predictions (stated before the runner exists)

| # | prediction |
|---|---|
| 1 | NQ compression C1 reads EARNS |
| 2 | NQ F2 (book B) reads BREAK-EVEN (ex-2 $636 over four years is $159 a year), and so does ES F2 |
| 3 | the MACD arm fails G2 (3 of 6 years positive) |
| 4 | at least one D735 equity-leg cell reads EARNS; the TICK cells do not |
| 5 | fewer than five families read EARNS |

## 5. What follows

- **The RESULT reports the full table,** grouped by label, then the shortlist.
- **Nothing proceeds without the principal's word.** For any EARNS family other than C1, the next step would be a
  pre-registration with its own confirmation slice. Where that slice could come from is the principal's call: the forward
  after 2026-09-18, or a held slice the line has not touched.
- **The relation to queued lines.** The runner reads no data and no vault output. D737 (D735's YM cell, slot 1) is
  frozen and queued, and this screen does not bear on it.
