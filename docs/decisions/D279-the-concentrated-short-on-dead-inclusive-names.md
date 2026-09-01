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

# RESULT — appended 2026-09-01, after the run

**Three of the four predictions are wrong, and one of them is wrong in the direction that matters.**

## The grid

Costs as pre-registered: 5 bp/side, borrow 3%/yr, `rf` 4%, PPY 252.

| cell | gross expo | CAGR | Sharpe | maxDD | trades | breakeven borrow | top name |
|---|---:|---:|---:|---:|---:|---:|---:|
| `S1_short\|all` | 16.52% | −2.45% | −0.757 | −35.00% | 45,405 | −11.4% | −2.4% |
| **`S1_short\|top10`** | 0.75% | **+0.77%** | **+2.343** | −0.35% | 5,349 | **+187.1%** | 1.5% |
| `S1_short\|rnd10` | 0.75% | −0.31% | −1.792 | −5.10% | 29,746 | −32.1% | −7.0% |
| **`S1_short\|top25`** | 1.86% | **+1.43%** | **+2.250** | −0.65% | 11,360 | **+121.7%** | 0.8% |
| `S1_short\|rnd25` | 1.86% | −0.58% | −1.528 | −9.22% | 67,031 | −24.7% | −136.9% |
| **`S1_short\|top50`** | 3.66% | **+2.05%** | **+1.865** | −1.12% | 19,419 | **+79.3%** | 0.7% |
| `S1_short\|rnd50` | 3.66% | −1.16% | −1.623 | −17.79% | 112,520 | −25.1% | −5.5% |
| `S2_short\|all` | 7.72% | −1.13% | −0.519 | −17.92% | 5,909 | −11.2% | −56.1% |
| `S2_short\|top10` | 0.75% | −0.11% | −0.374 | −2.35% | 1,778 | −11.0% | 17.4% |
| `S2_short\|top25` | 1.85% | −0.25% | −0.475 | −4.66% | 3,699 | −10.2% | 13.6% |
| `S2_short\|top50` | 3.53% | −0.40% | −0.465 | −7.23% | 5,608 | −8.2% | 12.2% |

Best-of-14 floor: **−0.165**. `S2_short`'s random controls are omitted from the table for width;
all four sit between −0.74 and −1.23 and none clears V.

## Two defects in my own runner, both found after the run and both fixed

**Neither changes a position, a return or a null.** Both are recorded because the pattern —
a hurdle computed, printed, and not actually applied to the thing it names — is the same one
[D230](D230-the-overlay-null.md) and D270 found, and this is its third appearance.

### 1. E′ measured the PANEL, not the HELD BOOK — and it flipped the survivor list

D279 above specifies E′ "over the held book". The runner called
`RP.effective_instruments(panel, 0)`, which measures all 1,573 names and returned **5.44 for every
cell**. A ten-name book and a 1,200-name book scored identically on the hurdle whose entire job is
to tell them apart. Recomputed on bars where **both names were held**
(`scripts/d279_fix_eprime.py`):

| cell | names held ≥250 bars | E′ over the book | E′ verdict |
|---|---:|---:|---|
| `S1_short\|top10` | **1** | **1.00** | **FAILS** (was passing on the panel value) |
| `S1_short\|top25` | 28 | 28.00 | passes |
| `S1_short\|top50` | 139 | 137.12 | passes |
| `S2_short\|top10` | 2 | 2.00 | **FAILS** |

**`top10` — the highest Sharpe in the study — is disqualified by its own pre-registered hurdle.**
It rotates so hard that exactly one name ever accumulates 250 held bars.

**And E′ is close to vacuous here even when it passes, which is a finding about the hurdle rather
than about the cells.** `top25` scores **28.00 on 28 names** — the correlation matrix is the
identity, because in a rotating book almost no *pair* shares 250 held bars. So E′ degenerates into
"how many names were held ≥250 bars". **The two survivors clear a hurdle that is barely measuring
what it claims**, and that is stated here rather than left for a reader to notice.

### 2. Hurdle C confounded the ranking with the turnover

`random-N` re-draws every bar. The ranked book does not have to: a name with the most negative
`hist_L` today is usually still near the bottom tomorrow. So the control **churns 5.6× harder and
pays 5.6× the fees** — the control differed from the treatment in *two* ways, and C could not say
which one it was measuring.

`scripts/d279_turnover_decomposition.py` separates them two ways: re-score everything at **zero
fees, zero borrow, zero rf**, and add a **persistent random control** (`per-N`) that draws at
random then *holds* the draw while it qualifies.

| arm | N | vs `rnd` net | vs `rnd` **GROSS** | vs `per` net | vs `per` **GROSS** | turnover |
|---|---:|---:|---:|---:|---:|---|
| S1_short | 10 | +4.135 | **+3.236** | +3.261 | **+3.218** | rnd 5.6× · per 0.5× |
| S1_short | 25 | +3.883 | **+2.990** | +3.127 | **+3.083** | rnd 5.9× · per 0.6× |
| S1_short | 50 | +3.483 | **+2.695** | +2.746 | **+2.719** | rnd 5.8× · per 0.6× |
| S2_short | 10 | +0.848 | +0.110 | −0.032 | **−0.068** | rnd 15.5× · per 0.6× |
| S2_short | 25 | +0.758 | +0.085 | −0.098 | **−0.121** | rnd 14.6× · per 0.6× |
| S2_short | 50 | +0.271 | −0.171 | −0.024 | **−0.038** | rnd 12.3× · per 0.7× |

