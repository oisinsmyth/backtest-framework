# D350 — a long-timing screen: 138 declared events, each scored against its own names at random times

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. Nothing here is a book. This is a **screen**: it makes no claim of its own, spends no
holdout, and produces at most a shortlist of long triggers for a D347-style full record.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D347 put four long signals against the per-name time rotation and every one was below its
own names' random-time excess: the long excess in this programme is which names, not when.
The principal wants a real long trigger for the spread book. Four signals is not a search;
this record declares the family, scores every member on the statistic D347 says matters —
the excess **minus** the same names' unconditional excess — and states the multiplicity up
front. It uses the cheap estimand (a cached forward grid) to score all of them, and D347's
kernel on the few that pass. R14's fourth amendment says threshold-based selection is
untested by the ranking design and needs its own pre-registration: this is it.

## 1. The family, declared: 46 scores × 3 event shapes = 138

The 46 dimensionless scores of D335/D346 (the D290 51 less `macd_line`, `macd_hist`,
`impulse_nodz`, `amihud_21`, `price_log`), each floored (`keep_v2`), deal-filtered (F0), on
the warm base, lagged one bar, turned into a cross-sectional percentile `pct` among floored
live names at t−1 (average rank on ties; bars with fewer than 50 finite names undefined).
Three event shapes on `pct`, every one a **long** event:

