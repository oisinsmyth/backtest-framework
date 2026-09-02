# D279 — The concentrated short on the dead-inclusive daily universe

**Status:** PRE-REGISTERED. Committed **before the run**. Nothing here is a result.
**Date:** 2026-09-01
**Area:** Strategy research · **personal track**

---

## Why this, and why it is the last untried thing that could work

[FINDINGS §9](../FINDINGS.md) named it, in the closing paragraph of
[D256](D256-the-book-on-single-names.md)'s post-mortem:

> An equal-weighted book over 1,580 single names **IS a diversified basket.** Idiosyncratic
> variance exists at the **name** level and averages away at the **book** level — the book holds
> **76.5% of live names at once.** We rebuilt the very diversification the hypothesis identified as
> the problem.
>
> **What is live now** is a question of **construction**, not universe: **a concentrated book**
> (colliding with hurdle E), or a factor-neutral one.

**D256 tested the universe. This tests the construction.** Same fixture, same arms, same constants
— the only change is **how many names are held at once.**

## And the cost arithmetic is why this deserves a proper test rather than another screen

The entire single-name intraday programme (D264–D278) failed one condition:

```
mean move per trade  >=  2c
```

**At fifteen minutes that bar was hopeless because the moves are small.** A 10-bar hold on a
40%-vol name moves ~80 bp against a 4–16 bp toll. **On daily bars with S1's ~15-day hold the same
name moves ~980 bp against the same toll** — roughly a twelvefold improvement in the ratio, from
holding period alone.

**That is the lever this whole session concluded was the only one left**, and it has never been
pulled on a concentrated book.

---

## The fixture

`us_shorts_daily_raw.csv.gz` — **1,573 names, 4,137,239 rows, 2010-01-04 → 2026-08-26, RAGGED.**
**562 carry a delisting date (35.7%)** and 122 more collapsed while listed.

**This is the only short-side fixture in the programme without the survivorship hole**, and D252's
own statement is carried rather than paraphrased: it *"deliberately contains dead companies and is
still not free of survivorship bias"* — provider coverage records 40–76 delistings a year for
2009–2012 against 700–1,000 after 2016, so **the dead cohort is materially under-sampled early in
the span** and any per-era reading must carry it.

---

## The construction — one change from D256

```
base      S1_short = -hold_book(hist_L < 0 & md_L >= 0)
          S2_short = -walk_state(g_lo < 0 & g_hi < 0), age cap 63
          exactly as D256 froze them; no constant is varied

CHANGE    hold only the TOP N qualifying names at each bar, by the signal's
          own continuous score:
            S1_short  rank by hist_L ASCENDING  (most negative acceleration)
            S2_short  rank by g_lo   ASCENDING  (steepest downtrend)
          N in {10, 25, 50}
```

### The control, and it is the hurdle that decides the study

**`random-N`: hold N qualifying names chosen AT RANDOM, same N, same count, same bars.**

**If concentration alone explains the result, the ranking carries nothing.** D267 measured that
signal strength is not magnitude-calibrated, and [D278](D278-the-instrument-holdout.md) watched
all five strength-based filters reverse sign out of sample. **So the burden is on the ranking to
beat random selection at matched concentration**, and that is where this study most likely dies.

**Cells: 2 arms × 3 N × 2 modes = 12, plus the 2 unconcentrated bases = 14.** Counted in full.

**Costs, unchanged from D256:** 5 bp/side, borrow 3%/yr, `rf` 4%, PPY 252.

---

## Hurdles

| | standard |
|---|---|
| **H** | **Matched-count rotation null ≥95th on BOTH legs**, Sharpe and money |
| **V** | **Positive net CAGR** after fees, financing and borrow |
| **C** | **Beats the `random-N` control at the same N and arm** — on Sharpe *and* on money |
| **F** | **Best-of-14 floor** (D228), one shared offset vector |
| **E′** | **Effective independent instruments ≥ 3.0** over the held book, and **≥500 pooled trades** |

### E is restated, and the restatement is declared rather than slipped in

**Hurdle E — ≥30 entries per symbol — cannot be met by a rotating top-N book and it is not a close
call:** with N = 10 drawn from 1,573 names, most names are never held. **E as written would fail
before the study started, which is exactly the tension FINDINGS §9 identified as having no
universe-level solution.**

**E measures independence, and its per-symbol form is a proxy that assumes a static universe.** For
a book that rotates through a large pool, R10's effective-instrument count measures the same thing
directly. **E′ replaces it, E is reported as it stands so nothing is hidden, and the verdict uses
E′.**

