# D753 STAGE 0 PRE-REGISTRATION — the channel level rule carried to daily futures: the principal's hand-cell lines on 34 roots, in volatility units, with a no-lines control

*2026-10-02.*
- *The principal: "I would like to revisit the channel mean reversion idea. Copy the construction and improve it with
  our new knowledge. Dont run anything until we have made improvements, dont look at results just the construction
  … hopefully we can avoid the multiplicity effects".*
- *The principal's choices:*
  - **"B: daily futures, 36 roots"**;
  - **"Convert by volatility"**;
  - **"Draft as written"** (the exits and the expected-profit gate).
- *Numbered D753, claimed with the documentation-review session.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29). Personal-book work, which is parked
  until real capital: when it runs is the principal's call.*

## 0. How this was designed, and what leaks

**How the construction was recovered.** A read-only Sonnet reader was told to return rules, parameters and the
principal's stated intent only, with no numbers, verdicts or "what was learned". It covered D398/D399, D476–D483 and
their runners' docstrings. The inventory of 2026-10-02 withholds the line's results for the same reason.

**What I (Opus) already knew, disclosed.** Before this redesign, this session's survey and my memory index had told
me the channel line's headline verdicts:
- the line was closed (D483-CLOSE);
- the level reading behaved like a generic dip;
- steeper lines did worse in real time;
- better-drawn lines gave the same trade.

**Where that may have shaped the design:**
- **§3's primary control** (the same rule with no lines) is partly informed by knowing how the channel line fared
  against a dip control. The rule behind it, "a control must break the claimed ingredient", is general.
- **Nothing else in §2 uses a channel-line result.** Each change cites a lesson from another line.

**The multiplicity this record carries.** The channel line's earlier records (D398, D399, D476–D483) are its prior
family, all on US equities 2010–2026. This record:
- reads **no data that family read**: futures, never equities;
- has **one primary cell**. Everything else is reported beside it and is never chosen from.

**Confirmation** would be the held futures slice (2024-01-01 → 2025-02-28), on the principal's word only. The vault
(2025-03-01 → 2026-09-18) is never read.

## 1. The construction recovered (the parts carried over unchanged)

**The lines: the principal's "hand cell"** (D480; `scripts/d480_hand_cell.py`'s `CELL_HAND`):
- `CELL_FINAL` with `pair_break=False`, `pair_draw=False`, `k=1`, `min_width=0`, `break_keep=1`, `break_depth=3.0`,
  `break_bars=1`, `stale_w=25`, `stale_d=12.0`, and a 4 % margin outside the wicks.
- It runs through `scripts/d399_recalc_segment.py`'s `recalc_pair`, with all the other dials as in `CELL_FINAL`:
  - pivots `pivots_tie_tolerant`, `mp=2`, `carry=7`;
  - an age-weighted OLS fit (`decay=0.76`, `dmode=rank`);
  - height anchored at the 0.2 quantile;
  - walk-back `reach=130`, `chain=body_only`, `fittol=16`, `dh=20`, `dg=0`.

**The level rule** (D482):
- pos = (log close − support level) / (resistance level − support level), with both lines drawn and width > 0;
- long on pos ≤ 0.10, short on pos ≥ 0.90, flat if both;
- **H = 5 sessions**, the original's headline: carried over, not re-chosen.

## 2. The changes, each from a lesson learned outside the channel line