| shape | long event at t | what it is |
|---|---|---|
| **E1** | `pct[t] ≤ 10` and `pct[t−1] > 10` | fresh entry into the bottom decile (D347's shape for `hist_L`, `rev_21`, `rsi` decile) |
| **E2** | `pct[t] ≥ 90` and `pct[t−1] < 90` | fresh entry into the top decile — the side is not a property of the score |
| **E3** | `pct[t] > 10` and `pct[t−1] ≤ 10` | the **recovery**: the percentile crosses back up out of the bottom decile (the `rsi`-turn shape; S1's shape) |

Every event is entered at the next open, hedged against the floored universe's own
equal-weight return, held 40 bars (the cap exit), truncated at delisting, confined to bars
after the hedge is defined everywhere (D347 §8). `hist_L`/E1, `rev_21`/E1 and `rsi`/E1 are
members and must reproduce D347's event sets exactly.

## 2. Stage 1 — the grid: every member, two controls, 1,000 draws each

`F[t, i]` is the forward-40 hedged excess of every floored name-bar (D347's
`forward_excess_grid`, signal-independent, one cumsum). The **grid estimand** for a member s
is `E_s = mean(F over its event cells)` — **every event counted**, including events on
names already held, which D347's kernel drops (a third of `hist_L`'s). That is a declared
deviation from the kernel estimand; the overlap share is reported per member, and stage 2
scores the survivors on the kernel.

**Control A on the grid** — each name's events rolled in time within its eligible bars,
offsets independent per name, implemented as a sparse gather of the rotated cells (guarded
against the dense rotation). **Control B on the grid** — each event's name replaced by a
random floored live name in the same `rsi`-rank bucket that day. **1,000 draws each.** Per
member: `E_s`, the **timing value** `TV_s = E_s − A's p50`, `z_A = (E_s − A p50) / A sd`,
`p_A`, `p_B`, `TV` in each era half, event count, distinct names, overlap share, and the
share of P&L in the top 1% of events.

**Multiplicity, three instruments (D299 §4):** per member, its own p; across the family,
**Benjamini–Hochberg at q = 0.10 on `p_A` over the 138** (with 1,000 draws the floor is
1/1001, so the bar is attainable); and for the headline, the **family-wise grid-max** — one
*shared* offset vector per draw (D288's device), the max `z_A` over the family, 1,000 draws,
reported beside the winner and not used as a gate. **`M_eff`** — the effective number of
independent tests by Li–Ji and Cheverud–Nyholt (`d321b_effective_tests.py`) from the
correlation matrix of the members' daily mean-`F` event series — is stated so that "138" is
read at its true size.

## 3. The stage-1 → stage-2 gate, declared

A member goes to the kernel if **all** of: `p_A ≤ 0.05`; `p_B ≤ 0.05`; `TV > 0` in **both**
era halves; at least 2,000 events. At most the **top five by `z_A`**. If none passes, the
top three by `z_A` run anyway, labelled as such, so the record shows what the best of 138
looks like under the kernel.

## 4. Stage 2 — the kernel: D347's estimand on the survivors

D345's kernel, cap exit, every event taken; controls A and B at 100 draws, C at 1,000; the
mirror; the invalidation exit; PUB net per trade; the four groups per trade with the top
trade named (bar, as-traded price, dollar-volume percentile); the splits; and the
interaction with the `rsi` ranking — the pair-book question: D347 says a long trigger must
fire profitably on **neutral** names, not on the extreme of the ranking.

## 5. The hurdle has teeth, shown before any member is read

R7's corollary cuts both ways: a hurdle nothing clears is as suspect as one everything
clears. The self-test builds an **oracle** event series from the future (events on the
name-bars whose `F` is in that name's own top decile) and asserts it clears control A at
p < 0.001; and a **noise** event series (matched count, random cells) and asserts its `p_A`
is not below 0.05 on more than 3 of 20 seeds. Both are assertions, not results.

## 6. Predictions

Q1 is load-bearing. Q7 and Q8 are against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* at least one member passes the stage-1 gate **and** is above the p95 of A, B and C under the kernel. |
| **Q2** | the number of members with `p_A ≤ 0.05` is at most `0.05 × M_eff + 2` — what false discovery alone would give. |
| **Q3** | no E1 member on a reversal-type score — `rsi`, `rev_5`, `rev_21`, `hist_L`, `md`, `dist_52w_high`, `mom_252_21` — has `TV > 0`: D347 generalises across the reversal family. |
| **Q4** | at least one **E3** member has `TV > 0` at `p_A ≤ 0.05`: if timing exists it is in the turn, not the extreme. |
| **Q5** | the family-wise grid-max p of the best member is **> 0.05**. |
| **Q6** | BH at q = 0.10 over the 138 rejects **zero** hypotheses. |
| **Q7** | *(against)* a stage-2 survivor's interaction with the `rsi` ranking is positive in the middle buckets (25–75) and negative in the bottom decile. |
| **Q8** | *(against)* a stage-2 survivor nets **> 0 per trade after PUB** under the invalidation exit. |
| *check* | `hist_L`/E1, `rev_21`/E1 and `rsi`/E1 reproduce D347's event counts exactly (23,491 for `hist_L`); the grid mean over `hist_L`/E1's events equals a direct per-event recomputation. |

## 7. Stop conditions

- **Q1 holds** → the survivor is a **candidate long trigger**, written up on its own with
  multiplicity 138 and `M_eff` stated, its `rsi`-bucket profile, and the four groups; the
  pair book's pre-registration is written on it and on D349's short side.
- **Q1 fails** → the long-timing search is **closed on this family**: no percentile-event on
  any of the 46 scores has timing against its own names. The pair book is short-signal-first
  if D349 delivers, and waits otherwise.
- **Q2 fails upward** (more survivors than false discovery gives) **and Q1 fails** → the grid
  and the kernel disagree; the overlap drop is the first suspect and the record says so.
- Nothing is promoted. Book: empty.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[F]** | the grid equals a direct per-cell recomputation on 3,000 sampled cells |
| **[G]** | `hist_L`/E1, `rev_21`/E1, `rsi`/E1 event matrices equal D347's `events_for` output exactly |
| **[SP]** | the sparse control-A gather equals the dense rotation-then-mask on 20 draws for 5 members, and on a tie-heavy synthetic grid |
| **[A]** | every name's event count preserved under A; **[B]** date and bucket preserved under B, name changed |
| **[O]** | the oracle clears A at p < 0.001; the noise series does not (≤ 3 of 20 seeds below 0.05) |
| **[E]** | 300 sampled events per shape satisfy the definition on the raw lagged percentile and fail unlagged |
| **[M]** | `1 ≤ M_eff ≤ 138`; the correlation matrix is symmetric with unit diagonal |
| **[BH]** | the BH procedure recovers the textbook rejections on a synthetic p-vector |
| **[X]** | on every stage-2 survivor: `Σ_b n_b (E_sb − E_s) = 0` |
| **[6]** | [O] raises when the oracle is replaced by noise; [SP] raises on a whole-grid roll |

## 9. Files

`docs/decisions/D350-a-long-timing-screen-scored-against-the-names-own-random-times.md`
(this record) · `scripts/run_d350_long_timing_screen.py` (stages: `--selftest`, `--screen`,
`--kernel <member> --part p`, `--report`) · `data/d350_screen.json`, `data/d350_ctrl_*.json`,
`data/d350_long_timing_screen.json` (to follow). Reuses `scripts/d348_prep.py`,
`scripts/d345_event_book.py`, `scripts/run_d347_long_signal_controls.py`'s helpers,
`scripts/d321b_effective_tests.py`'s estimators.
