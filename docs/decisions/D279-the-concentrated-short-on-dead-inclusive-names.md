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