| # | change | source |
|---|---|---|
| 1 | **Universe:** the 36 breadth roots less BZ and SR3 (more than 24 rolls a year, D555's exclusion), so **34 roots**, each from its first live year as `scripts/run_d555_tsmom_replication.py` defines it, through 2023-12-29 | unseen by the channel family |
| 2 | **Daily bars** from `fut_breadth_hourly` on the front contract (D555's session construction): O = the first bar's open, H/L over the session's bars, C = the last close. **Ratio back-adjusted at each roll** using both contracts' settlements on the last session before the roll (`fut_settle_strip`). The lines are drawn on the adjusted series; P&L is taken on the traded contract | an unadjusted roll gap would break every line; one stitching rule, stated once |
| 3 | **No trade spans a roll.** No entry when the front contract rolls within H + 2 sessions (the breadth fixture's roll calendar); a held position exits at the last session before a roll | the no-delivery ruling; no roll cost hidden in a trade |
| 4 | **Percent thresholds in volatility units.** Every threshold measured in log-price distance (margin 4 %, `break_depth` 3 %, `stale_d` 12 %, `dh` 20 %, `fit_tol` 16, `min_width` 0, and any other the code reads as percent of price; the runner lists them) is multiplied by r(root, t) = ATR20%(root, t−1) ÷ c_eq. ATR20% is the root's trailing 20-session ATR over its close; **c_eq** is the median of ATR20/close over the equity panel D476 read, on `keep_v2` bars 2010-01-04 → 2023-12-29. Dimensionless settings (counts in bars or pivots, quantiles, decay) are unchanged | the principal's choice, "Convert by volatility": the dialled geometry kept in risk units |
| 5 | **Entry at the next session's open** after the signal close | same-bar fills flatter reversion (D103; D341) |
| 6 | **Exits:** the first of (a) H = 5 sessions, at that session's close; (b) **a line break** of the side being traded (the hand cell's own invalidation: a close beyond the converted `break_depth`), at the next open; (c) the pre-roll exit (#3). **No target, no trailing stop** | brackets trade the mean for the win rate (D417, D752) |
| 7 | **Expected-profit gate:** enter only if the distance from the entry-signal close to the channel's middle, in dollars at one contract, is at least **3×** the round-trip cost | every strategy carries an expected-profit filter |
| 8 | **Cost:** one contract of the root's micro where `data/futures_costs.json` lists one, else the full contract; its `default_line` crossing (D748-A1's rule), plus one tick of slippage on each exit at the open | the ledger's measured cost, not Corwin–Schultz |
| 9 | **Both sides** traded symmetrically | futures short without borrow |

## 3. The tests

**Units.** Per trade, y = gross P&L ÷ σ\$, with σ\$ the root's trailing 20-session RMS daily move × \$/point at one
contract, known at entry. y pools the roots; dollars are reported beside it.

**PRIMARY (one cell): C1, the channel's mean gross y beats its null.**
- The null is the **exact circular rotation of each root's entry series** over its own eligible sessions, by a
  **shared offset k** across roots (k = 0 … the longest root's length − 1; each root shifted by k mod its own
  length).
- Each rotated entry keeps its date's bars and its exit rule; the side is recomputed from the rotated signal's sign.
- p_high ≤ 0.05; p50 and p95 reported.

**The economics, each required for a GO:**

| | criterion |
|---|---|
| **E1** | net mean per trade (\$) > 0 at **t ≥ 2** |
| **E2** | **median net per trade ≥ 0** (the principal's) |
| **E3** | skew of net per trade ≥ −0.5 (C-c) |
| **E4** | D736's G1–G3 on the yearly net: net without the two best years > 0; positive in ≥ ⌈2/3·n⌉ years; ≥ \$209 a year without the two best years |

**The control.**
- **X, the ingredient test:** the same level rule on a **plain rolling range** (the highest high and lowest low of
  the previous L sessions on the adjusted series, no lines).
  - **L = the median age of the drawn channels at their entries in this sample**: a property of the construction,
    measured by the runner before any P&L is computed.
  - The same gate, exits and costs.
- **X holds** when the channel's mean y exceeds the control's by more than 2 SE (the paired difference over the
  sessions where both trade, and the unpaired difference reported beside it).

**The reading:**
- **GO:** C1, E1–E4 and X.
- **SIGNAL, NOT THE LINES:** C1 holds but X fails.
- **SIGNAL ONLY:** C1 and X hold, some E fails (named).
- **NOTHING:** C1 fails.

**Reported, never chosen from:**
- per sector (equity index, rates, FX, metals, energy, grains/oilseeds, livestock, BTC) and per root: trades, mean,
  median and win rate in y and \$;
- long against short;
- H = 1, 3, 10, 20 beside the primary 5;
- the gate's effect (with against without);
- the four groups for the primary cell: Sharpe and Sortino of the daily book at one contract a root; max drawdown;
  breakeven cost; the 1 % trims; the top-name and top-year shares;
- the correlation with D737, F2 and C1's in-sample daily P&L (`data/d748_component_books.csv`).

## 4. Assertions (each canary must raise in the self-test)

1. **The known answer (construction):** the new line module, with every r ≡ 1 and the hand cell's percent values,
   reproduces `recalc_pair`'s support and resistance levels **exactly** on 24 sampled equity (name, window) pairs:
   D399's sampler, seeds 20260910 and 20260911. This is an equality of lines, not of any result.
2. **Stitching:** on every roll, the adjusted series' return across the roll equals the new contract's own return,
   the old contract's history scaled by the settlement ratio. A canary that skips one adjustment must fail it.
3. **Lag:**
   - r, σ\$, the lines and pos at t use data through t only; the fill is at t + 1's open;
   - a second implementation from raw sessions agrees on 40 sampled (root, t);
   - a canary that reads t + 1's close must disagree.
4. **Sign in money:** a long trade on a rising window pays positively; a short pays negatively.
5. **Rolls:** no trade's entry and exit straddle a roll; a planted roll inside a hold forces the pre-roll exit.
6. **The rotation:** offset 0 equals the observed; a planted entry series aligned to the outcomes gives p < 0.01;
   the vector form equals a loop on 50 offsets.
7. **The seal:** nothing on or after 2024-01-01 is read from any futures fixture. The equity panel is read only for
   c_eq (2010–2023) and assertion 1.

## 5. Predictions (Opus), declared before any number exists

- **P1:** C1 holds (P ≈ 0.5). The daily variance ratio is below 1 on 7 of 8 roots (D502), and a position-in-range
  rule should collect some of it.
- **P2:** X fails (P ≈ 0.65). The lines add nothing beyond the plain range at matched length. *This prediction is
  the place my prior knowledge leaks most, and it is stated as such.*
- **P3:** E1 fails (P ≈ 0.65). Daily reversion on futures is small, and the gate cuts the trade count.
- **P4:** rates and equity index carry most of any edge, and energy and metals the least (the variance-ratio
  ordering).
- **P(GO) ≈ 0.07.**

## A1 (2026-10-02, committed before the runner and before any run): how the construction is made exact

**Why.** Building the runner showed points the pre-registration left open, and one that cannot be built as written.
**No data has been read for this record.**

**A1.1, the volatility conversion, made exact.**
- **The change.** r is constant within each (root, calendar year):
  - r = the median of ATR20% over the root's sessions in the **previous calendar year** (at least 100 sessions),
    ÷ c_eq;
  - the lines for year y are drawn on the adjusted price raised to the power 1/r, over a window from 300 sessions
    before the year's first session to t;
  - a root's first traded year is its first with at least 250 earlier sessions.
- **Why a per-session r cannot be built.** The line construction is path-dependent (a segment persists for many
  bars), so a threshold that moves every bar cannot be applied to one line.
- **What the power transform does.** Every comparison the construction makes in log-price distance is multiplied
  by r at once, including two not listed in §2 #4:
  - **`delta`**, the slope gate (no line flatter than 1e-3 a bar). A slope is a log distance per bar.
  - **`touch_tol`**.
  - Pivot detection only compares highs and lows, so it is unchanged.
- **At r = 1 the transform is the identity** (`x ** 1.0` is exact), which is what §4's known answer checks.
- **A diagnostic, reported and not asserted:** the transformed run, against a run on raw prices with every
  log-distance threshold multiplied by r explicitly. A difference would expose a constant in the code that the
  explicit list misses.

**A1.2, non-positive prices.** A session with any non-positive price (CL, April 2020) is dropped from that root's
series. No trade spans a dropped session.

**A1.3, "a line break of the side being traded".** This is `recalc_pair`'s own `body` invalidation event on that
side (support for a long, resistance for a short) at the close of session u. The exit is at u + 1's open.

**A1.4, the control's break.** For the plain-range control (X), a close beyond the range's extreme, frozen at entry
(the low for a long, the high for a short), by `break_depth` × r. The exit is at the next open. This gives both
arms the same exit structure.

**A1.5, one position per root.** Re-entry only after an exit (D476's rule). The rotation null applies the same rule
to the rotated signals.

**A1.6, the control's length L.** Channel age at an entry = t − the later of the two segments' start bars. L = the
median over the channel's entries, rounded, computed before any P&L.

**A1.7, the daily book** (Sharpe, Sortino, drawdown, ρ): each trade's net is booked on its exit session.

**A1.8, the expected-profit gate's cost.** The base round trip: commission + the default-line crossing × tick. The
exit-at-open tick of slippage is charged in net but is not in the gate.