**What is lost by the substitution, stated plainly:** E also guards against a result carried by a
handful of names, and E′ does not. **So per-symbol P&L concentration is reported beside every
cell** — if one name carries a cell, that is disclosed with the cell, not buried.

### Borrow is the honest killer and is treated as such

**A book holding the ten weakest names holds precisely the hard-to-borrow ones.** D256's 3%/yr is
general-collateral and is almost certainly wrong for this book; realistic HTB on names in terminal
decline runs **20–100%/yr**.

**3% is charged for comparability with D256, and the BREAKEVEN BORROW RATE is reported as the
primary cost statistic** — it is a property of the book rather than of my assumption, exactly as
`breakeven_bps` was in D264.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **N1** | **At least one concentrated cell beats its unconcentrated base on Sharpe.** Concentration removes the dilution FINDINGS §9 identified | **moderate-high** |
| **N2** | **The STRENGTH ranking does not beat `random-N` (hurdle C).** D267 found strength is not magnitude-calibrated; D278 watched five strength filters reverse sign. **This is the hurdle I expect to kill it** | **moderate-high** |
| **N3** | **No cell clears H, V and C together** | **moderate** |
| **N4** | **Any cell that does clear has a breakeven borrow below 20%/yr**, i.e. realistic hard-to-borrow rates would sink it even if the signal survives | **moderate-high** |

**N2 and N4 are both declared against the construction.** If N2 is wrong — if ranking by signal
strength genuinely beats random selection at matched concentration — that is the first evidence in
this programme that a strength score carries usable information, and it would matter more than the
cell's return.

---

## Stop

**If no cell clears H, V and C, the concentrated short is closed** — no fourth N, no third arm, no
alternative ranking score, no re-cut of the universe. **Together with D256 that closes the
dead-inclusive daily fixture for directional shorts.**