**The two arms separate completely.**

- **S1's ranking survives both controls and the removal of all costs.** It beats a
  turnover-matched random book by **+3.22 Sharpe gross** at N = 10. The `per-N` control has
  *lower* turnover than the ranked book (0.5–0.7×), so it is if anything advantaged on cost, and
  it still loses by three Sharpe. The fee gap was never the story.
- **S2's three hurdle-C passes were ENTIRELY the fee gap.** Against a turnover-matched control at
  zero cost, S2's ranking is **worse than random** at all three N. **Those three C marks are
  withdrawn.** They changed no verdict — the S2 cells failed H, V and F anyway — but the mark was
  wrong and is corrected rather than left standing.

## Where the money comes from — the three ways a survivor could be fake

`scripts/d279_survivor_attribution.py`, on P&L D279 had already scored:

| | `top25` | `top50` |
|---|---:|---:|
| dead-name share of P&L | **+24.2%** (dead are **37.9%** of the panel) | +22.7% |
| names traded / profitable | 1,235 / **948** | 1,303 / **1,059** |
| names to reach **half** the P&L | **131** | **172** |
| top 1 / 5 / 10 name share | 0.8% / 3.5% / 6.5% | 0.7% / 2.9% / 5.3% |
| profitable years (of 14 traded) | **14 / 14** | 13 / 14 |

**It is not the dead names.** Delisted names carry **24.2%** of the P&L while making up **37.9%**
of the panel — they are *under*-represented, not driving it. The disqualifying pattern named in
advance (majority-dead **and** majority-late) does not occur.

**It is not a handful of names.** It takes **131 names to reach half the P&L**; the single best
name carries **0.8%**; 948 of 1,235 traded names are profitable. This is what E′ was supposed to
guard and could not — measured directly instead.

**It is not one era.** 2010–2012 produce exactly zero (warm-up: the 252-bar window plus the ragged
live mask), 2013 is ~0, and **every one of the 14 traded years is positive for `top25`.** The
87.1% "post-2016" share is 11 of the 13 effective years, i.e. proportionate, not an era effect.
Note the CAGR is divided by the **full 16.6-year** span while the book trades in 12.6 of them,
which understates it — conservative, and left uncorrected.

## Verdict against the pre-registered predictions

| | prediction | outcome |
|---|---|---|
| **N1** | a concentrated cell beats its base on Sharpe | **CORRECT** — S1 goes −0.757 → +2.343 |
| **N2** | the strength ranking does **not** beat `random-N` | **WRONG for S1, CORRECT for S2.** S1 beats a turnover-matched control by +3.22 Sharpe **gross** |
| **N3** | no cell clears H, V and C together | **WRONG** — `S1_short\|top25` and `\|top50` clear H, V, C, F and the corrected E′ |
| **N4** | any survivor has breakeven borrow below 20%/yr | **WRONG** — **121.7%** and **79.3%**. Even 100%/yr HTB leaves `top25` positive |

**N2 was the hurdle I said would kill this, and it is the one that did not.** By the terms written
above, that is the headline: *"the first evidence in this programme that a strength score carries
usable information, and it would matter more than the cell's return."* It is the first time in
D264–D279 that a strength ranking has beaten its own matched control.

## What must not be claimed from this

**Hurdle H carried no weight and should be treated as failed for this study.**
`S1_short|all` scores **100th percentile on both legs with −0.757 Sharpe and −2.45% CAGR.**
[R7](../RULES.md#r7)'s corollary is explicit that a null a *losing* book clears at the ceiling is
broken, not passed. Nine of fourteen cells clear H. **The verdicts here rest on V, C and F.**

**The book is tiny and the scaling step is not free.** Positions are `1/n_symbols` — **0.064% per
name** — so `top25` is 25 positions totalling **1.86% gross exposure** for **+1.43% CAGR**. In
[FINDINGS §1a](../FINDINGS.md) terms the product is `1.86% × 76.7%`: a small sleeve with a large
edge per unit of exposure. Running it as a real book means ~4% per name, a **~62× step**, and
Sharpe is scale-invariant but **borrow availability is not**. The breakeven-borrow figures say the
*rate* can be survived; they say nothing about whether 25 of the worst-accelerating names in the
market can be **located and held at size**, or about Reg SHO restrictions on exactly that
population. **The fixture cannot answer that and neither can I from here.**

**This is not a book entry.** Under [R8](../RULES.md#r8) it needs a pre-registered out-of-sample
test, and as this record said in advance, **this fixture has no untouched cohort left.** D246's
reserved wide-universe cohort is a different fixture and remains unspent.

## Ledger, restated

| count | N |
|---|---:|
| fresh — 14 as pre-registered | 14 |
| **`per-N` persistent controls added by the decomposition (2 arms × 3 N)** | **6** |
| carried: D256, same fixture and same arms | 21 |
| **total** | **41** |

Controls are counted like anything else — D228's floor does not care what a cell was built to
prove. The E′ fix and the attribution add **no** cells: both re-read numbers already scored.

## Stop, as written

The stop clause fires only on failure and did not fire. **Two cells survive**, so the concentrated
short is **not** closed — but nothing further may be tuned on this fixture either. The next honest
step is a pre-registered out-of-sample test on a fixture this programme has not touched, and
`cohort3` (D-number to be assigned) is **daily-selected but intraday** and is therefore *not* the
right instrument for it.