**If a cell clears, it is not a book entry.** Under [R8](../RULES.md#r8) it needs a pre-registered
out-of-sample test, and this fixture has no untouched cohort left — D246's reserved wide-universe
cohort is a *different* fixture and is not spent here.

---

## Ledger

| count | N |
|---|---:|
| fresh — 2 arms × 3 N × 2 modes, + 2 bases | **14** |
| carried: D256, same fixture and same arms | 21 |
| **total** | **35** |

**Under [R13](../RULES.md#r13), the single-name INTRADAY work (D264–D278, ~430) is disclosed and
NOT carried.** Different fixture, different frequency, and the construction tested here was named
by FINDINGS §9 **before** that programme began — so it did not shape this search space. The ETF
programme's 45,783 is not carried for the reasons R13 already records.

---
---

# RESULT — REWRITTEN 2026-09-02. The first RESULT section was WITHDRAWN IN FULL: it was look-ahead.

**Status of this study: RUN AND CLOSED. 0 of 14. SURVIVORS: NONE. The stop clause fires and the
concentrated short is closed.**

**Everything above this line is the pre-registration exactly as committed in `61ef31d`, unaltered.**
The RESULT that stood here from 2026-09-01 reported two surviving cells at **+2.250** and **+1.865**
Sharpe and called them the first evidence in this programme that a strength ranking carries usable
information. **Those numbers were manufactured by a look-ahead defect in my own runner. Every one of
them is withdrawn**, along with everything derived from them — the breakeven-borrow figures, the
P&L attribution, the corrected-E′ survivor list and the decomposition's +3.22 headline.

The contaminated artefacts are **kept, not deleted**, as
`data/d279_concentrated_summary.WITHDRAWN_lookahead.json` and
`data/d279_turnover_decomposition.WITHDRAWN_lookahead.json`.

`uv run python scripts/run_concentrated_short.py` · `data/d279_concentrated_summary.json` ·
`data/d279_run_corrected.log` — 1,573 names × 4,187 bars, 300 rotation draws, 1,549s.

---

## The verdict — hurdle V fails in all fourteen cells

**Every cell in the grid has a negative net CAGR.** V is the first hurdle the pre-registration lists
after H, and nothing reaches it, so C, F and E′ decide nothing.

| cell | gross expo | CAGR | Sharpe | maxDD | trades | H (Sharpe/money) | be borrow | top name |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `S1_short\|all` | 16.52% | −2.45% | −0.757 | −35.00% | 45,405 | 100.0 / 100.0 | −11.4% | −2.4% |
| `S1_short\|top10` | 0.75% | −0.18% | −0.662 | −3.09% | 5,341 | 63.7 / 42.3 | −18.9% | 27.1% |
| `S1_short\|rnd10` | 0.75% | −0.31% | −1.792 | −5.10% | 29,746 | 22.0 / 45.7 | −32.1% | −7.0% |
| `S1_short\|top25` | 1.86% | −0.32% | −0.638 | −5.65% | 11,246 | 99.3 / 91.7 | −13.4% | 13.1% |
| `S1_short\|rnd25` | 1.86% | −0.58% | −1.528 | −9.22% | 67,031 | 98.0 / 100.0 | −24.7% | −136.9% |
| `S1_short\|top50` | 3.66% | −0.56% | −0.659 | −9.30% | 19,180 | 100.0 / 100.0 | −11.6% | 15.9% |
| `S1_short\|rnd50` | 3.66% | −1.16% | −1.623 | −17.79% | 112,520 | 96.7 / 99.0 | −25.1% | −5.5% |
| `S2_short\|all` | 7.72% | −1.13% | −0.519 | −17.92% | 5,909 | 100.0 / 78.0 | −11.2% | −56.1% |
| `S2_short\|top10` | 0.75% | −0.10% | −0.337 | −2.37% | 1,805 | 72.7 / 53.7 | −9.5% | 15.8% |
| `S2_short\|rnd10` | 0.75% | −0.23% | −1.198 | −3.78% | 27,399 | 94.0 / 92.3 | −24.4% | 28.4% |
| `S2_short\|top25` | 1.85% | −0.21% | −0.414 | −4.21% | 3,719 | 97.3 / 84.7 | −8.1% | 11.7% |
| `S2_short\|rnd25` | 1.85% | −0.49% | −1.097 | −7.80% | 53,855 | 99.3 / 98.7 | −20.9% | 26.1% |
| `S2_short\|top50` | 3.53% | −0.39% | −0.449 | −7.00% | 5,645 | 100.0 / 97.0 | −7.7% | 11.5% |
| `S2_short\|rnd50` | 3.53% | −0.72% | −0.895 | −11.25% | 69,021 | 100.0 / 100.0 | −16.0% | 25.8% |

**Best-of-14 floor: −0.178. Best cell: −0.337.** F fails everywhere too, and by a wider margin than
V does. **Every breakeven borrow rate is negative** — the book does not survive borrow at *zero*,
let alone at the 20–100%/yr this record warned hard-to-borrow names actually cost.

### And the gross numbers say the costs are not what is wrong

`scripts/d279_turnover_decomposition.py` · `data/d279_turnover_decomposition.json` ·
`data/d279_decomp_corrected.log` — every book re-scored at **zero fees, zero borrow, zero rf**.

| arm | N | `top-N` gross SR | `rnd-N` gross SR | `per-N` gross SR | `top-N` gross CAGR |
|---|---:|---:|---:|---:|---:|
| S1_short | 10 | **−0.485** | −0.725 | −0.708 | −0.15% |
| S1_short | 25 | **−0.432** | −0.542 | −0.635 | **−0.26%** |
| S1_short | 50 | **−0.438** | −0.617 | −0.640 | −0.44% |
| S2_short | 10 | **−0.244** | −0.390 | −0.213 | −0.09% |
| S2_short | 25 | **−0.294** | −0.441 | −0.236 | −0.19% |
| S2_short | 50 | **−0.322** | −0.167 | −0.300 | −0.35% |

**`top25` scores −0.432 Sharpe and −0.26% CAGR before a single basis point is charged.** That is the
number to carry out of this study. **Costs are not the binding constraint on this fixture — the
drift is.** Every intraday record from D264 to D278 closed on `mean move per trade ≥ 2c`; this one
does not get that far. It loses at zero cost, at every N, on both arms.

---

## THE DEFECT — the ranking read the bar it was about to be paid for

**This is the primary finding of D279 and it is the reason the record exists in this form.**

`hold_book` is R9-clean and always was:

```
p[:, 1:] = mask[:, :-1]          # the position at t comes from the signal at t-1
```

`pooled_returns` then earns bar `t`'s return on the position held at bar `t`, so the **base** book is
aligned and **[D256](D256-the-book-on-single-names.md) is not in question.** But `top_n` ranked with

```
s = score[q, t]                  # <-- hist_L computed from the CLOSE OF BAR t
out[pick, t] = base[pick, t]     # <-- and this position earns bar t's return
```

**Which names QUALIFY was honest. Which N of the qualifiers were HELD was chosen using the bar the
position was about to be paid for** — and that is precisely the quantity hurdle C exists to test.
`hist_L` is a function of recent returns *including that bar's*, so ranking ascending on it selects
names that **had already fallen that day**, and a short book then books the fall it selected on.

### Measured, not argued — `scripts/d279_lookahead_check.py`

| | |
|---|---:|
| `corr(hist_L at t, hist_L at t−1)`, 3,897,016 live bars | **+0.9805** |
| `corr(hist_L at t, return at t)` — ranking on this is peeking | **+0.0737** |
| `corr(hist_L at t−1, return at t)` — the tradeable version | **−0.0103** |

| cell | UNLAGGED — what D279 ran | LAGGED one bar — R9 |
|---|---:|---:|
| `top25` | **+1.43% CAGR, +2.250 Sharpe** | **−0.32%, −0.638** |
| `top50` | **+2.05% CAGR, +1.865 Sharpe** | **−0.56%, −0.659** |

**The score is 98.05% the same number one bar earlier and the entire result is in the other 1.95%.**
That is the shape of every look-ahead defect: the contaminated quantity looks almost identical to
the honest one and carries all of the P&L.

**The fix lives inside `top_n`, not at the call site**, because three other modules call it and a
convention that must be remembered is one that will be forgotten. **One consequence, recorded so a
reader is not misled:** re-running `d279_lookahead_check.py` today no longer reproduces its own
UNLAGGED column — `top_n` now lags unconditionally, so the script's two arms have become *lag-1* and
*lag-2*. The correlations above still reproduce exactly; **the UNLAGGED Sharpes are reproducible
only against the pre-fix runner**, and are quoted here from the withdrawn artefact.

### Which pattern this is, checked against the records rather than asserted

**It is NOT the D230/D270 pattern.** That label belongs to the E′ defect below, where the withdrawn
RESULT correctly placed it; it does not stretch to this one.
[D230](D230-the-bootstrap-sweep.md) and D270 are both **R6**: a hurdle leg *named in prose and never
computed at all* — D230's paired bootstrap, D270's M3, which the runner skipped by control flow and
printed *"M3 not computed"*. **Nothing here was skipped. The ranking was computed, and computed at
the wrong time.**

**It is the [R9](../RULES.md#r9) pattern, and this is its third appearance in the programme** —
after D224's stop evaluated against its own bar's high/low, and [D248](D248-the-strength-filtered-intraday-short.md)'s
quintile anatomy, which conditioned on `hist_L[t]` and then measured the fall it had conditioned on.
**The same variable, `hist_L`, for the second time.**

**And it carries a new corollary that D248's does not, because D248's defect lived in a throwaway
script while this one lived in the runner:**

> **A position built by lagging a MASK is not lagged if the choice of WHICH positions to keep is
> made on an unlagged score. The base being correctly lagged is what hides it.**

Every look-ahead guard this programme owns points at `hold_book`, and `hold_book` was right. The
defect entered one layer above it, in a function that *filters* an already-lagged book — a place
nothing was watching, because filtering a lagged book feels like it cannot introduce a lag error.

---

## The two other defects, both still true after the correction

### 1. Hurdle C's control differed from the treatment in TWO ways

`random-N` re-draws every bar. The ranked book does not have to: a name with the most negative
`hist_L` today is usually still near the bottom tomorrow. So the control **churns 5.6–6.0× harder on
S1 and 12.2–15.3× harder on S2**, and pays that multiple of the fees. **C could not say which of the
two differences it was measuring.**

The decomposition adds `per-N` — draw at random, then *hold* the draw while it qualifies — which
matches turnover instead of count:

| arm | N | vs `rnd` net | vs `rnd` **GROSS** | vs `per` net | vs `per` **GROSS** | turnover |
|---|---:|---:|---:|---:|---:|---|
| S1_short | 10 | +1.129 | +0.240 | +0.255 | **+0.223** | rnd 5.6× · per 0.5× |
| S1_short | 25 | +0.995 | +0.110 | +0.240 | **+0.203** | rnd 6.0× · per 0.6× |
| S1_short | 50 | +0.960 | +0.178 | +0.222 | **+0.202** | rnd 5.9× · per 0.7× |
| S2_short | 10 | +0.885 | +0.146 | +0.004 | **−0.031** | rnd 15.3× · per 0.6× |
| S2_short | 25 | +0.819 | +0.147 | −0.037 | **−0.058** | rnd 14.6× · per 0.6× |
| S2_short | 50 | +0.287 | −0.155 | −0.008 | **−0.022** | rnd 12.2× · per 0.7× |

**All six top-N cells still pass hurdle C as pre-registered, and the pass is worth nothing.** Against
a turnover-matched persistent control at zero cost, S1's ranking is worth **+0.223 / +0.203 / +0.202**
Sharpe and S2's is worth **less than nothing** (−0.031 / −0.058 / −0.022). **Against the contaminated
positions the same three S1 numbers were +3.218 / +3.083 / +2.719, so roughly 93% of the apparent
edge was the look-ahead.** What survives is real and is an order of magnitude too small: **`top25`
needs +0.432 to reach zero GROSS and the ranking supplies +0.203.**

**A third problem with C, found while writing this up and not previously recorded.** `rnd-N` is **one
draw**, not a distribution, and the main run and the decomposition drew different sequences. The same
control cell scores **−1.528 in the runner and −1.633 in the decomposition** at S1/N=25, and
**−0.895 against −0.736** at S2/N=50. **So C's margin moves by up to 0.16 Sharpe purely on the seed.**
A hurdle scored against a single random draw has no error bar; `rotation_nulls` takes 300 draws and
C takes one. It changed no verdict here — nothing cleared V — but C as written is not a test.

### 2. E′ was measured over the PANEL, not the held book

The pre-registration specifies E′ *"over the held book"*. The runner called
`RP.effective_instruments(panel, 0)`, which measures all 1,573 names and returns **5.44 for every
cell** — a ten-name book and a 1,200-name book scoring identically on the hurdle whose entire job is
to tell them apart. **This is genuinely the D230/D270 pattern and its third appearance:** the leg was
computed, printed, and not applied to the thing it names. **The runner still has this defect** — the
corrected summary carries `effective_instruments: 5.44` and an `Eprime_panel_defect` flag on every
cell.

Recomputed on bars where **both** names were held (`scripts/d279_fix_eprime.py`, re-run on the
corrected positions, `data/d279_eprime_corrected.log`):

| cell | names held ≥250 bars | E′ over the book | E′ verdict |
|---|---:|---:|---|
| `S1_short\|top10` | **1** | **1.00** | **FAILS** |
| `S1_short\|top25` | 28 | 28.00 | passes |
| `S1_short\|top50` | 137 | 135.29 | passes |
| `S2_short\|top10` | **2** | **2.00** | **FAILS** |
| `S2_short\|top25` | 14 | 14.00 | passes |
| `S2_short\|top50` | 105 | 105.00 | passes |
| `S1_short\|rnd10`, `\|rnd25`, `S2_short\|rnd10`, `\|rnd25` | 0 | 0.00 | **FAIL** |

**And E′ is close to vacuous here even where it passes, which is a finding about the hurdle rather
than about the cells.** `top25` scores **28.00 on 28 names**: the correlation matrix is the identity,
because in a book that rotates this hard almost no *pair* of names shares the 250-bar overlap
minimum. **E′ silently degenerates into "how many names were held ≥250 bars".** Any independence
measure with an overlap floor needs that floor checked against the book's holding pattern before its
number is trusted.

---

## Hurdle H is FAILED for this study, under R7's corollary

`S1_short|all` scores the **100th percentile on both legs with −0.757 Sharpe and −2.45% CAGR.**
**Seven of the fourteen cells clear H, and all fourteen lose money.**

[R7](../RULES.md#r7)'s corollary is explicit: *a hurdle that everything clears is not evidence, it is
a broken hurdle*, and a null that a **losing** book clears at the ceiling is broken rather than
passed. The per-symbol rotation null randomises each name's offset independently, which on this
fixture is a control so weak that the worst book in the grid tops it.

**H carried no weight in this verdict, and it should not be reused unmodified** by anything that
inherits this construction.

---

## The pre-registered predictions, scored against the corrected result

| | prediction | outcome |
|---|---|---|
| **N1** | at least one concentrated cell beats its unconcentrated base on Sharpe | **CORRECT, and it means less than it looks.** S1 goes −0.757 → −0.638 at N=25 and every S2 cell beats its base. Concentration removes exposure faster than it removes loss; **none of it reaches positive** |
| **N2** | the strength ranking does **not** beat `random-N` (hurdle C) | **WRONG AS WRITTEN, CORRECT AS MEANT.** All six top-N cells beat `rnd-N` net. Against a turnover-matched control at zero cost the ranking is worth **+0.20** for S1 and **negative** for S2 — real, and roughly a fifth of what breakeven needs. **This was named as the hurdle that would kill the study and it is not the one that did** |
| **N3** | no cell clears H, V and C together | **CORRECT — 0 of 14**, on V, and on F as well |
| **N4** | any survivor has a breakeven borrow below 20%/yr | **VACUOUS — there are no survivors.** Every cell's breakeven borrow is **negative**: the book fails at zero borrow, so the question N4 asks never arises |

**The prediction that was wrong is N2, and it was wrong in both directions at once** — the ranking
does beat the control, and the margin is far too small to matter. **A pre-registration that asks
"does it beat the control" and not "by how much, against what bar" gets an answer it cannot use.**

---

## Ledger

| count | N |
|---|---:|
| fresh — 14 as pre-registered | 14 |
| `per-N` persistent controls added by the decomposition (2 arms × 3 N) | 6 |
| carried: D256, same fixture and same arms | 21 |
| **total** | **41** |

**A bug fix is not a fresh look.** The corrected run re-scores the same fourteen pre-registered cells
on the same fixture with the same constants; nothing was searched, nothing was chosen after seeing a
number, and no cell was added or dropped. The E′ recomputation and the look-ahead check likewise add
nothing — both re-read positions already scored. **The count is unchanged from the withdrawn
version**, which is the correct outcome: the ledger prices the search, and the search did not change.

The six `per-N` controls **are** counted, because D228's floor does not care what a cell was built to
prove.

---

## What is withdrawn

Everything in this list was computed on the contaminated positions and **none of it may be quoted**:

1. **Both former survivors** — `S1_short|top25` at +2.250 / +1.43% and `S1_short|top50` at
   +1.865 / +2.05%, together with `S1_short|top10` at +2.343 / +0.77%.
2. **The claim that a strength ranking beat its own matched control for the first time in
   D264–D279.** The corrected margin is +0.203 gross at N=25, on a book at −0.432 gross.
3. **The decomposition's +3.218 / +3.083 / +2.719** `vs per GROSS` figures for S1.
4. **Every breakeven-borrow figure** — +187.1%, +121.7%, +79.3%. The corrected values are all
   negative.
5. **The whole P&L attribution**, `data/d279_survivor_attribution.json` and
   `scripts/d279_survivor_attribution.py`: the dead-name share, the 131-names-to-half-the-P&L
   count, the per-year table. It attributes P&L that does not exist.
6. **The corrected-E′ survivor list** in `data/d279_eprime.log` — the E′ *defect* is real and the
   *numbers* were computed on contaminated positions. Superseded by
   `data/d279_eprime_corrected.log` above.
7. **The survivor-only cut**, `scripts/d279_survivor_only_cut.py` — written to ask whether the
   edge was the delistings, **never completed, and now moot**: there is no edge to attribute. The
   script is kept because the counterfactual it measures is a real one for any future study on this
   fixture, and it would need re-pointing at whatever that study's positions are.

**S2's three withdrawn hurdle-C marks are re-withdrawn on better grounds.** The withdrawn RESULT
struck them because they were the fee gap alone; that reasoning survives the correction unchanged and
is strengthened — S2's ranking is *worse than random* at all three N once turnover is matched.

---

## Stop — fired

**The pre-registered stop reads: *"If no cell clears H, V and C, the concentrated short is closed —
no fourth N, no third arm, no alternative ranking score, no re-cut of the universe."* Zero cells
clear. It fires.**

**Together with [D256](D256-the-book-on-single-names.md), that closes the dead-inclusive daily
fixture for directional shorts of this family.** D256 tested the universe and D279 tested the
construction; both answered no, and the second answered no at zero cost, which is the harder no.

**What this does NOT close** — and the distinction is the whole reason the ledger and R13 exist:

- **The ranking itself is not closed, because it was never honestly tested.** What the corrected
  decomposition establishes is that `hist_L` ascending, applied *inside the qualifying set*, is
  worth about +0.20 gross Sharpe. [D280](D280-the-forecast-precheck.md) measured why it is that
  small — **the filter and the ranking are the same variable** — and
  [D281](D281-the-unfiltered-ranking.md) is the pre-registered test of the construction with that
  collision removed. Neither is licensed by this record's cells; both are licensed by its defect.
- **The factor-neutral branch of [FINDINGS §9](../FINDINGS.md) remains untouched** after D256, D264
  and D279.

**And nothing here reaches [R8](../RULES.md#r8).** There is no candidate, so there is nothing to take
out of sample, and **D246's reserved wide-universe cohort remains unspent** — which is the one good
outcome of catching this before designing a holdout around it.
